# Study 1 data dictionary

## Files

- `episode_level.csv`: one row per task × model (390 rows); recipient lists omitted for easier analysis.
- `episode_level.json`: same rows with full scenario targets, parsed send sequence, and unique contacts.
- `task_policy_codebook.csv`: single-researcher prompt/scenario review for all 40 task folders.
- `model_summary.csv`: per-model coverage, score, completion and parsing-flag summaries.
- `contact_outcome_summary.csv`: descriptive normalized score and exact completion by any listed contact.
- `coverage_pairwise_holm.csv`: 45 paired model comparisons with raw and Holm-adjusted p-values.
- `metrics.json`: machine-readable statistical results.
- `run_manifest.json`: environment, data source, run date, file hashes.
- `figures/model_coverage.svg`: descriptive coverage plot.

## Row-level fields

| Field | Meaning |
|---|---|
| `model` | OpenHands model configuration label from the archived run. |
| `task` | TheAgentCompany task identifier. |
| `targets` | NPC names present as keys in the task's `scenarios.json`; not guaranteed required contacts. |
| `sent` | Parsed recipient name for each observed Enter-submitted chat action, preserving repeats. |
| `contacted` | Unique recipients in `sent`. |
| `n_sent_actions` | Count of parsed send actions with detected active room context. |
| `steps` | Number of trace events. |
| `finished` | Whether a finish action appears in the trace. |
| `fabricated` | Heuristic flag for selected simulation/placeholder language; not manually adjudicated. |
| `reached_chat` | Whether any trace observation URL matches Rocket.Chat direct/channel/group. Not a UI failure label. |
| `score`, `raw_score`, `score_total` | Evaluator normalized score and numerator/denominator. |
| `success` | Exact evaluator completion (`raw_score == score_total`). |
| `n_target` | Number of scenario-roster people. |
| `n_contacted_target` | Unique contacted people also listed in the scenario roster. |
| `n_outside_scenario` | Unique contacted people not listed in the scenario roster. |
| `n_uncalled_scenario` | Scenario-roster people not observed in the contacted set. Not a missed-required count. |
| `scenario_coverage` | `n_contacted_target / n_target`; roster proxy. |
| `any_scenario_contact` | Whether at least one listed NPC was contacted. |
| `any_outside_scenario` | Whether any unlisted recipient was contacted. |
| `all_scenario_contacts` | Whether all scenario-roster people were contacted. Not a task-success criterion. |

## Parsing caveat

The browser trace parser infers an active direct-message recipient from rendered sidebar links mapped to the current `/direct/<id>` URL, with heading fallback. The parsed contact sets exactly match the legacy `traj/events.json` contact sets for all 390 analyzed rows. This verifies implementation consistency, not semantic accuracy against human annotation.
