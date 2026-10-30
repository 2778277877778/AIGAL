################################################################################
## ai/testcases_ui.rpy —— settings / 生成中界面的自测（M3）
##
## 用法：.\dev.ps1 test ui_layer
##       .\dev.ps1 test            （跑全部套件）
##
## 这些 case 不碰网络、不碰界面：假请求走 start_fake，界面一律 blocking=True。
## 只验「配置夹紧 / key 的口径 / wait_ui 记账 / 跳过等于降级」这些能自动验的部分。
##
## 注意：这些 case 会改 persistent.ai_cfg，所以每个 case 自己存档/还原，
## 成套再在 teardown 里兜一次并 save_persistent()。
## —— 之前有一次 case 在中途失败，还原那行没跑到，把「仅本次会话」留在了
##    persistent 里，设置页下次进来就显示成会话模式。失败路径也得还原。
################################################################################

default _UI_CFG0 = None


init -1 python:

    def _ui_snap():
        """整套配置的快照：这些 case 会改 persistent，跑完必须原样还回去。"""
        return (dict(aig.cfg()), aig.key_effective(), aig.key_mode())

    def _ui_restore(snap):
        c0, key0, mode0 = snap
        c = aig.cfg()
        c.clear()
        c.update(c0)
        renpy.game.persistent.ai_cfg = c
        aig._SESSION["key"] = key0 if mode0 == "session" else ""
        if mode0 != "session":
            c["api_key"] = key0
        aig.clear_last()
        aig.reset_circuit()


testsuite ui_layer:
    setup:
        ## 5s 的默认 case 超时会被上一轮的陈旧计时器误伤（详见群里那条观察），松到 15s。
        $ _test.timeout = 15
        $ _UI_CFG0 = _ui_snap()
    teardown:
        ## 兜底：哪个 case 中途挂了也不会把配置留在半路上
        $ _ui_restore(_UI_CFG0)
        $ renpy.save_persistent()
        exit


## 设置项的夹紧：手改 persistent 也不能把 temperature 填成 5、timeout 填成 1
testcase cfg_clamp:
    $ _s = _ui_snap()
    $ aig.reset_circuit()
    $ _aig_test(abs(aig.set_conf("temperature", 5) - 2.0) < 0.001, "temperature 没夹到 2.0")
    $ _aig_test(abs(aig.set_conf("temperature", -1) - 0.0) < 0.001, "temperature 没夹到 0.0")
    $ _aig_test(abs(aig.set_conf("timeout", 1) - 4.0) < 0.001, "timeout 没夹到 4.0")
    $ _aig_test(abs(aig.set_conf("timeout", 999) - 60.0) < 0.001, "timeout 没夹到 60.0")
    $ _aig_test(aig.set_conf("base_url", "  https://x/v1  ") == "https://x/v1", "base_url 没去空白")
    $ _aig_test(abs(aig.cfg_timeout() - 60.0) < 0.001, "cfg_timeout 没跟 timeout 走")
    $ _ui_restore(_s)


## 会话模式：key 只在内存里，persistent 里必须一点痕迹都没有
testcase key_session:
    $ _s = _ui_snap()
    $ aig.set_key("sk-ui-test-session", remember=False)
    $ _aig_test(aig.key_mode() == "session", "mode 不是 session：%r" % (aig.key_mode(),))
    $ _aig_test(aig.key_effective() == "sk-ui-test-session", "key_effective 拿不到会话 key")
    $ _aig_test((aig.cfg().get("api_key") or "") == "", "会话模式还往 persistent 写了 key")
    $ _aig_test("sk-ui-test-session" not in repr(getattr(renpy.game.persistent, "__dict__", {})),
                "会话 key 出现在 persistent 里了")
    $ _m = aig.mask_key()
    $ _aig_test(aig.key_effective() not in _m, "掩码把整个 key 露出来了：%r" % (_m,))
    $ _aig_test("…" in _m or "••••" in _m, "掩码没打住：%r" % (_m,))
    $ _ui_restore(_s)


## 切模式不能把 key 弄丢：persistent -> session -> persistent
testcase key_move:
    $ _s = _ui_snap()
    $ aig.set_key("sk-ui-test-move", remember=True)
    $ _aig_test(aig.key_mode() == "persistent", "先设 persistent 失败")
    $ aig.set_key_mode("session")
    $ _aig_test(aig.key_effective() == "sk-ui-test-move", "切到 session 后 key 丢了")
    $ _aig_test((aig.cfg().get("api_key") or "") == "", "切到 session 后盘上还留着 key")
    $ aig.set_key_mode("persistent")
    $ _aig_test(aig.cfg().get("api_key") == "sk-ui-test-move", "切回 persistent 后 key 没回来")
    $ _aig_test(aig._SESSION["key"] == "", "切回 persistent 后内存里还留着 key")
    $ aig.clear_key()
    $ _aig_test(aig.key_effective() == "", "clear_key 没清干净")
    $ _ui_restore(_s)


## 没填 key 就不许发请求，且要说清楚原因
testcase probe_nokey:
    $ _s = _ui_snap()
    $ aig.reset_circuit()
    $ aig.clear_key()
    $ _before = aig.status()["requests"]
    $ _aig_test(aig.probe() == 0, "没 key 还给发请求了")
    $ _aig_test(aig.status()["requests"] == _before, "没 key 却增加了请求计数")
    $ _aig_test(aig.probe_poll()[0] == "error", "probe_poll 状态不是 error")
    $ _aig_test(not aig.ready(), "没 key 还说 ready")
    $ _ui_restore(_s)


## wait_ui 走完假请求：返回 same shape，并把原始正文档下来给诊断页
testcase waitui_fake:
    $ _s = _ui_snap()
    $ aig.reset_circuit()
    $ aig.clear_last()
    $ _j = aig.start_fake("ok", delay=0.1)
    $ _r = aig.wait_ui(_j, timeout=3.0, blocking=True)
    $ _aig_test(_r["state"] == "done", "wait_ui 没跑完：%r" % (_r,))
    $ _aig_test(aig.LAST["state"] == "done", "LAST 没记下这次结果")
    $ _aig_test("lines" in (aig.LAST["text"] or ""), "LAST 没存原始正文")
    $ _aig_test(aig.GEN["jid"] == 0, "wait_ui 结束后 GEN 没归零")
    $ _aig_test(not aig.GEN["shown"], "blocking 模式下不该显示生成中界面")
    $ _ui_restore(_s)


## 到点算超时（软的算取消）：两种都必须是「不是 done」，director 才会去取模板
testcase waitui_timeout:
    ## 假请求本身要挂满几秒，5s 的默认 case 超时不够
    $ _test.timeout = 15
    $ _s = _ui_snap()
    $ aig.reset_circuit()
    $ _j = aig.start_fake("timeout", delay=0.6)
    $ _r = aig.wait_ui(_j, timeout=0.4, soft=True, blocking=True)
    $ _aig_test(_r["state"] != "done", "超时还报 done：%r" % (_r,))
    $ aig.reset_circuit()
    $ _j2 = aig.start_fake("timeout", delay=0.6)
    $ _r2 = aig.wait_ui(_j2, timeout=0.4, soft=False, blocking=True)
    $ _aig_test(_r2["state"] == "timeout", "软关掉时状态应是 timeout，实际 %r" % (_r2,))
    $ aig.reset_circuit()
    $ _ui_restore(_s)


## 跳过 = cancel = 降级，不是报错
testcase skip_is_degrade:
    $ _test.timeout = 15
    $ _s = _ui_snap()
    $ aig.reset_circuit()
    $ _j = aig.start_fake("timeout", delay=0.6)
    $ aig.GEN["jid"] = _j
    $ _aig_test(aig.skip_generating(), "skip_generating 没取消")
    $ _aig_test(aig.GEN["skipped"], "跳过没记下来")
    $ _r = aig.wait(_j, timeout=2.0, blocking=True)
    $ _aig_test(_r["state"] == "cancelled", "跳过应是 cancelled，实际 %r" % (_r,))
    $ aig.GEN["jid"] = 0
    $ _aig_test(aig.skip_generating() is False, "没有在飞请求时不该返回 True")
    $ aig.reset_circuit()
    $ _ui_restore(_s)


## 诊断页那屏事实都得现算得出来，缺字就说明谁的表没就位
testcase debug_table:
    $ _rows = aig.debug_table()
    $ _aig_test(len(_rows) >= 15, "诊断表行数太少：%d" % len(_rows))
    $ _keys = [k for k, v in _rows]
    $ _aig_test("缓存 key 前缀" in _keys, "诊断表缺缓存前缀")
    $ _aig_test("提示词段落" in _keys, "诊断表缺提示词统计")
    $ _pfx = dict(_rows)["缓存 key 前缀"]
    $ _aig_test("|" in _pfx, "缓存前缀不像 cache.key 的前缀：%r" % (_pfx,))
    $ _aig_test(aig.last_line() != "", "last_line 给了空串")
