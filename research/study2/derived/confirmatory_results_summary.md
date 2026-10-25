# Study 2 confirmatory collection: first-pass results

> **Historical first pass, superseded for final interpretation.** This summary is retained as the original analysis record. Subsequent trace audit found that legacy `first_valid` can count approval-first behavior as valid, and old R2 profiles omit organization-domain facts present in R1. See `historical_confirmatory_reanalysis.md` for corrected outcomes and `study2_v04_analysis.md` for the matched-profile replication. Historical R2−R1 is not a clean representation-format effect. No R-weight sensitivity analysis is part of the final plan.

**Analysis set:** 168 unique planned episodes, 14 task-template clusters, two fixed model configurations, three role-information conditions, aligned/separated variants. The source file contains 44 extra duplicate-cell rows; see `confirmatory_data_integrity.md`. The analysis retains the first appended record per planned cell and preserves all source rows.

## Main results

- **R1 versus R0:** Average fixed-model reward increased by **0.498** (95% template-cluster bootstrap interval **0.374 to 0.638**). The effect was positive for both tested model configurations: +0.382 for `gpt-5.6-terra` and +0.613 for `gpt-6-luna`.
- **How behavior changed:** R1 increased first-contact validity by **0.786** (interval **0.571 to 1.000**) and reduced unauthorized approval requests by **1.393** and wasted/repeated requests by **1.982** per episode, on average across the two models. The two models showed the same direction of change.
- **Task completion:** Valid-path completion was already high in R0 and increased by only **0.054** on average (interval **0.000 to 0.107**). In these tasks, the clearer role information mainly improved the route and reduced interaction cost/errors; it did not produce a comparably large task-success gain.
- **R2 versus R1:** There was no positive average reward advantage for the structured profile: **−0.0046** (interval **−0.0102 to 0.000**). This does not support a general claim that structuring the same profile facts helps. `gpt-6-luna` had a small negative mean; `gpt-5.6-terra` showed no reward difference.
- **Aligned versus separated:** The R1−R0 reward benefit did not clearly differ by knowledge/authority configuration; difference-in-differences was **+0.011** (interval **−0.195 to 0.207**). The current sample does not support the predicted moderation.

## Interpretation against the planned hypotheses

- H2a receives support in this controlled synthetic setting: natural-language role information improved valid first contact and efficiency-aware reward relative to names alone.
- H2b is not supported: the structured representation did not improve outcomes over semantically matched prose.
- H2c is not supported in this sample: role-information gains were not clearly larger when knowledge and authority were separated.
- H2d receives support for fewer unauthorized approval attempts and uninformative/repeated contacts. Interpret these counts within the simulator's explicit authority and reply rules.

These are first-pass estimates from two fixed model aliases on 14 synthetic workflow templates with one planned episode per cell. Cluster intervals and exact sign-flip p-values are diagnostic summaries with limited cluster resolution and multiple outcomes. The simulator's repeated, deterministic NPC replies, fixed cost weights, non-pinned provider model versions, unobserved CLI temperature, and duplicate-cell collection issue all limit generalization. Treat the results as evidence about this controlled benchmark, not enterprise deployment effectiveness.

Machine-readable outputs: `confirmatory_cell_summary.csv`, `confirmatory_paired_contrasts.csv`, `confirmatory_unique_runs.jsonl`, and `confirmatory_unique_events.jsonl`.
