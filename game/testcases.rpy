################################################################################
## 冒烟自测（Ren'Py testcase）
##
## 用法：
##   tools\renpy-8.5.3-sdk\lib\py3-windows-x86_64\python.exe renpy.py "<工程路径>" test
##   （不带 testcase 名就跑 global 套件里的全部用例）
##
## 覆盖：主菜单 → 开局 → 三句占位对白 → 回主菜单 → 设置 / 关于 / 帮助 进出。
## 剧本和存档流程写进来之后，再补读档、选项分支和数值断言。
##
## 两个踩过的坑，改测试时注意：
## 1. 对白推进用 advance，但最后一句要改成点文本 —— 点完脚本 return 回主菜单，
##    没有下一个可 advance 的对象，第三次 advance 会等到超时。
## 2. 勾选类的按钮（未读文字 / 选项之后 / 转场）目前 TTS 文本还是英文，
##    测试里要用 "Unseen Text" 这种旧名字才点得到；导航按钮用中文没问题。
################################################################################

testsuite global:
    teardown:
        exit

testcase smoke:
    $ _test.transition_timeout = 0.05

    # 主菜单 → 开局
    click "开始"
    pause .6

    advance
    advance
    click "数值系统在"
    pause .8

    # 设置：进得去出得来
    click "设置"
    pause .5
    click "返回"
    pause .5

    # 关于
    click "关于"
    pause .5
    click "返回"
    pause .5

    # 帮助 → 键盘页
    click "帮助"
    pause .5
    click "键盘"
    click "返回"
    pause .5
