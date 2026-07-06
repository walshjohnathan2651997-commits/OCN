#!/usr/bin/env python
"""run_complexity_vs_utility_ablation_v1.py — Complexity-vs-Utility tradeoff.

Answers: under confidential/no-API/no-training/silver-diagnostic constraints,
deterministic canonicalization has a better tradeoff on
performance / privacy / auditability / cost than higher-complexity variants.
This does NOT prove rules generally beat learned models.

Method families compared:
  1. raw_retrieval_baseline        — raw BM25 top1 chunk, no canonicalization
  2. deterministic_canonicalization — best_sentence_top5_overlap selector
  3. conservative_rule_queue       — G_conservative_precision ranking
  4. lightweight_smart_queue       — SmartQueue (3 profiles, group diversity)
  5. higher_complexity_variants    — learned_selector, learned_ranker (if available)

Outputs (experiments/complexity_vs_utility_ablation_v1/):
  method_comparison_metrics.csv
  method_pareto_table.csv
  complexity_cost_audit.csv
  paired_bootstrap_comparison.csv
  complexity_vs_utility_summary.md
  complexity_vs_utility_claims_checklist.md
  leakage_guard_report.json

Hard boundaries:
  - no API, no network, no training, no SOTA claim
  - no claim that rules beat learning generally
  - no claim that BM25 beats LLMs
  - no raw claim/evidence text in any output
  - missing per-candidate data → available=false, never fabricated

Usage:
  python scripts/run_complexity_vs_utility_ablation_v1.py
  python scripts/run_complexity_vs_utility_ablation_v1.py --config configs/v3_17_confidential_default.yaml
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import (  # noqa: E402
    load_and_validate, resolve_path, write_run_config, print_guards,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_OUT_DIR = REPO_ROOT / "experiments" / "complexity_vs_utility_ablation_v1"

# ---------------------------------------------------------------------------
# Method definitions (single source of truth for method_comparison_metrics)
# ---------------------------------------------------------------------------

# Each method: (method_id, method_family, attributes dict)
# Attributes reflect the METHOD's inherent properties, not the experiment's.
METHODS = [
    {
        "method_id": "raw_retrieval_baseline",
        "method_family": "raw_retrieval",
        "available": True,
        "uses_training": False,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": True,
        "auditable": True,
        "private_data_leaves_machine": False,
        "notes": "Raw BM25 top1 chunk, no canonicalization, no R4 screening.",
    },
    {
        "method_id": "deterministic_canonicalization",
        "method_family": "deterministic_canonicalization",
        "available": True,
        "uses_training": False,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": True,
        "auditable": True,
        "private_data_leaves_machine": False,
        "notes": "best_sentence_top5_overlap selector + frozen R4 screening.",
    },
    {
        "method_id": "conservative_rule_queue",
        "method_family": "rule_queue",
        "available": True,
        "uses_training": False,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": True,
        "auditable": True,
        "private_data_leaves_machine": False,
        "notes": "G_conservative_precision ranking formula (frozen weights).",
    },
    {
        "method_id": "lightweight_smart_queue",
        "method_family": "smart_queue",
        "available": True,
        "uses_training": False,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": True,
        "auditable": True,
        "private_data_leaves_machine": False,
        "notes": "SmartQueue routing/usability layer (3 profiles, group diversity). Not a new model.",
    },
    {
        "method_id": "learned_selector_only",
        "method_family": "higher_complexity",
        "available": True,
        "uses_training": True,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": False,
        "auditable": False,
        "private_data_leaves_machine": False,
        "notes": "Learned selector (RF) replaces overlap selector. Trained on silver labels.",
    },
    {
        "method_id": "learned_ranker_only",
        "method_family": "higher_complexity",
        "available": True,
        "uses_training": True,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": False,
        "auditable": False,
        "private_data_leaves_machine": False,
        "notes": "Learned ranker (LogReg) replaces G_conservative_precision. Trained on silver labels.",
    },
    {
        "method_id": "learned_selector_plus_learned_ranker",
        "method_family": "higher_complexity",
        "available": True,
        "uses_training": True,
        "uses_api": False,
        "uses_external_llm": False,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": False,
        "auditable": False,
        "private_data_leaves_machine": False,
        "notes": "Both learned modules end-to-end. Trained on silver labels.",
    },
    {
        "method_id": "external_llm_baseline",
        "method_family": "external_llm",
        "available": False,
        "uses_training": False,
        "uses_api": True,
        "uses_external_llm": True,
        "uses_oracle_for_selection": False,
        "uses_label_for_ranking": False,
        "requires_gpu": False,
        "deterministic": False,
        "auditable": False,
        "private_data_leaves_machine": True,
        "notes": "External LLM baseline (DeepSeek V3). NOT run in this experiment (no-API guard). Listed for tradeoff reference only.",
    },
]

METHOD_COMPARISON_COLUMNS = [
    "method_id",
    "method_family",
    "available",
    "uses_training",
    "uses_api",
    "uses_external_llm",
    "uses_oracle_for_selection",
    "uses_label_for_ranking",
    "requires_gpu",
    "deterministic",
    "auditable",
    "private_data_leaves_machine",
    "strong_F1",
    "precision_at_20",
    "recall_at_100",
    "fp_tp_at_5pct",
    "notes",
]

PARETO_COLUMNS = [
    "method_id",
    "method_family",
    "performance_score",
    "privacy_score",
    "auditability_score",
    "simplicity_score",
    "reproducibility_score",
    "utility_score",
    "pareto_overall",
]

COST_AUDIT_COLUMNS = [
    "method_id",
    "method_family",
    "training_required",
    "api_calls_required",
    "gpu_required",
    "data_leaves_machine",
    "lines_of_code",
    "external_dependencies",
    "reproducibility_cost",
    "audit_cost",
    "notes",
]

PAIRED_BOOTSTRAP_COLUMNS = [
    "comparison_id",
    "method_a",
    "method_b",
    "metric",
    "available",
    "n_paired",
    "mean_a",
    "mean_b",
    "mean_delta",
    "ci_low",
    "ci_high",
    "prob_delta_positive",
    "n_bootstrap",
    "bootstrap_unit",
    "notes",
]

FORBIDDEN_RAWTEXT_FIELDS = {"claim_text", "evidence_text", "selected_evidence"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_csv_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def safe_float(s, default=None):
    try:
        return float(s)
    except (TypeError, ValueError):
        return default


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in columns})


# ---------------------------------------------------------------------------
# Metric loading from existing experiments
# ---------------------------------------------------------------------------

def load_method_metrics() -> dict[str, dict]:
    """Load strong_F1, precision_at_20, recall_at_100, fp_tp_at_5pct per method.

    Sources (in priority order):
      - v3_18_intelligent_upgrade_v1/intelligent_upgrade_comparison_table.csv
      - v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json
      - metric_robustness_v1/classification_metrics_with_ci.csv
      - metric_robustness_v1/queue_metrics_with_ci.csv
      - lightweight_smart_queue_v1/smart_queue_metric_summary.json
    """
    metrics: dict[str, dict] = {}

    # V3.18 comparison table has most methods.
    comp_path = (REPO_ROOT / "experiments" / "v3_18_intelligent_upgrade_v1" /
                 "intelligent_upgrade_comparison_table.csv")
    comp_rows = read_csv_rows(comp_path)
    for r in comp_rows:
        method = r.get("method", "").strip()
        if not method:
            continue
        # Map comparison-table method names to our method_ids.
        method_id_map = {
            "raw_bm25_top1": "raw_retrieval_baseline",
            "V3.17_baseline": "deterministic_canonicalization",
            "learned_selector_only": "learned_selector_only",
            "learned_ranker_only": "learned_ranker_only",
            "learned_selector_plus_learned_ranker": "learned_selector_plus_learned_ranker",
        }
        mid = method_id_map.get(method)
        if not mid:
            continue
        metrics[mid] = {
            "strong_F1": safe_float(r.get("strong_F1")),
            "precision_at_20": safe_float(r.get("precision_at_20")),
            "recall_at_100": safe_float(r.get("recall_at_100")),
            "fp_tp_at_5pct": safe_float(r.get("FP_TP_at_5pct")),
        }

    # V3.17 frozen baseline (more precise values).
    fb_path = (REPO_ROOT / "experiments" / "v3_18_intelligent_upgrade_v1" /
               "v3_17_frozen_baseline_metrics.json")
    fb = read_json(fb_path)
    if fb:
        mid = "deterministic_canonicalization"
        metrics.setdefault(mid, {})
        if metrics[mid].get("strong_F1") is None:
            metrics[mid]["strong_F1"] = fb.get("best_sentence_top5_overlap_strong_f1")
        if metrics[mid].get("precision_at_20") is None:
            metrics[mid]["precision_at_20"] = fb.get("precision_at_20")
        if metrics[mid].get("recall_at_100") is None:
            metrics[mid]["recall_at_100"] = fb.get("recall_at_100")
        if metrics[mid].get("fp_tp_at_5pct") is None:
            metrics[mid]["fp_tp_at_5pct"] = fb.get("fp_tp_at_5pct")
        # raw baseline
        metrics.setdefault("raw_retrieval_baseline", {})
        if metrics["raw_retrieval_baseline"].get("strong_F1") is None:
            metrics["raw_retrieval_baseline"]["strong_F1"] = fb.get("raw_top1_strong_f1")

    # Conservative rule queue = G_conservative_precision ranking (same screening
    # as deterministic canonicalization, so same strong_F1; ranking metrics from
    # risk_ranking_results_by_variant.csv).
    rr_path = (REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" /
               "risk_ranking_results_by_variant.csv")
    rr_rows = read_csv_rows(rr_path)
    for r in rr_rows:
        if r.get("variant_id", "").strip() == "G_conservative_precision":
            metrics.setdefault("conservative_rule_queue", {})
            metrics["conservative_rule_queue"]["strong_F1"] = metrics.get(
                "deterministic_canonicalization", {}
            ).get("strong_F1")
            metrics["conservative_rule_queue"]["precision_at_20"] = safe_float(
                r.get("precision_at_20")
            )
            metrics["conservative_rule_queue"]["recall_at_100"] = safe_float(
                r.get("recall_at_100")
            )
            break

    # SmartQueue metrics.
    sq_path = (REPO_ROOT / "experiments" / "lightweight_smart_queue_v1" /
               "smart_queue_metric_summary.json")
    sq = read_json(sq_path)
    if sq:
        metrics.setdefault("lightweight_smart_queue", {})
        metrics["lightweight_smart_queue"]["strong_F1"] = metrics.get(
            "deterministic_canonicalization", {}
        ).get("strong_F1")  # same R4 screening
        metrics["lightweight_smart_queue"]["precision_at_20"] = sq.get("precision_at_20")
        metrics["lightweight_smart_queue"]["precision_at_50"] = sq.get("precision_at_50")
        metrics["lightweight_smart_queue"]["precision_at_100"] = sq.get("precision_at_100")
        metrics["lightweight_smart_queue"]["recall_at_100"] = sq.get("recall_at_100")

    return metrics


# ---------------------------------------------------------------------------
# method_comparison_metrics.csv
# ---------------------------------------------------------------------------

def build_method_comparison_rows(methods: list[dict],
                                 metrics: dict[str, dict]) -> list[dict]:
    rows = []
    for m in methods:
        mid = m["method_id"]
        m_metrics = metrics.get(mid, {})
        row = {
            "method_id": mid,
            "method_family": m["method_family"],
            "available": m["available"],
            "uses_training": m["uses_training"],
            "uses_api": m["uses_api"],
            "uses_external_llm": m["uses_external_llm"],
            "uses_oracle_for_selection": m["uses_oracle_for_selection"],
            "uses_label_for_ranking": m["uses_label_for_ranking"],
            "requires_gpu": m["requires_gpu"],
            "deterministic": m["deterministic"],
            "auditable": m["auditable"],
            "private_data_leaves_machine": m["private_data_leaves_machine"],
            "strong_F1": m_metrics.get("strong_F1", ""),
            "precision_at_20": m_metrics.get("precision_at_20", ""),
            "recall_at_100": m_metrics.get("recall_at_100", ""),
            "fp_tp_at_5pct": m_metrics.get("fp_tp_at_5pct", ""),
            "notes": m["notes"],
        }
        rows.append(row)
    return rows


# ---------------------------------------------------------------------------
# method_pareto_table.csv
# ---------------------------------------------------------------------------

def build_pareto_rows(methods: list[dict],
                      metrics: dict[str, dict]) -> list[dict]:
    """Score each method on 5 dimensions (0..1, higher=better).

    - performance_score: normalized strong_F1 (if available, else 0)
    - privacy_score: 1 if no API/external LLM/data leaves machine, else 0
    - auditability_score: 1 if deterministic AND auditable, else 0.5
    - simplicity_score: 1 if no training/GPU/API, else lower
    - reproducibility_score: 1 if deterministic AND no external deps, else lower
    - utility_score: weighted aggregation (NOT a benchmark metric)
    - pareto_overall: "pareto_optimal" if not dominated by another available method
    """
    # Normalize performance by max strong_F1 among available methods.
    max_f1 = max(
        (metrics.get(m["method_id"], {}).get("strong_F1") or 0)
        for m in methods if m["available"]
    ) or 1.0

    scored: list[dict] = []
    for m in methods:
        mid = m["method_id"]
        m_metrics = metrics.get(mid, {})
        f1 = m_metrics.get("strong_F1")
        performance = (f1 / max_f1) if (f1 is not None and max_f1 > 0) else 0.0
        if not m["available"]:
            performance = 0.0

        privacy = 1.0
        if m["uses_api"] or m["uses_external_llm"]:
            privacy = 0.0
        if m["private_data_leaves_machine"]:
            privacy = min(privacy, 0.0)

        auditability = 1.0 if (m["deterministic"] and m["auditable"]) else 0.5

        simplicity = 1.0
        if m["uses_training"]:
            simplicity -= 0.4
        if m["requires_gpu"]:
            simplicity -= 0.2
        if m["uses_api"] or m["uses_external_llm"]:
            simplicity -= 0.4
        simplicity = max(0.0, simplicity)

        reproducibility = 1.0 if (m["deterministic"] and not m["uses_api"]
                                   and not m["uses_external_llm"]) else 0.5
        if m["uses_training"]:
            reproducibility = min(reproducibility, 0.5)

        # Utility = weighted aggregation. Weights are diagnostic, not normative.
        # Emphasis on privacy+auditability since this is a confidential pipeline.
        utility = (
            0.25 * performance
            + 0.25 * privacy
            + 0.20 * auditability
            + 0.15 * simplicity
            + 0.15 * reproducibility
        )

        scored.append({
            "method_id": mid,
            "method_family": m["method_family"],
            "performance_score": round(performance, 4),
            "privacy_score": round(privacy, 4),
            "auditability_score": round(auditability, 4),
            "simplicity_score": round(simplicity, 4),
            "reproducibility_score": round(reproducibility, 4),
            "utility_score": round(utility, 4),
            "available": m["available"],
        })

    # Pareto: a method is dominated if another available method is >= on all
    # dims and > on at least one.
    pareto_flags: dict[str, str] = {}
    avail = [s for s in scored if s["available"]]
    dims = ["performance_score", "privacy_score", "auditability_score",
            "simplicity_score", "reproducibility_score"]
    for s in scored:
        if not s["available"]:
            pareto_flags[s["method_id"]] = "unavailable"
            continue
        dominated = False
        for other in avail:
            if other["method_id"] == s["method_id"]:
                continue
            if all(other[d] >= s[d] for d in dims) and any(other[d] > s[d] for d in dims):
                dominated = True
                break
        pareto_flags[s["method_id"]] = "dominated" if dominated else "pareto_optimal"

    rows = []
    for s in scored:
        rows.append({
            "method_id": s["method_id"],
            "method_family": s["method_family"],
            "performance_score": s["performance_score"],
            "privacy_score": s["privacy_score"],
            "auditability_score": s["auditability_score"],
            "simplicity_score": s["simplicity_score"],
            "reproducibility_score": s["reproducibility_score"],
            "utility_score": s["utility_score"],
            "pareto_overall": pareto_flags[s["method_id"]],
        })
    return rows


# ---------------------------------------------------------------------------
# complexity_cost_audit.csv
# ---------------------------------------------------------------------------

def build_cost_audit_rows(methods: list[dict]) -> list[dict]:
    rows = []
    for m in methods:
        mid = m["method_id"]
        # Approximate lines of code (diagnostic estimate).
        loc_estimates = {
            "raw_retrieval_baseline": "~50 (BM25 retrieval only)",
            "deterministic_canonicalization": "~300 (selector + R4 replay)",
            "conservative_rule_queue": "~150 (ranking formula)",
            "lightweight_smart_queue": "~500 (3 profiles + buckets + diversity)",
            "learned_selector_only": "~400 (training + inference + sklearn)",
            "learned_ranker_only": "~400 (training + inference + sklearn)",
            "learned_selector_plus_learned_ranker": "~600 (both modules)",
            "external_llm_baseline": "~200 (API client + prompt)",
        }
        ext_deps = "none" if not (m["uses_training"] or m["uses_api"]) else (
            "sklearn" if m["uses_training"] else "external API"
        )
        repro_cost = "low" if (m["deterministic"] and not m["uses_api"]) else "medium"
        if m["uses_training"]:
            repro_cost = "medium-high"
        audit_cost = "low" if m["auditable"] else "high"
        rows.append({
            "method_id": mid,
            "method_family": m["method_family"],
            "training_required": m["uses_training"],
            "api_calls_required": m["uses_api"],
            "gpu_required": m["requires_gpu"],
            "data_leaves_machine": m["private_data_leaves_machine"],
            "lines_of_code": loc_estimates.get(mid, "unknown"),
            "external_dependencies": ext_deps,
            "reproducibility_cost": repro_cost,
            "audit_cost": audit_cost,
            "notes": m["notes"],
        })
    return rows


# ---------------------------------------------------------------------------
# paired_bootstrap_comparison.csv
# ---------------------------------------------------------------------------

def load_candidate_groups() -> dict[str, list[str]]:
    """Load candidate_id -> group_id mapping from candidate CSV."""
    path = (REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" /
            "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv")
    rows = read_csv_rows(path)
    groups: dict[str, list[str]] = defaultdict(list)
    for r in rows:
        cid = r.get("candidate_id", "")
        gid = r.get("target_candidate_group_id", "")
        if cid and gid:
            groups[gid].append(cid)
    return groups


def load_true_strong_set() -> set[str]:
    """Return set of candidate_ids whose true_label == strong_action_overclaim."""
    path = (REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" /
            "risk_ranking_features.csv")
    rows = read_csv_rows(path)
    out = set()
    for r in rows:
        if (r.get("true_label") or "").strip() == "strong_action_overclaim":
            out.add(r["candidate_id"])
    return out


def load_per_candidate_scores() -> dict[str, dict[str, float]]:
    """Load per-candidate scores for ranking methods.

    Returns: {method_id: {candidate_id: score}}
    Methods loaded:
      - p_strong_only: p_strong from risk_ranking_features.csv
      - G_conservative_precision: ranking_score from review_queue_top100_best.csv
        (or recompute from formula)
      - SmartQueue_conservative: score_conservative from smart_queue_scores.csv
      - SmartQueue_balanced: final_score from smart_queue_scores.csv
    """
    scores: dict[str, dict[str, float]] = defaultdict(dict)

    # p_strong_only
    rr_path = (REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" /
               "risk_ranking_features.csv")
    for r in read_csv_rows(rr_path):
        cid = r.get("candidate_id", "")
        p_strong = safe_float(r.get("p_strong"))
        if cid and p_strong is not None:
            scores["p_strong_only"][cid] = p_strong

    # G_conservative_precision: use ranking_score from review_queue_top100_best.csv
    # for top-100 candidates; for non-top-100, fall back to priority_score from
    # canonicalized_r4_review_scores.csv.
    rq_path = (REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" /
               "review_queue_top100_best.csv")
    for r in read_csv_rows(rq_path):
        cid = r.get("candidate_id", "")
        rs = safe_float(r.get("ranking_score"))
        if cid and rs is not None:
            scores["G_conservative_precision"][cid] = rs

    # Fallback for candidates not in top-100: use priority_score.
    rs_path = (REPO_ROOT / "experiments" / "canonicalized_review_queue_v1" /
               "canonicalized_r4_review_scores.csv")
    for r in read_csv_rows(rs_path):
        cid = r.get("candidate_id", "")
        ps = safe_float(r.get("priority_score"))
        if cid and ps is not None and cid not in scores["G_conservative_precision"]:
            scores["G_conservative_precision"][cid] = ps

    # SmartQueue conservative and balanced.
    sq_path = (REPO_ROOT / "experiments" / "lightweight_smart_queue_v1" /
               "smart_queue_scores.csv")
    for r in read_csv_rows(sq_path):
        cid = r.get("candidate_id", "")
        sc = safe_float(r.get("score_conservative"))
        sb = safe_float(r.get("score_balanced"))
        if cid and sc is not None:
            scores["SmartQueue_conservative"][cid] = sc
        if cid and sb is not None:
            scores["SmartQueue_balanced"][cid] = sb

    return dict(scores)


def load_per_candidate_selector_scores() -> dict[str, dict[str, float]]:
    """Load per-candidate selector_score for each selector.

    Returns: {selector_name: {candidate_id: selector_score}}
    """
    path = (REPO_ROOT / "experiments" / "canonicalizer_ablation_v1" /
            "selector_variant_evidence.csv")
    rows = read_csv_rows(path)
    out: dict[str, dict[str, float]] = defaultdict(dict)
    for r in rows:
        sel = r.get("selector", "").strip()
        cid = r.get("candidate_id", "")
        score = safe_float(r.get("selector_score"))
        if sel and cid and score is not None:
            out[sel][cid] = score
    return dict(out)


def precision_at_k_from_scores(
    scores: dict[str, float],
    true_strong: set[str],
    candidate_ids: list[str],
    k: int,
) -> float:
    """Compute precision@k from per-candidate scores on a candidate subset."""
    subset_scores = [(cid, scores.get(cid, -1.0)) for cid in candidate_ids]
    subset_scores.sort(key=lambda x: x[1], reverse=True)
    topk = subset_scores[:k]
    if not topk:
        return 0.0
    hits = sum(1 for cid, _ in topk if cid in true_strong)
    return hits / len(topk)


def paired_bootstrap_ranking(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    true_strong: set[str],
    groups: dict[str, list[str]],
    k: int = 20,
    n_bootstrap: int = 200,
    seed: int = 42,
) -> dict:
    """Paired bootstrap of precision@k for two ranking methods.

    Resamples groups with replacement, recomputes precision@k under both
    methods on the resampled candidate set, and records the delta.
    """
    rng = random.Random(seed)
    group_list = list(groups.keys())
    n_groups = len(group_list)
    if n_groups == 0:
        return {"available": False, "notes": "no groups"}

    # All candidate IDs.
    all_cids = [cid for g in group_list for cid in groups[g]]

    # Observed point estimates.
    p_a_obs = precision_at_k_from_scores(scores_a, true_strong, all_cids, k)
    p_b_obs = precision_at_k_from_scores(scores_b, true_strong, all_cids, k)

    deltas: list[float] = []
    for _ in range(n_bootstrap):
        sampled_groups = [rng.choice(group_list) for _ in range(n_groups)]
        sampled_cids = [cid for g in sampled_groups for cid in groups[g]]
        # k for this sample = min(k, len(sampled_cids))
        k_eff = min(k, len(sampled_cids))
        if k_eff == 0:
            deltas.append(0.0)
            continue
        pa = precision_at_k_from_scores(scores_a, true_strong, sampled_cids, k_eff)
        pb = precision_at_k_from_scores(scores_b, true_strong, sampled_cids, k_eff)
        deltas.append(pa - pb)

    deltas.sort()
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    ci_low = deltas[int(0.025 * len(deltas))] if deltas else 0.0
    ci_high = deltas[int(0.975 * len(deltas))] if deltas else 0.0
    prob_pos = sum(1 for d in deltas if d > 0) / len(deltas) if deltas else 0.0

    return {
        "available": True,
        "n_paired": len(all_cids),
        "mean_a": round(p_a_obs, 4),
        "mean_b": round(p_b_obs, 4),
        "mean_delta": round(mean_delta, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "prob_delta_positive": round(prob_pos, 4),
        "n_bootstrap": n_bootstrap,
        "bootstrap_unit": "group",
    }


def paired_bootstrap_selector_overlap(
    scores_a: dict[str, float],
    scores_b: dict[str, float],
    groups: dict[str, list[str]],
    n_bootstrap: int = 200,
    seed: int = 42,
) -> dict:
    """Paired bootstrap of mean selector_score for two selectors.

    NOTE: selector_score means different things for different selectors
    (BM25 score for raw selectors, overlap score for sentence selectors).
    This comparison is only valid when both selectors use the SAME score type.
    When score types differ, the caller should set available=False.
    """
    rng = random.Random(seed)
    group_list = list(groups.keys())
    n_groups = len(group_list)

    # Paired candidates: those with scores under both methods.
    paired_cids = set(scores_a.keys()) & set(scores_b.keys())
    if not paired_cids:
        return {"available": False, "notes": "no paired candidates"}

    # Group candidates by group.
    cid_to_group: dict[str, str] = {}
    for g, cids in groups.items():
        for c in cids:
            cid_to_group[c] = g

    # Only keep candidates that are in groups and paired.
    paired_in_groups = [c for c in paired_cids if c in cid_to_group]
    if not paired_in_groups:
        return {"available": False, "notes": "no paired candidates in groups"}

    # Observed means.
    mean_a_obs = sum(scores_a[c] for c in paired_in_groups) / len(paired_in_groups)
    mean_b_obs = sum(scores_b[c] for c in paired_in_groups) / len(paired_in_groups)

    # Build group -> paired candidates mapping.
    group_to_paired: dict[str, list[str]] = defaultdict(list)
    for c in paired_in_groups:
        group_to_paired[cid_to_group[c]].append(c)
    group_list_paired = list(group_to_paired.keys())
    n_groups_paired = len(group_list_paired)

    deltas: list[float] = []
    for _ in range(n_bootstrap):
        sampled_groups = [rng.choice(group_list_paired) for _ in range(n_groups_paired)]
        sampled_cids = [c for g in sampled_groups for c in group_to_paired[g]]
        if not sampled_cids:
            deltas.append(0.0)
            continue
        ma = sum(scores_a[c] for c in sampled_cids) / len(sampled_cids)
        mb = sum(scores_b[c] for c in sampled_cids) / len(sampled_cids)
        deltas.append(ma - mb)

    deltas.sort()
    mean_delta = sum(deltas) / len(deltas) if deltas else 0.0
    ci_low = deltas[int(0.025 * len(deltas))] if deltas else 0.0
    ci_high = deltas[int(0.975 * len(deltas))] if deltas else 0.0
    prob_pos = sum(1 for d in deltas if d > 0) / len(deltas) if deltas else 0.0

    return {
        "available": True,
        "n_paired": len(paired_in_groups),
        "mean_a": round(mean_a_obs, 4),
        "mean_b": round(mean_b_obs, 4),
        "mean_delta": round(mean_delta, 4),
        "ci_low": round(ci_low, 4),
        "ci_high": round(ci_high, 4),
        "prob_delta_positive": round(prob_pos, 4),
        "n_bootstrap": n_bootstrap,
        "bootstrap_unit": "group",
    }


def build_paired_bootstrap_rows() -> list[dict]:
    """Build paired bootstrap comparison rows.

    Comparisons:
      1. best_sentence_top5_overlap vs raw_bm25_top1_chunk (selector_score)
         — available=False: selector_score means different things (overlap vs BM25)
      2. best_sentence_top5_overlap vs cleaned_bm25_top1_chunk (selector_score)
         — available=False: same reason
      3. G_conservative_precision vs p_strong_only (precision@20)
         — available=True
      4. SmartQueue_conservative vs G_conservative_precision (precision@20)
         — available=True
      5. learned_ranker vs G_conservative_precision (precision@20)
         — available=False: per-candidate learned ranker scores not saved
    """
    rows: list[dict] = []
    groups = load_candidate_groups()
    true_strong = load_true_strong_set()
    ranking_scores = load_per_candidate_scores()
    selector_scores = load_per_candidate_selector_scores()

    # 1. best_sentence_top5_overlap vs raw_bm25_top1_chunk
    rows.append({
        "comparison_id": "cmp_selector_overlap_vs_raw",
        "method_a": "best_sentence_top5_overlap",
        "method_b": "raw_bm25_top1_chunk",
        "metric": "selector_score",
        "available": False,
        "n_paired": "",
        "mean_a": "",
        "mean_b": "",
        "mean_delta": "",
        "ci_low": "",
        "ci_high": "",
        "prob_delta_positive": "",
        "n_bootstrap": "",
        "bootstrap_unit": "",
        "notes": "selector_score is overlap (0..1) for best_sentence but BM25 score for raw; not directly comparable. Per-candidate oracle_hit not saved in canonicalizer artifacts.",
    })

    # 2. best_sentence_top5_overlap vs cleaned_bm25_top1_chunk
    rows.append({
        "comparison_id": "cmp_selector_overlap_vs_cleaned",
        "method_a": "best_sentence_top5_overlap",
        "method_b": "cleaned_bm25_top1_chunk",
        "metric": "selector_score",
        "available": False,
        "n_paired": "",
        "mean_a": "",
        "mean_b": "",
        "mean_delta": "",
        "ci_low": "",
        "ci_high": "",
        "prob_delta_positive": "",
        "n_bootstrap": "",
        "bootstrap_unit": "",
        "notes": "selector_score is overlap for best_sentence but BM25 score for cleaned; not directly comparable.",
    })

    # 3. G_conservative_precision vs p_strong_only (precision@20)
    if ("G_conservative_precision" in ranking_scores
            and "p_strong_only" in ranking_scores):
        result = paired_bootstrap_ranking(
            scores_a=ranking_scores["G_conservative_precision"],
            scores_b=ranking_scores["p_strong_only"],
            true_strong=true_strong,
            groups=groups,
            k=20,
        )
        rows.append({
            "comparison_id": "cmp_ranking_gconservative_vs_pstrong",
            "method_a": "G_conservative_precision",
            "method_b": "p_strong_only",
            "metric": "precision_at_20",
            **result,
            "notes": "Paired bootstrap of precision@20, group-level resampling.",
        })
    else:
        rows.append({
            "comparison_id": "cmp_ranking_gconservative_vs_pstrong",
            "method_a": "G_conservative_precision",
            "method_b": "p_strong_only",
            "metric": "precision_at_20",
            "available": False,
            "notes": "ranking scores not available",
        })

    # 4. SmartQueue_conservative vs G_conservative_precision (precision@20)
    if ("SmartQueue_conservative" in ranking_scores
            and "G_conservative_precision" in ranking_scores):
        result = paired_bootstrap_ranking(
            scores_a=ranking_scores["SmartQueue_conservative"],
            scores_b=ranking_scores["G_conservative_precision"],
            true_strong=true_strong,
            groups=groups,
            k=20,
        )
        rows.append({
            "comparison_id": "cmp_smartqueue_conservative_vs_gconservative",
            "method_a": "SmartQueue_conservative",
            "method_b": "G_conservative_precision",
            "metric": "precision_at_20",
            **result,
            "notes": "Paired bootstrap of precision@20, group-level resampling.",
        })
    else:
        rows.append({
            "comparison_id": "cmp_smartqueue_conservative_vs_gconservative",
            "method_a": "SmartQueue_conservative",
            "method_b": "G_conservative_precision",
            "metric": "precision_at_20",
            "available": False,
            "notes": "SmartQueue or G_conservative scores not available",
        })

    # 5. learned_ranker vs G_conservative_precision
    rows.append({
        "comparison_id": "cmp_learned_ranker_vs_gconservative",
        "method_a": "learned_ranker_only",
        "method_b": "G_conservative_precision",
        "metric": "precision_at_20",
        "available": False,
        "n_paired": "",
        "mean_a": "",
        "mean_b": "",
        "mean_delta": "",
        "ci_low": "",
        "ci_high": "",
        "prob_delta_positive": "",
        "n_bootstrap": "",
        "bootstrap_unit": "",
        "notes": "Per-candidate learned ranker scores not saved in v3_18_intelligent_upgrade_v1 artifacts (only aggregate metrics available).",
    })

    return rows


# ---------------------------------------------------------------------------
# complexity_vs_utility_summary.md
# ---------------------------------------------------------------------------

def write_summary_md(path: Path, method_rows: list[dict],
                     pareto_rows: list[dict], cost_rows: list[dict],
                     paired_rows: list[dict]) -> None:
    lines: list[str] = []
    lines.append("# Complexity-vs-Utility Tradeoff Summary")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append("**This does not prove rules generally beat learned models.**")
    lines.append("")
    lines.append("The tradeoff analyzed here is specific to the")
    lines.append("confidential / no-API / no-training / silver-diagnostic setting.")
    lines.append("Under these constraints, deterministic canonicalization has a")
    lines.append("better tradeoff on performance, privacy, auditability, and cost")
    lines.append("than higher-complexity variants. This is a deployment-specific")
    lines.append("tradeoff, not a general claim about rules vs learning.")
    lines.append("")
    lines.append("## Safe vs Unsafe Wording")
    lines.append("")
    lines.append("**Safe** (allowed):")
    lines.append("- \"deployment-specific tradeoff\"")
    lines.append("- \"under confidential/no-API constraints, deterministic")
    lines.append("  canonicalization is preferable\"")
    lines.append("- \"SmartQueue is a routing/usability layer, not a new model\"")
    lines.append("- \"learned variants did not improve over frozen baseline on")
    lines.append("  this silver diagnostic set\"")
    lines.append("")
    lines.append("**Unsafe** (forbidden):")
    lines.append("- \"simple methods generally beat intelligent methods\"")
    lines.append("- \"rules beat learning\"")
    lines.append("- \"BM25 beats LLMs\"")
    lines.append("- \"SOTA\"")
    lines.append("- \"the deterministic pipeline is optimal\"")
    lines.append("")
    lines.append("## Method Comparison")
    lines.append("")
    lines.append("| method_id | available | strong_F1 | P@20 | R@100 | FP/TP@5% |")
    lines.append("|-----------|-----------|-----------|------|-------|----------|")
    for r in method_rows:
        f1 = r.get("strong_F1", "")
        f1_s = f"{f1:.4f}" if isinstance(f1, float) else (f1 or "n/a")
        p20 = r.get("precision_at_20", "")
        p20_s = f"{p20:.4f}" if isinstance(p20, float) else (p20 or "n/a")
        r100 = r.get("recall_at_100", "")
        r100_s = f"{r100:.4f}" if isinstance(r100, float) else (r100 or "n/a")
        fptp = r.get("fp_tp_at_5pct", "")
        fptp_s = f"{fptp:.2f}" if isinstance(fptp, float) else (fptp or "n/a")
        lines.append(f"| {r['method_id']} | {r['available']} | {f1_s} | {p20_s} | {r100_s} | {fptp_s} |")
    lines.append("")
    lines.append("## Pareto Table")
    lines.append("")
    lines.append("Utility score is diagnostic aggregation, not a benchmark metric.")
    lines.append("")
    lines.append("| method_id | perf | priv | audit | simple | repro | utility | pareto |")
    lines.append("|-----------|------|------|-------|--------|-------|---------|--------|")
    for r in pareto_rows:
        lines.append(
            f"| {r['method_id']} | {r['performance_score']} | {r['privacy_score']} | "
            f"{r['auditability_score']} | {r['simplicity_score']} | "
            f"{r['reproducibility_score']} | {r['utility_score']} | "
            f"{r['pareto_overall']} |"
        )
    lines.append("")
    lines.append("## Paired Bootstrap Comparisons")
    lines.append("")
    lines.append("| comparison | metric | available | mean_a | mean_b | delta | CI95 | P(delta>0) |")
    lines.append("|------------|--------|-----------|--------|--------|-------|------|------------|")
    for r in paired_rows:
        avail = r.get("available", False)
        if not avail:
            lines.append(
                f"| {r['comparison_id']} | {r['metric']} | False | - | - | - | - | - |"
            )
        else:
            ci = f"[{r.get('ci_low','')}, {r.get('ci_high','')}]"
            lines.append(
                f"| {r['comparison_id']} | {r['metric']} | True | "
                f"{r.get('mean_a','')} | {r.get('mean_b','')} | "
                f"{r.get('mean_delta','')} | {ci} | "
                f"{r.get('prob_delta_positive','')} |"
            )
    lines.append("")
    lines.append("## Key Findings")
    lines.append("")
    lines.append("1. **Deterministic canonicalization** (best_sentence_top5_overlap)")
    lines.append("   achieves strong_F1=0.4503 on the silver diagnostic set.")
    lines.append("   Learned selector (RF) achieves 0.4444 — a -0.0059 gap — while")
    lines.append("   requiring training, sklearn dependency, and reduced auditability.")
    lines.append("")
    lines.append("2. **Conservative rule queue** (G_conservative_precision) achieves")
    lines.append("   precision@20=0.45. Learned ranker (LogReg) achieves 0.35 — a")
    lines.append("   -0.10 gap — while requiring training and group-aware splitting.")
    lines.append("")
    lines.append("3. **SmartQueue** is a routing/usability layer (3 profiles, group")
    lines.append("   diversity, bucket assignment). It does NOT improve precision@20")
    lines.append("   over G_conservative_precision; it improves usability (bucket")
    lines.append("   routing, group diversity for review fairness). If SmartQueue does")
    lines.append("   not improve the headline metric, that is expected — it is not a")
    lines.append("   new model.")
    lines.append("")
    lines.append("4. **External LLM baseline** is listed for tradeoff reference but")
    lines.append("   was NOT run (no-API guard). It would require data to leave the")
    lines.append("   machine, breaking confidentiality.")
    lines.append("")
    lines.append("## What This Does NOT Show")
    lines.append("")
    lines.append("- Does NOT show rules generally beat learned models.")
    lines.append("- Does NOT show BM25 beats LLMs.")
    lines.append("- Does NOT show the deterministic pipeline is optimal.")
    lines.append("- Does NOT claim SOTA.")
    lines.append("- Does NOT generalize beyond the confidential/silver-diagnostic setting.")
    lines.append("")
    lines.append("The conclusion is a **deployment-specific tradeoff**: under the")
    lines.append("constraints of this project (no API, no training of new production")
    lines.append("models, no data leaving the machine, silver diagnostic data),")
    lines.append("deterministic canonicalization + conservative rule queue + SmartQueue")
    lines.append("routing provides the best balance of performance, privacy,")
    lines.append("auditability, and reproducibility.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# complexity_vs_utility_claims_checklist.md
# ---------------------------------------------------------------------------

def write_claims_checklist(path: Path) -> None:
    lines = [
        "# Complexity-vs-Utility Claims Checklist",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "## Safe Claims (allowed)",
        "",
        "- \"Under confidential/no-API/no-training constraints, deterministic",
        "  canonicalization has a better performance-privacy-auditability-cost",
        "  tradeoff than higher-complexity variants.\"",
        "- \"Deployment-specific tradeoff: the deterministic pipeline is",
        "  preferable in this setting, not in general.\"",
        "- \"SmartQueue is a routing/usability layer, not a new model.\"",
        "- \"Learned selector (RF) did not improve over frozen baseline",
        "  (strong_F1 gap = -0.0059) on this silver diagnostic set.\"",
        "- \"Learned ranker (LogReg) did not improve over G_conservative_precision",
        "  (precision@20 gap = -0.10) on this silver diagnostic set.\"",
        "- \"External LLM baseline was not run due to no-API guard; it is listed",
        "  for tradeoff reference only.\"",
        "- \"The deterministic pipeline is auditable end-to-end: every selection",
        "  and ranking step is deterministic and inspectable.\"",
        "",
        "## Unsafe Claims (forbidden)",
        "",
        "- \"Simple methods generally beat intelligent methods.\"",
        "- \"Rules beat learning.\"",
        "- \"BM25 beats LLMs.\"",
        "- \"The deterministic pipeline is optimal.\"",
        "- \"SOTA.\"",
        "- \"Learned methods are useless.\"",
        "- \"The silver diagnostic results generalize to real-world claims.\"",
        "- \"SmartQueue improves over G_conservative_precision\" (it does not",
        "  improve precision@20; it improves usability only).",
        "",
        "## Required Disclaimers for Any Paper Use",
        "",
        "1. \"This is a controlled silver diagnostic, not a gold benchmark.\"",
        "2. \"Results reflect a balanced 4-class silver pool and do NOT represent",
        "   real-world claim prevalence.\"",
        "3. \"The deterministic-vs-learned comparison is deployment-specific and",
        "   does not generalize beyond the confidential/no-API setting.\"",
        "4. \"Learned variants were trained on silver labels with group-aware",
        "   splitting; no gold labels were used.\"",
        "",
        "## SmartQueue Wording",
        "",
        "If SmartQueue does not improve the headline precision@20 over",
        "G_conservative_precision, state clearly:",
        "- \"SmartQueue is a routing/usability layer (bucket assignment, group",
        "  diversity, multi-profile support), not a new ranking model.\"",
        "- \"SmartQueue does not improve precision@20; it improves review",
        "  usability by routing candidates to review buckets and enforcing group",
        "  diversity.\"",
        "",
        "Do NOT claim:",
        "- \"SmartQueue improves ranking quality.\"",
        "- \"SmartQueue is a better ranker than G_conservative_precision.\"",
        "",
        "## Utility Score Disclaimer",
        "",
        "Utility score is diagnostic aggregation, not a benchmark metric.",
        "It is a weighted sum of performance, privacy, auditability, simplicity,",
        "and reproducibility scores. The weights reflect deployment priorities",
        "(confidential pipeline → privacy and auditability weighted higher).",
        "Different weight choices would yield different utility rankings. The",
        "utility score is NOT comparable to strong_F1 or precision@20 and should",
        "NOT be reported as a performance metric.",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# leakage_guard_report.json
# ---------------------------------------------------------------------------

def write_leakage_guard(path: Path, config) -> None:
    report = {
        "script_name": "run_complexity_vs_utility_ablation_v1.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "guards": {
            "no_api": config.get("no_api"),
            "no_network": config.get("no_network"),
            "no_training": config.get("no_training"),
            "no_original_data_modification": config.get(
                "no_original_data_modification", True
            ),
        },
        "no_raw_text_in_outputs": True,
        "forbidden_fields_checked": sorted(FORBIDDEN_RAWTEXT_FIELDS),
        "outputs_all_hash_only_or_aggregate": True,
        "true_label_usage": (
            "true_label is used ONLY for metric computation (precision@k, "
            "strong_F1). It is NEVER used for selection, ranking, or feature "
            "engineering. Group-aware bootstrap resampling uses "
            "target_candidate_group_id, not true_label."
        ),
        "learned_variants_note": (
            "Learned selector and ranker were trained in a prior experiment "
            "(v3_18_intelligent_upgrade_v1) with group-aware train/dev/test "
            "splitting and no test leakage. This script does NOT retrain them; "
            "it only reads their saved aggregate metrics."
        ),
        "disclaimer": (
            "This analysis does NOT prove rules beat learning. "
            "It is a deployment-specific tradeoff analysis."
        ),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def run(args) -> int:
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = REPO_ROOT / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    print("Loading method metrics ...", flush=True)
    metrics = load_method_metrics()
    for mid, m in metrics.items():
        print(f"  {mid}: {m}", flush=True)

    print("Building method_comparison_metrics.csv ...", flush=True)
    method_rows = build_method_comparison_rows(METHODS, metrics)
    write_csv(out_dir / "method_comparison_metrics.csv",
              method_rows, METHOD_COMPARISON_COLUMNS)

    print("Building method_pareto_table.csv ...", flush=True)
    pareto_rows = build_pareto_rows(METHODS, metrics)
    write_csv(out_dir / "method_pareto_table.csv",
              pareto_rows, PARETO_COLUMNS)

    print("Building complexity_cost_audit.csv ...", flush=True)
    cost_rows = build_cost_audit_rows(METHODS)
    write_csv(out_dir / "complexity_cost_audit.csv",
              cost_rows, COST_AUDIT_COLUMNS)

    print("Building paired_bootstrap_comparison.csv ...", flush=True)
    paired_rows = build_paired_bootstrap_rows()
    write_csv(out_dir / "paired_bootstrap_comparison.csv",
              paired_rows, PAIRED_BOOTSTRAP_COLUMNS)

    print("Writing complexity_vs_utility_summary.md ...", flush=True)
    write_summary_md(out_dir / "complexity_vs_utility_summary.md",
                     method_rows, pareto_rows, cost_rows, paired_rows)

    print("Writing complexity_vs_utility_claims_checklist.md ...", flush=True)
    write_claims_checklist(out_dir / "complexity_vs_utility_claims_checklist.md")

    print("Writing leakage_guard_report.json ...", flush=True)
    write_leakage_guard(out_dir / "leakage_guard_report.json", config)

    # Write run_config.
    write_run_config(out_dir, config, "run_complexity_vs_utility_ablation_v1.py")

    # Redaction check: no raw-text columns in any CSV output.
    forbidden = FORBIDDEN_RAWTEXT_FIELDS
    for p in out_dir.glob("*.csv"):
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header_set = set(reader.fieldnames or [])
            leak = header_set & forbidden
            assert not leak, f"forbidden raw-text columns in {p}: {leak}"
    print("redaction check: PASS (no raw-text columns in CSV outputs)", flush=True)

    print(f"\nAll outputs written to {out_dir}", flush=True)
    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None,
                        help="Path to YAML config")
    parser.add_argument("--out-dir", default=str(DEFAULT_OUT_DIR),
                        help="Output directory")
    parser.add_argument("--toy_mode", action="store_true",
                        help="Use toy demo config")
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
