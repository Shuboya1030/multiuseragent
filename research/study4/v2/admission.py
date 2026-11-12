"""Static wire, source/authorization binding, and explicitly scoped token-bound proof."""
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
import os
from pathlib import Path
import platform

from .budget import BudgetBlocked, CallCaps
from .contracts import canonical, fingerprint, require, strict_json
from .executor import PROTOCOL, parse_tool
from .mini_request import MODEL, build_provider_request, build_request, validate_output
from .provider_bound import MODEL_MAXIMUM_BOUND, uses_model_maximum
from .response_diagnosis import at_stage
from .recovery_guard import validate_recovery

PRICE = {
    "model": MODEL, "input_per_million_USD": "0.75", "output_per_million_USD": "4.50",
    "surcharge_fraction": "0.10", "source": "https://developers.openai.com/api/docs/pricing",
    "source_read_date": "2026-11-11", "provider_account_region_verified": False,
}
SOURCE_FILES = ("admission.py", "durable.py", "http_transport.py", "mini_request.py",
                "contracts.py", "executor.py", "oracle.py", "npc_rule.py", "budget.py", "provider_bound.py",
                "configs/provider_model_maximum_bound_v1.json", "paid_driver.py", "runtime.py",
                "scheduler.py", "benchmark.py", "configs/ceiling_pilot.json", "response_diagnosis.py",
                "recovery_guard.py", "diagnostic_dispatch.py")


def runtime_binding():
    root = Path(__file__).parent
    return {"protocol": PROTOCOL, "python": platform.python_version(),
            "platform": platform.system(), "source_byte_semantics": "UTF8 LF normalized",
            "source_sha256": {name: hashlib.sha256(root.joinpath(*name.split("/")).read_bytes()
                                                 .replace(b"\r\n", b"\n")).hexdigest()
                              for name in SOURCE_FILES}}


def root_binding(path):
    return hashlib.sha256(os.path.normcase(str(Path(path).resolve())).encode("utf-8")).hexdigest()


def pending_plan():
    caps = asdict(CallCaps(input_tokens=MODEL_MAXIMUM_BOUND["input_tokens"]))
    return {
        "schema": "study4-v2-durable-preflight-3", "run_id": "study4-v2-ceiling-PENDING",
        "mode": "provider", "endpoint": "https://api.openai.com/v1/responses",
        "budget_cap_USD": None, "episodes": [], "runtime": runtime_binding(),
        "price": PRICE.copy(), "caps": caps,
        "max_calls": 4608, "max_episodes": 48, "total_input_tokens": 36_864_000,
        "total_output_tokens": 4_718_592, "max_request_bytes": 1_048_576,
        "max_response_bytes": 1_048_576, "http_timeout_seconds": 30,
        "token_bound": MODEL_MAXIMUM_BOUND.copy(),
        "actual_provider_schema_verified": False,
    }


def validate_binding(plan, approval, root, endpoint, now=None):
    """Executed before lock/file/socket creation. An approval record is not inferred from a cap."""
    if plan["budget_cap_USD"] is None or approval is None:
        raise BudgetBlocked("Independent budget approval pending; no file/network admission")
    from .http_transport import validate_endpoint
    validate_endpoint(endpoint, plan["mode"])
    require(plan["runtime"] == runtime_binding(), "Runtime/source binding changed")
    require(plan["endpoint"] == endpoint and plan["price"] == PRICE, "Endpoint/price/model binding changed")
    caps = CallCaps(**plan["caps"])
    require(caps.input_usd_per_million == PRICE["input_per_million_USD"] and
            caps.output_usd_per_million == PRICE["output_per_million_USD"] and
            caps.surcharge == PRICE["surcharge_fraction"], "Price/cap drift")
    require(type(plan["episodes"]) is list and plan["episodes"] and
            len(set(plan["episodes"])) == len(plan["episodes"]) <= plan["max_episodes"] and
            all(isinstance(e, str) and e for e in plan["episodes"]), "Frozen unique episode schedule required")
    require(all(type(plan[k]) is int and plan[k] > 0 for k in
                ("max_calls", "max_episodes", "total_input_tokens", "total_output_tokens",
                 "max_request_bytes", "max_response_bytes", "http_timeout_seconds")),
            "Explicit positive resource caps required")
    require(approval.get("approved") is True and approval.get("run_id") == plan["run_id"] and
            approval.get("plan_sha256") == fingerprint(plan) and
            approval.get("storage_root_sha256") == root_binding(root) and
            approval.get("budget_cap_USD") == plan["budget_cap_USD"] and approval.get("reference"),
            "Authorization does not exactly match independent run/config/cap/storage")
    current = now or datetime.now(timezone.utc)
    start = datetime.fromisoformat(approval["not_before"])
    end = datetime.fromisoformat(approval["expires"])
    require(start.tzinfo is not None and end.tzinfo is not None and start <= current < end,
            "Authorization not current")
    if plan["mode"] == "local_test":
        require(approval["scope"] == "LOCAL_TEST_NOT_PAID_AUTHORIZATION", "Local scope mismatch")
    else:
        require(plan["mode"] == "provider" and approval["scope"] == "STUDY4_V2_INDEPENDENT_PAID",
                "Paid scope mismatch")
    validate_recovery(plan, approval)
    token_bound(b"{}", plan)
    return caps


def token_bound(body, plan):
    require(isinstance(body, bytes) and len(body) <= plan["max_request_bytes"], "Serialized request byte cap")
    proof = plan["token_bound"]
    if uses_model_maximum(plan):
        require(plan["mode"] in {"provider", "local_test"} and proof["model"] == MODEL and
                plan["caps"]["input_tokens"] == proof["input_tokens"] and
                16 <= plan["caps"]["output_tokens"] <= proof["output_tokens"],
                "Model maximum reservation/source cap mismatch")
        return proof["input_tokens"]
    if (plan["mode"] != "local_test" or proof != {
            "kind": "LOCAL_BYTE_IDENTITY_ONLY", "model": MODEL, "provider_framing_upper": 0}):
        raise BudgetBlocked("Provider token/framing bound unproved; do not assume bytes+4096 is safe")
    return len(body)


def prepare_request(request, operation, plan):
    require(operation in {"control", "question", "ordinary"}, "Only scheduled mini operations")
    require(isinstance(request.get("input"), list) and len(request["input"]) == 2 and
            all(isinstance(item, dict) and isinstance(item.get("content"), str) for item in request["input"]),
            "Only explicit text messages; no image/audio/file/conversation input")
    body = strict_json(request["input"][1]["content"])
    observation = body["state"]
    kwargs = {}
    if operation == "control":
        proposal = body["proposed_ordinary"]
        kwargs["proposed"] = None if proposal is None else parse_tool(canonical(proposal))
    elif operation == "question":
        kwargs = {"person_id": body["person_id"], "assistance": body.get("request_plan")}
    builder = build_provider_request if uses_model_maximum(plan) else build_request
    require(request == builder(operation, observation, **kwargs), "Static public wire/schema/model/billing domain drift")
    require(request["max_output_tokens"] == plan["caps"]["output_tokens"], "Output cap drift")
    raw = canonical(request).encode("utf-8")
    bound = token_bound(raw, plan)
    require(bound <= plan["caps"]["input_tokens"], "Conservative input bound exceeds context cap")
    return raw, bound, observation, kwargs.get("assistance")


def decode_response(raw, operation, observation, assistance, plan, input_bound):
    response = at_stage("response_json", lambda: strict_json(raw))
    def envelope():
        require(isinstance(response, dict), "Response root must be object")
        if uses_model_maximum(plan):
            require(response.get("service_tier") == "default", "Actual service tier drift")
        require(response["model"] == MODEL and response["status"] == "completed" and
                response.get("error") is None and response.get("incomplete_details") is None and
                isinstance(response["id"], str) and response["id"], "Incomplete/model-drift response")
        return response["output"]
    output = at_stage("response_envelope", envelope)
    def message():
        require(isinstance(output, list) and len(output) == 1 and output[0]["type"] == "message" and
                output[0]["role"] == "assistant", "Foreign/multiple/tool response")
        return output[0]["content"]
    content = at_stage("output_items", message)
    def output_text():
        require(isinstance(content, list) and len(content) == 1 and content[0]["type"] == "output_text" and
                isinstance(content[0]["text"], str), "Incomplete/refused/foreign output")
        return content[0]["text"]
    text = at_stage("output_content", output_text)
    def usage():
        incoming, outgoing = response["usage"]["input_tokens"], response["usage"]["output_tokens"]
        require(type(incoming) is int and type(outgoing) is int and 0 <= incoming <= input_bound and
                0 <= outgoing <= plan["caps"]["output_tokens"], "Usage missing/invalid/above reservation")
        return incoming, outgoing
    incoming, outgoing = at_stage("usage", usage)
    parsed = at_stage("application_json", lambda: strict_json(text))
    data = at_stage("application_validation", lambda: validate_output(operation, parsed, observation, assistance))
    return {"data": data, "usage": {"input_tokens": incoming, "output_tokens": outgoing},
            "response_id": response["id"], "model": response["model"]}


def response_diagnostic(raw):
    """Keep useful typed failure evidence without arbitrary response text/header/exception strings."""
    try:
        response = strict_json(raw)
    except ValueError as error:
        return {"json_parse_error_type": type(error).__name__}
    if not isinstance(response, dict):
        return {"root_type": type(response).__name__}
    status = response.get("status")
    usage = response.get("usage")
    return {
        "returned_model_matches": response.get("model") == MODEL,
        "service_tier": response.get("service_tier") if response.get("service_tier") in
                        ("default", "priority", "fast", "flex", "scale", "ultrafast", "auto") else "unrecognized",
        "status": status if status in ("completed", "incomplete", "failed", "cancelled") else "unrecognized",
        "reported_usage_NOT_settlement": {key: value for key, value in usage.items()
                                         if key in {"input_tokens", "output_tokens"} and type(value) is int}
                                        if isinstance(usage, dict) else None,
    }


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--export-pending", type=Path, required=True)
    args = parser.parse_args()
    with args.export_pending.open("x", encoding="utf-8", newline="\n") as out:
        out.write(canonical(pending_plan()) + "\n")
    print("Exported pending config only; no authorization, ledger, key or network.")
