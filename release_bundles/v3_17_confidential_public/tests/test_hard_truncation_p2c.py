"""Tests for P2c: hard truncation with deployment_constraints and route_review.

Verifies:
- Action cap triggers when deployment_constraints is missing (extended dim).
- Certainty cap triggers when variance_seeds is missing (extended dim).
- Inference modes: none, soft_gate, hard_renormalize, route_review.
- route_review flags samples with violations and returns reviewed_sample_ids.
- Report includes trigger_rate, violation_before/after, review_rate.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS, NUM_TIERS
from cese.losses.truncation import compute_max_support_tiers, apply_strict_cap
from cese.models.inference_constraints import apply_inference_truncation


def _make_inputs(B=4, D=4, K=5, ev_dim=8):
    """Make random inputs for truncation tests."""
    torch.manual_seed(42)
    claim_probs = torch.softmax(torch.randn(B, D, K), dim=-1)
    support_probs = torch.softmax(torch.randn(B, D, K), dim=-1)
    ev = torch.rand(B, ev_dim)
    ec = torch.rand(B, ev_dim)
    return claim_probs, support_probs, ev, ec


def test_action_cap_triggers_on_low_risk_utility():
    """Action cap should trigger when risk_utility is low and claim_tiers[action] >= 3."""
    ev = torch.zeros(1, 8)  # all evidence = 0
    ec = torch.zeros(1, 8)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])  # action tier = 3
    max_tiers = compute_max_support_tiers(ev, ec, claim_tiers, cap_tier=2)
    # action is index 2 in CLAIM_DIMS = [scope, causal, action, certainty]
    action_idx = CLAIM_DIMS.index("action")
    assert max_tiers[0, action_idx] == 2  # capped


def test_certainty_cap_triggers_on_low_uncertainty():
    """Certainty cap should trigger when uncertainty is low and claim_tiers[certainty] >= 3."""
    ev = torch.zeros(1, 8)
    ec = torch.zeros(1, 8)
    claim_tiers = torch.tensor([[0, 0, 0, 3]])  # certainty tier = 3
    max_tiers = compute_max_support_tiers(ev, ec, claim_tiers, cap_tier=2)
    certainty_idx = CLAIM_DIMS.index("certainty")
    assert max_tiers[0, certainty_idx] == 2  # capped


def test_inference_mode_none_does_not_cap():
    """none mode should return original support_probs (no truncation)."""
    claim_probs, support_probs, ev, ec = _make_inputs()
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec, mode="none"
    )
    assert torch.equal(result["support_probs_capped"], support_probs)


def test_inference_mode_soft_gate_does_not_cap():
    """soft_gate mode should return original support_probs."""
    claim_probs, support_probs, ev, ec = _make_inputs()
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec, mode="soft_gate"
    )
    assert torch.equal(result["support_probs_capped"], support_probs)


def test_inference_mode_hard_renormalize_caps():
    """hard_renormalize should change support_probs when cap triggers."""
    # Force a violation: high support tier with low evidence.
    B, D, K = 2, 4, 5
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, :, 3] = 1.0  # claim tier = 3 (triggers action/certainty cap)
    support_probs = torch.zeros(B, D, K)
    support_probs[:, :, 4] = 1.0  # support tier = 4 (above cap_tier=2)
    ev = torch.zeros(B, 8)  # all evidence missing
    ec = torch.zeros(B, 8)
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec, mode="hard_renormalize", cap_tier=2
    )
    # After capping, support tiers should be <= 2 on capped dims
    # (causal, action, certainty). Scope is NOT capped by the rules.
    capped_tiers = result["support_probs_capped"].argmax(dim=-1)
    causal_idx = CLAIM_DIMS.index("causal")
    action_idx = CLAIM_DIMS.index("action")
    certainty_idx = CLAIM_DIMS.index("certainty")
    assert (capped_tiers[:, causal_idx] <= 2).all()
    assert (capped_tiers[:, action_idx] <= 2).all()
    assert (capped_tiers[:, certainty_idx] <= 2).all()
    # violation_before should be True (tier 4 > cap 2 on capped dims).
    assert result["violation_before"].all()
    # violation_after should be False on capped dims.
    assert not result["violation_after"].any()


def test_route_review_flags_violations():
    """route_review mode should flag samples with violations."""
    B, D, K = 3, 4, 5
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, :, 3] = 1.0
    support_probs = torch.zeros(B, D, K)
    # Sample 0: violation (tier 4 > cap 2)
    support_probs[0, :, 4] = 1.0
    # Sample 1: no violation (tier 1 <= cap 2)
    support_probs[1, :, 1] = 1.0
    # Sample 2: violation (tier 4 > cap 2)
    support_probs[2, :, 4] = 1.0
    ev = torch.zeros(B, 8)
    ec = torch.zeros(B, 8)
    sample_ids = ["s0", "s1", "s2"]
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec,
        mode="route_review", cap_tier=2, sample_ids=sample_ids,
    )
    # Samples 0 and 2 should be flagged.
    assert result["review_flags"][0].item() is True
    assert result["review_flags"][1].item() is False
    assert result["review_flags"][2].item() is True
    assert result["reviewed_sample_ids"] == ["s0", "s2"]
    assert result["review_rate"] > 0.0


def test_trigger_rate_reported():
    """Result should include trigger_rate (fraction of samples with any cap)."""
    claim_probs, support_probs, ev, ec = _make_inputs()
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec, mode="hard_renormalize"
    )
    assert "trigger_rate" in result
    assert isinstance(result["trigger_rate"], float)
    assert 0.0 <= result["trigger_rate"] <= 1.0


def test_violation_before_and_after_reported():
    """Result should include violation_before and violation_after tensors."""
    claim_probs, support_probs, ev, ec = _make_inputs()
    result = apply_inference_truncation(
        claim_probs, support_probs, ev, ec, mode="hard_renormalize"
    )
    assert "violation_before" in result
    assert "violation_after" in result
    assert result["violation_before"].shape == (claim_probs.size(0),)
    assert result["violation_after"].shape == (claim_probs.size(0),)
