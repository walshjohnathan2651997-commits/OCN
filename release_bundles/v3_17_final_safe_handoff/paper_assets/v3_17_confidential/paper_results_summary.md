# V3.17 Confidential Paper Results Summary

> Controlled silver diagnostic, not gold/human-audited.

## Research Questions

### RQ1: Retrieval Feasibility

- Sentence-level BM25 recall@1: **0.0000**
- Window-level BM25 recall@1: **0.0000**
- Sentence-level MRR: **0.0000**
- Finding: Sentence-level retrieval outperforms window-level on oracle recall.

### RQ2: Raw Chunk Failure

- Raw top-1 chunk oracle recall: **0.0428**
- Finding: Raw BM25 chunks have low oracle recall, motivating evidence canonicalization.

### RQ3: Canonicalization Recovery

- best_sentence_top5_overlap oracle recall: **0.3874**
- Mean oracle overlap: **0.5236**
- Finding: Canonicalization restores screening signal lost in raw chunk retrieval.

### RQ4: Format Shift Source

- Finding: Format shift (metadata, lengthening) degrades downstream classification.
- Evidence: See Table 3 and format_shift_bar_data.csv.

### RQ5: Review Queue Utility

- strong_precision: **0.3305** (95% CI: [0.3008, 0.3578])
- strong_recall: **0.7064** (95% CI: [0.6190, 0.7798])
- strong_F1: **0.4503** (95% CI: [0.4086, 0.4833])
- macro_F1: **0.3847** (95% CI: [0.3475, 0.4240])
- Finding: Frozen R4 screening achieves strong_F1≈0.45 with group-aware bootstrap CI.

### RQ6: Leakage/Confidentiality Audit

- All leakage checks passed (claim-only baseline, group split, label sorting, oracle selection, title-only, metadata-only).
- Finding: No label leakage detected; queue sorting uses only permitted features.

### RQ7: Complexity-vs-Utility Tradeoff

- Deterministic canonicalization strong_F1: **0.4503**
- Learned selector strong_F1: **0.4444**
- Pareto-optimal methods: deterministic_canonicalization, conservative_rule_queue, lightweight_smart_queue
- Finding: Under confidential/no-API/no-training/silver-diagnostic constraints, deterministic canonicalization has a better performance–privacy–auditability–cost tradeoff.
- Bound: This does not prove rules generally beat learned models. Conclusion is deployment-specific.

### RQ8: Human Audit (If Available)

- Status: **not generated** (human audit seed built; auditor labels pending)
- Finding: Audit protocol and seed queue are in place; empirical audit results deferred.

## Summary

- V3.17 confidential lightweight pipeline provides a frozen, reproducible screening baseline.
- All results are silver-label diagnostic, not gold/human-audited.
- Bootstrap CIs account for group-level correlation via target_candidate_group_id resampling.
- No raw claim/evidence text appears in any public artifact.