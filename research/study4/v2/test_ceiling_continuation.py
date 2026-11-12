from copy import deepcopy
from decimal import Decimal
import hashlib
import http.client
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from .budget import BudgetBlocked
from .ceiling_continuation import (PROMPT_VERSION, SOURCE, VERSION, make_plan, run_batch,
                                   validate_once, verify_history)
from .contracts import fingerprint
from .durable import BatchBusy, BatchLock, DurableLedger
from .http_transport import HTTPTransport
from .local_ceiling_check import make_case
from .mini_request import build_provider_request
from .test_durable_preflight import approval_for
from .test_paid_driver import ScriptedTransport


def frozen_history(root, run_id):
    return {"root": str(root), "run_id": run_id, "file_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}}


def setup(parent):
    history = []
    for index in range(2):
        root = parent / ("old" + str(index))
        root.mkdir()
        db = root / ("old" + str(index) + ".sqlite3")
        connection = sqlite3.connect(db)
        connection.execute("create table calls(state,reserved,charged,input_tokens,output_tokens)")
        connection.execute("insert into calls values('unknown','.858',null,null,null)")
        connection.commit()
        connection.close()
        (root / ("old" + str(index) + ".lock")).write_bytes(b"0")
        history.append(frozen_history(root, "old" + str(index)))
    root = parent / "validation"
    root.mkdir()
    _, runtime, _, _ = make_case("o-low-team-lunch", "A")
    request = build_provider_request("ordinary", runtime.observe())
    config = {"version": VERSION, "phase": "validation", "new_direct_user_source": SOURCE,
              "prompt_version": PROMPT_VERSION, "history": history, "request_sha256": fingerprint(request)}
    plan = make_plan(config)
    return root, plan, test_approval(root, plan), request


def test_approval(root, plan):
    approval = approval_for(root, plan)
    # Injected transport only: no credentials or HTTP in any test, even with provider-shaped plan.
    approval["scope"] = "STUDY4_V2_INDEPENDENT_PAID"
    approval["continuation_authorization"] = {
        "approved": True, "new_direct_user_source": SOURCE,
        "continuation_sha256": fingerprint(plan["continuation"])}
    return approval


class ContinuationTests(unittest.TestCase):
    def test_transport_error_type_alone_cannot_identify_connect_send_headers_or_read_stage(self):
        failures = (("connect", OSError()),
                    ("request", http.client.CannotSendRequest()),
                    ("getresponse", http.client.RemoteDisconnected()),
                    ("read", http.client.IncompleteRead(b"LOCAL_PARTIAL_NOT_RETURNED")))
        for stage, error in failures:
            with self.subTest(stage=stage), tempfile.TemporaryDirectory(
                    prefix="study4_v2_continuation_transport_") as folder:
                root, plan, approval, request = setup(Path(folder))
                provider = HTTPTransport(plan["endpoint"], plan["mode"], credential="LOCAL_MOCK_NOT_A_KEY")
                with patch("research.study4.v2.http_transport.http.client.HTTPSConnection") as factory:
                    connection = factory.return_value
                    if stage == "read":
                        response = connection.getresponse.return_value.__enter__.return_value
                        response.status = 200
                        response.getheader.return_value = "application/json"
                        response.read.side_effect = error
                    else:
                        getattr(connection, stage).side_effect = error
                    result = validate_once(root, plan, approval, request, provider)
                self.assertEqual(result["error_type"], "TransportFailure")
                self.assertEqual(result["calls"][0]["diagnostic"], {})
                self.assertIsNone(result["calls"][0]["response_bytes"])
                self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("2.574"))
                self.assertFalse((root / "ACTUAL_RESPONSE_SHAPE.json").exists())

    def test_one_success_prior_unknowns_unchanged_then_same_48_slot_batch_with_cumulative_cost(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_continuation_success_") as folder:
            root, plan, approval, request = setup(Path(folder))
            before = deepcopy(plan["continuation"]["history"])
            provider = ScriptedTransport(plan)
            result = validate_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 1)
            self.assertEqual(result["budget"]["settled"], 1)
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("1.716"))
            self.assertEqual(result["environment_tools_executed"], 0)
            with self.assertRaisesRegex(ValueError, "Already attempted"):
                validate_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 1)
            self.assertEqual(verify_history(before), (Decimal("1.716"), Decimal(0)))
            history = before + [frozen_history(root, plan["run_id"])]
            batch_root = Path(folder) / "batch"
            batch_root.mkdir()
            config = {**plan["continuation"], "phase": "batch", "history": history}
            config.pop("request_sha256")
            batch_plan = make_plan(config)
            batch_approval = test_approval(batch_root, batch_plan)
            batch_provider = ScriptedTransport(batch_plan)
            batch = run_batch(batch_root, batch_plan, batch_approval, batch_provider)
            self.assertEqual(batch["status"], "complete")
            self.assertEqual(len(batch["completed"]), 48)
            self.assertEqual(batch["budget"]["unknown"], 0)
            self.assertEqual(Decimal(batch["budget"]["prior_unknown_held_USD"]), Decimal("1.716"))
            self.assertEqual(Decimal(batch["budget"]["prior_settled_USD_upper"]),
                             Decimal(result["calls"][0]["charged"]))
            calls = batch_provider.calls
            with self.assertRaisesRegex(ValueError, "started before"):
                run_batch(batch_root, batch_plan, batch_approval, batch_provider)
            self.assertEqual(batch_provider.calls, calls)

    def test_failed_validation_retains_2574_and_cannot_unlock_batch_or_repeat(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_continuation_unknown_") as folder:
            root, plan, approval, request = setup(Path(folder))
            provider = ScriptedTransport(plan, invalid=True)
            result = validate_once(root, plan, approval, request, provider)
            self.assertEqual(result["calls"][0]["diagnostic"]["validation_stage"], "usage")
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("2.574"))
            history = plan["continuation"]["history"] + [frozen_history(root, plan["run_id"])]
            with self.assertRaisesRegex(ValueError, "not legally settled"):
                verify_history(history)
            with self.assertRaisesRegex(ValueError, "Already attempted"):
                validate_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 1)

    def test_source_history_authorization_or_request_drift_no_send(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_continuation_binding_") as folder:
            root, plan, approval, request = setup(Path(folder))
            provider = ScriptedTransport(plan)
            bad = deepcopy(approval)
            bad["continuation_authorization"]["new_direct_user_source"] = {"id": "NOT_APPROVED", "revision": 1}
            with self.assertRaisesRegex(ValueError, "explicit continuation"):
                validate_once(root, plan, bad, request, provider)
            changed = deepcopy(request)
            changed["max_output_tokens"] = 16
            with self.assertRaisesRegex(ValueError, "exact next-action"):
                validate_once(root, plan, approval, changed, provider)
            original = Path(plan["continuation"]["history"][0]["root"]) / "old0.sqlite3"
            original.write_bytes(original.read_bytes() + b"\n")
            with self.assertRaisesRegex(ValueError, "byte binding"):
                validate_once(root, plan, approval, request, provider)
            self.assertEqual(provider.calls, 0)
            self.assertEqual(list(root.iterdir()), [])

    def test_old_batch_mutex_excludes_second_continuation_before_send(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_continuation_mutex_") as folder:
            root, plan, approval, request = setup(Path(folder))
            prior = plan["continuation"]["history"][0]
            lock = BatchLock(Path(prior["root"]) / (prior["run_id"] + ".lock"))
            try:
                provider = ScriptedTransport(plan)
                with self.assertRaises(BatchBusy):
                    validate_once(root, plan, approval, request, provider)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(list(root.iterdir()), [])
            finally:
                lock.close()

    def test_remaining_less_than_reserve_counts_both_unknowns_before_send(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_continuation_admission_") as folder:
            root, plan, approval, request = setup(Path(folder))
            provider = ScriptedTransport(plan)
            ledger = DurableLedger(root, plan, approval, create=True)
            try:
                with patch.object(ledger, "cap", Decimal("2.573999")):
                    with self.assertRaises(BudgetBlocked):
                        ledger.call(plan["episodes"][0], "ordinary", 0, request, provider)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(ledger.status()["calls"], 0)
            finally:
                ledger.close()


if __name__ == "__main__":
    unittest.main()
