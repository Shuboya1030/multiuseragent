from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .contracts import canonical, fingerprint, strict_json
from .local_ceiling_check import ScriptedPublicMini
from .paid_driver import frozen_plan, run_fresh
from .test_durable_preflight import MockProvider, approval_for


def local_plan(root, slots=48):
    plan = frozen_plan()
    plan.update(mode="local_test", endpoint="http://127.0.0.1:9/v1/responses", run_id="LOCAL_FRESH_DRIVER_TEST")
    plan["slots"] = plan["slots"][:slots]
    plan["episodes"] = [s["episode_id"] for s in plan["slots"]]
    return plan, approval_for(root, plan)


class ScriptedTransport(MockProvider):
    def __init__(self, plan, invalid=False):
        super().__init__(plan)
        self.callback = ScriptedPublicMini()
        self.invalid = invalid

    def send(self, permit, body):
        permit.consume(body, self.endpoint, self.mode)
        self.calls += 1
        response = self.callback(strict_json(body))
        return canonical({"id": "local-" + str(self.calls), "model": strict_json(body)["model"],
                          "status": "completed", "service_tier": "default", "error": None,
                          "incomplete_details": None, "usage": None if self.invalid else response["usage"],
                          "output": [{"type": "message", "role": "assistant", "content": [
                              {"type": "output_text", "text": response["output_text"]}]}]}).encode()


class FreshDriverTests(unittest.TestCase):
    def test_exact_frozen_scope_balanced_groups_and_no_provider_seed_claim(self):
        plan = frozen_plan()
        self.assertEqual(plan["budget_cap_USD"], "50.00")
        self.assertEqual(len(plan["slots"]), 48)
        self.assertEqual(len(set(plan["episodes"])), 48)
        self.assertEqual(len({s["task_id"] for s in plan["slots"]}), 6)
        for start in range(0, 48, 4):
            block = plan["slots"][start:start + 4]
            self.assertEqual({s["arm"] for s in block}, set("ABCD"))
            self.assertEqual(len({(s["task_id"], s["repeat"]) for s in block}), 1)
        for arm in "ABCD":
            positions = [s["slot"] % 4 for s in plan["slots"] if s["arm"] == arm]
            self.assertEqual([positions.count(i) for i in range(4)], [3] * 4)
        self.assertEqual(plan["max_actions"], 24)
        self.assertTrue(plan["fresh_only"])

    def test_complete_scripted48_journal_hashes_and_rerun_cannot_pay_or_repost(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_fresh_driver_") as folder:
            root = Path(folder)
            plan, approval = local_plan(root)
            transport = ScriptedTransport(plan)
            groups = []
            with patch("research.study4.v2.paid_driver.frozen_plan", return_value=plan):
                result = run_fresh(root, plan, approval, transport, lambda rows, budget: groups.append(rows))
                self.assertEqual(result["status"], "complete")
                self.assertEqual(len(result["completed"]), 48)
                self.assertEqual(len(groups), 12)
                calls = transport.calls
                with self.assertRaisesRegex(ValueError, "started before"):
                    run_fresh(root, plan, approval, transport)
                self.assertEqual(transport.calls, calls)
            events = [strict_json(line) for line in (root / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            self.assertEqual(sum(e["kind"] == "episode_complete" for e in events), 48)
            for row in result["completed"]:
                record = strict_json((root / f"slot-{row['slot']:02d}.json").read_bytes())
                self.assertEqual(fingerprint(record), row["record_sha256"])
                self.assertTrue(row["score"]["official"]["base_pass"])
            self.assertEqual(result["budget"]["unknown"], 0)
            self.assertEqual(result["budget"]["calls"], transport.calls)

    def test_usage_failure_stops_whole_fresh_batch_keeps_unknown_and_no_resumption(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_fresh_unknown_") as folder:
            root = Path(folder)
            plan, approval = local_plan(root, 1)
            provider = ScriptedTransport(plan, invalid=True)
            with patch("research.study4.v2.paid_driver.frozen_plan", return_value=plan):
                result = run_fresh(root, plan, approval, provider)
                self.assertEqual(result["status"], "stopped")
                self.assertEqual(result["completed"], [])
                self.assertEqual(result["budget"]["unknown"], 1)
                self.assertEqual(provider.calls, 1)
                with self.assertRaisesRegex(ValueError, "started before"):
                    run_fresh(root, plan, approval, provider)
                self.assertEqual(provider.calls, 1)
            self.assertTrue((root / "slot-00-INCOMPLETE.json").is_file())
            self.assertIsNone(strict_json((root / "slot-00-INCOMPLETE.json").read_bytes())["business_outcome"])

    def test_tool_side_effect_then_interrupt_never_replayed_even_if_models_settled(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_fresh_tool_crash_") as folder:
            root = Path(folder)
            plan, approval = local_plan(root, 1)
            provider = ScriptedTransport(plan)
            from .runtime import SharedRuntime
            original = SharedRuntime._normal
            def interrupted(runtime, command):
                original(runtime, command)
                raise KeyboardInterrupt("LOCAL tool side effect then interruption")
            with patch("research.study4.v2.paid_driver.frozen_plan", return_value=plan), \
                    patch.object(SharedRuntime, "_normal", interrupted):
                result = run_fresh(root, plan, approval, provider)
                self.assertEqual(result["error_type"], "KeyboardInterrupt")
                self.assertEqual(result["budget"]["unknown"], 0)
                self.assertEqual(result["completed"], [])
                prior = provider.calls
                with self.assertRaisesRegex(ValueError, "started before"):
                    run_fresh(root, plan, approval, provider)
                self.assertEqual(provider.calls, prior)
            partial = strict_json((root / "slot-00-INCOMPLETE.json").read_bytes())
            self.assertGreater(partial["runtime_snapshot_PRIVATE_NOT_MODEL_INPUT"]["state"]["normal_actions"], 0)

    def test_frozen_plan_or_approval_drift_never_creates_ledger(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_fresh_drift_") as folder:
            root = Path(folder)
            plan, approval = local_plan(root, 1)
            expected = deepcopy(plan)
            plan["max_actions"] = 12
            approval = approval_for(root, plan)
            with patch("research.study4.v2.paid_driver.frozen_plan", return_value=expected):
                with self.assertRaisesRegex(ValueError, "exact authorized"):
                    run_fresh(root, plan, approval, ScriptedTransport(plan))
            self.assertEqual(list(root.iterdir()), [])


if __name__ == "__main__":
    unittest.main()
