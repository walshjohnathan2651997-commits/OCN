"""Tests for the data schema."""

from __future__ import annotations

import pytest

from cese.constants import (
    CLAIM_DIMS,
    EVIDENCE_DIMS,
    NUM_TIERS,
    TIER_EXCEEDANCE_GAP_LABELS,
)
from cese.data.schema import ClaimEvidenceSample, EvidenceVector, TierLabels
from cese.data.toy_data import generate_toy_records
from cese.data.validation import validate_records


def _valid_record():
    return {
        "sample_id": "test-001",
        "domain": "controlled_simulation",
        "source_type": "oracle",
        "claim_text": "The simulation reports throughput of 100.",
        "evidence_text": "Simulation log: throughput=100 (n=100, seed=42).",
        "evidence_vector": {d: 0.5 for d in EVIDENCE_DIMS},
        "evidence_confidence": {d: 1.0 for d in EVIDENCE_DIMS},
        "claim_tiers": {d: 2 for d in CLAIM_DIMS},
        "support_tiers": {d: 2 for d in CLAIM_DIMS},
        "contradiction_label": 0,
        "escalation_label": 0,
        "escalation_type": [],
        "evidence_gap_labels": [],
        "rewrite_target": None,
        "split": "train",
        "template_id": "tpl-test",
        "claim_family": "descriptive",
    }


def test_valid_record():
    rec = _valid_record()
    sample = ClaimEvidenceSample(**rec)
    assert sample.sample_id == "test-001"


def test_tier_exceedance_gap_labels_are_preserved_and_validated():
    rec = _valid_record()
    rec["tier_exceedance_gap_labels"] = ["scope_missing"]
    assert "scope_missing" in TIER_EXCEEDANCE_GAP_LABELS
    sample = ClaimEvidenceSample(**rec)
    assert sample.model_dump()["tier_exceedance_gap_labels"] == ["scope_missing"]

    rec["tier_exceedance_gap_labels"] = ["coverage_missing"]
    with pytest.raises(Exception, match="tier_exceedance_gap_label"):
        ClaimEvidenceSample(**rec)


def test_invalid_tier():
    rec = _valid_record()
    rec["claim_tiers"]["scope"] = NUM_TIERS  # out of range
    with pytest.raises(Exception):
        ClaimEvidenceSample(**rec)


def test_invalid_domain():
    rec = _valid_record()
    rec["domain"] = "invalid_domain"
    with pytest.raises(Exception):
        ClaimEvidenceSample(**rec)


def test_evidence_vector_range():
    with pytest.raises(Exception):
        EvidenceVector(alignment=1.5)


def test_tier_labels():
    tl = TierLabels(scope=0, causal=4, action=2, certainty=3)
    assert tl.as_vector() == [0, 4, 2, 3]


def test_toy_records_valid():
    records = generate_toy_records(n=20, seed=0)
    report = validate_records(records)
    assert report["n_invalid"] == 0, report["errors"][:3]
    assert report["n_valid"] == 20


def test_toy_records_splits():
    records = generate_toy_records(n=200, seed=1)
    splits = {r["split"] for r in records}
    assert splits == {"train", "dev", "test"}
