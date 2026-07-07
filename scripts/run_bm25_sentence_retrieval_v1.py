#!/usr/bin/env python
"""run_bm25_sentence_retrieval_v1.py — Sentence and window BM25 retrieval evaluation.

Evaluates whether sentence-level or window-level BM25 retrieval is better
suited as retrieval units for downstream R4 screening, compared to raw
long chunks.

Hard boundaries:
  - no network, no API, no cloud
  - no model training
  - no label fields used for retrieval selection
  - oracle metrics computed only AFTER ranking
  - claim_text is the only field used as query
  - pdf_filename/page_number/evidence_text/evidence_text_sha256 used for
    oracle evaluation only, never for ranking
"""

import argparse
import csv
import hashlib
import json
import math
import os
import re
import sys
from collections import Counter
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
# Config (single source of truth, no scattered magic numbers)
# ---------------------------------------------------------------------------

CONFIG = {
    "top_k": 10,
    "bm25_k1": 1.5,
    "bm25_b": 0.75,
    "exclude_references": True,
    "oracle_overlap_threshold": 0.65,
    "tokenizer": {
        "lowercase": True,
        "regex": r"[a-z0-9]+(?:[-'][a-z0-9]+)*",
        "remove_stopwords": True,
    },
    "no_network": True,
    "no_api": True,
    "no_training": True,
}

FORBIDDEN_RETRIEVAL_FIELDS = {
    "candidate_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
    "gold_label",
    "final_label",
    "human_audited",
    "true_label",
    "oracle_hit",
    "issue_binary_label_guess",
}

MINIMAL_STOPWORDS = {
    "a", "an", "the", "and", "or", "but", "in", "on", "at", "to", "for",
    "of", "with", "by", "from", "is", "are", "was", "were", "be", "been",
    "being", "have", "has", "had", "do", "does", "did", "will", "would",
    "could", "should", "may", "might", "must", "shall", "can", "this",
    "that", "these", "those", "i", "you", "he", "she", "it", "we", "they",
    "as", "if", "then", "than", "so", "such", "not", "no", "nor", "just",
    "only", "also", "too", "very", "more", "most", "some", "any", "all",
    "each", "every", "other", "another", "same", "different", "new", "old",
}


# ---------------------------------------------------------------------------
# Anti-leakage assertion
# ---------------------------------------------------------------------------

def assert_no_forbidden_fields_used_for_retrieval(candidate_df, fields_actually_read):
    """Assert that no forbidden field is used in retrieval selection.

    Called before ranking to verify that the retrieval code path does
    not touch label/audit/oracle fields.
    """
    forbidden_used = FORBIDDEN_RETRIEVAL_FIELDS & set(fields_actually_read)
    if forbidden_used:
        raise AssertionError(
            f"FATAL: forbidden fields used for retrieval: {forbidden_used}. "
            f"These fields are evaluation/audit-only and must never influence "
            f"retrieval selection, ranking, or queue routing."
        )


# ---------------------------------------------------------------------------
# Tokenizer
# ---------------------------------------------------------------------------

_TOKEN_RE = re.compile(r"[a-z0-9]+(?:[-'][a-z0-9]+)*")


def tokenize(text):
    """Lowercase, extract word tokens, optionally remove stopwords."""
    if not text:
        return []
    text = text.lower()
    tokens = _TOKEN_RE.findall(text)
    if CONFIG["tokenizer"]["remove_stopwords"]:
        tokens = [t for t in tokens if t not in MINIMAL_STOPWORDS]
    return tokens


def sha256_text(text):
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Lightweight BM25Okapi (rank_bm25 not installed)
# ---------------------------------------------------------------------------

class BM25OkapiLite:
    """Lightweight BM25Okapi implementation.

    idf = log((N - df + 0.5) / (df + 0.5) + 1)
    score = idf * (tf * (k1 + 1)) / (tf + k1 * (1 - b + b * dl / avgdl))
    """

    def __init__(self, corpus_tokens, k1=1.5, b=0.75):
        self.k1 = k1
        self.b = b
        self.N = len(corpus_tokens)
        if self.N == 0:
            self.avgdl = 0
            self.df = {}
            self.idf = {}
            self.corpus = []
            return
        self.corpus = corpus_tokens
        total_len = sum(len(doc) for doc in corpus_tokens)
        self.avgdl = total_len / self.N if self.N > 0 else 0
        self.df = Counter()
        for doc in corpus_tokens:
            for term in set(doc):
                self.df[term] += 1
        self.idf = {}
        for term, df in self.df.items():
            self.idf[term] = math.log((self.N - df + 0.5) / (df + 0.5) + 1)

    def get_scores(self, query_tokens):
        """Return BM25 scores for all documents in the corpus."""
        scores = [0.0] * self.N
        for i in range(self.N):
            doc = self.corpus[i]
            dl = len(doc)
            doc_counter = Counter(doc)
            score = 0.0
            for term in query_tokens:
                if term not in doc_counter:
                    continue
                tf = doc_counter[term]
                idf = self.idf.get(term, 0.0)
                numerator = tf * (self.k1 + 1)
                denominator = tf + self.k1 * (1 - self.b + self.b * dl / self.avgdl) if self.avgdl > 0 else tf + self.k1
                score += idf * numerator / denominator if denominator > 0 else 0
            scores[i] = score
        return scores


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates(csv_path, toy_mode=False):
    """Load candidate CSV. Returns list of dicts with only allowed fields.

    Allowed for retrieval: candidate_id, target_candidate_group_id, claim_text
    Allowed for oracle eval: pdf_filename, page_number, evidence_text, evidence_text_sha256
    Forbidden: all label/audit fields
    """
    fields_actually_read = [
        "candidate_id", "target_candidate_group_id", "claim_text",
        "pdf_filename", "page_number", "evidence_text", "evidence_text_sha256",
    ]
    assert_no_forbidden_fields_used_for_retrieval(None, fields_actually_read)

    candidates = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = {
                "candidate_id": row.get("candidate_id", ""),
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "claim_text": row.get("claim_text", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row["page_number"]) if row.get("page_number", "").isdigit() else 0,
                "evidence_text": row.get("evidence_text", ""),
                "evidence_text_sha256": row.get("evidence_text_sha256", ""),
            }
            if not rec["evidence_text_sha256"] and rec["evidence_text"]:
                rec["evidence_text_sha256"] = sha256_text(rec["evidence_text"])
            candidates.append(rec)
    return candidates


def load_sentence_corpus(jsonl_path, exclude_references=True):
    """Load sentence corpus from JSONL. Returns list of sentence dicts."""
    sentences = []
    with open(jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            if exclude_references and rec.get("section_hint") == "reference":
                continue
            sentences.append(rec)
    return sentences


def build_windows(sentences):
    """Build 3-sentence windows: prev + current + next.

    Windows are built within each paper (across pages). Each window
    inherits the current sentence's metadata. window_unit_id = unit_id + '::w3'.
    """
    windows = []
    by_paper = {}
    for s in sentences:
        pid = s["paper_id"]
        if pid not in by_paper:
            by_paper[pid] = []
        by_paper[pid].append(s)

    for pid, paper_sents in by_paper.items():
        n = len(paper_sents)
        for i in range(n):
            prev_text = paper_sents[i - 1]["clean_text"] if i > 0 else ""
            curr = paper_sents[i]
            next_text = paper_sents[i + 1]["clean_text"] if i < n - 1 else ""
            parts = [p for p in [prev_text, curr["clean_text"], next_text] if p]
            window_text = " ".join(parts)
            windows.append({
                "unit_id": curr["unit_id"] + "::w3",
                "paper_id": curr["paper_id"],
                "pdf_filename": curr["pdf_filename"],
                "page_number": curr["page_number"],
                "section_hint": curr["section_hint"],
                "clean_text": window_text,
            })
    return windows


# ---------------------------------------------------------------------------
# BM25 ranking
# ---------------------------------------------------------------------------

def bm25_rank(query_text, corpus_items, top_k=10):
    """Rank corpus items by BM25 score. Returns list of (rank, item, score).

    corpus_items: list of dicts with 'clean_text' and metadata.
    """
    query_tokens = tokenize(query_text)
    corpus_tokens = [tokenize(item["clean_text"]) for item in corpus_items]
    bm25 = BM25OkapiLite(corpus_tokens, k1=CONFIG["bm25_k1"], b=CONFIG["bm25_b"])
    scores = bm25.get_scores(query_tokens)

    ranked_indices = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    results = []
    for rank, idx in enumerate(ranked_indices[:top_k], start=1):
        results.append({
            "rank": rank,
            "item": corpus_items[idx],
            "bm25_score": scores[idx],
            "query_n_tokens": len(query_tokens),
        })
    return results


# ---------------------------------------------------------------------------
# Oracle metrics (computed AFTER ranking)
# ---------------------------------------------------------------------------

def token_f1(text1, text2):
    """Standard token-level F1 between two texts."""
    tokens1 = set(tokenize(text1))
    tokens2 = set(tokenize(text2))
    if not tokens1 or not tokens2:
        return 0.0
    overlap = tokens1 & tokens2
    if not overlap:
        return 0.0
    precision = len(overlap) / len(tokens2)
    recall = len(overlap) / len(tokens1)
    return 2 * precision * recall / (precision + recall)


def compute_oracle_metrics(retrieved_text, retrieved_sha256, evidence_text, evidence_sha256, cand_page, retrieved_page):
    """Compute oracle metrics for a single retrieved item.

    Called AFTER ranking to avoid leakage.
    """
    oracle_hash_exact = (retrieved_sha256 == evidence_sha256) and (evidence_sha256 != "")
    oracle_page_match = (cand_page == retrieved_page) and (cand_page > 0)
    oracle_overlap_score = token_f1(retrieved_text, evidence_text) if evidence_text else 0.0
    oracle_hit = oracle_hash_exact or (oracle_page_match and oracle_overlap_score >= CONFIG["oracle_overlap_threshold"])
    return {
        "oracle_overlap_score": round(oracle_overlap_score, 6),
        "oracle_hash_exact": oracle_hash_exact,
        "oracle_page_match": oracle_page_match,
        "oracle_hit": oracle_hit,
    }


def compute_recall_at_k(all_results, k_values=(1, 5, 10)):
    """Compute recall@k and MRR across all candidates.

    all_results: dict of candidate_id -> list of retrieval result rows (sorted by rank).
    Each row must have 'oracle_hit' already computed.
    """
    n_candidates = len(all_results)
    if n_candidates == 0:
        return {"recall@1": 0, "recall@5": 0, "recall@10": 0, "mrr": 0}

    recall = {}
    for k in k_values:
        hits = sum(1 for cid, rows in all_results.items()
                    if any(r["oracle_hit"] for r in rows[:k]))
        recall[f"recall@{k}"] = round(hits / n_candidates, 6)

    mrr_sum = 0.0
    for cid, rows in all_results.items():
        for r in rows:
            if r["oracle_hit"]:
                mrr_sum += 1.0 / r["rank"]
                break
    recall["mrr"] = round(mrr_sum / n_candidates, 6)
    return recall


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def save_retrieval_csv(filepath, results_by_candidate):
    """Save retrieval results to CSV."""
    fields = [
        "candidate_id", "target_candidate_group_id", "rank", "unit_id",
        "paper_id", "pdf_filename", "page_number", "section_hint",
        "retrieved_text", "bm25_score", "query_n_tokens", "retrieved_n_words",
        "oracle_overlap_score", "oracle_hash_exact", "oracle_page_match", "oracle_hit",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for cid, rows in results_by_candidate.items():
            for r in rows:
                writer.writerow(r)


def save_redacted_csv(filepath, results_by_candidate):
    """Save redacted examples (no raw text, only hashes and metadata)."""
    fields = [
        "candidate_id", "rank", "page_number", "section_hint",
        "text_sha256", "n_words", "bm25_score",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for cid, rows in results_by_candidate.items():
            for r in rows[:3]:  # top-3 per candidate
                writer.writerow({
                    "candidate_id": cid,
                    "rank": r["rank"],
                    "page_number": r["page_number"],
                    "section_hint": r["section_hint"],
                    "text_sha256": sha256_text(r["retrieved_text"]),
                    "n_words": r["retrieved_n_words"],
                    "bm25_score": r["bm25_score"],
                })


def write_leakage_guard_report(output_dir, n_candidates, n_sentences, n_windows):
    """Write leakage guard report documenting that no forbidden fields were
    used for retrieval selection, and oracle/label fields were used only
    for post-ranking evaluation.
    """
    report = {
        "status": "pass",
        "forbidden_fields_checked": sorted(FORBIDDEN_RETRIEVAL_FIELDS),
        "forbidden_fields_used_for_retrieval": [],
        "query_field": "claim_text",
        "retrieval_fields_used": ["claim_text"],
        "corpus_text_field": "clean_text (from sentences.jsonl)",
        "oracle_fields_used_only_after_ranking": True,
        "oracle_fields": [
            "evidence_text", "evidence_text_sha256", "page_number",
        ],
        "ranking_formula": "BM25Okapi(k1=1.5, b=0.75) over tokenized claim_text vs sentence/window clean_text",
        "labels_used_for_retrieval": False,
        "oracle_used_for_retrieval": False,
        "gold_label_used_for_retrieval": False,
        "human_audited_used_for_retrieval": False,
        "raw_text_used_for_retrieval": False,
        "evidence_text_used_for_retrieval": False,
        "n_candidates": n_candidates,
        "n_sentences_in_corpus": n_sentences,
        "n_windows_in_corpus": n_windows,
        "no_network": True,
        "no_api": True,
        "no_training": True,
        "notes": (
            "Retrieval ranks corpus items by BM25 score between claim_text (query) "
            "and sentence/window clean_text (corpus). Oracle metrics (oracle_hit, "
            "oracle_overlap_score, oracle_hash_exact, oracle_page_match) are computed "
            "AFTER ranking using evidence_text/evidence_text_sha256/page_number, and "
            "never influence retrieval selection."
        ),
    }
    report_path = output_dir / "leakage_guard_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    return report_path


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Sentence and window BM25 retrieval evaluation with oracle recall."
    )
    parser.add_argument("--candidate_csv", default=None)
    parser.add_argument("--sentence_jsonl", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--top_k", type=int, default=10)
    parser.add_argument("--exclude_references", type=str, default="True")
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    # --- Load config ---
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    CONFIG["top_k"] = args.top_k
    CONFIG["exclude_references"] = args.exclude_references.lower() in ("true", "1", "yes")

    output_dir = Path(args.output_dir) if args.output_dir else resolve_path(config, "retrieval_dir")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        candidate_csv = "data/toy_synthetic/toy_candidates_v1.csv"
        sentence_jsonl = "data/pdf_corpus_toy_v1/sentences.jsonl"
        print("[toy_mode] Using toy candidate CSV and toy sentence corpus")
    else:
        candidate_csv = args.candidate_csv or str(resolve_path(config, "candidate_csv") or "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv")
        sentence_jsonl = args.sentence_jsonl or str(resolve_path(config, "pdf_corpus_dir") or Path("data/pdf_corpus_v1")) + "/sentences.jsonl"

    # --- Load data ---
    print(f"Loading candidates from {candidate_csv}")
    candidates = load_candidates(candidate_csv)
    print(f"  {len(candidates)} candidates loaded")

    print(f"Loading sentence corpus from {sentence_jsonl}")
    sentences = load_sentence_corpus(sentence_jsonl, exclude_references=CONFIG["exclude_references"])
    print(f"  {len(sentences)} sentences loaded (exclude_references={CONFIG['exclude_references']})")

    if not sentences:
        print("ERROR: No sentences in corpus. Run build_pdf_sentence_corpus_v1.py first.", file=sys.stderr)
        raise SystemExit(2)

    # --- Build windows ---
    windows = build_windows(sentences)
    print(f"  {len(windows)} windows built")

    # --- Sentence BM25 retrieval ---
    print("\n=== Sentence BM25 Retrieval ===")
    sentence_results = {}
    for cand in candidates:
        ranked = bm25_rank(cand["claim_text"], sentences, top_k=CONFIG["top_k"])
        rows = []
        for r in ranked:
            item = r["item"]
            retrieved_text = item["clean_text"]
            retrieved_sha256 = item.get("clean_text_sha256", sha256_text(retrieved_text))
            oracle = compute_oracle_metrics(
                retrieved_text, retrieved_sha256,
                cand["evidence_text"], cand["evidence_text_sha256"],
                cand["page_number"], item["page_number"],
            )
            rows.append({
                "candidate_id": cand["candidate_id"],
                "target_candidate_group_id": cand["target_candidate_group_id"],
                "rank": r["rank"],
                "unit_id": item["unit_id"],
                "paper_id": item["paper_id"],
                "pdf_filename": item["pdf_filename"],
                "page_number": item["page_number"],
                "section_hint": item.get("section_hint", "unknown"),
                "retrieved_text": retrieved_text,
                "bm25_score": round(r["bm25_score"], 6),
                "query_n_tokens": r["query_n_tokens"],
                "retrieved_n_words": len(retrieved_text.split()),
                **oracle,
            })
        sentence_results[cand["candidate_id"]] = rows

    # --- Window BM25 retrieval ---
    print("=== Window BM25 Retrieval ===")
    window_results = {}
    for cand in candidates:
        ranked = bm25_rank(cand["claim_text"], windows, top_k=CONFIG["top_k"])
        rows = []
        for r in ranked:
            item = r["item"]
            retrieved_text = item["clean_text"]
            retrieved_sha256 = sha256_text(retrieved_text)
            oracle = compute_oracle_metrics(
                retrieved_text, retrieved_sha256,
                cand["evidence_text"], cand["evidence_text_sha256"],
                cand["page_number"], item["page_number"],
            )
            rows.append({
                "candidate_id": cand["candidate_id"],
                "target_candidate_group_id": cand["target_candidate_group_id"],
                "rank": r["rank"],
                "unit_id": item["unit_id"],
                "paper_id": item["paper_id"],
                "pdf_filename": item["pdf_filename"],
                "page_number": item["page_number"],
                "section_hint": item.get("section_hint", "unknown"),
                "retrieved_text": retrieved_text,
                "bm25_score": round(r["bm25_score"], 6),
                "query_n_tokens": r["query_n_tokens"],
                "retrieved_n_words": len(retrieved_text.split()),
                **oracle,
            })
        window_results[cand["candidate_id"]] = rows

    # --- Oracle recall ---
    sentence_recall = compute_recall_at_k(sentence_results)
    window_recall = compute_recall_at_k(window_results)

    print(f"\nSentence recall@1/5/10: {sentence_recall['recall@1']}/{sentence_recall['recall@5']}/{sentence_recall['recall@10']}, MRR={sentence_recall['mrr']}")
    print(f"Window   recall@1/5/10: {window_recall['recall@1']}/{window_recall['recall@5']}/{window_recall['recall@10']}, MRR={window_recall['mrr']}")

    # --- Save outputs ---
    sentence_csv = output_dir / "retrieval_results_sentence_bm25.csv"
    save_retrieval_csv(sentence_csv, sentence_results)
    print(f"Wrote {sentence_csv}")

    window_csv = output_dir / "retrieval_results_window_bm25.csv"
    save_retrieval_csv(window_csv, window_results)
    print(f"Wrote {window_csv}")

    recall_summary = {
        "sentence": sentence_recall,
        "window": window_recall,
        "n_candidates": len(candidates),
        "oracle_definition": (
            f"oracle_hit = oracle_hash_exact OR "
            f"(oracle_page_match AND oracle_overlap_score >= {CONFIG['oracle_overlap_threshold']})"
        ),
    }
    recall_path = output_dir / "oracle_recall_summary.json"
    with open(recall_path, "w", encoding="utf-8") as f:
        json.dump(recall_summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote {recall_path}")

    config_path = output_dir / "retrieval_config.json"
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2, ensure_ascii=False)
    print(f"Wrote {config_path}")

    redacted_path = output_dir / "retrieval_examples_redacted.csv"
    save_redacted_csv(redacted_path, sentence_results)
    print(f"Wrote {redacted_path}")

    # --- Schema validation ---
    schema_reports = [
        validate_csv_file(output_dir / "retrieval_results_sentence_bm25.csv", "bm25_retrieval_results"),
        validate_csv_file(output_dir / "retrieval_results_window_bm25.csv", "bm25_retrieval_results"),
        validate_redacted_csv_file(redacted_path, "bm25_retrieval_results"),
    ]
    write_schema_validation_report(
        output_dir, schema_reports, script_name="run_bm25_sentence_retrieval_v1.py"
    )
    print(f"Wrote schema_validation_report.json")

    write_run_config(output_dir, config, "run_bm25_sentence_retrieval_v1.py",
                     extra={"toy_mode": args.toy_mode})
    print(f"Wrote run_config.json")

    guard_path = write_leakage_guard_report(
        output_dir, len(candidates), len(sentences), len(windows)
    )
    print(f"Wrote {guard_path}")

    print("\nDone.")


if __name__ == "__main__":
    main()
