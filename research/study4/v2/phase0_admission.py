"""Versioned Phase0 authorization and all-call admission, reusing the durable HTTP ledger."""
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime, timezone
import hashlib
from pathlib import Path

from .admission import root_binding, runtime_binding as shared_binding
from .budget import BudgetBlocked, CallCaps
from .contracts import PROTOCOL, canonical, fingerprint, require, strict_json
from .mini_request import MODEL
from .native_protocol import BOUND, one_function
from .oracle import validate_public_observation
from .phase0 import (ARCHIVES, MAX_ACTIONS, NPC_PUBLISHED_SOURCE_SHA, OPERATION_LIMITS, SOURCE, VERSION, VENDOR,
                     build_request, load_case, npc_system, schedule)
from .phase0 import restore_public_state
from .response_diagnosis import at_stage

PRICE = {"model": MODEL, "input_per_million_USD": "0.75", "output_per_million_USD": "4.50",
         "surcharge_fraction": "0.10", "source_read_date": "2026-11-12",
         "sources": ["https://developers.openai.com/api/docs/models/gpt-5.4-mini",
                     "https://developers.openai.com/api/docs/pricing"],
         "billing_scope": "standard-text-local-functions-no-paid-builtins-no-compaction"}


def runtime_binding():
    shared = shared_binding()
    root = Path(__file__).parent
    shared["phase0_sources"] = {name: hashlib.sha256((root / name).read_bytes().replace(b"\r\n", b"\n")).hexdigest()
                               for name in ("phase0.py", "phase0_admission.py", "phase0_analysis.py",
                                            "reference_completion.py", "phase0_recovery.py",
                                            "phase0_derivation_recovery.py", "phase0_context_recovery.py",
                                            "request_pacing.py")}
    shared["phase0_assets"] = {name: hashlib.sha256((ARCHIVES / name).read_bytes()).hexdigest()
                              for name in ("tasks.zip", "context.zip")}
    shared["phase0_roster"] = hashlib.sha256((VENDOR / "organization" / "roster.json").read_bytes()).hexdigest()
    return shared


def make_plan(history, inherited, *, local_test=False, recovery_source=None):
    if not local_test:
        raise BudgetBlocked("Reference-v5 repair is offline only; paid recovery requires a new reviewed binding")
    slots = schedule()
    systems = set()
    for tid in {s["task_id"] for s in slots}:
        case = load_case(tid)
        systems.update(hashlib.sha256(npc_system(person, scenario).encode()).hexdigest()
                       for person, scenario in case.scenarios.items())
    return {"schema": VERSION, "phase0_protocol": VERSION,
            "run_id": "study4-formal-phase0-240-20261112-v2",
            "mode": "local_test" if local_test else "provider",
            "endpoint": "http://127.0.0.1:9/v1/responses" if local_test else "https://api.openai.com/v1/responses",
            "budget_cap_USD": "50.00", "runtime": runtime_binding(), "price": deepcopy(PRICE),
            "token_bound": deepcopy(BOUND), "caps": asdict(CallCaps(input_tokens=272000, output_tokens=2048)),
            "max_calls": 240 * 192, "max_episodes": 241 if local_test else 240,
            "total_input_tokens": 240 * 192 * 272000,
            "total_output_tokens": 240 * 192 * 128000,
            "max_request_bytes": 1_048_576, "max_response_bytes": 1_048_576, "http_timeout_seconds": 30,
            "operation_limits": deepcopy(OPERATION_LIMITS), "max_actions": MAX_ACTIONS,
            "episodes": (["phase0-preflight"] if local_test else []) + [
                s["episode_id"] for s in slots], "slots": slots,
            "history": deepcopy(history), "inherited": deepcopy(inherited),
            "direct_user_source": deepcopy(SOURCE),
            "npc": {"backend": "controlled_rest_conversational_v5", "model": MODEL,
                    "same_person_history_only": True, "allowed_system_sha256": sorted(systems),
                    "source_archive": "R1/context.zip", "source_implementation_sha256":
                    "07e7b828063a63dccaf3bffc9f678c1c1f8608bae2e64b159b49cacdbc994744",
                    "published_source_sha256": NPC_PUBLISHED_SOURCE_SHA},
            "scope": "Formal exposed60x4x1, nativeA/C and gold when-whomB/D, publicwhatC/D; original cumulative50",
            "statistics": {"repeats_per_task": 1, "equal_weight_60_tasks": True,
                           "single_repeat_not_repeat_stability": True,
                           "mean_delta_gate": ".10", "contrast": "B-A OR D-A",
                           "must_optional_separate": True, "CI_is_not_extra_Phase0_gate": True,
                           "missing_or_unknown_not_zero": True},
            "fresh_only": True, "automatic_retry": False,
            "reference_progress": "study4-reference-completion-5-offline-paid-recovery-disabled"}


def validate_binding(plan, approval, root, endpoint, now=None):
    if plan.get("budget_cap_USD") is None or approval is None:
        raise BudgetBlocked("No matching Phase0 authority; no key/file/network")
    recovery = plan.get("reference_recovery")
    derivation = recovery is not None and recovery.get("version") == (
        "study4-phase0-reference-v7-source-derivation-continuation-1")
    paced = recovery is not None and recovery.get("version") == (
        "study4-phase0-reference-v8-paced-continuation-1")
    if plan.get("mode") == "provider":
        if recovery is None:
            raise BudgetBlocked("Old full240 provider plan remains paused; reviewed214 binding required")
        if paced:
            from .phase0_context_recovery import validate_review
        elif derivation:
            from .phase0_derivation_recovery import validate_review
        else:
            from .phase0_recovery import validate_review
        validate_review(plan, approval)
    from .phase0_recovery import CONTINUE_SOURCE
    if paced:
        from .phase0_context_recovery import SOURCE as expected_source
    else:
        expected_source = CONTINUE_SOURCE if recovery is not None else SOURCE
    if plan.get("mode") not in {"provider", "local_test"} or plan.get("direct_user_source") != expected_source:
        raise BudgetBlocked("Only current direct240 recovery or local tests")
    from .http_transport import validate_endpoint
    validate_endpoint(endpoint, plan["mode"])
    require(plan["phase0_protocol"] == VERSION and plan["schema"] == VERSION and
            plan["direct_user_source"] == expected_source, "Exact new formal Phase0 scope/source required")
    require(plan["runtime"] == runtime_binding() and plan["price"] == PRICE and
            plan["endpoint"] == endpoint and plan["token_bound"] == BOUND,
            "Frozen Phase0 source/price/endpoint/domain drift")
    require(plan["caps"] == asdict(CallCaps(input_tokens=272000, output_tokens=2048)) and
            plan["operation_limits"] == OPERATION_LIMITS and plan["max_actions"] == MAX_ACTIONS,
            "Same frozen ordinary/NPC opportunity and token caps")
    expected_slots = schedule() if recovery is None else plan["slots"]
    remaining = 174 if paced else (199 if derivation else 214)
    expected_calls = (240 if recovery is None else remaining) * 192
    require(plan["slots"] == expected_slots and plan["episodes"] == (
        ["phase0-preflight"] if plan["mode"] == "local_test" else []) + [
        s["episode_id"] for s in (plan["slots"] if recovery is None else plan["fresh_slots"])],
        "Frozen complete60x4x1 target/fresh schedule changed")
    require(plan["budget_cap_USD"] == "50.00" and plan["max_calls"] == expected_calls and
            plan["max_episodes"] == (241 if plan["mode"] == "local_test" else (240 if recovery is None else remaining))
            and plan["http_timeout_seconds"] == 30 and
            plan["max_request_bytes"] == plan["max_response_bytes"] == 1_048_576,
            "Original cumulative50 and frozen resource bounds")
    require(plan["total_input_tokens"] == plan["max_calls"] * 272000 and
            plan["total_output_tokens"] == plan["max_calls"] * 128000,
            "Aggregate token bounds cannot become an unintended early cutoff")
    if plan["mode"] == "provider":
        if paced:
            from .phase0_context_recovery import INHERITED
        elif derivation:
            from .phase0_derivation_recovery import INHERITED
        else:
            from .phase0_recovery import INHERITED
        require(plan["inherited"] == INHERITED and len(plan["history"]) == (
            13 if paced else (12 if derivation else 11)),
                "All1040original calls, held unknown and paid18prefix remain counted")
    require(approval.get("approved") is True and approval.get("run_id") == plan["run_id"] and
            approval.get("plan_sha256") == fingerprint(plan) and approval.get("storage_root_sha256") == root_binding(root)
            and approval.get("budget_cap_USD") == "50.00" and approval.get("direct_user_source") == expected_source
            and approval.get("reference"), "Formal authority must match exact plan/root/cap/source")
    expected_scope = ("LOCAL_TEST_NOT_PAID_AUTHORIZATION" if plan["mode"] == "local_test"
                      else ("STUDY4_FORMAL_PHASE0_240_PATH66_REMAIN174_PACED_SAME50" if paced else
                            "STUDY4_FORMAL_PHASE0_240_PATH41_REMAIN199_SAME50" if derivation
                            else "STUDY4_FORMAL_PHASE0_240_AC26_FRESH214_SAME50"))
    require(approval.get("scope") == expected_scope, "Formal scope is not old48/another50")
    at = now or datetime.now(timezone.utc)
    start, end = datetime.fromisoformat(approval["not_before"]), datetime.fromisoformat(approval["expires"])
    require(start.tzinfo is not None and end.tzinfo is not None and start <= at < end, "Formal approval not current")
    return CallCaps(**plan["caps"])


def public_state(observation):
    view = deepcopy(observation)
    require(view["protocol"] == VERSION, "Only formal public observation")
    view["protocol"] = PROTOCOL
    for event in view["history"]:
        require(set(event) <= {
            "event_id", "kind", "action", "person_id", "message_id", "content", "in_reply_to", "path",
            "channel", "tool", "answer", "reason", "bridge_submitted", "exception_type", "business_outcome",
            "timestamp", "error_code", "applied"}, "Unknown/private formal history field")
        for key in ("timestamp", "error_code", "applied"):
            event.pop(key, None)
    validate_public_observation(view)


def validate_history(history):
    pending, seen = [], set()
    allowed = {"read_file", "write_file", "list_files", "post_channel", "submit", "ask_colleague"}
    for item in history:
        if item.get("type") == "function_call_output":
            call = one_function(pending, allowed_names=allowed)
            require(set(item) == {"type", "call_id", "output"} and
                    item["call_id"] == call["call_id"] and call["call_id"] not in seen and
                    isinstance(item["output"], str), "Native receipts must be unique and matched")
            seen.add(call["call_id"])
            pending = []
        else:
            pending.append(item)
    require(not pending, "No unresolved native history may enter another paid call")


def prepare_request(request, operation, plan):
    require(operation in OPERATION_LIMITS, "Formal executor/question/NPC only")
    require(request["model"] == MODEL and len(canonical(request).encode()) <= plan["max_request_bytes"],
            "Model or request byte cap drift")
    if operation == "npc":
        dialogue = request["input"]
        require(isinstance(dialogue, list) and dialogue and dialogue[0]["role"] == "system" and all(
            set(m) == {"role", "content"} and isinstance(m["content"], str) and
            m["role"] in ({"system"} if i == 0 else {"user", "assistant"})
            for i, m in enumerate(dialogue)), "Only isolated same-person natural NPC dialogue")
        require(hashlib.sha256(dialogue[0]["content"].encode()).hexdigest() in
                plan["npc"]["allowed_system_sha256"], "NPC private system outside frozen R1 scenarios")
        expected = build_request("npc", dialogue=dialogue)
        observation, context = None, {"mode": "npc"}
    else:
        require(isinstance(request["input"], list) and len(request["input"]) >= 2, "Explicit public state")
        body = strict_json(request["input"][-1]["content"])
        require(set(body) == {"protocol", "mode", "state", "person_id", "history_representation"} and
                body["protocol"] == VERSION and
                body["history_representation"] == "native_receipt_events_then_state_tail",
                "Only formal public request body")
        mode = body["mode"]
        require(mode in ({"question"} if operation == "question" else {"native", "ordinary"}), "Operation mismatch")
        history = request["input"][1:-1]
        validate_history(history)
        observation = restore_public_state(body["state"], history)
        public_state(observation)
        expected = build_request(mode, observation, person=body["person_id"], history=history)
        context = {"mode": mode, "person_id": body["person_id"]}
    require(request == expected, "Exact formal wire/domain/functions/schema required")
    return canonical(request).encode(), 272000, observation, context


def decode_response(raw, operation, observation, context, plan, input_bound):
    response = at_stage("response_json", lambda: strict_json(raw))
    def envelope():
        require(isinstance(response, dict) and response.get("model") == MODEL and
                response.get("status") == "completed" and response.get("service_tier") == "default" and
                response.get("error") is None and response.get("incomplete_details") is None and
                isinstance(response.get("id"), str) and response["id"], "Actual model/tier/completion drift")
        return response["output"]
    output = at_stage("response_envelope", envelope)
    function = None
    if operation == "npc":
        def natural_text():
            texts = []
            require(isinstance(output, list), "Natural NPC output list")
            for item in output:
                if item.get("type") == "reasoning":
                    require(isinstance(item.get("summary"), list), "Malformed NPC reasoning metadata")
                    continue
                require(item.get("type") == "message" and item.get("role") == "assistant" and
                        isinstance(item.get("content"), list), "NPC may not call tools or return foreign output")
                for part in item["content"]:
                    require(part.get("type") == "output_text" and isinstance(part.get("text"), str),
                            "NPC refused/foreign response")
                    texts.append(part["text"])
            require(texts and "\n".join(texts).strip(), "Empty natural NPC reply")
            return {"text": "\n".join(texts)}
        data = at_stage("output_content", natural_text)
    else:
        from .phase0 import tool_functions
        allowed = {f["name"] for f in tool_functions(context["mode"], observation, context["person_id"])}
        call = at_stage("output_items", lambda: one_function(output, allowed_names=allowed))
        args = at_stage("application_json", lambda: strict_json(call["arguments"]))
        def action():
            if call["name"] == "ask_colleague":
                require(isinstance(args, dict) and set(args) == {"person_id", "question"} and
                        args["person_id"] in {p["person_id"] for p in observation["task"]["people"]} and
                        isinstance(args["question"], str) and args["question"].strip() and
                        (context["person_id"] is None or args["person_id"] == context["person_id"]),
                        "Invalid public recipient/question; no silent repair")
            else:
                from .executor import parse_tool
                parse_tool(canonical({"tool": call["name"], "arguments": args}))
            return {"tool": call["name"], "arguments": args}
        data = at_stage("application_validation", action)
        function = {"call_id": call["call_id"], "name": call["name"], "arguments": call["arguments"],
                    "output_items": deepcopy(output)}
    def usage():
        incoming, outgoing = response["usage"]["input_tokens"], response["usage"]["output_tokens"]
        require(type(incoming) is int and type(outgoing) is int and 0 <= incoming <= input_bound and
                0 <= outgoing <= (1024 if operation == "npc" else 2048), "Actual usage missing/above limits")
        return {"input_tokens": incoming, "output_tokens": outgoing}
    return {"data": data, **({"native_function": function} if function else {}),
            "usage": at_stage("usage", usage), "model": response["model"], "response_id": response["id"]}
