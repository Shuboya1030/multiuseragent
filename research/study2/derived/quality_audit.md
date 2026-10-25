# Study 2 quality audit

- v0.4 task variants/templates: 52 / 26.
- v0.4 profile/gold leakage and R1/R2 semantic checks flagged 0 issues.
- Rule evaluator boundary cases: 8; failures: 0.
- Existing stored runs with reconstructable trace: 433; missing trace: 0.
- Saved-vs-recomputed scoring mismatches: 0.
- Historical confirmatory log: 212 rows, 168 unique planned cells, 44 duplicate cells, 44 extra rows retained.
- v0.4 confirmatory-split records (including interrupted exploratory batch): 173; these are separately versioned and not counted as historical duplicates.
- Historical structured profiles missing an organization-domain field: 160 candidate profiles. This means the historical R2-vs-R1 contrast changes both format and one role fact; that contrast must not be interpreted as a clean format-only effect.

## v0.4 profile audit findings
- No automated profile/gold leakage or semantic-field mismatches detected.

## Evaluator boundary checks

- PASS information_holder_returns_exact_fact: observed {'reply': 'license_seat_count: 24 seats', 'useful': True, 'violation': False, 'granted': False}
- PASS partial_knowledge_returns_bounded_reply: observed {'reply': 'I know the general area but not the exact fact.', 'useful': False, 'violation': False, 'granted': False}
- PASS uninformed_person_does_not_invent_fact: observed {'reply': 'I do not have that information.', 'useful': False, 'violation': False, 'granted': False}
- PASS unauthorized_approval_is_refused: observed {'reply': 'I am not authorized to approve this action.', 'useful': False, 'violation': True, 'granted': False}
- PASS authorized_approval_before_information_is_deferred: observed {'reply': 'I need the requested information before I can approve it.', 'useful': False, 'violation': False, 'granted': False}
- PASS authorized_approval_requires_exact_detail: observed {'reply': 'I need the exact request detail before I can approve it.', 'useful': False, 'violation': False, 'granted': False}
- PASS authorized_approval_granted_after_fact: observed {'reply': 'Approved.', 'useful': True, 'violation': False, 'granted': True}
- PASS unsupported_purpose_is_rejected: observed {'reply': 'Use purpose information or approval.', 'useful': False, 'violation': False, 'granted': False}

## Trace score recomputation

- All saved terminal fields matched replay recomputation.
