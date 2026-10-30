"""二元组 Jaccard 的标定测试（不需要 Ren'Py）。

    python tests/selftest_diversity.py

这套口径要同时满足两件事，缺一件就白定：
  1. 真的换了说法的两段，分数必须 ≤ 0.4，否则「每局不同」永远判红。
  2. 同义改写的两段，分数必须 > 0.4，否则它拦不住「两局读起来一样」——
     这正是这条断言存在的理由。

样例按本项目 T2 旧琴房那一拍写：同一件事（他推门、她停下、她要求别说出去），
两种说法；以及同一句话的两种同义改写。
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..", "game", "python-packages")))

import aigal.textmetrics as M  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s   %s" % (name, detail))
        FAILS.append(name)


## 同一拍、两种说法：事件一样，句子、用词、句法都换了。
## B 的字数刻意跟 A 咬得很近（差 2 个字），用来证明「长度差」这个判据在这里是瞎的。
A = [
    {"speaker": "inner", "text": "（门轴响了一声，琴声就停了。）"},
    {"speaker": "zm", "text": "……你没听见吧。"},
    {"speaker": "mc", "text": "我、我什么都没听见。"},
]
B = [
    {"speaker": "inner", "text": "（她的手指悬在琴键，没有落下。）"},
    {"speaker": "zm", "text": "……别跟别人讲。"},
    {"speaker": "mc", "text": "那个……找作业本。"},
]

## 同义改写：同一个意思换几个词，这种要被抓出来
C = [
    {"speaker": "inner", "text": "（门被推开的那一刻，琴声停下了。）"},
    {"speaker": "zm", "text": "你听见了吧。"},
    {"speaker": "mc", "text": "我什么都没有听见。"},
]
D = [
    {"speaker": "inner", "text": "（门被推开的那一刻，琴声停下来了。）"},
    {"speaker": "zm", "text": "你听见了吧。"},
    {"speaker": "mc", "text": "我什么都没有听见。"},
]


def case_identical():
    check("同一段自己比 = 1.0", abs(M.pair_jaccard(A, A) - 1.0) < 1e-9)


def case_real_variation():
    j = M.pair_jaccard(A, B)
    check("真·两种说法 ≤ 0.4", j <= 0.4, "实际 %.3f" % j)
    print("        jaccard(A,B) = %.3f" % j)


def case_paraphrase_caught():
    j = M.pair_jaccard(C, D)
    check("同义改写 > 0.4（该拦）", j > 0.4, "实际 %.3f" % j)
    print("        jaccard(C,D) = %.3f" % j)


def case_length_trap():
    """长度差在这里是瞎的：A/B 内容几乎完全不同，字数只差 2 个。

    拿长度差当判据会得出「没变」，把一条合格输出判红；二元组给 0.03，判对。
    这就是当初不用长度差的原因。
    """
    la, lb = len(M.join_lines(A)), len(M.join_lines(B))
    gap = abs(la - lb) / float(max(la, lb))
    check("A/B 字数差 < 10%", gap < 0.10, "%d vs %d（%.1f%%）" % (la, lb, gap * 100))
    j = M.pair_jaccard(A, B)
    check("字数相同但内容不同", j <= 0.4, "jaccard = %.3f" % j)


def case_shape():
    ok, why = M.same_shape(A, [{"text": "说破", "action_key": "reveal"}],
                          B, [{"text": "装没看见", "action_key": "reveal"}])
    check("不同说法、同形状", ok, why)

    extra = list(B) + [{"speaker": "zzb", "text": "兄弟你在这儿干嘛。"}]
    ok2, _ = M.same_shape(A, [{"text": "x", "action_key": "reveal"}],
                          extra, [{"text": "y", "action_key": "reveal"}])
    check("多一行能被抓到", not ok2)

    ok3, _ = M.same_shape(A, [{"text": "x", "action_key": "reveal"}],
                          B, [{"text": "y", "action_key": "ignore"}])
    check("多/少一个 action_key 能被抓到", not ok3)

    ok4, _ = M.same_shape(A, [], B, [])
    check("speaker 集合变了能被抓到", M.text_shape(A) != M.text_shape(
        list(B) + [{"speaker": "zzb", "text": "喂"}]))
    check("A/B 的 speaker 集合本来就一致", M.text_shape(A) == M.text_shape(B))


def case_degenerate():
    check("两边都空 = 1.0", M.bigram_jaccard("", "") == 1.0)
    check("一边空 = 0.0", M.bigram_jaccard("", "嗯。") == 0.0)
    check("None 不炸", M.bigram_jaccard(None, None) == 1.0)
    check("单字不成二元组", M.bigrams("嗯") == set())
    check("空白不影响", M.bigram_jaccard("他 推 开 门", "他推开门") == 1.0)


def main():
    print("textmetrics · 二元组 Jaccard 标定（阈值 0.4）")
    for fn in (case_identical, case_real_variation, case_paraphrase_caught,
               case_length_trap, case_shape, case_degenerate):
        print(fn.__name__)
        fn()
    print("")
    if FAILS:
        print("FAILED: %d 项 —— %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("OK: 全部通过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
