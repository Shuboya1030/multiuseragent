# Study 2 prospective extension protocol v0.2

**Status:** fixed before starting the v0.4 collection; this is a prospective extension/replication after inspection of historical pilot and confirmatory traces, not a preregistration made before any data were seen.

## Scope and research question

Estimate whether providing role information improves multi-step help-seeking in a controlled workplace simulation, and whether representing the same role facts as structured fields adds value beyond natural-language profiles. The study also tests whether effects differ when knowledge and authority are held by different people (aligned vs separated).

Study 2 does not train a policy. The reward `R` is a fixed descriptive composite, and component outcomes are reported directly. No reward-weight sensitivity analysis is included, as agreed with the user.

## Prospective collection

- Task set: `task_blueprints_v0.4.jsonl`, task version `0.4`, profile version `profile-0.4`.
- Confirmatory set: the 14 workflow templates used in the earlier collection, each in aligned and separated configurations (28 task variants), four candidates per task. These are a corrected-profile replication.
- 12 newly authored templates (24 variants) are retained as an audited extension set, but are not part of the confirmatory collection or primary effect estimates in this Study 2 closeout.
- Conditions: R0 names only; R1 natural-language profile; R2 structured profile. R1 and R2 encode the same semantic fields: organization domain, expertise, familiarity, authority, and availability. No condition reveals the gold recipient or task-specific answer.
- Models: `gpt-6-luna` and `gpt-5.6-terra`, treated as two fixed model configurations, not a sample of all LLMs.
- One episode per task × model × condition cell; 168 planned episodes. Candidate order is deterministically randomized by task and repetition. This preserves the original Study 2 scope and avoids treating repeated episodes as independent task evidence.
- The simulator provides deterministic, rule-based NPC responses and scoring. Complete prompts, actions, replies, model identifiers, task/profile/prompt versions, invocation IDs, and timestamps are stored.
- Prompt version: `S2-prompt-0.3`. Decode parameters follow the Codex CLI defaults; the runner does not expose temperature. This is logged as a reproducibility limitation.

## Outcomes

Primary behavioral outcomes:

1. Strict first-step validity: the first help request is an information request to an admissible knowledge holder.
2. Valid-path completion: the task fact is obtained and the required authorization is actually granted by an authorized person.
3. Task score `T` (0, 0.5, or 1).

Secondary outcomes: first request target/purpose match, information and approval request counts, total query cost, knowledge misses, unauthorized approval attempts, premature approval requests, unhelpful requests, repeated requests, final task success, and fixed-composite `R`.

The legacy field `first_valid` is not used as the strict first-step measure: it treats an approval-first request as valid when addressed to the approver. The corrected strict outcome is reconstructed from event traces.

## Hypotheses and comparisons

- H2a: R1 improves strict first-step validity and valid-path completion compared with R0.
- H2b: R2 improves these outcomes compared with R1 when the semantic facts are matched.
- H2c: R0→R1 and R1→R2 effects vary by aligned/separated task configuration.
- H2d: role information changes knowledge and authority errors; these error types are analyzed separately.

Primary contrasts are paired within task template and model configuration. Report absolute risk differences or mean differences with template-cluster bootstrap 95% intervals. Use exact sign-flip tests at the template level for paired contrasts; apply Holm correction across the predeclared primary outcome/contrast family. Treat the two model IDs as fixed configurations and show model-stratified estimates. No claim of population-level model-family superiority.

The 14 workflow-template clusters, not the 168 episodes, are the main independent sampling units for uncertainty. The interrupted three-repetition collection produced a small number of extra v0.4 records, including new-template episodes. They remain preserved but are classified as an exploratory harness/protocol pilot and excluded from the 168-cell confirmatory replication. The 12 new templates are not used to claim confirmatory effects in Study 2.

## Historical data handling

All earlier raw rows and traces, including 44 duplicate planned-cell rows, remain unchanged. Historical confirmatory primary summary uses one first-appended record per planned cell; a sensitivity summary uses per-cell means over all retained attempts. Historical R1/R2 estimates are labeled confounded because old R2 profiles omitted organization-domain information present in R1. Historical results are not pooled with v0.4 for the clean format contrast.

## Quality checks and exclusions

- Validate semantic parity and absence of gold-answer leakage in R1/R2 before analysis.
- Run the eight deterministic evaluator boundary cases and require all to pass.
- Recompute run-level outcomes from event traces and compare them with stored fields.
- Preserve incomplete/error runs and report counts; no post hoc deletion based on outcome.
- Report duplicate cells without deleting source rows.

## Known limitations

The environment is a synthetic text simulator with fixed query costs, four candidates, deterministic NPC behavior, and two Codex-hosted model configurations. It does not establish behavior in deployed organizations or under human response variability. The primary estimand is end-to-end help-seeking under a common task setup; it does not isolate a fixed-trigger “whom-only” decision.
