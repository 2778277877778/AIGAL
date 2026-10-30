################################################################################
## 结局收口 —— 判定在 systems/stats.rpy，这里只负责「取哪一版正文」。
##
##   true_ending() 为真            → TRUE「最后一个音」，台词按 confession 分两版
##   否则 end_variant() A/B/C      → END「琴盖没开」的三版正文，仍是一个结局
##
## 结局正文走 AI 的 ending 预算（160 字/行、600 字合计）；没 key 或超时取
## ai/fallback.rpy 里的 t8_true / t8_end_a / t8_end_b / t8_end_c 模板。
## 这里是整局最后一次 AI 呼叫，不预取、不重试第二拍。
################################################################################

label ending_gate:

    if true_ending():
        $ trace_ending("true")
        call ai_play("t8_true", "confess" if has_flag("confession") else "silent")
        $ _ending_line = "TRUE 结局 · 最后一个音"
        $ _ending_note = "弹错的音，也还在曲子里。"
    else:
        $ _end_var = end_variant()
        $ trace_ending("end_" + _end_var.lower())
        if _end_var == "A":
            call ai_play("t8_end_a")
        elif _end_var == "B":
            call ai_play("t8_end_b")
        else:
            call ai_play("t8_end_c")
        $ _ending_line = "END 结局 · 琴盖没开"
        $ _ending_note = "不是每首曲子都能弹完。"

    scene bg end_card
    "{size=+6}[_ending_line]{/size}"
    "[_ending_note]"
    $ _flag_names = "、".join(sorted(store.flags.keys())) or "（无）"
    "（本局：学习 [study] / 压力 [stress] / 已发生：[_flag_names]）"
    "—— 完 ——"

    return
