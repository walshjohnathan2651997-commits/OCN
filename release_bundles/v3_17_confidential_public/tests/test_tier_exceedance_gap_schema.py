"""Tests for tier_exceedance_gap_labels schema validity (ocn-33 P2-7).

Verifies the ``tier_exceedance_gap_labels`` field conforms to its schema:
  * Must be a list of strings (or JSON-encoded list).
  * Each label must be of the form ``f"{dim}_missing"`` where ``dim`` is
    one of the canonical claim dimensions (scope/causal/action/certainty).
  * Empty list is valid (means supported, no tier exceeds).
  * Mixed gaps (multiple dimensions) are valid.
  * Unknown labels (e.g. ``coverage_missing`` which belongs to
    evidence_gap_labels) must be flagged as schema violations.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS

# Canonical tier-exceedance gap-label set.
_VALID_TIER_GAP_LABELS = {f"{d}_missing" for d in CLAIM_DIMS}


def _validate_tier_gap_labels(value) -> list:
    """Return a list of schema-violation messages (empty = valid)."""
    issues: list = []
    if value is None:
        return issues  # missing field is allowed (treated as empty)
    if isinstance(value, str):
        # Tolerate JSON-encoded list.
        import json
        try:
            value = json.loads(value)
        except Exception:
            issues.append(f"string value {value!r} is not JSON-encoded list")
            return issues
    if not isinstance(value, (list, tuple)):
        issues.append(f"expected list, got {type(value).__name__}")
        return issues
    for item in value:
        if not isinstance(item, str):
            issues.append(f"item {item!r} is not a string")
            continue
        if item not in _VALID_TIER_GAP_LABELS:
            issues.append(
                f"unknown label {item!r}; valid labels are "
                f"{sorted(_VALID_TIER_GAP_LABELS)}"
            )
    return issues


def test_empty_list_is_valid():
    """Empty list means supported (no tier exceeds) — valid."""
    assert _validate_tier_gap_labels([]) == []


def test_single_dim_gap_is_valid():
    """A single ``{dim}_missing`` label is valid."""
    for dim in CLAIM_DIMS:
        assert _validate_tier_gap_labels([f"{dim}_missing"]) == []


def test_mixed_gaps_are_valid():
    """Multiple gap labels (mixed overclaim) are valid."""
    labels = [f"{d}_missing" for d in CLAIM_DIMS]
    assert _validate_tier_gap_labels(labels) == []


def test_json_encoded_list_is_valid():
    """JSON-encoded list string is accepted (legacy CSV encoding)."""
    import json
    s = json.dumps(["scope_missing", "action_missing"])
    assert _validate_tier_gap_labels(s) == []


def test_unknown_label_is_flagged():
    """``coverage_missing`` belongs to evidence_gap_labels, not tier gap."""
    issues = _validate_tier_gap_labels(["scope_missing", "coverage_missing"])
    assert len(issues) == 1
    assert "coverage_missing" in issues[0]


def test_non_string_item_is_flagged():
    """Non-string items in the list are flagged."""
    issues = _validate_tier_gap_labels(["scope_missing", 42])
    assert len(issues) == 1
    assert "42" in issues[0]


def test_non_list_value_is_flagged():
    """A bare string or dict is flagged (must be a list)."""
    assert _validate_tier_gap_labels("scope_missing")  # not JSON list
    assert _validate_tier_gap_labels({"scope": 1})


def test_none_value_is_allowed():
    """None / missing field is treated as empty (no violation)."""
    assert _validate_tier_gap_labels(None) == []


def test_legacy_overclaim_string_is_flagged():
    """Legacy ``mixed_overclaim`` / ``scope_overclaim`` strings are flagged.

    ocn-33 P0-2: escalation_type / gap-labels must be List[str] of dims,
    never the legacy family-string encoding.
    """
    issues = _validate_tier_gap_labels("mixed_overclaim")
    assert issues
    issues = _validate_tier_gap_labels("scope_overclaim")
    assert issues


def test_clean_v2_data_passes_schema():
    """All records in data/clean_v2_all.jsonl pass the schema check."""
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
            issues = _validate_tier_gap_labels(rec.get("tier_exceedance_gap_labels"))
            assert issues == [], (
                f"schema violation in {rec.get('sample_id')}: {issues}"
            )
            n_checked += 1
    assert n_checked > 0, "no records checked"
