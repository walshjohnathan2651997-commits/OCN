# Label-Shift / Gold-Collapse Stress Test

**Method:** For each retention rate r, randomly relabel (1-r) of silver strong_action_overclaim as mild_scope_overclaim, then recompute each judge's binary strong_action positive-F1. 1000 bootstrap resamples.

**Matched-100 has 25 silver strong_action samples.** Matched-200 has 50.

## Matched-100 Results

| Retention | n_keep | R4 F1 (mean ± std, 95% CI) | DeepSeek F1 | GPT-std F1 | GPT-struct F1 | Δ(R4-DS) | R4 wins % |
|---|---|---|---|---|---|---|---|
| 100% | 25 | 0.3000 ± 0.0000 [0.3000, 0.3000] | 0.0769 | 0.0769 | 0.0769 | +0.2231 | 100.0% |
| 90% | 22 | 0.2789 ± 0.0270 [0.2105, 0.3158] | 0.0777 | 0.0777 | 0.0777 | +0.2012 | 100.0% |
| 80% | 20 | 0.2616 ± 0.0361 [0.1818, 0.3273] | 0.0764 | 0.0764 | 0.0764 | +0.1853 | 100.0% |
| 70% | 18 | 0.2451 ± 0.0414 [0.1509, 0.3028] | 0.0759 | 0.0759 | 0.0759 | +0.1692 | 100.0% |
| 60% | 15 | 0.2184 ± 0.0477 [0.1200, 0.3200] | 0.0776 | 0.0776 | 0.0776 | +0.1408 | 98.6% |
| 50% | 12 | 0.1843 ± 0.0515 [0.0851, 0.2979] | 0.0706 | 0.0706 | 0.0706 | +0.1137 | 94.2% |
| 40% | 10 | 0.1612 ± 0.0530 [0.0444, 0.2667] | 0.0776 | 0.0776 | 0.0776 | +0.0835 | 70.1% |
| 30% | 8 | 0.1336 ± 0.0528 [0.0465, 0.2326] | 0.0691 | 0.0691 | 0.0691 | +0.0645 | 71.1% |

## Key Findings

1. **Break-even retention:** ~0.5 (CI lower bound crosses 0)
2. **At 60% retention:** R4 wins 98.6% of bootstraps, mean delta = +0.1408
3. **At 50% retention:** R4 wins 94.2% of bootstraps, mean delta = +0.1137
4. **Interpretation:** R4's strong_action advantage is robust to label shift because LLM F1 is already near zero (0.0769 baseline); shrinking the positive set hurts R4's precision but does not help LLM, which rarely predicts strong_action at all.
