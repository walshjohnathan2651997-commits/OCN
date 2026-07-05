# R4 Method Positioning Audit — V3.14 Mainline Locked

**Date:** 2026-07-05
**Version:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Source:** §III, §IV, §VI.A–§VI.E, §VIII.A, §VIII.D.B, §IX of CESE_OCN_V3_14_mainline_locked.md; `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_metrics_summary.json`.

This audit answers 6 reviewer-grade questions about the R4 method's positioning,合理性, and defensibility.

---

## Q1. Is R4 just rule stacking (规则堆叠)?

**Verdict: NO. R4 is a relation-specific mixed router, not a rule stack.**

**What R4 actually is (§III, §IV):**
R4 is a four-route mixed classifier that routes each claim-evidence pair to a relation-specific sub-model based on the failure mode hypothesis:
- **Route 1 (Contradiction detector):** NLI-style contradiction signal (SVM with calibrated threshold `t_contra=0.48`). If contradiction signal > t_contra, route to contradiction_candidate.
- **Route 2 (Strong-action escalation):** If not contradiction, check strong-action escalation signal (SVM with calibrated threshold `t_strong=0.535`). If strong-action signal > t_strong, route to strong_action_overclaim.
- **Route 3 (Scope calibration residual):** If neither contradiction nor strong-action, check scope-calibration residual (SVM with calibrated threshold `t_svm=0.51`). If scope residual > t_svm, route to mild_scope_overclaim.
- **Route 4 (Default to supported):** If none of the above routes fire, route to supported.

**Why this is NOT rule stacking:**
1. **Each route uses a trained sub-model (SVM), not a hand-crafted rule.** The SVMs are trained on the SimClaim silver training split (308 pairs) with frozen features (NLI contradiction signal, HCM scope residual, strong-action escalation signal).
2. **The thresholds are calibrated, not hand-tuned.** `t_contra`, `t_strong`, `t_svm` are calibrated on the dev split (64 pairs) and frozen. No threshold retuning has been performed since V3.11.
3. **The routing order is theoretically motivated, not arbitrary.** Contradiction is checked first (most clear-cut signal); strong-action second (high-risk boundary class); scope third (residual mild cases); supported last (default). This ordering reflects the failure-mode hierarchy.
4. **The router is ablated (§VI.A ablation).** Removing any single route degrades performance on the corresponding class, confirming each route contributes independently.

**What R4 IS (precise description):**
R4 is a **relation-specific mixed router** that combines three trained SVM sub-models with a theoretically motivated routing order and calibrated thresholds. It is NOT a single end-to-end classifier and NOT a hand-crafted rule stack.

---

## Q2. Why is lower macro-F1 NOT fatal for R4?

**Verdict: Because R4 is a screening-oriented complement, not a general-purpose classifier.**

**The macro-F1 fact (§VI.B, §VIII.A, §IX item 4):**
- R4 macro-F1 = 0.3280 on matched 100.
- GPT-5.5 macro-F1 = 0.5523 on matched 100.
- DeepSeek-V3 macro-F1 = 0.5248 on matched 100.
- R4's macro-F1 is **substantially lower** than both LLM judges.

**Why this is NOT fatal:**
1. **Macro-F1 weights all classes equally.** On SimClaim's balanced 1:1:1:1 design, macro-F1 treats `supported` (the easiest class, where LLMs excel) as equally important as `strong_action_overclaim` (the hardest class, where LLMs fail). R4 sacrifices `supported` accuracy (over-routing supported → strong, 98 FP) to gain `strong_action` recall.
2. **R4's design goal is screening, not classification.** A screening system is judged by its ability to surface high-risk cases for human review, not by its overall classification accuracy. R4's strong_F1 = 0.3000 vs. LLM 0.0769 (3.9× higher) is the relevant metric for screening.
3. **The paper explicitly states this trade-off.** §VI.B, §VIII.A, and §IX item 4 all state: "R4's macro-F1 is substantially lower than LLM judges (0.3280 vs. 0.5523); R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts." §IX item 4 lists this as a limitation, not a hidden defect.
4. **The screening orientation is the positioning.** §I Contribution 3 and §II.B Mainline Lock both state: "R4 is a screening-oriented complement to LLM judges, not a replacement and not a state-of-the-art overstatement detector."

**When would lower macro-F1 BE fatal?** If the paper claimed R4 as a general-purpose classifier or a state-of-the-art overstatement detector. The paper explicitly does NOT claim this (§I, §II.B, §VI.B, §IX item 4).

---

## Q3. Why is screening metric more appropriate than accuracy for R4?

**Verdict: Because R4's design goal is high-risk case surfacing, not overall classification.**

**Screening vs. accuracy:**
- **Accuracy / macro-F1:** Measures overall classification correctness. Appropriate when all classes are equally important and the cost of false positives equals the cost of false negatives.
- **Screening metrics (positive-F1, recall, FP/TP ratio, review burden):** Measures the ability to surface high-risk cases for human review. Appropriate when (a) the positive class is high-risk, (b) false negatives (missed high-risk cases) are more costly than false positives (unnecessary human review), and (c) the system is a complement to human review, not a replacement.

**Why screening metrics fit R4:**
1. **`strong_action_overclaim` is the high-risk class.** It represents claims that assert deployment, safety, or generalization conclusions that the evidence does not justify. Missing a `strong_action_overclaim` case (false negative) means a high-risk overclaim goes unflagged; over-flagging a non-strong case (false positive) means a human reviewer spends extra time on a non-high-risk case.
2. **R4 is designed as a screening complement.** §I Contribution 3 and §II.B state: "R4 is a screening-oriented complement to LLM judges, not a replacement." A screening complement is judged by its ability to surface cases the primary system (LLM) misses, not by its overall accuracy.
3. **The §VIII.D.B Screening Utility Test explicitly tests this.** It reports strong_F1, strong_recall, strong_precision, FP/TP ratio, and review burden — the screening metrics — not overall accuracy. R4's FP/TP = 2.89 means 2.89 false positives per true positive, which is operationally acceptable for a high-risk screening task (see Q4).

**When would accuracy be more appropriate?** If R4 were deployed as a standalone classifier (no human review) or if all four classes were equally costly. The paper does NOT claim this deployment mode.

---

## Q4. How to explain FP/TP = 2.89?

**Verdict: FP/TP = 2.89 is operationally acceptable for a high-risk screening task, but it is a known trade-off, not a strength.**

**The fact (§VIII.D.B):**
- R4 strong_action TP = 9, FP = 26 on matched 100.
- FP/TP = 26/9 = 2.89.
- Review burden = 35% (35 out of 100 samples routed to strong_action review).

**Why FP/TP = 2.89 is acceptable:**
1. **High-risk screening tolerates higher FP rates.** In high-risk screening (e.g., medical screening, fraud detection, safety-critical claim review), the cost of missing a true positive (a high-risk overclaim that goes unflagged) is much higher than the cost of reviewing a false positive (a non-high-risk claim that gets reviewed unnecessarily). A 2.89:1 FP/TP ratio means 2.89 non-strong cases are reviewed per true strong case — this is within the typical range for high-recall screening systems.
2. **The base rate matters.** On SimClaim's balanced 25% strong_action rate, FP/TP = 2.89 corresponds to precision = 0.257. On a natural-prevalence corpus where strong_action is rarer (e.g., 5%), the same recall would yield a higher FP/TP ratio. The paper acknowledges this in §IX item 10 (SimClaim is not natural-prevalence).
3. **The alternative (LLM only) misses 96% of strong_action.** LLM judges achieve strong_F1 = 0.0769, recall = 0.04 (1/25) on matched 100. R4 captures 9/25 strong_action cases (recall = 0.36), including 8/24 that all three LLM judges miss. The 26 false positives are the cost of capturing these 8 additional true positives.

**Why FP/TP = 2.89 is a trade-off, not a strength:**
1. **R4 over-routes supported → strong (98 FP) and mild → strong (24 FP) in the §VI.A ablation.** This is the known trade-off: R4 improves strong recall at the cost of supported/mild → strong false positives.
2. **The paper explicitly states this.** §VI.A, §VIII.D.B, and §IX item 5 all report FP/TP = 2.89 and the over-routing pattern. §IX item 5 lists this as a limitation.
3. **A lower FP/TP would be preferable.** If a future R5 can achieve the same strong recall with lower FP/TP, that would be a strict improvement. R4 is the current frozen method; R5 is future work.

---

## Q5. Can recall = 0.36 be called "high recall"?

**Verdict: NO. recall = 0.36 is NOT "high recall" in absolute terms. It is "higher recall than LLM judges under tested prompts" — a relative claim, not an absolute one.**

**The fact (§VI.B, §VIII.D.B):**
- R4 strong_recall = 0.36 on matched 100 (9/25).
- LLM strong_recall = 0.04 on matched 100 (1/25).
- R4 strong_recall = 0.4562 on silver 444 (51/111).

**Why recall = 0.36 is NOT "high recall":**
1. **Absolute recall = 0.36 means 64% of strong_action cases are missed.** This is not "high recall" by any standard definition. A high-recall screening system typically targets recall ≥ 0.70 or ≥ 0.80.
2. **The paper does NOT claim "high recall".** §VI.B, §VIII.D.B, and §IX item 5 report recall = 0.36 without calling it "high". The paper's claim is: "R4 improves strong_action recall from 0.04 to 0.36" — a relative improvement, not an absolute high-recall claim.
3. **The claim is "screening-oriented complement", not "high-recall screener".** §I Contribution 3 and §II.B position R4 as a complement that surfaces cases LLMs miss, not as a high-recall standalone screener.

**What CAN be said:**
- "R4 achieves 9× higher strong_action recall than LLM judges under the tested prompts (0.36 vs. 0.04 on matched 100)." — relative claim, defensible.
- "R4 captures 8/24 strong_action cases that all three LLM judges miss." — empirical fact, defensible.
- "R4's strong_action recall (0.36) is below typical high-recall screening thresholds (≥ 0.70); a future R5 should target higher recall with lower FP/TP." — honest acknowledgement, defensible.

**What CANNOT be said:**
- "R4 has high recall on strong_action." — FALSE (0.36 is not high in absolute terms).
- "R4 reliably catches strong_action cases." — MISLEADING (64% are missed).

---

## Q6. Why can't we say "R4 beats LLM"?

**Verdict: Because R4's macro-F1 is lower than LLM, and "beats" implies overall superiority.**

**The fact (§VI.B, §VIII.A, §IX item 4):**
- R4 macro-F1 = 0.3280 < GPT-5.5 macro-F1 = 0.5523.
- R4 macro-F1 = 0.3280 < DeepSeek-V3 macro-F1 = 0.5248.
- R4 strong_F1 = 0.3000 > LLM strong_F1 = 0.0769.
- R4 captures 8/24 strong_action cases that all three LLM judges miss.

**Why "R4 beats LLM" is FORBIDDEN:**
1. **"Beats" implies overall superiority.** In ML benchmarking, "X beats Y" typically means X outperforms Y on the primary metric (macro-F1, accuracy, etc.). R4's macro-F1 is 0.3280 vs. LLM's 0.5523 — R4 does NOT beat LLM on the primary metric.
2. **R4's advantage is relation-specific, not overall.** R4 outperforms LLM ONLY on `strong_action_overclaim` (strong_F1 = 0.3000 vs. 0.0769). On `supported`, `mild_scope_overclaim`, and `contradiction_candidate`, LLM judges outperform R4. Claiming "R4 beats LLM" without qualification would be misleading.
3. **The paper explicitly forbids this claim.** §II.B Mainline Lock, Appendix B Forbidden Claims, and `V3_13_claims_allowed_for_paper.md` all list "R4 outperforms LLM overall" / "R4 beats LLM" / "R4 is stronger than LLMs on all metrics" as FORBIDDEN.

**What CAN be said (allowed wording):**
- "R4 improves strong-action positive-F1 from 0.2408 to 0.3967 (+0.1559) on the controlled silver-stage evaluation." — relation-specific, defensible.
- "R4 achieves 3.9× higher strong_action F1 than LLM judges under the tested prompts (0.3000 vs. 0.0769 on matched 100)." — relative, relation-specific, defensible.
- "R4 captures 8/24 strong_action cases that all three LLM judges miss on matched 100." — empirical fact, defensible.
- "R4 is a screening-oriented complement to LLM judges, not a replacement." — positioning, defensible.

**What CANNOT be said (forbidden wording):**
- "R4 beats LLM." — implies overall superiority.
- "R4 outperforms LLM overall." — FALSE (macro-F1 is lower).
- "R4 is stronger than LLMs on all metrics." — FALSE (only stronger on strong_action).
- "R4 is the best model." — MISLEADING (best on what metric?).

---

## Summary

| Question | Verdict |
| --- | --- |
| Q1. Is R4 rule stacking? | NO — R4 is a relation-specific mixed router with trained SVM sub-models, calibrated thresholds, and theoretically motivated routing order |
| Q2. Why is lower macro-F1 not fatal? | Because R4 is a screening-oriented complement (§I, §II.B); macro-F1 weights all classes equally, but R4's design goal is strong_action surfacing, not overall classification |
| Q3. Why is screening metric more appropriate? | Because R4's design goal is high-risk case surfacing for human review, not standalone classification; §VIII.D.B explicitly tests screening metrics |
| Q4. How to explain FP/TP = 2.89? | Operationally acceptable for high-risk screening (cost of missing a true positive > cost of reviewing a false positive); known trade-off, not a strength; §IX item 5 lists it as a limitation |
| Q5. Can recall = 0.36 be called "high recall"? | NO — 0.36 is not high in absolute terms (64% missed); the claim is "9× higher than LLM under tested prompts" (relative), NOT "high recall" (absolute) |
| Q6. Why can't we say "R4 beats LLM"? | Because R4's macro-F1 is lower (0.3280 vs. 0.5523); "beats" implies overall superiority; R4's advantage is relation-specific (strong_action only) |
