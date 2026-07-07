# V3.17 Final Delivery Manifest

> **Mandatory framing.** Controlled silver diagnostic study, not a gold benchmark. Not SOTA. Not an automatic peer reviewer. Not a validated general detector.

Generated: 2026-07-08
Mainline: V3.17 Confidential Lightweight
Remote HEAD: `adcf485eeb9621fbd828ec7741ab508f66c8f9eb`

## Summary

| Metric | Count |
|---|---|
| Total items | 36 |
| Public-safe | 32 |
| Private-sensitive | 4 |
| Included in delivery | 31 |
| Excluded from delivery | 5 |
| Human audit executed | false |

## Delivery items

| Path | public_safe | private_sensitive | source_of_truth | include_in_delivery | notes |
|---|---|---|---|---|---|
| paper_assets/v3_17_confidential/submission_manuscript_v1.md | true | false | paper_assets/v3_17_confidential | true | Submission manuscript v2 Final Freeze; 15-section structure; all numbers have source notes |
| paper_assets/v3_17_confidential/submission_result_source_map.csv | true | false | paper_assets/v3_17_confidential | true | 80 result rows (R-01..R-80) mapping every claim to source file with source_status |
| paper_assets/v3_17_confidential/tables/table1_dataset_summary.md | true | false | docs/dataset_version_lock_v3_17.md | true | Dataset summary; 444 rows, 111 groups, 4 labels, 6 domains |
| paper_assets/v3_17_confidential/tables/table2_retrieval_recall.md | true | false | experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json | true | BM25 chunk/sentence/window retrieval recall |
| paper_assets/v3_17_confidential/tables/table3_format_shift_ablation.md | true | false | experiments/format_shift_ablation_v1/format_shift_metrics.csv | true | 8 format-shift variants from real metrics; no blocked wording; resolved offline sklearn 1.9.0 |
| paper_assets/v3_17_confidential/tables/table4_canonicalizer_ablation.md | true | false | experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv | true | Canonicalizer ablation; best_sentence_top5_overlap oracle_recall=0.387 |
| paper_assets/v3_17_confidential/tables/table5_review_queue.md | true | false | experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv | true | 8 ranking variants; best G_conservative_precision precision@20=0.45; second-stage only |
| paper_assets/v3_17_confidential/tables/table6_leakage_audit.md | true | false | experiments/leakage_audit_v1/audit_summary.md | true | 12-check leakage audit; overall PASS |
| paper_assets/v3_17_confidential/tables/table7_complexity_utility.md | true | false | experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv | true | Pareto analysis; 3 pareto_optimal deterministic methods |
| paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md | true | false | docs/human_audit_protocol_v1.md | true | Human audit status: STAGED not executed; no human-audited benchmark results reported |
| docs/reviewer_response_playbook_v3_17.md | true | false | docs | true | Reviewer response playbook |
| docs/reviewer_risk_register_v3_17.md | true | false | docs | true | Reviewer risk register |
| reports/final_perfect_state_gate_v3_17.md | true | false | reports/final_perfect_state_gate_v3_17.json | true | Final gate: PASS=42 WARNING=2 BLOCKED=0 FAIL=0 |
| reports/final_perfect_state_gate_v3_17.json | true | false | scripts/run_final_perfect_state_gate_v1.py | true | Machine-readable final gate |
| release_bundles/v3_17_confidential_public/MANIFEST.json | true | false | release_bundles/v3_17_confidential_public | true | Public release bundle manifest; 254 files; SHA-256 per file |
| release_bundles/v3_17_confidential_public/REDACTION_REPORT.json | true | false | scripts/build_public_sanitized_release_v1.py | true | Redaction report; redteam_pass=true; no PDF/raw text |
| reports/artifact_ledger_v3_17.md | true | false | reports/artifact_ledger_v3_17.csv | true | Artifact ledger; 54 artifacts |
| reports/artifact_ledger_v3_17.csv | true | false | scripts/build_artifact_ledger_v1.py | true | Machine-readable artifact ledger |
| experiments/human_audit_v1/audit_agreement_summary.json | true | false | experiments/human_audit_v1 | **false** | **NOT AVAILABLE** — human audit staged, not executed; file does not exist |
| experiments/format_shift_ablation_v1/format_shift_metrics.csv | true | false | experiments/format_shift_ablation_v1 | true | Real format-shift metrics; 8 variants; canonicalized strong_F1=0.4615; diagnostic not benchmark |
| reports/redteam_release_reconciliation_v3_17.md | true | false | reports/redteam_release_reconciliation_v3_17.json | true | Redteam reconciliation; 84 findings repo-wide, 0 in release bundle |
| docs/dataset_version_lock_v3_17.md | true | false | docs | true | Dataset version lock; SHA256, 444 rows, 36 cols; controlled silver diagnostic |
| reports/v3_17_one_page_status_card.md | true | false | reports | true | One-page status card; project status, key results, limitations, claims boundaries |
| reports/release_safety_manifest_v3_17.json | true | false | scripts/build_artifact_ledger_v1.py | true | Release safety manifest; 54 artifacts; 46 safe-to-release; gate PASS |
| reports/current_project_status_v3_17.md | true | false | scripts/generate_project_status_report_v1.py | true | Current project status; format-shift resolved |
| docs/safe_claims_dictionary_v3_17.md | true | false | docs | true | Safe claims dictionary; approved wording |
| docs/reproducibility_guide_v3_17.md | true | false | docs | true | Reproducibility guide |
| docs/result_narrative_freeze_v3_17.md | true | false | docs | true | Result narrative freeze; frozen numbers |
| artifacts_manifest_v3_17.yaml | true | false | artifacts_manifest_v3_17.yaml | true | Artifact manifest definitions; 54 artifact groups |
| experiments/leakage_audit_v1/audit_summary.md | true | false | experiments/leakage_audit_v1 | true | Leakage audit summary; 12 checks; PASS |
| experiments/metric_robustness_v1/classification_metrics_with_ci.csv | true | false | experiments/metric_robustness_v1 | true | R4 classification metrics with bootstrap CIs; strong_F1=0.4503 |
| experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv | true | false | experiments/canonicalizer_ablation_v1 | true | Canonicalizer selector metrics; no raw text columns |
| experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv | true | false | experiments/canonicalized_risk_ranking_v1 | true | Risk ranking results by variant; aggregate metrics only |

## Private-sensitive items (NEVER in delivery)

| Path | public_safe | private_sensitive | source_of_truth | include_in_delivery | notes |
|---|---|---|---|---|---|
| data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv | false | true | data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1 | false | PRIVATE — controlled silver dataset CSV with raw claim_text/evidence_text; never in delivery bundle |
| data/private_audit/v3_17_audit_packet/audit_packet_private.csv | false | true | data/private_audit/v3_17_audit_packet | false | PRIVATE — human audit packet with raw claim/evidence text; gitignored; never in delivery bundle |
| experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv | false | true | experiments/canonicalized_review_queue_v1 | false | PRIVATE — review queue scores with selected_evidence column; never in delivery bundle |
| experiments/canonicalized_review_queue_v1/review_queue_top100.csv | false | true | experiments/canonicalized_review_queue_v1 | false | PRIVATE — review queue top-100 with claim_text/selected_evidence; never in delivery bundle |

## Hard delivery boundaries

- No private audit CSV (`data/private_audit/`).
- No PDFs (`*.pdf`).
- No raw claim/evidence text (`claim_text`, `evidence_text`, `selected_evidence`, `raw_text`).
- No pkl/joblib/model artifacts (`*.pkl`, `*.joblib`, `*.npz`).
- No `data/private/`.
- No `data/private_audit/`.
- No `*.docx`, `*.xlsx`.
- No unredacted CSV with text columns.
- No silver-as-gold claims; no SOTA; no automatic peer reviewer; no general detector claims.
