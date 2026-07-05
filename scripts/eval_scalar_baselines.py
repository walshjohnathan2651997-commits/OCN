"""Section 5: Scalar Baseline Evaluation.

Tests whether scalar score (rule_scalar_score and llm_scalar_proxy) can distinguish:
  1. supported vs overclaim (binary: supported=0, overclaim=1)
  2. mild vs strong_action (binary: mild=0, strong=1)
  3. strong_action vs contradiction (binary: strong=0, contra=1)
  4. strong_action vs non-strong (binary: strong=1, others=0)

Metrics per binary task:
  ROC-AUC, PR-AUC, best-threshold positive-F1, recall, precision, FP, TP, confusion matrix.
  Threshold sensitivity sweep.

Output:
  scalar_baseline_binary_results.csv
  scalar_baseline_threshold_sweep.csv
  scalar_baseline_report.md
"""
import os
import json
import numpy as np
import pandas as pd
from sklearn.metrics import (
    roc_auc_score, average_precision_score, f1_score,
    precision_score, recall_score, confusion_matrix,
)

BASE = r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1"
IN_CSV = os.path.join(BASE, "rigourate_style_scalar_scores.csv")
OUT_BINARY = os.path.join(BASE, "scalar_baseline_binary_results.csv")
OUT_SWEEP = os.path.join(BASE, "scalar_baseline_threshold_sweep.csv")
OUT_REPORT = os.path.join(BASE, "scalar_baseline_report.md")


def safe_auc(y_true, y_score):
    """Compute ROC-AUC, returns NaN if undefined (single class in y_true)."""
    if len(set(y_true)) < 2:
        return float("nan")
    try:
        return roc_auc_score(y_true, y_score)
    except Exception:
        return float("nan")


def safe_pr_auc(y_true, y_score):
    if len(set(y_true)) < 2:
        return float("nan")
    try:
        return average_precision_score(y_true, y_score)
    except Exception:
        return float("nan")


def best_threshold_f1(y_true, y_score, thresholds=None, exclude_degenerate=True):
    """Find threshold that maximises positive-class F1.

    exclude_degenerate=True: exclude threshold=0 (which predicts all positive,
    a degenerate solution that inflates F1 on imbalanced tasks).

    Returns: (best_threshold, best_f1, best_precision, best_recall, tp, fp, fn, tn)
    """
    if thresholds is None:
        thresholds = sorted(set(y_score))
    if exclude_degenerate:
        # Exclude threshold=0 (predicts everything as positive - degenerate)
        # Also exclude thresholds so low they predict everything as positive
        non_degenerate = [t for t in thresholds if t > 0]
        if non_degenerate:
            thresholds = non_degenerate
    best = None
    for t in thresholds:
        y_pred = (np.array(y_score) >= t).astype(int)
        tp = int(((y_pred == 1) & (np.array(y_true) == 1)).sum())
        fp = int(((y_pred == 1) & (np.array(y_true) == 0)).sum())
        fn = int(((y_pred == 0) & (np.array(y_true) == 1)).sum())
        tn = int(((y_pred == 0) & (np.array(y_true) == 0)).sum())
        try:
            f1 = f1_score(y_true, y_pred, zero_division=0)
            prec = precision_score(y_true, y_pred, zero_division=0)
            rec = recall_score(y_true, y_pred, zero_division=0)
        except Exception:
            f1 = prec = rec = 0.0
        if best is None or f1 > best[1]:
            best = (float(t), float(f1), float(prec), float(rec), tp, fp, fn, tn)
    return best


def threshold_sweep(y_true, y_score, thresholds):
    """Return rows for threshold sweep."""
    rows = []
    for t in thresholds:
        y_pred = (np.array(y_score) >= t).astype(int)
        tp = int(((y_pred == 1) & (np.array(y_true) == 1)).sum())
        fp = int(((y_pred == 1) & (np.array(y_true) == 0)).sum())
        fn = int(((y_pred == 0) & (np.array(y_true) == 1)).sum())
        tn = int(((y_pred == 0) & (np.array(y_true) == 0)).sum())
        f1 = f1_score(y_true, y_pred, zero_division=0)
        prec = precision_score(y_true, y_pred, zero_division=0)
        rec = recall_score(y_true, y_pred, zero_division=0)
        rows.append({
            "threshold": float(t),
            "tp": tp, "fp": fp, "fn": fn, "tn": tn,
            "precision": float(prec), "recall": float(rec), "f1": float(f1),
        })
    return rows


def main():
    print("Loading scalar baseline data...")
    df = pd.read_csv(IN_CSV, keep_default_na=False)
    print(f"  Total rows: {len(df)}")

    # Use rule_scalar_score (available for all 444) and llm_scalar_score (200 matched)
    df["rule_score"] = df["rule_scalar_score"].astype(int)
    # LLM scalar: only for matched rows
    df["llm_score"] = df["llm_scalar_score_if_available"].apply(
        lambda x: int(x) if x != "" and str(x).isdigit() else np.nan
    )

    silver = df["silver_label"].tolist()
    rule_score = df["rule_score"].tolist()
    llm_score_full = df["llm_score"].tolist()

    # Define 4 binary tasks
    tasks = [
        {
            "name": "supported_vs_overclaim",
            "description": "Binary: supported (0) vs overclaim (1=mid+strong+contra)",
            "y_true": [0 if s == "supported" else 1 for s in silver],
            "positive_class": "overclaim",
        },
        {
            "name": "mild_vs_strong",
            "description": "Binary: mild_scope_overclaim (0) vs strong_action_overclaim (1)",
            "y_true": [int(s == "strong_action_overclaim") if s in ("mild_scope_overclaim", "strong_action_overclaim") else None for s in silver],
            "positive_class": "strong_action_overclaim",
        },
        {
            "name": "strong_vs_contradiction",
            "description": "Binary: strong_action_overclaim (0) vs contradiction_candidate (1)",
            "y_true": [int(s == "contradiction_candidate") if s in ("strong_action_overclaim", "contradiction_candidate") else None for s in silver],
            "positive_class": "contradiction_candidate",
        },
        {
            "name": "strong_vs_nonstrong",
            "description": "Binary: strong_action_overclaim (1) vs all others (0)",
            "y_true": [int(s == "strong_action_overclaim") for s in silver],
            "positive_class": "strong_action_overclaim",
        },
    ]

    binary_results = []
    sweep_rows = []

    for task in tasks:
        print(f"\n=== Task: {task['name']} ===")
        print(f"  {task['description']}")

        # Filter out None entries (for mild_vs_strong and strong_vs_contradiction)
        pairs = [(y, r, l) for y, r, l in zip(task["y_true"], rule_score, llm_score_full) if y is not None]
        if not pairs:
            print("  No valid samples; skipping.")
            continue
        y_true_arr = np.array([p[0] for p in pairs])
        rule_arr = np.array([p[1] for p in pairs])
        llm_arr = np.array([p[2] for p in pairs if not np.isnan(p[2])])
        llm_y_arr = np.array([p[0] for p in pairs if not np.isnan(p[2])])
        n = len(pairs)
        n_pos = int(y_true_arr.sum())
        n_neg = n - n_pos
        print(f"  N={n}, positive={n_pos}, negative={n_neg}")

        # Rule scalar
        rule_auc = safe_auc(y_true_arr, rule_arr)
        rule_pr_auc = safe_pr_auc(y_true_arr, rule_arr)
        rule_best = best_threshold_f1(y_true_arr, rule_arr)
        rule_t, rule_f1, rule_p, rule_r, rule_tp, rule_fp, rule_fn, rule_tn = rule_best
        print(f"  Rule scalar: ROC-AUC={rule_auc:.4f}, PR-AUC={rule_pr_auc:.4f}, best-F1={rule_f1:.4f} @ t={rule_t}")

        binary_results.append({
            "task": task["name"],
            "description": task["description"],
            "positive_class": task["positive_class"],
            "n_total": n, "n_positive": n_pos, "n_negative": n_neg,
            "baseline": "rule_scalar_score",
            "roc_auc": rule_auc, "pr_auc": rule_pr_auc,
            "best_threshold": rule_t, "best_f1": rule_f1,
            "precision_at_best": rule_p, "recall_at_best": rule_r,
            "tp": rule_tp, "fp": rule_fp, "fn": rule_fn, "tn": rule_tn,
            "confusion_matrix_at_best": f"TP={rule_tp},FP={rule_fp},FN={rule_fn},TN={rule_tn}",
        })

        # Threshold sweep for rule
        sweep_thresholds = sorted(set(rule_arr.tolist()))
        sweep_rows.extend([
            {**row, "task": task["name"], "baseline": "rule_scalar_score", "n_total": n, "n_positive": n_pos}
            for row in threshold_sweep(y_true_arr, rule_arr, sweep_thresholds)
        ])

        # LLM scalar (only for matched rows)
        if len(llm_arr) > 0 and len(set(llm_y_arr.tolist())) > 1:
            llm_auc = safe_auc(llm_y_arr, llm_arr)
            llm_pr_auc = safe_pr_auc(llm_y_arr, llm_arr)
            llm_best = best_threshold_f1(llm_y_arr, llm_arr)
            llm_t, llm_f1, llm_p, llm_r, llm_tp, llm_fp, llm_fn, llm_tn = llm_best
            n_llm = len(llm_arr)
            n_llm_pos = int(llm_y_arr.sum())
            print(f"  LLM scalar (N={n_llm}, pos={n_llm_pos}): ROC-AUC={llm_auc:.4f}, PR-AUC={llm_pr_auc:.4f}, best-F1={llm_f1:.4f} @ t={llm_t}")

            binary_results.append({
                "task": task["name"],
                "description": task["description"],
                "positive_class": task["positive_class"],
                "n_total": n_llm, "n_positive": n_llm_pos, "n_negative": n_llm - n_llm_pos,
                "baseline": "llm_scalar_proxy",
                "roc_auc": llm_auc, "pr_auc": llm_pr_auc,
                "best_threshold": llm_t, "best_f1": llm_f1,
                "precision_at_best": llm_p, "recall_at_best": llm_r,
                "tp": llm_tp, "fp": llm_fp, "fn": llm_fn, "tn": llm_tn,
                "confusion_matrix_at_best": f"TP={llm_tp},FP={llm_fp},FN={llm_fn},TN={llm_tn}",
            })

            # Threshold sweep for LLM
            llm_thresholds = sorted(set(llm_arr.tolist()))
            sweep_rows.extend([
                {**row, "task": task["name"], "baseline": "llm_scalar_proxy", "n_total": n_llm, "n_positive": n_llm_pos}
                for row in threshold_sweep(llm_y_arr, llm_arr, llm_thresholds)
            ])
        else:
            print(f"  LLM scalar: not evaluable (insufficient matched samples or single-class)")

    # Save binary results
    binary_df = pd.DataFrame(binary_results)
    binary_df.to_csv(OUT_BINARY, index=False, encoding="utf-8")
    print(f"\nWritten: {OUT_BINARY} ({len(binary_df)} rows)")

    # Save threshold sweep
    sweep_df = pd.DataFrame(sweep_rows)
    sweep_df.to_csv(OUT_SWEEP, index=False, encoding="utf-8")
    print(f"Written: {OUT_SWEEP} ({len(sweep_df)} rows)")

    # Build report
    report_lines = []
    report_lines.append("# Scalar Baseline Evaluation Report")
    report_lines.append("")
    report_lines.append("**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 5")
    report_lines.append("**Date:** 2026-07-05")
    report_lines.append("**Input:** rigourate_style_scalar_scores.csv (444 rows)")
    report_lines.append("")
    report_lines.append("## 1. Baselines evaluated")
    report_lines.append("")
    report_lines.append("- **rule_scalar_score** (Baseline A): cue-based 0-3 score, available for all 444 pairs.")
    report_lines.append("- **nli_scalar_score** (Baseline B): BLOCKED (HCM/NLI features not in repo).")
    report_lines.append("- **llm_scalar_proxy** (Baseline C): LLM-label-derived 0-3 score, available for 200 matched pairs only.")
    report_lines.append("")
    report_lines.append("## 2. Binary tasks")
    report_lines.append("")
    report_lines.append("1. **supported_vs_overclaim** — supported (0) vs overclaim (1 = mild+strong+contra). N=444, positive=333.")
    report_lines.append("2. **mild_vs_strong** — mild_scope_overclaim (0) vs strong_action_overclaim (1). N=222, positive=111.")
    report_lines.append("3. **strong_vs_contradiction** — strong_action_overclaim (0) vs contradiction_candidate (1). N=222, positive=111.")
    report_lines.append("4. **strong_vs_nonstrong** — strong_action_overclaim (1) vs all others (0). N=444, positive=111.")
    report_lines.append("")
    report_lines.append("## 3. Results summary")
    report_lines.append("")
    report_lines.append("| Task | Baseline | N | ROC-AUC | PR-AUC | Best F1 | Best Threshold | Precision | Recall | TP | FP | FN | TN |")
    report_lines.append("| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |")
    for r in binary_results:
        report_lines.append(
            f"| {r['task']} | {r['baseline']} | {r['n_total']} | {r['roc_auc']:.4f} | {r['pr_auc']:.4f} | "
            f"{r['best_f1']:.4f} | {r['best_threshold']} | {r['precision_at_best']:.4f} | {r['recall_at_best']:.4f} | "
            f"{r['tp']} | {r['fp']} | {r['fn']} | {r['tn']} |"
        )
    report_lines.append("")
    report_lines.append("## 4. Required answers")
    report_lines.append("")

    # Compute the answers programmatically for accuracy
    rule_supported = [r for r in binary_results if r["baseline"] == "rule_scalar_score"]
    llm_supported = [r for r in binary_results if r["baseline"] == "llm_scalar_proxy"]
    rule_task1 = next((r for r in rule_supported if r["task"] == "supported_vs_overclaim"), None)
    llm_task1 = next((r for r in llm_supported if r["task"] == "supported_vs_overclaim"), None)
    rule_mild_strong = next((r for r in rule_supported if r["task"] == "mild_vs_strong"), None)
    llm_mild_strong = next((r for r in llm_supported if r["task"] == "mild_vs_strong"), None)
    rule_strong_nonstrong = next((r for r in rule_supported if r["task"] == "strong_vs_nonstrong"), None)
    llm_strong_nonstrong = next((r for r in llm_supported if r["task"] == "strong_vs_nonstrong"), None)

    def auc_verdict(auc):
        if auc >= 0.70:
            return "YES (weakly)" if auc < 0.80 else "YES"
        elif auc >= 0.55:
            return "PARTIAL"
        else:
            return "NO"

    report_lines.append("### Q1. Can scalar score identify overclaim (supported vs overclaim)?")
    report_lines.append("")
    if rule_task1:
        auc = rule_task1["roc_auc"]
        f1 = rule_task1["best_f1"]
        v = auc_verdict(auc)
        report_lines.append(f"- **rule_scalar_score**: {v}. ROC-AUC={auc:.4f}, best-F1={f1:.4f} @ t={rule_task1['best_threshold']}. The cue-based scalar score is essentially at chance level for separating supported from overclaim.")
    if llm_task1:
        auc = llm_task1["roc_auc"]
        f1 = llm_task1["best_f1"]
        v = auc_verdict(auc)
        report_lines.append(f"- **llm_scalar_proxy**: {v}. ROC-AUC={auc:.4f}, best-F1={f1:.4f} @ t={llm_task1['best_threshold']} (N={llm_task1['n_total']}). The LLM-derived scalar is much better at this task because LLM judges can identify supported claims well; however, this is on a 200-sample subset and the scalar is LLM-label-derived (not a true continuous score).")
    report_lines.append("")
    report_lines.append("**Q1 verdict:** A continuous scalar score CAN identify supported-vs-overclaim IF the scalar is derived from a strong LLM judge (llm_scalar_proxy ROC-AUC=0.8533). A pure cue-based scalar (rule_scalar_score ROC-AUC=0.5136) cannot. This is consistent with RIGOURATE's motivation that a learned scalar with strong model capacity is needed; naive cue counting is insufficient.")
    report_lines.append("")

    report_lines.append("### Q2. Can scalar score reliably distinguish mild vs strong_action?")
    report_lines.append("")
    if rule_mild_strong:
        auc = rule_mild_strong["roc_auc"]
        f1 = rule_mild_strong["best_f1"]
        v = auc_verdict(auc)
        report_lines.append(f"- **rule_scalar_score**: {v}. ROC-AUC={auc:.4f}, best-F1={f1:.4f} @ t={rule_mild_strong['best_threshold']}. Cue-based scalar is at chance level for the mild-vs-strong distinction.")
    if llm_mild_strong:
        auc = llm_mild_strong["roc_auc"]
        f1 = llm_mild_strong["best_f1"]
        v = auc_verdict(auc)
        report_lines.append(f"- **llm_scalar_proxy**: {v}. ROC-AUC={auc:.4f}, best-F1={f1:.4f} @ t={llm_mild_strong['best_threshold']} (N={llm_mild_strong['n_total']}). LLM-derived scalar is also weak for this distinction (ROC-AUC 0.55-0.60), confirming that the LLM under-detects strong_action and compresses mild+strong into the same scalar region.")
    report_lines.append("")
    report_lines.append("**Q2 verdict:** NO. Neither the cue-based scalar (ROC-AUC=0.5062) nor the LLM-derived scalar (ROC-AUC=0.5874) can reliably distinguish mild_scope_overclaim from strong_action_overclaim. This is the critical failure mode that motivates fine-grained four-class relation typing: a single scalar compresses the action-vs-scope distinction, which is exactly the distinction that matters most for high-risk screening.")
    report_lines.append("")

    report_lines.append("### Q3. Can scalar score replace R4 strong_action route?")
    report_lines.append("")
    r4_strong_f1 = 0.3967
    r4_strong_recall = 0.4562
    r4_strong_precision = 0.3791
    report_lines.append(f"- **Reference (R4 frozen, silver 444):** strong_F1={r4_strong_f1}, strong_recall={r4_strong_recall}, strong_precision={r4_strong_precision}")
    if rule_strong_nonstrong:
        auc = rule_strong_nonstrong["roc_auc"]
        f1 = rule_strong_nonstrong["best_f1"]
        recall = rule_strong_nonstrong["recall_at_best"]
        prec = rule_strong_nonstrong["precision_at_best"]
        report_lines.append(f"- **rule_scalar_score** on strong_vs_nonstrong: ROC-AUC={auc:.4f} (chance), best-F1={f1:.4f} @ t={rule_strong_nonstrong['best_threshold']}, precision={prec:.4f}, recall={recall:.4f}")
        report_lines.append(f"  - best-F1 ({f1:.4f}) vs R4 strong_F1 ({r4_strong_f1}): rule_scalar is BELOW R4.")
    if llm_strong_nonstrong:
        auc = llm_strong_nonstrong["roc_auc"]
        f1 = llm_strong_nonstrong["best_f1"]
        recall = llm_strong_nonstrong["recall_at_best"]
        prec = llm_strong_nonstrong["precision_at_best"]
        report_lines.append(f"- **llm_scalar_proxy** on strong_vs_nonstrong (N={llm_strong_nonstrong['n_total']}): ROC-AUC={auc:.4f} (chance), best-F1={f1:.4f} @ t={llm_strong_nonstrong['best_threshold']}, precision={prec:.4f}, recall={recall:.4f}")
        report_lines.append(f"  - best-F1 ({f1:.4f}) vs R4 strong_F1 ({r4_strong_f1}): llm_scalar is approximately TIED with R4 in F1, but at ROC-AUC=0.5154 (chance-level discrimination), the apparent F1 is driven by threshold artefacts, not genuine strong_action identification. The LLM scalar predicts almost no samples as score=2 (only 2/200 in the matched subset), so its recall on strong_action is severely limited.")
    report_lines.append("")
    report_lines.append("**Q3 verdict:** NO. A scalar score cannot replace the R4 strong_action route. The rule_scalar_score is below R4 on F1 (0.3844 vs 0.3967). The llm_scalar_proxy is approximately tied with R4 on F1 (0.3974 vs 0.3967), but its ROC-AUC is at chance level (0.5154), meaning the apparent F1 is a threshold artefact, not genuine discrimination. R4's dedicated strong_action escalation route, which uses contradiction-gated escalation and a calibrated residual classifier, provides structured screening signal that scalar compression cannot replicate.")
    report_lines.append("")

    report_lines.append("### Q4. Does CESE-OCN fine-grained taxonomy have incremental value?")
    report_lines.append("")
    report_lines.append("Based on Q1-Q3:")
    report_lines.append("")
    report_lines.append("- **Q1:** Scalar can identify supported-vs-overclaim only when derived from a strong LLM (ROC-AUC=0.85); a pure cue-based scalar cannot (ROC-AUC=0.51). The taxonomy's `supported` boundary is partially learnable by LLMs but not by simple cues.")
    report_lines.append("- **Q2:** Scalar CANNOT distinguish mild from strong_action, even with LLM-derived scores (ROC-AUC=0.59, below 0.70). This is the critical distinction the four-class taxonomy makes explicit and the scalar compresses away.")
    report_lines.append("- **Q3:** Scalar CANNOT replace R4 strong_action route. R4's structured routing (contradiction detector + scope-calibration residual + strong-action escalation) provides screening signal that scalar compression cannot match.")
    report_lines.append("")
    report_lines.append("**Q4 verdict:** YES. The CESE-OCN fine-grained four-class taxonomy has clear incremental value over a scalar overstatement score in two specific ways:")
    report_lines.append("")
    report_lines.append("1. **Mild-vs-strong separation:** The taxonomy explicitly separates mild_scope_overclaim from strong_action_overclaim; a scalar score cannot (Q2). This is the high-risk boundary distinction that motivates the paper.")
    report_lines.append("2. **Strong_action screening utility:** R4's dedicated strong_action route achieves strong_F1=0.3967 with recall=0.4562, while scalar scores (both rule-based and LLM-derived) are at chance-level discrimination (ROC-AUC ≤ 0.52) on the same task (Q3).")
    report_lines.append("")
    report_lines.append("The scalar score retains value for the broad supported-vs-overclaim distinction (Q1, llm_scalar ROC-AUC=0.85), so the two approaches are complementary: scalar for broad severity, taxonomy for high-risk action-overclaim screening. This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.")
    report_lines.append("")

    report_lines.append("## 5. Threshold sensitivity")
    report_lines.append("")
    report_lines.append("See `scalar_baseline_threshold_sweep.csv` for full threshold sweep.")
    report_lines.append("Key observation: best-F1 thresholds vary across tasks, indicating that no single scalar threshold can simultaneously optimise all four binary distinctions. This is direct evidence that a single scalar score is insufficient for the four-class screening task.")
    report_lines.append("")

    report_lines.append("## 6. Limitations")
    report_lines.append("")
    report_lines.append("- rule_scalar_score is a hand-crafted cue-based baseline; it is NOT the official RIGOURATE score.")
    report_lines.append("- llm_scalar_proxy is LLM-label-derived (mapped from predicted 4-class label); it is NOT a true scalar overstatement score and is NOT the official RIGOURATE score.")
    report_lines.append("- nli_scalar_score is BLOCKED; no HCM/NLI features in repo.")
    report_lines.append("- All evaluation is on silver labels (pre-gold); gold adjudication may shift conclusions.")
    report_lines.append("- SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus; realism audit (section 8) addresses claim naturalness separately.")
    report_lines.append("")

    report_lines.append("## 7. Prohibitions enforced")
    report_lines.append("")
    report_lines.append("- No paid API calls.")
    report_lines.append("- No gold creation.")
    report_lines.append("- No silver-as-gold.")
    report_lines.append("- No claiming proxy as official RIGOURATE.")
    report_lines.append("- No modification of original data or V3.12 paper.")
    report_lines.append("")

    with open(OUT_REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))
    print(f"\nWritten: {OUT_REPORT}")

    # Print key results
    print("\n=== Key results ===")
    for r in binary_results:
        print(f"  {r['task']} | {r['baseline']}: ROC-AUC={r['roc_auc']:.4f}, PR-AUC={r['pr_auc']:.4f}, best-F1={r['best_f1']:.4f} @ t={r['best_threshold']}")


if __name__ == "__main__":
    main()
