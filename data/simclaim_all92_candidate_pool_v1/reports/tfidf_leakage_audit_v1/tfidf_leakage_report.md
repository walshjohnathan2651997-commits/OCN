# TF-IDF Leakage Audit — all92 Candidate Pool

TF-IDF + LogisticRegression, GroupKFold(5) on target_candidate_group_id.

No deep models, no LLM, no data modification, no sample deletion.


## 1. How strong is claim-only TF-IDF?

| config | accuracy | macro-F1 |
|---|---|---|
| claim-only | 0.3339 | 0.3098 |
| evidence-only | 0.25 | 0.1 |
| claim+evidence | 0.3245 | 0.3192 |

### Per-class F1

| label | claim-only | evidence-only | claim+evidence |
|---|---|---|---|
| contradiction_candidate | 0.4399 | 0.4 | 0.375 |
| mild_scope_overclaim | 0.2909 | 0.0 | 0.2993 |
| strong_action_overclaim | 0.3371 | 0.0 | 0.3352 |
| supported | 0.1712 | 0.0 | 0.2672 |

## 2. Does claim+evidence improve over claim-only?

- claim-only accuracy: 0.3339
- claim+evidence accuracy: 0.3245
- delta: -0.0094 (no improvement or regression)

## 3. Which domains leak most easily?

(leak_rate = fraction of A+D: claim-only solvable)

| domain | n | claim_only_correct | claim_evidence_correct | leak_rate |
|---|---|---|---|---|
| marl | 92 | 33 | 28 | 0.3587 |
| digital_twin | 104 | 36 | 34 | 0.3462 |
| autonomous_driving | 204 | 69 | 67 | 0.3382 |
| cyber_defense | 96 | 32 | 33 | 0.3333 |
| robotics | 44 | 14 | 15 | 0.3182 |
| policy_simulation | 104 | 31 | 32 | 0.2981 |

## 4. Which evidence_types leak most easily?

| evidence_type | n | claim_only_correct | leak_rate |
|---|---|---|---|
| deployment_boundary | 24 | 11 | 0.4583 |
| limitation | 204 | 72 | 0.3529 |
| experiment_setup | 160 | 52 | 0.325 |
| metric_result | 252 | 79 | 0.3135 |
| comparison | 4 | 1 | 0.25 |

## 5. Which labels are most easily guessed by claim-only?

| label | n | claim_only_correct | claim_only_acc |
|---|---|---|---|
| contradiction_candidate | 161 | 97 | 0.6025 |
| strong_action_overclaim | 161 | 59 | 0.3665 |
| mild_scope_overclaim | 161 | 40 | 0.2484 |
| supported | 161 | 19 | 0.118 |

## 6. Samples recommended for paper-full

| recommendation | count |
|---|---|
| include (B_evidence_gain) | 44 |
| review (C_both_wrong) | 385 |
| review_flag_leakage (A_claim_only_correct) | 165 |
| exclude_flag_leakage (D_claim_only_better) | 50 |

- **include (B_evidence_gain)**: claim-only fails, evidence needed — best paper-full candidates.
- **review (C_both_wrong)**: TF-IDF cannot solve — include but flag for human review.

## 7. Samples flagged for lexical leakage risk

- **A_claim_only_correct**: claim-only already solves — possible lexical cue leakage. Flag for review, do not auto-include.
- **D_claim_only_better**: claim-only beats claim+evidence — highest leakage risk. Flag for exclusion unless human review overrides.

## Leakage category counts

| category | count |
|---|---|
| A_claim_only_correct | 165 |
| B_evidence_gain | 44 |
| C_both_wrong | 385 |
| D_claim_only_better | 50 |

## Output files

- `data\simclaim_all92_candidate_pool_v1\reports\tfidf_leakage_audit_v1\tfidf_leakage_cases.csv`
- `data\simclaim_all92_candidate_pool_v1\reports\tfidf_leakage_audit_v1\paper_full_candidate_screen_v1.csv`
- `data\simclaim_all92_candidate_pool_v1\reports\tfidf_leakage_audit_v1\tfidf_leakage_summary.json`
- `data\simclaim_all92_candidate_pool_v1\reports\tfidf_leakage_audit_v1\tfidf_leakage_report.md`