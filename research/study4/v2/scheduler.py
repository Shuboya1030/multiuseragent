"""Coalesced shared proposals; privileged policy/what stay outside public requests."""
from dataclasses import asdict

from .contracts import Decision, fingerprint, require
from .npc_rule import contains_value

ARMS = {
    "A": {"private_when_whom": False, "private_what": False},
    "B": {"private_when_whom": True, "private_what": False},
    "C": {"private_when_whom": False, "private_what": True},
    "D": {"private_when_whom": True, "private_what": True},
}


class BenchmarkReference:
    """Greedy DAG reference; Optional improve path, not a proved utility optimum."""
    def __init__(self, task):
        self.task = task

    def ready(self, person_id, released):
        return [n for n in self.task.blueprint["gold_dag"]["nodes"]
                if n["id"] not in released and set(n["requires"]) <= set(released) and
                (person_id is None or person_id in n["admissible_recipients"])]

    def choose(self, observation, released):
        ready = self.ready(None, released)
        if not ready:
            require(len(released) == len(self.task.blueprint["gold_dag"]["nodes"]),
                    "Reference has no feasible next step")
            return {"action": "SELF", "person_id": None}
        people = {p["person_id"]: p for p in observation["task"]["people"]}
        recipient = min((p for n in ready for p in n["admissible_recipients"]),
                        key=lambda p: (people[p]["cost"], p))
        return {"action": "ASK", "person_id": recipient}

    def what(self, observation, person_id, released):
        ready = self.ready(person_id, released)
        if not ready:
            return None
        node = ready[0]
        hidden = {h["id"]: h for h in self.task.blueprint["hidden_information"]}
        records = [hidden[h] for h in node["information_ids"]]
        field = next((k for h in records for k in h["facts"] if k in observation["task"]["output_fields"]), None)
        require(field is not None, "Privileged what has no public intent")
        # Only IDs of values already in the public observation may cross this boundary.
        contexts = [x for h in records for x in h["required_context"]]
        selected = [v["value_id"] for v in observation["obtained_values"]
                    if any(contains_value(str(v["value"]), x) for x in contexts)]
        return {"intent": "request " + field, "include_value_ids": selected}


class FourArmScheduler:
    def __init__(self, runtime, mini, arm, reference=None, clock=None):
        require(arm in ARMS and runtime.executor is mini, "Shared mini executor identity required")
        require(callable(clock), "Explicit observed/synthetic clock required")
        require(not (ARMS[arm]["private_when_whom"] or ARMS[arm]["private_what"]) or reference is not None,
                "Privileged arm requires private reference")
        self.runtime, self.mini, self.arm, self.reference, self.clock = runtime, mini, arm, reference, clock
        self.cycles, self.timestamps = [], {}
        self.failed = False
        require(runtime.event_sink is None and not runtime.history, "Fresh event observer required; do not invent past times")
        runtime.event_sink = self._observe_event

    def _observe_event(self, event):
        if event["kind"] in {"send_message", "read_messages"}:
            require(event["message_id"] not in self.timestamps, "Duplicate message observation")
            self.timestamps[event["message_id"]] = self.clock()

    def step(self):
        rt = self.runtime
        require(not self.failed and not rt.terminal and not rt.failed, "Stopped schedule; do not retry")
        start = rt.observe()
        try:
            # At most one proposal, one coalesced decision, one question and one refreshed ordinary.
            proposal = self.mini.ordinary(start)
            reasons = rt.boundary_reasons(proposal)
            base = {"action": "SELF", "person_id": None}
            control_called = False
            if reasons:
                if ARMS[self.arm]["private_when_whom"]:
                    base = self.reference.choose(start, rt.npc.released)
                else:
                    base = self.mini.control(start, proposal)
                    control_called = True
            require(fingerprint(rt.observe()) == fingerprint(start), "Proposal/controller mutated runtime")
            decision, question, assistance = Decision(base["action"], base["person_id"]), None, None
            assistance_status = "not_requested"
            if base["action"] == "ASK":
                if ARMS[self.arm]["private_what"]:
                    assistance = self.reference.what(start, base["person_id"], rt.npc.released)
                    assistance_status = "obtained_only" if assistance is not None else "no_ready_node_public_fallback"
                plan = self.mini.question_plan(start, base["person_id"], assistance)
                decision = Decision("ASK", base["person_id"], plan["intent"], tuple(plan["include_value_ids"]))
                question = plan["question"]
            require(fingerprint(rt.observe()) == fingerprint(start), "Question planner mutated runtime")
            decision.validate(rt.task, start["obtained_values"])
            rt.cycle(decision, proposed_tool=None if decision.action == "ASK" else proposal, question=question)
            self.cycles.append({
                "cycle": len(self.cycles), "arm": self.arm, "public_before_sha256": fingerprint(start),
                "boundary_reasons": list(reasons), "public_controller_called": control_called,
                "private_when_whom_used": bool(reasons) and ARMS[self.arm]["private_when_whom"],
                "what_assistance_status": assistance_status, "decision": asdict(decision),
                "proposal": asdict(proposal), "proposal_discarded": decision.action == "ASK",
                "public_after_sha256": fingerprint(rt.observe()),
            })
        except Exception as error:
            self.failed, rt.failed = True, True
            rt._event("technical_failure", exception_type=type(error).__name__, business_outcome=None)
            raise
        return rt.observe()

    def run(self):
        while not self.runtime.terminal:
            self.step()
        return self.runtime.observe()
