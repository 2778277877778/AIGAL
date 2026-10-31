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

        两个数字要分清（README 也这么写）：
          - 目标每页 ≤ limit（100）；
          - 规则 3 合并碎片后允许到 109（100 + 9），这是设计上限，不是 bug；
          - 124 是版面物理上限，109 < 124，所以合并后不会画出框。
        """
        limit = _page_limit(limit)
        text = (text or "")
        if not text.strip():
            return []
        total = len(text)
        if total <= limit:
            return [text.strip()]

        min_len = max(1, min(SAY_FRAGMENT_MIN, limit // 2))
        pieces = []
        i = 0
        while i < total:
            if total - i <= limit:        # 剩下的放得下，收尾
                pieces.append(text[i:])
                break

            window_end = i + limit
            ## 窗口内最短可接受的切点：切完这一页不足 min_len 就不要这个标点，
            ## 否则句号挨在开头会切出一页两三个字（美工量出来的头部碎片）。
            floor = i + min_len - 1
            cut = -1
            ## 规则 2：先在句末标点后切 —— 整个窗口都看，不只最后 1/3。
            ## 只看最后 1/3 时，「句号在第 41 字」会被无视，结果硬切在句子中间。
            for k in range(window_end - 1, floor - 1, -1):
                if text[k] in SAY_BREAK_STRONG:
                    cut = k + 1
                    break
            if cut < 0:
                for k in range(window_end - 1, floor - 1, -1):
                    if text[k] in SAY_BREAK_WEAK:
                        cut = k + 1
                        break
            if cut < 0:
                cut = limit               # 一整段没有标点：硬切（兜底，正常不该走到）

            pieces.append(text[i:i + cut])
            i += cut

        ## 规则 3：碎片页合并。头一页就是碎片时没有上一页可并，先攒着拼到下一页前面。
        out = []
        carry = ""
        for piece in pieces:
            if carry:
                piece = carry + piece
                carry = ""
            if not piece.strip():
                continue
            if len(piece.strip()) < min_len:
                if out:
                    out[-1] = out[-1] + piece        # 并进上一页（尾部碎片）
                else:
                    carry = piece                    # 第一页就是碎片：留给下一页
                continue
            out.append(piece)
        if carry:
            if out:
                out[-1] = out[-1] + carry
            else:
                out.append(carry)

        return [p.strip() for p in out if p.strip()]
