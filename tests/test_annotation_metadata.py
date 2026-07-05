"""Tests for Task B: nested annotation.* metadata consistency.

Verifies that audit/import/agreement scripts read the nested
``annotation`` field (with legacy top-level fallback) so paper-ready
audit counts, dedupe, and agreement fallback all work after the schema
migration.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Make scripts/ importable.
SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import audit_dataset as audit_mod
import import_annotations as import_mod
import compute_annotation_agreement as agree_mod


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _nested_record(
    sample_id: str = "s1",
    annotators: list[str] | None = None,
    is_human_audited: bool = True,
    agreement_score: float | None = 0.85,
    annotation_round: int = 1,
    escalation_label: int = 1,
) -> dict:
    """Build a minimal record carrying nested annotation.* metadata."""
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "toy",
        "source_type": "oracle",
        "split": "train",
        "claim_text": "c",
        "evidence_text": "e",
        "claim_family": "causal",
        "evidence_vector": {d: 0.0 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
        "evidence_confidence": {d: 1.0 for d in [
            "alignment", "transparency", "coverage", "traceability",
            "boundary", "uncertainty", "causal_id", "risk_utility",
        ]},
        "claim_tiers": {d: 0 for d in ["scope", "causal", "action", "certainty"]},
        "support_tiers": {d: 0 for d in ["scope", "causal", "action", "certainty"]},
        "contradiction_label": 0,
        "escalation_label": escalation_label,
        "escalation_type": [],
        "evidence_gap_labels": [],
        "annotation": {
            "annotators": annotators or ["A1"],
            "annotation_round": annotation_round,
            "agreement_score": agreement_score,
            "is_human_audited": is_human_audited,
            "evidence_spans": [],
            "extraction_method": "human",
        },
    }


def _legacy_record(
    sample_id: str = "s1",
    annotator_id: str = "A1",
    audited: bool = True,
    agreement_score: float = 0.85,
    annotation_round: int = 1,
) -> dict:
    """Build a minimal legacy record with top-level annotation fields."""
    rec = _nested_record(
        sample_id=sample_id,
        annotators=[annotator_id],
        is_human_audited=audited,
        agreement_score=agreement_score,
        annotation_round=annotation_round,
    )
    # Replace nested annotation with legacy top-level fields.
    del rec["annotation"]
    rec["annotator_id"] = annotator_id
    rec["audited"] = audited
    rec["agreement_score"] = agreement_score
    rec["annotation_round"] = annotation_round
    return rec


# ---------------------------------------------------------------------------
# audit_dataset._annotation helpers
# ---------------------------------------------------------------------------

def test_annotation_helper_reads_nested_field():
    rec = _nested_record(annotators=["A1", "A2"], is_human_audited=True)
    assert audit_mod._is_human_audited(rec) is True
    assert audit_mod._annotators(rec) == ["A1", "A2"]
    assert audit_mod._agreement_score(rec) == 0.85


def test_annotation_helper_reads_legacy_top_level():
    rec = _legacy_record(annotator_id="A1", audited=True, agreement_score=0.9)
    assert audit_mod._is_human_audited(rec) is True
    assert audit_mod._annotators(rec) == ["A1"]
    assert audit_mod._agreement_score(rec) == 0.9


def test_annotation_helper_handles_legacy_annotators_list():
    """Legacy top-level ``annotators`` list should also be read."""
    rec = _nested_record()
    del rec["annotation"]
    rec["annotators"] = ["A1", "A2"]
    rec["audited"] = True
    assert audit_mod._annotators(rec) == ["A1", "A2"]


# ---------------------------------------------------------------------------
# paper-ready audit counts nested annotation
# ---------------------------------------------------------------------------

def test_paper_ready_audit_counts_nested_audited():
    """Paper-ready audit should count records with
    annotation.is_human_audited=True toward n_audited_logical_samples."""
    records = [
        _nested_record(sample_id=f"s{i}", is_human_audited=True)
        for i in range(5)
    ]
    # Use small min_* thresholds so the audit doesn't block on those.
    result = audit_mod._paper_ready_audit(
        records,
        min_total_pairs=1,
        min_audited_pairs=1,
        min_per_claim_family=1,
        min_per_domain=1,
        require_complete_source_triples=False,
        require_multi_annotator=False,
        require_adversarial_metadata=False,
    )
    # audited_logical should be 5 (one per sample_id).
    assert result["counts"]["n_audited_logical_samples"] == 5


def test_paper_ready_audit_counts_legacy_audited():
    """Legacy top-level ``audited=True`` should also be counted."""
    records = [
        _legacy_record(sample_id=f"s{i}", audited=True)
        for i in range(3)
    ]
    result = audit_mod._paper_ready_audit(
        records,
        min_total_pairs=1,
        min_audited_pairs=1,
        min_per_claim_family=1,
        min_per_domain=1,
        require_complete_source_triples=False,
        require_multi_annotator=False,
        require_adversarial_metadata=False,
    )
    assert result["counts"]["n_audited_logical_samples"] == 3


def test_paper_ready_audit_multi_annotator_reads_nested_annotators():
    """require_multi_annotator should read annotation.annotators."""
    # Two logical samples, each with >= 2 annotators.
    records = [
        _nested_record(sample_id="s1", annotators=["A1", "A2"]),
        _nested_record(sample_id="s2", annotators=["A1", "A3"]),
    ]
    result = audit_mod._paper_ready_audit(
        records,
        min_total_pairs=1,
        min_audited_pairs=1,
        min_per_claim_family=1,
        min_per_domain=1,
        require_complete_source_triples=False,
        require_multi_annotator=True,
        require_adversarial_metadata=False,
    )
    assert result["release_checklist"].get("multi_annotator") is True


# ---------------------------------------------------------------------------
# agreement fallback: agreement_score
# ---------------------------------------------------------------------------

def test_agreement_score_fallback_when_no_staged_report():
    """When no staged agreement report is provided, audit falls back to
    per-record annotation.agreement_score."""
    records = [
        _nested_record(sample_id=f"s{i}", agreement_score=0.9)
        for i in range(5)
    ]
    result = audit_mod._paper_ready_audit(
        records,
        min_total_pairs=1,
        min_audited_pairs=1,
        min_per_claim_family=1,
        min_per_domain=1,
        require_complete_source_triples=False,
        require_multi_annotator=False,
        require_adversarial_metadata=False,
        agreement_report=None,
    )
    # avg_agreement should be 0.9 (>= 0.7 threshold).
    assert result["agreement"].get("avg_agreement") == 0.9
    assert result["release_checklist"].get("agreement_threshold") is True


# ---------------------------------------------------------------------------
# import_annotations._dedupe_key
# ---------------------------------------------------------------------------

def test_dedupe_key_uses_nested_annotators():
    """_dedupe_key should use annotation.annotators[0] + annotation_round,
    so different annotators on the same sample are NOT collapsed."""
    r1 = _nested_record(sample_id="s1", annotators=["A1"], annotation_round=1)
    r2 = _nested_record(sample_id="s1", annotators=["A2"], annotation_round=1)
    k1 = import_mod._dedupe_key(r1)
    k2 = import_mod._dedupe_key(r2)
    assert k1 != k2, "different annotators on same sample must not dedupe"


def test_dedupe_key_legacy_annotator_id():
    """Legacy top-level annotator_id should still work as a fallback."""
    r = _legacy_record(sample_id="s1", annotator_id="A1", annotation_round=2)
    k = import_mod._dedupe_key(r)
    assert k == "s1|A1|2"


def test_dedupe_key_same_annotator_same_round_dedupes():
    r1 = _nested_record(sample_id="s1", annotators=["A1"], annotation_round=1)
    r2 = _nested_record(sample_id="s1", annotators=["A1"], annotation_round=1)
    assert import_mod._dedupe_key(r1) == import_mod._dedupe_key(r2)


# ---------------------------------------------------------------------------
# compute_annotation_agreement
# ---------------------------------------------------------------------------

def test_agreement_multi_row_mode():
    """Multi-row multi-annotator mode computes kappa normally."""
    records = [
        _nested_record(sample_id="s1", annotators=["A1"], escalation_label=1),
        _nested_record(sample_id="s1", annotators=["A2"], escalation_label=1),
        _nested_record(sample_id="s2", annotators=["A1"], escalation_label=0),
        _nested_record(sample_id="s2", annotators=["A2"], escalation_label=0),
    ]
    report = agree_mod.compute_agreement(records)
    assert report["n_samples_multi_annotated"] == 2
    assert report["cohens_kappa_escalation"] == 1.0  # perfect agreement


def test_agreement_single_row_mode_counts_but_no_kappa():
    """Single-row multi-annotator records count toward multi_annotator
    but kappa is None (we cannot compute per-annotator labels)."""
    records = [
        _nested_record(sample_id="s1", annotators=["A1", "A2"]),
        _nested_record(sample_id="s2", annotators=["A1", "A2"]),
    ]
    report = agree_mod.compute_agreement(records)
    assert report["n_samples_multi_annotated"] == 2
    assert report["cohens_kappa_escalation"] is None
    assert "message" in report


def test_staged_agreement_uses_contradiction_label():
    """Stage 3 should read contradiction_label, not the legacy
    top-level ``contradiction`` key."""
    records = [
        _nested_record(sample_id="s1", annotators=["A1"]),
        _nested_record(sample_id="s1", annotators=["A2"]),
    ]
    # Set contradiction_label to 1 on both rows.
    for r in records:
        r["contradiction_label"] = 1
    # Also set the legacy ``contradiction`` key to 0 to make sure it's
    # NOT read.
    for r in records:
        r["contradiction"] = 0
    staged = agree_mod.compute_staged_agreement(records)
    s3 = staged["stage_3_escalation_contradiction"]
    # Both annotators have contradiction_label=1 -> perfect kappa = 1.0.
    assert s3["contradiction_kappa"] == 1.0
