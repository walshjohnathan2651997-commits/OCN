# Related Work Differentiation Table (V3.13 Standalone)

**Date:** 2026-07-05
**Paper version:** V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH
**Source:** §II.A and Table X of `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md`

## Purpose

This file is a standalone extract of Table X and the §II.A positioning paragraphs, for advisor reference and for inclusion in the V3.13 strengthening plan. It is **not** a new experimental result; it is the positioning argument in tabular form.

## Positioning Statement

CESE-OCN is positioned on the **existing scientific overstatement / evidence-force calibration track**, not as a new field. It builds on:

- **RIGOURATE [30]** — scientific overstatement scoring (continuous score per claim-evidence pair, with evidence retrieval from full papers).
- **Evidence-licensed claims [31]** — scientific writing as calibrating assertion rights to available evidence.
- **ForceBench [35]** — contrastive evidence-force calibration stress test (calibrated vs. force-raised claim pairs, monotonic preference signal).
- **CLAIM-BENCH [28]** — scientific claim-evidence extraction and validation across full papers.

CESE-OCN's contribution is **fine-grained relation-type decomposition** (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) and **high-risk action-overclaim screening**, complementary to (not competing with) the above works.

## Table X. Positioning against Closest Related Work

| Work | Primary question | Data type | Output | Handles overclaim severity? | Separates overclaim types? | Targets action/deployment overclaim? | Our relation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| **RIGOURATE [30]** | How overstated is this claim, given retrieved evidence? | Natural author-written claims + retrieved evidence from full papers | Continuous overstatement score | Yes (continuous score) | No (single score, no type decomposition) | No (no separate action-overclaim class) | Complementary: score + relation-type decomposition |
| **ForceBench [35]** | Does the model monotonically prefer calibrated vs. force-raised claims? | Contrastive paired claims (calibrated vs. force-raised) with fixed cited passage | Monotonic preference signal per force dimension | Yes (force dimensions include scope and modality) | Partial (five force dimensions, but not single-instance four-class relation) | No (no separate action-overclaim screening target) | Complementary: contrastive force-sensitivity + single-instance relation typing |
| **CLAIM-BENCH [28]** | Is evidence correctly extracted and does it support the claim? | Natural full-paper claim-evidence pairs | Extraction + validation label (support/refute/NEI-style) | No (not strength-calibration oriented) | No (no overclaim-type taxonomy) | No | Complementary: extraction-validation + strength-calibration typing |
| **CESE-OCN / SimClaim (this work)** | What *type* of evidence-sufficiency mismatch is this, and is it a high-risk action overclaim? | Controlled counterfactual diagnostic set (real evidence spans + generated claim variants) | Four-class relation label + strong_action screening signal | Yes (taxonomy separates severity by relation type) | Yes (four-class relation decomposition) | Yes (strong_action_overclaim is the screening target) | — |

## Per-Work Differentiation Paragraphs

### RIGOURATE [30]

RIGOURATE retrieves supporting evidence from full papers and assigns continuous overstatement scores to scientific claims, aligning each claim with the evidence that supports (or fails to support) it. RIGOURATE is stronger than the present work along several axes: it operates on natural author-written claims at larger data scale, performs evidence retrieval from full papers, and has been validated against human overstatement judgments. We acknowledge this clearly.

**Difference:** RIGOURATE estimates the **degree of overstatement** as a score, while CESE-OCN diagnoses the **type of evidence-sufficiency mismatch** as a four-class relation. In particular, RIGOURATE does not isolate *mild scope expansion* from *high-risk action/deployment overclaim* as separate operational classes; a single overstatement score can conflate a claim that mildly over-extends scope with a claim that asserts deployment readiness, safety, or operational conclusions the evidence does not justify. CESE-OCN's contribution is to make this separation operational via the strong_action_overclaim class and a relation-specific screening route targeting it.

**Complementarity:** A continuous score can be produced by RIGOURATE-style systems, and a relation-type decomposition can be produced by CESE-OCN, on the same claim-evidence pair. The two are complementary.

### ForceBench [35]

ForceBench is a contrastive evidence-force calibration stress test. It fixes the cited passage and compares a *calibrated claim* against a *force-raised claim* across five force dimensions — relation, modality, scope, temporal validity, and numeric specificity — testing whether a model monotonically prefers the calibrated claim over the force-raised claim. ForceBench is stronger than the present work along several axes: it provides a clean contrastive paired-claim protocol, covers five distinct force dimensions, and is cited-RAG oriented with monotonic preference as the evaluation signal. We acknowledge this clearly.

**Difference:** ForceBench tests **monotonic preference between paired claims** (calibrated vs. force-raised), while CESE-OCN performs **single-instance relation typing and screening** for high-risk action-overclaim. ForceBench is cited-RAG oriented; CESE-OCN is scientific claim-evidence calibration / diagnostic screening oriented. ForceBench's contrastive design is powerful for testing whether a model *recognizes force mismatch at all*, but it does not directly output a four-class relation label on a single claim, and it does not isolate the high-risk action/deployment sub-class as a screening target.

**Complementarity:** ForceBench-style contrastive tests can probe whether a model is force-sensitive, while CESE-OCN-style relation typing can output an operational screening label on a single claim. The two are complementary.

### CLAIM-BENCH [28]

CLAIM-BENCH evaluates scientific claim-evidence extraction and validation across full papers, extending scientific claim verification to larger paper-level settings with full-paper evidence links. CLAIM-BENCH is stronger than the present work along several axes: it operates on natural full-paper claim-evidence pairs, evaluates extraction and validation jointly, and provides a larger-scale benchmark. We acknowledge this clearly.

**Difference:** CLAIM-BENCH focuses on **whether evidence supports claims** (extraction + validation), while CESE-OCN focuses on **whether evidence is sufficient for the strength and actionability of claims** (calibration of claim strength to evidence). CLAIM-BENCH does not introduce a strength-mismatch taxonomy that separates mild scope overclaim from high-risk action overclaim; its labels are organized around support/refute/NEI-style extraction validation rather than around the action-overclaim boundary.

**Complementarity:** CLAIM-BENCH-style extraction-validation can determine whether evidence is correctly linked to a claim, while CESE-OCN-style relation typing can diagnose whether the claim's strength is calibrated to that evidence. The two are complementary.

## What This Table Does NOT Claim

- **No empirical head-to-head advantage.** The "Our relation" column specifies *conceptual complementarity*, not an empirically demonstrated advantage. §IX item 9 of the V3.13 paper explicitly states the differentiation is positioning-level. Empirical head-to-head comparison is plan-only (P2 in `V3_13_strengthening_plan_after_related_work_shift.md`; see `rigourate_style_baseline_plan.md`).
- **No claim that RIGOURATE / ForceBench / CLAIM-BENCH cannot be extended** to do relation-type decomposition. The claim is that *as currently published*, they do not isolate the strong_action_overclaim sub-class as a screening target.
- **No claim that SimClaim is a natural-prevalence corpus.** SimClaim is a controlled counterfactual diagnostic set (§V.A); the comparison in the "Data type" column reflects this.

## Cross-References

- §II.A of `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md` (full text of the three differentiation paragraphs and Table X)
- §V.A (SimClaim synthetic/counterfactual transparency statement)
- §VIII.F (why fine-grained relation typing is valuable)
- §IX item 9 (differentiation is positioning-level, not empirical)
- `rigourate_style_baseline_plan.md` (P2 plan to convert conceptual complementarity to empirical)
- `V3_13_strengthening_plan_after_related_work_shift.md` (full P0–P4 roadmap)
