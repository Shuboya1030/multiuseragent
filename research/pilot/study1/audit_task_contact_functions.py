"""Create a manually reviewed, task-instruction-level contact-function audit."""
from __future__ import annotations

import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
PILOT = ROOT / "research" / "pilot"
OUT = PILOT / "study1"

# These codes describe what the task asks the agent to do, not what the agent
# actually did in a trajectory. The mapping was checked against each task.md.
LABELS = {
    "admin-ask-for-meeting-feedback": ("explicit", "task_directed_data_collection", "feedback_and_participant_discovery", "recipient_set_partly_discovered", "missing_participant_list; feedback collection"),
    "admin-ask-for-upgrade-reimbursement": ("explicit_with_conditional_branch", "conditional_help_or_authority_request", "reimbursement_request_then_policy_advice", "named_then_conditional_escalation", "reimbursement refusal / deadline procedure"),
    "admin-check-employees-budget-and-reply": ("explicit", "task_directed_data_collection", "collect_requests_then_report_calculation", "fixed_named_recipients", "equipment request inputs"),
    "admin-check-employees-budget-and-reply-2": ("explicit", "task_directed_data_collection", "collect_requests_and_budget_data", "fixed_named_recipients_plus_finance_contact", "equipment needs; budgets and prior expenses"),
    "admin-check-employees-budget-and-reply-and-record": ("explicit_with_conditional_branch", "task_directed_data_collection", "collect_requests_then_negotiate_reduction", "fixed_named_recipients_then_group_followup", "equipment needs; overspend triggers reduction request"),
    "admin-collect-requests-and-compute-total-price": ("explicit", "task_directed_data_collection", "collect_equipment_requests", "fixed_named_recipients", "equipment names and quantities"),
    "admin-employee-info-reconciliation": ("optional_if_needed", "conditional_help_seeking", "employee_information_verification_and_correction", "agent_discovers_employees_and_chooses_contacts", "missing, outdated, or conflicting employee facts"),
    "admin-get-best-vendor-quote": ("explicit", "task_directed_information_gathering", "locate_quotes_and_consult_requirements", "named_quote_owner_and_optional_expert", "quote location; server requirements"),
    "finance-apply-tax-credit": ("conditional_if_ambiguous", "conditional_clarification_or_advice", "resolve_ambiguous_tax_form_items", "role_lookup_then_finance_director", "ambiguous form questions"),
    "finance-find-signatories": ("explicit", "task_directed_information_gathering", "locate_financial_documents_then_report", "finance_director_by_role_then_sales_director", "annual-updates folder path"),
    "finance-r-d-activities": ("explicit", "task_directed_data_collection", "collect_employee_activity_and_hours", "relevant_personnel_selected_from_file", "employee-specific R&D hours and work descriptions"),
    "hr-check-attendance-multiple-days-department-with-chat": ("explicit", "task_directed_information_gathering", "department_membership_lookup", "fixed_role_based_recipients", "which employees belong to departments"),
    "hr-check-for-invalid-passwords-and-ask-for-valid-passwords": ("conditional_for_invalid_records", "task_directed_correction_request", "request_replacement_credentials", "only_people_with_invalid_passwords", "password fails explicit validation rules"),
    "hr-collect-feedbacks": ("explicit", "task_directed_feedback_collection", "collect_peer_feedback_then_deliver_review", "fixed_named_recipients", "peer opinions about one employee"),
    "hr-collect-multiple-valid-passwords": ("explicit", "task_directed_data_collection", "collect_credentials_from_team", "fixed_named_recipients", "password values from named employees"),
    "hr-delete-and-insert-user": ("no_personal_help_contact", "not_help_seeking", "perform_channel_membership_changes", "not_applicable", "no human information request in task"),
    "hr-get-valid-password": ("explicit", "task_directed_information_request", "obtain_corrected_credential", "fixed_named_recipient", "known password violates explicit rules"),
    "hr-green-card-consultation": ("optional_if_needed", "conditional_clarification", "resolve_personal_case_information_gap", "named_employee", "beneficiary category/birth-country detail if image insufficient"),
    "hr-mass-survey": ("explicit", "task_directed_survey", "collect_vacation_plans", "all_employees", "destination, duration, travel budget"),
    "hr-new-grad-job-description-2": ("explicit", "task_directed_information_gathering", "collect_job_requirements", "fixed_named_recipient", "specific job requirements"),
    "hr-new-grad-job-description-3": ("explicit", "task_directed_information_gathering", "collect_requirements_and_template_location", "fixed_named_recipients", "responsibilities; template location; qualifications; salary"),
    "hr-pick-interviewer-1": ("explicit", "task_directed_information_then_coordination", "gather_expertise_then_request_interview", "named_manager_then_agent_selects_one_from_roster", "interviewer tech stacks; selected person's availability"),
    "hr-pick-interviewer-2": ("explicit", "task_directed_coordination", "find_willing_available_interviewer", "manager_then_sequential_candidate_choice", "availability and willingness"),
    "hr-pick-interviewer-3": ("explicit", "task_directed_persuasion_or_consent_request", "request_interviewer_participation", "fixed_named_recipient", "recipient consent to interview"),
    "hr-resume-screening": ("explicit_with_conditional_fallback", "task_directed_information_request", "obtain_role_requirements_then_screen_candidate", "named_primary_then_named_fallback", "job requirements; fallback if Li Ming unavailable"),
    "pm-ask-for-issue-and-create-in-gitlab": ("explicit", "task_directed_information_gathering", "collect_issue_preferences_and_details", "fixed_named_recipient", "issue choice, description, milestone, due date"),
    "pm-ask-issue-assignee-for-issue-status-and-update-in-plane": ("explicit", "task_directed_status_inquiry", "discover_assignee_then_check_status", "assignee_discovered_from_plane", "issue completion status"),
    "pm-check-backlog-update-issues": ("explicit", "task_directed_status_inquiry_and_followup", "contact_assignees_about_blocked_work", "assignees_discovered_from_plane", "whether blocked/backlog items are complete"),
    "pm-plan-personnel-for-new-project": ("no_contact_instruction", "not_help_seeking", "plan_staffing_from_available_information", "not_applicable", "no explicit interpersonal query in task prompt"),
    "pm-prepare-meeting-with-customers": ("explicit", "task_directed_notification", "send_artifact_name_to_project_manager", "fixed_named_recipient", "no information requested; provide deliverable location/name"),
    "pm-schedule-meeting-1": ("explicit", "task_directed_coordination", "find_mutually_available_meeting_time", "fixed_two_recipients", "availability windows"),
    "pm-schedule-meeting-2": ("explicit", "task_directed_coordination", "find_mutually_available_meeting_time", "fixed_two_recipients", "availability windows"),
    "pm-send-notification-to-corresponding-user": ("explicit_but_underspecified", "task_directed_clarification", "ask_requester_what_action_is_expected", "fixed_named_recipient", "underspecified task instruction"),
    "qa-update-issue-status-according-to-colleagues": ("explicit", "task_directed_status_inquiry", "check_issue_status_then_update", "fixed_named_recipients", "two issue status reports"),
    "sde-create-new-gitlab-project-logo": ("explicit_with_approval_gate", "approval_or_consent_request", "obtain_review_before_publishing_logo", "fixed_named_reviewer", "approval of generated logo"),
    "sde-create-new-repo": ("explicit", "task_directed_information_gathering", "ask_leader_for_project_details_and_tasks", "fixed_named_recipient", "project description and concrete tasks"),
    "sde-debug-crashed-server": ("conditional_for_access_blocker", "conditional_help_seeking", "obtain_credentials_if_needed_to_unblock_debugging", "named_access_provider", "credentials/access blocker"),
    "sde-find-answer-in-codebase-3": ("explicit", "task_directed_expert_lookup", "find_on_call_expert_then_ask_answer", "on_call_person_discovered_from_schedule", "latest relevant pull-request number"),
    "sde-reply-community-issue-by-asking-npc": ("explicit", "task_directed_consultation", "ask_colleague_about_issue_then_reply", "fixed_named_recipient", "issue-specific expertise/context"),
    "sde-report-agent-repos": ("conditional_on_scan_result", "task_directed_notification", "report_security_scan_finding", "fixed_cto_recipient", "no help requested; notification depends on repository findings"),
}


def main() -> None:
    policy_rows = list(csv.DictReader((OUT / "task_policy_codebook.csv").open(encoding="utf-8-sig")))
    npc = json.loads((PILOT / "tac/npc_definition.json").read_text(encoding="utf-8"))
    names = [f"{x['first_name']} {x['last_name']}" for x in npc]
    fields = ["task", "n_scenario_people", "contact_policy_class_v1", "contact_mandate", "task_level_help_behavior_type", "primary_interaction_pattern", "recipient_autonomy", "task_defined_trigger", "prompt_named_contacts", "prompt_named_not_in_scenario_roster", "scenario_roster_names_not_named_in_prompt", "contact_instruction_excerpt", "evaluator_records_available", "audit_status"]
    rows = []
    for item in policy_rows:
        task = item["task"]
        if task not in LABELS:
            raise ValueError(f"Missing manual task code: {task}")
        mandate, help_status, pattern, autonomy, trigger = LABELS[task]
        text = (PILOT / "tac" / task / "task.md").read_text(encoding="utf-8")
        sentences = [" ".join(s.split()) for s in text.replace("\n", " ").split(". ")]
        evidence = next((s for s in sentences if any(w in s.lower() for w in ("ask ", "ask*", "contact", "reach out", "talk to", "message ", "rocket chat", "rocketchat", "chat with", "consult", "collect", "schedule", "availability", "interview"))), "No interpersonal contact instruction identified in task text.")
        scenario = json.loads((PILOT / "tac" / task / "scenarios.json").read_text(encoding="utf-8"))
        roster = set(scenario)
        named = sorted(n for n in names if n.lower() in text.lower())
        eval_count = len(list((PILOT / "traj/res").glob(f"*__eval_{task}*.json")))
        rows.append({
            "task": task,
            "n_scenario_people": item["n_scenario_people"],
            "contact_policy_class_v1": item["contact_policy_class"],
            "contact_mandate": mandate,
            "task_level_help_behavior_type": help_status,
            "primary_interaction_pattern": pattern,
            "recipient_autonomy": autonomy,
            "task_defined_trigger": trigger,
            "prompt_named_contacts": "; ".join(named),
            "prompt_named_not_in_scenario_roster": "; ".join(n for n in named if n not in roster),
            "scenario_roster_names_not_named_in_prompt": "; ".join(sorted(roster - set(named))),
            "contact_instruction_excerpt": evidence[:500],
            "evaluator_records_available": eval_count,
            "audit_status": "single-analyst task.md + scenario-roster cross-check; evaluator scores do not encode recipient validity",
        })
    out = OUT / "tac_task_help_behavior_audit_v1.csv"
    with out.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)
    print(f"Wrote {len(rows)} task audits to {out}")


if __name__ == "__main__":
    main()
