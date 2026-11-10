# 失败诊断与缺陷：不是“训练跑完了，就学会求助”

[阅读入口](../README.md) · [四组逐步trace](TRACE_CASES_ZH.md) · [下一步路线](NEXT_STEPS_ZH.md)

**当前模型的求助能力没有通过检查；同时普通执行循环有独立的接口混杂因素。**
下列分析只读既有证据，没有重训、GPU推理、API调用、任务重跑或改分。
“实现事实”“支持性机制”“待检验因果假设”分别标明，避免一个多数类故事解释全部现象。

## 四组案例先看实际行为

| 案例与选择理由 | 原生mini | mini＋SFT87 | 揭示的问题 |
|---|---|---|---|
| customer-mailing：原生唯一ASK | 问Mark获当前segment/455人；仍用旧批准；post、submit；T.75/R.60/C3 | 初态NO=.7495；旧资料写/发至cap，中途无回复支持地猜segment；T.5/R.5/C0 | 首次该问却不问；一次ASK也未必完成二跳批准 |
| demo-dataset：内容合法的Optional反例 | 旧版合法；write→post→submit，T.5/pass | 同样合法内容，但write后连续post至cap，T.5/pass，未submit | 此例不是应强制多问；普通执行终止要独立修 |
| policy-citation：角色与过期线索公开 | 不问、引用旧版；T.25 | NO=.8257；ASK内Alex .0344高于维护者Priya .0208；旧值、反复post；T.25 | when与whom都未学稳，不只阈值问题 |
| research-purchase：金额/权限依赖链 | 用旧16席/9600及临时reference；T0 | NO=.8579；错误联系人Jessica排高于Wang；同样旧值，反复post；T0 | 需当前席位→金额跨阈值→Finance release，不是一律问一次 |

这是有意覆盖不同路径的四例，不是随机代表性样本或全部任务分布估计。
逐cycle公开状态、legal actions、真实工具参数节选、NPC回复、概率分差、终态和原trace指纹见[trace文档](TRACE_CASES_ZH.md)。
离线私有参考只解释复核结论，不是控制器当时可见输入。

## 1. 动作accuracy等于多数类baseline：已证实，但不能补造完整混淆

| 数据 | NO / ASK | 永远NO的accuracy | SFT87已记录accuracy |
|---|---:|---:|---:|
| train 230决策 | 192 / 38 | 83.4783% | 83.4783% |
| dev 62决策 | 51 / 11 | 82.2581% | 82.2581% |

相等本身不能证明全部62个teacher-state预测均NO；checkpoint只保存聚合指标，没有逐条预测。
但已有rollout中能找出完全相同的公开状态，直接核对其已有预测：

| 已有预测子集 | TP：ASK→ASK | FN：ASK→NO | TN：NO→NO | FP：NO→ASK |
|---|---:|---:|---:|---:|
| 16个初始状态，与教师逐字段相同 | 0 | 10 | 6 | 0 |
| 全rollout中21个不同精确匹配教师状态 | 0 | 10 | 11 | 0 |

21状态子集ASK recall=0/10、balanced accuracy=.5。全dev只有11个ASK标签；
在相同确定性checkpoint/打分路径前提下，其全量ASK recall最多1/11≈9.09%，
精确值与完整whom混淆未知。本次没有补推理。
124个rollout NO不是62条teacher-state预测，不能互相替代。

初态完全匹配而10个教师ASK全漏，说明**不能只用mini后续走偏/状态分布漂移解释失败**。
另把这10个状态的已有概率限制到ASK候选内部取最高分，与教师联系人一致只有4/10：
这是离线排名诊断，非执行过的强制ASK策略，非gold认证的whom成功率。

## 2. 后续NO步骤主导与稀疏whom标签：支持性机制，未单独确认因果

| 教师阶段 | train ASK / NO | dev ASK / NO |
|---|---:|---:|
| c0 | 27 / 17 | 10 / 6 |
| c1 | 6 / 37 | 1 / 15 |
| c2 | 2 / 41 | 0 / 16 |
| c3–7合计 | 3 / 97 | 0 / 14 |

初始状态并非NO多数；把后续“已获信息后继续执行”的步骤等权计入，NO才占83%左右。
train已读消息的99状态中89 NO/10 ASK；dev24状态中23 NO/1 ASK。
这些状态不能和“从未问、仍缺信息”的mini rollout混为一类。
按decision等权可能让长轨迹后续NO淹没关键状态，但容量、优化、编码各自贡献仍待消融。

train只有38次ASK，分布在15位联系人：Huang7、Chen Xinyi5、Emma4、Sarah4、Liu3；
Mark/Emily/Li/Alex/Sophia各2；David/Wang/Priya/Jessica Lee/Zhang各1。
Jessica Chen、Mike Chen无正ASK标签，不代表永远不应问这两位。
联系人稀疏、人名长度与固定组织映射混在一起，不能据此声称角色泛化。

标签只是教师实际合法行为：train20业务成功/23失败/1 partial，dev9/7。
例如教师在mailing两问成功，但policy本身T.75仍未pass、purchase只问Wang未完成Finance链。
**教师不是oracle；未过滤的行为模仿会复制错误和不完整依赖。**
3 epochs完成不等于收敛，也没有证据保证加epoch会修好。

## 3. label＋EOS求和长度：实现已证实，偏置影响待测

对完整action JSON＋EOS逐token log-prob求和，再做合法label softmax；
实际NO_ASK长8 tokens，多数ASK9、部分10、Chen Xinyi12。
序列长度、人名先验、EOS可能影响排序，值得分类head/等token action-ID单变量消融。
但不能说短label必胜：同mailing初态的**已有**工程probe如下。

| 模型状态 | NO raw score | Mark raw score | p(NO) | p(Mark) |
|---|---:|---:|---:|---:|
| adapter-off | -21.2795 | -18.2766 | .0333 | .6709 |
| SFT87 | -18.3050 | -19.7788 | .7495 | .1717 |

训练改变了这个状态的偏好。这只是一个旧probe，不是新增推理或完整adapter-off任务基线，
不能据此声称base整体更强。
逐cycle原始绝对分数没保存；trace有完整归一化概率，只可恢复log(p_top/p_runner)分差。

## 4. argmax与成本目标：不是近似平局，也不是RL学到“不问划算”

124次SFT决策p(NO)范围.5556–.9685，最小top-2概率差.3854、log-score差1.1135。
所有已记录状态的总ASK概率也小于NO；简单改成ASK总量>.5仍不会问。
model softmax不是已校准的任务成功/收益概率，argmax行为概率1也不是模型p(NO)。
原生API动作概率未记录，保持未知。

SFT只做CE，不用R/T/C更新。Qwen公开候选objective T−.15C与原评测R联系系数.05不同，
教师标准请求又没有额外数值objective；这些是已知条件差别，不是已证明collapse原因。
不能说“RL算出不问更划算”。改lambda、采样或降低阈值会改变策略和后续状态，
尚未获益验证；错误whom排名意味着单改when可能只增加错误联系。

## 5. mini重复post：接口不相同已证实，单一因果未证实

| 层面 | NATIVE | SELF |
|---|---|---|
| 模型/生成设置 | 同mini、reasoning none、同生成参数 | 相同 |
| mode / phase | NATIVE / decision | SELF / agent-task |
| 普通工具呈现 | required_string_arguments字段列表，另含ask_colleague | JSON-Schema式properties/type/required等 |
| 指令重心 | 自主工具/求助，save→post→submit | 恰好一个normal tool，不是整个rollout |
| normal命令路径 | 缓存实际命令后执行同一命令 | mini直接生成普通命令 |
| 可执行普通工具/次数 | 含submit，最多8cycle | 同普通工具与上限 |

完整公开历史、workspace、剩余cycle在请求里；公共documents初始已载入。
无read_file不代表没看到文档。NO_ASK允许submit，不是“重复post”的指令；
外置控制器本身没有SUBMIT动作。
NATIVE 15题submit、SELF仅1题，但不能把流程差25个百分点全归adapter：
需匹配普通接口消融才能确认prompt/schema/phase及状态路径的因果贡献。

原任务正文主要要求artifact/channel；submit是桥接协议额外的显式结束要求。
内容pass和流程成功并列保留，demo的内容pass没有因未submit被改为false。
语义复核仍pending，不应把自动规则覆盖范围夸大成完整人工确认。

## 未能从既有证据回答

全62条逐样本混淆、完整whom泛化、接口差异因果、额外epoch/采样/表示收益、
完整质量—成本曲线、独立新任务/组织泛化，均未建立。
下一步应先隔离接口、验证可拟合性和标签质量，再研究结果支持的监督及最终RL，
而不是先扩大模型或承诺续训必胜。具体产物与停止门见[下一版路线](NEXT_STEPS_ZH.md)。

公开摘要/源码指纹的复核范围见[证据说明](EVIDENCE_ZH.md)；
没有把未上传的原始文件伪装成可点击公共来源。
