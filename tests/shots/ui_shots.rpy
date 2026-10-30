################################################################################
## ui_shots.rpy —— 界面的截图回归（可选，平时不在 game\ 里）
##
## 用法：.\dev.ps1 shots              比对；失败会报差了多少像素
##       .\dev.ps1 shots overwrite    重新生成基准图（改过版式必须跑这个）
##
## 为什么放在 tests\shots\ 而不是 game\：Ren'Py 只加载 game\ 下的 .rpy，所以默认
## .\dev.ps1 test 根本看不到它。基准图跟 DPI、字体 hinting、窗口缩放绑死，换台机器
## 尺寸一变就整片红；红了大家就开始习惯红 —— 那比没有回归测试更糟。
## dev.ps1 shots 会把它临时拷进 game\ 跑一次，跑完删掉。
##
## （试过 testsuite 上标 enabled False：Ren'Py 8.5 只对叶子节点判 enabled，
##   父 suite 关了里面的 case 照样跑；而 enabled False 的 case 又不会被按名字
##   注册进测试表，点名也跑不起来。所以只能用「不在加载路径里」这个办法。）
##
## 一个 case 走完整路径：case 之间不复位界面，拆开的话后一个会从上一次停的菜单
## 开始，点不到「设置」。
##
## 容差 0.0005 = 屏幕像素的 0.05%：抗锯齿和字体 hinting 的小抖动不算失败。
## 拍之前把配置摆成固定一份（否则「当前 key」「就绪 / 未就绪」随玩家状态变），
## 拍完还原。
################################################################################

testcase ui_shot:
    ## 默认 5s 不够点两页 + 两张截图
    $ _test.timeout = 40

    $ _s = _ui_snap()
    $ aig.clear_key()
    $ aig.set_key_mode("persistent")
    $ aig.set_conf("base_url", aig.DEFAULT_CFG["base_url"])
    $ aig.set_conf("model", aig.DEFAULT_CFG["model"])
    $ aig.set_conf("temperature", aig.DEFAULT_CFG["temperature"])
    $ aig.set_conf("timeout", 8)
    $ aig.clear_last()

    pause 0.4
    click "设置"
    pause 0.8
    screenshot "prefs.png" max_pixel_difference 0.0005

    click "接口设置"
    pause 1.0
    screenshot "ai_setup.png" max_pixel_difference 0.0005

    ## 生成中浮层：真请求等待期才出现，测试里截不到，所以把状态摆好直接显示。
    ## 这里能截到就说明版式没问题；截不到说明 show_screen 在测试上下文里不生效。
    $ aig.GEN.update(jid=999, elapsed=3.4, shown=True, skipped=False)
    $ renpy.show_screen("ai_generating")
    $ renpy.restart_interaction()
    pause 0.6
    screenshot "ai_generating.png" max_pixel_difference 0.0005
    $ renpy.hide_screen("ai_generating")
    $ renpy.restart_interaction()
    $ aig.GEN.update(jid=0, elapsed=0.0, shown=False)

    $ _ui_restore(_s)

    ## 没有这行，跑完会停在主菜单等人点 —— 命令行这边看起来就是卡死
    exit
