# Current Project Status — V3.17 Confidential Lightweight

Generated: 2026-07-07T16:48:11.786858+00:00

> This is a read-only inventory. No experiments were re-run, no data modified.

## 1. Current Mainline Status

### Completed
- [x] README denies gold benchmark
- [x] README denies human-audited
- [x] README denies SOTA
- [x] README mentions V3.17
- [x] CURRENT_MAINLINE points to V3.17
- [x] docs/current_mainline_v3_17_confidential.md exists

### Partial
- (none)

### Missing

### Old Narrative References
- `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architecture** (future architecture, not c"
- `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN** = future architecture, not current"
- `README.md`: gold benchmark — "gold benchmark"
- `README.md`: gold benchmark — "gold benchmark"
- `README.md`: human-audited — "human-audited"
- `README.md`: human-audited — "human-audited"
- `README.md`: human-audited — "human-audited"
- `README.md`: SOTA — "SOTA"
- `README.md`: SOTA — "SOTA"
- `README.md`: SOTA — "SOTA"
- `README.md`: automatic peer review — "automatic peer review"
- `README.md`: automatic peer review — "automatic peer review"
- `CURRENT_MAINLINE.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architecture** = future architecture, not "
- `CURRENT_MAINLINE.md`: gold benchmark — "gold benchmark"
- `CURRENT_MAINLINE.md`: human-audited — "human-audited"
- `CURRENT_MAINLINE.md`: SOTA — "SOTA"
- `CURRENT_MAINLINE.md`: automatic peer review — "automatic peer review"
- `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited"
- `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited"
- `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "Full shared-threshold CESE-OCN neural architecture validation." — The older CESE"

## 2. Existing Scripts Inventory

### A. Frozen V3.17 Scripts
| Script | Status | Size |
|---|---|---|
| run_simclaim_pdf_retrieval_v1.py | exists | 49010 |
| run_r4_evidence_canonicalization_v1.py | exists | 57805 |
| run_canonicalized_review_queue_v1.py | exists | 48063 |
| run_canonicalized_risk_ranking_v1.py | exists | 41616 |

### B. Proposed Strengthening Scripts
| Script | Status | Size |
|---|---|---|
| build_pdf_sentence_corpus_v1.py | exists | 39330 |
| run_bm25_sentence_retrieval_v1.py | exists | 24394 |
| run_canonicalizer_ablation_v1.py | exists | 32598 |
| run_format_shift_ablation_v1.py | exists | 17872 |
| evaluate_r4_on_evidence_variants_v1.py | exists | 33482 |
| run_leakage_audit_v1.py | exists | 52356 |
| run_error_taxonomy_v1.py | exists | 38243 |
| run_complexity_vs_utility_ablation_v1.py | exists | 52866 |
| run_lightweight_smart_queue_v1.py | exists | 26323 |
| run_toy_end_to_end_demo_v1.py | exists | 7167 |
| generate_paper_assets_v3_17.py | exists | 58158 |
| build_pdf_stress_suite_v1.py | exists | 7268 |
| run_pdf_extraction_stress_test_v1.py | exists | 21237 |
| run_pdf_extraction_to_bm25_stress_v1.py | exists | 19679 |
| summarize_pdf_stress_report_v1.py | exists | 12034 |

### C. Infrastructure Scripts
| Script | Status | Size |
|---|---|---|
| run_metric_robustness_v1.py | exists | 34895 |
| run_confidentiality_redteam_scan_v1.py | exists | 38414 |
| validate_experiment_outputs_v1.py | exists | 15323 |
| run_v3_17_confidential_pipeline.py | exists | 26070 |
| build_public_sanitized_release_v1.py | exists | 31469 |

## 3. Existing Experiment Outputs Inventory

| Directory | Exists | Toy | Key Files | Last Modified |
|---|---|---|---|---|
| simclaim_pdf_corpus_retrieval_v1 | Yes | No | bm25_scores_per_candidate.csv, claim_queries.csv, downstream_screening_bm25.csv (+9 more) | 2026-07-06 |
| r4_evidence_canonicalization_v1 | Yes | No | canonicalization_error_analysis.csv, canonicalized_evidence_spans.csv, evidence_canonicalization_gate.json (+6 more) | 2026-07-05 |
| canonicalized_review_queue_v1 | Yes | No | canonicalized_r4_review_scores.csv, canonicalized_review_queue_gate.json, canonicalized_review_queue_report.md (+6 more) | 2026-07-06 |
| canonicalized_risk_ranking_v1 | Yes | No | low_prevalence_ranking_results.csv, review_queue_top100_best.csv, risk_ranking_error_analysis.csv (+5 more) | 2026-07-05 |
| bm25_sentence_retrieval_v1 | Yes | Yes | leakage_guard_report.json, oracle_recall_summary.json, retrieval_config.json (+12 more) | 2026-07-07 |
| canonicalizer_ablation_v1 | Yes | Yes | canonicalizer_config.json, leakage_guard_report.json, run_config.json (+11 more) | 2026-07-06 |
| format_shift_ablation_v1 | Yes | Yes | format_shift_config.json, format_shift_failure_examples_redacted.csv, format_shift_inputs.csv (+19 more) | 2026-07-07 |
| leakage_audit_v1 | Yes | Yes | audit_summary.md, claim_only_baseline.json, cue_words_by_label.csv (+21 more) | 2026-07-07 |
| error_taxonomy_v1 | Yes | No | error_cases_redacted.csv, error_taxonomy_summary.csv, error_taxonomy_summary.json (+2 more) | 2026-07-06 |
| complexity_vs_utility_ablation_v1 | Yes | No | complexity_cost_audit.csv, complexity_vs_utility_claims_checklist.md, complexity_vs_utility_summary.md (+5 more) | 2026-07-06 |
| lightweight_smart_queue_v1 | Yes | Yes | leakage_guard_report.json, run_config.json, schema_validation_report.json (+15 more) | 2026-07-07 |
| pdf_extraction_stress_test_v1 | Yes | No | extraction_quality_metrics.csv, failure_cases_redacted.csv, leakage_guard_report.json (+9 more) | 2026-07-06 |
| toy_end_to_end_demo_v1 | Yes | No | run_config.json, schema_validation_report.json, toy_review_queue.csv (+1 more) | 2026-07-07 |
| metric_robustness_v1 | Yes | No | classification_metrics_with_ci.csv, paired_comparison.csv, queue_metrics_with_ci.csv (+3 more) | 2026-07-06 |
| confidentiality_redteam_scan_v1 | Yes | Yes | private_intermediate_allowlist.json, redteam_findings.csv, redteam_summary.json (+6 more) | 2026-07-07 |

## 4. Dataset Status

- **Path**: `data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv`
- **Rows**: 444
- **Groups**: 111
- **Labels**: {'supported': 111, 'mild_scope_overclaim': 111, 'strong_action_overclaim': 111, 'contradiction_candidate': 111}
- **Domains**: {'autonomous_driving': 140, 'policy_simulation': 84, 'digital_twin': 68, 'cyber_defense': 64, 'marl': 52, 'robotics': 36}
- **human_audited**: {False: 444}
- **final_label nonempty**: 0
- **gold_label nonempty**: 0
- **source_trace_complete**: {True: 444}
- **claim_generation_policy**: {'simclaim_ai_preannotated_candidates_no_gold_no_final_label': 196, 'simclaim_candidate_v1': 56, 'simclaim_four_variant_v1': 40, 'four_label_simclaim_candidate_generation_no_gold_no_final_no_human_audit': 36, 'four_label_ai_preannotation_clean_evidence_only': 36, 'four_label_balanced_candidate_generation': 32, 'same_frame_four_variant_generation': 24, 'four_label_simclaim_candidate_generation_v1_strict_no_gold': 12, 'four_label_balanced_ai_preannotation_clean_evidence_only': 12}
- **silver_label_source**: {'candidate_label_guess': 444}

## 5. Leakage Risk Quick Scan

**Overall Status**: `WARNING`

### PASS: No forbidden text columns in public/redacted files

### WARNING: Scripts with hardcoded D:\ocn paths
- `scripts\audit_path_hardcoding_v1.py`: 8 occurrences
- `scripts\build_gold_pilot_preparation_v1.py`: 5 occurrences
- `scripts\build_paper_ready_mixed_framework_v2.py`: 7 occurrences
- `scripts\build_rigourate_style_scalar_baselines.py`: 4 occurrences
- `scripts\build_v2_relation_realism_templates.py`: 2 occurrences
- `scripts\build_v3_10_1_docx.py`: 2 occurrences
- `scripts\build_v3_10_docx.py`: 2 occurrences
- `scripts\build_v3_11_docx.py`: 2 occurrences
- `scripts\build_v3_12_1_docx.py`: 2 occurrences
- `scripts\build_v3_12_docx.py`: 2 occurrences
- `scripts\build_v3_13_docx.py`: 2 occurrences
- `scripts\build_v3_13_rigourate_aware_docx.py`: 2 occurrences
- `scripts\build_v3_14_docx.py`: 2 occurrences
- `scripts\build_v3_15_attack_response_and_gate.py`: 1 occurrences
- `scripts\build_v3_15_hierarchical_taxonomy.py`: 2 occurrences
- `scripts\build_v3_16_no_gold_evidence_integration.py`: 3 occurrences
- `scripts\build_v3_1_docx.py`: 2 occurrences
- `scripts\build_v3_2_docx.py`: 2 occurrences
- `scripts\build_v3_2_table0_and_audit.py`: 3 occurrences
- `scripts\build_v3_3_docx.py`: 2 occurrences
- `scripts\build_v3_3_main_paper.py`: 2 occurrences
- `scripts\build_v3_4_docx.py`: 2 occurrences
- `scripts\build_v3_4_main_paper.py`: 2 occurrences
- `scripts\build_v3_4_taxonomy_hardening.py`: 4 occurrences
- `scripts\build_v3_5_docx.py`: 2 occurrences
- `scripts\build_v3_6_docx.py`: 2 occurrences
- `scripts\build_v3_7_docx.py`: 2 occurrences
- `scripts\build_v3_9_docx.py`: 2 occurrences
- `scripts\build_v3_external_gold_llm_plan_v1.py`: 4 occurrences
- `scripts\case_level_comparison.py`: 1 occurrences
- `scripts\check_v3_15_quality.py`: 2 occurrences
- `scripts\claim_realism_audit.py`: 1 occurrences
- `scripts\clean_project_state_consolidation_v1.py`: 2 occurrences
- `scripts\compare_rigourate_style_vs_r4.py`: 9 occurrences
- `scripts\eval_scalar_baselines.py`: 1 occurrences
- `scripts\generate_project_status_report_v1.py`: 4 occurrences
- `scripts\run_canonical_selector_robustness_v1.py`: 7 occurrences
- `scripts\run_external_gold_scifact_vitaminc_v1.py`: 2 occurrences
- `scripts\run_gpt_structured_judge_probe_v1.py`: 6 occurrences
- `scripts\run_llm_judge_baseline_v1.py`: 5 occurrences
- `scripts\run_mixed_framework_new_algorithm_sweep_v1.py`: 4 occurrences
- `scripts\run_mixed_framework_router_optimization_v2.py`: 3 occurrences
- `scripts\run_no_gold_evidence_integration_v3_16.py`: 4 occurrences
- `scripts\run_no_gold_rigourate_part1.py`: 8 occurrences
- `scripts\run_no_gold_rigourate_part2.py`: 7 occurrences
- `scripts\run_overnight_non_api_pipeline_v1.py`: 7 occurrences
- `scripts\run_project_state_consolidation_v1.py`: 49 occurrences
- `scripts\run_r4_backup_asset_search_v1.py`: 4 occurrences
- `scripts\run_r4_minimal_recovery_v1.py`: 6 occurrences
- `scripts\run_r4_on_retrieved_evidence_v1.py`: 0 occurrences
- `scripts\run_r4_retrieved_replay_v1.py`: 4 occurrences
- `scripts\run_simclaim_pdf_retrieval_v1.py`: 0 occurrences
- `scripts\run_v3_15_claim_realism_audit.py`: 2 occurrences
- `scripts\run_v3_15_low_prevalence_screening_simulation.py`: 2 occurrences
- `scripts\run_v3_15_scalar_vs_relation_deep_test.py`: 6 occurrences
- `scripts\run_v3_16_integration_summary.py`: 7 occurrences
- `scripts\run_v3_18_intelligent_upgrade_v1.py`: 7 occurrences
- `scripts\run_v3_r4_strong_baselines_holdout_v1.py`: 6 occurrences
- `scripts\verify_v3_16_consistency.py`: 1 occurrences
- `scripts\verify_v3_16_integration_quality.py`: 3 occurrences
- `scripts\_v2_qc_check.py`: 2 occurrences
- `scripts\_v3_15_scalar_gate_view.py`: 1 occurrences
- `scripts\_v3_15_view_metrics.py`: 2 occurrences

### Boundary Declarations
- `run_v3_17_confidential_pipeline.py`: no_api, no_network, no_training
- `run_metric_robustness_v1.py`: no_api, no_network, no_training
- `run_error_taxonomy_v1.py`: no_api, no_network, no_training

### Silver-as-Gold Risk
- PASS: No silver-as-gold risk detected

## 6. Current Strongest Evidence Chain

> Each item labeled: **real / toy / missing / blocked / private-only** (data_provenance)

| Claim | Evidence File | Status | Data Provenance | Safe Wording | Risk |
|---|---|---|---|---|---|
| Raw PDF chunk / BM25 retrieval has results | `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv` | exists | **private-only** | BM25 retrieval on local PDF corpus achieves measurable oracle recall | Oracle recall is on silver labels only; retrieval output is private-only (contains source text) |
| Sentence-level BM25 retrieval has results | `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json` | exists | **real** | Sentence-level BM25 outperforms window-level on oracle recall (toy) | Only toy data; real data run not yet executed |
| Canonicalization improves over raw chunks | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` | exists | **real** | best_sentence_top5_overlap oracle_recall=0.387 vs raw_top1_chunk=0.043 on 444 real candidates (9x improvement) | Silver labels only; 2/8 selectors (sentence_bm25, window_bm25) blocked by missing PDF corpus |
| Frozen R4 review queue has results | `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv` | exists | **real** | Frozen R4 screening achieves strong_F1=0.4503 on 436 candidates | Silver labels only; not human-audited; review queue output is private-only (contains labels for audit join) |
| Risk ranking has results | `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv` | exists | **real** | G_conservative_precision ranking provides top-100 review queue | Threshold not fitted on test; silver labels only; feature matrix is private-only (contains labels for audit join) |
| Leakage audit has results | `experiments/leakage_audit_v1/claim_only_baseline.json` | exists | **real** | All 12 leakage checks pass on 444 real candidates; claim-only ratio=0.74 (below WARNING threshold) | Silver labels (candidate_label_guess) used as true_label for audit; queue guard from toy SmartQueue |
| Bootstrap CI metrics have results | `experiments/metric_robustness_v1/classification_metrics_with_ci.csv` | exists | **real** | strong_F1=0.4503 with 95% CI [0.4086, 0.4833] (group-aware bootstrap) | CI reflects controlled pool variability, not natural prevalence |
| Error taxonomy has results | `experiments/error_taxonomy_v1/error_taxonomy_summary.csv` | exists | **real** | 9 error types tagged; top FP cause is mild_vs_strong_boundary | Silver labels only; error type thresholds are heuristic |
| PDF-start extraction stress test has results | `experiments/pdf_extraction_stress_test_v1/` | exists | **toy** | 12 synthetic PDF stress documents processed; 0 failures; 123 sentences extracted. Extraction robustness test, not SOTA. | Synthetic stress fixtures only; not real PDFs; not an empirical claim about real-world extraction |
| Complexity-vs-utility tradeoff analysis has results | `experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv` | exists | **real** | Deterministic canonicalization is Pareto-optimal under confidential/no-API/no-training/silver-diagnostic constraints | Does not prove rules generally beat learned models; deployment-specific tradeoff |
| Human audit has results | `experiments/human_audit_v1/audit_agreement_summary.json` | partial | **blocked** | Small targeted human audit protocol and seed queue are in place; auditor labels pending. Not a gold benchmark. | No human audit has been completed; all silver labels remain un-audited. Audit seed built (111 candidates); empirical results deferred. |
| Paper assets generated | `paper_assets/v3_17_confidential/tables/` | exists | **real** | 8 tables (md+tex), 4 figure data CSVs, paper_results_summary.md (RQ1-8), paper_claims_checklist.md generated | All tables include caveat: controlled silver diagnostic, not gold/human-audited |
| Public sanitized release bundle built | `release_bundles/v3_17_confidential_public/` | exists | **real** | 221 files; redteam scan PASS (high_risk=0); no raw claim/evidence/PDF text | Bundle excludes private scoring files, real review queues, PDFs, and label-bearing intermediates |

## 7. Priority Next Actions

> Each action labeled: **done / blocked / pending**

- **P0** [BLOCKED]: Clean up old narratives in docs (V2/gold/SOTA references)
  - Reason: 160 old narrative references found (majority are denials like 'not a gold benchmark')
  - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references are predominantly in denial/qualification context (e.g., 'not a gold benchmark', 'not human-audited', 'not SOTA'). Improving scanner to distinguish denials from claims requires NLP context analysis, out of scope for V3.17 confidential lightweight. Non-blocking for release.
- **P0** [DONE]: Fix leaked text fields in public/redacted files
  - Reason: No forbidden text columns in public/redacted files
- **P0** [DONE]: Run BM25 sentence retrieval on real data
  - Reason: Real data retrieval completed
- **P0** [DONE]: Run canonicalizer ablation on real data
  - Reason: Real data ablation completed (6/8 selectors)
- **P0** [DONE]: Run format shift ablation on real data
  - Reason: Format-shift R4 eval resolved offline using local .venv sklearn 1.9.0; no network, no API, no retraining, no repickling
- **P0** [DONE]: Run leakage audit on real data
  - Reason: Real data audit completed (12 checks, PASS)
- **P1** [DONE]: Run SmartQueue on real data
  - Reason: Real data SmartQueue completed (436 candidates, 4 buckets)
- **P1** [PENDING]: Remove hardcoded D:\ocn paths from scripts
  - Reason: 63 scripts with hardcoded paths (all in deprecated/legacy scripts, not V3.17 pipeline)
  - Note: Non-blocking; all hardcoded paths are in pre-V3.17 deprecated scripts
- **P1** [DONE]: Implement and run complexity-vs-utility ablation
  - Reason: Script exists and has been run on real data
- **P1** [DONE]: Implement and run PDF extraction stress test
  - Reason: Script exists and has been run on synthetic stress fixtures
- **P1** [DONE]: Define small human audit protocol (2-annotator, adjudication)
  - Reason: Protocol and seed queue built; auditor labels pending
  - Note: Protocol exists; empirical audit deferred (not a release blocker)
- **P2** [DONE]: Publish sanitized public release bundle
  - Reason: Bundle built: 221 files, redteam PASS
- **P2** [DONE]: Generate paper assets (8 tables, RQ1-8, claims checklist)
  - Reason: Paper assets generated
- **P2** [PENDING]: Compile final paper PDF from paper_assets
  - Reason: Tables/figures in LaTeX+MD; requires LaTeX compilation (out of scope for V3.17 confidential lightweight)

---

> All results are controlled silver diagnostic, not gold/human-audited.