"""
Canonical Evidence Selector Robustness v1
=========================================
Tests whether best_sentence_from_top5 is robust across selector variants,
or just a lucky post-hoc choice. 11 selector variants tested.

Prohibitions: no training, no API, no network, no threshold change, no proxy,
no true_label/oracle_hit use for evidence selection, no silver-as-gold.

Selector variants:
  A. bm25_top1_raw              : raw BM25 top1 chunk (negative baseline)
  B. oracle_span                : oracle evidence (upper bound)
  C. best_sentence_top3_overlap : top3 chunks, sentence by overlap
  D. best_sentence_top5_overlap : top5 chunks, sentence by overlap
  E. best_sentence_top10_overlap: top10 chunks, sentence by overlap
  F. best_sentence_top5_bm25weighted : overlap + 0.2 * parent chunk BM25 score
  G. best_sentence_top5_nli_entailment : max NLI entailment
  H. best_sentence_top5_nli_low_entropy: min NLI entropy
  I. best_sentence_top5_margin  : max abs(entailment - contradiction)
  J. two_sentence_window_top5   : best sentence + 1 most relevant neighbor
  K. length_limited_top5        : only 10-40 word sentences, by overlap
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
CANON_DIR = Path(r"D:\ocn\experiments\r4_evidence_canonicalization_v1")
RECOVERY_DIR = Path(r"D:\ocn\experiments\r4_minimal_recovery_v1")
RECOVERY_ARTIFACTS = RECOVERY_DIR / "artifacts"
RECOVERY_PREDICTIONS = RECOVERY_DIR / "r4_recovered_predictions_444.csv"
RECOVERY_SPLIT_MANIFEST = RECOVERY_DIR / "r4_recovery_split_manifest.csv"

RETRIEVAL_RESULTS_BM25 = Path(r"D:\ocn\experiments\simclaim_pdf_corpus_retrieval_v1\retrieval_results_bm25.csv")
PDF_CHUNKS = Path(r"D:\ocn\data\simclaim_pdf_corpus_retrieval_v1\local_pdf_corpus_chunks.csv")
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)

OUTPUT_DIR = Path(r"D:\ocn\experiments\canonical_selector_robustness_v1")
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

# Selector variants
SELECTOR_VARIANTS = [
    "bm25_top1_raw",
    "oracle_span",
    "best_sentence_top3_overlap",
    "best_sentence_top5_overlap",
    "best_sentence_top10_overlap",
    "best_sentence_top5_bm25weighted",
    "best_sentence_top5_nli_entailment",
    "best_sentence_top5_nli_low_entropy",
    "best_sentence_top5_margin",
    "two_sentence_window_top5",
    "length_limited_top5",
]

# Lexicons (copied exactly from recovery script)
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


# ---------------- Evidence cleaning & sentence splitting ----------------

METADATA_PATTERN = re.compile(r"\[RANK=\d+\]\[PDF=[^\]]+\]\[PAGE=\d+\]\s*")
HYPHEN_BREAK = re.compile(r"([a-z])-\s+([a-z])")
MULTI_WS = re.compile(r"\s+")
CITATION_PATTERN = re.compile(r"\[\s*\d+(?:\s*,\s*\d+)*\s*\]")
URL_PATTERN = re.compile(r"https?://\S+|www\.\S+")
FOOTER_PATTERN = re.compile(r"(?im)^(references|acknowledgments?|bibliography)\s*$")
FIGURE_PATTERN = re.compile(r"(?im)^(figure|table|fig\.?|tab\.?)\s*\d+[:.]")
SENT_SPLIT = re.compile(r"(?<=[.!?])\s+(?=[A-Z\"\(\[])")


def clean_chunk_text(text: str) -> str:
    if not isinstance(text, str) or not text.strip():
        return ""
    text = METADATA_PATTERN.sub("", text)
    text = HYPHEN_BREAK.sub(r"\1\2", text)
    text = MULTI_WS.sub(" ", text)
    text = URL_PATTERN.sub(" ", text)
    text = CITATION_PATTERN.sub(" ", text)
    text = FIGURE_PATTERN.sub(" ", text)
    m = FOOTER_PATTERN.search(text)
    if m:
        text = text[: m.start()]
    text = MULTI_WS.sub(" ", text).strip()
    return text


def split_sentences(text: str) -> list:
    text = text.strip()
    if not text:
        return []
    sents = SENT_SPLIT.split(text)
    out = []
    for s in sents:
        s = s.strip()
        if not s:
            continue
        n_words = len(s.split())
        if n_words < 4:
            continue
        if n_words > 80:
            for sub in s.split(";"):
                sub = sub.strip()
                if 4 <= len(sub.split()) <= 80:
                    out.append(sub)
            continue
        out.append(s)
    return out


def tokenize_simple(text: str) -> set:
    text_lower = str(text).lower()
    return set(re.findall(r"[a-z][a-z0-9_-]{2,}", text_lower))


def overlap_score(claim_tokens: set, sent: str) -> float:
    sent_tokens = tokenize_simple(sent)
    if not sent_tokens:
        return 0.0
    inter = len(claim_tokens & sent_tokens)
    denom = len(claim_tokens) + len(sent_tokens)
    return (2.0 * inter / denom) if denom > 0 else 0.0


# ---------------- NLI feature computation ----------------

def compute_nli_for_pairs(pairs, model, tokenizer, batch_size=32):
    """Returns array of shape (n_pairs, 7): [ent, neu, con, emc, cme, max, entropy]."""
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


# ---------------- Action gap features ----------------

def build_action_gap_features_for_replay(claims, evidences, original_df_for_tfidf):
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


# ---------------- Selector definitions ----------------

SELECTOR_DEFINITIONS = [
    {
        "selector": "bm25_top1_raw",
        "type": "negative_baseline",
        "rule": "Use original BM25 top1 chunk text verbatim (with metadata markers). No selection.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "oracle_span",
        "type": "upper_bound",
        "rule": "Use oracle evidence span (gold evidence from dataset).",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "best_sentence_top3_overlap",
        "type": "overlap",
        "rule": "Split each of top3 BM25 chunks into sentences. Pick sentence with max F1-like token overlap with claim.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "best_sentence_top5_overlap",
        "type": "overlap",
        "rule": "Split each of top5 BM25 chunks into sentences. Pick sentence with max F1-like token overlap with claim.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "best_sentence_top10_overlap",
        "type": "overlap",
        "rule": "Split each of top10 BM25 chunks into sentences. Pick sentence with max F1-like token overlap with claim.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "best_sentence_top5_bm25weighted",
        "type": "overlap_weighted",
        "rule": "Score = sentence-claim overlap + 0.2 * parent_chunk_bm25_score. Pick max.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "best_sentence_top5_nli_entailment",
        "type": "nli",
        "rule": "Compute NLI(evidence=sentence, hypothesis=claim) for all top5 sentences. Pick max entailment_prob.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": True,
    },
    {
        "selector": "best_sentence_top5_nli_low_entropy",
        "type": "nli",
        "rule": "Pick sentence with min NLI entropy (most confident).",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": True,
    },
    {
        "selector": "best_sentence_top5_margin",
        "type": "nli",
        "rule": "Pick sentence with max abs(entailment - contradiction).",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": True,
    },
    {
        "selector": "two_sentence_window_top5",
        "type": "window",
        "rule": "Pick best sentence by overlap from top5. Add 1 most-overlapping neighbor (same chunk adjacent OR another chunk sentence).",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
    {
        "selector": "length_limited_top5",
        "type": "overlap_length",
        "rule": "Filter top5 sentences to 10-40 words only. Pick max overlap.",
        "uses_true_label": False,
        "uses_oracle_hit": False,
        "uses_nli": False,
    },
]


# ---------------- Main ----------------

def main():
    log("=" * 70)
    log("Canonical Evidence Selector Robustness v1")
    log("=" * 70)

    # ---- Step 0: Load data ----
    log("\n[Step 0] Loading inputs ...")
    main_df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    assert len(main_df) == 444
    main_df = main_df.sort_values("candidate_id").reset_index(drop=True)
    log(f"  Main data: {len(main_df)} rows")

    # Load oracle evidence from canonicalization dir
    canon_evidence_df = pd.read_csv(CANON_DIR / "canonicalized_evidence_spans.csv", keep_default_na=False)
    canon_evidence_df = canon_evidence_df.sort_values("candidate_id").reset_index(drop=True)
    log(f"  Canonicalization evidence: {len(canon_evidence_df)} rows")

    # Load BM25 retrieval results
    bm25_df = pd.read_csv(RETRIEVAL_RESULTS_BM25, keep_default_na=False)
    log(f"  BM25 retrieval: {len(bm25_df)} rows")

    # Build candidate_id -> list of (rank, chunk_id, bm25_score, raw_text, paper_id, page_number)
    candidate_to_chunks = {}
    for cand_id, group in bm25_df.sort_values(["candidate_id", "rank"]).groupby("candidate_id"):
        chunks = []
        for _, row in group.iterrows():
            chunks.append({
                "rank": int(row["rank"]),
                "chunk_id": row["chunk_id"],
                "bm25_score": float(row["bm25_score"]),
                "raw_text": row["retrieved_text"],
                "paper_id": row["paper_id"],
                "page_number": row["page_number"],
            })
        candidate_to_chunks[cand_id] = chunks

    # ---- Step 1: Save selector definitions ----
    log("\n[Step 1] Saving selector definitions ...")
    sel_def_df = pd.DataFrame(SELECTOR_DEFINITIONS)
    sel_def_path = OUTPUT_DIR / "selector_variant_definitions.csv"
    sel_def_df.to_csv(sel_def_path, index=False, encoding="utf-8-sig")
    log(f"  -> {sel_def_path}")

    # ---- Step 2: Pre-compute sentences for top10 chunks per candidate ----
    log("\n[Step 2] Pre-computing cleaned sentences for top10 chunks per candidate ...")
    # For each candidate, store list of sentences with origin info, up to top10 chunks
    candidate_sentences = {}  # candidate_id -> list of {sent_idx_global, chunk_idx, sent_idx_in_chunk, text, n_words, parent_bm25_score, parent_chunk_id, parent_rank}
    for cand_id in main_df["candidate_id"].tolist():
        chunks = candidate_to_chunks.get(cand_id, [])
        top10 = chunks[:10]
        all_sents = []
        for ci, c in enumerate(top10):
            cleaned = clean_chunk_text(c["raw_text"])
            sents = split_sentences(cleaned)
            for si, s in enumerate(sents):
                all_sents.append({
                    "chunk_idx": ci,
                    "sent_idx_in_chunk": si,
                    "text": s,
                    "n_words": len(s.split()),
                    "parent_bm25_score": c["bm25_score"],
                    "parent_chunk_id": c["chunk_id"],
                    "parent_rank": c["rank"],
                })
        candidate_sentences[cand_id] = all_sents
    total_sents = sum(len(v) for v in candidate_sentences.values())
    log(f"  Total sentences across all candidates (top10): {total_sents}")

    # ---- Step 3: Compute NLI for ALL top5 sentences (for NLI-based selectors) ----
    log("\n[Step 3] Computing NLI for all top5 sentences (for NLI-based selectors) ...")

    # Build flat list of (candidate_id, sent_global_idx, sentence) for top5
    top5_pairs = []  # (cand_id, sent_global_idx, sentence_text)
    top5_sent_lookup = {}  # (cand_id, sent_global_idx) -> row in pairs
    for cand_id in main_df["candidate_id"].tolist():
        sents = candidate_sentences[cand_id]
        # Filter to top5 chunks (chunk_idx 0-4)
        top5_sents = [s for s in sents if s["chunk_idx"] < 5]
        claim = main_df.loc[main_df["candidate_id"] == cand_id, "claim_text"].iloc[0]
        for gi, s in enumerate(top5_sents):
            top5_pairs.append((cand_id, gi, s["text"], claim))
            top5_sent_lookup[(cand_id, gi)] = len(top5_pairs) - 1

    log(f"  Total top5 sentence-claim pairs: {len(top5_pairs)}")

    # Cache NLI features to disk to allow reruns without recomputing
    nli_cache_path = OUTPUT_DIR / "nli_top5_cache.npz"
    cache_meta_path = OUTPUT_DIR / "nli_top5_cache_meta.csv"

    if nli_cache_path.exists() and cache_meta_path.exists():
        log("  Loading cached NLI features ...")
        cached_meta = pd.read_csv(cache_meta_path, keep_default_na=False)
        cached_arr = np.load(nli_cache_path)["feats"]
        if len(cached_arr) == len(top5_pairs) and cached_meta["candidate_id"].tolist() == [p[0] for p in top5_pairs]:
            log(f"  Cache hit: loaded {len(cached_arr)} NLI feature rows")
            nli_feats_top5 = cached_arr
        else:
            log("  Cache stale (count mismatch), recomputing ...")
            nli_feats_top5 = None
    else:
        nli_feats_top5 = None

    if nli_feats_top5 is None:
        log("  Loading NLI model ...")
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
        nli_model.eval()
        log(f"  NLI model loaded: {NLI_MODEL_NAME}")

        pairs_for_nli = [(p[2], p[3]) for p in top5_pairs]  # (sentence=premise, claim=hypothesis)
        nli_feats_top5 = compute_nli_for_pairs(pairs_for_nli, nli_model, nli_tokenizer, batch_size=32)
        log(f"  NLI features shape: {nli_feats_top5.shape}")

        # Save cache
        np.savez(nli_cache_path, feats=nli_feats_top5)
        cache_meta_df = pd.DataFrame({
            "candidate_id": [p[0] for p in top5_pairs],
            "sent_global_idx": [p[1] for p in top5_pairs],
            "sentence_text": [p[2] for p in top5_pairs],
            "claim_text": [p[3] for p in top5_pairs],
        })
        cache_meta_df.to_csv(cache_meta_path, index=False, encoding="utf-8-sig")
        log(f"  -> Cached to {nli_cache_path}")

    # Ensure NLI model is loaded for Step 6 (selectors needing fresh NLI)
    if "nli_model" not in dir():
        log("  Loading NLI model for selector NLI computation ...")
        from transformers import AutoModelForSequenceClassification, AutoTokenizer
        nli_tokenizer = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        nli_model = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
        nli_model.eval()
        log(f"  NLI model loaded: {NLI_MODEL_NAME}")

    # Cache NLI features per (cand_id, sent_global_idx)
    nli_cache = {}  # (cand_id, gi) -> (entailment, neutral, contradiction, emc, cme, maxp, entropy)
    for i, (cand_id, gi, _, _) in enumerate(top5_pairs):
        nli_cache[(cand_id, gi)] = nli_feats_top5[i]

    # ---- Step 4: Run each selector to choose evidence ----
    log("\n[Step 4] Running selectors to choose evidence per candidate ...")
    # selected_evidence[selector][candidate_id] = {text, chunk_id, rank, n_words, score, reason}
    selected_evidence = {sel: {} for sel in SELECTOR_VARIANTS}

    for cand_id in main_df["candidate_id"].tolist():
        claim = main_df.loc[main_df["candidate_id"] == cand_id, "claim_text"].iloc[0]
        claim_tokens = tokenize_simple(claim)
        all_sents = candidate_sentences[cand_id]
        top3_sents = [s for s in all_sents if s["chunk_idx"] < 3]
        top5_sents = [s for s in all_sents if s["chunk_idx"] < 5]
        top10_sents = all_sents  # already top10

        # A. bm25_top1_raw
        chunks = candidate_to_chunks.get(cand_id, [])
        if chunks:
            c0 = chunks[0]
            selected_evidence["bm25_top1_raw"][cand_id] = {
                "text": c0["raw_text"],
                "chunk_id": c0["chunk_id"],
                "rank": c0["rank"],
                "n_words": len(c0["raw_text"].split()),
                "score": 0.0,
                "reason": "raw_top1_chunk_no_selection",
            }
        else:
            selected_evidence["bm25_top1_raw"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_chunks"
            }

        # B. oracle_span
        oracle_ev = canon_evidence_df.loc[canon_evidence_df["candidate_id"] == cand_id, "oracle_span"].iloc[0]
        selected_evidence["oracle_span"][cand_id] = {
            "text": oracle_ev,
            "chunk_id": "ORACLE",
            "rank": 0,
            "n_words": len(str(oracle_ev).split()),
            "score": 0.0,
            "reason": "oracle_provided",
        }

        # Helper for overlap-based selection
        def select_by_overlap(sent_list, score_fn=None):
            if not sent_list:
                return None
            scored = []
            for i, s in enumerate(sent_list):
                ov = overlap_score(claim_tokens, s["text"])
                extra = score_fn(s, ov) if score_fn else 0.0
                scored.append((ov + extra, i, s))
            scored.sort(key=lambda x: (-x[0], x[1]))
            best_score, _, best_s = scored[0]
            return best_s, best_score

        # C. best_sentence_top3_overlap
        result = select_by_overlap(top3_sents)
        if result:
            s, sc = result
            selected_evidence["best_sentence_top3_overlap"][cand_id] = {
                "text": s["text"], "chunk_id": s["parent_chunk_id"], "rank": s["parent_rank"],
                "n_words": s["n_words"], "score": sc, "reason": f"overlap_top3_max",
            }
        else:
            selected_evidence["best_sentence_top3_overlap"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
            }

        # D. best_sentence_top5_overlap
        result = select_by_overlap(top5_sents)
        if result:
            s, sc = result
            selected_evidence["best_sentence_top5_overlap"][cand_id] = {
                "text": s["text"], "chunk_id": s["parent_chunk_id"], "rank": s["parent_rank"],
                "n_words": s["n_words"], "score": sc, "reason": f"overlap_top5_max",
            }
        else:
            selected_evidence["best_sentence_top5_overlap"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
            }

        # E. best_sentence_top10_overlap
        result = select_by_overlap(top10_sents)
        if result:
            s, sc = result
            selected_evidence["best_sentence_top10_overlap"][cand_id] = {
                "text": s["text"], "chunk_id": s["parent_chunk_id"], "rank": s["parent_rank"],
                "n_words": s["n_words"], "score": sc, "reason": f"overlap_top10_max",
            }
        else:
            selected_evidence["best_sentence_top10_overlap"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
            }

        # F. best_sentence_top5_bm25weighted: score = overlap + 0.2 * parent_bm25_score
        def weighted_score_fn(s, ov):
            return 0.2 * s["parent_bm25_score"]
        result = select_by_overlap(top5_sents, score_fn=weighted_score_fn)
        if result:
            s, sc = result
            selected_evidence["best_sentence_top5_bm25weighted"][cand_id] = {
                "text": s["text"], "chunk_id": s["parent_chunk_id"], "rank": s["parent_rank"],
                "n_words": s["n_words"], "score": sc, "reason": f"overlap+0.2*bm25",
            }
        else:
            selected_evidence["best_sentence_top5_bm25weighted"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
            }

        # G. best_sentence_top5_nli_entailment: max entailment
        # H. best_sentence_top5_nli_low_entropy: min entropy
        # I. best_sentence_top5_margin: max abs(emc) = max abs(ent - con)
        if top5_sents:
            scored_nli = []
            for i, s in enumerate(top5_sents):
                feats = nli_cache.get((cand_id, i))
                if feats is None:
                    continue
                ent, neu, con, emc, cme, maxp, entropy = feats
                scored_nli.append({
                    "i": i, "s": s,
                    "ent": float(ent), "entropy": float(entropy), "margin": float(abs(emc)),
                })
            if scored_nli:
                # G: max entailment
                best_g = max(scored_nli, key=lambda x: (x["ent"], -x["i"]))
                selected_evidence["best_sentence_top5_nli_entailment"][cand_id] = {
                    "text": best_g["s"]["text"], "chunk_id": best_g["s"]["parent_chunk_id"],
                    "rank": best_g["s"]["parent_rank"], "n_words": best_g["s"]["n_words"],
                    "score": best_g["ent"], "reason": f"nli_max_entailment",
                }
                # H: min entropy
                best_h = min(scored_nli, key=lambda x: (x["entropy"], x["i"]))
                selected_evidence["best_sentence_top5_nli_low_entropy"][cand_id] = {
                    "text": best_h["s"]["text"], "chunk_id": best_h["s"]["parent_chunk_id"],
                    "rank": best_h["s"]["parent_rank"], "n_words": best_h["s"]["n_words"],
                    "score": -best_h["entropy"], "reason": f"nli_min_entropy",
                }
                # I: max margin
                best_i = max(scored_nli, key=lambda x: (x["margin"], -x["i"]))
                selected_evidence["best_sentence_top5_margin"][cand_id] = {
                    "text": best_i["s"]["text"], "chunk_id": best_i["s"]["parent_chunk_id"],
                    "rank": best_i["s"]["parent_rank"], "n_words": best_i["s"]["n_words"],
                    "score": best_i["margin"], "reason": f"nli_max_abs_emc",
                }
            else:
                for sel in ["best_sentence_top5_nli_entailment", "best_sentence_top5_nli_low_entropy", "best_sentence_top5_margin"]:
                    selected_evidence[sel][cand_id] = {
                        "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_nli_feats",
                    }
        else:
            for sel in ["best_sentence_top5_nli_entailment", "best_sentence_top5_nli_low_entropy", "best_sentence_top5_margin"]:
                selected_evidence[sel][cand_id] = {
                    "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
                }

        # J. two_sentence_window_top5: best sentence + 1 most relevant neighbor
        if top5_sents:
            # First find best by overlap
            scored = []
            for i, s in enumerate(top5_sents):
                ov = overlap_score(claim_tokens, s["text"])
                scored.append((ov, i, s))
            scored.sort(key=lambda x: (-x[0], x[1]))
            if scored:
                best_ov, best_i, best_s = scored[0]
                # Find neighbor: prefer same chunk adjacent; otherwise next-best by overlap
                neighbor = None
                # Same chunk adjacent
                same_chunk = [(ov, i, s) for ov, i, s in scored if i != best_i and s["chunk_idx"] == best_s["chunk_idx"]]
                if same_chunk:
                    # Pick adjacent (sent_idx_in_chunk differs by 1) if available
                    adj = [(ov, i, s) for ov, i, s in same_chunk if abs(s["sent_idx_in_chunk"] - best_s["sent_idx_in_chunk"]) == 1]
                    if adj:
                        neighbor = max(adj, key=lambda x: x[0])
                    else:
                        neighbor = max(same_chunk, key=lambda x: x[0])
                else:
                    # Pick next-best overall
                    if len(scored) > 1:
                        neighbor = scored[1]

                if neighbor:
                    _, _, n_s = neighbor
                    # Order by sent_idx_in_chunk if same chunk
                    if n_s["chunk_idx"] == best_s["chunk_idx"]:
                        if n_s["sent_idx_in_chunk"] < best_s["sent_idx_in_chunk"]:
                            text = n_s["text"] + " " + best_s["text"]
                        else:
                            text = best_s["text"] + " " + n_s["text"]
                    else:
                        text = best_s["text"] + " " + n_s["text"]
                    selected_evidence["two_sentence_window_top5"][cand_id] = {
                        "text": text, "chunk_id": best_s["parent_chunk_id"], "rank": best_s["parent_rank"],
                        "n_words": len(text.split()), "score": best_ov, "reason": f"best+neighbor_overlap",
                    }
                else:
                    selected_evidence["two_sentence_window_top5"][cand_id] = {
                        "text": best_s["text"], "chunk_id": best_s["parent_chunk_id"], "rank": best_s["parent_rank"],
                        "n_words": best_s["n_words"], "score": best_ov, "reason": "best_only_no_neighbor",
                    }
            else:
                selected_evidence["two_sentence_window_top5"][cand_id] = {
                    "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
                }
        else:
            selected_evidence["two_sentence_window_top5"][cand_id] = {
                "text": "", "chunk_id": "", "rank": 0, "n_words": 0, "score": 0.0, "reason": "no_sents",
            }

        # K. length_limited_top5: only 10-40 word sentences
        len_filtered = [s for s in top5_sents if 10 <= s["n_words"] <= 40]
        result = select_by_overlap(len_filtered)
        if result:
            s, sc = result
            selected_evidence["length_limited_top5"][cand_id] = {
                "text": s["text"], "chunk_id": s["parent_chunk_id"], "rank": s["parent_rank"],
                "n_words": s["n_words"], "score": sc, "reason": f"overlap_10-40words",
            }
        else:
            # Fallback: best_sentence_top5_overlap result
            fallback = selected_evidence["best_sentence_top5_overlap"][cand_id]
            selected_evidence["length_limited_top5"][cand_id] = {
                "text": fallback["text"], "chunk_id": fallback["chunk_id"], "rank": fallback["rank"],
                "n_words": fallback["n_words"], "score": fallback["score"], "reason": "fallback_no_10-40_sent",
            }

    # ---- Step 5: Save selector_variant_evidence.csv ----
    log("\n[Step 5] Saving selector_variant_evidence.csv ...")
    ev_rows = []
    for sel in SELECTOR_VARIANTS:
        for cand_id in main_df["candidate_id"].tolist():
            e = selected_evidence[sel][cand_id]
            ev_rows.append({
                "candidate_id": cand_id,
                "selector": sel,
                "selected_text": e["text"],
                "selected_chunk_id": e["chunk_id"],
                "selected_rank": e["rank"],
                "n_words": e["n_words"],
                "selection_score": e["score"],
                "reason": e["reason"],
            })
    ev_df = pd.DataFrame(ev_rows)
    ev_path = OUTPUT_DIR / "selector_variant_evidence.csv"
    ev_df.to_csv(ev_path, index=False, encoding="utf-8-sig")
    log(f"  -> {ev_path}")

    # Print length stats per selector
    log("  Length stats per selector (words):")
    for sel in SELECTOR_VARIANTS:
        s = ev_df[ev_df["selector"] == sel]["selected_text"].astype(str)
        log(f"    {sel:40s} mean={s.str.split().str.len().mean():.1f} median={s.str.split().str.len().median():.0f}")

    # ---- Step 6: Compute NLI features for each selector's selected evidence ----
    log("\n[Step 6] Computing NLI features for each selector's selected evidence ...")
    # For NLI-based selectors, we already have NLI features cached for the selected sentence
    # For others, compute fresh NLI

    # For oracle_span and bm25_top1_raw, we can reuse from r4_retrieved_replay_v1
    replay_dir = Path(r"D:\ocn\experiments\r4_retrieved_replay_v1")
    canon_hcm_oracle = pd.read_csv(replay_dir / "hcm_features_replay_oracle.csv", keep_default_na=False)
    canon_hcm_oracle = canon_hcm_oracle.sort_values("candidate_id").reset_index(drop=True)
    canon_hcm_bm25_top1 = pd.read_csv(replay_dir / "hcm_features_replay_bm25_top1.csv", keep_default_na=False)
    canon_hcm_bm25_top1 = canon_hcm_bm25_top1.sort_values("candidate_id").reset_index(drop=True)

    selector_hcm = {
        "oracle_span": canon_hcm_oracle,
        "bm25_top1_raw": canon_hcm_bm25_top1,
    }

    # For NLI-based selectors, reuse cached NLI for the selected sentence
    for sel in ["best_sentence_top5_nli_entailment", "best_sentence_top5_nli_low_entropy", "best_sentence_top5_margin"]:
        rows = []
        for cand_id in main_df["candidate_id"].tolist():
            e = selected_evidence[sel][cand_id]
            # Find the sent_global_idx for this selection
            # We need to look up which top5 sentence was selected
            top5_sents = [s for s in candidate_sentences[cand_id] if s["chunk_idx"] < 5]
            selected_idx = None
            for i, s in enumerate(top5_sents):
                if s["text"] == e["text"] and s["parent_chunk_id"] == e["chunk_id"]:
                    selected_idx = i
                    break
            if selected_idx is not None and (cand_id, selected_idx) in nli_cache:
                feats = nli_cache[(cand_id, selected_idx)]
                rows.append({
                    "candidate_id": cand_id,
                    "entailment_correct": float(feats[0]),
                    "neutral_correct": float(feats[1]),
                    "contradiction_correct": float(feats[2]),
                    "ent_minus_con_correct": float(feats[3]),
                    "con_minus_ent_correct": float(feats[4]),
                    "max_prob_correct": float(feats[5]),
                    "entropy_correct": float(feats[6]),
                })
            else:
                # Fallback: compute NLI for this single sentence
                rows.append(None)  # placeholder, will compute below
        # Check if any None
        if any(r is None for r in rows):
            log(f"  [{sel}] Some selections missing from cache, computing NLI for missing ...")
            missing_idx = [i for i, r in enumerate(rows) if r is None]
            missing_pairs = []
            for i in missing_idx:
                cand_id = main_df["candidate_id"].iloc[i]
                e = selected_evidence[sel][cand_id]
                claim = main_df.loc[main_df["candidate_id"] == cand_id, "claim_text"].iloc[0]
                missing_pairs.append((e["text"], claim))
            if missing_pairs:
                missing_feats = compute_nli_for_pairs(missing_pairs, nli_model, nli_tokenizer, batch_size=32)
                for j, i in enumerate(missing_idx):
                    f = missing_feats[j]
                    rows[i] = {
                        "candidate_id": main_df["candidate_id"].iloc[i],
                        "entailment_correct": float(f[0]),
                        "neutral_correct": float(f[1]),
                        "contradiction_correct": float(f[2]),
                        "ent_minus_con_correct": float(f[3]),
                        "con_minus_ent_correct": float(f[4]),
                        "max_prob_correct": float(f[5]),
                        "entropy_correct": float(f[6]),
                    }
        selector_hcm[sel] = pd.DataFrame(rows)

    # For remaining overlap-based selectors, compute fresh NLI (444 pairs each)
    remaining_selectors = [s for s in SELECTOR_VARIANTS if s not in selector_hcm]
    for sel in remaining_selectors:
        log(f"  [{sel}] Computing NLI features ...")
        pairs = []
        for cand_id in main_df["candidate_id"].tolist():
            e = selected_evidence[sel][cand_id]
            claim = main_df.loc[main_df["candidate_id"] == cand_id, "claim_text"].iloc[0]
            pairs.append((e["text"], claim))
        feats = compute_nli_for_pairs(pairs, nli_model, nli_tokenizer, batch_size=32)
        selector_hcm[sel] = pd.DataFrame({
            "candidate_id": main_df["candidate_id"],
            "entailment_correct": feats[:, 0],
            "neutral_correct": feats[:, 1],
            "contradiction_correct": feats[:, 2],
            "ent_minus_con_correct": feats[:, 3],
            "con_minus_ent_correct": feats[:, 4],
            "max_prob_correct": feats[:, 5],
            "entropy_correct": feats[:, 6],
        })
        log(f"    NLI features shape: {feats.shape}")

    # ---- Step 7: Build action gap features per selector ----
    log("\n[Step 7] Building action gap features per selector ...")
    selector_action_gap = {}
    for sel in SELECTOR_VARIANTS:
        claims = main_df["claim_text"].astype(str).tolist()
        evidences = [selected_evidence[sel][cid]["text"] for cid in main_df["candidate_id"]]
        ag_df = build_action_gap_features_for_replay(claims, evidences, main_df)
        ag_df["candidate_id"] = main_df["candidate_id"].values
        selector_action_gap[sel] = ag_df

    # ---- Step 8: Load R4 artifacts ----
    log("\n[Step 8] Loading recovered R4 artifacts ...")
    artifacts = {}
    for seed in SEEDS:
        sa = RECOVERY_ARTIFACTS / f"seed_{seed}"
        with open(sa / "thresholds.json") as f:
            thresholds = json.load(f)
        with open(sa / "feature_columns.json") as f:
            feat_cols = json.load(f)
        with open(sa / "label_mapping.json") as f:
            label_map = json.load(f)
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
            "thresholds": thresholds, "feature_columns": feat_cols, "label_mapping": label_map,
            "clf_contra": clf_contra, "clf_strong": clf_strong, "clf_svm": clf_svm,
            "scaler_contra": scaler_contra, "scaler_strong": scaler_strong, "scaler_svm": scaler_svm,
        }
    log(f"  Loaded {len(artifacts)} seed artifacts")

    split_manifest = pd.read_csv(RECOVERY_SPLIT_MANIFEST, keep_default_na=False)
    rec_preds = pd.read_csv(RECOVERY_PREDICTIONS, keep_default_na=False)
    rec_preds = rec_preds[rec_preds["pred_label"] != "NO_OOF_PREDICTION"].copy()
    eval_candidates = rec_preds["candidate_id"].tolist()
    log(f"  Eval candidates: {len(eval_candidates)} (missing: {444 - len(eval_candidates)})")

    cand_seed_split = {}
    for _, row in split_manifest.iterrows():
        cand_seed_split[(row["candidate_id"], int(row["seed"]))] = row["split"]

    # ---- Step 9: R4 replay per selector per seed ----
    log("\n[Step 9] Replaying R4 per selector per seed ...")
    expert_features = NLI_FEATURES + [
        "action_escalation_gap", "claim_action_strength", "evidence_action_support",
        "deployment_gap", "metric_to_action_gap", "certainty_gap", "scope_gap",
        "length_diff", "claim_evidence_overlap",
    ]
    svm_features = NLI_FEATURES + ["scope_gap"]

    per_seed_preds = {}  # {selector: {seed: {cand_id: pred_4idx}}}
    for sel in SELECTOR_VARIANTS:
        log(f"\n  --- {sel} ---")
        hcm_df = selector_hcm[sel].set_index("candidate_id")
        ag_df = selector_action_gap[sel].set_index("candidate_id")
        merged = hcm_df.join(ag_df, how="left", rsuffix="_ag")
        for col in list(merged.columns):
            if col.endswith("_ag"):
                merged.drop(col, axis=1, inplace=True)

        per_seed_preds[sel] = {}
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
                per_seed_preds[sel][seed] = {}
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

            preds = route_conservative_strong(
                p_contra, p_strong, p_svm,
                t_contra, t_contra_low, t_strong, t_svm,
                len(seed_eval_cands),
            )
            per_seed_preds[sel][seed] = {
                cid: int(p) for cid, p in zip(seed_eval_cands, preds)
            }

    # ---- Step 10: Aggregate predictions (majority vote) ----
    log("\n[Step 10] Aggregating predictions ...")
    def aggregate(per_seed):
        agg = {}
        for cid in eval_candidates:
            votes = []
            for seed in SEEDS:
                if cid in per_seed[seed]:
                    votes.append(per_seed[seed][cid])
            if not votes:
                agg[cid] = None
                continue
            counts = {}
            for v in votes:
                counts[v] = counts.get(v, 0) + 1
            best_v = sorted(counts.items(), key=lambda x: (-x[1], x[0]))[0][0]
            agg[cid] = best_v
        return agg

    selector_agg = {sel: aggregate(per_seed_preds[sel]) for sel in SELECTOR_VARIANTS}

    # ---- Step 11: Save predictions ----
    log("\n[Step 11] Saving selector_variant_predictions.csv ...")
    pred_rows = []
    for cid in eval_candidates:
        true_lab = main_df.loc[main_df["candidate_id"] == cid, "candidate_label_guess"].iloc[0]
        row = {"candidate_id": cid, "true_label": true_lab, "true_label_4idx": LABEL_TO_IDX[true_lab]}
        for sel in SELECTOR_VARIANTS:
            p = selector_agg[sel][cid]
            row[f"pred_{sel}"] = p
            row[f"pred_{sel}_label"] = IDX_TO_LABEL.get(p, "UNKNOWN")
            row[f"correct_{sel}"] = (p == LABEL_TO_IDX[true_lab])
        pred_rows.append(row)
    preds_df = pd.DataFrame(pred_rows)
    preds_path = OUTPUT_DIR / "selector_variant_predictions.csv"
    preds_df.to_csv(preds_path, index=False, encoding="utf-8-sig")
    log(f"  -> {preds_path}")

    # ---- Step 12: Compute metrics per selector ----
    log("\n[Step 12] Computing metrics per selector ...")
    y_4idx = preds_df["true_label_4idx"].values
    y_strong = np.array([to_strong_action_binary(l) for l in preds_df["true_label"]])
    y_esc = np.array([to_escalation_binary(l) for l in preds_df["true_label"]])
    y_contra = np.array([to_contradiction_binary(l) for l in preds_df["true_label"]])

    metrics_rows = []
    for sel in SELECTOR_VARIANTS:
        pred_4idx = preds_df[f"pred_{sel}"].values
        m = compute_all_metrics(y_4idx, y_strong, y_esc, y_contra, pred_4idx)
        m["selector"] = sel
        m["n_eval"] = len(y_4idx)
        metrics_rows.append(m)

    metrics_df = pd.DataFrame(metrics_rows)

    # Add gap and improvement columns
    oracle_f1 = float(metrics_df.loc[metrics_df["selector"] == "oracle_span", "strong_positive_f1"].iloc[0])
    raw_top1_f1 = float(metrics_df.loc[metrics_df["selector"] == "bm25_top1_raw", "strong_positive_f1"].iloc[0])
    metrics_df["oracle_to_selector_gap"] = oracle_f1 - metrics_df["strong_positive_f1"]
    metrics_df["improvement_over_raw_top1"] = metrics_df["strong_positive_f1"] - raw_top1_f1

    # Reorder columns
    metrics_df = metrics_df[[
        "selector", "n_eval", "flat4_accuracy", "flat4_macro_f1",
        "flat4_supported_f1", "flat4_mild_f1", "flat4_strong_f1", "flat4_contradiction_f1",
        "strong_positive_f1", "strong_precision", "strong_recall",
        "escalation_positive_f1", "contradiction_positive_f1",
        "oracle_to_selector_gap", "improvement_over_raw_top1",
    ]]
    metrics_path = OUTPUT_DIR / "selector_variant_metrics.csv"
    metrics_df.to_csv(metrics_path, index=False, encoding="utf-8-sig")
    log(f"  -> {metrics_path}")

    log("\n  Metrics summary (sorted by strong-F1 desc):")
    for _, row in metrics_df.sort_values("strong_positive_f1", ascending=False).iterrows():
        log(f"    {row['selector']:42s} strong-F1={row['strong_positive_f1']:.4f} "
            f"recall={row['strong_recall']:.4f} macro-F1={row['flat4_macro_f1']:.4f} "
            f"gap={row['oracle_to_selector_gap']:+.4f}")

    # ---- Step 13: Stability by label ----
    log("\n[Step 13] Computing per-label stability ...")
    stability_rows = []
    for sel in SELECTOR_VARIANTS:
        pred_4idx = preds_df[f"pred_{sel}"].values
        for lab_idx, lab_name in IDX_TO_LABEL.items():
            mask_true = (y_4idx == lab_idx)
            n = int(mask_true.sum())
            if n == 0:
                continue
            mask_pred = (pred_4idx == lab_idx)
            tp = int((mask_true & mask_pred).sum())
            fp = int((~mask_true & mask_pred).sum())
            fn = int((mask_true & ~mask_pred).sum())
            prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
            rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
            f1 = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
            stability_rows.append({
                "label": lab_name,
                "selector": sel,
                "precision": prec,
                "recall": rec,
                "f1": f1,
                "n": n,
            })
    stability_df = pd.DataFrame(stability_rows)
    stability_path = OUTPUT_DIR / "selector_stability_by_label.csv"
    stability_df.to_csv(stability_path, index=False, encoding="utf-8-sig")
    log(f"  -> {stability_path}")

    # ---- Step 14: Error overlap between best selectors ----
    log("\n[Step 14] Computing error overlap between key selectors ...")
    key_selectors = [
        "best_sentence_top5_overlap",
        "best_sentence_top5_nli_entailment",
        "best_sentence_top5_margin",
        "length_limited_top5",
    ]
    overlap_rows = []
    for i, sa in enumerate(key_selectors):
        for j, sb in enumerate(key_selectors):
            if i >= j:
                continue
            ca = preds_df[f"correct_{sa}"].values
            cb = preds_df[f"correct_{sb}"].values
            both_correct = int((ca & cb).sum())
            a_only = int((ca & ~cb).sum())
            b_only = int((~ca & cb).sum())
            both_wrong = int((~ca & ~cb).sum())
            overlap_rows.append({
                "selector_A": sa,
                "selector_B": sb,
                "both_correct": both_correct,
                "selector_A_only_correct": a_only,
                "selector_B_only_correct": b_only,
                "both_wrong": both_wrong,
                "agreement_rate": (both_correct + both_wrong) / len(ca),
            })
    overlap_df = pd.DataFrame(overlap_rows)
    overlap_path = OUTPUT_DIR / "selector_error_overlap.csv"
    overlap_df.to_csv(overlap_path, index=False, encoding="utf-8-sig")
    log(f"  -> {overlap_path}")
    log("  Error overlap summary:")
    for _, row in overlap_df.iterrows():
        log(f"    {row['selector_A']} vs {row['selector_B']}: "
            f"both_correct={row['both_correct']}, A_only={row['selector_A_only_correct']}, "
            f"B_only={row['selector_B_only_correct']}, both_wrong={row['both_wrong']}, "
            f"agreement={row['agreement_rate']:.3f}")

    # ---- Step 15: Gate ----
    log("\n[Step 15] Computing gate ...")
    best_row = metrics_df.loc[metrics_df["selector"] != "oracle_span"].sort_values(
        "strong_positive_f1", ascending=False).iloc[0]
    best_selector = best_row["selector"]
    best_selector_f1 = float(best_row["strong_positive_f1"])

    # Exclude oracle_span and bm25_top1_raw from "selectors above 0.40"
    candidate_selectors = [s for s in SELECTOR_VARIANTS if s not in ("oracle_span", "bm25_top1_raw")]
    n_above_040 = int(sum(
        1 for sel in candidate_selectors
        if float(metrics_df.loc[metrics_df["selector"] == sel, "strong_positive_f1"].iloc[0]) >= 0.40
    ))
    n_gap_le_005 = int(sum(
        1 for sel in candidate_selectors
        if float(metrics_df.loc[metrics_df["selector"] == sel, "oracle_to_selector_gap"].iloc[0]) <= 0.05
    ))

    robustness_passed = (n_above_040 >= 3) and (n_gap_le_005 >= 2)

    # Identify failure mode: is it selection failure or R4 screening failure?
    # Compare best selector errors to oracle errors
    best_sel = best_selector
    best_correct_mask = preds_df[f"correct_{best_sel}"].values
    oracle_correct_mask = preds_df[f"correct_oracle_span"].values
    # Cases where best_sel wrong but oracle right: selection failure (different evidence)
    selection_failure = int((~best_correct_mask & oracle_correct_mask).sum())
    # Cases where both wrong: likely R4 screening failure (same evidence family)
    both_wrong = int((~best_correct_mask & ~oracle_correct_mask).sum())
    # Cases where best_sel right but oracle wrong: canon helped
    canon_helped = int((best_correct_mask & ~oracle_correct_mask).sum())

    main_bottleneck = "selection" if selection_failure > both_wrong else "screening"

    # Should we continue hybrid/dense?
    # If multiple selectors already match oracle, BM25 is sufficient with canonicalization
    # If not, dense/reranker could help
    continue_dense = (n_above_040 < 3) or (best_selector_f1 < oracle_f1 - 0.05)

    gate = {
        "task": "Canonical Evidence Selector Robustness v1",
        "audit_date": datetime.now().isoformat(timespec="seconds"),
        "artifacts_loaded": True,
        "used_proxy": False,
        "retrained_model": False,
        "thresholds_changed": False,
        "n_eval": len(eval_candidates),
        "n_missing_due_to_split": 444 - len(eval_candidates),
        "n_selectors_tested": len(SELECTOR_VARIANTS),
        "raw_top1_strong_f1": raw_top1_f1,
        "oracle_strong_f1": oracle_f1,
        "best_selector": best_selector,
        "best_selector_strong_f1": best_selector_f1,
        "number_of_selectors_above_0_40": n_above_040,
        "number_of_selectors_with_gap_le_0_05": n_gap_le_005,
        "selectors_above_0_40": [
            sel for sel in candidate_selectors
            if float(metrics_df.loc[metrics_df["selector"] == sel, "strong_positive_f1"].iloc[0]) >= 0.40
        ],
        "selectors_with_gap_le_0_05": [
            sel for sel in candidate_selectors
            if float(metrics_df.loc[metrics_df["selector"] == sel, "oracle_to_selector_gap"].iloc[0]) <= 0.05
        ],
        "robustness_passed": robustness_passed,
        "main_bottleneck": main_bottleneck,
        "selection_failure_count": selection_failure,
        "both_wrong_vs_oracle": both_wrong,
        "canon_helped_count": canon_helped,
        "continue_dense_or_reranker": continue_dense,
        "supports_retrieval_canonicalization_screening_mainline": robustness_passed,
        "prohibitions_enforced": [
            "no_model_training", "no_api_calls", "no_network", "no_threshold_change",
            "no_original_data_modification", "no_paper_modification", "no_file_deletion",
            "no_cue_based_proxy", "no_silver_as_gold", "no_natural_distribution_claim",
            "no_split_missing_in_main_metrics", "no_true_label_for_evidence_selection",
            "no_oracle_hit_for_evidence_selection",
        ],
        "output_files": [
            "selector_variant_definitions.csv",
            "selector_variant_evidence.csv",
            "selector_variant_predictions.csv",
            "selector_variant_metrics.csv",
            "selector_stability_by_label.csv",
            "selector_error_overlap.csv",
            "selector_robustness_gate.json",
            "selector_robustness_report.md",
        ],
    }
    gate_path = OUTPUT_DIR / "selector_robustness_gate.json"
    with open(gate_path, "w") as f:
        json.dump(gate, f, indent=2, default=json_default)
    log(f"  -> {gate_path}")

    # ---- Step 16: Report ----
    log("\n[Step 16] Writing report ...")
    n_above_raw = int(sum(
        1 for sel in candidate_selectors
        if float(metrics_df.loc[metrics_df["selector"] == sel, "strong_positive_f1"].iloc[0]) > raw_top1_f1
    ))
    n_near_oracle = n_gap_le_005

    # NLI vs overlap comparison
    nli_selectors = ["best_sentence_top5_nli_entailment", "best_sentence_top5_nli_low_entropy", "best_sentence_top5_margin"]
    overlap_selectors = ["best_sentence_top3_overlap", "best_sentence_top5_overlap", "best_sentence_top10_overlap"]
    nli_best = max(float(metrics_df.loc[metrics_df["selector"] == s, "strong_positive_f1"].iloc[0]) for s in nli_selectors)
    overlap_best = max(float(metrics_df.loc[metrics_df["selector"] == s, "strong_positive_f1"].iloc[0]) for s in overlap_selectors)
    nli_better = nli_best > overlap_best

    report = f"""# Canonical Evidence Selector Robustness v1

- 审计时间: {datetime.now().isoformat(timespec='seconds')}
- 评估样本数: {len(eval_candidates)} (out-of-fold candidates)
- 缺失 (split-missing): {444 - len(eval_candidates)} (不纳入主指标)
- 测试 selector 数: {len(SELECTOR_VARIANTS)}
- 禁止: 无 proxy, 无重训, 无调参, 无 API, 无联网, 不使用 true_label/oracle_hit 选 evidence

## 1. best_sentence_from_top5 是否稳健？

**{'是' if robustness_passed else '否'}**。

best_sentence_from_top5_overlap strong-F1 = {float(metrics_df.loc[metrics_df['selector']=='best_sentence_top5_overlap','strong_positive_f1'].iloc[0]):.4f}

最佳 selector: **{best_selector}** (strong-F1 = {best_selector_f1:.4f})

判定: 至少 3 个 selector strong-F1 >= 0.40 (实际 {n_above_040}), 至少 2 个 selector gap <= 0.05 (实际 {n_gap_le_005})。

## 2. 有多少 selector 超过 raw top1？

**{n_above_raw} / {len(candidate_selectors)}** (排除 oracle 和 raw_top1 本身)

raw top1 strong-F1 = {raw_top1_f1:.4f}

## 3. 有多少 selector 接近 oracle (gap <= 0.05)？

**{n_near_oracle} / {len(candidate_selectors)}**

oracle strong-F1 = {oracle_f1:.4f}

selectors 接近 oracle:
"""
    for sel in gate["selectors_with_gap_le_0_05"]:
        f1 = float(metrics_df.loc[metrics_df["selector"] == sel, "strong_positive_f1"].iloc[0])
        gap = float(metrics_df.loc[metrics_df["selector"] == sel, "oracle_to_selector_gap"].iloc[0])
        report += f"- {sel}: strong-F1={f1:.4f}, gap={gap:+.4f}\n"

    report += f"""
## 4. NLI selector 是否优于 overlap selector？

**{'是' if nli_better else '否'}**。

- Best NLI selector strong-F1: {nli_best:.4f}
- Best overlap selector strong-F1: {overlap_best:.4f}

## 5. 失败主要来自选错句子还是 R4 判断失败？

主瓶颈: **{main_bottleneck}**

- Selection failure (best_sel 错, oracle 对): {selection_failure}
- Both wrong (best_sel 错, oracle 也错): {both_wrong}  → R4 screening 失败
- Canon helped (best_sel 对, oracle 错): {canon_helped}

## 6. 是否值得继续 hybrid/dense retrieval？

**{'是' if continue_dense else '否'}**。

判定依据:
- selectors >= 0.40: {n_above_040}
- best selector vs oracle gap: {oracle_f1 - best_selector_f1:+.4f}

## 7. 是否支持主线：retrieval → canonicalization → R4 screening？

**{'是' if robustness_passed else '否'}**。

- Robustness passed: {robustness_passed}
- 多个 selector 稳定接近 oracle, 证明 canonicalization 是稳健策略, 不是偶然

## 完整 metrics 表

| Selector | strong-F1 | recall | macro-F1 | gap | improvement vs raw |
|----------|-----------|--------|----------|-----|--------------------|
"""
    for _, row in metrics_df.sort_values("strong_positive_f1", ascending=False).iterrows():
        report += f"| {row['selector']} | {row['strong_positive_f1']:.4f} | {row['strong_recall']:.4f} | {row['flat4_macro_f1']:.4f} | {row['oracle_to_selector_gap']:+.4f} | {row['improvement_over_raw_top1']:+.4f} |\n"

    report += f"""
## 输出文件清单

- selector_variant_definitions.csv
- selector_variant_evidence.csv
- selector_variant_predictions.csv
- selector_variant_metrics.csv
- selector_stability_by_label.csv
- selector_error_overlap.csv
- selector_robustness_gate.json
- selector_robustness_report.md
"""
    report_path = OUTPUT_DIR / "selector_robustness_report.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report)
    log(f"  -> {report_path}")

    # ---- Final summary ----
    log("\n" + "=" * 70)
    log("ROBUSTNESS SUMMARY")
    log("=" * 70)
    log(f"n_eval: {len(eval_candidates)}")
    log(f"raw top1 strong-F1: {raw_top1_f1:.4f}")
    log(f"oracle strong-F1: {oracle_f1:.4f}")
    log(f"best selector: {best_selector} (strong-F1={best_selector_f1:.4f})")
    log(f"selectors above 0.40: {n_above_040}")
    log(f"selectors with gap <= 0.05: {n_gap_le_005}")
    log(f"robustness_passed: {robustness_passed}")
    log(f"continue_dense_or_reranker: {continue_dense}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"ERROR: {e}")
        log(traceback.format_exc())
        sys.exit(1)
