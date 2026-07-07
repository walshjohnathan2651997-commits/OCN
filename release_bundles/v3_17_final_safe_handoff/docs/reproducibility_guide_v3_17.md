# Reproducibility Guide — V3.17 Confidential Lightweight

> **Authority**: This guide tells you how to reproduce V3.17 artifacts,
> from the safest toy run up to the full private run, and how to build
> a sanitized public release. It is the entry point for any future
> reproducer (yourself included).
>
> **Companion documents**:
> - `docs/runbook_v3_17_confidential.md` — operator runbook for the pipeline runner
> - `artifacts_manifest_v3_17.yaml` — declarative artifact definitions
> - `reports/artifact_ledger_v3_17.csv` / `.md` — generated ledger with sensitivity flags
> - `reports/release_safety_manifest_v3_17.json` — release safety gate status
> - `docs/data_release_policy.md` — what may leave the private environment

## 1. Environment Setup

### 1.1 Prerequisites

- **OS**: Windows 11, Linux, or macOS. The reference environment is Windows 11.
- **Python**: 3.10+ (reference: `C:\Users\Administrator\AppData\Local\Programs\Python\Python310\python.exe`)
- **CPU only** — no GPU required. Toy mode runs in <10 seconds.
- **Disk**: ~500 MB for repo + toy outputs; ~5 GB if running real mode with PDFs.

### 1.2 Install dependencies

```bash
pip install -r requirements.txt
```

Required packages: `pyyaml`, `pandas`, `numpy`, `scikit-learn`, `pytest`,
`rank-bm25` (toy mode only needs `pyyaml`, `pandas`, `pytest`).

### 1.3 Verify install

```bash
python -m compileall -q scripts tests
python -m pytest tests/ -x -q
```

Expected: all tests pass (the suite is the V3.17 smoke test set).

### 1.4 Repository layout (reproducer's view)

```
d:\ocn/
├── artifacts_manifest_v3_17.yaml     # Artifact definitions (this guide's source of truth)
├── scripts/                          # Pipeline scripts (entry points)
│   ├── run_v3_17_confidential_pipeline.py    # Main runner
│   ├── build_artifact_ledger_v1.py           # Builds the ledger + safety manifest
│   ├── validate_experiment_outputs_v1.py     # Schema validation
│   ├── run_confidentiality_redteam_scan_v1.py
│   └── generate_paper_assets_v3_17.py
├── configs/                          # YAML configs (toy + private template)
├── data/                             # Toy + private datasets
├── experiments/                      # Per-experiment outputs (real + toy)
├── schemas/                          # JSON schema registry (9 schemas)
├── tests/                            # V3.17 smoke tests
├── docs/                             # This guide + runbook + data cards
├── paper_assets/v3_17_confidential/  # Paper-ready tables and drafts
├── release_bundles/v3_17_confidential_public/  # Sanitized public release
├── reports/                          # Generated ledgers and reports
└── Makefile                          # Unified entry points
```

### 1.5 Two run modes

| Mode | Flag | What it touches | Network | Authorization |
|---|---|---|---|---|
| **toy** | `--mode toy` | `data/toy_synthetic/` only | none | none |
| **full / real** | `--mode full --allow_private_data true` | `pdfs/` + private CSV | none | required |

There is **no third mode**. Anything that needs network access (e.g., sklearn
upgrade, NLI model download, LLM API) is out of scope for V3.17 mainline
reproducibility — see §4.

## 2. Toy Run (Safe for CI / Public)

The toy run reproduces the pipeline shape on synthetic data. It does **not**
reproduce real-data metrics, but it proves every script runs end-to-end
without errors.

### 2.1 Run

```bash
# Makefile entry point (Linux/macOS)
make toy

# Direct (Windows or no make)
python scripts/run_v3_17_confidential_pipeline.py --mode toy
```

### 2.2 What it runs (7 stages)

1. `corpus` — build toy sentence corpus from synthetic text
2. `retrieval` — BM25 sentence/window retrieval on toy data
3. `canonicalizer` — 8-selector canonicalizer ablation
4. `smart_queue` — SmartQueue + review queue (balanced profile)
5. `leakage_audit` — 7-check leakage audit
6. `schema_validation` — validate outputs against schema registry
7. `redteam_scan` — confidentiality red-team scanner

### 2.3 Expected output

```
experiments/v3_17_confidential_pipeline_runs/{timestamp}/
├── run_summary.json          # overall_status = "completed"
├── stage_status.csv          # per-stage status
├── run_log.txt               # combined stdout/stderr
└── config_snapshot.yaml      # effective config
```

### 2.4 Verify

```bash
python -c "import json; s=json.load(open('experiments/v3_17_confidential_pipeline_runs/LATEST/run_summary.json')); print(s['overall_status'])"
# Expected: completed
```

`schema_validation` and `redteam_scan` may report `ok_with_findings` — this
is **not** a failure; it means the scanner ran and found issues to review.

### 2.5 Expected runtime

~3 seconds total on a modern laptop. No network, no GPU, no PDFs.

## 3. Real / Private Run (Requires Authorization)

> **WARNING**: Real mode accesses confidential PDF data. Only run on
> authorized machines with the private PDF corpus present. Never upload
> PDFs, raw claim text, or raw evidence text to public repositories or
> third-party services.

### 3.1 Prerequisites

- Private PDF files in `pdfs/`
- Private candidate CSV at `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv`
- Explicit authorization (recorded in your local environment)

### 3.2 Run

```bash
python scripts/run_v3_17_confidential_pipeline.py \
    --mode full \
    --allow_private_data true \
    --config configs/v3_17_confidential_default.yaml
```

The `--allow_private_data true` flag is **mandatory**. Without it the pipeline
exits with code 2 and runs nothing.

### 3.3 What it runs (10 stages)

All 7 toy stages plus:

8. `format_shift` — format-shift ablation (8 variants × 444 candidates)
9. `r4_eval` — frozen R4 evaluation on evidence variants
10. `paper_assets` — collect paper-ready artifacts

### 3.4 Custom stages

```bash
# Only corpus + retrieval
python scripts/run_v3_17_confidential_pipeline.py \
    --mode full --allow_private_data true \
    --stages corpus,retrieval
```

### 3.5 Known blocked stages (do not re-run unless asked)

| Stage | Blocking reason | Source artifact |
|---|---|---|
| `bm25_sentence_retrieval` | `missing_pdf_corpus` — `data/pdf_corpus_v1/sentences.jsonl` not generated | `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json` |
| `r4_eval` (format-shift) | `sklearn_version_mismatch` — pickled with 1.9.0, runtime is 1.4.1; upgrade requires network | `experiments/format_shift_ablation_v1/r4_eval_blocked.json` |

These blocked artifacts are recorded in the ledger as `run_mode = blocked`.
They are not holes in reproducibility — they are documented blockages.

### 3.6 Heavy experiments (out of scope for default reproduction)

The following are **not** re-run by default. Each requires explicit user
instruction and may need network or external services:

- PDF sentence/window BM25 on real corpus (blocked)
- Format-shift R4 evaluation (blocked)
- LLM baseline (DeepSeek V3) — separate pilot, not part of V3.17 mainline

## 4. What Cannot Be Reproduced Publicly

The following artifacts are **private** and **never** appear in the public
release bundle. A reproducer without the private PDF corpus cannot regenerate
them; they can only reproduce the **shape** via toy mode.

| Artifact | Why private |
|---|---|
| `pdfs/*.pdf` | Source PDFs under confidential data agreement |
| `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv` | Contains `claim_text`, `evidence_text`, real labels |
| `data/simclaim_pdf_corpus_retrieval_v1/local_pdf_corpus_chunks.csv` | Extracted PDF chunk text |
| `experiments/canonicalizer_ablation_v1/selector_variant_evidence.csv` | Contains `selected_evidence` (raw text) |
| `experiments/format_shift_ablation_v1/format_shift_inputs.csv` | Evidence text variants |
| `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv` | Per-candidate scores linked to labels |
| `experiments/canonicalized_review_queue_v1/review_queue_top100.csv` | Top-100 queue with `claim_text`, `selected_evidence` |
| `experiments/lightweight_smart_queue_v1/smart_queue_top100.csv` | Top-100 queue with candidate IDs |

The artifact ledger (`reports/artifact_ledger_v3_17.csv`) flags each of these
with `private_sensitive = true` and `safe_to_release = false`.

**What CAN be reproduced publicly**: every metric in the paper (recall@k,
F1, precision@k, Pareto scores, leakage audit checks) is sourced from
aggregate JSON/CSV/MD files that contain no raw text. These are listed in
`reports/release_safety_manifest_v3_17.json` under `safe_to_release`.

## 5. Verifying No-API / No-Network

V3.17 mainline is hard-bound to no-API and no-network. To verify:

### 5.1 Static check (no run required)

```bash
# The redteam scanner checks for network/API calls in scripts
python scripts/run_confidentiality_redteam_scan_v1.py
cat experiments/confidentiality_redteam_scan_v1/redteam_summary.md
```

Expected: no `high` findings related to network/API.

### 5.2 Runtime check (toy mode)

```bash
# Run toy mode with network disabled at the OS level (Linux/macOS)
# Or simply observe: toy mode completes in ~3s with no network calls
python scripts/run_v3_17_confidential_pipeline.py --mode toy
```

### 5.3 CI check

The GitHub Actions workflow (`.github/workflows/smoke.yml`) runs on every
push/PR and never touches the network beyond the initial `pip install`. If
CI passes, the no-network guarantee holds for the toy path.

### 5.4 What "no network" excludes

- No `requests`, `urllib`, `httpx` calls in pipeline scripts
- No HuggingFace model downloads (R4 frozen artifacts are pickled locally)
- No LLM API calls (DeepSeek pilot is separate and out of mainline scope)
- No scikit-learn version upgrade (which would need `pip install`)

## 6. Regenerating Reports

### 6.1 Artifact ledger + release safety manifest

```bash
python scripts/build_artifact_ledger_v1.py
```

Outputs:

- `reports/artifact_ledger_v3_17.csv` — one row per artifact (52 rows)
- `reports/artifact_ledger_v3_17.md` — grouped summary with safety gate
- `reports/release_safety_manifest_v3_17.json` — machine-readable gate

Exit code 0 = gate PASS, 1 = FAIL. The script is read-only and does not
modify any artifact.

### 6.2 Schema validation report

```bash
python scripts/validate_experiment_outputs_v1.py
# or
make schema
```

Output: `experiments/schema_validation_summary.md`.

### 6.3 Confidentiality red-team scan

```bash
python scripts/run_confidentiality_redteam_scan_v1.py
# or
make redteam
```

Outputs: `experiments/confidentiality_redteam_scan_v1/redteam_summary.{md,json}`
and `redteam_findings.csv`.

### 6.4 Legacy narrative scan

```bash
python scripts/clean_legacy_narrative_scan_v1.py
```

Outputs: `reports/legacy_narrative_scan_v3_17.{csv,md}`.

Expected gate: `unsafe_current_claim = 0` and `ambiguous = 0`.

### 6.5 Project status report

```bash
python scripts/generate_project_status_report_v1.py
# or
make status
```

## 7. Regenerating Paper Assets

### 7.1 Generate all paper assets

```bash
python scripts/generate_paper_assets_v3_17.py
# or
make paper-assets
```

Outputs land in `paper_assets/v3_17_confidential/`:

- `paper_results_summary.md`
- `paper_claims_checklist.md`
- `abstract_draft.md`
- `contribution_bullets.md`
- `limitations_draft.md`
- `tables/table1_dataset_summary.md` … `table7_complexity_utility.md`

### 7.2 Paper tables are sourced from these experiment files

| Table | Source file |
|---|---|
| Table 1 (dataset) | `data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_groups_v1.csv` |
| Table 2 (retrieval) | `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json` |
| Table 4 (canonicalizer) | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` |
| Table 5 (review queue) | `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv` |
| Table 6 (leakage) | `experiments/leakage_audit_v1/audit_summary.md` |
| Table 7 (complexity) | `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` |

Every table in `paper_assets/v3_17_confidential/tables/` has a source
artifact recorded in the artifact ledger (A135–A140). The test
`tests/test_artifact_ledger_release_safety.py` verifies that every paper
table has a non-empty `generated_by_script` and a resolvable source artifact.

### 7.3 Frozen narrative documents

These are **hand-frozen** and not regenerated by a script. Edit them only
with explicit user approval:

- `docs/paper_outline_v3_17_confidential.md`
- `docs/result_narrative_freeze_v3_17.md`

## 8. Building a Sanitized Public Release

### 8.1 Build the release bundle

```bash
python scripts/build_public_sanitized_release_v1.py
# or
make release
```

Output: `release_bundles/v3_17_confidential_public/` with:

- `MANIFEST.json` — list of all included files with SHA-256 hashes
- `REDACTION_REPORT.json` — verification that no raw text is present
- All safe-to-release artifacts (configs, docs, scripts, toy data, redacted CSVs, paper assets)

### 8.2 Verify the release is safe

Before publishing, run:

```bash
# 1. Regenerate the artifact ledger (catches any new artifacts)
python scripts/build_artifact_ledger_v1.py

# 2. Check the release safety gate
python -c "import json; m=json.load(open('reports/release_safety_manifest_v3_17.json')); print(m['release_safety_gate'])"
# Expected: {'status': 'PASS', 'unsafe_public_artifacts': [], 'private_in_release': []}

# 3. Run the release safety tests
python -m pytest tests/test_artifact_ledger_release_safety.py -v

# 4. Run the redteam scan on the release bundle
python scripts/run_confidentiality_redteam_scan_v1.py
```

### 8.3 Release safety gate (what it checks)

The gate **PASS**es if and only if:

1. No artifact with `public_safe = true` contains raw text columns
   (`claim_text`, `evidence_text`, `selected_evidence`, `raw_text`,
   `clean_text`, `body_text`, `pdf_text`).
2. No artifact with `private_sensitive = true` is marked `safe_to_release`.

If either condition fails, the script exits with code 1 and the release
must NOT be published.

### 8.4 What is in the public release (categories)

- `documentation` — docs/, README, runbook, this guide
- `config` — `configs/*.yaml`
- `data_toy` — `data/toy_synthetic/*` (clearly marked synthetic)
- `metrics_csv` / `metrics_json` — aggregate experiment metrics (no raw text)
- `redacted_csv` — hash-only CSVs (SHA-256 identifiers)
- `paper_*` — paper assets (tables, drafts, checklists)
- `report_md` — summary reports
- `script` — all `scripts/*.py` (no hardcoded data)

### 8.5 What is NOT in the public release

- `pdfs/` — never
- `data/simclaim_all92_candidate_pool_v1/` — never (contains real claim text)
- `data/simclaim_pdf_corpus_retrieval_v1/local_pdf_corpus_chunks.csv` — never
- Any CSV with `claim_text`, `evidence_text`, or `selected_evidence` columns
- Any artifact flagged `private_sensitive = true` in the ledger

## 9. Quick Reference — Reproducer Decision Tree

```
Do you have the private PDF corpus?
├── NO  → Run `make toy` (§2). You can reproduce the pipeline shape
│        and all paper metrics (they are aggregate JSON/CSV). You
│        cannot reproduce per-candidate retrieval or canonicalization
│        on real data.
└── YES → Run `make p0-real` (§3) with `--allow_private_data true`.
          You can reproduce everything except the two blocked stages
          (§3.5). Blocked stages are documented, not holes.
```

## 10. Quick Reference — Artifact Ledger Fields

Each artifact in `reports/artifact_ledger_v3_17.csv` has:

| Field | Meaning |
|---|---|
| `artifact_id` | Stable ID (e.g., A030_canonicalizer_metrics) |
| `path` | Repo-relative path |
| `artifact_type` | dataset_csv, metrics_json, paper_table_md, … |
| `public_safe` | Declared safe to be public (manifest field) |
| `private_sensitive` | Contains private data (manifest field) |
| `generated_by_script` | Script that produces this artifact |
| `input_artifacts` | Comma-separated upstream artifact IDs |
| `run_mode` | real / toy / mock / blocked |
| `contains_raw_text` | Detected sensitive text columns |
| `contains_hash_only` | Only hash columns (safe) |
| `contains_labels` | Has silver/gold label columns |
| `contains_oracle_eval` | Has oracle evaluation columns |
| `safe_to_release` | Computed: public_safe AND NOT private_sensitive AND NOT contains_raw_text AND exists |
| `exists` | File present on disk |
| `detected_sensitive_columns` | CSV/JSON header scan result |
| `detected_label_columns` | CSV/JSON header scan result |
| `detected_oracle_columns` | CSV/JSON header scan result |
| `notes` | Free-text description |

## 11. Change Log

| Date | Change |
|---|---|
| 2026-07-07 | Initial V3.17 reproducibility guide created (Task Pack M) |
