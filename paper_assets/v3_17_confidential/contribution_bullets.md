# Contribution Bullets — V3.17 Confidential Lightweight

**Authority:** These are the frozen contribution claims for V3.17.
Each bullet is sourced from a specific experiment or audit file. No
bullet claims gold, SOTA, automatic peer review, or general detector
status.

---

## Contributions

1. **Identify retrieval-to-screening format shift in confidential
   local PDF review.**
   We quantify a concrete failure mode: raw BM25 PDF chunks are too
   long (91% exceed 60 words) and too noisy to match screening-format
   evidence (oracle_recall = 0.043). This is a format mismatch between
   the retrieval stage and the downstream screening stage, not a
   retrieval-quality problem.
   Source: `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`

2. **Propose deterministic evidence canonicalization as a no-API
   bridge.**
   We introduce an unsupervised, local canonicalizer that selects the
   best sentence from BM25 top-5 chunks by token overlap with the
   claim. The best canonicalizer (`best_sentence_top5_overlap`) raises
   oracle_recall from 0.043 to 0.387 (9x improvement) and produces
   screening-format-length evidence (0% exceed 60 words). No API
   calls, no model training, no cloud dependency.
   Source: `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`

3. **Evaluate frozen R4 screening and conservative queueing in a
   controlled silver diagnostic setting.**
   We evaluate a frozen R4 screening router (strong_F1 = 0.4503, 95%
   CI [0.4086, 0.4833]) and a conservative precision-optimized review
   queue (`G_conservative_precision`, precision@20 = 0.45, vs. 0.35
   for the flag-only baseline). The queue is a second-stage review
   tool that augments human reviewers; it is not a standalone
   detector.
   Sources:
   `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`,
   `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv`

4. **Provide leakage, error taxonomy, metric robustness, and
   release-safety audits.**
   We audit the silver diagnostic with 12 leakage checks (11 PASS + 1
   SKIP, overall PASS), tag 9 error types (top: mild_vs_strong_boundary
   at 38.83%), report group-aware bootstrap CIs for all R4 metrics,
   and run a confidentiality redteam scan (high_risk = 0) plus a
   public sanitized release bundle. The release excludes raw
   claim/evidence text, PDFs, and private scoring files.
   Sources:
   `experiments/leakage_audit_v1/audit_summary.md`,
   `experiments/error_taxonomy_v1/error_taxonomy_summary.csv`,
   `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`,
   `reports/confidentiality_redteam_scan_v3_17.md`,
   `release_bundles/v3_17_confidential_public/`

---

## Non-contributions (explicitly NOT claimed)

- We do **not** claim a gold benchmark.
- We do **not** claim a human-audited dataset.
- We do **not** claim SOTA on simulation claim screening.
- We do **not** claim an automatic peer reviewer.
- We do **not** claim a validated general detector.
- We do **not** claim full CESE-OCN neural architecture validation.
- We do **not** claim that deterministic canonicalization generally
  beats learned models; the Pareto result is deployment-specific
  (confidential / no-API / no-training / silver diagnostic).

---

## Required caveat

> We use a source-traceable controlled silver diagnostic set. The
> labels are not gold or human-audited, and results should not be
> interpreted as benchmark-level model validation.
