import csv
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))

from run_formal_baselines import TARGETS, compute_metrics, run_one  # noqa: E402


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data" / "simclaim_mvp_expansion_v1_150"
EXP_ROOT = ROOT / "experiments" / "formal_baseline_v1_150"
METRIC_DIR = EXP_ROOT / "metrics"
REPORT_DIR = EXP_ROOT / "reports"

TRAIN_PATH = DATA_ROOT / "splits" / "train.csv"
DEV_PATH = DATA_ROOT / "splits" / "dev.csv"
TEST_PATH = DATA_ROOT / "splits" / "test.csv"

MODELS = ["tfidf_centroid", "tfidf_logistic_l2", "tfidf_linear_svm_hinge"]
VIEWS = ["claim_only", "claim_evidence"]


PREFIX_PATTERNS = [
    r"^\s*the passage reports that\s+",
    r"^\s*a bounded reading of the evidence is that\s+",
    r"^\s*the study demonstrates that\s+",
    r"^\s*the claim moves from the reported setting to .*? interpretation:\s+",
    r"^\s*the claim suggests broader .*? establishes:\s+",
]


def strip_prefix(text):
    out = str(text)
    low = out.lower()
    for pat in PREFIX_PATTERNS:
        m = re.match(pat, low, flags=re.IGNORECASE)
        if m:
            out = out[m.end() :]
            break
    # Remove one common appended boilerplate sentence, but keep the substantive claim text.
    out = re.sub(r"\s*this result can be generalized to broader settings\.?\s*$", "", out, flags=re.IGNORECASE)
    return out.strip()


def read_split(path, split):
    df = pd.read_csv(path, dtype=str).fillna("")
    df["eval_split"] = split
    df["claim_text_original_for_prefix_stripped_diag"] = df["claim_text"]
    df["claim_text"] = df["claim_text"].map(strip_prefix)
    return df


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    train = read_split(TRAIN_PATH, "train")
    dev = read_split(DEV_PATH, "dev")
    test = read_split(TEST_PATH, "test")

    metric_rows = []
    for target in TARGETS:
        for view in VIEWS:
            for model in MODELS:
                for split_name, eval_df in [("dev", dev), ("test", test)]:
                    pred, score, met, meta = run_one(train, eval_df, target, view, model)
                    metric_rows.append(
                        {
                            "generated_at_utc": generated_at,
                            "target": target,
                            "input_view": view + "_prefix_stripped",
                            "model": model,
                            "eval_split": split_name,
                            "n_train": len(train),
                            "n_eval": len(eval_df),
                            "accuracy": met["accuracy"],
                            "macro_f1": met["macro_f1"],
                            "class0_f1": met["class0_f1"],
                            "class1_f1": met["class1_f1"],
                            "feature_info_json": json.dumps(meta, ensure_ascii=False),
                            "notes": "diagnostic only; obvious claim-prefix templates stripped; labels are AI-preannotated, not gold",
                        }
                    )

    out_path = METRIC_DIR / "prefix_stripped_baseline_metrics.csv"
    write_csv(
        out_path,
        metric_rows,
        [
            "generated_at_utc",
            "target",
            "input_view",
            "model",
            "eval_split",
            "n_train",
            "n_eval",
            "accuracy",
            "macro_f1",
            "class0_f1",
            "class1_f1",
            "feature_info_json",
            "notes",
        ],
    )

    best_rows = []
    for target in TARGETS:
        for split in ["dev", "test"]:
            candidates = [r for r in metric_rows if r["target"] == target and r["eval_split"] == split]
            candidates.sort(key=lambda r: (-float(r["macro_f1"]), -float(r["accuracy"]), r["input_view"], r["model"]))
            if candidates:
                top = candidates[0]
                best_rows.append(
                    {
                        "target": target,
                        "eval_split": split,
                        "best_model": top["model"],
                        "best_input_view": top["input_view"],
                        "accuracy": top["accuracy"],
                        "macro_f1": top["macro_f1"],
                        "class0_f1": top["class0_f1"],
                        "class1_f1": top["class1_f1"],
                    }
                )
    write_csv(
        METRIC_DIR / "prefix_stripped_best_summary.csv",
        best_rows,
        ["target", "eval_split", "best_model", "best_input_view", "accuracy", "macro_f1", "class0_f1", "class1_f1"],
    )

    report = [
        "# Prefix-Stripped Baseline Diagnostic",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "This diagnostic strips obvious claim-prefix templates before rerunning TF-IDF baselines.",
        "It estimates how much performance remains after removing the most visible wording cues.",
        "",
        "| target | split | best model | view | accuracy | macro-F1 | class0 F1 | class1 F1 |",
        "|---|---|---|---|---:|---:|---:|---:|",
    ]
    for r in best_rows:
        report.append(
            f"| {r['target']} | {r['eval_split']} | {r['best_model']} | {r['best_input_view']} | {r['accuracy']} | {r['macro_f1']} | {r['class0_f1']} | {r['class1_f1']} |"
        )
    report.extend(
        [
            "",
            "Interpretation: if scores remain very high, the synthetic claim wording still carries label cues beyond the first prefix. If scores drop toward 0.60-0.70, the earlier 1.0 was mainly template-driven.",
        ]
    )
    (REPORT_DIR / "prefix_stripped_baseline_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps({"rows": len(metric_rows), "best_rows": best_rows, "metrics": str(out_path)}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
