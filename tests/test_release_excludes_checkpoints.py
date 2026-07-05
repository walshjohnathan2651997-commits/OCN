"""Tests that model checkpoints are excluded from the release bundle
(ocn-33 P2-9).

Verifies:
  * ``release/`` contains no ``.pt`` / ``.pth`` / ``.ckpt`` files.
  * ``release/`` contains no ``optimizer_state*`` / ``scheduler_state*`` /
    ``resume_state*`` files.
  * ``RESULTS_MANIFEST.json`` declares a ``checkpoint_policy`` field with
    ``excluded_from_release=true``.
  * ``RESULTS_MANIFEST.json`` does not list any ``.pt`` path as a
    deliverable artifact.
  * ``build_release_bundle.assert_no_checkpoints_in_release`` raises
    ``RuntimeError`` when a checkpoint is placed under ``release/``.
  * ``build_release_bundle._is_excluded`` returns True for all checkpoint
    suffixes and resume-state filenames.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

RELEASE_DIR = ROOT / "release"
MANIFEST_PATH = RELEASE_DIR / "RESULTS_MANIFEST.json"

# All suffixes that count as "model checkpoint" for the release guard.
_CHECKPOINT_SUFFIXES = {".pt", ".pth", ".ckpt", ".bin"}
# All filenames that are resume/optimizer state even with unusual suffix.
_STATE_FILENAMES = {
    "optimizer_state.pt",
    "optimizer_state.pth",
    "scheduler_state.pt",
    "scheduler_state.pth",
    "resume_state.pt",
    "resume_state.pth",
}


# ---------------------------------------------------------------------
# 1. release/ directory must not contain checkpoints
# ---------------------------------------------------------------------

def test_release_dir_has_no_pt_files():
    """No .pt/.pth/.ckpt/.bin files under release/."""
    if not RELEASE_DIR.exists():
        pytest.skip("release/ not built yet")
    found: list = []
    for p in RELEASE_DIR.rglob("*"):
        if p.is_file() and p.suffix in _CHECKPOINT_SUFFIXES:
            found.append(str(p.relative_to(RELEASE_DIR)))
    assert not found, (
        "release/ must not contain model checkpoints (ocn-33 P2-9). "
        "Found:\n  " + "\n  ".join(found)
    )


def test_release_dir_has_no_resume_state_files():
    """No optimizer_state*/scheduler_state*/resume_state* under release/."""
    if not RELEASE_DIR.exists():
        pytest.skip("release/ not built yet")
    found: list = []
    for p in RELEASE_DIR.rglob("*"):
        if p.is_file() and p.name in _STATE_FILENAMES:
            found.append(str(p.relative_to(RELEASE_DIR)))
    assert not found, (
        "release/ must not contain optimizer/scheduler/resume state files "
        "(ocn-33 P2-9). Found:\n  " + "\n  ".join(found)
    )


def test_release_dir_size_is_small():
    """release/ total size must be well under 100MB (no checkpoints).

    A clean release bundle is typically < 5MB (tables + predictions +
    manifest). If it exceeds 50MB, a checkpoint likely leaked in.
    """
    if not RELEASE_DIR.exists():
        pytest.skip("release/ not built yet")
    total = sum(p.stat().st_size for p in RELEASE_DIR.rglob("*") if p.is_file())
    total_mb = total / (1024 * 1024)
    assert total_mb < 50, (
        f"release/ is {total_mb:.1f}MB — likely contains a leaked "
        f"checkpoint (expected < 50MB). Check for *.pt/*.pth/*.ckpt."
    )


# ---------------------------------------------------------------------
# 2. RESULTS_MANIFEST.json must declare checkpoint_policy
# ---------------------------------------------------------------------

@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip(f"{MANIFEST_PATH} not built yet")
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def test_manifest_has_checkpoint_policy(manifest: dict):
    """RESULTS_MANIFEST.json must declare checkpoint_policy."""
    cp = manifest.get("checkpoint_policy")
    assert isinstance(cp, dict), (
        "manifest.checkpoint_policy must be a dict (ocn-33 P2-9)"
    )


def test_manifest_checkpoint_policy_excluded_from_release(manifest: dict):
    """checkpoint_policy.excluded_from_release must be True."""
    cp = manifest.get("checkpoint_policy", {})
    assert cp.get("excluded_from_release") is True, (
        "checkpoint_policy.excluded_from_release must be True — model "
        "weights never ship in the release bundle"
    )


def test_manifest_checkpoint_policy_save_final_false(manifest: dict):
    """checkpoint_policy.save_final must be False (pilot/release)."""
    cp = manifest.get("checkpoint_policy", {})
    assert cp.get("save_final") is False, (
        "checkpoint_policy.save_final must be False for pilot/release runs"
    )


def test_manifest_checkpoint_policy_save_optimizer_false(manifest: dict):
    """checkpoint_policy.save_optimizer must be False (best.pt is model-only)."""
    cp = manifest.get("checkpoint_policy", {})
    assert cp.get("save_optimizer") is False, (
        "checkpoint_policy.save_optimizer must be False — optimizer state "
        "bloats checkpoints and is not needed for eval"
    )


def test_manifest_does_not_list_pt_as_deliverable(manifest: dict):
    """No manifest field should list a .pt path as a release deliverable."""
    # Check the canonical artifact-listing fields. checkpoint_path is a
    # build-time INPUT (path to best.pt under outputs/), not a release
    # deliverable — it must NOT point into release/.
    forbidden_fields = [
        "predictions_path",
        "data_path",
        "config_path",
        "best_model_path",
        "final_model_path",
    ]
    for field in forbidden_fields:
        val = manifest.get(field)
        if val is None:
            continue
        val_str = str(val).replace("\\", "/")
        # checkpoint_path may legitimately point at outputs/...best.pt
        # (a build-time input); only flag if it points into release/.
        if "release/" in val_str and val_str.endswith(
            (".pt", ".pth", ".ckpt", ".bin")
        ):
            pytest.fail(
                f"manifest.{field}={val!r} points at a checkpoint inside "
                f"release/ — checkpoints must not ship in the bundle"
            )


def test_manifest_excluded_artifacts_lists_pt_pth_ckpt(manifest: dict):
    """manifest.excluded_artifacts must list .pt/.pth/.ckpt patterns."""
    excluded = manifest.get("excluded_artifacts", [])
    joined = "\n".join(excluded)
    assert "*.pt" in joined, (
        f"excluded_artifacts must list *.pt patterns: {excluded}"
    )
    assert "*.pth" in joined, (
        f"excluded_artifacts must list *.pth patterns: {excluded}"
    )
    assert "*.ckpt" in joined, (
        f"excluded_artifacts must list *.ckpt patterns: {excluded}"
    )


# ---------------------------------------------------------------------
# 3. build_release_bundle guard function unit tests
# ---------------------------------------------------------------------

def test_is_excluded_pt_pth_ckpt_bin():
    """_is_excluded returns True for all checkpoint suffixes."""
    from scripts.build_release_bundle import _is_excluded
    for suffix in [".pt", ".pth", ".ckpt", ".bin"]:
        p = Path(f"model{suffix}")
        assert _is_excluded(p), f"_is_excluded must reject {suffix}"


def test_is_excluded_resume_state_filenames():
    """_is_excluded returns True for optimizer/scheduler/resume state files."""
    from scripts.build_release_bundle import _is_excluded
    for name in _STATE_FILENAMES:
        p = Path(name)
        assert _is_excluded(p), f"_is_excluded must reject {name}"


def test_is_excluded_allows_md_csv_json():
    """_is_excluded returns False for normal release files."""
    from scripts.build_release_bundle import _is_excluded
    for name in [
        "main_results.md",
        "predictions.csv",
        "RESULTS_MANIFEST.json",
        "test_predictions.jsonl",
    ]:
        p = Path(name)
        assert not _is_excluded(p), (
            f"_is_excluded must NOT reject normal release file {name}"
        )


def test_assert_no_checkpoints_passes_on_clean_dir(tmp_path: Path):
    """assert_no_checkpoints_in_release passes when no checkpoints exist."""
    from scripts.build_release_bundle import assert_no_checkpoints_in_release
    # Empty dir is fine.
    assert_no_checkpoints_in_release(tmp_path)
    # Dir with normal files is fine.
    (tmp_path / "main_results.md").write_text("ok", encoding="utf-8")
    (tmp_path / "predictions").mkdir()
    (tmp_path / "predictions" / "test_predictions.jsonl").write_text(
        "{}", encoding="utf-8"
    )
    assert_no_checkpoints_in_release(tmp_path)


def test_assert_no_checkpoints_fails_on_pt(tmp_path: Path):
    """assert_no_checkpoints_in_release raises on .pt files."""
    from scripts.build_release_bundle import assert_no_checkpoints_in_release
    (tmp_path / "best.pt").write_bytes(b"fake checkpoint")
    with pytest.raises(RuntimeError, match="model checkpoints are excluded"):
        assert_no_checkpoints_in_release(tmp_path)


def test_assert_no_checkpoints_fails_on_pth(tmp_path: Path):
    """assert_no_checkpoints_in_release raises on .pth files."""
    from scripts.build_release_bundle import assert_no_checkpoints_in_release
    (tmp_path / "model_weights.pth").write_bytes(b"fake weights")
    with pytest.raises(RuntimeError, match="model checkpoints are excluded"):
        assert_no_checkpoints_in_release(tmp_path)


def test_assert_no_checkpoints_fails_on_resume_state(tmp_path: Path):
    """assert_no_checkpoints_in_release raises on resume_state.pt files."""
    from scripts.build_release_bundle import assert_no_checkpoints_in_release
    (tmp_path / "resume_state.pt").write_bytes(b"fake optimizer state")
    with pytest.raises(RuntimeError, match="model checkpoints are excluded"):
        assert_no_checkpoints_in_release(tmp_path)


def test_assert_no_checkpoints_fails_on_nested_ckpt(tmp_path: Path):
    """assert_no_checkpoints_in_release raises on nested .ckpt files."""
    from scripts.build_release_bundle import assert_no_checkpoints_in_release
    nested = tmp_path / "models" / "deep"
    nested.mkdir(parents=True)
    (nested / "epoch_10.ckpt").write_bytes(b"fake checkpoint")
    with pytest.raises(RuntimeError, match="model checkpoints are excluded"):
        assert_no_checkpoints_in_release(tmp_path)


# ---------------------------------------------------------------------
# 4. train_cese_ocn.py checkpoint policy defaults
# ---------------------------------------------------------------------

def test_config_model_clean_v2_has_checkpoint_block():
    """configs/model_clean_v2.yaml must declare a checkpoint block."""
    import yaml
    cfg_path = ROOT / "configs" / "model_clean_v2.yaml"
    if not cfg_path.exists():
        pytest.skip(f"{cfg_path} not present")
    with cfg_path.open(encoding="utf-8") as f:
        cfg = yaml.safe_load(f) or {}
    assert "checkpoint" in cfg, (
        "configs/model_clean_v2.yaml must have a top-level 'checkpoint' "
        "block (ocn-33 P2-9)"
    )
    cp = cfg["checkpoint"]
    assert cp.get("save_best") is True
    assert cp.get("save_final") is False
    assert cp.get("save_optimizer") is False
    assert cp.get("exclude_from_release") is True
    assert cp.get("max_checkpoints") == 1
