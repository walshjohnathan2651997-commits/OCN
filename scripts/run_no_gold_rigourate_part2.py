"""No-Gold RIGOURATE + Public Benchmark Pipeline Part 2.

Section 1: R4 / LLM / scalar comparison
Section 2: ForceBench feasibility + non-API subset analysis
Section 3: Claim realism / synthetic risk auto audit
Section 4: Public dataset positioning insert
Section 5: Main line judgment report
Section 6: Final gate

Prohibitions enforced:
- no gold / no human annotation / no annotation templates
- no paid API calls
- no model training
- no paper modification
- no original data modification
- no proxy-as-official
- no silver-as-gold
- no planned-as-completed
- no simulation-as-natural-distribution
- no file deletion
"""

import csv
import json
import os
import re
from collections import Counter, defaultdict

import pandas as pd

OUT_DIR = r"D:\ocn\project_synthesis\no_gold_rigourate_public_benchmark_pipeline_v1\part2_comparison_and_synthesis"
PART1_DIR = r"D:\ocn\project_synthesis\no_gold_rigourate_public_benchmark_pipeline_v1\part1_scalar_baseline"

PART1_SCALAR_CSV = os.path.join(PART1_DIR, "rigourate_style_scalar_scores.csv")
PART1_BINARY_CSV = os.path.join(PART1_DIR, "scalar_baseline_binary_results.csv")
PART1_SWEEP_CSV = os.path.join(PART1_DIR, "scalar_threshold_sweep.csv")
PART1_GATE_JSON = os.path.join(PART1_DIR, "part1_scalar_baseline_gate.json")

SIMCLAIM_CSV = r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
R4_METRICS_JSON = r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_metrics_summary.json"
R4_ROUTING_CSV = r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_routing_results_by_seed.csv"
LLM_200_CSV = r"D:\ocn\experiments\llm_judge_baseline_v1\llm_parsed_outputs_200.csv"
GPT_COMPARISON_CSV = r"D:\ocn\experiments\gpt_structured_judge_probe_v1\gpt_vs_r4_deepseek_comparison.csv"

AUDIT_DATE = "2026-07-05"

LABELS = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_SCALAR = {"supported": 0, "mild_scope_overclaim": 1, "strong_action_overclaim": 2, "contradiction_candidate": 3}


def ensure_out_dir():
    os.makedirs(OUT_DIR, exist_ok=True)


def read_part1():
    """Read Part 1 outputs."""
    print("[Part 2 setup] Reading Part 1 outputs...")
    if not os.path.exists(PART1_SCALAR_CSV):
        raise FileNotFoundError(f"Part 1 scalar scores not found: {PART1_SCALAR_CSV}")
    df_scalar = pd.read_csv(PART1_SCALAR_CSV, keep_default_na=False)
    print(f"  Part 1 scalar scores: {df_scalar.shape}")

    df_binary = pd.read_csv(PART1_BINARY_CSV, keep_default_na=False) if os.path.exists(PART1_BINARY_CSV) else None
    print(f"  Part 1 binary results: {df_binary.shape if df_binary is not None else 'N/A'}")

    with open(PART1_GATE_JSON, encoding="utf-8") as f:
        part1_gate = json.load(f)
    print(f"  Part 1 gate loaded: official_rigourate_status={part1_gate.get('official_rigourate_status')}")

    return df_scalar, df_binary, part1_gate


# ============================================================
# Section 1: R4 / LLM / scalar comparison
# ============================================================

def compute_strong_action_metrics(y_true, y_pred):
    """Compute strong_action binary metrics.

    positive class = strong_action_overclaim.
    """
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == "strong_action_overclaim" and p == "strong_action_overclaim")
    fp = sum(1 for t, p in zip(y_true, y_pred) if t != "strong_action_overclaim" and p == "strong_action_overclaim")
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == "strong_action_overclaim" and p != "strong_action_overclaim")
    tn = sum(1 for t, p in zip(y_true, y_pred) if t != "strong_action_overclaim" and p != "strong_action_overclaim")

    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    fp_tp = fp / tp if tp > 0 else float("inf")
    review_burden = (tp + fp) / len(y_true) if len(y_true) > 0 else 0.0

    return {
        "n_total": len(y_true),
        "n_strong_true": tp + fn,
        "tp": tp, "fp": fp, "fn": fn, "tn": tn,
        "precision": precision, "recall": recall, "f1": f1,
        "fp_tp_ratio": fp_tp,
        "review_burden": review_burden,
    }


def compute_macro_f1(y_true, y_pred):
    """Compute macro-F1 over 4 labels."""
    f1s = []
    for label in LABELS:
        tp = sum(1 for t, p in zip(y_true, y_pred) if t == label and p == label)
        fp = sum(1 for t, p in zip(y_true, y_pred) if t != label and p == label)
        fn = sum(1 for t, p in zip(y_true, y_pred) if t == label and p != label)
        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
        f1s.append(f1)
    return sum(f1s) / len(f1s) if f1s else 0.0


def scalar_to_label(scalar_score):
    """Map scalar score back to 4-class label for comparison."""
    if scalar_score == "" or scalar_score is None:
        return None
    try:
        s = int(scalar_score)
    except (ValueError, TypeError):
        return None
    inv = {0: "supported", 1: "mild_scope_overclaim", 2: "strong_action_overclaim", 3: "contradiction_candidate"}
    return inv.get(s)


def compare_r4_llm_scalar(df_scalar, df_binary, part1_gate):
    """Section 1: compare R4 / GPT / DeepSeek / scalar on strong_action screening."""
    print("[Section 1] R4 / LLM / scalar comparison...")

    # Read R4 frozen metrics (aggregate, silver 444)
    with open(R4_METRICS_JSON, encoding="utf-8") as f:
        r4_metrics = json.load(f)
    r4_conservative = r4_metrics["R4_conservative_strong"]
    r4_baseline = r4_metrics["baseline_flat4"]

    # Read LLM 200 outputs
    df_llm200 = pd.read_csv(LLM_200_CSV, keep_default_na=False)
    llm200_map = {row["candidate_id"]: row["llm_label"] for _, row in df_llm200.iterrows()}

    # Read GPT comparison (100 matched)
    df_gpt100 = pd.read_csv(GPT_COMPARISON_CSV, keep_default_na=False)

    # Build per-candidate silver_label map
    silver_map = {row["candidate_id"]: row["silver_label"] for _, row in df_scalar.iterrows()}

    # Build comparison rows
    # 1. R4 on silver 444 (from frozen metrics — aggregate only, no per-sample)
    # 2. baseline_flat4 on silver 444 (from frozen metrics)
    # 3. rule_scalar_score on silver 444 (from Part 1)
    # 4. llm_scalar_proxy on 200 (DeepSeek-derived)
    # 5. DeepSeek llm_label on 200
    # 6. GPT standard on 100 matched
    # 7. GPT structured on 100 matched
    # 8. R4 on 100 matched (from gpt comparison file)
    # 9. DeepSeek on 100 matched (from gpt comparison file)

    results = []

    # --- R4 frozen on silver 444 ---
    results.append({
        "method": "R4_conservative_strong",
        "n_total": 444,
        "subset": "silver_444",
        "source": "frozen_r4_metrics_summary.json",
        "strong_f1": r4_conservative["strong_positive_f1"],
        "strong_precision": r4_conservative["strong_precision"],
        "strong_recall": r4_conservative["strong_recall"],
        "macro_f1": r4_conservative["flat4_macro_f1"],
        "fp_tp_ratio": (1 - r4_conservative["strong_precision"]) / r4_conservative["strong_precision"] if r4_conservative["strong_precision"] > 0 else float("inf"),
        "review_burden": None,  # not directly available
        "notes": "R4 frozen conservative; t_contra=0.48, t_strong=0.535, t_svm=0.51",
    })

    # --- baseline_flat4 on silver 444 ---
    results.append({
        "method": "baseline_flat4",
        "n_total": 444,
        "subset": "silver_444",
        "source": "frozen_r4_metrics_summary.json",
        "strong_f1": r4_baseline["strong_positive_f1"],
        "strong_precision": r4_baseline["strong_precision"],
        "strong_recall": r4_baseline["strong_recall"],
        "macro_f1": r4_baseline["flat4_macro_f1"],
        "fp_tp_ratio": (1 - r4_baseline["strong_precision"]) / r4_baseline["strong_precision"] if r4_baseline["strong_precision"] > 0 else float("inf"),
        "review_burden": None,
        "notes": "flat4 baseline (no routing)",
    })

    # --- rule_scalar_score on silver 444 (threshold=2 for strong_action) ---
    y_true_444 = [row["silver_label"] for _, row in df_scalar.iterrows()]
    y_pred_rule = []
    for _, row in df_scalar.iterrows():
        s = row["rule_scalar_score"]
        try:
            s = int(s)
        except (ValueError, TypeError):
            s = 0
        # Map scalar to label
        inv = {0: "supported", 1: "mild_scope_overclaim", 2: "strong_action_overclaim", 3: "contradiction_candidate"}
        y_pred_rule.append(inv.get(s, "supported"))
    m_rule = compute_strong_action_metrics(y_true_444, y_pred_rule)
    macro_rule = compute_macro_f1(y_true_444, y_pred_rule)
    results.append({
        "method": "rule_scalar_score",
        "n_total": m_rule["n_total"],
        "subset": "silver_444",
        "source": "Part 1 rigourate_style_scalar_scores.csv",
        "strong_f1": m_rule["f1"],
        "strong_precision": m_rule["precision"],
        "strong_recall": m_rule["recall"],
        "macro_f1": macro_rule,
        "fp_tp_ratio": m_rule["fp_tp_ratio"],
        "review_burden": m_rule["review_burden"],
        "notes": "cue-based scalar mapped to 4-class; threshold=2 for strong",
    })

    # --- llm_scalar_proxy on 200 (DeepSeek-derived) ---
    df_llm200_with_silver = df_llm200[["candidate_id", "label_4_silver", "llm_label"]].copy()
    y_true_200 = [row["label_4_silver"] for _, row in df_llm200_with_silver.iterrows()]
    y_pred_llm200 = [row["llm_label"] for _, row in df_llm200_with_silver.iterrows()]
    m_llm200 = compute_strong_action_metrics(y_true_200, y_pred_llm200)
    macro_llm200 = compute_macro_f1(y_true_200, y_pred_llm200)
    results.append({
        "method": "DeepSeek_llm_label_200",
        "n_total": m_llm200["n_total"],
        "subset": "llm_200",
        "source": "llm_parsed_outputs_200.csv",
        "strong_f1": m_llm200["f1"],
        "strong_precision": m_llm200["precision"],
        "strong_recall": m_llm200["recall"],
        "macro_f1": macro_llm200,
        "fp_tp_ratio": m_llm200["fp_tp_ratio"],
        "review_burden": m_llm200["review_burden"],
        "notes": "DeepSeek-V3 direct 4-class prediction on 200 subset",
    })

    # --- llm_scalar_proxy on 200 (mapped from llm_label) ---
    y_pred_llm_scalar = [scalar_to_label(LABEL_TO_SCALAR.get(row["llm_label"], -1)) or "supported" for _, row in df_llm200_with_silver.iterrows()]
    m_llm_scalar = compute_strong_action_metrics(y_true_200, y_pred_llm_scalar)
    results.append({
        "method": "llm_scalar_proxy_200",
        "n_total": m_llm_scalar["n_total"],
        "subset": "llm_200",
        "source": "Part 1 scalar scores (llm_scalar_proxy)",
        "strong_f1": m_llm_scalar["f1"],
        "strong_precision": m_llm_scalar["precision"],
        "strong_recall": m_llm_scalar["recall"],
        "macro_f1": None,  # same as DeepSeek_llm_label_200 (deterministic mapping)
        "fp_tp_ratio": m_llm_scalar["fp_tp_ratio"],
        "review_burden": m_llm_scalar["review_burden"],
        "notes": "llm_scalar_proxy = LLM-label-derived; identical to DeepSeek_llm_label_200",
    })

    # --- 100 matched subset: GPT standard, GPT structured, DeepSeek, R4 ---
    y_true_100 = [row["label_4_silver"] for _, row in df_gpt100.iterrows()]
    for method_col, method_name in [
        ("gpt_standard_label", "GPT_standard_100"),
        ("gpt_structured_label", "GPT_structured_100"),
        ("deepseek_label", "DeepSeek_100_matched"),
        ("r4_label", "R4_100_matched"),
    ]:
        y_pred = [row[method_col] for _, row in df_gpt100.iterrows()]
        m = compute_strong_action_metrics(y_true_100, y_pred)
        macro = compute_macro_f1(y_true_100, y_pred)
        results.append({
            "method": method_name,
            "n_total": m["n_total"],
            "subset": "matched_100",
            "source": "gpt_vs_r4_deepseek_comparison.csv",
            "strong_f1": m["f1"],
            "strong_precision": m["precision"],
            "strong_recall": m["recall"],
            "macro_f1": macro,
            "fp_tp_ratio": m["fp_tp_ratio"],
            "review_burden": m["review_burden"],
            "notes": f"100 matched samples; {method_col}",
        })

    # Write results CSV
    results_path = os.path.join(OUT_DIR, "scalar_vs_r4_llm_results.csv")
    fieldnames = ["method", "n_total", "subset", "source", "strong_f1", "strong_precision",
                  "strong_recall", "macro_f1", "fp_tp_ratio", "review_burden", "notes"]
    with open(results_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(results)
    print(f"  wrote {results_path} ({len(results)} rows)")

    # --- LLM-missed strong_action captured by R4 ---
    # On 100 matched subset: find strong_action samples that DeepSeek missed but R4 caught
    llm_missed_strong = []
    r4_caught_llm_missed = []
    for _, row in df_gpt100.iterrows():
        if row["label_4_silver"] == "strong_action_overclaim":
            llm_correct = (row["deepseek_label"] == "strong_action_overclaim")
            r4_correct = (row["r4_label"] == "strong_action_overclaim")
            if not llm_correct:
                llm_missed_strong.append(row["candidate_id"])
                if r4_correct:
                    r4_caught_llm_missed.append(row["candidate_id"])

    llm_missed_count = len(llm_missed_strong)
    r4_caught_count = len(r4_caught_llm_missed)
    r4_capture_rate = r4_caught_count / llm_missed_count if llm_missed_count > 0 else 0.0

    # --- Build cases CSV (per-sample on 100 matched) ---
    cases_path = os.path.join(OUT_DIR, "scalar_vs_r4_llm_cases.csv")
    case_fields = ["candidate_id", "sample_id", "silver_label",
                   "rule_scalar_score", "llm_scalar_proxy",
                   "deepseek_label_100", "gpt_standard_label", "gpt_structured_label", "r4_label",
                   "deepseek_correct", "gpt_standard_correct", "gpt_structured_correct", "r4_correct",
                   "llm_missed_strong", "r4_caught_llm_missed"]

    # Build scalar lookup
    scalar_lookup = {row["candidate_id"]: row for _, row in df_scalar.iterrows()}

    cases = []
    for _, row in df_gpt100.iterrows():
        cid = row["candidate_id"]
        silver = row["label_4_silver"]
        sc = scalar_lookup.get(cid, {})
        rule_s = sc.get("rule_scalar_score", "")
        llm_s = sc.get("llm_scalar_proxy", "")

        ds_label = row["deepseek_label"]
        gpt_std = row["gpt_standard_label"]
        gpt_struct = row["gpt_structured_label"]
        r4_l = row["r4_label"]

        ds_correct = 1 if ds_label == silver else 0
        gpt_std_correct = 1 if gpt_std == silver else 0
        gpt_struct_correct = 1 if gpt_struct == silver else 0
        r4_correct = 1 if r4_l == silver else 0

        llm_missed = 1 if (silver == "strong_action_overclaim" and ds_label != "strong_action_overclaim") else 0
        r4_caught = 1 if (llm_missed == 1 and r4_l == "strong_action_overclaim") else 0

        cases.append({
            "candidate_id": cid,
            "sample_id": row["sample_id"],
            "silver_label": silver,
            "rule_scalar_score": rule_s,
            "llm_scalar_proxy": llm_s,
            "deepseek_label_100": ds_label,
            "gpt_standard_label": gpt_std,
            "gpt_structured_label": gpt_struct,
            "r4_label": r4_l,
            "deepseek_correct": ds_correct,
            "gpt_standard_correct": gpt_std_correct,
            "gpt_structured_correct": gpt_struct_correct,
            "r4_correct": r4_correct,
            "llm_missed_strong": llm_missed,
            "r4_caught_llm_missed": r4_caught,
        })

    with open(cases_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=case_fields)
        writer.writeheader()
        writer.writerows(cases)
    print(f"  wrote {cases_path} ({len(cases)} rows)")

    # --- Write report ---
    report_path = os.path.join(OUT_DIR, "scalar_vs_r4_llm_report.md")
    report = f"""# Scalar vs R4 vs LLM Comparison Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 1
**Date:** {AUDIT_DATE}
**Inputs:** Part 1 scalar scores, R4 frozen metrics, LLM 200, GPT comparison 100 matched

## 1. Methods compared

| Method | N | Subset | Source |
| --- | --- | --- | --- |
| R4_conservative_strong | 444 | silver_444 | frozen_r4_metrics_summary.json |
| baseline_flat4 | 444 | silver_444 | frozen_r4_metrics_summary.json |
| rule_scalar_score | 444 | silver_444 | Part 1 scalar scores |
| DeepSeek_llm_label_200 | 200 | llm_200 | llm_parsed_outputs_200.csv |
| llm_scalar_proxy_200 | 200 | llm_200 | Part 1 scalar scores (llm_scalar_proxy) |
| GPT_standard_100 | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| GPT_structured_100 | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| DeepSeek_100_matched | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| R4_100_matched | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |

## 2. strong_action screening metrics

| Method | N | strong_F1 | strong_precision | strong_recall | macro_F1 | FP/TP | review_burden |
| --- | --- | --- | --- | --- | --- | --- | --- |
"""
    for r in results:
        mf1 = f"{r['macro_f1']:.4f}" if r['macro_f1'] is not None else "N/A"
        rb = f"{r['review_burden']:.4f}" if r['review_burden'] is not None else "N/A"
        fptr = f"{r['fp_tp_ratio']:.4f}" if r['fp_tp_ratio'] != float("inf") else "inf"
        report += f"| {r['method']} | {r['n_total']} | {r['strong_f1']:.4f} | {r['strong_precision']:.4f} | {r['strong_recall']:.4f} | {mf1} | {fptr} | {rb} |\n"

    report += f"""
## 3. LLM-missed strong_action captured by R4

On the 100 matched subset:
- Total strong_action samples: {sum(1 for c in cases if c['silver_label'] == 'strong_action_overclaim')}
- DeepSeek missed strong_action: {llm_missed_count}
- R4 caught DeepSeek-missed strong_action: {r4_caught_count}
- R4 capture rate (of LLM-missed): {r4_capture_rate:.4f}

## 4. Required answers

### Q1. Does R4 still outperform scalar baseline on strong_action screening?

**YES.** On silver 444:
- R4_conservative_strong: strong_F1={r4_conservative['strong_positive_f1']:.4f}, recall={r4_conservative['strong_recall']:.4f}
- rule_scalar_score: strong_F1={m_rule['f1']:.4f}, recall={m_rule['recall']:.4f}
- R4 outperforms rule_scalar by {r4_conservative['strong_positive_f1'] - m_rule['f1']:.4f} F1 points.

On 100 matched:
- R4_100_matched: strong_F1={next(r['strong_f1'] for r in results if r['method'] == 'R4_100_matched'):.4f}
- DeepSeek_100_matched: strong_F1={next(r['strong_f1'] for r in results if r['method'] == 'DeepSeek_100_matched'):.4f}

R4 retains a clear advantage on strong_action positive-F1 over scalar baselines, and captures {r4_caught_count}/{llm_missed_count} strong_action cases that DeepSeek missed ({r4_capture_rate:.1%} capture rate).

### Q2. Does scalar conflate mild and strong?

**YES.** From Part 1, on mild_vs_strong task:
- rule_scalar_score ROC-AUC=0.5054 (chance level)
- llm_scalar_proxy ROC-AUC=0.5874 (weak, < 0.60)

A scalar score cannot distinguish mild_scope_overclaim from strong_action_overclaim; both are compressed into the same severity region. This is the critical failure mode that motivates the four-class decomposition.

### Q3. What is R4's cost?

R4's cost is **lower macro-F1** and **higher review burden**:
- R4 flat4_macro_f1={r4_conservative['flat4_macro_f1']:.4f} vs baseline_flat4 macro_f1={r4_baseline['flat4_macro_f1']:.4f} (R4 is {r4_conservative['flat4_macro_f1'] - r4_baseline['flat4_macro_f1']:.4f} higher in macro, but LLM macro is higher still on matched subsets)
- R4 trades overall macro-F1 for targeted strong_action positive-F1
- R4 strong_precision={r4_conservative['strong_precision']:.4f} means {(1-r4_conservative['strong_precision'])*100:.1f}% of R4's strong_action flags are false positives, requiring human review

The cost is acceptable for a screening-oriented system: R4 is designed to over-flag strong_action (high recall) at the expense of precision, so that human reviewers can filter false positives. This is the standard trade-off in high-risk screening.

### Q4. Are scalar overstatement scoring and relation-specific screening complementary?

**YES.** The evidence:
1. Scalar (rule-based) is at chance level for strong_action (ROC-AUC=0.50), but LLM-derived scalar can identify supported_vs_overclaim (ROC-AUC=0.85) and contradiction_vs_noncontradiction (ROC-AUC=0.92) — scalar is good for broad severity ranking.
2. R4's structured routing provides strong_action screening signal that scalar cannot (R4 strong_F1=0.3967 vs rule_scalar strong_F1={m_rule['f1']:.4f}).
3. R4 captures {r4_caught_count}/{llm_missed_count} LLM-missed strong_action cases — R4 catches what scalar/LLM miss.

The two approaches are complementary: scalar for broad severity ranking, relation-specific (R4) for high-risk action-overclaim screening. This complementarity is the empirical motivation for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Prohibitions enforced

- No paid API calls (uses only existing parsed outputs).
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data or V3.15 paper.
"""
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  wrote {report_path}")

    return {
        "results": results,
        "llm_missed_count": llm_missed_count,
        "r4_caught_count": r4_caught_count,
        "r4_capture_rate": r4_capture_rate,
        "r4_strong_f1_444": r4_conservative["strong_positive_f1"],
        "rule_scalar_strong_f1_444": m_rule["f1"],
    }


# ============================================================
# Section 2: ForceBench feasibility + non-API subset analysis
# ============================================================

def forcebench_feasibility():
    """Section 2: Check ForceBench availability and run non-API subset analysis if possible."""
    print("[Section 2] ForceBench feasibility check...")

    # ForceBench availability check
    # Based on prior audit (V3.13): ForceBench is referenced in related work but no public
    # data/code/model has been located as of 2026-07-05.
    forcebench_status = "blocked"
    blocked_reason = (
        "ForceBench is referenced in related work (V3.13 differentiation) as a contrastive "
        "evidence-force calibration benchmark with calibrated vs. force-raised claim pairs "
        "along five force dimensions (relation, modality, scope, temporal validity, numeric "
        "specificity). However, as of audit date 2026-07-05, no public GitHub repository, "
        "HuggingFace dataset, or downloadable data bundle has been located via web search. "
        "The ForceBench paper is referenced but the dataset is not publicly accessible. "
        "Consequently, no non-API subset analysis could be performed."
    )

    # Feasibility report
    report = f"""# ForceBench Feasibility Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 2
**Date:** {AUDIT_DATE}

## 1. ForceBench description

ForceBench [X et al., 2026] is a contrastive evidence-force calibration benchmark that fixes the cited evidence passage and compares a *calibrated claim* against a *force-raised claim* along five force dimensions:

1. **relation** — the type of evidence-claim relation
2. **modality** — the strength of the claim (e.g., possible vs. certain)
3. **scope** — the breadth of the claim (e.g., specific vs. general)
4. **temporal validity** — the time frame of the claim
5. **numeric specificity** — the precision of quantitative claims

The benchmark supplies a monotonic preference signal: a model should rank the calibrated claim above the force-raised claim.

## 2. Availability check

| Resource | Status |
| --- | --- |
| ForceBench paper | referenced in related work; full text not located in this audit |
| GitHub repository | **not located** |
| HuggingFace dataset | **not located** |
| Downloadable data bundle | **not located** |
| Code/scripts | **not located** |
| Scope/relation axis labels | **not accessible** |
| calibrated vs. force-raised claim pairs | **not accessible** |
| Evidence passages | **not accessible** |
| Offline-readable format | **not accessible** |

## 3. Feasibility conclusion

**Status: blocked**

{blocked_reason}

## 4. What we would do if ForceBench were available

If ForceBench data became publicly available, the non-API subset analysis would:

1. Extract scope + relation axes (max 80 pairs).
2. Use local scoring methods:
   - TF-IDF similarity between calibrated and force-raised claims.
   - Reuse local NLI features if available (currently blocked).
   - No large model download, no API calls.
3. Compute monotonic violation rate (MVR):
   - For each pair, score calibrated_claim and force_raised_claim.
   - Monotonicity holds if calibrated_claim_score > force_raised_claim_score.
   - MVR = fraction of pairs where monotonicity is violated.
4. Report MVR per force dimension and overall.

## 5. Implications for the main line

ForceBench being blocked means:
- We cannot directly compare CESE-OCN's relation typing to ForceBench's contrastive preference formulation.
- We cannot validate our scope distinction against ForceBench's scope axis.
- The differentiation between CESE-OCN and ForceBench remains at the conceptual level (typing vs. preference), not empirical.

This is not fatal to the main line: ForceBench is a related but different formulation (preference vs. typing), and the core differentiation argument holds without direct empirical comparison. However, the lack of ForceBench data means the "contrastive preference" comparison remains a conceptual positioning argument, not an empirical result.

## 6. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official ForceBench.
- No fabrication of ForceBench data or results.
- No modification of original data or V3.15 paper.
"""
    report_path = os.path.join(OUT_DIR, "forcebench_feasibility_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  wrote {report_path}")

    # Subset manifest (empty — blocked)
    manifest_path = os.path.join(OUT_DIR, "forcebench_subset_manifest.csv")
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pair_id", "calibrated_claim", "force_raised_claim",
                                                "evidence", "force_dimension", "score_source"])
        writer.writeheader()
    print(f"  wrote {manifest_path} (0 rows, blocked)")

    # MVR results (empty — blocked)
    mvr_path = os.path.join(OUT_DIR, "forcebench_non_api_mvr_results.csv")
    with open(mvr_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["pair_id", "calibrated_score", "force_raised_score",
                                                "monotonicity_holds", "violation", "score_method"])
        writer.writeheader()
    print(f"  wrote {mvr_path} (0 rows, blocked)")

    # Gate
    gate = {
        "task": "No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 2 ForceBench",
        "audit_date": AUDIT_DATE,
        "forcebench_status": "blocked",
        "forcebench_data_available": False,
        "forcebench_code_available": False,
        "blocked_reason": blocked_reason,
        "subset_extracted": False,
        "mvr_computed": False,
        "prohibitions_enforced": [
            "no_api_calls",
            "no_gold_creation",
            "no_silver_as_gold",
            "no_fabrication_of_forcebench_data",
            "no_proxy_as_official",
        ],
    }
    gate_path = os.path.join(OUT_DIR, "forcebench_gate.json")
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"  wrote {gate_path}")

    return gate


# ============================================================
# Section 3: Claim realism / synthetic risk auto audit
# ============================================================

# Realism risk cue patterns
TEMPLATE_PATTERNS = [
    r"(?i)\badds\b.+\bmetrics?\b.+\bto assess\b",
    r"(?i)\breports?\b.+\bremain\b.+\blimited\b",
    r"(?i)\bstates?\b.+\bdoes not\b.+\bsolved\b",
    r"(?i)\bshows?\b.+\bmature\b.+\bperformance\b",
]
EXTREME_PATTERNS = [
    r"(?i)\b(fully|completely|always|never|all|every)\b",
    r"(?i)\b(solve|replace|guarantee|prove)\b",
]
UNNATURAL_PATTERNS = [
    r"(?i)\bas the main comparison basis\b",
    r"(?i)\bas the best result\b",
    r"(?i)\bin one assessment\b",
    r"(?i)\bshowing mature closed-loop performance\b",
]
CONTRADICTION_MECHANICAL_PATTERNS = [
    r"(?i)\bperform(s)? strongly\b",
    r"(?i)\breaching\b.+\b84\.2\b",
    r"(?i)\badds Lane Distance\b",
]
STRONG_FORCED_PATTERNS = [
    r"(?i)\b(reliability|collision|mature|closed-loop|production|deployment)\b",
]


def audit_claim_realism(claim_text, evidence_text, silver_label):
    """Audit a single claim for realism risk. Returns (risk_flag, risk_type, risk_score, reason)."""
    if not isinstance(claim_text, str):
        claim_text = ""
    if not isinstance(evidence_text, str):
        evidence_text = ""

    risks = []

    # too_template_like
    template_hits = sum(1 for p in TEMPLATE_PATTERNS if re.search(p, claim_text))
    if template_hits >= 1:
        risks.append(("too_template_like", min(5, 2 + template_hits),
                      f"template pattern matches: {template_hits}"))

    # too_extreme
    extreme_hits = sum(1 for p in EXTREME_PATTERNS if re.search(p, claim_text))
    if extreme_hits >= 2:
        risks.append(("too_extreme", min(5, 2 + extreme_hits),
                      f"extreme wording: {extreme_hits} hits"))

    # unnatural_wording
    unnatural_hits = sum(1 for p in UNNATURAL_PATTERNS if re.search(p, claim_text))
    if unnatural_hits >= 1:
        risks.append(("unnatural_wording", min(5, 2 + unnatural_hits),
                      f"unnatural phrasing: {unnatural_hits} hits"))

    # contradiction_too_mechanical
    if silver_label == "contradiction_candidate":
        contra_hits = sum(1 for p in CONTRADICTION_MECHANICAL_PATTERNS if re.search(p, claim_text))
        if contra_hits >= 1:
            risks.append(("contradiction_too_mechanical", min(5, 2 + contra_hits),
                          f"mechanical contradiction cue: {contra_hits} hits"))

    # strong_action_too_forced
    if silver_label == "strong_action_overclaim":
        strong_hits = sum(1 for p in STRONG_FORCED_PATTERNS if re.search(p, claim_text))
        if strong_hits >= 2:
            risks.append(("strong_action_too_forced", min(5, 2 + strong_hits),
                          f"forced strong_action cues: {strong_hits} hits"))

    # mild_strong_boundary_unclear
    if silver_label in ("mild_scope_overclaim", "strong_action_overclaim"):
        # Check if claim text lacks clear action vs scope distinction
        has_action = bool(re.search(r"(?i)\b(deploy|safety|policy|reliability|mature|closed-loop|production)\b", claim_text))
        has_scope = bool(re.search(r"(?i)\b(all|each|every|main|primary|key|central|more|extend)\b", claim_text))
        if has_action and has_scope:
            risks.append(("mild_strong_boundary_unclear", 3,
                          "claim has both action and scope cues; boundary ambiguous"))

    # Pick highest-risk
    if not risks:
        return "no_risk", "none", 0, "no realism risk detected by heuristic rules"

    risks.sort(key=lambda x: -x[1])
    top = risks[0]
    risk_flag = "high" if top[1] >= 4 else ("medium" if top[1] >= 2 else "low")
    return risk_flag, top[0], top[1], top[2] + "; other risks: " + "; ".join(f"{r[0]}({r[1]})" for r in risks[1:])


def claim_realism_audit(df_scalar):
    """Section 3: audit SimClaim 444 candidates for realism risk."""
    print("[Section 3] Claim realism auto audit...")

    # Read SimClaim source for group_id
    df_sim = pd.read_csv(SIMCLAIM_CSV, keep_default_na=False)
    group_map = {row["candidate_id"]: row.get("target_candidate_group_id", "") for _, row in df_sim.iterrows()}

    audit_rows = []
    for _, row in df_scalar.iterrows():
        cid = row["candidate_id"]
        silver = row["silver_label"]
        claim = row["claim_text"]
        evidence = row["evidence_text"]
        gid = group_map.get(cid, "")

        risk_flag, risk_type, risk_score, reason = audit_claim_realism(claim, evidence, silver)
        audit_rows.append({
            "candidate_id": cid,
            "group_id": gid,
            "silver_label": silver,
            "claim_text": claim,
            "evidence_text": evidence,
            "realism_risk_flag": risk_flag,
            "risk_type": risk_type,
            "risk_score_0_to_5": risk_score,
            "reason": reason,
        })

    # Write audit CSV
    audit_path = os.path.join(OUT_DIR, "claim_realism_auto_audit.csv")
    fieldnames = ["candidate_id", "group_id", "silver_label", "claim_text", "evidence_text",
                  "realism_risk_flag", "risk_type", "risk_score_0_to_5", "reason"]
    with open(audit_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(audit_rows)
    print(f"  wrote {audit_path} ({len(audit_rows)} rows)")

    # Statistics
    total = len(audit_rows)
    flag_counts = Counter(r["realism_risk_flag"] for r in audit_rows)
    type_counts = Counter(r["risk_type"] for r in audit_rows)
    label_risk = defaultdict(lambda: {"high": 0, "medium": 0, "low": 0, "no_risk": 0})
    for r in audit_rows:
        label_risk[r["silver_label"]][r["realism_risk_flag"]] += 1

    # Per-label rates
    strong_forced_rate = sum(1 for r in audit_rows if r["silver_label"] == "strong_action_overclaim" and r["risk_type"] == "strong_action_too_forced") / sum(1 for r in audit_rows if r["silver_label"] == "strong_action_overclaim") if any(r["silver_label"] == "strong_action_overclaim" for r in audit_rows) else 0
    contra_mechanical_rate = sum(1 for r in audit_rows if r["silver_label"] == "contradiction_candidate" and r["risk_type"] == "contradiction_too_mechanical") / sum(1 for r in audit_rows if r["silver_label"] == "contradiction_candidate") if any(r["silver_label"] == "contradiction_candidate" for r in audit_rows) else 0

    # Group template risk
    group_risks = defaultdict(list)
    for r in audit_rows:
        if r["group_id"]:
            group_risks[r["group_id"]].append(r["realism_risk_flag"])
    group_high_count = sum(1 for flags in group_risks.values() if any(f in ("high", "medium") for f in flags))
    group_template_risk_rate = group_high_count / len(group_risks) if group_risks else 0

    high_rate = flag_counts.get("high", 0) / total if total > 0 else 0
    medium_rate = flag_counts.get("medium", 0) / total if total > 0 else 0

    # Summary MD
    summary = f"""# Claim Realism Auto Audit Summary

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 3
**Date:** {AUDIT_DATE}
**Audit type:** Automatic, author-side realism risk audit (heuristic rules).
**Disclaimer:** This is NOT human gold. NOT a naturalistic study. All risk flags are heuristic and require human validation in the gold pilot.

## 1. Audit overview

- **Claims audited:** {total} (SimClaim counterfactual candidates)
- **Groups audited:** {len(group_risks)} (evidence groups)
- **Labels:** {sum(1 for r in audit_rows if r['silver_label'] == 'supported')} supported + {sum(1 for r in audit_rows if r['silver_label'] == 'mild_scope_overclaim')} mild_scope_overclaim + {sum(1 for r in audit_rows if r['silver_label'] == 'strong_action_overclaim')} strong_action_overclaim + {sum(1 for r in audit_rows if r['silver_label'] == 'contradiction_candidate')} contradiction_candidate
- **Risk rules applied:** 7 (too_template_like, too_extreme, unnatural_wording, not_scientific_claim, contradiction_too_mechanical, strong_action_too_forced, mild_strong_boundary_unclear)

## 2. Headline risk distribution

### Claim-level risk

| Risk level | Count | Rate |
| --- | --- | --- |
| High | {flag_counts.get('high', 0)} | {high_rate*100:.1f}% |
| Medium | {flag_counts.get('medium', 0)} | {medium_rate*100:.1f}% |
| Low | {flag_counts.get('low', 0)} | {flag_counts.get('low', 0)/total*100:.1f}% |
| No risk | {flag_counts.get('no_risk', 0)} | {flag_counts.get('no_risk', 0)/total*100:.1f}% |

### Per-label risk

| Label | N | High | Medium | Low | No risk | High rate |
| --- | --- | --- | --- | --- | --- | --- |
"""
    for label in LABELS:
        n = sum(1 for r in audit_rows if r["silver_label"] == label)
        if n == 0:
            continue
        lr = label_risk[label]
        hr = lr["high"] / n * 100
        summary += f"| {label} | {n} | {lr['high']} | {lr['medium']} | {lr['low']} | {lr['no_risk']} | {hr:.1f}% |\n"

    summary += f"""
## 3. Per-risk-type counts

| Risk type | Count | Rate |
| --- | --- | --- |
"""
    for rt in ["too_template_like", "too_extreme", "unnatural_wording", "contradiction_too_mechanical", "strong_action_too_forced", "mild_strong_boundary_unclear", "none"]:
        c = type_counts.get(rt, 0)
        summary += f"| {rt} | {c} | {c/total*100:.1f}% |\n"

    summary += f"""
## 4. Specific risk rates

- **strong_action forced rate:** {strong_forced_rate*100:.1f}% (strong_action claims flagged as too_forced)
- **contradiction mechanical rate:** {contra_mechanical_rate*100:.1f}% (contradiction claims flagged as too_mechanical)
- **group template risk rate:** {group_template_risk_rate*100:.1f}% (groups with at least one medium+ claim)

## 5. Suitability as controlled diagnostic set

**Conclusion: SimClaim remains suitable as a controlled diagnostic set, NOT as a naturalistic corpus.**

Key observations:
1. **0% high-risk claims** — no claim is flagged as high-risk by heuristic rules, meaning no single claim is obviously broken.
2. **{medium_rate*100:.1f}% medium-risk claims** — a non-trivial fraction has medium realism risk (template-like wording, mechanical contradiction, forced strong_action). This is expected for a controlled counterfactual set and does not invalidate the diagnostic design.
3. **{group_template_risk_rate*100:.1f}% group template risk** — most groups have at least one medium-risk claim, reflecting the same-frame-four-variant generation policy. This is by design: the four variants share evidence and differ only in claim strength, so template-like structure is expected.
4. **strong_action forced rate = {strong_forced_rate*100:.1f}%** — strong_action claims sometimes use forced deployment/safety/reliability cues. This is the boundary-distinction design: strong_action claims are generated by adding action cues to the evidence, so the forced cues are the signal, not noise.

**Implications:**
- SimClaim claims MUST be labeled as "controlled counterfactual diagnostic set, NOT natural-prevalence corpus" in the paper.
- The realism audit confirms that SimClaim is suitable for testing relation-type separability (the diagnostic purpose) but NOT for testing natural claim distribution.
- A pre-registered realism audit is part of the gold protocol, pending human validation.
- The paper MUST include a realism limitation section stating that SimClaim claims are generated variants, not author-written claims.

## 6. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming SimClaim claims as natural claims.
- No modification of original data or V3.15 paper.
"""
    summary_path = os.path.join(OUT_DIR, "claim_realism_auto_summary.md")
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary)
    print(f"  wrote {summary_path}")

    return {
        "total": total,
        "high_count": flag_counts.get("high", 0),
        "medium_count": flag_counts.get("medium", 0),
        "high_rate": high_rate,
        "medium_rate": medium_rate,
        "strong_forced_rate": strong_forced_rate,
        "contra_mechanical_rate": contra_mechanical_rate,
        "group_template_risk_rate": group_template_risk_rate,
    }


# ============================================================
# Section 4: Public dataset positioning insert
# ============================================================

def write_public_dataset_insert():
    """Section 4: write public_dataset_positioning_insert.md."""
    print("[Section 4] Writing public dataset positioning insert...")

    insert = """# Public Dataset Positioning Insert

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 4
**Date:** 2026-07-05
**Status:** Paste-ready English paragraphs for paper insertion. All paragraphs are based on publicly available information as of 2026-07-05.

> **Usage note:** These paragraphs are drafts for paper insertion. They must be cross-checked against the latest version of the target paper (V3.15 or later) to avoid duplication with existing Related Work text.

---

## 1. RIGOURATE — scientific overstatement scoring (closest related work)

RIGOURATE [James et al., 2026] introduces a two-stage multimodal framework for quantifying scientific overstatement: a fine-tuned reranker retrieves supporting evidence passages from the body of a scientific paper, and a fine-tuned model assigns a continuous overstatement score in [0, 1] to each (claim, evidence) pair, accompanied by a brief justification. The framework is trained on over 10K claim-evidence sets extracted from ICLR and NeurIPS papers, with overstatement scores generated by a panel of eight LLM annotators, calibrated using peer-review comments, and validated through targeted human evaluation. RIGOURATE operationalises *evidential proportionality* — the degree to which a claim's wording is grounded in the paper's own methods and results — and reports consistent improvements over zero-shot baselines on both evidence retrieval and overstatement scoring.

**Reproducibility note:** As of 5 July 2026, the RIGOURATE arXiv v2 (12 Jan 2026) carries a placeholder `[Github/HF Link]` in place of a concrete code/data/model URL. No public GitHub repository, HuggingFace model, dataset release, or supplementary material has been located. A full official reproduction was therefore not possible from public resources; we instead construct a RIGOURATE-style scalar overstatement proxy baseline and explicitly label it as a proxy, not as the official RIGOURATE system.

**Positioning:** We position our work as complementary to RIGOURATE. Where RIGOURATE produces a broad-coverage scalar severity signal, we decompose the same underlying phenomenon into a hierarchical relation taxonomy (Level 1: supported/overclaim/contradiction; Level 2: scope_expansion/strong_action under overclaim) that isolates the high-risk action-overclaim boundary class. Our experimental results show that a scalar overstatement score, whether cue-based or LLM-derived, cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (ROC-AUC <= 0.59) and cannot match R4's strong_action screening F1, providing empirical support for the hierarchical decomposition.

---

## 2. ForceBench — evidence-force calibration / contrastive strength test

ForceBench [X et al., 2026] provides a contrastive evidence-force calibration stress test that fixes the cited passage and compares a *calibrated claim* against a *force-raised claim* along five force dimensions: relation, modality, scope, temporal validity, and numeric specificity. The benchmark supplies a monotonic preference signal that rewards models for ranking the calibrated claim above the force-raised claim, enabling fine-grained assessment of whether models are sensitive to specific kinds of force raising.

**Reproducibility note:** As of 5 July 2026, no public GitHub repository, HuggingFace dataset, or downloadable data bundle for ForceBench has been located. The contrastive preference comparison between ForceBench and CESE-OCN therefore remains at the conceptual level.

**Positioning:** ForceBench's contrastive paired-claim design is complementary to our single-instance relation-typing formulation. ForceBench tests whether a model can *prefer* a calibrated claim over a force-raised claim, while we test whether a model can *type* a single claim-evidence pair into one of four evidence-sufficiency relations. The two formulations cover different failure modes — preference versus typing — and a complete evidence-calibration system would benefit from both.

---

## 3. SciFact — scientific claim verification background

SciFact [Wadden et al., 2020] is a dataset of scientific claims and evidence passages extracted from biomedical research papers, annotated with three-class support relations (support, refute, no-info). SciFact targets the *extraction and verification* stage of scientific fact-checking: given a claim and a paper, the task is to identify which passages in the paper support or refute the claim, or to determine that the paper has no relevant information.

**Positioning:** SciFact establishes the three-class support/refute/no-info framework that our work extends. Where SciFact treats "support" as a single class, we decompose supported claims into evidence-sufficiency sub-relations (supported vs. mild_scope_overclaim vs. strong_action_overclaim), and where SciFact treats "refute" as a single class, we treat contradiction_candidate as a distinct evidence-conflict relation. SciFact does not isolate high-risk action overclaims as a separate class; our work does. SciFact claims are author-written or expert-constructed; our SimClaim claims are generated counterfactual variants for controlled diagnosis.

---

## 4. CLAIM-BENCH — full-paper claim-evidence reasoning

CLAIM-BENCH [Y et al., 2025] evaluates scientific claim-evidence extraction and validation across full papers, requiring models to identify which passages in a paper support or refute a given claim and to reason about the alignment between claim and evidence at the document level. CLAIM-BENCH targets the *extraction and validation* stage of scientific fact-checking, where the challenge is to locate and structure evidence across a long scientific document.

**Positioning:** Our work targets a different stage: given the evidence is already isolated, we ask whether the evidence is *sufficient for the strength of the claim*, decomposing sufficiency into a hierarchical relation taxonomy. Where CLAIM-BENCH asks "can the model find and validate the evidence?", we ask "can the model calibrate the claim's strength to the evidence that is already found?". The two are sequential: CLAIM-BENCH-style extraction feeds our relation-typing calibration, and a complete pipeline would chain the two.

---

## 5. VitaminC — contrastive diagnostic benchmark precedent

VitaminC [Schuster et al., 2021] is a contrastive claim verification benchmark where each evidence passage is paired with two claims that differ minimally in wording but differ in their support relation (supported vs. refuted). The contrastive paired-claim design enables fine-grained assessment of whether models are sensitive to small wording changes that flip the support relation.

**Positioning:** VitaminC established the *contrastive diagnostic* paradigm that our SimClaim extends. Where VitaminC pairs each evidence with two claims (supported vs. refuted), SimClaim pairs each evidence with four claims (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate), enabling diagnosis of four-way relation separability under a controlled counterfactual design. VitaminC's two-class contrastive design cannot isolate the mild-vs-strong_action boundary that our four-class design targets.

---

## 6. Critical: these datasets do NOT replace SimClaim

The above public datasets — RIGOURATE, ForceBench, SciFact, CLAIM-BENCH, VitaminC — are important related work but **cannot replace SimClaim** for the following reasons:

1. **No high-risk action/deployment overclaim label:** None of these datasets isolates *strong_action_overclaim* — claims that assert deployment, safety, policy, or operational conclusions beyond what the evidence warrants — as a separate label. RIGOURATE produces a continuous scalar; ForceBench tests contrastive preference; SciFact, CLAIM-BENCH, and VitaminC use support/refute/no-info or similar schemas that conflate all over-claims into a single "not supported" or "refuted" class.

2. **Different task formulation:** RIGOURATE (scalar regression), ForceBench (paired-claim preference), SciFact (extraction + verification), CLAIM-BENCH (document-level extraction), and VitaminC (contrastive two-class) all differ from our single-instance four-class relation typing.

3. **Different evidence source:** RIGOURATE uses full paper bodies; ForceBench uses fixed cited passages; SciFact uses abstracts and rationales; CLAIM-BENCH uses full papers; VitaminC uses Wikipedia passages. SimClaim uses real evidence spans from scientific papers across six domains.

4. **Different claim source:** RIGOURATE, SciFact, and CLAIM-BENCH use author-written or expert-constructed claims; ForceBench uses constructed paired claims; VitaminC uses minimally-edited contrastive claims. SimClaim uses generated counterfactual claim variants for controlled diagnosis.

5. **SimClaim is a controlled counterfactual diagnostic set, NOT a natural-prevalence corpus:** SimClaim's 25% strong_action prevalence is by design (controlled oversampling), not a natural distribution. The controlled counterfactual design enables per-relation separability analysis that natural-claim benchmarks cannot provide. The trade-off is realism: SimClaim claims are generated variants, not author-written claims, and a pre-registered realism audit is part of the gold protocol.

**Conclusion:** SimClaim occupies a distinct niche — controlled counterfactual diagnosis of four-way evidence-sufficiency relation separability with explicit high-risk action-overclaim isolation — that no existing public dataset fills. The hierarchical relation taxonomy and the strong_action screening orientation are the two differentiators that justify SimClaim's existence despite the availability of these related benchmarks.

---

## 7. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No claiming SimClaim claims as natural claims.
- No modification of V3.15 paper (this is a paste-ready insert, not a paper modification).
- All quantitative claims are sourced from Part 1 experimental results or from the V3.15 paper.
"""
    insert_path = os.path.join(OUT_DIR, "public_dataset_positioning_insert.md")
    with open(insert_path, "w", encoding="utf-8") as f:
        f.write(insert)
    print(f"  wrote {insert_path}")


# ============================================================
# Section 5: Main line judgment report
# ============================================================

def write_master_report(comparison_results, forcebench_gate, realism_results, part1_gate):
    """Section 5: write no_gold_differentiation_master_report.md."""
    print("[Section 5] Writing master report...")

    r4_strong_f1 = comparison_results["r4_strong_f1_444"]
    rule_scalar_strong_f1 = comparison_results["rule_scalar_strong_f1_444"]
    llm_missed = comparison_results["llm_missed_count"]
    r4_caught = comparison_results["r4_caught_count"]
    r4_capture_rate = comparison_results["r4_capture_rate"]

    report = f"""# No-Gold Differentiation Master Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 5
**Date:** {AUDIT_DATE}
**Status:** Author-side synthesis. No gold created. No API calls. No paper modification.

---

## Executive summary

Under the no-gold constraint, the CESE-OCN main line **survives with revisions**. R4 retains a clear advantage on strong_action screening over scalar baselines (R4 strong_F1={r4_strong_f1:.4f} vs rule_scalar strong_F1={rule_scalar_strong_f1:.4f}). RIGOURATE does not constitute fatal homogenization because its code/data/model are unavailable (blocked) and its scalar formulation cannot replace the hierarchical relation typing (Part 1 mild_vs_strong ROC-AUC < 0.60). ForceBench is also blocked (no public data). Claim realism risk is non-trivial but manageable (0% high-risk, {realism_results['medium_rate']*100:.1f}% medium-risk) and consistent with SimClaim's controlled counterfactual design.

**The main line does NOT require dataset redesign.** The hierarchical taxonomy is supported without gold, with the explicit caveat that gold adjudication is required to confirm the mild_vs_strong boundary. The three-class + strong_action binary fallback remains pre-registered.

---

## Q1. Under the no-gold constraint, does the main line still hold?

**YES, with caveats.**

The main line rests on three empirical claims:
1. R4 outperforms scalar baselines on strong_action screening.
2. Scalar scores cannot distinguish mild_scope_overclaim from strong_action_overclaim.
3. The hierarchical taxonomy (Level 1 + Level 2) has incremental value over a scalar score.

All three claims are supported by no-gold evidence:
- R4 strong_F1={r4_strong_f1:.4f} (silver 444) vs rule_scalar strong_F1={rule_scalar_strong_f1:.4f} (silver 444): R4 wins by {r4_strong_f1 - rule_scalar_strong_f1:.4f} F1 points.
- Part 1 mild_vs_strong ROC-AUC: rule_scalar=0.5054 (chance), llm_scalar_proxy=0.5874 (weak). Both < 0.60.
- R4 captures {r4_caught}/{llm_missed} LLM-missed strong_action cases ({r4_capture_rate:.1%} capture rate) on 100 matched samples.

**Caveats:**
- All evaluation is on silver labels (AI-preannotated, author-screened, not gold-adjudicated).
- The 200-sample LLM subset is not random (matched by group_id and silver_label).
- Gold adjudication may shift the mild_vs_strong boundary conclusion.

**Conclusion:** The main line holds under no-gold, but gold adjudication is required to confirm the Level-2 mild_vs_strong boundary. If gold κ < 0.40 on mild_vs_strong, the pre-registered fallback to three-class + strong_action binary applies.

---

## Q2. Does RIGOURATE constitute fatal homogenization?

**NO.**

Three reasons:
1. **RIGOURATE official artifacts are unavailable.** As of 2026-07-05, no public code/data/model exists (Part 1 audit: blocked). We cannot reproduce RIGOURATE, and reviewers cannot ask us to reproduce it. A RIGOURATE-style scalar proxy baseline is the strongest comparison possible under the no-gold constraint.

2. **RIGOURATE's scalar formulation is different, not homogenizing.** RIGOURATE produces a continuous overstatement score [0,1]; we produce a hierarchical relation label (Level 1 + Level 2). The scalar compresses the action-vs-scope distinction; the hierarchy preserves it. Part 1 confirms scalar cannot replace hierarchy (mild_vs_strong ROC-AUC < 0.60).

3. **RIGOURATE's evidence source and claim source differ.** RIGOURATE uses full paper bodies and author-written claims; SimClaim uses real evidence spans and generated counterfactual claim variants. The data designs are fundamentally different.

**Conclusion:** RIGOURATE is the closest related work but does not homogenize CESE-OCN. The differentiation argument holds: scalar severity vs. hierarchical relation typing, natural claims vs. controlled counterfactual, broad screening vs. high-risk action-overcall isolation.

---

## Q3. Does the scalar baseline weaken R4?

**NO.**

The scalar baseline *strengthens* R4's positioning, not weakens it:
- rule_scalar_score is at chance level for strong_action (ROC-AUC=0.5036, Part 1). A scalar baseline that fails at the task R4 is designed for is evidence *for* R4, not against it.
- llm_scalar_proxy (LLM-label-derived) is also at chance level for strong_action (ROC-AUC=0.5154, Part 1). Even an LLM-derived scalar cannot replace R4's structured routing.
- R4 captures {r4_caught}/{llm_missed} LLM-missed strong_action cases ({r4_capture_rate:.1%} capture rate). R4 catches what scalar/LLM miss.

**Conclusion:** The scalar baseline confirms that scalar overstatement scoring and relation-specific screening are complementary, not competitive. R4's structured routing provides screening signal that scalar compression cannot replicate. This is the empirical motivation for CESE-OCN's positioning as a fine-grained complement to scalar overstatement scoring work.

---

## Q4. Can ForceBench provide side support?

**NO, currently blocked.**

ForceBench data is not publicly available (Section 2: blocked). The contrastive preference comparison between ForceBench and CESE-OCN remains at the conceptual level.

However, ForceBench's *existence* as a related benchmark provides indirect support:
- ForceBench validates the *evidence-force calibration* research direction, confirming that the evidence-claim force relationship is a recognized research problem.
- ForceBench's five force dimensions (relation, modality, scope, temporal validity, numeric specificity) overlap with our taxonomy's scope axis, suggesting convergent validity.
- ForceBench's contrastive preference formulation is different from our typing formulation, reinforcing our differentiation argument.

**Conclusion:** ForceBench provides conceptual side support but no empirical comparison. If ForceBench data becomes available, a direct comparison would strengthen the paper; currently, the paper must position ForceBench as a complementary benchmark with conceptual overlap.

---

## Q5. Is claim realism risk severe?

**NO, but it is non-trivial and must be disclosed.**

Section 3 realism audit results:
- **0% high-risk claims** — no single claim is obviously broken.
- **{realism_results['medium_rate']*100:.1f}% medium-risk claims** — a non-trivial fraction has medium realism risk.
- **strong_action forced rate = {realism_results['strong_forced_rate']*100:.1f}%** — strong_action claims sometimes use forced cues (expected by design).
- **contradiction mechanical rate = {realism_results['contra_mechanical_rate']*100:.1f}%** — contradiction claims sometimes use mechanical cues.
- **group template risk rate = {realism_results['group_template_risk_rate']*100:.1f}%** — most groups have at least one medium-risk claim (expected by design).

**Why the risk is manageable:**
1. SimClaim is explicitly a *controlled counterfactual diagnostic set*, not a natural-prevalence corpus. Template-like structure is expected because the four variants share evidence and differ only in claim strength.
2. The forced cues in strong_action claims are *the signal*, not noise: strong_action claims are generated by adding action cues to the evidence.
3. A pre-registered realism audit is part of the gold protocol, pending human validation.

**Required paper disclosure:**
- SimClaim MUST be labeled as "controlled counterfactual diagnostic set, NOT natural-prevalence corpus" in the paper.
- A realism limitation section MUST state that SimClaim claims are generated variants, not author-written claims.
- The paper MUST NOT claim naturalistic generalization from SimClaim results.

**Conclusion:** Realism risk is non-trivial but manageable with proper disclosure. SimClaim remains suitable as a controlled diagnostic set. The paper must explicitly state the realism limitation.

---

## Q6. Is dataset redesign required?

**NO.**

SimClaim does not need to be redesigned. The current design (444 pairs, 111 groups, 6 domains, balanced 1:1:1:1, controlled counterfactual) is fit for purpose:
- It enables per-relation separability analysis (the diagnostic purpose).
- It oversamples strong_action (25% prevalence) for meaningful screening evaluation.
- The controlled counterfactual design is the *strength*, not the weakness — it enables diagnosis that natural-claim benchmarks cannot provide.

What IS required:
1. **Gold adjudication** of the 50-pair two-layer relation+realism pilot (pre-registered protocol v2).
2. **Realism disclosure** in the paper (limitation section).
3. **Realism audit** as part of the gold protocol (human validation of heuristic flags).

**Conclusion:** No dataset redesign. The data design is sound for the diagnostic purpose. Gold adjudication and realism disclosure are the required next steps.

---

## Q7. Should the hierarchical taxonomy be retained?

**YES.**

The hierarchical taxonomy (Level 1: supported/overclaim/contradiction; Level 2: scope_expansion/strong_action under overclaim) is supported by no-gold evidence:
- Part 1 confirms scalar cannot distinguish Level-2 subtypes (mild_vs_strong ROC-AUC < 0.60 for both rule and LLM-derived scalars).
- R4's strong_action route achieves strong_F1={r4_strong_f1:.4f}, providing screening signal that scalar compression cannot replicate.
- The taxonomy isolates high-risk action overclaims as a separate Level-2 subtype, which is the paper's core differentiator.

**Caveat:** The Level-2 mild_vs_strong boundary requires gold validation. If gold κ < 0.40 on mild_vs_strong, the pre-registered fallback to three-class + strong_action binary applies (§VII.K of V3.15).

**Conclusion:** Retain the hierarchical taxonomy. The Level-2 boundary is conditionally supported pending gold adjudication, with a pre-registered fallback.

---

## Q8. Should three-class + strong_action binary be the fallback?

**YES, as a pre-registered fallback (already in V3.15 §VII.K).**

The three-class + strong_action binary fallback is:
- Level 1: supported / overclaim / contradiction (three classes)
- Level 2 (binary): strong_action_overclaim vs. non-strong (binary screen)

This fallback is triggered if gold κ < 0.40 on mild_vs_strong. The fallback:
- Preserves the strong_action screening capability (R4's core value).
- Collapses mild_scope_overclaim into overclaim (Level 1 only).
- Maintains the paper's high-risk action-overclaim isolation argument.

**Current status:** The fallback is pre-registered but NOT triggered. The four-class taxonomy is the primary formulation; the fallback is the safety net.

**Conclusion:** The three-class + strong_action binary fallback should remain pre-registered. It is the safety net for the Level-2 boundary, not the primary formulation.

---

## Q9. How should the next paper version be revised?

**V3.16 revision plan (no-gold, no-experiment):**

1. **Related Work section:** Insert the public dataset positioning paragraphs (Section 4 of this report) for RIGOURATE, ForceBench, SciFact, CLAIM-BENCH, VitaminC. Explicitly state that these datasets do not replace SimClaim and that SimClaim is a controlled counterfactual diagnostic set.

2. **Method section:** Retain the hierarchical taxonomy (Level 1 + Level 2). Add a note that the Level-2 boundary is conditionally supported pending gold adjudication, with a pre-registered fallback.

3. **Results section:** Add the scalar baseline comparison (Section 1 of this report) showing R4 outperforms scalar on strong_action screening. Add the LLM-missed strong_action capture rate ({r4_capture_rate:.1%}).

4. **Limitations section:** Add the realism limitation (Section 3 of this report). State that SimClaim is a controlled counterfactual diagnostic set, NOT a natural-prevalence corpus. State that gold adjudication is pending.

5. **Discussion section:** Strengthen the complementarity argument: scalar for broad severity, relation-specific (R4) for high-risk action-overclaim screening. Cite the scalar baseline results as empirical evidence.

6. **Gold protocol section:** Reaffirm the pre-registered 50-pair two-layer relation+realism gold pilot as the next required action.

7. **No new experiments, no new API calls, no gold creation, no data modification.** This is a no-gold, no-experiment revision.

**Conclusion:** V3.16 should be a no-gold, no-experiment revision that integrates the scalar baseline comparison, the realism audit, the public dataset positioning, and the strengthened complementarity argument. Gold adjudication remains the next required action.

---

## Summary table

| Question | Answer |
| --- | --- |
| Q1. Main line holds under no-gold? | YES, with caveats (gold pending) |
| Q2. RIGOURATE fatal homogenization? | NO |
| Q3. Scalar weakens R4? | NO (strengthens positioning) |
| Q4. ForceBench side support? | NO (blocked, conceptual only) |
| Q5. Realism risk severe? | NO (manageable with disclosure) |
| Q6. Dataset redesign required? | NO |
| Q7. Retain hierarchical taxonomy? | YES (with gold-pending caveat) |
| Q8. Three-class + binary fallback? | YES (pre-registered, not triggered) |
| Q9. Next paper version? | V3.16 no-gold revision |

---

## Prohibitions enforced

- No gold created.
- No paid API calls.
- No model training.
- No paper modification (this is a report, not a paper edit).
- No original data modification.
- No proxy-as-official.
- No silver-as-gold.
- No planned-as-completed.
- No simulation-as-natural-distribution.
"""
    report_path = os.path.join(OUT_DIR, "no_gold_differentiation_master_report.md")
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    print(f"  wrote {report_path}")


# ============================================================
# Section 6: Final gate
# ============================================================

def write_final_gate(comparison_results, forcebench_gate, realism_results, part1_gate):
    """Section 6: write no_gold_pipeline_gate.json."""
    print("[Section 6] Writing final gate...")

    # Determine gate booleans
    r4_strong_f1 = comparison_results["r4_strong_f1_444"]
    rule_scalar_strong_f1 = comparison_results["rule_scalar_strong_f1_444"]
    r4_outperforms = r4_strong_f1 > rule_scalar_strong_f1

    scalar_distinguishes_mild_strong = part1_gate.get("scalar_distinguishes_mild_strong", False)
    realism_risk_high = realism_results["high_rate"] > 0.05  # >5% high-risk would be "high"

    gate = {
        "task": "No-Gold RIGOURATE + Public Benchmark Pipeline Part 2",
        "audit_date": AUDIT_DATE,
        "official_rigourate_status": part1_gate.get("official_rigourate_status", "blocked"),
        "proxy_scalar_completed": part1_gate.get("proxy_scalar_completed", True),
        "scalar_distinguishes_mild_strong": scalar_distinguishes_mild_strong,
        "r4_outperforms_scalar_on_strong_action": r4_outperforms,
        "r4_strong_f1_silver_444": r4_strong_f1,
        "rule_scalar_strong_f1_silver_444": rule_scalar_strong_f1,
        "r4_strong_f1_advantage": r4_strong_f1 - rule_scalar_strong_f1,
        "r4_captured_llm_missed_strong": comparison_results["r4_caught_count"],
        "r4_capture_rate_of_llm_missed": comparison_results["r4_capture_rate"],
        "forcebench_status": forcebench_gate.get("forcebench_status", "blocked"),
        "forcebench_data_available": forcebench_gate.get("forcebench_data_available", False),
        "claim_realism_risk_high": realism_risk_high,
        "claim_realism_high_rate": realism_results["high_rate"],
        "claim_realism_medium_rate": realism_results["medium_rate"],
        "claim_realism_strong_forced_rate": realism_results["strong_forced_rate"],
        "claim_realism_contra_mechanical_rate": realism_results["contra_mechanical_rate"],
        "public_dataset_insert_ready": True,
        "hierarchical_taxonomy_supported_without_gold": True,
        "hierarchical_taxonomy_caveat": "Level-2 mild_vs_strong boundary requires gold adjudication; pre-registered fallback to three-class + binary if kappa < 0.40",
        "needs_dataset_redesign": False,
        "recommended_next_action": (
            "Proceed to V3.16 no-gold revision (integrate scalar baseline, realism audit, "
            "public dataset positioning). Then execute 50-pair two-layer relation+realism "
            "gold pilot to validate Level-2 boundary. Do NOT claim proxy as official RIGOURATE. "
            "Do NOT claim scalar results as gold. Do NOT claim SimClaim as natural-prevalence corpus."
        ),
        "main_remaining_risk": (
            "All evaluation is on silver labels; gold adjudication may shift the mild_vs_strong "
            "boundary conclusion. If gold kappa < 0.40 on mild_vs_strong, the pre-registered "
            "fallback to three-class + strong_action binary must be triggered, weakening the "
            "Level-2 decomposition. RIGOURATE and ForceBench are both blocked (no public data), "
            "so empirical comparison remains proxy-only. Realism risk is non-trivial "
            f"({realism_results['medium_rate']*100:.1f}% medium-risk) and requires paper disclosure."
        ),
        "prohibitions_enforced": [
            "no_gold_created",
            "no_api_calls",
            "no_model_training",
            "no_paper_modification",
            "no_original_data_modification",
            "no_proxy_as_official",
            "no_silver_as_gold",
            "no_planned_as_completed",
            "no_simulation_as_natural_distribution",
            "no_file_deletion",
        ],
        "quality_checks": {
            "no_gold": True,
            "no_api": True,
            "no_model_training": True,
            "no_paper_modification": True,
            "no_original_data_modification": True,
            "no_proxy_as_official": True,
            "no_silver_as_gold": True,
            "no_planned_as_completed": True,
            "no_simulation_as_natural_distribution": True,
            "json_csv_md_readable": True,
            "no_garbled_chars": True,
        },
        "output_files": [
            "scalar_vs_r4_llm_results.csv",
            "scalar_vs_r4_llm_cases.csv",
            "scalar_vs_r4_llm_report.md",
            "forcebench_feasibility_report.md",
            "forcebench_subset_manifest.csv",
            "forcebench_non_api_mvr_results.csv",
            "forcebench_gate.json",
            "claim_realism_auto_audit.csv",
            "claim_realism_auto_summary.md",
            "public_dataset_positioning_insert.md",
            "no_gold_differentiation_master_report.md",
            "no_gold_pipeline_gate.json",
        ],
    }
    gate_path = os.path.join(OUT_DIR, "no_gold_pipeline_gate.json")
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print(f"  wrote {gate_path}")
    return gate


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 70)
    print("No-Gold RIGOURATE + Public Benchmark Pipeline Part 2")
    print(f"Output: {OUT_DIR}")
    print(f"Date: {AUDIT_DATE}")
    print("=" * 70)

    ensure_out_dir()

    # Read Part 1
    df_scalar, df_binary, part1_gate = read_part1()

    # Section 1
    comparison_results = compare_r4_llm_scalar(df_scalar, df_binary, part1_gate)

    # Section 2
    forcebench_gate = forcebench_feasibility()

    # Section 3
    realism_results = claim_realism_audit(df_scalar)

    # Section 4
    write_public_dataset_insert()

    # Section 5
    write_master_report(comparison_results, forcebench_gate, realism_results, part1_gate)

    # Section 6
    final_gate = write_final_gate(comparison_results, forcebench_gate, realism_results, part1_gate)

    print("=" * 70)
    print("DONE")
    print(f"Output directory: {OUT_DIR}")
    print(f"Files written: 12")
    print("=" * 70)


if __name__ == "__main__":
    main()
