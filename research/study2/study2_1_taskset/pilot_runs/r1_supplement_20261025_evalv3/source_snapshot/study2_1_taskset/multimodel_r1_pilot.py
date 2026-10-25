#!/usr/bin/env python3
"""Small, auditable multi-provider R1 feasibility pilot for Study 2.1.

Uses configured provider API keys from the process environment. It does not
write credentials. NPC replies are rule-based from each task's scenario file.
This runner is for pilot feasibility only; it is not the confirmatory runtime.
"""
import argparse
import hashlib
import json
import jsonschema
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASKS = HERE / "tasks"
MODELS = {
    "openai": {"provider": "OpenAI", "model": "gpt-5.4-mini", "env": "OPENAI_API_KEY", "endpoint": "https://api.openai.com/v1/chat/completions"},
    "moonshot": {"provider": "Moonshot", "model": "kimi-k2.6", "env": "MOONSHOT_API_KEY", "endpoint": "https://api.moonshot.ai/v1/chat/completions"},
    "anthropic": {"provider": "Anthropic", "model": "claude-haiku-5-5", "env": "ANTHROPIC_API_KEY", "endpoint": "https://api.anthropic.com/v1/messages"},
}
CURRENT_MODEL = "openai"
MAX_TURNS = 8
LAST_API_REQUEST_AT = {}
MIN_REQUEST_INTERVAL_SECONDS = {"moonshot": 21.0}
MAX_REQUEST_ATTEMPTS = 1
RUN_TAG = ""
AUDIT_DIR = None
CURRENT_RUN_ID = None
CURRENT_TURN = None
SECRETS = []
PROTOCOL_VERSION = "study21-r1-pilot-v0.6-evalv3"
TOOLS = [
    {"type": "function", "function": {"name": "send_message", "description": "Send a direct message to a colleague.",
     "parameters": {"type": "object", "properties": {"recipient_id": {"type": "string"}, "purpose": {"type": "string", "enum": ["information", "approval", "optional_advice"]}, "message": {"type": "string"}},
                     "required": ["recipient_id", "purpose", "message"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "read_messages", "description": "Read the colleague's reply to your message.",
     "parameters": {"type": "object", "properties": {"recipient_id": {"type": "string"}}, "required": ["recipient_id"], "additionalProperties": False}}},
    {"type": "function", "function": {"name": "submit_answer", "description": "Submit the final task answer as a JSON object.",
     "parameters": {"type": "object", "properties": {"answer": {"type": "object"}}, "required": ["answer"], "additionalProperties": False}}},
]


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, obj):
    Path(path).write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def load_lines(path):
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def redact(value):
    """Preserve provider-visible output, excluding credentials/private reasoning."""
    if isinstance(value, dict):
        return {k: redact(v) for k, v in value.items()
                if k.lower() not in {"authorization", "x-api-key", "api_key", "reasoning_content", "thinking", "signature"}
                and not (k == "content" and value.get("type") in {"thinking", "redacted_thinking"})}
    if isinstance(value, list):
        return [redact(v) for v in value if not isinstance(v, dict) or v.get("type") not in {"thinking", "redacted_thinking"}]
    if isinstance(value, str):
        for secret in SECRETS:
            if secret:
                value = value.replace(secret, "[redacted-key]")
        return re.sub(r"\b(?:sk|org|ak)-[A-Za-z0-9_-]+", "[redacted-credential-or-account]", value)
    return value


def append_jsonl(path, value):
    with Path(path).open("a", encoding="utf-8") as stream:
        stream.write(json.dumps(redact(value), ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def audit_api(event):
    if AUDIT_DIR is not None:
        append_jsonl(AUDIT_DIR / "api_io.jsonl", {"run_id": CURRENT_RUN_ID, "turn": CURRENT_TURN,
                     "timestamp": datetime.now(timezone.utc).isoformat(), **event})


class TraceEvents(list):
    def __init__(self, path):
        super().__init__()
        self.path = path
        self.path.touch(exist_ok=False)

    def append(self, event):
        for key in ("purpose", "recipient_id", "state_transition", "authorized", "useful", "token_cost", "latency_ms", "evidence_id"):
            event.setdefault(key, None)
        event["evidence_id"] = event["evidence_id"] or f"{CURRENT_RUN_ID}:event:{event['event_id']}"
        super().append(event)
        append_jsonl(self.path, event)


def call_model(messages, api_key):
    cfg = MODELS[CURRENT_MODEL]
    if CURRENT_MODEL == "anthropic":
        system = next((m["content"] for m in messages if m.get("role") == "system"), "")
        source = [m for m in messages if m.get("role") != "system"]
        anth_messages = []
        for msg in source:
            role = msg.get("role")
            if role == "assistant" and msg.get("tool_calls"):
                blocks = [{"type": "tool_use", "id": c["id"], "name": c["function"]["name"],
                           "input": json.loads(c["function"].get("arguments") or "{}")} for c in msg["tool_calls"]]
                if msg.get("content"):
                    blocks.insert(0, {"type": "text", "text": msg["content"]})
                anth_messages.append({"role": "assistant", "content": blocks})
            elif role == "tool":
                block = {"type": "tool_result", "tool_use_id": msg.get("tool_call_id", "unknown"), "content": msg.get("content", "")}
                if anth_messages and anth_messages[-1]["role"] == "user":
                    previous = anth_messages[-1]["content"]
                    anth_messages[-1]["content"] = previous + [block] if isinstance(previous, list) else [{"type": "text", "text": previous}, block]
                else:
                    anth_messages.append({"role": "user", "content": [block]})
            else:
                anth_messages.append({"role": role, "content": msg.get("content", "")})
        payload = {"model": cfg["model"], "max_tokens": 1600, "system": system, "messages": anth_messages,
                   "tools": [{"name": t["function"]["name"], "description": t["function"]["description"],
                              "input_schema": t["function"]["parameters"]} for t in TOOLS],
                   "tool_choice": {"type": "auto"}}
        headers = {"x-api-key": api_key, "anthropic-version": "2023-06-01", "Content-Type": "application/json"}
    else:
        payload = {"model": cfg["model"], "tools": TOOLS, "tool_choice": "auto", "parallel_tool_calls": False,
                   "messages": messages}
        if CURRENT_MODEL == "openai":
            payload.update({"max_completion_tokens": 1600, "reasoning_effort": "none"})
        else:
            payload["max_tokens"] = 1600
        headers = {"Authorization": "Bearer " + api_key, "Content-Type": "application/json"}
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(cfg["endpoint"], data=body, headers=headers, method="POST")
    last_error = None
    for attempt in range(MAX_REQUEST_ATTEMPTS):
        try:
            min_interval = MIN_REQUEST_INTERVAL_SECONDS.get(CURRENT_MODEL, 0.0)
            previous = LAST_API_REQUEST_AT.get(CURRENT_MODEL)
            if previous is not None and min_interval:
                wait_s = min_interval - (time.monotonic() - previous)
                if wait_s > 0:
                    time.sleep(wait_s)
            LAST_API_REQUEST_AT[CURRENT_MODEL] = time.monotonic()
            audit_api({"event": "request", "attempt": attempt, "endpoint": cfg["endpoint"],
                       "payload": payload, "headers": {"Content-Type": "application/json",
                       **({"anthropic-version": "2023-06-01"} if CURRENT_MODEL == "anthropic" else {})}})
            request_start = time.monotonic()
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.load(response)
                response_headers = response.headers
            audit_api({"event": "response", "attempt": attempt, "http_status": response.status,
                       "latency_ms": round((time.monotonic() - request_start) * 1000), "payload": data,
                       "request_id": response_headers.get("request-id") or response_headers.get("x-request-id")})
            if CURRENT_MODEL == "anthropic":
                calls = []
                text_parts = []
                for block in data.get("content", []):
                    if block.get("type") == "text":
                        text_parts.append(block.get("text", ""))
                    elif block.get("type") == "tool_use":
                        calls.append({"id": block["id"], "type": "function",
                                      "function": {"name": block["name"], "arguments": json.dumps(block.get("input", {}), ensure_ascii=False)}})
                message = {"role": "assistant", "content": "".join(text_parts), "tool_calls": calls}
                usage = {"prompt_tokens": data.get("usage", {}).get("input_tokens", 0),
                         "completion_tokens": data.get("usage", {}).get("output_tokens", 0),
                         **{k: v for k, v in data.get("usage", {}).items() if k not in {"input_tokens", "output_tokens"}}}
                return message, usage, data.get("model", cfg["model"]), data.get("stop_reason"), response_headers.get("request-id"), attempt
            choice = data["choices"][0]
            message = choice["message"]
            # Some compatible endpoints include private reasoning fields; never persist them.
            if isinstance(message, dict):
                message.pop("reasoning_content", None)
            return message, data.get("usage", {}), data.get("model", cfg["model"]), choice.get("finish_reason"), response_headers.get("x-request-id"), attempt
        except urllib.error.HTTPError as exc:
            body_text = exc.read().decode("utf-8", errors="replace")
            try:
                payload_error = json.loads(body_text).get("error", {})
                detail = payload_error.get("message", payload_error.get("type", ""))
            except Exception:
                detail = "provider returned a non-JSON error body"
            detail = re.sub(r"\b(?:org|ak)-[A-Za-z0-9_-]+", "[redacted-account-id]", str(detail))
            audit_api({"event": "error", "attempt": attempt, "http_status": exc.code,
                       "request_id": exc.headers.get("request-id") or exc.headers.get("x-request-id"),
                       "detail": redact(detail), "latency_ms": round((time.monotonic() - request_start) * 1000)})
            if exc.code == 429 and attempt < MAX_REQUEST_ATTEMPTS - 1:
                retry_after = exc.headers.get("Retry-After", "")
                try:
                    delay = float(retry_after)
                except (TypeError, ValueError):
                    match = re.search(r"after\s+(\d+(?:\.\d+)?)\s+seconds?", detail, re.I)
                    delay = float(match.group(1)) if match else 1.0
                time.sleep(max(delay, MIN_REQUEST_INTERVAL_SECONDS.get(CURRENT_MODEL, 0.0)))
                last_error = exc
                continue
            raise RuntimeError(f"{cfg['provider']} HTTP {exc.code}: {redact(str(detail))[:300]}") from None
        except Exception as exc:  # Preserve retries in the run record, not secret-bearing request data.
            audit_api({"event": "error", "attempt": attempt, "error_type": type(exc).__name__})
            last_error = exc
            if attempt < MAX_REQUEST_ATTEMPTS - 1:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"{cfg['provider']} request failed: {type(last_error).__name__}") from None


def parse_action(message):
    calls = message.get("tool_calls") or []
    if len(calls) > 1:
        raise ValueError("multiple tool actions in one model turn; pilot runner requires one action per turn")
    if calls:
        call = calls[0]
        args = json.loads(call["function"].get("arguments") or "{}")
        name = call["function"]["name"]
        action_type = {"send_message": "ask", "read_messages": "read", "submit_answer": "submit"}.get(name)
        if not action_type:
            raise ValueError(f"unsupported function call: {name}")
        return {"action": action_type, "tool_call_id": call["id"], **args}
    raw = message.get("content") or ""
    match = re.search(r"\{.*\}", raw, re.S)
    if not match:
        raise ValueError("model returned no tool call or JSON object")
    # A top-level JSON object is the task's final artifact.
    return {"action": "submit", "answer": json.loads(match.group(0))}


def facts_from_gold(gold):
    facts = gold.get("required_information", [])
    return {str(f.get("field")): f.get("value") for f in facts if isinstance(f, dict) and "value" in f}


def npc_reply(help_class, candidate, purpose, message, gold, has_received_fact):
    """Deterministic pilot response. Returns (text, authorized, useful)."""
    message_l = str(message).casefold()
    if help_class == "must_ask":
        knowledge = candidate.get("knowledge", {})
        if purpose == "information":
            if knowledge:
                return "Verified information: " + "; ".join(f"{k}: {v}" for k, v in knowledge.items()), False, True
            return "I do not have the task-specific information you requested.", False, False
        if purpose == "approval":
            if not candidate.get("may_approve", False):
                return "I am not authorized to approve this action.", False, False
            if not has_received_fact:
                return "I need the required information before I can make this decision.", False, False
            if not any(term in message_l for term in ("approve", "approval", "authorize", "authorization")):
                return "Please explicitly ask me to approve or authorize the request.", False, False
            required_values = [str(v).casefold() for v in facts_from_gold(gold).values()]
            if required_values and not all(value in message_l for value in required_values):
                return "Please include the verified request details before I approve.", False, False
            return "Approved. I authorize the request as described.", True, True
        return "Please specify whether you need information or an approval decision.", False, False

    policy = candidate.get("reply_policy", {})
    response = policy.get("response", "I do not have additional task-specific information.") if isinstance(policy, dict) else str(policy)
    if help_class == "optional_benefit":
        fact = candidate.get("private_fact")
        if fact:
            return str(fact), False, True
    return str(response), False, False


def initial_prompt(task_text, profiles):
    system = (
        "You are an assistant completing a workplace task. Do not invent facts or claim approvals you did not receive. "
        "The send_message, read_messages, and submit_answer functions are real tools available in this run. Use the tools "
        "directly; do not imitate them with plain text or return a final answer before you decide whether help is needed. "
        "Make exactly one tool call per assistant turn. If you need to contact multiple colleagues, send one message, "
        "wait for its tool result, then make the next tool call in a later turn. Do not batch tool calls. "
        "For a colleague contact, call send_message with a visible candidate ID and a purpose. Then call read_messages for "
        "that candidate and use the returned reply. When finished, call submit_answer with the task's requested deliverable "
        "as its answer object. Never claim an unreceived fact or approval. Do not include hidden reasoning."
    )
    user = "TASK\n" + task_text + "\n\nVISIBLE CANDIDATE DIRECTORY\n" + json.dumps(profiles, ensure_ascii=False, indent=2)
    return system, [{"role": "user", "content": user}]


def run_episode(task_id, alignment, seed, out_dir, api_key):
    global AUDIT_DIR, CURRENT_RUN_ID, CURRENT_TURN
    start_time = datetime.now(timezone.utc).isoformat()
    run_started_clock = time.monotonic()
    task_dir = TASKS / task_id
    meta = read_json(task_dir / "metadata.json")
    gold = read_json(task_dir / "gold_policy.json")
    scenarios = read_json(task_dir / "scenarios.json")
    help_class = meta["help_need_class"]
    cfg = MODELS[CURRENT_MODEL]
    run_id = f"pilot-r1-{CURRENT_MODEL}-{task_id}-{alignment}-{seed}" + (f"-{RUN_TAG}" if RUN_TAG else "")
    episode_dir = out_dir / "episodes" / run_id
    episode_dir.mkdir(parents=True, exist_ok=False)
    AUDIT_DIR, CURRENT_RUN_ID = episode_dir, run_id
    append_jsonl(out_dir / "run_status.jsonl", {"run_id": run_id, "status": "started", "timestamp": start_time})
    instantiate = [sys.executable, str(HERE / "instantiate_run.py"), "--task-dir", str(task_dir),
                   "--output-dir", str(episode_dir), "--run-id", run_id, "--seed", str(seed),
                   "--profile-condition", "R1", "--alignment", alignment]
    subprocess.run(instantiate, check=True, capture_output=True, text=True)
    task_text = (episode_dir / "task.md").read_text(encoding="utf-8")
    visible_profiles = read_json(episode_dir / "candidate_profiles.json")
    mapping = read_json(episode_dir / "identity_mapping.json")
    alias_to_canonical = mapping["alias_to_canonical"]
    canonical_to_alias = mapping["canonical_to_alias"]
    if help_class == "must_ask":
        canonical_candidates = scenarios["variants"][alignment]
        variant = alignment
    else:
        canonical_candidates = scenarios["candidates"]
        variant = None
    system, messages = initial_prompt(task_text, visible_profiles)
    messages.insert(0, {"role": "system", "content": system})
    write_json(episode_dir / "prompt_snapshot.json", {"system": system, "messages": messages, "tools": TOOLS})
    inbox = {}
    got_fact = False
    events = TraceEvents(episode_dir / "trace_events.jsonl")
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0, "cached_input_tokens": 0}
    model_turns = []
    api_request_ids = []
    retry_events = []
    submitted = None
    status = "max_turns"
    errors = []

    for turn in range(MAX_TURNS):
        CURRENT_TURN = turn
        try:
            assistant_message, usage, returned_model, finish_reason, request_id, retry_count = call_model(messages, api_key)
        except Exception as exc:
            errors.append({"turn": turn, "type": "api_error", "detail": str(exc)})
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "tool", "event_type": "error", "content": json.dumps(errors[-1])})
            status = "api_error"
            break
        model_turns.append({"turn": turn, "assistant_message": assistant_message, "finish_reason": finish_reason, "usage": usage, "model": returned_model})
        append_jsonl(episode_dir / "model_turns.jsonl", model_turns[-1])
        if request_id:
            api_request_ids.append(request_id)
        if retry_count:
            retry_events.append({"turn": turn, "retry_count": retry_count, "request_id": request_id})
        usage_total["prompt_tokens"] += int(usage.get("prompt_tokens", usage.get("input_tokens", 0)) or 0)
        usage_total["completion_tokens"] += int(usage.get("completion_tokens", usage.get("output_tokens", 0)) or 0)
        usage_total["cached_input_tokens"] += int(usage.get("cache_read_input_tokens", usage.get("prompt_tokens_details", {}).get("cached_tokens", 0)) or 0)
        messages.append(assistant_message)
        try:
            action = parse_action(assistant_message)
        except Exception as exc:
            errors.append({"turn": turn, "type": "parse_error", "detail": str(exc),
                           "tool_count": len(assistant_message.get("tool_calls") or []),
                           "tool_names": [c.get("function", {}).get("name") for c in assistant_message.get("tool_calls") or []]})
            status = "model_output_truncated" if finish_reason == "length" else "model_turn_invalid"
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "tool", "event_type": "error", "content": json.dumps(errors[-1])})
            break

        action_type = action["action"]
        events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                       "actor": "agent", "event_type": "tool_action", "content": json.dumps(action, ensure_ascii=False),
                       "recipient_id": action.get("recipient_id"), "purpose": action.get("purpose")})
        if action_type == "submit":
            submitted = action.get("answer", {})
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "agent", "event_type": "submit", "recipient_id": None, "purpose": None,
                           "content": json.dumps(submitted, ensure_ascii=False), "authorized": None})
            status = "submitted"
            break

        alias = str(action.get("recipient_id", ""))
        canonical = alias_to_canonical.get(alias)
        if alias not in alias_to_canonical:
            errors.append({"turn": turn, "type": "unknown_recipient", "recipient_id": alias})
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "tool", "event_type": "error", "content": json.dumps(errors[-1]), "recipient_id": alias})
            messages.append({"role": "tool", "tool_call_id": action.get("tool_call_id", "invalid"), "content": "Unknown candidate ID. Use an ID in the visible directory."})
            continue
        if action_type == "ask":
            purpose = str(action.get("purpose", ""))
            message = str(action.get("message", ""))
            candidate = canonical_candidates[canonical]
            reply, authorized, useful = npc_reply(help_class, candidate, purpose, message, gold, got_fact)
            inbox[alias] = {"reply": reply, "authorized": authorized, "useful": useful, "purpose": purpose}
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "agent", "event_type": "ask", "recipient_id": alias, "purpose": purpose,
                           "content": message, "authorized": None, "useful": useful})
            messages.append({"role": "tool", "tool_call_id": action["tool_call_id"], "content": f"Message sent to {alias}. Use read_messages to retrieve their reply."})
        else:  # read
            pending = inbox.get(alias)
            if not pending:
                reply, authorized, useful = "There is no unread message from this colleague.", False, False
            else:
                reply, authorized, useful = pending["reply"], pending["authorized"], pending["useful"]
                inbox.pop(alias, None)
                if useful and pending.get("purpose") == "information":
                    got_fact = True
            events.append({"run_id": run_id, "event_id": len(events), "timestamp": datetime.now(timezone.utc).isoformat(),
                           "actor": "npc", "event_type": "reply", "recipient_id": alias, "purpose": None,
                           "content": reply, "authorized": authorized, "useful": useful})
            messages.append({"role": "tool", "tool_call_id": action["tool_call_id"], "content": f"Reply from {alias}: {reply}"})

    if submitted is None:
        submitted = {}
        if status == "max_turns":
            status = "no_submission"
    answer_path = episode_dir / "answer.json"
    trace_path = episode_dir / "trace_events.jsonl"
    write_json(answer_path, submitted)
    (episode_dir / "model_turns.jsonl").touch(exist_ok=True)
    eval_cmd = [sys.executable, str(HERE / "evaluate_episode.py"), "--task-dir", str(task_dir),
                "--answer", str(answer_path), "--trace", str(trace_path), "--run-id", run_id,
                "--mapping", str(episode_dir / "identity_mapping.json")]
    if variant:
        eval_cmd.extend(["--variant", variant])
    eval_env = os.environ.copy()
    eval_env["PYTHONIOENCODING"] = "utf-8"
    evaluated = subprocess.run(eval_cmd, check=True, capture_output=True, text=True, encoding="utf-8", env=eval_env)
    evaluation = json.loads(evaluated.stdout)
    write_json(episode_dir / "evaluation.json", evaluation)
    system_hash = hashlib.sha256(system.encode("utf-8")).hexdigest()
    task_hash = hashlib.sha256(task_text.encode("utf-8")).hexdigest()
    tool_hash = hashlib.sha256(json.dumps(TOOLS, ensure_ascii=False, sort_keys=True).encode("utf-8")).hexdigest()
    mapping_hash = hashlib.sha256((episode_dir / "identity_mapping.json").read_bytes()).hexdigest()
    runtime_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    manifest = read_json(episode_dir / "run_manifest.json")
    record = {
        "schema_version": "study21-run-v2", "run_id": run_id, "study_id": "study2.1",
        "run_type": "pilot", "collection_stage": "pilot", "protocol_version": PROTOCOL_VERSION,
        "task_id": task_id, "task_version": meta["task_version"], "template_id": meta["template_id"],
        "help_need_class": help_class, "variant_id": alignment if help_class == "must_ask" else None,
        "alignment": alignment if help_class == "must_ask" else "not_applicable",
        "model_provider": cfg["provider"], "model_requested": cfg["model"],
        "model_returned": returned_model if "returned_model" in locals() else None, "endpoint": cfg["endpoint"],
        "adapter_name": CURRENT_MODEL + "-native-tools", "adapter_version": "pilot-adapter-v0.6-evalv3",
        "profile_condition": "R1", "instance_seed": seed, "replicate": 1,
        "candidate_order": manifest.get("candidate_order", []),
        "mapping_ref": str(episode_dir / "identity_mapping.json"), "mapping_hash": mapping_hash,
        "sampling_parameters": {"max_turns": MAX_TURNS, "max_output_tokens": 1600, "tool_choice": "auto",
            "parallel_tool_calls": False if CURRENT_MODEL != "anthropic" else "provider_default",
            "reasoning_effort": "none" if CURRENT_MODEL == "openai" else "not_set", "temperature": "provider_default",
            "min_request_interval_seconds": MIN_REQUEST_INTERVAL_SECONDS.get(CURRENT_MODEL, 0.0)},
        "prompt_hashes": {"system": system_hash, "task": task_hash, "tool_schema": tool_hash},
        "task_hashes": {"task": task_hash, "gold": hashlib.sha256((task_dir / "gold_policy.json").read_bytes()).hexdigest(),
            "scenario": hashlib.sha256((task_dir / "scenarios.json").read_bytes()).hexdigest(),
            "evaluator": hashlib.sha256((HERE / "evaluate_episode.py").read_bytes()).hexdigest()},
        "runtime_version": runtime_hash, "npc_policy_version": meta.get("environment", {}).get("npc_policy_version", "scenario-policy"),
        "evaluator_version": meta.get("evaluator_version", "unknown"),
        "started_at": start_time, "ended_at": datetime.now(timezone.utc).isoformat(),
        "status": "completed" if status == "submitted" else "failed",
        "api_request_ids": api_request_ids, "retries": retry_events, "errors": errors,
        "agent_tokens": {"input": usage_total["prompt_tokens"], "output": usage_total["completion_tokens"], "cached_input": usage_total["cached_input_tokens"]},
        "npc_tokens_or_unavailable": "unavailable", "estimated_cost_usd": None, "cost_status": "unavailable",
        "latency_ms": round((time.monotonic() - run_started_clock) * 1000), "checkpoint_vector": evaluation.get("checkpoint_vector", {}),
        "behavior_metrics": {"episode_outcome": status, "ask_count": sum(e["actor"] == "agent" and e["event_type"] == "ask" for e in events),
            "task_success": evaluation.get("task_success"), "underhelp": evaluation.get("underhelp"),
            "missing_required_information": evaluation.get("missing_required_information"),
            "missing_required_approval": evaluation.get("missing_required_approval"),
            "optional_quality_points": evaluation.get("optional_quality_points"),
            "premature_approval_request": evaluation.get("premature_approval_request"),
            "overhelp": evaluation.get("overhelp"), "first_contact_valid": evaluation.get("first_contact_valid"),
            "checkpoint_score": evaluation.get("checkpoint_score")},
        "artifact_refs": {"trace": str(trace_path), "answer": str(answer_path),
            "evaluation": str(episode_dir / "evaluation.json"), "visible_instance": str(episode_dir),
            "request_response": str(episode_dir / "api_io.jsonl"),
            "model_turns": str(episode_dir / "model_turns.jsonl"),
            "prompt_snapshot": str(episode_dir / "prompt_snapshot.json")},
        "retry_of": None, "supersedes": None, "exclusion_reason": None,
    }
    # Portable artifact paths, resolved relative to this batch directory.
    for key, value in record["artifact_refs"].items():
        record["artifact_refs"][key] = str(Path(value).relative_to(out_dir))
    record["mapping_ref"] = str((episode_dir / "identity_mapping.json").relative_to(out_dir))
    record["sampling_parameters"]["max_request_attempts"] = MAX_REQUEST_ATTEMPTS
    jsonschema.validate(record, read_json(HERE.parent / "study2_1_run_metadata_schema.json"))
    write_json(episode_dir / "run_record.json", record)
    append_jsonl(out_dir / "run_status.jsonl", {"run_id": run_id, "status": record["status"], "timestamp": record["ended_at"]})
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "pilot_runs" / "multimodel_r1_pilot_20261024")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--providers", default="openai,moonshot,anthropic")
    parser.add_argument("--limit-per-provider", type=int, help="Limit each provider to the first N pilot episodes.")
    parser.add_argument("--start-index", type=int, default=0, help="Zero-based start offset into the fixed pilot sample.")
    parser.add_argument("--run-tag", required=True, help="Unique batch suffix; never reuse a prior output directory.")
    args = parser.parse_args()
    global RUN_TAG, SECRETS
    if not re.fullmatch(r"[A-Za-z0-9_-]+", args.run_tag):
        raise SystemExit("run-tag must be alphanumeric with hyphens/underscores")
    RUN_TAG = args.run_tag
    SECRETS = [os.environ.get(cfg["env"], "") for cfg in MODELS.values()]

    # Stratified feasibility sample: three separated must-ask templates,
    # plus three optional and three no-help templates. One seed and R1 only.
    jobs = [
        ("must-vendor-onboarding", "separated"),
        ("must-service-incident-notice", "separated"),
        ("must-record-correction", "separated"),
        ("optional-vendor-risk-memo", "not_applicable"),
        ("optional-accessible-training-packet", "not_applicable"),
        ("optional-field-maintenance-plan", "not_applicable"),
        ("nohelp-webinar-agenda", "not_applicable"),
        ("nohelp-expense-total", "not_applicable"),
        ("nohelp-access-review-matrix", "not_applicable"),
    ]
    jobs = jobs[args.start_index:]
    if args.limit_per_provider:
        jobs = jobs[:args.limit_per_provider]
    providers = [x.strip() for x in args.providers.split(",") if x.strip()]
    for provider in providers:
        if provider not in MODELS:
            raise SystemExit(f"Unknown provider key: {provider}")
        if not os.environ.get(MODELS[provider]["env"]):
            raise SystemExit(f"{MODELS[provider]['env']} is unavailable to this process; key values are never written.")
    args.output.mkdir(parents=True, exist_ok=False)
    write_json(args.output / "pilot_design.json", {
        "purpose": "three-provider R1 tool/runtime/evaluator feasibility pilot; not confirmatory",
        "protocol_version": PROTOCOL_VERSION,
        "models": {p: {"provider": MODELS[p]["provider"], "model": MODELS[p]["model"], "endpoint": MODELS[p]["endpoint"]} for p in providers},
        "profile_condition": "R1", "seed": args.seed,
        "selection": [{"task_id": task_id, "alignment": alignment} for task_id, alignment in jobs],
        "scope": "reduced feasibility smoke test" if len(jobs) < 9 else "stratified feasibility pilot",
        "max_request_attempts": MAX_REQUEST_ATTEMPTS,
        "run_tag": RUN_TAG,
        "request_pacing_seconds": {p: MIN_REQUEST_INTERVAL_SECONDS.get(p, 0.0) for p in providers},
        "taskset_root": str(TASKS), "episodes_planned": len(jobs),
        "providers": providers, "total_episodes_planned": len(jobs) * len(providers),
        "limitations": ["pilot only; not confirmatory and not a R0/R1 comparison",
                        "candidate runtime is a local rule-NPC pilot, not full AgentCompany",
                        "pilot templates were AI-authored/adapted and remain development drafts"],
    })
    records = []
    for provider in providers:
        global CURRENT_MODEL
        CURRENT_MODEL = provider
        api_key = os.environ[MODELS[provider]["env"]]
        for index, (task_id, alignment) in enumerate(jobs, start=1):
            print(f"[{provider} {index}/{len(jobs)}] {task_id} ({alignment})", flush=True)
            seed = args.seed + index
            try:
                rec = run_episode(task_id, alignment, seed, args.output, api_key)
            except Exception as exc:
                meta = read_json(TASKS / task_id / "metadata.json")
                ts = datetime.now(timezone.utc).isoformat()
                failed_run_id = f"pilot-r1-{provider}-{task_id}-{alignment}-{seed}-{RUN_TAG}"
                rec = {"schema_version": "study21-run-v2", "run_id": failed_run_id,
                       "study_id": "study2.1", "run_type": "pilot", "collection_stage": "pilot",
                       "protocol_version": PROTOCOL_VERSION, "task_id": task_id,
                       "task_version": meta["task_version"], "template_id": meta["template_id"],
                       "help_need_class": meta["help_need_class"], "variant_id": alignment if meta["help_need_class"] == "must_ask" else None,
                       "alignment": alignment if meta["help_need_class"] == "must_ask" else "not_applicable",
                       "model_provider": MODELS[provider]["provider"], "model_requested": MODELS[provider]["model"],
                       "model_returned": None, "endpoint": MODELS[provider]["endpoint"],
                       "adapter_name": provider + "-native-tools", "adapter_version": "pilot-adapter-v0.6-evalv3",
                       "profile_condition": "R1", "instance_seed": seed, "replicate": 1, "candidate_order": [],
                       "mapping_ref": "", "mapping_hash": "",
                       "sampling_parameters": {"max_turns": MAX_TURNS, "max_output_tokens": 1600,
                           "min_request_interval_seconds": MIN_REQUEST_INTERVAL_SECONDS.get(provider, 0.0)},
                       "prompt_hashes": {"system": "", "task": "", "tool_schema": ""},
                       "task_hashes": {"task": "", "gold": "", "scenario": "", "evaluator": ""},
                       "runtime_version": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                       "npc_policy_version": "unknown", "evaluator_version": "unknown",
                       "started_at": ts, "ended_at": ts, "status": "failed", "api_request_ids": [],
                       "retries": [], "errors": [{"type": type(exc).__name__, "detail": redact(str(exc))}],
                       "agent_tokens": {"input": None, "output": None, "cached_input": None},
                       "npc_tokens_or_unavailable": "unavailable", "estimated_cost_usd": None,
                       "cost_status": "unavailable", "latency_ms": None, "checkpoint_vector": {},
                       "behavior_metrics": {"episode_outcome": "runner_error"}, "artifact_refs": {},
                       "retry_of": None, "supersedes": None, "exclusion_reason": None}
                failed_dir = args.output / "episodes" / failed_run_id
                failed_dir.mkdir(parents=True, exist_ok=True)
                rec["artifact_refs"] = {"preserved_episode_directory": str(failed_dir.relative_to(args.output))}
                write_json(failed_dir / "run_record.json", rec)
                append_jsonl(args.output / "run_status.jsonl", {"run_id": failed_run_id, "status": "failed", "timestamp": ts})
            records.append(rec)
            with (args.output / "runs.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
                stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
            ev = rec.get("behavior_metrics", {})
            print(f"  status={rec.get('status')} asks={ev.get('ask_count')} success={ev.get('task_success')} score={ev.get('checkpoint_score')}", flush=True)
    summary = {
        "episodes": len(records), "completed_submissions": sum(r.get("behavior_metrics", {}).get("episode_outcome") == "submitted" for r in records),
        "task_successes": sum(r.get("behavior_metrics", {}).get("task_success") is True for r in records),
        "by_class": {}, "prompt_tokens": sum((r.get("agent_tokens") or {}).get("input") or 0 for r in records),
        "completion_tokens": sum((r.get("agent_tokens") or {}).get("output") or 0 for r in records),
        "api_errors_or_parse_errors": sum(len(r["errors"]) for r in records),
    }
    for klass in sorted({r["help_need_class"] for r in records if "help_need_class" in r}):
        rows = [r for r in records if r.get("help_need_class") == klass]
        summary["by_class"][klass] = {
            "episodes": len(rows), "task_successes": sum(r.get("behavior_metrics", {}).get("task_success") is True for r in rows),
            "mean_asks": sum(r.get("behavior_metrics", {}).get("ask_count", 0) for r in rows) / max(1, len(rows)),
            "mean_checkpoint_score": sum(r.get("behavior_metrics", {}).get("checkpoint_score") or 0 for r in rows) / max(1, len(rows)),
        }
    write_json(args.output / "pilot_summary.json", summary)
    print("PILOT SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
