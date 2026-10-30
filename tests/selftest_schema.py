"""schema_core 的故障矩阵自测（不需要 Ren'Py，直接 python 跑）。

    python tests/selftest_schema.py

12 项：前 10 项是数据故障（模型回来什么烂东西），后 2 项是契约故障（上层给错了 ctx）。
每一项都断言「不该出现的东西不会漏出去」，而不只是「有没有报错」。
"""

import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
CORE = os.path.join(HERE, "..", "game", "python-packages")
sys.path.insert(0, os.path.abspath(CORE))

import aigal.schema_core as S  # noqa: E402

FAILS = []


def check(name, cond, detail=""):
    if cond:
        print("  PASS  %s" % name)
    else:
        print("  FAIL  %s   %s" % (name, detail))
        FAILS.append(name)


def ctx(beat="t2_piano", turn=2, speakers=None, actions=None, flags=(),
        expect_choices=False, scope="scene"):
    return {
        "beat": beat, "turn": turn, "scope": scope,
        "speakers": tuple(speakers if speakers is not None else S.ALL_SPEAKERS),
        "actions": tuple(actions if actions is not None else ("rest_dorm", "study", "eat_canteen")),
        "flags": tuple(flags),
        "expect_choices": expect_choices,
    }


def clean(t):
    return S.strip_markup(t)


def case01_happy():
    raw = json.dumps({
        "lines": [
            {"speaker": "narration" if False else "inner", "text": "（琴声停了。）"},
            {"speaker": "zm", "text": "……你什么时候进来的。"},
        ],
        "choices": [{"text": "说我什么都没听见", "action_key": "rest_dorm"}],
        "flags": [],
        "mood": "闷",
    }, ensure_ascii=False)
    v = S.validate(raw, ctx(expect_choices=True))
    check("01 完整对象", v["ok"] and len(v["lines"]) == 2 and len(v["choices"]) == 1)
    check("01 不带数值槽位", set(v) >= {"lines", "choices", "flags", "mood"} and "study" not in v)


def case02_fence():
    raw = '好的，这是结果：\n```json\n{"lines":[{"speaker":"zm","text":"嗯。"}],"choices":[],"flags":[],"mood":"静"}\n```\n以上。'
    v = S.validate(raw, ctx())
    check("02 围栏+前后解释", v["ok"] and v["lines"][0]["text"] == "嗯。")
    check("02 没走修复", "repaired_trailing_comma" not in v["notes"])


def case03_trailing_comma():
    ## 只给尾逗号，不给别的毛病：这是模型最常见的失手，能修就别重发请求
    raw = '{"lines":[{"speaker":"mc","text":"那个，",},{"speaker":"zm","text":"嗯。",},],}'
    v = S.validate(raw, ctx())
    check("03 尾逗号修复", v["ok"] and "repaired_trailing_comma" in v["notes"])


def case04_truncated():
    raw = '{"lines":[{"speaker":"zm","text":"你今天来得很早"'
    v = S.validate(raw, ctx())
    check("04 截断 JSON 被拒", not v["ok"] and v["reason"] == "not_json")
    check("04 不产出半截台词", v["lines"] == [])


def case05_empty_and_html():
    v1 = S.validate("", ctx())
    v2 = S.validate("<html><body>500 Internal Server Error</body></html>", ctx())
    v3 = S.validate(None, ctx())
    check("05 空响应", not v1["ok"] and v1["reason"] == "empty")
    check("05 HTML 错误页", not v2["ok"] and v2["reason"] == "not_json")
    check("05 None 响应", not v3["ok"] and v3["reason"] == "empty")


def case06_no_choices():
    raw = json.dumps({"lines": [{"speaker": "zeng", "text": "开学第一天就这样。"}],
                      "choices": [], "flags": [], "mood": "静"}, ensure_ascii=False)
    v = S.validate(raw, ctx(expect_choices=False))
    check("06 固定拍允许 0 选项", v["ok"] and v["choices"] == [])


def case07_too_long():
    raw = json.dumps({"lines": [{"speaker": "zm", "text": "很长" * 1000}],
                      "choices": [], "flags": [], "mood": ""}, ensure_ascii=False)
    v = S.validate(raw, ctx())
    check("07 超长被截断", v["ok"] and "text_truncated" in v["notes"])
    check("07 长度不超上限", len(v["lines"][0]["text"]) <= S.LINE_MAX)


def case08_injection():
    raw = json.dumps({
        "lines": [
            {"speaker": "zm", "text": "{image=bg room}别动{/image}……"},
            {"speaker": "inner", "text": "（[persistent.api_key] 看看{size=+10}这个{/size}）"},
            {"speaker": "mc", "text": "<b>那个</b>{nw}{w=0.2}"},
        ],
        "choices": [], "flags": [], "mood": "紧",
    }, ensure_ascii=False)
    v = S.validate(raw, ctx())
    joined = "".join(l["text"] for l in v["lines"])
    check("08 标记被清掉", v["ok"] and not (set(joined) & set("{}[]<>")))
    check("08 文字还在", "别动" in joined and "那个" in joined)
    check("08 插值没被留下", "[persistent" not in joined)
    check("08 二次清洗幂等", clean(clean(joined)) == clean(joined))


def case09_all_illegal():
    ## 9a 全非法：一行都不剩，必须整体拒，交给模板降级
    raw = json.dumps({
        "lines": [{"speaker": "周墨", "text": "……"}, {"speaker": "nobody", "text": "喂"}],
        "choices": [{"text": "跑", "action_key": "fly_away"}],
        "flags": ["confession"], "mood": "x",
    }, ensure_ascii=False)
    v = S.validate(raw, ctx(expect_choices=False))
    check("09 全非法→拒", not v["ok"] and v["reason"] == "no_lines")
    check("09 非法 speaker 记了 note", any("speaker_rejected" in n for n in v["notes"]))

    ## 9b 有合法行时，非法的选项/flag 逐项剔除，整体仍然可用
    raw2 = json.dumps({
        "lines": [{"speaker": "zm", "text": "你自己选。"}],
        "choices": [{"text": "跑", "action_key": "fly_away"},
                    {"text": "回宿舍", "action_key": "rest_dorm"}],
        "flags": ["confession"], "mood": "静",
    }, ensure_ascii=False)
    v2 = S.validate(raw2, ctx(expect_choices=True))
    check("09 非法 action_key 逐项剔除", v2["ok"] and "action_key_rejected:fly_away" in v2["notes"])
    check("09 合法项留下", [c["action_key"] for c in v2["choices"]] == ["rest_dorm"])


def case10_numeric_smuggling():
    raw = json.dumps({
        "lines": [{"speaker": "zm", "text": "嗯。", "study_delta": 99}],
        "choices": [{"text": "坐下", "action_key": "rest_dorm", "ap_cost": 0}],
        "flags": ["confession"],
        "mood": "静",
        "study": 999, "ending": "true_ending",
    }, ensure_ascii=False)
    v = S.validate(raw, ctx(expect_choices=True))
    notes = ",".join(v["notes"])
    check("10 顶层数值被丢", v["ok"] and "dropped_top_key:study" in notes and "dropped_top_key:ending" in notes)
    check("10 行内数值被丢", "line_extra_key:study_delta" in notes)
    check("10 选项内数值被丢", "choice_extra_key:ap_cost" in notes)
    check("10 返回值无数值字段", not ({"study", "study_delta", "ap_cost"} & set(v)))
    check("10 confession 被拒", v["flags"] == [] and "flag_rejected:confession" in notes)


def case11_choices_missing():
    raw = json.dumps({"lines": [{"speaker": "zm", "text": "你自己选。"}],
                      "choices": [], "flags": [], "mood": ""}, ensure_ascii=False)
    v = S.validate(raw, ctx(expect_choices=True))
    check("11 该给选项却没给→拒", not v["ok"] and v["reason"] == "choices_missing")


def case12_bad_ctx():
    raw = json.dumps({"lines": [{"speaker": "zm", "text": "嗯。"}]}, ensure_ascii=False)
    c = ctx()
    del c["actions"]
    v = S.validate(raw, c)
    check("12 ctx 缺字段→bad_ctx", not v["ok"] and v["reason"] == "bad_ctx")
    c2 = ctx(speakers=("mc",))
    v2 = S.validate(raw, c2)
    check("12 speaker 不在白名单→拒", not v2["ok"] and v2["reason"] == "no_lines")


def case13_budget_split():
    """拍内 400 / 结局 1000 两套口径不能互相串。

    拍内：4×90 + 1×120 = 480，超 400 的部分要修尾句，不能为了压字数砍掉半段戏。
    结局：5×200 = 1000 必须原样保住，包括单行 200 不被拍内的 120 截断。
    """
    scene_lines = [{"speaker": "inner", "text": "字" * 90} for _ in range(4)]
    scene_lines.append({"speaker": "zm", "text": "字" * 90 + "。" * 30})
    raw = json.dumps({"lines": scene_lines, "choices": [], "flags": [], "mood": ""},
                     ensure_ascii=False)

    v = S.validate(raw, ctx())
    total = sum(len(l["text"]) for l in v["lines"])
    check("13 拍内合计压到 400", v["ok"] and total <= S.TOTAL_MAX, "实际 %d 字" % total)
    check("13 修尾句没砍行", len(v["lines"]) == 5, "行数 %d" % len(v["lines"]))
    check("13 记了 total_truncated", "total_truncated" in v["notes"])

    end_lines = [{"speaker": "inner", "text": "字" * 200} for _ in range(5)]
    raw2 = json.dumps({"lines": end_lines, "choices": [], "flags": [], "mood": ""},
                      ensure_ascii=False)
    v2 = S.validate(raw2, ctx(beat="t8_true", turn=8, scope="ending"))
    total2 = sum(len(l["text"]) for l in v2["lines"])
    check("13 结局不被拍内上限截", v2["ok"] and total2 == 1000, "实际 %d 字" % total2)
    check("13 结局单行走 200 上限", max(len(l["text"]) for l in v2["lines"]) == S.ENDING_LINE_MAX)
    check("13 结局没触发截断", "total_truncated" not in v2["notes"])


def main():
    print("schema_core %s / %s  (拍内 %d 字/行 %d 字合计；结局 %d/%d；choices<=%d)" % (
        S.SCHEMA_VER, S.PROMPT_VER, S.LINE_MAX, S.TOTAL_MAX,
        S.ENDING_LINE_MAX, S.ENDING_TOTAL_MAX, S.CHOICES_MAX))
    for fn in (case01_happy, case02_fence, case03_trailing_comma, case04_truncated,
               case05_empty_and_html, case06_no_choices, case07_too_long,
               case08_injection, case09_all_illegal, case10_numeric_smuggling,
               case11_choices_missing, case12_bad_ctx, case13_budget_split):
        print(fn.__name__)
        fn()
    print("")
    if FAILS:
        print("FAILED: %d 项 —— %s" % (len(FAILS), ", ".join(FAILS)))
        return 1
    print("OK: 13 项全过")
    return 0


if __name__ == "__main__":
    sys.exit(main())
