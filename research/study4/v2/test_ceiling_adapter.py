from copy import deepcopy
from decimal import Decimal
import json
import unittest

from .benchmark import (export_bundle, load_task, score_episode,
                        verify_assets, SCORER_SHA)
from .budget import BudgetBlocked, LocalBudget
from .contracts import Decision, canonical
from .local_ceiling_check import ScriptedPublicMini, make_case, run_check
from .mini_request import build_request
from .oracle import validate_public_observation
from .training_data import audit_rows, model_input, supervision_row

MAIL = "m-low-customer-mailing"


class ScorerAdapterTests(unittest.TestCase):
    def test_exact_pinned_source_and_24_structured_rule_cases(self):
        self.assertEqual(verify_assets()["files"]["scorer/scorer.py"]["sha256"], SCORER_SHA)
        report = run_check()
        self.assertEqual(report["local_cases"], 24)
        self.assertTrue(all(c["official"]["base_pass"] for c in report["cases"]))
        self.assertTrue(all(c["official"]["T"] == 1 and c["official"]["errors"]["n_auth"] == 0
                            for c in report["cases"]))
        self.assertEqual(report["actual_model_API_calls"], 0)
        self.assertFalse(report["ceiling_gain_or_task_improvement_established"])

    def test_public_load_does_not_depend_on_private_labels(self):
        task = load_task(MAIL)
        _, rt, _, _ = make_case(MAIL, "A")
        observed = rt.observe()
        self.assertNotIn("SEG-Q4-ENT", canonical(observed))
        self.assertNotIn("gold_dag", canonical(observed))
        for value in (task.blueprint["help_class"], "required_context", "candidate_pool", "release_rule"):
            self.assertNotIn(value, canonical(observed))
        validate_public_observation(observed)

    def test_dependency_partial_refusal_and_bound_rule_evidence(self):
        task, rt, _, scheduler = make_case(MAIL, "D")
        # Current full facts cannot be obtained before the dependent request.
        bad = "request authorization_ref. upgrade enterprise SEG-Q4-ENT 455"
        reply = json.loads(rt.npc.reply("Mark Johnson", bad, "probe-local-only"))
        self.assertEqual(reply["status"], "refused")
        self.assertEqual(reply["facts"], {})
        rt.npc.receipts.clear()
        scheduler.step()
        self.assertEqual(rt.npc.released, {"h1"})
        self.assertNotIn("APR-Q4-77", canonical(rt.observe()))
        scheduler.run()
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
        self.assertEqual(score_episode(task, rt, bundle)["official"]["R"], 1)
        rt.npc.receipts[0]["reply_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "binds actual message"):
            export_bundle(rt, scheduler.timestamps, rule_reviews=True)

    def test_unreviewed_structured_trace_is_unknown_not_automatic_success(self):
        task, rt, _, scheduler = make_case(MAIL, "D")
        scheduler.run()
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=False)
        scored = score_episode(task, rt, bundle)
        self.assertIsNone(scored["official"]["base_pass"])
        self.assertEqual(scored["episode_status"], "needs_evidence_review")
        self.assertFalse(scored["eligible_for_confirmatory_metrics"])
        self.assertEqual(scored["official"]["T"], 1)  # Actual pinned scorer: partial artifact metric, NOT pass.

    def test_submit_separate_from_official_content_and_infra_never_zero_filled(self):
        task, rt, _, scheduler = make_case(MAIL, "D")
        scheduler.run()
        rt.failed = True
        with self.assertRaisesRegex(ValueError, "Infra/incomplete"):
            score_episode(task, rt, export_bundle(rt, scheduler.timestamps))
        rt.failed = False
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
        del bundle["events"][0]["timestamp"]
        with self.assertRaises(ValueError):
            score_episode(task, rt, bundle)

    def test_trace_scope_edit_and_stale_review_refused(self):
        task, rt, _, scheduler = make_case(MAIL, "D")
        scheduler.run()
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
        bundle["events"][0]["content"] = "Edited after export"
        with self.assertRaisesRegex(ValueError, "actual runtime"):
            score_episode(task, rt, bundle)
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
        bundle["evidence_reviews"][0]["request_content_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "Stale evidence review"):
            score_episode(task, rt, bundle)
        bundle = export_bundle(rt, scheduler.timestamps, rule_reviews=True)
        bundle["complete"] = False
        with self.assertRaisesRegex(ValueError, "Incomplete trace"):
            score_episode(task, rt, bundle)

    def test_official_optional_no_contact_remains_half_quality(self):
        task, rt, _, scheduler = make_case("o-low-demo-dataset", "A", ScriptedPublicMini(no_ask=True))
        scheduler.run()
        scored = score_episode(task, rt, export_bundle(rt, scheduler.timestamps))
        self.assertTrue(scored["official"]["base_pass"])
        self.assertEqual(scored["official"]["T"], .5)
        self.assertEqual(scored["official"]["R"], .5)
        self.assertTrue(scored["bridge_submitted"])
        self.assertEqual(rt.contacts, 0)


class SchedulingTests(unittest.TestCase):
    def test_shared_ordinary_wire_schema_and_no_arm_or_gold_in_prompt(self):
        requests = []
        for arm in "ABCD":
            _, rt, _, _ = make_case(MAIL, arm)
            requests.append(build_request("ordinary", rt.observe()))
        self.assertTrue(all(r == requests[0] for r in requests))
        wire = canonical(requests[0])
        self.assertNotIn("gold", wire)
        self.assertNotIn("private_when_whom", wire)
        self.assertNotIn("send_message", wire)
        self.assertEqual(requests[0]["model"], "gpt-5.4-mini-2026-03-17")

    def test_start_proposal_reply_reasons_coalesced_once_and_ask_refreshes(self):
        _, rt, mini, scheduler = make_case(MAIL, "A")
        scheduler.step()
        self.assertEqual(len(mini.requests), 4)  # proposal, control, question, refreshed ordinary
        self.assertEqual(scheduler.cycles[0]["boundary_reasons"], ["start", "deliverable_or_submit_proposal"])
        self.assertEqual(rt.normal_actions, 1)
        self.assertTrue(scheduler.cycles[0]["proposal_discarded"])
        self.assertEqual([e["kind"] for e in rt.history].count("write_file"), 1)
        scheduler.step()
        operations = [json.loads(r["input"][1]["content"])["operation"] for r in mini.requests]
        self.assertEqual(operations.count("control"), 2)
        self.assertIn("reply", scheduler.cycles[1]["boundary_reasons"])
        self.assertEqual(rt.contacts, 2)

    def test_no_ask_reuses_proposal_and_does_not_call_question_or_refresh(self):
        _, rt, mini, scheduler = make_case("o-low-demo-dataset", "A", ScriptedPublicMini(no_ask=True))
        scheduler.step()
        self.assertEqual(len(mini.requests), 2)
        scheduler.run()
        self.assertTrue(rt.progress()["bridge_submitted"])
        self.assertEqual(rt.contacts, 0)
        self.assertFalse(any(c["proposal_discarded"] for c in scheduler.cycles))

    def test_privileged_what_only_passes_public_intent_and_obtained_ids(self):
        for arm in ("B", "D"):
            _, rt, mini, scheduler = make_case(MAIL, arm)
            scheduler.step()
            scheduler.step()
            questions = [json.loads(r["input"][1]["content"]) for r in mini.requests
                         if json.loads(r["input"][1]["content"])["operation"] == "question"]
            self.assertEqual("request_plan" in questions[0], arm == "D")
            for body in questions:
                self.assertNotIn("APR-Q4-77", canonical(body))
                if "request_plan" in body:
                    self.assertEqual(set(body["request_plan"]), {"intent", "include_value_ids"})
                    known = {v["value_id"] for v in body["state"]["obtained_values"]}
                    self.assertTrue(set(body["request_plan"]["include_value_ids"]) <= known)
            self.assertFalse(any(json.loads(r["input"][1]["content"])["operation"] == "control" for r in mini.requests))

    def test_prompt_metadata_leak_and_unread_assistance_are_rejected(self):
        _, rt, _, _ = make_case(MAIL, "A")
        state = rt.observe()
        state["task"]["required_context"] = ["secret"]
        with self.assertRaisesRegex(ValueError, "Private task"):
            build_request("ordinary", state)
        with self.assertRaisesRegex(ValueError, "unread"):
            build_request("question", rt.observe(), person_id="Mark Johnson",
                          assistance={"intent": rt.task.intents[0], "include_value_ids": ["unknown"]})

    def test_failure_after_dispatch_retains_unknown_and_stops_without_retry(self):
        _, rt, mini, scheduler = make_case(MAIL, "A", ScriptedPublicMini(fail_operation="control"))
        with self.assertRaises(TimeoutError):
            scheduler.step()
        self.assertTrue(rt.failed)
        self.assertEqual(mini.budget.receipt()["unknown"], 1)
        count = len(mini.requests)
        with self.assertRaises(ValueError):
            scheduler.step()
        self.assertEqual(len(mini.requests), count)

    def test_speculative_action_cannot_survive_ask(self):
        _, rt, mini, _ = make_case(MAIL, "A")
        proposal = mini.ordinary(rt.observe())
        with self.assertRaisesRegex(ValueError, "invalidates"):
            rt.cycle(Decision("ASK", "Mark Johnson", "request segment_id"), proposed_tool=proposal)
        self.assertEqual(rt.contacts, 0)

    def test_bad_output_with_settled_usage_stops_as_infra_not_unknown_money(self):
        class BadTool(ScriptedPublicMini):
            def __call__(self, request):
                result = super().__call__(request)
                result["output_text"] = canonical({"tool": "send_message", "arguments": "{}"})
                return result
        _, rt, mini, scheduler = make_case(MAIL, "A", BadTool())
        with self.assertRaisesRegex(ValueError, "forbidden"):
            scheduler.step()
        self.assertTrue(rt.failed)
        self.assertEqual(mini.budget.receipt()["settled"], 1)
        self.assertEqual(mini.budget.receipt()["unknown"], 0)
        with self.assertRaisesRegex(ValueError, "Stopped schedule"):
            scheduler.step()

    def test_missing_usage_is_unknown_and_cannot_dispatch_again(self):
        def partial(_):
            return {"output_text": "{}", "status": "completed", "usage": {}}
        _, _, mini, scheduler = make_case(MAIL, "A", partial)
        with self.assertRaisesRegex(ValueError, "Missing usage"):
            scheduler.step()
        self.assertEqual(mini.budget.receipt()["unknown"], 1)
        self.assertGreater(Decimal(mini.budget.receipt()["usd_exposure_upper"]), 0)

    def test_four_action_checkpoint_and_nonboundary_do_not_add_control_calls(self):
        class ListOnly(ScriptedPublicMini):
            def __call__(self, request):
                result = super().__call__(request)
                operation = json.loads(request["input"][1]["content"])["operation"]
                if operation == "ordinary":
                    result["output_text"] = canonical({"tool": "list_files", "arguments": "{}"})
                return result
        _, rt, mini, scheduler = make_case(MAIL, "A", ListOnly(no_ask=True))
        for _ in range(5):
            scheduler.step()
        self.assertEqual(rt.normal_actions, 5)
        self.assertEqual([c["public_controller_called"] for c in scheduler.cycles], [True, False, False, False, True])
        self.assertEqual(scheduler.cycles[-1]["boundary_reasons"], ["four_ordinary_actions"])
        self.assertEqual(len(mini.requests), 7)

    def test_C_wrong_recipient_is_not_privately_corrected(self):
        class WrongPerson(ScriptedPublicMini):
            def __call__(self, request):
                result = super().__call__(request)
                if json.loads(request["input"][1]["content"])["operation"] == "control":
                    result["output_text"] = canonical({"action": "ASK", "person_id": "Li Ming"})
                return result
        _, rt, _, scheduler = make_case(MAIL, "C", WrongPerson())
        scheduler.step()
        self.assertEqual(scheduler.cycles[0]["decision"]["person_id"], "Li Ming")
        self.assertEqual(scheduler.cycles[0]["what_assistance_status"], "no_ready_node_public_fallback")
        self.assertFalse(rt.npc.released)
        self.assertEqual(rt.history[1]["person_id"], "Li Ming")

    def test_invalid_control_response_disables_client_even_without_scheduler(self):
        class InvalidControl(ScriptedPublicMini):
            def __call__(self, request):
                result = super().__call__(request)
                result["output_text"] = canonical({"action": "ASK", "person_id": "unlisted-private-person"})
                return result
        _, rt, mini, _ = make_case(MAIL, "A", InvalidControl())
        with self.assertRaisesRegex(ValueError, "Invalid controller"):
            mini.control(rt.observe(), None)
        self.assertTrue(mini.failed)
        self.assertEqual(mini.budget.receipt()["settled"], 1)
        with self.assertRaisesRegex(ValueError, "retry forbidden"):
            mini.control(rt.observe(), None)
        self.assertEqual(mini.budget.receipt()["calls"], 1)


class BudgetTests(unittest.TestCase):
    def test_pending_budget_dispatches_nothing(self):
        callback = ScriptedPublicMini()
        _, rt, mini, scheduler = make_case(MAIL, "A", callback, LocalBudget())
        with self.assertRaisesRegex(BudgetBlocked, "pending"):
            scheduler.step()
        self.assertEqual(callback.seen, [])
        self.assertEqual(mini.budget.receipt()["calls"], 0)
        self.assertFalse(mini.budget.paid_authorization)

    def test_reserve_settle_funds_usage_and_never_uses_float_math(self):
        budget = LocalBudget("1")
        reserve = budget.reserve("a", "ep", "ordinary", 8000)
        self.assertEqual(reserve, Decimal(".0116688"))
        budget.settle("a", 100, 50)
        self.assertEqual(Decimal(budget.receipt()["usd_exposure_upper"]), Decimal(".00033"))
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            budget.reserve("a", "ep", "ordinary", 1)

    def test_token_call_usd_and_per_episode_operation_limits_pre_dispatch(self):
        for budget in (LocalBudget("0"), LocalBudget("1", max_calls=0),
                       LocalBudget("1", total_input_cap=0), LocalBudget("1", total_output_cap=0)):
            with self.assertRaises(BudgetBlocked):
                budget.reserve("first", "ep", "control", 100)
            self.assertEqual(budget.receipt()["calls"], 0)
        budget = LocalBudget("55")
        for i in range(24):
            budget.reserve(str(i), "ep", "control", 1)
            budget.settle(str(i), 1, 1)
        with self.assertRaises(BudgetBlocked):
            budget.reserve("25", "ep", "control", 1)
        with self.assertRaisesRegex(ValueError, "per-call"):
            budget.reserve("huge", "another", "control", 8001)

    def test_unknown_full_exposure_and_usage_overrun_never_released(self):
        budget = LocalBudget("1")
        amount = budget.reserve("a", "ep", "ordinary", 10)
        with self.assertRaises(BudgetBlocked):
            budget.settle("a", 11, 1)
        self.assertEqual(budget._exposure(), amount)
        with self.assertRaises(BudgetBlocked):
            budget.reserve("b", "ep", "ordinary", 1)
        with self.assertRaises(ValueError):
            budget.settle("a", 1, 1)
        self.assertEqual(budget.receipt()["unknown"], 1)

    def test_pending_inflight_blocks_parallel_reserve(self):
        budget = LocalBudget("1")
        budget.reserve("a", "ep", "ordinary", 10)
        with self.assertRaises(BudgetBlocked):
            budget.reserve("b", "another", "ordinary", 10)
        budget.settle("a", 10, 0)
        budget.reserve("b", "another", "ordinary", 10)

    def test_global_episode_bound_and_rule_NPC_cost_mode(self):
        budget = LocalBudget("1", max_episodes=1)
        budget.reserve("a", "first", "ordinary", 10)
        budget.settle("a", 10, 0)
        with self.assertRaises(BudgetBlocked):
            budget.reserve("b", "second", "ordinary", 10)
        with self.assertRaisesRegex(ValueError, "Rule NPC mode"):
            budget.reserve("c", "first", "npc", 10)


class TrainingInterfaceTests(unittest.TestCase):
    def test_public_projection_and_masked_three_heads_no_fake_RL_probability(self):
        _, rt, _, _ = make_case(MAIL, "A")
        row = supervision_row(rt.observe(), [Decision("ASK", "Mark Johnson", "request segment_id")],
                              "train-family", "train-org", "train")
        self.assertEqual(json.loads(model_input(row)), json.loads(canonical(rt.observe())))
        self.assertNotIn("acceptable", model_input(row))
        self.assertIsNone(row["private_supervision_NOT_model_input"]["behavior_probability"])
        self.assertFalse(row["private_supervision_NOT_model_input"]["offline_RL_eligible"])
        self.assertEqual(audit_rows([row])["rows"], 1)

    def test_split_overlap_and_unidentifiable_targets_fail(self):
        _, rt, _, _ = make_case(MAIL, "A")
        one = supervision_row(rt.observe(), [Decision("SELF")], "family", "org", "train")
        two = deepcopy(one)
        two["group"]["split"] = "dev"
        with self.assertRaisesRegex(ValueError, "crosses frozen split"):
            audit_rows([one, two])
        two["group"]["split"] = "train"
        two["private_supervision_NOT_model_input"]["acceptable"] = [
            {"when": "ASK", "whom": "Mark Johnson", "intent": "request segment_id", "include_value_ids": []}]
        with self.assertRaisesRegex(ValueError, "Unidentifiable"):
            audit_rows([one, two])

    def test_early_submit_or_unread_values_are_not_trainable_labels(self):
        _, rt, _, _ = make_case(MAIL, "A")
        for choice in (Decision("SUBMIT"), Decision("ASK", "Mark Johnson", "request segment_id", ("unread",))):
            with self.assertRaises(ValueError):
                supervision_row(rt.observe(), [choice], "train-family", "train-org", "train")


if __name__ == "__main__":
    unittest.main()
