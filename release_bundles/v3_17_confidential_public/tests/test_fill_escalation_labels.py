"""Tests for P1-5: scripts/fill_escalation_labels.py.

Verifies:
- Correctly fills missing escalation_label from tiers.
- escalation_type lists every dim where claim > support (multi-dim case).
- Conflicts (existing label != tier-derived) error by default.
- --overwrite replaces conflicting labels.
- Summary output is correct.
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

import fill_escalation_labels as fel


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
        "split": "train",
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# compute_escalation
# ---------------------------------------------------------------------------

def test_compute_escalation_supported():
    """claim_tiers == support_tiers -> label=0, type=[]"""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 2, "causal": 1, "action": 0, "certainty": 3}
    rec["support_tiers"] = {"scope": 2, "causal": 1, "action": 0, "certainty": 3}
    label, dims = fel.compute_escalation(rec)
    assert label == 0
    assert dims == []


def test_compute_escalation_single_dim_overclaim():
    """claim_tiers.scope > support_tiers.scope -> label=1, type=['scope']"""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 1, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 1, "action": 0, "certainty": 0}
    label, dims = fel.compute_escalation(rec)
    assert label == 1
    assert dims == ["scope"]


def test_compute_escalation_multi_dim_overclaim():
    """Multiple dims overclaim -> all listed in escalation_type."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 2, "action": 0, "certainty": 4}
    rec["support_tiers"] = {"scope": 1, "causal": 1, "action": 0, "certainty": 2}
    label, dims = fel.compute_escalation(rec)
    assert label == 1
    # All three escalated dims must be listed, in CLAIM_DIMS order.
    assert dims == ["scope", "causal", "certainty"]


# ---------------------------------------------------------------------------
# fill_escalation_labels: correct fill
# ---------------------------------------------------------------------------

def test_fill_missing_label():
    """Missing escalation_label is filled from tiers."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 0, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["escalation_label"] = None
    filled, summary = fel.fill_escalation_labels([rec])
    assert filled[0]["escalation_label"] == 1
    assert filled[0]["escalation_type"] == ["scope"]
    assert summary["positive_count"] == 1
    assert summary["negative_count"] == 0
    assert summary["changed_labels"] == 1


def test_fill_preserves_correct_label():
    """An existing correct label is not changed."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["escalation_label"] = 0
    rec["escalation_type"] = []
    filled, summary = fel.fill_escalation_labels([rec])
    assert filled[0]["escalation_label"] == 0
    assert summary["changed_labels"] == 0


# ---------------------------------------------------------------------------
# Conflict handling
# ---------------------------------------------------------------------------

def test_conflict_errors_by_default():
    """A conflicting existing label must error by default (no overwrite)."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 0, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["escalation_label"] = 0  # WRONG: tiers say 1
    with pytest.raises(ValueError, match="conflict"):
        fel.fill_escalation_labels([rec], overwrite=False)


def test_overwrite_fixes_conflict():
    """--overwrite replaces the conflicting label with the tier-derived one."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 0, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["escalation_label"] = 0  # WRONG
    filled, summary = fel.fill_escalation_labels([rec], overwrite=True)
    assert filled[0]["escalation_label"] == 1
    assert filled[0]["escalation_type"] == ["scope"]
    assert summary["changed_labels"] == 1
    assert summary["n_conflicts"] == 1


# ---------------------------------------------------------------------------
# Multi-dim escalation_type
# ---------------------------------------------------------------------------

def test_multi_dim_escalation_type_listed():
    """When multiple dims escalate, escalation_type lists all of them."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 2, "action": 0, "certainty": 4}
    rec["support_tiers"] = {"scope": 1, "causal": 1, "action": 0, "certainty": 2}
    rec["escalation_label"] = None
    filled, _ = fel.fill_escalation_labels([rec])
    assert filled[0]["escalation_type"] == ["scope", "causal", "certainty"]


# ---------------------------------------------------------------------------
# CLI end-to-end
# ---------------------------------------------------------------------------

def test_cli_end_to_end(tmp_path, capsys):
    """The CLI fills labels and prints a summary."""
    records = []
    # 1 overclaim (scope), 1 supported.
    r = _base_record("s1")
    r["claim_tiers"] = {"scope": 3, "causal": 0, "action": 0, "certainty": 0}
    r["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    r["escalation_label"] = None
    records.append(r)
    r = _base_record("s2")
    r["claim_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    r["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    r["escalation_label"] = None
    records.append(r)
    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.jsonl"
    _write_jsonl(in_path, records)

    rc = fel.main(["--input", str(in_path), "--output", str(out_path)])
    assert rc == 0
    lines = [l for l in out_path.read_text(encoding="utf-8").splitlines() if l]
    recs = [json.loads(l) for l in lines]
    assert recs[0]["escalation_label"] == 1
    assert recs[0]["escalation_type"] == ["scope"]
    assert recs[1]["escalation_label"] == 0
    assert recs[1]["escalation_type"] == []

    # Summary printed to stderr.
    err = capsys.readouterr().err
    assert "total samples:          2" in err
    assert "positive (overclaim):   1" in err
    assert "negative (supported):   1" in err


def test_cli_conflict_returns_nonzero(tmp_path):
    """The CLI returns non-zero on conflict (without --overwrite)."""
    rec = _base_record("s1")
    rec["claim_tiers"] = {"scope": 3, "causal": 0, "action": 0, "certainty": 0}
    rec["support_tiers"] = {"scope": 1, "causal": 0, "action": 0, "certainty": 0}
    rec["escalation_label"] = 0  # WRONG
    in_path = tmp_path / "in.jsonl"
    out_path = tmp_path / "out.jsonl"
    _write_jsonl(in_path, [rec])

    rc = fel.main(["--input", str(in_path), "--output", str(out_path)])
    assert rc != 0
