# Leakage Audit Summary

Generated: 2026-07-06T17:36:51.054425+00:00

## Overall Status: **PASS**

**Strongest leakage concern**: none

  (no significant concern detected)

## What This Means for Paper Wording

**Safe wording** (allowed):
- "controlled silver diagnostic"
- "silver-labeled retrieval-to-screening diagnostic"
- "not a gold benchmark"
- "not human-audited"
- "not a validated general detector"

**Unsafe wording** (forbidden):
- "gold benchmark"
- "validated general detector"
- "human-audited"
- "SOTA"
- "generalizes to real claims"

If overall status is WARNING or FAIL, the dataset shows evidence of
shortcuts or label contingencies. R4 results on this set should be
interpreted as diagnostic (does the pipeline run end-to-end?), not as
generalization performance.

## Check Results

| # | Check | Status | Key Metric |
|---|-------|--------|------------|
| 1 | Claim-only baseline (TF-IDF+LR) | pass | strong_F1=0.2448 (ratio to R4=0.5436) |
| 2 | Empty evidence baseline | pass | correct_overlap=0.361437 |
| 3 | Shuffled evidence baseline | pass | correct=0.361437, shuffled=0.007867 |
| 4 | Title-only retrieval | pass | mean_overlap=0.042765 |
| 5 | Metadata-only retrieval | pass | purity=0.25 |
| 6 | Lexical overlap by label | pass | overlap_ratio=1.3444 |
| 7 | Cue words by label | pass | max_cue_ratio=1.6075 |
| 8 | Label lexical cues | pass | max_cues=0 |
| 9 | Group split integrity | pass | cross_groups=0 |
| 10 | Generation policy distribution | pass | max_concentration=0.25 |
| 11 | No oracle in selector | pass |  |
| 12 | No label in queue sorting | skip |  |

## Forbidden Fields (selector)

- candidate_label_guess
- final_label
- gold_label
- human_audited
- oracle_hit
- true_label

## Forbidden Fields (queue sorting)

- candidate_label_guess
- evidence_text
- evidence_text_sha256
- final_label
- gold_label
- human_audited
- is_strong_action
- oracle_hit
- true_label

## Methodology Notes

- claim-only baseline uses TF-IDF (unigram+bigram, 5000 features) +
  LogisticRegression with GroupKFold (group-aware cross-validation).
- Evidence sanity baselines use Jaccard token overlap as a proxy for
  screening utility (frozen R4 eval is blocked by sklearn version mismatch).
- Cue word rates are computed against fixed heuristic word lists
  (action, certainty, deployment, safety). These are diagnostic, not
  comprehensive.
- Policy-label concentration tests whether certain generation policies
  are biased toward certain labels (expected: 25% for balanced 4-label).
