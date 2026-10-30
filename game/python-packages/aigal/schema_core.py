"""AIGAL · AI 输出契约（解析 / 清洗 / 校验）。

纯标准库，不 import renpy。这样能用系统 Python 直接跑
`tools/selftest_schema.py`，不用起游戏窗口。

Ren'Py 侧的绑定（beat 表、turn 断言、Character 是否真的 define 了、主角名替换）
在 `game/ai/schema.rpy`。

清洗顺序（顺序不能换，validate() 里一步一步来）：
    1  解析 raw → dict
    2  顶层键只留 lines / choices / flags / mood，其余丢弃并记 note
    3  lines：speaker 白名单 → text 清洗 → 截断 → 空行丢弃
    4  一行都不剩就拒（让上层走模板降级）
    5  choices：action_key 白名单 → 去重 → text 清洗 → 截断
    6  flags：本拍白名单 → 去重 → 截断
    7  mood：一个词
    8  总字数超了从末尾砍行

这里一个数值字段都不产出。AI 拿不到 study/stress/stamina/money/ap/turn——
返回值里没有这些槽位，raw 里带了也在第 2 步被丢掉。
"""

import json
import re

## 换掉 schema/提示词任何一处都要进缓存 key，否则旧缓存会继续命中旧口吻。
## 2：长度口径收到 400/120（运行时预算 v1），旧的 900 字缓存在新预算下不可用。
## 3：单行 120 → 100（美工实测正文框 31 字/行、4 行封顶 124，120 只剩 4 字余量）。
SCHEMA_VER = 3
PROMPT_VER = "角色_v1.2"


def cache_prefix():
    """缓存 key 的前缀。cache.rpy 拼 key 时必须以它开头。"""
    return "s%d|%s" % (SCHEMA_VER, PROMPT_VER)


## 长度上限（按字符算，中文一个字算 1）##########################################
## 口径见 高中校园物语/运行时预算_v1.md + Chief 的定稿：
##   提示词目标 250（管节奏），校验上限 400（管兜底），单行 100。
##   单行为什么是 100 不是 120：美工实测正文框每行约 31 字、4 行封顶 124 字，
##   120 只剩 4 字余量，标点和数字字宽一变就压出框；Ren'Py 不裁切、测试也不报错。
##   100 字是 3.2 行，留一整行余量。
## 只在这里截，代码别处不许再截一次。
LINE_MAX = 100
LINES_MAX = 5
CHOICE_MAX = 16
CHOICES_MAX = 3
MOOD_MAX = 8
FLAGS_MAX = 3
TOTAL_MAX = 400

## 结局单独一套：复用的后果是 TRUE 结局被截到 400 字，那是整局最后一段正文。
## TODO(M4)：真人交付时的口径是 1000 字 / 30s 超时，等结局分支接进来再定。
ENDING_LINE_MAX = 200
ENDING_TOTAL_MAX = 1000

## 主角名占位。AI 不知道玩家填的名字，正文里一律用这个 token，
## 到 ai_render() 才换成真名。字符集刻意不含 {}[]<>，不会被当标记解析。
NAME_TOKEN = "{name}"

## characters.rpy 里 define 过的那 8 个 + 待建的 5 个（人物卡 v1.1）。
## 这里只做「契约上允许」，运行时是否真的 define 由 schema.rpy 再查一遍。
ALL_SPEAKERS = (
    "mc", "zm", "zzb", "zeng", "stu_a", "stu_b", "bro", "inner",
    "xia", "kong", "x", "zm_dad", "zm_mom",
    ## 结构性 id：正体旁白，不是角色。不进人物卡，但任何一拍都可能出现。
    "nar",
)

_CONTROL_RE = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_TAG_RE = re.compile(r"\{[^{}]*\}")
_BRACKET_RE = re.compile(r"[\[\]<>]")
_WS_RE = re.compile(r"[ \t\u3000]+")
_NL_RE = re.compile(r"\r\n?|\n")
_FENCE_RE = re.compile(r"```(?:[a-zA-Z0-9_+-]*)\s*(.*?)```", re.S)
_TRAILING_COMMA_RE = re.compile(r",(\s*[}\]])")

_LINE_KEYS = ("speaker", "text")
_CHOICE_KEYS = ("text", "action_key")
_TOP_KEYS = ("lines", "choices", "flags", "mood")


def strip_markup(s):
    """去掉一切会被 Ren'Py 当标记解析的东西：{} 标签、[] 插值、<>、控制字符。

    标签要反复剥，防 `{a={b}}` 这种嵌套残留：剥一次会留下 `{a=}`，再剥一次才干净。
    """
    if not isinstance(s, str):
        return ""
    s = _CONTROL_RE.sub("", s)
    s = _NL_RE.sub(" ", s)
    prev = None
    while prev != s:
        prev = s
        s = _TAG_RE.sub("", s)
    s = s.replace("{", "").replace("}", "")
    s = _BRACKET_RE.sub("", s)
    return _WS_RE.sub(" ", s).strip()


def sanitize_text(raw, limit):
    """清洗一条文本，返回 (text, notes)。超长截断而不是拒，脏字比降级便宜。"""
    notes = []
    if raw is None:
        return "", ["text_missing"]
    if not isinstance(raw, str):
        return "", ["text_not_str"]
    s = strip_markup(raw)
    if "XXX" in s:                      # 骨架里的占位名，AI 会照抄
        s = s.replace("XXX", NAME_TOKEN)
        notes.append("name_token_substituted")
    if len(s) > limit:
        s = s[:limit].rstrip()
        notes.append("text_truncated")
    return s, notes


def parse_json(raw):
    """把模型回来的原文解析成 dict，返回 (obj, reason)。

    reason：ok / empty / not_json / root_not_object。
    容错顺序：先整段、再取 ``` 围栏里的、再取第一对花括号之间；都失败才试补尾逗号。
    尾逗号是模型最常见的失手，能修就修，别为一个逗号重发请求。
    """
    if raw is None:
        return None, "empty"
    if isinstance(raw, (bytes, bytearray)):
        raw = raw.decode("utf-8", "replace")
    if not isinstance(raw, str) or not raw.strip():
        return None, "empty"
    s = raw.replace("\ufeff", "").strip()

    candidates = []
    m = _FENCE_RE.search(s)
    if m:
        candidates.append(m.group(1))
    candidates.append(s)
    i, j = s.find("{"), s.rfind("}")
    if i != -1 and j > i:
        candidates.append(s[i:j + 1])

    for cand in candidates:
        for attempt in (cand, _TRAILING_COMMA_RE.sub(r"\1", cand)):
            try:
                obj = json.loads(attempt)
            except Exception:
                continue
            if isinstance(obj, dict):
                obj["__repaired__"] = attempt is not cand
                return obj, "ok"
            return None, "root_not_object"
    return None, "not_json"


def _show(v):
    """note 里展示被拒的值：字符串不加引号，其它用 repr，方便 grep。"""
    return v if isinstance(v, str) else repr(v)


def _reject(reason, notes, raw_len=0):
    return {
        "ok": False, "reason": reason, "notes": list(notes),
        "lines": [], "choices": [], "flags": [], "mood": "",
        "raw_len": raw_len,
    }


def _bad_ctx(ctx):
    """ctx 是上层代码给的，不是模型给的；缺字段是程序错，不是模型错。"""
    if not isinstance(ctx, dict):
        return True
    for k in ("beat", "turn", "speakers", "actions", "flags"):
        if k not in ctx:
            return True
    return not isinstance(ctx["speakers"], (list, tuple)) or not isinstance(ctx["actions"], (list, tuple))


def validate(raw, ctx):
    """校验一次模型输出。

    ctx = {
        "beat":  "t2_piano",          # 拍 id，只用来记日志
        "turn":  2,                   # 本拍属于哪个月，只用来记日志
        "speakers": ("mc", "zm"),     # 本拍允许的 speaker id
        "actions": ("study", "rest_dorm"),   # 本拍允许的 action_key
        "flags":   (),                # 本拍允许 AI 置位的 flag（通常是空的）
        "expect_choices": False,      # 这一拍本来就该给选项吗
    }
    返回 dict：ok / reason / notes / lines / choices / flags / mood / raw_len
    """
    notes = []
    raw_len = len(raw) if isinstance(raw, str) else 0

    if _bad_ctx(ctx):
        return _reject("bad_ctx", notes, raw_len)

    obj, why = parse_json(raw)
    if obj is None:
        return _reject(why, notes, raw_len)
    if obj.pop("__repaired__", False):
        notes.append("repaired_trailing_comma")

    ## 2. 顶层键白名单：数值类字段在这里就被丢掉，AI 永远碰不到 stats
    for k in list(obj.keys()):
        if k not in _TOP_KEYS:
            notes.append("dropped_top_key:%s" % k)

    allowed_speakers = set(ctx["speakers"])
    allowed_actions = set(ctx["actions"])
    allowed_flags = set(ctx["flags"])

    ## 3. lines
    raw_lines = obj.get("lines")
    if raw_lines is None:
        return _reject("no_lines", notes, raw_len)
    if not isinstance(raw_lines, list):
        return _reject("lines_not_list", notes, raw_len)

    ## 拍内一套（250 字），结局一套（600 字）。结局要是被拍内那套截到 250，
    ## 整局最后一段正文就没了，所以这两套常量不能互相复用。
    if (ctx.get("scope") or "scene") == "ending":
        line_max, total_max = ENDING_LINE_MAX, ENDING_TOTAL_MAX
    else:
        line_max, total_max = LINE_MAX, TOTAL_MAX

    lines = []
    for item in raw_lines:
        if len(lines) >= LINES_MAX:
            notes.append("lines_over_cap")
            break
        if not isinstance(item, dict):
            notes.append("line_not_object")
            continue
        for k in item:
            if k not in _LINE_KEYS:
                notes.append("line_extra_key:%s" % k)
        sp = item.get("speaker")
        sp = sp.strip() if isinstance(sp, str) else ""
        if sp not in allowed_speakers:
            notes.append("speaker_rejected:%s" % _show(sp or item.get("speaker")))
            continue
        txt, n2 = sanitize_text(item.get("text"), line_max)
        notes.extend(n2)
        if not txt:
            notes.append("line_empty")
            continue
        lines.append({"speaker": sp, "text": txt})

    ## 4. 一行都没剩，交给上层降级
    if not lines:
        return _reject("no_lines", notes, raw_len)

    ## 5. choices（0 条合法：固定骨架的拍本来不给选项）
    raw_choices = obj.get("choices")
    if raw_choices is None:
        raw_choices = []
    if not isinstance(raw_choices, list):
        return _reject("choices_not_list", notes, raw_len)

    choices = []
    seen = set()
    for item in raw_choices:
        if len(choices) >= CHOICES_MAX:
            notes.append("choices_over_cap")
            break
        if not isinstance(item, dict):
            notes.append("choice_not_object")
            continue
        for k in item:
            if k not in _CHOICE_KEYS:
                notes.append("choice_extra_key:%s" % k)
        ak = item.get("action_key")
        ak = ak.strip() if isinstance(ak, str) else ""
        if ak not in allowed_actions:
            notes.append("action_key_rejected:%s" % _show(ak or item.get("action_key")))
            continue
        if ak in seen:
            notes.append("action_key_duplicate:%s" % ak)
            continue
        txt, n2 = sanitize_text(item.get("text"), CHOICE_MAX)
        notes.extend(n2)
        if not txt:
            notes.append("choice_empty")
            continue
        seen.add(ak)
        choices.append({"text": txt, "action_key": ak})

    if ctx.get("expect_choices") and not choices:
        notes.append("choices_missing")
        return _reject("choices_missing", notes, raw_len)

    ## 6. flags：只认本拍白名单，只置位不撤销
    raw_flags = obj.get("flags")
    if raw_flags is None:
        raw_flags = []
    if isinstance(raw_flags, dict):          # 模型偶尔写成 {"set": [...]}
        notes.append("flags_dict_form")
        raw_flags = raw_flags.get("set") or []
    if not isinstance(raw_flags, list):
        return _reject("flags_not_list", notes, raw_len)

    flags = []
    for f in raw_flags:
        if len(flags) >= FLAGS_MAX:
            notes.append("flags_over_cap")
            break
        if not isinstance(f, str):
            notes.append("flag_not_str")
            continue
        f = f.strip()
        if f not in allowed_flags:
            notes.append("flag_rejected:%s" % f)
            continue
        if f in flags:
            continue
        flags.append(f)

    ## 7. mood
    mood, n2 = sanitize_text(obj.get("mood"), MOOD_MAX)
    notes.extend(n2)
    if not mood:
        mood = ""

    ## 8. 总字数兜底：先修尾句，实在不够再砍行。
    ##    整行砍掉会丢一整个表演段落，修尾句只丢半句；剩下的余量不足 4 字才丢整行。
    total = sum(len(l["text"]) for l in lines)
    guard = 0
    while total > total_max and len(lines) > 1 and guard < 32:
        guard += 1
        over = total - total_max
        last = lines[-1]["text"]
        if len(last) - over > 4:
            lines[-1]["text"] = last[:len(last) - over].rstrip()
            total = sum(len(l["text"]) for l in lines)
        else:
            total -= len(last)
            lines.pop()
        notes.append("total_truncated")

    return {
        "ok": True, "reason": "ok", "notes": notes,
        "lines": lines, "choices": choices, "flags": flags, "mood": mood,
        "raw_len": raw_len,
    }
