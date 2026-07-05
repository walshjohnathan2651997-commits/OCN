# all92 Candidate Pool QC Report

AI-preannotated candidate pool. NOT gold, NOT final, NOT human audited.


## A. File completeness

- Batches found: 20
- Batches with all 4 files: 20
- Missing/incomplete batches: 0

## B. Merge stats

| Metric | Value |
|---|---|
| accepted evidence | 161 |
| claim candidates | 644 |
| validation audit rows | 161 |
| source_id covered | 84 |
| span_id covered | 161 |
| domain covered | 6 |
| candidate groups | 161 |

### Per-domain evidence / claim counts

| domain | evidence | claims |
|---|---|---|
| autonomous_driving | 51 | 204 |
| cyber_defense | 24 | 96 |
| digital_twin | 26 | 104 |
| marl | 23 | 92 |
| policy_simulation | 26 | 104 |
| robotics | 11 | 44 |

## C. Schema check

- clean_queue schema ok: True (issues: 0)
- claim_candidates schema ok: True (issues: 0)
- validation_audit schema ok: True (issues: 0)

## D. Label check

- label issues: 0
- unique candidate_ids: 644 (of 644 claims)

## E. Forbidden field check

- human_audited / final_label / gold_label pollution found: **False**

## F. Source trace check

- source_trace_complete_true: 644
- source_trace_complete_false: 0
- source_location_empty: 0
- pdf_page_N_count: 644
- pdf_page_N_ratio: 1.0
- evidence_text_empty: 0
- url_empty: 0
- arxiv_id_empty: 0
- pdf_filename_empty: 0

## G. Leakage cue screening

| cue | hit_count |
|---|---|
| omit | 4 |
| complete | 1 |
| only | 1 |

## H. Issues summary

- total issues: 6
| issue_type | count |
|---|---|
| leakage_cue_risk | 6 |

## I. Conclusions

- Can be used as AI-preannotated candidate pool: **True**
- Can be used as gold: **NO** (not human audited, no adjudication)
- Can be used as final paper-full: **NO** — requires TF-IDF leakage audit first
- Recommended next step: TF-IDF leakage audit on claim_text across all92 pool

## Output files

- `data\simclaim_all92_candidate_pool_v1\all92_clean_evidence_merged.csv`
- `data\simclaim_all92_candidate_pool_v1\all92_claim_candidates_merged.csv`
- `data\simclaim_all92_candidate_pool_v1\all92_validation_audit_merged.csv`
- `data\simclaim_all92_candidate_pool_v1\reports\all92_candidate_pool_issues.csv`
- `data\simclaim_all92_candidate_pool_v1\reports\all92_candidate_pool_qc_report.md`
- `data\simclaim_all92_candidate_pool_v1\reports\all92_candidate_pool_qc_summary.json`