"""把 高中校园物语/提示词_角色_v1.md 里的段落编译成游戏内数据。

用法（工程根 gal/ 下）：
    python tests/build_prompts.py

产出 game/ai/prompts_data.rpy —— 自动生成，不要手改。
源文件改了以后重跑本脚本；prompt 内容一变，schema_core.PROMPT_VER 要一起升，
否则旧缓存会把新提示词顶掉。

认的两种段落标记：
    ### P_A 世界                        → P_A
    ### P_stu_a / P_stu_b 同学甲、同学乙   → 同一段文本挂到两个 id
    **P_zm_3（T3 揭）**                  → P_zm_3
段落正文取标记之后第一个 ```text 围栏；同一段里第二个围栏会存成 <id>_ending
（P_D 的「结局拍」那套就是这么进去的）。
"""

import io
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                      # gal/
SRC = os.path.join(ROOT, "高中校园物语", "提示词_角色_v1.md")
OUTLINE = os.path.join(ROOT, "高中校园物语", "剧情大纲_三年_v1.md")     ## §2.7 的机器可读细节段
SCHEMA = os.path.join(ROOT, "game", "ai", "schema.rpy")           ## AI_BEATS 的唯一来源
OUT = os.path.join(ROOT, "game", "ai", "prompts_data.rpy")

_HEAD_RE = re.compile(r"^###\s+(.+?)\s*$")
_BREAK_RE = re.compile(r"^#{1,2}\s")          # 二级及更靠上的标题 = 换章，段落归属清空
_BOLD_RE = re.compile(r"^\*\*(P_[A-Za-z0-9_]+)")
_ID_RE = re.compile(r"P_[A-Za-z0-9_]+")
_FENCE_RE = re.compile(r"^```")

## 只有这几段的第二个正文围栏算「另一套口径」。其余段落里出现的第二个围栏
## 是示例/说明，不能误收成 <id>_ending（P_bro 后面 §3 的示意块踩过这个坑）。
ENDING_HOSTS = ("P_D",)


def parse(text):
    """返回 {段落 id: 正文}，保持出现顺序。"""
    paras = {}
    ids = []
    i = 0
    lines = text.splitlines()
    while i < len(lines):
        line = lines[i]

        m = _HEAD_RE.match(line)
        if m:
            found = _ID_RE.findall(m.group(1))
            ids = found
            i += 1
            continue

        if _BREAK_RE.match(line):
            ids = []
            i += 1
            continue

        m = _BOLD_RE.match(line)
        if m:
            ids = [m.group(1)]
            i += 1
            continue

        if line.startswith("```") and ids:
            fence = line[3:].strip()
            body = []
            i += 1
            while i < len(lines) and not _FENCE_RE.match(lines[i]):
                body.append(lines[i])
                i += 1
            i += 1
            if fence and fence not in ("text", "txt"):
                continue                      # 只收 text 围栏
            chunk = "\n".join(body).strip()
            if not chunk:
                continue
            if any(pid in paras for pid in ids):
                # 同一段的第二个围栏：只有白名单里的段落才收成 _ending
                if ids[0] in ENDING_HOSTS:
                    tail = ids[0] + "_ending"
                    if tail not in paras:
                        paras[tail] = chunk
                else:
                    sys.stderr.write("跳过多余围栏（%s 后面第 2 个）：%s\n"
                                     % (ids[0], chunk.splitlines()[0][:40]))
            else:
                ## 一个标题挂多个 id 时（P_stu_a / P_stu_b）两个都要拿到同一段
                for pid in ids:
                    paras[pid] = chunk
            continue

        i += 1
    return paras


_DETAIL_RE = re.compile(r"^([a-z][a-z0-9_]*)\s*[:：]\s*(.+)$")
## 主线拍 t<回合>_<词>，事件拍 e_<词>。两类都进 BEAT_DETAILS；别的行一律跳过并报出来。
_BEAT_KEY_RE = re.compile(r"^(?:t\d+|e)_[a-z0-9_]+$")


def parse_details(text):
    """解析机器可读的细节段：`t2_piano: 雨刚停 / 谱架压着两叠谱`，一行一拍。

    只认 beat id 形状的键（t<回合>_<词> 或 e_<词>），散文里偶然出现 `时间: 九月` 不会被吞。
    认得形状却被丢掉的键会打到 stderr，不许静默——2026-10-30 就因为只认 t\\d+_ 把 20 个 e_* 全吞了。
    """
    details = {}
    dupes = []
    empties = []
    for line in text.splitlines():
        m = _DETAIL_RE.match(line.strip())
        if not m:
            continue
        key, body = m.group(1), m.group(2)
        if not _BEAT_KEY_RE.match(key):
            sys.stderr.write("跳过不认识的键：%s\n" % key)
            continue
        items = [x.strip() for x in body.split("/")]
        items = [x for x in items if x]
        if not items:
            ## 围栏写坏时会走到这里；静默跳过等于丢一条细节还不吭声
            empties.append(key)
            continue
        if key in details:
            ## dict 会静默后者覆盖前者，t2_track 上踩过
            dupes.append(key)
            continue
        details[key] = items
    return details, dupes, empties


_BEAT_ANY_RE = re.compile(r'"(t\d+_[a-z0-9_]+)"\s*:\s*dict\(')
_EVENT_RE = re.compile(r"^e_[a-z0-9_]+$")     ## 事件拍由 EVENT_POOL 动态派发，不在 AI_BEATS 字面量里


def parse_beat_ids(path):
    """从 schema.rpy 抓 AI_BEATS 的键。抓不到就返回 None，调用方据此跳过过滤。

    e_* 事件拍由 EVENT_POOL 动态派发，所以不在 AI_BEATS 的字面量里，单独放行；
    t*_free 由 AI_FREE_BEATS 合成，但自由行动已经不走 AI，细节用不上，一并滤掉。
    """
    if not os.path.exists(path):
        return None
    ids = set()
    with io.open(path, encoding="utf-8") as f:
        for m in _BEAT_ANY_RE.finditer(f.read()):
            ids.add(m.group(1))
    return ids or None


def emit(paras, details):
    out = io.StringIO()
    out.write("## 自动生成，别手改。\n")
    out.write("## 源文件：高中校园物语/提示词_角色_v1.md 与 剧情大纲_三年_v1.md §2.7\n")
    out.write("## 重新生成：python tests/build_prompts.py\n")
    out.write("## prompt 内容一变，schema_core.PROMPT_VER 要一起升，否则旧缓存会顶掉新提示词。\n\n")
    out.write("init -4 python in aig:\n\n")
    out.write("    PARAS = {\n")
    for pid in sorted(paras):
        out.write("        %r: %r,\n" % (pid, paras[pid]))
    out.write("    }\n\n")
    out.write("    ## 每拍的「种子化环境细节」：同一拍按 seed 取一条塞给模型。\n")
    out.write("    ## 改细节不用升 PROMPT_VER（key 里已经有 seed），删改拍名要注意 AI_BEATS。\n")
    out.write("    BEAT_DETAILS = {\n")
    for bid in sorted(details):
        out.write("        %r: %r,\n" % (bid, tuple(details[bid])))
    out.write("    }\n")
    return out.getvalue()


def main():
    if not os.path.exists(SRC):
        sys.stderr.write("找不到源文件：%s\n" % SRC)
        return 1
    with io.open(SRC, encoding="utf-8") as f:
        src_text = f.read()
    paras = parse(src_text)
    if not paras:
        sys.stderr.write("一个段落都没解析出来，检查标记格式\n")
        return 1
    ## 标题写了、正文没取到也叫「section 解析出 0 条」——围栏写坏时就是这个样子，
    ## 静默跳过会让这个角色在提示词里消失，而 lint 和测试都不会红。
    seen = set()
    for line in src_text.splitlines():
        m = _HEAD_RE.match(line)
        if m:
            seen.update(_ID_RE.findall(m.group(1)))
    missing = sorted(pid for pid in seen
                     if pid not in paras and (pid + "_ending") not in paras)
    if missing:
        sys.stderr.write("这些段落有标题但没有正文（围栏可能写坏了）：%s\n"
                         % ", ".join(missing))
        return 1
    details = {}
    dupes = []
    empties = []
    for extra in (OUTLINE,):
        if os.path.exists(extra):
            with io.open(extra, encoding="utf-8") as f:
                d, dp, em = parse_details(f.read())
            for k, v in d.items():
                if k in details:
                    dupes.append(k)          ## 跨文件重复也要报
                else:
                    details[k] = v
            dupes.extend(dp)
            empties.extend(em)

    ## 两道出声的闸。理由不是今天这两次手误，是「改源文件的人不知道生成器会沉默地吃下去」：
    ## 围栏写坏 → 空块 → 静默少一条细节；拍 id 写两遍 → dict 后者覆盖前者 → 静默换掉正文。
    if dupes:
        sys.stderr.write("源文件里拍 id 重复（后者会静默覆盖前者）：%s\n"
                         % ", ".join(sorted(set(dupes))))
        return 1
    if empties:
        sys.stderr.write("有些拍的细节行是空的（围栏可能写坏了）：%s\n"
                         % ", ".join(sorted(set(empties))))
        return 1
    if not details:
        sys.stderr.write("一条细节都没解析出来，检查 §2.7 的格式（大括号/围栏/分隔符）\n")
        return 1

    ## 按 AI_BEATS 白名单过滤：大纲里改期/合并掉的旧拍 id 不再生成进代码。
    ## 源文件里那几行也删了，但生成器这道闸是在源头又被加回来时不至于复发。
    known = parse_beat_ids(SCHEMA)
    dropped = []
    if known:
        keep = {}
        for bid, items in details.items():
            if bid in known or _EVENT_RE.match(bid):
                keep[bid] = items
            else:
                dropped.append(bid)
        details = keep

    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(emit(paras, details))
    if dropped:
        print("  按 AI_BEATS 过滤掉 %d 个未登记拍：%s"
              % (len(dropped), ", ".join(sorted(dropped))))
    print("写出 %s：%d 个段落，%d 拍的细节（共 %d 条）"
          % (OUT, len(paras), len(details), sum(len(v) for v in details.values())))
    print("  公共段：%s" % ", ".join(sorted(p for p in paras if p[2:3] in "ABCD")))
    print("  结局套：%s" % ", ".join(sorted(p for p in paras if p.endswith("_ending"))))
    print("  八拍变体：%s" % ", ".join(sorted(p for p in paras if re.match(r"P_zm_\d", p))))
    thin = sorted(k for k, v in details.items() if len(v) < 2)
    if thin:
        print("  细节不足 2 条的拍（coverage 会判红）：%s" % ", ".join(thin))
    return 0


if __name__ == "__main__":
    sys.exit(main())
