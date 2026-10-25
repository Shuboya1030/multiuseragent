# Study 2 execution log

**Date:** 2026-10-24  
**Status:** Study 2 collection and closeout analysis complete.
**Inference status:** The final matched-profile estimates are reported in `derived/study2_v04_analysis.md`. Historical R1-vs-R2 is not a clean format test because old R2 profiles omitted an organization-domain fact present in R1. No R-weight sensitivity analysis was run, per user decision.

## Environment and task set

- Created 12 original synthetic scenario blueprints: six workflow templates × aligned/separated knowledge-authority structures. Four candidates per scenario; target identity rotates across templates.
- R0 gives neutral IDs. R1/R2 present the same role expertise, authority, and availability facts in prose vs. structured fields.
- The task environment uses deterministic colleague replies, requires information before approval, and records each decision/reply.
- Fixed evaluation weights are inherited from the earlier feasibility pilot: λ=0.02 per contact, μ=0.2 per unauthorized approval attempt, ν=0.05 per uninformative/repeated query. T is the mean of fact correctness and actual authorized approval. Oracle path uses two contacts, so R*=0.96. These are pilot settings; sensitivity analyses and final protocol lock remain required.

## Development smoke test v0.1 — excluded

- 12 runs (4 task variants × 3 profile conditions), one gpt-6-luna run per cell.
- 12/12 reached a valid task path; mean reward was R0=0.69, R1=0.96, R2=0.96; T=1.00 in every run.
- Review found a design defect: v0.1 profiles stated directly whether a person knew the details of the specific request. This exposed the gold routing target and caused a ceiling in task completion. The runs are retained in `archive/prepilot_direct_disclosure_v0.1/` as harness smoke-test records only. They are not evidence for H2a–H2d and are excluded from analysis.

## Corrective change

- Task blueprint version advanced to 0.2. Profiles now expose domain expertise and decision authority only; they do not state who has the specific request fact.
- R1/R2 keep those semantic facts matched. Task IDs and candidate identity counterbalancing remain fixed.
- The old outputs were moved intact to the pre-pilot archive; no run records were deleted.

## Current model access

- Claude Code reports authenticated, but noninteractive inference did not return after repeated waits, so no Claude output was recorded.
- A minimal Codex CLI inference succeeded using the logged-in account. The pilot runner is configured for model `gpt-6-luna`, Codex CLI 0.163.0-alpha.11.2, isolated empty working directory, ephemeral sessions, and read-only sandbox. CLI does not expose a sampling-temperature setting in this run path; this is recorded as a reproducibility limitation.

## Corrected profile audit and closeout plan — 2026-10-25

- Full trace audit checked all 260 historical episodes: each had corresponding events and all stored terminal scores/rewards matched a fresh replay. Eight deterministic evaluator boundary cases passed.
- The audit found 160 historical structured candidate profiles missing the organization-domain field included in prose profiles. Thus, historical R2−R1 cannot isolate representation format. Historical data are retained, but that contrast is labeled confounded.
- The original `first_valid` outcome counted an approval-first request to an authorized person as valid. New analyses use strict first information-step validity, reconstructed from the trace.
- Built 52 v0.4 blueprints: the 14 prior workflow templates (28 aligned/separated variants) with matched prose/structured semantics, plus 12 newly authored templates (24 variants). The latter are retained as an audited extension set, outside the Study 2 confirmatory closeout.
- A three-repetition 936-episode collection was started and interrupted after five records when its scale proved disproportionate to the original Study 2 scope. Those raw records remain intact and are excluded from primary estimates. The closeout replication is 14 templates × 2 fixed model configurations × 3 profile conditions × 1 episode = 168 planned cells; existing v0.4 runs were resumed where they matched this design. Of the 173 total v0.4 confirmatory-split records, 168 enter the primary set; five are preserved as pilot/excluded records (including one new-template record).
- The runner now records invocation/task/profile/prompt versions and enforces a single active writer. Fixed R remains a descriptive composite; no reward-weight sensitivity scan is planned.
- Protocol, analysis, outcome definition, cluster-based uncertainty, task/evaluator audit, duplicate handling, and figure outputs are being documented separately. Results remain bounded to a synthetic simulator and two fixed model configurations.

## Corrected-profile replication and final analysis — 2026-10-25

- Completed all 168 planned v0.4 replication episodes: 28 task variants (14 workflow templates × aligned/separated) × two fixed model configurations × three profile conditions. There were 163 completed episodes and 5 max-turn episodes; all remain in the analysis as observed outcomes. Candidate order was identical within every matched task/repetition block.
- The v0.4 profile/task audit flagged no semantic parity or gold-recipient leakage issues. The 8 deterministic evaluator boundary cases passed. Across all 433 historical, pilot, interrupted-batch and replication runs, every run had a trace and all recomputed outcomes matched saved terminal values.
- Historical confirmatory data remain 212 rows / 168 planned cells / 44 retained extra duplicate rows. Duplicate sensitivity compares the first appended row with cell means over all attempts; the old raw records were not edited.
- Main v0.4 estimates (template-cluster bootstrap, 14 clusters): R1−R0 strict first-information-step validity +0.732 (95% CI +0.518 to +0.929; Holm-adjusted p=.002 across six primary contrasts); valid-path completion +0.089 (95% CI 0.000 to +0.214); task score T +0.089 (same CI); fixed R +0.528 (95% CI +0.376 to +0.713); contacts/query cost −3.196 (95% CI −4.089 to −2.375); knowledge misses −1.518 and unauthorized approval attempts −1.411 per episode on average.
- Marginal condition rates across the 56 runs per condition: R0 valid-path completion 91.1%, strict first-step validity 26.8%, mean contacts 5.25, mean R=.425; R1: 100%, 100%, 2.05, R=.954; R2: 100%, 98.2%, 2.02, R=.959.
- R2−R1: no evidence of a useful structured-profile advantage in this sample (R difference +.005, 95% CI −.003 to +.017; strict first-step difference −.018, 95% CI −.054 to 0). The representations encode matched facts, but R2 text is about 8% longer than R1; interpret this as a structured-profile package contrast, not a length-controlled typography-only effect.
- No clear alignment moderation: R1−R0 separated-minus-aligned DID for R was −.022 (95% CI −.279 to +.235); task completion DID was −.036 (95% CI −.143 to +.071).
- Current interpretation: role facts substantially improve route quality and reduce wasted contacts/authority mistakes in this simulation; the task-success gain is smaller because R0 already succeeds in about 91% of runs. Structured presentation adds no demonstrated benefit over prose. This is evidence for the two tested fixed configurations and 14 synthetic templates only.
- Figures/tables and full estimates: `derived/study2_v04_analysis.md`, `study2_v04_contrasts.csv`, `study2_v04_alignment_interactions.csv`, `study2_v04_cell_summary.csv`, `study2_v04_main_effects.svg`, `study2_v04_error_effects.svg`; trace-level replay and evaluator audit: `derived/quality_audit.md`; historical corrected analysis and duplicate check: `derived/historical_confirmatory_reanalysis.md` and `historical_confirmatory_contrasts.csv`.

## Locked pilot and confirmatory collection — 2026-10-24

- Finished the corrected locked pilot for both fixed tested configurations, `gpt-6-luna` and `gpt-5.6-terra`: 24 episodes per model (8 task variants × 3 conditions). Both had 100% valid-path completion and T=1 across pilot cells. R0 reward averaged 0.56–0.67 by alignment/model, while R1/R2 reached 0.96; these are feasibility diagnostics only.
- Before confirmatory inference, froze `confirmatory_analysis_plan_v0.1.md`. Main set: 14 workflow templates × aligned/separated variants × 3 profile conditions × 2 fixed models = 168 planned episodes. Primary emphasis is fixed composite R and first-valid-contact; T/path success and all cost/error components are reported separately. R is an evaluation score, not a learned/optimized objective.
- Completed all 168 unique planned confirmatory cells. During collection, 44 extra rows were written for 44 planned cells (one duplicate per cell). Some duplicate timestamps are only fractions of a second apart, consistent with overlapping runner invocations; the runner did not record invocation IDs, so the source cannot be proven from the stored files. All source JSONL records and events remain intact. Primary analysis uses the first appended record per planned cell, with the deduplicated analysis data saved separately.
- First-pass paired task-template analysis: fixed-model average R1−R0 reward difference +0.498 (95% template-cluster bootstrap interval +0.374 to +0.638); first-valid-contact +0.786 (interval +0.571 to +1.000); unauthorized approval requests −1.393 and wasted/repeated contacts −1.982 per episode. Valid-path success difference was only +0.054 (interval 0.000 to +0.107), reflecting a high baseline. R2−R1 had no positive reward advantage on average (−0.0046; interval −0.0102 to 0.000). The aligned/separated interaction for the R1−R0 reward contrast was near zero (+0.011; interval −0.195 to +0.207).
- Interpret these as bounded results for two model aliases and 14 synthetic workflow templates, with one planned run per cell. Exact sign-flip p-values and cluster-bootstrap intervals are small-sample diagnostics, not a substitute for a larger independently replicated study. Model alias versions and decoding temperature are not provider-pinned/controlled in this CLI path.
- Files: `confirmatory_analysis_plan_v0.1.md`, `analyze_study2_confirmatory.py`, and `derived/confirmatory_{data_integrity.md,cell_summary.csv,paired_contrasts.csv,unique_runs.jsonl,unique_events.jsonl}`.
