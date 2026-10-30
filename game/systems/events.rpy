################################################################################
## systems/events.rpy —— 随机事件池（《剧情大纲_三年_v1.md》§3）
##
## 一个完整回合的固定段是：主线拍（若有）→ 事件槽（掷中才有）→ 自由行动。
## 这里只管「掷不掷中、抽到谁」；数值与 Flag 由剧本和 relations 层写，AI 只出台词。
##
## 抽取规则（§3.1）：先掷 60% → grade → months → requires → exclude → 加权随机；
## 同局已出过的事件权重 ×0.3；与当月主线同 tag 的事件不出（避免一个月两场同类戏）。
##
## 纯函数 event_draw() 可传 rng，测试用 random.Random(seed) 固定结果；剧本不传，用 renpy.random。
################################################################################

init -1 python:

    EVENT_HIT = 0.6            # 每槽先掷「出不出」
    EVENT_SEEN_RATE = 0.3       # 同局已出过的权重衰减

    ## 有事件槽的回合（§1 总表的「槽」列，14 个；全落在偶数月）
    SLOT_TURNS = (2, 4, 6, 8, 10, 14, 16, 18, 20, 22, 26, 28, 30, 32)

    ## 20 个候选（§3.2 + 末尾补的两条）。
    ## months 是自然月窗口；grade 1/2/3；exclude 是互斥事件 id；requires 是必须已置位的 Flag。
    EVENT_POOL = {
        "e_welcome":       dict(grade=1, months=(9, 10),        weight=3, tags=("stage", "festival"), exclude=("e_newyear",),     requires=()),
        "e_sports_aut":    dict(grade=1, months=(10,),          weight=3, tags=("sports",),           exclude=("e_sports_spring",), requires=()),
        "e_open_day":      dict(grade=1, months=(9, 10, 11),    weight=2, tags=("open",),             exclude=(),                 requires=()),
        "e_outing":        dict(grade=1, months=(10, 11),       weight=2, tags=("trip",),             exclude=("e_study_tour",),  requires=()),
        "e_parent1":       dict(grade=1, months=(10, 11),       weight=2, tags=("parent",),           exclude=("e_culture",),     requires=()),
        "e_newyear":       dict(grade=1, months=(12,),          weight=2, tags=("stage", "festival"), exclude=("e_welcome",),     requires=()),
        "e_spring_fest":   dict(grade=1, months=(2,),           weight=2, tags=("festival",),         exclude=(),                 requires=()),
        "e_placement":     dict(grade=1, months=(9, 10),        weight=1, tags=("exam",),             exclude=(),                 requires=()),
        "e_culture":       dict(grade=2, months=(10, 11),       weight=3, tags=("stage", "festival"), exclude=("e_parent1",),     requires=()),
        "e_sports_spring": dict(grade=2, months=(4,),           weight=3, tags=("sports",),           exclude=("e_sports_aut",),  requires=()),
        "e_study_tour":    dict(grade=2, months=(4, 5),         weight=3, tags=("trip",),             exclude=("e_outing",),      requires=()),
        "e_club_fair":     dict(grade=2, months=(9, 10),        weight=2, tags=("club",),             exclude=(),                 requires=()),
        "e_chorus":        dict(grade=2, months=(4, 5),         weight=2, tags=("stage",),            exclude=(),                 requires=()),
        "e_transfer":      dict(grade=2, months=None,           weight=1, tags=("misc",),             exclude=(),                 requires=()),
        "e_pledge":        dict(grade=3, months=(2, 3),         weight=3, tags=("assembly",),         exclude=(),                 requires=()),
        "e_mock":          dict(grade=3, months=(3, 4),         weight=2, tags=("exam",),             exclude=("e_final_sprint",), requires=()),
        "e_apply":         dict(grade=3, months=(4, 5),         weight=2, tags=("form",),             exclude=(),                 requires=()),
        "e_grad_photo":    dict(grade=3, months=(4, 5, 6),      weight=2, tags=("assembly",),         exclude=(),                 requires=()),
        "e_final_sprint":  dict(grade=3, months=(4, 5),         weight=2, tags=("exam",),             exclude=("e_mock",),        requires=()),
        "e_university":    dict(grade=3, months=(10, 11),       weight=1, tags=("open",),             exclude=(),                 requires=()),
    }

    ## 主线拍的内容分类：和事件同 tag 就不出这个事件（§3.1「与当月主线互斥」）。
    MAINLINE_TAGS = {
        "t2_piano": ("stage",), "t2_welcome": ("stage",), "t2_gala": ("stage",),
        "t3_piano": ("stage",),
        "t4_artfair": ("stage",), "t4_newyear": ("stage", "festival"),
        "t6_sports": ("sports",), "t6_run": ("sports",),
        "t7_hall": ("stage", "trip"),
        "t8_subject": ("form",), "t8_form": ("form",),
        "t9_injury": ("sports",),
        "t10_subject": ("form",),
        "t13_artfair": ("stage",),
        "t14_coach": ("sports",),
        "t17_parent": ("parent",),
        "t19_club": ("club",),
        "t20_quit": ("sports",),
        "t21_transfer": ("misc",),
        "t25_hall": ("stage", "trip"),
        "t26_entry": ("sports",),
        "t28_form": ("form",),
        "t29_exam": ("sports",),
        "t32_choice": ("sports",),
        "t34_gaokao": ("exam",),
        "t35_score": ("exam",),
    }


    def calendar_month(turn_index=None):
        """回合号 → 自然月。T1=9 月，T5=1 月，T13=9 月（每年 9–6 月 + 7/8 月过场）。"""
        t = store.turn if turn_index is None else turn_index
        return (8 + (t - 1)) % 12 + 1


    def event_slot_at(turn_index=None):
        t = store.turn if turn_index is None else turn_index
        return t in SLOT_TURNS


    def event_months_cover_slot(eid):
        """这个事件的月窗口是否至少命中一个槽位月。

        槽位只落在偶数月（见 SLOT_TURNS）；窗口只写奇数月的事件永远抽不到，
        登记时看不出来——所以 event_pool 用例用这个函数把死数据挡在提交前。
        """
        e = EVENT_POOL[eid]
        if e["months"] is None:
            return True
        slot_months = set()
        for t in SLOT_TURNS:
            if school_year(t) == e["grade"]:
                slot_months.add(calendar_month(t))
        return bool(set(e["months"]) & slot_months)


    def month_mainline_tags(turn_index=None):
        """当月已登记的主线拍 union 出来的 tag 集合。"""
        t = store.turn if turn_index is None else turn_index
        tags = set()
        for bid, b in store.AI_BEATS.items():
            if not bid.startswith("t%d_" % t):
                continue
            if b.get("turn") == t or t in b.get("turns", ()):
                tags |= set(MAINLINE_TAGS.get(bid, ()))
        return tags


    def event_available(eid, turn_index=None, tags=None):
        """一个事件能不能在这个回合出现（不含 60% 与权重，只做硬过滤）。"""
        e = EVENT_POOL.get(eid)
        if e is None:
            raise Exception("未知事件：%r" % (eid,))
        t = store.turn if turn_index is None else turn_index
        if e["grade"] != school_year(t):
            return False
        months = e["months"]
        if months is not None and calendar_month(t) not in months:
            return False
        for flag in e.get("requires", ()):
            if not has_flag(flag):
                return False
        for other in e.get("exclude", ()):
            if store.event_seen.get(other):
                return False
        if tags is None:
            tags = month_mainline_tags(t)
        if set(e.get("tags", ())) & set(tags):
            return False
        return True


    def event_candidates(turn_index=None, tags=None):
        """本回合可抽的候选 id 列表，按 EVENT_POOL 的登记顺序（可复现）。"""
        t = store.turn if turn_index is None else turn_index
        if tags is None:
            tags = month_mainline_tags(t)
        return [eid for eid in EVENT_POOL if event_available(eid, t, tags)]


    def event_weights(eids):
        """同局已出过的 ×0.3，其余按表里的权重。"""
        out = []
        for eid in eids:
            w = EVENT_POOL[eid]["weight"]
            if store.event_seen.get(eid):
                w *= EVENT_SEEN_RATE
            out.append(w)
        return out


    def event_draw(turn_index=None, rng=None):
        """掷一个事件槽。返回事件 id，或 ""（没槽 / 没掷中 / 没有候选）。"""
        t = store.turn if turn_index is None else turn_index
        if not event_slot_at(t):
            return ""
        rng = renpy.random if rng is None else rng
        if rng.random() >= EVENT_HIT:
            return ""
        cands = event_candidates(t)
        if not cands:
            return ""
        return rng.choices(cands, weights=event_weights(cands), k=1)[0]


    def event_mark_seen(eid):
        """播完记一次，供互斥与权重衰减用。"""
        if eid not in EVENT_POOL:
            raise Exception("未知事件：%r" % (eid,))
        store.event_seen[eid] = int(store.event_seen.get(eid, 0)) + 1


    ## ── 事件选择点（《剧情大纲_三年_v1.md》§3.3，只给 4 个事件配）──────────
    ## 分支只改 rel，不置 Flag、不改 route、不新增拍；avoid/skip 记 0，没有负值。
    ## 模型仍然不许给选项：expect_choices=False 不变，下面这张表只给脚本用。
    EVENT_CHOICES = {
        "e_outing": (
            ("跟周墨一组", "with_zm"),
            ("跟夏幸悠一组", "with_xia"),
            ("跟温以宁一组", "with_x"),
        ),
        "e_parent1": (
            ("过去喊一声「周医生好」", "greet"),
            ("替她挡一句话", "cover"),
            ("装作没看见", "avoid"),
        ),
        "e_chorus": (
            ("报名合唱", "join"),
            ("只帮忙搬琴", "help"),
            ("不去", "skip"),
        ),
        "e_grad_photo": (
            ("站到周墨旁边", "with_zm"),
            ("站到夏幸悠旁边", "with_xia"),
            ("站到温以宁旁边", "with_x"),
        ),
    }

    ## 允许表：分支 → 该线 rel 增量。所有事件 rel 只能从这张表走（event_apply_choice）。
    EVENT_REL_GAINS = {
        ("e_outing", "with_zm"): {"zm": 5},
        ("e_outing", "with_xia"): {"xia": 5},
        ("e_outing", "with_x"): {"x": 5},
        ("e_parent1", "greet"): {"zm": 3},
        ("e_parent1", "cover"): {"zm": 8},
        ("e_parent1", "avoid"): {},
        ("e_chorus", "join"): {"zm": 5},
        ("e_chorus", "help"): {"zm": 3},
        ("e_chorus", "skip"): {},
        ("e_grad_photo", "with_zm"): {"zm": 5},
        ("e_grad_photo", "with_xia"): {"xia": 5},
        ("e_grad_photo", "with_x"): {"x": 5},
    }


    def event_has_choices(eid):
        return eid in EVENT_CHOICES


    def event_choice_items(eid):
        """给 renpy.display_menu 的 [(显示文本, action_key)]。"""
        if eid not in EVENT_CHOICES:
            raise Exception("这个事件没有选择点：%r" % (eid,))
        return [(text, key) for text, key in EVENT_CHOICES[eid]]


    def event_apply_choice(eid, key):
        """事件分支的 rel 增量只从允许表取；没登记的分支当场抛，不静默给 0。"""
        if eid not in EVENT_CHOICES:
            raise Exception("这个事件没有选择点：%r" % (eid,))
        if key not in [k for _, k in EVENT_CHOICES[eid]]:
            raise Exception("未知分支：%s/%s" % (eid, key))
        gains = EVENT_REL_GAINS.get((eid, key))
        if gains is None:
            raise Exception("分支没登记 rel 增量：%s/%s" % (eid, key))
        for sid, amount in gains.items():
            add_rel(sid, amount)
        return gains
