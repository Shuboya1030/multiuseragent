from copy import deepcopy
from decimal import Decimal
import hashlib
from pathlib import Path
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from .admission import decode_response, pending_plan, prepare_request
from .budget import BudgetBlocked
from .contracts import canonical, fingerprint, strict_json
from .durable import DurableLedger
from .local_ceiling_check import ScriptedPublicMini, make_case
from .native_driver import (RECOVERY_VERSION, SOURCE, NativeMini, make_plan, run_batch,
                            validate_once, verify_history)
from .native_protocol import (BOUND, DECISIONS, VERSION, build_native_request, one_function,
                              validate_history)
from .paid_driver import Journal
from .response_diagnosis import ResponseStageError
from .test_durable_preflight import approval_for


def native_plan(root):
    plan = pending_plan()
    plan.update(run_id="LOCAL_NATIVE_FUNCTIONS", mode="local_test",
                endpoint="http://127.0.0.1:9/v1/responses", budget_cap_USD="50.00",
                episodes=["ep-0"], native_protocol=VERSION, token_bound=deepcopy(BOUND))
    return plan, approval_for(root, plan)


def response(data=None, operation="ordinary", output=None):
    data = data or {"tool": "list_files", "arguments": "{}"}
    name = data["tool"] if operation == "ordinary" else DECISIONS[operation]
    arguments = data["arguments"] if operation == "ordinary" else canonical(data)
    return {"id": "LOCAL_RESPONSE", "model": BOUND["model"], "status": "completed", "service_tier": "default",
            "error": None, "incomplete_details": None, "usage": {"input_tokens": 100, "output_tokens": 20},
            "output": output if output is not None else [{"type": "function_call", "call_id": "LOCAL_CALL",
                                                         "name": name, "arguments": arguments, "status": "completed"}]}


class NativeTransport:
    def __init__(self, plan, invalid=False):
        self.endpoint, self.mode, self.calls = plan["endpoint"], plan["mode"], 0
        self.scripted, self.invalid = ScriptedPublicMini(), invalid

    def send(self, permit, body):
        permit.consume(body, self.endpoint, self.mode)
        self.calls += 1
        request = strict_json(body)
        content = strict_json(request["input"][-1]["content"])
        operation = content["operation"]
        scripted_request = {"input": [request["input"][0], request["input"][-1]]}
        data = strict_json(self.scripted(scripted_request)["output_text"])
        result = response(data, operation)
        result["output"][0]["call_id"] = "LOCAL_CALL_" + str(self.calls)
        if self.invalid:
            result["output"].append(deepcopy(result["output"][0]))
        return canonical(result).encode()


def frozen(root, run_id):
    return {"root": str(root), "run_id": run_id, "file_sha256": {
        p.name: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.iterdir() if p.is_file()}}


def history_fixture(parent):
    history = []
    for index in range(5):
        root = parent / ("history" + str(index))
        root.mkdir()
        run = "history" + str(index)
        connection = sqlite3.connect(root / (run + ".sqlite3"))
        connection.execute("create table calls(state,reserved,charged,input_tokens,output_tokens)")
        if index in {0, 1, 2, 4}:
            connection.execute("insert into calls values('unknown','.858',null,null,null)")
        if index == 3:
            connection.execute("insert into calls values('settled','.858','.001205325',1275,31)")
        if index == 4:
            usages = [(1275, 78), (857, 19), (1402, 31), (1500, 31), (1598, 37),
                      (1696, 37), (1251, 25), (1794, 31), (1892, 37)]
            from .budget import CallCaps
            for incoming, outgoing in usages:
                connection.execute("insert into calls values('settled','.858',?,?,?)",
                                   (str(CallCaps().charge(incoming, outgoing)), incoming, outgoing))
        connection.commit()
        connection.close()
        (root / (run + ".lock")).write_bytes(b"0")
        history.append(frozen(root, run))
    return history


def recovery_approval(root, plan):
    approval = approval_for(root, plan)
    approval["scope"] = "STUDY4_V2_INDEPENDENT_PAID"
    approval["native_recovery_authorization"] = {
        "approved": True, "new_direct_user_source": SOURCE,
        "recovery_sha256": fingerprint(plan["native_recovery"])}
    return approval


class NativeProtocolTests(unittest.TestCase):
    def test_all_arms_same_native_surface_and_unchanged_strict_argument_fields(self):
        requests = []
        for arm in "ABCD":
            _, runtime, _, _ = make_case("o-low-team-lunch", arm)
            requests.append(build_native_request("ordinary", runtime.observe()))
        self.assertTrue(all(r == requests[0] for r in requests))
        self.assertEqual({f["name"] for f in requests[0]["tools"]},
                         {"read_file", "write_file", "list_files", "post_channel", "submit"})
        self.assertEqual(requests[0]["tool_choice"], "required")
        self.assertFalse(requests[0]["parallel_tool_calls"])
        for function in requests[0]["tools"]:
            self.assertTrue(function["strict"])
            self.assertFalse(function["parameters"]["additionalProperties"])
            self.assertEqual(set(function["parameters"]["required"]), set(function["parameters"]["properties"]))

    def test_reasoning_and_text_metadata_do_not_count_as_actions_but_zero_many_unknown_refusal_fail(self):
        _, runtime, _, _ = make_case("o-low-team-lunch", "A")
        plan, _ = native_plan(Path("."))
        call = response()["output"][0]
        metadata = [{"type": "reasoning", "summary": [{"type": "summary_text", "text": "LOCAL_METADATA"}]},
                    {"type": "message", "role": "assistant", "content": [
                        {"type": "output_text", "text": "Non-executable commentary."}]}]
        data = decode_response(canonical(response(output=metadata + [call])).encode(),
                               "ordinary", runtime.observe(), None, plan, 272000)
        self.assertEqual(data["data"]["tool"], "list_files")
        for output in ([], metadata, [call, deepcopy(call)], [{"type": "web_search_call"}],
                       [{**call, "name": "unknown"}],
                       [call, {"type": "message", "role": "assistant", "content": [
                           {"type": "refusal", "refusal": "LOCAL_REFUSAL"}]}]):
            with self.subTest(output=output), self.assertRaises(ResponseStageError):
                decode_response(canonical(response(output=output)).encode(),
                                "ordinary", runtime.observe(), None, plan, 272000)
        for args in ('{"path":"x","extra":"y"}', '{"path":3}', "{", '["not an object"]'):
            with self.subTest(args=args), self.assertRaises(ResponseStageError):
                decode_response(canonical(response(output=[{**call, "name": "read_file", "arguments": args}])).encode(),
                                "ordinary", runtime.observe(), None, plan, 272000)

    def test_no_builtin_parallel_or_billing_scope_drift_and_full_model_reserve(self):
        _, runtime, _, _ = make_case("o-low-team-lunch", "A")
        request = build_native_request("ordinary", runtime.observe())
        plan, _ = native_plan(Path("."))
        self.assertEqual(prepare_request(request, "ordinary", plan)[1], 272000)
        for key, value in (("tools", [{"type": "web_search"}]), ("parallel_tool_calls", True),
                           ("service_tier", "auto"), ("tool_choice", "auto"),
                           ("context_management", [{"type": "compaction"}]), ("conversation", "x")):
            with self.subTest(key=key):
                changed = {**request, key: value}
                with self.assertRaises(ValueError):
                    prepare_request(changed, "ordinary", plan)
        plan["token_bound"]["billing_scope"] = "unapproved"
        with self.assertRaises(ValueError):
            prepare_request(request, "ordinary", plan)

    def test_call_result_links_and_public_only_input(self):
        _, runtime, _, _ = make_case("o-low-team-lunch", "A")
        call = response()["output"][0]
        history = [call, {"type": "function_call_output", "call_id": call["call_id"],
                          "output": canonical({"status": "applied", "public_event_id": "event-1"})}]
        request = build_native_request("ordinary", runtime.observe(), native_history=history)
        self.assertEqual(request["input"][1:-1], history)
        for bad in ([call], [call, {**history[-1], "call_id": "MISMATCH"}], history + history):
            with self.assertRaises(ValueError):
                validate_history(bad)
        private = runtime.observe()
        private["gold_dag"] = {"LOCAL_PRIVATE": True}
        with self.assertRaises(ValueError):
            build_native_request("ordinary", private)

    def test_actual_runner_scripted48_ASK_reply_refresh_results_binding_and_no_replay(self):
        with tempfile.TemporaryDirectory(prefix="study4_native48_") as folder:
            parent = Path(folder)
            history = history_fixture(parent)
            self.assertEqual(verify_history(history)["held"], Decimal("3.432"))
            root = parent / "validation"
            root.mkdir()
            _, runtime, _, _ = make_case("o-low-team-lunch", "A")
            request = build_native_request("ordinary", runtime.observe())
            config = {"version": RECOVERY_VERSION, "new_direct_user_source": SOURCE, "protocol": VERSION,
                      "phase": "validation", "history": history, "request_sha256": fingerprint(request)}
            plan = make_plan(config)
            approval = recovery_approval(root, plan)
            transport = NativeTransport(plan)
            result = validate_once(root, plan, approval, request, transport)
            self.assertEqual(result["budget"]["settled"], 1)
            self.assertEqual(result["environment_tools_executed"], 0)
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("3.432"))
            history.append(frozen(root, plan["run_id"]))
            batch = parent / "batch"
            batch.mkdir()
            config = {**config, "phase": "batch", "history": history}
            config.pop("request_sha256")
            plan = make_plan(config)
            approval = recovery_approval(batch, plan)
            transport = NativeTransport(plan)
            result = run_batch(batch, plan, approval, transport)
            self.assertEqual(result["status"], "complete")
            self.assertEqual(len(result["completed"]), 48)
            self.assertTrue(all(row["score"]["official"]["base_pass"] for row in result["completed"]))
            count = transport.calls
            with self.assertRaises(ValueError):
                run_batch(batch, plan, approval, transport)
            self.assertEqual(transport.calls, count)
            events = [strict_json(line) for line in (batch / "events.jsonl").read_text(encoding="utf-8").splitlines()]
            receipts = [e for e in events if e["kind"] == "native_function_result"]
            self.assertTrue(any(e["public_result"]["status"] == "proposal_discarded_not_executed" for e in receipts))
            self.assertTrue(any(e["public_result"].get("event", {}).get("kind") == "post_channel" for e in receipts))
            self.assertTrue(any(e["kind"] == "runtime_event" and e["event"]["kind"] == "read_messages" for e in events))
            for event in events:
                if event["kind"] == "model_request":
                    validate_history(event["public_request"]["input"][1:-1])
                    self.assertNotIn("gold_dag", canonical(event["public_request"]))

    def test_multiple_calls_unknown_retains_all_old_cost_no_second_call_or_tool(self):
        with tempfile.TemporaryDirectory(prefix="study4_native_unknown_") as folder:
            parent = Path(folder)
            root = parent / "validation"
            root.mkdir()
            history = history_fixture(parent)
            _, runtime, _, _ = make_case("o-low-team-lunch", "A")
            request = build_native_request("ordinary", runtime.observe())
            config = {"version": RECOVERY_VERSION, "new_direct_user_source": SOURCE, "protocol": VERSION,
                      "phase": "validation", "history": history, "request_sha256": fingerprint(request)}
            plan = make_plan(config)
            transport = NativeTransport(plan, invalid=True)
            result = validate_once(root, plan, recovery_approval(root, plan), request, transport)
            self.assertEqual(result["budget"]["unknown"], 1)
            self.assertEqual(Decimal(result["budget"]["held_USD_upper"]), Decimal("4.290"))
            self.assertEqual(Decimal(result["budget"]["occupied_USD_upper"]), Decimal("4.303762650"))
            self.assertEqual(result["calls"][0]["diagnostic"]["validation_stage"], "output_items")
            self.assertEqual(result["environment_tools_executed"], 0)
            self.assertEqual(transport.calls, 1)
            with self.assertRaises(ValueError):
                validate_once(root, plan, recovery_approval(root, plan), request, transport)
            self.assertEqual(transport.calls, 1)
            self.assertEqual(verify_history(history)["settled"], Decimal(".013762650"))


if __name__ == "__main__":
    unittest.main()
