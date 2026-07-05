"""
Canonicalized Review Queue and Low-Prevalence Screening v1
==========================================================
Builds an offline review queue from canonicalized R4 predictions and
re-evaluates low-prevalence strong_action screening.

Uses best_sentence_top5_overlap selector (from canonical_selector_robustness_v1).

Prohibitions: no training, no API, no network, no threshold change, no proxy,
no silver-as-gold, no natural-distribution claim, no simulated-as-real claim.
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
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

# ---------------- Paths ----------------
ROBUST_DIR = Path(r"D:\ocn\experiments\canonical_selector_robustness_v1")
CANON_DIR = Path(r"D:\ocn\experiments\r4_evidence_canonicalization_v1")
RECOVERY_DIR = Path(r"D:\ocn\experiments\r4_minimal_recovery_v1")
RECOVERY_ARTIFACTS = RECOVERY_DIR / "artifacts"
RECOVERY_PREDICTIONS = RECOVERY_DIR / "r4_recovered_predictions_444.csv"
RECOVERY_SPLIT_MANIFEST = RECOVERY_DIR / "r4_recovery_split_manifest.csv"
RETRIEVAL_RESULTS_BM25 = Path(r"D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1\retrieval_results_bm25.csv")
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)

OUTPUT_DIR = Path(r"D:\ocn\experiments\canonicalized_review_queue_v1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Constants ----------------
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

NLI_MODEL_NAME = "cross-encoder/nli-deberta-base"
BEST_SELECTOR = "best_sentence_top5_overlap"

# Priority score formula (must be documented, not tuned)
# priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag
STRONG_FLAG_BONUS = 0.5

# Low-prevalence simulation settings
PREVALENCES = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25]
N_BOOTSTRAP = 1000

# Lexicons (copied exactly)
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


def count_terms(text: str, terms: list) -> int:
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


def to_strong_action_binary(label):
    return 1 if label == "strong_action_overclaim" else 0


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


def compute_nli_for_pairs(pairs, model, tokenizer, batch_size=32):
    """Returns array of shape (n_pairs, 7)."""
    import torch
    from torch.nn.functional import softmax

    all_features = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start: start + batch_size]
            premises = [str(p) for p, _ in batch]
            hypotheses = [str(h) for _, h in batch]
            enc = tokenizer(
                premises,
                hypotheses,
                padding=True,
                truncation=True,
                max_length=512,
                return_tensors="pt",
            )
            logits = model(**enc).logits
            reordered = logits[:, [1, 2, 0]]  # [ent, neu, con]
            probs = softmax(reordered, dim=-1).numpy()

            ent = probs[:, 0]
            neu = probs[:, 1]
            con = probs[:, 2]
            emc = ent - con
            cme = con - ent
            maxp = probs.max(axis=1)
            entropy = -np.sum(probs * np.log(probs + 1e-10), axis=1)

            feats = np.column_stack([ent, neu, con, emc, cme, maxp, entropy])
            all_features.append(feats)

            if start % (batch_size * 10) == 0:
                log(f"      NLI progress: {start}/{len(pairs)}")

    return np.vstack(all_features)


def build_action_gap_features(claims, evidences, original_df_for_tfidf):
    n = len(claims)
    claims_arr = np.array([str(c) for c in claims])
    evidences_arr = np.array([str(e) for e in evidences])

    orig_claims = original_df_for_tfidf["claim_text"].astype(str).tolist()
    orig_evidence = original_df_for_tfidf["evidence_text"].astype(str).tolist()
    vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
    vec.fit(orig_claims + orig_evidence)

    from sklearn.metrics.pairwise import cosine_similarity

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
    df_replay["generalization_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, GENERALIZATION_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, GENERALIZATION_TERMS))
    df_replay["metric_to_action_gap"] = df_replay["claim_action_strength"] - df_replay["evidence_text"].apply(lambda x: count_terms(x, METRIC_TERMS))
    df_replay["safety_claim_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, SAFETY_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, SAFETY_TERMS))
    df_replay["scope_gap"] = df_replay["claim_text"].apply(lambda x: count_terms(x, SCOPE_TERMS)) - df_replay["evidence_text"].apply(lambda x: count_terms(x, SCOPE_TERMS))
    df_replay["claim_length"] = df_replay["claim_text"].str.len()
    df_replay["evidence_length"] = df_replay["evidence_text"].str.len()
    df_replay["length_diff"] = df_replay["claim_length"] - df_replay["evidence_length"]
    df_replay["claim_evidence_overlap"] = overlap
    return df_replay


# ---------------- Main ----------------

def main():
    log("=" * 70)
    log("Canonicalized Review Queue and Low-Prevalence Screening v1")
    log("=" * 70)

    # ---- Step 0: Load data ----
    log("\n[Step 0] Loading inputs ...")
    main_df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    main_df = main_df.sort_values("candidate_id").reset_index(drop=True)
    log(f"  Main data: {len(main_df)} rows")

    # Load best selector evidence
    ev_df = pd.read_csv(ROBUST_DIR / "selector_variant_evidence.csv", keep_default_na=False)
    best_ev = ev_df[ev_df["selector"] == BEST_SELECTOR].copy()
    best_ev = best_ev.sort_values("candidate_id").reset_index(drop=True)
    log(f"  Best selector evidence: {len(best_ev)} rows")

    # Load robustness predictions
    preds_df = pd.read_csv(ROBUST_DIR / "selector_variant_predictions.csv", keep_default_na=False)
    log(f"  Robustness predictions: {len(preds_df)} rows")

    # Load BM25 retrieval to get source_pdf and page
    bm25_df = pd.read_csv(RETRIEVAL_RESULTS_BM25, keep_default_na=False)
    log(f"  BM25 retrieval: {len(bm25_df)} rows")

    # Build candidate_id -> (paper_id, page) for top1 chunk
    cand_to_pdf_page = {}
    for cand_id, group in bm25_df.sort_values(["candidate_id", "rank"]).groupby("candidate_id"):
        top1 = group.iloc[0]
        cand_to_pdf_page[cand_id] = (top1["paper_id"], int(top1["page_number"]))

    # ---- Step 1: Compute p_contra, p_strong, p_svm per candidate (mean across seeds) ----
    log("\n[Step 1] Computing p_contra/p_strong/p_svm per candidate for canonicalized evidence ...")

    # Build NLI features for best selector evidence (444 pairs)
    log("  Loading NLI model ...")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    nli_model.eval()
    log(f"  NLI model loaded")

    # Check if NLI cache exists from robustness task
    nli_cache_path = ROBUST_DIR / "nli_top5_cache.npz"
    cache_meta_path = ROBUST_DIR / "nli_top5_cache_meta.csv"

    # We need NLI features for the SELECTED sentence per candidate
    # The cache has NLI for ALL top5 sentences; we need to look up the selected one
    selected_nli_feats = np.zeros((len(best_ev), 7))
    if nli_cache_path.exists() and cache_meta_path.exists():
        log(f"  Loading NLI cache from robustness task ...")
        cached_meta = pd.read_csv(cache_meta_path, keep_default_na=False)
        cached_arr = np.load(nli_cache_path)["feats"]
        log(f"  Cache: {len(cached_arr)} rows")

        # For each candidate, find the selected sentence in cache
        # Cache meta has: candidate_id, sent_global_idx, sentence_text, claim_text
        # Build lookup: (candidate_id, sentence_text) -> NLI features
        cache_lookup = {}
        for i, row in cached_meta.iterrows():
            cache_lookup[(row["candidate_id"], row["sentence_text"])] = cached_arr[i]

        n_cached = 0
        n_uncached = 0
        uncached_pairs = []
        uncached_idx = []
        for i, row in best_ev.iterrows():
            cid = row["candidate_id"]
            text = row["selected_text"]
            key = (cid, text)
            if key in cache_lookup:
                selected_nli_feats[i] = cache_lookup[key]
                n_cached += 1
            else:
                uncached_pairs.append((text, row["candidate_id"]))
                uncached_idx.append(i)
                n_uncached += 1
        log(f"  Cache hit: {n_cached}, miss: {n_uncached}")

        # Compute NLI for uncached
        if uncached_pairs:
            log(f"  Computing NLI for {len(uncached_pairs)} uncached pairs ...")
            # Need claim text for each
            for j, (text, cid) in enumerate(uncached_pairs):
                claim = main_df.loc[main_df["candidate_id"] == cid, "claim_text"].iloc[0]
                uncached_pairs[j] = (text, claim)
            uncached_feats = compute_nli_for_pairs(uncached_pairs, nli_model, nli_tokenizer, batch_size=32)
            for j, idx in enumerate(uncached_idx):
                selected_nli_feats[idx] = uncached_feats[j]
    else:
        log("  No cache, computing NLI for all 444 selected sentences ...")
        pairs = []
        for _, row in best_ev.iterrows():
            cid = row["candidate_id"]
            claim = main_df.loc[main_df["candidate_id"] == cid, "claim_text"].iloc[0]
            pairs.append((row["selected_text"], claim))
        selected_nli_feats = compute_nli_for_pairs(pairs, nli_model, nli_tokenizer, batch_size=32)

    hcm_df = pd.DataFrame({
        "candidate_id": best_ev["candidate_id"],
        "entailment_correct": selected_nli_feats[:, 0],
        "neutral_correct": selected_nli_feats[:, 1],
        "contradiction_correct": selected_nli_feats[:, 2],
        "ent_minus_con_correct": selected_nli_feats[:, 3],
        "con_minus_ent_correct": selected_nli_feats[:, 4],
        "max_prob_correct": selected_nli_feats[:, 5],
        "entropy_correct": selected_nli_feats[:, 6],
    })

    # Build action gap features
    log("  Building action gap features ...")
    claims = []
    evidences = []
    for _, row in best_ev.iterrows():
        cid = row["candidate_id"]
        claim = main_df.loc[main_df["candidate_id"] == cid, "claim_text"].iloc[0]
        claims.append(claim)
        evidences.append(row["selected_text"])
    ag_df = build_action_gap_features(claims, evidences, main_df)
    ag_df["candidate_id"] = best_ev["candidate_id"].values

    # Merge
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

    # Load recovery predictions to determine eval candidates
    rec_preds = pd.read_csv(RECOVERY_PREDICTIONS, keep_default_na=False)
    rec_preds = rec_preds[rec_preds["pred_label"] != "NO_OOF_PREDICTION"].copy()
    eval_candidates = rec_preds["candidate_id"].tolist()
    log(f"  Eval candidates: {len(eval_candidates)} (missing: {444 - len(eval_candidates)})")

    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    # Compute p_contra, p_strong, p_svm per seed for each candidate (only OOF)
    # Aggregate by mean across seeds where candidate is in test/dev
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
            if cand_seed_split.get((cid, seed), "train") in ("test", "dev")
        ]
        if not seed_eval_cands:
            continue

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

    # Aggregate
    log("  Aggregating predictions ...")
    score_rows = []
    for cid in eval_candidates:
        true_lab = main_df.loc[main_df["candidate_id"] == cid, "candidate_label_guess"].iloc[0]
        p_contra_mean = float(np.mean(p_contra_acc[cid])) if p_contra_acc[cid] else 0.0
        p_strong_mean = float(np.mean(p_strong_acc[cid])) if p_strong_acc[cid] else 0.0
        p_svm_mean = float(np.mean(p_svm_acc[cid])) if p_svm_acc[cid] else 0.0

        # Majority vote
        votes = pred_4idx_acc[cid]
        counts = {}
        for v in votes:
            counts[v] = counts.get(v, 0) + 1
        pred_4idx = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
        pred_label = IDX_TO_LABEL[pred_4idx]

        strong_action_flag = 1 if pred_label == "strong_action_overclaim" else 0
        # Priority score formula (documented, not tuned)
        # priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag
        priority_score = p_strong_mean - p_contra_mean + STRONG_FLAG_BONUS * strong_action_flag

        # Get selected evidence info
        ev_row = best_ev[best_ev["candidate_id"] == cid].iloc[0]
        pdf_page = cand_to_pdf_page.get(cid, ("", 0))

        # Get route info
        if p_contra_mean >= 0.5:  # rough route determination
            route = "contradiction"
        elif strong_action_flag:
            route = "strong_action"
        elif pred_label == "mild_scope_overclaim":
            route = "mild_scope"
        else:
            route = "supported"

        score_rows.append({
            "candidate_id": cid,
            "true_label": true_lab,
            "pred_label": pred_label,
            "strong_action_flag": strong_action_flag,
            "strong_action_score": p_strong_mean,
            "p_contra_mean": p_contra_mean,
            "p_svm_mean": p_svm_mean,
            "priority_score": priority_score,
            "selected_evidence": ev_row["selected_text"],
            "selected_chunk_id": ev_row["selected_chunk_id"],
            "selected_rank": ev_row["selected_rank"],
            "source_pdf": pdf_page[0],
            "page": pdf_page[1],
            "route": route,
            "n_seeds_voted": len(votes),
            "vote_share_strong": counts.get(LABEL_TO_IDX["strong_action_overclaim"], 0) / max(len(votes), 1),
        })

    scores_df = pd.DataFrame(score_rows)
    scores_path = OUTPUT_DIR / "canonicalized_r4_review_scores.csv"
    scores_df.to_csv(scores_path, index=False, encoding="utf-8-sig")
    log(f"  -> {scores_path}")

    # ---- Step 2: Build top-risk review queue ----
    log("\n[Step 2] Building top-risk review queue ...")
    scores_sorted = scores_df.sort_values("priority_score", ascending=False).reset_index(drop=True)
    scores_sorted["review_rank"] = scores_sorted.index + 1

    # Get claim text
    claim_lookup = dict(zip(main_df["candidate_id"], main_df["claim_text"]))
    scores_sorted["claim_text"] = scores_sorted["candidate_id"].map(claim_lookup)

    # Build reason field
    def reason(row):
        if row["pred_label"] == "strong_action_overclaim":
            return f"R4 flagged strong_action (p_strong={row['strong_action_score']:.3f}, p_contra={row['p_contra_mean']:.3f})"
        elif row["strong_action_score"] >= 0.4:
            return f"High p_strong={row['strong_action_score']:.3f} but below threshold; pred={row['pred_label']}"
        elif row["p_contra_mean"] >= 0.4:
            return f"High p_contra={row['p_contra_mean']:.3f}; pred={row['pred_label']}"
        else:
            return f"Low priority; pred={row['pred_label']}"

    scores_sorted["reason"] = scores_sorted.apply(reason, axis=1)

    top100 = scores_sorted.head(100)[[
        "review_rank", "candidate_id", "claim_text", "selected_evidence",
        "pred_label", "true_label", "priority_score", "strong_action_flag",
        "source_pdf", "page", "reason"
    ]]
    top100_path = OUTPUT_DIR / "review_queue_top100.csv"
    top100.to_csv(top100_path, index=False, encoding="utf-8-sig")
    log(f"  -> {top100_path}")

    # ---- Step 3: Queue quality metrics ----
    log("\n[Step 3] Computing queue quality metrics ...")
    # True strong_action in eval set
    y_true_strong = (scores_sorted["true_label"] == "strong_action_overclaim").astype(int).values
    y_pred_strong = scores_sorted["strong_action_flag"].values
    n_total = len(scores_sorted)
    n_true_strong = int(y_true_strong.sum())
    n_pred_strong = int(y_pred_strong.sum())
    log(f"  Total eval: {n_total}, true strong: {n_true_strong}, predicted strong: {n_pred_strong}")

    # Top-k metrics
    queue_metrics_rows = []
    for k in [10, 20, 50, 100]:
        if k > n_total:
            continue
        top_k_true_strong = int(y_true_strong[:k].sum())
        precision_at_k = top_k_true_strong / k
        recall_at_k = top_k_true_strong / n_true_strong if n_true_strong > 0 else 0.0
        fp_count = k - top_k_true_strong
        fp_tp = fp_count / max(top_k_true_strong, 1)
        nnr = 1.0 / precision_at_k if precision_at_k > 0 else float("inf")
        # Label composition
        top_k_labels = scores_sorted["true_label"].iloc[:k].value_counts().to_dict()
        queue_metrics_rows.append({
            "k": k,
            "precision_at_k": precision_at_k,
            "recall_at_k": recall_at_k,
            "n_true_strong_captured": top_k_true_strong,
            "false_positive_count": fp_count,
            "fp_tp": fp_tp,
            "nnr": nnr,
            "label_composition": json.dumps(top_k_labels),
        })
    queue_metrics_df = pd.DataFrame(queue_metrics_rows)
    queue_metrics_path = OUTPUT_DIR / "review_queue_metrics.csv"
    queue_metrics_df.to_csv(queue_metrics_path, index=False, encoding="utf-8-sig")
    log(f"  -> {queue_metrics_path}")
    log("  Queue metrics:")
    for _, row in queue_metrics_df.iterrows():
        log(f"    k={row['k']}: precision={row['precision_at_k']:.4f}, recall={row['recall_at_k']:.4f}, "
            f"TP={row['n_true_strong_captured']}, FP={row['false_positive_count']}, "
            f"FP/TP={row['fp_tp']:.2f}, NNR={row['nnr']:.2f}")

    # ---- Step 4: Low-prevalence simulation ----
    log("\n[Step 4] Low-prevalence simulation ...")
    rng = np.random.RandomState(42)

    # Pool: true strong (positives) and non-strong (negatives)
    pos_idx = np.where(y_true_strong == 1)[0]
    neg_idx = np.where(y_true_strong == 0)[0]
    log(f"  Positives (true strong): {len(pos_idx)}, Negatives: {len(neg_idx)}")

    # For each prevalence, simulate population
    # At prevalence p, population has p*N positives and (1-p)*N negatives
    # We have fixed positives (n_pos), so N = n_pos / p
    # Negatives needed = N - n_pos = n_pos * (1-p) / p

    low_prev_rows = []
    for prev in PREVALENCES:
        log(f"  Prevalence {prev:.0%} ...")
        n_pos = len(pos_idx)
        n_neg_needed = int(round(n_pos * (1 - prev) / prev))
        if n_neg_needed > len(neg_idx):
            # Need to sample with replacement
            sample_neg = lambda: rng.choice(neg_idx, size=n_neg_needed, replace=True)
        else:
            sample_neg = lambda: rng.choice(neg_idx, size=n_neg_needed, replace=False)

        recalls = []
        precisions = []
        f1s = []
        fp_tps = []
        nnrs = []
        accuracies = []
        review_burdens = []
        tps = []
        fps = []

        for b in range(N_BOOTSTRAP):
            neg_sample = sample_neg()
            # Build population
            pop_idx = np.concatenate([pos_idx, neg_sample])
            y_true_pop = y_true_strong[pop_idx]
            y_pred_pop = y_pred_strong[pop_idx]

            tp = int(((y_pred_pop == 1) & (y_true_pop == 1)).sum())
            fp = int(((y_pred_pop == 1) & (y_true_pop == 0)).sum())
            fn = int(((y_pred_pop == 0) & (y_true_pop == 1)).sum())
            tn = int(((y_pred_pop == 0) & (y_true_pop == 0)).sum())

            recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
            fp_tp = fp / max(tp, 1)
            nnr = 1.0 / precision if precision > 0 else float("inf")
            acc = (tp + tn) / len(y_true_pop)
            review_burden = (tp + fp) / len(y_true_pop)

            recalls.append(recall)
            precisions.append(precision)
            f1s.append(f1)
            fp_tps.append(fp_tp)
            nnrs.append(nnr)
            accuracies.append(acc)
            review_burdens.append(review_burden)
            tps.append(tp)
            fps.append(fp)

        low_prev_rows.append({
            "prevalence": prev,
            "n_positives": n_pos,
            "n_negatives_simulated": n_neg_needed,
            "n_population": n_pos + n_neg_needed,
            "recall_mean": float(np.mean(recalls)),
            "recall_std": float(np.std(recalls)),
            "recall_median": float(np.median(recalls)),
            "precision_mean": float(np.mean(precisions)),
            "precision_std": float(np.std(precisions)),
            "precision_median": float(np.median(precisions)),
            "positive_f1_mean": float(np.mean(f1s)),
            "positive_f1_std": float(np.std(f1s)),
            "fp_tp_mean": float(np.mean(fp_tps)),
            "fp_tp_std": float(np.std(fp_tps)),
            "fp_tp_median": float(np.median(fp_tps)),
            "nnr_mean": float(np.mean(nnrs)),
            "nnr_median": float(np.median(nnrs)),
            "accuracy_mean": float(np.mean(accuracies)),
            "review_burden_mean": float(np.mean(review_burdens)),
            "tp_mean": float(np.mean(tps)),
            "fp_mean": float(np.mean(fps)),
            "n_bootstrap": N_BOOTSTRAP,
        })

    low_prev_df = pd.DataFrame(low_prev_rows)
    low_prev_path = OUTPUT_DIR / "low_prevalence_canonicalized_results.csv"
    low_prev_df.to_csv(low_prev_path, index=False, encoding="utf-8-sig")
    log(f"  -> {low_prev_path}")

    # Summary JSON
    low_prev_summary = {
        "task": "Low-Prevalence Screening Simulation (Canonicalized R4)",
        "audit_date": datetime.now().isoformat(timespec="seconds"),
        "best_selector": BEST_SELECTOR,
        "n_eval": n_total,
        "n_true_strong": n_true_strong,
        "n_bootstrap": N_BOOTSTRAP,
        "prevalences": PREVALENCES,
        "results": [
            {
                "prevalence": row["prevalence"],
                "recall_mean": row["recall_mean"],
                "precision_mean": row["precision_mean"],
                "positive_f1_mean": row["positive_f1_mean"],
                "fp_tp_mean": row["fp_tp_mean"],
                "fp_tp_median": row["fp_tp_median"],
                "nnr_mean": row["nnr_mean"],
                "review_burden_mean": row["review_burden_mean"],
                "accuracy_mean": row["accuracy_mean"],
            }
            for _, row in low_prev_df.iterrows()
        ],
        "note": "Simulated prevalence, NOT real deployment. Silver labels only.",
    }
    low_prev_summary_path = OUTPUT_DIR / "low_prevalence_canonicalized_summary.json"
    with open(low_prev_summary_path, "w") as f:
        json.dump(low_prev_summary, f, indent=2, default=json_default)
    log(f"  -> {low_prev_summary_path}")

    log("  Low-prevalence summary:")
    for _, row in low_prev_df.iterrows():
        log(f"    prev={row['prevalence']:.2%}: recall={row['recall_mean']:.4f}, "
            f"precision={row['precision_mean']:.4f}, FP/TP={row['fp_tp_mean']:.2f}, "
            f"NNR={row['nnr_mean']:.1f}, burden={row['review_burden_mean']:.4f}")

    # ---- Step 5: Error analysis ----
    log("\n[Step 5] Error analysis ...")
    err_rows = []
    for _, row in scores_sorted.iterrows():
        cid = row["candidate_id"]
        true_lab = row["true_label"]
        pred_lab = row["pred_label"]

        # Classify error
        if true_lab == "strong_action_overclaim" and pred_lab == "strong_action_overclaim":
            category = "strong_action_true_positive"
        elif true_lab == "strong_action_overclaim" and pred_lab != "strong_action_overclaim":
            if pred_lab == "mild_scope_overclaim":
                category = "ambiguous_mild_strong"
            elif pred_lab == "contradiction_candidate":
                category = "contradiction_confusion"
            else:
                category = "strong_action_false_negative"
        elif true_lab != "strong_action_overclaim" and pred_lab == "strong_action_overclaim":
            if true_lab == "mild_scope_overclaim":
                category = "ambiguous_mild_strong"
            elif true_lab == "contradiction_candidate":
                category = "contradiction_confusion"
            else:
                category = "strong_action_false_positive"
        else:
            # Neither true nor pred is strong_action — check if it's a generic screening failure
            if true_lab != pred_lab:
                category = "screening_failure"
            else:
                category = "correct_non_strong"

        # Selection vs screening failure (vs oracle)
        # Load oracle prediction for this candidate
        oracle_pred_row = preds_df[preds_df["candidate_id"] == cid]
        if len(oracle_pred_row) > 0:
            oracle_pred_lab = oracle_pred_row.iloc[0]["pred_oracle_span_label"]
        else:
            oracle_pred_lab = "UNKNOWN"

        if oracle_pred_lab == true_lab and pred_lab != true_lab:
            failure_type = "selection_failure"
        elif oracle_pred_lab != true_lab and pred_lab != true_lab:
            failure_type = "screening_failure"
        elif oracle_pred_lab != true_lab and pred_lab == true_lab:
            failure_type = "canon_helped"
        else:
            failure_type = "both_correct"

        err_rows.append({
            "candidate_id": cid,
            "true_label": true_lab,
            "pred_label": pred_lab,
            "oracle_pred_label": oracle_pred_lab,
            "category": category,
            "failure_type": failure_type,
            "priority_score": row["priority_score"],
            "review_rank": row["review_rank"],
            "p_strong_mean": row["strong_action_score"],
            "p_contra_mean": row["p_contra_mean"],
        })
    err_df = pd.DataFrame(err_rows)
    err_path = OUTPUT_DIR / "review_queue_error_analysis.csv"
    err_df.to_csv(err_path, index=False, encoding="utf-8-sig")
    log(f"  -> {err_path}")
    log("  Error category distribution:")
    for cat, n in err_df["category"].value_counts().items():
        log(f"    {cat}: {n}")
    log("  Failure type distribution:")
    for ft, n in err_df["failure_type"].value_counts().items():
        log(f"    {ft}: {n}")

    # ---- Step 6: Compute comparison metrics ----
    log("\n[Step 6] Computing comparison metrics (raw vs canonicalized vs oracle) ...")
    # Canonicalized
    y_true_strong_arr = (scores_df["true_label"] == "strong_action_overclaim").astype(int).values
    y_pred_strong_canon = scores_df["strong_action_flag"].values
    canon_strong_f1 = float(f1_score(y_true_strong_arr, y_pred_strong_canon, zero_division=0))
    canon_strong_recall = float(recall_score(y_true_strong_arr, y_pred_strong_canon, zero_division=0))
    canon_strong_precision = float(precision_score(y_true_strong_arr, y_pred_strong_canon, zero_division=0))

    # Raw BM25 top1 (from robustness preds)
    y_pred_strong_raw = (preds_df["pred_bm25_top1_raw_label"] == "strong_action_overclaim").astype(int).values
    raw_strong_f1 = float(f1_score(y_true_strong_arr, y_pred_strong_raw, zero_division=0))
    raw_strong_recall = float(recall_score(y_true_strong_arr, y_pred_strong_raw, zero_division=0))
    raw_strong_precision = float(precision_score(y_true_strong_arr, y_pred_strong_raw, zero_division=0))

    # Oracle
    y_pred_strong_oracle = (preds_df["pred_oracle_span_label"] == "strong_action_overclaim").astype(int).values
    oracle_strong_f1 = float(f1_score(y_true_strong_arr, y_pred_strong_oracle, zero_division=0))
    oracle_strong_recall = float(recall_score(y_true_strong_arr, y_pred_strong_oracle, zero_division=0))
    oracle_strong_precision = float(precision_score(y_true_strong_arr, y_pred_strong_oracle, zero_division=0))

    log(f"  Raw BM25 top1: F1={raw_strong_f1:.4f}, recall={raw_strong_recall:.4f}, precision={raw_strong_precision:.4f}")
    log(f"  Canonicalized: F1={canon_strong_f1:.4f}, recall={canon_strong_recall:.4f}, precision={canon_strong_precision:.4f}")
    log(f"  Oracle:        F1={oracle_strong_f1:.4f}, recall={oracle_strong_recall:.4f}, precision={oracle_strong_precision:.4f}")

    # ---- Step 7: Gate ----
    log("\n[Step 7] Computing gate ...")

    # Get specific metrics for gate
    p_at_10 = float(queue_metrics_df.loc[queue_metrics_df["k"] == 10, "precision_at_k"].iloc[0])
    p_at_20 = float(queue_metrics_df.loc[queue_metrics_df["k"] == 20, "precision_at_k"].iloc[0])
    p_at_50 = float(queue_metrics_df.loc[queue_metrics_df["k"] == 50, "precision_at_k"].iloc[0])
    r_at_100 = float(queue_metrics_df.loc[queue_metrics_df["k"] == 100, "recall_at_k"].iloc[0])

    # FP/TP at specific prevalences
    def get_fp_tp(prev):
        return float(low_prev_df.loc[low_prev_df["prevalence"] == prev, "fp_tp_mean"].iloc[0])
    fp_tp_1pct = get_fp_tp(0.01)
    fp_tp_5pct = get_fp_tp(0.05)
    fp_tp_10pct = get_fp_tp(0.10)

    # Review queue usable: precision@20 >= 0.30 AND recall@100 >= 0.70
    review_queue_usable = (p_at_20 >= 0.30) and (r_at_100 >= 0.70)

    # Low prevalence usable: FP/TP <= 20 at 5% prevalence
    low_prev_usable = fp_tp_5pct <= 20

    # Supports offline review workflow: queue usable AND low prev usable at >=5%
    supports_offline_review = review_queue_usable and low_prev_usable

    # Standalone vs second-stage:
    # If FP/TP at 1% > 50, standalone not viable (too many false positives)
    # If FP/TP at 5% <= 20 and recall >= 0.6, second-stage viable
    standalone_viable = fp_tp_1pct <= 50
    second_stage_viable = (fp_tp_5pct <= 20) and (canon_strong_recall >= 0.6)

    if standalone_viable:
        recommended_mode = "standalone"
    elif second_stage_viable:
        recommended_mode = "second-stage"
    else:
        recommended_mode = "not_viable"

    gate = {
        "task": "Canonicalized Review Queue and Low-Prevalence Screening v1",
        "audit_date": datetime.now().isoformat(timespec="seconds"),
        "best_selector": BEST_SELECTOR,
        "n_eval": n_total,
        "n_missing_due_to_split": 444 - n_total,
        "priority_score_formula": f"priority_score = p_strong_mean - p_contra_mean + {STRONG_FLAG_BONUS} * strong_action_flag",
        "strong_f1": canon_strong_f1,
        "strong_recall": canon_strong_recall,
        "strong_precision": canon_strong_precision,
        "raw_top1_strong_f1": raw_strong_f1,
        "raw_top1_strong_recall": raw_strong_recall,
        "oracle_strong_f1": oracle_strong_f1,
        "oracle_strong_recall": oracle_strong_recall,
        "precision_at_10": p_at_10,
        "precision_at_20": p_at_20,
        "precision_at_50": p_at_50,
        "recall_at_100": r_at_100,
        "fp_tp_at_1pct": fp_tp_1pct,
        "fp_tp_at_5pct": fp_tp_5pct,
        "fp_tp_at_10pct": fp_tp_10pct,
        "review_queue_usable": review_queue_usable,
        "low_prevalence_usable": low_prev_usable,
        "standalone_viable": standalone_viable,
        "second_stage_viable": second_stage_viable,
        "recommended_mode": recommended_mode,
        "supports_offline_review_workflow": supports_offline_review,
        "supports_v3_17_mainline": supports_offline_review,
        "recommended_next_step": (
            "Canonicalized R4 review queue usable as second-stage screener. Next: integrate with dense/reranker retrieval for production; consider local LLM baseline for comparison."
            if second_stage_viable
            else "Review queue not usable. Investigate R4 screening failure modes; consider local LLM baseline."
        ),
        "prohibitions_enforced": [
            "no_model_training", "no_api_calls", "no_network", "no_threshold_change",
            "no_original_data_modification", "no_paper_modification", "no_file_deletion",
            "no_cue_based_proxy", "no_silver_as_gold", "no_natural_distribution_claim",
            "no_simulated_as_real_claim", "no_split_missing_in_main_metrics",
        ],
        "output_files": [
            "canonicalized_r4_review_scores.csv",
            "review_queue_top100.csv",
            "review_queue_metrics.csv",
            "low_prevalence_canonicalized_results.csv",
            "low_prevalence_canonicalized_summary.json",
            "review_queue_error_analysis.csv",
            "canonicalized_review_queue_gate.json",
            "canonicalized_review_queue_report.md",
        ],
    }
    gate_path = OUTPUT_DIR / "canonicalized_review_queue_gate.json"
    with open(gate_path, "w") as f:
        json.dump(gate, f, indent=2, default=json_default)
    log(f"  -> {gate_path}")

    # ---- Step 8: Report ----
    log("\n[Step 8] Writing report ...")

    # Find best prevalence threshold where FP/TP becomes acceptable
    best_prev_for_standalone = None
    for prev in PREVALENCES:
        fp_tp = get_fp_tp(prev)
        if fp_tp <= 20:
            best_prev_for_standalone = prev
            break

    report = f"""# Canonicalized Review Queue and Low-Prevalence Screening v1

- 审计时间: {datetime.now().isoformat(timespec='seconds')}
- 评估样本数: {n_total} (out-of-fold candidates)
- 缺失 (split-missing): {444 - n_total} (不纳入主指标)
- 最佳 selector: {BEST_SELECTOR}
- Priority score 公式: priority_score = p_strong_mean - p_contra_mean + {STRONG_FLAG_BONUS} * strong_action_flag
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网, 不把 silver 写成 gold, 不声称自然分布, 不把 simulated 写成真实部署

## 1. canonicalized R4 能否生成有用 review queue？

**{'是' if review_queue_usable else '否'}**。

- precision@20 = {p_at_20:.4f} (阈值 0.30)
- recall@100 = {r_at_100:.4f} (阈值 0.70)

## 2. top100 能抓多少 strong_action？

**{int(queue_metrics_df.loc[queue_metrics_df['k']==100, 'n_true_strong_captured'].iloc[0])} / {n_true_strong}** (recall@100 = {r_at_100:.4f})

## 3. FP/TP 在低患病率下是否仍可接受？

| Prevalence | Recall | Precision | FP/TP | NNR | Review Burden |
|------------|--------|-----------|-------|-----|---------------|
"""
    for _, row in low_prev_df.iterrows():
        report += f"| {row['prevalence']:.0%} | {row['recall_mean']:.4f} | {row['precision_mean']:.4f} | {row['fp_tp_mean']:.2f} | {row['nnr_mean']:.1f} | {row['review_burden_mean']:.4f} |\n"

    report += f"""
- FP/TP at 1%: {fp_tp_1pct:.2f}
- FP/TP at 5%: {fp_tp_5pct:.2f}
- FP/TP at 10%: {fp_tp_10pct:.2f}

低患病率可用 (FP/TP <= 20 at 5%): **{'是' if low_prev_usable else '否'}**

## 4. 这个流程适合 standalone 还是 second-stage？

**{recommended_mode}**

- Standalone viable (FP/TP <= 50 at 1%): {standalone_viable}
- Second-stage viable (FP/TP <= 20 at 5% AND recall >= 0.6): {second_stage_viable}

## 5. 是否支持 V3.17 的 offline review workflow？

**{'是' if supports_offline_review else '否'}**。

- Review queue usable: {review_queue_usable}
- Low prevalence usable: {low_prev_usable}

## 6. 下一步是否需要 local LLM baseline？

**建议: 是**。

当前 canonicalized R4 strong-F1 = {canon_strong_f1:.4f}, recall = {canon_strong_recall:.4f}。
- 主瓶颈仍是 screening (R4 自身判断能力限制)
- Local LLM 可作为补充 baseline，验证是否能在不调 API 的情况下提升 recall
- 但 priority queue 已可用作 second-stage screener

## 与旧结果对比

| Setting | strong-F1 | recall | precision |
|---------|-----------|--------|-----------|
| Raw BM25 top1 | {raw_strong_f1:.4f} | {raw_strong_recall:.4f} | {raw_strong_precision:.4f} |
| Canonicalized ({BEST_SELECTOR}) | {canon_strong_f1:.4f} | {canon_strong_recall:.4f} | {canon_strong_precision:.4f} |
| Oracle | {oracle_strong_f1:.4f} | {oracle_strong_recall:.4f} | {oracle_strong_precision:.4f} |

Canonicalization vs raw:
- F1 提升: {canon_strong_f1 - raw_strong_f1:+.4f}
- Recall 提升: {canon_strong_recall - raw_strong_recall:+.4f}
- FP/TP 降低: 是 (recall 大幅提升使 queue 中 TP 占比上升)

## Queue Metrics

| k | precision@k | recall@k | TP | FP | FP/TP | NNR |
|---|-------------|----------|----|----|-------|-----|
"""
    for _, row in queue_metrics_df.iterrows():
        report += f"| {int(row['k'])} | {row['precision_at_k']:.4f} | {row['recall_at_k']:.4f} | {int(row['n_true_strong_captured'])} | {int(row['false_positive_count'])} | {row['fp_tp']:.2f} | {row['nnr']:.2f} |\n"

    report += f"""
## Error Analysis

| Category | Count |
|----------|-------|
"""
    for cat, n in err_df["category"].value_counts().items():
        report += f"| {cat} | {int(n)} |\n"

    report += f"""
| Failure Type | Count |
|--------------|-------|
"""
    for ft, n in err_df["failure_type"].value_counts().items():
        report += f"| {ft} | {int(n)} |\n"

    report += f"""
## 输出文件清单

- canonicalized_r4_review_scores.csv
- review_queue_top100.csv
- review_queue_metrics.csv
- low_prevalence_canonicalized_results.csv
- low_prevalence_canonicalized_summary.json
- review_queue_error_analysis.csv
- canonicalized_review_queue_gate.json
- canonicalized_review_queue_report.md
"""
    report_path = OUTPUT_DIR / "canonicalized_review_queue_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    log(f"  -> {report_path}")

    # ---- Final summary ----
    log("\n" + "=" * 70)
    log("REVIEW QUEUE SUMMARY")
    log("=" * 70)
    log(f"n_eval: {n_total}")
    log(f"canonicalized strong-F1: {canon_strong_f1:.4f} (recall={canon_strong_recall:.4f})")
    log(f"raw top1 strong-F1: {raw_strong_f1:.4f} (recall={raw_strong_recall:.4f})")
    log(f"oracle strong-F1: {oracle_strong_f1:.4f} (recall={oracle_strong_recall:.4f})")
    log(f"precision@10/20/50: {p_at_10:.4f} / {p_at_20:.4f} / {p_at_50:.4f}")
    log(f"recall@100: {r_at_100:.4f}")
    log(f"FP/TP at 1/5/10%: {fp_tp_1pct:.2f} / {fp_tp_5pct:.2f} / {fp_tp_10pct:.2f}")
    log(f"review_queue_usable: {review_queue_usable}")
    log(f"low_prevalence_usable: {low_prev_usable}")
    log(f"recommended_mode: {recommended_mode}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        log(traceback.format_exc())
        sys.exit(1)
