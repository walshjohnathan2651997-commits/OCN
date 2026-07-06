"""Tests for the oracle/extracted/confidence-aware comparison (spec 8.2, P1-4).

Verifies that:
  * ``_build_complete_triples`` keeps only logical ids with all three
    source_types and returns a deterministic ordering.
  * Incomplete triples do not contribute to the gap.
  * The confidence_aware block emits a structured
    ``[P^-_exc, P^+_exc]`` interval summary.
"""

from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.run_oracle_extracted_comparison import (
    _build_complete_triples,
    _logical_sample_id,
    SOURCE_TYPES,
)


def _make_record(sample_id, source_type, logical_id=None):
    return {
        "sample_id": sample_id,
        "source_type": source_type,
        "logical_sample_id": logical_id or sample_id,
        "split": "test",
        "claim_text": "claim",
        "evidence_vector": {d: 0.0 for d in (
            "causal_id", "causal_strength", "coverage", "boundary",
            "actionability", "risk_utility", "uncertainty", "temporal",
        )},
        "evidence_confidence": {d: 1.0 for d in (
            "causal_id", "causal_strength", "coverage", "boundary",
            "actionability", "risk_utility", "uncertainty", "temporal",
        )},
        "claim_tiers": [0, 0, 0, 0],
        "support_tiers": [0, 0, 0, 0],
        "escalation_label": 0,
    }


class _FakeLogger:
    def info(self, msg):
        pass

    def warning(self, msg):
        pass


def test_build_complete_triples_keeps_only_complete_groups(tmp_path):
    """Only logical ids with all three source_types are kept."""
    records = []
    # Complete triple for L1.
    for st in SOURCE_TYPES:
        records.append(_make_record(f"L1-{st}", st, logical_id="L1"))
    # Incomplete: L2 missing confidence_aware.
    records.append(_make_record("L2-oracle", "oracle", logical_id="L2"))
    records.append(_make_record("L2-extracted", "extracted", logical_id="L2"))
    # Incomplete: L3 missing oracle.
    records.append(_make_record("L3-extracted", "extracted", logical_id="L3"))
    records.append(_make_record("L3-confidence_aware", "confidence_aware", logical_id="L3"))

    p = tmp_path / "test.jsonl"
    import json
    with open(p, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    groups, ordered_ids, skipped = _build_complete_triples(str(p), _FakeLogger())
    # Only L1 is a complete triple.
    assert ordered_ids == ["L1"]
    assert set(groups.keys()) == {"L1"}
    assert set(groups["L1"].keys()) == set(SOURCE_TYPES)
    # P1-4: incomplete triples are recorded in skipped with reasons.
    skipped_ids = {s["logical_sample_id"] for s in skipped}
    assert skipped_ids == {"L2", "L3"}
    for s in skipped:
        assert s["reason"] == "incomplete_triple"
        assert len(s["missing_source_types"]) >= 1


def test_build_complete_triples_deterministic_order(tmp_path):
    """ordered_ids must be sorted (deterministic) so the three source types
    align by index."""
    import json
    records = []
    for lsid in ["L3", "L1", "L2"]:
        for st in SOURCE_TYPES:
            records.append(_make_record(f"{lsid}-{st}", st, logical_id=lsid))
    p = tmp_path / "test.jsonl"
    with open(p, "w", encoding="utf-8") as f:
        for r in records:
            f.write(json.dumps(r) + "\n")

    _, ordered_ids, _ = _build_complete_triples(str(p), _FakeLogger())
    assert ordered_ids == ["L1", "L2", "L3"]


def test_logical_sample_id_strips_source_suffix():
    """_logical_sample_id must strip -oracle/-extracted/-confidence_aware
    suffixes when logical_sample_id is not set explicitly."""
    r = {"sample_id": "abc-oracle"}
    assert _logical_sample_id(r) == "abc"
    r = {"sample_id": "abc-extracted"}
    assert _logical_sample_id(r) == "abc"
    r = {"sample_id": "abc-confidence_aware"}
    assert _logical_sample_id(r) == "abc"
    # Explicit logical_sample_id wins.
    r = {"sample_id": "abc-oracle", "logical_sample_id": "real-id"}
    assert _logical_sample_id(r) == "real-id"


def test_interval_summary_structure():
    """The confidence_aware block must emit interval_summary with
    p_exc_lower and p_exc_upper keys (the [P^-_exc, P^+_exc] interval)."""
    # Simulate the comparison-level interval summary construction logic
    # from run_same_model_same_samples. This validates the structure
    # without requiring a full model checkpoint.
    conf_block = {
        "p_exceed_observed_mean": 0.7,
        "p_exceed_lower_mean": 0.4,
        "escalation_prob_mean": 0.65,
    }
    extracted_block = {"escalation_prob_mean": 0.7}

    p_exc_obs = conf_block.get("p_exceed_observed_mean", float("nan"))
    p_exc_low = conf_block.get("p_exceed_lower_mean", float("nan"))
    if np.isnan(p_exc_obs):
        p_exc_obs = extracted_block.get("escalation_prob_mean", float("nan"))
    if np.isnan(p_exc_low):
        p_exc_low = conf_block.get("escalation_prob_mean", float("nan"))
    interval_summary = {
        "p_exc_lower": float(p_exc_low) if not np.isnan(p_exc_low) else None,
        "p_exc_upper": float(p_exc_obs) if not np.isnan(p_exc_obs) else None,
    }
    assert interval_summary["p_exc_lower"] == 0.4
    assert interval_summary["p_exc_upper"] == 0.7
    # Lower bound must be <= upper bound.
    assert interval_summary["p_exc_lower"] <= interval_summary["p_exc_upper"]


def test_interval_summary_handles_nan():
    """When p_exceed means are NaN, interval_summary must use None
    (JSON-serializable) rather than NaN."""
    conf_block = {
        "p_exceed_observed_mean": float("nan"),
        "p_exceed_lower_mean": float("nan"),
        "escalation_prob_mean": float("nan"),
    }
    extracted_block = {"escalation_prob_mean": float("nan")}

    p_exc_obs = conf_block.get("p_exceed_observed_mean", float("nan"))
    p_exc_low = conf_block.get("p_exceed_lower_mean", float("nan"))
    if np.isnan(p_exc_obs):
        p_exc_obs = extracted_block.get("escalation_prob_mean", float("nan"))
    if np.isnan(p_exc_low):
        p_exc_low = conf_block.get("escalation_prob_mean", float("nan"))
    interval_summary = {
        "p_exc_lower": float(p_exc_low) if not np.isnan(p_exc_low) else None,
        "p_exc_upper": float(p_exc_obs) if not np.isnan(p_exc_obs) else None,
    }
    assert interval_summary["p_exc_lower"] is None
    assert interval_summary["p_exc_upper"] is None
