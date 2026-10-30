################################################################################
## T9–T36 —— 第二、三学年（新日历：T9=5 月 … T34=6 月，暑假为短过场）
##
## 每格骨架固定（《剧情大纲_三年_v1.md》§5.2 五）：
##   月初短场景 → 主线拍（若有）→ 事件槽（掷中才播）→ 自由行动 → 月末结算
## 短过场只有 1 屏文字 + 结算，不接 ai_play、不抽事件、不给选项。
## T22 月末调一次 lock_route()；T34 是高考（只掷一次）；T36 进结局。
## 旧 T5–T8 的 label 名不改（入口引用），从 T9 起按新日历命名。
################################################################################

label t9_may:
    $ start_month(9)
    scene bg classroom_day
    "五月。天气开始热，后排的人把窗开到最大。"
    scene bg classroom_day
    call ai_play("t9_injury")
    $ mark_milestone_for_beat("t9_injury")
    call free_actions
    scene bg dorm_402
    "〔T9 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t10_june


label t10_june:
    $ start_month(10)
    scene bg classroom_day
    "六月。期末复习，教室的灯开到很晚。"
    scene bg classroom_night
    call ai_play("t10_subject")
    $ mark_milestone_for_beat("t10_subject")
    $ exam_roll()
    $ _pass = exam_pass("final")
    if _pass:
        "〔期末 · 得分 [exam_score] · 过线〕"
    else:
        "〔期末 · 得分 [exam_score] · 没到线〕"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T10 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t11_summer


label t11_summer:
    $ start_month(11)
    $ ap = 0
    scene bg dorm_402
    "七月。暑假。宿舍楼里只剩一半人。"
    "〔暑假 · 学习 [study]，压力 [stress]〕"
    jump t12_summer_end


label t12_summer_end:
    $ start_month(12)
    $ ap = 0
    scene bg school_gate_rain
    "八月末。校门口的栾树还是绿的，蝉叫得比去年小。"
    "〔暑假结束 · 学习 [study]，压力 [stress]〕"
    jump t13_september


label t13_september:
    $ start_month(13)
    scene bg classroom_day
    "九月。高二开学，教室换到了三楼。"
    scene bg auditorium_night
    call ai_play("t13_artfair")
    $ mark_milestone_for_beat("t13_artfair")
    call free_actions
    scene bg dorm_402
    "〔T13 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t14_october


label t14_october:
    $ start_month(14)
    scene bg classroom_day
    "十月。体育班的名单贴出来了。"
    scene bg auditorium_night
    call ai_play("t14_coach")
    $ mark_milestone_for_beat("t14_coach")
    $ exam_roll()
    $ _pass = exam_pass("monthly")
    if _pass:
        "〔月考 · 得分 [exam_score] · 过线〕"
    else:
        "〔月考 · 得分 [exam_score] · 没到线〕"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T14 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t15_november


label t15_november:
    $ start_month(15)
    scene bg classroom_day
    "十一月。期中周的走廊，连脚步声都轻。"
    scene bg classroom_day
    call ai_play("t15_ask")
    $ mark_milestone_for_beat("t15_ask")
    $ exam_roll()
    $ _pass = exam_pass("midterm")
    if _pass:
        "〔期中 · 得分 [exam_score] · 过线〕"
    else:
        "〔期中 · 得分 [exam_score] · 没到线〕"
    call free_actions
    scene bg dorm_402
    "〔T15 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t16_december


label t16_december:
    $ start_month(16)
    scene bg classroom_day
    "十二月。天冷下来，走廊的窗上开始有雾。"
    scene bg classroom_night
    call ai_play("t16_mother")
    $ mark_milestone_for_beat("t16_mother")
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T16 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t17_january


label t17_january:
    $ start_month(17)
    scene bg classroom_day
    "一月。家长会。"
    scene bg classroom_night
    call ai_play("t17_parent")
    $ mark_milestone_for_beat("t17_parent")
    $ exam_roll()
    $ _pass = exam_pass("final")
    if _pass:
        "〔期末 · 得分 [exam_score] · 过线〕"
    else:
        "〔期末 · 得分 [exam_score] · 没到线〕"
    call free_actions
    scene bg dorm_402
    "〔T17 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t18_february


label t18_february:
    $ start_month(18)
    scene bg classroom_day
    "二月。寒假短，回来的时候，她的座位空了一天。"
    scene bg corridor_night
    call ai_play("t18_half")
    $ mark_milestone_for_beat("t18_half")
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T18 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t19_march


label t19_march:
    $ start_month(19)
    scene bg classroom_day
    "三月。艺术楼四楼的门牌换了。"
    scene bg music_room
    call ai_play("t19_club")
    $ mark_milestone_for_beat("t19_club")
    call free_actions
    scene bg dorm_402
    "〔T19 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t20_april


label t20_april:
    $ start_month(20)
    scene bg classroom_day
    "四月。运动会报名表又传下来了。"
    scene bg playground_heat
    call ai_play("t20_quit")
    $ mark_milestone_for_beat("t20_quit")
    $ exam_roll()
    $ _pass = exam_pass("monthly")
    if _pass:
        "〔月考 · 得分 [exam_score] · 过线〕"
    else:
        "〔月考 · 得分 [exam_score] · 没到线〕"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T20 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t21_may


label t21_may:
    $ start_month(21)
    scene bg classroom_day
    "五月。她的桌上多了一张外地的招生简章。"
    scene bg corridor_night
    call ai_play("t21_transfer")
    $ mark_milestone_for_beat("t21_transfer")
    call free_actions
    scene bg dorm_402
    "〔T21 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t22_june


label t22_june:
    $ start_month(22)
    scene bg classroom_day
    "六月。高二的最后一个月。"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T22 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    $ _r = lock_route()
    "〔这一年的关系锁定：[_r]〕"
    jump t23_summer


label t23_summer:
    $ start_month(23)
    $ ap = 0
    scene bg dorm_402
    "七月。高三补课前的最后一个暑假。"
    "〔暑假 · 学习 [study]，压力 [stress]〕"
    jump t24_summer_end


label t24_summer_end:
    $ start_month(24)
    $ ap = 0
    scene bg school_gate_rain
    "八月末。教学楼挂了新的横幅。"
    "〔暑假结束 · 学习 [study]，压力 [stress]〕"
    jump t25_september


label t25_september:
    $ start_month(25)
    scene bg classroom_day
    "九月。高三。黑板旁边多了一块倒计时牌。"
    scene bg concert_hall
    call ai_play("t25_hall")
    $ mark_milestone_for_beat("t25_hall")
    call free_actions
    scene bg dorm_402
    "〔T25 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t26_october


label t26_october:
    $ start_month(26)
    scene bg classroom_day
    "十月。她的桌上压着一张体育单招的报名表。"
    scene bg classroom_day
    call ai_play("t26_entry")
    $ mark_milestone_for_beat("t26_entry")
    $ exam_roll()
    $ _pass = exam_pass("monthly")
    if _pass:
        "〔月考 · 得分 [exam_score] · 过线〕"
    else:
        "〔月考 · 得分 [exam_score] · 没到线〕"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T26 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t27_november


label t27_november:
    $ start_month(27)
    scene bg classroom_day
    "十一月。期中的卷子比往年厚。"
    scene bg corridor_night
    call ai_play("t27_watch")
    $ mark_milestone_for_beat("t27_watch")
    $ exam_roll()
    $ _pass = exam_pass("midterm")
    if _pass:
        "〔期中 · 得分 [exam_score] · 过线〕"
    else:
        "〔期中 · 得分 [exam_score] · 没到线〕"
    call free_actions
    scene bg dorm_402
    "〔T27 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t28_december


label t28_december:
    $ start_month(28)
    scene bg classroom_day
    "十二月。志愿表的事开始有人问。"
    scene bg classroom_night
    call ai_play("t28_form")
    $ mark_milestone_for_beat("t28_form")
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T28 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t29_january


label t29_january:
    $ start_month(29)
    scene bg classroom_day
    "一月。单招考试在另一个城市。"
    scene bg classroom_night
    call ai_play("t29_exam")
    $ mark_milestone_for_beat("t29_exam")
    $ exam_roll()
    $ _pass = exam_pass("final")
    if _pass:
        "〔期末 · 得分 [exam_score] · 过线〕"
    else:
        "〔期末 · 得分 [exam_score] · 没到线〕"
    call free_actions
    scene bg dorm_402
    "〔T29 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t30_february


label t30_february:
    $ start_month(30)
    scene bg classroom_day
    "二月。离高考还有一百多天。"
    scene bg classroom_day
    call ai_play("t30_offer")
    $ mark_milestone_for_beat("t30_offer")
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T30 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t31_march


label t31_march:
    $ start_month(31)
    scene bg classroom_day
    "三月。模拟考排在月底，教室里的空气是干的。"
    call free_actions
    scene bg dorm_402
    "〔T31 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t32_april


label t32_april:
    $ start_month(32)
    scene bg classroom_day
    "四月。最后一次模拟考。"
    scene bg corridor_night
    call ai_play("t32_choice")
    $ mark_milestone_for_beat("t32_choice")
    $ exam_roll()
    $ _pass = exam_pass("final")
    if _pass:
        "〔模拟考 · 得分 [exam_score] · 过线〕"
    else:
        "〔模拟考 · 得分 [exam_score] · 没到线〕"
    call event_slot
    call free_actions
    scene bg dorm_402
    "〔T32 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t33_may


label t33_may:
    $ start_month(33)
    scene bg classroom_day
    "五月。教室里开始有人不来上课。"
    scene bg classroom_night
    call ai_play("t33_last")
    $ mark_milestone_for_beat("t33_last")
    call free_actions
    scene bg dorm_402
    "〔T33 月末结算 · 学习 [study]，压力 [stress]，体力 [stamina]，钱 [money]〕"
    jump t34_june


label t34_june:
    $ start_month(34)
    scene bg classroom_day
    "六月。高考。"
    $ exam_roll()
    $ _gk = exam_pass("gaokao")
    if _gk:
        $ set_flag("gaokao_pass")
    call ai_play("t34_gaokao")
    call free_actions
    scene bg dorm_402
    "〔高考 · 得分 [exam_score]〕"
    jump t35_july


label t35_july:
    $ start_month(35)
    $ ap = 0
    scene bg dorm_402
    "七月。查分那晚，家里很安静。"
    "〔查分 · 学习 [study]，压力 [stress]〕"
    jump t36_august


label t36_august:
    $ start_month(36)
    $ ap = 0
    scene bg classroom_day
    "八月。分班名单贴在教学楼一楼。"
    call ending_gate
    return
