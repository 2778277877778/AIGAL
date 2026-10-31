################################################################################
## T2 十月「藏」—— 骨架 + AI 演出
##
## 数值 / Flag / 结局判定一律不动，AI 只负责场景与台词的文字部分。
## 拍内选项一律由脚本的 menu 给（t2_piano / t2_call），AI 不产出选项、不产出 Flag。
## 调用只有一种：call ai_play("<拍 id>", <分支>, <既定事实>) —— 只演台词。
##
## 压拍（2026-10-30）：迎新筹备、撞见她弹琴、晚会录音伴奏合成一场 `t2_piano`
## （周 M2 的承载拍），旧 id `t2_welcome` / `t2_gala` 已从 beat 表与模板里删掉；
## 月考、楼梯间电话保留为月末结算拍。预取统一由 free_actions 末尾触发。
################################################################################

image bg art_backstage   = Solid("#1a1d22")
image bg auditorium_night = Solid("#12161b")
image bg stairwell_night = Solid("#15191e")

default t2_monthly_pass = False      # 第一次月考是否过线（线 35）
default t2_call = ""                 # stay / leave / water_only，楼梯间那三种处理
default t2_piano_choice = ""         # reveal / ignore，旧琴房那两种反应
default t2_exam_key = ""             # 月考那拍的变体 key（pass / fail）
default t2_exam_note = ""            # 交给 AI 的既定事实，不影响判定

label t2_october:

    $ start_month(2)

    ## 夏 M1（运动会报名）——脚本过场；内容待文案按夏线定稿
    scene bg classroom_day
    "运动会报名表传下来。八百米那栏，夏幸悠替我写了名字。"
    $ mark_milestone("xia", 1)

    ## 主拍 · 旧琴房（他把迎新晚会筹备、撞见她弹琴、晚会放录音伴奏并成一场）
    ## 选项由脚本给，AI 只写这一拍的台词——走向不能交给模型。
    scene bg art_backstage
    call ai_play("t2_piano", "", "同一晚三件事：合唱缺伴奏、她拒绝上台；主角在旧琴房撞见她弹琴，她只要求别说出去；晚会放录音伴奏，主持人夸伴奏，主角差点说漏嘴。")
    $ mark_milestone_for_beat("t2_piano")
    menu:
        "「我不会说。」":
            $ t2_piano_choice = "ignore"
        "「你弹得很好。」":
            $ t2_piano_choice = "reveal"

    # 两种反应都是「听见了琴」，Flag 只看这一点；分支文本留给后面的拍回指
    $ set_flag("heard_piano")

    ## 固定 · 月考 —— 分数由 exam_roll 算，不交给 AI 说
    scene bg classroom_day
    $ exam_roll()
    $ t2_monthly_pass = exam_pass("monthly")
    if t2_monthly_pass:
        "〔月考 · 得分 [exam_score] · 过线〕"
    else:
        "〔月考 · 得分 [exam_score] · 没到线〕"

    ## 固定 · 楼梯间电话（父亲打电话问数学为什么没满分）
    scene bg stairwell_night
    call ai_play("t2_call")
    menu:
        "过去问一句":
            $ t2_call = "stay"
        "走开，当没看见":
            $ t2_call = "leave"
        "放一瓶水在楼梯口":
            $ t2_call = "water_only"

    # 自由时段不调 AI 了（正文走 fallback 变体池），原来那条 prefetch("t2_free")
    # 现在是纯白烧一次调用加一个线程，已删。下个月第一拍的预取挪到 free_actions 末尾。

    # 他听见了这通电话，三种处理都算；具体怎么处理记在 t2_call
    $ set_flag("heard_call")

    ## 随机事件槽（60% 命中，抽不中就是纯自由行动）
    call event_slot

    ## 自由行动（T2 起艺术楼解锁）
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "〔T2 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    "〔T2 结束 · 十一月〕"

    jump t3_november
