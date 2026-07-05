import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASELINE_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_small_data_baselines.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v4_pilot" / "candidates" / "simclaim_hardpair_v4_pilot_candidates.csv"
EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v4_pilot_small_baselines"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"

METRICS_CSV = METRIC_DIR / "v4_pilot_small_data_baseline_metrics.csv"
PER_CLASS_CSV = METRIC_DIR / "v4_pilot_small_data_baseline_per_class_f1.csv"
PRED_CSV = PRED_DIR / "v4_pilot_small_data_baseline_predictions.csv"
SUMMARY_JSON = REPORT_DIR / "v4_pilot_small_data_baseline_summary.json"
REPORT_MD = REPORT_DIR / "v4_pilot_small_data_baseline_report.md"

TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]
TEXT_VIEWS = ["claim_only", "evidence_only", "claim_evidence"]
DATASET_NAME = "simclaim_hardpair_v4_pilot_success_only"
REPORT_TITLE = "v4 pilot small-data baseline report"
REPORT_NOTE = "This report uses only successfully generated v4 pilot rows. It does not use LLM evaluation."
ROW_FILTER = None


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
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def best(rows, target, predicate):
    sub = [r for r in rows if r["split"] == "test" and r["target"] == target and predicate(r)]
    return max(sub, key=lambda r: float(r["macro_f1"]))


def run():
    for p in [METRIC_DIR, PRED_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    rows = [r for r in read_csv(INPUT_CSV) if r.get("claim_generation_status") == "success"]
    if ROW_FILTER is not None:
        rows = [r for r in rows if ROW_FILTER(r)]
    train_rows = [r for r in rows if r.get("split") == "train"]
    dev_rows = [r for r in rows if r.get("split") == "dev"]
    test_rows = [r for r in rows if r.get("split") == "test"]
    if not train_rows or not dev_rows or not test_rows:
        raise RuntimeError(f"missing split rows train={len(train_rows)} dev={len(dev_rows)} test={len(test_rows)}")
    lib = load_lib()
    eval_sets = {"dev": dev_rows, "test": test_rows}
    metric_rows, per_class_rows, pred_rows = [], [], []
    for target in TARGETS:
        for split, eval_rows in eval_sets.items():
            for model in ["majority", "claim_length_median_rule", "prefix_first4_memorize"]:
                if model == "majority":
                    y_pred = lib.majority_predict(train_rows, eval_rows, target)
                elif model == "claim_length_median_rule":
                    y_pred = lib.length_threshold_predict(train_rows, eval_rows, target)
                else:
                    y_pred = lib.prefix_memorize_predict(train_rows, eval_rows, target, n=4)
                row, pcs, preds = lib.score_run(DATASET_NAME, target, split, model, "claim_only", train_rows, eval_rows, y_pred)
                metric_rows.append(row)
                per_class_rows.extend(pcs)
                pred_rows.extend(preds)
            for view in TEXT_VIEWS:
                for model in ["tfidf_centroid", "multinomial_nb"]:
                    if model == "tfidf_centroid":
                        y_pred = lib.tfidf_centroid_predict(train_rows, eval_rows, target, view)
                    else:
                        y_pred = lib.multinomial_nb_predict(train_rows, eval_rows, target, view)
                    row, pcs, preds = lib.score_run(DATASET_NAME, target, split, model, view, train_rows, eval_rows, y_pred)
                    metric_rows.append(row)
                    per_class_rows.extend(pcs)
                    pred_rows.extend(preds)
            y_pred = lib.pair_interaction_centroid_predict(train_rows, eval_rows, target)
            row, pcs, preds = lib.score_run(DATASET_NAME, target, split, "pair_interaction_centroid", "claim_evidence_pair", train_rows, eval_rows, y_pred)
            metric_rows.append(row)
            per_class_rows.extend(pcs)
            pred_rows.extend(preds)
    write_csv(METRICS_CSV, metric_rows)
    write_csv(PER_CLASS_CSV, per_class_rows)
    write_csv(PRED_CSV, pred_rows)
    write_report(metric_rows, rows, train_rows, dev_rows, test_rows)


def write_report(metric_rows, rows, train_rows, dev_rows, test_rows):
    summary = {
        "dataset": DATASET_NAME,
        "n_rows": len(rows),
        "n_groups": len({r["v4_group_id"] for r in rows}),
        "split_rows": {"train": len(train_rows), "dev": len(dev_rows), "test": len(test_rows)},
        "split_groups": {
            "train": len({r["v4_group_id"] for r in train_rows}),
            "dev": len({r["v4_group_id"] for r in dev_rows}),
            "test": len({r["v4_group_id"] for r in test_rows}),
        },
        "metrics_csv": str(METRICS_CSV),
        "report_md": str(REPORT_MD),
        "target_results": {},
    }
    lines = [
        f"# {REPORT_TITLE}",
        "",
        REPORT_NOTE,
        "",
        f"- Rows: {summary['n_rows']}",
        f"- Groups: {summary['n_groups']}",
        f"- Split rows: train={len(train_rows)}, dev={len(dev_rows)}, test={len(test_rows)}",
        f"- Split groups: train={summary['split_groups']['train']}, dev={summary['split_groups']['dev']}, test={summary['split_groups']['test']}",
        "",
        "| target | claim-only F1 | claim+evidence F1 | CE - claim | gate |",
        "|---|---:|---:|---:|---|",
    ]
    all_pass = True
    for target in TARGETS:
        claim = best(metric_rows, target, lambda r: r["text_view"] == "claim_only")
        ce = best(metric_rows, target, lambda r: r["text_view"] in {"claim_evidence", "claim_evidence_pair"})
        delta = float(ce["macro_f1"]) - float(claim["macro_f1"])
        gate = "pass" if delta > 0 else "fail"
        all_pass = all_pass and delta > 0
        summary["target_results"][target] = {
            "claim_only_best": claim,
            "claim_evidence_best": ce,
            "delta_ce_minus_claim": round(delta, 6),
            "gate": gate,
        }
        lines.append(f"| {target} | {claim['macro_f1']} | {ce['macro_f1']} | {delta:.6f} | {gate} |")
    summary["overall_gate"] = "pass" if all_pass else "fail"
    lines.extend([
        "",
        f"Overall gate: **{summary['overall_gate']}**",
    ])
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
