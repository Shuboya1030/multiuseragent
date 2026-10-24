# How Papers Write the Related Work Section: Patterns and Templates

> Compiled 2026-10-23. Source: the Related Work sections of 5 papers in the human–agent collaboration / multi-agent / enterprise agent area, read via the arXiv HTML versions.
> Purpose: a reference for writing the literature review in a proposal or paper.

## 1. The five sample papers

| Paper | Venue | Structure | How each paragraph is built | How it contrasts with prior work |
|---|---|---|---|---|
| **ReHAC** (Feng et al.) — [arXiv 2402.12914](https://arxiv.org/html/2402.12914v1) | Findings of EMNLP 2024 | 2 subsections, broad to narrow: *LLM-based Agent* → *Human-Agent Collaboration* | Survey prior work → "However" pivot → this paper's aim | "still perform poorly on some complex tasks"; "relies on designing high-quality rules or prompts"; "highly dependent on the designer's domain knowledge" → "a generalised and learnable method" |
| **Multi-User LLM Agents** (Yang et al.) — [arXiv 2604.08567](https://arxiv.org/html/2604.08567) | Preprint 2026 | No subsections; one paragraph with about 11 citations | Organized by dimension (interaction benchmarks → feedback/preference learning → proactive clarification → preference aggregation); transitions such as "Along the … dimension" and "Separately" | One contrasting sentence at the very end: "In contrast to these settings, we focus on…"; no direct criticism of prior work |
| **MAST** (Cemri et al.) — [arXiv 2503.13657](https://arxiv.org/html/2503.13657v3) | NeurIPS 2025 D&B | 3 subsections: challenges → design principles → datasets and taxonomies | Broad framing → cited examples → while/however contrast → positioning | Stresses a different perspective: "do not offer a fine-grained, empirically grounded taxonomy"; "primarily facilitate a top-down perspective" vs. "bottom-up analysis"; "extends these insights to the multi-agent context"; closes with "the first…" |
| **Who&When** (Zhang et al.) — [arXiv 2505.00212](https://arxiv.org/html/2505.00212v3) | ICML 2025 | 3 bold run-in headings: LLM MAS → LLM-as-judge → Reward Models | Neutral survey; concessive pivot in the last sentence | "Despite these advancements, failure attribution remains a manual process"; "focus primarily on … individual LLMs, rather than identifying the errors in complex agentic systems" |
| **TheAgentCompany** (Xu et al.) — [arXiv 2412.14161](https://arxiv.org/html/2412.14161) | NeurIPS 2025 D&B | No "Related Work" section; organized by **desiderata**, one paragraph per requirement, plus a large comparison table in the appendix | Requirement ("In order to…" / "If agents are…") → prior benchmarks that do not meet it → how this paper meets it | "In contrast, TheAgentCompany contains…"; "Most other benchmarks do not measure…, except for τ-bench"; "One novel contribution … is"; the table compares 19 benchmarks, and this paper is the only one checked in every column |

## 2. Common patterns

1. **One paragraph per theme, and the last sentence states the gap or position.** All five papers follow this rule.
   - The first half of the paragraph surveys prior work neutrally.
   - The final sentence pivots with However / Despite / In contrast / rather than.
2. **Order from broad to narrow.** The last paragraph is the one closest to the paper. ReHAC, for example, goes agent → human-agent collaboration.
3. **Frame the gap as a different focus, not as prior work being wrong.**
   - Common phrasings: *focus primarily on X rather than Y*, *complementary to*, *extends … to*, *bottom-up vs top-down*.
   - The Multi-User paper barely criticizes prior work. It only says the setting is different.
4. **Make the gap concrete along one dimension.** Common dimensions:
   - degree of automation: manual → automated
   - scope: single → multi (single-agent → multi-agent, single-user → multi-user)
   - perspective: reactive → proactive, top-down → bottom-up
   - method: rule- or prompt-based → learnable / generalizable
   - environment: synthetic → realistic, third-party hosted → self-hosted
5. **When the problem spans several dimensions, use a comparison table.** TheAgentCompany is the example: rows are prior work, columns are dimensions, and only this paper has every column checked. Readers can see the gap at a glance.
6. **Citations are unevenly distributed.**
   - Background paragraphs cite a lot. ReHAC's first subsection has about 30 citations.
   - The paragraph closest to the paper cites only a few, carefully chosen works.
7. **The review mirrors the Introduction.** Each challenge named in the Introduction gets a corresponding paragraph. ReHAC criticizes rule- and prompt-based methods in its Introduction, and its Related Work has a dedicated paragraph on exactly those methods.
8. **Placement and naming vary.**
   - The section can be called Related Work or Background.
   - It can sit in Section 2, before the method (MAST, TheAgentCompany), or near the end, before the Conclusion (ReHAC, Who&When, Multi-User).
   - A proposal usually places it right after the Introduction, as "Background and Research Gap."

## 3. Sentence templates

**Opening a paragraph**
- "Recent work has examined how … (Author, Year)."
- "LLMs have demonstrated … in X (refs), Y (refs), and Z (refs)."
- "Numerous studies have explored …"
- "Traditional research on X focused on …"
- "In order to make valid statements about …, a benchmark must …" (desiderata style)

**Moving between threads**
- "Along the X dimension, …"
- "Beyond X, another line of work studies …"
- "Separately, …"
- "Building on this, …"

**Pivoting to the gap (end of paragraph)**
- "However, these approaches assume …"
- "Despite these advancements, X remains …"
- "These works focus primarily on X, rather than Y."
- "Most existing X do not …, except for …"
- "While X addresses …, it does not consider …"

**Positioning this paper**
- "In contrast to these settings, we focus on …"
- "Our work is complementary: …"
- "Our work extends these insights to …"
- "To our knowledge, this is the first … that …"

## 4. Checklist for writing a Related Work section
- [ ] Is the order broad to narrow, with the last paragraph closest to my problem?
- [ ] Does every paragraph end with a sentence stating the gap or my position?
- [ ] Is each gap concrete along one dimension (scope, perspective, automation, method, environment)?
- [ ] Have I avoided wording that disparages prior work, framing gaps as differences in focus or setting?
- [ ] Does each challenge raised in the Introduction have a matching paragraph?
- [ ] If the problem spans several dimensions, have I included a comparison table?
- [ ] For a "first …" claim, is there a hedge (*to our knowledge*), and is it backed by a search?
- [ ] Are citation formats consistent, and is the publication status (preprint vs. published) correct?

## 5. Application to this project (role-aware help-seeking)

**Suggested paragraph order**, broad to narrow:
1. LLM agents and enterprise workflows (TheAgentCompany, τ-bench, CRMArena). Gap: autonomous agents are still unreliable.
2. Human–agent collaboration: deciding *when* to involve a human (ReHAC, Learning to Ask, Co-Gym, HAS-Bench). Gap: they assume a single, interchangeable human.
3. Rule- or prompt-based escalation. Gap: depends on context and does not generalize. (Corresponds to the challenge raised in the Introduction.)
4. Multi-user / multi-principal agents (Multi-User LLM Agents, Harness-MU, Collaborative Memory). Gap: reactive, not proactive.
5. Multi-expert learning-to-defer and adaptive elicitation (DeCCaF, Top-k L2D, Whom to Query). Gap: single-step classification or opinion estimation; no organizational roles.
6. Human–agent teaming in human factors (Chung et al., 2024). Gap: most studies examine one human and one agent.

**Suggested comparison table** (only this paper has every column checked):

| Work | Multiple humans | Decides when | Decides whom | Roles/authority | Multi-step tasks |
|---|---|---|---|---|---|
| ReHAC | ✗ | ✓ | ✗ | ✗ | ✓ |
| Learning to Ask | ✗ | ✓ | ✗ | ✗ | ✓ |
| Multi-User LLM Agents | ✓ | ✗ | ✗ | ✓ | ✓ |
| Multi-expert L2D | ✓ (experts) | ✓ | ✓ | ✗ | ✗ |
| Whom to Query for What | ✓ | ✗ | ✓ | ✗ (attributes only) | ✓ |
| TheAgentCompany | ✓ | — (benchmark) | — | partial | ✓ |
| **This work** | ✓ | ✓ | ✓ | ✓ | ✓ |

> The ✓/✗ entries in this table are my judgments based on the abstracts. Check each against the original papers before using the table.
