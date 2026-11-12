from copy import deepcopy
import unittest

from .admission import decode_response, pending_plan, prepare_request
from .contracts import canonical, strict_json
from .executor import ORDINARY_PROMPT_VERSION
from .local_ceiling_check import make_case
from .mini_request import build_provider_request
from .scheduler import ARMS
from .test_response_diagnosis import synthetic_response


class SingleActionPromptTests(unittest.TestCase):
    def test_all_arms_share_same_one_turn_ordinary_payload_and_unmodified_action_contract(self):
        requests = []
        for arm in ARMS:
            _, runtime, _, _ = make_case("o-low-team-lunch", arm)
            request = build_provider_request("ordinary", runtime.observe())
            prepare_request(request, "ordinary", pending_plan())
            requests.append(request)
            body = strict_json(request["input"][1]["content"])
            self.assertEqual(body["prompt_version"], ORDINARY_PROMPT_VERSION)
            self.assertIn("stop and wait for the tool result", request["input"][0]["content"])
            self.assertIn("separate future turns", request["input"][0]["content"])
            self.assertEqual(set(body["tools"]), {"read_file", "write_file", "list_files", "post_channel", "submit"})
        self.assertTrue(all(request == requests[0] for request in requests))

    def test_single_legal_action_accepted_but_two_messages_or_bad_arguments_still_rejected(self):
        _, runtime, _, _ = make_case("o-low-team-lunch", "A")
        request = build_provider_request("ordinary", runtime.observe())
        _, bound, observation, assistance = prepare_request(request, "ordinary", pending_plan())
        base = synthetic_response()
        base["output"][0]["content"][0]["text"] = canonical({"tool": "list_files", "arguments": "{}"})
        result = decode_response(canonical(base).encode(), "ordinary", observation, assistance, pending_plan(), bound)
        self.assertEqual(result["data"]["tool"], "list_files")
        multiple = deepcopy(base)
        multiple["output"].append(deepcopy(multiple["output"][0]))
        with self.assertRaisesRegex(ValueError, "output_items"):
            decode_response(canonical(multiple).encode(), "ordinary", observation, assistance, pending_plan(), bound)
        bad = deepcopy(base)
        bad["output"][0]["content"][0]["text"] = canonical({"tool": "list_files", "arguments": '{"extra":"bad"}'})
        with self.assertRaisesRegex(ValueError, "application_validation"):
            decode_response(canonical(bad).encode(), "ordinary", observation, assistance, pending_plan(), bound)


if __name__ == "__main__":
    unittest.main()
