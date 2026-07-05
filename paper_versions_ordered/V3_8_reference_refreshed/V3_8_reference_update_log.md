# V3.8 Reference Refresh Log

**Date:** 2026-07-04  
**Base version:** `V3_7_advisor_handoff_clean`  
**Output version:** `V3_8_reference_refreshed`

## Purpose

This pass updates the reference framing so the manuscript no longer looks anchored only in older FEVER/SNLI/SciFact-era claim verification. The scientific argument remains unchanged: CESE-OCN is an evidence-sufficiency calibration framework, and R4 is a relation-specific complement for strong_action_overclaim rather than a general-purpose replacement for LLM judges.

## What changed

1. Added recent scientific claim verification / claim-evidence reasoning references:
   - [27] SciClaimHunt, 2025.
   - [28] CLAIM-BENCH / Can AI Validate Science?, 2025.
   - [29] DeepSciVerify, 2026.

2. Added recent scientific overstatement / evidence-sufficiency-adjacent references:
   - [30] RIGOURATE, 2026.
   - [31] The Calibration Turn in AI-Assisted Research, 2026.

3. Added recent LLM-as-judge limitation references:
   - [32] A Survey on LLM-as-a-Judge, 2024.
   - [33] JUDGE-BENCH / LLMs instead of Human Judges?, ACL 2025.
   - [34] No Free Labels, 2025.

## Citation positions added

- **Introduction paragraph 1:** Added [27], [28] after SciFact to show recent scientific claim verification / claim-evidence reasoning work.
- **Introduction paragraph 2:** Added [30], [31] to support evidence sufficiency / claim strength / overstatement framing.
- **Introduction paragraph 3:** Added [32]–[34] to support the caution that LLM judges require task-specific and human-grounded validation.
- **Related Work:** Expanded from one compact paragraph into three modernized paragraphs:
  1. scientific claim verification and claim-evidence reasoning;
  2. LLM-as-judge reliability and human grounding;
  3. scientific overstatement and evidence-aligned claim evaluation.

## What did not change

- No experiments were run.
- No API calls were made.
- No data were changed.
- No numeric results were changed.
- No paper claims were strengthened beyond V3.7.
- Silver-label limitations remain intact.

## Remaining caution

Some added works are very recent preprints. They improve the manuscript's currency, but they should be reviewed manually before final submission for venue status, final author order, and final bibliographic details.
