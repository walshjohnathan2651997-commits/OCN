#!/usr/bin/env python
"""run_error_taxonomy_v1.py — Error analysis and failure taxonomy.

Categorizes false positives (FP) and false negatives (FN) into explainable
types for the paper's Discussion and Limitations sections.

Error types (a single candidate may carry multiple tags):
  1. retrieval_miss           — BM25 top-k has no oracle/evidence overlap
  2. evidence_format_noise    — selected evidence too long/short/multi-sentence
  3. weak_selector_overlap    — selector_score below threshold
  4. contradiction_confusion  — p_contra/contradiction_nli high but wrong label
  5. action_lexicon_shortcut  — action words in claim, no evidence support
  6. mild_vs_strong_boundary  — mild_scope_overclaim <-> strong_action_overclaim
  7. supported_overflag       — supported flagged as strong_action
  8. uncertainty_high_entropy — high entropy causing instability
  9. group_variant_artifact   — same group's template variants cause confusion

Inputs:
  --review_scores_csv  candidate_id, true_label, pred_label, selected_evidence, ...
  --selector_csv       candidate_id, p_strong, p_contra, entropy, selector_score, ...
  --retrieval_csv      candidate_id, is_oracle_hit, bm25_score, ...
  --candidate_csv      candidate_id, target_candidate_group_id, claim_text, evidence_text
  --smart_queue_csv    optional, candidate_id, bucket, ...
  --output_dir         experiments/error_taxonomy_v1

Outputs:
  private/error_cases_private.csv   — full text for local analysis (PRIVATE)
  error_cases_redacted.csv          — public, no raw text, only hashes
  error_taxonomy_summary.csv        — counts per error type
  error_taxonomy_summary.md         — paper-readable
  run_config.json                   — config snapshot

Hard boundaries: no network, no API, no training, no original data modification.
true_label is used ONLY for error analysis (FP/FN definition), never for
scoring, ranking, or feature engineering.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np
import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, write_run_config, print_guards  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

LABELS_4 = [
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
]
STRONG_LABEL = "strong_action_overclaim"
MILD_LABEL = "mild_scope_overclaim"
SUPPORTED_LABEL = "supported"
CONTRA_LABEL = "contradiction_candidate"

ERROR_TYPES = [
    "retrieval_miss",
    "evidence_format_noise",
    "weak_selector_overlap",
    "contradiction_confusion",
    "action_lexicon_shortcut",
    "mild_vs_strong_boundary",
    "supported_overflag",
    "uncertainty_high_entropy",
    "group_variant_artifact",
]

# Thresholds (transparent, documented in summary)
SELECTOR_SCORE_LOW = 0.30       # weak_selector_overlap
ENTROPY_HIGH = 0.50             # uncertainty_high_entropy
P_CONTRA_HIGH = 0.30            # contradiction_confusion
CONTRA_NLI_HIGH = 0.30          # contradiction_confusion
EVIDENCE_WORDS_SHORT = 5        # evidence_format_noise
EVIDENCE_WORDS_LONG = 50        # evidence_format_noise
EVIDENCE_SENTENCES_MULTI = 3    # evidence_format_noise (>=3 sentences = noisy)
SELECTED_RANK_HIGH = 5          # evidence_format_noise (rank > 5 = weak retrieval)

# Action lexicon for action_lexicon_shortcut detection
ACTION_LEXICON = [
    "extend", "extends", "extended", "extending",
    "add", "adds", "added", "adding",
    "improve", "improves", "improved", "improving",
    "propose", "proposes", "proposed", "proposing",
    "introduce", "introduces", "introduced", "introducing",
    "enhance", "enhances", "enhanced", "enhancing",
    "boost", "boosts", "boosted", "boosting",
    "increase", "increases", "increased", "increasing",
    "achieve", "achieves", "achieved", "achieving",
    "enable", "enables", "enabled", "enabling",
    "optimize", "optimizes", "optimized", "optimizing",
    "design", "designs", "designed", "designing",
    "develop", "develops", "developed", "developing",
    "build", "builds", "built", "building",
    "create", "creates", "created", "creating",
    "deliver", "delivers", "delivered", "delivering",
    "provide", "provides", "provided", "providing",
]


def log(msg):
    print(msg, flush=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_inputs(
    review_scores_csv: str,
    selector_csv: str,
    retrieval_csv: str,
    candidate_csv: str,
    smart_queue_csv: Optional[str],
) -> pd.DataFrame:
    """Load and merge all input CSVs on candidate_id.

    The merged DataFrame contains one row per candidate with all fields
    needed for error taxonomy. Text fields (claim_text, evidence_text,
    selected_evidence, retrieved_text) are kept in the private DataFrame
    and stripped from the redacted output.
    """
    review = pd.read_csv(review_scores_csv, keep_default_na=False)
    selector = pd.read_csv(selector_csv, keep_default_na=False)
    retrieval = pd.read_csv(retrieval_csv, keep_default_na=False)
    candidate = pd.read_csv(candidate_csv, keep_default_na=False)

    # Validate required columns
    for name, df, required in [
        ("review_scores", review, ["candidate_id", "true_label", "pred_label"]),
        ("selector", selector, ["candidate_id"]),
        ("retrieval", retrieval, ["candidate_id"]),
        ("candidate", candidate, ["candidate_id", "target_candidate_group_id"]),
    ]:
        missing = [c for c in required if c not in df.columns]
        if missing:
            raise ValueError(f"{name} CSV missing required columns: {missing}")

    # Start with review_scores (has true_label, pred_label, selected_evidence)
    keep_from_review = [c for c in [
        "candidate_id", "true_label", "pred_label", "strong_action_flag",
        "strong_action_score", "p_contra_mean", "priority_score",
        "selected_evidence", "selected_chunk_id", "selected_rank",
        "source_pdf", "page", "route", "n_seeds_voted", "vote_share_strong",
    ] if c in review.columns]
    df = review[keep_from_review].copy()

    # Add selector features (p_strong, p_contra, entropy, selector_score, etc.)
    selector_cols = [c for c in [
        "p_strong", "p_contra", "p_svm", "entailment", "neutral",
        "contradiction_nli", "entropy", "selector_score",
        "selected_rank", "selected_n_words", "bm25_score", "oracle_hit",
    ] if c in selector.columns]
    for col in selector_cols:
        # Prefer selector_csv version, rename to avoid conflicts
        if col in df.columns:
            df = df.drop(columns=[col])
        df[col] = df["candidate_id"].map(
            selector.set_index("candidate_id")[col].to_dict()
        )

    # Add retrieval info: for each candidate, did any retrieved chunk hit oracle?
    # Aggregate retrieval_csv to one row per candidate_id
    if "is_oracle_hit" in retrieval.columns:
        retrieval_agg = retrieval.groupby("candidate_id").agg(
            any_oracle_hit=("is_oracle_hit", "max"),
            n_retrieved_chunks=("rank", "count"),
            best_bm25_score=("bm25_score", "max"),
        ).reset_index()
        df = df.merge(retrieval_agg, on="candidate_id", how="left")
        df["any_oracle_hit"] = df["any_oracle_hit"].fillna(0).astype(int)
        df["n_retrieved_chunks"] = df["n_retrieved_chunks"].fillna(0).astype(int)
        df["best_bm25_score"] = df["best_bm25_score"].fillna(0.0)
    else:
        df["any_oracle_hit"] = 0
        df["n_retrieved_chunks"] = 0
        df["best_bm25_score"] = 0.0

    # Add candidate info (target_candidate_group_id, claim_text, evidence_text)
    candidate_keep = [c for c in [
        "candidate_id", "target_candidate_group_id",
        "claim_text", "evidence_text",
        "claim_text_sha256", "evidence_text_sha256",
        "domain", "source_id", "group_quality_tier",
    ] if c in candidate.columns]
    df = df.merge(candidate[candidate_keep], on="candidate_id", how="left")

    # Add smart_queue info if provided
    if smart_queue_csv:
        sq = pd.read_csv(smart_queue_csv, keep_default_na=False)
        sq_keep = [c for c in [
            "candidate_id", "bucket", "score_conservative",
            "score_balanced", "score_high_recall", "final_score",
        ] if c in sq.columns]
        if "candidate_id" in sq_keep:
            df = df.merge(sq[sq_keep], on="candidate_id", how="left")

    return df


# ---------------------------------------------------------------------------
# Error type detection
# ---------------------------------------------------------------------------

def _safe_str(x) -> str:
    if x is None or (isinstance(x, float) and math.isnan(x)):
        return ""
    return str(x)


def _safe_float(x, default=0.0) -> float:
    if x is None or x == "":
        return default
    try:
        return float(x)
    except (ValueError, TypeError):
        return default


def _safe_int(x, default=0) -> int:
    if x is None or x == "":
        return default
    try:
        return int(float(x))
    except (ValueError, TypeError):
        return default


def _count_sentences(text: str) -> int:
    if not text:
        return 0
    # Simple sentence counter: count sentence-ending punctuation
    count = len(re.findall(r"[.!?]+", text))
    return max(1, count)


def _has_action_words(text: str) -> Set[str]:
    if not text:
        return set()
    words = set(re.findall(r"\b[a-z]+\b", text.lower()))
    return words & set(ACTION_LEXICON)


def tag_retrieval_miss(row) -> bool:
    """BM25 top-k has no oracle/evidence overlap."""
    oracle_hit = _safe_int(row.get("oracle_hit", 0))
    any_oracle = _safe_int(row.get("any_oracle_hit", 0))
    return oracle_hit == 0 and any_oracle == 0


def tag_evidence_format_noise(row) -> bool:
    """Selected evidence too long, too short, multi-sentence, or high rank."""
    n_words = _safe_int(row.get("selected_n_words", 0))
    selected_rank = _safe_int(row.get("selected_rank", 0))
    evidence = _safe_str(row.get("selected_evidence", ""))
    n_sentences = _count_sentences(evidence)

    if n_words > 0 and n_words < EVIDENCE_WORDS_SHORT:
        return True
    if n_words > EVIDENCE_WORDS_LONG:
        return True
    if n_sentences >= EVIDENCE_SENTENCES_MULTI:
        return True
    if selected_rank > SELECTED_RANK_HIGH:
        return True
    return False


def tag_weak_selector_overlap(row) -> bool:
    """Selector_score below threshold."""
    score = _safe_float(row.get("selector_score", 0.0))
    return score < SELECTOR_SCORE_LOW


def tag_contradiction_confusion(row) -> bool:
    """p_contra or contradiction_nli high, but label is not contradiction."""
    p_contra = _safe_float(row.get("p_contra", 0.0))
    contra_nli = _safe_float(row.get("contradiction_nli", 0.0))
    true_label = _safe_str(row.get("true_label", ""))
    pred_label = _safe_str(row.get("pred_label", ""))

    high_contra_signal = p_contra > P_CONTRA_HIGH or contra_nli > CONTRA_NLI_HIGH
    if not high_contra_signal:
        return False
    # Confusion: contra signal high but neither true nor pred is contradiction
    if true_label != CONTRA_LABEL and pred_label != CONTRA_LABEL:
        return True
    # Or pred=contradiction but true is not (FP for contradiction)
    if pred_label == CONTRA_LABEL and true_label != CONTRA_LABEL:
        return True
    return False


def tag_action_lexicon_shortcut(row) -> bool:
    """Action words in claim, no corresponding support in evidence."""
    claim = _safe_str(row.get("claim_text", ""))
    evidence = _safe_str(row.get("evidence_text", ""))
    if not claim or not evidence:
        return False

    claim_actions = _has_action_words(claim)
    if not claim_actions:
        return False

    # Check if action words appear in evidence
    evidence_lower = evidence.lower()
    unsupported = [w for w in claim_actions if w not in evidence_lower]
    # If more than half the action words are unsupported, flag
    if len(unsupported) >= max(1, len(claim_actions) // 2):
        return True
    return False


def tag_mild_vs_strong_boundary(row) -> bool:
    """mild_scope_overclaim and strong_action_overclaim confusion."""
    true_label = _safe_str(row.get("true_label", ""))
    pred_label = _safe_str(row.get("pred_label", ""))
    return (
        (true_label == MILD_LABEL and pred_label == STRONG_LABEL)
        or (true_label == STRONG_LABEL and pred_label == MILD_LABEL)
    )


def tag_supported_overflag(row) -> bool:
    """Supported candidate flagged with strong_action_flag=1."""
    true_label = _safe_str(row.get("true_label", ""))
    flag = _safe_int(row.get("strong_action_flag", 0))
    return true_label == SUPPORTED_LABEL and flag == 1


def tag_uncertainty_high_entropy(row) -> bool:
    """Entropy above threshold causing instability."""
    entropy = _safe_float(row.get("entropy", 0.0))
    return entropy > ENTROPY_HIGH


def tag_group_variant_artifact(row, group_stats: Dict[str, Dict]) -> bool:
    """Same group's template variants cause confusion.

    A group is flagged if it has multiple candidates with different true_labels
    but the same pred_label (suggesting the model can't distinguish variants).
    """
    gid = _safe_str(row.get("target_candidate_group_id", ""))
    if not gid or gid not in group_stats:
        return False
    stats = group_stats[gid]
    # Group must have multiple distinct true_labels
    if stats["n_true_labels"] < 2:
        return False
    # And the model predicted the same label for all (or most) of them
    if stats["n_pred_labels"] == 1:
        return True
    return False


def compute_group_stats(df: pd.DataFrame) -> Dict[str, Dict]:
    """Compute per-group statistics for group_variant_artifact detection."""
    if "target_candidate_group_id" not in df.columns:
        return {}
    stats = {}
    for gid, group in df.groupby("target_candidate_group_id"):
        true_labels = set(group["true_label"].dropna().unique()) if "true_label" in group.columns else set()
        pred_labels = set(group["pred_label"].dropna().unique()) if "pred_label" in group.columns else set()
        stats[str(gid)] = {
            "n_candidates": len(group),
            "n_true_labels": len(true_labels),
            "n_pred_labels": len(pred_labels),
            "true_labels": sorted(true_labels),
            "pred_labels": sorted(pred_labels),
        }
    return stats


def assign_error_tags(df: pd.DataFrame) -> pd.DataFrame:
    """Assign error type tags to each row.

    Returns DataFrame with an 'error_type_tags' column (semicolon-separated)
    and individual boolean columns for each error type.
    """
    group_stats = compute_group_stats(df)

    tags_list = []
    for _, row in df.iterrows():
        tags = []
        if tag_retrieval_miss(row):
            tags.append("retrieval_miss")
        if tag_evidence_format_noise(row):
            tags.append("evidence_format_noise")
        if tag_weak_selector_overlap(row):
            tags.append("weak_selector_overlap")
        if tag_contradiction_confusion(row):
            tags.append("contradiction_confusion")
        if tag_action_lexicon_shortcut(row):
            tags.append("action_lexicon_shortcut")
        if tag_mild_vs_strong_boundary(row):
            tags.append("mild_vs_strong_boundary")
        if tag_supported_overflag(row):
            tags.append("supported_overflag")
        if tag_uncertainty_high_entropy(row):
            tags.append("uncertainty_high_entropy")
        if tag_group_variant_artifact(row, group_stats):
            tags.append("group_variant_artifact")

        tags_list.append(";".join(tags) if tags else "")

    df = df.copy()
    df["error_type_tags"] = tags_list
    return df


# ---------------------------------------------------------------------------
# FP/FN classification
# ---------------------------------------------------------------------------

def classify_fp_fn(df: pd.DataFrame) -> pd.DataFrame:
    """Classify each candidate as TP, FP, FN, or TN.

    FP: pred=strong_action_overclaim but true != strong_action_overclaim
    FN: true=strong_action_overclaim but pred != strong_action_overclaim
    """
    df = df.copy()
    true = df["true_label"].astype(str)
    pred = df["pred_label"].astype(str)

    is_strong_true = (true == STRONG_LABEL)
    is_strong_pred = (pred == STRONG_LABEL)

    df["error_category"] = "TN"
    df.loc[is_strong_true & is_strong_pred, "error_category"] = "TP"
    df.loc[~is_strong_true & is_strong_pred, "error_category"] = "FP"
    df.loc[is_strong_true & ~is_strong_pred, "error_category"] = "FN"
    return df


# ---------------------------------------------------------------------------
# SHA-256 hashing for redacted output
# ---------------------------------------------------------------------------

def sha256_hash(text: str) -> str:
    if not text:
        return ""
    return hashlib.sha256(str(text).encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

PRIVATE_TEXT_COLUMNS = [
    "claim_text", "evidence_text", "selected_evidence", "retrieved_text",
]

REDACTED_KEEP_COLUMNS = [
    "candidate_id",
    "target_candidate_group_id",
    "true_label",
    "pred_label",
    "error_category",
    "error_type_tags",
    "p_strong",
    "p_contra",
    "contradiction_nli",
    "entropy",
    "selector_score",
    "selected_n_words",
    "selected_rank",
    "bm25_score",
    "oracle_hit",
    "any_oracle_hit",
    "strong_action_flag",
    "strong_action_score",
    "priority_score",
    "selected_evidence_sha256",
    "claim_text_sha256",
    "evidence_text_sha256",
    "domain",
    "group_quality_tier",
]


def write_private_output(df: pd.DataFrame, output_path: Path) -> None:
    """Write private output with full text fields."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    log(f"  Private output: {output_path} ({len(df)} rows)")


def write_redacted_output(df: pd.DataFrame, output_path: Path) -> None:
    """Write redacted public output with no raw text, only hashes."""
    redacted = df.copy()

    # Add SHA-256 hashes for text fields
    if "selected_evidence" in redacted.columns:
        redacted["selected_evidence_sha256"] = redacted["selected_evidence"].apply(sha256_hash)
    else:
        redacted["selected_evidence_sha256"] = ""

    if "claim_text_sha256" not in redacted.columns:
        if "claim_text" in redacted.columns:
            redacted["claim_text_sha256"] = redacted["claim_text"].apply(sha256_hash)
        else:
            redacted["claim_text_sha256"] = ""

    if "evidence_text_sha256" not in redacted.columns:
        if "evidence_text" in redacted.columns:
            redacted["evidence_text_sha256"] = redacted["evidence_text"].apply(sha256_hash)
        else:
            redacted["evidence_text_sha256"] = ""

    # Keep only allowed columns
    keep = [c for c in REDACTED_KEEP_COLUMNS if c in redacted.columns]
    redacted = redacted[keep]

    # Drop any remaining text columns (safety net)
    for col in PRIVATE_TEXT_COLUMNS:
        if col in redacted.columns:
            redacted = redacted.drop(columns=[col])

    output_path.parent.mkdir(parents=True, exist_ok=True)
    redacted.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    log(f"  Redacted output: {output_path} ({len(redacted)} rows, {len(redacted.columns)} cols)")


def write_summary_csv(df: pd.DataFrame, output_path: Path) -> None:
    """Write error taxonomy summary CSV."""
    # Only consider error cases (FP + FN)
    error_df = df[df["error_category"].isin(["FP", "FN"])].copy()
    total_errors = len(error_df)
    if total_errors == 0:
        total_errors = 1  # avoid div-by-zero

    rows = []
    for etype in ERROR_TYPES:
        mask = error_df["error_type_tags"].str.contains(etype, na=False)
        subset = error_df[mask]
        n_cases = len(subset)
        fp_count = int((subset["error_category"] == "FP").sum())
        fn_count = int((subset["error_category"] == "FN").sum())
        # Example candidate IDs (up to 5)
        examples = subset["candidate_id"].head(5).tolist()
        rows.append({
            "error_type": etype,
            "n_cases": n_cases,
            "pct_cases": round(n_cases / total_errors * 100, 2) if total_errors > 0 else 0.0,
            "fp_count": fp_count,
            "fn_count": fn_count,
            "example_candidate_ids": ";".join(examples),
        })

    summary = pd.DataFrame(rows)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    summary.to_csv(output_path, index=False, quoting=csv.QUOTE_ALL)
    log(f"  Summary CSV: {output_path} ({len(summary)} error types)")


def write_summary_md(
    df: pd.DataFrame,
    summary_csv: Path,
    output_path: Path,
    n_total: int,
    n_fp: int,
    n_fn: int,
    n_groups: int,
) -> None:
    """Write paper-readable markdown summary."""
    summary = pd.read_csv(summary_csv, keep_default_na=False)

    lines = []
    lines.append("# Error Taxonomy Summary — V3.17 Screening Failures")
    lines.append("")
    lines.append("## Data Disclaimer")
    lines.append("")
    lines.append(
        "> **Controlled silver diagnostic data, NOT natural prevalence.** "
        "The candidate pool is a balanced 4-class sample (109 per class, 436 total) "
        "generated from SimClaim v2. Error rates and type distributions reflect "
        "this controlled setting and must not be interpreted as real-world base rates."
    )
    lines.append("")

    lines.append("## Overview")
    lines.append("")
    lines.append(f"- Total candidates: **{n_total}**")
    lines.append(f"- False positives (FP): **{n_fp}**")
    lines.append(f"- False negatives (FN): **{n_fn}**")
    lines.append(f"- Target candidate groups: **{n_groups}**")
    lines.append(f"- Error type categories: **{len(ERROR_TYPES)}**")
    lines.append("")
    lines.append(
        "FP = predicted `strong_action_overclaim` but true label is not.  "
        "FN = true `strong_action_overclaim` but predicted otherwise."
    )
    lines.append("")

    lines.append("## Error Type Distribution")
    lines.append("")
    lines.append("| Error Type | n_cases | % of errors | FP | FN |")
    lines.append("|---|---:|---:|---:|---:|")
    for _, row in summary.iterrows():
        lines.append(
            f"| {row['error_type']} | {row['n_cases']} | "
            f"{row['pct_cases']:.1f}% | {row['fp_count']} | {row['fn_count']} |"
        )
    lines.append("")

    # Top FP and FN causes
    fp_summary = summary.sort_values("fp_count", ascending=False).head(3)
    fn_summary = summary.sort_values("fn_count", ascending=False).head(3)

    lines.append("## Top FP Causes (false alarms)")
    lines.append("")
    for _, row in fp_summary.iterrows():
        if row["fp_count"] > 0:
            lines.append(
                f"- **{row['error_type']}** ({row['fp_count']} FP cases, "
                f"{row['pct_cases']:.1f}% of all errors)"
            )
    lines.append("")

    lines.append("## Top FN Causes (missed strong-action overclaims)")
    lines.append("")
    for _, row in fn_summary.iterrows():
        if row["fn_count"] > 0:
            lines.append(
                f"- **{row['error_type']}** ({row['fn_count']} FN cases, "
                f"{row['pct_cases']:.1f}% of all errors)"
            )
    lines.append("")

    lines.append("## Implications for Future Work")
    lines.append("")
    lines.append(
        "1. **Retrieval quality**: `retrieval_miss` cases indicate where BM25 "
        "top-k fails to surface oracle evidence; neural reranking or query "
        "expansion may help."
    )
    lines.append(
        "2. **Evidence canonicalization**: `evidence_format_noise` cases suggest "
        "the unsupervised sentence selector sometimes picks overly long, short, "
        "or multi-sentence evidence; a length-aware selector may reduce noise."
    )
    lines.append(
        "3. **Calibration**: `uncertainty_high_entropy` and `contradiction_confusion` "
        "cases indicate where classifier confidence is misplaced; temperature "
        "scaling or ensemble calibration may improve robustness."
    )
    lines.append(
        "4. **Lexical shortcuts**: `action_lexicon_shortcut` cases suggest the "
        "model may over-rely on action verbs in claims without verifying evidence "
        "support; adversarial lexical pairs (same evidence, different claim wording) "
        "are the targeted diagnostic."
    )
    lines.append(
        "5. **Group variant sensitivity**: `group_variant_artifact` cases show "
        "where template variants within the same group confuse the classifier; "
        "group-aware training or hard-negative mining may help."
    )
    lines.append("")
    lines.append("## Thresholds Used")
    lines.append("")
    lines.append(f"- `selector_score < {SELECTOR_SCORE_LOW}` → weak_selector_overlap")
    lines.append(f"- `entropy > {ENTROPY_HIGH}` → uncertainty_high_entropy")
    lines.append(f"- `p_contra > {P_CONTRA_HIGH}` or `contradiction_nli > {CONTRA_NLI_HIGH}` → contradiction_confusion")
    lines.append(f"- `selected_n_words < {EVIDENCE_WORDS_SHORT}` or `> {EVIDENCE_WORDS_LONG}` → evidence_format_noise")
    lines.append(f"- `selected_rank > {SELECTED_RANK_HIGH}` → evidence_format_noise")
    lines.append(f"- `n_sentences >= {EVIDENCE_SENTENCES_MULTI}` → evidence_format_noise")
    lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")
    log(f"  Summary MD: {output_path}")


def write_run_summary_json(
    output_path: Path,
    n_total: int,
    n_fp: int,
    n_fn: int,
    n_tp: int,
    n_tn: int,
    n_groups: int,
    error_type_counts: Dict[str, int],
    guards: Dict,
) -> None:
    """Write machine-readable summary JSON."""
    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "data_disclaimer": (
            "Controlled silver diagnostic data, NOT natural prevalence. "
            "Balanced 4-class pool (109 per class, 436 total). "
            "Error rates reflect this controlled setting."
        ),
        "n_candidates": n_total,
        "n_groups": n_groups,
        "n_tp": n_tp,
        "n_fp": n_fp,
        "n_fn": n_fn,
        "n_tn": n_tn,
        "error_type_counts": error_type_counts,
        "thresholds": {
            "selector_score_low": SELECTOR_SCORE_LOW,
            "entropy_high": ENTROPY_HIGH,
            "p_contra_high": P_CONTRA_HIGH,
            "contra_nli_high": CONTRA_NLI_HIGH,
            "evidence_words_short": EVIDENCE_WORDS_SHORT,
            "evidence_words_long": EVIDENCE_WORDS_LONG,
            "evidence_sentences_multi": EVIDENCE_SENTENCES_MULTI,
            "selected_rank_high": SELECTED_RANK_HIGH,
        },
        "guards": guards,
        "label_usage_policy": (
            "true_label is used ONLY for error analysis (FP/FN definition and "
            "error type tagging). It is NEVER used for scoring, ranking, or "
            "feature engineering."
        ),
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    log(f"  Summary JSON: {output_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def resolve_default_path(name: str, toy_mode: bool) -> str:
    """Resolve default input path based on mode."""
    if toy_mode:
        defaults = {
            "review_scores_csv": "experiments/canonicalized_review_queue_v1_toy/canonicalized_r4_review_scores.csv",
            "selector_csv": "experiments/canonicalized_risk_ranking_v1_toy/risk_ranking_features.csv",
            "retrieval_csv": "experiments/simclaim_pdf_corpus_retrieval_v1_toy/retrieval_results_bm25.csv",
            "candidate_csv": "data/toy_synthetic/toy_candidates_v1.csv",
            "smart_queue_csv": "experiments/lightweight_smart_queue_v1_toy/smart_queue_scores.csv",
        }
    else:
        defaults = {
            "review_scores_csv": "experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv",
            "selector_csv": "experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv",
            "retrieval_csv": "experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv",
            "candidate_csv": "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv",
            "smart_queue_csv": "experiments/lightweight_smart_queue_v1/smart_queue_scores.csv",
        }
    return defaults.get(name, "")


def main():
    parser = argparse.ArgumentParser(
        description="Error taxonomy analysis for V3.17 screening failures."
    )
    parser.add_argument("--review_scores_csv", default=None,
                        help="CSV with candidate_id, true_label, pred_label, selected_evidence")
    parser.add_argument("--selector_csv", default=None,
                        help="CSV with p_strong, p_contra, entropy, selector_score, oracle_hit")
    parser.add_argument("--retrieval_csv", default=None,
                        help="CSV with retrieval results (is_oracle_hit, bm25_score)")
    parser.add_argument("--candidate_csv", default=None,
                        help="CSV with claim_text, evidence_text, target_candidate_group_id")
    parser.add_argument("--smart_queue_csv", default=None,
                        help="Optional CSV with smart_queue scores (bucket, final_score)")
    parser.add_argument("--output_dir", default="experiments/error_taxonomy_v1",
                        help="Output directory")
    parser.add_argument("--config", default=None,
                        help="YAML config file (overrides defaults)")
    parser.add_argument("--toy_mode", action="store_true",
                        help="Use toy data defaults")
    args = parser.parse_args()

    # Load config if provided
    config = {}
    guards = {}
    if args.config:
        config = load_and_validate(args.config)
        guards = config.get("guards", {})
    else:
        # Default guards (no config file)
        guards = {
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
        }

    log("=" * 72)
    log("Error Taxonomy v1 — V3.17 Screening Failure Analysis")
    log("=" * 72)
    log(f"Output dir: {args.output_dir}")
    log(f"Toy mode: {args.toy_mode}")
    log(f"Guards: {guards}")
    log("")

    # Resolve input paths
    review_scores_csv = args.review_scores_csv or resolve_default_path("review_scores_csv", args.toy_mode)
    selector_csv = args.selector_csv or resolve_default_path("selector_csv", args.toy_mode)
    retrieval_csv = args.retrieval_csv or resolve_default_path("retrieval_csv", args.toy_mode)
    candidate_csv = args.candidate_csv or resolve_default_path("candidate_csv", args.toy_mode)
    smart_queue_csv = args.smart_queue_csv or resolve_default_path("smart_queue_csv", args.toy_mode)

    # Validate inputs exist
    for name, path in [
        ("review_scores_csv", review_scores_csv),
        ("selector_csv", selector_csv),
        ("retrieval_csv", retrieval_csv),
        ("candidate_csv", candidate_csv),
    ]:
        full_path = Path(path) if Path(path).is_absolute() else REPO_ROOT / path
        if not full_path.exists():
            log(f"  [ERROR] {name} not found: {full_path}")
            sys.exit(1)
        log(f"  {name}: {full_path}")

    sq_path = Path(smart_queue_csv) if Path(smart_queue_csv).is_absolute() else REPO_ROOT / smart_queue_csv
    if smart_queue_csv and sq_path.exists():
        log(f"  smart_queue_csv: {sq_path}")
    else:
        smart_queue_csv = None
        log("  smart_queue_csv: (not provided or not found, skipping)")

    log("")

    # Load and merge data
    log("Loading and merging input data...")
    df = load_inputs(
        str(Path(review_scores_csv) if Path(review_scores_csv).is_absolute() else REPO_ROOT / review_scores_csv),
        str(Path(selector_csv) if Path(selector_csv).is_absolute() else REPO_ROOT / selector_csv),
        str(Path(retrieval_csv) if Path(retrieval_csv).is_absolute() else REPO_ROOT / retrieval_csv),
        str(Path(candidate_csv) if Path(candidate_csv).is_absolute() else REPO_ROOT / candidate_csv),
        str(sq_path) if smart_queue_csv else None,
    )
    log(f"  Merged: {len(df)} candidates, {len(df.columns)} columns")

    # Classify FP/FN
    log("Classifying FP/FN...")
    df = classify_fp_fn(df)
    n_total = len(df)
    n_tp = int((df["error_category"] == "TP").sum())
    n_fp = int((df["error_category"] == "FP").sum())
    n_fn = int((df["error_category"] == "FN").sum())
    n_tn = int((df["error_category"] == "TN").sum())
    n_groups = df["target_candidate_group_id"].nunique() if "target_candidate_group_id" in df.columns else 0
    log(f"  TP={n_tp}, FP={n_fp}, FN={n_fn}, TN={n_tn}, Groups={n_groups}")

    # Assign error tags
    log("Assigning error type tags...")
    df = assign_error_tags(df)

    # Count error types
    error_df = df[df["error_category"].isin(["FP", "FN"])].copy()
    error_type_counts = {}
    for etype in ERROR_TYPES:
        count = int(error_df["error_type_tags"].str.contains(etype, na=False).sum())
        error_type_counts[etype] = count
    log(f"  Error type counts: {error_type_counts}")

    # Write outputs
    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    log("Writing outputs...")

    # Private output (full text)
    private_dir = output_dir / "private"
    write_private_output(df, private_dir / "error_cases_private.csv")

    # Redacted public output (no raw text)
    write_redacted_output(df, output_dir / "error_cases_redacted.csv")

    # Summary CSV
    write_summary_csv(df, output_dir / "error_taxonomy_summary.csv")

    # Summary MD (paper-readable)
    write_summary_md(
        df,
        output_dir / "error_taxonomy_summary.csv",
        output_dir / "error_taxonomy_summary.md",
        n_total, n_fp, n_fn, n_groups,
    )

    # Summary JSON (machine-readable)
    write_run_summary_json(
        output_dir / "error_taxonomy_summary.json",
        n_total, n_fp, n_fn, n_tp, n_tn, n_groups,
        error_type_counts, guards,
    )

    # Run config snapshot
    write_run_config(output_dir, config, "run_error_taxonomy_v1.py", extra={
        "inputs": {
            "review_scores_csv": str(review_scores_csv),
            "selector_csv": str(selector_csv),
            "retrieval_csv": str(retrieval_csv),
            "candidate_csv": str(candidate_csv),
            "smart_queue_csv": str(smart_queue_csv) if smart_queue_csv else None,
        },
        "output_dir": str(output_dir),
        "toy_mode": args.toy_mode,
        "guards": guards,
        "thresholds": {
            "selector_score_low": SELECTOR_SCORE_LOW,
            "entropy_high": ENTROPY_HIGH,
            "p_contra_high": P_CONTRA_HIGH,
            "contra_nli_high": CONTRA_NLI_HIGH,
            "evidence_words_short": EVIDENCE_WORDS_SHORT,
            "evidence_words_long": EVIDENCE_WORDS_LONG,
            "evidence_sentences_multi": EVIDENCE_SENTENCES_MULTI,
            "selected_rank_high": SELECTED_RANK_HIGH,
        },
        "data_disclaimer": (
            "Controlled silver diagnostic data, NOT natural prevalence. "
            "Balanced 4-class pool. Error rates reflect this controlled setting."
        ),
        "label_usage_policy": (
            "true_label used ONLY for error analysis (FP/FN definition). "
            "Never used for scoring, ranking, or feature engineering."
        ),
        "error_counts": {
            "n_total": n_total,
            "n_tp": n_tp,
            "n_fp": n_fp,
            "n_fn": n_fn,
            "n_tn": n_tn,
            "n_groups": n_groups,
        },
        "error_type_counts": error_type_counts,
    })

    # Schema validation: verify redacted output has no text columns
    redacted_path = output_dir / "error_cases_redacted.csv"
    try:
        redacted_df = pd.read_csv(redacted_path, keep_default_na=False)
        leaked_text_cols = [
            c for c in redacted_df.columns
            if any(t in c.lower() for t in ("claim_text", "evidence_text", "selected_evidence", "retrieved_text"))
            and "sha256" not in c.lower()
        ]
        if leaked_text_cols:
            log(f"  [ERROR] Redacted output leaked text columns: {leaked_text_cols}")
        else:
            log(f"  [OK] Redacted output clean: no raw text columns")
    except Exception as e:
        log(f"  [WARN] Redacted output check skipped: {e}")

    log("")
    log("Done. Outputs written to:")
    log(f"  {output_dir}")
    log("")
    log("  PRIVATE (do not commit, do not share):")
    log(f"    private/error_cases_private.csv  ({len(df)} rows, full text)")
    log("  PUBLIC (redacted, safe to share):")
    log(f"    error_cases_redacted.csv         (no raw text, hashes only)")
    log(f"    error_taxonomy_summary.csv       (counts per error type)")
    log(f"    error_taxonomy_summary.md        (paper-readable)")
    log(f"    error_taxonomy_summary.json      (machine-readable)")
    log(f"    run_config.json                  (config snapshot)")


if __name__ == "__main__":
    main()
