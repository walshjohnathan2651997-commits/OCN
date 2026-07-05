import csv
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\ocn")
EXP_ROOT = ROOT / "experiments" / "llm_baseline_v1_150"
PRED_PATH = EXP_ROOT / "predictions" / "llm_predictions.csv"
METRIC_DIR = EXP_ROOT / "metrics"
REPORT_DIR = EXP_ROOT / "reports"


def compute_metrics(y_true, y_pred):
    y_true = [int(x) for x in y_true]
    y_pred = [int(x) for x in y_pred]
    n = len(y_true)
    acc = sum(a == b for a, b in zip(y_true, y_pred)) / n if n else 0
    cm = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0}
    for a, b in zip(y_true, y_pred):
        cm[(a, b)] += 1
    out = {"accuracy": round(acc, 4), "tn": cm[(0, 0)], "fp": cm[(0, 1)], "fn": cm[(1, 0)], "tp": cm[(1, 1)]}
    f1s = []
    for c in [0, 1]:
        tp = cm[(c, c)]
        fp = sum(cm[(a, c)] for a in [0, 1] if a != c)
        fn = sum(cm[(c, b)] for b in [0, 1] if b != c)
        p = tp / (tp + fp) if tp + fp else 0
        r = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        out[f"class{c}_precision"] = round(p, 4)
        out[f"class{c}_recall"] = round(r, 4)
        out[f"class{c}_f1"] = round(f1, 4)
        f1s.append(f1)
    out["macro_f1"] = round(sum(f1s) / 2, 4)
    return out


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    if not PRED_PATH.exists():
        status = {
            "generated_at_utc": generated_at,
            "status": "blocked_no_predictions",
            "message": "Run run_llm_baseline.py first with a real LLM provider.",
            "expected_prediction_file": str(PRED_PATH),
        }
        (REPORT_DIR / "llm_score_status.json").write_text(json.dumps(status, ensure_ascii=False, indent=2), encoding="utf-8")
        print(json.dumps(status, ensure_ascii=False, indent=2))
        return

    df = pd.read_csv(PRED_PATH, dtype=str).fillna("")
    rows = []
    confusion = []
    for (target, setting, split), g in df.groupby(["target", "setting", "eval_split"]):
        parse_ok = g[g["parse_ok"].astype(str) == "1"].copy()
        parse_fail = len(g) - len(parse_ok)
        if len(parse_ok) == 0:
            continue
        met = compute_metrics(parse_ok["gold_proxy_label"].astype(int), parse_ok["pred_label"].astype(int))
        token_nums = pd.to_numeric(parse_ok["total_tokens"], errors="coerce")
        latency_nums = pd.to_numeric(parse_ok["latency_sec"], errors="coerce")
        row = {
            "generated_at_utc": generated_at,
            "target": target,
            "setting": setting,
            "eval_split": split,
            "n": len(g),
            "n_scored": len(parse_ok),
            "parse_failures": parse_fail,
            "parse_failure_rate": round(parse_fail / len(g), 4) if len(g) else 0,
            "mean_total_tokens": round(float(token_nums.mean()), 2) if token_nums.notna().any() else "",
            "mean_latency_sec": round(float(latency_nums.mean()), 4) if latency_nums.notna().any() else "",
        }
        row.update(met)
        rows.append(row)
        confusion.append({"target": target, "setting": setting, "eval_split": split, "tn": met["tn"], "fp": met["fp"], "fn": met["fn"], "tp": met["tp"]})

    fields = [
        "generated_at_utc",
        "target",
        "setting",
        "eval_split",
        "n",
        "n_scored",
        "parse_failures",
        "parse_failure_rate",
        "accuracy",
        "macro_f1",
        "class0_precision",
        "class0_recall",
        "class0_f1",
        "class1_precision",
        "class1_recall",
        "class1_f1",
        "tn",
        "fp",
        "fn",
        "tp",
        "mean_total_tokens",
        "mean_latency_sec",
    ]
    write_csv(METRIC_DIR / "llm_metrics.csv", rows, fields)
    write_csv(METRIC_DIR / "llm_confusion_matrices.csv", confusion, ["target", "setting", "eval_split", "tn", "fp", "fn", "tp"])

    best = []
    for target in sorted(set(r["target"] for r in rows)):
        test_rows = [r for r in rows if r["target"] == target and r["eval_split"] == "test"]
        test_rows.sort(key=lambda r: (-float(r["macro_f1"]), -float(r["accuracy"]), r["setting"]))
        if test_rows:
            best.append(test_rows[0])
    write_csv(METRIC_DIR / "llm_best_test_summary.csv", best, fields)

    report = [
        "# LLM Baseline v1 150 Score Report",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "| target | setting | test macro-F1 | test accuracy | class1 F1 | parse failure rate |",
        "|---|---|---:|---:|---:|---:|",
    ]
    for r in best:
        report.append(
            f"| {r['target']} | {r['setting']} | {r['macro_f1']} | {r['accuracy']} | {r['class1_f1']} | {r['parse_failure_rate']} |"
        )
    report.append("")
    report.append("Labels are AI-preannotated proxy labels, not gold.")
    (REPORT_DIR / "llm_score_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({"status": "scored", "metric_rows": len(rows), "best": best}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
