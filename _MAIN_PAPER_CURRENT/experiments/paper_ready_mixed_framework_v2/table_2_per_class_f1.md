# Table 2: Per-Class F1 (baseline vs R4)

| class | baseline_f1 | baseline_std | r4_f1 | r4_std | delta |
| --- | --- | --- | --- | --- | --- |
| supported | 0.4492 | 0.0600 | 0.4424 | 0.1194 | -0.0069 |
| mild_scope_overclaim | 0.1644 | 0.1168 | 0.1266 | 0.1366 | -0.0378 |
| strong_action_overclaim | 0.2408 | 0.0640 | 0.3967 | 0.0441 | 0.1559 |
| contradiction_candidate | 0.7308 | 0.1031 | 0.7296 | 0.0809 | -0.0012 |

- Per-class F1 computed from frozen_r4_routing_results_by_seed.csv (10 seeds).
- strong_action_overclaim shows the largest gain (R4 conservative-strong router target).
- supported and mild_scope_overclaim remain the weakest boundary; not solved.
