# Study 2 confirmatory data integrity

- Planned cells: 28 task variants × 2 models × 3 profile conditions × 1 repetition = 168.
- Raw confirmatory rows: 212.
- Unique planned cells retained for primary analysis: 168 (first appended record per cell).
- Repeated-cell rows beyond the first: 44 across 44 cells.
- All raw repeated rows and events remain in the source JSONL files. They are not counted as independent planned observations.
- The confirmatory analysis files use the first appended row per planned cell; the fixed pilot data are excluded.
- Some repeated records have very short timestamp gaps, consistent with overlapping invocations; the runner did not record invocation IDs, so the exact source of the duplicate writes cannot be established from the logs.
- Deduplicated run and event files are saved alongside the summaries for direct audit.
- Uncertainty is summarized over 14 workflow-template clusters. Exact sign-flip p-values are descriptive given the small number of clusters and multiple outcomes.

Repeated cells by model:
- gpt-5.6-terra: 23 extra rows across 23 cells
- gpt-6-luna: 21 extra rows across 21 cells
