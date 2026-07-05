"""
Task P - Strong Baselines + External/Holdout Validation for V3 R4.

Runs 6 strong baselines (B1-B6) vs frozen R4 (B0) on 10 seeds with group-aware
70/15/15 split. Then runs 4 holdout validations: leave-one-domain-out,
leave-one-source-out, source-pair holdout, and domain robustness table.

No new data, no LLM, no large model training, no CSV mutation.
All thresholds dev-tuned only; test evaluated once.
"""

from __future__ import annotations

import json
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
HCM_FEATURES_CSV = Path(r"D:\ocn\experiments\cese_ocn_hcm_v1\hcm_features.csv")
FROZEN_R4_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")
FROZEN_ENCODER_DIR = Path(r"D:\ocn\experiments\evidence_aware_frozen_encoder_v1")
NEW_ALGO_DIR = Path(r"D:\ocn\experiments\mixed_framework_new_algorithm_sweep_v1")

EXP_DIR = Path(r"D:\ocn\experiments\v3_r4_strong_baselines_holdout_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = EXP_DIR / "run.log"
LOG_PATH.write_text("", encoding="utf-8")

SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
N_BOOTSTRAP = 1000

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}

NLI_FEATURES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]

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

EXPERT_FEATURES = NLI_FEATURES + [
    "action_escalation_gap", "claim_action_strength", "evidence_action_support",
    "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
    "length_diff", "claim_evidence_overlap",
]
SVM_FEATURES = NLI_FEATURES + ["scope_gap"]


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def count_terms(text: str, terms: list) -> int:
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


# ---------------------------------------------------------------------------
# Feature building (identical to Task L)
# ---------------------------------------------------------------------------
def build_action_gap_features(df: pd.DataFrame) -> None:
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


# ---------------------------------------------------------------------------
# Splits
# ---------------------------------------------------------------------------
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


def group_aware_split_from_subset(group_ids, seed, train_frac=0.85, dev_frac=0.15):
    """Split a subset of groups into train/dev (no test). For holdout inner splits."""
    rng = np.random.RandomState(seed)
    unique_groups = np.array(sorted(set(group_ids.tolist())))
    rng.shuffle(unique_groups)
    n = len(unique_groups)
    n_train = int(round(n * train_frac))
    n_dev = n - n_train
    train_g = unique_groups[:n_train]
    dev_g = unique_groups[n_train:]
    train_mask = np.isin(group_ids, train_g)
    dev_mask = np.isin(group_ids, dev_g)
    return train_mask, dev_mask


# ---------------------------------------------------------------------------
# Metrics (identical to Task L)
# ---------------------------------------------------------------------------
def compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx):
    m_flat4_macro = float(f1_score(y_4idx, pred_4idx, average="macro", zero_division=0))
    per_label = {}
    for lab in [0, 1, 2, 3]:
        per_label[IDX_TO_LABEL[lab]] = float(f1_score(y_4idx, pred_4idx, labels=[lab], average="macro", zero_division=0))
    pred_strong = (pred_4idx == LABEL_TO_IDX["strong_action_overclaim"]).astype(int)
    pred_esc = (pred_4idx != LABEL_TO_IDX["supported"]).astype(int)
    pred_contra = (pred_4idx == LABEL_TO_IDX["contradiction_candidate"]).astype(int)
    return {
        "flat4_macro_f1": m_flat4_macro,
        "flat4_supported_f1": per_label["supported"],
        "flat4_mild_f1": per_label["mild_scope_overclaim"],
        "flat4_strong_f1": per_label["strong_action_overclaim"],
        "flat4_contradiction_f1": per_label["contradiction_candidate"],
        "strong_positive_f1": float(f1_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_precision": float(precision_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "strong_recall": float(recall_score(y_strong, pred_strong, pos_label=1, zero_division=0)),
        "escalation_macro_f1": float(f1_score(y_esc, pred_esc, average="macro", zero_division=0)),
        "contradiction_positive_f1": float(f1_score(y_contra, pred_contra, pos_label=1, zero_division=0)),
    }


# ---------------------------------------------------------------------------
# R4 reproduction (conservative-strong router)
# ---------------------------------------------------------------------------
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


def train_r4_and_predict(df, train_mask, dev_mask, test_mask, tune_on_dev=True):
    """Train R4's 3 models on train, tune thresholds on dev, predict on test.
    Matches Task L exactly: class_weight=balanced, NLI for contra, expert for strong.
    Returns (pred_test, metrics_test, thresholds)."""
    feature_cols_nli = [c for c in NLI_FEATURES if c in df.columns]
    feature_cols_expert = [c for c in EXPERT_FEATURES if c in df.columns]
    feature_cols_svm = [c for c in SVM_FEATURES if c in df.columns]

    y_4idx = df["label_4_idx"].values
    y_strong = df["y_strong"].values
    y_esc = df["y_esc"].values
    y_contra = df["y_contra"].values

    # NLI scaler (for contra detector + flat4)
    scaler_nli = StandardScaler()
    Xtr_nli = scaler_nli.fit_transform(df.iloc[train_mask][feature_cols_nli].values)
    Xdev_nli = scaler_nli.transform(df.iloc[dev_mask][feature_cols_nli].values)
    Xte_nli = scaler_nli.transform(df.iloc[test_mask][feature_cols_nli].values)

    # Expert scaler (for strong classifier)
    scaler_exp = StandardScaler()
    Xtr_exp = scaler_exp.fit_transform(df.iloc[train_mask][feature_cols_expert].values)
    Xdev_exp = scaler_exp.transform(df.iloc[dev_mask][feature_cols_expert].values)
    Xte_exp = scaler_exp.transform(df.iloc[test_mask][feature_cols_expert].values)

    # SVM scaler (for supported-vs-mild)
    scaler_svm = StandardScaler()
    Xtr_svm = scaler_svm.fit_transform(df.iloc[train_mask][feature_cols_svm].values)
    Xdev_svm = scaler_svm.transform(df.iloc[dev_mask][feature_cols_svm].values)
    Xte_svm = scaler_svm.transform(df.iloc[test_mask][feature_cols_svm].values)

    # Train 3 models (class_weight=balanced, matching Task L)
    clf_contra = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
    clf_contra.fit(Xtr_nli, y_contra[train_mask])
    clf_strong = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
    clf_strong.fit(Xtr_exp, y_strong[train_mask])

    # SVM: supported vs mild (filter to supported/mild only)
    y_svm_int = df["y_svm"].apply(lambda x: int(x) if x is not None and not (isinstance(x, float) and np.isnan(x)) else -1).values
    svm_train_mask = (y_svm_int >= 0) & train_mask
    if svm_train_mask.sum() > 0 and len(np.unique(y_svm_int[svm_train_mask])) > 1:
        clf_svm = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42)
        clf_svm.fit(Xtr_svm[svm_train_mask[train_mask]], y_svm_int[svm_train_mask])
        p_svm_dev = clf_svm.predict_proba(Xdev_svm)[:, 1]
        p_svm_test = clf_svm.predict_proba(Xte_svm)[:, 1]
    else:
        p_svm_dev = np.zeros(int(dev_mask.sum()))
        p_svm_test = np.zeros(int(test_mask.sum()))

    p_contra_dev = clf_contra.predict_proba(Xdev_nli)[:, 1]
    p_strong_dev = clf_strong.predict_proba(Xdev_exp)[:, 1]
    p_contra_test = clf_contra.predict_proba(Xte_nli)[:, 1]
    p_strong_test = clf_strong.predict_proba(Xte_exp)[:, 1]

    # Dev-tune thresholds (OBJ3 weighted)
    T_CONTRA_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_STRONG_GRID = [0.3, 0.35, 0.4, 0.45, 0.5, 0.55, 0.6, 0.65, 0.7]
    T_SVM_GRID = [0.4, 0.45, 0.5, 0.55, 0.6]
    T_CONTRA_LOW_GRID = [0.2, 0.25, 0.3, 0.35, 0.4]

    n_dev = int(dev_mask.sum())
    n_test = int(test_mask.sum())

    best_score = -1.0
    best_thresh = (0.5, 0.3, 0.5, 0.5)
    if tune_on_dev and n_dev > 0:
        for t_c in T_CONTRA_GRID:
            for t_cl in T_CONTRA_LOW_GRID:
                for t_s in T_STRONG_GRID:
                    for t_sv in T_SVM_GRID:
                        pred_dev = route_conservative_strong(p_contra_dev, p_strong_dev, p_svm_dev, t_c, t_cl, t_s, t_sv, n_dev)
                        m = compute_all_metrics(y_4idx[dev_mask], y_strong[dev_mask], y_esc[dev_mask], y_contra[dev_mask], pred_dev)
                        score = 0.4 * m["flat4_macro_f1"] + 0.3 * m["strong_positive_f1"] + 0.2 * m["contradiction_positive_f1"] + 0.1 * m["escalation_macro_f1"]
                        if score > best_score:
                            best_score = score
                            best_thresh = (t_c, t_cl, t_s, t_sv)

    t_c, t_cl, t_s, t_sv = best_thresh
    pred_test = route_conservative_strong(p_contra_test, p_strong_test, p_svm_test, t_c, t_cl, t_s, t_sv, n_test)
    metrics = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_test)
    return pred_test, metrics, best_thresh


# ---------------------------------------------------------------------------
# Flat4 baseline training
# ---------------------------------------------------------------------------
def train_flat4_baseline(df, feature_cols, train_mask, dev_mask, test_mask, use_tfidf=False, text_col=None):
    """Train a flat4 LR classifier (class_weight=balanced for fair comparison)."""
    y_4idx = df["label_4_idx"].values
    y_strong = df["y_strong"].values
    y_esc = df["y_esc"].values
    y_contra = df["y_contra"].values
    if use_tfidf:
        train_text = df.loc[train_mask, text_col].astype(str).values
        test_text = df.loc[test_mask, text_col].astype(str).values
        vec = TfidfVectorizer(max_features=3000, ngram_range=(1, 2), min_df=2, stop_words="english")
        X_train = vec.fit_transform(train_text)
        X_test = vec.transform(test_text)
        clf = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42, multi_class="multinomial")
        clf.fit(X_train, y_4idx[train_mask])
        pred_test = clf.predict(X_test)
    else:
        X_train = df.loc[train_mask, feature_cols].values
        X_test = df.loc[test_mask, feature_cols].values
        scaler = StandardScaler()
        X_train_s = scaler.fit_transform(X_train)
        X_test_s = scaler.transform(X_test)
        clf = LogisticRegression(class_weight="balanced", max_iter=3000, random_state=42, multi_class="multinomial")
        clf.fit(X_train_s, y_4idx[train_mask])
        pred_test = clf.predict(X_test_s)

    metrics = compute_all_metrics(y_4idx[test_mask], y_strong[test_mask], y_esc[test_mask], y_contra[test_mask], pred_test)
    return pred_test, metrics


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------
def bootstrap_ci(deltas, n_boot=N_BOOTSTRAP, ci=0.95):
    deltas = np.array(deltas, dtype=float)
    if len(deltas) < 2:
        return float(np.mean(deltas)) if len(deltas) == 1 else 0.0, 0.0, 0.0
    rng = np.random.RandomState(42)
    boot_means = np.array([np.mean(rng.choice(deltas, size=len(deltas), replace=True)) for _ in range(n_boot)])
    alpha = (1 - ci) / 2
    lo = float(np.percentile(boot_means, alpha * 100))
    hi = float(np.percentile(boot_means, (1 - alpha) * 100))
    return float(np.mean(deltas)), lo, hi


# ---------------------------------------------------------------------------
# MAIN
# ---------------------------------------------------------------------------
def main():
    log("=" * 70)
    log("Task P: Strong Baselines + External/Holdout Validation for V3 R4")
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
    df["y_strong"] = df["label_4"].apply(lambda x: 1 if x == "strong_action_overclaim" else 0)
    df["y_esc"] = df["label_4"].apply(lambda x: 0 if x == "supported" else 1)
    df["y_contra"] = df["label_4"].apply(lambda x: 1 if x == "contradiction_candidate" else 0)
    df["y_svm"] = df["label_4"].apply(lambda x: 0 if x == "supported" else (1 if x == "mild_scope_overclaim" else -1))

    group_ids = df["target_candidate_group_id"].values
    domain_ids = df["domain"].values
    source_ids = df["source_id"].values
    log(f"  Data: {len(df)} rows, {df['target_candidate_group_id'].nunique()} groups, {df['domain'].nunique()} domains, {df['source_id'].nunique()} sources")

    # ---------------- B0: Frozen R4 ----------------
    log("\n--- B0: Frozen R4 (read metrics) ---")
    frozen_manifest = json.load(open(FROZEN_R4_DIR / "frozen_r4_manifest.json", encoding="utf-8"))
    frozen_metrics = json.load(open(FROZEN_R4_DIR / "frozen_r4_metrics_summary.json", encoding="utf-8"))
    km = frozen_manifest["key_metrics"]
    r4_metrics = {
        "flat4_macro_f1": km["r4_flat4_macro_f1"],
        "strong_positive_f1": km["r4_strong_positive_f1"],
        "contradiction_positive_f1": km["r4_contradiction_positive_f1"],
        "escalation_macro_f1": km["r4_escalation_macro_f1"],
        "strong_precision": km["r4_strong_precision"],
        "strong_recall": km["r4_strong_recall"],
    }
    log(f"  R4 strong_positive_f1={r4_metrics['strong_positive_f1']}, flat4_macro_f1={r4_metrics['flat4_macro_f1']}")

    # ---------------- B6: Cost-sensitive cw4.0 (from Task M) ----------------
    log("\n--- B6: Cost-sensitive cw4.0 (read from Task M) ---")
    new_algo_summary = json.load(open(NEW_ALGO_DIR / "new_algorithm_summary.json", encoding="utf-8"))
    b6_metrics = new_algo_summary.get("B_cost_sensitive_cw4.0", {})
    log(f"  B6 strong_positive_f1={b6_metrics.get('strong_positive_f1_mean')}")

    # ================================================================
    # Part 1: Strong baselines on random splits (B1-B3)
    # ================================================================
    log("\n" + "=" * 70)
    log("Part 1: Strong Baselines on Random Splits (10 seeds, group-aware 70/15/15)")
    log("=" * 70)

    baseline_records = []
    r4_repro_records = []

    for seed in SEEDS:
        log(f"  Seed {seed} ...")
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)

        # R4 reproduction (for per-seed comparison and CI)
        _, r4_m, _ = train_r4_and_predict(df, train_mask, dev_mask, test_mask)
        r4_repro_records.append({"seed": seed, "method": "R4_conservative_strong", **r4_m})

        # B1: NLI-only flat4
        _, b1_m = train_flat4_baseline(df, NLI_FEATURES, train_mask, dev_mask, test_mask)
        baseline_records.append({"seed": seed, "method": "B1_nli_only_flat4", **b1_m})

        # B2: NLI + Action Gap flat4
        _, b2_m = train_flat4_baseline(df, EXPERT_FEATURES, train_mask, dev_mask, test_mask)
        baseline_records.append({"seed": seed, "method": "B2_nli_plus_action_gap_flat4", **b2_m})

        # B3a: TF-IDF claim-only
        _, b3a_m = train_flat4_baseline(df, None, train_mask, dev_mask, test_mask, use_tfidf=True, text_col="claim_text")
        baseline_records.append({"seed": seed, "method": "B3a_tfidf_claim_only", **b3a_m})

        # B3b: TF-IDF claim+evidence
        df_temp = df.copy()
        df_temp["claim_evidence"] = df_temp["claim_text"].astype(str) + " " + df_temp["evidence_text"].astype(str)
        _, b3b_m = train_flat4_baseline(df_temp, None, train_mask, dev_mask, test_mask, use_tfidf=True, text_col="claim_evidence")
        baseline_records.append({"seed": seed, "method": "B3b_tfidf_claim_evidence", **b3b_m})

    # Compute means
    baseline_df = pd.DataFrame(baseline_records)
    r4_repro_df = pd.DataFrame(r4_repro_records)

    metric_cols = ["flat4_macro_f1", "strong_positive_f1", "contradiction_positive_f1",
                   "escalation_macro_f1", "strong_precision", "strong_recall"]

    # Save per-seed results
    all_results = pd.concat([r4_repro_df, baseline_df], ignore_index=True)
    all_results.to_csv(EXP_DIR / "strong_baseline_results_by_seed.csv", index=False)
    log(f"  Saved strong_baseline_results_by_seed.csv ({len(all_results)} rows)")

    # Summary
    summary = {}
    for method in ["R4_conservative_strong", "B1_nli_only_flat4", "B2_nli_plus_action_gap_flat4",
                    "B3a_tfidf_claim_only", "B3b_tfidf_claim_evidence"]:
        mrows = all_results[all_results["method"] == method]
        summary[method] = {}
        for mc in metric_cols:
            vals = mrows[mc].astype(float).values
            summary[method][f"{mc}_mean"] = float(np.mean(vals))
            summary[method][f"{mc}_std"] = float(np.std(vals, ddof=1)) if len(vals) > 1 else 0.0

    # B4: Skipped (no sentence-transformer)
    summary["B4_sentence_embedding"] = {"status": "skipped", "reason": "sentence_transformers not installed; no cached embeddings"}

    # B5: Frozen encoder (report with caveat)
    fe_df = pd.read_csv(FROZEN_ENCODER_DIR / "frozen_encoder_by_seed.csv")
    fe_flat4 = fe_df[(fe_df["task"] == "flat_4class") & (fe_df["protocol"] == "strict_only")]
    for cfg in ["cross_encoder_nli_pair", "hybrid_tfidf_plus_nli", "tfidf_claim_only", "tfidf_claim_evidence"]:
        cfg_rows = fe_flat4[fe_flat4["config"] == cfg]
        if len(cfg_rows) > 0:
            summary[f"B5_{cfg}"] = {
                "flat4_macro_f1_mean": float(cfg_rows["macro_f1"].mean()),
                "flat4_macro_f1_std": float(cfg_rows["macro_f1"].std()),
                "strong_positive_f1": "NA (frozen encoder did not compute per-class strong F1)",
                "note": "Uses 70/30 split (no dev set); NOT directly comparable to R4 70/15/15",
                "n_seeds": len(cfg_rows),
            }

    # B6: Cost-sensitive
    summary["B6_cost_sensitive_cw4.0"] = {
        "strong_positive_f1_mean": b6_metrics.get("strong_positive_f1_mean"),
        "flat4_macro_f1_mean": b6_metrics.get("flat4_macro_f1_mean"),
        "contradiction_positive_f1_mean": b6_metrics.get("contradiction_positive_f1_mean"),
        "escalation_macro_f1_mean": b6_metrics.get("escalation_macro_f1_mean"),
        "note": "From Task M; auxiliary module, not main method",
    }

    with open(EXP_DIR / "strong_baseline_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log("  Saved strong_baseline_summary.json")

    # R4 vs strong baselines comparison table
    r4_vs_baselines_rows = []
    r4_strong_vals = r4_repro_df["strong_positive_f1"].astype(float).values
    r4_flat4_vals = r4_repro_df["flat4_macro_f1"].astype(float).values
    r4_contra_vals = r4_repro_df["contradiction_positive_f1"].astype(float).values
    r4_escal_vals = r4_repro_df["escalation_macro_f1"].astype(float).values

    for method in ["B1_nli_only_flat4", "B2_nli_plus_action_gap_flat4", "B3a_tfidf_claim_only", "B3b_tfidf_claim_evidence"]:
        mrows = all_results[all_results["method"] == method]
        b_strong = mrows["strong_positive_f1"].astype(float).values
        b_flat4 = mrows["flat4_macro_f1"].astype(float).values
        b_contra = mrows["contradiction_positive_f1"].astype(float).values
        b_escal = mrows["escalation_macro_f1"].astype(float).values
        deltas_strong = r4_strong_vals - b_strong
        mean_delta, ci_lo, ci_hi = bootstrap_ci(deltas_strong)
        positive_count = int(np.sum(deltas_strong > 0))
        r4_vs_baselines_rows.append({
            "method": method,
            "r4_strong_positive_f1": f"{np.mean(r4_strong_vals):.4f}",
            "baseline_strong_positive_f1": f"{np.mean(b_strong):.4f}",
            "delta_strong": f"{mean_delta:.4f}",
            "ci_lower": f"{ci_lo:.4f}",
            "ci_upper": f"{ci_hi:.4f}",
            "positive_seed_count": f"{positive_count}/10",
            "r4_flat4_macro_f1": f"{np.mean(r4_flat4_vals):.4f}",
            "baseline_flat4_macro_f1": f"{np.mean(b_flat4):.4f}",
            "delta_flat4": f"{np.mean(r4_flat4_vals) - np.mean(b_flat4):.4f}",
            "delta_contra": f"{np.mean(r4_contra_vals) - np.mean(b_contra):.4f}",
            "delta_escalation": f"{np.mean(r4_escal_vals) - np.mean(b_escal):.4f}",
            "r4_wins_strong": "YES" if mean_delta > 0 else "NO",
        })

    # Add B5 and B6 with available data
    for cfg in ["cross_encoder_nli_pair", "hybrid_tfidf_plus_nli"]:
        key = f"B5_{cfg}"
        if key in summary:
            r4_vs_baselines_rows.append({
                "method": f"{key} (70/30 split, not comparable)",
                "r4_strong_positive_f1": f"{np.mean(r4_strong_vals):.4f}",
                "baseline_strong_positive_f1": "NA",
                "delta_strong": "NA",
                "ci_lower": "NA", "ci_upper": "NA",
                "positive_seed_count": "NA",
                "r4_flat4_macro_f1": f"{np.mean(r4_flat4_vals):.4f}",
                "baseline_flat4_macro_f1": f"{summary[key]['flat4_macro_f1_mean']:.4f}",
                "delta_flat4": f"{np.mean(r4_flat4_vals) - summary[key]['flat4_macro_f1_mean']:.4f}",
                "delta_contra": "NA", "delta_escalation": "NA",
                "r4_wins_strong": "NA",
            })

    r4_vs_baselines_rows.append({
        "method": "B6_cost_sensitive_cw4.0 (auxiliary)",
        "r4_strong_positive_f1": f"{np.mean(r4_strong_vals):.4f}",
        "baseline_strong_positive_f1": f"{b6_metrics.get('strong_positive_f1_mean', 0):.4f}",
        "delta_strong": f"{np.mean(r4_strong_vals) - b6_metrics.get('strong_positive_f1_mean', 0):.4f}",
        "ci_lower": "NA", "ci_upper": "NA",
        "positive_seed_count": "NA",
        "r4_flat4_macro_f1": f"{np.mean(r4_flat4_vals):.4f}",
        "baseline_flat4_macro_f1": f"{b6_metrics.get('flat4_macro_f1_mean', 0):.4f}",
        "delta_flat4": f"{np.mean(r4_flat4_vals) - b6_metrics.get('flat4_macro_f1_mean', 0):.4f}",
        "delta_contra": "NA", "delta_escalation": "NA",
        "r4_wins_strong": "NO" if b6_metrics.get("strong_positive_f1_mean", 0) > np.mean(r4_strong_vals) else "YES",
    })

    import csv
    with open(EXP_DIR / "r4_vs_strong_baselines.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(r4_vs_baselines_rows[0].keys()))
        writer.writeheader()
        writer.writerows(r4_vs_baselines_rows)
    log("  Saved r4_vs_strong_baselines.csv")

    # ================================================================
    # Part 2: Holdout Validation
    # ================================================================
    log("\n" + "=" * 70)
    log("Part 2: Holdout Validation")
    log("=" * 70)

    # ---------------- H1: Leave-one-domain-out ----------------
    log("\n--- H1: Leave-one-domain-out ---")
    domains = sorted(df["domain"].unique().tolist())
    domain_holdout_rows = []
    for held_domain in domains:
        log(f"  Held-out domain: {held_domain}")
        test_domain_mask = (domain_ids == held_domain)
        train_domain_mask = ~test_domain_mask
        train_groups = group_ids[train_domain_mask]
        # Inner train/dev split (85/15) for threshold tuning
        inner_train_mask_local, inner_dev_mask_local = group_aware_split_from_subset(train_groups, seed=11, train_frac=0.85)
        # Map back to global masks
        global_train_mask = np.zeros(len(df), dtype=bool)
        global_dev_mask = np.zeros(len(df), dtype=bool)
        global_test_mask = test_domain_mask
        # train_groups[train_domain_mask] indexes into the subset; need to map
        train_indices = np.where(train_domain_mask)[0]
        for idx in train_indices:
            if inner_train_mask_local[np.where(train_indices == idx)[0][0]] if idx in train_indices else False:
                pass
        # Simpler: directly assign
        subset_groups = group_ids[train_domain_mask]
        tr_mask_sub, dev_mask_sub = group_aware_split_from_subset(subset_groups, seed=11, train_frac=0.85)
        global_train_mask[train_domain_mask] = tr_mask_sub
        global_dev_mask[train_domain_mask] = dev_mask_sub

        n_test = int(global_test_mask.sum())
        if n_test < 4:
            log(f"    Skipped (n_test={n_test} too small)")
            continue

        # R4
        _, r4_m, _ = train_r4_and_predict(df, global_train_mask, global_dev_mask, global_test_mask)
        # B1: NLI-only
        _, b1_m = train_flat4_baseline(df, NLI_FEATURES, global_train_mask, global_dev_mask, global_test_mask)
        # B3b: TF-IDF claim+evidence
        df_temp = df.copy()
        df_temp["claim_evidence"] = df_temp["claim_text"].astype(str) + " " + df_temp["evidence_text"].astype(str)
        _, b3b_m = train_flat4_baseline(df_temp, None, global_train_mask, global_dev_mask, global_test_mask, use_tfidf=True, text_col="claim_evidence")

        delta_r4_b1 = r4_m["strong_positive_f1"] - b1_m["strong_positive_f1"]
        delta_r4_b3 = r4_m["strong_positive_f1"] - b3b_m["strong_positive_f1"]
        best_baseline_strong = max(b1_m["strong_positive_f1"], b3b_m["strong_positive_f1"])
        domain_holdout_rows.append({
            "domain": held_domain,
            "n_test": n_test,
            "r4_flat4_macro": f"{r4_m['flat4_macro_f1']:.4f}",
            "r4_strong_f1": f"{r4_m['strong_positive_f1']:.4f}",
            "r4_contra_f1": f"{r4_m['contradiction_positive_f1']:.4f}",
            "r4_escalation_f1": f"{r4_m['escalation_macro_f1']:.4f}",
            "b1_nli_strong_f1": f"{b1_m['strong_positive_f1']:.4f}",
            "b3b_tfidf_strong_f1": f"{b3b_m['strong_positive_f1']:.4f}",
            "best_baseline_strong_f1": f"{best_baseline_strong:.4f}",
            "delta_r4_vs_best": f"{r4_m['strong_positive_f1'] - best_baseline_strong:.4f}",
            "r4_stable": "YES" if r4_m["strong_positive_f1"] >= best_baseline_strong else "NO",
        })
        log(f"    R4 strong={r4_m['strong_positive_f1']:.4f}, B1={b1_m['strong_positive_f1']:.4f}, B3b={b3b_m['strong_positive_f1']:.4f}")

    import csv
    with open(EXP_DIR / "domain_holdout_results.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(domain_holdout_rows[0].keys()))
        writer.writeheader()
        writer.writerows(domain_holdout_rows)
    log(f"  Saved domain_holdout_results.csv ({len(domain_holdout_rows)} domains)")

    # Leave-domain-out summary
    r4_stable_count = sum(1 for r in domain_holdout_rows if r["r4_stable"] == "YES")
    leave_domain_out_summary = {
        "n_domains": len(domain_holdout_rows),
        "r4_stable_domains": r4_stable_count,
        "r4_unstable_domains": len(domain_holdout_rows) - r4_stable_count,
        "fragile_domains": [r["domain"] for r in domain_holdout_rows if r["r4_stable"] == "NO"],
        "mean_r4_strong_f1": float(np.mean([float(r["r4_strong_f1"]) for r in domain_holdout_rows])),
        "mean_best_baseline_strong_f1": float(np.mean([float(r["best_baseline_strong_f1"]) for r in domain_holdout_rows])),
        "r4_generalizes_beyond_random_split": r4_stable_count >= 4,
    }
    with open(EXP_DIR / "leave_domain_out_summary.json", "w", encoding="utf-8") as f:
        json.dump(leave_domain_out_summary, f, indent=2, ensure_ascii=False)

    # ---------------- H2: Leave-one-source-out ----------------
    log("\n--- H2: Leave-one-source-out ---")
    source_counts = df["source_id"].value_counts()
    eligible_sources = source_counts[source_counts >= 8].index.tolist()
    log(f"  Eligible sources (n>=8): {len(eligible_sources)}")
    source_holdout_rows = []
    for held_source in eligible_sources:
        test_source_mask = (source_ids == held_source)
        train_source_mask = ~test_source_mask
        n_test = int(test_source_mask.sum())
        if n_test < 4:
            continue
        subset_groups = group_ids[train_source_mask]
        tr_mask_sub, dev_mask_sub = group_aware_split_from_subset(subset_groups, seed=11, train_frac=0.85)
        global_train_mask = np.zeros(len(df), dtype=bool)
        global_dev_mask = np.zeros(len(df), dtype=bool)
        global_test_mask = test_source_mask
        global_train_mask[train_source_mask] = tr_mask_sub
        global_dev_mask[train_source_mask] = dev_mask_sub

        _, r4_m, _ = train_r4_and_predict(df, global_train_mask, global_dev_mask, global_test_mask)
        _, b1_m = train_flat4_baseline(df, NLI_FEATURES, global_train_mask, global_dev_mask, global_test_mask)

        source_holdout_rows.append({
            "source_id": held_source,
            "n_test": n_test,
            "r4_flat4_macro": f"{r4_m['flat4_macro_f1']:.4f}",
            "r4_strong_f1": f"{r4_m['strong_positive_f1']:.4f}",
            "r4_contra_f1": f"{r4_m['contradiction_positive_f1']:.4f}",
            "b1_nli_strong_f1": f"{b1_m['strong_positive_f1']:.4f}",
            "b1_nli_flat4_macro": f"{b1_m['flat4_macro_f1']:.4f}",
            "delta_r4_vs_b1_strong": f"{r4_m['strong_positive_f1'] - b1_m['strong_positive_f1']:.4f}",
            "r4_stable": "YES" if r4_m["strong_positive_f1"] >= b1_m["strong_positive_f1"] else "NO",
        })

    if source_holdout_rows:
        with open(EXP_DIR / "source_holdout_results.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(source_holdout_rows[0].keys()))
            writer.writeheader()
            writer.writerows(source_holdout_rows)
        log(f"  Saved source_holdout_results.csv ({len(source_holdout_rows)} sources)")

    r4_stable_sources = sum(1 for r in source_holdout_rows if r["r4_stable"] == "YES")
    fragile_sources = [r["source_id"] for r in source_holdout_rows if r["r4_stable"] == "NO"]
    leave_source_out_summary = {
        "n_sources_tested": len(source_holdout_rows),
        "r4_stable_sources": r4_stable_sources,
        "r4_unstable_sources": len(source_holdout_rows) - r4_stable_sources,
        "fragile_sources": fragile_sources[:10],
        "mean_r4_strong_f1": float(np.mean([float(r["r4_strong_f1"]) for r in source_holdout_rows])),
        "mean_b1_strong_f1": float(np.mean([float(r["b1_nli_strong_f1"]) for r in source_holdout_rows])),
    }
    with open(EXP_DIR / "leave_source_out_summary.json", "w", encoding="utf-8") as f:
        json.dump(leave_source_out_summary, f, indent=2, ensure_ascii=False)

    # ---------------- H3: Source-pair holdout ----------------
    log("\n--- H3: Source-pair holdout ---")
    # Verify group integrity: each group should be entirely in one split
    # Run 3 seeds and check no group leakage
    source_pair_rows = []
    for seed in [11, 22, 33]:
        train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed)
        train_groups = set(group_ids[train_mask])
        dev_groups = set(group_ids[dev_mask])
        test_groups = set(group_ids[test_mask])
        overlap_td = len(train_groups & dev_groups)
        overlap_tt = len(train_groups & test_groups)
        overlap_dt = len(dev_groups & test_groups)

        _, r4_m, _ = train_r4_and_predict(df, train_mask, dev_mask, test_mask)
        source_pair_rows.append({
            "seed": seed,
            "n_train_groups": len(train_groups),
            "n_dev_groups": len(dev_groups),
            "n_test_groups": len(test_groups),
            "train_dev_overlap": overlap_td,
            "train_test_overlap": overlap_tt,
            "dev_test_overlap": overlap_dt,
            "group_leakage": "NONE" if (overlap_td + overlap_tt + overlap_dt) == 0 else "LEAKAGE",
            "r4_strong_f1": f"{r4_m['strong_positive_f1']:.4f}",
            "r4_flat4_macro": f"{r4_m['flat4_macro_f1']:.4f}",
        })
        log(f"  Seed {seed}: leakage={source_pair_rows[-1]['group_leakage']}, r4_strong={r4_m['strong_positive_f1']:.4f}")

    with open(EXP_DIR / "source_pair_holdout_results.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=list(source_pair_rows[0].keys()))
        writer.writeheader()
        writer.writerows(source_pair_rows)

    # ---------------- H4: Domain robustness table ----------------
    log("\n--- H4: Domain robustness table (per-domain on random split) ---")
    domain_robust_rows = []
    # Use seed=11 as representative
    train_mask, dev_mask, test_mask = group_aware_split(group_ids, seed=11)
    r4_pred, _, _ = train_r4_and_predict(df, train_mask, dev_mask, test_mask)

    test_df = df[test_mask].copy()
    test_df["r4_pred"] = r4_pred
    for dom in domains:
        dom_mask = test_df["domain"] == dom
        if dom_mask.sum() < 2:
            continue
        y_4 = test_df.loc[dom_mask, "label_4_idx"].values
        y_strong = test_df.loc[dom_mask, "y_strong"].values
        y_esc = test_df.loc[dom_mask, "y_esc"].values
        y_contra = test_df.loc[dom_mask, "y_contra"].values
        pred = test_df.loc[dom_mask, "r4_pred"].values
        m = compute_all_metrics(y_4, y_strong, y_esc, y_contra, pred)
        # Error rates
        sup_mask = y_4 == LABEL_TO_IDX["supported"]
        mild_mask = y_4 == LABEL_TO_IDX["mild_scope_overclaim"]
        strong_mask = y_4 == LABEL_TO_IDX["strong_action_overclaim"]
        sup_to_strong = float(np.mean(pred[sup_mask] == LABEL_TO_IDX["strong_action_overclaim"])) if sup_mask.sum() > 0 else 0.0
        mild_to_strong = float(np.mean(pred[mild_mask] == LABEL_TO_IDX["strong_action_overclaim"])) if mild_mask.sum() > 0 else 0.0
        strong_to_supported = float(np.mean(pred[strong_mask] == LABEL_TO_IDX["supported"])) if strong_mask.sum() > 0 else 0.0
        strong_to_mild = float(np.mean(pred[strong_mask] == LABEL_TO_IDX["mild_scope_overclaim"])) if strong_mask.sum() > 0 else 0.0
        strong_to_contra = float(np.mean(pred[strong_mask] == LABEL_TO_IDX["contradiction_candidate"])) if strong_mask.sum() > 0 else 0.0

        domain_robust_rows.append({
            "domain": dom,
            "n_test": int(dom_mask.sum()),
            "flat4_macro_f1": f"{m['flat4_macro_f1']:.4f}",
            "strong_positive_f1": f"{m['strong_positive_f1']:.4f}",
            "contradiction_positive_f1": f"{m['contradiction_positive_f1']:.4f}",
            "escalation_macro_f1": f"{m['escalation_macro_f1']:.4f}",
            "supported_to_strong_rate": f"{sup_to_strong:.4f}",
            "mild_to_strong_rate": f"{mild_to_strong:.4f}",
            "strong_to_supported_rate": f"{strong_to_supported:.4f}",
            "strong_to_mild_rate": f"{strong_to_mild:.4f}",
            "strong_to_contradiction_rate": f"{strong_to_contra:.4f}",
        })

    if domain_robust_rows:
        with open(EXP_DIR / "domain_holdout_results.csv", "a", encoding="utf-8", newline="") as f:
            pass  # Already saved H1 above
        # Save H4 separately by appending to a new file
        h4_path = EXP_DIR / "domain_robustness_table.csv"
        with open(h4_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(domain_robust_rows[0].keys()))
            writer.writeheader()
            writer.writerows(domain_robust_rows)
        log(f"  Saved domain_robustness_table.csv ({len(domain_robust_rows)} domains)")

    # ---------------- Holdout failure cases ----------------
    log("\n--- Holdout failure cases ---")
    failure_cases = []
    for r in domain_holdout_rows:
        if r["r4_stable"] == "NO":
            failure_cases.append({
                "holdout_type": "leave_domain_out",
                "identifier": r["domain"],
                "n_test": r["n_test"],
                "r4_strong_f1": r["r4_strong_f1"],
                "best_baseline_strong_f1": r["best_baseline_strong_f1"],
                "delta": r["delta_r4_vs_best"],
                "issue": "R4 strong F1 below best baseline on this domain",
            })
    for r in source_holdout_rows:
        if r["r4_stable"] == "NO":
            failure_cases.append({
                "holdout_type": "leave_source_out",
                "identifier": r["source_id"],
                "n_test": r["n_test"],
                "r4_strong_f1": r["r4_strong_f1"],
                "best_baseline_strong_f1": r["b1_nli_strong_f1"],
                "delta": r["delta_r4_vs_b1_strong"],
                "issue": "R4 strong F1 below NLI-only baseline on this source",
            })

    with open(EXP_DIR / "holdout_failure_cases.csv", "w", encoding="utf-8", newline="") as f:
        if failure_cases:
            writer = csv.DictWriter(f, fieldnames=list(failure_cases[0].keys()))
            writer.writeheader()
            writer.writerows(failure_cases)
        else:
            f.write("no_failure_cases\n")
    log(f"  Saved holdout_failure_cases.csv ({len(failure_cases)} cases)")

    # ================================================================
    # Readiness Gate
    # ================================================================
    log("\n" + "=" * 70)
    log("Readiness Gate")
    log("=" * 70)

    # Determine best baselines
    baseline_strong_means = {m: summary.get(m, {}).get("strong_positive_f1_mean", 0) for m in
                             ["B1_nli_only_flat4", "B2_nli_plus_action_gap_flat4", "B3a_tfidf_claim_only", "B3b_tfidf_claim_evidence"]}
    best_strong_baseline = max(baseline_strong_means, key=baseline_strong_means.get) if baseline_strong_means else "NA"
    best_strong_value = baseline_strong_means.get(best_strong_baseline, 0)
    r4_strong_mean = float(np.mean(r4_strong_vals))

    # Check if any baseline beats R4 overall
    any_baseline_beats_r4 = any(v > r4_strong_mean for v in baseline_strong_means.values() if isinstance(v, (int, float)))

    # R4 vs specific baselines
    r4_vs_nli_delta = r4_strong_mean - baseline_strong_means.get("B1_nli_only_flat4", 0)
    r4_vs_tfidf_delta = r4_strong_mean - baseline_strong_means.get("B3b_tfidf_claim_evidence", 0)
    r4_vs_best_strong_delta = r4_strong_mean - best_strong_value

    # Domain holdout status
    domain_holdout_status = "stable" if leave_domain_out_summary["r4_generalizes_beyond_random_split"] else "fragile"
    source_holdout_status = "stable" if r4_stable_sources >= len(source_holdout_rows) * 0.6 else "fragile"
    source_pair_holdout_status = "no_leakage" if all(r["group_leakage"] == "NONE" for r in source_pair_rows) else "leakage_detected"

    # Validation status
    r4_retained = (
        r4_vs_best_strong_delta > 0
        and not any_baseline_beats_r4
        and domain_holdout_status == "stable"
    )

    if any_baseline_beats_r4:
        validation_status = "R4_not_main_candidate"
        recommended_use = "reject"
        main_blocker = f"baseline {best_strong_baseline} beats R4 (delta={r4_vs_best_strong_delta:.4f})"
    elif domain_holdout_status == "fragile":
        validation_status = "fragile"
        recommended_use = "auxiliary_only"
        main_blocker = f"R4 fragile on domain holdout (only {r4_stable_count}/{len(domain_holdout_rows)} stable)"
    else:
        validation_status = "supportive_but_not_final"
        recommended_use = "main_method_retained"
        main_blocker = "none"

    gate = {
        "generated_at": datetime.now().isoformat(),
        "r4_main_method_retained": r4_retained,
        "validation_status": validation_status,
        "best_overall_baseline": best_strong_baseline,
        "best_strong_baseline": best_strong_baseline,
        "best_strong_baseline_value": best_strong_value,
        "r4_strong_positive_f1": r4_strong_mean,
        "r4_vs_best_strong_delta": r4_vs_best_strong_delta,
        "r4_vs_tfidf_delta": r4_vs_tfidf_delta,
        "r4_vs_nli_flat_delta": r4_vs_nli_delta,
        "domain_holdout_status": domain_holdout_status,
        "source_holdout_status": source_holdout_status,
        "source_pair_holdout_status": source_pair_holdout_status,
        "fragile_domains": leave_domain_out_summary["fragile_domains"],
        "fragile_sources": fragile_sources[:10],
        "does_r4_generalize_beyond_random_split": leave_domain_out_summary["r4_generalizes_beyond_random_split"],
        "does_r4_need_revision": (domain_holdout_status == "fragile" or any_baseline_beats_r4),
        "recommended_use": recommended_use,
        "main_blocker": main_blocker,
        "recommended_next_step": "expand to 300-500 human-audited pairs; validate on gold; run significance tests vs strong external baselines",
        "strong_baseline_summary": {
            "B1_nli_only": {"strong_f1": baseline_strong_means.get("B1_nli_only_flat4", 0), "flat4_macro": summary.get("B1_nli_only_flat4", {}).get("flat4_macro_f1_mean", 0)},
            "B2_nli_plus_gap": {"strong_f1": baseline_strong_means.get("B2_nli_plus_action_gap_flat4", 0), "flat4_macro": summary.get("B2_nli_plus_action_gap_flat4", {}).get("flat4_macro_f1_mean", 0)},
            "B3a_tfidf_claim_only": {"strong_f1": baseline_strong_means.get("B3a_tfidf_claim_only", 0), "flat4_macro": summary.get("B3a_tfidf_claim_only", {}).get("flat4_macro_f1_mean", 0)},
            "B3b_tfidf_claim_evidence": {"strong_f1": baseline_strong_means.get("B3b_tfidf_claim_evidence", 0), "flat4_macro": summary.get("B3b_tfidf_claim_evidence", {}).get("flat4_macro_f1_mean", 0)},
            "B4_sentence_embedding": "skipped (no sentence-transformer)",
            "B5_cross_encoder_nli": summary.get("B5_cross_encoder_nli_pair", {}),
            "B6_cost_sensitive_cw4.0": {"strong_f1": b6_metrics.get("strong_positive_f1_mean"), "note": "auxiliary"},
        },
        "holdout_summary": {
            "leave_domain_out": leave_domain_out_summary,
            "leave_source_out": leave_source_out_summary,
            "source_pair": {"group_leakage": source_pair_holdout_status, "seeds_tested": [r["seed"] for r in source_pair_rows]},
        },
    }

    with open(EXP_DIR / "validation_readiness_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    log("  Saved validation_readiness_gate.json")

    # ---------------- Verify all output files ----------------
    log("\nVerifying output files...")
    expected_files = [
        "strong_baseline_results_by_seed.csv",
        "strong_baseline_summary.json",
        "r4_vs_strong_baselines.csv",
        "domain_holdout_results.csv",
        "source_holdout_results.csv",
        "source_pair_holdout_results.csv",
        "leave_domain_out_summary.json",
        "leave_source_out_summary.json",
        "holdout_failure_cases.csv",
        "validation_readiness_gate.json",
        "run.log",
    ]
    for fname in expected_files:
        fpath = EXP_DIR / fname
        if fpath.exists():
            log(f"  OK: {fname} ({fpath.stat().st_size} bytes)")
        else:
            log(f"  MISSING: {fname}")

    log("\n" + "=" * 70)
    log("Task P complete.")
    log(f"  R4 retained: {r4_retained}")
    log(f"  Validation status: {validation_status}")
    log(f"  Best baseline: {best_strong_baseline} (strong_f1={best_strong_value:.4f})")
    log(f"  R4 strong_f1: {r4_strong_mean:.4f}, delta vs best: {r4_vs_best_strong_delta:.4f}")
    log(f"  Domain holdout: {domain_holdout_status} ({r4_stable_count}/{len(domain_holdout_rows)} stable)")
    log("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL ERROR: {e}")
        log(traceback.format_exc())
        sys.exit(1)
