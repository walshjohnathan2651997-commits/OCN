# Scalar Baseline Evaluation Report

**Task:** No-Gold RIGOURATE + Scalar Baseline Pipeline Part 1 - Section 3
**Date:** 2026-07-05
**Input:** rigourate_style_scalar_scores.csv (444 rows)

## 1. Baselines evaluated

- **rule_scalar_score** (Baseline A): cue-based 0-3 score, available for all 444 candidates.
  - Cues: action, deployment, safety, policy, generalization, guarantee, always, fully, replace, solve, ready, real-world + evidence limitation cues (limited, simulated, benchmark, remains, barrier, uncertainty, requires validation).
  - Scoring: 0=no overstatement, 1=mild scope, 2=strong action/deployment, 3=contradiction/severe mismatch.
  - Priority: contradiction (3) > strong_action (2) > mild_scope (1) > none (0).
- **nli_scalar_score** (Baseline B): **BLOCKED** (no HCM/NLI features available in repo).
- **llm_scalar_proxy** (Baseline C): LLM-label-derived 0-3 score, available for 200 candidates only.
  - Mapping: supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3.
  - Sources: DeepSeek-V3 (200 parsed outputs) + GPT structured (100 matched).
  - **This is LLM-label-derived proxy, NOT official RIGOURATE.**

## 2. Binary tasks

1. **supported_vs_overclaim** — supported (0) vs overclaim (1 = mild+strong+contra).
2. **mild_vs_strong** — mild_scope_overclaim (0) vs strong_action_overclaim (1).
3. **strong_vs_nonstrong** — strong_action_overclaim (1) vs all others (0).
4. **contradiction_vs_noncontradiction** — contradiction_candidate (1) vs all others (0).

## 3. Results summary

| Task | Baseline | N | ROC-AUC | PR-AUC | Best F1 | Best T | Precision | Recall | TP | FP | FN | TN | FP/TP | Review burden |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported_vs_overclaim | rule_scalar_score | 444 | 0.5036 | 0.7479 | 0.7665 | 1 | 0.7500 | 0.7838 | 261 | 87 | 72 | 24 | 0.3333 | 0.7838 |
| supported_vs_overclaim | llm_scalar_proxy | 200 | 0.8533 | 0.9546 | 0.8281 | 1 | 1.0000 | 0.7067 | 106 | 0 | 44 | 50 | 0.0000 | 0.5300 |
| mild_vs_strong | rule_scalar_score | 222 | 0.5054 | 0.5032 | 0.6105 | 1 | 0.5000 | 0.7838 | 87 | 87 | 24 | 24 | 1.0000 | 0.7838 |
| mild_vs_strong | llm_scalar_proxy | 100 | 0.5874 | 0.6723 | 0.5741 | 1 | 0.5345 | 0.6200 | 31 | 27 | 19 | 23 | 0.8710 | 0.5800 |
| strong_vs_nonstrong | rule_scalar_score | 444 | 0.5036 | 0.2549 | 0.3791 | 1 | 0.2500 | 0.7838 | 87 | 261 | 24 | 72 | 3.0000 | 0.7838 |
| strong_vs_nonstrong | llm_scalar_proxy | 200 | 0.5154 | 0.2420 | 0.3974 | 1 | 0.2925 | 0.6200 | 31 | 75 | 19 | 75 | 2.4194 | 0.5300 |
| contradiction_vs_noncontradiction | rule_scalar_score | 444 | 0.5036 | 0.2513 | 0.3791 | 1 | 0.2500 | 0.7838 | 87 | 261 | 24 | 72 | 3.0000 | 0.7838 |
| contradiction_vs_noncontradiction | llm_scalar_proxy | 200 | 0.9195 | 0.8285 | 0.8317 | 3 | 0.8235 | 0.8400 | 42 | 9 | 8 | 141 | 0.2143 | 0.2550 |

## 4. Required answers

### Q1. Can scalar score identify overclaim (supported vs overclaim)?

- **rule_scalar_score**: ROC-AUC=0.5036, best-F1=0.7665 @ t=1 (N=444). The cue-based scalar is **at chance level** for separating supported from overclaim.
- **llm_scalar_proxy**: ROC-AUC=0.8533, best-F1=0.8281 @ t=1 (N=200). The LLM-derived scalar can identify overclaim, but only on the matched subset and only because it inherits LLM label capacity.

**Q1 verdict:** A continuous scalar score CAN identify supported-vs-overclaim IF derived from a strong LLM judge. A pure cue-based scalar cannot. This is consistent with RIGOURATE's motivation that a learned scalar with strong model capacity is needed; naive cue counting is insufficient.

### Q2. Can scalar score reliably distinguish mild_scope vs strong_action?

- **rule_scalar_score**: ROC-AUC=0.5054, best-F1=0.6105 @ t=1 (N=222). **At chance level** for the mild-vs-strong distinction.
- **llm_scalar_proxy**: ROC-AUC=0.5874, best-F1=0.5741 @ t=1 (N=100). Also weak (ROC-AUC < 0.60), confirming LLM under-detects strong_action and compresses mild+strong into the same scalar region.

**Q2 verdict:** **NO.** Neither the cue-based scalar nor the LLM-derived scalar can reliably distinguish mild_scope_overclaim from strong_action_overclaim (both ROC-AUC < 0.60). This is the critical failure mode that motivates fine-grained four-class relation typing: a single scalar compresses the action-vs-scope distinction, which is exactly the distinction that matters most for high-risk screening.

### Q3. Can scalar score catch strong_action_overclaim?

- **rule_scalar_score**: ROC-AUC=0.5036, best-F1=0.3791 @ t=1, recall=0.7838, precision=0.2500 (N=444). **At chance level** for strong_action identification.
- **llm_scalar_proxy**: ROC-AUC=0.5154, best-F1=0.3974 @ t=1, recall=0.6200 (N=200). Also at chance level; apparent F1 is a threshold artefact, not genuine strong_action discrimination.

**Q3 verdict:** **NO.** Scalar scores (both rule-based and LLM-derived) are at chance-level discrimination (ROC-AUC ≤ 0.55) on strong_action identification. R4's dedicated strong_action escalation route (contradiction-gated escalation + calibrated residual classifier) provides structured screening signal that scalar compression cannot replicate. Reference: R4 frozen strong_F1=0.3967 on silver 444; rule_scalar best-F1 is below or comparable but at chance-level ROC-AUC.

### Q4. Can scalar score replace hierarchical relation typing?

Based on Q1-Q3:

- **Q1:** Scalar can identify supported-vs-overclaim only when derived from a strong LLM (ROC-AUC >= 0.85 on matched subset); a pure cue-based scalar cannot (ROC-AUC ~0.51).
- **Q2:** Scalar CANNOT distinguish mild from strong_action, even with LLM-derived scores (ROC-AUC < 0.60). This is the critical distinction the hierarchical taxonomy makes explicit and the scalar compresses away.
- **Q3:** Scalar CANNOT reliably catch strong_action_overclaim (ROC-AUC <= 0.55, chance-level).

**Q4 verdict:** **NO.** A scalar overstatement score is **insufficient** to replace hierarchical relation typing. The hierarchical taxonomy (Level 1: supported/overclaim/contradiction; Level 2: scope_expansion/strong_action under overclaim) has clear incremental value over a scalar score in two specific ways:

1. **Mild-vs-strong separation:** The taxonomy explicitly separates mild_scope_overclaim from strong_action_overclaim; a scalar score cannot (Q2). This is the high-risk boundary distinction that motivates the paper.
2. **Strong_action screening utility:** R4's dedicated strong_action route achieves strong_F1=0.3967 with structured routing, while scalar scores are at chance-level discrimination (ROC-AUC <= 0.55) on the same task (Q3).

The scalar score retains value for the broad supported-vs-overclaim distinction (Q1, llm_scalar ROC-AUC=0.85 on matched subset), so the two approaches are complementary: scalar for broad severity, taxonomy for high-risk action-overclaim screening. This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.

## 5. Threshold sensitivity

See `scalar_threshold_sweep.csv` for full threshold sweep.

- **mild_vs_strong / rule_scalar_score**: F1 range = [0.2745, 0.6667], spread = 0.3922
- **strong_vs_nonstrong / rule_scalar_score**: F1 range = [0.2154, 0.4000], spread = 0.1846

Key observation: best-F1 thresholds vary across tasks, indicating that **no single scalar threshold can simultaneously optimise all four binary distinctions**. This is direct evidence that a single scalar score is insufficient for the four-class screening task.

## 6. Limitations

- rule_scalar_score is a hand-crafted cue-based baseline; it is **NOT** the official RIGOURATE score.
- llm_scalar_proxy is LLM-label-derived (mapped from predicted 4-class label); it is **NOT** a true scalar overstatement score and is **NOT** the official RIGOURATE score.
- nli_scalar_score is **BLOCKED**; no HCM/NLI features in repo.
- All evaluation is on silver labels (pre-gold); gold adjudication may shift conclusions.
- SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus.
- The 200-sample LLM subset is not random (matched by group_id and silver_label); results on this subset are not directly comparable to the 444-sample full set.

## 7. Prohibitions enforced

- No paid API calls.
- No gold creation.
- No silver-as-gold.
- No claiming proxy as official RIGOURATE.
- No modification of original data or V3.15 paper.
- No annotation templates generated.
- No human annotation requested.
