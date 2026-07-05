"""Tests for escalation_type derivation (ocn-33 P0-2, P2-7).

Verifies ``derive_escalation_type_from_tiers`` returns a ``List[str]`` of
exceeded claim dimensions, NEVER the legacy ``mixed_overclaim`` /
``supported`` / ``{dim}_overclaim`` string encodings.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.utils.labels import (
    derive_escalation_type_from_tiers,
    derive_escalation_family_from_tiers,
    normalize_legacy_escalation_type,
)
from cese.constants import CLAIM_DIMS


def test_returns_list_of_strings():
    """escalation_type must be a List[str], not a string."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_type_from_tiers(rec)
    assert isinstance(result, list)
    assert all(isinstance(x, str) for x in result)
    assert result == ["scope"]


def test_supported_returns_empty_list():
    """Supported sample returns [], not 'supported' string."""
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_type_from_tiers(rec)
    assert isinstance(result, list)
    assert result == []


def test_does_not_return_mixed_overclaim_string():
    """Mixed overclaim must NOT be encoded as the string 'mixed_overclaim'."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 3, "action": 4, "certainty": 4},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_type_from_tiers(rec)
    assert isinstance(result, list)
    assert result != "mixed_overclaim"
    assert "mixed_overclaim" not in result
    # The list form should contain the exceeded dims.
    assert set(result) == {"scope", "causal", "action", "certainty"}


def test_does_not_return_supported_string():
    """Supported must NOT be encoded as the string 'supported'."""
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_type_from_tiers(rec)
    assert result != "supported"
    assert "supported" not in result
    assert result == []


def test_does_not_return_dim_overclaim_string():
    """Single-dim overclaim must NOT be encoded as '{dim}_overclaim'."""
    for dim in CLAIM_DIMS:
        ct = {"scope": 3, "causal": 2, "action": 2, "certainty": 3}
        st = {"scope": 3, "causal": 2, "action": 2, "certainty": 3}
        ct[dim] = ct[dim] + 1
        rec = {"claim_tiers": ct, "support_tiers": st}
        result = derive_escalation_type_from_tiers(rec)
        assert isinstance(result, list)
        legacy = f"{dim}_overclaim"
        assert result != legacy
        assert legacy not in result
        assert result == [dim]


def test_escalation_family_is_string_summary_only():
    """escalation_family is the convenience string, NOT the stored field."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    family = derive_escalation_family_from_tiers(rec)
    assert isinstance(family, str)
    assert family == "scope_overclaim"
    # The stored escalation_type field is the List[str], not the family.
    etype = derive_escalation_type_from_tiers(rec)
    assert etype == ["scope"]
    assert etype != family


def test_normalize_legacy_mixed_overclaim_to_empty_set():
    """Legacy ``mixed_overclaim`` normalizes to empty set (ambiguous dims)."""
    assert normalize_legacy_escalation_type("mixed_overclaim") == set()


def test_normalize_legacy_supported_to_empty_set():
    """Legacy ``supported`` normalizes to empty set (no exceeded dims)."""
    assert normalize_legacy_escalation_type("supported") == set()


def test_normalize_legacy_dim_overclaim_to_singleton():
    """Legacy ``{dim}_overclaim`` normalizes to {dim}."""
    for dim in CLAIM_DIMS:
        assert normalize_legacy_escalation_type(f"{dim}_overclaim") == {dim}


def test_normalize_list_of_dims_passes_through():
    """A List[str] of dims normalizes to a set of those dims."""
    result = normalize_legacy_escalation_type(["scope", "action"])
    assert result == {"scope", "action"}


def test_clean_v2_data_uses_list_not_legacy_string():
    """All clean_v2 records store escalation_type as List[str], not legacy."""
    data_path = ROOT / "data" / "clean_v2_all.jsonl"
    if not data_path.exists():
        pytest.skip(f"{data_path} not present")
    import json
    n_checked = 0
    with data_path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            rec = json.loads(line)
            et = rec.get("escalation_type")
            assert isinstance(et, list), (
                f"{rec.get('sample_id')}: escalation_type is "
                f"{type(et).__name__}, must be list"
            )
            for item in et:
                assert isinstance(item, str), (
                    f"{rec.get('sample_id')}: escalation_type item "
                    f"{item!r} is not a string"
                )
                assert item in set(CLAIM_DIMS), (
                    f"{rec.get('sample_id')}: unknown dim {item!r}"
                )
            n_checked += 1
    assert n_checked > 0, "no records checked"
