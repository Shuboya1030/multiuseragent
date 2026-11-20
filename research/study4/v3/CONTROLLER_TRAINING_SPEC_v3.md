# Study 4 v3 — LLM-Backbone Help-Seeking Controller: Training Spec

**Date:** 2026-11-16 · **Author:** paper/design session · **Implementer:** experiment agent
**Goal (from the researcher):** train a controller that measurably improves utility, and publish it.
**Supersedes for implementation:** `STUDY4_CONTROLLER_DESIGN_v1.md` §2–§5 (v1 remains the background). Keep v1, v2 and all reports; do not delete.

Read first: `v2/reports/PHASE0_81_TRAINING_HANDOFF_ZH.md` (Phase 0 evidence), `v3/STEP1_ASK_AUDIT.md` (ASK failure audit).

---

## 0. What the evidence says the controller must learn

| Evidence (20 paired Phase-0 tasks, 1 run) | Implication |
|---|---|
| Forced gold routing (B) raised T .365 → .565, full-content correct 1/20 → 7/20 | Asking the right people at the right steps does buy quality |
| B lost on cost: 5.45 asks/episode vs .85; R .308 → .140 | The controller must learn **when to stop** |
| B+D ASKs: 27% useful, 43% refused, 13% repeat-after-refusal, 18% stale value | It must learn **what to include** (confirmed values, fixes for refusals) |
| Native first ASK 25/25 to an admissible person; later ASKs 4/13 to non-admissible | **Whom** matters mainly for later steps, and "no further ask" is a valid option there |
| Max same-person loop 63 asks | Hard loop guards are mandatory |

The controller therefore decides **when (incl. stop) + whom + what**, and its main value should be: ask when needed, include the right confirmed values, stop when further asking does not pay.

---

## 1. Paper claims and the experiments that support them

| Claim | Required result |
|---|---|
| C1. A learned controller improves utility over prompting | L-RL > A2 (improved-prompt native mini) and > P-frontier on R, paired CI excludes 0 |
| C2. It beats fixed rules | L-RL > B2 (capped router + fact table rules) on R |
| C3. It generalizes to unseen organizations | Test-new-org R ≥ 80% of Dev-in-org R; holds with LLM NPCs on TribalBench |
| C4. RL adds value beyond imitation | L-RL > L-SFT on R; fewer repeats/refusals at equal or better T |
| C5. Each head matters | Ablations: when-only, when+whom, full |

Report all claims honestly, including failures.

---

## 2. System

| Component | Model | Trained? |
|---|---|---|
| Controller | `Qwen/Qwen2.5-1.5B-Instruct` + LoRA (r=16, α=32, all attn+MLP proj) + 3 heads | **Yes** |
| Executor | `gpt-5.4-mini-2026-03-17`, reasoning none, **with the fact-ledger prompt from `v3/step4_run.py`** | No |
| NPC (train/dev) | Rule NPC (§4) | No |
| NPC (final eval) | `gpt-5.4-mini` with frozen R1 scenarios (Phase-0 NPC) | No |

Do **not** use Haiku. Use OpenAI models for all API roles. Do not access pypi.org / files.pythonhosted.org; use the company pip mirror only.

Scale to Qwen2.5-3B only if the SFT gate (§6.2) fails for capacity reasons (train fits but dev fails *and* overfit check passes on 3B but not 1.5B).

---

## 3. Controller interface

### 3.1 When it is called
At episode start; after every colleague reply; when the executor proposes `write_file` on the deliverable or `submit`; every 4 executor steps. Otherwise the executor acts alone. Max 24 executor steps per episode.

### 3.2 Input (public information only)

Serialized text, fixed order, ≤ 6k tokens (truncate oldest non-reply events first; never truncate FACTS, REFUSALS, CANDIDATES):

```text
<TASK> {instruction}  OUTPUT_FIELDS: {fields}
<DOCS> {path}: {content} ...
<FACTS>
  <VAL_0> key=allocation value=A-9 source=Li Ming reply#1 supersedes_doc=yes
  <VAL_1> ...
<REFUSALS>
  Liu Qiang (ask#1): needs current revision, 6 replicas, current window
<CANDIDATES>
  <CAND_0> title | responsibilities | approval scope | cost=2 | asked=2 | refused=0 | last_reply_summary
  <CAND_1> ...
<HISTORY> (most recent first, truncated)
<STATE>
```

- FACTS is built by a deterministic **fact extractor** from reply text only (keys from the task's output fields and from value tokens; reply values override doc drafts for the same key). It must not read gold.
- **Never** input: gold DAG, private NPC records, `required_context`, evaluator output, task class (must/optional).

### 3.3 Output heads (hidden state at marker tokens → small MLP, 2 layers, hidden 512)

1. **Action** (from `<STATE>`): `SELF` | `ASK` | `SUBMIT`. SELF and SUBMIT are the no-ask options.
2. **Whom** (from each `<CAND_i>` concatenated with `<STATE>`): one score per candidate; softmax over legal candidates. No name tokens are generated.
3. **What** (from each `<VAL_j>` concatenated with `<STATE>`): include / exclude.

On ASK the system builds `{intent sentence} + included values (key: value)` and the executor only rephrases; a check rejects a message that drops any included value (re-prompt once, then send the template text).

### 3.4 Hard guards (always on, all arms incl. baselines)
- Max 2 asks to the same person while no new FACT was added since the last ask to them → force SELF.
- Max 12 asks per episode → force SUBMIT path.
- Guards are reported as counts; they are a safety net, not the method.

---

## 4. Environment

### 4.1 Procedural generator (`v3/gen/`)
Output in TribalBench blueprint format so the vendored scorer `tribalbench-1.0` works unchanged.

- Organizations: 8–30 people; departments, titles, reporting lines, per-action authority (e.g., approves ≤ USD 10k), delegations, cost 1/2/3 by seniority. Name and title pools **disjoint** across splits.
- Task templates (depth 1–4): single info; info → approval; parallel → join; referral chain ("ask X" → X points to team → Y holds it); delegation; threshold approval; **stale-draft trap** (docs contain an outdated value that a reply corrects).
- Must-help ~60%, optional-help ~40%. Optional: valid baseline from docs; a colleague holds an improvement worth a known quality gain.
- Distractors: same-department non-holder, outdated owner, approver below threshold.
- Validation per task (must pass): no-contact reference fails (must) / passes lower quality (optional); full-info reference passes; gold path solvable with the rule NPC; prompt has no hint words ("ask", "verify", "approval from").
- Scale: ≥ 50 orgs × ~100 tasks.

### 4.2 Rule NPC (`v3/npc_rule.py`), deterministic, no API
For person u receiving message m:
- u holds nothing for this task → "I don't hold that." If the blueprint gives a referral, name the **team**, not the person.
- u holds record r: release iff every `required_context` item appears in m (normalized string/number match) **and** prerequisites are released in this episode; else refuse **naming what is missing**.
- m contains a value that contradicts an already-released value for the same key → refuse and state the correct value is needed (models the stale-value failure).
- Approvals only when explicitly requested and context complete.
- 10% stochastic phrasing variants (synonyms, reordered sentences) so the controller does not overfit exact strings.

Unit tests: gold replay releases all; drop one context item → refusal naming it; stale value → refusal; approver before prerequisites → refusal.

### 4.3 Splits (freeze before training; record seeds and hashes)

| Split | Content | Use |
|---|---|---|
| Train | 40 generated orgs | SFT + RL |
| Dev-in-org | held-out tasks of train orgs | checkpoint selection |
| Dev-new-org | 5 unseen orgs | model selection |
| **Test-new-org** | 5 more unseen orgs | final, run once |
| **Test-TribalBench** | 60 published tasks, LLM NPC | final, run once |

The 20 Phase-0 paired tasks are TribalBench tasks: they may be used for **debugging only**, and results on them are labeled dev, not test.

---

## 5. Labels (oracle, for SFT only)

At each decision state compute from the gold DAG and the episode's released set:
- **Action**: SUBMIT if all must-steps released (and, for optional tasks, if remaining gain < cost penalty of the cheapest ask, i.e. `quality_gain < λ·cost`); ASK if a step is ready and unreleased **and** the request can be made complete from current FACTS (or the step needs no context); otherwise SELF.
  - After a refusal with no new FACT since → SELF (not ASK).
- **Whom**: admissible recipients of the first ready step (multi-label; cheapest = primary).
- **What**: include FACTS whose key is in that step's `required_context`; exclude others.

Data = oracle rollouts **+ perturbed rollouts**: inject wrong contact, stale value in request, missing context, premature approval request, then let the oracle recover from the resulting state. Target mix of states: ≥ 30% ASK, ≥ 30% SELF, ≥ 15% SUBMIT, ≥ 25% post-refusal states.

---

## 6. Training

### 6.1 Environment for compute
- 1× A100 80GB or H100 (cloud). Estimated: SFT 2–4 h, GRPO 24–48 h. Get budget approval from the researcher before renting.
- Packages via company mirror: torch, transformers, peft, accelerate. No pypi.

### 6.2 Stage 1 — SFT
- Loss: CE(action, class-weighted inverse frequency) + CE(whom over candidates) + BCE(what). Equal weights.
- lr 1e-4 cosine, warmup 3%, batch 32 states, 3 epochs, bf16.
- **Sanity first:** overfit 200 states to ≥ 98% on all three heads. If it fails, fix representation before scaling.
- Report per head: ASK P/R/F1, SUBMIT P/R, whom top-1 (only at states where a step is open), what F1. Never only overall accuracy.
- **Gate (Dev-new-org, rule NPC, full episodes):** mean R ≥ 0.85 × oracle R; whom top-1 ≥ 0.85; asks/episode ≤ 1.5 × oracle.

### 6.3 Stage 2 — GRPO on R
- Init from SFT. Group size 8 rollouts per task; advantage = R_k − mean(R_group), normalized by group std.
- Reward = TribalBench `R` at episode end (λ=.05, μ=.3, ν=.1, C* exempt). **No other shaping.**
- KL to SFT policy, β = 0.02; lr 1e-5; clip 0.2; sample actions from heads with temperature 1.0.
- Mix: 70% must / 30% optional; 90% rule NPC, 10% LLM NPC (needs API approval; skip if not approved and report).
- Executor during RL: **gpt-5.4-mini is too costly for RL rollouts.** Use a **local executor stub** for RL: deterministic template executor that (a) reads all docs, (b) sends the controller's built message verbatim, (c) writes the deliverable from FACTS (reply values) falling back to docs, (d) submits on SUBMIT. Document this; final evaluation uses gpt-5.4-mini.
- Monitor every 100 steps: mean R, T, asks/episode, must ASK recall, repeat-after-refusal rate, optional ask rate, KL. Stop and roll back if asks/episode → 0 or > 2× oracle.
- **Gate:** Dev-new-org R > SFT with paired bootstrap 95% CI excluding 0; N_auth not higher.

### 6.4 Seeds
3 training seeds for SFT and RL; report mean ± sd.

---

## 7. Evaluation (freeze everything first; run once)

### 7.1 Arms (all with the same executor, guards and NPC)

| Arm | Description |
|---|---|
| A | Native mini, original Phase-0 prompt |
| A2 | Native mini, fact-ledger prompt |
| B2 | Public rule controller (no gold): ask the latest referral target, else the candidate whose responsibilities best match an unfilled output field; include all FACTS; max 2 asks/person; SUBMIT when all output fields have a FACT or doc value |
| P-small | Qwen2.5-1.5B prompted (no training) through the same heads interface (zero-shot via generation, parsed) |
| P-frontier | gpt-5.4 prompted as controller, same interface |
| L-when | Learned action head; whom/what by prompting |
| L-ww | Learned action + whom; what = include all FACTS |
| L-SFT | Full controller after SFT |
| **L-RL** | Full controller after GRPO |
| Oracle | Gold-DAG controller with stop rule (upper bound) |

### 7.2 Test sets
Test-new-org (rule NPC and LLM NPC) and Test-TribalBench (LLM NPC). 3 runs per arm per task.

### 7.3 Metrics
R (primary), T, base_pass, excess C, N_auth, N_waste, asks/episode, must ASK recall, stop accuracy, repeat-after-refusal rate, later-ask whom accuracy (only where a step is open), refusals. Paired task-level bootstrap CIs; Holm correction across comparisons vs L-RL. Weight sensitivity: λ ∈ {.02,.05,.1,.2}, μ ∈ {.1,.3,.5}, ν ∈ {.05,.1,.2}.

### 7.4 Budget
LLM-NPC + gpt-5.4-mini executor for 10 arms × (60 + ~200) tasks × 3 runs is large. Run Test-TribalBench full; subsample Test-new-org to 100 tasks for LLM-NPC arms. Estimate cost before running and get approval. Use a USD hard cap in the caller.

---

## 8. Phases and gates

| Phase | Output | Gate | API |
|---|---|---|---|
| P1 Step-4 check | A2/B2/D2 on 20 paired tasks (`v3/step4_run.py`) | none — informs scope only | ~USD 20 |
| P2 Env | generator, rule NPC, fact extractor, executor stub, tests | ≥ 98% tasks validate; oracle ≥ 90% completion on Dev-new-org | 0 |
| P3 SFT | checkpoints, per-head report | §6.2 | 0 |
| P4 GRPO | checkpoints, curves | §6.3 | 0 (or small, LLM-NPC mix) |
| P5 Final eval | tables, CIs, ablations | report only | approval needed |

If a gate fails: stop, report numbers and the most likely cause, propose one fix. Do not lower the gate.

## 11. Worked SFT examples (illustrative; regenerate from real blueprints)

One sample = one decision state (input text) + labels for the three heads. A task yields 4-10 samples.

1. Start, nothing known -> action=ASK, whom={holder of first ready step}, what={} .
2. After replies gave allocation A-9 / 6 replicas / window 02:30 (docs say A-6/4/01:00) -> action=ASK, whom={readiness approver}, what={allocation, replicas, window}=1 (reply values, not doc drafts).
3. Perturbed: approver refused naming missing current values, and FACTS contain them -> ASK same person with those values. If FACTS do NOT contain what was named -> action=SELF (no repeat ask).
4. All must-steps released -> action=SUBMIT; whom/what losses masked.
5. Optional task, gain < lambda*cost -> action=SUBMIT (approximate label; RL refines).

Whom/what losses are masked whenever action != ASK. RL has no per-step labels: only the episode R.

---

## 9. Repository layout

```
research/study4/v3/
  CONTROLLER_TRAINING_SPEC_v3.md   this file
  step1_ask_audit.py, STEP1_ASK_AUDIT.md
  step4_run.py                     P1
  gen/                             generator + validation
  npc_rule.py, test_npc_rule.py
  facts.py                         public fact extractor
  executor_stub.py                 local executor for RL
  oracle_v3.py                     labels with stop rule
  controller/                      model, heads, dataset, sft.py, grpo.py
  eval/                            arms, metrics, bootstrap
  reports/P{1..5}.md               gate results, configs, seeds, spend
  configs/                         frozen configs + hashes
```

Use the vendored TribalBench scorer (`v2/vendor/tribalbench/scorer/scorer.py`); do not fork R.

---

## 10. Reporting rules
- Every phase report: what ran, configs/seeds, gate outcome, spend, next decision.
- Always report R with T, excess C, N_auth, N_waste, asks/episode.
- Never tune on test sets; label any re-run as a re-run.
- Commit/push only when the researcher asks.
