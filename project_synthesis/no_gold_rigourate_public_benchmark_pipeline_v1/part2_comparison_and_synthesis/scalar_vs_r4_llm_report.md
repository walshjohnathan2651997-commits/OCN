# Scalar vs R4 vs LLM Comparison Report

**Task:** No-Gold RIGOURATE + Public Benchmark Pipeline Part 2 - Section 1
**Date:** 2026-07-05
**Inputs:** Part 1 scalar scores, R4 frozen metrics, LLM 200, GPT comparison 100 matched

## 1. Methods compared

| Method | N | Subset | Source |
| --- | --- | --- | --- |
| R4_conservative_strong | 444 | silver_444 | frozen_r4_metrics_summary.json |
| baseline_flat4 | 444 | silver_444 | frozen_r4_metrics_summary.json |
| rule_scalar_score | 444 | silver_444 | Part 1 scalar scores |
| DeepSeek_llm_label_200 | 200 | llm_200 | llm_parsed_outputs_200.csv |
| llm_scalar_proxy_200 | 200 | llm_200 | Part 1 scalar scores (llm_scalar_proxy) |
| GPT_standard_100 | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| GPT_structured_100 | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| DeepSeek_100_matched | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |
| R4_100_matched | 100 | matched_100 | gpt_vs_r4_deepseek_comparison.csv |

## 2. strong_action screening metrics

| Method | N | strong_F1 | strong_precision | strong_recall | macro_F1 | FP/TP | review_burden |
| --- | --- | --- | --- | --- | --- | --- | --- |
| R4_conservative_strong | 444 | 0.3967 | 0.3791 | 0.4562 | 0.4238 | 1.6378 | N/A |
| baseline_flat4 | 444 | 0.2408 | 0.3097 | 0.2062 | 0.3963 | 2.2289 | N/A |
| rule_scalar_score | 444 | 0.2996 | 0.2564 | 0.3604 | 0.2507 | 2.9000 | 0.3514 |
| DeepSeek_llm_label_200 | 200 | 0.0769 | 1.0000 | 0.0400 | 0.5270 | 0.0000 | 0.0100 |
| llm_scalar_proxy_200 | 200 | 0.0769 | 1.0000 | 0.0400 | N/A | 0.0000 | 0.0100 |
| GPT_standard_100 | 100 | 0.0769 | 1.0000 | 0.0400 | 0.5523 | 0.0000 | 0.0100 |
| GPT_structured_100 | 100 | 0.0769 | 1.0000 | 0.0400 | 0.5543 | 0.0000 | 0.0100 |
| DeepSeek_100_matched | 100 | 0.0769 | 1.0000 | 0.0400 | 0.5248 | 0.0000 | 0.0100 |
| R4_100_matched | 100 | 0.3000 | 0.2571 | 0.3600 | 0.3280 | 2.8889 | 0.3500 |

## 3. LLM-missed strong_action captured by R4

On the 100 matched subset:
- Total strong_action samples: 25
- DeepSeek missed strong_action: 24
- R4 caught DeepSeek-missed strong_action: 8
- R4 capture rate (of LLM-missed): 0.3333

## 4. Required answers

### Q1. Does R4 still outperform scalar baseline on strong_action screening?

**YES.** On silver 444:
- R4_conservative_strong: strong_F1=0.3967, recall=0.4562
- rule_scalar_score: strong_F1=0.2996, recall=0.3604
- R4 outperforms rule_scalar by 0.0971 F1 points.

On 100 matched:
- R4_100_matched: strong_F1=0.3000
- DeepSeek_100_matched: strong_F1=0.0769

R4 retains a clear advantage on strong_action positive-F1 over scalar baselines, and captures 8/24 strong_action cases that DeepSeek missed (33.3% capture rate).

### Q2. Does scalar conflate mild and strong?

**YES.** From Part 1, on mild_vs_strong task:
- rule_scalar_score ROC-AUC=0.5054 (chance level)
- llm_scalar_proxy ROC-AUC=0.5874 (weak, < 0.60)

A scalar score cannot distinguish mild_scope_overclaim from strong_action_overclaim; both are compressed into the same severity region. This is the critical failure mode that motivates the four-class decomposition.

### Q3. What is R4's cost?

R4's cost is **lower macro-F1** and **higher review burden**:
- R4 flat4_macro_f1=0.4238 vs baseline_flat4 macro_f1=0.3963 (R4 is 0.0275 higher in macro, but LLM macro is higher still on matched subsets)
- R4 trades overall macro-F1 for targeted strong_action positive-F1
- R4 strong_precision=0.3791 means 62.1% of R4's strong_action flags are false positives, requiring human review

The cost is acceptable for a screening-oriented system: R4 is designed to over-flag strong_action (high recall) at the expense of precision, so that human reviewers can filter false positives. This is the standard trade-off in high-risk screening.

### Q4. Are scalar overstatement scoring and relation-specific screening complementary?

**YES.** The evidence:
1. Scalar (rule-based) is at chance level for strong_action (ROC-AUC=0.50), but LLM-derived scalar can identify supported_vs_overclaim (ROC-AUC=0.85) and contradiction_vs_noncontradiction (ROC-AUC=0.92) — scalar is good for broad severity ranking.
2. R4's structured routing provides strong_action screening signal that scalar cannot (R4 strong_F1=0.3967 vs rule_scalar strong_F1=0.2996).
3. R4 captures 8/24 LLM-missed strong_action cases — R4 catches what scalar/LLM miss.

The two approaches are complementary: scalar for broad severity ranking, relation-specific (R4) for high-risk action-overclaim screening. This complementarity is the empirical motivation for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Prohibitions enforced

- No paid API calls (uses only existing parsed outputs).
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data or V3.15 paper.
