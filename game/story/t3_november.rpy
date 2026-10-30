################################################################################
## T3 十一月「揭」—— 期中、家长会、旧琴房
##
## 骨架：固定拍 + 通用自由行动。数值 / Flag / 结局判定一律走 systems/stats.rpy，
## AI 只负责把固定拍的场景和台词写出来；AI 不可用就取 fallback 里的同拍模板。
## 本回合的 Flag：found_piano_room（旧琴房，TRUE 必需，脚本置位，AI 不许碰）。
################################################################################

image bg art_floor4      = Solid("#12161a")
image bg classroom_night = Solid("#181c22")
image bg office          = Solid("#1c1a16")

default t3_midterm_pass = False   # 期中是否到 50 分线
default t3_comfort      = ""      # talk / silent / press_key

label t3_november:

    $ start_month(3)

    ## 月初 · 期中复习
    scene bg classroom_day
    "十一月。后墙的倒计时牌翻到「期中」，白粉笔灰落在讲台边。"
    nar "周墨的练习册换成了最厚的那种，页边写满小字。"
    inner "（她一整节课笔尖都压在同一行上，没往下走。）"

    ## 固定 · 期中考试（数值判定不交给 AI）
    $ exam_roll()
    $ t3_midterm_pass = exam_pass("midterm")
    scene bg classroom_night
    if t3_midterm_pass:
        "〔期中 · 得分 [exam_score] · 过线〕"
    else:
        "〔期中 · 得分 [exam_score] · 没到线〕"

    ## 固定 · 家长会
    scene bg classroom_night
    call ai_play("t3_parent")
    $ mark_milestone_for_beat("t3_parent")

    ## 旧琴房（周 M2 的下半场，戏并进 T2 的主拍；这里只留脚本过场，不再单独调 AI）
    scene bg corridor_night
    "晚自习后，宿舍里没有她。我从三楼找到四楼。"
    $ set_flag("found_piano_room")
    scene bg art_floor4
    "门缝漏着光。她坐在琴前，左手按着一个按不下去的键。"
    "谱架翻到最后一页，页角卷了。她没哭出声。"
    menu:
        "说点什么，哪怕说不好。":
            $ t3_comfort = "talk"
        "站着，不说话。":
            $ t3_comfort = "silent"
        "蹲下去，帮她按住那个键。":
            $ t3_comfort = "press_key"
    if t3_comfort == "talk":
        "我张了几次嘴，说出来的话连自己都没记住。"
    elif t3_comfort == "press_key":
        "我蹲下去，替她按住那个按不下去的键。指节被琴键缝夹了一下，没敢出声。"
    else:
        "我在门口站着。她没让我走，也没让我进去。"

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T3 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本月结束。】"

    jump t4_december
