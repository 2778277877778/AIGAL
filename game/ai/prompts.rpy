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

        "t2_piano":       ("mc", "zm", "inner"),
        "t2_call":        ("mc", "zm", "zm_dad"),

        "t3_parent":      ("mc", "zm", "zm_dad", "inner"),

        "t4_artfair":     ("mc", "zm", "kong", "inner"),

        "t5_move":        ("mc", "zm", "inner"),
        "t5_mother":      ("mc", "zm", "zm_mom", "inner"),

        "t6_club":        ("mc", "zm", "zeng", "zzb"),

        "t7_hall":        ("mc", "zm", "stu_a", "inner"),

        "t8_subject":     ("mc", "zm", "inner"),
        "t8_form":        ("mc", "zm", "inner"),

        "t8_true":        ("mc", "zm", "nar"),
        "t8_end_a":       ("nar", "zm"),
        "t8_end_b":       ("nar", "zm"),
        "t8_end_c":       ("nar", "mc"),

        ## T9–T35 主线拍（《剧情大纲_三年_v1.md》§1.2）
        "t9_injury":      ("mc", "xia", "nar"),
        "t10_subject":    ("mc", "zm", "zm_dad", "nar"),
        "t13_artfair":    ("mc", "zm", "kong", "nar"),
        "t14_coach":      ("mc", "xia", "nar"),
        "t15_ask":        ("mc", "x", "nar"),
        "t16_mother":     ("mc", "zm", "zm_mom", "nar"),
        "t17_parent":     ("mc", "xia", "nar"),
        "t18_half":       ("mc", "x", "nar"),
        "t19_club":       ("mc", "zm", "zeng", "zzb"),
        "t20_quit":       ("mc", "xia", "nar"),
        "t21_transfer":   ("mc", "x", "nar"),
        "t25_hall":       ("mc", "zm", "nar"),
        "t26_entry":      ("mc", "xia", "nar"),
        "t27_watch":      ("mc", "x", "nar"),
        "t28_form":       ("mc", "zm", "zm_dad", "nar"),
        "t29_exam":       ("mc", "xia", "nar"),
        "t30_offer":      ("mc", "x", "nar"),
        "t32_choice":     ("mc", "xia", "nar"),
        "t33_last":       ("mc", "x", "nar"),
        "t34_gaokao":     ("mc", "zeng", "nar"),
        "t35_score":      ("mc", "nar"),

        ## 随机事件拍（§3.2）
        "e_welcome":      ("mc", "zm", "bro", "nar"),
        "e_sports_aut":   ("mc", "xia", "zzb", "nar"),
        "e_open_day":     ("mc", "x", "nar"),
        "e_outing":       ("mc", "zzb", "nar"),
        "e_parent1":      ("mc", "zeng", "nar"),
        "e_newyear":      ("mc", "kong", "nar"),
        "e_spring_fest":  ("mc", "zzb", "nar"),
        "e_placement":    ("mc", "zeng", "nar"),
        "e_culture":      ("mc", "x", "nar"),
        "e_sports_spring": ("mc", "xia", "nar"),
        "e_study_tour":   ("mc", "zm", "nar"),
        "e_club_fair":    ("mc", "kong", "nar"),
        "e_chorus":       ("mc", "zm", "nar"),
        "e_transfer":     ("mc", "x", "nar"),
        "e_pledge":       ("mc", "zeng", "nar"),
        "e_mock":         ("mc", "zeng", "nar"),
        "e_apply":        ("mc", "zm", "zm_dad"),
        "e_grad_photo":   ("mc", "zzb", "nar"),
        "e_final_sprint": ("mc", "zeng", "nar"),
        "e_university":   ("mc", "x", "nar"),
    }

    ## 本拍场景的一句话提示。同样按实际剧本补。
    BEAT_SCENE = {
        "t2_piano":       "主角推门撞见周墨在旧琴房弹琴。",
        "t2_call":        "月考后，楼梯间，周墨在接家里的电话。",

        "t3_parent":      "家长会，教室走廊；周墨父亲到了，主角喊错了称呼。",

        "t4_artfair":     "艺术节，礼堂；钢琴伴奏是周墨弹的，名字没有报。",

        "t5_move":        "艺术楼四楼，走廊；琴房要清空，她一个人在装箱，主角来帮忙。",
        "t5_mother":      "楼梯间，夜里；周墨母亲打来电话，说再跟她父亲说说。",

        "t6_club":        "音乐教室；音乐社批下来了，周墨当社长，主角站在报名表前。",

        "t7_hall":        "城市音乐厅门口，研学；周墨站在节目单前看了很久。",

        "t8_subject":     "教室，选科表摊在桌上；周墨问主角，她是不是错了。",
        "t8_form":        "教室；主角自己的选科表还空着，笔尖在史地政和物化生之间。",

        "t8_true":        "结局·TRUE：分班名单贴出来，两个名字在同一栏；暑假第一天，他抱着修好的节拍器去学校。",
        "t8_end_a":       "结局·END A：家长签字页被改回物化生，琴被搬回仓库，走廊擦肩。",
        "t8_end_b":       "结局·END B：她在史地政那一栏，他在隔壁；开学后走廊里撞见一次。",
        "t8_end_c":       "结局·END C：同班了，音乐社撑到六月散了；暑假第一天他在校门口等到中午。",

        ## T9–T35 主线拍（§1.2 的内容列）
        "t9_injury":      "操场，训练后；夏幸悠坐在跑道边按着脚踝，不肯说伤得怎么样。",
        "t10_subject":    "教室，选科表发下来；周墨想学音乐，被父亲否掉。",
        "t13_artfair":    "艺术节，礼堂；伴奏是周墨弹的，名字没有报。",
        "t14_coach":      "看台下面；教练找夏幸悠谈体育班的事。",
        "t15_ask":        "教室；温以宁第一次主动来找他问题。",
        "t16_mother":     "周墨母亲第一次替她说话。",
        "t17_parent":     "家长会；夏幸悠家里要她走文化课。",
        "t18_half":       "放学路上；温以宁讲家里的事，只说了一半。",
        "t19_club":       "音乐教室；音乐社成立，周墨当社长。",
        "t20_quit":       "队里要夏幸悠退队，主角替她争。",
        "t21_transfer":   "温以宁说，她可能随时要转走。",
        "t25_hall":       "城市音乐厅，研学；周墨说她想学音乐。",
        "t26_entry":      "体育单招报名表放在夏幸悠桌上。",
        "t27_watch":      "温以宁看着另外两条线，不评价。",
        "t28_form":       "志愿表；主角替周墨说话。",
        "t29_exam":       "单招考试那天，夏幸悠没有告诉他。",
        "t30_offer":      "主角桌上多了一个没有署名的小东西。",
        "t32_choice":     "夏幸悠做完决定，不等他回答。",
        "t33_last":       "温以宁对他说最后一句。",
        "t34_gaokao":     "高考，考场；这一回只掷一次。",
        "t35_score":      "查分夜，家里很安静。",

        ## 随机事件拍（§3.2 的事件列）
        "e_welcome":      "迎新晚会，礼堂；台下跟着合唱。",
        "e_sports_aut":   "秋季运动会，操场；八百米报名。",
        "e_open_day":     "校园开放日，走廊里全是家长。",
        "e_outing":       "班级秋游，山脚下的大巴。",
        "e_parent1":      "期中家长会，教室走廊。",
        "e_newyear":      "元旦晚会，礼堂；钢琴独奏。",
        "e_spring_fest":  "春节，宿舍楼没剩几个人。",
        "e_placement":    "开学摸底考，教室。",
        "e_culture":      "校园文化节，操场上的摊子。",
        "e_sports_spring": "春季运动会，操场。",
        "e_study_tour":   "研学，大巴上；她靠着窗睡了一路。",
        "e_club_fair":    "社团招新，艺术楼门口。",
        "e_chorus":       "合唱比赛，后台的钢琴。",
        "e_transfer":     "有同学转学，教室空了一张桌子。",
        "e_pledge":       "百日誓师，操场。",
        "e_mock":         "模拟考周，考场按高考时间来。",
        "e_apply":        "志愿填报咨询，办公室。",
        "e_grad_photo":   "毕业照，教学楼前。",
        "e_final_sprint": "考前冲刺，晚自习的教室。",
        "e_university":   "大学开放日，校门口的队伍。",
    }

    ## 剧情拍自己的分支 id —— 不是 ACTIONS 里的行动。
    ## 选项「说破 / 装作没看见」这种不消耗 AP，所以不能塞进 ACTIONS，但同样要白名单：
    ## 只允许本拍声明过的几个，返回值交给剧本 if/else 分支。
    ## 没登记的拍默认给全部 ACTIONS（自由时段/与行动有关的拍）。
    BEAT_CHOICES = {
        ## T1 三拍：取值和 t1_september.rpy 里 t1_answer / t1_candy / t1_night 一致
        "t2_piano": ("reveal", "ignore"),
        "t2_call": ("stay", "leave", "water_only"),
        "t4_artfair": ("speak", "quiet"),
        "t5_move": ("move", "teacher", "stop"),
        "t6_club": ("join", "help", "no"),
        "t8_subject": ("support", "against", "silent"),
        "t8_form": ("same", "different"),
        ## 事件选择点（§3.3）：只给脚本用，模型 expect_choices=False 不变
        "e_outing": ("with_zm", "with_xia", "with_x"),
        "e_parent1": ("greet", "cover", "avoid"),
        "e_chorus": ("join", "help", "skip"),
        "e_grad_photo": ("with_zm", "with_xia", "with_x"),
    }

    def choices_for(beat_id):
        """本拍允许的 choice id。None = 用 ACTIONS 全集。"""
        return BEAT_CHOICES.get(beat_id)

    ## 每拍的「种子化环境细节」：同一拍按本局 seed 挑一条塞给模型。
    ## 两个新开局会拿到不同的一条（细节只影响「看见什么」，不新增情节），
    ## 同一存档读档/回滚还是那一条。文案策划 按 BEAT_DETAILS 的键往里填。
    ## 内容从 剧情大纲_三年_v1.md 的细节段生成（tests/build_prompts.py），生成物在 prompts_data.rpy。
    if "BEAT_DETAILS" not in globals():
        BEAT_DETAILS = {}

    def detail_for(beat_id, seed, table=None):
        d = (table if table is not None else BEAT_DETAILS).get(beat_id)
        if not d:
            return ""
        return d[int(seed) % len(d)]

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

    def build_messages(beat_id, turn, state, ending=False, extra="", seed=0):
        """按 §0 的顺序拼出 chat 消息。"""
        system = "\n\n".join(
            PARAS.get(k, "") for k in ("P_A", "P_B", "P_C") if PARAS.get(k)
        )
        spk = speakers_for(beat_id, turn)
        roles = [para_for(s, turn) for s in spk]

        usr = []
        usr.append("【本拍场景】%s" % scene_for(beat_id, turn))
        usr.append("【本拍数值摘要】%s" % state_line(state))
        _detail = detail_for(beat_id, seed)
        if _detail:
            usr.append("【本拍的随机细节】%s" % _detail)
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
