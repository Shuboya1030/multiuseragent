"""Create public, sanitized copies of the ninety new attempts; no model calls."""
import argparse
import collections
import importlib.util
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "r1_2026_11_02"
spec = importlib.util.spec_from_file_location("prior_publication", OLD / "tools" / "package_sources.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
prior.ROOT = ROOT
prior.SENSITIVE_KEY = re.compile(
    r"^(?:api[_-]?key|x[_-]?api[_-]?key|x[_-]?auth[_-]?token|auth[_-]?token|"
    r"access[_-]?token|refresh[_-]?token|password|passwd|client[_-]?secret|"
    r"secret|cookie|set-cookie|credential|token)$", re.I)


class NewPackage(prior.Package):
    def __init__(self, source, independent, repo):
        super().__init__(source.parent, independent, repo)
        self.source = source
        self.new_index = prior.load(source / "derived_full_v1" / "All_90_Attempts.json")
        self.maps = [(a, "../r1_2026_11_02/" + b) for a, b in self.maps]
        for item in self.new_index:
            target = "evidence/" + item["episode_id"]
            self.maps += [(str(source / item["source"]), target),
                          (item["source"], target), (item["source"].replace("\\", "/"), target)]
        self.maps += [(str(source / "frozen_stage" / "runner"), "context/runner"),
                      (str(source / "analysis_inputs"), "analysis_inputs"),
                      (str(source), ".")]
        self.maps.sort(key=lambda pair: len(pair[0]), reverse=True)
        self.allowed_hosts.update({"developers.openai.com", "docs.python.org"})
        for path in (source / "analysis_inputs" / "tasks").glob("*/task_definition.json"):
            for url in prior.URL.findall(path.read_text(encoding="utf-8")):
                self.allowed_hosts.add(prior.urlsplit(url.rstrip(".,)")).hostname)

    def sanitize(self, value, counts):
        result = super().sanitize(value, counts)
        if isinstance(result, dict):
            normalized = {}
            for key, item in result.items():
                if "\\" in key:
                    key = key.replace("\\", "/")
                if key in {"source", "trace", "review", "packet", "source_packet",
                           "entry_report", "original_source", "target"} and isinstance(item, str):
                    item = item.replace("\\", "/")
                normalized[key] = item
            return normalized
        return result

    def build_new(self):
        allowed = {".json", ".jsonl", ".csv", ".md", ".txt", ".py"}
        for item in self.new_index:
            self.add_folder(self.source / item["source"], "evidence/" + item["episode_id"],
                            "archives/" + item["group"] + ".zip", recursive=True, extensions=allowed)
        for name in ("derived_full_v1", "derived_mini_v1"):
            self.add_folder(self.source / name, name, extensions=allowed)
        self.add_folder(self.source / "review_inputs", "review_inputs",
                        "archives/review_inputs.zip", extensions=allowed)
        self.add_folder(self.source / "analysis_inputs", "analysis_inputs",
                        "archives/analysis_inputs.zip", recursive=True, extensions=allowed)
        for file in sorted((self.source / "frozen_stage").rglob("*")):
            if (not file.is_file() or "episodes" in file.parts or "__pycache__" in file.parts
                    or file.suffix not in allowed):
                continue
            self.add(file, "context/" + file.relative_to(self.source / "frozen_stage").as_posix(),
                     "archives/context.zip")
        for file in sorted(self.source.iterdir()):
            if file.is_file() and file.suffix in allowed:
                self.add(file, "context/source/" + file.name, "archives/context.zip")
        for name in ("GPT54_Full60_Final_Evaluation_CN.md", "Mini_Must30_Repeat_Result_CN.md",
                     "evaluation_completion.json", "scope.json", "source_freeze.json"):
            self.add(self.source / name, name)
        ledger = self.source.parent / "r1_formal" / "shared_budget" / "cost_ledger.jsonl"
        self.add(ledger, "accounting/cost_ledger.jsonl")
        for stream in self.archives.values():
            stream.close()
        assert len(self.entries) == len({e["target"] for e in self.entries})
        source_runs = [e for e in self.entries if e["target"].startswith("evidence/")]
        manifest = {
            "version": "r1-openai-new90-publication-v1",
            "original_R1_package": "../r1_2026_11_02",
            "original_R1_commit": "823a12ae733ff790dd6910d6423c49731dc694ac",
            "scope": {"mini_repeat": 30, "gpt54_control": 60},
            "new_attempts": 90, "source_run_files": len(source_runs),
            "entries": self.entries,
            "omitted_research_records": [],
            "excluded_runtime_bootstrap": "launch.ps1: credential-loading bootstrap, not research payload",
        }
        (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
        (ROOT / "redaction_manifest.json").write_text(json.dumps({
            "source_evidence_read_only": True,
            "research_records_omitted": [],
            "source_to_public_hash_mapping": "manifest.json",
            "redactions_by_type": dict(collections.Counter(
                {key: sum(e["redactions"].get(key, 0) for e in self.entries)
                 for key in {k for e in self.entries for k in e["redactions"]}})),
            "entries": self.redactions,
        }, ensure_ascii=False, indent=2))
        print(json.dumps({"attempts": 90, "research_files": len(self.entries),
                          "raw_attempt_files": len(source_runs),
                          "archives": len(self.archives), "omitted_research_records": 0}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    args = parser.parse_args()
    NewPackage(args.source, args.independent, ROOT.parents[3]).build_new()
