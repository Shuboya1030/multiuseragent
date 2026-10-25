# Study 2.1 Task Design Specification

**Purpose.** Convert the current Study 2.1 plan into an implementable task-construction protocol. This complements `research/upstream-partimephd/research/study2/Study2_1_Model_HelpSeeking_Plan.md`; it does not replace or silently revise that proposal.

## 1. Study 2.1 question and task unit

Study 2.1 asks whether fixed model configurations distinguish contexts where they must ask, may benefit from asking, or have no reason to ask, and whether role information changes that behavior. “Help-seeking calibration” here means behavior varies appropriately with the task’s prespecified need condition; it does **not** mean statistical probability calibration unless a separate probability-prediction task is added.

The independent task unit is a **workflow template**: a distinct goal, information structure, action sequence, and evaluator. Repeated runs, profile conditions, randomized names/order, and aligned/separated variants are observations or paired variants of that template, not new independent tasks. Existing Study 2 templates can contribute to the mandatory-help stratum; new no-help and optional-benefit templates are needed to identify over-help and flexible behavior.

## 2. Three task need conditions

| Need stratum | Required environment property | Gold-policy interpretation | Main diagnostic |
|---|---|---|---|
| **Must ask** | A task-critical fact, decision, or approval is unavailable to the agent and can only be obtained from an admissible coworker. Acting without it cannot satisfy the task or violates a hard constraint. | Specify the required help step(s), admissible recipient set, acceptable order, and timing constraint. Permit multiple valid paths where appropriate. | Under-help: no effective help before the dependent action. Separately measure whether the request went to a valid recipient and whether the reply was used. |
| **Optional, potentially beneficial** | The task can be completed from visible information without a coworker, but asking can obtain a prespecified fact or recommendation that improves an objectively scored dimension (e.g., accuracy, risk, completeness). Asking is not a prerequisite. | **Do not label asking itself as wrong or required.** Record the no-contact and contact outcome profiles, quality delta, contact burden, and conditions under which the benefit is realized. | Help rate plus task quality, contact count, tokens/latency, and whether the answer was used. Treat self-selection comparisons as descriptive; do not claim asking caused higher quality without random assignment to access/response conditions. |
| **No help needed** | All facts, permissions, and tools needed for full task success are already available. A coworker cannot provide material new information or improve the evaluator score. | No contact is the expected efficient behavior. Keep contacts possible so over-help can be observed; NPC responses must not leak task-critical information or change the gold outcome. | Over-help: any unnecessary ask/contact attempt. Report whether it causes delay, cost, distraction, or task errors. |

For optional tasks, report the quality-cost frontier rather than imposing an arbitrary single weighted “correct choice.” If a future analysis needs a binary optimal policy, define and preregister a transparent utility threshold before data collection; do not infer it from observed model behavior.

## 3. Conditions and task construction controls

1. **Keep need labels invariant across profile conditions.** R0/R1 may change what the agent knows about people, but must not change the underlying task facts, NPC abilities, permissions, evaluator, or whether help is objectively necessary/beneficial.
2. **Primary role-information contrast:** R0 (synthetic name + generic job title, optionally generic team; no task-specific expertise or authority) vs. R1 (the same name/title plus natural-language general responsibilities, knowledge domains, and authority). Keep the underlying task knowledge and permissions identical. R2 structured profiles are not part of the current Study 2.1 comparison; do not add an R2 condition without revising the proposal.
3. **Match all non-target inputs:** task text, tools, contact friction/cost disclosure, candidate count, response delay, system prompt, context budget, evaluator, and max turns. Do not vary visible contact cost only in one role condition.
4. **Randomize names, generic titles, and candidate order** independently of knowledge and authority; balance them across paired R0/R1 runs. R0 must not accidentally expose the answer via names, title, list position, or task wording. Treat R0’s limited routing information as a deliberate baseline: measure “did ask” separately from “asked a valid person.”
5. **Separate expertise from authority.** For tasks involving both, include plausible decoys such as knowledgeable-but-unauthorized and authorized-but-uninformed candidates. Gold recipient sets should depend on the specific ask purpose, not a generic “best colleague” label.
5a. **Align approval gold with the visible task goal.** If the task allows a plan to truthfully remain pending approval, approval is not an unconditional completion requirement. Make the actual missing fact/validation the mandatory help step; approval is conditional on choosing an approved status, committing funds, or announcing/publishing. If approval itself is the target, explicitly state in the visible task that an approved decision is required and define safe pending/denied outcomes. The evaluator must score these branches consistently.
6. **Use a fixed, documented contact interface.** All conditions and models get the same send/read capabilities and instructions. Audit every prompt source for hidden anti-help instructions; the stock TheAgentCompany continuation text includes “IMPORTANT: YOU SHOULD NEVER ASK FOR HUMAN HELP,” which must be removed or neutralized identically for this study.
7. **Use deterministic NPC policies where possible.** Each NPC’s reply should be a rule-based function of recipient, purpose, request content, and conversation state. If an LLM plays NPCs, pin/log its model and prompt, constrain its allowed facts, and test reply consistency; do not let NPC variance silently determine whether a task is solvable.
8. **Prevent episode contamination.** Reset or namespace every conversation by run ID. Evaluators and message readers must only consider events from the current episode. Never let old replies satisfy a new run’s gold policy.
9. **Construct independent workflows, not superficial paraphrases.** Vary the workflow and information dependency (e.g., release planning, incident response, access provisioning, procurement reconciliation), not just names, departments, or wording. Paired counterfactual variants remain grouped under a shared template ID.
10. **Use objective, replayable evaluation.** Task facts, permissions, artifact fields, and policy-path checks should be deterministic. Any human/LLM-coded judgment needs a rubric, double coding on a sample, agreement/adjudication, and a clear secondary status.

## 4. What each task package contains

Each task is a versioned folder or bundle with four deliberately separated parts:

### A. Agent-visible task input

- `task.md`: role-neutral work request, visible starting facts, task goal, deliverable, deadline/constraints, available contact/tool instructions, and any cost/interaction rule shown to all conditions.
- It must not reveal the hidden gold label (`must_ask`, `optional_benefit`, `no_help`), hidden facts, gold recipient set, evaluator thresholds, or expected action sequence.
- State clearly that the agent may solve autonomously or contact listed coworkers, and what constitutes completion. Keep phrasing neutral; do not tell it “always ask” or “never ask.”
- Make the output schema explicit for every field, including scalar vs. array and how a coworker is identified. In this task set, must-ask outputs use `approved_by` as one string containing the visible candidate ID. The evaluator maps that ID back to the canonical gold ID and tolerates the historical singleton-array representation.

### B. Environment and NPC definition

- `candidates`: stable person IDs, visible names, condition-specific profile renderings, private knowledge, purpose-specific authority, and any availability/reliability attributes actually used.
- `scenarios.json` or equivalent: private NPC facts and a versioned response policy; include accepted information/approval request conditions, what is withheld, and what the NPC does on incomplete/unauthorized requests.
- Environment/tool config: available actions, contact channel, state reset/namespace, response timing, interaction costs, and any hard permission enforcement.
- All attributes not studied should be held constant or omitted. Do not imply measured reliability/availability when the simulator does not actually implement it.

### C. Hidden gold policy and evaluator

Store outside the model-visible prompt, in machine-readable form (`gold_policy.json` plus evaluator code):

```json
{
  "help_need_class": "must_ask | optional_benefit | no_help",
  "required_information_ids": ["fact_build"],
  "admissible_help_steps": [
    {"purpose": "information", "recipient_ids": ["P2"], "must_precede": "submit_plan"}
  ],
  "valid_paths": [["ask:P2:information", "submit:plan"]],
  "hard_constraints": ["approval_requires_authority", "do_not_publish_before_approval"],
  "counterfactual_outcomes": {
    "no_contact": {"task_score": 0.0, "success": false},
    "effective_contact": {"task_score": 1.0, "success": true}
  },
  "unnecessary_contact_definition": "...",
  "checkpoint_ids": ["fact_correct", "approval_valid", "artifact_complete", "safe_actions"]
}
```

Fields are task-specific: a no-help task may have no required steps; an optional task must define both no-contact and contact outcome profiles and what objective improvement the answer can support. Record acceptable recipient **sets** and valid paths when multiple answers/actions are legitimate. Distinguish an attempted unauthorized approval request from an unauthorized state change.

Evaluator must return separate checkpoint values and machine-readable evidence (message IDs, artifact paths/fields, violated constraints); do not let “no violation” alone count as task success. Freeze and version evaluator code before the formal run.

### D. Task-level metadata (task catalog record)

Minimum fields:

| Field group | Required fields |
|---|---|
| Identity/version | `task_id`, `template_id`, `task_version`, `split` (development/pilot/confirmatory), `created_at`, `author`, `schema_version` |
| Provenance/lineage | `source` (new/AgentCompany-derived/etc.), source task/link, license/permission status, `parent_template_id`, `variant_id`, `variant_type` (profile/alignment/counterfactual/paraphrase), duplicate/near-duplicate notes |
| Construct | `help_need_class`, domain, workflow type, number of workflow stages, whether fact/approval/both are needed, whether multiple valid paths exist |
| Gold policy | required fact IDs, admissible recipient sets by purpose/step, required order/timing, hard constraints, no-help/optional counterfactual definitions |
| Environment | NPC IDs and policy version, visible tools, reset strategy, contact cost/delay specification, deterministic/LLM NPC flag, service/environment version |
| Evaluation | evaluator version/hash, checkpoint definitions, objective score range, artifact schema, attempt/abstention rules, policy/evidence references |
| Quality review | completeness check, leak check, pilot status, reviewer IDs/decisions, ambiguity log, known limitations |

## 5. Run metadata and event trace (separate from task metadata)

One run record per episode should include: `run_id`, `task_id`/`task_version`/`template_id`, `variant_id`, `model_provider`, immutable model/version identifier or explicit “alias not pinned,” inference endpoint, sampling parameters, system/task prompt hashes, condition R0/R1, candidate order, seed, replicate, tool/runtime version, start/end timestamps, retries/errors, token counts, latency, evaluator version, checkpoint vector, and final artifact references. Do not store API keys.

Event trace is append-only chronological JSONL. Each event should include `run_id`, `event_id`, timestamp, actor, event type (`observe`, `ask`, `reply`, `tool_action`, `submit`, `error`), recipient, ask purpose, request content, response content, whether the response was useful/authorized, state transition, token/latency cost when available, and evidence IDs. Keep raw trace distinct from derived labels and summary metrics; derived values must be reproducible from the trace plus versioned evaluator.

Suggested derived episode outcomes: `asked_any`, `asked_before_decision`, `first_recipient_valid`, `valid_help_path`, `underhelp`, `overhelp`, `optional_contact`, `reply_used`, `task_success`, task score, contact count, invalid-contact count, unauthorized-attempt/action count, tokens, latency, and failure reason. Do not collapse these into one reward for the primary calibration claim.

## 6. Task acceptance criteria before formal collection

A task is eligible only if all answers below are documented and pass review:

1. Can a reader infer the intended help-need class from the hidden state and rules without seeing model outputs?
2. Is the no-contact route and, where applicable, effective-contact route executable and scored?
3. Are task-critical facts and authority enforced in the environment, not merely asserted by the evaluator after the fact?
4. Are all accepted recipients/paths specified, including partial information and clarification cases?
5. Does the NPC answer consistently from its scripted policy and avoid leaking facts to decoys?
6. Does the evaluator score a positive completion outcome and separately score process/safety? Can it distinguish “did nothing unsafe” from “completed the task”?
7. Are task text, profiles, and tools free of hidden labels, accidental answer leakage, shell interpolation hazards, and historical message contamination?
8. Does a pilot run show that the task is neither trivially solvable in every condition nor impossible under the intended condition?
9. Has an independent reviewer checked task realism, gold-policy defensibility, and evaluator evidence before it enters the confirmatory set?
10. If approval appears in the gold policy, does the agent-visible task require it or only conditionally trigger it? Are pending and denied branches scored consistently?

Pilot tasks may be revised. Freeze task/evaluator versions before confirmatory collection; report pilot and confirmatory tasks separately.

## 7. Study-level sampling, analyses, and paper outputs

- Preserve the proposal’s primary R0/R1 comparison. R2 structured profiles are outside the current Study 2.1 design and should only be added through a proposal/spec revision. Compare the same fixed model configurations on the same task templates and conditions. Model claims apply to tested configurations only.
- Reuse current Study 2 templates only in the must-ask stratum. Add independent no-help and optional-benefit workflow templates. The proposal’s “30 templates” is a planning target, not a power guarantee; use pilot task-level variance and interval precision/cluster-aware power analysis to lock the count. At least three within-template runs/seeds can be an initial pilot target, not a substitute for enough templates.
- Treat template as the sampling/cluster unit; profile/alignment variants and repeated model calls are within-template observations. Pair and randomize condition order, candidate order, and seeds. Report every denominator and failed/retried call.
- Primary figures: (1) help initiation by need stratum × model × R0/R1; (2) R1−R0 contrasts for under-help in must-ask and over-help in no-help, with template-clustered intervals; (3) optional-task quality vs. contact/token/latency outcomes without causal wording unless access/contact is randomized; (4) event-path/error breakdown and representative traces.
- Likely conclusion patterns must be treated as alternatives, not predicted findings: role information may reduce under-help and leave over-help unchanged; improve target choice but not the ask/no-ask decision; reduce under-help while increasing over-help; have model-specific effects; or show little effect. Optional-task contact/quality associations are descriptive unless experimentally manipulated.

## 8. Link to the local AgentCompany run

`research/agentcompany_single_run/outputs/episode_010/` is an engineering validation of one **must-ask + approval** workflow: the task completed and all four evaluator checks passed. It demonstrates that a controlled contact tool, NPC reply, trace capture, and deterministic checkpoint evaluation can work end to end. It is not yet a Study 2.1 calibration dataset: it has one workflow, one model configuration, no optional/no-help strata, and simulated NPCs. Its failure history also revealed concrete acceptance tests for future tasks: fresh-episode message filtering, current-run-only evaluator evidence, robust NPC startup, safe literal dollar handling, and checking every required artifact field.

