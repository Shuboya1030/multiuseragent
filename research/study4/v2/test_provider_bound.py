from copy import deepcopy
from decimal import Decimal
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from .admission import pending_plan, prepare_request, token_bound
from .budget import BudgetBlocked
from .contracts import canonical
from .durable import DurableLedger
from .local_ceiling_check import make_case
from .mini_request import build_provider_request, build_request
from .test_durable_preflight import MockProvider, approval_for


def model_max_config(root, cap="1.00"):
    plan = pending_plan()
    plan.update(run_id="MODEL_MAX_TEMP_TEST", mode="local_test",
                endpoint="http://127.0.0.1:9/v1/responses", budget_cap_USD=cap, episodes=["ep-0"])
    return plan, approval_for(root, plan)


def control_request():
    _, runtime, _, _ = make_case("m-low-customer-mailing", "A")
    return build_provider_request("control", runtime.observe())


def standard_mock(data):
    data["service_tier"] = "default"
    return data


class ModelMaximumTests(unittest.TestCase):
    def test_public_actions_unchanged_and_whole_model_bound_not_prompt_token_estimate(self):
        _, runtime, _, _ = make_case("m-low-customer-mailing", "A")
        observation = runtime.observe()
        plan = pending_plan()
        for operation, kwargs in (("control", {}), ("ordinary", {}),
                                  ("question", {"person_id": observation["task"]["people"][0]["person_id"]})):
            with self.subTest(operation=operation):
                request = build_provider_request(operation, observation, **kwargs)
                self.assertEqual(request["input"], build_request(operation, observation, **kwargs)["input"])
                raw, bound, _, _ = prepare_request(request, operation, plan)
                self.assertEqual(bound, 272000)
                self.assertNotEqual(len(raw), bound)
        self.assertEqual(token_bound(b"{}", plan), 272000)

    def test_durable_reserve_full_max_settle_reported_mock_usage_and_replay_without_send(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_model_max_") as folder:
            root = Path(folder)
            plan, approval = model_max_config(root)
            request = control_request()
            provider = MockProvider(plan, standard_mock)
            ledger = DurableLedger(root, plan, approval, create=True)
            try:
                result = ledger.call("ep-0", "control", 0, request, provider)
                self.assertEqual(Decimal(provider.observed_states[0][1]), Decimal(".858000"))
                row = ledger.connection.execute("select * from calls").fetchone()
                self.assertEqual((row["input_bound"], row["output_bound"]), (272000, 128000))
                expected = ledger.caps.charge(len(canonical(request).encode("utf-8")), 10)
                self.assertEqual(Decimal(row["charged"]), expected)
                self.assertLess(expected, Decimal(row["reserved"]))
                self.assertEqual(Decimal(ledger.status()["held_USD_upper"]), 0)
                self.assertEqual(result["usage"]["output_tokens"], 10)
            finally:
                ledger.close()
            reopened = DurableLedger(root, plan, approval, create=False)
            try:
                retry = MockProvider(plan, standard_mock)
                self.assertTrue(reopened.call("ep-0", "control", 0, request, retry)["replayed_without_send"])
                self.assertEqual(retry.calls, 0)
            finally:
                reopened.close()

    def test_remaining_less_than_full_reserve_blocks_even_after_small_settlement(self):
        for cap, completed in ((".857999", 0), (".858000", 1), ("1.00", 2)):
            with self.subTest(cap=cap), tempfile.TemporaryDirectory(prefix="study4_v2_model_remaining_") as folder:
                root = Path(folder)
                plan, approval = model_max_config(root, cap)
                ledger = DurableLedger(root, plan, approval, create=True)
                provider = MockProvider(plan, standard_mock)
                try:
                    for index in range(completed):
                        ledger.call("ep-0", "control", index, control_request(), provider)
                    if completed < 2:
                        with self.assertRaises(BudgetBlocked):
                            ledger.call("ep-0", "control", completed, control_request(), provider)
                    self.assertEqual(provider.calls, completed)
                    self.assertEqual(ledger.status()["calls"], completed)
                finally:
                    ledger.close()

    def test_unknown_usage_tier_or_overbound_keeps_full_max_after_restart(self):
        def transformed(kind):
            def transform(data):
                standard_mock(data)
                if kind == "missing_usage":
                    del data["usage"]
                elif kind == "nonstandard_tier":
                    data["service_tier"] = "priority"
                elif kind == "missing_tier":
                    del data["service_tier"]
                else:
                    data["usage"]["input_tokens"] = 272001
                return data
            return transform
        for kind in ("missing_usage", "nonstandard_tier", "missing_tier", "overbound"):
            with self.subTest(kind=kind), tempfile.TemporaryDirectory(prefix="study4_v2_model_unknown_") as folder:
                root = Path(folder)
                plan, approval = model_max_config(root)
                ledger = DurableLedger(root, plan, approval, create=True)
                provider = MockProvider(plan, transformed(kind))
                try:
                    with self.assertRaises((ValueError, KeyError)):
                        ledger.call("ep-0", "control", 0, control_request(), provider)
                    self.assertEqual(ledger.status()["unknown"], 1)
                    self.assertEqual(Decimal(ledger.status()["held_USD_upper"]), Decimal(".858000"))
                finally:
                    ledger.close()
                reopened = DurableLedger(root, plan, approval, create=False)
                try:
                    with self.assertRaises(BudgetBlocked):
                        reopened.call("ep-0", "control", 1, control_request(), provider)
                    self.assertEqual(provider.calls, 1)
                    self.assertEqual(Decimal(reopened.status()["held_USD_upper"]), Decimal(".858000"))
                finally:
                    reopened.close()

    def test_unsupported_billable_modes_rejected_before_reserve_or_transport(self):
        mutations = [
            ("tools", [{"type": "web_search"}]), ("tools", [{"type": "code_interpreter"}]),
            ("context_management", [{"type": "compaction", "compact_threshold": 1000}]),
            ("service_tier", "auto"), ("service_tier", "priority"),
            ("prompt_cache_retention", "12h"), ("conversation", "unapproved"),
            ("previous_response_id", "unapproved"), ("model", "gpt-5.4-mini"),
            ("background", True), ("max_output_tokens", 128000),
        ]
        with tempfile.TemporaryDirectory(prefix="study4_v2_model_scope_") as folder:
            root = Path(folder)
            plan, approval = model_max_config(root)
            ledger = DurableLedger(root, plan, approval, create=True)
            provider = MockProvider(plan, standard_mock)
            try:
                for key, value in mutations:
                    with self.subTest(key=key, value=value):
                        request = deepcopy(control_request())
                        request[key] = value
                        with self.assertRaises(ValueError):
                            ledger.call("ep-0", "control", 0, request, provider)
                request = control_request()
                request["input"][1]["content"] = [{"type": "input_image", "image_url": "not-fetched"}]
                with self.assertRaisesRegex(ValueError, "Only explicit text"):
                    ledger.call("ep-0", "control", 0, request, provider)
                self.assertEqual(provider.calls, 0)
                self.assertEqual(ledger.status()["calls"], 0)
            finally:
                ledger.close()

    def test_real_provider_dispatch_still_blocks_without_independent_approval_before_any_files_or_dns(self):
        with tempfile.TemporaryDirectory(prefix="study4_v2_model_pending_") as folder:
            root = Path(folder)
            plan = pending_plan()
            self.assertIsNone(plan["budget_cap_USD"])
            with patch("socket.getaddrinfo") as dns, patch("socket.create_connection") as connect:
                with self.assertRaises(BudgetBlocked):
                    DurableLedger(root, plan, None, create=True)
                self.assertEqual(list(root.iterdir()), [])
                dns.assert_not_called()
                connect.assert_not_called()


if __name__ == "__main__":
    unittest.main()
