# How to Reproduce the Mainline Results

> **REALIGNMENT BANNER (2026-07-05):** The current selected main method is the **V3.17 baseline** offline PDF-corpus evidence-sufficiency screening pipeline. The V3.7 paper reproduction path below is retained as historical. For the authoritative V3.17 baseline reproduction path, see Section 0 below and `D:\ocn\project_synthesis\mainline_realignment_v1\updated_reproducibility_note.md`.

## 0. Current Selected Method — V3.17 Baseline Reproduction

The V3.17 baseline pipeline is:

```
PDF corpus → BM25 top-k retrieval → evidence canonicalization (best_sentence_top5_overlap)
  → restored R4 screening (10 seeds [11,22,33,44,55,66,77,88,99,111], per-seed thresholds, majority vote, prefer test split)
  → risk ranking (G_conservative_precision) → second-stage review queue (top-100)
```

**Frozen V3.17 baseline metrics:** strong_F1=0.4503, strong_recall=0.7064, P@20=0.45, R@100=0.3303, FP/TP@5%=11.24, second-stage viable=true.

**Per-seed R4 thresholds (example seed_11):** `t_contra=0.4`, `t_contra_low=0.35`, `t_strong=0.55`, `t_svm=0.55`. Frozen reference thresholds: `t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`. Do not refit.

**R4 artifacts:** `D:\ocn\experiments\r4_minimal_recovery_v1\artifacts\seed_*\` (classifier.joblib, scaler.joblib, thresholds.json, feature_columns.json, label_mapping.json).

**V3.17 baseline replay (if needed):**
```
python D:\ocn\scripts\run_canonicalized_review_queue_v1.py
python D:\ocn\scripts\run_canonicalized_risk_ranking_v1.py
```

**V3.18 exploratory negative ablation replay (if needed):**
```
python D:\ocn\scripts\run_v3_18_intelligent_upgrade_v1.py
```

---

## Historical V3.7 Paper Reproduction (Retained for Traceability)

This file lists the canonical paths and the minimum set of scripts needed to reproduce or rebuild the historical CESE-OCN V3.7 paper artifacts. V3.7 is NOT the current selected method.

## 0. Important: Full Reproduction Is NOT Recommended

A full from-scratch reproduction is **NOT recommended**. Reasons:

1. **API results are frozen.** DeepSeek-V3 LLM judge baseline (200 samples) and GPT-5.5 standard/structured probe (100 samples each) outputs are on disk. Rerunning these scripts costs real money and requires explicit user authorization.
2. **R4 results are frozen.** Router optimization, strong baselines, holdout validations, and algorithm sweep outputs are on disk. R4 thresholds (`t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`, `t_low=lower guard`) are frozen. Rerunning breaks reproducibility against the frozen paper numbers.
3. **LLM calls cost money.** DeepSeek + GPT-5.5 (via holysheep.ai proxy) are paid APIs.
4. **Reruns may cause version differences.** Model/API/library versions may have drifted since the frozen runs; reruns could produce slightly different numbers, requiring re-explanation in the paper.

The recommended path is to **reuse existing experiment outputs** and only regenerate the docx when the paper text changes.

## 1. Current Paper Main Draft

- **Word (canonical):** `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx`
- **Word (root copy):** `D:\ocn\CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`
- **Markdown source:** `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.md`
- **Curated mainline mirror:** `D:\ocn\_MAIN_PAPER_CURRENT\`

## 2. Current Main Data

- **Strict silver source of truth:** `D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv` (444 pairs, 111 evidence groups, 6 domains; silver labels, NOT gold).
- **High-risk boundary bank:** `D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\high_risk_sample_bank.csv` (25 cases, HRC_001–025).
- **Trusted illustrative case bank:** `D:\ocn\paper_versions_ordered\V3_4_taxonomy_hardened\trusted_case_bank.csv` (18 cases, TCB_001–018).
- **External gold (SciFact + VitaminC):** `D:\ocn\data\external_gold\scifact\` and `D:\ocn\data\external_gold\vitaminc\`.

## 3. Current R4 Results (Frozen — Do Not Rerun)

- **Frozen R4 router optimization:** `D:\ocn\experiments\mixed_framework_router_optimization_v2\`
- **Frozen R4 main results (paper_ready):** `D:\ocn\experiments\paper_ready_mixed_framework_v2\`
  - `paper_ready_summary.json`, `paper_ready_gate.json`, `table_1_main_results.csv`, …, `table_6_error_transition.csv`, `paper_result_interpretation.md`.
- **Strong baselines + holdout validation:** `D:\ocn\experiments\v3_r4_strong_baselines_holdout_v1\`
  - `strong_baseline_results_by_seed.csv`, `domain_holdout_results.csv`, `source_holdout_results.csv`, `validation_readiness_gate.json`.

Frozen R4 thresholds: `t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`, `t_low=lower guard`. Do not refit.

## 4. Current LLM Baseline Results (Frozen — Do Not Rerun)

- **DeepSeek-V3 LLM judge baseline (200 samples):** `D:\ocn\experiments\llm_judge_baseline_v1\`
  - `llm_raw_outputs_200.jsonl`, `llm_parsed_outputs_200.csv`, `llm_run_gate_200.json`.
- **GPT-5.5 standard vs structured probe (100 samples each):** `D:\ocn\experiments\gpt_structured_judge_probe_v1\`
  - 13 files including `gpt_standard_metrics_100.json`, `gpt_structured_metrics_100.json`, `gpt_structured_probe_gate.json`.
- **External gold eval (SciFact + VitaminC):** `D:\ocn\experiments\external_gold_scifact_vitaminc_v1\`
  - 14 files including `external_gold_results_summary.json`, `readiness_gate.json`.

## 5. Current Gold Pilot Preparation Pack

- **Pack root:** `D:\ocn\gold_pilot_preparation_v1\`
  - `gold_pilot_candidate_50.csv` (50 samples: 25 high-risk + 16 trusted + 9 random).
  - `gold_pilot_annotation_guideline.md`.
  - `annotator_A_template.csv`, `annotator_B_template.csv` (label columns empty).
  - `adjudication_template.csv` (adjudicated_label empty).
  - `gold_pilot_sampling_report.md`, `agreement_statistics_plan.md`, `gold_pilot_readme_for_annotators.md`.

The pilot is NOT yet annotated. `gold_label`, `final_label`, `human_audited` are empty by design.

## 6. Recommended Reproduction Path

**Step 1 — Use existing experiment outputs.**

All paper numbers come from frozen outputs in `D:\ocn\experiments\`. Do not rerun. If a number is questioned, look it up in the corresponding `*_summary.json` or `*.csv` under the experiment directory.

**Step 2 — Use V3.7 markdown + docx as the paper source of truth.**

- Read: `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.md`
- Word: `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx`

**Step 3 — If you need to regenerate the Word doc, run ONLY `build_v3_7_docx.py`.**

```
python D:\ocn\scripts\build_v3_7_docx.py
```

- Builder uses `zipfile + XML` (python-docx is unavailable in this environment due to SSL).
- Input: `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.md`.
- Output: `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx`.
- **Before running:** confirm the run will not overwrite manual edits made to the docx. If the docx has manual edits, back it up first.

**Step 4 — If you need the gold pilot, use the existing pack files only.**

- Read: `D:\ocn\gold_pilot_preparation_v1\`
- If the pack needs regenerating (e.g. sample selection criteria changed), run `python D:\ocn\scripts\build_gold_pilot_preparation_v1.py`. **Before running:** confirm the run will not overwrite manual annotations in `annotator_A_template.csv` / `annotator_B_template.csv` / `adjudication_template.csv`.

**Step 5 — Do NOT rerun API or model scripts.**

The following are `safe_to_run = no` and should not be executed unless a new task explicitly authorizes it:

- `run_llm_judge_baseline_v1.py` (DeepSeek API, costs money)
- `run_gpt_structured_judge_probe_v1.py` (GPT-5.5 API, costs money)
- `run_external_gold_scifact_vitaminc_v1.py` (large download + NLI inference)
- `run_v3_r4_strong_baselines_holdout_v1.py` (frozen R4 results)
- `run_cese_ocn_lite_v3.py` (frozen R4 router)
- `run_mixed_framework_router_optimization_v2.py` (frozen thresholds)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (frozen sweep)

## 7. Old Experiment Results Are Frozen

All old experiment results (HCM, structured, escalation, simclaim_v4, hardpair, round1/round2, candidate_588, old sweeps, old ablations) are archived under `D:\ocn\_ARCHIVE_NON_MAINLINE\` and are NOT part of the V3.7 paper. They are kept for traceability only. Do not re-execute archived scripts.

If an archived result is genuinely needed (e.g. a reviewer asks about an old ablation), pull the script from `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_old_experiments\` using `D:\ocn\_PROJECT_INDEX\script_archive_manifest.csv` to find its old path, and run it in isolation — do not promote it back to `D:\ocn\scripts\`.

## 8. Quick Reference: Script Roles

| Script | Category | Safe to run? |
|---|---|---|
| `build_v3_7_docx.py` | current_mainline | YES (confirm no overwrite of manual docx edits) |
| `build_gold_pilot_preparation_v1.py` | current_mainline | YES (confirm no overwrite of manual annotations) |
| `build_v3_6_docx.py` / `build_v3_5_docx.py` / `build_v3_4_docx.py` | current_mainline (revision chain) | NO — frozen |
| `build_v3_4_main_paper.py` / `build_v3_4_taxonomy_hardening.py` / `build_v3_external_gold_llm_plan_v1.py` | current_mainline | NO — frozen |
| `build_paper_ready_mixed_framework_v2.py` | current_mainline | NO — frozen |
| `run_v3_r4_strong_baselines_holdout_v1.py` | current_mainline | NO — frozen, do not rerun |
| `run_llm_judge_baseline_v1.py` | current_mainline | NO — API, costs money, requires authorization |
| `run_gpt_structured_judge_probe_v1.py` | current_mainline | NO — API, costs money, requires authorization |
| `run_external_gold_scifact_vitaminc_v1.py` | current_mainline | NO — large download + inference |
| `run_cese_ocn_lite_v3.py` | current_mainline | NO — frozen R4 router |
| `run_mixed_framework_router_optimization_v2.py` | current_mainline | NO — frozen thresholds |
| `run_mixed_framework_new_algorithm_sweep_v1.py` | current_mainline | NO — frozen |
| `build_v3_1_docx.py` / `build_v3_2_docx.py` / `build_v3_2_table0_and_audit.py` / `build_v3_3_docx.py` / `build_v3_3_main_paper.py` | historical | NO — historical only; current paper is V3.7 |

Full per-script metadata: `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv`.
