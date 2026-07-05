# Scalar Score Distribution and Overlap Report (Score Collapse Analysis)

**Task:** V3.15 Task 4/5 §4 — Score collapse analysis for scalar overstatement score.
**Date:** 2026-07-05
**Status:** Reanalysis of existing scalar scores. NOT new experiments. NOT gold. NOT API.

## 1. Per-class score distribution (rule_scalar_score, 0-3)

| Silver label | N | Mean | Median | Std | Min | Max | Q25 | Q75 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported | 111 | 1.5586 | 2.0 | 1.1831 | 0.0 | 3.0 | 0.0 | 3.0 |
| mild_scope_overclaim | 111 | 1.5676 | 2.0 | 1.1826 | 0.0 | 3.0 | 0.0 | 3.0 |
| strong_action_overclaim | 111 | 1.5946 | 2.0 | 1.1498 | 0.0 | 3.0 | 1.0 | 3.0 |
| contradiction_candidate | 111 | 1.6847 | 2.0 | 1.2079 | 0.0 | 3.0 | 0.0 | 3.0 |

## 2. Score-count cross table

| Silver label | Score=0 | Score=1 | Score=2 | Score=3 |
| --- | --- | --- | --- | --- |
| supported | 31 (27.9%) | 20 (18.0%) | 27 (24.3%) | 33 (29.7%) |
| mild_scope_overclaim | 31 (27.9%) | 19 (17.1%) | 28 (25.2%) | 33 (29.7%) |
| strong_action_overclaim | 27 (24.3%) | 24 (21.6%) | 27 (24.3%) | 33 (29.7%) |
| contradiction_candidate | 29 (26.1%) | 17 (15.3%) | 25 (22.5%) | 40 (36.0%) |

## 3. Score collapse indicators

### 3.1 Mild/strong overlap at strong median (score >= 2.0)

- Mild claims at or above strong median: **55.0%**
- Strong claims at or above strong median: **54.1%**
- **Overlap ratio (mild / strong):** 1.02

If overlap ratio is close to 1.0, scalar score cannot distinguish mild from strong — **score collapse on the mild/strong boundary.**

### 3.2 Contradiction vs strong mixing (score >= 2.0)

- Contradiction claims at or above strong median: **58.6%**
- Strong claims at or above strong median: **54.1%**

If contradiction rate ≈ strong rate, scalar score treats contradiction and strong_action identically — **score collapse across relation types.**

### 3.3 Supported false-positive (supported with high score)

- Supported claims with score >= 2: **54.1%**
- Supported claims with score >= 3: **29.7%**

If supported claims frequently get high overstatement scores, the scalar score is conflating 'paraphrase of strong evidence' with 'overclaim' — **score collapse on supported vs overclaim.**

### 3.4 Strong_action score variance

- Strong_action score variance: **1.3221**
- Overall score variance: **1.4005**
- Ratio (strong / overall): 0.9440

If strong_action variance is similar to overall variance, the scalar score does not concentrate differently for strong_action — **no discriminative signal.**

## 4. Verdict

**SCORE COLLAPSE CONFIRMED.** 4 indicators detected:
- mild/strong overlap ratio = 1.02 (mild and strong scores nearly identical)
- contradiction vs strong score overlap = 0.05 (within 15pp)
- supported with high score = 54.1% (supported frequently mis-scored as overclaim)
- strong variance / overall variance = 0.94 (strong does not separate from overall)

## 5. Prohibitions enforced

- No API / no training / no R4 threshold modification / no data modification / no proxy-as-official / no gold — ALL PASS.