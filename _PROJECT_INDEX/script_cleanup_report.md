# Script Cleanup Report v1

Date: 2026-07-04
Operator: assistant (script_cleanup_v1)
Backup reference: `D:\ocn_backup_20260704_1606\`
Mainline mirror: `D:\ocn\_MAIN_PAPER_CURRENT\scripts\`

## 1. Scope

Reorganize `D:\ocn\scripts` so the root scripts directory only keeps the current V3.7 / gold pilot / R4 / LLM comparison / paper-ready scripts. All non-mainline scripts are moved (not deleted) to categorized archive subdirectories under `D:\ocn\_ARCHIVE_NON_MAINLINE\`.

This cleanup does NOT rewrite algorithm logic, run experiments, call APIs, train models, edit paper drafts, edit CSV data, or fill gold labels.

## 2. Before / After Counts

| Metric | Count |
|---|---|
| Scripts in `D:\ocn\scripts` BEFORE cleanup | 180 (179 original + 1 cleanup script) |
| Scripts in `D:\ocn\scripts` AFTER cleanup | 22 |
| Scripts archived | 158 |
| Archive subdirectories created | 5 |
| Files deleted | 0 |

## 3. Mainline Scripts Kept in `D:\ocn\scripts`

22 scripts, grouped by role:

### 3.1 Paper version builders (V3.x lineage, 12 scripts)
- `build_v3_1_docx.py`
- `build_v3_2_docx.py`
- `build_v3_2_table0_and_audit.py`
- `build_v3_3_docx.py`
- `build_v3_3_main_paper.py`
- `build_v3_4_docx.py`
- `build_v3_4_main_paper.py`
- `build_v3_4_taxonomy_hardening.py`
- `build_v3_5_docx.py`
- `build_v3_6_docx.py`
- `build_v3_7_docx.py`
- `build_v3_external_gold_llm_plan_v1.py`

### 3.2 Mainline experiments (5 scripts)
- `run_v3_r4_strong_baselines_holdout_v1.py`
- `run_llm_judge_baseline_v1.py`
- `run_gpt_structured_judge_probe_v1.py`
- `run_external_gold_scifact_vitaminc_v1.py`
- `run_cese_ocn_lite_v3.py`

### 3.3 Mainline result organization (3 scripts)
- `build_paper_ready_mixed_framework_v2.py`
- `run_mixed_framework_router_optimization_v2.py`
- `run_mixed_framework_new_algorithm_sweep_v1.py`

### 3.4 Gold pilot + cleanup audit (2 scripts)
- `build_gold_pilot_preparation_v1.py`
- `build_script_cleanup_v1.py`

## 4. Archive Layout

All archived scripts are under `D:\ocn\_ARCHIVE_NON_MAINLINE\`:

| Archive subdir | File count | Contents |
|---|---|---|
| `scripts_legacy\` | 0 | Reserved for legacy scripts that predate the V3.x line. Currently empty — no legacy scripts remained after categorization (all old scripts fit one of the four functional categories below). |
| `scripts_temp\` | 4 | Temporarily-named probes and lookup helpers (e.g. `_tmp_*`, `_v36_lookup*`, `_check_*`, `_verify_*`). |
| `scripts_old_experiments\` | 58 | Old experiment runners from retired lines (cese_ocn_hcm, cese_ocn_structured, escalation, evidence_aware, simclaim_v4, hardpair, old baselines, old ablations, toy, oracle, delexicalized, old strong sweep, old router sweep). |
| `scripts_old_data_pipeline\` | 30 | Old data pipeline scripts (round1/round2, source_bank, merge_all92, old candidate-pool builders, old split / train-dev-test generators, source triples, hard diagnostic dataset builders, release bundle builders). |
| `scripts_old_release_annotation\` | 66 | Old annotation / release / audit scripts (annotation, human pilot, release, old adjudication, import/validate annotations, candidate_588 related, old report/export packages). |
| **Total archived** | **158** | |

## 5. No-Deletion Declaration

- No script files were deleted during this cleanup.
- Every archived script is recoverable from `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_*\`.
- A complete archive manifest with old_path → archive_path mapping is in `D:\ocn\_PROJECT_INDEX\script_archive_manifest.csv` (158 entries + header).
- A complete mainline registry with purpose / dependencies / safe_to_run notes is in `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv` (22 entries + header).
- A full project backup predates this cleanup at `D:\ocn_backup_20260704_1606\`.

## 6. Should Old Scripts Be Refactored?

**Recommendation: Do NOT refactor old scripts.**

Reasons:

1. The old experiment/data/annotation scripts belong to retired project lines (HCM, structured, escalation, simclaim_v4, hardpair, round1/round2, candidate_588, etc.). Refactoring them would reopen frozen work and re-introduce risk into a paper that is already in the advisor-handoff stage.

2. The current paper (V3.7) and its immediate predecessors (V3.4–V3.6) depend only on the 22 mainline scripts kept in `D:\ocn\scripts`. Refactoring old scripts would not change any number in the current paper.

3. The remaining scientific risk for this project is independent gold pilot annotation — not code quality of archived scripts. Engineering effort should go to gold pilot adjudication and the resulting taxonomy revision, not to script refactoring.

4. Archived scripts are recoverable. If a future task genuinely requires reusing an old script, it can be pulled from `_ARCHIVE_NON_MAINLINE` on demand. Proactive refactoring would be speculative work.

5. Per the user's stated principle for this task: "不确定是否主线的脚本，归档，不删除" and "当前建议：不重构旧脚本，只维护主线最小脚本集".

**Action: Only maintain the mainline minimal script set. Do not refactor archived scripts.**

## 7. Final Verification (8 checks)

| # | Check | Result |
|---|---|---|
| 1 | `D:\ocn\scripts` file count reduced (180 → 22) | PASS |
| 2 | `D:\ocn\scripts` only contains mainline scripts + will contain README_MAINLINE.md and HOW_TO_REPRODUCE_MAINLINE.md | PASS |
| 3 | All old scripts findable in `D:\ocn\_ARCHIVE_NON_MAINLINE\scripts_*\` | PASS (158/158 in manifest) |
| 4 | `D:\ocn\_MAIN_PAPER_CURRENT\scripts\` still exists | PASS (22 .py files, synced) |
| 5 | V3.7 Word doc still exists | PASS (`D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx`, 25575 bytes; root copy `D:\ocn\CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`, 25575 bytes) |
| 6 | No files deleted | PASS (158 moved, 0 deleted) |
| 7 | No experiments / API / model training run | PASS (cleanup only moves files) |
| 8 | Project index has script manifests | PASS (`script_registry_mainline.csv`, `script_archive_manifest.csv`, this report) |

## 8. Files Produced by This Cleanup

| File | Path |
|---|---|
| Cleanup script | `D:\ocn\scripts\build_script_cleanup_v1.py` |
| Cleanup report (this file) | `D:\ocn\_PROJECT_INDEX\script_cleanup_report.md` |
| Mainline registry | `D:\ocn\_PROJECT_INDEX\script_registry_mainline.csv` |
| Archive manifest | `D:\ocn\_PROJECT_INDEX\script_archive_manifest.csv` |
| Scripts README | `D:\ocn\scripts\README_MAINLINE.md` |
| Reproduction guide | `D:\ocn\scripts\HOW_TO_REPRODUCE_MAINLINE.md` |

## 9. Prohibitions Honored

- No script deleted.
- No script logic modified.
- No rewrite to a new framework or package.
- No complex `run_all.py` CLI created.
- No experiments run.
- No API calls.
- No model training.
- No paper edits.
- No CSV data edits.
- No `gold_label` / `final_label` / `human_audited` written.
- `.venv`, `.github`, V3.7 paper directory, and `_MAIN_PAPER_CURRENT` not broken.
