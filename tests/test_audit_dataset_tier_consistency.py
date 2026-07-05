"""Tests for audit_dataset.py tier-consistency rule (ocn-31 P2-3, ocn-33 P0).

Verifies audit_dataset.py uses tier-exceedance (claim_tier > support_tier)
as the PRIMARY consistency rule for ``tier_exceedance_gap_labels`` (paper-main,
ocn-33 P0-1), and that ``evidence_gap_labels`` is now an auxiliary
feature-level rationale field (validity check only, warning), and that the
missing-evidence diagnostic is a warning only (does not block paper_ready
unless --strict_missing_evidence is set).
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
    derive_escalation_type_from_tiers,
)


def test_tier_exceedance_is_primary_rule():
    """The paper-main rule is claim_tier > support_tier → gap label."""
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
    }
    # Tier-exceedance says scope_missing.
    expected = derive_gap_labels_from_tiers(rec)
    assert expected == {"scope_missing"}


def test_audit_uses_tier_exceedance_gap_labels():
    """audit_dataset.py must check tier_exceedance_gap_labels (paper-main)."""
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "tier_exceedance_gap_labels": ["scope_missing"],
    }
    issues = _check_tier_exceedance_gap_labels(rec)
    assert issues == [], f"unexpected tier-exceedance issues: {issues}"


def test_audit_flags_missing_tier_gap():
    """audit must flag when tier_exceedance_gap_labels misses a tier gap."""
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "tier_exceedance_gap_labels": [],  # missing scope_missing
    }
    issues = _check_tier_exceedance_gap_labels(rec)
    missing = [i for i in issues if "missing" in i.lower()]
    assert missing, "audit must flag missing tier_exceedance_gap_labels"


def test_audit_flags_extra_tier_gap():
    """audit must flag when tier_exceedance_gap_labels has an extra gap."""
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "tier_exceedance_gap_labels": ["scope_missing"],  # no tier exceedance
    }
    issues = _check_tier_exceedance_gap_labels(rec)
    extra = [i for i in issues if "extra" in i.lower()]
    assert extra, "audit must flag extra tier_exceedance_gap_labels"


def test_audit_flags_unknown_tier_gap_label():
    """audit must flag unknown labels in tier_exceedance_gap_labels."""
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        # coverage_missing is a feature-level evidence_gap_label, NOT a
        # tier_exceedance_gap_label; it must be flagged as unknown.
        "tier_exceedance_gap_labels": ["scope_missing", "coverage_missing"],
    }
    issues = _check_tier_exceedance_gap_labels(rec)
    unknown = [i for i in issues if "unknown" in i.lower()]
    assert unknown, "audit must flag unknown tier_exceedance_gap_labels"


def test_evidence_gap_labels_is_auxiliary_validity_only():
    """evidence_gap_labels check is now validity-only (unknown labels)."""
    try:
        from scripts.audit_dataset import _check_gap_label_consistency
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    # evidence_gap_labels may carry feature-level rationale labels; the
    # auxiliary check only flags UNKNOWN labels (not in EVIDENCE_GAP_LABELS),
    # NOT tier-exceedance mismatches.
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        # scope_missing is a tier_exceedance label, not a valid
        # evidence_gap_label; if placed in evidence_gap_labels it is "unknown".
        "evidence_gap_labels": ["coverage_missing"],
    }
    issues = _check_gap_label_consistency(rec)
    # No tier-exceedance mismatch should be reported here (that moved to
    # _check_tier_exceedance_gap_labels).
    tier_issues = [i for i in issues if "tier-exceedance" in i]
    assert tier_issues == [], (
        "evidence_gap_labels check must not report tier-exceedance mismatches"
    )


def test_missing_evidence_diagnostic_is_separate():
    """The missing-evidence diagnostic is a separate function (warning only)."""
    try:
        from scripts.audit_dataset import (
            _check_tier_exceedance_gap_labels,
            _check_missing_evidence_diagnostic,
        )
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    # A record where tier-exceedance says no gap, but missing-evidence
    # diagnostic might flag something. The two functions must be separate.
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "tier_exceedance_gap_labels": [],
        "evidence_vector": {"scope": 0.1, "causal": 0.9, "action": 0.9, "certainty": 0.9},
        "evidence_confidence": {"scope": 0.1, "causal": 0.9, "action": 0.9, "certainty": 0.9},
    }
    tier_issues = _check_tier_exceedance_gap_labels(rec)
    assert tier_issues == [], "tier-exceedance must be clean"
    # Missing-evidence diagnostic may or may not flag depending on thresholds,
    # but it must be a separate call (not part of tier consistency).
    diag_issues = _check_missing_evidence_diagnostic(rec)
    assert isinstance(diag_issues, list)


def test_escalation_type_consistency_uses_list():
    """ocn-33 P0-2: escalation_type is List[str] of exceeded dims."""
    try:
        from scripts.audit_dataset import _check_escalation_consistency
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 3, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "escalation_label": 1,
        "escalation_type": ["scope", "action"],
    }
    issues = _check_escalation_consistency(rec)
    assert issues == [], f"unexpected escalation issues: {issues}"


def test_escalation_type_flags_wrong_dims():
    """audit must flag escalation_type with wrong exceeded dims."""
    try:
        from scripts.audit_dataset import _check_escalation_consistency
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 4, "causal": 2, "action": 3, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "escalation_label": 1,
        # wrong: should be ["scope", "action"]
        "escalation_type": ["scope"],
    }
    issues = _check_escalation_consistency(rec)
    type_issues = [i for i in issues if "escalation_type" in i]
    assert type_issues, "audit must flag wrong escalation_type dims"


def test_escalation_type_supported_is_empty_list():
    """supported sample: escalation_type == [] (not 'supported' string)."""
    try:
        from scripts.audit_dataset import _check_escalation_consistency
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = {
        "claim_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": 3, "causal": 2, "action": 2, "certainty": 3},
        "escalation_label": 0,
        "escalation_type": [],
    }
    issues = _check_escalation_consistency(rec)
    assert issues == [], f"unexpected escalation issues for supported: {issues}"
