# Mainline Evidence Map — 主线证据地图

**Date:** 2026-07-05
**Selected mainline:** V3.17 baseline (offline PDF-corpus evidence-sufficiency screening)
**Organization:** claim → evidence → metric → source path

---

## Claim 1: PDF retrieval is feasible

**Claim:** BM25 top-k retrieval over a scientific PDF corpus produces candidate evidence chunks usable by downstream screening.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Raw BM25 top1 chunk produces non-trivial R4 signal | strong_F1 | 0.1806 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` (row: raw_bm25_top1_chunk) |
| Raw BM25 top1 recall | strong_recall | 0.1193 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` |
| PDF corpus retrieval pipeline executed | n_candidates | 444 | `experiments/simclaim_pdf_corpus_retrieval_v1/simclaim_pdf_retrieval_gate.json` |
| Best canonicalized format beats raw | canonicalization_gain | +0.2697 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` |

---

## Claim 2: Raw retrieved chunks degrade R4 screening

**Claim:** Raw BM25 top1 chunks feed R4 a strong_F1 of only 0.1806, well below the oracle-span strong_F1 of 0.4257. The format shift (metadata + length + multi-sentence concatenation) is the dominant cause.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Raw BM25 top1 strong_F1 | strong_F1 | 0.1806 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` |
| Oracle span strong_F1 (upper bound) | strong_F1 | 0.4257 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` (row: oracle_span) |
| Raw-to-oracle gap | strong_F1 gap | -0.2451 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` |
| Format shift confirmed (ablation) | oracle_with_metadata drop | 0.0101 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (ablation_metadata_drop) |
| Format shift confirmed (ablation) | oracle_lengthened drop | 0.3320 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (ablation_lengthening_drop) |
| Main bottleneck identified | bottleneck | format_shift | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (main_bottleneck) |
| Cleaned top1 chunk (still degrades) | strong_F1 | 0.2282 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` (row: cleaned_top1_chunk) |

---

## Claim 3: Evidence canonicalization restores strong_action screening

**Claim:** `best_sentence_top5_overlap` canonicalization restores strong_F1 to 0.4503, a +0.2697 gain over raw BM25 top1, and is only -0.0246 below oracle span. Evidence canonicalization is the critical bridge between BM25 retrieval and R4 screening.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Best canonicalized format | best_canonical_format | best_sentence_from_top5 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` |
| Best canonicalized strong_F1 | strong_F1 | 0.4503 | `experiments/r4_evidence_canonicalization_v1/r4_metrics_by_format.csv` (row: best_sentence_from_top5) |
| Canonicalization gain vs raw | gain | +0.2697 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (canonicalization_gain_vs_raw) |
| Oracle-to-best gap | gap | -0.0246 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (oracle_to_best_gap) |
| Canonicalization improves over raw | flag | true | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (canonicalization_improves_over_raw) |
| Supports V3.17 mainline | flag | true | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (supports_v3_17_mainline) |
| Supports PDF corpus screening claim | flag | true | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (supports_pdf_corpus_screening_claim) |
| Canon helped (raw wrong, canon right) | n_candidates | 129 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_report.md` (Canon helped) |
| Canon harmed (raw right, canon wrong) | n_candidates | 3 | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_report.md` (Canon harmed) |

---

## Claim 4: Selector robustness (simple overlap-based canonicalization is robust)

**Claim:** The V3.18 intelligent upgrade attempted to replace the handcrafted overlap selector with sklearn learned models. The learned selector did NOT improve over the simple overlap selector. Simple overlap-based canonicalization is the robust choice under the current feature space.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| V3.17 baseline selector (overlap) strong_F1 | strong_F1 | 0.4503 | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` (best_sentence_top5_overlap_strong_f1) |
| V3.18 learned selector strong_F1 | strong_F1 | 0.4444 | `experiments/v3_18_intelligent_upgrade_v1/learned_selector_metrics.csv` |
| Selector upgrade gap | gap | -0.0059 | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (learned_selector_strong_f1 - baseline_strong_f1) |
| Selector upgrade passed | flag | false | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (selector_upgrade_passed) |
| Learned selector matches baseline on | n_candidates | 285/444 | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_report.md` (Learned selector matches baseline) |
| Selectors above 0.40 (robustness) | n_formats | 6/9 | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` (selectors_above_0.40) |
| Best learned selector model | model | rf | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (selector_best_model) |
| Selector robustness diagnostic gate | — | — | `experiments/canonical_selector_robustness_v1/selector_robustness_gate.json` |

---

## Claim 5: Second-stage review queue (R4 is second-stage, not standalone)

**Claim:** R4 is positioned as an offline, auditable, second-stage strong_action screening router. Standalone viability is false; second-stage viability is true.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Standalone viable (FP/TP @ 1% ≤ 50) | flag | false | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (standalone_viable) |
| Second-stage viable (FP/TP @ 5% ≤ 20 AND recall ≥ 0.6) | flag | true | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (second_stage_viable) |
| Recommended mode | mode | second-stage | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (recommended_mode) |
| FP/TP @ 1% prevalence | FP/TP | 66.82 | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (fp_tp_at_1pct) |
| FP/TP @ 5% prevalence | FP/TP | 12.84 | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (fp_tp_at_5pct) |
| FP/TP @ 10% prevalence | FP/TP | 6.07 | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (fp_tp_at_10pct) |
| Best ranking variant | variant | G_conservative_precision | `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (best_variant) |
| Best ranking P@20 | P@20 | 0.45 | `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (best_precision_at20) |
| Best ranking R@100 | R@100 | 0.3303 | `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (best_recall_at100) |
| Priority score formula | formula | p_strong_mean - p_contra_mean + 0.5 * strong_action_flag | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (priority_score_formula) |
| Review queue top-100 | file | — | `experiments/canonicalized_risk_ranking_v1/review_queue_top100_best.csv` |

---

## Claim 6: Learned upgrade negative ablation (V3.18 did not improve)

**Claim:** V3.18 attempted learned evidence selector + learned risk ranker as an upgrade over V3.17 baseline. Both modules failed to improve. V3.18 is retained as an exploratory negative result and is NOT the selected main method.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Selector upgrade passed | flag | false | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` |
| Ranker upgrade passed | flag | false | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` |
| Best overall method | method | V3.17_baseline | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (best_overall_method) |
| Supports V3.18 intelligent upgrade | flag | false | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (supports_v3_18_intelligent_upgrade) |
| Learned selector strong_F1 | strong_F1 | 0.4444 | `experiments/v3_18_intelligent_upgrade_v1/learned_selector_metrics.csv` |
| Learned ranker P@20 | P@20 | 0.35 | `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` |
| Learned ranker R@100 | R@100 | 0.3303 | `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` |
| Learned ranker FP/TP @ 5% | FP/TP | 2.00 | `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` |
| Learned ranker AP | AP | 0.3720 | `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` |
| Learned ranker AUC | AUC | 0.6740 | `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` |
| Best ranker model | model | logreg | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (ranker_best_model) |
| 5-method comparison table | file | — | `experiments/v3_18_intelligent_upgrade_v1/intelligent_upgrade_comparison_table.csv` |
| Error analysis (per-candidate) | file | — | `experiments/v3_18_intelligent_upgrade_v1/intelligent_upgrade_error_analysis.csv` |
| No test leakage | flag | true | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (no_test_leakage) |

---

## Claim 7: R4 macro_F1 lower than LLM, but R4 captures Level-2 strong_action signal

**Claim:** R4 macro_F1 is lower than LLM judges. The paper does NOT claim R4 overall beats LLM. R4 provides targeted Level-2 strong_action screening signal.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| R4 historical macro_F1 (silver 444) | macro_F1 | 0.4238 | `experiments/mixed_framework_v2_frozen_r4_baseline/frozen_r4_metrics_summary.json` (R4_conservative_strong.flat4_macro_f1) |
| R4 historical strong_F1 (silver 444) | strong_F1 | 0.3967 | `experiments/mixed_framework_v2_frozen_r4_baseline/frozen_r4_metrics_summary.json` (R4_conservative_strong.flat4_strong_f1) |
| R4 historical strong_recall (silver 444) | strong_recall | 0.4562 | `experiments/mixed_framework_v2_frozen_r4_baseline/frozen_r4_metrics_summary.json` (R4_conservative_strong.strong_recall) |
| DeepSeek-V3 LLM macro_F1 (200 samples) | macro_F1 | 0.5270 | `experiments/llm_judge_baseline_v1/llm_metrics_200.json` (flat4_macro_f1) |
| DeepSeek-V3 LLM strong_F1 (200 samples) | strong_F1 | 0.0769 | `experiments/llm_judge_baseline_v1/llm_metrics_200.json` (flat4_strong_f1) |
| DeepSeek-V3 LLM strong_recall (200 samples) | strong_recall | 0.04 | `experiments/llm_judge_baseline_v1/llm_metrics_200.json` (strong_recall) |
| GPT-5.5 standard macro_F1 (100 samples) | macro_F1 | 0.5523 | `experiments/gpt_structured_judge_probe_v1/gpt_standard_metrics_100.json` (flat4_macro_f1) |
| GPT-5.5 standard strong_F1 (100 samples) | strong_F1 | 0.0769 | `experiments/gpt_structured_judge_probe_v1/gpt_standard_metrics_100.json` (flat4_strong_f1) |
| GPT-5.5 standard strong_recall (100 samples) | strong_recall | 0.04 | `experiments/gpt_structured_judge_probe_v1/gpt_standard_metrics_100.json` (strong_recall) |
| GPT-5.5 structured macro_F1 (100 samples) | macro_F1 | 0.5543 | `experiments/gpt_structured_judge_probe_v1/gpt_structured_metrics_100.json` (flat4_macro_f1) |
| V3.17 baseline strong_recall (current mainline) | strong_recall | 0.7064 | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` |
| LLM strong_recall (matched 100) | strong_recall | 0.04 | `experiments/gpt_structured_judge_probe_v1/gpt_standard_metrics_100.json` |
| R4 vs LLM strong_recall gap | gap | +0.6664 | Computed: 0.7064 - 0.04 (V3.17 baseline vs LLM) |

---

## Claim 8: SimClaim is a controlled silver diagnostic test set

**Claim:** SimClaim is a controlled counterfactual diagnostic set, NOT a natural-prevalence corpus. Silver labels; gold adjudication pending.

| Evidence | Metric | Value | Source path |
|---|---|---|---|
| Total candidate pairs | n_pairs | 444 | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| Evidence groups | n_groups | 111 | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| Domains | n_domains | 6 | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| Label balance | balance | 1:1:1:1 | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` |
| Safe as diagnostic set | flag | true | Overnight pipeline Task A; `project_synthesis/current_project_state_consolidation_clean_v1/current_mainline_assessment.md` |
| Safe as naturalistic | flag | false | Overnight pipeline Task A |
| TF-IDF leakage gap | gap | -0.0066 | Overnight pipeline Task A (low leakage) |
| Gold adjudication status | status | NOT begun | `project_synthesis/current_project_state_consolidation_clean_v1/current_mainline_assessment.md` |

---

## Cross-reference: realignment docs

For the full realignment context, see `D:\ocn\project_synthesis\mainline_realignment_v1\`:
- `updated_project_mainline_summary.md`
- `updated_allowed_forbidden_claims.md`
- `updated_reproducibility_note.md`
- `mainline_realignment_change_log.md`
- `mainline_realignment_gate.json`
