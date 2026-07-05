# External Gold Test Protocol

> **Scope**: This is a PROTOCOL only. No public data is downloaded or evaluated 
> in this task. The protocol specifies what to do when downstream execution is approved.

> **Hard cap**: Each dataset samples up to 300 claim-evidence pairs. 
> No full-dataset runs. No model retraining on public data.

## Sampling Rules (all datasets)

1. Drop samples with empty evidence text.
2. Drop samples where claim-evidence pair is incomplete.
3. Balance labels as evenly as possible (up to 100 per class).
4. Preserve `source_id` / `dataset_id` for traceability.
5. Record original label and mapped V3 external label side-by-side.
6. Save the sampling seed for reproducibility.

## Task E1: support_vs_contradiction

- **Samples**: Only `supported` vs `contradiction_candidate` (drop `unsupported_or_insufficient`).
- **Metrics**: accuracy, macro-F1, supported F1, contradiction F1.
- **Purpose**: Test whether V3/R4 contradiction detection transfers to external data.
- **Reporting**: Separate table, NOT merged with SimClaim main results.

## Task E2: support_vs_non_support

- **Samples**: `supported` vs (`contradiction_candidate` + `unsupported_or_insufficient`).
- **Metrics**: macro-F1, positive-F1 for non-support, calibration (Brier score) if feasible.
- **Purpose**: Test support-vs-rest generalization.

## Task E3: evidence_sensitivity (VitaminC only)

- **Samples**: 100 claims, each paired with:
  - correct evidence (supports gold label)
  - wrong evidence (retrieved for a different claim, contrastive)
  - empty evidence (blank/placeholder string)
- **Metrics**:
  - `correct_vs_wrong_delta`: accuracy(correct) − accuracy(wrong)
  - `correct_vs_empty_delta`: accuracy(correct) − accuracy(empty)
  - `label_flip_rate`: fraction of claims whose predicted label changes across evidence variants
  - `evidence_sensitivity_rate`: fraction of claims where model uses evidence (flip on wrong/empty)
- **Purpose**: Verify R4 is evidence-aware, not just claim-text classifier.

## Task E4: transfer sanity

- **Samples**: All sampled pairs from E1 (binary).
- **Method**: Apply V3/R4 feature pipeline (NLI + action-gap + routing) to public data.
- **If labels incompatible**: Fall back to binary support-vs-non-support mapping.
- **Metric**: Compare R4 vs B1 (NLI-only) vs B3b (TF-IDF) on external data.
- **Pass criterion**: R4 should not collapse (macro-F1 > random baseline 0.50) on at least SciFact.

## Execution Order (recommended)

1. SciFact E1 + E2 (primary scientific external test)
2. VitaminC E3 (evidence sensitivity)
3. PubHealth E2 (health-domain sanity)
4. AVeriTeC E2 (complex fact-check sanity)
5. FEVER E1 (optional, general knowledge)

## Reporting Constraints

- Public results MUST be in a separate table from SimClaim main results.
- Table caption must say: "External sanity check on public gold datasets; labels are support/refute/NEI and do not include action-overclaim."
- Must NOT claim public results validate `strong_action_overclaim` detection.
