################################################################################
## ai/cache.rpy —— 缓存层：同一拍的内容只买一次。
##
## 两层，优先级固定 store.ai_cache > persistent.ai_seen：
##   ai_cache    本局已读文本，普通 store 变量，进存档、跟着回滚。
##   ai_seen     跨读档 / 跨回滚的那一份，存 persistent，按字符数封顶做 LRU。
## 顺序不能反：反了会出现「同一存档前后两次读到两版文本」。
##
## key 以 schema_core.cache_prefix() 开头，也就是 (schema_ver, prompt_ver)：
##   schema_ver  改 JSON 契约时 +1，旧缓存自动作废
##   prompt_ver  改提示词时 +1 —— 少了这个，改完 prompt 旧缓存照样命中，还查不出原因
## 后面接 (turn, beat_id, seed, choice_path)。seed 在骨架阶段就掷好并存档
## （见 seed_for），回滚后重进同一拍拿到同一个。
##
## 命名注意：store.ai_log 是 schema.rpy 里的日志函数，别拿来做缓存字典用。
##
## 写入只在主线程做：线程只填 Job，主线程取到结果再落缓存（provider 那层的约束）。
################################################################################

## 本局已生成的文本，key -> 正文。进存档。
default ai_cache = {}

## 每拍的 seed，beat_id|choice_path -> int。进存档，保证回滚/读档后一致。
default ai_seeds = {}


init -5 python in aig:

    import time

    ## persistent.ai_seen 的字符上限。persistent 每次变动全量重写，
    ## 不封顶的话几百条长文本会把文件撑大、存档明显变慢。
    P_CAP = 200000


    ## key #########################################################################

    def _prefix():
        """缓存前缀。唯一来源是 schema_core.cache_prefix()，这里不另存一份版本号。"""
        mod = getattr(renpy.store, "aischema", None)
        if mod is not None:
            try:
                return mod.cache_prefix()
            except Exception:
                pass
        ## schema.rpy 的导入还没发生时（几乎只在 init -5 期间的极端情况）用等价兜底。
        return "s%s|%s" % (
            getattr(renpy.store, "AI_SCHEMA_VER", 1),
            getattr(renpy.store, "AI_PROMPT_VER", "0"),
        )

    def key(beat_id, seed, choice_path="", turn=None):
        if turn is None:
            turn = renpy.store.turn
        return "%s|%d|%s|%d|%s" % (_prefix(), turn, beat_id, seed, choice_path)

    def seed_for(beat_id, choice_path=""):
        """取这一拍的 seed；没有就掷一个存进存档。回滚后重进同一拍结果不变。"""
        k = "%s|%s" % (beat_id, choice_path)
        seeds = renpy.store.ai_seeds
        if k in seeds:
            return seeds[k]
        s = renpy.random.randint(1, 2 ** 31 - 1)
        ## 重建而不是就地改：不赌 RevertableDict 的原地修改语义。
        renpy.store.ai_seeds = dict(seeds, **{k: s})
        return s


    ## 读 ##########################################################################

    def _seen():
        seen = getattr(renpy.game.persistent, "ai_seen", None)
        if seen is None:
            seen = {}
            renpy.game.persistent.ai_seen = seen
        return seen

    def get(k):
        """命中返回正文，没有返回 None。ai_cache 优先。"""
        log = renpy.store.ai_cache
        if k in log:
            return log[k]
        row = _seen().get(k)
        if row:
            return row[0]
        return None

    def has(k):
        return get(k) is not None


    ## 写 ##########################################################################

    def put(k, text, persist=True):
        """主线程调用。写两层：本局存档一份，persistent 备份一份。"""
        if not isinstance(text, str) or not text:
            return False
        renpy.store.ai_cache = dict(renpy.store.ai_cache, **{k: text})
        if persist:
            _put_seen(k, text)
        return True

    def _put_seen(k, text):
        seen = _seen()
        seen[k] = [text, time.time()]
        total = sum(len(row[0]) for row in seen.values())
        if total <= P_CAP:
            return
        ## 超了就从最旧的开始淘汰，直到回到上限以下。
        for old in sorted(seen, key=lambda kk: seen[kk][1]):
            if total <= P_CAP:
                break
            total -= len(seen[old][0])
            del seen[old]


    ## 运维 ########################################################################

    def stats():
        log = renpy.store.ai_cache
        seen = _seen()
        return {
            "session_entries": len(log),
            "session_chars": sum(len(v) for v in log.values()),
            "persist_entries": len(seen),
            "persist_chars": sum(len(row[0]) for row in seen.values()),
            "persist_cap": P_CAP,
            "prefix": _prefix(),
        }

    def forget(k):
        """删一条（两层都删）。"""
        if k in renpy.store.ai_cache:
            log = dict(renpy.store.ai_cache)
            del log[k]
            renpy.store.ai_cache = log
        seen = _seen()
        if k in seen:
            del seen[k]

    def clear_persistent():
        renpy.game.persistent.ai_seen = {}
