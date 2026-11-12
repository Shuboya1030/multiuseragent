"""Hand-authored dependency proofs, not generated/accepted benchmark tasks."""
import json

from .contracts import Node, Person, PrivateFixture, PublicTask, canonical


def task(name, people, intents, fields, baseline, calculations=()):
    return PublicTask(
        task_id=name,
        instruction="Prepare a current record with " + ", ".join(fields) +
                    ". Save /workspace/deliverable.json and post its path and a summary in #engineering.",
        people=people, documents=(("/workspace/planning.json", canonical(baseline)),),
        intents=intents, output_fields=fields, calculations=calculations,
    )


def fixture_suite():
    owner = Person("owner", "Current record owner", ("current record",), (), 1)
    deputy = Person("deputy", "Delegated record owner", ("current record",), (), 1)
    manager = Person("manager", "Purchase manager", ("purchase",), ("purchase<=10000",), 2)
    director = Person("director", "Purchase director", ("purchase",), ("purchase<=20000",), 3)
    route = Person("routing", "Team routing coordinator", ("active duty route",), (), 1)
    people = (owner, deputy, manager, director, route)
    single = PrivateFixture(
        task("single-info", people, ("current record",), ("record",), {"record": "old"}),
        (Node("record", "current record", ("owner", "deputy"), (("record", "REC-NEW"),)),),
        (("record", "REC-NEW"),), (("record", "old"),), "Must-help")
    chain = PrivateFixture(
        task("info-approval", people, ("current record", "release record"), ("record", "release"),
             {"record": "old", "release": "planning"}),
        (Node("record", "current record", ("owner",), (("record", "REC-NEW"),)),
         Node("release", "release record", ("manager",), (("release", "REL-NEW"),),
              ("record",), (("record", "REC-NEW"),))),
        (("record", "REC-NEW"), ("release", "REL-NEW")),
        (("record", "old"), ("release", "planning")), "Must-help")
    parallel = PrivateFixture(
        task("parallel-join", people, ("current record", "current amount", "release record"),
             ("record", "amount", "release"), {"record": "old", "amount": 10, "release": "planning"}),
        (Node("record", "current record", ("owner",), (("record", "REC-NEW"),)),
         Node("amount", "current amount", ("deputy",), (("amount", 500),)),
         Node("release", "release record", ("manager",), (("release", "REL-JOIN"),),
              ("record", "amount"), (("record", "REC-NEW"), ("amount", 500)))),
        (("record", "REC-NEW"), ("amount", 500), ("release", "REL-JOIN")),
        (("record", "old"), ("amount", 10), ("release", "planning")), "Must-help")
    routed = []
    for name, intent in (("referral", "active owner"), ("delegation", "active deputy")):
        routed.append(PrivateFixture(
            task(name, people, (intent, "current record"), ("active_person", "record"),
                 {"active_person": "old duty", "record": "old"}),
            (Node("route", intent, ("routing",), (("active_person", "deputy"),)),
             Node("record", "current record", ("deputy",), (("record", "REC-DEPUTY"),),
                  ("route",), (("active_person", "deputy"),))),
            (("active_person", "deputy"), ("record", "REC-DEPUTY")),
            (("active_person", "old duty"), ("record", "old")), "Must-help"))
    thresholds = []
    for seats in (10, 20):
        amount = seats * 600
        thresholds.append(PrivateFixture(
            task("threshold-" + str(seats), people, ("current seats", "release purchase"),
                 ("seats", "amount", "release"), {"seats": 16, "amount": 9600, "release": "planning"},
                 calculations=(("amount", "multiply", "seats", 600),)),
            (Node("seats", "current seats", ("owner",), (("seats", seats),)),
             Node("release", "release purchase", ("manager", "director"), (("release", "REL-PURCHASE"),),
                  ("seats",), (("seats", seats), ("amount", amount)), "purchase", amount)),
            (("seats", seats), ("amount", amount), ("release", "REL-PURCHASE")),
            (("seats", 16), ("amount", 9600), ("release", "planning")), "Must-help"))
    optional = []
    for path in ("baseline", "improve"):
        optional_people = (Person("owner", owner.role, owner.knowledge, owner.authority,
                                  20 if path == "baseline" else 1), *people[1:])
        optional.append(PrivateFixture(
            task("optional-" + path, optional_people, ("current record",), ("record",), {"record": "old-valid"}),
            (Node("record", "current record", ("owner",), (("record", "REC-NEW"),)),),
            (("record", "REC-NEW"),), (("record", "old-valid"),), "Optional-help", path))
    return (single, chain, parallel, *routed, *thresholds, *optional)


class PublicFixtureExecutor:
    """Deterministic ordinary executor using only its received public request."""
    def __init__(self):
        self.requests = []

    def __call__(self, request):
        self.requests.append(json.loads(canonical(request)))
        if request["operation"] == "question":
            citation = "; ".join(row["key"] + "=" + str(row["value"]) for row in request["included_values"])
            return canonical({"question": request["intent"] + ". " + citation})
        observation = request["state"]
        task, progress = observation["task"], observation["progress"]
        baseline = json.loads(observation["workspace"]["/workspace/planning.json"])
        values = dict(baseline)
        values.update({row["key"]: row["value"] for row in observation["obtained_values"]
                       if row["key"] in task["output_fields"]})
        expected = canonical(values)
        if observation["workspace"].get(task["artifact_path"]) != expected:
            command = {"tool": "write_file", "arguments": {"path": task["artifact_path"], "content": expected}}
        elif not progress["posted_current_revision"]:
            command = {"tool": "post_channel", "arguments": {
                "channel": task["channel"], "content": "Record prepared: " + task["artifact_path"]}}
        else:
            command = {"tool": "submit", "arguments": {"answer": "Record delivered."}}
        return canonical(command)


def fixture_proof(fixture, runtime):
    raw = runtime.workspace.get(fixture.task.artifact_path)
    try:
        actual = json.loads(raw) if raw is not None else None
    except json.JSONDecodeError:
        actual = None
    full = dict(fixture.full_reference)
    baseline = dict(fixture.baseline_reference)
    full_match = isinstance(actual, dict) and all(actual.get(k) == v for k, v in full.items())
    baseline_match = isinstance(actual, dict) and all(actual.get(k) == v for k, v in baseline.items())
    releases = runtime.npc.released == {n.node_id for n in fixture.nodes}
    content = (full_match and releases) if fixture.help_class == "Must-help" else (
        baseline_match or (full_match and releases))
    progress = runtime.progress()
    return {"checker": "local-fixture-proof-v1-NOT-TribalBench",
            "content_valid": content, "full_reference_and_release_match": full_match and releases,
            "user_delivery_complete": progress["user_delivery_complete"],
            "bridge_submitted": progress["bridge_submitted"],
            "proof_complete": content and progress["user_delivery_complete"] and progress["bridge_submitted"]}
