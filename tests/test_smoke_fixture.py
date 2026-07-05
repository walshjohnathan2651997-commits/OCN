"""Tests for smoke fixture split coverage and report metadata accuracy.

Task 2 acceptance:
- test_smoke_fixture_has_train_dev_test: smoke fixture has 16/8/8 with
  every source_type in train/test and both escalation classes per split.
- test_report_metadata_counts_real_splits: generate_tables._count_splits
  returns actual per-split counts, not total line count.
"""

from __future__ import annotations

import json
import os
import sys
from collections import Counter
from pathlib import Path

import pytest

# Ensure project root is importable.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.data.toy_data import generate_smoke_records
from cese.data.splits import split_stats
from cese.constants import CLAIM_DIMS, SOURCE_TYPES


def test_smoke_fixture_has_train_dev_test():
    """Smoke fixture must have train/dev/test = 16/8/8 with coverage."""
    records = generate_smoke_records(seed=42)
    stats = split_stats(records)

    # Exact split sizes.
    assert stats["train"]["n"] == 16, f"train={stats['train']['n']}, expected 16"
    assert stats["dev"]["n"] == 8, f"dev={stats['dev']['n']}, expected 8"
    assert stats["test"]["n"] == 8, f"test={stats['test']['n']}, expected 8"

    # Both escalation classes present in each split.
    for split in ("train", "dev", "test"):
        s = stats[split]
        assert s["escalation_pos"] > 0, f"{split} has no positive samples"
        assert s["escalation_neg"] > 0, f"{split} has no negative samples"

    # Every source_type appears in train and test.
    for split in ("train", "test"):
        sources = {r["source_type"] for r in records if r["split"] == split}
        for st in SOURCE_TYPES:
            assert st in sources, f"{st} missing from {split} split"


def test_report_metadata_counts_real_splits(tmp_path):
    """_count_splits must return per-split counts, not total line count."""
    # Import the function from generate_tables.
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_tables", ROOT / "scripts" / "generate_tables.py"
    )
    gt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gt)

    # Write a small JSONL with known splits.
    records = generate_smoke_records(seed=42)
    jsonl_path = tmp_path / "test.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    info = gt._count_splits(str(jsonl_path))

    # Should match actual split counts, not total (32).
    assert info["n_train"] == 16, f"n_train={info['n_train']}, expected 16"
    assert info["n_dev"] == 8, f"n_dev={info['n_dev']}, expected 8"
    assert info["n_test"] == 8, f"n_test={info['n_test']}, expected 8"
    # No warnings for a well-formed fixture.
    assert info["warnings"] == [], f"unexpected warnings: {info['warnings']}"


def test_report_metadata_warns_on_empty_split(tmp_path):
    """_count_splits must warn when a split is empty or single-class."""
    sys.path.insert(0, str(ROOT / "scripts"))
    import importlib.util

    spec = importlib.util.spec_from_file_location(
        "generate_tables", ROOT / "scripts" / "generate_tables.py"
    )
    gt = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gt)

    # All records in train, dev/test empty.
    records = [
        {"sample_id": f"r{i}", "split": "train", "escalation_label": 0}
        for i in range(10)
    ]
    jsonl_path = tmp_path / "degenerate.jsonl"
    with jsonl_path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    info = gt._count_splits(str(jsonl_path))
    assert info["n_train"] == 10
    assert info["n_dev"] == 0
    assert info["n_test"] == 0
    # Should warn about empty dev/test and single-class train.
    warnings_str = " ".join(info["warnings"])
    assert "dev" in warnings_str, f"expected dev warning, got: {info['warnings']}"
    assert "test" in warnings_str, f"expected test warning, got: {info['warnings']}"
    assert "single-class" in warnings_str, f"expected single-class warning, got: {info['warnings']}"


def test_toy_records_escalation_consistent():
    """escalation_label / escalation_type must be derived from
    claim_tiers > support_tiers, never independently sampled.
    """
    records = generate_smoke_records()
    for r in records:
        expected_dims = [
            d for d in CLAIM_DIMS
            if r["claim_tiers"][d] > r["support_tiers"][d]
        ]
        assert r["escalation_label"] == int(bool(expected_dims))
        assert sorted(r["escalation_type"]) == sorted(expected_dims)


def test_evidence_gap_labels_follow_preregistered_rule():
    """evidence_gap_labels must follow the pre-registered missing-evidence
    rule: a dim is "missing" iff value <= 0.2 AND confidence <= 0.3.

    Additionally, for each escalated dim k, at least one R(k) evidence dim
    must be in the gap labels (the toy generator weakens R(k) for escalated
    dims so the gap labels explain *why* support was downgraded).
    """
    from cese.constants import R_EXPERT
    from cese.data.toy_data import (
        EVIDENCE_VALUE_MISSING_THRESHOLD,
        EVIDENCE_CONF_MISSING_THRESHOLD,
    )

    records = generate_smoke_records()
    for r in records:
        ev = r["evidence_vector"]
        ec = r["evidence_confidence"]
        expected_gaps = {
            f"{d}_missing"
            for d in ev
            if ev[d] <= EVIDENCE_VALUE_MISSING_THRESHOLD
            and ec[d] <= EVIDENCE_CONF_MISSING_THRESHOLD
        }
        assert set(r["evidence_gap_labels"]) == expected_gaps

        # For each escalated dim k, at least one R(k) evidence dim must
        # appear in the gap labels.
        for k in r["escalation_type"]:
            rk_dims = R_EXPERT.get(k, [])
            rk_gaps = {f"{d}_missing" for d in rk_dims}
            assert rk_gaps & set(r["evidence_gap_labels"]), (
                f"escalated dim {k} has no R(k) gap in {r['evidence_gap_labels']}"
            )
