################################################################################
## 界面中文化
##
## Ren'Py 模板自带的按钮文字都是英文，这里统一改成中文。
## 用 `translate None strings` 覆盖默认语言（简体中文）的界面字符串，
## 不动 screens.rpy 里的原文，以后要做多语言也不会打架。
################################################################################

translate None strings:

    ## 主菜单 / 导航 ##########################################################
    old "Start"
    new "开始"

    old "Load"
    new "读档"

    old "Save"
    new "存档"

    old "Preferences"
    new "设置"

    old "About"
    new "关于"

    old "Help"
    new "帮助"

    old "Quit"
    new "退出"

    old "History"
    new "回顾"

    old "Main Menu"
    new "返回标题"

    old "Return"
    new "返回"

    old "End Replay"
    new "结束回放"

    ## 快捷菜单 ##############################################################
    old "Back"
    new "回退"

    old "Skip"
    new "快进"

    old "Auto"
    new "自动"

    old "Q.Save"
    new "快存"

    old "Q.Load"
    new "快读"

    old "Prefs"
    new "设置"

    old "Skipping"
    new "快进中"

    ## 设置页 ################################################################
    old "Display"
    new "画面"

    old "Window"
    new "窗口"

    old "Fullscreen"
    new "全屏"

    old "Rollback Side"
    new "回退侧"

    old "Disable"
    new "关闭"

    old "Left"
    new "左侧"

    old "Right"
    new "右侧"

    old "Unseen Text"
    new "未读文字"

    old "After Choices"
    new "选项之后"

    old "Transitions"
    new "转场"

    old "Text Speed"
    new "文字速度"

    old "Auto-Forward Time"
    new "自动前进"

    old "Music Volume"
    new "音乐音量"

    old "Sound Volume"
    new "音效音量"

    old "Voice Volume"
    new "语音音量"

    old "Mute All"
    new "全部静音"

    old "Test"
    new "试听"

    ## 存档 / 读档 ###########################################################
    old "Page {}"
    new "第 {} 页"

    old "Automatic saves"
    new "自动存档"

    old "Quick saves"
    new "快速存档"

    old "empty slot"
    new "空档位"

    old "Upload Sync"
    new "上传同步"

    old "Download Sync"
    new "下载同步"

    ## 确认框 ################################################################
    old "Yes"
    new "确定"

    old "No"
    new "取消"

    old "Are you sure?"
    new "确定吗？"

    old "Are you sure you want to quit?"
    new "确定要退出游戏吗？"

    old "Are you sure you want to return to the main menu?\nThis will lose unsaved progress."
    new "确定返回标题画面吗？\n未保存的进度会丢失。"

    old "Are you sure you want to end the replay?"
    new "确定结束回放吗？"

    old "Are you sure you want to begin skipping?"
    new "确定开始快进吗？"

    old "Are you sure you want to skip to the next choice?"
    new "确定快进到下一个选项吗？"

    old "Are you sure you want to skip unseen dialogue to the next choice?"
    new "确定跳过未读文字、快进到下一个选项吗？"

    ## 回顾 / 关于 ###########################################################
    old "The dialogue history is empty."
    new "还没有可以回顾的对白。"

    old "Version [config.version!t]\n"
    new "版本 [config.version!t]\n"

    old "Made with {a=https://www.renpy.org/}Ren'Py{/a} [renpy.version_only].\n\n[renpy.license!t]"
    new "使用 {a=https://www.renpy.org/}Ren'Py{/a} [renpy.version_only] 制作。\n\n[renpy.license!t]"

    ## 帮助页 ################################################################
    old "Keyboard"
    new "键盘"

    old "Mouse"
    new "鼠标"

    old "Gamepad"
    new "手柄"

    old "Enter"
    new "回车"

    old "Space"
    new "空格"

    old "Arrow Keys"
    new "方向键"

    old "Escape"
    new "Esc"

    old "Ctrl"
    new "Ctrl"

    old "Tab"
    new "Tab"

    old "Page Up"
    new "Page Up"

    old "Page Down"
    new "Page Down"

    old "Left Click"
    new "左键"

    old "Middle Click"
    new "中键"

    old "Right Click"
    new "右键"

    old "Mouse Wheel Up"
    new "滚轮上"

    old "Mouse Wheel Down"
    new "滚轮下"

    old "Right Trigger\nA/Bottom Button"
    new "右扳机 / A 键"

    old "Left Trigger\nLeft Shoulder"
    new "左扳机 / 左肩键"

    old "Right Shoulder"
    new "右肩键"

    old "D-Pad, Sticks"
    new "十字键 / 摇杆"

    old "Start, Guide, B/Right Button"
    new "Start / Guide / B 键"

    old "Y/Top Button"
    new "Y 键"

    old "Calibrate"
    new "校准"

    old "Advances dialogue and activates the interface."
    new "推进对白，并操作界面。"

    old "Advances dialogue without selecting choices."
    new "推进对白，但不选择选项。"

    old "Skips dialogue while held down."
    new "按住可快速跳过对白。"

    old "Toggles dialogue skipping."
    new "开关快进。"

    old "Rolls back to earlier dialogue."
    new "回到之前的对白。"

    old "Rolls forward to later dialogue."
    new "跳回之后的对白。"

    old "Accesses the game menu."
    new "打开游戏菜单。"

    old "Navigate the interface."
    new "在界面中移动。"

    old "Takes a screenshot."
    new "截图。"

    old "Hides the user interface."
    new "隐藏界面。"

    old "Toggles assistive {a=https://www.renpy.org/l/voicing}self-voicing{/a}."
    new "开关{a=https://www.renpy.org/l/voicing}辅助朗读{/a}。"

    old "Opens the accessibility menu."
    new "打开无障碍菜单。"

    old "Menu"
    new "菜单"
