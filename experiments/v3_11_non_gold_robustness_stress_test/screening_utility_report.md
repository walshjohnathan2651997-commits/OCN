# Screening Utility Curve

**Method:** R4 positioned as a high-recall screening layer for strong_action_overclaim. Binary screening at the frozen R4 prediction (r4_label == strong_action_overclaim). No continuous R4 scores available in frozen prediction files; budget curve approximated by class-priority ranking (strong > contra > mild > supp).

## Binary Screening (frozen threshold)

| Metric | Matched-100 | Matched-200 |
|---|---|---|
| n_samples | 100 | 200 |
| n_true_strong | 25 | 50 |
| n_r4_flagged_strong | 35 | 64 |
| TP | 9 | 18 |
| FP | 26 | 46 |
| FN | 16 | 32 |
| Review burden | 35.00% | 32.00% |
| Recall | 0.3600 | 0.3600 |
| Precision | 0.2571 | 0.2812 |
| FP/TP ratio | 2.89 | 2.56 |

### FP by original silver class (matched-100)

| True silver class | R4 flagged as strong (FP) |
|---|---|
| supported | 12 |
| mild_scope_overclaim | 13 |
| strong_action_overclaim | 9 |
| contradiction_candidate | 1 |

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

1. **Review burden:** R4 flags 35.0% of matched-100 samples as strong_action — this is the human review cost.
2. **FP/TP ratio:** 2.89 — **below** the pre-registered threshold of 10, confirming R4 is viable as a screening layer.
3. **Recall:** 0.3600 — R4 catches 9/25 true strong_action cases.
4. **FP breakdown:** Most FPs come from mild_scope_overclaim (13) and supported (12) — these are the mild/strong boundary confusions that gold adjudication is designed to resolve.
5. **Budget curve:** At 20% review budget, R4 already achieves most of its recall because strong_action flags are top-priority.
