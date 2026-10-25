init -100 python in gui:

    def scale(n):
        # gui.rpy / screens.rpy 里的数字是按 1280×720 设计的模板值，
        # 工程实际是 1920×1080，所以统一放大 1.5 倍。
        # 不放大时字会小 1/3，对白条只有 185px 高（应为 278px）。
        return int(round(n * 1.5))


## 模板自带的这段会在每次启动（包括 lint）时，按 gui.accent_color 重新烘焙
## gui/ 下的图片：对白条、名札、按钮、滑条、滚动条……
##
## 现在对白条、名札、选项按钮换成了手绘素材（tools/mkui.py 生成），自动烘焙会
## 把它们覆盖回默认样子，所以关掉。要换主题色重新烘焙时，临时打开这段跑一次，
## 再重跑 tools/mkui.py 恢复手绘素材。
##
# init 100 python in gui:
#
#     if not renpy.mobile:
#         from store import config
#
#         import sys
#         import os
#         sys.path.insert(0, os.path.join(config.renpy_base, "launcher", "game"))
#
#         from gui7.parameters import GuiParameters
#         from gui7.images import ImageGenerator
#         from gui7 import generate_gui
#
#         p = GuiParameters(
#             config.gamedir, config.gamedir,
#             config.screen_width, config.screen_height,
#             accent_color, "#000000", False, None,
#             True, False, False, "gui")
#
#         p.skip_backup = True
#
#         generate_gui(p)
#
#         _skip_backup = True
#         _gui_images()
