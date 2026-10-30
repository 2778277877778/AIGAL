################################################################################
## T6 四月「光」—— 运动会、八百米、音乐社成立
##
## 固定拍三个 + 自由行动。club（音乐社成立）由脚本置位。
## 报名那一拍给三个选项：join / help / no，只影响台词与后文细节。
################################################################################

image bg music_room = Solid("#20241f")

default t6_join = ""   # join / help / no

label t6_april:

    $ start_month(6)

    ## 月初 · 运动会报名
    scene bg classroom_day
    "四月。运动会报名表传到我手里的时候，八百米那栏已经写着我的名字。"
    inner "（周子博的字。他连「本人签字」都替我画好了。）"

    ## 固定 · 开幕式（礼堂后台那台琴推出来）
    scene bg auditorium_night
    call ai_play("t6_sports")

    ## 固定 · 八百米
    scene bg playground_heat
    call ai_play("t6_run")

    ## 固定 · 音乐社成立（关键选择：报名 / 只帮忙 / 不参与）
    $ set_flag("club")
    scene bg music_room
    call ai_play("t6_club")
    menu:
        "第一个在报名表上签字。":
            $ t6_join = "join"
        "只帮忙搬椅子，不签字。":
            $ t6_join = "help"
        "不参加。":
            $ t6_join = "no"
    if t6_join == "join":
        "报名表上我把名字写在第一行。写完才发现，手心里全是汗。"
    elif t6_join == "no":
        "我没报名。回教室的路上，周子博问我为什么不报，我说没时间。"
    else:
        "我帮着搬了两趟椅子，没在表上签字。"

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T6 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本月结束。】"

    jump t7_may
