#!/usr/bin/env python
"""build_pdf_sentence_corpus_v1.py — Local PDF sentence corpus builder.

Begins from local PDFs (or toy synthetic text, or pre-chunked CSV) and
constructs page/block/sentence corpus units before retrieval. The pipeline
starts from raw PDF files, a chunk CSV, or toy synthetic text, and does
NOT read evidence_text from strict_silver CSV or any label field.

Hard boundaries:
  - no network, no API, no cloud, no PDF upload
  - no model training, no original data modification
  - does not read label fields
  - does not read evidence_text as corpus source
  - corpus is built only from local PDFs, pre-chunked CSV, or toy text

Usage:
  python scripts/build_pdf_sentence_corpus_v1.py --pdf_dir pdfs --output_dir data/pdf_corpus_v1
  python scripts/build_pdf_sentence_corpus_v1.py --toy_mode --output_dir data/pdf_corpus_toy_v1
  python scripts/build_pdf_sentence_corpus_v1.py \
      --from_chunk_csv data/simclaim_pdf_corpus_retrieval_v1/local_pdf_corpus_chunks.csv \
      --output_dir data/pdf_corpus_v1 --private_mode true
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
from collections import defaultdict, Counter
from datetime import datetime, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# PDF library loading (fitz preferred, pypdf fallback, clear error otherwise)
# ---------------------------------------------------------------------------

_PDF_LIB = None
try:
    import fitz  # pymupdf
    _PDF_LIB = "fitz"
except ImportError:
    try:
        import pypdf
        _PDF_LIB = "pypdf"
    except ImportError:
        _PDF_LIB = None


def _require_pdf_lib():
    """Return the name of the available PDF library or raise with a clear message."""
    if _PDF_LIB is not None:
        return _PDF_LIB
    msg = (
        "ERROR: No PDF library available.\n"
        "Install one of:\n"
        "  pip install pymupdf    (preferred, provides 'fitz')\n"
        "  pip install pypdf      (fallback)\n"
        "Or run in toy mode:  --toy_mode"
    )
    print(msg, file=sys.stderr)
    raise SystemExit(2)


# ---------------------------------------------------------------------------
# Cleaning functions
# ---------------------------------------------------------------------------

def sha256_text(text):
    """Return SHA-256 hex digest of text (empty string for None)."""
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def normalize_unicode(text):
    """NFC-normalize and replace common smart quotes / dashes / spaces."""
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text)
    replacements = {
        "\u2018": "'", "\u2019": "'", "\u201c": '"', "\u201d": '"',
        "\u2013": "-", "\u2014": "-", "\u2026": "...",
        "\u00a0": " ", "\u2009": " ", "\u200a": " ", "\u202f": " ",
        "\u200b": "",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def dehyphenate(text):
    """Join hyphenated line-break words: 'More-\\nover' -> 'Moreover'.

    Convention: end-of-line hyphens are removed and the two parts joined
    directly (no inserted space). Intra-line 'word- word' patterns are
    also joined. This is consistent throughout the corpus.
    """
    if not text:
        return ""
    # "More-\nover" -> "Moreover"
    text = re.sub(r"(\w)-\n(\w)", r"\1\2", text)
    # "More-\n over" -> "Moreover" (optional space after newline)
    text = re.sub(r"(\w)-\n\s+(\w)", r"\1\2", text)
    # "multi-\nagent" -> "multiagent"
    # (same rule, covered above)
    return text


def repair_linebreaks(text):
    """Merge intra-paragraph single newlines to space; preserve paragraph
    boundaries (double newline). Compress multiple spaces."""
    if not text:
        return ""
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    paragraphs = re.split(r"\n\s*\n", text)
    repaired = []
    for para in paragraphs:
        para = re.sub(r"\n", " ", para)
        para = re.sub(r"[ \t]+", " ", para)
        para = para.strip()
        if para:
            repaired.append(para)
    return "\n\n".join(repaired)


def remove_repeated_headers_footers(page_texts):
    """Lightweight heuristic header/footer removal.

    Lines that (a) are shorter than 120 chars and (b) appear in at least
    half the pages (minimum 3 pages) are treated as header/footer and
    removed. Pure-numeric lines (page numbers) are always removed.
    Caption/table rows are NOT removed (they contain 'table'/'figure'
    keywords or are inside paragraph blocks).
    """
    if not page_texts:
        return page_texts
    n_pages = len(page_texts)
    if n_pages < 3:
        # With fewer than 3 pages, only strip pure-numeric lines.
        cleaned = []
        for pt in page_texts:
            lines = pt.split("\n")
            filtered = [ln for ln in lines if not ln.strip().isdigit()]
            cleaned.append("\n".join(filtered))
        return cleaned

    line_counts = {}
    for pt in page_texts:
        lines = pt.strip().split("\n")
        candidate_lines = lines[:3] + lines[-3:]
        seen = set()
        for line in candidate_lines:
            line = line.strip()
            if not line or len(line) >= 120:
                continue
            if line not in seen:
                seen.add(line)
                line_counts[line] = line_counts.get(line, 0) + 1

    threshold = max(3, n_pages // 2)
    repeated = {line for line, count in line_counts.items() if count >= threshold}

    cleaned = []
    for pt in page_texts:
        lines = pt.split("\n")
        filtered = []
        for line in lines:
            stripped = line.strip()
            if stripped.isdigit():
                continue
            if stripped in repeated:
                continue
            filtered.append(line)
        cleaned.append("\n".join(filtered))
    return cleaned


def detect_section_hint(text):
    """Detect section hint from nearby text. Returns one of:
    abstract, introduction, method, experiment, result, discussion,
    conclusion, reference, table, figure, unknown.
    """
    if not text:
        return "unknown"
    lower = text.lower()
    head = lower[:300]
    patterns = [
        (r"\babstract\b", "abstract"),
        (r"\bintroduction\b", "introduction"),
        (r"\b(method|methodology|approach|materials and methods)\b", "method"),
        (r"\b(experiment|experimental setup|evaluation setup)\b", "experiment"),
        (r"\b(result|results)\b", "result"),
        (r"\bdiscussion\b", "discussion"),
        (r"\bconclusion\b", "conclusion"),
        (r"\b(reference|bibliography|works cited)\b", "reference"),
        (r"^\s*table\s+\d", "table"),
        (r"^\s*figure\s+\d", "figure"),
    ]
    for pattern, hint in patterns:
        if re.search(pattern, head):
            return hint
    return "unknown"


# Abbreviation set for sentence splitting guard
_ABBREVIATIONS = {
    "et al", "i.e", "e.g", "cf", "vs", "Fig", "Table", "Tbl", "Eq", "Ref",
    "Dr", "Mr", "Mrs", "Ms", "Prof", "Sr", "Jr", "St",
    "No", "Vol", "pp", "ch", "Ch", "sec", "Sec",
    "approx", "min", "max", "avg", "std",
    "U.S", "U.K", "E.U",
    "al",  # for "et al."
}


def split_sentences(text):
    """Regex-based sentence splitting with abbreviation guard.

    Splits on [.!?] followed by whitespace + capital letter or quote,
    but protects common abbreviations and decimal numbers.
    """
    if not text:
        return []
    protected = text
    for abbr in _ABBREVIATIONS:
        protected = protected.replace(abbr + ".", abbr + "<DOT>")
    protected = re.sub(r"(\d)\.(\d)", r"\1<DOT>\2", protected)
    parts = re.split(r'(?<=[.!?])\s+(?=[A-Z"(])', protected)
    sentences = []
    for s in parts:
        s = s.replace("<DOT>", ".").strip()
        if s:
            sentences.append(s)
    return sentences


# ---------------------------------------------------------------------------
# PDF extraction
# ---------------------------------------------------------------------------

def extract_pages_with_fitz(pdf_path, max_pages=None):
    """Extract page text using pymupdf/fitz."""
    doc = fitz.open(str(pdf_path))
    pages = []
    n = doc.page_count
    if max_pages is not None:
        n = min(n, max_pages)
    for i in range(n):
        page = doc[i]
        text = page.get_text("text") or ""
        pages.append({"page_number": i + 1, "raw_text": text})
    doc.close()
    return pages


def extract_pages_with_pypdf(pdf_path, max_pages=None):
    """Extract page text using pypdf."""
    reader = pypdf.PdfReader(str(pdf_path))
    pages = []
    n = len(reader.pages)
    if max_pages is not None:
        n = min(n, max_pages)
    for i in range(n):
        text = reader.pages[i].extract_text() or ""
        pages.append({"page_number": i + 1, "raw_text": text})
    return pages


def extract_pages(pdf_path, max_pages=None):
    """Extract pages using whichever PDF library is available."""
    lib = _require_pdf_lib()
    if lib == "fitz":
        return extract_pages_with_fitz(pdf_path, max_pages)
    elif lib == "pypdf":
        return extract_pages_with_pypdf(pdf_path, max_pages)
    else:
        raise RuntimeError("No PDF library available")


# ---------------------------------------------------------------------------
# Block extraction
# ---------------------------------------------------------------------------

def split_blocks(raw_page_text):
    """Split page text into blocks by double newlines (paragraph-level)."""
    if not raw_page_text:
        return []
    chunks = re.split(r"\n\s*\n", raw_page_text)
    blocks = []
    for idx, chunk in enumerate(chunks):
        chunk = chunk.strip()
        if chunk:
            blocks.append({"block_id": idx, "raw_block_text": chunk})
    return blocks


# ---------------------------------------------------------------------------
# Word counting
# ---------------------------------------------------------------------------

def count_words(text):
    if not text:
        return 0
    return len(text.split())


# ---------------------------------------------------------------------------
# Corpus building
# ---------------------------------------------------------------------------

def build_corpus_from_pages(paper_id, pdf_filename, pdf_sha256, raw_pages):
    """Given raw page texts, run cleaning/blocking/splitting and return
    page_rows, block_rows, sentence_rows, stats."""
    # Step 1: normalize + dehyphenate + repair each raw page
    processed_texts = []
    for rp in raw_pages:
        t = normalize_unicode(rp["raw_text"])
        t = dehyphenate(t)
        t = repair_linebreaks(t)
        processed_texts.append(t)

    # Step 2: header/footer removal across pages
    cleaned_texts = remove_repeated_headers_footers(processed_texts)

    page_rows = []
    block_rows = []
    sentence_rows = []
    global_sentence_id = 0

    for i, rp in enumerate(raw_pages):
        page_number = rp["page_number"]
        raw_page_text = rp["raw_text"]
        clean_page_text = cleaned_texts[i]

        # Page-level row
        page_rows.append({
            "paper_id": paper_id,
            "pdf_filename": pdf_filename,
            "pdf_sha256": pdf_sha256,
            "page_number": page_number,
            "raw_page_text": raw_page_text,
            "clean_page_text": clean_page_text,
            "raw_text_sha256": sha256_text(raw_page_text),
            "clean_text_sha256": sha256_text(clean_page_text),
            "n_chars": len(clean_page_text),
            "n_words": count_words(clean_page_text),
        })

        # Block-level rows (with section hint propagation within page)
        blocks = split_blocks(clean_page_text)
        current_hint = "unknown"
        for blk in blocks:
            block_id = blk["block_id"]
            raw_block = blk["raw_block_text"]
            clean_block = re.sub(r"[ \t]+", " ", raw_block).strip()
            block_hint = detect_section_hint(clean_block)
            n_words_block = count_words(clean_block)
            # Heading block (short with section keyword) updates current section
            if block_hint != "unknown" and n_words_block < 10:
                current_hint = block_hint
            # Use block's own hint if known, else propagate current section
            section_hint = block_hint if block_hint != "unknown" else current_hint

            block_rows.append({
                "paper_id": paper_id,
                "pdf_filename": pdf_filename,
                "pdf_sha256": pdf_sha256,
                "page_number": page_number,
                "block_id": block_id,
                "raw_block_text": raw_block,
                "clean_block_text": clean_block,
                "raw_text_sha256": sha256_text(raw_block),
                "clean_text_sha256": sha256_text(clean_block),
                "n_chars": len(clean_block),
                "n_words": count_words(clean_block),
                "section_hint": section_hint,
            })

            # Sentence-level rows (filter n_words < 5)
            sents = split_sentences(clean_block)
            for j, sent in enumerate(sents):
                n_words = count_words(sent)
                if n_words < 5:
                    continue  # short sentences do not enter retrieval corpus
                unit_id = f"{paper_id}::p{page_number}::b{block_id}::s{global_sentence_id}"
                sentence_rows.append({
                    "paper_id": paper_id,
                    "pdf_filename": pdf_filename,
                    "pdf_sha256": pdf_sha256,
                    "page_number": page_number,
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

    stats = {
        "n_pages": len(page_rows),
        "n_blocks": len(block_rows),
        "n_sentences": len(sentence_rows),
    }
    return page_rows, block_rows, sentence_rows, stats


def build_windows(sentence_rows, window_size=3):
    """Group consecutive sentences (same paper, same page) into sliding windows.

    Each window contains up to `window_size` consecutive sentences.
    Window text is the concatenation of sentence clean_text with spaces.
    Preserves source_chunk_id when present (backward-compatible).
    """
    window_rows = []
    # Group sentences by (paper_id, page_number)
    by_page = defaultdict(list)
    for s in sentence_rows:
        key = (s["paper_id"], s["page_number"])
        by_page[key].append(s)

    global_window_id = 0
    for (paper_id, page_number), sents in by_page.items():
        sents_sorted = sorted(sents, key=lambda x: x["sentence_id"])
        n = len(sents_sorted)
        if n == 0:
            continue
        # Sliding window of size window_size
        for start in range(max(1, n - window_size + 1)):
            end = min(start + window_size, n)
            window_sents = sents_sorted[start:end]
            if not window_sents:
                continue
            window_text = " ".join(s["clean_text"] for s in window_sents)
            sentence_ids = [s["sentence_id"] for s in window_sents]
            unit_ids = [s["unit_id"] for s in window_sents]
            section_hints = [s["section_hint"] for s in window_sents]
            # Use the most common section hint
            hint = Counter(section_hints).most_common(1)[0][0] if section_hints else "unknown"

            pdf_filename = window_sents[0]["pdf_filename"]
            pdf_sha256 = window_sents[0]["pdf_sha256"]
            block_ids = [s["block_id"] for s in window_sents]
            source_chunk_ids = [s.get("source_chunk_id", "") for s in window_sents]

            window_row = {
                "paper_id": paper_id,
                "pdf_filename": pdf_filename,
                "pdf_sha256": pdf_sha256,
                "page_number": page_number,
                "window_id": global_window_id,
                "unit_id": f"{paper_id}::p{page_number}::w{global_window_id}",
                "sentence_ids": json.dumps(sentence_ids),
                "sentence_unit_ids": json.dumps(unit_ids),
                "block_ids": json.dumps(block_ids),
                "clean_text": window_text,
                "clean_text_sha256": sha256_text(window_text),
                "n_chars": len(window_text),
                "n_words": count_words(window_text),
                "n_sentences_in_window": len(window_sents),
                "section_hint": hint,
            }
            # Preserve source_chunk_id provenance when available
            if any(source_chunk_ids):
                window_row["source_chunk_id"] = source_chunk_ids[0] if source_chunk_ids else ""
                window_row["source_chunk_ids"] = json.dumps(source_chunk_ids)
            window_rows.append(window_row)
            global_window_id += 1

    return window_rows


def sha256_file(path):
    """Return SHA-256 hex digest of a file's bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Chunk CSV mode: build corpus from pre-chunked PDF text
# ---------------------------------------------------------------------------

def load_chunk_csv(csv_path):
    """Load pre-chunked PDF text from CSV.

    Expected columns: chunk_id, paper_id, source_pair_id, pdf_path,
                      page_start, page_end, chunk_index, chunk_text, n_words, extract_status

    Returns list of dicts with normalized fields. Does NOT print chunk_text.
    Handles NUL characters from PDF extraction (replaces with empty string).
    """
    chunks = []
    with open(csv_path, "r", encoding="utf-8", newline="", errors="replace") as f:
        content = f.read().replace("\x00", "")
    reader = csv.DictReader(content.splitlines())
    required = {"chunk_id", "paper_id", "chunk_text", "page_start"}
    missing = required - set(reader.fieldnames or [])
    if missing:
        raise SystemExit(f"ERROR: chunk CSV missing required columns: {missing}")
    for row in reader:
        if row.get("extract_status", "ok") != "ok":
            continue
        chunks.append({
            "chunk_id": row["chunk_id"],
            "paper_id": row["paper_id"],
            "source_pair_id": row.get("source_pair_id", row["paper_id"]),
            "pdf_path": row.get("pdf_path", ""),
            "page_start": int(row.get("page_start", 1) or 1),
            "page_end": int(row.get("page_end", row.get("page_start", 1)) or 1),
            "chunk_index": int(row.get("chunk_index", 0) or 0),
            "chunk_text": row.get("chunk_text", ""),
            "n_words": int(row.get("n_words", 0) or 0),
        })
    return chunks


def build_corpus_from_chunks(chunk_rows, window_size=3):
    """Build sentence and window corpus from pre-chunked PDF text.

    Each chunk is treated as a single block. Text is normalized,
    dehyphenated, and split into sentences. source_chunk_id is preserved
    for provenance tracking.

    Unlike build_corpus_from_pages(), this does NOT do header/footer
    removal (chunks are pre-extracted) and does NOT create page-level
    rows (chunks are the atomic unit).

    Returns:
        sentence_rows, window_rows, manifest_rows, stats
    """
    by_paper = defaultdict(list)
    for chunk in chunk_rows:
        by_paper[chunk["paper_id"]].append(chunk)

    all_sentence_rows = []
    manifest_rows = []
    global_sentence_id = 0

    for paper_id, chunks in by_paper.items():
        first_chunk = chunks[0]
        pdf_path = first_chunk.get("pdf_path", "")
        pdf_filename = Path(pdf_path).name if pdf_path else paper_id
        # Path-derived hash (stable identifier; not the actual file hash
        # since source PDFs may not be accessible from this working copy).
        pdf_sha256 = sha256_text(pdf_filename)
        source_id = first_chunk.get("source_pair_id", paper_id)

        pages_seen = set()
        n_blocks = 0
        n_sentences = 0

        for chunk in chunks:
            chunk_id = chunk["chunk_id"]
            chunk_text = chunk.get("chunk_text", "")
            page_number = chunk["page_start"]
            pages_seen.add(page_number)

            # Clean the chunk text (same pipeline as page mode)
            text = normalize_unicode(chunk_text)
            text = dehyphenate(text)
            text = repair_linebreaks(text)

            if not text.strip():
                continue

            block_id = n_blocks
            n_blocks += 1
            section_hint = detect_section_hint(text)

            sents = split_sentences(text)
            for sent in sents:
                n_words = count_words(sent)
                if n_words < 5:
                    continue
                unit_id = f"{paper_id}::p{page_number}::b{block_id}::s{global_sentence_id}"
                all_sentence_rows.append({
                    "paper_id": paper_id,
                    "source_id": source_id,
                    "pdf_filename": pdf_filename,
                    "pdf_sha256": pdf_sha256,
                    "page_number": page_number,
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
                    "source_chunk_id": chunk_id,
                })
                global_sentence_id += 1
                n_sentences += 1

        manifest_rows.append({
            "paper_id": paper_id,
            "source_id": source_id,
            "pdf_filename": pdf_filename,
            "pdf_path": pdf_path,
            "pdf_sha256": pdf_sha256,
            "n_pages": len(pages_seen),
            "extraction_status": "ok",
            "n_pages_extracted": len(pages_seen),
            "n_blocks": n_blocks,
            "n_sentences": n_sentences,
            "error_message": "",
        })

    all_window_rows = build_windows(all_sentence_rows, window_size=window_size)

    stats = {
        "n_papers": len(by_paper),
        "n_chunks": len(chunk_rows),
        "n_blocks": sum(r["n_blocks"] for r in manifest_rows),
        "n_sentences": len(all_sentence_rows),
        "n_windows": len(all_window_rows),
    }
    return all_sentence_rows, all_window_rows, manifest_rows, stats


def load_toy_pages(toy_path):
    """Load toy synthetic page texts from JSONL.

    Each line: {"paper_id": ..., "pdf_filename": ..., "page_number": ..., "page_text": ...}
    Returns: list of (paper_id, pdf_filename, [page dicts])
    """
    papers = {}
    with open(toy_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            pid = rec["paper_id"]
            fname = rec["pdf_filename"]
            pn = rec["page_number"]
            ptext = rec["page_text"]
            if pid not in papers:
                papers[pid] = {"pdf_filename": fname, "pages": []}
            papers[pid]["pages"].append({"page_number": pn, "raw_text": ptext})

    result = []
    for pid, info in papers.items():
        result.append((pid, info["pdf_filename"], info["pages"]))
    return result


def discover_pdfs(pdf_dir, manifest_path):
    """Discover PDF files. If manifest_path is given, read paper_id mapping
    from it; otherwise derive paper_id from filename stem."""
    pdfs = []
    if manifest_path and os.path.isfile(manifest_path):
        with open(manifest_path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pdf_path = row.get("pdf_path") or row.get("path") or ""
                paper_id = row.get("paper_id") or row.get("id") or ""
                if pdf_path and paper_id and os.path.isfile(pdf_path):
                    pdfs.append((paper_id, Path(pdf_path)))
        return pdfs

    pdf_dir = Path(pdf_dir)
    if not pdf_dir.is_dir():
        return []
    for ext in ("*.pdf", "*.PDF"):
        for p in sorted(pdf_dir.glob(ext)):
            paper_id = p.stem
            pdfs.append((paper_id, p))
    return pdfs


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Build local PDF sentence corpus (page/block/sentence units)."
    )
    parser.add_argument("--pdf_dir", default="pdfs", help="Directory containing PDF files (default: pdfs)")
    parser.add_argument("--output_dir", default="data/pdf_corpus_v1", help="Output directory (default: data/pdf_corpus_v1)")
    parser.add_argument("--manifest", default=None, help="Optional CSV manifest mapping paper_id to pdf_path")
    parser.add_argument("--max_pages", type=int, default=None, help="Max pages to extract per PDF (optional)")
    parser.add_argument("--toy_mode", action="store_true", help="Use toy synthetic text instead of real PDFs")
    parser.add_argument("--from_chunk_csv", default=None,
                        help="Build corpus from pre-chunked CSV (chunk_id, paper_id, chunk_text, page_start, ...). "
                             "Skips PDF extraction entirely.")
    parser.add_argument("--private_mode", action="store_true",
                        help="Hash-only public outputs (no raw/clean text in pages/blocks/sentences/windows.jsonl). "
                             "Full text saved to private/ subdirectory (gitignored).")
    parser.add_argument("--private_dir", default=None,
                        help="Directory for private full-text outputs (default: data/private/pdf_corpus_v1_internal "
                             "when --from_chunk_csv, else <output_dir>/private/)")
    parser.add_argument("--window_size", type=int, default=3,
                        help="Number of consecutive sentences per window (default: 3)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    all_page_rows = []
    all_block_rows = []
    all_sentence_rows = []
    all_window_rows = []

    n_pdfs = 0
    n_success = 0
    n_failed = 0
    total_pages = 0
    total_blocks = 0
    total_sentences = 0
    total_windows = 0

    # --- Determine private_dir ---
    if args.private_mode:
        if args.private_dir:
            private_dir = Path(args.private_dir)
        elif args.from_chunk_csv:
            private_dir = Path("data/private/pdf_corpus_v1_internal")
        else:
            private_dir = output_dir / "private"
        private_dir.mkdir(parents=True, exist_ok=True)
    else:
        private_dir = None

    if args.from_chunk_csv:
        chunk_csv_path = Path(args.from_chunk_csv)
        if not chunk_csv_path.is_file():
            print(f"ERROR: chunk CSV not found at {chunk_csv_path}", file=sys.stderr)
            raise SystemExit(2)
        print(f"[chunk_csv_mode] Loading chunks from {chunk_csv_path}")
        chunk_rows = load_chunk_csv(str(chunk_csv_path))
        print(f"  {len(chunk_rows)} chunks loaded")
        all_sentence_rows, all_window_rows, manifest_rows, stats = build_corpus_from_chunks(
            chunk_rows, window_size=args.window_size
        )
        n_pdfs = stats["n_papers"]
        n_success = stats["n_papers"]
        total_blocks = stats["n_blocks"]
        total_sentences = stats["n_sentences"]
        total_windows = stats["n_windows"]
        print(f"  {stats['n_papers']} papers, {stats['n_chunks']} chunks, "
              f"{stats['n_blocks']} blocks, {stats['n_sentences']} sentences, "
              f"{stats['n_windows']} windows")
    elif args.toy_mode:
        toy_path = Path("data/toy_synthetic/toy_pdf_texts.jsonl")
        if not toy_path.is_file():
            print(f"ERROR: toy data not found at {toy_path}", file=sys.stderr)
            print("Create it or run without --toy_mode to use real PDFs.", file=sys.stderr)
            raise SystemExit(2)
        print(f"[toy_mode] Loading synthetic page texts from {toy_path}")
        toy_papers = load_toy_pages(toy_path)
        n_pdfs = len(toy_papers)
        for paper_id, pdf_filename, pages in toy_papers:
            pdf_sha256 = sha256_text(pdf_filename + "::toy")
            max_p = args.max_pages
            page_list = pages if max_p is None else pages[:max_p]
            page_rows, block_rows, sentence_rows, stats = build_corpus_from_pages(
                paper_id, pdf_filename, pdf_sha256, page_list
            )
            all_page_rows.extend(page_rows)
            all_block_rows.extend(block_rows)
            all_sentence_rows.extend(sentence_rows)
            total_pages += stats["n_pages"]
            total_blocks += stats["n_blocks"]
            total_sentences += stats["n_sentences"]
            n_success += 1
            manifest_rows.append({
                "paper_id": paper_id,
                "pdf_filename": pdf_filename,
                "pdf_path": str(toy_path),
                "pdf_sha256": pdf_sha256,
                "n_pages": stats["n_pages"],
                "extraction_status": "ok",
                "n_pages_extracted": stats["n_pages"],
                "n_blocks": stats["n_blocks"],
                "n_sentences": stats["n_sentences"],
                "error_message": "",
            })
            print(f"  [toy] {paper_id}: {stats['n_pages']} pages, {stats['n_blocks']} blocks, {stats['n_sentences']} sentences")
    else:
        lib = _require_pdf_lib()
        print(f"[pdf_mode] Using library: {lib}")
        pdf_list = discover_pdfs(args.pdf_dir, args.manifest)
        if not pdf_list:
            print(f"ERROR: No PDF files found in '{args.pdf_dir}'.", file=sys.stderr)
            print("Options:", file=sys.stderr)
            print("  1. Place PDF files in a directory and pass --pdf_dir <dir>", file=sys.stderr)
            print("  2. Run in toy mode: --toy_mode", file=sys.stderr)
            raise SystemExit(2)

        n_pdfs = len(pdf_list)
        for paper_id, pdf_path in pdf_list:
            try:
                pdf_sha256 = sha256_file(pdf_path)
                raw_pages = extract_pages(pdf_path, args.max_pages)
                page_rows, block_rows, sentence_rows, stats = build_corpus_from_pages(
                    paper_id, pdf_path.name, pdf_sha256, raw_pages
                )
                all_page_rows.extend(page_rows)
                all_block_rows.extend(block_rows)
                all_sentence_rows.extend(sentence_rows)
                total_pages += stats["n_pages"]
                total_blocks += stats["n_blocks"]
                total_sentences += stats["n_sentences"]
                n_success += 1
                manifest_rows.append({
                    "paper_id": paper_id,
                    "pdf_filename": pdf_path.name,
                    "pdf_path": str(pdf_path),
                    "pdf_sha256": pdf_sha256,
                    "n_pages": stats["n_pages"],
                    "extraction_status": "ok",
                    "n_pages_extracted": stats["n_pages"],
                    "n_blocks": stats["n_blocks"],
                    "n_sentences": stats["n_sentences"],
                    "error_message": "",
                })
                print(f"  {paper_id}: {stats['n_pages']} pages, {stats['n_blocks']} blocks, {stats['n_sentences']} sentences")
            except Exception as e:
                n_failed += 1
                manifest_rows.append({
                    "paper_id": paper_id,
                    "pdf_filename": pdf_path.name if hasattr(pdf_path, 'name') else str(pdf_path),
                    "pdf_path": str(pdf_path),
                    "pdf_sha256": "",
                    "n_pages": 0,
                    "extraction_status": "failed",
                    "n_pages_extracted": 0,
                    "n_blocks": 0,
                    "n_sentences": 0,
                    "error_message": str(e),
                })
                print(f"  FAILED {paper_id}: {e}", file=sys.stderr)

    # --- Build windows from sentences (skip if already built in chunk mode) ---
    if not all_window_rows:
        all_window_rows = build_windows(all_sentence_rows, window_size=args.window_size)
        total_windows = len(all_window_rows)
    print(f"\n{total_windows} windows (window_size={args.window_size})")

    # --- Write outputs ---

    # In private_mode, public files are hash-only (no raw/clean text).
    # Full text goes to private/ subdirectory (gitignored).
    TEXT_FIELDS_PAGES = {"raw_page_text", "clean_page_text"}
    TEXT_FIELDS_BLOCKS = {"raw_block_text", "clean_block_text"}
    TEXT_FIELDS_SENTS = {"raw_text", "clean_text"}
    TEXT_FIELDS_WINDOWS = {"clean_text"}

    def redact_row(row, text_fields):
        """Return a copy of row with text fields removed."""
        return {k: v for k, v in row.items() if k not in text_fields}

    # pdf_manifest.csv (extrasaction='ignore' for optional source_id field)
    manifest_path = output_dir / "pdf_manifest.csv"
    manifest_fields = [
        "paper_id", "source_id", "pdf_filename", "pdf_path", "pdf_sha256",
        "n_pages", "extraction_status", "n_pages_extracted",
        "n_blocks", "n_sentences", "error_message",
    ]
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields, extrasaction="ignore")
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)
    print(f"Wrote {manifest_path} ({len(manifest_rows)} rows)")

    # pages.jsonl
    pages_path = output_dir / "pages.jsonl"
    with open(pages_path, "w", encoding="utf-8") as f:
        for row in all_page_rows:
            out_row = redact_row(row, TEXT_FIELDS_PAGES) if args.private_mode else row
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    print(f"Wrote {pages_path} ({len(all_page_rows)} rows)")
    if private_dir:
        priv_path = private_dir / "pages_full.jsonl"
        with open(priv_path, "w", encoding="utf-8") as f:
            for row in all_page_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {priv_path} (private, full text)")

    # blocks.jsonl
    blocks_path = output_dir / "blocks.jsonl"
    with open(blocks_path, "w", encoding="utf-8") as f:
        for row in all_block_rows:
            out_row = redact_row(row, TEXT_FIELDS_BLOCKS) if args.private_mode else row
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    print(f"Wrote {blocks_path} ({len(all_block_rows)} rows)")
    if private_dir:
        priv_path = private_dir / "blocks_full.jsonl"
        with open(priv_path, "w", encoding="utf-8") as f:
            for row in all_block_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {priv_path} (private, full text)")

    # sentences.jsonl
    sentences_path = output_dir / "sentences.jsonl"
    with open(sentences_path, "w", encoding="utf-8") as f:
        for row in all_sentence_rows:
            out_row = redact_row(row, TEXT_FIELDS_SENTS) if args.private_mode else row
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    print(f"Wrote {sentences_path} ({len(all_sentence_rows)} rows)")
    if private_dir:
        priv_path = private_dir / "sentences_full.jsonl"
        with open(priv_path, "w", encoding="utf-8") as f:
            for row in all_sentence_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {priv_path} (private, full text)")

    # windows.jsonl
    windows_path = output_dir / "windows.jsonl"
    with open(windows_path, "w", encoding="utf-8") as f:
        for row in all_window_rows:
            out_row = redact_row(row, TEXT_FIELDS_WINDOWS) if args.private_mode else row
            f.write(json.dumps(out_row, ensure_ascii=False) + "\n")
    print(f"Wrote {windows_path} ({len(all_window_rows)} rows)")
    if private_dir:
        priv_path = private_dir / "windows_full.jsonl"
        with open(priv_path, "w", encoding="utf-8") as f:
            for row in all_window_rows:
                f.write(json.dumps(row, ensure_ascii=False) + "\n")
        print(f"Wrote {priv_path} (private, full text)")

    # extraction_summary.json
    summary = {
        "n_pdfs": n_pdfs,
        "n_success": n_success,
        "n_failed": n_failed,
        "n_pages": total_pages,
        "n_blocks": total_blocks,
        "n_sentences": total_sentences,
        "n_windows": total_windows,
        "window_size": args.window_size,
        "private_mode": args.private_mode,
        "source_mode": "chunk_csv" if args.from_chunk_csv else ("toy" if args.toy_mode else "pdf_extraction"),
        "created_at": datetime.now(timezone.utc).isoformat(),
        "no_network": True,
        "no_api": True,
    }
    if args.from_chunk_csv:
        summary["chunk_csv_source"] = str(args.from_chunk_csv)
    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote {summary_path}")
    print(f"\nDone: {n_success}/{n_pdfs} PDFs succeeded, {total_pages} pages, {total_blocks} blocks, {total_sentences} sentences, {total_windows} windows")
    if args.private_mode:
        print(f"[private_mode] Public outputs are hash-only. Full text in {private_dir}/")


if __name__ == "__main__":
    main()
