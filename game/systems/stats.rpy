## systems/stats.rpy
##
## 四数值 / 行动点 / Flag 的唯一入口。
## 口径来源：剧情大纲_三年_v1.md §6，数值表见本文件。
##
## 规矩：剧情里不要写 `$ study += 5`，一律调用本文件的函数。
## 数值全部可调，改数字只改这里。

init -1 python:

    ## 初始值（设定总表 §四：学习 30 / 压力 10 / 体力 40 / 金钱 100）
    STAT_INIT = {"study": 30, "stress": 10, "stamina": 40, "money": 100}

    ## 回合规则（三年版 36 格：30 完整 + 6 暑假过场）
    ALLOWANCE_PER_MONTH = 150   # 月初生活费
    AP_PER_MONTH = 3            # 高一 / 高二常规月
    AP_GAOKAO_MONTH = 1         # T34 高考月
    ## 行动点特例：T10 / T22 期末月 2 点，高三（T25–T33）2 点，T34 只有 1 点
    AP_OVERRIDE = {10: 2, 22: 2, 34: AP_GAOKAO_MONTH}
    SUMMER_TURNS = (11, 12, 23, 24, 35, 36)   # 暑假短过场：不抽事件、不给选项

    ## 阈值（设定总表 §四）
    STRESS_INSOMNIA = 80        # ≥80 失眠：学习减半
    STRESS_SICK = 95            # ≥95 生病：少 1 AP
    STAMINA_LOW = 20            # <20 学习/小游戏收益减半

    ## 考试线按学年分段（三年版 §6）；gaokao 是终局唯一线
    EXAM_LINES_BY_YEAR = {
        1: {"monthly": 35, "midterm": 50, "final": 60},
        2: {"monthly": 50, "midterm": 65, "final": 75},
        3: {"monthly": 60, "midterm": 75, "final": 85},
    }
    GAOKAO_LINE = 85

    ## 学习类行动收益按学年递减（三年版 §6）：剧情给的固定值不打折
    STUDY_RATE_BY_YEAR = {1: 1.0, 2: 0.8, 3: 0.6}

    ## 结局门槛（回合事件表 §7；三年版的第 4 节另有一套，等 36 格接通再换）
    END_STUDY = 75
    END_STRESS = 70
    TRUE_FLAGS = ("found_piano_room", "art_fair", "club", "music_hall", "subject_support", "same_subject")

    ## Flag 的唯一名单（《剧情大纲_三年_v1.md》§5：三线各 5–6 个 + 公共）。
    ## set_flag 只认这些名字，拼错一个字母会当场抛异常。
    FLAG_NAMES = (
        ## 公共 / 周墨线（旧版内容不废）
        "met_zhoumo", "offered_candy", "heard_piano", "heard_call",
        "found_piano_room", "art_fair", "sheet_music", "piano_crisis",
        "club", "music_hall", "subject_support", "same_subject", "confession",
        ## 三年版新增：周墨线
        "zm_father", "zm_choice", "zm_mother",
        ## 夏幸悠线
        "xia_met", "xia_injury", "xia_parent", "xia_stay",
        "xia_entry", "xia_exam", "xia_choice",
        ## 温以宁线
        "x_met", "x_family", "x_offer", "x_choice",
        ## 终局
        "gaokao_pass",
    )

    ## 行动表（回合事件表 §3）。study/stress/stamina 是纯增量，money 是花费。
    ## ap = 0 表示不消耗行动点。key 同时是剧情里调 do_action() 时传的名字。
    ACTIONS = {
        "attend_class":     dict(label="去教室上课",     ap=1, study=5,  stress=8,  stamina=-7),
        "ask_zhoumo":       dict(label="找周墨问题",     ap=1, stress=-2),
        "study":            dict(label="去图书馆自习",   ap=1, study=5,  stress=8,  stamina=-7),
        "study_with":       dict(label="和周墨一起自习", ap=1, study=4, stress=5),
        "eat_canteen":      dict(label="去食堂吃饭",     ap=1, stress=-4, stamina=3, money=12),
        "buy_shop":         dict(label="去小卖部",       ap=0),   # 只开商店界面，扣钱走 add_stat("money", -价)
        "do_sport":         dict(label="打球/跑操",      ap=1, stress=-4, stamina=10),
        "watch_basketball": dict(label="看周子博打球",   ap=1, stress=-4),
        "rest_dorm":        dict(label="回宿舍休息",     ap=1, stress=-10, stamina=8),
        "listen_piano":     dict(label="站在琴房外听",   ap=1, stress=-8),   # 旧琴房，T3–T4
        "visit_auditorium": dict(label="去礼堂看琴",     ap=1, stress=-8),   # 礼堂，T5 后
        "visit_club":       dict(label="去音乐社",       ap=1, stress=-6),   # 艺术楼，T6 后
        "weekend_stay":     dict(label="周末留校",       ap=0, stress=-8),   # 每月一次减压口（三年版 §6）
    }

    ## 地图节点（回合事件表 §4）。key 由 campus_map 和剧情共用，label 是界面上的字，
    ## unlock 是解锁回合号（T 几）。节点常驻的人写在文档里，不进代码。
    NODES = {
        "dorm":         dict(label="宿舍",     unlock=1),
        "classroom":    dict(label="教室",     unlock=1),
        "library":      dict(label="图书馆",   unlock=1),
        "canteen":      dict(label="食堂",     unlock=1),
        "shop":         dict(label="小卖部",   unlock=1),
        "field":        dict(label="操场",     unlock=1),
        "art_building": dict(label="艺术楼",   unlock=2),
        "piano_room":   dict(label="旧琴房",   unlock=3),
        "auditorium":   dict(label="礼堂",     unlock=5),
        "music_room":   dict(label="音乐教室", unlock=6),
    }

    def unlocked_nodes():
        """当前回合能点的节点 key 列表，按 NODES 里的顺序。"""
        return [k for k, v in NODES.items() if store.turn >= v["unlock"]]

    def node_label(key):
        return NODES[key]["label"]

    def clamp(value, low=0, high=100):
        return max(low, min(high, value))

    def gain_multiplier():
        """失眠或体力不足时，正向收益减半（只作用于学习与体力类收益）。"""
        if store.stress >= STRESS_INSOMNIA:
            return 0.5
        if store.stamina < STAMINA_LOW:
            return 0.5
        return 1.0

    def school_year(turn_index=None):
        """回合号 → 学年（1/2/3）；暑假短过场返回 0。36 格总表见剧情大纲 §1。"""
        t = store.turn if turn_index is None else turn_index
        if 1 <= t <= 10:
            return 1
        if 13 <= t <= 22:
            return 2
        if 25 <= t <= 34:
            return 3
        return 0

    def study_rate():
        """学习类行动收益的学年系数（三年版 §6：1.0 / 0.8 / 0.6）。"""
        return STUDY_RATE_BY_YEAR.get(school_year(), 1.0)

    def ap_for_month(turn_index):
        """这一回合的行动点：高一/高二 3 点，T10/T22 与高三 2 点，T34 高考月 1 点。"""
        if 25 <= turn_index <= 34:
            return AP_OVERRIDE.get(turn_index, 2)
        return AP_OVERRIDE.get(turn_index, AP_PER_MONTH)

    def exam_line(line_key):
        """按当前学年取及格线；gaokao 固定 85，yearly 是旧名、按当年期末算。"""
        if line_key == "gaokao":
            return GAOKAO_LINE
        year = school_year() or 1
        if line_key == "yearly":
            line_key = "final"
        return EXAM_LINES_BY_YEAR[year][line_key]

    def add_stat(name, delta, affected_by_state=False):
        """改数值的唯一入口。affected_by_state=True 时按失眠/低体力 × 学年系数打折。

        打折后四舍五入取整（5 减半 = 2.5 → 3），不用 Python 的 round()：
        round(2.5) 走 banker's rounding 会给 2，失眠时反而比「减半」更狠。
        """
        if affected_by_state and delta > 0:
            delta = int(delta * gain_multiplier() * study_rate() + 0.5)
        if name == "money":
            store.money = max(0, store.money + delta)
        else:
            setattr(store, name, clamp(getattr(store, name) + delta))
        return delta

    def can_act():
        return store.ap > 0

    def do_action(key):
        """执行一次行动，扣 AP 并结算数值。返回实际变化，供 UI 显示。"""
        act = ACTIONS.get(key)
        if act is None:
            raise Exception("未知行动：%s" % key)
        if act["ap"] and not can_act():
            return False
        if key == "weekend_stay":
            if store.weekend_used:
                return False          # 每月一次减压口，多按不给
            store.weekend_used = True
        if act["ap"]:
            store.ap -= 1
        changed = {}
        for stat in ("study", "stress", "stamina"):
            if stat in act:
                changed[stat] = add_stat(stat, act[stat], affected_by_state=(stat == "study"))
        if "money" in act:
            changed["money"] = add_stat("money", -act["money"])
        ## 好感不由数值表给：按行动所在节点算（relations.rpy，每月每线一次）
        _rel = add_rel_from_action(key)
        if _rel:
            changed["rel_gain"] = _rel
        return changed

    def start_month(turn_index, allowance=ALLOWANCE_PER_MONTH):
        """月初：生活费到账、行动点重置。turn_index 从 1 开始（T1..T36）。"""
        store.turn = turn_index
        add_stat("money", allowance)
        ap = ap_for_month(turn_index)
        if store.stress >= STRESS_SICK:
            ap -= 1                       # 生病：少 1 AP
        store.ap = max(0, ap)
        store.weekend_used = False        # 每月的减压口重新可用

    def exam_roll():
        """掷一次：学习 + 随机(−5, +5)，存进 store.exam_score 并返回。

        同一回合查多条及格线（月考/期中/期末）共用这一次掷点，不会各掷一个随机数。
        """
        store.exam_score = clamp(store.study + renpy.random.randint(-5, 5))
        return store.exam_score

    def exam_pass(line_key):
        """拿 store.exam_score 比当前学年的及格线，不重新掷。

        key：monthly / midterm / final / yearly（旧名，按当年期末）/ gaokao（固定 85）。
        调用约定：同一回合必须先 exam_roll() 再 exam_pass()，月末流程固定是
        「exam_roll() → exam_pass(key)」。没掷过（exam_score 是 None）会直接抛。
        """
        if store.exam_score is None:
            raise Exception("还没掷点：exam_pass(%r) 之前必须先调 exam_roll()" % line_key)
        return store.exam_score >= exam_line(line_key)

    def set_flag(name):
        if name not in FLAG_NAMES:
            raise Exception("未知 Flag：%s（名单见 FLAG_NAMES / 变量命名规范 §5）" % name)
        store.flags[name] = True
        trace_flag(name)

    def has_flag(name):
        return bool(store.flags.get(name))

    ## ── 历史函数（8 回合结构，生产路径已不调用）──────────────────────────────
    ## endings.rpy 的 ending_id() 在旧存档（route_done 为假）时直接走 none_end，
    ## 不再问这两个函数。保留它们只给回归用例读旧口径；新代码别再调 ——
    ## END 正文已经按线拆成 t8_end_a/b/c，A/B/C 这套旧 Flag 组合不再对应任何正文。

    def true_ending():
        """【历史】TRUE「最后一个音」（8 回合口径）：学习 ≥75、压力 ≤70、六个 Flag 全触发。"""
        return store.study >= END_STUDY and store.stress <= END_STRESS and all(has_flag(f) for f in TRUE_FLAGS)

    def end_variant():
        """【历史】END 正文的旧变体（回合事件表 §7.1）：A 表被改回 / B 没跟着填 / C 曲子弹断了。

        只该在 true_ending() 为假时调用；输出 A/B/C，**不再对应 t8_end_a/b/c 的正文**。
        """
        if not has_flag("subject_support"):
            return "A"
        if not has_flag("same_subject"):
            return "B"
        return "C"

    def true_ending_v3():
        """三年版 TRUE（大纲 §4）：高考 ≥85、压力 ≤60、route == zm、
        rel_zm ≥60、周墨 10 个里程碑全中。判定永不读 AI 输出。"""
        return (store.exam_score is not None
                and store.exam_score >= GAOKAO_LINE
                and store.stress <= 60
                and store.route == "zm"
                and store.rel_zm >= 60
                and all(has_flag(f) for f in MILESTONE_FLAGS["zm"]))


## 存档状态 ####################################################################
## 初始值只写在 STAT_INIT 一处，这里从它取，别再重复写数字。

default study = STAT_INIT["study"]
default stress = STAT_INIT["stress"]
default stamina = STAT_INIT["stamina"]
default money = STAT_INIT["money"]
default ap = AP_PER_MONTH
default exam_score = None   # 最近一次 exam_roll() 的掷点；None = 本回合还没掷，exam_pass 会抛
default turn = 1
default flags = {}
default weekend_used = False   # 本月「周末留校」用没用过（start_month 重置）
