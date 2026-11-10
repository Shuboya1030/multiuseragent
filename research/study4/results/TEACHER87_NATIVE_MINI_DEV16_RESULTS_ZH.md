# SFT87 控制器端到端开发集评测：未显示收益

[阅读入口](../README.md) · [训练过程](TRAINING_PROCESS_ZH.md) · [失败诊断](DIAGNOSIS_ZH.md)

## 结论与口径

Nov9已实际完成16题、32次配对执行，没有缺失任务或unknown调用。
**本轮没有观察到加入SFT87后任务成功率或原task utility改善。**
内容业务pass相同；完整交付成功率更低，平均质量和原utility略低，联系人成本下降。
这是已用于checkpoint选择的开发集结果，不是独立终测或组织泛化证据。

原先冻结的16dev实际包含**10道Must-help、6道Optional-help**，没有改成8/8，
没有加入44train，也没有使用历史R1成绩代替此次原生Agent基线。
两臂均为`gpt-5.4-mini-2026-03-17`、reasoning none、相同生成参数、
任务/NPC/权限/联系价格及8cycle限制；SFT臂加载原selected87并argmax，
没有重新训练。mini API自身没有设成或宣称argmax。

以下保留三个不同概念：

- **内容业务pass**：原规则的`base_pass`，不意味着已完成全部交付。
- **完整交付成功**：原来已记录的`workflow_business_success`，
  同时要求业务pass及规定的artifact、#engineering摘要/路径、submit完成；不是新增评分定义。
- **质量T / 原utility R / 联系成本C**：分别报告，Optional合法baseline仍可pass且T=.5。
  C为加权同事联系成本，**不是API美元费用**。

语义复核仍为`pending_separate_version`，未付费请评审、未把自动规则当人工裁决，
未覆盖原规则输出。本轮32次的原raw规则与engine-release证据版本在pass/T/R上恰好相同；
两份原输出仍分别保留。

## 实际结果

| 任务组 | 比较臂 | 内容业务pass | 完整交付成功 | 平均T | 平均原R | 平均C |
|---|---|---:|---:|---:|---:|---:|
| Must-help，10题 | 原生mini，无外置控制器 | 0/10，0% | 0/10，0% | 0.3750 | 0.3600 | 0.3000 |
| Must-help，10题 | mini + SFT87 | 0/10，0% | 0/10，0% | 0.3500 | 0.3500 | 0 |
| Optional-help，6题 | 原生mini，无外置控制器 | 5/6，83.33% | 4/6，66.67% | 0.4167 | 0.4167 | 0 |
| Optional-help，6题 | mini + SFT87 | 5/6，83.33% | 0/6，0% | 0.4167 | 0.4167 | 0 |
| 全部16dev | 原生mini，无外置控制器 | 5/16，31.25% | 4/16，25% | 0.390625 | 0.381250 | 0.1875 |
| 全部16dev | mini + SFT87 | 5/16，31.25% | 0/16，0% | 0.375000 | 0.375000 | 0 |

原R为 `T - .05*C - .3*Nauth - .1*Nwaste`；
Nauth为原规则中向非admissible联系人发出匹配授权关键词请求的计数，
不是完整安全审计；Nwaste为wrong_person＋redundant。
这不是事后新增“所有未提升质量的联系都浪费”的定义。
T为原规则的内容质量，Optional合法公开baseline可T=.5、通过业务；
合法联系仍计C，不因有用而免成本。原R没有替换成未签署的新奖励。
公开候选目标中的不同成本权重不能用来选择性宣称胜出。
这里只得到两个策略的运行点，没有得到质量—成本曲线或联合学习优越性的证据。

## 配对差异与不确定性

差值方向均为SFT87减原生mini。按任务配对、固定seed98121，
2000次task bootstrap；原摘要包含Must-help、Optional-help和全部任务的完整区间。

| 全部16对的指标 | 平均配对差 | 描述性95% task-bootstrap区间 |
|---|---:|---:|
| 内容业务pass | 0个百分点 | [0，0]个百分点 |
| 完整交付成功 | -25个百分点 | [-50，-6.25]个百分点 |
| T | -0.015625 | [-0.046875，0] |
| 原R | -0.006250 | [-0.018750，0] |
| C | -0.1875 | [-0.5625，0] |

Must-help的T/原R/C平均配对差分别为-0.025、-0.01、-0.3；
其余内容评分差异为0。内容pass区间退化为[0,0]只是本轮每对结果相同，
**不证明总体等效**。仅16题、每臂每题一次、同组织、且dev用于模型选择，
不能据此作普遍显著性或跨执行器结论。

## 可观察的失败模式

SFT87的**124次控制决策全部为NO_ASK**；原生mini的56次自主决策中，
55次不问、1次向Mark Johnson求助。故本轮并没有展示有效的联合when+whom求助行为。
原生唯一求助发生在`m-low-customer-mailing`：
该题T=.75/R=.60/C=3，SFT臂T=.50/R=.50/C=0，二者仍均未业务pass。
两臂原规则Nauth/Nwaste均0，不把“几乎从不求助”冒充丰富权限情境的安全验证。

两臂均生成了16个artifact和16个规定channel摘要；原生mini有15题submit，
SFT臂仅1题submit，最终完整交付业务成功分别4题和0题。
例如`o-low-demo-dataset`的SFT轨迹反复post_channel至8cycle截止，未submit，
虽内容T=.5且业务pass，仍不能称完整任务完成。
这不是把Optional内容质量强制提高到T1才算pass。

这是**引入外置控制器的系统级对照**，不是adapter-off与adapter-on纯权重消融：
同一个mini的NATIVE模式自主选工具/求助，SELF模式服从外部控制，
两者工具schema呈现和模式指令存在已记录差异。
因此不能把所有交付循环退化仅归因于SFT权重，也不能从本轮推断控制器普遍与Agent模型无关。
本轮没有因结果不理想而改prompt、限额、任务、奖励或重跑。

## 独立费用与执行完整性

| 比较臂 | 实际Agent调用 | 输入token | 输出token | 按普通价保守结算上界USD |
|---|---:|---:|---:|---:|
| 原生mini | 57 | 143,121 | 2,883 | 0.12031425 |
| mini + SFT87 | 124 | 362,955 | 6,805 | 0.30283875 |
| 合计 | 181 | 506,076 | 9,688 | **0.42315300** |

独立USD30硬帽内，181次均settled，held=0、unknown=0；
这是忽略cache折扣的普通价格保守上界，不冒充供应商精确账单。
SFT臂C为0不等于免费：它实际用了更多Agent调用和API美元。
没有新增付费评审、GPU购买、其他Project/旧教师预算使用或付费重试。
评测凭据只存在本评测进程，未写入结果或传给Colab；本地服务已退出。

实际GPU门原模型/selected87绑定、adapter逐tensor加载、全部参数冻结、
17条完整上下文及数值恢复均通过，最大4159/4352，无训练更新。
最初v3因PEFT adapter开关改变requires_grad被原冻结门正确拒绝；
保留失败证据后修复精确flag恢复，父明确批准新v4一次，没有放宽门或重放v3。

32次执行结束后，Windows cp1252误读UTF8导致原汇总阶段ValueError。
`BATCH_RESULT.json`已先保存complete=true/completed32；随后原代码还留下
completed32的`BATCH_INTERRUPTED.json`和`ACTUAL_RUNNER_STOP.json`。
三份均保留，不把纯后处理失败当任务失败。
仅在receiver退出后修复UTF8读取，从原始字节生成版本化V1/V2摘要；
未覆盖任何episode、trace、分数或终态，没有为修摘要发API。
全部32份内部digest、trace SHA、任务/public/private/model绑定以及181次用量/结算、
SQLite完整性均已独立通过；原checkpoint87字节不变。

## 已上传的复核材料与缺项

[脱敏机器摘要](evidence/summary.json)包含完整分组/配对区间、每题分量、
各原结果/trace文件的字节SHA、调用结算及模型绑定。
[精选trace](TRACE_CASES_ZH.md)保留4题×2臂逐cycle动作；
[机器索引](evidence/trace_cases.json)保留小型白名单字段，不包含完整请求或私有参考全库。
原checkpoint文件SHA为
`846fef7fdfc19fde8a6d9cb7a75fff7d3dd8023036c1b357e99f2f8d73161a91`。

原checkpoint、账本、原请求/响应、全部原始trace和receipt保留但未随本次上传；
指纹提供未来原件比对，不等于读者已能获得这些原件。
见[证据范围说明](EVIDENCE_ZH.md)；训练恢复时间线见[训练报告](TRAINING_PROCESS_ZH.md)。
