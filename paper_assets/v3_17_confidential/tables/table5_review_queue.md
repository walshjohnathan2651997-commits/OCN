# Table 5 — Review Queue Ranking Variants

| Variant | precision@10 | precision@20 | precision@50 | precision@100 | recall@100 | average_precision |
|---|---|---|---|---|---|---|
| A_flag_only (baseline) | 0.40 | 0.35 | 0.36 | 0.36 | 0.330 | 0.356 |
| B_p_strong_desc | 0.40 | 0.35 | 0.32 | 0.33 | 0.303 | 0.332 |
| C_guarded_strong_score | 0.50 | 0.35 | 0.34 | 0.35 | 0.321 | 0.339 |
| D_confidence_guarded | 0.50 | 0.40 | 0.32 | 0.36 | 0.330 | 0.354 |
| E_selector_confidence | 0.40 | 0.35 | 0.36 | 0.30 | 0.275 | 0.335 |
| F_short_span_bonus | 0.40 | 0.40 | 0.32 | 0.36 | 0.330 | 0.351 |
| **G_conservative_precision** | 0.40 | **0.45** | 0.36 | 0.36 | 0.330 | 0.353 |
| H_balanced_review_score | 0.30 | 0.25 | 0.38 | 0.30 | 0.275 | 0.323 |

**Best variant:** `G_conservative_precision` (precision@20 = 0.45, +0.10 over baseline).

**Queue utility gate:** `review_queue_usable = false`, `low_prevalence_usable = true`, `standalone_viable = false`, `second_stage_viable = true`. The queue is a second-stage review tool that augments human reviewers; it is not a standalone detector.

All variants miss the strict queue-utility targets; the queue is second-stage only.

[Source: experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv; experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json; experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json]
