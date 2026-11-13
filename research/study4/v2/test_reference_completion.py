"""Zero-API completion and equivalence prerequisites, not new model outcomes."""
from copy import deepcopy
import json
import unittest

from .phase0 import load_case, reference_released, scorer, task_ids
from .reference_completion import contracts, progress, ReferenceUncertain


def exchange(events, person, request, reply):
    mid = "fixture:" + str(len(events))
    events.extend([
        {"kind": "send_message", "person_id": person, "message_id": mid, "content": request},
        {"kind": "read_messages", "person_id": person, "message_id": mid + ":reply",
         "in_reply_to": mid, "content": reply},
    ])


class ReferenceCompletionTests(unittest.TestCase):
    def test_issued_reference_roles_use_same_grant_lifecycle(self):
        examples = [
            ("m-high-service-cutover", "readiness_reference"),
            ("m-medium-research-purchase", "release_reference"),
            ("m-high-incident-postmortem", "publication_reference"),
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
        self.assertNotIn("total_usd", progress(case, events, scorer())["proof"][0]["field_sources"])
        events[-1]["content"] = "Framework rate: 8%."
        with self.assertRaises(ReferenceUncertain):
            reference_released(case, events)

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

    def test_numeric_value_in_wrong_field_is_not_certification_and_conflicts_stop(self):
        case = load_case("o-high-interview-panel")
        events = []
        exchange(events, "Chen Xinyi", "backend interviewers?",
                 "Panel size: 4. I cannot confirm the certified interviewer count.")
        self.assertEqual(reference_released(case, events), set())
        case = load_case("m-low-ledger-allocation")
        events = []
        exchange(events, "David Wong", "INV-841 2026-11?", "Cost center: CC-628.")
        exchange(events, "David Wong", "INV-841 2026-11?", "Cost center: CC-410.")
        with self.assertRaises(ReferenceUncertain):
            reference_released(case, events)

    def test_multiline_draft_echo_does_not_release_a_fact(self):
        events = []
        exchange(events, "Alex Turner", "Node-RED renewal?",
                 "Your draft says:\nseats: 26")
        with self.assertRaises(ReferenceUncertain):
            reference_released(load_case("m-med-support-renewal"), events)

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
