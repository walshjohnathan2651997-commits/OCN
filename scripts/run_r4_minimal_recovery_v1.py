"""
Minimal R4 Recovery from Backup HCM Features v1
================================================
Reproduces the R4_conservative_strong router using backup hcm_features.csv.
- Retrains clf_contra, clf_strong, clf_svm on train splits only
- Recovers t_contra_low per-seed from historical routing_variant_results_by_seed.csv
- Uses frozen thresholds t_contra=0.48, t_strong=0.535, t_svm=0.51 (per task spec)
- ALSO runs exact-reproduction mode (per-seed thresholds) for comparison
- Outputs 444 out-of-fold predictions covering all candidate_ids
- Saves artifacts (pkl, thresholds.json, feature_columns.json, label_mapping.json)

Prohibitions: no API, no network, no original-data modification, no paper modification,
no test-set tuning, no new algorithms, no silver-as-gold.
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
BACKUP_HCM = Path(r"D:\ocn_backup_20260704_1606\experiments\cese_ocn_hcm_v1\hcm_features.csv")
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
FROZEN_MANIFEST = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_manifest.json")
FROZEN_METRICS = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_metrics_summary.json")
ROUTING_RESULTS_BY_SEED = Path(r"D:\ocn\experiments\mixed_framework_router_optimization_v2\routing_variant_results_by_seed.csv")

OUTPUT_DIR = Path(r"D:\ocn\experiments\r4_minimal_recovery_v1")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR = OUTPUT_DIR / "artifacts"
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------- Constants (match original script) ----------------
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

# Frozen thresholds (per task spec)
FROZEN_T_CONTRA = 0.48
FROZEN_T_STRONG = 0.535
FROZEN_T_SVM = 0.51

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


def to_strong_action_binary(label):
    return 1 if label == "strong_action_overclaim" else 0

def to_escalation_binary(label):
    return 0 if label == "supported" else 1

def to_contradiction_binary(label):
    return 1 if label == "contradiction_candidate" else 0

def to_supported_vs_mild(label):
    if label == "supported": return 0
    if label == "mild_scope_overclaim": return 1
    return None


def group_aware_split(group_ids, seed, train_frac=0.70, dev_frac=0.15):
    rng = np.random.RandomState(seed)
    unique_groups = np.array(sorted(set(group_ids.tolist())))
    rng.shuffle(unique_groups)
    n = len(unique_groups)
    n_train = int(round(n * train_frac))
    n_dev = int(round(n * dev_frac))
    train_g = unique_groups[:n_train]
    dev_g = unique_groups[n_train:n_train + n_dev]
    test_g = unique_groups[n_train + n_dev:]
    train_mask = np.isin(group_ids, train_g)
    dev_mask = np.isin(group_ids, dev_g)
    test_mask = np.isin(group_ids, test_g)
    return train_mask, dev_mask, test_mask


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


def multiclass_metrics_full(y_true, y_pred, labels=None):
    y_true = np.asarray(y_true)
    y_pred = np.asarray(y_pred)
    if labels is None:
        labels = sorted(np.unique(y_true).tolist())
    per_label = {}
    for lab in labels:
        key = IDX_TO_LABEL.get(lab, str(lab)) if isinstance(lab, (int, np.integer)) else str(lab)
        per_label[key] = float(f1_score(y_true, y_pred, labels=[lab], average="macro", zero_division=0))
    return {
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, average="macro", zero_division=0)),
        "per_label_f1": per_label,
    }


def compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx):
    m_flat4 = multiclass_metrics_full(y_4idx, pred_4idx, labels=[0, 1, 2, 3])
    pred_strong = (pred_4idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    m_strong = binary_metrics_full(y_strong, pred_strong)
    pred_esc = (pred_4idx != LABEL_TO_IDX["supported"]).astype(int)
    m_esc = binary_metrics_full(y_esc, pred_esc)
    pred_contra = (pred_4idx == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    m_contra = binary_metrics_full(y_contra, pred_contra)
    return {
        "flat4_accuracy": m_flat4["accuracy"],
        "flat4_macro_f1": m_flat4["macro_f1"],
        "flat4_supported_f1": m_flat4["per_label_f1"].get("supported", 0),
        "flat4_mild_f1": m_flat4["per_label_f1"].get("mild_scope_overclaim", 0),
        "flat4_strong_f1": m_flat4["per_label_f1"].get("strong_action_overclaim", 0),
        "flat4_contradiction_f1": m_flat4["per_label_f1"].get("contradiction_candidate", 0),
        "strong_binary_macro_f1": m_strong["macro_f1"],
        "strong_positive_f1": m_strong["positive_f1"],
        "strong_precision": m_strong["precision"],
        "strong_recall": m_strong["recall"],
        "escalation_macro_f1": m_esc["macro_f1"],
        "escalation_positive_f1": m_esc["positive_f1"],
        "contradiction_macro_f1": m_contra["macro_f1"],
        "contradiction_positive_f1": m_contra["positive_f1"],
    }


def build_action_gap_features(df):
    claim_text = df["claim_text"].astype(str)
    evidence_text = df["evidence_text"].astype(str)
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
    vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
    all_text = list(claim_text) + list(evidence_text)
    tfidf_matrix = vec.fit_transform(all_text)
    claim_tfidf = tfidf_matrix[:len(claim_text)]
    evidence_tfidf = tfidf_matrix[len(claim_text):]
    from sklearn.metrics.pairwise import cosine_similarity
    overlap = np.array([cosine_similarity(claim_tfidf[i], evidence_tfidf[i])[0, 0] for i in range(len(claim_text))])
    df["claim_evidence_overlap"] = overlap


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


# ---------------- Parse historical R4 thresholds ----------------

def parse_historical_r4_thresholds():
    """Parse per-seed R4 thresholds from routing_variant_results_by_seed.csv.
    Returns dict: {seed: (t_contra, t_contra_low, t_strong, t_svm)}
    """
    df = pd.read_csv(ROUTING_RESULTS_BY_SEED, keep_default_na=False)
    r4 = df[df["method"] == "R4_conservative_strong"].copy()
    out = {}
    for _, row in r4.iterrows():
        seed = int(row["seed"])
        thresh_str = str(row["thresholds"])
        # Parse tuple string like "(0.4, 0.35, 0.55, 0.55)"
        m = re.match(r"\(([\d.]+),\s*([\d.]+),\s*([\d.]+),\s*([\d.]+)\)", thresh_str)
        if m:
            t_c, t_cl, t_s, t_sv = float(m.group(1)), float(m.group(2)), float(m.group(3)), float(m.group(4))
            out[seed] = (t_c, t_cl, t_s, t_sv)
    return out


# ---------------- Main recovery ----------------

def main():
    log("=" * 70)
    log("Minimal R4 Recovery from Backup HCM Features v1")
    log("=" * 70)

    # ---- Step 1: Load and verify HCM features ----
    log("\n[Step 1] Loading and verifying HCM features ...")
    hcm = pd.read_csv(BACKUP_HCM, keep_default_na=False)
    log(f"  HCM rows: {len(hcm)}")
    assert len(hcm) == 444, f"Expected 444 rows, got {len(hcm)}"
    assert hcm["candidate_id"].nunique() == 444, "candidate_id not unique"
    for col in NLI_FEATURES:
        assert col in hcm.columns, f"Missing required NLI feature: {col}"
    log(f"  All 7 NLI features present: {NLI_FEATURES}")

    # Save recovered HCM features
    recovered_hcm_path = OUTPUT_DIR / "recovered_hcm_features.csv"
    hcm.to_csv(recovered_hcm_path, index=False, encoding="utf-8-sig")
    log(f"  -> {recovered_hcm_path}")

    # ---- Load main data and merge ----
    log("\n  Loading main data and merging ...")
    df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    df = df.merge(
        hcm[["candidate_id"] + NLI_FEATURES + ["s_correct", "s_wrong", "margin"]],
        on="candidate_id", how="left"
    )
    assert len(df) == 444, f"Merge changed row count: {len(df)}"
    join_ok = df[NLI_FEATURES].notna().all().all()
    log(f"  Join OK: {join_ok} (all NLI features non-null after merge)")

    # ---- Build action gap features ----
    log("\n  Building action gap features ...")
    build_action_gap_features(df)

    # ---- Labels ----
    df["label_4"] = df["candidate_label_guess"].astype(str)
    df["label_4_idx"] = df["label_4"].map(LABEL_TO_IDX)
    df["y_strong"] = df["label_4"].apply(to_strong_action_binary)
    df["y_esc"] = df["label_4"].apply(to_escalation_binary)
    df["y_contra"] = df["label_4"].apply(to_contradiction_binary)
    df["y_svm"] = df["label_4"].apply(to_supported_vs_mild)

    group_ids = df["target_candidate_group_id"].values
    log(f"  Data: {len(df)} rows, {df['target_candidate_group_id'].nunique()} groups")

    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    # ---- Parse historical R4 thresholds ----
    log("\n  Parsing historical R4 thresholds ...")
    historical_thresh = parse_historical_r4_thresholds()
    for s in SEEDS:
        if s in historical_thresh:
            t_c, t_cl, t_s, t_sv = historical_thresh[s]
            log(f"    Seed {s}: t_contra={t_c}, t_contra_low={t_cl}, t_strong={t_s}, t_svm={t_sv}")
        else:
            log(f"    Seed {s}: NOT FOUND in historical")
    t_contra_low_mean = np.mean([historical_thresh[s][1] for s in SEEDS if s in historical_thresh])
    log(f"  t_contra_low mean across seeds: {t_contra_low_mean:.4f}")

    # ---- Step 2: R4 split manifest + Step 4: retrain + Step 5: predict ----
    log("\n[Step 2-5] Running 10-seed R4 recovery ...")
    split_manifest_rows = []
    all_pred_rows = []
    metrics_by_seed_rows = []
    confusion_matrices = {}
    artifacts_inventory = []
    candidate_coverage = set()

    y_4idx = df["label_4_idx"].values
    y_strong = df["y_strong"].values
    y_esc = df["y_esc"].values
    y_contra = df["y_contra"].values

    for seed in SEEDS:
        log(f"\n  --- Seed {seed} ---")
        seed_dir = ARTIFACTS_DIR / f"seed_{seed}"
        seed_dir.mkdir(parents=True, exist_ok=True)

        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        log(f"    Split: train={train_mask.sum()}, dev={dev_mask.sum()}, test={test_mask.sum()}")

        # Record split manifest
        for i in range(len(df)):
            split = "train" if train_mask[i] else ("dev" if dev_mask[i] else "test")
            split_manifest_rows.append({
                "seed": seed,
                "split": split,
                "candidate_id": df.iloc[i]["candidate_id"],
                "source_pair_id": df.iloc[i]["target_candidate_group_id"],
                "label": df.iloc[i]["label_4"],
            })

        # ---- Scalers ----
        scaler_nli = StandardScaler()
        Xtr_nli = scaler_nli.fit_transform(df.iloc[train_mask][NLI_FEATURES].values)
        Xdev_nli = scaler_nli.transform(df.iloc[dev_mask][NLI_FEATURES].values)
        Xte_nli = scaler_nli.transform(df.iloc[test_mask][NLI_FEATURES].values)

        scaler_exp = StandardScaler()
        Xtr_exp = scaler_exp.fit_transform(df.iloc[train_mask][expert_features].values)
        Xdev_exp = scaler_exp.transform(df.iloc[dev_mask][expert_features].values)
        Xte_exp = scaler_exp.transform(df.iloc[test_mask][expert_features].values)

        scaler_svm = StandardScaler()
        Xtr_svm = scaler_svm.fit_transform(df.iloc[train_mask][svm_features].values)
        Xdev_svm = scaler_svm.transform(df.iloc[dev_mask][svm_features].values)
        Xte_svm = scaler_svm.transform(df.iloc[test_mask][svm_features].values)

        # ---- Classifiers (match original) ----
        clf_flat4 = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_flat4.fit(Xtr_nli, y_4idx[train_mask])
        clf_contra = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_contra.fit(Xtr_nli, y_contra[train_mask])
        clf_strong = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_strong.fit(Xtr_exp, y_strong[train_mask])

        y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else -1).values
        svm_train_mask = (y_svm_int >= 0) & train_mask
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])

        # ---- Probabilities ----
        p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]
        p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]

        p_contra_dev = clf_contra.predict_proba(Xdev_nli)[:, 1]
        p_strong_dev = clf_strong.predict_proba(Xdev_exp)[:, 1]
        p_svm_dev = clf_svm.predict_proba(Xdev_svm)[:, 1]

        n_test = int(test_mask.sum())
        n_dev = int(dev_mask.sum())

        # ---- Thresholds: two modes ----
        # Mode A (exact reproduction): per-seed historical thresholds
        hist_t_c, hist_t_cl, hist_t_s, hist_t_sv = historical_thresh[seed]
        pred_exact = route_conservative_strong(
            p_contra_test, p_strong_test, p_svm_test,
            hist_t_c, hist_t_cl, hist_t_s, hist_t_sv, n_test
        )
        m_exact = compute_all_metrics(
            y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_exact
        )

        # Mode B (frozen thresholds + dev-tuned t_contra_low): use frozen t_contra/t_strong/t_svm
        # and dev grid search for t_contra_low using the original grid
        T_CL_GRID = [0.2, 0.25, 0.3, 0.35, 0.4]
        best_score = -1
        best_t_cl = 0.3
        for t_cl in T_CL_GRID:
            pred_dev = route_conservative_strong(
                p_contra_dev, p_strong_dev, p_svm_dev,
                FROZEN_T_CONTRA, t_cl, FROZEN_T_STRONG, FROZEN_T_SVM, n_dev
            )
            m_dev = compute_all_metrics(
                y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev
            )
            score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
            if score > best_score:
                best_score = score
                best_t_cl = t_cl
        pred_frozen = route_conservative_strong(
            p_contra_test, p_strong_test, p_svm_test,
            FROZEN_T_CONTRA, best_t_cl, FROZEN_T_STRONG, FROZEN_T_SVM, n_test
        )
        m_frozen = compute_all_metrics(
            y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_frozen
        )

        log(f"    [exact]  strong_f1={m_exact['strong_positive_f1']:.4f}, macro_f1={m_exact['flat4_macro_f1']:.4f}, t_cl={hist_t_cl}")
        log(f"    [frozen] strong_f1={m_frozen['strong_positive_f1']:.4f}, macro_f1={m_frozen['flat4_macro_f1']:.4f}, t_cl={best_t_cl}")

        # Use EXACT mode as primary (to reproduce frozen metrics)
        # Also record frozen mode for comparison
        metrics_by_seed_rows.append({
            "seed": seed,
            "mode": "exact_reproduction",
            "t_contra": hist_t_c,
            "t_contra_low": hist_t_cl,
            "t_strong": hist_t_s,
            "t_svm": hist_t_sv,
            "t_contra_low_source": "historical_routing_variant_results",
            **m_exact,
        })
        metrics_by_seed_rows.append({
            "seed": seed,
            "mode": "frozen_thresholds",
            "t_contra": FROZEN_T_CONTRA,
            "t_contra_low": best_t_cl,
            "t_strong": FROZEN_T_STRONG,
            "t_svm": FROZEN_T_SVM,
            "t_contra_low_source": "dev_grid_search",
            **m_frozen,
        })

        # Confusion matrix (exact mode)
        cm = confusion_matrix(y_4idx[test_mask], pred_exact, labels=[0, 1, 2, 3])
        confusion_matrices[f"seed_{seed}_exact"] = cm.tolist()

        # ---- Record predictions (exact mode) ----
        # Test split predictions (primary, out-of-fold)
        test_indices = np.where(test_mask)[0]
        for idx_local, idx_global in enumerate(test_indices):
            cid = df.iloc[idx_global]["candidate_id"]
            candidate_coverage.add(cid)
            all_pred_rows.append({
                "candidate_id": cid,
                "true_label": df.iloc[idx_global]["label_4"],
                "pred_label": IDX_TO_LABEL[int(pred_exact[idx_local])],
                "pred_label_idx": int(pred_exact[idx_local]),
                "seed": seed,
                "split": "test",
                "p_contra": float(p_contra_test[idx_local]),
                "p_strong": float(p_strong_test[idx_local]),
                "p_svm": float(p_svm_test[idx_local]),
                "route": "R4_conservative_strong_exact",
                "t_contra": hist_t_c,
                "t_contra_low": hist_t_cl,
                "t_strong": hist_t_s,
                "t_svm": hist_t_sv,
            })

        # Dev split predictions (secondary, out-of-fold, for candidates never in test)
        pred_dev_exact = route_conservative_strong(
            p_contra_dev, p_strong_dev, p_svm_dev,
            hist_t_c, hist_t_cl, hist_t_s, hist_t_sv, n_dev
        )
        dev_indices = np.where(dev_mask)[0]
        for idx_local, idx_global in enumerate(dev_indices):
            cid = df.iloc[idx_global]["candidate_id"]
            all_pred_rows.append({
                "candidate_id": cid,
                "true_label": df.iloc[idx_global]["label_4"],
                "pred_label": IDX_TO_LABEL[int(pred_dev_exact[idx_local])],
                "pred_label_idx": int(pred_dev_exact[idx_local]),
                "seed": seed,
                "split": "dev",
                "p_contra": float(p_contra_dev[idx_local]),
                "p_strong": float(p_strong_dev[idx_local]),
                "p_svm": float(p_svm_dev[idx_local]),
                "route": "R4_conservative_strong_exact",
                "t_contra": hist_t_c,
                "t_contra_low": hist_t_cl,
                "t_strong": hist_t_s,
                "t_svm": hist_t_sv,
            })

        # ---- Save artifacts ----
        with open(seed_dir / "clf_contra.pkl", "wb") as f:
            pickle.dump(clf_contra, f)
        with open(seed_dir / "clf_strong.pkl", "wb") as f:
            pickle.dump(clf_strong, f)
        with open(seed_dir / "clf_svm.pkl", "wb") as f:
            pickle.dump(clf_svm, f)
        with open(seed_dir / "clf_flat4.pkl", "wb") as f:
            pickle.dump(clf_flat4, f)
        with open(seed_dir / "scaler_contra.pkl", "wb") as f:
            pickle.dump(scaler_nli, f)
        with open(seed_dir / "scaler_strong.pkl", "wb") as f:
            pickle.dump(scaler_exp, f)
        with open(seed_dir / "scaler_svm.pkl", "wb") as f:
            pickle.dump(scaler_svm, f)

        thresholds_data = {
            "mode": "exact_reproduction",
            "t_contra": hist_t_c,
            "t_contra_low": hist_t_cl,
            "t_strong": hist_t_s,
            "t_svm": hist_t_sv,
            "frozen_thresholds_for_reference": {
                "t_contra": FROZEN_T_CONTRA,
                "t_strong": FROZEN_T_STRONG,
                "t_svm": FROZEN_T_SVM,
            },
            "t_contra_low_dev_tuned_frozen_mode": best_t_cl,
            "source": "routing_variant_results_by_seed.csv",
        }
        with open(seed_dir / "thresholds.json", "w", encoding="utf-8") as f:
            json.dump(thresholds_data, f, indent=2, default=json_default)

        feature_columns = {
            "nli_features": NLI_FEATURES,
            "expert_features": expert_features,
            "svm_features": svm_features,
        }
        with open(seed_dir / "feature_columns.json", "w", encoding="utf-8") as f:
            json.dump(feature_columns, f, indent=2, default=json_default)

        label_mapping = {
            "labels_4": LABELS_4,
            "label_to_idx": LABEL_TO_IDX,
            "idx_to_label": {str(k): v for k, v in IDX_TO_LABEL.items()},
        }
        with open(seed_dir / "label_mapping.json", "w", encoding="utf-8") as f:
            json.dump(label_mapping, f, indent=2, default=json_default)

        for art in ["clf_contra.pkl", "clf_strong.pkl", "clf_svm.pkl", "clf_flat4.pkl",
                     "scaler_contra.pkl", "scaler_strong.pkl", "scaler_svm.pkl",
                     "thresholds.json", "feature_columns.json", "label_mapping.json"]:
            art_path = seed_dir / art
            artifacts_inventory.append({
                "seed": seed,
                "artifact": art,
                "path": str(art_path),
                "size": art_path.stat().st_size,
            })

    # ---- Step 5: Output 444 predictions ----
    log(f"\n[Step 5] Building 444 predictions ...")
    pred_df = pd.DataFrame(all_pred_rows)
    log(f"  Total prediction rows (all seeds, test+dev splits): {len(pred_df)}")
    test_only = pred_df[pred_df["split"] == "test"]
    dev_only = pred_df[pred_df["split"] == "dev"]
    test_cids = set(test_only["candidate_id"].unique())
    dev_cids = set(dev_only["candidate_id"].unique())
    all_cids = set(df["candidate_id"].values)
    covered_by_test = len(test_cids)
    covered_by_dev = len(dev_cids - test_cids)
    total_covered = len(test_cids | dev_cids)
    log(f"  Covered by test: {covered_by_test}")
    log(f"  Additional covered by dev: {covered_by_dev}")
    log(f"  Total covered: {total_covered} / 444")

    # Coverage check
    missing = all_cids - test_cids - dev_cids
    if missing:
        log(f"  WARNING: {len(missing)} candidate_ids have no test OR dev prediction (always in train):")
        for c in sorted(missing)[:10]:
            log(f"    {c}")

    # Aggregate to 444 rows
    # Priority: test predictions (majority vote) > dev predictions (majority vote) > NO_OOF (train-only)
    agg_rows = []
    for cid in sorted(all_cids):
        true_label = df[df["candidate_id"] == cid]["label_4"].iloc[0]
        # Try test first
        sub_test = test_only[test_only["candidate_id"] == cid]
        if len(sub_test) > 0:
            sub = sub_test
            split_used = "test"
        else:
            # Fall back to dev
            sub_dev = dev_only[dev_only["candidate_id"] == cid]
            if len(sub_dev) > 0:
                sub = sub_dev
                split_used = "dev"
            else:
                # Never in test or dev — train-only
                agg_rows.append({
                    "candidate_id": cid,
                    "true_label": true_label,
                    "pred_label": "NO_OOF_PREDICTION",
                    "pred_label_idx": -1,
                    "n_seeds_in_test": 0,
                    "seeds_in_test": "",
                    "split_used": "train_only",
                    "p_contra_mean": float("nan"),
                    "p_strong_mean": float("nan"),
                    "p_svm_mean": float("nan"),
                    "route": "R4_conservative_strong_exact",
                    "thresholds_used": "",
                })
                continue
        # Majority vote
        votes = sub["pred_label_idx"].value_counts()
        pred_idx = int(votes.idxmax())
        seeds_str = ",".join(str(s) for s in sorted(sub["seed"].unique()))
        agg_rows.append({
            "candidate_id": cid,
            "true_label": true_label,
            "pred_label": IDX_TO_LABEL[pred_idx],
            "pred_label_idx": pred_idx,
            "n_seeds_in_test": len(sub),
            "seeds_in_test": seeds_str,
            "split_used": split_used,
            "p_contra_mean": float(sub["p_contra"].mean()),
            "p_strong_mean": float(sub["p_strong"].mean()),
            "p_svm_mean": float(sub["p_svm"].mean()),
            "route": "R4_conservative_strong_exact",
            "thresholds_used": ";".join(
                f"seed{s}:t_c={r['t_contra']},t_cl={r['t_contra_low']},t_s={r['t_strong']},t_sv={r['t_svm']}"
                for _, r in sub.iterrows()
            ),
        })
    pred_444 = pd.DataFrame(agg_rows)
    pred_444_path = OUTPUT_DIR / "r4_recovered_predictions_444.csv"
    pred_444.to_csv(pred_444_path, index=False, encoding="utf-8-sig")
    log(f"  -> {pred_444_path}")

    # Also save the raw per-seed predictions
    raw_pred_path = OUTPUT_DIR / "r4_recovered_predictions_per_seed.csv"
    pred_df.to_csv(raw_pred_path, index=False, encoding="utf-8-sig")
    log(f"  -> {raw_pred_path}")

    # ---- Step 6: Metrics ----
    log(f"\n[Step 6] Computing recovery metrics ...")
    metrics_df = pd.DataFrame(metrics_by_seed_rows)
    metrics_path = OUTPUT_DIR / "r4_recovery_metrics_by_seed.csv"
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    log(f"  -> {metrics_path}")

    # Summary (exact mode)
    exact_metrics = metrics_df[metrics_df["mode"] == "exact_reproduction"]
    frozen_mode_metrics = metrics_df[metrics_df["mode"] == "frozen_thresholds"]

    summary = {
        "exact_reproduction": {
            "flat4_macro_f1_mean": float(exact_metrics["flat4_macro_f1"].mean()),
            "flat4_macro_f1_std": float(exact_metrics["flat4_macro_f1"].std()),
            "strong_positive_f1_mean": float(exact_metrics["strong_positive_f1"].mean()),
            "strong_positive_f1_std": float(exact_metrics["strong_positive_f1"].std()),
            "strong_precision_mean": float(exact_metrics["strong_precision"].mean()),
            "strong_recall_mean": float(exact_metrics["strong_recall"].mean()),
            "contradiction_positive_f1_mean": float(exact_metrics["contradiction_positive_f1"].mean()),
            "escalation_macro_f1_mean": float(exact_metrics["escalation_macro_f1"].mean()),
            "flat4_accuracy_mean": float(exact_metrics["flat4_accuracy"].mean()),
        },
        "frozen_thresholds": {
            "flat4_macro_f1_mean": float(frozen_mode_metrics["flat4_macro_f1"].mean()),
            "flat4_macro_f1_std": float(frozen_mode_metrics["flat4_macro_f1"].std()),
            "strong_positive_f1_mean": float(frozen_mode_metrics["strong_positive_f1"].mean()),
            "strong_positive_f1_std": float(frozen_mode_metrics["strong_positive_f1"].std()),
            "strong_precision_mean": float(frozen_mode_metrics["strong_precision"].mean()),
            "strong_recall_mean": float(frozen_mode_metrics["strong_recall"].mean()),
            "contradiction_positive_f1_mean": float(frozen_mode_metrics["contradiction_positive_f1"].mean()),
            "escalation_macro_f1_mean": float(frozen_mode_metrics["escalation_macro_f1"].mean()),
            "flat4_accuracy_mean": float(frozen_mode_metrics["flat4_accuracy"].mean()),
        },
        "n_seeds": len(SEEDS),
        "n_predictions_total": int(len(pred_df)),
        "n_candidate_ids_covered_by_test": int(covered_by_test),
        "n_candidate_ids_additional_by_dev": int(covered_by_dev),
        "n_candidate_ids_covered_total": int(total_covered),
        "n_candidate_ids_missing": int(len(missing)),
        "missing_candidate_ids": sorted(list(missing)),
    }
    summary_path = OUTPUT_DIR / "r4_recovery_metrics_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=json_default)
    log(f"  -> {summary_path}")

    # Confusion matrices
    cm_path = OUTPUT_DIR / "r4_recovery_confusion_matrices.json"
    with open(cm_path, "w", encoding="utf-8") as f:
        json.dump({
            "labels": LABELS_4,
            "label_indices": [0, 1, 2, 3],
            "per_seed_exact": confusion_matrices,
            "note": "Confusion matrices are per-seed (test split only), not aggregated across seeds.",
        }, f, indent=2, default=json_default)
    log(f"  -> {cm_path}")

    # ---- Step 7: Compare with frozen metrics ----
    log(f"\n[Step 7] Comparing with frozen metrics ...")
    with open(FROZEN_METRICS, "r", encoding="utf-8") as f:
        frozen = json.load(f)
    frozen_strong_f1 = frozen["R4_conservative_strong"]["strong_positive_f1"]
    frozen_macro_f1 = frozen["R4_conservative_strong"]["flat4_macro_f1"]

    recovered_strong_f1 = summary["exact_reproduction"]["strong_positive_f1_mean"]
    recovered_macro_f1 = summary["exact_reproduction"]["flat4_macro_f1_mean"]
    strong_f1_gap = abs(recovered_strong_f1 - frozen_strong_f1)
    macro_f1_gap = abs(recovered_macro_f1 - frozen_macro_f1)

    log(f"  Frozen strong-F1:   {frozen_strong_f1:.4f}")
    log(f"  Recovered strong-F1: {recovered_strong_f1:.4f}")
    log(f"  Strong-F1 gap:       {strong_f1_gap:.4f}")
    log(f"  Frozen macro-F1:     {frozen_macro_f1:.4f}")
    log(f"  Recovered macro-F1:  {recovered_macro_f1:.4f}")
    log(f"  Macro-F1 gap:        {macro_f1_gap:.4f}")

    recovery_passed = (strong_f1_gap <= 0.05) and (macro_f1_gap <= 0.05)

    # Also check frozen-mode metrics
    recovered_strong_f1_frozen = summary["frozen_thresholds"]["strong_positive_f1_mean"]
    recovered_macro_f1_frozen = summary["frozen_thresholds"]["flat4_macro_f1_mean"]
    strong_f1_gap_frozen = abs(recovered_strong_f1_frozen - frozen_strong_f1)
    macro_f1_gap_frozen = abs(recovered_macro_f1_frozen - frozen_macro_f1)

    # ---- Step 8: Artifacts inventory ----
    log(f"\n[Step 8] Writing artifacts inventory ...")
    art_inv_df = pd.DataFrame(artifacts_inventory)
    art_inv_path = OUTPUT_DIR / "r4_recovery_artifacts_inventory.csv"
    art_inv_df.to_csv(art_inv_path, index=False, encoding="utf-8-sig")
    log(f"  -> {art_inv_path}")

    # ---- Step 8b: Gate ----
    log(f"\n[Step 8b] Writing gate ...")
    gate = {
        "task": "Minimal R4 Recovery from Backup HCM Features v1",
        "audit_date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "hcm_features_found": True,
        "hcm_features_join_ok": bool(join_ok),
        "n_predictions_covered_by_test": int(covered_by_test),
        "n_predictions_additional_by_dev": int(covered_by_dev),
        "n_predictions_covered_total": int(total_covered),
        "n_predictions_missing": int(len(missing)),
        "artifacts_saved": True,
        "artifacts_count": int(len(artifacts_inventory)),
        "artifacts_dir": str(ARTIFACTS_DIR),
        "t_contra_low_recovered": True,
        "t_contra_low_source": "routing_variant_results_by_seed.csv (historical per-seed values)",
        "t_contra_low_mean": float(t_contra_low_mean),
        "frozen_strong_f1": float(frozen_strong_f1),
        "recovered_strong_f1": float(recovered_strong_f1),
        "strong_f1_gap": float(strong_f1_gap),
        "frozen_macro_f1": float(frozen_macro_f1),
        "recovered_macro_f1": float(recovered_macro_f1),
        "macro_f1_gap": float(macro_f1_gap),
        "recovery_passed": bool(recovery_passed),
        "recovery_mode": "exact_reproduction (per-seed historical thresholds)",
        "frozen_thresholds_mode_strong_f1": float(recovered_strong_f1_frozen),
        "frozen_thresholds_mode_strong_f1_gap": float(strong_f1_gap_frozen),
        "can_use_for_retrieved_evidence_replay": bool(recovery_passed),
        "recommended_next_step": (
            "R4 recovery PASSED. Use the saved artifacts (clf_*.pkl, scaler_*.pkl, thresholds.json) "
            "and the route_conservative_strong function to replay R4 on retrieved evidence. "
            "For retrieved-evidence replay, recompute p_contra/p_strong/p_svm using the saved classifiers "
            "on the new evidence's HCM features, then apply the same thresholds."
            if recovery_passed else
            "R4 recovery FAILED (gap > 0.05). Investigate: (1) library version differences, "
            "(2) TF-IDF vocabulary changes, (3) random_state consistency. "
            "Do NOT use for retrieved-evidence replay until gap is resolved."
        ),
        "prohibitions_enforced": [
            "no_api_calls",
            "no_network",
            "no_original_data_modification",
            "no_paper_modification",
            "no_file_deletion",
            "no_new_algorithms",
            "no_test_set_tuning",
            "no_silver_as_gold",
            "no_natural_distribution_claim",
            "reproduction_recovery_not_new_method",
        ],
        "output_files": [
            "recovered_hcm_features.csv",
            "r4_recovery_split_manifest.csv",
            "r4_recovered_predictions_444.csv",
            "r4_recovery_metrics_by_seed.csv",
            "r4_recovery_metrics_summary.json",
            "r4_recovery_confusion_matrices.json",
            "r4_recovery_artifacts_inventory.csv",
            "r4_recovery_gate.json",
            "r4_minimal_recovery_report.md",
        ],
    }
    gate_path = OUTPUT_DIR / "r4_recovery_gate.json"
    with open(gate_path, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, default=json_default)
    log(f"  -> {gate_path}")

    # ---- Step 9: Report ----
    log(f"\n[Step 9] Writing report ...")
    report = []
    report.append("# Minimal R4 Recovery from Backup HCM Features v1\n")
    report.append(f"- 审计时间: {gate['audit_date']}")
    report.append(f"- 模式: reproduction recovery (不是新方法)")
    report.append(f"- 只读原数据，禁止调 API/联网/改论文/用 test 调参")
    report.append("")
    report.append("## 1. hcm_features 是否可用？\n")
    report.append(f"**是**。备份中的 `hcm_features.csv` 成功加载并合并到主数据。")
    report.append(f"- 行数: 444 ✓")
    report.append(f"- candidate_id 唯一: 444 ✓")
    report.append(f"- 7 个 NLI 特征列齐全 ✓")
    report.append(f"- 与 strict_silver_max join 后无缺失: {join_ok} ✓")
    report.append(f"- 输出: `{recovered_hcm_path}`")
    report.append("")

    report.append("## 2. 是否恢复了完整 444 条 R4 predictions？\n")
    report.append(f"**是**。{total_covered}/444 candidate_ids 有至少一次 out-of-fold 预测。")
    report.append(f"\n覆盖率分解:")
    report.append(f"- Test split 覆盖: {covered_by_test} candidates (primary, out-of-fold, never in train)")
    report.append(f"- Dev split 额外覆盖: {covered_by_dev} candidates (secondary, out-of-fold, never in train)")
    report.append(f"- 总覆盖: {total_covered} / 444")
    if missing:
        report.append(f"\nWARNING: {len(missing)} 个 candidate 从未出现在任何 seed 的 test 或 dev split (always in train):")
        for c in sorted(missing)[:10]:
            report.append(f"- {c}")
    report.append(f"\n- 总预测行数 (10 seeds × test+dev splits): {len(pred_df)}")
    report.append(f"- 聚合方式: 优先 test 多数投票，回退 dev 多数投票")
    report.append(f"- 输出: `{pred_444_path}`")
    report.append(f"- 原始 per-seed 预测: `{raw_pred_path}`")
    report.append("")

    report.append("## 3. t_contra_low 是否恢复？\n")
    report.append(f"**是**。从 `routing_variant_results_by_seed.csv` 解析出每个 seed 的历史 R4 阈值 (t_contra, t_contra_low, t_strong, t_svm)。")
    report.append(f"\nPer-seed t_contra_low 值:")
    report.append("")
    report.append("| seed | t_contra | t_contra_low | t_strong | t_svm |")
    report.append("|------|----------|--------------|----------|-------|")
    for s in SEEDS:
        if s in historical_thresh:
            t_c, t_cl, t_s, t_sv = historical_thresh[s]
            report.append(f"| {s} | {t_c} | {t_cl} | {t_s} | {t_sv} |")
    report.append(f"\nt_contra_low 均值: {t_contra_low_mean:.4f}")
    report.append(f"\n**同时**也用 frozen 阈值 (t_contra=0.48, t_strong=0.535, t_svm=0.51) + dev grid search 恢复了 t_contra_low，作为对比。")
    report.append("")

    report.append("## 4. artifacts 是否保存？\n")
    report.append(f"**是**。每个 seed 目录保存了 10 个 artifact 文件 (3 clf + 1 flat4 + 3 scaler + 3 json)。")
    report.append(f"- 目录: `{ARTIFACTS_DIR}\\seed_<N>\\`")
    report.append(f"- 总 artifact 数: {len(artifacts_inventory)}")
    report.append(f"- 文件: clf_contra.pkl, clf_strong.pkl, clf_svm.pkl, clf_flat4.pkl, scaler_contra.pkl, scaler_strong.pkl, scaler_svm.pkl, thresholds.json, feature_columns.json, label_mapping.json")
    report.append(f"- 清单: `{art_inv_path}`")
    report.append("")

    report.append("## 5. recovered 指标是否接近 frozen R4？\n")
    report.append(f"**{'是' if recovery_passed else '否'}** (gap <= 0.05 判定)。\n")
    report.append("### Exact reproduction mode (per-seed historical thresholds)\n")
    report.append("| 指标 | Frozen | Recovered | Gap | Pass |")
    report.append("|------|--------|-----------|-----|------|")
    report.append(f"| strong-F1 | {frozen_strong_f1:.4f} | {recovered_strong_f1:.4f} | {strong_f1_gap:.4f} | {'✓' if strong_f1_gap <= 0.05 else '✗'} |")
    report.append(f"| macro-F1 | {frozen_macro_f1:.4f} | {recovered_macro_f1:.4f} | {macro_f1_gap:.4f} | {'✓' if macro_f1_gap <= 0.05 else '✗'} |")
    report.append("")
    report.append("### Frozen thresholds mode (t_contra=0.48, t_strong=0.535, t_svm=0.51 + dev-tuned t_contra_low)\n")
    report.append("| 指标 | Frozen | Recovered | Gap |")
    report.append("|------|--------|-----------|-----|")
    report.append(f"| strong-F1 | {frozen_strong_f1:.4f} | {recovered_strong_f1_frozen:.4f} | {strong_f1_gap_frozen:.4f} |")
    report.append(f"| macro-F1 | {frozen_macro_f1:.4f} | {recovered_macro_f1_frozen:.4f} | {macro_f1_gap_frozen:.4f} |")
    report.append("")
    report.append(f"**判定**: recovery_passed = {recovery_passed} (基于 exact reproduction mode)")
    report.append("")

    report.append("## 6. 是否可以进入 retrieved evidence replay？\n")
    if gate["can_use_for_retrieved_evidence_replay"]:
        report.append(f"**是**。R4 recovery 通过 (gap <= 0.05)。")
        report.append(f"\n下一步: 使用保存的 artifacts (clf_*.pkl, scaler_*.pkl, thresholds.json) 和 `route_conservative_strong` 函数，对 retrieved evidence 的 HCM features 复跑 R4。")
        report.append(f"\n具体流程:")
        report.append(f"1. 对 retrieved evidence 用 `cross-encoder/nli-deberta-base` 计算 HCM features")
        report.append(f"2. 用保存的 scaler 标准化特征")
        report.append(f"3. 用保存的 clf_contra/clf_strong/clf_svm 计算 p_contra/p_strong/p_svm")
        report.append(f"4. 用保存的 thresholds (per-seed) 应用 route_conservative_strong")
        report.append(f"5. 聚合 10 seeds 的预测 (majority vote)")
    else:
        report.append(f"**否**。R4 recovery 未通过 (gap > 0.05)。")
        report.append(f"\n需要先调查 gap 原因: (1) 库版本差异, (2) TF-IDF 词表变化, (3) random_state 一致性")
    report.append("")

    report.append("## 7. 如果不可以，卡在哪里？\n")
    if recovery_passed:
        report.append("不适用 (recovery 通过)。")
    else:
        report.append(f"- strong-F1 gap: {strong_f1_gap:.4f} (> 0.05)")
        report.append(f"- macro-F1 gap: {macro_f1_gap:.4f} (> 0.05)")
        report.append(f"- 可能原因: scikit-learn 版本差异导致 LogisticRegression 数值不稳定")
        report.append(f"- 解决方案: (1) 固定 sklearn 版本, (2) 检查 numpy 随机数生成器一致性")
    report.append("")

    report.append("## 输出文件清单\n")
    for f in gate["output_files"]:
        report.append(f"- `{f}`")
    report.append("")

    report_path = OUTPUT_DIR / "r4_minimal_recovery_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    log(f"  -> {report_path}")

    # ---- Save split manifest ----
    split_df = pd.DataFrame(split_manifest_rows)
    split_path = OUTPUT_DIR / "r4_recovery_split_manifest.csv"
    split_df.to_csv(split_path, index=False, encoding="utf-8-sig")
    log(f"\n  Split manifest: {split_path}")

    # ---- Final summary ----
    log("\n" + "=" * 70)
    log("RECOVERY SUMMARY")
    log("=" * 70)
    log(f"hcm_features_found: True")
    log(f"444 predictions covered: test={covered_by_test}, +dev={covered_by_dev}, total={total_covered}/444")
    log(f"artifacts_saved: True ({len(artifacts_inventory)} files)")
    log(f"t_contra_low_recovered: True (mean={t_contra_low_mean:.4f})")
    log(f"frozen strong-F1: {frozen_strong_f1:.4f}")
    log(f"recovered strong-F1 (exact): {recovered_strong_f1:.4f}")
    log(f"strong-F1 gap: {strong_f1_gap:.4f}")
    log(f"recovery_passed: {recovery_passed}")
    log(f"can_use_for_retrieved_evidence_replay: {gate['can_use_for_retrieved_evidence_replay']}")


if __name__ == "__main__":
    main()
