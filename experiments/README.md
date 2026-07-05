# Experiments Index

This document indexes the experiment directories produced by the
**V3.17 Confidential Lightweight** pipeline. Each entry lists its purpose,
inputs, outputs, and leakage policy.

> **Mainline**: V3.17 Canonicalized R4 Baseline — frozen strong_F1 = 0.4503.
> Pipeline: PDF corpus → BM25 retrieval (top-5) → evidence canonicalization
> (`best_sentence_top5_overlap`) → frozen R4 screening (10-seed OOF) →
> `G_conservative_precision` risk ranking → top-100 review queue.
>
> **Confidentiality**: all stages run locally. No network, no API, no cloud,
> no PDF upload. See `docs/leakage_and_confidentiality_policy.md` and
> `docs/data_release_policy.md`.

## Directories

### 1. `bm25_sentence_retrieval_v1`

- **Purpose**: BM25 retrieval at sentence and window granularity. Computes
  oracle recall (recall@1/5/10, MRR) to measure whether the retrieval unit
  (sentence vs. window) affects evidence coverage.
- **Inputs**: candidate CSV (`claim_text` as query), sentence corpus JSONL.
- **Outputs**: `retrieval_results_sentence_bm25.csv`,
  `retrieval_results_window_bm25.csv`, `oracle_recall_summary.json`,
  `retrieval_config.json`, `retrieval_examples_redacted.csv`.
- **Leakage policy**: forbidden fields (`true_label`, `oracle_hit`,
  `evidence_text`, label guesses) are NOT used as retrieval features. A
  `assert_no_forbidden_fields_used_for_retrieval()` guard is enforced.
  Oracle hit is computed AFTER retrieval for metric evaluation only.
- **Toy variant**: `bm25_sentence_retrieval_v1_toy/` (synthetic data).

### 2. `canonicalizer_ablation_v1`

- **Purpose**: Ablation over 8 evidence selectors (raw_top1_chunk,
  cleaned_top1_chunk, first_sentence_top1, best_sentence_top1_overlap,
  best_sentence_top5_overlap, three_sentence_window_top5,
  sentence_bm25_top1, window_bm25_top1). Proves that raw chunks are not
  screening-compatible while short canonicalized spans restore signal.
- **Inputs**: candidate CSV, sentence corpus JSONL, BM25 retrieval results.
- **Outputs**: `selector_variant_evidence.csv` (13 fields),
  `selector_metrics_summary.csv`, `selector_examples_redacted.csv`,
  `canonicalizer_config.json`, `leakage_guard_report.json`.
- **Leakage policy**: selector scoring uses only token overlap F1 and length
  penalty. `oracle_hit`, `true_label`, and label guesses are forbidden for
  selection. Oracle recall is computed AFTER selection for metrics only.
- **Default selector** (mainline): `best_sentence_top5_overlap`.
- **Toy variant**: `canonicalizer_ablation_v1_toy/` (synthetic data).

### 3. `format_shift_ablation_v1`

- **Purpose**: Constructs 8 evidence format variants per candidate
  (oracle_clean, oracle+metadata, oracle_lengthened,
  oracle+metadata+lengthened, raw_bm25_top1, cleaned_bm25_top1,
  canonicalized_best_sentence_top5, canonicalized_window_top5) to isolate
  the effect of format shift on screening. Demonstrates that lengthening
  oracle evidence (12.7 → 93.3 words) flips predictions even in toy mode.
- **Inputs**: candidate CSV, canonicalizer output, BM25 retrieval results.
- **Outputs**: `format_shift_inputs.csv`,
  `format_shift_inputs_redacted.csv`, `format_shift_config.json`.
- **Leakage policy**: `oracle_clean` is DIAGNOSTIC only (uses oracle evidence
  span — never available in production). `canonicalized_best_sentence_top5`
  is the PRODUCTION variant. All variants are marked with `paper_ready=false`
  in toy mode.
- **Toy variant**: `format_shift_ablation_v1_toy/` (synthetic data).

### 4. `canonicalized_review_queue_v1`

- **Purpose**: Produces the canonicalized review queue with frozen R4
  screening scores (`p_strong`, `p_contra`, `p_svm`, `strong_action_flag`,
  `entropy`, vote shares) for each candidate. Input to SmartQueue.
- **Inputs**: candidate CSV, canonicalized evidence, frozen R4 artifacts
  (`experiments/r4_minimal_recovery_v1/artifacts/seed_<N>/`).
- **Outputs**: `canonicalized_r4_review_scores.csv` (per-candidate R4 scores),
  `review_queue_config.json`, `r4_leakage_guard_report.json`.
- **Leakage policy**: R4 is FROZEN — no threshold changes, no retraining.
  `true_label` is used for metrics ONLY. Forbidden fields are not fed to R4
  classifiers. 10-seed out-of-fold majority voting prevents train/test
  contamination.
- **Note**: produced by `evaluate_r4_on_evidence_variants_v1.py` when run on
  the canonicalized variant with `--no_threshold_change`.

### 5. `canonicalized_risk_ranking_v1`

- **Purpose**: Hard risk ranking (V3.17 baseline) using
  `G_conservative_precision` to produce the top-100 review queue. This is
  the pre-SmartQueue baseline ranking for comparison.
- **Inputs**: `canonicalized_r4_review_scores.csv`.
- **Outputs**: `risk_ranking_top100.csv`, `risk_ranking_config.json`,
  `risk_ranking_metric_summary.json`.
- **Leakage policy**: ranking uses only R4 scores
  (`p_strong`, `p_contra`, `strong_action_flag`). `true_label` is used for
  metrics (precision@k, recall@k) ONLY, never for ranking.
- **Note**: SmartQueue (directory 6) supersedes this with profile-based
  scoring, bucket routing, and group diversity.

### 6. `lightweight_smart_queue_v1`

- **Purpose**: Lightweight, auditable, confidentiality-friendly SmartQueue.
  Replaces hard ranking with 3 profiles (conservative / balanced /
  high_recall), 4 buckets (contradiction_or_conflict_review /
  high_priority_strong_review / evidence_check_needed / low_priority), and
  group diversity constraints (1/2/3 per group in top20/50/100).
- **Inputs**: `canonicalized_r4_review_scores.csv`,
  `selector_variant_evidence.csv` (canonicalizer output),
  `retrieval_results_sentence_bm25.csv`.
- **Outputs**: `smart_queue_scores.csv`, `smart_queue_top20.csv`,
  `smart_queue_top50.csv`, `smart_queue_top100.csv`,
  `smart_queue_config.json`, `smart_queue_metric_summary.json`,
  `leakage_guard_report.json`.
- **Leakage policy**: allowed sort fields = `{p_strong, p_contra, p_svm,
  strong_action_flag, entropy, selector_score, selected_rank,
  selected_n_words, bm25_score}`. Forbidden sort fields = `{true_label,
  is_strong_action, oracle_hit, candidate_label_guess, final_label,
  gold_label, human_audited, evidence_text, evidence_text_sha256}`.
  `true_label` is used for metrics ONLY.
- **Toy variant**: `lightweight_smart_queue_v1_toy/` (synthetic data with
  mock R4 scores).

### 7. `leakage_audit_v1`

- **Purpose**: 7-check leakage audit across the full pipeline.
  1. claim-only baseline (is claim text alone enough to predict label?)
  2. title-only retrieval baseline (does title-only retrieval overperform?)
  3. metadata-only retrieval baseline (does metadata leak label?)
  4. label lexical cues (are label words over-represented in claims?)
  5. group split integrity (does the same `target_candidate_group_id` cross
     train/test?)
  6. selector reads no oracle/label (selector source-code guard)
  7. SmartQueue reads no forbidden fields (queue source-code guard)
- **Inputs**: candidate CSV, claim JSONL, selector source, SmartQueue source.
- **Outputs**: `claim_only_baseline.json`,
  `title_only_retrieval_baseline.json`,
  `metadata_only_retrieval_baseline.json`,
  `lexical_overlap_by_label.csv`, `group_split_integrity.json`,
  `no_oracle_in_selector_check.json`,
  `no_label_in_queue_sorting_check.json`, `audit_summary.md`.
- **Leakage policy**: the audit ITSELF is the leakage guard. Each check
  produces a pass/fail verdict with evidence. Failures must be resolved
  before any paper-valid result is claimed.
- **Toy variant**: `leakage_audit_v1_toy/` (synthetic data with mock labels).

### 8. `toy_end_to_end_demo_v1`

- **Purpose**: End-to-end demo of the full V3.17 pipeline on toy synthetic
  data. Proves the pipeline runs without errors, schemas are correct, and
  no leakage occurs. Does NOT prove real screening quality.
- **Inputs**: `data/toy_synthetic/toy_pdf_texts.jsonl`,
  `data/toy_synthetic/toy_candidates_v1.csv`,
  `data/toy_synthetic/toy_claims.jsonl`.
- **Outputs**: `toy_review_queue.csv` (copy of SmartQueue top-100),
  `toy_run_summary.json` (step status, mock_r4_warning).
- **Leakage policy**: ALL R4 scores are MOCK/TOY. Results must NEVER be
  merged with real experiment results or cited in the paper. The
  `mock_r4_warning` field in `toy_run_summary.json` makes this explicit.
- **Running**: `python scripts/run_toy_end_to_end_demo_v1.py` (idempotent —
  skips steps whose output already exists). See `docs/toy_demo.md`.

## Related directories (not part of the 8-index above)

- `r4_minimal_recovery_v1/` — frozen R4 artifacts (10 seeds × classifiers,
  scalers, thresholds). Read-only input to directories 4, 5, 6.
- `r4_evidence_canonicalization_v1/` — earlier canonicalization experiments.
- `rigourate_reproduction_and_simclaim_baseline_v1/` — SimClaim dataset and
  RIGOURATE reproduction artifacts.

## Data release policy

See `docs/data_release_policy.md` for the full data release policy. Key
points:

- Toy / smoke / pilot_template data is always marked `paper_ready=false`.
- Real experiment results must have `paper_valid=true`,
  `metric_valid=true`, `prediction_source` specified, and must not use gold
  tiers.
- Diagnostic baselines are never included in main paper tables.
- Source triples are never split across train/test/dev splits.
