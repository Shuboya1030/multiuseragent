"""Extract and provisionally classify interpersonal message events from TAC traces.

Run from repository root: python research/pilot/study1/extract_help_episodes.py
The output is a screening/annotation file, not a validated gold-standard coding.
"""
from __future__ import annotations

import ast
import csv
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research" / "pilot"
OUT = PILOT / "study1"


def submitted_values(source: str, pending: dict[str, str]) -> list[str]:
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return []
    submitted: list[str] = []
    for statement in tree.body:
        if not isinstance(statement, ast.Expr) or not isinstance(statement.value, ast.Call):
            continue
        call = statement.value
        if not isinstance(call.func, ast.Name) or not call.args:
            continue
        element = str(call.args[0].value) if isinstance(call.args[0], ast.Constant) else ""
        if call.func.id == "fill" and len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
            pending[element] = call.args[1].value
        elif call.func.id in {"press", "keyboard_press"} and len(call.args) >= 2 and isinstance(call.args[1], ast.Constant) and isinstance(call.args[1].value, str):
            key = call.args[1].value
            if key.lower() == "enter":
                if element in pending:
                    submitted.append(pending[element])
                    pending.pop(element, None)
            elif re.search(r"\{Enter\}", key, re.I):
                message = re.sub(r"\{Enter\}", "", key, flags=re.I).strip()
                if message:
                    submitted.append(message)
                pending.pop(element, None)
    return submitted


def classify_message(text: str, names: set[str]) -> str:
    """Lexical candidate label; task context/manual adjudication is still needed."""
    s = text.strip()
    if not s:
        return "empty_or_unparsed"
    if re.sub(r"\s+", " ", s).strip().lower() in names:
        return "name_only_or_unclassifiable_contact"
    if len(s) <= 35 and re.fullmatch(r"[\w .'-]+", s) and not re.search(r"[?!.]", s):
        if len(s.split()) <= 3 and not re.search(r"\b(please|provide|share|tell|send|need|could|can|what|how|where|when|who)\b", s, re.I):
            return "short_reply_or_unclassifiable"
    if re.search(r"\b(available|availability|schedule|calendar|free next|what time|when can|interview next week|meeting time)\b", s, re.I):
        return "coordination_or_availability"
    if re.search(r"\b(feedback|opinion|review|rating|score|rate .*\d|how did .* perform)\b", s, re.I):
        return "feedback_or_evaluation_request"
    if re.search(r"\b(advice|recommendation|procedure|what should i|how should i|what do you suggest)\b", s, re.I) and re.search(r"\?|could you|can you|please|let me know|tell me|i need", s, re.I):
        return "advice_or_expertise_request"
    if re.search(r"\b(status|progress|update on|where are we|has .* been completed)\b", s, re.I):
        return "status_request"
    if re.search(r"\b(approve|approval|authorize|permission|process (this|the|my)|reimburse|sign off|please complete|please update|could you .* (create|change|fix|send|process))\b", s, re.I):
        return "approval_or_action_request"
    if re.search(r"\b(clarify|could you explain|what do you mean|which .* should|do you mean|is it .* or|confirm whether|is this correct|can you confirm)\b", s, re.I):
        return "clarification_or_verification"
    if re.search(r"\b(could you|can you|would you|please|what|who|where|when|how|which|share|provide|tell me|let me know|send me|do you know|i need to know|i need information|i need the requirements|i need to collect|i have a question)\b", s, re.I):
        return "information_or_input_request"
    if re.search(r"\b(thank you|thanks|perfect|okay|i can help|i'll help|i will help|i will forward|i will process|i will update|i'll wait|i will wait|i will get back|i'll get back|let me check|let me try|i understand your suggestion|i'm having trouble|i am having trouble|the sooner the better|any time in the next)\b", s, re.I):
        return "acknowledgment_or_action_commitment"
    if re.search(r"\b(password rules|password requirements|the password should be|your request cost|remaining budget|total cost|the server is safe|we have conducted|file is saved|i have created|i have all the information|i have all the info|here is|here are|just to let you know|for your information|i created|i updated|this is your|the report is|the presentation is|reminder|security inspection|the following repositories|have successfully|i have a logo)\b|\.pptx\b", s, re.I):
        return "information_or_task_result_delivery"
    if re.fullmatch(r"[A-Za-z0-9!@#$%^&*]{8,}", s) or re.search(r":\s*[A-Za-z0-9!@#$%^&*]{8,}$", s):
        return "answer_or_data_response"
    return "other_message"


def normalize_visible_text(text: str) -> str:
    text = re.sub(r"@[a-z]+_[a-z]+", " ", text, flags=re.I)
    return " ".join(re.sub(r"[^a-z0-9]+", " ", text.lower()).split())


def transcript_confirms_message(text: str, content: str) -> bool:
    """Require body text to appear after an Admin sender + timestamp marker."""
    body = normalize_visible_text(text)
    page = normalize_visible_text(content)
    if not body:
        return False
    pos = page.find(body)
    if pos < 0:
        return False
    context = page[max(0, pos - 220):pos]
    return bool(re.search(r"\badmin\b.*\b\d{1,2}\s+\d{2}\s+(?:am|pm)\b", context))


def main() -> None:
    npc = json.loads((PILOT / "tac/npc_definition.json").read_text(encoding="utf-8"))
    user_map = {
        f"{x['first_name']}_{x['last_name']}".lower(): f"{x['first_name']} {x['last_name']}"
        for x in npc
    }
    normalized_names = {x.lower().replace("_", " ") for x in user_map}
    event_rows: list[dict[str, object]] = []
    raw_count = 0
    for fp in sorted((PILOT / "traj/raw").glob("*.json.gz")):
        raw_count += 1
        model, rest = fp.name.split("__", 1)
        task = re.sub(r"^traj_|(-image)?\.json\.gz$", "", rest)
        trace = json.loads(gzip.open(fp, "rt", encoding="utf-8").read())
        pending_fills: dict[str, str] = {}
        active_recipient: str | None = None
        for idx, event in enumerate(trace):
            if event.get("observation"):
                extras = event.get("extras") or {}
                page_url = str(extras.get("url", "")) if isinstance(extras, dict) else ""
                page_content = str(event.get("content", "") or "")
                page_heading = re.findall(r"\n#\s+([a-z_\.]+)\s*\n", page_content)
                if "/rocket-search" in page_url:
                    active_recipient = None
                elif "/direct/" in page_url and page_heading:
                    slug = page_heading[0].strip().lower()
                    active_recipient = user_map.get(slug, slug.replace("_", " "))
                elif page_url and not re.search(r"/(direct|channel|group)/", page_url):
                    active_recipient = None
            if event.get("action") != "browse_interactive":
                continue
            args = event.get("args") or {}
            browser_actions = str(args.get("browser_actions", ""))
            values = submitted_values(browser_actions, pending_fills)
            if not values:
                continue
            # Resolve the recipient from the page observation caused by this
            # action. This avoids carrying a stale DM recipient through a
            # directory search or navigation action.
            next_event = trace[idx + 1] if idx + 1 < len(trace) else {}
            next_message = str(next_event.get("message", ""))
            next_content = str(next_event.get("content", "") or "")
            next_extras = next_event.get("extras") or {}
            next_url = str(next_extras.get("url", "")) if isinstance(next_extras, dict) else ""
            if not next_url:
                url_match = re.search(r"Visited (https?://\S+)", next_message)
                next_url = url_match.group(1) if url_match else ""
            if not re.search(r"/(direct|channel|group)/", next_url):
                continue
            if "/rocket-search" in next_url:
                continue
            next_heading = re.findall(r"\n#\s+([a-z_\.]+)\s*\n", next_content)
            if "/direct/" in next_url and next_heading:
                slug = next_heading[0].strip().lower()
                recipient = user_map.get(slug, slug.replace("_", " "))
            elif "/direct/" in next_url:
                recipient = active_recipient or "unresolved_direct_message_recipient"
            message = values[-1].strip()
            if not message:
                continue
            visible = transcript_confirms_message(message, next_content)
            if "/direct/" not in next_url:
                mentions = [user_map.get(slug.lower(), slug.replace("_", " ")) for slug in re.findall(r"@([a-z]+_[a-z]+)", message, re.I)]
                route = re.search(r"/(channel|group)/([^/?#]+)", next_url)
                room = (route.group(1) + ":" + route.group(2)) if route else "group:unknown"
                recipient = "; ".join(dict.fromkeys(mentions)) if mentions else room
            thought = re.sub(r"```(?:tool_code)?", "", str(args.get("thought", ""))).strip()
            event_rows.append({
                "source": "TheAgentCompany",
                "model": model.replace("20241217_OpenHands-0.14.2-", ""),
                "task": task,
                "trace_event_index": idx,
                "recipient": recipient,
                "message_text": message,
                "transcript_confirmed_message": visible,
                "agent_stated_rationale": thought,
                "provisional_message_function": classify_message(message, normalized_names),
                "coding_status": "single-analyst lexical screening; needs contextual review",
                "recipient_correctness": "unverified; scenario roster is not recipient ground truth",
            })

    # Join task policy labels as context only, not as an evaluation of message correctness.
    policy_path = OUT / "task_policy_codebook.csv"
    policies = {r["task"]: r["contact_policy_class"] for r in csv.DictReader(policy_path.open(encoding="utf-8-sig"))}
    for row in event_rows:
        row["task_contact_policy_context"] = policies.get(str(row["task"]), "unavailable")

    out_csv = OUT / "tac_contact_events_screening_v1.csv"
    fields = list(event_rows[0]) if event_rows else []
    with out_csv.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(event_rows)

    confirmed_rows = [r for r in event_rows if r["transcript_confirmed_message"]]
    counts = Counter(str(r["provisional_message_function"]) for r in confirmed_rows)
    by_model: dict[str, Counter[str]] = defaultdict(Counter)
    for row in confirmed_rows:
        by_model[str(row["model"])][str(row["provisional_message_function"])] += 1
    model_counts = Counter(str(r["model"]) for r in confirmed_rows)
    full_panel_models = {
        str(r["model"])
        for r in json.loads((OUT / "episode_level.json").read_text(encoding="utf-8"))
    }
    model_function_path = OUT / "tac_message_function_by_model_v1.csv"
    with model_function_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["model", "function_candidate", "event_count", "share_within_model_confirmed_messages"])
        writer.writeheader()
        for model in sorted(full_panel_models):
            denom = model_counts.get(model, 0)
            for label in sorted(counts):
                n = by_model[model].get(label, 0)
                writer.writerow({
                    "model": model,
                    "function_candidate": label,
                    "event_count": n,
                    "share_within_model_confirmed_messages": f"{n / denom:.6f}" if denom else "",
                })
    summary = [
        "# TAC help-seeking/contact event screening (v1)",
        "",
        "This is a **single-analyst, rule-assisted screening**, not validated semantic annotation. It extracts Enter-submitted Rocket.Chat text from archived browser trajectories when the resulting page is a direct, channel, or group chat. It includes task-directed communication (e.g., data collection, feedback requests, status updates) and therefore does not equate every contact with agent help-seeking.",
        "",
        f"- Raw trajectories present: {raw_count}.",
        f"- Enter-submitted chat-text candidates: {len(event_rows)}.",
        f"- Candidates confirmed as a posted Admin message (body follows the sender/timestamp marker) in the immediately following rendered transcript: {len(confirmed_rows)}; {len(event_rows) - len(confirmed_rows)} are unconfirmed and excluded from function counts.",
        f"- Model configurations with at least one extracted outgoing message: {len(by_model)} of {len(full_panel_models)} in the complete panel.",
        "- DM recipients are parsed from the resulting direct-message page; channel/group mentions are extracted from the submitted text. Recipient appropriateness is unverified.",
        "- Purpose labels are lexical candidates. The CSV retains confirmed and unconfirmed submissions; the function-count table below includes only message bodies located after the transcript's Admin sender/timestamp marker.",
        "",
        "## Provisional message-function counts",
        "",
        "| Function candidate | Events |",
        "|---|---:|",
    ]
    summary.extend(f"| `{label}` | {n} |" for label, n in sorted(counts.items()))
    summary += ["", "## Events by model configuration", "", "| Model configuration | Confirmed messages | Share of all confirmed messages |", "|---|---:|---:|"]
    all_models = sorted(full_panel_models)
    total_confirmed = len(confirmed_rows)
    summary.extend(f"| `{model}` | {model_counts.get(model, 0)} | {model_counts.get(model, 0) / total_confirmed:.1%} |" for model in all_models)
    summary += ["", "Function counts and within-model shares are in `tac_message_function_by_model_v1.csv`. These are descriptive event distributions, not model-level help-seeking rates: task exposure, run behavior, and repeated messages differ, and labels remain provisional."]
    summary += ["", "## Interpretation boundary", "", "The labels separate observable message functions (e.g., asking for missing information, requesting feedback, coordinating availability, requesting action, delivering information, short reply/UI ambiguity). They do **not** establish the trigger for asking, whether the agent could have found the answer elsewhere, whether it should have asked, whether the recipient was appropriate, or whether a reply was used. Those require task- and episode-context review. Do not treat these screening counts as Study 1 findings.", "", "## Next coding pass", "", "1. Review all extracted messages in context and distinguish genuine human-directed messages from search/navigation artifacts.", "2. Assign task-level trigger and contact policy using task prompt, scenario facts, and evaluator evidence.", "3. Code response received, response usefulness, and uptake only where trajectory evidence supports it.", "4. Compare model configurations on task-matched rates after restricting to validated opportunities; do not infer causal effects.", ""]
    (OUT / "tac_contact_event_screening_v1.md").write_text("\n".join(summary), encoding="utf-8")
    print(json.dumps({"raw_trajectories": raw_count, "submitted_candidates": len(event_rows), "transcript_confirmed": len(confirmed_rows), "models_with_confirmed_messages": len(by_model), "functions_confirmed": counts}, indent=2))


if __name__ == "__main__":
    main()
