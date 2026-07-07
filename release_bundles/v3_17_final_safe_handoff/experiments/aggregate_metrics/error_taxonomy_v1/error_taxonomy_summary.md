# Error Taxonomy Summary — V3.17 Screening Failures

## Data Disclaimer

> **Controlled silver diagnostic data, NOT natural prevalence.** The candidate pool is a balanced 4-class sample (109 per class, 436 total) generated from SimClaim v2. Error rates and type distributions reflect this controlled setting and must not be interpreted as real-world base rates.

## Overview

- Total candidates: **436**
- False positives (FP): **156**
- False negatives (FN): **32**
- Target candidate groups: **109**
- Error type categories: **9**

FP = predicted `strong_action_overclaim` but true label is not.  FN = true `strong_action_overclaim` but predicted otherwise.

## Error Type Distribution

| Error Type | n_cases | % of errors | FP | FN |
|---|---:|---:|---:|---:|
| retrieval_miss | 5 | 2.7% | 5 | 0 |
| evidence_format_noise | 22 | 11.7% | 13 | 9 |
| weak_selector_overlap | 65 | 34.6% | 59 | 6 |
| contradiction_confusion | 36 | 19.1% | 13 | 23 |
| action_lexicon_shortcut | 31 | 16.5% | 29 | 2 |
| mild_vs_strong_boundary | 73 | 38.8% | 66 | 7 |
| supported_overflag | 62 | 33.0% | 62 | 0 |
| uncertainty_high_entropy | 22 | 11.7% | 12 | 10 |
| group_variant_artifact | 53 | 28.2% | 51 | 2 |

## Top FP Causes (false alarms)

- **mild_vs_strong_boundary** (66 FP cases, 38.8% of all errors)
- **supported_overflag** (62 FP cases, 33.0% of all errors)
- **weak_selector_overlap** (59 FP cases, 34.6% of all errors)

## Top FN Causes (missed strong-action overclaims)

- **contradiction_confusion** (23 FN cases, 19.1% of all errors)
- **uncertainty_high_entropy** (10 FN cases, 11.7% of all errors)
- **evidence_format_noise** (9 FN cases, 11.7% of all errors)

## Implications for Future Work

1. **Retrieval quality**: `retrieval_miss` cases indicate where BM25 top-k fails to surface oracle evidence; neural reranking or query expansion may help.
2. **Evidence canonicalization**: `evidence_format_noise` cases suggest the unsupervised sentence selector sometimes picks overly long, short, or multi-sentence evidence; a length-aware selector may reduce noise.
3. **Calibration**: `uncertainty_high_entropy` and `contradiction_confusion` cases indicate where classifier confidence is misplaced; temperature scaling or ensemble calibration may improve robustness.
4. **Lexical shortcuts**: `action_lexicon_shortcut` cases suggest the model may over-rely on action verbs in claims without verifying evidence support; adversarial lexical pairs (same evidence, different claim wording) are the targeted diagnostic.
5. **Group variant sensitivity**: `group_variant_artifact` cases show where template variants within the same group confuse the classifier; group-aware training or hard-negative mining may help.

## Thresholds Used

- `selector_score < 0.3` → weak_selector_overlap
- `entropy > 0.5` → uncertainty_high_entropy
- `p_contra > 0.3` or `contradiction_nli > 0.3` → contradiction_confusion
- `selected_n_words < 5` or `> 50` → evidence_format_noise
- `selected_rank > 5` → evidence_format_noise
- `n_sentences >= 3` → evidence_format_noise
