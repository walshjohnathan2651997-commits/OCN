#!/usr/bin/env python
"""build_pdf_sentence_corpus_v1.py — Local PDF sentence corpus builder.

Begins from local PDFs (or toy synthetic text) and constructs page/block/
sentence corpus units before retrieval. The pipeline starts from raw PDF
files and does NOT read evidence_text from strict_silver CSV or any label
field.

Hard boundaries:
  - no network, no API, no cloud, no PDF upload
  - no model training, no original data modification
  - does not read label fields
  - does not read evidence_text as corpus source
  - corpus is built only from local PDFs or toy synthetic text

Usage:
  python scripts/build_pdf_sentence_corpus_v1.py --pdf_dir pdfs --output_dir data/pdf_corpus_v1
  python scripts/build_pdf_sentence_corpus_v1.py --toy_mode --output_dir data/pdf_corpus_toy_v1
"""

import argparse
import csv
import hashlib
import json
import os
import re
import sys
import unicodedata
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


def sha256_file(path):
    """Return SHA-256 hex digest of a file's bytes."""
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            h.update(chunk)
    return h.hexdigest()


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
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    manifest_rows = []
    all_page_rows = []
    all_block_rows = []
    all_sentence_rows = []

    n_pdfs = 0
    n_success = 0
    n_failed = 0
    total_pages = 0
    total_blocks = 0
    total_sentences = 0

    if args.toy_mode:
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

    # --- Write outputs ---

    # pdf_manifest.csv
    manifest_path = output_dir / "pdf_manifest.csv"
    manifest_fields = [
        "paper_id", "pdf_filename", "pdf_path", "pdf_sha256",
        "n_pages", "extraction_status", "n_pages_extracted",
        "n_blocks", "n_sentences", "error_message",
    ]
    with open(manifest_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=manifest_fields)
        writer.writeheader()
        for row in manifest_rows:
            writer.writerow(row)
    print(f"Wrote {manifest_path} ({len(manifest_rows)} rows)")

    # pages.jsonl
    pages_path = output_dir / "pages.jsonl"
    with open(pages_path, "w", encoding="utf-8") as f:
        for row in all_page_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {pages_path} ({len(all_page_rows)} rows)")

    # blocks.jsonl
    blocks_path = output_dir / "blocks.jsonl"
    with open(blocks_path, "w", encoding="utf-8") as f:
        for row in all_block_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {blocks_path} ({len(all_block_rows)} rows)")

    # sentences.jsonl
    sentences_path = output_dir / "sentences.jsonl"
    with open(sentences_path, "w", encoding="utf-8") as f:
        for row in all_sentence_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    print(f"Wrote {sentences_path} ({len(all_sentence_rows)} rows)")

    # extraction_summary.json
    summary = {
        "n_pdfs": n_pdfs,
        "n_success": n_success,
        "n_failed": n_failed,
        "n_pages": total_pages,
        "n_blocks": total_blocks,
        "n_sentences": total_sentences,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "no_network": True,
        "no_api": True,
    }
    summary_path = output_dir / "extraction_summary.json"
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    print(f"Wrote {summary_path}")
    print(f"\nDone: {n_success}/{n_pdfs} PDFs succeeded, {total_pages} pages, {total_blocks} blocks, {total_sentences} sentences")


if __name__ == "__main__":
    main()
