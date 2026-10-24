# QA Log

## 2026-10-23 — agent 该"找谁"有没有人做过？ReHAC 产出是模型还是框架？
- 没有发现完全覆盖的论文（检索有限）。相邻工作：多专家 L2D（DeCCaF、Top-k L2D，只针对单步分类，不含角色）；Whom to Query for What（ICML'26，选问题和受访者，但目的是群体意见估计）；Multi-User LLM Agents / Harness-MU / Collaborative Memory（多委托人、权限建模，但研究的是被动听谁的指令）；AgentAsk（路由对象是 agent）。
- 数据：TheAgentCompany npc_definition.json 有 17 个人类角色，41 个任务带 scenarios.json；EnterpriseBench（MIT，带访问控制层级）。
- ReHAC 的产出：既是方法框架（MDP + 人工成本奖励 + 离线 RL），也是训练好的协作策略模型，外加一个人机协作数据集。
- 参考：who_to_ask_survey.md

## 2026-10-23 — 有哪些开源的企业工作流 agent trace？（已在 GitHub 核实）
- TheAgentCompany/experiments：12 组模型/框架配置，约 1,926 条逐步轨迹（json.gz）加检查点评分和截图；仓库无许可证。
- τ-bench historical_trajectories：gpt-4o 和 sonnet-3.5 在零售、航空域，带 reward（MIT）；τ²-bench data/tau2/results/final 有 55 个文件（MIT）。
- AppWorld：用 `appworld download experiment-outputs` 下载；其他参赛者的轨迹在 leaderboard repo（Apache-2.0）。
- CRMArena：results/ 下 136 个结果文件，经 Git LFS 存储，CC BY-NC 4.0（禁止商用）。
- WorkArena：只提供生成轨迹的脚本，需要 ServiceNow 实例。
- 失败标注：Who&When 127+59 条（agent/step/reason，GAIA 类）；MAST 原始 traces 加 HF mcemri/MAD（含少量 AppWorld）。
- 结论：企业场景的原始轨迹有，但带根因标注的企业轨迹没有找到。

## 2026-10-23 — ReHAC 是怎么做的？（精读）
- 问题：多步任务中每一步由人还是 agent 来做；目标是用最少的人工介入换取最高的成功率。灵感来自自动驾驶的条件自动化。
- 以往不足：靠启发式规则或提示词决定何时求助，场景特定、难以泛化，也没有显式的人工成本。
- 方法：MDP；协作策略（Llama-2-7B + LoRA）决定每一步由谁做；R = 任务得分 − λ·人工次数；离线 REINFORCE（加重要性采样截断和熵正则）；训练数据为 50/50 随机分配的轨迹（14 名研究生约 1.9k 条，GPT-4 模拟人各约 2k 条）。
- 结果（λ=0.08）：HotpotQA 31.38 vs Prompt 29.26 vs 只用 agent 22.39；InterCode 60.08 vs 54.69。真人实验中协作优于只用人或只用 agent；GPT-4 模拟数据训练效果优于真人数据。
- Intuition：训练一个小型"派单员"，从结果中学习哪些步骤值得交给人，而不是让 LLM 凭感觉判断。
- 局限：任务是问答和 SQL 而非企业工作流；人工成本只按次数计；没有风险分级。
- 参考：https://arxiv.org/html/2402.12914v1 ；hai_enterprise_survey.md 领域 4

## 2026-10-23 — HAI 报告 §6 选题 1、2 具体是什么？
- 选题 1（监督者能否识别假成功）：τ-bench 中 27–78% 的"成功"是腐败成功（PAE）。实验用真成功、腐败成功、失败三类轨迹，比较四种审核界面（只看结果 / 加计划 / 加来源 / 加状态 diff），指标为漏检率、误拒率、AoR、用时。依赖研究以往多在单步决策上（推断）。
- 选题 2（升级时机校准）：在 τ²-bench、HAS-Bench 上比较总是问 / 从不问 / 置信度阈值 / 风险分级 / ReHAC 五种策略，指标为完成率、介入次数、严重错误率，输出成本-风险帕累托曲线。风险：ReHAC、HAS-Bench 已部分覆盖。
- 两者关系：前者研究"审得准不准"，后者研究"何时让人审"。
- 参考：hai_enterprise_survey.md §6；agent_failure_survey.md §3b

## 2026-10-23 — 失败归因领域有哪些常用数据集？
- 核心：Who&When（ICML'25，127 个多 agent 系统，标注出错 agent 和出错步骤，开源）；MAST-Data（NeurIPS'25 D&B，1,600+ 条 trace，14 种失败模式，开源）；TracerTraj（AgenTracer，用故障注入生成）；DoVer 实验集（GAIA/AssistantBench 上的 Magentic-One）；Agentic AI 故障集（385 个 GitHub 故障）；WebSuite。
- 上游任务来源：GAIA、AssistantBench、SWE-bench、τ-bench。
- 空白（推断）：缺少基于有状态企业工作流（τ²/AppWorld/TheAgentCompany）的根因标注数据集。
- 参考：agent_failure_survey.md §3b 领域 2；research/abs/abs.json

## 2026-10-23 — "用干预来验证归因"是什么意思？
- 出自 DoVer（ICLR'26）：先由 LLM 提出"第 X 步 agent Y 出错"的假设 → 修改该步（改消息或改计划）→ 从该步重放 → 如果翻转为成功，说明假设成立。本质是反事实检验。
- 动机：只看日志的归因无法验证；而且常常有多处修改都能修好任务，所以"唯一出错步骤"这个问题本身不一定成立。改为看"是否修好"。
- 数字：18–28% 的失败被翻转为成功；30–60% 的假设得到验证或否定。
- 企业场景的限制（推断）：有副作用的操作无法重放，需要沙箱和快照。
