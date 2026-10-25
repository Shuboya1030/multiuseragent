# Moonshot R1 Pilot: Rate-Paced Rerun

Date: 2026-10-24 (America/Los_Angeles)  
Model: `kimi-k2.6`  
Condition: R1; three separated must-ask, three optional-beneficial, three no-help templates; one episode per template.  
Protocol: `study21-r1-pilot-v0.3`; Moonshot requests spaced by at least 21 seconds, with delayed retry on HTTP 429.

## Outcome

All nine templates were attempted. **No HTTP 429 occurred**, confirming that request pacing kept this batch below the observed 3-RPM limit. Eight runs completed their evaluator step in the original runtime. The remaining episode completed its model interaction but the evaluator subprocess could not print a Unicode character under the Windows cp1252 console encoding. It was re-evaluated offline with UTF-8; the original failed run record was preserved, and a separate `run_record_recovered.json` records the recovery.

| Task class | Episodes | Submitted answers | Post-hoc successes | Mean asks after recovery |
|---|---:|---:|---:|---:|
| Must-ask (separated) | 3 | 3 | 1 | 2.0 |
| Optional-beneficial | 3 | 3 | 3 | 2.0 |
| No-help | 3 | 3 | 3 | 0.0 |
| **Total** | **9** | **9** | **7** | — |

Must-ask post-hoc scoring normalizes a scalar `approved_by` to the singleton gold array before exact answer comparison. Only one of three must-ask episodes then satisfies the full task and process criteria; the other two contacted/used help but did not produce a fully valid result. These are pilot diagnostics, not confirmatory evidence.

Recorded usage recovered from each episode's model turns, including the evaluator-encoding case: **31,639 input tokens and 8,881 output tokens**. Dollar cost is unavailable because the run has no dated pricing snapshot. API request IDs, task traces, outputs, and original scores remain available in the episode folders.

## Artifacts and audit trail

- `pilot_design.json`: sample, model, protocol, and pacing configuration.
- `runs.jsonl`: original append-only run records, including the evaluator serialization failure.
- `posthoc_scoring_audit.json`: offline rescoring with answer-shape normalization; original evaluator outputs are not overwritten.
- `episodes/<run_id>/run_record_recovered.json`: recovered metadata for the one completed episode whose evaluator output failed to serialize.
- `episodes/<run_id>/evaluation_posthoc_singleton_normalized.json`: diagnostic scores; not frozen confirmatory scores.

## Gate status

The Moonshot API is usable at the observed 3-RPM organization limit when this runner applies 21-second request pacing. The pilot runner also now forces UTF-8 for evaluator subprocess output. Do not start formal collection until the answer schema/evaluator is frozen and the three-provider pilot gate is reviewed.
