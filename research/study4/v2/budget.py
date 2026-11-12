"""Transport-free, in-memory reservation/unknown/no-retry checks. Not a paid ledger."""
from dataclasses import dataclass
from decimal import Decimal

from .contracts import require


@dataclass(frozen=True)
class CallCaps:
    input_tokens: int = 8000
    output_tokens: int = 1024
    input_usd_per_million: str = "0.75"
    output_usd_per_million: str = "4.50"
    surcharge: str = "0.10"

    def charge(self, incoming, outgoing):
        require(type(incoming) is int and type(outgoing) is int and incoming >= 0 and outgoing >= 0,
                "Nonnegative integer token counts required")
        return ((Decimal(incoming) * Decimal(self.input_usd_per_million) +
                 Decimal(outgoing) * Decimal(self.output_usd_per_million)) / Decimal(1_000_000) *
                (Decimal(1) + Decimal(self.surcharge)))

    def __post_init__(self):
        require(type(self.input_tokens) is int and type(self.output_tokens) is int and
                self.input_tokens > 0 and self.output_tokens > 0 and
                all(Decimal(v).is_finite() and Decimal(v) >= 0 for v in
                    (self.input_usd_per_million, self.output_usd_per_million, self.surcharge)),
                "Invalid explicit pricing/token caps")


class BudgetBlocked(RuntimeError):
    pass


class LocalBudget:
    """Only injected local callbacks supported; no credentials, persistence or real API authorization."""
    LIMITS = {"control": 24, "question": 24, "ordinary": 48, "npc": 24}

    def __init__(self, usd_cap=None, max_calls=4608, total_input_cap=36_864_000,
                 total_output_cap=4_718_592, caps=None, max_episodes=48, npc_mode="rule"):
        self.cap = Decimal(str(usd_cap)) if usd_cap is not None else None
        self.caps = caps or CallCaps()
        require(self.cap is None or (self.cap.is_finite() and self.cap >= 0), "Invalid USD cap")
        require(all(type(v) is int and v >= 0 for v in (max_calls, total_input_cap, total_output_cap, max_episodes)),
                "Invalid total caps")
        require(npc_mode in {"rule", "LLM"}, "Explicit NPC cost mode required")
        self.max_calls, self.input_cap, self.output_cap = max_calls, total_input_cap, total_output_cap
        self.max_episodes, self.npc_mode = max_episodes, npc_mode
        self.rows, self.stopped = {}, False
        self.paid_authorization = False

    def _exposure(self):
        return sum((row["charged"] if row["status"] == "settled" else row["reserved"])
                   for row in self.rows.values())

    def reserve(self, request_id, episode_id, operation, input_tokens):
        if self.cap is None:
            raise BudgetBlocked("Independent budget_cap pending; no dispatch")
        if self.stopped or any(row["status"] != "settled" for row in self.rows.values()):
            raise BudgetBlocked("Pending/unknown reservation blocks further dispatch")
        require(request_id not in self.rows and request_id and episode_id, "Duplicate/missing call identity; no retry")
        require(operation in self.LIMITS, "Unknown call operation")
        require(operation != "npc" or self.npc_mode == "LLM", "Rule NPC mode forbids model NPC dispatch")
        require(type(input_tokens) is int and 0 <= input_tokens <= self.caps.input_tokens,
                "Full request token count exceeds per-call cap")
        reserved = self.caps.charge(input_tokens, self.caps.output_tokens)
        input_total = sum(r.get("input", r["estimated_input"]) for r in self.rows.values()) + input_tokens
        output_total = sum(r.get("output", self.caps.output_tokens) for r in self.rows.values()) + self.caps.output_tokens
        operation_count = sum(r["episode"] == episode_id and r["operation"] == operation for r in self.rows.values())
        episodes = {r["episode"] for r in self.rows.values()} | {episode_id}
        if (len(self.rows) >= self.max_calls or input_total > self.input_cap or output_total > self.output_cap or
                len(episodes) > self.max_episodes or operation_count >= self.LIMITS[operation] or
                self._exposure() + reserved > self.cap):
            raise BudgetBlocked("Token/call/USD hard cap reached before dispatch")
        self.rows[request_id] = {"episode": episode_id, "operation": operation, "status": "reserved",
                                 "reserved": reserved, "estimated_input": input_tokens}
        return reserved

    def settle(self, request_id, incoming, outgoing):
        row = self.rows[request_id]
        require(row["status"] == "reserved", "Cannot settle twice or release unknown")
        if (type(incoming) is not int or type(outgoing) is not int or incoming < 0 or outgoing < 0 or
                incoming > row["estimated_input"] or outgoing > self.caps.output_tokens):
            self.unknown(request_id)
            raise BudgetBlocked("Usage missing/invalid/above reservation; exposure retained, stop")
        row.update(status="settled", input=incoming, output=outgoing,
                   charged=self.caps.charge(incoming, outgoing))

    def unknown(self, request_id):
        require(self.rows[request_id]["status"] == "reserved", "Unknown must retain an open reservation")
        self.rows[request_id]["status"] = "unknown"
        self.stopped = True

    def receipt(self):
        return {"mode": "local-in-memory-NOT-paid-ledger", "paid_authorization": False,
                "budget_cap_pending": self.cap is None, "calls": len(self.rows),
                "settled": sum(r["status"] == "settled" for r in self.rows.values()),
                "unknown": sum(r["status"] == "unknown" for r in self.rows.values()),
                "usd_exposure_upper": str(self._exposure()), "stopped": self.stopped,
                "real_API_calls": 0}
