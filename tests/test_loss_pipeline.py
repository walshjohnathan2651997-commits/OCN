"""End-to-end loss pipeline test.

Verifies that the full CesEOcnLoss pipeline (ordinal + escalation + monotonicity
+ truncation + confidence_lower_bound) all enter the computation graph and
produce non-negative, differentiable losses when ``evidence_branch`` and
``calibrator`` are provided.

This test does NOT depend on ``transformers``: it uses the shared-threshold
calibrator and the vector evidence encoder directly, mirroring what
``CesEOcnModel.forward`` produces internally.
"""

from __future__ import annotations

import torch

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS, NUM_TIERS, R_EXPERT
from cese.losses import CesEOcnLoss
from cese.models.evidence_branch import VectorEvidenceEncoder
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator


def test_full_loss_pipeline_all_components_active():
    """All five loss components should be real tensors (not 0.0) when
    evidence_branch and calibrator are provided."""
    torch.manual_seed(0)
    B, D, K = 6, len(CLAIM_DIMS), NUM_TIERS
    calibrator = SharedThresholdCalibrator(num_tiers=K, num_dims=D)
    evidence_branch = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        num_dims=D,
    )
    loss_fn = CesEOcnLoss(
        num_tiers=K,
        ordinal_weight=1.0,
        escalation_weight=1.0,
        monotonicity_weight=0.1,
        truncation_weight=0.1,
        confidence_lower_bound_weight=0.05,
        mapping=dict(R_EXPERT),
    )

    theta_claim = torch.randn(B, D, requires_grad=True)
    theta_support = torch.randn(B, D, requires_grad=True)
    out = calibrator(theta_claim, theta_support)
    # Mimic CesEOcnModel.forward output shape.
    out["theta_claim"] = theta_claim
    out["theta_support"] = theta_support

    ev = torch.rand(B, len(EVIDENCE_DIMS))
    conf = torch.rand(B, len(EVIDENCE_DIMS))
    claim_tiers = torch.randint(0, K, (B, D))
    support_tiers = torch.randint(0, K, (B, D))
    esc_labels = torch.randint(0, 2, (B,))

    ld = loss_fn(
        outputs=out,
        claim_tiers=claim_tiers,
        support_tiers=support_tiers,
        escalation_labels=esc_labels,
        evidence_vector=ev,
        evidence_confidence=conf,
        claim_families=["descriptive"] * B,
        evidence_branch=evidence_branch,
        calibrator=calibrator,
    )

    # All five components should be real tensors.
    for key in ("total", "ordinal", "escalation", "monotonicity",
                "truncation", "confidence_lower_bound"):
        assert torch.is_tensor(ld[key]), f"{key} is not a tensor: {type(ld[key])}"
        assert ld[key].item() >= 0, f"{key} is negative: {ld[key].item()}"

    # monotonicity and CLB should be computed (not skipped -> not 0.0 scalar).
    assert torch.is_tensor(ld["monotonicity"])
    assert torch.is_tensor(ld["confidence_lower_bound"])

    # Backward pass should populate gradients on theta_claim / theta_support.
    ld["total"].backward()
    assert theta_claim.grad is not None
    assert theta_support.grad is not None
    # Gradients should be non-zero (loss actually flows through both branches).
    assert theta_claim.grad.abs().sum().item() > 0
    assert theta_support.grad.abs().sum().item() > 0


def test_full_loss_pipeline_skips_mono_clb_without_branch():
    """Without evidence_branch/calibrator, mono and CLB are skipped (0.0)."""
    torch.manual_seed(0)
    B, D, K = 4, len(CLAIM_DIMS), NUM_TIERS
    calibrator = SharedThresholdCalibrator(num_tiers=K, num_dims=D)
    loss_fn = CesEOcnLoss(
        num_tiers=K,
        monotonicity_weight=0.1,
        truncation_weight=0.1,
        confidence_lower_bound_weight=0.05,
        mapping=dict(R_EXPERT),
    )
    theta_claim = torch.randn(B, D, requires_grad=True)
    theta_support = torch.randn(B, D, requires_grad=True)
    out = calibrator(theta_claim, theta_support)
    out["theta_claim"] = theta_claim
    out["theta_support"] = theta_support
    ev = torch.rand(B, len(EVIDENCE_DIMS))
    conf = torch.rand(B, len(EVIDENCE_DIMS))

    ld = loss_fn(
        outputs=out,
        claim_tiers=torch.randint(0, K, (B, D)),
        support_tiers=torch.randint(0, K, (B, D)),
        escalation_labels=torch.randint(0, 2, (B,)),
        evidence_vector=ev,
        evidence_confidence=conf,
    )
    # mono and CLB skipped -> scalar 0.0
    assert ld["monotonicity"] == 0.0
    assert ld["confidence_lower_bound"] == 0.0
    # ordinal, escalation, truncation still computed.
    assert torch.is_tensor(ld["ordinal"])
    assert torch.is_tensor(ld["escalation"])
    assert torch.is_tensor(ld["truncation"])
    ld["total"].backward()
    assert theta_claim.grad is not None


def test_loss_pipeline_thresholds_arg_ignored():
    """The ``thresholds`` kwarg should be accepted and ignored (backward compat)."""
    torch.manual_seed(0)
    B, D, K = 4, len(CLAIM_DIMS), NUM_TIERS
    calibrator = SharedThresholdCalibrator(num_tiers=K, num_dims=D)
    loss_fn = CesEOcnLoss(num_tiers=K, mapping=dict(R_EXPERT))
    theta_claim = torch.randn(B, D)
    theta_support = torch.randn(B, D)
    out = calibrator(theta_claim, theta_support)
    out["theta_claim"] = theta_claim
    out["theta_support"] = theta_support
    ev = torch.rand(B, len(EVIDENCE_DIMS))
    conf = torch.rand(B, len(EVIDENCE_DIMS))

    # Should not raise even though thresholds is passed.
    ld = loss_fn(
        outputs=out,
        claim_tiers=torch.randint(0, K, (B, D)),
        support_tiers=torch.randint(0, K, (B, D)),
        escalation_labels=torch.randint(0, 2, (B,)),
        evidence_vector=ev,
        evidence_confidence=conf,
        thresholds=calibrator.get_thresholds(),
    )
    assert torch.is_tensor(ld["total"])
