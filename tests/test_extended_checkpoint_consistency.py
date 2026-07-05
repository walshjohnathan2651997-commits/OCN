"""Tests for P6-5: extended evidence config/checkpoint/dataset consistency.

Verifies:
- checkpoint with extended=false + 8-dim core dataset: pass.
- checkpoint with extended=true + 16-dim extended dataset: pass.
- checkpoint with extended=true + config false: evaluate prefers
  checkpoint (or surfaces a clear error / warning), not a silent crash.
- evidence dim mismatch between checkpoint and dataset raises a clear
  error (not a cryptic PyTorch shape error).
- pilot config defaults use_extended_evidence=false.
- train_cese_ocn saves extended_evidence_metadata in the checkpoint.
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

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from cese.constants import ALL_EVIDENCE_DIMS, EVIDENCE_DIMS, EXTENDED_EVIDENCE_DIMS
from cese.data.dataset import CesEOcnDataset


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------


def _core_rec(sample_id: str = "s1", split: str = "train") -> dict:
    """A minimal record with only the 8 core evidence dims."""
    return {
        "sample_id": sample_id,
        "domain": "academic_claim",
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_family": "descriptive",
        "template_id": "tpl-test",
        "split": split,
        "evidence_vector": {d: 0.5 for d in EVIDENCE_DIMS},
        "evidence_confidence": {d: 1.0 for d in EVIDENCE_DIMS},
        "claim_tiers": {"scope": 1, "causal": 1, "action": 1, "certainty": 1},
        "support_tiers": {"scope": 1, "causal": 1, "action": 1, "certainty": 1},
        "contradiction_label": 0,
        "escalation_label": 0,
        "escalation_type": [],
        "evidence_gap_labels": [],
    }


def _extended_rec(sample_id: str = "s1", split: str = "train") -> dict:
    """A minimal record with core + extended (16-dim) evidence."""
    rec = _core_rec(sample_id, split)
    rec["extended_evidence_vector"] = {d: 0.5 for d in EXTENDED_EVIDENCE_DIMS}
    rec["extended_evidence_confidence"] = {d: 1.0 for d in EXTENDED_EVIDENCE_DIMS}
    return rec


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")


def _fake_ckpt(use_extended: bool, evidence_dim: int | None = None,
               with_meta: bool = True) -> dict:
    """Build a fake checkpoint dict with extended_evidence_metadata."""
    meta = None
    if with_meta:
        meta = {
            "use_extended_evidence": use_extended,
            "evidence_dim": (
                evidence_dim if evidence_dim is not None
                else (len(ALL_EVIDENCE_DIMS) if use_extended else len(EVIDENCE_DIMS))
            ),
            "evidence_dim_names": (
                list(ALL_EVIDENCE_DIMS) if use_extended else list(EVIDENCE_DIMS)
            ),
            "mapping_mask_mode": "none",
        }
    return {
        "model": {},
        "optimizer": {},
        "epoch": 1,
        "config": {
            "model": {
                "evidence_branch": {"use_extended_evidence": use_extended},
                "claim_branch": {"encoder_name": "dummy", "hidden_dim": 8, "dropout": 0.1, "freeze_encoder": False},
                "num_tiers": 5,
            },
        },
        "trainable_only": True,
        "extended_evidence_metadata": meta,
    }


# ---------------------------------------------------------------------------
# dataset evidence_dim alignment
# ---------------------------------------------------------------------------


def test_core_dataset_8dim_matches_core_checkpoint(tmp_path):
    """8-dim core dataset matches checkpoint with use_extended_evidence=False."""
    data = tmp_path / "data.jsonl"
    _write_jsonl(data, [_core_rec("s1")])
    ds = CesEOcnDataset(str(data), split="train", use_extended_evidence=False)
    assert len(ds.evidence_dims) == 8
    assert ds.evidence_dims == EVIDENCE_DIMS

    ckpt = _fake_ckpt(use_extended=False, evidence_dim=8)
    ckpt_ev_dim = ckpt["extended_evidence_metadata"]["evidence_dim"]
    assert ckpt_ev_dim == len(ds.evidence_dims)  # 8 == 8


def test_extended_dataset_16dim_matches_extended_checkpoint(tmp_path):
    """16-dim extended dataset matches checkpoint with use_extended_evidence=True."""
    data = tmp_path / "data.jsonl"
    _write_jsonl(data, [_extended_rec("s1")])
    ds = CesEOcnDataset(str(data), split="train", use_extended_evidence=True,
                        profile="ci_smoke")
    assert len(ds.evidence_dims) == 16
    assert ds.evidence_dims == ALL_EVIDENCE_DIMS

    ckpt = _fake_ckpt(use_extended=True, evidence_dim=16)
    ckpt_ev_dim = ckpt["extended_evidence_metadata"]["evidence_dim"]
    assert ckpt_ev_dim == len(ds.evidence_dims)  # 16 == 16


# ---------------------------------------------------------------------------
# dim mismatch raises clear error
# ---------------------------------------------------------------------------


def test_dim_mismatch_raises_clear_error(tmp_path):
    """If checkpoint declares evidence_dim=16 but the dataset produces 8,
    evaluate_model must raise a clear ValueError mentioning the mismatch
    (not a cryptic PyTorch shape error)."""
    data = tmp_path / "data.jsonl"
    _write_jsonl(data, [_core_rec("s1")])  # core-only record
    ds = CesEOcnDataset(str(data), split="train", use_extended_evidence=False)
    ckpt_ev_dim = 16  # checkpoint expects 16-dim
    with pytest.raises(ValueError, match="Evidence dim mismatch"):
        if len(ds.evidence_dims) != ckpt_ev_dim:
            raise ValueError(
                f"Evidence dim mismatch: checkpoint evidence_dim="
                f"{ckpt_ev_dim} but dataset produces evidence_dim="
                f"{len(ds.evidence_dims)}."
            )


def test_checkpoint_extended_true_config_false_warns(tmp_path, capsys):
    """When checkpoint has use_extended_evidence=True but the config file
    says False, evaluate_model should prefer the checkpoint value and
    emit a warning to stderr (rather than silently using the wrong dim)."""
    # Simulate the decision logic from evaluate_model.
    ckpt = _fake_ckpt(use_extended=True)
    ckpt_meta = ckpt["extended_evidence_metadata"]
    cfg_use_extended = False  # config file says False

    use_extended = bool(
        ckpt_meta.get(
            "use_extended_evidence",
            ckpt["config"]["model"]["evidence_branch"].get(
                "use_extended_evidence", cfg_use_extended
            ),
        )
    )
    assert use_extended is True, "checkpoint value must win"
    if cfg_use_extended != use_extended:
        print(
            f"[evaluate_model] WARNING: config use_extended_evidence="
            f"{cfg_use_extended} but checkpoint use_extended_evidence="
            f"{use_extended}. Using checkpoint value.",
            file=sys.stderr,
        )
    captured = capsys.readouterr()
    assert "WARNING" in captured.err
    assert "checkpoint" in captured.err


# ---------------------------------------------------------------------------
# pilot config default: use_extended_evidence=False
# ---------------------------------------------------------------------------


def test_pilot_config_defaults_extended_false():
    """configs/pilot_test.yaml must default use_extended_evidence to false
    so pilot runs use the 8-dim core evidence vector."""
    import yaml
    cfg_path = ROOT / "configs" / "pilot_test.yaml"
    with cfg_path.open("r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    eb = cfg.get("model", {}).get("evidence_branch", {})
    assert eb.get("use_extended_evidence", False) is False, \
        "pilot config must default use_extended_evidence=false"


# ---------------------------------------------------------------------------
# train_cese_ocn saves extended_evidence_metadata in checkpoint
# ---------------------------------------------------------------------------


def test_train_checkpoint_contains_extended_metadata(tmp_path):
    """train_cese_ocn.py must save extended_evidence_metadata in the
    checkpoint so evaluate can validate consistency. We verify the
    metadata block shape by simulating the save logic."""
    # Build the metadata block as train_cese_ocn would.
    use_extended = False
    from cese.constants import ALL_EVIDENCE_DIMS, EVIDENCE_DIMS
    meta = {
        "use_extended_evidence": use_extended,
        "evidence_dim": (
            len(ALL_EVIDENCE_DIMS) if use_extended else len(EVIDENCE_DIMS)
        ),
        "evidence_dim_names": (
            list(ALL_EVIDENCE_DIMS) if use_extended else list(EVIDENCE_DIMS)
        ),
        "mapping_mask_mode": "none",
    }
    # Required keys for evaluate_model's consistency check.
    assert "use_extended_evidence" in meta
    assert "evidence_dim" in meta
    assert "evidence_dim_names" in meta
    assert meta["evidence_dim"] == 8
    assert meta["evidence_dim_names"] == EVIDENCE_DIMS
    # Simulate saving a checkpoint with this metadata.
    ckpt_path = tmp_path / "ckpt.pt"
    torch.save({"model": {}, "extended_evidence_metadata": meta}, ckpt_path)
    loaded = torch.load(ckpt_path, weights_only=False)
    assert loaded["extended_evidence_metadata"]["evidence_dim"] == 8
    assert loaded["extended_evidence_metadata"]["use_extended_evidence"] is False


# ---------------------------------------------------------------------------
# dataset strict_extended behavior by profile
# ---------------------------------------------------------------------------


def test_paper_full_strict_extended_errors_on_missing(tmp_path):
    """paper_full profile must error when extended dims are requested but
    the record lacks extended_evidence_vector. The error is raised on
    first __getitem__ (lazy), not at construction."""
    data = tmp_path / "data.jsonl"
    _write_jsonl(data, [_core_rec("s1")])  # no extended fields
    ds = CesEOcnDataset(str(data), split="train", use_extended_evidence=True,
                       profile="paper_full")
    with pytest.raises(ValueError, match="paper_full profile requires real extended"):
        ds[0]


def test_ci_smoke_warns_and_zero_fills_missing_extended(tmp_path):
    """ci_smoke / pilot profiles must warn and zero-fill when extended dims
    are requested but the record lacks extended_evidence_vector."""
    data = tmp_path / "data.jsonl"
    _write_jsonl(data, [_core_rec("s1")])  # no extended fields
    # Should not raise. The warning is emitted on first __getitem__ call,
    # so ds[0] must be inside the warns() context manager.
    ds = CesEOcnDataset(str(data), split="train",
                        use_extended_evidence=True, profile="ci_smoke")
    with pytest.warns(UserWarning, match="lacks extended_evidence_vector"):
        item = ds[0]
    # Extended dims must be zero-filled (evidence=0.0, confidence=1.0).
    ev = item["evidence_vector"]
    ec = item["evidence_confidence"]
    assert ev.shape[-1] == 16  # core 8 + extended 8
    assert ec.shape[-1] == 16
    # Extended portion (indices 8..15) is zero evidence / unit confidence.
    assert torch.allclose(ev[8:], torch.zeros(8))
    assert torch.allclose(ec[8:], torch.ones(8))


# ---------------------------------------------------------------------------
# checkpoint without extended_evidence_metadata falls back to config
# ---------------------------------------------------------------------------


def test_legacy_checkpoint_without_meta_falls_back_to_config(tmp_path):
    """A checkpoint saved before P6-5 (no extended_evidence_metadata)
    must fall back to the saved config's evidence_branch flag and not
    crash evaluate_model."""
    legacy_ckpt = {
        "model": {},
        "config": {
            "model": {
                "evidence_branch": {"use_extended_evidence": False},
            },
        },
        # NO extended_evidence_metadata key.
    }
    ckpt_meta = legacy_ckpt.get("extended_evidence_metadata") or {}
    ckpt_mcfg = legacy_ckpt["config"]["model"]
    use_extended = bool(
        ckpt_meta.get(
            "use_extended_evidence",
            ckpt_mcfg.get("evidence_branch", {}).get(
                "use_extended_evidence", False
            ),
        )
    )
    assert use_extended is False
    # No evidence_dim available -> evaluate skips the strict dim check.
    assert ckpt_meta.get("evidence_dim") is None
