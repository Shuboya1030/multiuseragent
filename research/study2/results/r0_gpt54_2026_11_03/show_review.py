"""Print bounded unreviewed packets in full content, not prior judgments."""
import argparse
import json
from pathlib import Path

root = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument("--offset", type=int, default=0)
parser.add_argument("--limit", type=int, default=3)
args = parser.parse_args()
load = lambda p: json.loads(p.read_text(encoding="utf-8-sig"))
reviewed = load(root / "review_decisions.json")
index = [r for r in load(root / "review_inputs/index.json") if r["task_id"] not in reviewed]
for row in index[args.offset:args.offset + args.limit]:
    c = load(root / row["packet"])
    print("\nTASK", c["task_id"], "\nPUBLIC", c["task"]["prompt"])
    print("GOLD", c["task"]["full_information_reference"])
    print("BASE", c["task"]["no_contact_reference"])
    print("ARTIFACT", c["workspace"])
    for a in c["all_assistant_text"]:
        print("ASSISTANT", a["text"])
    for p in c["public_posts"]:
        print("POST", p["arguments"], "ERROR", p["is_error"])
    admissible = sorted({p for n in c["task"]["gold_dag"]["nodes"] for p in n["admissible_recipients"]})
    print("ADMISSIBLE", admissible, "C", c["C_from_delivered_contacts"])
    for e in c["contact_events"]:
        print(e["message_id"], e["actor"], e["colleague"], ":", e["content"])
    print("READ_CONTACTS", [p["arguments"] for p in c["read_tools"]])
    print("STATUS", c["status"])
