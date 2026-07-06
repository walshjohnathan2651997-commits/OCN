# V3.17 Confidential Lightweight Pipeline — Runbook

> **Confidentiality warning**: This pipeline processes proprietary PDF data
> under a confidential data agreement. Never upload PDFs, raw evidence text,
> or real claim text to public repositories, third-party tools, or external
> services. All public artifacts must be redacted (SHA-256 hashes only).

## 1. Environment Setup

### Prerequisites

- Python 3.10+
- Dependencies: `pip install -r requirements.txt`
- PyYAML, pandas, numpy, scikit-learn (for full mode)
- No GPU required (toy mode runs in <5 seconds)

### Repository Structure

```
d:\ocn/
├── configs/                    # YAML configs (toy + private template)
├── data/
│   ├── toy_synthetic/          # Toy data (safe for CI/public)
│   └── simclaim_all92_.../     # Private candidate CSV (NEVER commit)
├── experiments/                # Experiment outputs (per-run)
├── pdfs/                       # Private PDF source files (NEVER commit)
├── schemas/                    # JSON schema registry (9 schemas)
├── scripts/                    # Pipeline scripts
├── tests/                      # Test suite (183 tests)
├── Makefile                    # Unified entry points
└── docs/                       # Documentation (this file)
```

### Config Files

| Config | Purpose | Mode |
|--------|---------|------|
| `configs/toy_demo.yaml` | Toy synthetic data | `--mode toy` |
| `configs/v3_17_confidential_default.yaml` | Real private data | `--mode full` |
| `configs/local_private_template.yaml` | Local override template | Manual |

## 2. Toy Run (Safe for CI/Public)

### Quick Start

```bash
# Using Makefile (recommended on Linux/macOS)
make toy

# Using Python directly (Windows or no make)
python scripts/run_v3_17_confidential_pipeline.py --mode toy
```

### What It Does

The toy pipeline runs 7 stages on synthetic data:

1. **corpus** — Build toy sentence corpus from synthetic text
2. **retrieval** — BM25 sentence/window retrieval on toy data
3. **canonicalizer** — Evidence canonicalizer ablation (8 selectors)
4. **smart_queue** — SmartQueue + review queue (balanced profile)
5. **leakage_audit** — 7-check leakage audit
6. **schema_validation** — Validate outputs against schema registry
7. **redteam_scan** — Confidentiality red-team scanner

### Expected Output

```
experiments/v3_17_confidential_pipeline_runs/{timestamp}/
├── run_summary.json          # Overall status + per-stage results
├── run_log.txt               # Combined stdout/stderr
├── stage_status.csv          # Per-stage start/end/status/runtime
└── config_snapshot.yaml      # Effective config snapshot
```

### Expected Runtime

- **Toy mode**: ~3 seconds total (all 7 stages)
- Individual stages: 0.1–1.0 seconds each

### Verifying Success

```bash
# Check overall status
python -c "import json; s=json.load(open('experiments/v3_17_confidential_pipeline_runs/LATEST/run_summary.json')); print(s['overall_status'])"
# Expected: completed

# Check stage results
cat experiments/v3_17_confidential_pipeline_runs/LATEST/stage_status.csv
```

> **Note**: `schema_validation` and `redteam_scan` may show status
> `ok_with_findings` (exit code 1). This means the scripts ran successfully
> but found issues (e.g., missing files or risk findings). This is NOT a
> pipeline failure — the pipeline continues and records the findings.

## 3. Full Private Run (Requires Authorization)

> **WARNING**: Full mode accesses confidential PDF data. Only run on
> authorized machines with the private PDF corpus present.

### Prerequisites

- Private PDF files in `pdfs/` directory
- Private candidate CSV at `data/simclaim_all92_candidate_pool_v1/...`
- Explicit authorization to access private data

### Running Full Mode

```bash
# The --allow_private_data flag is REQUIRED for full mode
python scripts/run_v3_17_confidential_pipeline.py \
    --mode full \
    --allow_private_data true \
    --config configs/v3_17_confidential_default.yaml
```

### What It Does

Full mode runs all 10 stages:

1. **corpus** — Extract sentences from real PDFs
2. **retrieval** — BM25 retrieval on real corpus
3. **canonicalizer** — Evidence canonicalizer ablation
4. **format_shift** — Format-shift ablation
5. **r4_eval** — Frozen R4 evaluation on evidence variants
6. **smart_queue** — SmartQueue + review queue
7. **leakage_audit** — 7-check leakage audit
8. **schema_validation** — Validate outputs against schema registry
9. **redteam_scan** — Confidentiality red-team scanner
10. **paper_assets** — Collect paper-ready artifacts

### Authorization Check

If you run full mode without `--allow_private_data true`:

```
ERROR: full mode requires --allow_private_data true
       This flag confirms you have authorization to access private PDF data.
```

The pipeline exits with code 2 and does NOT run any stage.

### Custom Stages

You can run specific stages:

```bash
# Only corpus and retrieval
python scripts/run_v3_17_confidential_pipeline.py \
    --mode full \
    --allow_private_data true \
    --stages corpus,retrieval

# Skip R4 eval (requires NLI model download)
python scripts/run_v3_17_confidential_pipeline.py \
    --mode full \
    --allow_private_data true \
    --stages corpus,retrieval,canonicalizer,smart_queue,leakage_audit
```

### Available Stages

| Stage | Description | Toy | Full |
|-------|-------------|-----|------|
| `corpus` | Build PDF sentence corpus | ✓ | ✓ |
| `retrieval` | BM25 sentence/window retrieval | ✓ | ✓ |
| `canonicalizer` | Evidence canonicalizer ablation | ✓ | ✓ |
| `format_shift` | Format-shift ablation | — | ✓ |
| `r4_eval` | Frozen R4 evaluation | — | ✓ |
| `smart_queue` | SmartQueue + review queue | ✓ | ✓ |
| `leakage_audit` | 7-check leakage audit | ✓ | ✓ |
| `schema_validation` | Schema registry validation | ✓ | ✓ |
| `redteam_scan` | Confidentiality scanner | ✓ | ✓ |
| `paper_assets` | Collect paper-ready artifacts | — | ✓ |

## 4. Expected Outputs

### Per-Stage Outputs

| Stage | Output Directory | Key Files |
|-------|-----------------|-----------|
| corpus | `data/pdf_corpus_v1/` (or `_toy_v1`) | `sentences.jsonl`, `pdf_manifest.csv` |
| retrieval | `experiments/bm25_sentence_retrieval_v1/` | `retrieval_results_*.csv`, `oracle_recall_summary.json` |
| canonicalizer | `experiments/canonicalizer_ablation_v1/` | `selector_variant_evidence.csv`, `selector_metrics_summary.csv` |
| format_shift | `experiments/format_shift_ablation_v1/` | `format_shift_inputs.csv`, `format_shift_metrics.csv` |
| r4_eval | `experiments/r4_eval_v1/` | `r4_review_scores.csv`, `r4_metrics.json` |
| smart_queue | `experiments/lightweight_smart_queue_v1/` | `smart_queue_scores.csv`, `smart_queue_top100.csv` |
| leakage_audit | `experiments/leakage_audit_v1/` | `audit_summary.json`, `audit_summary.md` |
| schema_validation | `experiments/` | `schema_validation_report.json`, `schema_validation_summary.md` |
| redteam_scan | `experiments/confidentiality_redteam_scan_v1/` | `redteam_findings.csv`, `redteam_summary.json`, `redteam_summary.md` |
| paper_assets | `{run_dir}/paper_assets/` | `paper_assets_manifest.json` + collected files |

### Pipeline Run Outputs

Every pipeline run creates a timestamped directory under
`experiments/v3_17_confidential_pipeline_runs/{timestamp}/` containing:

- **`run_summary.json`** — Overall status, stage list, per-stage details
- **`stage_status.csv`** — Tabular per-stage status (stage, status, start, end, runtime, exit_code)
- **`run_log.txt`** — Combined stdout/stderr from all stages
- **`config_snapshot.yaml`** — Copy of the effective config

## 5. Troubleshooting

### Stage Fails: "Script not found"

**Cause**: A stage script is missing from `scripts/`.

**Fix**: Verify the script exists:
```bash
ls scripts/build_pdf_sentence_corpus_v1.py
ls scripts/run_bm25_sentence_retrieval_v1.py
# ... etc
```

### Stage Fails: Timeout

**Cause**: A stage exceeded the 600-second (10-minute) timeout.

**Fix**: For `r4_eval` (which loads NLI models), ensure you have a stable
network connection for the initial model download. The model is cached
after the first run. If the timeout persists, run the stage directly:
```bash
python scripts/evaluate_r4_on_evidence_variants_v1.py --toy_mode
```

### schema_validation Shows "ok_with_findings"

**Cause**: One or more experiment output files don't match their schema.
This is informational — the validation script ran successfully.

**Fix**: Check the validation report:
```bash
cat experiments/schema_validation_summary.md
```
Look for `[FAIL]` entries and fix the underlying output files.

### redteam_scan Shows "ok_with_findings"

**Cause**: The scanner found risk findings (high/medium/low). This is
expected — the scanner's job is to find risks.

**Fix**: Review the findings:
```bash
cat experiments/confidentiality_redteam_scan_v1/redteam_summary.md
```
Address high-risk findings before public release.

### Pipeline Stops Mid-Run

**Cause**: A stage failed (status `failed`), and the pipeline stops to
prevent cascading errors.

**Fix**: Check `run_log.txt` for the failing stage's output, fix the
underlying issue, and re-run. You can skip the failed stage:
```bash
python scripts/run_v3_17_confidential_pipeline.py \
    --mode toy \
    --stages corpus,retrieval,canonicalizer,smart_queue
```

### "full mode requires --allow_private_data true"

**Cause**: You ran full mode without the authorization flag.

**Fix**: Add `--allow_private_data true` to confirm you have authorization.

## 6. Confidentiality Warnings

### What NEVER to Commit

- `pdfs/` — Private PDF source files
- `data/simclaim_all92_candidate_pool_v1/` — Private candidate CSV with real claim text
- `data/private/` — Any private data directory
- `experiments/private/` — Private experiment outputs
- `*.pdf`, `*.docx`, `*.xlsx` — Binary document files
- `*.npz`, `*.pkl`, `*.joblib` — Binary data files (may contain cached models)

### What IS Safe to Commit

- `scripts/` — All Python scripts (no hardcoded data)
- `tests/` — All test files (use toy data only)
- `schemas/` — JSON schema definitions
- `configs/` — YAML configs (paths only, no data)
- `data/toy_synthetic/` — Toy synthetic data (clearly marked)
- `docs/` — Documentation
- `Makefile`, `.github/workflows/` — CI configuration

### Redaction Policy

All public artifacts must be redacted:
- Replace `claim_text` with `claim_text_sha256`
- Replace `evidence_text` with `evidence_text_sha256`
- Replace `selected_evidence` with `selected_evidence_sha256`
- Replace `source_pdf` with `source_pdf_sha256`
- Never include `true_label`, `oracle_hit`, or `gold_label` in scoring outputs

### .gitignore Verification

The `.gitignore` should include:
```
pdfs/
private_pdfs/
data/private/
experiments/private/
*.pdf
*.docx
*.xlsx
*.npz
*.pkl
*.joblib
```

Run `make check-no-private-delete` to verify the Makefile never deletes
private data.

## 7. Makefile Targets

| Target | Description |
|--------|-------------|
| `make toy` | Run full toy pipeline (7 stages) |
| `make validate` | Validate experiment outputs against schemas |
| `make redteam` | Run confidentiality red-team scanner |
| `make schemas` | Check schema registry health (pytest) |
| `make clean-toy` | Remove toy outputs (NOT private data) |
| `make paper-assets` | Collect paper-ready artifacts |
| `make test` | Run V3.17 smoke test suite (183 tests) |
| `make compile` | Compile-check all scripts and tests |
| `make help` | Show available targets |
| `make check-no-private-delete` | Verify no private data deletion |

### Clean-Toy Safety

`make clean-toy` only removes:
- `experiments/*_toy` directories
- `experiments/v3_17_confidential_pipeline_runs/`
- `experiments/toy_end_to_end_demo_v1/`
- `data/pdf_corpus_toy_v1/`

It does NOT touch:
- `pdfs/`
- `data/private/`
- `data/simclaim_all92_.../`
- `experiments/private/`

## 8. CI Integration

The GitHub Actions workflow (`.github/workflows/smoke.yml`) runs on every
push/PR to `main` or `dev`:

1. **Compile check** — `python -m compileall -q scripts tests`
2. **Smoke tests** — 183 tests across 8 test files
3. **Doc verification** — V3.17 + confidential + lightweight mentioned in README
4. **Data release policy** — Policy document exists

CI never touches real data, never calls APIs, and never requires network
access beyond the initial dependency install.
