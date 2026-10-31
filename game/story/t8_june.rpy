################################################################################
## T8 六月「选」—— 学年期末、选科、分班、结局
##
## 判定链全部在 systems/stats.rpy：exam_pass("yearly") / true_ending() / end_variant()。
## 这一拍脚本只做三件事：置 Flag、把既定事实交给 AI、按判定调对应结局拍。
##   subject_support  选科时站她这边
##   same_subject     自己也填史地政
##   confession       告白（TRUE 的台词分支，不进六个 TRUE Flag）
################################################################################

image bg end_card = Solid("#000000")

default t8_yearly_pass = False
default t8_support = ""    # support / against / silent
default t8_form    = ""    # same / different
default t8_confess = ""    # yes / no

label t8_june:

    $ start_month(8)

    ## 月初 · 期末复习
    scene bg classroom_day
    "六月。倒计时牌上的数字变成了两位数。"
    nar "周墨的桌子上多了一摞招生简章，压在最下面那本，露出「医学」两个字。"

    ## 温 M2（撞见另一面）——脚本过场；内容待文案按温线定稿
    "放学后我在图书馆后门撞见温以宁。她把手里的东西往身后藏了一下。"
    $ mark_milestone("x", 2)

    ## 固定 · 学年期末
    $ exam_roll()
    $ t8_yearly_pass = exam_pass("yearly")
    $ t8_yearly_line = exam_line("yearly")
    scene bg classroom_night
    if t8_yearly_pass:
        "〔学年期末 · 得分 [exam_score] · 过 [t8_yearly_line] 分线〕"
    else:
        "〔学年期末 · 得分 [exam_score] · 没到 [t8_yearly_line] 分线〕"

    ## 主拍 · 选科（她做出选择那一场并进这一拍的事实清单）
    scene bg classroom_night
    call ai_play("t8_subject", "", "选科表发下来，她在「史地政」那栏停了很久；父亲电话里要物化生，母亲说让她自己选；她第一次说「我想试一次」，填了史地政。")
    $ mark_milestone_for_beat("t8_subject")
    menu:
        "「你想弹就弹。」":
            $ t8_support = "support"
        "「你爸说得也对。」":
            $ t8_support = "against"
        "什么也不说。":
            $ t8_support = "silent"
    if t8_support == "support":
        $ set_flag("subject_support")
        "我说，你想弹就弹。她没抬头，笔尖在「史地政」上停了一下。"
    elif t8_support == "against":
        "我说，你爸说得也对。她把笔帽套上，又拔下来。"
    else:
        "我什么也没说。"

    ## 主角自己的表
    call ai_play("t8_form")
    $ mark_milestone_for_beat("t8_form")
    menu:
        "跟她填一样的（史地政）。":
            $ t8_form = "same"
        "按自己的打算填（物化生）。":
            $ t8_form = "different"
    if t8_form == "same":
        $ set_flag("same_subject")
        "我在自己的表上也填了史地政。"
    else:
        "我按自己的打算填了物化生。交表的时候，她在讲台左边第三摞前面站着。"

    ## 告白（不进六个 TRUE Flag，只决定结局台词）
    menu:
        "在分班名单贴出来之前，叫住她。":
            $ t8_confess = "yes"
            $ set_flag("confession")
            "我在走廊尽头叫了她的名字。她回过头。"
        "什么也没说。":
            $ t8_confess = "no"

    ## 随机事件槽（60% 命中，抽不中就是纯自由行动）
    call event_slot

    ## 自由行动（T8 只有 2 AP）
    call free_actions

    ## 月末结算（高一结束，进 T9；结局已移到 T36）
    scene bg dorm_402
    "〔T8 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    "〔高一结束。〕"

    jump t9_may
