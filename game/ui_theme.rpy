################################################################################
## UI 主题微调（美术）
##
## 这里只覆盖“样式”，不改 screens.rpy 的结构：
##   - 对白行距、名字字距
##   - 主菜单标题 / 菜单页标题 / 导航的字距
##   - 历史、存档槽的字号
##
## 颜色、字体、字号、间距的数值都在 gui.rpy；对白条、名札、选项按钮的图片在
## gui/textbox.png、gui/namebox.png、gui/button/choice_*_background.png。
## 图片用 tools/mkui.py 生成（仓库外），改主题色时重跑即可。
##
## init offset 1：保证在 screens.rpy（-1）之后生效。
################################################################################

init offset = 1


## 对白 ########################################################################

## 正文加一点行距，中文长段更好读。
style say_dialogue:
    line_spacing gui.scale(4)
    color gui.text_color

## 名字用主题色，加一点字距当标题。
style say_label:
    kerning gui.scale(2)


## 选项 ########################################################################

style choice_button_text:
    size gui.scale(24)
    kerning gui.scale(1)


## 主菜单 ######################################################################

style main_menu_title:
    font gui.title_text_font
    size gui.scale(64)
    kerning gui.scale(11)
    color "#ffffff"

style main_menu_vbox:
    spacing gui.scale(8)

style main_menu_version:
    size gui.scale(15)
    kerning gui.scale(4)
    color gui.idle_small_color


## 菜单页标题（存档 / 读档 / 设置 / 关于 …） ################################

style game_menu_label_text:
    font gui.title_text_font
    size gui.scale(40)
    kerning gui.scale(6)


## 导航与快捷菜单 ##############################################################

style navigation_button_text:
    kerning gui.scale(2)

style quick_button_text:
    kerning gui.scale(1)


## 历史记录 / 存档槽 ###########################################################

style history_text:
    size gui.scale(22)
    line_spacing gui.scale(4)

style history_name_text:
    size gui.scale(22)
    color gui.accent_color

style slot_button_text:
    size gui.scale(16)
