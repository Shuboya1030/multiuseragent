"""Bounded three-head interface proof; no corpus generation or training."""
from types import SimpleNamespace

from .contracts import CONTROL_ACTIONS, Decision, canonical, fingerprint, require
from .oracle import identifiability_audit, validate_public_observation

SCHEMA = "study4-v2-three-head-help-only-2"


def supervision_row(observation, acceptable, family, organization, split):
    validate_public_observation(observation)
    require(split in {"train", "dev", "test"} and family and organization and acceptable,
            "Frozen split/group binding and acceptable labels required")
    for decision in acceptable:
        decision.validate(_PublicTaskView(observation), observation["obtained_values"])
    persons = [p["person_id"] for p in observation["task"]["people"]]
    intents = observation["task"]["intents"]
    values = [v["value_id"] for v in observation["obtained_values"]]
    return {
        "schema": SCHEMA, "public_input": observation, "public_input_sha256": fingerprint(observation),
        "group": {"family": family, "organization": organization, "split": split},
        "private_supervision_NOT_model_input": {
            "acceptable": [{"when": d.action, "whom": d.person_id, "intent": d.intent,
                            "include_value_ids": list(d.include_value_ids)} for d in acceptable],
            "mask": {"when": list(CONTROL_ACTIONS),
                     "whom": persons, "intent": intents, "include_value_ids": values},
            "when_loss": True, "whom_and_what_loss_only_on_ASK": True,
            "behavior_probability": None, "offline_RL_eligible": False,
        },
    }


class _PublicTaskView:
    def __init__(self, observation):
        self.people = [SimpleNamespace(person_id=p["person_id"])
                       for p in observation["task"]["people"]]
        self.intents = observation["task"]["intents"]


def audit_rows(rows):
    groups, public_rows = {}, []
    for row in rows:
        require(row["schema"] == SCHEMA, "Historical three-head schema forbidden")
        obs = row["public_input"]
        validate_public_observation(obs)
        require(row["public_input_sha256"] == fingerprint(obs), "Public row content changed")
        group = row["group"]
        # Stronger than task renaming: no family OR organization crosses split in this proof contract.
        for key in ("family", "organization"):
            previous = groups.setdefault((key, group[key]), group["split"])
            require(previous == group["split"], "Family/organization crosses frozen split")
        choices = row["private_supervision_NOT_model_input"]["acceptable"]
        decisions = tuple(Decision(c["when"], c["whom"], c["intent"], tuple(c["include_value_ids"])) for c in choices)
        require(row == supervision_row(obs, decisions, group["family"], group["organization"], group["split"]),
                "Supervision tuple/mask contract changed")
        public_rows.append((obs, decisions))
    audit = identifiability_audit(public_rows)
    require(all(g["status"] == "compatible" for g in audit), "Unidentifiable targets: exclude/review, not one-hot")
    return {"rows": len(rows), "compatible_public_groups": len(audit),
            "unique_targets": sum(g["unique_label"] for g in audit),
            "trained": False, "generator_accepted": False}


def model_input(row):
    """Only this explicitly projected field may enter a model/tokenizer."""
    require(row["schema"] == SCHEMA, "Wrong three-head schema")
    validate_public_observation(row["public_input"])
    require(row["public_input_sha256"] == fingerprint(row["public_input"]), "Changed model input")
    return canonical(row["public_input"])
