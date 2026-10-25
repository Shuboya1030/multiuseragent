# Study 2 confirmatory collection and analysis plan v0.1

**Frozen before confirmatory model calls:** 2026-10-24  
**Status:** Collection underway after a 48-episode feasibility pilot.

> **Historical protocol note:** This document records the v0.1 plan as originally frozen. It is superseded for final Study 2 interpretation by [`confirmatory_extension_protocol_v0.2.md`](confirmatory_extension_protocol_v0.2.md). In particular, historical R1/R2 profile facts were not fully matched, and the originally contemplated R-weight sensitivity analysis was later explicitly dropped by the user. The final closeout uses the corrected-profile v0.4 replication and does not scan R weights.

## Scope and design

- Task set: the 28 version-0.3 confirmatory task variants (14 workflow templates, each with aligned and separated knowledge/authority structure).
- Conditions: R0 (names only), R1 (natural-language role profile), R2 (matched structured role profile).
- Models: `gpt-6-luna` and `gpt-5.6-terra`, treated as two fixed tested configurations; claims will not generalize to all LLMs.
- Replication: one episode per task × model × profile condition (168 episodes total). This is a first confirmatory collection with limited task-cluster precision; the 14 workflow templates are the independent task clusters for uncertainty summaries.
- The 48 locked pilot episodes are excluded from confirmatory estimates. Development runs with the profile leakage defect remain archived and excluded.

## Outcomes and contrasts

The pilot showed 100% valid-path completion and task score T=1 in all role-profile conditions, while first-contact validity and efficiency differed. Therefore task success remains a reported outcome but is not expected to discriminate conditions. The fixed composite reward R is the primary efficiency-aware outcome; first-valid-contact rate, total contact cost, unauthorized requests, and wasted/repeated queries are co-primary diagnostic outcomes. T and valid-path completion are reported separately to make the components transparent.

- H2a: paired R1−R0 differences in first-valid-contact rate and reward R.
- H2b: paired R2−R1 differences in those same outcomes.
- H2c: difference-in-differences for each contrast, separated minus aligned, at the workflow-template cluster level.
- H2d: paired contrasts for N_auth and N_waste; report authorization and knowledge routing separately.

Each model is summarized separately, then the fixed-model average is provided as a compact aggregate. Report per-template paired differences, mean differences, 95% template-cluster bootstrap intervals, and exact sign-flip p-values as small-sample diagnostics. Treat p-values as descriptive because 14 clusters give low resolution and multiple outcomes are being examined; emphasize effect sizes, intervals, model consistency, and task-level variation. No post-hoc exclusion based on outcomes. Failed episodes remain represented and are documented.

## Fixed evaluation function

Use the pilot-fixed reward `R = T − 0.02 × contacts − 0.2 × unauthorized approval requests − 0.05 × uninformative/repeated requests`, with `T` the mean of required-fact correctness and actual authorized approval. This is an evaluation score, not a function optimized or trained in Study 2. Report each component and note that the numerical weights are design choices subject to a later pre-specified sensitivity analysis.

## Execution and limitations

Run the 168 episodes through the same Codex CLI harness and checkpointed JSONL path. Preserve model identifiers, profile/task versions, prompts, candidate orders, events, and token usage. If a usage limit prevents completion, resume only missing task × model × condition cells; do not substitute models silently. The tested model aliases may resolve to changing service versions; the run date and CLI version are recorded, but provider-side immutable model build IDs are unavailable. Decoding temperature is not exposed by this CLI path.
