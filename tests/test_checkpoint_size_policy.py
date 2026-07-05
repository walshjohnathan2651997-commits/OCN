"""Tests for checkpoint size policy (lightweight / trainable / full).

Covers:
1. lightweight checkpoint drops PLM encoder keys (claim_branch.encoder,
   distilbert, bert, roberta, transformer, claim_encoder).
2. full checkpoint contains the complete state_dict.
3. ci_smoke ablation checkpoint stays under 10 MB.
4. checkpoint_mode=lightweight with a file over the threshold raises
   RuntimeError via assert_checkpoint_size.
5. run_all_experiments --profile ci_smoke does NOT default to
   configs/model_cese_ocn.yaml as the ablation config (it should pick
   configs/smoke_ablations.yaml).
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.models.cese_ocn import CesEOcnModel
from cese.utils.checkpoint import (
    ENCODER_KEY_FRAGMENTS,
    assert_checkpoint_size,
    checkpoint_filename,
    state_dict_for_saving,
)
from cese.utils.io import save_checkpoint


def _make_model():
    """Build a CesEOcnModel with the test-stub encoder (no HF download)."""
    return CesEOcnModel(
        claim_encoder_name="test-stub",
        hidden_dim=16,
        num_dims=4,
        evidence_hidden_dim=16,
        evidence_num_layers=1,
        evidence_dropout=0.1,
        claim_dropout=0.1,
        freeze_encoder=False,
        threshold_init="quantile",
        margin=0.5,
        score_mode="exceedance",
        escalation_aggregation="noisy_or",
    )


# ---------------------------------------------------------------------------
# 1. lightweight drops encoder keys
# ---------------------------------------------------------------------------


def test_lightweight_drops_encoder_keys():
    """lightweight mode must not contain any PLM encoder keys."""
    model = _make_model()
    full_sd = model.state_dict()
    lightweight_sd = state_dict_for_saving(model, mode="lightweight")

    # Sanity: full state dict has at least one encoder key.
    encoder_keys_in_full = [
        k for k in full_sd if any(frag in k for frag in ENCODER_KEY_FRAGMENTS)
    ]
    assert len(encoder_keys_in_full) > 0, (
        "Test setup broken: model has no encoder keys to filter."
    )

    # lightweight must drop every encoder key.
    for key in encoder_keys_in_full:
        assert key not in lightweight_sd, (
            f"lightweight checkpoint leaked encoder key: {key}"
        )

    # lightweight must keep non-encoder keys (heads, evidence branch, etc.).
    non_encoder_keys = [
        k for k in full_sd
        if not any(frag in k for frag in ENCODER_KEY_FRAGMENTS)
    ]
    for key in non_encoder_keys:
        assert key in lightweight_sd, (
            f"lightweight checkpoint dropped non-encoder key: {key}"
        )


# ---------------------------------------------------------------------------
# 2. full contains everything
# ---------------------------------------------------------------------------


def test_full_keeps_everything():
    """full mode must equal model.state_dict()."""
    model = _make_model()
    full_sd = model.state_dict()
    saved_sd = state_dict_for_saving(model, mode="full")
    assert set(saved_sd.keys()) == set(full_sd.keys())
    for k in full_sd:
        assert torch.equal(saved_sd[k], full_sd[k])


# ---------------------------------------------------------------------------
# 3. ci_smoke ablation checkpoint stays small
# ---------------------------------------------------------------------------


def test_smoke_ablation_checkpoint_under_10mb(tmp_path):
    """A lightweight checkpoint from the stub-encoder model must be < 10 MB.

    This mirrors what ci_smoke produces (test-stub encoder + lightweight
    mode). A 250 MB file here would indicate the encoder weights leaked
    through.
    """
    model = _make_model()
    ckpt_path = tmp_path / "calibration_full.lightweight.pt"
    save_checkpoint(
        {
            "model": state_dict_for_saving(model, mode="lightweight"),
            "checkpoint_mode": "lightweight",
        },
        ckpt_path,
    )
    size_mb = ckpt_path.stat().st_size / 1024 / 1024
    assert size_mb < 10.0, (
        f"Smoke checkpoint too large: {size_mb:.2f} MB (limit 10 MB). "
        "PLM encoder weights likely leaked into lightweight checkpoint."
    )


# ---------------------------------------------------------------------------
# 4. assert_checkpoint_size raises on oversized lightweight
# ---------------------------------------------------------------------------


def test_assert_checkpoint_size_raises_on_oversized_lightweight(tmp_path):
    """An oversized lightweight checkpoint must raise RuntimeError."""
    # Write a fake 20 MB file.
    big_path = tmp_path / "fake.lightweight.pt"
    big_path.write_bytes(b"\x00" * (20 * 1024 * 1024))

    with pytest.raises(RuntimeError, match="too large"):
        assert_checkpoint_size(
            big_path,
            mode="lightweight",
            max_mb_lightweight=10.0,
            max_mb_smoke=10.0,
            is_smoke=True,
        )


def test_assert_checkpoint_size_passes_for_full(tmp_path):
    """full mode must never raise (explicitly allowed to be large)."""
    big_path = tmp_path / "fake.full.pt"
    big_path.write_bytes(b"\x00" * (200 * 1024 * 1024))

    # Should not raise.
    assert_checkpoint_size(
        big_path,
        mode="full",
        max_mb_lightweight=10.0,
        max_mb_smoke=10.0,
        is_smoke=True,
    )


def test_assert_checkpoint_size_passes_small_lightweight(tmp_path):
    """A small lightweight checkpoint must not raise."""
    small_path = tmp_path / "small.lightweight.pt"
    small_path.write_bytes(b"\x00" * (1 * 1024 * 1024))  # 1 MB

    assert_checkpoint_size(
        small_path,
        mode="lightweight",
        max_mb_lightweight=10.0,
        max_mb_smoke=10.0,
        is_smoke=True,
    )


# ---------------------------------------------------------------------------
# 5. run_all_experiments ci_smoke does not default to model_cese_ocn.yaml
# ---------------------------------------------------------------------------


def test_ci_smoke_does_not_default_to_model_cese_ocn_for_ablations():
    """ci_smoke profile must pick smoke_ablations.yaml, not model_cese_ocn.yaml.

    This test inspects run_all_experiments.py source to ensure that when
    profile == 'ci_smoke' and the user did not pass --ablations-config, the
    ablation config is switched to configs/smoke_ablations.yaml (which uses
    test-stub + freeze_encoder=true).
    """
    src = (ROOT / "scripts" / "run_all_experiments.py").read_text(encoding="utf-8")
    assert "smoke_ablations.yaml" in src, (
        "run_all_experiments.py should switch to configs/smoke_ablations.yaml "
        "for ci_smoke profile."
    )
    assert "is_ci_smoke" in src, (
        "run_all_experiments.py should branch on is_ci_smoke for ablation config."
    )


# ---------------------------------------------------------------------------
# Bonus: checkpoint_filename
# ---------------------------------------------------------------------------


def test_checkpoint_filename():
    assert checkpoint_filename("calibration_full", "lightweight") == \
        "calibration_full.lightweight.pt"
    assert checkpoint_filename("calibration_full", "full") == \
        "calibration_full.full.pt"
    assert checkpoint_filename("calibration_full", "trainable") == \
        "calibration_full.trainable.pt"


def test_invalid_mode_raises():
    model = _make_model()
    with pytest.raises(ValueError, match="Unknown checkpoint mode"):
        state_dict_for_saving(model, mode="bogus")
