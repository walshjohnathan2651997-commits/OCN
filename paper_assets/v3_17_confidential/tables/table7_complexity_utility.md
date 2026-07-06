| Method | Family | Available | strong_F1 | P@20 | R@100 | deterministic | auditable |
|---|---|---|---|---|---|---|---|
| raw_retrieval_baseline | raw_retrieval | True | 0.1806 |  |  | True | True |
| deterministic_canonicalization | deterministic_canonicalization | True | 0.4503 | 0.4500 | 0.3303 | True | True |
| conservative_rule_queue | rule_queue | True | 0.4503 | 0.4500 | 0.3303 | True | True |
| lightweight_smart_queue | smart_queue | True | 0.4503 | 0.3500 | 0.3486 | True | True |
| learned_selector_only | higher_complexity | True | 0.4444 |  |  | False | False |
| learned_ranker_only | higher_complexity | True | 0.4503 | 0.3500 | 0.3303 | False | False |
| learned_selector_plus_learned_ranker | higher_complexity | True | 0.4444 | 0.3500 | 0.3303 | False | False |
| external_llm_baseline | external_llm | False |  |  |  | False | False |

*Controlled silver diagnostic, not gold/human-audited.*

**Pareto scores** (utility = diagnostic aggregation, not a benchmark metric):

| Method | perf | priv | audit | simple | repro | utility | pareto |
|---|---|---|---|---|---|---|
| raw_retrieval_baseline | 0.4011 | 1.0 | 1.0 | 1.0 | 1.0 | 0.8503 | dominated |
| deterministic_canonicalization | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| conservative_rule_queue | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| lightweight_smart_queue | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | 1.0 | pareto_optimal |
| learned_selector_only | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.7617 | dominated |
| learned_ranker_only | 1.0 | 1.0 | 0.5 | 0.6 | 0.5 | 0.765 | dominated |
| learned_selector_plus_learned_ranker | 0.987 | 1.0 | 0.5 | 0.6 | 0.5 | 0.7617 | dominated |
| external_llm_baseline | 0.0 | 0.0 | 0.5 | 0.6 | 0.5 | 0.265 | unavailable |