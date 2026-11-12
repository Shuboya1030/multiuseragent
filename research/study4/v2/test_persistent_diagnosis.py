from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from .budget import BudgetBlocked
from .contracts import canonical, fingerprint, strict_json
from .durable import DurableLedger
from .response_diagnosis import inspect_response_shape
from .test_durable_preflight import MockProvider, approval_for
from .test_provider_bound import control_request, model_max_config, standard_mock

PERSISTED_FAILURES_OBSERVED = []


def mutated_provider_response(kind):
    def transform(data):
        standard_mock(data)
        if kind == "response_json":
            return b'{"x": "DO_NOT_KEEP_RAW_ERROR"'
        if kind == "response_envelope":
            data["model"] = "DO_NOT_KEEP_MODEL_VALUE"
        elif kind == "output_items":
            data["output"].insert(0, {"type": "reasoning", "summary": [
                {"type": "summary_text", "text": "DO_NOT_KEEP_TASK_VALUE"}]})
        elif kind == "output_content":
            data["output"][0]["content"] = [{"type": "refusal", "refusal": "DO_NOT_KEEP_REFUSAL_VALUE"}]
        elif kind == "usage":
            data["usage"]["output_tokens"] = 1025
        elif kind == "application_json":
            data["output"][0]["content"][0]["text"] = "{DO_NOT_KEEP_APPLICATION_VALUE"
        elif kind == "application_validation":
            data["output"][0]["content"][0]["text"] = canonical(
                {"action": "INVALID", "person_id": None, "DO_NOT_KEEP_UNKNOWN_KEY": "DO_NOT_KEEP_TASK_VALUE"})
        return data
    return transform


def write_failed_call_in_child(config_path, stage):
    config = strict_json(Path(config_path).read_bytes())
    ledger = DurableLedger(Path(config_path).parent, config["plan"], config["approval"], create=True)
    try:
        try:
            ledger.call("ep-0", "control", 0, config["request"],
                        MockProvider(config["plan"], mutated_provider_response(stage)))
        except ValueError:
            pass
        else:
            raise AssertionError("Synthetic failure unexpectedly accepted")
    finally:
        ledger.close()


class PersistentDiagnosisTests(unittest.TestCase):
    def test_exact_failure_stage_and_safe_shape_survive_real_child_exit(self):
        for stage in ("response_json", "response_envelope", "output_items", "output_content", "usage",
                      "application_json", "application_validation"):
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(prefix="study4_v2_stage_child_") as folder:
                root = Path(folder)
                plan, approval = model_max_config(root)
                path = root / "LOCAL_CHILD_CONFIG.json"
                path.write_text(canonical({"plan": plan, "approval": approval, "request": control_request()}),
                                encoding="utf-8")
                code = ("from research.study4.v2.test_persistent_diagnosis import write_failed_call_in_child;"
                        "import sys; write_failed_call_in_child(sys.argv[1],sys.argv[2])")
                child = subprocess.run([sys.executable, "-c", code, str(path), stage], capture_output=True, timeout=20)
                self.assertEqual(child.returncode, 0, child.stderr.decode(errors="replace"))
                reopened = DurableLedger(root, plan, approval, create=False)
                try:
                    row = reopened.connection.execute("select * from calls").fetchone()
                    self.assertEqual(row["state"], "unknown")
                    self.assertEqual(Decimal(row["reserved"]), Decimal(".858"))
                    diagnostic = strict_json(row["diagnostic"])
                    self.assertEqual(diagnostic["validation_stage"], stage)
                    self.assertTrue(diagnostic["validator_frames"])
                    self.assertNotIn("DO_NOT_KEEP", canonical(diagnostic))
                    self.assertNotIn("Authorization", canonical(diagnostic))
                    self.assertNotIn("Bearer", canonical(diagnostic))
                    if stage == "output_items":
                        self.assertEqual(diagnostic["response_shape"]["output_count"], 2)
                        self.assertEqual(diagnostic["response_shape"]["output"][0]["type"], "reasoning")
                    self.assertIsNone(row["charged"])
                    PERSISTED_FAILURES_OBSERVED.append({"synthetic_stage": stage, "child_returncode": child.returncode,
                                                        "state_after_child_exit": row["state"],
                                                        "reserved_USD": row["reserved"], "diagnostic": diagnostic})
                finally:
                    reopened.close()

    def test_known_envelope_shapes_inspected_without_acceptance_or_task_values(self):
        for output in ([], [{"type": "reasoning", "summary": []}],
                       [{"type": "message", "role": "assistant", "content": []}],
                       [{"type": "function_call", "name": "DO_NOT_KEEP_TOOL", "arguments": "DO_NOT_KEEP_ARGS"}],
                       [{"type": "message", "content": [{"type": "refusal", "refusal": "DO_NOT_KEEP_VALUE"}]}]):
            shape = inspect_response_shape(canonical({"output": output, "DO_NOT_KEEP_KEY": "DO_NOT_KEEP_VALUE"}).encode())
            self.assertEqual(shape["output_count"], len(output))
            self.assertNotIn("DO_NOT_KEEP", canonical(shape))

    def test_old_ledger_schema_not_reinterpreted_as_new(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_oldschema_") as folder:
            root = Path(folder)
            plan, approval = model_max_config(root)
            ledger = DurableLedger(root, plan, approval, create=True)
            metadata = deepcopy(ledger.metadata)
            metadata["schema"] = "study4-v2-durable-1"
            ledger.connection.execute("update metadata set payload=?", (canonical(metadata),))
            ledger.close()
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                DurableLedger(root, plan, approval, create=False)

    def test_recovery_requires_new_source_and_includes_old_unknown_in_same50cap(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_recovery_guard_") as folder:
            root = Path(folder)
            plan, _ = model_max_config(root)
            plan.update(run_id="LOCAL_RECOVERY_TEST", max_calls=1, episodes=["diagnostic-only-no-tools"])
            plan["diagnostic_recovery"] = {
                "prior_run_id": "original-stopped-batch", "prior_ledger_sha256": "a" * 64,
                "prior_unknown_calls": 1, "prior_unknown_held_USD": ".858000", "prior_settled_USD": "0",
                "new_direct_user_source": None}
            plan["budget_cap_USD"] = "50.00"
            approval = approval_for(root, plan)
            with self.assertRaisesRegex(BudgetBlocked, "NEW authorization"):
                DurableLedger(root, plan, approval, create=True)
            self.assertEqual(list(root.iterdir()), [])
            plan["diagnostic_recovery"]["new_direct_user_source"] = "LOCAL_TEST_ONLY_NOT_REAL_APPROVAL"
            approval = approval_for(root, plan)
            approval["diagnostic_recovery_authorization"] = {
                "approved": True, "recovery_sha256": fingerprint(plan["diagnostic_recovery"]),
                "new_direct_user_source": plan["diagnostic_recovery"]["new_direct_user_source"]}
            ledger = DurableLedger(root, plan, approval, create=True)
            provider = MockProvider(plan, mutated_provider_response("usage"))
            try:
                self.assertEqual(Decimal(ledger.status()["occupied_USD_upper"]), Decimal(".858"))
                with self.assertRaises(ValueError):
                    ledger.call("diagnostic-only-no-tools", "control", 0, control_request(), provider)
                self.assertEqual(Decimal(ledger.status()["held_USD_upper"]), Decimal("1.716"))
                self.assertEqual(Decimal(ledger.status()["prior_unknown_held_USD"]), Decimal(".858"))
                self.assertEqual(provider.calls, 1)
                with self.assertRaises(BudgetBlocked):
                    ledger.call("diagnostic-only-no-tools", "control", 1, control_request(), provider)
                self.assertEqual(provider.calls, 1)
            finally:
                ledger.close()
            provider_plan = deepcopy(plan)
            provider_plan.update(mode="provider", endpoint="https://api.openai.com/v1/responses")
            provider_approval = approval_for(root, provider_plan)
            provider_approval["scope"] = "STUDY4_V2_INDEPENDENT_PAID"
            provider_approval["diagnostic_recovery_authorization"] = {
                "approved": True, "recovery_sha256": fingerprint(provider_plan["diagnostic_recovery"]),
                "new_direct_user_source": provider_plan["diagnostic_recovery"]["new_direct_user_source"]}
            before = {p.name for p in root.iterdir()}
            with self.assertRaisesRegex(BudgetBlocked, "executor not enabled"):
                DurableLedger(root, provider_plan, provider_approval, create=True)
            self.assertEqual({p.name for p in root.iterdir()}, before)


if __name__ == "__main__":
    unittest.main()
