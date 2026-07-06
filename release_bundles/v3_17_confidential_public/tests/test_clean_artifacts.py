"""Tests for scripts/clean_artifacts.py.

P0 (ocn-25): verify that after running clean_artifacts.py --all, the
repo does not残留 pycache, pytest cache, checkpoints, logs, or stale
outputs (but .gitkeep is preserved).
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.clean_artifacts import (
    clean_caches,
    clean_checkpoints,
    clean_outputs,
    clean_derived,
    clean_logs,
)


class _NullLogger:
    """Minimal logger stub that discards all output."""
    def info(self, msg): pass
    def warning(self, msg): pass
    def error(self, msg): pass


def _make_fake_repo(tmp_path: Path) -> Path:
    """Create a fake repo tree with all the artifact types we clean."""
    root = tmp_path / "fake_repo"
    root.mkdir()

    # __pycache__ / .pytest_cache
    (root / "cese" / "__pycache__").mkdir(parents=True)
    (root / "cese" / "__pycache__" / "mod.cpython-310.pyc").write_bytes(b"")
    (root / "scripts" / "__pycache__").mkdir(parents=True)
    (root / "scripts" / "__pycache__" / "run.cpython-310.pyc").write_bytes(b"")
    (root / ".pytest_cache").mkdir()
    (root / ".pytest_cache" / "v").mkdir()
    (root / ".pytest_cache" / "v" / "cache").write_bytes(b"{}")

    # outputs/ with .gitkeep + artifacts
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    (root / "outputs" / "train").mkdir(parents=True)
    (root / "outputs" / "train" / "best.pt").write_bytes(b"weights")
    (root / "outputs" / "run.log").write_text("log")
    (root / "outputs" / "results.json").write_text("{}")

    # data/derived/
    (root / "data" / "derived").mkdir(parents=True)
    (root / "data" / "derived" / "test_lexical_adv.jsonl").write_text("{}")

    # Global *.log outside outputs/
    (root / "debug.log").write_text("debug")

    return root


def test_clean_caches_removes_pycache_and_pytest_cache(tmp_path):
    root = _make_fake_repo(tmp_path)
    logger = _NullLogger()
    n = clean_caches(root, logger)
    assert n >= 3  # cese/__pycache__, scripts/__pycache__, .pytest_cache
    assert not (root / "cese" / "__pycache__").exists()
    assert not (root / "scripts" / "__pycache__").exists()
    assert not (root / ".pytest_cache").exists()


def test_clean_checkpoints_removes_pt_files(tmp_path):
    root = _make_fake_repo(tmp_path)
    logger = _NullLogger()
    n = clean_checkpoints(root, logger)
    assert n >= 1
    assert not (root / "outputs" / "train" / "best.pt").exists()
    # results.json should still exist (preserved)
    assert (root / "outputs" / "results.json").exists()


def test_clean_outputs_removes_everything_except_gitkeep(tmp_path):
    root = _make_fake_repo(tmp_path)
    logger = _NullLogger()
    n = clean_outputs(root, logger)
    assert n >= 3  # train/, run.log, results.json
    assert (root / "outputs" / ".gitkeep").exists()
    assert not (root / "outputs" / "train").exists()
    assert not (root / "outputs" / "run.log").exists()


def test_clean_derived_removes_derived_data(tmp_path):
    root = _make_fake_repo(tmp_path)
    logger = _NullLogger()
    n = clean_derived(root, logger)
    assert n >= 1
    assert not (root / "data" / "derived" / "test_lexical_adv.jsonl").exists()


def test_clean_logs_removes_global_log_files(tmp_path):
    root = _make_fake_repo(tmp_path)
    logger = _NullLogger()
    n = clean_logs(root, logger)
    assert n >= 2  # outputs/run.log + debug.log
    assert not (root / "debug.log").exists()


def test_clean_all_via_main_preserves_gitkeep(tmp_path):
    """Running clean_artifacts --all should leave outputs/.gitkeep."""
    from scripts.clean_artifacts import main as clean_main
    root = _make_fake_repo(tmp_path)
    rc = clean_main(["--all", "--root", str(root)])
    assert rc == 0
    assert (root / "outputs" / ".gitkeep").exists()
    assert not (root / "cese" / "__pycache__").exists()
    assert not (root / ".pytest_cache").exists()
    assert not (root / "outputs" / "train" / "best.pt").exists()
    assert not (root / "data" / "derived" / "test_lexical_adv.jsonl").exists()
    assert not (root / "debug.log").exists()
