# V3.9 Pre-Gold Complete Manuscript — Completion Log

**Date:** 2026-07-04
**Author:** Automated pass per V3.9 task spec
**Input:** `D:\ocn\paper_versions_ordered\V3_8_reference_refreshed\CESE_OCN_V3_8_reference_refreshed.md`
**Output directory:** `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\`

## 1. Goal

Convert V3.8 (reference refreshed) into a pre-gold complete manuscript: a complete draft in which all structure is in place except the gold validation numbers, which are left as `TO_BE_FILLED_AFTER_GOLD` placeholders. No gold annotation is performed; no models are run; no APIs are called; no original data is modified; V3.8 is not deleted.

## 2. Files Created

| File | Purpose | Status |
| --- | --- | --- |
| `CESE_OCN_V3_9_pre_gold_complete.md` | Main manuscript, pre-gold complete | Created |
| `CESE_OCN_V3_9_pre_gold_complete.docx` | DOCX build of the main manuscript | Created via zipfile+XML |
| `gold_validation_placeholder_tables.csv` | Three placeholder tables (G1, G2, G3) with TO_BE_FILLED_AFTER_GOLD | Created |
| `gold_validation_protocol_section.md` | Frozen pre-registered success and downgrade criteria | Created |
| `pre_gold_completion_log.md` | This log | Created |
| `advisor_note_v3_9.md` | Note to advisor explaining the pre-gold complete draft | Created |

## 3. Changes From V3.8 To V3.9

### 3.1 Header And Version Label
- V3.8: "Version: V3.8 (reference refreshed)"
- V3.9: "Version: V3.9 Pre-Gold Complete Manuscript / Status: complete draft except planned gold validation results / Not submission-ready until gold validation is completed."
- Added a "Changes from V3.8" paragraph at the top documenting that this is a structure-only pass.

### 3.2 New Section VII — Planned Gold Validation
- Inserted between §VI Results and the (renumbered) §VIII Discussion.
- Contains eight subsections:
  - A. Why Gold Is Needed
  - B. Gold Is for Validation, Not for Tuning
  - C. Silver-Stage Evidence Is Frozen
  - D. What Gold Will Test (six pre-registered hypotheses H1-H6)
  - E. What Gold Will Report (Tables G1, G2, G3)
  - F. Gold Subset (50-sample description)
  - G. Pre-Registered Downgrade Criteria (six downgrade triggers)
  - H. Closing Claim ("The current silver-stage evidence motivates gold validation rather than replacing it.")
- References the placeholder tables in `gold_validation_placeholder_tables.csv`.
- References the frozen criteria in `gold_validation_protocol_section.md`.

### 3.3 Section Renumbering
| V3.8 | V3.9 |
| --- | --- |
| VII. Discussion | VIII. Discussion |
| VIII. Limitations | IX. Limitations |
| IX. Conclusion | X. Conclusion |

Internal cross-references updated: §VII.D → §VIII.D, §VIII → §IX, §IX → §X, §VI.C → §VI.B (LLM under-detection finding reference).

### 3.4 Wording Adjustments Throughout

The following wording changes are applied throughout the manuscript to make sure current conclusions are described as **silver-stage evidence**, **pre-gold findings**, and **pilot diagnostic results**:

| V3.8 phrase | V3.9 phrase | Rationale |
| --- | --- | --- |
| "exploratory pilot validation" (Results framing) | "pre-gold pilot diagnostic findings" | "exploratory" is acceptable but "pre-gold" is more specific |
| "diagnostic evidence against silver labels, pending independent gold adjudication" | "pre-gold diagnostic evidence against silver labels, pending independent gold adjudication" | Reinforce pre-gold framing |
| "established property of LLM judges" | "established property of LLM judges (pending gold)" or "pre-gold pattern" | Avoid claiming establishment |
| "Independent gold validation is required before this pattern can be treated as established." | "Independent gold validation (§VII) is required before this pre-gold pattern can be treated as established." | Cross-reference the new section |
| "exploratory pilot validation" (in §V.E) | "pre-gold pilot diagnostic study" | Strengthen pre-gold framing |
| "the LLM blind spot finding" / "LLM under-detection finding" | "the LLM under-detection finding (pre-gold)" | Avoid "blind spot" language; reinforce pre-gold |
| "validated annotation scheme" | "validated annotation scheme" with explicit "(no gold labels exist)" | Keep the original caution |
| Final Discussion sentence "Until gold adjudication, decision-tree validation, prompt robustness sweeps, and open-source LLM replications are completed" | Same, with "(§VII)" cross-reference added | Cross-link to new section |

### 3.5 New Limitation Point
Added as Limitation point 7 in §IX:
> "This manuscript is intentionally written as a pre-gold complete draft. The gold validation section (§VII) is specified but not yet populated; all gold-related entries are marked `TO_BE_FILLED_AFTER_GOLD`. Final submission claims should be revised after gold results are available. If gold does not support the current taxonomy, the paper will be downgraded per the pre-registered criteria in §VII.G rather than re-tuned against gold."

### 3.6 Closing Sentence
The Conclusion (§X) and Limitations (§IX) both end with:
> "The current silver-stage evidence motivates gold validation rather than replacing it."

### 3.7 Language Guardrails Updated
Appendix B's "Forbidden claims" list now explicitly includes:
- "Established LLM blind spot." → use "pre-gold under-detection pattern under the tested prompts"
- "Validated taxonomy." → use "frozen taxonomy pending gold validation"
- "Final proof." → use "pre-gold finding"
- "Gold benchmark." → use "silver-stage pilot diagnostic"
- "Submission-ready." → explicitly note this is a pre-gold complete draft

The "Safe claims" list now includes:
- "The current silver-stage evidence motivates gold validation rather than replacing it."

### 3.8 Abstract Updated
The Abstract closes with a new sentence:
> "All results are pre-gold findings on silver labels; the LLM comparison is prompt/model/sample-specific. A planned gold validation is specified in §VII but not yet populated; final submission claims will be revised after gold results are available."

### 3.9 Numeric Results — Preserved Unchanged
All numeric results from V3.8 are preserved verbatim in V3.9 because they are explicitly labeled as silver-stage and pre-gold:
- R4 strong-F1 = 0.3967 (silver-label pilot)
- LLM strong-F1 = 0.0769 (matched 100/200 samples)
- R4 macro-F1 = 0.3280 / GPT-5.5 = 0.5523 / DeepSeek-V3 = 0.5270
- Author sanity audit 25/40 (62.5%) questionable/unclear
- External SciFact/VitaminC results
No numeric value was invented, modified, or fabricated.

## 4. Placeholder Tables (gold_validation_placeholder_tables.csv)

Three tables are created with `TO_BE_FILLED_AFTER_GOLD` placeholders:

- **Table G1 — Annotation agreement** (7 rows): overall agreement, Cohen's kappa, Krippendorff's alpha (optional), mild_vs_strong kappa, strong_vs_contradiction kappa, supported_vs_mild kappa, unsure rate.
- **Table G2 — Silver-gold consistency** (5 rows): silver-gold agreement, strong_action retention rate, mild-to-strong shift, strong-to-mild shift, contradiction retention rate.
- **Table G3 — Gold-subset model evaluation** (8 methods × 7 metrics = 56 rows): Flat baseline, NLI baseline, GPT standard, GPT decision-tree prompt, GPT few-shot prompt, DeepSeek, R4, LLM+R4 hybrid. Metrics: macro_f1, strong_precision, strong_recall, strong_f1, contra_f1, false_positives_per_true_positive, status.

Total: 68 placeholder rows. Zero numeric values pre-filled.

## 5. Frozen Success And Downgrade Criteria (gold_validation_protocol_section.md)

### Success criteria (all must hold)
- Overall agreement ≥ 0.70
- Cohen's kappa ≥ 0.45
- mild_vs_strong kappa ≥ 0.40
- strong_action retention ≥ 0.60
- LLM strong recall ≤ 0.20 (across GPT standard, GPT decision-tree, GPT few-shot, DeepSeek)
- R4 strong recall > LLM strong recall AND hybrid strong recall ≥ R4 alone
- R4 false positives per true positive ≤ 10 AND hybrid ≤ 10

### Downgrade criteria (any one triggers downgrade)
1. mild_vs_strong kappa < 0.40 → taxonomy must be revised
2. strong_action retention < 0.50 → paper claim downgraded
3. GPT few-shot or decision-tree prompt strong_F1 ≥ 0.20 → LLM under-detection claim downgraded
4. R4 false positives per true positive > 10 → screening claim downgraded
5. LLM+R4 hybrid gives no screening gain → complementarity claim downgraded
6. ≥ 5/50 cases flagged `taxonomy_revision_needed` → taxonomy revision required

## 6. Prohibitions Honored

- No gold annotation performed.
- No gold_label or final_label values written.
- No models run.
- No API calls.
- No training.
- No silver-as-gold claims.
- No "submission-ready" claim.
- No deletion of V3.8 (V3.8 directory and files preserved at `D:\ocn\paper_versions_ordered\V3_8_reference_refreshed\`).
- No modification of original data.

## 7. Verification

- V3.9 main manuscript contains Section VII "Planned Gold Validation" with eight subsections.
- Section numbering updated (Discussion → VIII, Limitations → IX, Conclusion → X).
- Three gold placeholder tables referenced in §VII.E.
- Closing sentence "The current silver-stage evidence motivates gold validation rather than replacing it." appears in §VII.H, §IX (final), and §X (final).
- Limitations point 7 ("This manuscript is intentionally written as a pre-gold complete draft...") present in §IX.
- All gold-related CSV entries are `TO_BE_FILLED_AFTER_GOLD`.
- V3.8 directory and files unchanged.
- All numeric results from V3.8 preserved verbatim.

## 8. Next Step

Await advisor review of the pre-gold complete draft. If the advisor approves the structure, proceed with the gold pilot per `gold_pilot_protocol_freeze_v1` and `gold_validation_protocol_section.md`. If the advisor does not approve, revise the taxonomy or positioning first — do not perform gold annotation on a structure that may still change.
