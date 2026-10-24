# Study 1 analysis report

## Scope and conclusion

This is a retrospective trace diagnostic, not a causal evaluation of a help-seeking method. We reprocessed 400 raw trajectories and analyzed the balanced subset of 390 task-model episodes (39 tasks × 10 model configurations). We operationalize help-seeking only as contact with people listed in each task's `scenarios.json`; that list is a candidate/context roster, not verified ground truth for who was required or appropriate to contact. Therefore all contact rates below are **scenario-roster proxies**.

## Data and processing

Raw browser actions were parsed to detect chat-room context and Enter-submitted messages; evaluator outputs provide normalized checkpoint score (result/total) and exact completion. The analysis excludes the single task with no `scenarios.json` recipient roster (10 episodes). We verified the expected complete balanced panel and complete evaluator join. Parsed unique-recipient sets match the legacy event extraction exactly for all analyzed rows; this checks implementation consistency, not semantic correctness. A new row-level dataset preserves parsed recipient lists and sends. The parser has not received independent double annotation. A separate message-level screen that requires the submitted text to appear in the following chat transcript has since found 19 task-model recipient-set discrepancies against the legacy parser; 3 contain search/navigation among Enter actions and 16 lack a transcript-confirmed message matched to the legacy recipient. These cases are listed in `recipient_reconciliation_queue_v1.csv` and must be manually resolved before recipient-level conclusions.

Task policy audit: of the 40 task folders, 17 explicitly specify a fixed contact set/group, 15 involve conditional or choice-based contact, 6 require dynamic recipient discovery, 1 has no person-contact task, and 1 has a prompt/roster mismatch. These are first-pass single-researcher codes; see `task_policy_codebook.csv`.

The separate task-instruction audit classifies contact as explicit, conditional, or absent (32/6/2 tasks). A first-pass message taxonomy now screens 457 transcript-confirmed outgoing messages across all 10 configurations; its counts and per-configuration breakdown are descriptive only. See `help_seeking_behavior_taxonomy_v1.md`, `tac_contact_event_screening_v1.md`, and `tac_message_function_by_model_v1.csv`.

## Findings

- At least one roster-listed person was contacted in 163/390 episodes (41.8%; Wilson 95% CI 37.0%–46.7%). This is contact occurrence, not a correctness rate.
- Every scenario-listed person was contacted in 97/390 episodes (24.9%); this is **not** a required-contact completion rate because task rosters can include conditional/alternative contacts.
- An unlisted person was also contacted in 48/390 episodes (12.3%); this is a roster mismatch signal, not proof of an inappropriate recipient.
- Exact evaluator completion occurred in 33/390 episodes (8.5%; Wilson 95% CI 6.1%–11.6%).

| Model configuration | Mean roster coverage | Mean checkpoint score | Exact completions |
|---|---:|---:|---:|
| sonnet-20241022 | 0.709 | 0.512 | 13/39 |
| gemini-2.0-flash | 0.523 | 0.360 | 7/39 |
| llama-3.1-405b | 0.510 | 0.274 | 6/39 |
| llama-3.3-70b | 0.326 | 0.187 | 3/39 |
| gpt-4o-2024-08-06 | 0.270 | 0.224 | 0/39 |
| llama-3.1-70b | 0.265 | 0.131 | 1/39 |
| qwen2.5-72b | 0.237 | 0.191 | 2/39 |
| gemini-1.5-pro | 0.229 | 0.137 | 1/39 |
| qwen2-72b | 0.097 | 0.078 | 0/39 |
| nova-pro-v1_0 | 0.006 | 0.070 | 0/39 |

### H1a — Are help-seeking-related behaviors visible in failures?

**Answer: partially, as a descriptive signal only.** Episodes with at least one roster-listed contact had mean normalized score 0.397 (SD 0.346; exact completion 31/163, 19.0%); episodes with no roster-listed contact had mean score 0.087 (SD 0.171; exact completion 2/227, 0.9%). This descriptive split is strongly confounded by task difficulty and agent competence. Existing trace structure alone does not establish that every roster member was necessary, that an unlisted contact was wrong, or that non-contact caused a failure. Among the 357 non-complete episodes, 225 (63.0%) had no observed contact with a roster-listed person. This is a failure-associated trace pattern, not a verified missed-help event. Thus the stronger “fraction of failures caused by wrong/missed help-seeking” claim is **not identified by these data**.

### H1b — Do models differ in help-seeking behavior?

Mean scenario-roster coverage ranges from 0.006 to 0.709 across model configurations. A Friedman test on matched task-level coverage gives χ²(9)=91.41, p<0.001, Kendall's W=0.260. 16 of 45 Holm-corrected pairwise comparisons are significant (α=.05); details are in `coverage_pairwise_holm.csv`. This supports model heterogeneity in **roster coverage behavior** on this fixed task sample; it does not establish relative quality of recipient choice.

### H1c — Is contact coverage associated with task score?

In an exploratory OLS model with task and model fixed effects and standard errors clustered by task, a 0-to-1 increase in scenario-roster coverage is associated with a 0.379 change in normalized checkpoint score (95% CI 0.259 to 0.499; p<0.001; n=390, 39 task clusters). This is an observational association, not a causal effect; both score and contact behavior can be driven by task-specific difficulty or agent competence. Excluding tasks with 10+ roster members, the estimate is 0.378 (95% CI 0.257 to 0.500; p<0.001; 37 tasks).

## Study-level conclusion

Study 1 establishes a reproducible baseline showing that help-seeking traces and task outcomes can be measured, and that roster coverage varies across model-task runs. It does **not yet validate a benchmark of correct “who to ask” decisions**, nor demonstrate that help-seeking errors explain failures. The strongest defensible contribution is a diagnostic motivation study that identifies measurement and annotation needs for Study 2.

## Required follow-up before publication

1. Independently annotate a stratified sample of send actions, active recipient, whether the recipient was required/valid, whether a reply was received, and whether the agent used it; report inter-annotator agreement.
2. Code each task's recipient policy from its full task instructions and scenarios: mandatory named contacts, conditional/alternative contacts, information-discovery tasks, and ambiguous/non-help-seeking tasks. Re-estimate H1a on the verified subset.
3. Treat `reached_chat=False` as “no observed Rocket.Chat page in parsed trace,” not “UI-blocked.”
4. Avoid causal language for H1c; test causality only in a controlled rerun/intervention.
