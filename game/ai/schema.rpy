################################################################################
## ai/schema.rpy — AI 输出的 Ren'Py 侧绑定
##
## 逻辑在 game/python-packages/aigal/schema_core.py（纯标准库，能离线跑测试）。
## 这里只放三件「必须知道 Ren'Py 状态」的事：
##   1. beat 表（beat_id → 回合号 / 本拍允许的 flag / 本拍该不该给选项）
##   2. beat.turn 断言（骨架搬回合时，这里立刻炸，而不是让剧情安静地串月）
##   3. speaker 是否真的 define 了（允许归允许，没 define 的行必须剔掉）
## 外加主角名替换 ai_render()，和给 director 用的 ai_say() / ai_apply_flags()。
##
## 本文件不新增任何 store 变量：schema 是无状态的，不参与 rollback、不进存档。
################################################################################

init -2 python:
    import aigal.schema_core as aischema
    ## 文本差异度量（二元组 Jaccard / 形状比对），给「每局不同」那套断言用。
    import aigal.textmetrics as aitext

    AI_SCHEMA_VER = aischema.SCHEMA_VER
    AI_PROMPT_VER = aischema.PROMPT_VER
    AI_NAME_TOKEN = aischema.NAME_TOKEN

    ## 对白分页阈值：对白框每行约 31 字、4 行封顶 ≈124 字，取 100 留余量。
    ## 结局正文允许写 200 字/条，靠 ai_say 分页落到框里，不靠压字数。
    SAY_PAGE_MAX = 100


init -1 python:

    ## 骨架里的拍。flags 是「本拍允许 AI 置位的 flag」，通常为空：
    ## 现在的 met_zhoumo / heard_piano / heard_call 都是脚本自己 set_flag 的，
    ## AI 不许再碰。等随机事件落地，把该事件真正该置的那一个 flag 加进来。
    ##
    ## TRUE_FLAGS / confession / piano_crisis 永远不许进这张表，init 1 那段有断言。
    AI_BEATS = {
        ## T1 九月：整段手写，0 次 AI 调用（创立者要求「开篇用原来的」），不登记拍。
        ## 自由段走模板池，t*_free 也不占登记表。

        ## T2 十月（合并后只剩主拍 + 楼梯间；考试不调 AI）
        "t2_piano":       dict(turn=2, flags=(), expect_choices=False),
        "t2_track":       dict(turn=2, flags=(), expect_choices=False),
        "t2_call":        dict(turn=2, flags=(), expect_choices=False),

        ## T3 十一月（旧琴房并进 T2 主拍；考试不调 AI）
        "t3_parent":      dict(turn=3, flags=(), expect_choices=False),

        ## T4 十二月（元旦回礼、寒假前父亲并进主拍；考试不调 AI）
        "t4_artfair":     dict(turn=4, flags=(), expect_choices=False),
        "t4_borrow":      dict(turn=4, flags=(), expect_choices=False),

        ## T5 三月（曾老师并进主拍）
        "t5_move":        dict(turn=5, flags=(), expect_choices=False),
        "t5_mother":      dict(turn=5, flags=(), expect_choices=False),

        ## T6 四月（开幕式、八百米并进主拍）
        "t6_club":        dict(turn=6, flags=(), expect_choices=False),

        ## T7 五月（夜谈并进主拍）
        "t7_hall":        dict(turn=7, flags=(), expect_choices=False),

        ## T8 六月（她的选科并进 t8_subject 主拍；考试不调 AI）
        "t8_subject":     dict(turn=8, flags=(), expect_choices=False),
        "t8_form":        dict(turn=8, flags=(), expect_choices=False),

        ## 结局拍放在 T36（分班名单之后），正文走 ENDING_* 那套上限。
        ## t8_end_a/b 留作「夏/温」两条 END 的载体，正文由文案按线重写；
        ## t8_end_c 是周墨线的 END（TRUE 之外）；none 用 t36_end_other。
        "t8_true":        dict(turn=36, flags=(), expect_choices=False, scope="ending"),
        "t8_end_a":       dict(turn=36, flags=(), expect_choices=False, scope="ending"),
        "t8_end_b":       dict(turn=36, flags=(), expect_choices=False, scope="ending"),
        "t8_end_c":       dict(turn=36, flags=(), expect_choices=False, scope="ending"),
        "t36_end_other":  dict(turn=36, flags=(), expect_choices=False, scope="ending"),

        ## ── T9–T35 主线拍（《剧情大纲_三年_v1.md》§1.2 登记表，21 个）──────
        ## 目前只有 id 与回合；台词/细节等 story 与 §2.7 跟上后再长。
        "t9_injury":      dict(turn=9,  flags=(), expect_choices=False),
        "t10_subject":    dict(turn=10, flags=(), expect_choices=False),
        "t13_artfair":    dict(turn=13, flags=(), expect_choices=False),
        "t14_coach":      dict(turn=14, flags=(), expect_choices=False),
        "t15_ask":        dict(turn=15, flags=(), expect_choices=False),
        "t16_mother":     dict(turn=16, flags=(), expect_choices=False),
        "t17_parent":     dict(turn=17, flags=(), expect_choices=False),
        "t18_half":       dict(turn=18, flags=(), expect_choices=False),
        "t19_club":       dict(turn=19, flags=(), expect_choices=False),
        "t20_quit":       dict(turn=20, flags=(), expect_choices=False),
        "t21_transfer":   dict(turn=21, flags=(), expect_choices=False),
        "t25_hall":       dict(turn=25, flags=(), expect_choices=False),
        "t26_entry":      dict(turn=26, flags=(), expect_choices=False),
        "t27_watch":      dict(turn=27, flags=(), expect_choices=False),
        "t28_form":       dict(turn=28, flags=(), expect_choices=False),
        "t29_exam":       dict(turn=29, flags=(), expect_choices=False),
        "t30_offer":      dict(turn=30, flags=(), expect_choices=False),
        "t32_choice":     dict(turn=32, flags=(), expect_choices=False),
        "t33_last":       dict(turn=33, flags=(), expect_choices=False),
        "t34_gaokao":     dict(turn=34, flags=(), expect_choices=False, scope="ending"),

        ## ── 随机事件拍（§3.2，20 个）──────────────────────────────────────
        ## turns 是允许出现的回合集合（事件有月窗口，不是单回合拍）。
        ## ai_beat_ok 先看 turns，没有再比 turn；prefetch_first 用 tN_ 前缀，不会误取 e_*。
        "e_welcome":      dict(turn=1,  turns=(1, 2),          flags=(), expect_choices=False),
        "e_sports_aut":   dict(turn=2,  turns=(2,),            flags=(), expect_choices=False),
        "e_open_day":     dict(turn=1,  turns=(1, 2, 3),       flags=(), expect_choices=False),
        "e_outing":       dict(turn=2,  turns=(2, 3),          flags=(), expect_choices=False),
        "e_parent1":      dict(turn=2,  turns=(2, 3),          flags=(), expect_choices=False),
        "e_newyear":      dict(turn=4,  turns=(4,),            flags=(), expect_choices=False),
        "e_spring_fest":  dict(turn=6,  turns=(6,),            flags=(), expect_choices=False),
        "e_placement":    dict(turn=1,  turns=(1, 2),          flags=(), expect_choices=False),
        "e_culture":      dict(turn=14, turns=(14, 15),        flags=(), expect_choices=False),
        "e_sports_spring": dict(turn=20, turns=(20,),          flags=(), expect_choices=False),
        "e_study_tour":   dict(turn=20, turns=(20, 21),        flags=(), expect_choices=False),
        "e_club_fair":    dict(turn=13, turns=(13, 14),        flags=(), expect_choices=False),
        "e_chorus":       dict(turn=20, turns=(20, 21),        flags=(), expect_choices=False),
        "e_transfer":     dict(turn=13, turns=tuple(range(13, 23)), flags=(), expect_choices=False),
        "e_pledge":       dict(turn=30, turns=(30, 31),        flags=(), expect_choices=False),
        "e_mock":         dict(turn=31, turns=(31, 32),        flags=(), expect_choices=False),
        "e_apply":        dict(turn=32, turns=(32, 33),        flags=(), expect_choices=False),
        "e_grad_photo":   dict(turn=32, turns=(32, 33, 34),    flags=(), expect_choices=False),
        "e_final_sprint": dict(turn=32, turns=(32, 33),        flags=(), expect_choices=False),
        "e_university":   dict(turn=26, turns=(26, 27),        flags=(), expect_choices=False),
    }

    ## 自由段不再走 beat：`free_scene()` 直接按 action_key 取模板变体池，
    ## 一整族 `t*_free` 没有任何调用点。合成逻辑已删（保留它就是留一族半死的拍）。
    def ai_beat(beat_id):
        """取 beat 定义。free 段不在这里，未登记一律返回 None。"""
        return AI_BEATS.get(beat_id)

    def ai_beat_ok(beat_id):
        """运行期用这个：返回 (bool, 说明)。对不上不该让玩家崩，走模板降级。"""
        b = ai_beat(beat_id)
        if b is None:
            return False, "beat 未登记：%s" % beat_id
        if "turns" in b:
            if store.turn not in b["turns"]:
                return False, ("beat 不在允许回合：%s 允许 %r，当前 T%s"
                               % (beat_id, b["turns"], store.turn))
            return True, ""
        if b["turn"] != store.turn:
            return False, "beat 回合对不上：%s 声明 T%s，当前 T%s" % (beat_id, b["turn"], store.turn)
        return True, ""

    def ai_require_beat(beat_id):
        """测试/开发期用这个：对不上直接抛，别让错误安静地过去。"""
        ok, why = ai_beat_ok(beat_id)
        if not ok:
            raise Exception("AI 契约：%s（beat 表在 game/ai/schema.rpy）" % why)
        return ai_beat(beat_id)

    def ai_player_name():
        """玩家填的主角名。还没做设置界面时回落到 mc 的定义名。"""
        for attr in ("player_name",):
            v = getattr(store, attr, None)
            if v:
                return str(v)
        ch = getattr(store, "mc", None)
        v = getattr(ch, "name", None) if ch is not None else None
        return str(v) if v else "XXX"

    def ai_default_actions():
        """本拍默认可给的 action_key。只有 ACTIONS 里有的才合法。"""
        return tuple(ACTIONS.keys())

    def ai_ctx(beat_id, actions=None, speakers=None, expect_choices=None):
        """给 schema 校验用的 ctx。断在这里比断在渲染时好。"""
        b = ai_require_beat(beat_id)
        return {
            "beat": beat_id,
            "turn": store.turn,
            "scope": b.get("scope", "scene"),   # scene 走 400 字，ending 走另一套
            "speakers": tuple(speakers if speakers is not None else aischema.ALL_SPEAKERS),
            "actions": tuple(actions if actions is not None else ai_default_actions()),
            "flags": tuple(b["flags"]),
            "expect_choices": b["expect_choices"] if expect_choices is None else expect_choices,
        }

    def ai_validate(raw, ctx):
        """校验 + 剔除未 define 的 speaker。返回值与 schema_core.validate 同构。"""
        v = aischema.validate(raw, ctx)

        keep = []
        for ln in v["lines"]:
            sid = ln["speaker"]
            if getattr(store, sid, None) is None:
                v["notes"].append("speaker_not_defined:%s" % sid)
                continue
            keep.append(ln)
        v["lines"] = keep

        ## 全被剔掉就等于没产出，得降级；否则导演层会以为拿到了正文。
        if v["ok"] and not v["lines"]:
            v["ok"] = False
            v["reason"] = "no_lines"

        if v["notes"]:
            ai_log("beat=%s ok=%s reason=%s notes=%s"
                   % (ctx.get("beat"), v["ok"], v["reason"], ",".join(v["notes"])))
        return v

    def ai_render(text):
        """把 {name} 换成玩家真名。名字本身也要洗——玩家可以把名字填成 {image=...}。"""
        safe_name = aischema.strip_markup(ai_player_name())
        return aischema.strip_markup(text.replace(AI_NAME_TOKEN, safe_name))

    def ai_say(lines):
        """按 speaker id 逐个说。渲染前再洗一次，AI 文本是外部输入。

        长台词分页走 ui_pages.rpy 的 page_text()：结局正文按 200 字/条写，
        对白框只放得下约 124 字，不分页就直接画出框外。那边有 page_* 三条用例，
        这里不再另写一份切分（重复实现等于两套真相）。
        """
        for ln in lines:
            ch = getattr(store, ln["speaker"], None)
            if ch is None:
                continue
            txt = ai_render(ln["text"])
            pieces = page_text(txt, SAY_PAGE_MAX) if len(txt) > SAY_PAGE_MAX else [txt]
            for piece in pieces:
                renpy.say(ch, piece)
        return True

    def ai_apply_flags(flags, ctx):
        """只置位、不撤销，且只认本拍白名单。set_flag 自己还会再查一次 FLAG_NAMES。"""
        allowed = set(ctx.get("flags") or ())
        applied = []
        for f in flags:
            if f not in allowed:
                continue
            set_flag(f)
            applied.append(f)
        return applied

    def ai_log(msg):
        """带前缀的日志，方便 grep；不含 key、不含提示词全文。"""
        try:
            renpy.log("[AIGAL] " + str(msg))
        except Exception:
            pass


## 跨文件断言放在 init 1：这时候 stats.rpy（init -1）的 FLAG_NAMES 已经就位。
## 这三条挂了说明有人往 beat 表里塞了不该由 AI 置位的 flag，必须当场炸。
init 1 python:

    _AI_SCRIPTED_ONLY = set(TRUE_FLAGS) | {"confession", "piano_crisis"}

    for _bid, _b in AI_BEATS.items():
        if not isinstance(_b["turn"], int) or not (1 <= _b["turn"] <= 36):
            raise Exception("AI beat %s 的 turn 不在 1..36：%r" % (_bid, _b["turn"]))
        for _t in _b.get("turns", ()):
            if not isinstance(_t, int) or not (1 <= _t <= 36):
                raise Exception("AI beat %s 的 turns 里有非法回合：%r" % (_bid, _t))
        _unknown = set(_b["flags"]) - set(FLAG_NAMES)
        if _unknown:
            raise Exception("AI beat %s 里出现未登记的 flag：%s" % (_bid, sorted(_unknown)))
        _bad = set(_b["flags"]) & _AI_SCRIPTED_ONLY
        if _bad:
            raise Exception(
                "AI beat %s 想置 %s —— 这些必须由脚本 set_flag，AI 不许碰（终结/告白是判定链）"
                % (_bid, sorted(_bad))
            )
