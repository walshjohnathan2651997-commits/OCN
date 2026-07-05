# Agreement Metric Plan v1 — FROZEN

**Version:** 1.0 (frozen)
**Date:** 2026-07-04
**Status:** FROZEN — do not modify after annotation begins.

This file defines the statistics that will be computed after both annotators submit and adjudication is complete.

---

## 1. Overall Agreement

**Metric:** Raw agreement rate between Annotator A and Annotator B (before adjudication).

**Formula:** `count(A_label == B_label) / 50`

**Report:** Overall percentage and count. Example: "32/50 = 64% overall agreement."

**Interpretation:**
- ≥ 0.80: High agreement. Taxonomy is operationalizable.
- 0.60 – 0.79: Moderate agreement. Taxonomy is usable but boundaries need tightening.
- < 0.60: Low agreement. Taxonomy needs revision before further use.

---

## 2. Cohen's Kappa (κ)

**Metric:** Cohen's kappa between Annotator A and Annotator B (before adjudication), computed on the 4-class label set (excluding `unsure` for the primary κ; `unsure` analyzed separately in §5).

**Formula:** `κ = (P_o - P_e) / (1 - P_e)` where `P_o` is observed agreement and `P_e` is expected agreement by chance.

**Implementation:** Use `sklearn.metrics.cohen_kappa_score(A_labels, B_labels)` or equivalent.

**Report:** κ value, 95% confidence interval, and interpretation.

**Interpretation (Landis & Koch 1977, conventional):**
- ≥ 0.81: Almost perfect agreement.
- 0.61 – 0.80: Substantial agreement.
- 0.41 – 0.60: Moderate agreement.
- 0.21 – 0.40: Fair agreement.
- ≤ 0.20: Poor agreement.

**Target for this pilot:** κ ≥ 0.60 (substantial). If κ < 0.40, the taxonomy is not reliably operationalizable and must be revised.

---

## 3. Krippendorff's Alpha (Optional)

**Metric:** Krippendorff's alpha for ordinal data (if labels are treated as ordered: supported < mild < strong < contradiction, though this ordering is debatable).

**Implementation:** Use `krippendorff.alpha` from the `krippendorff` Python package, or compute manually.

**Report:** Alpha value. This is **optional** — if the package is unavailable or the ordinal assumption is questionable, skip this metric and note why.

**Interpretation:**
- ≥ 0.80: High reliability.
- 0.67 – 0.79: Tentative reliability.
- < 0.67: Low reliability; conclusions should be drawn tentatively.

---

## 4. Per-Boundary Agreement

The taxonomy has three key boundaries. For each, compute agreement on the **subset** of cases where at least one annotator assigned a label on that boundary.

### 4.1 `supported_vs_mild` agreement

**Subset:** Cases where A or B assigned `supported` or `mild_scope_overclaim`.

**Metric:** Cohen's kappa on this subset, treating `supported` and `mild_scope_overclaim` as the two classes.

**Interpretation:** This is the weakest boundary in the project's silver-label experiments (mild-F1 = 0.1266). If κ < 0.4 here, the supported/mild distinction needs clearer operationalization.

### 4.2 `mild_vs_strong` agreement

**Subset:** Cases where A or B assigned `mild_scope_overclaim` or `strong_action_overclaim`.

**Metric:** Cohen's kappa on this subset.

**Interpretation:** This is the **hardest boundary** (12/25 questionable/unclear cases in the author sanity audit). **If κ < 0.4, the taxonomy MUST be revised** — the mild/strong distinction is not reliably operationalizable.

### 4.3 `strong_vs_contradiction` agreement

**Subset:** Cases where A or B assigned `strong_action_overclaim` or `contradiction_candidate`.

**Metric:** Cohen's kappa on this subset.

**Interpretation:** This is the second-hardest boundary (6/25 questionable/unclear cases). If κ < 0.4, the strong/contradiction distinction needs revision (possibly the detail-swap rule needs tightening).

---

## 5. Unsure Rate

**Metric:** How often annotators marked `unsure`.

**Report:**
- Annotator A unsure rate: `count(A_label == "unsure") / 50`
- Annotator B unsure rate: `count(B_label == "unsure") / 50`
- Combined unsure rate: `count(A_or_B_unsure) / 50`
- Cases where both marked unsure: `count(A_and_B_unsure) / 50`

**Interpretation:**
- Unsure rate < 10%: Annotators find the taxonomy applicable.
- Unsure rate 10-20%: Some cases are genuinely hard; expected.
- Unsure rate > 20%: Taxonomy or evidence quality is problematic; investigate `confusion_if_any` patterns.

**Also report:** Distribution of `confusion_if_any` values (supported_vs_mild, mild_vs_strong, strong_vs_contradiction, evidence_insufficient_context, other) to identify which boundary is most confusing.

---

## 6. Label Distribution Shift (Silver → Gold)

**Metric:** Compare the silver label distribution to the adjudicated gold label distribution.

**Report:**
- Silver label counts: {supported: N1, mild: N2, strong: N3, contradiction: N4}
- Gold label counts: {supported: M1, mild: M2, strong: M3, contradiction: M4}
- Shift matrix: For each silver label, how many cases survived as the same gold label vs shifted to another label.

**Example shift matrix:**

|  | Gold: supported | Gold: mild | Gold: strong | Gold: contradiction |
|---|---|---|---|---|
| Silver: supported | 7 | 2 | 0 | 0 |
| Silver: mild | 1 | 6 | 3 | 0 |
| Silver: strong | 0 | 5 | 12 | 3 |
| Silver: contradiction | 0 | 0 | 2 | 9 |

**Interpretation:**
- High diagonal: silver labels are mostly confirmed by gold.
- Off-diagonal patterns: silver labels systematically shift to specific gold labels (e.g., silver strong → gold mild), indicating silver label bias.

---

## 7. Strong-Action Retention Rate

**Metric:** Of the cases where silver label = `strong_action_overclaim`, how many survived as `strong_action_overclaim` in gold?

**Formula:** `count(silver == strong AND gold == strong) / count(silver == strong)`

**Report:** Percentage and count.

**Interpretation:**
- ≥ 0.70: Strong-action silver labels are mostly confirmed. The project's main R4/LLM comparison results (which target strong_action) are supported by gold.
- 0.40 – 0.69: Mixed. Some strong-action silver labels shift to mild or contradiction. The project's strong-action results need caveats.
- < 0.40: **Paper claim降级.** If the majority of silver `strong_action_overclaim` cases shift to `mild_scope_overclaim` in gold, the paper's central claim ("R4 targets strong_action_overclaim, which LLM judges miss") is weakened. The paper's main contribution would need to be reframed as "R4 targets evidence-strength over-extension (mild + strong combined)" rather than specifically `strong_action_overclaim`.

---

## 8. Pre-Registered Decision Rules

These decision rules are **pre-registered** before annotation begins. They bind the project's response to the pilot results.

### Rule 1: mild_vs_strong κ < 0.4 → taxonomy MUST be revised

If the per-boundary Cohen's kappa for `mild_vs_strong` is < 0.4, the taxonomy is not reliably operationalizable on this boundary. The project must:
1. Revise the mild/strong distinction (clearer signal words, stricter decision rule, or merge mild + strong into a single "evidence-strength over-extension" class).
2. Re-annotate a new pilot with the revised taxonomy.
3. NOT publish strong-action-specific results (R4 strong-F1, LLM strong-F1) as stable numbers until the revised taxonomy is validated.

### Rule 2: strong_action retention rate < 0.40 → paper claim降级

If the strong-action retention rate is < 0.40 (i.e., the majority of silver `strong_action_overclaim` cases shift to `mild_scope_overclaim` in gold), the paper's central claim must be降级:
- **Current claim:** "R4 targets strong_action_overclaim, which LLM judges systematically miss."
- **Downgraded claim:** "R4 targets evidence-strength over-extension (combining mild_scope_overclaim and strong_action_overclaim), which LLM judges miss. The mild/strong sub-distinction is not reliably operationalizable with current taxonomy."

### Rule 3: If GPT/R4 re-evaluation against gold is needed, wait until adjudication is complete

If the project later wants to re-compute R4 or GPT metrics against the gold pilot labels (instead of silver labels), this MUST happen **after** adjudication is complete and the gold labels are finalized. Do not re-run models mid-pilot.

### Rule 4: ≥ 5/50 `taxonomy_revision_needed` → taxonomy revision required

If the adjudicator marks ≥ 5 cases (10%) as `taxonomy_revision_needed`, the taxonomy must be revised before any further annotation, model training, or paper publication. The 5-case threshold is pre-registered.

---

## 9. What This Pilot Can and Cannot Prove

### Can prove
- Whether two independent annotators can apply the four-class taxonomy with substantial agreement (κ ≥ 0.60).
- Whether the mild_vs_strong boundary is the hardest boundary (expected from audit).
- Whether silver `strong_action_overclaim` labels survive gold adjudication.
- Whether the taxonomy needs revision (per pre-registered rules above).

### Cannot prove
- That the taxonomy is "correct" in an absolute sense — it only proves annotators can apply it consistently.
- That R4 or LLM results generalize to gold — that requires re-evaluation after adjudication (Rule 3).
- That the 50-pilot sample is representative of the full 444-pair dataset — the pilot oversamples boundary cases (25/50 are high-risk boundary cases).
- That the taxonomy will work on other domains — the pilot is limited to the 6 domains in SimClaim.

---

## 10. Output Files After Analysis

After adjudication and analysis, the following files will be produced (in a future task, NOT this freeze):

1. `pilot_50_agreement_results.json` — overall agreement, kappa, per-boundary kappa, unsure rate.
2. `pilot_50_label_shift_matrix.csv` — silver → gold shift matrix.
3. `pilot_50_strong_action_retention.json` — strong-action retention rate.
4. `pilot_50_taxonomy_revision_decision.md` — based on pre-registered rules, whether taxonomy needs revision.
5. `pilot_50_final_gold_labels.csv` — the 50 adjudicated gold labels, ready for re-evaluation if needed.

These files do NOT exist yet. They will be produced after annotation + adjudication is complete.
