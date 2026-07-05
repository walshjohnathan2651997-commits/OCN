"""Tests that audit uses tier_exceedance_gap_labels as primary, not
evidence_gap_labels (ocn-33 P2-7).

Constructs a sample where:
  * ``tier_exceedance_gap_labels`` is correct (matches tier-derived gaps).
  * ``evidence_gap_labels`` differs from the feature-warning diagnostic.

The audit's PRIMARY tier-consistency check must PASS; only a warning may
be emitted from the auxiliary feature-level diagnostic.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.utils.labels import derive_gap_labels_from_tiers


def _make_split_sample(
    *,
    sample_id: str = "s1",
    claim_scope: int = 4,
    support_scope: int = 3,
    tier_gap_labels: list = None,
    evidence_gap_labels: list = None,
) -> dict:
    """Build a single record with controllable tier/evidence gap fields."""
    if tier_gap_labels is None:
        # Default to the correct derived labels.
        rec_temp = {
            "claim_tiers": {"scope": claim_scope, "causal": 2, "action": 2, "certainty": 3},
            "support_tiers": {"scope": support_scope, "causal": 2, "action": 2, "certainty": 3},
        }
        tier_gap_labels = sorted(derive_gap_labels_from_tiers(rec_temp))
    if evidence_gap_labels is None:
        # Default to a DIFFERENT label set (feature-level rationale).
        evidence_gap_labels = ["coverage_missing", "boundary_missing"]
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "split": "test",
        "domain": "cyber_defense",
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_tiers": {"scope": claim_scope, "causal": 2, "action": 2, "certainty": 3},
        "support_tiers": {"scope": support_scope, "causal": 2, "action": 2, "certainty": 3},
        "contradiction_label": 0,
        "escalation_label": 1 if claim_scope > support_scope else 0,
        "escalation_type": ["scope"] if claim_scope > support_scope else [],
        "tier_exceedance_gap_labels": tier_gap_labels,
        "evidence_gap_labels": evidence_gap_labels,
        "annotation": {"is_human_audited": False, "annotators": ["ai"]},
    }


def test_audit_primary_check_passes_when_tier_gap_correct():
    """Tier-exceedance primary check passes when tier_gap_labels matches."""
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = _make_split_sample(
        claim_scope=4, support_scope=3,
        tier_gap_labels=["scope_missing"],
        evidence_gap_labels=["coverage_missing", "boundary_missing"],
    )
    issues = _check_tier_exceedance_gap_labels(rec)
    assert issues == [], (
        f"primary tier-consistency should pass but got: {issues}"
    )


def test_audit_primary_check_does_not_inspect_evidence_gap_labels():
    """The primary check ignores evidence_gap_labels entirely.

    Even if evidence_gap_labels carries tier-style labels (which is wrong
    for that field), the primary tier-consistency check on
    tier_exceedance_gap_labels must still pass when tier_gap is correct.
    """
    try:
        from scripts.audit_dataset import _check_tier_exceedance_gap_labels
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = _make_split_sample(
        claim_scope=4, support_scope=3,
        tier_gap_labels=["scope_missing"],
        # Deliberately put DIFFERENT labels in evidence_gap_labels — the
        # primary tier check must not look at this field.
        evidence_gap_labels=["coverage_missing", "uncertainty_missing"],
    )
    issues = _check_tier_exceedance_gap_labels(rec)
    assert issues == [], (
        f"primary check should not inspect evidence_gap_labels: {issues}"
    )


def test_audit_evidence_gap_check_is_warning_only():
    """The evidence_gap_labels check is validity-only (unknown labels),
    not a tier-exceedance mismatch check. A mismatch between
    evidence_gap_labels and the feature-warning diagnostic must NOT
    produce a tier-exceedance error."""
    try:
        from scripts.audit_dataset import _check_gap_label_consistency
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = _make_split_sample(
        claim_scope=4, support_scope=3,
        tier_gap_labels=["scope_missing"],
        # evidence_gap_labels deliberately does NOT match the
        # feature-warning diagnostic (low evidence value + low confidence).
        # The auxiliary check should only flag UNKNOWN labels, not
        # tier-exceedance mismatches.
        evidence_gap_labels=["coverage_missing"],
    )
    issues = _check_gap_label_consistency(rec)
    tier_issues = [i for i in issues if "tier-exceedance" in i.lower()]
    assert tier_issues == [], (
        "evidence_gap_labels check must not report tier-exceedance "
        f"mismatches: {tier_issues}"
    )


def test_audit_emits_warning_not_error_when_evidence_gap_differs():
    """End-to-end: full audit runs without crashing; primary check passes.

    Build a record where:
      * tier_exceedance_gap_labels is CORRECT (passes primary check).
      * evidence_gap_labels differs from the missing-evidence diagnostic.
    The audit must NOT raise and must NOT block on the tier check.
    """
    try:
        from scripts.audit_dataset import audit
    except ImportError:
        pytest.skip("audit_dataset not importable in this env")
    rec = _make_split_sample(
        claim_scope=4, support_scope=3,
        tier_gap_labels=["scope_missing"],
        # evidence_gap_labels is empty (does not match the feature warning
        # which would flag scope_missing). This is allowed: evidence_gap
        # is auxiliary, not the paper-main label.
        evidence_gap_labels=[],
        # Add evidence vector/confidence so the missing-evidence diagnostic
        # has something to compute. Low values trigger the diagnostic.
    )
    rec["evidence_vector"] = {"scope": 0.1, "causal": 0.9, "action": 0.9, "certainty": 0.9}
    rec["evidence_confidence"] = {"scope": 0.1, "causal": 0.9, "action": 0.9, "certainty": 0.9}
    report = audit([rec])
    # The audit must complete and return a report dict.
    assert isinstance(report, dict)
    # Primary tier-exceedance issues must be empty for this record.
    # Look for any issue mentioning the sample_id + tier-exceedance.
    all_issues = []
    if isinstance(report.get("issues"), list):
        all_issues = report["issues"]
    elif isinstance(report.get("records"), list):
        for r in report["records"]:
            if isinstance(r, dict) and r.get("sample_id") == rec["sample_id"]:
                all_issues = r.get("issues", [])
    tier_blockers = [
        i for i in all_issues
        if isinstance(i, str)
        and "tier_exceedance" in i.lower()
        and ("missing" in i.lower() or "extra" in i.lower())
        and rec["sample_id"] in i
    ]
    assert tier_blockers == [], (
        f"primary tier check should pass for {rec['sample_id']}: {tier_blockers}"
    )
