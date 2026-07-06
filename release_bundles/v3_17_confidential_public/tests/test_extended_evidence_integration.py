"""Tests for Task A: extended evidence dims integration.

Verifies that ``use_extended_evidence=True`` properly threads the 16-dim
evidence vector (core 8 + extended 8) through:
  - dataset loading (extended fields read into the tensor)
  - mapping_to_mask() (R(k) mask covers extended dims)
  - compute_max_support_tiers() (action cap checks deployment_constraints;
    certainty cap checks variance_seeds)
  - VectorEvidenceEncoder / EvidenceBranch (input_dim=32 accepted)
  - backward compatibility: use_extended_evidence=False still loads
    old 8-dim data and produces 16-dim input to the encoder.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import (
    ALL_EVIDENCE_DIMS,
    CLAIM_DIMS,
    EVIDENCE_DIMS,
    EXTENDED_EVIDENCE_DIMS,
    R_EXPERT,
)
from cese.data.mapping import (
    build_mapping,
    mapping_to_mask,
)
from cese.losses.truncation import compute_max_support_tiers
from cese.models.evidence_branch import EvidenceBranch, VectorEvidenceEncoder


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _toy_record(sample_id: str = "s1", with_extended: bool = True) -> dict:
    """Build a minimal valid record compatible with the schema."""
    rec = {
        "sample_id": sample_id,
        "domain": "toy",
        "source_type": "synthetic",
        "split": "train",
        "claim_text": "claim text",
        "evidence_text": "evidence text",
        "claim_family": "causal",
        "evidence_vector": {d: 0.0 for d in EVIDENCE_DIMS},
        "evidence_confidence": {d: 1.0 for d in EVIDENCE_DIMS},
        "extended_evidence_vector": {d: 0.0 for d in EXTENDED_EVIDENCE_DIMS},
        "extended_evidence_confidence": {d: 1.0 for d in EXTENDED_EVIDENCE_DIMS},
        "claim_tiers": {d: 0 for d in CLAIM_DIMS},
        "support_tiers": {d: 0 for d in CLAIM_DIMS},
        "contradiction_label": 0,
        "escalation_label": 0,
        "escalation_type": "none",
        "evidence_gap_labels": [],
    }
    if not with_extended:
        # Remove extended fields to simulate legacy 8-dim data.
        rec.pop("extended_evidence_vector", None)
        rec.pop("extended_evidence_confidence", None)
    return rec


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# Dataset tests
# ---------------------------------------------------------------------------

def test_dataset_reads_extended_dims(tmp_path):
    """When use_extended_evidence=True the dataset returns 16-dim tensors."""
    from cese.data.dataset import CesEOcnDataset

    p = tmp_path / "in.jsonl"
    _write_jsonl(p, [_toy_record("s1"), _toy_record("s2")])
    ds = CesEOcnDataset(p, split=None, use_extended_evidence=True, validate=False)
    item = ds[0]
    assert item["evidence_vector"].shape == (16,)
    assert item["evidence_confidence"].shape == (16,)


def test_dataset_legacy_8dim_when_disabled(tmp_path):
    """When use_extended_evidence=False the dataset still returns 8-dim
    tensors even if extended fields are present in the record."""
    from cese.data.dataset import CesEOcnDataset

    p = tmp_path / "in.jsonl"
    _write_jsonl(p, [_toy_record("s1"), _toy_record("s2")])
    ds = CesEOcnDataset(p, split=None, use_extended_evidence=False, validate=False)
    item = ds[0]
    assert item["evidence_vector"].shape == (8,)
    assert item["evidence_confidence"].shape == (8,)


def test_dataset_extended_mode_loads_old_8dim_data(tmp_path):
    """use_extended_evidence=True must still load legacy data that lacks
    extended fields (defaulting extended dims to 0.0 evidence / 1.0
    confidence), so old 8-dim datasets remain runnable."""
    from cese.data.dataset import CesEOcnDataset

    p = tmp_path / "in.jsonl"
    _write_jsonl(p, [_toy_record("s1", with_extended=False),
                     _toy_record("s2", with_extended=False)])
    ds = CesEOcnDataset(p, split=None, use_extended_evidence=True, validate=False)
    item = ds[0]
    # Extended dims default to 0.0 evidence / 1.0 confidence.
    assert item["evidence_vector"].shape == (16,)
    assert item["evidence_confidence"].shape == (16,)
    # First 8 entries come from core dims, last 8 are extended defaults.
    assert torch.allclose(item["evidence_vector"][8:], torch.zeros(8))
    assert torch.allclose(item["evidence_confidence"][8:], torch.ones(8))


# ---------------------------------------------------------------------------
# Mapping / mask tests
# ---------------------------------------------------------------------------

def test_mapping_mask_covers_extended_dims_when_enabled():
    """mapping_to_mask(use_extended_evidence=True) returns masks of width 16
    and R(k) extended dims (e.g. deployment_constraints for action) are
    properly marked as in-R(k)."""
    mapping = build_mapping("expert", use_extended_evidence=True)
    masks = mapping_to_mask(mapping, use_extended_evidence=True)
    for k in CLAIM_DIMS:
        assert masks[k].shape == (16,), f"{k} mask should be 16-dim"
    # R(action) includes deployment_constraints (extended dim) per R_EXPERT.
    action_mask = masks["action"]
    dc_idx = ALL_EVIDENCE_DIMS.index("deployment_constraints")
    assert action_mask[dc_idx], (
        "deployment_constraints should be in R(action) when extended dims "
        "are enabled"
    )
    # R(certainty) includes variance_seeds (extended dim).
    certainty_mask = masks["certainty"]
    vs_idx = ALL_EVIDENCE_DIMS.index("variance_seeds")
    assert certainty_mask[vs_idx], (
        "variance_seeds should be in R(certainty) when extended dims are "
        "enabled"
    )


def test_mapping_mask_8dim_when_disabled():
    """mapping_to_mask(use_extended_evidence=False) returns 8-dim masks
    (backward compatible)."""
    mapping = build_mapping("expert", use_extended_evidence=False)
    masks = mapping_to_mask(mapping, use_extended_evidence=False)
    for k in CLAIM_DIMS:
        assert masks[k].shape == (8,), f"{k} mask should be 8-dim"


# ---------------------------------------------------------------------------
# Truncation tests
# ---------------------------------------------------------------------------

def test_action_cap_triggers_on_missing_deployment_constraints():
    """When use_extended_evidence=True and deployment_constraints=0, the
    action cap must trigger (max_support_tier[action] <= cap)."""
    ev = torch.zeros(1, 16)  # all evidence = 0 (incl. deployment_constraints)
    ec = torch.zeros(1, 16)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])  # action tier = 3
    max_tiers = compute_max_support_tiers(
        ev, ec, claim_tiers,
        cap_tier=2,
        use_extended_evidence=True,
    )
    action_idx = CLAIM_DIMS.index("action")
    assert max_tiers[0, action_idx] <= 2, (
        "action cap should trigger when deployment_constraints is missing"
    )


def test_certainty_cap_triggers_on_missing_variance_seeds():
    """When use_extended_evidence=True and variance_seeds=0, the certainty
    cap must trigger (max_support_tier[certainty] <= cap)."""
    ev = torch.zeros(1, 16)  # all evidence = 0 (incl. variance_seeds)
    ec = torch.zeros(1, 16)
    claim_tiers = torch.tensor([[0, 0, 0, 3]])  # certainty tier = 3
    max_tiers = compute_max_support_tiers(
        ev, ec, claim_tiers,
        cap_tier=2,
        use_extended_evidence=True,
    )
    certainty_idx = CLAIM_DIMS.index("certainty")
    assert max_tiers[0, certainty_idx] <= 2, (
        "certainty cap should trigger when variance_seeds is missing"
    )


def test_action_cap_does_not_trigger_when_deployment_constraints_present():
    """When deployment_constraints is high, action cap should NOT trigger
    due to deployment_constraints alone (risk_utility also high)."""
    ev = torch.ones(1, 16)  # all evidence = 1.0
    ec = torch.ones(1, 16)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])  # action tier = 3
    max_tiers = compute_max_support_tiers(
        ev, ec, claim_tiers,
        cap_tier=2,
        gamma_action=0.5,
        q_min=0.5,
        use_extended_evidence=True,
    )
    action_idx = CLAIM_DIMS.index("action")
    assert max_tiers[0, action_idx] > 2, (
        "action cap should NOT trigger when deployment_constraints is present"
    )


def test_truncation_8dim_skips_extended_check():
    """When use_extended_evidence=False (8-dim input), the extended-dim
    checks are skipped (no index error, behavior unchanged)."""
    ev = torch.zeros(1, 8)
    ec = torch.zeros(1, 8)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])  # action tier = 3
    # Should not raise. Action cap triggers via risk_utility=0.
    max_tiers = compute_max_support_tiers(
        ev, ec, claim_tiers,
        cap_tier=2,
        use_extended_evidence=False,
    )
    action_idx = CLAIM_DIMS.index("action")
    assert max_tiers[0, action_idx] <= 2


# ---------------------------------------------------------------------------
# EvidenceBranch tests
# ---------------------------------------------------------------------------

def test_evidence_branch_accepts_32dim_input():
    """EvidenceBranch with use_extended_evidence=True accepts 32-dim input
    (16 evidence + 16 confidence)."""
    branch = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="none",
        use_extended_evidence=True,
        vector_kwargs={
            "input_dim": len(ALL_EVIDENCE_DIMS) * 2,
            "hidden_dim": 16,
            "num_layers": 1,
        },
    )
    B = 4
    ev = torch.randn(B, len(ALL_EVIDENCE_DIMS))
    ec = torch.rand(B, len(ALL_EVIDENCE_DIMS))
    out = branch(ev, ec)
    assert out.shape == (B, len(CLAIM_DIMS))


def test_evidence_branch_mask_mode_with_extended_dims():
    """mask_by_dim with use_extended_evidence=True should mask extended
    dims that are NOT in R(k)."""
    branch = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="mask_by_dim",
        use_extended_evidence=True,
        vector_kwargs={
            "input_dim": len(ALL_EVIDENCE_DIMS) * 2,
            "hidden_dim": 16,
            "num_layers": 1,
        },
    )
    enc = branch.encoder
    assert enc.evidence_mask.shape == (len(CLAIM_DIMS), len(ALL_EVIDENCE_DIMS))
    # action dim should include deployment_constraints in its mask.
    action_idx = CLAIM_DIMS.index("action")
    dc_idx = ALL_EVIDENCE_DIMS.index("deployment_constraints")
    assert enc.evidence_mask[action_idx, dc_idx] == 1.0


def test_evidence_branch_backward_compatible_8dim():
    """use_extended_evidence=False (default) keeps 16-dim input (8+8)
    and 8-dim masks, matching the pre-extended behavior."""
    branch = EvidenceBranch(
        mode="vector",
        mapping=R_EXPERT,
        mapping_mask_mode="mask_by_dim",
        vector_kwargs={
            "input_dim": len(EVIDENCE_DIMS) * 2,
            "hidden_dim": 16,
            "num_layers": 1,
        },
    )
    enc = branch.encoder
    assert enc.evidence_mask.shape == (len(CLAIM_DIMS), len(EVIDENCE_DIMS))
    B = 4
    ev = torch.randn(B, len(EVIDENCE_DIMS))
    ec = torch.rand(B, len(EVIDENCE_DIMS))
    out = branch(ev, ec)
    assert out.shape == (B, len(CLAIM_DIMS))
