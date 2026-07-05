# RQ -> Experiment Table Mapping

Release: `D:\ocn\release_simclaim_human_pilot`

All findings are pilot-diagnostic. The pilot is NOT a final benchmark. Claims marked `forbidden` MUST NOT appear in the paper.

## RQ Index

| RQ | Question | Status | Primary Table |
|----|----------|--------|---------------|
| RQ1 | Can CESE-OCN perform the main task? | complete | `tables/main_results_paper_fair.csv` |
| RQ2 | Does CESE reduce lexical cue dependency? | complete | `tables/delexicalized_variant_comparison.csv` |
| RQ3 | Do constraints contribute independently? | complete | `tables/fine_grained_constraint_ablation.csv` |
| RQ4 | Does CESE reduce high-strength false support? | partial | `tables/high_strength_false_support_ci.csv` |
| RQ5 | Is CESE's calibration issue repairable? | complete | `tables/posthoc_calibration_repair.csv` |

## RQ1: Can CESE-OCN perform the main task?

- **Status**: `complete`
- **Primary table**: `tables/main_results_paper_fair.csv`
- **Supporting tables**:
  - `tables/Table_Main_Results.csv`
  - `tables/Table_Baseline_Dominance.csv`
- **Main finding**: CESE-OCN is implemented and metric_valid=True on n_test=30 with macro_f1=0.9305555555555556. Fair baselines implemented: ['cese_ocn_full', 'claim_evidence_tfidf_linear_svm', 'claim_evidence_tfidf_logistic', 'claim_only_tfidf_logistic', 'claim_text_lexical_cue'].
- **Negative finding**: CESE does NOT lead on macro-F1 in the pilot. Best fair baseline macro_f1=0.9663299663299663 >= CESE macro_f1=0.9305555555555556. CESE's advantage must be framed as risk/diagnostic, not F1.
- **Paper sentence allowed**: CESE-OCN is implemented and produces valid predictions on the main task; its contribution lies in risk-sensitive diagnostics, not in maximising macro-F1.
- **Paper sentence forbidden**: Do NOT claim CESE outperforms all fair baselines on macro-F1; do NOT treat evidence_only_tfidf_logistic as a fair baseline; do NOT describe classic baselines with missing_api_key as 'strong baseline complete'.
- **Remaining gap**: Add transformer / LLM-based fair baseline in future work; current fair baselines are TF-IDF / lexical only.

- **Quantitative evidence**:
  - `evidence_only_is_fair_baseline`: False
  - `cese_metric_valid`: True
  - `best_fair_macro_f1`: 0.9663299663299663
  - `cese_macro_f1`: 0.9305555555555556

## RQ2: Does CESE reduce lexical cue dependency?

- **Status**: `complete`
- **Primary table**: `tables/delexicalized_variant_comparison.csv`
- **Supporting tables**:
  - `tables/delexicalized_results.csv`
  - `tables/Table_Baseline_Dominance.csv`
- **Main finding**: CESE claim_only cue_sensitivity_drop=0.0 vs max lexical baseline drop=0.244108. CESE is more cue-robust in claim_only.
- **Paper sentence allowed**: CESE exhibits lower cue_sensitivity_drop in claim_only mode, consistent with reduced surface-cue reliance.
- **Paper sentence forbidden**: Do NOT describe n_samples=0 adversarial rows as robustness evidence; do NOT claim CESE is universally cue-invariant.
- **Remaining gap**: Need larger adversarial / paraphrase set to test cue-invariance at scale; pilot n_test=30 only.

- **Quantitative evidence**:
  - `cese_claim_only_drop`: 0.0
  - `max_lexical_baseline_drop`: 0.244108

## RQ3: Do constraints contribute independently?

- **Status**: `complete`
- **Primary table**: `tables/fine_grained_constraint_ablation.csv`
- **Supporting tables**:
  - `tables/Table_Constraint_Ablation.csv`
- **Main finding**: Full CESE-OCN metric_valid=True, macro_f1=0.9305555555555556. Per-component deltas vs full: [('no_monotonicity', -0.463889), ('no_truncation', -0.508219), ('no_confidence_lower_bound', -0.576489), ('no_shared_threshold', -0.564593), ('zero_evidence_input', -0.489562), ('remove_evidence_branch_loss', -0.354176), ('no_evidence_branch', -0.530556)]. Any component removal costs >=0.02 macro-F1: True.
- **Paper sentence allowed**: Removing component X reduces macro-F1 by Y, consistent with the constraint contributing independently to model behaviour.
- **Paper sentence forbidden**: Do NOT claim mechanism is valid if Full CESE-OCN metric_valid=False; do NOT report Full CESE AUROC=NA as if AUROC was measured.
- **Remaining gap**: Need multiseed / bootstrap CI on per-component deltas; current deltas are point estimates on n_test=30.

- **Quantitative evidence**:
  - `full_cese_metric_valid`: True
  - `full_cese_macro_f1`: 0.9305555555555556
  - `per_component_deltas`: [('no_monotonicity', -0.463889), ('no_truncation', -0.508219), ('no_confidence_lower_bound', -0.576489), ('no_shared_threshold', -0.564593), ('zero_evidence_input', -0.489562), ('remove_evidence_branch_loss', -0.354176), ('no_evidence_branch', -0.530556)]

## RQ4: Does CESE reduce high-strength false support?

- **Status**: `partial`
- **Primary table**: `tables/high_strength_false_support_ci.csv`
- **Supporting tables**:
  - `tables/high_strength_false_support.csv`
- **Main finding**: CESE native HSFS=0.166667 with bootstrap CI=[0.0, 0.416667] over n_high_strength_cases=12.0.
- **Negative finding**: n_high_strength_cases=12.0 is small; CI is wide. HSFS must be reported as a diagnostic signal, NOT as a population estimate.
- **Paper sentence allowed**: HSFS = X [CI_low, CI_high] is a diagnostic signal of high-strength false support on the pilot set.
- **Paper sentence forbidden**: Do NOT report HSFS as a population-level estimate; do NOT omit the CI when n_high_strength_cases < 30.
- **Remaining gap**: Collect more high-strength cases to tighten the CI; current bootstrap CI is informative but wide.

- **Quantitative evidence**:
  - `n_high_strength_cases`: 12.0
  - `hsfs_rate`: 0.166667
  - `ci_low`: 0.0
  - `ci_high`: 0.416667

## RQ5: Is CESE's calibration issue repairable?

- **Status**: `complete`
- **Primary table**: `tables/posthoc_calibration_repair.csv`
- **Supporting tables**:
  - `tables/calibrated_decision_comparison.csv`
  - `tables/model_calibration_comparison.csv`
- **Main finding**: Raw CESE Brier=0.193227 -> Platt Brier=0.080337 (repair effective=True). Decision-level: raw HSFS=0.166667 -> Platt HSFS=0.0. Ranking (AUROC) is preserved across calibration.
- **Negative finding**: Raw CESE scores are NOT calibrated and must NOT be interpreted as calibrated probabilities; reliability is only achieved via post-hoc calibration.
- **Paper sentence allowed**: Post-hoc calibration (Platt / isotonic) substantially reduces Brier / ECE without degrading ranking performance; the raw CESE score should not be read as a calibrated probability.
- **Paper sentence forbidden**: Do NOT describe raw CESE scores as already calibrated; do NOT collapse ranking and calibration metrics.
- **Remaining gap**: Calibrators are fit on n_dev=30; need larger dev split for stable Platt / isotonic parameters.

- **Quantitative evidence**:
  - `raw_brier`: 0.193227
  - `platt_brier`: 0.080337
  - `raw_hsfs_decision`: 0.166667
  - `platt_hsfs_decision`: 0.0

