# Legacy Scripts — Path Hardcoding Exemptions

> **Authority:** This document lists scripts that retain `D:\ocn` hardcoded
> paths and are **exempt** from the V3.17 path-configurability requirement.
> These scripts are **legacy / deprecated / not current V3.17 mainline** and
> are excluded from the current reproducibility claim.

## Scope

The V3.17 Confidential Lightweight mainline requires all P0 pipeline scripts
to use repo-root-relative paths via `scripts/lib/config_utils.py` and
`configs/v3_17_paths.yaml`. The scripts listed below are **not** on the
current mainline and are therefore exempt from this requirement.

**These scripts are retained for historical reference only.** They are not
part of the V3.17 reproducibility claim, not run by `make toy` or
`make p0-real`, and not tested by the V3.17 CI smoke suite.

## Exemption categories

### 1. V3.1–V3.16 docx/paper builders (legacy paper generation)

These scripts generated paper-ready docx/table artifacts for older V3.x
manuscript versions. The current mainline uses
`scripts/generate_paper_assets_v3_17.py` instead.

| Script | Legacy version |
|---|---|
| `scripts/build_v3_1_docx.py` | V3.1 |
| `scripts/build_v3_2_docx.py` | V3.2 |
| `scripts/build_v3_2_table0_and_audit.py` | V3.2 |
| `scripts/build_v3_3_docx.py` | V3.3 |
| `scripts/build_v3_3_main_paper.py` | V3.3 |
| `scripts/build_v3_4_docx.py` | V3.4 |
| `scripts/build_v3_4_main_paper.py` | V3.4 |
| `scripts/build_v3_4_taxonomy_hardening.py` | V3.4 |
| `scripts/build_v3_5_docx.py` | V3.5 |
| `scripts/build_v3_6_docx.py` | V3.6 |
| `scripts/build_v3_7_docx.py` | V3.7 |
| `scripts/build_v3_9_docx.py` | V3.9 |
| `scripts/build_v3_10_docx.py` | V3.10 |
| `scripts/build_v3_10_1_docx.py` | V3.10.1 |
| `scripts/build_v3_11_docx.py` | V3.11 |
| `scripts/build_v3_12_docx.py` | V3.12 |
| `scripts/build_v3_12_1_docx.py` | V3.12.1 |
| `scripts/build_v3_13_docx.py` | V3.13 |
| `scripts/build_v3_13_rigourate_aware_docx.py` | V3.13 |
| `scripts/build_v3_14_docx.py` | V3.14 |
| `scripts/build_v3_15_attack_response_and_gate.py` | V3.15 |
| `scripts/build_v3_15_hierarchical_taxonomy.py` | V3.15 |
| `scripts/build_v3_16_no_gold_evidence_integration.py` | V3.16 |

### 2. V2 / mixed-framework scripts (legacy architecture)

These scripts belong to the V2 evidence-aware hierarchical pilot or the
mixed-framework router optimization era. The current mainline is V3.17
Confidential Lightweight (R4 + evidence canonicalization + review queue).

| Script | Notes |
|---|---|
| `scripts/_v2_qc_check.py` | V2 quality check |
| `scripts/build_v2_relation_realism_templates.py` | V2 template builder |
| `scripts/build_paper_ready_mixed_framework_v2.py` | Mixed-framework V2 paper builder |
| `scripts/run_mixed_framework_router_optimization_v2.py` | Mixed-framework router (pre-V3.17) |
| `scripts/run_mixed_framework_new_algorithm_sweep_v1.py` | Mixed-framework sweep (pre-V3.17) |
| `scripts/run_v3_r4_strong_baselines_holdout_v1.py` | V3 R4 strong baselines (pre-V3.17) |
| `scripts/run_v3_18_intelligent_upgrade_v1.py` | V3.18 negative ablation (not mainline) |

### 3. V3.15–V3.16 diagnostic scripts (legacy diagnostics)

| Script | Notes |
|---|---|
| `scripts/_v3_15_scalar_gate_view.py` | V3.15 scalar gate viewer |
| `scripts/_v3_15_view_metrics.py` | V3.15 metrics viewer |
| `scripts/check_v3_15_quality.py` | V3.15 quality check |
| `scripts/run_v3_15_claim_realism_audit.py` | V3.15 realism audit |
| `scripts/run_v3_15_low_prevalence_screening_simulation.py` | V3.15 prevalence sim |
| `scripts/run_v3_15_scalar_vs_relation_deep_test.py` | V3.15 deep test |
| `scripts/verify_v3_16_consistency.py` | V3.16 consistency check |
| `scripts/verify_v3_16_integration_quality.py` | V3.16 integration quality |
| `scripts/run_no_gold_evidence_integration_v3_16.py` | V3.16 no-gold integration |
| `scripts/run_v3_16_integration_summary.py` | V3.16 integration summary |

### 4. R4 recovery / replay scripts (pre-V3.17 frozen artifacts)

These scripts built the frozen R4 artifacts that V3.17 uses as read-only
inputs. The artifacts themselves are frozen; the scripts are not re-run.

| Script | Notes |
|---|---|
| `scripts/run_r4_minimal_recovery_v1.py` | R4 minimal recovery (frozen artifacts) |
| `scripts/run_r4_retrieved_replay_v1.py` | R4 retrieved evidence replay |
| `scripts/run_r4_backup_asset_search_v1.py` | R4 backup asset search |
| `scripts/run_canonical_selector_robustness_v1.py` | Canonical selector robustness (frozen) |

### 5. LLM / API baseline scripts (not mainline; require authorization)

These scripts require LLM API access and are **not** part of the no-API
V3.17 mainline. They are retained for the Task Q DeepSeek pilot only.

| Script | Notes |
|---|---|
| `scripts/run_gpt_structured_judge_probe_v1.py` | GPT structured judge probe |
| `scripts/run_llm_judge_baseline_v1.py` | LLM judge baseline |
| `scripts/run_external_gold_scifact_vitaminc_v1.py` | External gold (SciFact/VitaminC) |
| `scripts/build_v3_external_gold_llm_plan_v1.py` | External gold LLM plan |

### 6. RIGOURATE-related scripts (legacy scalar baselines)

| Script | Notes |
|---|---|
| `scripts/build_rigourate_style_scalar_baselines.py` | RIGOURATE-style scalar baselines |
| `scripts/compare_rigourate_style_vs_r4.py` | RIGOURATE vs R4 comparison |
| `scripts/run_no_gold_rigourate_part1.py` | No-gold RIGOURATE part 1 |
| `scripts/run_no_gold_rigourate_part2.py` | No-gold RIGOURATE part 2 |
| `scripts/eval_scalar_baselines.py` | Scalar baseline evaluation |

### 7. SimClaim scaffold / hardpair / detemplate scripts (legacy data generation)

These scripts generated SimClaim candidates, hard pairs, and detemplated
datasets. The current mainline uses the frozen `strict_silver_max_v1` CSV.

| Script group | Directory |
|---|---|
| SimClaim V4 scaffold | `scripts/simclaim_v4_scaffold/` |
| SimClaim hardpair V2 | `scripts/simclaim_hardpair_v2/` |
| SimClaim hardpair V2b | `scripts/simclaim_hardpair_v2b/` |
| SimClaim hardpair V3 | `scripts/simclaim_hardpair_v3/` |
| SimClaim hardpair V3b | `scripts/simclaim_hardpair_v3b/` |
| SimClaim hardpair V3 targeted | `scripts/simclaim_hardpair_v3_targeted/` |
| SimClaim detemplate V1 150 | `scripts/simclaim_detemplate_v1_150/` |
| SimClaim release candidate | `scripts/simclaim_release_candidate/` |

### 8. Other legacy / utility scripts

| Script | Notes |
|---|---|
| `scripts/clean_project_state_consolidation_v1.py` | Project state cleanup (legacy) |
| `scripts/run_project_state_consolidation_v1.py` | Project state consolidation (legacy) |
| `scripts/claim_realism_audit.py` | Claim realism audit (legacy) |
| `scripts/case_level_comparison.py` | Case-level comparison (legacy) |
| `scripts/build_gold_pilot_preparation_v1.py` | Gold pilot preparation (legacy) |
| `scripts/run_overnight_non_api_pipeline_v1.py` | Overnight pipeline (legacy) |

### 9. Scanner code (not a real path — string detection only)

| Script | Notes |
|---|---|
| `scripts/generate_project_status_report_v1.py` | Contains `D:\ocn` as a **string literal** in the hardcoded-path scanner. This is the scanner that detects hardcoding in other scripts; the literal is required for detection. Not a real hardcoded path. |

## Summary

| Category | Count | Status |
|---|---|---|
| V3.1–V3.16 docx/paper builders | 23 | legacy_exempt |
| V2 / mixed-framework | 7 | legacy_exempt |
| V3.15–V3.16 diagnostics | 10 | legacy_exempt |
| R4 recovery / replay | 4 | legacy_exempt (frozen artifacts) |
| LLM / API baselines | 4 | legacy_exempt (not mainline) |
| RIGOURATE-related | 5 | legacy_exempt |
| SimClaim scaffold / hardpair / detemplate | ~30 | legacy_exempt |
| Other legacy / utility | 6 | legacy_exempt |
| Scanner code (string literal) | 1 | safe (not a real path) |
| **Total exempt** | **~90** | |

## Enforcement

The V3.17 path-configurability requirement applies **only** to P0 mainline
scripts (listed in `configs/v3_17_paths.yaml` and scanned by
`scripts/audit_path_hardcoding_v1.py`). Scripts listed in this document are
excluded from the audit's `current_pipeline_blocker` classification.

If a legacy script is promoted to the V3.17 mainline in the future, it must
be refactored to use `config_utils` before it can be included in the
reproducibility claim.
