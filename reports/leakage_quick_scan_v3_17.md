# Leakage Quick Scan — V3.17 Confidential

Generated: 2026-07-06T18:36:04.851473+00:00

**Overall Status**: `WARNING`

## 1. Public/Redacted Files with Text Columns

**PASS** — No public/redacted files contain forbidden text columns.

## 2. Scripts with Hardcoded D:\ocn Paths

| Script | Occurrences | Severity |
|---|---|---|
| `scripts\build_gold_pilot_preparation_v1.py` | 5 | WARNING |
| `scripts\build_paper_ready_mixed_framework_v2.py` | 7 | WARNING |
| `scripts\build_rigourate_style_scalar_baselines.py` | 4 | WARNING |
| `scripts\build_v2_relation_realism_templates.py` | 2 | WARNING |
| `scripts\build_v3_10_1_docx.py` | 2 | WARNING |
| `scripts\build_v3_10_docx.py` | 2 | WARNING |
| `scripts\build_v3_11_docx.py` | 2 | WARNING |
| `scripts\build_v3_12_1_docx.py` | 2 | WARNING |
| `scripts\build_v3_12_docx.py` | 2 | WARNING |
| `scripts\build_v3_13_docx.py` | 2 | WARNING |
| `scripts\build_v3_13_rigourate_aware_docx.py` | 2 | WARNING |
| `scripts\build_v3_14_docx.py` | 2 | WARNING |
| `scripts\build_v3_15_attack_response_and_gate.py` | 1 | WARNING |
| `scripts\build_v3_15_hierarchical_taxonomy.py` | 2 | WARNING |
| `scripts\build_v3_16_no_gold_evidence_integration.py` | 3 | WARNING |
| `scripts\build_v3_1_docx.py` | 2 | WARNING |
| `scripts\build_v3_2_docx.py` | 2 | WARNING |
| `scripts\build_v3_2_table0_and_audit.py` | 3 | WARNING |
| `scripts\build_v3_3_docx.py` | 2 | WARNING |
| `scripts\build_v3_3_main_paper.py` | 2 | WARNING |
| `scripts\build_v3_4_docx.py` | 2 | WARNING |
| `scripts\build_v3_4_main_paper.py` | 2 | WARNING |
| `scripts\build_v3_4_taxonomy_hardening.py` | 4 | WARNING |
| `scripts\build_v3_5_docx.py` | 2 | WARNING |
| `scripts\build_v3_6_docx.py` | 2 | WARNING |
| `scripts\build_v3_7_docx.py` | 2 | WARNING |
| `scripts\build_v3_9_docx.py` | 2 | WARNING |
| `scripts\build_v3_external_gold_llm_plan_v1.py` | 4 | WARNING |
| `scripts\case_level_comparison.py` | 1 | WARNING |
| `scripts\check_v3_15_quality.py` | 2 | WARNING |
| `scripts\claim_realism_audit.py` | 1 | WARNING |
| `scripts\clean_project_state_consolidation_v1.py` | 2 | WARNING |
| `scripts\compare_rigourate_style_vs_r4.py` | 9 | WARNING |
| `scripts\eval_scalar_baselines.py` | 1 | WARNING |
| `scripts\generate_project_status_report_v1.py` | 4 | WARNING |
| `scripts\run_canonicalized_review_queue_v1.py` | 6 | WARNING |
| `scripts\run_canonicalized_risk_ranking_v1.py` | 4 | WARNING |
| `scripts\run_canonical_selector_robustness_v1.py` | 7 | WARNING |
| `scripts\run_external_gold_scifact_vitaminc_v1.py` | 2 | WARNING |
| `scripts\run_gpt_structured_judge_probe_v1.py` | 6 | WARNING |
| `scripts\run_llm_judge_baseline_v1.py` | 5 | WARNING |
| `scripts\run_mixed_framework_new_algorithm_sweep_v1.py` | 4 | WARNING |
| `scripts\run_mixed_framework_router_optimization_v2.py` | 3 | WARNING |
| `scripts\run_no_gold_evidence_integration_v3_16.py` | 4 | WARNING |
| `scripts\run_no_gold_rigourate_part1.py` | 8 | WARNING |
| `scripts\run_no_gold_rigourate_part2.py` | 7 | WARNING |
| `scripts\run_overnight_non_api_pipeline_v1.py` | 7 | WARNING |
| `scripts\run_project_state_consolidation_v1.py` | 49 | WARNING |
| `scripts\run_r4_backup_asset_search_v1.py` | 4 | WARNING |
| `scripts\run_r4_evidence_canonicalization_v1.py` | 7 | WARNING |
| `scripts\run_r4_minimal_recovery_v1.py` | 6 | WARNING |
| `scripts\run_r4_on_retrieved_evidence_v1.py` | 12 | WARNING |
| `scripts\run_r4_retrieved_replay_v1.py` | 4 | WARNING |
| `scripts\run_simclaim_pdf_retrieval_v1.py` | 7 | WARNING |
| `scripts\run_v3_15_claim_realism_audit.py` | 2 | WARNING |
| `scripts\run_v3_15_low_prevalence_screening_simulation.py` | 2 | WARNING |
| `scripts\run_v3_15_scalar_vs_relation_deep_test.py` | 6 | WARNING |
| `scripts\run_v3_16_integration_summary.py` | 7 | WARNING |
| `scripts\run_v3_18_intelligent_upgrade_v1.py` | 7 | WARNING |
| `scripts\run_v3_r4_strong_baselines_holdout_v1.py` | 6 | WARNING |
| `scripts\verify_v3_16_consistency.py` | 1 | WARNING |
| `scripts\verify_v3_16_integration_quality.py` | 3 | WARNING |
| `scripts\_v2_qc_check.py` | 2 | WARNING |
| `scripts\_v3_15_scalar_gate_view.py` | 1 | WARNING |
| `scripts\_v3_15_view_metrics.py` | 2 | WARNING |

## 3. Boundary Declarations

| Script | Boundaries Declared |
|---|---|
| `run_v3_17_confidential_pipeline.py` | no_api, no_network, no_training |
| `run_metric_robustness_v1.py` | no_api, no_network, no_training |
| `run_error_taxonomy_v1.py` | no_api, no_network, no_training |

## 4. Silver-as-Gold Risk

**PASS** — No silver-as-gold risk detected.

## 5. Forbidden Text Fields Checked

- `claim_text`
- `evidence_text`
- `selected_evidence`
- `raw_text`
- `clean_text`
- `retrieved_text`

## 6. Label Fields (Audit-Only)

- `true_label`
- `oracle_hit`
- `candidate_label_guess`
- `gold_label`
- `human_audited`
- `final_label`
- `is_strong_action`

---

> This scan is a quick check, not a substitute for the full red-team scanner.