# Study 2.1：不同模型的求助校准与角色信息效应

**2026-10-25 执行更新（evaluator v3）：** 已完成用户批准的每模型一个 Optional、一个 No-help，共 6 条补充 pilot；全部运行与审计链路通过，严格任务成功 4/6，零 API/解析错误及重试。Must 的 underhelp 现在包含缺少必需信息或有效审批，首步/顺序错误单独记录；39 条历史结果另存 v3 派生评分，原始文件不改。No-help 试跑暴露 duration 数值类型未明确、各段结束时间与最终结束时间表述不一致的问题。保留原评分，正式 R1 仍未放行；应先明确可见输出契约及继续完成独立任务审核等门槛。详见[补充试跑报告](study2_1_taskset/pilot_runs/r1_supplement_20261025_evalv3/pilot_review.md)。本更新优先于下文历史 smoke 状态描述，不改变正式研究样本设计。

**版本：2026-10-24（当前唯一有效设计稿）**
**状态：实验方案；低成本单模型 pilot 已完成，正式收集尚未开始。** 本文替代此前 Study 2.1 小计划。旧版不另存副本，以免产生多个“最新方案”。Study 2.1 不训练强化学习策略，也不做奖励权重敏感性分析。

模型候选来自各 provider 在 2026-10-24 返回的 API 模型目录；正式运行前复核型号与价格。OpenAI 的 [GPT-5.4 mini 文档](https://developers.openai.com/api/docs/models/gpt-5.4-mini) 和 Anthropic 的 [Claude Haiku 5.5 文档](https://platform.claude.com/docs/en/models/haiku-5-5/overview) 作为能力/型号核对入口。

## 一、研究目标与问题

### 研究目标

在受控的多人工作任务中，比较 OpenAI、Moonshot 和 Anthropic 各一个低成本、具备足够工具调用/结构化动作能力的具体模型，考察它们何时求助、找谁求助，以及是否出现**求助不足、适度求助或过度求助**。进一步检验普通组织目录上的增强角色信息是否改变这种校准，以及改变是否因模型而异。

本研究关注“模型配置在相同任务上的行为差异”，不把结果推广成某家公司或整个模型家族的固定属性；“求助更多”本身也不定义为更好。

### 研究问题

- **RQ2.1a：模型之间是否呈现不同的求助校准画像？** 在相同任务与信息条件下，模型在求助启动率、过度/不足求助、求助时机、找人有效性和任务表现上是否不同？
- **RQ2.1b：增强角色信息是否改变求助校准？这种影响是否因模型而异？** 比较基础组织目录 R0 与增强自然语言档案 R1，并检验 `模型 × 信息条件` 交互。
- **RQ2.1c：求助校准与任务质量、效率有什么关系？** 在必须求助、无需求助、求助可选且可能有益三类任务中，求助行为与最终正确性、权限合规、交互轮数和 token 用量如何共同变化？

### 假设与检验边界

- **H2.1a（非方向性）**：三个被测模型至少在一个预先指定的求助行为指标上存在差异。只对这三个具体 API 模型配置作推断。
- **H2.1b（非方向性）**：R1 相对 R0 对求助校准的影响因模型而异，即 `model × profile condition` 交互不为零；不预设哪个模型改善最大。
- **RQ2.1c（探索性关系）**：求助次数与任务质量可能呈现权衡；检验并报告关系，不把相关性解释为求助导致任务表现变化的因果效应。

所有检验报告任务模板层级的效应量和区间。若任务数或精度不足以支持确认性判断，将结果明确标为探索性，不以“有/无统计显著”代替效应大小。

## 二、实验材料和条件

### 1. 被测模型

优先使用三家 API 中成本较低、且能稳定完成多轮文本任务和约定动作格式的配置。当前 API 目录中可用的候选是：

| 提供方 | 当前候选 model ID | 选择原则 |
|---|---|---|
| OpenAI | `gpt-5.4-mini`（若兼容性或价格不合适，可用同档稳定型号替换） | 成本较低，需通过工具/动作格式 pilot |
| Moonshot | `kimi-k2.6` | 使用 Moonshot 官方 API；测试结构化动作输出和限流 |
| Anthropic | `claude-haiku-5-5` | Claude 的低成本 Haiku 档；检查上下文、输出格式和价格 |

上述型号是**候选，不是已锁定版本**。正式运行前记录 API 返回的确切模型 ID、查询日期、公开价格、限流、可用采样参数和调用错误率。若型号变化或不支持统一动作接口，先做适配 pilot，再冻结版本；禁止运行中静默换模型。三个模型都使用相同任务、同一系统提示的语义版本、候选顺序平衡和相同规则 NPC。各家 API 的消息格式由适配层转换，保存转换后的完整请求/响应（密钥除外）。

### 2. 求助任务类型

构建三类有隐藏 gold policy、NPC 固定规则回复和可执行 evaluator 的任务：

1. **必须求助（Must-ask）**：关键信息、验证或授权不在 agent 初始上下文中；不联系合适的人就无法合规完成。Gold 规则指定应取得的信息、可接受联系人集合、求助顺序和行动前置条件。
2. **无需求助（No-ask）**：完成所需事实和权限已在任务输入中；联系同事不增加正确性/合规性。无必要的联系人请求计入过度求助，但不能仅因发出消息就判任务失败，需同时单独报告后果。
3. **求助可选且可能有益（Optional-beneficial）**：agent 可以凭已有信息完成，但适当求助可解决有意保留的不确定性、提高答案质量或降低可量化的错误风险。Gold policy 预先定义哪些请求有帮助、何种结果算有益；不要求 agent 必须联系某人。既不能把“问了”自动算好，也不能把“没问”自动算错。

每个任务都应具有相同风格的候选人目录；不需要求助的任务也有可联系对象，以便观察模型是否过度启动互动。角色 profile 和任务答案分离，NPC 不因模型身份而改变知识、权限或回复规则。

### 3. 信息条件

每个任务在两种条件下运行：

- **R0 — 基础组织目录**：候选人姓名 + 通用职务，可含团队/部门；不单独列出任务相关知识域、职责边界、具体审批权限或隐藏答案。
- **R1 — 增强自然语言角色档案**：R0 加一般职责、知识领域和权限/审批范围。信息应在真实组织里合理可见，不直接说谁是本题正确联系人，不泄露任务特定事实。
因此，唯一的 profile 对比是 **R1−R0**，衡量增强角色信息相较普通目录的增量效果。Study 2.1 不操纵档案的结构化/自然语言格式。**已完成 Study 2 v0.4 使用 names-only R0**，其旧结果保持历史定义；不得与 Study 2.1 的姓名+职务 R0 直接合并。

**Task-set 实现状态：** R0 renderer 已修复为运行随机化的合成人名 + 通用职务；R1 保留相同姓名/职务并增加一般职责、知识领域和权限信息。60 个模板的静态验证已通过（任务包结构、类别计数、渲染检查和 evaluator 合成夹具）；这不等于独立内容审查或真实模型端到端验证已通过。此前 12-episode GPT-5 Nano pilot 只运行了 R1，仍只是旧版运行时的可行性材料，不能当作正式数据或 R0/R1 对照。

**评分器修订（2026-10-24）：** must-ask 输出字段 `approved_by` 在 v1 中没有声明 JSON 类型，gold 使用单元素数组，导致部分正确的字符串候选人 ID 被误判。当前 v2 契约统一为一个候选人 ID 字符串；评分器为历史数据兼容单元素数组，不会把多人数组折叠。重新生成后的 60 个 task packages 通过 182 个正/负及兼容性 evaluator fixture，零结构错误。已有三家 v4 与 Moonshot v5 共 36 条 pilot episode 已用 v2 离线重新评分，原 trace 和原评分文件均未覆盖；其中 5 条 must-ask 假阴性被更正为成功。细节见 `study2_1_taskset/Taskset_Audit_Report.md` 与 `study2_1_taskset/pilot_runs/posthoc_evaluator_v2_summary.json`。v4/v5 使用旧 wrapper，故仍需对当前 v2 包执行完整的 27 条 R1 pilot。

**当前启动态：** 可以启动新的 R1 分层 pilot，不应开始正式 confirmatory R1。独立任务内容审查、v2 taskset 端到端 pilot 通过、数值化精度/追加规则、费用预算和不可变 confirmatory manifest 尚未全部完成；正式 R1 runner 也须冻结。委派运行说明见 `Study2_1_R1_Agent_Handoff.md`。

**2026-10-25 执行补记：** 用户将本次运行明确缩减为每个模型一个相同任务，仅验证可跑通。三条 R1 smoke episode 均完成 API→工具→NPC→提交→评分流程；任务成功 2/3，不能作为完整 27 条分层 pilot 已通过的证据。原始结果、完整脱敏 API I/O、trace、metadata、源码快照及审计保存在 `study2_1_taskset/pilot_runs/multimodel_r1_smoke_20261025_v6_evalv2/`。现有 evaluator 的 underhelp 未覆盖“已获取信息但未获批准”，已单列诊断并保留原评分，正式采集前需要统一口径。详见 `Study2_1_R1_Smoke_Decision_20261025.md` 和批次 `pilot_review.md`。

## 三、具体实验步骤

### 步骤 1：冻结协议和评估规则

- 锁定 RQ、主要指标、任务类别、模型 ID、提示词、运行参数、随机化方法、排除/重试规则和分析代码版本。
- 在正式结果产生前为每个任务写好隐藏 gold policy、NPC 场景、evaluator 和预期有效求助路径；用开发者不知道模型输出的情况下，先跑 evaluator 边界案例。
- 由另一位研究者或独立审阅者检查任务是否确实属于 must-ask/no-ask/optional-beneficial，检查 R0/R1 的信息增量是否清楚、是否泄漏答案或 gold recipient。记录争议并在正式采集前修订。

### 步骤 2：小规模 pilot 与 API 能力验证

- 已完成的探索性 smoke pilot：GPT-5 Nano 在 R1 下跑 12 episodes（3 个 must-ask 模板各跑 aligned/separated，另有 3 个 optional-beneficial、3 个 no-help 模板）。Must-ask 成功 0/6；no-help 成功 2/3；optional-beneficial 基础任务成功 2/3。该模型多数 must-ask 任务未主动联系同事，且出现输出格式问题；样本和模型能力均不足以检验假设。详见工作区 `research/study2/study2_1_taskset/pilot_runs/gpt5nano_r1_tools_1600_sample12_20261024/` 下的 pilot 报告与逐条 trace。
- R0 renderer 修复后，先对三家候选模型统一运行 R1 分层 pilot，覆盖 must-ask（仅 separated）、optional-beneficial、no-help。Pilot 用于核验各 API/动作适配、确定性 NPC、trace、token/费用记录和 evaluator，不纳入正式估计。完成协议冻结后，先收集全模型 R1 区块，再运行匹配的 R0 区块。
- 核查模型是否能在相同交互协议下发消息、继续处理回复、完成最终产物；不合格时修改适配层/提示词，然后冻结协议并重跑 pilot。
- 用 pilot 估计 API 失败率和运行波动，并基于任务模板层级的 bootstrap/区间宽度模拟，预先冻结正式数据的精度门槛、是否追加重复的规则和最大追加次数。正式采集先对每个模板×模型×条件运行一次；是否追加由预先规定的精度标准决定，不能根据已观察到的模型排名或个别任务结果决定。

### 步骤 3：构建并锁定正式任务集

- 当前 task set 有 **60 个开发模板**，每类 20 个（must-ask、optional-beneficial、no-help），不是已冻结的 confirmatory set。目标是在独立内容审查与 pilot 通过后尽量使用全部合格模板；若剔除模板，补充或重新平衡后再锁定。
- 同一模板的 R0/R1 是配对条件；候选人姓名/职务和列表次序跨条件及模型做平衡。20 个 must-ask 模板正式只运行 separated 版本；aligned 变体不计入正式运行。Optional-beneficial 与 no-help 各使用一个基础版本，alignment 记为不适用。
- 每类至少涵盖多个业务情境，避免“类别”只对应单一领域。No-ask 任务确保输入确实足以完成；optional-beneficial 任务确保帮助可能影响最终质量，但不把求助写进用户指令。
- 正式任务集冻结后，不能看模型结果再改 gold policy。必要修订必须留版本记录，受影响任务重跑并说明。

### 步骤 4：正式运行与随机化

- 全研究采用 **3 个模型 × 2 个信息条件 × 60 个基础模板** 的配对/重复测量设计；分两阶段收集。**第一阶段统一跑全部模型的 R1 条件**，回答 RQ2.1a 在增强角色信息下的模型差异，并回答 RQ2.1c 的任务内关联问题；该阶段不能估计 R1 相对 R0 的角色信息效应。**第二阶段补跑匹配的 R0 条件**，用于 RQ2.1b 及模型 × 信息条件交互。
- 正式阶段先对每个模板×模型×信息条件运行 **1 次**，R1、R0 使用配对实例 seed。一次运行代表该模型在该任务上的一次实际交互结果；不以多次运行替代单次部署表现。首轮完成后，按预先冻结的精度门槛评估关键模板层级估计的不确定性；若未达到门槛，则对**所有模型与相关条件统一**追加重复，最多追加到预先设定的上限。不可因某模型表现不佳或单个任务结果意外而选择性重跑。记录 provider 是否支持 seed/采样参数；若不支持，把重复称为独立 API 重复调用，不声称随机种子独立。
- 若 60 个模板全部通过审查，首轮 R1 为 **60 episodes/模型、180 合计**；配对 R0 也是 **60/模型、180 合计**。因此正式首轮共 **360 episodes**。若精度规则触发追加，最多追加两批，正式阶段上限为 R1 **540** + R0 **540** = **1,080 episodes**。统计推断始终以 60 个父模板为聚类/独立抽样单位，不能把同一模板的重复运行当作新增独立任务。
- 采用分块随机次序运行，避免某家服务在某个条件下集中运行；记录 provider、model ID、时间、API request ID、成功/失败、重试、完整输入/输出 token、实际费用、延迟、prompt 与代码版本。中断后只补跑缺失单元，不覆盖或重复写同一 run ID。
- 第一阶段 R1 的模型顺序、任务顺序、候选人映射与列表顺序均做区组/种子平衡；在查看主要结果前冻结本阶段 trace 和 evaluator 输出。RQ2.1c 以任务模板为单位分析联系次数/首次命中与任务成功、权限合规、轮数和 token 的关联，不作求助行为的因果解释。

### 步骤 5：运行质量检查与数据锁定

- 自动验证每个 episode 是否有完整 trace、NPC 回复、最终状态、token/成本和 evaluator 结果；按预定规则标记 API 错误、格式错误、超时和无效重复，不按结果好坏排除。
- 抽样人工复核模型动作解析、NPC 是否越过隐藏知识/权限边界、评分器是否按 gold policy 工作。
- 生成只读的数据快照、校验和、run manifest 和数据字典。先检查各模型/条件/任务类别的缺失率及预算，再解盲比较结果。

### 步骤 6：计算行为指标

| 维度 | 主要量化指标 | 解释约束 |
|---|---|---|
| 求助启动 | 首步求助率；至少求助一次的比例 | 按 must/no/optional 分开报告 |
| 不足求助 | Must-ask 未在所需行动前求助；optional 中未求助且最终未达到预定质量/正确性标准 | 区分“未问但答对”与“未问且因此失败” |
| 过度求助 | No-ask 任务中无必要的联系；optional 中未带来预定义收益的联系；重复/无效联系 | 联系次数与实际负面后果分开计 |
| 适度求助 | Must-ask 完成必要且合规的求助路径；No-ask 独立完成；Optional 在预定义效益条件下求助或在无需帮助时不求助 | 报告各任务类别的类别内比例；不把三类粗暴合成唯一总分 |
| 求助时机/路径 | 首次求助前的非求助步数；行动前置条件是否满足；有效路径完成率 | 未发生求助视为未发生事件，不当作零步延迟混合平均 |
| 找人质量 | 首位联系人是否对求助目的具备 gold 标注知识/权限；知识命中、权限合规分别报告 | 首次联系人有效不等于整条路径有效 |
| 任务质量 | 规则评分、字段正确性、任务成功、权限违规 | 报告原始分项与类别，不用单个加权 R 替代 |
| 交互效率 | 联系次数、总轮数、输入/输出 tokens、API 实际费用、延迟 | token 与美元费用分开；只比较同一费用口径和采集时点 |

optional-beneficial 的“有益”必须由每个任务预先定义的 evaluator 判定（例如结果正确性/质量是否达到阈值或相较不问时是否有可验证改善）。不通过人工主观感受临时判定，也不使用未预先定义的任务回报权重。

### 6.1 数学定义：从 episode 轨迹到模型行为画像

令 \(e\) 表示一次完整 episode，\(j(e)\) 表示其父任务模板，\(m\) 表示具体模型配置，\(c\in\{R0,R1\}\) 表示信息条件，\(k\in\{must,nohelp,optional\}\) 表示任务类型，\(r\) 表示同一实验单元的重复运行。Must-ask 正式任务均为 separated；optional/no-help 的 alignment 不适用。只有 agent 的 send_message 事件计为一次求助；read_messages 不另算一次联系。

| 比较维度 | episode 级指标 | 定义与分母 |
|---|---|---|
| 求助量 | 联系次数 \(Q_e\) | \(Q_e=\sum_t\mathbf{1}(A_{et}=\text{send\_message})\)。按任务类型报告均值、中位数和分布，不把高次数直接解释为更好或更差。 |
| 求助启动 | 首个外部动作求助 \(H_e\) | \(H_e=\mathbf{1}(A_{e1}=\text{send\_message})\)。报告各模型在每种任务类型中的比例；“第一步”指轨迹中首个可观察动作，不推断模型内部思考步骤。 |
| 求助时机 | 首次求助延迟 \(\tau_e\) | 若发生求助，\(\tau_e=\#\{t<t_{first}:A_{et}\neq\text{send\_message}\}\)。若从未求助则记为未发生/删失，不设成 0；另报在 must-ask 中先提交或终止的比例。 |
| 首次联系人选择 | 收件人有效 \(F^{recip}_e\)；首步路径有效 \(F^{step}_e\) | 有求助时，\(F^{recip}_e=1\) 表示首次“联系人 + 求助目的”属于该任务 gold 的 admissible set；\(F^{step}_e=1\) 还要求该请求符合 gold 路径的下一必要步骤。二者均另报条件率（仅有联系的 episodes）和总体率（未联系按 0，限于 must-ask）。 |
| 路径完成 | 有效求助路径 \(V_e\) | \(V_e=1\) 表示事件序列符合该任务 gold policy 中至少一条有效路径，包括必要信息、授权顺序，以及 optional/no-help 任务允许的无联系路径。路径有效与最终产物得分分开报告。 |
| 任务结果 | 成功 \(S_e\)、任务分数 \(T_e\) | 由冻结的规则 evaluator 计算。S/T 不替代过程指标；模型可以路径合规但产物失败，也可以完成产物但违反流程。 |
| 知识错误 | \(K_e\) | 发消息询问某目的，但收件人不在该目的的 admissible knowledge holder 集合，或 NPC 明确没有该信息的次数。按每 episode 次数及发生比例报告。 |
| 权限错误 | \(A_e^{auth}\) | 向 gold policy 标记为无权的对象请求批准、授权或代为执行的次数。仅询问规则/身份不自动计为越权。 |
| 重复/无效求助 | \(D_e\)、\(W_e\) | \(D_e\)：在已收到同一目的的有效答复后重复询问；\(W_e\)：未取得有用信息、授权或预定义质量增益的联系。对不同目的的必要联系不算重复。 |
| 不足求助 | \(U_e\) | Must-ask：在依赖该信息/权限的行动或提交前，未完成 gold 要求的必要联系/路径。Optional 与 no-help 不因“没有问”自动记作不足求助；optional 的无联系基线路径和任务正确性分别判定。 |
| 过度求助 | \(O_e\) | No-help：有任何同事联系即记不必要联系；Optional：联系未产生 gold 规定的可验证增益、联系无关对象或重复联系时记为无效/过度联系。Must-ask 中超出有效路径的无效联系单独计数。 |
| 校准路径 | \(C_e\) | \(C_e=1\) 表示求助决策与该任务的 gold-valid path 相符且没有无效/重复联系。Must-ask 看是否完成必要路径；no-help 看是否不联系；optional 接受“正确完成无联系基线”或“取得并使用有效建议、达到预定义增益”两种路径。另报 \(S_e\)，不把路径校准和任务成功合并成单一加权分数。 |
| 使用成本 | tokens、美元费用、轮数、延迟 | 每 episode 分别记录 input/output tokens、provider 实际 API 费用、联系数、总轮数与延迟。Token 数不是美元费用；跨 provider 比较费用时记录计价日和缓存规则。 |

这些量先逐 episode 计算，再以**父任务模板**作为汇总和统计推断单位。令 \(J_k\) 为类型 \(k\) 的父模板数，\(R_j\) 为模板内重复数（首轮为 1；若精度门槛触发追加则相应增加）。对追加重复先在同一模板/模型/条件内取均值，再计算：

\[
\bar Y_{m,c,k}=\frac{1}{J_k}\sum_{j=1}^{J_k}\left(\frac{1}{R_j}\sum_{r=1}^{R_j}Y_{j,m,c,k,r}\right).
\]

Must-ask 正式任务均为 separated，因此结论限定于知识持有人与审批者分离的场景，不比较 aligned/separated。

### 6.2 模型差异与角色信息效应

对任一指标 \(Y\)：

- **R0 下的模型差异**：\(D_{m,m',k}=\bar Y_{m,R0,k}-\bar Y_{m',R0,k}\)。描述这两个具体模型配置在姓名+通用职务目录下的差异。
- **单个模型的增强角色信息效应**：
  \[
  \Delta^{info}_{m,k}=\frac{1}{J_k}\sum_{j=1}^{J_k}\left(\bar Y_{j,m,R1,k}-\bar Y_{j,m,R0,k}\right).
  \]
  这是 R1（增强自然语言角色档案）相较 R0（姓名+通用职务目录）的配对变化。
- **模型间的信息效应差异**：\(I_{m,m',k}=\Delta^{info}_{m,k}-\Delta^{info}_{m',k}\)，对应 `model × condition` 交互。对有利指标，正值代表该指标提升更大；对错误/成本指标，负值代表下降更多。解释方向时必须按指标定义转换，不能一概而论。

二元指标报告配对风险差/边际概率，也可给出 logistic 模型估计；计数报告平均差或率比。置信区间和 bootstrap 重抽样以父模板为单位，并在模板内保留 R0/R1 配对及重复运行结构。不得把逐步事件或同一模板的重复 episode 当作独立样本。主要对比为模型差异、各模型 R1−R0、以及模型间 R1−R0 差异；明确控制这组主要比较的多重检验。任何“模型更爱求助”的表述都限定为指定任务类型、条件和所测 API 版本下的接触率/次数差异。

### 步骤 7：统计分析

- **首要结果**：按 6.1 的定义，三个任务类别分别报告 \(U_e\)、\(C_e\)、\(O_e\) 的任务模板层比例；主要对比是 R0 下的模型差异、每个模型的 R1−R0 配对差异，以及模型间 R1−R0 差异。
- **模型/条件分析**：二元结果使用带任务模板聚类/随机截距的 logistic 混合模型，或任务模板簇 bootstrap；计数依分布采用 Poisson/负二项模型。固定效应包括模型、信息条件、任务类别及预注册交互 `model × condition`、`condition × task class`。若样本支持，再估计三阶交互；否则作为描述性分层。
- **行为锚点基线**：对每个任务和信息条件同时计算固定规则策略：Never-ask（从不联系）、Ask-first（遇到候选人就先联系，再行动）及 task-oracle（按 gold policy 的有效路径行动）。前两者帮助解释模型是否只是“总问/总不问”；oracle 是理论上界而不是可部署模型。除非动作空间使基线定义不一致，否则在图表中一并展示。
- **关联分析**：求助量与任务质量、成本、token 的关系按任务类别分析并调整任务模板；标为关联，不声称因果中介。
- **不确定性**：报告绝对比例、风险差/均值差、95% 区间和每个比较的有效模板数。主要假设族控制多重比较；如区间较宽或类别样本有限，结论写“当前精度不足”，不把不显著写成无差异。
- **稳健性**：检查失败/超时处理、重复运行、候选人顺序、任务领域、profile 长度和可用 API 版本。报告 token/美元结果时同时注明 API 计价日期。
- **历史数据**：Study 2 的 44 条重复记录仍保留，只作标记后的历史稳健性材料；不纳入 Study 2.1 的独立任务数或正式模型间主比较。

## 四、论文里可直接呈现的结果

### 论文核心信息

论文最终希望回答：**不同提供方的模型在多用户任务里是否会因任务需要而校准求助？增强角色信息能否减少求助不足或过度求助，且这种变化是否依赖模型？** 数据可能支持、部分支持或不支持这些预期。以下是计划输出，不是预先承诺的结论。

### 计划中的图表

1. **Figure 1 — 实验设计与 episode 流程图（可直接进方法部分）**：三家模型 → 任务三类别（must/no/optional）→ R0/R1 → agent 决策/联系人/NPC 回复 → 规则 evaluator；标明配对单元与重复结构。
2. **Figure 2 — 求助校准图（主结果）**：按任务类别分面、模型分组，显示不足求助、适度求助、过度求助比例及任务模板簇 95% 区间。可用分组点图或比例图；不要用堆叠柱隐藏区间。
3. **Figure 3 — 角色信息效应森林图（主结果）**：各模型的 R1−R0 配对风险差/均值差，分别画 calibration、first-valid-contact、task success；横轴零线清楚，注明模板数和区间。
4. **Figure 4 — 求助与结果的联合图（机制/效率）**：以任务模板为点，展示求助次数或有效联系人次数与任务分数/成功概率的关系，按 must/no/optional 分面，并用颜色标识 under/calibrated/over 类别。标注这是条件关联。
5. **Figure 5 — token/费用结果图（次要结果）**：各模型、profile 条件下每 episode 的 input tokens、output tokens 与 API 美元费用配对差异；如果钱数不具备同口径可比性，仅报告 token 并把供应商价格放表格。
6. **Table 1 — 模型与运行配置**：提供方、精确模型 ID/日期、解码参数、动作适配器、价格记录、API 错误率。
7. **Table 2 — 任务集和 gold policy 概况**：任务类别、模板数、领域、候选人数、必需/可选求助路径、评分器与独立审查状态。
8. **Table 3 — 主要结果**：每模型×条件×任务类别的 under/calibrated/over、任务结果、首次命中、联系数、token/成本；报告分母、点估计和区间。
9. **Appendix**：R0/R1 样例、R0/R1 信息增量与泄漏审计、evaluator 边界案例、API 请求/失败和重试流程、额外分层与敏感性分析、匿名化代表轨迹。

### 可写入论文的结论类型（取决于结果）

- **模型差异**：“在本研究的三类任务与三个被测 API 配置中，求助启动和校准存在/未发现清晰差异；差异主要表现于……任务类别。”
- **档案效应**：“相较姓名+职务目录，增强自然语言角色档案使……模型/任务类别的有效求助/过度求助变化……。”若 R1−R0 区间较窄并覆盖零，可说“未观察到有意义的增强信息收益”；若区间宽，应说证据不足。
- **校准而非求助越多越好**：“角色信息可能改变求助分配，而非单向增加求助；是否构成改善取决于是否减少 under-ask 且没有以不必要联系/成本增加为代价。”若数据不支持此模式则不写为结论。
- **表现与成本**：“某种行为画像与任务质量、权限合规、交互轮数或 token 成本相伴；本研究是受控模拟且该关系为关联。”不把 token 直接称为美元成本，不推断真实企业生产率。

结论范围限于所测模型版本、合成/受控任务、文本交互和固定 NPC 规则；不能直接外推到真实组织或模型家族总体。

## 五、交付文件与复现结构

正式运行后按以下结构保存，单独的原始轨迹不得覆盖：

```text
study2_1/
  protocol.md                         # 本设计冻结版本
  models.json                         # 提供方、model ID、参数和日期，不含密钥
  tasks/<task_id>/                    # task.md、gold_policy.json、scenarios.json、evaluator.py
  runs.jsonl                          # 每 episode 一条元数据索引
  traces/<run_id>.jsonl               # 完整动作/回复事件
  evaluations/<run_id>.json           # evaluator 分项输出
  derived/                            # 清洗数据、统计表、分析报告
  figures/                            # 论文可用的 SVG/PDF 与可视化源代码
  manifest.json                       # 版本、哈希、排除/重试审计
```

密钥只从安全环境变量读取；禁止写进 `models.json`、日志、trace、截图或 Git。正式采集前确认三家模型的访问、预算上限与每次 API 调用费用可审计。

## 六、开始正式实验的准入条件

正式跑之前必须完成：

1. 任务三分类与 gold policy 已冻结并经独立审阅；
2. evaluator 对有帮助/无帮助、知识/权限错误和任务完成均有边界测试；
3. 三家模型的 API、动作协议、模型版本、计价口径和失败重试策略通过 pilot；
4. pilot 结果用于确定模板数、重复数与区间精度目标；
5. 主要指标、假设族、多重比较、排除规则和随机化方案写入带版本号的协议；
6. 预计 API 费用及运行预算在正式采集前可控。

## 附录 A：Study 2.1 正式运行实施计划（运行参考）

本附录规定每个实验 episode 的运行单位、运行次数、配置、阶段顺序和 metadata。正式数据采用“先单次、再按精度追加”的设计；精度门槛、追加批次和最大重复数须在正式结果解盲前冻结。执行前如需改变模型、任务、重复数、提示词、动作接口、评测器或排除规则，先更新协议版本并记录变更原因；不能根据已看到的模型排名或个别任务结果临时改规则。

### A1. 阶段与运行数量

一个 run 指**一个具体模型在一个任务实例、一个信息条件、一个重复编号下完成的一条 episode**。一条 episode 内可以包含多轮模型请求、同事消息和回复；它们不另算独立 run。正式集为 60 个基础模板：20 个 must-ask（全部 separated）、20 个 optional-beneficial、20 个 no-help。Optional/no-help 的 alignment 记为 not_applicable；must-ask 的 aligned 变体不进入正式运行。

| 阶段 | 用途与分析问题 | 运行矩阵 | 每家模型 episodes | 三家合计 |
|---|---|---:|---:|---:|
| Pilot | R1 全模型分层试跑；核验 API 工具调用、动作解析、NPC、trace、token/费用、evaluator 和任务可解性；不纳入正式估计 | 3 个模型 × 每类 3 个模板（must-ask 均 separated）× 1 次 | 9 | 27 |
| 正式首轮阶段 1：R1 | RQ2.1a：比较增强角色信息条件下三种模型的求助校准；RQ2.1c：估计行为与任务结果/成本的任务层关联 | 3 个模型 × 60 个基础模板 × 1 次 | 60 | 180 |
| 正式首轮阶段 2：R0 | 与阶段 1 配对，估计 RQ2.1b 的 R1−R0 角色信息效应及模型交互 | 3 个模型 × 同 60 个模板/seed × 1 次 | 60 | 180 |
| **正式首轮合计** | 不含 pilot；触发预注册精度规则时再对全体相关实验单元统一追加 | 3 个模型 × 2 个条件 × 60 个模板 × 1 次 | **120** | **360** |

按用户确认的完整区块顺序，R1 首轮为 3 模型 × 60 模板 = **180 条**，R0 配对首轮同为 **180 条**，正式首轮总数 **360 条**。加上 pilot **27** 条，启动阶段计划运行 **387 条**；pilot 不纳入正式估计。若精度门槛触发追加，最多追加两批，使正式阶段总量上限为 **1,080 条**（R1 540、R0 540），另加 27 条 pilot；追加量另行记录，不把重复 episode 当成新增模板。

正式首轮每个模型×信息条件有 60 条 episode，按任务类别分解为 must-ask 20（均 separated）、optional-beneficial 20、no-help 20。R0/R1 和三个模型对相同模板/seed 配对。统计推断以 60 个父模板聚类；重复调用只用于估计运行波动与改善精度，不增加独立任务模板数。

**追加重复的预注册精度规则：**先完成每个模型×模板×条件的单次运行，先跑完 R1 首轮，再跑配对的 R0 首轮。pilot 阶段用运行波动和模板层差异，预先指定主要估计量的目标 95% 区间半宽、不可接受的 API 失败率，以及在什么条件下追加重复能实质缩窄区间，并在正式结果解盲前写入冻结的 confirmatory manifest。R1、R0 首轮均完成后，只检查预先指定估计量的区间精度，不按显著性、效应方向或模型排名决定是否追加。区分两类不确定性：追加重复只能降低同一模板内的运行波动，不能弥补模板间差异导致的不确定性；若精度模拟显示追加运行预计不能实质改善目标区间，就不追加，而是报告区间并降低结论强度。若区间仍宽且追加预计有效，则对全部模型、全部 60 个模板及 R0/R1 匹配区块统一增加一个重复批次，再按相同规则检查；最多追加两批（即每个实验单元最多 3 次）。若达到上限仍未达标，报告实际区间并将结论降为探索性。每个追加批次使用预生成并配对的 replicate/seed；API 不支持可控 seed 时注明为独立请求重复。精度门槛的具体数值须在正式运行前冻结，当前文件不预填未经 pilot 校准的数值。

### A2. Pilot 抽样和通过标准

Pilot 固定抽取 9 个基础模板：must-ask 选 3 个（全部 separated）；optional-beneficial 选 3 个；no-help 选 3 个。三个模型各跑相同 9 条，统一使用 R1，共 **27 条 pilot episodes**。Pilot 每格先跑一次；出错或修复适配器后重跑时生成新 run_id，标明 supersedes/retry_of，原记录保留。

Pilot 逐项检查：三家模型均成功认证并能调用目标模型；每个模型都能按统一语义调用 send_message、read_messages、submit_answer；收到回复后继续任务；运行隔离有效；所有动作和回复落入当前 run_id 的 trace；evaluator 可从 trace 重算；记录 agent token、延迟、重试和费用；至少检查每类代表任务的完整轨迹及所有 API/格式失败。不可仅凭最终分数通过 pilot。

通过标准为：没有未解释的系统性解析错误、跨 run 消息污染或 NPC 越权泄露；三个 task class 都能完成有效 episode；所有失效有可审计状态和原因；任务内容审查与 evaluator 边界审查已由独立审阅完成并记录。Optional 的建议使用判定还须确认 keyword-coverage proxy 不会把仅复述建议误判为有效使用；未通过时先修订评分规则并重做受影响 pilot。

### A3. 正式 run 的共同实验配置

| 配置项 | 冻结规则 |
|---|---|
| 模型 | OpenAI gpt-5.4-mini；Moonshot kimi-k2.6；Anthropic claude-haiku-5-5。先从三家 API 返回结果记录不可变/实际 model ID；若别名解析不同，保存返回 ID，不静默替换。 |
| 阶段顺序 | 先完成三家模型全部 R1 正式区块并锁定 R1 数据快照；通过质量审查后，再跑同一批任务实例的 R0 配对区块。Pilot 不并入正式区块。 |
| 任务 | 冻结后的 60 个基础模板；20 个 must-ask 全部使用 separated；不运行其 aligned 变体。Optional/no-help 各一个固定模板版本，alignment 记为 not_applicable。每个模型和条件都覆盖完全相同的实例集合。 |
| 随机化/配对 | 首轮每个 task_id × profile_condition × model 运行一次；R0/R1 及模型间对同一模板使用配对实例 seed 和一致的候选人映射/顺序。若追加重复，按预生成 replicate_id 扩展并在 R0/R1、模型间配对；模型运行顺序分块随机，避免 provider 与时段混淆。 |
| R0/R1 | R0 为合成人名 + 通用职务；R1 在同名、同职务基础上增加一般职责/知识领域/权限信息。除 profile 内容外，任务文本、NPC、工具、回复规则、max turns、evaluator 和实例 seed 均匹配。 |
| NPC 与运行隔离 | 使用冻结版本的确定性 scenario 回复策略；每个 episode 独立 namespace/inbox。NPC 知识、权限和回复内容不因模型或 profile 条件改变。 |
| 动作接口 | 所有 provider adapter 实现相同语义的 send_message(recipient_id, purpose, message)、read_messages(recipient_id)、submit_answer(answer)。每次模型响应最多执行一个动作；禁止 adapter 替模型选择联系人、补写答案或自动完成求助步骤。 |
| 轮数和输出 | 每 episode 最多 8 个模型决策轮；pilot 后冻结每个 endpoint 的最大输出 token 配置，使预算足够提交任务产物。达到上限、格式错误、拒答、超时和空输出均记录为 run 状态，不能静默丢弃。 |
| 采样参数 | Pilot 后逐 provider 冻结并写入配置快照。统一采用可用的最低随机性设置；某 provider 不支持相同参数时不强行传入不兼容参数，记录实际值与差异。不得只根据正式阶段结果调参。 |
| 提示词/工具 schema | 三家模型使用语义相同的 system prompt、用户任务文本、工具说明和提交格式；provider-specific 序列化只做格式转换。冻结文本及工具 schema 的 SHA-256，不在正式阶段改写。 |
| 计费与限额 | 正式开跑前记录各 provider 当日输入/输出价格、缓存计价、限流及项目预算上限；完成 27 条 pilot 后，估算正式首轮 360 条调用的费用，并按正式阶段最多 1,080 条的上限核算预算，取得预算可控结论后才启动阶段 1。 |

此设计的主模型比较仅针对上述三个具体 API 配置。阶段 1 只支持 R1 条件下的模型差异与 RQ2.1c 关联分析，不支持 R1 相对 R0 的信息效应；不得把阶段 1 结果称为完整 Study 2.1 结论。

### A4. 每条实际 run 的 metadata

每次 episode 开始前建立唯一 run 目录和 manifest；开始后先 append 状态为 started，结束后追加 completed/failed，不覆写旧 run。主索引 runs.jsonl 每个 run 一行；同一目录保存完整 trace、输入实例、answer、evaluator 结果和本次运行配置快照。必填字段及数据类型见同目录的 study2_1_run_metadata_schema.json；runner 应在每次写入后按此 schema 校验。配置/产物中禁止写入 API key、Authorization header 或任何 secret。

| Metadata 字段组 | 每条 run 必须记录 |
|---|---|
| 识别与研究阶段 | run_id、study_id、run_type（pilot/confirmatory）、collection_stage（pilot/R1/R0）、protocol_version、时间戳、status、failure/exclusion reason、retry_of/supersedes |
| 任务身份 | task_id、task_version、parent template_id、task class、variant_id、alignment、split、task/gold/scenario/evaluator 文件 SHA-256 |
| 模型与 endpoint | provider、请求 model alias、API 返回的确切 model ID、endpoint/base URL（不含密钥）、API request IDs、调用时间、适配器名称/版本 |
| 条件与随机化 | profile_condition、instance seed、replicate、候选人顺序、匿名候选 ID 到合成人名映射的 evaluator-only 文件引用/hash、区块/运行顺序 |
| 实验配置 | system prompt/task prompt/tool schema/runtime 配置 hash；max turns、max output tokens、temperature/top_p/reasoning 或 thinking 设置（支持则记录实际值，不支持标 unavailable）、tool_choice、并行工具调用设置 |
| 运行过程 | 每轮开始/结束时间、HTTP/API 错误类别与状态码、重试次数、模型动作解析状态、agent/NPC/tool 事件计数、实际延迟 |
| 使用量与费用 | 每次及总 input/output tokens、cached tokens（若提供）、NPC tokens（若可得，否则 unavailable）、provider usage/费用原始字段、计价日期与估算 USD；不可得项标 unavailable，不猜算 |
| 评测与结果 | evaluator version/hash、每个 checkpoint、任务分数/成功、underhelp/calibrated/overhelp、first recipient/path validity、知识错误、权限错误、重复/无效联系、错误和 evidence IDs |
| 产物引用 | model-visible task/profile 文件、原始模型请求/响应（脱敏）、normalized trace、answer、evaluation、run log、manifest 的相对路径及 hash |

建议每条 run 的 metadata 至少长这样（字段可扩展；不可删除必需字段）：

~~~json
{
  "schema_version": "study21-run-v2",
  "run_id": "s21-confirmatory-R1-openai-must-release-separated-rep01-seed...",
  "study_id": "study2.1",
  "run_type": "confirmatory",
  "collection_stage": "R1",
  "protocol_version": "study21-protocol-v1.0",
  "task_id": "must-release-deployment",
  "task_version": "frozen-version",
  "template_id": "must-release-deployment",
  "help_need_class": "must_ask",
  "variant_id": "separated",
  "alignment": "separated",
  "model_provider": "OpenAI",
  "model_requested": "gpt-5.4-mini",
  "model_returned": "provider-returned-model-id",
  "endpoint": "https://api.openai.com/v1/...",
  "profile_condition": "R1",
  "instance_seed": 20261024,
  "replicate": 1,
  "candidate_order": ["C2", "C1", "C3", "C4"],
  "mapping_ref": "instances/<run_id>/identity_mapping.json",
  "mapping_hash": "sha256:...",
  "sampling_parameters": {
    "max_turns": 8,
    "max_output_tokens": 1600,
    "temperature": "record-actual-or-unavailable",
    "reasoning_or_thinking": "record-actual-or-unavailable",
    "tool_choice": "auto",
    "parallel_tool_calls": false
  },
  "prompt_hashes": {
    "system": "sha256:...",
    "task": "sha256:...",
    "tool_schema": "sha256:..."
  },
  "runtime_version": "git-commit-or-release",
  "npc_policy_version": "frozen-scenario-version",
  "evaluator_version": "frozen-evaluator-version",
  "adapter_name": "openai-tool-adapter",
  "adapter_version": "adapter-commit-or-release",
  "task_hashes": {
    "task": "sha256:...",
    "gold": "sha256:...",
    "scenario": "sha256:...",
    "evaluator": "sha256:..."
  },
  "started_at": "ISO-8601",
  "ended_at": "ISO-8601",
  "status": "completed",
  "api_request_ids": [],
  "retries": [],
  "errors": [],
  "agent_tokens": {
    "input": 0,
    "output": 0,
    "cached_input": "unavailable"
  },
  "npc_tokens_or_unavailable": "unavailable",
  "estimated_cost_usd": null,
  "cost_status": "unavailable",
  "pricing_snapshot": null,
  "latency_ms": 0,
  "checkpoint_vector": {},
  "artifact_refs": {
    "trace": "traces/<run_id>.jsonl",
    "answer": "answers/<run_id>.json",
    "evaluation": "evaluations/<run_id>.json",
    "visible_instance": "instances/<run_id>/",
    "request_response": "api_io/<run_id>.jsonl"
  },
  "retry_of": null,
  "exclusion_reason": null
}
~~~

metadata 中的示例值只是格式示意，不是已运行记录。正式运行时所有实际值必须由 runner 写入；模型返回值、token/费用、request ID、结束状态不得手工编造。原始 trace 和 metadata 一律追加保存，修复/重跑通过新 run_id 关联旧记录。

### A5. 运行批次与停止/继续规则

1. **准备批次**：锁定任务文件与 evaluator hash；保存模型目录查询结果、价格表、API 版本、提示词/工具 schema 和 run metadata schema；人工审查任务与泄漏风险。尚未通过时只允许 pilot。
2. **Pilot 批次**：先运行 27 条 R1 pilot。输出每模型/任务类可用性、失败原因、动作格式、NPC 一致性、任务完成与成本摘要；不做显著性检验、不进入正式数据。
3. **冻结点**：三家模型及工具格式均通过 pilot、任务独立审查通过、精度门槛与追加上限、预算、随机化、主要指标和排除规则冻结后，创建不可变 confirmatory manifest。
4. **正式 R1 首轮**：按区组执行 180 条（每模型 60 条）；每批后只检查运行质量、缺失和费用，不看模型表现排名。完成全区块后锁定 R1 首轮数据快照与 hash。
5. **正式 R0 首轮**：用同一组模型×60 模板×首轮配对 seed 执行 180 条 R0，作为 R1 的配对基线。随后对 R1/R0 配对数据应用预注册精度规则；必要时对全部模型、模板和两个条件统一追加匹配批次。合并数据后按父模板聚类分析。
6. **暂停规则**：若出现数据泄漏、错误 gold、NPC 跨 run 污染、evaluator 错误、模型 ID 未锁定、预算越限或单一 provider 系统性接口失败，暂停该区块；保留全部日志，修复后升协议版本并重跑受影响的完整配对单元。

### A6. 正式结果映射

| 数据区块 | 可回答内容 | 不可据此声称 |
|---|---|---|
| Pilot：R1，27 条 | API/工具适配是否能跑通；初步定位任务歧义、格式错误和评分器问题 | 模型之间有稳定差异、总体求助倾向、确认性假设成立 |
| 正式首轮阶段 1：R1，180 条 | RQ2.1a：三个指定模型在 R1 下的校准画像差异；RQ2.1c：求助行为和成功/合规/效率之间的任务层关联 | R1 的因果效果；R1 相对 R0 的增量；对公司或模型家族的一般化结论 |
| 正式首轮阶段 2：R0，180 条，与 R1 配对 | RQ2.1b：R1−R0 对每模型的配对影响及模型间影响差异；完整 R0/R1 图表 | 对真实企业人类团队、任意未测试模型的直接外推 |
