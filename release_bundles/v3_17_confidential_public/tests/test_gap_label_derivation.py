"""Tests for tier-based gap label derivation (ocn-31 P2-3, ocn-33 P0).

Verifies cese.utils.labels.derive_gap_labels_from_tiers and
derive_escalation_type_from_tiers implement the paper-main rule:
  * gap label = dimension k where claim_tier[k] > support_tier[k]
  * escalation_type is a List[str] of exceeded dims (ocn-33 P0-2)
  * escalation_family is a string summary (supported / *_overclaim / mixed)
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.utils.labels import (
    derive_gap_labels_from_tiers,
    derive_exceeded_dims,
    derive_escalation_type_from_tiers,
    derive_escalation_family_from_tiers,
)


def test_no_gap_supported_case():
    """When all claim_tiers == support_tiers, no gaps and type=[] (supported)."""
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    assert derive_gap_labels_from_tiers(rec) == set()
    assert derive_exceeded_dims(rec) == []
    # ocn-33 P0-2: escalation_type is List[str]; supported == []
    assert derive_escalation_type_from_tiers(rec) == []
    assert derive_escalation_family_from_tiers(rec) == "supported"


def test_single_dimension_gap():
    """One exceeded dimension → single gap label + ["scope"]."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    assert derive_gap_labels_from_tiers(rec) == {"scope_missing"}
    assert derive_exceeded_dims(rec) == ["scope"]
    assert derive_escalation_type_from_tiers(rec) == ["scope"]
    assert derive_escalation_family_from_tiers(rec) == "scope_overclaim"


def test_mixed_gap_case():
    """Multiple exceeded dimensions → multiple gap labels + mixed list."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 3, "action": 4, "certainty": 4},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    gaps = derive_gap_labels_from_tiers(rec)
    assert gaps == {"scope_missing", "causal_missing", "action_missing", "certainty_missing"}
    exceeded = derive_exceeded_dims(rec)
    assert set(exceeded) == {"scope", "causal", "action", "certainty"}
    # ocn-33 P0-2: List[str] of exceeded dims (order = canonical dim order)
    assert sorted(derive_escalation_type_from_tiers(rec)) == ["action", "causal", "certainty", "scope"]
    assert derive_escalation_family_from_tiers(rec) == "mixed_overclaim"


def test_claim_below_support_no_gap():
    """claim_tier < support_tier is NOT a gap (only claim > support counts)."""
    rec = {
        "claim_tiers": {"scope": 2, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    assert derive_gap_labels_from_tiers(rec) == set()
    assert derive_escalation_type_from_tiers(rec) == []
    assert derive_escalation_family_from_tiers(rec) == "supported"


def test_each_dimension_overclaim_type():
    """Each dimension alone produces its own [dim] + {dim}_overclaim."""
    for dim in ("scope", "causal", "action", "certainty"):
        ct = {"scope": 3, "causal": 2, "action": 2, "certainty": 3}
        st = {"scope": 3, "causal": 2, "action": 2, "certainty": 3}
        ct[dim] = ct[dim] + 1
        rec = {"claim_tiers": ct, "support_tiers": st}
        assert derive_escalation_type_from_tiers(rec) == [dim]
        assert derive_escalation_family_from_tiers(rec) == f"{dim}_overclaim"


def test_two_dim_mixed_escalation_type():
    """Two exceeded dims → ["scope", "action"] + mixed_overclaim."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 3, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    assert sorted(derive_escalation_type_from_tiers(rec)) == ["action", "scope"]
    assert derive_escalation_family_from_tiers(rec) == "mixed_overclaim"


def test_malformed_tiers_skipped_not_crash():
    """Malformed tier values are skipped, not raised."""
    rec = {
        "claim_tiers": {"scope": "bad", "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    # Should not raise; scope is skipped.
    assert derive_gap_labels_from_tiers(rec) == set()
    assert derive_escalation_type_from_tiers(rec) == []
    assert derive_escalation_family_from_tiers(rec) == "supported"


def test_missing_tiers_fields():
    """Missing tiers fields default to empty dict (no gaps)."""
    rec: dict = {}
    assert derive_gap_labels_from_tiers(rec) == set()
    assert derive_escalation_type_from_tiers(rec) == []
    assert derive_escalation_family_from_tiers(rec) == "supported"


def test_escalation_type_is_list_not_string():
    """ocn-33 P0-2: escalation_type must be a list, not a string."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_type_from_tiers(rec)
    assert isinstance(result, list)
    assert result == ["scope"]


def test_escalation_family_is_string():
    """ocn-33 P0-2: escalation_family must be a string summary."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    result = derive_escalation_family_from_tiers(rec)
    assert isinstance(result, str)
    assert result == "scope_overclaim"
