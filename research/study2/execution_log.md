# Study 2 execution log

**Date:** 2026-10-24  
**Status:** Approved by user; execution underway.  
**Inference status:** No confirmatory results yet.

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

## Next execution stage

Run the eight `pilot_locked` task variants × three profile conditions (24 episodes, one model, one repetition) as a feasibility pilot. If the profile condition still produces a ceiling, revise only on the development split and freeze a new version before collecting further locked data. The pilot is too small (four matched workflow templates) to support final confirmatory inference; expand the task set and determine power before the main Study 2 collection.

## Locked pilot and confirmatory collection — 2026-10-24

- Finished the corrected locked pilot for both fixed tested configurations, `gpt-6-luna` and `gpt-5.6-terra`: 24 episodes per model (8 task variants × 3 conditions). Both had 100% valid-path completion and T=1 across pilot cells. R0 reward averaged 0.56–0.67 by alignment/model, while R1/R2 reached 0.96; these are feasibility diagnostics only.
- Before confirmatory inference, froze `confirmatory_analysis_plan_v0.1.md`. Main set: 14 workflow templates × aligned/separated variants × 3 profile conditions × 2 fixed models = 168 planned episodes. Primary emphasis is fixed composite R and first-valid-contact; T/path success and all cost/error components are reported separately. R is an evaluation score, not a learned/optimized objective.
- Completed all 168 unique planned confirmatory cells. During collection, 44 extra rows were written for 44 planned cells (one duplicate per cell). Some duplicate timestamps are only fractions of a second apart, consistent with overlapping runner invocations; the runner did not record invocation IDs, so the source cannot be proven from the stored files. All source JSONL records and events remain intact. Primary analysis uses the first appended record per planned cell, with the deduplicated analysis data saved separately.
- First-pass paired task-template analysis: fixed-model average R1−R0 reward difference +0.498 (95% template-cluster bootstrap interval +0.374 to +0.638); first-valid-contact +0.786 (interval +0.571 to +1.000); unauthorized approval requests −1.393 and wasted/repeated contacts −1.982 per episode. Valid-path success difference was only +0.054 (interval 0.000 to +0.107), reflecting a high baseline. R2−R1 had no positive reward advantage on average (−0.0046; interval −0.0102 to 0.000). The aligned/separated interaction for the R1−R0 reward contrast was near zero (+0.011; interval −0.195 to +0.207).
- Interpret these as bounded results for two model aliases and 14 synthetic workflow templates, with one planned run per cell. Exact sign-flip p-values and cluster-bootstrap intervals are small-sample diagnostics, not a substitute for a larger independently replicated study. Model alias versions and decoding temperature are not provider-pinned/controlled in this CLI path.
- Files: `confirmatory_analysis_plan_v0.1.md`, `analyze_study2_confirmatory.py`, and `derived/confirmatory_{data_integrity.md,cell_summary.csv,paired_contrasts.csv,unique_runs.jsonl,unique_events.jsonl}`.
