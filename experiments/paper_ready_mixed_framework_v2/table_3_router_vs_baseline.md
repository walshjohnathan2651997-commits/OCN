# Table 3: Router Variants vs Baseline

| method | strong_positive_f1 | flat4_macro_f1 | contradiction_positive_f1 | escalation_macro_f1 | strong_recall | selected |
| --- | --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.2408 | 0.3963 | 0.7308 | 0.5723 | 0.2062 |  |
| R1_contra_first | 0.3467 | 0.4124 | 0.7344 | 0.5955 | 0.4000 |  |
| R2_strong_first | 0.3400 | 0.3925 | 0.6755 | 0.5947 | 0.4125 |  |
| R3_margin_router | 0.4047 | 0.3565 | 0.7308 | 0.5488 | 0.6937 |  |
| R4_conservative_strong (SELECTED) | 0.3967 | 0.4238 | 0.7296 | 0.6143 | 0.4562 | YES |
| R5_strong_recall_router | 0.4399 | 0.3680 | 0.7363 | 0.4878 | 0.7000 |  |

- R4 is NOT the highest strong_positive_f1 (R5 is higher at 0.4399).
- R4 is selected because it is the only router meeting ALL 5 constraints:
-   (1) strong_positive_delta >= +0.05, (2) flat4_macro_delta >= -0.02,
-   (3) contradiction_positive_delta >= -0.03, (4) escalation_macro_delta >= -0.03,
-   (5) positive_delta_seed_count >= 7.
- R5_strong_recall_router has higher strong F1 but flat4_macro_delta = -0.0284 (exceeds -0.02).
- R3_margin_router has flat4_macro_delta = -0.0398 (exceeds -0.02).
