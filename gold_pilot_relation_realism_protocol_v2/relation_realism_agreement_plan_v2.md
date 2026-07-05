# Agreement Metric Plan v2 — Relation + Realism

**Version:** 2.0 (DRAFT)
**Date:** 2026-07-05
**Status:** v2 DRAFT. v1 (`agreement_metric_plan_v1.md`) is FROZEN and untouched. v2 extends v1 with Layer 2 realism agreement metrics.
**Predecessor:** `D:\ocn\gold_pilot_protocol_freeze_v1\agreement_metric_plan_v1.md`

---

## 0. Purpose

This document defines how annotator agreement will be computed for the v2 two-layer gold pilot. v1 covered Layer 1 (relation) agreement only. v2 adds Layer 2 (realism) agreement metrics.

**All metrics are computed AFTER both annotators submit their filled CSVs.** No metrics are computed during annotation.

---

## 1. Data inputs

| File | Source | Description |
| --- | --- | --- |
| `pilot_50_relation_realism_annotation_A_filled.csv` | Annotator A | 50 rows × 15 cols (5 basic + 5 Layer 1 + 5 Layer 2) |
| `pilot_50_relation_realism_annotation_B_filled.csv` | Annotator B | 50 rows × 15 cols |
| `adjudication_results_v2.csv` | Adjudicator | 50 rows × final labels (post-adjudication) |

Rows are matched by `pilot_id` (P001-P050). Both A and B must have the same 50 `pilot_id` values in the same order.

---

## 2. Layer 1: Relation agreement metrics (carried over from v1)

### 2.1 Overall agreement rate

- **Definition:** Fraction of rows where A's `annotator_relation_label` == B's `annotator_relation_label`.
- **Computation:** `mean(A.label == B.label)` over 50 rows.
- **Excludes:** Rows where either annotator marked `unsure` are reported separately (sensitivity analysis).
- **Target:** >= 0.70.

### 2.2 Cohen's kappa (4-class, excluding `unsure`)

- **Definition:** Cohen's κ for the 4-class label set {supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate}.
- **Computation:** Standard Cohen's κ formula. Rows where either annotator marked `unsure` are excluded from the primary κ, reported separately.
- **Target:** κ >= 0.60 (substantial agreement). κ < 0.40 triggers taxonomy revision (pre-registered).

### 2.3 Per-label agreement

- **Definition:** For each of the 4 labels, the agreement rate on rows where at least one annotator used that label.
- **Computation:** Per-label confusion matrix.
- **Reported as:** 4×4 confusion matrix + per-label precision/recall (treating A as reference, B as prediction, and vice versa).

### 2.4 Per-boundary kappa

- **Definition:** Cohen's κ on row subsets that involve specific boundaries.
- **Boundaries:**
  - `supported_vs_mild`: rows where at least one annotator chose supported or mild.
  - `mild_vs_strong`: rows where at least one annotator chose mild or strong. **(HARDEST boundary; pre-registered trigger.)**
  - `strong_vs_contradiction`: rows where at least one annotator chose strong or contradiction.
- **Pre-registered rule:** If `mild_vs_strong` κ < 0.40 → taxonomy revision required.

### 2.5 Unsure rate

- **Definition:** Fraction of rows where each annotator marked `unsure`.
- **Computation:** Per-annotator `unsure` rate.
- **Target:** < 20%. < 10% is ideal.

### 2.6 Label distribution shift (silver → gold)

- **Definition:** Comparison of silver label distribution (in the original `gold_pilot_candidate_50.csv`, accessible to adjudicator only post-adjudication) vs gold label distribution (post-adjudication).
- **Computation:** 4-class distribution shift, chi-square test.
- **Reported as:** 4-class distribution table + chi-square p-value.

### 2.7 Strong-action retention rate

- **Definition:** Of the silver-labeled `strong_action_overclaim` rows, fraction retained as `strong_action_overclaim` in gold (post-adjudication).
- **Computation:** `n(strong_silver AND strong_gold) / n(strong_silver)`.
- **Pre-registered rule:** If retention < 0.40 → paper claim downgrade.

---

## 3. Layer 2: Realism agreement metrics (NEW in v2)

### 3.1 Realism score distribution

- **Definition:** Distribution of `claim_realism_score_1_to_5` for each annotator.
- **Computation:** Histogram (1-5) per annotator.
- **Reported as:** Table + bar chart.

### 3.2 Realism score mean and median

- **Definition:** Mean and median `claim_realism_score_1_to_5` per annotator, and pooled.
- **Computation:** Standard mean/median.
- **Reported as:** Per-annotator + pooled.

### 3.3 Realism inter-annotator agreement (continuous)

- **Definition:** Agreement on the 1-5 realism score between A and B.
- **Computation:**
  - **Pearson correlation** between A's score and B's score (over 50 rows).
  - **Spearman rank correlation** (rank-based, more robust to non-linear mappings).
  - **Mean absolute difference** (MAD): mean(|A_score - B_score|).
  - **Exact agreement rate**: fraction where A_score == B_score.
  - **Within-1 agreement rate**: fraction where |A_score - B_score| <= 1.
- **Target:** Pearson r >= 0.60, within-1 agreement >= 0.80.
- **Pre-registered rule:** If Pearson r < 0.40 → realism annotation is unreliable; retraining required.

### 3.4 Realism issue agreement (categorical)

- **Definition:** Agreement on `claim_realism_issue` (9 categories: none, too_template_like, too_extreme, unnatural_wording, not_scientific_claim, contradiction_too_mechanical, strong_action_too_forced, mild_strong_boundary_unclear, ambiguous_or_vague).
- **Computation:**
  - **Overall agreement rate**: fraction where A.issue == B.issue.
  - **Cohen's κ** for the 9-class issue set.
  - **Per-issue confusion matrix**.
- **Target:** Overall agreement >= 0.50, κ >= 0.40.
- **Note:** Issue annotation is harder than score annotation; we expect lower agreement. The realism score (continuous) is the primary realism metric; issue type is secondary.

### 3.5 `claim_usable_for_paper_example` agreement

- **Definition:** Agreement on the yes/no `claim_usable_for_paper_example` field.
- **Computation:**
  - **Overall agreement rate**.
  - **Cohen's κ** (binary).
- **Target:** Agreement >= 0.70, κ >= 0.50.

### 3.6 Realism by relation label (cross-layer analysis)

- **Definition:** For each relation label (post-adjudication), distribution of realism scores.
- **Computation:** Group by `final_relation_label`, compute realism score mean/median/distribution.
- **Reported as:** Table: relation_label × realism_score distribution.
- **Hypothesis:** `strong_action_overclaim` claims may have lower realism (more likely to be forced) than `supported` claims. `contradiction_candidate` claims may have lower realism (more likely to be mechanical). This is exploratory.

### 3.7 High-risk realism issue distribution

- **Definition:** Distribution of `claim_realism_issue` values, post-adjudication.
- **Computation:** Count and rate of each issue type.
- **Reported as:** Table.
- **Pre-registered rule:**
  - **Class-level:** If for any relation label, the rate of `claim_realism_score <= 2` > 25% → paper claim downgrade (class-level).
  - **Paper-level:** If across all 50 pilot claims, the rate of `claim_realism_score <= 2` > 25% → major paper downgrade (paper-level).

### 3.8 Realism score by domain

- **Definition:** Realism score distribution per domain.
- **Computation:** Group by `domain`, compute realism mean/median.
- **Reported as:** Table: domain × realism_score distribution.
- **Hypothesis:** Some domains may have more realistic claims than others. Exploratory.

---

## 4. Cross-layer: Relation × Realism cross table

- **Definition:** 2D contingency table of `final_relation_label` (rows) × `final_realism_score` (columns, binned as 1-2 / 3 / 4-5).
- **Computation:** Cell counts and row percentages.
- **Reported as:** Table.
- **Interpretation:**
  - If high-realism (4-5) claims are evenly distributed across relation labels → realism is independent of relation correctness (good).
  - If `strong_action_overclaim` claims cluster in low-realism (1-2) → the strong_action claims are unrealistic, weakening the diagnostic set.
  - If `contradiction_candidate` claims cluster in low-realism → contradictions are mechanical, weakening the diagnostic set.

---

## 5. Adjudication metrics (post-adjudication)

### 5.1 Adjudication rate (Layer 1)

- **Definition:** Fraction of rows adjudicated for Layer 1 (where A and B disagreed, OR where either set `needs_relation_adjudication = yes`).
- **Computation:** Count / 50.

### 5.2 Adjudication rate (Layer 2)

- **Definition:** Fraction of rows adjudicated for Layer 2 (where |A.realism_score - B.realism_score| >= 2, OR where A.issue != B.issue, OR where either set `needs_realism_adjudication = yes`).
- **Computation:** Count / 50.

### 5.3 Adjudicator silver-peeking rate

- **Definition:** Fraction of adjudicated rows where the adjudicator consulted silver labels (should be 0 by default; only allowed if adjudicator explicitly notes a special case).
- **Computation:** Count / 50.
- **Target:** 0 (silver labels hidden from adjudicator by default).

---

## 6. Pre-registered decision rules (summary)

After all metrics are computed, apply these pre-registered rules:

| # | Rule | Trigger | Action |
| --- | --- | --- | --- |
| 1 | Taxonomy revision | `mild_vs_strong` κ < 0.40 | Taxonomy MUST be revised; re-pilot. |
| 2 | Strong-action downgrade | strong-action retention < 0.40 | Paper claim downgrade. |
| 3 | Taxonomy revision (rate-based) | >= 5/50 rows with `taxonomy_revision_needed` | Taxonomy revision required. |
| 4 | Class-level realism downgrade | Any relation label with `realism_score <= 2` rate > 25% | Paper claim downgrade (class-level). |
| 5 | Paper-level realism downgrade | All-claims `realism_score <= 2` rate > 25% | Major paper downgrade. |
| 6 | Realism annotation unreliable | Layer 2 Pearson r < 0.40 | Retraining required; realism results exploratory only. |
| 7 | Proceed to full gold | κ >= 0.60, retention >= 0.40, class-level realism <= 25%, paper-level realism <= 25%, < 5 revision-needed | Proceed to full 444-pair gold annotation. |

---

## 7. Reporting

After adjudication and metric computation, produce:

- `agreement_results_v2.json` — all metrics above as a JSON.
- `label_shift_matrix_v2.csv` — silver → gold label shift.
- `realism_distribution_v2.csv` — realism score × relation label cross table.
- `strong_action_retention_v2.json` — retention rate + per-claim retention flags.
- `taxonomy_revision_decision_v2.md` — decision based on pre-registered rules.
- `paper_claim_decision_v2.md` — paper claim upgrade/hold/downgrade decision.

**All metrics are reported with N=50 caveat.** The pilot is small; confidence intervals are wide. Decisions to revise taxonomy or downgrade paper claims should consider both the metric value and the qualitative review of disagreements.
