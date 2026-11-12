"""Concrete Responses API payloads with LOCAL injection only; no HTTP/key code."""

from .contracts import canonical, require, strict_json
from .executor import TOOL_SCHEMA, ordinary_request, parse_tool, validate_question
from .oracle import validate_public_observation

MODEL = "gpt-5.4-mini-2026-03-17"


def object_schema(properties):
    return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}


STRING = {"type": "string"}
SCHEMAS = {
    "control": object_schema({"action": {"type": "string", "enum": ["SELF", "ASK", "SUBMIT"]},
                              "person_id": {"type": ["string", "null"]}}),
    "question": object_schema({"intent": STRING, "include_value_ids": {"type": "array", "items": STRING},
                               "question": STRING}),
    "ordinary": object_schema({"tool": {"type": "string", "enum": list(TOOL_SCHEMA)},
                               "arguments": STRING}),
}


def build_request(operation, observation, proposed=None, person_id=None, assistance=None):
    validate_public_observation(observation)
    require(operation in SCHEMAS, "Unsupported mini operation")
    if operation == "ordinary":
        body = ordinary_request(observation)
        instruction = body["instruction"] + " Encode arguments as a JSON string; exactly the selected tool's fields."
    else:
        body = {"operation": operation, "state": observation}
        if operation == "control":
            body["proposed_ordinary"] = ({"tool": proposed.name, "arguments": dict(proposed.arguments)}
                                         if proposed is not None else None)
            instruction = ("Choose SELF (allow one ordinary action), ASK to one public person, or SUBMIT only "
                           "when public delivery is complete. Non-ASK person_id must be null. No final answer.")
        else:
            require(person_id in {p["person_id"] for p in observation["task"]["people"]}, "Nonpublic question recipient")
            body["person_id"] = person_id
            if assistance is not None:
                require(set(assistance) == {"intent", "include_value_ids"}, "Private what metadata forbidden")
                require(assistance["intent"] in observation["task"]["intents"] and
                        set(assistance["include_value_ids"]) <= {v["value_id"] for v in observation["obtained_values"]},
                        "Assistance cannot include unread fields/values")
                body["request_plan"] = assistance
            instruction = ("Choose one exact public intent and obtained value IDs. Begin question with that intent "
                           "and a period. Preserve each selected key=value citation and the public task context. "
                           "Never invent values or authority. If request_plan exists follow it exactly.")
    return {"model": MODEL, "reasoning": {"effort": "none"}, "max_output_tokens": 1024,
            "input": [{"role": "system", "content": instruction}, {"role": "user", "content": canonical(body)}],
            "text": {"format": {"type": "json_schema", "name": "study4_" + operation,
                                 "strict": True, "schema": SCHEMAS[operation]}}}


def validate_output(operation, data, observation, assistance=None):
    require(isinstance(data, dict) and set(data) == set(SCHEMAS[operation]["properties"]),
            "Wrong model response shape")
    if operation == "ordinary":
        require(isinstance(data["arguments"], str), "API arguments must be encoded JSON string")
        parse_tool(canonical({"tool": data["tool"], "arguments": strict_json(data["arguments"])}))
    elif operation == "control":
        require(data["action"] in {"SELF", "ASK", "SUBMIT"} and
                (data["person_id"] in {p["person_id"] for p in observation["task"]["people"]}
                 if data["action"] == "ASK" else data["person_id"] is None),
                "Invalid controller action/person")
    else:
        require(isinstance(data["include_value_ids"], list) and
                all(isinstance(v, str) for v in data["include_value_ids"]), "Invalid value selection")
        require(data["intent"] in observation["task"]["intents"] and
                len(set(data["include_value_ids"])) == len(data["include_value_ids"]) and
                set(data["include_value_ids"]) <= {v["value_id"] for v in observation["obtained_values"]},
                "Question selected unread/duplicate context")
        require(assistance is None or {k: data[k] for k in assistance} == assistance,
                "Privileged obtained-only request plan changed")
        selected = [v for v in observation["obtained_values"] if v["value_id"] in data["include_value_ids"]]
        validate_question(data["question"], data["intent"], selected)
    return data


class LocalMini:
    """Injected MOCK callback; a real API transport is intentionally absent until authorization."""
    def __init__(self, generate, count_full_request_tokens, budget, episode_id):
        require(callable(generate) and callable(count_full_request_tokens), "Explicit mock/tokenizer required")
        self.generate, self.count_tokens = generate, count_full_request_tokens
        self.budget, self.episode_id = budget, episode_id
        self.requests, self.failed = [], False
        self.identity = MODEL + ":LOCAL-callback-NOT-real-inference"

    def _call(self, operation, observation, **kwargs):
        require(not self.failed, "Failed mini turn; automatic retry forbidden")
        request = build_request(operation, observation, **kwargs)
        require(request["max_output_tokens"] == self.budget.caps.output_tokens,
                "Wire output ceiling differs from reservation")
        count = self.count_tokens(request)
        call_id = f"{self.episode_id}:mock-call:{len(self.requests)}"
        self.budget.reserve(call_id, self.episode_id, operation, count)
        self.requests.append(request)
        try:
            response = self.generate(request)
            require(set(response) == {"output_text", "usage", "status"} and response["status"] == "completed",
                    "Missing/partial response")
            usage = response["usage"]
            require(set(usage) == {"input_tokens", "output_tokens"}, "Missing usage")
            self.budget.settle(call_id, usage["input_tokens"], usage["output_tokens"])
        except Exception:
            if self.budget.rows[call_id]["status"] == "reserved":
                self.budget.unknown(call_id)
            self.failed = True
            raise
        try:
            data = strict_json(response["output_text"])
            return validate_output(operation, data, observation, kwargs.get("assistance"))
        except Exception:
            self.failed = True
            raise

    def ordinary(self, observation):
        data = self._call("ordinary", observation)
        try:
            require(isinstance(data["arguments"], str), "API arguments must be encoded JSON string")
            return parse_tool(canonical({"tool": data["tool"], "arguments": strict_json(data["arguments"])}))
        except Exception:
            self.failed = True
            raise

    def control(self, observation, proposed):
        return self._call("control", observation, proposed=proposed)

    def question_plan(self, observation, person_id, assistance=None):
        return self._call("question", observation, person_id=person_id, assistance=assistance)
