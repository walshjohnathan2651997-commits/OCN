# Code Structure Re-Audit Report

**Date:** 2026-07-05
**Total scripts scanned:** 48

## Summary by category

| Category | Count | Examples |
|---|---|---|
| mainline | 8 | build_gold_pilot_preparation_v1.py, build_paper_ready_mixed_framework_v2.py, build_v2_relation_realism_templates.py |
| experiment | 16 | case_level_comparison.py, claim_realism_audit.py, compare_rigourate_style_vs_r4.py |
| build_docx | 17 | build_rigourate_style_scalar_baselines.py, build_v3_10_docx.py, build_v3_11_docx.py |
| audit | 4 | _v2_qc_check.py, _v3_15_scalar_gate_view.py, _v3_15_view_metrics.py |
| unknown | 3 | build_v3_10_1_docx.py, build_v3_12_1_docx.py, run_project_state_consolidation_v1.py |

## Safety summary

- **Safe to run:** 34 scripts (audit/view, reanalysis, docx builders, template generators)
- **Not safe to run (frozen):** 14 scripts (historical experiments with frozen results, frozen paper builders)
- **Calls API:** 2 scripts (run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1) — require user authorization + API key
- **Trains model:** 2 scripts (run_mixed_framework_router_optimization_v2, run_mixed_framework_new_algorithm_sweep_v1)

## Answers to required questions

### 1. Which scripts are currently mainline-usable?

The current mainline scripts are the V3.15 hierarchical taxonomy revision builders and the V3.16 integration summary builder:
- `scripts/build_v3_15_hierarchical_taxonomy.py` — builds V3.15 MD + DOCX from V3.14 source
- `scripts/build_v3_15_attack_response_and_gate.py` — generates attack response + readiness gate
- `scripts/check_v3_15_quality.py` — runs §12 quality checks
- `scripts/run_v3_16_integration_summary.py` — generates V3.16 five-task integration summary
- `scripts/run_overnight_non_api_pipeline_v1.py` — overnight non-API compute pipeline (reanalysis only)

These are all safe to run (no API, no gold, no original data modification).

### 2. Which scripts are only historical experiments?

All `run_*` scripts except the recent V3.15/overnight/V3.16 ones are historical experiments with frozen results:
- `run_cese_ocn_lite_v3.py` (R4 frozen baseline)
- `run_llm_judge_baseline_v1.py` (DeepSeek LLM baseline, requires API)
- `run_gpt_structured_judge_probe_v1.py` (GPT probe, requires API)
- `run_external_gold_scifact_vitaminc_v1.py` (external gold eval)
- `run_v3_r4_strong_baselines_holdout_v1.py` (strong baselines + holdout)
- `run_mixed_framework_router_optimization_v2.py` (router optimization, trains model)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (algorithm sweep, trains model)

These should NOT be rerun — their results are frozen and feed the paper.

### 3. Which scripts call API?

Two scripts require API keys + user authorization:
- `run_llm_judge_baseline_v1.py` (DeepSeek API)
- `run_gpt_structured_judge_probe_v1.py` (GPT API)

Per project memory: DeepSeek API is authorized for small-sample pilot ONLY (max 200 SimClaim pairs); key is held in conversation context only, NEVER stored. The prior "no LLM API" constraint still applies to all other tasks.

### 4. Which scripts retrain models?

Two scripts involve model training:
- `run_mixed_framework_router_optimization_v2.py` (router threshold optimization)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (algorithm sweep)

Both are frozen; do not rerun.

### 5. Which scripts only generate documents?

The `build_v*_docx.py` family (V3.1 through V3.14) plus `build_v3_15_hierarchical_taxonomy.py`, `build_v3_15_attack_response_and_gate.py`, `build_v3_4_main_paper.py`, `build_v3_3_main_paper.py`, `build_v3_4_taxonomy_hardening.py`, `build_v3_2_table0_and_audit.py`, `build_gold_pilot_preparation_v1.py`, `build_paper_ready_mixed_framework_v2.py`, `build_v3_external_gold_llm_plan_v1.py`, `build_v2_relation_realism_templates.py`, `build_rigourate_style_scalar_baselines.py`, `build_v3_13_rigourate_aware_docx.py`.

### 6. Is further refactoring needed?

**Not urgent.** The script directory is well-organized by version (build_vN_docx pattern) and by task (run_X, build_X, check_X, _X_view). The `_PROJECT_INDEX/script_registry_mainline.csv` is outdated (references V3.7 as current); it should be updated to reflect V3.15 as current, but this is a documentation task, not a refactoring task. No duplicate or dangerous scripts were found. The two API-calling scripts are clearly labeled and require authorization.

### 7. Are there duplicate or dangerous scripts?

**No dangerous scripts found.** All scripts write to their own output directories and do not modify original data. The `_v3_15_view_metrics.py`, `_v3_15_scalar_gate_view.py`, `_v2_qc_check.py` are view/check utilities (safe). No scripts delete files or overwrite old versions. The `check_v3_15_quality.py` is read-only.

**Mild redundancy:** `claim_realism_audit.py` (in scripts/) and `run_v3_15_claim_realism_audit.py` both relate to the realism audit, but the former is the implementation and the latter is the runner. This is acceptable modular design, not duplication.

## Outdated registry note

`_PROJECT_INDEX/script_registry_mainline.csv` lists 22 scripts and references V3.7 as current paper. The actual current paper is V3.15. The registry should be updated, but this does not affect script safety — the name-based classification above is authoritative.
