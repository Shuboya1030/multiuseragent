"""Export this actual stop and explicit nonblind retained-evidence judgments; zero API."""
from decimal import Decimal
import gzip
import hashlib
import json
from pathlib import Path
import sqlite3
import sys

repo = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(repo))
from research.study4.v2.contracts import canonical, fingerprint, strict_json
from research.study4.v2.phase0 import load_case, scorer, write_new
from research.study4.v2.phase0_analysis import analyze
from research.study4.v2.phase0_recovery import verify_history
from research.study4.v2.reference_completion import context_present, progress

root = Path(sys.argv[1]).resolve()
out = Path(sys.argv[2]).resolve()
plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
receipt = strict_json((root / "FINAL_RECEIPT.json").read_bytes())
verify_history(plan["history"])
reviews = strict_json((root / "REVIEWS_RETAINED_AC.json").read_bytes())
judgments = {
    ("o-low-press-factsheet", "C"): (False, False, "Headline supplied but Q-1102 quote ID never disclosed."),
    ("o-low-press-factsheet", "A"): (False, False, "Release context alone gives neither Q-1102 nor the headline."),
    ("m-med-hiring-requisition", "C"): (False, True, "Neither L5 nor B5 disclosed; context/other-field caveats do not supply them."),
    ("m-med-hiring-requisition", "A"): (False, True, "Explicitly withholds level/band despite actual R-77 context."),
    ("m-low-new-hire-record", "A"): (True, False, "E-20931 and2026-11-16 affirmatively released; department is outside this node."),
    ("m-low-new-hire-record", "C"): (True, False, "Both employee ID and start date supplied; unrelated department limitation is not a refusal."),
}
initial = analyze(root, reviews)
assert len(initial["private_review_queue"]) == 6
for item in initial["private_review_queue"]:
    slot = next(s for s in plan["slots"] if s["episode_id"] == item["episode_id"])
    accepted, refused, reason = judgments[(slot["task_id"], slot["arm"])]
    reviews.setdefault(item["episode_id"], []).append({
        "node_id": item["node_id"], "message_id": item["message_id"], "request_id": item["request_id"],
        "decision": "accept" if accepted else "reject", "is_refusal": refused,
        "reviewer": "Copilot-direct-nonblind-AI-20261112-v5-stop",
        "reason": reason, "content_sha256": item["content_sha256"],
        "request_content_sha256": item["request_content_sha256"]})
write_new(root / "REVIEWS_RETAINED_AC_FINAL.json", reviews)
analysis = analyze(root, reviews)
assert not analysis["private_review_queue"] and analysis["mean_R_training_gate_passed"] is None
write_new(root / "ANALYSIS_RETAINED_AC_REVIEWED.json", analysis)
journal = [strict_json(line) for line in (root / "events.jsonl").read_bytes().splitlines()]
partial = next(e for e in journal if e["kind"] == "incomplete_episode")
case = load_case(partial["slot"]["task_id"])
hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
public_text = case.public.instruction + "\n" + "\n".join(text for _, text in case.public.documents)
prefix, requests, trace = [], {}, []
for event in partial["history"]:
    prefix.append(event)
    if event["kind"] == "send_message":
        requests[event["message_id"]] = event
    elif event["kind"] == "read_messages":
        request = requests[event["in_reply_to"]]
        state = progress(case, prefix, scorer())
        trace.append({
            "request": request, "reply": event,
            "released_nodes_after_reply": sorted(state["released"]), "unresolved": state["unresolved"],
            "required_context_satisfied_by_actual_request": {
                n["id"]: all(context_present(c, request["content"], public_text, scorer())
                             for h in n["information_ids"] for c in hidden[h]["required_context"])
                for n in case.blueprint["gold_dag"]["nodes"]}})
db = sqlite3.connect((root / (plan["run_id"] + ".sqlite3")).resolve().as_uri() + "?mode=ro&immutable=1", uri=True)
try:
    calls = db.execute("select state,charged,input_tokens,output_tokens from calls").fetchall()
finally:
    db.close()
assert len(calls) == 18 and all(c[0] == "settled" for c in calls)
new_cost = sum((Decimal(c[1]) for c in calls), Decimal(0))
assert new_cost == Decimal(".054096900")
contacts = [e for e in partial["history"] if e["kind"] == "send_message"]
payload = {
    "schema": "study4-reference-v5-actual-stop-1",
    "source_commit": plan["code_commit"], "plan_fingerprint": fingerprint(plan),
    "original_direct_user_source": plan["direct_user_source"],
    "agent_review_release_NOT_new_user_authorization": plan["reference_recovery"]["review_release"],
    "receipt_sha256": hashlib.sha256((root / "FINAL_RECEIPT.json").read_bytes()).hexdigest(),
    "journal_sha256_PRIVATE_NOT_PUBLISHED": hashlib.sha256((root / "events.jsonl").read_bytes()).hexdigest(),
    "receipt_summary": {k: receipt[k] for k in (
        "status", "error_type", "complete_episodes", "retained_complete_episodes",
        "fresh_complete_episodes", "complete_four_arm_blocks", "budget")},
    "actual_partial": {"slot": partial["slot"], "complete": False,
        "model_calls": partial["model_calls"], "normal_actions": partial["normal_actions"],
        "contact_cost": sum(case.costs[e["person_id"]] for e in contacts),
        "contacts": len(contacts), "artifact": partial["workspace"].get(case.public.artifact_path),
        "progress": partial["progress"], "T": None, "R": None,
        "gold_nodes_PRIVATE_AUDIT": case.blueprint["gold_dag"]["nodes"],
        "source_records_PRIVATE_AUDIT": case.blueprint["hidden_information"],
        "six_actual_exchanges_and_progress": trace},
    "budget": {"original_cap_USD": "50.00", "new_calls": len(calls),
        "new_settled_USD_upper": str(new_cost), "new_unknown": 0, "inflight": 0,
        "all_calls": 1040, "all_settled": 1034, "all_unknown": 6,
        "all_settled_USD_upper": str(Decimal(plan["inherited"]["settled_USD_upper"]) + new_cost),
        "old_unknown_held_USD": "5.148000",
        "occupied_USD_upper": receipt["budget"]["occupied_USD_upper"],
        "remaining_USD": str(Decimal("50") - Decimal(receipt["budget"]["occupied_USD_upper"])),
        "input_tokens": sum(c[2] for c in calls), "output_tokens": sum(c[3] for c in calls),
        "held_is_not_confirmed_payment": True},
    "retained_reviewed_analysis": analysis,
    "incomplete_not_business_zero_or_reusable_fresh_episode": True,
    "training_gate_unknown": True, "automatic_retry": False,
    "no_change_to_source_gold_or_conflict_policy_after_observation": True,
}
write_new(out, payload)
records = [strict_json(p.read_bytes()) for p in sorted(root.glob("slot-*.json"))] + [partial]
blob = gzip.compress(("\n".join(canonical(r) for r in records) + "\n").encode(), mtime=0)
with out.with_suffix(".public.jsonl.gz").open("xb") as handle:
    handle.write(blob)
print(json.dumps({"budget": payload["budget"], "retained_reviewed": analysis["complete_episodes"],
                  "review_unknown": len(analysis["private_review_queue"]),
                  "aggregates": analysis["aggregates"], "artifact": payload["actual_partial"]["artifact"],
                  "contact_cost": payload["actual_partial"]["contact_cost"],
                  "released_prefixes": [t["released_nodes_after_reply"] for t in trace]}))
