################################################################################
## 通用自由行动段（T2 以后每个月都 call 它）
##
## 每个行动演出一小段 AI 文本：call ai_play("t2_free", "<action_key>")
## 同一个月的同一个行动 choice_path 相同 → 落到同一个缓存 key，重复点不会重买。
##
## 已知取舍：这里是「每个行动一次调用」，不是玩法策划 定的「自由段打包一次」。
## 打包要 AI 一次返回 action_key → 短句的映射，那是新的输出形状（schema 那边的事），
## 现在按每行动一次跑，一个月最多 AP 次（2 点 AP 就是 2 次）。
##
## 只放会消耗 AP 的行动：buy_shop 是 0 AP，放进这个 while 会死循环。
################################################################################

label free_actions:

    $ _ai_free = "t%d_free" % turn

    "（本月还有 [ap] 点行动点。）"

    ## unlocked_nodes() 全空时不能留一个空 menu —— Ren'Py 遇空 menu 直接抛异常，不是降级
    while ap > 0 and unlocked_nodes():

        menu:
            "去教室上课" if "classroom" in unlocked_nodes():
                $ do_action("attend_class")
                call ai_play(_ai_free, "attend_class")

            "找周墨" if "classroom" in unlocked_nodes():
                $ do_action("ask_zhoumo")
                call ai_play(_ai_free, "ask_zhoumo")

            "去图书馆自习" if "library" in unlocked_nodes():
                $ do_action("study")
                call ai_play(_ai_free, "study")

            "和周墨一起自习" if "library" in unlocked_nodes() and turn >= 2:
                $ do_action("study_with")
                call ai_play(_ai_free, "study_with")

            "去食堂吃饭" if "canteen" in unlocked_nodes():
                $ do_action("eat_canteen")
                call ai_play(_ai_free, "eat_canteen")

            "去操场活动" if "field" in unlocked_nodes():
                $ do_action("do_sport")
                call ai_play(_ai_free, "do_sport")

            "看周子博打球" if "field" in unlocked_nodes():
                $ do_action("watch_basketball")
                call ai_play(_ai_free, "watch_basketball")

            "回宿舍休息" if "dorm" in unlocked_nodes():
                $ do_action("rest_dorm")
                call ai_play(_ai_free, "rest_dorm")

            "站在琴房外听" if "piano_room" in unlocked_nodes():
                $ do_action("listen_piano")
                call ai_play(_ai_free, "listen_piano")

            "去礼堂看琴" if "auditorium" in unlocked_nodes():
                $ do_action("visit_auditorium")
                call ai_play(_ai_free, "visit_auditorium")

            "去音乐社" if "music_room" in unlocked_nodes():
                $ do_action("visit_club")
                call ai_play(_ai_free, "visit_club")

    if ap > 0:
        "（这个月没地方可去了。）"
    else:
        "（行动点用完了，这个月就这样。）"
    return
