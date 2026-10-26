# Study 2 Task Redesign Proposals (living document)

> This document is updated as discussion continues. Following the naming convention, the timestamp in the filename is updated on every edit to the last-modified time, and the previous version is overwritten via `git mv` (history stays in git).
> Each change is recorded in **§9 Change log**, and decisions in **§8 Decision log**.
> Sources reviewed: `research/study2/derived/study2_v04_analysis.md`, `research/study2/study2_1_taskset/` (R1 analysis report, R0 formal run), `task_blueprints_v0.4.jsonl`.
> Statements marked "hypothesis" or "estimate" are not verified.

---

## 1. Diagnosis of current problems (evidence)

| # | Problem | Evidence | Consequence |
|---|---|---|---|
| D1 | **Profiles leak the answer** | In all 52/52 v0.4 tasks, the authority wording in the task text **exactly matches** the authority field of the gold candidate's profile; 130 distractors all have expertise "general team coordination" | With R1, string matching is enough to pick the right person. R1 first contact is 20/20 correct, a ceiling effect; the R2−R1 null result cannot be interpreted |
| D2 | **R0 baseline is unrealistic** | Study 2.1 R0 titles are all generic, such as "Program Associate" and "Business Associate" | R1−R0 is artificially inflated |
| D3 | **Task structure is too thin** | 4 candidates, 1 fact + 1 approval, identical distractor composition across tasks | Small decision space; cannot study scale or multi-step order |
| D4 | **Need for help is announced** | must tasks say "Use verified information… do not guess" and "approved_by must be the colleague who has authority" | Measures instructed help-seeking, not self-initiated help-seeking under uncertainty |
| D5 | **Evaluator flaws** | must success is defined to include the contacts (circular); 10/13 no-help failures are format mismatches; meeting-room-fit has no unique answer; optional quality uses keyword proxies | Outcome variables are confounded with format and definition |
| D6 | **Insufficient sample/models** | 1 rep per cell; Study 2.1 uses only small/low-cost models | Limited generality |

**Signal worth keeping:** finding the right person ≠ completing the process (GPT requested approval first in 15/20, and 12/20 ended with missing evidence); help-seeking propensity in optional tasks differs widely (5%/90%/40%). These do not depend on D1 and point straight at the two directions the user cares about: **scale** and **order**.

---

## 2. Design principles

- **P1 Require reasoning, not matching.** The gold candidate should be inferable through organizational knowledge (rules, thresholds, delegation, reporting lines), not by repeating words from the task text.
- **P2 Realistic baseline.** R0 = a realistic directory (name + informative title + department); R1 = R0 + responsibility/authority description. A names-only condition is reported only as a lower bound.
- **P3 Embed uncertainty; do not announce it.** The task text does not say "need to verify" or "need approval". Uncertainty is planted in the data, tools, and rules. Not asking still produces a plausible but wrong output (a silent failure).
- **P4 Orthogonal difficulty knobs.** Candidate count N, distractor similarity, and path depth are manipulated independently, so effects can be attributed.
- **P5 Process-aware evaluation.** Gold is a **partial order (DAG)** over steps, not a single sequence. Evaluation separately covers who, order, request content, repair, and the final artifact.
- **P6 Pass difficulty and leakage audits before formal runs** (§6).

---

## 3. Targeted modifications

### M1 De-leak profiles (addresses D1)
- **Change:** authority/knowledge in profiles is written as **rules or scope** requiring inference, rather than repeating the task action. Examples:
  - Amount thresholds: "approves vendor contracts **under $10k**; above that goes to the Director"
  - Delegation: "Li Ming is on leave until 11/30; approvals delegated to Wang Fang"
  - Reporting line: "approvals must come from the requester's **second-level manager**" (the agent must look up the org chart)
  - Scope: "responsible for **APAC** vendor records" (and the task vendor is in EMEA)
  - Stale information: "**previously** owned payroll corrections (moved to Data team in Sept)"
- **Implementation:** each template carries a set of authority rules plus a generator that renders rules into natural language, avoiding the task's verbs and nouns.
- **Acceptance:**
  - (a) Token overlap between the gold profile and the task text is not significantly higher than for distractors.
  - (b) A **keyword-matching baseline** (pick the candidate with the highest BM25 score between profile and task) has first-contact accuracy ≤ 1.5 × random (§6).

### M2 Realistic R0 (addresses D2)
- **R0 = realistic directory:** name + informative title (e.g., "Finance Director", "Vendor Ops Specialist") + department + reporting line.
- **R1 = R0 + general responsibilities/authority scope** (without leaking task answers).
- R1−R0 is then interpreted as "the increment of richer role profiles over an ordinary directory".

### M3 Hard distractors (addresses D1/D3)
Distractor types (each task samples a subset; types and proportions are recorded):
| Type | Description |
|---|---|
| near-miss authority | Same department, authority just below threshold or for the wrong scope |
| stale role | Previously owned it, has since moved |
| delegated / unavailable | Rightful owner is on leave; must find the delegate |
| knows stale fact | Knows an **outdated** version of the fact (gives a plausible but wrong answer) |
| referrer | Doesn't know, but says "ask X" (tests whether referrals are followed) |
| plausible-title | Title looks relevant but has no actual responsibility |
| neither | Completely unrelated (current distractor type, kept as the easy end) |

### M4 Embed the need for help (addresses D4)
- Delete hint wording such as "do not guess", "must be approved", and "verified information".
- Sources of uncertainty (pick 1–2 per task):
  - **Missing fact:** a field in the work packet is empty or marked TBD
  - **Conflicting records:** two documents disagree
  - **Ambiguous policy:** a rule's applicability depends on a judgment call
  - **Permission denied:** a tool call returns `403 / requires approval from <role>`, the most natural way to trigger an authority need
  - **Preference/taste:** the output style depends on what the requester wants
- **Plausible default:** without asking, the agent can still produce a seemingly reasonable answer (e.g., using an outdated value), enabling measurement of **silent failure**.

### M5 Multi-step dependencies and order (the order direction)
- Gold path is a **partial-order DAG**, depth d ∈ {1, 2, 3, 4}. Typical structures:
  - **info → approval** (approver requires the facts first)
  - **referral chain:** A → refers to B → B gives the fact
  - **parallel info + join:** two facts from two people, then a single approval
  - **delegation:** owner on leave → delegate
  - **conditional:** if the amount exceeds a threshold, an extra approval level is needed
- NPC behavior enforces dependencies: approval requests missing prerequisite information are **rejected with a reason** (tests repair).
- Order violations are allowed (not blocked) but recorded, along with whether the agent repairs afterward.

### M6 Scale up candidates (the scale direction)
- **N ∈ {4, 8, 16, 32}**, keeping the **number of valid recipients fixed** and the distractor composition proportionally fixed.
- Two presentation modes (can be a factor or a separate sub-experiment):
  - **Full list:** all candidates are placed in context (tests long-context selection; position effects are known, see Liu et al., 2024 *Lost in the Middle*, TACL)
  - **Search tool:** `search_directory(query)` returns matching people (closer to a real enterprise directory; tests retrieval strategy)
- **Controls:**
  - Randomize order and record the **position** of gold
  - Prompt length grows with N; add a **length-matched control** (N=4 but padded with irrelevant text to match N=32's length) to separate "more people" from "longer context"
- N=17 can directly reuse TheAgentCompany's 17 roles, improving ecological validity.

### M7 Error taxonomy (process-level; refines measurement)
For each help-seeking event and each episode, label:
| Error | Definition |
|---|---|
| wrong-person | Recipient cannot advance any pending step |
| wrong-order | Violates DAG prerequisites (e.g., approval before information) |
| missing-context | Right person, but request lacks details the recipient needs (rejected) |
| no-repair | Did not correct after a rejection or referral |
| referral-ignored | Did not follow a referral |
| redundant | Asked again for information already obtained |
| silent-failure | Submitted plausible default/stale value without asking |
| over-ask | Asked in a no-need task / asked at high cost when unnecessary |

### M8 Evaluator fixes (addresses D5)
- **Report separately:** artifact correctness (canonicalized, tolerant of format differences), process validity, and approval validity. Do not hard-code "contacted someone" into the success definition.
- Canonicalization: numeric units, list/map, name ↔ ID equivalence handled by rules, with **unit tests**.
- Remove or fix tasks without a unique answer (e.g., meeting-room-fit); each task passes a uniqueness check (§6).
- optional quality: rule-based checks (whether key information appears and is correctly incorporated), replacing keyword proxies; validate against a manually labeled subset.

### M9 NPC realism
- Introduce **unavailable / delayed reply / refer elsewhere / partially wrong** responses, each with a fixed probability and fixed per seed.
- The **cost** of senior people is no longer just a number; it shows up in behavior (e.g., slow replies, "please go through your manager").
- Responses stay rule-constrained (no fabricated key facts); only surface wording varies.

### M10 Sample and models (addresses D6)
- Each cell **≥ 3 reps**; the **template** is the unit of inference.
- Models: keep the current three as a baseline, plus **at least one frontier model** (to check whether conclusions hold only for small models).
- Lock model versions, temperature, and maximum turns, and record them.

---

## 4. Experiment modules

### Exp A: Candidate scale (who × N)
| Item | Setting |
|---|---|
| Factors | N ∈ {4, 8, 16, 32} × profile ∈ {R0, R1} × presentation ∈ {full list, search tool} (presentation optional) |
| Fixed | Depth d = 2 (info → approval); fixed number of valid recipients; proportional distractor composition |
| Hypotheses (hypothesis) | **H-A1:** first-contact validity decreases with N (negative slope on log₂N). **H-A2:** the decline is driven mainly by **similar distractors** rather than count alone (N × distractor-similarity interaction). **H-A3:** R1 slows the decline (profile × log₂N interaction). **H-A4:** in the full list, accuracy is lowest when gold is in the middle |
| Main metrics | first-contact validity; valid-path completion; number of contacts before first valid contact; cost |
| Model | `valid ~ log2(N) * profile + similarity + position + model + (1 + log2(N) | template)` (mixed-effects logistic) |

### Exp B: Order and dependencies (order × depth)
| Item | Setting |
|---|---|
| Factors | Depth d ∈ {1, 2, 3, 4} × structure ∈ {info→approval, referral chain, parallel+join, delegation, conditional} (by template) × profile ∈ {R0, R1} |
| Fixed | N = 8 |
| Hypotheses (hypothesis) | **H-B1:** order errors grow with d. **H-B2:** premature-approval is the most common order error. **H-B3:** after a rejection, the rate of successful repair is limited and differs across models. **H-B4:** referral chains have the highest dropout rate |
| Main metrics | order-violation count; DAG-consistent path completion; repair-after-rejection rate; normalized path edit distance; first-error step |

### Exp C: Value of role information (re-run of the RQ2 main contrast)
- Re-run R0 vs R1 on **de-leaked + realistic R0 + hard-distractor** tasks to obtain a believable R1−R0.
- Can be crossed with N in Exp A to save runs.

### Exp D: When to ask (when, embedded uncertainty)
- Tasks: must (uncertainty planted per M4, no hints) / optional / no-need.
- Metrics: help-seeking rate, silent-failure rate, over-ask rate, help-seeking timing (step index), benefit from asking.
- This is the most novel part of RQ "when"; it can continue from Study 2.1's optional findings.

### Size and cost (estimate)
- Exp A: 24 templates × 4 N × 2 profile × 4 models × 3 reps ≈ **2,300 episodes**
- Exp B: 20 templates × 2 profile × 4 models × 3 reps ≈ **480 episodes**
- Based on Study 2.1 R0 measurements (180 episodes ≈ $0.6), even with longer prompts (N=32) and a frontier model, the **total is estimated at tens to ~$100**. The frontier model's share should be estimated separately.

---

## 5. Unified metric definitions (math)

- Gold step DAG $G_\tau=(S, \prec)$. Each step $s$ has an admissible recipient set $A_s$.
- Agent contact sequence $c_1, \dots, c_k$; each contact is matched to the pending step it advances (unmatched → wrong-person).
- **First-contact validity:** $\mathbb{1}[c_1 \in \bigcup_{s \in \text{ready}_0} A_s]$, where $\text{ready}_0$ are the steps with no prerequisites.
- **Order violations:** $V = \#\{(s, s') : s \prec s',\ s' \text{ was requested before } s \text{ was satisfied}\}$
- **DAG-consistent completion:** every step is satisfied by an admissible recipient, and the satisfaction order is a topological order of $G_\tau$
- **Repair rate:** $P(\text{eventually satisfied} \mid \text{rejected at least once})$
- **Path efficiency:** $|S| / k$ (minimal steps / actual contacts)
- **Silent failure:** submitted, with a key field coming from an unverified default/stale value

---

## 6. Pre-run gates (must pass)

| Gate | Method | Pass criterion |
|---|---|---|
| G1 Leakage | BM25/keyword baseline picks the candidate with the highest profile–task similarity | First-contact accuracy under R1 ≤ 1.5 × random (to be decided) |
| G2 Solvable | 2 people solve the task with full information | Both reach the gold path and answer |
| G3 Must ask | Answer without contacting anyone | Cannot reach a correct artifact (but can produce a plausible one) |
| G4 Unique answer | Manual review + evaluator unit tests | Gold is unique or the equivalence class is explicit |
| G5 Evaluator | ≥ 100 boundary fixtures (formats, order, rejection repair) | All pass |
| G6 Pilot | Each cell runs a small number of episodes | No ceiling/floor effect (e.g., first-contact accuracy not uniformly > 95% or < 5%) |

---

## 7. Paper scope (suggestion)

- **Workshop (11-20):** Exp A (N ∈ {4, 8, 16}, R1, full list) + Exp B (d ∈ {1, 2, 3}) on **de-leaked tasks**, plus the existing "who ≠ process" finding. Core claim: *"agents' recipient selection degrades with organization size and multi-step dependencies, and errors are dominated by ordering/repair rather than recipient identity"* (hypothesis; depends on results).
- **Main conference:** full Exp A–D + human validation of task realism.

---

## 8. Decision log

| Date | Decision | Status |
|---|---|---|
| 2026-10-26 | Define help-seeking as self-initiated under uncertainty; instructed contacts are out of scope | Agreed in discussion (pending write-up into proposal) |
| 2026-10-26 | Add candidate scale N and order/dependencies as core manipulations | User proposed; included |
| — | Whether the search-tool presentation enters the main experiment | **Pending** |
| — | Whether to reuse TAC's 17 roles as the N=17 organization | **Pending** |
| — | Which frontier model to add | **Pending** |
| — | Workshop scope: A+B lightweight version | **Pending** |

## 9. Change log

| Version (time) | Change |
|---|---|
| 20261026-1236 | Initial version: D1–D6 diagnosis; P1–P6 principles; M1–M10 changes; Exp A–D; metric definitions; G1–G6 gates; paper scope |
