# V3.10 Revision Log

**Source:** V3.9 Pre-Gold Complete Manuscript
**Target:** V3.10 Advisor-Ready Silver-Stage
**Date:** 2026-07-04
**Revision type:** Wording, framing, qualifier, and risk-control pass only.
**No new experiments, no API calls, no model runs, no gold annotation, no data changes, no numeric result changes.**

---

## Summary

V3.10 is a minor revision of V3.9 produced in response to the V3.9 Pre-Advisor Critical Audit Pack (`V3_9_pre_gold_complete_audit/`). The audit verdict was **B** (minor revision before advisor): two fatal framing issues and six major issues, all fixable through wording without new experiments. V3.10 applies all ten required revisions. V3.9 is preserved unchanged.

---

## Revision 1 — Title page weakness exposure reduced

**V3.9 (lines 3-5):**
```
**Version:** V3.9 Pre-Gold Complete Manuscript
**Status:** complete draft except planned gold validation results
**Not submission-ready until gold validation is completed.**
```

**V3.10 (lines 3-6):**
```
**Version:** V3.10 Silver-stage pilot manuscript with a pre-registered gold validation protocol
**Date:** 2026-07-04

**Status note:** Gold validation is planned and pre-registered (§VII) but not yet completed. All numeric results in §VI are silver-stage pilot results computed against AI-preannotated, author-screened labels. The gold validation slots (Tables G1–G3) are designed so that gold results can be inserted without restructuring the paper.
```

**Rationale:** The V3.9 title page led with "Not submission-ready", which reads as apologetic and foregrounds weakness before the advisor sees any content. V3.10 leads with what the paper *is* (a silver-stage pilot manuscript with a pre-registered protocol) and moves the "not yet completed" note into a status note that also explains the structural readiness for gold insertion.

---

## Revision 2 — §VI Results opener conditional framing

**V3.9:** §VI opened directly with numeric results, no conditional frame.

**V3.10 (§VI opener, line 255):**
> **All numerical results in this section are silver-stage pilot results computed against AI-preannotated, author-screened silver labels. If the planned gold adjudication in §VII supports the silver labels, these patterns will be treated as validated pilot findings; otherwise, the affected claims will be downgraded according to the pre-registered criteria in §VII.G.** These are pre-gold findings; they are not gold benchmark numbers. The planned gold validation in §VII specifies how these numbers will be re-evaluated once gold labels are available.

**Rationale:** A harsh reviewer reading V3.9 §VI could mistake silver numbers for gold-validated findings. V3.10 puts the conditional frame at the top of §VI so every subsequent number is read as silver-stage and contingent on §VII.

---

## Revision 3 — "On silver labels" qualifiers on key §VI numbers

**Affected numeric claims (all in §VI):**
- R4 strong-F1 0.3967 (improvement from 0.2408)
- LLM strong-F1 0.0769 (DeepSeek-V3, 200 matched samples)
- R4 vs LLM strong_action gap (+0.2231 on 100 matched samples)
- GPT-5.5 standard / structured strong recall (0.04 = 1/25)
- R4 macro-F1 lower than LLM (0.3280 vs 0.5523)
- Bootstrap CI [0.1058, 0.1988], 10/10 seeds positive

**V3.9:** Numbers stated without silver qualifier in the immediate sentence.

**V3.10:** Each numeric claim now carries an explicit "on silver labels" / "in the silver-stage evaluation" qualifier in the same sentence or the immediately preceding sentence. Examples:
- "On silver labels, R4 improves strong_action positive-F1 from 0.2408 to 0.3967..."
- "On 200 matched silver-label samples, DeepSeek-V3 reaches macro-F1 0.5270 but strong_action-F1 only 0.0769..."
- "On silver labels, the bootstrap CI is [0.1058, 0.1988]..."

**Rationale:** Ensures no reader can quote a number from §VI and accidentally present it as a gold result.

---

## Revision 4 — "pre-gold" reduced from ~19 to 4 occurrences

**V3.9:** The phrase "pre-gold" appeared ~19 times throughout the manuscript, creating a repetitive apologetic tone.

**V3.10:** Reduced to exactly 4 occurrences, in the four allowed locations:
1. **Abstract** (line 14) — "A pre-gold validation protocol is pre-registered in §VII but not yet populated."
2. **§VI opener** (line 255) — "These are pre-gold findings; they are not gold benchmark numbers."
3. **§VII opener** (line 378) — "This section is the pre-gold validation plan; the results will be filled in after the 50-sample gold pilot is completed."
4. **§X Conclusion** (line 501) — "The result is promising but **pre-gold**."

**Other locations** replaced with: "silver-stage", "pilot-stage", "planned gold validation", "validation-pending".

---

## Revision 5 — Contributions rewritten as pilot contributions

**V3.9 §I contributions (lines 28-36):** Written as established findings ("It frames...", "It constructs...", "It introduces...", "It reports...").

**V3.10 §I contributions (lines 30-36):** Rewritten as pilot contributions:
- (i) "We propose a **pilot taxonomy** for scientific claim calibration..."
- (ii) "We construct a **silver-stage SimClaim diagnostic set**..."
- (iii) "We evaluate whether LLM judges under-detect strong_action_overclaim under tested prompts..."
- (iv) "We pre-register a gold validation protocol..."

**Rationale:** V3.9 contributions read as final findings. V3.10 contributions read as pilot-stage proposals with a pre-registered validation plan, which is what the work actually is.

---

## Revision 6 — R4 screening rationale with FP/TP estimate

**V3.9 §VIII.A:** Did not explain why R4 is useful despite lower macro-F1. A reviewer could attack: "R4 macro-F1 0.3280 is much worse than LLM 0.5523 — why is this a contribution?"

**V3.10 §VIII.A (line 449):**
> **R4 is not intended to maximize overall macro-F1. Its role is to screen for strong_action_overclaim candidates missed by LLM judges.** On silver labels, R4 produces approximately 122 false positives (98 supported → strong + 24 mild → strong) against about 25 true strong_action cases in the silver-stage matched analysis, yielding an estimated FP/TP ratio around 4.9. **This is not acceptable as a final automatic labeler, but may be acceptable as a high-recall screening layer for human or LLM-assisted review.** Whether the macro-F1 gap is an acceptable trade-off depends on the downstream use case... The screening viability will be re-evaluated under gold in Table G3 (FP/TP ratio against gold labels, pre-registered threshold ≤ 10 in §VII.G).

**Rationale:** Converts a latent reviewer attack ("R4 is worse overall") into an explicit, bounded screening-positioning claim with a quantified FP/TP ratio from existing audit data.

---

## Revision 7 — strong_action separability stated as hypothesis

**V3.9 §III.C:** Did not explicitly state that the four-class taxonomy's separability is a hypothesis.

**V3.10 §III.C (within contribution (i), line 30):**
> The separability of strong_action_overclaim as a reliably drawable class is a hypothesis to be tested by the planned gold validation (§VII), not an assumption taken as already proven.

**Rationale:** A reviewer could attack the taxonomy as an unvalidated artifact. V3.10 explicitly marks the separability as a hypothesis tested by §VII, removing the assumption.

---

## Revision 8 — External dataset section reframed as transferability probe

**V3.9 §VI.D:** Titled "External Public Dataset Sanity Check" — could be read as claiming external validation of the SimClaim taxonomy.

**V3.10 §VI.D (line 350):** Retitled **"External Transferability Probe"**.

Body text now states:
- Public datasets (SciFact, VitaminC) can only test support/refute, not the four-class evidence-sufficiency taxonomy.
- The probe is a sanity check that R4-compatible methods run on public data, not a validation of the SimClaim taxonomy.
- Public data cannot test evidence sufficiency calibration because they lack action-overclaim labels.

**Rationale:** Prevents a reviewer from attacking "external validation doesn't test your taxonomy" — V3.10 concedes this explicitly and reframes the section as a transferability probe.

---

## Revision 9 — Advisor cover note (separate file)

**File:** `advisor_cover_note_cn.md` (Chinese, stable tone, 5-part structure per spec).

**Structure:**
1. This is a silver-stage complete draft.
2. The mainline is finalized.
3. The advisor is not being asked to judge whether experiments are final — only whether the taxonomy + positioning is worth entering gold pilot.
4. If the advisor approves the structure, proceed with the 50-sample blind gold pilot per the frozen protocol.
5. If the advisor thinks the taxonomy is unsuitable, revise structure first, then gold.

---

## Revision 10 — Mojibake and format cleanup

**V3.9:** Some characters could render as mojibake (garbled section sign, garbled paragraph mark, garbled kappa, garbled ≥, garbled dash variants) if encoding was inconsistent.

**V3.10:** All special characters verified as proper UTF-8:
- § (section sign) — used throughout, e.g., §VI, §VII, §VIII.A
- ≥ (greater-than-or-equal) — used in thresholds and criteria
- κ (kappa) — used in inter-annotator agreement context
- — (em dash) — used in parenthetical asides
- " " (curly quotes) — used in quoted phrases
- → (right arrow) — used in routing descriptions

**Verification:** Grep for the known mojibake byte patterns (garbled section sign, garbled paragraph, garbled kappa, garbled geq, garbled dash variants, UTF-8 BOM artifacts) returns zero matches in V3.10 md.

---

## Items NOT changed (preserved from V3.9)

- All numeric results: R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 values, bootstrap CI, ablation numbers, seed counts.
- All frozen thresholds: t_contra=0.48, t_strong=0.535, t_svm=0.51.
- All experiment file references and traceability.
- The §VII gold validation protocol structure and pre-registered criteria.
- The placeholder Tables G1-G3 (still marked `TO_BE_FILLED_AFTER_GOLD`).
- The author sanity audit numbers (25/40 questionable, 62.5%).
- The dataset description (444 pairs, 111 evidence groups, 6 domains).
- V3.9 source files (read-only, not modified).

---

## Verification

- **V3.9 modified?** No. V3.9 source file `CESE_OCN_V3_9_pre_gold_complete.md` LastWriteTime unchanged.
- **New experiments run?** No.
- **API calls made?** No.
- **Gold annotation performed?** No.
- **Numeric results changed?** No.
- **Mojibake present?** No (verified by grep).
- **"pre-gold" count?** Exactly 4 (Abstract, §VI opener, §VII opener, §X Conclusion).
- **All 10 revisions applied?** Yes.
