# Complexity-vs-Utility Tradeoff Summary

Generated: 2026-07-06T17:58:16.172314+00:00

## Disclaimer

**This does not prove rules generally beat learned models.**

The tradeoff analyzed here is specific to the
confidential / no-API / no-training / silver-diagnostic setting.
Under these constraints, deterministic canonicalization has a
better tradeoff on performance, privacy, auditability, and cost
than higher-complexity variants. This is a deployment-specific
tradeoff, not a general claim about rules vs learning.

## Safe vs Unsafe Wording

**Safe** (allowed):
- "deployment-specific tradeoff"
- "under confidential/no-API constraints, deterministic
  canonicalization is preferable"
- "SmartQueue is a routing/usability layer, not a new model"
- "learned variants did not improve over frozen baseline on
  this silver diagnostic set"

**Unsafe** (forbidden):
- "simple methods generally beat intelligent methods"
- "rules beat learning"
- "BM25 beats LLMs"
- "SOTA"
- "the deterministic pipeline is optimal"

## Method Comparison

| method_id | available | strong_F1 | P@20 | R@100 | FP/TP@5% |
|-----------|-----------|-----------|------|-------|----------|
| raw_retrieval_baseline | True | 0.1806 | n/a | n/a | n/a |
| deterministic_canonicalization | True | 0.4503 | 0.4500 | 0.3303 | 11.24 |
| conservative_rule_queue | True | 0.4503 | 0.4500 | 0.3303 | n/a |
| lightweight_smart_queue | True | 0.4503 | 0.3500 | 0.3486 | n/a |
| learned_selector_only | True | 0.4444 | n/a | n/a | n/a |
| learned_ranker_only | True | 0.4503 | 0.3500 | 0.3303 | 2.00 |
| learned_selector_plus_learned_ranker | True | 0.4444 | 0.3500 | 0.3303 | 2.00 |
| external_llm_baseline | False | n/a | n/a | n/a | n/a |

## Pareto Table

Utility score is diagnostic aggregation, not a benchmark metric.

| method_id | perf | priv | audit | simple | repro | utility | pareto |
|-----------|------|------|-------|--------|-------|---------|--------|
| raw_retrieval_baseline | 0.4011 | 1.0 | 1.0 | 1.0 | 1.0 | 0.8503 | dominated |
| deterministic_canonicalization | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| conservative_rule_queue | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| lightweight_smart_queue | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| learned_selector_only | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.7617 | dominated |
| learned_ranker_only | 1.0 | 1.0 | 0.5 | 0.6 | 0.5 | 0.765 | dominated |
| learned_selector_plus_learned_ranker | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.7617 | dominated |
| external_llm_baseline | 0.0 | 0.0 | 0.5 | 0.6 | 0.5 | 0.265 | unavailable |

## Paired Bootstrap Comparisons

| comparison | metric | available | mean_a | mean_b | delta | CI95 | P(delta>0) |
|------------|--------|-----------|--------|--------|-------|------|------------|
| cmp_selector_overlap_vs_raw | selector_score | False | - | - | - | - | - |
| cmp_selector_overlap_vs_cleaned | selector_score | False | - | - | - | - | - |
| cmp_ranking_gconservative_vs_pstrong | precision_at_20 | True | 0.35 | 0.35 | -0.004 | [-0.3, 0.3] | 0.435 |
| cmp_smartqueue_conservative_vs_gconservative | precision_at_20 | True | 0.3 | 0.35 | 0.045 | [-0.3, 0.35] | 0.57 |
| cmp_learned_ranker_vs_gconservative | precision_at_20 | False | - | - | - | - | - |

## Key Findings

1. **Deterministic canonicalization** (best_sentence_top5_overlap)
   achieves strong_F1=0.4503 on the silver diagnostic set.
   Learned selector (RF) achieves 0.4444 — a -0.0059 gap — while
   requiring training, sklearn dependency, and reduced auditability.

2. **Conservative rule queue** (G_conservative_precision) achieves
   precision@20=0.45. Learned ranker (LogReg) achieves 0.35 — a
   -0.10 gap — while requiring training and group-aware splitting.

3. **SmartQueue** is a routing/usability layer (3 profiles, group
   diversity, bucket assignment). It does NOT improve precision@20
   over G_conservative_precision; it improves usability (bucket
   routing, group diversity for review fairness). If SmartQueue does
   not improve the headline metric, that is expected — it is not a
   new model.

4. **External LLM baseline** is listed for tradeoff reference but
   was NOT run (no-API guard). It would require data to leave the
   machine, breaking confidentiality.

## What This Does NOT Show

- Does NOT show rules generally beat learned models.
- Does NOT show BM25 beats LLMs.
- Does NOT show the deterministic pipeline is optimal.
- Does NOT claim SOTA.
- Does NOT generalize beyond the confidential/silver-diagnostic setting.

The conclusion is a **deployment-specific tradeoff**: under the
constraints of this project (no API, no training of new production
models, no data leaving the machine, silver diagnostic data),
deterministic canonicalization + conservative rule queue + SmartQueue
routing provides the best balance of performance, privacy,
auditability, and reproducibility.
