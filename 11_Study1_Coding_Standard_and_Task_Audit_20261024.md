# Study 1：跨数据源求助行为编码标准与任务审计（工作稿）

日期：2026-10-24  
范围：TheAgentCompany（TAC）+ HiL-Bench + AskBench。此处“求助”是一个宽的行为分析构念；三个来源的场景不同，编码共用框架，但频率与结果按来源分别报告。

## 1. Study 1 的两项贡献

1. **分析框架贡献**：基于多种 agent 交互轨迹，建立可复用的求助行为多维分类标准，归纳跨场景可观察的求助 pattern。
2. **诊断性实证贡献**：在 TAC 已发布企业任务轨迹中检验不同模型配置是否呈现不同求助行为，以及可验证的求助过程质量是否与任务评分相关。该分析是观察性研究，不作因果结论。

不另设“编码一致性”假设；编码一致性仍作为方法质量检查报告。

## 2. 分类单位与原则

### 2.1 两级分析单位

- **任务级 help opportunity（求助机会）**：任务初始信息、环境状态或后续执行是否产生了一个可验证的信息缺口、歧义、冲突、权限要求或协作需要。
- **事件级 help episode（求助事件）**：agent 围绕一次机会发起的一次或多次询问，直到得到回复、放弃或任务结束。单条消息是事件证据，不自动等同于完整求助过程。

### 2.2 核心编码原则

- 只标注轨迹和任务定义中可观察、可核查的内容；不推断模型的主观“不确定感”。
- “没有问”只有在任务审计确认存在求助机会时才可记为 missed-help；否则记为 no observed ask / 不适用。
- “问错人”只在任务材料给出明确的可接受联系人集合或知识/权限归属时使用。NPC 名单不等于正确联系人名单。
- 允许一条任务存在多个有效对象、条件式路径或先后询问；不强行指定唯一 oracle。
- TAC、HiL-Bench、AskBench 共用编码轴，但 source-specific 指标分开汇报；不把它们的比例直接合并。

## 3. 初版编码标准

| 维度 | 代码/取值 | 操作定义 | 适用范围 |
|---|---|---|---|
| 求助机会 | `present` / `absent` / `uncertain` | 依据任务审计与该步环境状态，判断是否有 agent 无法从已知信息或常规工具中自行解决的问题 | 三个来源 |
| 触发类型（可多选） | `missing_info` | 完成任务所需事实不在 agent 当前可访问信息中 | 三个来源 |
|  | `underspecified` | 用户意图或要求缺关键细节，需向请求者澄清 | AskBench、部分 TAC |
|  | `false_or_conflicting_premise` | 输入含错误前提或互相冲突的信息，需要核实/纠正 | AskBench、HiL-Bench |
|  | `blocker` | 工具、代码、数据或环境执行遇到无法自行解除的阻塞 | HiL-Bench、部分 TAC |
|  | `authority_or_permission` | 下一步行动需要有权限者批准、确认或授权 | 仅当 TAC 任务材料明确支持时 |
|  | `coordination_or_availability` | 需要协调多人时间、偏好、状态或承诺 | TAC |
| 求助时机 | `proactive` / `timely_after_gap` / `delayed_after_attempts` / `no_ask` / `not_observable` | 相对于可观察求助机会，记录首次提问时点；不根据推测的内心状态判定 | 三个来源；no-ask 只在机会明确时计分 |
| 对象类型 | `prompt_named_person` / `selected_from_roster` / `group_or_multiple` / `generic_human_or_user` / `not_applicable` / `unverifiable` | 记录联系人选择结构；另记录是否符合任务特定的 acceptable-recipient set | TAC 有联系人选择；HiL/AskBench 是通用 responder |
| 提问目的 | `information` / `clarification` / `verification` / `advice` / `approval` / `status` / `availability_or_preference` / `delegate_or_request_action` / `feedback` / `other` | 以消息实际请求的帮助功能为准；可多选 | 三个来源 |
| 问题质量 | `targeted` / `partly_targeted` / `broad` / `irrelevant_or_redundant` / `unclear` | 是否针对已识别的信息缺口提出足以促成有效回复的问题；按任务 rubric 判定 | 三个来源；按 source 报告 |
| 回复状态 | `useful_complete` / `useful_partial` / `no_reply` / `nonresponsive` / `incorrect_or_conflicting` / `not_observable` | 回复是否提供解决该机会所需的信息；NPC 回复和模拟用户回复分开识别 | 三个来源 |
| 回复利用 | `used_correctly` / `used_partly` / `ignored` / `misused` / `not_observable` | 后续动作/答案是否合理使用已收到的信息 | 有完整后续轨迹时 |
| 机会结果 | `resolved` / `partly_resolved` / `unresolved` / `not_observable` | 该求助机会是否被解决；和整项任务完成度分开编码 | 三个来源 |
| 证据置信度 | `high` / `medium` / `low` | 记录标签证据是否直接、充分；低置信度不进入严格正确率主分析 | 三个来源 |

### 3.1 衍生错误标签（仅在 ground truth 充分时）

- **missed-help**：存在已核实的求助机会，agent 未问，且后续确实无法从其他来源获得所需信息。
- **wrong-recipient**：所联系对象不在该任务允许集合中，且任务规则能排除其有效性。
- **no-uptake**：agent 得到足够且相关的回复，却未在后续决策/答案中使用。
- **redundant-ask**：同一信息已充分回答后重复询问，且无新状态变化。
- **over-asking**：没有可核实的信息缺口却请求帮助，或在已有充分答案后继续问；仅对提供了明确 rubric 的任务使用。

标签支持不足时用 `unverifiable`，不要把它折算为错误。

## 4. 三个数据源的任务审计

| 数据源 | 可用材料及轨迹状态 | 任务/触发结构 | 在共同框架中的适用维度 | 不支持的推断 |
|---|---|---|---|---|
| **TheAgentCompany** | 本地已有 400 条历史压缩轨迹（10 个模型配置 × 40 个 NPC 相关任务）；当前可与评分配对的分析面板为 390 条、39 个任务。官方实验仓库包含逐步轨迹和 evaluator/checkpoint 结果。 | 任务包括指定同事、多候选人/条件式咨询、动态发现联系人、多人协作。现有 `task_policy_codebook.csv` 的第一轮审计：17 个固定对象/对象组、15 个条件式选择、6 个动态发现、1 个非人员联系、1 个 prompt/roster 不匹配；分类仍需按本文件标准复核。 | 机会、触发、联系人选择、提问目的、回复、跟进和任务结果；只有逐任务核实 acceptable-recipient set 后，才计算 recipient hit/miss。 | scenario roster 覆盖率不能当正确率；固定点名任务主要测指令执行，不是自主找人；联系与分数的相关性不是求助的因果效果。 |
| **HiL-Bench** | Hugging Face 上公开 200 条 task records，含问题、测试信息和 `blocker_registry`；benchmark runner 可运行 baseline、full-info、ask-human，并生成逐次执行轨迹。任务文件本身不是 agent trace。 | SWE 与 text-to-SQL；blocker 是有标注的缺失信息/歧义/矛盾等澄清机会。以 blocker 是否触发为主要任务审计标签。 | 求助机会、时机、问题是否针对 blocker、模拟 responder 回复、是否利用回复、blocker/任务是否解决。 | 只有通用 ask-human 接口，没有组织内多候选联系人，不能用于“找对哪位同事”的率或组织角色/权限结论。 |
| **AskBench** | Hugging Face 发布评测任务数据；evaluation runner 可生成逐轮问题、模拟用户回复、最终答案和 judge/checkpoint 决策。任务数据本身不是已完成的企业 agent 轨迹。 | AskMind：意图或必要信息缺失；AskOverconfidence：输入带错误前提，需要识别并纠正。 | 机会识别、澄清/核实目的、提问针对性、模拟用户回复、回复利用及最终任务答案。 | 面向单一模拟用户/评测 judge；不包含同事角色、权限或多个可选求助对象，因此只用于澄清型 help-seeking pattern，不用于 whom 选择分析。 |

### 4.1 TAC 任务审计初步纳入决定

40 个任务的第一轮 policy 审计已经逐任务列在 `research/pilot/study1/task_policy_codebook.csv`；基于该审计生成了带 Study 1 纳入建议的 [study1_task_eligibility_v1.csv](research/pilot/study1/study1_task_eligibility_v1.csv)：

- **17 个固定对象/对象组任务**：纳入沟通过程描述和回复利用分析；不作为自主选人的主要证据，因为提示已指明联系人。
- **15 个条件式/选择任务**：作为 when/whom 的候选任务；只有触发条件和有效路径核实后，才进入求助机会、漏问或选人指标。
- **6 个动态发现任务**：作为自主找人的候选任务；须核实目录、任务状态和实际有效联系人集合。
- **1 个非人员联系任务**：排除求助分析。
- **1 个 prompt/roster 不匹配任务**：在差异解决前隔离，不进入目标正确率和任务结果主分析。

因此，当前可界定 **21 个候选自主决策任务**，但这不是说 21 个都已取得最终 ground truth；目前没有任务被认证为可直接用于严格的 wrong-recipient / missed-help 率。所有任务仍需逐项核实以下证据后，冻结最终纳入状态：

1. `opportunity_present`：是否存在可核验求助机会；
2. `trigger_type`：信息缺失、歧义、权限、协调、阻塞等；
3. `acceptable_recipient_set`：可接受对象及其证据出处，允许多对象/多条路径；
4. `answer_available_elsewhere`：agent 是否能从任务初始环境或工具中取得同一信息；
5. `scoring_contamination`：评分器是否直接奖励联系动作；
6. `strict_eligibility`：是否进入 missed-help / wrong-recipient 主分析及原因。

以上 40 条任务类别来自单研究者第一轮审计；须复核任务指令、场景事实与 evaluator，不可把 roster 直接当 gold label。

## 5. 分析范围和数据使用决定

- **Pattern 归纳**：从三种来源的轨迹抽取共同序列（机会识别 → 是否求助 → 对象/问题 → 回复 → 回复利用 → 机会结果）。用多维编码表达，允许同一事件有多个标签，不预设互斥的单一类别。
- **跨来源比较**：报告每个来源内的类别分布和典型序列；只比较语义上同构的标签，例如 targeted question 或 answer uptake。不得汇总成一个跨来源“总体求助率”。
- **H1（模型配置差异）**：仅在 TAC 做任务配对分析；HiL/AskBench 新跑轨迹可以作为 taxonomy transfer/探索性补充，不和 TAC 模型差异检验混池。
- **H2（过程质量与结果关联）**：主要在 TAC、且仅对 opportunity 和 acceptable-recipient 经过核实的子集中分析。主结果同时报告总分和剔除直接协作 checkpoint 后的分数。用关联措辞，不作因果解释。
- **当前尚未完成**：HiL-Bench/AskBench 的原始数据尚未下载到项目目录，也没有为这两个 benchmark 运行模型。因此本文件完成的是官方数据结构/任务类型审计和跨来源 codebook 草案；逐条任务实例和 agent 轨迹标注需在数据落地/运行后执行。

## 6. 官方来源

- TheAgentCompany 实验轨迹：[TheAgentCompany/experiments](https://github.com/TheAgentCompany/experiments)
- TheAgentCompany 运行配置与轨迹输出：[evaluation README](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/evaluation/README.md)
- HiL-Bench 公共任务数据：[ScaleAI/hil-bench](https://huggingface.co/datasets/ScaleAI/hil-bench)；运行并输出轨迹：[hilbenchauthors/hil-bench](https://github.com/hilbenchauthors/hil-bench)
- AskBench 评测数据：[jialeuuz/askbench_bench](https://huggingface.co/datasets/jialeuuz/askbench_bench)；运行代码及逐轮输出格式：[jialeuuz/askbench](https://github.com/jialeuuz/askbench)
- AskBench 论文：[Findings of ACL 2026](https://aclanthology.org/2026.findings-acl.845/)

