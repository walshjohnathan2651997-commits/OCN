# How to Upgrade to `simclaim_paper_full`

This guide walks through replacing the diagnostic pilot release
(`release_simclaim_human_pilot`) with the future confirmatory benchmark
(`release_simclaim_paper_full`). Following these steps in order is
required: skipping any of them leaves the pipeline in a state where
`paper_ready=false` is the only correct outcome.

## 0. Prerequisites

- The pilot release already exists under `release_simclaim_human_pilot/`
  and `paper_readiness_report.md` shows the data gates that are failing
  (typically: `human_audited_count < 300`, `n_test < 100`,
  `source_type` missing `extracted`/`confidence_aware`).
- You have read access to the annotation tooling and to the upstream
  claim extraction pipeline that produces `extracted` and
  `confidence_aware` source types.

## 1. Prepare `data/paper_full/` train/dev/test

The template config
[`configs/dataset_simclaim_paper_full_template.yaml`](../configs/dataset_simclaim_paper_full_template.yaml)
points at:

```
data/paper_full/splits/train.jsonl
data/paper_full/splits/dev.jsonl
data/paper_full/splits/test.jsonl
data/paper_full/annotation_summary.json
```

These files do **not** exist yet. Build them by:

1. Expanding the human-audited sample to at least 300 adjudicated items
   (two independent annotators + adjudication).
2. Stratifying into train / dev / test splits with no `paper_id` and no
   `logical_sample_id` crossing splits. The split script must record
   both IDs in the manifest so leakage can be checked.
3. Writing `annotation_summary.json` with `n_multi_annotator`,
   `n_with_agreement_score`, and per-annotator kappa.

Do **not** fabricate data. If you cannot reach 300 audited items, stay
on the pilot config and re-run the readiness gate.

## 2. Ensure fields conform to `schemas/simclaim_eval_schema.json`

Every record in train/dev/test must validate against
[`schemas/simclaim_eval_schema.json`](../schemas/simclaim_eval_schema.json).
Run:

```
python scripts/validate_dataset_contract.py \
    --config configs/dataset_simclaim_paper_full_template.yaml
```

The contract validator writes
`release_simclaim_paper_full/dataset_contract_validation.json`. If it
fails, fix the data, not the schema.

## 3. Ensure `human_audited: true`

The config sets `human_audited: true`. This must be backed by real
annotation records in `annotation_summary.json`. The readiness gate
does not inspect the annotation tool directly, but it does require
`n_multi_annotator >= 5` and `n_with_agreement_score >= 5` from the
audit summary. Faking `human_audited: true` while the audit summary is
empty is a blocking paper-gate violation.

## 4. Ensure `source_type` has oracle / extracted / confidence-aware

This is the single most common upgrade blocker. The pilot release only
has `oracle`. To pass the data gate:

- `oracle` — gold evidence provided by human annotators (already present).
- `extracted` — evidence retrieved by the upstream extraction pipeline
  (no confidence score).
- `confidence_aware` — extracted evidence with a calibrated confidence
  score attached.

All three must appear in `source_type_summary` in the release manifest
with non-zero counts. The readiness gate checks that all three keys
exist; it does not enforce a minimum count per source (that is a future
gate), but a missing source is an immediate FAIL.

## 5. Run `validate_dataset_contract`

```
python scripts/validate_dataset_contract.py \
    --config configs/dataset_simclaim_paper_full_template.yaml
```

Required output:

```
release_simclaim_paper_full/dataset_contract_validation.json
```

with `contract_valid: true`. If `contract_valid: false`, the data
contract is broken — do not proceed.

## 6. Run `run_dataset_pipeline`

```
python scripts/run_dataset_pipeline.py \
    --config configs/dataset_simclaim_paper_full_template.yaml
```

Before running, flip `placeholder: true` → `false` in the config and
verify `dataset_status: paper_full_candidate`. The pipeline runs the
full set of stages including `train_eval`, `run_strong_baselines`,
`run_calibration_ablation`, `run_constraint_ablation`,
`run_adversarial_eval`, `run_oracle_extracted_confidence`,
`bootstrap_metrics`, `paired_significance_tests`, and the new
`check_paper_readiness`, `export_paper_assets`, `package_release`
stages (see `run_dataset_pipeline.py` for the canonical ordering).

If any API key is missing, `run_strong_baselines` records
`skipped_reason=missing_api_key` per baseline and the readiness gate
will block on `experiment:strong baselines complete`.

## 7. Run `check_paper_readiness`

```
python scripts/check_paper_readiness.py \
    --release-dir release_simclaim_paper_full \
    --out release_simclaim_paper_full/paper_readiness_report.md
```

The report lists three gate groups (data / experiment / paper). All
three must show every row as `PASS`. A single FAIL keeps
`paper_ready=false` and adds a `paper:` blocking reason.

The report also writes `paper_readiness_report.json` for programmatic
consumers.

## 8. Run `export_paper_assets`

```
python scripts/export_paper_assets.py \
    --release-dir release_simclaim_paper_full \
    --out paper_assets/simclaim_paper_full
```

Once `paper_ready=true`, `metadata.json` records `table_kind=final` and
`final_main_table.csv` is emitted (when `paper_ready=false` it is
explicitly skipped with a `final_main_table.SKIPPED` marker file).

## 9. Update paper tables from `paper_assets/`

Pull LaTeX/Markdown tables from `paper_assets/simclaim_paper_full/tables/`
and PNGs from `paper_assets/simclaim_paper_full/figures/` directly into
the manuscript. Every exported CSV has `source_release`,
`generated_at`, and `table_kind` columns so provenance is auditable.

## 10. Never manually edit `paper_ready`

`paper_ready` is set exclusively by `check_paper_readiness.py` from the
structured gate results. Editing the value directly in
`RESULTS_MANIFEST.json` or in `paper_readiness_report.json` is a
paper-integrity violation. If a gate is incorrectly failing, fix the
underlying data or experiment, then re-run the gate.
