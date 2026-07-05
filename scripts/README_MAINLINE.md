# D:\ocn\scripts — Current Mainline Minimal Set

This directory holds the **current mainline minimal script set** for the CESE-OCN Mixed Framework V3.7 paper. It is **not** a complete historical code archive. Old / retired scripts live under `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_*\` (see `D:\ocn\_PROJECT_INDEX\script_archive_manifest.csv` for the old_path → archive_path mapping).

## What's Here

21 Python scripts + this README + `HOW_TO_REPRODUCE_MAINLINE.md`.

| Category | Count | Scripts |
|---|---|---|
| current_mainline | 16 | V3.4–V3.7 docx + main_paper + taxonomy_hardening + external_gold_llm_plan + paper_ready + gold_pilot + 6 run_* experiment/runner scripts |
| historical | 5 | `build_v3_1_docx.py`, `build_v3_2_docx.py`, `build_v3_2_table0_and_audit.py`, `build_v3_3_docx.py`, `build_v3_3_main_paper.py` |
| maintenance tools | 0 | Moved to `D:\ocn\_PROJECT_INDEX\tools\` (e.g. `build_script_cleanup_v1.py`) |

Full per-script metadata (purpose, input/output dependencies, safe_to_run, category, notes) is in `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv`.

## Rules

1. **Do not run API scripts.** `run_llm_judge_baseline_v1.py` and `run_gpt_structured_judge_probe_v1.py` cost real money (DeepSeek + GPT-5.5 via holysheep.ai proxy) and require explicit user authorization. Outputs from the last authorized run are already on disk — use those.
2. **Do not run experiment scripts.** `run_v3_r4_strong_baselines_holdout_v1.py`, `run_external_gold_scifact_vitaminc_v1.py`, `run_cese_ocn_lite_v3.py`, `run_mixed_framework_router_optimization_v2.py`, `run_mixed_framework_new_algorithm_sweep_v1.py` — R4 thresholds are frozen (`t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`, `t_low=lower guard`). Rerunning breaks reproducibility against the frozen paper numbers.
3. **Do not run result-pack or paper-content builders.** `build_paper_ready_mixed_framework_v2.py`, `build_v3_4_main_paper.py`, `build_v3_4_taxonomy_hardening.py`, `build_v3_external_gold_llm_plan_v1.py` — outputs already frozen; rerunning risks overwriting frozen artifacts.
4. **Historical scripts (V3.1, V3.2, V3.3 line) are kept for traceability only.** Do not use them unless reproducing old versions. Current paper is V3.7.
5. **Only 2 scripts are safe_to_run=yes:** `build_v3_7_docx.py` (regenerate V3.7 Word from markdown) and `build_gold_pilot_preparation_v1.py` (regenerate the 50-sample pilot pack from existing CSVs). For both, confirm the run will not overwrite manual edits before executing.
6. **Do not edit CSV data or fill gold labels.** `gold_label`, `final_label`, `human_audited` columns must remain empty until the independent gold pilot is adjudicated.
7. **Do not refactor.** Old scripts are intentionally not in this directory. If you need one, find it under `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_*\`.
8. **If unsure whether a script is mainline, do not promote it back to this directory without an explicit task.** The cleanup principle was "if unsure, archive, do not delete".

## Current Paper

- **Main draft:** V3.7 (Evidence Sufficiency Calibration main line).
- **Word path (canonical):** `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx`
- **Word path (root copy for advisor convenience):** `D:\ocn\CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`
- **Markdown source:** `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.md`
- **Curated mainline mirror:** `D:\ocn\_MAIN_PAPER_CURRENT\` (paper, scripts, data, experiments, root docx).

## How to Edit the Paper

**If you want to revise the paper text:**

1. Edit the markdown at `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.md`.
2. Regenerate the docx by running `python D:\ocn\scripts\build_v3_7_docx.py`.
3. Do NOT edit the docx directly — it is a generated artifact.
4. Do NOT run any other `build_v3_*` script — earlier versions are frozen.

## Where to Find Old Scripts

| You're looking for … | Look in |
|---|---|
| Temp probes / `_tmp_*` / `_v36_lookup*` | `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_temp\` |
| Old experiment runners (HCM, structured, escalation, simclaim_v4, hardpair, old baselines/ablations, toy, oracle, delexicalized, old sweeps) | `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_old_experiments\` |
| Old data pipeline (round1/round2, source_bank, merge_all92, old candidate pool / split / train-dev-test / release bundle builders) | `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_old_data_pipeline\` |
| Old annotation / release / audit (annotation, human pilot, old adjudication, candidate_588, old report/export) | `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_old_release_annotation\` |
| Pre-V3.x legacy (none currently, reserved) | `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_legacy\` |
| Maintenance / cleanup tools (e.g. `build_script_cleanup_v1.py`) | `D:\ocn\_PROJECT_INDEX\tools\` |

## Recommended Next Step

**Do the gold pilot, not new algorithms.**

The current paper's biggest scientific risk is the absence of independent gold adjudication. The gold pilot preparation pack is ready at `D:\ocn\gold_pilot_preparation_v1\` (50 candidates, two annotator templates, adjudication template, agreement statistics plan). The next step is human annotation + adjudication, then a taxonomy-revision decision based on per-boundary Cohen's κ.

New algorithms, new ablations, new LLM comparisons, and code refactoring are NOT the next step — they would not address the silver-label limitation that is the actual blocker for paper credibility.
