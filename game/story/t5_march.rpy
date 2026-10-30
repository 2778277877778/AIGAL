################################################################################
## T5 三月「护」—— 琴房清空、搬谱子、曾老师、母亲电话
##
## 固定拍三个 + 自由行动。piano_crisis（搬谱子）由脚本置位，AI 不许碰。
## 搬谱子那一拍给三个选项，选完的分支只影响后面的台词，不额外改数值。
################################################################################

default t5_choice = ""   # move / teacher / stop

label t5_march:

    $ start_month(5)

    ## 月初 · 开学、分科摸底、琴房清空通知
    scene bg classroom_day
    "三月，回南天。走廊的墙上一层水汽，扶手摸上去是湿的。"
    nar "艺术楼四楼贴出一张通知：琴房改储物间，东西月底前清走。"
    inner "（她站在通知前面看了很久，看完把书包带子往上提了一下。）"

    ## 固定 · 搬谱子（关键选择：帮她搬 / 找曾老师 / 劝她别弹了）
    $ set_flag("piano_crisis")
    scene bg art_floor4
    call ai_play("t5_move")
    menu:
        "蹲下去，把谱子一张张捡起来。":
            $ t5_choice = "move"
        "拉她去找曾老师。":
            $ t5_choice = "teacher"
        "劝她，别弹了。":
            $ t5_choice = "stop"
    if t5_choice == "teacher":
        "我拉着她去了曾老师办公室。她一路没说话，到门口才把手抽回去。"
    elif t5_choice == "stop":
        "我说，要不……先别弹了。她把纸箱放下，没看我。"
    else:
        "我蹲下去捡谱子。纸边割手，我没出声。"

    ## 固定 · 曾老师（社团申请 / 琴挪到礼堂后台）
    scene bg office
    call ai_play("t5_office", t5_choice)

    ## 固定 · 母亲电话
    scene bg stairwell_night
    call ai_play("t5_mother")

    ## 自由行动
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "【T5 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]。】"
    "【本月结束。】"

    jump t6_april
