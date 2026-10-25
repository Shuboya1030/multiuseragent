# Study 2 v0.4 corrected-profile replication analysis

- Episodes: 168; planned cells: 168; task variants: 28; workflow-template clusters: 14.
- Task blueprint inventory (including excluded extension): {'previously_seen_template': 28, 'new_extension_template': 24}.
- Models: gpt-5.6-terra, gpt-6-luna; conditions: R0/R1/R2; one analyzed episode per planned cell.
- Candidate display-order mismatches within paired cells: 0.
- Run statuses: {'completed': 163, 'max_turns': 5}.
- Inference unit: workflow-template cluster. Bootstrap intervals resample templates; sign-flip p-values use Monte Carlo sign randomization. Primary family uses Holm adjustment.
- Historical runs and the interrupted v0.4 three-repetition batch are analyzed separately/excluded from this 168-cell replication. Fixed R weights are unchanged and no weight sensitivity scan was run.
- Strict first-step validity requires the first action to request information from an admissible knowledge holder; the legacy `first_valid` field is not used.

## Primary contrasts (fixed-model average)

- Strict first information step, R1-R0: +0.732 (95% CI +0.518 to +0.929; 14 templates; Monte Carlo sign-flip p=0.0006; Holm-adjusted p=0.0035).
- Strict first information step, R2-R1: -0.018 (95% CI -0.054 to +0.000; 14 templates; Monte Carlo sign-flip p=1.0000; Holm-adjusted p=1.0000).
- Valid path completion, R1-R0: +0.089 (95% CI +0.000 to +0.214; 14 templates; Monte Carlo sign-flip p=0.2498; Holm-adjusted p=1.0000).
- Valid path completion, R2-R1: +0.000 (95% CI +0.000 to +0.000; 14 templates; Monte Carlo sign-flip p=1.0000; Holm-adjusted p=1.0000).
- Task score T, R1-R0: +0.089 (95% CI +0.000 to +0.214; 14 templates; Monte Carlo sign-flip p=0.2511; Holm-adjusted p=1.0000).
- Task score T, R2-R1: +0.000 (95% CI +0.000 to +0.000; 14 templates; Monte Carlo sign-flip p=1.0000; Holm-adjusted p=1.0000).
- Fixed composite R, R1-R0: +0.528 (95% CI +0.374 to +0.717; 14 templates; Monte Carlo sign-flip p=0.0002).
- Fixed composite R, R2-R1: +0.005 (95% CI -0.003 to +0.017; 14 templates; Monte Carlo sign-flip p=0.7495).
- Query cost, R1-R0: -3.196 (95% CI -4.071 to -2.393; 14 templates; Monte Carlo sign-flip p=0.0001).
- Query cost, R2-R1: -0.036 (95% CI -0.161 to +0.054; 14 templates; Monte Carlo sign-flip p=1.0000).
- Knowledge misses, R1-R0: -1.518 (95% CI -2.089 to -0.982; 14 templates; Monte Carlo sign-flip p=0.0004).
- Knowledge misses, R2-R1: +0.018 (95% CI +0.000 to +0.054; 14 templates; Monte Carlo sign-flip p=1.0000).
- Unauthorized approval attempts, R1-R0: -1.411 (95% CI -1.589 to -1.232; 14 templates; Monte Carlo sign-flip p=0.0002).
- Unauthorized approval attempts, R2-R1: +0.000 (95% CI +0.000 to +0.000; 14 templates; Monte Carlo sign-flip p=1.0000).

## Token use (input plus output tokens)

Token counts are summed over every model call in an episode. They are a usage measure, not billed-dollar cost; this Codex CLI run does not provide a comparable monetary price.

- R0: mean 98,342 tokens/episode; 51/56 valid-path successes; 107,983 aggregate tokens per successful task.
- R1: mean 49,175 tokens/episode; 56/56 valid-path successes; 49,175 aggregate tokens per successful task.
- R2: mean 48,852 tokens/episode; 56/56 valid-path successes; 48,852 aggregate tokens per successful task.
- R1-R0: -49,166 tokens/episode (95% CI -61,895 to -37,018; template-cluster bootstrap).
- R2-R1: -323 tokens/episode (95% CI -2,435 to 1,276; template-cluster bootstrap).

## Model-stratified estimates

These describe two fixed model configurations, not a comparison of model families.

- gpt-5.6-terra, Strict first information step, R1-R0: +0.714 (95% CI +0.500 to +0.929).
- gpt-5.6-terra, Strict first information step, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-6-luna, Strict first information step, R1-R0: +0.750 (95% CI +0.536 to +0.929).
- gpt-6-luna, Strict first information step, R2-R1: -0.036 (95% CI -0.107 to +0.000).
- gpt-5.6-terra, Valid path completion, R1-R0: +0.071 (95% CI +0.000 to +0.214).
- gpt-5.6-terra, Valid path completion, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-6-luna, Valid path completion, R1-R0: +0.107 (95% CI +0.000 to +0.214).
- gpt-6-luna, Valid path completion, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-5.6-terra, Task score T, R1-R0: +0.071 (95% CI +0.000 to +0.214).
- gpt-5.6-terra, Task score T, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-6-luna, Task score T, R1-R0: +0.107 (95% CI +0.000 to +0.214).
- gpt-6-luna, Task score T, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-5.6-terra, Fixed composite R, R1-R0: +0.439 (95% CI +0.281 to +0.656).
- gpt-5.6-terra, Fixed composite R, R2-R1: +0.007 (95% CI +0.000 to +0.020).
- gpt-6-luna, Fixed composite R, R1-R0: +0.617 (95% CI +0.422 to +0.834).
- gpt-6-luna, Fixed composite R, R2-R1: +0.004 (95% CI -0.006 to +0.015).
- gpt-5.6-terra, Query cost, R1-R0: -2.857 (95% CI -3.929 to -1.929).
- gpt-5.6-terra, Query cost, R2-R1: -0.071 (95% CI -0.214 to +0.000).
- gpt-6-luna, Query cost, R1-R0: -3.536 (95% CI -4.429 to -2.679).
- gpt-6-luna, Query cost, R2-R1: +0.000 (95% CI -0.107 to +0.107).
- gpt-5.6-terra, Knowledge misses, R1-R0: -1.500 (95% CI -2.143 to -0.893).
- gpt-5.6-terra, Knowledge misses, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-6-luna, Knowledge misses, R1-R0: -1.536 (95% CI -2.107 to -1.036).
- gpt-6-luna, Knowledge misses, R2-R1: +0.036 (95% CI +0.000 to +0.107).
- gpt-5.6-terra, Unauthorized approval attempts, R1-R0: -1.107 (95% CI -1.429 to -0.821).
- gpt-5.6-terra, Unauthorized approval attempts, R2-R1: +0.000 (95% CI +0.000 to +0.000).
- gpt-6-luna, Unauthorized approval attempts, R1-R0: -1.714 (95% CI -2.107 to -1.357).
- gpt-6-luna, Unauthorized approval attempts, R2-R1: +0.000 (95% CI +0.000 to +0.000).

## Alignment interactions

- Strict first information step, R1-R0, separated-minus-aligned difference-in-differences: -0.036 (95% CI -0.143 to +0.071).
- Strict first information step, R2-R1, separated-minus-aligned difference-in-differences: +0.036 (95% CI +0.000 to +0.107).
- Valid path completion, R1-R0, separated-minus-aligned difference-in-differences: -0.036 (95% CI -0.143 to +0.071).
- Valid path completion, R2-R1, separated-minus-aligned difference-in-differences: +0.000 (95% CI +0.000 to +0.000).
- Task score T, R1-R0, separated-minus-aligned difference-in-differences: -0.036 (95% CI -0.143 to +0.071).
- Task score T, R2-R1, separated-minus-aligned difference-in-differences: +0.000 (95% CI +0.000 to +0.000).
- Fixed composite R, R1-R0, separated-minus-aligned difference-in-differences: -0.022 (95% CI -0.276 to +0.240).
- Fixed composite R, R2-R1, separated-minus-aligned difference-in-differences: -0.010 (95% CI -0.035 to +0.005).

## Interpretation guardrails

- R1 and R2 contain the same audited role facts, but their profile strings are not length-matched (see `study2_v04_profile_lengths.csv`). Interpret R2−R1 as the effect of the structured-profile package, including formatting and its length/serialization, rather than a pure typography effect.
- Model-specific rows are fixed-configuration comparisons; they are not evidence that one model family is generally better.
- The 14 workflow-template clusters remain the basis for uncertainty.
- The 12 new extension templates are audited but excluded from this 168-cell confirmatory replication.
- Simulation realism and lack of human-response variability limit external validity; automated checks are not a substitute for human double-review of task realism.

## Publication-style figures

The first-pass root SVGs have been replaced with publication-oriented vector versions; the full package includes double-column PDFs, SVG previews, source code, captions, and interpretation notes in [`figures/`](figures/).

- Figure 1: [profile-condition outcomes (PDF)](figures/figure_01_profile_effects.pdf) · [SVG](figures/figure_01_profile_effects.svg)
- Figure 2: [help-seeking error mechanisms (PDF)](figures/figure_02_help_seeking_errors.pdf) · [SVG](figures/figure_02_help_seeking_errors.svg)
- Figure 3: [model-stratified token contrasts (PDF)](figures/figure_03_token_contrasts.pdf) · [SVG](figures/figure_03_token_contrasts.svg)
- Full captions and limitations: [`figure-catalog.md`](figures/figure-catalog.md)
- Statistical details: [`stats-appendix.md`](figures/stats-appendix.md)
