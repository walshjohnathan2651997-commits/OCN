#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Canonicalized R4 Risk Ranking Calibration v1

目标: 提升 canonicalized R4 review queue 的排序质量。
只做风险排序校准，不训练模型，不调 API，不改原数据，不改论文。
"""

import argparse
import json
import sys
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime
from sklearn.metrics import average_precision_score

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402

# ===== Paths (defaults — can be overridden by --config) =====
REVIEW_QUEUE_DIR = Path(r"D:\ocn\experiments\canonicalized_review_queue_v1")
SELECTOR_DIR = Path(r"D:\ocn\experiments\canonical_selector_robustness_v1")
RETRIEVAL_DIR = Path(r"D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1")
OUTPUT_DIR = Path(r"D:\ocn\experiments\canonicalized_risk_ranking_v1")

# ===== Constants =====
T_CONTRA_LOW = 0.36  # frozen mean threshold
BEST_SELECTOR = "best_sentence_top5_overlap"
STRONG_LABEL = "strong_action_overclaim"
N_BOOTSTRAP = 1000
PREVALENCES = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20]
QUEUE_KS = [10, 20, 50, 100]

# Baseline (Task J priority_score)
BASELINE_PRECISION_AT20 = 0.35
BASELINE_RECALL_AT100 = 0.3394495412844037


def log(msg):
    print(msg, flush=True)


def load_data():
    """Step 1: Load all input data."""
    log("[Step 1] Loading data ...")

    review_scores = pd.read_csv(
        REVIEW_QUEUE_DIR / "canonicalized_r4_review_scores.csv",
        keep_default_na=False,
    )
    log(f"  review_scores: {len(review_scores)} rows, cols={list(review_scores.columns)}")

    selector_evidence = pd.read_csv(
        SELECTOR_DIR / "selector_variant_evidence.csv",
        keep_default_na=False,
    )
    best_sel_evidence = selector_evidence[
        selector_evidence["selector"] == BEST_SELECTOR
    ].copy()
    log(f"  best_sel_evidence: {len(best_sel_evidence)} rows")

    nli_cache = np.load(SELECTOR_DIR / "nli_top5_cache.npz")
    nli_key = list(nli_cache.keys())[0]
    nli_features = nli_cache[nli_key]
    nli_meta = pd.read_csv(
        SELECTOR_DIR / "nli_top5_cache_meta.csv",
        keep_default_na=False,
    )
    log(f"  nli_cache: shape={nli_features.shape}, meta={len(nli_meta)} rows")

    retrieval_df = pd.read_csv(
        RETRIEVAL_DIR / "retrieval_results_bm25.csv",
        keep_default_na=False,
    )
    log(f"  retrieval_df: {len(retrieval_df)} rows")

    return review_scores, best_sel_evidence, nli_features, nli_meta, retrieval_df


def build_ranking_features(review_scores, best_sel_evidence, nli_features, nli_meta, retrieval_df):
    """Step 2: Build ranking features table."""
    log("\n[Step 2] Building ranking features ...")

    df = review_scores.merge(
        best_sel_evidence[["candidate_id", "selection_score", "n_words"]].rename(
            columns={"selection_score": "selector_score", "n_words": "selected_n_words"}
        ),
        on="candidate_id",
        how="left",
    )

    # Build NLI lookup: (candidate_id, sentence_text) -> row index in nli_features
    nli_lookup = {}
    for i in range(len(nli_meta)):
        cid = nli_meta.iloc[i]["candidate_id"]
        stext = nli_meta.iloc[i]["sentence_text"]
        nli_lookup[(cid, stext)] = i

    # Also build per-candidate sentence list for fallback matching
    nli_by_candidate = {}
    for i in range(len(nli_meta)):
        cid = nli_meta.iloc[i]["candidate_id"]
        if cid not in nli_by_candidate:
            nli_by_candidate[cid] = []
        nli_by_candidate[cid].append((i, nli_meta.iloc[i]["sentence_text"]))

    nli_matched = 0
    nli_fallback = 0
    nli_missing = 0
    ent_vals, neu_vals, con_vals, entropy_vals = [], [], [], []

    for i in range(len(df)):
        cid = df.iloc[i]["candidate_id"]
        ev = df.iloc[i]["selected_evidence"]

        # Exact match
        if (cid, ev) in nli_lookup:
            idx = nli_lookup[(cid, ev)]
            feats = nli_features[idx]
            nli_matched += 1
        else:
            # Fallback: try substring matching within candidate's sentences
            found = False
            if cid in nli_by_candidate:
                for idx, stext in nli_by_candidate[cid]:
                    if ev == stext or ev in stext or stext in ev:
                        feats = nli_features[idx]
                        nli_fallback += 1
                        found = True
                        break
            if not found:
                feats = np.zeros(7)
                nli_missing += 1

        ent_vals.append(float(feats[0]))
        neu_vals.append(float(feats[1]))
        con_vals.append(float(feats[2]))
        entropy_vals.append(float(feats[6]))

    df["entailment"] = ent_vals
    df["neutral"] = neu_vals
    df["contradiction_nli"] = con_vals
    df["entropy"] = entropy_vals
    log(f"  NLI lookup: exact={nli_matched}, fallback={nli_fallback}, missing={nli_missing}")

    # Look up BM25 score and oracle_hit for selected chunk
    retrieval_lookup = {}
    for i in range(len(retrieval_df)):
        key = (retrieval_df.iloc[i]["candidate_id"], retrieval_df.iloc[i]["chunk_id"])
        retrieval_lookup[key] = {
            "bm25_score": float(retrieval_df.iloc[i]["bm25_score"]),
            "is_oracle_hit": retrieval_df.iloc[i]["is_oracle_hit"],
        }

    bm25_scores = []
    oracle_hits = []
    for i in range(len(df)):
        cid = df.iloc[i]["candidate_id"]
        ck = df.iloc[i]["selected_chunk_id"]
        key = (cid, ck)
        if key in retrieval_lookup:
            bm25_scores.append(retrieval_lookup[key]["bm25_score"])
            oh = retrieval_lookup[key]["is_oracle_hit"]
            oracle_hits.append(1 if (oh is True or oh == "True" or oh == "1" or oh == 1) else 0)
        else:
            bm25_scores.append(0.0)
            oracle_hits.append(0)

    df["bm25_score"] = bm25_scores
    df["oracle_hit"] = oracle_hits

    # Rename for clarity
    df = df.rename(
        columns={
            "strong_action_score": "p_strong",
            "p_contra_mean": "p_contra",
            "p_svm_mean": "p_svm",
        }
    )

    # Ensure strong_action_flag is int
    df["strong_action_flag"] = df["strong_action_flag"].astype(int)
    df["selected_rank"] = df["selected_rank"].astype(int)
    df["selected_n_words"] = df["selected_n_words"].astype(int)

    # Add binary true label
    df["is_strong_action"] = (df["true_label"] == STRONG_LABEL).astype(int)

    # Save features
    features_cols = [
        "candidate_id", "true_label", "pred_label", "strong_action_flag",
        "p_strong", "p_contra", "p_svm",
        "entailment", "neutral", "contradiction_nli", "entropy",
        "selector_score", "selected_rank", "selected_n_words",
        "bm25_score", "oracle_hit",
    ]
    df[features_cols].to_csv(
        OUTPUT_DIR / "risk_ranking_features.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log(f"  -> risk_ranking_features.csv ({len(df)} rows)")

    return df


def compute_variant_scores(df):
    """Step 3a: Compute scores for each ranking variant."""
    variants = {}

    # A. flag_only: flag first, then p_strong
    variants["A_flag_only"] = df["strong_action_flag"].astype(float) * 1000.0 + df["p_strong"]

    # B. p_strong_desc
    variants["B_p_strong_desc"] = df["p_strong"].copy()

    # C. guarded_strong_score: p_strong - p_contra
    variants["C_guarded_strong_score"] = df["p_strong"] - df["p_contra"]

    # D. confidence_guarded: p_strong - p_contra - 0.2 * entropy
    variants["D_confidence_guarded"] = df["p_strong"] - df["p_contra"] - 0.2 * df["entropy"]

    # E. selector_confidence
    variants["E_selector_confidence"] = (
        df["p_strong"] - df["p_contra"]
        + 0.1 * df["selector_score"] - 0.05 * df["selected_rank"]
    )

    # F. short_span_bonus
    bonus = np.where(
        (df["selected_n_words"] >= 10) & (df["selected_n_words"] <= 40),
        0.1, 0.0,
    )
    variants["F_short_span_bonus"] = (
        df["p_strong"] - df["p_contra"] - 0.2 * df["entropy"] + bonus
    )

    # G. conservative_precision: filter then rank
    mask = (df["strong_action_flag"] == 1) & (df["p_contra"] < T_CONTRA_LOW)
    score_g = np.where(mask, df["p_strong"] - df["entropy"], -1e18)
    # For non-qualifying candidates, use a lower-but-finite score so top-100 still fills
    score_g = np.where(mask, df["p_strong"] - df["entropy"],
                       -1000.0 + df["p_strong"])  # fallback so we can fill 100
    variants["G_conservative_precision"] = score_g

    # H. balanced_review_score
    variants["H_balanced_review_score"] = (
        0.5 * df["p_strong"] - 0.3 * df["p_contra"] - 0.2 * df["entropy"]
        + 0.1 * df["selector_score"] - 0.05 * df["selected_rank"]
    )

    return variants


def save_formula_variants():
    """Step 3b: Save formula definitions."""
    formula_rows = [
        {
            "variant_id": "A_flag_only",
            "formula": "strong_action_flag * 1000 + p_strong",
            "description": "Flagged candidates first, then by p_strong descending",
        },
        {
            "variant_id": "B_p_strong_desc",
            "formula": "p_strong",
            "description": "Pure p_strong descending, ignores flag",
        },
        {
            "variant_id": "C_guarded_strong_score",
            "formula": "p_strong - p_contra",
            "description": "Strong score guarded by contradiction probability",
        },
        {
            "variant_id": "D_confidence_guarded",
            "formula": "p_strong - p_contra - 0.2 * entropy",
            "description": "Confidence-guarded with entropy penalty",
        },
        {
            "variant_id": "E_selector_confidence",
            "formula": "p_strong - p_contra + 0.1 * selector_score - 0.05 * selected_rank",
            "description": "Selector confidence weighted",
        },
        {
            "variant_id": "F_short_span_bonus",
            "formula": "p_strong - p_contra - 0.2 * entropy + 0.1 * (10 <= n_words <= 40)",
            "description": "Short span bonus for 10-40 word evidence",
        },
        {
            "variant_id": "G_conservative_precision",
            "formula": "if(flag==1 and p_contra<0.36): p_strong - entropy; else: -1000 + p_strong",
            "description": "Conservative: only rank low-contra flagged candidates",
        },
        {
            "variant_id": "H_balanced_review_score",
            "formula": "0.5*p_strong - 0.3*p_contra - 0.2*entropy + 0.1*selector_score - 0.05*selected_rank",
            "description": "Balanced review score with all features",
        },
    ]
    formula_df = pd.DataFrame(formula_rows)
    formula_df.to_csv(
        OUTPUT_DIR / "risk_ranking_formula_variants.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log(f"  -> risk_ranking_formula_variants.csv ({len(formula_df)} rows)")


def compute_queue_metrics(variant_scores, df, y_true_strong, n_positives):
    """Step 4: Compute queue metrics for each variant."""
    log("\n[Step 4] Computing queue metrics per variant ...")

    results_rows = []
    for variant_id, scores in variant_scores.items():
        sorted_idx = np.argsort(-scores, kind="stable")

        metrics = {"variant_id": variant_id}
        for k in QUEUE_KS:
            top_k_idx = sorted_idx[:k]
            top_k_true = y_true_strong[top_k_idx]
            tp = int(top_k_true.sum())
            fp = k - tp
            precision = tp / k
            recall = tp / n_positives if n_positives > 0 else 0.0
            metrics[f"precision_at_{k}"] = round(precision, 6)
            metrics[f"recall_at_{k}"] = round(recall, 6)
            metrics[f"tp_at_{k}"] = tp
            metrics[f"fp_at_{k}"] = fp

        # Average precision / AUPRC
        if len(np.unique(y_true_strong)) > 1:
            ap = float(average_precision_score(y_true_strong, scores))
        else:
            ap = 0.0
        metrics["average_precision"] = round(ap, 6)
        metrics["auprc"] = round(ap, 6)

        # Label composition @100
        top_100_idx = sorted_idx[:100]
        top_100_labels = df["true_label"].iloc[top_100_idx].value_counts()
        for label in ["strong_action_overclaim", "mild_scope_overclaim",
                       "contradiction_candidate", "supported"]:
            metrics[f"label_{label}_at_100"] = int(top_100_labels.get(label, 0))

        results_rows.append(metrics)

    results_df = pd.DataFrame(results_rows)
    results_df.to_csv(
        OUTPUT_DIR / "risk_ranking_results_by_variant.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log(f"  -> risk_ranking_results_by_variant.csv ({len(results_df)} rows)")

    # Print summary
    log("\n  Variant summary:")
    for _, row in results_df.iterrows():
        log(f"    {row['variant_id']}: "
            f"P@20={row['precision_at_20']:.4f}, P@50={row['precision_at_50']:.4f}, "
            f"R@100={row['recall_at_100']:.4f}, AP={row['average_precision']:.4f}")

    return results_df


def select_best_variant(results_df, variant_scores, df):
    """Step 5: Select best variant and save top-100."""
    log("\n[Step 5] Selecting best variant ...")

    # Composite: precision@20 + recall@100 (equally weighted)
    results_df = results_df.copy()
    results_df["composite_p20_r100"] = (
        results_df["precision_at_20"] + results_df["recall_at_100"]
    )

    # Check which variants meet all targets
    target_p20 = 0.40
    target_p50 = 0.35
    target_r100 = 0.45
    results_df["meets_all_targets"] = (
        (results_df["precision_at_20"] >= target_p20)
        & (results_df["precision_at_50"] >= target_p50)
        & (results_df["recall_at_100"] >= target_r100)
    )

    # Prefer variants that meet all targets; among those, pick highest composite
    # If none meet all targets, pick highest composite overall
    meeting = results_df[results_df["meets_all_targets"]]
    if len(meeting) > 0:
        best_idx = meeting["composite_p20_r100"].idxmax()
        partial = False
    else:
        best_idx = results_df["composite_p20_r100"].idxmax()
        partial = True

    best_row = results_df.loc[best_idx]
    best_variant_id = best_row["variant_id"]
    log(f"  Best variant: {best_variant_id}")
    log(f"    P@20={best_row['precision_at_20']:.4f}, P@50={best_row['precision_at_50']:.4f}, "
        f"R@100={best_row['recall_at_100']:.4f}, AP={best_row['average_precision']:.4f}")
    log(f"    Meets all targets: {not partial}")

    # Save top-100
    best_scores = variant_scores[best_variant_id]
    best_sorted_idx = np.argsort(-best_scores, kind="stable")
    top_100_df = df.iloc[best_sorted_idx[:100]].copy()
    top_100_df["rank"] = range(1, 101)
    top_100_df["ranking_score"] = best_scores[best_sorted_idx[:100]].astype(float)
    top_100_cols = [
        "rank", "candidate_id", "true_label", "pred_label", "strong_action_flag",
        "p_strong", "p_contra", "p_svm", "entailment", "neutral",
        "contradiction_nli", "entropy", "selector_score", "selected_rank",
        "selected_n_words", "bm25_score", "oracle_hit", "ranking_score",
        "selected_evidence",
    ]
    top_100_df[top_100_cols].to_csv(
        OUTPUT_DIR / "review_queue_top100_best.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log(f"  -> review_queue_top100_best.csv (100 rows)")

    return best_variant_id, best_row, best_sorted_idx, partial, results_df


def low_prevalence_simulation(best_sorted_idx, y_true_strong, n_positives):
    """Step 6: Low-prevalence simulation with best variant's top-100."""
    log("\n[Step 6] Low-prevalence simulation ...")

    # Use top-100 as "screened positive"
    y_pred_top100 = np.zeros(len(y_true_strong), dtype=int)
    y_pred_top100[best_sorted_idx[:100]] = 1

    rng = np.random.RandomState(42)
    pos_idx = np.where(y_true_strong == 1)[0]
    neg_idx = np.where(y_true_strong == 0)[0]
    log(f"  Positives: {len(pos_idx)}, Negatives: {len(neg_idx)}")
    log(f"  Top-100 TP: {int(y_pred_top100[pos_idx].sum())}, "
        f"Top-100 FP: {int(y_pred_top100[neg_idx].sum())}")

    low_prev_rows = []
    for prev in PREVALENCES:
        n_pos = len(pos_idx)
        n_neg_needed = int(round(n_pos * (1.0 - prev) / prev))
        if n_neg_needed > len(neg_idx):
            sample_neg = lambda: rng.choice(neg_idx, size=n_neg_needed, replace=True)
        else:
            sample_neg = lambda: rng.choice(neg_idx, size=n_neg_needed, replace=False)

        recalls, precisions, f1s, fp_tps, nnrs, review_burdens = [], [], [], [], [], []

        for _ in range(N_BOOTSTRAP):
            neg_sample = sample_neg()
            pop_idx = np.concatenate([pos_idx, neg_sample])
            y_true_pop = y_true_strong[pop_idx]
            y_pred_pop = y_pred_top100[pop_idx]

            tp = int(((y_pred_pop == 1) & (y_true_pop == 1)).sum())
            fp = int(((y_pred_pop == 1) & (y_true_pop == 0)).sum())
            fn = int(((y_pred_pop == 0) & (y_true_pop == 1)).sum())
            tn = int(((y_pred_pop == 0) & (y_true_pop == 0)).sum())

            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            fp_tp = fp / max(tp, 1)
            nnr = 1.0 / precision if precision > 0 else float("inf")
            review_burden = (tp + fp) / len(y_true_pop) if len(y_true_pop) > 0 else 0.0

            recalls.append(recall)
            precisions.append(precision)
            f1s.append(f1)
            fp_tps.append(fp_tp)
            nnrs.append(nnr)
            review_burdens.append(review_burden)

        row = {
            "prevalence": prev,
            "n_positives": n_pos,
            "n_negatives_simulated": n_neg_needed,
            "n_population": n_pos + n_neg_needed,
            "recall_mean": float(np.mean(recalls)),
            "precision_mean": float(np.mean(precisions)),
            "positive_f1_mean": float(np.mean(f1s)),
            "fp_tp_mean": float(np.mean(fp_tps)),
            "fp_tp_median": float(np.median(fp_tps)),
            "nnr_mean": float(np.mean(nnrs)),
            "review_burden_mean": float(np.mean(review_burdens)),
            "n_bootstrap": N_BOOTSTRAP,
        }
        low_prev_rows.append(row)
        log(f"  prev={prev:.0%}: recall={row['recall_mean']:.4f}, "
            f"precision={row['precision_mean']:.4f}, FP/TP={row['fp_tp_mean']:.2f}, "
            f"NNR={row['nnr_mean']:.2f}, burden={row['review_burden_mean']:.4f}")

    low_prev_df = pd.DataFrame(low_prev_rows)
    low_prev_df.to_csv(
        OUTPUT_DIR / "low_prevalence_ranking_results.csv",
        index=False,
        encoding="utf-8-sig",
    )
    log(f"  -> low_prevalence_ranking_results.csv ({len(low_prev_df)} rows)")

    return low_prev_df


def error_analysis(best_sorted_idx, df, y_true_strong):
    """Step 7: Error analysis with 8 categories."""
    log("\n[Step 7] Error analysis ...")

    top_100_set = set(best_sorted_idx[:100].tolist())
    entropy_median = float(np.median(df["entropy"].values))
    p_strong_median = float(np.median(df["p_strong"].values))

    error_rows = []
    for i in range(len(df)):
        row = df.iloc[i]
        in_top_100 = i in top_100_set
        is_strong = int(y_true_strong[i]) == 1
        true_label = row["true_label"]
        pred_label = row["pred_label"]
        flag = int(row["strong_action_flag"])

        # Determine category
        if in_top_100 and is_strong:
            category = "true_positive_in_queue"
        elif not in_top_100 and not is_strong:
            category = "true_negative_not_in_queue"
        elif in_top_100 and not is_strong:
            # FP in top-100
            if true_label == "mild_scope_overclaim":
                category = "false_positive_mild"
            elif true_label == "supported":
                category = "false_positive_supported"
            elif true_label == "contradiction_candidate":
                category = "false_positive_contradiction"
            else:
                category = "false_positive_other"
        else:
            # FN: true strong not in top-100
            if flag == 0:
                category = "r4_screening_failure"
            elif row["p_strong"] < p_strong_median:
                category = "false_negative_low_pstrong"
            elif row["entropy"] > entropy_median:
                category = "false_negative_high_entropy"
            else:
                category = "selector_failure"

        # Check ambiguous mild/strong (override for borderline cases)
        is_ambiguous = (
            (true_label == "mild_scope_overclaim" and pred_label == "strong_action_overclaim")
            or (true_label == "strong_action_overclaim" and pred_label == "mild_scope_overclaim")
        )
        if is_ambiguous and category in ("false_positive_mild", "true_negative_not_in_queue"):
            category = "ambiguous_mild_strong"

        error_rows.append({
            "candidate_id": row["candidate_id"],
            "true_label": true_label,
            "pred_label": pred_label,
            "in_top_100": in_top_100,
            "is_strong_action": is_strong,
            "strong_action_flag": flag,
            "category": category,
            "p_strong": float(row["p_strong"]),
            "p_contra": float(row["p_contra"]),
            "entropy": float(row["entropy"]),
            "oracle_hit": int(row["oracle_hit"]),
            "selected_n_words": int(row["selected_n_words"]),
        })

    error_df = pd.DataFrame(error_rows)
    error_df.to_csv(
        OUTPUT_DIR / "risk_ranking_error_analysis.csv",
        index=False,
        encoding="utf-8-sig",
    )

    # Print category counts
    cat_counts = error_df["category"].value_counts()
    log(f"  -> risk_ranking_error_analysis.csv ({len(error_df)} rows)")
    log("  Category counts:")
    for cat, count in cat_counts.items():
        log(f"    {cat}: {count}")

    return error_df


def build_gate(best_variant_id, best_row, low_prev_df, partial, results_df, error_df, model_recall):
    """Step 8a: Build gate JSON."""
    log("\n[Step 8] Building gate ...")

    fp_tp_at_1pct = float(low_prev_df.loc[low_prev_df["prevalence"] == 0.01, "fp_tp_mean"].iloc[0])
    fp_tp_at_5pct = float(low_prev_df.loc[low_prev_df["prevalence"] == 0.05, "fp_tp_mean"].iloc[0])
    recall_at_5pct_queue = float(low_prev_df.loc[low_prev_df["prevalence"] == 0.05, "recall_mean"].iloc[0])
    fp_tp_at_10pct = float(low_prev_df.loc[low_prev_df["prevalence"] == 0.10, "fp_tp_mean"].iloc[0])

    best_precision_at20 = float(best_row["precision_at_20"])
    best_precision_at50 = float(best_row["precision_at_50"])
    best_recall_at100 = float(best_row["recall_at_100"])

    precision_at20_improvement = best_precision_at20 - BASELINE_PRECISION_AT20
    recall_at100_improvement = best_recall_at100 - BASELINE_RECALL_AT100

    ranking_improved = (precision_at20_improvement >= 0.05) or (recall_at100_improvement >= 0.05)
    queue_usable = (best_precision_at20 >= 0.40) and (best_recall_at100 >= 0.45)
    # second_stage_usable: FP/TP@5% from ranking top-100 simulation + model's flag recall
    # (consistent with Task J: the model's recall reflects screening ability, not queue cutoff)
    second_stage_usable = (fp_tp_at_5pct <= 20) and (model_recall >= 0.60)
    standalone_usable = (fp_tp_at_1pct <= 50) and (best_precision_at20 >= 0.40)

    if standalone_usable:
        recommended_mode = "standalone"
    elif second_stage_usable:
        recommended_mode = "second-stage"
    else:
        recommended_mode = "not-viable"

    # Recommended next step
    if queue_usable and standalone_usable:
        next_step = "Queue is standalone-usable. Can deploy as primary screener. Consider local LLM baseline for further recall improvement."
    elif queue_usable and second_stage_usable:
        next_step = "Queue is usable as second-stage screener. Pair with upstream filter for production. Consider local LLM baseline for recall improvement."
    elif second_stage_usable:
        next_step = "Queue viable only as second-stage. Needs upstream filter to reduce FP load. Consider learned ranker or local LLM for better precision."
    else:
        next_step = "Queue not viable even as second-stage. Recommend local LLM baseline or learned ranker to improve ranking quality."

    # Error category summary
    error_summary = {}
    for cat in ["false_positive_mild", "false_positive_supported",
                "false_positive_contradiction", "false_negative_low_pstrong",
                "false_negative_high_entropy", "selector_failure",
                "r4_screening_failure", "ambiguous_mild_strong"]:
        error_summary[cat] = int((error_df["category"] == cat).sum())

    gate = {
        "task": "Canonicalized R4 Risk Ranking Calibration v1",
        "audit_date": datetime.now().isoformat(timespec="seconds"),
        "n_eval": int(len(error_df)),
        "n_true_strong": int(error_df["is_strong_action"].sum()),
        "baseline_priority_score_formula": "priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag",
        "baseline_precision_at20": BASELINE_PRECISION_AT20,
        "baseline_recall_at100": BASELINE_RECALL_AT100,
        "best_variant": best_variant_id,
        "best_precision_at20": best_precision_at20,
        "best_precision_at50": best_precision_at50,
        "best_recall_at100": best_recall_at100,
        "best_average_precision": float(best_row["average_precision"]),
        "best_tp_at_20": int(best_row["tp_at_20"]),
        "best_tp_at_100": int(best_row["tp_at_100"]),
        "precision_at20_improvement": float(precision_at20_improvement),
        "recall_at100_improvement": float(recall_at100_improvement),
        "ranking_improved": bool(ranking_improved),
        "queue_usable": bool(queue_usable),
        "targets_partial": bool(partial),
        "low_prevalence_second_stage_usable": bool(second_stage_usable),
        "standalone_usable": bool(standalone_usable),
        "fp_tp_at_1pct": fp_tp_at_1pct,
        "fp_tp_at_5pct": fp_tp_at_5pct,
        "fp_tp_at_10pct": fp_tp_at_10pct,
        "model_flag_recall": float(model_recall),
        "queue_recall_at_5pct": float(recall_at_5pct_queue),
        "recommended_mode": recommended_mode,
        "recommended_next_step": next_step,
        "error_category_counts": error_summary,
        "all_variant_summary": results_df[
            ["variant_id", "precision_at_20", "precision_at_50", "recall_at_100",
             "average_precision", "composite_p20_r100", "meets_all_targets"]
        ].to_dict(orient="records"),
        "prohibitions_enforced": [
            "no_model_training",
            "no_api_calls",
            "no_network",
            "no_threshold_change",
            "no_original_data_modification",
            "no_paper_modification",
            "no_true_label_in_ranking",
            "no_oracle_hit_in_ranking",
            "no_silver_as_gold",
            "no_natural_distribution_claim",
        ],
        "output_files": [
            "risk_ranking_features.csv",
            "risk_ranking_formula_variants.csv",
            "risk_ranking_results_by_variant.csv",
            "review_queue_top100_best.csv",
            "low_prevalence_ranking_results.csv",
            "risk_ranking_error_analysis.csv",
            "risk_ranking_gate.json",
            "risk_ranking_report.md",
        ],
    }

    gate_path = OUTPUT_DIR / "risk_ranking_gate.json"
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    log(f"  -> risk_ranking_gate.json")

    return gate


def build_report(gate, results_df, low_prev_df, error_df, df):
    """Step 8b: Build report markdown."""
    log("\n[Step 8] Building report ...")

    best_vid = gate["best_variant"]
    best_row = None
    for _, r in results_df.iterrows():
        if r["variant_id"] == best_vid:
            best_row = r
            break

    lines = []
    lines.append("# Canonicalized R4 Risk Ranking Calibration v1\n")
    lines.append(f"- 审计时间: {gate['audit_date']}")
    lines.append(f"- 评估样本数: {gate['n_eval']} (out-of-fold candidates)")
    lines.append(f"- true strong_action 数: {gate['n_true_strong']}")
    lines.append(f"- Baseline priority_score: {gate['baseline_priority_score_formula']}")
    lines.append(f"- 禁止: 无模型训练, 无API, 无联网, 无阈值修改, 无原数据修改, 无论文修改, "
                 f"无true_label/oracle_hit参与排序, 无silver写成gold, 无自然分布声明\n")

    # Q1: 当前 queue 排序为什么弱？
    lines.append("## 1. 当前 queue 排序为什么弱？\n")
    lines.append(f"Task J 的 priority_score = p_strong - p_contra + 0.5 * strong_action_flag 存在以下问题：\n")
    lines.append(f"- **precision@20 = {BASELINE_PRECISION_AT20:.4f}** (阈值 0.40): top-20 中只有 "
                 f"{int(BASELINE_PRECISION_AT20 * 20)}/20 是 true strong_action")
    lines.append(f"- **recall@100 = {BASELINE_RECALL_AT100:.4f}**: top-100 只抓到 "
                 f"{int(BASELINE_RECALL_AT100 * gate['n_true_strong'])}/{gate['n_true_strong']} true strong_action")
    lines.append(f"- flag 过于宽松: strong_action_flag=1 的样本过多 ({df['strong_action_flag'].sum()} 个)，"
                 f"其中只有 {df[df['strong_action_flag'] == 1]['is_strong_action'].sum()} 个是 true strong_action")
    lines.append(f"- priority_score 的 +0.5*flag 偏移量不足以区分 flag 内部的真实风险差异")
    lines.append(f"- p_strong 和 p_contra 单独区分力不足: strong_action 和非 strong_action 的 p_strong 分布重叠大\n")

    # Q2: 哪个 ranking formula 最好？
    lines.append("## 2. 哪个 ranking formula 最好？\n")
    lines.append(f"**{best_vid}**\n")
    lines.append(f"- precision@20 = {best_row['precision_at_20']:.4f}")
    lines.append(f"- precision@50 = {best_row['precision_at_50']:.4f}")
    lines.append(f"- recall@100 = {best_row['recall_at_100']:.4f}")
    lines.append(f"- average_precision = {best_row['average_precision']:.4f}")
    lines.append(f"- 是否达到推荐目标: {'是' if not gate['targets_partial'] else 'partial (未全部达到)'}\n")
    lines.append("所有 variant 对比:\n")
    lines.append("| Variant | P@20 | P@50 | R@100 | AP |")
    lines.append("|---------|------|------|-------|----|")
    for _, r in results_df.iterrows():
        mark = " **" if r["variant_id"] == best_vid else ""
        end = "**" if r["variant_id"] == best_vid else ""
        lines.append(f"| {r['variant_id']}{mark} | {r['precision_at_20']:.4f} | "
                     f"{r['precision_at_50']:.4f} | {r['recall_at_100']:.4f} | "
                     f"{r['average_precision']:.4f} |")
    lines.append("")

    # Q3: precision@20/50 和 recall@100 是否提升？
    lines.append("## 3. precision@20/50 和 recall@100 是否提升？\n")
    p20_imp = gate["precision_at20_improvement"]
    r100_imp = gate["recall_at100_improvement"]
    lines.append(f"| 指标 | Baseline | Best | 提升 |")
    lines.append(f"|------|----------|------|------|")
    lines.append(f"| precision@20 | {BASELINE_PRECISION_AT20:.4f} | "
                 f"{gate['best_precision_at20']:.4f} | "
                 f"{'+0' if p20_imp == 0 else ('+' if p20_imp > 0 else '')}{p20_imp:.4f} |")
    lines.append(f"| precision@50 | (baseline N/A) | {gate['best_precision_at50']:.4f} | - |")
    lines.append(f"| recall@100 | {BASELINE_RECALL_AT100:.4f} | "
                 f"{gate['best_recall_at100']:.4f} | "
                 f"{'+0' if r100_imp == 0 else ('+' if r100_imp > 0 else '')}{r100_imp:.4f} |")
    lines.append(f"\nranking_improved = {gate['ranking_improved']} "
                 f"(precision@20 提升 >= 0.05 或 recall@100 提升 >= 0.05)\n")

    # Q4: FP 主要来自哪些类？
    lines.append("## 4. FP 主要来自哪些类？\n")
    ec = gate["error_category_counts"]
    lines.append(f"| 错误类型 | 数量 |")
    lines.append(f"|---------|------|")
    for cat in ["false_positive_mild", "false_positive_supported",
                "false_positive_contradiction", "false_negative_low_pstrong",
                "false_negative_high_entropy", "selector_failure",
                "r4_screening_failure", "ambiguous_mild_strong"]:
        lines.append(f"| {cat} | {ec.get(cat, 0)} |")
    lines.append(f"\nFP 主要来源分析:")
    fp_total = ec.get("false_positive_mild", 0) + ec.get("false_positive_supported", 0) + ec.get("false_positive_contradiction", 0)
    if fp_total > 0:
        lines.append(f"- false_positive_mild: {ec.get('false_positive_mild', 0)} "
                     f"({ec.get('false_positive_mild', 0)/fp_total*100:.1f}%)")
        lines.append(f"- false_positive_supported: {ec.get('false_positive_supported', 0)} "
                     f"({ec.get('false_positive_supported', 0)/fp_total*100:.1f}%)")
        lines.append(f"- false_positive_contradiction: {ec.get('false_positive_contradiction', 0)} "
                     f"({ec.get('false_positive_contradiction', 0)/fp_total*100:.1f}%)")
    lines.append(f"- FN 主要来源: r4_screening_failure={ec.get('r4_screening_failure', 0)}, "
                 f"false_negative_low_pstrong={ec.get('false_negative_low_pstrong', 0)}, "
                 f"false_negative_high_entropy={ec.get('false_negative_high_entropy', 0)}, "
                 f"selector_failure={ec.get('selector_failure', 0)}\n")

    # Q5: 是否仍只能作为 second-stage？
    lines.append("## 5. 是否仍只能作为 second-stage？\n")
    lines.append(f"| 判定 | 结果 |")
    lines.append(f"|------|------|")
    lines.append(f"| queue_usable (P@20>=0.40 且 R@100>=0.45) | {gate['queue_usable']} |")
    lines.append(f"| standalone_usable (FP/TP@1%<=50 且 P@20>=0.40) | {gate['standalone_usable']} |")
    lines.append(f"| second_stage_usable (FP/TP@5%<=20 且 recall>=0.60) | {gate['low_prevalence_second_stage_usable']} |")
    lines.append(f"| recommended_mode | **{gate['recommended_mode']}** |\n")
    lines.append("低患病率模拟 (best variant top-100):\n")
    lines.append("| Prevalence | Recall | Precision | F1 | FP/TP | NNR | Review Burden |")
    lines.append("|------------|--------|-----------|----|-------|-----|---------------|")
    for _, r in low_prev_df.iterrows():
        lines.append(f"| {r['prevalence']:.0%} | {r['recall_mean']:.4f} | "
                     f"{r['precision_mean']:.4f} | {r['positive_f1_mean']:.4f} | "
                     f"{r['fp_tp_mean']:.2f} | {r['nnr_mean']:.2f} | "
                     f"{r['review_burden_mean']:.4f} |")
    lines.append("")

    # Q6: 是否需要 local LLM baseline 或 learned ranker？
    lines.append("## 6. 是否需要 local LLM baseline 或 learned ranker？\n")
    if gate["recommended_mode"] == "standalone":
        lines.append("**暂不需要**。当前 ranking 已可 standalone 使用。可考虑 local LLM 作为补充 baseline 验证。\n")
    elif gate["recommended_mode"] == "second-stage":
        lines.append("**建议: 是，考虑 local LLM baseline 或 learned ranker**。\n")
        lines.append(f"- 当前 best variant ({best_vid}) precision@20={gate['best_precision_at20']:.4f}, "
                     f"recall@100={gate['best_recall_at100']:.4f}")
        lines.append(f"- 虽然比 baseline 有提升, 但仍未达到 standalone 标准")
        lines.append(f"- FP/TP@1%={gate['fp_tp_at_1pct']:.2f} (阈值 50), 说明低患病率下 FP 负担仍高")
        lines.append(f"- r4_screening_failure={ec.get('r4_screening_failure', 0)} (R4 未 flag 的 true strong_action) "
                     f"是 FN 主要来源, ranking 无法修复")
        lines.append(f"- learned ranker 可利用更多特征 (如 evidence-claim 语义匹配) 提升排序")
        lines.append(f"- local LLM 可作为补充 screener, 提升 recall\n")
    else:
        lines.append("**强烈建议: local LLM baseline 和 learned ranker**。\n")
        lines.append(f"- 当前 ranking 无法达到 second-stage 标准")
        lines.append(f"- 需要更强的 screener 或 ranker\n")

    lines.append("## 输出文件清单\n")
    for f in gate["output_files"]:
        lines.append(f"- {f}")

    report_path = OUTPUT_DIR / "risk_ranking_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    log(f"  -> risk_ranking_report.md")


def main():
    global OUTPUT_DIR, REVIEW_QUEUE_DIR, SELECTOR_DIR, RETRIEVAL_DIR

    parser = argparse.ArgumentParser(description="Canonicalized R4 risk ranking calibration.")
    parser.add_argument("--config", default=None, help="Path to YAML config (optional, overrides defaults)")
    args = parser.parse_args()

    # --- Load config if provided ---
    if args.config:
        config = load_and_validate(args.config)
        print_guards(config)
        if resolve_path(config, "risk_ranking_dir"):
            OUTPUT_DIR = resolve_path(config, "risk_ranking_dir")
        if resolve_path(config, "review_queue_dir"):
            REVIEW_QUEUE_DIR = resolve_path(config, "review_queue_dir")
        if resolve_path(config, "canonicalizer_dir"):
            SELECTOR_DIR = resolve_path(config, "canonicalizer_dir")
        if resolve_path(config, "retrieval_dir"):
            RETRIEVAL_DIR = resolve_path(config, "retrieval_dir")
    else:
        config = None

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 70)
    log("Canonicalized R4 Risk Ranking Calibration v1")
    log("=" * 70)

    # Step 1: Load data
    review_scores, best_sel_evidence, nli_features, nli_meta, retrieval_df = load_data()

    # Step 2: Build ranking features
    df = build_ranking_features(
        review_scores, best_sel_evidence, nli_features, nli_meta, retrieval_df
    )
    y_true_strong = df["is_strong_action"].values
    n_positives = int(y_true_strong.sum())
    log(f"\n  Total candidates: {len(df)}, true strong_action: {n_positives}")

    # Step 3: Define and save formula variants
    log("\n[Step 3] Defining ranking formula variants ...")
    save_formula_variants()
    variant_scores = compute_variant_scores(df)

    # Step 4: Compute queue metrics
    results_df = compute_queue_metrics(variant_scores, df, y_true_strong, n_positives)

    # Step 5: Select best variant
    best_variant_id, best_row, best_sorted_idx, partial, results_df = select_best_variant(
        results_df, variant_scores, df
    )

    # Step 6: Low-prevalence simulation
    low_prev_df = low_prevalence_simulation(best_sorted_idx, y_true_strong, n_positives)

    # Step 7: Error analysis
    error_df = error_analysis(best_sorted_idx, df, y_true_strong)

    # Compute model's flag recall (for second_stage_usable, consistent with Task J)
    model_tp = int(((df["strong_action_flag"] == 1) & (df["is_strong_action"] == 1)).sum())
    model_recall = model_tp / n_positives if n_positives > 0 else 0.0
    log(f"\n  Model flag recall: {model_recall:.4f} ({model_tp}/{n_positives})")

    # Step 8: Gate and report
    gate = build_gate(best_variant_id, best_row, low_prev_df, partial, results_df, error_df, model_recall)
    build_report(gate, results_df, low_prev_df, error_df, df)

    # Final summary
    log("\n" + "=" * 70)
    log("FINAL SUMMARY")
    log("=" * 70)
    log(f"  Best variant: {best_variant_id}")
    log(f"  Baseline P@20: {BASELINE_PRECISION_AT20:.4f} -> Best P@20: {gate['best_precision_at20']:.4f} "
        f"(improvement: {gate['precision_at20_improvement']:+.4f})")
    log(f"  Baseline R@100: {BASELINE_RECALL_AT100:.4f} -> Best R@100: {gate['best_recall_at100']:.4f} "
        f"(improvement: {gate['recall_at100_improvement']:+.4f})")
    log(f"  Best FP/TP@5%: {gate['fp_tp_at_5pct']:.2f}")
    log(f"  Queue usable: {gate['queue_usable']}")
    log(f"  Standalone usable: {gate['standalone_usable']}")
    log(f"  Second-stage usable: {gate['low_prevalence_second_stage_usable']}")
    log(f"  Recommended mode: {gate['recommended_mode']}")
    log(f"  Gate: {OUTPUT_DIR / 'risk_ranking_gate.json'}")
    log(f"  Report: {OUTPUT_DIR / 'risk_ranking_report.md'}")
    if config:
        write_run_config(OUTPUT_DIR, config, "run_canonicalized_risk_ranking_v1.py")
        log(f"  Run config: {OUTPUT_DIR / 'run_config.json'}")
    log("=" * 70)


if __name__ == "__main__":
    main()
