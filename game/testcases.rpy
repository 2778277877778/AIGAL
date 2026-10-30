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
    setup:
        ## 单条用例的超时从 5s 放到 20s。用例自己在零点几秒内跑完，却被告知
        ## 「超时 5.0 秒」，是因为计时用的是墙钟：机器上还有别的 Ren'Py 实例
        ## 在抢 log.txt / persistent 时，进程被饿住，墙钟照走。
        ## 写在 setup 里而不是某条用例里 —— 超时判定发生在语句执行之前，
        ## 用例内部改 _test.timeout 永远赶不上自己那一条。
        $ _test.timeout = 20
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
            ## 自由段不直接播 tN_free（走 act/<action_key>），不要求它有拍模板
            if _bid.endswith("_free"):
                continue
            ## 必须命中这一拍自己的模板；落到 _EMPTY_TEMPLATE 也算缺
            ## （它有占位行，只看「有没有 lines」会漏掉「真空模板」）。
            if aig.template(_bid) is aig._EMPTY_TEMPLATE:
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


## 只读轨迹（systems/trace.rpy）：beat 顺序 / Flag 集合 / 结局 id，三样可逐字比对。
## 「变／不变」的五条断言都用 trace_digest()，别再各自遍历。
testcase trace_logic:
    pause .2

    python:
        _saved_flags = store.flags
        try:
            trace_reset()
            trace_beat("t2_welcome")
            trace_beat("t2_piano")
            set_flag("heard_piano")
            trace_ending("end_b")
            _d1 = trace_digest()
            assert _d1 == (("t2_welcome", "t2_piano"), ("heard_piano",), "end_b"), _d1

            ## 重复置位不重复记；轨迹里不含台词/来源字段
            set_flag("heard_piano")
            assert trace_digest() == _d1
            assert "lines" not in str(_d1) and "template" not in str(_d1)

            ## 清空后回到空轨迹
            trace_reset()
            assert trace_digest() == ((), (), "")
        finally:
            store.flags = _saved_flags


## 只读回放（systems/replay.rpy）：给 Chief 五条断言里的 1 / 3 / 5 共用。
## 纯函数，不碰 store、不碰 provider，所以有 key / 没 key 的结果必然同构。
testcase replay_logic:
    pause .2

    python:
        _p = {"t8_subject": "support", "t8_form": "same", "confession": "yes"}
        _a = replay_trace(_p, study=80, stress=60)
        _b = replay_trace(_p, study=80, stress=60)
        assert _a == _b, "同一条选择轨迹两次回放不一致"
        assert _a[2] == "true", "TRUE 条件应成立：%r" % (_a,)
        for _beat in _a[0]:
            assert _beat in AI_BEATS, "回放里有未登记的拍：%s" % _beat
        assert len(_a[0]) == len(set(_a[0])), "回放里 beat 重复"

        assert replay_trace({}, study=30, stress=10)[2] == "end_a", "缺 subject_support 应走 END A"
        assert replay_trace({"t8_subject": "support"}, 30, 10)[2] == "end_b", "缺 same_subject 应走 END B"
        assert replay_trace({"t8_subject": "support", "t8_form": "same"}, 60, 10)[2] == "end_c", "栽在数值应走 END C"

        try:
            replay_trace({"t8_nope": "x"})
            assert False, "未知选择点没抛"
        except Exception:
            pass


## 随机事件池（systems/events.rpy + §1.2 §3）：登记、闸门、过滤、互斥、权重衰减。
testcase event_pool:
    pause .2

    python:
        _saved_turn = store.turn
        _saved_seen = store.event_seen
        try:
            ## 回合 → 自然月：T1=9、T5=1、T13=9
            assert calendar_month(1) == 9 and calendar_month(5) == 1 and calendar_month(13) == 9
            assert event_slot_at(2) and event_slot_at(22) and not event_slot_at(1)

            ## §1.2 的 21 个主线拍 + 20 个事件拍都进了 beat 表
            for _bid in ("t9_injury", "t10_subject", "t13_artfair", "t14_coach", "t15_ask",
                         "t16_mother", "t17_parent", "t18_half", "t19_club", "t20_quit",
                         "t21_transfer", "t25_hall", "t26_entry", "t27_watch", "t28_form",
                         "t29_exam", "t30_offer", "t32_choice", "t33_last", "t34_gaokao",
                         "t35_score"):
                assert _bid in AI_BEATS, "主线拍未登记：%s" % _bid
            assert len(EVENT_POOL) == 20, "事件池应为 20 个，实际 %d" % len(EVENT_POOL)
            for _eid in EVENT_POOL:
                assert _eid in AI_BEATS, "事件未登记进 beat 表：%s" % _eid
                assert AI_BEATS[_eid].get("turns"), "事件缺 turns：%s" % _eid
            assert AI_BEATS["e_welcome"]["turns"] == (1, 2)

            class _FakeRng(object):
                def __init__(self, value):
                    self.value = value
                def random(self):
                    return self.value
                def choices(self, seq, weights=None, k=1):
                    return [seq[0]]

            store.turn = 2
            store.event_seen = {}

            ## 60% 闸门：0.7 不出，0.5 出
            assert event_draw(2, rng=_FakeRng(0.7)) == "", "0.7 不该掷中"
            assert event_draw(2, rng=_FakeRng(0.5)), "0.5 应当掷中"

            ## 与当月主线互斥：T2 有琴房/晚会（stage），舞台类事件不能出
            _cands = event_candidates(2)
            assert "e_welcome" not in _cands and "e_newyear" not in _cands
            assert "e_sports_aut" in _cands

            ## 年级过滤：T2 的候选只可能来自高一池
            for _eid in _cands:
                assert EVENT_POOL[_eid]["grade"] == 1, "T2 抽到了非高一事件：%s" % _eid

            ## 互斥：春季运动会出过，秋季运动会就不再出
            store.event_seen = {"e_sports_spring": 1}
            assert "e_sports_aut" not in event_candidates(2)

            ## 权重衰减：已出过 ×0.3
            store.event_seen = {"e_sports_aut": 1}
            _w = event_weights(["e_sports_aut", "e_open_day"])
            assert abs(_w[0] - EVENT_POOL["e_sports_aut"]["weight"] * EVENT_SEEN_RATE) < 1e-9
            assert abs(_w[1] - EVENT_POOL["e_open_day"]["weight"]) < 1e-9

            ## 断言 4「事件不改主线」：事件拍不许给 AI 置 Flag、不进 TRUE 判定、不进主线回放
            for _eid in EVENT_POOL:
                assert AI_BEATS[_eid]["flags"] == (), "事件拍不许给 AI 置 Flag：%s" % _eid
                assert _eid not in TRUE_FLAGS, "事件 id 混进了 TRUE 判定：%s" % _eid
            _main = replay_trace({}, 30, 10)[0]
            assert not any(_b.startswith("e_") for _b in _main), "事件不该出现在主线回放里"
        finally:
            store.turn = _saved_turn
            store.event_seen = _saved_seen
