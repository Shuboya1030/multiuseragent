import json
from copy import deepcopy
from dataclasses import replace
from decimal import Decimal
from pathlib import Path
import unittest

from .contracts import Decision, Node, Person, PrivateFixture, Tool, canonical, fingerprint
from .executor import SharedExecutor, ordinary_request, parse_tool
from .fixtures import PublicFixtureExecutor, fixture_proof, fixture_suite
from .npc_rule import RuleNPC, contains_field, contains_value
from .oracle import DAGReference, identifiability_audit, validate_public_observation
from .runtime import ContextOverflow, SharedRuntime, context_view
from .local_acceptance import run_suite


def runtime(fixture, callback=None, episode="fixture", limit=24):
    callback = callback or PublicFixtureExecutor()
    return SharedRuntime(fixture.task, SharedExecutor(callback), RuleNPC(fixture), episode, limit)


def finish(rt):
    reference = DAGReference(rt.npc.fixture)
    while not rt.terminal:
        rt.cycle(reference.choose(rt.observe(), rt.npc.released))
    return fixture_proof(rt.npc.fixture, rt)


class ProtocolTests(unittest.TestCase):
    def test_reference_paths_and_public_label_compatibility(self):
        audit_rows = []
        for fixture in fixture_suite():
            with self.subTest(fixture=fixture.task.task_id):
                rt = runtime(fixture)
                ref = DAGReference(fixture)
                while not rt.terminal:
                    obs = rt.observe()
                    validate_public_observation(obs)
                    labels = ref.acceptable(obs, rt.npc.released)
                    audit_rows.append((obs, labels))
                    rt.cycle(labels[0])
                self.assertTrue(fixture_proof(fixture, rt)["proof_complete"])
                self.assertLessEqual(rt.normal_actions, 24)
        self.assertTrue(all(row["status"] == "compatible" for row in identifiability_audit(audit_rows)))

    def test_self_can_submit_but_must_complete_delivery_first(self):
        fixture = fixture_suite()[-2]
        rt = runtime(fixture)
        for _ in range(3):
            rt.cycle(Decision("SELF"))
        self.assertTrue(rt.progress()["user_delivery_complete"])
        self.assertTrue(rt.progress()["bridge_submitted"])
        self.assertEqual(rt.contacts, 0)
        self.assertTrue(fixture_proof(fixture, rt)["proof_complete"])

    def test_information_complete_is_not_delivery_or_business_success(self):
        fixture = fixture_suite()[0]
        rt = runtime(fixture, lambda request: canonical({"tool": "list_files", "arguments": {}})
                     if request["operation"] == "ordinary" else canonical({"question": "current record"}))
        rt.cycle(Decision("ASK", "owner", "current record"))
        self.assertEqual(rt.npc.released, {"record"})
        before_calls = rt.executor.calls
        with self.assertRaisesRegex(ValueError, "help-only"):
            rt.cycle(Decision("SUBMIT"))
        self.assertEqual(rt.executor.calls, before_calls)
        self.assertFalse(rt.terminal)
        self.assertFalse(rt.progress()["user_delivery_complete"])
        self.assertFalse(any(row["kind"] == "submission_blocked" for row in rt.history))
        self.assertIsNone(rt.progress()["business_success"])

    def test_ask_delivers_before_exactly_one_ordinary_action(self):
        rt = runtime(fixture_suite()[0])
        rt.cycle(Decision("ASK", "owner", "current record"))
        kinds = [row["kind"] for row in rt.history]
        self.assertEqual(kinds, ["control_decision", "send_message", "read_messages", "write_file"])
        self.assertEqual(rt.normal_actions, 1)
        self.assertEqual(rt.executor.calls, 2)
        self.assertEqual(rt.cost, 1)
        self.assertEqual(rt.values[0]["source_person_id"], "owner")
        self.assertEqual(rt.values[0]["source_message_id"], rt.history[2]["message_id"])
        request = rt.executor.generate.requests[-1]
        self.assertTrue(request["state"]["obtained_values"])
        self.assertIn("reply", rt.boundary_reasons())

    def test_partial_reply_and_refusal_can_recover(self):
        rt = runtime(fixture_suite()[1])
        rt.cycle(Decision("ASK", "manager", "release record"))
        self.assertFalse(rt.npc.released)
        self.assertFalse(rt.values)
        refusal = json.loads(rt.history[2]["content"])
        self.assertEqual(refusal["status"], "refused")
        self.assertNotIn("REC-NEW", refusal["reason"])
        rt.cycle(Decision("ASK", "owner", "current record"))
        self.assertEqual(rt.npc.released, {"record"})
        rt.cycle(Decision("ASK", "manager", "release record"))
        self.assertEqual(rt.npc.released, {"record"})
        self.assertIn("record", json.loads(rt.history[-2]["content"])["reason"])
        self.assertTrue(finish(rt)["proof_complete"])
        self.assertEqual(rt.npc.released, {"record", "release"})
        self.assertEqual(rt.contacts, 4)

    def test_repeated_read_is_idempotent_and_edited_identity_rejected(self):
        rt = runtime(fixture_suite()[0])
        rt.cycle(Decision("ASK", "owner", "current record"))
        message = deepcopy(rt.messages[next(iter(rt.seen))])
        length, values = len(rt.history), deepcopy(rt.values)
        rt.reread_delivered(message["message_id"])
        rt.reread_delivered(message["message_id"])
        self.assertEqual(len(rt.history), length)
        self.assertEqual(rt.values, values)
        message["content"] = canonical({"status": "released", "facts": {"record": "CHANGED"}, "reason": ""})
        with self.assertRaisesRegex(ValueError, "Stable message"):
            rt._deliver(message)
        with self.assertRaisesRegex(ValueError, "unknown"):
            rt.reread_delivered("never-read")

    def test_repeated_post_keeps_history_and_rewrite_invalidates_summary(self):
        commands = iter([
            {"tool": "write_file", "arguments": {"path": "/workspace/deliverable.json", "content": '{"record":"old"}'}},
            *[{"tool": "post_channel", "arguments": {"channel": "#engineering",
                                                   "content": "Record: /workspace/deliverable.json"}}] * 2,
            {"tool": "write_file", "arguments": {"path": "/workspace/deliverable.json", "content": '{"record":"new"}'}},
            {"tool": "submit", "arguments": {"answer": "done"}},
        ])
        rt = runtime(fixture_suite()[0], lambda request: canonical(next(commands)))
        for _ in range(3):
            rt.cycle(Decision("SELF"))
        self.assertTrue(rt.progress()["posted_current_revision"])
        self.assertEqual(sum(r["kind"] == "post_channel" for r in rt.history), 2)
        rt.cycle(Decision("SELF"))
        self.assertFalse(rt.progress()["posted_current_revision"])
        rt.cycle(Decision("SELF"))
        self.assertFalse(rt.terminal)
        self.assertEqual(rt.history[-1]["kind"], "submission_blocked")
        self.assertEqual(sum(r["kind"] == "post_channel" for r in rt.history), 2)

    def test_bad_artifact_can_finish_delivery_without_business_success(self):
        rt = runtime(fixture_suite()[0])
        for _ in range(3):
            rt.cycle(Decision("SELF"))
        self.assertTrue(rt.progress()["bridge_submitted"])
        self.assertFalse(fixture_proof(rt.npc.fixture, rt)["content_valid"])
        self.assertIsNone(rt.progress()["business_success"])

    def test_all_arms_share_identical_ordinary_request_and_schema(self):
        fixture = fixture_suite()[0]
        states = [runtime(fixture, episode="same").observe() for _ in "ABCD"]
        requests = [ordinary_request(state) for state in states]
        self.assertTrue(all(row == requests[0] for row in requests))
        self.assertNotIn("arm", requests[0])
        self.assertNotIn("send_message", requests[0]["tools"])
        self.assertNotIn("read_messages", requests[0]["tools"])

    def test_illegal_tools_or_controller_private_fields_fail_explicitly(self):
        rt = runtime(fixture_suite()[0], lambda request: '{"tool":"send_message","arguments":{}}')
        with self.assertRaisesRegex(ValueError, "forbidden"):
            rt.cycle(Decision("SELF"))
        self.assertTrue(rt.failed)
        self.assertEqual(rt.history[-1]["kind"], "technical_failure")
        self.assertIsNone(rt.history[-1]["business_outcome"])
        with self.assertRaises(ValueError):
            Decision("ASK", "owner", "current record", ("unread-fact",)).validate(rt.task, [])
        with self.assertRaises(ValueError):
            Decision("SUBMIT", "owner").validate(rt.task, [])
        for forbidden in ("gold_dag", "required_context", "help_class", "score"):
            obs = rt.observe()
            obs["task"][forbidden] = "PRIVATE"
            with self.assertRaises(ValueError):
                validate_public_observation(obs)

    def test_no_private_values_before_release_and_source_conflicts_retained(self):
        rt = runtime(fixture_suite()[0])
        before = canonical(rt.observe())
        self.assertNotIn("REC-NEW", before)
        self.assertNotIn("node_id", before)
        rt.cycle(Decision("ASK", "owner", "current record"))
        first = rt.values[0]["value_id"]
        rt.npc.fixture = replace(rt.npc.fixture, nodes=(replace(rt.npc.fixture.nodes[0],
                                                               facts=(("record", "OTHER"),)),))
        rt.cycle(Decision("ASK", "deputy", "current record"))
        self.assertEqual([v["value"] for v in rt.values], ["REC-NEW", "OTHER"])
        self.assertNotEqual(first, rt.values[1]["value_id"])

    def test_question_cannot_drop_selected_context(self):
        rt = runtime(fixture_suite()[1])
        rt.cycle(Decision("ASK", "owner", "current record"))
        label = DAGReference(rt.npc.fixture).choose(rt.observe(), rt.npc.released)
        rt.executor.generate = lambda request: canonical({"question": "release record"})
        with self.assertRaisesRegex(ValueError, "lost included"):
            rt.cycle(label)
        self.assertEqual(rt.contacts, 1)
        self.assertEqual(rt.npc.released, {"record"})

    def test_threshold_arithmetic_source_and_authority(self):
        fixture = next(f for f in fixture_suite() if f.task.task_id == "threshold-20")
        rt = runtime(fixture)
        rt.cycle(Decision("ASK", "owner", "current seats"))
        calc = next(v for v in rt.observe()["obtained_values"] if v["key"] == "amount")
        self.assertEqual(calc["value"], 12000)
        self.assertEqual(calc["source_kind"], "public_calculation")
        self.assertEqual(calc["source_value_ids"], [rt.values[0]["value_id"]])
        wrong = rt.npc.reply("manager", "release purchase; seats=20; amount=12000", "wrong")
        self.assertEqual(json.loads(wrong)["status"], "refused")
        self.assertTrue(finish(rt)["proof_complete"])
        self.assertEqual(rt.contacts, 2)

    def test_private_snapshot_branch_restore_without_double_contact_or_replay(self):
        rt = runtime(fixture_suite()[1])
        rt.cycle(Decision("ASK", "owner", "current record"))
        snapshot = rt.snapshot()
        self.assertTrue(finish(rt)["proof_complete"])
        final = rt.snapshot()
        rt.restore(snapshot)
        self.assertEqual(rt.contacts, 1)
        self.assertTrue(finish(rt)["proof_complete"])
        self.assertEqual(rt.snapshot(), final)
        tampered = deepcopy(snapshot)
        tampered["state"]["cost"] = 0
        with self.assertRaisesRegex(ValueError, "hash"):
            rt.restore(tampered)
        other = runtime(fixture_suite()[1], episode="different")
        with self.assertRaisesRegex(ValueError, "binding"):
            other.restore(snapshot)

    def test_ambiguous_public_states_do_not_get_unique_private_labels(self):
        fixture = fixture_suite()[0]
        other = replace(fixture, nodes=(replace(fixture.nodes[0], recipients=("director",)),))
        a, b = runtime(fixture), runtime(other)
        audit = identifiability_audit([
            (a.observe(), DAGReference(fixture).acceptable(a.observe(), set())),
            (b.observe(), DAGReference(other).acceptable(b.observe(), set())),
        ])
        self.assertEqual(audit[0]["status"], "unidentifiable")
        self.assertFalse(audit[0]["unique_label"])
        self.assertEqual(audit[0]["shared_acceptable_label_fingerprints"], [])
        same = identifiability_audit([(a.observe(), DAGReference(fixture).acceptable(a.observe(), set()))])
        self.assertEqual(same[0]["status"], "compatible")
        self.assertFalse(same[0]["unique_label"])

    def test_context_protects_replies_and_summary_and_fails_if_protected_overflows(self):
        rt = runtime(fixture_suite()[0])
        rt.cycle(Decision("ASK", "owner", "current record"))
        observation = rt.observe()
        count = len
        for _ in range(10):
            observation["history"].insert(0, {"event_id": "old" + str(_), "kind": "post_channel",
                                              "content": "x" * 100})
        full = canonical(observation)
        view, receipt = context_view(observation, count, len(full) - 500)
        self.assertTrue(receipt["omitted_event_ids"])
        self.assertEqual(view["obtained_values"], observation["obtained_values"])
        self.assertEqual(view["progress"], observation["progress"])
        self.assertTrue(any(e["kind"] == "read_messages" for e in view["history"]))
        self.assertEqual(len(observation["history"]), len(rt.history) + 10)
        with self.assertRaises(ContextOverflow):
            context_view(observation, count, 1)
        with self.assertRaises(ValueError):
            context_view(observation, lambda text: True)

    def test_decision_points_include_proposal_reply_and_four_step_guard(self):
        rt = runtime(fixture_suite()[0], lambda request: canonical({"tool": "list_files", "arguments": {}}))
        self.assertEqual(rt.boundary_reasons(), ("start",))
        for _ in range(4):
            rt.cycle(Decision("SELF"))
        self.assertIn("four_ordinary_actions", rt.boundary_reasons())
        proposal = parse_tool('{"tool":"write_file","arguments":{"path":"/workspace/deliverable.json","content":"{}"}}')
        self.assertIn("deliverable_or_submit_proposal", rt.boundary_reasons(proposal))

    def test_bounded_stops_are_not_submitted_and_cyclic_dag_is_rejected(self):
        rt = runtime(fixture_suite()[0], lambda request: '{"tool":"list_files","arguments":{}}', limit=2)
        rt.cycle(Decision("SELF"))
        rt.cycle(Decision("SELF"))
        self.assertTrue(rt.terminal)
        self.assertFalse(rt.progress()["bridge_submitted"])
        self.assertEqual(rt.history[-1]["kind"], "action_limit")
        with self.assertRaises(ValueError):
            rt.cycle(Decision("SELF"))
        with self.assertRaisesRegex(ValueError, "Cyclic"):
            replace(fixture_suite()[1], nodes=(
                Node("a", "current record", ("owner",), (("record", "R"),), ("b",)),
                Node("b", "release record", ("manager",), (("release", "R"),), ("a",))))

    def test_numeric_context_match_is_token_bound_not_substring(self):
        self.assertTrue(contains_value("amount USD12,000", 12000))
        self.assertFalse(contains_value("amount=120001", 12000))
        self.assertFalse(contains_value("other-record", "record-new"))
        self.assertTrue(contains_field("amount=USD12,000; record=REC-NEW", "amount", 12000))
        self.assertFalse(contains_field("amount=120001", "amount", 12000))

    def test_quoted_intent_or_swapped_context_cannot_release(self):
        rt = runtime(fixture_suite()[1])
        rt.cycle(Decision("ASK", "owner", "current record"))
        response = rt.npc.reply("manager", "Do not release record; record=REC-NEW", "negated")
        self.assertEqual(json.loads(response)["status"], "refused")
        response = rt.npc.reply("manager", "release record. record=OTHER; note=REC-NEW", "swapped")
        self.assertEqual(json.loads(response)["status"], "refused")
        self.assertEqual(rt.npc.released, {"record"})

    def test_unknown_reply_cannot_enter_public_memory(self):
        rt = runtime(fixture_suite()[0])
        with self.assertRaisesRegex(ValueError, "tracked outgoing"):
            rt._deliver({"message_id": "unknown:reply", "in_reply_to": "unknown:out", "person_id": "owner",
                         "content": canonical({"status": "released", "facts": {"record": "SECRET"}, "reason": ""})})
        self.assertFalse(rt.values)

    def test_private_metadata_is_rejected_below_top_level(self):
        rt = runtime(fixture_suite()[0])
        obs = rt.observe()
        obs["progress"]["required_context"] = ["SECRET"]
        with self.assertRaises(ValueError):
            validate_public_observation(obs)
        rt.cycle(Decision("ASK", "owner", "current record"))
        obs = rt.observe()
        obs["obtained_values"][0]["gold_node"] = "private"
        with self.assertRaises(ValueError):
            validate_public_observation(obs)

    def test_report_is_local_proof_not_real_ceiling_or_generator_completion(self):
        report = run_suite()
        self.assertEqual(report["fixture_count"], 9)
        self.assertEqual(report["reference_fixture_proof_complete"], 9)
        self.assertEqual(report["always_SELF_public_delivery_and_submit"], 9)
        self.assertEqual(report["always_SELF_content_valid"], 2)
        self.assertEqual(report["new_model_API_calls"], 0)
        self.assertTrue(report["local_protocol_gate_passed"])
        self.assertFalse(report["official_TribalBench_scorer_executed"])
        self.assertIn("not run", report["real_mini_ceiling_gate"])

    def test_ceiling_budget_counts_episodes_refresh_calls_and_both_token_prices(self):
        cfg = json.loads((Path(__file__).parent / "configs" / "ceiling_pilot.json").read_bytes())
        episodes = len(cfg["task_ids"]) * len(cfg["arms"]) * cfg["repeats"]
        self.assertEqual(episodes, cfg["episodes"])
        per_call = (Decimal(str(cfg["input_tokens_per_call_assumed_cap"])) *
                    Decimal(str(cfg["standard_USD_per_million_input"])) +
                    Decimal(str(cfg["output_tokens_per_call_assumed_cap"])) *
                    Decimal(str(cfg["standard_USD_per_million_output"]))) / Decimal(1_000_000)
        self.assertEqual(per_call, Decimal(str(cfg["ordinary_price_upper_USD_per_call"])))
        calls = episodes * cfg["max_normal_actions"] * (
            cfg["max_public_controller_calls_per_action"] + cfg["max_question_calls_per_action"] +
            cfg["max_ordinary_calls_per_action"])
        self.assertEqual(cfg["max_ordinary_calls_per_action"], 2)
        for name, count in (("rule_NPC", calls), ("LLM_NPC", calls + episodes * cfg["max_normal_actions"])):
            self.assertEqual(cfg[name + "_calls_upper"], count)
            upper = Decimal(count) * per_call
            self.assertEqual(upper, Decimal(str(cfg[name + "_cost_upper_USD"])))
            surcharge = Decimal(1) + Decimal(str(cfg["possible_regional_surcharge_fraction"]))
            self.assertGreaterEqual(Decimal(cfg[name + "_suggested_independent_cap_USD"]), upper * surcharge)
        self.assertFalse(cfg["new_paid_ledger_created"])


if __name__ == "__main__":
    unittest.main()
