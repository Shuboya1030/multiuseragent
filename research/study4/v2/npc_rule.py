"""Deterministic release rules for small local proof fixtures, not LLM simulation."""
from copy import deepcopy
import re
import unicodedata

from .contracts import canonical, require


def normalized(value):
    return " ".join(unicodedata.normalize("NFKC", str(value)).casefold().split())


def contains_value(text, expected):
    value = normalized(expected)
    if type(expected) in (int, float):
        numeric_text = re.sub(r"\bUSD(?=\d)", "", text, flags=re.I)
        numbers = re.findall(r"(?<![\w.])-?\d[\d,]*(?:\.\d+)?(?![\w.])", numeric_text)
        return any(abs(float(n.replace(",", "")) - expected) <= 1e-6 for n in numbers)
    return re.search(r"(?<!\w)" + re.escape(value) + r"(?!\w)", normalized(text)) is not None


def has_authority(person, node):
    if node.authority_scope is None:
        return True
    for rule in person.authority:
        match = re.fullmatch(re.escape(node.authority_scope) + r"<=([0-9]+(?:\.[0-9]+)?)", rule)
        if match and float(match[1]) >= node.authority_amount:
            return True
    return False


def contains_intent(text, intent):
    value, prefix = normalized(text), normalized(intent)
    return value == prefix or (value.startswith(prefix) and value[len(prefix):len(prefix) + 1] in {".", ";", ":"})


def contains_field(text, key, expected):
    pattern = r'(?<!\w)"?' + re.escape(normalized(key)) + r'"?\s*[:=]\s*'
    for match in re.finditer(pattern, normalized(text)):
        suffix = normalized(text)[match.end():]
        if type(expected) in (int, float):
            number = re.match(r"(?:usd\s*|\$\s*)?(-?\d[\d,]*(?:\.\d+)?)(?![\w.])", suffix)
            if number and abs(float(number[1].replace(",", "")) - expected) <= 1e-6:
                return True
        else:
            token = re.escape(normalized(expected))
            if re.match(r'"?' + token + r'"?(?!\w)', suffix):
                return True
    return False


class RuleNPC:
    def __init__(self, fixture):
        self.fixture = fixture
        self.released = set()
        self.receipts = []

    def reply(self, person_id, question, request_id):
        require(person_id in {p.person_id for p in self.fixture.task.people}, "Unknown NPC")
        require(isinstance(question, str) and question.strip(), "Question required")
        before = set(self.released)
        facts, emitted, reasons = {}, [], []
        for node in self.fixture.nodes:
            if person_id not in node.recipients:
                continue
            if not contains_intent(question, node.intent):
                continue
            if node.authority_scope is not None:
                person = next(p for p in self.fixture.task.people if p.person_id == person_id)
                if not has_authority(person, node):
                    reasons.append("Outside this colleague's public authority scope")
                    continue
            missing_nodes = set(node.requires) - before
            missing_fields = [key for key, value in node.required_context
                              if not contains_field(question, key, value)]
            if missing_nodes or missing_fields:
                reasons.append("Prerequisite reply needed" if missing_nodes
                               else "Include obtained fields: " + ", ".join(missing_fields))
                continue
            require(not set(facts) & {k for k, _ in node.facts}, "Ambiguous simultaneous fact release")
            facts.update(node.facts)
            emitted.append(node.node_id)
        self.released.update(emitted)
        self.receipts.append({"request_id": request_id, "person_id": person_id,
                              "released_node_ids": emitted, "previously_released_node_ids": sorted(before)})
        return canonical({
            "status": "released" if emitted else "refused",
            "facts": facts,
            "reason": "; ".join(reasons) if reasons else
                      ("Requested record released." if emitted else
                       "No matching releasable record for this public intent."),
        })

    def snapshot(self):
        return {"released": sorted(self.released), "receipts": deepcopy(self.receipts)}

    def restore(self, state):
        require(set(state) == {"released", "receipts"}
                and set(state["released"]) <= {n.node_id for n in self.fixture.nodes},
                "Invalid private NPC snapshot")
        self.released = set(state["released"])
        self.receipts = deepcopy(state["receipts"])
