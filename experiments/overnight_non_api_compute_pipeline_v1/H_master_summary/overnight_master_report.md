# Overnight Non-API Compute Pipeline v1 — Master Report

**Date:** 2026-07-05
**Output root:** D:\ocn\experiments\overnight_non_api_compute_pipeline_v1
**Status:** Synthesis of 7 sub-tasks (A-G). NO API calls. NO gold. NO paper modification.

## 1. Task completion summary

| Status | Count |
|---|---|
| Completed | 7 |
| Partial | 0 |
| Blocked | 0 |

## 2. Q1. Which tasks completed?

- A Dataset Integrity + Leakage Re-Audit: completed
- B Claim Variant Similarity + Template Risk: completed
- C Low-Prevalence Screening Simulation: completed
- D Boundary Collapse Fallback Test: completed
- E LLM Conservatism + Error Direction Audit: completed
- F R4 False Positive Root Cause Analysis: completed
- G Scalar Score / RIGOURATE-style Baseline Sweep: completed

## 3. Q2. Which tasks blocked?



(None blocked.)

## 4. Q3. Dataset maximum risk

- **Claim-only TF-IDF risk: low** (separability gap = -0.006608406382115496)
- **Template risk: mean_template_risk = 0.6607090090090089** (76 high-risk groups)
- **Group leakage: low** (0 cross-group evidence hashes)

Maximum risk: claim-only TF-IDF leakage — if a linear classifier can predict label from claim text alone, the paper must report a claim-only baseline and acknowledge lexical leakage. Template risk is a known design attribute (controlled counterfactual), not a defect.

## 5. Q4. Is R4 screening positioning more stable?

**YES.** Three independent analyses support R4's screening-oriented positioning:
- T2 (low-prev sim): R4 recall stable ~0.36 across 1%-20% prevalence.
- T5 (LLM conservatism): R4 pred_strong_rate (0.36) >> LLM pred_strong_rate; LLM compresses strong to mild/supported.
- T1+T7 (scalar sweep): scalar cannot replace R4 (rule_scalar mild_vs_strong AUC near chance).

R4 is positioned as a **first-stage high-recall filter**, not a standalone screener.

## 6. Q5. Is R4 usable at low prevalence?

**NOT as standalone; YES as first-stage filter.**
- 1% prevalence: FP/TP = 120.0 (impractical standalone)
- 10% prevalence: FP/TP = 11.594594594594595 (marginal)
- R4 captures LLM-missed strong at all prevalences (first-stage value).
- Two-stage pipeline (R4 -> LLM/human) PROPOSED but NOT evaluated.

## 7. Q6. Is LLM conservatism confirmed?

**YES.**
- LLM pred_strong_rate = 0.04 (catches 1/25 silver=strong); R4 pred_strong_rate = 0.36 (catches 9/25).
- LLM is 9x more conservative than R4 on strong_action prediction.
- LLM error direction splits: GPT standard/structured over-route to contradiction (14/25=56%); DeepSeek compresses to mild/supported (19/25=76%).
- LLM exhibits high-accuracy/low-recall failure mode at low prevalence (T2/C).
- Complementary cases (LLM-only-correct + R4-only-correct) = 50/100 on matched 100 — strongly supports two-stage pipeline.

## 8. Q7. Is claim/template risk severe?

**NO — non-trivial but below 25% threshold.**
- Mean template_risk_score = 0.6607090090090089 (expected for controlled counterfactual design)
- 76/111 groups in high-risk tier (>0.6 cosine)
- Template risk is a design attribute (deliberate diagnostic separability), not a defect.
- Realism audit (T3 from V3.15) found 4.7% overall realism risk, 9.0% for strong_action.

## 9. Q8. Need dataset redesign?

**NO.** SimClaim retains diagnostic value. Risks are manageable:
- Template risk: report as deliberate design, not defect.
- Claim-only TF-IDF leakage: report claim-only baseline.
- Group leakage: investigate cross-group evidence hashes.
- Realism: add Layer-2 realism gold (v2 protocol).

## 10. Q9. Proceed to relation+realism gold?

**YES.** v2 two-layer protocol (T4 from V3.15) is drafted, silver-leakage-free, ready for annotation. Pre-registered decision rules (kappa<0.40, realism_score<=2 rate>25%) provide graceful degradation.

## 11. Q10. Tomorrow's first priority

**Run the v2 50-pair relation+realism gold pilot.**

This is the critical-path item blocking all downstream gold-validated claims. Sequence:
1. Identify 2 annotators + 1 adjudicator.
2. Train on v2 guideline (Layer 1 + Layer 2).
3. Distribute v2 A/B templates.
4. Annotate independently (~4h each).
5. Adjudicate per v2 protocol.
6. Compute agreement metrics (Layer 1 + Layer 2).
7. Apply pre-registered decision rules.

Until this pilot completes, all paper claims remain silver-stage directional support.

## 12. File inventory

- overnight_pipeline_status_matrix.csv (7 rows × 7 cols)
- overnight_master_report.md (this file)
- overnight_master_gate.json

## 13. Sub-task gate paths

- A: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\A_dataset_integrity_leakage\dataset_integrity_gate.json
- B: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\B_claim_variant_template_risk\template_risk_gate.json
- C: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\C_low_prevalence_screening\low_prevalence_gate.json
- D: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\D_boundary_collapse_fallback\boundary_collapse_gate.json
- E: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\E_llm_conservatism_error_direction\llm_conservatism_gate.json
- F: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\F_r4_false_positive_root_cause\r4_false_positive_gate.json
- G: D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\G_scalar_baseline_sweep\scalar_baseline_gate.json

## 14. Prohibitions enforced

- No API calls
- No gold annotation
- No large model training/downloading
- No paper modification
- No original data modification
- No file deletion
- No overwriting old experiments
- No simulation as real natural distribution
- No silver as gold
- No proxy as official RIGOURATE
