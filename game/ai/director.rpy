################################################################################
## ai/director.rpy —— 导演层：一拍内容从哪来、什么时候买、买不到给什么。
##
## 调用顺序固定：缓存 → 预取 → 现场请求 → 校验（失败重试一次）→ 模板降级。
## 剧本只调两个 label：ai_play / ai_menu，拿回来的东西不用管来源。
##
## 三段计时（别混）：
##   SOFT_TIMEOUT 8s   本层：到点切模板，玩家只看到一行提示，不卡
##   TIMEOUT 12s       传输层：硬超时，任务作废
##   预取            玩家在读当前拍时后台生成下一拍，等待被藏掉
##
## 预取触发点（玩法策划定的时序，别改）：
##   拍 2 / 拍 3   玩家点下选项那一刻（choice_path 定了，key 才成立）
##   自由行动包    拍 3 开演时（choice_path 恒空）
##   拍 1          上个月最后一点 AP 用掉时
################################################################################

## 自由行动变体池的轮转游标：action_key -> 已用次数。进存档，读档后接着上次的顺序。
default ai_free_counts = {}

## 已经落定的降级决定：缓存 key -> 当时那段模板。只写「再问一次也还是这个答案」的理由，见 _sticky()。
default ai_template = {}


init -1 python in aig:

    SOFT_TIMEOUT = 8.0


    ## 校验失败时的第二次请求只加这一句，不重写整段 prompt。
    RETRY_SUFFIX = (
        "上一次的输出没有通过校验。只输出一个 JSON 对象本身："
        "不要解释、不要 markdown 围栏、不要在前后加字。"
    )

    ## 上一次 run 的拍（同步调用，所以可以直接记）
    _LAST_RUN = {"beat": "", "choice_path": ""}

    ## 最近一次「一出即定」的降级：给浮层/诊断页的「重跑这一拍」按钮用
    LAST_DEGRADED = {}

    ## 在飞的预取：缓存 key -> {jid, beat, choice_path}。和 Job 表一样不进 store。
    PENDING = {}

    DEFAULT_CFG = {
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "api_key": "",
        "temperature": 0.8,
        "json_mode": True,
    }

    ## 配置：persistent 明文（设置页要如实提示），M3 做界面。
    def cfg():
        c = getattr(renpy.game.persistent, "ai_cfg", None)
        if not isinstance(c, dict):
            c = dict(DEFAULT_CFG)
            renpy.game.persistent.ai_cfg = c
        return c

    def api_ready():
        c = cfg()
        return bool(key_effective().strip()) and bool((c.get("base_url") or "").strip())

    def _state():
        s = renpy.store
        return {
            "name": renpy.store.ai_player_name(),
            "study": s.study, "stress": s.stress, "stamina": s.stamina,
            "money": s.money, "ap": s.ap,
            "flags": sorted(s.flags.keys()),
            "actions": tuple(renpy.store.ACTIONS.keys()),
        }

    def _dispatch(messages, fake=None):
        """发一次请求，返回 job id。fake 模式走假 provider（测试/演示用）。"""
        if fake:
            return start_fake(fake, delay=0.05, tag="fake")
        c = cfg()
        body = {
            "model": c.get("model"),
            "messages": messages,
            "temperature": float(c.get("temperature", 0.8)),
        }
        if c.get("json_mode"):
            ## 不是所有 OpenAI 兼容端点都认这个字段；端点报错就关掉（M3 设置页给开关）
            body["response_format"] = {"type": "json_object"}
        url = (c.get("base_url") or "").rstrip("/") + "/chat/completions"
        headers = {
            "Authorization": "Bearer " + key_effective(),
            "Content-Type": "application/json",
        }
        return start_http(url, headers, body, tag="chat")

    def _messages(beat_id, turn, ending, extra="", seed=0):
        st = _state()
        c = choices_for(beat_id)
        if c:
            ## 剧情拍的选项是分支 id，不是 ACTIONS；提示词里给的和校验用的必须是同一份
            st["actions"] = c
        return build_messages(beat_id, turn, st, ending=ending, extra=extra, seed=seed)

    def _pack(v, ctx, source, notes=None):
        return {
            "source": source,
            "lines": v["lines"],
            "choices": v["choices"],
            "flags": v["flags"],
            "mood": v["mood"],
            "notes": list(v.get("notes") or []) + list(notes or []),
            "ctx": ctx,
        }

    def _template_pack(beat_id, ctx, why):
        t = template(beat_id, (ctx or {}).get("choice_path", ""))
        return {
            "source": "template",
            "lines": t.get("lines") or [],
            "choices": t.get("choices") or [],
            "flags": [],
            "mood": t.get("mood", ""),
            "notes": [why],
            "ctx": ctx,
        }

    def _sticky(k, reason, pack):
        """一出即定：降级文本也写进存档，同一存档这一拍以后都是这一段。

        Chief 定的：seed 和 key 都没变却换了文本，是硬违约。所以超时、跳过、
        离线、连续不合格全都算「这一拍已经出过」，不再自动重买。要换只有一条路：
        显式调 reroll()（设置/调试页给按钮），不做自动重试。

        为什么不直接写进 ai_cache：那层存的是模型原文，回读时要再过一次校验，
        而模板里的空 action_key / 未登记的 speaker 会被校验剔掉，菜单拍会丢选项。
        """
        renpy.store.ai_template = dict(renpy.store.ai_template, **{k: {
            "source": "template",
            "lines": pack["lines"],
            "choices": pack["choices"],
            "flags": [],
            "mood": pack["mood"],
            "notes": [reason],
        }})
        ## 记下这一拍：浮层的「重跑这一拍」按钮和诊断页都读它
        LAST_DEGRADED.update(k=k, beat=_LAST_RUN["beat"],
                             choice_path=_LAST_RUN["choice_path"], reason=reason)
        ## 横幅也走这条：invalid_twice 是 wait 之后才判的，wait_ui 里看不见，
        ## 少了这一句，校验不过的降级就不会弹横幅。
        ## 注意 degrade_banner() 是**无参**的：拍和理由都已经在 LAST_DEGRADED 里，
        ## 它只负责 show_screen。之前这里传过三个参数，被下面的 except 吞掉，
        ## 结果横幅一直不弹 —— 所以异常改成记日志，不再静默。
        try:
            degrade_banner()
        except Exception as e:
            renpy.log("[AIGAL] degrade_banner 失败：%r" % (e,))
        return pack

    def reroll_last():
        """重跑最近一次被降级钉住的拍。没有就返回 False（按钮据此禁用）。"""
        if not LAST_DEGRADED.get("beat"):
            return False
        reroll(LAST_DEGRADED["beat"], LAST_DEGRADED.get("choice_path", ""))
        LAST_DEGRADED.clear()
        return True

    def degraded_now():
        """当前这一幕有没有被钉住的拍（浮层/诊断页决定按钮显不显示）。"""
        return dict(LAST_DEGRADED)

    def reroll(beat_id, choice_path=""):
        """玩家显式要求重跑这一拍：清掉这一拍的三处记录，下次 run 会掷新 seed 重买。

        清的是：两层正文缓存、降级记录、这一拍的 seed。seed 不清就会算出同一个 key，
        又命中同一份缓存，等于没重跑。
        """
        k = key(beat_id, seed_for(beat_id, choice_path), choice_path)
        forget(k)
        renpy.store.ai_template = dict(
            (kk, vv) for kk, vv in renpy.store.ai_template.items() if kk != k
        )
        seeds = dict(renpy.store.ai_seeds)
        seeds.pop("%s|%s" % (beat_id, choice_path), None)
        renpy.store.ai_seeds = seeds
        return k

    def _ctx(beat_id, expect_choices=None):
        kw = {
            "speakers": speakers_for(beat_id),
            "expect_choices": expect_choices,
        }
        c = choices_for(beat_id)
        if c:
            kw["actions"] = c
        return renpy.store.ai_ctx(beat_id, **kw)

    def _fake_ctx(beat_id):
        """beat 没登记时也要能返回一个能用的 ctx（不然剧本直接崩）。"""
        return {
            "beat": beat_id, "turn": renpy.store.turn,
            "speakers": speakers_for(beat_id), "actions": (),
            "flags": (), "expect_choices": False,
        }

    ## 主入口 ####################################################################

    def run(beat_id, choice_path="", fake=None, expect_choices=None, blocking=False, extra=""):
        """取这一拍的内容。返回 {source, lines, choices, flags, mood, notes, ctx}。

        source 只会是 cache / prefetch / ai / ai_retry / template 之一。
        剧本不要按 source 分支——降级文本和 AI 文本同构。
        """
        renpy.store.trace_beat(beat_id)
        _LAST_RUN["beat"] = beat_id
        _LAST_RUN["choice_path"] = choice_path
        ok, why = renpy.store.ai_beat_ok(beat_id)
        if not ok:
            return _template_pack(beat_id, _fake_ctx(beat_id), why)

        b = renpy.store.ai_beat(beat_id)
        turn = b["turn"]
        ctx = _ctx(beat_id, expect_choices)
        ## choice_path 要跟着 ctx 走：降级取模板时靠它选「拍 + 分支」那一版，
        ## 少了它，自由行动 11 个动作会全部渲染成同一个拍默认段。
        ctx["choice_path"] = choice_path
        seed = seed_for(beat_id, choice_path)
        k = key(beat_id, seed, choice_path)

        ## 0. 存档里已经落定的降级：同一存档同一拍，读两次必须一样
        stick = renpy.store.ai_template.get(k)
        if stick is not None:
            return dict(stick, ctx=ctx)

        ## 1. 缓存
        cached = get(k)
        if cached:
            v = renpy.store.ai_validate(cached, ctx)
            if v["ok"]:
                return _pack(v, ctx, "cache")
            forget(k)                       # 校验不过的缓存不再命中，当没缓存

        ## 2. 预取在飞：等它，等不到就往下走现场请求
        p = PENDING.pop(k, None)
        if p is not None:
            r = wait_ui(p["jid"], timeout=TIMEOUT, blocking=blocking)
            if r["state"] == "done":
                v = renpy.store.ai_validate(r["text"], ctx)
                if v["ok"]:
                    put(k, r["text"])
                    return _pack(v, ctx, "prefetch")

        ## 3. 不能买：没 key / 离线 / Ctrl 跳过中
        if fake is None and not api_ready():
            return _sticky(k, "no_api_key", _template_pack(beat_id, ctx, "no_api_key"))
        if not allowed():
            return _sticky(k, "offline_or_skipping", _template_pack(beat_id, ctx, "offline_or_skipping"))

        ending = (b.get("scope") == "ending")
        jid = _dispatch(_messages(beat_id, turn, ending, extra, seed), fake)
        if not jid:
            return _sticky(k, "not_sent", _template_pack(beat_id, ctx, "not_sent"))

        r = wait_ui(jid, soft=True, blocking=blocking)
        if r["state"] != "done":
            ## 8s 软降级：只提示一行，不打断；迟到成功也不会再把这一拍换回来
            return _sticky(k, "soft_" + str(r["state"]), _template_pack(beat_id, ctx, "soft_" + str(r["state"])))

        v = renpy.store.ai_validate(r["text"], ctx)
        if v["ok"]:
            put(k, r["text"])
            return _pack(v, ctx, "ai")

        ## 4. 校验失败：重试一次（只补一句约束，不重写整段 prompt）
        msgs = _messages(beat_id, turn, ending, extra, seed)
        msgs.append({"role": "user", "content": RETRY_SUFFIX})
        jid2 = _dispatch(msgs, fake)
        if not jid2:
            return _sticky(k, "retry_not_sent", _template_pack(beat_id, ctx, "retry_not_sent"))

        r2 = wait_ui(jid2, soft=True, blocking=blocking)
        if r2["state"] != "done":
            return _sticky(k, "retry_" + str(r2["state"]), _template_pack(beat_id, ctx, "retry_" + str(r2["state"])))
        v2 = renpy.store.ai_validate(r2["text"], ctx)
        if v2["ok"]:
            put(k, r2["text"])
            return _pack(v2, ctx, "ai_retry")
        return _sticky(k, "invalid_twice", _template_pack(beat_id, ctx, "invalid_twice"))

    def prefetch(beat_id, choice_path="", fake=None, extra=""):
        """后台买下一拍。返回 job id（0 = 没发，调用方不用管）。"""
        ok, why = renpy.store.ai_beat_ok(beat_id)
        if not ok:
            return 0
        if fake is None and not api_ready():
            return 0
        if not allowed():
            return 0

        b = renpy.store.ai_beat(beat_id)
        seed = seed_for(beat_id, choice_path)
        k = key(beat_id, seed, choice_path)
        if get(k):
            return 0                        # 已经买过
        if k in PENDING:
            return 0                        # 已经在飞

        jid = _dispatch(_messages(beat_id, b["turn"], b.get("scope") == "ending", extra, seed), fake)
        if jid:
            PENDING[k] = {"jid": jid, "beat": beat_id, "choice_path": choice_path}
        return jid

    def pending_count():
        return len(PENDING)

    def clear_pending():
        for kk in list(PENDING.keys()):
            cancel(PENDING[kk]["jid"])
        PENDING.clear()

    ## 自由行动正文（不调 AI）######################################################

    def _free_pool(action_key):
        """取一个行动的变体池。

        池子在 fallback.rpy：FREE_VARIANTS = {"attend_class": [变体0, 变体1, 变体2], ...}
        每个变体和 FALLBACK 里一个拍同形状（lines / mood）。没写池子就退回该月的拍模板。
        """
        pool = globals().get("FREE_VARIANTS") or {}
        one = pool.get(action_key)
        if one:
            return one
        single = FALLBACK.get("free_" + action_key)
        if isinstance(single, (list, tuple)):
            return single
        return ()

    def _free_start(action_key, n):
        """本局第一次点到这个行动时，随机挑一个起步位。

        为什么要有它：轮转本身是确定的，如果所有玩家都从 0 开始，33 条变体读到的
        顺序就完全一样——「每局对话不同」在自由行动这段直接失效。
        起步位从本局随机数里抽一次并存进存档，于是：新开一局是新起步位；
        同一存档回滚或读档，还接着那个位置走，一字不差。
        """
        counts = renpy.store.ai_free_counts
        if action_key in counts:
            return int(counts[action_key])
        start = renpy.random.randint(0, max(0, n - 1))
        renpy.store.ai_free_counts = dict(counts, **{action_key: start})
        return start

    def free_scene(action_key, pool=None, beat_id=None):
        """取这一次自由行动的台词，返回 lines（[(speaker, text)] 结构的字典列表）。

        随机只是起步位：每句单独随机会有 1/3 概率连着重复同一句，轮转不会。
        """
        if beat_id is None:
            beat_id = "t%d_free" % renpy.store.turn
        variants = pool if pool is not None else _free_pool(action_key)
        if not variants:
            ## 还没写池子：退回 fallback 里 act/<action_key> 那一版，宁可平淡也不要空白
            return template(beat_id, action_key).get("lines") or []

        n = _free_start(action_key, len(variants))
        v = variants[n % len(variants)]
        renpy.store.ai_free_counts = dict(
            renpy.store.ai_free_counts, **{action_key: n + 1}
        )
        ## 用 hasattr 而不是 isinstance(v, dict)：命名空间里的 dict 被 Ren'Py 换成了
        ## RevertableDict，测试里造的普通 dict 反而不认，会把变体当成序列拆成键名。
        if hasattr(v, "get"):
            return v.get("lines") or []
        return list(v)

    ## 预取：下个月第一拍 ##########################################################

    def prefetch_first(turn_no):
        """预取某个回合的第一拍（按 beat 表里的登记顺序）。

        T3 起的拍还没登记时返回 0 —— 调用方不用判断，登记之后自动生效。
        """
        for bid, b in renpy.store.AI_BEATS.items():
            if b.get("turn") == turn_no and bid.startswith("t%d_" % turn_no):
                return prefetch(bid)
        return 0


## 剧本层入口 ####################################################################
## call ai_play("t2_piano")                 —— 只演台词，不给选项
## call ai_menu("t2_piano")                 —— 演完台词给选项，返回值从 _return 取
## call ai_prefetch("t2_gala")              —— 只预取，不等
##
## extra 是本拍的既定事实（月考过没过、上一拍选了什么）。它不参与缓存 key，
## 所以凡是 extra 会变的分支，一定要把区分写进 choice_path，不然两个版本会撞缓存。

label ai_play(beat_id, choice_path="", extra=""):
    $ _ai_d = aig.run(beat_id, choice_path, expect_choices=False, extra=extra)
    $ ai_say(_ai_d["lines"])
    $ ai_apply_flags(_ai_d["flags"], _ai_d["ctx"])
    return _ai_d


label ai_menu(beat_id, choice_path="", extra=""):
    $ _ai_d = aig.run(beat_id, choice_path, expect_choices=True, extra=extra)
    $ ai_say(_ai_d["lines"])
    $ ai_apply_flags(_ai_d["flags"], _ai_d["ctx"])
    ## 兜底那一项必须给可点的值：display_menu 里 value=None 是标题，不是选项。
    $ _ai_items = [(c["text"], c["action_key"]) for c in _ai_d["choices"]] or [("（继续）", "")]
    $ _ai_pick = renpy.display_menu(_ai_items)
    return _ai_pick


label ai_prefetch(beat_id, choice_path="", extra=""):
    $ _ai_jid = aig.prefetch(beat_id, choice_path, extra=extra)
    return _ai_jid


## 自由行动的正文：不调 AI，从 fallback.rpy 的变体池按「本局已用次数」轮转。
## 数值变化已经由 do_action 结算完了，这里只出文字。
label ai_free_scene(action_key):
    $ ai_say(aig.free_scene(action_key))
    return
