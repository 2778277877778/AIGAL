################################################################################
## ai/settings.rpy —— 接口设置、连接测试、生成中界面（M3）
##
## 这层只做三件事，不另开一套传输：
##   1. 读写 persistent.ai_cfg —— 键名跟 director.DEFAULT_CFG 同一份，不另存
##   2. 测试连接 —— 真发一条 max_tokens=1 的请求，只走 start_http，不自己起线程
##   3. wait_ui —— 给 provider.wait 套一层「生成中」界面，Esc/按钮取消后照常降级
##
## 为什么测试连接不用 GET /v1/models：provider 回来只取 choices[0].message.content，
## /models 的响应剥不出正文，200 也会被报成「响应不是 OpenAI 兼容格式」。
## 用 1 token 的对话探针更实在：路径、key、model 三件事一次验完。
##
## director 侧要换的四处（见群里那条消息）：
##   wait(jid, timeout=SOFT_TIMEOUT, soft=True)   ->  wait_ui(jid, soft=True)
##   wait(jid2, timeout=SOFT_TIMEOUT, soft=True)  ->  wait_ui(jid2, soft=True)
##   wait(p["jid"], timeout=TIMEOUT)              ->  wait_ui(p["jid"], timeout=TIMEOUT)
##   c.get("api_key")  (api_ready / _dispatch)    ->  key_effective()
## 换之前：设置页能用，但「仅本次会话」的 key 和玩家改的超时进不到请求里。
##
## key 的落盘口径（README 里也这么写，别改口径）：
##   persistent 模式  -> 明文写 persistent，界面如实提示
##   session 模式     -> 只在 _SESSION 里，不写 persistent；重启后要重填
##   切模式时不丢 key，直接搬进对应的地方
################################################################################

init -2 python in aig:

    import time

    ## 设置项范围：手改 persistent 也夹得回来，界面不给输错的机会。
    TEMP_MIN, TEMP_MAX = 0.0, 2.0
    TIMEOUT_MIN, TIMEOUT_MAX = 4.0, 60.0
    TEMP_STEPS = (0.4, 0.6, 0.8, 1.0, 1.2)
    TIMEOUT_STEPS = (6, 8, 12, 20, 30)

    ## 生成中界面：快请求不打扰玩家（到 0.35s 还没回来才浮出来）。
    GEN_SHOW_DELAY = 0.35

    ## 会话专用 key。不进 persistent、不进存档，重启即没。
    _SESSION = {"key": ""}

    ## 连接测试的状态（界面只读，不阻塞）。
    PROBE = {"jid": 0, "state": "", "error": "", "t0": 0.0}

    ## 最近一次请求的原始返回：诊断页看它，M2 调提示词时最有用的就是这段。
    ## 4000 字够看出 JSON 断在哪，又不至于把内存堆起来。
    LAST = {"jid": 0, "state": "", "elapsed": 0.0, "error": "",
            "text": "", "when": 0.0}

    ## 生成中界面的当前状态。jid 为 0 表示没在等。
    GEN = {"jid": 0, "elapsed": 0.0, "shown": False, "skipped": False, "mode": ""}

    ## 界面缓冲：输入框用，用完即清（key 不留在 store 里等存档）。
    def ui_load():
        """进设置页时灌一次缓冲。已存的 key 不回填——不回填就没的地方漏明文。"""
        c = cfg()
        s = renpy.store
        s.ai_buf_url = c.get("base_url") or ""
        s.ai_buf_model = c.get("model") or ""
        s.ai_buf_key = ""
        return True

    def _clamp(v, lo, hi, dflt):
        try:
            v = float(v)
        except Exception:
            return dflt
        if v != v:                  # NaN
            return dflt
        return max(lo, min(hi, v))

    def conf(name, default=None):
        return cfg().get(name, default)

    def set_conf(name, value):
        """写一项配置。字符串去空白，数值夹紧，写完标脏 persistent。"""
        c = cfg()
        if name == "temperature":
            value = round(_clamp(value, TEMP_MIN, TEMP_MAX, 0.8), 2)
        elif name == "timeout":
            value = round(_clamp(value, TIMEOUT_MIN, TIMEOUT_MAX, SOFT_TIMEOUT), 1)
        elif name == "json_mode":
            value = bool(value)
        else:
            value = ("" if value is None else str(value)).strip()
        c[name] = value
        renpy.game.persistent.ai_cfg = c
        return value

    def cfg_timeout():
        """玩家可改的等待上限。默认沿用 director 的 SOFT_TIMEOUT（8s）。"""
        return _clamp(cfg().get("timeout", SOFT_TIMEOUT),
                      TIMEOUT_MIN, TIMEOUT_MAX, SOFT_TIMEOUT)

    ## key ####################################################################

    def key_mode():
        m = cfg().get("key_mode")
        return m if m in ("persistent", "session") else "persistent"

    def key_effective():
        """请求层唯一该拿 key 的入口（director 的 api_ready / _dispatch 换成它）。"""
        if key_mode() == "session":
            return _SESSION.get("key") or ""
        return cfg().get("api_key") or ""

    def set_key(text, remember=None):
        """remember: True 落 persistent / False 只留内存 / None 跟当前模式。"""
        text = (text or "").strip()
        if remember is None:
            remember = (key_mode() == "persistent")
        if remember:
            _SESSION["key"] = ""
            set_conf("api_key", text)
            set_conf("key_mode", "persistent")
        else:
            set_conf("api_key", "")         # 会话模式不把明文留在盘上
            _SESSION["key"] = text
            set_conf("key_mode", "session")
        return text

    def set_key_mode(mode):
        """切模式时把 key 搬到对应的地方，别让玩家填两次。"""
        if mode not in ("persistent", "session"):
            return key_mode()
        cur = key_effective()
        if mode == "session":
            _SESSION["key"] = cur
            set_conf("api_key", "")
        else:
            set_conf("api_key", cur)
            _SESSION["key"] = ""
        set_conf("key_mode", mode)
        return mode

    def clear_key():
        _SESSION["key"] = ""
        set_conf("api_key", "")
        return True

    def mask_key():
        """界面/诊断页只显示掩码，截图发群里也不漏 key。"""
        k = key_effective()
        if not k:
            return "（未填写）"
        if len(k) <= 10:
            return k[:2] + "••••"
        return "%s…%s（%d 位）" % (k[:4], k[-4:], len(k))

    def ready():
        c = cfg()
        return bool(key_effective().strip()) and bool((c.get("base_url") or "").strip())

    ## 界面动作 ################################################################

    ## 常见端点的一键填法。不联网、不猜：只是把地址和模型名填进框里。
    ## 名字和模型按 2026-10 的公开文档写；端点改了就改这张表，别在别处硬编码。
    PRESETS = (
        ("OpenAI", "https://api.openai.com/v1", "gpt-4o-mini"),
        ("DeepSeek", "https://api.deepseek.com/v1", "deepseek-chat"),
        ("本地 Ollama", "http://127.0.0.1:11434/v1", "qwen2.5:7b"),
    )

    def apply_preset(i):
        """一键填 base_url + model。key 不动——那是玩家自己的东西。"""
        try:
            name, url, model = PRESETS[int(i)]
        except Exception:
            return False
        set_conf("base_url", url)
        set_conf("model", model)
        ui_load()                           # 填完立刻回显到输入框
        renpy.notify("已填入 %s 的地址和模型，记得点保存" % name)
        return True

    def dirty():
        """文本框里有没保存的改动吗（数字项是点了就生效，不算）。"""
        s = renpy.store
        c = cfg()
        return ((s.ai_buf_url or "") != (c.get("base_url") or "")
                or (s.ai_buf_model or "") != (c.get("model") or "")
                or bool((s.ai_buf_key or "").strip()))

    def ui_save():
        s = renpy.store
        set_conf("base_url", s.ai_buf_url)
        set_conf("model", s.ai_buf_model)
        k = (s.ai_buf_key or "").strip()
        if k:
            set_key(k)
        s.ai_buf_key = ""                   # 填完就清，不在 store 里过夜
        if not (s.ai_buf_model or "").strip():
            renpy.notify("存了，但 model 还空着：发请求会被端点拒")
        else:
            renpy.notify("接口参数已保存")
        return True

    def ui_clear_buf():
        """离开设置页时清掉 key 缓冲：没点保存也不许留着明文进下一次存档。"""
        renpy.store.ai_buf_key = ""
        return True

    def ui_reset():
        """回默认：只回接口参数，key 和模式不动（免得玩家一按就丢 key）。"""
        for name in ("base_url", "model", "temperature", "timeout", "json_mode"):
            set_conf(name, DEFAULT_CFG[name])
        ui_load()
        renpy.notify("接口参数已回到默认")
        return True

    def last_text():
        return LAST.get("text") or ""

    ## 版面硬边界（美工实测，1080p 基准）：正文 24px、框宽 744px、正文区高 142px，
    ## 约每行 31 字、可放 4 行 —— 124 字是物理上限，超了 Ren'Py 不裁切，直接压到画面上。
    ## 三道线各归各管，别混：
    ##   80   提示词目标（3 行，留余量）       —— 本文件的告警线
    ##   100  校验上限（schema_core.LINE_MAX）  —— 超了 ai_validate 会剔行
    ##   124  版面物理上限
    LINE_PROMPT_TARGET = 80
    LINE_FLOOR_MAX = 124

    def line_schema_max():
        """校验上限以 schema_core 为准（Chief 定稿 100），取不到才退回 100。"""
        mod = getattr(renpy.store, "aischema", None)
        try:
            return int(getattr(mod, "LINE_MAX", 100))
        except Exception:
            return 100

    def last_summary():
        """解析最近一次原始返回，给出与版面相关的事实。

        只读 JSON，不校验、不改状态（校验是 schema 的活）。解析不了就返回 ok=False。
        """
        info = {"ok": False, "lines": 0, "longest": 0, "mood": "",
                "over_target": 0, "over_max": 0}
        raw = LAST.get("text") or ""
        if not raw:
            return info
        try:
            data = json.loads(raw)
        except Exception:
            return info
        if not hasattr(data, "get"):
            return info
        info["ok"] = True
        info["mood"] = str(data.get("mood") or "")
        lines = data.get("lines") or []
        info["lines"] = len(lines)
        lim = line_schema_max()
        for ln in lines:
            if not hasattr(ln, "get"):
                continue
            n = len((ln.get("text") or "").strip())
            if n > info["longest"]:
                info["longest"] = n
            if n > LINE_PROMPT_TARGET:
                info["over_target"] += 1
            if n > lim:
                info["over_max"] += 1
        return info

    def dbg(s):
        """把任意文本安全地塞进界面：{ 和 [ 都是 Ren'Py 标记，先转义再显示。"""
        s = "" if s is None else str(s)
        return s.replace("{", "{{").replace("[", "[[")

    ## 测试连接 ################################################################

    def probe():
        """真发一条 1 token 请求。返回 job id；0 = 没发出去（离线/跳过/没填）。"""
        PROBE.update(jid=0, state="running", error="", t0=time.time())
        c = cfg()
        if not ready():
            PROBE.update(state="error", error="base_url 或 key 没填，不会发请求。")
            return 0
        url = (c.get("base_url") or "").rstrip("/") + "/chat/completions"
        body = {
            "model": c.get("model") or "",
            "messages": [{"role": "user", "content": "ping"}],
            "max_tokens": 1,
            "temperature": 0,
        }
        headers = {
            "Authorization": "Bearer " + key_effective(),
            "Content-Type": "application/json",
        }
        jid = start_http(url, headers, body, tag="probe")
        if not jid:
            PROBE.update(state="error",
                         error="没发出去：熔断离线或快进中（诊断页可重置熔断）。")
            return 0
        PROBE.update(jid=jid, state="running")
        return jid

    def probe_poll():
        """界面每帧调一次，只读不阻塞。返回 (state, 给玩家看的一句话)。"""
        jid = PROBE.get("jid") or 0
        if not jid:
            return PROBE.get("state") or "", PROBE.get("error") or ""
        r = result(jid)
        st = r["state"]
        if st == "running":
            if time.time() - (PROBE.get("t0") or 0.0) > cfg_timeout() + 1.0:
                cancel(jid)
                PROBE.update(state="error",
                             error="%d 秒没回话，已取消（端点太慢或连不上）。"
                                   % int(cfg_timeout() + 1))
                return "error", PROBE["error"]
            return "running", "测试中…"
        if st == "done":
            PROBE.update(state="done", error="")
            return "done", "连接正常：路径、key、model 都对得上。"
        PROBE.update(state="error", error=_probe_hint(r.get("error")))
        return "error", PROBE["error"]

    def _probe_hint(err):
        e = str(err or "")
        if "401" in e or "403" in e:
            return e + "   →  key 不被接受。"
        if "404" in e:
            return e + "   →  路径或 model 不存在。base_url 一般写到 /v1 为止。"
        if "429" in e:
            return e + "   →  被限流，过一会儿再试。"
        if "HTTP 5" in e:
            return e + "   →  端点自己出错，不是你的配置问题。"
        low = e.lower()
        if "timeout" in low or "timed out" in low:
            return e + "   →  超时：端点慢或网络不通。"
        if "ssl" in low or "certificate" in low:
            return e + "   →  证书问题，多半是代理。"
        if "connection" in low or "name or service" in low:
            return e + "   →  连不上：检查 base_url 和网络。"
        if "openai 兼容" in e:
            return e + "   →  回的不是 OpenAI 格式，检查 base_url 是不是中转站根路径。"
        return e

    ## 生成中界面 ##############################################################

    def _gen_show(elapsed):
        GEN["elapsed"] = elapsed
        if not GEN["shown"] and elapsed >= GEN_SHOW_DELAY:
            GEN["shown"] = True
            renpy.show_screen("ai_generating")

    def _gen_hide():
        if GEN["shown"]:
            try:
                renpy.hide_screen("ai_generating")
            except Exception:
                pass
        GEN["shown"] = False

    def skip_generating():
        """Esc / 界面上的「跳过」：取消在飞请求。

        取消不等于出错：director 拿到非 done 就去取模板，这一拍照常演下去。
        """
        jid = GEN.get("jid") or 0
        if not jid:
            return False
        GEN["skipped"] = True
        cancel(jid)
        return True

    def wait_ui(jid, timeout=None, soft=True, blocking=False, tick=None, beat_id=None, choice_path=""):
        """provider.wait 的界面版。除 blocking（测试）外，跟 wait 的可观察行为一致。

        blocking=True 时绝不碰界面：自测里没有交互循环，show_screen 没有意义。
        timeout 传 None 就用玩家设置的那个上限（默认 8s）。
        """
        if not jid:
            return result(jid)
        budget = cfg_timeout() if timeout is None else float(timeout)
        ## beat_id / choice_path 只用于「这一拍正在生成」的浮层文案与「重跑这一拍」按钮，
        ## 不影响等待本身；不传时浮层退化成通用文案。
        GEN.update(jid=jid, elapsed=0.0, shown=False, skipped=False,
                   beat=beat_id or "", choice_path=choice_path or "")

        def _composed(elapsed):
            if not blocking:
                _gen_show(elapsed)
            if tick is not None:
                tick(elapsed)

        try:
            r = wait(jid, timeout=budget, tick=_composed,
                     blocking=blocking, soft=soft)
        finally:
            if not blocking:
                _gen_hide()
            GEN["jid"] = 0
            GEN["beat"] = ""
            GEN["choice_path"] = ""

        r_text = r.get("text") or ""
        LAST.update(jid=jid, state=r["state"], elapsed=r.get("elapsed") or 0.0,
                    error=r.get("error") or "", when=time.time(),
                    text=r_text[:4000])
        if GEN.get("skipped"):
            ## 玩家按了跳过：正文本来就不要了，记一笔好让诊断页说得清
            LAST["state"] = "skipped"

        ## 降级横幅不在这里弹：wait_ui 返回的时候导演层还没落档（_sticky 在它之后调），
        ## 在这儿判「有没有被钉住」必然早一拍。弹的时机只有一个——_sticky 落档之后。
        return r

    ## 降级横幅：一出即定之后的当场出口 ########################################
    ## 记录只有一份，在导演层（LAST_DEGRADED / degraded_now()）。这层不另存状态，
    ## 否则两处必然漂：一处说「已钉住」，另一处说「没有」。
    ## 这层只负责「什么时候弹」和「长什么样」。

    def degraded_line():
        why = degraded_now().get("reason") or ""
        if why:
            return "这一拍用的是本地文本（%s）。同一存档以后这一拍也是这段。" % why
        return "这一拍用的是本地文本。同一存档以后这一拍也是这段。"

    def degrade_banner():
        """弹横幅。导演层 _sticky 落档之后叫一次 —— 七条降级路径（含校验不过）就都齐了。"""
        try:
            renpy.show_screen("ai_degraded")
        except Exception:
            return False
        return True

    def damp_degraded():
        try:
            renpy.hide_screen("ai_degraded")
        except Exception:
            pass
        return True

    def rerun_beat():
        """玩家当场要求重跑：解除钉住（缓存 + 模板 + seed），再由 Rollback() 回到本拍开头。"""
        ok = reroll_last()
        damp_degraded()
        if not ok:
            renpy.notify("这一拍已经没有可重跑的记录了")
            return False
        renpy.notify("这一拍已解除钉住：回到本拍开头会重新生成")
        return True

    ## 调试：假请求走一遍完整界面路径（诊断页按钮用）##########################

    def debug_fake(mode="ok", delay=0.3):
        jid = start_fake(mode, delay=delay, tag="debug")
        if not jid:
            return None
        return wait_ui(jid, soft=True)

    ## 诊断页的表格与最近一次返回 ##############################################

    def clear_last():
        LAST.update(jid=0, state="", elapsed=0.0, error="", text="", when=0.0)
        return True

    def last_line():
        if not LAST.get("jid"):
            return "（还没有请求）"
        when = ""
        if LAST.get("when"):
            when = time.strftime("%H:%M:%S", time.localtime(LAST["when"])) + " "
        return "%s%s · %.1fs%s" % (
            when, LAST.get("state") or "?", LAST.get("elapsed") or 0.0,
            ("  · " + LAST["error"]) if LAST.get("error") else "")

    def debug_table():
        """诊断页要的一屏事实。全部现算，不缓存 —— 这页本来就是用来看漂移的。"""
        st = status()
        cs = stats()
        c = cfg()
        store = renpy.store
        beats = getattr(store, "AI_BEATS", None) or {}
        actions = getattr(store, "ACTIONS", None) or {}
        rows = [
            ("连接", "在线" if st["online"] else "离线（熔断中，可下拉重置）"),
            ("连续失败 / 上限", "%d / %d" % (st["consec_fail"], FAIL_LIMIT)),
            ("请求 / 失败", "%d / %d" % (st["requests"], st["fails"])),
            ("在飞 / 任务表", "%d / %d" % (st["running"], st["jobs"])),
            ("预取在飞", "%d" % pending_count()),
            ("key 模式", "仅本次会话（只在内存）" if key_mode() == "session" else "记住（明文写盘）"),
            ("key", mask_key()),
            ("base_url", c.get("base_url") or ""),
            ("model", c.get("model") or ""),
            ("temperature", "%.2f" % _clamp(c.get("temperature", 0.8), TEMP_MIN, TEMP_MAX, 0.8)),
            ("timeout", "%d 秒%s" % (cfg_timeout(),
                                    "" if abs(cfg_timeout() - 8) < 0.1 else "（默认 8）")),
            ("json_mode", "开" if c.get("json_mode") else "关"),
            ("缓存 key 前缀", cs["prefix"]),
            ("缓存（本局）", "%d 条 / %d 字" % (cs["session_entries"], cs["session_chars"])),
            ("缓存（跨局）", "%d 条 / %d 字，上限 %d" % (
                cs["persist_entries"], cs["persist_chars"], cs["persist_cap"])),
            ("提示词段落", "%d 段" % len(PARAS)),
            ("beat 表 / ACTIONS", "%d 拍 / %d 个 action_key" % (len(beats), len(actions))),
            ("当前回合 / 进度", "第 %d 回合" % getattr(store, "turn", 0)),
        ]

        ## 延迟三项：P50 / P95 / 超时率。provider 按会话收最近 50 次，
        ## 区分「模型慢 / 网络慢 / 代码慢」就看这三个数，不看平均值。
        try:
            lat = latency_stats()
        except Exception:
            lat = None
        if lat and lat.get("n"):
            rows.append(("延迟 P50 / P95", "%.2fs / %.2fs（最近 %d 次，最慢 %.2fs）"
                         % (lat["p50"], lat["p95"], lat["n"], lat["max"])))
            rows.append(("超时率 / 失败率", "%.0f%% / %.0f%%（共 %d 次请求）"
                         % (lat["timeout_rate"] * 100.0, lat["fail_rate"] * 100.0,
                            lat["requests"])))
        else:
            rows.append(("延迟 P50 / P95", "还没有采样（这一局还没发过请求）"))

        ls = last_summary()
        if ls["ok"]:
            rows.append(("最近返回", "%d 行 · 最长 %d 字 · mood=%s"
                         % (ls["lines"], ls["longest"], ls["mood"] or "（空）")))
            rows.append(("行字数", "目标 %d / 校验 %d / 版面 %d"
                         % (LINE_PROMPT_TARGET, line_schema_max(), LINE_FLOOR_MAX)))
            if ls["over_max"]:
                rows.append(("行字数告警", "%d 行超过校验上限，会被 schema 剔掉"
                             % ls["over_max"]))
            elif ls["over_target"]:
                rows.append(("行字数告警", "%d 行超过提示词目标（还没到校验线）"
                             % ls["over_target"]))
            else:
                rows.append(("行字数告警", "全部在目标以内"))
        else:
            rows.append(("最近返回", "还没有可解析的返回"))
        sticky = getattr(store, "ai_template", None) or {}
        rows.append(("钉住的拍", "%d 个（一出即定，要换只能 reroll）" % len(sticky)))
        return rows
