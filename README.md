# AIGAL

> 派生自 [2778277877778/gal](https://github.com/2778277877778/gal)，沿用原仓库的 MIT 许可（见[许可](#许可)）。原仓库「高中校园物语」的提交历史整份保留。
>
> 当前版本 `0.2.0`（2026-10-31）。更新记录见 [CHANGELOG.md](CHANGELOG.md)。

Ren'Py 校园视觉小说，带日程数值，简体中文，13+，首版只做 Windows。一局 60–90 分钟。走三年 36 个月格：30 个完整回合加 6 个暑假短过场，三位女主三条线，5 个结局。无内购，API key 玩家自己填，钱也他自己出。

原版是固定剧本。这一版把台词那层交给 AI 现场写，骨架不动：哪个月发生哪件事、有几个选项、Flag 怎么置，全在脚本里。玩家每局读到的台词不一样，走的线和到达的结局还是那几个。

游戏本体暂时还叫「高中校园物语」（`config.name`），仓库名是 AIGAL。结构以[剧情大纲_三年_v1.md](高中校园物语/剧情大纲_三年_v1.md) 为准，数字以[运行时预算_v1.md](高中校园物语/运行时预算_v1.md) 为准。

先说清楚四件事：

- 不是聊天机器人。没有输入框，玩家仍旧从有限选项里选。
- 不把剧本整份交给模型。模型能写数值，多结局就不可控了。
- 立绘和背景本期不做，用纯色占位，后期一次性补。
- 「UI 一样」说的是剧情画面：菜单页多一栏 AI 设置，等请求或降级时多一层临时浮层，其余逐像素不变。倍率、窗口、文本框都没动。

## 硬约束

冲突时按序号来。

1. 数值、Flag、考试、结局只走 `game/systems/stats.rpy`。AI 的输出里没有数值字段，有也不认。
2. AI 只写台词。选项从脚本的 `BEAT_CHOICES` 拿，Flag 由脚本 `set_flag` 置，这两样不由模型产出。
3. 骨架写死，台词随机。里程碑钉在固定窗口里，窗口内没满足就顺延，过了窗口就作废、奖励并进该线的 END，不卡主线。随机只发生在怎么说，以及随机事件抽到哪一个。
4. 没有 key 也能通关。本地模板库覆盖全流程，不当兜底补丁用。
5. AI 出来的文本当外部输入，不清洗不许进 `say`。网页上能塞的东西，模型也能塞。
6. 任何逻辑都不依赖立绘和背景，占位图得能跑完全程。

## 进度

能玩的：从开局一路到结局。T1–T36 的 label 都通了，五个结局都能走到（TRUE 加周墨 / 夏幸悠 / 温以宁 / 无路线四条），T22 锁线，T34 高考，T35 查分。T1 全手写，一次 AI 都不调；T2 往后走 director。T9–T36 目前是骨架：格子、里程碑、事件槽都排好了，正文没写。

判定与关系：数值和结局归 `game/systems/stats.rpy`，关系变量在 `relations.rpy`（`rel_zm` / `rel_xia` / `rel_x`，只加不减，`stage` 由已达成的里程碑数算出，不单独存）。TRUE 的门槛是高考 ≥85、压力 ≤60、`rel_zm` ≥60、10 个 Flag。

AI 层，`game/ai/` 下这些都在跑：

| 文件 | 管什么 |
|---|---|
| `provider.rpy` | HTTP 请求、线程、超时、熔断、并发上限 2、延迟 P50/P95、任务表回收 |
| `director.rpy` | 拼提示词、缓存、预取、重试、8 秒软降级 |
| `cache.rpy` | `store.ai_log` 与 `persistent.ai_seen` 两级缓存 |
| `schema.rpy` | 拍表 `BEATS`、输出校验、speaker 与 Flag 白名单、长文分页接线 |
| `fallback.rpy` | 无 key 时的模板库，以及每拍的选项表 `BEAT_CHOICES` |
| `prompts.rpy` / `prompts_data.rpy` | 提示词数据，由 `tests/build_prompts.py` 从大纲生成 |
| `settings.rpy` / `settings_screen.rpy` | key 存储、端点预设、测试连接、诊断页 |
| `api.md` | 请求与返回格式、错误码 |

校验的真身在 `game/python-packages/aigal/schema_core.py`，纯 Python，可以单独跑。

测试：现在 67 条用例全过，`check_cards` 和 lint 都在链里。其中 `story_graph` 静态核对所有 `jump` / `call` 的目标都存在、从 `start` 能走到 `ending_gate`，`smoke_deep` 从主菜单走到 T2，`beat_coverage` 逐拍跑假请求，`milestone_wiring` 核里程碑挂点，`every_beat_has_speakers` 挡住漏登记 speaker 的静默降级。

还没验的只有一件：真模型。前面所有用例证明的都是「假 provider 下成立」。真模型守不守 JSON、字数和 speaker 白名单，返回能不能在 12 秒内到，中文读着像不像人写的，只有真请求能回答。

## AI 输出

模型写台词，不写选项和 Flag：

```json
{
  "lines": [{"speaker": "zm", "text": "……不许说出去。"}],
  "mood": "quiet"
}
```

- `speaker` 只能是 `mc / zm / zzb / zeng / stu_a / stu_b / bro / xia / kong / x / zm_dad / zm_mom / inner / nar`，还要真的 define 过，没 define 的行直接剔。目前 13 个 id 全部已 define。
- 一拍最多 5 行，单行 80 字以内（120 是兜底），整拍目标 250 字、上限 400 字。这是版面约束不是文风建议：`gui.scale` 是 1.5 倍，实际 36px 字、1116px 宽、四行，每行 31 字，124 字是零余量的天花板；避头尾规则会把末字挤到第五行，所以安全线取 100。压到画面上 Ren'Py 不裁切，也不会报错。
- 结局正文单独一套预算：单条 200 字、整篇 1000 字（`ENDING_LINE_MAX` / `ENDING_TOTAL_MAX`）。一屏只放得下 124 字，两者之间靠分页补：`ui_pages.rpy` 的 `page_text()` 目标每页不超过 100 字，碎片并进上一页后最多 109；先按 `。！？…` 断，其次 `，、；`，最后硬切，切点不短于 10 字，不在句子中间切。分页只给结局用，拍内不接——拍内单行本来就压在 100 字以内，真要翻页说明那一行该砍，不该加页。
- 1.5 秒才浮出生成中界面，8 秒软降级走模板，12 秒硬熔断。下一拍预取，命中就没有等待。
- 提示词只喂事实清单（谁在场、必须发生什么，最多 3 条），不喂范文台词。给范文，模型只会做同义改写，两局读起来就成了同一段。
- `SCHEMA_VER` 是 4。协议升版时缓存全部作废，改完第一次跑会明显慢。

`choices` / `flags` 已经从契约里摘掉。模型多给了这两个字段、类型又不对，只丢字段记一条 note，不连坐正文——`lines` 合法就照用。

## 接一把真 key

这是唯一没走过的路。跑法：

1. `.\dev.ps1 run` 启动，进设置页填 `base_url` / `model` / `key`，点「测试连接」。
2. 开新游戏，玩到 T2 旧琴房那一拍。这一拍会真的发请求。
3. 第一遍每拍 5–10 秒是正常的（`SCHEMA_VER = 4` 让旧缓存全废，每拍都是现场请求）。

key 有三种来源，优先级是**本次会话 > 环境变量 `AIGAL_API_KEY` > 落盘配置**。设置页填的默认存 `persistent`，明文落盘，界面上会照实提示；也可以选「仅本次会话」，只在内存里，重启要重填；无头测试或临时换 key 就直接设环境变量，它压过落盘值，也不会被写回存档——切存法时只搬内存和落盘里的 key，环境变量那份不碰。

设置页会显示当前这把 key 从哪来：掩码加一行来源（本次会话 / 环境变量 / 已保存的配置），诊断页也有同样一行。所以设了环境变量却以为没生效这种误会，在界面上就能自己排除。内部标识看 `key_source()`（`session` / `env` / `persistent` / 空），给人看的文案在 `key_source_text()`。

key 不进日志、不进仓库。日志里一律打码，请求体只留长度和前 200 字。

## 运行

需要 Ren'Py 8.5.3 SDK，解压版就行，不用装进系统。SDK 自带 Python 3.12，别的都不用装，详见[依赖.md](依赖.md)。

`dev.ps1` 会把 SDK 路径、命令和参数都处理掉：

```powershell
.\dev.ps1 run          # 启动游戏
.\dev.ps1 lint         # 提交前检查
.\dev.ps1 test         # 冒烟与 AI 用例
.\dev.ps1 diversity    # 台词差异报告，逐拍打印抽到的细节
.\dev.ps1 compile      # 生成 .rpyc
.\dev.ps1 shots        # 截图比对，改过版式先跑 shots overwrite
.\dev.ps1 distribute   # 打开启动器，打包要手点（见下）
```

打包没有命令行入口。Ren'Py 8.5.3 注册的 CLI 命令只有 `run` / `lint` / `compile` / `rmpersistent` / `quit`，构建逻辑在启动器的 `Distributor` 里，只有 GUI 能驱动。所以 `dev.ps1 distribute` 只是把启动器打开，真正构建要自己在 Build Distributions 里勾 Windows 再点 Build，产物落在 `dist/`。

**本项目还没有实际构建验证过**：一次都没成功打出过包，产物也没在没装 SDK 的机器上试过。等真做一次、确认能跑，再把这句改成事实。`project.json` 现在是 `normal`，否则启动器项目列表里根本看不到这个仓库。

不用 `dev.ps1` 时，`<SDK>` 是 SDK 目录，`<仓库>` 是仓库根目录：

```powershell
"<SDK>\renpy.exe" "<仓库>"
"<SDK>\lib\py3-windows-x86_64\python.exe" renpy.py "<仓库>" lint
```

环境细节、沙箱里的存档目录设置、数值系统的函数说明，都在[开发环境说明.md](开发环境说明.md)。

一台机器同时只跑一个 Ren'Py 实例。`log.txt`、`saves/`、`persistent` 都是共享的，两个实例撞上会互相打断，写出成堆的假失败。要并发验证，先等 `dev.ps1` 的锁。

不联网也能玩：无 key 或无网时全部走模板库。接上 key 之后调 OpenAI 兼容端点，`base_url` / `model` / `key` / `temperature` / `timeout` 都可配。

## 目录

```
game/
  script.rpy        入口
  options.rpy       标题、版本、存档目录
  gui.rpy           GUI 变量（1920×1080）
  screens.rpy       默认界面，设置页里有 AI 那一栏
  ui_pages.rpy      长文本分页（结局专用）
  ui_zh.rpy         界面中文化
  ui_theme.rpy      样式微调
  testcases.rpy     冒烟用例
  ai/               AI 四层、模板库、提示词、设置页、诊断
  systems/          stats.rpy 数值与结局判定，relations.rpy 关系，events.rpy 事件抽取，replay.rpy 轨迹，trace.rpy 打点
  story/            characters、T1–T8 剧本、t9_t36 骨架、event_slot、endings、free_actions
  python-packages/aigal/schema_core.py  校验与清洗，纯 Python
  fonts/ gui/ images/ audio/
高中校园物语/         策划文档，见下一节
tests/
  check_cards.py    人物卡计数检查
  selftest_schema.py  schema 自检
  build_prompts.py  提示词构建
  shots/ screenshots/  截图回归用例与基准图
美术/                UI 规范、界面风格、预览图
开发环境说明.md       环境、命令、数值系统
依赖.md              依赖清单、换机器怎么跑
```

## 文档

结构：

- [剧情大纲_三年_v1.md](高中校园物语/剧情大纲_三年_v1.md)：36 格总表、三线里程碑（周墨 10 / 夏幸悠 9 / 温以宁 8）、随机事件池、5 个结局、变量表。这是骨架的权威。

AI 三份：

- [提示词_角色_v1.md](高中校园物语/提示词_角色_v1.md)：公共段、每个角色一段、差异的三层（锚点 / 可变 / 禁用）、怎么拼
- [运行时预算_v1.md](高中校园物语/运行时预算_v1.md)：250/400 字、8 秒与 12 秒、每局 39 次调用、约 0.27 元、预取
- [人物卡_v1.md](高中校园物语/人物卡_v1.md) / [.json](高中校园物语/人物卡_v1.json)：v1.1.2。说话方式、台词、行为反应、分拍状态，每条带出处，四级状态（✅ 明文依据 / 🟡 归纳 / ⬜ 待设计 / 🆕 拟定可改）

另有：

- [CHANGELOG.md](CHANGELOG.md)：每个版本一节，只记结论，不记过程。0.0.1-demo 那段是改造前的基线
- [变量命名规范_v1.md](高中校园物语/变量命名规范_v1.md)：代码和文档之间 key 的对照
- [剧本_周墨线_第一幕_开学.md](高中校园物语/剧本_周墨线_第一幕_开学.md)：第一幕全稿，已转成 `game/story/t1_september.rpy`

目录里只留现行版本。8 回合一年的那套（`剧本大纲_高一学年_v3`、`回合事件表_v3`、`游戏设定总表_v2`、`策划方案_AIGAL_v1`），以及更早的 20 回合旧结构、三幕 15 天结构、苏瑶角色稿、SKS 脚本示例、`项目文档.md`，都删了；要翻旧内容去 git 历史（`79d4456^:高中校园物语/角色设定_苏瑶.md` 就是那份旧稿）。

根目录不放文档副本，只改 `高中校园物语/` 里的版本。

## 约定

- 数值只走 `stats.rpy` 的函数。剧情里不写 `$ study += 5`。
- 剧本先写 markdown，标好 bg / bgm / sfx、选项和 Flag，再转 `.rpy`。
- 里程碑拍喂提示词时只写事实清单，最多 3 条。把台词写进去，AI 只会改写措辞。
- key 用英文小写 snake_case。改一个 key 得同时改三处：`变量命名规范_v1.md`、`stats.rpy`、回合事件表 §3 §5。
- 回合内的选择变量写成 `t<回合号>_<含义>`，小写英文值，在 story 文件顶部 `default` 一次，不进 `flags`。
- AI 文本入库顺序是：`filter_text_tags(t, allow=())` → `[` 转成 `[[` → 最后替换 `{name}` → 截断。顺序反了，`{name}` 会被当标签一起清掉。
- 玩家自填的主角名先 sanitize：1–8 字，不许带 `[` `{` `}` 和换行。名字里带这些字符等于二次注入。
- 线程的 Job 对象不进 `store`，存档会报 `cannot pickle _thread.lock`。只存 int id，Job 表放模块级，按 `keep` 回收最近若干条给诊断用。
- 缓存 key 是 `schema_ver / prompt_ver / turn / beat_id / seed / choice_path`。`store.ai_log`（进存档）优先于 `persistent.ai_seen`（跨档，200KB 封顶）。
- API key 不进日志：打码，请求体只留长度和前 200 字。
- `mood` 是场景层气氛，一个拍一个，不进画面、不做角色表情、不参与判定。以后做立绘时另开角色表情字段，别复用它——一拍里有 1–2 人在场，拍级字段驱动不了两张脸。
- 主角名在代码里还是 `XXX` 占位。改造后由玩家开局输入，`Character` 和 `{name}` 用同一个变量，不再全仓替换。

## 还没定

校名。文档里一律写「学校」，设定总表 §七 第 2 条还空着。

立绘要几个表情和姿势、素材从哪来，没定。小游戏做选择题、实时操作还是只算数值，也没定。

人物卡里标 🆕 的是「拟了、可改」，不算定稿：主角家（关外五金店、不管成绩）、周墨的琴级十级、初二停琴、节拍器来历。要改就改人物卡，别在剧本里绕开。

要你拍板的还剩这些：

1. 三条线是恋爱还是羁绊。13+ 下这决定 END 正文能写到哪。
2. AI 生成的文本进不进回滚录像。进就是能回看，代价是存档变大。
3. 首版只接一家 OpenAI 兼容端点，还是内置多家预设？

## 许可

MIT，见 [LICENSE](LICENSE)。本项目派生自 [2778277877778/gal](https://github.com/2778277877778/gal)，原仓库也是 MIT，原版权声明留在 [LICENSE](LICENSE) 里；本仓库的改动同样以 MIT 发布。
