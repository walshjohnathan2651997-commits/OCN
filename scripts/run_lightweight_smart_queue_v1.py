#!/usr/bin/env python
"""run_lightweight_smart_queue_v1.py — Lightweight auditable SmartQueue.

Upgrades V3.17 post-processing from hard ranking to a lightweight,
auditable, confidentiality-friendly SmartQueue with 3 profiles, bucket
routing, and group diversity constraints.

Hard boundaries:
  - no network, no API, no cloud
  - no model training
  - no threshold changes
  - no forbidden fields (true_label, oracle_hit, evidence_text, etc.)
    used for sorting
  - true_label used ONLY for metric evaluation, never for sorting
"""

import argparse
import csv
import json
import math
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Config (single source of truth)
# ---------------------------------------------------------------------------

CONFIG = {
    "selector": "best_sentence_top5_overlap",
    "profiles": {
        "conservative": {
            "p_strong_w": 1.20, "p_contra_w": -0.90, "entropy_w": -0.35,
            "strong_flag_w": 0.40, "evidence_w": 0.15,
        },
        "balanced": {
            "p_strong_w": 1.00, "p_contra_w": -0.60, "entropy_w": -0.25,
            "strong_flag_w": 0.25, "evidence_w": 0.25,
        },
        "high_recall": {
            "p_strong_w": 1.10, "p_contra_w": -0.35, "entropy_w": -0.15,
            "strong_flag_w": 0.0, "evidence_w": 0.10,
        },
    },
    "evidence_score_weights": {
        "selector_score": 0.40,
        "bm25_score": 0.25,
        "selected_rank": -0.15,
        "length_penalty": -0.20,
    },
    "length_penalty": {
        "optimal_min": 10, "optimal_max": 45,
        "borderline_min": 6, "borderline_max": 70,
        "optimal_penalty": 0.0,
        "borderline_penalty": 0.15,
        "extreme_penalty": 0.35,
    },
    "bucket_thresholds": {
        "contradiction_p_contra": 0.55,
        "high_priority_p_strong": 0.55,
        "high_priority_p_contra_max": 0.36,
        "high_priority_entropy_max": 0.85,
        "high_priority_evidence_min": 0.35,
        "evidence_check_evidence_max": 0.35,
    },
    "group_diversity": {
        "top20_max_per_group": 1,
        "top50_max_per_group": 2,
        "top100_max_per_group": 3,
    },
    "no_network": True,
    "no_api": True,
    "no_training": True,
    "no_threshold_change": True,
}

ALLOWED_SORT_FIELDS = {
    "p_strong", "p_contra", "p_svm", "strong_action_flag", "entropy",
    "selector_score", "selected_rank", "selected_n_words", "bm25_score",
}

FORBIDDEN_SORT_FIELDS = {
    "true_label", "is_strong_action", "oracle_hit",
    "candidate_label_guess", "final_label", "gold_label",
    "human_audited", "evidence_text", "evidence_text_sha256",
}

STRONG_LABEL = "strong_action_overclaim"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def log(msg):
    print(msg, flush=True)


def minmax_normalize(values):
    """Min-max normalize a list to [0, 1]."""
    if not values:
        return []
    lo = min(values)
    hi = max(values)
    if hi - lo < 1e-10:
        return [0.5] * len(values)
    return [(v - lo) / (hi - lo) for v in values]


def compute_length_penalty(n_words):
    """Length penalty based on word count."""
    lp = CONFIG["length_penalty"]
    if lp["optimal_min"] <= n_words <= lp["optimal_max"]:
        return lp["optimal_penalty"]
    if (lp["borderline_min"] <= n_words < lp["optimal_min"]) or (lp["optimal_max"] < n_words <= lp["borderline_max"]):
        return lp["borderline_penalty"]
    return lp["extreme_penalty"]


def compute_evidence_score(selector_score_norm, bm25_score_norm, selected_rank_norm, length_pen):
    """Compute evidence_score from normalized features."""
    w = CONFIG["evidence_score_weights"]
    return (
        w["selector_score"] * selector_score_norm
        + w["bm25_score"] * bm25_score_norm
        + w["selected_rank"] * selected_rank_norm
        + w["length_penalty"] * length_pen
    )


def compute_profile_score(profile_name, p_strong, p_contra, entropy, strong_flag, evidence_score):
    """Compute priority score for a given profile."""
    p = CONFIG["profiles"][profile_name]
    return (
        p["p_strong_w"] * p_strong
        + p["p_contra_w"] * p_contra
        + p["entropy_w"] * entropy
        + p["strong_flag_w"] * strong_flag
        + p["evidence_w"] * evidence_score
    )


def assign_bucket(p_strong, p_contra, entropy, evidence_score):
    """Assign review bucket based on scores."""
    bt = CONFIG["bucket_thresholds"]
    if p_contra >= bt["contradiction_p_contra"]:
        return "contradiction_or_conflict_review"
    if (p_strong >= bt["high_priority_p_strong"]
            and p_contra < bt["high_priority_p_contra_max"]
            and entropy < bt["high_priority_entropy_max"]
            and evidence_score >= bt["high_priority_evidence_min"]):
        return "high_priority_strong_review"
    if p_strong >= bt["high_priority_p_strong"] and evidence_score < bt["evidence_check_evidence_max"]:
        return "evidence_check_needed"
    return "low_priority"


def apply_group_diversity(ranked, max_per_group):
    """Enforce group diversity: limit items per target_candidate_group_id."""
    group_counts = Counter()
    result = []
    for item in ranked:
        gid = item.get("target_candidate_group_id", "")
        if group_counts[gid] < max_per_group:
            result.append(item)
            group_counts[gid] += 1
    return result


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_review_scores(csv_path):
    """Load canonicalized_r4_review_scores.csv.
    Maps: strong_action_score -> p_strong, p_contra_mean -> p_contra, p_svm_mean -> p_svm.
    Does NOT read true_label for sorting.
    """
    records = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["candidate_id"]
            records[cid] = {
                "candidate_id": cid,
                "p_strong": float(row.get("strong_action_score", 0)),
                "p_contra": float(row.get("p_contra_mean", 0)),
                "p_svm": float(row.get("p_svm_mean", 0)),
                "strong_action_flag": int(row.get("strong_action_flag", 0)),
                "vote_share_strong": float(row.get("vote_share_strong", 0)),
                # entropy not in review_scores; derived below
                "_true_label": row.get("true_label", ""),  # stored but NOT used for sorting
                "_pred_label": row.get("pred_label", ""),
            }
    # Derive entropy proxy from vote_share_strong if no entropy column
    for rec in records.values():
        vs = rec["vote_share_strong"]
        rec["entropy"] = round(1.0 - abs(vs - 0.5) * 2, 6)  # 0=confident, 1=uncertain
    return records


def load_selector_evidence(csv_path, selector_name):
    """Load selector_variant_evidence.csv for a specific selector."""
    records = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get("selector") != selector_name:
                continue
            cid = row["candidate_id"]
            records[cid] = {
                "candidate_id": cid,
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "selector_score": float(row.get("selector_score", 0)),
                "selected_rank": int(row.get("selected_rank", 0)) if str(row.get("selected_rank", "")).isdigit() else 0,
                "selected_n_words": int(row.get("n_words", 0)) if str(row.get("n_words", "")).isdigit() else 0,
                "selected_chunk_id": row.get("selected_chunk_id", ""),
                "selected_page_number": int(row.get("selected_page_number", 0)) if str(row.get("selected_page_number", "")).isdigit() else 0,
            }
    return records


def load_bm25_scores(csv_path):
    """Load BM25 retrieval results, return rank=1 bm25_score per candidate."""
    scores = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            cid = row["candidate_id"]
            rank = int(row.get("rank", 0)) if str(row.get("rank", "")).isdigit() else 99
            if cid not in scores or rank < scores[cid]["rank"]:
                scores[cid] = {
                    "candidate_id": cid,
                    "rank": rank,
                    "bm25_score": float(row.get("bm25_score", 0)),
                }
    return scores


def generate_mock_review_scores(selector_evidence):
    """Generate mock R4 scores for toy_mode."""
    import random
    random.seed(42)
    records = {}
    for cid, sel in selector_evidence.items():
        n_words = sel["selected_n_words"]
        # Mock: shorter evidence with good selector_score -> higher p_strong
        base = 0.3 + 0.4 * min(1.0, sel["selector_score"])
        if n_words < 8 or n_words > 60:
            base -= 0.1
        p_strong = max(0.05, min(0.95, base + random.uniform(-0.1, 0.1)))
        p_contra = max(0.02, min(0.8, 0.2 + random.uniform(-0.1, 0.15)))
        p_svm = max(0.05, min(0.9, 0.3 + random.uniform(-0.1, 0.1)))
        strong_flag = 1 if p_strong > 0.5 else 0
        vs = p_strong if strong_flag else (1 - p_strong) * 0.3
        entropy = round(1.0 - abs(vs - 0.5) * 2, 6)
        # Mock true_label for metrics testing
        labels = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
        mock_true = labels[random.randint(0, 3)]
        records[cid] = {
            "candidate_id": cid,
            "p_strong": round(p_strong, 6),
            "p_contra": round(p_contra, 6),
            "p_svm": round(p_svm, 6),
            "strong_action_flag": strong_flag,
            "vote_share_strong": round(vs, 6),
            "entropy": entropy,
            "_true_label": mock_true,
            "_pred_label": "strong_action_overclaim" if strong_flag else "supported",
        }
    return records


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_scores_csv(filepath, all_items):
    fields = [
        "candidate_id", "target_candidate_group_id", "bucket",
        "p_strong", "p_contra", "p_svm", "strong_action_flag", "entropy",
        "selector_score", "selected_rank", "selected_n_words", "bm25_score",
        "evidence_score", "length_penalty",
        "score_conservative", "score_balanced", "score_high_recall",
        "selected_profile", "final_score",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for item in all_items:
            writer.writerow({k: item.get(k, "") for k in fields})


def write_queue_csv(filepath, queue_items):
    fields = [
        "rank", "candidate_id", "target_candidate_group_id", "bucket",
        "final_score", "p_strong", "p_contra", "evidence_score",
        "selected_n_words", "selected_page_number",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for i, item in enumerate(queue_items, 1):
            writer.writerow({
                "rank": i,
                "candidate_id": item["candidate_id"],
                "target_candidate_group_id": item.get("target_candidate_group_id", ""),
                "bucket": item["bucket"],
                "final_score": round(item["final_score"], 6),
                "p_strong": item["p_strong"],
                "p_contra": item["p_contra"],
                "evidence_score": round(item["evidence_score"], 6),
                "selected_n_words": item["selected_n_words"],
                "selected_page_number": item.get("selected_page_number", 0),
            })


def write_config_json(filepath, selected_profile):
    config_out = {**CONFIG, "selected_profile": selected_profile}
    config_out["allowed_sort_fields"] = sorted(ALLOWED_SORT_FIELDS)
    config_out["forbidden_sort_fields"] = sorted(FORBIDDEN_SORT_FIELDS)
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(config_out, f, indent=2, ensure_ascii=False)


def write_metric_summary(filepath, queue_items, true_labels, n_total):
    """Compute metrics. true_label used ONLY here, never for sorting."""
    from sklearn.metrics import f1_score, precision_score, recall_score

    # Precision@k (strong_action)
    true_strong = {cid for cid, lab in true_labels.items() if lab == STRONG_LABEL}
    n_true_strong = len(true_strong)

    def precision_at_k(items, k):
        topk = items[:k]
        if not topk:
            return 0.0
        hits = sum(1 for item in topk if item["candidate_id"] in true_strong)
        return round(hits / len(topk), 6)

    def recall_at_k(items, k):
        if n_true_strong == 0:
            return 0.0
        topk = items[:k]
        hits = sum(1 for item in topk if item["candidate_id"] in true_strong)
        return round(hits / n_true_strong, 6)

    bucket_dist = Counter(item["bucket"] for item in queue_items)

    summary = {
        "n_candidates": n_total,
        "n_in_queue": len(queue_items),
        "n_true_strong": n_true_strong,
        "precision_at_20": precision_at_k(queue_items, 20),
        "precision_at_50": precision_at_k(queue_items, 50),
        "precision_at_100": precision_at_k(queue_items, 100),
        "recall_at_20": recall_at_k(queue_items, 20),
        "recall_at_50": recall_at_k(queue_items, 50),
        "recall_at_100": recall_at_k(queue_items, 100),
        "bucket_distribution": dict(bucket_dist),
        "true_label_used_for_metrics_only": True,
        "no_forbidden_fields_in_sorting": True,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def write_leakage_guard(filepath):
    report = {
        "forbidden_sort_fields": sorted(FORBIDDEN_SORT_FIELDS),
        "allowed_sort_fields": sorted(ALLOWED_SORT_FIELDS),
        "fields_actually_used_for_sorting": [
            "p_strong", "p_contra", "p_svm", "strong_action_flag", "entropy",
            "selector_score", "selected_rank", "selected_n_words", "bm25_score",
        ],
        "true_label_used_for_sorting": False,
        "true_label_used_for_metrics_only": True,
        "oracle_hit_used_for_sorting": False,
        "evidence_text_used_for_sorting": False,
        "no_network": CONFIG["no_network"],
        "no_api": CONFIG["no_api"],
        "no_training": CONFIG["no_training"],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Lightweight SmartQueue with 3 profiles and group diversity.")
    parser.add_argument("--review_scores_csv",
                        default="experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv")
    parser.add_argument("--selector_csv",
                        default="experiments/canonicalizer_ablation_v1/selector_variant_evidence.csv")
    parser.add_argument("--retrieval_csv",
                        default="experiments/bm25_sentence_retrieval_v1/retrieval_results_sentence_bm25.csv")
    parser.add_argument("--output_dir",
                        default="experiments/lightweight_smart_queue_v1")
    parser.add_argument("--selector", default=CONFIG["selector"])
    parser.add_argument("--profile", default="balanced", choices=["conservative", "balanced", "high_recall"])
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    CONFIG["selector"] = args.selector
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        selector_csv = "experiments/canonicalizer_ablation_v1_toy/selector_variant_evidence.csv"
        retrieval_csv = "experiments/bm25_sentence_retrieval_v1_toy/retrieval_results_sentence_bm25.csv"
        review_scores_csv = None  # will generate mock
        print("[toy_mode] Using toy inputs with mock R4 scores")
    else:
        selector_csv = args.selector_csv
        retrieval_csv = args.retrieval_csv
        review_scores_csv = args.review_scores_csv

    # --- Load data ---
    print(f"Loading selector evidence from {selector_csv}")
    selector_evidence = load_selector_evidence(selector_csv, args.selector)
    print(f"  {len(selector_evidence)} candidates with selector '{args.selector}'")

    print(f"Loading BM25 scores from {retrieval_csv}")
    bm25_scores = load_bm25_scores(retrieval_csv)
    print(f"  {len(bm25_scores)} candidates with BM25 scores")

    if args.toy_mode:
        print("Generating mock R4 review scores ...")
        review_scores = generate_mock_review_scores(selector_evidence)
    else:
        print(f"Loading review scores from {review_scores_csv}")
        review_scores = load_review_scores(review_scores_csv)
    print(f"  {len(review_scores)} candidates with review scores")

    # --- Build unified feature table ---
    print("\nBuilding feature table ...")
    all_cids = set(review_scores.keys()) & set(selector_evidence.keys())
    all_items = []
    for cid in sorted(all_cids):
        rs = review_scores[cid]
        sel = selector_evidence[cid]
        bm25 = bm25_scores.get(cid, {"bm25_score": 0.0, "rank": 99})

        item = {
            "candidate_id": cid,
            "target_candidate_group_id": sel["target_candidate_group_id"],
            "p_strong": rs["p_strong"],
            "p_contra": rs["p_contra"],
            "p_svm": rs["p_svm"],
            "strong_action_flag": rs["strong_action_flag"],
            "entropy": rs["entropy"],
            "selector_score": sel["selector_score"],
            "selected_rank": sel["selected_rank"],
            "selected_n_words": sel["selected_n_words"],
            "bm25_score": bm25["bm25_score"],
            "selected_page_number": sel.get("selected_page_number", 0),
            "_true_label": rs.get("_true_label", ""),
        }
        all_items.append(item)

    if not all_items:
        print("ERROR: No candidates with complete data. Exiting.")
        sys.exit(2)

    # --- Normalize features ---
    print("Normalizing features (minmax) ...")
    sel_scores_norm = minmax_normalize([it["selector_score"] for it in all_items])
    bm25_scores_norm = minmax_normalize([it["bm25_score"] for it in all_items])
    ranks_norm = minmax_normalize([it["selected_rank"] for it in all_items])
    nwords_norm = minmax_normalize([it["selected_n_words"] for it in all_items])

    for i, item in enumerate(all_items):
        item["selector_score_norm"] = sel_scores_norm[i]
        item["bm25_score_norm"] = bm25_scores_norm[i]
        item["selected_rank_norm"] = ranks_norm[i]
        item["length_penalty"] = compute_length_penalty(item["selected_n_words"])
        item["evidence_score"] = compute_evidence_score(
            sel_scores_norm[i], bm25_scores_norm[i], ranks_norm[i], item["length_penalty"]
        )
        item["score_conservative"] = compute_profile_score(
            "conservative", item["p_strong"], item["p_contra"],
            item["entropy"], item["strong_action_flag"], item["evidence_score"]
        )
        item["score_balanced"] = compute_profile_score(
            "balanced", item["p_strong"], item["p_contra"],
            item["entropy"], item["strong_action_flag"], item["evidence_score"]
        )
        item["score_high_recall"] = compute_profile_score(
            "high_recall", item["p_strong"], item["p_contra"],
            item["entropy"], item["strong_action_flag"], item["evidence_score"]
        )
        item["bucket"] = assign_bucket(
            item["p_strong"], item["p_contra"], item["entropy"], item["evidence_score"]
        )
        item["selected_profile"] = args.profile
        item["final_score"] = item[f"score_{args.profile}"]

    # --- Sort by final score ---
    all_items.sort(key=lambda x: x["final_score"], reverse=True)

    # --- Group diversity ---
    print("Applying group diversity ...")
    top20 = apply_group_diversity(all_items, CONFIG["group_diversity"]["top20_max_per_group"])[:20]
    top50 = apply_group_diversity(all_items, CONFIG["group_diversity"]["top50_max_per_group"])[:50]
    top100 = apply_group_diversity(all_items, CONFIG["group_diversity"]["top100_max_per_group"])[:100]

    # --- True labels for metrics ONLY ---
    true_labels = {it["candidate_id"]: it["_true_label"] for it in all_items if it["_true_label"]}

    # --- Write outputs ---
    scores_csv = output_dir / "smart_queue_scores.csv"
    write_scores_csv(scores_csv, all_items)
    print(f"\nWrote {scores_csv}")

    write_queue_csv(output_dir / "smart_queue_top20.csv", top20)
    print(f"Wrote smart_queue_top20.csv ({len(top20)} items)")

    write_queue_csv(output_dir / "smart_queue_top50.csv", top50)
    print(f"Wrote smart_queue_top50.csv ({len(top50)} items)")

    write_queue_csv(output_dir / "smart_queue_top100.csv", top100)
    print(f"Wrote smart_queue_top100.csv ({len(top100)} items)")

    write_config_json(output_dir / "smart_queue_config.json", args.profile)
    print(f"Wrote smart_queue_config.json")

    write_metric_summary(output_dir / "smart_queue_metric_summary.json", top100, true_labels, len(all_items))
    print(f"Wrote smart_queue_metric_summary.json")

    write_leakage_guard(output_dir / "leakage_guard_report.json")
    print(f"Wrote leakage_guard_report.json")

    # --- Summary ---
    bucket_dist = Counter(it["bucket"] for it in all_items)
    print(f"\nBucket distribution: {dict(bucket_dist)}")
    print(f"Profile: {args.profile}")
    print(f"Top20: {len(top20)}, Top50: {len(top50)}, Top100: {len(top100)}")
    print("Done.")


if __name__ == "__main__":
    main()
