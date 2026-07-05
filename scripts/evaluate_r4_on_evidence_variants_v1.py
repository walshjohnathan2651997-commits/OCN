#!/usr/bin/env python
"""evaluate_r4_on_evidence_variants_v1.py — Frozen R4 evaluation on evidence variants.

Adapter that connects format-shift variant inputs to the frozen R4
screening pipeline. No training, no threshold changes, no API calls.

R4 cascade (per seed, frozen):
  1. contradiction: clf_contra(nli_features) > t_contra → contradiction_candidate
  2. strong_action: clf_strong(expert_features) > t_strong → strong_action_overclaim
  3. svm: clf_svm(svm_features) > t_svm → mild_scope_overclaim
  4. else → supported
  10-seed majority vote → final prediction

Anti-leakage:
  - true_label loaded ONLY for metrics, never enters prediction path
  - no label fields used for feature computation or routing
  - oracle_hit not used for prediction
"""

import argparse
import csv
import hashlib
import json
import os
import pickle
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG = {
    "r4_mode": "frozen",
    "no_train": True,
    "no_api": True,
    "no_network": True,
    "no_threshold_change": True,
    "n_seeds": 10,
    "seeds": [11, 22, 33, 44, 55, 66, 77, 88, 99, 111],
    "nli_model_name": "cross-encoder/nli-deberta-base",
    "r4_artifacts_dir": "experiments/r4_minimal_recovery_v1/artifacts",
    "nli_cache_path": "experiments/canonical_selector_robustness_v1/nli_top5_cache.npz",
    "nli_cache_meta": "experiments/canonical_selector_robustness_v1/nli_top5_cache_meta.csv",
    "review_scores_path": "experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv",
    "batch_size": 32,
}

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
LABEL_TO_IDX = {lab: i for i, lab in enumerate(LABELS_4)}
IDX_TO_LABEL = {i: lab for i, lab in enumerate(LABELS_4)}
STRONG_LABEL = "strong_action_overclaim"

# Feature group names (must match feature_columns.json)
NLI_FEATURE_NAMES = [
    "entailment_correct", "neutral_correct", "contradiction_correct",
    "ent_minus_con_correct", "con_minus_ent_correct", "max_prob_correct", "entropy_correct",
]
ACTION_GAP_NAMES = [
    "action_escalation_gap", "claim_action_strength", "evidence_action_support",
    "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
    "length_diff", "claim_evidence_overlap",
]

# Lexicons (copied exactly from run_canonicalized_review_queue_v1.py)
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

FORBIDDEN_PREDICTION_FIELDS = {
    "true_label", "candidate_label_guess", "gold_label", "human_audited",
    "oracle_hit", "final_label", "issue_binary_label_guess",
    "escalation_binary_label_guess", "contradiction_binary_label_guess",
}


def log(msg):
    print(msg, flush=True)


def sha256_text(text):
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def count_terms(text, terms):
    text_lower = str(text).lower()
    return sum(1 for t in terms if t.lower() in text_lower)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_variant_inputs(csv_path):
    """Load format_shift_inputs.csv. No label fields read."""
    variants = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            variants.append({
                "candidate_id": row["candidate_id"],
                "variant": row["variant"],
                "evidence_input": row["evidence_input"],
                "evidence_input_sha256": row.get("evidence_input_sha256", sha256_text(row["evidence_input"])),
                "n_words": int(row.get("n_words", 0)) if str(row.get("n_words", "")).isdigit() else 0,
                "source": row.get("source", ""),
                "uses_oracle_text": row.get("uses_oracle_text", "") in ("True", "true", "1"),
                "contains_metadata": row.get("contains_metadata", "") in ("True", "true", "1"),
                "is_lengthened": row.get("is_lengthened", "") in ("True", "true", "1"),
            })
    return variants


def load_true_labels(review_scores_path, candidate_csv_path=None):
    """Load true_label for metrics ONLY. Returns dict: candidate_id -> true_label."""
    labels = {}
    path = Path(review_scores_path)
    if path.exists():
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                labels[row["candidate_id"]] = row.get("true_label", "")
    if candidate_csv_path and Path(candidate_csv_path).exists():
        with open(candidate_csv_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                cid = row["candidate_id"]
                if cid not in labels:
                    lab = row.get("final_label", "") or row.get("gold_label", "")
                    if lab:
                        labels[cid] = lab
    return labels


def load_claim_text(candidate_csv_path):
    """Load claim_text per candidate. Needed for feature computation."""
    claims = {}
    with open(candidate_csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            claims[row["candidate_id"]] = row.get("claim_text", "")
    return claims


# ---------------------------------------------------------------------------
# Feature computation
# ---------------------------------------------------------------------------

def compute_nli_features(pairs, model_name, batch_size=32):
    """Compute 7 NLI features for (evidence, claim) pairs.
    Returns array of shape (n_pairs, 7).
    """
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    import torch
    from torch.nn.functional import softmax

    log(f"  Loading NLI model: {model_name}")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name)
    model.eval()

    all_features = []
    with torch.no_grad():
        for start in range(0, len(pairs), batch_size):
            batch = pairs[start: start + batch_size]
            premises = [str(p) for p, _ in batch]
            hypotheses = [str(h) for _, h in batch]
            enc = tokenizer(premises, hypotheses, padding=True, truncation=True,
                            max_length=512, return_tensors="pt")
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
                log(f"    NLI progress: {start}/{len(pairs)}")

    return np.vstack(all_features)


def build_action_gap_features(claims, evidences):
    """Compute 9 action-gap features. Returns DataFrame-like dict of arrays."""
    n = len(claims)
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity

    claims_arr = [str(c) for c in claims]
    evidences_arr = [str(e) for e in evidences]

    vec = TfidfVectorizer(ngram_range=(1, 1), min_df=1, stop_words="english")
    vec.fit(claims_arr + evidences_arr)
    claim_tfidf = vec.transform(claims_arr)
    evidence_tfidf = vec.transform(evidences_arr)
    overlap = np.array([
        cosine_similarity(claim_tfidf[i], evidence_tfidf[i])[0, 0]
        for i in range(n)
    ])

    action_escalation_gap = []
    claim_action_strength = []
    evidence_action_support = []
    deployment_gap = []
    metric_to_action_gap = []
    certainty_gap = []
    scope_gap = []
    length_diff = []
    claim_evidence_overlap = overlap.tolist()

    for i in range(n):
        c = claims_arr[i]
        e = evidences_arr[i]
        cas = count_terms(c, CLAIM_ACTION_TERMS)
        eas = count_terms(e, EVIDENCE_ACTION_SUPPORT_TERMS)
        claim_action_strength.append(cas)
        evidence_action_support.append(eas)
        action_escalation_gap.append(cas - eas)
        deployment_gap.append(count_terms(c, DEPLOYMENT_TERMS) - count_terms(e, DEPLOYMENT_TERMS))
        metric_to_action_gap.append(cas - count_terms(e, METRIC_TERMS))
        certainty_gap.append(count_terms(c, CERTAINTY_TERMS) - count_terms(e, CERTAINTY_TERMS))
        scope_gap.append(count_terms(c, SCOPE_TERMS) - count_terms(e, SCOPE_TERMS))
        length_diff.append(len(c) - len(e))

    return {
        "action_escalation_gap": action_escalation_gap,
        "claim_action_strength": claim_action_strength,
        "evidence_action_support": evidence_action_support,
        "deployment_gap": deployment_gap,
        "metric_to_action_gap": metric_to_action_gap,
        "certainty_gap": certainty_gap,
        "scope_gap": scope_gap,
        "length_diff": length_diff,
        "claim_evidence_overlap": claim_evidence_overlap,
    }


# ---------------------------------------------------------------------------
# R4 frozen artifacts
# ---------------------------------------------------------------------------

def load_r4_artifacts(artifacts_dir):
    """Load all R4 artifacts for 10 seeds. Returns dict: seed -> artifacts."""
    artifacts = {}
    artifacts_path = Path(artifacts_dir)
    if not artifacts_path.exists():
        log(f"  WARNING: R4 artifacts dir not found: {artifacts_dir}")
        return artifacts

    for seed in CONFIG["seeds"]:
        seed_dir = artifacts_path / f"seed_{seed}"
        if not seed_dir.exists():
            log(f"  WARNING: seed dir not found: {seed_dir}")
            continue
        seed_artifacts = {}
        for name in ["clf_contra", "clf_strong", "clf_svm", "scaler_contra", "scaler_strong", "scaler_svm"]:
            pkl_path = seed_dir / f"{name}.pkl"
            if pkl_path.exists():
                with open(pkl_path, "rb") as f:
                    seed_artifacts[name] = pickle.load(f)
        thresh_path = seed_dir / "thresholds.json"
        if thresh_path.exists():
            with open(thresh_path, "r", encoding="utf-8") as f:
                seed_artifacts["thresholds"] = json.load(f)
        feat_path = seed_dir / "feature_columns.json"
        if feat_path.exists():
            with open(feat_path, "r", encoding="utf-8") as f:
                seed_artifacts["feature_columns"] = json.load(f)
        if seed_artifacts:
            artifacts[seed] = seed_artifacts
    return artifacts


def route_r4_single_seed(nli_feats, action_gap_dict, seed_artifacts):
    """Route through R4 cascade for a single seed. Returns (pred_label, p_contra, p_strong, p_svm, strong_flag)."""
    thresholds = seed_artifacts["thresholds"]
    t_contra = thresholds.get("t_contra", 0.48)
    t_strong = thresholds.get("t_strong", 0.535)
    t_svm = thresholds.get("t_svm", 0.51)

    # NLI features (7)
    nli_arr = np.array(nli_feats).reshape(1, -1)

    # Contradiction: uses nli_features
    scaler_contra = seed_artifacts["scaler_contra"]
    clf_contra = seed_artifacts["clf_contra"]
    nli_scaled = scaler_contra.transform(nli_arr)
    p_contra = float(clf_contra.predict_proba(nli_scaled)[0, 1])

    if p_contra >= t_contra:
        return "contradiction_candidate", p_contra, 0.0, 0.0, 0

    # Strong action: uses expert_features (16 = 7 nli + 9 action gaps)
    expert_feats = np.concatenate([
        nli_arr[0],
        np.array([
            action_gap_dict["action_escalation_gap"],
            action_gap_dict["claim_action_strength"],
            action_gap_dict["evidence_action_support"],
            action_gap_dict["deployment_gap"],
            action_gap_dict["metric_to_action_gap"],
            action_gap_dict["certainty_gap"],
            action_gap_dict["scope_gap"],
            action_gap_dict["length_diff"],
            action_gap_dict["claim_evidence_overlap"],
        ])
    ]).reshape(1, -1)

    scaler_strong = seed_artifacts["scaler_strong"]
    clf_strong = seed_artifacts["clf_strong"]
    expert_scaled = scaler_strong.transform(expert_feats)
    p_strong = float(clf_strong.predict_proba(expert_scaled)[0, 1])

    if p_strong >= t_strong:
        return "strong_action_overclaim", p_contra, p_strong, 0.0, 1

    # SVM: uses svm_features (8 = 7 nli + scope_gap)
    svm_feats = np.concatenate([
        nli_arr[0],
        np.array([action_gap_dict["scope_gap"]])
    ]).reshape(1, -1)

    scaler_svm = seed_artifacts["scaler_svm"]
    clf_svm = seed_artifacts["clf_svm"]
    svm_scaled = scaler_svm.transform(svm_feats)
    p_svm = float(clf_svm.predict_proba(svm_scaled)[0, 1])

    if p_svm >= t_svm:
        return "mild_scope_overclaim", p_contra, p_strong, p_svm, 0

    return "supported", p_contra, p_strong, p_svm, 0


def predict_with_r4_majority_vote(nli_feats, action_gap_dict, r4_artifacts):
    """Run R4 across all seeds and majority vote. Returns aggregated prediction."""
    votes = []
    p_contras = []
    p_strongs = []
    p_svms = []
    strong_flags = []

    for seed, seed_art in r4_artifacts.items():
        pred, p_c, p_s, p_sv, flag = route_r4_single_seed(nli_feats, action_gap_dict, seed_art)
        votes.append(pred)
        p_contras.append(p_c)
        p_strongs.append(p_s)
        p_svms.append(p_sv)
        strong_flags.append(flag)

    vote_counts = Counter(votes)
    final_pred = vote_counts.most_common(1)[0][0]

    return {
        "pred_label": final_pred,
        "p_contra": round(float(np.mean(p_contras)), 6),
        "p_strong": round(float(np.mean(p_strongs)), 6),
        "p_svm": round(float(np.mean(p_svms)), 6),
        "strong_action_flag": int(np.mean(strong_flags) > 0.5),
        "entropy": round(float(np.mean([
            -p * np.log(p + 1e-10) for p in [len([v for v in votes if v == lab]) / len(votes) for lab in LABELS_4]
        ])), 6) if votes else 0.0,
        "n_seeds_voted": len(votes),
    }


# ---------------------------------------------------------------------------
# Toy R4 simulator (for toy_mode only)
# ---------------------------------------------------------------------------

_TOK_RE = re.compile(r"[a-z0-9]+")
_TOK_STOP = {"a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}


def _tok(text):
    return [w for w in _TOK_RE.findall(text.lower()) if w not in _TOK_STOP]


def toy_r4_predict(claim_text, evidence_input):
    """Simplified R4 simulator for toy_mode. Uses token overlap as proxy."""
    if not evidence_input or not claim_text:
        return {"pred_label": "supported", "p_contra": 0.1, "p_strong": 0.1, "p_svm": 0.3,
                "strong_action_flag": 0, "entropy": 1.0, "n_seeds_voted": 10}

    ct = set(_tok(claim_text))
    et = set(_tok(evidence_input))
    overlap = len(ct & et) / max(len(ct | et), 1)

    action_terms = sum(1 for t in ["deploy", "production", "safe", "guarantee", "must", "always"] if t in evidence_input.lower())

    p_contra = max(0.05, 0.3 - overlap * 0.5)
    p_strong = min(0.9, 0.2 + action_terms * 0.15)
    p_svm = 0.3 + overlap * 0.2

    if p_contra > 0.25:
        pred = "contradiction_candidate"
    elif p_strong > 0.4:
        pred = "strong_action_overclaim"
    elif p_svm > 0.4:
        pred = "mild_scope_overclaim"
    else:
        pred = "supported"

    strong_flag = 1 if pred == "strong_action_overclaim" else 0
    entropy = round(-sum(p * np.log(p + 1e-10) for p in [0.25, 0.25, 0.25, 0.25]), 6)

    return {"pred_label": pred, "p_contra": round(p_contra, 6), "p_strong": round(p_strong, 6),
            "p_svm": round(p_svm, 6), "strong_action_flag": strong_flag, "entropy": entropy,
            "n_seeds_voted": 10}


# ---------------------------------------------------------------------------
# Metrics
# ---------------------------------------------------------------------------

def compute_variant_metrics(predictions, true_labels):
    """Compute metrics for a variant. true_label used ONLY here."""
    from sklearn.metrics import f1_score, precision_score, recall_score

    variant_preds = defaultdict(list)
    variant_trues = defaultdict(list)

    for p in predictions:
        cid = p["candidate_id"]
        variant = p["variant"]
        true = true_labels.get(cid, "")
        if not true:
            continue
        variant_preds[variant].append(p["pred_label"])
        variant_trues[variant].append(true)

    metrics = {}
    for variant in variant_preds:
        preds = variant_preds[variant]
        trues = variant_trues[variant]
        n = len(preds)

        strong_preds = [1 if p == STRONG_LABEL else 0 for p in preds]
        strong_trues = [1 if t == STRONG_LABEL else 0 for t in trues]

        if n > 0 and len(set(strong_trues)) > 1:
            strong_f1 = round(f1_score(strong_trues, strong_preds, zero_division=0), 6)
            strong_prec = round(precision_score(strong_trues, strong_preds, zero_division=0), 6)
            strong_rec = round(recall_score(strong_trues, strong_preds, zero_division=0), 6)
        else:
            strong_f1 = 0.0
            strong_prec = 0.0
            strong_rec = 0.0

        labels_present = set(trues) | set(preds)
        label_subset = [l for l in LABELS_4 if l in labels_present]
        if n > 0 and len(label_subset) > 1:
            macro_f1 = round(f1_score(trues, preds, labels=label_subset, average="macro", zero_division=0), 6)
        else:
            macro_f1 = 0.0

        metrics[variant] = {
            "variant": variant,
            "strong_F1": strong_f1,
            "strong_precision": strong_prec,
            "strong_recall": strong_rec,
            "macro_F1": macro_f1,
            "n_eval": n,
        }
    return metrics


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_predictions_csv(filepath, predictions):
    fields = ["candidate_id", "variant", "pred_label", "p_strong", "p_contra",
              "p_svm", "strong_action_flag", "entropy"]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for p in predictions:
            writer.writerow({k: p[k] for k in fields})


def write_metrics_csv(filepath, metrics_list, baseline_oracle="oracle_clean", baseline_raw="raw_bm25_top1_chunk"):
    fields = ["variant", "strong_F1", "strong_precision", "strong_recall", "macro_F1",
              "n_eval", "delta_vs_oracle_clean", "delta_vs_raw_bm25_top1"]
    oracle_f1 = metrics_list.get(baseline_oracle, {}).get("strong_F1", 0.0) if isinstance(metrics_list, dict) else 0.0
    raw_f1 = metrics_list.get(baseline_raw, {}).get("strong_F1", 0.0) if isinstance(metrics_list, dict) else 0.0

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for variant, m in (metrics_list.items() if isinstance(metrics_list, dict) else [(m["variant"], m) for m in metrics_list]):
            row = {
                "variant": variant,
                "strong_F1": m["strong_F1"],
                "strong_precision": m["strong_precision"],
                "strong_recall": m["strong_recall"],
                "macro_F1": m["macro_F1"],
                "n_eval": m["n_eval"],
                "delta_vs_oracle_clean": round(m["strong_F1"] - oracle_f1, 6),
                "delta_vs_raw_bm25_top1": round(m["strong_F1"] - raw_f1, 6),
            }
            writer.writerow(row)


def write_summary_json(filepath, metrics, predictions, n_candidates):
    oracle_f1 = metrics.get("oracle_clean", {}).get("strong_F1", 0.0)
    raw_f1 = metrics.get("raw_bm25_top1_chunk", {}).get("strong_F1", 0.0)
    canon_f1 = metrics.get("canonicalized_best_sentence_top5", {}).get("strong_F1", 0.0)
    lengthened_f1 = metrics.get("oracle_lengthened", {}).get("strong_F1", 0.0)
    metadata_f1 = metrics.get("oracle_plus_metadata", {}).get("strong_F1", 0.0)

    best_variant = max(metrics.keys(), key=lambda v: metrics[v]["strong_F1"]) if metrics else ""

    summary = {
        "best_variant": best_variant,
        "raw_chunk_drop": round(raw_f1 - canon_f1, 6),
        "canonicalization_gain": round(canon_f1 - raw_f1, 6),
        "lengthening_drop": round(oracle_f1 - lengthened_f1, 6),
        "metadata_drop": round(oracle_f1 - metadata_f1, 6),
        "no_training": CONFIG["no_train"],
        "no_api": CONFIG["no_api"],
        "no_network": CONFIG["no_network"],
        "no_threshold_change": CONFIG["no_threshold_change"],
        "r4_mode": CONFIG["r4_mode"],
        "n_seeds": CONFIG["n_seeds"],
        "n_candidates": n_candidates,
        "oracle_clean_is_diagnostic": True,
        "canonicalized_best_sentence_top5_is_production": True,
        "true_label_used_only_for_metrics": True,
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)


def write_failure_examples_csv(filepath, predictions, true_labels, variant_inputs_lookup):
    """Write failure examples: cases where variant_a and variant_b disagree."""
    by_cand_variant = {}
    for p in predictions:
        key = (p["candidate_id"], p["variant"])
        by_cand_variant[key] = p

    pairs = [
        ("oracle_clean", "oracle_lengthened"),
        ("oracle_clean", "oracle_plus_metadata"),
        ("raw_bm25_top1_chunk", "canonicalized_best_sentence_top5"),
    ]

    fields = ["candidate_id", "variant_a", "variant_b", "true_label",
              "pred_a", "pred_b", "evidence_hash_a", "evidence_hash_b",
              "n_words_a", "n_words_b", "comment_auto"]

    rows = []
    for cid in sorted(true_labels.keys()):
        true = true_labels[cid]
        for va, vb in pairs:
            pa = by_cand_variant.get((cid, va))
            pb = by_cand_variant.get((cid, vb))
            if not pa or not pb:
                continue
            if pa["pred_label"] != pb["pred_label"]:
                inp_a = variant_inputs_lookup.get((cid, va), {})
                inp_b = variant_inputs_lookup.get((cid, vb), {})
                comment = f"{va}={pa['pred_label']} vs {vb}={pb['pred_label']}"
                if true:
                    a_correct = "✓" if pa["pred_label"] == true else "✗"
                    b_correct = "✓" if pb["pred_label"] == true else "✗"
                    comment += f" | true={true} | {va}{a_correct} {vb}{b_correct}"
                rows.append({
                    "candidate_id": cid,
                    "variant_a": va,
                    "variant_b": vb,
                    "true_label": true,
                    "pred_a": pa["pred_label"],
                    "pred_b": pb["pred_label"],
                    "evidence_hash_a": inp_a.get("evidence_input_sha256", ""),
                    "evidence_hash_b": inp_b.get("evidence_input_sha256", ""),
                    "n_words_a": inp_a.get("n_words", 0),
                    "n_words_b": inp_b.get("n_words", 0),
                    "comment_auto": comment,
                })
                if len(rows) >= 100:
                    break
        if len(rows) >= 100:
            break

    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def write_leakage_guard(filepath):
    report = {
        "forbidden_fields_for_prediction": sorted(FORBIDDEN_PREDICTION_FIELDS),
        "used_for_prediction": ["claim_text", "evidence_input"],
        "true_label_used_for_prediction": False,
        "true_label_used_for_metrics_only": True,
        "oracle_used_for_prediction": False,
        "no_training": CONFIG["no_train"],
        "no_api": CONFIG["no_api"],
        "no_threshold_change": CONFIG["no_threshold_change"],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Frozen R4 evaluation on evidence variants."
    )
    parser.add_argument("--variant_inputs_csv", default=None)
    parser.add_argument("--candidate_csv", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--r4_mode", default="frozen")
    parser.add_argument("--no_train", default="true")
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    # --- Load config ---
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    CONFIG["r4_mode"] = args.r4_mode
    CONFIG["no_train"] = args.no_train.lower() in ("true", "1", "yes")

    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.toy_mode:
        output_dir = Path("experiments/format_shift_ablation_v1_toy")
    else:
        output_dir = Path("experiments/format_shift_ablation_v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        variant_inputs_csv = "experiments/format_shift_ablation_v1_toy/format_shift_inputs.csv"
        candidate_csv = "data/toy_synthetic/toy_candidates_v1.csv"
        print("[toy_mode] Using toy inputs")
    else:
        variant_inputs_csv = args.variant_inputs_csv or "experiments/format_shift_ablation_v1/format_shift_inputs.csv"
        candidate_csv = args.candidate_csv or str(resolve_path(config, "candidate_csv") or "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv")

    # --- Load inputs ---
    print(f"Loading variant inputs from {variant_inputs_csv}")
    variants = load_variant_inputs(variant_inputs_csv)
    print(f"  {len(variants)} variant rows loaded")

    print(f"Loading claim_text from {candidate_csv}")
    claim_text_lookup = load_claim_text(candidate_csv)
    print(f"  {len(claim_text_lookup)} candidates with claim_text")

    # Build variant_inputs lookup for failure examples
    variant_inputs_lookup = {}
    for v in variants:
        variant_inputs_lookup[(v["candidate_id"], v["variant"])] = v

    # --- Load true_label for metrics ONLY ---
    if args.toy_mode:
        toy_labels = [
            "supported", "strong_action_overclaim", "strong_action_overclaim",
            "mild_scope_overclaim", "supported", "contradiction_candidate"
        ]
        true_labels = {f"toy_cand_{i+1:03d}": lab for i, lab in enumerate(toy_labels)}
        print(f"  [toy_mode] Assigned synthetic true_labels for {len(true_labels)} candidates (for metrics testing only)")
    else:
        true_labels = load_true_labels(CONFIG["review_scores_path"], candidate_csv)
    print(f"  {len(true_labels)} true_labels loaded (for metrics only)")

    # --- R4 evaluation ---
    if args.toy_mode:
        print("\n[toy_mode] Running toy R4 simulator ...")
        predictions = []
        for v in variants:
            claim = claim_text_lookup.get(v["candidate_id"], "")
            pred = toy_r4_predict(claim, v["evidence_input"])
            pred["candidate_id"] = v["candidate_id"]
            pred["variant"] = v["variant"]
            predictions.append(pred)
    else:
        print("\nLoading R4 frozen artifacts ...")
        r4_artifacts = load_r4_artifacts(CONFIG["r4_artifacts_dir"])
        print(f"  {len(r4_artifacts)} seeds loaded")

        if not r4_artifacts:
            print("  ERROR: No R4 artifacts found. Cannot run frozen R4 evaluation.")
            print("  Falling back to toy simulator (diagnostic only).")
            predictions = []
            for v in variants:
                claim = claim_text_lookup.get(v["candidate_id"], "")
                pred = toy_r4_predict(claim, v["evidence_input"])
                pred["candidate_id"] = v["candidate_id"]
                pred["variant"] = v["variant"]
                predictions.append(pred)
        else:
            # Compute NLI features
            pairs = []
            pair_meta = []
            for v in variants:
                claim = claim_text_lookup.get(v["candidate_id"], "")
                pairs.append((v["evidence_input"], claim))
                pair_meta.append(v)

            print(f"\nComputing NLI features for {len(pairs)} pairs ...")
            nli_features = compute_nli_features(pairs, CONFIG["nli_model_name"], CONFIG["batch_size"])
            print(f"  NLI features shape: {nli_features.shape}")

            # Compute action-gap features
            print("Computing action-gap features ...")
            claims_list = [p[1] for p in pairs]
            evidences_list = [p[0] for p in pairs]
            ag_features = build_action_gap_features(claims_list, evidences_list)

            # Predict
            print("Running R4 cascade (10-seed majority vote) ...")
            predictions = []
            for i, v in enumerate(pair_meta):
                ag_dict = {k: ag_features[k][i] for k in ag_features}
                pred = predict_with_r4_majority_vote(nli_features[i], ag_dict, r4_artifacts)
                pred["candidate_id"] = v["candidate_id"]
                pred["variant"] = v["variant"]
                predictions.append(pred)
                if (i + 1) % 100 == 0:
                    print(f"  Progress: {i+1}/{len(pair_meta)}")

    # --- Compute metrics ---
    print("\nComputing metrics (true_label used here only) ...")
    metrics = compute_variant_metrics(predictions, true_labels)

    for variant in sorted(metrics.keys()):
        m = metrics[variant]
        print(f"  {variant}: strong_F1={m['strong_F1']}, macro_F1={m['macro_F1']}, n={m['n_eval']}")

    # --- Write outputs ---
    pred_csv = output_dir / "format_shift_predictions.csv"
    write_predictions_csv(pred_csv, predictions)
    print(f"\nWrote {pred_csv}")

    metrics_csv = output_dir / "format_shift_metrics.csv"
    write_metrics_csv(metrics_csv, metrics)
    print(f"Wrote {metrics_csv}")

    summary_json = output_dir / "format_shift_summary.json"
    write_summary_json(summary_json, metrics, predictions, len(claim_text_lookup))
    print(f"Wrote {summary_json}")

    failure_csv = output_dir / "format_shift_failure_examples_redacted.csv"
    write_failure_examples_csv(failure_csv, predictions, true_labels, variant_inputs_lookup)
    print(f"Wrote {failure_csv}")

    guard_json = output_dir / "r4_leakage_guard_report.json"
    write_leakage_guard(guard_json)
    print(f"Wrote {guard_json}")

    write_run_config(output_dir, config, "evaluate_r4_on_evidence_variants_v1.py",
                     extra={"toy_mode": args.toy_mode, "r4_mode": args.r4_mode})
    print(f"Wrote run_config.json")

    print("\nDone.")


if __name__ == "__main__":
    main()
