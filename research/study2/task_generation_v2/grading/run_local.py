"""Score one episode offline: python grading/run_local.py <task_id> <deliverable.json> <trace.json>"""
import json, pathlib, sys
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from scorer import score, costs_from_roster
R = pathlib.Path(__file__).resolve().parents[1]
tid, ans_p, tr_p = sys.argv[1:4]
bp = json.loads((R / 'templates' / tid / 'blueprint.json').read_text(encoding='utf-8'))
costs = costs_from_roster(json.loads((R / 'organization/roster.json').read_text(encoding='utf-8')))
ans = json.loads(pathlib.Path(ans_p).read_text(encoding='utf-8')) if pathlib.Path(ans_p).exists() else None
tr = json.loads(pathlib.Path(tr_p).read_text(encoding='utf-8')) if pathlib.Path(tr_p).exists() else []
print(json.dumps(score(bp, ans, tr, costs), indent=2))
