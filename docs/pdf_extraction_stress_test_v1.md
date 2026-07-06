# PDF Extraction Stress Test V1

## Purpose

This document describes the PDF extraction stress test pipeline, its design
rationale, and how to interpret results without overclaiming.

The stress test verifies **engineering reliability** of the local PDF
extraction pipeline (page → block → sentence → window corpus construction)
against common noise types found in real PDF documents. It does **NOT**
validate retrieval accuracy on real scientific claims, and it is **NOT** a
SOTA benchmark.

## Why Stress Testing

The V3.17 confidential lightweight pipeline begins from local PDFs. Before
retrieval or canonicalization can run, the extraction pipeline must:

1. Extract page text from PDF binary
2. Clean unicode artifacts, repair line breaks, dehyphenate
3. Remove repeated headers / footers / page numbers
4. Detect section hints (abstract, introduction, method, etc.)
5. Split into sentences and filter short fragments
6. Group sentences into sliding windows for context

Each of these steps can fail silently on degraded input. Common failure
modes include:

- Two-column layouts producing interleaved text
- Hyphenated line-break words splitting incorrectly
- Headers/footers contaminating sentence-level retrieval
- Page numbers being treated as content
- Scanned PDFs returning empty or garbage text
- Binary corruption (NUL bytes) from PDF extraction libraries
- Tables and captions polluting the sentence stream
- Reference-heavy pages overwhelming the corpus

The stress test exercises each of these cases with synthetic inputs of
known structure, so we can verify the cleaning pipeline handles them
correctly and measure the downstream impact on BM25 retrieval.

## Synthetic vs Private Mode

### Synthetic Mode (default)

The stress suite uses **synthetic** page texts from
`data/toy_synthetic/pdf_stress_sources.jsonl`. These are hand-crafted
strings that simulate each stress type. Synthetic inputs are used because:

1. They are not subject to any copyright or confidentiality constraints.
2. Their ground-truth structure is known, so we can verify cleaning
   correctness precisely.
3. They can be committed to the public repository.

### Private Mode

For real PDFs (not part of this stress test), the
`build_pdf_sentence_corpus_v1.py` script supports a `--private_mode` flag:

- **Public outputs** (`pages.jsonl`, `blocks.jsonl`, `sentences.jsonl`,
  `windows.jsonl`) contain only hashes, counts, unit IDs, page numbers,
  and section hints — **never** raw or clean text.
- **Private outputs** (`private/pages_full.jsonl`, etc.) contain the full
  text and must NOT be committed to the repository. The `private/`
  directory is gitignored.

This separation allows running the pipeline on confidential PDFs locally
while keeping public artifacts safe for release.

## Stress Types

The stress suite covers 12 stress types:

| Stress Type | Description |
|---|---|
| `normal_single_column` | Baseline: clean single-column text |
| `two_column_like` | Two-column layout with interleaved text |
| `header_footer_noise` | Repeated journal/proceedings headers and footers |
| `page_number_noise` | Stray page numbers interrupting text flow |
| `hyphenation_noise` | End-of-line hyphenated words requiring dehyphenation |
| `long_paragraph` | Single very long paragraph testing sentence splitting |
| `table_like_text` | Pipe-delimited table rows mixed with prose |
| `caption_like_text` | Figure/Table captions interspersed with body text |
| `reference_heavy` | Dense citation brackets and a references section |
| `empty_page` | Blank page (should produce zero sentences) |
| `corrupted_text` | NUL bytes and binary control chars mixed into text |
| `scanned_placeholder_detect_only` | Simulated scanned page — detected, NOT OCR'd |

## Metrics

### Extraction Quality Metrics

For each stress doc, the pipeline records 19 fields in
`extraction_quality_metrics.csv`:

| Field | Description |
|---|---|
| `stress_doc_id` | Unique ID for the stress document |
| `stress_type` | One of the 12 stress types |
| `parser_name` | Identifier for the extraction pipeline used |
| `extraction_status` | `ok`, `empty`, `scanned_detect_only`, `corrupted_cleaned`, or `failed` |
| `n_pages` | Number of pages extracted |
| `n_pages_empty` | Pages with zero words after cleaning |
| `empty_page_rate` | Fraction of pages that are empty |
| `n_blocks` | Number of paragraph-level blocks |
| `n_sentences` | Number of sentences (after short-sentence filter) |
| `mean_sentences_per_page` | Average sentences per page |
| `mean_words_per_sentence` | Average words per surviving sentence |
| `short_sentence_rate` | Fraction of sentences with < 8 words |
| `long_sentence_rate` | Fraction of sentences with > 60 words |
| `hyphenation_artifact_rate` | Fraction of sentences with residual `word-\nword` patterns |
| `header_footer_residual_rate` | Fraction of blocks that look like residual headers/footers |
| `reference_section_ratio` | Fraction of blocks tagged as `reference` section |
| `caption_marker_count` | Number of blocks starting with `Figure N` or `Table N` |
| `table_marker_count` | Number of blocks containing pipe-delimited table rows |
| `scanned_detected` | Whether the page was heuristically detected as scanned |
| `error_message` | Error string if extraction failed |

### Retrieval Under Stress

BM25 retrieval is evaluated against the extracted sentences and windows
for each stress doc, using a synthetic anchor derived from the source page:

| Metric | Description |
|---|---|
| `sentence_recall1` | Recall@1 against extracted sentences |
| `sentence-recall5` | Recall@5 |
| `sentence-recall10` | Recall@10 |
| `sentence-mrr` | Mean Reciprocal Rank |
| `window-recall1/5/10` | Same metrics against sliding windows |
| `window-mrr` | MRR against windows |

Aggregate and per-stress-type metrics are in `retrieval_stress_summary.json`.

**Important**: The anchor text is derived from the same source page as the
extraction target. Retrieval recall is therefore optimistic — the anchor
sentence is literally present in the extracted corpus. This metric measures
whether the extraction pipeline preserves the anchor sentence intact, NOT
whether BM25 can find semantically related evidence. Do not compare these
numbers to real-corpus BM25 baselines.

## No OCR by Default

Per project policy, **OCR is not performed by default**. The stress suite
includes a `scanned_placeholder_detect_only` type that simulates a scanned
PDF page. The pipeline:

1. Detects the page as scanned (very low alphanumeric ratio)
2. Reports `extraction_status = "scanned_detect_only"`
3. Does NOT attempt OCR
4. Produces zero or near-zero sentences

This is intentional. OCR would require either a local OCR engine (Tesseract)
or a cloud OCR API, both of which violate the hard boundaries
(no network, no API). Scanned PDFs are reported as a gap, not silently
OCR'd.

## Confidentiality Policy

### What is committed

- `stress_suite_manifest.csv` — hash-only manifest (no page text)
- `stress_*_redacted.jsonl` — hash-only page/block/sentence/window rows
- `extraction_quality_metrics.csv` — aggregate metrics only
- `retrieval_under_extraction_stress.csv` — `anchor_text_sha256` only (no anchor text)
- `stress_test_summary.md` — human-readable summary
- `leakage_guard_report.json` — verification that no text leaked

### What is NOT committed (gitignored)

- `private/stress_sources_full.jsonl` — full synthetic page texts
- `private/*_full.jsonl` — full-text page/block/sentence/window rows

### Leakage Guard

The `leakage_guard_report.json` file is generated by
`summarize_pdf_stress_report_v1.py` and verifies that no public/redacted
file contains any of these forbidden fields:

- `raw_text`, `clean_text`
- `raw_page_text`, `clean_page_text`
- `raw_block_text`, `clean_block_text`
- `retrieved_text`, `anchor_text`
- `evidence_text`, `claim_text`, `selected_evidence`

If any file fails this check, the leakage guard status is `FAIL` and the
stress test is considered invalid for release.

## How Not to Overclaim

When reporting results from this stress test:

1. **Do not call it a benchmark.** It is an extraction robustness test on
   synthetic inputs, not a benchmark on real scientific claims.

2. **Do not cite retrieval numbers as model performance.** The BM25
   retrieval metrics measure whether the extraction pipeline preserves
   sentences intact, not whether BM25 is a good retriever.

3. **Do not claim OCR capability.** The pipeline detects scanned PDFs but
   does not OCR them. Detection-only is a gap, not a feature.

4. **Do not claim coverage of all real-world PDF noise.** The 12 stress
   types cover common cases but are not exhaustive. Real PDFs may exhibit
   combinations of stress types or novel artifacts not in this suite.

5. **Do not claim private PDF compatibility without private-mode testing.**
   The synthetic stress test runs in public mode (synthetic inputs are
   safe). Real PDFs must be run with `--private_mode` and the leakage
   guard must pass before any output is released.

6. **Always include the disclaimer.** Any table or figure derived from
   this stress test must include a note: "Synthetic stress inputs;
   extraction robustness test, not SOTA."

## Scripts

| Script | Purpose |
|---|---|
| `scripts/build_pdf_stress_suite_v1.py` | Build stress suite manifest from synthetic sources |
| `scripts/run_pdf_extraction_stress_test_v1.py` | Run extraction pipeline against stress suite |
| `scripts/run_pdf_extraction_to_bm25_stress_v1.py` | Evaluate BM25 retrieval under stress |
| `scripts/summarize_pdf_stress_report_v1.py` | Generate summary report + leakage guard |

## Reproducing

```bash
# Step 1: Build stress suite manifest
python scripts/build_pdf_stress_suite_v1.py

# Step 2: Run extraction stress test
python scripts/run_pdf_extraction_stress_test_v1.py

# Step 3: Run BM25 stress retrieval
python scripts/run_pdf_extraction_to_bm25_stress_v1.py

# Step 4: Generate summary report
python scripts/summarize_pdf_stress_report_v1.py
```

All outputs are written to
`experiments/pdf_extraction_stress_test_v1/`.

## Tests

| Test File | What it checks |
|---|---|
| `tests/test_pdf_stress_suite_manifest.py` | Manifest exists, has required columns, covers all 12 stress types, no text fields |
| `tests/test_pdf_stress_outputs_redacted.py` | All redacted outputs have no forbidden text fields, leakage guard passes |
| `tests/test_pdf_stress_summary_exists.py` | Summary exists, disclaims SOTA, mentions robustness/OCR/synthetic/confidentiality |
