#!/usr/bin/env python3
"""Re-score selected Study 2.1 pilot episodes with evaluator v2.

Raw traces and original evaluation.json files are preserved. New scores are
written as evaluation_posthoc_eval_v2.json with a batch-level audit manifest.
"""
import hashlib
import importlib.util
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TASKS = ROOT / "tasks"
BATCHES = [
    ROOT / "pilot_runs" / "multimodel_r1_pilot_20261024_v4_single_action",
    ROOT / "pilot_runs" / "moonshot_r1_pilot_20261024_v5_paced",
]
OUT_NAME = "evaluation_posthoc_eval_v2.json"

spec = importlib.util.spec_from_file_location("study21_evaluator", ROOT / "evaluate_episode.py")
evaluator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(evaluator)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


totals = defaultdict(lambda: {"n": 0, "original_evaluation_n": 0, "original_success": 0, "v2_success": 0, "changed_among_scored": 0})
batch_audits = []
for batch in BATCHES:
    episodes_root = batch / "episodes"
    episode_rows = []
    for episode in sorted(episodes_root.iterdir()):
        if not episode.is_dir():
            continue
        record_path = episode / "run_record.json"
        if not record_path.exists():
            record_path = episode / "run_record_recovered.json"
        if not record_path.exists():
            continue
        record = read_json(record_path)
        refs = record.get("artifact_refs", {})
        answer = episode / "answer.json"
        trace = episode / "trace_events.jsonl"
        mapping = episode / "identity_mapping.json"
        task_id = record.get("task_id")
        task_dir = TASKS / task_id
        if not (answer.exists() and trace.exists() and task_dir.exists()):
            continue
        original_path = episode / "evaluation.json"
        original = read_json(original_path) if original_path.exists() else {}
        variant = record.get("variant_id") or record.get("alignment")
        result = evaluator.evaluate_task(
            task_dir,
            answer,
            trace,
            record.get("run_id"),
            variant,
            mapping if mapping.exists() else None,
        )
        result["posthoc_evaluator_version"] = "study21-eval-spec-2"
        result["posthoc_evaluator_sha256"] = sha256(ROOT / "evaluate_episode.py")
        result["source_artifacts"] = {
            "answer": answer.name,
            "trace": trace.name,
            "original_evaluation": original_path.name if original_path.exists() else None,
            "run_record": record_path.name,
        }
        destination = episode / OUT_NAME
        destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        model = record.get("model_returned") or record.get("model_requested") or record.get("model_provider", "unknown")
        klass = result.get("help_need_class", "unknown")
        key = (batch.name, model, klass)
        totals[key]["n"] += 1
        old_success = original.get("task_success")
        new_success = result.get("task_success")
        if old_success in (True, False):
            totals[key]["original_evaluation_n"] += 1
            totals[key]["original_success"] += int(old_success is True)
            totals[key]["changed_among_scored"] += int(old_success != new_success)
        totals[key]["v2_success"] += int(new_success is True)
        episode_rows.append({
            "episode_id": episode.name,
            "run_id": record.get("run_id"),
            "task_id": task_id,
            "model": model,
            "help_need_class": klass,
            "original_task_success": old_success,
            "posthoc_v2_task_success": new_success,
            "changed": old_success != new_success if old_success in (True, False) else None,
            "output": OUT_NAME,
        })
    batch_audits.append({
        "batch": batch.name,
        "episode_count_rescored": len(episode_rows),
        "evaluator_version": "study21-eval-spec-2",
        "evaluator_sha256": sha256(ROOT / "evaluate_episode.py"),
        "task_generator_version": "source-v0.4+study21-wrapper-2",
        "raw_artifacts_modified": False,
        "episodes": episode_rows,
    })
    (batch / "posthoc_evaluator_v2_audit.json").write_text(
        json.dumps(batch_audits[-1], ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )

summary = {
    "schema_version": "study21-posthoc-score-audit-v1",
    "purpose": "Re-score existing pilot answers/traces after clarifying approved_by as a single candidate ID; no model reruns.",
    "evaluator_version": "study21-eval-spec-2",
    "evaluator_sha256": sha256(ROOT / "evaluate_episode.py"),
    "raw_artifacts_modified": False,
    "batches": batch_audits,
    "group_summary": [
        {"batch": k[0], "model": k[1], "help_need_class": k[2], **v}
        for k, v in sorted(totals.items())
    ],
}
for batch in BATCHES:
    (batch / "posthoc_evaluator_v2_audit.json").write_text(
        json.dumps(next(x for x in batch_audits if x["batch"] == batch.name), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
(ROOT / "pilot_runs" / "posthoc_evaluator_v2_summary.json").write_text(
    json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
)
print(json.dumps({"batches": [(x["batch"], x["episode_count_rescored"]) for x in batch_audits],
                  "group_summary": summary["group_summary"]}, ensure_ascii=False, indent=2))
