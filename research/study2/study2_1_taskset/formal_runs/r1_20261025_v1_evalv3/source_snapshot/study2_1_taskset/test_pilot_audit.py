"""Offline audit regression tests; never calls a model or stores research data."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import urllib.error

import multimodel_r1_pilot as runner
from evaluate_episode import evaluate_task


class AuditTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        runner.CURRENT_MODEL = "openai"
        runner.RUN_TAG = "offline-test"
        runner.SECRETS = ["sk-test-do-not-save"]
        runner.LAST_API_REQUEST_AT.clear()

    def tearDown(self):
        self.temp.cleanup()

    def test_full_episode_and_replay(self):
        count = 0
        def fake_call(messages, key):
            nonlocal count
            ep = runner.AUDIT_DIR
            mapping = runner.read_json(ep / "identity_mapping.json")["canonical_to_alias"]
            gold = runner.read_json(runner.TASKS / "must-vendor-onboarding/gold_policy.json")
            recipients = gold["admissible_recipients_by_step"]["separated"]
            info = mapping[recipients["information"][0]]
            approval = mapping[recipients["approval"][0]]
            facts = runner.facts_from_gold(gold)
            actions = [
                ("send_message", {"recipient_id": info, "purpose": "information", "message": "Please provide verified vendor information."}),
                ("read_messages", {"recipient_id": info}),
                ("send_message", {"recipient_id": approval, "purpose": "approval", "message": "Please approve " + " ".join(map(str, facts.values()))}),
                ("read_messages", {"recipient_id": approval}),
                ("submit_answer", {"answer": {**facts, "approved_by": approval}}),
            ]
            name, args = actions[count]
            count += 1
            return {"role": "assistant", "content": None, "tool_calls": [{"id": f"test-{count}", "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}]}, {"prompt_tokens": 10, "completion_tokens": 5}, "offline-fake", "tool_calls", f"test-request-{count}", 0
        with patch.object(runner, "call_model", fake_call):
            record = runner.run_episode("must-vendor-onboarding", "separated", 20261026, self.root, "sk-test-do-not-save")
        self.assertTrue(record["behavior_metrics"]["task_success"])
        self.assertEqual(record["behavior_metrics"]["ask_count"], 2)
        ep = self.root / "episodes" / record["run_id"]
        events = runner.load_lines(ep / "trace_events.jsonl")
        required = runner.read_json(runner.HERE / "trace_schema.json")["required_fields"]
        self.assertTrue(all(set(required) <= set(e) for e in events))
        self.assertEqual(len(runner.load_lines(ep / "model_turns.jsonl")), 5)
        self.assertEqual(evaluate_task(runner.TASKS / "must-vendor-onboarding", ep / "answer.json", ep / "trace_events.jsonl", record["run_id"], "separated", ep / "identity_mapping.json"), runner.read_json(ep / "evaluation.json"))
        with self.assertRaises(FileExistsError):
            runner.run_episode("must-vendor-onboarding", "separated", 20261026, self.root, "sk-test-do-not-save")

    def test_failed_api_is_preserved_and_not_retried(self):
        err = urllib.error.HTTPError("https://api.openai.com/v1/chat/completions", 429, "limit", {}, io.BytesIO(b'{"error":{"message":"sk-test-do-not-save"}}'))
        with patch.object(runner.urllib.request, "urlopen", side_effect=err) as request:
            record = runner.run_episode("must-vendor-onboarding", "separated", 20261027, self.root, "sk-test-do-not-save")
        self.assertEqual(request.call_count, 1)
        self.assertEqual(record["status"], "failed")
        ep = self.root / "episodes" / record["run_id"]
        self.assertEqual([e["event"] for e in runner.load_lines(ep / "api_io.jsonl")], ["request", "error"])
        for p in ep.iterdir():
            if p.is_file(): self.assertNotIn("sk-test-do-not-save", p.read_text())

    def test_redaction(self):
        clean = runner.redact({"authorization": "secret", "reasoning_content": "private", "content": [{"type": "thinking", "thinking": "private"}, {"type": "text", "text": "public"}], "message": "sk-test-do-not-save"})
        self.assertEqual(clean, {"content": [{"type": "text", "text": "public"}], "message": "[redacted-key]"})


if __name__ == "__main__":
    unittest.main()
