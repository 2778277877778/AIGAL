################################################################################
## ui_pages.rpy —— 对白分页（结局正文用）
##
## 为什么需要：ending 契约允许 200 字 / 条（schema_core.ENDING_LINE_MAX），
## 而对白框实测只能放约 124 字（每行 31 字 × 4 行，见美工的量测）。结局走的是
## 同一条 ai_say → renpy.say → screen say，框里没有滚动，超出的部分直接画出框外、
## 且测试不会报 —— 那恰好是全剧最后一段文字。
##
## 所以不改契约、不改 UI、不改文案写法：把一条长台词按标点切成若干页，
## 同一个 speaker 连着说。1000 字 ≈ 9–10 屏，读起来也更像结尾。
##
## 接法（schema.rpy 的 ai_say，已接）：pieces = page_text(txt, SAY_PAGE_MAX)
##
## 规则（Chief 定稿的四条，改这里之前先看一遍）：
##   1. 每页 ≤ 100 字（版面安全线，不是 124）；
##   2. 先切 。！？… ，其次 ，、； ，都不行才硬切；不在句子中间切，宁可这页短；
##   3. 碎片页（< 10 字）并进上一页，别让玩家读到一页只有两个字；
##   4. 页间不加任何提示（不插「（继续）」、不插省略号），连着说。
################################################################################

init -1 python:

    ## 兜底值：正常情况下用 schema.rpy 的 SAY_PAGE_MAX（单一来源），取不到才用这个。
    SAY_SAFE_CHARS = 100

    ## 规则 3 的下限。合并后最长 100+9 = 109，仍在 124 的物理上限内。
    SAY_FRAGMENT_MIN = 10

    ## 规则 2 的优先级：先在句末断，其次句内断。
    SAY_BREAK_STRONG = "。！？!?…‥"
    SAY_BREAK_WEAK = "，、；：,;:—～"

    def _page_limit(limit=None):
        if limit is not None:
            try:
                return max(20, int(limit))
            except Exception:
                return SAY_SAFE_CHARS
        try:
            return max(20, int(SAY_PAGE_MAX))
        except Exception:
            return SAY_SAFE_CHARS

    def page_text(text, limit=None):
        """把一条长台词切成若干页。返回字符串列表；原文为空返回空列表。

        不丢字、不重排：拼起来等于原文（只去掉各页首尾空白）。
        """
        limit = _page_limit(limit)
        text = (text or "")
        if not text.strip():
            return []
        if len(text) <= limit:
            return [text.strip()]

        pages = []
        buf = ""
        for ch in text:
            buf += ch
            if len(buf) < limit:
                continue
            ## 到量了：先找句末标点，其次句内标点，都没有就硬切。
            ## 回看窗口取 limit//3：再往前找会把这一页切得太短，反而不像一句话。
            cut = -1
            back = max(0, len(buf) - limit // 3)
            for i in range(len(buf) - 1, back - 1, -1):
                if buf[i] in SAY_BREAK_STRONG:
                    cut = i + 1
                    break
            if cut < 0:
                for i in range(len(buf) - 1, -1, -1):
                    if buf[i] in SAY_BREAK_WEAK:
                        cut = i + 1
                        break
            if cut < 0:
                cut = len(buf)
            pages.append(buf[:cut])
            buf = buf[cut:]
        if buf.strip():
            pages.append(buf)

        ## 规则 3：碎片页并进上一页
        merged = []
        for piece in pages:
            piece = piece.strip()
            if not piece:
                continue
            if merged and len(piece) < SAY_FRAGMENT_MIN:
                merged[-1] = merged[-1] + piece
            else:
                merged.append(piece)
        return merged
