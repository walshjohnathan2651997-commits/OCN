"""Tests for P2-6: use_extended_evidence config propagation.

Verifies:
- pilot config defaults use_extended_evidence=false.
- smoke config defaults use_extended_evidence=false.
- extended config makes dataset output 16-dim vectors.
- extended dims missing -> ci_smoke/pilot warn, paper_full errors.
- deployment_constraints (extended) triggers action cap when extended.
- variance_seeds (extended) triggers certainty cap when extended.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest
import torch
import yaml

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import ALL_EVIDENCE_DIMS, EXTENDED_EVIDENCE_DIMS
from cese.data.dataset import CesEOcnDataset
from cese.losses.truncation import compute_max_support_tiers


def _base_record(sample_id: str, split: str = "train") -> dict:
    return {
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "academic_claim",
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_family": "descriptive",
        "evidence_vector": {
            "alignment": 1.0, "transparency": 1.0, "coverage": 1.0,
            "traceability": 1.0, "boundary": 1.0, "uncertainty": 1.0,
            "causal_id": 1.0, "risk_utility": 1.0,
        },
        "evidence_confidence": {
            "alignment": 1.0, "transparency": 1.0, "coverage": 1.0,
            "traceability": 1.0, "boundary": 1.0, "uncertainty": 1.0,
            "causal_id": 1.0, "risk_utility": 1.0,
        },
        "claim_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "support_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
        "contradiction_label": 0,
        "escalation_label": 0,
        "split": split,
    }


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


# ---------------------------------------------------------------------------
# Config defaults
# ---------------------------------------------------------------------------

def test_pilot_config_defaults_extended_off():
    """pilot_test.yaml must default use_extended_evidence=false."""
    cfg = yaml.safe_load(
        (ROOT / "configs" / "pilot_test.yaml").read_text(encoding="utf-8")
    )
    assert cfg["model"]["evidence_branch"].get("use_extended_evidence", False) is False


def test_smoke_config_defaults_extended_off():
    """smoke_test.yaml must default use_extended_evidence=false."""
    cfg = yaml.safe_load(
        (ROOT / "configs" / "smoke_test.yaml").read_text(encoding="utf-8")
    )
    assert cfg["model"]["evidence_branch"].get("use_extended_evidence", False) is False


# ---------------------------------------------------------------------------
# Dataset output dimensions
# ---------------------------------------------------------------------------

def test_dataset_core_mode_outputs_8dim(tmp_path):
    """use_extended_evidence=False -> 8-dim evidence_vector tensor."""
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [_base_record("s1")])
    ds = CesEOcnDataset(in_path, split="train", use_extended_evidence=False)
    item = ds[0]
    assert item["evidence_vector"].shape[0] == 8
    assert item["evidence_confidence"].shape[0] == 8


def test_dataset_extended_mode_outputs_16dim(tmp_path):
    """use_extended_evidence=True -> 16-dim evidence_vector tensor."""
    rec = _base_record("s1")
    rec["extended_evidence_vector"] = {d: 0.5 for d in EXTENDED_EVIDENCE_DIMS}
    rec["extended_evidence_confidence"] = {d: 1.0 for d in EXTENDED_EVIDENCE_DIMS}
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [rec])
    ds = CesEOcnDataset(
        in_path, split="train", use_extended_evidence=True, profile="ci_smoke"
    )
    item = ds[0]
    assert item["evidence_vector"].shape[0] == 16
    assert item["evidence_confidence"].shape[0] == 16


# ---------------------------------------------------------------------------
# Missing extended dims behavior
# ---------------------------------------------------------------------------

def test_extended_missing_warns_ci_smoke(tmp_path):
    """ci_smoke profile: missing extended dims -> warning + zero-fill."""
    rec = _base_record("s1")
    # No extended_evidence_vector / extended_evidence_confidence fields.
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [rec])
    ds = CesEOcnDataset(
        in_path, split="train", use_extended_evidence=True, profile="ci_smoke"
    )
    with pytest.warns(UserWarning, match="extended_evidence_vector"):
        item = ds[0]
    # Extended dims zero-filled.
    assert item["evidence_vector"].shape[0] == 16
    # First 8 are core (1.0), last 8 are extended (0.0 zero-filled).
    assert item["evidence_vector"][:8].tolist() == [1.0] * 8
    assert item["evidence_vector"][8:].tolist() == [0.0] * 8


def test_extended_missing_errors_paper_full(tmp_path):
    """paper_full profile: missing extended dims -> ValueError."""
    rec = _base_record("s1")
    in_path = tmp_path / "in.jsonl"
    _write_jsonl(in_path, [rec])
    ds = CesEOcnDataset(
        in_path, split="train", use_extended_evidence=True, profile="paper_full"
    )
    with pytest.raises(ValueError, match="paper_full profile requires"):
        ds[0]


# ---------------------------------------------------------------------------
# Action cap uses deployment_constraints (extended)
# ---------------------------------------------------------------------------

def test_action_cap_triggered_by_deployment_constraints_extended():
    """When use_extended_evidence=True (16-dim), action cap must trigger
    when deployment_constraints is low (extended dim), even if
    risk_utility is fine."""
    B = 1
    # 16-dim evidence vector: core 8 + extended 8.
    # deployment_constraints is index 13 in ALL_EVIDENCE_DIMS.
    ev = torch.ones(B, 16)
    ev[0, 13] = 0.1  # deployment_constraints low
    ec = torch.ones(B, 16)
    # claim_tiers: action=3 (triggers action cap check)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])
    max_tiers = compute_max_support_tiers(
        evidence_vector=ev,
        evidence_confidence=ec,
        claim_tiers=claim_tiers,
        use_extended_evidence=True,
    )
    # action is index 2; cap must be applied (cap_tier=2).
    assert max_tiers[0, 2].item() == 2


def test_action_cap_not_triggered_without_extended():
    """When use_extended_evidence=False (8-dim), deployment_constraints
    is NOT checked, so action cap should NOT trigger from it."""
    B = 1
    ev = torch.ones(B, 8)
    ec = torch.ones(B, 8)
    claim_tiers = torch.tensor([[0, 0, 3, 0]])
    max_tiers = compute_max_support_tiers(
        evidence_vector=ev,
        evidence_confidence=ec,
        claim_tiers=claim_tiers,
        use_extended_evidence=False,
    )
    # No cap applied because risk_utility is fine and
    # deployment_constraints is not in the 8-dim vector.
    assert max_tiers[0, 2].item() == 4  # default num_tiers-1


# ---------------------------------------------------------------------------
# Certainty cap uses variance_seeds (extended)
# ---------------------------------------------------------------------------

def test_certainty_cap_triggered_by_variance_seeds_extended():
    """When use_extended_evidence=True (16-dim), certainty cap must
    trigger when variance_seeds is low (extended dim), even if
    uncertainty is fine."""
    B = 1
    # variance_seeds is index 14 in ALL_EVIDENCE_DIMS.
    ev = torch.ones(B, 16)
    ev[0, 14] = 0.1  # variance_seeds low
    ec = torch.ones(B, 16)
    # claim_tiers: certainty=3 (triggers certainty cap check)
    claim_tiers = torch.tensor([[0, 0, 0, 3]])
    max_tiers = compute_max_support_tiers(
        evidence_vector=ev,
        evidence_confidence=ec,
        claim_tiers=claim_tiers,
        use_extended_evidence=True,
    )
    # certainty is index 3; cap must be applied (cap_tier=2).
    assert max_tiers[0, 3].item() == 2


def test_certainty_cap_not_triggered_without_extended():
    """When use_extended_evidence=False (8-dim), variance_seeds is NOT
    checked, so certainty cap should NOT trigger from it."""
    B = 1
    ev = torch.ones(B, 8)
    ec = torch.ones(B, 8)
    claim_tiers = torch.tensor([[0, 0, 0, 3]])
    max_tiers = compute_max_support_tiers(
        evidence_vector=ev,
        evidence_confidence=ec,
        claim_tiers=claim_tiers,
        use_extended_evidence=False,
    )
    # No cap because uncertainty is fine and variance_seeds not in 8-dim.
    assert max_tiers[0, 3].item() == 4
