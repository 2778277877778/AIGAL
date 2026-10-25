# 📜 第一章：开学篇 - SKS脚本示例

> 使用SakiEngine的SKS脚本语法编写  
> 语法参考：https://github.com/AimesSoft/SakiEngine/blob/main/docs/script-guide.md

---

## 📁 脚本文件结构

```
GameScript/
├── labels/
│   ├── chapter1/
│   │   ├── start.sks          # 第一章开始
│   │   ├── classroom.sks      # 教室场景
│   │   ├── library.sks        # 图书馆场景
│   │   ├── rooftop.sks        # 天台场景
│   │   └── choices.sks        # 选择分支
│   ├── chapter2/
│   └── ...
├── characters/
│   ├── mc.sks                 # 主角定义
│   ├── su_yao.sks             # 苏瑶定义
│   ├── lin_shiyu.sks          # 林诗语定义
│   └── ...
└── variables/
    └── stats.sks              # 属性变量定义
```

---

## 🎭 角色定义

### 主角定义 (characters/mc.sks)

```sks
# 主角定义
character mc "XXX" color=#FFFFFF
# color: 对话框颜色（白色）
# 主角没有语音，只有旁白和选项
```

### 苏瑶定义 (characters/su_yao.sks)

```sks
# 苏瑶定义
character su_yao "苏瑶" color=#4169E1 voice="su_yao"
# color: 对话框颜色（皇家蓝）
# voice: 语音文件前缀

# 表情定义
expression su_yao default "images/char/su_yao/default.png"
expression su_yao smile "images/char/su_yao/smile.png"
expression su_yao blush "images/char/su_yao/blush.png"
expression su_yao angry "images/char/su_yao/angry.png"
expression su_yao sad "images/char/su_yao/sad.png"
expression su_yao cry "images/char/su_yao/cry.png"
expression su_yao surprised "images/char/su_yao/surprised.png"
```

### 林诗语定义 (characters/lin_shiyu.sks)

```sks
# 林诗语定义
character lin_shiyu "林诗语" color=#9370DB voice="lin_shiyu"
# color: 对话框颜色（紫色）

# 表情定义
expression lin_shiyu default "images/char/lin_shiyu/default.png"
expression lin_shiyu shy "images/char/lin_shiyu/shy.png"
expression lin_shiyu happy "images/char/lin_shiyu/happy.png"
expression lin_shiyu worried "images/char/lin_shiyu/worried.png"
```

### 张浩定义 (characters/zhang_hao.sks)

```sks
# 张浩定义
character zhang_hao "张浩" color=#32CD32
# color: 对话框颜色（绿色）
# 好基友角色
```

---

## 📊 属性变量定义 (variables/stats.sks)

```sks
# 主角属性
default learning = 50        # 学习能力 (0-100)
default stamina = 100        # 体力/活力 (0-100)
default mood = 50            # 心情 (0-100)
default stress = 0           # 压力 (0-100, 越高越不好)
default money = 100          # 金钱

# 好感度
default su_yao_affection = 0      # 苏瑶好感度 (0-100)
default lin_shiyu_affection = 0   # 林诗语好感度 (0-100)
default zhang_hao_affection = 50  # 张浩好感度 (0-100)

# 时间系统
default current_day = 1      # 当前天数
default current_period = "morning"  # 当前时段

# 剧情标记
default met_su_yao = False       # 是否遇到苏瑶
default met_lin_shiyu = False    # 是否遇到林诗语
default know_su_yao_secret = False  # 是否知道苏瑶的秘密
```

---

## 📖 第一章脚本 (labels/chapter1/start.sks)

```sks
# ========================================
# 第一章：开学篇
# 场景1：开学第一天
# ========================================

label chapter1_start:

    # 初始化属性
    $ learning = 50
    $ stamina = 100
    $ mood = 60
    $ stress = 0
    $ money = 100

    # 设置背景
    scene bg school_gate with fade
    play music "audio/bgm/school_morning.ogg" fadein 2.0

    # 旁白
    "九月的阳光洒在校门口，金色的光芒映照着崭新的学期。"
    "我深吸一口气，踏入了这所普通却充满可能性的高中。"

    # 主角内心独白
    mc "（新学校...新开始...希望一切顺利。）"

    # 命名主角
    $ player_name = input("请输入你的名字：") or "XXX"
    
    mc "（我叫[player_name]，从今天开始，就是这所学校的学生了。）"

    # 转场到教室
    scene bg classroom with dissolve
    play music "audio/bgm/classroom.ogg" fadein 1.0

    "教室里已经坐了不少同学，叽叽喳喳地聊着天。"
    "我找了个靠窗的位置坐下，阳光正好洒在桌面上。"

    # 张浩登场
    show zhang_hao at center with dissolve

    zhang_hao "嘿！你也是新来的吗？"

    mc "嗯，我叫[player_name]。"

    zhang_hao "我叫张浩！以后我们就是同桌了！"

    mc "（他看起来挺热情的。）"

    zhang_hao "对了，你知道吗？我们班有个很厉害的人物。"

    mc "谁？"

    # 苏瑶登场
    hide zhang_hao
    show su_yao at center with dissolve
    play sound "audio/sfx/door_open.ogg"

    "教室门被推开，一个女生走了进来。"
    "她穿着整洁的校服，黑色长发扎成低马尾，眼神冷淡。"
    "整个教室瞬间安静下来。"

    mc "（她是谁？为什么大家都看着她？）"

    # 切换回张浩
    hide su_yao
    show zhang_hao at center

    zhang_hao "（小声）那就是苏瑶，据说中考全市第一进来的。"
    zhang_hao "学习超厉害，但是...好像不太好相处。"

    # 苏瑶坐下
    hide zhang_hao
    show su_yao default at center

    "苏瑶走到座位，坐下，拿出书本开始学习，完全无视周围的目光。"

    mc "（她看起来...很冷淡。）"

    # 第一个选择
    menu:
        "你会怎么做？"

        "主动打招呼":
            $ su_yao_affection += 2
            jump chapter1_greet_su_yao

        "远远观察":
            $ learning += 2
            jump chapter1_observe_su_yao

        "问张浩更多关于她的事":
            $ zhang_hao_affection += 2
            jump chapter1_ask_about_su_yao

    return

# ========================================
# 分支1：主动打招呼
# ========================================

label chapter1_greet_su_yao:

    mc "（主动一点吧，毕竟以后是同学。）"

    mc "你好，我叫[player_name]，以后请多指教。"

    show su_yao default at center
    su_yao "..."

    "她抬起头，看了我一眼，然后继续低头看书。"

    mc "（呃...被无视了。）"

    zhang_hao "（小声）别在意，她对谁都这样。"

    mc "（是吗...）"

    jump chapter1_continue

# ========================================
# 分支2：远远观察
# ========================================

label chapter1_observe_su_yao:

    mc "（还是先观察一下吧。）"

    "我静静地坐在座位上，偷偷观察着苏瑶。"
    "她翻书的速度很快，似乎在预习新课。"
    "偶尔会在笔记本上写些什么，字迹工整得像印刷体。"

    mc "（她真的很认真啊...）"

    "这时，一个同学不小心碰掉了她的笔。"

    "同学" "啊，对不起！"

    su_yao "..."

    "她什么也没说，只是弯腰捡起笔，继续学习。"

    mc "（真的很冷淡...）"

    jump chapter1_continue

# ========================================
# 分支3：问张浩
# ========================================

label chapter1_ask_about_su_yao:

    mc "她是什么来头？"

    zhang_hao "听说她爸爸是大公司的高管，对她要求特别高。"
    zhang_hao "她初中就是年级第一，从来没掉下来过。"
    zhang_hao "但是...好像没什么朋友。"

    mc "为什么？"

    zhang_hao "她不跟人说话啊，整天就知道学习。"
    zhang_hao "有人想跟她交朋友，都被拒绝了。"

    mc "（是吗...）"

    jump chapter1_continue

# ========================================
# 主线继续
# ========================================

label chapter1_continue:

    play sound "audio/sfx/bell.ogg"

    "上课铃响了，班主任走了进来。"

    show teacher at center with dissolve

    teacher "同学们好，我是你们的班主任王老师，教语文。"
    teacher "欢迎来到高一（3）班，希望我们能一起度过愉快的三年。"

    "王老师开始点名，我才知道班上一共有40个学生。"

    teacher "苏瑶。"
    su_yao "...到。"

    "她的声音很轻，但很清楚。"

    teacher "[player_name]。"
    mc "到。"

    "（就这样，我的高中生活开始了。）"

    hide teacher

    # 转场到放学后
    scene bg classroom_sunset with dissolve
    play music "audio/bgm/afternoon.ogg" fadein 1.0

    "放学后，同学们陆续离开教室。"
    "我收拾好书包，准备去图书馆看看。"

    # 张浩邀请
    show zhang_hao at center

    zhang_hao "嘿，要不要一起去小卖部？我请你喝饮料！"

    menu:
        "张浩邀请你去小卖部"

        "好啊，走吧":
            $ zhang_hao_affection += 3
            mc "好啊，正好有点渴。"
            zhang_hao "走走走！"
            "（我和张浩一起去了小卖部，聊了很多。）"
            $ stamina -= 10

        "我想去图书馆看看":
            $ learning += 3
            mc "我想去图书馆看看，下次吧。"
            zhang_hao "好吧，那明天见！"
            jump chapter1_library

        "我有点累了，想回家休息":
            $ stamina += 20
            mc "今天有点累，我想先回去了。"
            zhang_hao "好吧，注意安全！"
            jump chapter1_home

    jump chapter1_library

# ========================================
# 图书馆场景
# ========================================

label chapter1_library:

    scene bg library with dissolve
    play music "audio/bgm/library.ogg" fadein 1.0

    "图书馆里很安静，只有翻书的声音。"
    "我走进去，想找一本数学参考书。"

    "在书架间穿梭时，我看到一个娇小的女生正在整理书籍。"

    show lin_shiyu shy at center with dissolve

    lin_shiyu "（小声）这本放这里...那本放那里..."

    "她似乎没注意到我，专心地整理着。"

    mc "（她是图书委员吗？）"

    "我走近了一些，想问问她参考书在哪里。"

    mc "那个..."

    lin_shiyu "啊！"

    "她被吓了一跳，脸一下子红了。"

    lin_shiyu "对、对不起...我、我是图书委员...你、你需要找什么书吗？"

    mc "（她好容易紧张...）"

    menu:
        "林诗语问你需要什么"

        "我来找数学参考书":
            mc "我来找数学参考书，你知道在哪里吗？"
            lin_shiyu "数、数学参考书...在、在那边..."
            "她带着我走到书架前，帮我找到了书。"
            lin_shiyu "这、这本应该可以..."
            mc "谢谢。"
            lin_shiyu "不、不客气..."

        "你好像很擅长整理？":
            mc "你好像很擅长整理？"
            lin_shiyu "啊？还、还好啦...我是图书委员..."
            mc "整理这么多书，很辛苦吧？"
            lin_shiyu "不、不会的...我喜欢书..."
            "（她说话的时候，眼睛亮了起来。）"

        "你经常来这里吗？":
            mc "你经常来这里吗？"
            lin_shiyu "嗯、嗯...我每天都来..."
            mc "这么喜欢看书？"
            lin_shiyu "嗯...书、书里有很多有趣的故事..."
            "（她害羞地笑了笑。）"

    # 意外事件
    "这时，她不小心碰倒了一摞书。"

    lin_shiyu "啊！对不起对不起！"

    "她慌张地想捡书，我赶紧帮忙。"

    mc "没关系，我帮你。"

    "我们一起捡书时，我注意到她手里拿着一本诗集。"

    mc "你也喜欢诗吗？"

    lin_shiyu "嗯...我、我喜欢写诗..."

    mc "真的吗？能给我看看吗？"

    lin_shiyu "啊？不、不行！写得很差..."

    "她把诗集藏到身后，脸更红了。"

    mc "（她真的很害羞...）"

    mc "没关系，等你觉得可以的时候再给我看吧。"

    lin_shiyu "...嗯。"

    "（她轻轻点了点头，似乎松了口气。）"

    # 获得信息
    $ met_lin_shiyu = True
    $ lin_shiyu_affection += 3

    mc "（林诗语...图书委员...喜欢写诗...）"

    # 离开图书馆
    "借完书后，我离开了图书馆。"
    "回头看了一眼，她还在认真地整理书籍。"

    mc "（她是个很认真的女孩呢。）"

    jump chapter1_day1_end

# ========================================
# 回家场景
# ========================================

label chapter1_home:

    scene bg home_night with dissolve
    play music "audio/bgm/night.ogg" fadein 1.0

    "回到家，吃过晚饭，我开始整理今天的笔记。"

    mc "（第一天...还不错。）"
    mc "（认识了张浩...还有那个叫苏瑶的女生...）"

    "（她看起来很冷淡，但不知道为什么，我有点在意她。）"

    # 结束第一天
    jump chapter1_day1_end

# ========================================
# 第一天结束
# ========================================

label chapter1_day1_end:

    scene bg bedroom_night with dissolve
    play music "audio/bgm/sleepy.ogg" fadein 1.0

    "晚上，我躺在床上，回想着今天发生的事。"

    mc "（高中生活...就这样开始了。）"
    mc "（明天会怎样呢...）"

    # 显示状态
    "【当前状态】"
    "学习能力：[learning]"
    "体力：[stamina]"
    "心情：[mood]"
    "压力：[stress]"

    if met_su_yao:
        "苏瑶好感度：[su_yao_affection]"

    if met_lin_shiyu:
        "林诗语好感度：[lin_shiyu_affection]"

    # 自动存档
    save_game auto="day1_end"

    # 跳转到第二天
    jump chapter1_day2

    return

# ========================================
# 第二天开始
# ========================================

label chapter1_day2:

    scene bg bedroom_morning with fade
    play sound "audio/sfx/alarm.ogg"

    "叮铃铃——"

    "闹钟响了，新的一天开始了。"

    mc "（该去上学了...）"

    scene bg school_gate with dissolve
    play music "audio/bgm/school_morning.ogg" fadein 1.0

    "走进校门，我看到一个熟悉的身影。"

    show su_yao default at center with dissolve

    "是苏瑶。"
    "她独自走在前面，周围的同学都自动让开一条路。"

    menu:
        "你看到苏瑶独自走在前面"

        "追上去打招呼":
            $ su_yao_affection += 2
            mc "苏瑶！早上好！"
            su_yao "...早。"
            "她头也没回，只是淡淡地应了一声。"
            mc "（至少...她回应了。）"

        "保持距离跟着":
            $ learning += 1
            "我远远地跟在后面，看着她的背影。"
            mc "（她好像...很孤独。）"

        "去找张浩":
            $ zhang_hao_affection += 2
            "我转向另一边，去找张浩。"
            mc "张浩！早上好！"
            zhang_hao "嘿！走，一起去教室！"

    # 继续剧情...
    jump chapter1_day2_classroom

    return
```

---

## 🎵 音乐文件清单

| 文件名 | 用途 | 风格 |
|--------|------|------|
| school_morning.ogg | 上学路上 | 轻快、活力 |
| classroom.ogg | 教室场景 | 安静、学习氛围 |
| library.ogg | 图书馆 | 宁静、专注 |
| afternoon.ogg | 放学后 | 轻松、愉快 |
| night.ogg | 夜晚 | 安静、温馨 |
| sleepy.ogg | 睡前 | 轻柔、催眠 |

## 🔊 音效文件清单

| 文件名 | 用途 |
|--------|------|
| door_open.ogg | 开门声 |
| bell.ogg | 上课铃 |
| alarm.ogg | 闹钟声 |
| footstep.ogg | 脚步声 |
| paper.ogg | 翻书声 |

---

## 📝 脚本开发说明

### 基础语法

```sks
# 对话
角色名 "对话内容"

# 旁白
"旁白内容"

# 选择
menu:
    "提示文字"
    "选项1":
        # 选项1的剧情
    "选项2":
        # 选项2的剧情

# 属性变化
$ 变量名 += 数值
$ 变量名 -= 数值

# 场景切换
scene bg 背景名 with 效果

# 角色显示/隐藏
show 角色名 at 位置 with 效果
hide 角色名

# 音乐
play music "文件路径" fadein 秒数
stop music fadeout 秒数

# 音效
play sound "文件路径"

# 跳转
jump 标签名

# 条件判断
if 条件:
    # 满足条件时
else:
    # 不满足条件时
```

### 好感度变化示例

```sks
# 增加好感度
$ su_yao_affection += 5

# 检查好感度
if su_yao_affection >= 50:
    su_yao "...（微笑）"
else:
    su_yao "..."
```

---

*脚本由 MiMo 2.6 Pro 生成，可根据需要调整*