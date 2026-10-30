################################################################################
## T7 五月「野」—— 研学、城市音乐厅、酒店走廊夜谈
##
## 固定拍两个 + 自由行动。music_hall（音乐厅）由脚本置位。
## 夜谈那一拍给三个选项：support / persuade / silent，只改台词，不加 Flag。
################################################################################

image bg bus_highway     = Solid("#242a2e")
image bg concert_hall    = Solid("#15171c")
image bg hotel_corridor  = Solid("#191c21")

default t7_answer = ""   # support / persuade / silent

label t7_may:

    $ start_month(7)

    ## 月初 · 研学通知、大巴
    scene bg bus_highway
    "五月。研学，大巴开了两个小时，车窗上全是灰。"
    nar "周墨坐在靠窗那排，一路没睡，手里捏着学校发的那张行程单。"

    ## 主拍 · 城市音乐厅（酒店走廊夜谈并进这一拍的事实清单）
    $ set_flag("music_hall")
    scene bg concert_hall
    call ai_play("t7_hall", "", "她在音乐厅门口盯着节目单右下角那行小字站了很久；夜里在酒店走廊说她想学音乐、父亲要她学医，问「我是不是很自私」。")
    $ mark_milestone_for_beat("t7_hall")

    ## 夜谈的选择（台词并进上面的主拍）
    scene bg hotel_corridor
    menu:
        "「你弹琴的时候，不像在考试。」":
            $ t7_answer = "support"
        "「你爸也是为你好。」":
            $ t7_answer = "persuade"
        "什么也说不出来。":
            $ t7_answer = "silent"
    if t7_answer == "support":
        "我说，你弹琴的时候，不像在考试。"
    elif t7_answer == "persuade":
        "我说，你爸也是为你好。说完我自己都不太信。"
    else:
        "我什么也没说。她等了一会儿，转身回了房间。"

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T7 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本月结束。】"

    jump t8_june
