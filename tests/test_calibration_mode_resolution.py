"""Regression tests for CESE-OCN calibration-mode configuration."""

from __future__ import annotations

import pytest

from cese.models.cese_ocn import _resolve_calibration_mode


def test_legacy_shared_threshold_false_selects_no_calibration():
    assert _resolve_calibration_mode(None, False) == "no_calibration"


def test_legacy_shared_threshold_true_selects_shared_threshold():
    assert _resolve_calibration_mode(None, True) == "shared_threshold"


def test_explicit_calibration_mode_is_retained_when_consistent():
    assert (
        _resolve_calibration_mode("separate_thresholds", None)
        == "separate_thresholds"
    )


def test_conflicting_legacy_and_explicit_modes_fail_closed():
    with pytest.raises(ValueError, match="conflicting calibration settings"):
        _resolve_calibration_mode("shared_threshold", False)
