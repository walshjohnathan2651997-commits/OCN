# Boundary Collapse Fallback Test Report

**Date:** 2026-07-05
**Source:** gpt_vs_r4_deepseek_comparison.csv (100 matched samples)
**Status:** Reanalysis only. SILVER labels. No new experiments.

## 1. Five taxonomy variants

1. **original 4-class**: supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate
2. **supported / overclaim / contradiction**: mild+strong merged into overclaim
3. **acceptable / strong / contradiction**: supported+mild merged into acceptable
4. **strong vs rest**: binary
5. **overclaim vs non-overclaim**: binary

## 2. Macro-F1 by taxonomy and method

| Taxonomy | Method | n_classes | macro_F1 | strong_F1 | strong_recall | overclaim_recall |
|---|---|---|---|---|---|---|
| 1_original_4class | r4 | 4 | 0.328 |  |  |  |
| 1_original_4class | gpt_standard | 4 | 0.5523 |  |  |  |
| 1_original_4class | gpt_structured | 4 | 0.5543 |  |  |  |
| 1_original_4class | deepseek | 4 | 0.5248 |  |  |  |
| 2_supported_overclaim_contradiction | r4 | 3 | 0.4728 |  |  | 0.72 |
| 2_supported_overclaim_contradiction | gpt_standard | 3 | 0.7398 |  |  | 0.54 |
| 2_supported_overclaim_contradiction | gpt_structured | 3 | 0.7469 |  |  | 0.5 |
| 2_supported_overclaim_contradiction | deepseek | 3 | 0.7112 |  |  | 0.48 |
| 3_acceptable_strong_contradiction | r4 | 3 | 0.497 |  |  |  |
| 3_acceptable_strong_contradiction | gpt_standard | 3 | 0.5299 |  |  |  |
| 3_acceptable_strong_contradiction | gpt_structured | 3 | 0.5299 |  |  |  |
| 3_acceptable_strong_contradiction | deepseek | 3 | 0.5626 |  |  |  |
| 4_strong_vs_rest | r4 | 2 | 0.5 | 0.3 | 0.36 |  |
| 4_strong_vs_rest | gpt_standard | 2 | 0.4695 | 0.0769 | 0.04 |  |
| 4_strong_vs_rest | gpt_structured | 2 | 0.4695 | 0.0769 | 0.04 |  |
| 4_strong_vs_rest | deepseek | 2 | 0.4695 | 0.0769 | 0.04 |  |
| 5_overclaim_vs_nonoverclaim | r4 | 2 | 0.5484 |  |  | 0.72 |
| 5_overclaim_vs_nonoverclaim | gpt_standard | 2 | 0.7106 |  |  | 0.54 |
| 5_overclaim_vs_nonoverclaim | gpt_structured | 2 | 0.7149 |  |  | 0.5 |
| 5_overclaim_vs_nonoverclaim | deepseek | 2 | 0.7029 |  |  | 0.48 |

## 3. R4 vs LLM macro-F1 delta

| Taxonomy | R4 macro_F1 | LLM macro_F1 | Delta (R4 - LLM) |
|---|---|---|---|
| 1_original_4class | 0.3280 | 0.5523 | -0.2243 |
| 2_supported_overclaim_contradiction | 0.4728 | 0.7398 | -0.2670 |
| 3_acceptable_strong_contradiction | 0.4970 | 0.5299 | -0.0329 |
| 4_strong_vs_rest | 0.5000 | 0.4695 | 0.0305 |
| 5_overclaim_vs_nonoverclaim | 0.5484 | 0.7106 | -0.1622 |

## 4. Interpretation

- **Original 4-class**: R4 macro_F1 < LLM (R4 trades overall accuracy for strong_action F1).
- **Strong vs rest (binary)**: R4 typically retains strong_action advantage.
- **Overclaim vs non-overclaim**: collapsing mild+strong may obscure the high-risk boundary that R4 is designed to detect.
- **acceptable / strong / contradiction** (collapsing supported+mild): tests whether the supported/mild boundary is stable.

## 5. Recommendation

The four-class taxonomy is the most informative for the paper's strong_action screening claim. Collapsing to three-class or binary loses the action-vs-scope distinction that R4's routing is designed to detect. Three-class fallback is a contingency (Route C in next_route_decision.md), not a default.
