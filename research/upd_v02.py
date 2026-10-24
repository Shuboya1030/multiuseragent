p = r'C:\Users\shuyazong\repos\partimephd\agent_failure_survey.md'
s = open(p, encoding='utf-8').read()
R = [
("TheAgentCompany](https://arxiv.org/abs/2412.14161) | 模拟软件公司，覆盖 SWE、HR、财务、PM，含模拟同事 | 预印本 ✅（venue 未核实）",
 "TheAgentCompany](https://proceedings.neurips.cc/paper_files/paper/2025/hash/0d744742f6fac4d1134c019b7cef3c8a-Abstract-Datasets_and_Benchmarks_Track.html) | 模拟软件公司，覆盖 SWE、HR、财务、PM，含模拟同事 | NeurIPS 2025 D&B ✅"),
("τ²：ICML 2026 ✅；τ：⚠️",
 "τ：[ICLR 2025](https://proceedings.iclr.cc/paper_files/paper/2025/hash/1b126cc38b8638e07bef37e7b2bb72bf-Abstract-Conference.html) ✅；τ²：ICML 2026 ✅"),
("| WorkArena / WorkArena++ | ServiceNow 知识工作 | ICML 2024 / NeurIPS 2024 D&B ⚠️",
 "| WorkArena / [WorkArena++](https://proceedings.neurips.cc/paper_files/paper/2024/hash/0b82662b6c32e887bb252a74d8cb2d5e-Abstract-Datasets_and_Benchmarks_Track.html) | ServiceNow 知识工作 | WorkArena：ICML 2024 🔶（GS 只指向 arXiv）；WorkArena++：NeurIPS 2024 D&B ✅"),
("| CRMArena / CRMArena-Pro | Salesforce CRM | NAACL 2025 / 预印本 ⚠️",
 "| [CRMArena](https://aclanthology.org/2025.naacl-long.194/) / CRMArena-Pro | Salesforce CRM | NAACL 2025 ✅ / 预印本 |"[:-2]),
("| OSWorld、WebArena、SWE-bench (Verified) | 桌面、网页、软件工程 | NeurIPS 2024 D&B / ICLR 2024 / ICLR 2024 ⚠️",
 "| [OSWorld](https://proceedings.neurips.cc/paper_files/paper/2024/hash/5d413e48f84dc61244b6be550f1cd8f5-Abstract-Datasets_and_Benchmarks_Track.html)、WebArena、SWE-bench | 桌面、网页、软件工程 | OSWorld：NeurIPS 2024 D&B ✅；另两项 ICLR 2024 🔶"),
("3. TheAgentCompany – Xu et al., arXiv 2412.14161 ✅", "3. TheAgentCompany – Xu et al., NeurIPS 2025 D&B ✅"),
("5. τ-bench – Yao et al., 2024 ⚠️", "5. τ-bench – Yao et al., ICLR 2025 ✅"),
("11. OSWorld – Xie et al., NeurIPS 2024 ⚠️", "11. OSWorld – Xie et al., NeurIPS 2024 D&B ✅"),
("13. ToolEmu – Ruan et al., ICLR 2024 ⚠️", "13. ToolEmu – Ruan et al., [ICLR 2024](https://proceedings.iclr.cc/paper_files/paper/2024/hash/7274ed909a312d4d869cc328ad1c5f04-Abstract-Conference.html) ✅"),
("14. InjecAgent – Zhan et al., Findings ACL 2024 ⚠️", "14. InjecAgent – Zhan et al., [Findings ACL 2024](https://aclanthology.org/2024.findings-acl.624/) ✅"),
("15. AgentPoison – Chen et al., NeurIPS 2024 ⚠️", "15. AgentPoison – Chen et al., [NeurIPS 2024](https://proceedings.neurips.cc/paper_files/paper/2024/hash/eb113910e9c3f6242541c1652e30dfd6-Abstract-Conference.html) ✅"),
("- 状态说明：✅=本次检索已核对官方页面；⚠️=依据背景知识，**未核实**（需在正式版本前逐条核对）。",
 "- 状态说明：✅=已核对官方页面，或 Google Scholar 结果直接链接到官方 proceedings/Anthology 页面；🔶=只有 GS 元数据，官方页尚未打开核对；⚠️=依据背景知识，**未核实**。"),
("| 数量 | 初筛约 60 篇（来自背景知识和检索）；本轮官方核对 9 篇；其余标 ⚠️ |",
 "| 数量 | v0.2：Google Scholar 25 个检索式（限 2023 年及以后），每个取前 10 条，去重后 237 条 → 按标题和摘要人工初筛，保留约 60 篇（见 §4b）。原始结果在 research/gs/q*.json |"),
("# 企业式工作流中 AI Agent 的失败、诊断与缓解：文献调研（v0.1）", "# 企业式工作流中 AI Agent 的失败、诊断与缓解：文献调研（v0.2）"),
("| 检测器可能被自适应攻击绕过；CaMeL 有效用损失 |",
 "| **结论不一致**：[Zhan et al. 2025](https://aclanthology.org/2025.findings-naacl.395/) 用自适应攻击攻破了多种检测器类防御；AgentDojo 的约 8% 是在非自适应攻击下得到的。CaMeL 有效用损失 |"),
("- 核实所有 ⚠️ 条目的 venue、作者和开源链接。\n- 扩充候选清单到 50 篇以上。",
 "- 🔶 条目需要打开官方页面复核；各篇是否开源代码或数据，尚未逐篇核实。"),
("- 待补检索的方向：记忆投毒、WorkArena++、CRMArena-Pro、ToolEmu、OSWorld 及其后续、SWE agent 失败分析、记忆与上下文管理类论文。",
 "- 待补检索的方向：上下文管理与长期记忆更新（非安全视角）；跨系统事务与回滚；企业真实部署的实证研究。"),
]
for a, b in R:
    assert a in s, a[:50]
    s = s.replace(a, b)

cand = '''
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
'''
s = s.replace("\n## 5. 失败模式", cand + "\n## 5. 失败模式")
open(p, 'w', encoding='utf-8').write(s)
print('ok')
