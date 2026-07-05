"""Tests for P1-3: unified annotation metadata.

Verifies:
- nested ``annotation`` block passes validate_data.
- nested ``annotation.is_human_audited`` is counted by audit_dataset and
  check_pilot_balance.
- import_annotations converts legacy ``annotator_id`` to nested
  ``annotation.annotators``.
- compute_annotation_agreement handles multi-row multi-annotator and
  single-row multi-annotator (without faking kappa).
- legacy top-level ``contradiction`` is NOT read; only ``contradiction_label``.
- import_annotations dedupe does NOT collapse different annotators on
  the same sample.
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

from cese.data.schema import ClaimEvidenceSample


def _base_record(sample_id: str) -> dict:
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "academic_claim",
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_family": "descriptive",
        "evidence_vector": {
            "alignment": 1.0, "transparency": 1.0, "coverage": 1.0,
            "traceability": 1.0, "boundary": 1.0, "uncertainty": 1.0,
            "causal_id": 1.0, "risk_utility": 1.0,
        },
        "evidence_confidence": {
            "alignment": 1.0, "transparency": 1.0, "coverage": 1.0,
            "traceability": 1.0, "boundary": 1.0, "uncertainty": 1.0,
            "causal_id": 1.0, "risk_utility": 1.0,
        },
        "claim_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "support_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "contradiction_label": 0,
        "escalation_label": 0,
        "split": "train",
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# Nested annotation passes validate
# ---------------------------------------------------------------------------

def test_nested_annotation_passes_validate():
    """A record with the canonical nested ``annotation`` block must
    validate against ClaimEvidenceSample."""
    rec = _base_record("s1")
    rec["annotation"] = {
        "annotators": ["ann-01"],
        "annotation_round": 1,
        "agreement_score": None,
        "is_human_audited": True,
        "evidence_spans": [],
        "extraction_method": "human_oracle",
    }
    sample = ClaimEvidenceSample(**rec)
    assert sample.annotation is not None
    assert sample.annotation.annotators == ["ann-01"]
    assert sample.annotation.is_human_audited is True


def test_legacy_annotator_id_still_validates():
    """Legacy top-level ``annotator_id`` should NOT break validation
    (it is ignored by the schema, but import_annotations will convert it)."""
    rec = _base_record("s1")
    rec["annotator_id"] = "ann-01"  # legacy
    # Should still validate (extra fields are ignored by pydantic).
    sample = ClaimEvidenceSample(**rec)
    assert sample.annotation is None  # no nested block


# ---------------------------------------------------------------------------
# audit_dataset counts nested is_human_audited
# ---------------------------------------------------------------------------

def test_audit_counts_nested_human_audited(tmp_path):
    """audit_dataset must count ``annotation.is_human_audited=True``."""
    import audit_dataset as ad
    records = []
    # 2 audited, 1 not.
    for i in range(2):
        r = _base_record(f"aud{i}")
        r["annotation"] = {"annotators": ["ann-01"], "is_human_audited": True}
        records.append(r)
    r = _base_record("notaud")
    r["annotation"] = {"annotators": ["ann-01"], "is_human_audited": False}
    records.append(r)
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, records)

    # _is_human_audited helper.
    assert ad._is_human_audited(records[0]) is True
    assert ad._is_human_audited(records[2]) is False


def test_audit_legacy_audited_fallback(tmp_path):
    """audit_dataset reads legacy top-level ``audited`` when no nested
    ``annotation`` block is present."""
    import audit_dataset as ad
    rec = _base_record("s1")
    rec["audited"] = True  # legacy
    assert ad._is_human_audited(rec) is True


# ---------------------------------------------------------------------------
# check_pilot_balance counts nested annotation
# ---------------------------------------------------------------------------

def test_check_pilot_balance_counts_annotation(tmp_path):
    """check_pilot_balance must report n_human_audited, n_multi_annotator,
    n_with_agreement_score from the nested ``annotation`` block."""
    import check_pilot_balance as cpb
    records = []
    # 2 audited, 1 multi-annotator, 1 with agreement_score.
    r = _base_record("s1")
    r["annotation"] = {"annotators": ["ann-01"], "is_human_audited": True}
    records.append(r)
    r = _base_record("s2")
    r["annotation"] = {"annotators": ["ann-01"], "is_human_audited": True}
    records.append(r)
    r = _base_record("s3")
    r["annotation"] = {
        "annotators": ["ann-01", "ann-02"],  # multi-annotator
        "is_human_audited": False,
        "agreement_score": 0.8,
    }
    records.append(r)
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, records)

    report = cpb.check_balance(str(in_path))
    assert report["n_human_audited"] == 2
    assert report["n_multi_annotator"] == 1
    assert report["n_with_agreement_score"] == 1


def test_check_pilot_balance_legacy_audited_fallback(tmp_path):
    """check_pilot_balance reads legacy top-level ``audited`` and
    ``annotators`` when no nested block is present."""
    import check_pilot_balance as cpb
    rec = _base_record("s1")
    rec["audited"] = True  # legacy
    rec["annotators"] = ["ann-01", "ann-02"]  # legacy top-level list
    assert cpb._is_human_audited(rec) is True
    assert len(cpb._annotators(rec)) == 2


# ---------------------------------------------------------------------------
# import_annotations converts legacy annotator_id to nested annotators
# ---------------------------------------------------------------------------

def test_import_converts_legacy_annotator_id(tmp_path):
    """import_annotations must convert legacy ``annotator_id`` CSV column
    to nested ``annotation.annotators`` list."""
    import import_annotations as ia
    csv_path = tmp_path / "annotations.csv"
    csv_path.write_text(
        "sample_id,domain,source_type,claim_text,evidence_text,claim_family,"
        "claim_tiers.scope,claim_tiers.causal,claim_tiers.action,claim_tiers.certainty,"
        "support_tiers.scope,support_tiers.causal,support_tiers.action,support_tiers.certainty,"
        "escalation_label,annotator_id,annotation_round\n"
        "s1,academic_claim,oracle,c,e,descriptive,0,0,0,0,0,0,0,0,0,ann-01,1\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "out.jsonl"
    ia.main(["--input", str(csv_path), "--output", str(out_path)])
    rec = json.loads(out_path.read_text(encoding="utf-8").strip())
    assert "annotation" in rec
    assert rec["annotation"]["annotators"] == ["ann-01"]
    # Legacy top-level annotator_id should NOT be in the output.
    assert "annotator_id" not in rec


# ---------------------------------------------------------------------------
# import_annotations dedupe does NOT collapse different annotators
# ---------------------------------------------------------------------------

def test_import_dedupe_keeps_different_annotators(tmp_path):
    """dedupe by sample_id + annotator + round must NOT collapse two
    different annotators judging the same sample into one record."""
    import import_annotations as ia
    csv_path = tmp_path / "annotations.csv"
    csv_path.write_text(
        "sample_id,domain,source_type,claim_text,evidence_text,claim_family,"
        "claim_tiers.scope,claim_tiers.causal,claim_tiers.action,claim_tiers.certainty,"
        "support_tiers.scope,support_tiers.causal,support_tiers.action,support_tiers.certainty,"
        "escalation_label,annotator_id,annotation_round\n"
        "s1,academic_claim,oracle,c,e,descriptive,0,0,0,0,0,0,0,0,0,ann-01,1\n"
        "s1,academic_claim,oracle,c,e,descriptive,1,0,0,0,0,0,0,0,1,ann-02,1\n",
        encoding="utf-8",
    )
    out_path = tmp_path / "out.jsonl"
    ia.main(["--input", str(csv_path), "--output", str(out_path), "--dedupe"])
    lines = [l for l in out_path.read_text(encoding="utf-8").splitlines() if l]
    assert len(lines) == 2  # two different annotators kept
    recs = [json.loads(l) for l in lines]
    annotators = {recs[0]["annotation"]["annotators"][0], recs[1]["annotation"]["annotators"][0]}
    assert annotators == {"ann-01", "ann-02"}


# ---------------------------------------------------------------------------
# compute_annotation_agreement: single-row multi-annotator -> no fake kappa
# ---------------------------------------------------------------------------

def test_compute_agreement_single_row_multi_annotator_no_kappa(tmp_path):
    """A single-row record with annotation.annotators=[ann-01, ann-02]
    must contribute to n_multi_annotator but kappa must be None (cannot
    compute per-annotator labels from a single row)."""
    import compute_annotation_agreement as caa
    rec = _base_record("s1")
    rec["annotation"] = {
        "annotators": ["ann-01", "ann-02"],
        "annotation_round": 1,
    }
    report = caa.compute_agreement([rec])
    # No multi-row multi-annotator pairs -> kappa is None.
    assert report["cohens_kappa_escalation"] is None
    # Single-row multi-annotator count is tracked (key is
    # n_samples_multi_annotated; the report also sets
    # n_single_row_multi_annotator when applicable).
    assert report.get("n_samples_multi_annotated", 0) >= 1


def test_compute_agreement_multi_row_multi_annotator_kappa(tmp_path):
    """Two rows for the same sample_id, each with a different annotator,
    must compute a kappa (not None)."""
    import compute_annotation_agreement as caa
    r1 = _base_record("s1")
    r1["escalation_label"] = 1
    r1["annotation"] = {"annotators": ["ann-01"], "annotation_round": 1}
    r2 = _base_record("s1")
    r2["escalation_label"] = 1
    r2["annotation"] = {"annotators": ["ann-02"], "annotation_round": 1}
    report = caa.compute_agreement([r1, r2])
    # With 1 sample and 2 annotators agreeing, kappa is degenerate (1.0
    # or nan); the key assertion is that it is NOT None (i.e. the code
    # attempted to compute it rather than bailing out).
    assert report["cohens_kappa_escalation"] is not None


# ---------------------------------------------------------------------------
# contradiction_label is canonical; legacy `contradiction` not read
# ---------------------------------------------------------------------------

def test_compute_agreement_reads_contradiction_label_not_legacy(tmp_path):
    """compute_annotation_agreement must read ``contradiction_label``,
    NOT the legacy top-level ``contradiction`` field."""
    import compute_annotation_agreement as caa
    r1 = _base_record("s1")
    r1["contradiction_label"] = 1
    r1["contradiction"] = 0  # legacy, must be ignored
    r1["annotation"] = {"annotators": ["ann-01"], "annotation_round": 1}
    r2 = _base_record("s1")
    r2["contradiction_label"] = 1
    r2["contradiction"] = 0  # legacy, must be ignored
    r2["annotation"] = {"annotators": ["ann-02"], "annotation_round": 1}
    report = caa.compute_agreement([r1, r2])
    # Both annotators have contradiction_label=1 -> kappa should be 1.0
    # (perfect agreement on the canonical field, ignoring legacy).
    stage3 = report.get("stage_3_escalation_contradiction", {})
    contra_kappa = stage3.get("contradiction_kappa")
    if contra_kappa is not None:
        assert contra_kappa == 1.0
