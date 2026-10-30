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
        "t1_ceremony":    ("mc", "zm", "inner"),
        "t1_military":    ("mc", "zzb", "inner"),
        "t1_committee":   ("mc", "zm", "inner"),
        "t1_night_piano": ("mc", "zm", "inner"),
        "t1_free":        ("mc", "zm"),

        "t2_welcome":     ("mc", "zm"),
        "t2_piano":       ("mc", "zm", "inner"),
        "t2_gala":        ("mc", "zm", "bro"),
        "t2_exam":        ("mc", "zeng", "inner"),
        "t2_call":        ("mc", "zm", "zm_dad"),
        "t2_free":        ("mc", "zm", "zzb"),

        "t3_exam":        ("mc", "zeng", "inner"),
        "t3_parent":      ("mc", "zm", "zm_dad", "inner"),
        "t3_piano":       ("mc", "zm", "inner"),

        "t4_artfair":     ("mc", "zm", "kong", "inner"),
        "t4_exam":        ("mc", "zeng", "inner"),
        "t4_newyear":     ("mc", "zm", "inner"),
        "t4_father":      ("mc", "zm", "zm_dad"),

        "t5_move":        ("mc", "zm", "inner"),
        "t5_office":      ("mc", "zm", "zeng"),
        "t5_mother":      ("mc", "zm", "zm_mom", "inner"),

        "t6_sports":      ("mc", "zm", "zzb", "inner"),
        "t6_run":         ("mc", "zm", "zzb", "inner"),
        "t6_club":        ("mc", "zm", "zeng", "zzb"),

        "t7_hall":        ("mc", "zm", "stu_a", "inner"),
        "t7_talk":        ("mc", "zm", "inner"),

        "t8_exam":        ("mc", "zeng", "inner"),
        "t8_choice_her":  ("mc", "zm", "zm_dad", "zm_mom"),
        "t8_subject":     ("mc", "zm", "inner"),
        "t8_form":        ("mc", "zm", "inner"),

        "t8_true":        ("mc", "zm", "nar"),
        "t8_end_a":       ("nar", "zm"),
        "t8_end_b":       ("nar", "zm"),
        "t8_end_c":       ("nar", "mc"),
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

        "t3_exam":        "期中考试，考场；周墨物理失手，发了卷子还坐在位上。",
        "t3_parent":      "家长会，教室走廊；周墨父亲到了，主角喊错了称呼。",
        "t3_piano":       "旧琴房，夜里；周墨坐在琴前，左手按着一个按不下去的键。",

        "t4_artfair":     "艺术节，礼堂；钢琴伴奏是周墨弹的，名字没有报。",
        "t4_exam":        "期末考试，考场。",
        "t4_newyear":     "元旦，教室里；周墨递来一张手抄谱，主角要回赠一样东西。",
        "t4_father":      "寒假前，校门口；周墨父亲提分科，要她学医。",

        "t5_move":        "艺术楼四楼，走廊；琴房要清空，她一个人在装箱，主角来帮忙。",
        "t5_office":      "曾老师办公室；社团申请与礼堂后台那台旧琴。",
        "t5_mother":      "楼梯间，夜里；周墨母亲打来电话，说再跟她父亲说说。",

        "t6_sports":      "春季运动会开幕式，礼堂后台那台琴推了出来；周墨的名字被报了上去。",
        "t6_run":         "操场，八百米终点；主角最后一个跑完，摔在终点线。",
        "t6_club":        "音乐教室；音乐社批下来了，周墨当社长，主角站在报名表前。",

        "t7_hall":        "城市音乐厅门口，研学；周墨站在节目单前看了很久。",
        "t7_talk":        "酒店走廊，夜里；周墨说她想学音乐，问她是不是很自私。",

        "t8_exam":        "学年期末，考场；这是最后一次考试。",
        "t8_choice_her":  "选科表发下来；周墨父亲在电话里要物化生，她第一次说自己想试一次。",
        "t8_subject":     "教室，选科表摊在桌上；周墨问主角，她是不是错了。",
        "t8_form":        "教室；主角自己的选科表还空着，笔尖在史地政和物化生之间。",

        "t8_true":        "结局·TRUE：分班名单贴出来，两个名字在同一栏；暑假第一天，他抱着修好的节拍器去学校。",
        "t8_end_a":       "结局·END A：家长签字页被改回物化生，琴被搬回仓库，走廊擦肩。",
        "t8_end_b":       "结局·END B：她在史地政那一栏，他在隔壁；开学后走廊里撞见一次。",
        "t8_end_c":       "结局·END C：同班了，音乐社撑到六月散了；暑假第一天他在校门口等到中午。",
    }

    ## 剧情拍自己的分支 id —— 不是 ACTIONS 里的行动。
    ## 选项「说破 / 装作没看见」这种不消耗 AP，所以不能塞进 ACTIONS，但同样要白名单：
    ## 只允许本拍声明过的几个，返回值交给剧本 if/else 分支。
    ## 没登记的拍默认给全部 ACTIONS（自由时段/与行动有关的拍）。
    BEAT_CHOICES = {
        ## T1 三拍：取值和 t1_september.rpy 里 t1_answer / t1_candy / t1_night 一致
        "t1_ceremony":    ("deny", "ask", "fumble"),
        "t1_military":    ("hand", "step", "via_zzb"),
        "t1_night_piano": ("look", "listen"),
        "t2_piano": ("reveal", "ignore"),
        "t2_call": ("stay", "leave", "water_only"),
        "t3_piano": ("talk", "silent", "press_key"),
        "t4_artfair": ("speak", "quiet"),
        "t4_newyear": ("metronome", "strings"),
        "t5_move": ("move", "teacher", "stop"),
        "t6_club": ("join", "help", "no"),
        "t7_talk": ("support", "persuade", "silent"),
        "t8_subject": ("support", "against", "silent"),
        "t8_form": ("same", "different"),
    }

    def choices_for(beat_id):
        """本拍允许的 choice id。None = 用 ACTIONS 全集。"""
        return BEAT_CHOICES.get(beat_id)

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

    def build_messages(beat_id, turn, state, ending=False, extra=""):
        """按 §0 的顺序拼出 chat 消息。"""
        system = "\n\n".join(
            PARAS.get(k, "") for k in ("P_A", "P_B", "P_C") if PARAS.get(k)
        )
        spk = speakers_for(beat_id, turn)
        roles = [para_for(s, turn) for s in spk]

        usr = []
        usr.append("【本拍场景】%s" % scene_for(beat_id, turn))
        usr.append("【本拍数值摘要】%s" % state_line(state))
        if extra:
            ## 本拍的既定事实：月考过没过、玩家上一拍选了什么。这是叙述前提，不是可选项。
            usr.append("【本拍补充】%s" % extra)
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
