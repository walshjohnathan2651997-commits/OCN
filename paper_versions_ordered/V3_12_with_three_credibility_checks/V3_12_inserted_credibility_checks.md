# V3.12 Inserted Credibility Checks — Insertion Map

**Version:** V3.12 With Three Credibility Checks
**Date:** 2026-07-04
**Type: Non-gold robustness analysis.** Does not replace gold adjudication.

This document lists where the three non-gold credibility checks were inserted into V3.12, the key numbers used, which conclusions can and cannot be written, and how this strengthens V3.11's main line.

---

## 1. New Section Location

| Item | Detail |
|---|---|
| New section title | **§VIII.D Robustness and Credibility Checks Before Gold Adjudication** |
| Parent section | §VIII Discussion |
| Position | Inserted between §VIII.C (Boundary Cases Are Part of Evidence Sufficiency) and the prior §VIII.D (now renumbered to §VIII.E, What Remains Unresolved) |
| Subsections | §VIII.D.A Evidence Necessity Check; §VIII.D.B Screening Utility Test; §VIII.D.C Label-Shift Stress Test; §VIII.D Summary of §VIII.D |
| Other touched locations | Abstract (+1 sentence); §I organization paragraph (+1 clause); §IX Limitations (+item 8) |

## 2. Key Numbers Used (all from already-existing data, predictions, scores)

### A. Evidence Necessity Check

| Layer | Condition | Value |
|---|---|---|
| Layer A (NLI audit, 444 samples) | correct evidence accuracy | 0.4324 |
| Layer A | empty evidence accuracy | 0.2545 |
| Layer A | shuffled evidence accuracy | 0.3851 |
| Layer A | same-domain wrong evidence accuracy | 0.2568 |
| Layer A | correct→empty drop | −0.1779 |
| Layer A | correct→same_domain_wrong drop | −0.1757 |
| Layer A | correct→shuffled drop | −0.0473 |
| Layer B (TF-IDF cosine, 444 samples) | correct evidence mean sim | 0.4131 |
| Layer B | empty evidence mean sim | 0.0000 |
| Layer B | same-domain wrong evidence mean sim | 0.0124 |
| Layer B | shuffled evidence mean sim | 0.4131 (identical to correct — bag-of-words invariance) |
| Cross-layer | TF-IDF/NLI correlation r | −0.2736 (negative — different dimensions, complementary) |

### B. Screening Utility Test (matched-100, 25 true strong)

| Metric | Value |
|---|---|
| R4 predicted strong | 35 |
| TP | 9 |
| FP | 26 |
| FN | 16 |
| Precision | 0.257 |
| Recall | 0.360 |
| Positive-F1 | 0.300 |
| FP/TP ratio | 2.89 (threshold: 10) |
| Review burden | 35.0% |
| R4 captures LLM-missed | 8 |
| Actual FP: supported → strong | 12 |
| Actual FP: mild_scope_overclaim → strong | 13 |
| Actual FP: contradiction_candidate → strong | 1 |
| Total actual FP | 26 |

### C. Label-Shift Stress Test (matched-100, n_strong=25, 1000 bootstrap)

| Retention | R4 F1 (mean, 95% CI) | LLM F1 | Δ(R4−LLM) | Δ 95% CI | R4 wins % | Statistical strength |
|---|---|---|---|---|---|---|
| 70% | 0.2451 [0.1509, 0.3028] | 0.0759 | +0.1692 | [+0.083, +0.264] | 100.0% | robust |
| 60% | 0.2184 [0.1200, 0.3200] | 0.0776 | +0.1408 | [+0.035, +0.280] | 98.6% | marginal-positive (CI lower bound just above 0) |
| 50% | 0.1843 [0.0851, 0.2979] | 0.0706 | +0.1137 | [−0.026, +0.255] | 94.2% | positive but statistically weaker / CI crosses zero |
| 40% | 0.1612 [0.0444, 0.2667] | 0.0776 | +0.0835 | [−0.093, +0.222] | 70.1% | not significant (CI crosses zero) |

Break-even retention ≈ 0.5 (where Δ 95% CI first crosses zero).

## 3. Which Conclusions CAN Be Written

1. **Task evidence-sensitivity (suggest, not prove).** "Evidence perturbation *suggests* the task is evidence-sensitive" — accuracy drops under empty/shuffled/same-domain-wrong perturbation. TF-IDF and NLI probe different dimensions (negative correlation is expected, not contradictory).
2. **R4 screening utility (operational, not standalone).** "R4 provides targeted recall-improving screening signal for strong_action_overclaim" — FP/TP=2.89 (below pre-registered threshold of 10), captures 8 LLM-missed cases. R4 is *not* a final automatic labeler; recall is moderate (0.360), not high.
3. **Label-shift robustness with quantified threshold.** "If gold strong_action retention is around 60% or higher, the silver-stage screening claim has stronger support; at 50%, the point estimate remains positive but uncertainty crosses zero; below 50%, the paper should downgrade according to the pre-registered criteria in §VII.G."
4. **Non-gold caveat.** "These checks are non-gold robustness analyses. They do not replace gold adjudication (§VII)."
5. **R4 macro-F1 still lower than LLM.** "R4's overall macro-F1 remains lower than the LLM judges (0.3280 vs. 0.5523)."

## 4. Which Conclusions CANNOT Be Written

1. **Do NOT write** "R4 fully relies on evidence" — Layer A uses a pre-existing audit on an earlier dataset version; Layer B is a surface-level sanity check. Only *suggest* evidence sensitivity.
2. **Do NOT write** "R4 is a high-recall detector" without qualification — recall is 0.360 (moderate), and R4 is a screening-oriented complement, not a standalone detector.
3. **Do NOT write** "R4 is a final automatic labeler" — the 26 false positives require human/LLM-assisted adjudication (which is exactly §VII).
4. **Do NOT write** "50% retention is a robust pass" — the Δ 95% CI at 50% crosses zero ([−0.026, +0.255]). Must write "positive but statistically weaker / CI crosses zero."
5. **Do NOT write** "non-gold checks validate absolute numbers" — all counts depend on silver labels and may shift under gold.
6. **Do NOT write** "simulated label shift is gold data" — it is a sensitivity probe, not gold.
7. **Do NOT delete** the fact that R4 macro-F1 (0.3280) is lower than LLM (0.5523).
8. **Do NOT delete** the fact that gold adjudication is not yet performed.

## 5. Enhancement to V3.11 Main Line

| V3.11 claim | How V3.12 §VIII.D strengthens it |
|---|---|
| Task is evidence sufficiency calibration (§III) | (A) Evidence perturbation *suggests* the task is evidence-sensitive, ruling out the strongest claim-only shortcut. |
| R4 is a screening-oriented complement (§VIII.A) | (B) Screening utility is operationalized: FP/TP=2.89 below the pre-registered threshold, R4 captures 8 LLM-missed strong_action cases. |
| Gold adjudication is the validation mechanism (§VII) | (C) The label-shift break-even (~50% retention) quantifies the gold risk and ties directly to the §VII.G downgrade criteria. The gold pilot now has a pre-registered success bar: ≥70% robust, 60% marginal-positive, 50% CI-crosses-zero, <50% downgrade. |
| R4 macro-F1 is lower than LLM (§VIII.A, §IX.4) | Preserved unchanged. §VIII.D does not claim R4 is better overall; it claims R4 provides targeted screening signal on the high-risk boundary class. |
| Silver labels are validation-pending (§IX.1) | Preserved unchanged. §VIII.D explicitly labels itself non-gold and adds a Limitations item (§IX.8) restating the caveat. |

**Net effect:** V3.12 strengthens V3.11's *relative* pattern (R4 > LLM on strong_action) with three non-gold checks, while preserving every silver-stage caveat and the gold-adjudication dependency. No experimental number is changed; no gold claim is made.
