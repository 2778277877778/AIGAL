################################################################################
## T2 十月「藏」—— 骨架 + AI 演出
##
## 数值 / Flag / 结局判定一律不动，AI 只负责场景与台词的文字部分。
## 三个调用：
##   call ai_play("t2_welcome")   只演台词（固定拍，不给选项）
##   call ai_menu("t2_piano")     演完给选项，选中的分支 id 从 _return 取
##
## 预取按《运行时预算_v1.md》§2.1 的三条触发点放：
##   t2_piano 的选项点下之后 → 预取 t2_gala（这时才确定下一拍的 key 成不成立）
##   t2_call  的选项点下之后 → 预取 t2_free（自由时段 choice_path 恒空，窗口最长）
## 预取是后台跑的，不阻塞；取到缓存就命中，取不到就现场买或降级，剧本不用管。
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

    ## 月初 · 迎新晚会筹备（周墨拒绝上台）
    scene bg classroom_day
    call ai_play("t2_welcome")

    ## 固定 · 旧琴房（他撞见她弹琴）
    scene bg art_backstage
    call ai_menu("t2_piano")
    $ t2_piano_choice = _return or "reveal"

    # 选项点下的这一瞬间：下一拍的 choice_path 定了，key 才成立 —— 预取放这里
    $ aig.prefetch("t2_gala")

    # 两种反应都是「听见了琴」，Flag 只看这一点；分支文本留给后面的拍回指
    $ set_flag("heard_piano")

    ## 固定 · 迎新晚会（放录音伴奏，主持人夸伴奏）
    scene bg auditorium_night
    call ai_play("t2_gala")

    ## 固定 · 月考 —— 数值判定不动，AI 只写「过」或「没过」那一版
    scene bg classroom_day
    $ exam_roll()
    $ t2_monthly_pass = exam_pass("monthly")
    $ t2_exam_key = "pass" if t2_monthly_pass else "fail"
    $ t2_exam_note = "这次月考" + ("过了 35 分线。" if t2_monthly_pass else "没过 35 分线。")
    call ai_play("t2_exam", t2_exam_key, t2_exam_note)

    ## 固定 · 楼梯间电话（父亲打电话问数学为什么没满分）
    scene bg stairwell_night
    call ai_menu("t2_call")
    $ t2_call = _return or "stay"

    # 自由时段跟着就来，choice_path 恒空 —— 现在预取，窗口最长
    $ aig.prefetch("t2_free")

    # 他听见了这通电话，三种处理都算；具体怎么处理记在 t2_call
    $ set_flag("heard_call")

    ## 自由行动（T2 起艺术楼解锁）
    call free_actions

    ## 月末结算
    scene bg dorm_402
    "〔T2 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    "〔T2 结束 · T3「揭」待写〕"
    return
