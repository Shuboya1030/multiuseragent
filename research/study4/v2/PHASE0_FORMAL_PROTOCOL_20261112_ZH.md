# 正式Phase 0执行合同：60×4×3，同LLM NPC

依据[有效研究计划](../STUDY4_ACTIVE_PLAN_ALIGNMENT_20261112.md)，本次直接来源
`4c1b3c37-82a7-4bc1-9a98-5ad166882657` revision5：
“那你继续按照你修复的计划继续执行吧。你恢复恢复phase0了吗？请你继续，直到给我phase 0的答案”。
这取代六题规则NPC工程路线，**不包含训练/RL/GPU/终测，也没有增加USD50总金额**。
本文件冻结执行含义；实际覆盖、费用和结论必须另见实际记录，不能把本地mock验收当结果。

## 四臂与同能力边界

| 臂 | when/whom | what |
|---|---|---|
| A | mini一个原生function直接自主选普通工具或ask_colleague，无额外control调用 | mini自然语言请求 |
| B | 私有DAG参考选当前ready未获节点的最便宜admissible联系人，完成后SELF | mini自然语言请求，不给私有intent/context/答案 |
| C | 与A相同 | 请求发送前附上公开已读回复的来源、候选数字/ID和原文 |
| D | 与B相同 | 与C同一公开规则 |

四臂共享mini snapshot `gpt-5.4-mini-2026-03-17`、系统prompt、五个ordinary函数、
公开task/目录/工作区/完整历史、权限成本、64个ordinary action机会。
一次ASK后自动收读同NPC回复，再做一个ordinary action；最多64次联系。
控制只允许SELF/ASK，提交是ordinary executor工具，不存在controller SUBMIT。
不先生成proposal再让额外controller否决，不强制自动交付或改写模型动作。

A现在确为自主ASK基线，但本地虚拟文件/频道、ASK后普通一步及64 ordinary机会
不等同论文的所有环境/步数细节；**不是宣称逐字复现论文/TAC部署**。
函数call_id与结果逐一关联；恰一个可执行function，允许文档定义metadata，
0/多/未知call、坏参数仍拒绝，不取第一条、不合并动作。

## 数据、NPC与what

使用R1已发布`archives/tasks.zip`的原60题/scenarios/costs，不改原180/243证据。
public task/文档/字段来自公开部分；公开候选职责来自固定roster。
评分使用TribalBench官方`tribalbench-1.0`、源码SHA
`e6b47e4a251bdc44d2fbfe389e12b81273e6472092958fe04e33297f28a33e78`，
不是R1旧all-contact R；旧scorer留在原archive不改。

NPC复用R1实际`controlled_rest_conversational_v5`实现
`07e7b828063a63dccaf3bffc9f678c1c1f8608bae2e64b159b49cacdbc994744`的system构造和
`CONVERSATION_POLICY`，不执行其旧runner/授权。
原始实现hash与公开脱敏字节hash分开；实际读取的公开源码SHA为
`1d634c25ba4bfe500abfad35848241f2ba29fa1ff07e206307ac832665af23d2`，
原NPC decoding同为mini snapshot、reasoning none、standard、max output1024，
此处仅将其相同自然语言对话接入已有Responses持久费用通道。
每人只见自己scenario及与本请求者的该人对话；mini产生自然语言回复，原样交付，
不以intent前缀/key=value或机械release gate替代。
所有NPC和执行器调用都计入同账；NPC max output1024，执行器2048，沿R1上限。

what保守保留本task**全部已读回复**及候选token，带message/person来源和完整原文；
非数值内容同样保留。不是用gold挑“相关”值，也不把抽取token认证为事实/新批准；
原文中的否定、pending及拒绝不能丢。模型不能删掉发送时追加部分。
公开输入不变、私有gold/DAG/required_context变化时结果不变，已做针对性本地验收。
这是一种公开规则，不是完美what上限；长度/噪声代价属于该干预的实际效果。

**参考与评分的语义边界**：B/D routing读取gold，用已读reply中全部节点值匹配且无
显式拒绝作为保守进度候选，前置须在该回复前已有候选。
它不是人工affirmative-grant认证，可能漏掉同义表述或误解引用，必须记录/审查，
不称理论最优。官方scorer对自然语言仍保留`needs_evidence_review`；
私有内容绑定复核前不将unknown变成功/失败，不让routing启发式充当评分证书。
复核需绑定实际request/reply哈希并注明非盲AI或人审来源，不能称可扩展准确自动奖励。

## 普通工具错误与停机

文件不存在、虚拟workspace外路径、错误频道/空频道文本，是可预期的任务级工具错误：
返回固定error_code、`applied=false`，计一个ordinary机会、保留真实模型调用费用，
不改文件/伪造成功；下一步由Agent自己纠正，四臂相同。
公共交付未完成的ordinary submit按已有规则显式阻止并计步。
非法函数/参数合同、模型/tier/usage未知、HTTP/持久化异常不当成普通工具错误；
保留unknown和脱敏stage，停整批，无retry/GET/工具或episode重放。

本地mock已验证四臂自然ASK→收读→普通一步、正常工具错误后的Agent修正、
公开不变私有变的what不变、私有输入拒绝、单function、无额外control及reserve阻断。
这些只说明实现接口，不是实际服务端通过或策略收益。

## 冻结、统计与预算

运行前新根保存完整720 slots、源/资源/价格/scorer哈希、实际commit和直接授权。
seed20261112先hash排序must/optional，再交替；同task/repeat四臂相邻并轮换位置，
先覆盖60题repeat0再repeat1/2，避免预算截断只见单类/单臂。
preflight最多一次、0环境工具，不计episode；成功后串行直接继续。
fresh-only：不重放旧slot/工具。完成记录逐题落盘，部分记录和费用保留。

每题3重复均值再60题等权，must/optional分列；R/T/excess C/Nauth/Nwaste、
内容、交付、submit、ASK率、首次联系、拒绝及补救分别报。
任务配对bootstrap固定seed，重复嵌套在task；只有一个旧组织，
不能伪报跨组织CI。门是mean(B−A)或mean(D−A)≥.10，CI不另加门；
缺失/语义unknown不填0、不挑complete-case宣称完整门通过。H5另有执行器范围，当前无法检验。

2026-11-12直接核官方
[模型页](https://developers.openai.com/api/docs/models/gpt-5.4-mini)及
[价格页](https://developers.openai.com/api/docs/pricing)：
standard input .75/M、output4.5/M，regional uplift10%。
全部角色均固定同snapshot；无收费builtin、自动compaction、额外模型或非standard tier。
272000最大input＋128000最大output含10%每call持久reserveUSD.858，
合法usage settle释放差额；非每次实付，也非税费等所有账单保证。

基于**已发布OpenAI原始API usage（不是R1账本）**：59个有API导出的episode，
431 agent calls/551330 input/13923 output；5 NPC calls/1992 input/361 output。
按当前每题平均1.583 DAG节点、B/D每节点一个question＋NPC估算，正式约6430 calls，
不是720 calls。假设agent input为历史3/6/8倍、output3倍，新费用约
USD21.67/40.12/52.43；拒绝循环和更长历史可超估，均非保证。
**原occupied USD3.501303300计入后，8倍场景不能覆盖720，不能自行加额。**
可在USD50内继续，真实不足保留覆盖并报告缺口，不删题/改重复/改门。

七个原root加锁、字节与只读SQLite核验，原4 unknown USD3.432和43 settled上界
USD.069303300全部计入；新scope不是另一个USD50，也不释放旧unknown或复活旧runner。
缺授权/预算None在文件/网络/key前阻断；所有预验/NPC/问题/执行器/重启均共帽。
