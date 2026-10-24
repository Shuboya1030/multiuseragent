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
## 2026-10-24 update: behavior taxonomy and task-instruction audit

The initial scenario-roster coverage analysis is only a coarse contact proxy. A separate task-level review now distinguishes task-mandated contact from contact conditional on a task trigger: among 40 TAC NPC-related tasks, 32 explicitly require contact, 6 specify conditional contact, and 2 do not specify interpersonal help. This means the existing traces can support a taxonomy and analysis of how model configurations carry out prescribed or condition-triggered interactions; they do not, by themselves, identify spontaneous uncertainty-driven help-seeking.

A rule-assisted message extraction pass over the 400 traces produced 656 Enter-submitted message-text candidates, of which 457 have the message body following an Admin sender/timestamp marker in the next rendered chat transcript. The lexical screen now separates information/input requests, coordination, feedback, status, task-result delivery, advice, acknowledgments/commitments, action/approval, short replies, and unclear messages. Labels are not yet manually adjudicated, and raw counts are not inferential rates. The event-level data, task audit, taxonomy, and 19-case recipient reconciliation queue are in this directory.

Before testing model differences or process/outcome associations, manually reconcile the recipient extractor against the raw traces, contextually adjudicate the message-function pilot, and confirm task-specific help opportunities and acceptable recipient evidence. The new extraction has 19 recipient-set discrepancies with the legacy recipient parser (3 have search/navigation among Enter actions; 16 have no transcript-confirmed message matched in the new screen). Task evaluator scores do not validate recipient appropriateness.

The three-source taxonomy can include TAC, HiL-Bench, and AskBench trajectories, but the latter two have generic human/user responders and do not measure organizational recipient selection. The present sample is English-only; it supports a multi-model comparison, not multilingual behavior claims.
