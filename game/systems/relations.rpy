################################################################################
## systems/relations.rpy —— 三条线的好感 / 里程碑 / 路线锁定
##
## 口径：《剧情大纲_三年_v1.md》§2 里程碑表、§5 变量表。
##   好感   rel_zm / rel_xia / rel_x    0–100，只加不减，只经 add_rel() 改
##   阶段   stage                     不单独存，由该线已达成的里程碑数算（0–4）
##   路线   route                     只在 T22 锁一次，平局 周墨 > 夏幸悠 > 温以宁
##
## 剧本只调 add_rel() / mark_milestone() / lock_route()；
## 提示词只读 rel_hint()（行为短语，不含数字）。
## 这里是「每个角色一组变量」的唯一入口，别在剧情里直接改 rel_*。
################################################################################

init -1 python:

    REL_NAMES = ("zm", "xia", "x")
    REL_LABEL = {"zm": "周墨", "xia": "夏幸悠", "x": "温以宁"}

    ## 每线里程碑，按编号顺序；与 §2 的表一一对应，None = 该拍没有 Flag（只记进度）。
    MILESTONE_FLAGS = {
        "zm": (
            "met_zhoumo", "heard_piano", "zm_father", "piano_crisis", "zm_choice",
            "art_fair", "zm_mother", "club", "music_hall", "subject_support",
        ),
        "xia": (
            "xia_met", None, "xia_injury", None, "xia_parent",
            "xia_stay", "xia_entry", "xia_exam", "xia_choice",
        ),
        "x": (
            "x_met", None, None, None, "x_family",
            None, "x_offer", "x_choice",
        ),
    }

    ## 里程碑数 → stage：0–2 个=0，3–4=1，5–6=2，7–8=3，9+=4
    STAGE_CUTS = (2, 4, 6, 8)

    ## 好感档位。给提示词的是行为短语，不是数字。
    REL_TIERS = ("还不熟", "说得上话", "会主动找你", "很信你", "只肯跟你说")

    ROUTE_MIN = 60        # 三人 rel 都低于这个值 → route = none


    def add_rel(sid, amount):
        """唯一改好感的口子。只加不减；传负数直接抛，别让回滚吃掉好感。"""
        if sid not in REL_NAMES:
            raise Exception("未知角色线：%r" % (sid,))
        if amount < 0:
            raise Exception("好感只加不减：add_rel(%r, %r)" % (sid, amount))
        key = "rel_" + sid
        setattr(store, key, clamp(getattr(store, key) + amount))
        return getattr(store, key)


    def mark_milestone(sid, idx):
        """记一条主线里程碑（idx 从 1 开始）；该拍有 Flag 的同时置位。返回已达成数。"""
        flags = MILESTONE_FLAGS.get(sid)
        if flags is None:
            raise Exception("未知角色线：%r" % (sid,))
        if not (1 <= idx <= len(flags)):
            raise Exception("%s 没有第 %r 个里程碑" % (sid, idx))
        store.ms_done.setdefault(sid, {})[idx] = True
        flag = flags[idx - 1]
        if flag:
            set_flag(flag)
        return ms_count(sid)


    def ms_count(sid):
        return len(store.ms_done.get(sid) or {})


    def stage_of(sid):
        """0–4 档，由里程碑数算；不存 stage_* 变量。"""
        n = ms_count(sid)
        stage = 0
        for cut in STAGE_CUTS:
            if n > cut:
                stage += 1
        return stage


    def rel_tier(sid):
        v = getattr(store, "rel_" + sid)
        if v >= 80:
            return 4
        if v >= 60:
            return 3
        if v >= 40:
            return 2
        if v >= 20:
            return 1
        return 0


    def rel_hint(sid):
        """给提示词的一句话（不含数字），每拍只注入在场的那 1–2 人。"""
        return "%s：%s。" % (REL_LABEL[sid], REL_TIERS[rel_tier(sid)])


    ## ── 好感只由玩家行为给（《剧情大纲_三年_v1.md》§5.1、§5.3）──────────────
    ## 里程碑只置 Flag、不加 rel；rel 表示「你在谁身上花了时间」。
    ## 来源只有两个：下面这张行动表（每月每线一次）+ 事件选择点（events.rpy）。
    ## 列表照 §5.3 第二节抄：周墨 5 个、夏幸悠 1 个、温以宁 1 个；其余一律中立。
    REL_PER_ACTION = 5

    REL_ACTIONS = {
        "zm": ("ask_zhoumo", "study_with", "listen_piano", "visit_auditorium", "visit_club"),
        "xia": ("do_sport",),
        "x": ("study",),
    }


    def add_rel_from_action(action_key):
        """一次自由行动给对应线 +REL_PER_ACTION；同月同线只计一次。返回实际增量。"""
        sid = None
        for line, keys in REL_ACTIONS.items():
            if action_key in keys:
                sid = line
                break
        if not sid:
            return 0
        if store.rel_month.get(sid) == store.turn:
            return 0
        store.rel_month = dict(store.rel_month, **{sid: store.turn})
        add_rel(sid, REL_PER_ACTION)
        return REL_PER_ACTION


    ## ── 里程碑拍 → (sid, idx)（《剧情大纲_三年_v1.md》§5.2 第六节）──────────
    ## 按「这一拍的内容」对，不按回合号对：旧 T1–T8 的月份顺序和 36 格不同。
    ## 周墨线 10 条是现在就能接的上限；夏 9 / 温 8 等 T9+ 的 label 铺完再用下面预登记的行。
    MILESTONE_BEATS = {
        "t2_piano":      ("zm", 2),   # 旧琴房撞见她弹
        "t2_track":      ("xia", 1),  # 夏线第一次出场：运动会报名
        "t4_borrow":     ("x", 1),    # 温线第一次出场：图书馆同够一本书
        "t3_parent":     ("zm", 3),   # 家长会 / 她父亲的冷淡
        "t5_move":       ("zm", 4),   # 琴房清空通知
        "t8_subject":    ("zm", 5),   # 选科表：她想学音乐被否
        "t4_artfair":    ("zm", 6),   # 艺术节伴奏被听见
        "t5_mother":     ("zm", 7),   # 母亲第一次替她说话
        "t6_club":       ("zm", 8),   # 音乐社 / 她当社长
        "t7_hall":       ("zm", 9),   # 研学·音乐厅
        "t8_form":       ("zm", 10),  # 志愿表：他替她说话

        ## T9+ 的拍（§1.2）：label 铺到那一格时，同一行调用即可生效
        "t9_injury":     ("xia", 3),
        "t10_subject":   ("zm", 5),
        "t13_artfair":   ("zm", 6),
        "t14_coach":     ("xia", 4),
        "t15_ask":       ("x", 3),
        "t16_mother":    ("zm", 7),
        "t17_parent":    ("xia", 5),
        "t18_half":      ("x", 4),
        "t19_club":      ("zm", 8),
        "t20_quit":      ("xia", 6),
        "t21_transfer":  ("x", 5),
        "t25_hall":      ("zm", 9),
        "t26_entry":     ("xia", 7),
        "t27_watch":     ("x", 6),
        "t28_form":      ("zm", 10),
        "t29_exam":      ("xia", 8),
        "t30_offer":     ("x", 7),
        "t32_choice":    ("xia", 9),
        "t33_last":      ("x", 8),
    }


    def mark_milestone_for_beat(beat_id):
        """剧本在播完这一拍后调；没有映射的拍返回 0。"""
        m = MILESTONE_BEATS.get(beat_id)
        if not m:
            return 0
        return mark_milestone(m[0], m[1])


    def lock_route():
        """T22 锁一次路线；已锁过直接返回，读档/回滚可复现。

        平局按 周墨 > 夏幸悠 > 温以宁；三人 rel 都 < ROUTE_MIN → none。
        """
        if store.route_done:
            return store.route
        order = (("zm", store.rel_zm), ("xia", store.rel_xia), ("x", store.rel_x))
        best = max(v for _, v in order)
        store.route = "none" if best < ROUTE_MIN else next(s for s, v in order if v == best)
        store.route_done = True
        return store.route


## 存档状态 ####################################################################

default rel_zm = 0
default rel_xia = 0
default rel_x = 0
default route = "none"
default route_done = False
default ms_done = {"zm": {}, "xia": {}, "x": {}}
default event_seen = {}        # 随机事件 id → 次数，同局权重衰减用
default rel_month = {}         # sid → 最后一次靠行动加 rel 的回合号（每月每线一次）
