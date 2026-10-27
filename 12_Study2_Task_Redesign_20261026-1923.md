# Study 2 Task Redesign Proposals (living document)

> This document is updated as discussion continues. Following the naming convention, the timestamp in the filename is updated on every edit to the last-modified time, and the previous version is overwritten via `git mv` (history stays in git).
> Each change is recorded in **§9 Change log**, and decisions in **§8 Decision log**.
> Sources reviewed: `research/study2/derived/study2_v04_analysis.md`, `research/study2/study2_1_taskset/` (R1 analysis report, R0 formal run), `task_blueprints_v0.4.jsonl`.
> Statements marked "hypothesis" or "estimate" are not verified.

> **⚠ Revision 2026-10-26 (supersedes conflicting parts of §3, §4, §10, §12):** the task set now has **two classes only — Must-help and Optional-help, 30 templates each (60 total)**. The No-help class is dropped. "Hard distractors" is no longer a scored difficulty feature. The authoritative spec is **§13 (task set)** and **§14 (Task Evaluator)**. Earlier sections are kept for history.

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
- **R0⁻ (optional):** names only, reported only as a lower bound, not entered into the main contrast.
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
- **N ∈ {4, 8, 16}** (TAC has only 17 NPCs; N=32 dropped), keeping the **number of valid recipients fixed** and the distractor composition proportionally fixed.
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
- Models: keep the current three low-cost models as the main set; add **Claude Sonnet 5.5** as a stronger reference model on a subset of conditions (see decision log). Opus 5.5 optional if budget allows.
- Lock model versions, temperature, and maximum turns, and record them.

---

## 4. Experiment modules

### Exp A: Candidate scale (who × N)
| Item | Setting |
|---|---|
| Factors | N ∈ {4, 8, 16} × profile ∈ {R0, R1} × presentation ∈ {full list, search tool} (presentation optional) |
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

### Size and cost (recomputed from measured costs)

**Measured basis (Study 2.1 R0, N=4):** per-episode cost Claude Haiku ≈ $0.0011, GPT-5.4-mini ≈ $0.0023, Kimi ≈ $0.0064; average ≈ **$0.003/episode**, 2–7k tokens per episode.

**Assumption:** prompt length grows with N, and multi-turn dialogue resends context. Averaged over N ∈ {4, 8, 16}, per-episode cost is about 2–3× the N=4 cost, i.e., ≈ $0.01 (estimate).

| Plan | Episodes | Estimated cost |
|---|---|---|
| **Workshop lite**: Exp A (16 templates × N∈{4,8,16} × R1 × 3 low-cost models × 2 reps) + Exp B (12 templates × d∈{1,2,3} × R1 × 3 models × 2 reps) | ~290 + ~220 ≈ 510 | **≈ $3–5** |
| Full Exp A + B, low-cost models only (3 models, 3 reps) | ~2,200 | **≈ $20** |
| Full + 1 frontier model on **all** cells | ~2,800 | **$60–100+**, about 80% from the frontier model |
| Full + frontier model on a **subset only** (e.g., N∈{4,16}, d∈{1,3}, 1 rep) | ~2,400 | **≈ $25–30** |

**Cost-saving measures (by priority):**
1. Frontier model runs only on a subset of endpoints (at most 1 rep per cell), used only to check whether conclusions hold for strong models.
2. Choose N levels {4, 16} or {4, 8, 16} first; add 32 only if the trend is unclear.
3. Use prompt caching: the candidate directory is a fixed prefix within the same template, so repeated turns can be billed at the cached rate (Anthropic cache reads are about 1/10 of the input price).
4. Run 2 reps first; add more only for cells with high variance.
5. Use the search-tool presentation mode: prompts do not grow linearly with N, which saves money and is more realistic.

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

## 10. Task set acceptance criteria and target distribution (what success looks like)

### 10.1 Difficulty scoring (each task gets a difficulty score D, objectively computed from structural features)

| Feature | 0 points | 1 point | 2 points |
|---|---|---|---|
| **Candidate pool N** (number of people the agent can contact) | ≤ 4 | 5–8 | ≥ 9 (up to 17, TAC's full roster) |
| **Dependency depth d** (longest chain in the gold DAG) | 1 | 2 | ≥ 3 |
| **Knowledge–authority separation** | Same person | Different people | Different people + delegation/conditional approval |
| **Hard distractors** (near-miss / stale / delegated / stale-fact / referrer) | 0 | 1–2 | ≥ 3 |
| **Inference type** (how the gold candidate is identified) | Title/responsibility directly says it | Requires one rule (threshold/scope/delegation) | Requires multiple rules or tool lookup (org chart/permission error) |

- **D = sum of the five features, range 0–10.** Levels:
  - **Low (L): D ≤ 3**
  - **Medium (M): 4 ≤ D ≤ 6**
  - **High (H): D ≥ 7**, and must satisfy at least one of N ≥ 9 or d ≥ 3 (matching the user's definition of "more people or more than two dependency steps")
- For optional / no-help tasks, d and separation have little meaning. Their difficulty instead comes from **how hidden the uncertainty is** and **how tempting it is to ask** (see 10.3).

### 10.2 Target distribution (workshop lite version; can be scaled up proportionally)

**Unit: independent workflow templates. Variants of the same template (different N, aligned/separated) do not count separately.**

| Help-need type | L | M | H | Subtotal | Notes |
|---|---:|---:|---:|---:|---|
| **Must ask** | 6 | 10 | 8 | **24** | H tasks must include ≥ 4 with N ≥ 9 and ≥ 4 with d ≥ 3 |
| **Optional (asking may help)** | 4 | 6 | 2 | **12** | Asking improves quality; not asking can still pass the base check |
| **No help needed** | 6 | 4 | 2 | **12** | Asking is unnecessary; tests over-asking |
| **Total** | 16 | 20 | 12 | **48** | |

- Must-ask is the main body (half), because RQ2 who/order is measured mainly there.
- The scale experiment (Exp A) takes **12 templates** from must-ask and generates N ∈ {4, 8, 16} variants of each.
- The order experiment (Exp B) takes **12 templates** from must-ask, ensuring the d=1/2/3 distribution is 4/4/4.

### 10.3 Difficulty definitions for the other two types
| Type | L | M | H |
|---|---|---|---|
| **Optional** | Benefit from asking is obvious and the relevant person is clearly named | Benefit needs inference (e.g., noticing a "local holiday" note in the data) | Benefit is subtle, and the relevant person must be inferred from rules among N ≥ 9 people |
| **No-help** | All information is in the input | Input looks like it has a gap but can actually be derived | Strong temptation to ask is planted (e.g., a field labeled "confirm with finance"), but a tool can resolve it |

### 10.4 Quantitative acceptance criteria (pass/fail gates for the task set)

**A. Distribution and coverage**
| # | Criterion | Threshold |
|---|---|---|
| A1 | Number of templates per type | Matches 10.2 (±1) |
| A2 | Must-ask H tasks | ≥ 8, with ≥ 4 where N ≥ 9 and ≥ 4 where d ≥ 3 |
| A3 | Dependency structure coverage (must-ask) | Each of the 5 structures (info→approval / referral chain / parallel+join / delegation / conditional) appears ≥ 3 times |
| A4 | Distractor type coverage | Each of the 7 types in M3 appears in ≥ 4 templates |
| A5 | Business domains | ≥ 6 (engineering, product, HR, finance, sales/marketing, security/IT, etc.) |
| A6 | Aligned vs separated (must-ask) | Each 40–60% |

**B. Validity (the task measures what it claims to measure)**
| # | Criterion | Threshold |
|---|---|---|
| B1 | **Limited wording overlap**: for each task, compute the share of the task's key content words (e.g., the required authority phrase) that also appear in the gold recipient's profile, and the same share for the most similar distractor. Computed on task files at design time, before any agent runs | Gold-profile overlap is not much higher than the most similar distractor's (e.g., gold minus top distractor ≤ 30 percentage points); verbatim repetition of the full authority phrase is avoided. Exact threshold to finalize after measuring the current task set |
| B2 | **Must actually requires asking**: a "no-contact" agent (best effort with only the input) | Must-ask strict success ≤ 5% |
| B3 | **Silent-failure trap is effective**: under no-contact, a plausible but wrong output can be produced | ≥ 80% of must-ask tasks |
| B4 | **Solvability**: with full information, an oracle script and 2 human annotators | Both reach the gold path and answer in 100% of cases |
| B5 | **Unique answer**: gold artifact is unique or the equivalence class is explicit | 100% (meeting-room-fit-style tasks are fixed or removed) |
| B6 | **No-help needs no asking**: a no-contact agent | No-help strict success ≥ 90% (excluding format issues) |
| B7 | **Task text has no hints**: automated scan of the task text for "verify / approve / do not guess / ask / confirm" | 0 hits (except no-help temptation tasks, which are labeled) |

**C. Realism and complexity (judged on the task design, not on agent results)**
| # | Criterion | Threshold |
|---|---|---|
| C1 | Grounded in real workflows | Each template cites the real-world process it models (e.g., purchase approval with spending thresholds, access request via a manager, incident notice sign-off) |
| C2 | Organizational realism | Roles, reporting lines, and authority rules are consistent across the whole organization (one shared org chart, not per-task ad hoc roles) |
| C3 | Realism review | Two people with workplace experience rate each template's realism; templates rated unrealistic by either are revised |
| C4 | Complexity coverage | Distribution in 10.2 is met, including H tasks with N ≥ 9 and with d ≥ 3 |

> **We do not set targets on agent success rates.** Results may show 100% success for some models or conditions; that is a valid finding. Difficulty labels come from task structure (10.1), not from observed agent performance. A pilot run is used only to catch bugs (broken tasks, evaluator errors, NPC rule violations), not to tune difficulty toward a desired success rate.

**D. Engineering and evaluation**
| # | Criterion | Threshold |
|---|---|---|
| D1 | Evaluator unit tests | ≥ 100 fixtures (formats / order / rejection repair / referral), all pass |
| D2 | Format tolerance | Rule-based normalization for number units, list/map, name↔ID |
| D3 | NPC follows rules | Spot-check 20 dialogues: NPC never discloses unassigned facts or grants unauthorized approvals; 0 violations |
| D4 | **Runs in TAC** | See §11; every task passes the "TAC compatibility checklist" |

### 10.5 Example task table (illustrative only, not final)

| task_id | Type | Domain | N | d | Structure | Separated | Hard distractors | Inference | D | Level | TAC services |
|---|---|---|---:|---:|---|---|---|---|---:|---|---|
| must-vendor-contract | must | finance/procurement | 8 | 2 | conditional (>$10k needs Director) | Yes | near-miss authority, stale role | threshold rule | 7 | H | rocketchat, owncloud |
| must-prod-deploy | must | engineering | 12 | 3 | info → approval → notify | Yes | delegated, plausible-title | delegation + org chart | 9 | H | rocketchat, gitlab, plane |
| must-hire-interviewer | must | HR | 6 | 2 | referral chain (HR → team lead) | Yes | referrer | 1 rule | 5 | M | rocketchat |
| must-expense-category | must | finance | 4 | 1 | info only | No | 0 | directly stated | 1 | L | rocketchat, owncloud |
| opt-release-notes | optional | product | 8 | — | — | — | plausible-title | benefit needs inference | — | M | rocketchat, gitlab |
| nohelp-budget-sum | no-help | finance | 6 | — | — | — | "confirm with finance" temptation | derivable | — | H | owncloud |

---

## 11. TAC compatibility constraints (redesigned tasks must run in TheAgentCompany)

**Principle:** tasks must follow TAC's task package structure and runtime mechanisms. Our text simulator is only a fast development/pilot tool; formal results must be reproducible in TAC (or at least tasks must be exportable to the TAC format).

### 11.1 What TAC requires of a task (verified from the TAC repo)
- **Task package** `workspaces/tasks/<task>/`: `task.md`, `checkpoints.md`, `evaluator.py`, `dependencies.yml`, `Dockerfile`, `Makefile`; NPC tasks also need `scenarios.json` (`Dockerfile` copies it to `/npc`).
- **NPCs**: 17 existing NPCs (`npc_definition.json` + `npc_credential.json`), which are **company-level shared employees**. Adding an NPC requires manually creating a RocketChat account and updating credentials and the Sotopia definition. **So N ≤ 17 is the natural ceiling**; beyond that requires new NPCs (high cost, not recommended).
- **NPC behavior**: an LLM role-play (Sotopia) driven by each NPC's `extra_info` + `strategy_hint` in `scenarios.json`. **It is not a rule engine**. Rejection, referral, and delegation have to be described in the strategy_hint and cannot be guaranteed 100% deterministic.
- **Evaluation**: `evaluator.py` uses helpers from `common.py`: `get_rocketchat_personal_chat_history`, `num_rocketchat_users_contacted`, `evaluate_chat_history_with_llm`, plus checks on file and GitLab/Plane/OwnCloud state.
- **Channels/services**: RocketChat (15 channels), GitLab, OwnCloud, Plane; services are declared in `dependencies.yml`.

### 11.2 How the redesign adapts
| Redesign element | TAC implementation | Feasibility / note |
|---|---|---|
| **N (candidate pool)** | All 17 NPCs are always online in TAC, so **N cannot be "hidden"**. The scale manipulation becomes: the number of people listed in the task's relevant directory/channel/org chart document + how many of them have relevant roles in `scenarios.json` | ✅ N ∈ {4, 8, 16} feasible; N=32 **not feasible** (only 17 NPCs) |
| **Profiles R0/R1** | R0 = TAC's existing `npc_definition.json` (name + occupation; already a realistic directory); R1 = an extra **org chart / RACI document** in OwnCloud (authority rules, delegation, thresholds) | ✅ Natural fit; in TAC, profile information has to be **found** by the agent, which is more realistic |
| **Authority rules / delegation** | Written in an OwnCloud policy document + the NPC's strategy_hint (e.g., "if asked to approve > $10k, say you're not authorized and refer to David Wong") | ✅ But NPC compliance must be spot-checked (D3) |
| **Permission-denied trigger** | Use a real permission restriction in TAC (e.g., OwnCloud directory not shared; GitLab protected branch) | ⚠️ Requires extra service configuration (`pre_init.py` / `populate_data.py`); feasible but higher cost |
| **Multi-step order / rejection** | Write prerequisites into the strategy_hint: "only approve after you've been told X" | ✅ TAC already has similar patterns (e.g., the "trap" in hr-pick-interviewer-2) |
| **Evaluation** | `evaluator.py`: check whether the right people were DMed via `get_rocketchat_personal_chat_history`; **message timestamps** for order; final artifact checked by file/state | ✅ Order can use timestamps; avoid relying solely on `evaluate_chat_history_with_llm` |
| **Silent failure** | Leave a stale value in the OwnCloud data; the evaluator checks whether the submission is the new value | ✅ |
| **Unavailable / delayed reply** | strategy_hint: "reply that you're on leave until X; your delegate is Y" | ✅ Simulated in dialogue; it is not a real offline state |

### 11.3 Dual-track running (recommended)
1. **Development track: text simulator** (current Study 2.1 framework). Cheap, fast, deterministic; used for iterating tasks and catching bugs before TAC runs.
2. **Validation track: TAC.** Export the same templates as TAC task packages (generate `task.md`, `scenarios.json`, `checkpoints.md`, `evaluator.py`, `dependencies.yml`, `Dockerfile`), and run TAC on a **subset** to confirm conclusions agree.
- **Requirement:** every template's single source of truth (blueprint) can generate **both** the simulator format and the TAC package. Fields not in TAC (e.g., numeric interruption cost) are converted to behavior or documents.

### 11.4 TAC compatibility checklist (D4; each task must satisfy all)
- [ ] Uses only the existing 17 NPCs (no new accounts needed)
- [ ] Every NPC's knowledge and behavior can be expressed in `scenarios.json` `extra_info` + `strategy_hint`
- [ ] Profile/rule documents can be placed in OwnCloud or a RocketChat channel
- [ ] Every checkpoint can be implemented with existing helpers in `common.py` (or new helpers ≤ 20 lines)
- [ ] Order judgments rely on message timestamps, not on LLM judging
- [ ] `dependencies.yml` declares only available services (rocketchat / gitlab / owncloud / plane)
- [ ] Exportable to a complete task package, buildable by `make`

### 11.5 Cost in TAC (estimate)
- TAC runs **use OpenHands + a browser**. Per-episode tokens are far higher than in the text simulator (Study 1 trajectories show tens to hundreds of steps per episode, with full web pages as observations), and NPCs also consume LLM calls.
- So **TAC validation runs only a subset** (e.g., 12 templates × N ∈ {4, 16} × 2 models × 1 rep ≈ 48 episodes). Per-episode cost can be measured with 1–2 trial runs, then scaled up.


---

## 12. How help-need classes are built in at design time

The class (must / optional / no-help) is a **property of the task's information structure and evaluator**, fixed before any agent runs. It is verified with two scripted reference solutions, not with agent results.

### 12.1 Information split
- **V (visible):** everything the agent can get without asking anyone (task text, OwnCloud files, tool outputs).
- **H (held by colleagues):** facts, rules, or approvals that only specific NPCs provide.
- **Evaluator = base checks + quality checks.** Base checks define a valid deliverable; quality checks score extra, objectively measurable improvements.

| Class | Base checks need H? | Quality checks need H? | Design rule |
|---|---|---|---|
| **Must ask** | **Yes** | — | At least one base-check field or approval exists only in H. V contains a plausible-but-wrong default (stale value, closed code) so not asking produces a silent failure, not an obvious gap |
| **Optional** | **No** | **Yes** | V is sufficient for a valid baseline. H holds one extra fact that improves a scored dimension (accuracy, risk, cost, completeness). Not asking still passes base checks |
| **No-help** | No | No | Everything needed is in V or derivable with tools. NPCs hold nothing that changes the score. May include a temptation (a field marked "confirm with finance") that a tool or document already resolves |

### 12.2 Design-time verification: two reference solutions
For each task, write two deterministic reference solutions (scripts or human walkthroughs) and run both through the evaluator:
1. **No-contact reference:** best possible output using V only.
2. **Full-information reference:** output using V + H.

| Class | No-contact reference | Full-information reference |
|---|---|---|
| Must ask | Base checks **fail** | Base checks pass |
| Optional | Base checks **pass**, quality score = 0 (or low) | Base checks pass, quality score **higher** |
| No-help | Base checks pass, quality score = maximum | Same as no-contact (H adds nothing) |

A task gets its class label only if both references produce the pattern above. This is the acceptance gate for B2/B3/B6 in §10.4 and does not depend on how any model behaves.

### 12.3 Rules for a good optional task
1. **The improvement must be measurable by rules, not keywords.** Score a consequence, e.g., number of schedule conflicts with a regional holiday, whether a cheaper eligible license tier was used, whether a known risk is mitigated in the plan. Avoid scoring by matching specific phrases in free text.
2. **There must be a discoverable cue in V.** A careful worker would notice a reason to check (e.g., the event is in a region whose holiday calendar is not in the packet; the quote mentions "volume discount available, contact account owner"). Without a cue, asking is random rather than a judgment.
3. **The task text must not hint.** No "you may add information", "consider asking", or "no X is required" phrases (Study 2.1's optional tasks contain such hints; remove them).
4. **The benefit must be realistic.** It should be something a real employee would plausibly check with a colleague, and the colleague who holds it should be inferable from roles, as in must-ask tasks.
5. **Report the trade-off.** Asking has interruption cost; the paper reports quality gain vs. contact cost per agent, not a single "correct" choice.

### 12.4 Example: one workflow, three classes (SecureScan purchase)
| Class | Variant | V | H | Base / quality |
|---|---|---|---|---|
| Must ask | 12 seats, USD 14,400, tool uploads code | Quote, policy, org chart | Current budget code (Wang Fang), review (Emma Lewis), approval (Chen Xinyi) | Base needs all three |
| Optional | 6 seats, USD 7,200, CTO may approve per policy; quote notes "team-plan pricing may apply, ask your account owner" | Quote, policy, org chart, CTO approval rule | Wang Fang knows the company already has a team plan → USD 5,400 | Base: valid request at 7,200. Quality: total cost uses the team plan |
| No-help | Same as optional, but the team-plan price is already listed in an OwnCloud pricing sheet | Everything incl. pricing sheet | Nothing additional | Base and quality both from V |


---

## 13. Task set specification (two classes, 60 templates) — authoritative

### 13.1 Classes
| Class | Definition (design-time) | Base checks | Quality checks |
|---|---|---|---|
| **Must-help (M)** | At least one base-check field or required approval exists **only** with a colleague (H) | Need H | Optional extras allowed but not required |
| **Optional-help (O)** | All base-check fields are obtainable from visible information (V); a colleague holds an extra fact that improves a rule-scored quality dimension | Need only V | Need H for the quality gain |

The No-help class is dropped. Over-asking is still observable in O tasks (asking people who hold nothing useful, or asking when the expected gain is small) and is reported descriptively, not as an error class.

### 13.2 Difficulty features (hard distractors removed)
Every candidate pool still contains people who hold nothing relevant (N > number of needed people), but distractor *hardness* is no longer scored.

**Must-help (4 features, 0–2 each, D_M ∈ [0, 8])**
| Feature | 0 | 1 | 2 |
|---|---|---|---|
| Candidate pool N | ≤ 4 | 5–8 | 9–16 |
| Dependency depth d (longest chain in gold DAG) | 1 | 2 | ≥ 3 |
| Knowledge–authority separation | Same person | Different people | Different people + delegation or conditional approval |
| Inference type (identifying the right person) | Title/responsibility states it | One rule or one lookup | Multiple rules or ≥ 2 lookups |

**Optional-help (4 features, 0–2 each, D_O ∈ [0, 8])**
| Feature | 0 | 1 | 2 |
|---|---|---|---|
| Candidate pool N | ≤ 4 | 5–8 | 9–16 |
| Cue salience (how visible the reason to ask is in V) | Explicit cue (e.g., "pricing may differ, check with account owner") | Implicit cue requiring one inference (e.g., event region has no holiday calendar in the packet) | Cue only emerges after combining two pieces of V |
| Holder inference (identifying who holds the improvement) | Title/responsibility states it | One rule or one lookup | Multiple rules or ≥ 2 lookups |
| Integration effort (using the reply) | Copy one value | Recompute one field | Revise several fields consistently |

**Levels (both classes):** Low D ≤ 2; Medium 3 ≤ D ≤ 5; High D ≥ 6, and for M-High at least one of N ≥ 9 or d ≥ 3.

### 13.3 Target distribution (60 templates)
| Class | Low | Medium | High | Total |
|---|---:|---:|---:|---:|
| Must-help | 8 | 12 | 10 | **30** |
| Optional-help | 8 | 12 | 10 | **30** |
| **Total** | 16 | 24 | 20 | **60** |

Coverage requirements:
- M-High: ≥ 5 with N ≥ 9 and ≥ 5 with d ≥ 3.
- M: each dependency structure (info→approval / referral chain / parallel+join / delegation / conditional) appears ≥ 4 times.
- ≥ 6 business domains per class; aligned vs separated in M each 40–60%.
- N levels {4, 8, 16} each used by ≥ 8 templates per class (supports the scale analysis).
- Each M template is paired with an O template from the same workflow where natural (as in §12.4), to allow within-workflow comparison.

### 13.4 Design rules (carried over)
- M: V contains a plausible-but-wrong default (stale value, closed code, outdated owner) so not asking yields a silent failure.
- O: V contains a discoverable cue; the quality gain is scored by rules on outcomes (e.g., conflicts, cost, risk mitigations), not by keyword matching.
- Both: task text contains no hints about asking, verifying, approval, or who to contact; profiles do not repeat the task's key phrases verbatim (§10.4 B1, relaxed overlap check).
- Both: runnable in TAC (§11.4 checklist) and in the text simulator from one blueprint.

---

## 14. Task Evaluator (quality gate for each task and for the set)

### 14.1 Purpose
Decide, before any experiment, whether each generated task is (a) **complex and well-formed enough** to use, and (b) **correctly classified** as Must-help or Optional-help. It never runs the models under test.

### 14.2 Inputs and outputs
- **Input:** one task blueprint (single source of truth) + the generated simulator package and TAC package.
- **Output per task:** `task_eval.json` with each check's value, pass/fail, computed difficulty D, level, and a final verdict `ACCEPT / REVISE / REJECT`.
- **Output per set:** `set_eval.md` with the distribution table vs §13.3 targets and the list of failing tasks.

### 14.3 Checks

**A. Well-formedness (automatic, must all pass)**
| # | Check | Method |
|---|---|---|
| A1 | Required fields present (V, H, gold DAG, admissible recipients per step, base/quality checks, cue for O) | Schema validation |
| A2 | Both packages build | Simulator loader runs; TAC `Dockerfile` builds, `evaluator.py` imports |
| A3 | TAC compatibility | §11.4 checklist: only the 17 existing NPCs, services ∈ {rocketchat, owncloud, gitlab, plane}, order checks use timestamps |
| A4 | Unique gold | Base-check answer is unique or the equivalence class is listed; evaluator unit tests for format variants pass |

**B. Classification correctness (automatic, reference solutions)**
| # | Check | Must-help passes if | Optional-help passes if |
|---|---|---|---|
| B1 | No-contact reference (V only, best effort) | Base checks **fail** | Base checks **pass** |
| B2 | Full-information reference (V + H, gold path) | Base checks pass | Base pass and quality score **> no-contact quality score** by ≥ a preset margin |
| B3 | Necessity ablation: remove each H item from the full reference | Base checks fail for every *required* H item (no decorative requirements) | Quality gain disappears when the improvement item is removed |
| B4 | Silent-failure trap (M) / cue presence (O) | No-contact output is plausible (schema-valid, non-empty) but wrong | An LLM judge, given only V, answers "is there a reason a careful employee would check with someone?" → yes, and cites the cue |

The class label is accepted only if B1–B4 match the label.

**C. Complexity verification (automatic + LLM judge)**
| # | Check | Method |
|---|---|---|
| C1 | Recompute features from the blueprint, not from the author's claim | N = contactable people listed; d = longest path in gold DAG; separation from holders of info vs authority; inference type from the number of rules/lookups on the gold path |
| C2 | Inference type is real | A **title-only resolver** (script that picks the person whose title best matches the needed role) must fail for inference ≥ 1. For inference = 2, an LLM judge confirms that ≥ 2 documents/rules must be combined |
| C3 | Wording overlap | Gold-profile vs task-text overlap not much higher than the most similar other profile (§10.4 B1) |
| C4 | No hints | Task text scan for "ask / verify / confirm / approve / check with / do not guess / you may contact" → 0 hits |
| C5 | Difficulty label | Computed D and level match the target slot assigned in the distribution |

**D. Realism (LLM judge + human sample)**
| # | Check | Method |
|---|---|---|
| D1 | Workflow realism | LLM judge rubric (1–5): plausible workplace process, plausible roles and rules, coherent with the shared org chart; ≥ 4 required |
| D2 | Human spot check | Two reviewers rate a random 20% of tasks (and every task the judge scores ≤ 3); disagreements resolved by discussion |
| D3 | Org consistency | Roles, reporting lines, and authority rules match the shared org chart across all tasks (automatic cross-check) |

**E. Set-level checks**
| # | Check | Target |
|---|---|---|
| E1 | Class × level counts | §13.3 table (±1 per cell) |
| E2 | Coverage | §13.3 coverage requirements |
| E3 | Near-duplicates | No two templates with the same workflow + same gold path (embedding or rule-based similarity) |

### 14.4 Verdict rules
- **ACCEPT:** A, B, C all pass; D1 ≥ 4 (and D2 if sampled).
- **REVISE:** any C or D failure, or B4 failure → returned to the task generator with the failing check and reason.
- **REJECT:** A or B1–B3 failure that cannot be fixed without changing the class.

### 14.5 Implementation notes
- The reference solutions and ablations run in the **text simulator** (deterministic NPC rules), so the evaluator is cheap and repeatable; TAC is used only for A2/A3 build checks and for a final subset run.
- The LLM judge uses a fixed low-cost model and fixed prompts, logged with version; it is **different from the models under test**, and its role is limited to C2 (inference ≥ 2), B4 (cue presence), and D1 (realism).
- The Task Evaluator's own correctness is tested on a small set of deliberately broken tasks (mislabeled class, leaked answer, hinting text, fake dependency) that it must flag.


---

## 8. Decision log

| Date | Decision | Status |
|---|---|---|
| 2026-10-26 | Define help-seeking as self-initiated under uncertainty; instructed contacts are out of scope | Agreed in discussion (pending write-up into proposal) |
| 2026-10-26 | Add candidate scale N and order/dependencies as core manipulations | User proposed; included |
| 2026-10-26 | Redesigned tasks must run in the TAC framework; adopt dual-track (text simulator for development + TAC for validation); N ≤ 17 | User requested; included in §11 |
| — | Whether the search-tool presentation enters the main experiment | **Pending** (TAC has no directory search tool; could use OwnCloud documents or channel member lists instead) |
| 2026-10-26 | Two classes only (Must-help, Optional-help), 30 templates each; No-help dropped; hard distractors removed as a difficulty feature; add a Task Evaluator gate (§13–§14) | User decision |
| 2026-10-26 | Do not design toward expected results; no success-rate targets. Aim for complex, realistic tasks; difficulty is defined structurally | User decision |
| 2026-10-26 | Reuse TAC's 17 roles as the organization; N levels {4, 8, 16} | Includes TAC constraints; N=32 dropped |
| 2026-10-26 | Stronger reference model: Claude Sonnet 5.5 ($2/$10 per MTok) on a subset (endpoint conditions, 1 rep); main runs stay on low-cost models | Recommended; pending user confirmation |
| — | Workshop scope: A+B lightweight version | **Pending** |

## 9. Change log

| Version (time) | Change |
|---|---|
| 20261026-1923 | Two-class redesign (§13): Must-help and Optional-help, 30 each; class-specific difficulty features without hard distractors; new target distribution. Task Evaluator spec (§14): well-formedness, classification via reference solutions and ablations, complexity recomputation, realism review, set-level checks, verdict rules. Revision banner added at top |
| 20261026-1918 | Added §12: how must/optional/no-help are built in at design time (V vs H split, base vs quality checks), two-reference-solution verification, rules for optional tasks, one-workflow-three-classes example |
| 20261026-1259 | B1 relaxed per user: overlap percentage must not be too high relative to distractors, rather than "any repetition triggers rewrite". Model plan: Sonnet 5.5 as stronger reference on a subset |
| 20261026-1256 | Per user: removed outcome-based targets (old C1–C5: no ceiling, no floor, monotonic difficulty, model gap, scale effect). Section C now judges realism/complexity of the design only. Clarified B1 as a design-time word-overlap check on task files, not an agent success threshold |
| 20261026-1251 | Added §10 acceptance criteria (difficulty score D, target distribution 48 templates, A/B/C/D thresholds, example table) and §11 TAC compatibility constraints (task package structure, 17-NPC ceiling, dual-track run, compatibility checklist); N levels changed to {4, 8, 16} |
| 20261026-1246 | Cost section recomputed from measured per-episode cost (~$0.003/ep); added workshop-lite plan (≈$3–5) and cost-saving measures; frontier model limited to a subset |
| 20261026-1236 | Initial version: D1–D6 diagnosis; P1–P6 principles; M1–M10 changes; Exp A–D; metric definitions; G1–G6 gates; paper scope |
