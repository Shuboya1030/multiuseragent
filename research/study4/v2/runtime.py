"""In-memory shared workspace/message boundary; no scorer or model transports."""
from copy import deepcopy
from dataclasses import asdict
import json

from .contracts import canonical, fingerprint, require, workspace_path
from .executor import PROTOCOL, parse_tool


class ContextOverflow(ValueError):
    pass


class SharedRuntime:
    def __init__(self, task, executor, npc, episode_id, max_actions=24):
        require(task == npc.fixture.task and episode_id and type(max_actions) is int and max_actions > 0,
                "Explicit isolated task/NPC/episode bounds required")
        self.task, self.executor, self.npc = task, executor, npc
        self.episode_id, self.max_actions = episode_id, max_actions
        self.workspace, self.history, self.values = dict(task.documents), [], []
        self.messages, self.seen = {}, set()
        self.normal_actions, self.contacts, self.cost = 0, 0, 0.0
        self.artifact_revision, self.posted_revision = 0, None
        self.answer, self.terminal, self.failed = None, False, False
        self.after_reply = False

    def _event(self, kind, **fields):
        row = {"event_id": f"{self.episode_id}:event:{len(self.history)}", "kind": kind, **fields}
        self.history.append(row)
        return row

    def progress(self):
        raw = self.workspace.get(self.task.artifact_path)
        parsed = None
        if raw is not None:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                pass
        valid = isinstance(parsed, dict) and set(self.task.output_fields) <= set(parsed)
        posted = self.artifact_revision > 0 and self.posted_revision == self.artifact_revision
        return {"artifact_present": raw is not None, "artifact_public_shape_valid": valid,
                "artifact_revision": self.artifact_revision, "posted_current_revision": posted,
                "user_delivery_complete": valid and posted,
                "bridge_submitted": self.answer is not None,
                "business_success": None}

    def observe(self):
        values = deepcopy(self.values)
        for key, operation, source, factor in self.task.calculations:
            inputs = [v for v in values if v["key"] == source and type(v["value"]) in (int, float)]
            if inputs and len({v["value"] for v in inputs}) == 1:
                origin = inputs[-1]
                values.append({"value_id": "calculation:" + fingerprint([key, origin["value_id"], factor]),
                               "key": key, "value": origin["value"] * factor,
                               "source_message_id": None, "source_person_id": None,
                               "source_value_ids": [origin["value_id"]], "source_kind": "public_calculation"})
        return deepcopy({
            "protocol": PROTOCOL,
            "task": {"instruction": self.task.instruction, "people": [asdict(p) for p in self.task.people],
                     "intents": list(self.task.intents), "output_fields": list(self.task.output_fields),
                     "artifact_path": self.task.artifact_path, "channel": self.task.channel,
                     "calculations": list(self.task.calculations)},
            "workspace": self.workspace, "history": self.history, "obtained_values": values,
            "progress": self.progress(), "normal_actions": self.normal_actions,
            "remaining": self.max_actions - self.normal_actions,
            "contact_cost": self.cost, "terminal": self.terminal, "failed": self.failed,
        })

    def boundary_reasons(self, proposed_tool=None):
        reasons = []
        if self.normal_actions == 0:
            reasons.append("start")
        if self.after_reply:
            reasons.append("reply")
        if proposed_tool is not None and proposed_tool.name in {"write_file", "submit"}:
            if proposed_tool.name == "submit" or dict(proposed_tool.arguments).get("path") == self.task.artifact_path:
                reasons.append("deliverable_or_submit_proposal")
        if self.normal_actions > 0 and self.normal_actions % 4 == 0:
            reasons.append("four_ordinary_actions")
        return tuple(reasons)

    def _deliver(self, message):
        message_id = message["message_id"]
        outgoing = self.messages.get(message["in_reply_to"])
        require(outgoing is not None and outgoing.get("sender") == "agent"
                and outgoing["person_id"] == message["person_id"]
                and message_id == message["in_reply_to"].removesuffix(":out") + ":reply",
                "Reply is not bound to an actual tracked outgoing request")
        previous = self.messages.get(message_id)
        require(previous is None or previous == message, "Stable message ID changed")
        self.messages[message_id] = deepcopy(message)
        if message_id in self.seen:
            return
        body = json.loads(message["content"])
        require(set(body) == {"status", "facts", "reason"} and body["status"] in {"released", "refused"}
                and isinstance(body["facts"], dict) and isinstance(body["reason"], str),
                "Invalid rule reply envelope")
        require(body["status"] != "refused" or not body["facts"], "Refusal cannot grant facts")
        self._event("read_messages", **message)
        self.seen.add(message_id)
        if body["status"] == "released":
            for key, value in body["facts"].items():
                require(isinstance(key, str) and type(value) in (str, int, float), "Unsupported public fact")
                self.values.append({"value_id": message_id + ":" + key, "key": key, "value": value,
                                    "source_message_id": message_id, "source_person_id": message["person_id"]})
        self.after_reply = True

    def reread_delivered(self, message_id):
        require(message_id in self.seen, "Cannot read an unknown/pending message")
        self._deliver(deepcopy(self.messages[message_id]))

    def _normal(self, command):
        require(parse_tool(canonical({"tool": command.name, "arguments": dict(command.arguments)})) == command,
                "Invalid or noncanonical ordinary command")
        args = dict(command.arguments)
        if command.name == "write_file":
            path = workspace_path(args["path"])
            self.workspace[path] = args["content"]
            if path == self.task.artifact_path:
                self.artifact_revision += 1
            self._event("write_file", **args)
        elif command.name == "post_channel":
            require(args["channel"] == self.task.channel and args["content"].strip(), "Invalid public channel")
            if (self.artifact_revision > 0 and self.task.artifact_path in args["content"]
                    and args["content"].strip() != self.task.artifact_path):
                self.posted_revision = self.artifact_revision
            self._event("post_channel", **args)
        elif command.name == "submit":
            if not self.progress()["user_delivery_complete"]:
                self._event("submission_blocked", reason="Complete public artifact and current summary first")
            else:
                self.answer, self.terminal = args["answer"], True
                self._event("submit", **args)
        elif command.name == "read_file":
            path = workspace_path(args["path"])
            require(path in self.workspace, "Public file missing")
            self._event("tool_result", tool="read_file", path=path, content=self.workspace[path])
        else:
            self._event("tool_result", tool="list_files", content=canonical(sorted(self.workspace)))
        self.normal_actions += 1
        if self.normal_actions == self.max_actions and not self.terminal:
            self.terminal = True
            self._event("action_limit", bridge_submitted=False)

    def cycle(self, decision):
        require(not self.terminal and not self.failed, "Cannot advance a stopped episode")
        observation = self.observe()
        decision.validate(self.task, observation["obtained_values"])
        self.after_reply = False
        self._event("control_decision", action=decision.action, person_id=decision.person_id)
        try:
            if decision.action == "SUBMIT" and not self.progress()["user_delivery_complete"]:
                self._normal(parse_tool(canonical({"tool": "submit", "arguments": {"answer": ""}})))
                return self.observe()
            if decision.action == "ASK":
                require(self.contacts < self.max_actions, "Contact cap reached")
                selected = [v for v in observation["obtained_values"] if v["value_id"] in decision.include_value_ids]
                question = self.executor.question(observation, decision.person_id, decision.intent, selected)
                request_id = f"{self.episode_id}:contact:{self.contacts}:out"
                self.contacts += 1
                self.cost += next(p.cost for p in self.task.people if p.person_id == decision.person_id)
                self.messages[request_id] = {"message_id": request_id, "sender": "agent",
                                             "person_id": decision.person_id, "content": question}
                self._event("send_message", message_id=request_id, person_id=decision.person_id, content=question)
                reply = self.npc.reply(decision.person_id, question, request_id)
                self._deliver({"message_id": request_id.removesuffix(":out") + ":reply",
                               "in_reply_to": request_id, "person_id": decision.person_id, "content": reply})
            command = self.executor.ordinary(self.observe())
            require(decision.action != "SUBMIT" or command.name == "submit",
                    "SUBMIT requires an executor-produced submission, not a controller answer")
            self._normal(command)
        except Exception as error:
            self.failed = True
            self._event("technical_failure", exception_type=type(error).__name__, business_outcome=None)
            raise
        return self.observe()

    def snapshot(self):
        state = {key: deepcopy(getattr(self, key)) for key in (
            "workspace", "history", "values", "messages", "normal_actions", "contacts", "cost",
            "artifact_revision", "posted_revision", "answer", "terminal", "failed", "after_reply")}
        state["seen"] = sorted(self.seen)
        state["npc"] = self.npc.snapshot()
        body = {"private_snapshot_NOT_model_input": True,
                "binding": fingerprint({"fixture": asdict(self.npc.fixture), "max_actions": self.max_actions,
                                        "episode_id": self.episode_id, "executor": self.executor.identity}),
                "state": state}
        return {**body, "sha256": fingerprint(body)}

    def restore(self, snapshot):
        body = {k: v for k, v in snapshot.items() if k != "sha256"}
        require(snapshot["sha256"] == fingerprint(body) and snapshot["binding"] == self.snapshot()["binding"]
                and snapshot["private_snapshot_NOT_model_input"] is True, "Snapshot binding/hash mismatch")
        state = deepcopy(snapshot["state"])
        require(set(state) == set(self.snapshot()["state"]), "Unknown private snapshot state fields")
        require(type(state["normal_actions"]) is int and 0 <= state["normal_actions"] <= self.max_actions
                and type(state["contacts"]) is int and 0 <= state["contacts"] <= self.max_actions
                and state["cost"] >= 0, "Invalid snapshot counters")
        self.npc.restore(state.pop("npc"))
        self.seen = set(state.pop("seen"))
        for key, value in state.items():
            setattr(self, key, value)


def context_view(observation, count_tokens, limit=6000):
    require(type(limit) is int and limit > 0, "Explicit context limit required")
    view = deepcopy(observation)
    removed = []
    view["context"] = {"omitted_ordinary_event_ids": removed, "lossless_runtime_memory": True}
    while True:
        count = count_tokens(canonical(view))
        require(type(count) is int and count >= 0, "Explicit tokenizer count required")
        if count <= limit:
            return view, {"tokens": count, "limit": limit, "omitted_event_ids": list(removed)}
        candidate = next((i for i, e in enumerate(view["history"][:-1])
                          if e["kind"] in {"write_file", "post_channel", "tool_result", "control_decision"}), None)
        if candidate is None:
            raise ContextOverflow("Protected task/replies/source/progress exceeds context; no truncation fallback")
        removed.append(view["history"].pop(candidate)["event_id"])
