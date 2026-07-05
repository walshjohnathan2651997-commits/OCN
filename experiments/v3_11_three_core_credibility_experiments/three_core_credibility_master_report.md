# Three Core Credibility Experiments — Master Report

**Version:** V3.11 Three Core Credibility Experiments
**Date:** 2026-07-04
**Type: Non-gold robustness analysis.** Does not replace gold adjudication. Strengthens the silver-stage RELATIVE pattern only. Simulated label shift is NOT gold data — it is a sensitivity probe.
**Constraint:** No gold, no API, no new model training, no threshold retuning. Only existing data, predictions, and scores.

---

## Executive Summary

Three credibility experiments test whether V3.11's main claims are:
1. **Evidence-dependent** (not claim-only shortcut)
2. **Screening-useful** (R4 has value despite low macro-F1)
3. **Label-shift robust** (survives gold-induced label changes)

**Bottom line:** All 3 experiments pass at the directional-signal level. The RELATIVE pattern (R4 > LLM on strong_action) is evidence-dependent and screening-viable. Label-shift robustness is strong at ≥70% retention, marginal-positive at 60%, and **positive-but-statistically-weaker (CI crosses zero) at 50%** — the 50% retention result must NOT be reported as a robust pass.

## 1. Evidence Necessity Check

- **Correct evidence accuracy (Layer A audit):** 0.4324
- **User-spec perturbed accuracies:** empty=0.2545, shuffled=0.3851, same_domain_wrong=0.2568
- **Correct beats all 3 user-spec perturbed (audit):** True
- **TF-IDF sim (Layer B):** correct=0.4131 vs empty=0.0000, same_domain_wrong=0.0124 (correct beats both). shuffled=0.4131 is identical to correct because TF-IDF is bag-of-words; the shuffled condition is discriminated by the NLI audit (order-sensitive), which shows a 0.0473 accuracy drop.
- **NLI-TF-IDF correlation:** r=-0.2736 (negative). **TF-IDF and NLI probe DIFFERENT dimensions of the claim-evidence relation** — TF-IDF measures surface lexical overlap, NLI s_correct measures semantic entailment. The two signals are complementary, not redundant. Both layers independently support evidence dependence.
- **PASSED:** Task is evidence-dependent, not claim-only.

## 2. Screening Utility Test

- **FP/TP ratio:** 2.89 (threshold: 10)
- **Recall:** 0.3600 (9/25)
- **Precision:** 0.2571
- **Review burden:** 35.0%
- **R4 captures LLM-missed:** 8 cases
- **Screening viable:** True
- **Field naming:** `predicted_strong_by_silver_class` (TP+FP combined, was previously mislabeled as `fp_by_silver_class`); `actual_false_positive_by_silver_class` is FP-only (supported=12, mild_scope_overclaim=13, contradiction_candidate=1).

## 3. Label-Shift Stress Test

- **Break-even retention:** ~0.5 (delta 95% CI crosses zero at 50% retention)
- **70% retention:** R4 wins 100.0% (Δ=+0.1692, CI=[+0.083, +0.264]) — **robust**
- **60% retention:** R4 wins 98.6% (Δ=+0.1408, CI=[+0.035, +0.280]) — **marginal-positive**, CI lower bound just above 0
- **50% retention:** R4 wins 94.2% (Δ=+0.1137, CI=[-0.026, +0.255]) — **positive but statistically weaker / CI crosses zero**. Do NOT report as a robust pass.
- **Robust because:** LLM F1 ≈ 0.077, shrinking positive set hurts R4 precision but cannot help LLM. However, point-estimate dominance is not statistical robustness.

## Recommendations for V3.12

1. **Insert §VIII.D** with these 3 experiments, clearly labeled as "non-gold robustness analysis."
2. **Evidence Necessity** supports the task definition: evidence sufficiency calibration is a real task, not a claim-only shortcut. Report TF-IDF and NLI as complementary signals (negative correlation is expected, not contradictory).
3. **Screening Utility** quantifies R4's operational value: FP/TP=2.89, captures 8 LLM-missed cases. Use `actual_false_positive_by_silver_class` for FP breakdown, not `predicted_strong_by_silver_class`.
4. **Label-Shift** sets the gold pilot success bar with statistical caveats:
   - retention ≥ 70% → strong_action claim is robust
   - 60% → marginal-positive (CI lower bound just above 0)
   - 50% → **positive but statistically weaker / CI crosses zero** — report as directional signal, not robust pass
   - < 50% → downgrade per §VII.G
5. **Do NOT claim gold validation.** These tests strengthen the silver-stage RELATIVE pattern only. Simulated label shift is a sensitivity probe, not gold data.

## Readiness Gate

```json
{
  "evidence_necessity_passed": true,
  "correct_evidence_beats_perturbed": true,
  "screening_viable": true,
  "screening_fp_tp_ratio": 2.888888888888889,
  "screening_recall": 0.36,
  "r4_captures_llm_missed_cases": true,
  "label_shift_break_even_retention": "~0.5",
  "r4_wins_at_60_percent_retention": true,
  "r4_wins_at_50_percent_retention": true,
  "statistical_strength_at_60pct": "marginal-positive (CI lower bound just above 0 at 0.035)",
  "statistical_strength_at_50pct": "positive but statistically weaker / CI crosses zero (delta_ci_low=-0.0262)",
  "can_strengthen_v3_11_without_gold": true,
  "non_gold_robustness_analysis": true,
  "does_not_replace_gold": true,
  "recommended_paper_section_insert": "§VIII.D Three Core Credibility Experiments: (1) Evidence Necessity Check — correct evidence beats all perturbed conditions; (2) Screening Utility — FP/TP=2.89, R4 captures 8 LLM-missed strong_action cases; (3) Label-Shift Stress — break-even at ~0.5 retention, with 50% being positive-but-statistically-weaker (CI crosses zero). These strengthen V3.11's silver-stage claims without gold annotation.",
  "main_remaining_risk": "Evidence Necessity uses pre-existing audit results (v4 dataset, same SimClaim backbone but earlier version). The TF-IDF sanity check confirms the signal on the current dataset. Absolute strong_action F1 numbers remain silver-stage; gold adjudication needed to confirm absolute values and mild_vs_strong κ. At 50% retention the label-shift delta CI crosses zero — the 50% result is a directional signal, not a robust pass.",
  "recommended_next_action": "Insert §VIII.D into V3.12 with these 3 experiments, with the 50% retention caveat clearly stated. Proceed to 50-sample gold pilot per §VII protocol. The label-shift break-even (~50% retention) sets the minimum gold success bar: if gold retention ≥ 70%, the strong_action claim is robust; if 60%, marginal-positive; if 50%, positive-but-weaker (CI crosses zero); if <50%, downgrade per §VII.G.",
  "auxiliary": {
    "evidence_necessity_correct_acc": 0.4324324324324324,
    "evidence_necessity_min_perturbed_acc": 0.2545045045045045,
    "tfidf_nli_correlation": -0.27362379289375793,
    "tfidf_nli_correlation_interpretation": "negative — TF-IDF and NLI probe different dimensions (surface overlap vs semantic entailment), complementary not redundant",
    "screening_tp": 9,
    "screening_fp": 26,
    "screening_r4_captures_llm_missed": 8,
    "screening_actual_fp_by_silver_class": {"supported": 12, "mild_scope_overclaim": 13, "contradiction_candidate": 1},
    "label_shift_delta_60pct": 0.14077499999999998,
    "label_shift_delta_60pct_ci": [0.035, 0.28],
    "label_shift_delta_50pct": 0.11372504091653028,
    "label_shift_delta_50pct_ci": [-0.02618657937806876, 0.2553191489361702]
  }
}
```
