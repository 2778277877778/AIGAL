################################################################################
## ai/settings_screen.rpy —— M3 的三个界面
##
##   ai_setup       设置页的 API 段：base_url / model / key / temperature /
##                  timeout / json_mode + 测试连接 + key 落盘口径的选择
##   ai_debug       连接诊断：状态、缓存、最近一次原始返回、假请求按钮
##   ai_generating  生成中：0.35s 后才浮出来，Esc 或按钮取消后照常降级
##
## 配色/字号只取 gui.* 和第 8 号字号，跟现有菜单一致；不放新图片资源。
## 输入的 key 只在 ai_buf_key 里停一下，保存完立刻清空 —— 别让明文进存档。
################################################################################

default ai_buf_url = ""
default ai_buf_model = ""
default ai_buf_key = ""


style ai_field is frame:
    background "#ffffff12"
    padding (gui.scale(14), gui.scale(5))
    xsize gui.scale(620)

style ai_frame_body is frame:
    background "#ffffff0d"
    padding (gui.scale(14), gui.scale(10))
    xfill True

style ai_gen_frame is frame:
    background "#12161af7"
    padding (gui.scale(30), gui.scale(24))
    xalign 0.5
    yalign 0.5


## 设置页的 API 段 #############################################################

screen ai_setup():

    tag menu

    ## 每次进页面把当前配置灌进输入框；已存的 key 不回填。
    on "show" action Function(aig.ui_load)

    ## 离开时把 key 缓冲清掉：填了没保存也不许留着明文。
    on "hide" action Function(aig.ui_clear_buf)

    ## 测试连接是异步的，靠这个 timer 让结果自己刷出来。
    timer 0.25 repeat True action NullAction()

    use game_menu(_("AI 接口"), scroll="viewport"):

        vbox:
            spacing gui.scale(12)
            xsize gui.scale(860)

            text "AI 只负责把这一拍写出来。接口不通、没有 key，游戏照样能通关，台词换成本地模板。":
                size gui.scale(18)
                color gui.idle_color

            if aig.ready():
                text "● 接口已就绪" size gui.scale(19) color "#8ecf9b"
            else:
                text "● 未就绪：不会发请求，整局走本地模板" size gui.scale(19) color "#e0a04a"

            text ("当前 key：%s" % aig.dbg(aig.mask_key())):
                size gui.scale(18)
                color gui.idle_color

            ## 一键填地址和模型：省得玩家翻文档。key 不填，那是玩家自己的。
            hbox:
                spacing gui.scale(8)
                text "常用端点" size gui.scale(18) color gui.idle_color
                for _i, _p in enumerate(aig.PRESETS):
                    textbutton _p[0] action Function(aig.apply_preset, _i)
                text "（只填地址与模型，key 得自己填）":
                    size gui.scale(16)
                    color gui.idle_color

            null height gui.scale(4)

            ## base_url / model ------------------------------------------------
            text "接口地址 base_url" size gui.scale(19)
            frame:
                style "ai_field"
                input value VariableInputValue("ai_buf_url") length 300 size gui.scale(19)
            text "写到 /v1 为止就行，程序自己接 /chat/completions；中转站一般也这样填。":
                size gui.scale(16)
                color gui.idle_color

            text "模型名 model" size gui.scale(19)
            frame:
                style "ai_field"
                input value VariableInputValue("ai_buf_model") length 120 size gui.scale(19)
            text "比如 gpt-4o-mini、deepseek-chat、qwen-plus。填端点认的名字。":
                size gui.scale(16)
                color gui.idle_color

            null height gui.scale(4)

            ## key ------------------------------------------------------------
            text "API key" size gui.scale(19)
            frame:
                style "ai_field"
                input value VariableInputValue("ai_buf_key") length 300 size gui.scale(19)
            text "留空 = 不改动已存的 key。填了就是换掉它。":
                size gui.scale(16)
                color gui.idle_color

            vbox:
                style_prefix "radio"
                label "存法"
                textbutton "记住（明文写进存档目录）":
                    action Function(aig.set_key_mode, "persistent")
                    selected aig.key_mode() == "persistent"
                textbutton "仅本次会话（只在内存里）":
                    action Function(aig.set_key_mode, "session")
                    selected aig.key_mode() == "session"

            if aig.key_mode() == "persistent":
                text "「记住」会把 key 明文写进存档目录（persistent），能跨存档、跨重启用 —— 公用电脑请选会话。":
                    size gui.scale(16)
                    color "#e0a04a"
            else:
                text "「仅本次会话」不写盘：退出游戏就要重填，也不会出现在存档文件里。":
                    size gui.scale(16)
                    color "#8ecf9b"

            if aig.dirty():
                text "有还没保存的改动（地址 / 模型 / key）":
                    size gui.scale(17)
                    color "#e0a04a"

            hbox:
                spacing gui.scale(10)
                textbutton "保存接口参数" action Function(aig.ui_save)
                textbutton "清除 key" action [Function(aig.clear_key), Function(aig.ui_load)]
                textbutton "恢复默认" action Function(aig.ui_reset)
                textbutton "连接诊断" action ShowMenu("ai_debug")

            null height gui.scale(4)

            ## temperature / timeout ------------------------------------------
            text ("temperature　当前 %.2f" % float(aig.conf("temperature", 0.8))):
                size gui.scale(19)
            hbox:
                spacing gui.scale(8)
                for t in aig.TEMP_STEPS:
                    textbutton ("%.1f" % t):
                        action Function(aig.set_conf, "temperature", t)
                        selected abs(float(aig.conf("temperature", 0.8)) - t) < 0.001
            text "0.4 稳、0.8 默认、1.2 活。太低像在读说明书，太高人物会跑偏。":
                size gui.scale(16)
                color gui.idle_color

            text ("等待上限　当前 %d 秒%s" % (aig.cfg_timeout(), "" if abs(aig.cfg_timeout() - 8) < 0.1 else "（默认 8）")):
                size gui.scale(19)
            hbox:
                spacing gui.scale(8)
                for t in aig.TIMEOUT_STEPS:
                    textbutton ("%d 秒" % t):
                        action Function(aig.set_conf, "timeout", t)
                        selected abs(float(aig.cfg_timeout()) - t) < 0.001
            text "超过这个时间就切模板，不弹窗、不打断。端点慢就往大调；8 秒是默认。":
                size gui.scale(16)
                color gui.idle_color

            ## json_mode -------------------------------------------------------
            textbutton "让端点返回 JSON 模式（response_format）":
                action Function(aig.set_conf, "json_mode", not aig.conf("json_mode", True))
                selected bool(aig.conf("json_mode", True))
            text "端点报 400 / 说不认识 response_format，就关掉这里，靠提示词约束格式。":
                size gui.scale(16)
                color gui.idle_color

            null height gui.scale(6)

            ## 测试连接 --------------------------------------------------------
            hbox:
                spacing gui.scale(12)
                textbutton "测试连接" action Function(aig.probe)
                $ _ps, _pm = aig.probe_poll()
                if _ps == "done":
                    text aig.dbg(_pm) size gui.scale(18) color "#8ecf9b"
                elif _ps == "error":
                    text aig.dbg(_pm) size gui.scale(18) color "#e0705a"
                elif _ps == "running":
                    text aig.dbg(_pm) size gui.scale(18) color gui.idle_color
                else:
                    text "还没测过。发一条 1 token 的请求，路径 / key / model 一次验完。":
                        size gui.scale(18)
                        color gui.idle_color


## 连接诊断 ####################################################################

screen ai_debug():

    tag menu

    timer 0.5 repeat True action NullAction()

    use game_menu(_("连接诊断"), scroll="viewport"):

        vbox:
            spacing gui.scale(10)
            xsize gui.scale(860)

            text "只读页：改配置回「AI 接口」。下面的原始返回是 AI 层回来的正文，未经校验。":
                size gui.scale(17)
                color gui.idle_color

            for _k, _v in aig.debug_table():
                hbox:
                    spacing gui.scale(18)
                    text _k size gui.scale(17) color gui.idle_color xsize gui.scale(250)
                    text aig.dbg(_v) size gui.scale(17)

            ## 版面告警：文本会变、版面不变。超了框就压到画面上，测试不会报。
            $ _ls = aig.last_summary()
            if _ls["over_max"] > 0:
                text ("⚠ 最近一次返回有 %d 行超过校验上限 %d 字，schema 会把这些行剔掉；目标 %d 字，版面物理上限约 %d 字。" % (_ls["over_max"], aig.line_schema_max(), aig.LINE_PROMPT_TARGET, aig.LINE_FLOOR_MAX)):
                    size gui.scale(17)
                    color "#e0705a"
            elif _ls["over_target"] > 0:
                text ("● 最近一次返回有 %d 行超过提示词目标 %d 字（还没到校验线 %d，但已经 4 行边上了）。" % (_ls["over_target"], aig.LINE_PROMPT_TARGET, aig.line_schema_max())):
                    size gui.scale(17)
                    color "#e0a04a"

            null height gui.scale(6)

            text "假请求（不联网，走 start_fake，用来验收生成中界面和降级路径）":
                size gui.scale(18)
            hbox:
                spacing gui.scale(8)
                box_wrap True
                textbutton "正常" action Function(aig.debug_fake, "ok")
                textbutton "慢 2 秒" action Function(aig.debug_fake, "ok", 2.0)
                textbutton "坏 JSON" action Function(aig.debug_fake, "badjson")
                textbutton "空 choices" action Function(aig.debug_fake, "empty_choices")
                textbutton "超长" action Function(aig.debug_fake, "long_text")
                textbutton "注入标签" action Function(aig.debug_fake, "inject_tags")
                textbutton "注入插值" action Function(aig.debug_fake, "inject_interp")
                textbutton "超时" action Function(aig.debug_fake, "timeout")

            hbox:
                spacing gui.scale(8)
                textbutton "重置熔断" action Function(aig.reset_circuit)
                textbutton "清跨局缓存" action Function(aig.clear_persistent)
                textbutton "清空最近返回" action Function(aig.clear_last)

            null height gui.scale(6)

            text ("最近一次返回：%s" % aig.last_line()):
                size gui.scale(18)

            frame:
                style "ai_frame_body"
                ysize gui.scale(260)
                viewport:
                    mousewheel True
                    scrollbars "vertical"
                    vbox:
                        text aig.dbg(aig.last_text() or "（还没有请求）"):
                            size gui.scale(15)
                            color gui.idle_color


## 生成中 ######################################################################

screen ai_generating():

    ## 盖在最上面，把对白区的点击挡住；等完了由 wait_ui 自己 hide。
    zorder 200
    modal True

    ## Esc 默认是开游戏菜单，这里改成本拍跳过。
    key "game_menu" action Function(aig.skip_generating)

    ## 全屏压暗：add Solid 只铺到自身自然尺寸（截图上只看得到局部），
    ## 所以显式给虚拟分辨率大小。
    add Solid("#000000a8") xysize (config.screen_width, config.screen_height)

    frame:
        style "ai_gen_frame"

        vbox:
            spacing gui.scale(10)

            text "正在生成这一拍…" size gui.scale(26) color "#ffffff"
            text ("已等 %.1f 秒" % aig.GEN["elapsed"]):
                size gui.scale(18)
                color gui.idle_color
            text "跳过这一拍会用本地文本；同一存档以后这一拍也是这段（一出即定），要换只能显式重跑。":
                size gui.scale(17)
                color gui.idle_color

            hbox:
                spacing gui.scale(10)
                textbutton "跳过（Esc）" action Function(aig.skip_generating)


## 降级横幅 ####################################################################
## 「一出即定」是不可逆的，所以出口必须在降级那一刻出现：一条不挡对白的横幅，
## 15 秒后自己收；「重跑这一拍」= 解除钉住 + 回退到本拍开头，重进时重新生成。

screen ai_degraded():

    zorder 150

    timer 15.0 action Hide("ai_degraded")

    frame:
        background "#12161af2"
        padding (gui.scale(20), gui.scale(12))
        xalign 0.5
        yoffset gui.scale(24)

        vbox:
            spacing gui.scale(8)

            text aig.degraded_line() size gui.scale(17) color "#e0a04a"

            hbox:
                spacing gui.scale(10)
                if aig.ready():
                    textbutton "重跑这一拍" action [Function(aig.rerun_beat), Rollback()]
                else:
                    textbutton "去填 API key" action [Function(aig.damp_degraded), ShowMenu("ai_setup")]
                textbutton "知道了" action Hide("ai_degraded")
