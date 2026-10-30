################################################################################
## 人物定义
##
## 剧本里一律用这些变量，别在台词里写裸字符串。
## 外观 / 立绘表情等进 Character 的 image= 参数，等美术定稿再补。
################################################################################

define mc     = Character("XXX")                 # 主角名未定，正文暂用 XXX
define zm     = Character("周墨")
define zzb    = Character("周子博")
define zeng   = Character("曾老师")
define stu_a  = Character("同学甲")
define stu_b  = Character("同学乙")
define bro    = Character("广播")                 # 校园广播，不是人

## 人物卡 v1.1 里「待补」的 5 个 id。id 与提示词段落名一一对应（P_xia / P_kong / P_x / P_zm_dad / P_zm_mom），
## 别另起简称。x 就是温以宁，id 沿用 x 是为了不动人物卡/策划方案/README 四处引用。
define xia    = Character("夏幸悠")
define kong   = Character("孔子帆")
define x      = Character("温以宁")
define zm_dad = Character("周父")
define zm_mom = Character("周母")

## 心里独白：无声，用斜体区分
define inner  = Character(None, what_italic=True)
