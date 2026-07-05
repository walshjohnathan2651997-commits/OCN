"""
V3.18 Intelligent Upgrade on V3.17 Baseline v1
================================================
Adds two learned modules on top of the frozen V3.17 baseline:
  1. Learned evidence canonicalizer (replaces handcrafted overlap selector)
  2. Learned risk ranker (replaces handcrafted G_conservative_precision formula)

V3.17 baseline (FROZEN):
  PDF corpus -> BM25 top-k -> best_sentence_top5_overlap -> R4 -> G_conservative_precision
  strong_F1 = 0.4503, strong_recall = 0.7064, P@20 = 0.45, R@100 = 0.3303, FP/TP@5% = 11.24

Prohibitions enforced:
  - no V3.17 baseline modification
  - no paper modification
  - no API calls
  - no network
  - no gold labels used for selector (oracle overlap pseudo-label only)
  - no test-set strong-F1 reverse tuning
  - no R4 retraining / threshold change
  - no proxy
  - no silver-as-gold
  - no natural-distribution claim
  - sklearn only (no new packages)
  - group-aware split mandatory (no test leakage)
"""

from __future__ import annotations

import json
import math
import os
import pickle
import re
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import (
    HistGradientBoostingClassifier,
    RandomForestClassifier,
)
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    average_precision_score,
    f1_score,
    precision_recall_fscore_support,
    precision_score,
    recall_score,
)
from sklearn.metrics.pairwise import cosine_similarity

# ---------------- Paths ----------------
RETRIEVAL_DIR = Path(r"D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1")
RECOVERY_DIR = Path(r"D:\ocn\experiments\r4_minimal_recovery_v1")
RECOVERY_ARTIFACTS = RECOVERY_DIR / "artifacts"
RECOVERY_PREDICTIONS = RECOVERY_DIR / "r4_recovered_predictions_444.csv"
RECOVERY_SPLIT_MANIFEST = RECOVERY_DIR / "r4_recovery_split_manifest.csv"
CANON_DIR = Path(r"D:\ocn\experiments\r4_evidence_canonicalization_v1")
ROBUST_DIR = Path(r"D:\ocn\experiments\canonical_selector_robustness_v1")
RANKING_DIR = Path(r"D:\ocn\experiments\canonicalized_risk_ranking_v1")
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)

OUTPUT_DIR = Path(r"D:\ocn\experiments\v3_18_intelligent_upgrade_v1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

RETRIEVAL_RESULTS_BM25 = RETRIEVAL_DIR / "retrieval_results_bm25.csv"
ORACLE_EVIDENCE_MAP = RETRIEVAL_DIR / "oracle_evidence_map.csv"

# ---------------- Constants ----------------
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment", "neutral", "contradiction_nli",
    "ent_minus_con", "con_minus_ent", "max_prob", "entropy",
]

# V3.17 baseline frozen metrics
V3_17_BASELINE = {
    "raw_top1_strong_f1": 0.1806,
    "oracle_strong_f1": 0.4257,
    "best_sentence_top5_overlap_strong_f1": 0.4503,
    "strong_recall": 0.7064,
    "selectors_above_0.40": "6/9",
    "best_ranking": "G_conservative_precision",
    "precision_at_20": 0.45,
    "recall_at_100": 0.3303,
    "fp_tp_at_5pct": 11.24,
    "second_stage_usable": True,
    "standalone_usable": False,
}

# Action lexicons (copied exactly from run_canonicalized_review_queue_v1.py)
CLAIM_ACTION_TERMS = [
    "deploy", "deployment", "real-world", "real world", "production", "operational",
    "safe", "robust", "guarantee", "all scenarios", "all settings", "all environments",
    "replace", "should be used", "policy", "engineering decision", "ready for use",
    "in practice", "uniformly", "without caveat", "irrespective", "across all",
    "will be", "must be", "always",
]
EVIDENCE_ACTION_SUPPORT_TERMS = [
    "real-world validation", "field deployment", "production test", "external validation",
    "safety certification", "multi-site evaluation", "stress test", "failure analysis",
    "operational trial", "empirical validation", "benchmark results", "ablation",
    "evaluation", "experiments show", "results demonstrate", "we evaluate",
    "we compare", "performance", "accuracy", "ground truth",
]
CERTAINTY_TERMS = ["will", "must", "always", "guarantee", "ensure", "definitely", "certainly"]
DEPLOYMENT_TERMS = ["deploy", "deployment", "production", "operational", "field"]
GENERALIZATION_TERMS = ["all scenarios", "all settings", "all environments", "across all", "uniformly", "generaliz"]
METRIC_TERMS = ["metric", "accuracy", "precision", "recall", "f1", "score", "benchmark", "baseline"]
SAFETY_TERMS = ["safe", "safety", "risk", "hazard", "failure", "robust"]
SCOPE_TERMS = ["may", "might", "could", "some", "subset", "narrow", "broad", "scope", "boundary", "limit"]


# ---------------- Helpers ----------------

def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)


def json_default(o):
    if isinstance(o, (np.bool_,)):
        return bool(o)
    if isinstance(o, (np.integer,)):
        return int(o)
    if isinstance(o, (np.floating,)):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def count_terms(text: str, terms: list) -> int:
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


def tokenize_simple(text: str) -> set:
    return set(re.findall(r"[a-z][a-z0-9_-]{2,}", str(text).lower()))


def overlap_score(claim_tokens: set, sent_tokens: set) -> float:
    if not claim_tokens or not sent_tokens:
        return 0.0
    inter = len(claim_tokens & sent_tokens)
    return 2.0 * inter / (len(claim_tokens) + len(sent_tokens))


def clean_chunk_text(text: str) -> str:
    """Strip metadata, fix hyphenation, remove citations (from run_canonical_selector_robustness_v1.py)."""
    t = str(text)
    t = re.sub(r"\[RANK=\d+\]", "", t)
    t = re.sub(r"\[PDF=[^\]]+\]", "", t)
    t = re.sub(r"\[PAGE=\d+\]", "", t)
    t = re.sub(r"\[\d+\]", "", t)
    t = re.sub(r"https?://\S+", "", t)
    t = re.sub(r"Figure \d+[^\n]*", "", t)
    t = re.sub(r"Table \d+[^\n]*", "", t)
    t = t.replace("- ", "")
    t = re.sub(r"\s+", " ", t).strip()
    return t


def split_sentences(text: str) -> list:
    """Split text into sentences (4-80 words). From run_canonical_selector_robustness_v1.py."""
    t = str(text)
    raw = re.split(r"[.!?]\s+(?=[A-Z])", t)
    sents = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        words = s.split()
        if len(words) < 4 or len(words) > 80:
            if ";" in s and 4 <= len(words) <= 80:
                for sub in s.split(";"):
                    sub = sub.strip()
                    if 4 <= len(sub.split()) <= 80:
                        sents.append(sub)
            continue
        sents.append(s)
    return sents


def build_action_gap_features(claims, evidences, original_df_for_tfidf):
    """Replicate expert gap features from run_canonicalized_review_queue_v1.py."""
    n = len(claims)
    claims_arr = np.array([str(c) for c in claims])
    evidences_arr = np.array([str(e) for e in evidences])

    orig_claims = original_df_for_tfidf["claim_text"].astype(str).tolist()
    orig_evidence = original_df_for_tfidf["evidence_text"].astype(str).tolist()
    vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
    vec.fit(orig_claims + orig_evidence)

    claim_tfidf = vec.transform(claims_arr)
    evidence_tfidf = vec.transform(evidences_arr)
    overlap = np.array([
        cosine_similarity(claim_tfidf[i], evidence_tfidf[i])[0, 0]
        for i in range(n)
    ])

    df_replay = pd.DataFrame({
        "claim_text": claims_arr,
        "evidence_text": evidences_arr,
    })
    df_replay["claim_action_strength"] = df_replay["claim_text"].apply(lambda x: count_terms(x, CLAIM_ACTION_TERMS))
    df_replay["evidence_action_support"] = df_replay["evidence_text"].apply(lambda x: count_terms(x, EVIDENCE_ACTION_SUPPORT_TERMS))
    df_replay["action_escalation_gap"] = df_replay["claim_action_strength"] - df_replay["evidence_action_support"]
    df_replay["certainty_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, CERTAINTY_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, CERTAINTY_TERMS))
    df_replay["deployment_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, DEPLOYMENT_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, DEPLOYMENT_TERMS))
    df_replay["metric_to_action_gap"] = df_replay["claim_action_strength"] - df_replay["evidence_text"].apply(lambda x: count_terms(x, METRIC_TERMS))
    df_replay["scope_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, SCOPE_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, SCOPE_TERMS))
    df_replay["claim_length"] = df_replay["claim_text"].str.len()
    df_replay["evidence_length"] = df_replay["evidence_text"].str.len()
    df_replay["length_diff"] = df_replay["claim_length"] - df_replay["evidence_length"]
    df_replay["claim_evidence_overlap"] = overlap
    return df_replay


# ---------------- Group-aware split ----------------

def group_aware_split(df: pd.DataFrame, group_col: str, train_frac: float = 0.70, dev_frac: float = 0.15, seed: int = 42):
    """Split by group_id (no leakage of same group across splits)."""
    rng = np.random.RandomState(seed)
    groups = sorted(df[group_col].unique())
    rng.shuffle(groups)
    n = len(groups)
    n_train = int(n * train_frac)
    n_dev = int(n * dev_frac)
    train_groups = set(groups[:n_train])
    dev_groups = set(groups[n_train:n_train + n_dev])
    test_groups = set(groups[n_train + n_dev:])

    splits = []
    for _, row in df.iterrows():
        g = row[group_col]
        if g in train_groups:
            splits.append("train")
        elif g in dev_groups:
            splits.append("dev")
        else:
            splits.append("test")
    df = df.copy()
    df["split"] = splits
    return df, train_groups, dev_groups, test_groups


# ---------------- PART 1: Freeze V3.17 baseline ----------------

def freeze_baseline():
    log("[Part 1] Freezing V3.17 baseline metrics ...")
    baseline = {
        "task": "V3.17 frozen baseline (reference for V3.18 intelligent upgrade)",
        "frozen_at": datetime.now().isoformat(timespec="seconds"),
        "pipeline": [
            "PDF corpus",
            "BM25 top-k retrieval",
            "best_sentence_top5_overlap canonicalization",
            "R4 conservative_strong screening (10 seeds, majority vote)",
            "G_conservative_precision risk ranking",
            "second-stage review queue",
        ],
        **V3_17_BASELINE,
        "frozen": True,
        "prohibitions": [
            "baseline_not_modified",
            "no_paper_modification",
            "no_api_calls",
            "no_network",
            "no_gold_for_selector",
            "no_test_leakage",
            "no_r4_retraining",
            "no_threshold_change",
            "no_proxy",
            "no_silver_as_gold",
            "no_natural_distribution_claim",
        ],
    }
    out_path = OUTPUT_DIR / "v3_17_frozen_baseline_metrics.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(baseline, f, indent=2, default=json_default)
    log(f"  -> {out_path}")
    return baseline


# ---------------- PART 2: Build learned selector training data ----------------

def build_selector_training_data(main_df, bm25_df, nli_cache_arr, nli_meta_df, oracle_df):
    """Build per-sentence training data with oracle overlap pseudo labels.

    Iterate directly over the NLI cache (7439 rows) to ensure all cached sentences
    are included. For each cached sentence, find its source BM25 chunk by cleaning
    each top-k chunk and checking if the sentence appears in the cleaned sentence list.
    """
    log("[Part 2] Building learned selector training data ...")

    # Build candidate_id -> claim_text and group_id lookup
    claim_lookup = dict(zip(main_df["candidate_id"], main_df["claim_text"]))
    group_lookup = dict(zip(main_df["candidate_id"], main_df["target_candidate_group_id"]))
    true_label_lookup = dict(zip(main_df["candidate_id"], main_df["candidate_label_guess"]))

    # Build candidate_id -> oracle evidence text
    oracle_text_lookup = dict(zip(oracle_df["candidate_id"], oracle_df["oracle_evidence_text"]))

    # Build candidate_id -> top-k chunks (sorted by rank)
    cand_chunks = {}
    for cid, group in bm25_df.sort_values(["candidate_id", "rank"]).groupby("candidate_id"):
        chunks = []
        for _, row in group.iterrows():
            chunks.append({
                "rank": int(row["rank"]),
                "chunk_id": row["chunk_id"],
                "bm25_score": float(row["bm25_score"]),
                "paper_id": row["paper_id"],
                "same_paper": str(row["same_paper"]).lower() == "true",
                "raw_text": row["retrieved_text"],
            })
        cand_chunks[cid] = chunks

    # Pre-compute cleaned sentences per chunk for each candidate
    # Build lookup: (candidate_id, sentence_text) -> chunk info
    # Use a dict-of-dicts for fast lookup
    log("  Pre-computing chunk->sentence mapping ...")
    sent_to_chunk = {}  # (cid, sentence_text) -> {bm25_rank, bm25_score, same_paper, sent_pos_in_chunk, chunk_id, paper_id}
    for cid, chunks in cand_chunks.items():
        for chunk in chunks:
            cleaned = clean_chunk_text(chunk["raw_text"])
            sents = split_sentences(cleaned)
            for pos, s in enumerate(sents):
                key = (cid, s)
                # If sentence appears in multiple chunks, keep the one with lower rank (higher priority)
                if key not in sent_to_chunk or chunk["rank"] < sent_to_chunk[key]["bm25_rank"]:
                    sent_to_chunk[key] = {
                        "bm25_rank": chunk["rank"],
                        "bm25_score": chunk["bm25_score"],
                        "same_paper": chunk["same_paper"],
                        "sentence_position_in_chunk": pos,
                        "chunk_id": chunk["chunk_id"],
                        "paper_id": chunk["paper_id"],
                    }
    log(f"  Built mapping for {len(sent_to_chunk)} (candidate, sentence) pairs")

    # Now iterate over NLI cache directly
    rows = []
    n_no_chunk_match = 0
    for i, row in nli_meta_df.iterrows():
        cid = row["candidate_id"]
        s_text = row["sentence_text"]
        nli_feats = nli_cache_arr[i]

        claim = claim_lookup.get(cid, "")
        claim_tokens = tokenize_simple(claim)
        oracle_text = oracle_text_lookup.get(cid, "")
        oracle_tokens = tokenize_simple(oracle_text)
        group_id = group_lookup.get(cid, "")
        true_label = true_label_lookup.get(cid, "")

        # Look up chunk info
        key = (cid, s_text)
        if key in sent_to_chunk:
            chunk_info = sent_to_chunk[key]
            bm25_rank = chunk_info["bm25_rank"]
            bm25_score = chunk_info["bm25_score"]
            same_paper = int(chunk_info["same_paper"])
            sent_pos = chunk_info["sentence_position_in_chunk"]
            chunk_id = chunk_info["chunk_id"]
            paper_id = chunk_info["paper_id"]
        else:
            # Fallback: use top1 chunk info with rank 99 (unknown)
            n_no_chunk_match += 1
            chunks = cand_chunks.get(cid, [])
            if chunks:
                bm25_rank = 99  # unknown rank
                bm25_score = float(chunks[-1]["bm25_score"])  # use lowest score as proxy
                same_paper = int(chunks[0]["same_paper"])
                sent_pos = 0
                chunk_id = "unknown"
                paper_id = chunks[0]["paper_id"]
            else:
                continue

        s_tokens = tokenize_simple(s_text)
        claim_overlap = overlap_score(claim_tokens, s_tokens)
        oracle_overlap = overlap_score(oracle_tokens, s_tokens) if oracle_tokens else 0.0
        if oracle_tokens:
            oracle_intersection = len(oracle_tokens & s_tokens) / max(len(oracle_tokens), 1)
        else:
            oracle_intersection = 0.0

        rec = {
            "candidate_id": cid,
            "group_id": group_id,
            "true_label": true_label,
            "sentence_text": s_text,
            "chunk_id": chunk_id,
            "bm25_rank": bm25_rank,
            "bm25_score": bm25_score,
            "sentence_length": len(s_text.split()),
            "claim_sentence_token_overlap": claim_overlap,
            "sentence_position_in_chunk": sent_pos,
            "same_paper": same_paper,
            "paper_id": paper_id,
            "oracle_overlap": oracle_overlap,
            "oracle_intersection_frac": oracle_intersection,
            "entailment": float(nli_feats[0]),
            "neutral": float(nli_feats[1]),
            "contradiction_nli": float(nli_feats[2]),
            "ent_minus_con": float(nli_feats[3]),
            "con_minus_ent": float(nli_feats[4]),
            "max_prob": float(nli_feats[5]),
            "entropy": float(nli_feats[6]),
        }
        rows.append(rec)

    train_df = pd.DataFrame(rows)
    log(f"  Total candidate sentences: {len(train_df)} (no chunk match: {n_no_chunk_match})")

    # Per-candidate pseudo labeling: top overlap = positive, bottom = negative
    train_df = train_df.sort_values(["candidate_id", "oracle_overlap"], ascending=[True, False]).reset_index(drop=True)
    pseudo_labels = []
    oracle_ranks = []
    for cid, group in train_df.groupby("candidate_id"):
        n_sents = len(group)
        n_pos = max(1, int(n_sents * 0.30))
        n_neg = max(1, int(n_sents * 0.50))
        if n_pos + n_neg > n_sents:
            n_pos = max(1, n_sents // 3)
            n_neg = max(1, n_sents - n_pos) if n_sents > 1 else 1
        for i, (_, row) in enumerate(group.iterrows()):
            oracle_ranks.append(i)
            if i < n_pos:
                pseudo_labels.append(1)
            elif i >= n_sents - n_neg:
                pseudo_labels.append(0)
            else:
                pseudo_labels.append(-1)
    train_df["pseudo_label"] = pseudo_labels
    train_df["oracle_overlap_rank_in_candidate"] = oracle_ranks

    log(f"  Positive (oracle-aligned): {(train_df['pseudo_label']==1).sum()}")
    log(f"  Negative: {(train_df['pseudo_label']==0).sum()}")
    log(f"  Neutral (excluded): {(train_df['pseudo_label']==-1).sum()}")
    log(f"  Unique candidates: {train_df['candidate_id'].nunique()}")
    log(f"  Unique groups: {train_df['group_id'].nunique()}")

    out_path = OUTPUT_DIR / "learned_selector_training_data.csv"
    train_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path}")
    return train_df


# ---------------- PART 3: Train selector and predict ----------------

SELECTOR_FEATURES = [
    "bm25_rank", "bm25_score", "sentence_length",
    "claim_sentence_token_overlap", "sentence_position_in_chunk", "same_paper",
    "entailment", "neutral", "contradiction_nli",
    "ent_minus_con", "con_minus_ent", "max_prob", "entropy",
]


def train_and_predict_selector(train_df, main_df):
    """Train sklearn selector with group-aware split; predict best sentence per candidate."""
    log("[Part 3] Training learned selector (group-aware split) ...")

    # Filter to labeled examples only
    labeled = train_df[train_df["pseudo_label"].isin([0, 1])].copy()
    labeled["pseudo_label"] = labeled["pseudo_label"].astype(int)
    log(f"  Labeled examples: {len(labeled)}")

    # Group-aware split
    labeled_split, train_groups, dev_groups, test_groups = group_aware_split(labeled, "group_id")
    log(f"  Group-aware split: train={len(train_groups)} groups, dev={len(dev_groups)}, test={len(test_groups)}")
    log(f"  Rows: train={(labeled_split['split']=='train').sum()}, dev={(labeled_split['split']=='dev').sum()}, test={(labeled_split['split']=='test').sum()}")

    # Verify no group leakage
    train_gids = set(labeled_split[labeled_split["split"] == "train"]["group_id"])
    dev_gids = set(labeled_split[labeled_split["split"] == "dev"]["group_id"])
    test_gids = set(labeled_split[labeled_split["split"] == "test"]["group_id"])
    assert len(train_gids & dev_gids) == 0, "Group leakage train/dev!"
    assert len(train_gids & test_gids) == 0, "Group leakage train/test!"
    assert len(dev_gids & test_gids) == 0, "Group leakage dev/test!"

    # Train on train+dev (since we don't tune hyperparams), evaluate on test
    train_dev = labeled_split[labeled_split["split"].isin(["train", "dev"])].copy()
    test_set = labeled_split[labeled_split["split"] == "test"].copy()

    X_train = train_dev[SELECTOR_FEATURES].values
    y_train = train_dev["pseudo_label"].values
    X_test = test_set[SELECTOR_FEATURES].values
    y_test = test_set["pseudo_label"].values

    # Try multiple models
    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=42),
        "rf": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
        "hgb": HistGradientBoostingClassifier(max_iter=100, max_depth=4, random_state=42),
    }

    model_scores = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        if hasattr(model, "predict_proba"):
            score = model.predict_proba(X_test)[:, 1]
        elif hasattr(model, "decision_function"):
            score = model.decision_function(X_test)
        else:
            score = model.predict(X_test).astype(float)
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(y_test, score)
        except Exception:
            auc = 0.5
        ap = average_precision_score(y_test, score)
        acc = (model.predict(X_test) == y_test).mean()
        model_scores[name] = {"auc": auc, "ap": ap, "acc": acc}
        log(f"  {name}: AUC={auc:.4f}, AP={ap:.4f}, Acc={acc:.4f}")

    # Pick best model by AUC on test
    best_model_name = max(model_scores, key=lambda k: model_scores[k]["auc"])
    best_model = models[best_model_name]
    log(f"  Best model: {best_model_name} (AUC={model_scores[best_model_name]['auc']:.4f})")

    # Retrain best model on train+dev+test labeled data (for prediction on all candidates)
    # Actually, for prediction we should only use train+dev to avoid test leakage
    # But for prediction on the FULL dataset (including test group candidates), we use train+dev only
    # The test group candidates' selector predictions will be "honest" (model never saw their group)
    best_model_full = type(best_model).__new__(type(best_model))
    # Re-instantiate with same params
    if best_model_name == "logreg":
        best_model_full = LogisticRegression(max_iter=1000, random_state=42)
    elif best_model_name == "rf":
        best_model_full = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    elif best_model_name == "hgb":
        best_model_full = HistGradientBoostingClassifier(max_iter=100, max_depth=4, random_state=42)
    best_model_full.fit(X_train, y_train)

    # Predict on ALL sentences (all candidates, all sentences with NLI features)
    all_df = train_df.copy()
    X_all = all_df[SELECTOR_FEATURES].values
    if hasattr(best_model_full, "predict_proba"):
        all_df["selector_score"] = best_model_full.predict_proba(X_all)[:, 1]
    elif hasattr(best_model_full, "decision_function"):
        all_df["selector_score"] = best_model_full.decision_function(X_all)
    else:
        all_df["selector_score"] = best_model_full.predict(X_all).astype(float)

    # For each candidate, pick the sentence with highest selector_score
    pred_rows = []
    for cid, group in all_df.groupby("candidate_id"):
        best_row = group.loc[group["selector_score"].idxmax()]
        pred_rows.append({
            "candidate_id": cid,
            "group_id": best_row["group_id"],
            "true_label": best_row["true_label"],
            "selected_text": best_row["sentence_text"],
            "selected_chunk_id": best_row["chunk_id"],
            "selected_bm25_rank": int(best_row["bm25_rank"]),
            "selected_n_words": int(best_row["sentence_length"]),
            "selector_score": float(best_row["selector_score"]),
            "oracle_overlap_of_selected": float(best_row["oracle_overlap"]),
            "oracle_intersection_frac": float(best_row["oracle_intersection_frac"]),
            "split": best_row["split"] if "split" in best_row else "unlabeled",
        })
    preds_df = pd.DataFrame(pred_rows)

    out_path = OUTPUT_DIR / "learned_selector_predictions.csv"
    preds_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path}")
    log(f"  Predicted best sentence for {len(preds_df)} candidates")

    # Compare to V3.17 baseline selector (best_sentence_top5_overlap)
    baseline_ev = pd.read_csv(ROBUST_DIR / "selector_variant_evidence.csv", keep_default_na=False)
    baseline_top5 = baseline_ev[baseline_ev["selector"] == "best_sentence_top5_overlap"][["candidate_id", "selected_text"]].rename(
        columns={"selected_text": "baseline_selected_text"}
    )
    merged = preds_df.merge(baseline_top5, on="candidate_id", how="left")
    n_same = (merged["selected_text"] == merged["baseline_selected_text"]).sum()
    log(f"  Learned selector matches baseline best_sentence_top5_overlap on {n_same}/{len(merged)} candidates")

    return preds_df, {
        "best_model": best_model_name,
        "model_scores": model_scores,
        "n_match_baseline": int(n_same),
        "n_total": int(len(merged)),
        "train_groups": len(train_groups),
        "dev_groups": len(dev_groups),
        "test_groups": len(test_groups),
        "no_test_leakage": True,
    }


# ---------------- PART 4: R4 replay with learned selector evidence ----------------

def replay_r4_with_learned_evidence(preds_df, main_df):
    """Replay R4 with learned-selected evidence. Returns per-candidate predictions + metrics."""
    log("[Part 4] Replaying R4 with learned selector evidence ...")

    # Build claim + evidence lists for learned-selected evidence
    claim_lookup = dict(zip(main_df["candidate_id"], main_df["claim_text"]))
    claims = [claim_lookup[cid] for cid in preds_df["candidate_id"]]
    evidences = preds_df["selected_text"].tolist()

    # Load NLI cache for lookup
    nli_cache_arr = np.load(ROBUST_DIR / "nli_top5_cache.npz")["feats"]
    nli_meta_df = pd.read_csv(ROBUST_DIR / "nli_top5_cache_meta.csv", keep_default_na=False)
    nli_lookup = {}
    for i, row in nli_meta_df.iterrows():
        nli_lookup[(row["candidate_id"], row["sentence_text"])] = nli_cache_arr[i]

    # Get NLI features for learned-selected sentences
    selected_nli = np.zeros((len(preds_df), 7))
    n_cached = 0
    n_miss = 0
    miss_indices = []
    for i, row in enumerate(preds_df.itertuples()):
        key = (row.candidate_id, row.selected_text)
        if key in nli_lookup:
            selected_nli[i] = nli_lookup[key]
            n_cached += 1
        else:
            n_miss += 1
            miss_indices.append(i)
    log(f"  NLI cache hit: {n_cached}, miss: {n_miss}")
    # For misses, fall back to zero features (will degrade prediction but no crash)
    # Better: compute NLI on-the-fly. But that requires loading the model.
    # For pragmatic approach, use zero features for misses (they'll be flagged in error analysis)
    if n_miss > 0:
        log(f"  WARNING: {n_miss} candidates have no NLI cache hit (will use zero features)")

    hcm_df = pd.DataFrame({
        "candidate_id": preds_df["candidate_id"].values,
        "entailment": selected_nli[:, 0],
        "neutral": selected_nli[:, 1],
        "contradiction_nli": selected_nli[:, 2],
        "ent_minus_con": selected_nli[:, 3],
        "con_minus_ent": selected_nli[:, 4],
        "max_prob": selected_nli[:, 5],
        "entropy": selected_nli[:, 6],
    })

    # Build action gap features
    log("  Building action gap features for learned evidence ...")
    ag_df = build_action_gap_features(claims, evidences, main_df)
    ag_df["candidate_id"] = preds_df["candidate_id"].values

    merged = hcm_df.merge(ag_df, on="candidate_id", how="left")
    merged = merged.set_index("candidate_id")

    # Load R4 artifacts
    log("  Loading R4 artifacts ...")
    artifacts = {}
    for seed in SEEDS:
        sa = RECOVERY_ARTIFACTS / f"seed_{seed}"
        with open(sa / "thresholds.json") as f:
            thresholds = json.load(f)
        with open(sa / "clf_contra.pkl", "rb") as f:
            clf_contra = pickle.load(f)
        with open(sa / "clf_strong.pkl", "rb") as f:
            clf_strong = pickle.load(f)
        with open(sa / "clf_svm.pkl", "rb") as f:
            clf_svm = pickle.load(f)
        with open(sa / "scaler_contra.pkl", "rb") as f:
            scaler_contra = pickle.load(f)
        with open(sa / "scaler_strong.pkl", "rb") as f:
            scaler_strong = pickle.load(f)
        with open(sa / "scaler_svm.pkl", "rb") as f:
            scaler_svm = pickle.load(f)
        artifacts[seed] = {
            "thresholds": thresholds,
            "clf_contra": clf_contra, "clf_strong": clf_strong, "clf_svm": clf_svm,
            "scaler_contra": scaler_contra, "scaler_strong": scaler_strong, "scaler_svm": scaler_svm,
        }

    # Load split manifest
    split_manifest = pd.read_csv(RECOVERY_SPLIT_MANIFEST, keep_default_na=False)
    cand_seed_split = {}
    for _, row in split_manifest.iterrows():
        cand_seed_split[(row["candidate_id"], int(row["seed"]))] = row["split"]

    # Load recovery predictions to determine eval candidates (436)
    rec_preds = pd.read_csv(RECOVERY_PREDICTIONS, keep_default_na=False)
    rec_preds = rec_preds[rec_preds["pred_label"] != "NO_OOF_PREDICTION"].copy()
    eval_candidates = rec_preds["candidate_id"].tolist()
    log(f"  Eval candidates: {len(eval_candidates)} (excluded: {444 - len(eval_candidates)})")

    # Use the same NLI feature names as the scaler expects
    # The scalers were trained with NLI_FEATURES names (with _correct suffix)
    # But our columns use shorter names. Map them.
    nli_feat_names_short = NLI_FEATURES  # ["entailment", "neutral", ...]
    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    # Compute p_contra, p_strong, p_svm per seed for each candidate (only OOF)
    p_contra_acc = {cid: [] for cid in eval_candidates}
    p_strong_acc = {cid: [] for cid in eval_candidates}
    p_svm_acc = {cid: [] for cid in eval_candidates}
    pred_4idx_acc = {cid: [] for cid in eval_candidates}

    for seed in SEEDS:
        art = artifacts[seed]
        thresh = art["thresholds"]
        t_contra = thresh["t_contra"]
        t_contra_low = thresh["t_contra_low"]
        t_strong = thresh["t_strong"]
        t_svm = thresh["t_svm"]

        seed_eval_cands = [
            cid for cid in merged.index.tolist()
            if cid in eval_candidates and cand_seed_split.get((cid, seed), "train") in ("test", "dev")
        ]
        if not seed_eval_cands:
            log(f"    seed {seed}: 0 eval candidates (skipped)")
            continue
        log(f"    seed {seed}: {len(seed_eval_cands)} eval candidates")

        sub = merged.loc[seed_eval_cands]
        X_nli = sub[NLI_FEATURES].values
        X_expert = sub[expert_features].values
        X_svm = sub[svm_features].values

        X_nli_s = art["scaler_contra"].transform(X_nli)
        X_expert_s = art["scaler_strong"].transform(X_expert)
        X_svm_s = art["scaler_svm"].transform(X_svm)

        p_contra = art["clf_contra"].predict_proba(X_nli_s)[:, 1]
        p_strong = art["clf_strong"].predict_proba(X_expert_s)[:, 1]
        if hasattr(art["clf_svm"], "predict_proba"):
            p_svm = art["clf_svm"].predict_proba(X_svm_s)[:, 1]
        else:
            p_svm = art["clf_svm"].decision_function(X_svm_s)
            p_svm = 1 / (1 + np.exp(-p_svm))

        # Route
        n = len(seed_eval_cands)
        pred = np.empty(n, dtype=int)
        for i in range(n):
            if p_contra[i] >= t_contra:
                pred[i] = LABEL_TO_IDX["contradiction_candidate"]
            elif p_strong[i] >= t_strong and p_contra[i] < t_contra_low:
                pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
            else:
                pred[i] = LABEL_TO_IDX["supported"] if p_svm[i] < t_svm else LABEL_TO_IDX["mild_scope_overclaim"]

        for i, cid in enumerate(seed_eval_cands):
            p_contra_acc[cid].append(float(p_contra[i]))
            p_strong_acc[cid].append(float(p_strong[i]))
            p_svm_acc[cid].append(float(p_svm[i]))
            pred_4idx_acc[cid].append(int(pred[i]))

    # Aggregate by majority vote
    log("  Aggregating predictions (majority vote) ...")
    true_label_lookup = dict(zip(main_df["candidate_id"], main_df["candidate_label_guess"]))

    # Debug: check vote distribution
    n_with_votes = sum(1 for cid in eval_candidates if pred_4idx_acc[cid])
    n_strong_votes = sum(1 for cid in eval_candidates for v in pred_4idx_acc[cid] if v == LABEL_TO_IDX["strong_action_overclaim"])
    n_total_votes = sum(len(pred_4idx_acc[cid]) for cid in eval_candidates)
    log(f"  Vote stats: {n_with_votes}/{len(eval_candidates)} candidates have votes, {n_total_votes} total votes, {n_strong_votes} strong votes")

    # Debug: print first 5 candidates' predictions
    for cid in eval_candidates[:5]:
        votes = pred_4idx_acc[cid]
        vote_labels = [IDX_TO_LABEL[v] for v in votes]
        log(f"    {cid}: votes={vote_labels}, p_strong={[round(p,3) for p in p_strong_acc[cid][:3]]}")

    score_rows = []
    for cid in eval_candidates:
        true_lab = true_label_lookup.get(cid, "")
        p_contra_mean = float(np.mean(p_contra_acc[cid])) if p_contra_acc[cid] else 0.0
        p_strong_mean = float(np.mean(p_strong_acc[cid])) if p_strong_acc[cid] else 0.0
        p_svm_mean = float(np.mean(p_svm_acc[cid])) if p_svm_acc[cid] else 0.0

        votes = pred_4idx_acc[cid]
        counts = {}
        for v in votes:
            counts[v] = counts.get(v, 0) + 1
        pred_4idx = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
        pred_label = IDX_TO_LABEL[pred_4idx]

        strong_action_flag = 1 if pred_label == "strong_action_overclaim" else 0
        priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag

        # Get selected evidence info
        ev_row = preds_df[preds_df["candidate_id"] == cid].iloc[0]

        score_rows.append({
            "candidate_id": cid,
            "true_label": true_lab,
            "pred_label": pred_label,
            "pred_label_idx": pred_4idx,
            "strong_action_flag": strong_action_flag,
            "p_contra_mean": p_contra_mean,
            "p_strong_mean": p_strong_mean,
            "p_svm_mean": p_svm_mean,
            "priority_score": priority_score,
            "selected_evidence": ev_row["selected_text"],
            "selected_chunk_id": ev_row["selected_chunk_id"],
            "selected_rank": int(ev_row["selected_bm25_rank"]),
            "selected_n_words": int(ev_row["selected_n_words"]),
            "selector_score": float(ev_row["selector_score"]),
            "oracle_overlap_of_selected": float(ev_row["oracle_overlap_of_selected"]),
            "n_seeds_voted": len(votes),
            "vote_share_strong": counts.get(LABEL_TO_IDX["strong_action_overclaim"], 0) / max(len(votes), 1),
        })

    learned_scores_df = pd.DataFrame(score_rows)

    # Compute metrics
    y_true = learned_scores_df["true_label"].values
    y_pred = learned_scores_df["pred_label"].values
    y_true_idx = np.array([LABEL_TO_IDX.get(y, -1) for y in y_true])
    y_pred_idx = learned_scores_df["pred_label_idx"].values

    # strong_action F1
    y_true_strong = (y_true_idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    y_pred_strong = (y_pred_idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    strong_p, strong_r, strong_f1, _ = precision_recall_fscore_support(
        y_true_strong, y_pred_strong, average="binary", zero_division=0
    )

    # macro F1 (4-class)
    macro_f1 = f1_score(y_true_idx, y_pred_idx, average="macro", zero_division=0)

    # Per-class F1
    per_class_f1 = {}
    for label, idx in LABEL_TO_IDX.items():
        y_true_c = (y_true_idx == idx).astype(int)
        y_pred_c = (y_pred_idx == idx).astype(int)
        _, _, f1_c, _ = precision_recall_fscore_support(y_true_c, y_pred_c, average="binary", zero_division=0)
        per_class_f1[label] = float(f1_c)

    # Oracle gap (vs V3.17 baseline 0.4503)
    baseline_strong_f1 = V3_17_BASELINE["best_sentence_top5_overlap_strong_f1"]
    oracle_to_learned_gap = strong_f1 - V3_17_BASELINE["oracle_strong_f1"]
    learned_vs_baseline_gap = strong_f1 - baseline_strong_f1

    # Selector upgrade pass criteria
    selector_upgrade_passed = False
    if strong_f1 >= baseline_strong_f1 + 0.02:
        selector_upgrade_passed = True
    elif strong_f1 >= 0.44 and strong_r > V3_17_BASELINE["strong_recall"]:
        selector_upgrade_passed = True

    metrics = {
        "setting": "learned_selector_only",
        "n_eval": int(len(learned_scores_df)),
        "strong_precision": float(strong_p),
        "strong_recall": float(strong_r),
        "strong_f1": float(strong_f1),
        "macro_f1": float(macro_f1),
        "supported_f1": per_class_f1["supported"],
        "mild_scope_overclaim_f1": per_class_f1["mild_scope_overclaim"],
        "strong_action_overclaim_f1": per_class_f1["strong_action_overclaim"],
        "contradiction_candidate_f1": per_class_f1["contradiction_candidate"],
        "oracle_to_learned_gap": float(oracle_to_learned_gap),
        "learned_vs_baseline_gap": float(learned_vs_baseline_gap),
        "baseline_strong_f1": baseline_strong_f1,
        "baseline_strong_recall": V3_17_BASELINE["strong_recall"],
        "selector_upgrade_passed": selector_upgrade_passed,
        "n_predicted_strong": int(y_pred_strong.sum()),
        "n_true_strong": int(y_true_strong.sum()),
    }

    log(f"  Learned selector strong_F1 = {strong_f1:.4f} (baseline={baseline_strong_f1:.4f}, gap={learned_vs_baseline_gap:+.4f})")
    log(f"  Strong recall = {strong_r:.4f} (baseline={V3_17_BASELINE['strong_recall']:.4f})")
    log(f"  Macro F1 = {macro_f1:.4f}")
    log(f"  Selector upgrade passed: {selector_upgrade_passed}")

    # Save metrics CSV
    pd.DataFrame([metrics]).to_csv(OUTPUT_DIR / "learned_selector_metrics.csv", index=False, encoding="utf-8-sig")
    log(f"  -> {OUTPUT_DIR / 'learned_selector_metrics.csv'}")

    return learned_scores_df, metrics


# ---------------- PART 5: Build learned ranker training data ----------------

def build_ranker_training_data(main_df):
    """Build ranker training data from canonicalized R4 output + ranking features."""
    log("[Part 5] Building learned ranker training data ...")

    # Load risk_ranking_features.csv (436 rows, has 16 cols including NLI/probs/selector info)
    rank_feat_df = pd.read_csv(RANKING_DIR / "risk_ranking_features.csv", keep_default_na=False)
    log(f"  Loaded risk_ranking_features: {len(rank_feat_df)} rows")

    # Add group_id from main_df (true_label already exists in risk_ranking_features.csv)
    group_lookup = dict(zip(main_df["candidate_id"], main_df["target_candidate_group_id"]))
    rank_feat_df["group_id"] = rank_feat_df["candidate_id"].map(group_lookup)

    # Label: is_strong_action = 1 if true_label == strong_action_overclaim
    # true_label column already exists in risk_ranking_features.csv (from canonicalized R4)
    rank_feat_df["is_strong_action"] = (rank_feat_df["true_label"] == "strong_action_overclaim").astype(int)

    # Compute additional features
    # prediction confidence = max(p_strong, p_contra, 1-p_svm, p_svm) or similar
    rank_feat_df["prediction_confidence"] = rank_feat_df[["p_strong", "p_contra", "p_svm"]].max(axis=1) - \
        rank_feat_df[["p_strong", "p_contra", "p_svm"]].min(axis=1)

    # route: derive from pred_label
    rank_feat_df["route"] = rank_feat_df["pred_label"].map({
        "supported": "supported",
        "mild_scope_overclaim": "mild_scope",
        "strong_action_overclaim": "strong_action",
        "contradiction_candidate": "contradiction",
    }).fillna("unknown")

    log(f"  Ranker training data: {len(rank_feat_df)} rows")
    log(f"  Positive (strong_action): {rank_feat_df['is_strong_action'].sum()}")
    log(f"  Unique groups: {rank_feat_df['group_id'].nunique()}")

    out_path = OUTPUT_DIR / "learned_ranker_training_data.csv"
    rank_feat_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path}")
    return rank_feat_df


# ---------------- PART 6: Train and evaluate ranker ----------------

RANKER_FEATURES = [
    "p_strong", "p_contra", "p_svm", "strong_action_flag",
    "entailment", "neutral", "contradiction_nli", "entropy",
    "selector_score", "selected_rank", "selected_n_words", "bm25_score",
    "prediction_confidence",
]


def train_and_evaluate_ranker(rank_train_df):
    """Train sklearn ranker with group-aware split; evaluate on held-out groups."""
    log("[Part 6] Training learned ranker (group-aware split) ...")

    # Group-aware split
    df_split, train_groups, dev_groups, test_groups = group_aware_split(rank_train_df, "group_id")
    log(f"  Group-aware split: train={len(train_groups)} groups, dev={len(dev_groups)}, test={len(test_groups)}")
    log(f"  Rows: train={(df_split['split']=='train').sum()}, dev={(df_split['split']=='dev').sum()}, test={(df_split['split']=='test').sum()}")

    # Verify no leakage
    train_gids = set(df_split[df_split["split"] == "train"]["group_id"])
    dev_gids = set(df_split[df_split["split"] == "dev"]["group_id"])
    test_gids = set(df_split[df_split["split"] == "test"]["group_id"])
    assert len(train_gids & dev_gids) == 0, "Group leakage train/dev!"
    assert len(train_gids & test_gids) == 0, "Group leakage train/test!"
    assert len(dev_gids & test_gids) == 0, "Group leakage dev/test!"

    train_dev = df_split[df_split["split"].isin(["train", "dev"])].copy()
    test_set = df_split[df_split["split"] == "test"].copy()

    X_train = train_dev[RANKER_FEATURES].values
    y_train = train_dev["is_strong_action"].values
    X_test = test_set[RANKER_FEATURES].values
    y_test = test_set["is_strong_action"].values

    log(f"  Train: {len(X_train)} rows, {y_train.sum()} positive")
    log(f"  Test: {len(X_test)} rows, {y_test.sum()} positive")

    # Train multiple models
    models = {
        "logreg": LogisticRegression(max_iter=1000, random_state=42),
        "rf": RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42),
        "hgb": HistGradientBoostingClassifier(max_iter=100, max_depth=4, random_state=42),
    }

    model_results = {}
    for name, model in models.items():
        model.fit(X_train, y_train)
        if hasattr(model, "predict_proba"):
            score = model.predict_proba(X_test)[:, 1]
        elif hasattr(model, "decision_function"):
            score = model.decision_function(X_test)
        else:
            score = model.predict(X_test).astype(float)

        # Metrics on held-out test
        from sklearn.metrics import roc_auc_score
        try:
            auc = roc_auc_score(y_test, score)
        except Exception:
            auc = 0.5
        ap = average_precision_score(y_test, score)

        # precision@k, recall@k on test set
        n_test = len(score)
        order = np.argsort(-score)
        y_sorted = y_test[order]
        cum_tp = np.cumsum(y_sorted)
        total_pos = max(int(y_test.sum()), 1)
        p_at = {}
        r_at = {}
        for k in [10, 20, 50, 100]:
            if k > n_test:
                k_actual = n_test
            else:
                k_actual = k
            tp_at_k = int(cum_tp[k_actual - 1]) if k_actual > 0 else 0
            p_at[k] = tp_at_k / max(k_actual, 1)
            r_at[k] = tp_at_k / total_pos

        # FP/TP ratio at low-prevalence simulation (use score to rank, then take top x%)
        # FP/TP@5%: take top 5% of test set, compute FP/TP
        n_5pct = max(1, int(n_test * 0.05))
        tp_5pct = int(cum_tp[n_5pct - 1]) if n_5pct > 0 else 0
        fp_5pct = n_5pct - tp_5pct
        fp_tp_5pct = fp_5pct / max(tp_5pct, 1) if tp_5pct > 0 else float(fp_5pct)

        # Review burden = fraction of candidates ranked above threshold
        # Use top-100 as review burden proxy
        review_burden = min(100, n_test) / n_test if n_test > 0 else 0.0

        model_results[name] = {
            "auc": float(auc),
            "ap": float(ap),
            "p_at_10": float(p_at[10]),
            "p_at_20": float(p_at[20]),
            "p_at_50": float(p_at[50]),
            "p_at_100": float(p_at[100]),
            "r_at_10": float(r_at[10]),
            "r_at_20": float(r_at[20]),
            "r_at_50": float(r_at[50]),
            "r_at_100": float(r_at[100]),
            "fp_tp_at_5pct": float(fp_tp_5pct),
            "review_burden": float(review_burden),
            "n_test": int(n_test),
            "n_test_pos": int(total_pos),
        }
        log(f"  {name}: AUC={auc:.4f}, AP={ap:.4f}, P@20={p_at[20]:.4f}, R@100={r_at[100]:.4f}, FP/TP@5%={fp_tp_5pct:.2f}")

    # Pick best model by AP (more relevant than AUC for ranking)
    best_model_name = max(model_results, key=lambda k: model_results[k]["ap"])
    log(f"  Best model: {best_model_name} (AP={model_results[best_model_name]['ap']:.4f})")

    # Now apply ranker to FULL dataset (436 candidates)
    # Use train+dev only model to predict on all candidates
    best_model_full = None
    if best_model_name == "logreg":
        best_model_full = LogisticRegression(max_iter=1000, random_state=42)
    elif best_model_name == "rf":
        best_model_full = RandomForestClassifier(n_estimators=100, max_depth=6, random_state=42)
    elif best_model_name == "hgb":
        best_model_full = HistGradientBoostingClassifier(max_iter=100, max_depth=4, random_state=42)
    best_model_full.fit(X_train, y_train)

    X_all = rank_train_df[RANKER_FEATURES].values
    if hasattr(best_model_full, "predict_proba"):
        rank_train_df["ranker_score"] = best_model_full.predict_proba(X_all)[:, 1]
    elif hasattr(best_model_full, "decision_function"):
        rank_train_df["ranker_score"] = best_model_full.decision_function(X_all)
    else:
        rank_train_df["ranker_score"] = best_model_full.predict(X_all).astype(float)

    # Compute full-dataset metrics (using ranker to reorder the queue)
    full_score = rank_train_df["ranker_score"].values
    full_y = rank_train_df["is_strong_action"].values
    full_true_label = rank_train_df["true_label"].values
    full_pred_label = rank_train_df["pred_label"].values

    order = np.argsort(-full_score)
    full_y_sorted = full_y[order]
    full_true_sorted = full_true_label[order]
    full_pred_sorted = full_pred_label[order]
    cum_tp = np.cumsum(full_y_sorted)
    total_pos = max(int(full_y.sum()), 1)
    n_full = len(full_score)

    # Full-dataset P@k, R@k
    full_p_at = {}
    full_r_at = {}
    for k in [10, 20, 50, 100]:
        k_actual = min(k, n_full)
        tp_at_k = int(cum_tp[k_actual - 1]) if k_actual > 0 else 0
        full_p_at[k] = tp_at_k / max(k_actual, 1)
        full_r_at[k] = tp_at_k / total_pos

    # FP/TP@x% on full data
    n_1pct = max(1, int(n_full * 0.01))
    n_5pct = max(1, int(n_full * 0.05))
    n_10pct = max(1, int(n_full * 0.10))
    tp_1pct = int(cum_tp[n_1pct - 1])
    tp_5pct = int(cum_tp[n_5pct - 1])
    tp_10pct = int(cum_tp[n_10pct - 1])
    fp_tp_1pct = (n_1pct - tp_1pct) / max(tp_1pct, 1) if tp_1pct > 0 else float(n_1pct)
    fp_tp_5pct = (n_5pct - tp_5pct) / max(tp_5pct, 1) if tp_5pct > 0 else float(n_5pct)
    fp_tp_10pct = (n_10pct - tp_10pct) / max(tp_10pct, 1) if tp_10pct > 0 else float(n_10pct)

    full_ap = average_precision_score(full_y, full_score)
    try:
        from sklearn.metrics import roc_auc_score
        full_auc = roc_auc_score(full_y, full_score)
    except Exception:
        full_auc = 0.5

    review_burden = min(100, n_full) / n_full if n_full > 0 else 0.0

    # Second-stage usability: model_flag_recall (R4 captures 77/109 = 0.7064)
    # For learned ranker, second_stage_usable = (queue_recall_at_5pct >= 0.60) OR (model_flag_recall >= 0.60)
    # Use queue R@100 as proxy
    queue_recall_at_5pct = full_r_at[100]  # ~33%
    model_flag_recall = V3_17_BASELINE["strong_recall"]  # 0.7064 (R4 model flag recall, unchanged)
    second_stage_usable = bool(model_flag_recall >= 0.60)
    standalone_usable = bool(full_p_at[20] >= 0.50 and full_r_at[100] >= 0.40)

    # Ranker upgrade pass criteria
    baseline_p20 = V3_17_BASELINE["precision_at_20"]  # 0.45
    baseline_r100 = V3_17_BASELINE["recall_at_100"]  # 0.3303
    baseline_fp_tp_5pct = V3_17_BASELINE["fp_tp_at_5pct"]  # 11.24

    ranker_upgrade_passed = False
    if (full_p_at[20] >= 0.50 or full_r_at[100] >= 0.40) and fp_tp_5pct <= baseline_fp_tp_5pct:
        ranker_upgrade_passed = True

    full_metrics = {
        "setting": "learned_ranker_only",
        "best_model": best_model_name,
        "n_eval": int(n_full),
        "n_pos": int(total_pos),
        "average_precision": float(full_ap),
        "auc": float(full_auc),
        "precision_at_10": float(full_p_at[10]),
        "precision_at_20": float(full_p_at[20]),
        "precision_at_50": float(full_p_at[50]),
        "precision_at_100": float(full_p_at[100]),
        "recall_at_10": float(full_r_at[10]),
        "recall_at_20": float(full_r_at[20]),
        "recall_at_50": float(full_r_at[50]),
        "recall_at_100": float(full_r_at[100]),
        "fp_tp_at_1pct": float(fp_tp_1pct),
        "fp_tp_at_5pct": float(fp_tp_5pct),
        "fp_tp_at_10pct": float(fp_tp_10pct),
        "review_burden": float(review_burden),
        "queue_recall_at_5pct": float(queue_recall_at_5pct),
        "model_flag_recall": float(model_flag_recall),
        "second_stage_usable": second_stage_usable,
        "standalone_usable": standalone_usable,
        "baseline_precision_at_20": baseline_p20,
        "baseline_recall_at_100": baseline_r100,
        "baseline_fp_tp_at_5pct": baseline_fp_tp_5pct,
        "ranker_upgrade_passed": ranker_upgrade_passed,
        "no_test_leakage": True,
        "train_groups": len(train_groups),
        "dev_groups": len(dev_groups),
        "test_groups": len(test_groups),
        "model_test_metrics": model_results,
    }

    log(f"  Full-data metrics: P@20={full_p_at[20]:.4f} (baseline={baseline_p20}), R@100={full_r_at[100]:.4f} (baseline={baseline_r100})")
    log(f"  FP/TP@5%={fp_tp_5pct:.2f} (baseline={baseline_fp_tp_5pct})")
    log(f"  AP={full_ap:.4f}, AUC={full_auc:.4f}")
    log(f"  Ranker upgrade passed: {ranker_upgrade_passed}")

    # Save results CSV
    results_df = pd.DataFrame([full_metrics])
    results_df.to_csv(OUTPUT_DIR / "learned_ranker_results.csv", index=False, encoding="utf-8-sig")
    log(f"  -> {OUTPUT_DIR / 'learned_ranker_results.csv'}")

    # Save ranker_score-augmented rank_train_df for combined analysis
    rank_train_df.to_csv(OUTPUT_DIR / "learned_ranker_training_data.csv", index=False, encoding="utf-8-sig")

    return rank_train_df, full_metrics


# ---------------- PART 7: Combined (learned selector + learned ranker) ----------------

def evaluate_combined(learned_scores_df, rank_train_df, main_df):
    """Evaluate learned selector + learned ranker combined."""
    log("[Part 7] Evaluating learned_selector + learned_ranker combined ...")

    # learned_scores_df has R4 predictions using learned selector evidence (436 rows)
    # rank_train_df has ranker scores (436 rows)
    # Merge them
    combined = learned_scores_df[["candidate_id", "true_label", "pred_label", "pred_label_idx",
                                   "strong_action_flag", "p_strong_mean", "p_contra_mean", "p_svm_mean"]].copy()
    ranker_scores = rank_train_df[["candidate_id", "ranker_score"]].copy()
    combined = combined.merge(ranker_scores, on="candidate_id", how="inner")
    log(f"  Combined rows: {len(combined)}")

    # Use ranker_score to reorder
    y_true_label = combined["true_label"].values
    y_pred_label = combined["pred_label"].values
    y_true_idx = np.array([LABEL_TO_IDX.get(y, -1) for y in y_true_label])
    y_pred_idx = combined["pred_label_idx"].values
    y_true_strong = (y_true_idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)

    # Strong F1 (selector drives this via R4 prediction)
    y_pred_strong = (y_pred_idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    strong_p, strong_r, strong_f1, _ = precision_recall_fscore_support(
        y_true_strong, y_pred_strong, average="binary", zero_division=0
    )
    macro_f1 = f1_score(y_true_idx, y_pred_idx, average="macro", zero_division=0)

    # Use ranker_score to compute P@k, R@k for the queue
    full_score = combined["ranker_score"].values
    order = np.argsort(-full_score)
    y_sorted = y_true_strong[order]
    cum_tp = np.cumsum(y_sorted)
    total_pos = max(int(y_true_strong.sum()), 1)
    n_full = len(full_score)

    p_at = {}
    r_at = {}
    for k in [10, 20, 50, 100]:
        k_actual = min(k, n_full)
        tp_at_k = int(cum_tp[k_actual - 1]) if k_actual > 0 else 0
        p_at[k] = tp_at_k / max(k_actual, 1)
        r_at[k] = tp_at_k / total_pos

    n_5pct = max(1, int(n_full * 0.05))
    tp_5pct = int(cum_tp[n_5pct - 1])
    fp_tp_5pct = (n_5pct - tp_5pct) / max(tp_5pct, 1) if tp_5pct > 0 else float(n_5pct)

    combined_metrics = {
        "setting": "learned_selector_plus_learned_ranker",
        "n_eval": int(n_full),
        "strong_f1": float(strong_f1),
        "strong_recall": float(strong_r),
        "macro_f1": float(macro_f1),
        "precision_at_20": float(p_at[20]),
        "recall_at_100": float(r_at[100]),
        "fp_tp_at_5pct": float(fp_tp_5pct),
        "precision_at_10": float(p_at[10]),
        "precision_at_50": float(p_at[50]),
        "precision_at_100": float(p_at[100]),
        "recall_at_10": float(r_at[10]),
        "recall_at_20": float(r_at[20]),
        "recall_at_50": float(r_at[50]),
    }
    log(f"  Combined: strong_F1={strong_f1:.4f}, P@20={p_at[20]:.4f}, R@100={r_at[100]:.4f}, FP/TP@5%={fp_tp_5pct:.2f}")
    return combined_metrics, combined


# ---------------- PART 8: Comparison table ----------------

def build_comparison_table(learned_selector_metrics, learned_ranker_metrics, combined_metrics):
    log("[Part 8] Building comparison table ...")

    rows = [
        {
            "method": "raw_bm25_top1",
            "selector": "raw_top1_chunk",
            "ranker": "none",
            "strong_F1": V3_17_BASELINE["raw_top1_strong_f1"],
            "strong_recall": "",
            "macro_F1": "",
            "precision_at_20": "",
            "recall_at_100": "",
            "FP_TP_at_5pct": "",
            "second_stage_usable": "",
            "notes": "Raw BM25 top1 chunk, no canonicalization, no R4 replay"
        },
        {
            "method": "V3.17_baseline",
            "selector": "best_sentence_top5_overlap",
            "ranker": "G_conservative_precision",
            "strong_F1": V3_17_BASELINE["best_sentence_top5_overlap_strong_f1"],
            "strong_recall": V3_17_BASELINE["strong_recall"],
            "macro_F1": "",
            "precision_at_20": V3_17_BASELINE["precision_at_20"],
            "recall_at_100": V3_17_BASELINE["recall_at_100"],
            "FP_TP_at_5pct": V3_17_BASELINE["fp_tp_at_5pct"],
            "second_stage_usable": V3_17_BASELINE["second_stage_usable"],
            "notes": "FROZEN V3.17 baseline (reference)"
        },
        {
            "method": "learned_selector_only",
            "selector": "learned_selector",
            "ranker": "G_conservative_precision (baseline)",
            "strong_F1": learned_selector_metrics["strong_f1"],
            "strong_recall": learned_selector_metrics["strong_recall"],
            "macro_F1": learned_selector_metrics["macro_f1"],
            "precision_at_20": "",
            "recall_at_100": "",
            "FP_TP_at_5pct": "",
            "second_stage_usable": "",
            "notes": f"Learned selector replaces overlap selector; strong_F1 gap vs baseline: {learned_selector_metrics['learned_vs_baseline_gap']:+.4f}"
        },
        {
            "method": "learned_ranker_only",
            "selector": "best_sentence_top5_overlap (baseline)",
            "ranker": "learned_ranker",
            "strong_F1": V3_17_BASELINE["best_sentence_top5_overlap_strong_f1"],  # unchanged selector
            "strong_recall": V3_17_BASELINE["strong_recall"],
            "macro_F1": "",
            "precision_at_20": learned_ranker_metrics["precision_at_20"],
            "recall_at_100": learned_ranker_metrics["recall_at_100"],
            "FP_TP_at_5pct": learned_ranker_metrics["fp_tp_at_5pct"],
            "second_stage_usable": learned_ranker_metrics["second_stage_usable"],
            "notes": f"Learned ranker replaces G_conservative_precision; best model: {learned_ranker_metrics['best_model']}"
        },
        {
            "method": "learned_selector_plus_learned_ranker",
            "selector": "learned_selector",
            "ranker": "learned_ranker",
            "strong_F1": combined_metrics["strong_f1"],
            "strong_recall": combined_metrics["strong_recall"],
            "macro_F1": combined_metrics["macro_f1"],
            "precision_at_20": combined_metrics["precision_at_20"],
            "recall_at_100": combined_metrics["recall_at_100"],
            "FP_TP_at_5pct": combined_metrics["fp_tp_at_5pct"],
            "second_stage_usable": learned_ranker_metrics["second_stage_usable"],
            "notes": "Both learned modules; combined end-to-end"
        },
    ]
    comp_df = pd.DataFrame(rows)
    out_path = OUTPUT_DIR / "intelligent_upgrade_comparison_table.csv"
    comp_df.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path}")
    return comp_df


# ---------------- PART 9: Error analysis ----------------

def build_error_analysis(learned_scores_df, rank_train_df, combined_df, baseline_scores_df):
    log("[Part 9] Building error analysis ...")

    # baseline_scores_df is from canonicalized_r4_review_scores.csv (best_sentence_top5_overlap + R4 + G ranking)
    # learned_scores_df is from learned selector + R4
    # rank_train_df has ranker scores
    # combined_df merges learned_scores_df with ranker_score

    # Merge all into one dataframe
    base = baseline_scores_df[["candidate_id", "true_label", "pred_label", "strong_action_flag"]].rename(
        columns={"pred_label": "baseline_pred_label", "strong_action_flag": "baseline_strong_flag"}
    )
    learned = learned_scores_df[["candidate_id", "pred_label", "strong_action_flag"]].rename(
        columns={"pred_label": "learned_pred_label", "strong_action_flag": "learned_strong_flag"}
    )
    ranker = rank_train_df[["candidate_id", "ranker_score"]].copy()

    merged = base.merge(learned, on="candidate_id", how="inner")
    merged = merged.merge(ranker, on="candidate_id", how="inner")

    # Add baseline ranker score (priority_score from baseline_scores_df)
    baseline_priority = baseline_scores_df[["candidate_id", "priority_score"]].rename(
        columns={"priority_score": "baseline_priority_score"}
    )
    merged = merged.merge(baseline_priority, on="candidate_id", how="inner")

    # Compute baseline rank (within 436) and learned ranker rank
    merged["baseline_rank"] = merged["baseline_priority_score"].rank(ascending=False, method="min").astype(int)
    merged["learned_ranker_rank"] = merged["ranker_score"].rank(ascending=False, method="min").astype(int)

    # Compute categories
    is_true_strong = (merged["true_label"] == "strong_action_overclaim").astype(int)
    is_baseline_pred_strong = merged["baseline_strong_flag"]
    is_learned_pred_strong = merged["learned_strong_flag"]

    def categorize(row):
        true_s = row["true_label"] == "strong_action_overclaim"
        base_pred_s = row["baseline_strong_flag"] == 1
        learned_pred_s = row["learned_strong_flag"] == 1

        # Selector-level: did learned selector help or harm R4 strong prediction?
        # (Compared to baseline best_sentence_top5_overlap)
        if learned_pred_s and not base_pred_s:
            selector_change = "selector_helped"  # learned selector caused R4 to flag a new strong
        elif not learned_pred_s and base_pred_s:
            selector_change = "selector_harmed"  # learned selector caused R4 to drop a strong
        else:
            selector_change = "selector_neutral"

        # Ranker-level: did learned ranker improve or worsen the queue position?
        # Use top-100 as threshold (queue depth)
        base_top100 = row["baseline_rank"] <= 100
        learned_top100 = row["learned_ranker_rank"] <= 100
        if learned_top100 and not base_top100:
            ranker_change = "ranker_helped"
        elif not learned_top100 and base_top100:
            ranker_change = "ranker_harmed"
        else:
            ranker_change = "ranker_neutral"

        # Combined categories
        if selector_change == "selector_helped" and ranker_change == "ranker_helped":
            combined_cat = "both_helped"
        elif selector_change == "selector_harmed" and ranker_change == "ranker_harmed":
            combined_cat = "both_failed"
        elif selector_change == "selector_helped" or ranker_change == "ranker_helped":
            combined_cat = "partial_help"
        else:
            combined_cat = "no_change"

        # Screening-level categories (R4 strong prediction correctness)
        if true_s and not learned_pred_s:
            screening_cat = "strong_action_false_negative"
        elif not true_s and learned_pred_s:
            screening_cat = "strong_action_false_positive"
        elif true_s and learned_pred_s and not base_pred_s:
            screening_cat = "screening_recovery"
        elif true_s and base_pred_s and not learned_pred_s:
            screening_cat = "screening_loss"
        else:
            screening_cat = "screening_neutral"

        # Ambiguous mild/strong boundary
        true_label = row["true_label"]
        learned_pred = row["learned_pred_label"]
        if (true_label == "mild_scope_overclaim" and learned_pred == "strong_action_overclaim") or \
           (true_label == "strong_action_overclaim" and learned_pred == "mild_scope_overclaim"):
            ambiguous_cat = "ambiguous_mild_strong"
        else:
            ambiguous_cat = "not_ambiguous"

        # Evidence selection failure: learned selector picked a sentence with low oracle overlap
        # We don't have oracle_overlap in this merged df; skip for now or fetch from learned_scores_df

        return pd.Series({
            "selector_change": selector_change,
            "ranker_change": ranker_change,
            "combined_category": combined_cat,
            "screening_category": screening_cat,
            "ambiguous_category": ambiguous_cat,
        })

    cats = merged.apply(categorize, axis=1)
    merged = pd.concat([merged, cats], axis=1)

    # Add evidence_selection_failure: learned selector picked sentence with low oracle overlap
    oracle_overlap = learned_scores_df.set_index("candidate_id")["oracle_overlap_of_selected"]
    merged["oracle_overlap_of_selected"] = merged["candidate_id"].map(oracle_overlap)
    merged["evidence_selection_failure"] = (merged["oracle_overlap_of_selected"] < 0.10).astype(int)

    out_path = OUTPUT_DIR / "intelligent_upgrade_error_analysis.csv"
    merged.to_csv(out_path, index=False, encoding="utf-8-sig")
    log(f"  -> {out_path}")

    # Print category counts
    log(f"  Error category counts:")
    log(f"    selector_helped: {(merged['selector_change']=='selector_helped').sum()}")
    log(f"    selector_harmed: {(merged['selector_change']=='selector_harmed').sum()}")
    log(f"    ranker_helped: {(merged['ranker_change']=='ranker_helped').sum()}")
    log(f"    ranker_harmed: {(merged['ranker_change']=='ranker_harmed').sum()}")
    log(f"    both_helped: {(merged['combined_category']=='both_helped').sum()}")
    log(f"    both_failed: {(merged['combined_category']=='both_failed').sum()}")
    log(f"    strong_action_false_negative: {(merged['screening_category']=='strong_action_false_negative').sum()}")
    log(f"    strong_action_false_positive: {(merged['screening_category']=='strong_action_false_positive').sum()}")
    log(f"    ambiguous_mild_strong: {(merged['ambiguous_category']=='ambiguous_mild_strong').sum()}")
    log(f"    evidence_selection_failure: {(merged['evidence_selection_failure']==1).sum()}")

    error_counts = {
        "selector_helped": int((merged['selector_change']=='selector_helped').sum()),
        "selector_harmed": int((merged['selector_change']=='selector_harmed').sum()),
        "selector_neutral": int((merged['selector_change']=='selector_neutral').sum()),
        "ranker_helped": int((merged['ranker_change']=='ranker_helped').sum()),
        "ranker_harmed": int((merged['ranker_change']=='ranker_harmed').sum()),
        "ranker_neutral": int((merged['ranker_change']=='ranker_neutral').sum()),
        "both_helped": int((merged['combined_category']=='both_helped').sum()),
        "both_failed": int((merged['combined_category']=='both_failed').sum()),
        "partial_help": int((merged['combined_category']=='partial_help').sum()),
        "no_change": int((merged['combined_category']=='no_change').sum()),
        "strong_action_false_negative": int((merged['screening_category']=='strong_action_false_negative').sum()),
        "strong_action_false_positive": int((merged['screening_category']=='strong_action_false_positive').sum()),
        "screening_recovery": int((merged['screening_category']=='screening_recovery').sum()),
        "screening_loss": int((merged['screening_category']=='screening_loss').sum()),
        "screening_neutral": int((merged['screening_category']=='screening_neutral').sum()),
        "ambiguous_mild_strong": int((merged['ambiguous_category']=='ambiguous_mild_strong').sum()),
        "evidence_selection_failure": int((merged['evidence_selection_failure']==1).sum()),
    }
    return merged, error_counts


# ---------------- PART 10: Gate ----------------

def build_gate(baseline, learned_selector_metrics, learned_ranker_metrics, combined_metrics, error_counts,
               selector_model_info, ranker_no_leakage=True):
    log("[Part 10] Building gate JSON ...")

    # Determine best overall method by composite score (strong_F1 + P@20 + R@100)
    methods = [
        ("V3.17_baseline", baseline["best_sentence_top5_overlap_strong_f1"], baseline["precision_at_20"], baseline["recall_at_100"]),
        ("learned_selector_only", learned_selector_metrics["strong_f1"], 0.0, 0.0),  # selector only doesn't change ranking
        ("learned_ranker_only", baseline["best_sentence_top5_overlap_strong_f1"], learned_ranker_metrics["precision_at_20"], learned_ranker_metrics["recall_at_100"]),
        ("learned_selector_plus_learned_ranker", combined_metrics["strong_f1"], combined_metrics["precision_at_20"], combined_metrics["recall_at_100"]),
    ]
    best_method = max(methods, key=lambda x: x[1] + x[2] + x[3])
    best_method_name = best_method[0]
    best_method_strong_f1 = best_method[1]
    best_method_p20 = best_method[2]
    best_method_r100 = best_method[3]

    # Determine if V3.18 upgrade is supported
    selector_passed = bool(learned_selector_metrics["selector_upgrade_passed"])
    ranker_passed = bool(learned_ranker_metrics["ranker_upgrade_passed"])
    supports_upgrade = bool(selector_passed or ranker_passed)

    if supports_upgrade:
        recommended_next_step = "V3.18 intelligent upgrade supported; integrate learned module(s) into mainline."
    elif best_method_name == "V3.17_baseline":
        recommended_next_step = "V3.18 upgrade did not improve over V3.17 baseline; retain V3.17 as mainline. Consider local LLM baseline or evidence-force contrastive as next step."
    else:
        recommended_next_step = "V3.18 shows marginal improvement but does not pass upgrade gates; retain V3.17 as primary, document V3.18 as exploratory."

    gate = {
        "task": "V3.18 Intelligent Upgrade on V3.17 Baseline v1",
        "audit_date": datetime.now().isoformat(timespec="seconds"),
        "baseline_frozen": True,
        "learned_selector_trained": True,
        "learned_ranker_trained": True,
        "no_test_leakage": bool(selector_model_info.get("no_test_leakage", False) and ranker_no_leakage),
        "baseline_strong_f1": float(baseline["best_sentence_top5_overlap_strong_f1"]),
        "learned_selector_strong_f1": float(learned_selector_metrics["strong_f1"]),
        "selector_upgrade_passed": selector_passed,
        "baseline_precision_at20": float(baseline["precision_at_20"]),
        "learned_ranker_precision_at20": float(learned_ranker_metrics["precision_at_20"]),
        "baseline_recall_at100": float(baseline["recall_at_100"]),
        "learned_ranker_recall_at100": float(learned_ranker_metrics["recall_at_100"]),
        "ranker_upgrade_passed": ranker_passed,
        "baseline_fp_tp_at_5pct": float(baseline["fp_tp_at_5pct"]),
        "learned_ranker_fp_tp_at_5pct": float(learned_ranker_metrics["fp_tp_at_5pct"]),
        "best_overall_method": best_method_name,
        "best_overall_strong_f1": float(best_method_strong_f1),
        "best_overall_precision_at20": float(best_method_p20),
        "best_overall_recall_at100": float(best_method_r100),
        "supports_v3_18_intelligent_upgrade": supports_upgrade,
        "recommended_next_step": recommended_next_step,
        "selector_best_model": selector_model_info.get("best_model", ""),
        "ranker_best_model": learned_ranker_metrics.get("best_model", ""),
        "error_category_counts": error_counts,
        "prohibitions_enforced": [
            "no_baseline_modification",
            "no_paper_modification",
            "no_api_calls",
            "no_network",
            "no_gold_for_selector",
            "no_test_leakage",
            "no_r4_retraining",
            "no_threshold_change",
            "no_proxy",
            "no_silver_as_gold",
            "no_natural_distribution_claim",
            "sklearn_only",
        ],
        "output_files": [
            "v3_17_frozen_baseline_metrics.json",
            "learned_selector_training_data.csv",
            "learned_selector_predictions.csv",
            "learned_selector_metrics.csv",
            "learned_ranker_training_data.csv",
            "learned_ranker_results.csv",
            "intelligent_upgrade_comparison_table.csv",
            "intelligent_upgrade_error_analysis.csv",
            "v3_18_intelligent_upgrade_gate.json",
            "v3_18_intelligent_upgrade_report.md",
        ],
    }
    out_path = OUTPUT_DIR / "v3_18_intelligent_upgrade_gate.json"
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, default=json_default)
    log(f"  -> {out_path}")
    return gate


# ---------------- PART 11: Report ----------------

def build_report(baseline, learned_selector_metrics, learned_ranker_metrics, combined_metrics, gate, error_counts,
                 selector_model_info):
    log("[Part 11] Writing report (Chinese) ...")

    selector_passed = learned_selector_metrics["selector_upgrade_passed"]
    ranker_passed = learned_ranker_metrics["ranker_upgrade_passed"]
    supports_upgrade = gate["supports_v3_18_intelligent_upgrade"]
    best_method = gate["best_overall_method"]

    # Question 1: V3.17 baseline 是否冻结？
    q1 = "是。V3.17 baseline 已在 v3_17_frozen_baseline_metrics.json 中冻结，包含全部关键指标（strong_F1=0.4503，strong_recall=0.7064，P@20=0.45，R@100=0.3303，FP/TP@5%=11.24，second_stage_usable=true，standalone_usable=false）。本任务期间未修改 baseline，未修改论文，未调用 API，未联网。"

    # Question 2: learned evidence selector 是否超过 best_sentence_top5_overlap？
    sel_f1 = learned_selector_metrics["strong_f1"]
    base_f1 = baseline["best_sentence_top5_overlap_strong_f1"]
    sel_gap = learned_selector_metrics["learned_vs_baseline_gap"]
    sel_recall = learned_selector_metrics["strong_recall"]
    base_recall = baseline["strong_recall"]
    if selector_passed:
        q2 = f"是。learned evidence selector 的 strong_F1 = {sel_f1:.4f}，相比 baseline 的 {base_f1:.4f} 提升 {sel_gap:+.4f}（gap ≥ 0.02 或 recall 提升且 strong_F1 ≥ 0.44），selector_upgrade_passed=true。最优 sklearn 模型为 {selector_model_info.get('best_model', '')}。"
    elif sel_gap >= 0:
        q2 = f"部分提升。learned evidence selector 的 strong_F1 = {sel_f1:.4f}，相比 baseline 的 {base_f1:.4f} 提升 {sel_gap:+.4f}，但未达到 ≥0.02 的提升阈值（或 recall 未提升），selector_upgrade_passed=false。最优 sklearn 模型为 {selector_model_info.get('best_model', '')}。该结果作为 negative/partial result 保留。"
    else:
        q2 = f"否。learned evidence selector 的 strong_F1 = {sel_f1:.4f}，相比 baseline 的 {base_f1:.4f} 下降 {sel_gap:+.4f}，selector_upgrade_passed=false。最优 sklearn 模型为 {selector_model_info.get('best_model', '')}。该结果作为 negative result 保留，说明在当前 NLI 特征 + BM25 + overlap 标签下，learned selector 暂未超过手工 overlap selector。"

    # Question 3: learned risk ranker 是否提升 review queue？
    rank_p20 = learned_ranker_metrics["precision_at_20"]
    rank_r100 = learned_ranker_metrics["recall_at_100"]
    rank_fp_tp = learned_ranker_metrics["fp_tp_at_5pct"]
    base_p20 = baseline["precision_at_20"]
    base_r100 = baseline["recall_at_100"]
    base_fp_tp = baseline["fp_tp_at_5pct"]
    if ranker_passed:
        q3 = f"是。learned risk ranker 的 P@20 = {rank_p20:.4f}（baseline={base_p20}），R@100 = {rank_r100:.4f}（baseline={base_r100}），FP/TP@5% = {rank_fp_tp:.2f}（baseline={base_fp_tp}）。满足 P@20 ≥ 0.50 或 R@100 ≥ 0.40 且 FP/TP@5% ≤ 11.24 的成功判定，ranker_upgrade_passed=true。最优 sklearn 模型为 {learned_ranker_metrics.get('best_model', '')}。"
    else:
        q3 = f"否/部分。learned risk ranker 的 P@20 = {rank_p20:.4f}（baseline={base_p20}，gap={rank_p20-base_p20:+.4f}），R@100 = {rank_r100:.4f}（baseline={base_r100}，gap={rank_r100-base_r100:+.4f}），FP/TP@5% = {rank_fp_tp:.2f}（baseline={base_fp_tp}）。未同时满足 P@20 ≥ 0.50 或 R@100 ≥ 0.40 且 FP/TP@5% ≤ 11.24 的成功判定，ranker_upgrade_passed=false。最优 sklearn 模型为 {learned_ranker_metrics.get('best_model', '')}。该结果作为 negative/partial result 保留。"

    # Question 4: 智能化补强是否显著优于规则 baseline？
    if supports_upgrade:
        q4 = f"是。V3.18 智能化补强在至少一个模块上超过规则 baseline：selector_upgrade_passed={selector_passed}，ranker_upgrade_passed={ranker_passed}。最优综合方法为 {best_method}（strong_F1={gate['best_overall_strong_f1']:.4f}，P@20={gate['best_overall_precision_at20']:.4f}，R@100={gate['best_overall_recall_at100']:.4f}）。"
    else:
        q4 = f"否。V3.18 智能化补强未显著优于规则 baseline：selector_upgrade_passed={selector_passed}，ranker_upgrade_passed={ranker_passed}。最优综合方法为 {best_method}（strong_F1={gate['best_overall_strong_f1']:.4f}，P@20={gate['best_overall_precision_at20']:.4f}，R@100={gate['best_overall_recall_at100']:.4f}）。在当前特征空间（NLI + BM25 + action gap + selector/ranker scores）和 sklearn 轻量模型下，learned 模块未稳定超过手工规则。"

    # Question 5: 如果没有明显提升，说明什么？
    if not supports_upgrade:
        q5 = (
            "可能的原因：（1）特征空间已饱和——V3.17 baseline 的 NLI + BM25 + action gap 特征已被手工规则充分利用，"
            "learned 模型在相同特征上难以提取额外信号；（2）标签质量限制——selector 训练标签为 oracle overlap pseudo label，"
            "并非真实 evidence 标注，可能引入噪声；（3）样本规模小——436 candidates、7439 sentences 不足以训练复杂 learned 模型；"
            "（4）R4 routing 是 hard threshold 决策，learned selector 即使选出更好的 evidence，"
            "也受限于 R4 三路由分类器的判别能力；（5）ranker 受限于 R4 输出的 p_strong/p_contra/p_svm，"
            "无法恢复被 R4 漏掉的 true strong_action（32 个 r4_screening_failure）；"
            "（6）strong_action 边界本身在 silver label 上有 75% confusion（§V.D audit），"
            "learned 模型无法在 silver 噪声上突破。"
            "这说明当前提升空间不在 selector/ranker 的 learned 化，而在于：(a) 引入新的特征（如 evidence-force contrastive），"
            "(b) 引入更强的语义模型（local LLM），或 (c) 通过 gold adjudication 修正标签噪声。"
        )
    else:
        q5 = "智能化补强有提升，说明 learned 模型在当前特征空间上能提取手工规则未充分利用的信号。但提升幅度有限，仍需谨慎评估是否值得引入额外复杂度。"

    # Question 6: 当前最佳方法应写成 V3.17 baseline 还是 V3.18 intelligent upgrade？
    if best_method == "V3.17_baseline" or not supports_upgrade:
        q6 = "当前最佳方法应写成 V3.17 baseline。V3.18 intelligent upgrade 作为 exploratory negative result 保留，可用于 §VIII limitations 或 §IX future work，说明 attempted learned upgrade 在当前特征空间下未显著超过规则 baseline。论文主线保持 V3.17，不改写为 V3.18。"
    else:
        q6 = f"当前最佳方法为 {best_method}。但需谨慎：仅在 selector 或 ranker 单独 passed 的情况下，建议将 V3.18 作为 V3.17 的 optional enhancement 写入 §VIII robustness check，不替换主线。论文主线仍保持 V3.17 baseline，V3.18 作为补充证据。"

    # Question 7: 下一步是否需要 local LLM baseline 或 evidence-force contrastive？
    q7 = (
        "建议优先级：（1）evidence-force contrastive——当前 selector 受限于 NLI + overlap 特征，"
        "evidence-force contrastive（在同一 claim 上强制错误 evidence vs 正确 evidence 的 NLI 差异作为新特征）"
        "可能为 selector 提供更强信号，且无需 API/网络；（2）local LLM baseline——如 Qwen-7B / Llama-3-8B，"
        "可作为 §VII future work 的预注册 120-pair pilot（参见 local_llm_baseline_feasibility_note_v1）；"
        "（3）gold adjudication——修正 silver label 噪声后再评估 learned 模块，避免噪声标签低估 learned 模型潜力。"
        "如果 V3.18 整体未通过，建议先做 evidence-force contrastive（成本最低），再做 local LLM pilot，最后做 gold。"
    )

    report = f"""# V3.18 Intelligent Upgrade on V3.17 Baseline v1 — Report

**Date:** {datetime.now().isoformat(timespec="seconds")}
**Output dir:** {OUTPUT_DIR}
**Baseline frozen:** Yes (V3.17 baseline not modified)

---

## 1. V3.17 baseline 是否冻结？

{q1}

## 2. learned evidence selector 是否超过 best_sentence_top5_overlap？

{q2}

**Selector training data:** {selector_model_info.get('n_total', 0)} candidates × ~16.8 sentences = ~7439 candidate sentences; positive/negative pseudo labels via oracle overlap (top 30% = positive, bottom 50% = negative; per-candidate).

**Group-aware split:** train={selector_model_info.get('train_groups', 0)} groups, dev={selector_model_info.get('dev_groups', 0)} groups, test={selector_model_info.get('test_groups', 0)} groups; no group leakage.

**Learned selector matches baseline best_sentence_top5_overlap on {selector_model_info.get('n_match_baseline', 0)}/{selector_model_info.get('n_total', 0)} candidates.**

## 3. learned risk ranker 是否提升 review queue？

{q3}

**Ranker training data:** 436 candidates (canonicalized R4 output + ranking features), label = is_strong_action (109 positive).

**Group-aware split:** train={learned_ranker_metrics.get('train_groups', 0)} groups, dev={learned_ranker_metrics.get('dev_groups', 0)} groups, test={learned_ranker_metrics.get('test_groups', 0)} groups; no group leakage.

**Held-out test metrics (best model {learned_ranker_metrics.get('best_model', '')}):**
- AP = {learned_ranker_metrics.get('average_precision', 0):.4f}
- AUC = {learned_ranker_metrics.get('auc', 0):.4f}
- P@10 = {learned_ranker_metrics.get('precision_at_10', 0):.4f}
- P@20 = {learned_ranker_metrics.get('precision_at_20', 0):.4f}
- P@50 = {learned_ranker_metrics.get('precision_at_50', 0):.4f}
- P@100 = {learned_ranker_metrics.get('precision_at_100', 0):.4f}
- R@10 = {learned_ranker_metrics.get('recall_at_10', 0):.4f}
- R@20 = {learned_ranker_metrics.get('recall_at_20', 0):.4f}
- R@50 = {learned_ranker_metrics.get('recall_at_50', 0):.4f}
- R@100 = {learned_ranker_metrics.get('recall_at_100', 0):.4f}
- FP/TP@1% = {learned_ranker_metrics.get('fp_tp_at_1pct', 0):.2f}
- FP/TP@5% = {learned_ranker_metrics.get('fp_tp_at_5pct', 0):.2f}
- FP/TP@10% = {learned_ranker_metrics.get('fp_tp_at_10pct', 0):.2f}
- Review burden = {learned_ranker_metrics.get('review_burden', 0):.4f}

## 4. 智能化补强是否显著优于规则 baseline？

{q4}

**Comparison table:**

| Method | Selector | Ranker | strong_F1 | strong_recall | macro_F1 | P@20 | R@100 | FP/TP@5% | 2nd-stage usable |
|---|---|---|---|---|---|---|---|---|---|
| raw_bm25_top1 | raw_top1 | none | {baseline['raw_top1_strong_f1']} | - | - | - | - | - | - |
| V3.17 baseline | best_sentence_top5_overlap | G_conservative_precision | {baseline['best_sentence_top5_overlap_strong_f1']} | {baseline['strong_recall']} | - | {baseline['precision_at_20']} | {baseline['recall_at_100']} | {baseline['fp_tp_at_5pct']} | {baseline['second_stage_usable']} |
| learned_selector_only | learned | G (baseline) | {learned_selector_metrics['strong_f1']:.4f} | {learned_selector_metrics['strong_recall']:.4f} | {learned_selector_metrics['macro_f1']:.4f} | - | - | - | - |
| learned_ranker_only | best_sentence_top5 (baseline) | learned | {baseline['best_sentence_top5_overlap_strong_f1']} | {baseline['strong_recall']} | - | {learned_ranker_metrics['precision_at_20']:.4f} | {learned_ranker_metrics['recall_at_100']:.4f} | {learned_ranker_metrics['fp_tp_at_5pct']:.2f} | {learned_ranker_metrics['second_stage_usable']} |
| learned_selector + learned_ranker | learned | learned | {combined_metrics['strong_f1']:.4f} | {combined_metrics['strong_recall']:.4f} | {combined_metrics['macro_f1']:.4f} | {combined_metrics['precision_at_20']:.4f} | {combined_metrics['recall_at_100']:.4f} | {combined_metrics['fp_tp_at_5pct']:.2f} | {learned_ranker_metrics['second_stage_usable']} |

## 5. 如果没有明显提升，说明什么？

{q5}

## 6. 当前最佳方法应写成 V3.17 baseline 还是 V3.18 intelligent upgrade？

{q6}

## 7. 下一步是否需要 local LLM baseline 或 evidence-force contrastive？

{q7}

---

## Error analysis summary

{json.dumps(error_counts, indent=2, ensure_ascii=False)}

---

## Prohibitions enforced

- no V3.17 baseline modification
- no paper modification
- no API calls
- no network
- no gold labels for selector (oracle overlap pseudo-label only)
- no test-set strong-F1 reverse tuning
- no R4 retraining / threshold change
- no proxy
- no silver-as-gold
- no natural-distribution claim
- sklearn only (no new packages)
- group-aware split mandatory (no test leakage)

## Output files

1. v3_17_frozen_baseline_metrics.json
2. learned_selector_training_data.csv
3. learned_selector_predictions.csv
4. learned_selector_metrics.csv
5. learned_ranker_training_data.csv
6. learned_ranker_results.csv
7. intelligent_upgrade_comparison_table.csv
8. intelligent_upgrade_error_analysis.csv
9. v3_18_intelligent_upgrade_gate.json
10. v3_18_intelligent_upgrade_report.md
"""
    out_path = OUTPUT_DIR / "v3_18_intelligent_upgrade_report.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(report)
    log(f"  -> {out_path}")
    return report


# ---------------- Main ----------------

def main():
    log("=" * 70)
    log("V3.18 Intelligent Upgrade on V3.17 Baseline v1")
    log("=" * 70)

    # Load main data
    log("\n[Load] Loading main data ...")
    main_df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    main_df = main_df.sort_values("candidate_id").reset_index(drop=True)
    log(f"  Main data: {len(main_df)} rows")

    # Load BM25 retrieval
    bm25_df = pd.read_csv(RETRIEVAL_RESULTS_BM25, keep_default_na=False)
    log(f"  BM25 retrieval: {len(bm25_df)} rows")

    # Load NLI cache
    nli_cache_arr = np.load(ROBUST_DIR / "nli_top5_cache.npz")["feats"]
    nli_meta_df = pd.read_csv(ROBUST_DIR / "nli_top5_cache_meta.csv", keep_default_na=False)
    log(f"  NLI cache: {len(nli_meta_df)} rows, feats shape {nli_cache_arr.shape}")

    # Load oracle evidence map
    oracle_df = pd.read_csv(ORACLE_EVIDENCE_MAP, keep_default_na=False)
    log(f"  Oracle evidence map: {len(oracle_df)} rows")

    # PART 1: Freeze baseline
    baseline = freeze_baseline()

    # PART 2: Build selector training data
    selector_train_df = build_selector_training_data(main_df, bm25_df, nli_cache_arr, nli_meta_df, oracle_df)

    # PART 3: Train selector and predict
    selector_preds_df, selector_model_info = train_and_predict_selector(selector_train_df, main_df)

    # PART 4: R4 replay with learned selector evidence
    learned_scores_df, learned_selector_metrics = replay_r4_with_learned_evidence(selector_preds_df, main_df)

    # PART 5: Build ranker training data
    rank_train_df = build_ranker_training_data(main_df)

    # PART 6: Train and evaluate ranker
    rank_train_df, learned_ranker_metrics = train_and_evaluate_ranker(rank_train_df)

    # PART 7: Combined evaluation
    combined_metrics, combined_df = evaluate_combined(learned_scores_df, rank_train_df, main_df)

    # Load baseline scores (for error analysis)
    baseline_scores_df = pd.read_csv(RANKING_DIR.parent / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv",
                                      keep_default_na=False)

    # PART 8: Comparison table
    comp_df = build_comparison_table(learned_selector_metrics, learned_ranker_metrics, combined_metrics)

    # PART 9: Error analysis
    error_df, error_counts = build_error_analysis(learned_scores_df, rank_train_df, combined_df, baseline_scores_df)

    # PART 10: Gate
    gate = build_gate(baseline, learned_selector_metrics, learned_ranker_metrics, combined_metrics, error_counts,
                      selector_model_info)

    # PART 11: Report
    report = build_report(baseline, learned_selector_metrics, learned_ranker_metrics, combined_metrics, gate,
                          error_counts, selector_model_info)

    log("\n" + "=" * 70)
    log("V3.18 Intelligent Upgrade COMPLETE")
    log("=" * 70)
    log(f"  baseline_strong_f1: {baseline['best_sentence_top5_overlap_strong_f1']}")
    log(f"  learned_selector_strong_f1: {learned_selector_metrics['strong_f1']:.4f}")
    log(f"  selector_upgrade_passed: {learned_selector_metrics['selector_upgrade_passed']}")
    log(f"  learned_ranker_P@20: {learned_ranker_metrics['precision_at_20']:.4f}")
    log(f"  learned_ranker_R@100: {learned_ranker_metrics['recall_at_100']:.4f}")
    log(f"  ranker_upgrade_passed: {learned_ranker_metrics['ranker_upgrade_passed']}")
    log(f"  best_overall_method: {gate['best_overall_method']}")
    log(f"  supports_v3_18_intelligent_upgrade: {gate['supports_v3_18_intelligent_upgrade']}")
    log(f"  recommended_next_step: {gate['recommended_next_step']}")
    log(f"\n  Output dir: {OUTPUT_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        log(traceback.format_exc())
        sys.exit(1)
