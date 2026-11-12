"""Focused formal-Phase0 behavior checks; every model response here is a mock."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
import json
import hashlib
from pathlib import Path
import tempfile
import unittest

from .admission import prepare_request, root_binding, validate_binding
from .budget import BudgetBlocked
from .contracts import Tool, canonical, fingerprint
from .durable import BatchLock, DurableLedger
from .phase0 import (Phase0Mini, Phase0Runtime, SOURCE, build_request, episode,
                     history_events, load_case, npc_system, public_sources, public_what,
                     restore_public_state, schedule, score_record, verify_inherited, VERSION)
from .phase0_admission import decode_response, make_plan
from .paid_driver import Journal


class MockTransport:
    endpoint = "http://127.0.0.1:9/v1/responses"
    mode = "local_test"

    def __init__(self):
        self.calls = 0

    def send(self, permit, body):
        permit.consume(body, self.endpoint, self.mode)
        request = json.loads(body)
        self.calls += 1
        state = json.loads(request["input"][-1]["content"])["state"]
        workspace = state["workspace"]
        path = state["task"]["artifact_path"]
        if self.calls == 1:
            name, args = "read_file", {"path": "/workspace/missing.md"}
        elif path not in workspace:
            name, args = "write_file", {"path": path, "content": canonical(
                {field: 0 for field in state["task"]["output_fields"]})}
        elif not state["progress"]["posted_current_revision"]:
            name, args = "post_channel", {"channel": "#engineering", "content": "Prepared " + path}
        else:
            name, args = "submit", {"answer": "Delivered " + path}
        return canonical({"model": request["model"], "service_tier": "default", "status": "completed",
                          "id": "mock-" + str(self.calls), "usage": {"input_tokens": 100, "output_tokens": 10},
                          "output": [{"type": "function_call", "name": name, "call_id": str(self.calls),
                                      "arguments": canonical(args)}]}).encode()


class Phase0Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.case = load_case("o-low-team-lunch")
        cls.template = make_plan([], {"unknown_held_USD": "0", "settled_USD_upper": "0"}, local_test=True)

    def authority(self, root, plan):
        now = datetime.now(timezone.utc)
        return {"approved": True, "run_id": plan["run_id"], "plan_sha256": fingerprint(plan),
                "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                "direct_user_source": SOURCE, "scope": "LOCAL_TEST_NOT_PAID_AUTHORIZATION",
                "not_before": now.isoformat(), "expires": (now + timedelta(hours=1)).isoformat(),
                "reference": "mock-only"}

    def test_native_baseline_and_common_ordinary_tools(self):
        obs = Phase0Runtime(self.case, "mock").observe()
        native = build_request("native", obs)
        ordinary = build_request("ordinary", obs)
        self.assertEqual(native["input"][0], ordinary["input"][0])
        self.assertEqual([f for f in native["tools"] if f["name"] != "ask_colleague"], ordinary["tools"])
        self.assertNotIn("choose_help", [f["name"] for f in native["tools"]])
        self.assertEqual(len(native["input"]), 2)

    def test_public_what_invariant_to_private_gold_and_keeps_negation(self):
        runtime = Phase0Runtime(self.case, "mock")
        runtime.history.append({"kind": "read_messages", "message_id": "read1", "person_id": "Chen Xinyi",
                                "content": "ID HR-22 is pending, not an approval. Vegetarian menu."})
        before = runtime.observe()
        expected = public_what(before, "Please confirm the catering needs.")
        changed = deepcopy(self.case)
        changed.blueprint["gold_dag"] = {"nodes": []}
        changed.blueprint["hidden_information"][0]["required_context"] = ["NEVER_OBSERVED_SECRET"]
        changed.blueprint["full_information_reference"] = {"private": "NEVER_OBSERVED_SECRET"}
        other = Phase0Runtime(changed, "mock")
        other.history = deepcopy(runtime.history)
        self.assertEqual(expected, public_what(other.observe(), "Please confirm the catering needs."))
        self.assertIn("not an approval", expected)
        self.assertNotIn("NEVER_OBSERVED_SECRET", expected)

    def test_private_observation_rejected_before_send(self):
        obs = Phase0Runtime(self.case, "mock").observe()
        obs["gold"] = {"secret": 1}
        with self.assertRaises(ValueError):
            prepare_request(build_request("native", obs), "ordinary", self.template)

    def test_missing_file_is_explicit_counted_error_not_infra_failure(self):
        runtime = Phase0Runtime(self.case, "mock")
        runtime._normal(Tool("read_file", (("path", "/workspace/missing.md"),)))
        self.assertFalse(runtime.failed)
        self.assertEqual(runtime.normal_actions, 1)
        self.assertEqual(runtime.history[-1]["error_code"], "FILE_NOT_FOUND")
        self.assertFalse(runtime.history[-1]["applied"])

    def test_mock_fresh_episode_can_correct_tool_error_and_settle_every_call(self):
        with tempfile.TemporaryDirectory() as directory:
            root, plan = Path(directory), deepcopy(self.template)
            authority = self.authority(root, plan)
            ledger = DurableLedger(root, plan, authority, create=True)
            journal = Journal(root / "mock-events.jsonl")
            try:
                slot = next(s for s in plan["slots"] if s["task_id"] == self.case.public.task_id and s["arm"] == "A")
                transport = MockTransport()
                record = episode(self.case, slot, Phase0Mini(ledger, transport, slot, journal), journal)
                self.assertTrue(record["complete"])
                self.assertTrue(record["progress"]["bridge_submitted"])
                self.assertEqual(record["normal_actions"], 4)
                self.assertEqual(transport.calls, 4)
                self.assertEqual(ledger.status()["settled"], 4)
                self.assertEqual(ledger.status()["unknown"], 0)
            finally:
                journal.close()
                ledger.close()

    def test_remaining_below_reserve_and_missing_authority_block(self):
        with tempfile.TemporaryDirectory() as directory:
            root, plan = Path(directory), deepcopy(self.template)
            with self.assertRaises(BudgetBlocked):
                validate_binding(plan, None, root, plan["endpoint"])
            plan["inherited"]["unknown_held_USD"] = "49.2"
            authority = self.authority(root, plan)
            ledger = DurableLedger(root, plan, authority, create=True)
            transport = MockTransport()
            try:
                obs = Phase0Runtime(self.case, "phase0-preflight").observe()
                with self.assertRaises(BudgetBlocked):
                    ledger.call("phase0-preflight", "ordinary", 0, build_request("native", obs), transport)
                self.assertEqual(transport.calls, 0)
                self.assertEqual(ledger.status()["calls"], 0)
            finally:
                ledger.close()

    def test_zero_multiple_and_control_submit_rejected(self):
        obs = Phase0Runtime(self.case, "mock").observe()
        context = {"mode": "native", "person_id": None}
        call = {"type": "function_call", "name": "choose_help", "call_id": "bad",
                "arguments": canonical({"action": "SUBMIT", "person_id": None})}
        for output in ([], [call], [call, call]):
            response = {"model": self.template["price"]["model"], "id": "mock", "status": "completed",
                        "service_tier": "default", "usage": {"input_tokens": 1, "output_tokens": 1},
                        "output": output}
            with self.assertRaises(ValueError):
                decode_response(canonical(response).encode(), "ordinary", obs, context, self.template, 272000)

    def test_npc_is_exact_frozen_natural_policy_and_not_certified_by_tokens(self):
        person = self.case.public.people[0].person_id
        system = npc_system(person, self.case.scenarios[person])
        self.assertIn("Evaluate the meaning of the complete conversation", system)
        self.assertIn(self.case.scenarios[person]["extra_info"], system)
        runtime = Phase0Runtime(self.case, "mock")
        mid = "mock:contact:0:out"
        events = [{"episode_id": "mock", "message_id": mid, "timestamp": "2026-11-12T00:00:00+00:00",
                   "actor": "agent", "colleague": "Chen Xinyi", "room_id": "direct:Chen Xinyi",
                   "content": "Please confirm catering for Search team offsite lunch."},
                  {"episode_id": "mock", "message_id": "mock:contact:0:reply", "in_reply_to": mid,
                   "timestamp": "2026-11-12T00:00:01+00:00", "actor": "npc",
                   "colleague": "Chen Xinyi", "room_id": "direct:Chen Xinyi",
                   "content": "The number 6 is quoted here, not a release or approval."}]
        record = {"complete": True, "slot": {"episode_id": "mock"}, "workspace": runtime.workspace, "events": events}
        self.assertEqual(score_record(self.case, record)["evaluation_status"], "needs_evidence_review")

    def test_all_arms_natural_ask_auto_read_then_one_ordinary_without_extra_control(self):
        class AskTransport(MockTransport):
            def __init__(self):
                super().__init__()
                self.asked = False
                self.agent_bodies = []

            def send(self, permit, body):
                request = json.loads(body)
                if request["tools"]:
                    self.agent_bodies.append(body.decode())
                    data = json.loads(request["input"][-1]["content"])
                    if not self.asked:
                        permit.consume(body, self.endpoint, self.mode)
                        self.calls += 1
                        self.asked = True
                        person = data["person_id"] or "Chen Xinyi"
                        return canonical({"model": request["model"], "service_tier": "default",
                            "status": "completed", "id": "mock-ask", "usage": {"input_tokens": 100, "output_tokens": 20},
                            "output": [{"type": "function_call", "name": "ask_colleague", "call_id": "ask",
                                        "arguments": canonical({"person_id": person, "question":
                                            "For the Search team offsite lunch, please confirm vegetarian needs."})}]}).encode()
                    return super().send(permit, body)
                permit.consume(body, self.endpoint, self.mode)
                self.calls += 1
                return canonical({"model": request["model"], "service_tier": "default",
                    "status": "completed", "id": "mock-npc", "usage": {"input_tokens": 100, "output_tokens": 20},
                    "output": [{"type": "message", "role": "assistant", "content": [
                        {"type": "output_text", "text": "The Search team offsite lunch needs 6 vegetarian meals."}]}]}).encode()
        for arm in "ABCD":
            with self.subTest(arm=arm), tempfile.TemporaryDirectory() as directory:
                root, plan = Path(directory), deepcopy(self.template)
                ledger = DurableLedger(root, plan, self.authority(root, plan), create=True)
                journal = Journal(root / "mock-ask.jsonl")
                try:
                    slot = next(s for s in plan["slots"] if s["task_id"] == self.case.public.task_id and s["arm"] == arm)
                    transport = AskTransport()
                    record = episode(self.case, slot, Phase0Mini(ledger, transport, slot, journal), journal)
                    self.assertTrue(record["complete"])
                    self.assertEqual(record["contacts"], 1)
                    self.assertEqual(record["model_calls"]["npc"], 1)
                    kinds = [e["kind"] for e in record["history"]]
                    self.assertLess(kinds.index("send_message"), kinds.index("read_messages"))
                    self.assertLess(kinds.index("read_messages"), kinds.index("write_file"))
                    self.assertNotIn("choose_help", "".join(transport.agent_bodies))
                    self.assertNotIn("Task-local private records", "".join(transport.agent_bodies))
                    self.assertEqual(ledger.status()["unknown"], 0)
                finally:
                    journal.close()
                    ledger.close()

    def test_full60_balanced_schedule_preserved(self):
        slots = schedule()
        self.assertEqual(len(slots), 720)
        for start in range(0, 720, 4):
            block = slots[start:start+4]
            self.assertEqual({s["arm"] for s in block}, set("ABCD"))
            self.assertEqual(len({(s["task_id"], s["repeat"]) for s in block}), 1)
        for tid in {s["task_id"] for s in slots}:
            case = load_case(tid)
            self.assertEqual(len([s for s in slots if s["task_id"] == tid]), 12)
            self.assertEqual(set(case.scenarios), {p.person_id for p in case.public.people})

    def test_long_dialogue_has_one_event_projection_and_no_requoted_source_history(self):
        runtime = Phase0Runtime(self.case, "growth")
        mini = Phase0Mini(None, None, {"episode_id": "growth"}, None)
        known, quoted_count, previous_size = set(), 0, None
        marker = "\nPublic read-source index (quoted mentions, not new grants):\n"
        for index in range(28):
            mid = f"growth:contact:{index}:out"
            runtime._event("control_decision", action="ASK", person_id="Chen Xinyi")
            runtime._event("send_message", message_id=mid, person_id="Chen Xinyi",
                           content="Please confirm the current request.")
            runtime._event("read_messages", message_id=mid.removesuffix(":out") + ":reply",
                           in_reply_to=mid, person_id="Chen Xinyi",
                           content="ID HR-22 is pending, not an approval. Amount 17." if index < 14 else
                                   "ID HR-22 is approved for amount 23, not amount 17.")
            function = {"type": "function_call", "name": "ask_colleague", "call_id": str(index),
                        "arguments": canonical({"person_id": "Chen Xinyi", "question": "Please confirm."})}
            mini.receipt({"native_function": {"output_items": [function], "call_id": str(index)}},
                         runtime, {"status": "sent_and_read"})
            current = runtime.observe()
            request = build_request("native", current, history=mini.history)
            body = json.loads(request["input"][-1]["content"])
            self.assertEqual(body["state"]["history"], [])
            self.assertEqual(history_events(mini.history), runtime.history)
            self.assertEqual(canonical(restore_public_state(body["state"], mini.history)), canonical(current))
            self.assertEqual(len(history_events(mini.history)), 3 * (index + 1))
            prepare_request(request, "ordinary", self.template)
            question = public_what(current, "Please confirm.", known)
            appendix = json.loads(question.partition(marker)[2])
            quoted_count += len(appendix["new_sources"])
            known.update(s["source_id"] for s in public_sources(current))
            self.assertLessEqual(len(appendix["quoted_values"]), 3)
            if index >= 14:
                self.assertEqual({v["literal"] for v in appendix["quoted_values"]}, {"HR-22", "17", "23"})
            if previous_size is not None:
                self.assertLess(len(canonical(request).encode()) - previous_size, 2000)
            previous_size = len(canonical(request).encode())
        self.assertEqual(quoted_count, 28)
        self.assertEqual(len(public_sources(runtime.observe())), 28)
        self.assertNotIn("not an approval", question)
        self.assertIn("not an approval", canonical(mini.history))
        self.assertIn("not amount 17", canonical(mini.history))
        duplicated = deepcopy(body["state"])
        duplicated["history"] = deepcopy(runtime.history)
        with self.assertRaises(ValueError):
            restore_public_state(duplicated, mini.history)

    def test_identical_approval_words_do_not_merge_different_request_contexts(self):
        runtime = Phase0Runtime(self.case, "contexts")
        for index, amount in enumerate((17, 23)):
            mid = f"contexts:contact:{index}:out"
            runtime._event("send_message", message_id=mid, person_id="Chen Xinyi",
                           content=f"Please approve amount {amount}.")
            runtime._event("read_messages", message_id=mid + ":reply", in_reply_to=mid,
                           person_id="Chen Xinyi", content="Approved.")
        sources = public_sources(runtime.observe())
        self.assertEqual(len(sources), 2)
        self.assertNotEqual(sources[0]["request_context_not_confirmation"],
                            sources[1]["request_context_not_confirmation"])
        self.assertEqual(len(public_sources({"history": runtime.history + [runtime.history[-1]]})), 2)

    def test_agent_draft_is_not_a_confirmed_public_what_source(self):
        runtime = Phase0Runtime(self.case, "draft")
        runtime.workspace[runtime.task.artifact_path] = '{"calculated_total":7317}'
        self.assertEqual(public_what(runtime.observe(), "Please confirm."), "Please confirm.")

    def test_identical_write_keeps_post_valid_but_changed_content_needs_post(self):
        runtime = Phase0Runtime(self.case, "rewrite")
        path = runtime.task.artifact_path
        content = canonical({key: 0 for key in runtime.task.output_fields})
        write = Tool("write_file", (("content", content), ("path", path)))
        post = Tool("post_channel", (("channel", runtime.task.channel), ("content", "Prepared " + path)))
        runtime._normal(write)
        runtime._normal(post)
        for _ in range(6):
            runtime._normal(write)
        self.assertEqual(runtime.artifact_revision, 1)
        self.assertEqual(runtime.normal_actions, 8)
        self.assertEqual(sum(e["kind"] == "write_file" for e in runtime.history), 7)
        self.assertTrue(runtime.progress()["posted_current_revision"])
        runtime._normal(Tool("submit", (("answer", "Delivered"),)))
        self.assertTrue(runtime.progress()["bridge_submitted"])
        self.assertIsNone(runtime.progress()["business_success"])
        changed = Phase0Runtime(self.case, "changed")
        changed._normal(write)
        changed._normal(post)
        changed._normal(Tool("write_file", (("content", content + "\n"), ("path", path))))
        self.assertEqual(changed.artifact_revision, 2)
        changed._normal(Tool("submit", (("answer", "Delivered"),)))
        self.assertFalse(changed.progress()["bridge_submitted"])
        self.assertEqual(changed.history[-1]["kind"], "submission_blocked")
        changed._normal(post)
        changed._normal(Tool("submit", (("answer", "Delivered"),)))
        self.assertTrue(changed.progress()["bridge_submitted"])

    def test_new_provider_protocol_is_pending_not_a_reuse_of_old_paid_authority(self):
        with self.assertRaises(BudgetBlocked):
            make_plan([], {"unknown_held_USD": "0", "settled_USD_upper": "0"})
        with tempfile.TemporaryDirectory() as directory:
            plan = deepcopy(self.template)
            plan["mode"] = "provider"
            with self.assertRaises(BudgetBlocked):
                validate_binding(plan, self.authority(Path(directory), plan), Path(directory), plan["endpoint"])

    def test_historical_lock_hashes_checked_before_and_after_not_while_exclusively_locked(self):
        import sqlite3
        with tempfile.TemporaryDirectory() as directory:
            entries = []
            for index in range(7):
                root = Path(directory) / str(index)
                root.mkdir()
                (root / "prior.lock").write_bytes(b"0")
                db = sqlite3.connect(root / "prior.sqlite3")
                db.execute("create table calls(state,reserved,charged,input_tokens,output_tokens)")
                if index == 0:
                    db.executemany("insert into calls values(?,?,?,?,?)",
                        [("unknown", ".858000", None, None, None)] * 4 +
                        [("settled", ".858000", "0", 0, 0)] * 42 +
                        [("settled", ".858000", ".069303300", 84004, 0)])
                db.commit()
                db.close()
                entries.append({"root": str(root), "file_sha256": {
                    p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir()}})
            before = verify_inherited(entries)
            lock = BatchLock(Path(entries[0]["root"]) / "prior.lock")
            try:
                self.assertEqual(verify_inherited(entries, locked=True), before)
            finally:
                lock.close()
            self.assertEqual(verify_inherited(entries), before)


if __name__ == "__main__":
    unittest.main()
