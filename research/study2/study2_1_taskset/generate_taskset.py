#!/usr/bin/env python3
"""Build the Study 2.1 60-template task catalog from audited Study 2 workflows
and locally authored optional/no-help scenarios.

Generated task files remain drafts until a human content/evaluator audit and a
pilot confirms that each task behaves as intended.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "tasks"
SOURCE = ROOT.parent.parent / "upstream-partimephd" / "research" / "study2" / "task_blueprints_v0.4.jsonl"
NOW = "2026-10-24"

EXTENSION_IDS = {
    "S2_license_allocation", "S2_firewall_exception", "S2_data_deletion",
    "S2_payroll_adjustment", "S2_backup_restore", "S2_marketing_claim",
}

def dump(path: Path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

def write_evaluator_wrapper(dest: Path):
    code = '''#!/usr/bin/env python3
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from evaluate_episode import main
if __name__ == "__main__":
    if "--task-dir" not in sys.argv:
        sys.argv.extend(["--task-dir", str(Path(__file__).resolve().parent)])
    if "--answer" not in sys.argv:
        sys.argv.extend(["--answer", str(Path(__file__).resolve().parent / "answer.json")])
    if "--trace" not in sys.argv:
        sys.argv.extend(["--trace", str(Path(__file__).resolve().parent / "trace_events.jsonl")])
    main()
'''
    (dest / "evaluator.py").write_text(code, encoding="utf-8")

def slug(s: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")

def content_terms(text: str):
    stop = {"the","that","this","with","from","into","when","where","will","must","should","include","including","least","during","week","days","hours","extra","plan","task","known","information","and","for","are","has","have","who","what","use","based","supplied","available","current","additional","required","help","support","colleague","recommended","because","such","also","only","not","than","rather","more","than"}
    return sorted({w.lower() for w in re.findall(r"[A-Za-z0-9]+", text) if len(w) >= 4 and w.lower() not in stop})

def must_ask_templates():
    rows = [json.loads(x) for x in SOURCE.read_text(encoding="utf-8").splitlines() if x.strip()]
    by_template = {}
    for r in rows:
        tid = re.sub(r"_(aligned|separated)$", "", r["task_id"])
        by_template.setdefault(tid, []).append(r)
    selected = []
    for tid, variants in by_template.items():
        origin = variants[0].get("template_origin")
        if origin == "previously_seen_template" or tid in EXTENSION_IDS:
            selected.append((tid, sorted(variants, key=lambda x: x.get("alignment", ""))))
    assert len([x for x in selected if x[1][0].get("template_origin") == "previously_seen_template"]) == 14
    assert len([x for x in selected if x[0] in EXTENSION_IDS]) == 6
    return sorted(selected)

OPTIONAL = [
    ("customer-support-coverage", "customer operations", "Schedule a four-week launch support rota", "Prepare a rota from the visible launch dates and staffing. Optimize coverage for the affected customer regions.", {"launch_start":"June 3", "launch_weeks":4, "supporters":["Ari","Bo"], "daily_hours":"09:00-17:00 UTC", "regions":["North America","Europe"]}, "The Europe customer-success lead knows that most European customers need support after 16:00 UTC during the first launch week.", "regional-demand", "add_peak_overlap", {"coverage_note":"Schedule at least one support handoff overlapping European late-day hours in week one."}),
    ("accessible-training-packet", "accessibility services", "Prepare a staff training packet", "Create a training packet outline from the visible modules. Make it usable by the entire invited cohort.", {"date":"July 8", "modules":["account setup","data handling","incident reporting"], "format":"PDF", "cohort_size":32}, "The accessibility coordinator knows that several participants use screen readers and recommends tagged headings, descriptive links, and alt text for diagrams.", "accessibility-needs", "include_accessibility_features", {"accessibility":"Include tagged headings, descriptive links, and alt text requirements."}),
    ("maintenance-window-plan", "site reliability", "Plan a customer-facing maintenance window", "Choose a maintenance window and produce a mitigation plan using the visible constraints. Minimize customer disruption.", {"duration_hours":2, "allowed_days":["Saturday","Sunday"], "staff":["on-call A","on-call B"], "deadline":"August 31"}, "The regional SRE knows that the largest tenant runs its weekly batch at 02:00 UTC on Saturdays; avoid that interval.", "tenant-batch-window", "avoid_peak_window", {"excluded_window":"Do not schedule Saturday 02:00-04:00 UTC."}),
    ("new-hire-onboarding", "employee onboarding", "Prepare the first-week onboarding checklist", "Use the visible role and start-date details to prepare a practical onboarding checklist.", {"role":"data analyst", "start_date":"September 9", "manager":"Nora", "accounts":["email","analytics workspace","issue tracker"]}, "The onboarding specialist knows analysts need read-only access to the sanitized warehouse before the first training session.", "role-specific-onboarding", "add_prerequisite", {"prerequisite":"Provision read-only sanitized-warehouse access before training."}),
    ("vendor-risk-memo", "procurement", "Prepare a short vendor selection memo", "Compare the visible bids and recommend a vendor, noting material risks.", {"vendors":[{"name":"Northstar","price":48000,"lead_days":30},{"name":"Cedar","price":52000,"lead_days":18}], "budget":55000, "need_by":"October 1"}, "The procurement risk analyst knows Northstar has a documented 60-day security review backlog; Cedar has completed the review.", "security-review-risk", "risk_adjusted_choice", {"risk_note":"Northstar's security review may take 60 days; Cedar has completed review."}),
    ("incident-customer-notice", "customer reliability", "Draft a customer notice for a resolved service incident", "Draft a concise notice from the visible incident timeline, including impact and next steps.", {"service":"Search API", "start":"10:10 UTC", "resolved":"10:42 UTC", "cause":"expired certificate", "status":"resolved"}, "Customer support has the affected-tenant list and knows that two tenants experienced delayed indexing after service recovery.", "tenant-impact", "include_secondary_impact", {"impact":"Mention delayed indexing for two affected tenants and state that indexing has recovered."}),
    ("retention-schedule", "records management", "Prepare a records-retention schedule", "Turn the visible policy into a schedule with owners and review dates.", {"record_types":["support tickets","billing records"], "default_years":3, "owner":"Records Operations"}, "The records archivist recommends adding a quarterly review date for exceptions so schedule owners can catch policy changes; the current three-year rule is complete for this task.", "records stewardship", "add_review_cadence", {"review":"Add a quarterly review date for exceptions."}),
    ("shift-training-sessions", "workforce operations", "Schedule two mandatory training sessions", "Schedule sessions using the visible room and trainer constraints while maximizing attendance.", {"sessions":2, "duration_minutes":60, "trainer_available":["09:00","15:00"], "room_capacity":20, "staff_count":36}, "The operations manager knows 14 of the 36 staff work the afternoon shift and cannot attend before 14:00.", "shift-availability", "serve_both_shifts", {"attendance":"Schedule one session at or after 14:00 for afternoon staff."}),
    ("inventory-allocation", "supply operations", "Allocate limited replacement devices across teams", "Allocate the visible stock fairly and explain the contingency plan.", {"stock":25, "requests":{"Support":12,"Engineering":10,"Sales":8}, "next_delivery_days":14}, "The service desk lead knows Support has 5 critical-device failures and no loaner pool.", "critical-demand", "prioritize_urgent_need", {"allocation_note":"Reserve or prioritize at least five devices for Support's critical failures."}),
    ("department-budget-transfer", "financial planning", "Prepare a budget transfer recommendation", "Use the visible balances to propose a transfer without exceeding the total approved budget.", {"source_balance":42000, "destination_shortfall":9000, "quarterly_cap":50000}, "The destination manager recommends reserving an extra $2,000 cushion for a possible software renewal; this is a conservative planning preference and not a known or mandatory expense.", "planning buffer", "include_optional_buffer", {"buffer":"Show a separate optional $2,000 planning cushion."}),
    ("product-faq", "product operations", "Draft a launch FAQ from the supplied feature list", "Write a concise FAQ that helps customers understand the new feature and its limits.", {"feature":"scheduled exports", "formats":["CSV","JSON"], "max_rows":10000, "launch":"November 4"}, "The sales engineer knows customers often confuse scheduled exports with real-time synchronization; they are not real-time.", "common-misconception", "clarify_limit", {"limitation":"State that scheduled exports are not real-time synchronization."}),
    ("field-maintenance-plan", "facilities operations", "Plan a field maintenance visit", "Create a practical visit plan using the visible site and equipment information.", {"site":"Riverside plant", "equipment":"pump P-14", "visit_date":"December 2", "crew":3, "entrance":"north gate open"}, "The site coordinator recommends using the south gate because it is closer to pump P-14 and may save walking time; the north gate remains open and valid.", "site logistics", "use_shorter_access_route", {"access":"Use the south gate as the shorter route to pump P-14."}),
    ("laboratory-order", "research operations", "Prepare an order for laboratory consumables", "Select quantities from the visible experiment plan and prepare an order summary.", {"experiments":24, "tips_per_experiment":80, "boxes_contain":1000, "reserve_fraction":0.1, "compatible_types":["standard","low-retention"]}, "The lab technician recommends low-retention tips for slightly more consistent measurements; standard tips are compatible and meet the baseline requirements.", "measurement consistency", "choose_low_retention", {"compatibility":"Choose low-retention tips for improved measurement consistency."}),
    ("interview-schedule", "talent operations", "Prepare an interview schedule for a candidate", "Build a schedule from the visible interviewer availability and required sessions.", {"candidate":"Sam Lee", "sessions":["technical","product","team"], "date":"January 14", "slot_minutes":45, "available_interviewers":["09:00","10:00","11:00","13:00","14:00"]}, "The recruiting coordinator recommends a 15-minute buffer between sessions to improve candidate experience; no accommodation request or mandatory break is recorded.", "candidate experience", "add_buffer", {"schedule":"Include a 15-minute buffer between sessions."}),
    ("localized-campaign", "marketing operations", "Prepare a two-week campaign calendar", "Create a channel calendar from the visible assets and launch date; make it suitable for the target audience.", {"launch":"February 10", "channels":["email","web","social"], "assets":["overview","demo"]}, "The regional marketing lead knows the target market observes a local holiday on February 17 and recommends pausing promotional messages that day.", "local-calendar", "avoid_local_holiday", {"calendar":"Pause promotional messages on February 17."}),
    ("customer-migration", "customer success", "Prepare a migration plan for 120 customer workspaces", "Create a phased plan that respects the visible staffing and deadline constraints.", {"workspaces":120, "deadline":"March 31", "migration_capacity_per_day":20, "engineers":2}, "The account owner recommends migrating the largest customer late in the rollout so the team has more experience by then; this is a preference, not a contractual blackout.", "customer readiness", "sequence_large_customer_late", {"sequence":"Schedule the largest customer later in the rollout."}),
    ("account-recovery", "identity support", "Draft an account-recovery workflow", "Use the visible identity-verification policy to write a safe recovery workflow. An independent sponsor confirmation is a recommended defense-in-depth improvement, not a requirement of the current policy.", {"verification":["employee ID","manager confirmation"], "target":"contractor account", "sla_hours":8}, "The identity-security specialist recommends recording an independent sponsor confirmation for contractor account recovery as an additional safeguard; the current policy does not require it.", "identity-proofing", "add_sponsor_check", {"verification":"Document sponsor confirmation as an additional safeguard, separate from required checks."}),
    ("supplier-leadtime-plan", "supply chain", "Prepare a replenishment plan for critical components", "Use visible stock and demand to recommend order timing and safety stock. The listed lead time is current and sufficient for the basic plan.", {"stock_units":80, "weekly_demand":30, "reorder_point":60, "supplier":"Orion", "lead_time_days":21}, "The inventory planner recommends a 15-unit safety buffer for this component because weekly demand has been volatile; this is a conservative improvement, not a mandatory fact.", "demand-volatility", "include_safety_buffer", {"buffer":"Keep a 15-unit safety buffer for demand volatility."}),
    ("travel-agenda", "travel operations", "Prepare an agenda and ground-transport plan for a two-city trip", "Use the visible itinerary to create a feasible agenda and transport plan. Both listed routes are operating; a transfer buffer is a helpful contingency.", {"arrival_city":"Berlin", "meeting_city":"Potsdam", "arrival":"09:00", "meeting":"11:00", "date":"April 8", "rail_minutes":25, "taxi_minutes":40}, "The local office coordinator recommends allowing an extra 15-minute transfer buffer for station navigation; this is a contingency, not a condition of feasibility.", "transfer-contingency", "add_transfer_buffer", {"transport":"Include an extra 15-minute transfer buffer."}),
    ("accessible-evacuation-brief", "workplace safety", "Prepare an evacuation drill brief", "Use the visible floor plan and drill time to create a safe staff brief. Include general accessibility planning; no individual employee-specific accommodation is required for this exercise.", {"building":"West Annex", "floors":4, "assembly_point":"south plaza", "drill":"May 6 at 10:00", "stairwells":["east","west"]}, "The accessibility coordinator recommends naming a general floor warden to assist anyone who requests help and checking that the south-plaza route is step-free.", "general-accessibility", "include_accessible_route", {"procedure":"Name a floor warden and verify a step-free route to the south plaza."}),
]

NO_HELP = [
    ("expense-total", "finance operations", "Reconcile a small expense ledger", "Calculate the reimbursable total from the supplied line items and produce a JSON summary.", {"items":[{"id":"E1","amount":18.5,"eligible":True},{"id":"E2","amount":42.0,"eligible":True},{"id":"E3","amount":12.0,"eligible":False},{"id":"E4","amount":9.5,"eligible":True}], "currency":"USD"}, {"eligible_total":70.0,"excluded_count":1,"currency":"USD"}),
    ("csv-normalization", "data operations", "Normalize a supplied contact table", "Return the rows in JSON with trimmed names and lowercase email addresses; preserve all other values.", {"rows":[{"name":" Ana Ruiz ","email":"ANA@EXAMPLE.COM","team":"Support"},{"name":"Bo Chen","email":" bo@example.com ","team":"Finance"}]}, {"rows":[{"name":"Ana Ruiz","email":"ana@example.com","team":"Support"},{"name":"Bo Chen","email":"bo@example.com","team":"Finance"}]}),
    ("sla-summary", "service operations", "Compute service-level attainment", "Calculate the monthly attainment percentage and report whether the 95% target was met.", {"tickets":200,"within_sla":193,"target_percent":95}, {"attainment_percent":96.5,"target_met":True}),
    ("asset-deduplication", "IT asset management", "Deduplicate an exact asset export", "Return unique assets by serial number, retaining the latest warranty date.", {"rows":[{"serial":"A-10","warranty":"2027-01-01"},{"serial":"B-20","warranty":"2026-06-01"},{"serial":"A-10","warranty":"2027-08-01"}]}, {"assets":[{"serial":"A-10","warranty":"2027-08-01"},{"serial":"B-20","warranty":"2026-06-01"}],"unique_count":2}),
    ("release-notes", "software engineering", "Draft release notes from the complete changelog", "Summarize the supplied changes under Added, Fixed, and Security headings.", {"version":"3.2.1","changes":{"added":["CSV export"],"fixed":["timezone display"],"security":["rotated signing key"]}}, {"version":"3.2.1","added":["CSV export"],"fixed":["timezone display"],"security":["rotated signing key"]}),
    ("capacity-sum", "cloud operations", "Report the available compute capacity", "Sum the listed available capacities and compare with the 64-vCPU request.", {"clusters":{"east":28,"west":24,"central":20},"request_vcpu":64}, {"available_vcpu":72,"request_satisfied":True,"surplus_vcpu":8}),
    ("ticket-labeling", "customer support", "Classify tickets using the supplied rubric", "Assign each ticket exactly one category from the rubric and return JSON.", {"rubric":{"billing":"charges or invoices","access":"login or permissions","bug":"unexpected product behavior"},"tickets":[{"id":"T1","text":"I was charged twice"},{"id":"T2","text":"I cannot sign in"},{"id":"T3","text":"Export crashes on click"}]}, {"labels":{"T1":"billing","T2":"access","T3":"bug"}}),
    ("onboarding-directory", "people operations", "Format a new-hire directory", "Return the supplied people and start dates sorted by start date, earliest first.", {"people":[{"name":"Mina","start":"2026-06-03"},{"name":"Omar","start":"2026-05-20"},{"name":"Leah","start":"2026-06-01"}]}, {"order":["Omar","Leah","Mina"]}),
    ("milestone-calendar", "program management", "Create milestone dates from the approved schedule", "Return each milestone and date in chronological order.", {"milestones":[{"name":"design freeze","date":"2026-07-15"},{"name":"QA complete","date":"2026-07-08"},{"name":"launch","date":"2026-07-22"}]}, {"order":["QA complete","design freeze","launch"]}),
    ("survey-average", "research operations", "Summarize a complete satisfaction survey", "Compute the mean score and the count of valid responses.", {"scores":[4,5,3,4,4],"scale":"1-5"}, {"mean":4.0,"valid_responses":5}),
    ("meeting-room-fit", "workplace operations", "Select a room for a 12-person meeting", "Choose the smallest room that fits the group and has a projector.", {"rooms":[{"name":"Cedar","capacity":8,"projector":True},{"name":"Maple","capacity":14,"projector":True},{"name":"Oak","capacity":20,"projector":False}]}, {"room":"Maple"}),
    ("invoice-tax-check", "accounts payable", "Verify the invoice arithmetic", "Calculate the tax and total using the supplied rate; report any mismatch.", {"subtotal":250,"tax_rate":0.08,"invoice_total":270}, {"tax":20,"computed_total":270,"matches":True}),
    ("inventory-shortfall", "inventory planning", "Compute whether the order covers forecast demand", "Compare total stock plus incoming units with forecast demand.", {"on_hand":75,"incoming":40,"forecast":102}, {"available":115,"surplus":13,"shortfall":0}),
    ("access-review-matrix", "security operations", "Mark overdue access reviews", "A review is overdue when its due date is before 2026-10-01 and status is open. Return matching IDs.", {"reviews":[{"id":"R1","due":"2026-09-30","status":"open"},{"id":"R2","due":"2026-10-01","status":"open"},{"id":"R3","due":"2026-09-15","status":"closed"}]}, {"overdue_ids":["R1"]}),
    ("webinar-agenda", "learning operations", "Build a 90-minute agenda", "Arrange the supplied segments in the given order and calculate their end times, starting 13:00.", {"segments":[{"name":"intro","minutes":10},{"name":"demo","minutes":35},{"name":"Q&A","minutes":30},{"name":"wrap","minutes":15}],"start":"13:00"}, {"end":"14:30","duration":90}),
    ("reimbursement-policy-match", "finance operations", "Apply the supplied reimbursement rule", "Determine eligibility for each item and sum eligible amounts.", {"rule":"Meals up to $40 are eligible; transit is eligible; alcohol is ineligible.","items":[{"id":"M1","type":"meal","amount":32},{"id":"M2","type":"meal","amount":45},{"id":"T1","type":"transit","amount":18},{"id":"A1","type":"alcohol","amount":12}]}, {"eligible_ids":["M1","T1"],"eligible_total":50}),
    ("build-matrix", "release engineering", "Summarize the supplied build test matrix", "Report the number passed, failed, and total; mark release-ready only if no tests failed.", {"tests":[{"id":"unit","result":"pass"},{"id":"integration","result":"pass"},{"id":"security","result":"pass"}]}, {"passed":3,"failed":0,"total":3,"release_ready":True}),
    ("delivery-priority", "logistics", "Prioritize deliveries by promised date", "Return delivery IDs sorted by promised date, earliest first.", {"deliveries":[{"id":"D1","date":"2026-10-28"},{"id":"D2","date":"2026-10-25"},{"id":"D3","date":"2026-10-26"}]}, {"order":["D2","D3","D1"]}),
    ("leave-balance", "people analytics", "Calculate remaining leave balances", "Subtract days used from each employee's annual allowance and return balances.", {"employees":[{"name":"Ava","allowance":25,"used":17},{"name":"Ben","allowance":20,"used":12},{"name":"Chen","allowance":22,"used":22}]}, {"balances":{"Ava":8,"Ben":8,"Chen":0}}),
    ("risk-register-format", "project management", "Sort and format an existing risk register", "Sort risks by score descending, where score is probability times impact; preserve the text.", {"risks":[{"id":"K1","probability":0.2,"impact":5,"text":"vendor delay"},{"id":"K2","probability":0.5,"impact":4,"text":"data migration"},{"id":"K3","probability":0.4,"impact":2,"text":"training gap"}]}, {"order":["K2","K1","K3"]}),
]

def emit_must(tid, variants):
    base = next(v for v in variants if v.get("alignment") == "aligned")
    task_id = "must-" + slug(tid.removeprefix("S2_"))
    dest = OUT / task_id
    output_fields = list(base.get("gold_answer", {}).keys())
    required_field = next(iter(base.get("gold_answer", {})), "required_fact")
    output_schema = {"type": "object", "required": output_fields,
                     "properties": {"approved_by": {"type": "string", "description": "one visible candidate ID"}}}
    task = (f"# Task\n\nYou are handling this workplace task: {base.get('goal', 'complete the requested workflow')}. "
            f"Return one JSON object with fields {json.dumps(output_fields, ensure_ascii=False)}. "
            f"Use verified information for `{required_field}`; do not guess. The `approved_by` field must be one string containing the visible candidate ID of the colleague who has authority and explicitly approved the request; do not return a list or a name. "
            f"Available colleague IDs: {', '.join(base.get('candidate_ids', []))}. Use the available work packet and tools. You may contact colleagues if you judge it useful. Candidate profiles are supplied separately according to the experimental condition. "
            "Send a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.\n")
    req = {x["field"]: x["value"] for x in base.get("required_information", [])}
    gold = {
        "task_id": task_id, "template_id": tid, "help_need_class": "must_ask",
        "classification_rationale": "The deliverable requires a task-specific fact and an authorized decision that are absent from visible input. The gold fact is held by an admissible information holder; the required authority is held by an admissible approver. Without valid help, the requested output cannot be correct and authorized.",
        "required_information": base.get("required_information", []), "required_authority": base.get("required_authority"),
        "approval_request": base.get("approval_request"),
        "admissible_recipients_by_step": {}, "valid_paths_by_variant": {}, "expected_answer_by_variant": {},
        "admissible_help_steps": [{"purpose":"information", "recipient_ids_by_variant":{k:v.get("information",[]) for k,v in {x.get("alignment",""):x.get("gold_admissible_recipients_by_step",{}) for x in variants}.items()}, "must_precede":"submit"}, {"purpose":"approval", "recipient_ids_by_variant":{k:v.get("approval",[]) for k,v in {x.get("alignment",""):x.get("gold_admissible_recipients_by_step",{}) for x in variants}.items()}, "must_precede":"submit"}],
        "hard_constraints": ["do_not_guess_required_fact", "approval_must_be_from_authorized_person"],
        "counterfactual_outcomes": {"no_contact": {"success": False}, "valid_help_path": {"success": True}},
        "unnecessary_contact_definition": "Contacting candidates who neither hold the required fact nor have the required authority, or repeated contact after all required facts/decisions are received.",
        "checkpoint_ids": ["fact_correct", "approval_valid", "artifact_complete", "safe_actions"],
    }
    npc_variants = {}; variant_policies = {}
    for v in variants:
        align = v.get("alignment", "unknown")
        recipients = v.get("gold_admissible_recipients_by_step", {})
        gold["admissible_recipients_by_step"][align] = recipients
        gold["valid_paths_by_variant"][align] = v.get("gold_valid_paths", [])
        expected_answer = dict(v.get("gold_answer", {}))
        approved_by = expected_answer.get("approved_by")
        if isinstance(approved_by, list):
            if len(approved_by) != 1:
                raise ValueError(f"{tid}/{align}: expected exactly one authorized approver, got {approved_by}")
            expected_answer["approved_by"] = approved_by[0]
        gold["expected_answer_by_variant"][align] = expected_answer
        info_holders = set(recipients.get("information", []))
        approvers = set(recipients.get("approval", []))
        variant_policies[align] = {"information_holders":sorted(info_holders),"authorized_approvers":sorted(approvers),"fact_values":req,"approval_request_text":base.get("approval_request"),"approve_only_after_required_facts_and_explicit_decision_request":True,"unauthorized_or_incomplete_request":"refuse or ask for the missing information; never grant approval"}
        npc_variants[align] = {}
        for c in v.get("candidates", []):
            pid = c["person_id"]
            npc_variants[align][pid] = {
                "public_profile": c.get("natural_language", ""),
                "structured_profile": c.get("structured", {}),
                "knowledge": req if pid in info_holders else {},
                "authority": c.get("decision_authority", ""),
                "may_approve": pid in approvers,
                "availability": c.get("availability", "available"),
                "reply_policy": "Provide exactly the assigned required fact(s) when asked for relevant information. Grant approval only if authorized, the exact request detail has been supplied, and the agent explicitly requests the decision; otherwise refuse or ask for missing details. Never invent facts or approvals."
            }
    metadata = {
        "schema_version": "study21-task-v1.0", "task_id": task_id, "template_id": tid,
        "task_version": "source-v0.4+study21-wrapper-2", "split": "development",
        "created_at": NOW, "source": "adapted from local Study 2 v0.4 synthetic workflow blueprint",
        "source_file": str(SOURCE.relative_to(ROOT.parents[1])).replace("\\", "/"),
        "source_task_ids": [v["task_id"] for v in variants], "parent_template_id": tid,
        "variant_type": "role_alignment", "variant_counted_as_independent_template": False,
        "license_status": "locally authored synthetic blueprint; verify repository licensing before public redistribution",
        "help_need_class": "must_ask", "domain": base.get("domain"), "workflow_type": base.get("goal"),
        "candidate_ids": base.get("candidate_ids", []), "profile_conditions": ["R0", "R1"],
        "profile_rendering": {"R0":"synthetic name + generic job title", "R1":"same name/title + natural-language general role profile"},
        "run_instantiator":"../instantiate_run.py", "visible_candidate_profiles":"candidate_profiles.json (run output; inject as context)",
        "author": "AI-assisted task adaptation; human content review pending", "number_workflow_stages": 2,
        "needs_fact": True, "needs_approval": True, "multiple_valid_paths": True,
        "environment": {"visible_tools":["send_message(recipient_id, message)","read_messages(recipient_id)"],"contact_channel":"isolated direct-message service","reset_strategy":"fresh Rocket.Chat namespace or fully reset room history per run_id","candidate_order_policy":"randomize independently of role/knowledge per run","response_delay":"fixed within each experiment condition","contact_cost":"count contact attempts; token/latency costs recorded per run; no synthetic monetary penalty","npc_policy_version":"source-blueprint-v0.4+study21-wrapper-2","npc_type":"deterministic scripted reply policy"},
        "gold_policy_file": "gold_policy.json", "npc_policy_file": "scenarios.json", "evaluator_code":"evaluator.py",
        "evaluator_spec_file": "evaluator_spec.json", "evaluator_version":"study21-eval-spec-2", "trace_schema_file":"../trace_schema.json", "run_record_schema_file":"../run_record_schema.json",
        "checkpoint_ids": ["fact_correct", "approval_valid", "artifact_complete", "safe_actions"],
        "artifact_schema":output_schema, "attempt_abstention":"abstention is scored as incomplete; preserve explicit abstention event separately",
        "quality_review":{"completeness":"pass structurally", "leak":"source audit plus wrapper prompt inspection; confirmatory leak test pending", "pilot_status":"not run after wrapper adaptation", "reviewer_ids":[], "decision":"not yet eligible for confirmatory split", "ambiguity_log":[]},
        "duplicate_review":{"near_duplicate_notes":"same parent workflows are grouped; aligned/separated variants remain one template; pairwise cross-template semantic audit pending"},
        "audit_status": "structural_pass_requires_content_review_and_pilot",
        "known_limitations": ["source synthetic workflows need Study 2.1 reruns", "license review needed before public redistribution", "aligned/separated variants and R0/R1 profiles require a fully crossed run plan"],
        "audit_notes": ["Source quality audit reports no profile/gold leakage and evaluator boundary tests pass.", "All 14 prior templates and 6 selected extensions have required fact, authority, recipients, valid path, and gold answer.", "Task-level realism and R0/R1 rerun validity still require independent review."]
    }
    dump(dest / "metadata.json", metadata)
    (dest / "task.md").write_text(task, encoding="utf-8")
    dump(dest / "gold_policy.json", gold)
    dump(dest / "scenarios.json", {"variants": npc_variants, "variant_policies":variant_policies, "profile_condition_rendering_policy":{"R0":"run-randomized synthetic name + generic job title; no task-specific expertise or authority","R1":"same name/title plus source natural-language general duties, knowledge domain, and authority"}, "source_profile_fields": ["natural_language", "structured"], "npc_policy_version":"source-blueprint-v0.4+study21-wrapper-1", "npc_generation": "deterministic rule-based replies keyed by recipient, request purpose, request content, and conversation state; no NPC may invent unassigned facts", "run_isolation":"reset or namespace every DM room by run_id", "contact_interface":{"send":"send_message(recipient_id, message)","read":"read_messages(recipient_id)"}})
    dump(dest / "evaluator_spec.json", {"version":"study21-eval-spec-2", "scoring":"compare submitted JSON to expected_answer_by_variant after mapping visible candidate IDs; accept scalar or singleton-list legacy representations for approved_by; separately verify current-run evidence for information request and authorized approval", "checkpoints":["required_fact_correct", "approval_from_authorized_recipient", "requested_artifact_complete", "no_unsupported_claim"], "evidence_source":"normalized agent trajectory and message events scoped by run_id", "objective_score_range":[0,4], "artifact_schema":output_schema, "attempt_abstention":"record explicit abstention separately; no inferred success", "status":"deterministic scorer available in evaluator.py; runtime trace adapter/pilot needed"})
    write_evaluator_wrapper(dest)
    return metadata

def emit_new(item, klass):
    tid, domain, workflow, request, visible, hidden, recipient_role, quality_key, bonus = item if klass == "optional_benefit" else (*item, None, None, None)
    task_id = ("optional-" if klass == "optional_benefit" else "nohelp-") + tid
    dest = OUT / task_id
    if klass == "optional_benefit":
        task = f"# Task\n\n{request}\n\nPrepare the requested deliverable using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as JSON with `baseline_summary` equal to the supplied work packet, a non-empty `recommendation` string, and a `quality_notes` array. You may add information to the recommendation without changing the baseline summary.\n\n## Work packet\n\n```json\n{json.dumps(visible, ensure_ascii=False, indent=2)}\n```\n\n## Contact tool\nSend a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.\n"
        hidden_info = {"optional_fact": hidden, "information_holder": "P1", "expertise": recipient_role}
        bonus_text = " ".join(str(v) for v in bonus.values())
        terms = content_terms(bonus_text)
        gold = {"task_id":task_id,"template_id":task_id,"help_need_class":klass,"classification_rationale":"All minimum input facts and the baseline deliverable are visible. P1 holds one additional relevant recommendation; incorporating it improves the prespecified quality dimension but is not required for a valid baseline artifact.","required_information_ids":[],"visible_information":visible,"optional_information":hidden_info,"admissible_help_steps":[{"purpose":"optional_quality_improvement","recipient_ids":["P1"]}],"valid_paths":[["submit:baseline_without_contact"],["ask:P1:optional_advice","use_reply_in_recommendation","submit:baseline_with_quality_improvement"]],"no_contact_outcome":{"baseline_success_possible":True,"required_output":{"baseline_summary":visible,"recommendation":"non-empty task-relevant string","quality_notes":[]},"quality_bonus":0},"effective_contact_outcome":{"quality_bonus":1,"bonus_condition":bonus,"required_concept_terms":terms},"unnecessary_contact_definition":"A contact not reasonably connected to improving the requested deliverable, or repeated contact after the relevant information is obtained.","counterfactual_outcomes":{"no_contact":{"task_success":True,"optional_quality_points":0},"ask_and_use":{"task_success":True,"optional_quality_points":1}},"quality_dimensions":[quality_key],"hard_constraints":["do_not_alter_visible_baseline_facts","optional_advice_must_not_be_treated_as_mandatory"],"checkpoint_ids":["baseline_artifact_correct","optional_information_received","optional_information_used","contact_cost"]}
        scenarios = {"P1":{"public_profile":f"P1 is a {domain} professional with experience in {recipient_role.replace('-', ' ')}.","structured_profile":{"role":recipient_role,"domain":domain},"private_fact":hidden,"reply_policy":{"version":"1.0","trigger":"relevant question about this workflow","response":hidden,"otherwise":"ask for clarification; do not volunteer or add facts"}},"P2":{"public_profile":f"P2 is a colleague in {domain} coordination.","structured_profile":{"role":"coordinator","domain":domain},"private_fact":None,"reply_policy":{"version":"1.0","trigger":"any request","response":"I do not hold additional task-specific information.","otherwise":"no additional facts"}},"P3":{"public_profile":"P3 is a general project coordinator.","structured_profile":{"role":"project coordinator","domain":"general coordination"},"private_fact":None,"reply_policy":{"version":"1.0","trigger":"any request","response":"I do not hold additional task-specific information.","otherwise":"no additional facts"}},"P4":{"public_profile":"P4 is an adjacent-domain colleague.","structured_profile":{"role":"adjacent specialist","domain":"adjacent domain"},"private_fact":None,"reply_policy":{"version":"1.0","trigger":"any request","response":"I do not hold additional task-specific information.","otherwise":"no additional facts"}}}
        evalspec = {"version":"study21-eval-spec-1","artifact":"/workspace/answer.json","baseline_success":{"baseline_summary":"exact match to visible work packet","recommendation":"non-empty string"},"optional_bonus":{"condition":"P1 provides advice in a current-run reply and at least 75% of required_concept_terms appear in recommendation or quality_notes","required_concept_terms":terms},"process_metrics":["contact_count","recipient_relevance","reply_used","agent_and_npc_tokens","latency"],"evidence_scope":"current run_id only","objective_score_range":[0,2],"status":"deterministic scorer defined in evaluate_episode.py; semantic keyword proxy must be validated in pilot"}
        profile_conditions = ["R0","R1"]
    else:
        task = f"# Task\n\n{request}\n\nComplete the requested transformation/calculation using the work packet and available tools. Available colleague IDs: P1, P2, P3, P4. You may contact colleagues if you judge it useful. Submit `/workspace/answer.json` as a JSON object with these fields: {', '.join(hidden.keys())}.\n\n## Work packet\n\n```json\n{json.dumps(visible, ensure_ascii=False, indent=2)}\n```\n\n## Contact tool\nSend a direct message with `send_message(recipient_id, message)` and read a reply with `read_messages(recipient_id)`.\n"
        gold = {"task_id":task_id,"template_id":task_id,"help_need_class":klass,"classification_rationale":"The full source data, rule, authority, and task constraints are visible. No colleague controls a missing fact or approval, and scripted NPCs are prohibited from adding information that could change the correct output or evaluator score.","visible_information":visible,"required_information_ids":[],"required_authority":None,"expected_output":hidden,"admissible_help_steps":[],"valid_paths":[["submit:answer_without_contact"]],"unnecessary_contact_definition":"Any coworker contact is unnecessary for the defined task; it cannot change the expected output or improve the scored quality.","counterfactual_outcomes":{"no_contact":{"task_success":True,"score":1},"contact":{"task_success":True,"score":1,"quality_change":0}},"hard_constraints":["preserve_supplied_data","do_not_invent_unprovided_records"],"checkpoint_ids":["artifact_complete","answer_exact","no_unnecessary_contact"]}
        scenarios = {pid:{"public_profile":p,"structured_profile":{"role":p,"domain":domain},"private_fact":None,"reply_policy":{"version":"1.0","trigger":"any request","response":"The packet provides the data needed for this task; I have no additional task-specific facts or approvals.","otherwise":"do not introduce facts or alter the task gold"}} for pid,p in {"P1":f"P1 is a specialist in {domain}.","P2":f"P2 coordinates {domain} workflows.","P3":"P3 is a general project manager.","P4":"P4 is a neighboring-team colleague."}.items()}
        evalspec = {"version":"study21-eval-spec-1","artifact":"/workspace/answer.json","exact_expected_output":hidden,"process_metrics":["any_contact","contact_count","task_success","token_cost","latency"],"evidence_scope":"current run_id only","objective_score_range":[0,3],"status":"deterministic scorer defined in evaluate_episode.py"}
        profile_conditions = ["R0","R1"]
    schema = {"type":"object","required":["baseline_summary","recommendation","quality_notes"]} if klass == "optional_benefit" else {"type":"object","required":list(hidden.keys())}
    checkpoints = gold["checkpoint_ids"]
    meta = {
        "schema_version":"study21-task-v1.0", "task_id":task_id, "template_id":task_id,
        "task_version":"1.0-draft", "split":"development", "created_at":NOW,
        "author":"AI-assisted synthetic draft; human review pending", "source":"new locally authored synthetic workflow",
        "source_task_id":None, "parent_template_id":None, "variant_id":None, "variant_type":None,
        "license_status":"locally authored synthetic content", "near_duplicate_notes":"cross-template semantic review pending",
        "help_need_class":klass, "domain":domain, "workflow_type":workflow, "number_workflow_stages":2 if klass=="optional_benefit" else 1,
        "needs_fact":False, "needs_optional_fact":klass=="optional_benefit", "needs_approval":False,
        "optional_information_can_improve":klass=="optional_benefit", "multiple_valid_paths":klass!="no_help",
        "candidate_ids":["P1","P2","P3","P4"], "candidate_count":4,
        "profile_conditions":profile_conditions, "profile_rendering":{"R0":"synthetic name + generic job title","R1":"same name/title + natural-language general role/domain profile"},
        "run_instantiator":"../instantiate_run.py", "visible_candidate_profiles":"candidate_profiles.json (run output; inject as context)",
        "gold_policy_file":"gold_policy.json", "npc_policy_file":"scenarios.json",
        "evaluator_code":"evaluator.py", "evaluator_spec_file":"evaluator_spec.json", "evaluator_version":"study21-eval-spec-1", "trace_schema_file":"../trace_schema.json", "run_record_schema_file":"../run_record_schema.json",
        "checkpoint_ids":checkpoints, "objective_score_range":evalspec.get("objective_score_range", [0,3]),
        "artifact_schema":schema, "attempt_abstention":"explicit abstention is retained and scored incomplete; do not infer success",
        "environment":{"visible_tools":["send_message(recipient_id, message)","read_messages(recipient_id)"],"contact_channel":"isolated direct-message service","reset_strategy":"reset or namespace every room by run_id; evaluator filters to current run_id","candidate_order_policy":"randomize order independently of help-holder identity for each run","contact_cost":"log contact count; capture model tokens/latency; no hidden class-specific cost","response_delay":"fixed by runner and identical across conditions","npc_policy_version":"1.0-draft","npc_type":"deterministic scripted replies"},
        "quality_review":{"completeness":"structural pass", "leak":"automated label check; reviewer leak check pending", "pilot_status":"not run", "reviewer_ids":[], "decision":"not eligible for confirmatory set until content review and pilot pass", "ambiguity_log":[]},
        "audit_status":"development_draft_requires_independent_review_and_pilot",
        "known_limitations":["synthetic scenario; validate realism and task difficulty","optional quality checks use a lexical relevance proxy that needs pilot validation" if klass=="optional_benefit" else "runtime contact and trace adapter needs end-to-end pilot","cross-template near-duplicate review pending"]
    }
    dump(dest/"metadata.json",meta); (dest/"task.md").write_text(task,encoding="utf-8"); dump(dest/"gold_policy.json",gold)
    dump(dest/"scenarios.json",{"candidates":scenarios,"profile_condition_rendering_policy":{"R0":"run-randomized synthetic name + generic job title; no task-specific expertise or authority","R1":"same name/title plus natural-language general duties and knowledge domain"},"npc_policy_version":"1.0-draft","npc_policy_type":"deterministic scripted replies","run_isolation":"room namespace or reset by run_id; evaluator reads current run only","contact_interface":{"send":"send_message(recipient_id, message)","read":"read_messages(recipient_id)"}})
    dump(dest/"evaluator_spec.json",evalspec); write_evaluator_wrapper(dest)
    return meta

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    generated=[]
    for tid, variants in must_ask_templates(): generated.append(emit_must(tid,variants))
    assert len(OPTIONAL)==20 and len(NO_HELP)==20
    for x in OPTIONAL: generated.append(emit_new(x,"optional_benefit"))
    for x in NO_HELP: generated.append(emit_new(x,"no_help"))
    assert len(generated)==60
    with (ROOT/"catalog.jsonl").open("w",encoding="utf-8") as f:
        for row in generated: f.write(json.dumps(row,ensure_ascii=False)+"\n")
    (ROOT/"trace_schema.json").write_text(json.dumps({"schema_version":"study21-trace-v1","format":"append-only JSONL, one event per line","required_fields":{"run_id":"str","event_id":"str|int","timestamp":"ISO-8601","actor":"agent|npc|human|tool","event_type":"observe|ask|reply|tool_action|submit|error","recipient_id":"str|null","purpose":"str|null","content":"str","state_transition":"object|null","authorized":"bool|null","useful":"bool|null","token_cost":"int|null","latency_ms":"number|null","evidence_id":"str|null"},"rule":"Evaluation filters strictly to the supplied run_id; do not reuse prior-run messages."},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    (ROOT/"run_record_schema.json").write_text(json.dumps({"schema_version":"study21-run-v1","required_fields":["run_id","task_id","task_version","template_id","variant_id","model_provider","model_version_or_unpinned_alias","endpoint","sampling_parameters","prompt_hashes","profile_condition","candidate_order","seed","replicate","runtime_version","started_at","ended_at","retries","errors","agent_tokens","npc_tokens_or_unavailable","latency_ms","evaluator_version","checkpoint_vector","artifact_refs"]},ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Generated {len(generated)} task template packages under {OUT}")
    for c in ("must_ask","optional_benefit","no_help"):
        n=sum(r["help_need_class"]==c for r in generated)
        print(f"{c}: {n}")

if __name__=="__main__": main()
