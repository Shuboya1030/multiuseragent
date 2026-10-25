# Study 2.1 Task Set v1 (Draft)

This directory contains **60 unique workflow-template packages** for the three Study 2.1 help-need strata. Each template has `task.md`, `metadata.json`, `gold_policy.json`, `scenarios.json`, `evaluator_spec.json`, and an `evaluator.py` entry point. Shared evaluator code and trace/run schemas live at this directory level.

| Stratum | Templates | Construction |
|---|---:|---|
| Must ask | 20 | 14 previously used Study 2 templates plus 6 selected independent extensions from the local v0.4 catalog. Aligned/separated role variants are stored within each template and count once. |
| Optional, potentially beneficial | 20 | New synthetic workflows with a possible task-relevant information benefit. |
| No help needed | 20 | New synthetic workflows whose requested computation/transformation has all source data visible. |

## Profile conditions

- **R0:** run-randomized synthetic name + generic job title. It does not disclose task-specific expertise, responsibility, or authority.
- **R1:** the same name/title plus general natural-language role, responsibilities, knowledge domain, and authority information.
- **R2:** not included in this Study 2.1 task set; the current plan compares R0 with R1 and does not manipulate structured-vs-natural-language profile format.

Pair R0/R1 runs using the same instantiation seed so each candidate keeps the same synthetic name and generic title. The role-to-alias assignment and display order are randomized independently of the candidate's hidden knowledge/authority.

## Important status

These are **development drafts**, not a frozen confirmatory benchmark. The validator checks package completeness, metadata, class counts, unique template IDs, class-specific gold fields, hidden-answer leakage, and evaluator behavior against positive and negative synthetic trace fixtures for every template.

The evaluator is executable against the documented answer JSON and normalized current-run event trace. Optional-benefit scoring uses an explicit keyword-coverage proxy for reply use; that proxy needs validation against human judgments in pilot. The evaluator is not yet wired into the AgentCompany episode runtime. Static fixtures do not establish ecological validity, NPC runtime consistency, realistic model difficulty, or causal benefit of asking. Do not use these drafts to report experimental findings until all remaining gates in `Taskset_Audit_Report.md` and `Study2_1_Task_Design_Spec.md` pass.

The task prompts do not state the hidden help-need class or prescribe a contact sequence. The corrected release-readiness pilot likewise treats engineering validation as the required help step and Finance approval as conditional on choosing an approved status or announcing the release; see `../study2_1_pilot_tasks/s21-must-ask-release/`.

## Files

- `tasks/<task_id>/`: task package directories.
- `catalog.jsonl`: one catalog record per independent template.
- `generate_taskset.py`: deterministic local generator for the current 60 packages.
- `evaluate_episode.py`: shared deterministic evaluator for artifacts and normalized traces.
- `instantiate_run.py`: run-specific candidate identity/order permutation and R0/R1 profile rendering. Keep its `identity_mapping.json` hidden from the agent; pass it only to the evaluator.
- `validate_taskset.py`: structural and evaluator-fixture audit; run with `python validate_taskset.py`.
- `trace_schema.json` and `run_record_schema.json`: required event-trace and per-run metadata schemas.
- `Taskset_Audit_Report.md`: source audit, selected template lineage, known gaps, and next gates.

To regenerate after editing the source definitions:

```powershell
python research/study2/study2_1_taskset/generate_taskset.py
python research/study2/study2_1_taskset/validate_taskset.py
```

Create a model-visible run instance with a fresh randomization seed:

```powershell
python research/study2/study2_1_taskset/instantiate_run.py `
  --task-dir research/study2/study2_1_taskset/tasks/optional-customer-support-coverage `
  --output-dir outputs/run-001 --run-id run-001 --seed 101 --profile-condition R1
```

The runtime must inject `task.md` and `candidate_profiles.json` into the agent context, implement the documented send/read interface, and save normalized events matching `trace_schema.json`. The instantiator/evaluator do not yet launch or control AgentCompany by themselves.
