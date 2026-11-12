"""Small public/private types for the versioned local protocol."""
from dataclasses import dataclass
import hashlib
import json
import math
import math
from pathlib import PurePosixPath


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def strict_json(raw):
    def pairs(rows):
        require(len(dict(rows)) == len(rows), "Duplicate JSON object key")
        return dict(rows)
    def invalid_constant(_):
        raise ValueError("Nonfinite JSON number")
    def finite_float(value):
        parsed = float(value)
        require(math.isfinite(parsed), "Nonfinite JSON number")
        return parsed
    return json.loads(raw, object_pairs_hook=pairs, parse_constant=invalid_constant, parse_float=finite_float)


def fingerprint(value):
    return hashlib.sha256(canonical(value).encode("utf-8")).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def workspace_path(path):
    require(isinstance(path, str) and "\\" not in path, "Use a virtual workspace path")
    parsed = PurePosixPath(path)
    require(parsed.parts[:2] == ("/", "workspace") and len(parsed.parts) > 2
            and ".." not in parsed.parts, "Path outside virtual workspace")
    return str(parsed)


@dataclass(frozen=True)
class Person:
    person_id: str
    role: str
    knowledge: tuple[str, ...]
    authority: tuple[str, ...]
    cost: float

    def __post_init__(self):
        require(isinstance(self.person_id, str) and self.person_id and self.role,
                "Public person identity and role required")
        require(type(self.cost) in (float, int) and math.isfinite(self.cost) and self.cost >= 0,
                "Invalid public contact cost")


@dataclass(frozen=True)
class PublicTask:
    task_id: str
    instruction: str
    people: tuple[Person, ...]
    documents: tuple[tuple[str, str], ...]
    intents: tuple[str, ...]
    output_fields: tuple[str, ...]
    artifact_path: str = "/workspace/deliverable.json"
    channel: str = "#engineering"
    calculations: tuple[tuple[str, str, str, float], ...] = ()

    def __post_init__(self):
        require(self.task_id and self.instruction and self.people and self.intents and self.output_fields,
                "Explicit public task, intents and output contract required")
        require(len({p.person_id for p in self.people}) == len(self.people), "Duplicate public person")
        require(len(set(self.intents)) == len(self.intents) and all(self.intents), "Duplicate/empty intent")
        require(len(set(self.output_fields)) == len(self.output_fields), "Duplicate output field")
        require(len(dict(self.documents)) == len(self.documents), "Duplicate public document")
        require(all(workspace_path(p) == p and isinstance(text, str) for p, text in self.documents),
                "Invalid public document")
        workspace_path(self.artifact_path)
        require(self.artifact_path not in dict(self.documents), "Deliverable must not be a source document")
        require(all(operation == "multiply" and target and source and type(factor) in (int, float)
                    and math.isfinite(factor) for target, operation, source, factor in self.calculations),
                "Unsupported explicit public calculation")


@dataclass(frozen=True)
class Decision:
    action: str
    person_id: str | None = None
    intent: str | None = None
    include_value_ids: tuple[str, ...] = ()

    def validate(self, task, values):
        require(self.action in {"SELF", "ASK", "SUBMIT"}, "Unknown control action")
        if self.action == "ASK":
            require(self.person_id in {p.person_id for p in task.people}, "Unknown public recipient")
            require(self.intent in task.intents, "Intent must come from public task")
            require(len(set(self.include_value_ids)) == len(self.include_value_ids)
                    and set(self.include_value_ids) <= {v["value_id"] for v in values},
                    "Unknown/duplicate value ID; cannot include unread facts")
        else:
            require(self.person_id is None and self.intent is None and not self.include_value_ids,
                    "SELF/SUBMIT cannot carry a question, private step or answer")


@dataclass(frozen=True)
class Tool:
    name: str
    arguments: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class Node:
    node_id: str
    intent: str
    recipients: tuple[str, ...]
    facts: tuple[tuple[str, str | int | float], ...]
    requires: tuple[str, ...] = ()
    required_context: tuple[tuple[str, str | int | float], ...] = ()
    authority_scope: str | None = None
    authority_amount: float | None = None


@dataclass(frozen=True)
class PrivateFixture:
    task: PublicTask
    nodes: tuple[Node, ...]
    full_reference: tuple[tuple[str, str | int | float], ...]
    baseline_reference: tuple[tuple[str, str | int | float], ...]
    help_class: str
    reference_path: str = "improve"

    def __post_init__(self):
        require(self.help_class in {"Must-help", "Optional-help"}
                and self.reference_path in {"baseline", "improve"}, "Explicit private reference path required")
        require(self.help_class != "Must-help" or self.reference_path == "improve", "Must needs help path")
        ids = {n.node_id for n in self.nodes}
        require(len(ids) == len(self.nodes) and self.nodes, "Unique private nodes required")
        require(all(n.intent in self.task.intents and n.recipients and n.facts
                    and set(n.recipients) <= {p.person_id for p in self.task.people}
                    and set(n.requires) <= ids and n.node_id not in n.requires
                    and len(dict(n.facts)) == len(n.facts) for n in self.nodes),
                "Malformed dependency node")
        require(all((n.authority_scope is None and n.authority_amount is None) or
                    (isinstance(n.authority_scope, str) and type(n.authority_amount) in (int, float)
                     and math.isfinite(n.authority_amount) and n.authority_amount >= 0)
                    for n in self.nodes), "Authority scope and amount must be paired")
        seen = set()
        while len(seen) < len(ids):
            ready = {n.node_id for n in self.nodes if set(n.requires) <= seen} - seen
            require(ready, "Cyclic private DAG")
            seen.update(ready)
