# Table 5: New Algorithm Sweep vs Frozen R4

| method | strong_positive_f1 | delta_vs_r4_strong | flat4_macro_f1 | delta_vs_r4_flat4 | delta_vs_r4_contra | delta_vs_r4_escalation | ci_crosses_zero | recommended_use |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| B_cost_sensitive_cw4.0 | 0.4221 | 0.0254 | 0.4365 | 0.0127 | 0.0000 | 0.0119 | YES | auxiliary_module |
| B_cost_sensitive_cw1.5 | 0.4136 | 0.0169 | 0.4268 | 0.0030 | 0.0000 | -0.0135 | YES | auxiliary_module |
| A1_temp_scaled_router | 0.4076 | 0.0109 | 0.4338 | 0.0100 | 0.0000 | 0.0074 | YES | auxiliary_module |
| B_cost_sensitive_cw3.0 | 0.4059 | 0.0092 | 0.4269 | 0.0031 | 0.0000 | 0.0111 | YES | auxiliary_module |
| B_cost_sensitive_cw2.0 | 0.4023 | 0.0056 | 0.4274 | 0.0036 | 0.0000 | 0.0161 | YES | auxiliary_module |
| C_ordinal_severity | 0.3685 | -0.0282 | 0.3783 | -0.0455 | -0.0212 | -0.1528 | YES | diagnostic_only |
| A2_isotonic_router | 0.3661 | -0.0307 | 0.4302 | 0.0063 | 0.0000 | 0.0025 | YES | reject |
| F_recall_balance_router | 0.3185 | -0.0782 | 0.4189 | -0.0049 | -0.0021 | -0.0259 | NO | reject |
| D1_ovr_contra_priority | 0.3141 | -0.0826 | 0.3854 | -0.0384 | 0.0114 | -0.1172 | NO | reject |
| D2_ovr_strong_priority | 0.3036 | -0.0931 | 0.3813 | -0.0426 | -0.0218 | -0.1127 | NO | reject |
| E_error_corrector_r4 | 0.2787 | -0.1180 | 0.4135 | -0.0103 | 0.0000 | -0.0251 | NO | reject |
| A3_platt_router | 0.2540 | -0.1427 | 0.4147 | -0.0091 | -0.0021 | -0.0357 | NO | reject |
| D3_ovr_max_prob | 0.2397 | -0.1571 | 0.4003 | -0.0235 | 0.0015 | -0.0354 | NO | reject |

- R4 reference: strong_positive_f1 = 0.3967, flat4_macro_f1 = 0.4238.
- No new algorithm meets all 7 replacement criteria (delta >= +0.03, CI not crossing 0, etc.).
- B_cost_sensitive_cw4.0 is the best (delta = +0.0254) but below +0.03 threshold and CI crosses 0.
- 5 methods are auxiliary_module, 1 is diagnostic_only, 7 are reject.
- Conclusion: R4 remains the frozen main baseline; cw4.0 is auxiliary sensitivity analysis only.
