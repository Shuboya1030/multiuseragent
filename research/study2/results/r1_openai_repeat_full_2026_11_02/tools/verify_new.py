"""Audit or extract the public new90 evidence without any network/model calls."""
import argparse
import collections
import hashlib
import importlib.util
import json
import math
import re
import tempfile
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OLD = ROOT.parent / "r1_2026_11_02"
spec = importlib.util.spec_from_file_location("previous_bundle_reader", OLD / "tools" / "verify_bundle.py")
prior = importlib.util.module_from_spec(spec)
spec.loader.exec_module(prior)
prior.ROOT = ROOT


def equal(a, b):
    return a == b if a is None or b is None else math.isclose(a, b, abs_tol=1e-9)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--extract", type=Path)
    args = parser.parse_args()
    bundle = prior.Bundle()
    secret = re.compile(
        r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
        r"github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|eyJ[A-Za-z0-9_-]{15,}\."
        r"[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b")
    drive = re.compile(r"\b[A-Za-z]:[\\/]")
    for name, entry in bundle.entries.items():
        data = bundle.read(name)
        assert hashlib.sha256(data).hexdigest() == entry["published_sha256"], name
        text = data.decode("utf-8")
        assert not secret.search(text) and not drive.search(text), name
        assert "-----BEGIN PRIVATE KEY-----" not in text, name
        if name.endswith(".json"):
            prior.audit_credentials(json.loads(text))
        elif name.endswith(".jsonl"):
            for line in text.splitlines():
                if line:
                    prior.audit_credentials(json.loads(line))
    for archive, stream in bundle.archives.items():
        expected = {v["target"] for v in bundle.entries.values() if v["archive"] == archive}
        assert set(stream.namelist()) == expected and len(stream.namelist()) == len(expected)
        assert (ROOT / archive).stat().st_size < 45 * 1024 * 1024
    for p in ROOT.rglob("*"):
        if p.is_file() and p.suffix != ".zip" and "__pycache__" not in p.parts:
            text = p.read_text(encoding="utf-8-sig")
            assert not secret.search(text) and not drive.search(text), p.name
            assert p.stat().st_size < 45 * 1024 * 1024
    index = bundle.json("derived_full_v1/All_90_Attempts.json")
    assert len(index) == len({v["episode_id"] for v in index}) == 90
    assert collections.Counter(v["group"] for v in index) == {"mini_repeat": 30, "gpt54_control": 60}
    assert len({(v["group"], v["task_id"]) for v in index}) == 90
    full = bundle.json("derived_full_v1/adjudications.json")
    mini = bundle.json("derived_mini_v1/adjudications.json")
    assert len(full) == 60 and len(mini) == 30
    assert sum(v["business"] == "business_success" for v in full) == 50
    assert sum(v["business"] == "business_success" for v in mini) == 2
    rows = bundle.csv("derived_full_v1/GPT54_Full60_Comparison.csv")
    assert len(rows) == 60
    assert len(bundle.csv("derived_full_v1/Same_V6_Must30_Pairs.csv")) == 30
    raw_entries = [e for e in bundle.entries.values() if e["target"].startswith("evidence/")]
    assert len(raw_entries) == bundle.manifest["source_run_files"] == 1844
    assert {v["target"].split("/")[1] for v in raw_entries} == {v["episode_id"] for v in index}
    decisions = {v["episode_id"]: v for v in full + mini}
    ledger = [json.loads(s) for s in bundle.read("accounting/cost_ledger.jsonl").splitlines() if s]
    reserves = {v["id"]: v for v in ledger if v["event"] == "reserve"}
    settlements = {v["id"]: v for v in ledger if v["event"] == "settle"}
    unknown = set(reserves) - set(settlements)
    assert len(unknown) == 5
    paid = sum((Decimal(v["amount_usd"]) for v in settlements.values()), Decimal(0))
    held = sum((Decimal(reserves[k]["amount_usd"]) for k in unknown), Decimal(0))
    assert paid == Decimal("7.32870910") and held == Decimal(".11172275")
    costs = collections.defaultdict(Decimal)
    new_calls = set()
    raw_recomputed = 0
    with tempfile.TemporaryDirectory(prefix="new90-public-audit-") as directory:
        path = Path(directory) / "scorer.py"
        path.write_bytes(bundle.read("analysis_inputs/grading/scorer.py"))
        module_spec = importlib.util.spec_from_file_location("new90_frozen_scorer", path)
        scorer = importlib.util.module_from_spec(module_spec)
        module_spec.loader.exec_module(scorer)
        for row in index:
            decision = decisions[row["episode_id"]]
            case = bundle.json(row["packet"])
            assert case["source"] == "evidence/" + row["episode_id"]
            source = case["source"]
            assert case["manifest"]["episode_id"] == row["episode_id"]
            assert case["status"]["collection_complete"] and case["runtime_error"] is None
            for name, sha in case["source_hashes"].items():
                assert bundle.entries[source + "/" + name]["source_sha256"] == sha
            events = case["contact_events"]
            actual_C = sum(case["role_costs"][e["colleague"]] for e in events if e["actor"] == "agent")
            assert actual_C == decision["C"]
            assert equal(decision["R"], decision["T"] - .05 * actual_C -
                         .3 * decision["Nauth"] - .1 * decision["Nwaste"])
            trace = bundle.json(source + "/trace_bundle.json")
            raw_answer = json.loads(case["workspace"]["/workspace/deliverable.json"]) if case["workspace"] else None
            blueprint = bundle.json("analysis_inputs/tasks/" + row["task_id"] + "/task_definition.json")
            raw = scorer.score_bundle(blueprint, raw_answer, trace, case["role_costs"])
            assert equal(raw["T"], case["raw_evaluation"]["T"]), row["task_id"]
            assert equal(raw["R"], case["raw_evaluation"]["R"]), row["task_id"]
            raw_recomputed += 1
            for line in bundle.read(source + "/api_io.jsonl").splitlines():
                item = json.loads(line)
                if item["stage"] == "response":
                    call = item["call_id"]
                    assert call in settlements and call not in new_calls
                    new_calls.add(call)
                    costs[row["group"]] += Decimal(settlements[call]["amount_usd"])
    assert len(new_calls) == 933 and raw_recomputed == 90
    assert costs["mini_repeat"] == Decimal(".30682500")
    assert costs["gpt54_control"] == Decimal("2.19931925")
    assert not bundle.manifest["omitted_research_records"]
    result = {
        "passed": True, "public_files_checked": len(bundle.entries),
        "raw_attempt_files": 1844, "attempts": 90, "raw_scores_recomputed": raw_recomputed,
        "settled_new_calls": 933, "agent_calls": 838, "NPC_calls": 95,
        "full_business_pass": 50, "mini_business_pass": 2,
        "new_cost_usd": str(sum(costs.values(), Decimal(0))),
        "global_occupied_usd": str(paid + held), "historical_unknown_count": len(unknown),
        "historical_unknown_usd": str(held), "new_unknown": 0,
        "absolute_path_dependencies": 0, "unredacted_credentials_detected": 0,
        "omitted_research_records": 0, "gold_validity_flags": ["o-high-eval-budget"],
        "R_prime_computed": False,
    }
    (ROOT / "PUBLICATION_VALIDATION.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(result, indent=2))
    if args.extract:
        bundle.extract(args.extract)


if __name__ == "__main__":
    main()
