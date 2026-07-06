# Dataset Version Lock — V3.17

**Authority:** This document is the immutable version lock for the
SimClaim Strict Silver Diagnostic Set v1. Any change to the locked
CSV (content, row count, schema, or SHA256) requires explicitly
updating this document and bumping the version. If a future data edit
is made without updating this lock, the integrity test
`tests/test_dataset_version_lock_v3_17.py` will fail.

**Scope:** V3.17 Confidential Lightweight mainline only. Does not
apply to legacy V2 pilot data, future gold-augmented sets, or external
benchmarks (SciFact/VitaminC).

---

## Dataset name

SimClaim Strict Silver Diagnostic Set v1

## Role

Controlled silver diagnostic set for retrieval-to-screening format
shift. Each group contains four label variants (supported,
mild_scope_overclaim, strong_action_overclaim, contradiction_candidate)
sharing the same source evidence, enabling controlled study of how
retrieval-to-screening format shifts affect label preservation.

## Not

This dataset is **not**:

- **Not** a gold benchmark.
- **Not** a human-audited benchmark.
- **Not** a natural prevalence dataset.
- **Not** a general scientific claim benchmark.

## Safe caveat (paper-use)

> We use a source-traceable controlled silver diagnostic set. The
> labels are not gold or human-audited, and results should not be
> interpreted as benchmark-level model validation.

---

## Locked artifact

| Field | Value |
|---|---|
| CSV path (repo-relative) | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| File size (bytes) | 448144 |
| SHA256 | `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812` |
| File mtime (UTC) | 2026-07-02T04:40:34.878117+00:00 |
| Locked on (UTC) | 2026-07-07 |
| Lock version | v3_17 |
| Column count | 36 |
| Row count | 444 |
| Group count (`target_candidate_group_id` unique) | 111 |

## Label distribution (`candidate_label_guess`)

| Label | Count |
|---|---|
| supported | 111 |
| mild_scope_overclaim | 111 |
| strong_action_overclaim | 111 |
| contradiction_candidate | 111 |
| **Total** | **444** |

Each of the 111 groups contains exactly one candidate per label
(4 × 111 = 444). Groups with fewer than four labels were excluded at
strict-silver construction time (see `strict_silver_max_report.md`).

## Domain distribution

| Domain | Count |
|---|---|
| autonomous_driving | 140 |
| policy_simulation | 84 |
| digital_twin | 68 |
| cyber_defense | 64 |
| marl | 52 |
| robotics | 36 |
| **Total** | **444** |

## Group quality tier distribution

| Tier | Groups | Candidates |
|---|---|---|
| tier4_no_B_has_A | 85 | 340 |
| tier2_B_has_A | 13 | 52 |
| tier1_B_no_A | 8 | 32 |
| tier3_no_B_no_A | 5 | 20 |
| **Total** | **111** | **444** |

## Leakage category distribution

| Category | Count |
|---|---|
| C_both_wrong | 294 |
| A_claim_only_correct | 127 |
| B_evidence_gain | 23 |

## Critical field invariants

These invariants are enforced by `tests/test_dataset_version_lock_v3_17.py`.
If any invariant fails, the dataset has been modified and this lock
document must be explicitly updated.

| Field | Expected value | Count |
|---|---|---|
| `human_audited` | `False` | 444 |
| `gold_label` nonempty | 0 | 0 |
| `final_label` nonempty | 0 | 0 |
| `source_trace_complete` | `True` | 444 |
| `silver_label_source` | `candidate_label_guess` | 444 |
| `annotation_status` | `ai_preannotated` | 444 |
| `dataset_role` | `strict_silver_train_candidate` | 444 |

## Hash uniqueness

| Hash field | Unique | Total | Duplicates | Notes |
|---|---|---|---|---|
| `evidence_text_sha256` | 111 | 444 | 333 | Expected: 4 claims per group share the same source evidence |
| `claim_text_sha256` | 444 | 444 | 0 | All claims are unique |

## Claim generation policy distribution

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

## Schema (36 columns)

```
candidate_id, target_candidate_group_id, span_id, source_id, domain,
title, url, arxiv_id, pdf_filename, page_number, source_location,
evidence_type, evidence_text, evidence_text_sha256,
candidate_label_guess, issue_binary_label_guess,
escalation_binary_label_guess, contradiction_binary_label_guess,
claim_text, claim_text_sha256, claim_generation_status,
claim_generation_policy, annotation_status, human_audited,
final_label, gold_label, source_trace_complete, generation_notes,
leakage_category, claim_only_correct, claim_evidence_correct,
lexical_leakage_risk, exclude_recommended, group_quality_tier,
silver_label_source, dataset_role
```

Fields `evidence_text` and `claim_text` are present in the CSV for
diagnostic purposes but **must not** be copied into public reports,
release bundles, or paper assets. The redaction is enforced by
`scripts/run_confidentiality_redteam_scan_v1.py` and
`tests/test_no_private_text_in_public_outputs.py`.

---

## Known limitations

1. **Silver, not gold.** Labels are AI-preannotated
   (`annotation_status=ai_preannotated`) and have not been verified by
   human annotators. They are not appropriate for benchmark-level
   model validation.

2. **Not human-audited.** `human_audited=False` for all 444 rows. The
   small targeted human audit (Task Pack D) covered only 111 redacted
   seeds and did not produce gold labels.

3. **Not natural prevalence.** The dataset is artificially balanced
   (4 × 111) to support controlled format-shift study. Label
   proportions do not reflect real-world claim distributions.

4. **Controlled evidence sharing.** Within each group, the four
   label variants share the same source evidence. This is by design
   (controlled silver diagnostic) but means evidence-hash uniqueness
   is 111, not 444.

5. **Domain coverage is narrow.** Six domains
   (autonomous_driving, policy_simulation, digital_twin,
   cyber_defense, marl, robotics). Results should not be generalized
   to other scientific domains.

6. **PDF corpus dependency.** Some downstream experiments
   (BM25 retrieval, format-shift ablation on retrieved evidence)
   require the PDF sentence corpus
   (`data/pdf_corpus_v1/sentences.jsonl`), which is currently missing.
   This does not affect the locked CSV itself.

7. **No final/gold labels.** `final_label` and `gold_label` are empty
   for all rows by design. Filling these fields would violate the
   V3.17 hard boundary and invalidate this lock.

8. **Lexical leakage risk flagged but low.** 50 groups were excluded
   at construction time for cue risk (`exclude_recommended=True` on
   excluded rows). The locked 444 rows all have
   `exclude_recommended=False`.

---

## Change policy

If the locked CSV must be modified (e.g., to add a new column, fix a
data error, or incorporate human audit results):

1. **Bump the version** in this document (e.g., v1 → v2) and create a
   new lock document (`docs/dataset_version_lock_v3_17_v2.md`).
2. **Recompute SHA256, row count, group count, label counts, domain
   counts** and update all tables in this document.
3. **Update `tests/test_dataset_version_lock_v3_17.py`** with the new
   expected values.
4. **Regenerate the provenance ledger** by running
   `scripts/build_dataset_provenance_ledger_v1.py`.
5. **Document the change** in a commit message and update
   `reports/current_project_status_v3_17.md`.

Silent edits to the CSV without bumping the version are forbidden and
will cause the integrity test to fail.

---

## Related artifacts

- Provenance ledger: `reports/dataset_provenance_ledger_v3_17.json`,
  `reports/dataset_provenance_ledger_v3_17.md`,
  `reports/dataset_schema_summary_v3_17.csv`
- Provenance ledger generator: `scripts/build_dataset_provenance_ledger_v1.py`
- Integrity test: `tests/test_dataset_version_lock_v3_17.py`
- Original construction report: `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_report.md`
- Original construction summary: `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_summary.json`
- Safe claims dictionary: `docs/safe_claims_dictionary_v3_17.md`
- Current mainline: `docs/current_mainline_v3_17_confidential.md`
