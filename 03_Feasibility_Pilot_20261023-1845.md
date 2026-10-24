# Feasibility pilot: role-aware help-seeking (experiment date: 2026-10-23)

## 0. Purpose and design
**Purpose.** Before committing to the proposal, check three things: (1) whether TheAgentCompany (TAC) data supports the planned studies; (2) whether help-seeking errors are visible in real agent trajectories (RQ1); (3) whether the reward function R = T − λΣc − μN_auth − νN_waste can be computed end-to-end and separates the experimental conditions (RQ2/RQ3).

**Part B: real-trajectory analysis (RQ1).**
- Input: 10 models × 40 NPC tasks from `TheAgentCompany/experiments` (OpenHands 0.14.2 runs, Dec 2024), together with the official checkpoint scores.
- Contact detection: in each trajectory, find RocketChat direct-message rooms (the room header `# first_last`) followed by a send action (fill + Enter), plus @mentions in channels.
- Target people come from each task's `scenarios.json`.
- Categories: ui_blocked (never reached the chat), omitted_all, partial, partial+wrong, complete, complete+extra.

**Part C: text simulator (RQ2/RQ3 prototype).**
- Three scenarios adapted from TAC tasks:
  - equipment purchase, adapted from admin-check-employees-budget-and-reply-2 and extended with an approval step;
  - vendor quote (admin-get-best-vendor-quote);
  - pick interviewer (hr-pick-interviewer-2).
- Each person's knowledge K, authority A, and interruption cost c are specified per scenario. Costs are seniority-based: CTO 5, finance director 3, HR 2, others 1.
- NPC replies are rule-based and scenario-constrained, so evaluation is deterministic.
- Agent protocol: each turn the agent outputs a JSON action, either ask(to, message) or submit(answer); at most 10 turns.
- Conditions:
  - R0: names only;
  - R1: TAC job titles and public info;
  - R2: structured profile (knowledge, authority, cost) plus an instruction about cost.
- Models: claude-haiku-5-5 and claude-sonnet-5-5; 2 repeats each; candidate order shuffled.
- Scoring: T is the share of gold answer fields that are correct; Σc is the summed cost of everyone asked; N_auth counts approval requests sent to unauthorized people; N_waste counts uninformative or repeated asks. The oracle is the minimal valid path.


Code and data: `research/pilot/`. The scripts are `parse.py` and `rq1.py` (real trajectories) and `sim.py` and `score.py` (simulator).

## A. Data check (TheAgentCompany)
- The main repo is MIT-licensed.
- 40 tasks have `scenarios.json` (39 usable). The scenario files state exactly who knows what, which supports rule-based evaluation.
- Number of NPCs per task: 1 NPC in 16 tasks, 2 in 9, 3–5 in 12, 17 in 2.
- In 24 of the 40 tasks, the task text names everyone the agent should contact. So for "whom", the original tasks mostly test whether the agent follows instructions. Distractors and role-only descriptions have to be added (that is our planned extension).
- Public trajectories: 10 models × 40 tasks = 400 trajectories, plus official checkpoint scores.

## B. RQ1 pilot on real trajectories (390 trajectories, automatic parsing, unvalidated)
| Category | Share | Success | Mean score |
|---|---|---|---|
| UI-blocked (never reached chat) | 37.2% | 0% | 0.07 |
| Reached chat, asked no one | 13.6% | 3.8% | 0.11 |
| Partial targets | 14.9% | 0% | 0.15 |
| Partial + wrong person | 9.5% | 0% | 0.15 |
| All targets | 22.1% | 29.1% | 0.53 |
| All targets + extra | 2.8% | 54.5% | 0.74 |

- Success when all targets were contacted: 32.0% (n=97). Success when at least one target was missed: 0.7% (n=293).
- Target coverage by model: Sonnet-3.5 0.71 vs. Nova-Pro 0.01.
- Caveat: the 37% UI-blocked share is a confound. It has to be excluded, and it motivates a text simulator. Contact detection uses heuristics and needs a manual audit.

## C. Simulator pilot (3 scenarios × R0/R1/R2 × 2 models × 2 repeats = 36 runs)
Scenarios are adapted from three TAC tasks: equipment purchase (extended with approval), vendor quote, and pick interviewer. NPC replies follow rules and are constrained by each scenario.

| Model / condition | T | Queries | Cost | N_auth | N_waste |
|---|---|---|---|---|---|
| haiku R0 (names only) | 0.67 | 7.0 | 15.8 | 1.33 | 2.17 |
| haiku R1 (job titles) | 0.83 | 4.7 | 11.3 | 0.33 | 1.33 |
| haiku R2 (structured profile + cost note) | 1.00 | 2.3 | 5.0 | 0 | 0 |
| sonnet R0 | 0.83 | 6.7 | 16.5 | 1.50 | 1.67 |
| sonnet R1 | 1.00 | 5.7 | 14.8 | 1.00 | 1.83 |
| sonnet R2 | 1.00 | 2.7 | 5.3 | 0 | 0 |

Mean reward R = T − λΣc − μN_auth − νN_waste:

| (λ, μ, ν) | haiku R0 | haiku R1 | haiku R2 | sonnet R0 | sonnet R1 | sonnet R2 |
|---|---|---|---|---|---|---|
| (0, 0, 0) | 0.67 | 0.83 | 1.00 | 0.83 | 1.00 | 1.00 |
| (0.02, 0.2, 0.05) | −0.03 | 0.47 | 0.90 | 0.12 | 0.41 | 0.89 |
| (0.05, 0.3, 0.1) | −0.74 | 0.03 | 0.75 | −0.61 | −0.23 | 0.73 |
| (0.1, 0.5, 0.2) | −2.02 | −0.73 | 0.50 | −1.90 | −1.35 | 0.47 |

## Limitations of this pilot (to fix in the real study)
1. R2 mixes two manipulations: structured profiles and the cost instruction. These must be separated (2×3 design).
2. In R2, the profile states outright who knows what. This makes the task close to trivial and is a ceiling effect. Profiles should be noisier or partial, or learned from history.
3. The oracle for pick_interviewer is worst-case, which is why regret can be negative. An expected-cost oracle is needed.
4. The sample is small (n=6 per cell), so these are directional results only. All models are Claude; GPT, Gemini, and open models should be added.
5. N_auth is detected with a keyword heuristic, which is approximate.

## Conclusions
1. **The data is feasible.** TAC is MIT-licensed, `scenarios.json` gives ground truth for rule-based evaluation, and 400 public trajectories are available for RQ1.
2. **The RQ1 signal is strong.** Success is 32.0% when every required colleague was contacted, versus 0.7% when at least one was missed. Models also differ widely in how many required colleagues they cover. This supports H1b and H1c, pending a manual audit.
3. **The reward function works and discriminates.** Task completion alone barely separates conditions; for Sonnet, R1 and R2 both score T = 1.00. With cost and authority terms, the conditions separate clearly; at λ = 0.05, Sonnet R1 scores −0.23 and R2 scores 0.73. One concrete failure mode: without role information, agents escalate small purchases to the CTO and repeat questions to the same person.
4. **Required design changes.**
   - Use a 2×3 design that separates profile form from the cost instruction.
   - Use partial or noisy profiles to avoid a ceiling effect.
   - Distractors are mandatory, because 24 of 40 TAC tasks already name whom to ask.
   - Exclude UI-blocked runs, which are 37% of the TAC trajectories.
   - Use an expected-cost oracle.
   - Add GPT, Gemini, and open models.
   - The proposal says "41 tasks"; it should say 40 (39 usable).
