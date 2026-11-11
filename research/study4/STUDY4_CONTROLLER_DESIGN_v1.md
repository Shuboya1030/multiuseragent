# Study 4 — Help-Seeking Controller: Design and Implementation Spec (v1.0)

**Author:** paper/design session · **Date:** 2026-11-11 · **Status:** approved design, ready for implementation
**Implementer:** experiment agent · **Supersedes:** the SFT87 teacher-imitation design in `research/study4/` (kept for reference; do not delete)

This document is the implementation contract. Each phase has deliverables and a **go/no-go gate**. Do not start a phase until the previous gate passes; report gate results before proceeding. When a decision is not specified here, choose the simplest option and record it in the phase report.

---

## 0. Goal (from the research proposal, RQ4)

> Can a learned policy that jointly decides **when** and **whom** to ask outperform prompting-based help-seeking, and does it **generalize to unseen organizational structures**?

Three hard requirements follow:
1. **Beat prompting on utility R**, not only completion rate.
2. **Joint decision**: show value beyond a sequential "when, then whom" pipeline.
3. **Generalize to new organizations**: train and test on disjoint organizations.

We extend the decision to **when + whom + what** (what to include in the request), because the TribalBench results show that once agents ask, choosing the first recipient is almost never the problem (79/79 correct), while 41/79 asking episodes hit a refusal, usually because the request lacked a value obtained earlier (paper §5.3, Figure 5).

### Utility (reward and primary metric)

Use the published TribalBench utility (Eq. 1 of the paper; implemented in `Shuboya1030/tribalbench/scorer/scorer.py`, function `score`, field `R`):

$$R = T - \lambda\max(0, C - C^*) - \mu N_{\text{auth}} - \nu N_{\text{waste}},\quad \lambda=0.05,\ \mu=0.3,\ \nu=0.1$$

$C^*$ = cost of the cheapest gold path (`gold_path_cost`). Do **not** introduce other objectives (e.g., `T − 0.15C`). Weight sensitivity is analyzed only at evaluation time (§7).

---

## 1. Why the previous design is replaced (do not repeat these)

| Previous design | Problem | New design |
|---|---|---|
| Actions are person names (`ASK:Chen Xinyi`) scored as full JSON strings | Learns names, cannot generalize to new organizations; longer names get lower scores | Score each **candidate described by public attributes** with one shared head |
| Labels = GPT teacher's actual actions | Teacher itself was right on only 9/16 dev tasks; errors are copied | Labels computed from the **gold dependency graph** (oracle) |
| One 17-person organization, 60 tasks, LLM NPCs | Too little data; no new-organization test; every sample costs API money | **Procedural generator** of organizations and tasks + **rule-based NPCs** (free, unlimited) |
| Decision at every cycle | ~83% trivial NO_ASK labels drown the key states | Decide only at **key decision points**; class weighting |
| LoRA lr 1e-5, 87 steps | Underfit: accuracy equals always-NO | Overfit sanity check first; lr 1e-4 range |
| Executor interface differed between arms (SELF repeatedly posted, never submitted) | Confounds every comparison | Fix the executor protocol first (Phase 1) |

---

## 2. Architecture

### 2.1 Roles

- **Controller (learned):** decides when / whom / what at key decision points.
- **Executor (fixed):** an LLM (default `gpt-5.4-mini-2026-03-17`, reasoning none) that reads files, writes the deliverable, phrases messages, and submits. It is **not trained**. The executor is identical across all arms.
- **Colleagues (NPCs):** rule-based during training and development (§3.2); LLM-simulated (GPT-5.4-mini, as in the paper) only for final transfer evaluation.

### 2.2 Controller input (public information only)

- Task instruction and public documents.
- Interaction history: tools used, files written, messages sent, replies received (full text).
- Candidate list: for each colleague, the public directory entry (title, responsibilities, approval scope) and interruption cost.
- A **progress summary** derived from public history only: which values the agent has obtained so far (key → value, with source colleague), which requests were refused and the stated reason.

**Never** input: gold DAG, unreleased private facts, required_context lists, evaluator output, task class (must/optional).

### 2.3 Controller output (three heads)

1. **When** (3-way): `ASK`, `SELF` (executor does one ordinary action), `SUBMIT`.
2. **Whom** (if ASK): a score for each candidate computed by a shared scoring head over [state encoding ; candidate encoding]; softmax over the legal candidates. **No person-name output tokens.**
3. **What** (if ASK): for each obtained value in the progress summary, a binary decision "include in this request". The system then builds the request: `<intent sentence> + included values (key: value)`; the executor only rephrases it into a natural message and may not drop included values.

### 2.4 Model

- Backbone: `Qwen2.5-1.5B-Instruct` (scale to 7B only if Phase 3 gate fails due to capacity). LoRA r=16, α=32 on attention and MLP projections.
- Heads: small MLPs on the final hidden state of special marker tokens (`<STATE>`, one `<CAND_i>` per candidate, one `<VAL_j>` per obtained value).
- Context: up to 6k tokens; truncate history from the oldest non-reply events first; never truncate replies or the progress summary.

### 2.5 Key decision points

The controller is called only: (a) at task start, (b) after every colleague reply, (c) when the executor proposes to write the final deliverable or submit, (d) every 4 executor steps as a safety check. Between these, the executor acts alone. Maximum episode: 24 executor steps.

---

## 3. Environment

### 3.1 Procedural generator (`study4/gen/`)

Generate organizations and tasks in the **TribalBench blueprint format** (same fields as `tasks/<id>/gold/blueprint.json`), so the same scorer works.

**Organizations**
- Size 8–30 people; departments (engineering, finance, HR, security, sales, legal, ops, …), titles, reporting lines.
- Per-action authority (e.g., "approves purchases ≤ USD 10k"), delegations (leave + deputy), and interruption cost by seniority (3/2/1, as in TribalBench).
- Name and title pools must be **disjoint between train and test organizations**.

**Tasks**
- Dependency templates: single info; info → approval; parallel → join; referral chain; delegation; conditional approval (threshold); depth 1–4.
- Must-help (some required value or approval only held by a colleague; visible documents contain a plausible stale default) and optional-help (valid baseline from visible info; a colleague holds an improvement).
- Distractors: plausible-but-wrong holders (same department, outdated owner, approver without the right threshold).
- Difficulty features identical to TribalBench (pool size, inference, depth, separation / cue, integration).

**Validation per generated task (automatic, must pass):** no-contact reference fails (must-help) or passes with lower quality (optional-help); full-information reference passes; gold path is solvable with rule NPCs; task text contains no hint words ("ask", "verify", "approval from").

**Scale:** ≥ 50 organizations × ~100 tasks = ≥ 5,000 tasks.

### 3.2 Rule-based NPC (`study4/npc_rule.py`)

Deterministic, no API. For colleague u receiving request m in state s:
- If u holds no private record for this task → reply "I don't hold that information" (and, if u's public role makes a referral natural, name the right team, not the person, per the blueprint's release rule).
- Else for each private record of u: release its facts iff every item in `required_context` appears in m (normalized string/number match) **and** all prerequisite steps are satisfied in the episode; otherwise reply with a refusal that names what is missing (e.g., "I need the HR verification ID and the amount").
- Approvals: release only if the requester asks for approval and context is complete.

Unit tests: replay the gold path → all steps released; omit one context item → refusal naming it; ask approver before prerequisites → refusal.

### 3.3 Splits (fixed before any training; record seeds)

| Split | Content | Use |
|---|---|---|
| Train | 40 generated organizations, all their tasks | training |
| Dev-in-org | held-out tasks from training organizations | checkpoint selection |
| Dev-new-org | 5 unseen generated organizations | model selection for generalization |
| **Test-new-org** | 5 more unseen generated organizations (disjoint names, titles, structures) | **final test, touched once** |
| **Test-TribalBench** | the 60 published TribalBench tasks (17-person TAC organization) | external test, touched once |

---

## 4. Phases, deliverables, and gates

### Phase 0 — Ceiling check (no training) · ~USD 10–20 API

Run on the **60 TribalBench tasks**, executor = GPT-5.4-mini, LLM NPCs (paper setup), 4 arms:

| Arm | when + whom | what (request content) |
|---|---|---|
| A | executor decides alone (native) | executor writes |
| B | **oracle** (from gold DAG) | executor writes |
| C | executor decides alone | **rule completion**: attach all obtained values relevant to the target step |
| D | oracle | rule completion |

Oracle controller: at each decision point, if some step is ready (prerequisites satisfied) and not yet satisfied, ASK its cheapest admissible recipient; if all steps satisfied, SUBMIT; else SELF.

**Deliverable:** table of completion, T, R, excess cost, N_auth, N_waste per arm; 3 runs per arm.
**Gate:** proceed only if (B − A) or (D − A) in mean R ≥ 0.10. If both gaps are small, **stop and report**: the bottleneck is the executor, not the controller.

### Phase 1 — Executor protocol fix · local + mock

- One shared tool schema and one progress prompt for all arms; SELF executes exactly one ordinary action; SUBMIT ends the episode; ASK sends, waits for the reply, and appends it.
- Add an "already written / already posted" public progress hint to prevent repeated posting.
- **Gate:** mock replay of 20 gold paths completes and submits in 20/20; a fixed always-SELF controller with the fixed executor submits in ≥ 90% of episodes.

### Phase 2 — Generator + rule NPC · local

- Implement §3.1 and §3.2 with unit tests; generate splits.
- **Gate:** ≥ 98% of generated tasks pass automatic validation; the oracle controller (with rule NPCs and the fixed executor) reaches ≥ 90% completion on Dev-new-org. If not, the generator or NPC is wrong — fix before training.

### Phase 3 — Supervised pretraining on oracle labels · single GPU

- For every key decision point on oracle rollouts **plus** perturbed rollouts (inject random wrong contacts, skipped steps, missing values, then let the oracle recover), compute labels from the gold DAG:
  - when: ASK if some step is ready and unsatisfied; SUBMIT if all satisfied; else SELF.
  - whom: admissible recipients of the ready step (multi-label; use the cheapest as primary).
  - what: include obtained values that appear in the target step's `required_context`.
- Loss: cross-entropy for when (class-weighted to balance ASK/SELF/SUBMIT), softmax CE over candidates for whom, binary CE for what. lr 1e-4, cosine, warmup 3%.
- **Sanity first:** overfit 200 states to ≥ 98% accuracy on all three heads. If this fails, fix the model/representation before scaling.
- Report per head: precision/recall/F1 for ASK, top-1 whom accuracy, what F1; never only overall accuracy.
- **Gate:** on Dev-new-org (rule NPCs, full episodes) mean R ≥ 0.9 × oracle R, and whom top-1 ≥ 0.85.

### Phase 4 — Reinforcement learning on R · single GPU

- Initialize from Phase 3. Online RL with rule NPCs: **GRPO** (group size 8 rollouts per task; KL to the Phase-3 policy, β = 0.02) or PPO if GRPO is unstable. Reward = R at episode end; no shaping beyond R.
- Train on a mix: 70% must-help, 30% optional-help; include refusals, delegations, and threshold tasks.
- What RL must add beyond imitation: recovery after refusal, optional-help cost/benefit (when asking is worth it), fewer redundant contacts.
- **Gate:** on Dev-new-org, mean R exceeds the Phase-3 policy with a paired 95% bootstrap interval excluding 0; no increase in N_auth.

### Phase 4b — Offline RL comparison (proposal fidelity) · single GPU

- Collect a randomized-behavior dataset with rule NPCs (behavior = ε-mixture of oracle and uniform random over legal actions; **log behavior probabilities**). Train IQL (or CQL) on the same model with reward R.
- Purpose: answer whether a company could learn the controller from logs without a simulator.

### Phase 5 — Final evaluation (run once, after freezing everything)

Freeze checkpoints, prompts, weights, and executor before touching test sets.

**Arms**

| Arm | Description |
|---|---|
| P-small | Same Qwen backbone, zero-/few-shot prompting for when/whom/what |
| P-frontier | GPT-5.4 and Claude prompting as controller (same interface) |
| Native | Executor decides alone (no controller) |
| Seq | Two separately trained models: when-only, then whom-only (same data/budget) |
| L-when | Learned when; whom/what by prompting |
| L-ww | Learned when + whom; what by executor |
| **L-full** | Learned when + whom + what (Phase 4) |
| L-offline | Phase 4b policy |
| Oracle | Upper bound |

**Test sets:** Test-new-org (rule NPCs and LLM NPCs) and Test-TribalBench (LLM NPCs, paper setup). 3 runs per arm per task.

**Metrics:** R (primary), completion, T, excess interruption cost, N_auth, N_waste, ASK precision/recall, whom accuracy, requests refused. Paired task-level bootstrap CIs; Holm correction across arm comparisons against L-full.

**Weight sensitivity:** recompute R for λ ∈ {0.02, 0.05, 0.1, 0.2}, μ ∈ {0.1, 0.3, 0.5}, ν ∈ {0.05, 0.1, 0.2}; report whether L-full's rank changes.

**Success criteria for RQ4**
1. L-full > P-small and > P-frontier on R on Test-new-org (CI excludes 0).
2. L-full ≥ Seq and L-ww (joint and "what" add value).
3. L-full on Test-new-org retains ≥ 80% of its Dev-in-org R (generalization).
4. Results hold with LLM NPCs on Test-TribalBench (transfer from rule NPCs).

Report all criteria honestly, including failures.

---

## 5. Repository layout (create under `research/study4/v2/`)

```
research/study4/v2/
  README.md                 phase status + how to reproduce
  gen/                      organization + task generator, validation
  npc_rule.py               rule-based colleagues + tests
  executor/                 fixed executor protocol (shared by all arms)
  controller/               model, heads, data builder, training scripts
  oracle.py                 gold-DAG oracle controller + label builder
  eval/                     arms, metrics, bootstrap, sensitivity
  reports/phase{0..5}.md    gate results per phase (numbers + decision)
  configs/                  frozen configs with seeds and hashes
```

Use the TribalBench scorer from `Shuboya1030/tribalbench` (`scorer/scorer.py`, `tribalbench-1.0`); do not fork its R definition.

---

## 6. Budget and approvals

| Phase | Compute | API (est.) | Needs approval |
|---|---|---|---|
| 0 | none | USD 10–20 | yes (before running) |
| 1–2 | local | 0 | no |
| 3 | 1 GPU, hours | 0 | no |
| 4 / 4b | 1 GPU, 1–2 days | 0 | no |
| 5 | 1 GPU | USD 30–60 (LLM NPC + frontier prompting arms) | yes (before running) |

Report actual spend in each phase report. Do not run Phase 5 test sets more than once; if a bug is found after testing, report it, fix it, and label any re-run as a re-run.

## 7. Reporting rules

- Every phase report states: what was run, exact configs/seeds, gate outcome, and the next decision.
- Report utility components (T, excess C, N_auth, N_waste) with every R.
- Do not tune weights, prompts, or thresholds on test sets.
- If a gate fails, stop and report rather than lowering the gate.

## 8. Expected paper (Study 4)

If the success criteria hold, the paper's contributions are: (1) a procedural generator and rule-based colleague simulator for multi-person help-seeking; (2) a controller that jointly decides when, whom, and what to ask and generalizes to unseen organizations; (3) an analysis of the separate contributions of when, whom, and what, and of online versus offline RL.
