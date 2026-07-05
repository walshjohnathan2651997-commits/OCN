# Paper Version Lineage Report

> **REALIGNMENT BANNER (2026-07-05):** The current selected main method is the **V3.17 baseline** offline PDF-corpus evidence-sufficiency screening pipeline, which is NOT a paper version per se. V3.7 (listed below as the latest paper version) is a **historical advisor-handoff draft**, not the current selected method. V3.18 intelligent upgrade is an exploratory negative ablation (not selected). The paper-version lineage below is retained for traceability; see `D:\ocn\project_synthesis\mainline_realignment_v1\` for the authoritative realignment.

**Date:** 2026-07-05
**Versions scanned:** 16
**Note:** All paper versions below are historical. Current selected mainline method is V3.17 baseline (not a paper version).

## Version lineage (V3.4 → V3.15)

| Version | Positioning | Size (MD) | Hierarchical | RIGOURATE diff | Non-gold checks | Gold pending | Status |
|---|---|---|---|---|---|---|---|
| V3_4_taxonomy_hardened | taxonomy hardened | 82960 | no | no | no | yes | Historical taxonomy hardened |
| V3_5_presentation_ready | presentation ready | 54370 | no | no | no | yes | Historical |
| V3_6_case_figure_integrity_checked | case figure integrity checked | 62842 | no | no | no | yes | Historical |
| V3_7_advisor_handoff_clean | advisor handoff clean | 64620 | no | no | no | yes | Historical advisor handoff |
| V3_8_reference_refreshed | reference refreshed | 67424 | no | yes | no | yes | Historical reference refresh |
| V3_9_pre_gold_complete | pre-gold complete | 79984 | no | yes | no | yes | Historical pre-gold |
| V3_9_pre_gold_complete_audit | pre-gold complete audit | 0 | no | no | no | no | Historical pre-gold |
| V3_10_advisor_ready_silver_stage | advisor ready silver stage | 83393 | no | yes | no | yes | Historical advisor-ready |
| V3_10_1_advisor_send_clean | advisor send clean (V3.10.1) | 84688 | no | yes | no | yes | Historical advisor-ready |
| V3_11_high_standard_framework_roadmap | high-standard framework roadmap | 82599 | no | yes | no | yes | Historical framework roadmap |
| V3_12_with_three_credibility_checks | three credibility checks | 93389 | no | yes | yes | yes | Three credibility checks |
| V3_12_1_advisor_send_clean | advisor send clean (V3.12.1) | 94214 | no | yes | yes | yes | Historical advisor-send |
| V3_13_differentiated_against_rigourate_forcebench | differentiated against RIGOURATE/ForceBench | 115358 | no | yes | yes | yes | Historical |
| V3_13_rigourate_differentiated_realism_aware | RIGOURATE-differentiated + realism-aware | 138346 | no | yes | yes | yes | RIGOURATE-aware |
| V3_14_mainline_locked_consistency_audit | mainline locked + consistency audit | 142965 | no | yes | yes | yes | Source for V3.15 |
| V3_15_hierarchical_taxonomy_revision | hierarchical diagnostic taxonomy (Level 1 + Level 2) | 157953 | yes | yes | yes | yes | CURRENT RECOMMENDED VERSION |

## What each version did

- **V3.4 taxonomy_hardened:** Taxonomy hardening (decision tree, high_risk_sample_bank, trusted_case_bank). First version with the four-class taxonomy operationalized.
- **V3.5 presentation_ready:** Polished for presentation; case studies and figures finalized.
- **V3.6 case_figure_integrity_checked:** Case/figure integrity audit; ensured all figures and tables are consistent.
- **V3.7 advisor_handoff_clean:** Clean version for advisor handoff; was the V3.7-era "current" version. Includes advisor cover note, one-page summary, reviewer risk brief.
- **V3.8 reference_refreshed:** Reference list refreshed; citation consistency improved.
- **V3.9 pre_gold_complete:** Pre-gold-completion version; silver-stage results finalized.
- **V3.9_pre_gold_complete_audit:** Audit of V3.9; next-action gate generated.
- **V3.10 advisor_ready_silver_stage:** Silver-stage results packaged for advisor review.
- **V3.10_1 advisor_send_clean:** Clean send version; minor fixes over V3.10.
- **V3.11 high_standard_framework_roadmap:** High-standard framework roadmap; introduced three core credibility experiments plan.
- **V3.12 with_three_credibility_checks:** Added three credibility checks (label-shift, screening utility, evidence necessity); readiness gate confirmed advisor-send-ready.
- **V3.12_1 advisor_send_clean:** Clean send version of V3.12.
- **V3.13_differentiated_against_rigourate_forcebench:** First differentiation pass against RIGOURATE/ForceBench/CLAIM-BENCH.
- **V3.13_rigourate_differentiated_realism_aware:** RIGOURATE-differentiated + realism-aware; added §II.A positioning, §VII.J realism audit plan, §VI.E scalar baseline.
- **V3.14 mainline_locked_consistency_audit:** Mainline locked + reviewer-grade consistency audit; 142965 bytes MD; source for V3.15.
- **V3.15 hierarchical_taxonomy_revision:** CURRENT RECOMMENDED VERSION. Reframes flat four-class as hierarchical diagnostic taxonomy (Level 1 + Level 2); adds Table 0a, §VII.K, §VIII.G; 18 targeted replacements; all experimental numbers preserved byte-identical; all 10 §12 quality checks PASS.

## Current recommended reading version

**V3.15 hierarchical_taxonomy_revision** is the current recommended main paper version.

- **MD:** `D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision\CESE_OCN_V3_15_hierarchical_taxonomy_revision.md` (157953 bytes)
- **DOCX:** `D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision\CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx` (54349 bytes)
- **Attack response:** `flat_four_class_attack_response.md`
- **Gold plan:** `hierarchical_gold_validation_plan.md`
- **Mapping:** `hierarchical_label_mapping.csv`
- **Readiness gate:** `hierarchical_taxonomy_revision_gate.json` (13 fields, all True)

## Historical versions (do not use as main draft)

All versions V3.4 through V3.14 are historical. They are preserved unchanged for audit trail. **Do not modify them.** The lineage shows a clear progression: V3.4 (taxonomy hardened) → V3.7 (advisor handoff) → V3.12 (three credibility checks) → V3.13 (RIGOURATE-differentiated) → V3.14 (mainline locked) → V3.15 (hierarchical taxonomy).

**V3.14** is the immediate predecessor and remains the source-of-truth for experimental numbers (all V3.15 numbers are byte-identical to V3.14). If a reader wants the "last flat-four-class version", V3.14 is that version.

## Note on _MAIN_PAPER_CURRENT and _PROJECT_INDEX

`_PROJECT_INDEX/current_paper_paths.md` references V3.7 as current — this is **outdated**. The actual current paper is V3.15. The `_MAIN_PAPER_CURRENT/` directory contains V3.7-era curated copies and should not be used as the source of truth. Always read from `paper_versions_ordered/V3_15_hierarchical_taxonomy_revision/`.
