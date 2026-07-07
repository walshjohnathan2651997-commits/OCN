# Legacy Narrative Scan — V3.17 Confidential Lightweight

Generated: 2026-07-07T17:35:15.551257+00:00

> Read-only scan. No files were modified.

## Summary

| Classification | Count |
|---|---|
| safe_negation | 431 |
| legacy_section | 39 |
| future_work | 3 |
| unsafe_current_claim | 0 |
| ambiguous | 0 |
| **total** | **473** |

## Gate status

- **unsafe_current_claim = 0**: PASS
- **ambiguous = 0**: PASS
- Overall: PASS (all hits are safe_negation, legacy, or future_work)

## All findings by classification

### safe_negation (431)

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
| docs/human_audit_protocol_v1.md | 154 | human-audited | states "audit packet prepared; audit not yet executed" and "no human-audited |
| docs/human_audit_protocol_v1.md | 163 | gold benchmark | **This is a targeted audit protocol, not a gold benchmark.** Until the audit is |
| docs/human_audit_protocol_v1.md | 164 | human-audited | completed, the paper can only claim audit readiness, not human-audited |
| docs/human_audit_protocol_v1.md | 173 | gold benchmark | - "small targeted audit, not a gold benchmark" |
| docs/human_audit_protocol_v1.md | 180 | gold benchmark | - "gold benchmark" |
| docs/human_audit_protocol_v1.md | 183 | SOTA | - "SOTA" |
| docs/paper_outline_v3_17_confidential.md | 35 | gold benchmark | gold benchmark. |
| docs/paper_outline_v3_17_confidential.md | 48 | gold benchmark | The abstract must **not** contain: gold benchmark, SOTA, automatic |
| docs/paper_outline_v3_17_confidential.md | 48 | SOTA | The abstract must **not** contain: gold benchmark, SOTA, automatic |
| docs/paper_outline_v3_17_confidential.md | 82 | gold benchmark | - **Not** a gold benchmark, SOTA detector, automatic peer reviewer, or |
| docs/paper_outline_v3_17_confidential.md | 82 | SOTA | - **Not** a gold benchmark, SOTA detector, automatic peer reviewer, or |
| docs/paper_outline_v3_17_confidential.md | 82 | automatic peer reviewer | - **Not** a gold benchmark, SOTA detector, automatic peer reviewer, or |
| docs/paper_outline_v3_17_confidential.md | 109 | gold benchmark | - **Not** a gold benchmark, not human-audited, not natural prevalence. |
| docs/paper_outline_v3_17_confidential.md | 109 | human-audited | - **Not** a gold benchmark, not human-audited, not natural prevalence. |
| docs/paper_outline_v3_17_confidential.md | 137 | standalone detector | router — **not** a standalone detector. |
| docs/paper_outline_v3_17_confidential.md | 259 | gold benchmark | - "gold benchmark" — dataset is silver |
| docs/paper_outline_v3_17_confidential.md | 260 | human-audited | - "human-audited benchmark" — human_audited=False for all rows |
| docs/paper_outline_v3_17_confidential.md | 261 | SOTA | - "SOTA" / "state-of-the-art" — not SOTA |
| docs/paper_outline_v3_17_confidential.md | 261 | SOTA | - "SOTA" / "state-of-the-art" — not SOTA |
| docs/paper_outline_v3_17_confidential.md | 261 | state-of-the-art | - "SOTA" / "state-of-the-art" — not SOTA |
| docs/paper_outline_v3_17_confidential.md | 262 | automatic peer reviewer | - "automatic peer reviewer" — not automatic peer review |
| docs/paper_outline_v3_17_confidential.md | 262 | automatic peer review | - "automatic peer reviewer" — not automatic peer review |
| docs/paper_outline_v3_17_confidential.md | 272 | human-audited | > labels are not gold or human-audited, and results should not be |
| docs/paper_v2_reproduction_path.md | 16 | gold benchmark | The V2 manuscript is a silver-label pilot paper. It is **not** a gold benchmark, **not** a human-audited dataset pape... |
| docs/paper_v2_reproduction_path.md | 16 | human-audited | The V2 manuscript is a silver-label pilot paper. It is **not** a gold benchmark, **not** a human-audited dataset pape... |
| docs/paper_v2_reproduction_path.md | 42 | human-audited | - silver only; not gold; not human-audited |
| docs/paper_v2_reproduction_path.md | 93 | gold benchmark | - Do not claim gold benchmark. |
| docs/paper_v2_reproduction_path.md | 94 | human-audited | - Do not claim human-audited dataset. |
| docs/paper_v2_reproduction_path.md | 95 | SOTA | - Do not claim SOTA. |
| docs/pdf_extraction_stress_test_v1.md | 12 | SOTA | SOTA benchmark. |
| docs/pdf_extraction_stress_test_v1.md | 214 | SOTA | extraction robustness test, not SOTA." |
| docs/pdf_extraction_stress_test_v1.md | 250 | SOTA | \| `tests/test_pdf_stress_summary_exists.py` \| Summary exists, disclaims SOTA, mentions robustness/OCR/synthetic/con... |
| docs/result_narrative_freeze_v3_17.md | 15 | SOTA | - No SOTA / general detector / automatic peer reviewer claims. |
| docs/result_narrative_freeze_v3_17.md | 15 | automatic peer reviewer | - No SOTA / general detector / automatic peer reviewer claims. |
| docs/result_narrative_freeze_v3_17.md | 29 | SOTA | - **Not supported interpretation:** BM25 is SOTA for scientific claim |
| docs/result_narrative_freeze_v3_17.md | 141 | SOTA | detector; R4 achieves SOTA on simulation claim screening; the F1 |
| docs/result_narrative_freeze_v3_17.md | 159 | standalone detector | the queue acting as a standalone detector (not supported); |
| docs/result_narrative_freeze_v3_17.md | 188 | gold benchmark | all possible attacks; the dataset is a gold benchmark; the PASS |
| docs/result_narrative_freeze_v3_17.md | 247 | human-audited | - **Not supported interpretation:** The dataset is human-audited; |
| docs/result_narrative_freeze_v3_17.md | 253 | SOTA | ## Result R13 — PDF extraction stress test (robustness, not SOTA) |
| docs/result_narrative_freeze_v3_17.md | 263 | SOTA | SOTA claim. |
| docs/result_narrative_freeze_v3_17.md | 264 | SOTA | - **Not supported interpretation:** The extractor is SOTA on |
| docs/result_narrative_freeze_v3_17.md | 275 | gold benchmark | - "gold benchmark" — `human_audited=False` for all rows |
| docs/result_narrative_freeze_v3_17.md | 276 | human-audited | - "human-audited benchmark" — no full human audit completed |
| docs/result_narrative_freeze_v3_17.md | 277 | SOTA | - "SOTA" / "state-of-the-art" — no shared-benchmark comparison |
| docs/result_narrative_freeze_v3_17.md | 277 | state-of-the-art | - "SOTA" / "state-of-the-art" — no shared-benchmark comparison |
| docs/result_narrative_freeze_v3_17.md | 278 | automatic peer reviewer | - "automatic peer reviewer" — pipeline produces a review queue, |
| docs/result_narrative_freeze_v3_17.md | 279 | automatic peer review | not automatic peer review |
| docs/result_narrative_freeze_v3_17.md | 289 | human-audited | > labels are not gold or human-audited, and results should not be |
| docs/reviewer_response_playbook_v3_17.md | 17 | gold benchmark | > review. It is **not** a gold benchmark, SOTA detector, or automatic |
| docs/reviewer_response_playbook_v3_17.md | 17 | SOTA | > review. It is **not** a gold benchmark, SOTA detector, or automatic |
| docs/reviewer_response_playbook_v3_17.md | 30 | gold benchmark | We acknowledge the dataset is a controlled silver diagnostic set, not a gold benchmark. Labels are AI-preannotated (a... |
| docs/reviewer_response_playbook_v3_17.md | 72 | gold benchmark | We acknowledge the human audit is not complete. The protocol (2-annotator independent review + adjudication) and seed... |
| docs/reviewer_response_playbook_v3_17.md | 92 | full shared-threshold CESE-OCN | We explicitly state there is no full shared-threshold CESE-OCN validation in V3.17; the full architecture is future w... |
| docs/reviewer_response_playbook_v3_17.md | 147 | SOTA | **Safe response:** We test PDF extraction robustness with 12 synthetic stress documents covering multi-column, table-... |
| docs/reviewer_response_playbook_v3_17.md | 159 | general scientific overstatement detector | **Safe response:** We explicitly state the system is NOT a general scientific overstatement detector. It is a simulat... |
| docs/reviewer_response_playbook_v3_17.md | 181 | gold benchmark | - "Our gold benchmark shows..." (dataset is silver, not gold) |
| docs/reviewer_response_playbook_v3_17.md | 183 | SOTA | - "State-of-the-art detector..." (not SOTA) |
| docs/reviewer_response_playbook_v3_17.md | 183 | State-of-the-art | - "State-of-the-art detector..." (not SOTA) |
| docs/reviewer_response_playbook_v3_17.md | 184 | Automatic peer review | - "Automatic peer review..." (not automatic peer review) |
| docs/reviewer_response_playbook_v3_17.md | 184 | automatic peer review | - "Automatic peer review..." (not automatic peer review) |
| docs/reviewer_response_playbook_v3_17.md | 195 | gold benchmark | - "Small targeted audit (not a gold benchmark)..." |
| docs/reviewer_risk_register_v3_17.md | 47 | gold benchmark | - **safe_response:** We acknowledge the dataset is a controlled silver diagnostic set, not a gold benchmark. Labels a... |
| docs/reviewer_risk_register_v3_17.md | 121 | gold benchmark | - **safe_response:** We acknowledge the human audit is not complete. The protocol (2-annotator independent review + a... |
| docs/reviewer_risk_register_v3_17.md | 136 | SOTA | - **safe_response:** We test PDF extraction robustness with 12 synthetic stress documents covering multi-column, tabl... |
| docs/reviewer_risk_register_v3_17.md | 151 | general scientific overstatement detector | - **safe_response:** We explicitly state the system is NOT a general scientific overstatement detector. It is a simul... |
| docs/reviewer_risk_register_v3_17.md | 180 | full shared-threshold CESE-OCN | - **safe_response:** We explicitly state there is no full shared-threshold CESE-OCN validation in V3.17; the full arc... |
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
| paper_assets/v3_17_confidential/abstract_draft.md | 28 | human-audited | source-traceable but not gold and not human-audited |
| paper_assets/v3_17_confidential/abstract_draft.md | 45 | standalone detector | queue augments human review; it is not a standalone detector and does |
| paper_assets/v3_17_confidential/abstract_draft.md | 57 | SOTA | general detector, not SOTA, and not an automatic peer reviewer. |
| paper_assets/v3_17_confidential/abstract_draft.md | 57 | automatic peer reviewer | general detector, not SOTA, and not an automatic peer reviewer. |
| paper_assets/v3_17_confidential/abstract_draft.md | 77 | gold benchmark | \| gold benchmark \| no \| |
| paper_assets/v3_17_confidential/abstract_draft.md | 78 | SOTA | \| SOTA / state-of-the-art \| no \| |
| paper_assets/v3_17_confidential/abstract_draft.md | 78 | state-of-the-art | \| SOTA / state-of-the-art \| no \| |
| paper_assets/v3_17_confidential/abstract_draft.md | 79 | automatic peer review | \| automatic peer review \| no \| |
| paper_assets/v3_17_confidential/abstract_draft.md | 81 | human-audited | \| human-audited benchmark \| no \| |
| paper_assets/v3_17_confidential/contribution_bullets.md | 5 | SOTA | bullet claims gold, SOTA, automatic peer review, or general detector |
| paper_assets/v3_17_confidential/contribution_bullets.md | 5 | automatic peer review | bullet claims gold, SOTA, automatic peer review, or general detector |
| paper_assets/v3_17_confidential/contribution_bullets.md | 62 | gold benchmark | - We do **not** claim a gold benchmark. |
| paper_assets/v3_17_confidential/contribution_bullets.md | 63 | human-audited | - We do **not** claim a human-audited dataset. |
| paper_assets/v3_17_confidential/contribution_bullets.md | 64 | SOTA | - We do **not** claim SOTA on simulation claim screening. |
| paper_assets/v3_17_confidential/contribution_bullets.md | 65 | automatic peer reviewer | - We do **not** claim an automatic peer reviewer. |
| paper_assets/v3_17_confidential/contribution_bullets.md | 77 | human-audited | > labels are not gold or human-audited, and results should not be |
| paper_assets/v3_17_confidential/figures/pipeline_ascii.md | 25 | human-audited | <!-- Controlled silver diagnostic, not gold/human-audited. --> |
| paper_assets/v3_17_confidential/limitations_draft.md | 22 | human-audited | diagnostic set. The labels are not gold or human-audited, and |
| paper_assets/v3_17_confidential/limitations_draft.md | 49 | gold benchmark | This is a targeted audit protocol, not a gold benchmark. |
| paper_assets/v3_17_confidential/limitations_draft.md | 52 | human-audited | readiness, not human-audited validation." |
| paper_assets/v3_17_confidential/limitations_draft.md | 110 | standalone detector | ## L6 — Second-stage queue, not standalone detector |
| paper_assets/v3_17_confidential/limitations_draft.md | 114 | standalone detector | FP/TP = 66.82, which is unusable as a standalone detector. |
| paper_assets/v3_17_confidential/limitations_draft.md | 120 | standalone detector | queue that augments human review; it is not a standalone detector |
| paper_assets/v3_17_confidential/limitations_draft.md | 156 | full shared-threshold CESE-OCN | claim. There is no full shared-threshold CESE-OCN validation in |
| paper_assets/v3_17_confidential/limitations_draft.md | 172 | human-audited | > labels are not gold or human-audited, and results should not be |
| paper_assets/v3_17_confidential/limitations_draft.md | 174 | SOTA | > a validated general detector, not SOTA, and not an automatic peer |
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
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 15 | gold benchmark | We agree that the dataset is a **controlled silver diagnostic set**, not a gold benchmark. We agree that silver label... |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 15 | gold benchmark | We agree that the dataset is a **controlled silver diagnostic set**, not a gold benchmark. We agree that silver label... |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 15 | human-audited | We agree that the dataset is a **controlled silver diagnostic set**, not a gold benchmark. We agree that silver label... |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 37 | gold benchmark | We answer the reviewer as follows: the dataset is explicitly a controlled silver diagnostic set, not a gold benchmark... |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 50 | gold benchmark | > "We emphasize that the SimClaim Strict Silver Diagnostic Set v1 is a controlled silver diagnostic set, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 56 | gold benchmark | \| "gold benchmark" \| labels are silver (`candidate_label_guess`), `human_audited=False`, `gold_label` empty \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 57 | human-audited | \| "human-audited dataset" \| human audit protocol staged, not executed; no `audit_agreement_summary.json` \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 58 | human-audited | \| "validated general detector" \| silver diagnostic only; no cross-dataset or human-audited validation \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 59 | SOTA | \| "SOTA on simulation-claim screening" \| no gold comparison; silver labels cannot anchor a SOTA claim \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md | 59 | SOTA | \| "SOTA on simulation-claim screening" \| no gold comparison; silver labels cannot anchor a SOTA claim \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md | 36 | human-audited | We answer the reviewer as follows: the human audit is staged but not executed. The protocol, template, and seed queue... |
| paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md | 38 | human-audited | The safe empirical conclusion is therefore narrow: **the reported metrics are silver-conditional diagnostics on a con... |
| paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md | 50 | human-audited | > "We explicitly state that no human audit has been executed. The human audit protocol (`docs/human_audit_protocol_v1... |
| paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md | 56 | human-audited | \| "human-audited dataset" \| `human_audited=False` for all rows; no `audit_agreement_summary.json` \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md | 57 | human-audited | \| "human-audited validation" \| audit staged, not executed \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 15 | standalone detector | We agree that the queue is not a standalone detector (`standalone_viable = false`). We agree that the absolute precis... |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 24 | standalone detector | - **Review queue utility framing.** The manuscript states the queue is a second-stage review tool; the system is a se... |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 36 | standalone detector | We answer the reviewer as follows: the queue is explicitly a second-stage review tool, not a standalone detector. The... |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 38 | standalone detector | The safe empirical conclusion is therefore narrow: **the queue provides meaningful precision lift at the top (precisi... |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 42 | standalone detector | - The queue is not a standalone detector; `standalone_viable = false`. |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 50 | standalone detector | > "We clarify the review queue utility claim. The queue is explicitly a second-stage review tool; the system is a sec... |
| paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md | 56 | standalone detector | \| "standalone detector" \| `standalone_viable = false`; queue is second-stage only \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 1 | SOTA | # 09 — Not SOTA, Not Benchmark Response (Risk I) |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 4 | gold benchmark | **Reviewer attack:** "You do not compare against SOTA on any gold benchmark, you do not report results on SciFact/Vit... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 4 | SOTA | **Reviewer attack:** "You do not compare against SOTA on any gold benchmark, you do not report results on SciFact/Vit... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 11 | gold benchmark | The reviewer notes that the paper reports no comparison against SOTA on any gold benchmark, no results on standard cl... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 11 | SOTA | The reviewer notes that the paper reports no comparison against SOTA on any gold benchmark, no results on standard cl... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 15 | gold benchmark | We agree that the paper is not a SOTA claim on any gold benchmark. We agree that no comparison is reported against Sc... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 15 | SOTA | We agree that the paper is not a SOTA claim on any gold benchmark. We agree that no comparison is reported against Sc... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 19 | gold benchmark | - **Dataset is silver, not gold.** `docs/dataset_version_lock_v3_17.md` records `human_audited = False` for all 444 r... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 21 | gold benchmark | - **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 21 | gold benchmark | - **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 21 | human-audited | - **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 21 | SOTA | - **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 21 | automatic peer reviewer | - **Manuscript framing.** The manuscript states verbatim: "This is a controlled silver diagnostic study, not a gold b... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 22 | standalone detector | - **Pipeline scope.** The system is a second-stage review queue generator, not a standalone detector (`standalone_via... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 23 | SOTA | - **Leakage audit.** The 12-check leakage audit is structural (overlap, group leakage, claim-only collapse, shuffled-... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 24 | SOTA | - **Final gate status.** The Final Perfect State Gate does not include any SOTA or benchmark-comparison check; the ga... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 36 | gold benchmark | We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one.... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 36 | gold benchmark | We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one.... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 36 | gold benchmark | We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one.... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 36 | SOTA | We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one.... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 36 | SOTA | We answer the reviewer as follows: this paper is not a SOTA claim on any gold benchmark and is not positioned as one.... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 38 | SOTA | The safe empirical conclusion is therefore narrow: **the paper is a controlled silver diagnostic study of retrieval-t... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 38 | SOTA | The safe empirical conclusion is therefore narrow: **the paper is a controlled silver diagnostic study of retrieval-t... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 43 | SOTA | - No SOTA claim is supportable; the silver-label metrics (strong_F1 = 0.4503) are not comparable to gold-benchmark me... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 50 | gold benchmark | > "We clarify the scope of this paper. This is a controlled silver diagnostic study, not a gold benchmark, not a SOTA... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 50 | SOTA | > "We clarify the scope of this paper. This is a controlled silver diagnostic study, not a gold benchmark, not a SOTA... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 50 | SOTA | > "We clarify the scope of this paper. This is a controlled silver diagnostic study, not a gold benchmark, not a SOTA... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 50 | SOTA | > "We clarify the scope of this paper. This is a controlled silver diagnostic study, not a gold benchmark, not a SOTA... |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 56 | SOTA | \| "SOTA on simulation-claim screening" \| no gold comparison; silver labels; no SOTA claim is supportable \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 56 | SOTA | \| "SOTA on simulation-claim screening" \| no gold comparison; silver labels; no SOTA claim is supportable \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 57 | SOTA | \| "state-of-the-art" \| no gold-benchmark comparison; not a SOTA paper \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 57 | state-of-the-art | \| "state-of-the-art" \| no gold-benchmark comparison; not a SOTA paper \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 58 | gold benchmark | \| "gold benchmark" \| silver diagnostic only; `human_audited=False`; `gold_label` empty \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md | 61 | automatic peer reviewer | \| "automatic peer reviewer" \| queue is second-stage; does not replace human adjudication \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 26 | standalone detector | \| H \| Low prevalence queue: precision@20=0.35 is barely better than calibrated prior \| Medium \| Queue utility gat... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | gold benchmark | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | gold benchmark | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | SOTA | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | SOTA | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | SOTA | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 27 | SOTA | \| I \| No SOTA comparison, no gold benchmark, not a benchmark paper \| High \| Silver dataset (`human_audited=False`... |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 60 | gold benchmark | \| "gold benchmark" \| silver diagnostic only; `human_audited=False`; `gold_label` empty \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 61 | human-audited | \| "human-audited dataset" / "human-audited validation" \| audit staged, not executed \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 61 | human-audited | \| "human-audited dataset" / "human-audited validation" \| audit staged, not executed \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 62 | SOTA | \| "SOTA" / "state-of-the-art" \| no gold comparison; silver labels cannot anchor SOTA \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 62 | SOTA | \| "SOTA" / "state-of-the-art" \| no gold comparison; silver labels cannot anchor SOTA \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 62 | state-of-the-art | \| "SOTA" / "state-of-the-art" \| no gold comparison; silver labels cannot anchor SOTA \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 63 | automatic peer reviewer | \| "automatic peer reviewer" \| queue is second-stage; does not replace adjudication \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md | 64 | standalone detector | \| "standalone detector" \| `standalone_viable=false`; queue is second-stage only \| |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 13 | gold benchmark | We agree the 444-candidate set is a controlled silver diagnostic, not a gold benchmark. The dataset is locked at SHA2... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 13 | gold benchmark | We agree the 444-candidate set is a controlled silver diagnostic, not a gold benchmark. The dataset is locked at SHA2... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 13 | SOTA | We agree the 444-candidate set is a controlled silver diagnostic, not a gold benchmark. The dataset is locked at SHA2... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 37 | human-audited | We agree no human audit has been executed. The protocol (`docs/human_audit_protocol_v1.md`) defines a small targeted ... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 69 | standalone detector | We agree the queue is not a standalone detector. The queue utility gate reports `standalone_viable=false` and `second... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 69 | standalone detector | We agree the queue is not a standalone detector. The queue utility gate reports `standalone_viable=false` and `second... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 75 | SOTA | ## Snippet I — Not SOTA, not benchmark (Risk I) |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 77 | gold benchmark | We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controll... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 77 | gold benchmark | We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controll... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 77 | SOTA | We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controll... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 77 | SOTA | We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controll... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 77 | SOTA | We agree this paper is not a SOTA claim on any gold benchmark and is not positioned as one. The dataset is a controll... |
| paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md | 95 | SOTA | \| I \| Not SOTA, not benchmark \| 158 \| yes \| |
| paper_assets/v3_17_confidential/reviewer_risk_table.md | 8 | human-audited | a controlled silver diagnostic, not gold or human-audited. --> |
| paper_assets/v3_17_confidential/reviewer_risk_table.md | 28 | human-audited | set. The labels are not gold or human-audited, and results should not be |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 14 | gold benchmark | \| 444-candidate controlled silver diagnostic set \| Yes \| `docs/dataset_version_lock_v3_17.md` \| "controlled silve... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 14 | human-audited | \| 444-candidate controlled silver diagnostic set \| Yes \| `docs/dataset_version_lock_v3_17.md` \| "controlled silve... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 14 | human-audited | \| 444-candidate controlled silver diagnostic set \| Yes \| `docs/dataset_version_lock_v3_17.md` \| "controlled silve... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 16 | SOTA | \| BM25 chunk retrieval works (recall@10=0.980) \| Yes \| `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_met... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 17 | SOTA | \| BM25 sentence retrieval works (recall@10=0.948) \| Yes \| `experiments/bm25_sentence_retrieval_v1/oracle_recall_su... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 19 | SOTA | \| Frozen R4 screening strong_F1=0.4503 \| Yes \| `experiments/metric_robustness_v1/classification_metrics_with_ci.cs... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 19 | standalone detector | \| Frozen R4 screening strong_F1=0.4503 \| Yes \| `experiments/metric_robustness_v1/classification_metrics_with_ci.cs... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 21 | automatic peer reviewer | \| System is a second-stage review queue generator \| Yes (by design) \| `experiments/canonicalized_review_queue_v1/c... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 21 | standalone detector | \| System is a second-stage review queue generator \| Yes (by design) \| `experiments/canonicalized_review_queue_v1/c... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 21 | standalone detector | \| System is a second-stage review queue generator \| Yes (by design) \| `experiments/canonicalized_review_queue_v1/c... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 22 | gold benchmark | \| 12-check leakage audit PASS \| Yes \| `experiments/leakage_audit_v1/audit_summary.md` \| "12 leakage checks PASS; ... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 25 | SOTA | \| PDF extraction robustness on 12 stress docs \| Yes \| `experiments/pdf_extraction_stress_test_v1/stress_test_summa... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 25 | SOTA | \| PDF extraction robustness on 12 stress docs \| Yes \| `experiments/pdf_extraction_stress_test_v1/stress_test_summa... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 28 | human-audited | \| Human audit protocol staged \| Yes (staged, not executed) \| `docs/human_audit_protocol_v1.md`; `data/audit_templa... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 28 | human-audited | \| Human audit protocol staged \| Yes (staged, not executed) \| `docs/human_audit_protocol_v1.md`; `data/audit_templa... |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 45 | gold benchmark | - "gold benchmark" |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 46 | human-audited | - "human-audited dataset" |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 47 | human-audited | - "human-audited benchmark" |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 49 | SOTA | - "SOTA" (as a positive claim) |
| paper_assets/v3_17_confidential/submission_claims_matrix.md | 50 | automatic peer reviewer | - "automatic peer reviewer" |
| paper_assets/v3_17_confidential/submission_cover_note.md | 12 | gold benchmark | This submission is a **controlled silver diagnostic study** of retrieval-to-screening format shift in offline simulat... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 12 | human-audited | This submission is a **controlled silver diagnostic study** of retrieval-to-screening format shift in offline simulat... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 12 | SOTA | This submission is a **controlled silver diagnostic study** of retrieval-to-screening format shift in offline simulat... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 12 | automatic peer reviewer | This submission is a **controlled silver diagnostic study** of retrieval-to-screening format shift in offline simulat... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 14 | standalone detector | The system is a **second-stage review queue generator**, not a standalone detector. The queue augments human reviewer... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 18 | gold benchmark | - "This is a controlled silver diagnostic study, not a gold benchmark." |
| paper_assets/v3_17_confidential/submission_cover_note.md | 19 | standalone detector | - "The system is a second-stage review queue generator, not a standalone detector." |
| paper_assets/v3_17_confidential/submission_cover_note.md | 47 | SOTA | - No "validated general detector", "SOTA", "automatic peer reviewer", or "full CESE-OCN validation" claims |
| paper_assets/v3_17_confidential/submission_cover_note.md | 47 | automatic peer reviewer | - No "validated general detector", "SOTA", "automatic peer reviewer", or "full CESE-OCN validation" claims |
| paper_assets/v3_17_confidential/submission_cover_note.md | 55 | gold benchmark | The highest reviewer risks are: (a) misreading "silver diagnostic" as a forbidden gold-benchmark claim, (b) misreadin... |
| paper_assets/v3_17_confidential/submission_cover_note.md | 55 | standalone detector | The highest reviewer risks are: (a) misreading "silver diagnostic" as a forbidden gold-benchmark claim, (b) misreadin... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 12 | gold benchmark | 1. **Silver labels, not gold.** All 444 candidates have `human_audited=False` and `gold_label` empty. Silver labels (... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 14 | human-audited | 2. **Human audit staged, not executed.** A small targeted human audit protocol and seed queue are prepared; the audit... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 22 | SOTA | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 22 | SOTA | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 22 | automatic peer reviewer | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 36 | SOTA | - Do **not** rewrite limitation 6 as "SOTA on simulation-claim screening" or "validated general detector". |
| paper_assets/v3_17_confidential/submission_limitations_box.md | 51 | SOTA | \| 6 \| No SOTA claim \| `paper_assets/v3_17_confidential/paper_claims_checklist.md` \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 7 | gold benchmark | > **Mandatory framing.** This is a controlled silver diagnostic study, not a gold benchmark. The system is a second-s... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 7 | standalone detector | > **Mandatory framing.** This is a controlled silver diagnostic study, not a gold benchmark. The system is a second-s... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 15 | human-audited | We study this problem on a 444-candidate controlled silver diagnostic set (111 groups × 4 balanced labels: supported,... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 19 | standalone detector | We then evaluate a frozen R4 screening router (strong_F1 = 0.4503, 95% CI [0.4086, 0.4833]) and a conservative precis... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 21 | SOTA | Limitations: silver labels (not gold), no completed human audit (protocol staged, not executed), six domains only, an... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 21 | automatic peer reviewer | Limitations: silver labels (not gold), no completed human audit (protocol staged, not executed), six domains only, an... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 33 | gold benchmark | Simulation-claim review intersects three lines of prior work: (a) scientific claim verification on benchmarks such as... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 33 | human-audited | Simulation-claim review intersects three lines of prior work: (a) scientific claim verification on benchmarks such as... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 42 | gold benchmark | We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an auto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 42 | gold benchmark | We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an auto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 42 | human-audited | We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an auto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 42 | SOTA | We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an auto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 42 | automatic peer reviewer | We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an auto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 56 | standalone detector | The reviewer then adjudicates the top of the queue. **The system is a second-stage review queue generator, not a stan... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 81 | gold benchmark | **This is a controlled silver diagnostic study, not a gold benchmark.** The labels are silver (`candidate_label_guess... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 81 | human-audited | **This is a controlled silver diagnostic study, not a gold benchmark.** The labels are silver (`candidate_label_guess... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 104 | SOTA | We ran a synthetic PDF extraction stress suite of 12 documents covering stress types (caption-like text, corrupted te... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 173 | standalone detector | We rank candidates by `priority_score = p_strong_mean − p_contra_mean + 0.5 × strong_action_flag` and evaluate 8 rank... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 260 | gold benchmark | **This is a controlled silver diagnostic study, not a gold benchmark.** Silver labels (`candidate_label_guess`) are u... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 280 | human-audited | We do not claim any human-audited validation. The audit is the next planned step; results will be reported separately... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 310 | gold benchmark | 1. **Silver labels, not gold.** All 444 candidates have `human_audited=False` and `gold_label` empty. Silver labels (... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 311 | human-audited | 2. **Human audit staged, not executed.** A small targeted human audit protocol and seed queue are prepared (111 candi... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 315 | SOTA | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 315 | SOTA | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 315 | automatic peer reviewer | 6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detecto... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 337 | gold benchmark | The controlled silver diagnostic set is locked at version v3_17. Any change to the locked CSV requires updating the d... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 337 | human-audited | The controlled silver diagnostic set is locked at version v3_17. Any change to the locked CSV requires updating the d... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 349 | gold benchmark | **This is a controlled silver diagnostic study, not a gold benchmark.** The system is a second-stage review queue gen... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 349 | standalone detector | **This is a controlled silver diagnostic study, not a gold benchmark.** The system is a second-stage review queue gen... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 351 | SOTA | We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architecture ... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 351 | automatic peer reviewer | We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architecture ... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 390 | gold benchmark | - "This is a controlled silver diagnostic study, not a gold benchmark." |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 391 | standalone detector | - "The system is a second-stage review queue generator, not a standalone detector." |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 395 | SOTA | - "We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architectu... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 395 | automatic peer reviewer | - "We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architectu... |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 402 | gold benchmark | \| "gold benchmark" \| The dataset is a controlled silver diagnostic set, not a gold benchmark. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 402 | gold benchmark | \| "gold benchmark" \| The dataset is a controlled silver diagnostic set, not a gold benchmark. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 403 | human-audited | \| "human-audited dataset" \| All 444 rows have `human_audited=False`; the audit is staged, not executed. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 404 | SOTA | \| "SOTA" (as a positive claim) \| We do not claim SOTA on simulation-claim screening. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 404 | SOTA | \| "SOTA" (as a positive claim) \| We do not claim SOTA on simulation-claim screening. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 405 | automatic peer reviewer | \| "automatic peer reviewer" \| The system augments human reviewers; it is not an automatic peer reviewer. \| |
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | 405 | automatic peer reviewer | \| "automatic peer reviewer" \| The system augments human reviewers; it is not an automatic peer reviewer. \| |
| paper_assets/v3_17_confidential/tables/table5_review_queue.md | 16 | standalone detector | **Queue utility gate:** `review_queue_usable = false`, `low_prevalence_usable = true`, `standalone_viable = false`, `... |
| paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md | 17 | human-audited | **Current status:** The audit has **not been executed**. `human_audited=False` for all 444 candidates. `gold_label` i... |
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
| reports/current_project_status_v3_17.md | 36 | gold benchmark | - `CURRENT_MAINLINE.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 36 | gold benchmark | - `CURRENT_MAINLINE.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 204 | human-audited | \| Frozen R4 review queue has results \| `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.cs... |
| reports/current_project_status_v3_17.md | 209 | SOTA | \| PDF-start extraction stress test has results \| `experiments/pdf_extraction_stress_test_v1/` \| exists \| **toy** ... |
| reports/current_project_status_v3_17.md | 211 | gold benchmark | \| Human audit has results \| `experiments/human_audit_v1/audit_agreement_summary.json` \| partial \| **blocked** \| ... |
| reports/current_project_status_v3_17.md | 212 | human-audited | \| Paper assets generated \| `paper_assets/v3_17_confidential/tables/` \| exists \| **real** \| 8 tables (md+tex), 4 ... |
| reports/current_project_status_v3_17.md | 219 | SOTA | - **P0** [BLOCKED]: Clean up old narratives in docs (V2/gold/SOTA references) |
| reports/current_project_status_v3_17.md | 220 | gold benchmark | - Reason: 160 old narrative references found (majority are denials like 'not a gold benchmark') |
| reports/current_project_status_v3_17.md | 221 | gold benchmark | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 221 | human-audited | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 221 | SOTA | - Note: BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references... |
| reports/current_project_status_v3_17.md | 253 | human-audited | > All results are controlled silver diagnostic, not gold/human-audited. |
| reports/dataset_provenance_ledger_v3_17.md | 13 | gold benchmark | - not gold benchmark |
| reports/dataset_provenance_ledger_v3_17.md | 14 | human-audited | - not human-audited benchmark |
| reports/dataset_provenance_ledger_v3_17.md | 20 | human-audited | > We use a source-traceable controlled silver diagnostic set. The labels are not gold or human-audited, and results s... |
| reports/final_perfect_state_gate_v3_17.md | 110 | gold benchmark | \| 6.5 \| Never claims gold benchmark \| PASS \| P0 \| Legacy scan confirms no unsafe current claims (unsafe=0) \| |
| reports/v3_17_final_delivery_manifest.md | 3 | gold benchmark | > **Mandatory framing.** Controlled silver diagnostic study, not a gold benchmark. Not SOTA. Not an automatic peer re... |
| reports/v3_17_final_delivery_manifest.md | 3 | SOTA | > **Mandatory framing.** Controlled silver diagnostic study, not a gold benchmark. Not SOTA. Not an automatic peer re... |
| reports/v3_17_final_delivery_manifest.md | 3 | automatic peer reviewer | > **Mandatory framing.** Controlled silver diagnostic study, not a gold benchmark. Not SOTA. Not an automatic peer re... |
| reports/v3_17_final_delivery_manifest.md | 33 | human-audited | \| paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md \| true \| false \| docs/human_audit_pro... |
| reports/v3_17_final_delivery_manifest.md | 77 | SOTA | - No silver-as-gold claims; no SOTA; no automatic peer reviewer; no general detector claims. |
| reports/v3_17_final_delivery_manifest.md | 77 | automatic peer reviewer | - No silver-as-gold claims; no SOTA; no automatic peer reviewer; no general detector claims. |
| reports/v3_17_one_page_status_card.md | 3 | gold benchmark | > **Mandatory framing.** This is a **controlled silver diagnostic study**, not a gold benchmark. The system is a seco... |
| reports/v3_17_one_page_status_card.md | 3 | SOTA | > **Mandatory framing.** This is a **controlled silver diagnostic study**, not a gold benchmark. The system is a seco... |
| reports/v3_17_one_page_status_card.md | 3 | automatic peer reviewer | > **Mandatory framing.** This is a **controlled silver diagnostic study**, not a gold benchmark. The system is a seco... |
| reports/v3_17_one_page_status_card.md | 3 | standalone detector | > **Mandatory framing.** This is a **controlled silver diagnostic study**, not a gold benchmark. The system is a seco... |
| reports/v3_17_one_page_status_card.md | 39 | human-audited | - **Controlled silver diagnostic, not gold, not human-audited.** |
| reports/v3_17_one_page_status_card.md | 61 | human-audited | **STAGED, NOT EXECUTED.** A 111-candidate targeted audit packet exists (`data/private_audit/v3_17_audit_packet/audit_... |
| reports/v3_17_one_page_status_card.md | 79 | standalone detector | 5. Review queue is second-stage only; not a standalone detector and does not replace adjudication. |
| reports/v3_17_one_page_status_card.md | 93 | gold benchmark | - **Not a gold benchmark.** (silver labels, not human-audited) |
| reports/v3_17_one_page_status_card.md | 93 | human-audited | - **Not a gold benchmark.** (silver labels, not human-audited) |
| reports/v3_17_one_page_status_card.md | 94 | SOTA | - **Not SOTA** on simulation-claim screening. |
| reports/v3_17_one_page_status_card.md | 95 | automatic peer reviewer | - **Not an automatic peer reviewer.** |
| reports/v3_17_one_page_status_card.md | 98 | human-audited | - No completed human audit / no human-audited dataset claim. |

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
| reports/current_project_status_v3_17.md | 26 | gold benchmark | - `README.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 26 | gold benchmark | - `README.md`: gold benchmark — "gold benchmark" |
| reports/current_project_status_v3_17.md | 27 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 27 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 28 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 28 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 29 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 29 | human-audited | - `README.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 30 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 30 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 31 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 31 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 32 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 32 | SOTA | - `README.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 33 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 33 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 34 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 34 | automatic peer review | - `README.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 35 | full shared-threshold CESE-OCN | - `CURRENT_MAINLINE.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architect... |
| reports/current_project_status_v3_17.md | 35 | full shared-threshold CESE-OCN | - `CURRENT_MAINLINE.md`: full shared-threshold CESE-OCN as current — "full shared-threshold CESE-OCN neural architect... |
| reports/current_project_status_v3_17.md | 37 | human-audited | - `CURRENT_MAINLINE.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 37 | human-audited | - `CURRENT_MAINLINE.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 38 | SOTA | - `CURRENT_MAINLINE.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 38 | SOTA | - `CURRENT_MAINLINE.md`: SOTA — "SOTA" |
| reports/current_project_status_v3_17.md | 39 | automatic peer review | - `CURRENT_MAINLINE.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 39 | automatic peer review | - `CURRENT_MAINLINE.md`: automatic peer review — "automatic peer review" |
| reports/current_project_status_v3_17.md | 40 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 40 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 41 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 41 | human-audited | - `docs\annotation_guidelines_simclaim_eval_v1.md`: human-audited — "human-audited" |
| reports/current_project_status_v3_17.md | 42 | full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "Full shared-threshold CESE-OCN neura... |
| reports/current_project_status_v3_17.md | 42 | Full shared-threshold CESE-OCN | - `docs\current_mainline_v3_17.md`: full shared-threshold CESE-OCN as current — "Full shared-threshold CESE-OCN neura... |

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
- `docs/paper_outline_v3_17_confidential.md`
- `docs/paper_v2_reproduction_path.md`
- `docs/pdf_extraction_stress_test_v1.md`
- `docs/result_narrative_freeze_v3_17.md`
- `docs/reviewer_response_playbook_v3_17.md`
- `docs/reviewer_risk_register_v3_17.md`
- `docs/safe_claims_dictionary_v3_17.md`
- `docs/simclaim_current_data_status_lock.md`
- `docs/simclaim_eval_v1_data_status.md`
- `docs/simclaim_paper_full_data_generation_rules.md`
- `docs/tfidf_as_leakage_auditor.md`
- `paper_assets/v3_17_confidential/abstract_draft.md`
- `paper_assets/v3_17_confidential/contribution_bullets.md`
- `paper_assets/v3_17_confidential/figures/pipeline_ascii.md`
- `paper_assets/v3_17_confidential/limitations_draft.md`
- `paper_assets/v3_17_confidential/paper_claims_checklist.md`
- `paper_assets/v3_17_confidential/paper_results_summary.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/01_dataset_silver_risk_response.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/04_human_audit_pending_response.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/08_low_prevalence_review_queue_response.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/09_not_sota_not_benchmark_response.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/10_master_reviewer_response_table.md`
- `paper_assets/v3_17_confidential/reviewer_response_pack/rebuttal_snippets.md`
- `paper_assets/v3_17_confidential/reviewer_risk_table.md`
- `paper_assets/v3_17_confidential/submission_claims_matrix.md`
- `paper_assets/v3_17_confidential/submission_cover_note.md`
- `paper_assets/v3_17_confidential/submission_limitations_box.md`
- `paper_assets/v3_17_confidential/submission_manuscript_v1.md`
- `paper_assets/v3_17_confidential/tables/table5_review_queue.md`
- `paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md`
- `reports/current_project_status_v3_17.md`
- `reports/dataset_provenance_ledger_v3_17.md`
- `reports/final_perfect_state_gate_v3_17.md`
- `reports/v3_17_final_delivery_manifest.md`
- `reports/v3_17_one_page_status_card.md`
