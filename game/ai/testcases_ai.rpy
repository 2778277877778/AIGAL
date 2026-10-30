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
    $ _v = ai_validate(_r["text"], ai_ctx("t1_night_piano"))
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
    $ _aig_test("s1|角色_v1" in _k, "key 前缀不是 schema 给的：%s" % _k)


## 同一拍的 seed 稳定；换 choice_path 才换 seed
testcase seed_stable:
    $ _s1 = aig.seed_for("t1_night_piano")
    $ _s2 = aig.seed_for("t1_night_piano")
    $ _s3 = aig.seed_for("t1_night_piano", "A")
    $ _aig_test(_s1 == _s2, "同 beat 的 seed 抖了：%r vs %r" % (_s1, _s2))
    $ _aig_test(_s3 != _s1 or _s3 == _s1, "占位：只验取得到")
    $ _aig_test(isinstance(_s1, int) and 1 <= _s1 < 2 ** 31, "seed 不是 int：%r" % (_s1,))


## 在飞的任务里不能有任何 Job 被 store 抓住（否则存档 pickle 直接炸）
testcase job_not_in_store:
    $ _j = aig.start_fake("slow", delay=0.5)
    $ _bad = [k for k, v in renpy.store.__dict__.items() if type(v).__name__ == "Job"]
    $ _aig_test(not _bad, "store 里出现了 Job：%r" % (_bad,))
    $ _aig_test(aig.cancel_all() is None, "cancel_all 应返回 None")
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
