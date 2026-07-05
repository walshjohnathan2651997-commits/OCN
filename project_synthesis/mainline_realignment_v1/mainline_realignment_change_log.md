# Mainline Realignment Change Log v1

**Date:** 2026-07-05
**Task:** Project Records Realignment to Current Mainline v1
**Output directory:** `D:\ocn\project_synthesis\mainline_realignment_v1\`

---

## 1. Realignment Summary

This change log records all updates made to project records, indexes, and documentation to align the "mainline expression" with the current direction: the **offline PDF-corpus evidence-sufficiency screening framework** with **V3.17 baseline** as the selected method and **V3.18 intelligent upgrade** as an exploratory negative ablation.

**Constraints enforced:**
- No experiment data modified
- No experiments rerun
- No paper body modified (paper_versions_ordered is read-only)
- No files deleted
- Only project records / indexes / docs updated

---

## 2. Files Updated (Project Records)

### 2.1 `D:\ocn\scripts\README_MAINLINE.md`

**Before:** Stated V3.7 is the current paper, listed V3.7 docx as the canonical Word manuscript, recommended "do the gold pilot, not new algorithms" as the next step.

**After:** Reframed to state the current mainline is V3.17 baseline (offline PDF-corpus screening). V3.7 retained as historical advisor-handoff draft. Recommended next steps updated to: evidence-force contrastive, local LLM pilot, gold adjudication. Added a realignment banner pointing to `mainline_realignment_v1/`.

### 2.2 `D:\ocn\scripts\HOW_TO_REPRODUCE_MAINLINE.md`

**Before:** Reproduction path was V3.7-only (regenerate docx via `build_v3_7_docx.py`). R4 thresholds listed only as frozen reference values.

**After:** Added V3.17 baseline reproduction path (PDF → BM25 → canonicalization → R4 → ranking → review queue). Added per-seed R4 thresholds (seed_11 example). Added R4 artifacts location. Added V3.18 intelligent upgrade replay instructions. V3.7 reproduction retained as historical. Added realignment banner.

### 2.3 `D:\ocn\_PROJECT_INDEX\current_paper_paths.md`

**Before:** Header "Current Paper Paths — Top 5", dated 2026-07-04, Version: V3.7.

**After:** Relabeled as "Historical Advisor-Handoff Paths (V3.7)" with a realignment banner pointing to the current V3.17 baseline mainline. Original V3.7 paths retained for traceability.

### 2.4 `D:\ocn\_PROJECT_INDEX\mainline_file_manifest.csv`

**Before:** Manifest listed V3.7 docx as "Latest Word manuscript for advisor review" and `mixed_framework_v2_frozen_r4_baseline` as the main R4 result.

**After:** Added V3.17 baseline entries (`canonicalized_review_queue_v1`, `r4_evidence_canonicalization_v1`, `canonicalized_risk_ranking_v1`, `v3_18_intelligent_upgrade_v1`). Marked V3.7 docx as historical advisor-handoff artifact. Marked `mixed_framework_v2_frozen_r4_baseline` as historical (current mainline uses restored R4 per-seed thresholds).

### 2.5 `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv`

**Before:** Registry listed 16 current_mainline scripts anchored on V3.7 paper build chain.

**After:** Added V3.17 baseline scripts (`run_canonicalized_review_queue_v1.py`, `run_r4_evidence_canonicalization_v1.py`, `run_canonicalized_risk_ranking_v1.py`, `run_v3_18_intelligent_upgrade_v1.py`) as current_mainline. V3.x docx builders retained as historical. Added realignment note column.

### 2.6 `D:\ocn\_PROJECT_INDEX\project_cleanup_report.md`

**Before:** Referenced V3.7 as current paper.

**After:** Added realignment note at top pointing to `mainline_realignment_v1/`.

### 2.7 `D:\ocn\_PROJECT_INDEX\script_second_pass_cleanup_note.md`

**Before:** Referenced V3.7 as current paper.

**After:** Added realignment note pointing to `mainline_realignment_v1/`.

### 2.8 `D:\ocn\_PROJECT_INDEX\script_cleanup_report.md`

**Before:** Referenced V3.7 as current paper.

**After:** Added realignment note pointing to `mainline_realignment_v1/`.

### 2.9 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\current_mainline_assessment.md`

**Before:** Stated "CESE-OCN R4: a relation-specific screening router under the hierarchical diagnostic taxonomy" as the current mainline, with V3.15 hierarchical taxonomy revision as the basis. Positioned §VII gold pilot as the single most decisive next action.

**After:** Reframed current mainline as V3.17 baseline offline PDF-corpus evidence-sufficiency screening. V3.15 hierarchical taxonomy retained as paper-level interpretation only. Updated basis to V3.17 baseline + V3.18 negative result. Repositioned gold pilot as a future credibility step (not the current mainline direction). Added realignment banner.

### 2.10 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\allowed_vs_forbidden_claims_current.md`

**Before:** Allowed/forbidden list anchored on V3.15 hierarchical taxonomy. Missing V3.17 baseline and V3.18 negative ablation positioning.

**After:** Added allowed claims A1–A9 (PDF retrieval feasible, raw chunks degrade, canonicalization restores, overlap robust, R4 second-stage, V3.17 selected, SimClaim diagnostic, R4 macro_F1 < LLM, V3.18 negative ablation). Added forbidden claims F1–F10 (R4 beats LLM overall, gold validated, natural prevalence, full automatic review, standalone detector, learned improves main, raw BM25 solves screening, model fully understands, RIGOURATE reproduced, first benchmark). Retained V3.15-era claims that are still valid with minor wording updates. Added realignment banner.

### 2.11 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\current_project_state_master_report.md`

**Before:** Master report anchored on V3.7/V3.15/V3.16 hierarchical taxonomy mainline.

**After:** Added realignment section at top pointing to `mainline_realignment_v1/updated_project_mainline_summary.md` as the authoritative current mainline. Original content retained for traceability.

### 2.12 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\gate_synthesis_report.md`

**Before:** Gate synthesis anchored on V3.15/V3.16 hierarchical taxonomy gates.

**After:** Added realignment note: V3.17 baseline + V3.18 gates are the current authoritative gates. Original content retained.

### 2.13 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\paper_version_lineage_report.md`

**Before:** Lineage report listed V3.7 as the current paper version.

**After:** Updated to mark V3.7 as historical advisor-handoff draft. Current selected method is V3.17 baseline (not a paper version per se). V3.18 is exploratory negative ablation. Added realignment note.

### 2.14 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\paper_version_inventory.csv`

**Before:** Inventory listed V3.7 as the latest/current paper version.

**After:** Added note column: V3.7 is historical; current selected mainline method is V3.17 baseline (offline PDF-corpus screening).

### 2.15 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\experiment_result_synthesis.md`

**Before:** Synthesis did not include V3.17 baseline or V3.18 intelligent upgrade results.

**After:** Added V3.17 baseline entry (strong_F1=0.4503, P@20=0.45, R@100=0.3303, FP/TP@5%=11.24) and V3.18 negative result entry (selector strong_F1=0.4444, ranker P@20=0.35, FP/TP@5%=2.00, supports_v3_18=false). Added realignment note.

### 2.16 `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\current_project_state_gate.json`

**Before:** Gate did not reference V3.17 baseline or evidence canonicalization as mainline.

**After:** Added realignment fields: `current_mainline`, `selected_method_version`, `deprecated_versions`, `realignment_doc`, `paper_body_modified=false`, `experiments_modified=false`.

---

## 3. Files NOT Edited — Historical Status Notes

The following files were scanned and found to contain stale mainline references, but were NOT edited because they are historical records, historical experiment reports, or read-only paper body. Their historical status is documented here.

### 3.1 Historical project_synthesis consolidation (superseded)

- `project_synthesis/current_project_state_consolidation_v1/*` — older consolidation (non-clean), superseded by `current_project_state_consolidation_clean_v1` and now by `mainline_realignment_v1`. **Historical status:** Retained as-is for traceability; do not use as the current mainline reference.

### 3.2 Historical V3.16 revision plans

- `project_synthesis/v3_16_integration_summary_and_revision_plan/*` — V3.16 integration summary. **Historical status:** Superseded by V3.17 baseline selection; retained as-is.
- `project_synthesis/no_gold_evidence_integration_v3_16_plan/*` — V3.16 no-gold integration plan. **Historical status:** Superseded; retained as-is.
- `project_synthesis/no_gold_rigourate_public_benchmark_pipeline_v1/*` — no-gold RIGOURATE pipeline. **Historical status:** Historical; retained as-is.

### 3.3 Already-aligned experiments (no edit required)

- `experiments/v3_18_intelligent_upgrade_v1/*` — V3.18 gate already states `supports_v3_18_intelligent_upgrade=false` and `best_overall_method=V3.17_baseline`. **Status:** Already aligned; no edit required.
- `experiments/canonicalized_review_queue_v1/*` — gate already states `supports_v3_17_mainline` and `second_stage_viable=true`. **Status:** Already aligned.
- `experiments/r4_evidence_canonicalization_v1/*` — gate already states `supports_v3_17_mainline=true` and `supports_pdf_corpus_screening_claim=true`. **Status:** Already aligned.
- `experiments/canonicalized_risk_ranking_v1/*` — gate already states `best_variant=G_conservative_precision` and `low_prevalence_second_stage_usable=true`. **Status:** Already aligned.
- `project_synthesis/local_llm_baseline_feasibility_note_v1/*` — already positions local LLM baseline as future work, not completed. **Status:** Already aligned.

### 3.4 Historical diagnostic experiments (no edit required)

- `experiments/overnight_non_api_compute_pipeline_v1/*` — overnight pipeline Tasks A–H. **Historical status:** Results remain valid as supporting evidence; the overnight-pipeline framing is superseded by the V3.17 baseline mainline.
- `experiments/v3_15_scalar_vs_relation_screening_deep_test/*` — V3.15 deep test. **Historical status:** Retained as-is.
- `experiments/v3_15_claim_realism_audit/*` — V3.15 realism audit. **Historical status:** Retained as-is.
- `experiments/v3_15_low_prevalence_screening_simulation/*` — V3.15 low-prevalence simulation. **Historical status:** Retained as-is.
- `experiments/v3_11_three_core_credibility_experiments/*` — V3.11 credibility experiments. **Historical status:** Retained as-is.
- `experiments/v3_11_non_gold_robustness_stress_test/*` — V3.11 robustness stress test. **Historical status:** Retained as-is.
- `experiments/rigourate_reproduction_and_simclaim_baseline_v1/*` — RIGOURATE reproduction. **Historical status:** Retained as-is.
- `experiments/strict_silver_max_v1/*` and `experiments/strict_silver_max_v1_binary_decomposition/*` — historical strict silver. **Historical status:** Retained as-is.
- `experiments/gpt_structured_judge_probe_v1/*` — historical GPT probe. **Historical status:** Retained as-is.
- `experiments/llm_judge_baseline_v1/*` — historical LLM baseline. **Historical status:** Retained as-is.
- `experiments/external_gold_scifact_vitaminc_v1/*` — historical external gold. **Historical status:** Retained as-is.
- `experiments/v3_external_gold_llm_plan_v1/*` — historical external gold LLM plan. **Historical status:** Retained as-is.
- `experiments/v3_r4_strong_baselines_holdout_v1/*` — historical strong baselines holdout. **Historical status:** Retained as-is.
- `experiments/paper_ready_mixed_framework_v2/*` — historical paper-ready pack. **Historical status:** Retained as-is.
- `experiments/mixed_framework_new_algorithm_sweep_v1/*` — historical algorithm sweep. **Historical status:** Retained as-is.
- `experiments/mixed_framework_v2_frozen_r4_baseline/*` — historical frozen R4 baseline using frozen reference thresholds. **Historical status:** Current mainline uses restored R4 (per-seed thresholds) via `canonicalized_review_queue_v1`; this directory is retained as historical.
- `experiments/mixed_framework_router_optimization_v2/*` — historical router optimization. **Historical status:** Retained as-is.
- `experiments/canonical_selector_robustness_v1/*` — historical selector robustness. **Historical status:** Retained as-is.
- `experiments/r4_retrieved_replay_v1/*` — historical R4 retrieved replay. **Historical status:** Retained as-is.
- `experiments/r4_minimal_recovery_v1/*` — historical R4 minimal recovery; R4 artifacts still used by V3.17 baseline replay. **Historical status:** Report retained as-is; artifacts remain in use.
- `experiments/r4_backup_asset_search_v1/*` — historical R4 backup search. **Historical status:** Retained as-is.
- `experiments/r4_on_retrieved_evidence_v1/*` — historical R4 on retrieved evidence. **Historical status:** Retained as-is.
- `experiments/simclaim_pdf_corpus_retrieval_v1/*` — historical SimClaim PDF retrieval. **Historical status:** Retained as-is.

### 3.5 Read-only paper body (NOT modified)

- `paper_versions_ordered/VERSION_INDEX.md` — recommends V3 as the current working manuscript. **Read-only:** Documented as historical; current selected method is V3.17 baseline (offline PDF-corpus screening), not the V3 paper mainline.
- `paper_versions_ordered/V3_16_no_gold_evidence_integration/*` — V3.16 paper body and gates. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_15_hierarchical_taxonomy_revision/*` — V3.15 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_14_mainline_locked_consistency_audit/*` — V3.14 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_13_*` — V3.13 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_12_*` — V3.12 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_11_*` — V3.11 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_10_*` — V3.10 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_9_*` — V3.9 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_8_*` — V3.8 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_7_advisor_handoff_clean/*` — V3.7 paper body (cited as current paper in older mainline docs). **Read-only:** V3.7 is historical advisor-handoff draft, not current mainline.
- `paper_versions_ordered/V3_6_*` — V3.6 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_5_*` — V3.5 paper body. **Read-only:** Documented as historical.
- `paper_versions_ordered/V3_4_taxonomy_hardened/*` — V3.4 paper body; `high_risk_sample_bank.csv` and `trusted_case_bank.csv` retained as reference data. **Read-only:** Documented as historical.
- `_MAIN_PAPER_CURRENT/paper_versions/*` — curated mirror of historical paper. **Read-only:** Documented as historical.
- `docs/rigourate_reproduction_and_simclaim_baseline_v1/*` — historical docs. **Read-only:** Documented as historical.

### 3.6 Historical archive manifests (no edit required)

- `_PROJECT_INDEX/archived_file_manifest.csv` — historical archive manifest. **Status:** Retained as-is.
- `_PROJECT_INDEX/script_archive_manifest.csv` — historical archive manifest. **Status:** Retained as-is.
- `_PROJECT_INDEX/tools/*` — historical tools. **Status:** Retained as-is.

---

## 4. Files NOT Modified (Hard Constraints)

- **Paper body:** No file under `paper_versions_ordered/` was modified. `paper_body_modified = false`.
- **Experiment data:** No file under `experiments/*/` data files was modified. `experiments_modified = false`.
- **No files deleted.**
- **No experiments rerun.**
- **No API calls.**
- **No network access.**

---

## 5. Stale Claims Found

Total stale claims audited: **182** across **174** distinct files (see `stale_claims_audit.csv`).

Breakdown by risk level:
- **High risk:** 13 (V3.7 cited as current paper, hierarchical taxonomy cited as primary mainline, missing V3.17/V3.18 positioning in canonical docs)
- **Medium risk:** 21 (V3.15/V3.16 cited as basis, gold pilot positioned as decisive next step, historical frozen R4 baseline cited as main R4 result)
- **Low risk:** 148 (historical references in archived/superseded files, already-aligned experiments, read-only paper body)

Breakdown by `should_edit`:
- `should_edit = yes`: 24 rows across **16 distinct files** (all 16 files updated in Section 2 above)
- `should_edit = no`: 158 rows across 158 distinct files (documented as historical in Section 3 above)

Stale claims remaining after realignment: **0 high-risk stale claims in active project records**. All 16 distinct `should_edit = yes` files were updated with realignment banners. The 158 `should_edit = no` rows are either already-aligned, historical, or read-only paper body — they are documented as historical and do not require editing.

---

## 6. Authoritative Realignment Outputs

| File | Purpose |
|---|---|
| `mainline_realignment_inventory.csv` | Full inventory of scanned files with action taken |
| `stale_claims_audit.csv` | 119 stale claims with file_path, risk_level, replacement, should_edit |
| `updated_project_mainline_summary.md` | New canonical mainline summary (V3.17 baseline + V3.18 negative ablation) |
| `updated_allowed_forbidden_claims.md` | New allowed/forbidden claims list (A1–A9 allowed, F1–F10 forbidden) |
| `updated_reproducibility_note.md` | New reproducibility note (V3.17 baseline reproduction path) |
| `mainline_realignment_change_log.md` | This file |
| `mainline_realignment_gate.json` | Final realignment gate |

---

## 7. Confirmation

- **Paper body modified:** false
- **Experiments modified:** false
- **Files deleted:** 0
- **Experiments rerun:** 0
- **API calls:** 0
- **Network access:** 0
- **All `should_edit = yes` stale claims addressed:** true
- **Historical records preserved:** true
