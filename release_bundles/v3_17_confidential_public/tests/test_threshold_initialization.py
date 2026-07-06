"""Tests for threshold initialization (spec Section 4.3, task 11)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import numpy as np
import torch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from cese.constants import CLAIM_DIMS, NUM_TIERS
from cese.models import CesEOcnModel
from cese.models.shared_threshold_calibrator import SharedThresholdCalibrator


def test_initialize_from_data_sets_thresholds():
    """initialize_from_data should set raw_beta0/delta from tier distribution."""
    torch.manual_seed(0)
    calib = SharedThresholdCalibrator(num_tiers=NUM_TIERS, num_dims=len(CLAIM_DIMS))
    # Record thresholds BEFORE init.
    beta0_before = calib.raw_beta0.detach().clone()
    delta_before = calib.delta.detach().clone()

    # Synthetic tiers: mostly low (0,1) with some high (3,4).
    N, D = 64, len(CLAIM_DIMS)
    claim_tiers = torch.randint(0, NUM_TIERS, (N, D))
    support_tiers = torch.randint(0, NUM_TIERS, (N, D))
    info = calib.initialize_from_data(claim_tiers, support_tiers)

    # Thresholds should have changed.
    assert not torch.allclose(beta0_before, calib.raw_beta0.detach())
    if NUM_TIERS > 2:
        assert not torch.allclose(delta_before, calib.delta.detach())
    # Empirical cumulative probs in valid range.
    p_ge = info["empirical_p_ge"]
    assert (p_ge > 0).all() and (p_ge < 1).all()
    # Target betas strictly increasing over m.
    betas = info["target_betas"]
    diffs = betas[:, 1:] - betas[:, :-1]
    assert (diffs > -1e-5).all()


def test_threshold_init_via_model():
    """SharedThresholdCalibrator.initialize_from_data updates thresholds."""
    torch.manual_seed(0)
    calib = SharedThresholdCalibrator(
        num_tiers=NUM_TIERS, num_dims=len(CLAIM_DIMS),
        threshold_init="quantile",
    )
    N, D = 32, len(CLAIM_DIMS)
    claim_tiers = torch.randint(0, NUM_TIERS, (N, D))
    support_tiers = torch.randint(0, NUM_TIERS, (N, D))
    beta0_before = calib.raw_beta0.detach().clone()
    info = calib.initialize_from_data(claim_tiers, support_tiers)
    assert not torch.allclose(beta0_before, calib.raw_beta0.detach())


def test_fit_thresholds_script_produces_valid_state(tmp_path):
    """fit_thresholds.py should produce a valid threshold_state.json."""
    from scripts.fit_thresholds import compute_threshold_state

    # Synthetic records with claim/support tiers.
    records = []
    for i in range(40):
        records.append({
            "sample_id": f"s{i}",
            "claim_tiers": [i % NUM_TIERS] * len(CLAIM_DIMS),
            "support_tiers": [(i + 1) % NUM_TIERS] * len(CLAIM_DIMS),
        })
    state = compute_threshold_state(records, num_tiers=NUM_TIERS)
    assert state["n_samples"] == 80  # 40 claim + 40 support pooled
    assert state["num_tiers"] == NUM_TIERS
    assert len(state["target_betas"]) == len(CLAIM_DIMS)
    # Target betas strictly increasing.
    betas = np.array(state["target_betas"])
    diffs = betas[:, 1:] - betas[:, :-1]
    assert (diffs > -1e-5).all()


def test_fit_thresholds_cli(tmp_path):
    """End-to-end: fit_thresholds.py CLI writes a valid JSON state file."""
    import subprocess

    # Create a small JSONL input.
    jsonl_path = tmp_path / "input.jsonl"
    lines = []
    for i in range(20):
        rec = {
            "sample_id": f"s{i}",
            "split": "train",
            "claim_tiers": [i % NUM_TIERS] * len(CLAIM_DIMS),
            "support_tiers": [(i + 1) % NUM_TIERS] * len(CLAIM_DIMS),
        }
        lines.append(json.dumps(rec))
    jsonl_path.write_text("\n".join(lines), encoding="utf-8")

    out_path = tmp_path / "threshold_state.json"
    py = sys.executable
    result = subprocess.run(
        [py, str(ROOT / "scripts" / "fit_thresholds.py"),
         "--input", str(jsonl_path),
         "--output", str(out_path),
         "--source_split", "train"],
        capture_output=True, text=True, cwd=str(ROOT),
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert out_path.exists()
    with open(out_path, "r", encoding="utf-8") as f:
        state = json.load(f)
    assert state["n_samples"] == 40  # 20 claim + 20 support
    assert state["init_strategy"] == "quantile"


def test_evaluate_does_not_refit_thresholds():
    """evaluate_model.py must not call initialize_from_data (checkpoint only).

    P0-E: evaluate_model MAY load a pre-fitted threshold_state.json for
    provenance tracking (loading != refitting), but must NOT call any
    data-driven threshold initialization functions.
    """
    # Read the evaluate_model.py source and verify no threshold fitting calls.
    eval_path = ROOT / "scripts" / "evaluate_model.py"
    source = eval_path.read_text(encoding="utf-8")
    assert "initialize_from_data" not in source
    assert "initialize_thresholds_from_data" not in source
    assert "compute_threshold_state" not in source
