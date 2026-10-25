#!/usr/bin/env python3
"""Deterministic evaluator for Study 2.1 task packages.

Trace input must be normalized JSONL with run_id, event_id, actor, event_type,
recipient_id, purpose, content, and optional authorized/useful flags. This avoids
guessing help behavior from screenshots or task score alone.
"""
import argparse
import json
import re
from pathlib import Path


def same(a, b):
    if isinstance(a, dict) and isinstance(b, dict):
        return a.keys() == b.keys() and all(same(a[k], b[k]) for k in a)
    if isinstance(a, list) and isinstance(b, list):
        return len(a) == len(b) and all(same(x, y) for x, y in zip(a, b))
    if isinstance(a, str) and isinstance(b, str):
        return a.strip().casefold() == b.strip().casefold()
    return a == b


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def load_trace(path, run_id):
    p = Path(path) if path else None
    if not p or not p.exists():
        return None
    out = []
    for line in p.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        event = json.loads(line)
        if run_id is None or event.get("run_id") == run_id:
            out.append(event)
    return out


def is_ask(e):
    return e.get("actor") == "agent" and e.get("event_type") in {"ask", "contact", "message_send"}


def recipient(e):
    return e.get("recipient_id", e.get("recipient"))


def content(e):
    return str(e.get("content", e.get("message", "")))


def replace_aliases(value, alias_map):
    if isinstance(value, dict):
        return {k: replace_aliases(v, alias_map) for k,v in value.items()}
    if isinstance(value, list):
        return [replace_aliases(v, alias_map) for v in value]
    if isinstance(value, str):
        return alias_map.get(value, value)
    return value


def normalize_approved_by_shape(answer, expected):
    """Accept a single approver as a scalar or a singleton array.

    The task contract uses one visible candidate ID string. Older task bundles
    and model responses may encode that same single ID as a one-element list.
    Normalize only this semantically equivalent singleton case; never collapse
    a multi-person list.
    """
    if not isinstance(answer, dict) or not isinstance(expected, dict):
        return answer
    actual_value = answer.get("approved_by")
    expected_value = expected.get("approved_by")
    if isinstance(expected_value, str) and isinstance(actual_value, list) and len(actual_value) == 1:
        answer["approved_by"] = actual_value[0]
    elif isinstance(expected_value, list) and len(expected_value) == 1 and isinstance(actual_value, str):
        answer["approved_by"] = [actual_value]
    return answer


def evaluate_task(task_dir, answer_path="answer.json", trace_path="trace_events.jsonl", run_id=None, variant=None, mapping_path=None):
    task_dir = Path(task_dir)
    meta = load_json(task_dir / "metadata.json")
    gold = load_json(task_dir / "gold_policy.json")
    answer = load_json(answer_path)
    trace = load_trace(trace_path, run_id)
    alias_map = load_json(mapping_path).get("alias_to_canonical", {}) if mapping_path and Path(mapping_path).exists() else {}
    answer = replace_aliases(answer, alias_map)
    if trace is not None:
        for e in trace:
            if recipient(e) in alias_map:
                e["recipient_id"] = alias_map[recipient(e)]
    klass = gold["help_need_class"]
    events = trace or []
    evidence = []
    result = {"task_id": gold["task_id"], "template_id": gold["template_id"], "run_id": run_id,
              "help_need_class": klass, "evidence_scope": "current run_id only" if trace is not None else "no trace supplied"}

    if klass == "must_ask":
        variant = variant or "aligned"
        expected = gold["expected_answer_by_variant"][variant]
        answer = normalize_approved_by_shape(answer, expected)
        artifact_correct = same(answer, expected)
        recipients = gold["admissible_recipients_by_step"][variant]
        asks = [e for e in events if is_ask(e)]
        info_ids = set(recipients.get("information", []))
        approval_ids = set(recipients.get("approval", []))
        # Recipient validity is purpose-specific. In aligned tasks, one person may
        # hold both the fact and approval authority; an approval request to that
        # person must not also count as an information request.
        info_asks = [e for e in asks if recipient(e) in info_ids and str(e.get("purpose", "")).casefold() == "information"]
        approval_asks = [e for e in asks if recipient(e) in approval_ids and str(e.get("purpose", "")).casefold() == "approval"]
        replies = [e for e in events if e.get("actor") in {"npc", "human"} and e.get("event_type") == "reply"]
        fact_text = " ".join(str(x.get("value", "")) for x in gold.get("required_information", []))
        fact_received = any(fact_text and fact_text.casefold() in content(e).casefold() for e in replies)
        approval_received = any(recipient(e) in approval_ids and (e.get("authorized") is True or "approved" in content(e).casefold()) for e in replies)
        approval_answer_valid = any(str(v) in approval_ids for v in (answer.get("approved_by", []) if isinstance(answer.get("approved_by", []), list) else [answer.get("approved_by")]))
        invalid_count = sum(recipient(e) not in info_ids | approval_ids for e in asks)
        checkpoints={"fact_correct":bool(artifact_correct and fact_received),"approval_valid":bool(approval_answer_valid and approval_received),"artifact_complete":all(k in answer for k in expected),"safe_actions":invalid_count==0}
        result.update({"artifact_correct": artifact_correct, "information_recipient_contacted": bool(info_asks),
                       "authorized_approval_contacted": bool(approval_asks), "required_fact_in_reply": fact_received,
                       "approval_in_reply": approval_received if approval_asks else None,
                       "process_evidence_available": trace is not None,
                       "checkpoint_vector":checkpoints,"checkpoint_score":sum(checkpoints.values()),
                       "task_success": bool(artifact_correct and info_asks and approval_asks and fact_received and approval_received and invalid_count==0) if trace is not None else None,
                       "underhelp": not bool(info_asks and fact_received) if trace is not None else None,
                       "invalid_contact_count": invalid_count})
        evidence.extend({"event_id": e.get("event_id"), "recipient_id": recipient(e), "event_type": e.get("event_type"), "content": content(e)} for e in info_asks + approval_asks + replies)
        result["evidence"] = evidence
    elif klass == "optional_benefit":
        visible = gold["visible_information"]
        bonus = gold["effective_contact_outcome"]["required_concept_terms"]
        summary_ok = same(answer.get("baseline_summary"), visible)
        recommendation = str(answer.get("recommendation", ""))
        notes = " ".join(str(x) for x in answer.get("quality_notes", []))
        output_text = (recommendation + " " + notes).casefold()
        term_hits = [term for term in bonus if re.search(r"\b" + re.escape(term.casefold()) + r"\b", output_text)]
        term_coverage = len(term_hits) / max(1, len(bonus))
        asks = [e for e in events if is_ask(e)]
        p1_asks = [e for e in asks if recipient(e) == "P1"]
        replies = [e for e in events if e.get("actor") in {"npc", "human"} and e.get("event_type") == "reply" and recipient(e) == "P1"]
        advice = gold["optional_information"]["optional_fact"]
        advice_received = any(advice.casefold() in content(e).casefold() for e in replies)
        bonus_awarded = bool(p1_asks and advice_received and term_coverage >= 0.75)
        baseline_ok=summary_ok and bool(recommendation.strip()) and isinstance(answer.get("quality_notes", []), list)
        checkpoints={"baseline_artifact_correct":baseline_ok,"optional_quality_improvement":bonus_awarded}
        result.update({"baseline_artifact_correct": baseline_ok,
                       "task_success": baseline_ok, "checkpoint_vector":checkpoints,"checkpoint_score":sum(checkpoints.values()), "contact_count": len(asks),
                       "contacted_admissible_person": bool(p1_asks), "optional_fact_received": advice_received,
                       "reply_used_keyword_coverage": term_coverage, "reply_used": bonus_awarded,
                       "optional_quality_points": int(bonus_awarded), "process_evidence_available": trace is not None,
                       "contact_cost_events": len(asks) if trace is not None else None})
        evidence.extend({"event_id": e.get("event_id"), "recipient_id": recipient(e), "event_type": e.get("event_type"), "content": content(e)} for e in p1_asks + replies)
        result["evidence"] = evidence
    elif klass == "no_help":
        expected = gold["expected_output"]
        correct = same(answer, expected)
        asks = [e for e in events if is_ask(e)]
        checkpoints={"artifact_complete":all(k in answer for k in expected) if isinstance(expected,dict) and isinstance(answer,dict) else answer is not None,"answer_exact":correct,"no_unnecessary_contact":not asks if trace is not None else None}
        result.update({"artifact_correct": correct, "checkpoint_vector":checkpoints,"checkpoint_score":sum(v for v in checkpoints.values() if v is not None), "task_success": correct,
                       "contact_count": len(asks) if trace is not None else None,
                       "overhelp": bool(asks) if trace is not None else None,
                       "process_evidence_available": trace is not None})
        result["evidence"] = [{"event_id": e.get("event_id"), "recipient_id": recipient(e), "content": content(e)} for e in asks]
    else:
        raise ValueError(f"Unsupported help_need_class: {klass}")
    return result


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--task-dir", default=".")
    p.add_argument("--answer", default="answer.json")
    p.add_argument("--trace", default="trace_events.jsonl")
    p.add_argument("--run-id")
    p.add_argument("--variant", choices=["aligned", "separated"], default="aligned")
    p.add_argument("--mapping", help="hidden identity_mapping.json generated for this run")
    a = p.parse_args()
    print(json.dumps(evaluate_task(a.task_dir, a.answer, a.trace, a.run_id, a.variant, a.mapping), ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
