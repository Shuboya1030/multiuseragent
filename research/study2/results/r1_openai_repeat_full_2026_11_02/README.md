# Study 2.1 R1: independent mini repeat and GPT-5.4 full control

This package contains **90 new attempts**, not replacements for the original
180 slots / 243 attempts in [`../r1_2026_11_02`](../r1_2026_11_02/README.md).
All available new research records are included as sanitized, source-hashed
copies. No study model calls, paid judges, or R-prime calculations are required
to inspect this package.

## Start here

- [Final Chinese evaluation](GPT54_Full60_Final_Evaluation_CN.md)
- [Mini repeat report](Mini_Must30_Repeat_Result_CN.md)
- [Full 60-task comparison CSV](derived_full_v1/GPT54_Full60_Comparison.csv)
- [Same-v6 Must 30 paired CSV](derived_full_v1/Same_V6_Must30_Pairs.csv)
- [All 90 attempt index](derived_full_v1/All_90_Attempts.csv)
- [Full content adjudications](derived_full_v1/adjudications.json)
- [Mini content adjudications](derived_mini_v1/adjudications.json)
- [Evaluation completion manifest](evaluation_completion.json)
- [Public-copy verification](PUBLICATION_VALIDATION.json)

| Group | Scope | Business pass | Mean T | Mean old R |
|---|---:|---:|---:|---:|
| Mini independent Must repeat | 30 | 2/30 | 0.261667 | 0.203333 |
| GPT-5.4 full Must | 30 | 21/30 | 0.833333 | 0.566667 |
| GPT-5.4 full Optional | 30 | 29/30 | 0.697222 | 0.648889 |
| GPT-5.4 full total | 60 | 50/60 | 0.765278 | 0.607778 |

All 90 attempts were actually run, exported and directly reviewed. No unreviewed
episodes or numerical T/R gaps remain. **One gold-validity issue remains
explicitly flagged**, not silently resolved: `o-high-eval-budget` has optimized
reference 7 benchmarks / 170 GPU hours / USD510, but its public documents and
private cache-count record do not specify the runtime allocation needed to
derive 170. The Agent's 7/175/525 equal-weight estimate is arithmetically
consistent. The frozen-reference failure/T0 is retained; it is not proof of
Agent arithmetic error. Excluding this flagged task yields full 50/59 (84.75%),
Optional29/29; this is a sensitivity analysis, not a replacement score or
best-attempt selection.

## Files, archives and reproducibility

The five archives contain logical paths recorded in `manifest.json`:

| Archive | Contents |
|---|---|
| `archives/mini_repeat.zip` | All 30 mini episodes, under `evidence/<episode_id>/` |
| `archives/gpt54_control.zip` | All 60 full episodes, same episode namespace |
| `archives/review_inputs.zip` | Complete review packets and readable actual-answer evidence |
| `archives/analysis_inputs.zip` | Frozen 60 public/gold/DAG/task definitions, organization, role costs and scorer |
| `archives/context.zip` | Actual frozen runtime/NPC/controller source, scope/configuration snapshots and histories |

The **1,844 episode files** include full API request/response wires, tool
arguments/results, messages, send/read linkage, IDs/timestamps, workspace files,
usage, manifests, raw evaluations and episode audits. Analysis inputs include
all 60 frozen task definitions and public R1 documents. The credential-loading
`launch.ps1` is deliberately excluded: it is not research payload and should
not be shared.

From this directory, using Python standard library only:

```powershell
python tools\verify_new.py
python tools\verify_new.py --extract unpacked
```

Extraction requires a new/empty destination; it never overwrites a source.
Verification reads ZIP entries directly, validates every public hash, recomputes
all 90 raw scores, checks coverage, credentials and accounting, and needs no
model/API/service access. ZIP paths and CSV/JSON evidence references are logical
dataset-relative paths. `unpacked` is an optional materialization of them.
The sibling historical package has its own `tools\verify_bundle.py`; use its
bundle reader/archive index for historical episode references.

`manifest.json` maps each source file to its public target/archive, original
SHA and sanitized SHA. `redaction_manifest.json` records field-type reasons and
file mappings, never secret values. Original session evidence was read-only.
Published absolute machine paths, credential fields/headers and unnecessary
runtime endpoints were removed or converted to logical references. Synthetic
task roles, gold facts, authorization references and research payload were not
treated as real credentials.

Raw and derived versions remain separate. The original execution
`context/runner/progress.json` still records "semantic review pending" at
controller exit; the current completion state is `evaluation_completion.json`
and the derived tables, not that preserved historical snapshot. The old
four-case incremental review is also retained as history, not the final score
entry point.

## Columns and scoring

The 60-row CSV keys are `task_id`, `help_class`, `group`, `new_episode_id`.
`full_business`, `full_T/Q/R/C/Nauth/Nwaste` are the new independent semantic
results. `raw_terminal`, `raw_evaluation_status`, `raw_T/R` are unchanged
operational results. Original/latest mini episode and score columns refer to
the prior frozen package; `repeat_mini_*` is present only for Must tasks.
`same_v6_repeat_pair` identifies the 30 contemporaneous pairs. `source`, `review`,
`reason`, `issues`, `rule_version` bind evidence and qualifications.

The rule version is `semantic-content-pending-truthful-extra-v3-full-v1`
(mini has its independent repeat version). It is **nonblind offline AI content
review**, with no new paid judge. The prior five user decisions remain in the
old package and were not copied as user adjudications of these new episodes.
Content-equivalent lists/counts, descriptive names, UTC representations,
historical conflicts on an abandoned date and correct extra modules are
accepted; missing or wrong facts are not filled from gold.

- Must T: fraction of correct gold atomic fields.
- Optional T: `0.5 + 0.5*Q` when the base contract is valid; otherwise0.
- Optional Q: supported, adopted optimized fields divided by fields differing
  from the legal baseline, under the original fieldwise definition.
- Old R: `T - 0.05*C - 0.3*Nauth - 0.1*Nwaste`.
- C: per-message delivered-contact role cost, not API dollars.
- Nauth/Nwaste: unchanged old-role proxies, independently reviewed against the
  actual contact. Useful clarification/repair is not mechanically duplicate
  waste, nor does task success erase costs or wrong-role approval requests.

Business, atomic/quality score, contact cost and NPC problems are separate.
Preparing a request can pass with complete seeking of approval or explicit
pending status when public instructions do not demand an actual grant; private
DAG conditions are not invented as additional business obligations. Fieldwise
Optional Q can credit partial/hybrid plans without actual cost reduction:
the final report explicitly discloses interview/license/launch limitations.

## Conditions and comparison boundaries

Agent snapshots: mini `gpt-5.4-mini-2026-03-17`, full
`gpt-5.4-2026-03-05`. NPC always mini with frozen
`controlled_rest_conversational_repair_v6`. Both groups retain identical
public tasks, initial system/user prompting, directory, eight generic tools,
64 decisions, none reasoning, 2048 Agent / 1024 NPC output, auto tools,
parallel false and complete history. Temperature/API seed are omitted;
instance seeds retained. All thirty Must first wires differ only in the Agent
model. The original conservative UTF-8 byte input gate is retained; this is not
a new accurate tokenizer or input waiver.

Only new mini Must30 vs full Must30 is a contemporaneous same-NPC paired
comparison: fail-to-pass19, pass-to-pass2, fail-to-fail9. Full Optional vs
historical mini Optional is a different period/NPC stratum. Serial order,
single attempts and stochastic NPC replies limit causal interpretation.
Do not pool these rows into a fair three/four-model ranking.

Mini repeat is not a uniform third run: only four Must tasks have
original+targeted repair+repeat;26 have two attempts, and original model-release
had no actual Agent request. Historical mechanisms differ. No additional sealed
random replicate, extra pilot, best-attempt replacement, R0/R2 run or R-prime
computation occurred.

NPC issues are independent flags: invented traveler-name gating, incorrect
scope approvals, missing citation checks, a mandate before readiness, and
calendar wording contradictions. Correct final content is not erased merely
because an NPC has a separate problem, and task success does not certify that
every simulator precondition was faithfully enforced.

## Fees and preserved budget

Mini247 Agent+10 NPC calls cost USD0.30682500; full591 Agent+85 NPC calls cost
USD2.19931925. New total **933 calls / USD2.50614425**, with no new unknown.
Full prices per million are uncached2.50 / cached0.25 / output15.00; mini retains
the historical uncached-input accounting rule. Usage/cached/reasoning counters
are preserved. Accounting estimates are not vendor-invoice reconciliation.

The shared whole-history ledger is included: settled7.32870910 plus the
**original five unknown reservations0.11172275**, occupied7.44043185 / cap20.
There is no new USD20 allocation per group. The 26 local read-only HTTP429
retries were not paid generation replays. All 933 calls and settlements,
complete wires/history, 5,640 historical source hashes and ledger/pacer prefixes
were verified; the publication checker separately checks the sanitized copies.
