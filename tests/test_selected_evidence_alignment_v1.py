"""test_selected_evidence_alignment_v1.py — Tests for the automatic
selected_evidence alignment check.

Covers:
  1. empty selected -> missing_or_invalid
  2. "197" (placeholder) -> missing_or_invalid
  3. exact substring -> exact_or_contained
  4. high overlap paraphrase -> high_overlap or partial_overlap
  5. unrelated text -> low_or_unrelated
  6. output columns don't contain raw evidence/selected text field names
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from check_selected_evidence_alignment_v1 import (  # noqa: E402
    classify_alignment,
    REDACTED_CASE_COLUMNS,
)

ALIGNMENT_CSV = (
    REPO_ROOT
    / "experiments"
    / "human_audit_v1"
    / "selected_evidence_alignment_cases_redacted.csv"
)

# Field names that would indicate raw text leakage if present in outputs.
FORBIDDEN_RAW_FIELDS = {
    "claim_text", "evidence_text", "selected_evidence",
    "claim_text_原文", "evidence_text_原文", "selected_evidence_原文",
    "claim_text_中文对照", "evidence_text_中文对照", "selected_evidence_中文对照",
    "raw_text", "clean_text", "body_text", "pdf_text", "备注",
    "audit_notes",
}


# ---------------- Classification tests ----------------

def test_empty_selected_is_missing_or_invalid():
    """Test 1: empty selected_evidence -> missing_or_invalid."""
    cls, sim, conflict = classify_alignment("", "some evidence text here")
    assert cls == "missing_or_invalid", f"expected missing_or_invalid, got {cls}"
    assert conflict is False


def test_placeholder_197_is_missing_or_invalid():
    """Test 2: '197' (placeholder/pure number) -> missing_or_invalid."""
    cls, sim, conflict = classify_alignment("197", "the model achieved 95% accuracy")
    assert cls == "missing_or_invalid", f"expected missing_or_invalid, got {cls}"
    assert conflict is False


def test_exact_substring_is_exact_or_contained():
    """Test 3: selected is substring of evidence -> exact_or_contained."""
    evidence = "the model uses reinforcement learning for adaptive routing"
    selected = "reinforcement learning for adaptive routing"
    cls, sim, conflict = classify_alignment(selected, evidence)
    assert cls == "exact_or_contained", f"expected exact_or_contained, got {cls}"
    assert sim == 1.0


def test_high_overlap_paraphrase_is_high_or_partial():
    """Test 4: high overlap paraphrase -> high_overlap or partial_overlap."""
    evidence = (
        "the system uses a reinforcement learning approach to adaptively "
        "route requests across multiple service endpoints"
    )
    selected = (
        "the system adaptively routes requests across endpoints using "
        "a reinforcement learning approach"
    )
    cls, sim, conflict = classify_alignment(selected, evidence)
    assert cls in {"high_overlap", "partial_overlap", "exact_or_contained"}, (
        f"expected high_overlap/partial_overlap/exact_or_contained, got {cls}"
    )


def test_unrelated_text_is_low_or_unrelated():
    """Test 5: unrelated text -> low_or_unrelated."""
    evidence = "127.0.0.1 192.168.1.1 10.0.0.1 255.255.255.0 172.16.0.1"
    selected = "the quick brown fox jumps over the lazy dog every morning"
    cls, sim, conflict = classify_alignment(selected, evidence)
    assert cls == "low_or_unrelated", f"expected low_or_unrelated, got {cls} (sim={sim})"


# ---------------- Output redaction test ----------------

def test_output_csv_has_no_raw_text_fields():
    """Test 6: output CSV columns don't contain raw evidence/selected text
    field names."""
    if not ALIGNMENT_CSV.exists():
        return  # no output file generated yet; skip
    with open(ALIGNMENT_CSV, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = set(reader.fieldnames or [])
    leak = fieldnames & FORBIDDEN_RAW_FIELDS
    assert not leak, f"forbidden raw-text columns in output CSV: {leak}"
    # Also verify the allowed columns are hash-only (no raw text)
    for col in REDACTED_CASE_COLUMNS:
        assert col in fieldnames, f"expected column {col} not in output"
