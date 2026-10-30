"""AIGAL 的纯 Python 模块。

放这里（game/python-packages/）而不是 game/ 下面，是因为 Ren'Py 会把这个目录加进
sys.path 并一起打进 RPA（见 SDK 的 renpy/importer.py:359），打包后 import 照样成立。
game/ai/*.rpy 只做 Ren'Py 绑定，逻辑都在这层，能在 Ren'Py 外面直接跑测试。
"""
