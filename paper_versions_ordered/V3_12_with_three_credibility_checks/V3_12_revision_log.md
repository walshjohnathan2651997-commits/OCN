# V3.12 Revision Log

**Version:** V3.12 With Three Credibility Checks
**Date:** 2026-07-04
**Base version:** V3.11 High-Standard Framework
**Type of change:** Insertion-only (no rewrites of V3.11 content, no experimental changes)

---

## Summary

V3.12 inserts three non-gold credibility checks (§VIII.D) into the V3.11 manuscript, based on already-existing data, predictions, and scores from `D:\ocn\experiments\v3_11_three_core_credibility_experiments\`. **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning, no change to any experimental number.** All §VI numbers are preserved byte-identical from V3.11. The new section is explicitly labeled as non-gold robustness analysis and does not replace gold adjudication.

## Changes Made

### 1. Version header (line 3, 8)
- **Before:** "V3.11 High-Standard Framework (validation-pending, protocol-locked)"
- **After:** "V3.12 With Three Credibility Checks (validation-pending, protocol-locked)"
- **Added:** "Changes from V3.11" paragraph documenting the insertion-only nature of the change.

### 2. Abstract (line 16)
- **Added one sentence:** "We further report three non-gold credibility checks (§VIII.D) testing evidence necessity, screening utility, and sensitivity to simulated strong-label shift."
- **Rationale:** Per spec — only one short补强 sentence; abstract length preserved.

### 3. §I organization paragraph (line 42)
- **Added clause:** "§VIII discusses implications, including three non-gold credibility checks (§VIII.D) that test evidence necessity, screening utility, and label-shift robustness before gold adjudication"

### 4. §VIII.D — NEW SECTION (inserted at line 469)
- **New section title:** "§VIII.D Robustness and Credibility Checks Before Gold Adjudication"
- **Subsections:**
  - §VIII.D.A Evidence Necessity Check (Layer A NLI audit + Layer B TF-IDF sanity)
  - §VIII.D.B Screening Utility Test (matched-100, FP/TP=2.89, captures 8 LLM-missed)
  - §VIII.D.C Label-Shift Stress Test (1000 bootstrap, break-even ~0.5)
  - Summary of §VIII.D
- **Opening caveat:** "These checks are non-gold robustness analyses. They do not replace gold adjudication (§VII)."
- **Numbers used:** All from existing experiment outputs; no new numbers generated.

### 5. §VIII.E — RENUMBERED (was §VIII.D)
- **Before:** "§VIII.D What Remains Unresolved"
- **After:** "§VIII.E What Remains Unresolved"
- **Content:** Unchanged. Only the section letter changed.

### 6. §IX Limitations — ADDED ITEM 8 (line 542)
- **Added:** "8. The three credibility checks in §VIII.D are non-gold robustness analyses and do not replace independent gold adjudication..."
- **Rationale:** Per spec — add Limitations item restating the non-gold caveat, the 50%-CI-crosses-zero caveat, and that simulated label shift is not gold data.

## What Was NOT Changed

| Item | Status |
|---|---|
| §VI Results numbers (R4 strong-F1 0.3967, LLM 0.0769, macro-F1 0.3280/0.5523, etc.) | Preserved byte-identical |
| R4 macro-F1 < LLM fact | Preserved (still stated in §VIII.A, §IX.4, §X) |
| Gold not yet performed fact | Preserved (still stated in §VIII.E, §IX.1, §IX.7) |
| §VII Pre-Registered Gold Validation Protocol | Unchanged |
| Frozen R4 thresholds (t_contra=0.48, t_strong=0.535, t_svm=0.51) | Unchanged |
| Taxonomy boundary rules | Unchanged |
| V3.11 source file | Preserved unchanged (verified by size and content check) |
| V3.10.1, V3.9 source files | Preserved unchanged |

## Quality Verification

| Check | Result |
|---|---|
| Mojibake characters | NONE found |
| §VIII subsection order | A → B → C → D (new) → E (renamed) ✓ |
| Key numbers preserved (0.3967, 0.0769, 0.3280, 0.5523, 0.2408, 0.2231) | All present ✓ |
| Non-gold caveat present | ✓ ("These checks are non-gold robustness analyses") |
| 50% retention NOT written as robust pass | ✓ ("must *not* be reported as a robust pass") |
| R4 macro-F1 < LLM fact preserved | ✓ |
| Gold not done fact preserved | ✓ |
| V3.11 unchanged | ✓ (no new section header in V3.11, no limitation 8 in V3.11) |
| DOCX generated | ✓ (33849 bytes, valid OOXML) |
| File size delta | V3.12 = 93389 bytes; V3.11 = 82599 bytes; +10790 bytes (added section) |

## Forbidden Actions Check

| Forbidden action | Status |
|---|---|
| Modify V3.11 original files | NOT done ✓ |
| Run new experiments | NOT done ✓ |
| Call API | NOT done ✓ |
| Do gold annotation | NOT done ✓ |
| Change experimental numbers | NOT done ✓ |
| Write non-gold as gold | NOT done ✓ |
| Delete R4 macro-F1 < LLM fact | NOT done ✓ |
| Delete gold-not-done fact | NOT done ✓ |
| Write 50% retention as robust pass | NOT done ✓ |
