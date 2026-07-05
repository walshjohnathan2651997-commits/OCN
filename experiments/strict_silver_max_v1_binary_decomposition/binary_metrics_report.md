# Binary Decomposition Experiment Report

TF-IDF + LogisticRegression on strict_silver_max_v1.

Silver labels (AI-preannotated). NOT human-audited, NOT gold.


## Results: macro-F1

| task | claim-only | evidence-only | claim+evidence | ce-co delta |
|---|---|---|---|---|
| issue_binary | 0.5273 | 0.4286 | 0.5123 | -0.015 |
| escalation_binary | 0.4975 | 0.3333 | 0.5416 | +0.0441 |
| contradiction_binary | 0.5372 | 0.2 | 0.5625 | +0.0253 |
| supported_vs_rest | 0.5273 | 0.4286 | 0.5123 | -0.015 |
| contradiction_vs_rest | 0.5372 | 0.2 | 0.5625 | +0.0253 |

## Results: accuracy

| task | claim-only | evidence-only | claim+evidence |
|---|---|---|---|
| issue_binary | 0.6806 | 0.75 | 0.6944 |
| escalation_binary | 0.5139 | 0.5 | 0.5417 |
| contradiction_binary | 0.5694 | 0.25 | 0.6111 |
| supported_vs_rest | 0.6806 | 0.75 | 0.6944 |
| contradiction_vs_rest | 0.5694 | 0.25 | 0.6111 |

## Positive-class F1

| task | positive | claim-only | evidence-only | claim+evidence |
|---|---|---|---|---|
| issue_binary | issue | 0.7965 | 0.8571 | 0.8103 |
| escalation_binary | escalation | 0.4068 | 0.6667 | 0.5479 |
| contradiction_binary | contradiction | 0.4151 | 0.4 | 0.4167 |
| supported_vs_rest | supported | 0.2581 | 0.0 | 0.2143 |
| contradiction_vs_rest | contradiction | 0.4151 | 0.4 | 0.4167 |

## Confusion matrices

### issue_binary (claim+evidence)

| actual \ pred | issue | no_issue |
|---|---|---|
| issue | 47 | 7 |
| no_issue | 15 | 3 |

### escalation_binary (claim+evidence)

| actual \ pred | escalation | non_escalation |
|---|---|---|
| escalation | 20 | 16 |
| non_escalation | 17 | 19 |

### contradiction_binary (claim+evidence)

| actual \ pred | contradiction | not_contradiction |
|---|---|---|
| contradiction | 10 | 8 |
| not_contradiction | 20 | 34 |

### supported_vs_rest (claim+evidence)

| actual \ pred | non_supported | supported |
|---|---|---|
| non_supported | 47 | 7 |
| supported | 15 | 3 |

### contradiction_vs_rest (claim+evidence)

| actual \ pred | contradiction | non_contradiction |
|---|---|---|
| contradiction | 10 | 8 |
| non_contradiction | 20 | 34 |

## Answers

1. **Most stable task**: contradiction_binary (claim+evidence macro-F1=0.5625)
2. **claim+evidence vs claim-only**: 
   - issue_binary: -0.015
   - escalation_binary: +0.0441
   - contradiction_binary: +0.0253
   - supported_vs_rest: -0.015
   - contradiction_vs_rest: +0.0253
3. **Contradiction claim-only guessability**: contradiction_binary macro-F1=0.5372, contradiction_vs_rest macro-F1=0.5372
4. **Binary vs 4-class**: 4-class claim+evidence macro-F1=0.2592. Best binary: contradiction_binary=0.5625
5. **Hierarchical recommendation**: see conclusion below

## Conclusion

- Best binary task (contradiction_binary: 0.5625) outperforms 4-class (0.2592).
- **Recommend**: switch to hierarchical/binary calibration for pilot.
- Evidence gain max: escalation_binary (delta=+0.0441)
