# Study 2 figure catalog

All figures are generated from the trace-recomputed v0.4 confirmatory set (168 episodes; 14 independent workflow-template clusters; two fixed model configurations). The source script is `make_figures.py`. Each figure is exported as vector PDF for manuscript use and SVG for web preview/editing. Color encodes profile condition using an Okabe–Ito palette; marker shape redundantly encodes the same condition for grayscale/accessibility.

## Figure 1 — Profile condition outcomes

- **Files:** `figure_01_profile_effects.pdf` / `.svg`
- **Purpose:** Show how profile information relates to first-contact validity, complete valid-path success, and total model-token use.
- **Panels:** (A) strict first information request to the admissible knowledge holder (%); (B) valid-path completion (%); (C) input plus output tokens per episode (thousands). Conditions are names only (R0), natural-language profile (R1), and structured profile (R2).
- **Caption:** Points are condition means over 56 episodes (28 task variants × two fixed model configurations). Whiskers are 95% percentile bootstrap intervals obtained by resampling 14 workflow-template clusters. A zero-width interval coincides with its point (R1's first-contact validity is 100% in every template). R1/R2 profile facts are semantically matched; their text length is not matched.
- **Observation:** R1 and R2 substantially exceed R0 on first-contact validity and use roughly half the tokens. Valid-path completion has a smaller difference because R0 already succeeds in most episodes.
- **Interpretation:** Role information appears to improve routing efficiency in this simulator; the figure alone does not establish improvement in deployed organizations.
- **Caveat:** The CIs are template-cluster intervals; condition-level R1/R2 success intervals are degenerate at 100% because every observed episode succeeded.

## Figure 2 — Help-seeking error mechanisms

- **Files:** `figure_02_help_seeking_errors.pdf` / `.svg`
- **Purpose:** Identify which help-seeking failures change with role information.
- **Panels:** Mean knowledge misses, unauthorized approval attempts, repeated requests, and unhelpful requests per episode, by profile condition.
- **Caption:** Points are condition means; whiskers are 95% percentile bootstrap intervals from 14 workflow-template clusters. Means average the two fixed model configurations and both knowledge-authority alignments.
- **Observation:** Knowledge and authority errors concentrate in R0; they are near zero under R1/R2.
- **Interpretation:** This pattern is consistent with the role profiles helping the agent distinguish who may know a fact from who may authorize an action.
- **Caveat:** Simulator labels encode a single gold knowledge holder and authorizer. The figure does not show whether real organizational roles are equally legible.

## Figure 3 — Token contrasts by fixed model configuration

- **Files:** `figure_03_token_contrasts.pdf` / `.svg`
- **Purpose:** Test whether token reductions are visible in both tested model configurations and isolate the incremental R2/R1 contrast.
- **Panels:** Paired mean differences in total tokens per episode for R1−R0 and R2−R1. Negative values favor the higher-information condition. Rows show each fixed model configuration and the fixed-model average.
- **Caption:** Dots are mean within-template differences; horizontal whiskers are 95% percentile bootstrap intervals from 14 workflow-template clusters. These are token counts recorded by Codex CLI, not monetary charges.
- **Observation:** R1−R0 is strongly negative for both tested configurations; R2−R1 lies near zero and its interval crosses zero.
- **Interpretation:** The token evidence supports a reduction from providing role information, but does not show an additional token advantage from structuring the same information.
- **Caveat:** Only two fixed model configurations were run. Do not interpret the rows as a representative sample of model families.

## Figure inclusion examples

```latex
\begin{figure}[t]
  \centering
  \includegraphics[width=\textwidth]{figures/figure_01_profile_effects.pdf}
  \caption{Profile-condition outcomes. Points show means over 56 episodes per condition; whiskers show 95\% workflow-template-cluster bootstrap intervals (14 templates). Panel A is strict first-contact validity, panel B is valid-path completion, and panel C is total input-plus-output tokens per episode.}
  \label{fig:profile-effects}
\end{figure}
```
