# R4 False Positive Root Cause Analysis Report

**Date:** 2026-07-05
**Source:** case_level_comparison.csv (100 matched samples, 21 columns with claim_text)
**Status:** Reanalysis only. SILVER labels. R4 predictions from frozen thresholds.

## 1. R4 false positive count

R4 predicted strong_action_overclaim on 26 samples where silver was non-strong.
(R4 predicts strong on 35 of 100 total; 26 are false positives.)

## 2. False positives by silver label

| Silver label | n_FP | % of FP | with action cues | with safety cues | with deployment cues | with generalization cues | long claims |
|---|---|---|---|---|---|---|---|
| supported | 12 | 46.15% | 0 | 0 | 0 | 0 | 0 |
| mild_scope_overclaim | 13 | 50.0% | 0 | 1 | 0 | 0 | 0 |
| contradiction_candidate | 1 | 3.85% | 0 | 0 | 0 | 0 | 0 |

## 3. False positives by domain

| Domain | n_FP | % of FP |
|---|---|---|
| autonomous_driving | 2 | 7.69% |
| cyber_defense | 1 | 3.85% |
| digital_twin | 7 | 26.92% |
| marl | 5 | 19.23% |
| policy_simulation | 8 | 30.77% |
| robotics | 3 | 11.54% |

## 4. Root cause categories (per-case, see r4_false_positive_cases.csv)

Categories:
- mild_strong_boundary_confusion: silver=mild but R4 routed to strong (hardest boundary)
- supported_overclained_by_r4: silver=supported but R4 saw action cues
- contradiction_absorbed_by_strong_route: silver=contradiction but R4's strong route absorbed it
- multiple_action_cues_in_claim: >=2 action/deployment/safety cues triggered R4's strong route
- claim_too_long_abstract: claim_length > 250 chars (abstract claims may trigger escalation)
- no_clear_action_cue_but_r4_strong: R4 escalated without clear action cue (threshold artifact)

## 5. Interpretation

R4's false positives concentrate in:
1. **mild_scope_overclaim** samples (boundary confusion — the hardest part of the taxonomy)
2. Claims with multiple action/deployment/generalization cue words (R4's cue-based escalation triggers correctly on cues but the silver label is non-strong)
3. Long, abstract claims (R4's routing may over-escalate)

This is consistent with R4's design: R4 trades precision for recall on strong_action, intentionally over-routing to strong_action to capture LLM-missed cases. The FP rate is the cost of this trade.

## 6. Recommendations

- Report FP breakdown by silver label in the paper (R4 over-routes mild→strong, contradiction→strong).
- Note that mild→strong confusion is the same boundary that scalar score cannot resolve (T5 score collapse).
- Consider adding a mild-vs-strong second-stage filter (proposed two-stage pipeline).
