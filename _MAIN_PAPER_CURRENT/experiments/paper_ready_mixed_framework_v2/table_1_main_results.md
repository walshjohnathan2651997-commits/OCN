# Table 1: Main Results

| method | flat4_macro_f1 | strong_positive_f1 | contradiction_positive_f1 | escalation_macro_f1 | strong_precision | strong_recall | recommended_use |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.3963 | 0.2408 | 0.7308 | 0.5723 | 0.3097 | 0.2062 | baseline |
| R4_conservative_strong_router (MAIN) | 0.4238 | 0.3967 | 0.7296 | 0.6143 | 0.3791 | 0.4562 | main_method |
| B_cost_sensitive_cw4.0 (AUXILIARY) | 0.4365 | 0.4221 | 0.7296 | 0.6262 | 0.4109 | 0.4625 | auxiliary_module |

- Values are means over 10 seeds (group-aware 70/15/15 split).
- R4_conservative_strong is the frozen main method (immutable).
- B_cost_sensitive_cw4.0 is auxiliary: delta vs R4 = +0.0254 (below +0.03 threshold).
- All metrics computed on silver-label pilot data, NOT gold/human-audited.
