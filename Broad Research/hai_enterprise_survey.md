# 企业协作中的人机交互（Human–AI Interaction in Enterprise Collaboration）：文献调研 v0.1

- 检索日：2026-10-23；时间窗：**2023-10-23 至 2026-10-23**。少数 2021–2023 年的奠基性论文会单独标注。
- 方法：叙述性调研，**不是系统综述**。
  - 发现：Google Scholar 15 个检索式（限 2023 年及以后），每个取前 10 条，共约 150 条，存于 `research/hai/gs/q*.json`。
  - 元数据和摘要：OpenAlex API（`research/hai/oa.json`）。
  - 本文所有数字都取自摘要。标 ⚠️ 的条目没有拿到摘要，内容凭背景知识写成，**未核实**。
- 状态标记：
  - **[期刊]**、**[会议]** 表示已正式发表，依据是 OpenAlex 的 venue 加 DOI。
  - **[预印本]** 指 arXiv 或 SSRN。
  - **[工作论文]** 指 NBER 等。

## 0. 检索记录
| 项 | 内容 |
|---|---|
| 检索式 | human-AI collaboration enterprise；generative AI productivity field experiment；copilot knowledge workers；trust calibration/reliance；overreliance explanations；oversight delegation；meeting assistant；complementarity；customer support GenAI；mixed-initiative human-agent；AI in teams CSCW；developer RCT；deskilling；human-in-the-loop agent benchmark；organizational adoption |
| 纳入 | ①在工作或组织情境中的人与 AI（LLM、生成式 AI、agent）交互；②有实证（实验、现场数据、访谈）或可复现的基准 |
| 排除 | 纯观点文章、低质量期刊、学位论文（GS 结果中这类很多）；教育、医疗等非企业场景（只保留方法上有启发的） |
| 数量 | 约 150 条 → 按标题初筛约 55 条 → 抓摘要 38 条，标题匹配 36 条 → 本文详细讨论约 30 篇 |

## 1. 领域边界与定义
- **研究对象**：员工、团队、组织与 AI 系统在**真实工作任务**中如何分工、交互、依赖和相互影响。AI 系统包括 copilot、聊天助手和自主 agent。
- **交互范式的三个层级**。这个划分是本文提出的，用来组织文献：
  1. **AI 作为工具或助手**（copilot 模式）：人主导，AI 给建议或草稿。
  2. **AI 作为队友**（teammate）：参与团队流程，例如会议、群聊、共同创作。
  3. **AI 作为被委派的执行者**（agent / workflow agent）：AI 主导执行，人负责监督、审批、接手。
- **与上一份报告（agent 失败）的关系**：在第 3 层级，"人怎么监督 agent"直接决定 agent 失败能否被拦截，所以两份报告在人机协作和审批这个主题上交叉。
- **学科分布**：
  - 经济学和管理学：生产力、劳动市场。
  - HCI 和 CSCW：交互、信任、团队。
  - 信息系统（IS）：采纳、组织。
  - NLP 和 ML：人-agent 协作基准。
  - 软件工程：开发者研究。

## 2. 领域详解：各方向在研究什么、贡献是什么

### 领域 1：生成式 AI 对工作生产力的因果效应（经济学、管理学）
**核心问题**：给员工用 AI，产出、质量、速度到底变化多少？对哪些人效果最大？
**主要方法**：现场实验、随机对照试验（RCT）、交错上线（staggered rollout）的准实验。

| 论文 | 设计 | 发现 |
|---|---|---|
| **Generative AI at Work**（Brynjolfsson, Li, Raymond；[QJE 2025](https://doi.org/10.1093/qje/qjae044)）[期刊] | 5,172 名客服人员，AI 助手交错上线 | 每小时解决的问题数平均 **+15%**；**新手和低技能者获益最大**，速度和质量都提高；最有经验的人速度略升、**质量略降**；AI 加快了学习；客户更礼貌，要求找经理的情况变少 |
| **Noy & Zhang**（[Science 2023](https://doi.org/10.1126/science.adh2586)）[期刊] | 453 名专业人员做写作任务，预注册在线实验 | 用时 **−40%**，质量 **+18%**；员工之间的差距缩小 |
| **Jagged Frontier**（Dell'Acqua et al.；[SSRN/HBS WP 2023](https://doi.org/10.2139/ssrn.4573321)）[工作论文] ⚠️ | BCG 咨询顾问 | ⚠️ 凭背景知识：在 AI 能力"边界内"的任务上更快、质量更高；在"边界外"的任务上，用 AI 的人**正确率反而下降**。由此提出"锯齿状边界"概念 |
| **Cui et al. 三个现场实验**（[SSRN 2024](https://doi.org/10.2139/ssrn.4945566)；GS 显示已刊于 Management Science）⚠️ | Microsoft、Accenture 等公司的开发者使用 Copilot | ⚠️ 凭背景知识：完成任务数约 +26%，新手获益更大 |
| **Google 企业内 RCT**（Paradis et al.；[ICSE-SEIP 2025](https://doi.org/10.1109/icse-seip66354.2025.00060)）[会议] | 96 名 Google 工程师，完成一个复杂的企业级任务 | 用时约 **−21%**，但置信区间很宽；每天写代码时间越长的人用 AI 越快 |
| **METR RCT**（Becker et al.；[arXiv 2025](https://doi.org/10.48550/arxiv.2507.09089)）[预印本] | 16 名资深开源开发者在自己熟悉的成熟项目上做 246 个任务 | 允许用 AI 时**用时 +19%（变慢）**；而开发者自己的估计是变快 20%，经济学和 ML 专家预测变快约 38–39% |
| **The Cybernetic Teammate**（Dell'Acqua et al.；[NBER WP 2025](https://doi.org/10.3386/w33641)）[工作论文] | 776 名 P&G 员工，2×2 设计：有/无 AI × 个人/团队 | **单人加 AI ≈ 没有 AI 的两人团队**；AI 打破了职能壁垒（研发人员和商业人员的方案趋于平衡）；参与者情绪更积极 |

**结论分歧与可能原因**（我的解读）：
- **加速 vs 减速**。Google 的结果是 −21% 用时，METR 是 +19% 用时。差异可能来自：
  - 任务是否是新的。
  - 开发者对代码库的熟悉程度。METR 的被试平均有 5 年项目经验，AI 帮助的边际价值小。
  - 质量标准的高低。
  - 工具的世代不同。
- **谁获益更多**。多数研究发现新手获益大（客服、写作、Copilot）。但 Brynjolfsson 的研究中，高手的**质量会下降**；Jagged Frontier 发现在边界外的任务上用 AI 有害。共同的含义是：**收益取决于任务是否在 AI 能力边界内，以及人能否识别这条边界**。这一点直接连到领域 2。
- **外推限制**：多数实验只测**单个员工完成单个任务**，很少测团队、跨部门流程、长期效果。另外大部分研究是在 copilot 时代做的，**对自主 agent 的生产力证据还非常少**。

### 领域 2：依赖、信任与校准（appropriate reliance，HCI 方向）
**核心问题**：人在什么时候会**过度依赖**（AI 错了也照单全收）或**依赖不足**？怎样让信任与 AI 的真实可靠度相匹配？
**主要方法**：受控用户实验，通常预注册，操纵解释、来源、置信度等界面因素。

| 论文 | 发现 |
|---|---|
| **Bansal et al., Does the Whole Exceed its Parts?**（[CHI 2021](https://doi.org/10.1145/3411764.3445717)，奠基性论文）[会议] | 人机组合有互补提升，但**解释并没有带来额外提升**；解释只是让人**更容易接受 AI 的建议，不管对错** |
| **Vasconcelos et al.**（[PACM HCI / CSCW 2023](https://doi.org/10.1145/3579605)）[期刊] | 5 个研究，N=731。把依赖解释为**成本-收益的策略选择**：任务越难、解释越难读，人越依赖 AI；提高回报能减少过度依赖。所以**解释在特定条件下可以减少过度依赖** |
| **Schemmer et al.**（[IUI 2023](https://doi.org/10.1145/3581641.3584066)）[会议] | 提出 **Appropriateness of Reliance (AoR)**，一个二维可量化指标：对正确建议采纳，对错误建议拒绝。实验 N=200 |
| **Kim et al., Fostering Appropriate Reliance on LLMs**（[CHI 2025](https://doi.org/10.1145/3706598.3714020)）[会议] | 有声思维研究加 N=308 的预注册实验：**解释会同时增加对正确和错误回答的依赖**；**提供来源**或**解释中出现不一致**时，对错误回答的依赖会下降 |
| **Lee et al., GenAI & Critical Thinking**（[CHI 2025](https://doi.org/10.1145/3706598.3713778)）[会议] | 319 名知识工作者，936 个实例：**对 AI 越有信心，批判性思考越少**；对自己越有信心，批判性思考越多。批判性思考的重心转向**核实信息、整合回答、管理任务** |

**主线脉络**：先发现"解释 ≠ 更好的决策"（Bansal），再把依赖建模为成本-收益选择（Vasconcelos），然后给出可量化的指标（AoR），最后在 LLM 时代检验来源和不一致性的作用（Kim 2025）。
**分歧**：解释到底减少还是增加过度依赖，取决于**验证成本**和**任务难度**。Bansal 和 Kim 发现解释增加依赖，Vasconcelos 发现在一定条件下能减少。这些研究的任务大多是**单次决策**（迷宫、问答），推到企业的多步工作流时要谨慎。

### 领域 3：人机互补性（complementarity）——"人 + AI 何时优于两者各自单干？"
| 论文 | 发现 |
|---|---|
| **Vaccaro, Almaatouq, Malone**（[Nature Human Behaviour 2024](https://doi.org/10.1038/s41562-024-02024-1)）[期刊] | 预注册的元分析，106 个实验、370 个效应量：**人机组合平均比单独的人或单独的 AI 中较好的一方更差**（g=−0.23）；**决策类任务有损失，内容创作类任务有收益**；当人本身强于 AI 时，组合会有增益 |
| **Hemmer et al.**（[EJIS 2025](https://doi.org/10.1080/0960085x.2025.2475962)）[期刊] | 把互补团队绩效（CTP）形式化，区分"潜力"和"实际实现"；提出两大互补来源：**信息不对称**和**能力不对称** |
| **Inkpen et al.**（ACM TOCHI）、**Yang et al. 投资顾问现场实验**（Management Science 2026）| 只有 GS 元数据 ⚠️。分别研究用户专长、算法调参，以及"顾问 + AI"三方决策 |

**含义**（我的解读）：互补性**不是默认会出现的**。企业部署时，如果只是"让人审核 AI 的决定"，在决策类任务上可能**还不如只让表现更好的一方单独做**。这对审批型的人机协作设计（上一份报告中的人工审批）是一个重要警示。

### 领域 4：人与 agent 协作的系统和基准（NLP / ML 方向，2024–2026 年快速兴起）
**核心问题**：从"完全自主的 agent"转向"人在回路中的 agent"。在什么时候、以什么方式、由谁介入最有效？怎样评测这种协作？

| 论文 | 贡献 |
|---|---|
| **ReHAC**（Feng et al.；[Findings EMNLP 2024](https://doi.org/10.18653/v1/2024.findings-emnlp.72)）[会议] | 用强化学习训练一个策略，决定**什么时候请人介入**；结论是少量、安排得当的人工介入能显著提升复杂任务表现。代码和数据已开源 |
| **Collaborative Gym (Co-Gym)**（Shao et al.；[arXiv 2024](https://doi.org/10.48550/arxiv.2412.15701)）[预印本] | 开放框架，支持**非轮流式**的双向交互，有模拟用户和真人两种条件；在旅行规划、文献综述写作、表格分析上，协作型 agent 胜过完全自主 agent，旅行规划胜率 86% |
| **CollabSkill**（[arXiv 2026](https://doi.org/10.48550/arxiv.2606.09833)）[预印本] | 93 名真实工作者、386 个工作会话，在与各自职业匹配的任务上和 agent 协作；用贝叶斯技能评分**分离人和 agent 各自的贡献**；agent 排名与自主基准**不一致**；**实践经验**是人这一方协作效果的主要驱动因素 |
| **HAS-Bench**（[arXiv 2026](https://doi.org/10.48550/arxiv.2607.04329)）[预印本] | 用图结构建模人和 agent 的**角色、权限、通信路径、行动权限**；评测过程层面的指标：澄清质量、反馈利用、控制校准、主动性、交互成本；人的参与能提升完成率和**失败恢复**，但效果取决于**何时、如何、由谁**介入 |
| **CentaurEval**（[arXiv 2025](https://doi.org/10.48550/arxiv.2512.04111)）[预印本] | 45 个"必须协作才能解"的编程模板：LLM 单独 0.67%，人单独 18.89%，协作 **31.11%**；突破性思路**既可能来自人，也可能来自 AI** |
| **Plan-Then-Execute**（He, Demartini, Gadiraju；[CHI 2025](https://doi.org/10.1145/3706598.3713218)）[会议] | N=248，6 种不同风险等级的日常任务（如订机票、信用卡支付），agent 先规划再分步执行；考察用户在各阶段的参与对**信任和团队绩效**的影响；摘要的结论是 LLM agent 是一把"双刃剑"，细节在正文 |
| **LLM-HAS 综述**（Zou et al.；arXiv 2025，GS 显示已刊于 Findings ACL 2026）| 把人-agent 系统拆成环境、画像、人类反馈、交互类型、编排、通信几个部分 |
| **τ²-bench**（ICML 2026，见上一份报告） | dual-control 设定：用户也要操作环境；agent 需要**引导用户**完成操作 |

**趋势**（我的解读）：评测对象从"agent 自己能做多少"转向"**人机系统作为整体能做多少**，以及人的介入值多少"。CollabSkill 和 CentaurEval 都发现，**自主基准上的排名不能代表协作场景下的排名**。

### 领域 5：团队与群体层面的 AI（CSCW 方向）
| 论文 | 内容 |
|---|---|
| **The Cybernetic Teammate**（见领域 1） | 这是团队层面少有的**大规模现场实验**：AI 部分替代了队友在**专长共享和情绪支持**上的作用 |
| **Group Ideation with an LLM in a Virtual Canvas**（He et al.；[CHIWORK 2024](https://doi.org/10.1145/3663384.3663398)）[会议] | 17 名专业人员使用一个带 AI 的协作画布探针工具；AI 有助于主持讨论和扩展视角；参与者担心失去人的视角、批判性思维，以及有害输出带来的**声誉风险**；需要明确**内容归属**和保留**私人空间** |
| **SeeSawBot**（CHI 2026）[会议] | 一个在**私有和共享 Slack 频道之间**做协调的 LLM 机器人，用来支持团队动态；没有拿到摘要 |
| **O'Hara et al.**（[CSCW Journal 2026](https://doi.org/10.1007/s10606-026-09549-1)）[期刊] | 在一家 IT 服务公司做定性研究，对象是一个**接入企业系统、文档和工作流的定制 LLM agent**，研究员工怎样把它嵌入日常协作实践。作者指出，现有研究多关注个人和现成的 ChatGPT，**对组织内嵌 agent 的研究很少** |

**空白**：多人和 AI 同时协作时的**责任归属、信息可见性（私有还是共享）、群体决策质量**，目前只有小样本的定性研究。

### 领域 6：组织采纳与真实使用（IS / CSCW / 产业研究）
| 论文 | 内容 |
|---|---|
| **AI in the Enterprise: M365 Copilot Chat**（Microsoft；[arXiv 2026](https://doi.org/10.48550/arxiv.2605.23958)）[预印本] | 约 550 万个会话，用意图分类加 O*NET 工作活动分类：**写作占主导**，也用于检索、分析、决策、诊断系统；使用重心从"把聊天当搜索"转向内容和沟通类工作；在不同职业间分布广泛但不均匀 |
| **Beyond Training**（Sahni & Chilton；[HICSS 2026](https://doi.org/10.24251/hicss.2026.028)）[会议] | 访谈 10 名 M365 Copilot 用户：**0/10** 主要靠正式培训学会使用，8/10 靠试错，6/10 靠同事之间交流技巧；对高级功能缺乏把握 |
| **Argo @ 美国国家实验室**（Wagman et al.；[CHI 2025](https://doi.org/10.1145/3706598.3713827)）[会议] | 问卷 66 人、访谈 22 人，加上使用日志：使用量小但在增长；使用场景分为 **copilot** 和 **workflow agent** 两种模式；顾虑集中在敏感数据、学术发表、对岗位的影响 |
| **IBM watsonx Code Assistant**（Weisz et al.；[CHI EA 2025](https://doi.org/10.1145/3706599.3706670)）[会议] | 问卷 N=669：总体上有净收益，但**不是所有人都能感受到**；出现了**生成代码的归属和责任**这个新问题 |
| **Still just personal assistants?**（Kemell et al.；[IST 2025](https://doi.org/10.1016/j.infsof.2025.107805)）[期刊] | 7 家欧洲软件公司的多案例研究：识别出 25 类用途、12 项收益、10 项挑战；**数据隐私和法规**是主要障碍；使用仍以**个人助手**为主，很少进入组织流程 |
| **GenAI in Customer Support**（Reinhard et al.；[HICSS 2024](https://doi.org/10.24251/hicss.2024.028)）[会议] | IT 支持一线员工的例程框架：**调整解决方案**和**沉淀知识**两类工作最适合由 AI 增强 |

**共同发现**（我的解读）：企业 AI 的价值是**自下而上、靠社会学习发现的**，而不是靠培训推动；使用主要停留在个人层面，向**组织流程层面**（workflow agent）迁移得很慢。

### 领域 7：长期影响——技能退化、认知负担、"自动化的反讽"
| 论文 | 内容 |
|---|---|
| **Ironies of Generative AI**（Simkute et al.；[IJHCI 2024](https://doi.org/10.1080/10447318.2024.2405782)）[期刊] | 借鉴 30 年的人因研究，总结 GenAI 导致生产力损失的四个原因：①角色从**生产者变成评估者**；②工作流被不恰当地重组；③打断；④**简单任务更简单，困难任务更困难**。对应的设计建议：持续反馈、个性化、生态界面设计、任务稳定化、明确分工 |
| **More Code, Less Understanding?**（Martin-Lopez et al.；[IEEE TSE 2026](https://doi.org/10.1109/tse.2026.3679627)）[期刊] | 69 名参与者做组内实验，研究生产力和**代码归属**（能否讲清楚自己的实现）之间的权衡；具体结果在正文中，摘要没有给出 |
| **Critical Thinking**（Lee et al.，见领域 2） | 自报数据显示批判性思考的投入减少 |
| **AI Deskilling is a Structural Problem**（Ferdman；[AI & Society 2025](https://doi.org/10.1007/s00146-025-02686-z)）[期刊] | 哲学分析：提出"**对能力培养不友好的环境**"（capacity-hostile environments）这一概念，认为技能退化是结构性问题，不只是个人的责任 |
| **Expertise Atrophy**（Siderius et al.；SSRN 2026）[预印本] | 只有 GS 元数据：建模组织使用 AI 时专业能力的衰退 |

**空白**：缺少**纵向的因果证据**。这一领域多是自报、理论或短期实验，没有长期追踪"监督者的技能退化是否导致漏检 AI 错误"。

## 3. 研究分类图谱（横向比较）
| 方向 | 核心问题 | 主要方法 | 代表论文 | 主要数据/环境 | 证据强度 | 主要空白 |
|---|---|---|---|---|---|---|
| 1 生产力 | 效应大小和异质性 | 现场实验、RCT | Brynjolfsson；Noy & Zhang；METR | 企业内部数据（**通常不公开**） | 高（因果设计） | agent 时代、团队层面、长期效果 |
| 2 依赖与信任 | 如何做到恰当依赖 | 受控实验 | Bansal；Vasconcelos；Kim 2025 | 实验材料，部分公开 | 中高 | 多步工作流和 agent 场景 |
| 3 互补性 | 人+AI 何时优于单方 | 元分析、理论 | Vaccaro；Hemmer | 106 个实验 | 高（元分析） | 互补性的**设计方法** |
| 4 人-agent 协作基准 | 介入的时机、方式、价值 | 基准、强化学习、用户研究 | Co-Gym；CollabSkill；HAS-Bench；CentaurEval | 多数开源（未逐一核实） | 中（多为预印本） | 真人数据规模、企业任务、可复现性 |
| 5 团队 AI | AI 对团队过程的影响 | 现场实验、设计探针 | Cybernetic Teammate；O'Hara | 定性数据 | 低到中 | 多人场景下的责任与可见性 |
| 6 组织采纳 | 真实使用模式 | 日志分析、访谈、案例 | M365 Copilot；Argo；Kemell | 日志（不公开） | 中（描述性） | 从个人使用走向流程使用的机制 |
| 7 长期影响 | 技能和认知的变化 | 问卷、理论 | Ironies；Lee；Ferdman | 问卷 | 低（自报） | 纵向因果研究 |

**各方向之间的重叠**：
- 方向 2 和方向 3 高度耦合：恰当依赖是实现互补的前提。
- 方向 4 是方向 2 和 3 在 agent 上的延伸。
- 方向 1 中"高手质量下降""边界外出错"的发现，本质上就是方向 2 研究的依赖问题。
- 方向 7 是方向 2 的长期后果。
- 方向 4 和上一份报告中的"人工审批与升级"直接重叠。

## 4. 入门必读（覆盖不同方向）
1. Brynjolfsson et al., *Generative AI at Work*, QJE 2025：企业现场证据的标杆
2. Noy & Zhang, Science 2023
3. Dell'Acqua et al., *Jagged Frontier*, 2023 WP ⚠️
4. Becker et al. (METR), 2025 预印本：反例，适合和第 3 篇对照阅读
5. Dell'Acqua et al., *Cybernetic Teammate*, NBER 2025：团队层面
6. Vaccaro et al., Nature Human Behaviour 2024：元分析，说明人机组合不一定有增益
7. Bansal et al., CHI 2021：奠基性论文
8. Vasconcelos et al., CSCW 2023
9. Kim et al., CHI 2025：LLM 时代的依赖研究
10. Lee et al., CHI 2025：批判性思考
11. Simkute et al., *Ironies of GenAI*, IJHCI 2024：理论框架
12. Shao et al., *Collaborative Gym*, 2024
13. *HAS-Bench* 或 *CollabSkill*, 2026
14. Feng et al., *ReHAC*, Findings EMNLP 2024
15. Microsoft, *M365 Copilot Chat usage*, 2026
16. O'Hara et al., CSCW Journal 2026：组织内嵌 agent

## 5. 发表渠道
| 类型 | 渠道 | 适合的工作 |
|---|---|---|
| HCI / CSCW | CHI、CSCW（PACM HCI）、IUI、CHIWORK、CSCW Journal、TOCHI、IJHCI | 用户实验、定性研究、设计探针 |
| AI 伦理与社会 | FAccT、AIES、AI & Society | 依赖、技能退化、治理 |
| 信息系统与管理 | MIS Quarterly、ISR、Management Science、EJIS、ICIS、HICSS、ECIS | 组织采纳、互补性理论、现场实验 |
| 经济学 | QJE、Science/Nature 系列、NBER/SSRN 工作论文 | 因果意义上的生产力效应 |
| NLP / ML | ACL/EMNLP/NAACL、NeurIPS（D&B track）、ICLR、ICML | 人-agent 协作基准与方法 |
| 软件工程 | ICSE（含 SEIP）、FSE、TSE | 开发者 RCT、代码归属 |

本文不提供影响因子或排名。需要的话，应查 JCR（期刊）和 CORE（会议）的当年数据。

## 6. 研究机会（与 agent 失败报告衔接）
| # | 问题 | 可用的环境/数据 | 指标 | 基线 | 难点 | venue | 新颖性风险 |
|---|---|---|---|---|---|---|---|
| 1 | 在**多步 agent 工作流**中，监督者能否识别"假成功"？哪些界面线索（来源、计划、差异视图）能提升识别率？ | τ-bench 轨迹，加上 Procedure-Aware Evaluation 标注出的腐败成功样本 | 漏检率、AoR、用时 | 只展示最终结果 | 招募有领域知识的被试 | CHI / CSCW | 中低（依赖研究多在单步决策上，推断） |
| 2 | 升级（escalation）时机的校准：agent 什么时候该把任务交还给人？ | HAS-Bench、τ²-bench、ReHAC | 完成率、人工调用次数、严重错误率 | 总是询问 / 从不询问 / ReHAC | 用户模拟的偏差 | ACL / NeurIPS | 中（ReHAC、HAS-Bench 已经部分覆盖） |
| 3 | 互补性在 agent 场景下是否成立？Vaccaro 的元分析结论能否推广到 agent 任务？ | CollabSkill、CentaurEval 类型的任务 | 人+agent 与单方的对比 | 人单独 / agent 单独 | 需要真人实验，成本高 | CHI / Nature HB | 低到中 |
| 4 | 审批疲劳：大量审批请求会不会降低审批质量？ | 自建 TheAgentCompany 审批场景 | 审批准确率随时间的变化 | 固定审批 / 风险分级审批 | 需要纵向设计 | CSCW / FAccT | 低（推断） |
| 5 | 团队里的共享 agent：责任归属和信息可见性 | Slack 类模拟环境（参考 SeeSawBot） | 协调成本、冲突次数、信任 | 私人助手 | 原型开发 | CSCW | 中 |
| 6 | 监督技能退化：长期依赖 agent 后，人对 agent 错误的检测能力会不会下降？ | 纵向实验 | 检测率随周数的变化 | 无 AI 对照组 | 时间周期长，被试流失 | CHI / MISQ | 低 |

## 7. 阅读路线
- **广度优先**（约 2 周）：Vaccaro 元分析 → Brynjolfsson → Jagged Frontier → METR → Cybernetic Teammate → Bansal 2021 → Kim 2025 → Ironies → Co-Gym → HAS-Bench → M365 Copilot usage
- **深入"人如何监督 agent"**：Bansal → Vasconcelos → Schemmer（AoR）→ Kim 2025 → Plan-Then-Execute → ReHAC → HAS-Bench → 上一份报告中的 τ²-bench 和 Procedure-Aware Evaluation

## 8. 局限与待补
- Jagged Frontier 和 Cui et al. 的数字凭背景知识写成（⚠️），需要核对原文。
- SeeSawBot、Inkpen、Yang（Management Science）、Expertise Atrophy 只有 GS 元数据。
- 各基准是否开源，未逐一核实。
- 未覆盖的方向：
  - 人力资源与算法管理（algorithmic management）
  - 管理者视角
  - 法律与合规中的人机分工
  - 非英语国家的企业
