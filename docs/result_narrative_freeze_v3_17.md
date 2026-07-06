# Result Narrative Freeze — V3.17 Confidential Lightweight

**Authority:** This document freezes the interpretation of every
quantitative result in V3.17. Each result has a metric, a source file,
a safe interpretation, and a "not supported" interpretation. Any change
to a result requires updating this document.

**Scope:** V3.17 Confidential Lightweight mainline only.

**Hard boundaries:**
- No fabricated results. Every number is traceable to a file under
  `experiments/`, `reports/`, or `paper_assets/`.
- Missing results are marked `TBD` or `blocked` with the blocking reason.
- Silver labels are never described as gold.
- No SOTA / general detector / automatic peer reviewer claims.

---

## Result R1 — BM25 retrieval (RQ1)

- **Metric:** recall@1 = 0.7162, recall@5 = 0.9730, recall@10 = 0.9797,
  MRR = 0.8261, oracle_match_rate = 0.9910, pdf_coverage_rate = 1.0
  (69/69 PDFs found).
- **Source file:** `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json`
- **Safe interpretation:** On the controlled silver diagnostic, local
  BM25 retrieves source-traceable evidence for the large majority of
  candidates (recall@10 = 0.98), confirming that confidential local
  retrieval is viable as the first stage of the pipeline.
- **Not supported interpretation:** BM25 is SOTA for scientific claim
  retrieval; the retrieval system generalizes to gold benchmarks;
  recall numbers transfer to natural prevalence settings.

---

## Result R2 — Sentence/window BM25 on real PDF corpus (RQ1 extension)

- **Metric:** recall@1 = 0, recall@5 = 0, recall@10 = 0, MRR = 0
  (blocked).
- **Source file:** `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json`
- **Blocking reason:** `missing_pdf_corpus` — the
  `data/pdf_corpus_v1/sentences.jsonl` file required by the
  sentence/window retriever was not generated in this run.
- **Safe interpretation:** Sentence-level and window-level BM25 on the
  real PDF corpus could not be evaluated; the result is blocked.
  Toy-mode results (separate file) suggest sentence-level retrieval
  outperforms window-level, but this is not a real-data claim.
- **Not supported interpretation:** Sentence/window BM25 is worse than
  chunk BM25 on real data; the format-shift finding does not hold at
  sentence granularity.

---

## Result R3 — Raw chunk format hurts screening (RQ2)

- **Metric:** `raw_top1_chunk` oracle_recall = 0.0428; 90.99% of raw
  chunks exceed 60 words.
- **Source file:** `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- **Safe interpretation:** Raw BM25 chunks are too long and too noisy
  to match screening-format evidence (oracle recall 4.3%). This
  quantifies the retrieval-to-screening format shift as a concrete
  failure mode in confidential local PDF review.
- **Not supported interpretation:** BM25 retrieval is broken; raw
  chunks are unsuitable for all downstream tasks; the format shift
  generalizes to gold benchmarks.

---

## Result R4 — Canonicalization restores screening signal (RQ3)

- **Metric:** `best_sentence_top5_overlap` oracle_recall = 0.3874,
  mean_overlap = 0.5236, 0% of selected evidence exceeds 60 words.
  Improvement over `raw_top1_chunk` = 9.0x (0.387 / 0.043).
- **Source file:** `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- **Safe interpretation:** Deterministic evidence canonicalization
  (selecting the best sentence from BM25 top-5 chunks by token overlap
  with the claim) substantially raises oracle recall and produces
  screening-format-length evidence. This supports canonicalization as
  a no-API, no-training bridge between retrieval and screening.
- **Not supported interpretation:** Canonicalization always improves
  retrieval; canonicalization is necessary for all datasets; the 9x
  improvement generalizes to gold benchmarks.

---

## Result R5 — Canonicalizer variant ranking (RQ4)

- **Metric:** Selector ranking by oracle_recall:
  1. `best_sentence_top5_overlap`: 0.3874
  2. `best_sentence_top1_overlap`: 0.2207
  3. `three_sentence_window_top5`: 0.2027
  4. `raw_top1_chunk`: 0.0428
  5. `first_sentence_top1`: 0.0270
  6. `cleaned_top1_chunk`: 0.0180
  7. `sentence_bm25_top1`: BLOCKED (missing PDF corpus)
  8. `window_bm25_top1`: BLOCKED (missing PDF corpus)
- **Source file:** `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- **Safe interpretation:** On the controlled silver diagnostic,
  overlap-based sentence selectors dominate position-based selectors
  (`first_sentence`, `cleaned_top1_chunk`). Top-5 pooling beats
  top-1 pooling. The two BM25-based selectors are blocked and cannot
  be ranked on real data.
- **Not supported interpretation:** Overlap-based selectors are
  universally best; the ranking generalizes to gold benchmarks; the
  blocked selectors would rank below the overlap-based ones on real
  data.

---

## Result R6 — Format-shift R4 evaluation (RQ2/RQ3 bridge)

- **Metric:** blocked. Variant inputs generated: 3552 rows (8 variants
  × 444 candidates); NLI features computed (shape 3552 × 7).
- **Source file:** `experiments/format_shift_ablation_v1/r4_eval_blocked.json`
- **Blocking reason:** `sklearn_version_mismatch` — R4 frozen
  artifacts were pickled with scikit-learn 1.9.0 but the current
  environment has 1.4.1.post1. The `LogisticRegression.multi_class`
  attribute was removed in 1.9.0 but is accessed by 1.4.1
  `predict_proba`. Fix requires network access (violates no_network
  boundary).
- **Safe interpretation:** The end-to-end format-shift R4 evaluation
  could not be completed. Variant inputs and NLI features are
  available for manual analysis or future re-run after a network-free
  sklearn upgrade.
- **Not supported interpretation:** Format shift does not affect R4
  screening; canonicalization does not improve R4 F1; the blocked
  evaluation would have shown a positive result.

---

## Result R7 — Frozen R4 screening (RQ5 baseline)

- **Metric:** strong_F1 = 0.4503, 95% CI [0.4086, 0.4833],
  strong_precision = 0.3305, strong_recall = 0.7064,
  macro_F1 = 0.3847 (group-aware bootstrap, n=100).
- **Source file:** `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`
- **Safe interpretation:** On the controlled silver diagnostic, frozen
  R4 screening yields strong_F1 ≈ 0.45 with a tight group-aware
  bootstrap CI. This is a promising signal that the pipeline produces
  usable screening output, but it is not benchmark-level validation.
- **Not supported interpretation:** R4 is a validated general
  detector; R4 achieves SOTA on simulation claim screening; the F1
  generalizes to gold benchmarks or natural prevalence.

---

## Result R8 — Conservative review queue (RQ5)

- **Metric:** `G_conservative_precision` precision@20 = 0.45,
  recall@100 = 0.330, AP = 0.3532.
  Baseline `A_flag_only`: precision@20 = 0.35, recall@100 = 0.330.
  Queue overall: precision@100 = 0.37, recall@100 = 0.339.
- **Source file:** `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv`
- **Safe interpretation:** The conservative precision-optimized
  variant (`G_conservative_precision`) improves precision@20 from
  0.35 (flag-only baseline) to 0.45 while preserving recall@100. This
  supports the use of conservative ranking as a second-stage review
  queue that augments human reviewers.
- **Not supported interpretation:** The queue replaces human review;
  the queue acting as a standalone detector (not supported);
  precision@20 = 0.45 being sufficient for deployment without human
  adjudication (not supported).

---

## Result R9 — Leakage audit (RQ6)

- **Metric:** 12 checks: 11 PASS + 1 SKIP = overall PASS.
  - Claim-only strong_F1 = 0.2448 (ratio to R4 = 0.5436, below 0.8
    WARNING threshold).
  - Shuffled evidence: correct_overlap = 0.3614,
    shuffled_overlap = 0.0079, ratio = 45.94x.
  - Title-only retrieval: mean_overlap = 0.0428.
  - Metadata-only retrieval: purity = 0.25.
  - Lexical overlap by label: ratio = 1.3444.
  - Cue words by label: max_cue_ratio = 1.6075.
  - Label lexical cues: max_cues = 0.
  - Group split integrity: cross_groups = 0.
  - Generation policy concentration: max = 0.25.
- **Source file:** `experiments/leakage_audit_v1/audit_summary.md`,
  `experiments/leakage_audit_v1/claim_only_baseline.json`,
  `experiments/leakage_audit_v1/shuffled_evidence_baseline.json`
- **Safe interpretation:** The silver diagnostic shows no significant
  shortcuts or leakage. Claim-only signal is well below the R4
  threshold (ratio 0.54 < 0.8). Shuffled evidence collapses overlap
  by 46x, confirming the pipeline depends on real evidence rather
  than claim-only cues. Group integrity holds (cross_groups = 0).
- **Not supported interpretation:** The dataset is leak-free under
  all possible attacks; the dataset is a gold benchmark; the PASS
  result certifies generalization to real claims.

---

## Result R10 — Complexity-vs-utility tradeoff (RQ7)

- **Metric:** Pareto table (8 methods × 6 scores):
  - `deterministic_canonicalization`: Pareto optimal (performance=1,
    privacy=1, auditability=1, simplicity=1, reproducibility=1).
  - `conservative_rule_queue`: Pareto optimal.
  - `lightweight_smart_queue`: Pareto optimal.
  - `learned_selector_only`, `learned_ranker_only`,
    `learned_selector_plus_learned_ranker`: dominated
    (auditability=0.5, reproducibility=0.5).
  - `external_llm_baseline`: unavailable (privacy=0).
  - `raw_retrieval_baseline`: dominated (performance=0.40).
- **Source file:** `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- **Safe interpretation:** Under confidential / no-API / no-training
  / silver-diagnostic constraints, deterministic canonicalization
  and conservative rule-based queues are Pareto-optimal. Learned
  methods are dominated on auditability and reproducibility; the
  external LLM baseline is unavailable due to privacy constraints.
- **Not supported interpretation:** Rules generally beat learned
  models; the Pareto result generalizes to settings with API access
  or training budget; the LLM baseline would underperform if
  available.

---

## Result R11 — Error taxonomy (RQ-adjacent)

- **Metric:** 9 error types tagged.
  Top 3: `mild_vs_strong_boundary` (38.83%),
  `weak_selector_overlap` (34.57%), `supported_overflag` (32.98%).
- **Source file:** `experiments/error_taxonomy_v1/error_taxonomy_summary.csv`
- **Safe interpretation:** The dominant error mode is the
  mild-vs-strong boundary, which is intrinsic to the four-label
  scheme and would benefit from human adjudication. Weak selector
  overlap points to canonicalization failures on long claims.
- **Not supported interpretation:** The error distribution certifies
  the system is production-ready; the errors would not occur on gold
  benchmarks; the taxonomy generalizes to other domains.

---

## Result R12 — Human audit (partial / blocked)

- **Metric:** partial. Protocol built (`docs/human_audit_protocol_v1.md`),
  audit template built (`data/audit_templates/human_audit_template.csv`),
  audit queue seeds built (111 seeds, redacted).
  No adjudication completed; no agreement metrics available.
- **Source file:** `experiments/human_audit_v1/audit_agreement_summary.json`
  (does not exist or partial),
  `data/audit_templates/human_audit_template.csv`,
  `docs/human_audit_protocol_v1.md`
- **Safe interpretation:** A small targeted human audit protocol is
  in place, but no full human audit has been completed. The dataset
  remains silver-label (`human_audited=False` for all 444 rows).
- **Not supported interpretation:** The dataset is human-audited;
  the human audit certifies the silver labels; the audit agreement
  is sufficient to convert silver to gold.

---

## Result R13 — PDF extraction stress test (robustness, not SOTA)

- **Metric:** 12 stress documents processed, 0 failures, 123
  sentences and 102 windows extracted. Anchor retrieval
  (sentence Recall@1 = 1.0, window Recall@1 = 0.2) on synthetic
  stress sources.
- **Source file:** `experiments/pdf_extraction_stress_test_v1/` (12 files)
- **Safe interpretation:** The PDF extraction pipeline is robust
  across 12 synthetic stress types (multi-column, scanned fallback,
  math-heavy, etc.). This is an extraction robustness test, not a
  SOTA claim.
- **Not supported interpretation:** The extractor is SOTA on
  scientific PDFs; the robustness result generalizes to all PDF
  types; the stress test certifies production readiness.

---

## Forbidden interpretations (apply to ALL results above)

The following interpretations are NEVER supported by V3.17 data:

- "validated general detector" — six domains only, silver labels
- "gold benchmark" — `human_audited=False` for all rows
- "human-audited benchmark" — no full human audit completed
- "SOTA" / "state-of-the-art" — no shared-benchmark comparison
- "automatic peer reviewer" — pipeline produces a review queue,
  not automatic peer review
- "full CESE-OCN validated" — V3.17 is a scoped subset
- "outperforms LLMs" — no LLM baseline available (privacy=0)
- "generalizes to real claims" — silver diagnostic only

---

## Required caveat (must accompany every result section)

> We use a source-traceable controlled silver diagnostic set. The
> labels are not gold or human-audited, and results should not be
> interpreted as benchmark-level model validation.
