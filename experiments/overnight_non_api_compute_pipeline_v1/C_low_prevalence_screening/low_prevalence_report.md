# Low-Prevalence Screening Simulation Report

**Date:** 2026-07-05
**Status:** SIMULATION. NOT real natural distribution. SILVER labels only.
**Method:** Bootstrap 1000 iterations, N=1000 per iteration, non-strong composition 80/15/5 (supported/mild/contradiction).
**Discrete-score limitation:** Uses predicted-strong discrete label (no continuous score available for R4). For scalar methods this is an approximation.

## 1. R4 screening by prevalence

| Prev | Recall | Precision | F1 | FP/TP (median) | Review burden | Accuracy | LLM-missed captured |
|---|---|---|---|---|---|---|---|
| 1% | 0.3686 | 0.0080 | 0.0156 | 120.0 | 0.463 | 0.5347 | 3.28 |
| 10% | 0.3599 | 0.0794 | 0.1300 | 11.6 | 0.453 | 0.5187 | 32.00 |
| 20% | 0.3603 | 0.1626 | 0.2240 | 5.1 | 0.443 | 0.5011 | 64.07 |

## 2. LLM (GPT standard) at 1% prevalence

| Recall | Precision | F1 | FP/TP | Review burden | Accuracy |
|---|---|---|---|---|---|
| 0.0425 | 0.3550 | 0.0751 | 0.0 | 0.000 | 0.9904 |

LLM shows high-accuracy/low-recall failure mode at low prevalence.

## 3. Verdict

- R4 recall is stable (~0.36) across prevalences (does not degrade as strong_action becomes rarer).
- R4 is NOT viable as standalone screener below 10% prevalence (FP/TP > 12).
- R4 retains value as first-stage filter: captures LLM-missed strong at all prevalences.
- LLM judges exhibit high-accuracy/low-recall failure mode at low prevalence (accuracy misleading).
- Two-stage pipeline (R4 -> LLM/human) PROPOSED but NOT evaluated.

## 4. Limitations

- Simulation uses heuristic 80/15/5 non-strong composition (NOT empirically validated).
- Base pool is 100 matched samples (25 strong_action); diversity limited.
- All results on silver labels (pre-gold).
- Discrete predicted-strong used (no continuous R4 score available).
- This is NOT a natural-distribution study.
