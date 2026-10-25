# 美术 / UI 规范（0.0.1-demo）

> 这一版只做界面层：字体、配色、对白条、按钮、菜单中文化。
> 立绘、背景、CG、地图 HUD 都还没做。

预览图在 `美术/预览/`：主菜单、对白、长段对白、选项、设置。

---

## 一、这一版改了什么

| 改动 | 位置 | 说明 |
|---|---|---|
| 全局缩放 ×1.5 | `game/guisupport.rpy` | 模板数字是按 1280×720 写的，工程是 1920×1080。以前字和面板整体小一圈，对白条只有 185px 高（应为 278px） |
| 换正文/标题字体 | `game/gui.rpy` | 霞鹜文楷子集（正文、名字、标题），思源黑体 Lite 留给界面小字 |
| 配色换成雨青 | `game/gui.rpy` | 去掉模板默认的青色 `#00b8c3` |
| 对白条 / 名札 / 选项按钮 | `game/gui/*.png` | 手绘 9-patch 素材，暗底 + 雨青细描边 |
| 界面中文化 | `game/ui_zh.rpy` | `translate None strings`，不动 `screens.rpy` 原文 |
| 标题排版 | `game/screens.rpy`、`game/ui_theme.rpy` | 主菜单标题加字距、投影，下面加一条雨青短线 |
| 样式微调 | `game/ui_theme.rpy` | 行距、名字字距、菜单页标题、历史、存档槽字号 |

---

## 二、配色

| 用途 | gui 变量 | 色值 |
|---|---|---|
| 主题色（雨青）：名字、选中、滑条、强调 | `gui.accent_color` | `#96c8b2` |
| 对白正文 | `gui.text_color` | `#f2eee3` |
| 界面文字 | `gui.interface_text_color` | `#e7e2d6` |
| 按钮常态 | `gui.idle_color` | `#8e9a93` |
| 小字常态 | `gui.idle_small_color` | `#a9b5ae` |
| 选中 / 高亮 | `gui.selected_color` | `#f6f2e8` |
| 不可用 | `gui.insensitive_color` | `#4e5a54` 60% |
| 进度条槽 / 悬停 | `gui.muted_color` / `gui.hover_muted_color` | `#22362f` / `#2c463c` |
| 悬停色 | `gui.hover_color` | 主题色提亮 60% |
| 墨绿黑（面板底） | — | `#090f0d` |
| 导航栏压暗层 | — | 黑 80% + 右缘 2px 雨青 43% |

底色偏墨绿，主题色是低饱和的雨青，整体往「潮湿的南方春天」走，不用纯黑纯白。

---

## 三、字体

| 用途 | 字体 | 1080p 字号 |
|---|---|---|
| 对白正文 | `fonts/WenKaiLite.ttf` | 36 |
| 角色名字 | `fonts/WenKaiLite.ttf` | 50 |
| 选项文字 | `fonts/WenKaiLite.ttf` | 36 |
| 界面 / 按钮 | `fonts/SourceHanSansLite.ttf` | 33 |
| 菜单页标题（设置、存档…） | `fonts/WenKaiLite.ttf` | 60，字距 9 |
| 主菜单标题 | `fonts/WenKaiLite.ttf` | 96，字距 12，投影 |
| 版本号 | 思源黑体 | 23，字距 6 |
| 快捷菜单 / 存档槽 | 思源黑体 | 21 / 24 |

### 授权

- **霞鹜文楷（LXGW WenKai）**：SIL OFL 1.1，全文见 `game/fonts/OFL.txt`。
  仓库里的 `WenKaiLite.ttf` 是子集：GB2312 全部汉字 + 拉丁 + 常用标点，共 7906 字，3.5 MB。
  OFL 的保留字体名条款不允许修改版继续叫 LXGW WenKai，所以子集内部改名为 `GZXY WenKai Lite`。
- **思源黑体 Lite**：Ren'Py SDK 模板自带。

---

## 四、文件清单

```
game/gui.rpy          颜色、字体、字号、间距（所有数值都在这里）
game/ui_theme.rpy     样式微调（行距、字距、标题、历史、存档槽）
game/ui_zh.rpy        界面中文字符串
game/guisupport.rpy   1.5 倍缩放；已关掉模板的 GUI 图片自动烘焙
game/fonts/           WenKaiLite.ttf、SourceHanSansLite.ttf、OFL.txt
game/gui/textbox.png          1920×278，上缘柔和淡出
game/gui/namebox.png          300×120，9-patch，borders 24/15
game/gui/button/choice_*_background.png   360×120，9-patch，borders 36/21
game/gui/overlay/{main,game}_menu.png     420×1080 压暗层
```

---

## 五、要改主题色 / 重做素材时

1. 改 `game/gui.rpy` 里的 `gui.accent_color`。
2. 临时打开 `game/guisupport.rpy` 里注释掉的 `init 100` 那段，跑一次 `lint`（它会按新主题色重新烘焙滑条、滚动条、压暗层等图片）。
3. 跑 `tools/mkui.py`，把对白条、名札、选项按钮这三套手绘素材写回去——自动烘焙会把它们覆盖成默认样子。
4. 跑一遍 `lint`，再启动看效果。

生成脚本在工作区（仓库外）：

- `tools/makefont.py`：从霞鹜文楷完整版裁子集、改字体名。
- `tools/mkui.py`：对白条、名札、选项按钮、菜单压暗层。

---

## 六、注意

- `game/testcases.rpy` 是按英文按钮名写的（点 `"Start"`、`"Save"`…），界面中文化后跑 `testcases` 会失败。要么改成中文按钮名，要么删掉。
- 字距（`kerning`）只加在标题、名字、版本号上；正文不加，中文加字距会散。
- 对白条最多放 4 行 36px 正文；剧本单块建议不超过 4 行。

---

## 七、还没做

- 立绘规格（表情数、姿势数）与像素素材清单
- 背景、CG
- 地图 HUD：左上人物、右上时间 / AP、左下数值
- 选项悬停动效、逐字机、打字音
