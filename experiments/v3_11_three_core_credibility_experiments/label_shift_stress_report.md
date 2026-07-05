# Label-Shift Stress Test

**Type: Non-gold robustness analysis.** Does not replace gold adjudication. Simulated label shift is NOT gold data — it is a sensitivity probe.

**Method:** For each retention rate r, randomly relabel (1-r) of silver strong_action as mild_scope, recompute binary strong_action F1. 1000 bootstrap resamples on matched-100 (n_strong=25).

| Retention | n_keep | R4 F1 (mean ± std, 95% CI) | DeepSeek F1 | GPT-std F1 | Δ(R4-DS) | Δ 95% CI | R4 wins % | Statistical strength |
|---|---|---|---|---|---|---|---|---|
| 100% | 25.0 | 0.3000 ± 0.0000 [0.3000, 0.3000] | 0.0769 | 0.0769 | +0.2231 | [+0.223, +0.223] | 100.0% | robust |
| 90% | 22.0 | 0.2789 ± 0.0270 [0.2105, 0.3158] | 0.0777 | 0.0777 | +0.2012 | [+0.159, +0.281] | 100.0% | robust |
| 80% | 20.0 | 0.2616 ± 0.0361 [0.1818, 0.3273] | 0.0764 | 0.0764 | +0.1853 | [+0.123, +0.291] | 100.0% | robust |
| 70% | 18.0 | 0.2451 ± 0.0414 [0.1509, 0.3028] | 0.0759 | 0.0759 | +0.1692 | [+0.083, +0.264] | 100.0% | robust |
| 60% | 15.0 | 0.2184 ± 0.0477 [0.1200, 0.3200] | 0.0776 | 0.0776 | +0.1408 | [+0.035, +0.280] | 98.6% | marginal-positive (CI lower bound just above 0) |
| 50% | 12.0 | 0.1843 ± 0.0515 [0.0851, 0.2979] | 0.0706 | 0.0706 | +0.1137 | [-0.026, +0.255] | 94.2% | **positive but statistically weaker / CI crosses zero** |
| 40% | 10.0 | 0.1612 ± 0.0530 [0.0444, 0.2667] | 0.0776 | 0.0776 | +0.0835 | [-0.093, +0.222] | 70.1% | NOT significant (CI crosses zero) |
| 30% | 8.0 | 0.1336 ± 0.0528 [0.0465, 0.2326] | 0.0691 | 0.0691 | +0.0645 | [-0.129, +0.233] | 71.1% | NOT significant (CI crosses zero) |

## Key Findings

1. **Break-even retention:** ~0.5 (delta 95% CI crosses zero at 50% retention)
2. **60% retention:** R4 wins 98.6% of bootstraps (Δ=+0.1408, 95% CI=[+0.035, +0.280]) — **marginal-positive**, CI lower bound just above 0. Treat as a directional signal, not a robust pass.
3. **50% retention:** R4 wins 94.2% of bootstraps (Δ=+0.1137, 95% CI=[-0.026, +0.255]) — **positive point estimate but statistically weaker / CI crosses zero**. **Do NOT report as a robust pass.** It is a directional signal that requires gold confirmation. The 94.2% bootstrap-win rate reflects the point estimate distribution, but the CI crossing zero means the advantage is not statistically distinguishable from zero at the 95% confidence level.
4. **Gold pilot implication:** If gold retention ≥ 70%, the strong_action claim is robust. At 60%, it survives as a marginal-positive signal. At 50%, it is positive-but-weaker and must be reported with the CI-crosses-zero caveat. Below 50%, downgrade per §VII.G.
5. **Downgrade if retention < break-even:** If gold retention < 50%, downgrade per §VII.G: strong_action claim becomes "R4 detects a candidate set that includes true strong_action cases, but precision is too low for standalone use." The fallback 3-class taxonomy (acceptable/strong/contra) remains viable.
6. **Why R4 still wins point-estimate-wise:** LLM F1 is already near zero (~0.077), so shrinking the positive set hurts R4's precision but cannot help LLM, which rarely predicts strong_action at all. However, point-estimate dominance is not the same as statistical robustness — at 50% retention the CI crosses zero, so the advantage is directional, not confirmed.
