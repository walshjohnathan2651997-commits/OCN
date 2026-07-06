#!/usr/bin/env python
"""run_pdf_extraction_stress_test_v1.py — Run PDF extraction pipeline against stress suite.

Reads synthetic stress page texts and runs them through the same cleaning pipeline
as build_pdf_sentence_corpus_v1.py (unicode normalization, dehyphenation, line
break repair, header/footer removal, page number removal, section hint detection,
sentence splitting, short-sentence filter, and window construction).

For each stress_doc_id, produces:
  - redacted pages/blocks/sentences/windows (hash-only public outputs)
  - extraction_quality_metrics.csv row with 19 fields
  - failure_cases_redacted.csv row if extraction_status != ok

Hard boundaries:
  - no network, no API, no cloud, no OCR, no training
  - private mode default: public outputs are hash-only
  - scanned PDFs are detected and reported but NOT OCR'd

Usage:
  python scripts/run_pdf_extraction_stress_test_v1.py \
      --output_dir experiments/pdf_extraction_stress_test_v1
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Import cleaning functions from the corpus builder
sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_pdf_sentence_corpus_v1 import (  # noqa: E402
    normalize_unicode,
    dehyphenate,
    repair_linebreaks,
    remove_repeated_headers_footers,
    detect_section_hint,
    split_sentences,
    split_blocks,
    count_words,
    sha256_text,
    build_windows,
)


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


def load_sources(sources_path: Path) -> list[dict]:
    records = []
    with open(sources_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            records.append(json.loads(line))
    return records


def detect_scanned(page_text: str) -> bool:
    """Heuristic: a page is 'scanned' if it has very few alphanumeric chars
    relative to whitespace, OR it contains the explicit synthetic marker."""
    if not page_text:
        return False
    if "scanned_placeholder_detect_only" in page_text or "[Note: this is a synthetic placeholder representing a scanned PDF page" in page_text:
        return True
    # Heuristic: very low alphanumeric ratio
    alnum = sum(1 for c in page_text if c.isalnum())
    total = len(page_text)
    if total == 0:
        return False
    ratio = alnum / total
    # Also require very few actual word boundaries
    n_words = len(page_text.split())
    if ratio < 0.10 and n_words < 10:
        return True
    return False


def detect_corrupted(page_text: str) -> bool:
    """Heuristic: page is corrupted if it contains NUL bytes."""
    if not page_text:
        return False
    return "\x00" in page_text


def clean_corrupted_text(text: str) -> str:
    """Remove NUL bytes and other binary control characters."""
    if not text:
        return ""
    # Remove NUL and other C0 control chars except \n, \r, \t
    return re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", "", text)


# Redaction field sets (must match build_pdf_sentence_corpus_v1.py)
TEXT_FIELDS_PAGES = {"raw_page_text", "clean_page_text"}
TEXT_FIELDS_BLOCKS = {"raw_block_text", "clean_block_text"}
TEXT_FIELDS_SENTS = {"raw_text", "clean_text"}
TEXT_FIELDS_WINDOWS = {"clean_text"}


def redact_row(row: dict, text_fields: set) -> dict:
    return {k: v for k, v in row.items() if k not in text_fields}


# ---------------------------------------------------------------------------
# Per-stress-doc extraction
# ---------------------------------------------------------------------------

def extract_one_stress_doc(rec: dict, window_size: int = 3) -> dict:
    """Run the cleaning pipeline on one stress_doc and return results + metrics.

    Returns:
        {
            "stress_doc_id": ...,
            "stress_type": ...,
            "extraction_status": "ok"|"empty"|"scanned_detect_only"|"corrupted_cleaned"|"failed",
            "page_rows": [...],
            "block_rows": [...],
            "sentence_rows": [...],
            "window_rows": [...],
            "metrics": {... 19 fields ...},
        }
    """
    stress_doc_id = rec["stress_doc_id"]
    stress_type = rec["stress_type"]
    paper_id = rec["paper_id"]
    pdf_filename = rec["pdf_filename"]
    page_number = rec["page_number"]
    page_text = rec.get("page_text", "")
    pdf_sha256 = sha256_text(pdf_filename + "::stress_toy")

    error_message = ""
    extraction_status = "ok"

    # Pre-extraction detection: scanned / corrupted / empty
    is_scanned = detect_scanned(page_text)
    is_corrupted = detect_corrupted(page_text)
    is_empty = (len(page_text.strip()) == 0)

    if is_scanned:
        extraction_status = "scanned_detect_only"
    elif is_empty and stress_type == "empty_page":
        extraction_status = "empty"

    # Clean corrupted text (NUL bytes) before pipeline — does not OCR
    working_text = page_text
    if is_corrupted:
        working_text = clean_corrupted_text(page_text)
        extraction_status = "corrupted_cleaned"

    raw_pages = [{"page_number": page_number, "raw_text": working_text}]

    try:
        # Step 1: normalize + dehyphenate + repair
        processed_texts = []
        for rp in raw_pages:
            t = normalize_unicode(rp["raw_text"])
            t = dehyphenate(t)
            t = repair_linebreaks(t)
            processed_texts.append(t)

        # Step 2: header/footer removal
        cleaned_texts = remove_repeated_headers_footers(processed_texts)

        page_rows = []
        block_rows = []
        sentence_rows = []
        global_sentence_id = 0

        for i, rp in enumerate(raw_pages):
            pn = rp["page_number"]
            raw_page_text = rp["raw_text"]
            clean_page_text = cleaned_texts[i]

            page_rows.append({
                "stress_doc_id": stress_doc_id,
                "stress_type": stress_type,
                "paper_id": paper_id,
                "pdf_filename": pdf_filename,
                "pdf_sha256": pdf_sha256,
                "page_number": pn,
                "raw_page_text": raw_page_text,
                "clean_page_text": clean_page_text,
                "raw_text_sha256": sha256_text(raw_page_text),
                "clean_text_sha256": sha256_text(clean_page_text),
                "n_chars": len(clean_page_text),
                "n_words": count_words(clean_page_text),
                "section_hint": detect_section_hint(clean_page_text[:500]),
            })

            # Blocks
            blocks = split_blocks(clean_page_text)
            current_hint = "unknown"
            for blk in blocks:
                block_id = blk["block_id"]
                raw_block = blk["raw_block_text"]
                clean_block = re.sub(r"[ \t]+", " ", raw_block).strip()
                block_hint = detect_section_hint(clean_block)
                n_words_block = count_words(clean_block)
                if block_hint != "unknown" and n_words_block < 10:
                    current_hint = block_hint
                section_hint = block_hint if block_hint != "unknown" else current_hint

                block_rows.append({
                    "stress_doc_id": stress_doc_id,
                    "stress_type": stress_type,
                    "paper_id": paper_id,
                    "pdf_filename": pdf_filename,
                    "pdf_sha256": pdf_sha256,
                    "page_number": pn,
                    "block_id": block_id,
                    "raw_block_text": raw_block,
                    "clean_block_text": clean_block,
                    "raw_text_sha256": sha256_text(raw_block),
                    "clean_text_sha256": sha256_text(clean_block),
                    "n_chars": len(clean_block),
                    "n_words": count_words(clean_block),
                    "section_hint": section_hint,
                })

                sents = split_sentences(clean_block)
                for sent in sents:
                    n_words = count_words(sent)
                    if n_words < 5:
                        continue
                    unit_id = f"{paper_id}::p{pn}::b{block_id}::s{global_sentence_id}"
                    sentence_rows.append({
                        "stress_doc_id": stress_doc_id,
                        "stress_type": stress_type,
                        "paper_id": paper_id,
                        "pdf_filename": pdf_filename,
                        "pdf_sha256": pdf_sha256,
                        "page_number": pn,
                        "block_id": block_id,
                        "sentence_id": global_sentence_id,
                        "unit_id": unit_id,
                        "raw_text": sent,
                        "clean_text": sent,
                        "raw_text_sha256": sha256_text(sent),
                        "clean_text_sha256": sha256_text(sent),
                        "n_chars": len(sent),
                        "n_words": n_words,
                        "section_hint": section_hint,
                    })
                    global_sentence_id += 1

        window_rows = build_windows(
            [{**s, "paper_id": s["paper_id"]} for s in sentence_rows],
            window_size=window_size,
        )
        # Add stress_doc_id / stress_type to window rows
        for w in window_rows:
            w["stress_doc_id"] = stress_doc_id
            w["stress_type"] = stress_type

    except Exception as e:
        extraction_status = "failed"
        error_message = str(e)
        page_rows = []
        block_rows = []
        sentence_rows = []
        window_rows = []

    # --- Compute metrics (19 fields) ---
    n_pages = len(page_rows)
    n_pages_empty = sum(1 for p in page_rows if p["n_words"] == 0)
    empty_page_rate = (n_pages_empty / n_pages) if n_pages > 0 else 1.0
    n_blocks = len(block_rows)
    n_sentences = len(sentence_rows)
    mean_sentences_per_page = (n_sentences / n_pages) if n_pages > 0 else 0.0

    # mean_words_per_sentence
    if n_sentences > 0:
        mean_words_per_sentence = sum(s["n_words"] for s in sentence_rows) / n_sentences
    else:
        mean_words_per_sentence = 0.0

    # short_sentence_rate (< 8 words) — note sentences < 5 words are filtered out
    if n_sentences > 0:
        n_short = sum(1 for s in sentence_rows if s["n_words"] < 8)
        short_sentence_rate = n_short / n_sentences
        n_long = sum(1 for s in sentence_rows if s["n_words"] > 60)
        long_sentence_rate = n_long / n_sentences
    else:
        short_sentence_rate = 0.0
        long_sentence_rate = 0.0

    # hyphenation_artifact_rate: fraction of sentences that still contain "word-\n"
    # after cleaning (residual hyphenation). Since dehyphenation runs, this should
    # be near zero; we measure residual.
    if n_sentences > 0:
        n_hyphen_resid = sum(
            1 for s in sentence_rows
            if re.search(r"\w-\n\w", s["clean_text"])
        )
        hyphenation_artifact_rate = n_hyphen_resid / n_sentences
    else:
        hyphenation_artifact_rate = 0.0

    # header_footer_residual_rate: heuristic — fraction of blocks that look like
    # pure header/footer lines (very short, often repeated). Approximated by
    # blocks with n_words < 5 that are not section headings.
    if n_blocks > 0:
        n_hf_like = sum(
            1 for b in block_rows
            if b["n_words"] < 5 and b["section_hint"] == "unknown"
        )
        header_footer_residual_rate = n_hf_like / n_blocks
    else:
        header_footer_residual_rate = 0.0

    # reference_section_ratio: fraction of blocks tagged 'reference'
    if n_blocks > 0:
        n_ref = sum(1 for b in block_rows if b["section_hint"] == "reference")
        reference_section_ratio = n_ref / n_blocks
    else:
        reference_section_ratio = 0.0

    # caption_marker_count: count of blocks matching "Figure N" or "Table N"
    caption_marker_count = sum(
        1 for b in block_rows
        if re.match(r"^\s*(figure|table)\s+\d", b["clean_block_text"], re.IGNORECASE)
    ) if n_blocks > 0 else 0

    # table_marker_count: count of blocks containing pipe-delimited rows
    # (3+ rows separated by | )
    table_marker_count = 0
    for b in block_rows:
        cb = b["clean_block_text"]
        n_pipe_rows = len(re.findall(r"^[^|\n]*\|[^|\n]*\|", cb, re.MULTILINE))
        if n_pipe_rows >= 3:
            table_marker_count += 1

    scanned_detected = is_scanned

    metrics = {
        "stress_doc_id": stress_doc_id,
        "stress_type": stress_type,
        "parser_name": "synthetic_text_pipeline_v1",
        "extraction_status": extraction_status,
        "n_pages": n_pages,
        "n_pages_empty": n_pages_empty,
        "empty_page_rate": round(empty_page_rate, 4),
        "n_blocks": n_blocks,
        "n_sentences": n_sentences,
        "mean_sentences_per_page": round(mean_sentences_per_page, 4),
        "mean_words_per_sentence": round(mean_words_per_sentence, 4),
        "short_sentence_rate": round(short_sentence_rate, 4),
        "long_sentence_rate": round(long_sentence_rate, 4),
        "hyphenation_artifact_rate": round(hyphenation_artifact_rate, 4),
        "header_footer_residual_rate": round(header_footer_residual_rate, 4),
        "reference_section_ratio": round(reference_section_ratio, 4),
        "caption_marker_count": caption_marker_count,
        "table_marker_count": table_marker_count,
        "scanned_detected": scanned_detected,
        "error_message": error_message,
    }

    return {
        "stress_doc_id": stress_doc_id,
        "stress_type": stress_type,
        "extraction_status": extraction_status,
        "page_rows": page_rows,
        "block_rows": block_rows,
        "sentence_rows": sentence_rows,
        "window_rows": window_rows,
        "metrics": metrics,
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Run PDF extraction pipeline against synthetic stress suite."
    )
    parser.add_argument(
        "--sources",
        default="data/toy_synthetic/pdf_stress_sources.jsonl",
        help="JSONL file with synthetic stress page texts",
    )
    parser.add_argument(
        "--output_dir",
        default="experiments/pdf_extraction_stress_test_v1",
        help="Output directory",
    )
    parser.add_argument(
        "--window_size",
        type=int,
        default=3,
        help="Number of consecutive sentences per window (default: 3)",
    )
    args = parser.parse_args()

    sources_path = Path(args.sources)
    if not sources_path.is_file():
        print(f"ERROR: sources file not found at {sources_path}", file=sys.stderr)
        raise SystemExit(2)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    private_dir = output_dir / "private"
    private_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading stress sources from {sources_path}")
    records = load_sources(sources_path)
    print(f"  Loaded {len(records)} records")

    all_page_rows = []
    all_block_rows = []
    all_sentence_rows = []
    all_window_rows = []
    metrics_rows = []
    failure_rows = []

    for rec in records:
        print(f"\nProcessing {rec['stress_doc_id']} ({rec['stress_type']})...")
        result = extract_one_stress_doc(rec, window_size=args.window_size)
        status = result["extraction_status"]
        m = result["metrics"]
        print(
            f"  status={status}, n_pages={m['n_pages']}, n_blocks={m['n_blocks']}, "
            f"n_sentences={m['n_sentences']}, n_windows={len(result['window_rows'])}"
        )
        all_page_rows.extend(result["page_rows"])
        all_block_rows.extend(result["block_rows"])
        all_sentence_rows.extend(result["sentence_rows"])
        all_window_rows.extend(result["window_rows"])
        metrics_rows.append(m)
        if status not in ("ok", "empty", "scanned_detect_only", "corrupted_cleaned"):
            failure_rows.append({
                "stress_doc_id": m["stress_doc_id"],
                "stress_type": m["stress_type"],
                "extraction_status": m["extraction_status"],
                "error_message": m["error_message"],
            })

    # --- Write redacted public outputs (no raw_text / clean_text) ---
    pages_path = output_dir / "stress_pages_redacted.jsonl"
    with open(pages_path, "w", encoding="utf-8") as f:
        for row in all_page_rows:
            f.write(json.dumps(redact_row(row, TEXT_FIELDS_PAGES), ensure_ascii=False) + "\n")
    print(f"\nWrote {pages_path} ({len(all_page_rows)} rows)")

    blocks_path = output_dir / "stress_blocks_redacted.jsonl"
    with open(blocks_path, "w", encoding="utf-8") as f:
        for row in all_block_rows:
            f.write(json.dumps(redact_row(row, TEXT_FIELDS_BLOCKS), ensure_ascii=False) + "\n")
    print(f"Wrote {blocks_path} ({len(all_block_rows)} rows)")

    sentences_path = output_dir / "stress_sentences_redacted.jsonl"
    with open(sentences_path, "w", encoding="utf-8") as f:
        for row in all_sentence_rows:
            f.write(json.dumps(redact_row(row, TEXT_FIELDS_SENTS), ensure_ascii=False) + "\n")
    print(f"Wrote {sentences_path} ({len(all_sentence_rows)} rows)")

    windows_path = output_dir / "stress_windows_redacted.jsonl"
    with open(windows_path, "w", encoding="utf-8") as f:
        for row in all_window_rows:
            f.write(json.dumps(redact_row(row, TEXT_FIELDS_WINDOWS), ensure_ascii=False) + "\n")
    print(f"Wrote {windows_path} ({len(all_window_rows)} rows)")

    # --- Write private full-text versions (NOT for public release) ---
    for name, rows, tf in [
        ("pages_full.jsonl", all_page_rows, TEXT_FIELDS_PAGES),
        ("blocks_full.jsonl", all_block_rows, TEXT_FIELDS_BLOCKS),
        ("sentences_full.jsonl", all_sentence_rows, TEXT_FIELDS_SENTS),
        ("windows_full.jsonl", all_window_rows, TEXT_FIELDS_WINDOWS),
    ]:
        priv_path = private_dir / name
        with open(priv_path, "w", encoding="utf-8") as f:
            for row in rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")

    # --- extraction_quality_metrics.csv ---
    metrics_fields = [
        "stress_doc_id", "stress_type", "parser_name", "extraction_status",
        "n_pages", "n_pages_empty", "empty_page_rate",
        "n_blocks", "n_sentences", "mean_sentences_per_page",
        "mean_words_per_sentence", "short_sentence_rate", "long_sentence_rate",
        "hyphenation_artifact_rate", "header_footer_residual_rate",
        "reference_section_ratio", "caption_marker_count", "table_marker_count",
        "scanned_detected", "error_message",
    ]
    metrics_path = output_dir / "extraction_quality_metrics.csv"
    with open(metrics_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=metrics_fields)
        writer.writeheader()
        for row in metrics_rows:
            writer.writerow(row)
    print(f"Wrote {metrics_path} ({len(metrics_rows)} rows)")

    # --- failure_cases_redacted.csv (only if there are failures) ---
    failure_path = output_dir / "failure_cases_redacted.csv"
    failure_fields = ["stress_doc_id", "stress_type", "extraction_status", "error_message"]
    with open(failure_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=failure_fields)
        writer.writeheader()
        for row in failure_rows:
            writer.writerow(row)
    print(f"Wrote {failure_path} ({len(failure_rows)} rows)")

    # --- run_config.json ---
    config = {
        "sources": str(sources_path),
        "output_dir": str(output_dir),
        "window_size": args.window_size,
        "n_records": len(records),
        "n_pages_total": len(all_page_rows),
        "n_blocks_total": len(all_block_rows),
        "n_sentences_total": len(all_sentence_rows),
        "n_windows_total": len(all_window_rows),
        "n_failures": len(failure_rows),
    }
    rc_path = write_run_config(
        output_dir, config, "run_pdf_extraction_stress_test_v1.py",
        extra={"purpose": "Extraction robustness test, not SOTA"},
    )
    print(f"Wrote {rc_path}")

    print(f"\nDone: {len(records)} stress docs processed, {len(failure_rows)} failures")


if __name__ == "__main__":
    main()
