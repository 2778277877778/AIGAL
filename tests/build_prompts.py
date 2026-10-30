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


def emit(paras):
    out = io.StringIO()
    out.write("## 自动生成，别手改。\n")
    out.write("## 源文件：高中校园物语/提示词_角色_v1.md\n")
    out.write("## 重新生成：python tests/build_prompts.py\n")
    out.write("## prompt 内容一变，schema_core.PROMPT_VER 要一起升，否则旧缓存会顶掉新提示词。\n\n")
    out.write("init -4 python in aig:\n\n")
    out.write("    PARAS = {\n")
    for pid in sorted(paras):
        out.write("        %r: %r,\n" % (pid, paras[pid]))
    out.write("    }\n")
    return out.getvalue()


def main():
    if not os.path.exists(SRC):
        sys.stderr.write("找不到源文件：%s\n" % SRC)
        return 1
    with io.open(SRC, encoding="utf-8") as f:
        paras = parse(f.read())
    if not paras:
        sys.stderr.write("一个段落都没解析出来，检查标记格式\n")
        return 1
    with io.open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write(emit(paras))
    common = [p for p in paras if p.count("_") == 1]
    print("写出 %s：%d 个段落" % (OUT, len(paras)))
    print("  公共段：%s" % ", ".join(sorted(p for p in paras if p[2:3] in "ABCD")))
    print("  结局套：%s" % ", ".join(sorted(p for p in paras if p.endswith("_ending"))))
    print("  八拍变体：%s" % ", ".join(sorted(p for p in paras if re.match(r"P_zm_\d", p))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
