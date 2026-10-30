################################################################################
## ai/testcases_diversity.rpy —— 「每局不同、存档一致」的契约断言
##
## 对应 Chief 定的五条里的第 1、2、3 条里**能在引擎内验的部分**：
##   1. 同一 seed 两次取同一拍 → 一字不差，且第二次不再发请求
##   2. 不同 seed → 不同 key，不会命中上一局的缓存（"每局不同"的机制底座）
##   3. 措辞变了但结构不变：行数、speaker 集合、action_key 集合必须一致
##   4. 结局只可能落在已声明的那几种里
##
## 明确验不到的（不是漏写，是缺前提）：
##   · 真实措辞的差异率——fake provider 每次返回同一段文本，测不出 0.4 阈值；
##     那一条要真 key，用 ai_debug 里抓到的两段真实返回去算。
##   · 同一条选择轨迹重放后的 beat 序列 / Flag 集合——等后端的只读回放接口。
##   · 随机事件不改主线——事件池还没进代码。
##
## 离线部分在 tests/selftest_diversity.py（度量标定），不占 Ren'Py 实例。
################################################################################

init -1 python:

    def _div_test(cond, msg):
        if not cond:
            raise Exception("差异断言失败：" + msg)


testsuite ai_diversity:
    teardown:
        exit


## 1. 同一 seed：两遍一字不差，第二遍不许再发请求
##    beat 要挑「没有 BEAT_CHOICES」的拍：假正文里的 action_key 是 ACTIONS 里的 study，
##    剧情拍的选项白名单（deny/ask/fumble 之类）会把它判掉，两次都 invalid，就验不到 AI 那条路。
##    用 T1 的拍同理：测试跑在开局头，store.turn 是 1。
testcase div_same_seed_identical:
    $ aig.reset_circuit()
    $ aig.clear_pending()
    $ store.ai_cache = {}
    $ store.ai_template = {}
    $ _r1 = aig.run("t1_free", "same", fake="ok", blocking=True)
    $ _n1 = aig.status()["requests"]
    $ _r2 = aig.run("t1_free", "same", fake="ok", blocking=True)
    $ _n2 = aig.status()["requests"]
    $ _div_test(_r1["source"] == "ai", "第一遍应走现场请求，实际 %r / %r" % (_r1["source"], _r1["notes"]))
    $ _div_test(_r2["source"] == "cache", "第二遍应命中缓存，实际 %r / %r" % (_r2["source"], _r2["notes"]))
    $ _div_test([l["text"] for l in _r1["lines"]] == [l["text"] for l in _r2["lines"]],
                "同一 seed 两遍文本不一致")
    $ _div_test(_n2 == _n1, "第二遍又发了请求：%d -> %d" % (_n1, _n2))
    $ store.ai_cache = {}
    $ store.ai_template = {}


## 2. 换 seed：key 必须不同，且不许命中上一局写进去的文本
testcase div_seed_separates_runs:
    $ _k1 = aig.key("t2_welcome", 11111, "same")
    $ _k2 = aig.key("t2_welcome", 22222, "same")
    $ aig.forget(_k1)
    $ aig.forget(_k2)
    $ _div_test(_k1 != _k2, "换 seed 换了同一个 key")
    $ aig.put(_k1, "上一局的说法")
    $ _div_test(aig.get(_k1) == "上一局的说法", "刚写进去就取不到")
    $ _div_test(aig.get(_k2) is None, "换 seed 命中了上一局的缓存——新开局会读到一样的台词")
    $ aig.forget(_k1)
    $ aig.forget(_k2)


## 3. 措辞变、结构不变：同一拍两份不同说法，形状一致且重合度 ≤ 0.4
testcase div_shape_and_wording:
    python:
        ## actions 直接给这一拍声明两个分支 id（t1_ceremony 不在 BEAT_CHOICES 里，
        ## 默认是全量 ACTIONS，这里要的是「剧情分支 id」那种形状）。
        _ctx = ai_ctx("t1_ceremony", actions=("reveal", "ignore"), expect_choices=True)
        _a = (
            '{"lines":['
            '{"speaker":"inner","text":"（门轴响了一声，琴声就停了。）"},'
            '{"speaker":"zm","text":"……你没听见吧。"},'
            '{"speaker":"mc","text":"我、我什么都没听见。"}],'
            '"choices":[{"text":"说破","action_key":"reveal"}],"flags":[],"mood":"闷"}'
        )
        _b = (
            '{"lines":['
            '{"speaker":"inner","text":"（她的手指悬在琴键，没有落下。）"},'
            '{"speaker":"zm","text":"……别跟别人讲。"},'
            '{"speaker":"mc","text":"那个……找作业本。"}],'
            '"choices":[{"text":"装没看见","action_key":"reveal"}],"flags":[],"mood":"紧"}'
        )
        _va = ai_validate(_a, _ctx)
        _vb = ai_validate(_b, _ctx)
        _div_test(_va["ok"] and _vb["ok"],
                  "两份样例都没过校验：%r / %r" % (_va["reason"], _vb["reason"]))

        _same, _why = aitext.same_shape(_va["lines"], _va["choices"],
                                        _vb["lines"], _vb["choices"])
        _div_test(_same, "换了说法就变了形状：" + _why)

        _j = aitext.pair_jaccard(_va["lines"], _vb["lines"])
        _div_test(_j <= 0.4, "两份措辞重合度太高（%.2f），这等于没换说法" % _j)

        ## 负向：多一行、多一个 speaker、多一个 action_key 都必须被抓出来
        _v2 = ai_validate(
            '{"lines":[{"speaker":"zm","text":"嗯。"},{"speaker":"zzb","text":"喂。"}],'
            '"choices":[{"text":"走","action_key":"ignore"}],"flags":[],"mood":""}',
            _ctx,
        )
        _div_test(_v2["ok"], "负向样例本身没通过校验：%r" % (_v2["reason"],))
        _same2, _ = aitext.same_shape(_va["lines"], _va["choices"],
                                      _v2["lines"], _v2["choices"])
        _div_test(not _same2, "多一行/多一个 speaker/多个 action_key 没被抓到")


## 4. 结局收敛：只可能落在已声明的那几种里，不存在第 6 种
testcase div_ending_space:
    python:
        _declared = {"true", "end_a", "end_b", "end_c"}
        _saved = (store.study, store.stress, store.flags)
        try:
            _seen = set()
            for _study, _stress, _all_flags in (
                (80, 10, True), (80, 90, True), (30, 10, False), (30, 90, False),
            ):
                store.study = _study
                store.stress = _stress
                store.flags = dict((f, True) for f in TRUE_FLAGS) if _all_flags else {}
                ## 结局 id 一律小写：endings.rpy 记的是 "end_" + _end_var.lower()，
                ## replay.rpy 也是小写。end_variant() 本身返回大写字母，别直接拼。
                _seen.add("true" if true_ending() else "end_" + end_variant().lower())
            _div_test(_seen <= _declared, "出现了声明外的结局：%r" % (_seen - _declared,))
            _div_test("true" in _seen, "TRUE 结局在四种组合里一次都没出现")
        finally:
            store.study, store.stress, store.flags = _saved


## 5. 骨架不变（第 1 条）：同一条选择轨迹回放两次，beat 序列 / Flag 集合 / 结局逐字一致
testcase div_replay_stable:
    python:
        _picks = {"t2_piano": "reveal", "t2_call": "stay"}
        _d1 = replay_trace(_picks)
        _d2 = replay_trace(_picks)
        _div_test(_d1 == _d2, "同一轨迹回放两次不一致：\n%r\n%r" % (_d1, _d2))
        _div_test(bool(_d1[0]), "回放出来的 beat 序列是空的")
        _div_test(_d1[2] in ("true", "end_a", "end_b", "end_c"),
                  "回放出了声明外的结局：%r" % (_d1[2],))

        ## 每个 beat 都必须在 beat 表里登记过，否则剧本走的是没登记的名字
        _missing = [b for b in _d1[0] if ai_beat(b) is None]
        _div_test(not _missing, "回放里出现了未登记的 beat：%r" % (_missing,))


## 6. 无 key 同构（第 5 条）：结局只由选择与数值算，和有没有 key 无关
testcase div_replay_key_independent:
    python:
        _c = aig.cfg()
        _saved_key = _c.get("api_key")
        _saved_study = store.study
        _n0 = aig.status()["requests"]
        try:
            _c["api_key"] = ""
            _a = replay_trace({"t2_piano": "ignore"}, study=70, stress=40)
            _c["api_key"] = "sk-fake-not-used"
            _b = replay_trace({"t2_piano": "ignore"}, study=70, stress=40)
        finally:
            _c["api_key"] = _saved_key
        _div_test(_a == _b, "有 key / 没 key 回放结果不同：\n%r\n%r" % (_a, _b))
        _div_test(aig.status()["requests"] == _n0, "回放竟然发了请求")
        _div_test(store.study == _saved_study, "回放改动了 store 的数值")


## 7. 细节位：读**真实** BEAT_DETAILS，不看注入表
##    Chief 定的口径：每个会播的 AI 拍至少 2 条，seed 0..n-1 必须逐个命中、不许越界。
##    这条今天应该是红的——大纲 §2.6 的 132 条还在 md 里，没编译进代码。
##    红着比绿着有用：改成注入表就是「测试全绿但差异已死」。
testcase div_detail_coverage:
    python:
        ## 清单取自 story/*.rpy 的 ai_play 调用点（29 处、28 个 id）。
        ## 剧本加拍要同步这张表；拍不在这张表里就说明它不会被播，也就不用有细节。
        _used = (
            "t2_welcome", "t2_piano", "t2_gala", "t2_exam", "t2_call",
            "t3_exam", "t3_parent", "t3_piano",
            "t4_artfair", "t4_exam", "t4_newyear", "t4_father",
            "t5_move", "t5_office", "t5_mother",
            "t6_sports", "t6_run", "t6_club",
            "t7_hall", "t7_talk",
            "t8_exam", "t8_choice_her", "t8_subject", "t8_form",
            "t8_true", "t8_end_a", "t8_end_b", "t8_end_c",
        )
        _real = getattr(aig, "BEAT_DETAILS", {}) or {}
        _thin = [b for b in _used if len(_real.get(b, ()) or ()) < 2]
        _div_test(
            not _thin,
            "%d 个会播的拍缺细节（每拍至少 2 条）：%r；BEAT_DETAILS 现在有 %d 拍。"
            "这是设计上的红：等 md 走 build_prompts.py 编译进 prompts_data.rpy 就会变绿"
            % (len(_thin), _thin, len(_real)),
        )

        ## 有数据的拍：seed 取模必须正好遍历它自己那几条，不越到别的拍
        for _b in _used:
            _d = _real.get(_b) or ()
            _got = [aig.detail_for(_b, _s) for _s in range(len(_d))]
            _div_test(_got == list(_d),
                      "%s 的 seed 取模没覆盖全：%r vs %r" % (_b, _got, list(_d)))


## 8. 差异观测命令的载荷（.\dev.ps1 diversity 才跑它）：只打数、只在真数据缺位时判红
##    Jaccard 那条在这里也只是打印，不设 0.4 硬门——0.4 实际测的是「模型重写了多少」，
##    不是细节位能保证的（算法见 玩法策划 的估算：一条 16 字细节只影响约 17 个二元组）。
testcase diversity_report:
    python:
        _real = getattr(aig, "BEAT_DETAILS", {}) or {}
        _beats = len(_real)
        _items = sum(len(v) for v in _real.values())
        print("DETAILS beats=%d items=%d (预期 52 拍 / 132 条)" % (_beats, _items))

        for _bid in sorted(_real)[:6]:
            _d = _real[_bid]
            print("  %s: %d 条, seed0..%d -> %s"
                  % (_bid, len(_d), len(_d) - 1,
                     [aig.detail_for(_bid, _s) for _s in range(len(_d))]))

        ## 样例对的 Jaccard：标定阈值用，不是被测对象
        _a = "（门轴响了一声，琴声就停了。）……你没听见吧。我、我什么都没听见。"
        _b = "（她的手指悬在琴键，没有落下。）……别跟别人讲。那个……找作业本。"
        print("jaccard(样例A,样例B)=%.3f" % aitext.bigram_jaccard(_a, _b))

        ## 唯一判红的地方：真数据一条都没有，说明差异机制根本没通电。
        ## 只在 \dev.ps1 diversity 下判红（环境变量），默认链只打印——
        ## 否则每次提交都会被一条「等文案数据」的断言卡住。
        import os
        _strict = os.environ.get("AIGAL_DIVERSITY") == "1"
        _msg = ("BEAT_DETAILS 是空的——大纲 §2.6 的 132 条还没进代码，"
                "现在每拍抽到的细节都是空串，差异只剩温度采样")
        if _strict:
            _div_test(_beats > 0, _msg)
        elif _beats == 0:
            print("WARN " + _msg + "（默认链不判红；用 .\\dev.ps1 diversity 看）")
