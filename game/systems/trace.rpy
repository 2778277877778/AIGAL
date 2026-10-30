################################################################################
## systems/trace.rpy —— 一次运行的只读轨迹（给「变／不变」的五条断言共用）
##
## 只记三样东西：beat 顺序、Flag 集合、结局 id。
## 不记台词、不记数值、不记 AI 来源——这三样正是「神不散」要比对的部分。
##
## 写入点只有三个：director.run()（拍）、set_flag()（Flag）、ending_gate（结局）。
## 剧本和测试都读 trace_digest()，不要各自再遍历一遍。
## 同一存档回滚时 story_trace 跟着 store 一起回滚，所以轨迹和存档始终一致。
################################################################################

init -1 python:

    def trace_reset():
        """新开一局时清空；读档不清（轨迹跟着存档走）。"""
        store.story_trace = {"beats": [], "flags": [], "ending": ""}


    def trace_beat(beat_id):
        """director.run() 每取一拍记一次。"""
        if not beat_id:
            return
        store.story_trace["beats"].append(str(beat_id))


    def trace_flag(name):
        """set_flag() 每置位一次记一次；重复置位只记一条。"""
        flags = store.story_trace["flags"]
        if name not in flags:
            flags.append(name)


    def trace_ending(ending_id):
        """ending_gate 定下走哪一版结局时记一次。"""
        store.story_trace["ending"] = str(ending_id)


    def trace_digest():
        """(beat 序列, 排好序的 Flag 集合, 结局 id) —— 直接比对用。"""
        t = store.story_trace
        return (tuple(t["beats"]), tuple(sorted(t["flags"])), t["ending"])


    def trace_snapshot():
        """可读副本，调试/日志用；测试请用 trace_digest()。"""
        t = store.story_trace
        return {"beats": list(t["beats"]), "flags": list(t["flags"]), "ending": t["ending"]}


## 存档状态 ####################################################################

default story_trace = {"beats": [], "flags": [], "ending": ""}
