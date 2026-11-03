"""Reuse full R1 review-packet extraction without reusing its judgments."""
from pathlib import Path

here = Path(__file__).resolve().parent
old = here.parent / "r1_openai_repeat_and_full_v1"
text = (old / "collect_review_inputs.py").read_text(encoding="utf-8")
assert 'definition = HERE / "analysis_inputs" / "tasks" / slot["task_id"]' in text
text = text.replace('definition = HERE / "analysis_inputs" / "tasks" / slot["task_id"]',
                    'definition = HERE / "task_inputs" / "templates" / slot["task_id"]')
text = text.replace('definition / "task_definition.json"', 'definition / "blueprint.json"')
text = text.replace('/90 terminated', '/60 terminated')
(here / "collect_review_inputs.py").write_text(text, encoding="utf-8")
print("Prepared R0 review extraction only; no semantic decisions copied from R1")
