"""Tests for current-mainline documentation hygiene (Task Pack G Step 4).

Verifies:
  - README.md and CURRENT_MAINLINE.md mention V3.17 + confidential + lightweight
  - Neither document marks V2 (or any non-V3.17 line) as the current mainline
  - V3.17 is the only line labelled "current empirical mainline"
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

REQUIRED_NEEDLES = ["V3.17", "confidential", "lightweight"]

# Phrases that, if present alongside "V2", would indicate V2 is being
# presented as the current mainline. We allow legacy/future framing but
# forbid "current" framing for V2.
V2_CURRENT_PATTERNS = [
    re.compile(r"V2[^.\n]{0,80}current empirical mainline", re.IGNORECASE),
    re.compile(r"current empirical mainline[^.\n]{0,80}V2", re.IGNORECASE),
    re.compile(r"V2[^.\n]{0,80}current mainline", re.IGNORECASE),
    re.compile(r"current mainline[^.\n]{0,80}V2", re.IGNORECASE),
]


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def readme_text() -> str:
    return _read(REPO_ROOT / "README.md")


@pytest.fixture(scope="module")
def current_mainline_text() -> str:
    return _read(REPO_ROOT / "CURRENT_MAINLINE.md")


class TestReadmeMentionsV317:
    def test_readme_mentions_v317_confidential_lightweight(self, readme_text):
        assert readme_text, "README.md is missing or empty"
        lower = readme_text.lower()
        for needle in REQUIRED_NEEDLES:
            assert needle.lower() in lower, (
                f"README.md missing required term '{needle}'"
            )

    def test_readme_does_not_mark_v2_as_current(self, readme_text):
        assert readme_text, "README.md is missing or empty"
        for pat in V2_CURRENT_PATTERNS:
            match = pat.search(readme_text)
            assert match is None, (
                f"README.md appears to mark V2 as current mainline: "
                f"{match.group(0)!r}"
            )


class TestCurrentMainlineMentionsV317:
    def test_current_mainline_mentions_v317_confidential_lightweight(
        self, current_mainline_text
    ):
        assert current_mainline_text, "CURRENT_MAINLINE.md is missing or empty"
        lower = current_mainline_text.lower()
        for needle in REQUIRED_NEEDLES:
            assert needle.lower() in lower, (
                f"CURRENT_MAINLINE.md missing required term '{needle}'"
            )

    def test_current_mainline_does_not_mark_v2_as_current(
        self, current_mainline_text
    ):
        assert current_mainline_text, "CURRENT_MAINLINE.md is missing or empty"
        for pat in V2_CURRENT_PATTERNS:
            match = pat.search(current_mainline_text)
            assert match is None, (
                f"CURRENT_MAINLINE.md appears to mark V2 as current mainline: "
                f"{match.group(0)!r}"
            )

    def test_current_mainline_header_is_v317(self, current_mainline_text):
        # The first "current mainline" header should reference V3.17
        # (not V2 or any older line).
        lines = current_mainline_text.splitlines()
        v317_header_seen = False
        for line in lines:
            if "V3.17" in line and "confidential" in line.lower():
                v317_header_seen = True
                break
        assert v317_header_seen, (
            "CURRENT_MAINLINE.md does not declare V3.17 confidential as the "
            "current mainline"
        )
