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

init -1 python in aig:

    SOFT_TIMEOUT = 8.0

    ## 校验失败时的第二次请求只加这一句，不重写整段 prompt。
    RETRY_SUFFIX = (
        "上一次的输出没有通过校验。只输出一个 JSON 对象本身："
        "不要解释、不要 markdown 围栏、不要在前后加字。"
    )

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
        return bool((c.get("api_key") or "").strip()) and bool((c.get("base_url") or "").strip())

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
            "Authorization": "Bearer " + (c.get("api_key") or ""),
            "Content-Type": "application/json",
        }
        return start_http(url, headers, body, tag="chat")

    def _messages(beat_id, turn, ending):
        return build_messages(beat_id, turn, _state(), ending=ending)

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
        t = template(beat_id)
        return {
            "source": "template",
            "lines": t.get("lines") or [],
            "choices": t.get("choices") or [],
            "flags": [],
            "mood": t.get("mood", ""),
            "notes": [why],
            "ctx": ctx,
        }

    def _ctx(beat_id, expect_choices=None):
        return renpy.store.ai_ctx(
            beat_id,
            speakers=speakers_for(beat_id),
            expect_choices=expect_choices,
        )

    def _fake_ctx(beat_id):
        """beat 没登记时也要能返回一个能用的 ctx（不然剧本直接崩）。"""
        return {
            "beat": beat_id, "turn": renpy.store.turn,
            "speakers": speakers_for(beat_id), "actions": (),
            "flags": (), "expect_choices": False,
        }

    ## 主入口 ####################################################################

    def run(beat_id, choice_path="", fake=None, expect_choices=None, blocking=False):
        """取这一拍的内容。返回 {source, lines, choices, flags, mood, notes, ctx}。

        source 只会是 cache / prefetch / ai / ai_retry / template 之一。
        剧本不要按 source 分支——降级文本和 AI 文本同构。
        """
        ok, why = renpy.store.ai_beat_ok(beat_id)
        if not ok:
            return _template_pack(beat_id, _fake_ctx(beat_id), why)

        b = renpy.store.ai_beat(beat_id)
        turn = b["turn"]
        ctx = _ctx(beat_id, expect_choices)
        seed = seed_for(beat_id, choice_path)
        k = key(beat_id, seed, choice_path)

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
            r = wait(p["jid"], timeout=TIMEOUT, blocking=blocking)
            if r["state"] == "done":
                v = renpy.store.ai_validate(r["text"], ctx)
                if v["ok"]:
                    put(k, r["text"])
                    return _pack(v, ctx, "prefetch")

        ## 3. 不能买：没 key / 离线 / Ctrl 跳过中
        if fake is None and not api_ready():
            return _template_pack(beat_id, ctx, "no_api_key")
        if not allowed():
            return _template_pack(beat_id, ctx, "offline_or_skipping")

        ending = (b.get("scope") == "ending")
        jid = _dispatch(_messages(beat_id, turn, ending), fake)
        if not jid:
            return _template_pack(beat_id, ctx, "not_sent")

        r = wait(jid, timeout=SOFT_TIMEOUT, soft=True, blocking=blocking)
        if r["state"] != "done":
            ## 8s 软降级：只提示一行，不打断；迟到成功也不会再把这一拍换回来
            return _template_pack(beat_id, ctx, "soft_" + str(r["state"]))

        v = renpy.store.ai_validate(r["text"], ctx)
        if v["ok"]:
            put(k, r["text"])
            return _pack(v, ctx, "ai")

        ## 4. 校验失败：重试一次（只补一句约束，不重写整段 prompt）
        msgs = _messages(beat_id, turn, ending)
        msgs.append({"role": "user", "content": RETRY_SUFFIX})
        jid2 = _dispatch(msgs, fake)
        if not jid2:
            return _template_pack(beat_id, ctx, "retry_not_sent")

        r2 = wait(jid2, timeout=SOFT_TIMEOUT, soft=True, blocking=blocking)
        if r2["state"] != "done":
            return _template_pack(beat_id, ctx, "retry_" + str(r2["state"]))
        v2 = renpy.store.ai_validate(r2["text"], ctx)
        if v2["ok"]:
            put(k, r2["text"])
            return _pack(v2, ctx, "ai_retry")
        return _template_pack(beat_id, ctx, "invalid_twice")

    def prefetch(beat_id, choice_path="", fake=None):
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

        jid = _dispatch(_messages(beat_id, b["turn"], b.get("scope") == "ending"), fake)
        if jid:
            PENDING[k] = {"jid": jid, "beat": beat_id, "choice_path": choice_path}
        return jid

    def pending_count():
        return len(PENDING)

    def clear_pending():
        for kk in list(PENDING.keys()):
            cancel(PENDING[kk]["jid"])
        PENDING.clear()


## 剧本层入口 ####################################################################
## call ai_play("t2_piano")            —— 只演台词，不给选项
## call ai_menu("t2_piano")            —— 演完台词给选项，返回 action_key
## call ai_prefetch("t2_gala")         —— 只预取，不等

label ai_play(beat_id, choice_path=""):
    $ _ai_d = aig.run(beat_id, choice_path)
    $ ai_say(_ai_d["lines"])
    $ ai_apply_flags(_ai_d["flags"], _ai_d["ctx"])
    return _ai_d


label ai_menu(beat_id, choice_path=""):
    $ _ai_d = aig.run(beat_id, choice_path)
    $ ai_say(_ai_d["lines"])
    $ ai_apply_flags(_ai_d["flags"], _ai_d["ctx"])
    $ _ai_items = [(c["text"], c["action_key"]) for c in _ai_d["choices"]] or [("（继续）", None)]
    $ _ai_pick = renpy.display_menu(_ai_items)
    return _ai_pick


label ai_prefetch(beat_id, choice_path=""):
    $ _ai_jid = aig.prefetch(beat_id, choice_path)
    return _ai_jid
