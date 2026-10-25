## systems/stats.rpy
##
## 四数值 / 行动点 / Flag 的唯一入口。
## 口径来源：《回合事件表_v2.2》§0 §3 §5 §7、《游戏设定总表_v2.4》§四。
##
## 规矩：剧情里不要写 `$ study += 5`，一律调用本文件的函数。
## 数值全部可调，改数字只改这里。

init -1 python:

    ## 初始值（设定总表 §四：学习 30 / 压力 10 / 体力 40 / 金钱 100）
    STAT_INIT = {"study": 30, "stress": 10, "stamina": 40, "money": 100}

    ## 回合规则
    ALLOWANCE_PER_MONTH = 150   # 月初生活费
    AP_PER_MONTH = 3            # 每月行动点
    AP_LAST_MONTH = 2           # T8 只有 2 点

    ## 阈值（设定总表 §四）
    STRESS_INSOMNIA = 80        # ≥80 失眠：学习减半
    STRESS_SICK = 95            # ≥95 生病：少 1 AP
    STAMINA_LOW = 20            # <20 学习/小游戏收益减半

    ## 考试线（回合事件表 §1）
    EXAM_LINES = {"月考": 35, "期中": 50, "期末": 60, "学年期末": 70}

    ## 结局门槛（回合事件表 §7）
    END_STUDY = 75
    END_STRESS = 70
    TRUE_FLAGS = ("found_garden", "art_fair", "club", "botanical", "subject_support", "same_subject")

    ## 行动表（回合事件表 §3）。study/stress/stamina 是纯增量，money 是花费。
    ## ap = 0 表示不消耗行动点。
    ACTIONS = {
        "class":       dict(label="去教室上课",   ap=1, study=5,  stress=8,  stamina=-7),
        "ask_zhoumo":  dict(label="找周墨问题",   ap=1, stress=-2),
        "study":       dict(label="去图书馆自习", ap=1, study=5,  stress=8,  stamina=-7),
        "study_with":  dict(label="和周墨一起自习", ap=1, study=4, stress=5),
        "canteen":     dict(label="去食堂吃饭",   ap=1, stress=-4, stamina=3, money=12),
        "shop":        dict(label="去小卖部",     ap=0),
        "sport":       dict(label="打球/跑操",    ap=1, stress=-4, stamina=10),
        "watch":       dict(label="看周子博打球", ap=1, stress=-4),
        "rest":        dict(label="回宿舍休息",   ap=1, stress=-10, stamina=8),
        "garden":      dict(label="上天台看花",   ap=1, stress=-8),
        "club":        dict(label="去花艺社",     ap=1, stress=-6),
    }

    def clamp(value, low=0, high=100):
        return max(low, min(high, value))

    def gain_multiplier():
        """失眠或体力不足时，正向收益减半（只作用于学习与体力类收益）。"""
        if store.stress >= STRESS_INSOMNIA:
            return 0.5
        if store.stamina < STAMINA_LOW:
            return 0.5
        return 1.0

    def add_stat(name, delta, affected_by_state=False):
        """改数值的唯一入口。affected_by_state=True 时按失眠/低体力打折正收益。"""
        if affected_by_state and delta > 0:
            delta = int(round(delta * gain_multiplier()))
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
        if act["ap"]:
            store.ap -= 1
        changed = {}
        for stat in ("study", "stress", "stamina"):
            if stat in act:
                changed[stat] = add_stat(stat, act[stat], affected_by_state=(stat == "study"))
        if "money" in act:
            changed["money"] = add_stat("money", -act["money"])
        return changed

    def start_month(turn_index, allowance=ALLOWANCE_PER_MONTH):
        """月初：生活费到账、行动点重置。turn_index 从 1 开始（T1..T8）。"""
        store.turn = turn_index
        add_stat("money", allowance)
        ap = AP_LAST_MONTH if turn_index >= 8 else AP_PER_MONTH
        if store.stress >= STRESS_SICK:
            ap -= 1                       # 生病：少 1 AP
        store.ap = max(0, ap)

    def exam_roll(line_name):
        """考试得分 = 学习 + 随机(−5, +5)。"""
        return clamp(store.study + renpy.random.randint(-5, 5))

    def exam_pass(line_name):
        return exam_roll(line_name) >= EXAM_LINES[line_name]

    def set_flag(name):
        store.flags[name] = True

    def has_flag(name):
        return bool(store.flags.get(name))

    def true_ending():
        """TRUE「花开的时候」：学习 ≥75、压力 ≤70、六个 Flag 全触发（不看好感）。"""
        return store.study >= END_STUDY and store.stress <= END_STRESS and all(has_flag(f) for f in TRUE_FLAGS)


## 存档状态 ####################################################################

default study = 30
default stress = 10
default stamina = 40
default money = 100
default ap = 3
default turn = 1
default flags = {}
