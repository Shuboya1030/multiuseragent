# Whom Should the Agent Ask? Role-Aware Help-Seeking in Multi-User LLM Agent Systems

**Research Proposal** · Shuya Zong · Draft v0.5, October 2026

---

## 1. Overview

**Motivation.** LLM-based agents are increasingly embedded in organizational workflows. In these settings a single agent often serves multiple users who differ in role, expertise, and authority. Current agent systems, however, are designed under a *single-principal interaction paradigm* (Yang et al., 2026): one user is treated as the sole source of authority and information. In practice, the information and approvals an agent needs to complete a task are distributed across an organization. When an agent is blocked by missing information, an ambiguous requirement, or an action that requires approval, it must decide not only **when** to involve a human but also **whom** to involve. A query directed to a colleague who lacks the relevant knowledge wastes effort. An approval obtained from someone without authority is invalid. Escalating a routine question to a senior stakeholder incurs unnecessary interruption cost.

**Aim.** This research aims to establish **role-aware help-seeking** as a research problem in multi-user LLM agent systems. It will develop the empirical, conceptual, and methodological foundations for agents that select the appropriate human collaborator based on that person's knowledge, authority, and interruption cost.

**Significance.** As agents move from individual assistants to shared team infrastructure, principal selection becomes a core determinant of task success, efficiency, and governance. Addressing it informs the design of enterprise agents, the allocation of human oversight, and the evaluation of human–agent systems beyond single-user benchmarks.

## 2. Background and Research Gap

**Human–agent collaboration.** Fully autonomous agents remain unreliable on complex workplace tasks. In a simulated software company, the strongest agent completed about 30% of tasks (Xu et al., 2025). This has motivated *conditional automation*, in which humans intervene only at critical steps. ReHAC (Feng et al., 2024) formulates human intervention as a sequential decision problem and learns a policy that trades off task reward against the number of interventions. Related work studies proactive clarification (Wang et al., 2025) and benchmarks with configurable human participation (Shao et al., 2024; Wu et al., 2026). These approaches model the human as a **single, homogeneous collaborator**.

**Multi-user and multi-principal agents.** Recent work formalizes the *multiple principal–agent scenario*. In it, an agent serves a principal set in which each principal holds a private context and an authority level. This work shows that frontier LLMs struggle with conflicting instructions, privacy preservation, and coordination (Yang et al., 2026). Complementary systems enforce role-based permissions (Fan et al., 2026) and access-controlled memory (Rezazadeh et al., 2025). These studies address a **reactive** question: how should an agent respond to instructions from multiple principals?

**Deferral to multiple experts.** Multi-expert learning-to-defer allocates predictions among experts under cost and workload constraints (Alves et al., 2024; Montreuil et al., 2026). It operates on single-step classification, and it characterizes experts only by accuracy and cost.

**Human–agent teaming.** Human factors research characterizes human–agent teams along structural dimensions. Chung et al. (2024) adapt a human–human team classification to nine dimensions: team composition, task interdependence, role structure, leadership structure, authority differentiation, communication structure, communication direction, communication medium, and team life span. Applying the scheme to 25 testbeds from 68 empirical studies, they find that most research examines teams of one human and one agent with human leadership and static structure. Multi-human teams that share an agent remain understudied.

**Gap.** No existing work addresses the **proactive** counterpart of the multi-principal problem in multi-step, interactive tasks: *when the agent lacks the information or authority to proceed, which principal should it consult?* Three properties distinguish this problem from single-human deferral:
1. **Information asymmetry.** Knowledge is distributed across principals.
2. **Authority asymmetry.** A correct answer from an unauthorized principal is insufficient.
3. **Heterogeneous interruption costs.** Consulting different principals carries different costs.

## 3. Research Questions

- **RQ1 (Characterization).** How prevalent are help-seeking failures among current LLM agents in enterprise tasks, and what forms do they take? Examples include consulting the wrong principal, omitting a needed consultation, and failing to act on a response.
- **RQ2 (Representation).** Does explicit role information about collaborators (knowledge, authority, cost) improve help-seeking, and does its effect depend on whether knowledge and authority reside in the same principal?
- **RQ3 (Adaptation).** Do LLM agents adapt their help-seeking appropriately to interruption costs and authority constraints, relative to an oracle policy?
- **RQ4 (Learning).** Can a learned policy that jointly decides *when* and *whom* to ask outperform prompting-based help-seeking, and does it generalize to unseen organizational structures?
- **RQ5 (Team structure).** Do properties of the human–agent team moderate help-seeking behavior and its effectiveness? The properties considered are task interdependence, team life span, and communication structure. *We hypothesize that sequential interdependence and short-lived teams increase help-seeking errors, and that persistent teams allow agents to learn role profiles from interaction history.*

## 4. Methodology

**Formulation.** We model help-seeking as a Markov decision process.
- At each step, the agent either acts autonomously or sends a query to a principal uᵢ.
- Each principal has a role profile Pᵢ = ⟨knowledge, authority, interruption cost, availability, reliability⟩.
- The objective balances task success T against cumulative interruption cost, authority violations, and uninformative queries:

$$R = T - \lambda \sum_t c_{u_t} - \mu N_{\text{auth}} - \nu N_{\text{waste}}$$

This generalizes the single-human formulation of ReHAC, which is the case N = 1 with uniform cost. Authority is encoded at the level of actions and information items rather than as a single per-person label. For example, a principal may approve a budget but may not access personnel records. The evaluator determines whether each approval is valid.

**Team configuration.** We specify the environment using the nine-dimension team classification scheme of Chung et al. (2024). This makes explicit the class of teams to which our findings apply.

| Dimension | Configuration in this study |
|---|---|
| Team composition | Multiple humans, one agent |
| Task interdependence | Independent information requests, or sequential (consult an informant, then an approver) |
| Role structure | Functionally differentiated (e.g., engineering, product, HR, finance) |
| Leadership structure | No designated coordinator; the agent selects collaborators |
| Authority differentiation | Action-level authority (who may approve which actions) |
| Communication structure | Agent-to-individual, one principal at a time (Studies 1–3) |
| Communication direction | Agent-initiated |
| Communication medium | Text chat |
| Team life span | Single-task (Studies 1–3); persistent team (later work) |

Studies 1–4 hold the team structure fixed at the configuration above. The only structural factor they manipulate is whether knowledge and authority reside in the same principal. Fixing the structure keeps simulation and interpretation tractable, and it scopes the claims of the early papers to this class of teams. Team structure itself is examined in Study 5.

**Environment and data.** The study builds on TheAgentCompany (Xu et al., 2025), a public simulation of a software company.
- It includes LLM-simulated colleagues with defined roles, such as CTO, HR manager, finance director, product managers, and engineers.
- It includes tasks that require information held by specific colleagues.
- It provides publicly released agent trajectories from multiple models.

We will extend these tasks by manipulating the **alignment of knowledge and authority**: whether the information and the approval rights a task requires reside in the same principal or in different principals. We will also add distractor principals: colleagues who are knowledgeable but unauthorized, authorized but uninformed, or adequate but costly to consult. For each task we specify the set of **valid help-seeking paths** (for example, consulting an informant and then an approver), which enables rule-based evaluation. To assess generality, organizational metadata from EnterpriseBench (Vishwakarma et al., 2025) will be used to construct additional organizations.

**Study 1: Characterization (RQ1).**
- Annotate help-seeking events in the public trajectories using a coding scheme: correct, wrong principal, omitted, no follow-up, redundant. The scheme also records who initiated each exchange, the role of the consulted principal, and whether the task required subsequent approval.
- Annotation is LLM-assisted. Following the procedure of Chung et al. (2024), two researchers independently code a subset and resolve disagreements through discussion; we report inter-annotator agreement.
- Analyses relate error types to task outcomes and compare models.

**Study 2: Role-information ablation (RQ2).**
- Evaluate several open and proprietary LLMs in a design that crosses role information (names only / natural-language role descriptions / structured role profiles) with knowledge–authority alignment (aligned / separated).
- Primary outcomes: task success, **path validity** (whether the agent followed a valid help-seeking path), **approval validity**, number of queries, and cumulative interruption cost. First-query accuracy is reported as a secondary measure, because a valid path may consult an informant before an approver.

**Study 3: Cost and authority sensitivity (RQ3).**
- Systematically vary interruption costs and authority penalties.
- Compare agent behavior with an oracle policy derived from the ground-truth task specification.
- Report regret and success–cost trade-off curves.

**Study 4: Learned policy (RQ4).**
- Collect trajectories under randomized help-seeking assignments.
- Train a lightweight open-weight policy model with offline reinforcement learning.
- Baselines: prompting, sequential when-then-whom decisions, adapted multi-expert deferral, and the oracle.
- Generalization is tested on held-out organizational structures.

**Study 5: Team structure as a moderator (RQ5).**
- Vary one structural dimension at a time, building on the environment and metrics of Studies 1–3:
  - task interdependence: independent vs. sequential;
  - team life span: single-task vs. persistent;
  - communication structure: one-to-one vs. broadcast.
- Each variant requires its own scenario specification and valid-path definitions. This is why the study is scoped as separate work.

**Risks and mitigation.**
- *Validity of simulated colleagues.* LLM-simulated colleagues may not reflect human behavior. Their responses will be constrained by task specifications, and a later human-participant study will validate key findings.
- *Assumed costs.* Interruption costs are assumed rather than measured. Sensitivity analyses will test whether conclusions hold across cost settings.
- *Limited trajectory coverage.* If public trajectories cover too few help-seeking events, Study 1 will be supplemented with newly collected trajectories.

**Ethics.** Studies 1–4 use only public resources and simulated users. A future human-participant study would require research ethics board approval.

## 5. Expected Contributions

1. A **formal problem definition** of role-aware help-seeking in multi-user LLM agent systems, which generalizes single-human deferral to heterogeneous principals.
2. A **specification of the help-seeking environment** grounded in an established human–agent team taxonomy, extended with action-level authority and valid help-seeking paths.
3. **Empirical evidence** on the prevalence and forms of help-seeking failures in current agents.
4. An **evaluation environment** with distractor principals and rule-based metrics for principal selection.
5. A **comparative analysis** of how LLMs use role information and respond to cost and authority constraints.
6. A **learned help-seeking policy**, together with an analysis of its generalization across organizational structures.

## 6. Planned Outputs

The research is organized as a sequence of papers. Each paper has a self-contained scope.

| Paper | Research questions | Treatment of team structure | Candidate venues |
|---|---|---|---|
| 1. Characterizing role-aware help-seeking | RQ1–RQ3 (Studies 1–3) | Fixed; knowledge–authority alignment manipulated | Workshop version (AAAI-27 Workshop on Human-AI Collaboration); full version at ACL/EMNLP |
| 2. Learning when and whom to ask | RQ4 (Study 4) | Fixed; role compositions vary | ACL/EMNLP, NeurIPS |
| 3. Team structure and help-seeking | RQ5 (Study 5) | Independent variable | HFES, CSCW |
| 4. Human-participant validation | Key findings of Papers 1–3 | Real teams | CHI, CSCW |

## References

Alves, J. V., Leitão, D., Jesus, S., Sampaio, M. O. P., Liébana, J., Saleiro, P., et al. (2024). *Cost-sensitive learning to defer to multiple experts with workload constraints* (arXiv:2403.06906). arXiv. https://doi.org/10.48550/arXiv.2403.06906

Chung, H., Holder, T., Shah, J., & Yang, X. J. (2024). Developing a team classification scheme for human-agent teaming. *Proceedings of the Human Factors and Ergonomics Society Annual Meeting, 68*(1), 1394–1399. https://doi.org/10.1177/10711813241260387

Fan, W., Nie, X., & Dai, Z. (2026). *Harness-MU: A safe, governed, and effective harness for multi-user LLM agents* (arXiv:2606.21856). arXiv. https://doi.org/10.48550/arXiv.2606.21856

Feng, X., Chen, Z.-Y., Qin, Y., Lin, Y., Chen, X., Liu, Z., & Wen, J.-R. (2024). Large language model-based human-agent collaboration for complex task solving. In *Findings of the Association for Computational Linguistics: EMNLP 2024* (pp. 1336–1357). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.findings-emnlp.72

Montreuil, Y., Carlier, A., Ng, L. X., & Ooi, W. T. (2026). Why ask one when you can ask *k*? Learning-to-defer to the top-*k* experts. In *Proceedings of the International Conference on Learning Representations (ICLR 2026)*. https://doi.org/10.48550/arXiv.2504.12988

Rezazadeh, A., Li, Z., Lou, A., Zhao, Y., Wei, W., & Bao, Y. (2025). *Collaborative memory: Multi-user memory sharing in LLM agents with dynamic access control* (arXiv:2505.18279). arXiv. https://doi.org/10.48550/arXiv.2505.18279

Shao, Y., Samuel, V., Jiang, Y., Yang, J., & Yang, D. (2024). *Collaborative Gym: A framework for enabling and evaluating human-agent collaboration* (arXiv:2412.15701). arXiv. https://doi.org/10.48550/arXiv.2412.15701

Vishwakarma, H., Agarwal, A., Patil, O., Devaguptapu, C., & Chandran, M. (2025). Can LLMs help you at work? A sandbox for evaluating LLM agents in enterprise environments. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*. Association for Computational Linguistics. https://doi.org/10.48550/arXiv.2510.27287

Wang, W., Shi, J., Ling, Z., Chan, Y.-K., Wang, C., Lee, C., et al. (2025). Learning to ask: When LLM agents meet unclear instruction. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*. Association for Computational Linguistics. https://aclanthology.org/2025.emnlp-main.1104/

Wu, Y., Huang, W.-X., Guo, J., Li, D., & Jiang, R. (2026). *HAS-Bench: Evaluating LLM-based human-agent systems under configurable human participation* (arXiv:2607.04329). arXiv. https://doi.org/10.48550/arXiv.2607.04329

Xu, F. F., Song, Y., Li, B., Tang, Y., Jain, K., Bao, M., et al. (2025). TheAgentCompany: Benchmarking LLM agents on consequential real world tasks. In *Advances in Neural Information Processing Systems 38: Datasets and Benchmarks Track*. https://doi.org/10.48550/arXiv.2412.14161

Yang, S., Zhu, S., Zhu, H., Enríquez, J. R., Wang, D., Pentland, A., et al. (2026). *Multi-user large language model agents* (arXiv:2604.08567). arXiv. https://doi.org/10.48550/arXiv.2604.08567
