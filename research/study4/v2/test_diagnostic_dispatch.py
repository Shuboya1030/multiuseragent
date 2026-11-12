from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest

from .contracts import fingerprint, strict_json
from .diagnostic_dispatch import execute_once, verify_prior, VERSION
from .test_durable_preflight import MockProvider, approval_for
from .test_paid_driver import ScriptedTransport
from .test_provider_bound import control_request, model_max_config, standard_mock
from .local_ceiling_check import make_case
from .mini_request import build_provider_request


def setup_local(parent):
    prior = parent / "prior"
    prior.mkdir()
    db = prior / "prior-run.sqlite3"
    connection = sqlite3.connect(db)
    connection.execute("create table calls(state text,reserved text,charged text)")
    connection.execute("insert into calls values('unknown','.858',null)")
    connection.commit()
    connection.close()
    root = parent / "new"
    root.mkdir()
    plan, _ = model_max_config(root)
    plan.update(run_id="LOCAL_SINGLE_DIAGNOSTIC", budget_cap_USD="50.00", max_calls=1, max_episodes=1,
                episodes=["diagnostic-only-no-tools"], dispatcher_version=VERSION, environment_tools_allowed=False)
    plan["diagnostic_recovery"] = {
        "prior_run_id": "prior-run", "prior_root": str(prior),
        "prior_ledger_sha256": hashlib.sha256(db.read_bytes()).hexdigest(),
        "prior_original_file_sha256": {db.name: hashlib.sha256(db.read_bytes()).hexdigest()},
        "prior_unknown_calls": 1, "prior_unknown_held_USD": ".858000", "prior_settled_USD": "0",
        "new_direct_user_source": "LOCAL_TEST_ONLY_NOT_USER_APPROVAL"}
    lock = prior / "prior-run.lock"
    lock.write_bytes(b"0")
    plan["diagnostic_recovery"]["prior_original_file_sha256"][lock.name] = hashlib.sha256(b"0").hexdigest()
    _, runtime, _, _ = make_case("o-low-team-lunch", "A")
    request = build_provider_request("ordinary", runtime.observe())
    plan["request_sha256"] = fingerprint(request)
    approval = approval_for(root, plan)
    approval["diagnostic_recovery_authorization"] = {
        "approved": True, "recovery_sha256": fingerprint(plan["diagnostic_recovery"]),
        "new_direct_user_source": plan["diagnostic_recovery"]["new_direct_user_source"]}
    return root, plan, approval, request, db


class SingleDiagnosticTests(unittest.TestCase):
    def test_exactly_one_success_settles_only_new_call_prior_unchanged_no_tools_or_replay(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_single_success_") as folder:
            root, plan, approval, request, prior = setup_local(Path(folder))
            before = prior.read_bytes()
            provider = ScriptedTransport(plan)
            result = execute_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 1)
            self.assertEqual(result["budget"]["settled"], 1)
            self.assertEqual(result["budget"]["unknown"], 0)
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal(".858"))
            self.assertGreater(Decimal(result["budget"]["occupied_USD_upper"]), Decimal(".858"))
            self.assertEqual(result["environment_tools_executed"], 0)
            self.assertEqual(result["complete_episodes"], 0)
            self.assertEqual(prior.read_bytes(), before)
            self.assertTrue((root / "ACTUAL_RESPONSE_SHAPE.json").is_file())
            with self.assertRaisesRegex(ValueError, "Already attempted"):
                execute_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 1)

    def test_one_decode_failure_retains_both_unknowns_and_safe_actual_shape(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_single_failure_") as folder:
            root, plan, approval, request, prior = setup_local(Path(folder))
            def extra_reasoning(data):
                standard_mock(data)
                data["output"].insert(0, {"type": "reasoning", "summary": []})
                return data
            provider = MockProvider(plan, extra_reasoning)
            before = prior.read_bytes()
            result = execute_once(root, plan, approval, request, provider)
            self.assertEqual(result["calls"][0]["diagnostic"]["validation_stage"], "output_items")
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("1.716"))
            self.assertEqual(result["budget"]["settled"], 0)
            self.assertEqual(provider.calls, 1)
            self.assertEqual(prior.read_bytes(), before)
            shape = strict_json((root / "ACTUAL_RESPONSE_SHAPE.json").read_bytes())
            self.assertTrue(shape["actual_not_reconstruction"])
            self.assertEqual(shape["shape"]["output_count"], 2)

    def test_prior_tamper_and_request_drift_block_before_call_or_new_ledger(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_single_binding_") as folder:
            root, plan, approval, request, prior = setup_local(Path(folder))
            provider = ScriptedTransport(plan)
            changed = deepcopy(request)
            changed["max_output_tokens"] = 16
            with self.assertRaisesRegex(ValueError, "binding mismatch"):
                execute_once(root, plan, approval, changed, provider)
            prior.write_bytes(prior.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "byte binding"):
                execute_once(root, plan, approval, request, provider)
            self.assertEqual(list(root.iterdir()), [])
            self.assertEqual(provider.calls, 0)

    def test_exact_frozen_empty_wal_allowed_but_any_wal_frames_block(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_single_sidecars_") as folder:
            root, plan, approval, request, prior = setup_local(Path(folder))
            recovery = plan["diagnostic_recovery"]
            wal, shm = Path(str(prior) + "-wal"), Path(str(prior) + "-shm")
            wal.write_bytes(b"")
            shm.write_bytes(b"LOCAL_FROZEN_SHM_NOT_SQLITE_READER_INPUT")
            recovery["prior_original_file_sha256"].update({
                wal.name: hashlib.sha256(wal.read_bytes()).hexdigest(),
                shm.name: hashlib.sha256(shm.read_bytes()).hexdigest()})
            verify_prior(recovery)
            wal.write_bytes(b"unapplied-frame")
            recovery["prior_original_file_sha256"][wal.name] = hashlib.sha256(wal.read_bytes()).hexdigest()
            with self.assertRaisesRegex(ValueError, "unapplied WAL"):
                verify_prior(recovery)


if __name__ == "__main__":
    unittest.main()
