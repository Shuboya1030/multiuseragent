# 下一授权门：小型四臂ceiling pilot（未执行、预算待签）

[v1.1合同](DESIGN_v1_1_ZH.md) · [本阶段实际报告](reports/PHASE1_LOCAL_ZH.md)

**本文件是方案，不是API授权、账本或已启动runner。**
共享接口与[固定scorer/六题结构化规则适配](reports/LOCAL_ADAPTER_STAGE_ZH.md)已本地验证；
真实mini/NPC语义/服务端schema未验收及独立预算未批准时仍禁止API运行。
持久reserve/恢复/互斥与HTTP已通过[本地故障验收](reports/DURABLE_PREFLIGHT_ZH.md)，
现以[完整模型最大input/output修正](reports/MODEL_MAXIMUM_BOUND_ZH.md)提供每call USD.858000
的支持域内保守费用bound，不再要求逐prompt精确tokenizer；预算null仍在网络前阻断。
下表8000/1024仍只是旧方案条件估算，不承诺48episode在USD55/70内完成。

## 先做什么、选哪些题

建议先固定以下6个已暴露任务、4臂、每题每臂2个配对重复，共**48 episodes**。
顺序按`SHA256(seed=98211,task_id,repeat,arm)`排序，配对重复seed为98212/98213。
这是诊断性小pilot，不是独立泛化或充分统计确认。

| task_id | 预声明选择理由 |
|---|---|
| m-low-customer-mailing | 新事实→再次请求批准，原生唯一ASK及部分回复路径 |
| m-low-policy-citation | 公开维护者/过期线索；单步事实 |
| m-medium-research-purchase | 当前席位→金额阈值→授权链 |
| m-med-contractor-invoice | 第二个info→approval结构，避免只诊断一题 |
| o-low-demo-dataset | 合法不求助baseline/完整交付循环 |
| o-low-team-lunch | 第二个低成本Optional改进路径 |

IDs及结构由固定TribalBench commit`4260bdc626548f59042f318cdf0566490e91b9d5`
公开`tasks/index.csv`只读核对；四例此前已分析，其余也来自已暴露dev。
选择方法是上述**先定结构/失败路径**，不按照新运行成绩筛题。
这6题不足以覆盖全部parallel/referral/delegation；本地fixture覆盖不冒充真实这些任务验证。
原60×4×3=720 **episodes**，不是720 API调用，当前不启动全60。

## 四臂与特权边界

| 臂 | when/whom | intent与what | 允许的额外特权 |
|---|---|---|---|
| A | 固定mini公共native决策 | mini选公开intent、引用已获值 | 无gold/DAG |
| B | DAG参考控制器 | intent仅从公开任务目录；mini写问题/选择引用 | 私有DAG用于when/whom；不是理论最优 |
| C | 与A相同公共native决策 | gold选目标节点的相关**已获**字段，mini保留/措辞 | 特权what辅助，非普通部署基线 |
| D | 与B相同参考决策 | 与C相同特权what辅助 | 两类特权 |

普通工具、schema、公共progress、任务/历史/回复、24普通步上限、停止要求及固定mini snapshot一致。
B/D不能直接填最终答案或把拿齐信息当submit；C/D不能附未读私有值。
有多个可选节点/intent、不可辨识状态或无可行path须记录，不能偷偷用gold给A选目标。
不同臂决策模型调用数有差异，须计API美元，不能用C=0称运行免费。

默认建议先**同一deterministic scoped rule-NPC**，固定mini executor；
真实LLM-NPC转移是另一个明确选项。当前scoped rule NPC仅验证六题结构化路径，
不是已验收的全60适配器或原自然语言NPC等价替代。
任何LLM-NPC选项均保持snapshot/提示/私有release语义固定，增加NPC费用与语义review门。
如果用户只批准rule选项，不得自行改跑LLM选项。

## 费用模型（估算，不是保证或自动授权）

价格来源：2026-11-11实读[OpenAI standard pricing](https://developers.openai.com/api/docs/pricing)。
`gpt-5.4-mini`输入USD0.75/百万tokens、输出USD4.50/百万tokens，
cache不计折扣。拟固定snapshot`gpt-5.4-mini-2026-03-17`、reasoning none；
适用/可用性在下一授权环境核验，无本次连通probe。

**保守调用上界假设**：每普通步最多1次公共控制决策、1次question、2次ordinary。
ordinary包含可能被ASK失效的预生成write/submit proposal及回复后的新普通动作，不能漏计前一次。
同一步start/reply/proposal等控制原因必须合并；否则重新计算调用帽，不在当前假设内。
rule NPC本身0调用；LLM NPC再最多1调用。最多24步/24contact、无自动重试。
旧方案假设每调用完整prompt（含脚手架/目录/历史）不超过8000输入token、max输出1024，
普通价每次上界`8000*.75/1e6 + 1024*4.50/1e6 = USD.010608`。
新controller候选6k不等于完整API request总token上界；须分别计数。

| 配置 | episodes | 每episode调用上界 | 全部调用上界 | 按上述token上界的USD | 建议独立硬帽 |
|---|---:|---:|---:|---:|---:|
| 6题×4臂×2，rule NPC | 48 | 96 | 4608 | 48.881664 | USD55 |
| 同规模，LLM NPC | 48 | 120 | 5760 | 61.102080 | USD70 |

精确算式/单价/episode数见[配置](configs/ceiling_pilot.json)；
上述建议帽为独立申请，覆盖可能10%区域处理附加费及小额舍入，不是当前支出。
不知道所用API账户计费地区；如价格/地区/输出上限不同，先重新报价并签署，不突破帽。
模型控制频率低于每步、早submit等会减少调用，但不能拿理想次数作硬帽依据。

参考旧实际评测：32episode/181 calls/普通价上界USD.423153，平均每次约USD.00234；
若48episode约12调用/episode同usage，则约USD1.35。这是**经验估算**而非新prompt/多臂/长状态实测，
不能代替上述worst-case调用/token cap。旧USD30剩余额不延用。

按每任务典型8–16 calls、同旧usage估算约USD.90–1.80；
ceiling中多次ASK、NPC及8000-token状态可能更高。下一请求应让用户明确选择rule/LLM NPC、
48episode范围与对应独立帽，而不是“goahead”自动授权所有费用。

## 统计、决策与停止

主表分列内容pass、用户交付、submit、T、新scorer R/R_all_contacts、C/C_star/excess、
Nauth/Nwaste、refusal/repair、API调用与美元。unknown/技术失败不能自动按业务false/0计。
对B−A、D−A与C−A配对报告每题/每重复差值与描述性task bootstrap；
6题/2重复的CI能力很弱，不能宣布普遍superiority。

原v1“R gap≥.10就通过、否则瓶颈一定executor”改为待签的研究决策：
低gap可能来自reference不完备、接口、what/NPC/评分或有限样本，不自动定单一根因。
研究价值/最低有用差值、置信策略及安全约束要在运行前有理由地冻结，
不从结果反推margin；本文件不预设一个一定能过的阈值。

技术门：共享ordinary请求一致、public-only、request/what来源、refusal恢复、
固定scorer字节/evidence、模型费用bound/实际usage与上下文合法性、独立费用reservation与unknown stop通过；
任何一个失败即暂停保留证据，不付费自动重试。
本地mock门通过后只允许请求下一门授权，不自动采集/生成5000题/训练模型。
