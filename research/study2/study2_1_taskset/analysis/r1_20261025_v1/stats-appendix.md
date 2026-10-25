# Statistical appendix

Unit: parent template, paired across three configurations. Twenty templates per class; one run per model/template. Do not use 180 episodes as 180 independent templates. Intervals describe resampling of this authored template set; external task-population representativeness is not established.

Binary proportions: Wilson 95% intervals. No Gaussian assumption or normality test is appropriate for these binary counts. Paired comparisons: exact two-sided McNemar test, 10000 paired-template percentile-bootstrap draws, seed 2026102502. Holm correction across the nine planned contrasts. CIs are unadjusted; p values are multiplicity-adjusted. Complete pairs only for process metrics; missingness bounds in group_summary.json. This can still be subject to nonrandom completion selection.

**Degenerate intervals:** when all observed paired differences are zero, the empirical bootstrap gives [0,0]. This is a resampling degeneracy, not proof of equal population rates or no uncertainty; do not make an equivalence claim.

**Posthoc definitions:** optional ineffective contact is any contact without final proxy bonus, any irrelevant-recipient contact, or more than one contact; failed episode values are unknown for primary process tests. This implements the frozen conceptual definition, but code was finalized after collection. The stricter calibrated_path_proxy is explicitly posthoc and descriptive. No output was rescored.

| Class | Metric | A − B | Paired n | Difference | 95% bootstrap CI | Exact p | Holm p |
|---|---|---|---:|---:|---|---:|---:|
| must_ask | underhelp | OpenAI − Moonshot | 19 | 0.5789 | 0.3684, 0.7895 | 0.000977 | 0.008789 |
| must_ask | underhelp | OpenAI − Anthropic | 17 | 0.5882 | 0.3529, 0.8235 | 0.001953 | 0.015625 |
| must_ask | underhelp | Moonshot − Anthropic | 18 | 0.0000 | 0.0000, 0.0000 | 1.000000 | 1.000000 |
| no_help | overhelp | OpenAI − Moonshot | 20 | -0.0500 | -0.1500, 0.0000 | 1.000000 | 1.000000 |
| no_help | overhelp | OpenAI − Anthropic | 20 | -0.0500 | -0.1500, 0.0000 | 1.000000 | 1.000000 |
| no_help | overhelp | Moonshot − Anthropic | 20 | 0.0000 | 0.0000, 0.0000 | 1.000000 | 1.000000 |
| optional_benefit | optional_ineffective | OpenAI − Moonshot | 15 | -0.4667 | -0.7333, -0.2000 | 0.015625 | 0.109375 |
| optional_benefit | optional_ineffective | OpenAI − Anthropic | 18 | -0.2222 | -0.4444, -0.0556 | 0.125000 | 0.750000 |
| optional_benefit | optional_ineffective | Moonshot − Anthropic | 13 | 0.1538 | -0.2308, 0.5385 | 0.726562 | 1.000000 |

## Exact descriptive groups

| Model | Class | N | Submitted | Strict success | Any contact | Contacts mean ± SD | Tokens mean ± SD | Estimated USD total |
|---|---|---:|---:|---:|---:|---|---|---:|
| OpenAI | must_ask | 20 | 19 | 8 | 20 | 1.90 ± 0.97 | 5121.6 ± 2315.4 | 0.079177 |
| Moonshot | must_ask | 20 | 20 | 17 | 20 | 2.15 ± 0.37 | 6317.2 ± 1072.2 | 0.127882 |
| Anthropic | must_ask | 20 | 18 | 17 | 20 | 2.40 ± 0.68 | 13140.0 ± 3146.8 | 0.033639 |
| OpenAI | optional_benefit | 20 | 20 | 20 | 1 | 0.05 ± 0.22 | 1120.5 ± 474.8 | 0.034170 |
| Moonshot | optional_benefit | 20 | 15 | 15 | 18 | 1.50 ± 1.15 | 5507.4 ± 2749.2 | 0.180893 |
| Anthropic | optional_benefit | 20 | 18 | 17 | 8 | 0.60 ± 0.88 | 5205.9 ± 4005.1 | 0.020017 |
| OpenAI | no_help | 20 | 20 | 15 | 0 | 0.00 ± 0.00 | 814.4 ± 35.6 | 0.014916 |
| Moonshot | no_help | 20 | 20 | 16 | 1 | 0.10 ± 0.45 | 1293.5 ± 946.7 | 0.041872 |
| Anthropic | no_help | 20 | 20 | 16 | 1 | 0.10 ± 0.45 | 2224.6 ± 1988.6 | 0.006757 |

Primary uncertainty target half-width 0.10 is not uniformly met; no extra runs are triggered. Optional contact/no-contact comparisons are descriptive and confounded; no pooled causal test is conducted. Original strict success includes 10 non-submissions as failures. Process missingness is never filled with zero in paired tests. R0, independent semantic judging, and repeated-run variance are unavailable. No inferred human-workplace generalization.
