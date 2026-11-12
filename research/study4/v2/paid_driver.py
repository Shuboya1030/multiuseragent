"""Fresh-only single-process ceiling driver. Interrupted tools/episodes are NEVER replayed."""
from datetime import datetime, timezone
import os
from pathlib import Path

from .admission import pending_plan, validate_binding
from .benchmark import (ASSET_MANIFEST_SHA, REVISION, SCORER_SHA, BenchmarkNPC, export_bundle,
                        load_task, score_episode, verify_assets)
from .contracts import canonical, fingerprint, require, strict_json
from .durable import DurableLedger
from .executor import parse_tool
from .http_transport import HTTPTransport
from .mini_request import MODEL, build_provider_request
from .runtime import SharedRuntime
from .scheduler import ARMS, BenchmarkReference, FourArmScheduler
from .budget import BudgetBlocked

SOURCE_APPROVAL = {"id": "760d5626-c63b-4996-9e1a-2171c5037300", "revision": 2,
                   "user_text": "\u9884\u7b9750\u7f8e\u5143"}
RUN_ID = "study4-v2-rule-ceiling50-20261111-v1"


def now():
    return datetime.now(timezone.utc).isoformat()


def write_new(path, value):
    with path.open("x", encoding="utf-8", newline="\n") as out:
        out.write(canonical(value) + "\n")
        out.flush()
        os.fsync(out.fileno())


def frozen_plan():
    proposal = strict_json((Path(__file__).parent / "configs" / "ceiling_pilot.json").read_bytes())
    verify_assets()
    groups = sorted(((task, repeat) for task in proposal["task_ids"] for repeat in range(2)),
                    key=lambda pair: fingerprint({"seed": 98211, "task_id": pair[0], "repeat": pair[1]}))
    slots = []
    for group, (task, repeat) in enumerate(groups):
        # Outcome-independent rotation balances positions; keep four arms adjacent for usable pairs.
        arms = list(ARMS)
        order = arms[group % 4:] + arms[:group % 4]
        for arm in order:
            slots.append({"slot": len(slots), "group": group, "task_id": task, "repeat": repeat,
                          "arm": arm, "episode_id": f"slot-{len(slots):02d}:{task}:{arm}:r{repeat}"})
    plan = pending_plan()
    plan.update(run_id=RUN_ID, budget_cap_USD="50.00", episodes=[s["episode_id"] for s in slots],
                slots=slots, approval_source=SOURCE_APPROVAL,
                schedule={"version": "v2-balanced-adjacent-four-arm-blocks",
                          "seed": 98211, "repeat_labels_not_provider_random_seeds": [98212, 98213],
                          "change": "Outcome-independent blocked order replaces proposal all-slot hash sort"},
                benchmark={"revision": REVISION, "scorer_sha256": SCORER_SHA,
                           "asset_manifest_sha256": ASSET_MANIFEST_SHA},
                permissions=ARMS, npc="scoped-structured-rule-v1-NOT-original-NL-NPC",
                max_actions=24, fresh_only=True, interrupted_episode_replay=False,
                scope="48 exposed-development ceiling slots, rule NPC, all preflight included; no training/GPU")
    return plan


class Journal:
    def __init__(self, path):
        self.out = path.open("x", encoding="utf-8", newline="\n")

    def append(self, value):
        self.out.write(canonical({"at": now(), **value}) + "\n")
        self.out.flush()
        os.fsync(self.out.fileno())

    def close(self):
        self.out.close()


class PaidMini:
    def __init__(self, ledger, transport, episode_id, journal):
        self.ledger, self.transport, self.episode_id, self.journal = ledger, transport, episode_id, journal
        self.indices = {"control": 0, "question": 0, "ordinary": 0}
        self.failed = False
        self.identity = MODEL + ":frozen-provider-envelope-v1"

    def _call(self, operation, observation, **kwargs):
        require(not self.failed, "No automatic failed-call retry")
        request = build_provider_request(operation, observation, **kwargs)
        index = self.indices[operation]
        self.journal.append({"kind": "model_request", "episode_id": self.episode_id, "operation": operation,
                             "index": index, "request_sha256": fingerprint(request),
                             "public_observation_sha256": fingerprint(observation),
                             "public_request": request})
        try:
            result = self.ledger.call(self.episode_id, operation, index, request, self.transport)
            require(not result["replayed_without_send"], "Fresh batch must never replay a cached tool proposal")
            self.indices[operation] += 1
            self.journal.append({"kind": "model_result", "episode_id": self.episode_id, "operation": operation,
                                 "index": index, "result": result, "budget": self.ledger.status()})
            return result["data"]
        except BaseException:
            self.failed = True
            raise

    def ordinary(self, observation):
        data = self._call("ordinary", observation)
        return parse_tool(canonical({"tool": data["tool"], "arguments": strict_json(data["arguments"])}))

    def control(self, observation, proposed):
        return self._call("control", observation, proposed=proposed)

    def question_plan(self, observation, person_id, assistance=None):
        return self._call("question", observation, person_id=person_id, assistance=assistance)


def run_fresh(root, plan, approval, transport, on_group=None):
    root = Path(root).resolve()
    validate_binding(plan, approval, root, transport.endpoint)
    if plan.get("continuation") is not None:
        from .ceiling_continuation import make_plan
        require(plan["continuation"]["phase"] == "batch" and plan == make_plan(plan["continuation"]),
                "Only exact authorized continuation of frozen48 slots")
    else:
        require(plan == frozen_plan(), "Only exact authorized frozen 48-slot USD50 plan")
    require(not (root / "FRESH_STARTED.json").exists(), "Batch started before; interrupted tools/episodes NEVER replay")
    ledger = DurableLedger(root, plan, approval, create=True)
    journal, rows, current = None, [], None
    status, error_type = "complete", None
    try:
        write_new(root / "FRESH_STARTED.json", {"started": now(), "plan_sha256": fingerprint(plan),
                                              "approval_sha256": fingerprint(approval), "fresh_only": True})
        journal = Journal(root / "events.jsonl")
        for slot in plan["slots"]:
            current = slot
            journal.append({"kind": "episode_start", **slot})
            task = load_task(slot["task_id"])
            mini = PaidMini(ledger, transport, slot["episode_id"], journal)
            runtime = SharedRuntime(task.public, mini, BenchmarkNPC(task), slot["episode_id"],
                                    max_actions=plan["max_actions"])
            scheduler = FourArmScheduler(runtime, mini, slot["arm"], BenchmarkReference(task), now)
            timestamp_sink = runtime.event_sink
            def observed_event(event):
                timestamp_sink(event)
                journal.append({"kind": "runtime_event", "episode_id": slot["episode_id"], "event": event})
            runtime.event_sink = observed_event
            try:
                while not runtime.terminal:
                    scheduler.step()
                    journal.append({"kind": "cycle_complete", "episode_id": slot["episode_id"],
                                     "cycle": scheduler.cycles[-1], "progress": runtime.progress()})
                bundle = export_bundle(runtime, scheduler.timestamps, rule_reviews=True)
                scored = score_episode(task, runtime, bundle)
                record = {"slot": slot, "score": scored, "bundle": bundle, "cycles": scheduler.cycles,
                          "runtime_snapshot_PRIVATE_NOT_MODEL_INPUT": runtime.snapshot(),
                          "model_calls": mini.indices}
                write_new(root / f"slot-{slot['slot']:02d}.json", record)
                row = {**slot, "score": scored, "record_sha256": fingerprint(record),
                       "normal_actions": runtime.normal_actions, "contacts": runtime.contacts,
                       "model_calls": mini.indices}
                rows.append(row)
                journal.append({"kind": "episode_complete", "row": row, "budget": ledger.status()})
                if len(rows) % 4 == 0 and on_group is not None:
                    on_group(rows[-4:], ledger.status())
            except BaseException:
                write_new(root / f"slot-{slot['slot']:02d}-INCOMPLETE.json",
                          {"slot": slot, "business_outcome": None, "cycles": scheduler.cycles,
                           "runtime_snapshot_PRIVATE_NOT_MODEL_INPUT": runtime.snapshot(),
                           "model_calls": mini.indices, "budget": ledger.status()})
                raise
    except BaseException as error:
        status = "budget_stopped" if isinstance(error, BudgetBlocked) and ledger.status()["unknown"] == 0 else "stopped"
        error_type = type(error).__name__
        if journal is not None:
            journal.append({"kind": "batch_stop", "status": status, "error_type": error_type,
                             "business_outcome": None, "slot": current, "budget": ledger.status()})
    finally:
        receipt = {"schema": "study4-v2-ceiling50-actual-1", "run_id": plan["run_id"],
                   "plan_sha256": fingerprint(plan), "status": status, "error_type": error_type,
                   "finished": now(), "completed": rows, "current_slot": current,
                   "budget": ledger.status(), "automatic_retry": False, "fresh_only": True,
                   "episode_tool_exactly_once_proven": False}
        write_new(root / "FINAL_RECEIPT.json", receipt)
        if journal is not None:
            journal.close()
        ledger.close()
    return receipt


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--execute-fresh", action="store_true")
    args = parser.parse_args()
    root = args.root.resolve()
    plan = strict_json((root / "FROZEN_PLAN.json").read_bytes())
    approval = strict_json((root / "APPROVAL.json").read_bytes())
    require(args.execute_fresh, "Explicit fresh execution required; no resume mode")
    validate_binding(plan, approval, root, plan["endpoint"])
    require(plan == frozen_plan() and not (root / "FRESH_STARTED.json").exists()
            and not (root / (plan["run_id"] + ".sqlite3")).exists(), "No started/existing batch may replay")
    key = os.environ.get("OPENAI_API_KEY")
    require(isinstance(key, str) and key, "Explicit process credential injection missing")
    transport = HTTPTransport(plan["endpoint"], plan["mode"], credential=key,
                              timeout=plan["http_timeout_seconds"], max_response_bytes=plan["max_response_bytes"])
    def group_report(rows, budget):
        print(canonical({"kind": "actual_group_complete", "rows": rows, "budget": budget}), flush=True)
    result = run_fresh(root, plan, approval, transport, group_report)
    print(canonical({"kind": "batch_terminal", "status": result["status"],
                     "completed_episodes": len(result["completed"]), "error_type": result["error_type"],
                     "budget": result["budget"]}), flush=True)
