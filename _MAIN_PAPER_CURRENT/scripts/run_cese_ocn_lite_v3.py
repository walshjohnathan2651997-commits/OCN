"""CESE-OCN-lite V3: Evidence-Necessity Calibration.

Upgrades V2 (frozen NLI cross-encoder + LR) by adding evidence-necessity
delta features: correct NLI minus shuffled/empty/title NLI.

Core claim: the model needs CORRECT evidence to judge escalation, not just
claim lexical patterns or NLI prior.

Constraints:
  - Frozen encoder only (cross-encoder/nli-deberta-base, cached)
  - No transformer fine-tuning, no LLM API, no data modification
  - Silver labels (AI-preannotated). NOT gold, NOT human-audited.
  - human_audited=False, final_label/gold_label always empty
"""
from __future__ import annotations

import csv
import json
import math
import warnings
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.sparse import hstack as sparse_hstack, csr_matrix
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_score,
    recall_score,
)

warnings.filterwarnings("ignore", category=FutureWarning)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
BASE = Path(r"d:\ocn")
DATA_CSV = BASE / "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv"
V2_SUMMARY = BASE / "experiments/evidence_aware_frozen_encoder_v1/frozen_encoder_summary.json"
OUT_DIR = BASE / "experiments/cese_ocn_lite_v3"
DOC_DIR = BASE / "docs/cese_ocn_lite_v3"

SEEDS = [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]
NLI_MODEL_NAME = "cross-encoder/nli-deberta-base"
SHUFFLE_SEED = 42
LR_RANDOM_STATE = 42
CUE_WORDS = [
    "always", "guarantee", "fully", "complete", "only",
    "no longer", "across all", "deployment-ready", "real-world",
]

# V2 baseline number (for comparison)
V2_BEST_MACRO_F1 = 0.6893  # cross_encoder_nli_pair escalation_binary strict_only

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def load_data():
    df = pd.read_csv(DATA_CSV, keep_default_na=False)
    assert len(df) == 444, f"Expected 444 rows, got {len(df)}"
    assert df["target_candidate_group_id"].nunique() == 111
    assert df["domain"].nunique() == 6
    esc = df["escalation_binary_label_guess"].value_counts().to_dict()
    assert esc.get("escalation", 0) == 222 and esc.get("non_escalation", 0) == 222
    assert (df["human_audited"] == False).all() or (df["human_audited"] == "False").all()
    assert (df["final_label"] == "").all()
    assert (df["gold_label"] == "").all()
    # Encode labels
    df["y_escalation"] = (df["escalation_binary_label_guess"] == "escalation").astype(int)
    df["y_contradiction"] = (df["contradiction_binary_label_guess"] == "contradiction").astype(int)
    return df


# ---------------------------------------------------------------------------
# Shuffled evidence (group-level derangement)
# ---------------------------------------------------------------------------
def build_shuffled_indices(df):
    rng = np.random.RandomState(SHUFFLE_SEED)
    group_ids = df["target_candidate_group_id"].values
    n = len(df)
    for _ in range(1000):
        perm = rng.permutation(n)
        if np.all(group_ids[perm] != group_ids):
            return perm
    # Fallback: cyclic shift by half
    return np.roll(np.arange(n), n // 2)


# ---------------------------------------------------------------------------
# NLI feature precomputation
# ---------------------------------------------------------------------------
def compute_nli_for_pairs(pairs, model, tokenizer, batch_size=16):
    """Compute NLI features for a list of (premise, hypothesis) pairs.

    Returns array of shape (n_pairs, 7):
      [entailment_prob, neutral_prob, contradiction_prob,
       entailment_minus_contradiction, contradiction_minus_entailment,
       max_prob, entropy]
    """
    import torch
    from torch.nn.functional import softmax

    all_features = []
    model.eval()
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start : start + batch_size]
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
                print(f"    NLI progress: {start}/{len(pairs)}")

    return np.vstack(all_features)


def precompute_all_nli(df, model, tokenizer):
    """Compute NLI features for 4 evidence conditions."""
    n = len(df)
    claims = df["claim_text"].tolist()
    evidence = df["evidence_text"].tolist()
    titles = df["title"].tolist()
    shuffled_idx = build_shuffled_indices(df)
    shuffled_evidence = [evidence[i] for i in shuffled_idx]

    print(f"  Computing NLI for correct evidence ({n} pairs)...")
    correct_nli = compute_nli_for_pairs(
        list(zip(evidence, claims)), model, tokenizer
    )

    print(f"  Computing NLI for shuffled evidence ({n} pairs)...")
    shuffled_nli = compute_nli_for_pairs(
        list(zip(shuffled_evidence, claims)), model, tokenizer
    )

    print(f"  Computing NLI for empty evidence ({n} pairs)...")
    empty_nli = compute_nli_for_pairs(
        list(zip([""] * n, claims)), model, tokenizer
    )

    print(f"  Computing NLI for title evidence ({n} pairs)...")
    title_nli = compute_nli_for_pairs(
        list(zip(titles, claims)), model, tokenizer
    )

    return {
        "correct": correct_nli,
        "shuffled": shuffled_nli,
        "empty": empty_nli,
        "title": title_nli,
        "shuffled_idx": shuffled_idx,
    }


# ---------------------------------------------------------------------------
# V3 feature construction
# ---------------------------------------------------------------------------
def build_lexical_features(df):
    n = len(df)
    claim_lens = np.array([len(str(t).split()) for t in df["claim_text"]])
    evidence_lens = np.array([len(str(t).split()) for t in df["evidence_text"]])

    overlaps = []
    cue_counts = []
    for _, row in df.iterrows():
        claim_tokens = set(str(row["claim_text"]).lower().split())
        evidence_tokens = set(str(row["evidence_text"]).lower().split())
        union = claim_tokens | evidence_tokens
        overlap = len(claim_tokens & evidence_tokens) / max(len(union), 1)
        overlaps.append(overlap)

        claim_lower = str(row["claim_text"]).lower()
        cue = sum(1 for w in CUE_WORDS if w in claim_lower)
        cue_counts.append(cue)

    return np.column_stack([
        claim_lens, evidence_lens, np.array(overlaps), np.array(cue_counts)
    ]).astype(float)


def build_v3_features(nli_data, lexical):
    correct = nli_data["correct"]  # (n, 7)
    shuffled = nli_data["shuffled"]
    empty = nli_data["empty"]
    title = nli_data["title"]

    # correct_nli: 7 dims (indices: 0=ent, 1=neu, 2=con, 3=emc, 4=cme, 5=max, 6=entropy)
    correct_nli = correct.copy()

    # Delta features: 8 dims
    delta = np.column_stack([
        correct[:, 0] - shuffled[:, 0],   # ent_delta_shuffled
        correct[:, 2] - shuffled[:, 2],   # con_delta_shuffled
        correct[:, 6] - shuffled[:, 6],   # entropy_delta_shuffled
        correct[:, 0] - empty[:, 0],      # ent_delta_empty
        correct[:, 2] - empty[:, 2],      # con_delta_empty
        correct[:, 6] - empty[:, 6],      # entropy_delta_empty
        correct[:, 0] - title[:, 0],      # ent_delta_title
        correct[:, 2] - title[:, 2],      # con_delta_title
    ])

    # V3 full: correct_nli (7) + delta (8) + lexical (4) = 19
    v3_full = np.column_stack([correct_nli, delta, lexical])

    return {
        "correct_nli": correct_nli,      # 7 dims (V2 replication)
        "delta_only": delta,              # 8 dims
        "v3_full": v3_full,               # 19 dims
        "lexical": lexical,               # 4 dims
    }


# ---------------------------------------------------------------------------
# Group-aware split
# ---------------------------------------------------------------------------
def group_split(group_ids, seed, train_ratio=0.70, dev_ratio=0.15):
    """Split groups into train/dev/test. Returns (train_idx, dev_idx, test_idx)."""
    unique_groups = sorted(set(group_ids))
    rng = np.random.RandomState(seed)
    rng.shuffle(unique_groups)

    n = len(unique_groups)
    n_train = int(n * train_ratio)
    n_dev = int(n * dev_ratio)

    train_groups = set(unique_groups[:n_train])
    dev_groups = set(unique_groups[n_train : n_train + n_dev])
    test_groups = set(unique_groups[n_train + n_dev :])

    group_arr = np.array(group_ids)
    train_idx = np.where([g in train_groups for g in group_arr])[0]
    dev_idx = np.where([g in dev_groups for g in group_arr])[0]
    test_idx = np.where([g in test_groups for g in group_arr])[0]

    return train_idx, dev_idx, test_idx


# ---------------------------------------------------------------------------
# Config definitions
# ---------------------------------------------------------------------------
CONFIG_NAMES = [
    "tfidf_claim_only",
    "tfidf_claim_evidence",
    "v2_cross_encoder_nli_pair",
    "v3_cese_ocn_lite_delta_only",
    "v3_cese_ocn_lite_full",
    "v3_hybrid_tfidf_plus_cese_lite",
]

DELTA_FEATURE_NAMES = [
    "ent_delta_shuffled", "con_delta_shuffled", "entropy_delta_shuffled",
    "ent_delta_empty", "con_delta_empty", "entropy_delta_empty",
    "ent_delta_title", "con_delta_title",
]


def get_config_features(config_name, df, v3_features, tfidf_claim, tfidf_claim_evidence):
    """Return (X_train_fn, X_test_fn) that produce feature matrices given indices."""
    if config_name == "tfidf_claim_only":
        return ("sparse_precomputed", tfidf_claim)
    elif config_name == "tfidf_claim_evidence":
        return ("sparse_precomputed", tfidf_claim_evidence)
    elif config_name == "v2_cross_encoder_nli_pair":
        return ("dense", v3_features["correct_nli"])
    elif config_name == "v3_cese_ocn_lite_delta_only":
        return ("dense", v3_features["delta_only"])
    elif config_name == "v3_cese_ocn_lite_full":
        return ("dense", v3_features["v3_full"])
    elif config_name == "v3_hybrid_tfidf_plus_cese_lite":
        return ("hybrid", (tfidf_claim, v3_features["v3_full"]))
    else:
        raise ValueError(f"Unknown config: {config_name}")


def build_tfidf(train_text, test_text, config_name):
    """Fit TF-IDF on train, transform both."""
    if config_name == "tfidf_claim_only":
        vec = TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english"
        )
        X_train = vec.fit_transform(train_text)
        X_test = vec.transform(test_text)
        return X_train, X_test
    elif config_name == "tfidf_claim_evidence":
        vec = TfidfVectorizer(
            ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english"
        )
        X_train = vec.fit_transform(train_text)
        X_test = vec.transform(test_text)
        return X_train, X_test
    return None, None


# ---------------------------------------------------------------------------
# Metric computation
# ---------------------------------------------------------------------------
def compute_metrics(y_true, y_pred):
    acc = accuracy_score(y_true, y_pred)
    mf1 = f1_score(y_true, y_pred, average="macro")
    pp = precision_score(y_true, y_pred, pos_label=1, zero_division=0)
    pr = recall_score(y_true, y_pred, pos_label=1, zero_division=0)
    pf1 = f1_score(y_true, y_pred, pos_label=1, zero_division=0)
    cm = confusion_matrix(y_true, y_pred, labels=[0, 1]).tolist()
    return {
        "accuracy": round(acc, 4),
        "macro_f1": round(mf1, 4),
        "positive_precision": round(pp, 4),
        "positive_recall": round(pr, 4),
        "positive_f1": round(pf1, 4),
        "confusion_matrix": cm,
    }


# ---------------------------------------------------------------------------
# Protocol A: 10-seed group split
# ---------------------------------------------------------------------------
def run_protocol_a(df, v3_features, group_ids):
    print("\n=== Protocol A: 10-seed group split ===")
    results = []
    delta_results = []
    seed11_predictions = None

    for seed in SEEDS:
        train_idx, dev_idx, test_idx = group_split(group_ids, seed)
        print(f"  seed={seed}: train={len(train_idx)}, dev={len(dev_idx)}, test={len(test_idx)}")

        y_train = df["y_escalation"].values[train_idx]
        y_test = df["y_escalation"].values[test_idx]

        # Precompute TF-IDF for this seed
        claim_train = df["claim_text"].iloc[train_idx].tolist()
        claim_test = df["claim_text"].iloc[test_idx].tolist()
        ce_train = (df["claim_text"] + " " + df["evidence_text"]).iloc[train_idx].tolist()
        ce_test = (df["claim_text"] + " " + df["evidence_text"]).iloc[test_idx].tolist()

        tfidf_claim_train, tfidf_claim_test = build_tfidf(claim_train, claim_test, "tfidf_claim_only")
        tfidf_ce_train, tfidf_ce_test = build_tfidf(ce_train, ce_test, "tfidf_claim_evidence")

        seed_metrics = {}
        for config_name in CONFIG_NAMES:
            clf = LogisticRegression(
                class_weight="balanced", max_iter=3000, random_state=LR_RANDOM_STATE
            )

            if config_name == "tfidf_claim_only":
                X_train, X_test = tfidf_claim_train, tfidf_claim_test
            elif config_name == "tfidf_claim_evidence":
                X_train, X_test = tfidf_ce_train, tfidf_ce_test
            elif config_name == "v2_cross_encoder_nli_pair":
                X_train = v3_features["correct_nli"][train_idx]
                X_test = v3_features["correct_nli"][test_idx]
            elif config_name == "v3_cese_ocn_lite_delta_only":
                X_train = v3_features["delta_only"][train_idx]
                X_test = v3_features["delta_only"][test_idx]
            elif config_name == "v3_cese_ocn_lite_full":
                X_train = v3_features["v3_full"][train_idx]
                X_test = v3_features["v3_full"][test_idx]
            elif config_name == "v3_hybrid_tfidf_plus_cese_lite":
                X_train = sparse_hstack(
                    [tfidf_claim_train, csr_matrix(v3_features["v3_full"][train_idx])]
                )
                X_test = sparse_hstack(
                    [tfidf_claim_test, csr_matrix(v3_features["v3_full"][test_idx])]
                )

            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            m = compute_metrics(y_test, y_pred)
            m["seed"] = seed
            m["config"] = config_name
            m["n_train"] = len(train_idx)
            m["n_test"] = len(test_idx)
            m["task"] = "escalation_binary"
            m["protocol"] = "strict_only"
            results.append(m)
            seed_metrics[config_name] = m

            if seed == 11 and config_name == "v3_cese_ocn_lite_full":
                seed11_predictions = pd.DataFrame({
                    "candidate_id": df["candidate_id"].iloc[test_idx].values,
                    "group_id": df["target_candidate_group_id"].iloc[test_idx].values,
                    "domain": df["domain"].iloc[test_idx].values,
                    "y_true": y_test,
                    "y_pred": y_pred,
                    "config": config_name,
                })

        # Delta vs tfidf_claim_only and vs v2
        baseline_co = seed_metrics["tfidf_claim_only"]["macro_f1"]
        v2_mf1 = seed_metrics["v2_cross_encoder_nli_pair"]["macro_f1"]
        for config_name in CONFIG_NAMES:
            if config_name == "tfidf_claim_only":
                continue
            mf1 = seed_metrics[config_name]["macro_f1"]
            delta_results.append({
                "seed": seed,
                "config": config_name,
                "macro_f1": mf1,
                "delta_vs_tfidf_co": round(mf1 - baseline_co, 4),
                "delta_vs_v2": round(mf1 - v2_mf1, 4),
                "positive_vs_tfidf_co": int(mf1 > baseline_co),
                "positive_vs_v2": int(mf1 > v2_mf1),
            })

    return results, delta_results, seed11_predictions


# ---------------------------------------------------------------------------
# Protocol B: Domain hold-out
# ---------------------------------------------------------------------------
def run_protocol_b(df, v3_features):
    print("\n=== Protocol B: Domain hold-out ===")
    domains = sorted(df["domain"].unique())
    results = []

    for held_domain in domains:
        train_mask = df["domain"] != held_domain
        test_mask = df["domain"] == held_domain
        train_idx = np.where(train_mask)[0]
        test_idx = np.where(test_mask)[0]

        y_train = df["y_escalation"].values[train_idx]
        y_test = df["y_escalation"].values[test_idx]

        print(f"  held_out={held_domain}: train={len(train_idx)}, test={len(test_idx)}")

        claim_train = df["claim_text"].iloc[train_idx].tolist()
        claim_test = df["claim_text"].iloc[test_idx].tolist()
        ce_train = (df["claim_text"] + " " + df["evidence_text"]).iloc[train_idx].tolist()
        ce_test = (df["claim_text"] + " " + df["evidence_text"]).iloc[test_idx].tolist()

        tfidf_claim_train, tfidf_claim_test = build_tfidf(claim_train, claim_test, "tfidf_claim_only")
        tfidf_ce_train, tfidf_ce_test = build_tfidf(ce_train, ce_test, "tfidf_claim_evidence")

        for config_name in CONFIG_NAMES:
            clf = LogisticRegression(
                class_weight="balanced", max_iter=3000, random_state=LR_RANDOM_STATE
            )

            if config_name == "tfidf_claim_only":
                X_train, X_test = tfidf_claim_train, tfidf_claim_test
            elif config_name == "tfidf_claim_evidence":
                X_train, X_test = tfidf_ce_train, tfidf_ce_test
            elif config_name == "v2_cross_encoder_nli_pair":
                X_train = v3_features["correct_nli"][train_idx]
                X_test = v3_features["correct_nli"][test_idx]
            elif config_name == "v3_cese_ocn_lite_delta_only":
                X_train = v3_features["delta_only"][train_idx]
                X_test = v3_features["delta_only"][test_idx]
            elif config_name == "v3_cese_ocn_lite_full":
                X_train = v3_features["v3_full"][train_idx]
                X_test = v3_features["v3_full"][test_idx]
            elif config_name == "v3_hybrid_tfidf_plus_cese_lite":
                X_train = sparse_hstack(
                    [tfidf_claim_train, csr_matrix(v3_features["v3_full"][train_idx])]
                )
                X_test = sparse_hstack(
                    [tfidf_claim_test, csr_matrix(v3_features["v3_full"][test_idx])]
                )

            clf.fit(X_train, y_train)
            y_pred = clf.predict(X_test)
            m = compute_metrics(y_test, y_pred)
            m["held_out_domain"] = held_domain
            m["config"] = config_name
            m["n_train"] = len(train_idx)
            m["n_test"] = len(test_idx)
            m["task"] = "escalation_binary"
            m["protocol"] = "domain_holdout"
            results.append(m)

    return results


# ---------------------------------------------------------------------------
# Protocol C: Evidence necessity audit
# ---------------------------------------------------------------------------
def run_protocol_c(df, v3_features, nli_data):
    print("\n=== Protocol C: Evidence necessity audit ===")
    delta_feats = v3_features["delta_only"]
    y = df["y_escalation"].values

    audit_rows = []
    for i in range(len(df)):
        row = {
            "candidate_id": df["candidate_id"].iloc[i],
            "group_id": df["target_candidate_group_id"].iloc[i],
            "domain": df["domain"].iloc[i],
            "y_escalation": int(y[i]),
        }
        for j, fname in enumerate(DELTA_FEATURE_NAMES):
            row[fname] = round(float(delta_feats[i, j]), 6)
        row["evidence_necessity_score"] = round(
            float(delta_feats[i, 0] + delta_feats[i, 3] + delta_feats[i, 6]), 6
        )
        audit_rows.append(row)

    audit_df = pd.DataFrame(audit_rows)

    # Margin statistics by class
    margin_stats = {}
    for fname in DELTA_FEATURE_NAMES + ["evidence_necessity_score"]:
        esc_vals = audit_df.loc[audit_df["y_escalation"] == 1, fname].values
        non_vals = audit_df.loc[audit_df["y_escalation"] == 0, fname].values
        margin_stats[fname] = {
            "escalation_mean": round(float(np.mean(esc_vals)), 6),
            "non_escalation_mean": round(float(np.mean(non_vals)), 6),
            "difference": round(float(np.mean(esc_vals) - np.mean(non_vals)), 6),
            "escalation_std": round(float(np.std(esc_vals)), 6),
            "non_escalation_std": round(float(np.std(non_vals)), 6),
        }

    # Top margin samples
    top_margin = audit_df.nlargest(10, "evidence_necessity_score")[
        ["candidate_id", "domain", "y_escalation", "evidence_necessity_score"]
    ].to_dict("records")

    # Anomalous: high necessity but non-escalation (or low necessity but escalation)
    anomalous_low = audit_df.nsmallest(10, "evidence_necessity_score")[
        ["candidate_id", "domain", "y_escalation", "evidence_necessity_score"]
    ].to_dict("records")

    summary = {
        "experiment": "cese_ocn_lite_v3_evidence_necessity_audit",
        "margin_stats": margin_stats,
        "top_margin_samples": top_margin,
        "anomalous_low_margin_samples": anomalous_low,
        "evidence_necessity_signal": any(
            abs(margin_stats[f]["difference"]) > 0.02 for f in DELTA_FEATURE_NAMES
        ),
    }

    return audit_df, summary


# ---------------------------------------------------------------------------
# Bootstrap CI
# ---------------------------------------------------------------------------
def run_bootstrap_ci(delta_results):
    print("\n=== Bootstrap CI ===")
    # Collect per-seed deltas for V3 full vs V2 and vs TF-IDF
    v3_full_deltas_v2 = []
    v3_full_deltas_tfidf = []
    for r in delta_results:
        if r["config"] == "v3_cese_ocn_lite_full":
            v3_full_deltas_v2.append(r["delta_vs_v2"])
            v3_full_deltas_tfidf.append(r["delta_vs_tfidf_co"])

    v3_full_deltas_v2 = np.array(v3_full_deltas_v2)
    v3_full_deltas_tfidf = np.array(v3_full_deltas_tfidf)

    rng = np.random.RandomState(42)
    n_bootstrap = 1000

    def bootstrap_ci(deltas):
        n = len(deltas)
        means = []
        for _ in range(n_bootstrap):
            sample = rng.choice(deltas, size=n, replace=True)
            means.append(np.mean(sample))
        means = np.array(means)
        return {
            "mean_delta": round(float(np.mean(deltas)), 4),
            "ci_lower": round(float(np.percentile(means, 2.5)), 4),
            "ci_upper": round(float(np.percentile(means, 97.5)), 4),
            "positive_seed_count": int(np.sum(deltas > 0)),
            "total_seeds": int(len(deltas)),
            "p_delta_le_zero": round(float(np.mean(means <= 0)), 4),
        }

    ci_v2 = bootstrap_ci(v3_full_deltas_v2)
    ci_tfidf = bootstrap_ci(v3_full_deltas_tfidf)

    summary = {
        "experiment": "cese_ocn_lite_v3_bootstrap_ci",
        "n_bootstrap": n_bootstrap,
        "comparisons": {
            "v3_full_vs_v2_cross_encoder_nli_pair": ci_v2,
            "v3_full_vs_tfidf_claim_only": ci_tfidf,
        },
    }
    return summary, ci_v2, ci_tfidf


# ---------------------------------------------------------------------------
# Report and decision gate
# ---------------------------------------------------------------------------
def aggregate_protocol_a(results):
    """Compute mean/std per config across seeds."""
    df = pd.DataFrame(results)
    agg = {}
    for config in CONFIG_NAMES:
        sub = df[df["config"] == config]
        agg[config] = {
            "macro_f1_mean": round(float(sub["macro_f1"].mean()), 4),
            "macro_f1_std": round(float(sub["macro_f1"].std()), 4),
            "macro_f1_min": round(float(sub["macro_f1"].min()), 4),
            "macro_f1_max": round(float(sub["macro_f1"].max()), 4),
            "accuracy_mean": round(float(sub["accuracy"].mean()), 4),
            "positive_f1_mean": round(float(sub["positive_f1"].mean()), 4),
        }
    return agg


def aggregate_domain_holdout(results):
    """Compute mean per config across domains."""
    df = pd.DataFrame(results)
    agg = {}
    for config in CONFIG_NAMES:
        sub = df[df["config"] == config]
        agg[config] = {
            "macro_f1_mean": round(float(sub["macro_f1"].mean()), 4),
            "macro_f1_std": round(float(sub["macro_f1"].std()), 4),
            "per_domain": {
                row["held_out_domain"]: row["macro_f1"]
                for _, row in sub.iterrows()
            },
        }
    return agg


def write_report(agg_a, agg_b, bootstrap_summary, ci_v2, ci_tfidf,
                 audit_summary, v3_full_vs_v2_positive, v3_full_vs_tfidf_positive):
    lines = []
    lines.append("# CESE-OCN-lite V3 Report: Evidence-Necessity Calibration")
    lines.append("")
    lines.append("> **Silver-label pilot. AI-preannotated. NOT gold, NOT human-audited.**")
    lines.append("> Frozen encoder only. No transformer fine-tuning. No LLM API.")
    lines.append("")

    lines.append("## 1. V3 Method Definition")
    lines.append("")
    lines.append("V3 upgrades V2 by adding evidence-necessity delta features. For each sample,")
    lines.append("NLI features are computed for 4 evidence conditions (correct, shuffled, empty,")
    lines.append("title), and delta features (correct minus shuffled/empty/title) encode how much")
    lines.append("the correct evidence matters. The core claim: the model needs CORRECT evidence")
    lines.append("to judge escalation, not just claim lexical patterns or NLI prior.")
    lines.append("")

    lines.append("## 2. Difference from V2")
    lines.append("")
    lines.append("| Aspect | V2 | V3 |")
    lines.append("|---|---|---|")
    lines.append("| Features | NLI(correct, claim) only | NLI(correct, claim) + delta vs shuffled/empty/title |")
    lines.append("| Feature dim | 7 | 19 (7 correct + 8 delta + 4 lexical) |")
    lines.append("| Core claim | Cross-encoder captures evidence signal | Model needs correct evidence; delta encodes necessity |")
    lines.append("| Evidence sensitivity | Implicit (sanity check separate) | Explicit (delta features in the model) |")
    lines.append("")

    lines.append("## 3. Data Status")
    lines.append("")
    lines.append(f"- Dataset: strict_silver_max_v1")
    lines.append(f"- 444 claims, 111 groups, 6 domains")
    lines.append(f"- Escalation: 222/222 (balanced)")
    lines.append(f"- Labels: AI-preannotated (candidate_label_guess). NOT gold, NOT human-audited.")
    lines.append(f"- human_audited=False, final_label=empty, gold_label=empty")
    lines.append("")

    lines.append("## 4. 10-Seed Results (Protocol A)")
    lines.append("")
    lines.append("| config | macro-F1 (mean) | std | min | max | acc | pos-F1 |")
    lines.append("|---|---|---|---|---|---|---|")
    for config in CONFIG_NAMES:
        a = agg_a[config]
        lines.append(
            f"| {config} | {a['macro_f1_mean']:.4f} | {a['macro_f1_std']:.4f} | "
            f"{a['macro_f1_min']:.4f} | {a['macro_f1_max']:.4f} | "
            f"{a['accuracy_mean']:.4f} | {a['positive_f1_mean']:.4f} |"
        )
    lines.append("")

    v3_full_mean = agg_a["v3_cese_ocn_lite_full"]["macro_f1_mean"]
    v2_mean = agg_a["v2_cross_encoder_nli_pair"]["macro_f1_mean"]
    tfidf_mean = agg_a["tfidf_claim_only"]["macro_f1_mean"]
    lines.append(f"**V3 full mean macro-F1**: {v3_full_mean:.4f}")
    lines.append(f"**V2 cross_encoder_nli_pair mean macro-F1**: {v2_mean:.4f}")
    lines.append(f"**TF-IDF claim-only mean macro-F1**: {tfidf_mean:.4f}")
    lines.append(f"**V3 full vs V2 delta**: {v3_full_mean - v2_mean:+.4f} ({v3_full_vs_v2_positive}/10 positive)")
    lines.append(f"**V3 full vs TF-IDF delta**: {v3_full_mean - tfidf_mean:+.4f} ({v3_full_vs_tfidf_positive}/10 positive)")
    lines.append("")

    lines.append("## 5. Domain Hold-Out Results (Protocol B)")
    lines.append("")
    lines.append("| config | macro-F1 (mean) | std |")
    lines.append("|---|---|---|")
    for config in CONFIG_NAMES:
        b = agg_b[config]
        lines.append(f"| {config} | {b['macro_f1_mean']:.4f} | {b['macro_f1_std']:.4f} |")
    lines.append("")

    v3_domain = agg_b["v3_cese_ocn_lite_full"]["macro_f1_mean"]
    v2_domain = agg_b["v2_cross_encoder_nli_pair"]["macro_f1_mean"]
    lines.append(f"**V3 full domain hold-out mean**: {v3_domain:.4f}")
    lines.append(f"**V2 domain hold-out mean**: {v2_domain:.4f}")
    lines.append(f"**Domain hold-out delta (V3 - V2)**: {v3_domain - v2_domain:+.4f}")
    lines.append("")

    lines.append("## 6. Bootstrap CI")
    lines.append("")
    lines.append("| comparison | mean delta | 95% CI | positive seeds | P(delta<=0) |")
    lines.append("|---|---|---|---|---|")
    lines.append(
        f"| V3 full vs V2 | {ci_v2['mean_delta']:+.4f} | "
        f"[{ci_v2['ci_lower']:+.4f}, {ci_v2['ci_upper']:+.4f}] | "
        f"{ci_v2['positive_seed_count']}/{ci_v2['total_seeds']} | "
        f"{ci_v2['p_delta_le_zero']:.4f} |"
    )
    lines.append(
        f"| V3 full vs TF-IDF | {ci_tfidf['mean_delta']:+.4f} | "
        f"[{ci_tfidf['ci_lower']:+.4f}, {ci_tfidf['ci_upper']:+.4f}] | "
        f"{ci_tfidf['positive_seed_count']}/{ci_tfidf['total_seeds']} | "
        f"{ci_tfidf['p_delta_le_zero']:.4f} |"
    )
    lines.append("")

    lines.append("## 7. Evidence Necessity Audit (Protocol C)")
    lines.append("")
    lines.append("Delta feature margin statistics (escalation vs non-escalation):")
    lines.append("")
    lines.append("| feature | escalation mean | non-esc mean | difference |")
    lines.append("|---|---|---|---|")
    for fname, stats in audit_summary["margin_stats"].items():
        lines.append(
            f"| {fname} | {stats['escalation_mean']:.4f} | "
            f"{stats['non_escalation_mean']:.4f} | {stats['difference']:+.4f} |"
        )
    lines.append("")
    lines.append(f"**evidence_necessity_signal**: {audit_summary['evidence_necessity_signal']}")
    lines.append("")

    lines.append("## 8. Does V3 Improve Over V2?")
    lines.append("")
    v3_better = v3_full_mean > v2_mean
    v3_stable = v3_full_vs_v2_positive >= 7
    ci_positive = ci_v2["ci_lower"] > 0
    lines.append(f"- V3 full macro-F1 > V2: {v3_full_mean:.4f} > {v2_mean:.4f} → **{'YES' if v3_better else 'NO'}**")
    lines.append(f"- V3 full >= 7/10 seeds positive vs V2: {v3_full_vs_v2_positive}/10 → **{'YES' if v3_stable else 'NO'}**")
    lines.append(f"- Bootstrap CI lower bound > 0: {ci_v2['ci_lower']:+.4f} → **{'YES' if ci_positive else 'NO'}**")
    lines.append("")

    lines.append("## 9. Should Paper Upgrade to V3?")
    lines.append("")
    if v3_better and v3_stable and ci_positive:
        lines.append("**YES** — V3 full improves over V2 with stable seeds and positive CI.")
    elif v3_better:
        lines.append("**PARTIAL** — V3 full mean is better but stability/CI not fully conclusive.")
    else:
        lines.append("**NO** — V3 full does not consistently improve over V2. V2 remains the main line.")
    lines.append("")

    lines.append("## 10. What We Still Cannot Claim")
    lines.append("")
    lines.append("- NOT gold benchmark (silver labels only, AI-preannotated)")
    lines.append("- NOT human-audited (no double annotation, no agreement)")
    lines.append("- NOT SOTA (no comparison with published methods)")
    lines.append("- NOT SCI tier-1 ready (pilot only, needs gold eval)")
    lines.append("- NOT final dataset (strict_silver_max_v1 is a pilot subset)")
    lines.append("- NOT CESE-OCN superiority (unless V3 proves it on gold)")
    lines.append("- NOT cross-domain generalizable (domain hold-out is exploratory)")
    lines.append("")

    (OUT_DIR / "cese_ocn_lite_v3_report.md").write_text("\n".join(lines), encoding="utf-8")


def write_decision_gate(agg_a, agg_b, ci_v2, ci_tfidf, audit_summary,
                        v3_full_vs_v2_positive, v3_full_vs_tfidf_positive):
    v3_full_mean = agg_a["v3_cese_ocn_lite_full"]["macro_f1_mean"]
    v2_mean = agg_a["v2_cross_encoder_nli_pair"]["macro_f1_mean"]
    tfidf_mean = agg_a["tfidf_claim_only"]["macro_f1_mean"]

    v3_domain = agg_b["v3_cese_ocn_lite_full"]["macro_f1_mean"]
    v2_domain = agg_b["v2_cross_encoder_nli_pair"]["macro_f1_mean"]

    v3_better = v3_full_mean > v2_mean
    v3_stable = v3_full_vs_v2_positive >= 7
    ci_positive = ci_v2["ci_lower"] > 0
    v3_improves = v3_better and v3_stable and ci_positive

    delta_only_mean = agg_a["v3_cese_ocn_lite_delta_only"]["macro_f1_mean"]
    delta_has_signal = delta_only_mean > 0.55

    gate = {
        "experiment": "cese_ocn_lite_v3",
        "v3_runs_completed": True,
        "n_claims": 444,
        "n_groups": 111,
        "n_domains": 6,
        "best_v3_config": "v3_cese_ocn_lite_full" if v3_full_mean >= delta_only_mean else "v3_cese_ocn_lite_delta_only",
        "best_v3_macro_f1": max(v3_full_mean, delta_only_mean),
        "v2_cross_encoder_macro_f1": v2_mean,
        "delta_vs_v2": round(v3_full_mean - v2_mean, 4),
        "delta_vs_v2_positive_seeds": v3_full_vs_v2_positive,
        "delta_vs_tfidf_claim_only": round(v3_full_mean - tfidf_mean, 4),
        "domain_holdout_v3_mean_macro_f1": v3_domain,
        "domain_holdout_delta_vs_v2": round(v3_domain - v2_domain, 4),
        "evidence_necessity_signal": audit_summary["evidence_necessity_signal"],
        "delta_only_has_independent_signal": delta_has_signal,
        "delta_only_macro_f1": delta_only_mean,
        "bootstrap_ci_v3_vs_v2": ci_v2,
        "bootstrap_ci_v3_vs_tfidf": ci_tfidf,
        "v3_improves_article_level": v3_improves,
        "recommended_paper_positioning": (
            "V3 evidence-necessity calibration pilot" if v3_improves
            else "V2 frozen NLI cross-encoder remains main line; V3 delta features are diagnostic"
        ),
        "recommended_next_step": (
            "upgrade paper to V3 main line + small gold eval" if v3_improves
            else "keep V2 as main line, use V3 delta features as evidence-necessity diagnostic + gold eval"
        ),
        "human_audited": False,
        "is_gold": False,
        "silver_label_source": "candidate_label_guess",
        "no_llm_called": True,
        "no_model_trained": True,
        "no_data_modified": True,
    }

    with open(OUT_DIR / "cese_ocn_lite_v3_decision_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)

    return gate


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=== CESE-OCN-lite V3 ===")
    print("  Loading data...")
    df = load_data()
    group_ids = df["target_candidate_group_id"].tolist()
    print(f"  Data: {len(df)} claims, {df['target_candidate_group_id'].nunique()} groups, {df['domain'].nunique()} domains")

    print("  Loading NLI model...")
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
    model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
    print(f"    id2label: {model.config.id2label}")

    print("  Precomputing NLI features (4 conditions × 444 pairs = 1776)...")
    nli_data = precompute_all_nli(df, model, tokenizer)

    print("  Building lexical features...")
    lexical = build_lexical_features(df)

    print("  Building V3 features...")
    v3_features = build_v3_features(nli_data, lexical)
    print(f"    correct_nli: {v3_features['correct_nli'].shape}")
    print(f"    delta_only: {v3_features['delta_only'].shape}")
    print(f"    v3_full: {v3_features['v3_full'].shape}")

    # Protocol A
    results_a, delta_results, seed11_pred = run_protocol_a(df, v3_features, group_ids)

    # Save Protocol A outputs
    pd.DataFrame(results_a).to_csv(OUT_DIR / "v3_by_seed.csv", index=False)
    pd.DataFrame(delta_results).to_csv(OUT_DIR / "v3_delta_by_seed.csv", index=False)
    if seed11_pred is not None:
        seed11_pred.to_csv(OUT_DIR / "v3_seed11_predictions.csv", index=False)

    # Protocol B
    results_b = run_protocol_b(df, v3_features)
    pd.DataFrame(results_b).to_csv(OUT_DIR / "v3_domain_holdout_results.csv", index=False)

    # Protocol C
    audit_df, audit_summary = run_protocol_c(df, v3_features, nli_data)
    audit_df.to_csv(OUT_DIR / "v3_evidence_necessity_audit.csv", index=False)
    with open(OUT_DIR / "v3_evidence_necessity_summary.json", "w", encoding="utf-8") as f:
        json.dump(audit_summary, f, indent=2, ensure_ascii=False)

    # Bootstrap CI
    bootstrap_summary, ci_v2, ci_tfidf = run_bootstrap_ci(delta_results)
    with open(OUT_DIR / "v3_bootstrap_ci_summary.json", "w", encoding="utf-8") as f:
        json.dump(bootstrap_summary, f, indent=2, ensure_ascii=False)

    # Bootstrap CI report
    ci_lines = [
        "# Bootstrap CI Report — V3 CESE-OCN-lite",
        "",
        f"Method: 1000 bootstrap resamples of 10 seed-level deltas.",
        "",
        "## V3 full vs V2 cross_encoder_nli_pair",
        f"- Mean delta: {ci_v2['mean_delta']:+.4f}",
        f"- 95% CI: [{ci_v2['ci_lower']:+.4f}, {ci_v2['ci_upper']:+.4f}]",
        f"- Positive seeds: {ci_v2['positive_seed_count']}/{ci_v2['total_seeds']}",
        f"- P(delta <= 0): {ci_v2['p_delta_le_zero']:.4f}",
        "",
        "## V3 full vs TF-IDF claim-only",
        f"- Mean delta: {ci_tfidf['mean_delta']:+.4f}",
        f"- 95% CI: [{ci_tfidf['ci_lower']:+.4f}, {ci_tfidf['ci_upper']:+.4f}]",
        f"- Positive seeds: {ci_tfidf['positive_seed_count']}/{ci_tfidf['total_seeds']}",
        f"- P(delta <= 0): {ci_tfidf['p_delta_le_zero']:.4f}",
        "",
    ]
    (OUT_DIR / "v3_bootstrap_ci_report.md").write_text("\n".join(ci_lines), encoding="utf-8")

    # Domain hold-out summary
    agg_b = aggregate_domain_holdout(results_b)
    with open(OUT_DIR / "v3_domain_holdout_summary.json", "w", encoding="utf-8") as f:
        json.dump(agg_b, f, indent=2, ensure_ascii=False)

    # Domain hold-out report
    dh_lines = [
        "# Domain Hold-Out Report — V3 CESE-OCN-lite",
        "",
        "> Silver-label pilot. NOT gold, NOT human-audited.",
        "",
        "## Mean macro-F1 by config",
        "",
        "| config | mean | std |",
        "|---|---|---|",
    ]
    for config in CONFIG_NAMES:
        b = agg_b[config]
        dh_lines.append(f"| {config} | {b['macro_f1_mean']:.4f} | {b['macro_f1_std']:.4f} |")
    dh_lines.append("")
    dh_lines.append("## Per-domain macro-F1")
    dh_lines.append("")
    dh_lines.append("| domain | V3 full | V2 NLI | TF-IDF co | delta-only |")
    dh_lines.append("|---|---|---|---|---|")
    domains_sorted = sorted(agg_b["v3_cese_ocn_lite_full"]["per_domain"].keys())
    for d in domains_sorted:
        dh_lines.append(
            f"| {d} | "
            f"{agg_b['v3_cese_ocn_lite_full']['per_domain'][d]:.4f} | "
            f"{agg_b['v2_cross_encoder_nli_pair']['per_domain'][d]:.4f} | "
            f"{agg_b['tfidf_claim_only']['per_domain'][d]:.4f} | "
            f"{agg_b['v3_cese_ocn_lite_delta_only']['per_domain'][d]:.4f} |"
        )
    dh_lines.append("")
    (OUT_DIR / "v3_domain_holdout_report.md").write_text("\n".join(dh_lines), encoding="utf-8")

    # Aggregate
    agg_a = aggregate_protocol_a(results_a)

    # V3 full vs V2 positive seeds
    v3_full_vs_v2_positive = sum(
        1 for r in delta_results
        if r["config"] == "v3_cese_ocn_lite_full" and r["positive_vs_v2"] == 1
    )
    v3_full_vs_tfidf_positive = sum(
        1 for r in delta_results
        if r["config"] == "v3_cese_ocn_lite_full" and r["positive_vs_tfidf_co"] == 1
    )

    # Write report
    write_report(agg_a, agg_b, bootstrap_summary, ci_v2, ci_tfidf,
                 audit_summary, v3_full_vs_v2_positive, v3_full_vs_tfidf_positive)

    # Write decision gate
    gate = write_decision_gate(
        agg_a, agg_b, ci_v2, ci_tfidf, audit_summary,
        v3_full_vs_v2_positive, v3_full_vs_tfidf_positive
    )

    # Write summary JSON
    summary = {
        "experiment": "cese_ocn_lite_v3",
        "n_claims": 444,
        "n_groups": 111,
        "n_domains": 6,
        "seeds": SEEDS,
        "nli_model": NLI_MODEL_NAME,
        "configs": CONFIG_NAMES,
        "protocol_a_aggregated": agg_a,
        "protocol_b_aggregated": agg_b,
        "protocol_c_summary": audit_summary,
        "bootstrap_ci": bootstrap_summary,
        "decision_gate": gate,
        "human_audited": False,
        "is_gold": False,
        "no_llm_called": True,
        "no_model_trained": True,
        "no_data_modified": True,
    }
    with open(OUT_DIR / "cese_ocn_lite_v3_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Print summary
    print("\n=== V3 Complete ===")
    print(f"  best_v3_config: {gate['best_v3_config']}")
    print(f"  best_v3_macro_f1: {gate['best_v3_macro_f1']}")
    print(f"  v2_macro_f1: {gate['v2_cross_encoder_macro_f1']}")
    print(f"  delta_vs_v2: {gate['delta_vs_v2']:+.4f} ({gate['delta_vs_v2_positive_seeds']}/10)")
    print(f"  v3_improves_article_level: {gate['v3_improves_article_level']}")
    print(f"  evidence_necessity_signal: {gate['evidence_necessity_signal']}")
    print(f"  domain_holdout_delta_vs_v2: {gate['domain_holdout_delta_vs_v2']:+.4f}")
    print(f"  output_dir: {OUT_DIR}")
    files = sorted(OUT_DIR.glob("*"))
    print(f"  files: {len(files)}")
    for f in files:
        print(f"    {f.name}")


if __name__ == "__main__":
    main()
