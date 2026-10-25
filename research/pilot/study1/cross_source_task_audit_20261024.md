# Study 1 task-level audit: cross-source inventory (2026-10-24)

## Scope and status
This audit compares task metadata and runner support across TheAgentCompany (TAC), HiL-Bench, and AskBench. It is a task-definition audit, not trajectory coding. Raw benchmark files were read transiently from official public repositories; they are not copied into this project.

The companion TAC inventory CSV includes a simple prompt-keyword flag only as a retrieval aid; it is not an adjudicated label or eligibility criterion.

## TAC
- 40 task definitions reviewed at first-pass level; policy classes: conditional_or_choice=15, dynamic_discovery=6, explicit_fixed_set_or_group=17, explicit_recipient_roster_mismatch=1, non_person_contact_task=1.
- Eligibility suggestions: candidate_when_whom_after_review:15; candidate_whom_after_review:6; communication_process_only:17; exclude_help_seeking:1; quarantine_until_resolved:1.
- TAC is the only source here with organizational named NPC contacts and historical multi-model traces, so only TAC can currently support the primary model-configuration comparison and process/outcome association. Strict missed-help/wrong-recipient scoring remains task-specific and requires verifying task prompt, scenario facts, initial state, and evaluator; roster membership alone is not a gold label.

## HiL-Bench
- 200 public task records; domain split: sql=100, swe=100.
- Blocker type counts (multi-label blocker instances, not tasks): ambiguous requirements=108; contradictory requirements=111; missing parameters=134; business info=118; question=188; schema=92 (751 tagged instances total). A task/blocker may carry multiple type tags.
- Subtype counts: confusing_column_or_column_definition,42; confusing_information,59; confusing_table_or_table_definition,50; contradicting_requirements,27; contradicts_real_life,25; missing_information,59; multiple_interpretations,26; requires_real_time_information,26; timeframe_ambiguity,27; unclear_value,29; underspecified_concepts,28.
- Blockers per task distribution: 3 blockers/task=96 tasks, 4 blockers/task=57 tasks, 5 blockers/task=47 tasks.
- Structured blocker registry includes descriptions, example questions and resolution criteria. Useful for help-opportunity/timing/question-targetedness analyses with the official human-help runner. The responder is generic; no team roster or recipient-choice ground truth exists. Task files are not completed agent traces; runner execution is needed.

## AskBench
- `ask_mind.jsonl`: 400 records; source_task counts: ask_mind_bbhde:100; ask_mind_gpqade:100; ask_mind_math500de:100; ask_mind_medqade:100; mean checklist points: 3.85.
- `ask_overconfidence.jsonl`: 400 records; source_task counts: ask_overconfidence_bbh:100; ask_overconfidence_gpqa:100; ask_overconfidence_math500:100; ask_overconfidence_medqa:100; mean checklist points: 2.25.
- AskMind `required_points` and AskOverconfidence `misleading_points` provide explicit answer/correction rubrics. This is single-user clarification/correction, not multi-person organizational help seeking. Use only for taxonomy transfer and pattern exemplars, not recipient choice or TAC H1/H2 inference.
- Task rows are not agent traces; fresh runs are required for event-level analysis.

## Decision for the planned Study 1
1. **Taxonomy/pattern contribution:** retain all three sources, but report each separately and distinguish observed traces from task definitions. Use TAC traces already available; run HiL-Bench and AskBench only with a concrete trace-collection and annotation plan.
2. **Primary H1 (model configuration and help behavior):** TAC paired task/model traces only; analyze tasks with independently verified opportunities. Named-recipient mandated tasks describe communication execution, not autonomous whom choice.
3. **Primary H2 (process quality and task outcome):** TAC only, and only for episodes with verified opportunity, available-help path, and evaluator linkage. Adjust/stratify for task and model; exclude or separately report checkpoints that directly reward contacting people.
4. **Cross-source limitation:** HiL-Bench and AskBench have structured clarification opportunities, but neither has multi-recipient/team role structure. They support construct breadth, not external validation of role-aware recipient selection.
5. **Immediate next work:** verify the 21 TAC candidate tasks against task.md, scenario facts, initial state, and evaluator; decide which have an observable help opportunity and independently supported acceptable paths; then freeze eligibility. Next, run a small trace-generation/coding pilot on HiL-Bench and AskBench if cross-source trajectory patterns remain a paper claim; pilot-code TAC traces in parallel. Revise the codebook once before full eligible TAC annotation.

## Evidence files
- TAC: `research/pilot/study1/task_policy_codebook.csv`, `study1_task_eligibility_v1.csv`.
- HiL-Bench and AskBench: source links and field descriptions in `11_Study1_Coding_Standard_and_Task_Audit_20261024.md`; no raw data vendored.


