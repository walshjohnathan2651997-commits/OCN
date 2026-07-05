"""Tests for scripts/build_paper_splits.py.

P1e: verify that the paper split builder produces valid splits with
no template/domain leakage and sufficient overclaim positives.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

sys.path.insert(0, str(ROOT / "scripts"))
import importlib.util

_spec = importlib.util.spec_from_file_location(
    "build_paper_splits", ROOT / "scripts" / "build_paper_splits.py"
)
bps = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bps)


def _make_records(n: int = 60, n_templates: int = 3, n_domains: int = 3) -> list:
    """Generate test records with enough templates/domains for holdout."""
    records = []
    for i in range(n):
        records.append({
            "sample_id": f"r{i:04d}",
            "logical_sample_id": f"r{i:04d}",
            "domain": f"domain_{i % n_domains}",
            "source_type": "oracle",
            "claim_text": f"claim {i}",
            "evidence_text": f"evidence {i}",
            "evidence_vector": {d: 0.5 for d in [
                "alignment", "transparency", "coverage", "traceability",
                "boundary", "uncertainty", "causal_id", "risk_utility",
            ]},
            "evidence_confidence": {d: 1.0 for d in [
                "alignment", "transparency", "coverage", "traceability",
                "boundary", "uncertainty", "causal_id", "risk_utility",
            ]},
            "claim_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
            "support_tiers": {"scope": 0, "causal": 0, "action": 0, "certainty": 0},
            "escalation_label": i % 2,  # alternating pos/neg
            "escalation_type": ["scope"] if i % 2 == 1 else [],
            "evidence_gap_labels": [],
            "split": "train",
            "template_id": f"tpl_{i % n_templates}",
            "claim_family": "descriptive",
        })
    return records


def test_build_all_splits_produces_four_variants():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    assert "standard" in result["splits"]
    assert "lexical_adversarial" in result["splits"]
    assert "template_heldout" in result["splits"]
    assert "domain_heldout" in result["splits"]


def test_template_heldout_has_no_leakage():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    manifest = result["manifest"]
    assert manifest["template_heldout"]["template_leakage"]["has_leakage"] is False
    assert manifest["template_heldout"]["template_leakage"]["n_leaked"] == 0


def test_domain_heldout_has_no_leakage():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    manifest = result["manifest"]
    assert manifest["domain_heldout"]["domain_leakage"]["has_leakage"] is False
    assert manifest["domain_heldout"]["domain_leakage"]["n_leaked"] == 0


def test_standard_split_has_pos_neg():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    manifest = result["manifest"]
    for side in ("train", "dev", "test"):
        info = manifest["standard"][side]
        # At least one of each class (dev/test may be small but must have both).
        if info["n"] > 0:
            assert info["n_positive"] > 0, f"{side} has no positives"
            assert info["n_negative"] > 0, f"{side} has no negatives"


def test_template_heldout_train_excludes_heldout():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    splits = result["splits"]
    heldout = set(result["manifest"]["template_heldout"]["heldout_templates"])
    train_templates = {r["template_id"] for r in splits["template_heldout"]["train"]}
    test_templates = {r["template_id"] for r in splits["template_heldout"]["test"]}
    # Held-out templates must be in test, not in train.
    assert heldout.issubset(test_templates)
    assert heldout.isdisjoint(train_templates)


def test_domain_heldout_train_excludes_heldout():
    records = _make_records(n=60, n_templates=3, n_domains=3)
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    splits = result["splits"]
    heldout = set(result["manifest"]["domain_heldout"]["heldout_domains"])
    train_domains = {r["domain"] for r in splits["domain_heldout"]["train"]}
    test_domains = {r["domain"] for r in splits["domain_heldout"]["test"]}
    assert heldout.issubset(test_domains)
    assert heldout.isdisjoint(train_domains)


def test_manifest_reports_issues():
    """When splits have issues, manifest.issues should list them."""
    # Single-class records: all escalation_label=0.
    records = _make_records(n=60, n_templates=3, n_domains=3)
    for r in records:
        r["escalation_label"] = 0
        r["escalation_type"] = []
    result = bps.build_all_splits(records, n_template_holdout=1, n_domain_holdout=1)
    assert len(result["manifest"]["issues"]) > 0
    assert result["manifest"]["passed"] is False
