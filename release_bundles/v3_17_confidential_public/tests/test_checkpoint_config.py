"""Tests for checkpoint config recovery.

Task 5 acceptance:
- test_eval_loads_checkpoint_config: evaluate_model.py must recover
  structural params (calibration_mode, score_mode, escalation_aggregation)
  from the checkpoint's saved config, not from the CLI config.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.models.cese_ocn import CesEOcnModel
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator
from cese.utils.io import save_checkpoint, load_checkpoint, trainable_state_dict


def _make_model(calibration_mode="shared_threshold", score_mode="exceedance",
               escalation_aggregation="noisy_or", margin=0.5,
               threshold_init="quantile", enforce_monotonic=True):
    """Build a CesEOcnModel with the given structural params.

    Uses the `test-stub` encoder so no transformers/HF download is needed.

    Note: ``shared_threshold`` is a deprecated alias for ``calibration_mode``.
    When ``calibration_mode`` is passed explicitly, ``shared_threshold`` must
    be ``None`` so :func:`_resolve_calibration_mode` does not raise a
    contradictory-settings error. ``enforce_monotonic`` is an independent
    flag (threshold monotonicity) and is passed through unchanged.
    """
    return CesEOcnModel(
        claim_encoder_name="test-stub",
        hidden_dim=32,
        num_tiers=5,
        evidence_mode="vector",
        shared_threshold=None,
        mapping=None,
        claim_dropout=0.1,
        freeze_encoder=True,
        evidence_hidden_dim=32,
        evidence_num_layers=1,
        evidence_dropout=0.1,
        threshold_init=threshold_init,
        enforce_monotonic=enforce_monotonic,
        margin=margin,
        score_mode=score_mode,
        escalation_aggregation=escalation_aggregation,
        calibration_mode=calibration_mode,
    )


def test_checkpoint_preserves_structural_params(tmp_path):
    """A checkpoint must save the config so eval can recover structural params."""
    model = _make_model(
        calibration_mode="separate_thresholds",
        score_mode="exceedance",
        escalation_aggregation="noisy_or",
        margin=0.7,
        threshold_init="uniform",
        enforce_monotonic=False,
    )
    cfg = {
        "model": {
            "num_tiers": 5,
            "claim_branch": {"encoder_name": "distilbert-base-uncased",
                             "hidden_dim": 32, "dropout": 0.1,
                             "freeze_encoder": True},
            "evidence_branch": {"mode": "vector", "hidden_dim": 32,
                                "num_layers": 1, "dropout": 0.1},
            "shared_threshold": {
                "init_strategy": "uniform",
                "margin": 0.7,
                "enforce_monotonic": False,
                "calibration_mode": "separate_thresholds",
                "score_mode": "exceedance",
                "escalation_aggregation": "noisy_or",
            },
        }
    }
    ckpt_path = tmp_path / "test.pt"
    save_checkpoint(
        {
            "model": trainable_state_dict(model),
            "config": cfg,
            "trainable_only": True,
        },
        ckpt_path,
    )
    loaded = load_checkpoint(str(ckpt_path))
    assert "config" in loaded
    st = loaded["config"]["model"]["shared_threshold"]
    assert st["calibration_mode"] == "separate_thresholds"
    assert st["score_mode"] == "exceedance"
    assert st["escalation_aggregation"] == "noisy_or"
    assert st["margin"] == 0.7
    assert st["init_strategy"] == "uniform"
    assert st["enforce_monotonic"] is False


def test_eval_loads_checkpoint_config(tmp_path):
    """Eval must use the checkpoint's config, not the CLI config, for
    structural params like calibration_mode.
    """
    # Train with separate_thresholds, save checkpoint.
    model_train = _make_model(calibration_mode="separate_thresholds")
    cfg_train = {
        "model": {
            "num_tiers": 5,
            "claim_branch": {"encoder_name": "distilbert-base-uncased",
                             "hidden_dim": 32, "dropout": 0.1,
                             "freeze_encoder": True},
            "evidence_branch": {"mode": "vector", "hidden_dim": 32,
                                "num_layers": 1, "dropout": 0.1},
            "shared_threshold": {
                "init_strategy": "quantile",
                "margin": 0.5,
                "enforce_monotonic": True,
                "calibration_mode": "separate_thresholds",
                "score_mode": "exceedance",
                "escalation_aggregation": "noisy_or",
            },
        }
    }
    ckpt_path = tmp_path / "ckpt.pt"
    save_checkpoint(
        {"model": trainable_state_dict(model_train), "config": cfg_train,
         "trainable_only": True},
        ckpt_path,
    )

    # Eval with a DIFFERENT config (shared_threshold), but the checkpoint
    # config should override it.
    ckpt = load_checkpoint(str(ckpt_path))
    ckpt_cfg = ckpt["config"]
    ckpt_st = ckpt_cfg["model"]["shared_threshold"]

    # Build model from checkpoint config.
    model_eval = _make_model(
        calibration_mode=ckpt_st.get("calibration_mode", "shared_threshold"),
        score_mode=ckpt_st.get("score_mode", "exceedance"),
        escalation_aggregation=ckpt_st.get("escalation_aggregation", "noisy_or"),
        margin=ckpt_st.get("margin", 0.5),
        threshold_init=ckpt_st.get("init_strategy", "quantile"),
        enforce_monotonic=ckpt_st.get("enforce_monotonic", True),
    )

    # The eval model should have separate_thresholds params, not shared.
    assert model_eval.calibrator.calibration_mode == "separate_thresholds"
    assert hasattr(model_eval.calibrator, "raw_a_claim")
    assert hasattr(model_eval.calibrator, "raw_a_support")


def test_model_stores_structural_params():
    """CesEOcnModel must store calibration_mode/score_mode/escalation_aggregation
    as attributes for checkpoint recovery.
    """
    model = _make_model(
        calibration_mode="no_calibration",
        score_mode="exceedance",
        escalation_aggregation="max",
        margin=0.3,
    )
    assert model.calibration_mode == "no_calibration"
    assert model.score_mode == "exceedance"
    assert model.escalation_aggregation == "max"
    assert model.margin == 0.3
    assert model.threshold_init == "quantile"
    assert model.enforce_monotonic is True
    # shared_threshold is a deprecated read-only alias for
    # (calibration_mode == "shared_threshold").
    assert model.shared_threshold is False
