# Final Perfect-State Readiness Gate — V3.17 Confidential Lightweight

Generated: 2026-07-07T09:56:34+0000

> Read-only gate. No experiments were re-run. No results were modified.

## Executive Summary

**Final status: READY WITH LIMITATIONS**

| Metric | Count |
|---|---|
| Total checks | 44 |
| PASS | 40 |
| WARNING | 3 |
| BLOCKED | 1 |
| FAIL | 0 |

### Status logic

- No FAIL items detected.
- All BLOCKED items have documented reasons and next actions.
- WARNING items are documented limitations (not safety issues).
- The project is ready for release **with documented limitations**.

### Blocked items (documented)

| ID | Check | Reason | Next Action |
|---|---|---|---|
| 3.4 | Format shift blocked documented | sklearn_version_mismatch | Upgrade sklearn (needs network) or document as permanent limitation |

### Warning items (documented limitations)

| ID | Check | Evidence | Next Action |
|---|---|---|---|
| 6.4 | Audit not yet run (documented) | No audit dir; protocol documents audit as not complete | Execute human audit when annotators available |
| 9.1 | Redteam high risk in internal files (release excluded) | high_risk_count=3 in internal files; release_safety_gate=PASS confirms exclusion; reconciliation report present | Address high-risk findings or confirm permanent exclusion from release |
| 10.2 | Schema validation has documented failures | 36 passed, 2 failed (failures from blocked experiments) | Fix blocked experiments or document as permanent |

---

## Full Check Details

### 1. Mainline

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 1.1 | README points to V3.17 | PASS | P0 | README.md mentions V3.17 |
| 1.2 | CURRENT_MAINLINE points to V3.17 | PASS | P0 | CURRENT_MAINLINE.md mentions V3.17 |
| 1.3 | Legacy narrative unsafe=0 | PASS | P0 | unsafe=0, ambiguous=0 |


### 10. CI/Repro

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 10.1 | Toy demo passes | PASS | P0 | all_steps_success=true, 6 steps completed |
| 10.2 | Schema validation has documented failures | WARNING | P1 | 36 passed, 2 failed (failures from blocked experiments) |
| 10.3 | Pipeline runner exists | PASS | P0 | run_v3_17_confidential_pipeline.py present |
| 10.4 | Makefile/CI smoke exists | PASS | P0 | Makefile + 3 workflow(s): ['ci-nightly.yml', 'ci-smoke.yml', 'smoke.yml'] |

- **10.2 WARNING**: 36 passed, 2 failed (failures from blocked experiments) → next_action=`Fix blocked experiments or document as permanent`

### 2. Dataset

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 2.1 | Dataset lock exists | PASS | P0 | dataset_version_lock_v3_17.md present |
| 2.2 | 444 rows / 111 groups / 4 labels | PASS | P0 | Lock doc confirms 444 rows, 111 groups, 4 balanced labels |
| 2.3 | human_audited=False documented | PASS | P0 | Lock doc documents human_audited=False |
| 2.4 | gold_label empty documented | PASS | P0 | Lock doc documents gold_label is empty |
| 2.5 | Silver caveat present | PASS | P0 | Lock doc contains silver caveat |


### 3. Real Experiments

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 3.1 | BM25 real complete | PASS | P0 | n_claims=444, recall@10=0.9797297297297297 |
| 3.2 | Sentence/window BM25 complete | PASS | P0 | n_candidates=444 |
| 3.3 | Canonicalizer real complete | PASS | P0 | 8 selectors evaluated |
| 3.4 | Format shift blocked documented | BLOCKED | P0 | status=blocked, reason=sklearn_version_mismatch |
| 3.5 | Leakage audit complete | PASS | P0 | audit_summary.md reports PASS |
| 3.6 | Review queue real exists | PASS | P0 | canonicalized_r4_review_scores.csv exists |
| 3.7 | Risk ranking real exists | PASS | P0 | 8 variants |
| 3.8 | Metric robustness exists | PASS | P0 | 4 metrics with CI |
| 3.9 | Error taxonomy exists | PASS | P1 | 9 error types |

- **3.4 BLOCKED**: reason=`sklearn_version_mismatch`, next_action=`Upgrade sklearn (needs network) or document as permanent limitation`

### 4. PDF

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 4.1 | PDF extraction complete | PASS | P0 | local_pdf_corpus_chunks.csv exists |
| 4.2 | PDF stress test complete | PASS | P1 | 12 stress documents tested |
| 4.3 | Scanned PDF no-OCR boundary documented | PASS | P1 | docs/pdf_extraction_stress_test_v1.md documents scanned/OCR boundary |


### 5. Leakage

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 5.1 | Claim-only baseline exists | PASS | P0 | strong_f1=0.2448, ratio=0.5436 |
| 5.2 | Shuffled/title-only/metadata baselines exist | PASS | P0 | Baselines present: shuffled, title_only, metadata_only |
| 5.3 | no_oracle_in_selector pass | PASS | P0 | Oracle not used in selector |
| 5.4 | no_label_in_queue_sorting pass | PASS | P0 | Labels not used in queue sorting |
| 5.5 | Public outputs no sensitive text | PASS | P0 | release_safety_manifest gate=PASS, no unsafe public artifacts |


### 6. Human Audit

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 6.1 | Protocol exists | PASS | P1 | docs/human_audit_protocol_v1.md present |
| 6.2 | Template exists | PASS | P1 | human_audit_template.csv present |
| 6.3 | Queue seed exists | PASS | P1 | Redacted queue seed present |
| 6.4 | Audit not yet run (documented) | WARNING | P1 | No audit dir; protocol documents audit as not complete |
| 6.5 | Never claims gold benchmark | PASS | P0 | Legacy scan confirms no unsafe current claims (unsafe=0) |

- **6.4 WARNING**: No audit dir; protocol documents audit as not complete → next_action=`Execute human audit when annotators available`

### 7. Complexity

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 7.1 | Complexity summary exists | PASS | P1 | complexity_vs_utility_summary.md present |
| 7.2 | Contains required disclaimer | PASS | P0 | Found: 'This does not prove rules generally beat learned models' |
| 7.3 | Pareto table exists | PASS | P1 | 8 methods in Pareto table |


### 8. Paper

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 8.1 | Paper assets generated | PASS | P0 | 6 top-level + 8 tables |
| 8.2 | Claims checklist exists | PASS | P0 | paper_claims_checklist.md present |
| 8.3 | Reviewer risk register exists | PASS | P0 | reviewer_risk_register_v3_17.md present |
| 8.4 | Limitations draft exists | PASS | P0 | limitations_draft.md present |


### 9. Release

| ID | Check | Status | Priority | Evidence |
|---|---|---|---|---|
| 9.1 | Redteam high risk in internal files (release excluded) | WARNING | P0 | high_risk_count=3 in internal files; release_safety_gate=PASS confirms exclusion; reconciliation report present |
| 9.2 | Release excludes private text/PDF | PASS | P0 | No PDFs in bundle; no private artifacts in release |
| 9.3 | Artifact ledger exists | PASS | P0 | artifact_ledger_v3_17.csv present |

- **9.1 WARNING**: high_risk_count=3 in internal files; release_safety_gate=PASS confirms exclusion; reconciliation report present → next_action=`Address high-risk findings or confirm permanent exclusion from release`

---

## Scoring legend

| Status | Meaning |
|---|---|
| PASS | Complete and safe |
| WARNING | Limitation documented |
| BLOCKED | Missing input documented (with reason + next action) |
| FAIL | Unsafe or undocumented missing |

## Final status legend

| Status | Condition |
|---|---|
| READY_WITH_LIMITATIONS | No FAIL; all BLOCKED have reasons |
| NOT_READY_P0_BLOCKERS | P0 items unknown/missing without reason |
| BLOCKED_BY_PRIVATE_DATA | All issues due to private data access |
| UNSAFE_OVERCLAIM | Unsafe claims detected |