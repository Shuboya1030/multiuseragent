# Study 1: Help-seeking and human-contact behavior taxonomy (v1)

Date: 2026-10-24  
Status: operational draft informed by a task-instruction audit and a first pass over archived TAC traces. This is not yet a validated annotation instrument or a final result.

## Why the taxonomy must separate help-seeking from contact

TheAgentCompany tasks often explicitly tell the agent to contact coworkers. A message asking employees for vacation plans, collecting interview feedback, or scheduling a meeting is observable human contact, but it does not by itself show that the agent recognized uncertainty and autonomously asked for help. Study 1 should therefore distinguish **what the agent did** from **why the task called for it**.

Task-instruction audit of 40 TAC NPC-related tasks:

- 32 explicitly direct the agent to contact one or more people as part of task completion (including tasks with a conditional follow-up or approval gate).
- 6 make contact conditional on a specified event or need (for example ambiguity, invalid data, an access blocker, or a scan result).
- 2 do not specify an interpersonal help request.

This count is based on task instructions only. The row-level evidence and caveats are in `tac_task_help_behavior_audit_v1.csv`. All labels are single-analyst and still need scenario/evaluator cross-checking.

## Coding units

1. **Task-level contact/help opportunity:** a task instruction or observable task state supports a human interaction. Record whether contact is mandated, conditional, optional, or absent, plus the evidence.
2. **Message event:** one message the agent submits to a person or group. Preserve the text, recipient, task, model, event index, and subsequent transcript evidence.
3. **Help episode:** one or more related messages responding to the same information gap, ambiguity, blocker, decision need, or coordination dependency, through reply use or episode termination.

Do not infer an internal uncertainty state from a question alone. The agent’s stated rationale may be recorded as evidence, but it is not a substitute for task-state evidence.

## Orthogonal coding dimensions

| Dimension | Values / categories | Rule |
|---|---|---|
| **Task relation** | `task_mandated_contact`; `conditional_contact`; `agent_discretionary_contact`; `no_contact_instruction`; `unclear` | Read task.md and scenario context. This is not a message-function label. |
| **Help-seeking relation** | `instrumental_input_seeking`; `clarification_or_verification`; `advice_or_expertise`; `authority_or_approval`; `unblocking_or_access`; `status_inquiry`; `coordination`; `task-directed data collection`; `feedback/survey`; `notification/delivery`; `not_help_seeking`; `unclear` | A message may have multiple functions. Mark “task-directed” separately from whether the message requests information. |
| **Trigger** | `missing_fact`; `underspecified_instruction`; `conflicting_or_false_premise`; `execution_blocker`; `permission_or_authority`; `external_status_dependency`; `availability_dependency`; `user-mandated collection`; `no evidenced trigger`; `unclear` | Use prompt, environment, and trajectory. Do not map every request for information to uncertainty. |
| **When** | `before_independent_attempt`; `after_failed_attempt`; `after_partial_attempt`; `follow_up_after_reply`; `no observed ask`; `not observable` | Only code when an opportunity and task timeline are supported by evidence. |
| **Recipient selection** | `named_by_prompt`; `role_lookup`; `selected_from_known_roster`; `discovered_from_environment`; `group_broadcast`; `unverifiable` | Candidate/roster presence is not proof of appropriateness. Maintain a separate acceptable-recipient evidence field. |
| **Message quality** | `targeted`; `partly_targeted`; `broad`; `redundant`; `irrelevant_or_non-substantive`; `unclear` | Evaluate against the evidenced information gap and intended recipient. |
| **Response and uptake** | response `useful_complete`, `useful_partial`, `nonresponsive`, `incorrect_or_conflicting`, `no_reply`, `unobservable`; uptake `used_correctly`, `used_partly`, `ignored`, `misused`, `unobservable` | Do not infer uptake merely because the task score improved. Trace evidence must show the information and subsequent use. |

## Message-function categories for first-pass screening

The current extractor assigns a transparent lexical **candidate** label; annotators must adjudicate it in context.

- **Information/input request:** asks for a fact, file location, preference, quantity, requirements, or other task input.
- **Clarification/verification:** resolves ambiguity or checks a premise/answer.
- **Advice/expertise/decision:** asks for judgment or recommendation.
- **Status inquiry:** asks about task, issue, or work progress.
- **Coordination/availability:** schedules or checks willingness/availability.
- **Feedback/evaluation:** asks for opinion, rating, or performance feedback.
- **Authority/action request:** asks someone to approve or perform an action.
- **Information delivery/notification:** tells someone a result or provides an artifact/location.
- **Short/name-only or unclear message:** retain for review; do not automatically call it help-seeking.
- **Other/unclear:** retain original text and adjudicate.

The labels intentionally allow a directed survey question to be coded as `feedback/evaluation` while its task relation remains `task_mandated_contact`. Those are different analytic facts.

## First-pass TAC trace screen (not inferential findings)

From 400 archived task-model traces, the rule-assisted parser identified 656 Enter-submitted Rocket.Chat text candidates. In 457 cases the message body appeared after the sender and timestamp marker in the immediately following rendered chat observation; the remaining 199 are retained as unconfirmed submissions and are not counted as confirmed messages. Confirmed events span all 10 configurations and 186 task-model episodes.

Of the 457 transcript-confirmed messages, 387 occurred in tasks whose prompts explicitly required contact, 61 in tasks with a conditional contact instruction, and 9 in two tasks without an explicit interpersonal help request. These are message-event counts clustered in repeated task-model runs; they are not independent observations or help-seeking rates.

Candidate function counts among the 457 transcript-confirmed messages:

| Candidate function | Messages |
|---|---:|
| Information/input request | 264 |
| Coordination/availability | 58 |
| Feedback/evaluation | 38 |
| Status inquiry | 22 |
| Information/task-result delivery | 30 |
| Advice/expertise request | 11 |
| Acknowledgment/action commitment | 15 |
| Approval/action request | 8 |
| Name-only or unclear | 4 |
| Answer/data response | 2 |
| Short reply or unclear | 1 |
| Other/unclear | 4 |

These counts are raw event totals across tasks and models. They are not rates, model rankings, nor counts of autonomous help-seeking. Repeated messages within one task-model run are included. The event CSV is `tac_contact_events_screening_v1.csv`; all 656 candidates remain available with a transcript-confirmation flag. All function labels are still lexical screening labels and need contextual adjudication. This revised lexical pass maps obvious notifications, task-result delivery, commitments, and short replies more explicitly than the initial broad `other` bucket.

### Multi-model descriptive summary

| Model configuration | Confirmed messages | Most frequent candidate functions (counts) |
|---|---:|---|
| gemini-1.5-pro | 33 | information/input 20; feedback/evaluation 5 |
| gemini-2.0-flash | 74 | information/input 49; coordination 10 |
| gpt-4o-2024-08-06 | 46 | information/input 26; coordination 5 |
| llama-3.1-405b | 53 | information/input 34; coordination 9 |
| llama-3.1-70b | 30 | information/input 14; coordination 7 |
| llama-3.3-70b | 65 | information/input 45; feedback/evaluation 9 |
| nova-pro-v1_0 | 8 | name-only/unclear 4; status inquiry 2 |
| qwen2-72b | 9 | information/input 7; advice/expertise 1; coordination 1 |
| qwen2.5-72b | 32 | information/input 20; coordination 5 |
| sonnet-20241022 | 107 | information/input 49; coordination 16 |

These are **message counts**, and total volume varies substantially by configuration. The complete model-by-function table also gives within-configuration proportions in `tac_message_function_by_model_v1.csv`. Neither table supports ranking help-seeking propensity: tasks, opportunities, action rates, and repeated messages differ, and this sample has no validated autonomous-help denominator.

### Extraction quality warning

The 457 transcript-confirmed messages recover most, but not all, recipient sets in the historical `traj/events.json` parser: 19 task-model episodes have at least one recipient-set discrepancy. Preliminary trace inspection found directory/message-search navigation among Enter actions in 3 episodes; in the other 16, the historical recipient was not paired with a transcript-confirmed message in the new extraction. These are diagnostic hypotheses only. The new message extractor and legacy recipient parser do not yet agree on those cases. Therefore this output is suitable for taxonomy development and targeted manual review, but **not yet for strict recipient correctness or final inferential comparisons**. Resolve the 19 discrepancies before freezing recipient-level outcomes.

## Cross-source and language scope

The trajectory labels are now being connected to a separate, literature- and industry-informed framework. That synthesis distinguishes **team structure** (macro context), **help/coordination episodes** (interaction purpose, trigger, recipient, timing, response and uptake), and **workflow control** (who delegates, approves, or owns the decision). It adapts the established HAT structural dimensions while adding episode types such as fact seeking, clarification, expertise consultation, approval, blocker removal, coordination, escalation, and notification. See `literature_industry_help_modes_synthesis_v1.md` for the source review and crosswalk from current TAC labels. This is a candidate integrated codebook; it still requires contextual annotation and revision.

The agreed Study 1 taxonomy can be applied to TAC, HiL-Bench, and AskBench traces, but each source must retain its own task relation and responder structure. HiL-Bench and AskBench use a generic human/user response rather than an organizational roster, so they can inform help timing, clarification, question quality, reply use, and outcome patterns; they cannot validate coworker recipient selection.

The current TAC sample is English-language. It supports a **multi-model / multi-configuration** comparison, not a multilingual comparison. If “Multilingual” means cross-language behavior literally, that is a different research question and requires non-English tasks and traces.

## Next annotation steps

1. Use the literature/industry synthesis to freeze a versioned integrated codebook, while keeping structural labels separate from episode labels.
2. Manually inspect the 19 recipient-set discrepancy episodes and reconcile the message-to-recipient parser.
3. Contextually adjudicate a stratified pilot of message events (including each task-relation type, episode mode, and model configuration); revise the codebook once.
4. Add task-level opportunity/trigger, recipient justification, reply quality and uptake evidence to the pilot; only then freeze eligible episodes.
5. Expand to the full TAC panel. Keep descriptive counts separate from rates; compare configurations on matched task-level opportunities and report uncertainty/sparse cells.
6. Generate and annotate HiL-Bench / AskBench trajectories only if cross-source trajectory patterns remain a claim in the paper; task records alone do not provide behavior traces.



