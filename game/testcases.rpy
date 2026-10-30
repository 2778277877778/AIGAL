################################################################################
## 冒烟自测（Ren'Py testcase）
##
## 用法：
##   ... renpy.py "<工程路径>" test
##
## 现在只覆盖「主菜单 → 开始 → 推进几句 T1 台词」。T1 接进来以后开局就不回主菜单了，
## 菜单页（设置 / 关于 / 帮助）那几条等 campus_map 做完再补回来。
##
## 两个踩过的坑：
## 1. 对白最后一句别用 advance —— 脚本 return 回主菜单后没有可推进的对象，会等到超时；
##    改点文本更稳。
## 2. 勾选类按钮（未读文字 / 选项之后 / 转场）的测试文本还是英文，
##    要用 "Unseen Text" 这种旧名字才点得到；导航按钮用中文没问题。
################################################################################

testsuite global:
    teardown:
        exit

testcase smoke:
    $ _test.transition_timeout = 0.05

    click "开始"
    pause .8

    advance
    advance
    advance
    pause .3


## AI 契约自测：beat 表 / turn 断言 / 主角名清洗。不联网、不需要 API key。
## 纯数据的 12 项故障矩阵在 tools/selftest_schema.py，用系统 Python 跑。
##
## 刻意不点「开始」：这条用例跑在 smoke 之后，游戏已经进了剧本，
## 主菜单的按钮早没了。turn 自己摆好再还原，跟前面用例的顺序无关。
testcase ai_contract:
    $ _test.transition_timeout = 0.05

    pause .3

    python:
        _saved_turn = getattr(store, "turn", 1)
        store.turn = 1
        try:
            ## T1 的拍能和当前回合对上
            assert ai_require_beat("t1_report")["turn"] == 1, "t1_report 的 turn 不对"

            ## 跨回合的拍必须被挡下来：T1 的流程里不该出现 T2 的拍
            assert ai_beat_ok("t2_piano")[0] is False, "T1 里放行了 T2 的拍"

            ## 未登记的 beat 要报出名字，不能静默返回 None 让上层崩在渲染时
            assert ai_beat_ok("t9_final")[0] is False, "未登记的 beat 没被拦"

            ## 自由行动段按需合成，T1..T8 每个月都得有
            for _n in range(1, 9):
                assert ai_beat("t%d_free" % _n) is not None, "t%d_free 没合成出来" % _n

            ## 本拍 flag 白名单为空：终结/告白这类判定链 flag 不许 AI 置位
            assert ai_ctx("t1_free")["flags"] == (), "t1_free 的 flag 白名单不是空的"

            ## 玩家可以把名字填成标签，渲染时也必须洗掉
            _saved_name = getattr(store, "player_name", None)
            store.player_name = "{image=bg room}阿明[persistent.api_key]<b>"
            _rendered = ai_render("叫我" + AI_NAME_TOKEN + "……")
            assert not (set(_rendered) & set("{}[]<>")), "主角名把标记带进了正文：%r" % _rendered
            assert "阿明" in _rendered, "真名被洗掉了：%r" % _rendered

            ## 清洗是幂等的：同一句渲染两次结果一样
            assert ai_render(_rendered) == _rendered, "ai_render 不幂等"

            store.player_name = _saved_name
        finally:
            store.turn = _saved_turn


## 骨架覆盖：每个登记过的拍都得有本地模板（没 key 的玩家走的就是这些），
## 模板里的 action_key 必须在本拍白名单里，speaker 必须真的 define 了。
testcase beat_coverage:
    pause .2

    python:
        _missing = []
        for _bid in AI_BEATS:
            if not (aig.template(_bid).get("lines") or ()):
                _missing.append(_bid)
        assert not _missing, "这些拍没有本地模板：%s" % ", ".join(sorted(_missing))

        _bad_choices = []
        for _bid in AI_BEATS:
            _allowed = set(aig.choices_for(_bid) or ())
            if not _allowed:
                continue
            for _c in aig.template(_bid).get("choices") or ():
                if _c["action_key"] not in _allowed:
                    _bad_choices.append("%s/%s" % (_bid, _c["action_key"]))
        assert not _bad_choices, "模板选项不在本拍白名单：%s" % ", ".join(_bad_choices)

        _bad_spk = []
        for _bid in AI_BEATS:
            for _ln in aig.template(_bid).get("lines") or ():
                if getattr(store, _ln["speaker"], None) is None:
                    _bad_spk.append("%s/%s" % (_bid, _ln["speaker"]))
        assert not _bad_spk, "模板里有没 define 的 speaker：%s" % ", ".join(_bad_spk)

        ## 每个拍真的走一遍 run()（假请求，不联网）：beat 登记、ctx、choice_path、
        ## 校验失败后的模板降级，整条链都得能拿到正文。
        _saved_turn = store.turn
        try:
            for _bid, _b in AI_BEATS.items():
                store.turn = _b["turn"]
                _d = aig.run(_bid, "", fake="ok", blocking=True)
                assert _d["lines"], "run() 没拿到正文：%s（%s）" % (_bid, _d["notes"])
        finally:
            store.turn = _saved_turn


## 结局判定：只读 study / stress / 六个 Flag；END 的三个变体按顺序取第一条命中的。
testcase ending_logic:
    pause .2

    python:
        _saved_study = store.study
        _saved_stress = store.stress
        _saved_flags = store.flags
        try:
            store.study = 80
            store.stress = 60
            store.flags = {f: True for f in TRUE_FLAGS}
            assert true_ending(), "六个 TRUE Flag 齐全且数值达标，应为 TRUE"

            store.study = 74
            assert not true_ending(), "学习 74 不该出 TRUE"
            store.study = 80
            store.stress = 71
            assert not true_ending(), "压力 71 不该出 TRUE"
            store.stress = 60

            store.flags = dict(store.flags)
            del store.flags["same_subject"]
            assert not true_ending(), "缺 same_subject 不该出 TRUE"
            assert end_variant() == "B", "缺 same_subject 应走 END B"
            del store.flags["subject_support"]
            assert end_variant() == "A", "缺 subject_support 应走 END A"

            store.flags["subject_support"] = True
            store.flags["same_subject"] = True
            store.study = 60
            assert end_variant() == "C", "两个 Flag 都有、栽在数值应走 END C"
        finally:
            store.study = _saved_study
            store.stress = _saved_stress
            store.flags = _saved_flags


## 三线变量（《剧情大纲_三年_v1.md》§5 §6）：好感只加不减、stage 由里程碑数算、
## route 在平局时的优先级、学年系数与分段考试线、每月一次的减压口。
testcase relation_logic:
    pause .2

    python:
        _saved = (
            store.rel_zm, store.rel_xia, store.rel_x, store.route, store.route_done,
            dict(store.ms_done), store.flags, store.turn, store.stress, store.weekend_used,
        )
        try:
            store.rel_zm = store.rel_xia = store.rel_x = 0
            store.route, store.route_done = "none", False
            store.ms_done = {"zm": {}, "xia": {}, "x": {}}
            store.flags = {}
            store.turn = 1

            ## add_rel：只加不减、上限 100、未知线直接抛
            assert add_rel("zm", 30) == 30
            assert add_rel("zm", 200) == 100, "好感上限应为 100"
            try:
                add_rel("zm", -1)
                assert False, "add_rel 传负数没抛"
            except Exception:
                pass
            try:
                add_rel("nobody", 1)
                assert False, "未知角色线没抛"
            except Exception:
                pass

            ## stage：0–2 个=0，3–4=1，5–6=2，7–8=3，9+=4
            assert stage_of("zm") == 0
            for _i in (1, 2, 3):
                mark_milestone("zm", _i)
            assert stage_of("zm") == 1, "3 个里程碑应为 stage 1"
            for _i in (4, 5, 6):
                mark_milestone("zm", _i)
            assert stage_of("zm") == 2
            for _i in (7, 8):
                mark_milestone("zm", _i)
            assert stage_of("zm") == 3
            mark_milestone("zm", 9)
            mark_milestone("zm", 10)
            assert stage_of("zm") == 4
            assert has_flag("met_zhoumo") and has_flag("subject_support"), "里程碑应顺手置 Flag"

            ## route：平局 周墨 > 夏幸悠 > 温以宁；锁过不再变；都 <60 为 none
            store.rel_zm = store.rel_xia = store.rel_x = 70
            assert lock_route() == "zm", "平局应按 周墨 > 夏幸悠 > 温以宁"
            store.rel_x = 100
            assert lock_route() == "zm", "锁过之后不该改"

            store.route, store.route_done = "none", False
            store.rel_zm, store.rel_xia, store.rel_x = 50, 80, 80
            assert lock_route() == "xia", "夏幸悠与温以宁并列时取夏幸悠"

            store.route, store.route_done = "none", False
            store.rel_zm, store.rel_xia, store.rel_x = 10, 20, 59
            assert lock_route() == "none", "三人都低于 60 应为 none"

            ## 学年系数 / 分段考试线 / 行动点
            store.turn = 1
            assert school_year() == 1 and study_rate() == 1.0
            assert exam_line("midterm") == 50 and exam_line("final") == 60
            assert ap_for_month(1) == 3 and ap_for_month(10) == 2
            store.turn = 13
            assert school_year() == 2 and study_rate() == 0.8
            assert exam_line("midterm") == 65
            store.turn = 25
            assert school_year() == 3 and study_rate() == 0.6
            assert exam_line("final") == 85 and ap_for_month(25) == 2
            store.turn = 34
            assert exam_line("gaokao") == 85 and ap_for_month(34) == 1, "高考月只有 1 AP"
            store.turn = 11
            assert school_year() == 0, "暑假短过场应为 0"

            ## 每月一次的减压口：同月第二次不给
            store.turn = 2
            store.stress = 50
            store.weekend_used = False
            do_action("weekend_stay")
            assert store.stress == 42, "周末留校应减 8 点压力"
            assert do_action("weekend_stay") is False, "同月第二次不该给"
        finally:
            (store.rel_zm, store.rel_xia, store.rel_x, store.route, store.route_done,
             store.ms_done, store.flags, store.turn, store.stress, store.weekend_used) = _saved
