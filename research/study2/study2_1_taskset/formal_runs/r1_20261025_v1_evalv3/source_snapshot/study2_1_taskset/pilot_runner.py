#!/usr/bin/env python3
"""Small, auditable R1 smoke pilot for the Study 2.1 task packages.

Uses the configured OpenAI API key from the process environment. It does not
write credentials. NPC replies are rule-based from each task's scenario file.
This runner is for pilot feasibility only; it is not the confirmatory runtime.
"""
import argparse
import json
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
MODEL = "gpt-5-nano"
MAX_TURNS = 8
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


def call_model(messages, api_key):
    body = json.dumps({
        "model": MODEL,
        "reasoning_effort": "minimal",
        "max_completion_tokens": 1600,
        "tools": TOOLS,
        "tool_choice": "auto",
        "messages": messages,
    }).encode("utf-8")
    req = urllib.request.Request(
        "https://api.openai.com/v1/chat/completions",
        data=body,
        headers={"Authorization": "Bearer " + api_key, "Content-Type": "application/json"},
        method="POST",
    )
    last_error = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=90) as response:
                data = json.load(response)
            choice = data["choices"][0]
            return choice["message"], data.get("usage", {}), data.get("model", MODEL), choice.get("finish_reason")
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:1200]
            raise RuntimeError(f"OpenAI HTTP {exc.code}: {detail}") from None
        except Exception as exc:  # Preserve retries in the run record, not secret-bearing request data.
            last_error = exc
            if attempt < 2:
                time.sleep(2 ** attempt)
    raise RuntimeError(f"OpenAI request failed: {type(last_error).__name__}: {last_error}")


def parse_action(message):
    calls = message.get("tool_calls") or []
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
        "For a colleague contact, call send_message with a visible candidate ID and a purpose. Then call read_messages for "
        "that candidate and use the returned reply. When finished, call submit_answer with the task's requested deliverable "
        "as its answer object. Never claim an unreceived fact or approval. Do not include hidden reasoning."
    )
    user = "TASK\n" + task_text + "\n\nVISIBLE CANDIDATE DIRECTORY\n" + json.dumps(profiles, ensure_ascii=False, indent=2)
    return system, [{"role": "user", "content": user}]


def run_episode(task_id, alignment, seed, out_dir, api_key):
    start_time = datetime.now(timezone.utc).isoformat()
    task_dir = TASKS / task_id
    meta = read_json(task_dir / "metadata.json")
    gold = read_json(task_dir / "gold_policy.json")
    scenarios = read_json(task_dir / "scenarios.json")
    help_class = meta["help_need_class"]
    run_id = f"pilot-gpt5nano-{task_id}-{alignment}-{seed}"
    episode_dir = out_dir / "episodes" / run_id
    episode_dir.mkdir(parents=True, exist_ok=True)
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
    inbox = {}
    got_fact = False
    events = []
    usage_total = {"prompt_tokens": 0, "completion_tokens": 0}
    model_turns = []
    submitted = None
    status = "max_turns"
    errors = []

    for turn in range(MAX_TURNS):
        assistant_message, usage, returned_model, finish_reason = call_model(messages, api_key)
        model_turns.append({"turn": turn, "assistant_message": assistant_message, "finish_reason": finish_reason, "usage": usage, "model": returned_model})
        usage_total["prompt_tokens"] += int(usage.get("prompt_tokens", 0) or 0)
        usage_total["completion_tokens"] += int(usage.get("completion_tokens", 0) or 0)
        messages.append(assistant_message)
        try:
            action = parse_action(assistant_message)
        except Exception as exc:
            errors.append({"turn": turn, "type": "parse_error", "detail": str(exc), "assistant_message": assistant_message})
            status = "model_output_truncated" if finish_reason == "length" else "model_turn_invalid"
            break

        action_type = action["action"]
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
        status = "no_submission"
    answer_path = episode_dir / "answer.json"
    trace_path = episode_dir / "trace_events.jsonl"
    write_json(answer_path, submitted)
    trace_path.write_text("".join(json.dumps(e, ensure_ascii=False) + "\n" for e in events), encoding="utf-8")
    (episode_dir / "model_turns.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in model_turns), encoding="utf-8")
    eval_cmd = [sys.executable, str(HERE / "evaluate_episode.py"), "--task-dir", str(task_dir),
                "--answer", str(answer_path), "--trace", str(trace_path), "--run-id", run_id,
                "--mapping", str(episode_dir / "identity_mapping.json")]
    if variant:
        eval_cmd.extend(["--variant", variant])
    evaluated = subprocess.run(eval_cmd, check=True, capture_output=True, text=True)
    evaluation = json.loads(evaluated.stdout)
    write_json(episode_dir / "evaluation.json", evaluation)
    record = {
        "run_id": run_id, "task_id": task_id, "template_id": meta["template_id"],
        "help_need_class": help_class, "alignment": alignment, "model_provider": "OpenAI",
        "model_requested": MODEL, "model_returned": returned_model, "profile_condition": "R1",
        "seed": seed, "status": status, "agent_tokens": usage_total,
        "ask_count": sum(e["actor"] == "agent" and e["event_type"] == "ask" for e in events),
        "errors": errors, "evaluator": evaluation,
        "started_at": start_time, "ended_at": datetime.now(timezone.utc).isoformat(),
    }
    write_json(episode_dir / "run_record.json", record)
    return record


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=HERE / "pilot_runs" / "gpt5nano_r1_tools_v1_20261024")
    parser.add_argument("--seed", type=int, default=20261024)
    parser.add_argument("--limit", type=int, help="Run only the first N episodes.")
    parser.add_argument("--start-index", type=int, default=0, help="Zero-based start offset into the fixed pilot sample.")
    args = parser.parse_args()
    api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not available to this process; key value is never written to files.")

    # Stratified feasibility sample: three must-ask templates with both alignment variants,
    # plus three optional and three no-help templates. One seed and R1 only.
    jobs = [
        ("must-vendor-onboarding", "aligned"), ("must-vendor-onboarding", "separated"),
        ("must-service-incident-notice", "aligned"), ("must-service-incident-notice", "separated"),
        ("must-record-correction", "aligned"), ("must-record-correction", "separated"),
        ("optional-vendor-risk-memo", "aligned"), ("optional-accessible-training-packet", "aligned"),
        ("optional-field-maintenance-plan", "aligned"),
        ("nohelp-webinar-agenda", "aligned"), ("nohelp-expense-total", "aligned"),
        ("nohelp-access-review-matrix", "aligned"),
    ]
    jobs = jobs[args.start_index:]
    if args.limit:
        jobs = jobs[:args.limit]
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "pilot_design.json", {
        "purpose": "runtime/evaluator/feasibility pilot; not confirmatory",
        "model": MODEL, "profile_condition": "R1", "seed": args.seed,
        "selection": "3 must-ask templates x aligned/separated, 3 optional, 3 no-help; one episode each",
        "taskset_root": str(TASKS), "episodes_planned": len(jobs),
        "limitations": ["this pilot runs R1 only; the current renderer also supports paired R0 (synthetic name + generic job title), while R2 is outside the current Study 2.1 contrast",
                        "candidate runtime is a local rule-NPC pilot, not full AgentCompany",
                        "pilot templates were AI-authored/adapted and remain development drafts"],
    })
    records = []
    for index, (task_id, alignment) in enumerate(jobs, start=1):
        print(f"[{index}/{len(jobs)}] {task_id} ({alignment})", flush=True)
        rec = run_episode(task_id, alignment, args.seed + index, args.output, api_key)
        records.append(rec)
        with (args.output / "runs.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
            stream.write(json.dumps(rec, ensure_ascii=False) + "\n")
        ev = rec["evaluator"]
        print(f"  status={rec['status']} asks={rec['ask_count']} success={ev.get('task_success')} score={ev.get('checkpoint_score')}", flush=True)
    summary = {
        "episodes": len(records), "completed_submissions": sum(r["status"] == "submitted" for r in records),
        "task_successes": sum(r["evaluator"].get("task_success") is True for r in records),
        "by_class": {}, "prompt_tokens": sum(r["agent_tokens"]["prompt_tokens"] for r in records),
        "completion_tokens": sum(r["agent_tokens"]["completion_tokens"] for r in records),
        "api_errors_or_parse_errors": sum(len(r["errors"]) for r in records),
    }
    for klass in sorted({r["help_need_class"] for r in records}):
        rows = [r for r in records if r["help_need_class"] == klass]
        summary["by_class"][klass] = {
            "episodes": len(rows), "task_successes": sum(r["evaluator"].get("task_success") is True for r in rows),
            "mean_asks": sum(r["ask_count"] for r in rows) / len(rows),
            "mean_checkpoint_score": sum(r["evaluator"].get("checkpoint_score", 0) for r in rows) / len(rows),
        }
    write_json(args.output / "pilot_summary.json", summary)
    print("PILOT SUMMARY " + json.dumps(summary, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
