#!/usr/bin/env python
"""run_canonicalizer_ablation_v1.py — Unified evidence canonicalizer ablation.

Compares 8 evidence selectors to show that raw retrieved chunks are not
screening-compatible evidence units, while short canonicalized spans
restore screening signal.

Hard boundaries:
  - no network, no API, no cloud
  - no model training
  - no R4 threshold changes
  - no original data modification
  - no label/oracle fields used for evidence selection
  - oracle metrics computed only AFTER selection (evaluation only)
"""

import argparse
import csv
import hashlib
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402
from schema_utils import (  # noqa: E402
    validate_csv_file,
    validate_redacted_csv_file,
    write_schema_validation_report,
)

# ---------------------------------------------------------------------------
# Config (single source of truth)
# ---------------------------------------------------------------------------

CONFIG = {
    "top_k": 5,
    "min_sentence_words": 8,
    "max_sentence_words": 60,
    "short_penalty": 0.5,
    "long_penalty": 0.7,
    "oracle_overlap_threshold": 0.65,
    "no_network": True,
    "no_api": True,
    "no_training": True,
}

FORBIDDEN_SELECTION_FIELDS = {
    "true_label",
    "candidate_label_guess",
    "gold_label",
    "human_audited",
    "oracle_hit",
    "final_label",
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
}

USED_FOR_SELECTION = [
    "claim_text",
    "retrieved_text",
    "rank",
    "page_number",
    "unit_id",
    "chunk_id",
    "bm25_score",
]

MINIMAL_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "as", "if", "then", "than", "so", "such", "not", "no", "nor", "just",
    "only", "also", "too", "very", "more", "most", "some", "any", "all",
}

SELECTOR_NAMES = [
    "raw_top1_chunk",
    "cleaned_top1_chunk",
    "first_sentence_top1",
    "best_sentence_top1_overlap",
    "best_sentence_top5_overlap",
    "three_sentence_window_top5",
    "sentence_bm25_top1",
    "window_bm25_top1",
]

DEFAULT_SELECTOR = "best_sentence_top5_overlap"

# ---------------------------------------------------------------------------
# Tokenizer and scoring
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def tokenize(text):
    if not text:
        return []
    text = text.lower()
    tokens = _TOKEN_RE.findall(text)
    return [t for t in tokens if t not in MINIMAL_STOPWORDS]


def overlap_f1(claim_tokens, sent_tokens):
    """Dice coefficient = 2*|intersection| / (|A| + |B|)."""
    if not claim_tokens or not sent_tokens:
        return 0.0
    claim_set = set(claim_tokens)
    sent_set = set(sent_tokens)
    overlap = len(claim_set & sent_set)
    if overlap == 0:
        return 0.0
    return 2.0 * overlap / (len(claim_set) + len(sent_set))


def length_penalty(n_words):
    if n_words < CONFIG["min_sentence_words"]:
        return CONFIG["short_penalty"]
    if n_words > CONFIG["max_sentence_words"]:
        return CONFIG["long_penalty"]
    return 1.0


def sha256_text(text):
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Text cleaning and sentence splitting
# ---------------------------------------------------------------------------

_HYPHEN_RE = re.compile(r"-\s*\n\s*")
_WS_RE = re.compile(r"\s+")
_PAGE_NUM_RE = re.compile(r"\b\d+\s*/\s*\d+\b")
_SENT_SPLIT_RE = re.compile(r"(?<=[.!?])\s+")
_ABBREV = {"dr.", "mr.", "mrs.", "ms.", "ph.d.", "e.g.", "i.e.", "etc.", "vs.", "fig.", "eq.", "no.", "vol.", "pp.", "p."}


def clean_chunk_text(text):
    """Dehyphenate, normalize whitespace, remove page-number metadata."""
    if not text:
        return ""
    text = _HYPHEN_RE.sub("", text)
    text = _PAGE_NUM_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


def split_sentences(text):
    """Split text into sentences with abbreviation guard."""
    if not text:
        return []
    raw = _SENT_SPLIT_RE.split(text.strip())
    sentences = []
    for s in raw:
        s = s.strip()
        if not s:
            continue
        sentences.append(s)
    # Merge abbreviation-caused splits
    merged = []
    for s in sentences:
        if merged and any(merged[-1].lower().endswith(ab) for ab in _ABBREV):
            merged[-1] = merged[-1] + " " + s
        else:
            merged.append(s)
    return merged


# ---------------------------------------------------------------------------
# Anti-leakage guard
# ---------------------------------------------------------------------------

def assert_no_forbidden_fields_used_for_selection(fields_read):
    """Assert no forbidden field is used in evidence selection."""
    forbidden_used = FORBIDDEN_SELECTION_FIELDS & set(fields_read)
    if forbidden_used:
        raise AssertionError(
            f"FATAL: forbidden fields used for selection: {forbidden_used}"
        )


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates(csv_path):
    """Load candidate CSV. Only reads allowed fields."""
    fields_actually_read = [
        "candidate_id", "target_candidate_group_id", "claim_text",
        "pdf_filename", "page_number", "evidence_text", "evidence_text_sha256",
    ]
    assert_no_forbidden_fields_used_for_selection(fields_actually_read)

    candidates = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = {
                "candidate_id": row.get("candidate_id", ""),
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "claim_text": row.get("claim_text", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row["page_number"]) if str(row.get("page_number", "")).isdigit() else 0,
                "evidence_text": row.get("evidence_text", ""),
                "evidence_text_sha256": row.get("evidence_text_sha256", ""),
            }
            if not rec["evidence_text_sha256"] and rec["evidence_text"]:
                rec["evidence_text_sha256"] = sha256_text(rec["evidence_text"])
            candidates.append(rec)
    return candidates


def load_chunk_retrieval(csv_path):
    """Load chunk retrieval CSV. Returns dict: candidate_id -> list of chunk dicts (sorted by rank)."""
    by_cand = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_cand[row["candidate_id"]].append({
                "candidate_id": row["candidate_id"],
                "rank": int(row.get("rank", 0)),
                "chunk_id": row.get("chunk_id", ""),
                "bm25_score": float(row.get("bm25_score", 0)),
                "retrieved_text": row.get("retrieved_text", ""),
                "paper_id": row.get("paper_id", ""),
                "page_number": int(row.get("page_number", 0)) if str(row.get("page_number", "")).isdigit() else 0,
            })
    for cid in by_cand:
        by_cand[cid].sort(key=lambda x: x["rank"])
    return dict(by_cand)


def load_sentence_or_window_retrieval(csv_path):
    """Load sentence/window retrieval CSV. Returns dict: candidate_id -> list of unit dicts (sorted by rank)."""
    by_cand = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_cand[row["candidate_id"]].append({
                "candidate_id": row["candidate_id"],
                "rank": int(row.get("rank", 0)),
                "unit_id": row.get("unit_id", ""),
                "paper_id": row.get("paper_id", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row.get("page_number", 0)) if str(row.get("page_number", "")).isdigit() else 0,
                "section_hint": row.get("section_hint", "unknown"),
                "retrieved_text": row.get("retrieved_text", ""),
                "bm25_score": float(row.get("bm25_score", 0)),
            })
    for cid in by_cand:
        by_cand[cid].sort(key=lambda x: x["rank"])
    return dict(by_cand)


def build_toy_chunk_retrieval(sentence_jsonl_path, candidates):
    """Build pseudo chunk retrieval from toy sentence corpus for toy_mode.

    Groups sentences by (paper_id, page_number) into page-level chunks,
    ranks pages by token overlap with claim_text.
    """
    sentences = []
    with open(sentence_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sentences.append(json.loads(line))

    # Group by (paper_id, page_number) -> chunk
    chunks_by_paper_page = defaultdict(list)
    for s in sentences:
        key = (s["paper_id"], s["page_number"])
        chunks_by_paper_page[key].append(s)

    # For each candidate, rank pages of its pdf_filename by overlap with claim
    by_cand = defaultdict(list)
    for cand in candidates:
        cid = cand["candidate_id"]
        claim_tokens = tokenize(cand["claim_text"])
        # Find chunks matching candidate's pdf_filename
        pdf_name = cand["pdf_filename"].replace(".pdf", "")
        candidate_chunks = []
        for (paper_id, page_num), sent_list in chunks_by_paper_page.items():
            if paper_id == pdf_name:
                chunk_text = " ".join(s["clean_text"] for s in sent_list)
                chunk_tokens = tokenize(chunk_text)
                score = overlap_f1(claim_tokens, chunk_tokens)
                candidate_chunks.append({
                    "candidate_id": cid,
                    "rank": 0,  # will be set after sorting
                    "chunk_id": f"{paper_id}_p{page_num}_c0",
                    "bm25_score": round(score, 6),
                    "retrieved_text": chunk_text,
                    "paper_id": paper_id,
                    "page_number": page_num,
                })
        candidate_chunks.sort(key=lambda x: x["bm25_score"], reverse=True)
        for i, ch in enumerate(candidate_chunks, 1):
            ch["rank"] = i
        by_cand[cid] = candidate_chunks
    return dict(by_cand)


# ---------------------------------------------------------------------------
# Selectors
# ---------------------------------------------------------------------------

def _empty_selection(reason="no retrieval data"):
    return {
        "selected_evidence": "",
        "selected_source_unit_id": "",
        "selected_chunk_id": "",
        "selected_rank": 0,
        "selected_page_number": 0,
        "selector_score": 0.0,
        "n_words": 0,
        "source_type": "empty",
        "selection_reason": reason,
        "_sentence_index": -1,
        "_sentence_list": [],
    }


def select_raw_top1_chunk(cand, chunk_retrieval):
    chunks = chunk_retrieval.get(cand["candidate_id"], [])
    if not chunks:
        return _empty_selection("no chunk retrieval for candidate")
    top1 = chunks[0]
    text = top1["retrieved_text"]
    return {
        "selected_evidence": text,
        "selected_source_unit_id": "",
        "selected_chunk_id": top1["chunk_id"],
        "selected_rank": top1["rank"],
        "selected_page_number": top1["page_number"],
        "selector_score": top1["bm25_score"],
        "n_words": len(text.split()),
        "source_type": "raw_chunk",
        "selection_reason": "raw chunk text from rank=1 retrieval",
        "_sentence_index": -1,
        "_sentence_list": [],
    }


def select_cleaned_top1_chunk(cand, chunk_retrieval):
    raw = select_raw_top1_chunk(cand, chunk_retrieval)
    if not raw["selected_evidence"]:
        return raw
    cleaned = clean_chunk_text(raw["selected_evidence"])
    raw["selected_evidence"] = cleaned
    raw["n_words"] = len(cleaned.split())
    raw["source_type"] = "cleaned_chunk"
    raw["selection_reason"] = "cleaned (dehydrated, normalized) rank=1 chunk"
    return raw


def select_first_sentence_top1(cand, chunk_retrieval):
    cleaned = select_cleaned_top1_chunk(cand, chunk_retrieval)
    if not cleaned["selected_evidence"]:
        return cleaned
    sentences = split_sentences(cleaned["selected_evidence"])
    for idx, s in enumerate(sentences):
        n = len(s.split())
        if n >= 5:
            cleaned["selected_evidence"] = s
            cleaned["n_words"] = n
            cleaned["source_type"] = "first_sentence"
            cleaned["selection_reason"] = "first qualifying sentence (n_words>=5) from cleaned rank=1 chunk"
            cleaned["_sentence_index"] = idx
            cleaned["_sentence_list"] = sentences
            return cleaned
    # No qualifying sentence, return shortest
    if sentences:
        s = sentences[0]
        cleaned["selected_evidence"] = s
        cleaned["n_words"] = len(s.split())
        cleaned["source_type"] = "first_sentence"
        cleaned["selection_reason"] = "no sentence met n_words>=5; returned first available"
        cleaned["_sentence_index"] = 0
        cleaned["_sentence_list"] = sentences
    else:
        cleaned["selection_reason"] = "no sentences found in cleaned chunk"
    return cleaned


def _best_sentence_from_chunks(cand, chunk_retrieval, top_k):
    """Internal: find best sentence by overlap_f1 * length_penalty from top-k chunks."""
    chunks = chunk_retrieval.get(cand["candidate_id"], [])[:top_k]
    if not chunks:
        return None, None, None, None
    claim_tokens = tokenize(cand["claim_text"])
    best_score = -1.0
    best = None
    best_chunk = None
    best_idx = -1
    best_sentences = []
    for chunk in chunks:
        cleaned = clean_chunk_text(chunk["retrieved_text"])
        sentences = split_sentences(cleaned)
        for idx, s in enumerate(sentences):
            n = len(s.split())
            if n < 3:
                continue
            sent_tokens = tokenize(s)
            of1 = overlap_f1(claim_tokens, sent_tokens)
            pen = length_penalty(n)
            score = of1 * pen
            if score > best_score:
                best_score = score
                best = s
                best_chunk = chunk
                best_idx = idx
                best_sentences = sentences
    if best is None:
        return None, None, None, None
    return best, best_chunk, best_idx, best_sentences


def select_best_sentence_top1(cand, chunk_retrieval):
    best, chunk, idx, sentences = _best_sentence_from_chunks(cand, chunk_retrieval, 1)
    if best is None:
        return _empty_selection("no qualifying sentence in rank=1 chunk")
    n = len(best.split())
    return {
        "selected_evidence": best,
        "selected_source_unit_id": "",
        "selected_chunk_id": chunk["chunk_id"],
        "selected_rank": chunk["rank"],
        "selected_page_number": chunk["page_number"],
        "selector_score": round(overlap_f1(tokenize(cand["claim_text"]), tokenize(best)) * length_penalty(n), 6),
        "n_words": n,
        "source_type": "best_sentence_top1",
        "selection_reason": "highest overlap_f1*length_penalty sentence from rank=1 chunk",
        "_sentence_index": idx,
        "_sentence_list": sentences,
    }


def select_best_sentence_top5(cand, chunk_retrieval, top_k=5):
    best, chunk, idx, sentences = _best_sentence_from_chunks(cand, chunk_retrieval, top_k)
    if best is None:
        return _empty_selection(f"no qualifying sentence in top-{top_k} chunks")
    n = len(best.split())
    return {
        "selected_evidence": best,
        "selected_source_unit_id": "",
        "selected_chunk_id": chunk["chunk_id"],
        "selected_rank": chunk["rank"],
        "selected_page_number": chunk["page_number"],
        "selector_score": round(overlap_f1(tokenize(cand["claim_text"]), tokenize(best)) * length_penalty(n), 6),
        "n_words": n,
        "source_type": "best_sentence_top5",
        "selection_reason": f"highest overlap_f1*length_penalty sentence from top-{top_k} chunks",
        "_sentence_index": idx,
        "_sentence_list": sentences,
    }


def select_window_top5(cand, chunk_retrieval, top_k=5):
    base = select_best_sentence_top5(cand, chunk_retrieval, top_k)
    if not base["selected_evidence"]:
        return base
    sentences = base["_sentence_list"]
    idx = base["_sentence_index"]
    if idx < 0 or not sentences:
        base["selection_reason"] = "window: no sentence list available"
        return base
    prev_s = sentences[idx - 1] if idx > 0 else ""
    next_s = sentences[idx + 1] if idx < len(sentences) - 1 else ""
    parts = [p for p in [prev_s, base["selected_evidence"], next_s] if p]
    window_text = " ".join(parts)
    base["selected_evidence"] = window_text
    base["n_words"] = len(window_text.split())
    base["source_type"] = "window_3"
    base["selection_reason"] = "3-sentence window (prev+current+next) around best_sentence_top5_overlap"
    return base


def select_sentence_bm25_top1(cand, sentence_retrieval):
    units = sentence_retrieval.get(cand["candidate_id"], [])
    if not units:
        return _empty_selection("no sentence BM25 retrieval for candidate")
    top1 = units[0]
    text = top1["retrieved_text"]
    return {
        "selected_evidence": text,
        "selected_source_unit_id": top1["unit_id"],
        "selected_chunk_id": "",
        "selected_rank": top1["rank"],
        "selected_page_number": top1["page_number"],
        "selector_score": top1["bm25_score"],
        "n_words": len(text.split()),
        "source_type": "sentence_bm25",
        "selection_reason": "rank=1 sentence from sentence BM25 retrieval",
        "_sentence_index": -1,
        "_sentence_list": [],
    }


def select_window_bm25_top1(cand, window_retrieval):
    units = window_retrieval.get(cand["candidate_id"], [])
    if not units:
        return _empty_selection("no window BM25 retrieval for candidate")
    top1 = units[0]
    text = top1["retrieved_text"]
    return {
        "selected_evidence": text,
        "selected_source_unit_id": top1["unit_id"],
        "selected_chunk_id": "",
        "selected_rank": top1["rank"],
        "selected_page_number": top1["page_number"],
        "selector_score": top1["bm25_score"],
        "n_words": len(text.split()),
        "source_type": "window_bm25",
        "selection_reason": "rank=1 window from window BM25 retrieval",
        "_sentence_index": -1,
        "_sentence_list": [],
    }


# ---------------------------------------------------------------------------
# Oracle metrics (evaluation only, computed AFTER selection)
# ---------------------------------------------------------------------------

def token_f1_eval(text1, text2):
    """Token F1 for oracle evaluation (uses sets, same as task pack 3)."""
    t1 = set(tokenize(text1))
    t2 = set(tokenize(text2))
    if not t1 or not t2:
        return 0.0
    overlap = t1 & t2
    if not overlap:
        return 0.0
    p = len(overlap) / len(t2)
    r = len(overlap) / len(t1)
    return 2 * p * r / (p + r)


def compute_oracle_for_selection(sel_result, cand):
    """Compute oracle metrics for a selected evidence. Evaluation only."""
    selected = sel_result["selected_evidence"]
    evidence = cand["evidence_text"]
    evidence_sha = cand["evidence_text_sha256"]
    selected_sha = sha256_text(selected)

    oracle_hash_exact = (selected_sha == evidence_sha) and (evidence_sha != "")
    oracle_page_match = (sel_result["selected_page_number"] == cand["page_number"]) and (cand["page_number"] > 0)
    oracle_overlap = token_f1_eval(selected, evidence) if evidence else 0.0
    oracle_hit = oracle_hash_exact or (oracle_page_match and oracle_overlap >= CONFIG["oracle_overlap_threshold"])
    return {
        "oracle_hash_exact": oracle_hash_exact,
        "oracle_page_match": oracle_page_match,
        "oracle_overlap_score": round(oracle_overlap, 6),
        "oracle_hit": oracle_hit,
    }


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_selector_evidence_csv(filepath, all_results):
    fields = [
        "candidate_id", "target_candidate_group_id", "selector",
        "selected_evidence", "selected_source_unit_id", "selected_chunk_id",
        "selected_rank", "selected_page_number", "selector_score", "n_words",
        "source_type", "selection_reason", "selected_evidence_sha256",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in all_results:
            out = {k: row[k] for k in fields if k != "selected_evidence_sha256"}
            out["selected_evidence_sha256"] = sha256_text(row["selected_evidence"])
            writer.writerow(out)


def write_metrics_summary_csv(filepath, metrics):
    fields = [
        "selector", "n_candidates", "mean_selector_score", "median_n_words",
        "pct_empty", "pct_short_lt8", "pct_long_gt60", "mean_selected_rank",
        "oracle_recall_at_selected", "mean_oracle_overlap",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for m in metrics:
            writer.writerow(m)


def write_redacted_csv(filepath, all_results):
    fields = [
        "candidate_id", "selector", "selected_evidence_sha256", "n_words",
        "selector_score", "selected_rank", "source_type", "selection_reason",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        # top-3 per candidate per selector
        seen = set()
        for row in all_results:
            key = (row["candidate_id"], row["selector"])
            if key in seen:
                continue
            seen.add(key)
            writer.writerow({
                "candidate_id": row["candidate_id"],
                "selector": row["selector"],
                "selected_evidence_sha256": sha256_text(row["selected_evidence"]),
                "n_words": row["n_words"],
                "selector_score": row["selector_score"],
                "selected_rank": row["selected_rank"],
                "source_type": row["source_type"],
                "selection_reason": row["selection_reason"],
            })


def write_leakage_guard_report(filepath):
    report = {
        "forbidden_fields_for_selection": sorted(FORBIDDEN_SELECTION_FIELDS),
        "used_for_selection": USED_FOR_SELECTION,
        "oracle_used_for_selection": False,
        "labels_used_for_selection": False,
        "oracle_computed_after_selection": True,
        "no_network": CONFIG["no_network"],
        "no_api": CONFIG["no_api"],
        "no_training": CONFIG["no_training"],
    }
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Unified evidence canonicalizer ablation (8 selectors)."
    )
    parser.add_argument("--candidate_csv", default=None)
    parser.add_argument("--chunk_retrieval_csv", default=None)
    parser.add_argument("--sentence_retrieval_csv", default=None)
    parser.add_argument("--window_retrieval_csv", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--top_k", type=int, default=5)
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    # --- Load config ---
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    CONFIG["top_k"] = args.top_k
    output_dir = Path(args.output_dir) if args.output_dir else resolve_path(config, "canonicalizer_dir")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        candidate_csv = "data/toy_synthetic/toy_candidates_v1.csv"
        sentence_jsonl = "data/pdf_corpus_toy_v1/sentences.jsonl"
        sentence_retrieval_csv = "experiments/bm25_sentence_retrieval_v1_toy/retrieval_results_sentence_bm25.csv"
        window_retrieval_csv = "experiments/bm25_sentence_retrieval_v1_toy/retrieval_results_window_bm25.csv"
        print("[toy_mode] Using toy inputs")
    else:
        candidate_csv = args.candidate_csv or str(resolve_path(config, "candidate_csv") or "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv")
        retr_dir = resolve_path(config, "retrieval_dir") or Path("experiments/bm25_sentence_retrieval_v1")
        sentence_retrieval_csv = args.sentence_retrieval_csv or str(retr_dir / "retrieval_results_sentence_bm25.csv")
        window_retrieval_csv = args.window_retrieval_csv or str(retr_dir / "retrieval_results_window_bm25.csv")

    # --- Load inputs ---
    print(f"Loading candidates from {candidate_csv}")
    candidates = load_candidates(candidate_csv)
    print(f"  {len(candidates)} candidates loaded")

    if args.toy_mode:
        print(f"Building toy chunk retrieval from {sentence_jsonl}")
        chunk_retrieval = build_toy_chunk_retrieval(sentence_jsonl, candidates)
    else:
        print(f"Loading chunk retrieval from {args.chunk_retrieval_csv}")
        chunk_retrieval = load_chunk_retrieval(args.chunk_retrieval_csv)
    print(f"  {len(chunk_retrieval)} candidates with chunk retrieval")

    print(f"Loading sentence retrieval from {sentence_retrieval_csv}")
    sentence_retrieval = load_sentence_or_window_retrieval(sentence_retrieval_csv)
    print(f"  {len(sentence_retrieval)} candidates with sentence retrieval")

    print(f"Loading window retrieval from {window_retrieval_csv}")
    window_retrieval = load_sentence_or_window_retrieval(window_retrieval_csv)
    print(f"  {len(window_retrieval)} candidates with window retrieval")

    # --- Run all selectors ---
    selector_fns = {
        "raw_top1_chunk": lambda c: select_raw_top1_chunk(c, chunk_retrieval),
        "cleaned_top1_chunk": lambda c: select_cleaned_top1_chunk(c, chunk_retrieval),
        "first_sentence_top1": lambda c: select_first_sentence_top1(c, chunk_retrieval),
        "best_sentence_top1_overlap": lambda c: select_best_sentence_top1(c, chunk_retrieval),
        "best_sentence_top5_overlap": lambda c: select_best_sentence_top5(c, chunk_retrieval, CONFIG["top_k"]),
        "three_sentence_window_top5": lambda c: select_window_top5(c, chunk_retrieval, CONFIG["top_k"]),
        "sentence_bm25_top1": lambda c: select_sentence_bm25_top1(c, sentence_retrieval),
        "window_bm25_top1": lambda c: select_window_bm25_top1(c, window_retrieval),
    }

    all_results = []
    metrics = []

    print(f"\nRunning {len(SELECTOR_NAMES)} selectors ...")
    for sel_name in SELECTOR_NAMES:
        sel_fn = selector_fns[sel_name]
        sel_results = []
        oracle_hits = 0
        oracle_overlaps = []
        scores = []
        n_words_list = []
        ranks = []
        n_empty = 0
        n_short = 0
        n_long = 0

        for cand in candidates:
            res = sel_fn(cand)
            res["candidate_id"] = cand["candidate_id"]
            res["target_candidate_group_id"] = cand["target_candidate_group_id"]
            res["selector"] = sel_name

            # Oracle metrics (evaluation only, AFTER selection)
            oracle = compute_oracle_for_selection(res, cand)
            res["oracle_hit"] = oracle["oracle_hit"]
            res["oracle_overlap_score"] = oracle["oracle_overlap_score"]
            if oracle["oracle_hit"]:
                oracle_hits += 1
            oracle_overlaps.append(oracle["oracle_overlap_score"])

            scores.append(res["selector_score"])
            n_words_list.append(res["n_words"])
            ranks.append(res["selected_rank"])
            if res["n_words"] == 0:
                n_empty += 1
            if res["n_words"] < CONFIG["min_sentence_words"]:
                n_short += 1
            if res["n_words"] > CONFIG["max_sentence_words"]:
                n_long += 1

            sel_results.append(res)

        all_results.extend(sel_results)
        n = len(candidates)
        metrics.append({
            "selector": sel_name,
            "n_candidates": n,
            "mean_selector_score": round(sum(scores) / n, 6) if n else 0,
            "median_n_words": sorted(n_words_list)[n // 2] if n else 0,
            "pct_empty": round(n_empty / n, 6) if n else 0,
            "pct_short_lt8": round(n_short / n, 6) if n else 0,
            "pct_long_gt60": round(n_long / n, 6) if n else 0,
            "mean_selected_rank": round(sum(ranks) / n, 6) if n else 0,
            "oracle_recall_at_selected": round(oracle_hits / n, 6) if n else 0,
            "mean_oracle_overlap": round(sum(oracle_overlaps) / n, 6) if n else 0,
        })

        m = metrics[-1]
        print(f"  {sel_name}: oracle_recall={m['oracle_recall_at_selected']}, "
              f"mean_overlap={m['mean_oracle_overlap']}, "
              f"median_n_words={m['median_n_words']}")

    # --- Write outputs ---
    ev_csv = output_dir / "selector_variant_evidence.csv"
    write_selector_evidence_csv(ev_csv, all_results)
    print(f"\nWrote {ev_csv}")

    metrics_csv = output_dir / "selector_metrics_summary.csv"
    write_metrics_summary_csv(metrics_csv, metrics)
    print(f"Wrote {metrics_csv}")

    redacted_csv = output_dir / "selector_examples_redacted.csv"
    write_redacted_csv(redacted_csv, all_results)
    print(f"Wrote {redacted_csv}")

    guard_json = output_dir / "leakage_guard_report.json"
    write_leakage_guard_report(guard_json)
    print(f"Wrote {guard_json}")

    # Config dump
    config_json = output_dir / "canonicalizer_config.json"
    with open(config_json, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2, ensure_ascii=False)
    print(f"Wrote {config_json}")

    # --- Schema validation ---
    schema_reports = [
        validate_csv_file(output_dir / "selector_variant_evidence.csv", "selector_variant_evidence"),
        validate_redacted_csv_file(output_dir / "selector_examples_redacted.csv", "selector_variant_evidence"),
    ]
    write_schema_validation_report(
        output_dir, schema_reports, script_name="run_canonicalizer_ablation_v1.py"
    )
    print(f"Wrote schema_validation_report.json")

    write_run_config(output_dir, config, "run_canonicalizer_ablation_v1.py",
                     extra={"toy_mode": args.toy_mode})
    print(f"Wrote run_config.json")

    print(f"\nDefault mainline selector: {DEFAULT_SELECTOR}")
    print("Done.")


if __name__ == "__main__":
    main()
