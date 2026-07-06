"""Tests for P6-14: scripts/check_release_hygiene.py.

Covers:
- Hygiene check fails when forbidden artifacts (pycache/log/pt/pyc)
  are present.
- Hygiene check passes after clean_artifacts.py --all removes them.
- Real user data files (data/pilot_*.jsonl) are NOT flagged or deleted.
- Hygiene check fails on outputs/ non-.gitkeep files.
- Hygiene check fails on stale release/ artifacts.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(cmd: list[str], cwd: Path = ROOT, timeout: int = 60):
    return subprocess.run(
        cmd, cwd=str(cwd), capture_output=True, text=True, timeout=timeout,
    )


def test_hygiene_fails_when_pycache_present(tmp_path):
    """A __pycache__ directory triggers a violation."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__pycache__").mkdir()
    (root / "cese" / "__pycache__" / "x.pyc").write_text("")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0, (
        f"expected failure but got rc=0\nstdout:{code.stdout}\nstderr:{code.stderr}"
    )
    assert "__pycache__" in code.stdout or "__pycache__" in code.stderr


def test_hygiene_fails_when_log_present(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "run.log").write_text("log line\n")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0


def test_hygiene_fails_when_pt_present(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "model.pt").write_text("weights")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0


def test_hygiene_fails_when_pyc_present(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    (root / "module.pyc").write_text("")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0


def test_hygiene_passes_on_clean_repo(tmp_path):
    """A clean repo with source files only passes."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "cese" / "model.py").write_text("x = 1\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "train.py").write_text("print('hi')\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): assert True\n")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode == 0, (
        f"expected pass but got rc={code.returncode}\n"
        f"stdout:{code.stdout}\nstderr:{code.stderr}"
    )


def test_hygiene_fails_on_outputs_non_gitkeep(tmp_path):
    """outputs/ files other than .gitkeep are flagged."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    (root / "outputs" / "eval.json").write_text("{}")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0


def test_hygiene_outputs_gitkeep_only_passes(tmp_path):
    """outputs/ with only .gitkeep passes."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode == 0


def test_hygiene_fails_on_stale_release_artifact(tmp_path):
    """release/ stale files (non-manifest/template) are flagged."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "release").mkdir()
    (root / "release" / "RESULTS_MANIFEST.json").write_text("{}")
    (root / "release" / "stale.pt").write_text("weights")
    code = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert code.returncode != 0


def test_clean_then_hygiene_passes(tmp_path):
    """After clean_artifacts.py --all, hygiene check must pass."""
    root = tmp_path / "repo"
    root.mkdir()
    # Mirror minimal repo structure.
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "scripts").mkdir()
    (root / "scripts" / "train.py").write_text("print('hi')\n")
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    # Forbidden artifacts. Checkpoints (*.pt) live under outputs/ (the
    # only place clean_artifacts --checkpoints scans).
    (root / "cese" / "__pycache__").mkdir()
    (root / "cese" / "__pycache__" / "x.pyc").write_text("")
    (root / "run.log").write_text("log\n")
    (root / "outputs" / "model.pt").write_text("w")
    (root / "outputs" / "eval.json").write_text("{}")
    # Run clean.
    clean = _run([
        sys.executable, "-u", "scripts/clean_artifacts.py", "--all",
        "--root", str(root),
    ], timeout=60)
    assert clean.returncode == 0, clean.stderr
    # Now hygiene should pass.
    hyg = _run([
        sys.executable, "-u", "scripts/check_release_hygiene.py",
        "--root", str(root),
    ])
    assert hyg.returncode == 0, (
        f"hygiene failed after clean\nstdout:{hyg.stdout}\nstderr:{hyg.stderr}"
    )


def test_clean_does_not_delete_user_data(tmp_path):
    """clean_artifacts.py --all must NOT delete data/pilot_*.jsonl."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "data").mkdir()
    pilot_file = root / "data" / "pilot_all.jsonl"
    pilot_file.write_text('{"sample_id": "p1"}\n')
    (root / "cese" / "__pycache__").mkdir()
    (root / "cese" / "__pycache__" / "x.pyc").write_text("")
    clean = _run([
        sys.executable, "-u", "scripts/clean_artifacts.py", "--all",
        "--root", str(root),
    ], timeout=60)
    assert clean.returncode == 0
    # User data must survive.
    assert pilot_file.exists(), "clean deleted user pilot data!"
    assert pilot_file.read_text() == '{"sample_id": "p1"}\n'


# ---------------------------------------------------------------------------
# build_release_zip.py: pre-flight gate + clean zip
# ---------------------------------------------------------------------------


def test_build_release_zip_fails_on_dirty_tree(tmp_path):
    """build_release_zip.py must refuse to build when hygiene check fails
    after clean. We place a checkpoint .pt file at the repo ROOT (not
    under outputs/) so clean_artifacts --checkpoints (which only scans
    outputs/) cannot remove it, and hygiene must flag it."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "scripts").mkdir()
    (root / "scripts" / "train.py").write_text("print('hi')\n")
    # A checkpoint at repo root: clean_artifacts --checkpoints only scans
    # outputs/**, so this survives clean. Hygiene flags *.pt anywhere.
    (root / "stale_model.pt").write_text("weights")
    out_zip = tmp_path / "out.zip"
    code = _run([
        sys.executable, "-u", "scripts/build_release_zip.py",
        "--root", str(root), "--out", str(out_zip),
    ], timeout=60)
    # Must refuse to build (hygiene failed on the .pt file).
    assert code.returncode != 0, (
        f"expected build to fail on dirty tree but got rc=0\n"
        f"stdout:{code.stdout}\nstderr:{code.stderr}"
    )
    assert not out_zip.exists(), "zip was created despite dirty tree"


def test_build_release_zip_succeeds_on_clean_tree(tmp_path):
    """build_release_zip.py builds a clean zip on a clean tree. The zip
    must contain source files but NOT forbidden artifacts, and must
    preserve user pilot data files."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "cese" / "model.py").write_text("x = 1\n")
    (root / "scripts").mkdir()
    (root / "scripts" / "train.py").write_text("print('hi')\n")
    (root / "tests").mkdir()
    (root / "tests" / "test_x.py").write_text("def test_x(): assert True\n")
    (root / "data").mkdir()
    pilot_file = root / "data" / "pilot_all.jsonl"
    pilot_file.write_text('{"sample_id": "p1"}\n')
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    out_zip = tmp_path / "out.zip"
    code = _run([
        sys.executable, "-u", "scripts/build_release_zip.py",
        "--root", str(root), "--out", str(out_zip),
    ], timeout=60)
    assert code.returncode == 0, (
        f"expected build to succeed but got rc={code.returncode}\n"
        f"stdout:{code.stdout}\nstderr:{code.stderr}"
    )
    assert out_zip.exists(), "zip was not created"
    # Inspect contents: source files present, no forbidden artifacts.
    import zipfile
    with zipfile.ZipFile(out_zip, "r") as zf:
        names = zf.namelist()
    assert "cese/__init__.py" in names
    assert "cese/model.py" in names
    assert "scripts/train.py" in names
    assert "data/pilot_all.jsonl" in names, "user pilot data was excluded!"
    # No forbidden artifacts.
    forbidden = [n for n in names if
                 n.endswith(".pyc") or n.endswith(".log") or
                 n.endswith(".pt") or "__pycache__" in n or
                 n == "outputs/eval.json"]
    assert forbidden == [], f"forbidden artifacts leaked into zip: {forbidden}"


def test_build_release_zip_excludes_outputs_non_gitkeep(tmp_path):
    """Even after clean + hygiene, build must defensively exclude any
    outputs/ file that is not .gitkeep (in case a race regenerated one)."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "outputs").mkdir()
    (root / "outputs" / ".gitkeep").write_text("")
    (root / "outputs" / "eval.json").write_text("{}")
    out_zip = tmp_path / "out.zip"
    # --skip_clean so hygiene doesn't fail on the eval.json first; we
    # want to verify the zip-level exclusion defense.
    code = _run([
        sys.executable, "-u", "scripts/build_release_zip.py",
        "--root", str(root), "--out", str(out_zip), "--skip_clean",
    ], timeout=60)
    assert code.returncode == 0
    import zipfile
    with zipfile.ZipFile(out_zip, "r") as zf:
        names = zf.namelist()
    assert "outputs/.gitkeep" in names
    assert "outputs/eval.json" not in names, "outputs/eval.json leaked"


def test_build_release_zip_preserves_user_data(tmp_path):
    """build_release_zip.py must include data/pilot_*.jsonl and
    data/templates/* files in the zip (never exclude user data)."""
    root = tmp_path / "repo"
    root.mkdir()
    (root / "cese").mkdir()
    (root / "cese" / "__init__.py").write_text("")
    (root / "data").mkdir()
    (root / "data" / "pilot_all.jsonl").write_text('{"sample_id": "p1"}\n')
    (root / "data" / "pilot_split").mkdir()
    (root / "data" / "pilot_split" / "train.jsonl").write_text(
        '{"sample_id": "p2"}\n'
    )
    (root / "data" / "templates").mkdir()
    (root / "data" / "templates" / "tpl1.json").write_text("{}")
    out_zip = tmp_path / "out.zip"
    code = _run([
        sys.executable, "-u", "scripts/build_release_zip.py",
        "--root", str(root), "--out", str(out_zip), "--skip_clean",
    ], timeout=60)
    assert code.returncode == 0
    import zipfile
    with zipfile.ZipFile(out_zip, "r") as zf:
        names = zf.namelist()
    assert "data/pilot_all.jsonl" in names
    assert "data/pilot_split/train.jsonl" in names
    assert "data/templates/tpl1.json" in names
