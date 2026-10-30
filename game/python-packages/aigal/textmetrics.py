"""「每局不同」这条验收标准的度量工具。

口径（Chief 定的）：字符二元组 Jaccard。为什么不换别的：
- 长度差不行：同义改写往往等长，长度差会把「换了个说法」判成没变。
- 词袋不行：中文不分词，二元组够用，而且不用第三方库。
- 编辑距离不行：它是绝对量，两段 200 字和两段 20 字的阈值没法共用。

判读：Jaccard ≤ 0.4 算「真的换了说法」；> 0.4 说明在做同义改写，
两局读起来会是同一段。同义改写被抓出来是这套口径存在的理由，不是副作用。

纯标准库，不 import renpy，能离线跑（tests/selftest_diversity.py）。
"""


def _norm(text):
    """统一空白与大小写；标点保留——标点也在参与二元组，剥掉会让分数虚高。"""
    if not isinstance(text, str):
        return ""
    return "".join(ch for ch in text.strip().lower() if not ch.isspace())


def bigrams(text):
    s = _norm(text)
    if len(s) < 2:
        return set()
    return {s[i:i + 2] for i in range(len(s) - 1)}


def bigram_jaccard(a, b):
    """两段文本的字符二元组 Jaccard，0.0–1.0。两边都空算 1.0（没有任何差异）。"""
    A = bigrams(a)
    B = bigrams(b)
    if not A and not B:
        return 1.0
    if not A or not B:
        return 0.0
    return len(A & B) / float(len(A | B))


def join_lines(lines):
    """把一个 payload 的台词接成一整段，用来算拍与拍之间的差异。"""
    parts = []
    for ln in lines or ():
        if hasattr(ln, "get"):
            parts.append(ln.get("text") or "")
        else:
            parts.append(str(ln))
    return "\n".join(parts)


def pair_jaccard(a_lines, b_lines):
    return bigram_jaccard(join_lines(a_lines), join_lines(b_lines))


def text_shape(lines):
    """「说什么」的形状：行数 + speaker 集合。台词怎么变，这两样不许变。"""
    speakers = set()
    for ln in lines or ():
        speakers.add(ln.get("speaker") if hasattr(ln, "get") else None)
    return (len(lines or ()), tuple(sorted(s for s in speakers if s)))


def choice_shape(choices):
    """可用 action_key 集合。差异不许来自「多了一个选项」。"""
    keys = set()
    for c in choices or ():
        keys.add(c.get("action_key") if hasattr(c, "get") else None)
    return tuple(sorted(k for k in keys if k))


def same_shape(a_lines, a_choices, b_lines, b_choices):
    """返回 (bool, 说明)。"""
    sa, sb = text_shape(a_lines), text_shape(b_lines)
    ca, cb = choice_shape(a_choices), choice_shape(b_choices)
    if sa != sb:
        return False, "行数/speaker 变了：%r -> %r" % (sa, sb)
    if ca != cb:
        return False, "action_key 集合变了：%r -> %r" % (ca, cb)
    return True, ""
