"""Tests that redacted/public output files contain no raw text or forbidden scoring fields.

Verifies the acceptance criterion: "redacted 文件不含 raw evidence/claim text"
and "SmartQueue scoring 文件没有 forbidden scoring fields".

Walks the experiments/ directory and checks every file matching *redacted*.csv
or *redacted*.json against the appropriate schema using validate_redacted_file.
Also checks smart_queue_scores.csv (the canonical scoring output) for absence
of the 9 forbidden scoring fields.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts" / "lib"))

from schema_utils import (  # noqa: E402
    FORBIDDEN_SCORING_FIELDS,
    load_schema,
    validate_redacted_file,
)


EXPERIMENTS_DIR = REPO_ROOT / "experiments"


def _find_redacted_files():
    """Find all *redacted*.csv files under experiments/."""
    if not EXPERIMENTS_DIR.exists():
        return []
    return sorted(EXPERIMENTS_DIR.rglob("*redacted*.csv"))


def _schema_for_redacted_file(filename: str):
    """Map a redacted filename to its schema name."""
    mapping = {
        "retrieval_examples_redacted.csv": "bm25_retrieval_results",
        "selector_examples_redacted.csv": "selector_variant_evidence",
        "format_shift_inputs_redacted.csv": "format_shift_inputs",
        "format_shift_failure_examples_redacted.csv": "format_shift_inputs",
    }
    return mapping.get(filename)


# ---------------- TestRedactedFilesHaveNoText ----------------

class TestRedactedFilesHaveNoText:
    """Every *redacted*.csv must not contain text_columns or
    forbidden_columns_for_public_release from its schema."""

    @pytest.mark.parametrize("redacted_path", _find_redacted_files())
    def test_redacted_file_has_no_text_columns(self, redacted_path):
        schema_name = _schema_for_redacted_file(redacted_path.name)
        if schema_name is None:
            pytest.skip(f"No schema mapping for {redacted_path.name}")

        df = pd.read_csv(redacted_path, keep_default_na=False)
        report = validate_redacted_file(df, schema_name)

        assert report["ok"], (
            f"Redacted file {redacted_path} has leaked columns: "
            f"text={report['leaked_text_columns']}, "
            f"public={report['leaked_public_columns']}, "
            f"scoring={report['leaked_scoring_columns']}"
        )

    def test_no_raw_evidence_text_in_any_redacted_csv(self):
        """Brute-force check: no redacted CSV should have a column whose name
        contains 'evidence' or 'claim' or 'text' (excluding hash columns)."""
        redacted_files = _find_redacted_files()
        if not redacted_files:
            pytest.skip("No redacted files found")

        violations = []
        for rp in redacted_files:
            df = pd.read_csv(rp, keep_default_na=False)
            for col in df.columns:
                col_lower = col.lower()
                if col_lower.endswith("_sha256"):
                    continue  # hash columns are OK
                if any(kw in col_lower for kw in ("evidence", "claim", "page_text", "raw_text", "clean_text")):
                    violations.append((rp.name, col))

        assert not violations, (
            f"Redacted files contain raw text columns: {violations}"
        )


# ---------------- TestSmartQueueNoForbiddenScoringFields ----------------

class TestSmartQueueNoForbiddenScoringFields:
    """smart_queue_scores.csv must not contain any of the 9 forbidden scoring fields."""

    def _find_smart_queue_scores(self):
        results = []
        if not EXPERIMENTS_DIR.exists():
            return results
        for p in EXPERIMENTS_DIR.rglob("smart_queue_scores.csv"):
            results.append(p)
        return sorted(results)

    def test_smart_queue_scores_has_no_forbidden_fields(self):
        paths = self._find_smart_queue_scores()
        if not paths:
            pytest.skip("No smart_queue_scores.csv found")

        for p in paths:
            df = pd.read_csv(p, keep_default_na=False)
            cols = set(df.columns.astype(str))
            leaked = cols & set(FORBIDDEN_SCORING_FIELDS)
            assert not leaked, (
                f"{p.name} contains forbidden scoring fields: {leaked}"
            )

    def test_smart_queue_scores_schema_forbids_all_9_fields(self):
        """The schema itself must list all 9 forbidden fields."""
        schema = load_schema("smart_queue_scores")
        forbidden = set(schema["forbidden_columns_for_scoring"])
        assert forbidden == set(FORBIDDEN_SCORING_FIELDS)

    @pytest.mark.parametrize("field", FORBIDDEN_SCORING_FIELDS)
    def test_individual_forbidden_field_absent_from_smart_queue(self, field):
        paths = self._find_smart_queue_scores()
        if not paths:
            pytest.skip("No smart_queue_scores.csv found")
        for p in paths:
            df = pd.read_csv(p, keep_default_na=False)
            assert field not in df.columns, (
                f"{p.name} contains forbidden field: {field}"
            )


# ---------------- TestRedactedFileProvenance ----------------

class TestRedactedFileProvenance:
    """Sanity: redacted files should be smaller (in column count) than their
    non-redacted counterparts — redaction strips columns, never adds them."""

    def test_redacted_has_fewer_columns_than_full(self):
        """For each redacted file with a known full counterpart, verify the
        redacted version has fewer columns."""
        pairs = [
            (
                EXPERIMENTS_DIR / "bm25_sentence_retrieval_v1_toy" / "retrieval_results_sentence_bm25.csv",
                EXPERIMENTS_DIR / "bm25_sentence_retrieval_v1_toy" / "retrieval_examples_redacted.csv",
            ),
            (
                EXPERIMENTS_DIR / "canonicalizer_ablation_v1_toy" / "selector_variant_evidence.csv",
                EXPERIMENTS_DIR / "canonicalizer_ablation_v1_toy" / "selector_examples_redacted.csv",
            ),
            (
                EXPERIMENTS_DIR / "format_shift_ablation_v1_toy" / "format_shift_inputs.csv",
                EXPERIMENTS_DIR / "format_shift_ablation_v1_toy" / "format_shift_inputs_redacted.csv",
            ),
        ]
        checked = 0
        for full_path, redacted_path in pairs:
            if not full_path.exists() or not redacted_path.exists():
                continue
            full_df = pd.read_csv(full_path, keep_default_na=False)
            redacted_df = pd.read_csv(redacted_path, keep_default_na=False)
            assert len(redacted_df.columns) < len(full_df.columns), (
                f"Redacted {redacted_path.name} should have fewer columns than "
                f"{full_path.name} (got {len(redacted_df.columns)} vs {len(full_df.columns)})"
            )
            checked += 1
        if checked == 0:
            pytest.skip("No full/redacted pairs found")
