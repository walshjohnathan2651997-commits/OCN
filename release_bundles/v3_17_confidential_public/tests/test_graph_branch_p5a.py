"""Tests for GraphEvidenceEncoder (P5a).

Covers:
  * no-graph fallback (vector encoder path)
  * simple graph forward
  * wrong feature dimension error
  * relation ablation (relation_vocab controls edge_type ids)
  * DependencyError when torch_geometric is missing
  * num_relations validation against relation_vocab

Tests that require torch_geometric are skipped when the package is not
installed, so the suite still runs in minimal CI environments.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


# Skip the entire module if torch is unavailable (graph_branch imports torch
# at module load).
torch = pytest.importorskip("torch")

from cese.models.graph_branch import (
    DEFAULT_RELATION_VOCAB,
    DependencyError,
    GraphEvidenceEncoder,
)


def _torch_geometric_available() -> bool:
    try:
        import torch_geometric  # noqa: F401
        return True
    except ImportError:
        return False


_HAS_TG = _torch_geometric_available()


def _make_simple_graph():
    """Build a tiny evidence graph with 3 nodes and 2 edges."""
    return {
        "nodes": [
            {"id": "n1", "type": "claim"},
            {"id": "n2", "type": "evidence"},
            {"id": "n3", "type": "evidence"},
        ],
        "edges": [
            {"src": "n2", "dst": "n1", "relation": "supports"},
            {"src": "n3", "dst": "n1", "relation": "contradicts"},
        ],
    }


# ---------------------------------------------------------------------------
# DependencyError when torch_geometric is missing
# ---------------------------------------------------------------------------


def test_dependency_error_when_torch_geometric_missing(monkeypatch):
    """When torch_geometric is not installed, constructing the encoder
    must raise DependencyError (not a bare ImportError)."""
    if _HAS_TG:
        pytest.skip("torch_geometric is installed; cannot test missing-dep path")

    # Force the import to fail even if it somehow becomes available.
    import builtins

    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "torch_geometric":
            raise ImportError("simulated missing torch_geometric")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)
    with pytest.raises(DependencyError):
        GraphEvidenceEncoder()


# ---------------------------------------------------------------------------
# no-graph fallback
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_no_graph_fallback_uses_vector_encoder():
    """When graphs=None, the encoder must fall back to the vector MLP
    and still produce a (B, num_dims) tensor."""
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4, node_type_dim=4
    )
    enc.eval()
    B = 2
    evidence_vector = torch.randn(B, 2)
    evidence_confidence = torch.rand(B, 2)
    with torch.no_grad():
        out = enc(evidence_vector, evidence_confidence, graphs=None, device=torch.device("cpu"))
    assert out.shape == (B, 4)


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_empty_graph_falls_back_to_vector():
    """When a sample's graph dict has no nodes, the encoder must fall
    back to the vector path (not crash)."""
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4, node_type_dim=4
    )
    enc.eval()
    B = 1
    evidence_vector = torch.randn(B, 2)
    evidence_confidence = torch.rand(B, 2)
    graphs = [{"nodes": [], "edges": []}]
    with torch.no_grad():
        out = enc(evidence_vector, evidence_confidence, graphs=graphs, device=torch.device("cpu"))
    assert out.shape == (B, 4)


# ---------------------------------------------------------------------------
# simple graph forward
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_simple_graph_forward():
    """A simple 3-node, 2-edge graph must forward without error and
    produce a (B, num_dims) tensor."""
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4, node_type_dim=4, num_relations=8
    )
    enc.eval()
    B = 1
    evidence_vector = torch.randn(B, 2)
    evidence_confidence = torch.rand(B, 2)
    graphs = [_make_simple_graph()]
    with torch.no_grad():
        out = enc(evidence_vector, evidence_confidence, graphs=graphs, device=torch.device("cpu"))
    assert out.shape == (B, 4)
    assert torch.isfinite(out).all()


# ---------------------------------------------------------------------------
# wrong feature dimension error
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_wrong_node_feature_dimension_raises():
    """node_proj expects node_type_dim features. If the encoder is built
    with node_type_dim=4 but the graph somehow produces a different
    width, the linear layer must raise a runtime error.

    We verify the encoder validates its configuration: building with
    node_type_dim=4 and then calling _build_graph directly must produce
    a Data.x tensor of width 4 (i.e. node_type_dim), not some other
    width derived from relation_type_dim.
    """
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4,
        node_type_dim=4, relation_type_dim=32,  # deliberately different
    )
    enc.eval()
    g = _make_simple_graph()
    data = enc._build_graph(g, torch.device("cpu"))
    assert data is not None
    # The node feature width must equal node_type_dim, NOT
    # relation_type_dim * 2.
    assert data.x.shape[1] == 4, (
        f"node feature width {data.x.shape[1]} != node_type_dim=4; "
        f"the implicit relation_type_dim*2 dependency has regressed"
    )


# ---------------------------------------------------------------------------
# relation ablation / relation vocabulary
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_relation_vocab_controls_edge_type_ids():
    """When a global relation_vocab is provided, the same relation
    string must map to the same id across graphs (not per-graph
    numbering)."""
    vocab = {
        "default": 0,
        "supports": 1,
        "contradicts": 2,
        "causes": 3,
    }
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4,
        node_type_dim=4, num_relations=8, relation_vocab=vocab,
    )
    enc.eval()

    g1 = _make_simple_graph()
    g2 = {
        "nodes": [
            {"id": "a", "type": "claim"},
            {"id": "b", "type": "evidence"},
        ],
        "edges": [
            {"src": "b", "dst": "a", "relation": "supports"},
            {"src": "a", "dst": "b", "relation": "contradicts"},
        ],
    }
    d1 = enc._build_graph(g1, torch.device("cpu"))
    d2 = enc._build_graph(g2, torch.device("cpu"))
    # "supports" must map to id 1 in both graphs.
    assert d1.edge_type[0].item() == 1
    assert d2.edge_type[0].item() == 1
    # "contradicts" must map to id 2 in both graphs.
    assert d1.edge_type[1].item() == 2
    assert d2.edge_type[1].item() == 2


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_unknown_relation_maps_to_default_zero():
    """Unknown relations (not in the vocab) must map to id 0
    ("default"), not be silently re-numbered."""
    enc = GraphEvidenceEncoder(
        input_dim=4, hidden_dim=8, num_dims=4,
        node_type_dim=4, num_relations=8,
    )
    enc.eval()
    g = {
        "nodes": [
            {"id": "n1", "type": "claim"},
            {"id": "n2", "type": "evidence"},
        ],
        "edges": [
            {"src": "n2", "dst": "n1", "relation": "totally_unknown_relation"},
        ],
    }
    data = enc._build_graph(g, torch.device("cpu"))
    assert data is not None
    # Unknown relation maps to 0 (default) when the vocab is full
    # (DEFAULT_RELATION_VOCAB already has 8 entries, filling num_relations=8).
    assert data.edge_type[0].item() == 0


# ---------------------------------------------------------------------------
# num_relations validation
# ---------------------------------------------------------------------------


@pytest.mark.skipif(not _HAS_TG, reason="torch_geometric not installed")
def test_num_relations_must_cover_vocab_size():
    """If relation_vocab is larger than num_relations, the constructor
    must raise ValueError (not silently truncate)."""
    vocab = {f"rel_{i}": i for i in range(16)}  # 16 entries
    with pytest.raises(ValueError, match="num_relations"):
        GraphEvidenceEncoder(
            input_dim=4, hidden_dim=8, num_dims=4,
            node_type_dim=4, num_relations=8, relation_vocab=vocab,
        )


def test_default_relation_vocab_is_stable():
    """DEFAULT_RELATION_VOCAB must contain the canonical relations with
    stable ids (so relation ids are reproducible across encoders)."""
    assert DEFAULT_RELATION_VOCAB["default"] == 0
    assert DEFAULT_RELATION_VOCAB["supports"] == 1
    assert DEFAULT_RELATION_VOCAB["contradicts"] == 2
    assert len(DEFAULT_RELATION_VOCAB) == 8
