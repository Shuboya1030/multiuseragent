# R1 reduced smoke pilot decision — 2026-10-25

## Authorization and purpose

The user explicitly reduced the next pilot from nine tasks per model to **one task per model**, solely to check that the workflow runs end to end. The user also requested preservation of the decision, all results, traces and metadata in the repository's existing format, and comparison with the earlier run artifacts from another computer.

This is a three-episode **smoke pilot**, not the full 27-episode stratified acceptance pilot and not confirmatory data. Success here does not close independent task review, optional/no-help runtime coverage, optional scoring validation, precision planning, budget freeze, or confirmatory-runner gates. Formal R1 remains not ready.

## Frozen pre-run choices

- Source default-branch commit: `c9e305e6550d0b9fb351211896db514e453261b1`.
- Task: `must-vendor-onboarding`, `separated`, R1, all three providers. It is the first task in the existing fixed pilot sample and exercises information contact, reading a reply, authorized approval, and final submission. Selection was made before any new model output.
- CLI seed: `20261025`; existing runner adds task index 1, so each episode uses instance seed `20261026`. All models receive identical task/profile contents, alias mapping and display order. Seed controls the task instance, not provider sampling.
- Models: OpenAI `gpt-5.4-mini`, Moonshot `kimi-k2.6`, Anthropic `claude-haiku-5-5`. Preserve returned model IDs; no substitutions.
- Runtime: existing local deterministic-NPC pilot, not full AgentCompany. Current v2 task wrapper, gold, evaluator, tools and system prompt are unchanged.
- One episode per provider, in the existing OpenAI → Moonshot → Anthropic order. This convenience order is acceptable for a smoke check only; it is not formal randomized collection.
- Maximum 8 model decisions per episode and 1,600 output tokens per request. At most 24 requests and 38,400 configured maximum output tokens across three episodes. Input usage depends on growing conversation history. This is not a dollar-cost bound.
- Retain Moonshot's 21-second minimum request interval. One API attempt per decision; failures stop that episode and are preserved, not retried silently. Any later rerun needs a new run ID and an explicit link to the failed episode.
- Actual dollar cost is `unavailable` unless sufficient provider accounting is returned; token usage is recorded, never substituted for cost. No formal experiment is launched.

## Compatibility with previous results

Reference batches in `study2_1_taskset/pilot_runs/`:

- `multimodel_r1_pilot_20261024_v4_single_action`: 27 episodes.
- `moonshot_r1_pilot_20261024_v5_paced`: 9 episodes.

Keep the same batch-level `pilot_design.json`, `runs.jsonl`, `pilot_summary.json`, `pilot_review.md` and per-episode `task.md`, `candidate_profiles.json`, `identity_mapping.json`, `run_manifest.json`, `run_record.json`, `model_turns.jsonl`, `trace_events.jsonl`, `answer.json`, and `evaluation.json`.

Metadata remains `study21-run-v2`, validated against `study2_1_run_metadata_schema.json`. The old taskset-level `run_record_schema.json` is a v1 field checklist; the study-level JSON Schema is authoritative for these v2 records. Keep ask/reply/submit event meanings and evaluator behavior. Add required nullable trace fields and explicit tool_action/error events, which are not extra contacts.

New audit additions: append-only `api_io.jsonl` for provider-serialized requests/responses, `prompt_snapshot.json`, append-only batch `run_status.jsonl`, a source/config snapshot, artifact SHA-256 manifest, and schema/replay/secret checks. `artifact_refs` become portable paths relative to the batch directory; historical absolute Windows paths are left intact. API headers with credentials are never saved. Provider private reasoning blocks are omitted consistently with the existing repository policy; public text, tool arguments, usage, returned model IDs and request IDs are retained.

Runner audit version: `study21-r1-pilot-v0.5-audit`. Audit changes include incremental trace/model-turn writes, complete sanitized API I/O, preservation of cache usage, accurate failed status, no implicit retry, unique run suffixes and refusal to overwrite existing batches/episodes. These are recorded as a new runtime version; this is not a claim of identical software to v4/v5.

## Acceptance and interpretation

Inspect each full trajectory. Report API acceptance, tool parsing, send/read flow, deterministic NPC behavior, submission, evaluator result, required artifacts, tokens and latency separately. A valid failed task is not automatically an infrastructure failure. A 3/3 success result still says nothing reliable about cross-task model ranking or R1−R0 effects.

Store failures and all first-attempt outputs. Generate only descriptive diagnostics; no hypothesis tests, confidence intervals or model ranking from one template.
