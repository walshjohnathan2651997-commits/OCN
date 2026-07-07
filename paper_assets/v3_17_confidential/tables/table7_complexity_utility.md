# Table 7 — Complexity vs Utility Pareto Analysis

Under the confidential / no-API / no-training / silver-diagnostic constraint set.

| Method | Family | Performance | Privacy | Auditability | Simplicity | Reproducibility | Utility | Pareto |
|---|---|---|---|---|---|---|---|---|
| raw_retrieval_baseline | raw_retrieval | 0.401 | 1.0 | 1.0 | 1.0 | 1.0 | 0.850 | dominated |
| **deterministic_canonicalization** | deterministic | **1.000** | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | **pareto_optimal** |
| **conservative_rule_queue** | rule_queue | **1.000** | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | **pareto_optimal** |
| **lightweight_smart_queue** | smart_queue | **1.000** | 1.0 | 1.0 | 1.0 | 1.0 | **1.000** | **pareto_optimal** |
| learned_selector_only | higher_complexity | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.762 | dominated |
| learned_ranker_only | higher_complexity | 1.000 | 1.0 | 0.5 | 0.6 | 0.5 | 0.765 | dominated |
| learned_selector_plus_learned_ranker | higher_complexity | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.762 | dominated |
| external_llm_baseline | external_llm | 0.000 | 0.0 | 0.5 | 0.6 | 0.5 | 0.265 | unavailable |

Three methods are Pareto-optimal under the constraint set: `deterministic_canonicalization`, `conservative_rule_queue`, and `lightweight_smart_queue`. Learned alternatives are dominated (match or slightly underperform on performance while losing on auditability, simplicity, and reproducibility). The external LLM baseline is unavailable under the no-API boundary.

This is a deployment-specific tradeoff. It does **not** prove that rules generally beat learned models; it shows that under this constraint set, the deterministic pipeline is Pareto-optimal.

[Source: experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv; experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv]
