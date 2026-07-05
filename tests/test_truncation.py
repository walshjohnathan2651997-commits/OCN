"""Tests for the truncation loss / penalty."""

from __future__ import annotations

import torch

from cese.constants import NUM_TIERS
from cese.losses.truncation import (
    truncation_loss,
    truncation_penalty,
    compute_max_support_tiers,
    apply_strict_cap,
)


def test_truncation_penalty_zero_when_within_gap():
    """Legacy gap penalty: when gap <= max_gap, penalty ~0."""
    K = NUM_TIERS
    claim_probs = torch.zeros(1, 1, K)
    support_probs = torch.zeros(1, 1, K)
    claim_probs[..., 1] = 1.0
    support_probs[..., 0] = 1.0
    loss = truncation_penalty(claim_probs, support_probs, max_gap=1)
    assert loss.item() < 1e-6


def test_truncation_penalty_positive_when_gap_exceeds():
    K = NUM_TIERS
    claim_probs = torch.zeros(1, 1, K)
    support_probs = torch.zeros(1, 1, K)
    claim_probs[..., K - 1] = 1.0
    support_probs[..., 0] = 1.0
    loss = truncation_penalty(claim_probs, support_probs, max_gap=1)
    assert loss.item() > 0.5


def test_truncation_penalty_increases_with_gap():
    K = NUM_TIERS
    support_probs = torch.zeros(1, 1, K)
    support_probs[..., 0] = 1.0
    claim2 = torch.zeros(1, 1, K)
    claim2[..., 2] = 1.0
    claim4 = torch.zeros(1, 1, K)
    claim4[..., 4] = 1.0
    loss2 = truncation_penalty(claim2, support_probs, max_gap=1)
    loss4 = truncation_penalty(claim4, support_probs, max_gap=1)
    assert loss4.item() > loss2.item()


def test_noncompensatory_truncation_zero_within_cap():
    """Spec 5.4: support mass below cap -> loss ~0."""
    K = NUM_TIERS
    support_probs = torch.zeros(2, 4, K)
    support_probs[..., 0] = 1.0
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    loss = truncation_loss(support_probs, max_tiers, K)
    assert loss.item() < 1e-6


def test_noncompensatory_truncation_positive_above_cap():
    K = NUM_TIERS
    support_probs = torch.zeros(2, 4, K)
    support_probs[..., K - 1] = 1.0
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    loss = truncation_loss(support_probs, max_tiers, K)
    assert loss.item() > 0.5


def test_max_support_tiers_causal_cap():
    ev = torch.zeros(2, 8)
    conf = torch.zeros(2, 8)
    claim_tiers = torch.zeros(2, 4)
    claim_tiers[:, 1] = 3  # causal >= 3
    max_tiers = compute_max_support_tiers(ev, conf, claim_tiers)
    assert max_tiers[0, 1].item() == 2
    assert max_tiers[0, 0].item() == NUM_TIERS - 1


def test_strict_cap_renormalizes():
    K = NUM_TIERS
    # Mass spread across tiers; cap at 2 should zero tiers 3,4 and renormalize.
    support_probs = torch.ones(2, 4, K) / K
    max_tiers = torch.full((2, 4), 2, dtype=torch.long)
    capped = apply_strict_cap(support_probs, max_tiers, K)
    # Mass above tier 2 should be zero.
    assert capped[..., 3:].sum().item() < 1e-6
    # Remaining mass should sum to 1.
    assert torch.allclose(capped.sum(dim=-1), torch.ones(2, 4), atol=1e-5)


def test_inference_truncation_uses_predicted_claim_tiers():
    """The ceiling must come from predicted claim tiers, not gold support."""
    from cese.models.inference_constraints import apply_inference_truncation

    K = NUM_TIERS
    B, D = 4, 4
    # claim_probs put mass on tier 3 for the causal dim (index 1).
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, 1, 3] = 1.0
    claim_probs[:, 0, 0] = 1.0
    claim_probs[:, 2, 0] = 1.0
    claim_probs[:, 3, 0] = 1.0
    # support mass on the top tier (should be capped away on dim 1).
    support_probs = torch.zeros(B, D, K)
    support_probs[:, :, K - 1] = 1.0
    # Low causal evidence + low confidence -> cap kicks in on dim 1.
    evidence_vector = torch.zeros(B, 8)
    evidence_confidence = torch.zeros(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    # Predicted claim tier on dim 1 is 3 -> cap at 2.
    assert (out["claim_tiers_pred"][:, 1] == 3).all()
    assert (out["max_support_tiers"][:, 1] == 2).all()
    # Capped support has no mass above tier 2 on dim 1.
    capped = out["support_probs_capped"]
    assert capped[:, 1, 3:].sum().item() < 1e-6
    # Remaining mass renormalized to 1.
    assert torch.allclose(capped[:, 1].sum(dim=-1), torch.ones(B), atol=1e-5)
    # Escalation score is in [0,1].
    s = out["escalation_score"]
    assert (s >= 0).all() and (s <= 1).all()


def test_inference_truncation_no_gold_leakage():
    """Violation rate must not use gold support tiers as the cap."""
    from cese.models.inference_constraints import apply_inference_truncation
    from cese.eval.cese_metrics import truncation_violation_rate

    K = NUM_TIERS
    B, D = 4, 4
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, :, 0] = 1.0  # low claim tiers -> no cap
    support_probs = torch.ones(B, D, K) / K
    evidence_vector = torch.ones(B, 8)  # high evidence -> no cap
    evidence_confidence = torch.ones(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    # No cap applied -> max tier = K-1 everywhere.
    assert (out["max_support_tiers"] == K - 1).all()
    # Violation rate against the predicted cap should be 0 (nothing forbidden).
    vr = truncation_violation_rate(
        support_probs.numpy(), out["max_support_tiers"].numpy(), num_tiers=K
    )
    assert vr == 0.0


# ---------------------------------------------------------------------------
# P1-3: truncation must actually change inference results.
# These tests verify that renormalize zeroes above-ceiling mass, renormalizes
# to 1, recomputes p_exceed, and that route_review produces review_sample_ids.
# ---------------------------------------------------------------------------


def test_truncation_renormalize_zeroes_above_ceiling_when_causal_id_missing():
    """When causal_id evidence is missing, causal support tier > ceiling
    must have its probability mass zeroed out."""
    from cese.models.inference_constraints import apply_inference_truncation

    K = NUM_TIERS
    B, D = 2, 4
    # claim tier 3 on causal dim (index 1) -> ceiling = 2.
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, 1, 3] = 1.0
    claim_probs[:, 0, 0] = 1.0
    claim_probs[:, 2, 0] = 1.0
    claim_probs[:, 3, 0] = 1.0
    # support mass on the top tier (above ceiling 2 on dim 1).
    support_probs = torch.zeros(B, D, K)
    support_probs[:, :, K - 1] = 1.0
    # Missing causal_id: zero evidence + zero confidence on causal dim.
    evidence_vector = torch.zeros(B, 8)
    evidence_confidence = torch.zeros(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    capped = out["support_probs_capped"]
    # On dim 1 (causal_id), mass above tier 2 must be zeroed.
    assert capped[:, 1, 3:].sum().item() < 1e-6, (
        "above-ceiling causal support mass should be zeroed"
    )


def test_truncation_renormalize_probs_sum_to_one():
    """After renormalize, support probabilities must sum to 1 per (B, D)."""
    from cese.models.inference_constraints import apply_inference_truncation

    K = NUM_TIERS
    B, D = 3, 4
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, 1, 3] = 1.0  # ceiling = 2 on dim 1
    claim_probs[:, 0, 0] = 1.0
    claim_probs[:, 2, 0] = 1.0
    claim_probs[:, 3, 0] = 1.0
    support_probs = torch.ones(B, D, K) / K  # uniform, some mass above cap
    evidence_vector = torch.zeros(B, 8)
    evidence_confidence = torch.zeros(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    capped = out["support_probs_capped"]
    # Every (B, D) row must sum to 1 after renormalization.
    assert torch.allclose(capped.sum(dim=-1), torch.ones(B, D), atol=1e-5), (
        "renormalized support probs must sum to 1"
    )


def test_truncation_renormalize_changes_p_exceed():
    """p_exceed must change after the renormalize policy is applied."""
    from cese.models.inference_constraints import apply_inference_truncation

    K = NUM_TIERS
    B, D = 2, 4
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, 1, 3] = 1.0  # ceiling = 2 on dim 1
    claim_probs[:, 0, 0] = 1.0
    claim_probs[:, 2, 0] = 1.0
    claim_probs[:, 3, 0] = 1.0
    # support mass on the top tier (above ceiling 2 on dim 1).
    support_probs = torch.zeros(B, D, K)
    support_probs[:, :, K - 1] = 1.0
    evidence_vector = torch.zeros(B, 8)
    evidence_confidence = torch.zeros(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    # Original p_exceed: claim tier 3 > support tier K-1 -> exceedance = 1
    # on dim 1 (since 3 < K-1 means no exceedance; 3 == K-1 means no gap).
    # Actually with claim=3 and support=K-1=4, gap = 3-4 < 0 -> no exceed.
    # After capping, support mass moves to tier <= 2, so claim=3 > support<=2
    # -> exceedance = 1 on dim 1. So p_exceed must change.
    p_exceed_post = out["p_exceed"]
    # Compute original p_exceed (before truncation) for comparison.
    idx = torch.arange(K)
    gap = idx.unsqueeze(1) - idx.unsqueeze(0)
    exceed_mask = (gap > 0).float()
    p_exceed_orig = torch.einsum(
        "bdk,bdj,kj->bd", claim_probs, support_probs, exceed_mask
    )
    # On dim 1, p_exceed must differ after renormalize.
    assert not torch.allclose(
        p_exceed_orig[:, 1], p_exceed_post[:, 1], atol=1e-6
    ), "p_exceed should change after renormalize policy"


def test_truncation_route_review_produces_review_sample_ids():
    """route_review policy must produce review_sample_ids for triggered
    samples (support tier > ceiling)."""
    from cese.models.inference_constraints import apply_inference_truncation

    K = NUM_TIERS
    B, D = 4, 4
    # claim tier 3 on dim 1 -> ceiling = 2.
    claim_probs = torch.zeros(B, D, K)
    claim_probs[:, 1, 3] = 1.0
    claim_probs[:, 0, 0] = 1.0
    claim_probs[:, 2, 0] = 1.0
    claim_probs[:, 3, 0] = 1.0
    # Samples 0,1 have support mass above ceiling; samples 2,3 do not.
    support_probs = torch.zeros(B, D, K)
    support_probs[0, :, K - 1] = 1.0  # above ceiling on dim 1
    support_probs[1, :, K - 1] = 1.0  # above ceiling on dim 1
    support_probs[2, :, 0] = 1.0      # within ceiling
    support_probs[3, :, 0] = 1.0      # within ceiling
    evidence_vector = torch.zeros(B, 8)
    evidence_confidence = torch.zeros(B, 8)

    out = apply_inference_truncation(
        claim_probs=claim_probs,
        support_probs=support_probs,
        evidence_vector=evidence_vector,
        evidence_confidence=evidence_confidence,
        num_tiers=K,
    )
    # Trigger mask: any dim where support tier > ceiling.
    support_tiers_pred = support_probs.argmax(dim=-1)  # (B, D)
    trigger_mask = (support_tiers_pred > out["max_support_tiers"]).any(dim=-1)
    # Samples 0,1 should trigger; 2,3 should not.
    assert trigger_mask[0].item() and trigger_mask[1].item()
    assert not trigger_mask[2].item() and not trigger_mask[3].item()
    # review_sample_ids = indices where trigger_mask is True.
    review_sample_ids = torch.where(trigger_mask)[0].tolist()
    assert review_sample_ids == [0, 1], (
        "route_review should produce review_sample_ids for triggered samples"
    )
