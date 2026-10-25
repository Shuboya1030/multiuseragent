# R1 smoke batch: one task × three models

Start with [pilot_review.md](pilot_review.md). The user authorized exactly one task per model for feasibility; three episodes were collected and all original outcomes are retained.

| Artifact | Purpose |
|---|---|
| `pilot_design.json` | Executed model/task selection, seed and scope |
| `runs.jsonl` | One terminal metadata record per episode, `study21-run-v2` |
| `run_status.jsonl` | Append-only started/terminal status events |
| `episodes/<run_id>/` | Exact inputs, hidden evaluator mapping, model turns, sanitized API request/response logs, trace, answer and evaluation |
| `pilot_summary.json` | Original runner summary |
| `episode_metrics.json` | Descriptive diagnostics including the approval/underhelp discrepancy |
| `format_comparison.json` | Compatibility with the historical v4 results |
| `artifact_audit.json` | Schema, trace, replay, usage, pairing and credential-scan checks |
| `preflight_checks.json` | Taskset validation and offline test results |
| `source_snapshot/`, `source_manifest.json` | Exact code, task, protocol and pre-run decision with source hashes |
| `console.log` | Runner status output |
| `artifact_manifest.json` | SHA-256 and sizes for every batch file except the manifest itself |

Resolve `artifact_refs` and `mapping_ref` relative to this directory. The identity mapping and gold/scenario snapshot are evaluator-only and were never injected into model requests. Provider-private reasoning content and authentication headers are omitted from `api_io.jsonl`; public responses/tool calls, model IDs, usage, request IDs and timings are retained.

Replay/audit from repository root (requires Python with jsonschema and the three key environment variables only for the leak scan):

```bash
python research/study2/study2_1_taskset/audit_pilot_batch.py \
  research/study2/study2_1_taskset/pilot_runs/multimodel_r1_smoke_20261025_v6_evalv2
```

This command performs no API calls. It regenerates deterministic audit derivatives; do not change raw episodes. If derivatives are intentionally changed in future, preserve this frozen manifest and create a separately versioned derived audit.
