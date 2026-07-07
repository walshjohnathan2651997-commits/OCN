# 08 — Low Prevalence Review Queue Response (Risk H)

**Risk ID:** H
**Reviewer attack:** "The review queue has precision@10 = 0.50, precision@20 = 0.35, recall@100 = 0.330. This is a low-prevalence screening setting; the queue looks barely better than a calibrated prior. Why is this a useful contribution?"
**Severity:** Medium

---

## 1. Reviewer concern

The reviewer notes that the review queue's precision and recall are modest in absolute terms and that the queue is explicitly described as second-stage-only (`standalone_viable = false`). The reviewer may suspect that the queue is not a meaningful improvement over a calibrated label-prior baseline, that the low-prevalence setting makes the queue trivial, or that the "second-stage-only" framing is a hedge to avoid reporting weak standalone performance.

## 2. What we agree with

We agree that the queue is not a standalone detector (`standalone_viable = false`). We agree that the absolute precision and recall are modest. We agree that in a low-prevalence screening setting, queue precision is constrained by base rates and cannot be compared directly to balanced-classification metrics. We do not contest that a reviewer is entitled to ask whether the queue provides meaningful lift over a calibrated prior.

## 3. Evidence we have

- **Queue utility gate.** `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` reports `second_stage_viable = true`, `standalone_viable = false`, `strong_f1 = 0.4503`, `strong_recall = 0.706`, `strong_precision = 0.330`, `n_eval = 436`. The queue is explicitly designed to augment human reviewers, not to replace adjudication.
- **Risk ranking variants.** `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` reports the best variant is `G_conservative_precision` with `precision@20 = 0.45` (vs 0.35 baseline, +0.10) and `recall@100 = 0.330` (negligible cost vs 0.330 baseline). All 8 variants miss the strict queue-utility targets; the queue is second-stage-only.
- **Queue precision curve.** precision@10 = 0.50, precision@20 = 0.35, precision@50 = 0.34. The curve is consistent with a low-prevalence screening setting where the top of the queue is enriched but the tail regresses toward the base rate.
- **Conservative precision optimization.** `G_conservative_precision` improves precision@20 by +0.10 over the `A_flag_only` baseline (0.45 vs 0.35) at negligible recall cost (recall@100 = 0.330 vs 0.330). This is a meaningful lift in a low-prevalence setting where every percentage point of precision at the top of the queue reduces reviewer load.
- **Error taxonomy.** `experiments/error_taxonomy_v1/error_taxonomy_summary.csv` shows the dominant error types are boundary errors (mild_vs_strong_boundary = 38.83%, weak_selector_overlap = 34.57%, supported_overflag = 32.98%); the queue does not fail by missing strong cases (strong_recall = 0.706) but by overflagging boundary cases.
- **Review queue utility framing.** The manuscript states the queue is a second-stage review tool; the system is a second-stage review queue generator, not a standalone detector.

## 4. Evidence file

- `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json`
- `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json`
- `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv`
- `experiments/error_taxonomy_v1/error_taxonomy_summary.csv`
- `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`

## 5. Safe response

We answer the reviewer as follows: the queue is explicitly a second-stage review tool, not a standalone detector. The conservative precision-optimized variant (`G_conservative_precision`) improves precision@20 from 0.35 to 0.45 (+0.10) at negligible recall cost, which is a meaningful lift in a low-prevalence screening setting where the top of the queue drives reviewer load. The absolute precision and recall are modest because the setting is low-prevalence and the labels are silver; the queue is designed to augment human reviewers, not to replace adjudication. The error taxonomy shows the queue overflags boundary cases rather than missing strong cases (strong_recall = 0.706), which is the desired failure mode for a review queue (false positives are cheap; false negatives are expensive).

The safe empirical conclusion is therefore narrow: **the queue provides meaningful precision lift at the top (precision@20 = 0.45 vs 0.35 baseline) in a low-prevalence screening setting, and is viable as a second-stage review tool (`second_stage_viable = true`). It is not a standalone detector (`standalone_viable = false`) and does not replace human adjudication. All precision and recall numbers are silver-conditional diagnostics and may shift under human audit.**

## 6. Remaining limitation

- The queue is not a standalone detector; `standalone_viable = false`.
- Absolute precision is modest (precision@20 = 0.45, precision@50 = 0.34); the queue enriches the top but regresses toward the base rate in the tail.
- All 8 ranking variants miss the strict queue-utility targets; the queue is second-stage-only by design and by empirical performance.
- The precision lift (+0.10 at k=20) is measured on silver labels; under human adjudication the lift could shrink, especially if the mild-vs-strong boundary (38.83% of errors) shifts.
- The low-prevalence setting means precision is bounded by base rates; the queue cannot achieve high absolute precision without a stronger screening signal, which is blocked by the no-API/no-training constraint.

## 7. Paper text to add

> "We clarify the review queue utility claim. The queue is explicitly a second-stage review tool; the system is a second-stage review queue generator, not a standalone detector (`standalone_viable = false`, `second_stage_viable = true`). The conservative precision-optimized variant (`G_conservative_precision`) improves precision@20 from 0.35 (baseline) to 0.45 (+0.10) at negligible recall cost (recall@100 = 0.330 vs 0.330), which is a meaningful lift in a low-prevalence screening setting where the top of the queue drives reviewer load. The absolute precision and recall are modest (precision@10 = 0.50, precision@20 = 0.35, precision@50 = 0.34) because the setting is low-prevalence and the labels are silver. The error taxonomy shows the queue overflags boundary cases (mild_vs_strong_boundary = 38.83% of errors) rather than missing strong cases (strong_recall = 0.706), which is the preferred failure mode for a review queue. All precision and recall numbers are silver-conditional diagnostics and may shift under human audit."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "standalone detector" | `standalone_viable = false`; queue is second-stage only |
| "the queue replaces human reviewers" | queue augments reviewers; does not replace adjudication |
| "high-precision screening" | precision@20 = 0.45, precision@50 = 0.34; modest in absolute terms |
| "the queue solves the low-prevalence problem" | queue provides lift but does not solve the base-rate constraint |
| "the queue is validated for deployment" | silver-conditional diagnostics only; no human audit; no deployment validation |

---

*End of response 08.*
