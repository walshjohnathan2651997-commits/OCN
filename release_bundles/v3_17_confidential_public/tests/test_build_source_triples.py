"""Tests for scripts/build_source_triples.py.

P1d: verify that the source triple builder correctly groups, validates,
synthesizes, and rejects incomplete triples.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util

spec = importlib.util.spec_from_file_location(
    "build_source_triples", ROOT / "scripts" / "build_source_triples.py"
)
bst = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bst)


def _make_oracle_record(sid: str) -> dict:
    return {
        "sample_id": sid,
        "logical_sample_id": sid,
        "source_type": "oracle",
        "evidence_vector": {d: 0.8 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
        "evidence_confidence": {d: 1.0 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
    }


def test_group_by_logical():
    records = [
        _make_oracle_record("s1"),
        {**_make_oracle_record("s1"), "source_type": "extracted",
         "sample_id": "s1-extracted"},
    ]
    grouped = bst.group_by_logical(records)
    assert "s1" in grouped
    assert set(grouped["s1"].keys()) == {"oracle", "extracted"}


def test_validate_triples_complete():
    records = []
    for sid in ["s1", "s2"]:
        records.append(_make_oracle_record(sid))
        records.append({**_make_oracle_record(sid), "source_type": "extracted",
                        "sample_id": f"{sid}-extracted"})
        records.append({**_make_oracle_record(sid), "source_type": "confidence_aware",
                        "sample_id": f"{sid}-ca"})
    grouped = bst.group_by_logical(records)
    report = bst.validate_triples(grouped)
    assert report["n_complete_triples"] == 2
    assert report["n_incomplete_triples"] == 0
    assert report["same_sample_set"] is True


def test_validate_triples_incomplete():
    records = [
        _make_oracle_record("s1"),
        {**_make_oracle_record("s1"), "source_type": "extracted",
         "sample_id": "s1-extracted"},
        # Missing confidence_aware for s1.
        _make_oracle_record("s2"),
    ]
    grouped = bst.group_by_logical(records)
    report = bst.validate_triples(grouped)
    assert report["n_complete_triples"] == 0
    assert report["n_incomplete_triples"] == 2
    assert "confidence_aware" in report["missing_source_types"]["s1"]
    assert "extracted" in report["missing_source_types"]["s2"]
    assert "confidence_aware" in report["missing_source_types"]["s2"]
    assert report["same_sample_set"] is False


def test_synthesize_missing_from_oracle():
    records = [_make_oracle_record("s1")]
    grouped = bst.group_by_logical(records)
    import random
    rng = random.Random(42)
    synthesized = bst.synthesize_missing(grouped, rng)
    # Should synthesize extracted and confidence_aware.
    assert len(synthesized) == 2
    types = {r["source_type"] for r in synthesized}
    assert types == {"extracted", "confidence_aware"}


def test_reject_incomplete_filters():
    """When --reject-incomplete, only complete triples are kept."""
    records = [
        _make_oracle_record("s1"),
        {**_make_oracle_record("s1"), "source_type": "extracted",
         "sample_id": "s1-extracted"},
        {**_make_oracle_record("s1"), "source_type": "confidence_aware",
         "sample_id": "s1-ca"},
        _make_oracle_record("s2"),  # incomplete: only oracle
    ]
    output, report = bst.build_triples(
        records, reject_incomplete=True, synthesize=False
    )
    # Only s1's 3 records should remain.
    assert report["rejected_incomplete"] is True
    assert report["n_output_records"] == 3
    lsids = {r.get("logical_sample_id") for r in output}
    assert lsids == {"s1"}


def test_synthesize_then_complete():
    """When --synthesize, missing types are created and triples complete."""
    records = [_make_oracle_record("s1")]
    output, report = bst.build_triples(
        records, reject_incomplete=False, synthesize=True
    )
    assert report["n_synthesized"] == 2
    assert report["n_complete_triples"] == 1
    assert report["n_incomplete_triples"] == 0
    types = {r["source_type"] for r in output}
    assert types == {"oracle", "extracted", "confidence_aware"}


def test_reject_incomplete_with_synthesize():
    """Synthesize first, then reject any still-incomplete."""
    records = [
        _make_oracle_record("s1"),  # will be completed by synthesis
        {"sample_id": "s2", "logical_sample_id": "s2",
         "source_type": "extracted"},  # no oracle, cannot synthesize
    ]
    output, report = bst.build_triples(
        records, reject_incomplete=True, synthesize=True
    )
    # s1 should be complete (3 records), s2 should be rejected.
    assert report["n_complete_triples"] == 1
    lsids = {r.get("logical_sample_id") for r in output}
    assert "s1" in lsids
    assert "s2" not in lsids
