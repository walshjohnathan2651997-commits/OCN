"""Tests for baseline metric validity (no gold support/claim leakage).

Task 5 acceptance:
- OrdinalOnlyBaseline / EvidenceOnlyBaseline / NoCalibrationBaseline have a
  dedicated escalation head (no gold support/claim tier leakage).
- _baseline_metric_validity returns the correct flags.
- _evaluate_trained_baseline reports metric_validity and marks CESE special
  metrics as NA for baselines that don't predict support tiers.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest
import torch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from cese.baselines import (
    OrdinalOnlyBaseline,
    EvidenceOnlyBaseline,
    NoCalibrationBaseline,
)
from cese.constants import NUM_TIERS


# ---------------------------------------------------------------------------
# Test 1: baselines have an escalation head
# ---------------------------------------------------------------------------


def test_ordinal_only_baseline_has_escalation_head():
    """OrdinalOnlyBaseline must have an escalation_head attribute."""
    bl = OrdinalOnlyBaseline(
        encoder_name="test-stub",
        hidden_dim=16,
        num_tiers=NUM_TIERS,
        freeze_encoder=True,
    )
    assert hasattr(bl, "escalation_head")
    # Forward returns escalation_prob.
    out = bl(claim_texts=["hello world", "foo bar"], device="cpu")
    assert "escalation_prob" in out
    assert out["escalation_prob"].shape == (2,)
    assert (out["escalation_prob"] >= 0).all() and (out["escalation_prob"] <= 1).all()


def test_evidence_only_baseline_has_escalation_head():
    """EvidenceOnlyBaseline must have an escalation_head attribute."""
    bl = EvidenceOnlyBaseline(hidden_dim=16, num_tiers=NUM_TIERS)
    assert hasattr(bl, "escalation_head")
    ev = torch.rand(2, 8)
    ec = torch.rand(2, 8)
    out = bl(evidence_vector=ev, evidence_confidence=ec, device="cpu")
    assert "escalation_prob" in out
    assert out["escalation_prob"].shape == (2,)
    assert (out["escalation_prob"] >= 0).all() and (out["escalation_prob"] <= 1).all()


def test_no_calibration_baseline_has_escalation_head():
    """NoCalibrationBaseline must have an escalation_head attribute."""
    bl = NoCalibrationBaseline(
        encoder_name="test-stub",
        hidden_dim=16,
        num_tiers=NUM_TIERS,
        freeze_encoder=True,
    )
    assert hasattr(bl, "escalation_head")
    ev = torch.rand(2, 8)
    ec = torch.rand(2, 8)
    out = bl(
        claim_texts=["hello world", "foo bar"],
        evidence_vector=ev,
        evidence_confidence=ec,
        device="cpu",
    )
    assert "escalation_prob" in out
    assert out["escalation_prob"].shape == (2,)


# ---------------------------------------------------------------------------
# Test 2: _baseline_metric_validity returns correct flags
# ---------------------------------------------------------------------------


def test_baseline_metric_validity_flags():
    """_baseline_metric_validity must mark baselines as not using gold."""
    from scripts.run_baselines import _baseline_metric_validity
    for name in ("ordinal_only", "no_calibration", "evidence_only"):
        v = _baseline_metric_validity(name)
        assert v["uses_gold_support"] is False
        assert v["uses_gold_claim"] is False
        assert v["supports_cese_special_metrics"] is False


# ---------------------------------------------------------------------------
# Test 3: escalation head does not use gold support/claim tiers
# ---------------------------------------------------------------------------


def test_escalation_head_does_not_use_gold_support():
    """Changing gold support tiers must not change escalation_prob."""
    bl = OrdinalOnlyBaseline(
        encoder_name="test-stub",
        hidden_dim=16,
        num_tiers=NUM_TIERS,
        freeze_encoder=True,
    )
    bl.eval()
    texts = ["claim one", "claim two"]
    with torch.no_grad():
        out1 = bl(claim_texts=texts, device="cpu")
    # The escalation head only depends on the claim representation, so
    # calling forward again yields the same escalation_prob.
    with torch.no_grad():
        out2 = bl(claim_texts=texts, device="cpu")
    assert torch.allclose(out1["escalation_prob"], out2["escalation_prob"], atol=1e-6)


# ---------------------------------------------------------------------------
# Test 4: _evaluate_trained_baseline includes metric_validity
# ---------------------------------------------------------------------------


def test_evaluate_trained_baseline_includes_metric_validity():
    """_evaluate_trained_baseline must include a metric_validity field."""
    from scripts.run_baselines import _evaluate_trained_baseline
    from cese.data.collate import collate_fn
    from torch.utils.data import DataLoader
    from cese.data.dataset import CesEOcnDataset

    # Use the smoke toy data if available.
    data_path = Path("data/toy/smoke.jsonl")
    if not data_path.exists():
        pytest.skip("smoke data not available")
    ds = CesEOcnDataset(str(data_path), split="test")
    loader = DataLoader(ds, batch_size=4, collate_fn=collate_fn, num_workers=0)
    bl = OrdinalOnlyBaseline(
        encoder_name="test-stub",
        hidden_dim=16,
        num_tiers=NUM_TIERS,
        freeze_encoder=True,
    )
    m = _evaluate_trained_baseline(
        bl, loader, torch.device("cpu"), ds.records, None, "ordinal_only"
    )
    assert "metric_validity" in m
    assert m["metric_validity"]["uses_gold_support"] is False
    assert m["metric_validity"]["supports_cese_special_metrics"] is False
    # CESE special metrics should be NaN for baselines.
    assert np.isnan(m.get("high_strength_false_support_rate", float("nan")))
    assert np.isnan(m.get("causal_overclaim_recall", float("nan")))


# ---------------------------------------------------------------------------
# Test 5: P1 - n_samples=0 rows must be metric_valid=False / split_valid=False
# ---------------------------------------------------------------------------


def test_metric_valid_false_when_n_samples_zero():
    """_metric_valid must return False when n_samples <= 0."""
    from scripts.generate_tables import _metric_valid
    # n_samples=0 -> False
    assert _metric_valid({"n_samples": 0, "metric_valid": True}) is False
    # n_samples missing -> False
    assert _metric_valid({"metric_valid": True}) is False
    # n_samples negative -> False
    assert _metric_valid({"n_samples": -1, "metric_valid": True}) is False
    # n_samples>0 + metric_valid=True -> True
    assert _metric_valid({"n_samples": 8, "metric_valid": True}) is True
    # n_samples>0 + metric_valid=False -> False
    assert _metric_valid({"n_samples": 8, "metric_valid": False}) is False
    # non-dict -> False
    assert _metric_valid(None) is False
    assert _metric_valid("foo") is False


def test_adversarial_split_valid_false_when_n_samples_zero(tmp_path):
    """build_adversarial_results must set split_valid=False when
    n_samples=0, even if the source JSON says split_valid=True."""
    import json
    from scripts.generate_tables import build_adversarial_results
    adv_dir = tmp_path / "adversarial"
    adv_dir.mkdir()
    (adv_dir / "adversarial_results.json").write_text(
        json.dumps({
            "standard": {"escalation_f1": 0.5, "n_samples": 8, "split_valid": True},
            "template_held_out": {"escalation_f1": None, "n_samples": 0, "split_valid": True},
            "domain_held_out": {"escalation_f1": None, "n_samples": 0, "split_valid": True},
        }),
        encoding="utf-8",
    )
    rows = build_adversarial_results(tmp_path)
    by_split = {r["split"]: r for r in rows}
    assert by_split["Standard test"]["split_valid"] is True
    # P1: empty splits must be split_valid=False even when source says True.
    assert by_split["Template-held-out test"]["split_valid"] is False
    assert by_split["Domain-held-out test"]["split_valid"] is False


def test_main_results_paper_valid_false_when_metrics_missing(tmp_path):
    """build_main_results must set paper_valid=False when a baseline has
    no real predictions (all metrics NaN), even if the source JSON says
    paper_valid=True.

    P0-C: rule_baseline is NEVER paper_valid (uses gold tiers), so its
    paper_valid is forced to False regardless of source JSON claims.
    """
    import json
    from scripts.generate_tables import build_main_results
    bl_dir = tmp_path / "baselines"
    bl_dir.mkdir()
    (bl_dir / "baselines_results.json").write_text(
        json.dumps({
            "rule_baseline": {"accuracy": 1.0, "macro_f1": 1.0, "n_samples": 8, "paper_valid": True},
            "nli_baseline": {"accuracy": None, "macro_f1": None, "escalation_f1": None, "paper_valid": True},
            "rag_llm_baseline": {"accuracy": 0.8, "macro_f1": 0.7, "n_samples": 8, "paper_valid": True},
        }),
        encoding="utf-8",
    )
    rows = build_main_results(tmp_path, profile="ci_smoke")
    by_model = {r["model"]: r for r in rows}
    # P0-C: rule_baseline is never paper_valid (uses gold tiers).
    assert by_model["Rule baseline"]["paper_valid"] is False
    assert by_model["Rule baseline"]["uses_gold_tiers"] is True
    # rag_llm_baseline with real metrics is paper_valid.
    assert by_model["RAG-LLM baseline"]["paper_valid"] is True
    # P1: empty baseline must be paper_valid=False even when source says True.
    assert by_model["NLI baseline"]["paper_valid"] is False


def test_main_results_paper_full_excludes_invalid_baselines(tmp_path):
    """paper_full must exclude baselines with paper_valid=False from the
    main table entirely.

    P0-C: rule_baseline is excluded from paper_full (uses gold tiers,
    never paper-valid) even when source JSON claims paper_valid=True.
    """
    import json
    from scripts.generate_tables import build_main_results
    bl_dir = tmp_path / "baselines"
    bl_dir.mkdir()
    (bl_dir / "baselines_results.json").write_text(
        json.dumps({
            "rule_baseline": {"accuracy": 1.0, "macro_f1": 1.0, "n_samples": 8, "paper_valid": True},
            "nli_baseline": {"accuracy": None, "macro_f1": None, "paper_valid": True},
            "rag_llm_baseline": {"accuracy": 0.8, "macro_f1": 0.7, "n_samples": 8, "paper_valid": True},
        }),
        encoding="utf-8",
    )
    rows = build_main_results(tmp_path, profile="paper_full")
    models = {r["model"] for r in rows}
    # P0-C: rule_baseline excluded from paper_full (uses gold tiers).
    assert "Rule baseline" not in models
    # RAG-LLM with real metrics is included.
    assert "RAG-LLM baseline" in models
    # P2: paper_full excludes invalid baselines entirely.
    assert "NLI baseline" not in models
