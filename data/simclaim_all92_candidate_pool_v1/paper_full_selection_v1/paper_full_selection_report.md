# Paper-full v1 Candidate Selection Report

Built from TF-IDF leakage audit. NOT gold, NOT final, NOT human audited.


## 1. Core candidates count

- core candidates: **200** (target ~200)
- B_evidence_gain in core: **44**
- C_both_wrong sampled into core: **156**

## 2. A/D flagged counts

- A_claim_only_correct (lexical_leakage_risk): **165**
- D_claim_only_better (exclude_recommended): **50**
- contradiction_leakage_review flagged: **97**
- high-risk cue samples: **6**

## 3. Review queue / exclude

- review queue: **581**
- exclude recommended: **56**

## 4. Core domain distribution

| domain | count |
|---|---|
| autonomous_driving | 64 |
| policy_simulation | 34 |
| cyber_defense | 31 |
| digital_twin | 31 |
| marl | 26 |
| robotics | 14 |

## 5. Core label distribution

| label | count |
|---|---|
| supported | 73 |
| mild_scope_overclaim | 56 |
| strong_action_overclaim | 48 |
| contradiction_candidate | 23 |

## 6. Why this is NOT gold / final

- **Not gold**: no human adjudication, no double-annotation, no agreement metrics.
- **Not final**: candidate_label_guess is AI preannotation only; final_label and gold_label are empty; human_audited is false on all samples.
- TF-IDF audit is a lexical-leakage screen, not a validity check.

## 7. Next step

1. Small-scale human review of core candidates (focus on B_evidence_gain first).
2. Review flagged A/D samples and contradiction_leakage_review samples.
3. After human adjudication, run model experiments on the adjudicated subset.

## Output files

- `data\simclaim_all92_candidate_pool_v1\paper_full_selection_v1\paper_full_core_candidates_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_selection_v1\paper_full_review_queue_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_selection_v1\paper_full_exclude_recommended_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\paper_full_selection_v1\paper_full_selection_summary.json`
- `data\simclaim_all92_candidate_pool_v1\paper_full_selection_v1\paper_full_selection_report.md`