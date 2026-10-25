# Multi-user agent collaboration and help-seeking: literature + industry synthesis (v1)

**Prepared:** 2026-10-24  
**Purpose:** Build a literature- and practice-informed codebook that can be applied to the Study 1 trajectory audit.  
**Scope note:** This is a focused scoping synthesis, not a systematic review or an exhaustive census. Sources were selected for direct relevance to (a) human-agent team structure, (b) agents interacting with several human principals/coworkers, (c) help-seeking, clarification, escalation, approval, or delegation, and (d) production patterns described by major AI platform companies.

## Executive synthesis

The literature located in this focused search does not provide one accepted, exclusive taxonomy of “multi-user agent help-seeking.” Instead, it offers complementary pieces at different analytical levels:

1. **Team structure:** who is in the team, how tasks depend on each other, who leads, how authority is distributed, and who communicates with whom.
2. **Collaboration protocol:** how work is divided, delegated, coordinated, reviewed, approved, escalated, and returned.
3. **Help-seeking event:** what the agent needs, what triggered the request, whom it asks, what it asks for, what response it gets, and whether it uses the response.

The closest existing structural foundation is Chung et al.’s human-agent team classification scheme: nine dimensions covering composition, task interdependence, role structure, leadership, authority differentiation, communication structure, communication direction, communication medium, and team lifespan. This is useful for describing the **team around an interaction**, but it does not classify the fine-grained purpose and trigger of every help-seeking event.

At the episode level, ReHAC directly studies **when** an agent should request human intervention, while PeopleJoin studies **whom** an agent should contact to gather information from synthetic coworkers. Multi-User LLM Agents/Muses-Bench studies a different but adjacent problem: one agent serves several users with conflicting authority, privacy, and coordination requirements. These works do not yet jointly cover multi-step work where an agent autonomously detects a need, chooses among organizationally distinct people, and manages the response through task completion.

Industry materials add concrete operational patterns—specialist-agent delegation, human approval gates, skilled-human handoff, asynchronous coworker messages, status updates, and explicit escalation paths. These sources describe product affordances or company experience; they are not independent empirical evidence that a pattern improves team performance.

**Synthesis for this project:** retain Chung et al.’s team-level dimensions as context, and add a multi-label **help/coordination episode codebook** grounded in ReHAC, PeopleJoin, multi-user-agent work, and industry patterns. Then code the trajectories at event and episode level. This makes the taxonomy deductive-inductive: literature/practice supplies candidate categories; trace evidence tests which categories appear, how they manifest, and where current labels need refinement.

## How sources were selected

Searches covered scholarly indexes/venues (ACL Anthology, AAMAS proceedings, SAGE, Microsoft Research publications, arXiv) and official company research/product sources (Microsoft Research/Learn, Google DeepMind/Cloud/Developers, Anthropic, OpenAI developer documentation, Salesforce). Search concepts included *human-agent teams*, *multi-user LLM agents*, *help-seeking*, *human intervention*, *who to query*, *delegation*, *handoff*, *approval*, *coordination*, and *escalation*.

Included sources either present a team classification/framework, evaluate agents interacting with multiple humans/coworkers, study agent help-seeking/human intervention, or document a concrete enterprise collaboration pattern. General agent orchestration claims without a human/team interaction component are used only as context. The search is a targeted first pass; publication, version, and product availability should be rechecked before manuscript submission.

## Literature findings

### 0. “Multi-user agent” names several different settings

The term is overloaded, so classify the **interaction configuration** before classifying the behavior:

| Configuration | Who interacts with the agent? | Example / relevance |
|---|---|---|
| **Shared agent, multiple principals** | Several humans give instructions to one shared agent, possibly with conflicting goals or authority. | Muses-Bench / Multi-User LLM Agents [R06]. Relevant for priority, privacy, and coordination. |
| **One requester, multiple human knowledge sources** | One human assigns work; the agent contacts coworkers to collect information or get expertise. | PeopleJoin [R04]; closest to our “whom to ask” setting. |
| **Human-agent team** | One or more humans and one or more agents jointly perform interdependent work. | Chung et al.’s HAT scheme [R01] and Yurrita et al.’s design guidelines [R02]. Relevant for team structure and control. |
| **Multi-agent digital organization** | Several role-based agents coordinate with one another, sometimes through channels also used by humans. | CORPGEN [R20]; relevant for delegation and asynchronous coordination, but it is not direct evidence about human help-seeking. |

These configurations can overlap in a real company, but they should not be pooled as if they were the same unit. The primary Study 1 target is **one task-owning agent that can approach multiple human coworkers with different knowledge, authority, availability, or cost**. Shared-principal conflict and agent-agent delegation are contextual dimensions or adjacent modes.

The role-profile dimensions used in our proposal have specific anchors in prior work; they are not intended as an unsupported new theory of people:

| Role-profile dimension | How it affects a help decision | Source anchors |
|---|---|---|
| Knowledge / expertise | Who possesses the needed information or judgment. | Distributed coworker information and expertise-based advice source selection: [R04], [R08]. |
| Authority / permission | Who can authorize, commit, or legitimately decide. | HAT authority differentiation and multi-principal hierarchy: [R01], [R06]; approval practice: [R14], [R15]. |
| Availability / interruption cost | Whether a person can respond and whether asking is worth their time. | Accessibility and helper burden in organizational help-seeking research: [R07], [R08]; intervention-cost framing: [R21]. |
| Trust / answer reliability | Whether the agent should rely on an answer, especially when the issue is consequential or contested. | Trustworthiness in source selection and trust in delegation: [R08], [R10]. |

These anchors motivate candidate role-profile fields. Values in a dataset still require task-specific evidence; they should not be inferred from a person’s title or seniority alone.

### 1. Human-agent team structure: a strong macro-level foundation

Chung et al. analyze 25 testbeds from 68 empirical human-agent teaming studies and propose nine team-level dimensions: **team composition, task interdependence, role structure, leadership structure, authority differentiation, communication structure, communication direction, communication medium, and team lifespan**. Their review finds much prior work concentrated on one-human/one-agent teams, human leadership, and static interaction. This gives our project a recognized vocabulary for describing the wider team configuration. It is not a message-purpose taxonomy: “agent asks a coworker for a missing fact” and “agent asks a manager for authorization” can occur in the same team structure but are different interaction episodes. [Chung et al. (2024)](https://journals.sagepub.com/doi/10.1177/10711813241260387)

The 2026 multi-stakeholder guidelines by Yurrita et al. are based on an expert workshop and a review of 93 empirical papers. They organize design recommendations across teamwork stages and explicitly include agent behaviors such as clarifying goals, requesting authorization, and double-checking decisions. This supports a process view and several episode labels below, but the paper is a set of design guidelines rather than an empirical taxonomy of naturally occurring help-seeking events. [Yurrita et al. (AAMAS 2026)](https://doi.org/10.65109/JOWO4591)

Wang and Lu’s Interaction–Process–Infrastructure framework argues that collaborative work needs an inspectable process representation, with structural adaptation as goals evolve. It helps explain why an interaction should be located in a workflow (e.g., a clarification before action, an approval gate before commitment), rather than coded from message wording alone. [Wang & Lu (Microsoft Research, 2025)](https://www.microsoft.com/en-us/research/publication/interaction-process-infrastructure-a-unified-framework-for-human-agent-collaboration/)

### 2. Agent-initiated help and human intervention: the “when/why” axis

ReHAC formulates intervention timing as a policy decision within a multi-step task. Its core distinction is between letting the agent continue and requesting human help at an opportune stage; experiments include real and simulated human responses. It is the closest precedent for asking whether help is timely and useful, but its central decision is **when to defer to a human**, not which organizationally distinct coworker should be asked. [Feng et al. (Findings of EMNLP 2024)](https://aclanthology.org/2024.findings-emnlp.72/)

Related work on proactive help-seeking treats the request decision as a tradeoff: request assistance when likely benefit exceeds interruption/resource cost, and distinguish proactive help before failure from reactive help after failure. This supports coding trigger and timing separately from the content of the question. [Gao et al. (2026), “Knowing When to Ask”](https://arxiv.org/abs/2606.11349); [Shaikh (2026), “Bayesian Self-Escalation”](https://arxiv.org/abs/2608.24087). These are recent preprints and should be cited with that status in mind.

### 3. Choosing whom to contact: the “recipient” axis

PeopleJoin is the closest benchmark precedent for **whom to ask**: the agent receives a request from one user, identifies coworkers who may have relevant information, talks with those people, then synthesizes a response for the initiating user. Its information is distributed across synthetic organizations with 2–20 users. It foregrounds discovery, information gathering, and synthesis, rather than organizational approval authority or the risks/costs of interrupting particular coworkers. [Jhamtani, Andreas, & Van Durme (Findings of ACL 2025)](https://aclanthology.org/2025.findings-acl.916/)

The broader workplace literature already studies help-seeking as an organizational and relational process. Pagnozzi and Antonelli’s systematic review of 93 peer-reviewed organizational studies identifies individual, organizational-network, and work-environment themes; it notes that help-seeking is embedded in advice networks and expertise, while technical systems receive relatively little attention. Hofmann et al. find that employees’ choices of whom to ask depend on perceived expertise, accessibility, and trustworthiness. Sherf et al.’s meta-analysis distinguishes help-seeking from advice-, information-, and feedback-seeking. These are important foundations for our role and episode codes. The opportunity is to adapt and connect them to agent-mediated multi-user work, not to claim that these help-seeking categories are new. [Pagnozzi & Antonelli (2025)](https://link.springer.com/article/10.1007/s11301-025-00570-0); [Hofmann et al. (2009)](https://doi.org/10.1037/a0016557); [Sherf et al. (2024)](https://doi.org/10.1111/peps.12579)

### 4. Shared agent, multiple principals: authority, privacy, and coordination

Multi-User LLM Agents (Muses-Bench) formalizes a single agent serving multiple users as a multi-principal problem. Its benchmark stresses (a) instruction conflicts under authority hierarchy, (b) cross-user access control/privacy, and (c) multi-user meeting coordination. It establishes that “multiple users” changes the authority and information-governance problem. Its central direction is usually **which user’s instruction to follow and what information may be shared**; it is not primarily about the agent proactively choosing a coworker to resolve its own uncertainty during a work task. [Yang et al. (2026)](https://arxiv.org/abs/2604.08567)

The 2026 AAMAS guidelines and Microsoft’s collaboration framework complement this by emphasizing role clarity, shared awareness, workflow structure, and adaptive coordination. Anthropic’s multi-agent field report illustrates a failure mode relevant to escalation: agents with incompatible goals can interpret each other as adversaries and escalate conflict; the authors identify human deferral or conflict-resolution judgment as an open capability. These sources suggest adding conflict resolution and privacy boundaries as **context/risk codes**, not treating them as ordinary information-seeking. [Anthropic, “Patterns and problems in multiagent systems”](https://www.anthropic.com/research/multiagent-systems)

## Industry and platform patterns

These materials are useful for identifying what deployed systems support and how companies frame operational needs. They should be labeled **practice evidence**, not treated as peer-reviewed validation.

| Company/source | Documented pattern | What it contributes to our taxonomy | Evidence limit |
|---|---|---|---|
| **Microsoft Research — CORPGEN** | Persistent role-specific digital employees exchange asynchronous email/Teams messages; no shared internal state; sub-agents handle specialized work in isolated contexts; messages and shared documents support coordination. | Async request/response, coworker-to-coworker information exchange, specialist delegation, role-specific expertise, shared artifact handoff. | Company research environment; agent-agent/corporate simulation, not a human help-seeking comparison. [Source](https://www.microsoft.com/en-us/research/blog/corpgen-advances-ai-agents-for-real-work/) |
| **Microsoft Copilot Studio** | Parent agents delegate to connected specialist agents; maker defines handoff criteria and context transfer; permissions, audit logs, and approval are governance concerns. Human-in-the-loop can pause workflows for approval or interactive input. | Skill-based routing, context-bearing handoff, authorization/approval, human review, controlled resume. | Product documentation describes capabilities and recommendations, not outcome evidence. [Connected agents](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/authoring-add-other-agents), [multi-agent patterns](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/multi-agent-patterns), [HITL workflows](https://learn.microsoft.com/en-us/agent-framework/workflows/human-in-the-loop) |
| **Google DeepMind / Google Cloud** | Delegation is framed as task allocation plus authority/responsibility/accountability transfer, clear role boundaries, trust, and adaptive negotiation. The agent may challenge an ambiguous request or ask a human to verify; avoid unnecessary human burden. | Clarification of intent, recipient/agent capability matching, authority transfer, verification, boundary-aware escalation, interruption cost. | The delegation framework is a research preprint; Cloud blog is company interpretation/practice guidance. [Research paper](https://arxiv.org/abs/2602.11865), [Google Cloud discussion](https://cloud.google.com/blog/products/ai-machine-learning/how-agents-can-delegate-better/) |
| **Google A2A** | Agents discover capabilities, delegate tasks, exchange context/artifacts, and send status updates during long-running work; protocol anticipates human-in-the-loop situations. | Capability discovery, task delegation, progress/status messages, artifact handoff, asynchronous coordination. | Interoperability protocol describes communication primitives, not the quality of whom-to-ask decisions. [A2A announcement](https://developers.googleblog.com/a2a-a-new-era-of-agent-interoperability/) |
| **OpenAI Agents SDK** | Tool use can pause for human approval; approvals can apply to tools invoked by the current agent or through agent handoffs/nested agents. | Permission check and approval gate at action boundary. | Developer documentation, not an empirical teamwork study. [Source](https://openai.github.io/openai-agents-python/human_in_the_loop/) |
| **Salesforce Agentforce** | Customer-support conversations can transfer to a skilled human queue with conversation context; product guidance includes user-requested and rule-triggered escalation. | Human takeover, queue-based expertise routing, context-preserving handoff. | Customer-service escalation is adjacent to internal coworker help-seeking; do not generalize its recipient logic without evidence. [Source](https://www.salesforce.com/blog/agent-handoff/) |

## Candidate collaboration and help-seeking modes

These are **overlapping episode labels**, not mutually exclusive team types. One episode can be both “request expertise” and “clarify a decision,” for example. Record the evidence and permit multiple labels.

| Candidate episode mode | Operational meaning | Typical trigger | Direct references | Evidence status |
|---|---|---|---|
| **Fact / knowledge acquisition** | Ask a user or coworker for a missing fact, preference, document, or domain-specific information. | Missing information or distributed knowledge. | [R04], [R05], [R06], [R07] | Established information/help-seeking construct; multi-user-agent benchmark precedent. |
| **Clarification / intent negotiation** | Ask the requester to resolve ambiguity, conflicting requirements, or an underspecified goal. | Ambiguous instruction, multiple plausible interpretations. | [R02], [R03], [R10], [R11] | Human-agent design guidance + company delegation practice; candidate operational episode label. |
| **Advice / expert consultation** | Seek a recommendation, judgment, or interpretation from a knowledgeable teammate. | Capability gap, unfamiliar or high-complexity decision. | [R07], [R08], [R09], [R23] | Grounded in organizational help/advice-seeking research; closely related to, but distinct from, information-seeking. |
| **Verification / second opinion** | Ask a person to check a claim, result, or planned action before proceeding. | Low confidence, high consequence, or conflicting evidence. | [R02], [R10], [R11], [R14] | Named in human-agent design guidance and instantiated in company approval/verification workflows; not a settled standalone taxonomy. |
| **Authorization / approval** | Request permission from an authority holder to commit, access, or perform an action. | Policy boundary, role/authority requirement, sensitive action. | [R01], [R02], [R13], [R14], [R15], [R16] | Authority is an established team dimension; explicit agent approval gates are documented practice. |
| **Access / blocker removal** | Ask someone to grant access, provide a resource, or perform an action needed to proceed. | Execution blocker or missing capability/permission. | [R05], [R15], [R18] | Supported by benchmark task patterns and product handoff/approval examples; retain as candidate subtype until trajectories validate it. |
| **Status / availability coordination** | Ask when a dependency will be ready, whether someone is available, or coordinate sequencing. | External dependency, schedule constraint, concurrent work. | [R04], [R07], [R08], [R19], [R20] | Status coordination appears in multi-user information gathering, organizational help-seeking research, and company protocols; availability/accessibility is grounded in workplace research. |
| **Multi-person information coordination** | Contact more than one person, reconcile responses, synthesize distributed knowledge, or relay a result among users. | Information distributed across roles; conflicting inputs. | [R04], [R06], [R17], [R19], [R20] | Direct human-coworker benchmark precedent plus multi-user coordination and analogous specialist-agent routing examples. |
| **Escalation / responsibility handoff** | Transfer control or a customer/task episode to a human or more capable specialist, with context. | Agent limit, failure, risk, unresolved conflict, user request. | [R02], [R10], [R18], [R21], [R22] | ReHAC is peer-reviewed; handoff specifics are documented product practice, primarily in customer support. |
| **Conflict / authority arbitration** | Surface incompatible user goals, authority claims, or instructions and seek resolution rather than silently choosing. | Multi-principal conflict or unclear authority. | [R06], [R10], [R12] | Multi-user benchmark precedent and company field report; candidate event code, distinct from ordinary help requests. |
| **Notification / progress reporting** | Tell a user or teammate what has been done, what is blocked, or what happens next; not necessarily a help request. | Milestone, handoff, long-running task, dependency update. | [R03], [R19], [R20] | Process/protocol patterns; interactional category is retained mainly to distinguish communication from seeking help. |
| **Feedback / evaluation request** | Ask a user or coworker for preferences, ratings, review, or feedback needed to complete a task. | User-mandated collection or iterative quality review. | [R05], [R09], [R23] | Feedback-seeking is a distinct established work-seeking construct; TAC also contains task-mandated examples. |

Reference keys resolve to the complete bibliography in “Reference register and source type” below. Every candidate mode now has at least one traceable source. “Direct reference” means the source addresses the construct or a close operational instance; it does **not** mean that the source validates our exact label boundaries.

“Privacy/access control” is not a help-seeking mode by itself. It is a **constraint on all modes**: what may be asked, passed to another person/agent, or included in a handoff. Likewise, “agent-led,” “human-led,” and “co-led” describe authority/leadership structure; they should not replace episode labels.

## Integrated coding framework for Study 1

Code each trajectory at three linked levels:

### A. Team/context profile (macro)

Adapt the nine Chung et al. dimensions. For our data, at minimum record: composition (one shared agent + number/type of human coworkers), role differentiation, leadership/authority, task interdependence, communication topology/direction, medium, and task duration. Add whether users are principals issuing instructions, coworkers holding task information, approvers, or generic simulated responders.

### B. Help/coordination episode (meso)

Record:

1. **Initiator and direction:** agent → requester; agent → coworker/authority; human → agent; agent → agent; group broadcast.
2. **Episode mode:** one or more candidate modes from the table above.
3. **Task relation:** required by task; trigger-conditional; agent-discretionary; user-initiated; absent/unclear.
4. **Trigger:** missing knowledge; ambiguity; expertise gap; uncertainty/verification; authority; access/blocker; dependency/status; conflict; routine milestone; no evidenced trigger.
5. **Timing:** before attempting; after an attempt; after failure/blocker; at a planned checkpoint; after receiving conflicting responses; not observable.
6. **Recipient choice:** named in instructions; selected by role/expertise; discovered through directory/tool; authority-based; broadcast; recipient not recoverable. Separately code whether the choice is justified by task evidence.
7. **Interaction quality and outcome:** specificity, response latency/availability where measurable, response completeness/correctness, follow-up, uptake, and task consequence. Keep response and uptake separate.

### C. Team architecture / control (workflow-level)

Record who owns task decomposition, recipient selection, final decision, and execution authority: fixed human-led chain; agent-coordinated specialist network; shared/negotiated control; agent-led with human checkpoints; or unclear. These are descriptive patterns inferred from repeated process evidence, not mutually exclusive identities to assign from one message.

## Mapping the current TAC trace labels into the integrated framework

The current lexical labels map into the episode-mode candidates as follows, pending contextual adjudication:

| Existing TAC screening label | Candidate integrated mode(s) | Additional evidence needed |
|---|---|---|
| `information_or_input_request` | Fact/knowledge acquisition; feedback/evaluation; access/blocker removal; clarification | Read prompt and task state to identify what information was missing and whether it was a request, survey, or clarification. |
| `advice_or_expertise_request` | Advice/expert consultation; decision support | Verify that the recipient was asked for judgment and had relevant expertise. |
| `approval_or_action_request` | Authorization/approval; access/blocker removal; action delegation | Establish authority/permission condition and whether request asks for approval versus execution. |
| `coordination_or_availability` | Status/availability coordination | Link to a real task dependency; distinguish scheduling from availability for interview/survey tasks. |
| `status_request` | Status/availability coordination; task monitoring | Identify dependency and whether the agent is checking another person’s progress or a project state. |
| `feedback_or_evaluation_request` | Feedback/evaluation; task-directed data collection | Keep separate from uncertainty-driven help unless the feedback is needed to resolve a task decision. |
| `information_or_task_result_delivery` | Notification/progress reporting; result handoff | Determine whether the recipient must act/review or is simply informed. |
| `acknowledgment_or_action_commitment` | Coordination/closure; response uptake evidence | Link to prior message and verify whether the promised action occurred. |
| `answer_or_data_response`, `short_reply_or_unclassifiable`, `name_only_or_unclassifiable_contact`, `other_message` | Response/uptake or unresolved | Inspect preceding turn and subsequent action; lexical text alone is insufficient. |

The present extraction can support message-function distributions. It does not yet support claims about true trigger, best recipient, team authority, reply usefulness, or uptake without episode-level annotation. Because 32/40 TAC task prompts explicitly require contact and six specify conditional contact, the initial descriptive claim should concern **observed interaction modes in prescribed/conditional work**, not a prevalence estimate of spontaneous help-seeking.

## What this synthesis changes in our research framing

1. **Do not pitch the novelty as a general human-agent team classification scheme.** Chung et al. already provide a broad structural classification, and newer guidelines organize team design across stages and stakeholders.
2. **Position our unit of contribution at the interaction-process level.** The proposed gap is a task-grounded taxonomy/coding framework for *agent-initiated help and coordination across multiple organizationally differentiated people*, connected to team structure and authority.
3. **Separate “who is in the team” from “what the agent asks for.”** A flat/centralized/distributed leadership label cannot tell us whether an interaction was knowledge seeking, clarification, approval, escalation, or routine collection.
4. **Add mode × trigger × recipient × response/uptake to the trajectory audit.** This connects the trace evidence to established human-agent team dimensions without mistaking the message’s wording for its cause.
5. **Use industry documents to expand the design space, not to validate outcomes.** Product docs provide examples of approval gates, handoffs, context transfer, status updates, and specialist delegation. We should cite them as examples of current practice and test efficacy using traces/controlled experiments.

### Novelty and claim audit

- The general idea of classifying human-agent team structure is **already established** by Chung et al.; the 2026 guidelines also synthesize 93 empirical papers into design recommendations. We should not claim the first general human-agent taxonomy or the first review of human-agent teamwork.
- The more defensible contribution is a **cross-level operational framework**: connect team context and authority structure to the *episode-level* function, trigger, recipient rationale, timing, response, and uptake of agent-initiated help across multiple human coworkers.
- ReHAC covers intervention timing; PeopleJoin covers coworker discovery/information gathering; Muses-Bench covers shared-agent multi-principal conflict/privacy/coordination. The focused search did not identify one of these as integrating all these dimensions for multi-step enterprise help-seeking. Phrase this as a **provisional gap from a focused search**, not proof of absence.
- The current TAC evidence is especially weak for spontaneous help-seeking because contact is often prescribed by the task. It can ground the observed communication categories and help identify process failures; it cannot alone establish autonomous need detection or correct-recipient rates.
- To make a taxonomy contribution substantive, the next study needs a versioned codebook, examples and counterexamples, unit/decision rules, independent coding with agreement/adjudication, and application to more than one trace source where the construct is genuinely comparable. The source-specific limitations (especially generic responder roles in HiL-Bench/AskBench) must remain visible.

## Reference register and source type

The labels below are **our synthesis labels**, not names claimed by every cited source. The register distinguishes scholarly research from company practice documentation so a reader can tell what kind of evidence supports each category.

| ID | Reference | Source type and use here |
|---|---|---|
| **R01** | Chung, H., Holder, T., Shah, J., & Yang, X. J. (2024). [Developing a Team Classification Scheme for Human-Agent Teaming](https://journals.sagepub.com/doi/10.1177/10711813241260387). *Proceedings of the Human Factors and Ergonomics Society Annual Meeting*. | Peer-reviewed conference proceedings; source for macro team-structure dimensions, especially role, leadership, authority, and communication. |
| **R02** | Yurrita, M., Dell’Anna, D., Murukannaiah, P. K., Jonker, C. M., & Yolum, P. (2026). [Developing Guidelines for Human-LLM Agent Teams: A Multi-Stakeholder Lens](https://doi.org/10.65109/JOWO4591). *AAMAS 2026*, 1956–1966. | Peer-reviewed conference paper; workshop + review of 93 empirical papers + expert study. Supports goal clarification, authorization, checking decisions, team process. |
| **R03** | Wang, Y., & Lu, Y. (2025). [Interaction, Process, Infrastructure: A Unified Framework for Human-Agent Collaboration](https://www.microsoft.com/en-us/research/publication/interaction-process-infrastructure-a-unified-framework-for-human-agent-collaboration/). | Microsoft Research-hosted conceptual preprint; supports placing interactions within an explicit, adaptive workflow. Not a validated episode taxonomy. |
| **R04** | Jhamtani, H., Andreas, J., & Van Durme, B. (2025). [LLM Agents for Coordinating Multi-User Information Gathering](https://aclanthology.org/2025.findings-acl.916/). *Findings of ACL 2025*, 17800–17826. | Peer-reviewed conference paper; direct benchmark precedent for discovering coworkers, gathering distributed information, and synthesizing a response. |
| **R05** | Xu, F. F., et al. (2025). [TheAgentCompany: Benchmarking LLM Agents on Consequential Real World Tasks](https://arxiv.org/abs/2412.14161). *NeurIPS 2025 Datasets and Benchmarks*. | Peer-reviewed benchmark paper and task/trace source; evidence for workplace messages, task-directed information collection, and colleague interaction in this dataset. |
| **R06** | Yang, S., et al. (2026). [Multi-User Large Language Model Agents](https://arxiv.org/abs/2604.08567). | Research preprint introducing Muses-Bench; supports multi-principal authority conflict, cross-user privacy, and meeting coordination. |
| **R07** | Pagnozzi, F., & Antonelli, G. (2025). [How to seek help? A systematic literature review of help-seeking practices in organizations](https://link.springer.com/article/10.1007/s11301-025-00570-0). *Management Review Quarterly*. | Peer-reviewed systematic review of 93 organizational studies; supports treating help-seeking as embedded in organizational networks, roles, accessibility, and technical context. |
| **R08** | Hofmann, D. A., Lei, Z., & Grant, A. M. (2009). [Seeking help in the shadow of doubt: The sensemaking processes underlying how nurses decide whom to ask for advice](https://doi.org/10.1037/a0016557). *Journal of Applied Psychology, 94*(5), 1261–1274. | Peer-reviewed organizational study; direct evidence that expertise, role, accessibility, and trust affect whom people ask. |
| **R09** | Sherf, E. N., Gilliam, N., & McElroy, T. (2024). [A reinforcement sensitivity theory view of seeking behaviors at work: A meta-analysis](https://doi.org/10.1111/peps.12579). *Personnel Psychology, 77*, 847–890. | Peer-reviewed meta-analysis of 393 samples; distinguishes help-, advice-, information-, and feedback-seeking as related but separate constructs. |
| **R10** | Tomašev, N., Franklin, M., & Osindero, S. (2026). [Intelligent AI Delegation](https://arxiv.org/abs/2602.11865). | Google DeepMind research preprint; supports role/boundary clarity, transfer of authority/responsibility, adaptive negotiation, and trust in delegation. |
| **R11** | Tomasev, N., & Yadav, R. (2026). [How agents can delegate better](https://cloud.google.com/blog/products/ai-machine-learning/how-agents-can-delegate-better/). | Google Cloud company blog/practice interpretation; describes challenging ambiguous requests and asking for human verification while controlling interruption burden. |
| **R12** | Anthropic. (2026). [Patterns and problems in multiagent systems](https://www.anthropic.com/research/multiagent-systems). | Company research/field report; documents conflict escalation among agents with incompatible goals and identifies deference/conflict resolution as open issues. |
| **R13** | OpenAI. [Human-in-the-loop](https://openai.github.io/openai-agents-python/human_in_the_loop/). | Official developer documentation; illustrates pause/approve/reject/resume patterns for tool actions, including nested or handed-off agents. |
| **R14** | Microsoft. [Multistage and AI approvals in agent flows](https://learn.microsoft.com/en-us/microsoft-copilot-studio/flows-advanced-approvals). | Official product documentation; illustrates sequential AI and human approval stages. Preview/product evidence, not outcome evaluation. |
| **R15** | Microsoft. [Design autonomous agent capabilities](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/autonomous-agents). | Official product guidance; recommends human confirmation for sensitive actions and least-privilege access. |
| **R16** | Microsoft. [Multi-agent orchestration patterns and best practices](https://learn.microsoft.com/en-us/microsoft-copilot-studio/guidance/multi-agent-patterns). | Official product guidance; supports specialist-agent routing, context handoff, access controls, audit, and approval safeguards. |
| **R17** | Microsoft. [Connected agents overview](https://learn.microsoft.com/en-us/microsoft-copilot-studio/agents-experience/authoring-add-other-agents). | Official product documentation; describes capability/domain-based specialist routing and returning a response to the primary agent. |
| **R18** | Microsoft. [Configure handoff to any generic engagement hub](https://learn.microsoft.com/en-us/microsoft-copilot-studio/configure-generic-handoff). | Official product documentation; illustrates context-preserving escalation to a skilled human selected by availability. Customer-support context. |
| **R19** | Google. [Announcing the Agent2Agent Protocol (A2A)](https://developers.googleblog.com/a2a-a-new-era-of-agent-interoperability/). | Company protocol announcement/spec context; supports capability discovery, task delegation, messages, artifacts, and long-running status updates among agents. |
| **R20** | Jaye, A., et al. (2026). [CORPGEN: Simulating Corporate Environments with Autonomous Digital Employees in Multi-Horizon Task Environments](https://www.microsoft.com/en-us/research/publication/corpgen-simulating-corporate-environments-with-autonomous-digital-employees-in-multi-horizon-task-environments/). | Microsoft Research paper and company report; supports asynchronous requests/responses, role-based digital employees, subagent specialization, and shared artifacts in a simulated organization. |
| **R21** | Feng, X., et al. (2024). [Large Language Model-based Human-Agent Collaboration for Complex Task Solving](https://aclanthology.org/2024.findings-emnlp.72/). *Findings of EMNLP 2024*, 1336–1357. | Peer-reviewed conference paper; direct precedent for timing human intervention in multi-step tasks and real/simulated human responses. |
| **R22** | Salesforce. (2026). [The Art of the Handoff: How Agentforce Voice Escalation Works](https://www.salesforce.com/blog/agent-handoff/). | Company product/practice article; illustrates user-triggered or rule-triggered customer-service escalation after agent pre-work. |
| **R23** | Liu, Y., Chen, F. X., Chiang, J. T.-J., Wang, Z., & Liu, H. (2022). [Asking how to fish vs. asking for fish: Antecedents and outcomes of different types of help-seeking at work](https://doi.org/10.1111/peps.12479). *Personnel Psychology, 75*(3), 557–587. | Peer-reviewed workplace study; supports differentiating help that builds capability/autonomy from requests for a complete answer/solution. |
