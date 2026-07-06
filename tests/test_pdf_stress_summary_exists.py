"""Tests that the PDF stress test summary report exists and contains
required sections.

Validates the acceptance criterion: "summary 明确这是 extraction robustness
test，不是 SOTA".
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
STRESS_DIR = REPO_ROOT / "experiments" / "pdf_extraction_stress_test_v1"
SUMMARY_PATH = STRESS_DIR / "stress_test_summary.md"


class TestStressSummaryExists:
    def test_summary_file_exists(self):
        assert SUMMARY_PATH.is_file(), (
            f"Stress test summary not found at {SUMMARY_PATH}"
        )

    def test_summary_states_not_sota(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        # Must explicitly disclaim SOTA
        assert "NOT a SOTA claim" in content or "not a SOTA" in content.lower(), (
            "Summary must explicitly state this is NOT a SOTA claim"
        )

    def test_summary_mentions_extraction_robustness(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        assert "robustness" in content.lower(), (
            "Summary must mention 'robustness' (extraction robustness test)"
        )

    def test_summary_mentions_no_ocr_by_default(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        assert "OCR" in content, (
            "Summary must mention OCR policy (no OCR by default)"
        )

    def test_summary_mentions_synthetic_inputs(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        assert "synthetic" in content.lower(), (
            "Summary must mention that inputs are synthetic"
        )

    def test_summary_mentions_confidentiality(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        # Either 'Confidentiality' or 'Leakage' section should exist
        assert "Confidentiality" in content or "Leakage" in content, (
            "Summary must mention confidentiality or leakage guard"
        )

    def test_summary_has_by_stress_type_table(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        # Should have a "By Stress Type" table
        assert "By Stress Type" in content or "by_stress_type" in content, (
            "Summary must include per-stress-type metrics table"
        )

    def test_summary_mentions_overclaim_guidance(self):
        if not SUMMARY_PATH.is_file():
            pytest.skip("Summary not found")
        content = SUMMARY_PATH.read_text(encoding="utf-8")
        # Should have a "How Not to Overclaim" section
        assert "Overclaim" in content or "overclaim" in content.lower(), (
            "Summary must include guidance on how not to overclaim"
        )
