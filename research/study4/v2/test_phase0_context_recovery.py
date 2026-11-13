"""Source/admission fixtures only: no real call, key or writable historical root."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest

from .admission import root_binding, validate_binding
from .contracts import fingerprint, strict_json
from .phase0_admission import make_plan
from . import phase0_context_recovery as recovery
from .request_pacing import CONFIG


class ContextRecoveryTests(unittest.TestCase):
    def binding(self, root):
        audit, full, fresh = recovery.selection()
        plan = make_plan([{}] * 13, recovery.INHERITED, local_test=True)
        cohort = strict_json((Path(__file__).parent / "reports" /
                              "REFERENCE_V8_AC26_CERTIFIED_20261113.json").read_bytes())
        cohort["current_runtime_binding"] = plan["runtime"]
        plan.update(
            run_id=recovery.RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
            slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
            max_calls=174 * 192, max_episodes=174, total_input_tokens=174 * 192 * 272000,
            total_output_tokens=174 * 192 * 128000, direct_user_source=deepcopy(recovery.SOURCE),
            execution_cohort_audit=cohort, pacing=deepcopy(CONFIG),
            reference_recovery={"version": recovery.VERSION, "reviewed_audit": fingerprint(audit),
                                "review_release": deepcopy(recovery.REVIEW)},
            unknown_attempt={
                "old_call_id": audit["partial"]["unknown_call_id"],
                "old_request_sha256": audit["partial"]["unknown_request_sha256"],
                "new_episode_id": next(s["episode_id"] for s in fresh if s["slot"] == 67),
                "operation": "ordinary", "index": 62, "max_new_attempts": 1,
                "old_unknown_preserved": True})
        at = datetime.now(timezone.utc)
        approval = {
            "approved": True, "run_id": recovery.RUN_ID, "plan_sha256": fingerprint(plan),
            "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
            "direct_user_source": deepcopy(recovery.SOURCE), "review_release": deepcopy(recovery.REVIEW),
            "scope": "STUDY4_FORMAL_PHASE0_240_PATH66_REMAIN174_PACED_SAME50",
            "not_before": at.isoformat(), "expires": (at + timedelta(hours=1)).isoformat(),
            "reference": recovery.REVIEW["assignment_id"]}
        return plan, approval

    def test_confirmed_paced_binding_preserves_full_target_and_all_unknowns(self):
        with tempfile.TemporaryDirectory() as root:
            plan, approval = self.binding(root)
            validate_binding(plan, approval, root, plan["endpoint"])
            self.assertEqual(plan["inherited"]["unknown_held_USD"], "6.006000")
            self.assertEqual(len(plan["slots"]), 240)
            self.assertEqual(len(plan["fresh_slots"]), 174)
            self.assertTrue(plan["unknown_attempt"]["new_episode_id"].startswith("reference-v8:"))

    def test_no_fast_pacing_released_unknown_changed_source_or_repeated_attempt(self):
        changes = [
            lambda p: p["pacing"].update(spacing_seconds=0),
            lambda p: p["unknown_attempt"].update(max_new_attempts=2),
            lambda p: p["unknown_attempt"].update(old_unknown_preserved=False),
            lambda p: p["unknown_attempt"].update(index=0),
            lambda p: p["inherited"].update(unknown_held_USD="0"),
            lambda p: p["direct_user_source"].update(revision=1),
            lambda p: p["fresh_slots"].pop(),
            lambda p: p.update(budget_cap_USD="80.00"),
        ]
        with tempfile.TemporaryDirectory() as root:
            plan, approval = self.binding(root)
            for change in changes:
                modified, admitted = deepcopy(plan), deepcopy(approval)
                change(modified)
                admitted["plan_sha256"] = fingerprint(modified)
                with self.subTest(change=change):
                    with self.assertRaises(ValueError):
                        validate_binding(modified, admitted, root, modified["endpoint"])
