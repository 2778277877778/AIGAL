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
default event_seen = {}        # 随机事件 id → 次数，同局权重衰减用（引擎还没接）
