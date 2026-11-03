"""Build read-only sanitized R0 evidence; no service or experiment calls."""
import argparse
import collections
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location(
    "publication90", ROOT.parent / "r1_openai_repeat_full_2026_11_02/tools/package_new.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
prior = module.prior
prior.ROOT = ROOT


class R0Package(module.NewPackage):
    def __init__(self, source, independent, repo):
        prior.Package.__init__(self, source.parent, independent, repo)
        self.source = source
        self.maps = [(a, "../r1_2026_11_02/" + b) for a, b in self.maps]
        self.maps += [(str(source), "."),
                      (str(source.parent / "r1_openai_repeat_and_full_v1"),
                       "../r1_openai_repeat_full_2026_11_02")]
        self.maps.sort(key=lambda pair: len(pair[0]), reverse=True)
        for task in (source / "task_inputs/templates").glob("*/blueprint.json"):
            for url in prior.URL.findall(task.read_text(encoding="utf-8")):
                self.allowed_hosts.add(prior.urlsplit(url.rstrip(".,)")).hostname)
        self.allowed_hosts.update({"developers.openai.com", "docs.python.org"})

    def build(self):
        excluded = []
        for file in sorted(self.source.rglob("*")):
            if not file.is_file():
                continue
            name = file.relative_to(self.source).as_posix()
            if file.suffix in {".pyc", ".ps1"} or "__pycache__" in file.parts:
                excluded.append({"path": name, "reason": "Bytecode or credential-loading bootstrap; not research payload"})
                continue
            if name.startswith("frozen_stage/runner/episodes/"):
                task = name.split("/")[4]
                help_class = prior.load(self.source / "task_inputs/templates" / task / "blueprint.json")["help_class"]
                archive = "archives/episodes-" + ("must" if help_class == "Must-help" else "optional") + ".zip"
            elif name.startswith("task_inputs/"):
                archive = "archives/frozen_inputs.zip"
            elif name.startswith("review_inputs/"):
                archive = "archives/review_packets.zip"
            elif name.startswith("frozen_stage/"):
                archive = "archives/runtime_context.zip"
            else:
                archive = None
            self.add(file, name, archive)
        for archive in self.archives.values():
            archive.close()
        assert len(self.entries) == len({e["target"] for e in self.entries})
        manifest = {"version": "study21-r0-publication-v1", "attempts": 60,
                    "paired_R1_package": "../r1_openai_repeat_full_2026_11_02",
                    "entries": self.entries, "omitted_research_records": [],
                    "excluded_nonresearch_files": excluded}
        (ROOT / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        (ROOT / "redaction_manifest.json").write_text(json.dumps({
            "source_read_only": True, "research_records_omitted": [],
            "source_to_public_hash_mapping": "manifest.json",
            "redactions_by_type": dict(collections.Counter({
                k: sum(e["redactions"].get(k, 0) for e in self.entries)
                for k in {k for e in self.entries for k in e["redactions"]}})),
            "entries": self.redactions
        }, indent=2), encoding="utf-8")
        print("Packaged", len(self.entries), "research files;", len(excluded), "nonresearch exclusions.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--independent", type=Path, required=True)
    args = parser.parse_args()
    R0Package(args.source, args.independent, ROOT.parents[3]).build()
