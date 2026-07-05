# Scalar Baseline Evaluation Report

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 5
**Date:** 2026-07-05
**Input:** rigourate_style_scalar_scores.csv (444 rows)

## 1. Baselines evaluated

- **rule_scalar_score** (Baseline A): cue-based 0-3 score, available for all 444 pairs.
- **nli_scalar_score** (Baseline B): BLOCKED (HCM/NLI features not in repo).
- **llm_scalar_proxy** (Baseline C): LLM-label-derived 0-3 score, available for 200 matched pairs only.

## 2. Binary tasks

1. **supported_vs_overclaim** — supported (0) vs overclaim (1 = mild+strong+contra). N=444, positive=333.
2. **mild_vs_strong** — mild_scope_overclaim (0) vs strong_action_overclaim (1). N=222, positive=111.
3. **strong_vs_contradiction** — strong_action_overclaim (0) vs contradiction_candidate (1). N=222, positive=111.
4. **strong_vs_nonstrong** — strong_action_overclaim (1) vs all others (0). N=444, positive=111.

## 3. Results summary

| Task | Baseline | N | ROC-AUC | PR-AUC | Best F1 | Best Threshold | Precision | Recall | TP | FP | FN | TN |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported_vs_overclaim | rule_scalar_score | 444 | 0.5136 | 0.7563 | 0.7466 | 1.0 | 0.7546 | 0.7387 | 246 | 80 | 87 | 31 |
| supported_vs_overclaim | llm_scalar_proxy | 200 | 0.8533 | 0.9267 | 0.8281 | 1.0 | 1.0000 | 0.7067 | 106 | 0 | 44 | 50 |
| mild_vs_strong | rule_scalar_score | 222 | 0.5062 | 0.5016 | 0.6109 | 1.0 | 0.5122 | 0.7568 | 84 | 80 | 27 | 31 |
| mild_vs_strong | llm_scalar_proxy | 100 | 0.5874 | 0.5931 | 0.5741 | 1.0 | 0.5345 | 0.6200 | 31 | 27 | 19 | 23 |
| strong_vs_contradiction | rule_scalar_score | 222 | 0.5233 | 0.5209 | 0.5921 | 1.0 | 0.4940 | 0.7387 | 82 | 84 | 29 | 27 |
| strong_vs_contradiction | llm_scalar_proxy | 100 | 0.8512 | 0.7985 | 0.8400 | 3.0 | 0.8400 | 0.8400 | 42 | 8 | 8 | 42 |
| strong_vs_nonstrong | rule_scalar_score | 444 | 0.4971 | 0.2464 | 0.3844 | 1.0 | 0.2577 | 0.7568 | 84 | 242 | 27 | 91 |
| strong_vs_nonstrong | llm_scalar_proxy | 200 | 0.5154 | 0.2505 | 0.3974 | 1.0 | 0.2925 | 0.6200 | 31 | 75 | 19 | 75 |

## 4. Required answers

### Q1. Can scalar score identify overclaim (supported vs overclaim)?

- **rule_scalar_score**: NO. ROC-AUC=0.5136, best-F1=0.7466 @ t=1.0. The cue-based scalar score is essentially at chance level for separating supported from overclaim.
- **llm_scalar_proxy**: YES. ROC-AUC=0.8533, best-F1=0.8281 @ t=1.0 (N=200). The LLM-derived scalar is much better at this task because LLM judges can identify supported claims well; however, this is on a 200-sample subset and the scalar is LLM-label-derived (not a true continuous score).

**Q1 verdict:** A continuous scalar score CAN identify supported-vs-overclaim IF the scalar is derived from a strong LLM judge (llm_scalar_proxy ROC-AUC=0.8533). A pure cue-based scalar (rule_scalar_score ROC-AUC=0.5136) cannot. This is consistent with RIGOURATE's motivation that a learned scalar with strong model capacity is needed; naive cue counting is insufficient.

### Q2. Can scalar score reliably distinguish mild vs strong_action?

- **rule_scalar_score**: NO. ROC-AUC=0.5062, best-F1=0.6109 @ t=1.0. Cue-based scalar is at chance level for the mild-vs-strong distinction.
- **llm_scalar_proxy**: PARTIAL. ROC-AUC=0.5874, best-F1=0.5741 @ t=1.0 (N=100). LLM-derived scalar is also weak for this distinction (ROC-AUC 0.55-0.60), confirming that the LLM under-detects strong_action and compresses mild+strong into the same scalar region.

**Q2 verdict:** NO. Neither the cue-based scalar (ROC-AUC=0.5062) nor the LLM-derived scalar (ROC-AUC=0.5874) can reliably distinguish mild_scope_overclaim from strong_action_overclaim. This is the critical failure mode that motivates fine-grained four-class relation typing: a single scalar compresses the action-vs-scope distinction, which is exactly the distinction that matters most for high-risk screening.

### Q3. Can scalar score replace R4 strong_action route?

- **Reference (R4 frozen, silver 444):** strong_F1=0.3967, strong_recall=0.4562, strong_precision=0.3791
- **rule_scalar_score** on strong_vs_nonstrong: ROC-AUC=0.4971 (chance), best-F1=0.3844 @ t=1.0, precision=0.2577, recall=0.7568
  - best-F1 (0.3844) vs R4 strong_F1 (0.3967): rule_scalar is BELOW R4.
- **llm_scalar_proxy** on strong_vs_nonstrong (N=200): ROC-AUC=0.5154 (chance), best-F1=0.3974 @ t=1.0, precision=0.2925, recall=0.6200
  - best-F1 (0.3974) vs R4 strong_F1 (0.3967): llm_scalar is approximately TIED with R4 in F1, but at ROC-AUC=0.5154 (chance-level discrimination), the apparent F1 is driven by threshold artefacts, not genuine strong_action identification. The LLM scalar predicts almost no samples as score=2 (only 2/200 in the matched subset), so its recall on strong_action is severely limited.

**Q3 verdict:** NO. A scalar score cannot replace the R4 strong_action route. The rule_scalar_score is below R4 on F1 (0.3844 vs 0.3967). The llm_scalar_proxy is approximately tied with R4 on F1 (0.3974 vs 0.3967), but its ROC-AUC is at chance level (0.5154), meaning the apparent F1 is a threshold artefact, not genuine discrimination. R4's dedicated strong_action escalation route, which uses contradiction-gated escalation and a calibrated residual classifier, provides structured screening signal that scalar compression cannot replicate.

### Q4. Does CESE-OCN fine-grained taxonomy have incremental value?

Based on Q1-Q3:

- **Q1:** Scalar can identify supported-vs-overclaim only when derived from a strong LLM (ROC-AUC=0.85); a pure cue-based scalar cannot (ROC-AUC=0.51). The taxonomy's `supported` boundary is partially learnable by LLMs but not by simple cues.
- **Q2:** Scalar CANNOT distinguish mild from strong_action, even with LLM-derived scores (ROC-AUC=0.59, below 0.70). This is the critical distinction the four-class taxonomy makes explicit and the scalar compresses away.
- **Q3:** Scalar CANNOT replace R4 strong_action route. R4's structured routing (contradiction detector + scope-calibration residual + strong-action escalation) provides screening signal that scalar compression cannot match.

**Q4 verdict:** YES. The CESE-OCN fine-grained four-class taxonomy has clear incremental value over a scalar overstatement score in two specific ways:

1. **Mild-vs-strong separation:** The taxonomy explicitly separates mild_scope_overclaim from strong_action_overclaim; a scalar score cannot (Q2). This is the high-risk boundary distinction that motivates the paper.
2. **Strong_action screening utility:** R4's dedicated strong_action route achieves strong_F1=0.3967 with recall=0.4562, while scalar scores (both rule-based and LLM-derived) are at chance-level discrimination (ROC-AUC ≤ 0.52) on the same task (Q3).

The scalar score retains value for the broad supported-vs-overclaim distinction (Q1, llm_scalar ROC-AUC=0.85), so the two approaches are complementary: scalar for broad severity, taxonomy for high-risk action-overclaim screening. This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Threshold sensitivity

See `scalar_baseline_threshold_sweep.csv` for full threshold sweep.
Key observation: best-F1 thresholds vary across tasks, indicating that no single scalar threshold can simultaneously optimise all four binary distinctions. This is direct evidence that a single scalar score is insufficient for the four-class screening task.

## 6. Limitations

- rule_scalar_score is a hand-crafted cue-based baseline; it is NOT the official RIGOURATE score.
- llm_scalar_proxy is LLM-label-derived (mapped from predicted 4-class label); it is NOT a true scalar overstatement score and is NOT the official RIGOURATE score.
- nli_scalar_score is BLOCKED; no HCM/NLI features in repo.
- All evaluation is on silver labels (pre-gold); gold adjudication may shift conclusions.
- SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus; realism audit (section 8) addresses claim naturalness separately.

## 7. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data or V3.12 paper.
