# Benchmark Contribution Brainstorm: Role-Aware Help-Seeking

> Discussion update, 2026-10-23. This is a seed memo for a **separate future research proposal**, not an expansion of the current Role-Aware Help-Seeking paper. It revises the novelty framing after checking PeopleJoin, Muses-Bench, TheAgentCompany, Co-Gym, HiL-Bench, and Manager Agent Gym. See the future-proposal queue in `06_Publication_Plan_20261023-1921.md`.

## 1. Revised premise

We should **not** claim that multi-user organizational agent traces or synthetic multi-user organizations are absent. PeopleJoin already evaluates agents that identify teammates, contact them, gather information, and complete a task in synthetic organizations of 2–20 users. Its QA and document-creation tasks derive from existing datasets, and its code supports generating more organizations. Muses-Bench already covers multi-user instruction following, access control, meeting coordination, and synthetic scenario generation. TheAgentCompany already provides long-horizon workplace tasks, simulated colleagues, and released model traces.

The defensible opportunity is narrower and more specific: build a **resettable, process-auditable benchmark for role-aware help-seeking during multi-step organizational work**, where asking is a decision with both informational and organizational consequences. The benchmark would make explicit and jointly test:

- whether a person has relevant task knowledge;
- whether that person has authority for the action being requested;
- the cost/availability of interrupting that person;
- whether to ask now or continue autonomously;
- how the team/workflow structure changes the value of asking.

This is a candidate gap, not a proven novelty claim. A targeted literature review and benchmark-by-benchmark feature audit are still required before submission.

## 2. What existing work already covers

| Resource | Existing coverage | What it does not directly provide for this project |
|---|---|---|
| [PeopleJoin](https://github.com/microsoft/peoplejoin) | Multi-step information gathering from synthetic organizations; agent chooses whom to contact; QA and document creation; answer accuracy and contact efficiency. | Its primary task is obtaining distributed information. It does not appear to jointly operationalize action-specific approval authority, interruption cost, and team-structure moderators in long-horizon enterprise workflows. Verify this against the full paper and current code before making a claim. |
| [Muses-Bench / Multi-User LLM Agents](https://github.com/Kordi-Lab/Multi-User-LLM-Agent) | Multi-principal instruction conflict, access-control/privacy, meeting coordination; synthetic users/scenarios and runnable model evaluation. | It studies the agent serving multiple principals and coordinating requests; this is not the same estimand as an executing agent proactively choosing which colleague to consult for task knowledge or approval during a workflow. Meeting coordination is an important adjacent case and must be compared directly. |
| [TheAgentCompany](https://github.com/TheAgentCompany/TheAgentCompany) and [released experiments](https://github.com/TheAgentCompany/experiments) | Long-horizon simulated workplace tasks, NPC colleagues, checkpoints, execution traces, and multi-model results. | Existing tasks/traces were not designed as a balanced, resettable factorial benchmark for profile information, cost, knowledge-authority separation, or team structure. Some prompts name the colleague to contact. |
| [Co-Gym](https://github.com/SALT-NLP/collaborative-gym) | Extensible, resettable human-agent collaboration framework with simulated and real conditions, event logs, and outcome/process metrics. | Its released tasks primarily model one human collaborator with one agent; not a multi-colleague role/authority routing benchmark. |
| [HiL-Bench](https://github.com/hilbenchauthors/hil-bench) | Controlled blockers and an ask-human action; measures when to seek clarification versus guess, with rerunnable task environments. | One generic clarification source rather than multiple colleagues with distinct knowledge, authority, or interruption cost; coding and SQL domains. |
| [Manager Agent Gym](https://github.com/DeepFlow-research/manager_agent_gym) | Multi-worker workflow graphs, simulated human and AI workers, changing teams and constraints; relevant to team structure and task interdependence. | Its main decision is workflow decomposition/assignment by a manager, not an executor's when-and-whom help-seeking policy. |

Primary references: [PeopleJoin ACL Anthology paper](https://aclanthology.org/2025.findings-acl.916/); [Muses-Bench official repository](https://github.com/Kordi-Lab/Multi-User-LLM-Agent); [TheAgentCompany experiment-data README](https://github.com/TheAgentCompany/experiments); [Co-Gym paper](https://arxiv.org/abs/2412.15701); [HiL-Bench paper](https://arxiv.org/abs/2604.09408); [Manager Agent Gym paper](https://arxiv.org/abs/2510.02557).

## 3. Proposed contribution package

### Contribution 1 — A sharper problem formulation

Define organizational help-seeking as a sequential decision problem with two linked choices: **whether/when to ask** and **which principal to ask**. Distinguish at least three kinds of correctness:

1. **Epistemic correctness:** did the recipient possess the information needed?
2. **Normative/authority correctness:** could that recipient legitimately provide the approval or authorize the requested action?
3. **Economic/process efficiency:** was the information worth the interruption, delay, or extra interaction?

This differs from treating every colleague as an interchangeable source of clarification or measuring only whether the final answer/task is correct.

### Contribution 2 — A benchmark, not merely a trace dump

Release a benchmark with three separable layers:

1. **Scenario specification:** task goal, initial state, team roster, private knowledge, action-specific permissions, costs/availability, task dependencies, valid help paths, and machine-checkable success criteria.
2. **Executable environment:** reset/replay API, agent action interface, grounded NPC responses, and rule-based evaluators. Hosted LLM APIs can run the agent and NPCs; local model hosting is optional.
3. **Trace corpus:** complete actions/messages/replies, model and prompt metadata, condition assignments, checkpoint outcomes, costs, authority violations, and annotations for all runs.

A trace-only release is useful, but the stronger contribution is the **environment + scenario schema + benchmark protocol + reference traces**. This allows other researchers to run new agents and intervene on experimental factors.

### Contribution 3 — A controlled empirical map of help-seeking behavior

Use matched scenario variants to answer RQ2–RQ3:

- role information: names only / prose / structured profile, with equal semantic content for prose and structured profiles;
- knowledge-authority assignment: aligned / separated;
- candidate composition: no distractor / knowledge-only / authority-only / partial-knowledge / high-cost candidates;
- interruption-cost and authority-penalty settings, evaluated against a scenario-derived oracle;
- outcomes: first-contact validity, valid-path completion, task score, unauthorized requests/actions, missed consultations, redundant queries, total cost, and regret.

This contribution is about evidence and validated measurement, not simply publishing a larger number of synthetic rows.

### Contribution 4 — A reusable policy-learning track (Paper 2)

Generate trajectories under randomized or exploratory help-seeking policies, train a joint when-and-whom policy, and evaluate on held-out tasks and **held-out organizational structures**. Keep this as a later paper if building the environment and validating the benchmark already form a substantial first paper.

### Contribution 5 — Team structure as a modular extension (Paper 3)

Use the same scenario families while changing one structural property at a time: task interdependence, team lifespan, and communication topology. This should be a separately powered study, not an uncontrolled bundle of structural changes.

## 4. Minimum useful data design

### Scenario records

Each scenario should encode:

- `task_id`, `task_family`, `initial_state`, `goal`, and task checkpoints;
- a roster of stable participant IDs, role descriptions, knowledge/evidence ownership, action-specific permissions, availability, reliability assumptions, and interruption cost;
- a communication graph/channel configuration and team lifespan;
- hidden ground truth and valid action/help paths;
- distractor types and an oracle policy or dynamic-programming solution for the specified cost regime;
- reset seed, NPC response rules, evaluator version, and license/provenance.

### Trace records

For each event, log the observation/state ID, agent action, whether it was `SELF` or `ASK(person_id, question)`, recipient, message, NPC reply, evidence revealed, permission verdict, whether the answer was used, elapsed interaction/turn cost, and subsequent checkpoint/final result. Store model/provider/version, prompt/config hash, temperature/seeds, retries, and error/termination state.

### Scenario and trace quality controls

- Keep the answer/ground truth out of the agent-visible profile; profiles describe capability and authority, not the answer itself.
- NPCs should answer only from scenario-owned knowledge, and should refuse unauthorized disclosure/approval according to scripted rules.
- Human reviewers should validate that each task really requires the modeled help and that distractors are plausible.
- Publish both successful and failed traces; do not curate only clean demonstrations.
- Separate templates from repeated stochastic runs in analysis; scenario template is the sampling unit for generalization.
- Report sensitivity to NPC implementation and model versions.

## 5. What makes simulated data credible enough

Simulation is acceptable for controlled benchmark claims, as TheAgentCompany and other benchmarks demonstrate, but synthetic generation alone is not evidence of realism. The paper should validate the environment at several levels:

1. **Construct validity:** experts agree that the scenario encodes the intended knowledge, authority, cost, and team-structure conditions.
2. **Evaluator validity:** rule-based metrics correctly identify legal/illegal actions and task completion; manually audit edge cases.
3. **Behavioral validity:** NPC responses are grounded and consistent; compare a small human-authored or human-played subset if feasible.
4. **Intervention validity:** matched variants differ only in the intended factor; profile formats contain semantically equivalent information.
5. **Robustness:** replicate across multiple models, seeds, task families, and unseen organizations.

Claims should be bounded to the benchmark if real workplace behavior has not been validated. A small human validation subset is valuable but is not required to establish benchmark reproducibility.

## 6. Suggested staged scope

### Paper 1: Benchmark + characterization (RQ1–RQ3)

- Study 1: audit existing TheAgentCompany traces; observational evidence only.
- Study 2/3: controlled reruns in the new benchmark for role profiles, knowledge-authority separation, interruption cost, and oracle regret.
- Main contribution: formal task definition, scenario benchmark, reliable metrics, and empirical characterization.

### Paper 2: Learning a policy (RQ4)

- Train joint when/whom strategy on environment-generated trajectories.
- Test generalization on new task templates and organizations, compare against prompts, sequential policy, and oracle.

### Paper 3: Team structure (RQ5)

- Reuse the benchmark with explicit matched topology/interdependence/lifespan manipulations.
- Estimate moderation effects rather than merely report different aggregate scores.

Keep a small Paper 0 workshop study limited to preliminary diagnosis and a pilot causal probe; do not promise the full benchmark, trained policy, and RQ5 factorial in the short paper.

## 7. Recommended novelty statement (working draft)

> Existing resources study complementary pieces of organizational agent behavior: long-horizon workplace execution, multi-user information gathering, multi-principal governance, and human-agent collaboration. We propose a controlled benchmark for the help-seeking decisions that connect these settings: deciding whether to seek assistance and which colleague to approach when knowledge, action authority, and interruption cost are distributed across a team. The benchmark supports end-to-end reruns, rule-based process evaluation, and controlled variation in organizational structure.

This statement must be revised after a systematic comparison with PeopleJoin, Muses-Bench, TheAgentCompany, and any newer work. Avoid “first” until that comparison is completed.

## 8. Open design decisions

1. Should the main benchmark be a new lightweight environment, an extension of PeopleJoin, an extension of TheAgentCompany, or a modular combination?
2. Is the core construct “whom to ask” with when as a necessary control, or fully joint when-and-whom from the outset?
3. Which approval actions should anchor authority validity (budget approval, access grant, task sign-off)?
4. Should costs be treated as stipulated benchmark parameters only, or calibrated with a small human rating study?
5. Which team-structure dimensions belong in the first release, and which should be reserved for Paper 3?

