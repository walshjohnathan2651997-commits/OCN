# Metric Robustness Summary

Generated: 2026-07-06T06:13:08.486377+00:00

## Data Disclaimer

> **Controlled silver diagnostic data, NOT natural prevalence.**
> Metrics reflect a balanced 4-class silver pool (109 per class) and
> do NOT represent real-world claim prevalence. Confidence intervals
> reflect sampling variability within this diagnostic pool only.

- Candidates: **436**
- Groups: **109**
- Bootstrap unit: **group**

## Classification Metrics (with 95% CI)

| Metric | Point Estimate | CI Low (2.5%) | CI High (97.5%) |
|--------|---------------|---------------|-----------------|
| strong_precision | 0.3305 | 0.3008 | 0.3578 |
| strong_recall | 0.7064 | 0.6190 | 0.7798 |
| strong_F1 | 0.4503 | 0.4086 | 0.4833 |
| macro_F1 | 0.3847 | 0.3475 | 0.4240 |

## Queue Metrics (with 95% CI)

Best queue variant: **priority_score**

| Variant | Metric | K/Prev | Point Estimate | CI Low | CI High |
|---------|--------|--------|---------------|--------|---------|
| priority_score | precision_at_10 | 10 | 0.5000 | 0.2000 | 0.8000 |
| priority_score | precision_at_20 | 20 | 0.3500 | 0.2000 | 0.5500 |
| priority_score | precision_at_50 | 50 | 0.3400 | 0.2400 | 0.3905 |
| priority_score | recall_at_100 | 100 | 0.3394 | 0.2477 | 0.3761 |
| priority_score | tp_at_20 | 20 | 7 | 4.0000 | 11.0000 |
| priority_score | fp_at_20 | 20 | 13 | 9.0000 | 16.0000 |
| priority_score | fp_tp_ratio_at_0.01 | 0.01 | 1.5000 | 0.0312 | 4.0000 |
| priority_score | fp_tp_ratio_at_0.03 | 0.03 | 1.3333 | 0.4739 | 4.8917 |
| priority_score | fp_tp_ratio_at_0.05 | 0.05 | 2.1429 | 0.8333 | 4.5000 |
| priority_score | fp_tp_ratio_at_0.1 | 0.1 | 1.9333 | 1.3769 | 3.4000 |
| priority_score | fp_tp_ratio_at_0.15 | 0.15 | 2.3000 | 1.5867 | 3.2694 |
| priority_score | fp_tp_ratio_at_0.2 | 0.2 | 2.0345 | 1.4444 | 3.1000 |

## Methodology

- Bootstrap resampling: **group-aware** (target_candidate_group_id)
  - Groups are resampled with replacement; all candidates within a group
    move together to preserve intra-group correlation.
  - Fallback: candidate-level (if <2 groups available).
- true_label is used **only** for metric computation.
- Ranking/scoring uses model scores (priority_score, score_conservative, etc.).
- 95% CI computed via percentile method (2.5th and 97.5th percentiles).
