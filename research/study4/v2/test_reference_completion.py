"""Zero-API completion and equivalence prerequisites, not new model outcomes."""
from copy import deepcopy
import json
import unittest

from .phase0 import load_case, reference_released, scorer, task_ids
from .reference_completion import (
    contracts, context_present, progress, public_context_aliases, ReferenceUncertain)


def exchange(events, person, request, reply):
    mid = "fixture:" + str(len(events))
    events.extend([
        {"kind": "send_message", "person_id": person, "message_id": mid, "content": request},
        {"kind": "read_messages", "person_id": person, "message_id": mid + ":reply",
         "in_reply_to": mid, "content": reply},
    ])


class ReferenceCompletionTests(unittest.TestCase):
    def test_public_entity_expansion_preserves_actual_portal_release(self):
        case, events = load_case("m-high-portal-launch"), []
        public = case.public.instruction + "\n" + "\n".join(t for _, t in case.public.documents)
        question = (
            "For the API v3 documentation portal go/no-go record, can you confirm the current "
            "docs_build_id, QA signoff, launch_date, and authorization_ref that should go into "
            "/workspace/deliverable.json?")
        exchange(events, "Priya Sharma", question,
                 "I can confirm the current build and launch date for the API v3 portal:\n"
                 "- docs_build_id: DB-318\n- launch_date: 2026-11-17\n"
                 "I don't have the QA signoff or authorization_ref.")
        self.assertIn("api v3 documentation portal", public_context_aliases("API v3 portal", public))
        self.assertEqual(reference_released(case, events), {"h1"})
        self.assertFalse(context_present("API v3 portal", question, "", scorer()))
        events[-1]["content"] = "The current build is DB-318."
        self.assertEqual(reference_released(case, events), set())
        self.assertNotIn("h2", progress(case, events, scorer())["released"])

    def test_public_aliases_are_general_source_bound_and_conservative(self):
        public = "The Atlas r7 customer console is the current public project."
        self.assertTrue(context_present(
            "Atlas r7 console", "Please confirm the Atlas r7 customer console details.", public, scorer()))
        cases = [
            "Please confirm the Atlas r2 customer console.",
            "Please confirm the Atlas r70 customer console.",
            "Please confirm the Borealis r7 customer console.",
            "This is not the Atlas r7 customer console.",
            "Maybe the Atlas r7 customer console is relevant.",
            "Atlas r7 customer console or Atlas r2 customer console?",
            "Atlas r7; the customer console belongs to a different project.",
            "The Atlas r7 customer console is not the task.",
        ]
        for request in cases:
            with self.subTest(request=request):
                self.assertFalse(context_present("Atlas r7 console", request, public, scorer()))
        self.assertFalse(context_present(
            "Atlas r7 console", "Atlas r7 confidential console?", public, scorer()))
        self.assertFalse(context_present("L5", "Not L5, use L6.", "", scorer()))
        self.assertFalse(context_present("9100", "Not USD 9100.", "", scorer()))
        self.assertFalse(context_present("9100", "Not USD 9,100.", "", scorer()))
        self.assertFalse(context_present("3", "There are 3.1 units.", "", scorer()))
        self.assertTrue(context_present("9100", "Total USD 9,100.", "", scorer()))

    def test_release_tier_has_actual_premises_and_source_bound_public_rule(self):
        case, events = load_case("m-high-model-release"), []
        exchange(events, "Wang Fang", "Aurora-7B current evaluation?",
                 "The current evaluation report is EV-19 and includes external benchmark claims. "
                 "I do not have the exact release tier or safety attestation wording.")
        result = progress(case, events, scorer())
        self.assertEqual(result["released"], {"h1"})
        certificate = next(iter(result["public_derivation_proofs_PRIVATE"].values()))
        self.assertEqual(certificate["target"], "release_tier")
        self.assertEqual(set(certificate["premise_sources"]), {"eval_report_id", "external_benchmark_claims"})
        self.assertIn("release-tiers.md", certificate["public_source_path"])
        self.assertFalse(any(p["node_id"] == "h2" for p in result["proof"]))
        missing_rule = deepcopy(case)
        from dataclasses import replace
        missing_rule.public = replace(case.public, documents=tuple(
            (p, t) for p, t in case.public.documents if not p.endswith("release-tiers.md")))
        self.assertEqual(reference_released(missing_rule, events), set())
        missing_report = deepcopy(events)
        missing_report[-1]["content"] = "The current evaluation includes external benchmark claims."
        self.assertEqual(reference_released(case, missing_report), set())

    def test_public_arithmetic_does_not_require_npc_to_repeat_a_computed_total(self):
        examples = [
            ("o-high-stream-cluster", "Zhang Wei", "analytics stream?",
             "Use cluster sw-2 with 2 new nodes.", "monthly_usd"),
            ("o-med-renewal-quote", "Mark Johnson", "Litware terms?",
             "Term years: 3\nAnnual USD: 21600", "total_usd"),
            ("o-high-cloud-budget", "Emma Lewis", "API server 2027?",
             "Instance count: 8\nCommitment: 1-year committed\nDiscount: 30%", "annual_usd"),
            ("o-med-batch-schedule", "Mike Chen", "embedding batch?",
             "Start UTC: 02:00\nDiscount: 40%", "monthly_usd"),
            ("o-med-brochure-translation", "Jessica Lee", "LinguaPro?",
             "Framework rate: USD 0.08 per word.", "total_usd"),
        ]
        for tid, person, question, reply, field in examples:
            with self.subTest(field=field, source=tid):
                case, events = load_case(tid), []
                exchange(events, person, question, reply)
                result = progress(case, events, scorer())
                self.assertEqual(result["released"], {"h1"})
                self.assertIn(field, {p["target"] for p in result["public_derivation_proofs_PRIVATE"].values()})

    def test_public_scope_or_deprecation_rationale_need_not_be_recited_as_extra_private_facts(self):
        examples = [
            ("o-med-browser-matrix", "Liu Qiang", "e-commerce redesign?",
             "The current supported browser count is 4."),
            ("o-medium-event-package", "Mark Johnson", "Harbor 30 customer workshop?",
             "Current commercial package: COMM30\nDiscount rate: 15%"),
        ]
        for tid, person, question, reply in examples:
            with self.subTest(source=tid):
                events = []
                exchange(events, person, question, reply)
                case = load_case(tid)
                self.assertEqual(reference_released(case, events),
                                 {n["id"] for n in case.blueprint["gold_dag"]["nodes"]})

    def test_actual_six_reply_conflict_keeps_acquired_fact_but_not_early_grant(self):
        from pathlib import Path
        data = json.loads((Path(__file__).parent / "reports" /
                          "REFERENCE_V5_ACTUAL_STOP_20261112.json").read_text(encoding="utf-8"))
        actual = data["actual_partial"]
        case, events = load_case(actual["slot"]["task_id"]), []
        for contact in actual["six_actual_exchanges_and_progress"]:
            exchange(events, "Mark Johnson", contact["request"]["content"], contact["reply"]["content"])
            self.assertEqual(reference_released(case, events), {"h1"})
        result = progress(case, events, scorer())
        self.assertIn("credit_percent", result["field_conflicts_or_ambiguity"]["h1"])
        h1 = [p for p in result["proof"] if p["node_id"] == "h1"]
        self.assertEqual(h1[-1]["field_sources"]["credit_percent"], events[1]["message_id"])
        self.assertFalse(any(p["node_id"] == "h2" for p in result["proof"]))

    def test_wrong_only_or_wrong_scope_reply_never_supplies_missing_facts(self):
        case = load_case("m-low-ledger-allocation")
        for reply in ("For INV-842: cost_center: CC-628; ledger_period: 2026-11.",
                      "Cost center: CC-410. Ledger period: 2026-11."):
            events = []
            exchange(events, "David Wong", "INV-841 2026-11?", reply)
            self.assertEqual(reference_released(case, events), set())
            self.assertTrue(progress(case, events, scorer())["field_conflicts_or_ambiguity"])

    def test_issued_reference_roles_use_same_grant_lifecycle(self):
        examples = [
            ("m-high-service-cutover", "readiness_reference"),
            ("m-medium-research-purchase", "release_reference"),
            ("m-high-incident-postmortem", "publication_reference"),
            ("m-high-incident-postmortem", "root_cause_code"),
            ("m-high-payroll-correction", "hr_verification_id"),
            ("m-high-price-change", "margin_check_id"),
        ]
        for tid, key in examples:
            case = load_case(tid)
            hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
            preceding = []
            for node in case.blueprint["gold_dag"]["nodes"]:
                records = [hidden[h] for h in node["information_ids"]]
                request = " ".join(str(c) for h in records for c in h["required_context"])
                facts = {k: v for h in records for k, v in h["facts"].items()}
                person = node["admissible_recipients"][0]
                if key in facts:
                    break
                exchange(preceding, person, request,
                         "\n".join(k + ": " + json.dumps(v) for k, v in facts.items()))
            else:
                self.fail("Missing source-spec grant role: " + key)
            self.assertTrue(set(node["requires"]) <= reference_released(case, preceding))
            value = facts[key]
            grant = f"I approve this request. {key}: {value}"
            scenarios = [
                ("if", f"If approved, {key}: {value}"),
                ("once", f"Once approved, use reference {value}"),
                ("revoked", f"The previous approval {value} is revoked."),
                ("not_authorized", f"The previous approval {value} is not authorized."),
            ]
            for kind, reply in scenarios:
                with self.subTest(field=key, scenario=kind):
                    events = deepcopy(preceding)
                    if kind in {"revoked", "not_authorized"}:
                        exchange(events, person, request, grant)
                        self.assertIn(node["id"], reference_released(case, events))
                    exchange(events, person, request, reply)
                    self.assertNotIn(node["id"], progress(case, events, scorer())["released"])
                    exchange(events, person, request, grant)
                    self.assertIn(node["id"], reference_released(case, events))
                    exchange(events, person, request, f"Approval {value} has not been revoked.")
                    self.assertIn(node["id"], reference_released(case, events))

    def requisition_context(self):
        events = []
        exchange(events, "Huang Jie", "R-77?", "Confirmed level L5 and salary band B5 for R-77.")
        return load_case("m-med-hiring-requisition"), events

    def test_conditional_authorization_is_not_an_actual_grant(self):
        replies = [
            "If approved, authorization_ref: REQ-APR-310",
            "Once approved, use reference REQ-APR-310",
            "If approved:\nauthorization_ref: REQ-APR-310",
            "Once approved:\nuse reference REQ-APR-310",
        ]
        for reply in replies:
            with self.subTest(reply=reply):
                case, events = self.requisition_context()
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.", reply)
                self.assertNotIn("h2", progress(case, events, scorer())["released"])

    def test_explicit_same_scope_revocation_removes_a_previous_grant(self):
        for ending in ("is revoked", "is not authorized"):
            with self.subTest(ending=ending):
                case, events = self.requisition_context()
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                         "Approved. Authorization reference: REQ-APR-310.")
                self.assertIn("h2", reference_released(case, events))
                exchange(events, "Sarah Johnson", "What is the status of REQ-APR-310?",
                         "The previous approval REQ-APR-310 " + ending + ".")
                result = progress(case, events, scorer())
                self.assertEqual(reference_released(case, events), {"h1"})
                self.assertEqual(result["withdrawals"][0]["previous_reply_message_id"],
                                 events[3]["message_id"])
                self.assertEqual(result["withdrawals"][0]["reply_message_id"],
                                 events[-1]["message_id"])
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                         "I approve this requisition. Authorization reference: REQ-APR-310.")
                self.assertEqual(reference_released(case, events), {"h1", "h2"})

    def test_quote_or_historical_record_is_not_a_current_grant_or_revocation(self):
        replies = [
            "Your note quotes:\nThe previous approval REQ-APR-310 is revoked.",
            "Historical record: approval REQ-APR-310 was revoked last year.",
        ]
        for reply in replies:
            with self.subTest(reply=reply):
                case, events = self.requisition_context()
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.", reply)
                self.assertNotIn("h2", progress(case, events, scorer())["released"])
                case, events = self.requisition_context()
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                         "Approved. Authorization reference: REQ-APR-310.")
                exchange(events, "Sarah Johnson", "Please confirm L5 B5 approval status.", reply)
                self.assertIn("h2", progress(case, events, scorer())["released"])

    def test_unrelated_authority_refusal_does_not_veto_current_explicit_grant(self):
        case, events = self.requisition_context()
        exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                 "I cannot approve the unrelated equipment purchase.\n"
                 "I approve this requisition. Authorization reference: REQ-APR-310.")
        self.assertIn("h2", reference_released(case, events))

    def test_negated_or_unconfirmed_revocation_does_not_retract_a_grant(self):
        for reply in ("Approval REQ-APR-310 has not been revoked.",
                      "I cannot confirm whether approval REQ-APR-310 is revoked."):
            with self.subTest(reply=reply):
                case, events = self.requisition_context()
                exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                         "Approved. Authorization reference: REQ-APR-310.")
                exchange(events, "Sarah Johnson", "What is the status of REQ-APR-310?", reply)
                self.assertIn("h2", reference_released(case, events))
                self.assertEqual(progress(case, events, scorer())["withdrawals"], [])

    def test_ledger_current_invoice_mapping_does_not_require_register_date(self):
        case = load_case("m-low-ledger-allocation")
        events = []
        exchange(events, "David Wong", "November allocation for INV-841?",
                 "For INV-841, use cost_center CC-628 and ledger_period 2026-11.")
        self.assertEqual(reference_released(case, events), {"mapping"})
        self.assertEqual(contracts(case)["mapping"].qualifiers, ("effective_date",))
        bad = deepcopy(events)
        bad[-1]["content"] = "For another invoice, cost_center: CC-410."
        self.assertEqual(reference_released(case, bad), set())

    def test_backup_requires_actual_retention_and_storage_not_maintenance_recitation(self):
        case = load_case("o-med-backup-window")
        events = []
        exchange(events, "Li Ming", "JanusGraph backup details?",
                 "Backup window: 03:00 UTC\nRetention: 14 days\nEstimated storage: 6 TB")
        self.assertEqual(reference_released(case, events), {"h1"})
        events[-1]["content"] = "Backup window: 03:00 UTC\nRetention: 14 days"
        self.assertEqual(reference_released(case, events), set())

    def test_metadata_needed_by_a_later_authorization_remains_obligatory(self):
        case = deepcopy(load_case("m-low-ledger-allocation"))
        case.blueprint["hidden_information"].append({
            "id": "future", "facts": {"authorization_ref": "SAFE-FIXTURE-ONLY"},
            "required_context": ["2026-11-01"], "release_rule": "Approve with the effective date cited."})
        case.blueprint["gold_dag"]["nodes"].append({
            "id": "later", "information_ids": ["future"], "requires": ["mapping"],
            "admissible_recipients": ["David Wong"]})
        self.assertNotIn("effective_date", contracts(case)["mapping"].qualifiers)

    def test_split_replies_unrelated_refusal_and_real_refusal(self):
        case = load_case("m-med-hiring-requisition")
        events = []
        exchange(events, "Huang Jie", "R-77 level?", "For R-77, the confirmed level is L5.")
        self.assertEqual(reference_released(case, events), set())
        exchange(events, "Huang Jie", "R-77 salary band?",
                 "The salary band for R-77 is B5. I cannot approve the separate requisition.")
        self.assertEqual(reference_released(case, events), {"h1"})
        events[-1]["content"] = "I cannot confirm salary band B5 for R-77."
        self.assertEqual(reference_released(case, events), set())

    def test_persisted_actual_first_replies_complete_ledger_and_backup_nodes(self):
        from pathlib import Path
        path = Path(__file__).parent / "reports" / "REFERENCE_CONTRACT_AUDIT_20261112.json"
        audit = json.loads(path.read_text(encoding="utf-8"))
        for actual in audit["actual_counterexamples"]:
            case = load_case(actual["slot"]["task_id"])
            evidence = actual["selected_actual_evidence"][0]
            events = []
            exchange(events, evidence["person_id"], evidence["request"], evidence["reply"])
            self.assertEqual(reference_released(case, events),
                             {n["id"] for n in actual["gold_dag"]["nodes"]})

    def test_decimal_rate_is_not_percentage_and_partial_quote_is_not_invented(self):
        case = load_case("o-med-brochure-translation")
        events = []
        exchange(events, "Jessica Lee", "LinguaPro rate?", "Framework rate: USD 0.08 per word.")
        self.assertEqual(reference_released(case, events), {"h1"})
        self.assertTrue(progress(case, events, scorer())["proof"][0]["field_sources"]["total_usd"].startswith(
            "public-derivation:"))
        self.assertEqual(next(iter(progress(case, events, scorer())[
            "public_derivation_proofs_PRIVATE"].values()))["derived_value"], "960.00")
        events[-1]["content"] = "Framework rate: 8%."
        self.assertEqual(reference_released(case, events), set())
        self.assertTrue(progress(case, events, scorer())["field_conflicts_or_ambiguity"])

    def test_numeric_punctuation_and_unrelated_authority_limits_preserve_actual_facts(self):
        examples = [
            ("m-med-support-renewal", "Alex Turner", "Node-RED renewal?",
             "For Node-RED, the current seat count needed is **26**.\n"
             "I can't confirm the signer or authorization reference."),
            ("m-med-campaign-spend", "Jessica Lee", "Q4 webinar spend?",
             "I can confirm the approved campaign spend is **USD 7,300**.\n"
             "I can't provide the signed_by name or authorization_ref."),
        ]
        for tid, person, question, reply in examples:
            events = []
            exchange(events, person, question, reply)
            self.assertEqual(reference_released(load_case(tid), events), {"h1"})

    def test_authorization_requires_preceding_facts_context_and_actual_release(self):
        case = load_case("m-med-hiring-requisition")
        events = []
        exchange(events, "Sarah Johnson", "Please approve L5 B5.",
                 "Approved. Authorization reference: REQ-APR-310.")
        self.assertEqual(reference_released(case, events), set())
        exchange(events, "Huang Jie", "R-77?", "Confirmed level L5 and salary band B5 for R-77.")
        exchange(events, "Sarah Johnson", "Please approve L5.", "Approval reference: REQ-APR-310.")
        self.assertEqual(reference_released(case, events), {"h1"})
        exchange(events, "Sarah Johnson", "Please approve L5 and B5.",
                 "I cannot approve this. Your draft approval reference is REQ-APR-310.")
        self.assertEqual(reference_released(case, events), {"h1"})
        clean = events[:-2]
        exchange(clean, "Sarah Johnson", "Please approve L5 and B5.",
                 "That satisfies the context. The approval reference to use is:\nREQ-APR-310")
        self.assertEqual(reference_released(case, clean), {"h1", "h2"})

    def test_numeric_value_in_wrong_field_is_not_certification_and_conflicts_are_diagnostics(self):
        case = load_case("o-high-interview-panel")
        events = []
        exchange(events, "Chen Xinyi", "backend interviewers?",
                 "Panel size: 4. I cannot confirm the certified interviewer count.")
        self.assertEqual(reference_released(case, events), set())
        case = load_case("m-low-ledger-allocation")
        events = []
        exchange(events, "David Wong", "INV-841 2026-11?", "Cost center: CC-628.")
        exchange(events, "David Wong", "INV-841 2026-11?", "Cost center: CC-410.")
        self.assertEqual(reference_released(case, events), {"mapping"})
        self.assertIn("cost_center", progress(case, events, scorer())[
            "field_conflicts_or_ambiguity"]["mapping"])
        exchange(events, "David Wong", "INV-841 2026-11?", "Ledger period: 2026-11.")
        self.assertEqual(reference_released(case, events), {"mapping"})

    def test_multiline_draft_echo_does_not_release_a_fact(self):
        events = []
        exchange(events, "Alex Turner", "Node-RED renewal?",
                 "Your draft says:\nseats: 26")
        self.assertEqual(reference_released(load_case("m-med-support-renewal"), events), set())

    def test_all60_contracts_have_sources_and_ordered_canonical_releases(self):
        for tid in task_ids():
            with self.subTest(task=tid):
                case = load_case(tid)
                specs = contracts(case)
                hidden = {h["id"]: h for h in case.blueprint["hidden_information"]}
                events = []
                for node in case.blueprint["gold_dag"]["nodes"]:
                    records = [hidden[h] for h in node["information_ids"]]
                    request = " ".join(str(c) for h in records for c in h["required_context"])
                    reply = "\n".join(k + ": " + json.dumps(v)
                                      for h in records for k, v in h["facts"].items())
                    exchange(events, node["admissible_recipients"][0], request, reply)
                    self.assertTrue(specs[node["id"]].explanation)
                self.assertEqual(reference_released(case, events), set(specs))


if __name__ == "__main__":
    unittest.main()
