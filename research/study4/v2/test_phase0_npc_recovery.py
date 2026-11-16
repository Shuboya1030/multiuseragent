"""No network: pending NPC completion equals the original ASK suffix."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from .admission import root_binding, validate_binding
from .contracts import canonical, fingerprint, strict_json
from .phase0 import Phase0Mini, Phase0Runtime, load_case
from .phase0_admission import make_plan
from . import phase0_npc_recovery as recovery
from .request_pacing import CONFIG


class FixtureMini(Phase0Mini):
    def __init__(self):
        super().__init__(None, None, {"episode_id": "fixture"}, None)
        self.fail_npc, self.operations = False, []

    def call(self, mode, observation=None, person=None):
        self.operations.append(mode)
        if mode == "npc":
            if self.fail_npc:
                raise ConnectionError("local fixture: no response")
            self.indices["npc"] += 1
            return {"data": {"text": "No, I cannot confirm those values."}}
        assert mode == "ordinary"
        self.indices["ordinary"] += 1
        return function("read_file", {"path": "/workspace/missing.md"}, "ordinary6")


def function(name, args, identity):
    return {"data": {"tool": name, "arguments": args}, "native_function": {
        "call_id": identity, "output_items": [{"type": "function_call", "name": name,
            "arguments": canonical(args), "call_id": identity}]}}


class NPCRecoveryTests(unittest.TestCase):
    def binding(self, root):
        audit, full, fresh = recovery.selection()
        plan = make_plan([{}] * 14, recovery.INHERITED, local_test=True)
        cohort = strict_json((Path(__file__).parent / "reports" /
                              "REFERENCE_V8_PACED_EXECUTION_AC26_20261113.json").read_bytes())
        cohort["current_runtime_binding"] = plan["runtime"]
        plan.update(run_id=recovery.RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                    slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                    max_calls=167 * 192, max_episodes=167, total_input_tokens=167 * 192 * 272000,
                    total_output_tokens=167 * 192 * 128000, direct_user_source=deepcopy(recovery.SOURCE),
                    execution_cohort_audit=cohort, pacing=deepcopy(CONFIG),
                    reference_recovery={"version": recovery.VERSION, "reviewed_audit": fingerprint(audit),
                                        "review_release": deepcopy(recovery.REVIEW)},
                    unknown_attempt=recovery.attempt_binding(fresh))
        at = datetime.now(timezone.utc)
        approval = {"approved": True, "run_id": recovery.RUN_ID, "plan_sha256": fingerprint(plan),
                    "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                    "direct_user_source": deepcopy(recovery.SOURCE), "review_release": deepcopy(recovery.REVIEW),
                    "scope": "STUDY4_FORMAL_PHASE0_240_PATH73_TARGET167_NPC6_SAME50",
                    "not_before": at.isoformat(), "expires": (at + timedelta(hours=1)).isoformat(),
                    "reference": recovery.REVIEW["assignment_id"]}
        return plan, approval

    def test_exact_authorization_and_complete_cohort_admitted(self):
        with tempfile.TemporaryDirectory() as root:
            plan, approval = self.binding(root)
            validate_binding(plan, approval, root, plan["endpoint"])
            self.assertEqual(len(plan["slots"]), 240)
            self.assertEqual(plan["inherited"]["unknown_held_USD"], "6.864000")

    def test_no_released_unknown_second_attempt_question_replay_or_budget_increase(self):
        with tempfile.TemporaryDirectory() as root:
            plan, approval = self.binding(root)
            mutations = [
                lambda p: p["unknown_attempt"].update(max_new_attempts=2),
                lambda p: p["unknown_attempt"].update(operation="question"),
                lambda p: p["unknown_attempt"].update(old_request_sha256="wrong"),
                lambda p: p["unknown_attempt"].update(paid_question_not_regenerated_or_resent=False),
                lambda p: p["inherited"].update(unknown_held_USD="0"),
                lambda p: p["pacing"].update(spacing_seconds=0),
                lambda p: p["direct_user_source"].update(revision=1),
                lambda p: p.update(budget_cap_USD="80.00"),
                lambda p: p["fresh_slots"].pop(),
            ]
            for mutate in mutations:
                p, a = deepcopy(plan), deepcopy(approval)
                mutate(p)
                a["plan_sha256"] = fingerprint(p)
                with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                    validate_binding(p, a, root, p["endpoint"])

    def test_pending_suffix_identical_to_original_ask_and_one_ordinary(self):
        case = load_case("o-low-team-lunch")
        for supplement in (False, True):
            with self.subTest(supplement=supplement):
                rt = Phase0Runtime(case, "fixture")
                mini = FixtureMini()
                person = next(iter(case.scenarios))
                for i in range(6):
                    paid = function("ask_colleague", {"person_id": person, "question": "Please confirm."}, str(i))
                    mini.ask(case, rt, paid, supplement)
                rt.normal_actions = 6
                mini.indices = {"question": 7, "npc": 6, "ordinary": 6}
                paid = function("ask_colleague", {"person_id": person, "question": "Confirm final values."}, "paid6")
                original_rt, original_mini = deepcopy(rt), deepcopy(mini)
                original_mini.ask(case, original_rt, paid, supplement)
                original_mini.ordinary(original_rt, original_mini.call("ordinary", original_rt.observe()))
                mini.fail_npc = True
                with self.assertRaises(ConnectionError):
                    mini.ask(case, rt, paid, supplement)
                self.assertEqual(rt.contacts, 7)
                self.assertEqual(len(rt.seen), 6)
                mini.fail_npc, mini.operations = False, []
                recovery.finish_pending(mini, rt, paid, supplement=supplement)
                self.assertEqual(mini.operations, ["npc", "ordinary"])
                self.assertEqual(rt.observe(), original_rt.observe())
                for field in ("history", "dialogues", "known_sources", "indices", "event_cursor"):
                    self.assertEqual(getattr(mini, field), getattr(original_mini, field))
                with self.assertRaises(ValueError):
                    recovery.finish_pending(mini, rt, paid, supplement=supplement)

    def test_new_unknown_in_pending_suffix_does_not_send_or_apply_tool(self):
        case = load_case("o-low-team-lunch")
        mini, rt = FixtureMini(), Phase0Runtime(case, "fixture")
        person = next(iter(case.scenarios))
        mini.indices = {"ordinary": 6, "question": 7, "npc": 6}
        rt.contacts, rt.normal_actions = 6, 6
        paid = function("ask_colleague", {"person_id": person, "question": "Existing request."}, "paid6")
        mini.fail_npc = True
        with self.assertRaises(ConnectionError):
            mini.ask(case, rt, paid, False)
        before, native, dialogues = rt.observe(), deepcopy(mini.history), deepcopy(mini.dialogues)
        mini.operations = []
        with self.assertRaises(ConnectionError):
            recovery.finish_pending(mini, rt, paid, supplement=False)
        self.assertEqual(rt.observe(), before)
        self.assertEqual(mini.history, native)
        self.assertEqual(mini.dialogues, dialogues)
        self.assertEqual(mini.operations, ["npc"])
