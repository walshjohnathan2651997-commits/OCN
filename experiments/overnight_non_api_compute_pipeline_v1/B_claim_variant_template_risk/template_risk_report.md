# Claim Variant Similarity + Template Risk Report

**Date:** 2026-07-05
**Source:** strict_silver_max_candidates_v1.csv (111 groups × 4 claims)

## 1. Overall template risk

| Tier | Count | % |
|---|---|---|
| High (>0.6 cosine) | 76 | 68.5% |
| Medium (0.3-0.6) | 34 | 30.6% |
| Low (<0.3) | 1 | 0.9% |

Mean template_risk_score across 111 groups: 0.6607

## 2. By-label similarity (pairs where label_i == X)

| Label | Mean TF-IDF cosine | Mean Jaccard | Mean SeqRatio | n_pairs |
|---|---|---|---|---|
| mild_scope_overclaim | 0.7316 | 0.7816 | 0.8822 | 222 |
| strong_action_overclaim | 0.6832 | 0.7273 | 0.8504 | 111 |
| contradiction_candidate | 0.6059 | 0.659 | 0.8106 | 333 |

## 3. Inter-label similarity (between different labels in same group)

| Pair | Mean TF-IDF cosine | Mean Jaccard |
|---|---|---|
| mild_scope_overclaim__supported | 0.8195 | 0.8485 |
| mild_scope_overclaim__strong_action_overclaim | 0.6437 | 0.7147 |
| strong_action_overclaim__supported | 0.6832 | 0.7273 |
| contradiction_candidate__supported | 0.6911 | 0.7239 |
| contradiction_candidate__mild_scope_overclaim | 0.5916 | 0.6501 |
| contradiction_candidate__strong_action_overclaim | 0.5351 | 0.6029 |

## 4. Top 10 high-risk groups (highest template_risk_score)

| group_id | domain | template_risk_score | tier |
|---|---|---|---|
| SBV2-ALL92-G043 | autonomous_driving | 0.9557 | high |
| SBV2-ALL92-G040 | autonomous_driving | 0.9415 | high |
| SBV2-ALL92-G055 | autonomous_driving | 0.9123 | high |
| SBV2-ALL92-G035 | autonomous_driving | 0.8902 | high |
| SBV2-ALL92-G233 | policy_simulation | 0.8689 | high |
| SBV2-ALL92-G086 | cyber_defense | 0.8642 | high |
| SBV2-ALL92-G062 | autonomous_driving | 0.8626 | high |
| SBV2-ALL92-G226 | policy_simulation | 0.8609 | high |
| SBV2-ALL92-G259 | policy_simulation | 0.8592 | high |
| SBV2-ALL92-G111 | digital_twin | 0.8561 | high |

## 5. Interpretation

High template_risk_score means the four claim variants in a group are lexically very similar — they share most words and differ only in strength markers. This is **expected** for SimClaim's controlled counterfactual design (same evidence, four generated variants differing in claim strength).

However, high template risk has two implications:
1. **Claim-only classifiers may exploit template patterns** rather than learning genuine evidence-sufficiency reasoning. The paper must report claim-only baseline performance to bound this leakage.
2. **Realism is limited**: real scientific claims do not come in such tightly templated quartets. SimClaim is a diagnostic set, not a naturalistic corpus.

## 6. Recommendations

- Report template_risk_score distribution in the paper Data section.
- Acknowledge that high template overlap is a deliberate design choice for diagnostic separability, not a defect.
- Ensure paper illustrative examples draw from low-template-risk groups where possible.
