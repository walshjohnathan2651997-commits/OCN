# Scalar Score / RIGOURATE-style Baseline Sweep Report

**Date:** 2026-07-05
**Source:** rigourate_style_scalar_scores.csv (444 rows), rigourate_style_vs_r4_cases.csv (100 matched)
**Status:** PROXY baseline. NOT official RIGOURATE. SILVER labels only.

## 1. Scalar score availability

- rule_scalar_score: 444/444 valid (integer 0-3)
- llm_scalar_score: 200/444 valid (200 with values; 244 blank)
- nli_scalar_score: all "blocked" (NLI features not in repo)

## 2. AUC summary

| Task | rule_scalar ROC-AUC | llm_scalar ROC-AUC | R4 F1 (matched 100) |
|---|---|---|---|
| supported_vs_overclaim | 0.5136 | 0.8533 | 0.8193 |
| mild_vs_strong | 0.5062 | 0.5874 | 0.383 |
| strong_vs_rest | 0.4971 | 0.5154 | 0.3 |
| contradiction_vs_rest | 0.5277 | 0.9195 | 0.68 |

## 3. Threshold sweep (rule_scalar_score, integer thresholds 0.5-3.5)

See scalar_threshold_sweep.csv for full sweep. Headline finding: rule_scalar_score cannot separate mild from strong (ROC-AUC near chance).

## 4. Verdict

- rule_scalar_score: ROC-AUC near chance on mild_vs_strong (cannot separate the high-risk boundary).
- llm_scalar_score: ROC-AUC weak (<0.70) on mild_vs_strong.
- Scalar compression collapses mild and strong into similar score ranges (score collapse).
- R4 retains advantage on strong_vs_rest F1 (uses structured routing, not scalar threshold).

## 5. Limitations

- Scalar baseline is PROXY (rule-based / LLM-label-derived), NOT official RIGOURATE.
- Official RIGOURATE artifacts unavailable (blocked).
- llm_scalar_score has 244/444 missing values (only 200 valid).
- All results on silver labels (pre-gold).
- R4 comparison is on matched 100, not full 444 (R4 case-level predictions on 444 not available in this pipeline).
