"""Tests for cese.data.annotation_io (cleaned v2 annotation CSV reader).

Verifies:
  * The real v2 CSV reads successfully.
  * JSON-array fields are parsed into Python lists.
  * Split counts are train=48, validation=16, test=16.
  * claim_tiers.action allows tier 0.
  * sample_weight exists and lies in [0, 1].
  * escalation_label matches the claim>support overflow rule.
  * get_split_dataframes returns the three splits with correct sizes.
  * row_to_record produces a schema-valid ClaimEvidenceSample.
  * Tier out-of-range and escalation mismatch raise AnnotationValidationError.
"""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.data.annotation_io import (
    AnnotationValidationError,
    get_split_dataframes,
    read_annotation_csv,
    row_to_record,
)
from cese.data.schema import ClaimEvidenceSample

REAL_CSV = ROOT / "data" / "all_preannotated_annotations_clean_v2.csv"


def _write_csv(path: Path, header: list, rows: list) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(header)
        for r in rows:
            w.writerow(r)


# Minimal 44-column header matching the v2 schema.
_HEADER = [
    "sample_id", "logical_sample_id", "domain", "source_type",
    "claim_text", "evidence_text",
    "claim_tiers.scope", "claim_tiers.causal", "claim_tiers.action", "claim_tiers.certainty",
    "support_tiers.scope", "support_tiers.causal", "support_tiers.action", "support_tiers.certainty",
    "evidence_vector.alignment", "evidence_vector.transparency", "evidence_vector.coverage",
    "evidence_vector.traceability", "evidence_vector.boundary", "evidence_vector.uncertainty",
    "evidence_vector.causal_id", "evidence_vector.risk_utility",
    "evidence_confidence.alignment", "evidence_confidence.transparency", "evidence_confidence.coverage",
    "evidence_confidence.traceability", "evidence_confidence.boundary", "evidence_confidence.uncertainty",
    "evidence_confidence.causal_id", "evidence_confidence.risk_utility",
    "contradiction_label", "escalation_label", "escalation_type", "evidence_gap_labels",
    "rewrite_target", "split", "template_id", "claim_family",
    "annotation.annotators", "annotation.annotation_round", "annotation.agreement_score",
    "annotation.is_human_audited", "annotation.evidence_spans", "annotation.extraction_method",
]


def _toy_row(sample_id: str, split: str, action_claim: int = 0, action_support: int = 0,
             esc_label: int = 0) -> list:
    """Build one CSV row. action tiers are parameterized to test tier=0."""
    return [
        sample_id, f"lsid-{sample_id}", "cyber_defense", "oracle",
        "claim", "evidence",
        # claim tiers
        2, 1, action_claim, 2,
        # support tiers
        2, 1, action_support, 2,
        # evidence_vector
        0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 0.5,
        # evidence_confidence (varied so sample_weight is meaningful)
        0.8, 0.7, 0.6, 0.5, 0.7, 0.6, 0.5, 0.8,
        # contradiction, escalation, escalation_type, gap_labels
        0, esc_label, "[]", "[]",
        # rewrite, split, template, family
        "", split, "tpl-1", "cyber_acd_gym",
        # annotation
        '["ai_pre_annotated"]', 1, "0.6", "false",
        '[{"start":0,"end":5}]', "ai_pre_annotation",
    ]


# ---------------------------------------------------------------------------
# Tests against the real shipped v2 CSV
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not REAL_CSV.exists(), reason="v2 CSV not shipped")
class TestRealCsv:
    def test_reads_without_error(self):
        df = read_annotation_csv(REAL_CSV)
        assert len(df) == 80
        assert df.shape[1] >= 44  # 44 original + sample_weight

    def test_json_fields_are_lists(self):
        df = read_annotation_csv(REAL_CSV)
        for col in ("escalation_type", "evidence_gap_labels",
                    "annotation.annotators", "annotation.evidence_spans"):
            assert all(isinstance(v, list) for v in df[col]), f"{col} not all lists"

    def test_split_counts(self):
        tr, va, te = get_split_dataframes(REAL_CSV)
        assert len(tr) == 48
        assert len(va) == 16
        assert len(te) == 16

    def test_action_tier_allows_zero(self):
        df = read_annotation_csv(REAL_CSV)
        # The v2 CSV has rows where claim_tiers.action == 0.
        n_zero = int((df["claim_tiers.action"] == 0).sum())
        assert n_zero > 0, "expected claim_tiers.action=0 to be present"
        # And they must be in the valid [0,4] range.
        assert df["claim_tiers.action"].between(0, 4).all()

    def test_sample_weight_in_unit_range(self):
        df = read_annotation_csv(REAL_CSV)
        assert "sample_weight" in df.columns
        sw = df["sample_weight"]
        assert (sw >= 0.0).all() and (sw <= 1.0).all()

    def test_escalation_label_matches_overflow(self):
        df = read_annotation_csv(REAL_CSV)
        # read_annotation_csv already validates this, but double-check.
        claim = df[[f"claim_tiers.{d}" for d in ("scope", "causal", "action", "certainty")]].to_numpy()
        support = df[[f"support_tiers.{d}" for d in ("scope", "causal", "action", "certainty")]].to_numpy()
        expected = (claim > support).any(axis=1).astype(int)
        assert (expected == df["escalation_label"].to_numpy()).all()

    def test_row_to_record_is_schema_valid(self):
        df = read_annotation_csv(REAL_CSV)
        rec = row_to_record(df.iloc[0])
        # Must not raise.
        sample = ClaimEvidenceSample(**rec)
        assert sample.sample_id == rec["sample_id"]
        assert sample.sample_weight is not None


# ---------------------------------------------------------------------------
# Synthetic CSV tests for validation failure modes
# ---------------------------------------------------------------------------

class TestValidationFailures:
    def test_tier_out_of_range_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        row = _toy_row("s1", "train", action_claim=5)  # 5 > 4
        _write_csv(p, _HEADER, [row])
        with pytest.raises(AnnotationValidationError, match="outside"):
            read_annotation_csv(p)

    def test_tier_negative_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        row = _toy_row("s1", "train", action_claim=-1)
        _write_csv(p, _HEADER, [row])
        with pytest.raises(AnnotationValidationError, match="outside"):
            read_annotation_csv(p)

    def test_escalation_mismatch_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        # action claim=3 > support=1 => overclaim, but label says 0.
        row = _toy_row("s1", "train", action_claim=3, action_support=1, esc_label=0)
        _write_csv(p, _HEADER, [row])
        with pytest.raises(AnnotationValidationError, match="escalation_label disagrees"):
            read_annotation_csv(p)

    def test_logical_sample_inconsistency_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        # Two rows same logical_sample_id but different evidence_text.
        r1 = _toy_row("s1", "train")
        r2 = _toy_row("s2", "train")
        r2[1] = "lsid-s1"  # same logical id
        r2[5] = "DIFFERENT evidence"  # different evidence_text (col index 5)
        # Fix escalation: make r2 consistent (claim=support so label=0).
        _write_csv(p, _HEADER, [r1, r2])
        with pytest.raises(AnnotationValidationError, match="inconsistent"):
            read_annotation_csv(p)

    def test_unexpected_split_value_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        row = _toy_row("s1", "holdout")  # not train/validation/test
        _write_csv(p, _HEADER, [row])
        with pytest.raises(AnnotationValidationError, match="unexpected"):
            get_split_dataframes(p)

    def test_malformed_json_raises(self, tmp_path):
        p = tmp_path / "bad.csv"
        row = _toy_row("s1", "train")
        row[32] = "not json"  # escalation_type column
        _write_csv(p, _HEADER, [row])
        with pytest.raises(AnnotationValidationError, match="not valid JSON"):
            read_annotation_csv(p)


class TestTierZeroAcceptance:
    def test_action_claim_zero_accepted(self, tmp_path):
        p = tmp_path / "ok.csv"
        row = _toy_row("s1", "train", action_claim=0, action_support=0, esc_label=0)
        _write_csv(p, _HEADER, [row])
        df = read_annotation_csv(p)
        assert int(df["claim_tiers.action"].iloc[0]) == 0
