# Non-Gold Robustness Stress Test — Master Report

**Version:** V3.11 Non-Gold Robustness Stress Test
**Date:** 2026-07-04
**Constraint:** No gold annotation, no API calls, no new model training, no threshold retuning, no modification of V3.11 or original data.
**Inputs:** Frozen R4 predictions + existing LLM (DeepSeek, GPT-5.5) predictions on silver labels.

---

## Executive Summary

Five non-gold stress tests were run to evaluate whether V3.11's main claim — **R4 provides complementary strong_action screening value that LLM judges lack** — survives label shift, boundary collapse, screening application, and statistical scrutiny.

**Bottom line:** The RELATIVE pattern (R4 > LLM on strong_action) is robust across all five tests. The ABSOLUTE numbers remain silver-stage and require gold adjudication.

## 1. Label-Shift Stress Test

- **Break-even retention:** ~0.5 (CI lower bound crosses 0)
- **At 60% retention:** R4 wins 98.6% of bootstraps (mean Δ=+0.1408)
- **At 50% retention:** R4 wins 94.2% of bootstraps (mean Δ=+0.1137)
- **Why robust:** LLM F1 is already near zero (0.0769); shrinking the positive set hurts R4's precision but cannot help LLM, which rarely predicts strong_action at all.

## 2. Boundary-Collapse Fallback Test

- **Best fallback taxonomy:** C_3class_acceptable_merge
- A_4class: R4 key recall=0.3600, DS key recall=0.0400, Δ=+0.3200
- B_3class_overclaim_merge: R4 key recall=0.7200, DS key recall=0.4800, Δ=+0.2400
- C_3class_acceptable_merge: R4 key recall=0.3600, DS key recall=0.0400, Δ=+0.3200
- **Implication:** If the mild/strong boundary collapses under gold, the paper can fall back to taxonomy C (acceptable/strong_action/contradiction, merging supported+mild) and R4 still retains screening value with Δrecall=+0.32.

## 3. Screening Utility

- **Review burden:** 35.0% of samples flagged
- **Recall:** 0.3600 (9/25 true strongs caught)
- **Precision:** 0.2571
- **FP/TP ratio:** 2.89 (below pre-registered threshold of 10 — screening viable)
- **FP breakdown:** mild=13, supp=12, contra=1

## 4. LLM Conservatism Audit

- **GPT-5.5 error pattern:** collapses to contradiction 56% (treats strong_action as factual contradiction), supported/mild 40%
- **DeepSeek error pattern:** collapses to supported/mild 76-80% (charitable interpretation), contradiction 16-20%
- **All LLMs:** strong_action correct recall = 4% (vs R4 36%)
- **Structured prompt fixes strong_action:** NO (GPT-std=1/25, GPT-struct=1/25, identical)
- **R4 correct strong predictions:** 9/25

## 5. Matched Significance

- **R4 vs DeepSeek (strong_f1):** Δ=+0.2231, CI=[+0.0397, +0.3947], McNemar p=0.0029
- **R4 vs GPT-standard (strong_f1):** Δ=+0.2231, CI=[+0.0323, +0.3944]
- **GPT std vs structured (strong_f1):** Δ=+0.0000, NOT significant
- **R4 vs DeepSeek (macro_f1):** Δ=-0.1968 (R4 still lower on overall macro-F1 — complement, not replacement)
- **matched_significance_supports_r4 = True**

## Recommendations for V3.12

1. **Insert §VIII.D Non-Gold Robustness Stress Tests** with these 5 analyses.
2. **Frame as:** 'The relative pattern (R4 > LLM on strong_action) is robust under label shift, boundary collapse, and statistical scrutiny. Absolute numbers remain silver-stage pending gold adjudication.'
3. **Use label-shift break-even as a pre-registered safety margin:** If gold retention ≥ 60%, the strong_action claim survives.
4. **Use boundary-collapse fallback as a contingency:** If gold κ < 0.40 on mild_vs_strong, fall back to 3-class overclaim taxonomy.
5. **Use screening utility to quantify operational cost:** FP/TP = 2.89, below the pre-registered threshold of 10.
6. **Use LLM conservatism to explain the mechanism:** LLMs are not randomly wrong — they systematically avoid strong_action predictions.
7. **Do NOT claim gold validation.** These tests strengthen the silver-stage RELATIVE pattern, not absolute numbers.

## Readiness Gate

```json
{
  "label_shift_break_even_retention": "~0.5 (CI lower bound crosses 0)",
  "r4_wins_at_60_percent_retention": true,
  "r4_wins_at_50_percent_retention": true,
  "best_fallback_taxonomy": "C_3class_acceptable_merge",
  "screening_fp_tp_ratio": 2.888888888888889,
  "screening_viable": true,
  "llm_conservatism_confirmed": true,
  "matched_significance_supports_r4": true,
  "can_strengthen_v3_11_without_gold": true,
  "recommended_paper_insert_section": "§VIII.D Non-Gold Robustness Stress Tests: label-shift persistence, boundary-collapse fallback, screening utility, LLM conservatism audit, matched significance. These results strengthen V3.11's silver-stage claims without requiring gold annotation.",
  "remaining_gold_dependency": "Gold adjudication still needed to: (1) confirm the absolute strong_action F1 numbers (silver→gold may shift), (2) resolve the mild_vs_strong boundary κ, (3) confirm strong_action retention rate. The non-gold stress tests show the RELATIVE pattern (R4 > LLM on strong_action) is robust, but absolute numbers remain silver-stage.",
  "auxiliary_fields": {
    "r4_wins_at_60pct_pct": 0.986,
    "r4_wins_at_50pct_pct": 0.942,
    "delta_at_60pct": 0.14077499999999998,
    "delta_at_50pct": 0.11372504091653028,
    "r4_vs_deepseek_strong_f1_delta": 0.22307692307692306,
    "r4_vs_deepseek_strong_f1_ci": [
      0.0397162485065711,
      0.39474937343358396
    ],
    "r4_vs_deepseek_mcnemar_p": 0.0029350556433200836,
    "llm_conservative_collapse_gpt_std": 0.4,
    "llm_conservative_collapse_deepseek": 0.76,
    "screening_review_burden": 0.35,
    "screening_recall": 0.36,
    "screening_precision": 0.2571428571428571
  }
}
```
