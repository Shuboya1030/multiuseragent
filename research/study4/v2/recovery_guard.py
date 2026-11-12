"""Explicit single-request diagnostic exception; old unknown remains occupied."""
from decimal import Decimal

from .budget import BudgetBlocked
from .contracts import fingerprint, require


def prior_hold(plan):
    if plan.get("continuation") is not None:
        from .ceiling_continuation import verify_history
        return verify_history(plan["continuation"]["history"])[0]
    recovery = plan.get("diagnostic_recovery")
    if recovery is None:
        return Decimal(0)
    require(plan["budget_cap_USD"] == "50.00" and plan["max_calls"] == 1 and
            plan["episodes"] == ["diagnostic-only-no-tools"] and
            recovery["prior_run_id"] != plan["run_id"] and
            isinstance(recovery["prior_ledger_sha256"], str) and len(recovery["prior_ledger_sha256"]) == 64,
            "Recovery must bind prior evidence, same50cap and one no-tools request")
    held = Decimal(recovery["prior_unknown_held_USD"])
    require(held == Decimal(".858000") and recovery["prior_unknown_calls"] == 1 and
            recovery["prior_settled_USD"] == "0", "Never omit or release old unknown exposure")
    return held


def validate_recovery(plan, approval):
    if plan.get("continuation") is not None:
        from .ceiling_continuation import validate_continuation
        validate_continuation(plan, approval)
        return
    held = prior_hold(plan)
    if not held:
        return
    recovery = plan["diagnostic_recovery"]
    extra = approval.get("diagnostic_recovery_authorization")
    if (recovery.get("new_direct_user_source") is None or extra is None or extra.get("approved") is not True):
        raise BudgetBlocked("Single diagnostic recovery awaits explicit NEW authorization; old50 not enough")
    require(extra.get("recovery_sha256") == fingerprint(recovery) and
            extra.get("new_direct_user_source") == recovery["new_direct_user_source"],
            "Recovery exception must exactly bind old hold and new direct approval")
    if plan["mode"] != "local_test":
        from .diagnostic_dispatch import SOURCE, VERSION, verify_prior
        if plan.get("dispatcher_version") != VERSION:
            raise BudgetBlocked("Provider diagnostic recovery executor not enabled for this plan")
        require(recovery["new_direct_user_source"] == SOURCE and
                extra["new_direct_user_source"] == SOURCE and plan.get("environment_tools_allowed") is False,
                "Only current direct single-diagnostic authority; tools forbidden")
        verify_prior(recovery)


def prior_settled(plan):
    if plan.get("continuation") is not None:
        from .ceiling_continuation import verify_history
        return verify_history(plan["continuation"]["history"])[1]
    return Decimal(0)
