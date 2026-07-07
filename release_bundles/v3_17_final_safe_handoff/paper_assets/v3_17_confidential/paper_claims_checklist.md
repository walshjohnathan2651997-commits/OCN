# Paper Claims Checklist — V3.17 Confidential

> Controlled silver diagnostic, not gold/human-audited.

## Required Caveat Items

| # | Required statement | Present |
|---|---|---|
| C1 | not gold | YES (see U6, S5 bound) |
| C2 | not human-audited benchmark | YES (see U7, S8) |
| C3 | not SOTA | YES (see U8) |
| C4 | not automatic peer review | YES (see U9) |
| C5 | not full CESE-OCN validation | YES (see U10) |
| C6 | second-stage review queue only | YES (see S6) |
| C7 | retrieval-to-screening format shift supported | YES (see S7) |
| C8 | canonicalization supported | YES (see S1) |

## Safe Claims (Supported)

### S1: Canonicalization supported — evidence canonicalization improves over raw BM25 chunks
- **Supported?**: YES
- **Evidence file**: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv (Table 4)
- **Safe wording**: "On the controlled silver diagnostic, evidence canonicalization (best_sentence_top5_overlap) yields higher oracle recall than raw_top1_chunk, supporting canonicalization as a recovery step."
- **Unsafe wording**: "Canonicalization always improves retrieval." / "Canonicalization is necessary for all datasets."
- **Bound**: Limited to silver diagnostic data; not generalizable to gold-standard.

### S2: Frozen R4 screening achieves strong_F1 ≈ 0.45 with group-aware bootstrap CI
- **Supported?**: YES
- **Evidence file**: experiments/metric_robustness_v1/classification_metrics_with_ci.csv (Table 5)
- **Safe wording**: "On the controlled silver diagnostic, frozen R4 screening achieves strong_F1 ≈ 0.45 with group-aware bootstrap 95% CI."
- **Unsafe wording**: "The system achieves F1=0.45 in production." / "strong_F1=0.45 generalizes to real data."
- **Bound**: CI is group-aware (resampled by target_candidate_group_id); reflects controlled balanced pool.

### S3: No label leakage in queue sorting or selector
- **Supported?**: YES
- **Evidence file**: experiments/leakage_audit_v1/*.json (Table 6)
- **Safe wording**: "Leakage audit on the V3.17 frozen code path confirms true_label and oracle_hit are not used for queue sorting or selector choice."
- **Unsafe wording**: "No confidentiality leaks exist." / "The system is provably leak-free."
- **Bound**: Audit covers the V3.17 frozen code path; future code changes require re-audit.

### S4: Sentence-level retrieval outperforms window-level on oracle recall
- **Supported?**: YES
- **Evidence file**: experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json (Table 2)
- **Safe wording**: "Under BM25 with the current PDF corpus, sentence-level retrieval yields higher oracle recall@1 and MRR than window-level."
- **Unsafe wording**: "Sentence retrieval beats window retrieval universally." / "BM25 beats neural retrievers."
- **Bound**: Limited to BM25 with the current PDF corpus; neural retrievers may differ.

### S5: Dataset is silver diagnostic, not gold
- **Supported?**: YES (structural fact)
- **Evidence file**: data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv (human_audited=False for all rows)
- **Safe wording**: "The 444-candidate dataset is a controlled silver diagnostic with human_audited=False; it is not a gold benchmark."
- **Unsafe wording**: "Gold-standard evaluation set." / "Human-verified benchmark."
- **Bound**: All quantitative results must be qualified as silver-label diagnostic.

### S6: Second-stage review queue only (not a standalone detector)
- **Supported?**: YES
- **Evidence file**: experiments/canonicalized_review_queue_v1/, experiments/lightweight_smart_queue_v1/smart_queue_metric_summary.json
- **Safe wording**: "The pipeline produces a second-stage review queue that augments human review; it is not a standalone automatic detector."
- **Unsafe wording**: "The system detects simulation claim overclaims automatically." / "The pipeline replaces human review."
- **Bound**: Human adjudication remains the gold standard; the queue only prioritizes cases for review.

### S7: Retrieval-to-screening format shift is supported
- **Supported?**: YES
- **Evidence file**: experiments/format_shift_ablation_v1/format_shift_inputs.csv (Table 3), experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv (Table 4)
- **Safe wording**: "Format shift (metadata, lengthening) between PDF retrieval and downstream screening is characterized; canonicalization mitigates the resulting signal loss."
- **Unsafe wording**: "Format shift is fully solved." / "Canonicalization eliminates all retrieval-to-screening gap."
- **Bound**: Mitigation, not elimination; gap remains and is reported.

### S8: Small targeted human audit protocol is in place (not a full benchmark)
- **Supported?**: YES (protocol exists; empirical results may be pending)
- **Evidence file**: docs/human_audit_protocol_v1.md, data/audit_templates/human_audit_template.csv, experiments/human_audit_v1/audit_agreement_summary.json (if completed)
- **Safe wording**: "A small targeted human audit protocol is defined to verify directional reliability of top queue and strong_action labels; it is not a human-audited benchmark."
- **Unsafe wording**: "Human-validated benchmark." / "Gold-standard audit."
- **Bound**: Small targeted audit (80–120 candidates); not a gold benchmark; not a full human-audited benchmark.

## Unsafe Claims (Do NOT make)

### U1: "The system detects real-world simulation claim overclaims."
- **Why unsafe**: System is a review queue generator, not a standalone detector. Silver labels only.

### U2: "strong_F1 of 0.45 generalizes to production data."
- **Why unsafe**: Controlled balanced 4-class pool. Natural prevalence is unknown.

### U3: "The pipeline replaces human review."
- **Why unsafe**: Pipeline augments human review; does not replace it. Human adjudication is gold standard.

### U4: "Bootstrap CI reflects real-world uncertainty."
- **Why unsafe**: CI reflects sampling variability in the controlled pool, not population prevalence.

### U5: "No confidentiality leaks exist."
- **Why unsafe**: Red-team scanner checks known patterns; cannot guarantee zero leaks. Continuous auditing needed.

### U6: "This is a gold benchmark."  (violates: not gold)
- **Why unsafe**: All rows have human_audited=False; gold_label is empty. Silver diagnostic only.

### U7: "This is a human-audited benchmark."  (violates: not human-audited benchmark)
- **Why unsafe**: No full human audit has been completed. Only a small targeted audit protocol exists.

### U8: "The pipeline achieves SOTA on simulation claim overclaim detection."  (violates: not SOTA)
- **Why unsafe**: No comparison to other systems on a shared benchmark; silver diagnostic, not gold.

### U9: "The pipeline performs automatic peer review."  (violates: not automatic peer review)
- **Why unsafe**: Pipeline produces a review queue for human reviewers; it does not perform peer review automatically.

### U10: "This constitutes full CESE-OCN validation."  (violates: not full CESE-OCN validation)
- **Why unsafe**: V3.17 confidential lightweight is a scoped subset; full CESE-OCN validation requires additional stages, gold labels, and human adjudication not present here.

### U11: "Rules generally beat learned models."  (complexity-vs-utility bound)
- **Why unsafe**: Pareto analysis is deployment-specific (confidential/no-API/no-training/silver diagnostic). It does not support a general claim about rules vs. learned models.

## Evidence Index

| Claim | Evidence File | Table/Figure |
|---|---|---|
| S1 (canonicalization supported) | selector_metrics_summary.csv | Table 4 |
| S2 (strong_F1 ≈ 0.45) | classification_metrics_with_ci.csv | Table 5 |
| S3 (no leakage) | leakage_audit_v1/*.json | Table 6 |
| S4 (sentence > window) | oracle_recall_summary.json | Table 2 |
| S5 (silver, not gold) | strict_silver_max_candidates_v1.csv | Table 1 |
| S6 (second-stage queue only) | smart_queue_metric_summary.json | Table 5 |
| S7 (format shift supported) | format_shift_inputs.csv | Table 3 |
| S8 (audit protocol, not benchmark) | human_audit_protocol_v1.md | Table 8 |

> Controlled silver diagnostic, not gold/human-audited.