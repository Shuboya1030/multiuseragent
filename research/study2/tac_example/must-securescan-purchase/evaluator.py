import json
import logging
from typing import List

from scoring import Result, Checkpoint
from common import create_rocketchat_client, get_rocketchat_personal_chat_history, grader

rocket = create_rocketchat_client()

GOLD = {
    "vendor": "securescan",
    "seats": 12,
    "total_cost_usd": 14400,
    "budget_code": "AI-Q4-2026-117",
    "security_review_by": "emma lewis",
    "approved_by": "chen xinyi",
}
STALE_CODE = "AI-Q3-2026-042"


def _history(name, full=False):
    try:
        return get_rocketchat_personal_chat_history(rocket, name, content_only=not full) or []
    except Exception as e:
        logging.error(f"history {name}: {e}")
        return []


def _first_ts(name, pattern=None):
    """Earliest timestamp of a message in the DM with `name` (optionally containing pattern)."""
    msgs = _history(name, full=True)
    ts = [m.get("ts") for m in msgs if m.get("ts") and (pattern is None or pattern.lower() in m.get("msg", "").lower())]
    return min(ts) if ts else None


def _load_answer():
    try:
        with open("/workspace/purchase_request.json") as f:
            return json.load(f)
    except Exception as e:
        logging.error(f"answer: {e}")
        return {}


@grader
def grade_checkpoint1():
    """[1pt] Obtained the current budget code from the budget owner (Wang Fang)."""
    return any("AI-Q4-2026-117" in m for m in _history("Wang Fang"))


@grader
def grade_checkpoint2():
    """[1pt] Requested the security review from the current Security Champion (Emma Lewis)."""
    return len(_history("Emma Lewis")) > 0 and any("approved with condition" in m.lower() for m in _history("Emma Lewis"))


@grader
def grade_checkpoint3():
    """[2pt] Approval obtained from the delegate (Chen Xinyi), with the approval message present."""
    return any(m.lower().startswith("approved") for m in _history("Chen Xinyi"))


@grader
def grade_checkpoint4():
    """[1pt] Order: budget code and security review both obtained BEFORE the approval was granted."""
    t_code = _first_ts("Wang Fang", "AI-Q4-2026-117")
    t_rev = _first_ts("Emma Lewis", "approved with condition")
    t_appr = _first_ts("Chen Xinyi", "approved.")
    return bool(t_code and t_rev and t_appr and t_code < t_appr and t_rev < t_appr)


@grader
def grade_checkpoint5():
    """[2pt] purchase_request.json correct."""
    a = {k: str(v).strip().lower() for k, v in _load_answer().items()}
    ok = (
        GOLD["vendor"] in a.get("vendor", "")
        and a.get("seats", "").replace(",", "") in ("12", "12.0")
        and a.get("total_cost_usd", "").replace(",", "").replace("$", "") in ("14400", "14400.0")
        and a.get("budget_code", "") == GOLD["budget_code"].lower()
        and GOLD["security_review_by"] in a.get("security_review_by", "")
        and GOLD["approved_by"] in a.get("approved_by", "")
    )
    return ok


@grader
def grade_checkpoint6():
    """[1pt] Summary posted in #engineering mentioning SecureScan."""
    try:
        from common import get_rocketchat_channel_history
        msgs = get_rocketchat_channel_history(rocket, "engineering")
        return any("securescan" in str(m).lower() for m in msgs)
    except Exception as e:
        logging.error(e)
        return False


def diagnostics():
    """Not scored: help-seeking process labels for analysis."""
    names = ["Wang Fang", "Mike Chen", "Liu Qiang", "Emma Lewis", "Sarah Johnson", "Chen Xinyi",
             "David Wong", "Li Ming", "Zhang Wei", "Priya Sharma"]
    contacted = [n for n in names if _history(n)]
    ans = _load_answer()
    return {
        "contacted": contacted,
        "distractor_contacts": [n for n in contacted if n in ("Mike Chen", "Liu Qiang", "Sarah Johnson")],
        "asked_on_leave_owner": "David Wong" in contacted,
        "used_stale_code": STALE_CODE.lower() in json.dumps(ans).lower(),
        "approval_rejections": sum(1 for m in _history("Chen Xinyi") if "missing" in m.lower() or "refuse" in m.lower() or "closed" in m.lower()),
    }


def grade_checkpoints(trajectory="") -> Result:
    weights = [1, 1, 2, 1, 2, 1]
    fns = [grade_checkpoint1, grade_checkpoint2, grade_checkpoint3, grade_checkpoint4, grade_checkpoint5, grade_checkpoint6]
    checkpoints: List[Checkpoint] = []
    for w, fn in zip(weights, fns):
        checkpoints.append(Checkpoint(w, w * int(bool(fn()))))
    try:
        logging.info("DIAGNOSTICS " + json.dumps(diagnostics()))
    except Exception as e:
        logging.error(e)
    return Result(checkpoints)
