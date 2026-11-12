"""Six exposed task packages x four arms, SCRIPTED public callback, no model calls."""
from datetime import datetime, timedelta, timezone
import json
import math
from pathlib import Path

from .benchmark import BenchmarkNPC, export_bundle, load_task, score_episode, verify_assets
from .budget import LocalBudget
from .contracts import canonical, fingerprint, require
from .mini_request import LocalMini
from .runtime import SharedRuntime
from .scheduler import ARMS, BenchmarkReference, FourArmScheduler


def public_plan(observation):
    """Hand-reviewed public document parsing for these six exposed tasks, not an NL solver."""
    task = observation["task"]
    fields = task["output_fields"]
    text = task["instruction"] + "\n" + "\n".join(observation["workspace"].values())
    if "segment_id" in fields:
        require(all(s in text for s in ("SEG-Q3-ENT", "420", "2026-11-12", "APR-Q3")), "Mail public seed changed")
        seed = dict(segment_id="SEG-Q3-ENT", recipient_count=420, send_date="2026-11-12", authorization_ref="APR-Q3")
        sequence = [("segment_id", "Sales Director"), ("authorization_ref", "Sales Director")]
    elif "url_slug" in fields:
        require(all(s in text for s in ("remote-work", "v3.1", "2026-01-01", "remote-work-v3")), "Wiki seed changed")
        seed = dict(policy="remote-work", version="v3.1", effective_date="2026-01-01", url_slug="remote-work-v3")
        sequence = [("version", "Documentation Engineer")]
    elif "hours" in fields:
        require(all(s in text for s in ("DBX Consulting", "64", "150/hour")), "Invoice seed changed")
        seed = dict(vendor="DBX Consulting", hours=64, amount_usd=9600, authorization_ref="PENDING")
        sequence = [("hours", "Database Team Project Manager"), ("authorization_ref", "Database Team Project Manager")]
    elif "seats" in fields:
        require(all(s in text for s in ("16 seats", "600 per seat", "P-01", "AI-26-A", "VB-PLAN-16")), "Order seed changed")
        seed = dict(seats=16, total_usd=9600, allocation_revision="P-01", budget_code="AI-26-A",
                    release_reference="VB-PLAN-16")
        sequence = [("seats", "AI Researcher"), ("release_reference", "Finance")]
    elif "dataset_id" in fields:
        require(all(s in text for s in ("DS-DEMO-2", "420000", "2025-12-01")), "Dataset seed changed")
        seed = dict(dataset_id="DS-DEMO-2", document_count=420000, refreshed_on="2025-12-01")
        sequence = [("dataset_id", "Web Crawler")]
    else:
        require(all(s in text for s in ("22 attendees", "M1", "25 per person", "all meals regular")), "Lunch seed changed")
        seed = dict(headcount=22, menu="M1", vegetarian_meals=0, total_usd=550)
        sequence = [("vegetarian_meals", "Human Resources")]
    return seed, sequence


def mock_token_count(request):
    """Deliberately approximate local-only counter, never usable to authorize real spending."""
    return math.ceil(len(canonical(request).encode("utf-8")) / 4)


class ScriptedPublicMini:
    def __init__(self, no_ask=False, fail_operation=None):
        self.no_ask, self.fail_operation = no_ask, fail_operation
        self.seen = []

    def __call__(self, request):
        self.seen.append(json.loads(canonical(request)))
        body = json.loads(request["input"][1]["content"])
        operation, observation = body["operation"], body["state"]
        if operation == self.fail_operation:
            raise TimeoutError("Intentional local transport failure; no API")
        seed, sequence = public_plan(observation)
        obtained = {v["key"]: v["value"] for v in observation["obtained_values"]}
        if operation == "ordinary":
            seed.update({k: v for k, v in obtained.items() if k in observation["task"]["output_fields"]})
            path = observation["task"]["artifact_path"]
            if observation["workspace"].get(path) != canonical(seed):
                tool, arguments = "write_file", {"path": path, "content": canonical(seed)}
            elif not observation["progress"]["posted_current_revision"]:
                tool, arguments = "post_channel", {"channel": observation["task"]["channel"],
                                                   "content": "Prepared current record: " + path}
            else:
                tool, arguments = "submit", {"answer": "Record delivered."}
            output = {"tool": tool, "arguments": canonical(arguments)}
        elif operation == "control":
            missing = next(((field, role) for field, role in sequence if field not in obtained), None)
            if missing is None or self.no_ask:
                output = {"action": "SELF", "person_id": None}
            else:
                choices = [p for p in observation["task"]["people"] if missing[1] in p["role"]]
                require(len(choices) == 1, "Scripted public role rule not uniquely applicable")
                output = {"action": "ASK", "person_id": choices[0]["person_id"]}
        else:
            plan = body.get("request_plan")
            if plan is None:
                field, _ = next((f, r) for f, r in sequence if f not in obtained)
                plan = {"intent": "request " + field,
                        "include_value_ids": [v["value_id"] for v in observation["obtained_values"]]}
            values = [v for v in observation["obtained_values"] if v["value_id"] in plan["include_value_ids"]]
            citations = "; ".join(v["key"] + "=" + str(v["value"]) for v in values)
            # Public context only; include no artifact or generated private state.
            docs = "\n".join(t for p, t in observation["workspace"].items()
                             if p != observation["task"]["artifact_path"])
            output = {**plan, "question": plan["intent"] + ". " + observation["task"]["instruction"] + "\n" +
                       docs + "\n" + citations}
        return {"output_text": canonical(output), "status": "completed",
                "usage": {"input_tokens": mock_token_count(request), "output_tokens": math.ceil(len(canonical(output)) / 4)}}


def make_case(task_id, arm, callback=None, budget=None):
    task = load_task(task_id)
    budget = budget or LocalBudget("55")
    mini = LocalMini(callback or ScriptedPublicMini(), mock_token_count, budget, f"LOCAL:{task_id}:{arm}")
    rt = SharedRuntime(task.public, mini, BenchmarkNPC(task), mini.episode_id)
    ticks = iter(range(1000))
    clock = lambda: (datetime(2000, 1, 1, tzinfo=timezone.utc) + timedelta(seconds=next(ticks))).isoformat()
    scheduler = FourArmScheduler(rt, mini, arm, BenchmarkReference(task), clock)
    return task, rt, mini, scheduler


def run_check():
    assets = verify_assets()
    ids = json.loads((Path(__file__).parent / "configs" / "ceiling_pilot.json").read_bytes())["task_ids"]
    rows = []
    budget = LocalBudget("55")
    for task_id in ids:
        for arm in ARMS:
            task, rt, mini, scheduler = make_case(task_id, arm, budget=budget)
            scheduler.run()
            bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
            scored = score_episode(task, rt, bundle)
            require(scored["official"]["base_pass"] is True and scored["episode_status"] == "scored",
                    "Scripted reference compatibility failed")
            rows.append({"task_id": task_id, "arm": arm, "official": scored["official"],
                         "bridge_submitted": scored["bridge_submitted"],
                         "user_delivery_complete": scored["user_delivery_complete"],
                         "input_fingerprint": scored["input_fingerprint"], "trace_sha256": fingerprint(bundle),
                         "schedule_sha256": fingerprint(scheduler.cycles), "normal_actions": rt.normal_actions,
                         "mock_requests": len(mini.requests), "proposal_refreshes": sum(
                             c["proposal_discarded"] for c in scheduler.cycles),
                         "budget": mini.budget.receipt()})
    return {"schema": "study4-v2-local-adapter-check-1", "mode": "SCRIPTED-LOCAL-NOT-mini-inference",
            "source_revision": assets["revision"], "source_files_byte_verified": len(assets["files"]),
            "cases": rows, "local_cases": len(rows), "actual_model_API_calls": 0, "actual_GPU_jobs": 0,
            "paid_pilot_48_episodes_executed": False, "training_executed": False,
            "actual_paid_USD": "0", "local_mock_global_budget": budget.receipt(),
            "NL_matching_validated": False, "real_tokenizer_and_request_acceptance_validated": False,
            "budget_cap_approval": "pending", "ceiling_gain_or_task_improvement_established": False}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = run_check()
    with args.output.open("x", encoding="utf-8", newline="\n") as out:
        out.write(json.dumps(result, indent=2, ensure_ascii=False) + "\n")
    print("Completed 24 SCRIPTED local compatibility cases, official scorer; zero model calls.")
