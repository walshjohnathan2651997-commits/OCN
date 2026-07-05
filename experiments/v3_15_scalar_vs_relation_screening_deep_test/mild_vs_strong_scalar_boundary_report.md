# Mild vs Strong Scalar Boundary Test

**Task:** V3.15 Task 4/5 §2 — Mild vs Strong boundary test for scalar overstatement score.
**Date:** 2026-07-05
**Status:** Reanalysis of existing scalar baseline predictions. NOT new experiments. NOT gold. NOT API.

## 1. Setup

- **Data:** SimClaim 444 candidates, filtered to silver_label in {mild_scope_overclaim, strong_action_overclaim}.
- **N (rule_scalar):** 222 (111 mild + 111 strong).
- **N (llm_scalar):** 100 (subset with non-blocked LLM scalar score).
- **Positive class:** strong_action_overclaim.
- **Score source:** `rigourate_style_scalar_scores.csv`.

## 2. Results

| Variant | N | ROC-AUC | PR-AUC | Best F1 | Best Threshold | Precision@Best | Recall@Best | Recall@P>=0.3 | Recall@P>=0.5 | Confusion@Best |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| rule_scalar_score | 222 | 0.5062 | 0.5016 | 0.6667 | 0.0 | 0.5 | 1.0 | 1.0 | 1.0 | TN=0,FP=111,FN=0,TP=111 |
| llm_scalar_score | 100 | 0.5874 | 0.5931 | 0.6667 | 0.0 | 0.5 | 1.0 | 1.0 | 1.0 | TN=0,FP=50,FN=0,TP=50 |

## 3. Threshold sensitivity

### rule_scalar_score

```
t=0.0:F1=0.667,R=1.000,P=0.500; t=0.5:F1=0.611,R=0.757,P=0.512; t=1.0:F1=0.611,R=0.757,P=0.512; t=1.5:F1=0.517,R=0.540,P=0.496; t=2.0:F1=0.517,R=0.540,P=0.496; t=2.5:F1=0.373,R=0.297,P=0.500; t=3.0:F1=0.373,R=0.297,P=0.500
```

### llm_scalar_score

```
t=0.0:F1=0.667,R=1.000,P=0.500; t=0.5:F1=0.574,R=0.620,P=0.534; t=1.0:F1=0.574,R=0.620,P=0.534; t=1.5:F1=0.328,R=0.200,P=0.909; t=2.0:F1=0.328,R=0.200,P=0.909; t=2.5:F1=0.271,R=0.160,P=0.889; t=3.0:F1=0.271,R=0.160,P=0.889
```

## 4. Verdict

**FAIL.** Rule-based scalar score cannot distinguish mild from strong (ROC-AUC = 0.5062, near random). The score collapses across labels — see §4 score collapse analysis.

## 5. Prohibitions enforced

- No API calls — PASS (only reanalysis of existing predictions).
- No model training — PASS (no new models trained).
- No R4 threshold modification — PASS (R4 frozen).
- No original data modification — PASS (input CSVs read-only).
- No proxy-as-official-RIGOURATE — PASS (labelled 'rule_scalar_score' / 'llm_scalar_score', NOT 'RIGOURATE').
- No gold — PASS (all on silver labels).