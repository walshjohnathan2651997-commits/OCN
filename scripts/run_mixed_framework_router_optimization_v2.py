"""Task L: Mixed Framework v2 Threshold/Router Optimization.

Corrects Task K's metric issue: cannot use binary macro-F1 alone as strong_action
success criterion. Primary metrics are strong_action positive-F1 and flat4 per-label
strong F1. Uses dev-tuned routing thresholds, class-specific threshold moving, and
light calibration to judge whether mixed framework truly improves strong_action
positive-class recognition without harming contradiction/escalation.

8 tasks:
  1. Corrected metric definitions
  2. Reproduce Task K E1/E2/E3 with correct metrics
  3. Dev-tuned router threshold search (OBJ1/OBJ2/OBJ3)
  4. Routing variants (R1-R5)
  5. Strong expert ablation (A0-A6)
  6. Error transition analysis
  7. Dev-based selection rule
  8. Readiness gate
"""

from __future__ import annotations

import json
import math
import os
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
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
HCM_FEATURES_CSV = Path(r"D:\ocn\experiments\cese_ocn_hcm_v1\hcm_features.csv")

EXP_DIR = Path(r"D:\ocn\experiments\mixed_framework_router_optimization_v2")
EXP_DIR.mkdir(parents=True, exist_ok=True)

LOG_PATH = EXP_DIR / "run.log"
SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
N_BOOTSTRAP = 1000

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

# ---------------- Action escalation lexicons (from Task K) ----------------
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

def to_supported_vs_mild(label):
    if label == "supported": return 0
    if label == "mild_scope_overclaim": return 1
    return None


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
    """Compute all 7 metric types for a 4-class prediction."""
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


# ---------------- Build action gap features ----------------
def build_action_gap_features(df):
    log("Building action escalation gap features ...")
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
    log("  Built action gap features")


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


def route_strong_first(p_contra, p_strong, p_svm, t_contra, t_strong, t_svm, n):
    pred = np.empty(n, dtype=int)
    for i in range(n):
        if p_strong[i] >= t_strong:
            pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
        elif p_contra[i] >= t_contra:
            pred[i] = LABEL_TO_IDX["contradiction_candidate"]
        else:
            pred[i] = LABEL_TO_IDX["supported"] if p_svm[i] < t_svm else LABEL_TO_IDX["mild_scope_overclaim"]
    return pred


def route_margin(p_contra, p_strong, flat4_pred, margin, n):
    pred = np.empty(n, dtype=int)
    for i in range(n):
        if p_contra[i] - p_strong[i] >= margin:
            pred[i] = LABEL_TO_IDX["contradiction_candidate"]
        elif p_strong[i] - p_contra[i] >= margin:
            pred[i] = LABEL_TO_IDX["strong_action_overclaim"]
        else:
            pred[i] = flat4_pred[i]
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


# ---------------- Main ----------------
def main():
    log("=" * 70)
    log("Task L: Mixed Framework v2 Threshold/Router Optimization")
    log("=" * 70)

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
    df["y_svm"] = df["label_4"].apply(to_supported_vs_mild)

    group_ids = df["target_candidate_group_id"].values
    log(f"  Data: {len(df)} rows, {df['target_candidate_group_id'].nunique()} groups")

    # Expert features
    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    # Threshold grids
    T_CONTRA_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_STRONG_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_SVM_GRID = [0.4, 0.45, 0.5, 0.55, 0.6]
    MARGIN_GRID = [0.05, 0.1, 0.15, 0.2]

    # ================================================================
    # Task 2: Reproduce Task K E1/E2/E3 with correct metrics
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 2: Reproduce Task K E1/E2/E3 with corrected metrics")
    log("=" * 70)

    taskk_corrected_records = []

    for seed in SEEDS:
        log(f"  [Task2] Seed {seed}")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values
        y_esc = df["y_esc"].values
        y_contra = df["y_contra"].values

        # Train classifiers
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

        # flat4 NLI
        clf_flat4 = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42, multi_class="multinomial")
        clf_flat4.fit(Xtr_nli, y_4idx[train_mask])
        pred_flat4_test = clf_flat4.predict(Xte_nli)

        # contradiction detector
        clf_contra = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_contra.fit(Xtr_nli, y_contra[train_mask])
        p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]

        # strong expert
        clf_strong = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_strong.fit(Xtr_exp, y_strong[train_mask])
        p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]

        # supported_vs_mild
        y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else -1).values
        svm_train_mask = (y_svm_int >= 0) & train_mask
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]

        n_test = int(test_mask.sum())

        # Baseline flat4
        m_base = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_flat4_test)
        taskk_corrected_records.append({"method": "baseline_flat4", "seed": seed, **m_base})

        # E1: contra first (default thresholds 0.5)
        e1_pred = route_contra_first(p_contra_test, p_strong_test, p_svm_test, 0.5, 0.5, 0.5, n_test)
        m_e1 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], e1_pred)
        taskk_corrected_records.append({"method": "E1_contra_first", "seed": seed, **m_e1})

        # E2: strong first
        e2_pred = route_strong_first(p_contra_test, p_strong_test, p_svm_test, 0.5, 0.5, 0.5, n_test)
        m_e2 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], e2_pred)
        taskk_corrected_records.append({"method": "E2_strong_first", "seed": seed, **m_e2})

        # E3: soft voting
        prob_flat4 = clf_flat4.predict_proba(Xte_nli)
        gap_scores = df["action_escalation_gap"].astype(float).values
        gap_min, gap_max = gap_scores[train_mask].min(), gap_scores[train_mask].max()
        gap_norm = (gap_scores - gap_min) / (gap_max - gap_min) if gap_max > gap_min else np.zeros_like(gap_scores)
        gap_norm_test = gap_norm[test_mask]
        e3_pred = np.empty(n_test, dtype=int)
        for i in range(n_test):
            scores = np.zeros(4)
            for j in range(4):
                scores[j] = prob_flat4[i, j]
            scores[LABEL_TO_IDX["strong_action_overclaim"]] += 0.3 * p_strong_test[i] + 0.2 * gap_norm_test[i]
            scores[LABEL_TO_IDX["contradiction_candidate"]] += 0.2 * p_contra_test[i]
            e3_pred[i] = np.argmax(scores)
        m_e3 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], e3_pred)
        taskk_corrected_records.append({"method": "E3_soft_voting", "seed": seed, **m_e3})

    taskk_df = pd.DataFrame(taskk_corrected_records)
    taskk_df.to_csv(EXP_DIR / "taskK_corrected_metrics_by_seed.csv", index=False)
    log(f"  Saved taskK_corrected_metrics_by_seed.csv ({len(taskk_df)} rows)")

    taskk_summary = {}
    for method in taskk_df["method"].unique():
        sub = taskk_df[taskk_df["method"] == method]
        taskk_summary[method] = {}
        for col in ["flat4_macro_f1", "flat4_strong_f1", "strong_binary_macro_f1", "strong_positive_f1",
                     "strong_precision", "strong_recall", "escalation_macro_f1", "contradiction_macro_f1",
                     "contradiction_positive_f1", "escalation_positive_f1"]:
            if col in sub.columns:
                taskk_summary[method][col + "_mean"] = round(float(sub[col].mean()), 4)
                taskk_summary[method][col + "_std"] = round(float(sub[col].std()), 4)
    with open(EXP_DIR / "taskK_corrected_summary.json", "w", encoding="utf-8") as f:
        json.dump(taskk_summary, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved taskK_corrected_summary.json")

    # Print E1 vs baseline comparison
    base_strong_pf1 = taskk_df[taskk_df["method"] == "baseline_flat4"]["strong_positive_f1"].mean()
    e1_strong_pf1 = taskk_df[taskk_df["method"] == "E1_contra_first"]["strong_positive_f1"].mean()
    base_flat4_strong = taskk_df[taskk_df["method"] == "baseline_flat4"]["flat4_strong_f1"].mean()
    e1_flat4_strong = taskk_df[taskk_df["method"] == "E1_contra_first"]["flat4_strong_f1"].mean()
    base_binary_macro = taskk_df[taskk_df["method"] == "baseline_flat4"]["strong_binary_macro_f1"].mean()
    e1_binary_macro = taskk_df[taskk_df["method"] == "E1_contra_first"]["strong_binary_macro_f1"].mean()
    log(f"  [Task2] baseline strong_positive_f1={base_strong_pf1:.4f}, E1={e1_strong_pf1:.4f}, delta={e1_strong_pf1-base_strong_pf1:+.4f}")
    log(f"  [Task2] baseline flat4_strong_f1={base_flat4_strong:.4f}, E1={e1_flat4_strong:.4f}, delta={e1_flat4_strong-base_flat4_strong:+.4f}")
    log(f"  [Task2] baseline strong_binary_macro_f1={base_binary_macro:.4f}, E1={e1_binary_macro:.4f}, delta={e1_binary_macro-base_binary_macro:+.4f}")

    # ================================================================
    # Task 3: Dev-tuned Router Threshold Search
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 3: Dev-tuned Router Threshold Search (OBJ1/OBJ2/OBJ3)")
    log("=" * 70)

    threshold_search_records = []
    test_eval_records = []

    for seed in SEEDS:
        log(f"  [Task3] Seed {seed}")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values
        y_esc = df["y_esc"].values
        y_contra = df["y_contra"].values

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

        y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else -1).values
        svm_train_mask = (y_svm_int >= 0) & train_mask
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])

        # Dev probabilities
        p_contra_dev = clf_contra.predict_proba(Xdev_nli)[:, 1]
        p_strong_dev = clf_strong.predict_proba(Xdev_exp)[:, 1]
        p_svm_dev = clf_svm.predict_proba(Xdev_svm)[:, 1]
        # Test probabilities
        p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]
        p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]

        n_dev = int(dev_mask.sum())
        n_test = int(test_mask.sum())

        # Baseline (flat4 NLI only) on test
        pred_flat4_test = clf_flat4.predict(Xte_nli)
        m_base_test = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_flat4_test)
        test_eval_records.append({"method": "baseline_flat4", "seed": seed, **m_base_test})

        # Search thresholds on dev for each objective
        best_per_obj = {}
        for obj_name in ["OBJ1_flat4_macro", "OBJ2_strong_pf1_constrained", "OBJ3_weighted"]:
            best_score = -1
            best_thresh = (0.5, 0.5, 0.5)
            best_dev_metrics = None
            for t_c in T_CONTRA_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_contra_first(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        if obj_name == "OBJ1_flat4_macro":
                            score = m_dev["flat4_macro_f1"]
                        elif obj_name == "OBJ2_strong_pf1_constrained":
                            # constraint: contradiction positive-F1 not down more than 0.03 vs baseline dev
                            base_dev_pred = clf_flat4.predict(Xdev_nli)
                            m_base_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], base_dev_pred)
                            if m_dev["contradiction_positive_f1"] < m_base_dev["contradiction_positive_f1"] - 0.03:
                                continue
                            score = m_dev["strong_positive_f1"]
                        else:  # OBJ3
                            score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_s, t_sv)
                            best_dev_metrics = m_dev
            best_per_obj[obj_name] = (best_thresh, best_dev_metrics, best_score)
            log(f"    {obj_name}: best thresh={best_thresh}, dev_score={best_score:.4f}")

            # Record threshold search
            threshold_search_records.append({
                "seed": seed, "objective": obj_name,
                "t_contra": best_thresh[0], "t_strong": best_thresh[1], "t_svm": best_thresh[2],
                "dev_score": round(best_score, 4),
                "dev_flat4_macro": round(best_dev_metrics["flat4_macro_f1"], 4),
                "dev_strong_pf1": round(best_dev_metrics["strong_positive_f1"], 4),
                "dev_contra_pf1": round(best_dev_metrics["contradiction_positive_f1"], 4),
            })

            # Evaluate on test with selected thresholds
            t_c, t_s, t_sv = best_thresh
            pred_test = route_contra_first(p_contra_test, p_strong_test, p_svm_test, t_c, t_s, t_sv, n_test)
            m_test = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_test)
            test_eval_records.append({"method": f"R1_contra_first_{obj_name}", "seed": seed, **m_test})

    thresh_df = pd.DataFrame(threshold_search_records)
    thresh_df.to_csv(EXP_DIR / "router_threshold_search_by_seed.csv", index=False)
    log(f"  Saved router_threshold_search_by_seed.csv ({len(thresh_df)} rows)")

    thresh_summary = {}
    for obj in thresh_df["objective"].unique():
        sub = thresh_df[thresh_df["objective"] == obj]
        thresh_summary[obj] = {
            "t_contra_mean": round(float(sub["t_contra"].mean()), 4),
            "t_strong_mean": round(float(sub["t_strong"].mean()), 4),
            "t_svm_mean": round(float(sub["t_svm"].mean()), 4),
            "dev_score_mean": round(float(sub["dev_score"].mean()), 4),
        }
    with open(EXP_DIR / "router_threshold_summary.json", "w", encoding="utf-8") as f:
        json.dump(thresh_summary, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved router_threshold_summary.json")

    # ================================================================
    # Task 4: Routing Variants
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 4: Routing Variants (R1-R5)")
    log("=" * 70)

    routing_variant_records = []

    for seed in SEEDS:
        log(f"  [Task4] Seed {seed}")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values
        y_esc = df["y_esc"].values
        y_contra = df["y_contra"].values

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

        y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else -1).values
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

        # Baseline
        m_base = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_flat4_test)
        routing_variant_records.append({"method": "baseline_flat4", "seed": seed, **m_base})

        # R1 contra_first: use OBJ3 thresholds (weighted objective, best general)
        best_score = -1
        best_thresh = (0.5, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_s in T_STRONG_GRID:
                for t_sv in T_SVM_GRID:
                    pred_dev = route_contra_first(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_s, t_sv, n_dev)
                    m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                    score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                    if score > best_score:
                        best_score = score
                        best_thresh = (t_c, t_s, t_sv)
        t_c, t_s, t_sv = best_thresh
        pred_r1 = route_contra_first(p_contra_test, p_strong_test, p_svm_test, t_c, t_s, t_sv, n_test)
        m_r1 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r1)
        routing_variant_records.append({"method": "R1_contra_first", "seed": seed, "thresholds": str(best_thresh), **m_r1})

        # R2 strong_first: dev-tuned with OBJ3
        best_score = -1
        best_thresh = (0.5, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_s in T_STRONG_GRID:
                for t_sv in T_SVM_GRID:
                    pred_dev = route_strong_first(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_s, t_sv, n_dev)
                    m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                    score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                    if score > best_score:
                        best_score = score
                        best_thresh = (t_c, t_s, t_sv)
        t_c, t_s, t_sv = best_thresh
        pred_r2 = route_strong_first(p_contra_test, p_strong_test, p_svm_test, t_c, t_s, t_sv, n_test)
        m_r2 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r2)
        routing_variant_records.append({"method": "R2_strong_first", "seed": seed, "thresholds": str(best_thresh), **m_r2})

        # R3 margin_router: dev-tuned margin
        best_score = -1
        best_margin = 0.1
        for margin in MARGIN_GRID:
            pred_dev = route_margin(p_contra_dev, p_strong_dev, clf_flat4.predict(Xdev_nli), margin, n_dev)
            m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
            score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
            if score > best_score:
                best_score = score
                best_margin = margin
        pred_r3 = route_margin(p_contra_test, p_strong_test, pred_flat4_test, best_margin, n_test)
        m_r3 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r3)
        routing_variant_records.append({"method": "R3_margin_router", "seed": seed, "margin": best_margin, **m_r3})

        # R4 conservative_strong: dev-tuned (t_contra, t_contra_low, t_strong, t_svm)
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_cl in [0.2, 0.25, 0.3, 0.35, 0.4]:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)
        t_c, t_cl, t_s, t_sv = best_thresh
        pred_r4 = route_conservative_strong(p_contra_test, p_strong_test, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
        m_r4 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r4)
        routing_variant_records.append({"method": "R4_conservative_strong", "seed": seed, "thresholds": str(best_thresh), **m_r4})

        # R5 strong_recall_router: lower t_strong to maximize strong_positive_f1, constrain flat4_macro not down >0.02
        base_dev_pred = clf_flat4.predict(Xdev_nli)
        m_base_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], base_dev_pred)
        best_score = -1
        best_thresh = (0.5, 0.3, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_s in [0.2, 0.25, 0.3, 0.35, 0.4]:  # lower strong threshold
                for t_sv in T_SVM_GRID:
                    pred_dev = route_contra_first(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_s, t_sv, n_dev)
                    m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                    if m_dev["flat4_macro_f1"] < m_base_dev["flat4_macro_f1"] - 0.02:
                        continue
                    if m_dev["strong_positive_f1"] > best_score:
                        best_score = m_dev["strong_positive_f1"]
                        best_thresh = (t_c, t_s, t_sv)
        t_c, t_s, t_sv = best_thresh
        pred_r5 = route_contra_first(p_contra_test, p_strong_test, p_svm_test, t_c, t_s, t_sv, n_test)
        m_r5 = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_r5)
        routing_variant_records.append({"method": "R5_strong_recall_router", "seed": seed, "thresholds": str(best_thresh), **m_r5})

    rv_df = pd.DataFrame(routing_variant_records)
    rv_df.to_csv(EXP_DIR / "routing_variant_results_by_seed.csv", index=False)
    log(f"  Saved routing_variant_results_by_seed.csv ({len(rv_df)} rows)")

    rv_summary = {}
    for method in rv_df["method"].unique():
        sub = rv_df[rv_df["method"] == method]
        rv_summary[method] = {}
        for col in ["flat4_macro_f1", "flat4_strong_f1", "strong_positive_f1", "strong_precision", "strong_recall",
                     "escalation_macro_f1", "contradiction_positive_f1", "contradiction_macro_f1"]:
            if col in sub.columns:
                rv_summary[method][col + "_mean"] = round(float(sub[col].mean()), 4)
                rv_summary[method][col + "_std"] = round(float(sub[col].std()), 4)
    with open(EXP_DIR / "routing_variant_summary.json", "w", encoding="utf-8") as f:
        json.dump(rv_summary, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved routing_variant_summary.json")

    # ================================================================
    # Task 5: Strong Expert Ablation
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 5: Strong Expert Ablation (A0-A6)")
    log("=" * 70)

    ablation_records = []
    ablation_configs = {
        "A0_nli_only": NLI_FEATURES,
        "A1_action_gap_only": ["action_escalation_gap", "claim_action_strength", "evidence_action_support",
                                "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
                                "length_diff", "claim_evidence_overlap"],
        "A2_nli_plus_action_gap": NLI_FEATURES + ["action_escalation_gap", "claim_action_strength", "evidence_action_support",
                                "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
                                "length_diff", "claim_evidence_overlap"],
        "A3_nli_plus_length_overlap": NLI_FEATURES + ["length_diff", "claim_evidence_overlap", "claim_length", "evidence_length"],
        "A4_nli_plus_gap_no_length": NLI_FEATURES + ["action_escalation_gap", "claim_action_strength", "evidence_action_support",
                                "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
                                "claim_evidence_overlap"],
        "A5_nli_plus_gap_no_claim_strength": NLI_FEATURES + ["action_escalation_gap", "evidence_action_support",
                                "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
                                "length_diff", "claim_evidence_overlap"],
    }

    for seed in SEEDS:
        log(f"  [Task5] Seed {seed}")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values
        y_esc = df["y_esc"].values
        y_contra = df["y_contra"].values

        # A6: TF-IDF claim-only
        claim_text_all = df["claim_text"].astype(str).values
        tfidf = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
        Xtr_tfidf = tfidf.fit_transform(claim_text_all[train_mask])
        Xte_tfidf = tfidf.transform(claim_text_all[test_mask])
        clf_tfidf = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_tfidf.fit(Xtr_tfidf, y_strong[train_mask])
        pred_tfidf = clf_tfidf.predict(Xte_tfidf)
        prob_tfidf = clf_tfidf.predict_proba(Xte_tfidf)[:, 1]
        m_tfidf = binary_metrics_full(y_strong[test_mask], pred_tfidf)
        # For flat4 strong per-label, compose: if pred=1 -> strong, else use flat4 NLI
        scaler_nli = StandardScaler()
        Xtr_nli = scaler_nli.fit_transform(df.iloc[train_mask][NLI_FEATURES].values)
        Xte_nli = scaler_nli.transform(df.iloc[test_mask][NLI_FEATURES].values)
        clf_flat4 = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42, multi_class="multinomial")
        clf_flat4.fit(Xtr_nli, y_4idx[train_mask])
        pred_flat4_test = clf_flat4.predict(Xte_nli)
        composed_pred = pred_flat4_test.copy()
        composed_pred[pred_tfidf == 1] = LABEL_TO_IDX["strong_action_overclaim"]
        m_composed = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], composed_pred)
        ablation_records.append({
            "method": "A6_tfidf_claim_only", "seed": seed,
            "strong_positive_f1": m_tfidf["positive_f1"], "strong_macro_f1": m_tfidf["macro_f1"],
            "strong_precision": m_tfidf["precision"], "strong_recall": m_tfidf["recall"],
            "flat4_strong_f1": m_composed["flat4_strong_f1"],
        })

        for config_name, feats in ablation_configs.items():
            scaler = StandardScaler()
            Xtr = scaler.fit_transform(df.iloc[train_mask][feats].values)
            Xte = scaler.transform(df.iloc[test_mask][feats].values)
            clf = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
            clf.fit(Xtr, y_strong[train_mask])
            pred = clf.predict(Xte)
            prob = clf.predict_proba(Xte)[:, 1]
            m = binary_metrics_full(y_strong[test_mask], pred)
            # Compose with flat4
            composed = pred_flat4_test.copy()
            composed[pred == 1] = LABEL_TO_IDX["strong_action_overclaim"]
            m_comp = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], composed)
            ablation_records.append({
                "method": config_name, "seed": seed,
                "strong_positive_f1": m["positive_f1"], "strong_macro_f1": m["macro_f1"],
                "strong_precision": m["precision"], "strong_recall": m["recall"],
                "flat4_strong_f1": m_comp["flat4_strong_f1"],
            })

    abl_df = pd.DataFrame(ablation_records)
    abl_df.to_csv(EXP_DIR / "strong_expert_ablation_by_seed.csv", index=False)
    log(f"  Saved strong_expert_ablation_by_seed.csv ({len(abl_df)} rows)")

    abl_summary = {}
    for method in abl_df["method"].unique():
        sub = abl_df[abl_df["method"] == method]
        abl_summary[method] = {}
        for col in ["strong_positive_f1", "strong_macro_f1", "strong_precision", "strong_recall", "flat4_strong_f1"]:
            if col in sub.columns:
                abl_summary[method][col + "_mean"] = round(float(sub[col].mean()), 4)
                abl_summary[method][col + "_std"] = round(float(sub[col].std()), 4)
    with open(EXP_DIR / "strong_expert_ablation_summary.json", "w", encoding="utf-8") as f:
        json.dump(abl_summary, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved strong_expert_ablation_summary.json")

    # ================================================================
    # Task 6: Error Transition Analysis
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 6: Error Transition Analysis")
    log("=" * 70)

    # Find best routing method from Task 4 (by strong_positive_f1 mean)
    rv_means = rv_df.groupby("method").agg({
        "strong_positive_f1": "mean", "flat4_macro_f1": "mean", "contradiction_positive_f1": "mean"
    }).reset_index()
    rv_means = rv_means[rv_means["method"] != "baseline_flat4"]
    best_router_name = rv_means.sort_values("strong_positive_f1", ascending=False).iloc[0]["method"]
    log(f"  Best router by strong_positive_f1: {best_router_name}")

    # Compute error transitions: baseline vs best router
    transition_counts = {}
    strong_error_cases = []
    label_names = LABELS_4

    for seed in SEEDS:
        log(f"  [Task6] Seed {seed}")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        y_4idx = df["label_4_idx"].values
        y_strong = df["y_strong"].values

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

        y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and math.isnan(x)) else -1).values
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

        # Baseline predictions
        base_pred = pred_flat4_test
        # Best router predictions (re-run with dev-tuned thresholds, OBJ3)
        best_score = -1
        best_thresh = (0.5, 0.5, 0.5)
        for t_c in T_CONTRA_GRID:
            for t_s in T_STRONG_GRID:
                for t_sv in T_SVM_GRID:
                    pred_dev = route_contra_first(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_s, t_sv, n_dev)
                    m_dev = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                    score = 0.4 * m_dev["flat4_macro_f1"] + 0.3 * m_dev["strong_positive_f1"] + 0.2 * m_dev["contradiction_positive_f1"] + 0.1 * m_dev["escalation_macro_f1"]
                    if score > best_score:
                        best_score = score
                        best_thresh = (t_c, t_s, t_sv)
        t_c, t_s, t_sv = best_thresh
        best_pred = route_contra_first(p_contra_test, p_strong_test, p_svm_test, t_c, t_s, t_sv, n_test)

        y_true = y_4idx[test_mask]
        test_df = df.iloc[test_mask].copy()
        for i in range(n_test):
            true_lab = IDX_TO_LABEL[y_true[i]]
            base_lab = IDX_TO_LABEL[base_pred[i]]
            best_lab = IDX_TO_LABEL[best_pred[i]]
            key = f"{base_lab}_to_{best_lab}"
            transition_counts[key] = transition_counts.get(key, 0) + 1
            # Record strong action error cases
            if true_lab == "strong_action_overclaim" and best_lab != "strong_action_overclaim":
                strong_error_cases.append({
                    "seed": seed,
                    "candidate_id": test_df.iloc[i]["candidate_id"],
                    "true_label": true_lab,
                    "baseline_pred": base_lab,
                    "router_pred": best_lab,
                    "p_contra": round(float(p_contra_test[i]), 4),
                    "p_strong": round(float(p_strong_test[i]), 4),
                    "claim_text": str(test_df.iloc[i]["claim_text"])[:200],
                })

    trans_df = pd.DataFrame([
        {"transition": k, "count": v} for k, v in sorted(transition_counts.items())
    ])
    trans_df.to_csv(EXP_DIR / "error_transition_matrix.csv", index=False)
    log(f"  Saved error_transition_matrix.csv ({len(trans_df)} transitions)")

    err_cases_df = pd.DataFrame(strong_error_cases)
    err_cases_df.to_csv(EXP_DIR / "strong_action_error_cases_after_router.csv", index=False)
    log(f"  Saved strong_action_error_cases_after_router.csv ({len(err_cases_df)} cases)")

    # ================================================================
    # Task 7 & 8: Selection Rule + Readiness Gate
    # ================================================================
    log("\n" + "=" * 70)
    log("Task 7 & 8: Dev-based Selection Rule + Readiness Gate")
    log("=" * 70)

    # Method selection table (corrected)
    method_sel_records = []
    baseline_row = rv_df[rv_df["method"] == "baseline_flat4"]
    base_strong_pf1 = float(baseline_row["strong_positive_f1"].mean())
    base_flat4_macro = float(baseline_row["flat4_macro_f1"].mean())
    base_flat4_strong = float(baseline_row["flat4_strong_f1"].mean())
    base_contra_pf1 = float(baseline_row["contradiction_positive_f1"].mean())
    base_esc_macro = float(baseline_row["escalation_macro_f1"].mean())
    base_strong_recall = float(baseline_row["strong_recall"].mean())
    base_strong_precision = float(baseline_row["strong_precision"].mean())

    for method in rv_df["method"].unique():
        sub = rv_df[rv_df["method"] == method]
        strong_pf1 = float(sub["strong_positive_f1"].mean())
        flat4_macro = float(sub["flat4_macro_f1"].mean())
        flat4_strong = float(sub["flat4_strong_f1"].mean())
        contra_pf1 = float(sub["contradiction_positive_f1"].mean())
        esc_macro = float(sub["escalation_macro_f1"].mean())
        strong_recall = float(sub["strong_recall"].mean())
        strong_precision = float(sub["strong_precision"].mean())
        # positive delta seed count
        if method != "baseline_flat4":
            base_per_seed = baseline_row.set_index("seed")["strong_positive_f1"]
            method_per_seed = sub.set_index("seed")["strong_positive_f1"]
            common = sorted(set(base_per_seed.index) & set(method_per_seed.index))
            deltas = (method_per_seed.loc[common] - base_per_seed.loc[common]).values
            pos_count = int((deltas > 0).sum())
        else:
            pos_count = 10
        method_sel_records.append({
            "method": method,
            "strong_positive_f1": round(strong_pf1, 4),
            "strong_positive_delta": round(strong_pf1 - base_strong_pf1, 4),
            "flat4_macro_f1": round(flat4_macro, 4),
            "flat4_macro_delta": round(flat4_macro - base_flat4_macro, 4),
            "flat4_strong_f1": round(flat4_strong, 4),
            "contradiction_positive_f1": round(contra_pf1, 4),
            "contradiction_positive_delta": round(contra_pf1 - base_contra_pf1, 4),
            "escalation_macro_f1": round(esc_macro, 4),
            "escalation_macro_delta": round(esc_macro - base_esc_macro, 4),
            "strong_recall": round(strong_recall, 4),
            "strong_recall_delta": round(strong_recall - base_strong_recall, 4),
            "strong_precision": round(strong_precision, 4),
            "strong_precision_delta": round(strong_precision - base_strong_precision, 4),
            "positive_delta_seed_count": pos_count,
        })

    method_sel_df = pd.DataFrame(method_sel_records)
    method_sel_df = method_sel_df.sort_values("strong_positive_delta", ascending=False)
    method_sel_df.to_csv(EXP_DIR / "method_selection_corrected.csv", index=False)
    log(f"  Saved method_selection_corrected.csv")

    # Selection rule (dev-based, applied to test metrics)
    # 1. strong positive-F1 improve >= +0.05
    # 2. flat4 macro-F1 not down > 0.02
    # 3. contradiction positive-F1 not down > 0.03
    # 4. escalation macro-F1 not down > 0.03
    # 5. at least 7/10 seeds positive
    eligible = []
    for rec in method_sel_records:
        if rec["method"] == "baseline_flat4":
            continue
        if (rec["strong_positive_delta"] >= 0.05 and
            rec["flat4_macro_delta"] >= -0.02 and
            rec["contradiction_positive_delta"] >= -0.03 and
            rec["escalation_macro_delta"] >= -0.03 and
            rec["positive_delta_seed_count"] >= 7):
            eligible.append(rec)

    if eligible:
        best = max(eligible, key=lambda x: x["strong_positive_f1"])
        best_router = best["method"]
        best_obj = "OBJ3_weighted"
        mixed_ready = True
        recommended_use = "main_method"
        main_blocker = "none"
    else:
        # Find best by strong_positive_delta even if not eligible
        non_base = [r for r in method_sel_records if r["method"] != "baseline_flat4"]
        best = max(non_base, key=lambda x: x["strong_positive_delta"]) if non_base else None
        best_router = best["method"] if best else "none"
        best_obj = "OBJ3_weighted"
        mixed_ready = False
        # Determine blocker
        if best is None:
            main_blocker = "no methods evaluated"
            recommended_use = "reject"
        elif best["strong_positive_delta"] < 0.05:
            main_blocker = f"strong_positive_delta={best['strong_positive_delta']:.4f} below +0.05 threshold"
            recommended_use = "diagnostic_only"
        elif best["flat4_macro_delta"] < -0.02:
            main_blocker = f"flat4_macro_delta={best['flat4_macro_delta']:.4f} below -0.02"
            recommended_use = "auxiliary_module"
        elif best["contradiction_positive_delta"] < -0.03:
            main_blocker = f"contradiction_positive_delta={best['contradiction_positive_delta']:.4f} below -0.03"
            recommended_use = "auxiliary_module"
        elif best["escalation_macro_delta"] < -0.03:
            main_blocker = f"escalation_macro_delta={best['escalation_macro_delta']:.4f} below -0.03"
            recommended_use = "auxiliary_module"
        elif best["positive_delta_seed_count"] < 7:
            main_blocker = f"positive_delta_seed_count={best['positive_delta_seed_count']}/10 below 7"
            recommended_use = "diagnostic_only"
        else:
            main_blocker = "unknown"
            recommended_use = "diagnostic_only"

    # Selected thresholds mean (from Task 3)
    obj3_thresh = thresh_df[thresh_df["objective"] == "OBJ3_weighted"]
    selected_thresholds_mean = {
        "t_contra": round(float(obj3_thresh["t_contra"].mean()), 4) if len(obj3_thresh) > 0 else 0.5,
        "t_strong": round(float(obj3_thresh["t_strong"].mean()), 4) if len(obj3_thresh) > 0 else 0.5,
        "t_svm": round(float(obj3_thresh["t_svm"].mean()), 4) if len(obj3_thresh) > 0 else 0.5,
    }

    # Bootstrap CI on strong_positive_f1 delta
    if best is not None and best_router != "baseline_flat4":
        best_per_seed = rv_df[rv_df["method"] == best_router].set_index("seed")["strong_positive_f1"]
        base_per_seed = rv_df[rv_df["method"] == "baseline_flat4"].set_index("seed")["strong_positive_f1"]
        common = sorted(set(best_per_seed.index) & set(base_per_seed.index))
        deltas = (best_per_seed.loc[common] - base_per_seed.loc[common]).values
        rng = np.random.RandomState(42)
        n = len(deltas)
        boots = np.array([deltas[rng.randint(0, n, size=n)].mean() for _ in range(N_BOOTSTRAP)])
        ci_low, ci_high = np.percentile(boots, [2.5, 97.5])
        ci_crosses_zero = ci_low <= 0 <= ci_high
    else:
        ci_low, ci_high, ci_crosses_zero = 0.0, 0.0, True

    # Determine if improvement is real (positive-F1) vs binary macro only
    best_strong_pf1 = best["strong_positive_f1"] if best else 0
    best_flat4_strong = best["flat4_strong_f1"] if best else 0
    strong_pf1_delta = best_strong_pf1 - base_strong_pf1 if best else 0
    flat4_strong_delta = best_flat4_strong - base_flat4_strong if best else 0
    does_improve_real = strong_pf1_delta >= 0.05 and flat4_strong_delta > 0
    is_binary_macro_only = strong_pf1_delta < 0.05 and best is not None

    gate = {
        "generated_at": datetime.now().isoformat(),
        "mixed_framework_router_ready": bool(mixed_ready),
        "best_router": best_router,
        "best_objective": best_obj,
        "selected_thresholds_mean": selected_thresholds_mean,
        "baseline_strong_positive_f1": round(base_strong_pf1, 4),
        "best_strong_positive_f1": round(best_strong_pf1, 4),
        "strong_positive_delta": round(strong_pf1_delta, 4),
        "baseline_flat4_strong_per_label_f1": round(base_flat4_strong, 4),
        "best_flat4_strong_per_label_f1": round(best_flat4_strong, 4),
        "flat4_strong_per_label_delta": round(flat4_strong_delta, 4),
        "flat4_macro_delta": round(best["flat4_macro_delta"], 4) if best else 0,
        "contradiction_positive_delta": round(best["contradiction_positive_delta"], 4) if best else 0,
        "escalation_macro_delta": round(best["escalation_macro_delta"], 4) if best else 0,
        "positive_delta_seed_count": best["positive_delta_seed_count"] if best else 0,
        "strong_recall_delta": round(best["strong_recall_delta"], 4) if best else 0,
        "strong_precision_delta": round(best["strong_precision_delta"], 4) if best else 0,
        "delta_ci_lower": round(float(ci_low), 4),
        "delta_ci_upper": round(float(ci_high), 4),
        "delta_ci_crosses_zero": bool(ci_crosses_zero),
        "does_improve_real_strong_class": bool(does_improve_real),
        "is_binary_macro_only_gain": bool(is_binary_macro_only),
        "recommended_use": recommended_use,
        "main_blocker": main_blocker,
        "recommended_next_step": (
            "adopt as main method for strong_action; report in paper with positive-F1 as primary metric"
            if recommended_use == "main_method"
            else "use as auxiliary module; report as diagnostic; expand data for stable conclusion"
            if recommended_use == "auxiliary_module"
            else "use as diagnostic only; do not claim strong_action improvement in paper"
            if recommended_use == "diagnostic_only"
            else "do not use; method rejected"
        ),
        "selection_criteria": {
            "strong_positive_f1_improve_ge_0.05": bool(strong_pf1_delta >= 0.05),
            "flat4_macro_not_down_gt_0.02": bool(best["flat4_macro_delta"] >= -0.02) if best else False,
            "contradiction_positive_not_down_gt_0.03": bool(best["contradiction_positive_delta"] >= -0.03) if best else False,
            "escalation_macro_not_down_gt_0.03": bool(best["escalation_macro_delta"] >= -0.03) if best else False,
            "at_least_7_seeds_positive": bool(best["positive_delta_seed_count"] >= 7) if best else False,
            "all_criteria_met": bool(mixed_ready),
        },
        "taskk_correction": {
            "taskk_original_best_method": "M5_E1_contra_first",
            "taskk_original_metric": "strong_binary_macro_f1",
            "taskk_original_delta": 0.0995,
            "taskk_corrected_e1_strong_positive_f1": round(float(taskk_df[taskk_df["method"] == "E1_contra_first"]["strong_positive_f1"].mean()), 4),
            "taskk_corrected_e1_strong_positive_delta": round(float(taskk_df[taskk_df["method"] == "E1_contra_first"]["strong_positive_f1"].mean() - base_strong_pf1), 4),
            "taskk_corrected_e1_flat4_strong_f1": round(float(taskk_df[taskk_df["method"] == "E1_contra_first"]["flat4_strong_f1"].mean()), 4),
            "taskk_corrected_e1_flat4_strong_delta": round(float(taskk_df[taskk_df["method"] == "E1_contra_first"]["flat4_strong_f1"].mean() - base_flat4_strong), 4),
            "taskk_conclusion_needs_correction": bool(strong_pf1_delta < 0.05 or flat4_strong_delta <= 0),
        },
        "key_metrics_all_methods": {
            method: {
                "strong_positive_f1": rec["strong_positive_f1"],
                "strong_positive_delta": rec["strong_positive_delta"],
                "flat4_strong_f1": rec["flat4_strong_f1"],
                "flat4_macro_f1": rec["flat4_macro_f1"],
                "strong_recall": rec["strong_recall"],
                "strong_precision": rec["strong_precision"],
            }
            for method, rec in zip([r["method"] for r in method_sel_records], method_sel_records)
        },
    }
    with open(EXP_DIR / "mixed_framework_router_readiness_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False, default=str)
    log(f"  Saved mixed_framework_router_readiness_gate.json")
    log(f"  Recommended use: {recommended_use}")
    log(f"  Main blocker: {main_blocker}")

    # ---------------- Final summary ----------------
    log("\n" + "=" * 70)
    log("ALL DONE")
    log("=" * 70)

    print("\n" + "=" * 70)
    print("FINAL SUMMARY (Task L)")
    print("=" * 70)
    print(f"Best router: {best_router}")
    print(f"Strong positive-F1: {base_strong_pf1:.4f} -> {best_strong_pf1:.4f} (delta={strong_pf1_delta:+.4f})")
    print(f"Flat4 strong per-label F1: {base_flat4_strong:.4f} -> {best_flat4_strong:.4f} (delta={flat4_strong_delta:+.4f})")
    print(f"Flat4 macro delta: {best['flat4_macro_delta']:+.4f}" if best else "N/A")
    print(f"Contradiction positive delta: {best['contradiction_positive_delta']:+.4f}" if best else "N/A")
    print(f"Escalation macro delta: {best['escalation_macro_delta']:+.4f}" if best else "N/A")
    print(f"Strong recall delta: {best['strong_recall_delta']:+.4f}" if best else "N/A")
    print(f"Strong precision delta: {best['strong_precision_delta']:+.4f}" if best else "N/A")
    print(f"Positive seeds: {best['positive_delta_seed_count']}/10" if best else "N/A")
    print(f"CI: [{ci_low:+.4f}, {ci_high:+.4f}], crosses 0: {ci_crosses_zero}")
    print(f"Does improve real strong class: {does_improve_real}")
    print(f"Is binary macro only gain: {is_binary_macro_only}")
    print(f"Recommended use: {recommended_use}")
    print(f"Main blocker: {main_blocker}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
        sys.exit(1)
