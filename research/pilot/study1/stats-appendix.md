# Statistical appendix

## Design and analysis units

- Primary repeated unit: task (39 paired tasks × 10 fixed model configurations).
- Episode-level denominator: 390; each task appears once per model.
- Contact proxies: `scenario_coverage` = unique contacted scenario-listed NPCs / number listed; `any_scenario_contact`; `all_scenario_contacts`; `any_outside_scenario`.
- Outcome: normalized checkpoint score = evaluator result / total. Exact completion is descriptive only.
- Missing roster: one no-scenario task excluded, leaving 390/400 episodes.

## H1a descriptive inference

Wilson score intervals (95%) are reported for key binary episode rates in `metrics.json`. They describe uncertainty over episode proportions under a binomial approximation, but episodes are clustered by task and model; hence they are not population-level independent-sample intervals. Treat as descriptive precision, not a design-based generalization.

## H1b matched model comparison

Friedman rank test across 10 model configurations, blocking by task, on per-task roster coverage; statistic χ²(9)=91.4138, p=8.4689e-16. Kendall's W=0.2604 (χ²/[n(k−1)]). Pairwise follow-ups use two-sided asymptotic Wilcoxon signed-rank tests on the 39 matched task differences, with Holm family-wise correction over 45 comparisons. Full estimates, raw p-values, adjusted p-values and adjusted decisions are in `coverage_pairwise_holm.csv`.

## H1c adjusted association

OLS: normalized score ~ scenario coverage + task fixed effects + model fixed effects; task-clustered sandwich standard errors with finite-sample correction. Estimate=0.37892, SE=0.06132, 95% CI [0.25872, 0.49911], p=6.44553e-10, R²=0.6187. Sensitivity excluding tasks whose roster has ≥10 people: estimate=0.37827, SE=0.06198, 95% CI [0.25680, 0.49975], p=1.03899e-09.

No normality test is used to select the regression: inference uses task-clustered robust errors and asymptotic normal p-values/CIs. The small number of clusters (39), unmodeled task-by-model interactions, bounded score, and endogenous coverage remain limitations. These results should be considered exploratory.

## Reproduction

From repository root: `python research/pilot/study1/run_study1.py`. Deterministic parser and analysis; no random seed required. Environment and SHA-256 hashes are in `run_manifest.json`.
