# Path Hardcoding Audit — V3.17

**Generated:** 2026-07-06T19:58:52.006810+00:00
**Scripts scanned:** 138

## Summary

| Classification | Count | Description |
|---|---|---|
| current_pipeline_blocker | 0 | P0 mainline scripts with D:\ocn hardcoding (must be 0) |
| current_pipeline_warning | 0 | V3.17 toolchain scripts with D:\ocn hardcoding |
| legacy_exempt | 105 | Legacy scripts listed in exemptions doc |
| safe | 33 | No D:\ocn hardcoding (or scanner code using string literal) |

## Legacy exempt scripts

See `docs/legacy_scripts_path_hardcoding_exemptions.md` for the full list.

| Path | Count |
|---|---|
| scripts/_v2_qc_check.py | 2 |
| scripts/_v3_15_scalar_gate_view.py | 1 |
| scripts/_v3_15_view_metrics.py | 2 |
| scripts/build_gold_pilot_preparation_v1.py | 5 |
| scripts/build_paper_ready_mixed_framework_v2.py | 7 |
| scripts/build_rigourate_style_scalar_baselines.py | 4 |
| scripts/build_v2_relation_realism_templates.py | 2 |
| scripts/build_v3_10_1_docx.py | 2 |
| scripts/build_v3_10_docx.py | 2 |
| scripts/build_v3_11_docx.py | 2 |
| scripts/build_v3_12_1_docx.py | 2 |
| scripts/build_v3_12_docx.py | 2 |
| scripts/build_v3_13_docx.py | 2 |
| scripts/build_v3_13_rigourate_aware_docx.py | 2 |
| scripts/build_v3_14_docx.py | 2 |
| scripts/build_v3_15_attack_response_and_gate.py | 1 |
| scripts/build_v3_15_hierarchical_taxonomy.py | 2 |
| scripts/build_v3_16_no_gold_evidence_integration.py | 3 |
| scripts/build_v3_1_docx.py | 2 |
| scripts/build_v3_2_docx.py | 2 |
| scripts/build_v3_2_table0_and_audit.py | 3 |
| scripts/build_v3_3_docx.py | 2 |
| scripts/build_v3_3_main_paper.py | 2 |
| scripts/build_v3_4_docx.py | 2 |
| scripts/build_v3_4_main_paper.py | 2 |
| scripts/build_v3_4_taxonomy_hardening.py | 4 |
| scripts/build_v3_5_docx.py | 2 |
| scripts/build_v3_6_docx.py | 2 |
| scripts/build_v3_7_docx.py | 2 |
| scripts/build_v3_9_docx.py | 2 |
| scripts/build_v3_external_gold_llm_plan_v1.py | 4 |
| scripts/case_level_comparison.py | 1 |
| scripts/check_v3_15_quality.py | 2 |
| scripts/claim_realism_audit.py | 1 |
| scripts/clean_project_state_consolidation_v1.py | 2 |
| scripts/compare_rigourate_style_vs_r4.py | 9 |
| scripts/eval_scalar_baselines.py | 1 |
| scripts/formal_baseline_v1_150/run_formal_baselines.py | 1 |
| scripts/formal_baseline_v1_150/run_leakage_diagnostics.py | 1 |
| scripts/formal_baseline_v1_150/run_prefix_stripped_baselines.py | 1 |
| scripts/llm_baseline_v1_150/prepare_llm_inputs.py | 1 |
| scripts/llm_baseline_v1_150/run_llm_baseline.py | 1 |
| scripts/llm_baseline_v1_150/score_llm_baseline.py | 1 |
| scripts/run_canonical_selector_robustness_v1.py | 7 |
| scripts/run_external_gold_scifact_vitaminc_v1.py | 2 |
| scripts/run_gpt_structured_judge_probe_v1.py | 6 |
| scripts/run_llm_judge_baseline_v1.py | 5 |
| scripts/run_mixed_framework_new_algorithm_sweep_v1.py | 4 |
| scripts/run_mixed_framework_router_optimization_v2.py | 3 |
| scripts/run_no_gold_evidence_integration_v3_16.py | 4 |
| scripts/run_no_gold_rigourate_part1.py | 8 |
| scripts/run_no_gold_rigourate_part2.py | 7 |
| scripts/run_overnight_non_api_pipeline_v1.py | 7 |
| scripts/run_project_state_consolidation_v1.py | 49 |
| scripts/run_r4_backup_asset_search_v1.py | 4 |
| scripts/run_r4_minimal_recovery_v1.py | 6 |
| scripts/run_r4_retrieved_replay_v1.py | 4 |
| scripts/run_v3_15_claim_realism_audit.py | 2 |
| scripts/run_v3_15_low_prevalence_screening_simulation.py | 2 |
| scripts/run_v3_15_scalar_vs_relation_deep_test.py | 6 |
| scripts/run_v3_16_integration_summary.py | 7 |
| scripts/run_v3_18_intelligent_upgrade_v1.py | 7 |
| scripts/run_v3_r4_strong_baselines_holdout_v1.py | 6 |
| scripts/simclaim_detemplate_v1_150/build_small_eval_comparison.py | 1 |
| scripts/simclaim_detemplate_v1_150/finalize_detemplate_dataset.py | 1 |
| scripts/simclaim_detemplate_v1_150/run_detemplate_pipeline.py | 1 |
| scripts/simclaim_detemplate_v1_150/run_llm_small_eval.py | 1 |
| scripts/simclaim_detemplate_v1_150/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v2/run_hardpair_generation.py | 1 |
| scripts/simclaim_hardpair_v2/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v2b/build_final_readout.py | 1 |
| scripts/simclaim_hardpair_v2b/run_llm_small_eval.py | 1 |
| scripts/simclaim_hardpair_v2b/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v2b/run_style_neutralization.py | 1 |
| scripts/simclaim_hardpair_v3/analyze_targeted_optimization.py | 1 |
| scripts/simclaim_hardpair_v3/build_final_readout.py | 1 |
| scripts/simclaim_hardpair_v3/run_counterfactual_decoy_generation.py | 1 |
| scripts/simclaim_hardpair_v3/run_llm_small_eval.py | 1 |
| scripts/simclaim_hardpair_v3/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v3/run_v3_resplit_seed_sweep.py | 1 |
| scripts/simclaim_hardpair_v3_targeted/run_balanced_resplit_diagnostic.py | 1 |
| scripts/simclaim_hardpair_v3_targeted/run_balanced_resplit_seed_sweep.py | 1 |
| scripts/simclaim_hardpair_v3_targeted/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v3_targeted/run_targeted_repair_generation.py | 1 |
| scripts/simclaim_hardpair_v3b/build_v3b_gate_report.py | 1 |
| scripts/simclaim_hardpair_v3b/run_small_data_baselines.py | 1 |
| scripts/simclaim_hardpair_v3b/run_v3b_generation.py | 1 |
| scripts/simclaim_release_candidate/build_release_seed_v1.py | 1 |
| scripts/simclaim_v4_scaffold/analyze_v4_pilot_leakage.py | 1 |
| scripts/simclaim_v4_scaffold/analyze_v4b_pilot_leakage.py | 1 |
| scripts/simclaim_v4_scaffold/audit_v4_source_pool.py | 1 |
| scripts/simclaim_v4_scaffold/build_v4_evidence_registry.py | 1 |
| scripts/simclaim_v4_scaffold/build_v4_generation_queue.py | 1 |
| scripts/simclaim_v4_scaffold/build_v4b_no_llm_style_control.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4_claim_generation.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4_pilot_cue_ablation.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4_pilot_small_baselines.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4b_claim_generation.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4b_no_llm_style_control_baselines.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4b_pilot_small_baselines.py | 1 |
| scripts/simclaim_v4_scaffold/run_v4b_pilot_strict_pass_baselines.py | 1 |
| scripts/simclaim_v4_scaffold/salvage_v4b_raw_outputs_with_local_repair.py | 1 |
| scripts/simclaim_v4_scaffold/validate_generated_candidates.py | 1 |
| scripts/verify_v3_16_consistency.py | 1 |
| scripts/verify_v3_16_integration_quality.py | 3 |

## Gate

**current_pipeline_blocker = 0:** PASS
