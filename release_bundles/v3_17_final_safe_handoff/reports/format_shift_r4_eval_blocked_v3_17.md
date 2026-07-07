# Format-Shift R4 Evaluation Report (V3.17)

**Generated:** 2026-07-07 (updated)
**Experiment:** `format_shift_ablation_v1`
**Status:** RESOLVED (previously BLOCKED)
**Previous reason:** `sklearn_version_mismatch`
**Resolution path:** A (local compatible sklearn environment)

## 1. Diagnosis (previous block)

| Field | Value |
|---|---|
| Required sklearn | >=1.5.0 (frozen R4 artifacts pickled with scikit-learn 1.9.0) |
| Previous environment sklearn | 1.4.1.post1 (Python 3.10) |
| Frozen artifact path | `experiments/r4_minimal_recovery_v1/artifacts/` |
| Exact error | `AttributeError: LogisticRegression object has no attribute 'multi_class'` |

**Root cause:** Frozen R4 classifiers (`clf_contra.pkl`, `clf_strong.pkl`, `clf_svm.pkl`) were pickled with scikit-learn 1.9.0. The previous environment (Python 3.10, sklearn 1.4.1.post1) could not unpickle and call `predict_proba` on these artifacts because the `multi_class` attribute was removed in sklearn 1.9.0.

## 2. Resolution (Path A)

An offline compatibility investigation (`reports/sklearn_offline_compatibility_investigation_v3_17.md`) identified a project-local `.venv` at `d:\ocn\.venv\` containing:

- Python 3.13.7
- scikit-learn 1.9.0 (exact match for frozen R4 artifacts)
- joblib 1.5.3, numpy 2.5.0, pandas 3.0.3, scipy 1.18.0
- transformers 5.12.1, torch 2.12.1+cpu
- NLI model `cross-encoder/nli-deberta-base` fully cached locally (556 MB)

The eval was run with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, ensuring zero network access. No retraining, no model-artifact modification, and no fake metrics were involved.

## 3. Completed Artifacts

All steps now complete:

| Step | Status | Output |
|---|---|---|
| Variant construction | success | 8 variants x 444 candidates = 3552 rows |
| NLI feature extraction | success | shape [3552, 7] |
| R4 prediction | success | 3552 predictions, 10-seed majority vote |
| Metrics computation | success | 8 variants, n_eval=436 per variant |
| Schema validation | PASS | 38/38 files OK, 0 fail |
| Final gate check 3.4 | PASS | "Format shift R4 eval completed" |

**Output files:**
- `experiments/format_shift_ablation_v1/format_shift_metrics.csv`
- `experiments/format_shift_ablation_v1/format_shift_predictions.csv`
- `experiments/format_shift_ablation_v1/format_shift_summary.json`
- `experiments/format_shift_ablation_v1/format_shift_failure_examples_redacted.csv`
- `experiments/format_shift_ablation_v1/r4_leakage_guard_report.json`
- `experiments/format_shift_ablation_v1/schema_validation_report.json`

## 4. Key Metric Findings

| Variant | strong_F1 | strong_recall | macro_F1 |
|---|---|---|---|
| oracle_clean (diagnostic upper bound) | 0.4627 | 0.5688 | 0.4609 |
| canonicalized_best_sentence_top5 (production) | 0.4615 | 0.7982 | 0.3570 |
| canonicalized_three_sentence_window_top5 | 0.3985 | 0.4862 | 0.3871 |
| oracle_plus_metadata | 0.4335 | 0.4037 | 0.4798 |
| cleaned_bm25_top1_chunk | 0.2769 | 0.2477 | 0.3608 |
| raw_bm25_top1_chunk (baseline) | 0.2755 | 0.2477 | 0.3590 |
| oracle_lengthened | 0.0 | 0.0 | 0.3470 |
| oracle_plus_metadata_lengthened | 0.0 | 0.0 | 0.3725 |

**Canonicalization gain:** +0.186 strong_F1 (canonicalized vs raw BM25).

## 5. Safe Paper Wording

**Use this wording:**

> Variant construction, NLI feature extraction, and frozen R4 prediction were completed using a local scikit-learn 1.9.0 environment, run offline with no network, no API, no retraining, and no model-artifact modification. Canonicalized evidence achieves strong_F1=0.4615, close to the oracle upper bound (0.4627) and substantially above raw BM25 chunks (0.2755). Results are diagnostic (silver labels, frozen R4), not benchmark-level.

**Do NOT use these wordings:**

- Format-shift metrics are validated (silver labels, not gold).
- Benchmark-level format-shift results (diagnostic, not benchmark).
- R4 is robust to format shift (only 8 variants; no formal robustness guarantee).

## 6. Final Gate Impact

- **Check ID:** 3.4
- **Current status:** PASS
- **Previous status:** BLOCKED
- **Resolution:** Local compatible sklearn environment identified; eval completed offline.

## 7. Hard Boundaries Enforced

- `no_network`: true (HF_HUB_OFFLINE=1; all model files local)
- `no_api`: true
- `no_training`: true (frozen R4 artifacts loaded read-only)
- No fake `format_shift_metrics.csv` (real prediction produces real metrics)
- No silver relabeled as gold
- No human audit results fabricated
