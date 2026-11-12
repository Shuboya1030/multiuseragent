"""Offline paired Phase0 analysis. Unreviewed natural-language evidence stays unknown."""
from collections import defaultdict
import hashlib
from pathlib import Path
import random

from .contracts import fingerprint, require, strict_json
from .phase0 import load_case, score_record


def mean(values):
    return sum(values) / len(values) if values else None


def paired_interval(values, seed=20261112):
    if len(values) < 2:
        return None
    rng = random.Random(seed)
    samples = sorted(mean(rng.choices(values, k=len(values))) for _ in range(5000))
    return [samples[124], samples[4874]]


def analyze(root, reviews=None):
    root = Path(root)
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    repeats = sorted({s["repeat"] for s in plan["slots"]})
    expected_episodes = len(plan["slots"])
    reviews = reviews or {}
    records, by_task, rows, queue = [], defaultdict(dict), [], []
    frozen_slots = {s["episode_id"]: s for s in plan["slots"]}
    seen = set()
    for path in sorted(root.glob("slot-*.json")):
        record = strict_json(path.read_bytes())
        require(record["complete"] is True, "Only complete slot exports have an official score")
        slot = record["slot"]
        require(slot == frozen_slots.get(slot["episode_id"]) and slot["episode_id"] not in seen,
                "Each scored record must bind one unique frozen formal slot")
        seen.add(slot["episode_id"])
        case = load_case(slot["task_id"])
        score = score_record(case, record, reviews.get(slot["episode_id"]))
        rows.append({"slot": slot, "score": score, "progress": record["progress"],
                     "normal_actions": record["normal_actions"], "model_calls": record["model_calls"]})
        records.append(record)
        if score["evaluation_status"] == "scored":
            by_task[slot["task_id"]][(slot["arm"], slot["repeat"])] = score
        by_id = {e["message_id"]: e for e in record["events"]}
        for item in score["evidence"]:
            if item["status"] != "unknown":
                continue
            node = next(n for n in case.blueprint["gold_dag"]["nodes"] if n["id"] == item["node_id"])
            hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
            queue.append({"episode_id": slot["episode_id"], "task_id": slot["task_id"],
                          "node_id": node["id"], "message_id": item["message_id"],
                          "request_id": item["request_id"],
                          "request": by_id[item["request_id"]]["content"],
                          "reply": by_id[item["message_id"]]["content"],
                          "expected_records_PRIVATE_REVIEW_ONLY": [hidden[h] for h in node["information_ids"]],
                          "content_sha256": hashlib.sha256(by_id[item["message_id"]]["content"].encode()).hexdigest(),
                          "request_content_sha256": hashlib.sha256(by_id[item["request_id"]]["content"].encode()).hexdigest(),
                          "reviewer_required_NOT_automatic_release": True})
    aggregates = {}
    for group in ("all", "Must-help", "Optional-help"):
        selected = rows if group == "all" else [r for r in rows if r["score"]["help_class"] == group]
        arms = {}
        for arm in "ABCD":
            own = [r for r in selected if r["slot"]["arm"] == arm]
            eligible = [r for r in own if r["score"]["evaluation_status"] == "scored"]
            values = [r["score"] for r in eligible]
            arms[arm] = {"complete": len(own), "official_evidence_resolved": len(eligible),
                         "T": mean([s["T"] for s in values]), "R": mean([s["R"] for s in values]),
                         "excess_C": mean([max(0, s["process"]["interruption_cost"] -
                             (sum(min(load_case(r["slot"]["task_id"]).costs[p]
                                      for p in n["admissible_recipients"])
                                  for n in load_case(r["slot"]["task_id"]).blueprint["gold_dag"]["nodes"])
                              if s["help_class"] == "Must-help" else 0))
                             for r, s in zip(eligible, values)]),
                         "Nauth": mean([s["errors"]["n_auth"] for s in values]),
                         "Nwaste": mean([s["errors"]["n_waste"] for s in values]),
                         "content_full_match": sum(
                             s["artifact"].get("artifact_correct", s["artifact"]["field_accuracy"] == 1)
                             is True for s in values),
                         "official_base_pass": sum(s["base_pass"] is True for s in values),
                         "delivery": sum(r["progress"]["user_delivery_complete"] for r in own),
                         "submit": sum(r["progress"]["bridge_submitted"] for r in own),
                         "ASK_episode_rate": mean([int(r["score"]["process"]["n_asks"] > 0) for r in own]),
                         "first_contact_valid": mean([int(s["process"]["first_contact_valid"]) for s in values
                                                       if s["process"]["first_contact_valid"] is not None]),
                         "refusals": sum(s["errors"]["rejections"] for s in values),
                         "repaired_nodes": sum(s["errors"]["repaired_nodes"] for s in values),
                         "note": "available-only descriptive; gate requires the full frozen coverage"}
        contrasts = {}
        for left, right in (("B", "A"), ("C", "A"), ("D", "B"), ("D", "A")):
            deltas = []
            for tid, scores in by_task.items():
                if group != "all" and load_case(tid).blueprint["help_class"] != group:
                    continue
                if all((arm, repeat) in scores for arm in (left, right) for repeat in repeats):
                    deltas.append(mean([scores[(left, r)]["R"] - scores[(right, r)]["R"] for r in repeats]))
            contrasts[left + "-" + right] = {
                "tasks_with_all_frozen_paired_repeats": len(deltas), "mean_R_difference": mean(deltas),
                "within_single_org_task_paired_CI95": paired_interval(deltas),
                "not_between_organization_uncertainty": True}
        aggregates[group] = {"arms": arms, "contrasts": contrasts}
    complete_coverage = len(rows) == expected_episodes and all(
        len(by_task[tid]) == 4 * len(repeats) for tid in {s["task_id"] for s in plan["slots"]})
    contrasts = aggregates["all"]["contrasts"]
    gate = None
    if complete_coverage:
        gate = any(contrasts[name]["mean_R_difference"] >= .10 for name in ("B-A", "D-A"))
    return {"schema": "study4-formal-phase0-analysis-2", "record_protocol": plan["phase0_protocol"],
            "complete_episodes": len(rows),
            "expected_episodes": expected_episodes, "repeats_per_task": len(repeats), "missing_slots": [
                s for s in plan["slots"] if s["episode_id"] not in {r["slot"]["episode_id"] for r in rows}],
            "full_coverage_and_evidence_resolved": complete_coverage,
            "mean_R_training_gate_passed": gate, "gate_unknown_not_false": gate is None,
            "aggregates": aggregates, "rows": rows, "private_review_queue": queue,
            "unreviewed_messages_not_automatically_certified": True}
