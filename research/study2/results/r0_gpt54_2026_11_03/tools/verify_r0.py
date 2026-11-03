"""Verify/replay published R0 without session paths, services or model calls."""
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
spec = importlib.util.spec_from_file_location(
    "bundle_reader", ROOT.parent / "r1_2026_11_02/tools/verify_bundle.py")
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)
reader.ROOT = ROOT


def equal(a, b):
    return a == b if a is None or b is None else math.isclose(float(a), float(b), abs_tol=1e-9)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--extract", type=Path)
    args = parser.parse_args()
    bundle = reader.Bundle()
    secret = re.compile(r"\b(?:sk-(?:ant-)?[A-Za-z0-9_-]{20,}|gh[pousr]_[A-Za-z0-9]{20,}|"
                        r"github_pat_[A-Za-z0-9_]{20,}|AKIA[A-Z0-9]{16}|"
                        r"eyJ[A-Za-z0-9_-]{15,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,})\b")
    for name, entry in bundle.entries.items():
        data = bundle.read(name)
        assert hashlib.sha256(data).hexdigest() == entry["published_sha256"], name
        text = data.decode("utf-8")
        assert not secret.search(text) and not re.search(r"\b[A-Za-z]:[\\/]", text), name
        assert not re.search(r"-----BEGIN .*PRIVATE KEY-----|<Objs Version=", text), name
        if name.endswith(".json"):
            reader.audit_credentials(json.loads(text))
        elif name.endswith(".jsonl"):
            for line in text.splitlines():
                if line:
                    reader.audit_credentials(json.loads(line))
    for archive, stream in bundle.archives.items():
        expected = {e["target"] for e in bundle.entries.values() if e["archive"] == archive}
        assert set(stream.namelist()) == expected and len(stream.namelist()) == len(expected)
        assert (ROOT / archive).stat().st_size < 45 * 1024 * 1024
    scope = bundle.json("scope.json")
    decisions = bundle.json("evaluation_v1/adjudications.json")
    reviews = bundle.json("review_decisions.json")
    rows = bundle.csv("evaluation_v1/R0_R1_Paired60.csv")
    assert len(scope) == len(decisions) == len(rows) == len(reviews) == 60
    assert len({s["R0_episode_id"] for s in rows}) == 60
    assert {s["task_id"] for s in scope} == {d["task_id"] for d in decisions} == {s["task_id"] for s in rows}
    assert collections.Counter(d["help_class"] for d in decisions) == {"Must-help": 30, "Optional-help": 30}
    assert sum(d["business"] == "business_success" for d in decisions) == 54
    events = bundle.json("evaluation_v1/budget_provenance.json")["new_R0_events"]
    settled = {e["id"]: e for e in events if e["event"] == "settle"}
    reserved = {e["id"]: e for e in events if e["event"] == "reserve"}
    assert len(settled) == len(reserved) == 728 and set(settled) == set(reserved)
    assert sum((Decimal(e["amount_usd"]) for e in settled.values()), Decimal(0)) == Decimal("1.97668125")
    used, roles = set(), collections.Counter()
    with tempfile.TemporaryDirectory(prefix="r0-offline-replay-") as directory:
        file = Path(directory) / "scorer.py"
        file.write_bytes(bundle.read("task_inputs/grading/scorer.py"))
        spec = importlib.util.spec_from_file_location("r0_frozen_grader", file)
        scorer = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(scorer)
        for d in decisions:
            case = bundle.json(d["source_packet"])
            source = case["source"]
            assert case["manifest"]["episode_id"] == d["episode_id"]
            for name, digest in case["source_hashes"].items():
                assert bundle.entries[source + "/" + name]["source_sha256"] == digest
            answer = json.loads(case["workspace"]["/workspace/deliverable.json"])
            trace = bundle.json(source + "/trace_bundle.json")
            raw = scorer.score_bundle(case["task"], answer, trace, case["role_costs"])
            assert equal(raw["T"], case["raw_evaluation"]["T"]) and equal(raw["R"], case["raw_evaluation"]["R"])
            answer.update(reviews[d["task_id"]].get("projection", {}))
            gold, base = case["task"]["full_information_reference"], case["task"]["no_contact_reference"]
            match = {k: scorer.same_value(v, answer.get(k)) for k, v in gold.items()}
            if d["help_class"] == "Must-help":
                T = sum(match.values()) / len(match)
                business = all(match.values())
            else:
                different = [k for k in gold if not scorer.same_value(gold[k], base.get(k))]
                business = all(match[k] or (k in different and scorer.same_value(base[k], answer.get(k))) for k in gold)
                adopted = reviews[d["task_id"]].get("supported_fields", [])
                assert all(match[k] for k in adopted) and (not adopted or case["read_tools"])
                Q = len(adopted) / len(different) if business else 0
                assert equal(Q, d["Q"])
                T = .5 + .5 * Q if business else 0
            business = reviews[d["task_id"]].get("business", "business_success" if business else "business_failure")
            assert business == d["business"] and equal(T, d["T"])
            contacts = [e for e in case["contact_events"] if e["actor"] == "agent"]
            assert {e["message_id"] for e in contacts} == {l["request_id"] for l in d["contact_labels"]}
            assert sum(case["role_costs"][e["colleague"]] for e in contacts) == d["C"]
            admissible = {p for node in case["task"]["gold_dag"]["nodes"] for p in node["admissible_recipients"]}
            expected_labels = {}
            for event in contacts:
                wrong = event["colleague"] not in admissible
                na = int(wrong and bool(scorer.AUTH_RE.search(event["content"])))
                nw = int(wrong)
                override = reviews[d["task_id"]].get("contact_overrides", {}).get(event["message_id"])
                if override:
                    na, nw = override["Nauth"], override["Nwaste"]
                expected_labels[event["message_id"]] = (na, nw)
            assert all(expected_labels[l["request_id"]] == (l["Nauth"], l["Nwaste"]) for l in d["contact_labels"])
            assert sum(v[0] for v in expected_labels.values()) == d["Nauth"]
            assert sum(v[1] for v in expected_labels.values()) == d["Nwaste"]
            assert equal(d["R"], T - .05*d["C"] - .3*d["Nauth"] - .1*d["Nwaste"])
            io = [json.loads(s) for s in bundle.read(source + "/api_io.jsonl").splitlines() if s]
            requests = {e["call_id"]: e for e in io if e["stage"] == "request"}
            responses = {e["call_id"]: e for e in io if e["stage"] == "response"}
            assert set(requests) == set(responses) and not used & set(requests)
            used.update(requests)
            directory = bundle.read("task_inputs/templates/" + d["task_id"] + "/tac/documents_R0/directory.md").decode()
            previous = None
            for ident, req in requests.items():
                payload, response = req["request"], responses[ident]["response"]
                assert response["usage"] == settled[ident]["usage"]
                expected = "gpt-5.4-2026-03-05" if req["role"] == "agent" else "gpt-5.4-mini-2026-03-17"
                assert payload["model"] == response["model"] == expected
                assert payload["reasoning_effort"] == "none"
                assert response["usage"].get("completion_tokens_details", {}).get("reasoning_tokens", 0) == 0
                assert Decimal(settled[ident]["amount_usd"]) <= Decimal(reserved[ident]["amount_usd"])
                roles[req["role"]] += 1
                if req["role"] == "agent":
                    assert payload["messages"][1]["content"].endswith(directory)
                    assert payload["reasoning_effort"] == "none" and payload["max_completion_tokens"] == 2048
                    assert payload["parallel_tool_calls"] is False and payload["tool_choice"] == "auto"
                    if previous:
                        assert payload["messages"][:len(previous)] == previous
                    previous = payload["messages"]
                else:
                    assert payload["max_completion_tokens"] == 1024
    assert used == set(settled) and roles == {"agent": 626, "npc": 102}
    assert not bundle.manifest["omitted_research_records"]
    result = {"passed": True, "attempts": 60, "raw_scores_replayed": 60,
              "semantic_scores_replayed": 60, "calls": 728, "roles": dict(roles),
              "business_pass": 54, "research_files": len(bundle.entries),
              "omitted_research_records": 0, "unredacted_credentials_detected": 0,
              "absolute_path_dependencies": 0, "R_prime_computed": False}
    (ROOT / "PUBLICATION_VALIDATION.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))
    if args.extract:
        bundle.extract(args.extract)


if __name__ == "__main__":
    main()
