# OCN v3.17 Final Archive Handoff

**Status:** ARCHIVED — mainline frozen for OCN/CESE-OCN R4 v3.17.
**Archive branch:** `archive/ocn-v3-17-final`
**Tag:** `ocn-v3-17-audit-final`
**Date:** 2026-07-08

---

## 1. Purpose

This document freezes the OCN v3.17 mainline after completion of the
111-row claim-evidence human audit and the selected_evidence automatic
alignment addendum. The mainline is preserved as an archive; no further
experiment or audit changes are expected on this branch.

R4 should be framed as an evidence-canonicalized second-stage screener,
not a standalone classifier.

---

## 2. Audit Execution Scope

| flag | value |
|------|-------|
| claim_evidence_human_audit_executed | true |
| n_audited | 111 |
| selected_evidence_audit_executed | false |
| selected_evidence_automatic_alignment_check_executed | true |

The 111-row human audit evaluated `claim_text` vs `evidence_text` only.
`selected_evidence` was not manually audited. The automatic alignment
check is a text-overlap analysis, not a human-verified sufficiency audit.

---

## 3. Key Commits

| commit | description |
|--------|-------------|
| `285feb5` | audit: summarize claim-evidence human audit without selected evidence audit |
| `79211e9` | audit: add selected evidence automatic alignment addendum |

---

## 4. Claim-Evidence Human Audit Summary (N=111)

| metric | value |
|--------|-------|
| silver_vs_auditor_agreement | 0.5135 |
| major_disagreement_rate | 0.018 |
| strong_action_precision_in_top20 | 1.0 |
| strong_action_precision_in_top50 | 1.0 |
| evidence_consistency_error_rate | 0.2613 |
| needs_second_review_rate | 0.5315 |

The `evidence_consistency_error_rate` is derived from the `证据是否一致`
(claim-evidence audit) field. It is NOT a selected_evidence human audit
result. `selection_error_rate` is kept as a deprecated alias with the
same value; do not interpret it as selected_evidence human-verified error.

---

## 5. Selected Evidence Automatic Alignment (N=111)

This is an automatic text-alignment check, NOT a human audit.

| metric | value |
|--------|-------|
| selected_evidence_nonempty_count | 111 |
| selected_evidence_missing_or_invalid_count | 59 |
| exact_or_contained_count | 8 |
| high_overlap_count | 0 |
| partial_overlap_count | 22 |
| low_or_unrelated_count | 19 |
| conflict_candidate_count | 3 |
| selected_evidence_strong_alignment_rate | 0.0721 |
| selected_evidence_usable_alignment_rate | 0.2703 |

**Coverage assessment:** selected_evidence trace coverage/alignment is
insufficient for treating selected_evidence as a reliable explanation of
the model's screening decision.

The result should be interpreted as automatic trace-coverage analysis,
not as human-verified selected-evidence sufficiency.

---

## 6. Final Gate Status

| status | count |
|--------|-------|
| PASS | 43 |
| WARNING | 1 |
| BLOCKED | 0 |
| FAIL | 0 |

The remaining WARNING is for the staged-but-not-executed selected_evidence
human audit (optional; not required for the claim-evidence audit conclusion).

---

## 7. Private Data Handling

- Private audit xlsx/csv files were NOT committed to the repository.
- `data/private_audit/v3_17_audit_packet/*.xlsx` and `*.csv` are gitignored.
- No raw `claim_text`, `evidence_text`, or `selected_evidence` text appears
  in any committed output file.
- All public outputs use SHA-256 hashes only; no raw text columns.

---

## 8. Forbidden Wording (do not use in any derived document)

| forbidden wording | why forbidden |
|---|---|
| "R4 is a validated standalone classifier" | R4 is a second-stage screener, not a standalone classifier |
| "selected_evidence was human verified" | selected_evidence was not manually audited |
| "selected_evidence provides reliable explanations" | trace coverage insufficient; not reliable |
| "selected_evidence human audit passed" | not a human audit |
| "selected_evidence failure invalidates the claim-evidence human labels" | claim-evidence audit stands independently |

---

## 9. Safe Wording

- "R4 is an evidence-canonicalized second-stage screener"
- "automatic trace-coverage analysis, not human-verified"
- "selected_evidence alignment check (automatic)"
- "selected_evidence trace coverage/alignment is insufficient"
- "claim-evidence human audit (N=111), selected_evidence not audited"

---

## 10. Archive Access

- **Archive branch:** `archive/ocn-v3-17-final` (pushed to origin)
- **Tag:** `ocn-v3-17-audit-final` (pushed to origin)
- **Main branch:** `main` at commit `79211e9` (or later doc-only commits)

To checkout the archive:
```
git checkout archive/ocn-v3-17-final
# or
git checkout ocn-v3-17-audit-final
```
