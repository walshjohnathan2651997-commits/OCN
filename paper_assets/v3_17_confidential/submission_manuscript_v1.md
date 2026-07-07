# Local Evidence Canonicalization for Offline Simulation-Claim Review Queues

### A Controlled Silver Diagnostic Study of Retrieval-to-Screening Format Shift

**Submission Manuscript Draft v1 — V3.17 Confidential Lightweight**

> **Mandatory framing.** This is a controlled silver diagnostic study, not a gold benchmark. The system is a second-stage review queue generator, not a standalone detector. Confidentiality is a deployment constraint, not the empirical contribution. Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch.

---

## 1. Title

**Local Evidence Canonicalization for Offline Simulation-Claim Review Queues: A Controlled Silver Diagnostic Study of Retrieval-to-Screening Format Shift**

---

## 2. Abstract

Simulation-claim review requires screening claims about autonomous driving, policy simulation, digital twins, cyber defense, multi-agent reinforcement learning, and robotics against source PDF evidence. In confidential offline deployment settings, API egress, network access, and new model training are prohibited, so all retrieval, screening, and ranking must run locally and remain auditable.

We study this problem on a 444-candidate controlled silver diagnostic set (111 groups × 4 balanced labels: supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate). The dataset is source-traceable but **not gold and not human-audited** (`human_audited=False` for all rows); results are diagnostic, not benchmark-level validation.

We identify a retrieval-to-screening format shift: raw BM25 PDF chunks are too long and noisy to match screening-format evidence (oracle_recall = 0.043, 91% of chunks exceed 60 words). To bridge this gap without API calls or training, we propose deterministic evidence canonicalization that selects the best sentence from BM25 top-5 chunks by token overlap with the claim. The best canonicalizer (`best_sentence_top5_overlap`) raises oracle_recall to 0.387 (9x improvement) and produces screening-format-length evidence (0% of selected evidence exceeds 60 words).

We then evaluate a frozen R4 screening router (strong_F1 = 0.4503, 95% CI [0.4086, 0.4833]) and a conservative precision-optimized review queue (`G_conservative_precision`, precision@20 = 0.45). The queue augments human review; **it is a second-stage review queue generator, not a standalone detector**, and does not replace adjudication. A 12-check leakage audit finds no significant shortcuts or label contingencies: claim-only strong_F1 = 0.2448 (ratio to R4 = 0.54, below the 0.8 warning threshold).

Limitations: silver labels (not gold), no completed human audit (protocol staged, not executed), six domains only, and **format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch**. The system is not a validated general detector, not SOTA, and not an automatic peer reviewer.

[Source: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv; experiments/metric_robustness_v1/classification_metrics_with_ci.csv; experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json; experiments/leakage_audit_v1/audit_summary.md; reports/format_shift_r4_eval_blocked_v3_17.md]

---

## 3. Introduction

Simulation-claim review is the task of checking whether a claim about a simulated system (autonomous driving, policy simulation, digital twins, cyber defense, multi-agent reinforcement learning, robotics) is supported by, in mild scope overclaim of, in strong action overclaim of, or in contradiction with its source evidence. In confidential deployment settings, the evidence is held as local PDF corpora that cannot leave the deployment boundary, API egress is prohibited, and retraining is disallowed.

This setting produces a concrete engineering problem: the retrieval stage returns long PDF chunks (≈200 words, ≈91% exceed 60 words), but the downstream screening stage was trained on short screening-format evidence. We call this mismatch the **retrieval-to-screening format shift**. Bridging it without API calls or new training requires a deterministic, auditable transformation.

We make the following contributions in this submission:

1. We quantify the retrieval-to-screening format shift on a 444-candidate controlled silver diagnostic set.
2. We propose deterministic evidence canonicalization (best-sentence selection from BM25 top-5 chunks by token overlap) as a no-API, no-training bridge.
3. We evaluate a frozen R4 screening router and a conservative precision-optimized review queue, with group-aware bootstrap CIs and a 12-check leakage audit.
4. We provide a complexity-vs-utility Pareto analysis showing that, under the confidential / no-API / no-training / silver-diagnostic constraint set, the deterministic canonicalization is Pareto-optimal against learned alternatives.

We explicitly do **not** claim a gold benchmark, a human-audited dataset, SOTA on simulation-claim screening, an automatic peer reviewer, a validated general detector, or full CESE-OCN neural architecture validation. **This is a controlled silver diagnostic study, not a gold benchmark.**

[Source: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv; experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv; docs/dataset_version_lock_v3_17.md]

---

## 4. Related Work

Simulation-claim review intersects three lines of prior work: (a) scientific claim verification on benchmarks such as SciFact and VitaminC, (b) retrieval-augmented screening for systematic review and triage, and (c) confidential/on-premise NLP pipelines that operate without API egress or external LLMs.

Two structural differences apply. First, prior claim-verification benchmarks are gold-labeled and human-audited; our setting is a controlled silver diagnostic set with `human_audited=False` for all rows. **This is a controlled silver diagnostic study, not a gold benchmark.** Second, prior retrieval-augmented screening pipelines typically assume cloud LLM access; our deployment constraint forbids it.

We therefore do not position the system as a validated general detector and do not claim SOTA against gold benchmarks. The empirical contribution is the identification and bridging of the retrieval-to-screening format shift under explicit no-API, no-network, no-training boundaries.

[Source: docs/dataset_version_lock_v3_17.md; experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv]

---

## 5. Problem Setting

A candidate is a tuple `(claim_text, source_evidence, candidate_label_guess)` where `candidate_label_guess ∈ {supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate}`. The deployment pipeline runs in three stages:

1. **Retrieval.** Given `claim_text`, retrieve top-k evidence units from a local PDF corpus using BM25.
2. **Canonicalization.** Transform the retrieved long chunk into screening-format evidence (≤60 words).
3. **Screening + ranking.** Apply a frozen R4 screening router to compute per-candidate risk scores; rank into a review queue.

The reviewer then adjudicates the top of the queue. **The system is a second-stage review queue generator, not a standalone detector.** The output is a prioritized queue, not an automated decision.

**Confidentiality is a deployment constraint, not the empirical contribution.** All experiments run under `no_api`, `no_network`, `no_training` boundaries enforced by the V3.17 pipeline runner.

[Source: configs/v3_17_paths.yaml; experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json]

---

## 6. Dataset and Boundaries

We use the **SimClaim Strict Silver Diagnostic Set v1**, locked at SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812` (448144 bytes, 444 rows, 36 columns, 111 groups).

| Property | Value |
|---|---|
| Row count | 444 |
| Group count | 111 (one candidate per label per group) |
| Labels | supported (111), mild_scope_overclaim (111), strong_action_overclaim (111), contradiction_candidate (111) |
| `human_audited` | False for all 444 rows |
| `gold_label` nonempty | 0 |
| `final_label` nonempty | 0 |
| `silver_label_source` | `candidate_label_guess` (444) |
| `source_trace_complete` | 444 / 444 |

Domain distribution: autonomous_driving=140, policy_simulation=84, digital_twin=68, cyber_defense=64, marl=52, robotics=36.

**This is a controlled silver diagnostic study, not a gold benchmark.** The labels are silver (`candidate_label_guess`), not gold, and not human-audited. Results should not be interpreted as benchmark-level model validation.

[Source: data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv; docs/dataset_version_lock_v3_17.md; reports/current_project_status_v3_17.md]

---

## 7. Method

### 7.1 Retrieval

We run BM25 (k1=1.5, b=0.75) over a local PDF corpus of 69 PDFs (4747 chunks, ≈200 words per chunk with 50-word overlap). Query is `claim_text`. The chunk-level retrieval achieves oracle_match_rate = 0.991, recall@10 = 0.980, MRR = 0.826.

We additionally build a sentence/window corpus from the chunk corpus: 34643 sentences and 32250 windows. Sentence-level BM25 retrieval achieves recall@1 = 0.851, recall@5 = 0.932, recall@10 = 0.948, MRR = 0.883, outperforming window-level retrieval (recall@10 = 0.396, MRR = 0.324). Public artifacts are hash-only (no raw text); BM25 reads from a gitignored private corpus.

[Source: experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json; experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json; experiments/bm25_sentence_retrieval_v1/leakage_guard_report.json]

### 7.2 Evidence Canonicalization

Raw BM25 chunks are too long for the screening stage: 91% exceed 60 words. We propose deterministic canonicalizers that select or compose screening-format evidence from BM25 top-5 chunks:

- `raw_top1_chunk` (baseline): raw BM25 top-1 chunk.
- `best_sentence_top1_overlap`: single best sentence by claim overlap.
- `best_sentence_top5_overlap` (best): best sentence among top-5 chunks by overlap.
- `three_sentence_window_top5`: three-sentence window among top-5 chunks.

All canonicalizers are unsupervised, deterministic, and use only `claim_text` and the retrieved text — no labels, no oracle, no API calls.

[Source: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv; experiments/bm25_sentence_retrieval_v1/leakage_guard_report.json]

### 7.3 Frozen R4 Screening Router

We use a frozen R4 cascade (10 seeds, thresholds frozen at lock time). Per candidate, the router computes 7 NLI features + 9 action-gap features, then routes through:

1. contradiction: `clf_contra(nli_features) > t_contra` → `contradiction_candidate`
2. strong_action: `clf_strong(expert_features) > t_strong` → `strong_action_overclaim`
3. svm: `clf_svm(svm_features) > t_svm` → `mild_scope_overclaim`
4. else → `supported`

10-seed majority vote → final prediction. No training, no threshold change, no API. True labels are loaded only for metrics, never for prediction.

[Source: experiments/r4_minimal_recovery_v1/r4_recovery_gate.json; scripts/evaluate_r4_on_evidence_variants_v1.py]

### 7.4 Risk Ranking and Review Queue

We rank candidates by `priority_score = p_strong_mean − p_contra_mean + 0.5 × strong_action_flag` and evaluate 8 ranking variants. The best variant is `G_conservative_precision` (precision-optimized conservative formula). The queue is a second-stage review tool; **the system is a second-stage review queue generator, not a standalone detector.**

[Source: experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json; experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json]

---

## 8. Experiments

### 8.1 Canonicalizer Ablation

| Selector | oracle_recall | mean_overlap | pct_long_gt60 |
|---|---|---|---|
| raw_top1_chunk | 0.043 | 0.199 | 0.910 |
| cleaned_top1_chunk | 0.043 | 0.199 | 0.910 |
| first_sentence_top1 | 0.027 | 0.086 | 0.059 |
| best_sentence_top1_overlap | 0.221 | 0.319 | 0.052 |
| **best_sentence_top5_overlap** | **0.387** | **0.524** | **0.000** |
| three_sentence_window_top5 | 0.203 | 0.376 | 0.304 |

`best_sentence_top5_overlap` achieves 9x oracle_recall improvement over `raw_top1_chunk` (0.043 → 0.387) and produces screening-format-length evidence (0% exceed 60 words).

[Source: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv]

### 8.2 Frozen R4 Screening (group-aware bootstrap CI)

| Metric | Point estimate | 95% CI (group-aware, 100 bootstrap) |
|---|---|---|
| strong_precision | 0.330 | [0.301, 0.358] |
| strong_recall | 0.706 | [0.619, 0.780] |
| strong_F1 | 0.4503 | [0.4086, 0.4833] |
| macro_F1 | 0.385 | [0.348, 0.424] |

Computed on n=436 candidates (8 missing due to split). Silver labels used as `true_label` for metrics only.

[Source: experiments/metric_robustness_v1/classification_metrics_with_ci.csv; experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json]

### 8.3 Risk Ranking Variants

| Variant | precision@20 | precision@50 | recall@100 | average_precision |
|---|---|---|---|---|
| A_flag_only (baseline) | 0.35 | 0.36 | 0.330 | 0.356 |
| B_p_strong_desc | 0.35 | 0.32 | 0.303 | 0.332 |
| C_guarded_strong_score | 0.35 | 0.34 | 0.321 | 0.339 |
| D_confidence_guarded | 0.40 | 0.32 | 0.330 | 0.354 |
| E_selector_confidence | 0.35 | 0.36 | 0.275 | 0.335 |
| F_short_span_bonus | 0.40 | 0.32 | 0.330 | 0.351 |
| **G_conservative_precision** | **0.45** | 0.36 | 0.330 | 0.353 |
| H_balanced_review_score | 0.25 | 0.38 | 0.275 | 0.323 |

`G_conservative_precision` improves precision@20 from 0.35 (baseline) to 0.45 (+0.10), with negligible recall cost (recall@100: 0.330 vs 0.330). All variants miss the strict queue-utility targets; the queue is second-stage only.

[Source: experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv; experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json]

### 8.4 Review Queue Utility

| k | precision@k | recall@k | FP/TP | label composition (top-k) |
|---|---|---|---|---|
| 10 | 0.50 | 0.046 | 1.00 | strong=5, mild=4, supported=1 |
| 20 | 0.35 | 0.064 | 1.86 | mild=7, strong=7, supported=3, contradiction=3 |
| 50 | 0.34 | 0.156 | 1.94 | strong=17, mild=16, supported=10, contradiction=7 |
| 100 | 0.37 | 0.339 | 1.70 | strong=37, mild=29, supported=22, contradiction=12 |

`review_queue_usable = false`, `low_prevalence_usable = true`, `standalone_viable = false`, `second_stage_viable = true`. The queue is a second-stage review tool that augments human reviewers.

[Source: experiments/canonicalized_review_queue_v1/review_queue_metrics.csv; experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json]

### 8.5 Format-Shift Ablation (partial)

We constructed 8 format-shift variants × 444 candidates = 3552 rows and computed 7 NLI features per row (shape [3552, 7]). Variants include `oracle_clean`, `oracle_plus_metadata`, `oracle_lengthened`, `oracle_plus_metadata_lengthened`, `raw_bm25_top1_chunk`, `cleaned_bm25_top1_chunk`, `canonicalized_best_sentence_top5`, `canonicalized_three_sentence_window_top5`.

**Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch.** Frozen R4 classifiers were pickled with scikit-learn ≥1.5.0; the current offline environment has 1.4.1.post1 and cannot call `predict_proba` (`AttributeError: LogisticRegression object has no attribute 'multi_class'`). Upgrading requires network access, which violates the `no_network` boundary. We do not report unsupported R4 format-shift metrics.

[Source: experiments/format_shift_ablation_v1/format_shift_summary.json; experiments/format_shift_ablation_v1/r4_eval_blocked.json; reports/format_shift_r4_eval_blocked_v3_17.md]

---

## 9. Results

### 9.1 Headline numbers

- BM25 chunk retrieval: oracle_match_rate = 0.991, recall@10 = 0.980, MRR = 0.826 on 69 PDFs / 4747 chunks.
- BM25 sentence retrieval: recall@1 = 0.851, recall@10 = 0.948, MRR = 0.883.
- Best canonicalizer (`best_sentence_top5_overlap`): oracle_recall = 0.387 (9x over raw chunk 0.043).
- Frozen R4 screening: strong_F1 = 0.4503, 95% CI [0.4086, 0.4833].
- Best ranking variant (`G_conservative_precision`): precision@20 = 0.45, recall@100 = 0.330.

[Source: experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json; experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json; experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv; experiments/metric_robustness_v1/classification_metrics_with_ci.csv; experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json]

### 9.2 Complexity vs Utility Pareto

Under the confidential / no-API / no-training / silver-diagnostic constraint set, `deterministic_canonicalization`, `conservative_rule_queue`, and `lightweight_smart_queue` are Pareto-optimal. Learned alternatives (`learned_selector_only`, `learned_ranker_only`, `learned_selector_plus_learned_ranker`) are dominated: they match or slightly underperform the deterministic baseline on strong_F1 while losing on auditability, simplicity, and reproducibility. The external LLM baseline is unavailable under the no-API boundary.

This is a deployment-specific tradeoff. It does **not** prove that rules generally beat learned models; it shows that under this constraint set, the deterministic pipeline is Pareto-optimal.

[Source: experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv; experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv]

### 9.3 PDF Extraction Robustness

We ran a synthetic PDF extraction stress suite of 12 documents covering stress types (caption-like text, corrupted text, empty page, header/footer noise, hyphenation, long paragraph, page-number noise, reference-heavy, scanned-placeholder detect-only, table-like, two-column-like). 9 OK, 1 empty page, 1 scanned (detect-only), 1 corrupted (NUL cleaned), 0 failed. This is an engineering robustness test, not a SOTA claim.

[Source: experiments/pdf_extraction_stress_test_v1/stress_test_summary.md; experiments/pdf_extraction_stress_test_v1/stress_suite_manifest.csv]

---

## 10. Leakage and Shortcut Audits

We run a 12-check leakage audit. **Overall status: PASS.** Strongest leakage concern: none.

| # | Check | Status | Key metric |
|---|---|---|---|
| 1 | Claim-only baseline (TF-IDF+LR, GroupKFold) | pass | strong_F1=0.2448 (ratio to R4=0.5436, below 0.8 warning) |
| 2 | Empty evidence baseline | pass | correct_overlap=0.361 |
| 3 | Shuffled evidence baseline | pass | correct=0.361, shuffled=0.008 (46x collapse) |
| 4 | Title-only retrieval | pass | mean_overlap=0.043 |
| 5 | Metadata-only retrieval | pass | purity=0.25 |
| 6 | Lexical overlap by label | pass | overlap_ratio=1.344 |
| 7 | Cue words by label | pass | max_cue_ratio=1.608 |
| 8 | Label lexical cues | pass | max_cues=0 |
| 9 | Group split integrity | pass | cross_groups=0 |
| 10 | Generation policy distribution | pass | max_concentration=0.25 |
| 11 | No oracle in selector | pass | — |
| 12 | No label in queue sorting | pass | — |

Forbidden fields (selector): `candidate_label_guess`, `final_label`, `gold_label`, `human_audited`, `oracle_hit`, `true_label`. Forbidden fields (queue sorting): the same plus `evidence_text`, `evidence_text_sha256`, `is_strong_action`.

**This is a controlled silver diagnostic study, not a gold benchmark.** Silver labels (`candidate_label_guess`) are used as `true_label` for audit metrics only; the audit checks for shortcuts and label contingencies, not for gold-level validity.

[Source: experiments/leakage_audit_v1/audit_summary.md; experiments/leakage_audit_v1/claim_only_baseline.json]

### 10.1 Confidentiality Redteam Scan

A repo-wide confidentiality redteam scan finds 79 findings: 3 high-risk, 22 medium-risk, 54 low-risk. The 3 high-risk findings are `forbidden_sorting_field` (`true_label`, `oracle_hit`) in **internal scoring files** (`experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv`, `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv`). All three are excluded from the public release bundle. The release safety gate (bundle-only) PASS. The reconciliation report documents the scope difference: redteam scan is repo-wide (internal + public), release safety gate operates only on the public bundle.

[Source: experiments/confidentiality_redteam_scan_v1/redteam_summary.json; reports/redteam_release_reconciliation_v3_17.md; reports/release_safety_manifest_v3_17.json]

---

## 11. Error Taxonomy

We tag 9 error types over the R4 predictions (cases can carry multiple tags; percentages are of 188 error cases):

| Error type | n_cases | pct | FP | FN |
|---|---|---|---|---|
| mild_vs_strong_boundary | 73 | 38.83% | 66 | 7 |
| weak_selector_overlap | 65 | 34.57% | 59 | 6 |
| supported_overflag | 62 | 32.98% | 62 | 0 |
| group_variant_artifact | 53 | 28.19% | 51 | 2 |
| contradiction_confusion | 36 | 19.15% | 13 | 23 |
| action_lexicon_shortcut | 31 | 16.49% | 29 | 2 |
| evidence_format_noise | 22 | 11.70% | 13 | 9 |
| uncertainty_high_entropy | 22 | 11.70% | 12 | 10 |
| retrieval_miss | 5 | 2.66% | 5 | 0 |

The top FP cause is `mild_vs_strong_boundary` (66 FP, 38.83%), reflecting the inherent ambiguity of the mild-vs-strong boundary rather than a systematic shortcut. The top FN cause is `uncertainty_high_entropy` (10 FN) and `contradiction_confusion` (23 FN). Error-type thresholds are heuristic, not learned.

[Source: experiments/error_taxonomy_v1/error_taxonomy_summary.csv]

---

## 12. Review Queue Utility

The review queue is a **second-stage review tool**. The pipeline gate confirms: `review_queue_usable = false`, `low_prevalence_usable = true`, `standalone_viable = false`, `second_stage_viable = true`. The recommended mode is `second-stage`.

At the top of the queue, precision@10 = 0.50 and precision@20 = 0.45 (with `G_conservative_precision`), meaning roughly half of the top-10 and top-20 candidates are true strong-action overclaims under silver labels. FP/TP ratios are 1.00 at top-10 and 1.86 at top-20 — usable for prioritizing reviewer attention, not for automated decisions.

A small targeted human audit protocol (2-annotator independent review followed by adjudication) is staged with 6 sampling buckets: top-20 queue, top-50 strong-action, R4 false positives, R4 false negatives, mild-vs-strong boundary cases, contradiction confusion cases. The protocol, template, and redacted seed queue are prepared. **The audit has not been executed.** We do not report human-audited benchmark results.

[Source: experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json; experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json; docs/human_audit_protocol_v1.md; data/audit_templates/human_audit_queue_seed_v1_redacted.csv; reports/final_perfect_state_gate_v3_17.md]

---

## 13. Limitations

1. **Silver labels, not gold.** All 444 candidates have `human_audited=False` and `gold_label` empty. Silver labels (`candidate_label_guess`) are used as `true_label` for metrics only. **This is a controlled silver diagnostic study, not a gold benchmark.**
2. **Human audit staged, not executed.** A small targeted human audit protocol and seed queue are prepared; the audit has not been executed. We do not report human-audited benchmark results. Paper wording: "small targeted human audit protocol and seed queue prepared; audit not yet executed."
3. **Format-shift R4 metrics not reported.** **Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch.** Variant construction (3552 rows, 8 variants) and NLI feature extraction completed; R4 prediction blocked. Fix requires network/pip install, which violates the `no_network` boundary.
4. **Six domains only.** Coverage: autonomous_driving (140), policy_simulation (84), digital_twin (68), cyber_defense (64), marl (52), robotics (36). Not a general scientific claim benchmark.
5. **Deployment-specific Pareto result.** The complexity-vs-utility Pareto result shows deterministic canonicalization is optimal under the confidential / no-API / no-training / silver-diagnostic constraint set. It does **not** prove rules generally beat learned models.
6. **No SOTA claim.** We do not claim SOTA on simulation-claim screening. We do not claim a validated general detector. We do not claim an automatic peer reviewer. We do not claim full CESE-OCN neural architecture validation.
7. **CI reflects controlled pool variability, not natural prevalence.** Bootstrap CIs are group-aware (group-level resampling, 100 bootstrap iterations) over the controlled 444-candidate pool. They do not estimate performance under natural prevalence.
8. **Redteam high-risk findings are internal-only.** 3 high-risk `forbidden_sorting_field` findings exist in internal scoring files. They are excluded from the public release bundle; the release safety gate PASS.

[Source: docs/dataset_version_lock_v3_17.md; reports/format_shift_r4_eval_blocked_v3_17.md; docs/human_audit_protocol_v1.md; experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv; experiments/metric_robustness_v1/classification_metrics_with_ci.csv; reports/redteam_release_reconciliation_v3_17.md]

---

## 14. Ethics / Confidentiality / Release Policy

### 14.1 Confidentiality as a deployment constraint

The deployment setting prohibits API egress, network access, and new model training. All retrieval, screening, and ranking run locally. **Confidentiality is a deployment constraint, not the empirical contribution.** The empirical contribution is the identification and bridging of the retrieval-to-screening format shift.

### 14.2 Public release policy

The public sanitized release bundle (221 files) excludes: raw claim/evidence/PDF text, private scoring files, real review queues, PDFs, label-bearing intermediates, and unredacted selected_evidence. Public PDF corpus artifacts (`data/pdf_corpus_v1/sentences.jsonl`, `windows.jsonl`) are hash-only; full text resides in a gitignored private directory.

Forbidden columns for public release: `claim_text`, `evidence_text`, `selected_evidence`, `raw_text`, `clean_text`, `body_text`, `pdf_text`, `pdf_path`. Forbidden sorting fields: `true_label`, `oracle_hit`, `candidate_label_guess`, `gold_label`, `human_audited`, `final_label`, `is_strong_action`.

### 14.3 No silver-as-gold

The controlled silver diagnostic set is locked at version v3_17. Any change to the locked CSV requires updating the dataset lock document and associated tests. `final_label` and `gold_label` are not populated. `human_audited` is not set to true. The 444-candidate set is never described as a gold benchmark, human-audited dataset, or validated general detector.

[Source: reports/release_safety_manifest_v3_17.json; reports/redteam_release_reconciliation_v3_17.md; docs/dataset_version_lock_v3_17.md; reports/current_project_status_v3_17.md]

---

## 15. Conclusion

We identified the retrieval-to-screening format shift in offline simulation-claim review: raw BM25 PDF chunks are too long and noisy to match screening-format evidence (oracle_recall = 0.043, 91% exceed 60 words). We proposed deterministic evidence canonicalization (`best_sentence_top5_overlap`) as a no-API, no-training bridge, raising oracle_recall to 0.387 (9x improvement) while producing screening-format-length evidence.

On a 444-candidate controlled silver diagnostic set, a frozen R4 screening router achieves strong_F1 = 0.4503 (95% CI [0.4086, 0.4833]) and a conservative precision-optimized review queue achieves precision@20 = 0.45. A 12-check leakage audit finds no significant shortcuts or label contingencies. Under the confidential / no-API / no-training / silver-diagnostic constraint set, the deterministic pipeline is Pareto-optimal against learned alternatives.

**This is a controlled silver diagnostic study, not a gold benchmark.** The system is a second-stage review queue generator, not a standalone detector. Confidentiality is a deployment constraint, not the empirical contribution. Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch. The human audit is staged, not executed.

We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architecture validation.

[Source: reports/final_perfect_state_gate_v3_17.md; reports/current_project_status_v3_17.md]

---

## Appendix A. Result Source Map

| Result | Source file |
|---|---|
| Dataset 444 / 111 / 4 labels | docs/dataset_version_lock_v3_17.md |
| BM25 chunk retrieval metrics | experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json |
| BM25 sentence/window retrieval | experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json |
| Canonicalizer ablation | experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv |
| R4 screening CI | experiments/metric_robustness_v1/classification_metrics_with_ci.csv |
| R4 review queue gate | experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json |
| Risk ranking variants | experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv |
| Risk ranking gate | experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json |
| Review queue metrics | experiments/canonicalized_review_queue_v1/review_queue_metrics.csv |
| Leakage audit | experiments/leakage_audit_v1/audit_summary.md |
| Claim-only baseline | experiments/leakage_audit_v1/claim_only_baseline.json |
| Error taxonomy | experiments/error_taxonomy_v1/error_taxonomy_summary.csv |
| Complexity vs utility Pareto | experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv |
| Method comparison | experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv |
| PDF stress test | experiments/pdf_extraction_stress_test_v1/stress_test_summary.md |
| Format-shift block | reports/format_shift_r4_eval_blocked_v3_17.md |
| Human audit protocol | docs/human_audit_protocol_v1.md |
| Final gate | reports/final_perfect_state_gate_v3_17.md |
| Redteam reconciliation | reports/redteam_release_reconciliation_v3_17.md |
| Release safety | reports/release_safety_manifest_v3_17.json |
| Project status | reports/current_project_status_v3_17.md |

---

## Appendix B. Mandatory Safe Wording (audit checklist)

The following safe wording is used in this manuscript:

- "This is a controlled silver diagnostic study, not a gold benchmark."
- "The system is a second-stage review queue generator, not a standalone detector."
- "Confidentiality is a deployment constraint, not the empirical contribution."
- "Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch."
- "small targeted human audit protocol and seed queue prepared; audit not yet executed"
- "We do not claim SOTA, a validated general detector, an automatic peer reviewer, or full CESE-OCN neural architecture validation."

The following forbidden wording is **not** used in this manuscript:

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "validated general detector" | The system is a second-stage review queue generator, not a validated general detector. |
| "gold benchmark" | The dataset is a controlled silver diagnostic set, not a gold benchmark. |
| "human-audited dataset" | All 444 rows have `human_audited=False`; the audit is staged, not executed. |
| "SOTA" (as a positive claim) | We do not claim SOTA on simulation-claim screening. |
| "automatic peer reviewer" | The system augments human reviewers; it is not an automatic peer reviewer. |
| "full CESE-OCN validation completed" | CESE-OCN is a future architecture, not a current validated system. |
| "full format-shift R4 evaluation completed" | Format-shift R4 prediction is blocked by sklearn version mismatch. |
| "Canonicalized format-shift metrics are validated" | Format-shift R4 metrics are not reported. |
| "R4 format-shift result is final" | Format-shift R4 metrics are not reported. |

---

*End of submission manuscript draft v1.*
