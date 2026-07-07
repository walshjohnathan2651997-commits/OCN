# Format-Shift R4 Evaluation Blocked Report (V3.17)

**Generated:** 2026-07-07
**Experiment:** `format_shift_ablation_v1`
**Status:** BLOCKED
**Reason:** `sklearn_version_mismatch`

## 1. Diagnosis

| Field | Value |
|---|---|
| Required sklearn | >=1.5.0 (frozen R4 artifacts use `LogisticRegression` API changed after 1.4.x) |
| Current sklearn | 1.4.1.post1 |
| Frozen artifact path | `experiments/r4_minimal_recovery_v1/artifacts/` |
| Exact error | `AttributeError: LogisticRegression object has no attribute 'multi_class'` |

**Root cause:** Frozen R4 classifiers (`clf_contra.pkl`, `clf_strong.pkl`, `clf_svm.pkl`) were pickled with a scikit-learn version where `LogisticRegression.multi_class` existed. The current environment (1.4.1) cannot unpickle and call `predict_proba` on these artifacts because the attribute was removed/renamed in newer sklearn releases.

## 2. Why No-Network Prevents Fix

Upgrading scikit-learn requires `pip install scikit-learn --upgrade`, which downloads wheels from PyPI. The V3.17 confidential pipeline enforces `no_network` and `no_api` hard boundaries. No cached wheels for newer scikit-learn versions are available in the local pip cache.

**This is a permanent limitation of the current environment, not a code defect.**

## 3. Completed Artifacts

The following steps completed successfully before the R4 prediction block:

| Step | Status | Output |
|---|---|---|
| Variant construction | success | 8 variants x 444 candidates = 3552 rows |
| NLI feature extraction | success | shape [3552, 7] |
| `format_shift_inputs.csv` | exists | 3552 rows (internal, contains evidence text) |
| `format_shift_inputs_redacted.csv` | exists | redacted, safe for release |
| `format_shift_summary.json` | partial | variant construction OK, R4 metrics blocked |
| `leakage_guard_report.json` | exists | documents no forbidden fields used |

**Variants constructed:**
1. `oracle_clean` (diagnostic upper-bound)
2. `oracle_plus_metadata`
3. `oracle_lengthened`
4. `oracle_plus_metadata_lengthened`
5. `raw_bm25_top1_chunk`
6. `cleaned_bm25_top1_chunk`
7. `canonicalized_best_sentence_top5` (production-like selector)
8. `canonicalized_three_sentence_window_top5`

## 4. Missing Artifacts

| Artifact | Reason |
|---|---|
| `format_shift_metrics.csv` | R4 prediction blocked — cannot compute p_contra/p_strong/p_svm without frozen classifiers |
| `format_shift_summary.json` (complete) | Cannot include R4 metrics |

## 5. Safe Paper Wording

**Use this wording:**

> Format-shift variant construction and feature extraction completed, but frozen R4 prediction was blocked by environment compatibility (scikit-learn version mismatch). We do not report unsupported R4 format-shift metrics.

**Do NOT use these wordings:**

- Full R4 format-shift evaluation completed.
- Canonicalized format-shift metrics are validated.
- R4 format-shift result is final.

## 6. Final Gate Impact

- **Check ID:** 3.4
- **Current status:** BLOCKED
- **Acceptable as documented limitation:** Yes
- **Rationale:** Variant inputs and NLI features are available for manual analysis. R4 metrics cannot be computed without upgrading sklearn, which requires network access that violates the `no_network` boundary.

## 7. Hard Boundaries Enforced

- `no_network`: true (no pip install)
- `no_api`: true
- `no_training`: true
- No fake `format_shift_metrics.csv` generated
- No silver relabeled as gold
- No human audit results fabricated
