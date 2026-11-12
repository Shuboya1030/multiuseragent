"""Pinned MIT benchmark assets; private scorer and scoped rule-NPC adapters."""
from copy import deepcopy
from dataclasses import dataclass
import hashlib
import importlib.util
import json
from pathlib import Path
import re

from .contracts import Node, Person, PrivateFixture, PublicTask, canonical, fingerprint, require
from .npc_rule import contains_value

VENDOR = Path(__file__).parent / "vendor" / "tribalbench"
REVISION = "4260bdc626548f59042f318cdf0566490e91b9d5"
SCORER_SHA = "e6b47e4a251bdc44d2fbfe389e12b81273e6472092958fe04e33297f28a33e78"
ASSET_MANIFEST_SHA = "0182abb6c0a1ad6bcfd77394e56a495607d7784d02ac5ce874c22db0de32f2b6"


def verify_assets(root=VENDOR):
    raw_manifest = (root / "SOURCE_MANIFEST.json").read_bytes()
    require(hashlib.sha256(raw_manifest).hexdigest() == ASSET_MANIFEST_SHA, "Asset manifest binding changed")
    manifest = json.loads(raw_manifest)
    require(manifest["revision"] == REVISION and manifest["license"] == "MIT", "Wrong source binding")
    for path, expected in manifest["files"].items():
        require(not Path(path).is_absolute() and ".." not in Path(path).parts, "Unsafe source path")
        raw = root.joinpath(*path.split("/")).read_bytes()
        require(len(raw) == expected["bytes"] and hashlib.sha256(raw).hexdigest() == expected["sha256"],
                "Pinned source/data bytes changed: " + path)
    require(manifest["files"]["scorer/scorer.py"]["sha256"] == SCORER_SHA, "Wrong scorer source")
    return manifest


def official_scorer():
    verify_assets()
    spec = importlib.util.spec_from_file_location("study4_pinned_tribalbench", VENDOR / "scorer" / "scorer.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    require(module.GRADER_VERSION == "tribalbench-1.0", "Unexpected scorer version")
    return module


@dataclass(frozen=True)
class BenchmarkTask:
    public: PublicTask
    blueprint: dict
    costs: dict


def load_task(task_id):
    """Public fields are parsed exclusively from public files, never blueprint metadata."""
    manifest = verify_assets()
    prefix = f"tasks/{task_id}/"
    require(prefix + "public/instruction.md" in manifest["files"], "Task outside frozen exposed six")
    root = VENDOR / "tasks" / task_id
    instruction = (root / "public" / "instruction.md").read_text(encoding="utf-8").strip()
    match = re.search(r"with (.+?)\.\s+Post", instruction)
    require(match is not None, "Public output contract needs explicit adapter review")
    fields = tuple(re.split(r",\s*|\s+and\s+", match[1]))
    directory = (root / "public" / "documents" / "directory.md").read_text(encoding="utf-8")
    people = []
    for block in directory.split("\n## ")[1:]:
        name, role, *rest = block.strip().splitlines()
        cost = 3 if re.search(r"\b(CTO|Director)\b", role) else (2 if "Manager" in role else 1)
        people.append(Person(name, role, ("\n".join(rest).strip(),), (), cost))
    require(people and all(re.fullmatch(r"[a-z_]+", field) for field in fields), "Invalid public parsing")
    documents = tuple(("/workspace/" + p.name, p.read_text(encoding="utf-8"))
                      for p in sorted((root / "public" / "documents").glob("*.md")))
    calculations = ()
    text = "\n".join(t for _, t in documents)
    if "total_usd" in fields and "per seat annually" in text:
        rate = re.search(r"USD (\d+) per seat annually", text)
        require(rate is not None, "Public annual price missing")
        calculations = (("total_usd", "multiply", "seats", int(rate[1])),)
    if "amount_usd" in fields and "/hour" in text:
        rate = re.search(r"USD (\d+)/hour", text)
        require(rate is not None, "Public hourly price missing")
        calculations = (("amount_usd", "multiply", "hours", int(rate[1])),)
    public = PublicTask(task_id, instruction, tuple(people), documents,
                        tuple("request " + field for field in fields), fields, calculations=calculations)
    bp = json.loads((root / "gold" / "blueprint.json").read_bytes())
    costs = json.loads((root / "gold" / "colleague_costs.json").read_bytes())
    require(all(costs[p.person_id] == p.cost for p in people), "Public price reconstruction differs from pinned costs")
    return BenchmarkTask(public, bp, costs)


def runtime_fixture(task):
    """Compatibility container only; BenchmarkNPC enforces actual upstream context strings."""
    bp = task.blueprint
    hidden = {h["id"]: h for h in bp["hidden_information"]}
    nodes = []
    for node in bp["gold_dag"]["nodes"]:
        facts = {}
        for hid in node["information_ids"]:
            facts.update(hidden[hid]["facts"])
        targets = [k for k in facts if k in task.public.output_fields]
        require(targets, "No public request field for private node; adapter is incomplete")
        nodes.append(Node(node["id"], "request " + targets[0], tuple(node["admissible_recipients"]),
                          tuple(facts.items()), tuple(node["requires"])))
    return PrivateFixture(task.public, tuple(nodes), tuple(bp["full_information_reference"].items()),
                          tuple(bp["no_contact_reference"].items()), bp["help_class"])


class BenchmarkNPC:
    """New scoped structured rule environment, NOT the original natural-language NPC."""
    def __init__(self, task):
        self.task = task
        self.fixture = runtime_fixture(task)
        self.released, self.receipts = set(), []

    def reply(self, person_id, question, request_id):
        require(person_id in {p.person_id for p in self.task.public.people}, "Unknown benchmark NPC")
        require(all(r["request_id"] != request_id for r in self.receipts), "Duplicate rule request")
        intent = next((i for i in self.task.public.intents if question.startswith(i + ".")), None)
        require(intent is not None, "Structured public intent prefix required; no NL equivalence claim")
        requested = intent.removeprefix("request ")
        hidden = {h["id"]: h for h in self.task.blueprint["hidden_information"]}
        before, released, facts = set(self.released), [], {}
        for node in self.task.blueprint["gold_dag"]["nodes"]:
            records = [hidden[h] for h in node["information_ids"]]
            node_facts = {k: v for record in records for k, v in record["facts"].items()}
            if person_id not in node["admissible_recipients"] or requested not in node_facts:
                continue
            contexts = [x for record in records for x in record["required_context"]]
            if not set(node["requires"]) <= before or not all(contains_value(question, x) for x in contexts):
                continue
            require(not facts.keys() & node_facts.keys(), "Ambiguous simultaneous benchmark release")
            facts.update(node_facts)
            released.append(node["id"])
        self.released.update(released)
        reply = canonical({"status": "released" if released else "refused", "facts": facts,
                           "reason": "Requested record released." if released else
                                     "Request not releasable; check public scope, context and prior replies."})
        self.receipts.append({"request_id": request_id, "person_id": person_id,
                              "request_sha256": hashlib.sha256(question.encode()).hexdigest(),
                              "reply_sha256": hashlib.sha256(reply.encode()).hexdigest(),
                              "released_node_ids": released, "requested_field": requested,
                              "before": sorted(before), "environment": "scoped-structured-rule-v1"})
        return reply

    def snapshot(self):
        return {"released": sorted(self.released), "receipts": deepcopy(self.receipts)}

    def restore(self, state):
        require(set(state) == {"released", "receipts"} and
                set(state["released"]) <= {n.node_id for n in self.fixture.nodes}, "Invalid benchmark state")
        self.released, self.receipts = set(state["released"]), deepcopy(state["receipts"])


def export_bundle(runtime, timestamps, rule_reviews=False):
    """Explicit message timestamps required; no invented clock for a real episode."""
    events = []
    for event in runtime.history:
        if event["kind"] not in {"send_message", "read_messages"}:
            continue
        mid = event["message_id"]
        require(mid in timestamps, "Missing observed message timestamp")
        row = {"episode_id": runtime.episode_id, "message_id": mid, "timestamp": timestamps[mid],
               "actor": "agent" if event["kind"] == "send_message" else "npc",
               "colleague": event["person_id"], "room_id": "direct:" + event["person_id"],
               "content": event["content"]}
        if row["actor"] == "npc":
            row["in_reply_to"] = event["in_reply_to"]
        events.append(row)
    bundle = {"task_id": runtime.task.task_id, "episode_id": runtime.episode_id,
              "complete": runtime.terminal and not runtime.failed, "events": events, "evidence_reviews": []}
    if rule_reviews:
        require(type(runtime.npc) is BenchmarkNPC, "Cannot certify natural-language NPC as rule evidence")
        by_id = {e["message_id"]: e for e in events}
        bp = runtime.npc.task.blueprint
        hidden = {h["id"]: h for h in bp["hidden_information"]}
        for receipt in runtime.npc.receipts:
            request = by_id[receipt["request_id"]]
            reply = by_id[receipt["request_id"].removesuffix(":out") + ":reply"]
            require(hashlib.sha256(request["content"].encode()).hexdigest() == receipt["request_sha256"] and
                    hashlib.sha256(reply["content"].encode()).hexdigest() == receipt["reply_sha256"],
                    "Rule receipt no longer binds actual message bytes")
            body = json.loads(reply["content"])
            expected_facts = {k: v for n in bp["gold_dag"]["nodes"] if n["id"] in receipt["released_node_ids"]
                              for hid in n["information_ids"] for k, v in hidden[hid]["facts"].items()}
            require(body["facts"] == expected_facts, "Rule release facts changed")
            for node in bp["gold_dag"]["nodes"]:
                if receipt["person_id"] not in node["admissible_recipients"]:
                    continue
                accepted = node["id"] in receipt["released_node_ids"]
                targeted = any(receipt["requested_field"] in hidden[h]["facts"] for h in node["information_ids"])
                bundle["evidence_reviews"].append({
                    "node_id": node["id"], "message_id": reply["message_id"], "request_id": request["message_id"],
                    "decision": "accept" if accepted else "reject",
                    "reviewer": "deterministic-structured-rule-v1-NOT-human-NL-review",
                    "reason": "Exact environment release receipt" if accepted else "No release for this node",
                    "is_refusal": targeted and not accepted,
                    "content_sha256": receipt["reply_sha256"],
                    "request_content_sha256": receipt["request_sha256"],
                })
    return bundle


def score_episode(task, runtime, bundle):
    require(not runtime.failed and runtime.terminal, "Infra/incomplete episode cannot become business failure")
    require(bundle["episode_id"] == runtime.episode_id and bundle["task_id"] == task.public.task_id,
            "Scorer episode/task mismatch")
    timestamps = {event["message_id"]: event.get("timestamp") for event in bundle["events"]}
    expected = export_bundle(runtime, timestamps)["events"]
    require(bundle["events"] == expected, "Scorer trace differs from actual runtime history")
    raw = runtime.workspace.get(task.public.artifact_path)
    try:
        artifact = json.loads(raw) if raw is not None else None
    except json.JSONDecodeError:
        artifact = None
    scorer = official_scorer()
    result = scorer.score_bundle(task.blueprint, artifact, bundle, task.costs)
    return {"scorer_revision": REVISION, "scorer_source_sha256": SCORER_SHA,
            "input_fingerprint": fingerprint({"blueprint": task.blueprint, "artifact": artifact,
                                               "bundle": bundle, "costs": task.costs}),
            "official": result, "user_delivery_complete": runtime.progress()["user_delivery_complete"],
            "bridge_submitted": runtime.progress()["bridge_submitted"],
            "episode_status": "needs_evidence_review" if result["evaluation_status"] != "scored" else "scored",
            "eligible_for_confirmatory_metrics": result["evaluation_status"] == "scored"}
