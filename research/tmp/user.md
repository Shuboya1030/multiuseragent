# Whom and When Should the Agent Ask? Role-aware Help-Seeking in Multi-User LLM Agent Systems

**Research Proposal (short version)** · Shuya Zong · October 2026

## 1. Problem and Motivation

LLM-based agents are increasingly deployed as shared infrastructure in organizational workflows. A single agent often serves multiple users who differ in role, expertise, and authority. Most agent systems, however, are designed under a *single-principal interaction paradigm*, in which one user is the sole source of authority and information (Yang et al., 2026). In practice, the information and approvals an agent needs are distributed across an organization. When an agent is blocked, it must decide not only **when** to involve a human but also **whom** to involve. A query to a colleague who lacks the relevant knowledge wastes effort. An approval from someone without authority is invalid. Escalating a routine question to a senior stakeholder incurs unnecessary interruption cost.

This project aims to establish **role-aware help-seeking** as a research problem: how an agent should select a human collaborator based on that person's knowledge, authority, and interruption cost.

## 2. Background and Research Gap

**Human--agent collaboration.** Autonomous agents remain unreliable on workplace tasks. In a simulated software company, the strongest agent completed about 30% of tasks (Xu et al., 2025). ReHAC (Feng et al., 2024) formulates human intervention as a sequential decision problem and learns *when* an agent should hand a step to a human. Related work studies proactive clarification (Wang et al., 2025). These approaches model the human as a single, interchangeable collaborator.

**Multi-principal agents.** Recent work formalizes the *multiple principal--agent scenario*, in which each principal holds a private context and an authority level. It shows that frontier LLMs struggle with conflicting instructions, privacy, and coordination (Yang et al., 2026). Runtime systems enforce role-based permissions (Fan et al., 2026). These studies address a **reactive** question: how should an agent respond to multiple principals?

**Related directions.** Multi-expert learning-to-defer routes single-step predictions to experts characterized only by accuracy and cost (Alves et al., 2024; Montreuil et al., 2026). In human factors research, a review of 68 human--agent teaming studies found that most examine one-human--one-agent teams (Chung et al., 2024). Multi-human teams that share an agent remain understudied.

**Gap.** No prior work addresses the **proactive** counterpart in multi-step tasks: *when the agent lacks the information or authority to proceed, which principal should it consult?* Three properties distinguish this problem from single-human deferral: - information asymmetry (knowledge is distributed across principals); - authority asymmetry (a correct answer from an unauthorized principal is insufficient); - heterogeneous interruption costs.

## 3. Research Questions

- **RQ1.** How prevalent are help-seeking failures among current LLM agents in enterprise tasks, and what forms do they take? Examples include asking the wrong principal, omitting a needed consultation, and failing to follow up.
- **RQ2.** Does explicit role information (knowledge, authority, cost) improve help-seeking? Does its effect depend on whether knowledge and authority reside in the same principal?
- **RQ3.** Do LLM agents adapt whom they ask to interruption costs and authority constraints, relative to an oracle policy?

## 4. Approach

**Formulation.** We model help-seeking as a Markov decision process. - At each step, the agent either acts autonomously or queries a principal uᵢ. - Each principal has a role profile ⟨knowledge, authority, interruption cost⟩. - The objective is

$$R = T - \lambda\sum_{t}^{}c_{u_{t}} - \mu N_{\text{auth}} - \nu N_{\text{waste}}$$

- T: task success
- the λ term: interruption cost
- N_auth: authority violations
- N_waste: uninformative queries

This generalizes ReHAC's single-human formulation. Authority is encoded per action (for example, who may approve a budget), not as a single label per person.

**Environment.** We build on TheAgentCompany (Xu et al., 2025), a public simulation of a software company. It includes role-defined LLM colleagues (e.g., CTO, HR manager, finance director, engineers), tasks that require information held by specific colleagues, and publicly released agent trajectories. - We extend these tasks by manipulating whether the required knowledge and approval rights reside in the **same or different** colleagues. - We add distractor colleagues: knowledgeable but unauthorized, authorized but uninformed, or adequate but costly to interrupt. - Each task specifies its **valid help-seeking paths** (for example, ask an informant, then an approver), which enables rule-based evaluation. - The team structure (multiple humans and one agent, agent-initiated text communication, single-task teams) is held fixed. This structure is described using the scheme of Chung et al. (2024).

**Study 1 (RQ1).** Code each help-seeking event in the public trajectories as *correct*, *wrong principal*, *omitted*, *no follow-up*, or *redundant*. Coding is LLM-assisted, with dual human coding of a subset, and we report inter-annotator agreement. We then relate error types to task outcomes across models.

**Study 2 (RQ2).** Evaluate several open and proprietary LLMs in a 3 × 2 design: - role information: names only / natural-language descriptions / structured profiles; - knowledge--authority alignment: aligned / separated.

Outcomes are task success, path validity, approval validity, number of queries, and interruption cost.

**Study 3 (RQ3).** Vary interruption costs and authority penalties. Compare agent behavior with an oracle policy, and report regret and success--cost trade-off curves.

**Risks.** LLM-simulated colleagues may not reflect human behavior, and interruption costs are stipulated rather than measured. We mitigate the first by constraining colleague responses to the task specification. We mitigate the second with sensitivity analyses over cost settings. All studies use public resources only.

## 5. Expected Contributions

1.  A formal definition of role-aware help-seeking in multi-user LLM agent systems.
2.  Empirical evidence on how often, and in what ways, current agents fail at help-seeking.
3.  An evaluation environment with distractor principals and rule-based metrics for principal selection.
4.  A comparative analysis of how LLMs use role information and respond to cost and authority constraints.

**Longer-term agenda.** Follow-up work will develop the remaining directions: - a learned policy that jointly decides when and whom to ask, extending ReHAC to multiple principals; - the effect of team structure (task interdependence, team life span, communication structure) on help-seeking; - validation with human participants.

## References

Alves, J. V., Leitão, D., Jesus, S., Sampaio, M. O. P., Liébana, J., Saleiro, P., et al. (2024). *Cost-sensitive learning to defer to multiple experts with workload constraints* (arXiv:2403.06906). arXiv. https://doi.org/10.48550/arXiv.2403.06906

Chung, H., Holder, T., Shah, J., & Yang, X. J. (2024). Developing a team classification scheme for human-agent teaming. *Proceedings of the Human Factors and Ergonomics Society Annual Meeting, 68*(1), 1394--1399. https://doi.org/10.1177/10711813241260387

Fan, W., Nie, X., & Dai, Z. (2026). *Harness-MU: A safe, governed, and effective harness for multi-user LLM agents* (arXiv:2606.21856). arXiv. https://doi.org/10.48550/arXiv.2606.21856

Feng, X., Chen, Z.-Y., Qin, Y., Lin, Y., Chen, X., Liu, Z., & Wen, J.-R. (2024). Large language model-based human-agent collaboration for complex task solving. In *Findings of the Association for Computational Linguistics: EMNLP 2024* (pp. 1336--1357). Association for Computational Linguistics. https://doi.org/10.18653/v1/2024.findings-emnlp.72

Montreuil, Y., Carlier, A., Ng, L. X., & Ooi, W. T. (2026). Why ask one when you can ask *k*? Learning-to-defer to the top-*k* experts. In *Proceedings of the International Conference on Learning Representations (ICLR 2026)*. https://doi.org/10.48550/arXiv.2504.12988

Wang, W., Shi, J., Ling, Z., Chan, Y.-K., Wang, C., Lee, C., et al. (2025). Learning to ask: When LLM agents meet unclear instruction. In *Proceedings of the 2025 Conference on Empirical Methods in Natural Language Processing*. Association for Computational Linguistics. https://aclanthology.org/2025.emnlp-main.1104/

Xu, F. F., Song, Y., Li, B., Tang, Y., Jain, K., Bao, M., et al. (2025). TheAgentCompany: Benchmarking LLM agents on consequential real world tasks. In *Advances in Neural Information Processing Systems 38: Datasets and Benchmarks Track*. https://doi.org/10.48550/arXiv.2412.14161

Yang, S., Zhu, S., Zhu, H., Enríquez, J. R., Wang, D., Pentland, A., et al. (2026). *Multi-user large language model agents* (arXiv:2604.08567). arXiv. https://doi.org/10.48550/arXiv.2604.08567
