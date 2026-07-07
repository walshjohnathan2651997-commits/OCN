# Sklearn Offline Compatibility Investigation (V3.17)

**Generated:** 2026-07-07
**Investigator:** Task Pack V3.17 Format-Shift R4 Offline Compatibility Investigation v1
**Scope:** Determine whether the `sklearn_version_mismatch` block on format-shift R4 evaluation can be resolved offline without violating `no_network` / `no_api` / `no_training` boundaries.

---

## 1. Summary

**Offline fix possible:** YES — Path A (local compatible sklearn environment).

A project-local `.venv` at `d:\ocn\.venv\` contains scikit-learn 1.9.0, which is the exact version the frozen R4 artifacts were pickled with. All other dependencies (transformers, torch, numpy, pandas, scipy) are present, and the NLI model `cross-encoder/nli-deberta-base` is fully cached locally. Running the eval with `HF_HUB_OFFLINE=1` requires zero network access, zero retraining, and zero model-artifact modification.

---

## 2. Environment Inventory

### 2.1 Python interpreters found on this machine

| Interpreter | Path | Version | sklearn | joblib | cloudpickle | Notes |
|---|---|---|---|---|---|---|
| Default (PATH) | `D:\Scripts\python.exe` | 3.13.7 | — | — | — | No sklearn; not usable for R4 eval |
| Python 3.10 | `C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe` | 3.10.3 | 1.4.1.post1 | 1.3.2 | — | The interpreter used by the previous blocked run; sklearn too old |
| **Project .venv** | `d:\ocn\.venv\Scripts\python.exe` | 3.13.7 | **1.9.0** | **1.5.3** | — | **Compatible** — exact match for frozen R4 artifacts |
| D:\python.exe | `D:\python.exe` | 3.13.7 | — | — | — | No sklearn |

### 2.2 Key dependency versions in the project .venv

| Package | Version | Required by eval? |
|---|---|---|
| scikit-learn | 1.9.0 | yes (R4 pickle loading + metrics) |
| joblib | 1.5.3 | yes (pickle backend) |
| numpy | 2.5.0 | yes (feature arrays) |
| pandas | 3.0.3 | yes (CSV I/O) |
| scipy | 1.18.0 | yes (sklearn dependency) |
| torch | 2.12.1+cpu | yes (NLI model inference) |
| transformers | 5.12.1 | yes (NLI model loading) |
| PyYAML | 6.0.3 | yes (config loading) |

### 2.3 No conda environments

`conda` is not installed on this machine. No conda envs are available.

### 2.4 Requirements / lockfile

- `d:\ocn\requirements.txt` specifies `scikit-learn>=1.2.0` (loose lower bound; does not pin the upper bound).
- No `pyproject.toml`, `Pipfile.lock`, `poetry.lock`, or `environment.yml` at the project root.
- The `.venv` was created independently of `requirements.txt` (it has sklearn 1.9.0, well above the >=1.2.0 floor).

### 2.5 Local pip cache

No pip wheel cache for scikit-learn was located. This is irrelevant for Path A because the `.venv` already has sklearn 1.9.0 installed — no installation step is needed.

### 2.6 NLI model local cache

The HuggingFace model `cross-encoder/nli-deberta-base` is fully cached locally at:

```
C:\Users\Administrator\.cache\huggingface\hub\models--cross-encoder--nli-deberta-base\
```

Snapshot `f375a3f8bdba5a9ea9489179fe2f7b7d69c00b76` contains all required files (symbolic links to blobs):

| File | Blob size |
|---|---|
| `model.safetensors` | 556,806,836 bytes (~532 MB) |
| `config.json` | 975 bytes |
| `tokenizer.json` | 1,356,443 bytes |
| `vocab.json` | 798,296 bytes |
| `merges.txt` | 456,356 bytes |
| `special_tokens_map.json` | 778 bytes |
| `tokenizer_config.json` | 1,135 bytes |

**Offline load verified:** With `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`, the model loads and runs inference successfully. Label order: `{contradiction: 0, entailment: 1, neutral: 2}`, which matches the script's `logits[:, [1, 2, 0]]` reordering to `[ent, neu, con]`.

### 2.7 Frozen R4 artifacts

Located at `experiments/r4_minimal_recovery_v1/artifacts/`. All 10 seeds present:

`seed_11, seed_22, seed_33, seed_44, seed_55, seed_66, seed_77, seed_88, seed_99, seed_111`

Each seed directory contains:
- `clf_contra.pkl` — LogisticRegression (contradiction classifier)
- `clf_strong.pkl` — LogisticRegression (strong-action classifier)
- `clf_svm.pkl` — LogisticRegression (SVM/mild classifier)
- `clf_flat4.pkl` — LogisticRegression (flat-4 classifier, not used by R4 cascade)
- `scaler_contra.pkl`, `scaler_strong.pkl`, `scaler_svm.pkl` — StandardScaler
- `thresholds.json` — frozen thresholds (t_contra, t_strong, t_svm)
- `feature_columns.json` — feature name lists
- `label_mapping.json` — label-to-index mapping

**Pickle load verified:** `clf_contra.pkl` and `clf_strong.pkl` load successfully with the `.venv` Python (sklearn 1.9.0). The `multi_class` attribute is absent (correct for sklearn 1.9.0), confirming the previous `AttributeError` is resolved.

---

## 3. Path Determination

| Path | Condition | Met? |
|---|---|---|
| A | Local compatible sklearn environment exists; no network, no retraining, no model modification | **YES** |
| B | Local wheel cache available for offline install into a new venv | Not needed (Path A applies) |
| C | Cannot solve offline; keep BLOCKED | Not applicable |

**Selected path: A**

Rationale:
1. The `.venv` has sklearn 1.9.0 — the exact version the frozen R4 pickles were created with.
2. All other dependencies (transformers, torch, numpy, pandas, scipy, yaml) are installed.
3. The NLI model is fully cached locally; `HF_HUB_OFFLINE=1` forces offline-only access.
4. R4 pickle files load without error.
5. NLI model inference works in offline mode.
6. No network access is required at any point.
7. No retraining is performed — the script runs frozen R4 prediction only.
8. No model artifacts are modified — pickles are loaded read-only.

---

## 4. Execution Plan (Path A)

Run `evaluate_r4_on_evidence_variants_v1.py` with the `.venv` Python and offline environment variables:

```
HF_HUB_OFFLINE=1
TRANSFORMERS_OFFLINE=1
d:\ocn\.venv\Scripts\python.exe scripts/evaluate_r4_on_evidence_variants_v1.py --config configs/v3_17_confidential_default.yaml
```

Expected outputs (in `experiments/format_shift_ablation_v1/`):
- `format_shift_predictions.csv` — per-candidate per-variant predictions
- `format_shift_metrics.csv` — variant-level metrics (strong_F1, macro_F1, etc.)
- `format_shift_summary.json` — complete summary with R4 metrics
- `format_shift_failure_examples_redacted.csv` — disagreement cases
- `r4_leakage_guard_report.json` — leakage guard report
- `schema_validation_report.json` — schema validation

---

## 5. Hard Boundaries Enforced

| Boundary | Status | Evidence |
|---|---|---|
| no_network | enforced | `HF_HUB_OFFLINE=1`, `TRANSFORMERS_OFFLINE=1`; all model files local |
| no_api | enforced | No API calls; local NLI model only |
| no_training | enforced | Frozen R4 artifacts loaded read-only; no `.fit()` calls |
| no repickling | enforced | No pickle writes; only `pickle.load` |
| no fake metrics | enforced | Real R4 prediction produces real metrics |
| no gate strictness reduction | enforced | Gate check 3.4 will be satisfied by real metrics, not by relaxation |

---

## 6. Recommended Next Action

1. Run the eval with `.venv` Python (offline mode).
2. Verify `format_shift_metrics.csv` is produced and passes schema validation.
3. Re-run `run_final_perfect_state_gate_v1.py` — check 3.4 should move from BLOCKED to PASS.
4. Update `reports/format_shift_r4_eval_blocked_v3_17.md/json` to reflect resolution.
5. Update paper text (submission_limitations_box.md, 03_format_shift_blocked_response.md).
