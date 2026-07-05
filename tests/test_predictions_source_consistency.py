"""Tests that main_results and error_analysis read the same predictions
source (ocn-33 P2-7 / P1-5).

Verifies:
  * ``release/RESULTS_MANIFEST.json`` declares a single
    ``predictions_path`` pointing to ``test_predictions.jsonl``.
  * ``release/error_analysis.md`` references the same operating threshold
    as the manifest, and its operating-threshold row's F1 matches
    ``release/tables/main_results.md`` escalation_f1 for CESE-OCN full.
  * The operating threshold equals best_threshold_on_dev (no test tuning).
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

MANIFEST_PATH = ROOT / "release" / "RESULTS_MANIFEST.json"
MAIN_RESULTS_PATH = ROOT / "release" / "tables" / "main_results.md"
ERROR_ANALYSIS_PATH = ROOT / "release" / "error_analysis.md"


@pytest.fixture(scope="module")
def manifest() -> dict:
    if not MANIFEST_PATH.exists():
        pytest.skip(f"manifest not found at {MANIFEST_PATH}")
    with MANIFEST_PATH.open(encoding="utf-8") as f:
        return json.load(f)


def _read_text(path: Path) -> str:
    if not path.exists():
        pytest.skip(f"{path} not present")
    return path.read_text(encoding="utf-8")


def test_manifest_declares_single_predictions_path(manifest: dict):
    """Manifest must declare exactly one predictions_path."""
    pp = manifest.get("predictions_path")
    assert pp, "manifest.predictions_path must be set"
    assert "test_predictions.jsonl" in str(pp), (
        f"predictions_path must point to test_predictions.jsonl, got: {pp!r}"
    )
    # predictions_sha256 must be set so the file is content-addressed.
    assert manifest.get("predictions_sha256"), (
        "manifest.predictions_sha256 must be set (content-address the file)"
    )


def test_operating_threshold_equals_best_threshold_on_dev(manifest: dict):
    """operating_threshold must equal best_threshold_on_dev (no test tuning)."""
    op = manifest.get("operating_threshold")
    best = manifest.get("best_threshold_on_dev")
    assert op is not None and best is not None, (
        "operating_threshold and best_threshold_on_dev must both be set"
    )
    assert op == best, (
        f"operating_threshold ({op}) must equal best_threshold_on_dev ({best}); "
        "test_threshold_tuning_used must be False"
    )


def test_test_threshold_tuning_used_is_false(manifest: dict):
    """test_threshold_tuning_used must be False."""
    assert manifest.get("test_threshold_tuning_used") is False


def test_error_analysis_uses_same_operating_threshold(manifest: dict):
    """error_analysis.md must reference the manifest's operating_threshold.

    The error_analysis.md must contain an explicit operating-threshold row
    in its sweep table whose threshold matches the manifest's
    operating_threshold (so reviewers can see main_results and
    error_analysis use the SAME threshold).
    """
    ea_text = _read_text(ERROR_ANALYSIS_PATH)
    op = manifest.get("operating_threshold")
    assert op is not None
    # Look for the explicit operating-threshold row marker we added in
    # error_analysis.py (_write_release_md): a line like
    #   "> Row above: operating_threshold=0.3250 (fit on dev, NOT tuned on test)."
    m = re.search(
        r"operating_threshold=([0-9.]+)",
        ea_text,
    )
    assert m, (
        "error_analysis.md must contain an explicit operating_threshold row "
        "(added by _write_release_md when --operating_threshold is passed)"
    )
    ea_op = float(m.group(1))
    assert abs(ea_op - op) < 1e-6, (
        f"error_analysis.md operating_threshold ({ea_op}) must match "
        f"manifest.operating_threshold ({op})"
    )


def test_main_results_f1_matches_error_analysis_operating_threshold_f1(
    manifest: dict,
):
    """The F1 at operating_threshold must be the same in both deliverables.

    main_results.md escalation_f1 (CESE-OCN full row) must equal the F1
    in error_analysis.md's operating-threshold sweep row. Both must be
    computed from the SAME test_predictions.jsonl.
    """
    main_text = _read_text(MAIN_RESULTS_PATH)
    ea_text = _read_text(ERROR_ANALYSIS_PATH)

    # Extract escalation_f1 from main_results.md CESE-OCN full row.
    # The row looks like:
    #   | CESE-OCN full | 0.5625 | 0.4589... | <escalation_f1> | ... |
    main_f1 = None
    for line in main_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        if "CESE-OCN full" not in line:
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        # Find a numeric cell that looks like an F1 in [0, 1].
        # Columns: model | accuracy | macro_f1 | escalation_f1 | ...
        # escalation_f1 is the 4th column (index 3).
        if len(cells) >= 4:
            try:
                main_f1 = float(cells[3])
            except ValueError:
                # Fall back: scan for the first float in [0, 1] after
                # accuracy / macro_f1 (which are also in [0, 1]).
                pass
        break
    assert main_f1 is not None, (
        "could not extract escalation_f1 from main_results.md CESE-OCN full row"
    )

    # Extract F1 from error_analysis.md operating-threshold row.
    # The row looks like:
    #   | 0.3250 | 1 | 0 | 7 | 8 | 1.0000 | 0.1250 | <f1> | ... |
    # We match the row whose first cell is the manifest operating_threshold.
    op = manifest.get("operating_threshold")
    ea_f1 = None
    for line in ea_text.splitlines():
        if not line.lstrip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) < 8:
            continue
        try:
            row_thr = float(cells[0])
        except ValueError:
            continue
        if abs(row_thr - op) < 1e-6:
            # cells: threshold | tp | fp | fn | tn | precision | recall | f1 | ...
            try:
                ea_f1 = float(cells[7])
            except ValueError:
                pass
            break
    assert ea_f1 is not None, (
        f"could not find operating-threshold row in error_analysis.md "
        f"with threshold={op}"
    )

    # error_analysis.md rounds to 4 decimals (e.g. 0.2222) while
    # main_results.md may carry full float precision (0.22222222...).
    # A 5e-4 tolerance safely admits 4-decimal rounding (max error 5e-5)
    # while still catching genuine mismatches (different predictions /
    # different thresholds would differ by >> 0.01).
    assert abs(main_f1 - ea_f1) < 5e-4, (
        f"F1 mismatch: main_results.md escalation_f1={main_f1} but "
        f"error_analysis.md operating-threshold F1={ea_f1}. Both must be "
        "computed from the same test_predictions.jsonl with the same "
        "dev-fitted operating_threshold."
    )


def test_error_analysis_has_threshold_sweep_disclaimer():
    """error_analysis.md must declare test sweep is diagnostic only."""
    ea_text = _read_text(ERROR_ANALYSIS_PATH)
    assert (
        "diagnostic only" in ea_text.lower()
        and "operating_threshold" in ea_text.lower()
    ), (
        "error_analysis.md must declare that the threshold sweep on test "
        "is diagnostic only and the main result uses the dev-fit "
        "operating_threshold."
    )
