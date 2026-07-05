# Updated Reproducibility Note (Post-Realignment v1)

**Date:** 2026-07-05
**Selected main method:** V3.17 baseline (offline PDF-corpus evidence-sufficiency screening)
**Supersedes:** `scripts/HOW_TO_REPRODUCE_MAINLINE.md` (which anchored on V3.7 paper regeneration)

---

## 1. Current Selected Method — V3.17 Baseline

The current selected main method is the **V3.17 baseline offline PDF-corpus evidence-sufficiency screening pipeline**:

```
PDF corpus
  -> BM25 top-k retrieval (top-5 chunks per claim)
  -> evidence canonicalization (best_sentence_top5_overlap)
  -> restored R4 screening (10 seeds, per-seed thresholds, majority vote)
  -> risk ranking (G_conservative_precision)
  -> second-stage review queue (top-100 prioritized candidates)
```

**Frozen V3.17 baseline metrics (436 eval candidates):**
- strong_F1 = 0.4503
- strong_recall = 0.7064
- strong_precision = 0.3305
- macro_F1 = 0.3847
- precision@20 = 0.45
- recall@100 = 0.3303
- FP/TP @ 5% prevalence = 11.24
- standalone viable = false
- second-stage viable = true

## 2. Full Reproduction Is NOT Recommended

A full from-scratch reproduction is **NOT recommended**. Reasons:

1. **R4 artifacts are frozen.** Per-seed classifiers, scalers, thresholds, and feature columns are frozen on disk under `experiments/r4_minimal_recovery_v1/artifacts/seed_*/`. Rerunning R4 training breaks reproducibility against the frozen V3.17 baseline numbers.
2. **R4 thresholds are frozen.** Per-seed thresholds (e.g. seed_11: `t_contra=0.4`, `t_contra_low=0.35`, `t_strong=0.55`, `t_svm=0.55`) and the frozen reference thresholds (`t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`) must not be refit.
3. **NLI cache is frozen.** The 7439-row NLI cache for candidate sentences is frozen; rerunning NLI inference may produce slightly different probabilities.
4. **API results are frozen.** DeepSeek-V3 LLM judge baseline (200 samples) and GPT-5.5 probe (100 samples each) outputs are on disk. Rerunning costs real money and requires explicit user authorization.
5. **Reruns may cause version drift.** Model/API/library versions may have drifted since the frozen runs.

The recommended path is to **reuse existing experiment outputs** and only regenerate the V3.17 baseline review queue / ranking if the underlying CSVs change.

## 3. Reproduction Path for V3.17 Baseline

### Step 1 — Use existing experiment outputs (default)

All V3.17 baseline numbers come from frozen outputs in `experiments/`. Do not rerun. If a number is questioned, look it up in:

| Artifact | Path |
|---|---|
| V3.17 frozen baseline metrics | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` |
| Evidence canonicalization metrics | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` |
| Evidence canonicalization predictions | `experiments/r4_evidence_canonicalization_v1/r4_predictions_by_format.csv` |
| Canonicalized review queue scores | `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv` |
| Review queue top-100 | `experiments/canonicalized_review_queue_v1/review_queue_top100.csv` |
| Risk ranking features | `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv` |
| Risk ranking best-variant top-100 | `experiments/canonicalized_risk_ranking_v1/review_queue_top100_best.csv` |
| V3.18 intelligent upgrade comparison | `experiments/v3_18_intelligent_upgrade_v1/intelligent_upgrade_comparison_table.csv` |

### Step 2 — R4 artifacts (frozen, do not retrain)

R4 artifacts are at `experiments/r4_minimal_recovery_v1/artifacts/seed_*/` for seeds [11, 22, 33, 44, 55, 66, 77, 88, 99, 111]. Each seed folder contains:

- `classifier.joblib` (multi-route SVM + calibrated classifiers)
- `scaler.joblib` (feature scaler)
- `thresholds.json` (per-seed thresholds)
- `feature_columns.json` (NLI_FEATURES, expert_features, svm_features definitions)
- `label_mapping.json` (supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3)

### Step 3 — V3.17 baseline replay (if needed)

If a faithful replay of the V3.17 baseline review queue is required (e.g. to inspect a specific candidate), use:

```
python D:\ocn\scripts\run_canonicalized_review_queue_v1.py
```

This script:
- Loads the SimClaim candidate pool (444 pairs)
- Loads BM25 top-k chunks per candidate
- Applies `best_sentence_top5_overlap` canonicalization
- Loads R4 artifacts for all 10 seeds
- Computes NLI + action-gap features for the canonicalized evidence
- Routes through R4 (per-seed thresholds, majority vote, prefer test split with dev fallback)
- Computes `priority_score = p_strong_mean - p_contra_mean + 0.5 * strong_action_flag`
- Outputs the canonicalized review queue

**Before running:** confirm the run will not overwrite frozen outputs. The script enforces `no_model_training`, `no_api_calls`, `no_network`, `no_threshold_change`, `no_original_data_modification`.

### Step 4 — Risk ranking replay (if needed)

```
python D:\ocn\scripts\run_canonicalized_risk_ranking_v1.py
```

This script:
- Loads the canonicalized R4 review scores
- Computes 8 ranking formula variants (A_flag_only through H_balanced_review_score)
- Selects `G_conservative_precision` as the best variant (P@20=0.45)
- Outputs the best-variant review queue

### Step 5 — V3.18 intelligent upgrade replay (if needed)

```
python D:\ocn\scripts\run_v3_18_intelligent_upgrade_v1.py
```

This script reproduces the V3.18 negative ablation: trains sklearn learned selector + learned ranker (group-aware split), replays R4 with learned-selected evidence, and produces the 5-method comparison table. V3.17 baseline is NOT modified by this script.

## 4. Historical Paper Reproduction (V3.7)

The V3.7 advisor-handoff paper draft is retained as a historical artifact. To regenerate the V3.7 docx:

```
python D:\ocn\scripts\build_v3_7_docx.py
```

- Input: `paper_versions_ordered/V3_7_advisor_handoff_clean/CESE_OCN_V3_7_advisor_handoff_clean.md`
- Output: `paper_versions_ordered/V3_7_advisor_handoff_clean/CESE_OCN_V3_7_advisor_handoff_clean.docx`
- **Note:** V3.7 is NOT the current selected method. The current selected method is V3.17 baseline.

## 5. Do NOT Rerun These Scripts

The following are frozen and should not be rerun unless a new task explicitly authorizes it:

- `run_llm_judge_baseline_v1.py` (DeepSeek API, costs money)
- `run_gpt_structured_judge_probe_v1.py` (GPT-5.5 API, costs money)
- `run_external_gold_scifact_vitaminc_v1.py` (large download + NLI inference)
- `run_v3_r4_strong_baselines_holdout_v1.py` (frozen R4 results)
- `run_cese_ocn_lite_v3.py` (frozen R4 router)
- `run_mixed_framework_router_optimization_v2.py` (frozen thresholds)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (frozen sweep)

## 6. Historical / Diagnostic Experiment Reports

The following experiment directories contain historical/diagnostic reports that are retained for traceability but are NOT part of the V3.17 baseline mainline. Do not edit their reports; treat them as historical:

- `experiments/overnight_non_api_compute_pipeline_v1/` (Tasks A–H)
- `experiments/v3_15_*` (V3.15 deep tests and audits)
- `experiments/v3_11_*` (V3.11 credibility and robustness experiments)
- `experiments/rigourate_reproduction_and_simclaim_baseline_v1/`
- `experiments/strict_silver_max_v1/` and `experiments/strict_silver_max_v1_binary_decomposition/`
- `experiments/mixed_framework_v2_frozen_r4_baseline/` (historical frozen R4 baseline using frozen reference thresholds; current mainline uses restored R4 per-seed thresholds via `canonicalized_review_queue_v1`)
- `experiments/mixed_framework_router_optimization_v2/`
- `experiments/mixed_framework_new_algorithm_sweep_v1/`
- `experiments/paper_ready_mixed_framework_v2/`
- `experiments/external_gold_scifact_vitaminc_v1/`
- `experiments/v3_external_gold_llm_plan_v1/`
- `experiments/v3_r4_strong_baselines_holdout_v1/`

## 7. Data Sources (Frozen)

| Data | Path | Notes |
|---|---|---|
| SimClaim candidate pool | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` | 444 pairs, 111 groups, 6 domains; silver labels |
| SimClaim PDF corpus | `data/simclaim_pdf_corpus_v1/` | Source PDFs for BM25 retrieval |
| NLI cache | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/nli_cache/` | 7439 rows, frozen NLI probabilities |
| BM25 chunks | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/bm25_top_k_chunks/` | Top-k chunks per candidate |
| External gold (SciFact + VitaminC) | `data/external_gold/` | Used only by historical external gold experiment |

## 8. Prohibitions Enforced

- no experiment data modification
- no experiment rerun (without explicit authorization)
- no paper body modification
- no file deletion
- no API calls (without explicit authorization)
- no network
- no silver-as-gold
- no natural-distribution claim
- no R4 retraining / threshold change
- no learned-upgrade-as-main-method claim
