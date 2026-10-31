################################################################################
## systems/replay.rpy —— 只读回放：给定选择序列，返回 (beat 序列, Flag 集合, 结局 id)
##
## 给「变／不变」五条断言里的 1（骨架不变）、3（结局收敛）、5（无 key 同构）共用。
## 纯函数：不调 AI、不写 store、不读存档、不看 provider——所以有 key / 没 key 结果必然一样。
##
## picks 是「选择点 → 分支 id」的序列，键名与 story 里的变量一致：
##   t2_piano / t2_call / t3_piano / t4_artfair / t4_newyear / t5_move /
##   t6_club / t7_talk / t8_subject / t8_form / confession
## 缺省取 story 里脚本书写的那一支，和脚本的默认值对齐。
##
## study / stress 是结局判定要用的终局数值（自由行动的净效果由调用方给），
## 默认 30 / 10 = 完全不做自由行动。route / rel_zm / flags 同理，由调用方给：
## 回放模型不重建 T9+ 的里程碑过程，要判 TRUE 就把那 10 个 Flag 用 flags 传进来。
##
## 结局 id 与 endings.rpy 走**同一套表**（ENDING_BY_ROUTE / ENDING_BEAT），
## 这里不另存一份「线 → 正文」的映射，也不自己发明结局名。
##
## ⚠ 这张表是「T1–T8 八回合骨架」的过渡模型：只回放 T1–T8 的拍，不模拟事件槽、
##   自由行动和 T9+ 的里程碑。36 格表驱动落地后删掉本文件，改成从月表直接算；
##   在那之前它是唯一一份可以被测试直接调用的纯回放——**简化模型，不是第二条真相**。
################################################################################

init -1 python:

    ## 每个回合的 AI 拍，顺序与 story/t2_october.rpy … t8_june.rpy 一致。
    ## T1 是手写（0 次 AI 调用），不计入 beat 序列。
    REPLAY_TURNS = (
        (2, ("t2_track", "t2_piano", "t2_call")),
        (3, ("t3_parent",)),
        (4, ("t4_borrow", "t4_artfair")),
        (5, ("t5_move", "t5_mother")),
        (6, ("t6_club",)),
        (7, ("t7_hall",)),
        (8, ("t8_subject", "t8_form")),
    )

    ## 这些拍由脚本事先置位，与选择无关（T1 的两条是手写段固定置位）。
    REPLAY_BASE_FLAGS = ("met_zhoumo", "offered_candy")

    REPLAY_FLAGS = {
        2: ("heard_piano", "heard_call", "xia_met"),
        3: ("found_piano_room",),
        4: ("art_fair", "sheet_music", "x_met"),
        5: ("piano_crisis",),
        6: ("club",),
        7: ("music_hall",),
    }

    ## 选择点的默认分支：与各 story 文件里 menu 的默认/最省事那一支一致。
    REPLAY_DEFAULTS = {
        "t2_piano": "reveal",
        "t2_call": "stay",
        "t3_piano": "silent",
        "t4_artfair": "quiet",
        "t4_newyear": "metronome",
        "t5_move": "move",
        "t6_club": "help",
        "t7_talk": "silent",
        "t8_subject": "silent",
        "t8_form": "different",
        "confession": "no",
    }


    def replay_trace(picks=None, study=30, stress=10, route="none", rel_zm=0, flags=None):
        """选择序列 → (beat 序列, Flag 集合, 结局 id)。纯函数，可重复调用、结果逐字相同。

        route / rel_zm / flags 是终局输入：不传就是「没锁线、里程一个没中」，
        结局落在 none_end。判 TRUE 需要的 10 个周墨里程碑 Flag 由 flags 传入
        （回放模型只重建 T1–T8 的剧情 Flag，不重建 T9+ 的里程碑过程）。
        """
        chosen = dict(REPLAY_DEFAULTS)
        chosen.update(picks or {})

        unknown = set(chosen) - set(REPLAY_DEFAULTS)
        if unknown:
            raise Exception("回放里有未知的选择点：%s" % ", ".join(sorted(unknown)))

        beats = []
        story_flags = list(REPLAY_BASE_FLAGS)
        for turn, seq in REPLAY_TURNS:
            beats.extend(seq)
            story_flags.extend(REPLAY_FLAGS.get(turn, ()))

        if chosen["t8_subject"] == "support":
            story_flags.append("subject_support")
        if chosen["t8_form"] == "same":
            story_flags.append("same_subject")
        if chosen["confession"] == "yes":
            story_flags.append("confession")

        ## 结局判定与 endings.rpy 同口径：route 决定走哪条线，TRUE 只可能出在周墨线。
        ## 结局 id 不在这里拼字符串，全部取自 ENDING_BY_ROUTE / ENDING_BEAT。
        ## _flags 由「回放重建的剧情 Flag」+「调用方传入的终局 Flag」合起来算；
        ## 注意别把参数 flags 覆盖掉（上一版就是在这里把入参 shadow 掉了）。
        _flags = set(story_flags) | set(flags or ())
        if (route == "zm"
                and study >= GAOKAO_LINE
                and stress <= 60
                and rel_zm >= 60
                and all(f in _flags for f in MILESTONE_FLAGS["zm"])):
            ending = "true"
        else:
            ending = ENDING_BY_ROUTE.get(route, "none_end")

        beats.append(ENDING_BEAT[ending])
        return (tuple(beats), tuple(sorted(set(story_flags))), ending)
