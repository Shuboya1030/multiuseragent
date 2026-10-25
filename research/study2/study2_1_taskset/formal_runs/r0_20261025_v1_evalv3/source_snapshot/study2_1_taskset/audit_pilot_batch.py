"""Read a pilot batch, replay scores, validate metadata, and write audit derivatives."""
import argparse
import hashlib
import json
import os
from pathlib import Path

import jsonschema
from evaluate_episode import evaluate_task

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def rows(path):
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def write(path, data):
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def audit(batch):
    records = rows(batch / "runs.jsonl")
    schema = read(HERE.parent / "study2_1_run_metadata_schema.json")
    trace_fields = set(read(HERE / "trace_schema.json")["required_fields"])
    problems, metrics, inputs, format_rows = [], [], [], []
    old_batch = HERE / "pilot_runs/multimodel_r1_pilot_20261024_v4_single_action"
    old_records = rows(old_batch / "runs.jsonl")
    design = read(batch / "pilot_design.json")
    if len(records) != design["total_episodes_planned"]:
        problems.append("Episode count differs from declared design")
    if len({r["run_id"] for r in records}) != len(records):
        problems.append("Duplicate run IDs")
    for record in records:
        rid = record["run_id"]
        ep = batch / "episodes" / rid
        try:
            jsonschema.validate(record, schema, format_checker=jsonschema.FormatChecker())
            assert record == read(ep / "run_record.json"), "index/record mismatch"
            events = rows(ep / "trace_events.jsonl")
            turns = rows(ep / "model_turns.jsonl")
            api = rows(ep / "api_io.jsonl")
            assert all(trace_fields <= set(e) for e in events), "trace fields missing"
            assert all(e["run_id"] == rid for e in events + api), "cross-run event"
            assert [e["event_id"] for e in events] == list(range(len(events))), "event order"
            for value in record["artifact_refs"].values():
                assert (batch / value).exists(), "missing referenced artifact"
            replay = evaluate_task(HERE / "tasks" / record["task_id"], ep / "answer.json", ep / "trace_events.jsonl", rid, record["alignment"], ep / "identity_mapping.json")
            saved = read(ep / "evaluation.json")
            assert replay == saved, "saved/replayed scores differ"
            mapping = read(ep / "identity_mapping.json")
            assert hashlib.sha256((ep / "identity_mapping.json").read_bytes()).hexdigest() == record["mapping_hash"], "mapping hash mismatch"
            prompt = read(ep / "prompt_snapshot.json")
            requests = [e for e in api if e["event"] == "request"]
            responses = [e for e in api if e["event"] == "response"]
            assert len(responses) == len(turns), "response/turn count differs"
            assert len(requests) == len(responses) + sum(e["event"] == "error" for e in api), "unresolved API call"
            assert all(e.get("http_status") == 200 for e in responses), "unexpected response status"
            assert all(t["model"] == record["model_returned"] for t in turns), "model changed within episode"
            assert sum(t["usage"].get("prompt_tokens", 0) for t in turns) == record["agent_tokens"]["input"], "input token sum"
            assert sum(t["usage"].get("completion_tokens", 0) for t in turns) == record["agent_tokens"]["output"], "output token sum"
            visible = read(ep / "candidate_profiles.json")
            inputs.append(((record["task_id"], record["profile_condition"], record["instance_seed"]), (prompt, visible, mapping["alias_to_canonical"])))
            alias = mapping["alias_to_canonical"]
            gold = read(HERE / "tasks" / record["task_id"] / "gold_policy.json")
            asks = [e for e in events if e["actor"] == "agent" and e["event_type"] == "ask"]
            first_valid = saved.get("first_contact_valid")
            first_step_valid = saved.get("first_step_valid")
            ordered_evidence = saved.get("ordered_information_approval_submission")
            api_failures = [e for e in api if e["event"] == "error"]
            metrics.append({"run_id": rid, "provider": record["model_provider"], "model_requested": record["model_requested"], "model_returned": record["model_returned"],
                "status": record["status"], "submitted": record["behavior_metrics"]["episode_outcome"] == "submitted",
                "api_requests": len(requests), "api_failures": len(api_failures), "model_turns": len(turns), "contacts": len(asks),
                "first_recipient_valid": first_valid, "first_step_valid": first_step_valid,
                "required_fact_received": saved.get("required_fact_in_reply"), "authorized_approval_received": saved.get("approval_in_reply"),
                "ordered_information_approval_submission": ordered_evidence,
                "protocol_underhelp_missing_required_evidence": saved.get("underhelp") if record["help_need_class"] == "must_ask" else None,
                "help_need_class": record["help_need_class"], "task_id": record["task_id"],
                "missing_required_information": saved.get("missing_required_information"), "missing_required_approval": saved.get("missing_required_approval"),
                "overhelp": saved.get("overhelp"), "optional_quality_points": saved.get("optional_quality_points"),
                "reply_used_keyword_coverage": saved.get("reply_used_keyword_coverage"),
                "evaluator_underhelp": saved.get("underhelp"), "evaluator_task_success": saved.get("task_success"),
                "checkpoint_score": saved.get("checkpoint_score"), "checkpoint_vector": saved.get("checkpoint_vector"),
                "tokens": record["agent_tokens"], "latency_ms": record["latency_ms"], "cost_status": record["cost_status"],
                "infrastructure_smoke_pass": record["status"] == "completed" and not record["errors"] and not api_failures})
            historical = next(r for r in old_records if r["model_provider"] == record["model_provider"] and r["task_id"] == record["task_id"])
            old_ep = old_batch / "episodes" / historical["run_id"]
            original_files = {"task.md", "candidate_profiles.json", "identity_mapping.json", "run_manifest.json", "run_record.json", "model_turns.jsonl", "trace_events.jsonl", "answer.json", "evaluation.json"}
            assert all((ep / name).exists() for name in original_files), "missing legacy file"
            format_rows.append({"provider": record["model_provider"], "schema_same": record["schema_version"] == historical["schema_version"],
                "top_level_keys_added": sorted(set(record) - set(historical)), "top_level_keys_removed": sorted(set(historical) - set(record)),
                "legacy_files_preserved": sorted(original_files), "additional_files": sorted(p.name for p in ep.iterdir() if p.name not in original_files),
                "historical_reference": str(old_ep.relative_to(HERE)), "path_semantics": "new artifact_refs relative to batch; historical Windows absolute paths unchanged",
                "trace_extension": "additional tool_action/error events and nullable fields; contact count still uses ask only"})
        except Exception as exc:
            problems.append({"run_id": rid, "error_type": type(exc).__name__, "detail": str(exc)[:300]})
    matched = {}
    for cell, value in inputs:
        if cell in matched and value != matched[cell]:
            problems.append("Model-visible inputs or candidate mappings differ within matched cell: " + str(cell))
        matched[cell] = value
    keys = [os.environ.get(k, "") for k in ("OPENAI_API_KEY", "MOONSHOT_API_KEY", "ANTHROPIC_API_KEY")]
    secret_hits = []
    if not all(keys): problems.append("Credential leak scan could not load every configured key")
    for path in batch.rglob("*"):
        if path.is_file():
            data = path.read_bytes()
            if any(k and k.encode() in data for k in keys): secret_hits.append(str(path.relative_to(batch)))
    if secret_hits: problems.append({"credential_leak_files": secret_hits})
    report = {"passed": not problems, "episodes": len(records), "problems": problems,
              "checks": ["study21-run-v2 JSON Schema", "trace required fields/order/run isolation", "portable artifact references", "score replay equality", "mapping hash", "request/response completeness", "stable returned model per episode", "token sums", "matched inputs across providers", "legacy file/field compatibility", "exact configured credential scan"],
              "interpretation": "Audit completeness is separate from task success; a diagnostic sample does not pass full stratified pilot gates."}
    write(batch / "artifact_audit.json", report)
    write(batch / "episode_metrics.json", metrics)
    write(batch / "format_comparison.json", format_rows)
    print(json.dumps(report, ensure_ascii=False))
    return not problems


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("batch", type=Path)
    args = parser.parse_args()
    raise SystemExit(0 if audit(args.batch.resolve()) else 1)
