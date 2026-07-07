# PDF Extraction Stress Test Summary

Generated: 2026-07-06T17:27:34.745592+00:00

> **This is an extraction robustness test, NOT a SOTA claim.**
> The purpose is to verify engineering reliability of the PDF
> extraction pipeline against common stress types. Results here
> must not be cited as benchmark performance.

## 1. Scope and Boundaries

- **No OCR by default**: scanned PDFs are detected and reported only.
- **No network, no API, no cloud, no training**.
- **Synthetic inputs only**: stress suite uses synthetic page texts,
  not private PDFs. No private PDF text enters public/redacted outputs.
- **Private mode**: public outputs are hash-only. Full text lives in
  `private/` subdirectory and must NOT be committed or released.
- **Anchor text usage**: anchor text is used for evaluation only,
  never for ranking. Public outputs keep only `anchor_text_sha256`.

## 2. Stress Suite Coverage

- Total stress docs: **12**
- Stress types covered: **12**

| Stress Type | N | N Blocks | N Sentences |
|---|---|---|---|
| caption_like_text | 1 | 9 | 17 |
| corrupted_text | 1 | 4 | 6 |
| empty_page | 1 | 0 | 0 |
| header_footer_noise | 1 | 9 | 13 |
| hyphenation_noise | 1 | 6 | 12 |
| long_paragraph | 1 | 2 | 8 |
| normal_single_column | 1 | 6 | 13 |
| page_number_noise | 1 | 8 | 14 |
| reference_heavy | 1 | 6 | 24 |
| scanned_placeholder_detect_only | 1 | 1 | 2 |
| table_like_text | 1 | 7 | 8 |
| two_column_like | 1 | 4 | 6 |

## 3. Extraction Quality

- OK: **9**
- Empty page: **1**
- Scanned (detect only): **1**
- Corrupted (NUL cleaned): **1**
- Failed: **0**

## 4. Retrieval Under Stress (Aggregate)

- N queries: **10**
- Sentence Recall@1: **1.0**
- Sentence Recall@5: **1.0**
- Sentence Recall@10: **1.0**
- Sentence MRR: **1.0**
- Window Recall@1: **0.2**
- Window Recall@5: **0.2**
- Window Recall@10: **0.2**
- Window MRR: **0.2**

### By Stress Type

| Stress Type | N | Sent R@1 | Sent R@5 | Sent MRR | Win R@1 | Win R@5 | Win MRR |
|---|---|---|---|---|---|---|---|
| caption_like_text | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| corrupted_text | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| header_footer_noise | 1 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |
| hyphenation_noise | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| long_paragraph | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| normal_single_column | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| page_number_noise | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| reference_heavy | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| table_like_text | 1 | 1.0 | 1.0 | 1.0 | 0.0 | 0.0 | 0.0 |
| two_column_like | 1 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 |

## 5. Confidentiality / Leakage Guard

- Status: **PASS**
- Files checked: **6**
  - [PASS] stress_pages_redacted.jsonl (12 rows)
  - [PASS] stress_blocks_redacted.jsonl (62 rows)
  - [PASS] stress_sentences_redacted.jsonl (123 rows)
  - [PASS] stress_windows_redacted.jsonl (102 rows)
  - [PASS] retrieval_under_extraction_stress.csv (12 rows)
  - [PASS] failure_cases_redacted.csv (0 rows)

## 6. How Not to Overclaim

- These results are from **synthetic** stress texts, not real PDFs.
- The stress suite validates that the extraction pipeline handles
  common noise types; it does NOT validate retrieval accuracy on
  real scientific claims.
- Anchor texts are synthetic and derived from the same source page
  as the extraction target — recall is therefore optimistic and
  should not be compared to real-corpus BM25 baselines.
- No human audit, no gold labels, no SOTA claim.
- Scanned PDFs are NOT OCR'd. Detection-only results indicate the
  pipeline correctly identifies them as non-extractable, not that
  OCR was performed.
