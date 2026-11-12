"""Privileged DAG reference and necessary public-label consistency checks."""
from copy import deepcopy

from .contracts import CONTROL_ACTIONS, PROTOCOL, Decision, fingerprint, require
from .npc_rule import has_authority


class DAGReference:
    """A declared path reference, not a utility-optimal policy or deployed input."""
    def __init__(self, fixture):
        self.fixture = fixture

    def acceptable(self, observation, released):
        require(set(released) <= {n.node_id for n in self.fixture.nodes}, "Invalid private release state")
        if self.fixture.reference_path == "improve":
            unsatisfied = [n for n in self.fixture.nodes if n.node_id not in released]
            ready = [n for n in unsatisfied if set(n.requires) <= set(released)]
            if ready:
                decisions = []
                for node in ready:
                    included = []
                    for key, value in node.required_context:
                        matches = [v["value_id"] for v in observation["obtained_values"]
                                   if v["key"] == key and v["value"] == value]
                        if not matches:
                            break
                        included.append(matches[-1])
                    else:
                        eligible = [p for p in self.fixture.task.people
                                    if p.person_id in node.recipients and has_authority(p, node)]
                        require(eligible, "Private reference has no legally authorized recipient")
                        cheapest = min(p.cost for p in eligible)
                        decisions.extend(Decision("ASK", p.person_id, node.intent, tuple(included))
                                         for p in eligible if p.cost == cheapest)
                require(decisions, "Ready private step has no obtained context: reference cannot solve this state")
                return tuple(decisions)
            require(not unsatisfied, "No ready private node; reference state is inconsistent")
        return (Decision("SELF"),)

    def choose(self, observation, released):
        return self.acceptable(observation, released)[0]


def validate_public_observation(observation):
    expected = {"protocol", "task", "workspace", "history", "obtained_values", "progress",
                "normal_actions", "remaining", "contact_cost", "terminal", "failed"}
    require(set(observation) in (expected, expected | {"context"}), "Unknown/private observation fields")
    require(observation["protocol"] == PROTOCOL, "Historical observation protocol is not help-only")
    require(set(observation["task"]) == {"instruction", "people", "intents", "output_fields",
                                        "artifact_path", "channel", "calculations"}, "Private task metadata")
    require(all(set(p) == {"person_id", "role", "knowledge", "authority", "cost"}
                for p in observation["task"]["people"]), "Private candidate metadata")
    require(set(observation["progress"]) == {"artifact_present", "artifact_public_shape_valid",
                                             "artifact_revision", "posted_current_revision",
                                             "user_delivery_complete", "bridge_submitted", "business_success"},
            "Private progress metadata")
    require(observation["progress"]["business_success"] is None, "Evaluator outcome is not public progress")
    allowed_values = {"value_id", "key", "value", "source_message_id", "source_person_id",
                      "source_value_ids", "source_kind"}
    require(all(set(v) <= allowed_values and {"value_id", "key", "value", "source_message_id",
                                            "source_person_id"} <= set(v)
                for v in observation["obtained_values"]), "Private obtained-value metadata")
    allowed_event_keys = {"event_id", "kind", "action", "person_id", "message_id", "content",
                          "in_reply_to", "path", "channel", "tool", "answer", "reason",
                          "bridge_submitted", "exception_type", "business_outcome"}
    require(all(set(event) <= allowed_event_keys for event in observation["history"]), "Private history metadata")
    require(all(event["kind"] != "control_decision" or event.get("action") in CONTROL_ACTIONS
                for event in observation["history"]), "Historical three-state control history forbidden")


def public_signature(observation):
    validate_public_observation(observation)
    omitted = {"event_id", "message_id", "source_message_id", "value_id", "in_reply_to", "source_value_ids"}

    def clean(value):
        if isinstance(value, dict):
            return {k: clean(v) for k, v in value.items() if k not in omitted}
        if isinstance(value, (tuple, list)):
            return [clean(v) for v in value]
        return value

    return fingerprint(clean(observation))


def label_signature(decision, observation):
    require(decision.action in CONTROL_ACTIONS, "Historical three-state supervision label forbidden")
    included = [v for v in observation["obtained_values"] if v["value_id"] in decision.include_value_ids]
    return fingerprint({"action": decision.action, "person": decision.person_id, "intent": decision.intent,
                        "included": [(v["key"], v["value"], v["source_person_id"]) for v in included]})


def identifiability_audit(rows):
    """Intersection-empty labels for identical public states cannot be uniquely learned."""
    groups = {}
    for observation, acceptable in rows:
        require(acceptable, "Reference must supply explicit acceptable labels")
        signature = public_signature(observation)
        labels = {label_signature(d, observation) for d in acceptable}
        group = groups.setdefault(signature, [])
        group.append(labels)
    output = []
    for signature, choices in groups.items():
        intersection = set.intersection(*choices)
        output.append({"public_signature": signature, "states": len(choices),
                       "status": "compatible" if intersection else "unidentifiable",
                       "shared_acceptable_label_fingerprints": sorted(intersection),
                       "unique_label": len(intersection) == 1})
    return deepcopy(output)
