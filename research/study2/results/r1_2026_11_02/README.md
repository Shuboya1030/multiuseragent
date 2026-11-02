# Study 2.1 R1: analysis handoff

This directory is a self-contained, sanitized publication of the R1 research
records, not a new experiment or a runner deployment. A clone is sufficient
for offline analysis. No credentials, original Windows paths, external session
directories, package downloads, or live services are required.

## Start here

| File | Purpose |
|---|---|
| `evaluation/R1_All_180_Slots.csv` | One row per original task/model slot; original results, every authorized repair, and last-authorized display result. |
| `evaluation/All_243_Attempts.csv` | Flat attempt index with raw and semantic scores, process components, evidence, and reviewer provenance. |
| `evaluation/all_attempt_evaluations.json` | Full structured evaluations, semantic projections, bound message reviews, and user adjudications. |
| `evaluation/summary.json` | Separate original and last-authorized aggregates. |
| `evaluation/R1_Final_Coverage_Evaluation_CN.md` | Current Chinese coverage and evaluation report. |
| `evaluation/Five_Gap_Termination_Correction_CN.md` | Correction of the superseded five-gap conclusion, with actual final provider responses. |
| `evaluation/Current_Display_Gaps.csv` | Current scoring gaps: **zero**, with header retained. |
| `evaluation/All_Attempt_Gaps.csv` | Historical censoring and independent NPC interpretation uncertainty; not current missing evaluations. |
| `manifest.json` | Every source-to-published file mapping and both SHA-256 values, archive membership, and implementation provenance. |
| `redaction_manifest.json` | Per-file redaction reasons/counts, without credential values or private local paths. |
| `PUBLICATION_VALIDATION.json` | Offline publication verification results. |

The latest evaluation supersedes earlier reports in `history/`; in particular,
the old statement that five current slots were unevaluable is **not current**.
Those agents ended normally, rather than experiencing transport failure.

### Offline verification and extraction

Run from the repository root with Python 3.10+ and its standard library:

```powershell
python research\study2\results\r1_2026_11_02\tools\verify_bundle.py
python research\study2\results\r1_2026_11_02\tools\verify_bundle.py --extract .\r1_analysis_materials
```

The optional extraction destination must be new or empty. Verification reads the
archives directly and checks source provenance, all records, raw score
reproduction, semantic score arithmetic/recomputation, chain selection, budget,
and file safety. It does not contact a model, count tokens, start services, or
run experiments. Extraction materializes portable references such as
`packets/<attempt-id>.json` and `evidence/<episode-uuid>/trace_bundle.json`.
Forward slashes in stored references are portable path separators; the commands
above use Windows syntax.

## Study scope and denominators

R1 has **60 tasks x 3 model labels = 180 original formal slots**. There are
**63 authorized repair attempts covering 61 slots**: the primary session's
55 attempts, six independent Kimi attempts, and two additional authorized
attempts for technical failures. All **243 episodes** are retained.
There are no R0 or R2 results in this handoff.

| View | Business pass | Business fail | Technically censored / unevaluable | T/R available |
|---|---:|---:|---:|---:|
| Original 180 only | 115 | 54 | 11 | 169/180 |
| Last explicitly authorized attempt per slot | 133 | 47 | 0 | 180/180 |

In the display view, OpenAI has 32 pass / 28 fail, Haiku has 51 pass / 9 fail,
and Kimi has 50 pass / 10 fail. These are **not fair cross-model rankings**:
repairs were targeted at selected exceptions, not independently resampled.
Never silently replace the original experiment with this mixed display view.
The selection rule is the last attempt in the preauthorized chain, **not the
highest score**. There are 119 unrepaired slots, 59 one-repair chains, and two
two-repair chains.

There are 230 attempts with derived numeric T/R and 13 historical censored
attempts. Censoring includes recorded runtime/protocol/transport and research
input-safety interruptions, not just provider faults. Raw scores, partial work,
and the exact recorded interruption remain available; censored attempts have
not been assigned invented semantic zeros. A separate historical NPC
extra-disclosure interpretation question does not make business or T/R unknown.

## Table schema and evidence

The master table key is `(provider, task_id)`. `original_episode_id` identifies
the formal attempt; `original_raw_state`, `original_raw_T/R` preserve runtime
results. `original_historical_prior_review` retains the earlier review;
`original_business` and `original_semantic_T/R` are the current review of the
original attempt. `authorized_repair_chain` is a JSON array, not a single
replacement score. `display_episode_id`, `display_attempt_order`, and
`display_condition` identify the last authorized attempt.

The attempt index includes `phase`, `attempt_order`, original/predecessor IDs,
`raw_T/R`, `business`, `derived_T/R`, `quality_Q`, `C`, `Nauth`, `Nwaste`,
`weights`, `npc_status`, `score_projection`, `projection_notes`,
`field_assessments`, `bound_evidence_reviews`, `user_adjudication`, and evidence
references. Complex CSV cells contain JSON. Use a CSV parser, not line counting.
The structured JSON also contains the full original-formula result.

Each packet contains the actual public instructions, frozen task blueprint and
documents, private gold/baseline/DAG, actual workspace, complete available tool
and conversation records, errors/status, raw evaluation, and prior review.
The original run directories are separately preserved in the evidence archives,
including complete available API request/response payloads, tool events,
messages, normalized usage, manifests, final outputs, and error records.
For an interrupted attempt, absent exports remain absent; no output is invented.

Task definitions are frozen once per task under `tasks/` in `archives/tasks.zip`,
including blueprint, scenarios, exact scorer, and role costs. These deliberately
do not depend on potentially different task files elsewhere in the checkout.
Individual packets repeat the exact relevant blueprint for auditing convenience.
Source payload hashes in `manifest.json` distinguish originals from sanitized
publication bytes. Published hashes, not original hashes, verify sanitized files.

## Scoring and adjudication

Business completion, optional quality, process cost, and NPC errors are separate
axes. The current content rule is: a human must be able to recover all required
gold information accurately and unambiguously from the actual answer. Equivalent
lists/counts, dates, names, and correct additional details do not fail solely
because of formatting. Missing, contradictory, or wrong facts are not supplied
from gold. A legitimate Optional baseline can pass without attaining every
optimization.

For public preparation tasks that do not require completed approval, a complete
approval request **or explicit pending** satisfies approval behavior; pending
does not require an NPC reply. Real references/names are not proof of actual
authorization. Private DAG requirements cannot create hidden public obligations.
Approval-related symbolic score projections are disclosed and must not be read
as evidence that someone actually signed. Actual private-DAG satisfaction remains
a separate field.

Original score definitions and weights remain:

- Must-help: original atomic field accuracy; genuine normal non-submission uses
  the original scorer's T=0 branch, rather than being classified automatically as
  a technical unknown.
- Optional-help: valid base plus supported optimization fraction Q gives
  `T = 0.5 + 0.5*Q`; a failed base gives 0. See the frozen scorer for exact
  baseline, shared-field, and evidence-release conditions.
- `R = T - 0.05*C - 0.3*Nauth - 0.1*Nwaste`.
- C is the sum of role-weighted **every contact**, not distinct people.
  `Nwaste = wrong_person + redundant` follows the old DAG definition.
  Clarification can be useful in ordinary language while still being redundant
  under that old benchmark. Nauth is the old request-based metric, not proof
  of an actually issued unauthorized approval.

**R-prime has not been computed.** Weights were not changed to raise scores.
Strict/raw evaluation remains independent of semantic projections.

Five binding user decisions are retained with the original user statements and
versioned calculations in `adjudications/` within `archives/history.zip`:

| Model/task | T | R |
|---|---:|---:|
| Haiku / o-high-security-training | 1 | 0.95 |
| Haiku / o-med-batch-schedule | 0.75 | 0.70 |
| Haiku / o-med-usability-budget | 1 | 0.95 |
| Kimi / o-med-browser-matrix | 1 | 0.65 |
| Kimi / o-med-offsite-date | 1 | -3.10 |

All other semantic decisions are **non-blind AI reviews**, not independent
human judgments or a paid blind judge study. The conference-travel correction is
an AI application of the user's general content/pending rule, not a sixth
individual user adjudication. It has T=1/R=0.70 despite not saving JSON: the
actual final text gives the current facts and pending approver context.
The private DAG does not certify completed approval.

## Conditions, NPC changes, and cost

Do not treat all attempts as having identical conditions. Read each run's
`run_manifest.json`, `condition`, model IDs/versions, timestamps, NPC backend,
implementation hashes, actual prompts/responses, and the repair authorization
records. The original formal NPC implementation and the subsequent natural
language/post-hoc interpretation and repair rule changes are preserved in
`provenance/` and per-attempt records. Implementation files are stored by their
original SHA-256 where available, with an explicit missing-hash list rather than
an assumed substitute.

The six independent Kimi repairs plus the two technical additions used an
explicit **local input-gate waiver**. They did not validate accurate preflight
token counting. Their observed input sizes do not retroactively repair the
counting method. The primary 55 repairs used their recorded original input gate.
NPC issues are independently recorded and were not automatic reasons to rerun.

The shared stage ledger's final settled amount is **USD 4.82256485**. Five
historical unresolved reservations total **USD 0.11172275**, so occupied budget
is **USD 4.93428760 / 20**, not a claim that the unknown requests were free or
settled. This is cumulative stage accounting, including earlier preparation/
pilot/judge activity, **not just the cost of the 180 formal episodes**.
Use call IDs, episode usage, and the complete ledger to construct a desired
analysis subset. The six-run addition settled USD 0.73122825; the two technical
additions settled USD 0.06181370; neither added new unknown reservations.

## Archive layout and publication safety

`archives/<provider>-original.zip` and `archives/<provider>-repair.zip` contain
all available original run files. `archives/packets.zip` contains 243 JSON and
243 readable Markdown packets. `archives/tasks.zip` holds 60 frozen task/scorer
sets. `archives/history.zip` preserves prior reviews, five user decisions, and
the superseded publication. `archives/context.zip` holds independent-session
scope/results/reviews, source implementations, protocol, and shared accounting.

No research record is intentionally omitted. Runtime caches, dependencies,
downloaded vocabularies, live lock files, unrelated dirty checkout files, and
personal researcher context are not part of the package. Credentials,
authenticated URL material, private local paths, and unnecessary private
runtime endpoints are removed only in publication copies; reasons and file
hash mappings are in `redaction_manifest.json`. Synthetic task roles, benchmark
authorization references, gold facts, and substantive research payloads are
not credentials and are retained. The source session evidence was not modified.

This directory's `.gitattributes` disables line-ending conversion so published
file hashes remain stable across Windows and other checkouts.

The GitHub repository is public. Recheck privacy and permissions before adding
any new records. This handoff does not authorize another experiment, upload of
credentials, or publication of unrelated local files.
