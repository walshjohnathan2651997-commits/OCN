# Schema Registry

This directory holds JSON schemas describing the column/key shape of every experiment output produced by the V3.17 confidential lightweight pipeline. Schemas are consumed by:

- `scripts/lib/schema_utils.py` — programmatic validation (`load_schema`, `validate_dataframe_columns`, `validate_required_columns`, `write_schema_validation_report`)
- `scripts/validate_experiment_outputs_v1.py` — repository-wide validation pass that writes `experiments/schema_validation_report.json` and `experiments/schema_validation_summary.md`
- `tests/test_schema_registry.py` — registry health tests (all schemas load, required metadata present, SmartQueue forbidden scoring fields enforced)
- `tests/test_redacted_outputs_no_text.py` — redacted output files contain no raw text columns

## Common schema fields

Every schema JSON file contains these top-level keys:

| Field | Type | Purpose |
|---|---|---|
| `name` | string | Schema identifier (matches the filename stem) |
| `version` | string | Semantic version of the schema |
| `description` | string | Human-readable description of the output |
| `file_format` | string | One of: `csv`, `jsonl`, `json` |
| `primary_file` | string | Default filename produced by the script (informational) |
| `sibling_files` | string[] | Other files sharing the schema (optional) |
| `redacted_file` | string | Public-redacted variant filename, if any (optional) |
| `required_columns` | string[] | Columns/keys that MUST be present |
| `optional_columns` | string[] | Columns/keys that MAY be present |
| `forbidden_columns_for_public_release` | string[] | Columns that MUST NOT appear in any public/redacted release (raw text, local paths, etc.) |
| `forbidden_columns_for_scoring` | string[] | Label/oracle fields that MUST NOT be used for selection, sorting, or scoring (the 9 leak-protection fields) |
| `hash_columns` | string[] | SHA-256 hash columns retained for traceability when raw text is redacted |
| `text_columns` | string[] | Columns containing raw claim/evidence text (subject to redaction) |
| `redaction_required` | bool | Whether a redacted variant MUST be produced for public release |

## Registered schemas

| Schema | File | Producer | Format | Redacted variant |
|---|---|---|---|---|
| pdf_manifest | `pdf_manifest.schema.json` | `scripts/build_pdf_sentence_corpus_v1.py` | csv | n/a (no raw text) |
| pdf_sentence_corpus | `pdf_sentence_corpus.schema.json` | `scripts/build_pdf_sentence_corpus_v1.py` | jsonl | redaction_required=true (raw_text/clean_text stripped) |
| bm25_retrieval_results | `bm25_retrieval_results.schema.json` | `scripts/run_bm25_sentence_retrieval_v1.py` | csv | `retrieval_examples_redacted.csv` |
| selector_variant_evidence | `selector_variant_evidence.schema.json` | `scripts/run_canonicalizer_ablation_v1.py` | csv | `selector_examples_redacted.csv` |
| format_shift_inputs | `format_shift_inputs.schema.json` | `scripts/run_format_shift_ablation_v1.py` | csv | `format_shift_inputs_redacted.csv` |
| format_shift_metrics | `format_shift_metrics.schema.json` | `scripts/evaluate_r4_on_evidence_variants_v1.py` | csv | n/a (no raw text) |
| r4_review_scores | `r4_review_scores.schema.json` | `scripts/run_canonicalized_review_queue_v1.py`, `scripts/run_canonicalized_risk_ranking_v1.py` | csv | redaction_required=true (selected_evidence/claim_text/source_pdf stripped) |
| smart_queue_scores | `smart_queue_scores.schema.json` | `scripts/run_lightweight_smart_queue_v1.py` | csv | n/a (no raw text) |
| leakage_audit | `leakage_audit.schema.json` | `scripts/run_leakage_audit_v1.py` | json | n/a (no raw text) |

## The 9 forbidden scoring fields

These fields must NEVER appear in any scoring/sorting/selection output column list. They are encoded in `forbidden_columns_for_scoring` for `smart_queue_scores` (the canonical SmartQueue scoring output). The `r4_review_scores` schema intentionally leaves `forbidden_columns_for_scoring` empty because it describes a REVIEW OUTPUT where `true_label` and `oracle_hit` legitimately appear for offline metrics — their absence from sorting keys is verified at the source-code level by `tests/test_no_leakage_fields.py`.

1. `true_label`
2. `is_strong_action`
3. `oracle_hit`
4. `candidate_label_guess`
5. `final_label`
6. `gold_label`
7. `human_audited`
8. `evidence_text`
9. `evidence_text_sha256`

## Adding a new schema

1. Pick a `snake_case` name and create `<name>.schema.json` in this directory.
2. Fill in all required top-level keys listed above.
3. For any output that contains raw claim/evidence text, set `redaction_required: true` and list the text columns under `text_columns` and `forbidden_columns_for_public_release`.
4. For any per-candidate scoring output, copy the 9 forbidden scoring fields above into `forbidden_columns_for_scoring`.
5. Add a row to the "Registered schemas" table in this file.
6. Add a test case in `tests/test_schema_registry.py` covering the new schema.
7. If the new schema is produced by a script under `scripts/`, wire `scripts/lib/schema_utils.py` validation into the script's tail (see `run_lightweight_smart_queue_v1.py` for the pattern).

## Validation report

`scripts/validate_experiment_outputs_v1.py` walks `experiments/` and validates each known output against its schema. The report contains:

- `schema_validation_report.json` — machine-readable per-file pass/fail with column-level diagnostics
- `schema_validation_summary.md` — human-readable markdown summary

Each producing script also writes a per-directory `schema_validation_report.json` at the end of its run, so a failed validation is visible in the same directory as the offending output.
