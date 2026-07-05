"""Tests for P6-4: check_pilot_balance.py structured report + checks.

Verifies the 7 checks required by task 1:
  1. Each split has pos + neg samples.
  2. Each main dimension has supported + overclaim.
  3. Overclaim samples must have evidence_gap_labels.
  4. Overclaim samples should have rewrite_target (warning).
  5. source_type should be all oracle; mix -> warning.
  6. claim_tiers/support_tiers consistency with escalation_label.
  7. contradiction=1 AND escalation=1 -> warning.

Plus structured JSON report shape (total/positive/negative/by_split/
by_dimension/warnings/errors).
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

import check_pilot_balance as cpb


# ---------------------------------------------------------------------------
# record builders
# ---------------------------------------------------------------------------


def _supported_rec(sample_id: str, split: str = "train",
                   rewrite_target: str = "rewrite-x",
                   source_type: str = "oracle") -> dict:
    """A balanced supported record (escalation_label=0)."""
    return {
        "sample_id": sample_id,
        "escalation_label": 0,
        "escalation_type": [],
        "claim_tiers": {"scope": 1, "causal": 1, "action": 1, "certainty": 1},
        "support_tiers": {"scope": 2, "causal": 2, "action": 2, "certainty": 2},
        "evidence_gap_labels": [],
        "rewrite_target": rewrite_target,
        "split": split,
        "source_type": source_type,
        "contradiction_label": 0,
        "claim_family": "descriptive",
    }


def _overclaim_rec(sample_id: str, dim: str = "scope",
                  split: str = "train",
                  with_gap: bool = True,
                  with_rewrite: bool = True,
                  source_type: str = "oracle",
                  contradiction: int = 0) -> dict:
    """A balanced overclaim record (escalation_label=1) on the given dim."""
    ct = {"scope": 1, "causal": 1, "action": 1, "certainty": 1}
    st = {"scope": 1, "causal": 1, "action": 1, "certainty": 1}
    ct[dim] = 3
    st[dim] = 1
    return {
        "sample_id": sample_id,
        "escalation_label": 1,
        "escalation_type": [dim],
        "claim_tiers": ct,
        "support_tiers": st,
        "evidence_gap_labels": [f"{dim}_missing"] if with_gap else [],
        "rewrite_target": "rewrite-x" if with_rewrite else None,
        "split": split,
        "source_type": source_type,
        "contradiction_label": contradiction,
        "claim_family": dim,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _balanced_40_records() -> list[dict]:
    """40 balanced records: 4 dims x 5 supported + 5 overclaim, split
    across train/dev/test with both classes in each split."""
    recs = []
    sid = 0
    dims = ["scope", "causal", "action", "certainty"]
    # 4 dims x 5 overclaim + 4 dims x 5 supported = 40 records.
    for dim in dims:
        for _ in range(5):
            sid += 1
            recs.append(_overclaim_rec(f"s{sid:03d}", dim=dim,
                                       split="train" if sid % 3 else "dev"))
    for dim in dims:
        for _ in range(5):
            sid += 1
            recs.append(_supported_rec(f"s{sid:03d}",
                                       split="train" if sid % 3 else "dev"))
    # Ensure test split also has pos+neg (rotate a few into test).
    recs[0]["split"] = "test"
    recs[1]["split"] = "test"
    recs[20]["split"] = "test"
    recs[21]["split"] = "test"
    return recs


# ---------------------------------------------------------------------------
# check 1+2: balanced pilot passes
# ---------------------------------------------------------------------------


def test_balanced_40_pilot_passes(tmp_path):
    """A balanced 40-record pilot must pass all checks (ok=True, no errors)."""
    p = tmp_path / "pilot.jsonl"
    _write_jsonl(p, _balanced_40_records())
    report = cpb.check_balance(str(p))

    # Structured report keys.
    assert report["total"] == 40
    assert "positive" in report
    assert "negative" in report
    assert report["positive"] + report["negative"] == 40
    assert isinstance(report["by_split"], dict)
    assert isinstance(report["by_dimension"], dict)
    assert set(report["by_dimension"].keys()) == {"scope", "causal", "action", "certainty"}
    assert isinstance(report["warnings"], list)
    assert isinstance(report["errors"], list)
    # Each split has both pos and neg.
    for split, counts in report["by_split"].items():
        assert counts["positive"] > 0, f"{split} has no positive"
        assert counts["negative"] > 0, f"{split} has no negative"
    # Each dimension has both supported and overclaim.
    for dim, counts in report["by_dimension"].items():
        assert counts["supported"] > 0, f"{dim} has no supported"
        assert counts["overclaim"] > 0, f"{dim} has no overclaim"
    # No errors: balance + consistency all OK.
    assert report["errors"] == [], f"unexpected errors: {report['errors']}"
    assert report["ok"] is True


# ---------------------------------------------------------------------------
# check 2: missing dimension overclaim -> warning
# ---------------------------------------------------------------------------


def test_missing_dim_overclaim_warns(tmp_path):
    """When a dimension has no overclaim samples, check_pilot_balance must
    add a warning (advisory, not blocking)."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Remove all 'certainty' overclaims -> certainty has 0 overclaim.
    recs = [r for r in recs if not (
        r["escalation_label"] == 1 and r["escalation_type"] == ["certainty"]
    )]
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    # certainty overclaim=0 should produce a warning.
    cert_warnings = [w for w in report["warnings"] if "certainty" in w and "overclaim" in w]
    assert len(cert_warnings) >= 1, \
        f"expected warning for missing certainty overclaim, got {report['warnings']}"


# ---------------------------------------------------------------------------
# check 1: single-class split -> error
# ---------------------------------------------------------------------------


def test_single_class_split_errors(tmp_path):
    """A split with only positive (or only negative) samples must error."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Move all test-split negatives to train -> test becomes pos-only.
    for r in recs:
        if r["split"] == "test" and r["escalation_label"] == 0:
            r["split"] = "train"
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    split_errors = [e for e in report["errors"] if "split 'test'" in e]
    assert len(split_errors) >= 1, \
        f"expected split balance error, got {report['errors']}"
    assert report["ok"] is False


# ---------------------------------------------------------------------------
# check 3: overclaim without evidence_gap_labels -> error
# ---------------------------------------------------------------------------


def test_overclaim_without_gap_labels_errors(tmp_path):
    """An overclaim record with no evidence_gap_labels must error."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Strip gap labels from the first overclaim record.
    for r in recs:
        if r["escalation_label"] == 1:
            r["evidence_gap_labels"] = []
            break
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    gap_errors = [e for e in report["errors"] if "evidence_gap_labels" in e]
    assert len(gap_errors) >= 1, \
        f"expected gap_labels error, got {report['errors']}"
    assert report["ok"] is False


# ---------------------------------------------------------------------------
# check 4: overclaim without rewrite_target -> warning
# ---------------------------------------------------------------------------


def test_overclaim_without_rewrite_warns(tmp_path):
    """An overclaim record without rewrite_target must produce a warning
    (advisory, not blocking)."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Strip rewrite_target from the first overclaim record.
    for r in recs:
        if r["escalation_label"] == 1:
            r["rewrite_target"] = None
            break
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    rewrite_warnings = [w for w in report["warnings"] if "rewrite_target" in w]
    assert len(rewrite_warnings) >= 1, \
        f"expected rewrite_target warning, got {report['warnings']}"
    # Warnings are advisory: ok is still True (no errors).
    assert report["ok"] is True


# ---------------------------------------------------------------------------
# check 5: source_type mix -> warning
# ---------------------------------------------------------------------------


def test_source_type_mix_warns(tmp_path):
    """A pilot dataset mixing source_type (oracle + extracted) must warn."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    recs[0]["source_type"] = "extracted"
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    src_warnings = [w for w in report["warnings"] if "source_type" in w]
    assert len(src_warnings) >= 1, \
        f"expected source_type warning, got {report['warnings']}"


# ---------------------------------------------------------------------------
# check 6: claim_tiers / support_tiers consistency
# ---------------------------------------------------------------------------


def test_tier_label_inconsistency_errors(tmp_path):
    """escalation_label=1 but no dim has claim_tiers > support_tiers -> error."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Make an overclaim record's tiers equal (no actual overclaim).
    for r in recs:
        if r["escalation_label"] == 1:
            r["claim_tiers"] = {"scope": 1, "causal": 1, "action": 1, "certainty": 1}
            r["support_tiers"] = {"scope": 1, "causal": 1, "action": 1, "certainty": 1}
            break
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    tier_errors = [e for e in report["errors"] if "claim_tiers > support_tiers" in e]
    assert len(tier_errors) >= 1, \
        f"expected tier consistency error, got {report['errors']}"
    assert report["ok"] is False


def test_supported_with_overclaim_tiers_errors(tmp_path):
    """escalation_label=0 but claim_tiers > support_tiers -> error."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Make a supported record's tiers inconsistent.
    for r in recs:
        if r["escalation_label"] == 0:
            r["claim_tiers"]["scope"] = 3
            r["support_tiers"]["scope"] = 1
            break
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    tier_errors = [e for e in report["errors"] if "claim_tiers > support_tiers" in e]
    assert len(tier_errors) >= 1, \
        f"expected tier consistency error, got {report['errors']}"
    assert report["ok"] is False


# ---------------------------------------------------------------------------
# check 7: contradiction=1 AND escalation=1 -> warning
# ---------------------------------------------------------------------------


def test_contradiction_escalation_warns(tmp_path):
    """contradiction_label=1 AND escalation_label=1 must warn."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    recs[0]["contradiction_label"] = 1  # also escalation_label=1
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    dual_warnings = [
        w for w in report["warnings"]
        if "contradiction_label=1" in w and "escalation_label=1" in w
    ]
    assert len(dual_warnings) >= 1, \
        f"expected contradiction+escalation warning, got {report['warnings']}"
    # Advisory: ok stays True.
    assert report["ok"] is True


# ---------------------------------------------------------------------------
# escalation_label=None -> error (call fill_escalation_labels first)
# ---------------------------------------------------------------------------


def test_none_escalation_label_errors(tmp_path):
    """Records with escalation_label=None must error (must fill first)."""
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    recs[0]["escalation_label"] = None
    _write_jsonl(p, recs)
    report = cpb.check_balance(str(p))

    none_errors = [e for e in report["errors"] if "escalation_label is None" in e]
    assert len(none_errors) >= 1, \
        f"expected None-label error, got {report['errors']}"
    assert report["ok"] is False


# ---------------------------------------------------------------------------
# CLI exit code: blocking errors -> exit 1
# ---------------------------------------------------------------------------


def test_cli_exit_code_on_blocking_error(tmp_path):
    """CLI must exit 1 when there are blocking errors."""
    import subprocess
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Strip gap labels -> blocking error.
    for r in recs:
        if r["escalation_label"] == 1:
            r["evidence_gap_labels"] = []
            break
    _write_jsonl(p, recs)
    proc = subprocess.run(
        [sys.executable, "-u", "scripts/check_pilot_balance.py",
         "--input", str(p)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode != 0, "blocking errors must exit non-zero"


def test_cli_exit_code_zero_on_warnings(tmp_path):
    """CLI must exit 0 when only warnings (no errors)."""
    import subprocess
    p = tmp_path / "pilot.jsonl"
    recs = _balanced_40_records()
    # Strip rewrite_target -> warning only.
    for r in recs:
        if r["escalation_label"] == 1:
            r["rewrite_target"] = None
            break
    _write_jsonl(p, recs)
    proc = subprocess.run(
        [sys.executable, "-u", "scripts/check_pilot_balance.py",
         "--input", str(p)],
        cwd=str(ROOT), capture_output=True, text=True, timeout=60,
    )
    assert proc.returncode == 0, "warnings only must exit zero"
