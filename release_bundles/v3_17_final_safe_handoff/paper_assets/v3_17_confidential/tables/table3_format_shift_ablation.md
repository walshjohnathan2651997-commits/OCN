# Table 3 — Format-Shift Ablation

Format-shift R4 evaluation completed offline using a project-local `.venv` with scikit-learn 1.9.0 (exact match for frozen R4 artifacts), under `HF_HUB_OFFLINE=1`/`TRANSFORMERS_OFFLINE=1`. No network, no API, no retraining, no model-artifact modification. Schema validation: 38/38 PASS.

| Variant | strong_F1 | strong_precision | strong_recall | macro_F1 | n_eval | Δ vs oracle_clean | Δ vs raw_bm25 |
|---|---|---|---|---|---|---|---|
| oracle_clean | 0.4627 | 0.3899 | 0.5688 | 0.4609 | 436 | 0.000 | +0.1872 |
| oracle_plus_metadata | 0.4335 | 0.4681 | 0.4037 | 0.4798 | 436 | −0.0292 | +0.1580 |
| oracle_lengthened | 0.0000 | 0.0000 | 0.0000 | 0.3470 | 436 | −0.4627 | −0.2755 |
| oracle_plus_metadata_lengthened | 0.0000 | 0.0000 | 0.0000 | 0.3725 | 436 | −0.4627 | −0.2755 |
| raw_bm25_top1_chunk | 0.2755 | 0.3103 | 0.2477 | 0.3590 | 436 | −0.1872 | 0.000 |
| cleaned_bm25_top1_chunk | 0.2769 | 0.3140 | 0.2477 | 0.3608 | 436 | −0.1858 | +0.0014 |
| **canonicalized_best_sentence_top5** | **0.4615** | 0.3246 | 0.7982 | 0.3570 | 436 | −0.0011 | **+0.1860** |
| canonicalized_three_sentence_window_top5 | 0.3985 | 0.3376 | 0.4862 | 0.3871 | 436 | −0.0642 | +0.1230 |

**Key findings:**
- Canonicalized evidence (`canonicalized_best_sentence_top5`) achieves strong_F1=0.4615, close to the oracle upper bound (0.4627, Δ=−0.0011) and substantially above raw BM25 chunks (0.2755, Δ=+0.1860).
- Canonicalization gain: +0.186 strong_F1 confirms the retrieval-to-screening format shift materially affects R4 performance.
- Lengthened variants produce strong_F1=0.0, confirming that lengthening evidence beyond the screening format collapses R4 prediction.
- Results are diagnostic (silver labels, frozen R4), not benchmark-level.

[Source: experiments/format_shift_ablation_v1/format_shift_metrics.csv; experiments/format_shift_ablation_v1/format_shift_summary.json; reports/sklearn_offline_compatibility_investigation_v3_17.md]
