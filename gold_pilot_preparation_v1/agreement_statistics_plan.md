# Agreement Statistics Plan — Gold Pilot v1

**Date:** 2026-07-04
**Purpose:** Pre-registered analysis plan for inter-annotator agreement on the 50-sample gold pilot. This plan is fixed before annotation begins to prevent post-hoc analysis bias.

---

## 1. Overall agreement

**Metric:** Raw agreement = (# pairs where annotator A label = annotator B label) / (total pairs).

**Report:** Overall agreement rate with 95% confidence interval (Wilson score interval).

**Interpretation:**
- ≥ 0.80: strong agreement; taxonomy is drawable.
- 0.60-0.79: moderate agreement; some boundaries need clarification.
- < 0.60: weak agreement; taxonomy needs substantial revision.

## 2. Cohen's kappa (overall)

**Metric:** Cohen's κ across all 50 pairs, treating the five labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate, unsure) as nominal categories.

**Report:** κ with 95% confidence interval (bootstrap, 1000 resamples).

**Interpretation (Landis-Koch benchmarks, nominal):**
- ≥ 0.81: almost perfect.
- 0.61-0.80: substantial.
- 0.41-0.60: moderate.
- 0.21-0.40: fair.
- ≤ 0.20: poor.

**Pre-registered threshold:** κ ≥ 0.60 overall is required to claim the taxonomy is reliably drawable by independent annotators.

## 3. Per-boundary agreement

For each boundary, compute pairwise agreement and Cohen's κ on the subset of cases where at least one annotator chose one of the two boundary classes.

### 3.1 supported_vs_mild

**Subset:** Cases where annotator A or B chose `supported` or `mild_scope_overclaim`.
**Binary recode:** supported = 0, mild_scope_overclaim = 1.
**Metric:** Cohen's κ on the binary recode.
**Interpretation:** κ ≥ 0.6 → boundary is drawable. κ < 0.4 → boundary needs clarification.

### 3.2 mild_vs_strong (PRIMARY BOUNDARY)

**Subset:** Cases where annotator A or B chose `mild_scope_overclaim` or `strong_action_overclaim`.
**Binary recode:** mild_scope_overclaim = 0, strong_action_overclaim = 1.
**Metric:** Cohen's κ on the binary recode.
**Pre-registered decision rule:**
- **κ ≥ 0.4:** `strong_action_overclaim` is defensible as a separate class. The paper's central taxonomy holds. Proceed to larger gold adjudication.
- **κ < 0.4:** The mild/strong boundary is not reliably drawable. Consider merging `strong_action_overclaim` into `mild_scope_overclaim`. The paper's central contribution weakens — `strong_action_overclaim` would need to be re-framed as a severity sub-type of `mild_scope_overclaim`, not a separate class.

This is the **single most important number** in the gold pilot. It directly tests whether the paper's central class is drawable by independent annotators.

### 3.3 strong_vs_contradiction

**Subset:** Cases where annotator A or B chose `strong_action_overclaim` or `contradiction_candidate`.
**Binary recode:** strong_action_overclaim = 0, contradiction_candidate = 1.
**Metric:** Cohen's κ on the binary recode.
**Interpretation:** κ ≥ 0.6 → detail-swapping is reliably classified as contradiction. κ < 0.4 → the boundary between action-escalation and directional conflict needs clarification.

## 4. Unsure rate

**Metric:** For each annotator, (# pairs labeled `unsure`) / (total pairs).

**Report:** Unsure rate per annotator, and the union rate (# pairs where A or B was unsure).

**Interpretation:**
- Unsure rate ≤ 5%: annotators find the taxonomy applicable.
- Unsure rate 5-15%: some boundary cases are genuinely hard; review the `confusion_if_any` field for patterns.
- Unsure rate > 15%: the taxonomy or guideline is insufficient; annotators cannot reliably apply it.

**Pre-registered rule:** If the union unsure rate > 20%, the annotation guideline must be revised before adjudication. Pairs where both annotators are `unsure` are flagged as `taxonomy_revision_needed` in the adjudication template.

## 5. Per-class precision-like agreement

For each class C, compute:

- **Precision (annotator A → B):** Of pairs where A labeled C, the fraction where B also labeled C.
- **Precision (annotator B → A):** Of pairs where B labeled C, the fraction where A also labeled C.
- **F1 (symmetric):** Harmonic mean of the two precision values.

**Report:** Per-class precision-like F1 for all four classes (plus `unsure`).

**Interpretation:**
- High F1 (≥ 0.7) on `contradiction_candidate`: expected — contradiction is the most separable class.
- High F1 (≥ 0.7) on `supported`: expected — supported is the easiest class.
- Moderate F1 (0.4-0.7) on `mild_scope_overclaim`: expected — mild is a residual category.
- Low F1 (< 0.4) on `strong_action_overclaim`: **red flag.** If independent annotators cannot agree on `strong_action_overclaim`, the class is not reliably drawable, regardless of the mild/strong κ.

## 6. Confidence-analysis (secondary)

For each pair, compute the mean confidence (A confidence + B confidence) / 2.

**Report:** Mean confidence for agreed pairs vs. disagreed pairs. A large gap (agreed mean ≥ 4, disagreed mean ≤ 3) confirms that confidence tracks agreement — annotators know when they are uncertain.

## 7. Confusion matrix

Report the full 5×5 confusion matrix (A rows × B columns), including `unsure` as a row/column.

## 8. Decision rules (pre-registered)

| Outcome | Action |
|---|---|
| Overall κ ≥ 0.60 AND mild_vs_strong κ ≥ 0.40 | Taxonomy holds. Proceed to larger gold adjudication (100-200 pairs). Re-evaluate R4 and LLM judges against gold labels. |
| Overall κ ≥ 0.60 BUT mild_vs_strong κ < 0.40 | Taxonomy partially holds. `strong_action_overclaim` may need to be merged with `mild_scope_overclaim`. Paper's central contribution weakens. Revise taxonomy before larger gold effort. |
| Overall κ < 0.60 | Taxonomy is not reliably drawable. Major revision needed. Do not proceed to larger gold effort until guideline and taxonomy are revised. |
| LLM strong_action-F1 on gold ≥ 0.30 | LLM under-detection finding was a silver-label artifact. Paper's central claim weakens substantially. Report honestly. |
| LLM strong_action-F1 on gold ≤ 0.15 | LLM under-detection finding holds against gold. Paper's central claim is strengthened. Can report as "validated on gold pilot (N=50)." |
| R4 strong_action-F1 on gold ≥ 0.25 | R4's targeted value holds against gold. Can report as "validated on gold pilot (N=50)." |
| R4 strong_action-F1 on gold < 0.15 | R4's targeted value was a silver-label artifact. Paper's central claim weakens. Report honestly. |
| Gold reveals strong_action cases mostly re-labeled as mild | `strong_action_overclaim` class is not separable. Downgrade the class to a severity sub-type of `mild_scope_overclaim`. Paper's central contribution weakens. |

## 9. What will NOT be done

- **No post-hoc relabeling.** Once annotators submit, their labels are fixed. The adjudicator may override, but annotator A and B labels in the agreement statistics are the original submissions.
- **No excluding pairs to improve κ.** All 50 pairs are included in the agreement statistics. Pairs may be flagged as `exclude_due_to_unclear_evidence` in adjudication, but they remain in the agreement calculation.
- **No model-in-the-loop adjudication.** The adjudicator must not consult R4, LLM, or any model prediction when assigning `adjudicated_label`. Adjudication is human-only.
- **No silver-label-informed adjudication.** The adjudicator must not consult the silver labels when assigning `adjudicated_label`. Adjudication is independent of silver.

## 10. Reporting

After adjudication, the following will be reported:
1. Overall agreement + 95% CI.
2. Overall Cohen's κ + 95% CI.
3. Per-boundary κ (supported_vs_mild, mild_vs_strong, strong_vs_contradiction).
4. Per-class precision-like F1.
5. Unsure rate per annotator + union rate.
6. Full 5×5 confusion matrix.
7. Mean confidence for agreed vs. disagreed pairs.
8. Adjudicated label distribution.
9. Per-pair adjudication reasons (for boundary cases).
10. Decision-rule outcomes (which pre-registered rules were triggered).

This report will be saved as `gold_pilot_agreement_results.md` (to be generated after annotation + adjudication are complete — NOT in this preparation pack).
