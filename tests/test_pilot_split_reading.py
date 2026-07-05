"""Tests for P0-1: train/dev/test split reading in train_cese_ocn.py and
CesEOcnDataset.

Verifies:
- When the SAME JSONL is passed for train/dev/test, each split reads its
  own subset via the per-record ``split`` field (no aliasing of dev to
  train).
- Pre-split files (pilot_train.jsonl / pilot_dev.jsonl / pilot_test.jsonl)
  work correctly when records do not carry a ``split`` field (the dataset
  must not error just because split=X is requested on a file with no
  ``split`` column when ``split=None``).
- Empty split -> clear ValueError.
- Missing ``split`` field entirely -> clear ValueError pointing at the
  missing column.
- Single-class split (only positives or only negatives) is detectable
  via the dataset's records (check_pilot_balance is the real gate, but
  we expose the per-split records so it can run).
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.data.dataset import CesEOcnDataset


def _make_record(
    sample_id: str, split: str, escalation_label: int = 0,
    claim_family: str = "descriptive",
) -> dict:
    """Minimal valid record for CesEOcnDataset."""
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "academic_claim",
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
        "claim_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "support_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "contradiction_label": 0,
        "escalation_label": escalation_label,
        "split": split,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# Same JSONL for train/dev/test must split correctly
# ---------------------------------------------------------------------------

def test_same_jsonl_for_all_splits_yields_distinct_subsets(tmp_path):
    """When pilot_all.jsonl is used for train, dev, AND test, each split
    must read its own subset via the per-record ``split`` field. Dev must
    NOT be aliased to train (the old bug)."""
    all_path = tmp_path / "pilot_all.jsonl"
    records = []
    # 6 train, 3 dev, 3 test -> 12 total. Positive/negative mixed.
    for i in range(6):
        records.append(_make_record(f"tr{i}", "train", escalation_label=i % 2))
    for i in range(3):
        records.append(_make_record(f"dv{i}", "dev", escalation_label=i % 2))
    for i in range(3):
        records.append(_make_record(f"te{i}", "test", escalation_label=i % 2))
    _write_jsonl(all_path, records)

    # All three use the SAME path. This is the bug scenario.
    train_ds = CesEOcnDataset(all_path, split="train")
    dev_ds = CesEOcnDataset(all_path, split="dev")
    test_ds = CesEOcnDataset(all_path, split="test")

    assert len(train_ds) == 6
    assert len(dev_ds) == 3
    assert len(test_ds) == 3
    # Verify the records are actually different (no aliasing).
    train_ids = {r["sample_id"] for r in train_ds.records}
    dev_ids = {r["sample_id"] for r in dev_ds.records}
    test_ids = {r["sample_id"] for r in test_ds.records}
    assert train_ids == {f"tr{i}" for i in range(6)}
    assert dev_ids == {f"dv{i}" for i in range(3)}
    assert test_ids == {f"te{i}" for i in range(3)}
    # No overlap between splits.
    assert train_ids.isdisjoint(dev_ids)
    assert train_ids.isdisjoint(test_ids)
    assert dev_ids.isdisjoint(test_ids)


# ---------------------------------------------------------------------------
# Pre-split files (records with no ``split`` field) work when split=None
# ---------------------------------------------------------------------------

def test_pre_split_file_no_split_field_works_with_split_none(tmp_path):
    """Pre-split files like pilot_train.jsonl may not carry a ``split``
    field. Loading with split=None must read all records."""
    train_path = tmp_path / "pilot_train.jsonl"
    records = [_make_record(f"tr{i}", split=None) for i in range(5)]
    # Remove the split field entirely.
    for r in records:
        del r["split"]
    _write_jsonl(train_path, records)

    ds = CesEOcnDataset(train_path, split=None)
    assert len(ds) == 5


def test_pre_split_file_no_split_field_errors_when_split_requested(tmp_path):
    """Pre-split file with no ``split`` field: requesting split='train'
    must raise a CLEAR error explaining the column is missing."""
    train_path = tmp_path / "pilot_train.jsonl"
    records = [_make_record(f"tr{i}", split=None) for i in range(5)]
    for r in records:
        del r["split"]
    _write_jsonl(train_path, records)

    with pytest.raises(ValueError, match="split"):
        CesEOcnDataset(train_path, split="train")


# ---------------------------------------------------------------------------
# Empty / missing split -> clear error
# ---------------------------------------------------------------------------

def test_empty_file_raises_clear_error(tmp_path):
    """An empty JSONL must raise a clear error (file is empty)."""
    empty_path = tmp_path / "empty.jsonl"
    empty_path.write_text("", encoding="utf-8")
    with pytest.raises(ValueError, match="empty"):
        CesEOcnDataset(empty_path, split="train")


def test_split_field_present_but_no_match_raises_clear_error(tmp_path):
    """File only contains 'train' records; requesting split='test' must
    raise an error listing the requested split."""
    train_only_path = tmp_path / "pilot_train.jsonl"
    records = [_make_record(f"tr{i}", "train") for i in range(5)]
    _write_jsonl(train_only_path, records)
    with pytest.raises(ValueError, match="test"):
        CesEOcnDataset(train_only_path, split="test")


# ---------------------------------------------------------------------------
# Single-class split is detectable via records
# ---------------------------------------------------------------------------

def test_single_class_split_records_exposed_for_balance_check(tmp_path):
    """A split with only positives (escalation_label=1) must be loadable
    so check_pilot_balance can flag the imbalance. The dataset itself
    does NOT enforce balance; it just exposes the records."""
    all_path = tmp_path / "pilot_all.jsonl"
    records = []
    # train has both classes.
    for i in range(4):
        records.append(_make_record(f"tr{i}", "train", escalation_label=i % 2))
    # dev has ONLY positives (imbalanced).
    for i in range(4):
        records.append(_make_record(f"dv{i}", "dev", escalation_label=1))
    # test has ONLY negatives (imbalanced).
    for i in range(4):
        records.append(_make_record(f"te{i}", "test", escalation_label=0))
    _write_jsonl(all_path, records)

    dev_ds = CesEOcnDataset(all_path, split="dev")
    dev_labels = [r["escalation_label"] for r in dev_ds.records]
    assert all(l == 1 for l in dev_labels)
    # The dataset loads successfully; check_pilot_balance is the gate.

    test_ds = CesEOcnDataset(all_path, split="test")
    test_labels = [r["escalation_label"] for r in test_ds.records]
    assert all(l == 0 for l in test_labels)


# ---------------------------------------------------------------------------
# train_cese_ocn.py CLI behavior (integration)
# ---------------------------------------------------------------------------

def test_train_cli_uses_per_record_split_not_path_alias(tmp_path):
    """Integration: train_cese_ocn.main with --train=--dev=--test=pilot_all.jsonl
    must load distinct subsets. We verify by reading the source and
    checking the short-circuit (dev_path != train_path) is GONE."""
    src_path = ROOT / "scripts" / "train_cese_ocn.py"
    source = src_path.read_text(encoding="utf-8")
    # The old buggy short-circuit must NOT be present.
    assert "if dev_path != train_path else train_ds" not in source
    # The fix loads dev independently. The exact call format may vary
    # (e.g. multi-line with use_extended_evidence kwarg), so we check
    # that dev_path is loaded with split="dev" rather than aliasing
    # train_ds.
    assert 'dev_path, split="dev"' in source


def test_train_cli_has_test_argument(tmp_path):
    """--test argument must exist for spec CLI provenance."""
    src_path = ROOT / "scripts" / "train_cese_ocn.py"
    source = src_path.read_text(encoding="utf-8")
    assert '"--test"' in source
