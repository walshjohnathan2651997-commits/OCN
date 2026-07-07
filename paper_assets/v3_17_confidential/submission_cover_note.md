# Submission Cover Note — V3.17 Confidential Lightweight

**Manuscript:** Local Evidence Canonicalization for Offline Simulation-Claim Review Queues: A Controlled Silver Diagnostic Study of Retrieval-to-Screening Format Shift
**Submission manuscript draft:** `paper_assets/v3_17_confidential/submission_manuscript_v1.md`
**Final gate status:** `READY_WITH_LIMITATIONS` (PASS=42, WARNING=2, BLOCKED=0, FAIL=0)
**Generated:** 2026-07-07

---

## 1. What this submission is

This submission is a **controlled silver diagnostic study** of retrieval-to-screening format shift in offline simulation-claim review. It is **not** a gold benchmark, not a human-audited dataset, not SOTA, not a validated general detector, and not an automatic peer reviewer.

The system is a **second-stage review queue generator**, not a standalone detector. The queue augments human reviewers; it does not replace adjudication.

## 2. Mandatory framing (verbatim from manuscript)

- "This is a controlled silver diagnostic study, not a gold benchmark."
- "The system is a second-stage review queue generator, not a standalone detector."
- "Confidentiality is a deployment constraint, not the empirical contribution."
- "Format-shift R4 evaluation was completed offline using a compatible local scikit-learn environment; results are diagnostic (silver labels), not benchmark-level."

## 3. Documented limitations (acceptable for submission)

| # | Limitation | Status | Evidence |
|---|---|---|---|
| 1 | Silver labels, not gold | Documented | `human_audited=False` for all 444 rows; `gold_label` empty |
| 2 | Human audit staged, not executed | WARNING (6.4) | `docs/human_audit_protocol_v1.md` + `data/audit_templates/`; no `audit_agreement_summary.json` |
| 3 | Format-shift R4 eval completed | PASS (3.4 resolved) | `experiments/format_shift_ablation_v1/format_shift_metrics.csv`; `reports/sklearn_offline_compatibility_investigation_v3_17.md` — local scikit-learn 1.9.0 env, offline, no retraining |
| 4 | Redteam high-risk in internal files | WARNING (9.1) | 3 high-risk `forbidden_sorting_field` in internal scoring files; excluded from release bundle |
| 5 | Schema validation | PASS (10.2) | `experiments/schema_validation_summary.md` — 38/38 OK, 0 fail |

## 4. Verification rerun (Task Pack 4, STEP 5)

- `run_final_perfect_state_gate_v1.py` → PASS=42, WARNING=2, BLOCKED=0, FAIL=0
- `clean_legacy_narrative_scan_v1.py` → unsafe_current_claim=0, ambiguous=0
- `validate_experiment_outputs_v1.py` → 38/38 OK, 0 fail
- `run_confidentiality_redteam_scan_v1.py` → 3 high-risk (internal-only, excluded from release)
- `pytest tests/test_final_perfect_state_gate_v3_17.py` → 31/31 PASS

## 5. What is NOT in this submission

- No fake `format_shift_metrics.csv` (real metrics generated via offline sklearn 1.9.0 environment; `experiments/format_shift_ablation_v1/format_shift_metrics.csv`)
- No fake `audit_agreement_summary.json` (human audit staged, not executed)
- No silver relabeled as gold (`human_audited` stays False; `gold_label` stays empty)
- No raw claim/evidence/PDF text in public artifacts (hash-only public corpus)
- No "validated general detector", "SOTA", "automatic peer reviewer", or "full CESE-OCN validation" claims

## 6. Source-file traceability

All quantitative claims in the manuscript are traced to source files via `[Source: ...]` annotations at the end of each result paragraph. The full source map is in `paper_assets/v3_17_confidential/submission_result_source_map.csv`. The claims matrix is in `paper_assets/v3_17_confidential/submission_claims_matrix.md`.

## 7. Reviewer risk note

The highest reviewer risks are: (a) misreading "silver diagnostic" as a forbidden gold-benchmark claim, (b) misreading "second-stage review queue" as a forbidden standalone-detector claim, (c) misreading the completed format-shift R4 eval as benchmark-level validation rather than silver-conditional diagnostics. The manuscript and this cover note explicitly counter all three by using safe wording ("not a gold benchmark", "not a standalone detector", "diagnostic, not benchmark-level").

---

*End of cover note.*
