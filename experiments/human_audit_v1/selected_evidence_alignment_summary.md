# Selected Evidence Alignment — Automatic Check (v1)

Generated: 2026-07-08T11:46:57.139775+00:00

## Disclaimer

The 111-row claim-evidence human audit was completed using evidence_text as the audit anchor. selected_evidence was not manually audited. This addendum performs an automatic text-alignment check between selected_evidence and the audited evidence_text anchor to assess evidence-selection trace coverage. The result should be interpreted as automatic trace-coverage analysis, not as human-verified selected-evidence sufficiency.

## Execution Flags

| flag | value |
|------|-------|
| selected_evidence_human_audit_executed | False |
| selected_evidence_automatic_alignment_check_executed | True |

## Metrics

| metric | value |
|--------|-------|
| n_total | 111 |
| selected_evidence_nonempty_count | 111 |
| selected_evidence_missing_or_invalid_count | 59 |
| exact_or_contained_count | 8 |
| high_overlap_count | 0 |
| partial_overlap_count | 22 |
| low_or_unrelated_count | 19 |
| conflict_candidate_count | 3 |
| selected_evidence_strong_alignment_rate | 0.0721 |
| selected_evidence_usable_alignment_rate | 0.2703 |

## Coverage Assessment

selected_evidence trace coverage/alignment is insufficient for treating selected_evidence as a reliable explanation of the model's screening decision.

## Forbidden wording

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "selected_evidence human audit passed" | not a human audit |
| "human reviewers verified selected_evidence quality" | not manually audited |
| "selected_evidence failure invalidates the claim-evidence human labels" | claim-evidence audit stands independently |
| "selected_evidence was manually audited" | automatic check only |

## Safe wording

- "automatic trace-coverage analysis, not human-verified"
- "selected_evidence alignment check (automatic)"
- "evidence-selection trace coverage is insufficient" (if applicable)

## Methodology

- Classification thresholds: high_overlap >= 0.6, partial_overlap >= 0.2
- Minimum valid selected_evidence length: 10 chars
- Similarity = max(SequenceMatcher ratio, Jaccard token similarity)
- conflict_candidate: partial+ overlap with differing key numbers
- All outputs are hash-only (SHA-256). No raw text in any output.

