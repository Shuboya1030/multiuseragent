"""Verify or safely extract the portable R1 dataset. No network or experiment calls."""
import argparse
import collections
import csv
import hashlib
import importlib.util
import io
import json
import math
import re
import tempfile
import zipfile
from decimal import Decimal
from pathlib import Path, PurePosixPath

ROOT = Path(__file__).resolve().parents[1]


class Bundle:
    def __init__(self):
        self.manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
        self.entries = {e["target"]: e for e in self.manifest["entries"]}
        assert len(self.entries) == len(self.manifest["entries"])
        self.archives = {e["archive"]: zipfile.ZipFile(ROOT / e["archive"])
                         for e in self.entries.values() if e["archive"]}

    def read(self, name):
        entry = self.entries[name.replace("\\", "/").removeprefix("./")]
        return (self.archives[entry["archive"]].read(entry["target"])
                if entry["archive"] else (ROOT / entry["target"]).read_bytes())

    def json(self, name):
        return json.loads(self.read(name))

    def csv(self, name):
        return list(csv.DictReader(io.StringIO(self.read(name).decode("utf-8-sig"))))

    def extract(self, destination):
        destination.mkdir(parents=True, exist_ok=True)
        for name, entry in self.entries.items():
            path = PurePosixPath(name)
            assert not path.is_absolute() and ".." not in path.parts
            target = destination.joinpath(*path.parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            with target.open("xb") as stream:
                stream.write(self.read(name))


def equal(a, b):
    return a == b if a is None or b is None else math.isclose(a, b, abs_tol=1e-9)


def audit_credentials(value):
    sensitive = {"apikey", "xapikey", "authtoken", "xauthtoken", "accesstoken", "refreshtoken",
                 "clientsecret", "password", "passwd", "cookie", "setcookie", "secret", "credential", "token"}
    if isinstance(value, dict):
        for key, item in value.items():
            if re.sub(r"[-_]", "", key.lower()) in sensitive and isinstance(item, str) and item:
                assert item.startswith("[REDACTED"), "Unredacted credential field"
            if key.lower() == "authorization" and isinstance(item, str):
                assert not re.match(r"(?i)^(?:Bearer|Basic)\s", item), "Unredacted authorization header"
            audit_credentials(item)
    elif isinstance(value, list):
        for item in value:
            audit_credentials(item)
    elif isinstance(value, str) and value.lstrip().startswith(("{", "[")):
        try:
            parsed = json.loads(value)
        except ValueError:
            return
        audit_credentials(parsed)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", type=Path, help="Extract into a new/empty local directory.")
    parser.add_argument("--write-validation", action="store_true", help="Write the verification summary.")
    args = parser.parse_args()
    bundle = Bundle()
    secret = re.compile(
        r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
        r"github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{15,}\."
        r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b")
    drive = re.compile(r"\b[A-Za-z]:[\\/]")
    for name, entry in bundle.entries.items():
        data = bundle.read(name)
        assert hashlib.sha256(data).hexdigest() == entry["published_sha256"], name
        text = data.decode("utf-8")
        assert not secret.search(text), "Credential-shaped value: " + name
        assert not drive.search(text), "Private absolute path: " + name
        assert "-----BEGIN PRIVATE KEY-----" not in text, name
        if name.endswith(".json"):
            audit_credentials(json.loads(text))
        elif name.endswith(".jsonl"):
            for line in text.splitlines():
                if line:
                    audit_credentials(json.loads(line))
    for archive, stream in bundle.archives.items():
        expected = {e["target"] for e in bundle.entries.values() if e["archive"] == archive}
        assert set(stream.namelist()) == expected and len(stream.namelist()) == len(expected), archive
        assert (ROOT / archive).stat().st_size < 45 * 1024 * 1024, archive
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix == ".zip" or "__pycache__" in path.parts:
            continue
        text = path.read_text(encoding="utf-8-sig")
        assert not secret.search(text), "Credential-shaped value in publication file"
        assert not drive.search(text), "Private absolute path in publication file"
        assert path.stat().st_size < 45 * 1024 * 1024
    master = bundle.csv("evaluation/R1_All_180_Slots.csv")
    attempts = bundle.json("evaluation/all_attempt_evaluations.json")["attempts"]
    assert len(master) == len({(r["provider"], r["task_id"]) for r in master}) == 180
    assert collections.Counter(r["provider"] for r in master) == {"openai": 60, "anthropic": 60, "kimi": 60}
    assert len(attempts) == len({r["episode_id"] for r in attempts}) == 243
    assert sum(int(r["authorized_repair_count"]) for r in master) == 63
    assert sum(int(r["authorized_repair_count"]) > 0 for r in master) == 61
    by_episode = {r["episode_id"]: r for r in attempts}
    for row in master:
        chain = [a for a in attempts if a["provider"] == row["provider"] and a["task_id"] == row["task_id"]]
        assert row["display_episode_id"] == max(chain, key=lambda a: a["attempt_order"])["episode_id"]
        assert row["display_T"] != "" and row["display_R"] != ""
        bundle.read(row["original_evidence"])
        bundle.read(row["display_evidence"])
    assert collections.Counter(r["display_business"] for r in master) == {
        "business_success": 133, "business_failure": 47}
    raw_files = [e for e in bundle.entries.values() if e["target"].startswith("evidence/")]
    assert len(raw_files) == bundle.manifest["source_run_files"] == 5393
    assert {e["target"].split("/")[1] for e in raw_files} == set(by_episode)
    freeze = bundle.json("evaluation/freeze.json")["source_hashes"]
    for name, sha in freeze.items():
        key = name.replace("\\", "/").removeprefix("./")
        assert key in bundle.entries, "Unpackaged frozen research source: " + key
        assert bundle.entries[key]["source_sha256"] == sha, key
    ledger = [json.loads(line) for line in bundle.read("accounting/cost_ledger.jsonl").splitlines() if line]
    reserved, settled = {}, Decimal(0)
    for event in ledger:
        if event["event"] == "reserve":
            assert event["id"] not in reserved
            reserved[event["id"]] = Decimal(event["amount_usd"])
        elif event["event"] == "settle":
            reserved.pop(event["id"])
            settled += Decimal(event["amount_usd"])
        else:
            raise AssertionError("Unexpected accounting event")
    assert settled == Decimal("4.82256485")
    assert len(reserved) == 5 and sum(reserved.values()) == Decimal("0.11172275")
    assert settled + sum(reserved.values()) == Decimal("4.93428760")
    raw_matches = derived_matches = 0
    with tempfile.TemporaryDirectory(prefix="r1-offline-score-") as directory:
        cache = {}
        for a in attempts:
            task = a["task_id"]
            if task not in cache:
                source = bundle.read("tasks/" + task + "/tac/grading/scorer.py")
                path = Path(directory) / (task + ".py")
                path.write_bytes(source)
                spec = importlib.util.spec_from_file_location(task.replace("-", "_"), path)
                scorer = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(scorer)
                cache[task] = (scorer, bundle.json("tasks/" + task + "/tac/grading/costs.json"))
            scorer, costs = cache[task]
            packet = bundle.json(a["packet"])
            blueprint = bundle.json("tasks/" + task + "/blueprint.json")
            assert blueprint == packet["task"]
            assert packet["identity"]["episode_id"] == a["episode_id"]
            trace = packet["trace"]
            if trace and trace.get("complete") is True and packet["evaluation"]:
                answer = packet["workspace"].get("/workspace/deliverable.json")
                answer = json.loads(answer) if isinstance(answer, str) else answer
                raw = scorer.score_bundle(blueprint, answer, trace, costs)
                assert equal(raw["T"], packet["evaluation"]["T"]), a["id"]
                assert equal(raw["R"], packet["evaluation"]["R"]), a["id"]
                raw_matches += 1
            if a["derived_T"] is None:
                assert a["business"] == "not_evaluable"
                continue
            expected = a["derived_T"] - .05 * a["C"] - .3 * a["Nauth"] - .1 * a["Nwaste"]
            assert equal(expected, a["derived_R"]), a["id"]
            if a["user_adjudication"]:
                result = a["user_adjudication"]["derived_original_formula_result"]
            else:
                trace["evidence_reviews"] = a["bound_evidence_reviews"]
                answer = None if a.get("observed_normal_stop_no_final_answer") else a["score_projection"]
                result = scorer.score_bundle(blueprint, answer, trace, costs)
            assert equal(result["T"], a["derived_T"]), a["id"]
            assert equal(result["R"], a["derived_R"]), a["id"]
            derived_matches += 1
    assert raw_matches == 242 and derived_matches == 230
    users = [a for a in attempts if a["user_adjudication"]]
    assert len(users) == 5 and all(a["business"] == "business_success" for a in users)
    if args.extract:
        bundle.extract(args.extract)
    result = {
        "original_slots": 180, "attempts": 243, "source_run_files": len(raw_files),
        "source_hashes_matched": len(freeze), "strict_raw_scores_reproduced": raw_matches,
        "derived_scores_verified": derived_matches, "binding_user_decisions": len(users),
        "display_business": {"pass": 133, "fail": 47}, "display_T_R_available": 180,
        "settled_usd": str(settled), "unknown_reservations": len(reserved),
        "unknown_reserved_usd": str(sum(reserved.values())),
        "implementation_hashes_not_located": bundle.manifest["implementation_hashes_not_located"],
        "archive_bytes": {name: (ROOT / name).stat().st_size for name in bundle.archives},
        "network_calls": 0,
    }
    if args.write_validation:
        (ROOT / "PUBLICATION_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
