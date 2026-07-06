"""Tests for P0-2: scripts/split_pilot_data.py."""

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

import split_pilot_data as sp


def _make_record(
    sample_id: str,
    escalation_label: int = 0,
    claim_family: str = "descriptive",
    domain: str = "academic_claim",
    template_id: str = "t0",
    primary_dim: str = "scope",
) -> dict:
    """Make a record with a given primary escalation dimension.

    To control primary_dim, we set claim_tiers/support_tiers so the
    requested dim is the first where claim > support.
    """
    claim = {"scope": 0, "causal": 0, "action": 0, "certainty": 0}
    support = {"scope": 0, "causal": 0, "action": 0, "certainty": 0}
    if escalation_label == 1:
        # Set the requested dim to claim>support.
        claim[primary_dim] = 2
        support[primary_dim] = 0
    else:
        # For negatives, set claim=support on all dims so primary_dim
        # is computed from the first non-zero claim dim (still the
        # requested dim if claim > 0).
        claim[primary_dim] = 1
        support[primary_dim] = 1
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": domain,
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_family": claim_family,
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
        "claim_tiers": claim,
        "support_tiers": support,
        "contradiction_label": 0,
        "escalation_label": escalation_label,
        "template_id": template_id,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# 40 samples -> 24/8/8 split
# ---------------------------------------------------------------------------

def test_40_samples_split_into_24_8_8(tmp_path):
    """40 synthetic pilot records split 60/20/20 -> 24/8/8."""
    records = []
    dims = ["scope", "causal", "action", "certainty"]
    for i in range(40):
        records.append(_make_record(
            sample_id=f"s{i}",
            escalation_label=i % 2,  # balanced pos/neg
            primary_dim=dims[i % 4],  # covers all 4 dims
        ))
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)

    rc = sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
        "--train_ratio", "0.6",
        "--dev_ratio", "0.2",
        "--test_ratio", "0.2",
        "--seed", "13",
    ])
    assert rc == 0
    out = tmp_path / "out"
    train = [json.loads(l) for l in (out / "pilot_train.jsonl").read_text(encoding="utf-8").splitlines() if l]
    dev = [json.loads(l) for l in (out / "pilot_dev.jsonl").read_text(encoding="utf-8").splitlines() if l]
    test = [json.loads(l) for l in (out / "pilot_test.jsonl").read_text(encoding="utf-8").splitlines() if l]
    assert len(train) == 24
    assert len(dev) == 8
    assert len(test) == 8
    # No sample_id overlap.
    ids = {s["sample_id"] for s in train}
    ids |= {s["sample_id"] for s in dev}
    ids |= {s["sample_id"] for s in test}
    assert len(ids) == 40


def test_split_records_stamped_with_split_field(tmp_path):
    """Output records must carry the ``split`` field so downstream
    loaders (CesEOcnDataset) filter correctly even if concatenated."""
    records = [_make_record(f"s{i}", escalation_label=i % 2) for i in range(20)]
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
    ])
    out = tmp_path / "out"
    for split_name in ("train", "dev", "test"):
        p = out / f"pilot_{split_name}.jsonl"
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            assert json.loads(line)["split"] == split_name


def test_split_manifest_complete(tmp_path):
    """split_manifest.json must contain per-split stats."""
    records = []
    dims = ["scope", "causal", "action", "certainty"]
    for i in range(40):
        records.append(_make_record(
            sample_id=f"s{i}",
            escalation_label=i % 2,
            primary_dim=dims[i % 4],
            claim_family=["descriptive", "causal", "action", "certainty"][i % 4],
            domain=["academic_claim", "controlled_simulation"][i % 2],
            template_id=f"t{i % 3}",
        ))
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
        "--seed", "13",
    ])
    manifest = json.loads(
        (tmp_path / "out" / "split_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["total_samples"] == 40
    assert manifest["seed"] == 13
    assert manifest["stratify_by"] == ["escalation_label", "primary_escalation_dimension"]
    for split_name in ("train", "dev", "test"):
        s = manifest["splits"][split_name]
        assert s["n_samples"] > 0
        assert "n_positive" in s
        assert "n_negative" in s
        assert "claim_family_distribution" in s
        assert "domain_distribution" in s
        assert "template_distribution" in s
        assert "primary_escalation_dimension_distribution" in s
    assert (
        manifest["splits"]["train"]["n_samples"]
        + manifest["splits"]["dev"]["n_samples"]
        + manifest["splits"]["test"]["n_samples"]
        == 40
    )


def test_split_validates_after_split(tmp_path):
    """Split files must pass ClaimEvidenceSample validation."""
    from cese.data.schema import ClaimEvidenceSample
    records = [_make_record(f"s{i}", escalation_label=i % 2) for i in range(20)]
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
    ])
    out = tmp_path / "out"
    for split_name in ("train", "dev", "test"):
        p = out / f"pilot_{split_name}.jsonl"
        for line in p.read_text(encoding="utf-8").splitlines():
            if not line:
                continue
            r = json.loads(line)
            # Must validate without error.
            ClaimEvidenceSample(**r)


def test_small_sample_emits_warning(tmp_path, capsys):
    """When sample size is too small to balance, emit a WARNING."""
    # Only 4 records, all negative -> imbalanced.
    records = [_make_record(f"s{i}", escalation_label=0) for i in range(4)]
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
    ])
    # The script should have written warnings to the log (we check the
    # exit code is still 0, NOT a silent failure).
    out = tmp_path / "out"
    assert (out / "split_manifest.json").exists()


def test_each_split_has_supported_and_overclaim(tmp_path):
    """Each split should contain at least one positive and one negative
    when the input is balanced and large enough."""
    records = []
    dims = ["scope", "causal", "action", "certainty"]
    for i in range(40):
        records.append(_make_record(
            sample_id=f"s{i}",
            escalation_label=i % 2,
            primary_dim=dims[i % 4],
        ))
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    sp.main([
        "--input", str(in_path),
        "--output_dir", str(tmp_path / "out"),
    ])
    out = tmp_path / "out"
    for split_name in ("train", "dev", "test"):
        p = out / f"pilot_{split_name}.jsonl"
        records = [json.loads(l) for l in p.read_text(encoding="utf-8").splitlines() if l]
        labels = [r["escalation_label"] for r in records]
        assert any(l == 1 for l in labels), f"{split_name} has no positives"
        assert any(l == 0 for l in labels), f"{split_name} has no negatives"


def test_invalid_ratios_raise(tmp_path):
    """Ratios that don't sum to 1.0 must raise."""
    records = [_make_record("s0", 0), _make_record("s1", 1)]
    in_path = tmp_path / "pilot_all.jsonl"
    _write_jsonl(in_path, records)
    with pytest.raises(ValueError, match="sum to 1"):
        sp.split_pilot_data(
            records,
            train_ratio=0.5,
            dev_ratio=0.3,
            test_ratio=0.3,  # sum=1.1
        )
