################################################################################
## T4 十二月「亮」—— 艺术节、期末、元旦、寒假前
##
## 固定拍四个 + 自由行动。考试线走 exam_pass("final")，台词只演结果。
## Flag：art_fair（艺术节）、sheet_music（元旦手抄谱），两个都由脚本置位。
################################################################################

image bg gate_winter = Solid("#1a1d22")

default t4_final_pass = False   # 期末是否到 60 分线
default t4_speak      = ""      # speak / quiet
default t4_gift       = ""      # metronome / strings

label t4_december:

    $ start_month(4)

    ## 月初 · 艺术节筹备
    scene bg classroom_day
    "十二月。艺术节的通知贴在公告栏，班级节目是《送别》。"
    nar "伴奏那栏空着。报名表在讲台上放了三天，周墨没去填。"

    ## 固定 · 艺术节（关键选择：替不替她说话）
    $ set_flag("art_fair")
    scene bg auditorium_night
    call ai_play("t4_artfair")
    menu:
        "去跟主持人说清楚，伴奏是她弹的。":
            $ t4_speak = "speak"
        "什么也不说。":
            $ t4_speak = "quiet"
    if t4_speak == "speak":
        "散场后我在后台站了一会儿，跟主持人说，伴奏是她弹的。她不知道。"
    else:
        "我什么也没说。她把琴盖合上，又打开。"

    ## 固定 · 期末
    $ exam_roll()
    $ t4_final_pass = exam_pass("final")
    scene bg classroom_night
    call ai_play("t4_exam", "pass" if t4_final_pass else "fail", "这次期末" + ("过了 60 分线。" if t4_final_pass else "没到 60 分线。"))

    ## 固定 · 元旦（回赠什么）
    $ set_flag("sheet_music")
    scene bg classroom_night
    call ai_play("t4_newyear")
    menu:
        "把旧节拍器给她。":
            $ t4_gift = "metronome"
        "送一盒琴弦。":
            $ t4_gift = "strings"
    if t4_gift == "metronome":
        "那个节拍器是从旧货市场淘的。电池装反了，走得比实际快。"
    else:
        "琴弦是在文具店买的，包装上落了灰。我不会挑，随便拿了一盒。"

    ## 固定 · 寒假前（她父亲提分科）
    scene bg gate_winter
    call ai_play("t4_father")

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T4 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本学期最后一个月结束，寒假。】"

    jump t5_march
