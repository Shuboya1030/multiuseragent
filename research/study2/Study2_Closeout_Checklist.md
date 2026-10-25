# Study 2 closeout checklist

Study 2 closeout after the user confirmed that reward-weight sensitivity analysis is not needed. The separate Study 2.1 model-preference study remains out of scope until separately authorized.

## Final answer the study should support

Study 2 tests whether role information, and the way it is represented, changes an agent's end-to-end help-seeking behavior and task outcomes in a controlled workplace simulation. The main contrasts are R1−R0 (natural-language role facts vs. names only) and R2−R1 (matched structured vs. prose role facts), with aligned/separated knowledge-authority configurations as a moderator.

## Planned paper contents

1. **Motivation and questions:** why the agent needs both task knowledge and organizational authority to seek help effectively.
2. **Design and task set:** episode flow, aligned/separated cases, four-candidate profile examples, role-profile information parity, fixed prompts and model configurations.
3. **Hypotheses:** H2a role facts vs. names; H2b matched structure vs. prose; H2c interaction with aligned/separated configuration; H2d knowledge and authority failure mechanisms.
4. **Measures:** strict first information-step validity, full valid-path completion, task score T, direct request/cost/error components, with fixed composite R secondary and no weight scan.
5. **Results:** primary paired contrasts and confidence intervals over workflow-template clusters; model-stratified fixed-configuration estimates; alignment interactions; error-mechanism results; historical duplicate sensitivity; task-template replication vs. extension boundary.
6. **Limitations:** synthetic rules and NPC replies; fixed costs; small number of independent workflow templates; two fixed model aliases; non-pinned provider versions and unobserved decoding temperature; no real human response variance.

## Planned figures and tables

- Figure 1: episode pipeline and what R0/R1/R2 change.
- Figure 2: one aligned and one separated role-profile example; explicitly show semantic parity between R1 and R2.
- Figure 3: main paired effects with template-cluster bootstrap intervals (`derived/study2_v04_main_effects.svg`).
- Figure 4: changes in knowledge, authority, premature, repeated and unhelpful requests (`derived/study2_v04_error_effects.svg`).
- Table 1: task-template coverage and aligned/separated scenario counts.
- Table 2: condition/outcome definitions and the corrected strict first-step metric.
- Table 3: main effect estimates with intervals and Holm-adjusted primary tests (`derived/study2_v04_contrasts.csv`).
- Table 4: separated-minus-aligned difference-in-differences (`derived/study2_v04_alignment_interactions.csv`).
- Appendix: quality/evaluator checks, complete model-stratified estimates, profile lengths, duplicate sensitivity, and representative anonymized traces.

## Exit conditions

- [x] 168-cell corrected-profile replication completes with all expected task/model/condition cells.
- [x] All 433 runs have event traces; terminal outcomes reconcile with trace replay.
- [x] Eight deterministic evaluator boundary checks pass.
- [x] Historical duplicate rows are preserved and both first-record and all-attempt summaries are available.
- [x] Primary analysis and figures are generated from versioned raw data.
- [x] Manuscript-facing results distinguish historical confounded contrasts from the corrected-profile replication.
- [x] Study 2 limitations and external-validity boundaries are explicit.
- [x] Changes and artifacts are committed and pushed to the user's GitHub repository (commit `8b1df70`; final checklist sync follows).

Automated structural and evaluator checks do not replace a separate human review of scenario realism and profile plausibility. The analysis reports that limitation rather than claiming independent human validation.
