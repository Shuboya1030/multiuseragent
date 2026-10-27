# partimephd memory
## Where to find things
| Need | Location | Caveat |
|---|---|---|
| U of T flex PhD list | https://sgs.calendar.utoronto.ca/graduate-programs-at-a-glance | check each year |
| U of T flex rules | https://www.sgs.utoronto.ca/policies-guidelines/flexible-time-phd-program-option-guidelines/ | |
| UBC part-time PhD list | https://www.grad.ubc.ca/prospective-students/graduate-degree-programs/part-time-doctoral-programs | CS not included |
| UBC part-time policy | https://www.grad.ubc.ca/policies/student-status | |
| Report v1 | report_v1.md | alumni outcomes not yet verified |
| U of T iSchool PhD placement | https://ischool.utoronto.ca/phd-in-information/phd-graduates-where-are-they-now/ | selective list, no denominator |
| Waterloo CS part-time rule | https://uwaterloo.ca/computer-science/current-graduate-students/overview-degree-programs/phd-computer-science | PT only for school employees |
| Report v2 | report_v2.md | |
| User profile file | C:\Users\shuyazong\repos\NIW\niw_context.md | MISSING at given path (2026-10-22) |
| User resume (academic/work background) | C:\Users\shuyazong\repos\Linkedin_jobs_datalake\JobSearch\Shuya_Zong\deliverables\resume_final.md (PDFs: Shuya_Zong_Microsoft_AI.pdf, Shuya_Zong_Data_Final_2026-10-21.pdf) | md is text-readable; PDFs need a parser |
| Google Scholar | https://scholar.google.com/citations?user=IJ9Ph6cAAAAJ&hl=en | blocked by CAPTCHA for automated fetch |
| Research plan | C:\Users\shuyazong\.claude\plans\dreamy-splashing-stream.md | scope: UBC/UofT/Waterloo only, direction-first |
| Per-school sweep outputs | research/uoft.md, research/ubc.md, research/waterloo.md | in progress 2026-10-22 |
| Final report v3 | report_v3.md | sweep not 100% exhaustive; BC teaching-college hiring not yet researched |
| Agent failure lit survey v0.2 | agent_failure_survey.md | ~60 candidates; open-source not verified per paper |
| Agent survey GS raw results | research/gs/q*.json (25 queries, 237 unique) | 🔶 items need official-page check |
| Google Scholar via CDP | web-access skill + user's logged-in Chrome | allow CDP popup; ~15s spacing avoided CAPTCHA (2026-10-23) |
| HAI enterprise collab survey v0.1 | hai_enterprise_survey.md / .html | GS raw: research/hai/gs; abstracts: research/hai/oa.json |
| Enterprise agent trace data (verified 2026-10-23) | TheAgentCompany/experiments (~1.9k traj, checkpoint scores, no license); sierra-research/tau-bench historical_trajectories (MIT); tau2-bench data/tau2/results/final (MIT); appworld `download experiment-outputs` (Apache-2.0); CRMArena results/ (Git LFS, CC BY-NC 4.0); Who&When (MIT); MAST traces + HF mcemri/MAD | none has root-cause labels on enterprise tasks |
| Who-to-ask survey v0.1 | who_to_ask_survey.md/.html; raw research/whom/ | TheAgentCompany npc_definition.json has 17 human roles; 41 tasks with scenarios.json |
| Xiaoxiao Li (UBC ECE, TEA Lab) | https://xxlya.github.io/ ; https://ece.ubc.ca/xiaoxiao-li/ | not in report_v3 DB; fit = RL/agent methods for who-to-ask; UBC ECE part-time policy unverified |
| Workshop targets (checked 2026-10-23) | AAAI-27 Human-AI Collab workshop https://human-ai-workshop-7p350s.webnode.page/ (due 2026-11-20 AoE, Montréal); AAAI-27 workshop list https://aaai.org/conference/aaai/aaai-27/aaai-27-workshop-program/ ; ELLIS multi-agent https://yalidu.github.io/ellis-multi-agent-workshop-2026/ (11-18, non-archival); CHI'27 workshops https://chi2027.acm.org/authors/workshops/ (CFPs 12-17, papers ~2027-02-11); ICLR'27 workshops (list 11-29) | dates from search; confirm on official sites; CHIWORK'27 date unofficial |
| Who-to-ask research proposal v0.1 | who_to_ask_proposal.md/.html | C1 framework / C2 model / C3 LLM comparison; v1 target AAAI-27 workshop 11-20 |
| Who-to-ask hypotheses & experiment design | who_to_ask_hypotheses.md/.html | RQ1-4, H1a-H4c, Exp1-4; v1 scope for 11-20 |
| Co-author proposal (EN) | proposal_who_to_ask_EN.md/.html | draft v0.1; resume source resume_final.md |
| X. Jessie Yang (UMich ICRL) | https://www.si.umich.edu/people/x-jessie-yang | senior author of Chung et al. 2024 team scheme; 2026 multi-human-multi-agent trust papers; US-based, collab only |
| Kate Larson (Waterloo CS) | https://cs.uwaterloo.ca/~klarson/ | multiagent/mechanism design/cooperative AI; Waterloo CS no part-time |
| Proposal short (email attachment) | proposal_who_to_ask_short.md/.docx | ~3 pages; RQ1-3 only; full version proposal_who_to_ask_EN |
| Feasibility pilot | feasibility_pilot_2026-10-23.md; research/pilot/ | 400 TAC traj parsed; 36-run simulator; R computed |
| Related Work writing patterns | related_work_writing_patterns.md | from ReHAC, Multi-User, MAST, Who&When, TAC; templates + checklist |
| **FINAL PhD proposal (send this)** | 01_PhD_Research_Proposal_RoleAwareHelpSeeking_<YYYYMMDD-HHMM>.docx (current: 20261024-1628, merged with remote Study 2 R0/R1/R2 edits) | naming: NN_Title_lastmodified; superseded versions in archive/ |
| Supporting docs | 02_Hypotheses…, 03_Feasibility_Pilot…, 04_Literature_Survey…, 05_Related_Work_Writing_Patterns… | old paths (who_to_ask_*, proposal_who_to_ask_*, feasibility_pilot_*, related_work_writing_patterns.md) moved/renamed |
| Broad Research folder | Broad Research/ | agent_failure_survey, hai_enterprise_survey (.md+.html), plus HTML views of who_to_ask_survey / hypotheses / related_work_patterns; user needs these HTMLs — never delete |
| Archive folder | archive/ | superseded proposal versions; user said do NOT delete |
| Publication plan | 06_Publication_Plan_20261023-1921.md | 4 papers + workshop; deadlines marked confirmed/estimated |
| GitHub repo (private) | https://github.com/Shuboya1030/partimephd | personal account Shuboya1030; memory.md renamed to AGENTS.md (2026-10-23) |
| Study 1 design | 07_Study1_Design_20261023-2053.md | inputs/outputs, formal defs, mixed-effects + checkpoint-level analysis |
| Paper 0 workshop brainstorm | 07_Paper_0_Brainstorm_20261023.md | Discussion draft; not a finalized protocol |
| **Study 2 task redesign (LIVING doc)** | 12_Study2_Task_Redesign_<YYYYMMDD-HHMM>.md | update on every discussion; rename timestamp on edit; decision + change log at bottom |
| Tenured-only advisor lists (filter added 2026-10-26: Assoc/Full Prof only) | research/uoft_tenured.md, research/ubc_tenured.md | ranks partly from search snippets; re-verify profile before emailing |
| **Paper 0 AAAI skeleton (LIVING doc)** | 13_Paper0_AAAI_Skeleton_<YYYYMMDD-HHMM>.md | structure + analysis plan; experiment agent fills [RESULT] slots; this session owns writing/architecture |

## Working rules (user instructions)
- **Do NOT commit/push to GitHub unless the user explicitly asks** (2026-10-26). Keep changes local until told to check in.
- Docker CLI on this machine: `C:/Users/shuyazong/AppData/Local/Programs/DockerDesktop/resources/bin/docker.exe` (not on PATH; prepend to PATH in each shell).
- **Network restriction (company policy, 2026-10-26): do NOT access pypi.org / files.pythonhosted.org.** Use the company pip mirror only; ask before any external package download.


## Advisor preferences & shortlist (updated 2026-10-26)
**User preferences**
- Only tenured advisors (Associate/Full Prof); exclude Assistant Profs & teaching-stream — believes senior profs mean less student pressure.
- Wants agentic / LLM-agent / human-AI focus; rejected Donmez (UofT MIE) as too transportation/driving-focused.
- Must keep Microsoft full-time job; scope UBC + UofT (Waterloo deprioritized for now).

**Ranked shortlist (user's choice)**
1. **Scott Sanner** — Professor, UofT MIE Industrial Eng (x-appt CS, Vector). LLM conversational recommenders (LLM-ConvRec), verifiable LLM reasoning (LLM-TRes), agentic planning. MIE flex PhD = allowed. Email ssanner@mie.utoronto.ca; lab https://d3m.mie.utoronto.ca/ (no prospective-student instructions, recruiting status unknown). Draft outreach email written 2026-10-26 (not yet sent); user nervous about first email.
2. **Eric Baumer** — Assoc Prof, UofT iSchool (since Jul 2025; tenured at Lehigh). Human interaction with AI / NL tech, sociocultural. iSchool flex = allowed. https://ericbaumer.com/
3. **Ashton Anderson** — Assoc Prof, UofT CS (UTSC). Over-reliance on LLM advice (CHI'25), LLM sycophancy (CHI'26), ChatBench human-AI eval (ACL'25). CS no flex → co-supervisor only.
- Backups: Ishtiaque Ahmed (Assoc, CS x-appt iSchool, responsible AI); Sheila McIlraith (Prof, CS; agents/instructions; committee). UBC path: MERM (Zumbo/Wu) or HDLC (Shapka) primary + Conati/Yoon (CS) co-supervision, needs program approval.
- Excluded: Kuzminykh, Ferguson (Assistant); Donmez (topic); Chignell (deceased); J.J. Williams (moved).

**Open questions**: Can MIE/iSchool flex students have CS co-supervisor? Fall 2027 recruiting? On-campus expectations for Vancouver-based student? IRCC/work-permit vs full-time registration.

**Contacted (informational)**: Michael Glueck (Autodesk Research; did UofT CS PhD while employed) — message drafted 2026-10-23.
