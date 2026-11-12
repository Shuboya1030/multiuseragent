"""Run hand-authored proof fixtures without models, external scorer or API."""
import argparse
from dataclasses import asdict, replace
import json
from pathlib import Path

from .contracts import PROTOCOL, Decision, canonical, fingerprint
from .executor import SharedExecutor
from .fixtures import PublicFixtureExecutor, fixture_proof, fixture_suite
from .npc_rule import RuleNPC
from .oracle import DAGReference, identifiability_audit
from .runtime import SharedRuntime


def run_suite():
    results, audit_rows = [], []
    for fixture in fixture_suite():
        row = {"fixture_id": fixture.task.task_id, "fixture_canonical_sha256": fingerprint(asdict(fixture)),
               "not_accepted_generated_benchmark_task": True, "declared_reference_path": fixture.reference_path}
        for policy in ("privileged_DAG_reference", "always_SELF"):
            callback = PublicFixtureExecutor()
            rt = SharedRuntime(fixture.task, SharedExecutor(callback), RuleNPC(fixture),
                               fixture.task.task_id + ":" + policy)
            reference = DAGReference(fixture)
            trajectory = []
            while not rt.terminal:
                before = rt.observe()
                labels = reference.acceptable(before, rt.npc.released) if policy == "privileged_DAG_reference" else ()
                if labels:
                    audit_rows.append((before, labels))
                decision = labels[0] if labels else Decision("SELF")
                rt.cycle(decision)
                trajectory.append({"public_observation_sha256": fingerprint(before),
                                   "decision": asdict(decision), "progress": rt.progress(),
                                   "normal_actions": rt.normal_actions, "contacts": rt.contacts})
            row[policy] = {"proof": fixture_proof(fixture, rt), "normal_actions": rt.normal_actions,
                           "contacts": rt.contacts, "contact_cost": rt.cost,
                           "mock_executor_callback_calls": rt.executor.calls, "trajectory": trajectory}
        results.append(row)
    ambiguous = fixture_suite()[0]
    contradictory = replace(ambiguous, nodes=(replace(ambiguous.nodes[0], recipients=("director",)),))
    states = []
    for fixture in (ambiguous, contradictory):
        rt = SharedRuntime(fixture.task, SharedExecutor(PublicFixtureExecutor()), RuleNPC(fixture), "ambiguous")
        states.append((rt.observe(), DAGReference(fixture).acceptable(rt.observe(), set())))
    audit = identifiability_audit(audit_rows)
    negative = identifiability_audit(states)
    reference_complete = sum(r["privileged_DAG_reference"]["proof"]["proof_complete"] for r in results)
    self_delivery = sum(r["always_SELF"]["proof"]["user_delivery_complete"]
                        and r["always_SELF"]["proof"]["bridge_submitted"] for r in results)
    report = {
        "schema": "study4-v2-local-fixture-acceptance-v2", "protocol_version": PROTOCOL,
        "new_model_API_calls": 0, "new_GPU_jobs": 0, "new_training_updates": 0,
        "mock_executor_only": True, "official_TribalBench_scorer_executed": False,
        "fixture_count": len(results), "reference_fixture_proof_complete": reference_complete,
        "always_SELF_public_delivery_and_submit": self_delivery,
        "always_SELF_content_valid": sum(r["always_SELF"]["proof"]["content_valid"] for r in results),
        "public_state_label_compatibility": audit, "intentional_unidentifiable_negative_control": negative,
        "local_protocol_gate_passed": reference_complete == len(results) and self_delivery == len(results)
                                      and all(r["status"] == "compatible" for r in audit)
                                      and all(r["status"] == "unidentifiable" for r in negative),
        "real_mini_ceiling_gate": "not run; requires separate authorization",
        "Phase2_generator_and_real_executor_gate": "not run; only hand-authored unit fixtures",
        "fixtures": results,
    }
    return json.loads(canonical(report))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True, help="New output JSON; existing files are refused")
    args = parser.parse_args()
    report = run_suite()
    with args.output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(report, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({k: report[k] for k in ("fixture_count", "reference_fixture_proof_complete",
                                           "always_SELF_public_delivery_and_submit", "local_protocol_gate_passed",
                                           "new_model_API_calls", "real_mini_ceiling_gate")}))
    if not report["local_protocol_gate_passed"]:
        raise SystemExit("Local protocol/fixture gate failed; do not proceed")


if __name__ == "__main__":
    main()
