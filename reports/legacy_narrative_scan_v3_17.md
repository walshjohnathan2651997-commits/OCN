# Legacy Narrative Scan — V3.17 Confidential Lightweight

Generated: 2026-07-06T20:06:52.444845+00:00

> Read-only scan. No files were modified.

## Summary

| Classification | Count |
|---|---|
| safe_negation | 166 |
| legacy_section | 39 |
| future_work | 3 |
| unsafe_current_claim | 0 |
| ambiguous | 0 |
| **total** | **208** |

## Gate status

- **unsafe_current_claim = 0**: PASS
- **ambiguous = 0**: PASS
- Overall: PASS (all hits are safe_negation, legacy, or future_work)

## All findings by classification

### safe_negation (166)

| Path | Line | Phrase | Context |
|---|---|---|---|
| CURRENT_MAINLINE.md | 27 | gold benchmark | - no gold benchmark claim |
| CURRENT_MAINLINE.md | 28 | human-audited | - no human-audited dataset claim |
| CURRENT_MAINLINE.md | 29 | SOTA | - no SOTA claim |
| CURRENT_MAINLINE.md | 31 | full shared-threshold CESE-OCN | - no full shared-threshold CESE-OCN validation claim |
| CURRENT_MAINLINE.md | 32 | automatic peer review | - no automatic peer review claim |
| CURRENT_MAINLINE.md | 33 | standalone detector | - no standalone detector claim |
| CURRENT_MAINLINE.md | 46 | full shared-threshold CESE-OCN | - **full shared-threshold CESE-OCN neural architecture** = future architecture, not current empirical claim |
| docs/annotation_guidelines_simclaim_eval_v1.md | 5 | human-audited | **Not for:** this guideline must not be used to claim that round1_seed is a benchmark, gold test, or human-audited set. |
| docs/annotation_guidelines_simclaim_eval_v1.md | 224 | human-audited | 5. **`user_confirmed=true` does not imply `human_audited=true`.** Round1 labels are GPT-annotated + GPT-adjudicated +... |
| docs/current_mainline_v3_17.md | 109 | Standalone detector | - "Standalone detector." — R4 standalone viability is false. |
| docs/current_mainline_v3_17.md | 113 | Full shared-threshold CESE-OCN | - "Full shared-threshold CESE-OCN neural architecture validation." — The older CESE-OCN architecture is development h... |
| docs/current_mainline_v3_17.md | 133 | human-audited | \| Validation status \| External \| Controlled silver diagnostic only; not gold; not human-audited \| |
| docs/current_mainline_v3_17.md | 149 | full shared-threshold CESE-OCN | - **Not full CESE-OCN validation.** The older full shared-threshold CESE-OCN neural architecture is development histo... |
| docs/current_mainline_v3_17.md | 163 | full shared-threshold CESE-OCN | 3. **Positioning.** R4 is an offline, auditable, second-stage strong_action screening router (standalone_viable = fal... |
| docs/current_mainline_v3_17.md | 163 | standalone detector | 3. **Positioning.** R4 is an offline, auditable, second-stage strong_action screening router (standalone_viable = fal... |
| docs/current_mainline_v3_17.md | 166 | human-audited | **Safety framing:** All results are silver-label diagnostic only. Not gold. Not human-audited. Not SOTA. Not natural-... |
| docs/current_mainline_v3_17.md | 166 | SOTA | **Safety framing:** All results are silver-label diagnostic only. Not gold. Not human-audited. Not SOTA. Not natural-... |
| docs/current_mainline_v3_17.md | 166 | automatic peer review | **Safety framing:** All results are silver-label diagnostic only. Not gold. Not human-audited. Not SOTA. Not natural-... |
| docs/current_mainline_v3_17_confidential.md | 80 | standalone detector | - **Standalone viability is false.** At 1% prevalence (realistic for unfiltered corpora), FP/TP = 66.82. Every true p... |
| docs/current_mainline_v3_17_confidential.md | 83 | automatic peer reviewer | The system is therefore positioned as a **conservative second-stage screener / review queue generator**, not a standa... |
| docs/current_mainline_v3_17_confidential.md | 149 | gold benchmark | - no gold benchmark claim |
| docs/current_mainline_v3_17_confidential.md | 150 | human-audited | - no human-audited dataset claim |
| docs/current_mainline_v3_17_confidential.md | 151 | SOTA | - no SOTA claim |
| docs/current_mainline_v3_17_confidential.md | 153 | full shared-threshold CESE-OCN | - no full shared-threshold CESE-OCN validation claim |
| docs/current_mainline_v3_17_confidential.md | 154 | automatic peer review | - no automatic peer review claim |
| docs/current_mainline_v3_17_confidential.md | 155 | standalone detector | - no standalone detector claim |
| docs/data_card_simclaim_eval.md | 7 | human-audited | > diagnostic — **not** human-audited, **not** gold). This card is |
| docs/data_release_policy.md | 14 | human-audited | - **Toy synthetic fixtures.** `data/toy/*.jsonl`, `data/pilot_template.jsonl`, and any synthetic data explicitly mark... |
| docs/data_versions.md | 9 | gold benchmark | ## clean_v2 — pilot gold benchmark (NOT paper-ready) |
| docs/data_versions.md | 25 | gold benchmark | AI-preannotated candidate set，共 588 条。它不是 human-audited gold benchmark， |
| docs/data_versions.md | 25 | human-audited | AI-preannotated candidate set，共 588 条。它不是 human-audited gold benchmark， |
| docs/data_versions.md | 54 | gold benchmark | - **NOT allowed as**: paper-ready test set, gold benchmark, sole training source |
| docs/data_versions.md | 72 | gold benchmark | directories and must not be merged into a single gold benchmark. |
| docs/dataset_shortcut_risk_v1.md | 97 | gold benchmark | external gold benchmark (e.g., SciFact, VitaminC). Without external |
| docs/dataset_shortcut_risk_v1.md | 141 | gold benchmark | - "Not a gold benchmark; labels are silver..." |
| docs/dataset_shortcut_risk_v1.md | 145 | Gold benchmark | - "Gold benchmark performance..." |
| docs/dataset_shortcut_risk_v1.md | 147 | Human-audited | - "Human-audited results..." |
| docs/dataset_shortcut_risk_v1.md | 148 | SOTA | - "SOTA performance..." |
| docs/dataset_shortcut_risk_v1.md | 176 | human-audited | silver-labeled, not human-audited)" |
| docs/dataset_shortcut_risk_v1.md | 189 | SOTA | 5. **No SOTA claim**: "This is not a SOTA result; it is a controlled |
| docs/dataset_shortcut_risk_v1.md | 189 | SOTA | 5. **No SOTA claim**: "This is not a SOTA result; it is a controlled |
| docs/dataset_version_lock_v3_17.md | 32 | gold benchmark | - **Not** a gold benchmark. |
| docs/dataset_version_lock_v3_17.md | 33 | human-audited | - **Not** a human-audited benchmark. |
| docs/dataset_version_lock_v3_17.md | 40 | human-audited | > labels are not gold or human-audited, and results should not be |
| docs/dataset_version_lock_v3_17.md | 171 | human-audited | 2. **Not human-audited.** `human_audited=False` for all 444 rows. The |
| docs/human_audit_protocol_v1.md | 6 | gold benchmark | diagnostic candidate pool. The audit is **not** a gold benchmark and must not be |
| docs/human_audit_protocol_v1.md | 26 | gold benchmark | - Not a gold benchmark. |
| docs/human_audit_protocol_v1.md | 132 | gold benchmark | - "small targeted audit, not a gold benchmark" |
| docs/human_audit_protocol_v1.md | 139 | gold benchmark | - "gold benchmark" |
| docs/human_audit_protocol_v1.md | 142 | SOTA | - "SOTA" |
| docs/paper_v2_reproduction_path.md | 16 | gold benchmark | The V2 manuscript is a silver-label pilot paper. It is **not** a gold benchmark, **not** a human-audited dataset pape... |
| docs/paper_v2_reproduction_path.md | 16 | human-audited | The V2 manuscript is a silver-label pilot paper. It is **not** a gold benchmark, **not** a human-audited dataset pape... |
| docs/paper_v2_reproduction_path.md | 42 | human-audited | - silver only; not gold; not human-audited |
| docs/paper_v2_reproduction_path.md | 93 | gold benchmark | - Do not claim gold benchmark. |
| docs/paper_v2_reproduction_path.md | 94 | human-audited | - Do not claim human-audited dataset. |
| docs/paper_v2_reproduction_path.md | 95 | SOTA | - Do not claim SOTA. |
| docs/pdf_extraction_stress_test_v1.md | 12 | SOTA | SOTA benchmark. |
| docs/pdf_extraction_stress_test_v1.md | 214 | SOTA | extraction robustness test, not SOTA." |
| docs/pdf_extraction_stress_test_v1.md | 250 | SOTA | \| `tests/test_pdf_stress_summary_exists.py` \| Summary exists, disclaims SOTA, mentions robustness/OCR/synthetic/con... |
| docs/safe_claims_dictionary_v3_17.md | 16 | gold benchmark | \| Project type \| controlled silver diagnostic study \| gold benchmark study / validated detector study \| "This wor... |
| docs/safe_claims_dictionary_v3_17.md | 17 | gold benchmark | \| Dataset \| source-traceable silver set \| gold-standard dataset / human-verified benchmark \| "The 444-candidate d... |
| docs/safe_claims_dictionary_v3_17.md | 18 | standalone detector | \| Pipeline output \| second-stage review queue \| automatic detector / standalone detector \| "The pipeline produces... |
| docs/safe_claims_dictionary_v3_17.md | 19 | SOTA | \| Research contribution \| retrieval-to-screening format shift analysis \| SOTA claim / SOTA retrieval / SOTA screen... |
| docs/safe_claims_dictionary_v3_17.md | 19 | SOTA | \| Research contribution \| retrieval-to-screening format shift analysis \| SOTA claim / SOTA retrieval / SOTA screen... |
| docs/safe_claims_dictionary_v3_17.md | 19 | SOTA | \| Research contribution \| retrieval-to-screening format shift analysis \| SOTA claim / SOTA retrieval / SOTA screen... |
| docs/safe_claims_dictionary_v3_17.md | 19 | state-of-the-art | \| Research contribution \| retrieval-to-screening format shift analysis \| SOTA claim / SOTA retrieval / SOTA screen... |
| docs/safe_claims_dictionary_v3_17.md | 29 | gold benchmark | > review. It is not a gold benchmark, SOTA detector, or automatic |
| docs/safe_claims_dictionary_v3_17.md | 29 | SOTA | > review. It is not a gold benchmark, SOTA detector, or automatic |
| docs/safe_claims_dictionary_v3_17.md | 63 | SOTA | - **Unsafe**: "We solve the retrieval problem." / "BM25 is SOTA for |
| docs/safe_claims_dictionary_v3_17.md | 92 | gold benchmark | \| U1 \| "This is a gold benchmark." \| All rows have `human_audited=False`; `gold_label` is empty. Silver diagnostic... |
| docs/safe_claims_dictionary_v3_17.md | 92 | gold benchmark | \| U1 \| "This is a gold benchmark." \| All rows have `human_audited=False`; `gold_label` is empty. Silver diagnostic... |
| docs/safe_claims_dictionary_v3_17.md | 93 | human-audited | \| U2 \| "This is a human-audited dataset." \| No full human audit has been completed. Only a small targeted audit pr... |
| docs/safe_claims_dictionary_v3_17.md | 94 | SOTA | \| U3 \| "The pipeline achieves SOTA on simulation claim overclaim detection." \| No comparison to other systems on a... |
| docs/safe_claims_dictionary_v3_17.md | 94 | SOTA | \| U3 \| "The pipeline achieves SOTA on simulation claim overclaim detection." \| No comparison to other systems on a... |
| docs/safe_claims_dictionary_v3_17.md | 95 | automatic peer review | \| U4 \| "The pipeline performs automatic peer review." \| Pipeline produces a review queue for human reviewers; it d... |
| docs/safe_claims_dictionary_v3_17.md | 95 | automatic peer reviewer | \| U4 \| "The pipeline performs automatic peer review." \| Pipeline produces a review queue for human reviewers; it d... |
| docs/safe_claims_dictionary_v3_17.md | 97 | standalone detector | \| U6 \| "The system is a standalone detector." \| At realistic prevalence (1%), FP/TP = 66.82 — unusable as a standa... |
| docs/safe_claims_dictionary_v3_17.md | 97 | standalone detector | \| U6 \| "The system is a standalone detector." \| At realistic prevalence (1%), FP/TP = 66.82 — unusable as a standa... |
| docs/safe_claims_dictionary_v3_17.md | 97 | standalone detector | \| U6 \| "The system is a standalone detector." \| At realistic prevalence (1%), FP/TP = 66.82 — unusable as a standa... |
| docs/safe_claims_dictionary_v3_17.md | 98 | general scientific overstatement detector | \| U7 \| "The system is a general scientific overstatement detector." \| The system is specific to simulation claims ... |
| docs/safe_claims_dictionary_v3_17.md | 112 | Full shared-threshold CESE-OCN | \| Full CESE-OCN \| "Full shared-threshold CESE-OCN neural architecture (future work, not current empirical claim)" \... |
| docs/safe_claims_dictionary_v3_17.md | 113 | human-audited | \| Human audit \| "A small targeted human audit protocol exists (future work, not yet completed)" \| "The dataset is ... |
| docs/safe_claims_dictionary_v3_17.md | 114 | Gold benchmark | \| Gold labels \| "Gold labels are future work; current labels are silver (`human_audited=False`)" \| "Gold benchmark... |
| docs/safe_claims_dictionary_v3_17.md | 127 | human-audited | 3. A clear statement that V2 / full CESE-OCN / gold / human-audited / |
| docs/safe_claims_dictionary_v3_17.md | 128 | SOTA | SOTA / automatic peer review are **not** claimed. |
| docs/safe_claims_dictionary_v3_17.md | 128 | automatic peer review | SOTA / automatic peer review are **not** claimed. |
| docs/safe_claims_dictionary_v3_17.md | 130 | current paper V2 | The README MUST NOT contain "current paper V2" or "current manuscript |
| docs/simclaim_current_data_status_lock.md | 24 | human audited | - `human_audited` = false (single-annotator pilot, not dual-human audited) |
| docs/simclaim_current_data_status_lock.md | 32 | human-audited | - **Not** a human-audited benchmark. |
| docs/simclaim_current_data_status_lock.md | 45 | human-audited | - Missing: human-audited gold, larger test set, strong baselines (BERT/RoBERTa/DeBERTa), OOD validation. |
| docs/simclaim_current_data_status_lock.md | 58 | human-audited | - `human_audited` = **false** (NOT human-audited). |
| docs/simclaim_current_data_status_lock.md | 74 | Human-audited | - Human-audited test set. |
| docs/simclaim_current_data_status_lock.md | 80 | human audited | These labels are **user-confirmed GPT-adjudicated round1 seed labels**. They are final labels for the internal round1... |
| docs/simclaim_current_data_status_lock.md | 84 | human-audited | - human-audited benchmark |
| docs/simclaim_current_data_status_lock.md | 117 | human-audited | - `human_audited` = **false** (NOT human-audited). |
| docs/simclaim_current_data_status_lock.md | 136 | Human-audited | - Human-audited test set. |
| docs/simclaim_current_data_status_lock.md | 144 | human-audited | These 14 rows are **annotation-ready candidates**. They have **not** been annotated yet. They are **not** final label... |
| docs/simclaim_current_data_status_lock.md | 187 | human-audited | 9. **No relabeling.** round1_seed labels remain user-confirmed GPT-adjudicated; they are not human-audited gold. roun... |
| docs/simclaim_current_data_status_lock.md | 199 | human-audited | 4. Only after `simclaim_eval_v1_core` is human-audited, consider training or evaluation. |
| docs/simclaim_current_data_status_lock.md | 200 | human-audited | 5. Do **not** merge `round1_seed` (GPT-adjudicated) with `simclaim_eval_v1_core` (human-audited) without explicit pro... |
| docs/simclaim_eval_v1_data_status.md | 6 | human-audited | > diagnostic, `human_audited=False`, **not** gold, **not** human-audited). |
| docs/simclaim_eval_v1_data_status.md | 71 | human-audited | - human-audited test set |
| docs/simclaim_eval_v1_data_status.md | 100 | human-audited | - "human-audited" |
| docs/simclaim_paper_full_data_generation_rules.md | 164 | human-audited | - no human-audited gold labels |
| docs/tfidf_as_leakage_auditor.md | 33 | human-audited | - no human-audited gold labels |
| paper_assets/v3_17_confidential/figures/pipeline_ascii.md | 25 | human-audited | <!-- Controlled silver diagnostic, not gold/human-audited. --> |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 3 | human-audited | > Controlled silver diagnostic, not gold/human-audited. |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 10 | human-audited | \| C2 \| not human-audited benchmark \| YES (see U7, S8) \| |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 11 | SOTA | \| C3 \| not SOTA \| YES (see U8) \| |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 12 | automatic peer review | \| C4 \| not automatic peer review \| YES (see U9) \| |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 51 | gold benchmark | - **Safe wording**: "The 444-candidate dataset is a controlled silver diagnostic with human_audited=False; it is not ... |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 55 | standalone detector | ### S6: Second-stage review queue only (not a standalone detector) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 72 | human-audited | - **Safe wording**: "A small targeted human audit protocol is defined to verify directional reliability of top queue ... |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 74 | gold benchmark | - **Bound**: Small targeted audit (80–120 candidates); not a gold benchmark; not a full human-audited benchmark. |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 74 | human-audited | - **Bound**: Small targeted audit (80–120 candidates); not a gold benchmark; not a full human-audited benchmark. |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 79 | standalone detector | - **Why unsafe**: System is a review queue generator, not a standalone detector. Silver labels only. |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 93 | gold benchmark | ### U6: "This is a gold benchmark."  (violates: not gold) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 96 | human-audited | ### U7: "This is a human-audited benchmark."  (violates: not human-audited benchmark) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 96 | human-audited | ### U7: "This is a human-audited benchmark."  (violates: not human-audited benchmark) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 99 | SOTA | ### U8: "The pipeline achieves SOTA on simulation claim overclaim detection."  (violates: not SOTA) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 99 | SOTA | ### U8: "The pipeline achieves SOTA on simulation claim overclaim detection."  (violates: not SOTA) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 102 | automatic peer review | ### U9: "The pipeline performs automatic peer review."  (violates: not automatic peer review) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 102 | automatic peer review | ### U9: "The pipeline performs automatic peer review."  (violates: not automatic peer review) |
| paper_assets/v3_17_confidential/paper_claims_checklist.md | 124 | human-audited | > Controlled silver diagnostic, not gold/human-audited. |
| paper_assets/v3_17_confidential/paper_results_summary.md | 3 | human-audited | > Controlled silver diagnostic, not gold/human-audited. |
| paper_assets/v3_17_confidential/paper_results_summary.md | 59 | human-audited | - All results are silver-label diagnostic, not gold/human-audited. |
| paper_assets/v3_17_confidential/tables/table7_complexity_utility.md | 12 | human-audited | *Controlled silver diagnostic, not gold/human-audited.* |
| paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md | 5 | gold benchmark | *Small targeted audit, not a gold benchmark. Audit seed is built; auditor labels pending.* |
| README.md | 9 | gold benchmark | > confidential local PDF review. It is **not** a gold benchmark, SOTA |
| README.md | 9 | SOTA | > confidential local PDF review. It is **not** a gold benchmark, SOTA |
| README.md | 10 | automatic peer reviewer | > detector, or automatic peer reviewer. |
| README.md | 38 | gold benchmark | - no gold benchmark claim |
| README.md | 39 | human-audited | - no human-audited dataset claim |
| README.md | 40 | SOTA | - no SOTA claim |
| README.md | 42 | full shared-threshold CESE-OCN | - no full shared-threshold CESE-OCN validation claim |
| README.md | 43 | automatic peer review | - no automatic peer review claim |
| README.md | 44 | standalone detector | - no standalone detector claim |
| README.md | 78 | human-audited | - not human-audited |
| README.md | 79 | SOTA | - not SOTA |
| README.md | 81 | full shared-threshold CESE-OCN | - not full shared-threshold CESE-OCN neural architecture validation |
| README.md | 82 | standalone detector | - not a standalone detector |
| README.md | 95 | full shared-threshold CESE-OCN | The sections below describe older material: the **V2 evidence-aware hierarchical pilot** (legacy pilot), the **simcla... |
| README.md | 99 | full shared-threshold CESE-OCN | - **full shared-threshold CESE-OCN** = future architecture, not current empirical claim |
| README.md | 218 | human-audited | is NOT human-audited and NOT paper-ready. Use it to verify the pipeline |
| reports/current_project_status_v3_17.md | 10 | gold benchmark | - [x] README denies gold benchmark |
| reports/current_project_status_v3_17.md | 11 | human-audited | - [x] README denies human-audited |
| reports/current_project_status_v3_17.md | 12 | SOTA | - [x] README denies SOTA |
| reports/current_project_status_v3_17.md | 24 | full shared-threshold CESE-OCN | - `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN** = future architecture, n... |
| reports/current_project_status_v3_17.md | 24 | full shared-threshold CESE-OCN | - `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN** = future architecture, n... |
| reports/current_project_status_v3_17.md | 25 | gold benchmark | - `README.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 25 | gold benchmark | - `README.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 33 | gold benchmark | - `CURRENT_MAINLINE.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 33 | gold benchmark | - `CURRENT_MAINLINE.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 206 | human-audited | \| Frozen R4 review queue has results \| `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.cs... |
| reports/current_project_status_v3_17.md | 211 | SOTA | \| PDF-start extraction stress test has results \| `experiments/pdf_extraction_stress_test_v1/` \| exists \| **toy** ... |
| reports/current_project_status_v3_17.md | 213 | gold benchmark | \| Human audit has results \| `experiments/human_audit_v1/audit_agreement_summary.json` \| partial \| **blocked** \| ... |
| reports/current_project_status_v3_17.md | 214 | human-audited | \| Paper assets generated \| `paper_assets/v3_17_confidential/tables/` \| exists \| **real** \| 8 tables (md+tex), 4 ... |
| reports/current_project_status_v3_17.md | 221 | SOTA | - **P0** [BLOCKED]: Clean up old narratives in docs (V2/gold/SOTA references) |
| reports/current_project_status_v3_17.md | 222 | gold benchmark | - Reason: 79 old narrative references found (majority are denials like 'not a gold benchmark') |
| reports/current_project_status_v3_17.md | 223 | gold benchmark | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 223 | human-audited | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 223 | SOTA | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 255 | human-audited | > All results are controlled silver diagnostic, not gold/human-audited. |
| reports/dataset_provenance_ledger_v3_17.md | 13 | gold benchmark | - not gold benchmark |
| reports/dataset_provenance_ledger_v3_17.md | 14 | human-audited | - not human-audited benchmark |
| reports/dataset_provenance_ledger_v3_17.md | 20 | human-audited | > We use a source-traceable controlled silver diagnostic set. The labels are not gold or human-audited, and results s... |

### legacy_section (39)

| Path | Line | Phrase | Context |
|---|---|---|---|
| docs/archive/README.md | 25 | Full shared-threshold CESE-OCN | - **Full shared-threshold CESE-OCN neural architecture.** The dual-branch ordinal calibration network with shared thr... |
| docs/data_card_simclaim_eval.md | 22 | human-audited | cites. Each record pairs a claim with evidence and a human-audited |
| docs/simclaim_eval_v1_data_status.md | 26 | human-audited | - human-audited: governed by the existing pilot/paper_full ruleset. |
| docs/simclaim_eval_v1_data_status.md | 53 | human-audited | ### 3. `simclaim_eval_v1_core` — future human-audited core |
| docs/simclaim_eval_v1_data_status.md | 56 | human-audited | - Role: to be constructed from human-audited source-paired samples. |
| reports/current_project_status_v3_17.md | 23 | full shared-threshold CESE-OCN | - `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architecture** (fut... |
| reports/current_project_status_v3_17.md | 23 | full shared-threshold CESE-OCN | - `README.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architecture** (fut... |
| reports/current_project_status_v3_17.md | 26 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 26 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 27 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 27 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 28 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 28 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 29 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 29 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 30 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 30 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 31 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 31 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 32 | full shared-threshold CESE-OCN | - `CURRENT_MAINLINE.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architect... |
| reports/current_project_status_v3_17.md | 32 | full shared-threshold CESE-OCN | - `CURRENT_MAINLINE.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architect... |
| reports/current_project_status_v3_17.md | 34 | human-audited | - `CURRENT_MAINLINE.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 34 | human-audited | - `CURRENT_MAINLINE.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 35 | SOTA | - `CURRENT_MAINLINE.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 35 | SOTA | - `CURRENT_MAINLINE.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 36 | automatic peer review | - `CURRENT_MAINLINE.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 36 | automatic peer review | - `CURRENT_MAINLINE.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 37 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 37 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 38 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 38 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 39 | full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "Full shared-threshold CESE-OCN neura... |
| reports/current_project_status_v3_17.md | 39 | Full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "Full shared-threshold CESE-OCN neura... |
| reports/current_project_status_v3_17.md | 40 | full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neura... |
| reports/current_project_status_v3_17.md | 40 | full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neura... |
| reports/current_project_status_v3_17.md | 41 | human-audited | - `docs\current_mainline_v3_17.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 41 | human-audited | - `docs\current_mainline_v3_17.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 42 | human-audited | - `docs\current_mainline_v3_17.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 42 | human-audited | - `docs\current_mainline_v3_17.md`: human-audited — "human-audited" |

### future_work (3)

| Path | Line | Phrase | Context |
|---|---|---|---|
| docs/data_versions.md | 65 | gold benchmark | the audited subset may seed a gold benchmark |
| docs/how_to_upgrade_to_paper_full.md | 34 | human-audited | 1. Expanding the human-audited sample to at least 300 adjudicated items |
| docs/next_phase_benchmark_plan.md | 31 | Human-audited | \| Human-audited \| 0 \| 100% of test + 30% of train (stratified) \| Adjudicated gold for every reported number \| |

## Scanned files

- `CURRENT_MAINLINE.md`
- `README.md`
- `docs/annotation_guidelines_simclaim_eval_v1.md`
- `docs/archive/README.md`
- `docs/current_mainline_v3_17.md`
- `docs/current_mainline_v3_17_confidential.md`
- `docs/data_card_simclaim_eval.md`
- `docs/data_release_policy.md`
- `docs/data_versions.md`
- `docs/dataset_shortcut_risk_v1.md`
- `docs/dataset_version_lock_v3_17.md`
- `docs/how_to_upgrade_to_paper_full.md`
- `docs/human_audit_protocol_v1.md`
- `docs/next_phase_benchmark_plan.md`
- `docs/paper_v2_reproduction_path.md`
- `docs/pdf_extraction_stress_test_v1.md`
- `docs/safe_claims_dictionary_v3_17.md`
- `docs/simclaim_current_data_status_lock.md`
- `docs/simclaim_eval_v1_data_status.md`
- `docs/simclaim_paper_full_data_generation_rules.md`
- `docs/tfidf_as_leakage_auditor.md`
- `paper_assets/v3_17_confidential/figures/pipeline_ascii.md`
- `paper_assets/v3_17_confidential/paper_claims_checklist.md`
- `paper_assets/v3_17_confidential/paper_results_summary.md`
- `paper_assets/v3_17_confidential/tables/table7_complexity_utility.md`
- `paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md`
- `reports/current_project_status_v3_17.md`
- `reports/dataset_provenance_ledger_v3_17.md`
