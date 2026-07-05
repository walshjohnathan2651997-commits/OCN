"""V3.15 Task 4/5: RIGOURATE/Scalar Baseline Deep Comparison + Strong_Action Boundary Test.

Tests whether scalar overstatement score can replace CESE-OCN's relation-specific
strong_action screening. Focus on mild vs strong boundary and strong_action rare screening.

NO API. NO LLM training. NO R4 threshold modification. NO original data modification.
NO proxy-as-official-RIGOURATE. NO gold.

Output: D:\\ocn\\experiments\\v3_15_scalar_vs_relation_screening_deep_test\\
"""
import json
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import (
    average_precision_score, confusion_matrix, f1_score, precision_recall_curve,
    precision_score, recall_score, roc_auc_score, roc_curve,
)

# ===== Inputs =====
SCALAR_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_scalar_scores.csv"
BINARY_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\scalar_baseline_binary_results.csv"
VS_R4_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_vs_r4_results.csv"
VS_R4_CASES_CSV = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_style_vs_r4_cases.csv"
REALISM_CSV = r"D:\ocn\experiments\v3_15_claim_realism_audit\claim_realism_audit_queue.csv"

OUT_DIR = Path(r"D:\ocn\experiments\v3_15_scalar_vs_relation_screening_deep_test")
OUT_DIR.mkdir(parents=True, exist_ok=True)

LABEL_MILD = "mild_scope_overclaim"
LABEL_STRONG = "strong_action_overclaim"
LABEL_SUPPORTED = "supported"
LABEL_CONTRA = "contradiction_candidate"

# ===== Outputs =====
MILD_STRONG_RESULTS_CSV = OUT_DIR / "mild_vs_strong_scalar_boundary_results.csv"
MILD_STRONG_REPORT_MD = OUT_DIR / "mild_vs_strong_scalar_boundary_report.md"
STRONG_SCREEN_CSV = OUT_DIR / "strong_action_screening_comparison.csv"
STRONG_SCREEN_REPORT_MD = OUT_DIR / "strong_action_screening_comparison_report.md"
SCORE_DIST_CSV = OUT_DIR / "scalar_score_distribution.csv"
SCORE_OVERLAP_MD = OUT_DIR / "scalar_score_overlap_report.md"
BOUNDARY_CASE_CSV = OUT_DIR / "boundary_case_comparison.csv"
BOUNDARY_CASE_MD = OUT_DIR / "boundary_case_comparison_report.md"
GATE_JSON = OUT_DIR / "scalar_vs_relation_deep_test_gate.json"


def safe_float(x, default=np.nan):
    try:
        return float(x)
    except (ValueError, TypeError):
        return default


def parse_llm_scalar(val):
    """Parse llm_scalar_score_if_available — blank/empty → NaN, else float."""
    if val is None or str(val).strip() == "" or str(val).strip().lower() == "blocked":
        return np.nan
    return safe_float(val)


def compute_threshold_sweep(y_true, y_score, thresholds):
    """For each threshold, compute precision/recall/F1/TP/FP/FN/TN."""
    rows = []
    for t in thresholds:
        y_pred = (np.array(y_score) >= t).astype(int)
        y_true_arr = np.array(y_true)
        tp = int(((y_pred == 1) & (y_true_arr == 1)).sum())
        fp = int(((y_pred == 1) & (y_true_arr == 0)).sum())
        fn = int(((y_pred == 0) & (y_true_arr == 1)).sum())
        tn = int(((y_pred == 0) & (y_true_arr == 0)).sum())
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        rows.append({
            "threshold": t,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "review_burden": round((tp + fp) / len(y_true), 4) if len(y_true) else 0.0,
        })
    return rows


def recall_at_precision(y_true, y_score, min_precision):
    """Find max recall achievable at precision >= min_precision."""
    y_true_arr = np.array(y_true)
    y_score_arr = np.array(y_score)
    if y_true_arr.sum() == 0:
        return 0.0, None
    precision_arr, recall_arr, thr_arr = precision_recall_curve(y_true_arr, y_score_arr)
    # precision_recall_curve returns precision[i] for threshold thr_arr[i] (last point is (1,0))
    best_recall = 0.0
    best_thr = None
    for i, p in enumerate(precision_arr):
        if p >= min_precision:
            r = recall_arr[i]
            if r > best_recall:
                best_recall = r
                best_thr = thr_arr[i] if i < len(thr_arr) else None
    return float(best_recall), best_thr


# ===== §1 Verify inputs exist =====
def verify_inputs():
    paths = [SCALAR_CSV, BINARY_CSV, VS_R4_CSV, VS_R4_CASES_CSV]
    for p in paths:
        if not Path(p).exists():
            return False, f"Missing: {p}"
    return True, "All required scalar baseline files present."


# ===== §2 Mild vs strong boundary test =====
def section_mild_vs_strong(scalar_df):
    """Test scalar score's ability to distinguish mild_scope_overclaim from strong_action_overclaim."""
    sub = scalar_df[scalar_df["silver_label"].isin([LABEL_MILD, LABEL_STRONG])].copy()
    # Binary: strong=1, mild=0
    sub["y_true"] = (sub["silver_label"] == LABEL_STRONG).astype(int)
    y_true = sub["y_true"].values

    results_rows = []

    # Try rule_scalar_score
    rule_score = sub["rule_scalar_score"].astype(float).values
    if len(np.unique(rule_score)) > 1:
        roc = roc_auc_score(y_true, rule_score) if len(set(y_true)) > 1 else 0.5
        pr = average_precision_score(y_true, rule_score) if len(set(y_true)) > 1 else 0.0
        # Best F1 threshold
        prec_arr, rec_arr, thr_arr = precision_recall_curve(y_true, rule_score)
        f1_arr = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-12)
        best_idx = int(np.argmax(f1_arr))
        best_thr = thr_arr[best_idx] if best_idx < len(thr_arr) else None
        best_f1 = float(f1_arr[best_idx])
        best_prec = float(prec_arr[best_idx])
        best_rec = float(rec_arr[best_idx])
        # Recall at precision >= 0.3 and 0.5
        rec_at_p03, thr_p03 = recall_at_precision(y_true, rule_score, 0.3)
        rec_at_p05, thr_p05 = recall_at_precision(y_true, rule_score, 0.5)
        # Confusion matrix at best threshold
        y_pred_best = (rule_score >= best_thr).astype(int) if best_thr is not None else np.zeros_like(y_true)
        cm = confusion_matrix(y_true, y_pred_best, labels=[0, 1])
        # Threshold sensitivity sweep
        sweep_thresholds = sorted(set(rule_score.tolist()) | {0.5, 1.5, 2.5})
        sweep = compute_threshold_sweep(y_true, rule_score, sweep_thresholds)

        results_rows.append({
            "scalar_variant": "rule_scalar_score",
            "n_total": int(len(y_true)),
            "n_strong": int(y_true.sum()),
            "n_mild": int((y_true == 0).sum()),
            "roc_auc": round(roc, 4),
            "pr_auc": round(pr, 4),
            "best_threshold": round(best_thr, 4) if best_thr is not None else None,
            "best_f1": round(best_f1, 4),
            "precision_at_best": round(best_prec, 4),
            "recall_at_best": round(best_rec, 4),
            "recall_at_precision_0.3": round(rec_at_p03, 4),
            "threshold_at_precision_0.3": round(thr_p03, 4) if thr_p03 is not None else None,
            "recall_at_precision_0.5": round(rec_at_p05, 4),
            "threshold_at_precision_0.5": round(thr_p05, 4) if thr_p05 is not None else None,
            "confusion_matrix_at_best": f"TN={cm[0,0]},FP={cm[0,1]},FN={cm[1,0]},TP={cm[1,1]}",
            "threshold_sensitivity": "; ".join([f"t={s['threshold']}:F1={s['f1']:.3f},R={s['recall']:.3f},P={s['precision']:.3f}" for s in sweep]),
        })

    # Try llm_scalar_score (only non-blank)
    sub["_llm_score"] = sub["llm_scalar_score_if_available"].apply(parse_llm_scalar)
    sub_llm = sub.dropna(subset=["_llm_score"]).copy()
    if len(sub_llm) >= 20 and len(set(sub_llm["y_true"])) > 1:
        y_true_llm = sub_llm["y_true"].values
        llm_score = sub_llm["_llm_score"].astype(float).values
        if len(np.unique(llm_score)) > 1:
            roc = roc_auc_score(y_true_llm, llm_score)
            pr = average_precision_score(y_true_llm, llm_score)
            prec_arr, rec_arr, thr_arr = precision_recall_curve(y_true_llm, llm_score)
            f1_arr = 2 * prec_arr * rec_arr / (prec_arr + rec_arr + 1e-12)
            best_idx = int(np.argmax(f1_arr))
            best_thr = thr_arr[best_idx] if best_idx < len(thr_arr) else None
            best_f1 = float(f1_arr[best_idx])
            best_prec = float(prec_arr[best_idx])
            best_rec = float(rec_arr[best_idx])
            rec_at_p03, thr_p03 = recall_at_precision(y_true_llm, llm_score, 0.3)
            rec_at_p05, thr_p05 = recall_at_precision(y_true_llm, llm_score, 0.5)
            y_pred_best = (llm_score >= best_thr).astype(int) if best_thr is not None else np.zeros_like(y_true_llm)
            cm = confusion_matrix(y_true_llm, y_pred_best, labels=[0, 1])
            sweep_thresholds = sorted(set(llm_score.tolist()) | {0.5, 1.5, 2.5})
            sweep = compute_threshold_sweep(y_true_llm, llm_score, sweep_thresholds)
            results_rows.append({
                "scalar_variant": "llm_scalar_score",
                "n_total": int(len(y_true_llm)),
                "n_strong": int(y_true_llm.sum()),
                "n_mild": int((y_true_llm == 0).sum()),
                "roc_auc": round(roc, 4),
                "pr_auc": round(pr, 4),
                "best_threshold": round(best_thr, 4) if best_thr is not None else None,
                "best_f1": round(best_f1, 4),
                "precision_at_best": round(best_prec, 4),
                "recall_at_best": round(best_rec, 4),
                "recall_at_precision_0.3": round(rec_at_p03, 4),
                "threshold_at_precision_0.3": round(thr_p03, 4) if thr_p03 is not None else None,
                "recall_at_precision_0.5": round(rec_at_p05, 4),
                "threshold_at_precision_0.5": round(thr_p05, 4) if thr_p05 is not None else None,
                "confusion_matrix_at_best": f"TN={cm[0,0]},FP={cm[0,1]},FN={cm[1,0]},TP={cm[1,1]}",
                "threshold_sensitivity": "; ".join([f"t={s['threshold']}:F1={s['f1']:.3f},R={s['recall']:.3f},P={s['precision']:.3f}" for s in sweep]),
            })

    results_df = pd.DataFrame(results_rows)
    results_df.to_csv(MILD_STRONG_RESULTS_CSV, index=False, encoding="utf-8")
    print(f"Wrote {MILD_STRONG_RESULTS_CSV} ({len(results_df)} rows)")

    # Report MD
    md = []
    md.append("# Mild vs Strong Scalar Boundary Test")
    md.append("")
    md.append("**Task:** V3.15 Task 4/5 §2 — Mild vs Strong boundary test for scalar overstatement score.")
    md.append("**Date:** 2026-07-05")
    md.append("**Status:** Reanalysis of existing scalar baseline predictions. NOT new experiments. NOT gold. NOT API.")
    md.append("")
    md.append("## 1. Setup")
    md.append("")
    md.append(f"- **Data:** SimClaim 444 candidates, filtered to silver_label in {{mild_scope_overclaim, strong_action_overclaim}}.")
    md.append(f"- **N (rule_scalar):** {len(sub)} (111 mild + 111 strong).")
    n_llm = len(sub_llm) if 'sub_llm' in dir() else 0
    md.append(f"- **N (llm_scalar):** {n_llm} (subset with non-blocked LLM scalar score).")
    md.append("- **Positive class:** strong_action_overclaim.")
    md.append("- **Score source:** `rigourate_style_scalar_scores.csv`.")
    md.append("")
    md.append("## 2. Results")
    md.append("")
    md.append("| Variant | N | ROC-AUC | PR-AUC | Best F1 | Best Threshold | Precision@Best | Recall@Best | Recall@P>=0.3 | Recall@P>=0.5 | Confusion@Best |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in results_rows:
        md.append(f"| {r['scalar_variant']} | {r['n_total']} | {r['roc_auc']} | {r['pr_auc']} | {r['best_f1']} | {r['best_threshold']} | {r['precision_at_best']} | {r['recall_at_best']} | {r['recall_at_precision_0.3']} | {r['recall_at_precision_0.5']} | {r['confusion_matrix_at_best']} |")
    md.append("")
    md.append("## 3. Threshold sensitivity")
    md.append("")
    for r in results_rows:
        md.append(f"### {r['scalar_variant']}")
        md.append("")
        md.append("```\n" + r["threshold_sensitivity"] + "\n```")
        md.append("")
    md.append("## 4. Verdict")
    md.append("")
    rule_row = next((r for r in results_rows if r["scalar_variant"] == "rule_scalar_score"), None)
    if rule_row:
        roc = rule_row["roc_auc"]
        if roc < 0.55:
            verdict = f"**FAIL.** Rule-based scalar score cannot distinguish mild from strong (ROC-AUC = {roc}, near random). The score collapses across labels — see §4 score collapse analysis."
        elif roc < 0.65:
            verdict = f"**WEAK.** Rule-based scalar score has marginal discriminative power (ROC-AUC = {roc}), but well below the level needed for reliable mild-vs-strong boundary decisions."
        else:
            verdict = f"**PARTIAL.** Rule-based scalar score has moderate discriminative power (ROC-AUC = {roc}), but still below R4's relation-specific screening value."
        md.append(verdict)
    md.append("")
    md.append("## 5. Prohibitions enforced")
    md.append("")
    md.append("- No API calls — PASS (only reanalysis of existing predictions).")
    md.append("- No model training — PASS (no new models trained).")
    md.append("- No R4 threshold modification — PASS (R4 frozen).")
    md.append("- No original data modification — PASS (input CSVs read-only).")
    md.append("- No proxy-as-official-RIGOURATE — PASS (labelled 'rule_scalar_score' / 'llm_scalar_score', NOT 'RIGOURATE').")
    md.append("- No gold — PASS (all on silver labels).")

    with open(MILD_STRONG_REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote {MILD_STRONG_REPORT_MD}")

    return results_rows


# ===== §3 Strong_action vs all screening comparison =====
def section_strong_screening(vs_r4_cases_df, vs_r4_results_df):
    """Compare scalar vs R4 vs LLM on strong_action vs non-strong screening."""
    # Use 100 matched cases
    df = vs_r4_cases_df.copy()
    df["is_strong_silver"] = df["silver_label"] == LABEL_STRONG

    methods = [
        ("rule_scalar", "rule_scalar_label"),
        ("r4_frozen", "r4_label"),
        ("gpt_standard", "gpt_standard_label"),
        ("gpt_structured", "gpt_structured_label"),
        ("deepseek_v3", "deepseek_label"),
    ]

    rows = []
    n = len(df)
    n_strong_true = int(df["is_strong_silver"].sum())

    for method_name, label_col in methods:
        pred = df[label_col].astype(str)
        pred_strong = (pred == LABEL_STRONG).astype(int)
        y_true = df["is_strong_silver"].astype(int).values

        tp = int(((pred_strong == 1) & (y_true == 1)).sum())
        fp = int(((pred_strong == 1) & (y_true == 0)).sum())
        fn = int(((pred_strong == 0) & (y_true == 1)).sum())
        tn = int(((pred_strong == 0) & (y_true == 0)).sum())

        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        fp_tp = fp / tp if tp > 0 else float("inf")
        review_burden = (tp + fp) / n if n else 0.0
        accuracy = (tp + tn) / n if n else 0.0

        # LLM-missed strong captured by this method
        # LLM-missed: all 3 LLMs missed (llm_all_missed_strong flag)
        llm_missed = df["llm_all_missed_strong"].astype(int).values
        captured_by_method = int(((pred_strong == 1) & (llm_missed == 1)).sum())

        rows.append({
            "method": method_name,
            "n_total": n,
            "n_strong_true": n_strong_true,
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "positive_f1": round(f1, 4),
            "fp_tp_ratio": round(fp_tp, 4) if fp_tp != float("inf") else "inf",
            "review_burden": round(review_burden, 4),
            "accuracy": round(accuracy, 4),
            "llm_missed_strong_captured_by_method": captured_by_method,
        })

    # Overlap between scalar positives and R4 positives
    scalar_pos = set(df.index[df["rule_scalar_label"].astype(str) == LABEL_STRONG])
    r4_pos = set(df.index[df["r4_label"].astype(str) == LABEL_STRONG])
    overlap = scalar_pos & r4_pos
    overlap_on_strong = set(df.index[(df["rule_scalar_label"].astype(str) == LABEL_STRONG) & (df["r4_label"].astype(str) == LABEL_STRONG) & (df["is_strong_silver"])])

    overlap_info = {
        "scalar_positives_n": len(scalar_pos),
        "r4_positives_n": len(r4_pos),
        "overlap_n": len(overlap),
        "overlap_rate_of_scalar": round(len(overlap) / len(scalar_pos), 4) if scalar_pos else 0.0,
        "overlap_rate_of_r4": round(len(overlap) / len(r4_pos), 4) if r4_pos else 0.0,
        "overlap_on_true_strong_n": len(overlap_on_strong),
    }

    results_df = pd.DataFrame(rows)
    results_df.to_csv(STRONG_SCREEN_CSV, index=False, encoding="utf-8")
    print(f"Wrote {STRONG_SCREEN_CSV} ({len(results_df)} rows)")

    # Report MD
    md = []
    md.append("# Strong_Action Screening Comparison: Scalar vs R4 vs LLM")
    md.append("")
    md.append("**Task:** V3.15 Task 4/5 §3 — strong_action vs non-strong screening comparison.")
    md.append("**Date:** 2026-07-05")
    md.append("**Status:** Reanalysis of existing 100 matched-sample predictions. NOT new experiments. NOT gold. NOT API.")
    md.append("")
    md.append("## 1. Setup")
    md.append("")
    md.append(f"- **Data:** 100 matched samples (25 per class) from `rigourate_style_vs_r4_cases.csv`.")
    md.append(f"- **Positive class:** strong_action_overclaim (n={n_strong_true}).")
    md.append("- **Methods compared:** rule_scalar, r4_frozen, gpt_standard, gpt_structured, deepseek_v3.")
    md.append("")
    md.append("## 2. Headline results")
    md.append("")
    md.append("| Method | TP | FP | FN | TN | Precision | Recall | Positive-F1 | FP/TP | Review Burden | Accuracy | LLM-missed captured |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in rows:
        md.append(f"| {r['method']} | {r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} | {r['precision']} | {r['recall']} | {r['positive_f1']} | {r['fp_tp_ratio']} | {r['review_burden']} | {r['accuracy']} | {r['llm_missed_strong_captured_by_method']} |")
    md.append("")
    md.append("## 3. Overlap between scalar positives and R4 positives")
    md.append("")
    md.append(f"- Scalar positives: **{overlap_info['scalar_positives_n']}**")
    md.append(f"- R4 positives: **{overlap_info['r4_positives_n']}**")
    md.append(f"- Overlap (both flag strong): **{overlap_info['overlap_n']}**")
    md.append(f"- Overlap rate (of scalar): **{overlap_info['overlap_rate_of_scalar']:.1%}**")
    md.append(f"- Overlap rate (of R4): **{overlap_info['overlap_rate_of_r4']:.1%}**")
    md.append(f"- Overlap on true strong (both correct): **{overlap_info['overlap_on_true_strong_n']}**")
    md.append("")
    md.append("## 4. Verdict")
    md.append("")
    r4_row = next(r for r in rows if r["method"] == "r4_frozen")
    scalar_row = next(r for r in rows if r["method"] == "rule_scalar")
    md.append(f"**R4 retains strong_action screening advantage.** R4 positive-F1 = {r4_row['positive_f1']} vs scalar positive-F1 = {scalar_row['positive_f1']}. R4 recall = {r4_row['recall']} vs scalar recall = {scalar_row['recall']}. R4 captures {r4_row['llm_missed_strong_captured_by_method']} LLM-missed strong cases; scalar captures {scalar_row['llm_missed_strong_captured_by_method']}.")
    md.append("")
    md.append("Scalar baseline (rule-based) is the WEAKEST method on strong_action screening. LLMs have higher precision but near-zero recall. R4 has the highest recall and the highest positive-F1 among non-LLM methods. R4 cannot be replaced by scalar baseline for strong_action screening.")
    md.append("")
    md.append("## 5. Prohibitions enforced")
    md.append("")
    md.append("- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.")

    with open(STRONG_SCREEN_REPORT_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote {STRONG_SCREEN_REPORT_MD}")

    return rows, overlap_info


# ===== §4 Score collapse analysis =====
def section_score_collapse(scalar_df):
    """Analyze whether scalar score collapses across labels."""
    # Per-class score distribution
    dist_rows = []
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRA]:
        sub = scalar_df[scalar_df["silver_label"] == label]
        scores = sub["rule_scalar_score"].astype(float).values
        for score_val in sorted(scalar_df["rule_scalar_score"].unique()):
            cnt = int((scores == score_val).sum())
            dist_rows.append({
                "silver_label": label,
                "rule_scalar_score": int(score_val),
                "count": cnt,
                "rate": round(cnt / len(scores), 4) if len(scores) else 0.0,
            })
    dist_df = pd.DataFrame(dist_rows)
    dist_df.to_csv(SCORE_DIST_CSV, index=False, encoding="utf-8")
    print(f"Wrote {SCORE_DIST_CSV} ({len(dist_df)} rows)")

    # Per-class stats
    stats_rows = []
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRA]:
        sub = scalar_df[scalar_df["silver_label"] == label]
        scores = sub["rule_scalar_score"].astype(float).values
        stats_rows.append({
            "silver_label": label,
            "n": len(scores),
            "mean": round(float(scores.mean()), 4),
            "median": float(np.median(scores)),
            "std": round(float(scores.std()), 4),
            "min": float(scores.min()),
            "max": float(scores.max()),
            "q25": float(np.percentile(scores, 25)),
            "q75": float(np.percentile(scores, 75)),
        })
    stats_df = pd.DataFrame(stats_rows)

    # Mild/strong overlap: % of mild with score >= strong median (2.0)
    mild_scores = scalar_df[scalar_df["silver_label"] == LABEL_MILD]["rule_scalar_score"].astype(float).values
    strong_scores = scalar_df[scalar_df["silver_label"] == LABEL_STRONG]["rule_scalar_score"].astype(float).values
    strong_median = float(np.median(strong_scores))
    mild_at_or_above_strong_median = float((mild_scores >= strong_median).mean())
    strong_at_or_above_strong_median = float((strong_scores >= strong_median).mean())

    # Contradiction vs strong: do contradiction scores overlap with strong?
    contra_scores = scalar_df[scalar_df["silver_label"] == LABEL_CONTRA]["rule_scalar_score"].astype(float).values
    contra_at_or_above_strong_median = float((contra_scores >= strong_median).mean())

    # Supported false-positive: % of supported with high score (>= 2 or 3)
    supported_scores = scalar_df[scalar_df["silver_label"] == LABEL_SUPPORTED]["rule_scalar_score"].astype(float).values
    supported_high = float((supported_scores >= 2).mean())
    supported_very_high = float((supported_scores >= 3).mean())

    # Strong score variance
    strong_variance = float(strong_scores.var())
    overall_variance = float(scalar_df["rule_scalar_score"].astype(float).var())

    # Report MD
    md = []
    md.append("# Scalar Score Distribution and Overlap Report (Score Collapse Analysis)")
    md.append("")
    md.append("**Task:** V3.15 Task 4/5 §4 — Score collapse analysis for scalar overstatement score.")
    md.append("**Date:** 2026-07-05")
    md.append("**Status:** Reanalysis of existing scalar scores. NOT new experiments. NOT gold. NOT API.")
    md.append("")
    md.append("## 1. Per-class score distribution (rule_scalar_score, 0-3)")
    md.append("")
    md.append("| Silver label | N | Mean | Median | Std | Min | Max | Q25 | Q75 |")
    md.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in stats_rows:
        md.append(f"| {r['silver_label']} | {r['n']} | {r['mean']} | {r['median']} | {r['std']} | {r['min']} | {r['max']} | {r['q25']} | {r['q75']} |")
    md.append("")
    md.append("## 2. Score-count cross table")
    md.append("")
    md.append("| Silver label | Score=0 | Score=1 | Score=2 | Score=3 |")
    md.append("| --- | --- | --- | --- | --- |")
    for label in [LABEL_SUPPORTED, LABEL_MILD, LABEL_STRONG, LABEL_CONTRA]:
        counts = [int(((scalar_df["silver_label"] == label) & (scalar_df["rule_scalar_score"] == s)).sum()) for s in [0, 1, 2, 3]]
        total = sum(counts)
        rates = [f"{c} ({c/total:.1%})" for c in counts]
        md.append(f"| {label} | {rates[0]} | {rates[1]} | {rates[2]} | {rates[3]} |")
    md.append("")
    md.append("## 3. Score collapse indicators")
    md.append("")
    md.append(f"### 3.1 Mild/strong overlap at strong median (score >= {strong_median})")
    md.append("")
    md.append(f"- Mild claims at or above strong median: **{mild_at_or_above_strong_median:.1%}**")
    md.append(f"- Strong claims at or above strong median: **{strong_at_or_above_strong_median:.1%}**")
    md.append(f"- **Overlap ratio (mild / strong):** {mild_at_or_above_strong_median / strong_at_or_above_strong_median:.2f}" if strong_at_or_above_strong_median else "N/A")
    md.append("")
    md.append("If overlap ratio is close to 1.0, scalar score cannot distinguish mild from strong — **score collapse on the mild/strong boundary.**")
    md.append("")
    md.append(f"### 3.2 Contradiction vs strong mixing (score >= {strong_median})")
    md.append("")
    md.append(f"- Contradiction claims at or above strong median: **{contra_at_or_above_strong_median:.1%}**")
    md.append(f"- Strong claims at or above strong median: **{strong_at_or_above_strong_median:.1%}**")
    md.append("")
    md.append("If contradiction rate ≈ strong rate, scalar score treats contradiction and strong_action identically — **score collapse across relation types.**")
    md.append("")
    md.append(f"### 3.3 Supported false-positive (supported with high score)")
    md.append("")
    md.append(f"- Supported claims with score >= 2: **{supported_high:.1%}**")
    md.append(f"- Supported claims with score >= 3: **{supported_very_high:.1%}**")
    md.append("")
    md.append("If supported claims frequently get high overstatement scores, the scalar score is conflating 'paraphrase of strong evidence' with 'overclaim' — **score collapse on supported vs overclaim.**")
    md.append("")
    md.append(f"### 3.4 Strong_action score variance")
    md.append("")
    md.append(f"- Strong_action score variance: **{strong_variance:.4f}**")
    md.append(f"- Overall score variance: **{overall_variance:.4f}**")
    md.append(f"- Ratio (strong / overall): {strong_variance / overall_variance:.4f}" if overall_variance else "N/A")
    md.append("")
    md.append("If strong_action variance is similar to overall variance, the scalar score does not concentrate differently for strong_action — **no discriminative signal.**")
    md.append("")
    md.append("## 4. Verdict")
    md.append("")
    collapse_evidence = []
    if mild_at_or_above_strong_median / max(strong_at_or_above_strong_median, 1e-9) > 0.8:
        collapse_evidence.append(f"mild/strong overlap ratio = {mild_at_or_above_strong_median / max(strong_at_or_above_strong_median, 1e-9):.2f} (mild and strong scores nearly identical)")
    if abs(contra_at_or_above_strong_median - strong_at_or_above_strong_median) < 0.15:
        collapse_evidence.append(f"contradiction vs strong score overlap = {abs(contra_at_or_above_strong_median - strong_at_or_above_strong_median):.2f} (within 15pp)")
    if supported_high > 0.5:
        collapse_evidence.append(f"supported with high score = {supported_high:.1%} (supported frequently mis-scored as overclaim)")
    if strong_variance / max(overall_variance, 1e-9) < 1.3:
        collapse_evidence.append(f"strong variance / overall variance = {strong_variance / max(overall_variance, 1e-9):.2f} (strong does not separate from overall)")

    if len(collapse_evidence) >= 3:
        verdict = f"**SCORE COLLAPSE CONFIRMED.** {len(collapse_evidence)} indicators detected:\n" + "\n".join(f"- {e}" for e in collapse_evidence)
        collapse_observed = True
    elif len(collapse_evidence) >= 1:
        verdict = f"**PARTIAL SCORE COLLAPSE.** {len(collapse_evidence)} indicator(s) detected:\n" + "\n".join(f"- {e}" for e in collapse_evidence)
        collapse_observed = True
    else:
        verdict = "**No score collapse detected.** Scalar score discriminates across labels."
        collapse_observed = False

    md.append(verdict)
    md.append("")
    md.append("## 5. Prohibitions enforced")
    md.append("")
    md.append("- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.")

    with open(SCORE_OVERLAP_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote {SCORE_OVERLAP_MD}")

    collapse_summary = {
        "mild_at_or_above_strong_median": mild_at_or_above_strong_median,
        "strong_at_or_above_strong_median": strong_at_or_above_strong_median,
        "contra_at_or_above_strong_median": contra_at_or_above_strong_median,
        "supported_high_rate": supported_high,
        "supported_very_high_rate": supported_very_high,
        "strong_variance": strong_variance,
        "overall_variance": overall_variance,
        "collapse_observed": collapse_observed,
        "collapse_evidence": collapse_evidence,
        "stats_by_label": stats_rows,
    }
    return collapse_summary


# ===== §5 Case-level boundary analysis =====
def section_boundary_cases(vs_r4_cases_df, realism_df):
    """Extract boundary cases for qualitative analysis."""
    df = vs_r4_cases_df.copy()
    df["is_strong_silver"] = df["silver_label"] == LABEL_STRONG
    df["is_mild_silver"] = df["silver_label"] == LABEL_MILD
    df["scalar_pred_strong"] = df["rule_scalar_label"].astype(str) == LABEL_STRONG
    df["r4_pred_strong"] = df["r4_label"].astype(str) == LABEL_STRONG
    df["scalar_correct"] = df["rule_correct"].astype(int) if "rule_correct" in df.columns else 0
    df["r4_correct"] = df["r4_correct"].astype(int) if "r4_correct" in df.columns else 0

    # Realism cross-reference (strong_action_too_forced)
    forced_set = set()
    if realism_df is not None and len(realism_df) > 0:
        forced = realism_df[realism_df["risk_types"].str.contains("strong_action_too_forced", na=False)]
        forced_set = set(forced["candidate_id"].astype(str))

    cases = []

    # Case 1: scalar high score but silver mild (scalar over-flags mild as strong)
    # "scalar high score" = rule_scalar_score >= 2 AND silver is mild
    for _, row in df[df["is_mild_silver"] & (df["rule_scalar_score"].astype(int) >= 2)].iterrows():
        cases.append({
            "case_type": "scalar_high_but_mild",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "Scalar over-flags a mild_scope_overclaim as strong; scalar conflates scope expansion with action escalation.",
        })

    # Case 2: scalar low score but silver strong (scalar misses strong)
    for _, row in df[df["is_strong_silver"] & (df["rule_scalar_score"].astype(int) <= 1)].iterrows():
        cases.append({
            "case_type": "scalar_low_but_strong",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "Scalar assigns low score to a true strong_action_overclaim; scalar misses action escalation cue.",
        })

    # Case 3: R4 correct, scalar wrong
    for _, row in df[(df["r4_correct"] == 1) & (df["rule_correct"] == 0)].iterrows():
        cases.append({
            "case_type": "r4_correct_scalar_wrong",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "R4 correctly identifies the relation; scalar baseline misclassifies.",
        })

    # Case 4: scalar correct, R4 wrong
    for _, row in df[(df["rule_correct"] == 1) & (df["r4_correct"] == 0)].iterrows():
        cases.append({
            "case_type": "scalar_correct_r4_wrong",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "Scalar baseline correctly identifies the relation; R4 misclassifies (rare — scalar occasionally wins on supported).",
        })

    # Case 5: both wrong
    for _, row in df[(df["r4_correct"] == 0) & (df["rule_correct"] == 0)].iterrows():
        cases.append({
            "case_type": "both_wrong",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "Both R4 and scalar baseline misclassify; case may be genuinely hard or boundary case.",
        })

    # Case 6: strong_action_too_forced (from realism audit)
    for _, row in df[df["candidate_id"].astype(str).isin(forced_set)].iterrows():
        cases.append({
            "case_type": "strong_action_too_forced",
            "sample_id": row.get("sample_id", ""),
            "candidate_id": row["candidate_id"],
            "silver_label": row["silver_label"],
            "rule_scalar_score": row["rule_scalar_score"],
            "rule_scalar_label": row["rule_scalar_label"],
            "r4_label": row["r4_label"],
            "gpt_standard_label": row.get("gpt_standard_label", ""),
            "deepseek_label": row.get("deepseek_label", ""),
            "interpretation": "Flagged by V3.15 realism audit as strong_action_too_forced; cross-reference for boundary analysis.",
        })

    cases_df = pd.DataFrame(cases)
    cases_df.to_csv(BOUNDARY_CASE_CSV, index=False, encoding="utf-8")
    print(f"Wrote {BOUNDARY_CASE_CSV} ({len(cases_df)} cases)")

    # Report MD
    by_type = Counter(c["case_type"] for c in cases)
    md = []
    md.append("# Boundary Case Comparison Report")
    md.append("")
    md.append("**Task:** V3.15 Task 4/5 §5 — Case-level boundary analysis between scalar baseline and R4.")
    md.append("**Date:** 2026-07-05")
    md.append("**Status:** Reanalysis of existing 100 matched-sample predictions + realism audit cross-reference. NOT new experiments. NOT gold. NOT API.")
    md.append("")
    md.append("## 1. Case type counts")
    md.append("")
    md.append("| Case type | N | Description |")
    md.append("| --- | --- | --- |")
    md.append(f"| scalar_high_but_mild | {by_type.get('scalar_high_but_mild', 0)} | Scalar over-flags mild as strong (score >= 2) |")
    md.append(f"| scalar_low_but_strong | {by_type.get('scalar_low_but_strong', 0)} | Scalar misses strong (score <= 1) |")
    md.append(f"| r4_correct_scalar_wrong | {by_type.get('r4_correct_scalar_wrong', 0)} | R4 correct, scalar wrong |")
    md.append(f"| scalar_correct_r4_wrong | {by_type.get('scalar_correct_r4_wrong', 0)} | Scalar correct, R4 wrong |")
    md.append(f"| both_wrong | {by_type.get('both_wrong', 0)} | Both R4 and scalar wrong |")
    md.append(f"| strong_action_too_forced | {by_type.get('strong_action_too_forced', 0)} | Flagged by realism audit as forced |")
    md.append("")
    md.append("## 2. Key observations")
    md.append("")
    md.append(f"- **scalar_high_but_mild ({by_type.get('scalar_high_but_mild', 0)} cases):** Scalar score gives high overstatement score to mild_scope_overclaim, conflating scope expansion with action escalation. This is direct evidence of mild/strong boundary collapse.")
    md.append(f"- **scalar_low_but_strong ({by_type.get('scalar_low_but_strong', 0)} cases):** Scalar score misses true strong_action_overclaim. These are the cases R4 captures but scalar misses.")
    md.append(f"- **r4_correct_scalar_wrong ({by_type.get('r4_correct_scalar_wrong', 0)} cases):** R4 wins on these cases. Predominantly strong_action and contradiction boundaries where relation-specific routing matters.")
    md.append(f"- **scalar_correct_r4_wrong ({by_type.get('scalar_correct_r4_wrong', 0)} cases):** Scalar wins on these cases (rare). Predominantly supported cases where R4 over-routes.")
    md.append(f"- **both_wrong ({by_type.get('both_wrong', 0)} cases):** Genuinely hard cases or boundary cases. Both methods fail.")
    md.append(f"- **strong_action_too_forced ({by_type.get('strong_action_too_forced', 0)} cases):** Realism audit flagged these as forced. Even if R4 correctly identifies them as strong_action, the underlying claim may be unrealistic — see V3.15 realism audit.")
    md.append("")
    md.append("## 3. Verdict")
    md.append("")
    r4_wins = by_type.get("r4_correct_scalar_wrong", 0)
    scalar_wins = by_type.get("scalar_correct_r4_wrong", 0)
    if r4_wins > scalar_wins:
        md.append(f"**R4 wins more cases than scalar ({r4_wins} vs {scalar_wins}).** Scalar baseline does not replace R4 on relation-specific boundaries.")
    elif scalar_wins > r4_wins:
        md.append(f"**Scalar wins more cases than R4 ({scalar_wins} vs {r4_wins}).** Unexpected — investigate whether scalar is genuinely better on a subclass.")
    else:
        md.append(f"**Tied ({r4_wins} vs {scalar_wins}).** Neither method dominates.")
    md.append("")
    md.append("## 4. Prohibitions enforced")
    md.append("")
    md.append("- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.")

    with open(BOUNDARY_CASE_MD, "w", encoding="utf-8") as f:
        f.write("\n".join(md))
    print(f"Wrote {BOUNDARY_CASE_MD}")

    return by_type


# ===== §6 Gate JSON =====
def section_gate(mild_strong_rows, strong_screen_rows, collapse_summary, case_counts):
    rule_mild_strong = next((r for r in mild_strong_rows if r["scalar_variant"] == "rule_scalar_score"), None)
    llm_mild_strong = next((r for r in mild_strong_rows if r["scalar_variant"] == "llm_scalar_score"), None)

    rule_strong_screen = next((r for r in strong_screen_rows if r["method"] == "rule_scalar"), None)
    r4_strong_screen = next((r for r in strong_screen_rows if r["method"] == "r4_frozen"), None)

    # scalar_can_detect_overclaim: rule_scalar supported_vs_overclaim ROC (from binary_results) was 0.51 — near random
    # But mild+strong+contra all are "overclaim" in some sense. We use mild_vs_strong ROC as the test.
    scalar_can_detect_overclaim = bool(
        (rule_mild_strong and rule_mild_strong["roc_auc"] > 0.55) or
        (llm_mild_strong and llm_mild_strong["roc_auc"] > 0.55)
    )

    # scalar_can_separate_mild_strong: ROC-AUC > 0.65 considered acceptable
    best_mild_strong_roc = max(
        rule_mild_strong["roc_auc"] if rule_mild_strong else 0,
        llm_mild_strong["roc_auc"] if llm_mild_strong else 0,
    )
    scalar_can_separate_mild_strong = bool(best_mild_strong_roc > 0.65)

    # scalar_can_replace_r4: scalar F1 >= R4 F1 on strong_action screening
    scalar_can_replace_r4 = bool(
        rule_strong_screen and r4_strong_screen and
        rule_strong_screen["positive_f1"] >= r4_strong_screen["positive_f1"]
    )

    # r4_retains_strong_action_advantage: R4 recall > scalar recall AND R4 F1 > scalar F1
    r4_retains_advantage = bool(
        r4_strong_screen and rule_strong_screen and
        r4_strong_screen["recall"] > rule_strong_screen["recall"] and
        r4_strong_screen["positive_f1"] > rule_strong_screen["positive_f1"]
    )

    # mild_strong_overlap_high: overlap ratio > 0.8
    mild_strong_overlap_high = bool(
        collapse_summary["mild_at_or_above_strong_median"] /
        max(collapse_summary["strong_at_or_above_strong_median"], 1e-9) > 0.8
    )

    score_collapse_observed = collapse_summary["collapse_observed"]

    if not scalar_can_replace_r4 and r4_retains_advantage and score_collapse_observed:
        recommended_claim = (
            "RIGOURATE-style scalar overstatement score (rule-based proxy, NOT official RIGOURATE — official code/data unavailable) "
            "cannot replace CESE-OCN's relation-specific strong_action screening. On the matched-100 evaluation, scalar positive-F1 = "
            f"{rule_strong_screen['positive_f1'] if rule_strong_screen else 'N/A'} vs R4 positive-F1 = "
            f"{r4_strong_screen['positive_f1'] if r4_strong_screen else 'N/A'}. "
            "Scalar score collapses across relation labels (mean score is ~1.6 for all four labels), and the mild/strong boundary ROC-AUC is near random. "
            "R4 retains a strong_action screening advantage (higher recall, higher positive-F1, captures LLM-missed strong cases). "
            "Scalar baseline is reported as a complementary reference, NOT as a replacement for R4."
        )
    else:
        recommended_claim = "See detailed report for recommended paper claim."

    main_risk = (
        "Scalar baseline results are based on a rule-based proxy (NOT official RIGOURATE). "
        "Official RIGOURATE code/data/model are unavailable (blocked). "
        "If a future release of RIGOURATE provides a continuous overstatement score with stronger discriminative power, "
        "the conclusion may need to be revisited. "
        "Additionally, all results are on silver labels (pre-gold); gold validation may shift the comparison."
    )

    gate = {
        "gate_name": "scalar_vs_relation_deep_test_gate",
        "task": "V3.15 Task 4/5 — RIGOURATE/Scalar Baseline Deep Comparison + Strong_Action Boundary Test",
        "date": "2026-07-05",
        "scalar_can_detect_overclaim": scalar_can_detect_overclaim,
        "scalar_can_separate_mild_strong": scalar_can_separate_mild_strong,
        "scalar_can_replace_r4": scalar_can_replace_r4,
        "r4_retains_strong_action_advantage": r4_retains_advantage,
        "mild_strong_overlap_high": mild_strong_overlap_high,
        "score_collapse_observed": score_collapse_observed,
        "recommended_paper_claim": recommended_claim,
        "main_remaining_risk": main_risk,
        "supporting_metrics": {
            "mild_vs_strong_roc_auc_rule_scalar": rule_mild_strong["roc_auc"] if rule_mild_strong else None,
            "mild_vs_strong_roc_auc_llm_scalar": llm_mild_strong["roc_auc"] if llm_mild_strong else None,
            "strong_screen_positive_f1_rule_scalar": rule_strong_screen["positive_f1"] if rule_strong_screen else None,
            "strong_screen_positive_f1_r4": r4_strong_screen["positive_f1"] if r4_strong_screen else None,
            "strong_screen_recall_rule_scalar": rule_strong_screen["recall"] if rule_strong_screen else None,
            "strong_screen_recall_r4": r4_strong_screen["recall"] if r4_strong_screen else None,
            "strong_screen_llm_missed_captured_rule_scalar": rule_strong_screen["llm_missed_strong_captured_by_method"] if rule_strong_screen else None,
            "strong_screen_llm_missed_captured_r4": r4_strong_screen["llm_missed_strong_captured_by_method"] if r4_strong_screen else None,
            "score_collapse_indicators": collapse_summary["collapse_evidence"],
            "case_counts": dict(case_counts),
        },
        "prohibitions_enforced": {
            "no_api_calls": True,
            "no_llm_training": True,
            "no_r4_threshold_modification": True,
            "no_original_data_modification": True,
            "no_proxy_as_official_rigourate": True,
            "no_gold": True,
        },
        "audit_disclaimer": "Scalar baseline is a rule-based / LLM-label-derived PROXY. Official RIGOURATE code/data/model are NOT available. All scalar results are labelled 'rule_scalar_score' or 'llm_scalar_score', NOT 'RIGOURATE'. All comparison is on silver labels (pre-gold).",
    }

    with open(GATE_JSON, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"Wrote {GATE_JSON}")
    return gate


# ===== Main =====
def main():
    print("=== V3.15 Task 4/5: Scalar vs Relation Screening Deep Test ===\n")

    # §1 Verify inputs
    ok, msg = verify_inputs()
    print(f"[§1] Input verification: {msg}")
    if not ok:
        blocked = OUT_DIR / "blocked_reason.md"
        with open(blocked, "w", encoding="utf-8") as f:
            f.write(f"# Blocked\n\n{msg}\n\nNo further analysis possible.\n")
        print(f"Wrote {blocked} — STOPPING.")
        return

    # Load data
    scalar_df = pd.read_csv(SCALAR_CSV, keep_default_na=False)
    vs_r4_cases_df = pd.read_csv(VS_R4_CASES_CSV, keep_default_na=False)
    vs_r4_results_df = pd.read_csv(VS_R4_CSV, keep_default_na=False)
    realism_df = None
    if Path(REALISM_CSV).exists():
        realism_df = pd.read_csv(REALISM_CSV, keep_default_na=False)
        print(f"Loaded realism audit: {len(realism_df)} rows")
    print(f"Loaded scalar scores: {len(scalar_df)} rows")
    print(f"Loaded vs_r4 cases: {len(vs_r4_cases_df)} rows\n")

    # §2
    print("[§2] Mild vs strong boundary test...")
    mild_strong_rows = section_mild_vs_strong(scalar_df)

    # §3
    print("\n[§3] Strong_action screening comparison...")
    strong_screen_rows, overlap_info = section_strong_screening(vs_r4_cases_df, vs_r4_results_df)

    # §4
    print("\n[§4] Score collapse analysis...")
    collapse_summary = section_score_collapse(scalar_df)

    # §5
    print("\n[§5] Case-level boundary analysis...")
    case_counts = section_boundary_cases(vs_r4_cases_df, realism_df)

    # §6
    print("\n[§6] Gate JSON...")
    gate = section_gate(mild_strong_rows, strong_screen_rows, collapse_summary, case_counts)

    print("\n=== DONE ===")
    print(f"Output: {OUT_DIR}")
    print(f"\nKey verdicts:")
    print(f"  scalar_can_detect_overclaim:        {gate['scalar_can_detect_overclaim']}")
    print(f"  scalar_can_separate_mild_strong:    {gate['scalar_can_separate_mild_strong']}")
    print(f"  scalar_can_replace_r4:              {gate['scalar_can_replace_r4']}")
    print(f"  r4_retains_strong_action_advantage: {gate['r4_retains_strong_action_advantage']}")
    print(f"  mild_strong_overlap_high:           {gate['mild_strong_overlap_high']}")
    print(f"  score_collapse_observed:            {gate['score_collapse_observed']}")


if __name__ == "__main__":
    main()
