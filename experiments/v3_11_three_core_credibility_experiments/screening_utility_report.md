# Screening Utility Test

**Type: Non-gold robustness analysis.** Does not replace gold adjudication. Strengthens the silver-stage RELATIVE pattern only.

**Method:** R4 positioned as a high-recall screening layer for strong_action_overclaim. Binary screening at frozen R4 prediction. Budget curve approximated by class-priority ranking (strong > contra > mild > supp) due to absence of continuous R4 scores.

## Binary Screening (frozen threshold, matched-100)

| Metric | Value |
|---|---|
| Total samples | 100 |
| True strong_action | 25 |
| R4 predicted strong | 35 |
| TP | 9 |
| FP | 26 |
| FN | 16 |
| Precision | 0.2571 |
| Recall | 0.3600 |
| Positive-F1 | 0.3000 |
| FP/TP ratio | 2.89 |
| Review burden | 35.0% |
| R4 captures LLM-missed | 8 |

### R4 Predicted Strong, by Original Silver Class (TP + FP combined)

This table breaks down all 35 R4-predicted-strong samples by their silver label. The strong_action_overclaim row (9) is TP; the other rows are FP.

| Silver class | R4 predicted strong | Role |
|---|---|---|
| supported | 12 | FP |
| mild_scope_overclaim | 13 | FP |
| strong_action_overclaim | 9 | TP |
| contradiction_candidate | 1 | FP |

### Actual False Positive by Silver Class (FP only, excludes TP)

This table is the true FP breakdown — R4 predicted strong but the silver label is not strong_action. The strong_action_overclaim row is excluded because those are TP, not FP.

| Silver class | R4 FP count |
|---|---|
| supported | 12 |
| mild_scope_overclaim | 13 |
| contradiction_candidate | 1 |
| **Total FP** | **26** |

## Recall at Review Budget (matched-100)

| Budget | n_reviewed | Recall | Precision |
|---|---|---|---|
| 10% | 10 | 0.0800 | 0.2000 |
| 20% | 20 | 0.0800 | 0.1000 |
| 30% | 30 | 0.2400 | 0.2000 |
| 40% | 40 | 0.3600 | 0.2571 |
| 50% | 50 | 0.3600 | 0.2571 |
| 60% | 60 | 0.3600 | 0.2571 |
| 70% | 70 | 0.3600 | 0.2571 |
| 80% | 80 | 0.3600 | 0.2571 |
| 90% | 90 | 0.3600 | 0.2571 |
| 100% | 100 | 0.3600 | 0.2571 |

## Key Findings

1. **FP/TP ratio = 2.89** — below pre-registered threshold of 10. Screening viable.
2. **R4 captures 8 strong_action cases that LLM missed** — this is the core screening value proposition.
3. **Review burden = 35.0%** — a human reviewer needs to check 35 out of 100 samples.
4. **Recall = 0.3600** — R4 catches 9/25 true strong_action cases.
5. **R4 is a screening layer, not an autonomous annotator** — the 26 false positives require human adjudication, which is exactly the gold validation protocol in §VII.
6. **Non-gold caveat:** All numbers are silver-stage. The 9 TP and 26 FP counts depend on silver labels; gold adjudication may shift these counts. This analysis validates the screening *structure* (FP/TP ratio, LLM-missed-R4-captured), not the absolute TP/FP counts.
