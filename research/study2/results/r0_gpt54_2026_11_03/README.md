# Study2.1 R0: GPT-5.4, 60 paired tasks

This independent package contains **60 unique attempts, 728 API calls
(626 Agent / 102 NPC), and all 60 raw and semantic evaluations**. Nothing
replaces the original R1 results or the mini repeat.
The frozen completion report predates this publication; its final "not pushed"
statement describes that historical checkpoint, not the status of this release.

## Entry points

- [Final Chinese report](Study21_R0_Final_Report_CN.md)
- [60-row R0/R1 comparison](evaluation_v1/R0_R1_Paired60.csv)
- [Semantic adjudications](evaluation_v1/adjudications.json) and
  [direct review decisions](review_decisions.json)
- [Episode index](evaluation_v1/episode_index.csv) /
  [call index](evaluation_v1/call_index.csv)
- [Budget provenance](evaluation_v1/budget_provenance.json)
- [Source-to-public mapping](manifest.json) /
  [redaction manifest](redaction_manifest.json)
- [Archive-only replay verification](PUBLICATION_VALIDATION.json)

From a clone, using existing Python (standard library only):

```powershell
python research\study2\results\r0_gpt54_2026_11_03\tools\verify_r0.py
python research\study2\results\r0_gpt54_2026_11_03\tools\verify_r0.py --extract .\r0-evidence
```

Use a new extraction directory. The verifier recomputes **all 60 raw scores and
all 60 semantic scores**, checks contacts/costs, models, full Agent history across
NPC calls, directory retention, all 728 settlements, archive inventories and hashes.
No service, download or model call is needed.

Five ZIPs preserve the complete available evidence in its relative layout:
`frozen_stage/runner/episodes/r0_gpt54/<task>/` contains actual API request/response
messages, timestamps/IDs, tool calls/results, send/read relations, conversations,
outputs, usage, manifests and raw grading. `task_inputs/` contains frozen task,
public/gold, costs, graders, R0/R1 directories and organization inputs;
`frozen_stage/` retains the exact runner and NPC implementation.
`review_inputs/` retains the actual content inspected by the reviewer.
The source manifest covers 3,342 research files. Only one bytecode file and
one credential-loading PowerShell bootstrap are excluded; no research record is
omitted. Archived controllers are provenance, **not instructions to resume a
sealed queue**. Fresh online reproduction requires fresh credentials, explicit
scope/budget approval and a fresh isolated queue; none is performed by these tools.

## Results and schema

R0 content/reference pass: **54/60** (Must **26/30**, Optional **28/30**).
Mean T **0.800000**; mean old R **0.581667**. Frozen GPT-5.4 R1 pass is
50/60 (21 Must, 29 Optional). R1-to-R0 transitions: 48 pass/pass, 2 pass/fail,
6 fail/pass, 4 fail/fail. This single nonrandomized comparison does not establish
that R0 is better.

The comparison CSV keys each task to both episode IDs; it separately retains
`R0_business`, `R1_business`, T/Q/R/C/Nauth/Nwaste, original raw status/T/R,
terminal state, actual contacts/first recipient, Agent/NPC counts, USD, evidence
paths and rule version. `adjudications.json` adds actual semantic projections,
field matching, actual message-bound contact labels and independent NPC/data issues.
Use the final `R0_R1_Paired60.csv`; partial/checkpoint tables are historical.

Scoring is `semantic-content-pending-truthful-extra-v3-r0-v1`. Correct content
recoverable by a human passes despite formatting or correct extra detail.
An honestly pending preparation does not invent a requirement to obtain approval;
false claims of approval, missing/current-value errors and contradictions remain
distinct. Must T uses original atomic fields. Optional uses the existing legal
baseline/full fieldwise alternatives, `T = 0.5 + 0.5 Q`, with Q bound to
actually read and adopted optimization evidence. A legal hybrid reference pass
does **not** certify real-world feasibility or fully optimized cost.

Old `R = T - 0.05 C - 0.3 Nauth - 0.1 Nwaste`, without clamping.
C is delivered role-contact cost, not API USD. Original role/authorization
proxies and reviewed redundancy labels are disclosed. NPC gate deviations are
independent of Agent content. **R-prime has not been computed**; the full
dialogues, role costs, private prerequisites and contact IDs are preserved for
subsequent offline analysis. Review was nonblind AI review, not a paid judge or
a new direct user adjudication of every R0 output.

## Conditions, limitations and accounting

Agent: `gpt-5.4-2026-03-05`; NPC: `gpt-5.4-mini-2026-03-17`, frozen v6.
Reasoning none, Agent/NPC output 2048/1024, 64 Agent steps, the same original
32768 UTF8-byte input guard, prompt, eight tools and full history as GPT-5.4 R1.
Only the public directory changes to names plus generic titles; genuine teams
in titles remain. Candidate pools are preserved (4/8/16 people in 20/18/22 tasks).
Public owner/policy/OOO clues and private facts/capabilities do not change.
Learning duties through an actual paid contact is still possible in R0.

`o-high-eval-budget` retains its known gold-validity caveat: 12/300 and five
cached results do not uniquely determine 7/170/510. The observed 7/175/525
equal-cost estimate is arithmetically correct. The frozen reference failure is
retained; sensitivity excludes this task: **54/59**, T **0.813559**,
old R **0.592373**. Numerical evaluation gaps are zero; gold validity is not
therefore universally established. NPC stochastic behavior, gate deviations,
execution period and nonblind judgments limit causal interpretation.

R0 ledger USD **1.97668125**. Shared history: settled **9.30539035** plus
five unchanged unknown reserves **0.11172275** = occupied **9.41711310 / 20**.
No new unknown, extra attempt, automatic rerun or R-prime calculation.
Accounting follows existing usage price rules, including the historic NPC
input convention; it is not invoice reconciliation. Budget provenance includes
all 1,456 new reserve/settle events and the preserved five unknown records.

Credentials/private runtime endpoints and machine paths are removed only from
publication copies. `manifest.json` binds original source hashes to public hashes;
the redaction manifest records types and file mappings without secret values.
Research task aliases and synthetic authorization references are not credentials.
Old source hash fields intentionally describe pre-redaction bytes; use
`published_sha256` for extracted-byte validation.

No dependency downloads/CDN access are required for publication or replay.
The historical user-observed CDN request's specific origin remains unverified;
this is not a claim about every background process on the host.
