# Study 1: plan and execution record

## Objective

Use existing TheAgentCompany/OpenHands traces to test whether archived trajectories contain measurable interpersonal help-seeking behavior, whether this behavior differs across model configurations on matched tasks, and whether observed contact coverage is associated with task score. This is a retrospective diagnostic study, not a causal test of a new routing method.

## Analysis steps

1. **Inventory and lock sources.** Read the 400 compressed raw traces, 400 evaluator outputs, 40 task instructions, and scenario rosters. Preserve raw files. Record SHA-256 hashes of raw traces.
2. **Reconstruct trace events.** Parse chat page observations and browser Enter submissions; map the active direct-message URL to a displayed NPC username when possible. Keep send-event list, unique contacted set, whether a chat page was observed, finish marker, and heuristic fabrication flag.
3. **Establish the analysis panel.** Join by task and model to evaluator checkpoint results. Exclude the one task with an empty scenario roster for roster-coverage analysis; assert a complete 39-task × 10-model panel.
4. **Interpret task recipient policies.** Manually code all 40 task folders in `task_policy_codebook.csv` as fixed set/group, conditional/choice, dynamic discovery, roster mismatch, or non-person-contact task. The purpose is to expose why raw scenario membership cannot itself be ground truth. This pass is a single-researcher audit, not independent annotation.
5. **Define operational metrics.** Treat scenarios roster membership as a proxy: coverage = unique listed NPCs contacted / roster size; any listed contact; every listed contact; any unlisted contact. Use normalized evaluator checkpoint score and exact task completion as outcome measures.
6. **Describe H1a.** Report Wilson intervals for the overall rates and descriptive score/completion by whether any listed person was contacted. Do not call roster omissions or unlisted contacts errors without validated task-level gold labels.
7. **Test H1b.** Compare the 10 model configurations on the same 39 tasks using a tie-corrected Friedman test; report Kendall's W. Conduct all 45 paired Wilcoxon signed-rank comparisons and Holm-adjust p-values.
8. **Model H1c.** Fit OLS to normalized checkpoint score with scenario coverage, task fixed effects, and model fixed effects; use task-clustered sandwich SE with finite-sample correction. Repeat excluding tasks with roster size ≥10. Interpret as association only.
9. **Package and verify.** Save row-level episodes, model summaries, pairwise tests, figures, manifests, statistical appendix, limitations and this script. Compare parsed recipient sets to the legacy output; verify expected panel size.

## Hypotheses and decision rules

- **H1a (diagnostic):** trace behaviors related to contacting scenario-listed people are observable in task episodes. Test is descriptive; the stronger claim that help-seeking errors explain failure is not identifiable without recipient-validity labels.
- **H1b:** model configurations differ in scenario-roster coverage. Primary test: Friedman χ², α=.05; effect size Kendall's W. Pairwise follow-ups use two-sided Wilcoxon and Holm family-wise correction at α=.05.
- **H1c:** scenario-roster coverage is positively associated with normalized evaluator score conditional on task and model fixed effects. Exploratory, two-sided α=.05; no causal interpretation.

## Decision / inference limits

The statistical tests evaluate this fixed benchmark sample. Ten configurations may differ in provider, model generation, prompting, or infrastructure; thus “model effect” means observed configuration-level difference, not isolated architecture or scale. The recipient policy audit helps qualify the proxy but does not repair ground truth: the trace study requires a second annotator and event-level correctness rubric before it can claim wrong-recipient, missed-recipient, or follow-up error prevalence.
