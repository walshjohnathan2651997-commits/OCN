# Paper Result Interpretation - CESE-OCN Mixed Framework v2

Generated: 2026-07-03T14:55:28.833302

## 1. Main Method

**CESE-OCN Mixed Framework v2 with R4_conservative_strong router**

The R4 router applies a conservative strategy: contradiction is detected first; strong is predicted only when
`p_strong >= t_strong` AND `p_contra < t_contra_low`; otherwise supported/mild is decided by an SVM margin.
This prevents contradiction->strong errors while improving strong recall.

Frozen at: `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline`
Immutable: true

## 2. What the Results Support

### 2.1 Strong-Action Improvement (Primary Finding)

R4 improves strong-action positive-F1 from **0.2408** to **0.3967** (delta = **+0.1559**).

- Bootstrap 95% CI: **[0.1058, 0.1988]** (does NOT cross 0)
- Positive in **10/10** seeds
- Improvement is primarily from RECALL (+0.2500), not just precision (+0.0693)

This is the strongest claim the paper can make.

### 2.2 No Damage to Contradiction / Escalation

| Metric | Baseline | R4 | Delta |
|---|---|---|---|
| flat4 macro-F1 | 0.3963 | 0.4238 | +0.0275 |
| contradiction positive-F1 | 0.7308 | 0.7296 | -0.0012 |
| escalation macro-F1 | 0.5723 | 0.6143 | +0.042 |

R4 preserves contradiction performance (delta = -0.0012) and improves escalation (+0.042).

### 2.3 Feature Complementarity (Ablation)

The ablation confirms the improvement comes from NLI + action-gap feature combination, not claim-only keywords:
- TF-IDF claim-only: 0.2747 (weak baseline)
- NLI only: 0.3934
- Action-gap only: 0.3648
- NLI + action gap: 0.4209 (best combination)

### 2.4 Mixed Framework Justification

The mixed framework v1 gate confirms:
- mixed_framework_supported: True
- single_model_all_labels_supported: False
- class_specific_reasoning_needed: True

A single flat classifier cannot handle all four labels; relation-specific reasoning is needed.

## 3. What the Results Do NOT Support

### 3.1 Cost-Sensitive cw4.0 Does NOT Replace R4

- Best new method: B_cost_sensitive_cw4.0
- strong_positive_f1: 0.4221 (delta vs R4 = +0.0254)
- Below +0.03 replacement threshold
- CI crosses 0: True
- recommended_use: auxiliary_module

cw4.0 can be reported as a sensitivity analysis showing cost-weighting trends, but NOT as the main method.

### 3.2 No Gold / Human Validation

- All results are on silver-label pilot data
- No human adjudication performed
- No inter-annotator agreement computed
- Cannot claim confirmatory performance

### 3.3 Strong-Action Is NOT Solved

- R4 strong F1 = 0.3967 (moderate)
- supported->strong false positives: 98 cases
- mild->strong false positives: 24 cases
- This is a LIMITATION that must be reported honestly

### 3.4 supported_vs_mild Boundary NOT Solved

- supported/mild boundary F1 ~0.52 (weakest boundary)
- Claim-only features approximate evidence-aware features here
- Additional relation-specific reasoning needed

## 4. Limitations (Must Report)

1. **Silver labels only**: no human gold validation; results are exploratory, not confirmatory
2. **Small dataset**: 444 claims, 111 groups, test ~16 samples/seed
3. **supported/mild ambiguity**: boundary F1 ~0.52, weakest class boundary
4. **strong_action moderate**: F1 = 0.3967, not solved; false positives from supported/mild
5. **No external validation**: no cross-domain or external benchmark comparison
6. **No significance vs strong baselines**: only internal baseline comparison
7. **Counterfactual robustness**: not validated

## 5. Paper Positioning

**Recommended positioning**: mixed evidence calibration framework / relation-specific router / action-overclaim diagnostic

- Frame as a PILOT VALIDATION of a mixed framework, not a final benchmark
- Use cautious language: "on silver-label pilot data", "suggests", "supports", "requires validation on gold adjudicated data"
- Report R4 as the main method with cw4.0 as auxiliary sensitivity analysis
- Explicitly state the supported/mild->strong false positive limitation
- Do NOT claim Q1 readiness; state that 300-500 human-audited pairs are required for high-tier submission

## 6. Q1 Readiness Assessment

- **q1_ready**: false
- **current_level**: pilot_to_mid_tier_ready
- **q1_possible_with_validation**: true (contingent on gold adjudication, data expansion, significance tests, external baselines)
- **biggest_risk**: overclaiming silver-label pilot results as final benchmark performance
- **next_required_action**: expand to 300-500 human-audited pairs; run significance tests; validate on gold

## 7. Tables Summary

- Table 1: Main results (baseline vs R4 vs cw4.0 auxiliary)
- Table 2: Per-class F1 (baseline vs R4)
- Table 3: Router variants comparison (R1-R5, R4 selected)
- Table 4: Strong expert ablation (feature complementarity)
- Table 5: New algorithm sweep vs R4 (no replacement)
- Table 6: Error transition matrix (R4 false positive pattern)
