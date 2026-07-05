# Low-Prevalence Screening Simulation Report (V3.16 Integration)

**Task:** No-Gold Evidence Integration Plan for V3.16 - Section 4
**Date:** 2026-07-05
**Source:** Reused from `D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\` (1000 bootstrap iterations per prevalence level).
**Disclaimer:** This is a **simulation** over silver-labelled SimClaim data. The prevalence values are *imposed* by resampling, NOT observed in a natural corpus. The numbers below must NOT be reported as natural-distribution results.

---

## 1. Simulation setup (recap)

- **Bootstrap iterations:** 1000 per prevalence level
- **Sample size per iteration:** 1000
- **Prevalence levels (strong_action_overclaim):** 1%, 3%, 5%, 10%, 15%, 20% (also 25% in source)
- **Non-strong composition:** supported 80% / mild_scope_overclaim 15% / contradiction_candidate 5%
- **Methods compared:** r4, gpt_standard, gpt_structured, deepseek
- **Random seed:** 20260705
- **Base data:** 100 matched samples from `gpt_vs_r4_deepseek_comparison.csv`

---

## 2. R4 metrics across prevalence

- prevalence=0.01: recall=0.3626, precision=0.0078, positive-F1=0.0153, FP/TP=158.32 (median 121.00), review_burden=0.4634, NNR=159.32, accuracy=0.5339, LLM-missed-strong-captured=3.194
- prevalence=0.03: recall=0.3606, precision=0.0235, positive-F1=0.0441, FP/TP=44.75 (median 41.05), review_burden=0.4611, NNR=45.75, accuracy=0.5305, LLM-missed-strong-captured=9.637
- prevalence=0.05: recall=0.3585, precision=0.0391, positive-F1=0.0704, FP/TP=25.63 (median 24.72), review_burden=0.4589, NNR=26.63, accuracy=0.5269, LLM-missed-strong-captured=15.929
- prevalence=0.10: recall=0.3632, precision=0.0799, positive-F1=0.1310, FP/TP=11.71 (median 11.51), review_burden=0.4544, NNR=12.71, accuracy=0.5182, LLM-missed-strong-captured=32.362
- prevalence=0.15: recall=0.3621, precision=0.1208, positive-F1=0.1811, FP/TP=7.37 (median 7.29), review_burden=0.4496, NNR=8.37, accuracy=0.5090, LLM-missed-strong-captured=48.259
- prevalence=0.20: recall=0.3605, precision=0.1626, positive-F1=0.2240, FP/TP=5.20 (median 5.16), review_burden=0.4435, NNR=6.20, accuracy=0.5007, LLM-missed-strong-captured=63.967

---

## 3. LLM comparison (representative)

- prevalence=0.01: LLM recall=0.0432, precision=0.3530, positive-F1=0.0759, FP/TP=0.00, accuracy=0.9904
- prevalence=0.05: LLM recall=0.0399, precision=0.8690, positive-F1=0.0755, FP/TP=0.00, accuracy=0.9520
- prevalence=0.10: LLM recall=0.0395, precision=0.9850, positive-F1=0.0754, FP/TP=0.00, accuracy=0.9040

LLM (GPT/DeepSeek) is highly conservative: precision ~1.0 (it almost never predicts strong_action), recall ~0.04 (it misses >95% of true strong_action cases). Accuracy is high only because the negative class dominates.

---

## 4. Required answers

### **Answer 1 — R4 usability at 1/3/5/10% prevalence:** R4 recall is essentially flat (0.3626 @1%, 0.3606 @3%, 0.3585 @5%, 0.3632 @10%), so R4 *detects* about a third of true strong_action cases at every prevalence. However, R4 is **standalone-usable only at >=10% prevalence** (FP/TP=11.7, NNR=12.7); below 10% the FP/TP ratio explodes (158 @1%, 25.6 @5%), making standalone screening impractical. R4 must therefore be positioned as a *second-stage* router inside a two-stage pipeline at low prevalence, not as a standalone screen.

### **Answer 2 — FP/TP acceptability:** FP/TP is unacceptable at 1% (158 false positives per true positive), borderline at 5% (25.6), and approaches operational tolerance only at >=10% (11.7 @10%, 7.4 @15%, 5.2 @20%). Standalone R4 screening at <5% prevalence is NOT supported by FP/TP; a high-precision first stage (e.g., LLM-gated) is required to keep R4's false-positive load manageable.

### **Answer 3 — accuracy is misleading:** LLM accuracy at 1% prevalence is 0.9904 (because the majority class dominates), but LLM recall is only ~0.0432. R4 accuracy is much lower (0.5339) yet R4 recall is ~8x higher (0.3626 vs 0.0432). Accuracy is dominated by the negative class at low prevalence and obscures the screening signal; recall, positive-F1, and FP/TP are the operative metrics. **Accuracy must NOT be used as the headline metric for low-prevalence screening.**

### **Answer 4 — R4 screening positioning:** R4 screening positioning is **partially supported**. R4 captures a stable ~36% of true strong_action cases across all prevalence levels, including 3.19 LLM-missed strong cases per 1000 samples at 1% prevalence and 32.36 at 10%. R4 retains independent value as a *complementary* second-stage strong_action detector that recovers LLM-missed cases, but its standalone-usable window is prevalence >= 10%. The recommended deployment is **two-stage**: LLM high-precision first stage -> R4 second-stage recall booster on LLM-rejected cases.

---

## 5. Verdict

- **R4 standalone-usable window:** prevalence >= 10% (FP/TP <= 12, NNR <= 13).
- **R4 two-stage window:** prevalence 1-10% (must be gated by a high-precision first stage).
- **R4 NOT recommended as standalone screen below 5% prevalence.**
- **R4 captures LLM-missed strong_action at every prevalence** — this is R4's independent value.
- **Headline metric for low-prevalence screening must be recall and FP/TP, NOT accuracy.**

---

## 6. Prohibitions enforced

- No gold annotation — PASS (silver labels only).
- No API calls — PASS (results reused from v3_15 simulation).
- No paper modification — PASS.
- No original-data modification — PASS.
- No simulation-as-natural-distribution — PASS (prevalence is imposed by resampling, clearly labelled).
- No silver-as-gold — PASS.
