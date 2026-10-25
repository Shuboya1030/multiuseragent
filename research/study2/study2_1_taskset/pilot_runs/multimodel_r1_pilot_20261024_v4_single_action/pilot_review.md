# Study 2.1 R1 Pilot Review

Date: 2026-10-24 (America/Los_Angeles)  
Protocol: 9 templates per provider, R1 only; three must-ask templates use separated; three optional-beneficial and three no-help templates use `not_applicable` alignment. One episode per template/provider.  
Models: `gpt-5.4-mini`, `kimi-k2.6`, `claude-haiku-5-5`.

## Outcome

The 27 planned episodes were attempted. This batch **does not pass the end-to-end pilot gate** and must not be treated as confirmatory evidence or used to start formal R1 collection.

| Provider | Episodes | Submissions | Evaluator task successes | Total asks | Input / output tokens | Main issue |
|---|---:|---:|---:|---:|---:|---|
| OpenAI | 9 | 8 | 5 | 5 | 17,930 / 1,246 | One invalid final response; must-ask scoring is affected by an answer-schema mismatch described below. |
| Moonshot | 9 | 0 | 0 | 2 | 2,706 / 791 | All nine runs ended with HTTP 429 rate-limit errors; provider reported organization maximum 3 RPM. |
| Anthropic | 9 | 8 | 6 | 12 | 64,195 / 7,715 | API/tool interaction worked; one must-ask run used all turns without submitting. Must-ask scoring has the same answer-schema issue. |
| **Total** | **27** | **16** | **11** | **19** | **84,831 / 9,752** | **10 logged errors: 9 Moonshot 429s and 1 OpenAI output-parse error.** |

Evaluator outcomes by task stratum were 0/9 must-ask, 6/9 optional-beneficial, and 5/9 no-help. These are descriptive diagnostics only. The must-ask success rate is not interpretable as model performance until the answer comparison is corrected; the Moonshot denominators include rate-limited runs.

## Run history and usage

- `multimodel_r1_pilot_20261024_v2`: 27 local attempts were blocked by sandbox DNS/network access before any API response; token usage was zero. Not counted as API pilot data.
- `multimodel_r1_pilot_20261024_v3_network`: 27 API attempts with the earlier tool-turn prompt; multi-action responses exposed an adapter/protocol issue. This diagnostic batch used 37,393 input and 6,407 output tokens. Its Moonshot/account identifiers and provider-returned private reasoning fields were redacted from local diagnostics.
- This v4 batch used 84,831 input and 9,752 output tokens. Across the two network-enabled diagnostic batches, recorded usage totals 122,224 input and 16,159 output tokens. Dollar cost remains unavailable because the runner did not attach a dated provider pricing snapshot; the API errors and retries are preserved in each record.
- The v4 records carry the runner's old `v0.1` label even though the one-action-per-turn prompt was added before this batch. Their runtime and prompt hashes capture the actual configuration; the runner is now set to write `v0.3` for future batches, including Moonshot pacing metadata. Treat v4 as prompt protocol v0.2 for interpretation.

## Issues found

1. **Must-ask answer schema is ambiguous and the evaluator is too strict.** The task asks the agent to identify one approver but does not specify whether `approved_by` is a scalar or array. The gold answer stores one acceptable approver as a singleton array. In three traces (OpenAI vendor onboarding; Anthropic vendor onboarding and service incident notice), the agent contacted the correct information holder and approver, received the required fact and approval, and returned the correct visible alias. Alias mapping canonicalized the scalar ID, but exact answer comparison still rejected scalar-versus-array shape. A diagnostic re-score that normalizes a scalar to the singleton gold array makes these three task paths successful; this is not the frozen score and must not be reported as a final pilot result. Make the output schema explicit or normalize this valid singleton representation in the evaluator, then re-score from saved traces without overwriting the original evaluation.
2. **Moonshot rate limit prevents a complete episode.** Requests reached the provider successfully, but the account limit of 3 RPM caused 429s mid-episode and on subsequent episodes. Add provider-aware pacing/retry or obtain a higher limit before collecting its complete pilot block. Do not treat these failed episodes as behavioral observations.
3. **One OpenAI final response was not parseable.** Keep it as a runtime failure and verify whether a stricter output-format instruction or adapter handling resolves it before freezing the protocol.
4. **Pilot API cost is not yet computed.** Token counts and request IDs are in the run records, but all `estimated_cost_usd` values are unavailable because no dated pricing snapshot/cost calculation was attached.

## Gate decision

Static taskset validation passed earlier (60 templates, 141 evaluator fixtures, zero structural errors). This live pilot identified evaluator, rate-limit, and output-format issues. Resolve these, create a new versioned pilot output directory, and rerun the affected pilot cells before starting formal R1. The original run records remain preserved for audit.

Follow-up: the Moonshot-only rerun with 21-second request pacing completed all nine tasks without any 429; see [the paced Moonshot pilot review](../moonshot_r1_pilot_20261024_v5_paced/pilot_review.md). This resolves the observed RPM blocker for Moonshot. The answer-schema/evaluator issue and remaining three-provider pilot review still need resolution before formal collection.

## Files

- `pilot_design.json`: exact sample, models, and condition.
- `runs.jsonl`: one metadata record per attempted episode.
- `episodes/`: instantiated tasks, traces, answers, evaluations, and model-turn records.
