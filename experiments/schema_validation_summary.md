# Schema Validation Summary

Generated: 2026-07-07T17:56:54

- Total files checked: **38**
- Passed: **36**
- Failed: **2**

## Per-directory results

### `data/pdf_corpus_toy_v1` — OK (2/2 ok)

- [PASS] `pdf_manifest.csv` (schema: `pdf_manifest`)
- [PASS] `sentences.jsonl` (schema: `pdf_sentence_corpus`)

### `data/pdf_corpus_v1` — OK (2/2 ok)

- [PASS] `pdf_manifest.csv` (schema: `pdf_manifest`)
- [PASS] `sentences.jsonl` (schema: `pdf_sentence_corpus`)

### `experiments/bm25_sentence_retrieval_v1` — OK (3/3 ok)

- [PASS] `retrieval_results_sentence_bm25.csv` (schema: `bm25_retrieval_results`)
- [PASS] `retrieval_results_window_bm25.csv` (schema: `bm25_retrieval_results`)
- [PASS] `retrieval_examples_redacted.csv` (schema: `bm25_retrieval_results`)

### `experiments/bm25_sentence_retrieval_v1_toy` — OK (3/3 ok)

- [PASS] `retrieval_results_sentence_bm25.csv` (schema: `bm25_retrieval_results`)
- [PASS] `retrieval_results_window_bm25.csv` (schema: `bm25_retrieval_results`)
- [PASS] `retrieval_examples_redacted.csv` (schema: `bm25_retrieval_results`)

### `experiments/canonicalized_review_queue_v1` — OK (2/2 ok)

- [PASS] `canonicalized_r4_review_scores.csv` (schema: `r4_review_scores`)
- [PASS] `review_queue_top100.csv` (schema: `r4_review_scores`)

### `experiments/canonicalized_risk_ranking_v1` — OK (2/2 ok)

- [PASS] `risk_ranking_features.csv` (schema: `r4_review_scores`)
- [PASS] `review_queue_top100_best.csv` (schema: `r4_review_scores`)

### `experiments/canonicalizer_ablation_v1` — OK (2/2 ok)

- [PASS] `selector_variant_evidence.csv` (schema: `selector_variant_evidence`)
- [PASS] `selector_examples_redacted.csv` (schema: `selector_variant_evidence`)

### `experiments/canonicalizer_ablation_v1_toy` — OK (2/2 ok)

- [PASS] `selector_variant_evidence.csv` (schema: `selector_variant_evidence`)
- [PASS] `selector_examples_redacted.csv` (schema: `selector_variant_evidence`)

### `experiments/format_shift_ablation_v1` — FAIL (2/3 ok)

- [FAIL] `format_shift_metrics.csv` (schema: `format_shift_metrics`)
  - file does not exist
  - error: file not found
- [PASS] `format_shift_inputs.csv` (schema: `format_shift_inputs`)
- [PASS] `format_shift_inputs_redacted.csv` (schema: `format_shift_inputs`)

### `experiments/format_shift_ablation_v1_toy` — FAIL (2/3 ok)

- [FAIL] `format_shift_metrics.csv` (schema: `format_shift_metrics`)
  - file does not exist
  - error: file not found
- [PASS] `format_shift_inputs.csv` (schema: `format_shift_inputs`)
- [PASS] `format_shift_inputs_redacted.csv` (schema: `format_shift_inputs`)

### `experiments/leakage_audit_v1` — OK (6/6 ok)

- [PASS] `claim_only_baseline.json` (schema: `leakage_audit`)
- [PASS] `title_only_retrieval_baseline.json` (schema: `leakage_audit`)
- [PASS] `metadata_only_retrieval_baseline.json` (schema: `leakage_audit`)
- [PASS] `group_split_integrity.json` (schema: `leakage_audit`)
- [PASS] `no_oracle_in_selector_check.json` (schema: `leakage_audit`)
- [PASS] `no_label_in_queue_sorting_check.json` (schema: `leakage_audit`)

### `experiments/leakage_audit_v1_toy` — OK (6/6 ok)

- [PASS] `claim_only_baseline.json` (schema: `leakage_audit`)
- [PASS] `title_only_retrieval_baseline.json` (schema: `leakage_audit`)
- [PASS] `metadata_only_retrieval_baseline.json` (schema: `leakage_audit`)
- [PASS] `group_split_integrity.json` (schema: `leakage_audit`)
- [PASS] `no_oracle_in_selector_check.json` (schema: `leakage_audit`)
- [PASS] `no_label_in_queue_sorting_check.json` (schema: `leakage_audit`)

### `experiments/lightweight_smart_queue_v1` — OK (1/1 ok)

- [PASS] `smart_queue_scores.csv` (schema: `smart_queue_scores`)

### `experiments/lightweight_smart_queue_v1_toy` — OK (1/1 ok)

- [PASS] `smart_queue_scores.csv` (schema: `smart_queue_scores`)
