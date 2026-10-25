# Figure statistics appendix

## Data and unit

- Confirmatory data only: task version 0.4, profile version 0.4, previously used 14 workflow templates, repetition 0.
- 168 episodes total: 56 per profile condition; each workflow template includes aligned/separated variants, both fixed model configurations, and all three profile conditions.
- Independent resampling unit: the 14 workflow templates. The episode rows are paired/repeated within template and were not treated as independent clusters.
- Outcomes are recomputed from the event trace. The token measure is `input_tokens + output_tokens` summed over all model calls in one episode.

## Descriptive results

| Condition | Strict first information step | Valid path | Total tokens/episode | Tokens per successful task | Successes |
|---|---:|---:|---:|---:|---:|
| R0 names only | 26.8% | 91.1% | 98,342 | 107,983 | 51/56 |
| R1 natural-language profiles | 100.0% | 100.0% | 49,175 | 49,175 | 56/56 |
| R2 structured profiles | 98.2% | 100.0% | 48,852 | 48,852 | 56/56 |

Mean human-contact actions per episode were 5.25 (R0), 2.05 (R1), and 2.02 (R2). This is a descriptive mechanism check: the experiment did not independently randomize whether a contact was correct, so it cannot isolate the causal effect of “asking the right person” from the effect of providing role information.

“Tokens per successful task” is total token volume across all episodes in a condition divided by the number of successful episodes. It charges unsuccessful runs to the condition that incurred them. For R0, mean tokens among successful episodes alone are 92,305; this conditional mean excludes its five failed episodes.

## Paired token contrasts

The estimand is each template's mean token difference (averaged over its aligned/separated task variants and the two fixed model configurations), followed by an equal-weight average over templates.

| Contrast | Difference, tokens/episode | 95% template-cluster bootstrap CI | Relative to lower-information condition |
|---|---:|---:|---:|
| R1−R0 | −49,166 | [−61,895, −37,018] | −50.0% |
| R2−R1 | −323 | [−2,435, +1,276] | −0.7%; interval includes zero |

Intervals are percentile intervals from 20,000 cluster-bootstrap draws. For R1−R0 the interval supports a reduction in token volume in this experiment. For R2−R1 it does not establish a difference. Token volume is not a billed-dollar measure, and this analysis does not separate prompt/context overhead from model-generated tokens.

## Figure 3 model-stratified token contrasts

The source file `study2_v04_contrasts.csv` contains model-specific estimates. These are descriptive comparisons of the two named configurations. The forest plot uses the same 14-template bootstrap unit and 20,000 draws. No model-family inference is made.

## Multiplicity and inference

The figures are descriptive. Primary hypothesis tests remain those in `../study2_v04_analysis.md`: template-level Monte Carlo sign-flip tests with Holm correction over six fixed-model-average primary contrasts. The token endpoint is a prespecified secondary resource measure in this figure package, and its intervals are reported without converting them to a confirmatory universal claim.

## Limitations

- One analyzed episode per task × model × condition cell; repeated stochastic variation is not estimated separately from task-template variation.
- Four candidates, fixed simulated query cost, deterministic NPC response rules, and synthetic scenarios.
- Codex CLI's recorded token counters are comparable within this run setup, but are not a direct price estimate.
- The 14 template clusters give limited precision for generalization to other workflows.
