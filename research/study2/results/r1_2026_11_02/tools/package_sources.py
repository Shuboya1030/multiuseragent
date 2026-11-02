"""Build a sanitized, portable R1 research handoff from read-only source evidence."""
import argparse
import collections
import csv
import hashlib
import io
import json
import re
import zipfile
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

ROOT = Path(__file__).resolve().parents[1]
SENSITIVE_KEY = re.compile(
    r"^(?:api[_-]?key|auth[_-]?token|access[_-]?token|refresh[_-]?token|"
    r"password|passwd|client[_-]?secret|secret|cookie|set-cookie|credential|token)$", re.I)
SECRET = re.compile(r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
                    r"github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16})\b")
URL = re.compile(r"https?://[^\s<>\"'`\\]+")
LOCAL_PATH = re.compile(r"\b[A-Za-z]:[\\/][^\s\"<>|`]+")
PRIVATE_KEY = re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")


def load(p):
    return json.loads(p.read_text(encoding="utf-8-sig"))


def digest(b):
    return hashlib.sha256(b).hexdigest()


class Package:
    def __init__(self, primary, other, repo):
        self.primary, self.other, self.repo = primary, other, repo
        self.final = primary / "r1_formal" / "final_r1_evaluation_v1"
        self.index = load(self.final / "index.json")
        self.entries, self.redactions = [], []
        self.maps = [(str(Path(a["run"])), "evidence/" + a["episode_id"]) for a in self.index]
        self.maps += [
            (str(self.final / "published_v1_snapshot"), "history/published_v1"),
            (str(self.final), "."),
            (str(primary / "r1_formal" / "five_content_adjudication_v1"), "adjudications"),
            (str(primary / "r1_formal" / "review84_semantic_v1"), "history/review84_semantic_v1"),
            (str(primary / "r1_formal" / "repair_review55_v1"), "history/repair_review55_v1"),
            (str(primary / "r1_formal" / "shared_budget"), "accounting"),
            (str(primary / "r1_formal"), "provenance/primary"),
            (str(other), "provenance/independent"),
            (str(primary), "provenance/primary-session"),
            (str(repo), "repository-source"),
        ]
        for task in sorted({row["task_id"] for row in self.index}):
            self.maps.append((str(repo / "research" / "study2" / "task_generation_v2" / "templates" / task),
                              "tasks/" + task))
        self.maps.sort(key=lambda pair: len(pair[0]), reverse=True)
        self.allowed_hosts = {"127.0.0.1", "localhost", "github.com", "raw.githubusercontent.com",
                              "api.openai.com", "api.anthropic.com", "api.moonshot.cn",
                              "api.moonshot.ai", "docs.github.com", "arxiv.org"}
        self.known_safe_literals = set()
        for row in self.index:
            packet = load(self.final / row["packet"])
            for url in URL.findall(json.dumps(packet["task"], ensure_ascii=False)):
                self.allowed_hosts.add(urlsplit(url.rstrip(".,)")).hostname)
        self.freeze = load(self.final / "freeze.json")["source_hashes"]
        self.archives = {}

    def source_ref(self, path):
        for root, label in ((self.primary, "primary"), (self.other, "independent"), (self.repo, "repository")):
            if path.is_relative_to(root):
                return label + "/" + path.relative_to(root).as_posix()
        raise ValueError("Source outside explicitly authorized roots")

    def string(self, value, counts):
        for before, after in self.maps:
            for spelling in (before, before.replace("\\", "/"), before.replace("\\", "\\\\")):
                if spelling in value:
                    counts["local_path_to_portable_reference"] += value.count(spelling)
                    value = value.replace(spelling, after)
        def private_path(match):
            counts["private_local_path_removed"] += 1
            return "[REDACTED_LOCAL_PATH]"
        value = LOCAL_PATH.sub(private_path, value)
        value = re.sub(r"(?:evidence|packets|tasks|adjudications|history|provenance|accounting|repository-source|\.)"
                       r"(?:[\\/][^\s\"'`<>]+)+", lambda m: m.group().replace("\\", "/"), value)
        def url_replace(match):
            raw = match.group()
            url = urlsplit(raw)
            if url.username or url.password:
                counts["url_userinfo_removed"] += 1
                return "[REDACTED_AUTHENTICATED_URL]"
            if url.hostname not in self.allowed_hosts:
                counts["unnecessary_external_runtime_endpoint_removed"] += 1
                return "[REDACTED_RUNTIME_ENDPOINT]" + url.path
            if re.search(r"(?i)(?:api[_-]?key|token|password|signature|sig)=", url.query):
                counts["url_credential_query_removed"] += 1
                return urlunsplit((url.scheme, url.netloc, url.path, "[REDACTED_QUERY]", url.fragment))
            return raw
        value = URL.sub(url_replace, value)
        def secret_replace(match):
            counts["credential_pattern_removed"] += 1
            return "[REDACTED_CREDENTIAL]"
        value = SECRET.sub(secret_replace, value)
        value = re.sub(r"(?i)\b(?:Bearer|Basic)\s+[A-Za-z0-9+/_=.-]{12,}", secret_replace, value)
        if PRIVATE_KEY.search(value):
            raise ValueError("Private key in source: manual review required; no file emitted")
        return value

    def sanitize(self, value, counts):
        if isinstance(value, dict):
            result = {}
            for key, item in value.items():
                new_key = self.string(key, counts)
                if SENSITIVE_KEY.fullmatch(key) and isinstance(item, str) and item:
                    counts["credential_field_removed"] += 1
                    result[new_key] = "[REDACTED_CREDENTIAL]"
                elif key.lower() == "authorization" and isinstance(item, str) and re.match(
                        r"(?i)^(?:Bearer|Basic)\s", item):
                    counts["authorization_header_removed"] += 1
                    result[new_key] = "[REDACTED_CREDENTIAL]"
                else:
                    result[new_key] = self.sanitize(item, counts)
            return result
        if isinstance(value, list):
            return [self.sanitize(item, counts) for item in value]
        if isinstance(value, str):
            if value.lstrip().startswith(("{", "[")):
                try:
                    parsed = json.loads(value)
                except ValueError:
                    pass
                else:
                    clean = self.sanitize(parsed, counts)
                    if clean != parsed:
                        return json.dumps(clean, ensure_ascii=False)
            return self.string(value, counts)
        return value

    def transform(self, source, raw):
        counts = collections.Counter()
        text = raw.decode("utf-8-sig")
        if source.suffix == ".json":
            clean = json.dumps(self.sanitize(json.loads(text), counts), ensure_ascii=False, indent=2) + "\n"
        elif source.suffix == ".jsonl":
            clean = "\n".join(json.dumps(self.sanitize(json.loads(line), counts), ensure_ascii=False)
                              for line in text.splitlines() if line) + "\n"
        elif source.suffix == ".csv":
            reader = csv.DictReader(io.StringIO(text))
            stream = io.StringIO(newline="")
            writer = csv.DictWriter(stream, fieldnames=reader.fieldnames)
            writer.writeheader()
            for row in reader:
                writer.writerow({k: self.sanitize(v, counts) for k, v in row.items()})
            clean = stream.getvalue()
        else:
            clean = self.string(text, counts)
        return clean.encode("utf-8"), counts

    def add(self, source, target, archive=None):
        raw = source.read_bytes()
        if str(source) in self.freeze:
            assert digest(raw) == self.freeze[str(source)], "Frozen source drift: " + self.source_ref(source)
        clean, counts = self.transform(source, raw)
        if archive:
            if archive not in self.archives:
                dest = ROOT / archive
                dest.parent.mkdir(parents=True, exist_ok=True)
                self.archives[archive] = zipfile.ZipFile(dest, "x", zipfile.ZIP_DEFLATED, compresslevel=9)
            info = zipfile.ZipInfo(target, (2026, 11, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            self.archives[archive].writestr(info, clean)
        else:
            dest = ROOT / target
            dest.parent.mkdir(parents=True, exist_ok=True)
            with dest.open("xb") as stream:
                stream.write(clean)
        record = {"source": self.source_ref(source), "target": target, "archive": archive,
                  "source_sha256": digest(raw), "published_sha256": digest(clean),
                  "source_bytes": len(raw), "published_bytes": len(clean),
                  "redactions": dict(counts)}
        self.entries.append(record)
        if counts:
            self.redactions.append(record)

    def add_folder(self, source, target, archive=None, recursive=False, extensions=None):
        iterator = source.rglob("*") if recursive else source.iterdir()
        for file in sorted(iterator):
            if not file.is_file() or "__pycache__" in file.parts:
                continue
            if extensions and file.suffix not in extensions:
                continue
            self.add(file, target + "/" + file.relative_to(source).as_posix(), archive)

    def build(self):
        text_data = {".json", ".jsonl", ".csv", ".md"}
        self.add_folder(self.final, "evaluation", extensions=text_data)
        self.add_folder(self.final / "published_v1_snapshot", "history/published_v1",
                        "archives/history.zip", extensions=text_data)
        self.add_folder(self.final / "packets", "packets", "archives/packets.zip",
                        extensions={".json", ".md"})
        for row in self.index:
            archive = "archives/" + row["provider"] + "-" + (
                "original" if row["attempt_order"] == 0 else "repair") + ".zip"
            self.add_folder(Path(row["run"]), "evidence/" + row["episode_id"], archive, recursive=True)
        task_ids = sorted({row["task_id"] for row in self.index})
        for task in task_ids:
            folder = self.repo / "research" / "study2" / "task_generation_v2" / "templates" / task
            for sub in ("blueprint.json", "tac/scenarios.json", "tac/grading/scorer.py", "tac/grading/costs.json"):
                self.add(folder / sub, "tasks/" + task + "/" + sub, "archives/tasks.zip")
        base = self.primary / "r1_formal"
        self.add(base / "tasks.csv", "provenance/primary/tasks.csv", "archives/context.zip")
        protocol = self.repo / "research" / "study2" / "Study2_1_R1_Formal_Protocol_20261025.md"
        self.add(protocol, "provenance/protocol/" + protocol.name, "archives/context.zip")
        for name in ("five_content_adjudication_v1", "review84_semantic_v1", "repair_review55_v1"):
            self.add_folder(base / name, "adjudications" if name.startswith("five") else "history/" + name,
                            "archives/history.zip", extensions=text_data)
        repair = base / "repair61_v1"
        for name in ("authorization.json", "NPC_rule_v3.json", "resume_rule_v3_manifest.json",
                     "queue.json", "progress.json", "results.jsonl", "completion_rule_v3.json",
                     "baseline_budget.json", "controller.py", "runtime.py"):
            if (repair / name).exists():
                self.add(repair / name, "provenance/primary/repair61_v1/" + name, "archives/context.zip")
        for name in ("R1_Kimi_Six_Results_CN.md", "R1_Kimi_Two_Technical_Reruns_CN.md"):
            self.add(self.other / name, "provenance/independent/" + name, "archives/context.zip")
        for phase, runner in (("r1_six_input_waiver", "six_runner"),
                              ("r1_two_technical_reruns", "two_runner")):
            origin = self.other / phase
            self.add_folder(origin, "provenance/independent/" + phase, "archives/context.zip",
                            extensions=text_data)
            folder = origin / "frozen_stage" / runner
            self.add_folder(folder, "provenance/independent/" + phase + "/frozen_stage/" + runner,
                            "archives/context.zip", extensions=text_data | {".py"})
            for file in (origin / "frozen_stage").glob("*.py"):
                self.add(file, "provenance/independent/" + phase + "/frozen_stage/" + file.name,
                         "archives/context.zip")
        for name in ("cost_ledger.jsonl", "shared_budget_manifest.json", "kimi_account_pacing_v1.jsonl",
                     "rest_rate_pacing.jsonl", "chat_post_pacing.jsonl"):
            self.add(base / "shared_budget" / name, "accounting/" + name, "archives/context.zip")
        wanted = set()
        for row in self.index:
            manifest = load(Path(row["run"]) / "run_manifest.json")
            wanted.update(v for k, v in manifest.items()
                          if k in ("runner_sha256", "npc_implementation_sha256", "controller_sha256")
                          and isinstance(v, str))
        found = set()
        candidates = list(self.primary.rglob("*.py")) + list(self.other.rglob("*.py"))
        candidates += list((self.repo / "research" / "study2" / "task_generation_v2" / "runtime").glob("*.py"))
        for source in candidates:
            sha = digest(source.read_bytes())
            if sha in wanted and sha not in found:
                self.add(source, "implementations/" + sha + ".py", "archives/context.zip")
                found.add(sha)
        for archive in self.archives.values():
            archive.close()
        payload = {
            "schema": "r1-portable-handoff-1", "original_slots": 180, "repair_slots": 61,
            "repair_attempts": 63, "total_attempts": 243, "source_run_files": 5393,
            "entries": self.entries,
            "implementation_hashes_required": sorted(wanted),
            "implementation_hashes_found": sorted(found),
            "implementation_hashes_not_located": sorted(wanted - found),
            "omitted_research_records": [],
            "intentionally_not_copied": ["runtime caches/dependencies/model vocabularies",
                                        "live service locks/cursors as control files",
                                        "unrelated dirty checkout files and personal research context"],
        }
        write_json(ROOT / "manifest.json", payload)
        write_json(ROOT / "redaction_manifest.json", {
            "policy": "No credentials, local personal paths or unnecessary private runtime endpoints. "
                      "Synthetic benchmark authorization references, roles, factual payloads and tool outputs retained.",
            "files": self.redactions,
            "reason_counts": dict(sum((collections.Counter(r["redactions"]) for r in self.redactions),
                                     collections.Counter())),
        })
        print(json.dumps({"records": len(self.entries), "archives": len(self.archives),
                          "redacted_files": len(self.redactions),
                          "implementation_hashes_not_located": sorted(wanted - found)}, indent=2))


def write_json(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--primary-files", type=Path, required=True)
    parser.add_argument("--independent-files", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, required=True)
    parser.add_argument("--add-missing-frozen-sources", action="store_true")
    args = parser.parse_args()
    package = Package(args.primary_files.resolve(), args.independent_files.resolve(), args.repo_root.resolve())
    if args.add_missing_frozen_sources:
        manifest = load(ROOT / "manifest.json")
        redactions = load(ROOT / "redaction_manifest.json")
        targets = {entry["target"] for entry in manifest["entries"]}
        for source in package.freeze:
            target = package.string(source, collections.Counter()).removeprefix("./")
            if target not in targets:
                package.add(Path(source), target)
        manifest["entries"] += package.entries
        redactions["files"] += package.redactions
        redactions["reason_counts"] = dict(collections.Counter(redactions["reason_counts"]) +
                                            sum((collections.Counter(r["redactions"]) for r in package.redactions),
                                                collections.Counter()))
        for name, value in (("manifest.json", manifest), ("redaction_manifest.json", redactions)):
            (ROOT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding="utf-8")
        print("Added frozen sources:", len(package.entries))
    else:
        package.build()


if __name__ == "__main__":
    main()
