# Gold Pilot Sampling Report — CESE-OCN v1

**Date:** 2026-07-04
**Output:** `D:\ocn\gold_pilot_preparation_v1\gold_pilot_candidate_50.csv`
**Total samples:** 50

---

## 1. Why 50 samples?

50 samples is the smallest size that allows meaningful inter-annotator agreement statistics while remaining feasible for two independent annotators within a reasonable timeframe (estimated 6-10 hours per annotator).

- **Smaller (e.g., 25):** Cohen's κ on per-boundary agreement becomes unstable; with only 3-4 cases per boundary type, a single disagreement swings κ by 0.1+.
- **Larger (e.g., 100-200):** Better statistics, but requires substantially more annotator time (12-40 hours per annotator) and delays the gold pilot feedback loop. The 50-sample pilot is designed to *test whether the taxonomy is drawable* before committing to a larger adjudication effort.
- **Per-class minimum:** 50 samples allows ≥ 9 cases per class (supported 9, mild 10, strong 20, contradiction 11), which is enough for per-class agreement statistics while concentrating the high-risk boundary cases where disagreement is most likely.

50 is a **pilot**, not a final gold set. If the 50-sample pilot shows κ ≥ 0.4 on the mild/strong boundary, a larger gold adjudication (100-200 pairs) is recommended as the next step.

## 2. Why high-risk 25 cases must be prioritized

The 25 high-risk boundary cases (from `high_risk_sample_bank.csv`) are the **single most informative subset** for testing whether the four-class taxonomy is drawable. They were flagged in the V3.4 author sanity audit as cases where:
- The silver label may be wrong (alternative label listed in `possible_alternative_label`).
- The boundary between two classes is genuinely unclear (e.g., mild_vs_strong, strong_vs_contradiction).
- The audit heuristic missed a pattern (e.g., detail-swapping as contradiction).

These 25 cases directly test the three boundaries that the paper's central contribution depends on:
- **mild vs strong** (15 cases, HRC_001-015): Is `strong_action_overclaim` distinguishable from `mild_scope_overclaim`? If gold annotators cannot reliably separate these, the central class may need to be merged.
- **strong vs contradiction** (6 cases, HRC_020-025): Is detail-swapping reliably classified as contradiction, not strong_action? If gold annotators disagree, the contradiction detector's recall is unverifiable.
- **supported vs mild** (1 case, HRC_016) and **evidence_context_missing** (3 cases, HRC_016-019): Is `mild_scope_overclaim` distinguishable from `supported` when scope cues are weak?

If these 25 cases show κ ≥ 0.4 on each boundary, the taxonomy is defensible. If they show κ < 0.4, the paper's central contribution needs revision **before** any larger gold effort.

## 3. Label distribution (silver labels, for reference only — NOT gold)

| Silver label | Count | Source: high-risk | Source: trusted | Source: random |
|---|---|---|---|---|
| supported | 9 | 0 | 4 | 5 |
| mild_scope_overclaim | 10 | 4 | 4 | 2 |
| strong_action_overclaim | 20 | 15 | 4 | 1 |
| contradiction_candidate | 11 | 6 | 4 | 1 |
| **Total** | **50** | **25** | **16** | **9** |

**Note:** Silver labels are shown here for sampling-report purposes only. Annotators will NOT see silver labels. The distribution is skewed toward `strong_action_overclaim` (20/50 = 40%) because the high-risk sample bank is concentrated on the mild_vs_strong boundary (15/25 high-risk cases are silver-labeled strong_action). This is intentional — the pilot's primary goal is to test the mild/strong boundary.

## 4. Domain distribution

| Domain | Count | Source: high-risk | Source: trusted | Source: random |
|---|---|---|---|---|
| autonomous_driving | 11 | 5 | 4 | 2 |
| policy_simulation | 10 | 5 | 4 | 1 |
| marl | 9 | 4 | 4 | 1 |
| cyber_defense | 8 | 3 | 1 | 4 |
| digital_twin | 6 | 3 | 1 | 2 |
| robotics | 6 | 5 | 2 | 0 |
| **Total** | **50** | **25** | **16** | **9** |

All 6 SimClaim domains are represented. The distribution roughly mirrors the SimClaim silver set's domain proportions.

## 5. Boundary type distribution

| Boundary type | Count | Source: high-risk | Source: trusted | Source: random |
|---|---|---|---|---|
| mild_vs_strong | 16 | 15 | 0 | 1 |
| clear_illustrative | 16 | 0 | 16 | 0 |
| random_sample | 9 | 0 | 0 | 9 |
| strong_vs_contradiction | 8 | 6 | 0 | 2 |
| supported_vs_mild | 1 | 1 | 0 | 0 |
| **Total** | **50** | **25** | **16** | **9** |

- **mild_vs_strong (16):** The hardest and most consequential boundary. 15 from high-risk + 1 random.
- **strong_vs_contradiction (8):** Detail-swapping vs action-escalation. 6 from high-risk + 2 random.
- **clear_illustrative (16):** Trusted cases (4 per class) for baseline agreement check.
- **random_sample (9):** Unscreened cases for representativeness.
- **supported_vs_mild (1):** Only 1 case — this boundary is less contested in the audit, but underrepresented.

## 6. Samples for taxonomy validation

The following subsets are designed to test specific taxonomy claims:

| Taxonomy claim | Subset | Sample IDs |
|---|---|---|
| `strong_action_overclaim` is distinguishable from `mild_scope_overclaim` | 15 high-risk mild_vs_strong cases (HRC_001-015) | P001-P015 |
| `contradiction_candidate` (detail-swapping) is distinguishable from `strong_action_overclaim` | 6 high-risk strong_vs_contradiction cases (HRC_020-025) | P020-P025 |
| `mild_scope_overclaim` is distinguishable from `supported` | 1 high-risk supported_vs_mild case (HRC_016) + trusted mild/supported pairs | P016, P026-P033 |
| All four classes are reliably drawable | 16 trusted illustrative cases (4 per class) | P026-P041 |

**Decision rule:**
- If gold κ on mild_vs_strong (P001-P015) ≥ 0.4 → `strong_action_overclaim` is defensible as a separate class.
- If gold κ on mild_vs_strong < 0.4 → consider merging `strong_action_overclaim` with `mild_scope_overclaim`.
- If gold κ on strong_vs_contradiction (P020-P025) ≥ 0.4 → detail-swapping is reliably contradiction.
- If gold κ on strong_vs_contradiction < 0.4 → the contradiction detector's boundary needs revision.

## 7. Samples for LLM/R4 re-evaluation

After gold adjudication, the 50 gold-labeled pairs can be used to re-evaluate:
- **R4 router:** Re-compute strong_action-F1, mild-F1, contradiction-F1, supported-F1 against gold labels (currently computed against silver).
- **LLM judges (GPT-5.5, DeepSeek-V3):** Re-compute strong_action-F1 against gold labels. If LLM strong_action-F1 remains low (≤ 0.15) on gold-labeled pairs, the "LLM under-detection" finding is strengthened. If LLM strong_action-F1 rises substantially on gold (≥ 0.30), the finding was an artifact of silver labels and the paper's central claim weakens.
- **Combined system:** Test whether LLM + R4 escalation outperforms either alone on gold-labeled pairs.

The 9 random samples (P042-P050) are specifically included to prevent the re-evaluation from being tested only on boundary cases. If R4/LLM performance on the 9 random samples differs substantially from the 41 boundary/trusted samples, the paper should report both.

## 8. What this pilot CANNOT prove

This 50-sample gold pilot **cannot**:

1. **Establish the LLM under-detection finding as a general property of LLM judges.** 50 samples is too small, and the LLM comparison remains prompt/model/sample-specific. The pilot can only test whether the finding holds against gold labels (vs. silver), not whether it generalizes across models/prompts.

2. **Validate the four-class taxonomy as a public benchmark.** The pilot tests whether two annotators can reliably draw the boundaries, but a public benchmark requires larger-scale multi-annotator adjudication (≥ 200 pairs, ≥ 3 annotators, κ reported per class).

3. **Prove R4 is superior to LLM judges.** R4's macro-F1 is lower than GPT/DeepSeek. The pilot can only test whether R4's strong_action-F1 advantage holds against gold labels, not whether R4 is better overall.

4. **Resolve the mild/strong boundary definitively.** Even if gold κ ≥ 0.4 on 16 mild_vs_strong cases, the boundary may not generalize to other domains or harder cases. The pilot provides evidence, not proof.

5. **Replace the silver-label pilot results.** The 444-pair silver results remain the main quantitative findings. The 50-pair gold pilot is a *validation check* on those findings, not a replacement.

6. **Be used as a training set.** The 50 gold pairs are for evaluation and agreement statistics only. They must not be used to train or tune R4 or any other model. Using them for training would invalidate them as a gold evaluation set.

---

**Bottom line:** This 50-sample pilot is designed to answer one question: *Can two independent annotators reliably draw the four-class boundaries, especially mild_vs_strong?* If yes, the paper's taxonomy is defensible and a larger gold effort is warranted. If no, the taxonomy needs revision before any further gold adjudication.
