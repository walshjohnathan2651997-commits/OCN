# Strict Silver Max v1 Experiment Report

**This experiment uses AI-preannotated silver labels.**

**It is NOT human-audited.**

**It is NOT gold.**

**It is NOT final paper-full.**

Results are silver-label pilot results only.


## Split

| split | groups | claims |
|---|---|---|
| train | 77 | 308 |
| dev | 16 | 64 |
| test | 18 | 72 |

## Baseline results (test set)

| config | accuracy | macro-F1 |
|---|---|---|
| claim_only | 0.2778 | 0.2164 |
| evidence_only | 0.25 | 0.1 |
| claim_evidence | 0.2778 | 0.2592 |

**Best (macro-F1): claim_evidence**

**claim+evidence vs claim-only**: acc delta=+0.0, macro-F1 delta=+0.0428


### Per-class F1

| label | claim-only | evidence-only | claim+evidence |
|---|---|---|---|
| contradiction_candidate | 0.4062 | 0.4 | 0.35 |
| mild_scope_overclaim | 0.2308 | 0.0 | 0.2069 |
| strong_action_overclaim | 0.2286 | 0.0 | 0.32 |
| supported | 0.0 | 0.0 | 0.16 |

### Confusion matrices

#### claim_only

| actual \ pred | contradiction_candidate | mild_scope_overclaim | strong_action_overclaim | supported |
|---|---|---|---|---|
| contradiction_candidate | 13 | 1 | 4 | 0 |
| mild_scope_overclaim | 10 | 3 | 4 | 1 |
| strong_action_overclaim | 11 | 3 | 4 | 0 |
| supported | 12 | 1 | 5 | 0 |

#### evidence_only

| actual \ pred | contradiction_candidate | mild_scope_overclaim | strong_action_overclaim | supported |
|---|---|---|---|---|
| contradiction_candidate | 18 | 0 | 0 | 0 |
| mild_scope_overclaim | 18 | 0 | 0 | 0 |
| strong_action_overclaim | 18 | 0 | 0 | 0 |
| supported | 18 | 0 | 0 | 0 |

#### claim_evidence

| actual \ pred | contradiction_candidate | mild_scope_overclaim | strong_action_overclaim | supported |
|---|---|---|---|---|
| contradiction_candidate | 7 | 2 | 8 | 1 |
| mild_scope_overclaim | 5 | 3 | 8 | 2 |
| strong_action_overclaim | 5 | 3 | 8 | 2 |
| supported | 5 | 3 | 8 | 2 |

## Conclusion

- Best baseline (macro-F1): **claim_evidence**
- claim+evidence vs claim-only: acc +0.0, macro-F1 +0.0428
- Results are **silver-label pilot results**, not validated performance.
- More data (308+ train) vs previous pilot (140 train) — compare metrics.
