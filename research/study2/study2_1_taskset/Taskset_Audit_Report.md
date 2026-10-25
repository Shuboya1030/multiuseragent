# Study 2.1 Task Set: audit and readiness report

## 2026-10-25 evaluator-v3 correction

Missing required approval now contributes to Must underhelp. Valid evidence must be current-run delivered replies paired with admissible pending requests before submission; approval requires explicit authorization after information receipt. All 60 current metadata/spec files and the generator carry v3; task prompts, gold answers and NPC policies are unchanged. Unit boundaries and 182 package fixtures pass. Historical raw batches are preserved; 39 offline v3 derivatives are stored separately. These checks do not replace independent content review or formal collection gates.

**Status: 60 draft templates generated; not ready for confirmatory runs.**

## 1. Counts and independent-template unit

| Help-need stratum | Count | Independent workflow unit |
|---|---:|---|
| Must ask | 20 | 20 unique template IDs; each imports the aligned and separated profile-alignment records under one parent template, so those variants count once. |
| Optional, potentially beneficial | 20 | 20 newly authored workflow templates. |
| No help needed | 20 | 20 newly authored workflow templates. |
| **Total** | **60** | **60 unique template IDs** |

All task templates implement the Study 2.1 profile contrast as **R0 = synthetic name + generic job title** and **R1 = the same name/title plus general natural-language role information**. R2 is not included because the current Study 2.1 plan specifies R0/R1 as its contrast and does not manipulate profile format.

## 2. Must-ask templates and source audit

The local Study 2 v0.4 catalog has 52 records grouped into 26 independent workflows: 14 `previously_seen_template` workflows and 12 `new_extension_template` workflows. Each workflow has aligned and separated variants; the pair is not counted twice.

The source repository's `research/study2/derived/quality_audit.md` reports: zero profile/gold leakage flags, eight evaluator boundary cases with zero failures, 433 stored runs with reconstructable traces and no missing traces, and no saved-versus-recomputed score mismatches. This is useful source evidence, but does not by itself validate the Study 2.1 adaptation or prove every task's ecological validity.

The structural audit found that each of the 26 aligned blueprint records has: one required information fact, a specified authority requirement, at least one admissible information recipient, at least one admissible approver, a valid path, a gold answer, and four distractor types. In the imported prompts, the hidden fact and decision are required for the requested task output. The task wrappers in this dataset remove the source's explicit “before submitting, find out / obtain approval” procedure and instead specify the factual output and authorized-approval requirement, leaving the contact decision to the agent.

The 20 included must-ask workflows are:

### 14 previously seen Study 2 workflows

1. `must-expense-reimbursement` — expense reimbursement
2. `must-system-access` — project workspace access
3. `must-release-deployment` — production deployment
4. `must-customer-data-export` — customer data export
5. `must-vendor-onboarding` — vendor onboarding
6. `must-maintenance-window` — maintenance window
7. `must-contract-renewal` — software contract renewal
8. `must-site-safety` — contractor site visit
9. `must-cloud-quota` — cloud capacity increase
10. `must-cost-center-transfer` — internal budget transfer
11. `must-new-hire-equipment` — new employee equipment
12. `must-record-correction` — customer-record correction
13. `must-mileage-reimbursement` — mileage reimbursement
14. `must-service-incident-notice` — service-incident notice

### 6 selected independent v0.4 extensions

1. `must-license-allocation` — software license allocation
2. `must-firewall-exception` — firewall exception
3. `must-data-deletion` — records deletion
4. `must-payroll-adjustment` — payroll adjustment
5. `must-backup-restore` — backup restoration
6. `must-marketing-claim` — customer-facing product claim

The six were selected to add workflow diversity across software assets, security, records/compliance, payroll, data reliability, and marketing compliance. The remaining six v0.4 extensions are not treated as failed; they are an unselected reserve because the requested stratum needs only six additions:

- `S2_accessibility_format`
- `S2_vendor_payment`
- `S2_customer_refund`
- `S2_security_key_rotation`
- `S2_lab_equipment`
- `S2_office_relocation`

The must-ask packages are currently marked `development`, not confirmatory. Their source licensing and the adapted task text should be checked before redistribution or confirmatory use.

## 3. New optional-benefit and no-help templates

The optional set varies domains and potential benefit sources: regional/customer demand, accessibility, maintenance windows, onboarding prerequisites, vendor risk, incident impact, legal exceptions, shift coverage, urgent inventory needs, near-term obligations, customer misconceptions, site access, equipment compatibility, accommodations, local calendars, blackout windows, identity proofing, supplier lead times, transit disruption, and evacuation accessibility.

The no-help set varies deterministic task operations: ledger arithmetic, table normalization, SLA computation, deduplication, release-note formatting, capacity sums, rubric classification, sorting, survey statistics, room selection, invoice arithmetic, inventory arithmetic, date sorting, access-review filtering, agenda timing, policy matching, test-matrix summaries, delivery prioritization, leave balances, and risk sorting.

## 4. Spec audit completed for all 60 packages

- [x] 60 package directories generated.
- [x] 20 task metadata records per help-need class.
- [x] All 60 `task_id` and `template_id` values are unique.
- [x] Each package has task input, task/run metadata pointers, gold policy, NPC scenario policy, evaluator spec, and an executable evaluator entry point.
- [x] Run instantiator shuffles the role-to-alias assignment, synthetic names/generic titles, and candidate display order per seed; paired R0/R1 conditions keep the same name/title while R1 adds general role information. The hidden alias map is written separately for evaluator-only use.
- [x] A renderer-specific fixture checks that R0 is not ID-only, R1 preserves the paired name/title and adds role detail, and role-to-alias/order assignments vary across seeds.
- [x] Metadata covers identity/version, source/licensing, construct, variants, profile conditions, environment/contact interface, reset-by-run, evaluation/checkpoints, artifact schema, reviewer/pilot status, and limitations.
- [x] Each task prompt has the task goal, output format, candidate IDs, a common contact interface, and visible work packet where applicable; hidden class labels and prescribed contact sequences are omitted.
- [x] Must-ask tasks specify purpose-specific admissible recipients and valid paths for both alignment variants; answers are variant-specific. The v2 output contract uses one visible candidate ID string for `approved_by`; the evaluator maps aliases to canonical IDs and accepts legacy singleton arrays. New optional tasks define a valid no-contact baseline and an additional fact/quality condition. No-help tasks provide a deterministic expected output and define contacts as non-beneficial.
- [x] NPC policies specify private facts, authorized recipients, response triggers, refusal/no-invention behavior, and run isolation.
- [x] Hidden-label and exact hidden-value leakage checks pass.
- [x] Structural class and metadata checks pass (`validate_taskset.py`: zero errors).
- [x] Evaluator fixtures cover positive and negative branches across all tasks (must-ask aligned/separated valid paths and no-contact under-help; optional no-contact and advice-use; no-help no-contact and over-help) plus run-specific alias remapping and singleton-array compatibility. The v2 validation run reports 182 synthetic fixture evaluations.
- [x] Python syntax checks pass for the task generator, evaluator, validator, and corrected pilot evaluator.
- [x] The release-readiness pilot's approval target was corrected: engineering validation is mandatory; finance approval is conditional on an approved status/announcement, and pending approval is valid.

### Scoring contract correction (2026-10-24)

The v1 task wording required the agent to identify one approver but did not define the JSON type of `approved_by`; v1 gold stored that single approver as a one-item array. Some model outputs correctly returned a scalar candidate ID and were falsely scored as artifact errors. The generator now specifies `approved_by` as one visible candidate ID string, v2 gold stores it as a scalar, and the evaluator accepts a singleton array for backward compatibility. Alias mapping remains applied before comparison. Raw pilot artifacts remain unchanged; any updated scores are saved as separate post-hoc evaluations.

The v2 evaluator was applied offline to the existing three-provider v4 batch (27 episodes) and paced Moonshot v5 batch (9 episodes), without rerunning any model. New episode-level scores are saved as `evaluation_posthoc_eval_v2.json`; batch provenance is in `posthoc_evaluator_v2_audit.json`, and the combined summary is `pilot_runs/posthoc_evaluator_v2_summary.json`. In the 27 v4 episodes, four must-ask false negatives became successes after the scalar/singleton-list normalization (Anthropic 2/3, OpenAI 1/3); no other scored v4 result changed. In v5, one of three must-ask episodes changed to success. One optional Moonshot episode had no original `evaluation.json` because its scorer serialization failed; it was recovered by offline v2 scoring, so the three post-hoc optional scores are available, while only two original scores are available for comparison. These pilot outcomes are diagnostic and are not confirmatory evidence.

## 5. Gaps before any confirmatory use

1. **No real AgentCompany pilot has been run on these 60 adapted/new templates.** Synthetic evaluator fixtures exercise scoring logic, not whether an LLM can solve each task, whether the task is ambiguous/trivial/impossible, or whether the environment works end to end.
2. **Independent review is not complete.** The package was generated and checked by the same assistant. The spec explicitly requires independent review before confirmatory use; that gate remains open.
3. **NPC/task environment enforcement needs integration.** Scenario files define deterministic policies, but the 60 task bundles are not yet wired to the AgentCompany runtime and those policies are not yet enforced by a deployed environment. The evaluator only consumes normalized current-run traces. The run instantiator creates condition-specific inputs and mappings, but does not launch an episode.
4. **Optional quality scoring uses a keyword-coverage proxy.** It is deterministic and replayable, but semantic validity (whether the advice was truly understood and applied) must be compared with human judgments and calibrated in pilot.
5. **Renderer randomization is statically exercised, but episode isolation is not yet exercised in AgentCompany**; verify run-specific namespace/reset and current-run filtering in runtime pilots.
6. **Source/licensing review is pending** for adapted Study 2 workflows before any external release.
7. **Freeze and power/precision planning are pending.** Twenty per class satisfies the requested template count but does not guarantee adequate power; estimate task-level variation and choose repeat counts before confirmatory collection.

Accordingly, the tasks **pass the package/design-level static audit** but do **not yet pass every Study 2.1 acceptance gate**. In particular, the spec's runtime-enforcement, real-pilot, and independent-review requirements cannot honestly be marked complete based on file checks or synthetic fixtures.

## 6. Next required sequence

1. Obtain an independent content audit and adjudicate every flagged assumption/ambiguity.
2. Wire `instantiate_run.py`, the shared evaluator, and deterministic NPC policies into the AgentCompany runtime; enforce run-specific namespace/reset and trace capture.
3. Pilot every candidate template at least once or preregister a defensible stratified pilot/acceptance protocol; inspect full trajectories, evaluator evidence, and model/NPC token accounting.
4. Fix rejected tasks, rerun audits, then freeze task and evaluator versions; keep pilots out of confirmatory estimates.
5. Run matched model × profile conditions and repeated episodes, saving immutable model IDs, raw trajectories, messages, token usage, evaluator evidence, and error/retry logs.
