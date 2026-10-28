# 美术 / UI 规范（0.0.1-demo）

> 界面层：字体、配色、对白条、按钮、菜单中文化。
> 立绘、背景、CG、地图 HUD 都还没做。

预览图在 `美术/预览/`：主菜单、对白、长段对白、选项、设置。

---

## 一、三主色

整个界面只有三种颜色，别的都不进 UI：

| 角色 | 色值 | 用在哪 |
|---|---|---|
| **透白** | `#ffffff` 加不同透明度（62% / 85% / 100%） | 正文、描边、次要文字、选中态 |
| **浅蓝** | `#a9cbe4` | 唯一的强调色：角色名、滑条、选中态、悬停描边、和「琴」有关的东西 |
| **墨黑** | `#0b0e12` ~ `#15181b` | 所有面板底色 |

灰色不是第四种颜色，是「白 + 墨黑半透明」叠出来的。所以：**不加铜色、不加绿色、不加红色**，要强调就提亮白，或者给浅蓝。

---

## 二、色值表

| 用途 | gui 变量 | 色值 |
|---|---|---|
| 强调（浅蓝）：名字、选中的选项、滑条、和琴有关 | `gui.accent_color` | `#a9cbe4` |
| 对白正文 | `gui.text_color` | `#ffffff` |
| 界面文字 | `gui.interface_text_color` | `#ffffffe6` |
| 按钮常态（透白 62%） | `gui.idle_color` | `#ffffff9e` |
| 小字常态（透白 52%） | `gui.idle_small_color` | `#ffffff85` |
| 悬停（浅蓝提亮） | `gui.hover_color` | `#dcecf8` |
| 选中 / 高亮 | `gui.selected_color` | `#ffffff` |
| 不可用（透白 30%） | `gui.insensitive_color` | `#ffffff4d` |
| 条槽 / 悬停槽（墨黑两档） | `gui.muted_color` / `gui.hover_muted_color` | `#15181b` / `#1e2226` |
| 对白条底 | — | 黑 72%，上缘 84px 平滑淡出 |
| 对白条顶线 | — | 1px 白 12%（谱表起始线） |
| 名札 | — | 黑 45% + 1px 白 30% 描边 + 左侧 6px 浅蓝竖条 |
| 选项（常态 / 悬停） | — | 黑 38% + 1px 白 32% / 白 14% + 1px 浅蓝 90% |
| 导航栏压暗层 | — | 黑 72% + 右缘 1px 白 18% |
| 菜单底图 | — | 墨黑竖向渐变 + 一团 10% 浅蓝光晕 |

圆角统一 6px（对白条不圆），描边统一 1px。

---

## 三、字体

| 用途 | 字体 | 1080p 字号 |
|---|---|---|
| 对白正文 | `fonts/WenKaiLite.ttf` | 36 |
| 角色名字 | `fonts/WenKaiLite.ttf` | 50，浅蓝 |
| 选项文字 | `fonts/WenKaiLite.ttf` | 36 |
| 界面 / 按钮 | `fonts/SourceHanSansLite.ttf` | 33 |
| 菜单页标题（设置、存档…） | `fonts/WenKaiLite.ttf` | 60，字距 9 |
| 主菜单标题 | `fonts/WenKaiLite.ttf` | 96，字距 16 |
| 版本号 | 思源黑体 | 23，字距 6 |
| 快捷菜单 / 存档槽 | 思源黑体 | 21 / 24 |

### 授权

- **霞鹜文楷（LXGW WenKai）**：SIL OFL 1.1，全文见 `game/fonts/OFL.txt`。
  仓库里的 `WenKaiLite.ttf` 是子集：GB2312 全部汉字 + 拉丁 + 常用标点，共 7906 字，3.5 MB。
  OFL 的保留字体名条款不允许修改版继续叫 LXGW WenKai，所以子集内部改名为 `GZXY WenKai Lite`。
- **思源黑体 Lite**：Ren'Py SDK 模板自带。

---

## 四、封面（主菜单）

照钢琴线提案的版式，颜色换成三主色：

- 左边 420px 墨黑压暗柱，右缘 1px 白线；导航左对齐，常态透白 62%，悬停浅蓝提亮
- 标题右下、纯白、96px、字距 16
- 标题底下一条 1px 白 27% 的线（宽度按标题给：6 字 × 96 + 5 × 16 ≈ 658px）
- 版本号压在线的下面，思源黑体 23，透白 52%
- 底图留白等立绘/背景，现在是墨黑渐变 + 一点浅蓝光晕

---

## 五、文件清单

```
game/gui.rpy          三主色、字体、字号、间距（所有数值都在这里）
game/ui_theme.rpy     样式微调（行距、字距、标题、历史、存档槽）
game/ui_zh.rpy        界面中文字符串
game/guisupport.rpy   1.5 倍缩放；已关掉模板的 GUI 图片自动烘焙
game/fonts/           WenKaiLite.ttf、SourceHanSansLite.ttf、OFL.txt
game/gui/main_menu.png        1920×1080 封面底图
game/gui/game_menu.png        1920×1080 菜单底图
game/gui/textbox.png          1920×278，上缘柔和淡出 + 1px 白顶线
game/gui/namebox.png          300×120，9-patch，borders 24/15
game/gui/button/choice_*_background.png   360×120，9-patch，borders 36/21
game/gui/overlay/{main,game}_menu.png     420×1080 压暗层
```

`game/gui/` 下其余图片（滑条、滚动条、勾选、存档槽…）是 Ren'Py 模板按 `gui.accent_color` 烘出来的，浅蓝。

---

## 六、改色 / 重做素材

1. 改 `game/gui.rpy` 里的色值。
2. **删掉 `game/gui/` 下的 png**（自动烘焙只补缺的文件，不覆盖已有的）。
3. 临时打开 `game/guisupport.rpy` 里注释掉的 `init 100` 那段，跑一次 `lint`。
4. 关回去，跑 `tools/mkui.py` 写回手绘素材：对白条、名札、选项按钮、两张菜单底图、两张压暗层。
5. `lint` 一遍，启动看效果。

生成脚本在工作区（仓库外）：

- `tools/makefont.py`：从霞鹜文楷完整版裁子集、改字体名。
- `tools/mkui.py`：对白条、名札、选项按钮、菜单底图、压暗层。

---

## 七、注意

- 字距（`kerning`）只加在标题、名字、版本号上；正文不加，中文加字距会散。
- 对白条最多放 4 行 36px 正文；剧本单块建议不超过 4 行。
- 界面字符串在 `game/ui_zh.rpy` 里改，不动 `screens.rpy` 原文。
- `美术/界面风格_钢琴线_v1.md` 里的**旧铜方案不采用**：配色以「透白 / 浅蓝 / 墨黑」为准，那三张效果图的版式可以参考，颜色过时。

---

## 八、还没做

- 立绘规格（表情数、姿势数）与像素素材清单
- 背景、CG
- 地图 HUD：左上人物、右上时间 / AP、左下数值
- 选项悬停动效、逐字机、打字音
