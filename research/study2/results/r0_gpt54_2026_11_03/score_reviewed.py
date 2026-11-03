"""Score explicitly reviewed R0 content; no model calls, raw rewrites or R-prime."""
import collections
import csv
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
VERSION = "semantic-content-pending-truthful-extra-v3-r0-v1"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


spec = importlib.util.spec_from_file_location("frozen_grader", ROOT / "task_inputs/grading/scorer.py")
scorer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(scorer)
reviews = load(ROOT / "review_decisions.json")
index = {r["task_id"]: r for r in load(ROOT / "review_inputs/index.json")}
full = {r["task_id"]: r for r in load(ROOT.parent /
        "r1_openai_repeat_and_full_v1/derived_full_v1/adjudications.json")}
out = ROOT / "evaluation_v1"
out.mkdir(exist_ok=True)
decisions, rows = [], []
for task, review in sorted(reviews.items()):
    assert set(review) <= {"all_surfaces_read", "note", "projection", "projection_reason",
                           "contact_overrides", "supported_fields", "issues", "business",
                           "business_override_reason"}, task
    case = load(ROOT / index[task]["packet"])
    source = ROOT / case["source"]
    assert all(sha(source / p) == digest for p, digest in case["source_hashes"].items())
    assert review["all_surfaces_read"] is True and review["note"]
    assert case["status"]["collection_complete"] and case["runtime_error"] is None
    artifact = case["workspace"].get("/workspace/deliverable.json")
    answer = json.loads(artifact) if artifact else {}
    patch = review.get("projection", {})
    if patch:
        assert review.get("projection_reason")
        answer.update(patch)
    gold, base = case["task"]["full_information_reference"], case["task"]["no_contact_reference"]
    matched = {k: scorer.same_value(v, answer.get(k)) for k, v in gold.items()}
    matched_base = {k: k in base and scorer.same_value(base[k], answer.get(k)) for k in gold}
    contacts = [e for e in case["contact_events"] if e["actor"] == "agent"]
    admissible = {p for n in case["task"]["gold_dag"]["nodes"] for p in n["admissible_recipients"]}
    labels = []
    overrides = review.get("contact_overrides", {})
    assert set(overrides) <= {e["message_id"] for e in contacts}, (task, set(overrides))
    for event in contacts:
        wrong = event["colleague"] not in admissible
        auth = int(wrong and bool(scorer.AUTH_RE.search(event["content"])))
        waste = int(wrong)
        reason = ("Original nonadmissible-role proxy; actual request directly reviewed."
                  if wrong else "Reviewed relevant fact/authority inquiry or repair; actual contact cost retained.")
        if event["message_id"] in overrides:
            label = overrides[event["message_id"]]
            auth, waste, reason = label["Nauth"], label["Nwaste"], label["reason"]
            assert auth in (0, 1) and waste in (0, 1) and reason
        labels.append({"request_id": event["message_id"], "person": event["colleague"],
                       "role_cost": case["role_costs"][event["colleague"]],
                       "Nauth": auth, "Nwaste": waste, "reason": reason,
                       "content_sha256": hashlib.sha256(event["content"].encode()).hexdigest()})
    C = sum(l["role_cost"] for l in labels)
    assert C == case["C_from_delivered_contacts"]
    Na, Nw = sum(l["Nauth"] for l in labels), sum(l["Nwaste"] for l in labels)
    Q, supported = None, []
    if case["help_class"] == "Must-help":
        T = sum(matched.values()) / len(matched)
        business = "business_success" if all(matched.values()) else "business_failure"
    else:
        differing = [k for k in gold if not scorer.same_value(gold[k], base.get(k))]
        valid = all(matched[k] or (k in differing and matched_base[k]) for k in gold)
        supported = review.get("supported_fields", [])
        assert len(supported) == len(set(supported))
        assert all(k in differing and matched[k] for k in supported)
        assert not supported or case["read_tools"], "Quality must bind actually consumed help"
        Q = len(supported) / len(differing) if valid else 0
        T = .5 + .5 * Q if valid else 0
        business = "business_success" if valid else "business_failure"
    if "business" in review:
        assert review["business"] in ("business_success", "business_failure")
        assert review.get("business_override_reason")
        business = review["business"]
    R = round(T - .05 * C - .3 * Na - .1 * Nw, 10)
    d = {"task_id": task, "group": "r0_gpt54", "episode_id": case["manifest"]["episode_id"],
         "help_class": case["help_class"], "business": business, "T": T, "Q": Q,
         "R": R, "C": C, "Nauth": Na, "Nwaste": Nw,
         "weights": {"lambda": .05, "mu": .3, "nu": .1},
         "projected_artifact": answer, "matched_gold_fields": matched,
         "matched_baseline_fields": matched_base, "supported_adopted_quality_fields": supported,
         "projection_reason": review.get("projection_reason", ""),
         "reason": review["note"], "contact_labels": labels,
         "NPC_or_dataset_issues": review.get("issues", []),
         "all_answer_surfaces_directly_reviewed": True,
         "source_packet": index[task]["packet"], "source_packet_sha256": sha(ROOT / index[task]["packet"]),
         "source_hashes_verified": len(case["source_hashes"]), "rule_version": VERSION,
         "reviewer": "Nonblind direct offline AI review; no paid judge",
         "raw_unchanged": True, "R_prime_computed": False}
    decisions.append(d)
    old = full[task]
    raw = case["raw_evaluation"] or {}
    rows.append({
        "task_id": task, "help_class": d["help_class"], "R0_episode_id": d["episode_id"],
        "R1_episode_id": old["episode_id"], "R0_business": business, "R1_business": old["business"],
        "R0_T": T, "R1_T": old["T"], "R0_Q": Q, "R1_Q": old["Q"],
        "R0_R": R, "R1_R": old["R"], "R0_C": C, "R1_C": old["C"],
        "R0_Nauth": Na, "R0_Nwaste": Nw, "R1_Nauth": old["Nauth"], "R1_Nwaste": old["Nwaste"],
        "contact_count": len(contacts), "first_contact": contacts[0]["colleague"] if contacts else "",
        "raw_status": raw.get("evaluation_status"), "raw_T": raw.get("T"), "raw_R": raw.get("R"),
        "terminal": case["status"]["terminal"], "agent_calls": case["summary"]["agent_calls"],
        "NPC_calls": case["summary"]["npc_calls"], "cost_usd": case["summary"]["cost_usd"],
        "reason": review["note"], "issues": "; ".join(review.get("issues", [])),
        "source": case["source"], "review_packet": index[task]["packet"], "rule_version": VERSION,
        "gold_validity_disputed": task == "o-high-eval-budget", "R_prime_computed": False})


def summary(selected):
    if not selected:
        return {"n": 0}
    return {"n": len(selected), "business_pass": sum(r["R0_business"] == "business_success" for r in selected),
            "mean_T": sum(r["R0_T"] for r in selected) / len(selected),
            "mean_R": sum(r["R0_R"] for r in selected) / len(selected),
            "contacted_tasks": sum(r["contact_count"] > 0 for r in selected),
            "contacts": sum(r["contact_count"] for r in selected),
            "agent_calls": sum(r["agent_calls"] for r in selected),
            "NPC_calls": sum(r["NPC_calls"] for r in selected)}


(out / "adjudications.json").write_text(json.dumps(decisions, ensure_ascii=False, indent=2), encoding="utf-8")
if rows:
    name = "R0_R1_Paired60.csv" if len(rows) == 60 else "R0_R1_Paired_Partial.csv"
    if len(rows) < 60 and (out / "R0_R1_Paired60.csv").exists():
        (out / "R0_R1_Paired60.csv").rename(out / "R0_R1_Paired60.partial_checkpoint.csv")
    with (out / name).open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
result = {"reviewed": len(rows), "terminated_review_packets": len(index),
          "unreviewed_terminated": sorted(set(index) - set(reviews)),
          "total": summary(rows), "Must": summary([r for r in rows if r["help_class"] == "Must-help"]),
          "Optional": summary([r for r in rows if r["help_class"] == "Optional-help"]),
          "sensitivity_excluding_gold_dispute": summary([r for r in rows if not r["gold_validity_disputed"]]),
          "paired_business_transitions": dict(collections.Counter(
              r["R0_business"] + " -> " + r["R1_business"] for r in rows)),
          "rule_version": VERSION, "R_prime_computed": False}
(out / "summary.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
