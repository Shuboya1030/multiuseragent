# RQ1/RQ2 Data and Experiment Design

> Working memo, 2026-10-23. Assumes “RQ A” means the proposal's RQ1 (diagnosing current help-seeking failures). This is a design for the current Role-Aware Help-Seeking paper, not the separate future proposal to build a general-purpose reusable organizational benchmark.

## Recommendation in one paragraph

Use **TheAgentCompany (TAC) historical traces as the primary RQ1 dataset**. For RQ2, run a controlled, matched experiment on a **small study-specific set of resettable scenarios** seeded primarily by TAC, with a smaller PeopleJoin-derived information-gathering stratum if resources permit. Use Muses-Bench only as a separate permission/coordination stress check, not as pooled core data. Analyze each source/domain separately or as a prespecified stratum; do not report a pooled “overall success” that conflates different task constructs. This gives the current paper external breadth without turning it into the separate benchmark-building proposal.

## 1. RQ1: diagnose help-seeking failures

### Primary data: TheAgentCompany experiments

- Start with the released trajectories and task evaluator/checkpoint records.
- Include all eligible trajectories for the colleague-relevant task set after auditing the actual task IDs, prompts, and trace availability. Existing proposal notes cite approximately 400 traces and about 40–41 colleague-related/scenario-backed tasks; reconcile that denominator before preregistration.
- Keep two analyses distinct:
  1. **Communication execution:** contact, reply use/follow-up, redundancy, task outcome. May include tasks whose instructions name a person.
  2. **Recipient selection (“whom”):** only tasks where the agent is not explicitly told the correct recipient, or report named-recipient tasks as a separate instruction-following stratum.
- Use task scenario metadata to define expected information holders/valid paths where available. Do not infer a unique “correct person” when multiple recipients are valid.
- Label event-level errors and task-level missed opportunities separately; multiple events within a trajectory are not independent samples.
- Treat relations between help-seeking errors and task score as **associations**, not causal effects. Harder tasks may cause both failed communication and lower scores.

### Optional external replication: PeopleJoin

PeopleJoin is a strong adjacent task source because it asks agents to identify and contact teammates in synthetic organizations to gather information. If we add it to RQ1, run a small, instrumented comparison with the same available model/harness families and harmonized annotations. Report it as a separate “information gathering” stratum; do not combine its rates with TAC's workplace workflow rates. Its task generation code can create organization/task instances, but generated reruns are a new controlled benchmark evaluation, not historical traces of deployment behavior.

### Not a main RQ1 source: Muses-Bench

Muses-Bench can provide supplementary evidence on multi-user authority and meeting coordination. Its instruction-following/access-control scenarios mostly test how the shared agent responds to principals, and meeting scheduling may require soliciting constraints from everyone rather than choosing the best knowledge/authority holder. Use only a clearly matched subset, and report it separately. It is not a substitute for TAC's work-execution traces.

### RQ1 outputs

- Counts/rates with denominators by dataset, task type, model, and whether the target was named in the prompt.
- Categories: failed to reach/use communication channel, missed needed consultation, wrong/low-value recipient, no follow-up/use of reply, redundant query, invalid authority request where ground truth supports it.
- Association between prespecified help-seeking errors and task/checkpoint success, with task/model clustering and uncertainty intervals.
- Manual audit of a random subset of LLM-assisted annotations; revise codebook before full coding if disagreements expose ambiguity.

## 2. RQ2: does role information improve help-seeking?

### Core study conditions

Use within-scenario matched reruns from identical initial states:

- **R0:** candidate names/IDs only.
- **R1:** natural-language role and responsibility descriptions.
- **R2:** structured profile.

R1 and R2 must contain the same semantic facts. Neither can reveal the answer itself. Give the evaluator complete private ground truth regardless of what the agent sees.

Cross role-information condition with **knowledge-authority alignment** only in task scenarios where both concepts are meaningful:

- **Aligned:** one colleague holds required knowledge and has authority for the relevant decision.
- **Separated:** one colleague holds knowledge; a different colleague has the authority to approve/act.

Include distractor variants only when each distractor is semantically defined (knowledge but no authority; authority but no knowledge; partial knowledge). A no-distractor control tests whether role information matters only when recipient choice is nontrivial.

### Which scenario sources to use

| Scenario source | RQ2 role | Recommendation |
|---|---|---|
| TAC-derived scenarios | Main enterprise-work stratum; best match to the paper's motivating context and multi-step execution. | Primary. Select tasks with hidden/known recipient ground truth and rewrite prompts that name the target. Make matched variants with identical goal and answer state. Add controlled approval steps only when the task naturally supports them. |
| PeopleJoin-derived scenarios | Knowledge-holder selection and information-gathering replication. | Optional secondary stratum. Convert a subset to R0/R1/R2 profiles; use for knowledge-routing effects. Do not claim authority effects unless approval authority is explicitly added as a new experimental manipulation (then label the scenarios as adapted, not native PeopleJoin tasks). |
| Muses-Bench scenarios | Authority/access-control and multi-user coordination stress cases. | Small supplementary stratum. Use a task only if it contains an actual recipient choice and a clear action-specific permission ground truth. Meeting tasks where everyone must be queried are not valid “whom” tests. |

Do not require all three datasets in the first RQ2 run. The cleanest initial study is TAC-derived matched scenarios only; add PeopleJoin as replication if the pilot codebook and harness are stable. Muses can remain a robustness/scope check.

### Execution controls and measures

- Reset every scenario for each role condition; pair on task template, model, NPC policy, and seed where possible.
- Randomize run order and log provider/model version, prompt/config hash, seed, and failures.
- Use scripted or retrieval-grounded NPC replies and rule-based task/authority evaluators. The agent may use a hosted API; self-hosting is not required.
- Primary outcome: first-contact validity, defined against the task's acceptable-recipient set. Secondary outcomes: valid-path completion, task/checkpoint score, follow-up, authority violations, number of queries, and stipulated interruption cost.
- Analyze task templates as the sampling units; repeated seeds are repeated measurements, not new independent tasks. Include task and model effects. Treat source/domain as strata or a moderator, not as interchangeable rows.
- Pilot roughly 30–50 scenario templates as currently scoped, then use observed variance and a detectable-effect/power or sensitivity analysis to choose confirmatory sample size. Do not claim that a convenient pilot count is automatically adequately powered.

## 3. What multiple datasets buy us—and what they cost

Using multiple sources can test whether effects replicate across enterprise workflows and information-gathering tasks. It also adds scenario conversion, differing success metrics, difficulty confounds, and possible changes in the construct. Therefore:

1. Keep TAC as the primary source for RQ1 and primary RQ2 claims.
2. Use PeopleJoin as an external replication for knowledge-based recipient selection, if feasible.
3. Use Muses only for a narrowly matched permission/coordination check.
4. Report source-specific results and a source-by-condition interaction; avoid pooling unless metric equivalence is justified in advance.
5. The small, task-specific scenario pack is experimental stimulus material for this paper. A larger reusable environment, broad task taxonomy, and benchmark release belong to the separate future proposal queued in the publication plan.

## 4. Likely claims and limits

Potentially supportable claims:

- Existing TAC runs contain observable help-seeking/communication failure patterns.
- Under controlled matched scenarios, profile information changes agent recipient selection and/or task outcomes.
- Knowledge-authority separation is a distinct stress condition for help-seeking.
- A result replicates in PeopleJoin-like information-gathering tasks only if the separate stratum supports it.

Do not claim that results establish realistic human interruption costs, general organizational behavior, or an ecosystem-wide benchmark result without corresponding validation.

## 5. Primary references

- [TheAgentCompany experiment traces](https://github.com/TheAgentCompany/experiments)
- [PeopleJoin paper](https://aclanthology.org/2025.findings-acl.916/) and [code/data](https://github.com/microsoft/peoplejoin)
- [Muses-Bench code and scenarios](https://github.com/Kordi-Lab/Multi-User-LLM-Agent)
- [Current proposal](01_PhD_Research_Proposal_RoleAwareHelpSeeking_20261023-1919.docx)
- [Hypotheses and experiment design](02_Hypotheses_and_Experiment_Design_20261023-1423.md)

