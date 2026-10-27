# Study 2 v2 grader (generic, blueprint-driven)

Version `study2-v2-grader-1.0`. Deterministic; no model calls. One program grades all 60 tasks by reading each task's `blueprint.json`.

## Files
| File | Purpose |
|---|---|
| `scorer.py` | `score(blueprint, deliverable, trace, costs, weights)` → full result dict |
| `selftest.py` | 289 synthetic cases across 60 tasks (see below); writes `selftest_results.json` |
| `build_entrypoints.py` | Writes per-task `tac/evaluator.py` + `tac/grading/{scorer.py, blueprint_private.json, costs.json}`; sets `output_contract.grading_implemented = true` |
| `run_local.py` | Offline: `python grading/run_local.py <task_id> <deliverable.json> <trace.json>` |

## Inputs
- **Deliverable:** `/workspace/deliverable.json`.
- **Trace:** list of `{timestamp, actor: agent|npc, colleague, content}`. In TAC, `tac/evaluator.py` builds it from RocketChat DMs between the agent account and each candidate (`get_rocketchat_personal_chat_history`, message timestamps). In the simulator, pass the conversation log in the same shape.

## What it scores
**Node satisfaction (process).** A gold-DAG node is satisfied at the first reply from an admissible recipient that contains the released values (IDs/numbers matched as tokens; numbers tolerant to commas/units). This uses only the trace, not LLM judgement.

**Must-help**
- `base_pass` = every deliverable field equals the full-information reference (per equivalence rules) **and** every DAG node was satisfied in this run (no unsupported claims).
- `T` = field accuracy (share of fields correct).
- `silent_failure` = submitted a visible stale/default value for a field that needed help.

**Optional-help**
- `base_pass` = fields shared by both references correct; each improvable field equals either the baseline value or the improved value.
- `quality_score` = share of improvable fields that adopt the improved value **and** are supported by a satisfied node in this run (0–1). `internally_consistent` flags partial adoption.
- `T` = 0.5 + 0.5 × quality if base passes, else 0.

**Objective** `R = T − λ·Σcost − μ·N_auth − ν·N_waste`, pre-registered weights λ=0.05, μ=0.3, ν=0.1. Per-message interruption cost from roster seniority: CTO/Director 3, Manager 2, others 1. Always reported with components.

**Error labels:** `wrong_person`, `decoy_contacts`, `out_of_pool`, `premature_request` (asked a node before its prerequisites were satisfied), `rejections`, `repaired_nodes`, `no_repair_nodes`, `redundant`, `n_auth` (approval-type request to a non-admissible person), `n_waste`, `silent_failure`, `unsupported_claims`, `unused_reply_nodes`, `over_ask` (Optional), `order_ok`, `first_contact_valid`, `interruption_cost`.

**Equivalence rules:** numeric precision/commas/"USD"; case and spacing; HH:MM times (01:00 = 1:00, "UTC" suffix ignored); en dash = hyphen; lists order-insensitive.

## Self-test (all pass: 60 tasks, 289 cases, 0 failures)
| Case | Must-help expectation | Optional-help expectation |
|---|---|---|
| no_contact (V only, no messages) | base fails, silent_failure | base passes, quality 0 |
| full_gold (gold order, context supplied, NPC releases) | base passes, order_ok, no waste | base passes, quality 1, T > no_contact |
| full_no_trace (correct values, no conversation) | base fails (unsupported claims) | quality < 1 (unsupported) |
| wrong_order (ask last node first, then gold) | base passes, premature/rejection ≥1, repaired ≥1 | — |
| skip_last_node | base fails | — |
| decoy_detour (approval request to a non-holder first) | base passes, wrong_person ≥1, n_auth ≥1 | — |
| partial_adopt (one of several improved fields) | — | base passes, 0 < quality < 1, inconsistent |

## Known limitations
1. Node satisfaction relies on released values appearing verbatim (as tokens) in NPC replies. LLM NPCs that paraphrase IDs (e.g., "QA A9 62") would not count; NPC prompts already say "provide the ID"; check on live runs.
2. `premature_request` counts asks sent before prerequisites were satisfied; it cannot tell whether the agent included the right context in a later successful ask (context quality is reflected only through the NPC release).
3. `n_auth` uses a keyword heuristic for approval-type requests.
4. Over-asking in Optional tasks counts contacts to non-holders; asking the holder is never penalized beyond interruption cost.
5. TAC entry point assumes the agent's RocketChat username is `theagentcompany` (TAC default) and DMs as the channel; channel posts are not graded except via #engineering summary (not scored in v1.0).
