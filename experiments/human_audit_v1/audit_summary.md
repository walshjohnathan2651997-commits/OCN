# Human Audit Summary (v1)

Generated: 2026-07-08T11:46:24.399200+00:00

Input format: bilingual Chinese (xlsx/csv)

## Disclaimer

This is a **small targeted audit, not a gold benchmark**.
Do not claim human-audited dataset.
Use it only to support directional reliability of the top
review queue and silver labels.

## Safe vs Unsafe Wording

**Safe** (allowed):
- "small targeted audit, not a gold benchmark"
- "directional reliability check on the top of the review queue"
- "auditor agreement with silver on the audited subset was X%"
- "strong_action precision in the top-20 audited subset was Y"

**Unsafe** (forbidden):
- "human-validated dataset"
- "gold benchmark"
- "the silver labels are correct"
- "the model generalizes to real claims"
- "SOTA"

## Metrics

- n_filled: 111
- n_decided (excluding uncertain): 111
- n_uncertain: 0
- n_disagreement (any): 54
- n_major_disagreement (supported vs strong axis): 2

| Metric | Value |
|--------|-------|
| silver_vs_auditor_agreement | 0.5135 |
| any_disagreement_rate | 0.4865 |
| major_disagreement_rate | 0.018 |
| uncertain_rate | 0.0 |
| strong_action_precision_in_top20 | 1.0 |
| strong_action_precision_in_top50 | 1.0 |

### Audit Execution Scope

| flag | value |
|------|-------|
| claim_evidence_human_audit_executed | True |
| selected_evidence_audit_executed | False |

**Note:** selected_evidence audit was NOT executed this round.
selected_evidence_sufficiency fields were not filled by the auditor.
Do NOT interpret the absence of selected_evidence data as:
- human label audit failure
- model label disagreement
- claim-evidence audit failure
selected_evidence coverage is an evidence-selection issue,
analyzed separately in the corpus alignment pilot.

### Evidence Consistency & Sufficiency

**selected_evidence_audit_executed = false; therefore no human-verified selected-evidence sufficiency or selected-evidence error rate is reported in the main audit summary.**

| Metric | Value |
|--------|-------|
| evidence_consistency_error_rate | 0.2613 |
| needs_second_review_rate | 0.5315 |

**evidence_consistency_distribution:**

| value | count |
|---|---|
| consistent | 31 |
| inconsistent | 29 |
| partial_consistent | 51 |

## Silver x Auditor Confusion Matrix

| silver_label | auditor_label | n |
|--------------|---------------|---|
| contradiction_candidate | contradiction_candidate | 6 |
| contradiction_candidate | mild_scope_overclaim | 2 |
| mild_scope_overclaim | contradiction_candidate | 11 |
| mild_scope_overclaim | mild_scope_overclaim | 32 |
| mild_scope_overclaim | supported | 5 |
| strong_action_overclaim | contradiction_candidate | 12 |
| strong_action_overclaim | mild_scope_overclaim | 20 |
| strong_action_overclaim | strong_action_overclaim | 2 |
| strong_action_overclaim | supported | 2 |
| supported | mild_scope_overclaim | 2 |
| supported | supported | 17 |

## Disagreement Cases (redacted, hash-only)

54 disagreement rows written to `audit_disagreement_cases_redacted.csv`. No raw text, no candidate_id, no target_candidate_group_id.

## Methodology Notes

- Agreement excludes `uncertain_insufficient_context` rows from
  the denominator, per protocol.
- Major disagreement is restricted to the
  supported vs strong_action_overclaim axis (the highest-stakes
  axis for the paper).
- Strong-action precision in top20/top50 is computed over rows
  with queue_rank <= 20 / 50 and auditor_label == 
  strong_action_overclaim. It measures whether silver also
  called these rows strong_action_overclaim. n/a if no such rows.
- All outputs are hash-only. No raw claim or evidence text is
  written by this script.
- Bilingual format detected: Chinese labels mapped to English
  internally. evidence_consistency is an auditor-assessed field
  (not raw text) and is included in redacted outputs.
- selected_evidence_sufficiency was NOT audited this round.
  The auditor did not fill 系统证据是否足够. selected_evidence
  coverage is analyzed separately in the corpus alignment pilot.
