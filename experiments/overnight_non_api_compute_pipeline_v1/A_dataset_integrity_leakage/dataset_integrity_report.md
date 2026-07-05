# Dataset Integrity + Leakage Re-Audit Report

**Date:** 2026-07-05
**Source:** strict_silver_max_candidates_v1.csv (444 rows)
**Status:** Re-audit only. No original data modification.

## 1. Basic integrity

| Check | Value |
|---|---|
| Total rows | 444 |
| Total groups | 111 |
| Groups with exactly 4 claims | 111 |
| Groups NOT 4 claims | 0 |
| Labels complete (111 each) | True |
| Label distribution | {'supported': 111, 'mild_scope_overclaim': 111, 'strong_action_overclaim': 111, 'contradiction_candidate': 111} |
| candidate_id duplicates | 0 |
| Missing claim_text | 0 |
| Missing evidence_text | 0 |
| source_trace_complete count | 444 (of 444) |

## 2. Duplicate detection

| Check | Value |
|---|---|
| claim_text_sha256 duplicates | 0 |
| evidence_text_sha256 duplicates | 333 (expected: 4 claims share 1 evidence per group) |
| Cross-group evidence leakage | 0 (evidence SHA appearing in >1 group) |

## 3. Gold field verification (must be empty/false)

| Check | Value | Expected |
|---|---|---|
| human_audited=True count | 0 | 0 (no gold annotation) |
| final_label filled | 0 | 0 |
| gold_label filled | 0 | 0 |

## 4. Cue word leakage

Cue words are label-specific lexical markers. If a cue word appears at much higher rate in its label than other labels, claim-only classifiers can exploit this leakage.

- Total cue word entries analyzed: 45
- High-imbalance cues (imbalance_ratio > 5): see cue_word_leakage_table.csv

## 5. Claim-only TF-IDF separability

| Metric | Value |
|---|---|
| Mean cosine similarity, same-label pairs | 0.0142 |
| Mean cosine similarity, diff-label pairs | 0.0208 |
| Separability gap | -0.0066 |
| Risk rating | low |

Interpretation: gap > 0.05 = high leakage risk (claim text alone is highly predictive of label); 0.02-0.05 = medium; < 0.02 = low.

## 6. Within-group token overlap (template risk)

Mean Jaccard token overlap between claims in the same group: 0.7112

High overlap indicates the four claims in a group are templated (share most words), which is expected for controlled counterfactual design but limits naturalness.

## 7. Group leakage risk

Cross-group evidence leakage count: 0

0 evidence SHA256 hashes appear in more than one group. This may indicate shared evidence spans across groups (acceptable if evidence spans are long and reused intentionally) or data construction artifacts (requires review).

## 8. Overall integrity verdict

- Basic integrity: PASS (444 rows, 111 groups, 4 per group, 4 labels balanced)
- Gold fields: PASS (all empty/false as expected for silver-stage)
- Claim-only TF-IDF risk: low
- Group leakage risk: low
- Template risk (within-group overlap): 0.7112

## 9. Recommendations

1. If claim-only TF-IDF risk is high, the paper must report claim-only baseline and acknowledge lexical leakage.
2. If group leakage is non-zero, investigate whether shared evidence is intentional or a construction artifact.
3. Within-group template overlap is a known design attribute of SimClaim; report it as deliberate diagnostic design, not a defect.
