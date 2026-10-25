"""Analyze the locked Study 2 confirmatory set using one first record per planned cell."""
import csv
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent
RUNS = ROOT / "runs.jsonl"
DER = ROOT / "derived"
METRICS = ["valid_path", "task_score_T", "reward_R", "total_cost", "N_auth", "N_waste", "first_valid"]


def avg(values):
    return sum(values) / len(values) if values else float("nan")


def template_id(task_id):
    return task_id.removeprefix("S2_").removesuffix("_aligned").removesuffix("_separated")


def bootstrap_ci(values, seed, draws=20000):
    if not values:
        return float("nan"), float("nan")
    rng = random.Random(seed)
    means = sorted(avg([rng.choice(values) for _ in values]) for _ in range(draws))
    return means[int(.025 * draws)], means[min(draws - 1, int(.975 * draws))]


def sign_flip_p(values):
    values = [x for x in values if x != 0]
    if not values:
        return 1.0
    observed = abs(avg(values))
    count = 0
    for mask in range(1 << len(values)):
        permuted = [x if mask & (1 << i) else -x for i, x in enumerate(values)]
        count += abs(avg(permuted)) >= observed - 1e-12
    return count / (1 << len(values))


def write_csv(path, rows):
    if not rows:
        return
    with path.open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)


def main():
    all_rows = [json.loads(line) for line in RUNS.read_text(encoding="utf-8").splitlines() if line.strip()]
    raw = [row for row in all_rows if row.get("split") == "confirmatory"]
    key_fields = ("task_id", "model_id", "profile_condition", "rep")
    seen = set()
    rows = []
    for row in raw:
        key = tuple(row.get(field) for field in key_fields)
        if key not in seen:
            seen.add(key)
            rows.append(row)

    counts = Counter(tuple(row.get(field) for field in key_fields) for row in raw)
    duplicate_keys = {key: count for key, count in counts.items() if count > 1}
    if len(rows) != 168:
        raise SystemExit(f"Expected 168 unique planned confirmatory cells, found {len(rows)}")
    DER.mkdir(exist_ok=True)
    kept_ids = {row["run_id"] for row in rows}
    events_path = ROOT / "events.jsonl"
    events = [json.loads(line) for line in events_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    confirmatory_events = [event for event in events if event.get("run_id") in kept_ids]
    (DER / "confirmatory_unique_runs.jsonl").write_text(
        "".join(json.dumps(row, ensure_ascii=False) + "\n" for row in rows), encoding="utf-8")
    (DER / "confirmatory_unique_events.jsonl").write_text(
        "".join(json.dumps(event, ensure_ascii=False) + "\n" for event in confirmatory_events), encoding="utf-8")

    cell_groups = defaultdict(list)
    for row in rows:
        cell_groups[(row["model_id"], row["alignment"], row["profile_condition"])].append(row)
    cells = []
    for (model, alignment, condition), group in sorted(cell_groups.items()):
        cells.append({"model": model, "alignment": alignment, "condition": condition,
                      "n_planned_cells": len(group), **{metric: avg([float(r[metric]) for r in group]) for metric in METRICS}})
    write_csv(DER / "confirmatory_cell_summary.csv", cells)

    task_groups = defaultdict(list)
    for row in rows:
        task_groups[(row["model_id"], row["task_id"], row["profile_condition"])].append(row)
    task_means = {(model, task, condition): {metric: avg([float(r[metric]) for r in group]) for metric in METRICS}
                  for (model, task, condition), group in task_groups.items()}

    contrasts = []
    contrast_pairs = [("R1-R0", "R1", "R0"), ("R2-R1", "R2", "R1")]
    models = sorted({r["model_id"] for r in rows})
    for model in models + ["fixed_model_average"]:
        for metric in METRICS:
            for label, high, low in contrast_pairs:
                by_template = defaultdict(list)
                for (m, task, condition), value in task_means.items():
                    if condition != high or (m, task, low) not in task_means:
                        continue
                    if model != "fixed_model_average" and m != model:
                        continue
                    by_template[template_id(task)].append(value[metric] - task_means[(m, task, low)][metric])
                ds = [avg(v) for v in by_template.values()]
                lo, hi = bootstrap_ci(ds, 20261024 + len(contrasts))
                contrasts.append({"model": model, "outcome": metric, "contrast": label,
                                  "n_task_templates": len(ds), "mean_difference": avg(ds),
                                  "cluster_boot_95_low": lo, "cluster_boot_95_high": hi,
                                  "exact_sign_flip_p_descriptive": sign_flip_p(ds)})

            # Difference-in-differences: separated minus aligned, paired within template.
            by_template = defaultdict(dict)
            for (m, task, condition), value in task_means.items():
                if condition not in ("R0", "R1", "R2"):
                    continue
                alignment = "aligned" if task.endswith("_aligned") else "separated"
                for label, high, low in contrast_pairs:
                    if condition != high or (m, task, low) not in task_means:
                        continue
                    if model != "fixed_model_average" and m != model:
                        continue
                    by_template[(label, template_id(task))].setdefault(alignment, []).append(
                        value[metric] - task_means[(m, task, low)][metric])
            for (label, tid), alignments in by_template.items():
                if {"aligned", "separated"} <= set(alignments):
                    alignments["did"] = [avg(alignments["separated"]) - avg(alignments["aligned"])]
            for label, _, _ in contrast_pairs:
                ds = [v["did"][0] for (lab, _), v in by_template.items() if lab == label and "did" in v]
                lo, hi = bootstrap_ci(ds, 20261024 + len(contrasts))
                contrasts.append({"model": model, "outcome": metric, "contrast": label + " DID separated-aligned",
                                  "n_task_templates": len(ds), "mean_difference": avg(ds),
                                  "cluster_boot_95_low": lo, "cluster_boot_95_high": hi,
                                  "exact_sign_flip_p_descriptive": sign_flip_p(ds)})
    write_csv(DER / "confirmatory_paired_contrasts.csv", contrasts)

    report = [
        "# Study 2 confirmatory data integrity",
        "",
        "- Planned cells: 28 task variants × 2 models × 3 profile conditions × 1 repetition = 168.",
        f"- Raw confirmatory rows: {len(raw)}.",
        f"- Unique planned cells retained for primary analysis: {len(rows)} (first appended record per cell).",
        f"- Repeated-cell rows beyond the first: {len(raw) - len(rows)} across {len(duplicate_keys)} cells.",
        "- All raw repeated rows and events remain in the source JSONL files. They are not counted as independent planned observations.",
        "- The confirmatory analysis files use the first appended row per planned cell; the fixed pilot data are excluded.",
        "- Some repeated records have very short timestamp gaps, consistent with overlapping invocations; the runner did not record invocation IDs, so the exact source of the duplicate writes cannot be established from the logs.",
        "- Deduplicated run and event files are saved alongside the summaries for direct audit.",
        "- Uncertainty is summarized over 14 workflow-template clusters. Exact sign-flip p-values are descriptive given the small number of clusters and multiple outcomes.",
        "",
        "Repeated cells by model:",
    ]
    model_dupes = Counter(key[1] for key in duplicate_keys)
    report.extend(f"- {model}: {sum(c - 1 for key, c in duplicate_keys.items() if key[1] == model)} extra rows across {model_dupes[model]} cells"
                  for model in sorted(model_dupes))
    (DER / "confirmatory_data_integrity.md").write_text("\n".join(report) + "\n", encoding="utf-8")
    print(f"Analyzed {len(rows)} unique planned cells from {len(raw)} raw confirmatory rows; {len(raw)-len(rows)} extra rows are documented.")
    print(f"Wrote confirmatory summaries to {DER}")


if __name__ == "__main__":
    main()
