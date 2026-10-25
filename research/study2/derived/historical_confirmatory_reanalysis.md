# Historical Study 2 confirmatory reanalysis

- Historical raw confirmatory rows: 212; unique planned cells: 168; extra duplicate attempts retained: 44.
- `first_appended` is the historical planned-cell analysis; `mean_all_retained_attempts` checks whether all duplicate attempts change the estimate. Raw traces remain in the source files.
- Outcomes were recomputed from event traces. The first-information-step outcome requires an information request to an admissible knowledge holder; legacy first_valid may accept approval-first behavior.
- Legacy first_valid disagrees with strict first-step validity in 0 of 168 first-appended cells.
- Historical R1/R2 contrasts are not format-only comparisons: v0.3 structured profiles omit organization-domain facts present in prose profiles. Do not use historical R2−R1 to claim a pure structured-format effect.
- Cluster bootstrap and Monte Carlo sign-flip summaries use 14 workflow-template clusters; uncertainty is coarse and p-values descriptive.

## Historical R1−R0 estimates (first appended record)

- gpt-6-luna, strict_first_information_step_valid: +0.786 (95% cluster bootstrap CI +0.571 to +1.000).
- gpt-5.6-terra, strict_first_information_step_valid: +0.786 (95% cluster bootstrap CI +0.571 to +1.000).
- gpt-6-luna, first_target_matches_request_purpose: +0.786 (95% cluster bootstrap CI +0.571 to +1.000).
- gpt-5.6-terra, first_target_matches_request_purpose: +0.786 (95% cluster bootstrap CI +0.571 to +1.000).
- gpt-6-luna, valid_path_recomputed: +0.107 (95% cluster bootstrap CI +0.000 to +0.214).
- gpt-5.6-terra, valid_path_recomputed: +0.000 (95% cluster bootstrap CI +0.000 to +0.000).
- gpt-6-luna, task_score_recomputed: +0.107 (95% cluster bootstrap CI +0.000 to +0.214).
- gpt-5.6-terra, task_score_recomputed: +0.000 (95% cluster bootstrap CI +0.000 to +0.000).
- gpt-6-luna, reward_recomputed: +0.613 (95% cluster bootstrap CI +0.422 to +0.830).
- gpt-5.6-terra, reward_recomputed: +0.382 (95% cluster bootstrap CI +0.276 to +0.487).
- gpt-6-luna, total_query_cost_recomputed: -3.786 (95% cluster bootstrap CI -4.571 to -2.964).
- gpt-5.6-terra, total_query_cost_recomputed: -2.857 (95% cluster bootstrap CI -3.571 to -2.107).
- gpt-6-luna, N_knowledge_miss: -1.857 (95% cluster bootstrap CI -2.357 to -1.321).
- gpt-5.6-terra, N_knowledge_miss: -1.643 (95% cluster bootstrap CI -2.143 to -1.107).
- gpt-6-luna, N_auth_recomputed: -1.571 (95% cluster bootstrap CI -2.000 to -1.143).
- gpt-5.6-terra, N_auth_recomputed: -1.214 (95% cluster bootstrap CI -1.643 to -0.786).
- gpt-6-luna, N_premature_approval: +0.000 (95% cluster bootstrap CI +0.000 to +0.000).
- gpt-5.6-terra, N_premature_approval: +0.000 (95% cluster bootstrap CI +0.000 to +0.000).
- gpt-6-luna, N_repeat_requests: -0.429 (95% cluster bootstrap CI -0.786 to -0.143).
- gpt-5.6-terra, N_repeat_requests: +0.000 (95% cluster bootstrap CI +0.000 to +0.000).
- gpt-6-luna, N_unhelpful_recomputed: -2.321 (95% cluster bootstrap CI -2.893 to -1.679).
- gpt-5.6-terra, N_unhelpful_recomputed: -1.643 (95% cluster bootstrap CI -2.143 to -1.107).

## Duplicate-cell sensitivity for reward R1−R0

- gpt-5.6-terra: first appended +0.382; per-cell mean across every retained attempt +0.378.
- gpt-6-luna: first appended +0.613; per-cell mean across every retained attempt +0.638.

Full estimates and duplicate sensitivity are in `historical_confirmatory_contrasts.csv`.
