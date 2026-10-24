# 企业式工作流中 AI Agent 的失败、诊断与缓解：文献调研（v0.2）

- 检索日：2026-10-23；时间窗：**2023-10-23 至 2026-10-23**
- 状态说明：✅=已核对官方页面，或 Google Scholar 结果直接链接到官方 proceedings/Anthology 页面；🔶=只有 GS 元数据，官方页尚未打开核对；⚠️=依据背景知识，**未核实**。
- 方法声明：这是**叙述性调研**，不是系统综述。没有执行可复现的 PRISMA 式筛选。Google Scholar 有 CAPTCHA，自动抓取被拦截（见 memory.md），因此本轮通过 Web 搜索加官方页面核对完成。

## 0. 检索记录
| 项 | 内容 |
|---|---|
| 数据源 | Web 搜索 → arXiv、PMLR、NeurIPS Proceedings、ACL Anthology、ICML 官网 |
| 检索式（示例） | `enterprise workflow agent benchmark failure analysis`；`"Why Do Multi-Agent LLM Systems Fail"`；`Who&When failure attribution`；`AgentDojo / CaMeL / tau2-bench / AppWorld` |
| 纳入标准 | ①多步、有状态、调用工具的 agent；②企业式任务或其直接前置能力；③涉及失败分析、诊断或缓解 |
| 排除标准 | 单轮问答、纯游戏环境（除非作为对照） |
| 数量 | v0.2：Google Scholar 25 个检索式（限 2023 年及以后），每个取前 10 条，去重后 237 条 → 按标题和摘要人工初筛，保留约 60 篇（见 §4b）。原始结果在 research/gs/q*.json |

## 1. 定义与边界
- **LLM agent**：以 LLM 作为策略，在“观察→推理→动作（工具/API/GUI）”的循环中运行的系统，带有跨步状态。
- **工具增强型 LLM（tool-augmented LLM）**：单次或少次调用工具，没有自主循环和长期状态。
- **Agentic workflow**：由开发者预先编排的固定流程，LLM 只在节点上做决策。
- **传统 MAS / 自主 agent**：BDI、强化学习等非 LLM 体系，只作为对照。
- **企业式工作流**：多步骤、有状态、跨工具或跨角色的业务任务。
- **可复现分级**：
  - R3：任务、环境、评测脚本全部公开，可本地或 Docker 重跑
  - R2：数据和代码公开，但依赖闭源 API 或商业实例（如 ServiceNow、Salesforce）
  - R1：只公开数据或 trace
  - R0：不公开
  - 无法确认时标“未核实”。

## 2. 代表性公开环境
| 环境 | 领域 | 状态 | 可复现 |
|---|---|---|---|
| [TheAgentCompany](https://proceedings.neurips.cc/paper_files/paper/2025/hash/0d744742f6fac4d1134c019b7cef3c8a-Abstract-Datasets_and_Benchmarks_Track.html) | 模拟软件公司，覆盖 SWE、HR、财务、PM，含模拟同事 | NeurIPS 2025 D&B ✅ | R3（自托管 GitLab/ownCloud 等，依据论文） |
| [τ-bench](https://arxiv.org/abs/2406.12045) / [τ²-bench](https://proceedings.mlr.press/v306/barres26a.html) | 零售、航空、电信客服，带策略文档与用户模拟 | τ：[ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html) ✅；τ²：ICML 2026 ✅ | R3（GitHub sierra-research，⚠️） |
| [AppWorld](https://aclanthology.org/2024.acl-long.850/) | 9 个 app、457 个 API、750 个任务 | ACL 2024 Best Resource ✅ | R3 |
| [AgentDojo](https://proceedings.neurips.cc/paper_files/paper/2024/file/97091a5177d8dc64b1da8bf3e1f6fb54-Paper-Datasets_and_Benchmarks_Track.pdf) | 邮件、银行、旅行，含注入测试 | NeurIPS 2024 D&B ✅ | R3（[code](https://github.com/ethz-spylab/agentdojo)） |
| WorkArena / [WorkArena++](https://proceedings.neurips.cc/paper_files/paper/2024/hash/0b82662b6c32e887bb252a74d8cb2d5e-Abstract-Datasets_and_Benchmarks_Track.html) | ServiceNow 知识工作 | WorkArena：ICML 2024 🔶（GS 只指向 arXiv）；WorkArena++：NeurIPS 2024 D&B ✅ | R2（需 ServiceNow 开发者实例） |
| [CRMArena](https://aclanthology.org/2025.naacl-long.194/) / CRMArena-Pro | Salesforce CRM | NAACL 2025 ✅ / 预印本 | R2 |
| [OSWorld](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)、WebArena、SWE-bench | 桌面、网页、软件工程 | OSWorld：NeurIPS 2024 D&B ✅；另两项 ICLR 2024 🔶 | R3 |

## 3. 研究分类图谱
重叠关系：
- “诊断/归因”（D 类）横跨所有类别。
- 安全（S 类）与记忆（M 类）在“记忆投毒”上交叉。
- 多 agent 失败（MA 类）多数可以还原为规格（规划类）和验证（V 类）问题，MAST 的结论即如此。

| 大类/小类 | 典型失败 | 诊断 | 缓解 | 环境 | 代表论文 | 企业相关性 | 可复现 | 空白 |
|---|---|---|---|---|---|---|---|---|
| U 任务理解/澄清 | 歧义下擅自假设、违背策略 | 用户模拟、对照有无澄清 | 主动澄清、约束确认 | τ/τ²-bench | τ²-bench ✅ | 高（客服） | R3 | 澄清成本与收益的量化 |
| P 规划/长时程 | 步骤遗漏、提前宣告完成、重复步骤 | trace 标注（MAST） | 计划验证、分阶段验收 | TheAgentCompany、AppWorld | [MAST](https://proceedings.neurips.cc/paper_files/paper/2025/file/b1041e52d3be19f0a9bc491657488e4a-Paper-Datasets_and_Benchmarks_Track.pdf) ✅ | 高 | R3 | 长任务中的状态检查点 |
| T 工具/API | 参数错误、误读工具返回 | 状态差分评测（AppWorld） | schema 校验、dry-run | AppWorld、BFCL ⚠️ | AppWorld ✅ | 高 | R3 | 跨系统事务一致性 |
| GUI 操作 | 卡在弹窗、点错元素 | 截图与 trace 回放 | grounding 模型 | OSWorld、WorkArena | TheAgentCompany §7.3 ✅ | 中-高 | R2-R3 | 企业 UI 分布外泛化 |
| M 记忆/检索 | 记忆污染、过时知识 | 触发器检索分析 | provenance、可撤销写入 | AgentPoison ⚠️ | AgentPoison ⚠️ | 高 | R3 ⚠️ | 记忆治理基准缺失 |
| S 安全 | 间接提示注入、数据外泄、越权 | 注入用例攻击成功率 | 检测器、CaMeL 式控制流/数据流隔离 | AgentDojo、InjecAgent ⚠️ | AgentDojo ✅、[CaMeL](https://arxiv.org/abs/2503.18813) ✅ | 极高 | R3 | 效用损失（CaMeL 77% vs 无防御 84%） |
| MA 多 agent | 角色违背、通信失配、缺少验证 | LLM-as-judge 标注、失败归因 | 改进角色规格（ChatDev +9.4%） | MAST-Data、[Who&When](https://proceedings.mlr.press/v267/zhang25cq.html) | MAST ✅、Who&When ✅ | 中（企业数据少） | R1-R3 | 步骤级归因准确率仅 14.2% |
| H 人机协作 | 不跟进同事回复、不升级 | 模拟同事交互 | 升级策略、人工审批 | TheAgentCompany | ✅ | 高 | R3 | 审批点放置的最优化 |
| R 可靠性/成本 | 多次运行一致性差 | pass^k | 投票、重试 | τ-bench、[CLEAR](https://arxiv.org/abs/2511.14136) | CLEAR（预印本）✅ | 极高 | — | 成本与可靠性的帕累托前沿 |
| V 验证/审计 | “成功”但结果错误、自欺式捷径 | 结果状态检查、对账 | 独立验证器、测试 | SWE-bench、TheAgentCompany | ✅ | 高 | R3 | 无标准答案任务的验证 |


## 3b. 领域详解：各方向在研究什么、具体贡献是什么
> 本节内容依据各论文的 **arXiv 摘要**（2026-10-23 通过 arXiv API 获取，原文存于 `research/abs/abs.json`）。数字都直接取自摘要。"我的解读"段落是推断，不是论文的结论。

### 领域 1：企业工作流基准——"agent 到底能做多少真实工作？"
**核心问题**：从"会不会调用 API"转向"能否在有状态、多应用、有规则约束的业务环境里把事情做完"。
**主要研究路线**：①仿真公司或业务系统；②真实 SaaS 平台；③办公软件或桌面；④软件工程。

| 论文 | 环境与规模 | 主要发现 / 贡献 |
|---|---|---|
| **TheAgentCompany**（Xu et al.，NeurIPS'25 D&B） | 自托管的"小软件公司"：内部网站、数据、模拟同事；agent 可以浏览网页、写代码、和同事沟通 | 最强 agent 自主完成 **30%** 的任务；简单任务可以自动化，长时程任务仍做不到。代码、数据、环境全部公开 |
| **τ-bench**（Yao et al.，ICLR'25） | 零售、航空客服；LLM 模拟用户 + 领域 API + **策略文档** | 用"对话结束时的数据库状态 vs 目标状态"做评测；提出 **pass^k**（k 次都成功）。GPT-4o 成功率 <50%，零售域 pass^8 <25%，说明 agent 很**不稳定** |
| **τ²-bench**（Barres et al.，ICML'26） | 新增电信 **dual-control** 域（用户也要操作设备），建模为 Dec-POMDP | 从"没有用户"切换到"双方都要操作"时性能大幅下降；能分开统计**推理错误**和**沟通/协调错误**；带组合式任务生成器 |
| **AppWorld**（Trivedi et al.，ACL'24 最佳资源） | 9 个日常 app、457 个 API、约 100 个虚拟用户；750 个任务 | 用**基于状态的单元测试**评测，允许多种解法，同时检查 **collateral damage**（附带破坏）。GPT-4o 普通任务约 49%，挑战任务约 30% |
| **WorkArena / WorkArena++**（ServiceNow） | 真实 ServiceNow 平台；第一代 33 个任务 → 第二代 682 个工作流 | 第一代同时推出 BrowserGym，开源和闭源模型差距明显；第二代考察规划、算术推理、检索，并能自动生成大量 ground-truth 轨迹用于微调 |
| **CRMArena / Pro**（Salesforce） | 16 类 CRM 对象，含潜变量（如投诉习惯、违规）；Pro 版有 19 个任务，覆盖 B2B/B2C | 第一代：ReAct <40%，函数调用 <55%。Pro：单轮约 58%，**多轮降到约 35%**；agent **几乎没有保密意识**，靠提示改善保密又会**损害任务表现** |
| **OSWorld**（NeurIPS'24 D&B） | 真实操作系统（Ubuntu/Windows/macOS），369 个跨应用任务 | 人类 72.36%，最佳模型 **12.24%**；主要卡在 **GUI grounding**（定位界面元素）和**操作知识** |
| **OfficeBench** / **OdysseyBench** | Office 多应用；Odyssey 有 602 个长时程任务（Word/Excel/PDF/邮件/日历） | OfficeBench：GPT-4o 47%，失败主要来自**冗余操作、幻觉、应用切换**。Odyssey：需要从**很长的交互历史**中提取信息，并提出 HomerAgents 自动造题 |
| **SWE-Bench Pro** | 1,865 题，41 个仓库，含商业私有仓库 | 抗数据污染；任务需要专业工程师花数小时到数天；对失败轨迹做了**失败模式聚类** |

**我的解读**：这些基准反复指向三类共性短板——**多轮/人机交互**（τ²、CRMArena-Pro）、**规则遵循**（τ、CRMArena）、**长时程状态保持**（TheAgentCompany、Odyssey）。另外，"单次成功率"会高估真实可用性。

### 领域 2：失败分类与失败归因——"它为什么失败？是谁、在哪一步出的错？"
**核心问题**：不只是报一个成功率，而是把失败**拆解到原因**。演进路线如下：
人工建分类法 → 标注数据集 → 用 LLM 自动归因 → 训练专门的归因模型 → **用干预来验证归因**。

| 论文 | 方法 | 贡献 / 数字 |
|---|---|---|
| **MAST**（Cemri et al.，NeurIPS'25 D&B） | 对 150 条 trace 做 grounded theory 建分类法，再用 LLM-judge 扩展标注 | 14 种失败模式、3 大类（系统设计、agent 间失配、任务验证）；1,600+ 条标注 trace，覆盖 7 个框架；κ=0.88。结论：多 agent 系统（MAS）的收益常常很小，很多失败源于**系统设计**而不是模型本身 |
| **Who&When**（Zhang et al.，ICML'25） | 定义"自动失败归因"任务；127 个 MAS 的失败日志 | 最好的方法：找出责任 agent 53.5%，定位错误步骤 **14.2%**；o1、R1 也达不到实用水平 |
| **AgenTracer**（ICLR'26） | 用**反事实重放 + 程序化故障注入**自动造标注数据（TracerTraj），再用 RL 训练 8B 归因模型 | 在 Who&When 上比 Gemini-2.5-Pro、Claude-4-Sonnet 高至多 18%；把归因结果反馈给 MetaGPT 等，带来 4.8–14.2% 的提升 |
| **DoVer**（ICLR'26） | 指出两点：只看日志的归因**无法验证**，"单一步骤归因"本身常常**定义不当**（多种修改都能修好）。改用**主动干预**（改消息、改计划）检验假设 | 18–28% 的失败试次被翻转为成功；验证或否定了 30–60% 的假设 |
| **WebSuite** | 把 web 任务拆成原子动作分类法 | 任务失败可以**直接归因到具体的 web 动作** |
| **Code agent 轨迹研究**（Majgaonkar et al.） | 比较 OpenHands、SWE-agent、Prometheus 的成功与失败轨迹 | 失败轨迹**更长、方差更大**；72–81% 的失败轨迹其实找对了文件，成败取决于修改是否"大致正确" |
| **Characterizing Faults in Agentic AI** | 从 40 个仓库的 13,602 个 issue/PR 中分层抽样 385 个故障，用 grounded theory 分析 | 34 种故障类型；根因包括 **schema 不匹配、依赖漂移、状态管理、模型接口不稳定**；145 名从业者验证。这是**工程视角**的分类 |
| **AgentOps** | 对现有 AgentOps 工具做系统映射研究 | 列出 agent 全生命周期中应该追踪的工件和数据，作为可观测性的参考模板 |

**分歧与张力**：Who&When 和 AgenTracer 把"准确定位到单一 agent 和步骤"当作目标；DoVer 认为这个目标常常**不成立**，应改用"能否修复"来评测。这是一个开放的方法论争议，也适合拿来做研究切入点。

### 领域 3：工具调用失败——"参数填错、读错返回值、调错工具"
| 论文 | 内容 |
|---|---|
| **Butterfly Effects in Toolchains**（Findings EMNLP'25） | 建立了 5 类**参数失败**分类，并用 15 种输入扰动做实验：**参数名幻觉**主要源于 LLM 本身的局限，其余失败主要由输入来源（用户指令、工具返回等）引起。建议标准化工具返回格式、改进错误反馈、保证参数一致 |
| **ToolScan** | 定义 7 种 tool-use 错误模式，并为每种构造测试；主流 LLM 都会出现这些错误 |
| **Characterizing Faults**（见上） | 工程侧证据：结构化输出解析和 schema 不匹配是高频根因 |

### 领域 4：歧义、澄清与"能力边界意识"
| 论文 | 内容 |
|---|---|
| **Learning to Ask**（EMNLP'25） | 分析真实用户指令，构建 NoisyToolBench。发现 LLM 因 next-token 训练目标会**编造缺失的参数**；提出 Ask-when-Needed（AwN），并用 ToolEvaluator 自动评估准确率和效率 |
| **CAR-bench**（ACL'26） | 车载助手场景，58 个工具。设计了 **Hallucination 任务**（缺工具或缺信息时是否承认）和 **Disambiguation 任务**。前沿推理模型在消歧任务上的稳定通过率 <50%，主要原因是**过早行动**；还会**为了满足用户而违反策略或编造信息** |
| ASPI（预印本，摘要未获取） | GS 标题显示：主动澄清**会放大提示注入风险**。这说明"多澄清"并不是免费的，与安全领域有交叉 |

### 领域 5：安全——提示注入、权限、记忆投毒
**攻击与评测**
- **InjecAgent**（Findings ACL'24）：1,054 个用例，17 个用户工具、62 个攻击工具。攻击意图分为**直接伤害**和**窃取数据**两类。ReAct-GPT-4 有 24% 的概率中招，加入"hacking prompt"后成功率接近翻倍。
- **AgentDojo**（NeurIPS'24 D&B）：97 个任务（邮件、网银、旅行），629 个安全用例。它不是静态测试集，而是**可扩展的攻防环境**。
- **Adaptive Attacks**（Findings NAACL'25）：测试了 8 种防御，用**自适应攻击全部绕过**，攻击成功率 >50%。结论：防御论文必须用自适应攻击来评测。
- **AgentPoison**（NeurIPS'24）：通过优化后门触发器来**投毒长期记忆或 RAG 知识库**。投毒率 <0.1%，攻击成功率 >80%，对正常任务的影响 <1%。
- **MemoryGraft**（预印本）：把恶意的"成功经验"植入经验记忆，利用 agent **模仿过去成功做法**的倾向，造成**跨会话的持久行为漂移**。这对"自我改进型 agent"是新的攻击面。

**防御（从"检测"到"按设计保证安全"）**
- **Task Shield**（ACL'25）：把安全问题重新表述为**任务对齐**，即每个动作都要服务于用户目标。在 AgentDojo 上，GPT-4o 的攻击成功率降到 2.07%，任务效用 69.79%。
- **CaMeL**（预印本，Google DeepMind/ETH）：从**可信的用户查询**中提取控制流和数据流，不可信数据无法改变程序流；再用 capability 机制阻止数据外泄。可证明安全的前提下解决 77% 的任务，无防御时是 84%。
- **AgentSpec**（ICSE'26）：一种 DSL，规则由"触发器 + 谓词 + 执行动作"组成，在运行时强制执行。代码 agent 中 >90% 的不安全执行被阻止，开销在毫秒级；还尝试用 o1 自动生成规则。
- **Progent**（预印本）：可编程的权限控制。本轮没有拿到摘要，细节待补。

**安全行为评测（不局限于注入）**
- **ToolEmu**（ICLR'24）：用 LM **模拟工具执行**来低成本发现高风险失败。经人工验证，68.8% 的失败是真实有效的；最安全的 agent 也有 23.9% 的情况出现风险行为。
- **ST-WebAgentBench**（ICLR'26）：222 个企业 web 任务，每个都配有策略。提出 **CuP（Completion under Policy，遵守策略的完成率）**：CuP 不到名义完成率的 2/3。
- **OpenAgentSafety**（ICLR'26）：使用真实工具（浏览器、bash、文件系统、消息平台），350+ 个多轮、多用户任务。在易出安全问题的任务中，不安全行为占 51.2%（Claude-3.7）到 72.7%（o3-mini）。
- **Agent-SafetyBench**：2,000 个用例，没有一个 agent 的安全分超过 60%。主要缺陷是**缺乏鲁棒性**和**缺乏风险意识**；只靠防御提示不够。
- **Contextual Integrity**（Google）：把"隐私"定义为**信息流是否符合语境**，用于引导 agent 的表单填写行为。

**结论差异**：AgentDojo 的检测器在非自适应攻击下能把攻击成功率降到约 8%，但会被自适应攻击打穿。Task Shield 报告 2.07%，但这是**非自适应**设置下的数字，需要和 Adaptive Attacks 那篇对照着看。CaMeL 一类"系统设计型"防御更难被绕过，代价是效用下降和工程复杂度上升。（我的解读）

### 领域 6：可靠性、"假成功"与成本
| 论文 | 内容 |
|---|---|
| **CLEAR**（预印本） | 分析了 12 个基准：同等精度下成本相差 **50 倍**；单次 60% → 8 次一致 25%。只优化准确率得到的 agent 贵 4.4–10.8 倍。15 名专家评估：CLEAR 与生产成功的相关 ρ=0.83，只看准确率时 ρ=0.41 |
| **ReliabilityBench**（预印本） | 三个维度：一致性 pass^k、语义扰动 ε、**故障注入** λ（超时、限流、部分响应、schema 漂移）。扰动让成功率从 96.9% 降到 88.1%；**限流**伤害最大；ReAct 比 Reflexion 更稳 |
| **Procedure-Aware Evaluation / Corrupt Success**（预印本） | 在 τ-bench 上，**27–78% 的"成功"其实是腐败成功**，即结果对了但过程违规；加入过程门控后排名改变；还暴露了基准本身的缺陷（模拟器伪影、矛盾的奖励信号） |
| **SWE-PRM**（预印本） | 推理时用过程奖励模型**中途纠偏**（循环、冗余探索、不停止）。SWE-bench Verified 从 40.0% 提升到 50.6%，额外成本低至 $0.2 |
| **Efficient Agents**（预印本） | 在 GAIA 上用 cost-of-pass 分析：保留 OWL 96.7% 的性能，成本从 $0.398 降到 $0.228 |

**我的解读**：这一组论文共同说明，"**成功率**"这个指标本身就是失败来源之一。它掩盖了不一致、违规过程和成本，企业落地的评测应该是多维的。

### 各领域之间怎么连起来（读者导航）
- 基准（领域 1）提供**失败样本** → 分类与归因（领域 2）解释**原因** → 工具、澄清、安全（领域 3–5）是**具体失败机制**及其防御 → 可靠性评测（领域 6）检验**修好没有**。
- 交叉热点：
  - 澄清 × 注入（ASPI）
  - 保密意识 × 效用（CRMArena-Pro）
  - 记忆 × 安全（AgentPoison、MemoryGraft）
  - 归因 × 修复（AgenTracer、DoVer）

## 4. 入门必读（✅ 已核对，其余 ⚠️）
1. MAST – Cemri et al., NeurIPS 2025 D&B ✅：14 种失败模式，1600+ 条 trace，κ=0.88
2. Who&When – Zhang et al., ICML 2025 ✅：最佳方法定位责任 agent 准确率 53.5%，定位错误步骤 14.2%（[code](https://github.com/mingyin1/Agents_Failure_Attribution)）
3. TheAgentCompany – Xu et al., NeurIPS 2025 D&B ✅：最佳 agent 约 30% 完成率
4. τ²-bench – Barres et al., ICML 2026 ✅
5. τ-bench – Yao et al., ICLR 2025 ✅：提出 pass^k 指标
6. AppWorld – Trivedi et al., ACL 2024 ✅
7. AgentDojo – Debenedetti et al., NeurIPS 2024 D&B ✅
8. CaMeL – Debenedetti et al., arXiv 2025 ✅
9. CLEAR – arXiv 2511.14136 ✅（预印本）：单次运行 60%，8 次一致仅 25%
10. WorkArena – Drouin et al., ICML 2024 ⚠️
11. OSWorld – Xie et al., NeurIPS 2024 D&B ✅
12. SWE-bench – Jimenez et al., ICLR 2024 ⚠️
13. ToolEmu – Ruan et al., [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/7274ed909a312d4d869cc328ad1c5f04-Abstract-Conference.html) ✅（用 LM 模拟工具做风险评测）
14. InjecAgent – Zhan et al., [Findings ACL 2024](https://aclanthology.org/2024.findings-acl.624/) ✅
15. AgentPoison – Chen et al., [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/eb113910e9c3f6242541c1652e30dfd6-Abstract-Conference.html) ✅

## 4b. 候选清单（按主题；发现来源：Google Scholar，2026-10-23）
Venue 依据 GS 链接的域名判断：proceedings.* 和 aclanthology 视为已发表（✅）；arXiv 视为预印本；其余标 🔶。**是否开源本轮未逐篇核实。**

**企业基准与环境**
- [WorkArena++](https://proceedings.neurips.cc/paper_files/paper/2024/hash/0b82662b6c32e887bb252a74d8cb2d5e-Abstract-Datasets_and_Benchmarks_Track.html)：Boisvert et al., NeurIPS 2024 D&B ✅
- [CRMArena](https://aclanthology.org/2025.naacl-long.194/)：Huang et al., NAACL 2025 ✅；CRMArena-Pro：arXiv 2025（预印本）
- [FlowBench](https://aclanthology.org/2024.findings-emnlp.638/)：Xiao et al., Findings EMNLP 2024 ✅
- [OfficeBench](https://arxiv.org/abs/2407.19056)：Wang et al., arXiv 2024
- [OdysseyBench](https://arxiv.org/abs/2508.09124)：Wang et al., arXiv 2025，长时程 Office 工作流
- [CI-Work](https://aclanthology.org/2026.acl-industry.103/)：Fu et al., ACL 2026 Industry ✅，企业 agent 的上下文完整性与隐私
- [World of Workflows](https://arxiv.org/abs/2601.22130)：Gupta et al., arXiv 2026
- [Top of the CLASS](https://openreview.net/forum?id=RQjUpeINII)：Wornow et al., ICLR 2025 Workshop（workshop，非主会）
- [Windows Agent Arena](https://arxiv.org/abs/2409.08264)：Bonatti et al., arXiv 2024
- [SWE-bench Pro](https://arxiv.org/abs/2509.16941)：Deng et al., arXiv 2025
- [SWE-bench Goes Live!](https://proceedings.neurips.cc/paper_files/paper/2025/hash/d83c4a745789690f82e86d0ef752ae7c-Abstract-Datasets_and_Benchmarks_Track.html)：Zhang et al., NeurIPS 2025 D&B ✅
- OSWorld-MCP：Jia et al., ICLR 2026（据 GS）🔶
- DataSciBench：Zhang et al., Findings ACL 2026（据 GS）🔶

**失败归因与诊断**
- DoVer（干预驱动的自动调试）：Ma et al., ICLR 2026（GS 指向 proceedings.iclr.cc）✅
- AgenTracer：Zhang et al., ICLR 2026（同上）✅
- Seeing the Whole Elephant（失败归因基准）：Chen et al., ACL 2026（据 GS）🔶
- StepFinder：Zhu et al., KDD 2026（据 GS）🔶
- [MAS-FIRE](https://arxiv.org/abs/2602.19843)：故障注入，arXiv 2026
- [Characterizing Faults in Agentic AI](https://arxiv.org/abs/2603.06847)：Shah et al., arXiv 2026
- [AgentOps](https://arxiv.org/abs/2411.05285)：Dong et al., arXiv 2024，可观测性
- [AgentTrace](https://arxiv.org/abs/2602.10133)：arXiv 2026
- TRAJDEBUG：Qi et al., arXiv 2026（链接待补）🔶
- [Understanding Code Agent Behaviour](https://arxiv.org/abs/2511.00197)：Majgaonkar et al., arXiv 2025
- [WebSuite](https://arxiv.org/abs/2406.01623)：Li & Waldo, arXiv 2024，分析 web agent 为何失败
- [Characterizing Unintended Consequences of GUI Agents](https://dl.acm.org/doi/abs/10.1145/3772318.3790696)：Zhang et al., CHI 2026 🔶

**工具调用**
- [Butterfly Effects in Toolchains](https://aclanthology.org/2025.findings-emnlp.907/)：Xiong et al., Findings EMNLP 2025 ✅，参数填充失败
- [ToolScan](https://arxiv.org/abs/2411.13547)：Kokane et al., arXiv 2024
- Benchmarking LLM Tool-Use in the Wild：Yu et al., ICLR 2026（GS 指向 proceedings.iclr.cc）✅

**澄清与意图**
- [Learning to Ask](https://aclanthology.org/2025.emnlp-main.1104/)：Wang et al., EMNLP 2025 ✅
- [CAR-bench](https://aclanthology.org/2026.acl-long.1886/)：Kirmayr et al., ACL 2026 ✅
- CLAMBER：Zhang et al., ACL 2024（据 GS）🔶
- ASPI：Sehwag et al., arXiv 2026（链接待补）🔶。发现澄清行为会放大提示注入风险，是与安全类的交叉点。

**安全：注入、权限、记忆**
- [Adaptive Attacks Break IPI Defenses](https://aclanthology.org/2025.findings-naacl.395/)：Zhan et al., Findings NAACL 2025 ✅
- [Task Shield](https://aclanthology.org/2025.acl-long.1435/)：Jia et al., ACL 2025 ✅
- [IPIGuard](https://aclanthology.org/2025.emnlp-main.53/)：An et al., EMNLP 2025 ✅
- [Progent](https://arxiv.org/abs/2504.11703)：Shi et al., arXiv 2025，权限控制
- [AgentArmor](https://arxiv.org/abs/2508.01249)、[PromptArmor](https://arxiv.org/abs/2507.15219)：arXiv 2025
- [AgentSpec](https://dl.acm.org/doi/abs/10.1145/3744916.3764546)：Wang et al., ICSE 2026（据 GS；ACM 页面返回 403）🔶
- InfrastructureSentinel：Kumar et al., AAAI 2026（据 GS）🔶
- [Evaluating Privilege Usage of Agents with Real-World Tools](https://dl.acm.org/doi/abs/10.1145/3803437.3805554)：2026 🔶
- [MemSecBench](https://arxiv.org/abs/2607.27080)：arXiv 2026
- [Memory Poisoning Attack and Defense](https://arxiv.org/abs/2601.05504)：arXiv 2026
- [ST-WebAgentBench](https://proceedings.iclr.cc/paper_files/paper/2026/hash/c6c29e590e3c62e37e6b39cdd6baf2e8-Abstract-Conference.html)：ICLR 2026 ✅
- [OpenAgentSafety](https://proceedings.iclr.cc/paper_files/paper/2026/hash/a0f6c06b8d6114bb37688c2dc19b4d74-Abstract-Conference.html)：ICLR 2026 ✅
- [Agent-SafetyBench](https://arxiv.org/abs/2412.14470)：arXiv 2024

**可靠性、成本、人机协作**
- [ReliabilityBench](https://arxiv.org/abs/2601.06112)：arXiv 2026
- [Beyond pass@1](https://arxiv.org/abs/2603.29231)：arXiv 2026
- [Corrupt Success / Procedure-Aware Evaluation](https://arxiv.org/abs/2603.03116)：arXiv 2026；另有 ECML-PKDD 2026 版本 🔶
- [When Agents Go Astray](https://arxiv.org/abs/2509.02360)：arXiv 2025，用 PRM 纠偏 SWE agent
- [Fail-fast, Restart-smart](https://arxiv.org/abs/2608.03222)：arXiv 2026
- [Efficient Agents](https://arxiv.org/abs/2508.02694)：arXiv 2025
- Optima：Findings ACL 2025；AI-LieDar：NAACL 2025（均据 GS）🔶
- When to Act, When to Ask：SSRN 2026（非同行评审），研究企业 agent 的人机协作（HITL）策略

**综述（用于建立分类，不作为关键证据）**
- [Evaluation and Benchmarking of LLM Agents](https://dl.acm.org/doi/abs/10.1145/3711896.3736570)：Mohammadi et al., KDD 2025 🔶
- [Towards Trustworthy GUI Agents](https://arxiv.org/abs/2503.23434)：arXiv 2025

> GS 结果中有不少 SSRN、ResearchGate、TechRxiv 和小型期刊条目，例如 "Why enterprise agent deployments fail"（IJCTECE）。它们标题相关，但同行评审质量无法确认，**没有**被当作证据使用。

## 5. 失败模式—缓解矩阵（仅列有证据支持的控制点）
| 失败 | 控制点 | 证据 | 适用条件/局限 |
|---|---|---|---|
| 违背任务或角色规格 | 改写角色规格 | MAST：ChatDev +9.4% ✅ | 单一框架、单一模型，未必能推广 |
| 提前宣告完成、不跟进 | 完成条件检查、升级 | TheAgentCompany §7.3 ✅ | 失败分析是定性的 |
| 外部内容注入 | 检测器（ASR 降到约 8%）；控制流/数据流隔离 | AgentDojo ✅；CaMeL ✅ | **结论不一致**：[Zhan et al. 2025](https://aclanthology.org/2025.findings-naacl.395/) 用自适应攻击攻破了多种检测器类防御；AgentDojo 的约 8% 是在非自适应攻击下得到的。CaMeL 有效用损失 |
| 多次运行不一致 | pass^k 评测、投票 | CLEAR ✅、τ-bench ⚠️ | 成本线性增长 |
| 失败难以定位 | LLM 归因、MAST 标注器（κ=0.77） | Who&When ✅、MAST ✅ | 步骤级定位远未可用 |
| 工具调用后状态错误 | 状态差分单元测试 | AppWorld ✅ | 需要可程序化检查的状态 |

## 6. 发表渠道（不列影响因子）
- **Agent 专门**：AAMAS（MAS 理论与系统）
- **ML 主流**：NeurIPS（含 D&B track，适合基准）、ICML、ICLR
- **NLP**：ACL / EMNLP / NAACL（资源、工具使用类工作）
- **SE 与安全**：ICSE、FSE、ASE（SWE agent）；IEEE S&P、USENIX Security、CCS（注入与权限）；SaTML
- **交叉**：CHI、CSCW（人机协作）；SIGIR、WWW（检索、网页 agent）；CoRL（机器人）
- 会议排名（如 CORE）与期刊 IF（如 TMLR、JAIR）需要分开核实，本轮**未核实**。

## 7. 选题建议
| # | 问题 | 环境 | 指标 | 基线 | 难点 | venue | 新颖性风险 |
|---|---|---|---|---|---|---|---|
| 1 | 步骤级失败归因能否借助环境状态差分提升？ | Who&When + AppWorld | 步骤定位准确率（基线 14.2%） | Who&When 的三种方法 | 需要标注 | ICML/NeurIPS | 中（后续工作较多，⚠️） |
| 2 | 澄清策略在 dual-control 下的成本与收益 | τ²-bench | pass^k、轮数 | 不澄清 / 总是澄清 | 用户模拟偏差 | ACL/EMNLP | 中 |
| 3 | 企业记忆治理基准（provenance + 回滚） | AppWorld 扩展 | 投毒 ASR、效用 | AgentPoison 设置 | 需自建任务 | NeurIPS D&B | 低-中 |
| 4 | CaMeL 式隔离的效用损失归因 | AgentDojo | 效用差（84→77） | CaMeL | 需理解其解释器 | SaTML/USENIX | 中 |
| 5 | 成本-可靠性帕累托前沿 | τ-bench、TheAgentCompany | 美元/成功、pass^8 | 单次运行 | API 费用 | TMLR | 中 |
| 6 | 人工审批点的最优放置 | TheAgentCompany | 严重错误率与人工调用次数 | 全审批 / 无审批 | 需要人工模拟 | CHI/CSCW | 低 |
| 7 | 结果层面的“假成功”检测 | TheAgentCompany | 漏检率 | LLM judge | 定义真值 | ICSE/FSE | 中 |

## 8. 阅读路线
- **广度优先**：CLEAR → TheAgentCompany → τ²-bench → AppWorld → AgentDojo → MAST → Who&When → CaMeL
- **深入“诊断/归因”**：MAST → Who&When → TheAgentCompany §7.3 → AppWorld（状态评测）→ τ-bench（pass^k）

## 9. 下一步（未完成项）
- 🔶 条目需要打开官方页面复核；各篇是否开源代码或数据，尚未逐篇核实。

- 待补检索的方向：上下文管理与长期记忆更新（非安全视角）；跨系统事务与回滚；企业真实部署的实证研究。
