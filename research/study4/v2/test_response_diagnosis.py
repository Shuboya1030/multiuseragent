from copy import deepcopy
import unittest

from .admission import pending_plan
from .contracts import canonical
from .response_diagnosis import diagnose_offline
from .test_provider_bound import control_request


def synthetic_response():
    return {"id": "SYNTHETIC-NOT-ACTUAL", "model": pending_plan()["token_bound"]["model"],
            "status": "completed", "service_tier": "default", "error": None, "incomplete_details": None,
            "usage": {"input_tokens": 1101, "output_tokens": 133},
            "output": [{"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": canonical({"action": "SELF", "person_id": None})}]}]}


class OfflineDiagnosisTests(unittest.TestCase):
    def test_candidate_layers_reproduce_separate_failures_not_actual_root_cause(self):
        cases = {}
        base = synthetic_response()
        cases["baseline"] = base
        extra = deepcopy(base)
        extra["output"].insert(0, {"type": "reasoning", "summary": []})
        cases["extra_reasoning_candidate"] = extra
        refusal = deepcopy(base)
        refusal["output"][0]["content"] = [{"type": "refusal", "refusal": "NOT-RETAIN-ARBITRARY-TEXT"}]
        cases["refusal_candidate"] = refusal
        parse = deepcopy(base)
        parse["output"][0]["content"][0]["text"] = "{"
        cases["application_parse_candidate"] = parse
        invalid = deepcopy(base)
        invalid["output"][0]["content"][0]["text"] = canonical({"action": "INVALID", "person_id": None})
        cases["application_action_candidate"] = invalid
        frames = []
        for name, response in cases.items():
            with self.subTest(name=name):
                result = diagnose_offline(canonical(response).encode(), "control", control_request(),
                                          pending_plan(), provenance="SYNTHETIC-NOT-ACTUAL:" + name)
                self.assertEqual(result["accepted"], name == "baseline")
                self.assertNotIn("NOT-RETAIN-ARBITRARY-TEXT", canonical(result))
                if name != "baseline":
                    frames.extend(row["function"] for row in result["validator_frames"])
        self.assertIn("message", frames)
        self.assertIn("validate_output", frames)

    def test_embedded_arguments_diagnostic_keeps_only_allowlisted_key_types(self):
        from .local_ceiling_check import make_case
        from .mini_request import build_provider_request
        _, runtime, _, _ = make_case("o-low-team-lunch", "A")
        request = build_provider_request("ordinary", runtime.observe())
        raw = synthetic_response()
        raw["output"][0]["content"][0]["text"] = canonical({
            "tool": "write_file", "arguments": canonical({
                "path": "/workspace/DO-NOT-RETAIN", "content": "DO-NOT-RETAIN",
                "DO-NOT-RETAIN-UNKNOWN-KEY": "secret"})})
        result = diagnose_offline(canonical(raw).encode(), "ordinary", request, pending_plan(),
                                  provenance="SYNTHETIC-NOT-ACTUAL")
        self.assertFalse(result["accepted"])
        self.assertNotIn("DO-NOT-RETAIN", canonical(result))
        details = result["shape"]["output"][0]["content"][0]
        self.assertEqual(details["argument_shape"]["other_key_count"], 1)
        self.assertEqual(details["argument_shape"]["known_keys"], ["content", "path"])
        self.assertEqual(result["validator_frames"][-2]["function"], "parse_tool")


if __name__ == "__main__":
    unittest.main()
