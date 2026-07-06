"""Tests for P2e: evidence-gap explanation and bounded rewrite."""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS, R_EXPERT
from cese.explain import (
    generate_evidence_gap_rationale,
    generate_bounded_rewrite,
    compute_evidence_gap_f1,
    check_rewrite_no_overclaim,
    generate_explanations,
)


def _make_inputs(B=2, D=4, E=8):
    """Make inputs with exceedance on action dim."""
    claim_tiers = torch.zeros(B, D, dtype=torch.long)
    support_tiers = torch.zeros(B, D, dtype=torch.long)
    # Sample 0: exceedance on action (claim=3, support=1)
    claim_tiers[0, CLAIM_DIMS.index("action")] = 3
    support_tiers[0, CLAIM_DIMS.index("action")] = 1
    # Sample 1: no exceedance
    claim_tiers[1] = 1
    support_tiers[1] = 1
    ev = torch.zeros(B, E)
    ec = torch.zeros(B, E)
    return claim_tiers, support_tiers, ev, ec


def test_generate_evidence_gap_rationale_finds_exceedance():
    claim_tiers, support_tiers, ev, ec = _make_inputs()
    rationales = generate_evidence_gap_rationale(
        claim_tiers, support_tiers, ev, ec,
    )
    assert len(rationales) == 2
    # Sample 0 should have action in exceedance_dims
    assert "action" in rationales[0]["exceedance_dims"]
    # Sample 1 should have no exceedance
    assert len(rationales[1]["exceedance_dims"]) == 0


def test_generate_evidence_gap_rationale_finds_missing_evidence():
    claim_tiers, support_tiers, ev, ec = _make_inputs()
    rationales = generate_evidence_gap_rationale(
        claim_tiers, support_tiers, ev, ec,
    )
    # Sample 0: action exceedance -> R(action) = [baseline_comparison,
    # coverage, risk_utility, deployment_constraints]
    # ev=0 for all -> all R(action) dims with value < 0.5 should be listed
    missing = rationales[0]["missing_evidence"]
    missing_names = {m["evidence_name"] for m in missing}
    # risk_utility is in base EVIDENCE_DIMS and R(action)
    assert "risk_utility" in missing_names
    assert "coverage" in missing_names


def test_generate_bounded_rewrite_no_exceedance():
    """When no exceedance, rewrite should equal original."""
    claim_text = "The model works well."
    claim_tiers = torch.tensor([1, 1, 1, 1])
    support_tiers = torch.tensor([1, 1, 1, 1])
    rewrite = generate_bounded_rewrite(claim_text, claim_tiers, support_tiers)
    assert rewrite == claim_text


def test_generate_bounded_rewrite_with_exceedance():
    """When exceedance, rewrite should prepend a hedge."""
    claim_text = "The model works well."
    claim_tiers = torch.tensor([1, 1, 3, 1])  # action=3
    support_tiers = torch.tensor([1, 1, 1, 1])  # action=1
    rewrite = generate_bounded_rewrite(claim_text, claim_tiers, support_tiers)
    assert rewrite != claim_text
    assert "not fully supported" in rewrite
    assert "action" in rewrite


def test_compute_evidence_gap_f1_perfect():
    pred = [{"a", "b"}, {"c"}]
    gold = [{"a", "b"}, {"c"}]
    f1 = compute_evidence_gap_f1(pred, gold)
    assert f1["precision"] == 1.0
    assert f1["recall"] == 1.0
    assert f1["f1"] == 1.0


def test_compute_evidence_gap_f1_partial():
    pred = [{"a"}, {"c"}]
    gold = [{"a", "b"}, {"c"}]
    f1 = compute_evidence_gap_f1(pred, gold)
    # tp=2 (a, c), fp=0, fn=1 (b)
    assert f1["precision"] == 1.0
    assert f1["recall"] == pytest.approx(2 / 3, abs=1e-6)
    assert f1["f1"] == pytest.approx(2 * 1.0 * (2 / 3) / (1.0 + 2 / 3), abs=1e-6)


def test_check_rewrite_no_overclaim_true():
    rewrite_tiers = torch.tensor([1, 1, 1, 1])
    support_tiers = torch.tensor([1, 1, 1, 1])
    assert check_rewrite_no_overclaim(rewrite_tiers, support_tiers) is True


def test_check_rewrite_no_overclaim_false():
    rewrite_tiers = torch.tensor([2, 1, 1, 1])
    support_tiers = torch.tensor([1, 1, 1, 1])
    assert check_rewrite_no_overclaim(rewrite_tiers, support_tiers) is False


def test_generate_explanations_full():
    B, D, E = 2, 4, 8
    claim_tiers, support_tiers, ev, ec = _make_inputs()
    claim_texts = ["claim 0", "claim 1"]
    sample_ids = ["s0", "s1"]
    gold_gaps = [{"risk_utility", "coverage"}, set()]
    results = generate_explanations(
        claim_texts, claim_tiers, support_tiers, ev, ec,
        sample_ids=sample_ids, gold_evidence_gaps=gold_gaps,
    )
    assert len(results) == 2
    assert results[0]["sample_id"] == "s0"
    assert "evidence_gap_rationale" in results[0]
    assert "bounded_rewrite_target" in results[0]
    assert "rewrite_no_overclaim" in results[0]
    assert "evidence_gap_f1" in results[0]
    # Sample 1 has no exceedance -> no rewrite
    assert results[1]["bounded_rewrite_target"] == "claim 1"
    assert results[1]["rewrite_no_overclaim"] is True


def test_generate_explanations_without_gold():
    B, D, E = 2, 4, 8
    claim_tiers, support_tiers, ev, ec = _make_inputs()
    claim_texts = ["claim 0", "claim 1"]
    results = generate_explanations(
        claim_texts, claim_tiers, support_tiers, ev, ec,
    )
    assert len(results) == 2
    # Without gold, evidence_gap_f1 should not be present
    assert "evidence_gap_f1" not in results[0]
