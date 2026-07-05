# Project Cleanup Report — D:\ocn

> **REALIGNMENT BANNER (2026-07-05):** This cleanup report was written when V3.7 was treated as the current paper. The current mainline is now the **V3.17 baseline** offline PDF-corpus evidence-sufficiency screening pipeline. V3.7 is a historical advisor-handoff draft. See `D:\ocn\project_synthesis\mainline_realignment_v1\` for the authoritative realignment docs. The cleanup operations described below remain valid; only the "current paper = V3.7" framing is superseded.

**Date:** 2026-07-04
**Operation:** Full backup + mainline reorganization + archive
**Operator:** TRAE agent (automated)
**Status:** Complete

---

## 1. Backup

- **Backup directory:** `D:\ocn_backup_20260704_1606\`
- **Backup method:** robocopy /E (full recursive copy)
- **Original file count:** 43,898
- **Backup file count:** 43,898 (exact match)
- **Key directories verified in backup:** paper_versions_ordered, experiments, data, scripts, docs (all present)
- **Original D:\ocn not deleted:** Confirmed. Original directory remains in place; backup is a separate copy.

## 2. Reorganization structure

Three new directories created in D:\ocn:

| Directory | Purpose |
|---|---|
| `_MAIN_PAPER_CURRENT\` | Curated copies of the current mainline paper, experiments, data, and scripts for quick access. |
| `_ARCHIVE_NON_MAINLINE\` | Moved (not deleted) non-mainline content: old paper versions, old experiments, old data, old docs, old root-level files/dirs. Preserves original structure within archive. |
| `_PROJECT_INDEX\` | This report + manifests + key path list. |

## 3. Mainline directory (kept in root)

After cleanup, the D:\ocn root contains only mainline-relevant content:

```
D:\ocn\
├── .github\                          (infrastructure, kept)
├── .venv\                            (infrastructure, kept)
├── data\                             (2 mainline dirs: simclaim_all92_candidate_pool_v1, external_gold)
├── docs\                             (22 mainline doc items)
├── experiments\                      (11 mainline experiment dirs + 1 summary md)
├── gold_pilot_preparation_v1\        (next-step gold pilot prep, mainline-adjacent)
├── paper_versions_ordered\           (4 mainline versions: V3_4, V3_5, V3_6, V3_7 + VERSION_INDEX.md)
├── scripts\                          (all scripts kept for reference; 16 mainline scripts also copied to _MAIN_PAPER_CURRENT)
├── tests\                            (kept)
├── _ARCHIVE_NON_MAINLINE\            (archived content, see §4)
├── _MAIN_PAPER_CURRENT\              (curated mainline copies, see §5)
├── _PROJECT_INDEX\                   (this report + manifests)
├── .gitignore
├── CESE_OCN_CURRENT_ADVISOR_REVIEW.docx  (copy of V3.7 docx)
├── pytest.ini
├── README.md
└── requirements.txt
```

## 4. Archive directory

**Path:** `D:\ocn\_ARCHIVE_NON_MAINLINE\`

Contents (moved from original locations, structure preserved):

| Archive subdirectory | Contents | Source |
|---|---|---|
| `paper_versions_ordered\` | 7 old paper versions: V1_original_OCN, V2_evidence_aware_hierarchical, V3_1_evidence_sufficiency_llm_blindspot, V3_1_evidence_sufficiency_llm_blindspot_review, V3_2_p0_repaired_evidence_sufficiency, V3_3_reviewer_defense_polished, V3_mixed_framework_v2_R4 | D:\ocn\paper_versions_ordered\ |
| `experiments\` | 42 old experiment directories (cese_ocn_hcm_v1, escalation_focused_pilot_v1, simclaim_hardpair_v2/v3/v4 variants, simclaim_v4 variants, llm_baseline_v1_150, formal_baseline_v1_150, etc.) | D:\ocn\experiments\ |
| `data\` | 42 old data directories (adversarial_splits, clean_v2_split, control_splits, hard_diagnostic, human_pilot, legacy_dev, simclaim_detemplate_v1_150, simclaim_hardpair_v2/v3/v4 variants, simclaim_mvp_*, simclaim_release_candidate_v1, simclaim_v4_*, source_bank, templates, toy, etc.) | D:\ocn\data\ |
| `docs\` | 10 old doc subdirectories (cese_ocn_hcm_v1, cese_ocn_lite_v3, cese_ocn_mixed_framework_v1, cese_ocn_structured_v1, evidence_conditioned_update_v1, simclaim_v4_evidence_necessity, simclaim_v4_nonpaper_prototype, simclaim_v4_protocol_freeze, simclaim_v4_source_genre_pilot, strong_action_broad_sweep_v2) | D:\ocn\docs\ |
| `root_files\` | 12 old root-level files (audit_paper_consistency.py, candidate_588_*.csv/.rg.txt/.md, CESE_OCN_submit_ready_controlled_diagnostic.docx, GPT_QUICKSTART.md, last_q2_clean_copy_path.txt, rewrite_paper_to_rq.py) | D:\ocn\ (root) |
| `cese\` | Old CESE code | D:\ocn\cese\ |
| `configs\` | Old config files | D:\ocn\configs\ |
| `handoff_from_chatgpt\` | Old ChatGPT handoff materials | D:\ocn\handoff_from_chatgpt\ |
| `handoff_from_chatgpt_all92\` | Old ChatGPT handoff (all92) | D:\ocn\handoff_from_chatgpt_all92\ |
| `handoff_to_chatgpt\` | Old ChatGPT handoff (outbound) | D:\ocn\handoff_to_chatgpt\ |
| `paper_assets\` | Old paper assets | D:\ocn\paper_assets\ |
| `paper_draft_materials_v1\` | Old draft materials | D:\ocn\paper_draft_materials_v1\ |
| `paper_manuscript_v0\` | Old manuscript v0 | D:\ocn\paper_manuscript_v0\ |
| `release_simclaim_human_pilot\` | Old release package | D:\ocn\release_simclaim_human_pilot\ |
| `reports\` | Old reports | D:\ocn\reports\ |
| `schemas\` | Old schemas | D:\ocn\schemas\ |
| `_archive_docx_versions\` | Previously archived docx versions | D:\ocn\_archive_docx_versions\ |

## 5. Mainline current directory

**Path:** `D:\ocn\_MAIN_PAPER_CURRENT\`

Contents (curated copies for quick advisor-handoff access):

```
_MAIN_PAPER_CURRENT\
├── CESE_OCN_CURRENT_ADVISOR_REVIEW.docx   (copy of V3.7 docx)
├── paper_versions\
│   ├── V3_4_taxonomy_hardened\            (copy)
│   ├── V3_5_presentation_ready\           (copy)
│   ├── V3_6_case_figure_integrity_checked\ (copy)
│   └── V3_7_advisor_handoff_clean\        (copy, current final)
├── experiments\
│   ├── external_gold_scifact_vitaminc_v1\ (copy)
│   ├── gpt_structured_judge_probe_v1\     (copy)
│   ├── llm_judge_baseline_v1\             (copy)
│   ├── mixed_framework_v2_frozen_r4_baseline\ (copy)
│   └── paper_ready_mixed_framework_v2\    (copy)
├── data\
│   └── strict_silver_max_v1\              (copy of main silver-label data)
└── scripts\
    └── 16 mainline scripts (build_v3_*_docx.py, run_*_v1.py, etc.)
```

## 6. Latest Word manuscript

- **Root copy:** `D:\ocn\CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`
- **Mainline copy:** `D:\ocn\_MAIN_PAPER_CURRENT\CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`
- **Source:** `D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\CESE_OCN_V3_7_advisor_handoff_clean.docx` (unchanged)
- **Content:** Not modified. Byte-for-byte copy.

## 7. No-deletion declaration

I confirm that:
- **No files were deleted** during this operation. All non-mainline content was MOVED to `D:\ocn\_ARCHIVE_NON_MAINLINE\`, not deleted.
- **No paper content was modified.** All paper_versions_ordered content (V3_4 through V3_7) remains unchanged in its original location.
- **No CSV data was modified.** All data files remain unchanged.
- **No gold_label / final_label / human_audited fields were written.**
- **No models were run. No APIs were called. No training was performed.**
- **No experiment results were regenerated.**
- **V3.7 original files were not overwritten.** The V3.7 directory in paper_versions_ordered is untouched; copies were made to _MAIN_PAPER_CURRENT and root.
- **The only file removed** was `_backup_dir.txt`, a temporary file created by this script to store the backup path during execution. It was never part of the original project.

## 8. What was kept as mainline

### Paper versions (kept in paper_versions_ordered/):
- V3_4_taxonomy_hardened (taxonomy decision tree, high_risk_sample_bank, trusted_case_bank)
- V3_5_presentation_ready (presentation pack)
- V3_6_case_figure_integrity_checked (case/figure integrity pass)
- V3_7_advisor_handoff_clean (current advisor-review draft)
- VERSION_INDEX.md

### Experiments (kept in experiments/):
- mixed_framework_v2_frozen_r4_baseline (R4 frozen baseline)
- paper_ready_mixed_framework_v2 (paper-ready result pack)
- gpt_structured_judge_probe_v1 (GPT standard vs structured probe)
- llm_judge_baseline_v1 (DeepSeek LLM baseline)
- external_gold_scifact_vitaminc_v1 (SciFact + VitaminC external eval)
- v3_r4_strong_baselines_holdout_v1 (strong baselines + holdout)
- v3_external_gold_llm_plan_v1 (external gold/LLM plan)
- strict_silver_max_v1 (strict silver main data)
- strict_silver_max_v1_binary_decomposition (binary decomposition variant)
- mixed_framework_router_optimization_v2 (router optimization)
- mixed_framework_new_algorithm_sweep_v1 (algorithm sweep)
- paper_v2_strengthening_summary.md (summary)

### Data (kept in data/):
- simclaim_all92_candidate_pool_v1 (main SimClaim data, contains strict_silver_max_v1)
- external_gold (SciFact + VitaminC for external eval)

### Scripts (kept in scripts/, all 190 scripts):
- All scripts retained in original location for reference.
- 16 mainline scripts additionally copied to _MAIN_PAPER_CURRENT/scripts/.

### Docs (kept in docs/):
- 22 mainline doc items (annotation guidelines, data cards, paper-code alignment, reproduction path, workflow, etc.)

## 9. What was archived

See §4 above. Summary by category:
- 7 old paper versions (V1, V2, V3_1, V3_1_review, V3_2, V3_3, V3_mixed_framework_v2_R4)
- 42 old experiment directories
- 42 old data directories
- 10 old doc subdirectories
- 12 old root-level files
- 12 old root-level directories (cese, configs, handoff_*, paper_assets, paper_draft_materials_v1, paper_manuscript_v0, release_simclaim_human_pilot, reports, schemas, _archive_docx_versions)

## 10. Next-step recommendations

1. **Verify the backup** by spot-checking a few files in `D:\ocn_backup_20260704_1606\` against the current D:\ocn.
2. **Test that scripts still run** from the reorganized structure. The scripts/ directory was not moved, so imports should still work. If any script breaks, check whether it referenced a path that was archived.
3. **Send the advisor handoff pack** from `D:\ocn\_MAIN_PAPER_CURRENT\paper_versions\V3_7_advisor_handoff_clean\` (or the root `CESE_OCN_CURRENT_ADVISOR_REVIEW.docx`).
4. **Run the gold pilot** using the materials in `D:\ocn\gold_pilot_preparation_v1\` when annotators are ready.
5. **After gold pilot results are in**, re-evaluate R4 and LLM judges against gold labels per the agreement_statistics_plan.
6. **If the project grows further**, consider a second archive pass for scripts/ (currently 190 scripts, not individually categorized).
7. **The backup at D:\ocn_backup_20260704_1606 can be deleted** after you have verified the reorganized D:\ocn is functioning correctly. Keep it until then.
