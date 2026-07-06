#!/usr/bin/env python
"""run_pdf_extraction_to_bm25_stress_v1.py — BM25 retrieval under extraction stress.

Reads the stress sentences/windows produced by run_pdf_extraction_stress_test_v1.py
and the stress sources (which contain anchor texts derived from clean portions of
each stress page). For each stress_doc_id, evaluates anchor retrieval against the
extracted sentences/windows using a pure-Python BM25 implementation.

anchor_text is used ONLY for evaluation — never for ranking. Public/redacted outputs
retain only anchor_text_sha256, never the anchor text itself.

Outputs:
  - retrieval_under_extraction_stress.csv (per-query results)
  - retrieval_stress_summary.json (aggregate + by_stress_type metrics)

Hard boundaries:
  - no network, no API, no cloud, no OCR, no training
  - anchor_text only for evaluation, not for ranking
  - redacted outputs keep only anchor_text_sha256
  - no label leakage: ranking is purely lexical BM25 over extracted sentences

Usage:
  python scripts/run_pdf_extraction_to_bm25_stress_v1.py \
      --stress_dir experiments/pdf_extraction_stress_test_v1
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def write_run_config(output_dir: Path, config: dict, script_name: str, extra: dict | None = None):
    rc = {
        "script": script_name,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "config": config,
        "no_api": True,
        "no_network": True,
        "no_training": True,
        "no_ocr_by_default": True,
    }
    if extra:
        rc.update(extra)
    path = output_dir / "run_config.json"
    with open(path, "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=2, ensure_ascii=False)
    return path


def sha256_text(text: str) -> str:
    if text is None:
        text = ""
    import hashlib
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")


def tokenize(text: str) -> list[str]:
    return [t.lower() for t in _TOKEN_RE.findall(text or "")]


# ---------------------------------------------------------------------------
# Pure-Python BM25
# ---------------------------------------------------------------------------

class BM25:
    """Pure-Python BM25 implementation (Okapi BM25)."""

    def __init__(self, docs: list[list[str]], k1: float = 1.5, b: float = 0.75):
        self.k1 = k1
        self.b = b
        self.docs = docs
        self.n_docs = len(docs)
        self.doc_len = [len(d) for d in docs]
        self.avgdl = (sum(self.doc_len) / self.n_docs) if self.n_docs > 0 else 0.0
        self.df = defaultdict(int)
        self.tf = []
        for d in docs:
            tf = defaultdict(int)
            seen = set()
            for term in d:
                tf[term] += 1
                if term not in seen:
                    self.df[term] += 1
                    seen.add(term)
            self.tf.append(tf)
        # IDF: ln(1 + (N - df + 0.5) / (df + 0.5))
        self.idf = {}
        for term, df in self.df.items():
            self.idf[term] = math.log(1 + (self.n_docs - df + 0.5) / (df + 0.5))

    def score(self, query_terms: list[str], doc_idx: int) -> float:
        if doc_idx >= self.n_docs:
            return 0.0
        tf = self.tf[doc_idx]
        dl = self.doc_len[doc_idx] or 1
        score = 0.0
        for term in query_terms:
            if term not in self.idf:
                continue
            f = tf.get(term, 0)
            if f == 0:
                continue
            idf = self.idf[term]
            denom = f + self.k1 * (1 - self.b + self.b * dl / (self.avgdl or 1))
            score += idf * (f * (self.k1 + 1)) / denom
        return score

    def rank(self, query_terms: list[str], top_k: int = 10) -> list[tuple[int, float]]:
        scores = [(i, self.score(query_terms, i)) for i in range(self.n_docs)]
        scores.sort(key=lambda x: -x[1])
        return scores[:top_k]


# ---------------------------------------------------------------------------
# Anchor text construction (from stress sources)
# ---------------------------------------------------------------------------

def build_anchors_from_sources(sources_path: Path) -> list[dict]:
    """Build one anchor query per stress_doc_id from the clean (synthetic) source text.

    Each anchor is the first substantive sentence (>= 8 words) from the source
    page_text after light cleaning. This is a synthetic anchor for evaluation
    purposes — it is NOT used for ranking, only for measuring retrieval recall.
    """
    anchors = []
    with open(sources_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            stress_doc_id = rec["stress_doc_id"]
            stress_type = rec["stress_type"]
            paper_id = rec["paper_id"]
            page_text = rec.get("page_text", "")

            # Light cleaning to derive a candidate anchor sentence
            # Remove NUL bytes if corrupted
            page_text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", page_text)
            # Split into sentences (very simple)
            sentences = re.split(r"(?<=[.!?])\s+", page_text)
            anchor_text = ""
            for s in sentences:
                s = s.strip()
                if len(s.split()) >= 8:
                    anchor_text = s
                    break
            # For empty / scanned docs, anchor is empty
            if not page_text.strip() or stress_type in ("empty_page", "scanned_placeholder_detect_only"):
                anchor_text = ""

            anchors.append({
                "stress_doc_id": stress_doc_id,
                "stress_type": stress_type,
                "paper_id": paper_id,
                "anchor_text": anchor_text,
                "anchor_text_sha256": sha256_text(anchor_text),
                "anchor_n_words": len(anchor_text.split()) if anchor_text else 0,
            })
    return anchors


# ---------------------------------------------------------------------------
# Retrieval evaluation
# ---------------------------------------------------------------------------

def evaluate_retrieval(
    anchors: list[dict],
    sentence_rows: list[dict],
    window_rows: list[dict],
) -> tuple[list[dict], dict]:
    """For each anchor, retrieve top-k sentences and windows from the SAME
    stress_doc_id. Ground truth: a sentence is a hit if its clean_text overlaps
    significantly with the anchor_text (token Jaccard >= 0.5).

    Returns (per_query_results, summary_dict).
    """
    # Group sentences/windows by stress_doc_id
    sents_by_doc = defaultdict(list)
    for s in sentence_rows:
        sents_by_doc[s["stress_doc_id"]].append(s)
    windows_by_doc = defaultdict(list)
    for w in window_rows:
        windows_by_doc[w["stress_doc_id"]].append(w)

    per_query = []
    # Aggregate metrics
    n_queries = 0
    n_with_hits_sentence = 0
    n_with_hits_window = 0
    sum_recall1_s = 0.0
    sum_recall5_s = 0.0
    sum_recall10_s = 0.0
    sum_mrr_s = 0.0
    sum_recall1_w = 0.0
    sum_recall5_w = 0.0
    sum_recall10_w = 0.0
    sum_mrr_w = 0.0
    by_stress_type = defaultdict(lambda: {
        "n": 0,
        "sentence_recall1": 0.0, "sentence_recall5": 0.0, "sentence_recall10": 0.0, "sentence_mrr": 0.0,
        "window_recall1": 0.0, "window_recall5": 0.0, "window_recall10": 0.0, "window_mrr": 0.0,
    })

    for anchor in anchors:
        doc_id = anchor["stress_doc_id"]
        stress_type = anchor["stress_type"]
        anchor_text = anchor["anchor_text"]
        anchor_terms = tokenize(anchor_text)

        # Skip empty anchors (empty_page, scanned)
        if not anchor_terms:
            per_query.append({
                "stress_doc_id": doc_id,
                "stress_type": stress_type,
                "anchor_text_sha256": anchor["anchor_text_sha256"],
                "anchor_n_words": 0,
                "sentence_recall1": 0.0, "sentence_recall5": 0.0, "sentence_recall10": 0.0, "sentence_mrr": 0.0,
                "window_recall1": 0.0, "window_recall5": 0.0, "window_recall10": 0.0, "window_mrr": 0.0,
                "n_sentence_candidates": len(sents_by_doc.get(doc_id, [])),
                "n_window_candidates": len(windows_by_doc.get(doc_id, [])),
                "n_relevant_sentences": 0,
                "skipped_reason": "empty_anchor",
            })
            continue

        # --- Sentence retrieval ---
        sents = sents_by_doc.get(doc_id, [])
        sent_docs = [tokenize(s.get("clean_text", "")) for s in sents]
        if sent_docs:
            bm25_s = BM25(sent_docs)
            ranked_s = bm25_s.rank(anchor_terms, top_k=10)
            # Determine relevant set: sentences with token Jaccard >= 0.5 vs anchor
            anchor_set = set(anchor_terms)
            relevant_s = set()
            for idx, s in enumerate(sents):
                s_terms = set(tokenize(s.get("clean_text", "")))
                if not s_terms:
                    continue
                jaccard = len(anchor_set & s_terms) / len(anchor_set | s_terms)
                if jaccard >= 0.5:
                    relevant_s.add(idx)
            # Compute Recall@1/5/10 and MRR
            r1_s = 1.0 if (ranked_s and ranked_s[0][0] in relevant_s) else 0.0
            r5_s = 1.0 if any(idx in relevant_s for idx, _ in ranked_s[:5]) else 0.0
            r10_s = 1.0 if any(idx in relevant_s for idx, _ in ranked_s[:10]) else 0.0
            mrr_s = 0.0
            for rank, (idx, _) in enumerate(ranked_s, start=1):
                if idx in relevant_s:
                    mrr_s = 1.0 / rank
                    break
            n_relevant_s = len(relevant_s)
        else:
            r1_s = r5_s = r10_s = mrr_s = 0.0
            n_relevant_s = 0

        # --- Window retrieval ---
        windows = windows_by_doc.get(doc_id, [])
        win_docs = [tokenize(w.get("clean_text", "")) for w in windows]
        if win_docs:
            bm25_w = BM25(win_docs)
            ranked_w = bm25_w.rank(anchor_terms, top_k=10)
            anchor_set = set(anchor_terms)
            relevant_w = set()
            for idx, w in enumerate(windows):
                w_terms = set(tokenize(w.get("clean_text", "")))
                if not w_terms:
                    continue
                jaccard = len(anchor_set & w_terms) / len(anchor_set | w_terms)
                if jaccard >= 0.5:
                    relevant_w.add(idx)
            r1_w = 1.0 if (ranked_w and ranked_w[0][0] in relevant_w) else 0.0
            r5_w = 1.0 if any(idx in relevant_w for idx, _ in ranked_w[:5]) else 0.0
            r10_w = 1.0 if any(idx in relevant_w for idx, _ in ranked_w[:10]) else 0.0
            mrr_w = 0.0
            for rank, (idx, _) in enumerate(ranked_w, start=1):
                if idx in relevant_w:
                    mrr_w = 1.0 / rank
                    break
        else:
            r1_w = r5_w = r10_w = mrr_w = 0.0

        per_query.append({
            "stress_doc_id": doc_id,
            "stress_type": stress_type,
            "anchor_text_sha256": anchor["anchor_text_sha256"],
            "anchor_n_words": anchor["anchor_n_words"],
            "sentence_recall1": round(r1_s, 4),
            "sentence_recall5": round(r5_s, 4),
            "sentence_recall10": round(r10_s, 4),
            "sentence_mrr": round(mrr_s, 4),
            "window_recall1": round(r1_w, 4),
            "window_recall5": round(r5_w, 4),
            "window_recall10": round(r10_w, 4),
            "window_mrr": round(mrr_w, 4),
            "n_sentence_candidates": len(sents),
            "n_window_candidates": len(windows),
            "n_relevant_sentences": n_relevant_s,
            "skipped_reason": "",
        })

        n_queries += 1
        sum_recall1_s += r1_s
        sum_recall5_s += r5_s
        sum_recall10_s += r10_s
        sum_mrr_s += mrr_s
        sum_recall1_w += r1_w
        sum_recall5_w += r5_w
        sum_recall10_w += r10_w
        sum_mrr_w += mrr_w
        if r1_s > 0 or r5_s > 0 or r10_s > 0:
            n_with_hits_sentence += 1
        if r1_w > 0 or r5_w > 0 or r10_w > 0:
            n_with_hits_window += 1

        by_stress_type[stress_type]["n"] += 1
        by_stress_type[stress_type]["sentence_recall1"] += r1_s
        by_stress_type[stress_type]["sentence_recall5"] += r5_s
        by_stress_type[stress_type]["sentence_recall10"] += r10_s
        by_stress_type[stress_type]["sentence_mrr"] += mrr_s
        by_stress_type[stress_type]["window_recall1"] += r1_w
        by_stress_type[stress_type]["window_recall5"] += r5_w
        by_stress_type[stress_type]["window_recall10"] += r10_w
        by_stress_type[stress_type]["window_mrr"] += mrr_w

    # Average by stress_type
    by_stress_type_avg = {}
    for st, vals in by_stress_type.items():
        n = vals["n"] or 1
        by_stress_type_avg[st] = {
            "n": vals["n"],
            "sentence_recall1": round(vals["sentence_recall1"] / n, 4),
            "sentence_recall5": round(vals["sentence_recall5"] / n, 4),
            "sentence_recall10": round(vals["sentence_recall10"] / n, 4),
            "sentence_mrr": round(vals["sentence_mrr"] / n, 4),
            "window_recall1": round(vals["window_recall1"] / n, 4),
            "window_recall5": round(vals["window_recall5"] / n, 4),
            "window_recall10": round(vals["window_recall10"] / n, 4),
            "window_mrr": round(vals["window_mrr"] / n, 4),
        }

    n_avg = n_queries or 1
    summary = {
        "n_queries": n_queries,
        "n_with_hits_sentence": n_with_hits_sentence,
        "n_with_hits_window": n_with_hits_window,
        "sentence_recall1": round(sum_recall1_s / n_avg, 4),
        "sentence_recall5": round(sum_recall5_s / n_avg, 4),
        "sentence_recall10": round(sum_recall10_s / n_avg, 4),
        "sentence_mrr": round(sum_mrr_s / n_avg, 4),
        "window_recall1": round(sum_recall1_w / n_avg, 4),
        "window_recall5": round(sum_recall5_w / n_avg, 4),
        "window_recall10": round(sum_recall10_w / n_avg, 4),
        "window_mrr": round(sum_mrr_w / n_avg, 4),
        "by_stress_type": by_stress_type_avg,
        "note": "Anchor text used for evaluation only, not for ranking. Ranking is pure BM25 over extracted sentences/windows.",
    }
    return per_query, summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="BM25 retrieval under PDF extraction stress."
    )
    parser.add_argument(
        "--stress_dir",
        default="experiments/pdf_extraction_stress_test_v1",
        help="Directory containing stress extraction outputs",
    )
    parser.add_argument(
        "--sources",
        default="data/toy_synthetic/pdf_stress_sources.jsonl",
        help="JSONL file with synthetic stress page texts (used to build anchors)",
    )
    args = parser.parse_args()

    stress_dir = Path(args.stress_dir)
    sources_path = Path(args.sources)
    if not sources_path.is_file():
        print(f"ERROR: sources file not found at {sources_path}", file=sys.stderr)
        raise SystemExit(2)

    # Load sentence / window rows from private full-text versions (we need clean_text)
    # Fall back to redacted if private not present (then no text available — will produce zeros)
    sentences_path = stress_dir / "private" / "sentences_full.jsonl"
    windows_path = stress_dir / "private" / "windows_full.jsonl"
    if not sentences_path.is_file():
        print(f"WARNING: {sentences_path} not found; retrieval will produce zero scores", file=sys.stderr)
        sentence_rows = []
    else:
        with open(sentences_path, "r", encoding="utf-8") as f:
            sentence_rows = [json.loads(l) for l in f if l.strip()]
    if not windows_path.is_file():
        print(f"WARNING: {windows_path} not found; retrieval will produce zero scores", file=sys.stderr)
        window_rows = []
    else:
        with open(windows_path, "r", encoding="utf-8") as f:
            window_rows = [json.loads(l) for l in f if l.strip()]

    print(f"Loaded {len(sentence_rows)} sentence rows, {len(window_rows)} window rows")

    # Build anchors
    anchors = build_anchors_from_sources(sources_path)
    print(f"Built {len(anchors)} anchors")
    n_nonempty = sum(1 for a in anchors if a["anchor_n_words"] > 0)
    print(f"  Non-empty anchors: {n_nonempty}")

    # Evaluate
    per_query, summary = evaluate_retrieval(anchors, sentence_rows, window_rows)

    # Write retrieval_under_extraction_stress.csv (redacted: anchor_text_sha256 only, no anchor_text)
    out_csv = stress_dir / "retrieval_under_extraction_stress.csv"
    fields = [
        "stress_doc_id", "stress_type", "anchor_text_sha256", "anchor_n_words",
        "sentence_recall1", "sentence_recall5", "sentence_recall10", "sentence_mrr",
        "window_recall1", "window_recall5", "window_recall10", "window_mrr",
        "n_sentence_candidates", "n_window_candidates", "n_relevant_sentences",
        "skipped_reason",
    ]
    with open(out_csv, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in per_query:
            writer.writerow(row)
    print(f"Wrote {out_csv} ({len(per_query)} rows)")

    # Write retrieval_stress_summary.json
    summary_path = stress_dir / "retrieval_stress_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote {summary_path}")

    # Update run_config.json (append)
    rc_path = stress_dir / "run_config.json"
    if rc_path.is_file():
        with open(rc_path, "r", encoding="utf-8") as f:
            rc = json.load(f)
    else:
        rc = {}
    rc["bm25_stress"] = {
        "script": "run_pdf_extraction_to_bm25_stress_v1.py",
        "sources": str(sources_path),
        "n_anchors": len(anchors),
        "n_nonempty_anchors": n_nonempty,
        "n_sentence_candidates_total": len(sentence_rows),
        "n_window_candidates_total": len(window_rows),
        "sentence_recall1": summary["sentence_recall1"],
        "sentence_recall5": summary["sentence_recall5"],
        "sentence_recall10": summary["sentence_recall10"],
        "sentence_mrr": summary["sentence_mrr"],
        "window_recall1": summary["window_recall1"],
        "window_recall5": summary["window_recall5"],
        "window_recall10": summary["window_recall10"],
        "window_mrr": summary["window_mrr"],
    }
    with open(rc_path, "w", encoding="utf-8") as f:
        json.dump(rc, f, indent=2, ensure_ascii=False)
    print(f"Updated {rc_path}")

    print("\n=== Aggregate Retrieval Metrics ===")
    print(f"  Sentence  Recall@1={summary['sentence_recall1']:.3f}  Recall@5={summary['sentence_recall5']:.3f}  Recall@10={summary['sentence_recall10']:.3f}  MRR={summary['sentence_mrr']:.3f}")
    print(f"  Window    Recall@1={summary['window_recall1']:.3f}  Recall@5={summary['window_recall5']:.3f}  Recall@10={summary['window_recall10']:.3f}  MRR={summary['window_mrr']:.3f}")
    print(f"\nDone: {len(per_query)} queries evaluated")


if __name__ == "__main__":
    main()
