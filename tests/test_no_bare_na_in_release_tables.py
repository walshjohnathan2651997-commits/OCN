"""Tests that release/tables/*.md contain no bare NA cells (ocn-33 P2-7).

The user spec (ocn-33 P1-3) forbids bare ``NA`` in release tables. Every
missing value must be replaced with an explicit status code:
  * ``not_implemented``
  * ``not_run``
  * ``not_applicable``
  * ``insufficient_data``
  * ``requires_api_key``
  * ``missing_or_legacy``

A bare ``| NA |`` cell is a violation because it does not tell reviewers
WHY the value is missing.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

TABLES_DIR = ROOT / "release" / "tables"

# Matches a bare NA cell in a markdown table row: ``| NA |`` with
# optional surrounding whitespace. Captures the literal "NA" token.
# This intentionally does NOT match status codes like "not_applicable"
# or substrings like "NAME" or "NAVIGATE".
_BARE_NA_CELL = re.compile(r"\|\s*NA\s*\|", re.IGNORECASE)


def _list_table_md_files() -> list:
    """Return all *.md files under release/tables (or skip if absent)."""
    if not TABLES_DIR.exists():
        pytest.skip(f"release/tables not found at {TABLES_DIR}")
    files = sorted(TABLES_DIR.glob("*.md"))
    if not files:
        pytest.skip(f"no .md files under {TABLES_DIR}")
    return files


def test_no_bare_na_in_any_table_md():
    """No ``| NA |`` cell may appear in any release/tables/*.md file."""
    files = _list_table_md_files()
    violations: list = []
    for md in files:
        text = md.read_text(encoding="utf-8")
        for line_no, line in enumerate(text.splitlines(), start=1):
            # Only inspect table rows (lines starting with |).
            stripped = line.lstrip()
            if not stripped.startswith("|"):
                continue
            # Skip the separator row (| --- | --- |).
            if set(stripped.replace("|", "").replace("-", "").split()) == {""}:
                continue
            matches = _BARE_NA_CELL.findall(line)
            if matches:
                violations.append(
                    f"{md.name}:{line_no}: {line.strip()}"
                )
    assert not violations, (
        "Bare NA cells are forbidden in release tables (ocn-33 P1-3). "
        "Replace each with an explicit status code "
        "(not_implemented / not_run / not_applicable / insufficient_data / "
        "requires_api_key / missing_or_legacy):\n  " +
        "\n  ".join(violations)
    )


def test_main_results_md_has_no_bare_na():
    """Specifically check release/tables/main_results.md for bare NA."""
    target = TABLES_DIR / "main_results.md"
    if not target.exists():
        pytest.skip(f"{target} not present")
    text = target.read_text(encoding="utf-8")
    for line_no, line in enumerate(text.splitlines(), start=1):
        if not line.lstrip().startswith("|"):
            continue
        if _BARE_NA_CELL.search(line):
            pytest.fail(
                f"main_results.md:{line_no} contains bare NA: {line.strip()}"
            )


def test_status_codes_are_present_in_tables():
    """At least one explicit status code must appear in the tables.

    This guards against a regression where the NA-replacement logic is
    silently bypassed (e.g. all rows happen to have real metrics, so no
    status code is emitted). The clean_v2 release has unimplemented
    baselines, so at least ``not_implemented`` / ``requires_api_key``
    must appear.
    """
    files = _list_table_md_files()
    allowed_codes = {
        "not_implemented",
        "not_run",
        "not_applicable",
        "insufficient_data",
        "requires_api_key",
        "missing_or_legacy",
    }
    found_codes: set = set()
    for md in files:
        text = md.read_text(encoding="utf-8")
        for code in allowed_codes:
            if code in text:
                found_codes.add(code)
    assert found_codes, (
        "Expected at least one explicit status code in release/tables/*.md "
        "(clean_v2 has unimplemented baselines). Found none."
    )


def test_main_results_md_has_pilot_disclaimer():
    """main_results.md must declare pilot-only status at the top."""
    target = TABLES_DIR / "main_results.md"
    if not target.exists():
        pytest.skip(f"{target} not present")
    text = target.read_text(encoding="utf-8")
    # The first ~10 lines must contain a pilot-only disclaimer.
    head = "\n".join(text.splitlines()[:15])
    assert (
        "pilot" in head.lower()
        and "submission-ready" in head.lower()
    ), (
        "main_results.md must open with a pilot-only disclaimer "
        "(e.g. 'Pilot pipeline validation only. Not submission-ready "
        "empirical evidence.')"
    )
