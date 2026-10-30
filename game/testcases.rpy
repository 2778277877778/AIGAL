################################################################################
## 冒烟自测（Ren'Py testcase）
##
## 用法：
##   ... renpy.py "<工程路径>" test
##
## 现在只覆盖「主菜单 → 开始 → 推进几句 T1 台词」。T1 接进来以后开局就不回主菜单了，
## 菜单页（设置 / 关于 / 帮助）那几条等 campus_map 做完再补回来。
##
## 两个踩过的坑：
## 1. 对白最后一句别用 advance —— 脚本 return 回主菜单后没有可推进的对象，会等到超时；
##    改点文本更稳。
## 2. 勾选类按钮（未读文字 / 选项之后 / 转场）的测试文本还是英文，
##    要用 "Unseen Text" 这种旧名字才点得到；导航按钮用中文没问题。
################################################################################

testsuite global:
    teardown:
        exit

testcase smoke:
    $ _test.transition_timeout = 0.05

    click "开始"
    pause .8

    advance
    advance
    advance
    pause .3


## AI 契约自测：beat 表 / turn 断言 / 主角名清洗。不联网、不需要 API key。
## 纯数据的 12 项故障矩阵在 tools/selftest_schema.py，用系统 Python 跑。
##
## 刻意不点「开始」：这条用例跑在 smoke 之后，游戏已经进了剧本，
## 主菜单的按钮早没了。turn 自己摆好再还原，跟前面用例的顺序无关。
testcase ai_contract:
    $ _test.transition_timeout = 0.05

    pause .3

    python:
        _saved_turn = getattr(store, "turn", 1)
        store.turn = 1
        try:
            ## T1 的拍能和当前回合对上
            assert ai_require_beat("t1_report")["turn"] == 1, "t1_report 的 turn 不对"

            ## 跨回合的拍必须被挡下来：T1 的流程里不该出现 T2 的拍
            assert ai_beat_ok("t2_piano")[0] is False, "T1 里放行了 T2 的拍"

            ## 未登记的 beat 要报出名字，不能静默返回 None 让上层崩在渲染时
            assert ai_beat_ok("t9_final")[0] is False, "未登记的 beat 没被拦"

            ## 自由行动段按需合成，T1..T8 每个月都得有
            for _n in range(1, 9):
                assert ai_beat("t%d_free" % _n) is not None, "t%d_free 没合成出来" % _n

            ## 本拍 flag 白名单为空：终结/告白这类判定链 flag 不许 AI 置位
            assert ai_ctx("t1_free")["flags"] == (), "t1_free 的 flag 白名单不是空的"

            ## 玩家可以把名字填成标签，渲染时也必须洗掉
            _saved_name = getattr(store, "player_name", None)
            store.player_name = "{image=bg room}阿明[persistent.api_key]<b>"
            _rendered = ai_render("叫我" + AI_NAME_TOKEN + "……")
            assert not (set(_rendered) & set("{}[]<>")), "主角名把标记带进了正文：%r" % _rendered
            assert "阿明" in _rendered, "真名被洗掉了：%r" % _rendered

            ## 清洗是幂等的：同一句渲染两次结果一样
            assert ai_render(_rendered) == _rendered, "ai_render 不幂等"

            store.player_name = _saved_name
        finally:
            store.turn = _saved_turn
