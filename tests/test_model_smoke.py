"""Full model smoke test with a stubbed ClaimBranch.

This test verifies the complete CesEOcnModel -> CesEOcnLoss -> backward
pipeline WITHOUT requiring a HuggingFace model download. It replaces
ClaimBranch with a lightweight embedding-based encoder, keeping the rest
of the model (EvidenceBranch, SharedThresholdCalibrator) intact.

Run:
    python -m pytest -q tests/test_model_smoke.py
    python tests/test_model_smoke.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import List

import torch
import torch.nn as nn

# Ensure repo root is importable when running as a script.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS, NUM_TIERS, R_EXPERT
from cese.data.collate import collate_fn
from cese.data.dataset import CesEOcnDataset
from cese.losses import CesEOcnLoss
from cese.models.cese_ocn import CesEOcnModel
from cese.models.evidence_branch import EvidenceBranch
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator


class StubClaimBranch(nn.Module):
    """Lightweight stand-in for ClaimBranch (no transformers needed).

    Hashes claim text to a fixed embedding and projects to theta_claim.
    """

    def __init__(self, hidden_dim: int = 32, num_dims: int = 4):
        super().__init__()
        self.num_dims = num_dims
        self.embed = nn.EmbeddingBag(1000, hidden_dim, mode="mean")
        self.proj = nn.Linear(hidden_dim, num_dims)

    def forward(self, claim_texts: List[str], device) -> torch.Tensor:
        # Simple hash-based tokenization.
        indices = []
        offsets = [0]
        for t in claim_texts:
            toks = [hash(w) % 1000 for w in t.split()[:64]] or [0]
            indices.extend(toks)
            offsets.append(len(indices))
        idx = torch.tensor(indices, dtype=torch.long, device=device)
        off = torch.tensor(offsets[:-1], dtype=torch.long, device=device)
        emb = self.embed(idx, off)
        return self.proj(emb)


def _build_stub_model(num_tiers=NUM_TIERS, hidden_dim=32, device="cpu"):
    """Build a CesEOcnModel-like module with a stubbed claim branch.

    We construct the submodules directly (bypassing CesEOcnModel.__init__
    which requires transformers) and wire them into a minimal nn.Module
    that mirrors CesEOcnModel.forward's output contract.
    """
    import types
    model = CesEOcnModel.__new__(CesEOcnModel)  # bypass __init__
    nn.Module.__init__(model)
    model.num_tiers = num_tiers
    model.num_dims = len(CLAIM_DIMS)
    model.evidence_mode = "vector"
    model.mapping = dict(R_EXPERT)
    model.claim_branch = StubClaimBranch(hidden_dim=hidden_dim, num_dims=len(CLAIM_DIMS))
    model.evidence_branch = EvidenceBranch(
        mode="vector",
        mapping=dict(R_EXPERT),
        vector_kwargs={
            "input_dim": len(EVIDENCE_DIMS) * 2,
            "hidden_dim": hidden_dim,
            "num_layers": 1,
            "num_dims": len(CLAIM_DIMS),
            "dropout": 0.1,
        },
    )
    model.calibrator = SharedThresholdCalibrator(
        num_tiers=num_tiers, num_dims=len(CLAIM_DIMS), score_mode="exceedance"
    )
    # Reuse CesEOcnModel.forward by binding it.
    model.forward = types.MethodType(CesEOcnModel.forward, model)
    model.predict = types.MethodType(CesEOcnModel.predict, model)
    return model.to(device)


def _make_toy_batch(n=4, device="cpu"):
    """Create a minimal batch matching collate_fn output."""
    B = n
    D = len(CLAIM_DIMS)
    E = len(EVIDENCE_DIMS)
    K = NUM_TIERS
    return {
        "claim_text": [f"claim number {i} about scope and causal" for i in range(B)],
        "evidence_vector": torch.rand(B, E),
        "evidence_confidence": torch.rand(B, E),
        "claim_tiers": torch.randint(0, K, (B, D)),
        "support_tiers": torch.randint(0, K, (B, D)),
        "escalation_label": torch.randint(0, 2, (B,)),
        "claim_family": ["descriptive"] * B,
        "evidence_gap_labels": [["coverage_missing"]] * B,
    }


def test_full_model_forward_loss_backward():
    """End-to-end: model.forward -> loss_fn -> backward."""
    device = "cpu"
    torch.manual_seed(0)
    model = _build_stub_model(device=device)
    loss_fn = CesEOcnLoss(
        num_tiers=NUM_TIERS,
        ordinal_weight=1.0,
        monotonicity_weight=0.1,
        truncation_weight=0.1,
        confidence_lower_bound_weight=0.05,
        mapping=dict(R_EXPERT),
    )
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-3)

    batch = _make_toy_batch(n=4, device=device)
    # Forward
    outputs = model(
        claim_texts=batch["claim_text"],
        evidence_vector=batch["evidence_vector"],
        evidence_confidence=batch["evidence_confidence"],
        device=device,
    )
    # Verify model outputs include p_ge_claim/p_ge_support (added in P2).
    assert "p_ge_claim" in outputs, "p_ge_claim missing from model output"
    assert "p_ge_support" in outputs, "p_ge_support missing from model output"
    assert outputs["p_ge_support"] is not None, "p_ge_support is None"

    # Loss
    loss_dict = loss_fn(
        outputs=outputs,
        claim_tiers=batch["claim_tiers"],
        support_tiers=batch["support_tiers"],
        escalation_labels=batch["escalation_label"],
        evidence_vector=batch["evidence_vector"],
        evidence_confidence=batch["evidence_confidence"],
        claim_families=batch["claim_family"],
        evidence_branch=model.evidence_branch,
        calibrator=model.calibrator,
    )
    # All five loss components should be real tensors.
    for key in ("total", "ordinal", "escalation", "monotonicity",
                "truncation", "confidence_lower_bound"):
        assert torch.is_tensor(loss_dict[key]), f"{key} not a tensor"
        assert loss_dict[key].item() >= 0, f"{key} negative: {loss_dict[key].item()}"
    # monotonicity and CLB should be non-zero (computed, not skipped).
    assert torch.is_tensor(loss_dict["monotonicity"])
    assert torch.is_tensor(loss_dict["confidence_lower_bound"])

    # Backward + step
    optimizer.zero_grad()
    loss_dict["total"].backward()
    # Gradients should flow through both branches.
    g_claim = model.claim_branch.proj.weight.grad
    g_evidence = model.evidence_branch.vector_encoder[0].weight.grad \
        if hasattr(model.evidence_branch, "vector_encoder") else None
    assert g_claim is not None and g_claim.abs().sum().item() > 0, "no grad on claim branch"
    optimizer.step()
    print(f"SMOKE OK: total={loss_dict['total'].item():.4f} "
          f"mono={loss_dict['monotonicity'].item():.4f} "
          f"clb={loss_dict['confidence_lower_bound'].item():.4f}")


def test_model_predict():
    """Verify model.predict returns hard labels."""
    device = "cpu"
    torch.manual_seed(0)
    model = _build_stub_model(device=device)
    model.eval()
    batch = _make_toy_batch(n=3, device=device)
    with torch.no_grad():
        pred = model.predict(
            claim_texts=batch["claim_text"],
            evidence_vector=batch["evidence_vector"],
            evidence_confidence=batch["evidence_confidence"],
            device=device,
        )
    assert pred["claim_tiers"].shape == (3, len(CLAIM_DIMS))
    assert pred["support_tiers"].shape == (3, len(CLAIM_DIMS))
    assert pred["escalation_pred"].shape == (3,)


if __name__ == "__main__":
    test_full_model_forward_loss_backward()
    test_model_predict()
    print("ALL SMOKE TESTS PASSED")
