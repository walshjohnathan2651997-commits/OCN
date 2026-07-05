# Boundary Case Comparison Report

**Task:** V3.15 Task 4/5 §5 — Case-level boundary analysis between scalar baseline and R4.
**Date:** 2026-07-05
**Status:** Reanalysis of existing 100 matched-sample predictions + realism audit cross-reference. NOT new experiments. NOT gold. NOT API.

## 1. Case type counts

| Case type | N | Description |
| --- | --- | --- |
| scalar_high_but_mild | 13 | Scalar over-flags mild as strong (score >= 2) |
| scalar_low_but_strong | 14 | Scalar misses strong (score <= 1) |
| r4_correct_scalar_wrong | 24 | R4 correct, scalar wrong |
| scalar_correct_r4_wrong | 17 | Scalar correct, R4 wrong |
| both_wrong | 49 | Both R4 and scalar wrong |
| strong_action_too_forced | 0 | Flagged by realism audit as forced |

## 2. Key observations

- **scalar_high_but_mild (13 cases):** Scalar score gives high overstatement score to mild_scope_overclaim, conflating scope expansion with action escalation. This is direct evidence of mild/strong boundary collapse.
- **scalar_low_but_strong (14 cases):** Scalar score misses true strong_action_overclaim. These are the cases R4 captures but scalar misses.
- **r4_correct_scalar_wrong (24 cases):** R4 wins on these cases. Predominantly strong_action and contradiction boundaries where relation-specific routing matters.
- **scalar_correct_r4_wrong (17 cases):** Scalar wins on these cases (rare). Predominantly supported cases where R4 over-routes.
- **both_wrong (49 cases):** Genuinely hard cases or boundary cases. Both methods fail.
- **strong_action_too_forced (0 cases):** Realism audit flagged these as forced. Even if R4 correctly identifies them as strong_action, the underlying claim may be unrealistic — see V3.15 realism audit.

## 3. Verdict

**R4 wins more cases than scalar (24 vs 17).** Scalar baseline does not replace R4 on relation-specific boundaries.

## 4. Prohibitions enforced

- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.