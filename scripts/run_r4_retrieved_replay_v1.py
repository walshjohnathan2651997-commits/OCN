"""
Formal R4 Replay on PDF-Retrieved Evidence v1
==============================================
Uses recovered R4 artifacts (r4_minimal_recovery_v1) to formally replay R4
on PDF BM25 retrieved evidence. No proxy, no retraining, no threshold tuning.

Steps:
  1. Load recovered R4 artifacts (classifiers, scalers, thresholds)
  2. Compute HCM/NLI features for 4 evidence settings (oracle, top1, top3, top5)
     - Oracle: reuse recovered_hcm_features.csv (no NLI recomputation)
     - top1/top3/top5: compute new NLI features using cross-encoder/nli-deberta-base
  3. Replay R4 per seed using saved classifiers + thresholds
  4. Compute metrics for each setting
  5. Error analysis
  6. Gate and report

Prohibitions: no training, no API, no network, no threshold change, no proxy,
no silver-as-gold, no natural-distribution claim.
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
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

# ---------------- Paths ----------------
RECOVERY_DIR = Path(r"D:\ocn\experiments\r4_minimal_recovery_v1")
RECOVERY_ARTIFACTS = RECOVERY_DIR / "artifacts"
RECOVERED_HCM = RECOVERY_DIR / "recovered_hcm_features.csv"
RECOVERY_PREDICTIONS = RECOVERY_DIR / "r4_recovered_predictions_444.csv"
RECOVERY_SPLIT_MANIFEST = RECOVERY_DIR / "r4_recovery_split_manifest.csv"

RETRIEVAL_INPUT_DIR = Path(r"D:\ocn\experiments\r4_on_retrieved_evidence_v1")
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)

OUTPUT_DIR = Path(r"D:\ocn\experiments\r4_retrieved_replay_v1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Constants ----------------
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
SETTINGS = ["oracle", "bm25_top1", "bm25_top3", "bm25_top5"]

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

NLI_MODEL_NAME = "cross-encoder/nli-deberta-base"

# Lexicons (copied exactly from original script)
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


def strip_retrieval_markers(text: str) -> str:
    """Strip [RANK=*][PDF=*][PAGE=*] markers from retrieved evidence text."""
    text = str(text)
    # Remove all [RANK=...], [PDF=...], [PAGE=...] markers
    text = re.sub(r"\[RANK=\d+\]", "", text)
    text = re.sub(r"\[PDF=[^\]]+\]", "", text)
    text = re.sub(r"\[PAGE=\d+\]", "", text)
    # Clean up extra whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def route_conservative_strong(p_contra, p_strong, p_svm, t_contra, t_contra_low, t_strong, t_svm, n):
    pred = np.empty(n, dtype=int)
    for i in range(n):
        if p_contra[i] >= t_contra:
            pred[i] = LABEL_TO_IDX["contradiction_candidate"]
        elif p_strong[i] >= t_strong and p_contra[i] < t_contra_low:
            pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
        else:
            pred[i] = LABEL_TO_IDX["supported"] if p_svm[i] < t_svm else LABEL_TO_IDX["mild_scope_overclaim"]
    return pred


def binary_metrics_full(y_true, y_pred):
    y_true = np.asarray(y_true).astype(int)
    y_pred = np.asarray(y_pred).astype(int)
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "positive_f1": float(f1_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "precision": float(precision_score(y_true, y_pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, y_pred, pos_label=1, zero_division=0)),
    }


def compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx):
    pred_strong = (pred_4idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    m_strong = binary_metrics_full(y_strong, pred_strong)
    pred_esc = (pred_4idx != LABEL_TO_IDX["supported"]).astype(int)
    m_esc = binary_metrics_full(y_esc, pred_esc)
    pred_contra = (pred_4idx == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    m_contra = binary_metrics_full(y_contra, pred_contra)
    # Per-label F1
    per_label_f1 = {}
    for lab_idx, lab_name in IDX_TO_LABEL.items():
        per_label_f1[lab_name] = float(f1_score(y_4idx, pred_4idx, labels=[lab_idx], average="macro", zero_division=0))
    return {
        "accuracy": float(accuracy_score(y_4idx, pred_4idx)),
        "macro_f1": float(f1_score(y_4idx, pred_4idx, average="macro", zero_division=0)),
        "weighted_f1": float(f1_score(y_4idx, pred_4idx, average="weighted", zero_division=0)),
        "supported_f1": per_label_f1.get("supported", 0),
        "mild_scope_f1": per_label_f1.get("mild_scope_overclaim", 0),
        "strong_action_f1": per_label_f1.get("strong_action_overclaim", 0),
        "contradiction_f1": per_label_f1.get("contradiction_candidate", 0),
        "strong_precision": m_strong["precision"],
        "strong_recall": m_strong["recall"],
        "strong_positive_f1": m_strong["positive_f1"],
        "escalation_macro_f1": m_esc["macro_f1"],
        "contradiction_positive_f1": m_contra["positive_f1"],
    }


# ---------------- NLI feature computation ----------------

def compute_nli_for_pairs(pairs, model, tokenizer, batch_size=8):
    """Compute NLI features for (evidence=premise, claim=hypothesis) pairs.
    Returns array of shape (n_pairs, 7).
    """
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
            # id2label = {0: 'contradiction', 1: 'entailment', 2: 'neutral'}
            # Reorder to [entailment, neutral, contradiction]
            reordered = logits[:, [1, 2, 0]]
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
                log(f"    NLI progress: {start}/{len(pairs)}")

    return np.vstack(all_features)


# ---------------- Action gap features ----------------

def build_action_gap_features_for_replay(df, evidence_col="evidence_text", tfidf_vec=None):
    """Build action gap features. If tfidf_vec is None, fit it; else use provided.
    Returns (df_with_features, tfidf_vec).
    """
    claim_text = df["claim_text"].astype(str)
    evidence_text = df[evidence_col].astype(str)

    df["claim_action_strength"] = claim_text.apply(lambda x: count_terms(x, CLAIM_ACTION_TERMS))
    df["evidence_action_support"] = evidence_text.apply(lambda x: count_terms(x, EVIDENCE_ACTION_SUPPORT_TERMS))
    df["action_escalation_gap"] = df["claim_action_strength"] - df["evidence_action_support"]
    df["certainty_gap"] = claim_text.apply(lambda x: count_terms(x, CERTAINTY_TERMS)) - evidence_text.apply(lambda x: count_terms(x, CERTAINTY_TERMS))
    df["deployment_gap"] = claim_text.apply(lambda x: count_terms(x, DEPLOYMENT_TERMS)) - evidence_text.apply(lambda x: count_terms(x, DEPLOYMENT_TERMS))
    df["generalization_gap"] = claim_text.apply(lambda x: count_terms(x, GENERALIZATION_TERMS)) - evidence_text.apply(lambda x: count_terms(x, GENERALIZATION_TERMS))
    df["metric_to_action_gap"] = df["claim_action_strength"] - evidence_text.apply(lambda x: count_terms(x, METRIC_TERMS))
    df["safety_claim_gap"] = claim_text.apply(lambda x: count_terms(x, SAFETY_TERMS)) - evidence_text.apply(lambda x: count_terms(x, SAFETY_TERMS))
    df["scope_gap"] = claim_text.apply(lambda x: count_terms(x, SCOPE_TERMS)) - evidence_text.apply(lambda x: count_terms(x, SCOPE_TERMS))
    df["claim_length"] = claim_text.str.len()
    df["evidence_length"] = evidence_text.str.len()
    df["length_diff"] = df["claim_length"] - df["evidence_length"]

    if tfidf_vec is None:
        tfidf_vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
        all_text = list(claim_text) + list(evidence_text)
        tfidf_vec.fit(all_text)

    claim_tfidf = tfidf_vec.transform(claim_text)
    evidence_tfidf = tfidf_vec.transform(evidence_text)
    from sklearn.metrics.pairwise import cosine_similarity
    overlap = np.array([cosine_similarity(claim_tfidf[i], evidence_tfidf[i])[0, 0] for i in range(len(claim_text))])
    df["claim_evidence_overlap"] = overlap

    return df, tfidf_vec


# ---------------- Main ----------------

def main():
    log("=" * 70)
    log("Formal R4 Replay on PDF-Retrieved Evidence v1")
    log("=" * 70)

    # ---- Step 1: Load recovered R4 artifacts ----
    log("\n[Step 1] Loading recovered R4 artifacts ...")
    artifacts = {}
    for seed in SEEDS:
        seed_dir = RECOVERY_ARTIFACTS / f"seed_{seed}"
        assert seed_dir.exists(), f"Missing seed dir: {seed_dir}"
        art = {}
        for name in ["clf_contra", "clf_strong", "clf_svm", "clf_flat4",
                      "scaler_contra", "scaler_strong", "scaler_svm"]:
            with open(seed_dir / f"{name}.pkl", "rb") as f:
                art[name] = pickle.load(f)
        with open(seed_dir / "thresholds.json", "r", encoding="utf-8") as f:
            art["thresholds"] = json.load(f)
        with open(seed_dir / "feature_columns.json", "r", encoding="utf-8") as f:
            art["feature_columns"] = json.load(f)
        with open(seed_dir / "label_mapping.json", "r", encoding="utf-8") as f:
            art["label_mapping"] = json.load(f)
        artifacts[seed] = art
        t = art["thresholds"]
        log(f"  Seed {seed}: t_contra={t['t_contra']}, t_contra_low={t['t_contra_low']}, t_strong={t['t_strong']}, t_svm={t['t_svm']}")
    log(f"  All 10 seed artifacts loaded successfully")

    # ---- Load original data + recovered HCM features ----
    log("\n  Loading original data ...")
    df_orig = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    hcm = pd.read_csv(RECOVERED_HCM, keep_default_na=False)
    df_orig = df_orig.merge(
        hcm[["candidate_id"] + NLI_FEATURES + ["s_correct", "s_wrong", "margin"]],
        on="candidate_id", how="left"
    )
    df_orig["label_4"] = df_orig["candidate_label_guess"].astype(str)
    df_orig["label_4_idx"] = df_orig["label_4"].map(LABEL_TO_IDX)
    log(f"  Original data: {len(df_orig)} rows")

    # Build action gap features on ORIGINAL data (fit TF-IDF, save vectorizer)
    log("  Building action gap features on original data (fitting TF-IDF) ...")
    df_orig, tfidf_vec = build_action_gap_features_for_replay(df_orig, "evidence_text", tfidf_vec=None)

    # ---- Load recovery predictions (for candidate set) ----
    log("  Loading recovery predictions ...")
    rec_pred = pd.read_csv(RECOVERY_PREDICTIONS, keep_default_na=False)
    # Main eval set: candidates with OOF predictions (not "NO_OOF_PREDICTION")
    eval_cids = set(rec_pred[rec_pred["pred_label"] != "NO_OOF_PREDICTION"]["candidate_id"].tolist())
    missing_cids = set(rec_pred[rec_pred["pred_label"] == "NO_OOF_PREDICTION"]["candidate_id"].tolist())
    log(f"  Eval candidates: {len(eval_cids)} (missing: {len(missing_cids)})")

    # ---- Load split manifest ----
    log("  Loading split manifest ...")
    split_manifest = pd.read_csv(RECOVERY_SPLIT_MANIFEST, keep_default_na=False)
    # For each seed, get test + dev candidate_ids (from recovery)
    seed_eval_cids = {}
    for seed in SEEDS:
        sm = split_manifest[split_manifest["seed"] == seed]
        test_cids = set(sm[sm["split"] == "test"]["candidate_id"].tolist())
        dev_cids = set(sm[sm["split"] == "dev"]["candidate_id"].tolist())
        seed_eval_cids[seed] = {"test": test_cids, "dev": dev_cids, "test_or_dev": test_cids | dev_cids}

    # ---- Step 2: Compute HCM features for 4 settings ----
    log("\n[Step 2] Computing HCM features for 4 evidence settings ...")

    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    feature_sets = {}

    # --- Oracle: reuse original HCM features ---
    log("  [oracle] Reusing recovered_hcm_features (no NLI recomputation) ...")
    df_oracle = df_orig.copy()
    # Save HCM features for oracle
    oracle_hcm = df_oracle[["candidate_id"] + NLI_FEATURES].copy()
    oracle_hcm_path = OUTPUT_DIR / "hcm_features_replay_oracle.csv"
    oracle_hcm.to_csv(oracle_hcm_path, index=False, encoding="utf-8-sig")
    log(f"    -> {oracle_hcm_path}")
    feature_sets["oracle"] = df_oracle

    # --- bm25_top1/top3/top5: compute new NLI features ---
    log("  Loading NLI model ...")
    import torch
    from transformers import AutoTokenizer, AutoModelForSequenceClassification
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    nli_model.eval()
    log(f"  NLI model loaded: {NLI_MODEL_NAME}")

    for setting in ["bm25_top1", "bm25_top3", "bm25_top5"]:
        log(f"\n  [{setting}] Computing NLI features ...")
        input_csv = RETRIEVAL_INPUT_DIR / f"r4_input_{setting}.csv"
        df_retrieved = pd.read_csv(input_csv, keep_default_na=False)
        log(f"    Loaded {len(df_retrieved)} rows from {input_csv}")

        # Strip retrieval markers from evidence_text
        df_retrieved["evidence_text_clean"] = df_retrieved["evidence_text"].apply(strip_retrieval_markers)
        log(f"    Stripped retrieval markers. Sample evidence (first 100): {str(df_retrieved.iloc[0]['evidence_text_clean'])[:100]}")

        # Compute NLI features: (evidence=premise, claim=hypothesis)
        pairs = list(zip(df_retrieved["evidence_text_clean"].tolist(), df_retrieved["claim_text"].tolist()))
        log(f"    Computing NLI for {len(pairs)} pairs ...")
        nli_features = compute_nli_for_pairs(pairs, nli_model, tokenizer, batch_size=8)
        log(f"    NLI features shape: {nli_features.shape}")

        # Build HCM features CSV
        hcm_df = pd.DataFrame({
            "candidate_id": df_retrieved["candidate_id"],
        })
        for i, col in enumerate(NLI_FEATURES):
            hcm_df[col] = nli_features[:, i]
        hcm_path = OUTPUT_DIR / f"hcm_features_replay_{setting}.csv"
        hcm_df.to_csv(hcm_path, index=False, encoding="utf-8-sig")
        log(f"    -> {hcm_path}")

        # Merge with original data and build action gap features with retrieved evidence
        df_setting = df_orig.drop(columns=NLI_FEATURES).merge(
            hcm_df, on="candidate_id", how="left"
        )
        # Replace evidence_text with retrieved evidence (clean version)
        ev_map = df_retrieved.set_index("candidate_id")["evidence_text_clean"].to_dict()
        df_setting["evidence_text"] = df_setting["candidate_id"].map(ev_map)
        # Build action gap features using the ORIGINAL TF-IDF vectorizer
        df_setting, _ = build_action_gap_features_for_replay(df_setting, "evidence_text", tfidf_vec=tfidf_vec)
        feature_sets[setting] = df_setting

    # ---- Step 3: Replay R4 ----
    log("\n[Step 3] Replaying R4 for each seed and setting ...")

    all_predictions = {setting: [] for setting in SETTINGS}

    for seed in SEEDS:
        log(f"\n  --- Seed {seed} ---")
        art = artifacts[seed]
        t = art["thresholds"]
        t_contra = t["t_contra"]
        t_contra_low = t["t_contra_low"]
        t_strong = t["t_strong"]
        t_svm = t["t_svm"]

        # Get candidates for this seed (test + dev from recovery)
        seed_cids = seed_eval_cids[seed]["test_or_dev"]

        for setting in SETTINGS:
            df_setting = feature_sets[setting]
            # Filter to candidates in this seed's test or dev split
            df_seed = df_setting[df_setting["candidate_id"].isin(seed_cids)].copy()
            if len(df_seed) == 0:
                continue

            # Determine split for each candidate
            test_cids = seed_eval_cids[seed]["test"]
            df_seed["split"] = df_seed["candidate_id"].apply(lambda x: "test" if x in test_cids else "dev")

            # Prepare features
            X_nli = art["scaler_contra"].transform(df_seed[NLI_FEATURES].values)
            X_exp = art["scaler_strong"].transform(df_seed[expert_features].values)
            X_svm = art["scaler_svm"].transform(df_seed[svm_features].values)

            # Compute probabilities
            p_contra = art["clf_contra"].predict_proba(X_nli)[:, 1]
            p_strong = art["clf_strong"].predict_proba(X_exp)[:, 1]
            p_svm = art["clf_svm"].predict_proba(X_svm)[:, 1]

            # Route
            n = len(df_seed)
            pred = route_conservative_strong(p_contra, p_strong, p_svm, t_contra, t_contra_low, t_strong, t_svm, n)

            # Record predictions
            for i, (_, row) in enumerate(df_seed.iterrows()):
                all_predictions[setting].append({
                    "candidate_id": row["candidate_id"],
                    "true_label": row["label_4"],
                    "pred_label": IDX_TO_LABEL[int(pred[i])],
                    "pred_label_idx": int(pred[i]),
                    "seed": seed,
                    "split": row["split"],
                    "p_contra": float(p_contra[i]),
                    "p_strong": float(p_strong[i]),
                    "p_svm": float(p_svm[i]),
                    "route": "R4_conservative_strong_replay",
                    "t_contra": t_contra,
                    "t_contra_low": t_contra_low,
                    "t_strong": t_strong,
                    "t_svm": t_svm,
                    "setting": setting,
                })

    # ---- Aggregate predictions (majority vote, same as recovery) ----
    log("\n  Aggregating predictions (majority vote) ...")
    aggregated = {}
    for setting in SETTINGS:
        pred_df = pd.DataFrame(all_predictions[setting])
        if len(pred_df) == 0:
            log(f"  WARNING: No predictions for {setting}")
            aggregated[setting] = pd.DataFrame()
            continue
        # Aggregate: prefer test, fall back to dev
        test_only = pred_df[pred_df["split"] == "test"]
        dev_only = pred_df[pred_df["split"] == "dev"]
        test_cids = set(test_only["candidate_id"].unique())

        agg_rows = []
        for cid in sorted(eval_cids):
            sub_test = test_only[test_only["candidate_id"] == cid]
            if len(sub_test) > 0:
                sub = sub_test
                split_used = "test"
            else:
                sub_dev = dev_only[dev_only["candidate_id"] == cid]
                if len(sub_dev) > 0:
                    sub = sub_dev
                    split_used = "dev"
                else:
                    continue
            votes = sub["pred_label_idx"].value_counts()
            pred_idx = int(votes.idxmax())
            true_label = sub["true_label"].iloc[0]
            seeds_str = ",".join(str(s) for s in sorted(sub["seed"].unique()))
            agg_rows.append({
                "candidate_id": cid,
                "true_label": true_label,
                "pred_label": IDX_TO_LABEL[pred_idx],
                "pred_label_idx": pred_idx,
                "n_seeds": len(sub),
                "seeds": seeds_str,
                "split_used": split_used,
                "p_contra_mean": float(sub["p_contra"].mean()),
                "p_strong_mean": float(sub["p_strong"].mean()),
                "p_svm_mean": float(sub["p_svm"].mean()),
                "setting": setting,
            })
        agg_df = pd.DataFrame(agg_rows)
        aggregated[setting] = agg_df
        log(f"  {setting}: {len(agg_df)} aggregated predictions")

        # Save predictions
        pred_path = OUTPUT_DIR / f"r4_replay_predictions_{setting}.csv"
        agg_df.to_csv(pred_path, index=False, encoding="utf-8-sig")
        log(f"    -> {pred_path}")

        # Also save raw per-seed predictions
        raw_path = OUTPUT_DIR / f"r4_replay_predictions_{setting}_per_seed.csv"
        pred_df.to_csv(raw_path, index=False, encoding="utf-8-sig")

    # ---- Step 4: Compute metrics ----
    log("\n[Step 4] Computing metrics for each setting ...")
    metrics_rows = []
    confusion_matrices = {}

    for setting in SETTINGS:
        agg_df = aggregated[setting]
        if len(agg_df) == 0:
            metrics_rows.append({"setting": setting, "n_eval": 0})
            continue

        y_4idx = agg_df["true_label"].map(LABEL_TO_IDX).values
        pred_4idx = agg_df["pred_label_idx"].values
        y_strong = (agg_df["true_label"] == "strong_action_overclaim").astype(int).values
        y_esc = (agg_df["true_label"] != "supported").astype(int).values
        y_contra = (agg_df["true_label"] == "contradiction_candidate").astype(int).values

        m = compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx)
        m["setting"] = setting
        m["n_eval"] = len(agg_df)
        metrics_rows.append(m)

        cm = confusion_matrix(y_4idx, pred_4idx, labels=[0, 1, 2, 3])
        confusion_matrices[setting] = cm.tolist()
        log(f"  {setting}: n={len(agg_df)}, strong_f1={m['strong_action_f1']:.4f}, macro_f1={m['macro_f1']:.4f}")

    metrics_df = pd.DataFrame(metrics_rows)
    metrics_path = OUTPUT_DIR / "r4_replay_metrics_by_setting.csv"
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    log(f"  -> {metrics_path}")

    cm_path = OUTPUT_DIR / "r4_replay_confusion_matrices.json"
    with open(cm_path, "w", encoding="utf-8") as f:
        json.dump({
            "labels": LABELS_4,
            "label_indices": [0, 1, 2, 3],
            "per_setting": confusion_matrices,
        }, f, indent=2, default=json_default)
    log(f"  -> {cm_path}")

    # ---- Step 5: Compute gap ----
    log("\n[Step 5] Computing oracle-to-retrieved gaps ...")
    metrics_dict = {row["setting"]: row for row in metrics_rows}

    oracle_strong_f1 = metrics_dict.get("oracle", {}).get("strong_action_f1", 0)
    top1_strong_f1 = metrics_dict.get("bm25_top1", {}).get("strong_action_f1", 0)
    top3_strong_f1 = metrics_dict.get("bm25_top3", {}).get("strong_action_f1", 0)
    top5_strong_f1 = metrics_dict.get("bm25_top5", {}).get("strong_action_f1", 0)

    oracle_to_top1_gap = oracle_strong_f1 - top1_strong_f1
    oracle_to_top3_gap = oracle_strong_f1 - top3_strong_f1
    oracle_to_top5_gap = oracle_strong_f1 - top5_strong_f1

    retrieved_f1s = {"bm25_top1": top1_strong_f1, "bm25_top3": top3_strong_f1, "bm25_top5": top5_strong_f1}
    best_retrieved_setting = max(retrieved_f1s, key=retrieved_f1s.get)
    oracle_to_best_gap = oracle_strong_f1 - retrieved_f1s[best_retrieved_setting]

    log(f"  oracle strong-F1: {oracle_strong_f1:.4f}")
    log(f"  top1 strong-F1:   {top1_strong_f1:.4f} (gap={oracle_to_top1_gap:.4f})")
    log(f"  top3 strong-F1:   {top3_strong_f1:.4f} (gap={oracle_to_top3_gap:.4f})")
    log(f"  top5 strong-F1:   {top5_strong_f1:.4f} (gap={oracle_to_top5_gap:.4f})")
    log(f"  best retrieved: {best_retrieved_setting} (gap={oracle_to_best_gap:.4f})")

    retrieved_replay_passed = oracle_to_best_gap <= 0.05

    # ---- Step 6: Error analysis ----
    log("\n[Step 6] Error analysis ...")
    error_rows = []
    oracle_agg = aggregated["oracle"]
    best_agg = aggregated[best_retrieved_setting] if best_retrieved_setting in aggregated else aggregated.get("bm25_top5", pd.DataFrame())

    if len(oracle_agg) > 0 and len(best_agg) > 0:
        # Merge oracle and best retrieved
        merged = oracle_agg[["candidate_id", "true_label", "pred_label", "pred_label_idx"]].rename(
            columns={"pred_label": "oracle_pred", "pred_label_idx": "oracle_pred_idx"}
        ).merge(
            best_agg[["candidate_id", "pred_label", "pred_label_idx"]].rename(
                columns={"pred_label": "retrieved_pred", "pred_label_idx": "retrieved_pred_idx"}
            ),
            on="candidate_id", how="inner"
        )

        for _, r in merged.iterrows():
            true_label = r["true_label"]
            oracle_pred = r["oracle_pred"]
            retrieved_pred = r["retrieved_pred"]

            error_types = []

            # Oracle correct, retrieved wrong
            oracle_correct = (oracle_pred == true_label)
            retrieved_correct = (retrieved_pred == true_label)

            if not retrieved_correct and oracle_correct:
                error_types.append("retrieval_harmed_screening")
            if not retrieved_correct and not oracle_correct:
                error_types.append("both_failed")
            if retrieved_correct and not oracle_correct:
                error_types.append("retrieval_helped")

            # Specific error categories
            if true_label == "strong_action_overclaim" and retrieved_pred != "strong_action_overclaim":
                error_types.append("strong_action_false_negative")
            if true_label != "strong_action_overclaim" and retrieved_pred == "strong_action_overclaim":
                error_types.append("strong_action_false_positive")
            if {true_label, retrieved_pred} == {"supported", "mild_scope_overclaim"}:
                error_types.append("supported_mild_confusion")
            if retrieved_pred == "contradiction_candidate" and true_label != "contradiction_candidate":
                error_types.append("contradiction_false_positive")
            if true_label == "contradiction_candidate" and retrieved_pred != "contradiction_candidate":
                error_types.append("contradiction_false_negative")

            if not error_types:
                error_types.append("correct")

            error_rows.append({
                "candidate_id": r["candidate_id"],
                "true_label": true_label,
                "oracle_pred": oracle_pred,
                "retrieved_pred": retrieved_pred,
                "oracle_correct": oracle_correct,
                "retrieved_correct": retrieved_correct,
                "error_types": "|".join(error_types),
                "best_retrieved_setting": best_retrieved_setting,
            })

    error_df = pd.DataFrame(error_rows)
    error_path = OUTPUT_DIR / "r4_replay_error_analysis.csv"
    error_df.to_csv(error_path, index=False, encoding="utf-8-sig")
    log(f"  -> {error_path}")

    # Error summary
    if len(error_df) > 0:
        n_correct = len(error_df[error_df["error_types"] == "correct"])
        n_retrieval_harmed = len(error_df[error_df["error_types"].str.contains("retrieval_harmed_screening")])
        n_both_failed = len(error_df[error_df["error_types"].str.contains("both_failed")])
        n_retrieval_helped = len(error_df[error_df["error_types"].str.contains("retrieval_helped")])
        log(f"  Correct: {n_correct}, retrieval_harmed: {n_retrieval_harmed}, both_failed: {n_both_failed}, retrieval_helped: {n_retrieval_helped}")

    # Determine main bottleneck
    if len(error_df) > 0:
        n_screening_fail = len(error_df[error_df["error_types"].str.contains("strong_action_false_negative|strong_action_false_positive|supported_mild_confusion|contradiction")])
        n_retrieval_fail = len(error_df[error_df["error_types"].str.contains("retrieval_harmed_screening")])
        if n_retrieval_fail > n_screening_fail:
            main_bottleneck = "retrieval"
        elif n_screening_fail > n_retrieval_fail:
            main_bottleneck = "screening"
        else:
            main_bottleneck = "both"
    else:
        main_bottleneck = "unknown"

    # ---- Step 7: Gate ----
    log("\n[Step 7] Writing gate ...")
    n_eval = metrics_dict.get("oracle", {}).get("n_eval", 0)

    gate = {
        "task": "Formal R4 Replay on PDF-Retrieved Evidence v1",
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "artifacts_loaded": True,
        "used_proxy": False,
        "retrained_model": False,
        "thresholds_changed": False,
        "n_eval": int(n_eval),
        "n_missing_due_to_split": int(len(missing_cids)),
        "oracle_strong_f1": float(oracle_strong_f1),
        "top1_strong_f1": float(top1_strong_f1),
        "top3_strong_f1": float(top3_strong_f1),
        "top5_strong_f1": float(top5_strong_f1),
        "oracle_to_top1_gap": float(oracle_to_top1_gap),
        "oracle_to_top3_gap": float(oracle_to_top3_gap),
        "oracle_to_top5_gap": float(oracle_to_top5_gap),
        "best_retrieved_setting": best_retrieved_setting,
        "oracle_to_best_gap": float(oracle_to_best_gap),
        "retrieved_replay_passed": bool(retrieved_replay_passed),
        "main_bottleneck": main_bottleneck,
        "supports_pdf_corpus_screening_claim": bool(retrieved_replay_passed),
        "supports_v3_17_mainline": bool(retrieved_replay_passed),
        "recommended_next_step": (
            f"R4 replay on retrieved evidence {'PASSED' if retrieved_replay_passed else 'FAILED'} "
            f"(oracle-to-best gap={oracle_to_best_gap:.4f}). "
            + ("V3.17 mainline supported. Proceed to dense retrieval + reranker upgrade." if retrieved_replay_passed else
               "V3.17 mainline needs retrieval upgrade (dense/reranker) before R4 screening can retain strong_action signal.")
        ),
        "prohibitions_enforced": [
            "no_model_training",
            "no_api_calls",
            "no_network",
            "no_threshold_change",
            "no_original_data_modification",
            "no_paper_modification",
            "no_file_deletion",
            "no_cue_based_proxy",
            "no_silver_as_gold",
            "no_natural_distribution_claim",
            "no_split_missing_in_main_metrics",
        ],
        "output_files": [
            "hcm_features_replay_oracle.csv",
            "hcm_features_replay_bm25_top1.csv",
            "hcm_features_replay_bm25_top3.csv",
            "hcm_features_replay_bm25_top5.csv",
            "r4_replay_predictions_oracle.csv",
            "r4_replay_predictions_bm25_top1.csv",
            "r4_replay_predictions_bm25_top3.csv",
            "r4_replay_predictions_bm25_top5.csv",
            "r4_replay_metrics_by_setting.csv",
            "r4_replay_confusion_matrices.json",
            "r4_replay_error_analysis.csv",
            "r4_replay_gate.json",
            "r4_replay_report.md",
        ],
    }
    gate_path = OUTPUT_DIR / "r4_replay_gate.json"
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, default=json_default)
    log(f"  -> {gate_path}")

    # ---- Step 8: Report ----
    log("\n[Step 8] Writing report ...")
    report = []
    report.append("# Formal R4 Replay on PDF-Retrieved Evidence v1\n")
    report.append(f"- 审计时间: {gate['audit_date']}")
    report.append(f"- 评估样本数: {n_eval} (out-of-fold candidates)")
    report.append(f"- 缺失 (split-missing): {len(missing_cids)} (不纳入主指标)")
    report.append(f"- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网")
    report.append("")
    report.append("## 1. 是否成功加载 recovered R4 artifacts？\n")
    report.append(f"**是**。10 个 seed 的 artifacts 全部加载成功 (clf_contra/clf_strong/clf_svm + scaler + thresholds + feature_columns + label_mapping)。")
    report.append(f"路径: `{RECOVERY_ARTIFACTS}\\seed_<N>\\`")
    report.append("")

    report.append("## 2. 是否没有使用 proxy？\n")
    report.append(f"**是**。所有预测均来自 R4_conservative_strong 路由 (clf_contra + clf_strong + clf_svm + route_conservative_strong)，无 cue-based proxy。")
    report.append("")

    report.append("## 3. 是否没有重新训练/调参？\n")
    report.append(f"**是**。使用 r4_minimal_recovery_v1 已保存的 classifiers 和 thresholds，未重新训练，未调整阈值。")
    report.append(f"thresholds 来源: routing_variant_results_by_seed.csv (historical per-seed values)")
    report.append("")

    report.append("## 4. retrieved evidence 下 R4 strong_action 是否保留？\n")
    report.append(f"| Setting | n_eval | strong-F1 | macro-F1 | strong-precision | strong-recall |")
    report.append(f"|---------|--------|-----------|----------|------------------|---------------|")
    for setting in SETTINGS:
        m = metrics_dict.get(setting, {})
        report.append(f"| {setting} | {m.get('n_eval', 0)} | {m.get('strong_action_f1', 0):.4f} | {m.get('macro_f1', 0):.4f} | {m.get('strong_precision', 0):.4f} | {m.get('strong_recall', 0):.4f} |")
    report.append("")
    report.append(f"**retrieved replay {'通过' if retrieved_replay_passed else '未通过'}** (oracle-to-best gap = {oracle_to_best_gap:.4f}, 阈值 0.05)")
    report.append("")

    report.append("## 5. top1/top3/top5 哪个最好？\n")
    report.append(f"**{best_retrieved_setting}** (strong-F1 = {retrieved_f1s[best_retrieved_setting]:.4f})")
    report.append(f"\n| Setting | strong-F1 | gap vs oracle |")
    report.append(f"|---------|-----------|---------------|")
    report.append(f"| bm25_top1 | {top1_strong_f1:.4f} | {oracle_to_top1_gap:.4f} |")
    report.append(f"| bm25_top3 | {top3_strong_f1:.4f} | {oracle_to_top3_gap:.4f} |")
    report.append(f"| bm25_top5 | {top5_strong_f1:.4f} | {oracle_to_top5_gap:.4f} |")
    report.append("")

    report.append("## 6. oracle-to-best gap 多大？\n")
    report.append(f"**{oracle_to_best_gap:.4f}** (oracle strong-F1 = {oracle_strong_f1:.4f}, best retrieved = {retrieved_f1s[best_retrieved_setting]:.4f})")
    report.append(f"\n判定: gap <= 0.05 → {'通过' if retrieved_replay_passed else '未通过'}")
    report.append("")

    report.append("## 7. 主要错误来自 retrieval 还是 screening？\n")
    if len(error_df) > 0:
        report.append(f"主瓶颈: **{main_bottleneck}**")
        report.append(f"\n错误分布 (best retrieved = {best_retrieved_setting}):")
        report.append(f"- Correct: {len(error_df[error_df['error_types'] == 'correct'])}")
        report.append(f"- Retrieval harmed screening: {len(error_df[error_df['error_types'].str.contains('retrieval_harmed_screening')])}")
        report.append(f"- Both failed: {len(error_df[error_df['error_types'].str.contains('both_failed')])}")
        report.append(f"- Retrieval helped: {len(error_df[error_df['error_types'].str.contains('retrieval_helped')])}")
        report.append(f"- Strong action false negative: {len(error_df[error_df['error_types'].str.contains('strong_action_false_negative')])}")
        report.append(f"- Strong action false positive: {len(error_df[error_df['error_types'].str.contains('strong_action_false_positive')])}")
    report.append("")

    report.append("## 8. 是否支持 V3.17 主线：offline PDF-corpus retrieval + CESE-OCN/R4 screening？\n")
    if retrieved_replay_passed:
        report.append(f"**是**。oracle-to-best gap = {oracle_to_best_gap:.4f} <= 0.05，retrieved evidence 下 R4 strong_action screening 信号保留。")
        report.append(f"\nV3.17 主线成立: offline PDF-corpus retrieval (BM25) + CESE-OCN/R4 screening 可行。")
        report.append(f"\n下一步建议: dense retrieval (sentence-transformers) + reranker 升级，进一步缩小 gap。")
    else:
        report.append(f"**否**。oracle-to-best gap = {oracle_to_best_gap:.4f} > 0.05，retrieved evidence 损害 R4 strong_action screening。")
        report.append(f"\nV3.17 主线需要 retrieval 升级 (dense/reranker) 后才能成立。")
    report.append("")

    report.append("## 输出文件清单\n")
    for f in gate["output_files"]:
        report.append(f"- `{f}`")
    report.append("")

    report_path = OUTPUT_DIR / "r4_replay_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    log(f"  -> {report_path}")

    # ---- Final summary ----
    log("\n" + "=" * 70)
    log("REPLAY SUMMARY")
    log("=" * 70)
    log(f"n_eval: {n_eval}")
    log(f"oracle strong-F1: {oracle_strong_f1:.4f}")
    log(f"top1 strong-F1: {top1_strong_f1:.4f} (gap={oracle_to_top1_gap:.4f})")
    log(f"top3 strong-F1: {top3_strong_f1:.4f} (gap={oracle_to_top3_gap:.4f})")
    log(f"top5 strong-F1: {top5_strong_f1:.4f} (gap={oracle_to_top5_gap:.4f})")
    log(f"best retrieved: {best_retrieved_setting} (gap={oracle_to_best_gap:.4f})")
    log(f"retrieved_replay_passed: {retrieved_replay_passed}")
    log(f"supports_v3_17_mainline: {gate['supports_v3_17_mainline']}")


if __name__ == "__main__":
    main()
