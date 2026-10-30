################################################################################
## ai/provider.rpy —— 传输层：把一次请求丢到独立线程，主线程轮询/超时/熔断。
##
## 这层只管「把一句话送到端点、把助手正文拿回来」，不认识 beat、不碰数值、
## 不碰 Flag。校验在 schema，缓存和 key 在 cache，剧本调用在 director。
##
## 三条硬约束（来自小组记忆里的 AI 线程条目，改动前先读一遍）：
##   1. Job 对象绝不进 store。存档会 pickle 它，直接报 cannot pickle _thread.lock。
##      对外只暴露 int id，表放在本命名空间里（init 时建，不进存档、不参与回滚）。
##   2. 运行期只改内容，不重新绑定模块级名字（_JOBS / _STATE / _NEXT …）。
##      一旦重绑，名字进入 ever_been_changed，就会开始被存档跟踪。
##   3. 线程里不调任何 renpy API，连 renpy.notify 都不行。只用纯 Python 写结果。
##
## 平台说明：renpy.invoke_in_thread 在 web 上直接返回、不起线程。web 构建要改用
## renpy.fetch（同步、内部会 renpy.pause），这一版不做。
################################################################################

init -6 python in aig:

    import json
    import threading
    import time

    ## 单次请求的硬超时。requests 的 timeout 只管单次读，整体还要靠 wait() 的 deadline 兜。
    TIMEOUT = 12.0

    ## 连续失败几次转离线（本会话有效，不落盘）。
    FAIL_LIMIT = 3

    _LOCK = threading.RLock()
    _JOBS = {}
    _NEXT = [0]

    ## 会话基址：id = 基址 + 序号。读档后存档里那个 id 是本会话之前的，查不到就是查不到，
    ## 不会撞上新建的 Job（跨进程重启时序号会从头开始，靠基址拉开）。
    _BASE = (int(time.time() * 1000) % 10 ** 9) * 1000

    _STATE = {
        "consec_fail": 0,
        "offline": False,
        "requests": 0,
        "fails": 0,
        "fake": None,
    }

    FAKE_MODES = (
        "ok", "badjson", "empty_choices", "long_text",
        "inject_tags", "inject_interp", "timeout", "http500",
    )

    class Job(object):
        """一次在飞请求。只活在 _JOBS 里，永远不进 store。"""

        ## 不写 __slots__：带 slots 的类在这个命名空间里定义时，Ren'Py 的 rollback
        ## 包装会直接抛 TypeError（slots 类不支持 rollback）。Job 本来也不进 store。
        def __init__(self, jid, tag):
            self.id = jid
            self.tag = tag
            self.state = "running"      # running / done / error / timeout / cancelled
            self.text = None
            self.error = None
            self.started = time.time()
            self.ended = None
            self.abandoned = False

    ## 内部：任务表 ################################################################

    def _new_job(tag, id_=None):
        with _LOCK:
            _NEXT[0] += 1
            jid = _BASE + _NEXT[0] if id_ is None else id_
            job = Job(jid, tag)
            _JOBS[jid] = job
            _STATE["requests"] += 1
            return job

    def _job(jid):
        if not isinstance(jid, int):
            return None
        with _LOCK:
            return _JOBS.get(jid)

    def _finish(job, state, text=None, error=None):
        """线程里调用。只碰 Job 自己的字段，不碰 renpy。"""
        with _LOCK:
            if job.abandoned:
                return
            job.state = state
            job.text = text
            job.error = error
            job.ended = time.time()
            if state == "error":
                _STATE["fails"] += 1
                _STATE["consec_fail"] += 1
                if _STATE["consec_fail"] >= FAIL_LIMIT:
                    _STATE["offline"] = True
            elif state == "done":
                _STATE["consec_fail"] = 0
        # 走到这里不用 renpy.restart_interaction：invoke_in_thread 在线程返回时会自己重启交互。

    def _abandon(job, state="timeout"):
        with _LOCK:
            if job.state != "running":
                return
            job.abandoned = True
            job.state = state
            job.ended = time.time()
            if state == "timeout":
                _STATE["fails"] += 1
                _STATE["consec_fail"] += 1
                if _STATE["consec_fail"] >= FAIL_LIMIT:
                    _STATE["offline"] = True

    def _spawn(target, job):
        try:
            renpy.invoke_in_thread(target, job)
        except Exception as e:
            _finish(job, "error", None, "无法启动线程：%s" % e)

    ## 对外：状态 ##################################################################

    def online():
        return not _STATE["offline"]

    def allowed():
        """能不能现在发现场请求：离线、Ctrl 跳过时都不行（跳过时只读缓存/模板）。"""
        if _STATE["offline"]:
            return False
        try:
            if renpy.config.skipping:
                return False
        except Exception:
            pass
        return True

    def reset_circuit():
        """清熔断。故障矩阵每个 case 前后都该调一次，否则第 4 个 case 开始全离线。"""
        with _LOCK:
            _STATE["consec_fail"] = 0
            _STATE["offline"] = False

    def status():
        with _LOCK:
            running = sum(1 for j in _JOBS.values() if j.state == "running")
            return {
                "online": not _STATE["offline"],
                "consec_fail": _STATE["consec_fail"],
                "requests": _STATE["requests"],
                "fails": _STATE["fails"],
                "running": running,
                "jobs": len(_JOBS),
                "fake": _STATE["fake"],
            }

    ## 对外：发起 ##################################################################

    def start_http(url, headers, body_json, tag=""):
        """POST 一个 JSON body，返回 job id。离线 / 跳过中返回 0。"""
        if not allowed():
            return 0
        job = _new_job(tag)

        def run(j):
            try:
                import requests
            except ImportError:
                _finish(j, "error", None, "requests 不可用")
                return
            try:
                data = json.dumps(body_json, ensure_ascii=False).encode("utf-8")
                r = requests.post(url, data=data, headers=headers, timeout=TIMEOUT)
            except Exception as e:
                _finish(j, "error", None, _brief(e))
                return
            if r.status_code != 200:
                _finish(j, "error", None, "HTTP %d" % r.status_code)
                return
            try:
                content = _extract_content(r.text)
            except Exception as e:
                _finish(j, "error", None, _brief(e))
                return
            _finish(j, "done", content, None)

        _spawn(run, job)
        return job.id

    def _extract_content(body):
        """从 OpenAI 兼容响应里取 choices[0].message.content。取不到就抛。"""
        try:
            data = json.loads(body)
            content = data["choices"][0]["message"]["content"]
        except Exception:
            raise ValueError("响应不是 OpenAI 兼容格式")
        if not isinstance(content, str):
            raise ValueError("content 不是字符串")
        return content

    def _brief(e):
        text = "%s: %s" % (type(e).__name__, e)
        return text[:200]

    ## 对外：假 provider（M1 用，故障矩阵靠它）####################################

    ## 返回的是「助手正文」，不是整包 HTTP body —— 和 start_http 的出参口径一致，
    ## 所以 schema 在两个来源上跑的是同一条校验路径。
    FAKE_BODY_OK = (
        '{"lines":[{"speaker":"zm","text":"他把琴谱翻到最后一页，没说话。"}],'
        '"choices":[{"text":"问他为什么","action_key":"ask_zhoumo"},'
        '{"text":"装作没看见","action_key":""}],'
        '"flags":[],"mood":"quiet"}'
    )

    _FAKE_LONGTEXT_LINES = "[" + ",".join(
        '{"speaker":"zm","text":"%s"}' % ("很长的一句话，" * 20)
        for _ in range(6)
    ) + "]"

    _FAKE_BODIES = {
        "ok": FAKE_BODY_OK,
        "slow": FAKE_BODY_OK,
        "badjson": "好的，这是你要的台词：他把琴谱翻到最后一页。",
        "empty_choices": (
            '{"lines":[{"speaker":"zm","text":"……"}],"choices":[],"flags":[],"mood":"quiet"}'
        ),
        "long_text": '{"lines":%s,"choices":[{"text":"继续","action_key":""}],"flags":[],"mood":"quiet"}'
                     % _FAKE_LONGTEXT_LINES,
        "inject_tags": (
            '{"lines":[{"speaker":"zm","text":"{image=bg room}{nw}别过来"}],'
            '"choices":[{"text":"退后","action_key":""}],"flags":[],"mood":"tense"}'
        ),
        "inject_interp": (
            '{"lines":[{"speaker":"zm","text":"[persistent.api_key] 你看"}],'
            '"choices":[{"text":"……","action_key":""}],"flags":[],"mood":"quiet"}'
        ),
    }

    def start_fake(mode="ok", delay=2.0, tag=""):
        """假请求：sleep(delay) 后返回预设正文。mode 见 FAKE_MODES。

        不受 allowed() 限制 —— 测试要能在「离线」「跳过」状态下也能造出结果。
        """
        if mode not in FAKE_MODES:
            mode = "ok"
        _STATE["fake"] = mode
        job = _new_job(tag)

        def run(j):
            time.sleep(max(0.0, delay))
            if mode == "timeout":
                return                      # 一直不结束，靠 wait() 的 deadline 判超时
            if mode == "http500":
                _finish(j, "error", None, "HTTP 500")
                return
            _finish(j, "done", _FAKE_BODIES.get(mode, FAKE_BODY_OK), None)

        _spawn(run, job)
        return job.id

    ## 对外：取结果 ################################################################

    def result(jid):
        job = _job(jid)
        if job is None:
            ## 读档 / 重启后存档里那个 id 找不到：当作「没开始过」，调用方走缓存或降级。
            return {"id": jid, "state": "missing", "text": None,
                    "error": "任务已失效（读档或重启后）", "elapsed": 0.0}
        with _LOCK:
            return {
                "id": job.id,
                "tag": job.tag,
                "state": job.state,
                "text": job.text,
                "error": job.error,
                "elapsed": (job.ended or time.time()) - job.started,
            }

    def wait(jid, timeout=None, tick=None, blocking=False):
        """主线程等结果。返回 result() 的字典型。

        timeout  总时限，默认 TIMEOUT。到点把任务标 timeout 并返回，不阻塞游戏。
        tick     每轮回调一次，参数是已等待秒数。前端拿它更新「生成中…」的进度。
        blocking 测试专用：用 time.sleep 轮询，不产生交互（testcase 里没有界面循环）。
        """
        if timeout is None:
            timeout = TIMEOUT
        job = _job(jid)
        if job is None:
            return result(jid)

        renpy.block_rollback()      # 生成期间不许回滚，避免留下悬空线程

        deadline = time.time() + timeout
        while True:
            with _LOCK:
                state = job.state
                started = job.started
            if state != "running":
                break
            now = time.time()
            if now >= deadline:
                _abandon(job)
                break
            if tick is not None:
                try:
                    tick(now - started)
                except Exception:
                    pass
            if blocking:
                time.sleep(0.02)
            else:
                renpy.pause(0.05)

        return result(jid)

    ## 对外：收尾 ##################################################################

    def cancel(jid, state="cancelled"):
        job = _job(jid)
        if job is not None:
            _abandon(job, state)
        return job is not None

    def cancel_all():
        with _LOCK:
            jobs = list(_JOBS.values())
        for job in jobs:
            _abandon(job, "cancelled")

    def clear_jobs():
        """把表清空（只清已完成/已放弃的）。测试和 after-load 用。"""
        with _LOCK:
            for jid in [j.id for j in _JOBS.values() if j.state != "running"]:
                del _JOBS[jid]


## 退游戏时把在飞的都掐掉，不留 daemon 线程做请求。
## 放在 -1：保证 aig 命名空间里的函数都已经定义完。
init -1 python:
    config.quit_callbacks.append(aig.cancel_all)
