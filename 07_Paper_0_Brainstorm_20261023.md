# Paper 0 Brainstorm: Role-Aware Help-Seeking

> Status: discussion draft, not a finalized protocol. Prepared 2026-10-23 from the current proposal, publication plan, hypotheses/experiment-design document, and feasibility pilot. The first planned paper is a 4–6 page workshop paper on problem definition and preliminary evidence, scoped to RQ1–RQ2.

## 1. Project context and Paper 0's job

The PhD research line asks how an LLM agent serving multiple people in an organization should decide **when to ask for help and whom to ask**. Colleagues may differ in task knowledge, action-specific authority, and the cost of interrupting them. The project roadmap separates this into:

- **Paper 0 (workshop short paper):** establish that help-seeking is a meaningful failure surface and probe whether role information helps. It should motivate the research program, not claim to solve the full problem.
- **Paper 1:** characterize help-seeking more comprehensively, extend the benchmark, and compare models.
- **Paper 2:** learn a joint when-and-whom policy.
- **Paper 3:** study team structure as a moderator.
- **Later work:** validate selected findings with human participants.

### Recommended central story

> Enterprise agents can fail at the communication steps needed to finish a task. A controlled probe asks whether giving an agent information about colleagues' roles improves valid help-seeking, especially when task knowledge and decision authority belong to different people.

Keep the short paper's center of gravity on **diagnosis + a small causal probe**. Avoid turning it into a full benchmark paper, an RL-method paper, or a cost-optimization paper.

## 2. Questions and hypotheses to discuss

### RQ1 — What help-seeking failures appear in existing enterprise-agent trajectories?

Use TheAgentCompany trajectories to describe how often agents reach the relevant communication surface, contact required colleagues, contact irrelevant colleagues, use answers, or repeat requests. Keep this an observational question.

- **H1 (association, not causation):** trajectories with greater coverage of required help sources will have higher task/checkpoint success than trajectories that omit required sources.
- **Exploratory question:** which failure categories are most common: failure to reach chat, omission, wrong person, no follow-up, or redundant contact?
- Do not interpret contact coverage as a causal effect. Harder tasks may both cause more missed contacts and lower task scores.

### RQ2 — Does role information improve valid help-seeking?

In a controlled text environment, vary the information available about candidate colleagues and whether knowledge and authority are held by the same person.

- **H2a:** role information (prose or structured) improves valid help-seeking relative to names/neutral IDs only.
- **H2b (format, initially exploratory):** with the same facts, a structured profile may improve valid routing relative to prose. A null result is meaningful: the benefit may come from information content, not structure.
- **H2c:** the benefit of role information is larger when the knowledge holder and authorized decision-maker are different people, because the agent must compose a valid multi-person path.

Treat RQ2 as the primary causal claim. H2b should not be presented as a confirmed directional hypothesis until there is a stronger reason to expect structure itself to help.

## 3. Study 1 — Trajectory diagnosis

### Data and unit

Start from the public TheAgentCompany runs with tasks that have colleague/scenario information. The pilot reports 40 tasks with `scenarios.json` (39 usable) and 400 public trajectories, of which 390 entered its current analysis. Reproduce these counts and exclusions before writing the paper; the unit should be a task–model trajectory, with individual contact events nested within it.

### Coding

Use an auditable codebook for:

1. reached the communication UI or was UI-blocked;
2. required contact omitted;
3. correct information source contacted;
4. unauthorized person asked to approve/decide;
5. answer followed up and used;
6. unnecessary or repeated contact.

Separate **task text that explicitly names the colleague** from tasks where the target must be inferred. The former measures execution/adherence more than role-aware selection. Have human annotators audit the automatic contact parser and independently code a subset; report agreement and adjudication rules.

### Analysis and interpretation

Report category prevalence with denominators and uncertainty. Show the association between contact coverage and task outcome, controlling or stratifying for task and model where possible. Report UI-blocked traces separately; do not treat them as deliberate decisions not to ask. The current pilot's strong coverage–success gap is motivation for an audited analysis, not proof that asking caused success.

## 4. Study 2 — Controlled role-information probe

### Minimal factorial design

Use a paired, task-level design with:

- **Profile condition:** R0 = neutral candidate IDs/names only; R1 = natural-language role descriptions; R2 = structured role profiles.
- **Knowledge–authority configuration:** aligned (one colleague can provide the needed information and authorize the action) vs. separated (the information source and authorized decision-maker differ).

R1 and R2 must encode the **same semantic facts**. Otherwise, a R2 advantage cannot be attributed to structure. Randomize candidate ordering and neutral IDs. Keep cost equal and do not vary interruption penalties in Paper 0; cost sensitivity belongs to the later RQ3 study. This also avoids repeating the pilot's confound, where R2 changed both profile format and the cost instruction.

Profiles should identify expertise/authority at a useful level, not reveal the answer itself. NPC responses and permissions should be scenario-constrained; evaluate with deterministic rules rather than an LLM judge. Add distractors who are knowledgeable but unauthorized, authorized but uninformed, or plausibly relevant but unable to answer the exact question.

### Outcomes

- **Primary:** valid help-seeking path completion (the agent obtains the needed information from a valid source and gets required approval from an authorized person).
- **Secondary:** first-contact validity, task/checkpoint success, unauthorized requests, wrong-person requests, missed consultations, follow-up, redundant contacts, and number of queries.

Avoid making a hand-chosen weighted reward the primary result in this short paper. Report the components separately; a cost-weighted objective needs its own justification and sensitivity analysis.

### Scale and execution

Begin with a pilot of matched scenario pairs to check that tasks are understandable, conditions are genuinely equivalent, rule-based scores work, and outcomes are not at ceiling/floor. Then set the final number of task templates using a power/sensitivity analysis based on between-task variation. A few repeated model calls do not replace independent scenario templates.

For a short-paper scope, compare a small, preselected set of models (for example, one strong proprietary model and one or two open/API alternatives) rather than building a model leaderboard. Pair each model–task seed across R0/R1/R2, randomize condition order, and freeze prompts, decoding settings, candidate order rules, and task specifications before the confirmatory run.

### Analysis

Pre-register one primary endpoint and the planned contrasts. A mixed-effects logistic model is a reasonable starting point for valid-path completion, with profile condition, alignment, their interaction, and model as fixed effects and scenario template as a random effect. Use appropriate count models for query counts. Report effect sizes and uncertainty, not only p-values. Keep additional error categories descriptive if the sample is too small for reliable interaction tests.

## 5. What the paper should and should not claim

### Claims it could support, depending on results

- Existing trajectories contain identifiable communication/help-seeking failures (after manual/parser audit).
- Contact coverage is associated with task outcome in the observed benchmark traces.
- Providing role information changes help-seeking behavior in a controlled simulation.
- Knowledge–authority separation is a meaningful stress condition for role-aware help-seeking.

### Claims to defer

- Role-aware help-seeking is solved or generalizes to real organizations.
- Structured profiles are inherently better than prose (unless the comparison holds semantic content constant and has adequate power).
- The agent learned a general optimal policy.
- A particular interruption-cost weighting represents real human burden.
- Any result from the tiny 3-scenario pilot is a robust model-level finding.

## 6. Likely short-paper structure

1. **Title and abstract:** problem, evidence source, controlled probe, main result once known.
2. **Introduction:** one concrete workplace scenario; why “when” alone is incomplete without “whom”; narrow research questions and contributions.
3. **Problem framing and related work:** human-agent help-seeking, multi-user/multi-principal agents, expert routing; position the gap as a different setting and decision, not as prior work being wrong.
4. **Study 1: trajectory audit:** data, codebook, exclusions, reliability, descriptive/associational results.
5. **Study 2: controlled probe:** environment, factorial conditions, NPC rules, metrics, baselines, analysis plan.
6. **Results:** separate observational and causal evidence; include uncertainty and null findings.
7. **Discussion:** what role information does/does not buy, implications for future benchmarks and joint when–whom policies.
8. **Limitations and conclusion:** UI/tool confounding, benchmark scope, simulated colleagues, stipulated roles, sample size, external validity.
9. **Appendix/repository artifacts:** scenario schemas, prompts, annotation guide, parser audit, scoring code, model/version/date, exclusions, and license/provenance notes.

### Possible figures/tables

- Figure 1: the help-seeking decision and role dimensions (knowledge, authority; cost held fixed here).
- Figure 2: audited error-category rates and contact-coverage/task-outcome association, with UI-blocked cases visible.
- Figure 3: valid-path completion by R0/R1/R2 and knowledge–authority alignment, with uncertainty intervals.
- Table 1: related-work comparison focused on multiple humans, proactive help-seeking, role/authority, and multi-step tasks.
- Table 2: condition definitions and primary/secondary metrics.

## 7. Main vulnerabilities to resolve before running the confirmatory study

1. **Observational confounding:** successful/easier trajectories may also be more likely to reach chat. Use Study 1 for motivation, not causal language.
2. **Task wording gives away the answer:** audit whether TAC explicitly names whom to contact; anonymize and balance instructions in the controlled tasks.
3. **Profile-content confound:** R1 and R2 must contain identical information; cost cues should be held fixed or tested as a separate factor later.
4. **Ceiling effects:** the pilot's R2 profiles almost state the exact mapping, and the three scenarios are too few. Add plausible distractors and enough diverse templates without hiding ground truth from the evaluator.
5. **Path-length confound in alignment:** separated knowledge/authority naturally needs more contacts. Match scenario pairs and report first-contact validity alongside end-to-end path completion.
6. **Repeated calls are not independent samples:** use scenario templates as the primary sampling unit and model repeated stochastic runs appropriately.
7. **Simulator validity:** scripted colleagues give deterministic scoring but may overstate real-world behavior. Make claims about the benchmark setting and reserve human validation for later work.
8. **Small, shifting literature gap:** rerun targeted literature searches before submission; current repository survey is explicitly preliminary.

## 8. Decisions for our next brainstorm round

1. Should Paper 0's main contribution be (A) a rigorous trajectory diagnosis, or (B) a controlled causal test of role information? Recommendation: B as the central claim, A as motivation, provided the controlled experiment is ready; otherwise make A the honest short paper and label Study 2 preliminary.
2. Should RQ2 test only information availability (R0 vs. R1/R2), or also the representation-format effect (R1 vs. R2)? Recommendation: include both only if semantic parity is enforced and the task count supports the contrast.
3. Should the short paper include the alignment moderator? Recommendation: yes as the theoretically central stress condition, but only with matched scenario pairs and first-contact validity as a diagnostic.
4. What exactly counts as the action needing authority—budget approval, access grant, or task sign-off? Choose one primary action type for the first version and keep the other as a later extension.
5. Which two or three models are affordable and reproducible for the workshop deadline? Decide before expanding the task set.

---

This is a working brainstorm to revise together. It does not replace the project proposal or claim that any hypothesis has been confirmed.

## 9. A2 feasibility: what it means to rerun an AgentCompany trace

I inspected `research/pilot/traj/sample.gz` directly. It is a 54-event trajectory, not a plain transcript: events include the task instruction, OpenHands/browser actions, rendered observations, model-response metadata, and the final `finish` action. `events.json` has 400 parsed trajectory rows; `rq1_rows.json` has 390 scored rows. The parser in `research/pilot/parse.py` infers visited Rocket.Chat rooms and sent messages from browser traces, while `rq1.py` compares contacted colleagues with `scenarios.json` targets.

One sampled interview-selection task explicitly tells the agent to contact Chen Xinyi. The trace shows the agent asking Chen for eligible interviewers, repeatedly waiting for follow-up, and finishing without a confirmed interviewer. This is useful evidence about interaction/follow-up failure; it is not a clean test of whether a profile helps the agent choose Chen, because the task instruction already names her.

### Three different meanings of “rerun”

1. **Re-score/annotate old traces:** add the role roster and re-evaluate who was contacted, whether each request was valid, and whether the answer was used. This is cheap and useful for diagnosis. It cannot estimate how the same agent would behave under profiles because its recorded actions do not change.
2. **One-step counterfactual replay:** at selected decision points, provide the recorded prefix plus the role profiles and ask a model what action it would take next. This tests local routing decisions, but not the full task: subsequent NPC replies, browser state, and downstream actions are not generated by that counterfactual choice.
3. **End-to-end rerun:** reset the task environment for every condition, add the profile to the agent's context/harness, and let the agent execute again. This is the appropriate design for an A2 causal claim about profile effects on task-level help-seeking.

### Do we need to deploy our own LLM?

No. The agent under test can call a hosted model API; the local runner needs the model name, base URL, and API key. A locally served open-weight model is an option, not a requirement. Full TheAgentCompany runs additionally require the benchmark's Dockerized work environment and servers; NPCs and some evaluators may also use a separately configured environment LLM. See the official [TheAgentCompany setup](https://github.com/TheAgentCompany/TheAgentCompany) and [evaluation instructions](https://github.com/TheAgentCompany/TheAgentCompany/blob/main/evaluation/README.md).

The existing pilot `research/pilot/sim.py` already demonstrates a lighter path: it calls an Anthropic-compatible API for the task agent and uses scripted, scenario-constrained colleague replies plus deterministic scoring. It does not need a locally deployed LLM or the full GitLab/Plane/ownCloud/Rocket.Chat stack.

### Recommendation for Paper 0

Use the original traces for Study 1 diagnosis. For Study 2, expand the text simulator into matched, profile-condition variants, reset each scenario for each run, and call hosted models through an API. Keep colleague answers and permissions rule-based so the treatment is the agent's available role information and the outcome is reproducibly scored. Do not call this a rerun of the original traces; call it a controlled TAC-derived simulation.

If ecological validity becomes a concern, rerun a small, preselected subset in full TAC/OpenHands after the simulator result. Do not start by rerunning every trace/task: the official harness runs real agent interactions in task containers, can take days for the full evaluation, and requires the benchmark services and Docker setup.

### Key design implication

Some original TAC task prompts already name the colleague the agent must contact (the pilot notes this for 24 of 40 scenario tasks). Those tasks are unsuitable as the main test of **whom selection**. Either exclude them from that causal estimand or rewrite them into matched variants where the goal and hidden answer stay fixed but the target is not named. Keep original wording only for the trace-diagnostic study, and label it as instruction-following/communication execution evidence.
