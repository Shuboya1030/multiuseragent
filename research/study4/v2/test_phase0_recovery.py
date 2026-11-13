"""Offline admission checks; the transport below never opens a socket."""
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .admission import root_binding, validate_binding
from .budget import BudgetBlocked
from .contracts import fingerprint, strict_json
from .phase0 import SOURCE
from .phase0_admission import make_plan
from .phase0_recovery import CONTINUE_SOURCE, INHERITED, RECOVERY, REVIEW, REVIEWED, RUN_ID, selection


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.prefix = strict_json((Path(__file__).parent / "reports" /
            "REFERENCE_V6_PREFIX_CERTIFICATE_20261112.json").read_bytes())["proof"]

    def binding(self, root):
        proof, full, fresh = selection()
        plan = make_plan([{}] * 11, INHERITED, local_test=True)
        plan["history"][-1] = {"root": "offline-fixture-not-used"}
        audit = deepcopy(proof)
        audit["current_runtime_binding"] = plan["runtime"]
        audit["reference_source_sha256_LF"] = plan["runtime"]["phase0_sources"]["reference_completion.py"]
        audit["episode_optional_hydrated_runtime_only_default_branch_AST_identical"] = True
        plan.update(run_id=RUN_ID, mode="provider", endpoint="https://api.openai.com/v1/responses",
                    direct_user_source=deepcopy(CONTINUE_SOURCE),
                    prefix_proof=deepcopy(self.prefix),
                    slots=full, fresh_slots=fresh, episodes=[s["episode_id"] for s in fresh],
                    max_calls=214 * 192, max_episodes=214,
                    total_input_tokens=214 * 192 * 272000, total_output_tokens=214 * 192 * 128000,
                    execution_cohort_audit=audit, reference_recovery={
                        "version": RECOVERY, "reviewed_manifest_fingerprint": REVIEWED,
                        "review_release": deepcopy(REVIEW),
                        "retained_slots": [r["slot"]["slot"] for r in proof["rows"]
                                           if r["retain_in_formal_cohort"]],
                        "old_partial52_not_resumed": True, "all_BD_not_selected_by_results": True,
                        "paid_prefix18_continued_without_replay": True})
        at = datetime.now(timezone.utc)
        approval = {"approved": True, "run_id": RUN_ID, "plan_sha256": fingerprint(plan),
                    "storage_root_sha256": root_binding(root), "budget_cap_USD": "50.00",
                    "direct_user_source": CONTINUE_SOURCE, "review_release": REVIEW,
                    "scope": "STUDY4_FORMAL_PHASE0_240_AC26_FRESH214_SAME50",
                    "not_before": at.isoformat(), "expires": (at + timedelta(hours=1)).isoformat(),
                    "reference": REVIEW["assignment_id"]}
        return plan, approval

    def test_review_release_preserves_original_source_and_all_costs(self):
        with tempfile.TemporaryDirectory() as directory:
            plan, approval = self.binding(Path(directory))
            validate_binding(plan, approval, directory, plan["endpoint"])
            self.assertEqual(plan["direct_user_source"], CONTINUE_SOURCE)
            self.assertEqual(plan["reference_recovery"]["review_release"]["original_direct_user_source"], SOURCE)
            self.assertEqual(plan["inherited"]["calls"], 1040)
            self.assertEqual(plan["inherited"]["unknown_held_USD"], "5.148000")

    def test_mutated_cohort_review_source_or_cap_is_rejected(self):
        mutations = [
            lambda p: p["fresh_slots"].pop(),
            lambda p: p["reference_recovery"]["retained_slots"].pop(),
            lambda p: p["reference_recovery"]["review_release"].update(attribution="new user approval"),
            lambda p: p["prefix_proof"].update(invented=True),
            lambda p: p["direct_user_source"].update(revision=11),
            lambda p: p["inherited"].update(unknown_held_USD="0"),
            lambda p: p.update(budget_cap_USD="100.00"),
        ]
        with tempfile.TemporaryDirectory() as directory:
            for mutate in mutations:
                with self.subTest(mutation=mutate):
                    plan, approval = self.binding(Path(directory))
                    mutate(plan)
                    approval["plan_sha256"] = fingerprint(plan)
                    with self.assertRaises((ValueError, KeyError, BudgetBlocked)):
                        validate_binding(plan, approval, directory, plan["endpoint"])

    def test_fresh_namespace_never_contains_old_retained_or_partial_ids(self):
        proof, full, fresh = selection()
        old_ids = {s["episode_id"] for s in proof["remaining_manifest"]}
        self.assertEqual(len(full), 240)
        self.assertEqual(len(fresh), 214)
        self.assertFalse(old_ids & {s["episode_id"] for s in fresh})
        self.assertEqual(sum(s["episode_id"].startswith("reference-v5:") for s in fresh), 1)
        self.assertEqual(sum(s["episode_id"].startswith("reference-v6:") for s in fresh), 213)
        self.assertEqual(sum(s["arm"] in {"B", "D"} for s in fresh), 120)


if __name__ == "__main__":
    unittest.main()
