################################################################################
## AI 层接口（M1）
##
## 三层：schema（校验）→ provider（传输）→ cache（缓存）。
## director 还没写，写的时候只调这张表里的东西，不要自己起线程、不要自己拼 key。
################################################################################

一、schema.rpy ← 校验、清洗、beat 白名单（coding检查）
    ai_ctx(beat_id, actions=None, speakers=None, expect_choices=None) -> ctx
    ai_validate(raw, ctx) -> {ok, reason, notes, lines, choices, flags, mood, raw_len}
        传原始正文（字符串），传 ctx。ok=False 时 director 走模板降级。
    ai_render(text) / ai_say(lines) / ai_apply_flags(flags, ctx) / ai_log(msg)
    AI_BEATS / ai_beat(beat_id) / ai_require_beat(beat_id)（开发期断言用）

二、provider.rpy ← 传输、线程、超时、熔断（coding）
    start_http(url, headers, body_json, tag="") -> int
        返回 0 表示没发出去：离线、或 Ctrl 跳过中（只读缓存/模板）。
        回来的正文已经剥过 OpenAI 外壳（choices[0].message.content）。
    start_fake(mode, delay=2.0, tag="") -> int
        假请求。dev.ps1 test 和故障矩阵用它，不受熔断/跳过限制。
        mode: ok / slow / badjson / empty_choices / long_text /
              inject_tags / inject_interp / timeout / http500
    wait(jid, timeout=None, tick=None, blocking=False) -> dict
        {id, tag, state, text, error, elapsed}
        state: done / error / timeout / cancelled / missing
        timeout 默认 12.0s（硬超时）；到点标 timeout 并返回，不卡游戏。
        tick(elapsed_seconds) 每轮回调，给「生成中…」用。
        blocking=True 是测试专用（time.sleep 轮询，不产生交互）。
    result(jid) / cancel(jid) / cancel_all() / clear_jobs()
    online() / allowed() / reset_circuit() / status()
    TIMEOUT = 12.0

三、cache.rpy ← 双层缓存、seed（coding）
    seed_for(beat_id, choice_path="") -> int
        第一次给这拍掷一个并存进存档；回滚/读档后重进拿到同一个。
    key(beat_id, seed, choice_path="", turn=None) -> str
        前缀固定来自 schema_core.cache_prefix()（现在是 s1|角色_v1），
        后接 turn | beat_id | seed | choice_path。
    get(k) -> str | None      ai_cache 优先，persistent.ai_seen 兜底
    has(k) / put(k, text, persist=True) / forget(k) / stats() / clear_persistent()

四、不变量（改这里之前先看小组记忆）
    1. Job 对象不进 store。对外只给 int id；id 是「会话基址 + 序号」，
       读档后查不到就是 missing，不抛 KeyError。
    2. 线程里不调任何 renpy API。结果只写 Job 字段，主线程取完再落缓存。
    3. 缓存只在主线程写。put() 不要在线程里调。
    4. 12.0s 是 provider 的硬超时。8s 软降级归 director，是第二个计时器。
    5. store.ai_log 是 schema 的日志函数；缓存字典叫 store.ai_cache。

五、跑测试
    .\dev.ps1 test            # 全部套件
    .\dev.ps1 test ai_layer   # 只跑 provider/cache 这 8 个 case
    熔断会在连 3 次 error/timeout 后转离线，测试 case 开头都调 reset_circuit()。
