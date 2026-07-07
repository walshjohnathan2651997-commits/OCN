# Artifact Ledger — V3.17 Confidential Lightweight

Generated: 2026-07-07T05:01:58+0000

> Read-only scan. No artifacts were modified.

## Summary

| Metric | Count |
|---|---|
| Total artifacts | 54 |
| Exists on disk | 54 |
| Safe to release | 46 |
| Private/sensitive | 8 |
| Contains raw text | 4 |
| Blocked run mode | 3 |

## Release Safety Gate

**PASS**: No public_safe artifact contains raw text.

**PASS**: No private_sensitive artifact is marked safe_to_release.

**Overall: PASS**

---

## Full Artifact Ledger

| ID | Path | Type | Run Mode | Raw Text | Labels | Oracle | Safe to Release | Notes |
|---|---|---|---|---|---|---|---|---|
| A001_strict_silver_csv | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` | dataset_csv | real | yes | yes | no | no | Controlled silver diagnostic; contains claim_text, evidence_... |
| A002_strict_silver_groups | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_groups_v1.csv` | dataset_metadata | real | no | no | no | yes | Group-level metadata only; no raw text or labels. |
| A003_dataset_version_lock | `docs/dataset_version_lock_v3_17.md` | documentation | real | no | no | no | yes | Version lock document with SHA256, row counts, field constra... |
| A010_pdf_corpus_chunks | `data/simclaim_pdf_corpus_retrieval_v1/local_pdf_corpus_chunks.csv` | pdf_corpus | real | no | no | no | no | Contains chunk text extracted from PDFs. Never released. |
| A011_pdf_corpus_toy | `data/pdf_corpus_toy_v1/pdf_manifest.csv` | pdf_corpus_toy | toy | no | no | no | yes | Toy PDF manifest; no real PDF text. |
| A020_retrieval_metrics | `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json` | metrics_json | real | no | no | no | yes | Aggregate metrics only; recall@k, MRR. No raw text. |
| A021_retrieval_results | `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv` | retrieval_results_csv | real | no | no | no | no | Per-candidate retrieval results; may contain chunk text snip... |
| A022_bm25_sentence_blocked | `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json` | blocked_metrics_json | blocked | no | no | no | yes | Blocked: missing PDF sentence corpus. Contains status only. |
| A030_canonicalizer_metrics | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` | metrics_csv | real | no | no | no | yes | Selector-level metrics; oracle_recall, mean_overlap. No raw ... |
| A031_canonicalizer_variant_evidence | `experiments/canonicalizer_ablation_v1/selector_variant_evidence.csv` | evidence_csv | real | yes | no | no | no | Contains selected_evidence (raw text). Never released. |
| A032_canonicalizer_redacted | `experiments/canonicalizer_ablation_v1/selector_examples_redacted.csv` | redacted_csv | real | no | no | no | yes | Redacted examples; hash-only, no raw text. |
| A040_format_shift_inputs | `experiments/format_shift_ablation_v1/format_shift_inputs.csv` | inputs_csv | real | no | no | no | no | Contains evidence text variants. Never released. |
| A041_format_shift_redacted | `experiments/format_shift_ablation_v1/format_shift_inputs_redacted.csv` | redacted_csv | real | no | no | no | yes | Redacted format-shift inputs; hash-only. |
| A042_format_shift_blocked | `experiments/format_shift_ablation_v1/r4_eval_blocked.json` | blocked_metrics_json | blocked | no | no | no | yes | Blocked: sklearn version mismatch. Contains status only. |
| A050_review_queue_scores | `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv` | scores_csv | real | yes | yes | no | no | Per-candidate scores; may link to labels. Not released. |
| A051_review_queue_top100 | `experiments/canonicalized_review_queue_v1/review_queue_top100.csv` | queue_csv | real | yes | yes | no | no | Top-100 queue; contains candidate IDs and scores. Not releas... |
| A052_risk_ranking_results | `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv` | metrics_csv | real | no | no | no | yes | Variant-level ranking metrics; precision@k, recall@k. No raw... |
| A053_risk_ranking_report | `experiments/canonicalized_risk_ranking_v1/risk_ranking_report.md` | report_md | real | no | no | no | yes | Summary report; aggregate metrics only. |
| A060_leakage_audit_summary | `experiments/leakage_audit_v1/audit_summary.md` | report_md | real | no | no | no | yes | 12-check audit summary; PASS. No raw text. |
| A061_claim_only_baseline | `experiments/leakage_audit_v1/claim_only_baseline.json` | metrics_json | real | no | no | no | yes | Claim-only baseline F1; aggregate metric. |
| A062_shuffled_evidence_baseline | `experiments/leakage_audit_v1/shuffled_evidence_baseline.json` | metrics_json | real | no | no | no | yes | Shuffled evidence baseline; aggregate metric. |
| A070_error_taxonomy_summary | `experiments/error_taxonomy_v1/error_taxonomy_summary.csv` | metrics_csv | real | no | no | no | yes | Error type counts and rates; aggregate. No raw text. |
| A071_error_cases_redacted | `experiments/error_taxonomy_v1/error_cases_redacted.csv` | redacted_csv | real | no | yes | yes | yes | Redacted error cases; hash-only, no raw text. |
| A080_classification_metrics_ci | `experiments/metric_robustness_v1/classification_metrics_with_ci.csv` | metrics_csv | real | no | no | no | yes | F1/precision/recall with bootstrap CIs. No raw text. |
| A081_robustness_summary | `experiments/metric_robustness_v1/robustness_summary.md` | report_md | real | no | no | no | yes | Summary report; aggregate metrics only. |
| A090_pareto_table | `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` | metrics_csv | real | no | no | no | yes | Pareto table; 8 methods x 6 scores. No raw text. |
| A091_complexity_summary | `experiments/complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md` | report_md | real | no | no | no | yes | Summary report; aggregate metrics only. |
| A100_stress_summary | `experiments/pdf_extraction_stress_test_v1/stress_test_summary.md` | report_md | toy | no | no | no | yes | Extraction robustness summary; synthetic data only. |
| A101_stress_blocks_redacted | `experiments/pdf_extraction_stress_test_v1/stress_blocks_redacted.jsonl` | redacted_jsonl | toy | no | no | no | yes | Redacted stress blocks; hash-only. |
| A110_audit_template | `data/audit_templates/human_audit_template.csv` | template_csv | real | no | yes | no | yes | Audit template; 17 fields, no claim/evidence text. |
| A111_audit_queue_redacted | `data/audit_templates/human_audit_queue_seed_v1_redacted.csv` | redacted_csv | real | no | no | no | yes | Redacted audit queue seeds; hash-only. |
| A112_audit_protocol | `docs/human_audit_protocol_v1.md` | documentation | real | no | no | no | yes | Audit protocol; no raw text. |
| A120_smart_queue_summary | `experiments/lightweight_smart_queue_v1/smart_queue_metric_summary.json` | metrics_json | real | no | no | no | yes | SmartQueue summary; aggregate metrics. |
| A121_smart_queue_top100 | `experiments/lightweight_smart_queue_v1/smart_queue_top100.csv` | queue_csv | real | no | no | no | no | Top-100 queue; contains candidate IDs. Not released. |
| A130_paper_results_summary | `paper_assets/v3_17_confidential/paper_results_summary.md` | paper_summary_md | real | no | no | no | yes | Paper results summary; aggregate metrics only. |
| A131_paper_claims_checklist | `paper_assets/v3_17_confidential/paper_claims_checklist.md` | paper_checklist_md | real | no | no | no | yes | Claims checklist; safe/unsafe wording. |
| A132_abstract_draft | `paper_assets/v3_17_confidential/abstract_draft.md` | paper_draft_md | real | no | no | no | yes | Frozen abstract draft; sourced metrics only. |
| A133_contribution_bullets | `paper_assets/v3_17_confidential/contribution_bullets.md` | paper_draft_md | real | no | no | no | yes | 4 contribution bullets with source traceability. |
| A134_limitations_draft | `paper_assets/v3_17_confidential/limitations_draft.md` | paper_draft_md | real | no | no | no | yes | 9 limitations (L1-L9) with source files. |
| A135_table1_dataset | `paper_assets/v3_17_confidential/tables/table1_dataset_summary.md` | paper_table_md | real | no | no | no | yes | Table 1; aggregate dataset stats. |
| A136_table2_retrieval | `paper_assets/v3_17_confidential/tables/table2_retrieval_recall.md` | paper_table_md | real | no | no | no | yes | Table 2; BM25 recall@k. |
| A137_table4_canonicalizer | `paper_assets/v3_17_confidential/tables/table4_canonicalizer_ablation.md` | paper_table_md | real | no | no | no | yes | Table 4; canonicalizer ablation. |
| A138_table5_review_queue | `paper_assets/v3_17_confidential/tables/table5_review_queue.md` | paper_table_md | real | no | no | no | yes | Table 5; review queue precision@k. |
| A139_table6_leakage | `paper_assets/v3_17_confidential/tables/table6_leakage_audit.md` | paper_table_md | real | no | no | no | yes | Table 6; leakage audit checks. |
| A140_table7_complexity | `paper_assets/v3_17_confidential/tables/table7_complexity_utility.md` | paper_table_md | real | no | no | no | yes | Table 7; complexity-utility Pareto. |
| A141_table3_format_shift | `paper_assets/v3_17_confidential/tables/table3_format_shift_ablation.md` | paper_table_md | blocked | no | no | no | yes | Table 3; format-shift ablation. Blocked by sklearn version m... |
| A142_table8_human_audit | `paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md` | paper_table_md | real | no | no | no | yes | Table 8; human audit status. Partial/blocked; no adjudicatio... |
| A150_release_manifest | `release_bundles/v3_17_confidential_public/MANIFEST.json` | release_manifest | real | no | no | no | yes | Release manifest; lists all included files. |
| A151_release_redaction_report | `release_bundles/v3_17_confidential_public/REDACTION_REPORT.json` | redaction_report | real | no | no | no | yes | Redaction report; verifies no raw text in release. |
| A160_paper_outline | `docs/paper_outline_v3_17_confidential.md` | documentation | real | no | no | no | yes | Frozen paper outline; RQ1-7, section structure. |
| A161_result_narrative_freeze | `docs/result_narrative_freeze_v3_17.md` | documentation | real | no | no | no | yes | Frozen result narrative; 13 results with safe/unsafe interpr... |
| A162_reviewer_risk_register | `docs/reviewer_risk_register_v3_17.md` | documentation | real | no | no | no | yes | 10 reviewer risks with safe responses. |
| A163_safe_claims_dictionary | `docs/safe_claims_dictionary_v3_17.md` | documentation | real | no | no | no | yes | Safe/unsafe wording dictionary. |
| A164_reproducibility_guide | `docs/reproducibility_guide_v3_17.md` | documentation | real | no | no | no | yes | Reproducibility guide; environment, toy run, real run. |

## Sensitive Column Detection Details

| ID | Sensitive Columns | Label Columns | Oracle Columns |
|---|---|---|---|
| A001_strict_silver_csv | claim_text, evidence_text, generation_notes, title, url | candidate_label_guess, final_label, gold_label, human_audited, silver_label_source | — |
| A031_canonicalizer_variant_evidence | selected_evidence | — | — |
| A050_review_queue_scores | selected_evidence | true_label | — |
| A051_review_queue_top100 | claim_text, selected_evidence | true_label | — |
| A071_error_cases_redacted | — | true_label | oracle_hit |
| A110_audit_template | — | human_audited | — |
