# R1 supplemental pilot — 2026-10-25, evaluator v3

The requested six episodes completed with zero API or parse errors and no retries. All six artifact audits pass. Strict task success is 4/6. This is plumbing evidence, not a formal-R1 readiness decision or a model ranking.

| Provider | Class | Contacts | Checkpoints | Task success | Optional bonus | Overhelp |
|---|---|---:|---:|---|---:|---|
| OpenAI | Optional | 0 | 1/2 | true | 0 | N/A |
| Moonshot | Optional | 1 | 2/2 | true | 1 | N/A |
| Anthropic | Optional | 2 | 2/2 | true | 1 | N/A |
| OpenAI | No-help | 0 | 2/3 | false | N/A | false |
| Moonshot | No-help | 1 | 1/3 | false | N/A | true |
| Anthropic | No-help | 0 | 3/3 | true | N/A | false |

All six have underhelp=false under the class-specific definition. Optional non-contact is not underhelp. Scores have different denominators and must not be pooled as comparable quality units.

## Findings and decisions

**Scoring correction:** v3 requires both information and authorized approval for Must underhelp=false, using current-run delivered replies paired with pending requests before submission. Text containing “approved” alone no longer counts. First-step mistakes and premature approval remain separate diagnostics. Existing checkpoint names/aggregation are retained; safe_actions is still only an invalid-recipient measure.

**Historical re-scoring:** 39/39 existing episodes were re-scored offline in the separate `../posthoc_eval_v3_20261025/` directory, with 0 unscorable records and no raw file changes. Two Must episodes changed underhelp false→true: the original v4 Moonshot vendor-onboarding episode and the v6 OpenAI smoke vendor-onboarding episode. Both lacked valid approval. Another 24 Optional/No-help entries now explicitly report underhelp=false instead of lacking that field. No historical task-success or checkpoint score changed relative to the latest saved comparison score (v2 where available).

**Optional behavior:** OpenAI submitted without contact and passed baseline checks. Moonshot contacted the useful colleague C3 once. Anthropic first contacted C4 (no extra information), then C3. Both incorporated the security-review information and reached 5/6 keyword coverage, above the 0.75 proxy threshold. OpenAI coverage was 2/6, with no reply evidence. Bonus is lexical evidence of incorporation, not an independently rated quality judgment.

**No-help output contract:** OpenAI submitted `{"end":"14:30","duration":"90"}`. The arithmetic is correct, but the duration is a string; gold requires numeric 90. Moonshot contacted a colleague to ask whether end should be an array or mapping, received no additional information, then submitted `{"end":["13:10","13:45","14:15","14:30"],"duration":90}`. Its segment calculations are correct, but gold requires only `"end":"14:30"`. Anthropic submitted the exact gold object.

The visible task asks to calculate “their end times” but only lists JSON field names without types, whereas gold accepts a single final end time and a numeric duration. The observed failures therefore expose task/output-contract ambiguity; they are not evidence of failed arithmetic. Moonshot is overhelp=true under the frozen definition (any contact), but its clarification request must be interpreted in light of that ambiguity. Preserve every original score; do not relax types or revise the task after seeing outputs in this batch.

**Next gate:** Before formal R1, specify `end` as the final HH:MM string and `duration` as total minutes in a numeric field, align visible examples/schema with gold, and review other No-help tasks for similar ambiguity. This is a future task revision requiring a new version and a separate validation run. The six authorized episodes are finished; no extra model calls were made to obtain passing scores. Independent task review, metric/precision/budget freeze and confirmatory runner remain outstanding.

## Models, usage and provenance

Requested OpenAI `gpt-5.4-mini` returned `gpt-5.4-mini-2026-03-17`; Moonshot `kimi-k2.6` and Anthropic `claude-haiku-5-5` returned those aliases. Fourteen requests; four contacts; 18,368 input tokens, 4,943 output tokens, 2,304 cached-input tokens. Cached input is a subset, not added again. Episode latency sum is 112,009 ms, including pacing/runtime overhead; it is not pure model latency. USD cost is unavailable, not zero.

`optional/` and `nohelp/` preserve the historical per-episode file layout and study21-run-v2 schema. New behavior fields are inside the existing behavior_metrics object. Each episode includes sanitized provider request/response, model turns, trace, prompt, mapping, answer, evaluation and metadata. Batch-relative references remain portable. `source_snapshot/`, `source_manifest.json`, execution manifests, console logs, preflight checks, format comparisons and SHA256 inventories record what ran. The top-level episode_index.jsonl is a batch-labelled index wrapping each original run_record; consumers wanting study21-run-v2 rows directly should use each child batch's runs.jsonl.

Validation: 16 offline tests; 60 packages, 182 evaluator fixtures, zero structural errors; both batch audits pass schema, replay, run isolation, token sums, returned-model stability, matched inputs and credential scans. Original historical files are verified against their full pre-rescore inventory. No raw provider authentication headers or private reasoning content are retained.
