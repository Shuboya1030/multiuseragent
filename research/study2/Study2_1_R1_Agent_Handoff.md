# Study 2.1 R1 Agent Handoff

**Updated:** 2026-10-24  
**Purpose:** Give the delegated agent one operational entry point for the R1 pilot, the later confirmatory R1 block, required artifacts, and the remaining Study 2.1 work.

## Readiness decision

**Start with the R1 pilot; do not start confirmatory R1 yet.** The 60-template task set passes its static package checks (20 tasks in each of must-ask, optional-beneficial, and no-help; 182 evaluator fixtures; zero structural errors). The `approved_by` scoring contract has also been corrected: the prompt and current gold use one candidate-ID string, and the evaluator accepts a legacy one-element list.

The existing three-provider v4 and paced Moonshot v5 runs used the prior wrapper version. Their 36 episodes have been re-scored offline with evaluator v2, but that does not validate the regenerated v2 prompts end to end. Run the current 27-episode stratified R1 pilot first, inspect every task-class/model combination, and report the pilot for review. The taskset audit still lists independent content review and runtime/task acceptance as open. The numeric precision rule, provider/model settings, budget freeze, confirmatory manifest, and a confirmatory runner also need to be finalized before formal collection.

The pilot runner is explicitly **pilot-only**. Do not relabel its records as confirmatory or use it to launch the 180-episode formal R1 block.

## Canonical files to read

Read these in order; the plan is authoritative when details differ.

1. `research/study2/Study2_1_Model_HelpSeeking_Plan.md` — canonical study design. Read §1–§3, §6 (metric definitions), §7 (statistics), and Appendix A1–A6 (run counts, configuration, metadata, stop/go rules, and what each phase can support).
2. `research/study2/Study2_1_R1_Agent_Handoff.md` — this operational handoff and current go/no-go status.
3. `research/study2/study2_1_taskset/README.md` — taskset contents, R0/R1 definitions, and commands.
4. `research/study2/study2_1_taskset/Taskset_Audit_Report.md` — task provenance, static audit, scoring-contract correction, known limits, and open acceptance gates.
5. `research/study2/study2_1_taskset/Study2_1_Task_Design_Spec.md` — task authoring, gold-policy, NPC, evaluator, metadata, and acceptance criteria.
6. `research/study2/study2_1_taskset/multimodel_r1_pilot.py` — current R1 pilot runner only; read its header and CLI before running.
7. `research/study2/study2_1_taskset/instantiate_run.py`, `evaluate_episode.py`, `run_record_schema.json`, and `trace_schema.json` — per-run rendering, scoring and artifact contracts.
8. `research/study2/study2_1_taskset/posthoc_rescore_v2.py` and `pilot_runs/posthoc_evaluator_v2_summary.json` — how old pilot data were re-scored without changing raw outputs.

`research/study2/Study2_1_Model_HelpSeeking_Plan.md` and this handoff are the study-level instructions. The taskset code is an implementation aid and must not silently override the plan.

## R1 conditions and run counts

### Pilot now

Run the three selected provider configurations on the same nine R1 pilot tasks: three must-ask (all **separated**), three optional-beneficial, and three no-help. That is 9 episodes per provider, **27 total**. Pilot records remain separate from confirmatory data.

Use a new, uniquely named output folder so earlier pilot artifacts cannot be overwritten. Example from repository root:

```powershell
python research/study2/study2_1_taskset/multimodel_r1_pilot.py `
  --output research/study2/study2_1_taskset/pilot_runs/multimodel_r1_pilot_20261024_v6_evalv2 `
  --seed 20261024
```

The runner reads `OPENAI_API_KEY`, `MOONSHOT_API_KEY`, and `ANTHROPIC_API_KEY` from the process environment and must never write them to files. Moonshot requests are paced by the runner; retain its pacing setting and record any 429/retry events. If any task/API/format/evaluator defect appears, stop the affected pilot, preserve the failed run, fix it under a new version, and rerun with new run IDs.

### Formal R1 after the go/no-go gates

Once independent task review, evaluator and runtime acceptance, exact model IDs/settings, budget, randomization, exclusion/retry rules, and the numeric precision/extension rule are frozen in a confirmatory manifest:

- 60 base templates × 3 models × 1 initial R1 episode = **180 episodes**.
- Each model receives all 20 must-ask (separated), 20 optional-beneficial, and 20 no-help templates.
- The selected model IDs are OpenAI `gpt-5.4-mini`, Moonshot `kimi-k2.6`, and Anthropic `claude-haiku-5-5`; record the actual returned model ID per request and do not silently swap versions.
- The first formal pass is one run per model × template × condition. Additional repeats are allowed only if the predeclared precision rule triggers; no selective reruns based on model ranking or individual outcomes. The current plan caps this at three runs per cell, but the numeric precision threshold must be written before formal collection.
- The confirmatory R1 runner has not yet been implemented/frozen. `multimodel_r1_pilot.py` writes `run_type=pilot` and is not that runner.

R1 alone supports comparisons among these three tested model configurations under enhanced role information and descriptive/associational RQ2.1c analyses. R1 alone cannot estimate the role-information effect R1−R0 or support a causal claim that asking improves performance.

## Required outputs for every episode

Use one immutable run directory and unique `run_id` per episode. Preserve failures and retries; do not overwrite prior records. At minimum, each episode must have:

- run manifest/metadata conforming to `study2_1_run_metadata_schema.json` (provider, requested and returned model IDs, `profile_condition=R1`, task/template/version, `alignment=separated` only for must-ask, seed, replicate, prompt/tool/evaluator hashes, sampling config, API request IDs, retries/errors, token usage, latency, cost or `unavailable`, status, and artifact references);
- the exact model-visible instantiated task and candidate profiles, plus a separate evaluator-only identity mapping;
- append-only normalized `trace_events.jsonl`, preserving each agent contact, NPC reply, tool action, submission, error, and run ID;
- final `answer.json`, evaluator output with checkpoint vector and evidence, raw provider turn/request-response log with secrets removed;
- a `runs.jsonl` row and batch design/config snapshot; after collection, summary tables by model × task class and a manifest with file hashes.

Never include API keys, authorization headers, or secrets in artifacts or Git. A failed API call remains a recorded failed episode. If retried, create a new run ID and link it using `retry_of`/`supersedes`.

## R1 metrics and reports

Use the definitions in the canonical plan §6; do not reduce the study to help count alone. Report denominators and missingness per model and class. The R1 result table should include:

- **Must-ask:** any/effective help, under-help, first recipient validity, first-step/path validity, required fact in reply, authorized approval in reply, invalid/unauthorized contact attempts, task completion and checkpoint scores.
- **No-help:** over-help/contact rate, contact count, exact artifact/task success, and whether unnecessary contact coincided with cost or errors.
- **Optional-beneficial:** contact rate, whether the reply was received and used per the frozen evaluator, objective quality points, baseline task completion, contacts, tokens, and latency. Treat self-selected contact–quality relations as descriptive, not causal.
- **Across classes:** contacts per episode, timing/first action, duplicate/ineffective inquiries, task success, permission compliance, model tokens (input/output/cached), latency, API failures, and cost where the provider supplies enough information.

The core R1 outputs are (1) a model × need-class behavior/calibration table with uncertainty intervals; (2) a plot of help initiation and under-/over-help by model and class; (3) a first-contact/path error breakdown; and (4) task outcome and token/latency summaries. These are pilot diagnostics until the confirmatory set and analysis protocol are frozen.

For uncertainty, use the **template** as the independent/cluster unit, not message events or repeated episodes. R1 results do not establish R1−R0 improvement; do not call one model generally “more helpful” outside the tested model versions and task conditions.

## What to do after R1

1. **Pilot first:** run 27 R1 pilot episodes, inspect all traces, and write a pilot report against the plan’s A2 pass criteria. Stop for API mismatch, repeated parser errors, cross-run contamination, NPC leaks, score defects, or unaudited ambiguous tasks.
2. **Freeze:** complete independent review of task class/gold paths and optional scoring; lock model IDs, prompt/tool/runtime/evaluator hashes, budgets, run order, exclusions/retries, primary metrics, multiple-comparison policy, and numeric precision/maximum-repeat rules in a versioned confirmatory manifest.
3. **Implement formal runner:** validate metadata and file hashes on each run, create immutable episode directories, save failed runs, and produce resumable block-level progress. It must not auto-select recipients or complete agent actions.
4. **Formal R1:** run 180 episodes, 60 per model. At block end, freeze and hash the R1 data snapshot; perform only preregistered quality checks before interpreting outcomes.
5. **Paired R0:** run the same templates/model matrix with matched instance seeds and identity/order mapping. R0 is synthetic name + generic title; R1 keeps the same name/title and adds general role information.
6. **Precision extension and analysis:** apply the frozen rule uniformly to models/templates/conditions; then run template-clustered analysis, generate paper-ready figures/tables and a reproducible analysis manifest. Report effects and intervals, not only p-values.
7. **Writing:** update the paper with task construction, model/version/date, API and NPC details, run failures/retries, evaluator, metrics, uncertainty, limitations, and artifacts. Keep pilot and confirmatory results clearly separated.

## Skills to use

The delegated agent should have these three Codex skills enabled to match the current research workflow:

| Skill | When to use |
|---|---|
| `experimental-design` | Before freezing conditions, seeds, controls, and the precision/repeat rule. |
| `statistical-experimental-evaluation` | When translating the hypotheses and design into preregistered comparisons, baselines/diagnostics, and analysis decisions. |
| `results-analysis` | After data collection, for the strict statistical analysis, interval estimates, diagnostics, and paper-quality figures. |

These skills are already present in the current Codex skill catalog. If the other agent runs under the same Codex profile, first check that these exact skill names appear in its skill list; no separate installation should be needed. If absent, install/enable those skills before analytical work. Do not install unrelated academic-writing or literature-search skills for the R1 execution task.

## Repository and artifact handling

The canonical project repository is `https://github.com/Shuboya1030/partimephd`. Pull the latest default branch before work; after review, commit and push the handoff, taskset source, evaluator/generator/validator, 60 task packages, and compact score audits. Keep API keys out of the repository. Pilot traces and full model request/response logs should be stored only if the repository’s data/privacy policy permits; otherwise keep them in the agreed private artifact location and commit their manifest/hashes and summary. The taskset audit currently flags source licensing for external redistribution, so confirm the repository visibility/licensing status before making the generated task packages public.
