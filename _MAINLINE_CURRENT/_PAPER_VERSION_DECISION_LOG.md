# Paper Version Decision Log — 版本决策记录

**Date:** 2026-07-05
**Scope:** V3.15 / V3.16 / V3.17 / V3.18
**Purpose:** 记录每个版本的角色、状态、为何被选中或拒绝、关键证据

---

## V3.15 — Hierarchical Taxonomy Revision

| Field | Value |
|---|---|
| **version** | V3.15 |
| **role** | Paper-level interpretation framework (hierarchical diagnostic taxonomy) |
| **status** | historical (retained as paper-level interpretation; NOT empirical mainline) |
| **why_selected_or_rejected** | Rejected as empirical mainline. The hierarchical taxonomy (Level-1 / Level-2 / Level-3) is a valid paper-level framing for organizing the four operational labels (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate), but it is NOT the empirical mainline. The empirical mainline is the offline PDF-corpus evidence-sufficiency screening pipeline (V3.17 baseline). V3.15 is retained as paper interpretation only. |
| **key_evidence** | `paper_versions_ordered/V3_15_hierarchical_taxonomy_revision/CESE_OCN_V3_15_hierarchical_taxonomy_revision.md`; `project_synthesis/v3_16_integration_summary_and_revision_plan/mainline_impact_summary.md` (historical) |
| **decision_date** | 2026-07-05 (realignment) |

---

## V3.16 — No-Gold Evidence Integration

| Field | Value |
|---|---|
| **version** | V3.16 |
| **role** | Historical paper revision plan (no-gold evidence integration) |
| **status** | superseded |
| **why_selected_or_rejected** | Superseded. V3.16 attempted to integrate the no-gold evidence (scalar baseline, RIGOURATE reproduction, low-prevalence simulation) into the paper. The V3.16 plan was superseded by the V3.17 baseline selection, which reframes the contribution around evidence canonicalization as the retrieval-to-screening bridge rather than no-gold integration. V3.16 elements (scalar baseline, RIGOURATE proxy) are retained as historical context only. |
| **key_evidence** | `paper_versions_ordered/V3_16_no_gold_evidence_integration/CESE_OCN_V3_16_no_gold_evidence_integration.md`; `project_synthesis/no_gold_evidence_integration_v3_16_plan/no_gold_evidence_integration_master_report.md` (historical) |
| **decision_date** | 2026-07-05 (realignment) |

---

## V3.17 — Baseline (Selected Main Method)

| Field | Value |
|---|---|
| **version** | V3.17 |
| **role** | **Selected main method** (offline PDF-corpus evidence-sufficiency screening baseline) |
| **status** | **selected** |
| **why_selected_or_rejected** | **Selected.** V3.17 baseline is the current selected main method because: (1) it achieves the best strong_F1 (0.4503) under the current feature space; (2) it uses a simple, robust, auditable pipeline (BM25 + overlap canonicalization + restored R4 + G_conservative_precision ranking + review queue); (3) it demonstrates the core contribution that evidence canonicalization is the critical bridge between BM25 retrieval and R4 screening (canonicalization gain +0.2697); (4) it positions R4 correctly as a second-stage screening router (standalone_viable=false, second_stage_viable=true); (5) the V3.18 intelligent upgrade did not improve over it, confirming that simple overlap-based canonicalization is robust under the current feature space. |
| **key_evidence** | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` (frozen); `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` (supports_v3_17_mainline=true); `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` (second_stage_viable=true); `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` (best_variant=G_conservative_precision) |
| **frozen_metrics** | strong_F1=0.4503; strong_recall=0.7064; strong_precision=0.3305; macro_F1=0.3847; P@20=0.45; R@100=0.3303; FP/TP@5%=11.24; standalone_viable=false; second_stage_viable=true |
| **decision_date** | 2026-07-05 (frozen baseline for V3.18 intelligent upgrade) |

---

## V3.18 — Intelligent Upgrade (Negative Ablation)

| Field | Value |
|---|---|
| **version** | V3.18 |
| **role** | Exploratory negative ablation (learned evidence selector + learned risk ranker) |
| **status** | **negative_ablation (NOT selected as main method)** |
| **why_selected_or_rejected** | **Rejected as main method.** V3.18 attempted to replace the handcrafted overlap selector and risk ranker with sklearn learned models (LogisticRegression / RandomForest / HistGradientBoosting, group-aware split). Both modules failed to improve over V3.17 baseline: (1) learned selector strong_F1=0.4444 vs baseline 0.4503 (gap -0.0059, threshold 0.4703 NOT met); (2) learned ranker P@20=0.35 vs baseline 0.45 (gap -0.10, threshold 0.50 NOT met); (3) learned ranker FP/TP@5%=2.00 (better than baseline 11.24, but P@20 did not pass). `supports_v3_18_intelligent_upgrade=false`; `best_overall_method=V3.17_baseline`. V3.18 is retained as an exploratory negative result for §VIII limitations / §IX future work. Possible causes: feature space saturation, silver label noise, small sample size, R4 hard threshold limitations. |
| **key_evidence** | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` (supports_v3_18_intelligent_upgrade=false; best_overall_method=V3.17_baseline; selector_upgrade_passed=false; ranker_upgrade_passed=false); `experiments/v3_18_intelligent_upgrade_v1/learned_selector_metrics.csv` (strong_F1=0.4444); `experiments/v3_18_intelligent_upgrade_v1/learned_ranker_results.csv` (P@20=0.35); `experiments/v3_18_intelligent_upgrade_v1/intelligent_upgrade_comparison_table.csv` (5-method comparison) |
| **decision_date** | 2026-07-05 (negative ablation completed) |

---

## Decision Summary

| Version | Role | Status | Selected as main? |
|---|---|---|---|
| V3.15 | Paper-level interpretation (hierarchical taxonomy) | historical | No (paper interpretation only) |
| V3.16 | Historical revision plan (no-gold integration) | superseded | No |
| **V3.17** | **Offline PDF-corpus screening baseline** | **selected** | **YES** |
| V3.18 | Exploratory learned upgrade | negative_ablation | No (negative result; §VIII limitations) |

**Current selected main method: V3.17 baseline.**
**V3.18 is NOT selected as main method.**

---

## Cross-reference

- Realignment docs: `D:\ocn\project_synthesis\mainline_realignment_v1\`
- Frozen V3.17 metrics: `D:\ocn\experiments\v3_18_intelligent_upgrade_v1\v3_17_frozen_baseline_metrics.json`
- V3.18 negative gate: `D:\ocn\experiments\v3_18_intelligent_upgrade_v1\v3_18_intelligent_upgrade_gate.json`
- Paper version lineage (historical): `D:\ocn\project_synthesis\current_project_state_consolidation_clean_v1\paper_version_lineage_report.md`
