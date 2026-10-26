# Paper 0 Skeleton: AAAI-27 HAIC Workshop (living document)

> Target: AAAI-27 Workshop on Human-AI Collaboration (full paper, ≤ 8 pages + references, AAAI two-column). Deadline 2026-11-20 AoE.
> Roles: **this document = paper structure and analysis plan**. Task generation and experiment runs are done by the experiment agent (see `12_Study2_Task_Redesign_*.md`). Result slots are marked `[RESULT: …]` and filled as runs complete.
> Analyses are phrased as **questions**, not expected outcomes. Any result, including 100% success, is reported as found.

---

## 0. One-sentence story

When an AI agent is shared by a team, getting help is not one decision but two coupled ones — **when** to involve a person and **whom** — and the second becomes a multi-step, rule-governed problem as organizations grow; we build a controllable, TAC-compatible task suite to measure where agents succeed and fail along this process.

## 1. Working title options
1. *Whom Should the Agent Ask? Measuring Role-Aware Help-Seeking in Multi-User Workplaces*
2. *When and Whom to Ask: Help-Seeking Decisions of LLM Agents in Shared Organizational Settings*
3. *Beyond Single-Principal Agents: A Benchmark for Role-Aware Help-Seeking*

## 2. Contributions (as they will be claimed)
1. **Problem formulation.** Help-seeking in multi-user agent systems as a joint *when/whom/order* decision over principals with distinct knowledge and authority; a taxonomy of help-seeking errors (wrong person, wrong order, missing context, no repair, silent failure, over-asking).
2. **Task suite.** A controllable set of workplace tasks (must-ask / optional / no-help) with structural difficulty knobs (candidate pool size, dependency depth, knowledge–authority separation, hard distractors, inference type), built on TheAgentCompany's organization and exportable to its runtime.
3. **Empirical study.** How current LLM agents' help-seeking changes with organizational scale, dependency depth, and available role information; where in the process failures concentrate.

## 3. Section outline and page budget (8 pages)

| § | Section | Pages | Content | Status |
|---|---|---|---|---|
| — | Abstract | — | Problem → gap → suite → 2–3 headline findings | Write last |
| 1 | Introduction | 1.0 | Shared agents are common; single-principal assumption; help-seeking is part of task execution; when + whom are coupled and affect quality; contributions | Draftable now (from proposal §1) |
| 2 | Related Work | 0.75 | When-to-ask HAC (ReHAC, Learning to Ask, KnowNo); multi-user/multi-principal agents; multi-expert L2D; proactive agents; enterprise benchmarks; human–agent teaming. **Comparison table** | Draftable now (proposal §2 + patterns doc) |
| 3 | Problem Formulation | 0.75 | Principals and role profiles; help-need classes; gold step DAG; metrics; error taxonomy | Draftable now |
| 4 | Task Suite | 1.25 | Why existing benchmarks don't measure it (TAC audit); design principles; difficulty features and distribution; validity checks; TAC compatibility | Partly now; stats after generation |
| 5 | Experimental Setup | 0.5 | Models, conditions, runs, evaluation, cost | After protocol frozen |
| 6 | Results | 2.5 | RQ1 when · RQ2 whom × scale · RQ3 order × depth · RQ4 role information · error funnel | After runs |
| 7 | Discussion & Limitations | 0.75 | Deployment implications; finance/legal angle; simulation vs. reality; limitations | After results |
| 8 | Conclusion | 0.25 | Summary + future work (learned policy, team structure, human study) | Last |
| — | Appendix (if allowed) | — | Task examples, prompts, full tables | — |

## 4. Section-by-section notes

### §1 Introduction (paragraph plan)
1. Agents are becoming shared team infrastructure (enterprise copilots, team chat assistants) → cite Brachman 2025, Counts 2026, O'Hara 2026.
2. But agents are built for a single principal (Yang, Zhu et al. 2026); other people are information sources, not collaborators with roles.
3. Workplace tasks require human input — missing facts, ambiguous rules, approvals; help-seeking is part of execution (TheAgentCompany ~30%; ReHAC's conditional automation).
4. In multi-user settings help-seeking is two coupled decisions; failures: asking the wrong person, asking in the wrong order, not asking and guessing, asking unnecessarily. Prior work covers *when* with a single interchangeable human.
5. **Motivating example** (Figure 1): purchase above a threshold → need quote details from requester, budget from finance, approval from director (owner on leave → delegate).
6. Contributions (3 bullets) + headline findings `[RESULT]`.

### §2 Related Work
- Use the comparison table from `05_Related_Work_Writing_Patterns_*.md` §5 (columns: multiple humans / decides when / decides whom / roles & authority / multi-step). Verify ✓/✗ against originals.
- Each paragraph ends with the gap sentence (pattern doc rules).

### §3 Problem Formulation
- Principal set 𝒰; role profile ⟨knowledge, authority, cost, availability⟩.
- Help-need classes: **must** (task cannot be completed correctly without a person), **optional** (asking can improve quality), **no-help** (all needed information is available).
- Gold step DAG G = (S, ≺); admissible recipients A_s per step.
- Metrics: help rate, first valid contact, DAG-consistent completion, order violations, repair rate, silent failure, over-ask, interruption cost, artifact correctness.
- Error taxonomy table (wrong-person / wrong-order / missing-context / no-repair / referral-ignored / redundant / silent-failure / over-ask).
- Objective R as a descriptive summary only (no weight tuning claims).

### §4 Task Suite
- **4.1 Why a new suite.** Audit of TAC's 40 NPC tasks: in 24/40 the task text names whom to contact; contacts are instructed rather than self-initiated → existing traces measure instruction following. (Short table: TAC NPC tasks by type of contact.) This replaces the old "Study 1 trajectory diagnosis" as motivation.
- **4.2 Design principles.** Reasoning not matching; realistic directory baseline; embedded (not announced) need for help; orthogonal difficulty knobs.
- **4.3 Difficulty features and distribution.** Table: features → points; distribution by class × level `[RESULT: final counts]`.
- **4.4 Validity checks.** Wording-overlap check; no-contact baseline; oracle solvability; unique answer; realism review `[RESULT]`.
- **4.5 TAC compatibility.** Same blueprint exports to simulator and TAC task package; subset run in TAC `[RESULT: agreement]`.

### §5 Setup
- Models: low-cost main set (Claude Haiku 5.5, GPT-5.4-mini, Kimi-k2.6) + Claude Sonnet 5.5 on a subset `[confirm]`.
- Conditions: N ∈ {4, 8, 16}; d ∈ {1, 2, 3}; profile R0 (directory) vs R1 (directory + role/authority documents); help-need class.
- Reps, temperature, turn limits, total episodes and cost `[RESULT]`.

### §6 Results — see §5 of this document for the analysis plan.

### §7 Discussion
- Implications: organizational metadata as agent infrastructure; escalation policies; where to put human checkpoints.
- Workshop focal domains: finance (spending thresholds, approvals) and legal (sign-off authority) — tie examples to these.
- Limitations: simulated colleagues (LLM/rule NPCs), stipulated costs, one synthetic organization, model set, no human participants.

## 5. Analysis plan (what to compute and show)

Each analysis is tagged with the figure/table it produces and its priority for the 8-page version.

| # | Question | Analysis | Output | Priority |
|---|---|---|---|---|
| A1 | **When:** do agents ask when they need to, and refrain when they don't? | Help rate by help-need class × model; silent-failure rate in must; over-ask rate in no-help; benefit of asking in optional | **Fig 2** heatmap (class × model) + small table | Must |
| A2 | **Where does the process break?** | **Error funnel** per episode: needed help → asked → reached a valid recipient → correct order → request carried needed context → repaired after rejection → correct artifact. Report conversion at each stage | **Fig 3** funnel/Sankey by model | Must (core figure; generalizes the "finding the right person ≠ completing the process" finding) |
| A3 | **Whom × scale:** how does recipient selection change as the candidate pool grows? | First valid contact and contacts-before-first-valid vs N ∈ {4,8,16}, by profile; length-matched control; gold position effect | **Fig 4** line plot with CIs | Must |
| A4 | **Order × depth:** how does multi-step dependency affect completion? | DAG-consistent completion vs d; order-violation types (premature approval, skipped prerequisite); repair-after-rejection rate | **Fig 5** stacked bars by d | Must |
| A5 | **Which structural features matter most?** | Mixed-effects logistic: success ~ N + d + separation + #hard distractors + inference type + profile + model + (1 \| template) | **Table 3** coefficients (odds ratios) | Should |
| A6 | **Which distractors mislead?** | Confusion: for wrong contacts, which distractor type was chosen (near-miss authority, stale role, delegated, stale fact, referrer, plausible title) | **Fig 6** bar or confusion matrix | Should |
| A7 | **Value of role information** | R1 − R0 on first valid contact, completion, authority violations, cost; by difficulty level | Table or panel in Fig 4 | Should |
| A8 | **Cost of help-seeking** | Queries, interruption cost, tokens per successful task by model × condition | Small table | Could |
| A9 | **Cheap vs strong model** | Sonnet 5.5 vs Haiku 5.5 on the subset: do the same failure patterns persist? | One row/panel | Could |
| A10 | **Simulator vs TAC agreement** | Same tasks in both runtimes: agreement on outcome and error type | One sentence + appendix table | Could (strengthens validity) |
| A11 | **Qualitative cases** | 2–3 annotated traces: premature approval → rejection → no repair; asked a stale-role colleague; silent failure with stale value | Boxed examples | Must (1 case in main text) |

**Statistics conventions.** Template is the unit of inference; template-clustered bootstrap CIs; mixed-effects models with template random effects; report effect sizes and CIs, not only p-values; per-model results described as configuration-specific, not model-family rankings.

## 6. Figures and tables plan (main text)

| ID | Content | Section |
|---|---|---|
| Fig 1 | Motivating scenario: shared agent, colleagues with roles, when/whom/order decisions | §1 |
| Tab 1 | Comparison with prior work | §2 |
| Tab 2 | Task suite: difficulty features + distribution | §4 |
| Fig 2 | When: help rate by class × model | §6 |
| Fig 3 | Error funnel | §6 |
| Fig 4 | Scale: first valid contact vs N (± role info) | §6 |
| Fig 5 | Depth: order errors and completion vs d | §6 |
| Tab 3 | Feature-level regression (if space) | §6 |

## 7. What already exists vs. what is needed

| Item | Status | Source |
|---|---|---|
| Intro / related work text | Draft exists | `01_PhD_Research_Proposal_*.docx` §1–2 |
| Related-work comparison table | Draft, needs verification | `05_Related_Work_Writing_Patterns_*.md` |
| Formulation and metrics | Exists | proposal §4; `12_…` §5 |
| TAC audit (24/40 named) | Exists | `03_Feasibility_Pilot_*.md`; `11_Study1_Coding_…` |
| Earlier evidence: "right person ≠ completed process", optional-ask differences | Exists (Study 2.1, old task design) | `research/study2/study2_1_taskset/analysis/` — use only as pilot evidence or drop once new results arrive |
| New task suite + runs | Assumed done (experiment agent) | `12_Study2_Task_Redesign_*.md` |
| AAAI-27 LaTeX template | Not set up | — |

## 8. Open questions for the authors
1. Lead framing: benchmark paper (contribution = suite) or findings paper (contribution = empirical results)? Default: findings-led, suite as enabler.
2. Keep the objective R in the paper or report only component metrics?
3. Include Study 2.1 old-design results at all, or rely only on the new suite?
4. Single author or with collaborators (affects writing split and endorsement for arXiv).

## 9. Change log
| Version | Change |
|---|---|
| 20261026-1353 | Skeleton: story, contributions, outline with page budget, section notes, analysis plan A1–A11, figure plan, status table, open questions |
