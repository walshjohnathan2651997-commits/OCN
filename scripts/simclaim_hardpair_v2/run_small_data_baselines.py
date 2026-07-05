import csv
import importlib.util
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASELINE_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_small_data_baselines.py"
SPLIT_ROOT = ROOT / "data" / "simclaim_hardpair_v2" / "splits_group_stratified"
EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v2_small_baselines"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"

METRICS_CSV = METRIC_DIR / "hardpair_v2_small_data_baseline_metrics.csv"
PER_CLASS_CSV = METRIC_DIR / "hardpair_v2_small_data_baseline_per_class_f1.csv"
PRED_CSV = PRED_DIR / "hardpair_v2_small_data_baseline_predictions.csv"
SUMMARY_JSON = REPORT_DIR / "hardpair_v2_small_data_baseline_summary.json"
REPORT_MD = REPORT_DIR / "hardpair_v2_small_data_baseline_report.md"

TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "candidate_label_guess",
]
TEXT_VIEWS = ["claim_only", "evidence_only", "claim_evidence"]


def load_lib():
    spec = importlib.util.spec_from_file_location("baseline_lib", BASELINE_LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def ensure_dirs():
    for p in [METRIC_DIR, PRED_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def run():
    ensure_dirs()
    lib = load_lib()
    train_rows = read_csv(SPLIT_ROOT / "train.csv")
    dev_rows = read_csv(SPLIT_ROOT / "dev.csv")
    test_rows = read_csv(SPLIT_ROOT / "test.csv")
    eval_sets = {"dev": dev_rows, "test": test_rows}

    metric_rows = []
    per_class_rows = []
    pred_rows = []

    for target in TARGETS:
        for split, eval_rows in eval_sets.items():
            for model in ["majority", "claim_length_median_rule", "prefix_first4_memorize"]:
                if model == "majority":
                    y_pred = lib.majority_predict(train_rows, eval_rows, target)
                elif model == "claim_length_median_rule":
                    y_pred = lib.length_threshold_predict(train_rows, eval_rows, target)
                else:
                    y_pred = lib.prefix_memorize_predict(train_rows, eval_rows, target, n=4)
                row, pcs, preds = lib.score_run(
                    "simclaim_hardpair_v2_268_group_stratified",
                    target,
                    split,
                    model,
                    "claim_only",
                    train_rows,
                    eval_rows,
                    y_pred,
                )
                metric_rows.append(row)
                per_class_rows.extend(pcs)
                pred_rows.extend(preds)

            for view in TEXT_VIEWS:
                for model in ["tfidf_centroid", "multinomial_nb"]:
                    if model == "tfidf_centroid":
                        y_pred = lib.tfidf_centroid_predict(train_rows, eval_rows, target, view)
                    else:
                        y_pred = lib.multinomial_nb_predict(train_rows, eval_rows, target, view)
                    row, pcs, preds = lib.score_run(
                        "simclaim_hardpair_v2_268_group_stratified",
                        target,
                        split,
                        model,
                        view,
                        train_rows,
                        eval_rows,
                        y_pred,
                    )
                    metric_rows.append(row)
                    per_class_rows.extend(pcs)
                    pred_rows.extend(preds)

    write_csv(METRICS_CSV, metric_rows)
    write_csv(PER_CLASS_CSV, per_class_rows)
    write_csv(PRED_CSV, pred_rows)
    write_report(metric_rows)


def write_report(metric_rows):
    best = {}
    for row in metric_rows:
        if row["split"] != "test":
            continue
        key = row["target"]
        if key not in best or float(row["macro_f1"]) > float(best[key]["macro_f1"]):
            best[key] = row
    prefix = [r for r in metric_rows if r["split"] == "test" and r["model"] == "prefix_first4_memorize"]
    claim_only = [
        max([r for r in metric_rows if r["split"] == "test" and r["target"] == target and r["text_view"] == "claim_only"], key=lambda r: float(r["macro_f1"]))
        for target in TARGETS
    ]
    summary = {
        "dataset": "simclaim_hardpair_v2_268_group_stratified",
        "best_test_by_target": best,
        "test_prefix_first4": prefix,
        "test_claim_only_best": claim_only,
        "metrics_csv": str(METRICS_CSV),
        "report_md": str(REPORT_MD),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Small-data baseline report: hardpair v2 268")
    lines.append("")
    lines.append("Split: `data/simclaim_hardpair_v2/splits_group_stratified`.")
    lines.append("")
    lines.append("## Best test result by target")
    lines.append("")
    lines.append("| target | best model | view | acc | macro-F1 | positive F1 |")
    lines.append("|---|---|---|---:|---:|---:|")
    for target, row in best.items():
        lines.append(f"| {target} | {row['model']} | {row['text_view']} | {row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |")
    lines.append("")
    lines.append("## Claim-only best, test split")
    lines.append("")
    lines.append("| target | best claim-only model | acc | macro-F1 | positive F1 |")
    lines.append("|---|---|---:|---:|---:|")
    for row in claim_only:
        lines.append(f"| {row['target']} | {row['model']} | {row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |")
    lines.append("")
    lines.append("## Prefix-only leakage check, test split")
    lines.append("")
    lines.append("| target | acc | macro-F1 | positive F1 |")
    lines.append("|---|---:|---:|---:|")
    for row in prefix:
        lines.append(f"| {row['target']} | {row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
