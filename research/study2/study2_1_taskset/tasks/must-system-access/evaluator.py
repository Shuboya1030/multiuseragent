#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate_episode import main
if __name__ == "__main__":
    if "--task-dir" not in sys.argv:
        sys.argv.extend(["--task-dir", str(Path(__file__).resolve().parent)])
    if "--answer" not in sys.argv:
        sys.argv.extend(["--answer", str(Path(__file__).resolve().parent / "answer.json")])
    if "--trace" not in sys.argv:
        sys.argv.extend(["--trace", str(Path(__file__).resolve().parent / "trace_events.jsonl")])
    main()
