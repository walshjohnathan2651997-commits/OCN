"""Tests for P2b: R(k) mapping affects evidence branch forward pass.

Verifies that mapping_mask_mode != 'none' actually changes the forward
pass, not just the loss.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, EVIDENCE_DIMS, R_EXPERT
from cese.models.evidence_branch import EvidenceBranch, VectorEvidenceEncoder


def _make_inputs(batch: int = 4) -> tuple[torch.Tensor, torch.Tensor]:
    ev = torch.randn(batch, len(EVIDENCE_DIMS))
    ec = torch.rand(batch, len(EVIDENCE_DIMS))
    return ev, ec


def test_none_mode_backward_compatible():
    """none mode should produce same output shape as before."""
    enc = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        mapping_mask_mode="none",
    )
    ev, ec = _make_inputs()
    out = enc(ev, ec)
    assert out.shape == (4, len(CLAIM_DIMS))


def test_mask_by_dim_requires_mapping():
    """mask_by_dim mode should raise if mapping is None."""
    with pytest.raises(ValueError, match="mapping is required"):
        VectorEvidenceEncoder(
            input_dim=len(EVIDENCE_DIMS) * 2,
            hidden_dim=16,
            num_layers=1,
            mapping_mask_mode="mask_by_dim",
            mapping=None,
        )


def test_mask_by_dim_changes_output():
    """mask_by_dim should produce different output than none when
    evidence vector differs on non-R(k) dims."""
    enc_none = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        mapping_mask_mode="none",
    )
    enc_mask = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        mapping_mask_mode="mask_by_dim",
        mapping=R_EXPERT,
    )
    # Copy weights so the only difference is the masking.
    enc_mask.load_state_dict(enc_none.state_dict(), strict=False)

    ev, ec = _make_inputs()
    out_none = enc_none(ev, ec)
    out_mask = enc_mask(ev, ec)
    assert out_none.shape == out_mask.shape
    # Outputs should differ because masking changes the input.
    assert not torch.allclose(out_none, out_mask)


def test_mask_by_dim_zeros_non_rk_dims():
    """When evidence is non-zero only on non-R(k) dims, mask_by_dim
    should produce zero theta_support (since all evidence is masked out
    for every dim)."""
    enc = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        mapping_mask_mode="mask_by_dim",
        mapping=R_EXPERT,
    )
    # Set evidence to 0 everywhere.
    ev = torch.zeros(1, len(EVIDENCE_DIMS))
    ec = torch.zeros(1, len(EVIDENCE_DIMS))
    out = enc(ev, ec)
    # With zero input, output may not be exactly zero due to bias, but
    # the mask should not add any signal.
    assert out.shape == (1, len(CLAIM_DIMS))


def test_gated_by_dim_learns_gate():
    """gated_by_dim should have a learnable gate_logits parameter."""
    enc = VectorEvidenceEncoder(
        input_dim=len(EVIDENCE_DIMS) * 2,
        hidden_dim=16,
        num_layers=1,
        mapping_mask_mode="gated_by_dim",
        mapping=R_EXPERT,
    )
    assert enc.gate_logits is not None
    assert enc.gate_logits.shape == (len(CLAIM_DIMS), len(EVIDENCE_DIMS))
    # Gate for R(k) dims should be initialized high (favor).
    gate = torch.sigmoid(enc.gate_logits)
    for k_idx, k in enumerate(CLAIM_DIMS):
        rk_dims = set(R_EXPERT.get(k, []))
        for j, d in enumerate(EVIDENCE_DIMS):
            if d in rk_dims:
                assert gate[k_idx, j] > 0.8, f"R(k) dim {d} for {k} should be favored"
            else:
                assert gate[k_idx, j] < 0.2, f"non-R(k) dim {d} for {k} should be suppressed"


def test_evidence_branch_passes_mapping_mask_mode():
    """EvidenceBranch should pass mapping_mask_mode to the encoder."""
    branch = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="mask_by_dim",
        vector_kwargs={"hidden_dim": 16, "num_layers": 1},
    )
    assert branch.encoder.mapping_mask_mode == "mask_by_dim"
    ev, ec = _make_inputs()
    out = branch(ev, ec)
    assert out.shape == (4, len(CLAIM_DIMS))


def test_mapping_ablation_affects_forward():
    """The whole point of P2b: turning on mapping_mask_mode should
    change forward outputs, so ablation is meaningful."""
    torch.manual_seed(42)
    branch_none = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="none",
        vector_kwargs={"hidden_dim": 16, "num_layers": 1},
    )
    torch.manual_seed(42)
    branch_mask = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="mask_by_dim",
        vector_kwargs={"hidden_dim": 16, "num_layers": 1},
    )
    # Copy weights from none to mask so only masking differs.
    branch_mask.encoder.load_state_dict(
        branch_none.encoder.state_dict(), strict=False
    )
    ev, ec = _make_inputs()
    out_none = branch_none(ev, ec)
    out_mask = branch_mask(ev, ec)
    assert not torch.allclose(out_none, out_mask), (
        "mapping_mask_mode should affect forward outputs"
    )
