# Matched Significance Test

**Method:** Paired bootstrap (1000 resamples) for CI; McNemar exact binomial test for strong_action detection. All on matched-100 (n=100, 25 per class).

## All Pairwise Comparisons

| Pair | Metric | Value 1 | Value 2 | Δ (1-2) | 95% CI | CI excl. 0 | McNemar p | Significant |
|---|---|---|---|---|---|---|---|---|
| r4 vs gpt_standard | strong_recall | 0.3600 | 0.0400 | +0.3200 | [+0.1429, +0.4852] | yes | 0.0029 | yes |
| r4 vs gpt_standard | strong_precision | 0.2571 | 1.0000 | -0.7429 | [-0.8529, +0.3462] | no | 0.0029 | yes |
| r4 vs gpt_standard | strong_f1 | 0.3000 | 0.0769 | +0.2231 | [+0.0323, +0.3944] | yes | 0.0029 | yes |
| r4 vs gpt_standard | macro_f1 | 0.3280 | 0.5523 | -0.2243 | [-0.0758, +0.1173] | no | -1.0000 | no |
| r4 vs gpt_standard | contradiction_f1 | 0.6800 | 0.6857 | -0.0057 | [-0.2037, +0.0393] | no | -1.0000 | no |
| r4 vs gpt_structured | strong_recall | 0.3600 | 0.0400 | +0.3200 | [+0.1304, +0.5000] | yes | 0.0029 | yes |
| r4 vs gpt_structured | strong_precision | 0.2571 | 1.0000 | -0.7429 | [-0.8571, +0.3449] | no | 0.0029 | yes |
| r4 vs gpt_structured | strong_f1 | 0.3000 | 0.0769 | +0.2231 | [+0.0307, +0.3860] | yes | 0.0029 | yes |
| r4 vs gpt_structured | macro_f1 | 0.3280 | 0.5543 | -0.2263 | [-0.0786, +0.1234] | no | -1.0000 | no |
| r4 vs gpt_structured | contradiction_f1 | 0.6800 | 0.6857 | -0.0057 | [-0.2102, +0.0388] | no | -1.0000 | no |
| r4 vs deepseek | strong_recall | 0.3600 | 0.0400 | +0.3200 | [+0.1333, +0.5200] | yes | 0.0029 | yes |
| r4 vs deepseek | strong_precision | 0.2571 | 1.0000 | -0.7429 | [-0.8462, +0.3501] | no | 0.0029 | yes |
| r4 vs deepseek | strong_f1 | 0.3000 | 0.0769 | +0.2231 | [+0.0397, +0.3947] | yes | 0.0029 | yes |
| r4 vs deepseek | macro_f1 | 0.3280 | 0.5248 | -0.1968 | [-0.0719, +0.1151] | no | -1.0000 | no |
| r4 vs deepseek | contradiction_f1 | 0.6800 | 0.8077 | -0.1277 | [-0.1393, +0.1155] | no | -1.0000 | no |
| gpt_standard vs gpt_structured | strong_recall | 0.0400 | 0.0400 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs gpt_structured | strong_precision | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs gpt_structured | strong_f1 | 0.0769 | 0.0769 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs gpt_structured | macro_f1 | 0.5523 | 0.5543 | -0.0021 | [-0.0292, +0.0272] | no | -1.0000 | no |
| gpt_standard vs gpt_structured | contradiction_f1 | 0.6857 | 0.6857 | +0.0000 | [+0.0000, +0.0000] | no | -1.0000 | no |
| gpt_standard vs deepseek | strong_recall | 0.0400 | 0.0400 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs deepseek | strong_precision | 1.0000 | 1.0000 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs deepseek | strong_f1 | 0.0769 | 0.0769 | +0.0000 | [+0.0000, +0.0000] | no | 1.0000 | no |
| gpt_standard vs deepseek | macro_f1 | 0.5523 | 0.5248 | +0.0275 | [-0.0745, +0.0758] | no | -1.0000 | no |
| gpt_standard vs deepseek | contradiction_f1 | 0.6857 | 0.8077 | -0.1220 | [-0.0406, +0.1892] | no | -1.0000 | no |

## Key Findings

1. **R4 strong_action advantage is statistically supported:**
   - R4 vs DeepSeek: Δ=+0.2231, CI=[+0.0397, +0.3947], McNemar p=0.0029
   - R4 vs GPT-standard: Δ=+0.2231, CI=[+0.0323, +0.3944]
2. **GPT structured ≠ GPT standard on strong_action:** Δ=+0.0000, NOT significant — structured prompt does not fix strong_action.
3. **R4 macro-F1 still lower than DeepSeek:** Δ=-0.1968 — R4 is a complement, not an overall replacement.
4. **matched_significance_supports_r4 = True**
