# Confidentiality Red-Team Scan Summary

Generated: 2026-07-08T00:44:04
Scanned files: 253

## Gate Status

**Public Release Gate: PASS**

- High risk findings: **0**
- Medium risk findings: **0**
- Low risk findings: **38**
- Total findings: **38**
- Strict mode: False

## High Risk (0 findings)

None.

## Medium Risk (0 findings)

None.

## Low Risk (38 findings)

### toy_validation (38)

- **`release_bundles\v3_17_confidential_public\data\toy_synthetic\pdf_stress_sources.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\data\toy_synthetic\toy_claims.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\data\toy_synthetic\toy_pdf_texts.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\bm25_sentence_retrieval_v1_toy\oracle_recall_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\bm25_sentence_retrieval_v1_toy\retrieval_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\bm25_sentence_retrieval_v1_toy\retrieval_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\bm25_sentence_retrieval_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\canonicalizer_ablation_v1_toy\canonicalizer_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\canonicalizer_ablation_v1_toy\leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\canonicalizer_ablation_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\canonicalizer_ablation_v1_toy\selector_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\canonicalizer_ablation_v1_toy\selector_metrics_summary.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\format_shift_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\format_shift_inputs_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\format_shift_metrics.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\format_shift_predictions.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\format_shift_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\r4_leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\format_shift_ablation_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\claim_only_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\group_split_integrity.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\lexical_overlap_by_label.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\metadata_only_retrieval_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\no_label_in_queue_sorting_check.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\no_oracle_in_selector_check.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\leakage_audit_v1_toy\title_only_retrieval_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\lightweight_smart_queue_v1_toy\leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\lightweight_smart_queue_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\lightweight_smart_queue_v1_toy\smart_queue_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\lightweight_smart_queue_v1_toy\smart_queue_metric_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\format_shift_metrics.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\format_shift_predictions.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\format_shift_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\r4_leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\toy_end_to_end_demo_v1\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\toy_end_to_end_demo_v1\toy_run_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.

## .gitignore Check

- Existing entries: 70
- Missing entries: 0
