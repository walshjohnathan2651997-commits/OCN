# V3.15 Revision Log — Hierarchical Taxonomy Revision

**Date:** 2026-07-05
**Source:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Output directory:** `D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision\`

## Summary

V3.15 reframes the paper's interpretive framing from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy** (Level 1: supported / overclaim / contradiction; Level 2: scope_expansion / strong_action under overclaim). The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space; only the interpretation changes.

## Changes Applied

Total targeted string replacements: 18

### 1. Header / Changes Log
- Updated version header to V3.15 Hierarchical Taxonomy Revision.
- Added V3.15 changes entry at top of changes block.

### 2. Abstract
- Replaced "we define a four-class taxonomy" with hierarchical framing.
- Added standard wording: "We do not assume that mild_scope_overclaim is a naturally discrete category. Instead, it is used as a diagnostic buffer subtype..."
- Reframed R4 description as "relation-specific screening router under the hierarchical taxonomy".

### 3. Introduction (§I)
- Reframed contribution 1 as "Hierarchical diagnostic taxonomy" (Level 1 + Level 2).
- Reframed contribution 2 as "Controlled counterfactual diagnostic set + LLM under-detection finding".
- Reframed contribution 3 as "Screening method (R4) targeting the Level-2 high-risk strong_action subtype".
- mild_scope_overclaim explicitly described as boundary-sensitive buffer subtype, not naturally stable.

### 4. Task Formulation (§III.A)
- Added Table 0a (hierarchical label mapping) with 5 rows.
- Added hierarchical interpretation paragraph after the four-class bullet list.
- §III.C title changed to "Why strong_action_overclaim Is the Level-2 High-Risk Subtype".

### 5. Method (§IV.A)
- Reframed R4 as "relation-specific screening router under the hierarchical taxonomy".
- Mapped three routes onto hierarchical levels (Level-1 contradiction gate, Level-2 scope residual, Level-2 strong_action route).
- Explicitly stated "R4 is not a flat 4-class best classifier".

### 6. Results (§VI)
- §VI.A title: "Internal Silver Diagnostic Results (Table 1) — Flat Operational-Label Evaluation".
- §VI.B title: "LLM Judge Comparison (Table 2, Figure 3) — Level-2 High-Risk Strong_Action Screening".
- Added note: "macro-F1 over operational labels is diagnostic, not the primary deployment metric".
- Added screening utility reinforcement: "In real-world deployment, strong_action is a rare high-risk subtype; therefore recall, FP/TP ratio, and review burden are more important than overall accuracy."

### 7. Discussion (§VIII.G — NEW)
- Added new subsection "Why the Taxonomy Is Hierarchical Rather Than Flat".
- Explains Level 1 / Level 2 structure.
- Explains why mild_scope is buffer, strong_action is high-risk subtype.
- Includes fallback logic (Level-1 κ, Level-2 κ, strong_action retention thresholds).

### 8. Gold Protocol (§VII.K — NEW)
- Added new subsection "Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)".
- References `hierarchical_gold_validation_plan.md`.
- Specifies three validation requirements: Level-1 κ, Level-2 κ, claim realism.
- Specifies three fallback rules: Level-1 OK + Level-2 fail → 3-class + binary screen; retention ≥ 0.60 → retain; retention < 0.50 → exploratory.

### 9. Conclusion (§X)
- Reframed taxonomy contribution as hierarchical.
- Added: "mild_scope_overclaim is a boundary-sensitive buffer subtype, not a naturally stable discrete class; strong_action_overclaim is the high-risk Level-2 subtype targeted by R4 screening."

## Preserved Byte-Identical (Verified)

All experimental numbers preserved byte-identical from V3.14:
- R4 strong-F1 = 0.3967 (silver 444)
- R4 strong-F1 = 0.3000 (matched 100)
- LLM strong-F1 = 0.0769 (matched 100)
- R4 macro-F1 = 0.3280 (matched 100)
- LLM macro-F1 = 0.5523 (matched 100)
- Baseline strong-F1 = 0.2408
- Absolute gap = +0.2231
- R4 strong recall = 0.4562 (silver 444), 0.36 (matched 100)
- Baseline strong recall = 0.2062
- R4 macro-F1 = 0.4238 (silver 444)
- Bootstrap CI = [0.1058, 0.1988]
- FP/TP = 2.89, review burden = 35%

## Prohibitions Enforced

- No experiments run.
- No API calls.
- No gold annotation.
- No original data modification.
- No experimental number changes.
- No deletion of the four operational labels.
- No silver written as gold.
- No claim that mild_scope is naturally stable.
- No claim that R4 overall beats LLM.
- No modification to V3.14 or any prior version source files.

## Files Generated

1. `CESE_OCN_V3_15_hierarchical_taxonomy_revision.md` — main paper
2. `CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx` — DOCX version
3. `hierarchical_label_mapping.csv` — 4-row mapping table
4. `hierarchical_gold_validation_plan.md` — Level-1/Level-2 + fallback plan
5. `V3_15_revision_log.md` — this file
6. `V3_15_hierarchical_taxonomy_gate.json` — gate JSON
