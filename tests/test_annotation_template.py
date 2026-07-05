"""Tests for P1-4: pilot annotation template files.

Verifies:
- data/templates/pilot_annotation_template.jsonl exists with the canonical
  blank-form fields (null escalation_label / tiers).
- data/templates/pilot_annotation_template.csv exists and imports cleanly
  via import_annotations.py, producing a record that passes validate_data.
- schemas/pilot_annotation_minimal_schema.md documents the 0-4 tier scale,
  the 8 evidence vector dims, and states that extended dims are NOT used
  at pilot stage.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

TEMPLATE_JSONL = ROOT / "data" / "templates" / "pilot_annotation_template.jsonl"
TEMPLATE_CSV = ROOT / "data" / "templates" / "pilot_annotation_template.csv"
SCHEMA_MD = ROOT / "schemas" / "pilot_annotation_minimal_schema.md"


# ---------------------------------------------------------------------------
# JSONL template
# ---------------------------------------------------------------------------

def test_jsonl_template_exists_and_has_required_fields():
    """The JSONL template must exist and contain all pilot-stage minimum
    fields per the P1-4 spec."""
    assert TEMPLATE_JSONL.exists(), f"missing {TEMPLATE_JSONL}"
    rec = json.loads(TEMPLATE_JSONL.read_text(encoding="utf-8").strip())
    # Top-level required fields.
    for k in [
        "sample_id", "logical_sample_id", "domain", "source_type",
        "claim_text", "evidence_text", "evidence_vector", "evidence_confidence",
        "claim_tiers", "support_tiers", "contradiction_label",
        "escalation_label", "escalation_type", "evidence_gap_labels",
        "rewrite_target", "split", "template_id", "claim_family", "annotation",
    ]:
        assert k in rec, f"template missing field {k}"
    # evidence_vector must have all 8 core dims.
    ev = rec["evidence_vector"]
    for d in ["alignment", "transparency", "coverage", "traceability",
              "boundary", "uncertainty", "causal_id", "risk_utility"]:
        assert d in ev, f"evidence_vector missing dim {d}"
    # evidence_confidence must have all 8 core dims with 1.0 default.
    ec = rec["evidence_confidence"]
    for d in ["alignment", "transparency", "coverage", "traceability",
              "boundary", "uncertainty", "causal_id", "risk_utility"]:
        assert d in ec and ec[d] == 1.0, f"evidence_confidence.{d} must default to 1.0"
    # claim_tiers / support_tiers must have the 4 claim dims.
    for k in ["claim_tiers", "support_tiers"]:
        for d in ["scope", "causal", "action", "certainty"]:
            assert d in rec[k], f"{k} missing dim {d}"
    # escalation_label defaults to null (auto-filled by fill_escalation_labels.py).
    assert rec["escalation_label"] is None, "escalation_label should be null in template"
    # Nested annotation block with required sub-fields.
    ann = rec["annotation"]
    for k in ["annotators", "annotation_round", "agreement_score",
              "is_human_audited", "evidence_spans", "extraction_method"]:
        assert k in ann, f"annotation missing sub-field {k}"
    assert ann["annotators"] == ["ann-01"]
    assert ann["is_human_audited"] is True
    assert ann["extraction_method"] == "human_oracle"
    # source_type must be oracle for pilot human annotation.
    assert rec["source_type"] == "oracle"
    # contradiction_label uses the canonical name (not legacy `contradiction`).
    assert "contradiction_label" in rec
    assert "contradiction" not in rec  # legacy field must NOT be present


def test_jsonl_template_does_not_use_extended_evidence_dims():
    """The pilot template must NOT include extended evidence dimensions
    (distribution_shift, scenario_diversity, etc.)."""
    rec = json.loads(TEMPLATE_JSONL.read_text(encoding="utf-8").strip())
    extended = [
        "distribution_shift", "scenario_diversity", "temporal_order",
        "contrast_counterfactual", "baseline_comparison",
        "deployment_constraints", "variance_seeds", "sensitivity_analysis",
    ]
    for d in extended:
        assert d not in rec["evidence_vector"], \
            f"pilot template must not include extended dim {d}"


# ---------------------------------------------------------------------------
# CSV template imports cleanly
# ---------------------------------------------------------------------------

def test_csv_template_imports_and_validates(tmp_path):
    """The CSV template must import via import_annotations.py and the
    resulting JSONL record must pass validate_data."""
    import import_annotations as ia
    out_path = tmp_path / "out.jsonl"
    ia.main([
        "--input", str(TEMPLATE_CSV),
        "--output", str(out_path),
    ])
    lines = [l for l in out_path.read_text(encoding="utf-8").splitlines() if l]
    assert len(lines) >= 1, "CSV template produced no records on import"
    rec = json.loads(lines[0])
    # Nested annotation block must be present (legacy annotator_id converted).
    assert "annotation" in rec
    assert rec["annotation"]["annotators"] == ["ann-01"]
    assert "annotator_id" not in rec  # legacy field converted
    # Validate against the schema.
    from cese.data.schema import ClaimEvidenceSample
    sample = ClaimEvidenceSample(**rec)
    assert sample.sample_id == "pilot-001"
    assert sample.source_type == "oracle"


# ---------------------------------------------------------------------------
# Schema markdown documents required content
# ---------------------------------------------------------------------------

def test_schema_md_documents_tier_scale_and_evidence_dims():
    """pilot_annotation_minimal_schema.md must document:
    - the 0-4 tier scale,
    - the 8 evidence vector dimensions,
    - that extended dims are NOT used at pilot stage.
    """
    assert SCHEMA_MD.exists(), f"missing {SCHEMA_MD}"
    text = SCHEMA_MD.read_text(encoding="utf-8")
    # 0-4 tier scale.
    for tier_label in ["0", "1", "2", "3", "4"]:
        assert tier_label in text, f"tier {tier_label} not documented"
    # 8 evidence vector dims.
    for d in ["alignment", "transparency", "coverage", "traceability",
              "boundary", "uncertainty", "causal_id", "risk_utility"]:
        assert d in text, f"evidence dim {d} not documented"
    # Extended dims NOT used at pilot.
    assert "extended" in text.lower() or "NOT" in text
    assert "pilot" in text.lower()
    # contradiction_label canonical (not legacy contradiction).
    assert "contradiction_label" in text
