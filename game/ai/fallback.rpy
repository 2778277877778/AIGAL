################################################################################
## ai/fallback.rpy —— 本地模板库（降级文本）。
##
## 这一层的存在意义：没 key、断网、超时、模型连续两次输出不合格时，游戏必须还能玩，
## 而且是「像样的文本」，不是一句报错。
##
## 形状（和 ai_validate 的返回同构，剧本层不用区分来源）：
##   "t2_piano": {
##       "lines":   [{"speaker": "zm", "text": "……"}],   # 3–5 行，每行 40–60 字
##       "choices": [{"text": "……", "action_key": "study"}],  # action_key 必须 ∈ ACTIONS
##       "mood":    "quiet",
##   }
##
## 规则（跟 prompt 里的长度预算对齐，不然降级版和 AI 版观感差太多）：
##   - 3–5 行，每行 40–60 字，合计 200–250 字
##   - 最后一行留给旁白收尾
##   - action_key 只能填 ACTIONS 里有的 key，或者空字符串（表示这一项不触发行动）
##
## 文案策划按这张形状填，coding 不改文本。
################################################################################

init -4 python in aig:

    FALLBACK = {}

    ## 撑不住时的最后一道：一句中性占位，绝不编剧情。
    _EMPTY_TEMPLATE = {
        "lines": [
            {"speaker": "inner", "text": "这一段先走本地文本。"},
            {"speaker": "inner", "text": "（需要在 ai/fallback.rpy 里给这一拍补一条模板。）"},
        ],
        "choices": [],
        "mood": "",
    }

    def template(beat_id):
        t = FALLBACK.get(beat_id)
        if t:
            return t
        return _EMPTY_TEMPLATE
