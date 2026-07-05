"""Task M: Freeze R4 Baseline + Explore New Algorithms Safely.

Phase 2: Test 6 new algorithms (A-F) against frozen R4 baseline.
All algorithms use dev-tuned thresholds; test evaluated once.
R4 remains main baseline unless a new algorithm beats it on all criteria.

Algorithms:
  A. Calibrated Router (temperature/isotonic/platt scaling)
  B. Cost-Sensitive Strong Expert (class_weight sweep)
  C. Ordinal Severity Router (regression + threshold)
  D. One-vs-Rest Ensemble (4 binary + priority)
  E. Error-Corrector on R4 (correction model)
  F. Conservative Recall Balance Router (R4 + FP penalty)
"""

from __future__ import annotations

import json
import math
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.isotonic import IsotonicRegression
from sklearn.linear_model import LogisticRegression, Ridge
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_score,
    recall_score,
)
from sklearn.preprocessing import StandardScaler

# ---------------- Paths ----------------
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
HCM_FEATURES_CSV = Path(r"D:\ocn\experiments\cese_ocn_hcm_v1\hcm_features.csv")
FROZEN_R4_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")

EXP_DIR = Path(r"D:\ocn\experiments\mixed_framework_new_algorithm_sweep_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = EXP_DIR / "run.log"
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
N_BOOTSTRAP = 1000

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}
SEVERITY_MAP = {"supported": 0, "mild_scope_overclaim": 1, "strong_action_overclaim": 2, "contradiction_candidate": 3}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

# Action gap lexicons
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


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_terms(text: str, terms: list) -> int:
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


# ---------------- Label mapping ----------------
def to_strong_action_binary(label):
    return 1 if label == "strong_action_overclaim" else 0

def to_escalation_binary(label):
    return 0 if label == "supported" else 1

def to_contradiction_binary(label):
    return 1 if label == "contradiction_candidate" else 0


# ---------------- Split ----------------
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


# ---------------- Metrics ----------------
def compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx):
    pred_4idx = np.asarray(pred_4idx)
    m_flat4_macro = float(f1_score(y_4idx, pred_4idx, average="macro", zero_division=0))
    per_label = {}
    for lab in [0, 1, 2, 3]:
        per_label[IDX_TO_LABEL[lab]] = float(f1_score(y_4idx, pred_4idx, labels=[lab], average="macro", zero_division=0))
    pred_strong = (pred_4idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    pred_esc = (pred_4idx != LABEL_TO_IDX["supported"]).astype(int)
    pred_contra = (pred_4idx == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    # supported→strong and mild→strong false positive rates
    sup_mask = (y_4idx == LABEL_TO_IDX["supported"])
    mild_mask = (y_4idx == LABEL_TO_IDX["mild_scope_overclaim"])
    sup_to_strong = float((pred_strong[sup_mask] == 1).mean()) if sup_mask.sum() > 0 else 0.0
    mild_to_strong = float((pred_strong[mild_mask] == 1).mean()) if mild_mask.sum() > 0 else 0.0
    return {
        "flat4_macro_f1": m_flat4_macro,
        "flat4_strong_f1": per_label["strong_action_overclaim"],
        "flat4_supported_f1": per_label["supported"],
        "flat4_mild_f1": per_label["mild_scope_overclaim"],
        "flat4_contradiction_f1": per_label["contradiction_candidate"],
        "strong_positive_f1": float(f1_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_precision": float(precision_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_recall": float(recall_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "escalation_macro_f1": float(f1_score(y_esc, pred_esc, average="macro", zero_division=0)),
        "escalation_positive_f1": float(f1_score(y_esc, pred_esc, pos_label=1, zero_division=0)),
        "contradiction_macro_f1": float(f1_score(y_contra, pred_contra, average="macro", zero_division=0)),
        "contradiction_positive_f1": float(f1_score(y_contra, pred_contra, pos_label=1, zero_division=0)),
        "supported_to_strong_rate": sup_to_strong,
        "mild_to_strong_rate": mild_to_strong,
    }


# ---------------- Build action gap features ----------------
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


# ---------------- Routing functions ----------------
def route_contra_first(p_contra, p_strong, p_svm, t_contra, t_strong, t_svm, n):
    pred = np.empty(n, dtype=int)
    for i in range(n):
        if p_contra[i] >= t_contra:
            pred[i] = LABEL_TO_IDX["contradiction_candidate"]
        elif p_strong[i] >= t_strong:
            pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
        else:
            pred[i] = LABEL_TO_IDX["supported"] if p_svm[i] < t_svm else LABEL_TO_IDX["mild_scope_overclaim"]
    return pred


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


# ---------------- Calibration ----------------
def temperature_scale(p, y, T_grid=[0.5, 0.75, 1.0, 1.5, 2.0, 3.0]):
    """Temperature scaling: p_calibrated = sigmoid(logit(p) / T)."""
    best_T = 1.0
    best_score = -1
    for T in T_grid:
        logits = np.log(np.clip(p, 1e-7, 1 - 1e-7) / (1 - np.clip(p, 1e-7, 1 - 1e-7)))
        p_cal = 1 / (1 + np.exp(-logits / T))
        # Score by how well calibrated (use F1 of threshold 0.5)
        pred = (p_cal >= 0.5).astype(int)
        score = f1_score(y, pred, pos_label=1, zero_division=0)
        if score > best_score:
            best_score = score
            best_T = T
    logits = np.log(np.clip(p, 1e-7, 1 - 1e-7) / (1 - np.clip(p, 1e-7, 1 - 1e-7)))
    return 1 / (1 + np.exp(-logits / best_T)), best_T


def isotonic_calibrate(p_train, y_train, p_apply):
    """Isotonic regression calibration."""
    iso = IsotonicRegression(out_of_bounds="clip", y_min=0, y_max=1)
    iso.fit(p_train, y_train)
    return iso.predict(p_apply)


def platt_calibrate(p_train, y_train, p_apply):
    """Platt scaling: logistic regression on probability."""
    lr = LogisticRegression(max_iter=1000, random_state=42)
    lr.fit(p_train.reshape(-1, 1), y_train)
    return lr.predict_proba(p_apply.reshape(-1, 1))[:, 1]


# ---------------- Main ----------------
def main():
    log("=" * 70)
    log("Task M: New Algorithm Sweep v1 (vs Frozen R4)")
    log("=" * 70)

    # ---------------- Load R4 frozen metrics ----------------
    with open(FROZEN_R4_DIR / "frozen_r4_manifest.json", "r", encoding="utf-8") as f:
        r4_manifest = json.load(f)
    r4_metrics = r4_manifest["key_metrics"]
    log(f"  R4 frozen: strong_positive_f1={r4_metrics['r4_strong_positive_f1']}, flat4_macro={r4_metrics['r4_flat4_macro_f1']}")

    # ---------------- Load data ----------------
    log("Loading data ...")
    df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    hcm = pd.read_csv(HCM_FEATURES_CSV, keep_default_na=False)
    df = df.merge(
        hcm[["candidate_id"] + NLI_FEATURES + ["s_correct", "s_wrong", "margin"]],
        on="candidate_id", how="left"
    )
    build_action_gap_features(df)

    df["label_4"] = df["candidate_label_guess"].astype(str)
    df["label_4_idx"] = df["label_4"].map(LABEL_TO_IDX)
    df["y_strong"] = df["label_4"].apply(to_strong_action_binary)
    df["y_esc"] = df["label_4"].apply(to_escalation_binary)
    df["y_contra"] = df["label_4"].apply(to_contradiction_binary)
    df["severity"] = df["label_4"].map(SEVERITY_MAP)

    group_ids = df["target_candidate_group_id"].values
    log(f"  Data: {len(df)} rows, {df['target_candidate_group_id'].nunique()} groups")

    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    T_CONTRA_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_STRONG_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_SVM_GRID = [0.4, 0.45, 0.5, 0.55, 0.6]
    T_CONTRA_LOW_GRID = [0.2, 0.25, 0.3, 0.35, 0.4]

    all_results = []

    for seed in SEEDS:
        log(f"\n--- Seed {seed} ---")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values
        y_esc = df["y_esc"].values
        y_contra = df["y_contra"].values
        y_sev = df["severity"].values

        # Train base classifiers
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

        clf_flat4 = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42, multi_class="multinomial")
        clf_flat4.fit(Xtr_nli, y_4idx[train_mask])
        clf_contra = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_contra.fit(Xtr_nli, y_contra[train_mask])
        clf_strong = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_strong.fit(Xtr_exp, y_strong[train_mask])

        y_svm_int = df["y_svm"].apply(lambda x: 0 if x == "supported" else (1 if x == "mild_scope_overclaim" else -1)).values if "y_svm" in df.columns else df["label_4"].apply(lambda x: 0 if x == "supported" else (1 if x == "mild_scope_overclaim" else -1)).values
        svm_train_mask = (y_svm_int >= 0) & train_mask
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])

        p_contra_dev = clf_contra.predict_proba(Xdev_nli)[:, 1]
        p_strong_dev = clf_strong.predict_proba(Xdev_exp)[:, 1]
        p_svm_dev = clf_svm.predict_proba(Xdev_svm)[:, 1]
        p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]
        p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]
        pred_flat4_test = clf_flat4.predict(Xte_nli)

        n_dev = int(dev_mask.sum())
        n_test = int(test_mask.sum())

        # ---- R4 baseline (reproduce for this seed) ----
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        r4_thresh = (t_c, t_cl, t_s, t_sv)
        pred_r4 = route_conservative_strong(p_contra_test, p_strong_test, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_r4 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r4)
        all_results.append({"method": "R4_conservative_strong", "seed": seed, **m_r4})
        log(f"  R4: strong_pf1={m_r4['strong_positive_f1']:.4f}, flat4={m_r4['flat4_macro_f1']:.4f}")

        # ============ Algorithm A: Calibrated Router ============
        # A1: Temperature scaling on strong expert
        p_strong_dev_cal, best_T = temperature_scale(p_strong_dev, y_strong[dev_mask])
        logits_test = np.log(np.clip(p_strong_test, 1e-7, 1 - 1e-7) / (1 - np.clip(p_strong_test, 1e-7, 1 - 1e-7)))
        p_strong_test_cal = 1 / (1 + np.exp(-logits_test / best_T))
        # Dev-tune thresholds on calibrated
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev_cal, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        pred_a1 = route_conservative_strong(p_contra_test, p_strong_test_cal, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_a1 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_a1)
        all_results.append({"method": "A1_temp_scaled_router", "seed": seed, **m_a1})

        # A2: Isotonic calibration on strong expert
        p_strong_train = clf_strong.predict_proba(Xtr_exp)[:, 1]
        p_strong_dev_iso = isotonic_calibrate(p_strong_train, y_strong[train_mask], p_strong_dev)
        p_strong_test_iso = isotonic_calibrate(p_strong_train, y_strong[train_mask], p_strong_test)
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev_iso, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        pred_a2 = route_conservative_strong(p_contra_test, p_strong_test_iso, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_a2 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_a2)
        all_results.append({"method": "A2_isotonic_router", "seed": seed, **m_a2})

        # A3: Platt scaling on strong expert
        p_strong_dev_platt = platt_calibrate(p_strong_train, y_strong[train_mask], p_strong_dev)
        p_strong_test_platt = platt_calibrate(p_strong_train, y_strong[train_mask], p_strong_test)
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev_platt, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        pred_a3 = route_conservative_strong(p_contra_test, p_strong_test_platt, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_a3 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_a3)
        all_results.append({"method": "A3_platt_router", "seed": seed, **m_a3})

        # ============ Algorithm B: Cost-Sensitive Strong Expert ============
        for cw in [1.5, 2.0, 3.0, 4.0]:
            clf_strong_cs = LogisticRegression(class_weight={0: 1, 1: cw}, max_iter=3000, random_state=42)
            clf_strong_cs.fit(Xtr_exp, y_strong[train_mask])
            p_strong_dev_cs = clf_strong_cs.predict_proba(Xdev_exp)[:, 1]
            p_strong_test_cs = clf_strong_cs.predict_proba(Xte_exp)[:, 1]
            best_score = -1
            best_thresh = (0.5, 0.3, 0.5, 0.5)
            for t_c in T_CONTRA_GRID:
                for t_cl in T_CONTRA_LOW_GRID:
                    for t_s in T_STRONG_GRID:
                        for t_sv in T_SVM_GRID:
                            pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev_cs, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                            m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                            score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                            if score > best_score:
                                best_score = score
                                best_thresh = (t_c, t_cl, t_s, t_sv)
            t_c, t_cl, t_s, t_sv = best_thresh
            pred_b = route_conservative_strong(p_contra_test, p_strong_test_cs, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
            m_b = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_b)
            all_results.append({"method": f"B_cost_sensitive_cw{cw}", "seed": seed, **m_b})

        # ============ Algorithm C: Ordinal Severity Router ============
        clf_sev = Ridge(alpha=1.0, random_state=42)
        clf_sev.fit(Xtr_nli, y_sev[train_mask])
        sev_dev = clf_sev.predict(Xdev_nli)
        sev_test = clf_sev.predict(Xte_nli)
        # Dev-tune severity thresholds: t0 (supported/mild), t1 (mild/strong), t2 (strong/contra)
        best_score = -1
        best_sev_thresh = (0.5, 1.5, 2.5)
        for t0 in [0.3, 0.4, 0.5, 0.6, 0.7]:
            for t1 in [1.0, 1.2, 1.4, 1.5, 1.6, 1.8]:
                for t2 in [2.0, 2.2, 2.4, 2.5, 2.6, 2.8]:
                    pred_dev = np.empty(n_dev, dtype=int)
                    for i in range(n_dev):
                        if sev_dev[i] < t0:
                            pred_dev[i] = 0
                        elif sev_dev[i] < t1:
                            pred_dev[i] = 1
                        elif sev_dev[i] < t2:
                            pred_dev[i] = 2
                        else:
                            pred_dev[i] = 3
                    m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                    score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                    if score > best_score:
                        best_score = score
                        best_sev_thresh = (t0, t1, t2)
        t0, t1, t2 = best_sev_thresh
        pred_c = np.empty(n_test, dtype=int)
        for i in range(n_test):
            if sev_test[i] < t0:
                pred_c[i] = 0
            elif sev_test[i] < t1:
                pred_c[i] = 1
            elif sev_test[i] < t2:
                pred_c[i] = 2
            else:
                pred_c[i] = 3
        m_c = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_c)
        all_results.append({"method": "C_ordinal_severity", "seed": seed, **m_c})

        # ============ Algorithm D: One-vs-Rest Ensemble ============
        clf_sup = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_sup.fit(Xtr_nli, (y_4idx[train_mask] == 0).astype(int))
        clf_mild = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_mild.fit(Xtr_nli, (y_4idx[train_mask] == 1).astype(int))
        clf_strong_ovr = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_strong_ovr.fit(Xtr_nli, (y_4idx[train_mask] == 2).astype(int))
        clf_contra_ovr = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_contra_ovr.fit(Xtr_nli, (y_4idx[train_mask] == 3).astype(int))

        p_sup_dev = clf_sup.predict_proba(Xdev_nli)[:, 1]
        p_mild_dev = clf_mild.predict_proba(Xdev_nli)[:, 1]
        p_strong_ovr_dev = clf_strong_ovr.predict_proba(Xdev_nli)[:, 1]
        p_contra_ovr_dev = clf_contra_ovr.predict_proba(Xdev_nli)[:, 1]
        p_sup_test = clf_sup.predict_proba(Xte_nli)[:, 1]
        p_mild_test = clf_mild.predict_proba(Xte_nli)[:, 1]
        p_strong_ovr_test = clf_strong_ovr.predict_proba(Xte_nli)[:, 1]
        p_contra_ovr_test = clf_contra_ovr.predict_proba(Xte_nli)[:, 1]

        # D1: priority contra > strong > mild > supported
        best_score = -1
        best_thresh = (0.5, 0.5, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_s in T_STRONG_GRID:
                for t_m in [0.4, 0.45, 0.5, 0.55, 0.6]:
                    for t_su in [0.4, 0.45, 0.5, 0.55, 0.6]:
                        pred_dev = np.empty(n_dev, dtype=int)
                        for i in range(n_dev):
                            if p_contra_ovr_dev[i] >= t_c:
                                pred_dev[i] = 3
                            elif p_strong_ovr_dev[i] >= t_s:
                                pred_dev[i] = 2
                            elif p_mild_dev[i] >= t_m:
                                pred_dev[i] = 1
                            else:
                                pred_dev[i] = 0
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_s, t_m, t_su)
        t_c, t_s, t_m, t_su = best_thresh
        pred_d1 = np.empty(n_test, dtype=int)
        for i in range(n_test):
            if p_contra_ovr_test[i] >= t_c:
                pred_d1[i] = 3
            elif p_strong_ovr_test[i] >= t_s:
                pred_d1[i] = 2
            elif p_mild_test[i] >= t_m:
                pred_d1[i] = 1
            else:
                pred_d1[i] = 0
        m_d1 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_d1)
        all_results.append({"method": "D1_ovr_contra_priority", "seed": seed, **m_d1})

        # D2: priority strong > contra > mild > supported
        best_score = -1
        best_thresh = (0.5, 0.5, 0.5, 0.5)
        for t_s in T_STRONG_GRID:
            for t_c in T_CONTRA_GRID:
                for t_m in [0.4, 0.45, 0.5, 0.55, 0.6]:
                    for t_su in [0.4, 0.45, 0.5, 0.55, 0.6]:
                        pred_dev = np.empty(n_dev, dtype=int)
                        for i in range(n_dev):
                            if p_strong_ovr_dev[i] >= t_s:
                                pred_dev[i] = 2
                            elif p_contra_ovr_dev[i] >= t_c:
                                pred_dev[i] = 3
                            elif p_mild_dev[i] >= t_m:
                                pred_dev[i] = 1
                            else:
                                pred_dev[i] = 0
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_s, t_c, t_m, t_su)
        t_s, t_c, t_m, t_su = best_thresh
        pred_d2 = np.empty(n_test, dtype=int)
        for i in range(n_test):
            if p_strong_ovr_test[i] >= t_s:
                pred_d2[i] = 2
            elif p_contra_ovr_test[i] >= t_c:
                pred_d2[i] = 3
            elif p_mild_test[i] >= t_m:
                pred_d2[i] = 1
            else:
                pred_d2[i] = 0
        m_d2 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_d2)
        all_results.append({"method": "D2_ovr_strong_priority", "seed": seed, **m_d2})

        # D3: max calibrated probability
        probs_dev = np.column_stack([p_sup_dev, p_mild_dev, p_strong_ovr_dev, p_contra_ovr_dev])
        probs_test = np.column_stack([p_sup_test, p_mild_test, p_strong_ovr_test, p_contra_ovr_test])
        pred_d3 = np.argmax(probs_test, axis=1)
        m_d3 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_d3)
        all_results.append({"method": "D3_ovr_max_prob", "seed": seed, **m_d3})

        # ============ Algorithm E: Error-Corrector on R4 ============
        # Get R4 predictions on dev using saved R4 thresholds
        t_c_r4, t_cl_r4, t_s_r4, t_sv_r4 = r4_thresh
        pred_r4_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c_r4, t_cl_r4, t_s_r4, t_sv_r4, n_dev)
        # Identify errors: focus on supported→strong and mild→strong false positives
        # Train a correction model: predict whether R4's strong prediction is correct
        r4_strong_dev = (pred_r4_dev == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
        r4_strong_test = (pred_r4 == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
        # Among samples R4 predicts as strong, which are actually strong?
        strong_pred_mask_dev = r4_strong_dev == 1
        if strong_pred_mask_dev.sum() > 5:
            # Train correction: is R4's strong prediction correct?
            y_correct = (y_strong[dev_mask][strong_pred_mask_dev] == 1).astype(int)
            X_correct_dev = np.column_stack([
                p_contra_dev[strong_pred_mask_dev],
                p_strong_dev[strong_pred_mask_dev],
                p_svm_dev[strong_pred_mask_dev],
            ])
            clf_correct = LogisticRegression(class_weight="balanced", max_iter=1000, random_state=42)
            clf_correct.fit(X_correct_dev, y_correct)
            # Apply on test: among R4 strong predictions, decide if correct
            strong_pred_mask_test = r4_strong_test == 1
            if strong_pred_mask_test.sum() > 0:
                X_correct_test = np.column_stack([
                    p_contra_test[strong_pred_mask_test],
                    p_strong_test[strong_pred_mask_test],
                    p_svm_test[strong_pred_mask_test],
                ])
                correct_pred = clf_correct.predict(X_correct_test)
                # Flip incorrect strong predictions to supported/mild
                pred_e = pred_r4.copy()
                flip_indices = np.where(strong_pred_mask_test)[0][correct_pred == 0]
                for idx in flip_indices:
                    pred_e[idx] = LABEL_TO_IDX["supported"] if p_svm_test[idx] < 0.5 else LABEL_TO_IDX["mild_scope_overclaim"]
                m_e = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_e)
            else:
                m_e = m_r4.copy()
        else:
            m_e = m_r4.copy()
        all_results.append({"method": "E_error_corrector_r4", "seed": seed, **m_e})

        # ============ Algorithm F: Conservative Recall Balance Router ============
        # R4 with FP penalty: add penalty for supported→strong and mild→strong
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = (0.4 * m_dev["strong_positive_f1"] + 0.3 * m_dev["flat4_macro_f1"]
                                 + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                                 - 0.15 * m_dev["supported_to_strong_rate"]
                                 - 0.1 * m_dev["mild_to_strong_rate"])
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        pred_f = route_conservative_strong(p_contra_test, p_strong_test, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_f = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_f)
        all_results.append({"method": "F_recall_balance_router", "seed": seed, **m_f})

    # ---------------- Save results ----------------
    log("\nSaving results ...")
    results_df = pd.DataFrame(all_results)
    results_df.to_csv(EXP_DIR / "new_algorithm_results_by_seed.csv", index=False)
    log(f"  Saved new_algorithm_results_by_seed.csv ({len(results_df)} rows)")

    # Summary
    summary = {}
    for method in results_df["method"].unique():
        sub = results_df[results_df["method"] == method]
        summary[method] = {}
        for col in ["strong_positive_f1", "flat4_macro_f1", "flat4_strong_f1", "strong_precision", "strong_recall",
                     "escalation_macro_f1", "contradiction_positive_f1", "supported_to_strong_rate", "mild_to_strong_rate"]:
            if col in sub.columns:
                summary[method][col + "_mean"] = round(float(sub[col].mean()), 4)
                summary[method][col + "_std"] = round(float(sub[col].std()), 4)
    with open(EXP_DIR / "new_algorithm_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved new_algorithm_summary.json")

    # Ablation (subset of results for specific algorithm comparisons)
    abl_df = results_df[results_df["method"].str.startswith(("A", "B", "C", "D", "E", "F"))].copy()
    abl_df.to_csv(EXP_DIR / "new_algorithm_ablation.csv", index=False)
    log(f"  Saved new_algorithm_ablation.csv ({len(abl_df)} rows)")

    # Method selection
    r4_row = results_df[results_df["method"] == "R4_conservative_strong"]
    r4_strong_pf1 = float(r4_row["strong_positive_f1"].mean())
    r4_flat4_macro = float(r4_row["flat4_macro_f1"].mean())
    r4_contra_pf1 = float(r4_row["contradiction_positive_f1"].mean())
    r4_esc_macro = float(r4_row["escalation_macro_f1"].mean())
    r4_sup_to_strong = float(r4_row["supported_to_strong_rate"].mean())
    r4_mild_to_strong = float(r4_row["mild_to_strong_rate"].mean())

    method_sel = []
    for method in results_df["method"].unique():
        if method == "R4_conservative_strong":
            continue
        sub = results_df[results_df["method"] == method]
        strong_pf1 = float(sub["strong_positive_f1"].mean())
        flat4_macro = float(sub["flat4_macro_f1"].mean())
        contra_pf1 = float(sub["contradiction_positive_f1"].mean())
        esc_macro = float(sub["escalation_macro_f1"].mean())
        sup_to_strong = float(sub["supported_to_strong_rate"].mean())
        mild_to_strong = float(sub["mild_to_strong_rate"].mean())
        strong_recall = float(sub["strong_recall"].mean())
        strong_precision = float(sub["strong_precision"].mean())
        # positive delta seed count
        r4_per_seed = r4_row.set_index("seed")["strong_positive_f1"]
        method_per_seed = sub.set_index("seed")["strong_positive_f1"]
        common = sorted(set(r4_per_seed.index) & set(method_per_seed.index))
        deltas = (method_per_seed.loc[common] - r4_per_seed.loc[common]).values
        pos_count = int((deltas > 0).sum())
        # Bootstrap CI
        rng = np.random.RandomState(42)
        n = len(deltas)
        if n > 0:
            boots = np.array([deltas[rng.randint(0, n, size=n)].mean() for _ in range(N_BOOTSTRAP)])
            ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
        else:
            ci_low, ci_high = 0.0, 0.0
        method_sel.append({
            "method": method,
            "strong_positive_f1": round(strong_pf1, 4),
            "delta_vs_r4_strong": round(strong_pf1 - r4_strong_pf1, 4),
            "flat4_macro_f1": round(flat4_macro, 4),
            "delta_vs_r4_flat4": round(flat4_macro - r4_flat4_macro, 4),
            "contradiction_positive_f1": round(contra_pf1, 4),
            "delta_vs_r4_contra": round(contra_pf1 - r4_contra_pf1, 4),
            "escalation_macro_f1": round(esc_macro, 4),
            "delta_vs_r4_escalation": round(esc_macro - r4_esc_macro, 4),
            "strong_precision": round(strong_precision, 4),
            "strong_recall": round(strong_recall, 4),
            "supported_to_strong_rate": round(sup_to_strong, 4),
            "mild_to_strong_rate": round(mild_to_strong, 4),
            "positive_delta_seed_count": pos_count,
            "ci_lower": round(float(ci_low), 4),
            "ci_upper": round(float(ci_high), 4),
        })
    method_sel_df = pd.DataFrame(method_sel)
    method_sel_df = method_sel_df.sort_values("delta_vs_r4_strong", ascending=False)
    method_sel_df.to_csv(EXP_DIR / "new_algorithm_method_selection.csv", index=False)
    log(f"  Saved new_algorithm_method_selection.csv")

    # vs R4 table
    vs_r4_records = []
    for rec in method_sel:
        # Determine recommended_use
        replace = (rec["delta_vs_r4_strong"] >= 0.03 and
                   rec["delta_vs_r4_flat4"] >= -0.01 and
                   rec["delta_vs_r4_contra"] >= -0.02 and
                   rec["delta_vs_r4_escalation"] >= -0.02 and
                   rec["positive_delta_seed_count"] >= 7 and
                   rec["ci_lower"] > 0 and
                   rec["supported_to_strong_rate"] <= r4_sup_to_strong + 0.05 and
                   rec["mild_to_strong_rate"] <= r4_mild_to_strong + 0.05)
        if replace:
            rec_use = "replace_r4"
        elif rec["delta_vs_r4_strong"] > 0:
            rec_use = "auxiliary_module"
        elif rec["delta_vs_r4_strong"] > -0.03:
            rec_use = "diagnostic_only"
        else:
            rec_use = "reject"
        vs_r4_records.append({**rec, "recommended_use": rec_use})
    vs_r4_df = pd.DataFrame(vs_r4_records)
    vs_r4_df.to_csv(EXP_DIR / "new_algorithm_vs_r4_table.csv", index=False)
    log(f"  Saved new_algorithm_vs_r4_table.csv")

    # ---------------- Readiness gate ----------------
    log("\nReadiness gate ...")
    eligible = [r for r in vs_r4_records if r["recommended_use"] == "replace_r4"]
    if eligible:
        best_new = max(eligible, key=lambda x: x["strong_positive_f1"])
        replace_r4 = True
        recommended_use = "replace_r4"
        main_blocker = "none"
    else:
        # Find best by delta even if not eligible
        non_r4 = [r for r in vs_r4_records if r["delta_vs_r4_strong"] != 0 or True]
        best_new = max(non_r4, key=lambda x: x["strong_positive_f1"]) if non_r4 else None
        replace_r4 = False
        recommended_use = "auxiliary_module" if best_new and best_new["delta_vs_r4_strong"] > 0 else "diagnostic_only"
        if best_new is None:
            main_blocker = "no methods evaluated"
        elif best_new["delta_vs_r4_strong"] < 0.03:
            main_blocker = f"strong_positive_delta={best_new['delta_vs_r4_strong']:.4f} below +0.03 vs R4"
        elif best_new["delta_vs_r4_flat4"] < -0.01:
            main_blocker = f"flat4_macro_delta={best_new['delta_vs_r4_flat4']:.4f} below -0.01 vs R4"
        elif best_new["delta_vs_r4_contra"] < -0.02:
            main_blocker = f"contradiction_delta={best_new['delta_vs_r4_contra']:.4f} below -0.02 vs R4"
        elif best_new["delta_vs_r4_escalation"] < -0.02:
            main_blocker = f"escalation_delta={best_new['delta_vs_r4_escalation']:.4f} below -0.02 vs R4"
        elif best_new["positive_delta_seed_count"] < 7:
            main_blocker = f"positive_delta_seed_count={best_new['positive_delta_seed_count']}/10 below 7"
        elif best_new["ci_lower"] <= 0:
            main_blocker = f"CI [{best_new['ci_lower']:.4f}, {best_new['ci_upper']:.4f}] crosses 0"
        else:
            main_blocker = "false positive rate too high"

    gate = {
        "generated_at": datetime.now().isoformat(),
        "r4_frozen": True,
        "frozen_r4_path": str(FROZEN_R4_DIR),
        "best_new_method": best_new["method"] if best_new else "none",
        "best_new_strong_positive_f1": round(best_new["strong_positive_f1"], 4) if best_new else 0,
        "r4_strong_positive_f1": round(r4_strong_pf1, 4),
        "delta_vs_r4": round(best_new["delta_vs_r4_strong"], 4) if best_new else 0,
        "flat4_macro_delta_vs_r4": round(best_new["delta_vs_r4_flat4"], 4) if best_new else 0,
        "contradiction_delta_vs_r4": round(best_new["delta_vs_r4_contra"], 4) if best_new else 0,
        "escalation_delta_vs_r4": round(best_new["delta_vs_r4_escalation"], 4) if best_new else 0,
        "positive_delta_seed_count": best_new["positive_delta_seed_count"] if best_new else 0,
        "ci_crosses_zero": bool(best_new["ci_lower"] <= 0) if best_new else True,
        "false_positive_risk_vs_r4": {
            "r4_supported_to_strong": round(r4_sup_to_strong, 4),
            "best_new_supported_to_strong": round(best_new["supported_to_strong_rate"], 4) if best_new else 0,
            "r4_mild_to_strong": round(r4_mild_to_strong, 4),
            "best_new_mild_to_strong": round(best_new["mild_to_strong_rate"], 4) if best_new else 0,
        },
        "replace_r4": bool(replace_r4),
        "recommended_use": recommended_use,
        "main_blocker": main_blocker,
        "recommended_next_step": (
            "replace R4 with new method; update frozen baseline"
            if replace_r4
            else "keep R4 as main baseline; use new method as auxiliary if delta > 0"
            if recommended_use == "auxiliary_module"
            else "keep R4 as main baseline; new method is diagnostic only"
            if recommended_use == "diagnostic_only"
            else "keep R4; new method rejected"
        ),
        "all_methods_ranked": [
            {"method": r["method"], "strong_positive_f1": r["strong_positive_f1"], "delta_vs_r4": r["delta_vs_r4_strong"], "recommended_use": r["recommended_use"]}
            for r in sorted(vs_r4_records, key=lambda x: x["strong_positive_f1"], reverse=True)
        ],
    }
    with open(EXP_DIR / "new_algorithm_readiness_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved new_algorithm_readiness_gate.json")
    log(f"  replace_r4: {replace_r4}, recommended_use: {recommended_use}")

    # ---------------- Final summary ----------------
    log("\n" + "=" * 70)
    log("ALL DONE")
    log("=" * 70)

    print("\n" + "=" * 70)
    print("FINAL SUMMARY (Task M)")
    print("=" * 70)
    print(f"R4 frozen at: {FROZEN_R4_DIR}")
    print(f"R4 strong_positive_f1: {r4_strong_pf1:.4f}")
    if best_new:
        print(f"Best new method: {best_new['method']}")
        print(f"Best new strong_positive_f1: {best_new['strong_positive_f1']:.4f} (delta={best_new['delta_vs_r4_strong']:+.4f})")
        print(f"Flat4 delta: {best_new['delta_vs_r4_flat4']:+.4f}")
        print(f"Contradiction delta: {best_new['delta_vs_r4_contra']:+.4f}")
        print(f"Escalation delta: {best_new['delta_vs_r4_escalation']:+.4f}")
        print(f"Positive seeds: {best_new['positive_delta_seed_count']}/10")
        print(f"CI: [{best_new['ci_lower']:+.4f}, {best_new['ci_upper']:+.4f}]")
        print(f"sup→strong: R4={r4_sup_to_strong:.4f}, new={best_new['supported_to_strong_rate']:.4f}")
        print(f"mild→strong: R4={r4_mild_to_strong:.4f}, new={best_new['mild_to_strong_rate']:.4f}")
    print(f"Replace R4: {replace_r4}")
    print(f"Recommended use: {recommended_use}")
    print(f"Main blocker: {main_blocker}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
        sys.exit(1)
