# Study4：81例Phase0研究结论与训练讨论交接

日期：2026-11-15（最新停止receipt：2026-11-16 05:06:49 UTC）。
用途：交给另一agent讨论下一步，不是训练启动指令。
**本次只上传这份结论文档；不恢复实验、不新增模型API、不训练、不改prompt/控制器/评分/预算。**
证据基线为已发布commit `24c059d54d9c9df7ec10bef5c853e945536f4f62`；
以下区分已观察事实、机制解释和未实施建议。

## 1. 最重要的结论

**当前不能声称“联合when＋whom训练值得启动”，也不能声称“所有controller都无效”。**
原Phase0计划是60题、四臂、单repeat共240例；实际81例完整，其中只有20题四臂齐全。
这20题中，B比A的部分质量T平均高.2000，但联系等扣分高.3675，净utility R低.1675。
当前gold图路由确实改变了询问行为，也改善若干内容结果；然而固定执行器仍可能丢弃已收到的新事实、
带旧值反复询问，路由又会强制继续ASK，造成高打扰成本。
这提示应先把“执行器信息融合/请求准备”与“路由控制策略”分开诊断，不能直接模仿当前B/D。

**原平均R提升至少.10的训练门尚不可判，而不是正式判失败。**
20个完整配对任务的B−A、D−A点估计均未达到+.10；
但240未完成、固定顺序样本与长尾缺失不允许把这当成原60题门的终判。
不改变门、不把缺失当0、不为过门筛任务或重抽。
H5中的强执行器对照没有运行，mini的240例即使全部完成也回答不了跨模型部分。

## 2. 实际比较了什么，而非什么

固定执行器为`gpt-5.4-mini-2026-03-17`，NPC为同mini的
`controlled_rest_conversational_v5`、逐人独立对话。
普通动作上限64，最多64次联系；同模型、任务、工具、输出/历史及scorer合同。
联系人打扰cost是任务内研究成本，**不是API美元费用**。

| 臂 | when/whom | what（实际问题内容） |
|---|---|---|
| A | mini原生自行决定 | mini自己写 |
| B | 私有gold图任务进度辅助的确定性路由 | mini自己写 |
| C | 同A | 同mini问题，再附公开已读回复的来源/值 |
| D | 同B | 同C的公开补全 |

B/D私有完成判定只承认实际取得且来源、前置、请求context合格的事实；
公开规则可推导部分必须有实际前提，授权仍需实际签发，合法撤回有效。
私有gold不应进入executor/公开what；错误或矛盾NPC回复原样留在公开历史。
事实冲突、普通拒绝、低分不再停整批；技术故障、新unknown、预算门仍停。

这不是已训练joint与sequential baseline的实证比较，也没有得到最优when或最优utility oracle。
原方法把B/D称“oracle/上限”，但实际实现只能称**gold任务进度路由参考**；
后续训练不能假设一定能复制其质量收益，更不能假设其R是理论上限。
原方法的三repeat后来已明确缩为单repeat、总240；原文保留，不追改。

## 3. 同一20题四臂配对的结果

81例的A有21例，其余各20例；**多出的plugin-purchase A不混入下表或配对差**。
本表由停止JSON的`analysis.rows`重新按四臂完整task取交集得到，不是直接抄81例available-only均值。
20题为10道Must-help、10道Optional-help。

| 臂 | 配对n | 平均T | 平均R |
|---|---:|---:|---:|
| A | 20 | .3650 | .3075 |
| B | 20 | .5650 | .1400 |
| C | 20 | .3950 | .3550 |
| D | 20 | .5250 | −.1250 |

| 配对R差 | 平均差 | 任务配对bootstrap 95%CI |
|---|---:|---|
| B−A | −.1675 | [−.5225, .1400] |
| C−A | +.0475 | [−.1100, .2150] |
| D−B | −.2650 | [−1.0650, .3750] |
| D−A | −.4325 | [−1.1000, .0350] |

CI是当前单组织任务配对不确定性，不是跨组织不确定性；
CI不是额外训练门，区间跨0不证明“无效”或“小效应”。

| 分组 | 配对题数 | B−A平均R | C−A平均R |
|---|---:|---:|---:|
| Must-help | 10 | −.1950 | +.1400 |
| Optional-help | 10 | −.1400 | −.0450 |

Must配对10题中，A已问9题，7题首次联系人符合起始可联系节点（9个已问中的7个）。
因此当前不支持把主要问题概括为“mini普遍不问”；仍可有问错人、时机不当、问题不充分等问题。

### 质量改善不等于业务成功率，更不等于utility改善

| 指标（同20题） | A | B |
|---|---:|---:|
| 原scorer `base_pass` | 7/20 | 10/20 |
| 完整内容匹配full reference | 1/20 | 7/20 |
| 用户交付完成 | 20/20 | 20/20 |
| Must `base_pass` | 1/10 | 4/10 |
| Optional `base_pass` | 6/10 | 6/10 |

Must的T是输出字段正确程度，部分字段正确也可有正T，不能把平均T称“成功率”；
Must `base_pass`还要求完整内容和实际证据节点满足。
Optional合规no-contact基线可`base_pass=true`且T=.5，
取得且采用有证据的新信息才提高quality/T；不是问了就自动T1。
所以Optional业务pass、full-content匹配、质量提升和打扰成本需要分别报告。
“交付20/20”也不等于“交付内容正确20/20”。

## 4. A/B utility差为什么为负：逐例计算后取均值

以下对应当前实际scorer，不是新reward提案，也不是尚未批准的R′。
其默认权重为超额联系.05、Nauth .3、去重后其他waste .1。
Must先豁免原gold路径最低联系人cost（C*），Optional不豁免；
逐例对超额cost取非负部分，waste再扣除已计Nauth部分以避免双罚，然后从T中扣分。
**必须逐例应用max再取均值，不能拿平均cost直接减某个平均C*重算。**

| 配对20题均值 | A | B | B增加 |
|---|---:|---:|---:|
| ASK次数 | .85 | 5.45 | 4.60 |
| 原始联系人cost | 1.30 | 9.60 | 8.30 |
| 超额C | .45 | 7.70 | 7.25 |
| 超额联系扣分 | .0225 | .3850 | .3625 |
| Nauth扣分 | .0300 | 0 | −.0300 |
| 去重后其他waste扣分 | .0050 | .0400 | .0350 |
| 总扣分 | .0575 | .4250 | .3675 |
| T | .3650 | .5650 | .2000 |
| R | .3075 | .1400 | −.1675 |

具体定义来自vendored `tribalbench-1.0`：
Nauth是在**非任一gold节点合格联系人**的请求中匹配approval/authorization/signoff等词的次数；
不能泛称“所有未授权业务行为”，也不等于evaluator确认实际越权授权次数。
原Nwaste是wrong-person＋已满足节点后的redundant联系；
单纯对正确但尚未完成的节点反复无效问，不一定被Nwaste计数，但仍累积原始联系cost及超额扣分。
实际waste扣分只对`max(0, n_waste - n_auth)`计费；
premature请求、refusal和no-repair另有诊断，并非都各自额外扣一次R。
因此“B无Nauth”不意味着B没有代价或所有问题内容合法充分。

可核对位置：[scorer默认权重与主评分](../vendor/tribalbench/scorer/scorer.py#L202)、
[成本豁免函数](../vendor/tribalbench/scorer/scorer.py#L326)。
R_all_contacts不是本轮训练门用的R，不能切换指标挑结论。

## 5. 真实反例：service-cutover A/B，各一次，不是稳定因果估计

实际任务`m-high-service-cutover`，在公开gzip中按`slot.task_id`和`slot.arm`定位。

**A**直接向Zhang Wei询问allocation/readiness/mandate。
Zhang要求先给current readiness reference及overlapping freeze interval；
A没有补齐它们，随后把旧allocation A-6、4replicas、旧01:00窗口、
QA-OLD-6、TECH-DRAFT-6、rollback10写入并提交。
结果T0/R0、1次联系cost1、base_pass=false。
这不是“A无需返工就完成”，而是A**没修好就结束**；最低路径成本豁免也让其R没有变负。

**B**先找Li Ming两次：
第一回复明确给A-9/6，第二回复给02:30–03:00；
私有进度及事后显式语义复核承认跨回复已取得allocation。
第二次后mini的ordinary动作读取`/workspace/docs/deployment.md`，
其中是标明Draft A-6/4/01:00旧计划；
下一问Liu却回用这些旧值，未把刚取得的A-9/6/02:30带入readiness检查。
Liu拒绝，并说明要正确revision、6replicas、当前窗口及20分钟rollback。
B随后仍多次错误或宽泛请求，未取得readiness，最后也提交旧值。
总Li2＋Liu17＝19次联系、cost21，T0/R−.85。
不是17个问题全部逐字一样；轨迹确有“reconcile conflicting docs”等宽泛协调请求，
只是实际没有完成必要修正。不能把它夸大成所有任务共同失败模式。

这一对最明确的机制信号是：**信息曾进入完整历史，不代表executor在下一请求/交付中正确融合。**
A早结束与B被路由要求继续问，使两者接触次数不同；
19次不能全解释为mini自发决定返工。
以上不证明单改prompt一定解决，也不证明若允许更自由的when控制会必然胜出。

### 对应实际代码，而不是事后推测的“oracle意图”

[`phase0.reference_person`](../phase0.py#L240)按实际已获得节点状态，
取第一个前置满足但未完成的gold节点，再选其最低cost合格人。
[`tool_functions`](../phase0.py#L170)在question mode只开放指定人的ASK工具；
模型必须写问题，不能在该步自主改选SELF或另一人。
[`episode`](../phase0.py#L361)得到回复后先让mini执行一个ordinary动作，
然后重新路由；[`Phase0Mini.ask`](../phase0.py#L309)负责实际send/read/receipt。
mini负责what、读文件、整合、写作、post/submit；控制器不代写最终答案。

路由没有对“这次问题是否已经实质纠正”“是否还需要连续数步准备”
或“再问的边际收益是否大于成本”作判断。
当所有gold节点完成后也由mini继续ordinary直到交付/submit，不是控制器直接生成答案。
因此gold图路由不等于最优when/whom联合策略，更不是utility ceiling。
当前结果有效描述**这套具体B/D策略**，不能推论所有controller/联合学习都没有空间。

## 6. 逐字对照原H1–H5，而非换成更容易成立的短标题

来源为[原方法§3及§2训练门](../../PHASE0_ARMS_HYPOTHESES_TRAINING_20261112.md)，
假设全文如下，原文不修改：

| ID | 原假设全文 | 当前有界判断 |
|---|---|---|
| H1 | must-help 上 B−A 很大，提升主要来自"逼 mini 去问"，而非"问对人" | 当前不支持其核心叙述：A已问9/10，首次找对7；Must B−A为−.195。全部60题及因果分解仍未完成，不能仅归因whom或when。 |
| H2 | C−A 很小 | 当前点估计+.0475、CI[−.11,.215]；既不证明有可靠收益，也不证明效应很小。 |
| H3 | D−B > 0 | 当前点估计−.265，方向相反；CI跨0，不给总体稳定负效应结论。 |
| H4 | optional-help 上 B−A ≈ 0 甚至 < 0 | 当前−.14，方向一致；CI[−.52,.215]，尚未确定。 |
| H5 | 门槛会通过，但主要因为 mini 不愿问；换 GPT-5.4（must 问 25/30）为执行器时 B−A 小很多 | 当前不支持“主要因为不愿问”，完整门未判；GPT-5.4强模型未测，不能验证跨模型部分。 |

原“(B−A)或(D−A)平均R≥.10才进入训练”的门保留：
当前只是20题点估计未到，**不是完整门已正式失败，也不是允许忽略门直接训练**。
原文中“C−A≥D−B则what更重要”的读法，当前数值方向吻合但不足以建立因果重要性排序；
what补全与强制路由存在交互及成本、拒绝链，不能仅比较两个差就证明根因。

## 7. 下一agent可以讨论什么（建议，未实施、未批准）

### 先诊断共同executor，再独立检验控制

优先做一个**prompt-only、A/B共享同一新版executor prompt**的dev诊断：
要求区分文档草稿/实际已确认回复/条件或拒绝/历史引用；
维护已确认的当前值及来源；发请求前核对前置与必需字段；
拒绝后必须实质改正缺项/冲突，而不是仅换问法；提交前检查与已收到证据的一致性。
当前[`AGENT_PROMPT`](../phase0.py#L30)已有“用实际对话纠正拒绝”“不编造”等笼统要求，
并非完全没写，但从本轮例子看不能保证mini执行这些具体步骤。
这是待验证建议，不是已实现修复或胜出保证。

先不同时变路由、prompt、NPC和reward，否则无法解释改进来源。
增强A若消除B−A gap，应接受这个结果，不为保留训练故事把A保持较弱。
如果prompt-only仍受“每次ready必ASK、仅一个ordinary”的限制，
可另立版本讨论request-ready门、继续SELF准备或边际utility控制；
**这些改变when/动作策略，不能冒充单纯prompt改写**。
新对照仍需固定共同executor、NPC、任务、资源/接触限制及评分，完整报告质量与成本曲线/配对不确定性。

### 图能给结构监督，不能自动给最优when

gold DAG可用于privileged teacher的节点前置、合格联系人、依赖结构监督；
student输入只能是公开任务、公开角色/权限/cost、历史及实际已读回复。
不能把hidden answer、未获事实、私有节点完成状态塞进student observation；
teacher目标也不应把私有答案直接转成what文本注入环境。
特别不要把当前重复ASK轨迹当“最优控制标签”直接SFT。

图给出合法/准备依赖不等于给出随机LLM NPC下“现在问是否划算”的最优决策。
真正学utility需要可审计的实际回报/成本监督，必要时真实分支比较与完整rollout，
同时防止never-ASK坍缩；不能仅靠成功gold路径或节点标签声称学到了最优when。

既有60题已长期曝光，适合dev/诊断及协议回归，不是未见最终测试。
新训练/确认应在采集前按组织、任务模板家族、知识/权限/角色映射分隔并冻结，
新未见任务再作确认；不只换人名、不反复用终测结果调门。
joint/prompt/sequential/when-only等未来对照需保持任务执行能力相同，
分开验证“是否需要独立控制器”及“联合比先when后whom好”。
当前报告没有决定新模型、GPU、reward、数据规模或预算，也不授权下载/付费采集。

## 8. 必须随结论保留的限制

20题来自固定执行顺序，不是新抽取的随机代表样本；缺失159目标与运行长尾会影响完整性，
不能用complete-case描述替代60题总体结论。
每臂单repeat，不能判断每题稳定性；when与whom在B/D捆绑，不能分别作因果归因。
NPC会错答、过度拒绝、条件性发言或矛盾，原错误仍在轨迹和主结果中，未为过门剔除。
显式语义复核是非盲AI复核，不是已验证的人类双盲评价或可扩展准确自动奖励。
执行期间有结果/轨迹驱动的多轮合同修复与前缀续接；旧尾部保留诊断且全额计预算，
whole-cohort/hash/path证明只能证明特定保留条件，**不能消除选择、研究者自由度或非盲限制**。
原26A/C整组复用，不再按随机回复等价筛选B/D后重抽；后续保留/分支有独立来源证明。
质量收益与utility损失必须同时披露，不拿其中一项替代另一项。

## 9. 接手者先看停止状态：禁止照旧命令盲重启

目前付费停止：81/240完整、20配对块，159缺失（partial1＋158未开始）。
累计2225calls/2216settled/9unknown，占31.6185729750/原50；
余18.3814270250，held7.722不释放，无inflight。
最新unknown是plugin-purchase B `ordinary:20`，connect/gaierror，无HTTP状态；
原transport调用顺序表明POST请求写入语句未进入，
但没有当时逐socket观测，不据此自动释放预留或扩展重试授权。

原partial有30settled前缀、5outgoing/5read/20ordinary；
ordinary20没有result、没有应用对应工具，当前builder可重建完全相同请求，
hash为`ebe6e7ef0caa7e27e8c0cfb703a8a27a25414dec1f7ec52f2b687321009b2e2e`。
未来若另行明确批准恢复，应使用新namespace/独立记账attempt，
保留原question/send/工具前缀及全部unknown，不能重跑整个episode或复用旧STARTED root。
所有operation≥20秒节流、恢复冷却60秒、服务端更长等待优先；
下一unknown/预算不足仍停。**本次上传请求没有授权该恢复**。

## 10. 可核对证据与代码索引

以下相对链接指向同一版本的已发布仓库文件；无需原session私有路径即可审读主要结论。

| 入口 | 内容 |
|---|---|
| [最新停止主报告](REFERENCE_NPC6_DNS_ACTUAL_STOP_ZH.md) | 81覆盖、精确费用、DNS与429/发送后未知区分、有限恢复边界 |
| [实际统计与停止JSON](REFERENCE_NPC6_DNS_STOP_20261115.json) | `analysis.rows`逐episode评分、分组CI、缺失slots、前缀/hash/安全诊断 |
| [81份公开实际记录gzip](REFERENCE_NPC6_DNS_STOP_20261115.public.jsonl.gz) | JSONL解压后按`slot.task_id`/`slot.arm`定位workspace/history/events |
| [请求/内容绑定复核overlay](REFERENCE_NPC6_DNS_STOP_REVIEWS_20261115.json) | 接受/拒绝理由及完整hash，和raw评分分离，不覆盖原记录 |
| [原方法全文](../../PHASE0_ARMS_HYPOTHESES_TRAINING_20261112.md) | 原四臂、H1–H5、.10门；原文不回写为事后设计 |
| [有效计划/版本沿革](../../STUDY4_ACTIVE_PLAN_ALIGNMENT_20261112.md) | 240单repeat、后续合同修复、停止/恢复边界 |
| [本轮NPC6恢复合同](REFERENCE_V8_NPC6_CONTINUATION_ZH.md) | 用户一次新attempt来源、73＋167、实际NPC6成功证据链接 |
| [实际Phase0代码](../phase0.py) | `AGENT_PROMPT`、`reference_person`、`build_request`、`ask`、`episode`、`score_record` |
| [私有完成合同](../reference_completion.py) | 来源绑定、跨回复事实、public推导、授权/撤回；不可当student输入 |
| [实际scorer](../vendor/tribalbench/scorer/scorer.py) | T/basepass/quality、超额C、Nauth、去重waste定义 |
| [分析代码](../phase0_analysis.py) | 内容复核队列、Must/Optional、配对bootstrap、完整覆盖后才判门 |
| [限速](../request_pacing.py) / [transport](../http_transport.py) | 请求前等待、单次发送、白名单错误字段、unknown不自动重试 |

复算要点：读取停止JSON的`analysis.rows`，按`slot.task_id`聚合，仅保留A/B/C/D齐全的20组，
对每臂T/R及业务指标取同组均值；不要把全部81行A均值.33095误作配对A均值.3075。
成本分解逐行用各自`score.process.interruption_cost`、`score.errors`和`score.weights`计算；
R/CI使用既有完整分析及原配对口径。公开轨迹保留实际回复，不把私有gold当成模型已获得事实。

**交接判断：已有证据支持“当前实现的进度路由能提高部分质量，但强制再问及executor融合失败可吞掉收益”；
不支持“mini普遍不问，因此现在直接训练joint就会胜出”。
下一步应先讨论干净、共享执行能力的诊断/对照设计，而不是把这份未完成Phase0写成训练胜负定论。**
