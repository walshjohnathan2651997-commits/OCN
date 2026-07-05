# Paper V2 Strengthening Summary

## Completed strengthening actions

### 1. Fixed result-table consistency

The TF-IDF claim+evidence delta in the V2 readiness table and manuscript was corrected from the old stability-run value to the value from the same frozen-encoder run:

```text
0.5296 - 0.5420 = -0.0123
```

Updated files:

- `scripts/build_paper_readiness_v2.py`
- `scripts/build_cese_ocn_v2_docx.py`
- `experiments/paper_readiness_v2_evidence_aware/table_key_results.csv`
- `paper_versions_ordered/V2_evidence_aware_hierarchical/V2_CESE_OCN_evidence_aware_hierarchical_pilot.docx`

### 2. Added V2 reproduction path

Created a clear V2-only reproduction path:

- `docs/paper_v2_reproduction_path.md`

Updated `README.md` to state that the current paper mainline is the V2 evidence-aware hierarchical pilot, not the older full shared-threshold CESE-OCN architecture claim.

### 3. Added bootstrap confidence interval audit

Created and ran:

- `scripts/run_paper_v2_bootstrap_ci.py`

Outputs:

- `experiments/paper_v2_bootstrap_ci/bootstrap_ci_summary.json`
- `experiments/paper_v2_bootstrap_ci/bootstrap_ci_report.md`
- `experiments/paper_v2_bootstrap_ci/cross_encoder_vs_tfidf_delta_by_seed.csv`

Key result:

```text
10-seed mean delta: +0.1474
95% bootstrap CI: [0.1235, 0.1750]
P(mean delta <= 0): 0.0000
positive seeds: 10/10
```

### 4. Added leave-one-domain-out evaluation

Created and ran:

- `scripts/run_paper_v2_domain_holdout.py`

Outputs:

- `experiments/paper_v2_domain_holdout_v1/domain_holdout_summary.json`
- `experiments/paper_v2_domain_holdout_v1/domain_holdout_report.md`
- `experiments/paper_v2_domain_holdout_v1/domain_holdout_results.csv`
- `experiments/paper_v2_domain_holdout_v1/domain_holdout_predictions.csv`
- `experiments/paper_v2_domain_holdout_v1/domain_holdout_macro_f1_pivot.csv`

Key result:

```text
cross_encoder_nli_pair mean macro-F1: 0.6774
TF-IDF claim-only mean macro-F1: 0.6055
delta: +0.0719
cross-encoder wins domains: 5/6
```

### 5. Updated V2 manuscript

The V2 Word manuscript now includes:

- corrected TF-IDF delta;
- bootstrap confidence interval result;
- leave-one-domain-out result;
- updated abstract and conclusion;
- continued silver-label / pilot-only caveats.

Main file:

- `paper_versions_ordered/V2_evidence_aware_hierarchical/V2_CESE_OCN_evidence_aware_hierarchical_pilot.docx`

## Updated readiness judgment

Before strengthening:

```text
SCI Q1 readiness: approximately 40%-45%
```

After this strengthening pass:

```text
SCI Q1 readiness: approximately 55%-60%
```

The project is now substantially stronger as a pilot paper. It still needs more work before a serious SCI Q1 submission.

## Remaining major gaps

1. Full Related Work and references are still missing.
2. The method contribution is still mostly an evidence-aware formulation plus frozen NLI feature validation, not a new trained model.
3. Labels are still silver, not gold.
4. Data scale is still small: 444 claims / 111 groups.
5. Fine-tuning and stronger modern baselines are not yet included.
6. The codebase still contains many historical routes; the V2 reproduction path is clear, but a release-clean package would be better.

## Recommended next strengthening step

The next highest-value step is:

```text
Write full Related Work + Introduction framing + References, then add one stronger model/fine-tuning experiment if GPU is available.
```

