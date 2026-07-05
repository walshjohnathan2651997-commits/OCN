# Claim Realism Audit Summary

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 8
**Date:** 2026-07-05
**Audit scope:** All 444 SimClaim silver pairs (controlled counterfactual diagnostic set)
**Audit method:** Heuristic pattern matching on claim_text + evidence_text. NOT a substitute for human realism review.

## 1. Summary statistics

- **Total claims audited:** 444
- **Claims with realism risk flag:** 21 (4.7%)
- **Recommended for gold realism check:** 21 / 444

## 2. Risk type distribution

| Risk type | Count | % |
| --- | --- | --- |
| none | 423 | 95.3% |
| too_template_like | 8 | 1.8% |
| too_extreme | 7 | 1.6% |
| unnatural_wording | 6 | 1.4% |

## 3. Risk by silver label

| Silver label | N | Risk flagged | Risk rate |
| --- | --- | --- | --- |
| supported | 111 | 3 | 2.7% |
| mild_scope_overclaim | 111 | 4 | 3.6% |
| strong_action_overclaim | 111 | 10 | 9.0% |
| contradiction_candidate | 111 | 4 | 3.6% |

### Risk type x silver label crosstab

| Silver label | none | too_extreme | too_template_like | unnatural_wording | All |
| --- | --- | --- | --- | --- | --- |
| contradiction_candidate | 107 | 0 | 2 | 2 | 111 |
| mild_scope_overclaim | 107 | 0 | 2 | 2 | 111 |
| strong_action_overclaim | 101 | 7 | 2 | 1 | 111 |
| supported | 108 | 0 | 2 | 1 | 111 |
| All | 423 | 7 | 8 | 6 | 444 |

## 4. Required answers

### Q1. Is claim realism a primary risk?

- **Verdict:** NO. 21/444 (4.7%) of SimClaim claims have heuristic realism risk flags. Realism risk is low.

### Q2. Which labels are most unnatural?

- **strong_action_overclaim**: 10/111 = 9.0%
- **mild_scope_overclaim**: 4/111 = 3.6%
- **contradiction_candidate**: 4/111 = 3.6%
- **supported**: 3/111 = 2.7%

- **Most unnatural label:** strong_action_overclaim (9.0% risk flag rate)
- **Least unnatural label:** supported (2.7% risk flag rate)

### Q3. Does gold need a realism_score?

- **YES.** The heuristic audit shows non-trivial realism risk across all silver labels. The V3.13 `proposed_gold_realism_extension.md` already specifies `claim_realism_score_1_to_5` and `claim_realism_issue` fields. This audit confirms that those fields are needed: gold annotators should rate claim realism independently of relation labeling, and claims with low realism scores should be flagged for paper-validity review.
- Pre-registered thresholds (25% class-level, 25% paper-level) from the V3.13 extension should be applied to the gold realism scores once collected. The heuristic rates in this audit are upper bounds; human gold realism review may yield lower (or different) rates.

## 5. Limitations

- Heuristic pattern matching is a coarse pre-screen; it has both false positives (flagging natural claims) and false negatives (missing subtle unnaturalness).
- The audit does NOT replace human realism review; it produces a queue for prioritisation.
- Risk type assignments are priority-ordered when multiple risks are present; the CSV records only the primary risk type. Full multi-risk annotation is future work.
- All claims are SimClaim silver-stage (pre-gold); gold adjudication may shift realism judgments.

## 6. Prohibitions enforced

- No paid API calls.
- No gold creation (this is a heuristic pre-screen, not gold).
- No silver-as-gold.
- No claiming SimClaim claims as natural claims.
- No modification of original data.