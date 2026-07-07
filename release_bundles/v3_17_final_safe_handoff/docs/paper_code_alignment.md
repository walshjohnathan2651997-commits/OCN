# Paper-Code Alignment Matrix

Release: `D:\ocn\release_simclaim_human_pilot`
Dataset: `simclaim_human_pilot`
Dataset status: `human_audited_pilot`
n_test: `30`
paper_ready: `False`

## Reading this matrix

- **complete** — release artefacts exist and every required row is metric_valid=true, n_samples>0, no skipped_reason. Pilot data may be `complete` for a *diagnostic* claim but never `complete` for a paper-full benchmark claim.
- **partial** — some required rows are valid; others missing/invalid.
- **blocked** — required code/release file missing, or an upstream gate (CESE checkpoint, API key) is missing.
- **diagnostic_only** — file exists and is valid, but the data is a human pilot (n_test<100); the claim is usable only as a pilot diagnostic, NOT as a paper-full benchmark claim.
- **not_implemented** — required code path does not exist.

## Summary by section

| Section | Claims | complete | diagnostic_only | partial | blocked |
| --- | --- | --- | --- | --- | --- |
| Introduction | 1 | 0 | 1 | 0 | 0 |
| Problem Formulation | 2 | 0 | 2 | 0 | 0 |
| CESE-OCN Method | 1 | 0 | 0 | 0 | 1 |
| Dataset / SimClaim-Eval Protocol | 2 | 0 | 2 | 0 | 0 |
| Main Experiments | 2 | 0 | 2 | 0 | 0 |
| Strong Baselines | 1 | 0 | 0 | 1 | 0 |
| Calibration Ablation | 1 | 0 | 1 | 0 | 0 |
| Constraint Ablation | 1 | 0 | 0 | 0 | 1 |
| Adversarial / Robustness | 1 | 0 | 0 | 1 | 0 |
| Oracle / Extracted / Confidence-aware Evidence | 2 | 0 | 2 | 0 | 0 |
| Error Analysis | 1 | 0 | 1 | 0 | 0 |
| Limitations | 1 | 1 | 0 | 0 | 0 |

## Introduction

### Claim: CESE-OCN models claim-evidence calibration as ordinal exceedance.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `cese/models/cese_ocn.py`
  - `cese/models/ordinal.py`
- **Required release file:**
  - `release_simclaim_human_pilot/RESULTS_MANIFEST.json`
- **Allowed wording:**
  - CESE-OCN casts claim-evidence calibration as ordinal exceedance between claim strength and evidence support on a shared tier scale.
- **Forbidden wording:**
  - CESE-OCN is a production deployment system.
  - CESE-OCN is a final benchmark for SimClaim-Eval.

## Problem Formulation

### Claim: escalation_label is derived from ordinal exceedance (claim_tier > support_tier on any dimension).

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `cese/utils/labels.py`
  - `scripts/validate_dataset_contract.py`
  - `scripts/audit_label_derivation.py`
- **Required release file:**
  - `release_simclaim_human_pilot/dataset_contract_validation.json`
  - `release_simclaim_human_pilot/reports/label_derivation_audit.json`
- **Allowed wording:**
  - We define escalation as any ordinal claim tier exceeding its support tier.
- **Forbidden wording:**
  - The dataset is a final benchmark.
  - escalation_label is a free-form human judgement with no rule.

### Claim: Shared thresholds place claim strength and evidence support on a common ordinal scale.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `cese/models/shared_threshold_calibrator.py`
  - `scripts/fit_operating_threshold.py`
- **Required release file:**
  - `release_simclaim_human_pilot/train_eval/operating_threshold.json`
- **Allowed wording:**
  - A single set of shared thresholds maps claim strength and evidence support onto the same 0..4 ordinal scale.
- **Forbidden wording:**
  - We calibrate separate thresholds per branch with no shared scale.

## CESE-OCN Method

### Claim: Non-compensatory constraints prevent unsupported dimensions from being compensated by unrelated evidence strength.

- **Status:** `blocked`
- **Blocking reason:** code_ok=True full_cese_valid=False no_constraints_valid=False
- **Required code:**
  - `cese/models/inference_constraints.py`
  - `cese/losses/truncation.py`
  - `cese/losses/monotonicity.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/constraint_ablation.csv`
  - `release_simclaim_human_pilot/ablations/constraint_ablation_results.json`
- **Required table:**
  - `constraint_ablation.csv`
- **Allowed wording:**
  - We enforce a non-compensatory truncation so that an unsupported dimension cannot be rescued by evidence strength on unrelated dimensions.
- **Forbidden wording:**
  - CESE-OCN sums evidence strengths freely across dimensions.

## Dataset / SimClaim-Eval Protocol

### Claim: Human pilot data contains double-annotated/adjudicated simulation claim-evidence pairs.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `cese/data/annotation_io.py`
  - `scripts/adjudicate_annotations.py`
  - `scripts/compute_annotation_agreement.py`
- **Required release file:**
  - `release_simclaim_human_pilot/RESULTS_MANIFEST.json`
  - `release_simclaim_human_pilot/reports/dataset_quality_audit.json`
- **Allowed wording:**
  - The pilot split was double-annotated and adjudicated; inter-annotator agreement is reported per dimension.
- **Forbidden wording:**
  - The dataset is a final benchmark.
  - The dataset is a fully adjudicated paper-full benchmark (n_test>=100).

### Claim: Significance is confirmatory only if n_test>=100; otherwise exploratory.

- **Status:** `diagnostic_only`
- **Blocking reason:** n_test=30 < 100; significance is exploratory, not confirmatory.
- **Required code:**
  - `scripts/split_pilot_data.py`
- **Required release file:**
  - `release_simclaim_human_pilot/RESULTS_MANIFEST.json`
- **Allowed wording:**
  - Statistical significance on the pilot split (n_test<100) is exploratory and must not be reported as confirmatory.
- **Forbidden wording:**
  - We confirm the hypothesis at p<0.05 on the pilot split.

## Main Experiments

### Claim: Main results compare CESE-OCN with fair lexical and TF-IDF baselines.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `scripts/run_baselines.py`
  - `cese/baselines/text_fair_baselines.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/main_results.csv`
  - `release_simclaim_human_pilot/baselines_results.json`
- **Required table:**
  - `main_results.csv`
- **Allowed wording:**
  - On the pilot split, CESE-OCN is compared against lexical-cue and TF-IDF fair baselines under the same train/dev/test protocol.
- **Forbidden wording:**
  - CESE-OCN outperforms all baselines on a paper-full benchmark.
  - evidence_only_tfidf_logistic is a fair baseline.

### Claim: Evidence-only baseline is diagnostic/leakage-risk, not a fair comparison.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `cese/baselines/text_fair_baselines.py`
  - `scripts/audit_baseline_dominance.py`
  - `scripts/audit_baseline_feature_leakage.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/main_results.csv`
  - `release_simclaim_human_pilot/reports/baseline_dominance_audit.json`
  - `release_simclaim_human_pilot/tables/baseline_dominance.csv`
- **Required table:**
  - `main_results.csv`
  - `baseline_dominance.csv`
- **Allowed wording:**
  - The evidence-only baseline is reported as an oracle / leakage diagnostic and excluded from the fair main comparison.
- **Forbidden wording:**
  - evidence_only_tfidf_logistic is a fair main baseline.
  - CESE-OCN outperforms the evidence-only baseline in a fair comparison.

## Strong Baselines

### Claim: Strong baselines (structured_llm_judge, nli_scifact_style, ragas_style, ares_style, pairwise_llm_judge) are reported only when metric_valid=true.

- **Status:** `partial`
- **Blocking reason:** missing valid strong baselines: ['ares_style', 'pairwise_llm_judge', 'ragas_style', 'structured_llm_judge']; skipped_reasons={'structured_llm_judge': 'missing_api_key', 'ragas_style': 'missing_api_key', 'ares_style': 'missing_api_key', 'pairwise_llm_judge': 'missing_api_key'}
- **Required code:**
  - `scripts/run_strong_baselines.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/strong_baselines.csv`
  - `release_simclaim_human_pilot/strong_baselines/strong_baselines_results.json`
- **Required table:**
  - `strong_baselines.csv`
- **Allowed wording:**
  - Strong baselines that lacked an API key are reported as skipped (missing_api_key) and excluded from any superiority claim.
- **Forbidden wording:**
  - CESE-OCN outperforms all strong baselines.
  - All strong baselines were evaluated.

## Calibration Ablation

### Claim: Calibration ablation shows shared-threshold ordinal calibration improves over no calibration.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `scripts/run_calibration_ablation.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/calibration_ablation.csv`
  - `release_simclaim_human_pilot/ablations/calibration_ablation_results.json`
- **Required table:**
  - `calibration_ablation.csv`
- **Allowed wording:**
  - On the pilot split, shared-threshold ordinal calibration reaches macro-F1 at least as high as the no-calibration variant.
- **Forbidden wording:**
  - Calibration ablation confirms superiority on a paper-full benchmark.

## Constraint Ablation

### Claim: Constraint ablation shows full CESE-OCN beats no-constraints and partial-gate variants on high-strength false support.

- **Status:** `blocked`
- **Blocking reason:** full_cese row metric_valid=false or n_samples=0; constraint ablation cannot support any constraint-superiority claim.
- **Required code:**
  - `scripts/run_constraint_ablation.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/constraint_ablation.csv`
  - `release_simclaim_human_pilot/ablations/constraint_ablation_results.json`
- **Required table:**
  - `constraint_ablation.csv`
- **Allowed wording:**
  - On the pilot split, full CESE-OCN achieves a lower high-strength false-support rate than the no-constraints variant.
- **Forbidden wording:**
  - Constraint ablation confirms superiority on a paper-full benchmark.
  - Full CESE-OCN achieves perfect monotonicity on the pilot split.

## Adversarial / Robustness

### Claim: Adversarial robustness is claimed only if adversarial_results has CESE rows with n_samples>0 on standard + >=2 adversarial splits.

- **Status:** `partial`
- **Blocking reason:** cese_ocn valid splits=['Domain-held-out test', 'Lexical-adversarial test', 'Logical-sample-held-out test', 'Standard test', 'Style-balanced test', 'Template-held-out test']; need standard + 2 adversarial splits.
- **Required code:**
  - `scripts/run_adversarial_eval.py`
  - `scripts/build_adversarial_splits.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/adversarial_results.csv`
- **Required table:**
  - `adversarial_results.csv`
- **Allowed wording:**
  - Fair baseline robustness on cue_words_removed and style_balanced splits is reported; CESE-OCN adversarial robustness is not claimed because the checkpoint is not available for adversarial evaluation.
- **Forbidden wording:**
  - CESE-OCN is robust to adversarial cue removal.
  - CESE-OCN maintains accuracy on all adversarial splits.

## Oracle / Extracted / Confidence-aware Evidence

### Claim: Oracle / extracted / confidence-aware evidence modes are compared only when all three modes exist with valid metrics.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `scripts/run_oracle_extracted_confidence.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/oracle_extracted_confidence.csv`
- **Required table:**
  - `oracle_extracted_confidence.csv`
- **Allowed wording:**
  - On the pilot split, oracle, extracted, and confidence-aware evidence modes are compared on the same logical samples.
- **Forbidden wording:**
  - We compare only oracle evidence.
  - Extracted and confidence-aware modes are not needed.

### Claim: CESE-OCN evidence-mode comparison requires the CESE checkpoint.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `scripts/run_oracle_extracted_confidence.py`
  - `cese/utils/checkpoint.py`
- **Required release file:**
  - `release_simclaim_human_pilot/tables/oracle_extracted_confidence.csv`
- **Required table:**
  - `oracle_extracted_confidence.csv`
- **Allowed wording:**
  - Fair-baseline evidence-mode comparison is reported; CESE-OCN evidence-mode comparison is blocked because the checkpoint is not shipped with the pilot release (see docs/checkpoint_policy.md).
- **Forbidden wording:**
  - CESE-OCN outperforms fair baselines across all three evidence modes.

## Error Analysis

### Claim: Error analysis is reported at the per-dimension level on the pilot split.

- **Status:** `diagnostic_only`
- **Blocking reason:** Release is human pilot (n_test<100, dataset_status=human_audited_pilot). Pilot findings only; not a paper-full benchmark claim.
- **Required code:**
  - `scripts/error_analysis.py`
  - `cese/eval/error_decomposition.py`
- **Required release file:**
  - `release_simclaim_human_pilot/train_eval/eval_test_ordinal_per_dim.csv`
- **Required table:**
  - `eval_test_ordinal_per_dim.csv`
- **Allowed wording:**
  - We report per-dimension error decomposition on the pilot split as a diagnostic of where CESE-OCN fails.
- **Forbidden wording:**
  - Error analysis confirms the model is deployment-ready.

## Limitations

### Claim: The current release is a human pilot (n_test<100), not a paper-full benchmark; paper_ready must remain false.

- **Status:** `complete`
- **Blocking reason:** paper_ready=false; n_test<100; blocking_reasons recorded.
- **Required release file:**
  - `release_simclaim_human_pilot/RESULTS_MANIFEST.json`
  - `release_simclaim_human_pilot/paper_readiness_report.json`
- **Allowed wording:**
  - This release is a human pilot (n_test<100) and not a paper-full benchmark; all quantitative findings are diagnostic.
- **Forbidden wording:**
  - We present a final benchmark for SimClaim-Eval.
  - paper_ready=true.

