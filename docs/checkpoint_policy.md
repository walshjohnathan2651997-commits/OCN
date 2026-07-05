# Checkpoint Policy

This document explains how model checkpoints (`*.pt` / `*.pth` / `*.ckpt` / `*.bin`)
are handled in CESE-OCN releases, why the lightweight share package excludes them
by default, and how to obtain or regenerate them.

## 1. Default: checkpoints are NOT included in the share package

`scripts/package_project_for_share.py` enforces a strict exclude list:

```python
EXCLUDE_PATTERNS = [
    "*.pt", "*.pth", "*.ckpt", "*.bin",
    ...
]
EXCLUDE_SUBPATHS = [
    "multiseed/seed_*/best.pt",
    "train_eval/train/best.pt",
]
```

Consequence: the lightweight zip produced by `package_project_for_share.py`
contains **tables, reports, prediction jsonl, manifests, configs, and source
code only**. It does **not** contain any loadable model weights.

This is intentional:

- A single `distilbert-base-uncased` checkpoint is ~254 MB; the full pilot release
  ships 4 checkpoints (~1 GB). Bundling them would make the share package
  unusable for code review, CI smoke, and email/PR distribution.
- Checkpoints are regeneratable from `configs/pilot_bert.yaml` + the pilot
  train/dev splits, so excluding them does not lose reproducibility.
- Mixing loadable weights with table-only releases causes reviewers to
  confuse "tables look good" with "model is available", which has caused
  incorrect `paper_ready` declarations in the past.

## 2. Three legitimate ways to obtain a checkpoint

| Situation | Action |
|---|---|
| Reviewer / collaborator wants to load the trained pilot model | **(a)** Ask the release author to share `release_simclaim_human_pilot/train_eval/train/best.pt` and `release_simclaim_human_pilot/multiseed/seed_{7,42,123}/best.pt` via external storage (网盘 / OSS / internal release server). Then drop them into the same paths locally. |
| Has HuggingFace network access, no checkpoint | **(b)** Re-train with `configs/pilot_bert.yaml`: `python scripts/run_stage_model_train.py --config configs/pilot_bert.yaml --train data/human_pilot/splits/train.jsonl --dev data/human_pilot/splits/dev.jsonl --output outputs/pilot_stage_bert/model_train --step_timeout_sec 600`. The resulting `outputs/pilot_stage_bert/model_train/train/best.pt` is a real BERT pilot checkpoint. |
| Offline (no HuggingFace), no checkpoint | **(c)** Cannot run real BERT. Run stub smoke only: `configs/smoke_test.yaml` or `configs/pilot_test.yaml` (both use the `test-stub` encoder). Do **not** treat stub output as BERT result. |

See `GPT_QUICKSTART.md` section 7 for the exact commands.

## 3. Loading a checkpoint

```python
import torch
ckpt = torch.load(
    "release_simclaim_human_pilot/train_eval/train/best.pt",
    map_location="cpu",
    weights_only=False,
)
print(ckpt.keys())  # ['model', 'epoch', 'dev_loss', 'config', ...]
```

For multi-seed reproduction, the three seeds used in the pilot release are
`seed=7`, `seed=42`, `seed=123`. Each lives under
`release_simclaim_human_pilot/multiseed/seed_<N>/best.pt`.

## 4. Paper release vs lightweight share

- **Lightweight share zip** (default `package_project_for_share.py` output):
  source + configs + tables + reports + prediction jsonl. No `.pt`. Suitable
  for code review, CI smoke, paper review at the table level.
- **Paper release bundle** (separately distributed, not via the share zip):
  the above plus `*.pt` checkpoints (~1 GB) and the matching
  `RESULTS_MANIFEST.json` snapshot. Required only when a reviewer needs to
  re-run evaluation on the exact trained model.

Do not mix the two: a `RESULTS_MANIFEST.json` that claims `paper_ready=true`
must be accompanied by an actual checkpoint bundle, and vice versa.

## 5. Manifest fields affected by checkpoint absence

`RESULTS_MANIFEST.json` reflects the state of artifacts actually present in
the release directory. If `best.pt` is absent (the default lightweight share
case), the following fields are unaffected but should be read together with
`paper_ready`:

- `weak_baselines_complete`: weak baseline stage ran and produced CSV.
- `strong_baselines_complete`: all 5 strong baselines have `metric_valid=true`.
- `strong_baselines_min_complete`: at least `structured_llm_judge` +
  `nli_scifact_style` ran with real metrics.
- `adversarial_eval_complete`: `cese_ocn` has `metric_valid=true` on the
  standard split AND at least 2 adversarial splits.
- `paper_ready`: only `true` if every blocking reason is cleared AND the
  dataset is the paper-full dataset (not pilot).

In the current `release_simclaim_human_pilot`:

```json
{
  "weak_baselines_complete": true,
  "strong_baselines_complete": false,
  "strong_baselines_min_complete": false,
  "adversarial_eval_complete": false,
  "paper_ready": false
}
```

This honestly reflects that the pilot release is diagnostic only — the absence
of checkpoints is just one of several blocking reasons (pilot dataset, missing
strong baselines, missing adversarial splits, etc.).

## 6. Reproducibility contract

A reviewer reproducing the pilot results must:

1. Obtain `release_simclaim_human_pilot/train_eval/train/best.pt` (or re-train
   with `configs/pilot_bert.yaml`).
2. Run `scripts/run_adversarial_eval.py` with `--profile pilot` and the
   checkpoint path.
3. Compare the resulting `adversarial_results.csv` against the one in the
   release directory. Numbers should match within seed tolerance.

If step 1 cannot be satisfied (no checkpoint, no HuggingFace access), the
reviewer can still audit tables / code / configs but cannot reproduce metric
values. This is a known limitation of the offline lightweight share and is
the reason `paper_ready=false`.
