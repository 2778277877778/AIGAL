################################################################################
## 结局收口 —— 判定在 systems/stats.rpy，这里只负责「按 route 取哪一版正文」。
##
## 5 个结局（《剧情大纲_三年_v1.md》§4）：
##   route == zm 且 true_ending_v3()          → TRUE「最后一个音」
##   route == zm 但 true_ending_v3() 不成立    → 周墨 END（t8_end_c）
##   route == xia                             → 夏幸悠 END（t8_end_b）
##   route == x                               → 温以宁 END（t8_end_a）
##   route == none                            → 普通 END「三年过去了」（t36_end_other）
##
## route 在 T22 由 lock_route() 锁一次。没锁过的是旧 8 回合存档：直接走 none_end，
## 不再按旧 Flag 组合分 A/B/C —— t8_end_a/b/c 现在是三条线各自的正文，按旧组合分
## 会把周墨线的存档送到温以宁的结局里。t36_end_other 是路线中立的，语义才对得上。
################################################################################

init -1 python:

    ## 线 → END 正文的对照表（Chief 定：用表不用函数，一眼看全）。
    ## TRUE 是 zm 的加分项，不放进表；表里只放「这条线的 END」。
    ENDING_BY_ROUTE = {
        "zm": "zm_end",
        "xia": "xia_end",
        "x": "x_end",
        "none": "none_end",
    }

    ## 已声明的结局集合（含 TRUE），供「每个 route 都有可达结局」的断言用。
    ENDING_IDS = ("true",) + tuple(ENDING_BY_ROUTE[_r] for _r in ("zm", "xia", "x", "none"))

    ## 结局 id → 正文拍。ending_gate 和 replay.rpy 共用这一份，别在别处再写一张。
    ENDING_BEAT = {
        "true": "t8_true",
        "zm_end": "t8_end_c",
        "xia_end": "t8_end_b",
        "x_end": "t8_end_a",
        "none_end": "t36_end_other",
    }


    def ending_id():
        """当前状态该走哪个结局 id；纯读 store，不写任何东西。

        `route_done` 为假 = 旧 8 回合存档（或在 T22 之前被读出来的状态）：直接走
        none_end。这里**不再问 true_ending() / end_variant()** —— 那两个是旧结构的
        A/B/C 正文选择，而 t8_end_a/b/c 现在分别是温以宁 / 夏幸悠 / 周墨的正文，
        按旧 Flag 组合分会把玩家按到别人那条线的结尾上。
        """
        if not store.route_done:
            return "none_end"
        if store.route == "zm" and true_ending_v3():
            return "true"
        return ENDING_BY_ROUTE.get(store.route, "none_end")


label ending_gate:

    $ _eid = ending_id()
    $ trace_ending(_eid)

    if _eid == "true":
        ## TRUE 只有这一个是「同一拍、两种收法」：说了告白那句就多一段
        call ai_play(ENDING_BEAT["true"], "confess" if has_flag("confession") else "silent")
        $ _ending_line = "TRUE 结局 · 最后一个音"
    elif _eid == "zm_end":
        call ai_play(ENDING_BEAT["zm_end"])
        $ _ending_line = "END 结局 · 琴盖没开"
    elif _eid == "xia_end":
        call ai_play(ENDING_BEAT["xia_end"])
        $ _ending_line = "END 结局 · 跑道尽头"
    elif _eid == "x_end":
        call ai_play(ENDING_BEAT["x_end"])
        $ _ending_line = "END 结局 · 没打开的门"
    else:
        call ai_play(ENDING_BEAT["none_end"])
        $ _ending_line = "END 结局 · 三年过去了"

    ## 结局卡只出标题：提示语不在这里重复（留作结局收集页的提要）。
    ## 调试行只在开发模式出现，且不把内部 id / Flag 名摊给玩家。
    $ _ending_route = {"true": "周墨线", "zm_end": "周墨线", "xia_end": "夏幸悠线", "x_end": "温以宁线", "none_end": "无路线"}[_eid]
    call ending_card_display

    return


## 结局卡单独一个 label：剧情走它的同时，截图回归可以直接设好
## `_ending_line` / `_ending_route` 再 call 它，不必真的玩到 T36。
label ending_card_display:

    scene bg end_card
    "{color=#a9cbe4}{b}{size=+8}[_ending_line]{/size}{/b}{/color}"
    if config.developer:
        "（开发用：学习 [study] / 压力 [stress] / 路线 [_ending_route]）"
    "{color=#8899a6}—— 完 ——{/color}"

    return
