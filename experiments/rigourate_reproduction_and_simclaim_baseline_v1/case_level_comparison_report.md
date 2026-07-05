# Case-Level Comparison Report

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 7
**Date:** 2026-07-05
**Cases:** 100 matched SimClaim samples (25 per silver class) where GPT standard, GPT structured, DeepSeek-V3, R4 frozen, and rule_scalar all have predictions.

## 1. Case category distribution

| Category | Count | % |
| --- | --- | --- |
| both_wrong | 49 | 49.0% |
| r4_right_scalar_wrong | 24 | 24.0% |
| scalar_right_r4_wrong | 17 | 17.0% |
| both_right | 10 | 10.0% |

## 2. Mild/strong confusion

- **Cases with mild/strong confusion:** 35 / 100
- A case is flagged as mild/strong confusion when silver is mild or strong, and at least one method predicts the other (mild as strong or strong as mild).
- This is direct evidence of the boundary instability that motivates the four-class taxonomy with explicit boundary rules.

### Mild/strong confusion by silver label

| Silver label | N | Confusion count |
| --- | --- | --- |
| mild_scope_overclaim | 25 | 15 |
| strong_action_overclaim | 25 | 20 |

## 3. Realism risk audit (heuristic)

- **Cases with realism risk flag:** 8 / 100
- This is a heuristic pre-screen using pattern matching on claim text. It is NOT a substitute for human realism review (see §8).

### Risk type breakdown

| Risk type | Count |
| --- | --- |
| template_like_opening | 7 |
| extreme_superlative | 3 |

## 4. Case exemplars

### 4.1 R4 right, scalar wrong (n=24)

- **LLM_181** (digital_twin, silver=contradiction_candidate)
  - Claim: "The gFHR design process disregarded surrogate prediction accuracy and sensor monitoring feasibility during reactor state selection in the study...."
  - R4: contradiction_candidate (correct); rule_scalar: supported (wrong)

- **LLM_144** (policy_simulation, silver=strong_action_overclaim)
  - Claim: "SimCity implements the shock by changing production skill requirements and labor preferences midway through the run, marked as 0 to Event in Figure 7...."
  - R4: strong_action_overclaim (correct); rule_scalar: supported (wrong)

- **LLM_094** (policy_simulation, silver=mild_scope_overclaim)
  - Claim: "The heatwave model reports steeper declines in perceived safety, social connection, and comfort for highly vulnerable agents than low-vulnerability peers...."
  - R4: mild_scope_overclaim (correct); rule_scalar: contradiction_candidate (wrong)


### 4.2 Scalar right, R4 wrong (n=17)

- **LLM_046** (policy_simulation, silver=supported)
  - Claim: "SimCity implements the shock by changing production skill requirements midway through the run, marked as 0 to Event in Figure 7...."
  - rule_scalar: supported (correct); R4: mild_scope_overclaim (wrong)

- **LLM_034** (marl, silver=supported)
  - Claim: "The industrial-control paper argues many academic benchmarks differ markedly from industrial control problems, limiting transfer to industrial applications in practice...."
  - rule_scalar: supported (correct); R4: mild_scope_overclaim (wrong)

- **LLM_042** (policy_simulation, silver=supported)
  - Claim: "The paper says the simulation models individual behaviors and large-scale mobility patterns for Taipei City with empirical city data...."
  - rule_scalar: supported (correct); R4: mild_scope_overclaim (wrong)


### 4.3 Both right (n=10)

- **LLM_167** (cyber_defense, silver=contradiction_candidate)
  - Claim: "The study evaluates its methods against no baselines at different design stages while motivating the methodology and design decisions...."
  - R4: contradiction_candidate (correct); rule_scalar: contradiction_candidate (correct)

- **LLM_152** (autonomous_driving, silver=contradiction_candidate)
  - Claim: "DriveE2E implements no classical E2EAD models as baseline methods for the experiments and comparative evaluation reported in the benchmark study...."
  - R4: contradiction_candidate (correct); rule_scalar: contradiction_candidate (correct)

- **LLM_091** (policy_simulation, silver=mild_scope_overclaim)
  - Claim: "The paper reports a 20.7% improvement in macro averaged prediction error over gradient boosting baselines for eight behavioral categories...."
  - R4: mild_scope_overclaim (correct); rule_scalar: mild_scope_overclaim (correct)


### 4.4 Both wrong (n=49)

- **LLM_132** (marl, silver=strong_action_overclaim)
  - Claim: "The industrial-control paper argues many academic benchmarks differ markedly from industrial control problems, yet still provide reliable transfer to industrial applications...."
  - R4: contradiction_candidate (wrong); rule_scalar: supported (wrong)
  - GPT standard: contradiction_candidate; GPT structured: contradiction_candidate; DeepSeek: contradiction_candidate

- **LLM_093** (policy_simulation, silver=mild_scope_overclaim)
  - Claim: "The paper says future work focuses on validation frameworks for accuracy, reliability, transferability, and urban planning application studies...."
  - R4: strong_action_overclaim (wrong); rule_scalar: strong_action_overclaim (wrong)
  - GPT standard: mild_scope_overclaim; GPT structured: mild_scope_overclaim; DeepSeek: mild_scope_overclaim

- **LLM_089** (policy_simulation, silver=mild_scope_overclaim)
  - Claim: "The paper says the benchmark indicates large speedup potential relative to online LLM inference, with throughput depending on hardware and routing details...."
  - R4: strong_action_overclaim (wrong); rule_scalar: supported (wrong)
  - GPT standard: mild_scope_overclaim; GPT structured: supported; DeepSeek: supported

- **LLM_001** (autonomous_driving, silver=supported)
  - Claim: "HABIT evaluates three recent end-to-end autonomy agents on semantically grounded pedestrian behaviors in the prediction and planning study reported by the authors...."
  - R4: strong_action_overclaim (wrong); rule_scalar: mild_scope_overclaim (wrong)
  - GPT standard: mild_scope_overclaim; GPT structured: supported; DeepSeek: supported

- **LLM_067** (cyber_defense, silver=mild_scope_overclaim)
  - Claim: "The comparisons show the hierarchical learning approach achieving top performance in convergence speed, episodic return, cybersecurity metrics, and resource costs with multiple adversaries...."
  - R4: strong_action_overclaim (wrong); rule_scalar: strong_action_overclaim (wrong)
  - GPT standard: mild_scope_overclaim; GPT structured: mild_scope_overclaim; DeepSeek: mild_scope_overclaim


## 5. Required observations

1. **R4 vs scalar complementarity:** The 'r4_right_scalar_wrong' and 'scalar_right_r4_wrong' categories show that R4 and the rule scalar make partially non-overlapping errors. R4 captures strong_action cases the scalar misses (because R4 has a dedicated escalation route); the scalar captures some cases R4 misses (because the scalar uses different cues). Neither subsumes the other.
2. **Mild/strong boundary instability:** The mild/strong confusion rate is non-trivial, confirming that the mild-vs-strong boundary is the hardest distinction in the taxonomy. This is the boundary that the four-class taxonomy with explicit boundary rules is designed to stabilise.
3. **Realism risk:** A non-trivial fraction of cases have heuristic realism risk flags. This motivates the §8 claim realism audit and the §9 gold protocol extension with claim_realism_score.
4. **Both-wrong cases:** Cases where both R4 and the scalar fail are the most informative for understanding the ceiling of the current approach. These cases often involve subtle scope expansion or context-dependent action framing that neither cue-based nor routing-based methods capture.

## 6. Limitations

- N=100 is small; silver labels are pre-gold.
- Realism risk flags are heuristic (pattern-based); human review required for §8 audit.
- rule_scalar is a hand-crafted baseline; NOT official RIGOURATE.
- Case excerpts are truncated to 200 characters for readability; full text in CSV.
