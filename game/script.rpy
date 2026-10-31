################################################################################
## 入口
##
## T1–T8 已接通（每个回合一个 label：t1_september … t8_june，见变量命名规范 §7），
## 分班名单之后进 story/endings.rpy 的 ending_gate，按 stats.rpy 的判定出 TRUE / END。
################################################################################

## 占位背景：美术给出正式背景图后换成 images/bg_*.png
image bg room = Solid("#101820")

label start:

    scene bg room

    $ trace_reset()

    "（高中校园物语 · 0.2.0）"

    jump t1_september
