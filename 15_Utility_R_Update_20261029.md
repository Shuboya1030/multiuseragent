# 15 — Utility R → R′: Why and How to Update the Task Utility (decision note)

**Date:** 2026-10-29 · **Author:** paper/evaluator session · **Status:** decided by user; grader change **not yet applied**
**Audience:** the experiment agent running Study 2 v2 (new tasks). Please read before changing the grader or reporting R.

---

## 1. Summary

- The current task utility R charges interruption cost for **every** contact, including contacts that are **required** to complete the task (must-help tasks cannot be completed without asking the knowledge holders and the approver).
- This charge makes a perfect agent score below 1, does not discriminate between agents, and double-counts some errors.
- We replace R with **R′**, which charges only **excess** interruption cost beyond the cheapest gold path and removes double counting.
- **Do not change the running experiments.** Keep the current grader as is. After all runs finish, recompute R′ (and the sensitivity grid) offline from the saved traces.

---

## 2. Current definition (grader `study2-v2-grader-1.0`)

$$R = T - \lambda\sum_t c_{u_t} - \mu N_{\text{auth}} - \nu N_{\text{waste}},\qquad \lambda=0.05,\ \mu=0.3,\ \nu=0.1$$

The terms:

- **T**: task score.
- **c_u**: per-message interruption cost by roster seniority: CTO/Director 3, Manager 2, others 1.
- **N_auth**: approval-type requests sent to someone without authority.
- **N_waste**: contacts that release nothing.

Source: `research/study2/task_generation_v2/grading/README.md` ("Objective").

## 3. Why change it

| # | Problem | Example (SecureScan must-help: Finance 1 + Security 1 + Director 3) |
|---|---|---|
| P1 | Required contacts are charged, but every correct agent pays the same amount. The charge is a constant offset and does not discriminate between agents. | A perfect agent scores R = 1 − 0.05×5 = **0.75**, not 1. "R = 0.75" has no clear meaning. |
| P2 | Double counting. A useless contact is charged both by c (interruption) and by N_waste; an unauthorized approval request may also count as waste. | Asking the Eng. Manager for approval is penalized three times. |
| P3 | Seniority is only a proxy, and the 3/2/1 values are stipulated. | Reviewers will ask "why 3/2/1?" (addressed by the sensitivity analysis, §6). |
| P4 | λ = 0.05 is small relative to the optional-task quality gain (up to +0.5). R almost always favors asking. | Asking the Director costs 0.15. |

Only the **extra** contacts beyond what the task requires tell agents apart. Those should carry the cost.

## 4. New definition: R′ (cost-adjusted task utility)

$$R' = T - \lambda\cdot\max\big(0,\ C - C^{*}\big) - \mu\,N_{\text{auth}} - \nu\,N_{\text{waste}}^{\neg\text{auth}}$$

| Symbol | Definition | Change |
|---|---|---|
| T | Task score (must-help: field accuracy; optional-help: 0.5 + 0.5·quality if base passes, else 0) | unchanged |
| C = Σ_t c_{u_t} | Actual interruption cost of all agent messages | unchanged |
| **C\*** | **Cost of the cheapest gold path** (§5). Optional-help tasks: C\* = 0 | **new** |
| max(0, C − C\*) | **Excess interruption cost** | **core change** |
| N_auth | Approval-type requests to non-authorized people | unchanged |
| **N_waste^¬auth** | Wasted contacts **not already counted in N_auth** | **no double counting** |
| λ, μ, ν | Defaults 0.05 / 0.3 / 0.1; varied in the sensitivity grid (§6) | unchanged defaults |

**Interpretation.** R′ is the net value of the task to the organization. It equals task quality minus the extra burden the agent placed on colleagues. A correct agent that adds no extra burden scores **R′ = T** (= 1 on must-help). In Paper 0, R′ is an **evaluation objective, not a training reward**. In Study 4 (RL), the same function becomes the reward.

**Optional-help tasks.** These need no special case. C\* = 0, so asking the holder costs λ·c_holder and buys a quality gain of up to +0.5. R′ therefore measures whether asking was worth it.

### Worked examples (SecureScan, C\* = 5)

| Behavior | Old R | **R′** |
|---|---|---|
| Correct 3 contacts in order (C = 5) | 0.75 | **1.00** |
| + asks Eng. Manager for approval (unauthorized; cost 2) | 0.25 | 1 − 0.10 − 0.30 = **0.60** |
| + asks HR (useless; cost 1) | 0.60 | 1 − 0.05 − 0.10 = **0.85** |
| Submits without asking (T = 0) | 0 | **0** |

## 5. Computing C\*

For each task:

1. Read the gold DAG in `blueprint.json` (`gold_dag.nodes`, each node has `admissible_recipients`).
2. For each node, take the **cheapest admissible recipient** by roster cost.
3. Sum one message per node: C\* = Σ_nodes min_{u ∈ A_s} c_u.
4. Use **one message per node** as the minimum. If a node requires a reply round-trip with the same person, count only the agent's outgoing messages, consistent with how C is computed.

C\* depends only on the blueprint and the roster (`organization/roster.json`). It does not use run data.

## 6. Sensitivity analysis (analysis plan item A12)

Recompute R′ over a grid:

- λ ∈ {0.02, 0.05, 0.1, 0.2}
- μ ∈ {0.1, 0.3, 0.5}
- ν ∈ {0.05, 0.1, 0.2}
- cost model: **rank-based** (3/2/1) or **flat** (all 1)

That is 4 × 3 × 3 × 2 = 72 settings.

For each setting, report:

- the model ranking by mean R′, and its Kendall τ against the default setting;
- the sign of the R1−R0 and R2−R1 differences in R′;
- the share of settings that preserve each main conclusion.

Output an appendix table, plus one sentence in Results. No re-runs are needed. Plan reference: `13_Paper0_AAAI_Skeleton_<latest>.md`, items A8 and A12.

## 7. What to do (checklist)

**Now, during the runs (experiment agent):**
- [ ] **Do not modify the grader** used by the running experiments. Keep reporting the old R.
- [ ] Make sure every episode saves (a) the submitted deliverable and (b) the **full message trace**: sender, recipient, content, timestamp, and NPC replies, in order. Totals alone are **not** enough to recompute R′, because removing double counting needs per-contact labels.

**After all runs finish:**
- [ ] Add `C*` computation to the grader (`grading/scorer.py`). Keep the old `R` field and add `R_prime`, `C_star`, `excess_cost`, `n_waste_excl_auth`.
- [ ] Bump the grader version (e.g., `study2-v2-grader-1.1`). Re-run `grading/selftest.py`. The full_gold case must now give R′ = T.
- [ ] Write an **offline re-scoring script** that reads every saved episode (deliverable + trace) and outputs R′ plus all components per episode.
- [ ] Run the sensitivity grid (§6). Save it next to the episode table.
- [ ] Report R′ as the primary utility in the paper. Report the old R in the appendix with a one-line reason for the change.

**Pre-registration note.** This change was decided on **2026-10-29, before the new results were seen**. The reason is design (P1–P4), not results. Keep this file, and the changelog entry in `13_Paper0_AAAI_Skeleton_20261029-1400.md`, as the record.

## 8. Related discussion (for context)

- **Graph view.** The task is a gold dependency DAG. Equivalently, the agent moves on a progress graph whose states are the sets of satisfied steps. The gold path is the cheapest route to completion, and C\* is its cost. Excess cost, path efficiency (|S|/k), and repair rate measure how far the agent deviates from that route.
- **Markov assumption.** Paper 0 frames help-seeking as sequential decision-making under partial observability: the agent cannot see what colleagues know. Nothing is trained in Paper 0. For Study 4 (RL), the paper must state the following explicitly:
  - the state definition. With the full history, the Markov property holds by construction; with compressed features, it is an approximation and must be called out;
  - that NPC behavior is stationary;
  - that R′ decomposes into per-step costs plus the terminal T;
  - the coverage assumptions for offline RL.
