# Study 4：求助控制器训练、结果与下一步

更新：2026-11-10。**训练已完成；当前模型没有体现任务收益。**
本目录是研究报告发布，不是可直接复跑的完整训练包；原始数据、模型和请求未随本次上传。

**2026-11-11 v2推进**：[共享协议与零付费第一阶段](v2/README.md)已另立版本，
含设计v1.1/v1.2、fixture基础与六题固定scorer/四臂调度本地验收、
[USD50真实ceiling首接口停止报告](v2/reports/CEILING50_ACTUAL_STOP_ZH.md)及
[双动作真实诊断](v2/reports/SINGLE_DIAGNOSTIC_ACTUAL_ZH.md)；
**2026-11-12最新**：[原生单函数真实验收及四臂部分结果](v2/reports/NATIVE_FUNCTION_ACTUAL_ZH.md)，
真实完成A/B两题例，C本地缺文件读取停批；同一Optional题T/R从.5/.5到1/.9，
但B为特权参考，0完整四臂block，不能宣称训练收益或ceiling通过。
累计unknownUSD3.432＋settled上界USD0.069303300，仍占原USD50；
后续[controller仅SELF/ASK的职责修复](v2/reports/HELP_ONLY_REPAIR_ZH.md)已零API本地验收，
submit仍由ordinary executor产生；尚无新版真实验证或收益，原actual与费用不变。
不改下述SFT87历史结果，不代表新训练或真实ceiling已完成。

研究问题：在固定任务执行器和NPC的能力下，单独学习联合决策 **when（何时求助）＋whom（向谁求助）**，
能否比prompt或先when后whom获得更好的质量—成本权衡？这是待检验假设，不是已实现结论。

## 一分钟结论

| 问题 | 当前事实 |
|---|---|
| 训练了什么？ | Qwen2.5-1.5B-Instruct + LoRA，GPT-only教师行为模仿；3 epochs / 87 updates已完成。不是RL。 |
| 用了什么数据？ | 59条完整轨迹＋1条历史partial，共292决策；44题/230决策train，16题/62决策dev。 |
| 动作准确率如何？ | dev 82.258%，**恰等于永远NO_ASK的多数类基线**，不能作为求助能力证明。 |
| 真任务结果如何？ | 原生mini vs 同mini＋SFT87：16题/32次执行，内容pass均5/16；完整流程成功4/16→0/16。 |
| 质量和成本？ | 平均T .390625→.375；原R .38125→.375；加权联系成本C .1875→0，但API美元上界反而更高。 |
| 观察到了什么？ | SFT 124次决策全NO_ASK；16个初始状态与教师完全相同，其中10个教师ASK全被漏掉。 |
| 能否只怪控制器权重？ | 不能。NATIVE/SELF普通执行接口有差异；mini在SELF中常重复post、不submit，需要单独隔离。 |
| 是否独立终测？ | 否。60题有既往R1暴露、同17人组织；16dev已用于checkpoint选择及本次诊断。 |

箭头均为“原生mini → mini＋SFT87”。T是内容质量，R是原规则utility，C不是API美元。
完整流程指标包含桥接协议额外的submit要求，必须与内容pass并列，不能互相替代。

## 阅读顺序

1. [训练过程与成果](results/TRAINING_PROCESS_ZH.md)：模型、数据、训练目标、完整指标、恢复时间线及选中模型。
2. [端到端评测结果](results/TEACHER87_NATIVE_MINI_DEV16_RESULTS_ZH.md)：协议、分组结果、配对不确定性、费用及有效性边界。
3. [失败诊断与缺陷](results/DIAGNOSIS_ZH.md)：已证实事实、支持性机制与尚未验证的解释。
4. [四组真实配对trace](results/TRACE_CASES_ZH.md)：8条轨迹、44个cycle，看到实际动作、工具、回复与停止情况。
5. [下一版策略与实验路线](results/NEXT_STEPS_ZH.md)：优先级、阶段产物、go/no-go及新资源授权边界。
6. [证据范围与复核说明](results/EVIDENCE_ZH.md)：已上传/未上传的界限、原字节hash与摘录hash的区别。

小型机器可读证据：[训练/评测摘要](results/evidence/summary.json)、
[精选trace索引](results/evidence/trace_cases.json)、
[本次发布文件指纹](results/evidence/publication_manifest.json)。
上述旧发布manifest针对提交`3c6e8b3`的历史LF字节（包括当时README），
不用于断言随后新增导航的README字节未变；v2有独立文件指纹。

## 已做与未做

**已做**：GPT教师数据转换、public-only观察/合法动作mask、真实GPU LoRA更新与精确恢复、
SFT87端到端开发集评测、现存trace/标签/源码的零调用离线诊断。
执行器与NPC没有参与本轮训练。NO_ASK/SELF只允许执行器自主一步，不是做到结束；
ASK由执行器生成问题，发送并读取NPC回复后再自主一步。控制器不写最终答案、不伪造批准。

**未做**：三教师完整采集、最终奖励签署后的randomized offline RL、完整prompt/joint/学习型两阶段对照、
接口匹配因果消融、独立新组织终测、语义复核完成或质量—成本优势证明。
此前filtered SFT15/selected10、Joint4与learned Sequential2等工程边界在训练报告末尾单列；
它们与当前87模型不是同一数据/模型，不等于上述研究目标已完成。

下一版路线全部是**待批准、未执行**；本次文档发布没有新增训练、GPU或模型调用，
没有改变原32次episode、分数或87模型。新采集、新GPU运行和API费用须独立授权，
不自动延用已结束的USD30评测帽余额。
