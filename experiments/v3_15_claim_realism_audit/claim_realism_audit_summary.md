# Claim Realism Audit Summary

**Task:** V3.15 Claim Realism Audit + Synthetic Counterfactual Risk Scoring
**Date:** 2026-07-05
**Audit type:** Automatic, author-side realism risk audit (heuristic rules).
**Disclaimer:** This is NOT human gold. NOT a naturalistic study. All risk flags are heuristic and require human validation in the gold pilot.
**Output directory:** `D:\ocn\experiments\v3_15_claim_realism_audit`

---

## 1. Audit overview

- **Claims audited:** 444 (444 SimClaim counterfactual candidates)
- **Groups audited:** 111 (111 evidence groups, 4 claims each)
- **Labels:** 111 supported + 111 mild_scope_overclaim + 111 strong_action_overclaim + 111 contradiction_candidate
- **Domains:** 6 (autonomous_driving, policy_simulation, digital_twin, cyber_defense, marl, robotics)
- **Risk rules applied:** 7 (too_template_like, too_extreme, unnatural_wording, not_scientific_claim, contradiction_too_mechanical, strong_action_too_forced, mild_strong_boundary_unclear)

---

## 2. Headline risk distribution

### Claim-level risk

| Risk level | Count | Rate |
| --- | --- | --- |
| High | 0 | 0.0% |
| Medium | 155 | 34.9% |
| Low | 289 | 65.1% |

### Group-level risk

| Risk level | Count | Rate |
| --- | --- | --- |
| High | 0 | 0.0% |
| Medium | 71 | 64.0% |
| Low | 40 | 36.0% |

---

## 3. Per-label realism risk

| Label | N | High | Medium | Low | High rate | Mean risk score (0-5) |
| --- | --- | --- | --- | --- | --- | --- |
| supported | 111 | 0 | 8 | 103 | 0.0% | 1.06 |
| mild_scope_overclaim | 111 | 0 | 43 | 68 | 0.0% | 1.39 |
| strong_action_overclaim | 111 | 0 | 44 | 67 | 0.0% | 1.32 |
| contradiction_candidate | 111 | 0 | 60 | 51 | 0.0% | 1.42 |

---

## 4. Specific risk type rates

### strong_action_too_forced

- **Count:** 1 / 111 strong_action_overclaim claims
- **Rate:** 0.9%

### contradiction_too_mechanical

- **Count:** 58 / 111 contradiction_candidate claims
- **Rate:** 52.3%

### group_template_risk (template_similarity_score > 0.6)

- **Count:** 85 / 111 groups
- **Rate:** 76.6%

### All risk type distribution (a claim may trigger multiple)

| Risk type | Count |
| --- | --- |
| too_template_like | 412 |
| mild_strong_boundary_unclear | 74 |
| contradiction_too_mechanical | 58 |
| too_extreme | 31 |
| unnatural_wording | 1 |
| strong_action_too_forced | 1 |

---

## 5. Low-risk claims usable as paper examples

- **Total low-risk claims:** 289
- **Per label:**
  - supported: 103
  - mild_scope_overclaim: 68
  - strong_action_overclaim: 67
  - contradiction_candidate: 51

These low-risk claims are recommended as candidates for paper illustrative examples (still subject to gold validation).

---

## 6. High-risk claims recommended for gold realism check

- **Total high-risk claims:** 0
- **Per label:**
  - supported: 0
  - mild_scope_overclaim: 0
  - strong_action_overclaim: 0
  - contradiction_candidate: 0

These high-risk claims should be prioritized in the gold realism annotation (Layer 2 of the gold protocol), to confirm whether the heuristic risk translates to human-judged unrealistic claims.

---

## 7. Recommended action distribution

| Action | Count |
| --- | --- |
| keep | 289 |
| review | 147 |
| prioritize_gold_realism | 8 |

- **keep:** low risk, suitable as-is (still silver, not gold).
- **review:** medium risk, author should manually inspect before paper use.
- **prioritize_gold_realism:** high risk, must be prioritized in gold realism annotation.
- **exclude_from_paper_examples:** high risk with extreme/templated wording, must NOT be used as illustrative example in paper.

---

## 8. Domain risk distribution

| Domain | N | High risk | High risk rate |
| --- | --- | --- | --- |
| autonomous_driving | 140 | 0 | 0.0% |
| cyber_defense | 64 | 0 | 0.0% |
| digital_twin | 68 | 0 | 0.0% |
| robotics | 36 | 0 | 0.0% |
| marl | 52 | 0 | 0.0% |
| policy_simulation | 84 | 0 | 0.0% |

---

## 9. Risk rules summary

| # | Rule | Scope | Heuristic |
| --- | --- | --- | --- |
| 1 | too_template_like | all claims | Mean pairwise content-token Jaccard > 0.6 within group |
| 2 | too_extreme | all claims | Contains extreme words (always, guarantee, fully, completely, solve, replace, eliminate, proves, deployment-ready, etc.) |
| 3 | unnatural_wording | all claims | Matches mechanical phrasing patterns OR abnormal length (<6 or >70 words) |
| 4 | not_scientific_claim | all claims | Matches slogan/policy/marketing patterns (should be deployed, we recommend, game-changer, revolutionize, etc.) |
| 5 | contradiction_too_mechanical | contradiction_candidate only | High token similarity to supported claim (>0.7) OR (>0.5 + negation cue) |
| 6 | strong_action_too_forced | strong_action_overclaim only | Strong cues (deployment/safety/policy/generalization) in claim but absent in evidence, OR 3+ strong cues |
| 7 | mild_strong_boundary_unclear | mild & strong only | Mild-strong token Jaccard > 0.75 OR (token diff <=3 AND sim > 0.5) |

---

## 10. Prohibitions enforced

- No original data modification — PASS (input CSV read-only; output is new files only).
- No gold annotation — PASS (all risk scores are heuristic, no human label applied).
- No API calls — PASS (regex/token rules only, no LLM/API).
- No model training — PASS (no ML models trained).
- No paper modification — PASS (V3.12/V3.13/V3.14 papers untouched).
- No realism-audit-as-human-gold — PASS (clearly labelled 'automatic, author-side realism risk audit').
- No sample deletion — PASS (all 444 claims retained in audit queue).

---

## 11. Limitations

1. **Heuristic rules.** All 7 risk rules are regex/token-based heuristics. They will miss subtle unrealistic phrasing and may false-flag stylometrically dense but realistic claims. Human gold validation is required to calibrate.
2. **No semantic understanding.** The rules cannot detect semantically absurd claims that use natural phrasing. A claim like 'This benchmark result proves that autonomous driving is solved' would be flagged by 'too_extreme' (proves, solved) but a more subtle semantic overclaim might be missed.
3. **Token Jaccard is coarse.** Template similarity uses content-token Jaccard, which does not capture syntactic structure. Two claims with the same tokens in different order would score 1.0 similarity, but might be genuinely different.
4. **Non-scientific-claim patterns are English-centric.** The patterns target English slogan/marketing phrasing; claims in other languages or domain-specific jargon may be mis-flagged.
5. **Strong-forced detection is conservative.** A claim is flagged only if strong cues appear in claim but NOT in evidence. Claims where evidence briefly mentions deployment but the claim heavily extrapolates may not be flagged.
6. **All scores are silver-stage.** Gold adjudication (gold_pilot_protocol_freeze_v1, PROTOCOL FROZEN, annotation NOT begun) is required to validate the heuristic risk against human judgment.