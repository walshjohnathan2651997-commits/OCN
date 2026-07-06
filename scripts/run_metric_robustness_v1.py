#!/usr/bin/env python
"""run_metric_robustness_v1.py — Bootstrap confidence intervals and robustness analysis.

Computes bootstrap confidence intervals for classification and queue metrics,
with group-aware resampling to account for candidate-level correlations within
the same target_candidate_group_id.

Metrics:
  Classification: strong_precision, strong_recall, strong_F1, macro_F1, confusion_matrix
  Queue: precision_at_{10,20,50}, recall_at_100, tp_at_20, fp_at_20,
         fp_tp_ratio_at_prevalence for [0.01, 0.03, 0.05, 0.10, 0.15, 0.20]

Bootstrap:
  - Default unit: target_candidate_group_id (resample groups, not candidates)
  - Fallback: candidate-level (with warning in summary)
  - true_label is used ONLY for metric computation, never for ranking/scoring

Paired comparison:
  - G_conservative_precision (priority_score) vs SmartQueue conservative (score_conservative)
  - G_conservative_precision (priority_score) vs SmartQueue balanced (score_balanced)

Hard boundaries: no network, no API, no training, no original data modification.
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, write_run_config, print_guards  # noqa: E402
from schema_utils import write_schema_validation_report  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
STRONG_LABEL = "strong_action_overclaim"
PREVALENCES = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20]
QUEUE_K_VALUES = [10, 20, 50]


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_and_merge(review_scores_csv: str, ranking_scores_csv: str, candidate_csv: str) -> pd.DataFrame:
    """Load and merge the three input CSVs on candidate_id.

    review_scores_csv: must have candidate_id, true_label, pred_label
    ranking_scores_csv: must have candidate_id and at least one score column
    candidate_csv: must have candidate_id, target_candidate_group_id
    """
    review = pd.read_csv(review_scores_csv, keep_default_na=False)
    ranking = pd.read_csv(ranking_scores_csv, keep_default_na=False)
    candidate = pd.read_csv(candidate_csv, keep_default_na=False)

    for name, df, required in [
        ("review_scores", review, ["candidate_id", "true_label", "pred_label"]),
        ("ranking_scores", ranking, ["candidate_id"]),
        ("candidate", candidate, ["candidate_id", "target_candidate_group_id"]),
    ]:
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"{name} CSV missing required columns: {missing}")

    # Merge: start with review_scores, add group from candidate, add scores from ranking
    df = review[["candidate_id", "true_label", "pred_label"]].copy()

    # Add priority_score from review_scores if present (G_conservative_precision baseline)
    if "priority_score" in review.columns:
        df["priority_score"] = review["priority_score"].values

    # Add group from candidate
    group_map = candidate.set_index("candidate_id")["target_candidate_group_id"].to_dict()
    df["target_candidate_group_id"] = df["candidate_id"].map(group_map)

    # Add score columns from ranking_scores
    score_cols = [c for c in ranking.columns if c not in ("candidate_id",) and ranking[c].dtype in (float, int, np.float64, np.int64)]
    for col in score_cols:
        score_map = ranking.set_index("candidate_id")[col].to_dict()
        df[col] = df["candidate_id"].map(score_map)

    return df


def detect_score_columns(df: pd.DataFrame) -> List[str]:
    """Detect available ranking score columns in the merged DataFrame."""
    candidates = ["priority_score", "score_conservative", "score_balanced", "score_high_recall", "final_score"]
    return [c for c in candidates if c in df.columns and df[c].dtype in (float, int, np.float64, np.int64)]


# ---------------------------------------------------------------------------
# Classification metrics
# ---------------------------------------------------------------------------

def compute_classification_metrics(true_labels: np.ndarray, pred_labels: np.ndarray) -> Dict[str, float]:
    """Compute classification metrics from true and predicted labels.

    Returns dict with strong_precision, strong_recall, strong_F1, macro_F1.
    """
    true = np.array(true_labels)
    pred = np.array(pred_labels)

    # Strong action binary: positive = strong_action_overclaim
    tp_strong = int(np.sum((true == STRONG_LABEL) & (pred == STRONG_LABEL)))
    fp_strong = int(np.sum((true != STRONG_LABEL) & (pred == STRONG_LABEL)))
    fn_strong = int(np.sum((true == STRONG_LABEL) & (pred != STRONG_LABEL)))

    strong_prec = tp_strong / (tp_strong + fp_strong) if (tp_strong + fp_strong) > 0 else 0.0
    strong_rec = tp_strong / (tp_strong + fn_strong) if (tp_strong + fn_strong) > 0 else 0.0
    strong_f1 = 2 * strong_prec * strong_rec / (strong_prec + strong_rec) if (strong_prec + strong_rec) > 0 else 0.0

    # Macro F1 across all 4 classes
    f1_per_class = []
    for label in LABELS_4:
        tp = int(np.sum((true == label) & (pred == label)))
        fp = int(np.sum((true != label) & (pred == label)))
        fn = int(np.sum((true == label) & (pred != label)))
        prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        f1_per_class.append(f1)
    macro_f1 = float(np.mean(f1_per_class))

    # Confusion matrix (4x4)
    conf_matrix = np.zeros((4, 4), dtype=int)
    for i, true_lab in enumerate(LABELS_4):
        for j, pred_lab in enumerate(LABELS_4):
            conf_matrix[i, j] = int(np.sum((true == true_lab) & (pred == pred_lab)))

    return {
        "strong_precision": round(strong_prec, 6),
        "strong_recall": round(strong_rec, 6),
        "strong_F1": round(strong_f1, 6),
        "macro_F1": round(macro_f1, 6),
        "confusion_matrix": conf_matrix.tolist(),
    }


# ---------------------------------------------------------------------------
# Queue metrics
# ---------------------------------------------------------------------------

def compute_queue_metrics(
    true_labels: np.ndarray,
    scores: np.ndarray,
    n_total: int,
) -> Dict[str, float]:
    """Compute queue metrics by ranking candidates by score (descending).

    true_labels: array of true labels
    scores: array of ranking scores (higher = more priority)
    n_total: total number of candidates (for recall@100)
    """
    true = np.array(true_labels)
    scores = np.array(scores, dtype=float)
    n = len(true)

    # Sort by score descending
    order = np.argsort(-scores)
    true_sorted = true[order]

    # Strong action binary
    is_strong = (true_sorted == STRONG_LABEL).astype(int)
    n_strong_total = int(np.sum(is_strong))

    metrics: Dict[str, float] = {}

    # Precision@K
    for k in QUEUE_K_VALUES:
        k_eff = min(k, n)
        if k_eff == 0:
            metrics[f"precision_at_{k}"] = 0.0
        else:
            metrics[f"precision_at_{k}"] = round(float(np.sum(is_strong[:k_eff]) / k_eff), 6)

    # Recall@100 (fraction of strong claims in top 100)
    k_recall = min(100, n)
    if n_strong_total > 0:
        metrics["recall_at_100"] = round(float(np.sum(is_strong[:k_recall]) / n_strong_total), 6)
    else:
        metrics["recall_at_100"] = 0.0

    # TP@20 and FP@20
    k20 = min(20, n)
    tp20 = int(np.sum(is_strong[:k20]))
    fp20 = k20 - tp20
    metrics["tp_at_20"] = tp20
    metrics["fp_at_20"] = fp20

    # FP/TP ratio at various prevalences
    for prev in PREVALENCES:
        k_prev = max(1, int(np.ceil(prev * n)))
        k_prev = min(k_prev, n)
        tp_prev = int(np.sum(is_strong[:k_prev]))
        fp_prev = k_prev - tp_prev
        ratio = fp_prev / tp_prev if tp_prev > 0 else float("inf")
        if ratio == float("inf"):
            metrics[f"fp_tp_ratio_at_{prev}"] = float("inf")
        else:
            metrics[f"fp_tp_ratio_at_{prev}"] = round(ratio, 6)

    return metrics


# ---------------------------------------------------------------------------
# Bootstrap
# ---------------------------------------------------------------------------

def bootstrap_group_aware(
    df: pd.DataFrame,
    metric_fn,
    n_bootstrap: int,
    random_seed: int,
    bootstrap_unit: str = "group",
) -> Tuple[List[Dict], str, Optional[str]]:
    """Bootstrap resampling, group-aware or candidate-level.

    Returns (list_of_metric_dicts, effective_bootstrap_unit, warning_message).
    """
    rng = np.random.RandomState(random_seed)

    if bootstrap_unit == "group" and "target_candidate_group_id" in df.columns:
        groups = df["target_candidate_group_id"].dropna().unique()
        if len(groups) < 2:
            warning = f"Only {len(groups)} groups found; falling back to candidate-level bootstrap."
            log(f"  [WARN] {warning}")
            return _bootstrap_candidate_level(df, metric_fn, n_bootstrap, rng), "candidate", warning

        group_to_indices = {}
        for idx, row in df.iterrows():
            gid = row["target_candidate_group_id"]
            if gid not in group_to_indices:
                group_to_indices[gid] = []
            group_to_indices[gid].append(idx)

        group_ids = list(group_to_indices.keys())
        bootstrap_results = []
        for _ in range(n_bootstrap):
            sampled_groups = rng.choice(group_ids, size=len(group_ids), replace=True)
            sampled_indices = []
            for gid in sampled_groups:
                sampled_indices.extend(group_to_indices[gid])
            sampled_df = df.iloc[sampled_indices]
            metrics = metric_fn(sampled_df)
            bootstrap_results.append(metrics)
        return bootstrap_results, "group", None

    else:
        if bootstrap_unit == "group":
            warning = "target_candidate_group_id not found; using candidate-level bootstrap."
            log(f"  [WARN] {warning}")
            return _bootstrap_candidate_level(df, metric_fn, n_bootstrap, rng), "candidate", warning
        return _bootstrap_candidate_level(df, metric_fn, n_bootstrap, rng), "candidate", None


def _bootstrap_candidate_level(df: pd.DataFrame, metric_fn, n_bootstrap: int, rng) -> List[Dict]:
    """Candidate-level bootstrap (each candidate resampled independently)."""
    n = len(df)
    indices = np.arange(n)
    bootstrap_results = []
    for _ in range(n_bootstrap):
        sampled = rng.choice(indices, size=n, replace=True)
        sampled_df = df.iloc[sampled]
        metrics = metric_fn(sampled_df)
        bootstrap_results.append(metrics)
    return bootstrap_results


def compute_ci(bootstrap_values: List[float], confidence: float = 0.95) -> Tuple[float, float]:
    """Compute confidence interval from bootstrap values."""
    if not bootstrap_values:
        return (0.0, 0.0)
    arr = np.array(bootstrap_values)
    alpha = (1 - confidence) / 2
    ci_low = float(np.percentile(arr, alpha * 100))
    ci_high = float(np.percentile(arr, (1 - alpha) * 100))
    return (round(ci_low, 6), round(ci_high, 6))


# ---------------------------------------------------------------------------
# Main metric computation with CI
# ---------------------------------------------------------------------------

def run_classification_with_ci(df: pd.DataFrame, n_bootstrap: int, random_seed: int, bootstrap_unit: str) -> Tuple[List[Dict], str, Optional[str]]:
    """Compute classification metrics with bootstrap CI."""
    log("  Computing classification metrics with CI...")

    def metric_fn(sample_df):
        return compute_classification_metrics(
            sample_df["true_label"].values,
            sample_df["pred_label"].values,
        )

    point_estimate = metric_fn(df)
    bootstrap_results, effective_unit, warning = bootstrap_group_aware(
        df, metric_fn, n_bootstrap, random_seed, bootstrap_unit
    )

    rows = []
    for metric_name in ["strong_precision", "strong_recall", "strong_F1", "macro_F1"]:
        values = [r[metric_name] for r in bootstrap_results]
        ci_low, ci_high = compute_ci(values)
        rows.append({
            "metric": metric_name,
            "point_estimate": point_estimate[metric_name],
            "ci_low_2_5": ci_low,
            "ci_high_97_5": ci_high,
            "bootstrap_unit": effective_unit,
            "n_bootstrap": n_bootstrap,
        })

    return rows, effective_unit, warning


def run_queue_with_ci(
    df: pd.DataFrame,
    score_columns: List[str],
    n_bootstrap: int,
    random_seed: int,
    bootstrap_unit: str,
) -> Tuple[List[Dict], str, Optional[str]]:
    """Compute queue metrics with bootstrap CI for each score variant."""
    log("  Computing queue metrics with CI...")

    all_rows = []
    effective_unit = bootstrap_unit
    warning = None

    for score_col in score_columns:
        log(f"    Variant: {score_col}")

        # Filter out rows where the score is NaN
        valid_df = df.dropna(subset=[score_col]).copy()
        if len(valid_df) == 0:
            log(f"      [SKIP] No valid scores for {score_col}")
            continue

        def metric_fn(sample_df, sc=score_col):
            return compute_queue_metrics(
                sample_df["true_label"].values,
                sample_df[sc].values,
                len(sample_df),
            )

        point_estimate = metric_fn(valid_df)
        bootstrap_results, eff_unit, warn = bootstrap_group_aware(
            valid_df, metric_fn, n_bootstrap, random_seed, bootstrap_unit
        )
        if warn and not warning:
            warning = warn
        effective_unit = eff_unit

        metric_names = [k for k in point_estimate.keys()]
        for metric_name in metric_names:
            values = [r[metric_name] for r in bootstrap_results]
            # Handle inf values for fp_tp_ratio
            finite_values = [v for v in values if v != float("inf")]
            if len(finite_values) < len(values):
                # Some bootstrap samples had inf (no TP in top-k)
                ci_low, ci_high = compute_ci(finite_values) if finite_values else (float("inf"), float("inf"))
            else:
                ci_low, ci_high = compute_ci(values)

            k_or_prev = ""
            if metric_name.startswith("precision_at_"):
                k_or_prev = metric_name.replace("precision_at_", "")
            elif metric_name.startswith("recall_at_"):
                k_or_prev = metric_name.replace("recall_at_", "")
            elif metric_name.startswith("tp_at_") or metric_name.startswith("fp_at_"):
                k_or_prev = metric_name.split("_at_")[-1]
            elif metric_name.startswith("fp_tp_ratio_at_"):
                k_or_prev = metric_name.replace("fp_tp_ratio_at_", "")

            all_rows.append({
                "variant_or_profile": score_col,
                "metric": metric_name,
                "k_or_prevalence": k_or_prev,
                "point_estimate": point_estimate[metric_name],
                "ci_low_2_5": ci_low,
                "ci_high_97_5": ci_high,
            })

    return all_rows, effective_unit, warning


# ---------------------------------------------------------------------------
# Paired bootstrap comparison
# ---------------------------------------------------------------------------

def paired_bootstrap_comparison(
    df: pd.DataFrame,
    variant_a: str,
    variant_b: str,
    n_bootstrap: int,
    random_seed: int,
    bootstrap_unit: str,
) -> List[Dict]:
    """Paired bootstrap comparison of two ranking variants.

    For each bootstrap sample, compute the metric for both variants and record
    the delta. This preserves the paired structure (same bootstrap sample).
    """
    log(f"  Paired comparison: {variant_a} vs {variant_b}")
    rng = np.random.RandomState(random_seed + 1)

    valid_df = df.dropna(subset=[variant_a, variant_b]).copy()
    if len(valid_df) == 0:
        log(f"    [SKIP] No valid scores for both {variant_a} and {variant_b}")
        return []

    metrics_to_compare = ["precision_at_20", "recall_at_100", "tp_at_20"]

    def compute_for_variant(sample_df, score_col):
        return compute_queue_metrics(
            sample_df["true_label"].values,
            sample_df[score_col].values,
            len(sample_df),
        )

    # Determine bootstrap groups
    if bootstrap_unit == "group" and "target_candidate_group_id" in valid_df.columns:
        groups = valid_df["target_candidate_group_id"].dropna().unique()
        if len(groups) >= 2:
            group_to_indices = {}
            for idx, row in valid_df.iterrows():
                gid = row["target_candidate_group_id"]
                group_to_indices.setdefault(gid, []).append(idx)
            group_ids = list(group_to_indices.keys())

            deltas_by_metric: Dict[str, List[float]] = {m: [] for m in metrics_to_compare}
            for _ in range(n_bootstrap):
                sampled_groups = rng.choice(group_ids, size=len(group_ids), replace=True)
                sampled_indices = []
                for gid in sampled_groups:
                    sampled_indices.extend(group_to_indices[gid])
                sample_df = valid_df.iloc[sampled_indices]
                metrics_a = compute_for_variant(sample_df, variant_a)
                metrics_b = compute_for_variant(sample_df, variant_b)
                for m in metrics_to_compare:
                    deltas_by_metric[m].append(metrics_b[m] - metrics_a[m])
        else:
            deltas_by_metric = _paired_candidate_level(valid_df, variant_a, variant_b, metrics_to_compare, n_bootstrap, rng)
    else:
        deltas_by_metric = _paired_candidate_level(valid_df, variant_a, variant_b, metrics_to_compare, n_bootstrap, rng)

    rows = []
    for metric_name in metrics_to_compare:
        deltas = deltas_by_metric[metric_name]
        if not deltas:
            continue
        delta_arr = np.array(deltas)
        point_a = compute_for_variant(valid_df, variant_a)[metric_name]
        point_b = compute_for_variant(valid_df, variant_b)[metric_name]
        delta_point = point_b - point_a
        ci_low, ci_high = compute_ci(deltas)
        prob_positive = float(np.mean(delta_arr > 0))
        rows.append({
            "metric": metric_name,
            "variant_a": variant_a,
            "variant_b": variant_b,
            "delta": round(delta_point, 6),
            "ci_low": ci_low,
            "ci_high": ci_high,
            "prob_delta_positive": round(prob_positive, 4),
        })

    return rows


def _paired_candidate_level(valid_df, variant_a, variant_b, metrics_to_compare, n_bootstrap, rng):
    """Candidate-level paired bootstrap helper."""
    n = len(valid_df)
    indices = np.arange(n)
    deltas_by_metric: Dict[str, List[float]] = {m: [] for m in metrics_to_compare}

    def compute_for_variant(sample_df, score_col):
        return compute_queue_metrics(
            sample_df["true_label"].values,
            sample_df[score_col].values,
            len(sample_df),
        )

    for _ in range(n_bootstrap):
        sampled = rng.choice(indices, size=n, replace=True)
        sample_df = valid_df.iloc[sampled]
        metrics_a = compute_for_variant(sample_df, variant_a)
        metrics_b = compute_for_variant(sample_df, variant_b)
        for m in metrics_to_compare:
            deltas_by_metric[m].append(metrics_b[m] - metrics_a[m])

    return deltas_by_metric


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_classification_metrics_csv(output_dir: Path, rows: List[Dict]) -> None:
    """Write classification_metrics_with_ci.csv."""
    csv_path = output_dir / "classification_metrics_with_ci.csv"
    fieldnames = ["metric", "point_estimate", "ci_low_2_5", "ci_high_97_5", "bootstrap_unit", "n_bootstrap"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log(f"  Wrote {csv_path}")


def write_queue_metrics_csv(output_dir: Path, rows: List[Dict]) -> None:
    """Write queue_metrics_with_ci.csv."""
    csv_path = output_dir / "queue_metrics_with_ci.csv"
    fieldnames = ["variant_or_profile", "metric", "k_or_prevalence", "point_estimate", "ci_low_2_5", "ci_high_97_5"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log(f"  Wrote {csv_path}")


def write_paired_comparison_csv(output_dir: Path, rows: List[Dict]) -> None:
    """Write paired_comparison.csv."""
    csv_path = output_dir / "paired_comparison.csv"
    fieldnames = ["metric", "variant_a", "variant_b", "delta", "ci_low", "ci_high", "prob_delta_positive"]
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    log(f"  Wrote {csv_path}")


def write_summary_json(
    output_dir: Path,
    best_queue_variant: str,
    ci_overlaps_baseline: bool,
    n_groups: int,
    n_candidates: int,
    bootstrap_unit: str,
    warning: Optional[str],
    classification_rows: List[Dict],
    queue_rows: List[Dict],
    paired_rows: List[Dict],
) -> None:
    """Write robustness_summary.json."""
    summary = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "best_queue_variant": best_queue_variant,
        "whether_ci_overlaps_baseline": ci_overlaps_baseline,
        "n_groups": n_groups,
        "n_candidates": n_candidates,
        "bootstrap_unit": bootstrap_unit,
        "warning": warning,
        "data_disclaimer": (
            "Controlled silver diagnostic data, NOT natural prevalence. "
            "Metrics reflect a balanced 4-class silver pool (109 per class) and "
            "do NOT represent real-world claim prevalence. CIs reflect sampling "
            "variability within this diagnostic pool only."
        ),
        "n_classification_metrics": len(classification_rows),
        "n_queue_metric_rows": len(queue_rows),
        "n_paired_comparisons": len(paired_rows),
        "guards": {
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
            "true_label_used_only_for_metrics": True,
        },
    }
    summary_path = output_dir / "robustness_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"  Wrote {summary_path}")


def write_summary_md(
    output_dir: Path,
    classification_rows: List[Dict],
    queue_rows: List[Dict],
    paired_rows: List[Dict],
    best_queue_variant: str,
    n_groups: int,
    n_candidates: int,
    bootstrap_unit: str,
    warning: Optional[str],
) -> None:
    """Write robustness_summary.md in paper-readable format."""
    md_path = output_dir / "robustness_summary.md"
    lines = [
        "# Metric Robustness Summary",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Data Disclaimer",
        "",
        "> **Controlled silver diagnostic data, NOT natural prevalence.**",
        "> Metrics reflect a balanced 4-class silver pool (109 per class) and",
        "> do NOT represent real-world claim prevalence. Confidence intervals",
        "> reflect sampling variability within this diagnostic pool only.",
        "",
        f"- Candidates: **{n_candidates}**",
        f"- Groups: **{n_groups}**",
        f"- Bootstrap unit: **{bootstrap_unit}**",
    ]
    if warning:
        lines.append(f"- Warning: **{warning}**")
    lines.extend([
        "",
        "## Classification Metrics (with 95% CI)",
        "",
        "| Metric | Point Estimate | CI Low (2.5%) | CI High (97.5%) |",
        "|--------|---------------|---------------|-----------------|",
    ])
    for row in classification_rows:
        lines.append(
            f"| {row['metric']} | {row['point_estimate']:.4f} | "
            f"{row['ci_low_2_5']:.4f} | {row['ci_high_97_5']:.4f} |"
        )

    lines.extend([
        "",
        "## Queue Metrics (with 95% CI)",
        "",
        f"Best queue variant: **{best_queue_variant}**",
        "",
        "| Variant | Metric | K/Prev | Point Estimate | CI Low | CI High |",
        "|---------|--------|--------|---------------|--------|---------|",
    ])
    for row in queue_rows:
        pe = row["point_estimate"]
        pe_str = f"{pe:.4f}" if isinstance(pe, float) and pe != float("inf") else str(pe)
        cl = row["ci_low_2_5"]
        cl_str = f"{cl:.4f}" if isinstance(cl, float) and cl != float("inf") else str(cl)
        ch = row["ci_high_97_5"]
        ch_str = f"{ch:.4f}" if isinstance(ch, float) and ch != float("inf") else str(ch)
        lines.append(
            f"| {row['variant_or_profile']} | {row['metric']} | {row['k_or_prevalence']} | "
            f"{pe_str} | {cl_str} | {ch_str} |"
        )

    if paired_rows:
        lines.extend([
            "",
            "## Paired Bootstrap Comparison",
            "",
            "| Metric | Variant A | Variant B | Delta | CI Low | CI High | P(delta>0) |",
            "|--------|-----------|-----------|-------|--------|---------|------------|",
        ])
        for row in paired_rows:
            lines.append(
                f"| {row['metric']} | {row['variant_a']} | {row['variant_b']} | "
                f"{row['delta']:.4f} | {row['ci_low']:.4f} | {row['ci_high']:.4f} | "
                f"{row['prob_delta_positive']:.4f} |"
            )

    lines.extend([
        "",
        "## Methodology",
        "",
        "- Bootstrap resampling: **group-aware** (target_candidate_group_id)",
        "  - Groups are resampled with replacement; all candidates within a group",
        "    move together to preserve intra-group correlation.",
        "  - Fallback: candidate-level (if <2 groups available).",
        "- true_label is used **only** for metric computation.",
        "- Ranking/scoring uses model scores (priority_score, score_conservative, etc.).",
        "- 95% CI computed via percentile method (2.5th and 97.5th percentiles).",
        "",
    ])

    md_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"  Wrote {md_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Bootstrap robustness analysis for screening and queue metrics."
    )
    parser.add_argument("--review_scores_csv", required=False, default=None,
                        help="CSV with candidate_id, true_label, pred_label (and optionally priority_score)")
    parser.add_argument("--ranking_scores_csv", required=False, default=None,
                        help="CSV with candidate_id and ranking score columns")
    parser.add_argument("--candidate_csv", required=False, default=None,
                        help="CSV with candidate_id, target_candidate_group_id")
    parser.add_argument("--output_dir", default="experiments/metric_robustness_v1",
                        help="Output directory")
    parser.add_argument("--n_bootstrap", type=int, default=1000,
                        help="Number of bootstrap iterations (default: 1000)")
    parser.add_argument("--bootstrap_unit", choices=["group", "candidate"], default="group",
                        help="Bootstrap unit: group (default) or candidate")
    parser.add_argument("--random_seed", type=int, default=20260706,
                        help="Random seed for bootstrap (default: 20260706)")
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true", help="Use toy config")
    args = parser.parse_args()

    # Load config for guard enforcement
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    # Resolve default paths from config if not provided
    review_scores_csv = args.review_scores_csv
    ranking_scores_csv = args.ranking_scores_csv
    candidate_csv = args.candidate_csv

    if not review_scores_csv:
        review_scores_csv = str(REPO_ROOT / "experiments" / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv")
    if not ranking_scores_csv:
        # Default: smart_queue_scores or risk_ranking_features
        toy_ranking = REPO_ROOT / "experiments" / "lightweight_smart_queue_v1_toy" / "smart_queue_scores.csv"
        real_ranking = REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" / "risk_ranking_features.csv"
        ranking_scores_csv = str(toy_ranking if args.toy_mode or toy_ranking.exists() else real_ranking)
    if not candidate_csv:
        candidate_csv = str(REPO_ROOT / "configs" / ".." / "data" / "toy_synthetic" / "toy_candidates_v1.csv")
        if not Path(candidate_csv).exists():
            candidate_csv = str(REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv")

    log(f"[metric_robustness] review_scores_csv={review_scores_csv}")
    log(f"[metric_robustness] ranking_scores_csv={ranking_scores_csv}")
    log(f"[metric_robustness] candidate_csv={candidate_csv}")
    log(f"[metric_robustness] n_bootstrap={args.n_bootstrap}")
    log(f"[metric_robustness] bootstrap_unit={args.bootstrap_unit}")
    log(f"[metric_robustness] random_seed={args.random_seed}")

    # Check files exist
    for label, path in [("review_scores", review_scores_csv), ("ranking_scores", ranking_scores_csv), ("candidate", candidate_csv)]:
        if not Path(path).exists():
            log(f"ERROR: {label} CSV not found: {path}")
            return 1

    # Load and merge data
    log("[metric_robustness] Loading and merging data...")
    df = load_and_merge(review_scores_csv, ranking_scores_csv, candidate_csv)
    log(f"  Merged DataFrame: {len(df)} rows")

    # Detect score columns
    score_columns = detect_score_columns(df)
    log(f"  Detected score columns: {score_columns}")
    if not score_columns:
        log("ERROR: No ranking score columns found in ranking_scores_csv")
        return 1

    # Determine groups
    if "target_candidate_group_id" in df.columns:
        n_groups = int(df["target_candidate_group_id"].nunique())
    else:
        n_groups = 0
    n_candidates = len(df)

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # --- Classification metrics with CI ---
    log("[metric_robustness] Computing classification metrics with CI...")
    classification_rows, effective_unit, warning = run_classification_with_ci(
        df, args.n_bootstrap, args.random_seed, args.bootstrap_unit
    )

    # --- Queue metrics with CI ---
    log("[metric_robustness] Computing queue metrics with CI...")
    queue_rows, effective_unit2, warning2 = run_queue_with_ci(
        df, score_columns, args.n_bootstrap, args.random_seed, args.bootstrap_unit
    )
    if warning2 and not warning:
        warning = warning2

    # --- Paired bootstrap comparison ---
    paired_rows = []
    if "priority_score" in score_columns:
        for sq_variant in ["score_conservative", "score_balanced"]:
            if sq_variant in score_columns:
                paired_rows.extend(paired_bootstrap_comparison(
                    df, "priority_score", sq_variant,
                    args.n_bootstrap, args.random_seed, args.bootstrap_unit,
                ))

    # --- Determine best queue variant (by P@20 point estimate) ---
    p20_rows = [r for r in queue_rows if r["metric"] == "precision_at_20"]
    if p20_rows:
        best_row = max(p20_rows, key=lambda r: r["point_estimate"] if r["point_estimate"] != float("inf") else -1)
        best_queue_variant = best_row["variant_or_profile"]
    else:
        best_queue_variant = "unknown"

    # --- Check if CI overlaps baseline ---
    ci_overlaps = False
    if "priority_score" in score_columns and best_queue_variant != "priority_score":
        baseline_p20 = [r for r in queue_rows if r["variant_or_profile"] == "priority_score" and r["metric"] == "precision_at_20"]
        best_p20 = [r for r in queue_rows if r["variant_or_profile"] == best_queue_variant and r["metric"] == "precision_at_20"]
        if baseline_p20 and best_p20:
            b_low, b_high = baseline_p20[0]["ci_low_2_5"], baseline_p20[0]["ci_high_97_5"]
            s_low, s_high = best_p20[0]["ci_low_2_5"], best_p20[0]["ci_high_97_5"]
            ci_overlaps = (s_low <= b_high) and (b_low <= s_high)

    # --- Write outputs ---
    log("[metric_robustness] Writing outputs...")
    write_classification_metrics_csv(output_dir, classification_rows)
    write_queue_metrics_csv(output_dir, queue_rows)
    write_paired_comparison_csv(output_dir, paired_rows)
    write_summary_json(
        output_dir, best_queue_variant, ci_overlaps, n_groups, n_candidates,
        effective_unit, warning, classification_rows, queue_rows, paired_rows,
    )
    write_summary_md(
        output_dir, classification_rows, queue_rows, paired_rows,
        best_queue_variant, n_groups, n_candidates, effective_unit, warning,
    )

    # Write run_config
    write_run_config(output_dir, config, "run_metric_robustness_v1.py", extra={
        "n_bootstrap": args.n_bootstrap,
        "bootstrap_unit": args.bootstrap_unit,
        "random_seed": args.random_seed,
        "review_scores_csv": review_scores_csv,
        "ranking_scores_csv": ranking_scores_csv,
        "candidate_csv": candidate_csv,
        "n_candidates": n_candidates,
        "n_groups": n_groups,
        "score_columns": score_columns,
    })

    log(f"\n[metric_robustness] Done. Best queue variant: {best_queue_variant}")
    log(f"[metric_robustness] CI overlaps baseline: {ci_overlaps}")
    log(f"[metric_robustness] Outputs in: {output_dir}")

    return 0


if __name__ == "__main__":
    sys.exit(main())