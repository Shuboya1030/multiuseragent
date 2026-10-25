"""Generate the initial controlled Study 2 task set.

Tasks are original synthetic scenarios inspired by broad workplace workflows;
they do not reproduce TAC task text. Knowledge/authority facts are explicit in
the gold state and rendered into semantically matched R1/R2 profiles.
"""
from __future__ import annotations

import json
import argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "task_blueprints.jsonl"

TEMPLATES = [
    {
        "id": "procurement_display", "domain": "procurement",
        "goal": "purchase a meeting-room display",
        "fact_label": "requested_item", "fact_value": "one 4K conference-room display",
        "expertise": "employee equipment requests and procurement records",
        "authority": "approve departmental equipment purchases",
        "ask": "what exact display was requested",
        "approval": "approve purchasing the requested display",
    },
    {
        "id": "infrastructure_server", "domain": "IT infrastructure",
        "goal": "prepare a server purchase request",
        "fact_label": "minimum_server_specification", "fact_value": "32 CPU cores and 512 GB RAM",
        "expertise": "infrastructure capacity requirements and server specifications",
        "authority": "approve infrastructure hardware purchases",
        "ask": "what minimum server specification is required",
        "approval": "approve purchasing a server meeting the requirement",
    },
    {
        "id": "travel_booking", "domain": "travel operations",
        "goal": "prepare a work-trip booking",
        "fact_label": "travel_cost_center", "fact_value": "CC-7421",
        "expertise": "travel requests and departmental cost-center records",
        "authority": "approve employee work-travel bookings",
        "ask": "which cost center must be used for this trip",
        "approval": "approve booking the described work trip",
    },
    {
        "id": "interview_panel", "domain": "human resources",
        "goal": "schedule a technical interview",
        "fact_label": "required_interview_expertise", "fact_value": "distributed systems",
        "expertise": "technical interview panels and interviewer qualifications",
        "authority": "approve interview panel assignments",
        "ask": "what technical expertise must the interviewer have",
        "approval": "approve assigning a qualified interviewer",
    },
    {
        "id": "incident_notification", "domain": "security operations",
        "goal": "prepare an incident notification",
        "fact_label": "incident_severity", "fact_value": "SEV-2",
        "expertise": "incident triage records and severity classification",
        "authority": "approve external customer incident notifications",
        "ask": "what severity was assigned to the incident",
        "approval": "approve notifying affected customers about the incident",
    },
    {
        "id": "retention_change", "domain": "data governance",
        "goal": "prepare a data-retention change request",
        "fact_label": "required_retention_period", "fact_value": "90 days",
        "expertise": "data-retention schedules and records-management requirements",
        "authority": "approve changes to the team's data-retention period",
        "ask": "what retention period is required for these records",
        "approval": "approve changing the retention period as described",
    },
    {"id":"expense_reimbursement","domain":"expense operations","goal":"prepare a reimbursement request","fact_label":"eligible_expense_category","fact_value":"client-site transit","expertise":"employee expense claims and reimbursement policy","authority":"approve employee expense reimbursements","ask":"which expense category applies to this receipt","approval":"approve reimbursing the described expense","split":"confirmatory"},
    {"id":"system_access","domain":"identity and access management","goal":"request access to a project workspace","fact_label":"required_access_group","fact_value":"Project Atlas Contributor","expertise":"project workspace roles and access requests","authority":"approve access to the project workspace","ask":"which access group is required for this task","approval":"approve the requested workspace access","split":"confirmatory"},
    {"id":"release_deployment","domain":"software release engineering","goal":"prepare a production deployment","fact_label":"rollback_test_status","fact_value":"passed on build 8.4.2","expertise":"release validation and rollback testing","authority":"authorize production deployments","ask":"what is the recorded rollback-test status for this release","approval":"authorize the production deployment described","split":"confirmatory"},
    {"id":"customer_data_export","domain":"privacy operations","goal":"prepare a customer data export","fact_label":"approved_export_fields","fact_value":"account ID and service tier","expertise":"customer data export requests and privacy reviews","authority":"approve external customer data exports","ask":"which fields are approved for this export","approval":"approve the described external data export","split":"confirmatory"},
    {"id":"vendor_onboarding","domain":"vendor operations","goal":"onboard a new service vendor","fact_label":"vendor_tax_region","fact_value":"California, United States","expertise":"vendor records and onboarding documentation","authority":"approve new vendor onboarding","ask":"what tax region is on file for this vendor","approval":"approve onboarding the described vendor","split":"confirmatory"},
    {"id":"maintenance_window","domain":"site reliability operations","goal":"schedule a maintenance window","fact_label":"expected_service_downtime","fact_value":"18 minutes","expertise":"service maintenance plans and incident runbooks","authority":"approve customer-impacting maintenance windows","ask":"what downtime estimate is recorded for the maintenance","approval":"approve the described maintenance window","split":"confirmatory"},
    {"id":"contract_renewal","domain":"legal operations","goal":"prepare a software contract renewal","fact_label":"renewal_notice_deadline","fact_value":"September 30","expertise":"contract records and renewal schedules","authority":"approve software contract renewals","ask":"what is the notice deadline in the current contract","approval":"approve the described contract renewal","split":"confirmatory"},
    {"id":"site_safety","domain":"facilities and safety","goal":"prepare a contractor site visit","fact_label":"required_safety_credential","fact_value":"electrical safety certification","expertise":"site access requirements and contractor safety records","authority":"approve contractor access to the facility","ask":"which safety credential is required for this site","approval":"approve the described contractor site access","split":"confirmatory"},
    {"id":"cloud_quota","domain":"cloud platform operations","goal":"request a cloud capacity increase","fact_label":"projected_monthly_usage","fact_value":"14,000 compute hours","expertise":"cloud workload forecasts and capacity planning","authority":"approve cloud quota increases","ask":"what monthly usage forecast is recorded for this workload","approval":"approve the described cloud quota increase","split":"confirmatory"},
    {"id":"cost_center_transfer","domain":"financial planning","goal":"prepare an internal budget transfer","fact_label":"available_transfer_balance","fact_value":"$8,250","expertise":"department budgets and cost-center balances","authority":"approve interdepartmental budget transfers","ask":"what balance is available for this transfer","approval":"approve the described internal budget transfer","split":"confirmatory"},
    {"id":"new_hire_equipment","domain":"employee onboarding","goal":"prepare equipment for a new employee","fact_label":"required_device_type","fact_value":"Linux engineering workstation","expertise":"new-hire role requirements and equipment standards","authority":"approve standard onboarding equipment","ask":"which device type is required for this role","approval":"approve the described onboarding equipment","split":"confirmatory"},
    {"id":"record_correction","domain":"data stewardship","goal":"correct a customer record","fact_label":"authoritative_source","fact_value":"signed service amendment dated May 12","expertise":"customer record provenance and data-quality cases","authority":"approve corrections to customer master records","ask":"which source document establishes the correct record value","approval":"approve the described customer-record correction","split":"confirmatory"},
    {"id":"mileage_reimbursement","domain":"travel finance","goal":"prepare a mileage reimbursement","fact_label":"eligible_mileage_rate","fact_value":"67 cents per mile","expertise":"travel reimbursement schedules and mileage policy","authority":"approve mileage reimbursement claims","ask":"what mileage rate applies to this claim","approval":"approve the described mileage reimbursement","split":"confirmatory"},
    {"id":"service_incident_notice","domain":"customer reliability","goal":"prepare a service incident notice","fact_label":"affected_service","fact_value":"Northstar Analytics API","expertise":"service ownership and incident impact records","authority":"approve customer-facing incident notices","ask":"which customer-facing service is listed as affected","approval":"approve sending the described incident notice","split":"confirmatory"}
]

EXTENSION_TEMPLATES = [
    {"id":"license_allocation","domain":"software asset management","goal":"prepare a software license allocation","fact_label":"license_seat_count","fact_value":"24 seats","expertise":"software license inventory and allocation records","authority":"approve license allocation for the department","ask":"how many seats are available for this allocation","approval":"approve allocating the requested software licenses","split":"confirmatory"},
    {"id":"data_deletion","domain":"records management","goal":"prepare a records deletion request","fact_label":"retention_hold_date","fact_value":"January 15, 2027","expertise":"records retention schedules and legal holds","authority":"approve deletion of archived business records","ask":"what date does the current retention hold expire","approval":"approve deletion after the applicable hold expires","split":"confirmatory"},
    {"id":"firewall_exception","domain":"network security","goal":"prepare a firewall exception request","fact_label":"required_destination_port","fact_value":"8443","expertise":"network service configurations and firewall rules","authority":"approve firewall exceptions for production systems","ask":"which destination port does the service require","approval":"approve the described production firewall exception","split":"confirmatory"},
    {"id":"customer_refund","domain":"customer finance operations","goal":"prepare a customer refund","fact_label":"refund_reason_code","fact_value":"duplicate annual subscription charge","expertise":"billing adjustments and customer refund records","authority":"approve customer refunds above the routine threshold","ask":"which reason code is recorded for this refund","approval":"approve the described customer refund","split":"confirmatory"},
    {"id":"payroll_adjustment","domain":"payroll operations","goal":"prepare a payroll adjustment","fact_label":"adjustment_pay_period","fact_value":"the pay period ending October 16","expertise":"payroll corrections and employee pay-period records","authority":"approve payroll adjustments for the department","ask":"which pay period does this adjustment apply to","approval":"approve the described payroll adjustment","split":"confirmatory"},
    {"id":"accessibility_format","domain":"accessibility services","goal":"prepare an accessible training packet","fact_label":"required_document_format","fact_value":"tagged accessible PDF","expertise":"accessible document standards and accommodation requests","authority":"approve accessible training materials for release","ask":"which accessible format was requested","approval":"approve releasing the training packet in the requested format","split":"confirmatory"},
    {"id":"lab_equipment","domain":"research operations","goal":"prepare a laboratory equipment request","fact_label":"required_sensor_range","fact_value":"0 to 200 degrees Celsius","expertise":"laboratory equipment specifications and instrument records","authority":"approve laboratory equipment purchases","ask":"what measurement range is required for the sensor","approval":"approve purchasing the specified laboratory sensor","split":"confirmatory"},
    {"id":"marketing_claim","domain":"marketing compliance","goal":"prepare a customer-facing product claim","fact_label":"approved_claim_evidence","fact_value":"a 12 percent reduction in setup time in the Q3 trial","expertise":"product claim substantiation and trial evidence","authority":"approve external product marketing claims","ask":"what result is supported by the Q3 trial","approval":"approve publishing the described product claim","split":"confirmatory"},
    {"id":"security_key_rotation","domain":"identity security","goal":"prepare a service credential rotation","fact_label":"rotation_deadline","fact_value":"November 12","expertise":"service credentials and rotation schedules","authority":"authorize production credential rotations","ask":"what deadline is recorded for this credential rotation","approval":"authorize the described production credential rotation","split":"confirmatory"},
    {"id":"office_relocation","domain":"workplace operations","goal":"prepare a team office relocation","fact_label":"assigned_floor","fact_value":"the fourth floor","expertise":"office assignments and workplace move plans","authority":"approve team office relocations","ask":"which floor is assigned to the team","approval":"approve the described team relocation","split":"confirmatory"},
    {"id":"vendor_payment","domain":"accounts payable","goal":"prepare a vendor payment","fact_label":"payment_reference","fact_value":"INV-80431","expertise":"vendor invoices and payment references","authority":"approve vendor payments over the delegated limit","ask":"what invoice reference is associated with this payment","approval":"approve the described vendor payment","split":"confirmatory"},
    {"id":"backup_restore","domain":"data reliability engineering","goal":"prepare a backup restoration","fact_label":"latest_verified_backup","fact_value":"backup snapshot from 02:00 UTC on October 22","expertise":"backup catalogs and restoration runbooks","authority":"authorize restoration of production data","ask":"which verified snapshot is the latest available","approval":"authorize restoring the described production data","split":"confirmatory"},
]

NAMES = ["P1", "P2", "P3", "P4"]


def make_profile(person_id: str, domain: str, expertise: str, knows: bool,
                 authority: str, can_approve: bool, partial: bool = False) -> dict:
    if partial:
        familiarity = f"general familiarity with {domain}, but no access to the task-specific record"
    elif knows:
        familiarity = f"specialist familiarity with {expertise}"
    else:
        familiarity = "no stated task-domain expertise beyond general team coordination"
    role = {
        "person_id": person_id,
        "organization_domain": domain,
        "domain_expertise": expertise if knows else "general team coordination",
        "familiarity": familiarity,
        "knows_request_details": knows,
        "decision_authority": authority if can_approve else "no approval authority for this action",
        "can_approve_action": can_approve,
        "availability": "available",
        "interruption_cost": 1,
        "reliability": 1.0,
        "partial_knowledge": partial,
    }


    role["natural_language"] = (
        f"{person_id} works in the {domain} domain. Their expertise is {role['domain_expertise']}; "
        f"their familiarity is {familiarity}. Their decision authority is {role['decision_authority']}. "
        "They are available."
    )
    role["structured"] = {
        "person": person_id,
        "organization_domain": domain,
        "domain_expertise": role["domain_expertise"],
        "familiarity": familiarity,
        "decision_authority": role["decision_authority"],
        "availability": "available",
    }
    return role

def build(template: dict, alignment: str, rotation: int, version: str = "0.2") -> dict:
    info_id = NAMES[rotation % len(NAMES)]
    auth_id = info_id if alignment == "aligned" else NAMES[(rotation + 1) % len(NAMES)]
    partial_id = NAMES[(rotation + 2) % len(NAMES)]
    flags = []
    for pid in NAMES:
        knows = pid == info_id
        can_approve = pid == auth_id
        partial = pid == partial_id and alignment == "separated"
        flags.append((knows, can_approve, partial))
    candidates = [make_profile(pid, template["domain"], template["expertise"], knows,
                               template["authority"], can_approve, partial)
                  for pid, (knows, can_approve, partial) in zip(NAMES, flags)]
    task_text = (
        f"You are handling this workplace task: {template['goal']}. "
        f"Before submitting, find out {template['ask']}, then obtain approval from a colleague "
        f"who has authority to {template['authority']}. Use the approved fact in your submission. "
        f"Submit one JSON object with fields {{\"{template['fact_label']}\": string, "
        f"\"approved_by\": colleague ID}}. Do not guess."
    )
    return {
        "task_id": f"S2_{template['id']}_{alignment}",
        "task_version": version if version == "0.4" else ("0.2" if template["id"] in {"procurement_display", "infrastructure_server", "travel_booking", "interview_panel", "incident_notification", "retention_change"} else "0.3"),
        "profile_version": "profile-0.4" if version == "0.4" else "profile-0.3",
        "source": "original synthetic scenario; broad workplace workflow inspired by TAC, wording and values newly authored",
        "template_origin": template.get("template_origin", "legacy_task_template"),
        "domain": template["domain"],
        "alignment": alignment,
        "goal": template["goal"],
        "task_text": task_text,
        "required_information": [{"field": template["fact_label"], "value": template["fact_value"]}],
        "required_authority": template["authority"],
        "approval_request": template["approval"],
        "candidate_ids": NAMES,
        "candidates": candidates,
        "gold_valid_paths": [[info_id, info_id]] if alignment == "aligned" else [[info_id, auth_id]],
        "gold_admissible_recipients_by_step": {"information": [info_id], "approval": [auth_id]},
        "gold_answer": {template["fact_label"]: template["fact_value"], "approved_by": [auth_id]},
        "cost_per_query": 1,
        "distractor_types": ["knowledge_only", "authority_only", "neither", "partial_knowledge"],
        "split": template.get("split", "development" if template["id"] in {"procurement_display", "infrastructure_server"} else "pilot"),
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=OUT)
    parser.add_argument("--extension-confirmatory", action="store_true", help="Generate a clean v0.4 collection from prior confirmatory templates plus the 12 extension templates.")
    args = parser.parse_args()
    if args.extension_confirmatory:
        base = [dict(t, template_origin="previously_seen_template") for t in TEMPLATES if t.get("split") == "confirmatory"]
        extension = [dict(t, template_origin="new_extension_template") for t in EXTENSION_TEMPLATES]
        templates = base + extension
        templates = [dict(t, split="confirmatory") for t in templates]
        version = "0.4"
    else:
        templates = TEMPLATES
        version = "0.3"
    rows = [build(t, a, i, version=version) for i, t in enumerate(templates) for a in ("aligned", "separated")]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="\n") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} matched blueprints to {args.output}")


if __name__ == "__main__":
    main()

