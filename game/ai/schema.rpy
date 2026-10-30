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

    AI_SCHEMA_VER = aischema.SCHEMA_VER
    AI_PROMPT_VER = aischema.PROMPT_VER
    AI_NAME_TOKEN = aischema.NAME_TOKEN


init -1 python:

    ## 骨架里的拍。flags 是「本拍允许 AI 置位的 flag」，通常为空：
    ## 现在的 met_zhoumo / heard_piano / heard_call 都是脚本自己 set_flag 的，
    ## AI 不许再碰。等随机事件落地，把该事件真正该置的那一个 flag 加进来。
    ##
    ## TRUE_FLAGS / confession / piano_crisis 永远不许进这张表，init 1 那段有断言。
    AI_BEATS = {
        ## T1 九月
        "t1_report":      dict(turn=1, flags=(), expect_choices=False),
        "t1_ceremony":    dict(turn=1, flags=(), expect_choices=True),
        "t1_military":    dict(turn=1, flags=(), expect_choices=True),
        "t1_committee":   dict(turn=1, flags=(), expect_choices=False),
        "t1_night_piano": dict(turn=1, flags=(), expect_choices=True),
        "t1_free":        dict(turn=1, flags=(), expect_choices=True),

        ## T2 十月
        "t2_welcome":     dict(turn=2, flags=(), expect_choices=False),
        "t2_piano":       dict(turn=2, flags=(), expect_choices=True),
        "t2_gala":        dict(turn=2, flags=(), expect_choices=False),
        "t2_exam":        dict(turn=2, flags=(), expect_choices=False),
        "t2_call":        dict(turn=2, flags=(), expect_choices=True),
        "t2_free":        dict(turn=2, flags=(), expect_choices=True),

        ## T8 结局。正文比拍内长，走 ENDING_* 那套上限（160 字/行、600 字合计），
        ## 别让它跟拍内那套 250 字共用——截到 250 就是整局最后一段正文没了。
        "t8_true":        dict(turn=8, flags=(), expect_choices=False, scope="ending"),
        "t8_end_a":       dict(turn=8, flags=(), expect_choices=False, scope="ending"),
        "t8_end_b":       dict(turn=8, flags=(), expect_choices=False, scope="ending"),
        "t8_end_c":       dict(turn=8, flags=(), expect_choices=False, scope="ending"),
    }

    ## 自由行动段每个月都有，不用一个月往表里抄一行。
    ## 用 tuple 不用生成器：生成器被 `in` 判定消费一次就空了，第二次起永远命不中。
    AI_FREE_BEATS = tuple("t%d_free" % n for n in range(1, 9))

    def ai_beat(beat_id):
        """取 beat 定义。t3_free…t8_free 按需合成，其余必须已登记。"""
        b = AI_BEATS.get(beat_id)
        if b is not None:
            return b
        if beat_id in AI_FREE_BEATS:
            return dict(turn=int(beat_id[1]), flags=(), expect_choices=True)
        return None

    def ai_beat_ok(beat_id):
        """运行期用这个：返回 (bool, 说明)。对不上不该让玩家崩，走模板降级。"""
        b = ai_beat(beat_id)
        if b is None:
            return False, "beat 未登记：%s" % beat_id
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
            "turn": b["turn"],
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
        """按 speaker id 逐个说。渲染前再洗一次，AI 文本是外部输入。"""
        for ln in lines:
            ch = getattr(store, ln["speaker"], None)
            if ch is None:
                continue
            renpy.say(ch, ai_render(ln["text"]))
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
        if not isinstance(_b["turn"], int) or not (1 <= _b["turn"] <= 8):
            raise Exception("AI beat %s 的 turn 不在 1..8：%r" % (_bid, _b["turn"]))
        _unknown = set(_b["flags"]) - set(FLAG_NAMES)
        if _unknown:
            raise Exception("AI beat %s 里出现未登记的 flag：%s" % (_bid, sorted(_unknown)))
        _bad = set(_b["flags"]) & _AI_SCRIPTED_ONLY
        if _bad:
            raise Exception(
                "AI beat %s 想置 %s —— 这些必须由脚本 set_flag，AI 不许碰（终结/告白是判定链）"
                % (_bid, sorted(_bad))
            )
