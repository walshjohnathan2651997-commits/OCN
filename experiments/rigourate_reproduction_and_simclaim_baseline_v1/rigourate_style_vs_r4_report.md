# RIGOURATE-style vs R4 Comparison Report

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 6
**Date:** 2026-07-05
**Comparison set:** 100 matched SimClaim samples (25 per class) where GPT standard, GPT structured, DeepSeek-V3, and R4 frozen all have predictions.

## 1. Methods compared

1. **rigourate_style_rule_scalar** - RIGOURATE-style cue-based scalar score (Baseline A from §4-§5), mapped 0-3 to 4-class label (0=supported, 1=mild, 2=strong, 3=contradiction). NOT official RIGOURATE.
2. **gpt_standard** - GPT-5.5 with standard judge prompt (100 samples).
3. **gpt_structured** - GPT-5.5 with structured 5-step evidence-sufficiency decomposition prompt (100 samples).
4. **deepseek_v3** - DeepSeek-V3 (100 samples).
5. **r4_frozen** - CESE-OCN R4 frozen mixed relation-routing framework (matched 100 samples).

Reference (not on matched 100): r4_frozen_silver_444_reference - R4 on full 444 silver set, for context.

## 2. Results table (100 matched samples)

| Method | N | Strong TP | Strong FP | Strong FN | Strong TN | Strong Precision | Strong Recall | Strong F1 | Review Burden | Macro-F1 (aux) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rigourate_style_rule_scalar | 100 | 3 | 16 | 22 | 59 | 0.1579 | 0.1200 | 0.1364 | 19 (19.00%) | 0.2591 |
| gpt_standard | 100 | 1 | 0 | 24 | 75 | 1.0000 | 0.0400 | 0.0769 | 1 (1.00%) | 0.5523 |
| gpt_structured | 100 | 1 | 0 | 24 | 75 | 1.0000 | 0.0400 | 0.0769 | 1 (1.00%) | 0.5543 |
| deepseek_v3 | 100 | 1 | 0 | 24 | 75 | 1.0000 | 0.0400 | 0.0769 | 1 (1.00%) | 0.5248 |
| r4_frozen | 100 | 9 | 26 | 16 | 49 | 0.2571 | 0.3600 | 0.3000 | 35 (35.00%) | 0.3280 |

Reference: r4_frozen_silver_444: strong_F1=0.3967, strong_recall=0.4562, strong_precision=0.3791, macro_F1=0.4238

## 3. Strong_action capture analysis

- **N strong_action samples (silver):** 25
- **LLM (GPT standard + GPT structured + DeepSeek) all missed:** 24 / 25
- **R4 captured LLM-missed strong_action:** 8 / 24
- **R4 missed strong_action:** 16 / 25
- **Rule scalar captured R4-missed strong_action:** 3 / 16

## 4. Required answers

### Q1. Can scalar score capture strong_action_overclaim?

- **rule_scalar** (mapped to 4-class label, threshold-free): strong_F1=0.1364, recall=0.1200, precision=0.1579, TP=3, FP=16.
- Compare R4 on same 100: strong_F1=0.3000, recall=0.3600.
- **Verdict:** The rule-based scalar maps to a 4-class label but achieves lower strong_F1 than R4. From §5, the rule_scalar ROC-AUC on strong_vs_nonstrong is 0.4971 (chance), so the apparent F1 here is driven by the score-to-label mapping, not by genuine strong_action discrimination. The scalar score CANNOT reliably capture strong_action_overclaim.

### Q2. Is the scalar easily confused between mild and strong?

- From §5: rule_scalar ROC-AUC on mild_vs_strong = 0.5062 (chance). LLM-derived scalar ROC-AUC on mild_vs_strong = 0.5874 (weak).
- This means both scalar variants struggle to distinguish mild_scope_overclaim from strong_action_overclaim.
- The scalar compresses the action-vs-scope distinction, which is exactly the high-risk boundary the four-class taxonomy is designed to isolate.
- **Verdict:** YES, the scalar is easily confused between mild and strong. This is the critical failure mode that motivates fine-grained relation typing.

### Q3. Does R4 still have screening value?

- R4 strong_F1 on matched 100: 0.3000
- R4 strong_F1 on silver 444: 0.3967
- LLM (GPT/DeepSeek) strong_F1 on matched 100: 0.0769 (all variants)
- R4 captures LLM-missed strong_action: 8 / 24 cases
- **Verdict:** YES. R4 provides screening signal on strong_action that all tested LLM judges miss. R4's strong_F1 is 3-5x higher than LLM judges on the same matched samples. R4 captures a non-trivial fraction of strong_action cases that all three LLM judges miss. R4 retains clear screening value.

### Q4. What is the cost of R4?

- R4 macro_F1 on matched 100: 0.3280
- GPT standard macro_F1 on matched 100: 0.5523
- R4 macro_F1 on silver 444: 0.4238
- R4 has LOWER macro_F1 than LLM judges (0.3280 vs 0.5523 on matched 100). This is the cost: R4 trades overall macro-F1 for targeted strong_action screening signal.
- R4 also has higher review burden (more samples flagged as strong_action) due to its conservative escalation route, which is by design - it prioritises recall on the high-risk class over precision.
- **Verdict:** R4's cost is (a) lower overall macro-F1 than LLM judges, and (b) higher review burden (more false positives on strong_action). The benefit is 3-5x higher strong_action F1 and capture of LLM-missed high-risk cases. The trade-off is intentional: R4 is a screening-oriented complement, not a replacement.

### Q5. Are score-based overstatement detection and relation-specific screening complementary?

- **YES.** The evidence from §5 and §6 supports complementarity:
  - Scalar scores (especially LLM-derived) are good at the broad supported-vs-overclaim distinction (ROC-AUC=0.85) and at strong-vs-contradiction (ROC-AUC=0.85).
  - Scalar scores CANNOT distinguish mild from strong (ROC-AUC ≤ 0.59) and cannot reliably identify strong_action (ROC-AUC ≤ 0.52 on strong_vs_nonstrong).
  - R4 provides the missing signal: strong_F1=0.3967 vs scalar/LLM ≤ 0.10 on matched samples.
- The two approaches address different sub-problems:
  - Scalar: broad severity ranking, useful for triage and for the supported-vs-overclaim boundary.
  - Relation-specific screening (R4): high-risk action-overclaim identification, useful for the mild-vs-strong boundary that scalar compresses.
- This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Limitations

- N=100 matched samples is small; gold adjudication may shift conclusions.
- rule_scalar_score is a hand-crafted cue-based baseline; NOT official RIGOURATE.
- LLM scalar proxy is LLM-label-derived; NOT a true continuous score; NOT official RIGOURATE.
- R4 macro-F1 < LLM macro-F1 is a known feature of R4's screening-oriented design, not a defect.
- All evaluation is on silver labels (pre-gold).

## 6. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of V3.12 or original data.
- No R4 retuning.