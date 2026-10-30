################################################################################
## ai/testcases_ai.rpy —— provider / cache 两层的自测（M1）
##
## 用法：.\dev.ps1 test ai_layer
##       .\dev.ps1 test            （跑全部套件）
##
## 这些 case 不碰网络：全部走 aig.start_fake()，等的是假请求。
## 熔断会在连 3 次失败后转离线，所以每个 case 开头都 reset_circuit()。
## 故障矩阵里那 10 个用例是 schema 的活，这里只验「线程 + 超时 + 缓存」。
################################################################################

init -1 python:

    def _aig_test(cond, msg):
        if not cond:
            raise Exception("AIGAL 自测失败：" + msg)

    def _aig_check_saveable():
        """在飞状态下验存档路径。返回 "" 表示干净，否则返回原因。

        两条路都走：
          1) 存档真正序列化的那份根清单（renpy.game.log.get_roots()），直接 pickle 一遍
             —— 这就是 cannot pickle _thread.lock 的实际触发点
          2) 真调一次 renpy.save()，非 pickle 类的错误按环境问题放过（主菜单没有存档上下文
             之类的），不让它冒充「Job 泄漏」
        """
        import pickle
        try:
            pickle.dumps(renpy.game.log.get_roots(), pickle.HIGHEST_PROTOCOL)
        except Exception as e:
            return "根清单 pickle 失败：%s: %s" % (type(e).__name__, e)
        try:
            renpy.save("aig-selftest")
            renpy.unlink_save("aig-selftest")
        except Exception as e:
            msg = "%s: %s" % (type(e).__name__, e)
            if "pickle" in msg or "_thread" in msg or "_thread.lock" in msg:
                return "renpy.save 被线程对象卡住：" + msg
            return "renpy.save 失败：" + msg
        return ""


testsuite ai_layer:
    teardown:
        exit


## 假请求能走完，且回来的正文能过 schema
testcase fake_ok:
    $ aig.reset_circuit()
    $ _j = aig.start_fake("ok", delay=0.2)
    $ _r = aig.wait(_j, timeout=3.0, blocking=True)
    $ _aig_test(_j != 0, "start_fake 没给 id")
    $ _aig_test(_r["state"] == "done", "fake ok 没跑完：%r" % (_r,))
    $ _v = ai_validate(_r["text"], ai_ctx("t1_free"))
    $ _aig_test(_v["ok"], "schema 拒了 fake ok：%s / %r" % (_v["reason"], _v["notes"]))
    $ _aig_test(len(_v["lines"]) == 1, "行数不对：%r" % (_v["lines"],))
    $ _aig_test(_v["lines"][0]["speaker"] == "zm", "speaker 不对")


## 到点不结束的任务判 timeout，且不会把游戏卡死
testcase timeout:
    $ aig.reset_circuit()
    $ _j = aig.start_fake("timeout", delay=5.0)
    $ _r = aig.wait(_j, timeout=0.4, blocking=True)
    $ _aig_test(_r["state"] == "timeout", "应是 timeout，实际 %r" % (_r,))
    $ _aig_test(_r["elapsed"] >= 0.3, "elapsed 不对：%r" % (_r["elapsed"],))
    $ aig.reset_circuit()


## 连 3 次失败转离线；离线时不再发新请求；reset 后恢复
testcase breaker:
    $ aig.reset_circuit()
    $ _ids = [aig.start_fake("http500", delay=0.05) for _n in range(3)]
    $ _rs = [aig.wait(_i, timeout=2.0, blocking=True) for _i in _ids]
    $ _aig_test(all(_r["state"] == "error" for _r in _rs), "http500 应报 error：%r" % (_rs,))
    $ _aig_test(not aig.online(), "三次失败后应转离线")
    $ _aig_test(not aig.allowed(), "离线时 allowed() 应为假")
    $ _aig_test(aig.start_http("http://127.0.0.1:9/x", {}, {}) == 0, "离线时不该再发请求")
    $ aig.reset_circuit()
    $ _aig_test(aig.online() and aig.allowed(), "reset_circuit 没恢复")


## 两层缓存：本局那层清掉后，persistent 那层要能兜住；key 前缀归 schema 管
testcase cache_two_layers:
    $ _k = aig.key("t1_night_piano", 12345)
    $ aig.forget(_k)
    $ _aig_test(aig.get(_k) is None, "刚删过不该命中")
    $ aig.put(_k, "缓存正文")
    $ _aig_test(aig.get(_k) == "缓存正文", "put 之后应命中")
    $ renpy.store.ai_cache = {}
    $ _aig_test(aig.get(_k) == "缓存正文", "persistent 那层没兜住")
    $ _aig_test(aischema.cache_prefix() in _k, "key 前缀不是 schema 给的：%s" % _k)


## 同一拍的 seed 稳定；换 choice_path 才换 seed
testcase seed_stable:
    $ _s1 = aig.seed_for("t1_night_piano")
    $ _s2 = aig.seed_for("t1_night_piano")
    $ _s3 = aig.seed_for("t1_night_piano", "A")
    $ _aig_test(_s1 == _s2, "同 beat 的 seed 抖了：%r vs %r" % (_s1, _s2))
    $ _aig_test(aig.seed_for("t1_night_piano", "A") == _s3, "带 choice_path 的 seed 不稳定")
    $ _aig_test(aig.key("t1_night_piano", _s1, "A") != aig.key("t1_night_piano", _s1, ""),
                 "choice_path 没进 key")
    $ _aig_test(isinstance(_s1, int) and 1 <= _s1 < 2 ** 31, "seed 不是 int：%r" % (_s1,))


## 在飞状态下存档必须不炸：Job 只要被 store 抓住，这里就会 cannot pickle _thread.lock
testcase save_while_running:
    $ aig.reset_circuit()
    $ _j = aig.start_fake("slow", delay=1.5)
    $ _aig_test(_j != 0, "start_fake 没给 id")
    $ _why = _aig_check_saveable()
    $ _aig_test(_why == "", _why)
    $ aig.cancel_all()
    $ aig.reset_circuit()


## 读档 / 重启后存档里那个 id 查不到：必须返回 missing，不许 KeyError
testcase missing_job:
    $ _r = aig.result(0)
    $ _aig_test(_r["state"] == "missing", "空 id 应判 missing：%r" % (_r,))
    $ _r = aig.result(999999999999)
    $ _aig_test(_r["state"] == "missing", "陌生 id 应判 missing：%r" % (_r,))


## Ctrl 跳过时不发现场请求（只读缓存/模板）
testcase skip_blocks_request:
    $ aig.reset_circuit()
    $ renpy.config.skipping = True
    $ _aig_test(not aig.allowed(), "跳过中不该发现场请求")
    $ _aig_test(aig.start_http("http://127.0.0.1:9/x", {}, {}) == 0, "跳过中还发了请求")
    $ renpy.config.skipping = None
    $ _aig_test(aig.allowed(), "恢复正常后应能请求")


## 导演层全链路：买一次 → 校验 → 落缓存 → 第二次直接命中，不再发请求
testcase pipeline_fake:
    $ aig.reset_circuit()
    $ aig.clear_pending()
    $ _n0 = aig.status()["requests"]
    $ _d1 = aig.run("t1_free", fake="ok", blocking=True)
    $ _aig_test(_d1["source"] == "ai", "第一次应走 ai，实际 %r（notes=%r）" % (_d1["source"], _d1["notes"]))
    $ _aig_test(len(_d1["lines"]) >= 1, "没有台词：%r" % (_d1,))
    $ _d2 = aig.run("t1_free", fake="ok", blocking=True)
    $ _aig_test(_d2["source"] == "cache", "第二次应命中缓存，实际 %r" % (_d2["source"],))
    $ _aig_test(aig.status()["requests"] == _n0 + 1, "第二次不该再发请求：%r" % (aig.status()["requests"],))


## 预取：后台买好，进拍时直接取，不重复买
testcase pipeline_prefetch:
    $ aig.reset_circuit()
    $ aig.clear_pending()
    $ _saved_turn2 = store.turn
    $ store.turn = 2
    $ _jid = aig.prefetch("t2_free", fake="ok")
    $ _aig_test(_jid != 0, "预取没发出去")
    $ _d = aig.run("t2_free", fake="ok", blocking=True)
    $ store.turn = _saved_turn2
    $ _aig_test(_d["source"] in ("prefetch", "cache"), "应吃到预取，实际 %r" % (_d["source"],))
    $ aig.clear_pending()


## 没 key 走模板：不崩、不卡、有台词
testcase pipeline_template:
    $ aig.reset_circuit()
    $ aig.cfg()["api_key"] = ""
    $ _d = aig.run("t1_committee", blocking=True)
    $ _aig_test(_d["source"] == "template", "无 key 应走模板，实际 %r" % (_d["source"],))
    $ _aig_test(len(_d["lines"]) >= 1, "模板没有台词")


## 剧情拍的选项走「拍内分支 id 白名单」，不是 ACTIONS 全集
testcase pipeline_narrative:
    $ aig.reset_circuit()
    $ aig.clear_pending()
    $ _saved_turn = store.turn
    $ store.turn = 2
    $ _d = aig.run("t2_piano", fake="narrative", blocking=True)
    $ store.turn = _saved_turn
    $ _aig_test(_d["source"] == "ai", "应走 ai，实际 %r（notes=%r）" % (_d["source"], _d["notes"]))
    $ _keys = sorted(c["action_key"] for c in _d["choices"])
    $ _aig_test(_keys == ["ignore", "reveal"], "分支 id 不对：%r" % (_keys,))


## 「每局不同、同存档相同」的最小验证：新开一局的 seed 必须不同，且必须进 key
testcase seed_varies_per_run:
    $ store.ai_seeds = {}
    $ _s1 = aig.seed_for("t1_free")
    $ _s2 = aig.seed_for("t1_free")
    $ _aig_test(_s1 == _s2, "同一局内同一拍的 seed 不能变：%r vs %r" % (_s1, _s2))
    $ store.ai_seeds = {}
    $ _s3 = aig.seed_for("t1_free")
    $ _aig_test(_s1 != _s3, "两次新开局 seed 撞了，两局台词会完全一样")
    $ _aig_test(aig.key("t1_free", _s1) != aig.key("t1_free", _s3), "seed 没进 cache key")


## 自由行动变体池：起步位随机（每局不同），局内顺序确定，游标进 store
testcase free_rotation:
    $ _pool = [{"lines": [{"speaker": "inner", "text": "A"}]}, {"lines": [{"speaker": "inner", "text": "B"}]}, {"lines": [{"speaker": "inner", "text": "C"}]}]
    $ store.ai_free_counts = {}
    $ _start = aig._free_start("study", 3)
    $ _aig_test(0 <= _start <= 2, "起步位越界：%r" % (_start,))
    $ _aig_test(aig._free_start("study", 3) == _start, "起步位没存住：%r" % (_start,))
    $ _a = aig.free_scene("study", pool=_pool)[0]["text"]
    $ _b = aig.free_scene("study", pool=_pool)[0]["text"]
    $ _c = aig.free_scene("study", pool=_pool)[0]["text"]
    $ _aig_test(len({_a, _b, _c}) == 3, "三次应轮完三条不同的：%r" % ([_a, _b, _c],))
    $ _aig_test(store.ai_free_counts.get("study") == _start + 3, "游标没累计：%r" % (store.ai_free_counts,))


## 提示词数据确实编译进来了：公共四段 + 周墨八拍 + 每个 speaker 一段
testcase prompt_data:
    $ _aig_test(len(aig.PARAS) >= 25, "段落数不对：%d" % len(aig.PARAS))
    $ _aig_test(all(k in aig.PARAS for k in ("P_A", "P_B", "P_C", "P_D")), "公共段缺")
    $ _aig_test(all(("P_zm_%d" % n) in aig.PARAS for n in range(1, 9)), "周墨八拍缺")
    $ _m = aig.build_messages("t1_night_piano", 1, {"study": 30, "stress": 10, "stamina": 40, "money": 100, "ap": 3, "flags": [], "name": "测试", "actions": ("study",)})
    $ _aig_test(len(_m) == 2 and _m[0]["role"] == "system", "消息结构不对")
    $ _aig_test("只输出一个 JSON 对象" in _m[1]["content"], "输出契约没进 user 消息")
    $ _aig_test(_m[1]["content"].index("出场角色段") < _m[1]["content"].index("只输出一个 JSON 对象"),
                 "输出契约没排在角色段之后（近因效应就没了）")
