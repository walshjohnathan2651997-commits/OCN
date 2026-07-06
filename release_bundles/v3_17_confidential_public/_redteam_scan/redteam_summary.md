# Confidentiality Red-Team Scan Summary

Generated: 2026-07-07T02:13:56
Scanned files: 220

## Gate Status

**Public Release Gate: PASS**

- High risk findings: **0**
- Medium risk findings: **0**
- Low risk findings: **45**
- Total findings: **45**
- Strict mode: False

## High Risk (0 findings)

None.

## Medium Risk (0 findings)

None.

## Low Risk (45 findings)

### gitignore_missing (10)

- **`.gitignore`** — `pdfs/`
  - .gitignore missing required entry 'pdfs/'
  - Recommendation: Add 'pdfs/' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `private_pdfs/`
  - .gitignore missing required entry 'private_pdfs/'
  - Recommendation: Add 'private_pdfs/' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `data/private/`
  - .gitignore missing required entry 'data/private/'
  - Recommendation: Add 'data/private/' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `experiments/private/`
  - .gitignore missing required entry 'experiments/private/'
  - Recommendation: Add 'experiments/private/' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.pdf`
  - .gitignore missing required entry '*.pdf'
  - Recommendation: Add '*.pdf' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.docx`
  - .gitignore missing required entry '*.docx'
  - Recommendation: Add '*.docx' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.xlsx`
  - .gitignore missing required entry '*.xlsx'
  - Recommendation: Add '*.xlsx' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.npz`
  - .gitignore missing required entry '*.npz'
  - Recommendation: Add '*.npz' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.pkl`
  - .gitignore missing required entry '*.pkl'
  - Recommendation: Add '*.pkl' to .gitignore to prevent committing sensitive files.
- **`.gitignore`** — `*.joblib`
  - .gitignore missing required entry '*.joblib'
  - Recommendation: Add '*.joblib' to .gitignore to prevent committing sensitive files.

### toy_validation (35)

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
- **`release_bundles\v3_17_confidential_public\experiments\aggregate_metrics\toy_outputs\r4_eval_v1_toy\format_shift_failure_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
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

- Existing entries: 59
- Missing entries: 10

Missing entries:
- `pdfs/`
- `private_pdfs/`
- `data/private/`
- `experiments/private/`
- `*.pdf`
- `*.docx`
- `*.xlsx`
- `*.npz`
- `*.pkl`
- `*.joblib`
