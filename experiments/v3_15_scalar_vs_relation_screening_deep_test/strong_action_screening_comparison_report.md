# Strong_Action Screening Comparison: Scalar vs R4 vs LLM

**Task:** V3.15 Task 4/5 §3 — strong_action vs non-strong screening comparison.
**Date:** 2026-07-05
**Status:** Reanalysis of existing 100 matched-sample predictions. NOT new experiments. NOT gold. NOT API.

## 1. Setup

- **Data:** 100 matched samples (25 per class) from `rigourate_style_vs_r4_cases.csv`.
- **Positive class:** strong_action_overclaim (n=25).
- **Methods compared:** rule_scalar, r4_frozen, gpt_standard, gpt_structured, deepseek_v3.

## 2. Headline results

| Method | TP | FP | FN | TN | Precision | Recall | Positive-F1 | FP/TP | Review Burden | Accuracy | LLM-missed captured |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rule_scalar | 3 | 16 | 22 | 59 | 0.1579 | 0.12 | 0.1364 | 5.3333 | 0.19 | 0.62 | 3 |
| r4_frozen | 9 | 26 | 16 | 49 | 0.2571 | 0.36 | 0.3 | 2.8889 | 0.35 | 0.58 | 8 |
| gpt_standard | 1 | 0 | 24 | 75 | 1.0 | 0.04 | 0.0769 | 0.0 | 0.01 | 0.76 | 0 |
| gpt_structured | 1 | 0 | 24 | 75 | 1.0 | 0.04 | 0.0769 | 0.0 | 0.01 | 0.76 | 0 |
| deepseek_v3 | 1 | 0 | 24 | 75 | 1.0 | 0.04 | 0.0769 | 0.0 | 0.01 | 0.76 | 0 |

## 3. Overlap between scalar positives and R4 positives

- Scalar positives: **19**
- R4 positives: **35**
- Overlap (both flag strong): **5**
- Overlap rate (of scalar): **26.3%**
- Overlap rate (of R4): **14.3%**
- Overlap on true strong (both correct): **0**

## 4. Verdict

**R4 retains strong_action screening advantage.** R4 positive-F1 = 0.3 vs scalar positive-F1 = 0.1364. R4 recall = 0.36 vs scalar recall = 0.12. R4 captures 8 LLM-missed strong cases; scalar captures 3.

Scalar baseline (rule-based) is the WEAKEST method on strong_action screening. LLMs have higher precision but near-zero recall. R4 has the highest recall and the highest positive-F1 among non-LLM methods. R4 cannot be replaced by scalar baseline for strong_action screening.

## 5. Prohibitions enforced

- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.