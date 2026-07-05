# Balanced SimClaim vs Low-Prevalence Simulation: Interpretation Guide

**Task:** V3.15 Low-Prevalence Screening Simulation
**Date:** 2026-07-05
**Status:** Simulated low-prevalence screening analysis (NOT real natural distribution; NOT gold; NOT new experiments)
**Companion file:** `low_prevalence_screening_report.md`, `low_prevalence_screening_metrics.csv`, `review_budget_curve.csv`

---

## 1. Purpose of this document

This document explains how to interpret the relationship between two distinct evaluation settings used in the CESE-OCN paper:

1. **Balanced SimClaim diagnostic set** (444 pairs, 1:1:1:1, 25% prevalence per class) — used in the main paper §VI.B, §VIII.D.B.
2. **Low-prevalence screening simulation** (V3.15, this directory) — simulated 1%, 3%, 5%, 10%, 15%, 20%, 25% prevalence via bootstrap resampling.

Both are reported in the paper, and **they are NOT contradictory** — they answer fundamentally different questions. Misreading one as the other leads to incorrect conclusions about R4's value.

---

## 2. The two settings side by side

| Dimension | Balanced SimClaim (main paper) | Low-prevalence simulation (V3.15) |
| --- | --- | --- |
| **Question answered** | Can R4 *recognize* the boundary between mild_scope_overclaim and strong_action_overclaim under controlled conditions? | Can R4 *screen* for strong_action_overclaim when it is rare, as in real scientific writing? |
| **Evaluation type** | Boundary recognition (diagnostic-stage) | Deployment-style screening stress test |
| **Prevalence of strong_action** | 25% (1:1:1:1 balanced) | 1%, 3%, 5%, 10%, 15%, 20%, 25% (simulated) |
| **Sample construction** | Controlled counterfactual diagnostic set (444 pairs, 111 per class, 6 domains) | Bootstrap resampling of 100 matched samples with controlled prevalence and 80/15/5 non-strong composition |
| **Primary metrics** | Macro-F1, per-class F1, strong_F1, confusion matrix | Recall, precision, FP/TP, NNR (Number Needed to Review), review burden, review budget curve |
| **Accuracy role** | Reported, but not the headline metric | Reported as auxiliary only — explicitly called misleading at low prevalence |
| **Gold status** | Silver labels (pre-gold); gold pilot protocol frozen but annotation NOT begun | Silver labels (pre-gold); same base predictions, resampled |
| **What it represents** | An upper-bound stress test of R4's discrimination ability under balanced conditions | A lower-bound stress test of R4's deployment value under realistic class imbalance |
| **What it does NOT represent** | Real-world deployment performance | Real natural distribution (composition is heuristic) |

---

## 3. Why balanced SimClaim exists: boundary recognition

The balanced SimClaim diagnostic set is a **controlled counterfactual diagnostic set**, not a natural-prevalence corpus. It was constructed with deliberate 1:1:1:1 balance so that:

- R4's per-class discrimination ability can be measured without prevalence artifacts.
- The hardest boundary (`mild_scope_overclaim` vs `strong_action_overclaim`) gets enough positive cases (111 each) for a meaningful F1.
- Confusion matrices are not dominated by the majority class.
- Macro-F1 reflects true per-class performance, not majority-class accuracy.

**Interpretation rule for balanced SimClaim:** A macro-F1 of 0.33 on balanced SimClaim means R4 has *boundary-recognition* ability that is measurably above chance (chance = 0.25 for 4-class balanced). It does NOT mean R4 will classify 33% of real-world scientific claims correctly — that depends on the real prevalence, which is NOT 25%.

**Forbidden inference:** "R4 macro-F1 = 0.33 on SimClaim, so R4 will achieve 33% accuracy in production." This is wrong because (a) production prevalence is not 25%, (b) macro-F1 is not accuracy, (c) SimClaim is a counterfactual diagnostic set, not a representative sample of scientific writing.

---

## 4. Why low-prevalence simulation exists: deployment stress test

Real scientific writing is **not balanced**. In a typical paper, most claims are `supported`, a few are `mild_scope_overclaim`, very few are `strong_action_overclaim`, and `contradiction_candidate` is rare. The low-prevalence simulation asks:

- If `strong_action_overclaim` is only 1%, 3%, 5%, 10% of claims, does R4 still add value?
- How does R4's precision drop as prevalence drops?
- Is R4's review burden (fraction of population flagged) manageable at low prevalence?
- Can LLMs substitute for R4 at low prevalence? (Answer: NO — LLMs have high accuracy but ~4% recall, the screening failure mode.)

**Interpretation rule for low-prevalence simulation:** A FP/TP of 121 at 1% prevalence means R4 is NOT viable as a standalone screener at 1% prevalence. It does NOT mean R4 is useless — R4 captures 36% of true strong_action cases that all three LLM judges miss (3.19 per 1000 samples at 1% prevalence). R4's value at low prevalence is as a **first-stage high-recall filter** in a two-stage pipeline, NOT as a standalone classifier.

**Forbidden inference:** "R4 FP/TP = 121 at 1% prevalence, so R4 fails in production." This is wrong because (a) the simulation uses heuristic non-strong composition (80/15/5), not empirically validated natural distribution; (b) R4 is positioned as a screening complement, not a standalone classifier; (c) the two-stage pipeline (R4 → LLM/human) is the recommended deployment configuration, not tested here.

---

## 5. The two settings are NOT contradictory

A reader might see:

- Balanced SimClaim: R4 strong_F1 = 0.40, macro-F1 = 0.33 — "R4 works."
- Low-prevalence simulation: R4 FP/TP = 121 at 1%, precision = 0.78% — "R4 doesn't work."

These are **not contradictions**. They are answers to different questions:

| Question | Setting | Answer |
| --- | --- | --- |
| Can R4 distinguish mild from strong under balanced conditions? | Balanced SimClaim | YES — strong_F1 = 0.40, above chance (0.25). |
| Can R4 screen for strong_action when it is rare (1%)? | Low-prevalence sim | NOT as standalone (FP/TP = 121), but YES as first-stage filter (captures LLM-missed cases). |
| Does R4's recall degrade at low prevalence? | Low-prevalence sim | NO — recall is stable at ~0.36 across all prevalences. |
| Does R4's precision degrade at low prevalence? | Low-prevalence sim | YES — precision drops from 0.21 (25%) to 0.008 (1%). |
| Is R4's balanced macro-F1 representative of deployment performance? | Both | NO — balanced macro-F1 (0.33) cannot be extrapolated to deployment; deployment requires prevalence-aware metrics (FP/TP, NNR). |

**The correct reading:** R4 has demonstrable boundary-recognition ability (balanced SimClaim) AND demonstrable screening value at low prevalence (low-prevalence simulation), but the *form* of value differs:
- At balanced prevalence: R4 is a viable standalone classifier (FP/TP = 3.8).
- At low prevalence: R4 is a viable first-stage filter (high recall, captures LLM-missed cases), but NOT a viable standalone classifier (FP/TP = 25–121).

---

## 6. Why balanced macro-F1 cannot represent real deployment performance

Macro-F1 on a balanced 4-class set has three properties that make it **non-representative** of deployment:

1. **Equal class weighting.** Macro-F1 averages F1 across the four classes equally. In deployment, the cost of missing a `strong_action_overclaim` is much higher than the cost of misclassifying a `supported` claim. Macro-F1 does not capture this asymmetry.
2. **No prevalence artifact.** Balanced SimClaim has 25% prevalence per class. Real deployment has 1–10% `strong_action_overclaim` prevalence. A system that achieves macro-F1 = 0.33 on balanced data may have very different precision/recall trade-offs at low prevalence.
3. **No review-burden information.** Macro-F1 does not tell you how many samples the system flags for review. In deployment, review burden is a critical operational metric (a system that flags 46% of samples for review may be unusable regardless of recall).

**What to report in deployment:** FP/TP ratio, NNR, recall, precision, review burden, and review budget curve. Macro-F1 should be reported only as a diagnostic-stage reference, NOT as a deployment performance estimate.

---

## 7. Why precision drops and recall/FP-TP/review-burden matter more at low prevalence

At low prevalence, **precision is mathematically penalized** even when the classifier's behavior is unchanged. Concretely:

- R4 flags ~46% of samples as `strong_action_overclaim` regardless of prevalence (frozen thresholds).
- At 25% prevalence: of the 46% flagged, ~21% are true strong (precision = 0.21).
- At 1% prevalence: of the 46% flagged, ~0.78% are true strong (precision = 0.008).

R4's behavior is the same; only the prior changes. This is **Bayesian**: the posterior (precision) is dominated by the prior (prevalence) when the prior is small.

**Implication for metric selection at low prevalence:**

| Metric | Behavior at low prevalence | Should it be the primary metric? |
| --- | --- | --- |
| **Recall** | Stable (R4: ~0.36 across all prevalences) — measures the classifier's intrinsic ability to capture positives. | YES — primary metric. |
| **FP/TP ratio** | Increases as prevalence drops (R4: 3.8 → 121) — measures the operational cost of screening. | YES — primary metric. |
| **NNR (Number Needed to Review)** | Increases as prevalence drops (R4: 5 → 159) — measures human review load per true positive. | YES — primary metric. |
| **Review burden** | Fixed (R4: ~46%) — measures capacity requirement. | YES — primary metric. |
| **Precision** | Drops as prevalence drops (R4: 0.21 → 0.008) — mathematically inevitable, NOT a classifier quality signal. | NO — report but do not optimize at low prevalence. |
| **Positive-F1** | Drops (R4: 0.26 → 0.015) — dominated by precision drop. | NO — secondary metric. |
| **Accuracy** | MISLEADING — LLMs achieve 99% accuracy at 1% prevalence with 4.3% recall, hiding the screening failure mode. | NO — auxiliary only, with explicit caveat. |

**Paper-level guidance:** When reporting low-prevalence results, lead with recall, FP/TP, NNR, and review burden. Explicitly state that precision is prevalence-dependent and should not be compared across prevalence levels as a classifier quality signal.

---

## 8. What the paper may and may not claim

### MAY claim (with appropriate framing)

1. R4 has boundary-recognition ability on the balanced SimClaim diagnostic set (strong_F1 = 0.40, above chance).
2. R4's recall is stable (~0.36) across simulated prevalences from 1% to 25%.
3. At low prevalence (1–5%), R4 is NOT viable as a standalone screener (FP/TP = 25–121).
4. At low prevalence, R4 retains value as a first-stage high-recall filter that captures strong_action cases LLM judges miss (3.19 per 1000 at 1% prevalence).
5. LLM judges show a high-accuracy / low-recall failure mode at low prevalence (99% accuracy, 4.3% recall at 1%).
6. The two-stage pipeline (R4 → LLM/human) is the recommended deployment configuration, NOT tested in this paper.
7. Balanced macro-F1 cannot be extrapolated to deployment performance; prevalence-aware metrics (FP/TP, NNR) are required.

### MAY NOT claim

1. R4 is a viable standalone screener at 1% prevalence. (FALSE — FP/TP = 121.)
2. R4's balanced macro-F1 represents its real-world deployment performance. (FALSE — different prevalence, different metric.)
3. The low-prevalence simulation reflects a real natural distribution. (FALSE — composition 80/15/5 is heuristic, not empirically validated.)
4. R4 outperforms LLMs at low prevalence. (FALSE — R4 and LLMs are complementary, not rankable; R4 has higher recall, LLMs have higher precision and accuracy.)
5. The two-stage pipeline is empirically validated. (FALSE — proposed, not tested.)
6. The low-prevalence simulation replaces gold validation. (FALSE — all results on silver labels; gold pilot protocol frozen, annotation NOT begun.)
7. The simulation results are generalizable to all scientific writing. (FALSE — base pool is 100 matched samples, 6 domains; generalization requires larger base pool and natural-prevalence corpus.)

---

## 9. One-paragraph summary (paste-ready for paper §VIII.D.E or limitations)

> The balanced SimClaim diagnostic set (25% prevalence per class) measures R4's boundary-recognition ability under controlled conditions and is not representative of deployment performance. A complementary low-prevalence screening simulation (V3.15) resamples the same predictions at 1%–25% `strong_action_overclaim` prevalence with a heuristic 80/15/5 non-strong composition. The simulation shows that R4's recall is stable (~0.36) across prevalences, but its precision drops sharply at low prevalence (FP/TP = 121 at 1%, 12 at 10%, 3.8 at 25%), making R4 non-viable as a standalone screener below 10% prevalence but still valuable as a high-recall first-stage filter that captures `strong_action_overclaim` cases missed by LLM judges. LLM judges exhibit a high-accuracy / low-recall failure mode at low prevalence (99% accuracy, 4.3% recall at 1%), making accuracy a misleading deployment metric. The two settings are not contradictory: balanced SimClaim answers "can R4 recognize the boundary?" (yes, above chance); the low-prevalence simulation answers "can R4 screen for rare strong_action overclaims?" (yes, as a first-stage filter, not as a standalone classifier). The recommended deployment configuration is a two-stage pipeline (R4 → LLM/human), which is proposed but not evaluated in this paper. All simulation results are on silver labels and use a heuristic non-strong composition; gold validation and natural-prevalence corpus studies are required before deployment claims can be made.

---

## 10. Prohibitions enforced

- No gold annotation — PASS (all results on silver labels).
- No API calls — PASS (only existing predictions reused).
- No new model training — PASS (only existing R4/LLM predictions).
- No threshold retuning — PASS (R4 thresholds frozen).
- No original data modification — PASS (only bootstrap resampling).
- No simulation written as real natural distribution — PASS (clearly labelled "simulated low-prevalence screening analysis").
- No silver written as gold — PASS (all results labelled silver-stage).
- No contradiction between balanced and low-prevalence results — PASS (different questions, different metrics, different interpretations).
- No extrapolation of balanced macro-F1 to deployment — PASS (explicitly forbidden in §6 and §8).
