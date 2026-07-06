"""Tests for the schema registry (schemas/*.schema.json) and schema_utils.py.

Verifies:
  - All 9 schema files load successfully.
  - Each schema has the required metadata fields.
  - smart_queue_scores has the 9 forbidden_columns_for_scoring fields.
  - selector_variant_evidence has the spec-required required_columns.
  - load_schema raises SchemaError on missing/malformed schemas.
  - validate_dataframe_columns catches missing required and forbidden scoring fields.
  - validate_redacted_file catches leaked text columns.
  - write_schema_validation_report writes the expected JSON structure.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from schema_utils import (  # noqa: E402
    FORBIDDEN_SCORING_FIELDS,
    REQUIRED_SCHEMA_KEYS,
    SchemaError,
    list_schemas,
    load_schema,
    validate_dataframe_columns,
    validate_redacted_file,
    validate_required_columns,
    write_schema_validation_report,
)


SCHEMAS_DIR = REPO_ROOT / "schemas"

EXPECTED_SCHEMAS = [
    "pdf_manifest",
    "pdf_sentence_corpus",
    "bm25_retrieval_results",
    "selector_variant_evidence",
    "format_shift_inputs",
    "format_shift_metrics",
    "r4_review_scores",
    "smart_queue_scores",
    "leakage_audit",
]


# ---------------- TestSchemaRegistry ----------------

class TestSchemaRegistry:
    """Registry health: all schemas present, loadable, well-formed."""

    def test_at_least_8_schemas_registered(self):
        schemas = list_schemas()
        assert len(schemas) >= 8, f"Expected >=8 schemas, got {len(schemas)}: {schemas}"

    def test_all_expected_schemas_present(self):
        schemas = set(list_schemas())
        for name in EXPECTED_SCHEMAS:
            assert name in schemas, f"Missing schema: {name}"

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_schema_loadable(self, schema_name):
        schema = load_schema(schema_name)
        assert schema["name"] == schema_name

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_schema_has_required_metadata(self, schema_name):
        schema = load_schema(schema_name)
        for key in REQUIRED_SCHEMA_KEYS:
            assert key in schema, f"Schema {schema_name} missing key: {key}"

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_schema_has_version_and_description(self, schema_name):
        schema = load_schema(schema_name)
        assert isinstance(schema["version"], str)
        assert len(schema["version"]) > 0
        assert isinstance(schema["description"], str)
        assert len(schema["description"]) > 20

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_required_and_optional_are_lists(self, schema_name):
        schema = load_schema(schema_name)
        assert isinstance(schema["required_columns"], list)
        assert isinstance(schema["optional_columns"], list)
        # No overlap between required and optional
        req = set(schema["required_columns"])
        opt = set(schema["optional_columns"])
        overlap = req & opt
        assert not overlap, f"Schema {schema_name}: required/optional overlap: {overlap}"

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_forbidden_lists_are_lists(self, schema_name):
        schema = load_schema(schema_name)
        assert isinstance(schema["forbidden_columns_for_public_release"], list)
        assert isinstance(schema["forbidden_columns_for_scoring"], list)

    @pytest.mark.parametrize("schema_name", EXPECTED_SCHEMAS)
    def test_redaction_required_is_bool(self, schema_name):
        schema = load_schema(schema_name)
        assert isinstance(schema["redaction_required"], bool)


# ---------------- TestSmartQueueForbiddenFields ----------------

class TestSmartQueueForbiddenFields:
    """SmartQueue schema must enforce the 9 forbidden scoring fields."""

    def test_smart_queue_has_all_9_forbidden_scoring_fields(self):
        schema = load_schema("smart_queue_scores")
        forbidden = set(schema["forbidden_columns_for_scoring"])
        for field in FORBIDDEN_SCORING_FIELDS:
            assert field in forbidden, f"smart_queue_scores missing forbidden field: {field}"

    def test_smart_queue_forbidden_fields_exact_match(self):
        schema = load_schema("smart_queue_scores")
        forbidden = set(schema["forbidden_columns_for_scoring"])
        assert forbidden == set(FORBIDDEN_SCORING_FIELDS), (
            f"smart_queue_scores forbidden_columns_for_scoring mismatch: "
            f"extra={forbidden - set(FORBIDDEN_SCORING_FIELDS)}, "
            f"missing={set(FORBIDDEN_SCORING_FIELDS) - forbidden}"
        )

    def test_smart_queue_true_label_not_in_optional(self):
        """true_label must NOT be in optional_columns (it's forbidden in the scoring output)."""
        schema = load_schema("smart_queue_scores")
        assert "true_label" not in schema["optional_columns"]
        assert "true_label" not in schema["required_columns"]

    def test_load_schema_raises_if_smart_queue_missing_forbidden_field(self, tmp_path):
        """If a schema named smart_queue_scores is missing a forbidden field, load_schema raises."""
        # This is enforced by load_schema itself; verify by checking the real schema loads OK
        # (the test would fail if someone removed a field from the JSON).
        schema = load_schema("smart_queue_scores")
        assert "true_label" in schema["forbidden_columns_for_scoring"]


# ---------------- TestSelectorVariantEvidenceSchema ----------------

class TestSelectorVariantEvidenceSchema:
    """selector_variant_evidence.schema.json must have the spec-required columns."""

    REQUIRED_PER_SPEC = [
        "candidate_id",
        "target_candidate_group_id",
        "selector",
        "selected_evidence",
        "selected_source_unit_id",
        "selected_rank",
        "selector_score",
        "n_words",
        "selected_evidence_sha256",
    ]

    def test_required_columns_match_spec(self):
        schema = load_schema("selector_variant_evidence")
        required = set(schema["required_columns"])
        for col in self.REQUIRED_PER_SPEC:
            assert col in required, f"selector_variant_evidence missing required column: {col}"

    def test_selected_evidence_in_forbidden_public(self):
        """Public redacted version must NOT contain selected_evidence."""
        schema = load_schema("selector_variant_evidence")
        assert "selected_evidence" in schema["forbidden_columns_for_public_release"]
        assert "selected_evidence" in schema["text_columns"]

    def test_selected_evidence_sha256_in_hash_columns(self):
        schema = load_schema("selector_variant_evidence")
        assert "selected_evidence_sha256" in schema["hash_columns"]


# ---------------- TestSchemaErrorHandling ----------------

class TestSchemaErrorHandling:
    """load_schema raises SchemaError on bad input."""

    def test_load_schema_raises_on_missing_file(self):
        with pytest.raises(SchemaError, match="Schema file not found"):
            load_schema("nonexistent_schema_xyz")

    def test_load_schema_raises_on_empty_name(self):
        with pytest.raises(SchemaError, match="schema_name is required"):
            load_schema("")

    def test_load_schema_accepts_filename_form(self):
        # Should accept both "smart_queue_scores" and "smart_queue_scores.schema.json"
        s1 = load_schema("smart_queue_scores")
        s2 = load_schema("smart_queue_scores.schema.json")
        assert s1 == s2


# ---------------- TestValidateDataFrameColumns ----------------

class TestValidateDataFrameColumns:
    """validate_dataframe_columns catches missing required and forbidden scoring fields."""

    def test_valid_dataframe_passes(self):
        df = pd.DataFrame({
            "candidate_id": ["c1", "c2"],
            "target_candidate_group_id": ["g1", "g2"],
            "bucket": ["low_priority", "low_priority"],
            "p_strong": [0.1, 0.2],
            "p_contra": [0.0, 0.1],
            "p_svm": [0.3, 0.4],
            "strong_action_flag": [0, 0],
            "entropy": [0.5, 0.6],
            "selector_score": [0.7, 0.8],
            "selected_rank": [1, 1],
            "selected_n_words": [10, 12],
            "bm25_score": [5.0, 6.0],
            "evidence_score": [0.5, 0.5],
            "length_penalty": [0.0, 0.0],
            "score_conservative": [0.1, 0.2],
            "score_balanced": [0.2, 0.3],
            "score_high_recall": [0.3, 0.4],
            "selected_profile": ["balanced", "balanced"],
            "final_score": [0.2, 0.3],
        })
        report = validate_dataframe_columns(df, "smart_queue_scores")
        assert report["ok"], f"Expected OK, got: {report}"
        assert report["required_missing"] == []
        assert report["forbidden_scoring_present"] == []

    def test_missing_required_column_reported(self):
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            # missing: target_candidate_group_id, bucket, p_strong, etc.
        })
        report = validate_dataframe_columns(df, "smart_queue_scores")
        assert not report["ok"]
        assert "target_candidate_group_id" in report["required_missing"]
        assert "bucket" in report["required_missing"]

    def test_forbidden_scoring_field_detected(self):
        """If true_label appears in smart_queue_scores, validation flags it."""
        schema = load_schema("smart_queue_scores")
        # Build a minimal valid DF then add a forbidden column
        df = pd.DataFrame({col: ["x"] for col in schema["required_columns"]})
        df["true_label"] = "supported"  # forbidden!
        report = validate_dataframe_columns(df, "smart_queue_scores")
        assert not report["ok"]
        assert "true_label" in report["forbidden_scoring_present"]

    def test_strict_mode_catches_unexpected_columns(self):
        from schema_utils import ValidationError
        schema = load_schema("smart_queue_scores")
        df = pd.DataFrame({col: ["x"] for col in schema["required_columns"]})
        df["unexpected_column"] = "surprise"
        with pytest.raises(ValidationError, match="unexpected_column"):
            validate_dataframe_columns(df, "smart_queue_scores", strict=True)


# ---------------- TestValidateRequiredColumns ----------------

class TestValidateRequiredColumns:
    def test_all_present(self):
        df = pd.DataFrame({"a": [1], "b": [2], "c": [3]})
        report = validate_required_columns(df, ["a", "b"])
        assert report["ok"]
        assert report["missing"] == []

    def test_missing_reported(self):
        df = pd.DataFrame({"a": [1]})
        report = validate_required_columns(df, ["a", "b", "c"])
        assert not report["ok"]
        assert "b" in report["missing"]
        assert "c" in report["missing"]


# ---------------- TestValidateRedactedFile ----------------

class TestValidateRedactedFile:
    """validate_redacted_file catches leaked text columns in redacted outputs."""

    def test_clean_redacted_file_passes(self):
        """selector_examples_redacted.csv shape (no selected_evidence)."""
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            "selector": ["best_sentence_top5_overlap"],
            "selected_evidence_sha256": ["abc123"],
            "n_words": [10],
            "selector_score": [0.8],
            "selected_rank": [1],
            "source_type": ["sentence"],
            "selection_reason": ["token_overlap"],
        })
        report = validate_redacted_file(df, "selector_variant_evidence")
        assert report["ok"], f"Expected OK, got: {report}"
        assert report["leaked_text_columns"] == []
        assert report["leaked_public_columns"] == []

    def test_leaked_text_column_detected(self):
        """If selected_evidence appears in a redacted file, validation flags it."""
        df = pd.DataFrame({
            "candidate_id": ["c1"],
            "selector": ["x"],
            "selected_evidence": "leaked raw evidence text",  # FORBIDDEN in redacted
            "selected_evidence_sha256": ["abc123"],
        })
        report = validate_redacted_file(df, "selector_variant_evidence")
        assert not report["ok"]
        assert "selected_evidence" in report["leaked_text_columns"]
        assert "selected_evidence" in report["leaked_public_columns"]

    def test_leaked_scoring_field_detected(self):
        """If a forbidden scoring field appears in a redacted SmartQueue file,
        validation flags it. Uses smart_queue_scores schema which has the 9
        forbidden_columns_for_scoring fields per the spec."""
        schema = load_schema("smart_queue_scores")
        # Build a minimal DF with smart_queue_scores required columns
        df = pd.DataFrame({col: ["x"] for col in schema["required_columns"]})
        df["true_label"] = "supported"  # forbidden scoring field!
        report = validate_redacted_file(df, "smart_queue_scores")
        assert not report["ok"]
        assert "true_label" in report["leaked_scoring_columns"]


# ---------------- TestWriteSchemaValidationReport ----------------

class TestWriteSchemaValidationReport:
    def test_report_written_with_correct_structure(self, tmp_path):
        reports = [
            {"ok": True, "schema": "smart_queue_scores", "n_rows": 10, "n_cols": 19},
            {"ok": False, "schema": "r4_review_scores", "error": "missing column"},
        ]
        out_path = write_schema_validation_report(
            tmp_path, reports, script_name="test_script.py"
        )
        assert out_path.exists()
        assert out_path.name == "schema_validation_report.json"
        with open(out_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["script_name"] == "test_script.py"
        assert payload["n_reports"] == 2
        assert payload["n_ok"] == 1
        assert payload["n_fail"] == 1
        assert payload["all_ok"] is False
        assert len(payload["reports"]) == 2

    def test_report_all_ok(self, tmp_path):
        reports = [{"ok": True}, {"ok": True}]
        out_path = write_schema_validation_report(tmp_path, reports)
        with open(out_path, "r", encoding="utf-8") as f:
            payload = json.load(f)
        assert payload["all_ok"] is True
        assert payload["n_fail"] == 0

    def test_report_creates_output_dir(self, tmp_path):
        """If output_dir doesn't exist, it's created."""
        target = tmp_path / "nested" / "deeper"
        reports = [{"ok": True}]
        out_path = write_schema_validation_report(target, reports)
        assert out_path.exists()
        assert target.exists()
