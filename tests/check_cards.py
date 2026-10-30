"""人物卡 / characters.rpy / 提示词 三处一致性检查。

为什么不手写计数：「13 个 id 里有 8 个 define、5 个待补」这种句子，只要有人动一次
characters.rpy 就过期，而且过期了没人报错。这个脚本现算现比，任何一处对不上就 fail。

用法（工程根 gal/ 下）：
    python tests/check_cards.py

退出码 0 = 全过；1 = 有检查没过（dev.ps1 会 grep 输出并拦下来）。
不依赖引擎、不联网、只用标准库。
"""

import io
import json
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)                                   # gal/

CHARS = os.path.join(ROOT, "game", "story", "characters.rpy")
CARD_JSON = os.path.join(ROOT, "高中校园物语", "人物卡_v1.json")
PROMPTS_MD = os.path.join(ROOT, "高中校园物语", "提示词_角色_v1.md")

## 提示词里除角色段之外的公共段
COMMON_IDS = {"P_A", "P_B", "P_C", "P_D"}

## 结构性 speaker：在 characters.rpy 里 define、但不属于「角色」，不进人物卡。
## 目前只有 nar（正体旁白，P_D 收尾靠它）。新增同类 id 就加到这里，别去改人物卡。
STRUCTURAL_IDS = {"nar"}

_DEFINE_RE = re.compile(r"^define\s+([A-Za-z_][A-Za-z0-9_]*)\s*=\s*Character\(")
_PID_RE = re.compile(r"P_[A-Za-z0-9_]+")
_BEAT_RE = re.compile(r"^P_zm_\d$")

## 这些字段是给 AI 当正面示例用的，里面出现定性形容词就是错的
SCAN_FIELDS = ("speech", "habits", "lines", "lines_new", "voice")


def _read(path):
    with io.open(path, encoding="utf-8") as f:
        return f.read()


def parse_defines(text):
    """characters.rpy 里的 define 名，按出现顺序。"""
    names = []
    for line in text.splitlines():
        m = _DEFINE_RE.match(line.strip())
        if m and m.group(1) not in names:
            names.append(m.group(1))
    return names


def parse_prompt_ids(text):
    """提示词文档里登记了段落的 id。

    只认两种标记，正文里顺嘴提到的不算：
        ### P_xxx ...
        **P_xxx（...）**
    """
    ids = set()
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("### "):
            ids.update(_PID_RE.findall(s))
        elif s.startswith("**P_"):
            m = _PID_RE.match(s[2:])
            if m:
                ids.add(m.group(0))
    return ids


class Checker(object):
    def __init__(self):
        self.fails = []

    def check(self, name, cond, detail=""):
        if cond:
            print("  ok    %s" % name)
        else:
            print("  FAIL  %s%s" % (name, ("  <- " + detail) if detail else ""))
            self.fails.append(name)


def main():
    for path in (CHARS, CARD_JSON, PROMPTS_MD):
        if not os.path.exists(path):
            sys.stderr.write("找不到文件：%s\n" % path)
            return 1

    defines = parse_defines(_read(CHARS))
    card = json.loads(_read(CARD_JSON))
    speakers = card.get("speakers", {})
    counts = card.get("speaker_counts", {})
    prompt_ids = parse_prompt_ids(_read(PROMPTS_MD))

    sp_ids = set(speakers)
    def_ids = set(defines)

    c = Checker()

    print("[1] characters.rpy")
    c.check("define 数量 > 0", len(defines) > 0, "一个 define 都没解析到")

    print("[2] 人物卡 speakers 与 characters.rpy")
    char_ids = def_ids - STRUCTURAL_IDS
    c.check("两边的 id 集合相同（结构性 id 除外）", sp_ids == char_ids,
            "只在卡里：%s ｜ 只在 rpy 里：%s ｜ 结构性：%s"
            % (sorted(sp_ids - char_ids) or "无", sorted(char_ids - sp_ids) or "无",
               sorted(STRUCTURAL_IDS & def_ids) or "无"))
    c.check("结构性 id 都已 define", STRUCTURAL_IDS <= def_ids,
            "缺：%s" % (sorted(STRUCTURAL_IDS - def_ids) or "无"))

    print("[3] speaker_counts 自洽（这几条就是原来手写的那几个数）")
    c.check("total == speakers 数",
            counts.get("total") == len(sp_ids),
            "写的 %r，实际 %d" % (counts.get("total"), len(sp_ids)))
    c.check("defined_in_characters_rpy == 交集数",
            counts.get("defined_in_characters_rpy") == len(sp_ids & def_ids),
            "写的 %r，实际 %d" % (counts.get("defined_in_characters_rpy"), len(sp_ids & def_ids)))
    c.check("defined_ids 与实际交集一致",
            set(counts.get("defined_ids") or []) == (sp_ids & def_ids),
            "写的 %s" % sorted(set(counts.get("defined_ids") or []) ^ (sp_ids & def_ids)))
    missing = sp_ids - def_ids
    c.check("pending_define == 差集数",
            counts.get("pending_define") == len(missing),
            "写的 %r，实际 %d" % (counts.get("pending_define"), len(missing)))
    c.check("pending_define_ids 与差集一致",
            set(counts.get("pending_define_ids") or []) == missing,
            "写的 %s" % sorted(set(counts.get("pending_define_ids") or []) ^ missing))
    c.check("gaps.missing_character_defines 与差集一致",
            len(card.get("gaps", {}).get("missing_character_defines") or []) == len(missing),
            "写明 %d 个，实际缺 %d 个"
            % (len(card.get("gaps", {}).get("missing_character_defines") or []), len(missing)))

    print("[4] 提示词段落覆盖")
    no_prompt = sorted(i for i in sp_ids if ("P_" + i) not in prompt_ids)
    c.check("每个 speaker 都有 P_<id> 段", not no_prompt, "缺：%s" % (no_prompt or "无"))
    known = set("P_" + i for i in sp_ids) | COMMON_IDS | set("P_" + i for i in STRUCTURAL_IDS)
    stray = sorted(p for p in prompt_ids
                   if p not in known and not _BEAT_RE.match(p))
    c.check("没有未登记的段落 id", not stray, "多出：%s" % (stray or "无"))

    print("[5] 周墨八拍变体")
    beats = set("P_zm_%d" % i for i in range(1, 9))
    c.check("P_zm_1..8 齐全", beats <= prompt_ids,
            "缺：%s" % (sorted(beats - prompt_ids) or "无"))

    print("[6] look 不进 prompt")
    render = card.get("render", {})
    c.check("never_send 里有 look", "look" in (render.get("never_send") or []),
            "现在只有 %s" % (render.get("never_send") or []))
    c.check("default_fields 里没有 look",
            "look" not in (render.get("default_fields") or []),
            "现在是 %s" % (render.get("default_fields") or []))

    print("[7] 定性形容词没有混进示例字段")
    banned = card.get("banned_style", {}).get("adjectives") or []
    dirty = []
    for sid, s in speakers.items():
        for field in SCAN_FIELDS:
            for item in (s.get(field) or []):
                if not isinstance(item, str):
                    continue
                for word in banned:
                    if word in item:
                        dirty.append("%s.%s 含「%s」" % (sid, field, word))
    c.check("示例字段干净", not dirty, "；".join(dirty[:6]))

    print("")
    if c.fails:
        print("FAILED: %d 项没过 —— %s" % (len(c.fails), ", ".join(c.fails)))
        return 1
    print("all checks passed（%d 个 speaker，%d 个 define，提示词 %d 段）"
          % (len(sp_ids), len(def_ids), len(prompt_ids)))
    return 0


if __name__ == "__main__":
    if hasattr(sys.stdout, "reconfigure"):
        # PS 5.1 默认 GBK，中文输出会炸；这里钉死 utf-8
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.exit(main())
