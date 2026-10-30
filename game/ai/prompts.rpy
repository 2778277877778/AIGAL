################################################################################
## ai/prompts.rpy —— 拼提示词。
##
## 段落正文在 prompts_data.rpy（自动生成，源文件是 高中校园物语/提示词_角色_v1.md）。
## 本文件只负责「按 §0 的顺序拼」和「本拍该带哪几个角色段」。
##
## 拼装顺序（见文件里 §0，角色段靠后、D 最后）：
##   system: P_A 世界 + P_B 写法 + P_C 去 AI 味
##   user  : 本拍场景 + 数值摘要 + 可用 speaker / action_key + 出场角色段 + P_D 输出契约
##   结局拍的拍用 P_D_ending 换掉 P_D，别的段不动。
################################################################################

init -3 python in aig:

    if "PARAS" not in globals():
        PARAS = {}          # prompts_data.rpy 没生成时也不至于崩

    ## 每拍在场的角色段。只带 1–3 个（全带会串味）。
    ## 这张表是骨架，剧本定稿后按实际出场改；没登记的拍默认 mc + zm。
    BEAT_SPEAKERS = {
        "t1_report":      ("mc", "zeng"),
        "t1_ceremony":    ("mc", "zm"),
        "t1_military":    ("mc", "zzb"),
        "t1_committee":   ("mc", "zm"),
        "t1_night_piano": ("mc", "zm", "inner"),
        "t1_free":        ("mc", "zm"),

        "t2_welcome":     ("mc", "zm"),
        "t2_piano":       ("mc", "zm", "inner"),
        "t2_gala":        ("mc", "zm", "bro"),
        "t2_exam":        ("mc", "zeng"),
        "t2_call":        ("mc", "zm", "zm_dad"),
        "t2_free":        ("mc", "zm", "zzb"),
    }

    ## 本拍场景的一句话提示。同样按实际剧本补。
    BEAT_SCENE = {
        "t1_report":      "开学报到，宿舍楼报到点，主角第一次离家住校。",
        "t1_ceremony":    "开学典礼，礼堂后排，周墨坐在旁边但没有说话。",
        "t1_military":    "军训，操场，周子博在队伍里带节奏。",
        "t1_committee":   "班委选举，教室，周墨不想上台。",
        "t1_night_piano": "夜里，旧琴房外，有人在里面弹琴。",
        "t1_free":        "九月剩下的自由时间。",
        "t2_welcome":     "迎新晚会筹备，合唱队缺伴奏。",
        "t2_piano":       "主角推门撞见周墨在旧琴房弹琴。",
        "t2_gala":        "迎新晚会当晚，礼堂，放的是录音伴奏。",
        "t2_exam":        "第一次月考，考场。",
        "t2_call":        "月考后，楼梯间，周墨在接家里的电话。",
        "t2_free":        "十月剩下的自由时间。",
    }

    def speakers_for(beat_id, turn=None):
        if beat_id in BEAT_SPEAKERS:
            return BEAT_SPEAKERS[beat_id]
        if beat_id.endswith("_free"):
            return ("mc", "zm")
        return ("mc", "zm")

    def para_for(sid, turn=None):
        """取一个角色的段落。周墨按 turn 取八拍变体，没有就退回通用段。"""
        if sid == "zm" and turn:
            p = PARAS.get("P_zm_%d" % int(turn))
            if p:
                return p
        return PARAS.get("P_" + sid, "")

    def scene_for(beat_id, turn):
        return BEAT_SCENE.get(beat_id, "第 %s 回合的固定拍 %s。" % (turn, beat_id))

    def state_line(state):
        """本拍数值摘要。给 AI 看，不让它算——P_D 里写死了不许返回数值。"""
        parts = []
        if state.get("name"):
            parts.append("主角名：%s" % state["name"])
        parts.append("学习 %s / 压力 %s / 体力 %s / 钱 %s / 本回合剩余 AP %s"
                     % (state.get("study"), state.get("stress"),
                        state.get("stamina"), state.get("money"), state.get("ap")))
        flags = state.get("flags") or ()
        parts.append("已发生的事标：%s" % ("、".join(flags) if flags else "（无）"))
        return "；".join(parts)

    def build_messages(beat_id, turn, state, ending=False):
        """按 §0 的顺序拼出 chat 消息。"""
        system = "\n\n".join(
            PARAS.get(k, "") for k in ("P_A", "P_B", "P_C") if PARAS.get(k)
        )
        spk = speakers_for(beat_id, turn)
        roles = [para_for(s, turn) for s in spk]

        usr = []
        usr.append("【本拍场景】%s" % scene_for(beat_id, turn))
        usr.append("【本拍数值摘要】%s" % state_line(state))
        usr.append("【本拍可用 speaker】%s" % "、".join(spk))
        actions = state.get("actions") or ()
        usr.append("【本拍可用 action_key】%s"
                   % ("、".join(actions) if actions else "（本拍不给选项）"))
        roles = [r for r in roles if r]
        if roles:
            usr.append("【出场角色段（只写这几位）】\n\n" + "\n\n".join(roles))
        tail = PARAS.get("P_D_ending" if ending else "P_D", "")
        if tail:
            usr.append(tail)

        return [
            {"role": "system", "content": system},
            {"role": "user", "content": "\n\n".join(usr)},
        ]
