# Pilot Workflow (ocn-29)

This document is the **canonical manual pilot workflow** for CESE-OCN.
It exists as a fallback for the (still maturing) one-shot
`scripts/run_pilot_loop.py --skip_report`. Even when the loop is green,
keep this manual flow available — it is the only way to debug a single
stage in isolation when the loop misbehaves.

> **Status: NOT paper-ready.** Everything in this document produces
> *diagnostic* pilot data only. Toy / smoke / pilot_template / the
> 40-row human oracle pilot must never appear in a paper table, abstract,
> or conclusion. The `paper_valid=False` / `result_scope="pilot_diagnostic"`
> fields written into every `pilot_loop_summary.json` enforce this
> machine-readably.

> **ocn-29 report strategy.** The full `run_stage_report.py` step is
> **post-hoc** and is NOT part of the CI / pilot main path. The main
> path is `run_pilot_loop.py --skip_report`. The report can be
> generated manually afterward (see §7) and its failure must never
> invalidate the already-successful `train_eval` artifacts. The summary
> records a `recommended_next_command` field when `--skip_report` is
> passed so the manual report invocation is one copy-paste away.

See also:
- [schemas/pilot_annotation_minimal_schema.md](../schemas/pilot_annotation_minimal_schema.md)
  — field-level schema and tier scale.
- [README.md](../README.md) §"Pilot data: template vs. real" — toy vs.
  real data split.

## 1. Scope of the first batch

| Item | Value |
|------|-------|
| Trial run | **5–10 rows** hand-annotated to validate the template / import / fill / validate loop before committing to the 40-row batch. |
| Batch size | **40 oracle pilot rows** (first batch). A second batch of 40 (80 total) follows only after the first 40 pass validation + balance + train_eval. |
| Evidence mode | `oracle` only. `extracted` is NOT supported at pilot stage. |
| Evidence dims | 8 core only: `alignment`, `transparency`, `coverage`, `traceability`, `boundary`, `uncertainty`, `causal_id`, `risk_utility`. The 8 extended dims must stay `0.0` / absent. |
| Claim dims | 4: `scope`, `causal`, `action`, `certainty`. |
| Annotator | Human oracle (`source_type=oracle`, `evidence_confidence=1.0`). |
| Output scope | `pilot_diagnostic`. `paper_valid=False` always. |

## 2. Binding guardrails

1. First batch = 40 rows. Do NOT annotate 300–500 rows; that is a
   paper-ready milestone and is out of scope.
2. Use the 8 core evidence dimensions only (see §1).
3. **Every overclaim row must fill `evidence_gap_labels`**
   (e.g. `coverage_missing`, `traceability_missing`). An overclaim row
   with empty `evidence_gap_labels` is a schema violation for pilot.
4. **Overclaim rows should fill `rewrite_target`** with the revised
   claim the evidence actually supports. Leave blank only when no
   defensible rewrite exists.
5. **Do NOT write pilot results as paper results.**
6. **Do NOT enable at pilot stage:**
   - `extracted` evidence mode,
   - confidence-aware lower-bound loss with learned confidence,
   - graph evidence (R-GCN branch),
   - LLM judge baseline,
   - paper release (`run_stage_report.py` on real data),
   - 300–500 row paper-ready formal annotation.

## 3. Manual fallback flow (recommended until the loop is fully stable)

Each step writes its own artifacts, so a failure at step N does not
invalidate steps 1..N-1. Re-run from the failed step.

### 3.1 Import CSV → JSONL

```bash
python scripts/import_annotations.py \
  --input data/pilot_raw.csv \
  --output data/pilot_raw.jsonl
```

### 3.2 Auto-fill escalation labels

```bash
python scripts/fill_escalation_labels.py \
  --input data/pilot_raw.jsonl \
  --output data/pilot_filled.jsonl
```

### 3.3 Validate

```bash
python scripts/validate_data.py \
  --input data/pilot_filled.jsonl
```

### 3.4 Audit

```bash
python scripts/audit_dataset.py \
  --input data/pilot_filled.jsonl \
  --report outputs/pilot_audit.json
```

### 3.5 Check pilot balance

```bash
python scripts/check_pilot_balance.py \
  --input data/pilot_filled.jsonl \
  --report outputs/pilot_balance.json
```

A `soft_failed` status here is acceptable for a pilot diagnostic; it
must NOT block the rest of the flow. The one-shot loop treats it the
same way (top-level stays `ok`).

### 3.6 Split

```bash
python scripts/split_pilot_data.py \
  --input data/pilot_filled.jsonl \
  --output_dir data/pilot_split \
  --train_ratio 0.6 \
  --dev_ratio 0.2 \
  --test_ratio 0.2 \
  --seed 13
```

### 3.7 Train + eval

```bash
python scripts/run_stage_train_eval.py \
  --config configs/pilot_test.yaml \
  --train data/pilot_split/pilot_train.jsonl \
  --dev data/pilot_split/pilot_dev.jsonl \
  --test data/pilot_split/pilot_test.jsonl \
  --output outputs/pilot_real/train_eval \
  --step_timeout_sec 120
```

Required artifacts after this step:

```
outputs/pilot_real/train_eval/dev_predictions.jsonl
outputs/pilot_real/train_eval/operating_threshold.json   # test_split_used=false
outputs/pilot_real/train_eval/eval_test.json
outputs/pilot_real/train_eval/train_eval_summary.json
```

`operating_threshold.json` must have `test_split_used=false`: the
operating threshold is fit on dev only, never on test, to avoid test
leakage.

## 4. One-shot loop (`run_pilot_loop.py --skip_report`) — main path

When the manual flow above is green, the same stages can be run as a
single orchestrator. **This is the recommended main path for both CI
smoke and human pilot runs.**

```bash
python scripts/run_pilot_loop.py \
  --input data/pilot_filled.jsonl \
  --output outputs/pilot_loop_real \
  --config configs/pilot_test.yaml \
  --seed 13 \
  --allow_toy_results \
  --skip_report \
  --step_timeout_sec 120
```

Notes:
- `--skip_report` is the recommended main path: it skips
  `run_stage_report.py`, which is paper-release infrastructure not
  needed for pilot diagnostics. The full report can be generated
  afterwards (see §7).
- `--stage_timeout_sec` (default `step_timeout_sec * 6`) is the budget
  for the bundled `run_stage_train_eval` step. Override it only if your
  pilot rows are larger.
- The loop writes `pilot_loop_summary.json` with per-step status,
  `timeout_sec`, `log_path`, and the top-level
  `paper_valid=False` / `result_scope="pilot_diagnostic"` fields. The
  summary never lingers in `status=running` (a `finally` block
  finalizes it).
- A `BrokenPipeError` from a closed parent pipe (TRAE / pytest / timeout
  wrapper) is swallowed by `safe_print()` and does NOT mark a successful
  loop as failed.

### 4.1 Summary fields added in ocn-29

When `--skip_report` is passed, the summary additionally contains:

- `recommended_next_command`: a copy-pasteable
  `python scripts/run_stage_report.py ...` invocation that generates
  the full report on the already-produced `train_eval` artifacts. See §7.
- `train_eval_artifacts`: a map of the four canonical train_eval
  outputs (`dev_predictions`, `operating_threshold`, `eval_test`,
  `train_eval_summary`) to `{path, exists}`. If any are missing, the
  top-level `status` is downgraded to `failed` even if the
  `run_stage_train_eval` subprocess exited 0.
- `balance_findings`: `warnings` / `errors` / `ok` lifted from
  `pilot_balance.json` so an annotator can localize imbalance problems
  without opening the balance report. Balance is soft-fail; this never
  downgrades the top-level status.

## 5. When to use which flow

| Situation | Use |
|-----------|-----|
| First-time pilot, debugging a single stage | Manual flow (§3) |
| Repeatable pilot run on stable data | `run_pilot_loop.py --skip_report` (§4) |
| Suspected loop bug (summary stuck, BrokenPipe) | Manual flow (§3) to localize, then file the issue |
| Full paper-style report (post-hoc, optional) | `run_stage_report.py` manually (§7) |
| Paper-ready milestone | **Out of scope.** Neither flow is paper-ready. |

## 6. Acceptance for the 40-row batch

A 40-row oracle pilot batch is acceptable as a *diagnostic* (not
paper-ready) when ALL of:

- `validate_data.py` exits 0,
- `audit_dataset.py` exits 0,
- `check_pilot_balance.py` exits 0 or `soft_failed`,
- `split_pilot_data.py` produces `pilot_train.jsonl` / `pilot_dev.jsonl`
  / `pilot_test.jsonl`,
- `run_stage_train_eval.py` produces `dev_predictions.jsonl`,
  `operating_threshold.json` (`test_split_used=false`), `eval_test.json`,
  `train_eval_summary.json`,
- `pilot_loop_summary.json` (if using the loop) has `status=ok` and no
  step in `running`, and `train_eval_artifacts` lists all four files
  with `exists=true`.

Anything beyond this (e.g. ablations, baselines, report generation,
300+ rows) is paper-stage work and is out of scope for ocn-29.

## 7. Full report — post-hoc, optional (ocn-29)

The full `run_stage_report.py` step is **NOT** part of the CI / pilot
main path. It is paper-release infrastructure and can deadlock under
TRAE / pytest / timeout-wrapper pipe capture when run inline. Generate
it manually after a successful `--skip_report` run:

```bash
python scripts/run_stage_report.py \
  --results_dir outputs/pilot_real \
  --data data/pilot_split/pilot_train.jsonl \
  --output outputs/pilot_real/report \
  --profile pilot \
  --allow_toy_results
```

Rules:
- **Full report failure must NOT invalidate the train_eval results.**
  The `--skip_report` main path already wrote
  `dev_predictions.jsonl`, `operating_threshold.json`, `eval_test.json`,
  and `train_eval_summary.json` before the report step would have run.
  If you run the report manually and it fails, the train_eval artifacts
  are still valid for diagnostic inspection.
- The report is **never** a smoke-CI必跑项. CI smoke runs use
  `--skip_report` exclusively.
- The report output is also `paper_valid=False` /
  `result_scope="pilot_diagnostic"`; it is a diagnostic report, not a
  paper artifact.
- The `recommended_next_command` field written into the
  `--skip_report` summary is the exact invocation to use here (with
  paths already filled in for the run that just completed).

## 8. Trial annotation (5–10 rows) before the 40-row batch

Before committing to the 40-row oracle pilot batch, do a **5–10 row
trial annotation** to validate the end-to-end loop end-to-end:

1. Copy `data/templates/pilot_annotation_template.csv` to
   `data/pilot_trial.csv`.
2. Fill in 5–10 rows by hand (mix of supported and overclaim samples).
3. Run the manual flow (§3.1 → §3.5) or the one-shot loop with
   `--allow_toy_results --skip_report` (§4).
4. Confirm: import succeeds, `fill_escalation_labels` fills the empty
   `escalation_label` cells, `validate_data.py` exits 0, and
   `check_pilot_balance.py` exits 0 or `soft_failed`.
5. Only after the trial is green, proceed to the 40-row batch (§1).

The trial rows are diagnostic only and must NOT be reused as part of
the 40-row batch (re-annotate from scratch to avoid self-training on
debug data).
