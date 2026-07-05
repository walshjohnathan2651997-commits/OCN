# OCN / CESE-OCN

## Current mainline

The current empirical mainline is **Confidential Lightweight V3.17: Local Evidence Canonicalization and Review Queueing for Simulation Claim Escalation Screening**.

This repository currently studies a narrow retrieval-to-screening problem: in local confidential PDF review, high-recall retrieval of raw PDF chunks does not guarantee downstream evidence-sufficiency screening quality. Raw chunks are often too long, noisy, multi-sentence, or metadata-contaminated. Simple local evidence canonicalization converts retrieved chunks into screening-compatible evidence spans and supports a conservative second-stage human review queue.

## Current pipeline

```text
private/local PDFs
→ local PDF text extraction
→ BM25 sentence/window retrieval
→ best_sentence_top5_overlap evidence canonicalization
→ frozen R4 out-of-fold screening
→ conservative/SmartQueue ranking
→ human review queue
```

## Current claims

**Safe:**

- local / no-API / no-cloud / no-training pipeline
- controlled silver diagnostic setting
- retrieval-to-screening format shift analysis
- evidence canonicalization restores strong_action_overclaim screening signal
- second-stage review queue support

**Not safe (do NOT claim):**

- no gold benchmark claim
- no human-audited dataset claim
- no SOTA claim
- no natural-prevalence claim
- no full shared-threshold CESE-OCN validation claim
- no automatic peer review claim
- no standalone detector claim

## Current frozen metrics (V3.17, 436 eval candidates)

| Metric | Value | Note |
|---|---|---|
| strong_F1 | 0.4503 | main metric |
| strong_recall | 0.7064 | high recall, second-stage value |
| strong_precision | 0.3305 | low precision, motivates second-stage |
| macro_F1 | 0.3847 | lower than LLM |
| precision@20 | 0.45 | review queue top-20 precision |
| precision@50 | 0.36 | review queue top-50 precision |
| recall@100 | 0.3303 | review queue top-100 coverage |
| FP/TP @ 5% prevalence | 11.24 | second-stage viable |
| standalone viable | false | R4 is second-stage only |
| second-stage viable | true | R4 is second-stage only |
| raw BM25 top1 strong_F1 | 0.1806 | raw chunks degrade screening |
| canonicalization gain | +0.2697 | canonicalization restores signal |

## Where to read next

- **`CURRENT_MAINLINE.md`** — short authoritative mainline lock
- **`docs/current_mainline_v3_17_confidential.md`** — detailed mainline spec (problem framing, format shift, relationship to SciFact-Open / SciClaimHunt / RIGOURATE / LLM-as-judge)
- **`docs/data_release_policy.md`** — what is released vs. withheld (confidentiality)
- **`docs/leakage_and_confidentiality_policy.md`** — forbidden fields in retrieval/ranking/queue routing
- **`docs/archive/README.md`** — archive disclaimer (legacy/future material)
- **`_MAINLINE_CURRENT/READ_ME_FIRST_CURRENT_MAINLINE.md`** — mainline entry point
- **`_MAINLINE_CURRENT/_FINAL_NUMBERS_FOR_PAPER.csv`** — paper-allowed final numbers
- **`_MAINLINE_CURRENT/_DO_NOT_USE_OLD_CLAIMS.md`** — forbidden stale claims

## Safety boundaries (enforced)

- silver-label diagnostic only
- not gold
- not human-audited
- not SOTA
- not natural-distribution prevalence
- not full shared-threshold CESE-OCN neural architecture validation
- not a standalone detector
- not replacing human review
- no LLM / API / cloud calls in mainline
- no new training
- no threshold changes
- no original data changes
- no silver-as-gold claim
- confidential local PDFs: raw text and real claim text are not released

---

## Legacy and future-work material (NOT current mainline)

The sections below describe older material: the **V2 evidence-aware hierarchical pilot** (legacy pilot), the **simclaim_human_pilot workflow** (legacy workflow), and the **full shared-threshold CESE-OCN neural architecture** (future architecture, not current empirical claim). None of the material below this divider is the current V3.17 mainline claim. Treat everything below as legacy context or future architecture exploration.

- **V2 evidence-aware hierarchical pilot** = legacy pilot (superseded)
- **simclaim_human_pilot** = legacy workflow (superseded)
- **full shared-threshold CESE-OCN** = future architecture, not current empirical claim

# CESE-OCN: Shared-Threshold Ordinal Calibration Network
# for Simulation Claim-Evidence Calibration

This repository implements **CESE-OCN**, a dual-branch ordinal calibration
network for detecting semantic escalation / overclaim in natural-language
claims that are supported by simulation evidence.

All experimental results are produced by running the provided scripts against
real JSONL/CSV data. No performance numbers are hard-coded. If real data is
unavailable, toy fixtures plus a schema validator are provided so the full
pipeline remains runnable end-to-end.

## Repo hygiene (do not commit experiment outputs)

The repository **does not commit experiment artifacts**. Checkpoints
(`*.pt`), logs (`*.log`), figures, tables, and the contents of `outputs/`
are all gitignored (see `.gitignore`). Every number in any report must be
regenerated by running the pipeline; no result is shipped as a committed
file.

To clean a working tree before zipping or opening a PR:

```bash
# Remove __pycache__ / .pytest_cache / *.pyc only.
python scripts/clean_artifacts.py

# Also wipe outputs/ (keeps outputs/.gitkeep) and data/derived/.
python scripts/clean_artifacts.py --all
```

`outputs/.gitkeep` is preserved so the directory exists after cleaning.

## What CESE-OCN does

CESE-OCN detects **semantic escalation** — situations where a claim asserts
stronger scope, causality, action, or certainty than the underlying
simulation evidence actually supports. It is an *ordinal* classifier: claim
and support strengths are scored on ordinal tiers (0–4), and escalation is
declared when the claim tier exceeds the support tier on any dimension.

The model has two branches:

- **Claim branch**: a transformer encoder produces a latent ordinal strength
  `theta_claim[k]` per claim dimension (scope, causal, action, certainty).
- **Evidence branch**: consumes the extracted evidence vector (8 dims) plus
  per-dim confidence; optional R-GCN graph mode when `torch_geometric` is
  installed.

A **shared-threshold ordinal calibrator** maps latent strengths to tier
probabilities via a cumulative-link (proportional-odds) parameterization
with a single ordered threshold vector `tau_1 < tau_2 < tau_3 < tau_4`
shared across all claim dimensions.

Three structural constraints are enforced during training:

1. **Monotonicity** — increasing relevant evidence must not decrease the
   predicted support probability.
2. **Hard truncation** — when critical causal/action evidence is missing,
   probability mass on forbidden high tiers is removed.
3. **Confidence lower bound** — escalation under observed evidence must not
   fall below the worst-case escalation computed under a confidence-aware
   lower-bound evidence vector.

A pre-registered **mapping R(k)** links each claim dimension to its relevant
evidence dimensions. R(k) is never learned using dev/test data.

## Repository layout

```
cese_ocn/
  configs/        YAML configurations (model, baselines, ablations, metrics)
  cese/
    data/         Schema, dataset, collate, splits, validation, toy fixtures
    models/       Ordinal layer, claim/evidence/graph branches, calibrator, full model
    losses/       Ordinal losses, monotonicity, truncation, confidence lower bound
    eval/         Metrics, calibration, thresholding, error decomposition, adversarial, cese_metrics
    baselines/    Rule / NLI / RAG-LLM / LLM-judge / ordinal-only / no-calibration
    extraction/   Evidence extractor interface, LLM stub, confidence estimator
    utils/        Config, seed, logging, io, registry
  scripts/        Entry points for data gen, training, eval, baselines, ablations, tables
  tests/          Unit tests (pytest)
  outputs/        Experiment artifacts (gitignored; regenerated by the pipeline)
```

## How to prepare JSONL data

Input is JSONL, one claim-evidence pair per line. See
`cese/data/schema.py` for the full pydantic model (`ClaimEvidenceSample`).
Tier labels are integers 0–4 (ordinal tiers, NOT interval-scale values).
Ordinal exceedance is used rather than continuous subtraction.

To generate toy fixtures (only if you lack real data):

```bash
python scripts/make_toy_data.py --out data/toy.jsonl --n 200
```

To validate any JSONL file against the schema:

```bash
python scripts/validate_data.py --input data/toy.jsonl
```

Each record must include the claim text, per-dimension claim tiers, the
extracted evidence vector (8 dims), per-dim confidence, support tiers, and
the binary escalation label. The validator reports the first 5 schema
errors and exits non-zero on any invalid record.

### Pilot data: template vs. real

```text
pilot_template.jsonl is schema/template data only.
Real pilot experiments must use data/pilot.jsonl.
```

- `data/pilot_template.jsonl` — schema/template data only. Passes
  `validate_data.py` / `audit_dataset.py` / `check_pilot_balance.py` but
  is NOT human-audited and NOT paper-ready. Use it to verify the pipeline
  end-to-end, never as experiment results.
- `data/pilot.jsonl` — real human-annotated pilot data (20 samples,
  balanced across scope/causal/action/certainty). Use this for pilot
  experiments that judge whether the research has signal.

### Pilot loop + manual fallback (ocn-29)

The first batch of human oracle pilot annotation is **40 rows only**
(not paper-ready). Before that, do a **5–10 row trial annotation** to
validate the template / import / fill / validate loop end-to-end. Use
the 8 core evidence dimensions
(`alignment`, `transparency`, `coverage`, `traceability`, `boundary`,
`uncertainty`, `causal_id`, `risk_utility`); every overclaim row must
fill `evidence_gap_labels` and should fill `rewrite_target`.

Two equivalent paths exist; both write `paper_valid=False` /
`result_scope="pilot_diagnostic"` so pilot output can never be mistaken
for paper results:

- **One-shot loop (recommended main path):**
  ```bash
  python scripts/run_pilot_loop.py \
    --input data/pilot_filled.jsonl \
    --output outputs/pilot_loop_real \
    --config configs/pilot_test.yaml \
    --seed 13 --allow_toy_results --skip_report \
    --step_timeout_sec 120
  ```
  `--skip_report` skips paper-release report generation. The full
  `run_stage_report.py` is **post-hoc** (see below) and is NOT a CI
  smoke必跑项 — it can deadlock under TRAE / pytest / timeout-wrapper
  pipe capture when run inline. The summary records a
  `recommended_next_command` field so the manual report invocation is
  one copy-paste away.
  `--stage_timeout_sec` (default `step_timeout_sec * 6`) is the budget
  for the bundled `run_stage_train_eval` step. The summary never lingers
  in `status=running`, and a `BrokenPipeError` from a closed parent pipe
  is swallowed by `safe_print()` so a successful loop is not mis-marked
  as failed. The summary also writes `train_eval_artifacts`
  (`{dev_predictions, operating_threshold, eval_test, train_eval_summary}`
  → `{path, exists}`) and `balance_findings` (warnings/errors lifted
  from `pilot_balance.json`).

- **Manual fallback (debugging individual stages):** see
  [docs/pilot_workflow.md](docs/pilot_workflow.md) for the canonical
  step-by-step flow (import → fill → validate → audit → balance → split
  → train_eval) and the binding guardrails. Keep this flow available
  even when the loop is green.

- **Full report (post-hoc, optional):** after a successful
  `--skip_report` run, generate the report manually without re-running
  train_eval:
  ```bash
  python scripts/run_stage_report.py \
    --results_dir outputs/pilot_real \
    --data data/pilot_split/pilot_train.jsonl \
    --output outputs/pilot_real/report \
    --profile pilot \
    --allow_toy_results
  ```
  Full report failure must NOT invalidate the already-successful
  `train_eval` artifacts.

**Toy / smoke / pilot_template / 40-row oracle pilot are diagnostic
only. Do NOT write them as paper results.** Paper-ready milestones
(300–500 rows, `extracted` evidence, graph evidence, LLM judge,
`run_stage_report.py` on real data) are out of scope for ocn-29.

## Legacy recommended entry points (ocn-23 / ocn-41 task 1) — NOT current mainline

The legacy paper main line was **CESE-OCN on `simclaim_human_pilot`**:
`simclaim_human_pilot` → `release_simclaim_human_pilot` →
`paper_assets/simclaim_human_pilot` → 论文结果表. This is superseded by
the V3.17 mainline (see `CURRENT_MAINLINE.md`). Do **not** introduce
new datasets, new release names, or new "future pipeline" branches.

Only two classes of entry points are recommended for the main line:

### Class 1 — Per-stage debugging entry points

These 6 independent stage scripts are the only per-stage entry points
maintained for the main line. Each writes its own `stage_summary.json`
and never blocks the others.

- `scripts/run_stage_model_train.py` — Stage 1a: CESE validate + train
- `scripts/run_stage_model_eval_dev.py` — Stage 1b: dev eval + dev predictions
- `scripts/run_stage_fit_threshold.py` — Stage 1c: fit operating threshold
- `scripts/run_stage_model_eval_test.py` — Stage 1d: test eval with fitted threshold
- `scripts/run_stage_baseline_train.py` — Stage 2a: train baselines
- `scripts/run_stage_baseline_eval.py` — Stage 2b: eval baselines

(The Stage 3 ablation / adversarial / oracle scripts
`run_stage_ablations.py` / `run_stage_adversarial.py` /
`run_stage_oracle_extracted.py` and the Stage 4 `run_stage_report.py`
are still available for diagnostic flows but are not on the
critical main-line path; the one-click release below regenerates the
canonical `release_simclaim_human_pilot/` tables directly.)

### Class 2 — One-click release entry point

- `scripts/run_dataset_pipeline.py` — the canonical one-click entry point
  that regenerates `release_simclaim_human_pilot/` from
  `configs/dataset_simclaim_human_pilot.yaml`. Use this for release
  regeneration.

### Deprecated entry points (do NOT use for the main line)

These are kept for historical / debugging reference only and are not
maintained as paper main-line entry points. New main-line work should
not depend on them.

- `scripts/run_human_150_pilot_pipeline.py` — DEPRECATED (ocn-41 task 1).
  Use `run_dataset_pipeline.py` for release regeneration.
- `scripts/run_all_experiments.py` — DEPRECATED EXPERIMENTAL
  orchestrator (ocn-22 / ocn-41 task 1). May hang on nested
  subprocesses. Use the per-stage scripts or `run_dataset_pipeline.py`.
- `scripts/run_pilot_loop.py` — DEPRECATED convenience loop
  (ocn-41 task 1). Use `run_stage_*.py` per-stage scripts.
- `scripts/run_release_pipeline.py` — DEPRECATED clean_v2 release
  orchestrator (ocn-33 / ocn-41 task 1). Use `run_dataset_pipeline.py`
  for the `release_simclaim_human_pilot/` main line.
- `scripts/run_stage_train_eval.py` — DEPRECATED convenience wrapper
  (ocn-30). Unreliable after multiple torch child processes. Use the
  four Stage 1 scripts above instead.
- `scripts/run_stage_diagnostics.py` — DEPRECATED convenience wrapper.
  Unreliable nested subprocess steps. Use `run_stage_ablations.py` +
  `run_stage_adversarial.py` + `run_stage_oracle_extracted.py` instead.

1. **smoke_minimal** — verify the CESE main chain (validate → train → eval).
   ```bash
   python scripts/run_smoke_minimal.py \
       --config configs/smoke_test.yaml \
       --data data/toy/smoke.jsonl \
       --output outputs/smoke_minimal \
       --step_timeout_sec 120
   ```
2. **pilot stage scripts** — run the pilot suite as 10 independent stages.
   Each stage writes its own `stage_summary.json` and never blocks the
   others. P1 (ocn-21): baseline train and eval are now separate stages;
   the old `run_stage_baselines.py` wrapper is deprecated. P1 (ocn-23):
   diagnostics is now split into ablations / adversarial / oracle_extracted;
   the old `run_stage_diagnostics.py` wrapper is deprecated.

   ```bash
   # Stage 1a: CESE validate + train
   python scripts/run_stage_model_train.py \
       --config configs/pilot_test.yaml \
       --train data/pilot_template.jsonl \
       --dev data/pilot_template.jsonl \
       --output outputs/pilot_stage/model_train \
       --step_timeout_sec 120

   # Stage 1b: dev eval (writes dev_predictions.jsonl)
   python scripts/run_stage_model_eval_dev.py \
       --config configs/pilot_test.yaml \
       --checkpoint outputs/pilot_stage/model_train/train/best.pt \
       --dev data/pilot_template.jsonl \
       --output outputs/pilot_stage/model_eval_dev \
       --step_timeout_sec 120

   # Stage 1c: fit operating threshold on dev predictions
   python scripts/run_stage_fit_threshold.py \
       --predictions outputs/pilot_stage/model_eval_dev/dev_predictions.jsonl \
       --output outputs/pilot_stage/fit_threshold \
       --step_timeout_sec 120

   # Stage 1d: test eval using the fitted operating threshold
   python scripts/run_stage_model_eval_test.py \
       --config configs/pilot_test.yaml \
       --checkpoint outputs/pilot_stage/model_train/train/best.pt \
       --test data/pilot_template.jsonl \
       --operating-threshold-state outputs/pilot_stage/fit_threshold/operating_threshold.json \
       --output outputs/pilot_stage/model_eval_test \
       --step_timeout_sec 120

   # Stage 2a: baseline train (ordinal_only / evidence_only / no_calibration)
   python scripts/run_stage_baseline_train.py \
       --config configs/pilot_baselines.yaml \
       --train data/pilot_template.jsonl \
       --dev data/pilot_template.jsonl \
       --output outputs/pilot_stage/baseline_train \
       --step_timeout_sec 120

   # Stage 2b: baseline eval (load checkpoints, run run_baselines.py)
   python scripts/run_stage_baseline_eval.py \
       --config configs/pilot_baselines.yaml \
       --test data/pilot_template.jsonl \
       --checkpoint-dir outputs/pilot_stage/baseline_train \
       --output outputs/pilot_stage/baseline_eval \
       --profile pilot \
       --step_timeout_sec 120

   # Stage 3a: ablations only
   python scripts/run_stage_ablations.py \
       --config configs/pilot_test.yaml \
       --ablations-config configs/pilot_ablations.yaml \
       --checkpoint outputs/pilot_stage/model_train/train/best.pt \
       --data data/pilot_template.jsonl \
       --output outputs/pilot_stage/ablations \
       --step_timeout_sec 120

   # Stage 3b: adversarial eval only
   python scripts/run_stage_adversarial.py \
       --config configs/pilot_test.yaml \
       --checkpoint outputs/pilot_stage/model_train/train/best.pt \
       --data data/pilot_template.jsonl \
       --output outputs/pilot_stage/adversarial \
       --profile pilot \
       --step_timeout_sec 120

   # Stage 3c: oracle/extracted comparison only
   python scripts/run_stage_oracle_extracted.py \
       --config configs/pilot_test.yaml \
       --checkpoint outputs/pilot_stage/model_train/train/best.pt \
       --data data/pilot_template.jsonl \
       --output outputs/pilot_stage/oracle_extracted \
       --step_timeout_sec 120

   # Stage 4: report (normalizes nested stage outputs into flat layout,
   # then calls generate_tables.py)
   python scripts/run_stage_report.py \
       --results_dir outputs/pilot_stage \
       --data data/pilot_template.jsonl \
       --output outputs/pilot_stage/report \
       --profile pilot \
       --allow_toy_results \
       --step_timeout_sec 120
   ```

   P0 (ocn-21): all stage scripts are quiet by default (one-line status
   per step). Pass `--verbose` to also print the last 10 lines of each
   step's log.
3. **paper_full** — restore `run_all_experiments.py` for the full paper
   experiment once the stage scripts are green.

```text
run_all_experiments.py is currently an optional full orchestration script.
For stable development, use stage scripts first.
```

## How to train

```bash
python scripts/train_cese_ocn.py \
    --config configs/model_cese_ocn.yaml \
    --train data/train.jsonl \
    --dev data/dev.jsonl \
    --output outputs/cese_ocn
```

Checkpoints are written to `outputs/cese_ocn/best.pt` (best dev loss) and
`outputs/cese_ocn/final.pt`. Training is deterministic given the `seed`
field in the config.

### Smoke / CI configuration (hermetic, no network)

The smoke configs (`configs/smoke_test.yaml`, `configs/smoke_baselines.yaml`,
`configs/smoke_ablations.yaml`) use the **`test-stub`** encoder instead of a
real HuggingFace model. `test-stub` is a lightweight deterministic encoder
that requires no `transformers` install and no network access, so the full
smoke pipeline can run in CI / offline environments:

```bash
python scripts/run_all_experiments.py \
    --config configs/smoke_test.yaml \
    --ablations-config configs/smoke_ablations.yaml \
    --baselines-config configs/smoke_baselines.yaml \
    --output outputs/smoke_pipeline \
    --allow_toy_results
```

The **full experiment** configs (`configs/model_cese_ocn.yaml`,
`configs/baselines.yaml`, `configs/ablations.yaml`) use a real HuggingFace
encoder (default `distilbert-base-uncased`). To run them you must:

1. `pip install transformers`
2. Ensure the model is downloadable or already cached locally
   (`~/.cache/huggingface/` or `TRANSFORMERS_CACHE`).

Never point a smoke/CI config at a real encoder — that breaks hermeticity.

## How to run baselines

```bash
python scripts/run_baselines.py \
    --config configs/baselines.yaml \
    --test data/test.jsonl \
    --output outputs/baselines
```

Enabled baselines (toggle in `configs/baselines.yaml`):

- **Rule baseline** — ordinal exceedance rule.
- **NLI baseline** — pretrained NLI entailment scorer.
- **RAG-LLM baseline** — retrieval-augmented LLM (requires API key).
- **Structured LLM judge** — GPT-style judge (requires API key).
- **Ordinal-only classifier** — claim branch + ordinal layer, no shared
  threshold calibration.
- **Dual-branch no calibration** — full dual-branch model without ordinal
  calibration.

## How to run ablations

```bash
python scripts/run_ablations.py \
    --config configs/ablations.yaml \
    --train data/train.jsonl \
    --dev data/dev.jsonl \
    --test data/test.jsonl \
    --output outputs/ablations
```

`configs/ablations.yaml` defines three experiment groups (spec Section 8):

- **8.3 Calibration ablation** — no calibration, separate thresholds,
  temperature scaling, isotonic calibration, shared-threshold ordinal
  calibration. Temperature/isotonic are fit on **dev only** (never test).
- **8.4 Constraint ablation** — full model vs. dropping monotonicity,
  truncation, confidence lower bound, or all constraints.
- **8.5 Mapping ablation** — expert R(k), uniform, random seeded,
  learned-train-only, and drop-one-dimension variants.

Results are written to `outputs/ablations/ablations_results.json` and
`outputs/ablations/mapping_ablation_results.json`.

Adversarial splits (spec Section 8.6):

```bash
python scripts/run_adversarial_eval.py \
    --checkpoint outputs/cese_ocn/best.pt \
    --standard data/test.jsonl \
    --lexical data/test_lexical_adv.jsonl \
    --template data/test_template_heldout.jsonl \
    --domain data/test_domain_heldout.jsonl \
    --output outputs/adversarial
```

## How to generate paper tables

```bash
python scripts/generate_tables.py \
    --results_dir outputs \
    --output outputs/report
```

This produces:

- `outputs/tables/main_results.csv`
- `outputs/tables/oracle_extracted_confidence.csv`
- `outputs/tables/calibration_ablation.csv`
- `outputs/tables/constraint_ablation.csv`
- `outputs/tables/mapping_ablation.csv`
- `outputs/tables/adversarial_results.csv`
- `outputs/tables/llm_stability.csv`
- `outputs/report/results.md` (Markdown report aggregating all tables)
- `outputs/figures/calibration_curve.png`
- `outputs/figures/threshold_sensitivity.png`
- `outputs/figures/oracle_extracted_gap.png`
- `outputs/figures/adversarial_drop.png`
- `outputs/figures/monotonic_violation.png`

Figures use matplotlib only.

## How to plug in GPT-5.5 or other LLM judge predictions as offline JSONL

CESE-OCN supports offline LLM judge evaluation. Instead of calling the LLM
API at evaluation time, you produce a JSONL file of predictions from your
LLM (GPT-5.5, Claude, Gemini, etc.) and feed it to the evaluation pipeline.

### 1. Generate predictions with your LLM

Run your LLM on each test sample and write one JSON object per line with the
following fields:

```json
{
  "sample_id": "test_0001",
  "escalation_pred": 1,
  "escalation_prob": 0.82,
  "claim_tiers_pred": [3, 2, 1, 2],
  "support_tiers_pred": [2, 1, 1, 2],
  "evidence_gaps_pred": ["missing_causal_id"],
  "prompt_run_id": "gpt55_run0"
}
```

- `escalation_pred`: 0/1 binary prediction.
- `escalation_prob`: model's confidence in escalation (for AUROC/AUPRC).
- `claim_tiers_pred` / `support_tiers_pred`: per-dimension tier predictions.
- `evidence_gaps_pred`: list of evidence-gap labels (for evidence-gap F1).
- `prompt_run_id`: identifier for the prompt/run (for LLM stability analysis,
  spec Section 8.7). Generate multiple files with different `prompt_run_id`
  values to compute mean / std / max-min range / disagreement rate.

### 2. Point the baselines config at your prediction file

Edit `configs/baselines.yaml`:

```yaml
baselines:
  llm_judge_baseline:
    enabled: true
    predictions_file: outputs/llm_judge/gpt55_predictions.jsonl
```

### 3. Run the baselines script

```bash
python scripts/run_baselines.py \
    --config configs/baselines.yaml \
    --test data/test.jsonl \
    --output outputs/baselines
```

The LLM judge baseline will load predictions from the JSONL file, compute
all metrics (accuracy, macro-F1, escalation F1, high-strength false-support
rate, evidence-gap F1, ordinal calibration error), and write them to
`outputs/baselines/baselines_results.json`.

### 4. (Optional) LLM judge stability

For the stability analysis (spec Section 8.7), place multiple prediction
files in a directory and run:

```bash
python -c "
from cese.eval import prompt_run_variance_for_llm_baselines
import json, numpy as np
runs = []
for f in ['run0.jsonl','run1.jsonl','run2.jsonl']:
    runs.append([json.loads(l)['escalation_prob'] for l in open(f)])
print(prompt_run_variance_for_llm_baselines(runs))
"
```

This reports mean, std, max-min range, and disagreement rate across runs.

## Key design choices

- **Claim branch**: transformer encoder (default `distilbert-base-uncased`)
  outputs latent ordinal strength `theta_claim[k]` per claim dimension.
- **Evidence branch**: vector MLP mode (8 evidence values + 8 confidence
  values) by default; optional R-GCN graph mode when `torch_geometric` is
  installed.
- **Shared-threshold ordinal calibration**: a single ordered threshold vector
  `tau_1 < tau_2 < tau_3 < tau_4` is shared across all claim dimensions and
  maps latent strength to ordinal tier probabilities via cumulative-link
  (proportional-odds) parameterization.
- **Mapping R(k)**: expert pre-registered mapping from claim dimensions to
  evidence dimensions; alternative modes (`uniform_all`, `random_seeded`,
  `drop_one_dimension`, `learned_train_only`) are provided for ablation. R(k)
  is never learned using dev/test data.

## Train/dev/test leakage policy

Per spec Section 12, all of the following are fit on **train/dev only** and
never touch test:

- Operating thresholds
- Calibration parameters (temperature, isotonic regression)
- Learned mappings R(k)
- Isotonic calibration curves

The `run_ablations.py` script fits temperature/isotonic on the dev split
explicitly before evaluating on test.

## Notes

- Graph mode requires `torch_geometric`. If it is unavailable,
  `cese/models/graph_branch.py` raises a clear `DependencyError` and the
  vector MLP mode continues to work.
- No hard-coded metrics: every number in any report is computed from a real
  run. `outputs/` is gitignored; regenerate all artifacts via the pipeline
  scripts (see "Repo hygiene" above).
- All scripts use type hints, docstrings, deterministic seeds, and readable
  logs.
