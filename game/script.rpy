################################################################################
## 入口脚本（占位）
##
## 目前只有工程骨架：选项、GUI、中文字体、四数值系统（game/systems/stats.rpy）。
## 正式剧本按《剧本_周墨线_第一幕_开学.md》（钢琴线 T1）拆成
## game/story/t1_september.rpy … t8_june.rpy。
################################################################################

## 占位背景：等《美术》给出正式背景图后换成 images/bg_xxx.png
image bg room = Solid("#101820")

label start:

    scene bg room

    "（工程骨架已跑通：Ren'Py 8.5.3、1920×1080、思源黑体 Lite。）"

    "剧本还没写进来。八个月的第一幕在 game/story/ 等着落地。"

    "数值系统在 game/systems/stats.rpy，剧情里改数值请调用 do_action / add_stat。"

    return
