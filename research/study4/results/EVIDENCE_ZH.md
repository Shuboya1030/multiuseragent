# 证据范围、脱敏与复核边界

[阅读入口](../README.md) · [训练](TRAINING_PROCESS_ZH.md) · [评测](TEACHER87_NATIVE_MINI_DEV16_RESULTS_ZH.md)

本次向公开仓库发布的是**研究报告与有限证据摘要**，不是完整可复跑包。
文档基于已经完成的真实训练/32次评测和只读离线诊断；发布本身不运行模型、不改分。

## 已上传

| 文件 | 读者可复核的内容 |
|---|---|
| [summary.json](evidence/summary.json) | 训练各阶段指标、230/62标签/阶段/类别计数、数据/配置/模型指纹、评测分组/配对区间、32题臂结果、181调用结算摘要、64个原文件SHA |
| [trace_cases.json](evidence/trace_cases.json) | 4题×2臂44cycle的小型索引：合法动作、实际动作、全部已有label概率、分差、公开状态计数、工具摘要、事件行号和原trace SHA |
| [四例trace文档](TRACE_CASES_ZH.md) | 人可读逐cycle表、原工具参数**节选**、唯一NPC回复、各臂终态、概率表及原件来源标识 |
| [publication_manifest.json](evidence/publication_manifest.json) | Git保存的UTF8/LF文档/摘要字节SHA256及用途；不自包含它自己的SHA |

`summary.json`中的原文件hash是原字节SHA，canonical digest标为canonical对象指纹：
二者算法输入不同，不能混用。例如`MODEL_INPUTS.jsonl`文件SHA不等于dataset canonical digest。
未公开的证据只登记basename或中性archive标识，不含本机路径。
用于追溯的archive名称不是一个可点击的已上传目录。

trace文档是从**最终V2**提取出的公开版，不是原JSONL字节。
原行号1起算、事件索引0起算；每条cycle起止按实际决策事件和结果的
`steps[c].next_observation`核对。完成事件是在cycle递增后写入，不能按相同cycle值误取上一条完成事件。
早期V1提取草稿有这一派生索引问题，未在本次发布。

**原trace SHA仅用于将来比对原trace；不是节选或脱敏文本的SHA。**
公开文件自己的SHA单独在publication manifest登记。
该发布SHA以Git保存的LF字节为准；Windows checkout自动换成CRLF时，本地文件字节SHA可能不同。
这不改变summary中登记的历史原件hash，后者始终指历史原字节。
工具节选不补造参数，省略处有标记；实际概率为原记录，不是新增模型推理。
绝对log-score未逐cycle保存，故只报已有概率及可由其恢复的log分差。

## 没有上传

大checkpoint/base权重、完整训练样本/原教师请求、完整mini请求响应、SQLite账本、
完整私有NPC/gold参考库、含访问能力的运行脚本、依赖wheel与一次性启动文件均不在此提交。
不会上传API key、访问令牌、账户信息或本机用户名路径。
示例中的同事名称、预算/批准reference和`/workspace/deliverable.json`属于研究任务场景；
不是评测进程凭据或宿主机私人目录。离线私有事实只按案例解释最小必要信息，
明确不是当时controller输入。

因此第三方现在可检查公开表格一致性、案例动作和摘要重算，
**无法仅凭本目录独立重跑训练、完整还原环境或核验全部未公开原字节**。
尚无已发布的模型下载地址或原始数据获取接口；如后续开放，
需另行做权限/敏感信息审查并提供固定版本、获取说明及复现入口，不能假装现已齐备。

## 原始证据完整性与剩余不确定性

离线诊断前后核对了原32结果＋32 trace字节、selected87 checkpoint、
已关闭账本SHA和181条settled状态；四例44cycle/179事件定位、
45条实际mini请求响应与账本逐条一致。这里发布的是这些核对的摘要，不代替原件。
Windows cp1252问题只影响后处理读取；以UTF8原字节重建的摘要没有写回episode或改评分。
v3冻结门拒绝与v4精确flag修复记录分开保留，不把失败门冒充通过。

语义复核仍pending；自动规则与engine-release在本32次pass/T/R相同，不代表规则适用于所有语义等价形式。
没有完整62条teacher-state预测，不能补造完整混淆矩阵。
dev已用于checkpoint选择和诊断，不能作为未见终测；接口差异也未做因果消融。
本次报告不把无证据部分填成结果，不把旧R1/其他试验混成新的配对基线。
