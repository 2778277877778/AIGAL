################################################################################
## ai/fallback.rpy —— 本地模板库。
##
## 两种用途：
##   1. 降级：没 key、断网、超时、模型连续两次输出不合格时，游戏必须还能玩。
##   2. 正文：自由行动（自习、吃饭、打球）**不走 AI**，这里就是唯一正文
##      （2026-10-30 定）。所以这几段不是「备选」，是玩家真要读的文本。
##
## 形状（和 ai_validate 的返回同构，剧本层不用区分来源）：
##   "t2_piano": {"lines": [...], "choices": [...], "mood": "quiet"}
##
## 查找顺序（template(beat_id, choice_path)）：
##   1. "<beat>/<choice_path>"   拍内分支专用
##   2. "act/<choice_path>"      自由行动的通用正文，跟月份无关
##   3. "<beat>"                 这一拍的默认
##   4. _EMPTY_TEMPLATE          兜底占位，绝不编剧情
##
## 旁白与内心是两条通道，不许互相顶：
##   nar   正体、无名字、无括号 —— 写看得见的事实（谁在哪、什么在响、光从哪来）
##   inner 斜体、无名字、带括号 —— 写主角心里的话（自嘲、自我拆台）
## 拿 inner 写天气是错的：显示会变斜体，跟 T1 正文的旁白不是一种东西。
##
## 三条长度档（不是「凑不到 250 字」，是故意的）：
##   - 剧情拍 4–5 行、合计 80–160 字：按人物纪律写，主角半句就断、周墨每拍十来字。
##   - 自由行动 2–3 行、合计 40–90 字：同一段一个月要读两三次、八个月十几遍，
##     写 250 字等于逼玩家把同一段长文读十几遍。短是对的。
##   - 结局走 schema 的 ending 预算（160 字/行、600 字合计），另算。
##
## 选项的 action_key：
##   - 自由行动：本来就给 ACTIONS 的 key；但自由段已不走 AI，模板里不填选项。
##   - 剧情拍：不是 ACTIONS，是分支 id，取值以 ai/prompts.rpy 的 BEAT_CHOICES 为准。
##     t2_piano → reveal / ignore；t2_call → stay / leave / water_only；
##     t1 三拍 → 与 game/story/t1_september.rpy 的 t1_answer / t1_candy / t1_night 取值一致
##     （deny·ask·fumble / hand·step·via_zzb / look·listen），否则剧本的 if/else 走不到。
##   fallback 不走 ai_validate，填错了不会报错，只会静默走不到分支——所以别照抄 ACTIONS。
################################################################################

init -4 python in aig:

    ## beat_id（或 "act/<action_key>"）→ 一段固定文本。
    ## 剧情拍的对话 speaker 要和 prompts.rpy 的 BEAT_SPEAKERS 对得上，不然 AI 版和模板版换人。
    ## nar 是结构性 id，不受 BEAT_SPEAKERS 限制，任何一拍都可以有。
    FALLBACK = {

        ## ── T1 九月（剧本目前是硬编码，这几段留给以后接 AI 用）─────────────





        ## ── T2 十月 ────────────────────────────────────────────────────────

        "t2_piano": {
            "lines": [
                {"speaker": "nar", "text": "四楼走廊尽头，门虚掩着，灯只开了一盏。"},
                {"speaker": "zm", "text": "……你怎么在这。"},
                {"speaker": "mc", "text": "我、我搬东西。不是——我听见琴声。"},
                {"speaker": "zm", "text": "……不许说出去。"},
                {"speaker": "nar", "text": "她手还停在半空。谱架上一叠手抄谱，页角卷了。"},
            ],
            "choices": [
                {"text": "「我不会说。」", "action_key": "ignore"},
                {"text": "「你弹得很好。」", "action_key": "reveal"},
            ],
            "mood": "cold",
        },



        "t2_call": {
            "lines": [
                {"speaker": "nar", "text": "楼梯间的灯坏了一半，她背对着门打电话。"},
                {"speaker": "zm_dad", "text": "数学为什么没满分？"},
                {"speaker": "zm", "text": "……最后一道，算错了。"},
                {"speaker": "zm_dad", "text": "你自己算算差多少。别想那些没用的。"},
                {"speaker": "nar", "text": "她挂了电话，靠着墙站了很久，没动。"},
            ],
            "choices": [
                {"text": "过去问一句", "action_key": "stay"},
                {"text": "走开，当没看见", "action_key": "leave"},
                {"text": "放一瓶水在楼梯口", "action_key": "water_only"},
            ],
            "mood": "low",
        },

        ## ── T3 十一月 ───────────────────────────────────────────────────
        ## 这几段是「没有 key 也能玩」的正文，不是备胎。文案定稿后直接换文字，
        ## 不要改 action_key —— 剧本按 key 走分支。

        "t3_exam/pass": {
            "lines": [
                {"speaker": "inner", "text": "（期中的分数条夹在卷子里。总分过了线，物理那一栏还是难看。）"},
                {"speaker": "zm", "text": "……第三。"},
                {"speaker": "nar", "text": "她说这两个字的时候没什么表情。卷子被她折成四折，塞进书里。"},
            ],
            "choices": [],
            "mood": "tense",
        },

        "t3_exam/fail": {
            "lines": [
                {"speaker": "inner", "text": "（分数条发下来，我看了两遍才看懂。没到线。）"},
                {"speaker": "zeng", "text": "这次不算，期末再补。别把卷子揉了，留着看错题。"},
                {"speaker": "nar", "text": "她自己那张卷子考得比谁都高。她没看我。"},
            ],
            "choices": [],
            "mood": "low",
        },

        "t3_parent": {
            "lines": [
                {"speaker": "nar", "text": "家长会。走廊里全是家长，她父亲站在窗边，白大褂没换。"},
                {"speaker": "mc", "text": "周、周医生好。"},
                {"speaker": "zm_dad", "text": "你是？"},
                {"speaker": "mc", "text": "我、我是她同学。我帮她拿一下东西。"},
                {"speaker": "nar", "text": "她把她父亲送到楼梯口，回来站了一会儿才开口。"},
                {"speaker": "zm", "text": "你不用这样。"},
            ],
            "choices": [],
            "mood": "low",
        },


        ## ── T4 十二月 ───────────────────────────────────────────────────
        "t4_artfair": {
            "lines": [
                {"speaker": "bro", "text": "——下一个节目，《送别》，钢琴伴奏。"},
                {"speaker": "nar", "text": "灯暗下来。琴声起来的时候，前排有人回头。"},
                {"speaker": "nar", "text": "是她。报名表上「伴奏」那栏，还是空的。"},
                {"speaker": "nar", "text": "她父亲的位置空着，一直空到散场。"},
            ],
            "choices": [
                {"text": "去跟主持人说清楚，伴奏是她弹的。", "action_key": "speak"},
                {"text": "什么也不说。", "action_key": "quiet"},
            ],
            "mood": "light",
        },


        "t4_exam/pass": {
            "lines": [
                {"speaker": "inner", "text": "（期末分数出来，过了线。不高，但过了。）"},
                {"speaker": "zeng", "text": "寒假别把书扔了。开学还有摸底。"},
                {"speaker": "nar", "text": "她第一。成绩单贴在教室后面，她没去看。"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "t4_exam/fail": {
            "lines": [
                {"speaker": "inner", "text": "（期末没过线。卷子发下来，我把它夹在书里，没再翻开。）"},
                {"speaker": "zeng", "text": "寒假把错题抄一遍。开学我查。"},
                {"speaker": "nar", "text": "她经过我桌子，停了一下，把一支笔放回来。"},
            ],
            "choices": [],
            "mood": "low",
        },



        ## ── T5 三月 ─────────────────────────────────────────────────────
        "t5_move": {
            "lines": [
                {"speaker": "nar", "text": "四楼走廊堆着纸箱。她一个人把谱子往里塞，塞得很整齐。"},
                {"speaker": "mc", "text": "我、我来。"},
                {"speaker": "nar", "text": "箱子底一滑，谱子撒了一地。节拍器从箱底滚出来，外壳裂了一道。"},
                {"speaker": "zm", "text": "你手流血了。"},
                {"speaker": "nar", "text": "她先看的是我的手。"},
            ],
            "choices": [
                {"text": "蹲下去，把谱子一张张捡起来。", "action_key": "move"},
                {"text": "拉她去找曾老师。", "action_key": "teacher"},
                {"text": "劝她，别弹了。", "action_key": "stop"},
            ],
            "mood": "cold",
        },


        "t5_mother": {
            "lines": [
                {"speaker": "nar", "text": "楼梯间的灯坏了一半。她在下一层，背着身打电话。"},
                {"speaker": "zm_mom", "text": "你爸那边，我再跟他说说。"},
                {"speaker": "zm", "text": "……嗯。"},
                {"speaker": "nar", "text": "她挂了电话，靠着墙蹲下去。我站在上一层的拐角，没下去。"},
            ],
            "choices": [],
            "mood": "low",
        },

        ## ── T6 四月 ─────────────────────────────────────────────────────


        "t6_club": {
            "lines": [
                {"speaker": "zeng", "text": "申请批了。社长，你来当。"},
                {"speaker": "zm", "text": "我？"},
                {"speaker": "zzb", "text": "社长，收不收男生？"},
                {"speaker": "zm", "text": "收。但你不许偷弹。"},
                {"speaker": "nar", "text": "报名表传到我手里，最上面一行还空着。"},
            ],
            "choices": [
                {"text": "第一个在报名表上签字。", "action_key": "join"},
                {"text": "只帮忙搬椅子，不签字。", "action_key": "help"},
                {"text": "不参加。", "action_key": "no"},
            ],
            "mood": "light",
        },

        ## ── T7 五月 ─────────────────────────────────────────────────────
        "t7_hall": {
            "lines": [
                {"speaker": "nar", "text": "音乐厅门口，她站在节目单前面，站了很久。"},
                {"speaker": "nar", "text": "节目单右下角有一行小字：本场钢琴，某某音乐学院。"},
                {"speaker": "stu_a", "text": "周墨——走了！"},
                {"speaker": "nar", "text": "她回头，跟着队伍走了。走之前，又看了一眼那行字。"},
            ],
            "choices": [],
            "mood": "still",
        },


        ## ── T8 六月 ─────────────────────────────────────────────────────

        "t8_exam/pass": {
            "lines": [
                {"speaker": "inner", "text": "（学年期末过了线。）"},
                {"speaker": "zeng", "text": "成绩单拿回去给家长看。分科表明天交。"},
                {"speaker": "nar", "text": "她从我旁边过去，手里两张表，一张自己的，一张空的。"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "t8_exam/fail": {
            "lines": [
                {"speaker": "inner", "text": "（学年期末没过线。）"},
                {"speaker": "zeng", "text": "分科表照填。成绩的事，暑假补。"},
                {"speaker": "nar", "text": "她在门口等我，没说分数，只把一支笔递过来。"},
            ],
            "choices": [],
            "mood": "low",
        },


        "t8_subject": {
            "lines": [
                {"speaker": "nar", "text": "她把表摊在桌上，笔盖没盖。"},
                {"speaker": "zm", "text": "你说……我是不是错了。"},
                {"speaker": "nar", "text": "她第一次问我这种问题。我嘴张开，又合上。"},
            ],
            "choices": [
                {"text": "「你想弹就弹。」", "action_key": "support"},
                {"text": "「你爸说得也对。」", "action_key": "against"},
                {"text": "什么也不说。", "action_key": "silent"},
            ],
            "mood": "low",
        },

        "t8_form": {
            "lines": [
                {"speaker": "inner", "text": "（我的选科表还空着。笔尖在「史地政」和「物化生」之间悬着。）"},
                {"speaker": "nar", "text": "她在讲台左边第三摞前面站着，等我。"},
            ],
            "choices": [
                {"text": "跟她填一样的（史地政）。", "action_key": "same"},
                {"text": "按自己的打算填（物化生）。", "action_key": "different"},
            ],
            "mood": "tense",
        },

        ## ── 结局 ───────────────────────────────────────────────────────
        ## 正文以大纲 §5 为准；这里是没有 key 时的版本，改动时两边一起改。
        "t8_true": {
            "lines": [
                {"speaker": "nar", "text": "分班名单贴出来那天，两个名字在同一栏，中间隔了三个名字。"},
                {"speaker": "nar", "text": "音乐社留了下来。礼堂后台那台琴正式归了社团，琴盖上贴了一张手写的牌子。"},
                {"speaker": "nar", "text": "暑假第一天，他抱着修好的节拍器去学校。还是慢半拍。"},
                {"speaker": "zm", "text": "能走。"},
                {"speaker": "mc", "text": "周墨。我、我喜欢你。"},
                {"speaker": "zm", "text": "……我知道了。"},
                {"speaker": "mc", "text": "你、你知道什么了。"},
                {"speaker": "zm", "text": "知道你要说什么。"},
                {"speaker": "nar", "text": "她把节拍器拨到零。"},
                {"speaker": "zm", "text": "我也是。"},
                {"speaker": "nar", "text": "弹错的音，也还在曲子里。"},
            ],
            "choices": [],
            "mood": "warm",
        },

        "t8_true/silent": {
            "lines": [
                {"speaker": "nar", "text": "分班名单贴出来那天，两个名字在同一栏。"},
                {"speaker": "nar", "text": "音乐社留了下来。礼堂后台那台琴正式归了社团。"},
                {"speaker": "nar", "text": "暑假第一天，他抱着修好的节拍器去学校。它还是慢半拍。"},
                {"speaker": "nar", "text": "她接过去拧了两圈，说：能走。"},
                {"speaker": "nar", "text": "他憋了一路的话，最后没说。她也没问。"},
                {"speaker": "nar", "text": "两个人坐在礼堂后台的台阶上，把节拍器拨到零，又拧回去。"},
                {"speaker": "nar", "text": "弹错的音，也还在曲子里。"},
            ],
            "choices": [],
            "mood": "warm",
        },

        "t8_end_a": {
            "lines": [
                {"speaker": "nar", "text": "分班名单贴出来那天，她才知道，家长签字那一栏被改回了「物化生」。"},
                {"speaker": "nar", "text": "礼堂后台的琴被搬回仓库，旧谱架堆在楼梯间。"},
                {"speaker": "nar", "text": "分班后走廊擦肩，她低头走过去，手里抱着一摞新课本。"},
                {"speaker": "nar", "text": "他口袋里是那张手抄谱，折痕已经磨白了。"},
                {"speaker": "nar", "text": "不是每首曲子都能弹完。"},
            ],
            "choices": [],
            "mood": "cold",
        },

        "t8_end_b": {
            "lines": [
                {"speaker": "nar", "text": "她的名字在「史地政」那一栏。他在隔壁，中间隔一行字、三个班。"},
                {"speaker": "nar", "text": "她这次没给家里打电话，自己在表上填完，交到讲台左边第三摞——就是他开学那天领书的那一摞。"},
                {"speaker": "nar", "text": "开学后走廊里撞见一次，她抱着书，点了下头就走了。"},
                {"speaker": "nar", "text": "旧琴房那台琴还在，音乐社也还在。那些事，他后来都是听同学说的。"},
                {"speaker": "nar", "text": "不是每首曲子都能弹完。"},
            ],
            "choices": [],
            "mood": "cold",
        },

        "t8_end_c": {
            "lines": [
                {"speaker": "nar", "text": "两个人最后在同一个班。"},
                {"speaker": "nar", "text": "音乐社撑到六月就散了。礼堂后台的琴被搬回仓库，谁也没留一把钥匙。"},
                {"speaker": "nar", "text": "暑假第一天，他抱着修好的节拍器在校门口等到中午。它还是慢半拍。"},
                {"speaker": "nar", "text": "她没来。"},
                {"speaker": "nar", "text": "他把节拍器放在门卫室的窗台上，走了两步，又折回去，把指针拨到零。"},
                {"speaker": "nar", "text": "不是每首曲子都能弹完。"},
            ],
            "choices": [],
            "mood": "cold",
        },

        ## ── 自由行动：唯一正文，跟月份无关，按行动 key 查 ──────────────────
        ## 短是设计，不是偷懒：同一段一个月读两三次，八个月十几遍。
        "act/attend_class": {
            "lines": [
                {"speaker": "nar", "text": "黑板右上角写着日期。前排的人把练习册翻到新的一页。"},
                {"speaker": "zeng", "text": "第三段，明天默写。"},
                {"speaker": "inner", "text": "（默写。我昨晚背到第二段就睡了。）"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "act/ask_zhoumo": {
            "lines": [
                {"speaker": "mc", "text": "那个……这道题，第三问我没看懂。"},
                {"speaker": "zm", "text": "先看例题，第七页。"},
                {"speaker": "nar", "text": "她把书推过来，指尖压在那一行上，没抬头。"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "act/study": {
            "lines": [
                {"speaker": "nar", "text": "图书馆的空调开得很低。还书车上堆着没人收拾的书。"},
                {"speaker": "inner", "text": "（练习册摊开，写了两页，第三页开始走神。）"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "act/study_with": {
            "lines": [
                {"speaker": "nar", "text": "她坐对面，两个小时没说话，笔一直在动。"},
                {"speaker": "zm", "text": "你写字太用力了，纸都透了。"},
                {"speaker": "mc", "text": "……我知道。"},
            ],
            "choices": [],
            "mood": "quiet",
        },

        "act/eat_canteen": {
            "lines": [
                {"speaker": "zzb", "text": "今天有烧腊，最后一份被我拿了。"},
                {"speaker": "mc", "text": "……你拿了还站这儿干什么。"},
                {"speaker": "zzb", "text": "等你啊，兄弟。坐。"},
            ],
            "choices": [],
            "mood": "plain",
        },

        "act/do_sport": {
            "lines": [
                {"speaker": "xia", "text": "喂，三对三，缺一个。"},
                {"speaker": "zzb", "text": "他上。他跑得慢，但是他站得住。"},
                {"speaker": "inner", "text": "（球衣湿透了，风一吹，背上凉。）"},
            ],
            "choices": [],
            "mood": "hot",
        },

        "act/watch_basketball": {
            "lines": [
                {"speaker": "nar", "text": "他跳起来的时候裤腿甩到膝盖，落地没站稳，球还是进了。"},
                {"speaker": "zzb", "text": "看见没有！这球。"},
            ],
            "choices": [],
            "mood": "hot",
        },

        "act/rest_dorm": {
            "lines": [
                {"speaker": "nar", "text": "上铺的箱子堆到天花板。风扇转得慢，吹不动热气。"},
                {"speaker": "inner", "text": "（躺下才想起来，作业还在讲台左边第三摞。）"},
            ],
            "choices": [],
            "mood": "still",
        },

        "act/listen_piano": {
            "lines": [
                {"speaker": "nar", "text": "旧琴房的门没锁。里面的人弹到一半就停，重来。"},
                {"speaker": "inner", "text": "（我站在楼梯拐角，没上去。）"},
            ],
            "choices": [],
            "mood": "night",
        },

        "act/visit_auditorium": {
            "lines": [
                {"speaker": "nar", "text": "礼堂后台堆着谱架。那台琴推到墙角，琴盖上落了灰。"},
                {"speaker": "nar", "text": "有人来清过场，地上留着纸箱压出的印子。"},
            ],
            "choices": [],
            "mood": "still",
        },

        "act/weekend_stay": {
            "lines": [
                {"speaker": "nar", "text": "周末留校。宿舍楼里没几个人，水房的水龙头滴了一下午。"},
                {"speaker": "inner", "text": "（作业写完，趴在桌上睡了半小时。醒来天还亮着。）"},
            ],
            "choices": [],
            "mood": "still",
        },

        "act/visit_club": {
            "lines": [
                {"speaker": "zm", "text": "报名表在这儿。名字写清楚。"},
                {"speaker": "mc", "text": "……写全名？"},
                {"speaker": "nar", "text": "她低头把表收起来，没说收几个。"},
            ],
            "choices": [],
            "mood": "light",
        },
        "e_welcome": {
            "lines": [
                {"speaker": "nar", "text": "礼堂的灯一半是坏的。后台堆着没拆的纸箱。"},
                {"speaker": "zm", "text": "我站后面就行。"},
                {"speaker": "nar", "text": "名单上「伴奏」那栏空着，一直空到散会。"},
            ],
            "choices": [],
            "mood": "grey",
        },
        "e_sports_aut": {
            "lines": [
                {"speaker": "nar", "text": "跑道上的划线漆还没干。"},
                {"speaker": "xia", "text": "喂，八百米，缺一个。"},
                {"speaker": "zzb", "text": "他上。他跑得慢，但是他站得住。"},
            ],
            "choices": [],
            "mood": "hot",
        },
        "e_open_day": {
            "lines": [
                {"speaker": "nar", "text": "校门口摆着签到桌，家长手里拿着招生简章。"},
                {"speaker": "x", "text": "今天人多，别站在这儿。"},
                {"speaker": "nar", "text": "他把路让开，退到门后面。"},
            ],
            "choices": [],
            "mood": "plain",
        },
        "e_outing": {
            "lines": [
                {"speaker": "nar", "text": "大巴最后一排的窗打不开。"},
                {"speaker": "zzb", "text": "晕车的坐前面，别硬撑。"},
                {"speaker": "nar", "text": "野餐垫上全是草屑。"},
            ],
            "choices": [],
            "mood": "light",
        },
        "e_parent1": {
            "lines": [
                {"speaker": "nar", "text": "走廊摆了一排塑料凳，成绩单贴在教室后墙。"},
                {"speaker": "zeng", "text": "家长问什么，照实说，别加话。"},
                {"speaker": "nar", "text": "教室门一直关着，没人出来。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "e_newyear": {
            "lines": [
                {"speaker": "nar", "text": "教室窗上贴着剪纸，日光灯管闪了一下。"},
                {"speaker": "zzb", "text": "节目报满了，你还想上？"},
                {"speaker": "kong", "text": "这段我排到第三个，别改。"},
            ],
            "choices": [],
            "mood": "warm",
        },
        "e_spring_fest": {
            "lines": [
                {"speaker": "nar", "text": "校门口挂了两个灯笼，食堂窗口只开了两个。"},
                {"speaker": "nar", "text": "走廊里没人，教室门都锁着。"},
                {"speaker": "nar", "text": "广播放着一首拜年的曲子，放完又从头放。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "e_placement": {
            "lines": [
                {"speaker": "nar", "text": "卷子还带着油印味。"},
                {"speaker": "zeng", "text": "名字先写，写完再动笔。"},
                {"speaker": "nar", "text": "讲台上那盒粉笔没人拆。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "e_culture": {
            "lines": [
                {"speaker": "nar", "text": "展板摆在操场边上，边角翘了。"},
                {"speaker": "zeng", "text": "你们班这块字太小，重做。"},
                {"speaker": "x", "text": "我重抄一遍。"},
            ],
            "choices": [],
            "mood": "plain",
        },
        "e_sports_spring": {
            "lines": [
                {"speaker": "nar", "text": "场边放着几箱矿泉水，地还是潮的。"},
                {"speaker": "xia", "text": "三对三，缺一个。"},
                {"speaker": "nar", "text": "她先跑了一圈热身，回来的时候没喘。"},
            ],
            "choices": [],
            "mood": "hot",
        },
        "e_study_tour": {
            "lines": [
                {"speaker": "nar", "text": "高速上的指示牌一闪而过。"},
                {"speaker": "zm", "text": "到了别乱走，跟队。"},
                {"speaker": "x", "text": "手机没信号。你们谁的能打？"},
            ],
            "choices": [],
            "mood": "plain",
        },
        "e_club_fair": {
            "lines": [
                {"speaker": "nar", "text": "横幅绑在栏杆上，被风吹歪了。"},
                {"speaker": "kong", "text": "报名表在这儿，名字写清楚。"},
                {"speaker": "nar", "text": "桌上摆着没人填的表，风一吹就翻页。"},
            ],
            "choices": [],
            "mood": "light",
        },
        "e_chorus": {
            "lines": [
                {"speaker": "nar", "text": "排练放在午休，窗帘拉着。"},
                {"speaker": "zm", "text": "第二段再来一遍。"},
                {"speaker": "nar", "text": "钢琴盖上有一层灰，没人擦。"},
            ],
            "choices": [],
            "mood": "quiet",
        },
        "e_transfer": {
            "lines": [
                {"speaker": "nar", "text": "教室后排空了一张桌子。"},
                {"speaker": "x", "text": "他东西昨天就搬完了。"},
                {"speaker": "nar", "text": "窗台上有个没人带走的杯子。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "e_pledge": {
            "lines": [
                {"speaker": "nar", "text": "操场上摆了红色拱门，风把横幅吹得啪啪响。"},
                {"speaker": "zzb", "text": "站直点，拍照的来了。"},
                {"speaker": "nar", "text": "队伍从楼梯口一直排到门口。"},
            ],
            "choices": [],
            "mood": "loud",
        },
        "e_mock": {
            "lines": [
                {"speaker": "nar", "text": "后墙的倒计时牌翻到了两位数。"},
                {"speaker": "zeng", "text": "卷子收上去，别在走廊对答案。"},
                {"speaker": "nar", "text": "走廊上有人抱着卷子跑。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "e_apply": {
            "lines": [
                {"speaker": "nar", "text": "会议室摆着一排宣传册。"},
                {"speaker": "zm_dad", "text": "学医，物化生。别想那些没用的。"},
                {"speaker": "zm", "text": "我看看就行。"},
            ],
            "choices": [],
            "mood": "low",
        },
        "e_grad_photo": {
            "lines": [
                {"speaker": "nar", "text": "拍毕业照是在下午，逆光。"},
                {"speaker": "nar", "text": "有人没系校服最上面那颗扣子。"},
                {"speaker": "nar", "text": "摄影师喊了三遍「往中间靠」。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "e_final_sprint": {
            "lines": [
                {"speaker": "nar", "text": "教室的风扇开到最大，纸还是贴在胳膊上。"},
                {"speaker": "nar", "text": "黑板角落的倒计时只剩个位数。"},
                {"speaker": "nar", "text": "有人趴在桌上睡着了，没人叫。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "e_university": {
            "lines": [
                {"speaker": "nar", "text": "校门口发着带校徽的袋子。"},
                {"speaker": "nar", "text": "礼堂里在放宣传片，声音开得很大。"},
                {"speaker": "nar", "text": "她拿了一份简章，没翻开。"},
            ],
            "choices": [],
            "mood": "light",
        },
        ## ── T9–T35 主线拍（§1.2；没 key 时读的就是这几段）──────────────────
        "t9_injury": {
            "lines": [
                {"speaker": "nar", "text": "训练散了。她坐在跑道边，手按着脚踝，没站起来。"},
                {"speaker": "mc", "text": "你、你没事吧。"},
                {"speaker": "xia", "text": "没事。"},
                {"speaker": "nar", "text": "她说完站起来，走了两步，又停下。"},
            ],
            "choices": [],
            "mood": "low",
        },
        "t10_subject": {
            "lines": [
                {"speaker": "nar", "text": "选科表发下来。她在「史地政」那一栏停住，笔尖压出一个点。"},
                {"speaker": "zm_dad", "text": "物化生。学医，我跟你说过。"},
                {"speaker": "zm", "text": "……我知道。"},
                {"speaker": "nar", "text": "她把笔放下，表没有填完。"},
            ],
            "choices": [],
            "mood": "cold",
        },
        "t13_artfair": {
            "lines": [
                {"speaker": "nar", "text": "艺术节的灯暗下来，琴声从侧幕后面出来。"},
                {"speaker": "kong", "text": "是她。"},
                {"speaker": "nar", "text": "报名表上「伴奏」那一栏，还是空的。"},
            ],
            "choices": [],
            "mood": "light",
        },
        "t14_coach": {
            "lines": [
                {"speaker": "nar", "text": "教练把她叫到看台下面，说了很久。"},
                {"speaker": "xia", "text": "我知道。"},
                {"speaker": "nar", "text": "她回来的时候，把外套拉链一直拉到顶。"},
            ],
            "choices": [],
            "mood": "cold",
        },
        "t15_ask": {
            "lines": [
                {"speaker": "nar", "text": "她第一次主动站到他桌边。"},
                {"speaker": "x", "text": "这道题，你也不会？"},
                {"speaker": "mc", "text": "我、我看看。"},
                {"speaker": "nar", "text": "她把练习册放下，人没走。"},
            ],
            "choices": [],
            "mood": "quiet",
        },
        "t16_mother": {
            "lines": [
                {"speaker": "nar", "text": "电话里她母亲说了很久，她只应了两声。"},
                {"speaker": "zm_mom", "text": "你爸那边，我再说。"},
                {"speaker": "nar", "text": "她挂了电话，站在窗边没动。"},
            ],
            "choices": [],
            "mood": "low",
        },
        "t17_parent": {
            "lines": [
                {"speaker": "nar", "text": "家长会散场，她母亲在走廊里跟老师说话。"},
                {"speaker": "xia", "text": "我妈想让我走文化课。"},
                {"speaker": "nar", "text": "她说完，把成绩单折起来塞进口袋。"},
            ],
            "choices": [],
            "mood": "low",
        },
        "t18_half": {
            "lines": [
                {"speaker": "nar", "text": "放学路上，她讲家里的事，讲到一半停住。"},
                {"speaker": "x", "text": "算了，不说了。"},
                {"speaker": "nar", "text": "她踢了一下路边的石子，又往前走。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "t19_club": {
            "lines": [
                {"speaker": "zeng", "text": "社团批了。社长，你来当。"},
                {"speaker": "zm", "text": "我？"},
                {"speaker": "zzb", "text": "社长，收不收男生？"},
                {"speaker": "zm", "text": "收。但你不许偷弹。"},
            ],
            "choices": [],
            "mood": "light",
        },
        "t20_quit": {
            "lines": [
                {"speaker": "nar", "text": "队里有人要她退，他站在门口没让开。"},
                {"speaker": "mc", "text": "她、她没说不跑。"},
                {"speaker": "nar", "text": "她在他身后，一直没有说话。"},
            ],
            "choices": [],
            "mood": "hot",
        },
        "t21_transfer": {
            "lines": [
                {"speaker": "x", "text": "我可能……要转走。"},
                {"speaker": "mc", "text": "转、转去哪。"},
                {"speaker": "x", "text": "还没定。"},
                {"speaker": "nar", "text": "她说完，低头笑了一下。"},
            ],
            "choices": [],
            "mood": "cold",
        },
        "t25_hall": {
            "lines": [
                {"speaker": "nar", "text": "音乐厅门口，她盯着节目单右下角那行小字。"},
                {"speaker": "zm", "text": "你说，我要是学这个。"},
                {"speaker": "nar", "text": "她没说完。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "t26_entry": {
            "lines": [
                {"speaker": "nar", "text": "体育单招报名表放在她桌上，压了一整天。"},
                {"speaker": "xia", "text": "我还没想好。"},
                {"speaker": "nar", "text": "她嘴上这么说，表已经填了一半。"},
            ],
            "choices": [],
            "mood": "plain",
        },
        "t27_watch": {
            "lines": [
                {"speaker": "nar", "text": "她看着另外两条线，什么也没评价。"},
                {"speaker": "x", "text": "她们都挺好的。"},
                {"speaker": "nar", "text": "她说的是别人。"},
            ],
            "choices": [],
            "mood": "still",
        },
        "t28_form": {
            "lines": [
                {"speaker": "zm_dad", "text": "志愿表，你自己想清楚。"},
                {"speaker": "zm", "text": "……我想填这个。"},
                {"speaker": "mc", "text": "我、我支持她。"},
                {"speaker": "nar", "text": "她父亲看了他很久，没说话。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "t29_exam": {
            "lines": [
                {"speaker": "nar", "text": "单招考试那天，她没有告诉他。"},
                {"speaker": "nar", "text": "他是从别人嘴里知道的。"},
                {"speaker": "xia", "text": "考完了。"},
                {"speaker": "nar", "text": "就这三个字。"},
            ],
            "choices": [],
            "mood": "low",
        },
        "t30_offer": {
            "lines": [
                {"speaker": "nar", "text": "他桌上多了一个没署名的小东西。"},
                {"speaker": "nar", "text": "一张折好的纸，里面是修好的琴弦。"},
                {"speaker": "x", "text": "不是我。"},
                {"speaker": "nar", "text": "她说完就走了。"},
            ],
            "choices": [],
            "mood": "quiet",
        },
        "t32_choice": {
            "lines": [
                {"speaker": "xia", "text": "我做完决定了。"},
                {"speaker": "mc", "text": "什么决定。"},
                {"speaker": "xia", "text": "不用你回答。"},
                {"speaker": "nar", "text": "她说完，转身跑进雨里。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        "t33_last": {
            "lines": [
                {"speaker": "x", "text": "这三年，谢谢你。"},
                {"speaker": "mc", "text": "你、你要走了？"},
                {"speaker": "x", "text": "嗯。"},
                {"speaker": "nar", "text": "她没回头。"},
            ],
            "choices": [],
            "mood": "cold",
        },
        "t34_gaokao": {
            "lines": [
                {"speaker": "nar", "text": "高考。考场外面的树一动不动。"},
                {"speaker": "zeng", "text": "名字先写，写完再动笔。"},
                {"speaker": "nar", "text": "这一回，没有人再问第几名。"},
            ],
            "choices": [],
            "mood": "tense",
        },
        ## 自由段时间拍：现在剧本走 ai_free_scene/act/*，这两条只作测试与旧调用点的兜底。
        "t36_end_other": {
            "lines": [
                {"speaker": "nar", "text": "三年过去。"},
                {"speaker": "nar", "text": "分班名单贴出来那天，有人在楼下站了很久。"},
                {"speaker": "nar", "text": "后来谁都去了自己该去的地方。"},
                {"speaker": "nar", "text": "不是每首曲子都能弹完。"},
            ],
            "choices": [],
            "mood": "still",
        },

    }

    ## 撑不住时的最后一道：一句中性占位，绝不编剧情。
    _EMPTY_TEMPLATE = {
        "lines": [
            {"speaker": "nar", "text": "这一段先走本地文本。"},
            {"speaker": "inner", "text": "（需要在 ai/fallback.rpy 里给这一拍补一条模板。）"},
        ],
        "choices": [],
        "mood": "",
    }

    def template(beat_id, choice_path=""):
        """按 拍内分支 → 行动通用 → 拍默认 的顺序取一段文本。"""
        keys = []
        if choice_path:
            keys.append(beat_id + "/" + choice_path)
            keys.append("act/" + choice_path)
        keys.append(beat_id)
        for k in keys:
            t = FALLBACK.get(k)
            if t:
                return t
        return _EMPTY_TEMPLATE
