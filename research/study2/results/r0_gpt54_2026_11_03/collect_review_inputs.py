"""Index terminated new attempts for direct, offline semantic review."""
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
RUNNER = HERE / "frozen_stage" / "runner"


def load(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def lines(path):
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s] if path.exists() else []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = HERE / "review_inputs"
    destination.mkdir(exist_ok=True)
    index = []
    for slot in load(HERE / "scope.json"):
        output = RUNNER / "episodes" / slot["group"] / slot["task_id"]
        if not (output / "controller_summary.json").is_file():
            continue
        definition = HERE / "task_inputs" / "templates" / slot["task_id"]
        tools = lines(output / "tool_events.jsonl")
        trace = load(output / "trace_bundle.json") if (output / "trace_bundle.json").exists() else None
        api = lines(output / "api_io.jsonl")
        events = (trace or {}).get("events", [])
        contacts = [e for e in events if e["actor"] == "agent"]
        costs = load(definition / "tac" / "grading" / "costs.json")
        facts = load(definition / "blueprint.json")
        error = load(output / "runtime_error.json") if (output / "runtime_error.json").exists() else None
        item = {
            "group": slot["group"], "task_id": slot["task_id"], "help_class": slot["help_class"],
            "manifest": load(output / "run_manifest.json"), "task": facts,
            "public_instruction": (output / "public_instruction.md").read_text(encoding="utf-8"),
            "workspace": load(output / "workspace.json"),
            "all_assistant_text": [
                {"call_id": a["call_id"], "text": a["response"]["choices"][0]["message"]["content"]}
                for a in api if a["stage"] == "response" and a["role"] == "agent"
                and a["response"]["choices"][0]["message"].get("content")],
            "public_posts": [t for t in tools if t["tool"] == "post_message"],
            "send_tools": [t for t in tools if t["tool"] == "send_message"],
            "read_tools": [t for t in tools if t["tool"] == "read_messages"],
            "contact_events": events, "role_costs": costs, "costs_sha256": sha(
                definition / "tac" / "grading" / "costs.json"),
            "C_from_delivered_contacts": sum(costs[e["colleague"]] for e in contacts),
            "status": load(output / "status.json"), "runtime_error": error,
            "raw_evaluation": load(output / "evaluation.json") if (output / "evaluation.json").exists() else None,
            "summary": load(output / "controller_summary.json"),
            "source": str(output.relative_to(HERE)), "direct_content_review_pending": True,
            "source_hashes": {str(p.relative_to(output)): sha(p) for p in output.rglob("*") if p.is_file()},
        }
        name = slot["group"] + "__" + slot["task_id"]
        path = destination / (name + ".json")
        path.write_text(json.dumps(item, ensure_ascii=False, indent=2), encoding="utf-8")
        text = "\n".join([
            "# " + name,
            "GOLD " + json.dumps(facts["full_information_reference"], ensure_ascii=False),
            "BASELINE " + json.dumps(facts["no_contact_reference"], ensure_ascii=False),
            "GOLD DAG " + json.dumps(facts["gold_dag"], ensure_ascii=False),
            "WORKSPACE " + json.dumps(item["workspace"], ensure_ascii=False),
            "ALL ASSISTANT TEXT " + json.dumps(item["all_assistant_text"], ensure_ascii=False),
            "POSTS " + json.dumps(item["public_posts"], ensure_ascii=False),
            "CONTACT EVENTS " + json.dumps(events, ensure_ascii=False),
            "C " + str(item["C_from_delivered_contacts"]),
            "RAW " + json.dumps(item["raw_evaluation"], ensure_ascii=False),
            "STATUS " + json.dumps(item["status"]),
            "ERROR " + json.dumps(error, ensure_ascii=False)])
        (destination / (name + ".txt")).write_text(text, encoding="utf-8")
        index.append({"group": slot["group"], "task_id": slot["task_id"],
                      "episode_id": item["manifest"]["episode_id"],
                      "packet": str(path.relative_to(HERE)), "source": item["source"],
                      "source_hashes_count": len(item["source_hashes"]), "semantic_review": "pending"})
    (destination / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Captured {len(index)}/60 terminated episodes for direct review; no semantic decisions invented.")


if __name__ == "__main__":
    main()
