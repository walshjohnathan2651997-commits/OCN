# Gate Synthesis Report

**Date:** 2026-07-05
**Total gates scanned:** 25
**Valid JSON:** 24
**Completed=True:** 7
**Blocked=True:** 0
**Missing:** 1

## Summary

### Successfully completed tasks

The following gates report `completed=true`:

- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\A_dataset_integrity_leakage\dataset_integrity_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\B_claim_variant_template_risk\template_risk_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\C_low_prevalence_screening\low_prevalence_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\D_boundary_collapse_fallback\boundary_collapse_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\E_llm_conservatism_error_direction\llm_conservatism_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\F_r4_false_positive_root_cause\r4_false_positive_gate.json`
- `D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\G_scalar_baseline_sweep\scalar_baseline_gate.json`

### Blocked / partial tasks

None. All valid gates report completed=true or have no completed field (informational gates).

### Missing gates

- `D:\ocn\gold_pilot_protocol_freeze_v1\MISSING`


## Key findings across gates

1. **Mainline survives (V3.16 integration gate):** `mainline_survives=true`, `needs_dataset_redesign=false`, `needs_relation_realism_gold=true`, `rigourate_overlap_fatal=false`. The four-class + relation+realism gold route (Route A) is the default.

2. **Overnight pipeline (8 sub-tasks A-H):** All 7 sub-tasks + master summary completed. Key results: dataset integrity PASS (TF-IDF separability gap=-0.0066 = LOW leakage); LLM conservatism CONFIRMED (pred_strong_rate 0.04 vs R4 0.36, 9x gap); R4 FP concentrated in mild→strong boundary (26 FP of 35 strong predictions); scalar cannot replace R4 (rule_scalar AUC=0.5062 on mild_vs_strong); 50/100 complementary cases support two-stage pipeline.

3. **V3.15 hierarchical taxonomy revision:** `hierarchical_taxonomy_inserted=true`, `flat_four_class_deemphasized=true`, `fallback_to_3class_plus_binary_defined=true`, `numbers_unchanged=true`, `gold_not_claimed=true`, `old_files_unchanged=true`, `docx_generated=true`. All 10 §12 quality checks PASS.

4. **RIGOURATE reproduction:** `official_reproduction_possible=false`. Proxy scalar baseline built; official code/data/model not publicly available. Scalar cannot distinguish mild vs strong (ROC-AUC ≤ 0.59).

5. **Claim realism audit:** `high_risk_claim_rate=0.0`, `safe_to_use_as_diagnostic_set=true`, `safe_to_claim_naturalistic=false`. SimClaim remains suitable as controlled diagnostic set but NOT as naturalistic corpus.

6. **Low-prevalence screening:** `r4_screening_viable_at_1pct=false`, `r4_usable_low_prevalence_first_stage=true`. R4 recall stable ~0.36 across 1%-25%; NOT viable standalone <10%; viable as first-stage filter.

7. **Scalar vs relation deep test:** `scalar_can_separate_mild_strong=false`, `scalar_can_replace_r4=false`, `score_collapse_observed=true`. Scalar score compresses the mild/strong boundary.

8. **Gold protocol v2:** `ready_for_blind_annotation=true`, `does_not_modify_v1=true`. Two-layer (relation + realism) protocol DRAFT; annotation NOT begun.

## Main remaining risks (aggregated)

- **Level-2 mild_vs_strong boundary** is the hardest to draw (75% confusion in §V.D audit). If gold adjudication reveals κ < 0.40, paper must fall back to Level-1 three-class + binary strong_action screening per §VII.K.
- **RIGOURATE proxy:** §VI.E scalar baseline is proxy, not official RIGOURATE. Conclusions may shift when official artifacts become available.
- **Gold not yet collected:** All strong-action screening claims are silver-stage evidence pending §VII protocol-locked gold adjudication.
- **SimClaim is counterfactual, not natural-prevalence:** Balanced four-way design is deliberate for diagnostic pressure-testing, not an estimate of real-world prevalence.
- **R4 macro-F1 < LLM:** R4 macro-F1=0.3280 vs LLM=0.5523 on matched 100. R4 is a screening complement, not an overall-beats-LLM claim.

## Recommended next action (aggregated)

Execute the §VII 50-pair two-layer gold pilot (Layer 1 relation + Layer 2 realism) using the frozen gold_pilot_protocol_freeze_v1 package and the v2 relation+realism protocol. Compute Level-1 κ, Level-2 κ, strong_action retention; apply §VII.K fallback rules to determine whether to retain hierarchical taxonomy or fall back to Level-1 three-class + binary strong_action screening.
