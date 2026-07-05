# LLM Conservatism + Error Direction Audit Report

**Date:** 2026-07-05
**Source:** gpt_vs_r4_deepseek_comparison.csv (100 matched, 25 strong_action)
**Status:** Reanalysis only. SILVER labels.

## 1. When silver=strong_action, where does each method predict?

| Method | n_strong | pred_supported | pred_mild | pred_strong | pred_contradiction | pred_strong_rate | compress_rate (to mild+supported) |
|---|---|---|---|---|---|---|---|
| GPT standard | 25 | 0 | 10 | 1 | 14 | 0.04 | 0.4 |
| GPT structured | 25 | 0 | 10 | 1 | 14 | 0.04 | 0.4 |
| DeepSeek | 25 | 9 | 10 | 1 | 5 | 0.04 | 0.76 |
| R4 | 25 | 2 | 8 | 9 | 6 | 0.36 | 0.4 |

## 2. LLM conservatism verdict

LLM conservatism = LLM predicts strong_action at much lower rate than R4 on silver=strong cases (i.e., LLM under-detects strong_action).

- GPT standard: pred_strong_rate = 0.04 (catches 1/25 strong; sends 10/25 to mild/supported, 14/25 to contradiction)
- GPT structured: pred_strong_rate = 0.04 (catches 1/25 strong; sends 10/25 to mild/supported, 14/25 to contradiction)
- DeepSeek: pred_strong_rate = 0.04 (catches 1/25 strong; sends 19/25 to mild/supported, 5/25 to contradiction)
- R4: pred_strong_rate = 0.36 (catches 9/25 strong; sends 10/25 to mild/supported, 6/25 to contradiction)

**LLM conservatism CONFIRMED**: LLM pred_strong_rate (0.04) is 9x lower than R4 (0.36). LLMs almost never predict strong_action when silver=strong. The LLM error direction splits into two patterns:
1. **Over-contradiction** (GPT standard/structured): 14/25 (56%) silver=strong cases sent to contradiction_candidate.
2. **Compression to mild/supported** (DeepSeek): 19/25 (76%) silver=strong cases sent to mild/supported.

Both patterns result in strong_action under-detection. R4's higher pred_strong_rate gives higher recall but more false positives (see Task F).

## 3. GPT structured vs standard improvement

GPT structured pred_strong_rate (0.04) vs GPT standard (0.04): no improvement or worse

## 4. Complementarity (R4 vs LLM, on full 100)

| Method | both_correct | llm_only_correct | r4_only_correct | both_wrong | complementary_cases |
|---|---|---|---|---|---|
| gpt_standard | 23 | 39 | 11 | 27 | 50 |
| gpt_structured | 23 | 40 | 11 | 26 | 51 |
| deepseek | 22 | 38 | 12 | 28 | 50 |

Complementary cases = LLM catches what R4 misses + R4 catches what LLM misses. High complementary count supports two-stage pipeline.

## 5. Interpretation

- LLM conservatism is the dominant failure mode for strong_action detection: LLMs predict strong_action at 9x lower rate than R4 on silver=strong cases.
- LLM error direction splits: GPT standard/structured over-route to contradiction (56%); DeepSeek compresses to mild/supported (76%).
- R4 over-routes to strong_action (pred_strong_rate=0.36) which gives higher recall but more false positives (see Task F: 26 FP of 35 strong predictions).
- The two are complementary: LLM provides precision (when it does predict strong, it's usually right), R4 provides recall (catches LLM-missed strong).
- 50/100 samples show complementary cases (LLM-only-correct + R4-only-correct), strongly supporting the two-stage pipeline proposal.
