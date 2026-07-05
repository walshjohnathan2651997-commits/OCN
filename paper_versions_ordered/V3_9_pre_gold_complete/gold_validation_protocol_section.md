# Gold Validation Protocol — Pre-Registered Success and Downgrade Criteria (V3.9 Frozen)

**Status:** Frozen as of V3.9 Pre-Gold Complete Manuscript (2026-07-04).
**Purpose:** Pre-register the success and downgrade criteria for the planned gold validation described in §VII of the main manuscript. Gold annotation has **not** been performed. No numeric values are populated. All entries in Tables G1-G3 of `gold_validation_placeholder_tables.csv` are marked `TO_BE_FILLED_AFTER_GOLD`.
**Scope:** This protocol governs ONLY the gold validation step. It does not change the silver-stage results in §VI, the frozen R4 thresholds, the decision tree (Figure 2), or any other artifact in V3.9.

## 1. Why This Protocol Is Pre-Registered

The pre-gold finding — R4 targets a relation that LLM judges miss under the tested prompts — is computed against silver labels. If the gold criteria were defined *after* seeing gold results, the paper could selectively report favorable metrics, undermining the falsifiability of the framework. Pre-registration before gold annotation is therefore mandatory. Once gold annotation begins, this protocol cannot be revised; any deviation must be reported explicitly as a protocol violation, not as a quiet re-definition.

## 2. Gold Subset

The gold pilot uses a 50-sample subset drawn from the 444-row SimClaim silver-label pilot set:

- 25 high-risk samples from `high_risk_sample_bank.csv` (concentrated at the mild_vs_strong and strong_vs_contradiction boundaries).
- 16 trusted samples from `trusted_case_bank.csv` (≥4 per class).
- 9 random samples from the remaining silver pool (stratified by class to keep class balance).

Two annotators independently label under the frozen protocol (`annotation_guideline_v1_frozen.md`, `annotation_decision_tree_v1.md`, `boundary_rules_v1.md`). Disagreements are adjudicated by a third annotator (`adjudication_protocol_v1.md`). Silver labels are **hidden** from annotators during labeling (`pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`). The 50-sample size is a pilot — sufficient to estimate per-boundary κ, not sufficient to support confirmatory benchmark claims.

## 3. Frozen Success Criteria

The gold validation is considered **supportive of the pre-gold findings** if ALL of the following hold:

| Criterion | Threshold | Source |
| --- | --- | --- |
| Overall agreement | ≥ 0.70 | Table G1 |
| Cohen's kappa | ≥ 0.45 | Table G1 |
| mild_vs_strong kappa | ≥ 0.40 | Table G1 |
| strong_action retention rate | ≥ 0.60 | Table G2 |
| LLM strong recall remains low | ≤ 0.20 (GPT standard, GPT decision-tree, GPT few-shot, DeepSeek) | Table G3 |
| R4 or hybrid improves strong recall / screening recall | R4 strong recall > LLM strong recall AND hybrid strong recall ≥ R4 alone | Table G3 |
| False positives per true positive is acceptable | R4 ≤ 10 AND hybrid ≤ 10 | Table G3 |

If all success criteria hold, the pre-gold findings are considered **supported by gold**, and the paper proceeds to a confirmatory submission with gold-validated numbers inserted into Tables G1-G3.

## 4. Frozen Downgrade Criteria

The gold validation triggers **downgrade** of one or more paper claims if ANY of the following hold:

### Downgrade Criterion 1 — Taxonomy revision
**Trigger:** mild_vs_strong kappa < 0.40.
**Consequence:** The mild_vs_strong boundary is not reliably drawable. The strong_action_overclaim class may need to be merged with mild_scope_overclaim. The paper is re-framed as a three-class framework (supported / scope_overclaim / contradiction_candidate), and the central contribution is weakened.

### Downgrade Criterion 2 — Paper claim downgraded
**Trigger:** strong_action retention rate < 0.50.
**Consequence:** Most silver-stage strong_action cases convert to mild under gold. The pre-gold finding (R4 > LLM on strong_action) becomes a finding about scope overclaim, not action overclaim. The paper is re-framed accordingly.

### Downgrade Criterion 3 — LLM under-detection claim downgraded
**Trigger:** GPT few-shot prompt OR GPT decision-tree prompt achieves strong_action-F1 ≥ 0.20 on the gold subset.
**Consequence:** A different prompt design closes the strong_action gap. The pre-gold under-detection finding is prompt-specific rather than pattern-specific. The paper is re-framed as "under-detection under specific prompts" rather than "consistent under-detection pattern".

### Downgrade Criterion 4 — Screening claim downgraded
**Trigger:** R4 false positives per true positive > 10 on the gold subset.
**Consequence:** R4 produces too many false positives for the screening use case to be viable. The screening-layer positioning is removed from the paper.

### Downgrade Criterion 5 — Complementarity claim downgraded
**Trigger:** LLM+R4 hybrid does not improve screening recall over R4 alone (hybrid strong recall < R4 strong recall).
**Consequence:** Combining LLM and R4 does not exploit the complementarity. The "R4 as a complement to LLM judges" positioning is weakened to "R4 as an alternative strong_action detector with lower macro-F1".

### Downgrade Criterion 6 — Taxonomy revision required (boundary disagreement)
**Trigger:** ≥ 5/50 cases flagged as `taxonomy_revision_needed` during adjudication (both annotators high-confidence disagreement OR decision tree yields ambiguous routing).
**Consequence:** The taxonomy itself needs structural revision. The paper is paused; the taxonomy is revised; silver labels are re-generated for the revised taxonomy; R4 and LLM comparisons are re-run; V3.9 is replaced by a new version.

## 5. What Does NOT Trigger a Downgrade

The following are NOT downgrade triggers on their own:

- **supported_vs_mild kappa < 0.40.** This is the weakest silver-stage boundary and is reported as informational. The paper already acknowledges that supported/mild is an open problem.
- **strong_vs_contradiction kappa < 0.40.** This boundary was historically confused by the audit heuristic missing detail-swapping; the decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction. A low kappa here would prompt further decision-tree revision but does not invalidate the four-class taxonomy.
- **R4 macro-F1 < LLM macro-F1 on gold.** This is *expected* and is already the pre-gold finding. R4 is positioned as a complement, not a replacement.
- **GPT standard prompt strong recall remains low.** This *supports* the pre-gold finding (H4).
- **Some silver labels shift under gold.** A shift rate up to 30% is consistent with the author sanity audit's 62.5% questionable/unclear rate, because not all questionable/unclear cases will actually shift.

## 6. What Gold Will NOT Be Used For

- **Re-tuning R4 thresholds.** `t_contra`, `t_strong`, `t_svm`, `t_low` are frozen.
- **Re-fitting the decision tree.** Figure 2 and `taxonomy_boundary_decision_tree.md` are frozen.
- **Re-selecting router variants.** R4 is the frozen main method.
- **Modifying the four-class taxonomy.** The taxonomy is frozen pending gold; if gold requires revision, the revision is a separate V4.0 effort, not a quiet modification of V3.9.
- **Re-running the LLM judge comparison.** The frozen LLM predictions (DeepSeek 200, GPT standard 100, GPT structured 100) are re-scored against gold labels; new LLM runs are NOT part of the gold validation. New prompts (decision-tree, few-shot) ARE part of gold validation (Table G3) and are pre-registered as new runs, not as re-tuning of existing ones.
- **Generating new SimClaim data.** Original data is not modified; the 444-row silver set is preserved.

## 7. Reporting Policy

- Gold results will be reported in Tables G1-G3 of the main manuscript. All `TO_BE_FILLED_AFTER_GOLD` entries will be replaced with actual numbers; no other cells will be modified.
- The Limitations section (§IX) will be updated to reflect gold outcomes: "supported by gold" / "downgraded per criterion X" / "inconclusive — pilot too small".
- If a downgrade criterion is triggered, the affected paper claim will be revised explicitly; the original pre-gold claim will be retained in a "Pre-gold claim vs gold outcome" appendix for transparency.
- The completion log (`pre_gold_completion_log.md`) will be extended with a "Gold outcomes" section.
- Gold results are pilot results (N=50); they cannot be claimed as a confirmatory benchmark. A separate confirmatory study (300–500 independently adjudicated pairs) is required for submission to a top-tier venue.

## 8. Pre-Registration Summary

- This protocol (`gold_validation_protocol_section.md`) is frozen as of 2026-07-04 in V3.9 Pre-Gold Complete Manuscript.
- The placeholder tables (`gold_validation_placeholder_tables.csv`) are frozen with `TO_BE_FILLED_AFTER_GOLD` entries.
- The success criteria (§3) and downgrade criteria (§4) are pre-registered.
- Gold annotation has not started.
- Once gold annotation starts, this protocol cannot be revised; deviations must be reported as protocol violations.
