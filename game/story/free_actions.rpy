################################################################################
## 通用自由行动段（T2 以后每个月都 call 它）
##
## 自由行动**不调 AI**（Chief 定的）：它是数值行为，8 个月里同一动作要重复十几次，
## 每次挂一次可见等待不划算。正文走 fallback.rpy 的变体池，按本局已用次数轮转，
## 同局内不重句——这里恰好是全游戏点击最密的地方，第二次就认出死文本会很廉价。
##
## 轮转状态在 store.ai_free_counts（进存档），读档后接着上次的序号，不重抽。
## 只有「这个月没地方可去」和月末收尾这两句是纯脚本文本。
##
## 只放会消耗 AP 的行动：buy_shop 是 0 AP，放进这个 while 会死循环。
################################################################################

label free_actions:

    "（本月还有 [ap] 点行动点。）"

    ## unlocked_nodes() 全空时不能留一个空 menu —— Ren'Py 遇空 menu 直接抛异常，不是降级
    while ap > 0 and unlocked_nodes():

        menu:
            "去教室上课" if "classroom" in unlocked_nodes():
                $ do_action("attend_class")
                call ai_free_scene("attend_class")

            "找周墨" if "classroom" in unlocked_nodes():
                $ do_action("ask_zhoumo")
                call ai_free_scene("ask_zhoumo")

            "去图书馆自习" if "library" in unlocked_nodes():
                $ do_action("study")
                call ai_free_scene("study")

            "和周墨一起自习" if "library" in unlocked_nodes() and turn >= 2:
                $ do_action("study_with")
                call ai_free_scene("study_with")

            "去食堂吃饭" if "canteen" in unlocked_nodes():
                $ do_action("eat_canteen")
                call ai_free_scene("eat_canteen")

            "去操场活动" if "field" in unlocked_nodes():
                $ do_action("do_sport")
                call ai_free_scene("do_sport")

            "看周子博打球" if "field" in unlocked_nodes():
                $ do_action("watch_basketball")
                call ai_free_scene("watch_basketball")

            "回宿舍休息" if "dorm" in unlocked_nodes():
                $ do_action("rest_dorm")
                call ai_free_scene("rest_dorm")

            "站在琴房外听" if "piano_room" in unlocked_nodes():
                $ do_action("listen_piano")
                call ai_free_scene("listen_piano")

            "去礼堂看琴" if "auditorium" in unlocked_nodes():
                $ do_action("visit_auditorium")
                call ai_free_scene("visit_auditorium")

            "去音乐社" if "music_room" in unlocked_nodes():
                $ do_action("visit_club")
                call ai_free_scene("visit_club")

            ## 0 AP 的减压口，每月一次（store.weekend_used 由 start_month 重置）。
            "周末留校（减压，本月一次）" if not weekend_used:
                $ do_action("weekend_stay")
                call ai_free_scene("weekend_stay")

    if ap > 0:
        "（这个月没地方可去了。）"
    else:
        ## 每月结算：收掉已结束的任务，只留最近 20 条给诊断页
        $ aig.clear_jobs()
        ## 最后一点 AP 用掉的这一刻，正好是下个月第一拍预取的触发点。
        ## T3 起的拍还没登记时 prefetch_first 会返回 0，不会报错；登记后自动生效。
        $ aig.prefetch_first(turn + 1)
        "（行动点用完了，这个月就这样。）"
    return
