# V3.17 Confidential — Public Sanitized Release Bundle

This public bundle contains only code, schemas, toy synthetic fixtures,
redacted audits, and aggregate metrics. Confidential PDFs, raw claim texts,
raw evidence spans, and real review queues are not included.

## Contents

- `scripts/` — V3.17 confidential pipeline scripts (safe subset)
- `schemas/` — JSON schemas for experiment output validation
- `data/toy_synthetic/` — Toy synthetic fixtures for testing
- `experiments/aggregate_metrics/` — Aggregate metrics with bootstrap CIs
- `experiments/redacted_audits/` — Redacted leakage and confidentiality audit results
- `paper_assets/` — Generated paper tables (LaTeX + Markdown) and figure data
- `docs/` — Selected policy and documentation files
- `MANIFEST.json` — File manifest with SHA-256 hashes
- `REDACTION_REPORT.json` — Redaction verification report

## What is NOT included

- Confidential PDF corpus (real research papers)
- Raw claim text or evidence text
- Real review queue (top-100 candidates with text)
- Private error analysis (full-text error cases)
- Model checkpoints, trained weights, or pickled artifacts
- Any file failing the confidentiality red-team scan

## Usage

```bash
# Run toy demo
python scripts/run_toy_end_to_end_demo_v1.py

# Validate schemas
python scripts/validate_experiment_outputs_v1.py

# Run red-team scan
python scripts/run_confidentiality_redteam_scan_v1.py --scan_dirs release_bundles/v3_17_confidential_public
```

## Disclaimer

All metrics are based on controlled silver diagnostic data, not gold/human-audited.
The balanced 4-class pool (109 per class) does not reflect natural prevalence.
