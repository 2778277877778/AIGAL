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

    def _div_story_refs():
        """扫 story/ 下 ai_play / aig.run 的字面量 beat id。

        返回 (refs, has_dynamic, file_count, pool_ids)。
        定义在 init 里的普通函数，推导式能正常用；测试用例的 python 块是
        exec(globals, locals) 跑的，那里不能用推导式（见下面用例里的注释）。
        """
        import re
        pat = re.compile(r"""(?:ai_play|aig\.run)\(\s*["']([a-z0-9_]+)["']""")
        dyn = re.compile(r"""(?:ai_play|aig\.run)\(\s*[A-Za-z_]""")
        refs = set()
        has_dyn = False
        files = 0
        for f in renpy.list_files():
            if not (f.startswith("story/") and f.endswith(".rpy")):
                continue
            try:
                fh = renpy.loader.load(f)
                blob = fh.read()
                fh.close()
            except Exception:
                continue
            text = blob.decode("utf-8", "replace") if not isinstance(blob, str) else blob
            files += 1
            refs.update(pat.findall(text))
            if dyn.search(text):
                has_dyn = True
        ## 变量派发点能产出的 id 集合（事件池），归一化成普通 str 的集合
        pool = {}
        for k in (globals().get("EVENT_POOL") or {}):
            pool[str(k)] = True
        return refs, has_dyn, files, pool


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
    $ _saveturn_div = store.turn
    $ store.turn = 3
    $ _r1 = aig.run("t3_parent", "same", fake="ok", blocking=True)
    $ _n1 = aig.status()["requests"]
    $ _r2 = aig.run("t3_parent", "same", fake="ok", blocking=True)
    $ _n2 = aig.status()["requests"]
    $ _div_test(_r1["source"] == "ai", "第一遍应走现场请求，实际 %r / %r" % (_r1["source"], _r1["notes"]))
    $ _div_test(_r2["source"] == "cache", "第二遍应命中缓存，实际 %r / %r" % (_r2["source"], _r2["notes"]))
    $ _div_test([l["text"] for l in _r1["lines"]] == [l["text"] for l in _r2["lines"]],
                "同一 seed 两遍文本不一致")
    $ _div_test(_n2 == _n1, "第二遍又发了请求：%d -> %d" % (_n1, _n2))
    $ store.ai_cache = {}
    $ store.ai_template = {}
    $ store.turn = _saveturn_div


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
    $ store.turn = 3
    python:
        ## actions 直接给这一拍声明两个分支 id（t3_parent 不在 BEAT_CHOICES 里，
        ## 默认是全量 ACTIONS，这里要的是「剧情分支 id」那种形状）。
        _ctx = ai_ctx("t3_parent", actions=("reveal", "ignore"), expect_choices=True)
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


## 7. 细节位：读**真实** BEAT_DETAILS，且清单来自 story 的调用点，不写死
##    Chief 定的口径：每个会播的 AI 拍至少 2 条，seed 0..n-1 必须逐个命中、不许越界。
testcase div_detail_coverage:
    python:
        ## 清单不写死：取 story/ 里真被调用的拍 ∩ 已登记表。
        ## 写死过一次 28 个 id，压拍后有 10 个永远不会播，等于在验一批死 id。
        _refs, _dyn, _scanned, _pool = _div_story_refs()
        _used = []
        for _b in _refs:
            if _b in AI_BEATS:
                _used.append(_b)
        _used.sort()

        _real = getattr(aig, "BEAT_DETAILS", {}) or {}
        _thin = []
        for _b in _used:
            if len(_real.get(_b, ()) or ()) < 2:
                _thin.append(_b)
        _div_test(
            not _thin,
            "%d 个会播的拍缺细节（每拍至少 2 条）：%r；BEAT_DETAILS 现在有 %d 拍。"
            "这是设计上的红：md 走 build_prompts.py 编译进 prompts_data.rpy 才会变绿"
            % (len(_thin), _thin, len(_real)),
        )

        ## 有数据的拍：seed 取模必须正好遍历它自己那几条，不越到别的拍
        for _b in _used:
            _d = _real.get(_b) or ()
            _got = []
            for _s in range(len(_d)):
                _got.append(aig.detail_for(_b, _s))
            _div_test(_got == list(_d),
                      "%s 的 seed 取模没覆盖全：%r vs %r" % (_b, _got, list(_d)))


## 9. 死登记：AI_BEATS 里登记的每个拍，story/ 里必须至少有一处真调用
##    今天已经踩过三种同形的空转：文档写了代码没有、登记了抽不到、合拍后旧 id 没人调。
##    静态扫源码比「跑一遍看有没有播到」可靠：剧情有分支，跑一遍覆盖不全。
testcase div_no_dead_beats:
    python:
        _refs, _has_dynamic, _scanned, _pool = _div_story_refs()

        ## 自由段的拍由 free_scene 取模板，不走 ai_play，不参与这条
        _registered = []
        for _b in AI_BEATS.keys():
            if not _b.endswith("_free"):
                _registered.append(_b)
        _registered.sort()

        ## 豁免只认一条证据：存在变量派发点，且 id 属于该派发点真正能产出的集合（事件池）。
        ## 不写「允许清单」——允许清单只会越来越长；也不按前缀整族豁免。
        _dyn_ok = set()
        for _b in _registered:
            if _has_dynamic and str(_b) in _pool:
                _dyn_ok.add(_b)

        ## 分类：turn >= 9 是 §5.2 计划里还没铺的拍（待铺，不算死数据）；
        ## turn <= 8 是已交付回合，登记了却没人调就是死数据。label 一铺，待铺自动变引用。
        _pending = []
        _dead = []
        for _b in _registered:
            if _b in _refs or _b in _dyn_ok:
                continue
            if int(AI_BEATS[_b].get("turn", 99)) >= 9:
                _pending.append(_b)
            else:
                _dead.append(_b)

        print("BEATS registered=%d scanned=%d literal_refs=%d exempt=%d pending=%d dead=%d"
              % (len(_registered), _scanned, len(_refs), len(_dyn_ok), len(_pending), len(_dead)))
        print("  exempt rule: 变量派发点 x EVENT_POOL(%d) -> 豁免 %d；"
              "pending rule: turn>=9 视为 §5.2 待铺" % (len(_pool), len(_dyn_ok)))
        _div_test(_scanned > 0, "一个 story 文件都没扫到，扫源码这条路本身失效了")
        _div_test(not _dead,
                  "%d 个拍在已交付的回合里登记了却没人调（死数据）：%r"
                  % (len(_dead), _dead))


## 8. 差异观测命令的载荷（.\dev.ps1 diversity 才跑它）：只打数、只在真数据缺位时判红
##    Jaccard 那条在这里也只是打印，不设 0.4 硬门——0.4 实际测的是「模型重写了多少」，
##    不是细节位能保证的（算法见 玩法策划 的估算：一条 16 字细节只影响约 17 个二元组）。
##    注意：这几段刻意不用推导式——测试的 python 块是 exec(globals, locals) 跑的，
##    推导式按 globals 找名字，看不到局部变量，会报 NameError。
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


## 11. 三条 route 各自有玩家真能读到的结局
##     只验 lock_route() 选对了线是不够的：route 对了、ending_gate 没按 route 分支，
##     玩家照样读不到那三个结局。这条要的是「route → 结局 id」这一跳本身。
testcase div_route_endings:
    python:
        _saved = (store.rel_zm, store.rel_xia, store.rel_x,
                  store.route, store.route_done)
        try:
            _picked = {}
            for _r, _v in (("zm", (80, 10, 10)),
                           ("xia", (10, 80, 10)),
                           ("x", (10, 10, 80))):
                store.rel_zm, store.rel_xia, store.rel_x = _v
                store.route_done = False          # lock_route 只锁一次，每轮都要放开
                _picked[_r] = lock_route()
            _div_test(_picked["zm"] == "zm" and _picked["xia"] == "xia" and _picked["x"] == "x",
                      "lock_route 没按好感选出三条线：%r" % (_picked,))

            ## 结局得有一条 route → 结局 id 的接缝；没有就说明 ending_gate 还在按
            ## TRUE / END A-B-C 分，三个 route 结局玩家永远读不到。
            _tab = getattr(store, "ENDING_BY_ROUTE", None)
            _fn = getattr(store, "ending_for", None)
            _div_test(_tab is not None or _fn is not None,
                      "缺少 route→结局 的接缝：既没有 ENDING_BY_ROUTE 表，也没有 ending_for()，"
                      "这条没法独立验证；ending_gate 现在仍是 TRUE/END A-B-C")

            _ids = {}
            for _r in ("zm", "xia", "x"):
                if _tab is not None:
                    _ids[_r] = str(_tab.get(_r) or "")
                else:
                    _ids[_r] = str(_fn(_r) or "")
            _blank = []
            for _r in ("zm", "xia", "x"):
                if not _ids[_r]:
                    _blank.append(_r)
            _div_test(not _blank, "这些 route 没有结局 id：%r（全表 %r）" % (_blank, _ids))

            _distinct = set(_ids.values())
            _div_test(len(_distinct) == 3,
                      "三个 route 的结局没有各不相同（玩家会读到同一个结局）：%r" % (_ids,))
        finally:
            store.rel_zm, store.rel_xia, store.rel_x = _saved[0], _saved[1], _saved[2]
            store.route, store.route_done = _saved[3], _saved[4]


## 12. 分页的两个边界（独立复验，不依赖前端那份夹具）
##     输入直接取 美工 复现时用的两串，断言看的是玩家真正读到的东西：
##     首页不能是碎片、有句末标点时不能切在句子中间。
testcase div_page_edges:
    python:
        ## ① 第 2 个字就是弱标点、其后 150 字无标点：首页不许只剩两个字
        _head = "你，" + ("雨" * 150)
        _p = page_text(_head, 100)
        _div_test("".join(_p) == _head, "首页边界：切完拼不回原文")
        _div_test(len(_p[0]) >= 10,
                  "结局第一屏只有 %d 个字：%r（玩家最后读到的东西，不能是两个字的碎片）"
                  % (len(_p[0]), _p[0]))

        ## ② 句号在第 41 字、其后 120 字无标点：切点必须落在句号后，
        ##    宁可这一页短，也不要在句子中间断（Chief 规则 2）。
        _mid = ("字" * 40) + "。" + ("雨" * 120)
        _q = page_text(_mid, 100)
        _div_test("".join(_q) == _mid, "句中切点：切完拼不回原文")
        _div_test(_q[0].endswith("。"),
                  "第 1 页切在句子中间：末字是 %r，页长 %d（句号在第 41 字，应该切在它后面）"
                  % (_q[0][-1:], len(_q[0])))
