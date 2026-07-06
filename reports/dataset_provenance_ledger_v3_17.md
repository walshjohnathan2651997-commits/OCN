# Dataset Provenance Ledger — V3.17

**Generated (UTC):** 2026-07-06T20:04:13.113207+00:00
**Ledger version:** v3_17
**Dataset:** SimClaim Strict Silver Diagnostic Set v1

## Role

controlled silver diagnostic set for retrieval-to-screening format shift

## Not

- not gold benchmark
- not human-audited benchmark
- not natural prevalence dataset
- not general scientific claim benchmark

## Safe caveat

> We use a source-traceable controlled silver diagnostic set. The labels are not gold or human-audited, and results should not be interpreted as benchmark-level model validation.

## Source CSV

| Field | Value |
|---|---|
| Path (repo-relative) | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| Size (bytes) | 448144 |
| SHA256 | `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812` |
| mtime (UTC) | 2026-07-02T04:40:34.878117+00:00 |
| Row count | 444 |
| Column count | 36 |

## Statistics

| Statistic | Value |
|---|---|
| rows | 444 |
| groups | 111 |
| human_audited_true | 0 |
| human_audited_false | 444 |
| final_label_nonempty | 0 |
| gold_label_nonempty | 0 |
| source_trace_complete_true | 444 |
| source_trace_complete_false | 0 |
| groups_with_four_labels_complete | 111 |
| groups_missing_labels | 0 |
| evidence_text_sha256_unique | 111 |
| evidence_text_sha256_duplicates | 333 |
| claim_text_sha256_unique | 444 |
| claim_text_sha256_duplicates | 0 |

### candidate_label_guess counts

| Label | Count |
|---|---|
| contradiction_candidate | 111 |
| mild_scope_overclaim | 111 |
| strong_action_overclaim | 111 |
| supported | 111 |

### domain counts

| Domain | Count |
|---|---|
| autonomous_driving | 140 |
| policy_simulation | 84 |
| digital_twin | 68 |
| cyber_defense | 64 |
| marl | 52 |
| robotics | 36 |

### silver_label_source counts

| Source | Count |
|---|---|
| candidate_label_guess | 444 |

### claim_generation_policy counts

| Policy | Count |
|---|---|
| simclaim_ai_preannotated_candidates_no_gold_no_final_label | 196 |
| simclaim_candidate_v1 | 56 |
| simclaim_four_variant_v1 | 40 |
| four_label_simclaim_candidate_generation_no_gold_no_final_no_human_audit | 36 |
| four_label_ai_preannotation_clean_evidence_only | 36 |
| four_label_balanced_candidate_generation | 32 |
| same_frame_four_variant_generation | 24 |
| four_label_simclaim_candidate_generation_v1_strict_no_gold | 12 |
| four_label_balanced_ai_preannotation_clean_evidence_only | 12 |

### human_audited counts

| Value | Count |
|---|---|
| False | 444 |

### annotation_status counts

| Value | Count |
|---|---|
| ai_preannotated | 444 |

### dataset_role counts

| Value | Count |
|---|---|
| strict_silver_train_candidate | 444 |

### group_quality_tier counts

| Tier | Count |
|---|---|
| tier1_B_no_A | 32 |
| tier2_B_has_A | 52 |
| tier3_no_B_no_A | 20 |
| tier4_no_B_has_A | 340 |

### leakage_category counts

| Category | Count |
|---|---|
| C_both_wrong | 294 |
| A_claim_only_correct | 127 |
| B_evidence_gain | 23 |

## Invariants

| Invariant | Holds |
|---|---|
| human_audited_all_false | PASS |
| gold_label_all_empty | PASS |
| final_label_all_empty | PASS |
| source_trace_complete_all_true | PASS |
| silver_label_source_all_candidate_label_guess | PASS |
| four_labels_each_111 | PASS |
| row_count_444 | PASS |
| groups_111 | PASS |
| evidence_text_sha256_unique_is_111 | PASS |
| claim_text_sha256_unique_is_444 | PASS |

## Schema (columns)

```
candidate_id, target_candidate_group_id, span_id, source_id, domain, title, url, arxiv_id, pdf_filename, page_number, source_location, evidence_type, evidence_text, evidence_text_sha256, candidate_label_guess, issue_binary_label_guess, escalation_binary_label_guess, contradiction_binary_label_guess, claim_text, claim_text_sha256, claim_generation_status, claim_generation_policy, annotation_status, human_audited, final_label, gold_label, source_trace_complete, generation_notes, leakage_category, claim_only_correct, claim_evidence_correct, lexical_leakage_risk, exclude_recommended, group_quality_tier, silver_label_source, dataset_role
```

## Redaction note

Fields listed in redacted_fields_present_in_csv exist in the source CSV but their raw values are NEVER copied into this ledger. Only SHA256 hashes and aggregate counts are emitted.

Redacted fields present in source CSV (values NOT emitted in this ledger):

- `claim_text`
- `evidence_text`
- `generation_notes`
- `title`
- `url`
