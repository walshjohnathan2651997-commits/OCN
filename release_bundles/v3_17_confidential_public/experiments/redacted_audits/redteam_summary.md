# Confidentiality Red-Team Scan Summary

Generated: 2026-07-07T13:10:28
Scanned files: 805

## Gate Status

**Public Release Gate: FAIL**

- High risk findings: **3**
- Medium risk findings: **22**
- Low risk findings: **54**
- Total findings: **79**
- Strict mode: False

## High Risk (3 findings)

### forbidden_sorting_field (3)

- **`experiments\canonicalized_review_queue_v1\canonicalized_r4_review_scores.csv`** — `true_label`
  - Scoring output contains forbidden sorting field 'true_label'
  - Location: header
  - Recommendation: Remove 'true_label' from scoring output. This field must not appear in any sorting/scoring CSV.
- **`experiments\canonicalized_risk_ranking_v1\risk_ranking_features.csv`** — `true_label`
  - Scoring output contains forbidden sorting field 'true_label'
  - Location: header
  - Recommendation: Remove 'true_label' from scoring output. This field must not appear in any sorting/scoring CSV.
- **`experiments\canonicalized_risk_ranking_v1\risk_ranking_features.csv`** — `oracle_hit`
  - Scoring output contains forbidden sorting field 'oracle_hit'
  - Location: header
  - Recommendation: Remove 'oracle_hit' from scoring output. This field must not appear in any sorting/scoring CSV.

## Medium Risk (22 findings)

### filename_risk (22)

- **`experiments\canonicalized_review_queue_v1\review_queue_top100.csv`** — `top100`
  - Filename contains sensitive keyword 'top100'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\canonicalized_risk_ranking_v1\review_queue_top100_best.csv`** — `top100`
  - Filename contains sensitive keyword 'top100'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\external_gold_scifact_vitaminc_v1\external_gold_readiness_gate.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\external_gold_scifact_vitaminc_v1\external_gold_results_summary.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\external_gold_scifact_vitaminc_v1\external_gold_subset_provenance.csv`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\lightweight_smart_queue_v1\smart_queue_top100.csv`** — `top100`
  - Filename contains sensitive keyword 'top100'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\rigourate_reproduction_and_simclaim_baseline_v1\proposed_relation_realism_gold_protocol_v2.md`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_11_non_gold_robustness_stress_test\non_gold_robustness_master_report.md`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_11_non_gold_robustness_stress_test\non_gold_robustness_readiness_gate.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\external_gold_expected_outputs.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\external_gold_llm_readiness_gate.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\external_gold_sampling_plan.csv`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\external_gold_test_protocol.md`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\public_gold_dataset_inventory.csv`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`experiments\v3_external_gold_llm_plan_v1\public_gold_dataset_inventory.json`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\build_gold_pilot_preparation_v1.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\build_v3_16_no_gold_evidence_integration.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\build_v3_external_gold_llm_plan_v1.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\run_external_gold_scifact_vitaminc_v1.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\run_no_gold_evidence_integration_v3_16.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\run_no_gold_rigourate_part1.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.
- **`scripts\run_no_gold_rigourate_part2.py`** — `gold`
  - Filename contains sensitive keyword 'gold'
  - Recommendation: Ensure this file is excluded from public release artifacts.

## Low Risk (54 findings)

### filename_risk (1)

- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_top100.csv`** — `top100`
  - Filename contains sensitive keyword 'top100'
  - Recommendation: Verify this file is NOT included in public release. If toy/synthetic, prefix with 'toy_' to clarify.

### toy_validation (53)

- **`data\toy_synthetic\pdf_stress_sources.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`data\toy_synthetic\toy_candidates_v1.csv`** — `claim_text`
  - Toy data file has text column 'claim_text' without 'toy_' prefix
  - Location: header
  - Recommendation: Rename column to 'toy_claim_text' or add 'synthetic=true' marker to the file.
- **`data\toy_synthetic\toy_candidates_v1.csv`** — `evidence_text`
  - Toy data file has text column 'evidence_text' without 'toy_' prefix
  - Location: header
  - Recommendation: Rename column to 'toy_evidence_text' or add 'synthetic=true' marker to the file.
- **`data\toy_synthetic\toy_candidates_v1.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`data\toy_synthetic\toy_claims.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`data\toy_synthetic\toy_pdf_texts.jsonl`** — ``
  - Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Location: line 1
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\bm25_sentence_retrieval_v1_toy\oracle_recall_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\bm25_sentence_retrieval_v1_toy\retrieval_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\bm25_sentence_retrieval_v1_toy\retrieval_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\bm25_sentence_retrieval_v1_toy\retrieval_results_sentence_bm25.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\bm25_sentence_retrieval_v1_toy\retrieval_results_window_bm25.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\bm25_sentence_retrieval_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\canonicalizer_ablation_v1_toy\canonicalizer_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\canonicalizer_ablation_v1_toy\leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\canonicalizer_ablation_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\canonicalizer_ablation_v1_toy\selector_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\canonicalizer_ablation_v1_toy\selector_metrics_summary.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\canonicalizer_ablation_v1_toy\selector_variant_evidence.csv`** — `selected_evidence`
  - Toy data file has text column 'selected_evidence' without 'toy_' prefix
  - Location: header
  - Recommendation: Rename column to 'toy_selected_evidence' or add 'synthetic=true' marker to the file.
- **`experiments\canonicalizer_ablation_v1_toy\selector_variant_evidence.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\confidentiality_redteam_scan_v1_toy\redteam_findings.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\confidentiality_redteam_scan_v1_toy\redteam_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\confidentiality_redteam_scan_v1_toy\run_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\format_shift_ablation_v1_toy\format_shift_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\format_shift_ablation_v1_toy\format_shift_inputs.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\format_shift_ablation_v1_toy\format_shift_inputs_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\format_shift_ablation_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\claim_only_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\group_split_integrity.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\lexical_overlap_by_label.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\leakage_audit_v1_toy\metadata_only_retrieval_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\no_label_in_queue_sorting_check.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\no_oracle_in_selector_check.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\leakage_audit_v1_toy\title_only_retrieval_baseline.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\lightweight_smart_queue_v1_toy\leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\lightweight_smart_queue_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_config.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_metric_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_scores.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_top100.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_top20.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\lightweight_smart_queue_v1_toy\smart_queue_top50.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\r4_eval_v1_toy\format_shift_failure_examples_redacted.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\r4_eval_v1_toy\format_shift_metrics.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\r4_eval_v1_toy\format_shift_predictions.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\r4_eval_v1_toy\format_shift_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\r4_eval_v1_toy\r4_leakage_guard_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\r4_eval_v1_toy\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\toy_end_to_end_demo_v1\schema_validation_report.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\toy_end_to_end_demo_v1\toy_review_queue.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.
- **`experiments\toy_end_to_end_demo_v1\toy_run_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\v3_17_confidential_pipeline_runs\smoke_test_toy\run_summary.json`** — ``
  - Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker
  - Recommendation: Add 'synthetic: true' field or prefix keys with 'toy_'.
- **`experiments\v3_17_confidential_pipeline_runs\smoke_test_toy\stage_status.csv`** — ``
  - Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker
  - Recommendation: Add 'toy_' prefix to column names or include a 'synthetic=true' column.

## .gitignore Check

- Existing entries: 70
- Missing entries: 0
