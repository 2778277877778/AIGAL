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

    ## 温 M1（第一次正面说话）——脚本过场；内容待文案按温线定稿
    "艺术节后台，温以宁第一次正面跟我说话：她问我借一支笔。"
    $ mark_milestone("x", 1)

    ## 主拍 · 艺术节（元旦回礼、寒假前父亲提分科并进这一拍的事实清单）
    $ set_flag("art_fair")
    scene bg auditorium_night
    call ai_play("t4_artfair", "", "艺术节伴奏是她弹的、名字没报、她父亲没来；元旦她送手抄谱，他回赠旧节拍器（电池装反，走得比实际快）；寒假前父亲在校门口提学医、物化生。")
    $ mark_milestone_for_beat("t4_artfair")
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
    if t4_final_pass:
        "〔期末 · 得分 [exam_score] · 过线〕"
    else:
        "〔期末 · 得分 [exam_score] · 没到线〕"

    ## 元旦回赠（选项保留，台词并进上面的主拍）
    $ set_flag("sheet_music")
    menu:
        "把旧节拍器给她。":
            $ t4_gift = "metronome"
        "送一盒琴弦。":
            $ t4_gift = "strings"
    if t4_gift == "metronome":
        "那个节拍器是从旧货市场淘的。电池装反了，走得比实际快。"
    else:
        "琴弦是在文具店买的，包装上落了灰。我不会挑，随便拿了一盒。"

    ## 随机事件槽（60% 命中，抽不中就是纯自由行动）
    call event_slot

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T4 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本学期最后一个月结束，寒假。】"

    jump t5_march
