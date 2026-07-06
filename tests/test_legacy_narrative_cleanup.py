"""Tests for legacy narrative cleanup and safe claims standardization (Task Pack H).

Verifies:
  - README.md first screen does not present V2 (or any non-V3.17 line) as current.
  - CURRENT_MAINLINE.md contains "V3.17 Confidential Lightweight".
  - README.md first screen contains the safe one-sentence positioning.
  - The legacy narrative scan report exists and reports unsafe_current_claim = 0.
  - The scan report shows ambiguous = 0.
  - No unsafe_current_claim findings appear in the scan CSV outside the
    safe_negation / legacy_section / future_work classifications.
"""

from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

SCAN_MD = REPO_ROOT / "reports" / "legacy_narrative_scan_v3_17.md"
SCAN_CSV = REPO_ROOT / "reports" / "legacy_narrative_scan_v3_17.csv"
SCAN_CONFIG = REPO_ROOT / "reports" / "legacy_narrative_scan_v3_17_run_config.json"
SAFE_CLAIMS_DICT = REPO_ROOT / "docs" / "safe_claims_dictionary_v3_17.md"

# README "first screen" = the lines a reader sees before scrolling. We treat
# everything before the first "---" divider (or the first 50 lines, whichever
# is shorter) as the first screen.
FIRST_SCREEN_MAX_LINES = 50

# Patterns that would indicate V2 is being framed as the current mainline.
V2_CURRENT_PATTERNS = [
    re.compile(r"V2[^.\n]{0,80}current empirical mainline", re.IGNORECASE),
    re.compile(r"current empirical mainline[^.\n]{0,80}V2", re.IGNORECASE),
    re.compile(r"V2[^.\n]{0,80}current mainline", re.IGNORECASE),
    re.compile(r"current mainline[^.\n]{0,80}V2", re.IGNORECASE),
    re.compile(r"current paper\s+V2", re.IGNORECASE),
    re.compile(r"current manuscript\s+is\s+V2", re.IGNORECASE),
]

# Phrases that must NOT appear as positive current claims. They are allowed
# only inside negations, legacy sections, or future-work sections (the scanner
# enforces this; these tests add a structural check on the first screen).
FORBIDDEN_POSITIVE_PHRASES = [
    "gold benchmark",
    "human-audited",
    "human audited",
    "SOTA",
    "state-of-the-art",
    "automatic peer review",
    "standalone detector",
    "general scientific overstatement detector",
    "full shared-threshold CESE-OCN validation",
]

ALLOWED_CLASSIFICATIONS = {"safe_negation", "legacy_section", "future_work"}
FORBIDDEN_CLASSIFICATIONS = {"unsafe_current_claim", "ambiguous"}

SAFE_ONE_SENTENCE_NEEDLES = [
    "controlled silver diagnostic",
    "retrieval-to-screening format shift",
    "confidential local pdf review",
    "gold benchmark",
    "sota detector",
    "automatic peer reviewer",
]


def _read(path: Path) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")


def _first_screen(text: str) -> str:
    """Return the README first screen: lines before the first `---` divider."""
    lines = text.splitlines()
    out: list[str] = []
    for i, line in enumerate(lines):
        if i >= FIRST_SCREEN_MAX_LINES:
            break
        if line.strip() == "---":
            break
        out.append(line)
    return "\n".join(out)


@pytest.fixture(scope="module")
def readme_text() -> str:
    return _read(REPO_ROOT / "README.md")


@pytest.fixture(scope="module")
def readme_first_screen(readme_text: str) -> str:
    return _first_screen(readme_text)


@pytest.fixture(scope="module")
def current_mainline_text() -> str:
    return _read(REPO_ROOT / "CURRENT_MAINLINE.md")


@pytest.fixture(scope="module")
def scan_config() -> dict:
    if not SCAN_CONFIG.exists():
        return {}
    return json.loads(SCAN_CONFIG.read_text(encoding="utf-8"))


@pytest.fixture(scope="module")
def scan_csv_rows() -> list[dict]:
    if not SCAN_CSV.exists():
        return []
    with SCAN_CSV.open(encoding="utf-8", newline="") as f:
        return list(csv.DictReader(f))


class TestReadmeFirstScreen:
    def test_readme_first_screen_no_v2_current(self, readme_first_screen):
        assert readme_first_screen, "README.md first screen is empty"
        for pat in V2_CURRENT_PATTERNS:
            match = pat.search(readme_first_screen)
            assert match is None, (
                f"README.md first screen appears to mark V2 as current: "
                f"{match.group(0)!r}"
            )

    def test_readme_first_screen_has_v317_confidential_lightweight(
        self, readme_first_screen
    ):
        assert readme_first_screen, "README.md first screen is empty"
        lower = readme_first_screen.lower()
        for needle in ["v3.17", "confidential", "lightweight"]:
            assert needle in lower, (
                f"README.md first screen missing required term '{needle}'"
            )

    def test_readme_first_screen_has_safe_one_sentence(
        self, readme_first_screen
    ):
        assert readme_first_screen, "README.md first screen is empty"
        # Normalize: lowercase + strip blockquote markers + collapse
        # whitespace so phrases that span line breaks in a blockquote
        # (e.g., "SOTA\n> detector") still match.
        normalized = readme_first_screen.lower()
        normalized = normalized.replace(">", " ")
        normalized = normalized.replace("\n", " ")
        normalized = " ".join(normalized.split())
        for needle in SAFE_ONE_SENTENCE_NEEDLES:
            needle_norm = " ".join(needle.lower().split())
            assert needle_norm in normalized, (
                f"README.md first screen missing safe-positioning needle "
                f"'{needle}'"
            )

    def test_readme_first_screen_no_unsafe_positive_claims(
        self, readme_first_screen
    ):
        """First screen must not positively assert gold/SOTA/human-audited/etc.

        Negated mentions (e.g. "not a gold benchmark") are allowed and
        expected. Cross-line negation (e.g., "is **not** a gold benchmark,
        SOTA\\ndetector, or automatic peer reviewer.") is also allowed.
        """
        assert readme_first_screen, "README.md first screen is empty"
        # Join lines with spaces so cross-line negation is detectable.
        joined = readme_first_screen.lower().replace("\n", " ")
        for phrase in FORBIDDEN_POSITIVE_PHRASES:
            phrase_lower = phrase.lower()
            search_from = 0
            while True:
                idx = joined.find(phrase_lower, search_from)
                if idx == -1:
                    break
                # Check the 80 chars before the phrase for a negation marker
                # (window is large enough to cross line boundaries).
                window = joined[max(0, idx - 80) : idx]
                negated = any(
                    neg in window
                    for neg in [
                        "not ",
                        "no ",
                        "never ",
                        "without ",
                        "cannot ",
                        "**not** ",
                        "isn't ",
                        "aren't ",
                        "don't ",
                        "do not ",
                        "is false",
                        "denies",
                        "do not claim",
                        "no gold benchmark claim",
                        "no sota claim",
                        "no human-audited dataset claim",
                        "no automatic peer review claim",
                        "no standalone detector claim",
                    ]
                )
                # Also allow post-keyword negation like "(NOT paper-ready)".
                tail = joined[idx : idx + 60]
                post_negated = any(
                    neg in tail
                    for neg in ["is false", "(not ", "(not)", "not paper-ready"]
                )
                assert negated or post_negated, (
                    f"README.md first screen has non-negated mention of "
                    f"forbidden phrase '{phrase}' near: "
                    f"{joined[max(0,idx-40):idx+40]!r}"
                )
                search_from = idx + len(phrase_lower)


class TestCurrentMainline:
    def test_current_mainline_has_v317_confidential_lightweight(
        self, current_mainline_text
    ):
        assert current_mainline_text, "CURRENT_MAINLINE.md is missing or empty"
        lower = current_mainline_text.lower()
        for needle in ["v3.17", "confidential", "lightweight"]:
            assert needle in lower, (
                f"CURRENT_MAINLINE.md missing required term '{needle}'"
            )

    def test_current_mainline_no_v2_current(self, current_mainline_text):
        assert current_mainline_text, "CURRENT_MAINLINE.md is missing or empty"
        for pat in V2_CURRENT_PATTERNS:
            match = pat.search(current_mainline_text)
            assert match is None, (
                f"CURRENT_MAINLINE.md appears to mark V2 as current: "
                f"{match.group(0)!r}"
            )


class TestScanReport:
    def test_scan_md_exists(self):
        assert SCAN_MD.exists(), (
            f"Legacy narrative scan report missing: {SCAN_MD}"
        )

    def test_scan_csv_exists(self):
        assert SCAN_CSV.exists(), (
            f"Legacy narrative scan CSV missing: {SCAN_CSV}"
        )

    def test_scan_config_exists(self):
        assert SCAN_CONFIG.exists(), (
            f"Legacy narrative scan run config missing: {SCAN_CONFIG}"
        )

    def test_scan_unsafe_current_claim_is_zero(self, scan_config):
        assert scan_config, "Scan run config is empty"
        assert scan_config.get("unsafe_current_claim_count") == 0, (
            f"unsafe_current_claim_count != 0: "
            f"{scan_config.get('unsafe_current_claim_count')}"
        )

    def test_scan_ambiguous_is_zero(self, scan_config):
        assert scan_config, "Scan run config is empty"
        assert scan_config.get("ambiguous_count") == 0, (
            f"ambiguous_count != 0: {scan_config.get('ambiguous_count')}"
        )

    def test_scan_gate_passes(self, scan_config):
        assert scan_config, "Scan run config is empty"
        assert scan_config.get("gate_pass") is True, (
            f"Scan gate did not pass: {scan_config.get('gate_pass')}"
        )

    def test_scan_md_states_unsafe_zero(self):
        text = _read(SCAN_MD)
        assert "unsafe_current_claim" in text, (
            "Scan MD does not mention unsafe_current_claim"
        )
        # The summary table row should show 0.
        match = re.search(
            r"\|\s*unsafe_current_claim\s*\|\s*(\d+)\s*\|", text
        )
        assert match, "Scan MD summary table missing unsafe_current_claim row"
        assert int(match.group(1)) == 0, (
            f"Scan MD shows unsafe_current_claim = {match.group(1)}, expected 0"
        )

    def test_scan_md_states_ambiguous_zero(self):
        text = _read(SCAN_MD)
        match = re.search(r"\|\s*ambiguous\s*\|\s*(\d+)\s*\|", text)
        assert match, "Scan MD summary table missing ambiguous row"
        assert int(match.group(1)) == 0, (
            f"Scan MD shows ambiguous = {match.group(1)}, expected 0"
        )

    def test_scan_csv_no_forbidden_classifications(self, scan_csv_rows):
        """No row in the scan CSV may be classified as unsafe_current_claim
        or ambiguous. Only safe_negation / legacy_section / future_work are
        allowed."""
        assert scan_csv_rows, "Scan CSV is empty or missing"
        bad: list[str] = []
        for row in scan_csv_rows:
            cls = (row.get("classification") or "").strip()
            if cls in FORBIDDEN_CLASSIFICATIONS:
                bad.append(
                    f"{row.get('path')}:{row.get('line_number')} "
                    f"[{cls}] {row.get('matched_phrase')}"
                )
        assert not bad, (
            "Scan CSV contains forbidden classifications:\n  - "
            + "\n  - ".join(bad)
        )

    def test_scan_csv_all_classifications_allowed(self, scan_csv_rows):
        assert scan_csv_rows, "Scan CSV is empty or missing"
        for row in scan_csv_rows:
            cls = (row.get("classification") or "").strip()
            assert cls in ALLOWED_CLASSIFICATIONS, (
                f"Unexpected classification '{cls}' in row: {row}"
            )


class TestSafeClaimsDictionary:
    def test_safe_claims_dictionary_exists(self):
        assert SAFE_CLAIMS_DICT.exists(), (
            f"Safe claims dictionary missing: {SAFE_CLAIMS_DICT}"
        )

    def test_safe_claims_dictionary_has_required_safe_wording(self):
        text = _read(SAFE_CLAIMS_DICT).lower()
        # Normalize whitespace around slashes so both "local/no-api" and
        # "local / no-api" match.
        normalized = text.replace(" / ", "/")
        required_safe = [
            "controlled silver diagnostic",
            "source-traceable silver set",
            "second-stage review queue",
            "retrieval-to-screening format shift",
            "evidence canonicalization",
            "local/no-api/confidential review",
        ]
        for needle in required_safe:
            assert needle in normalized, (
                f"Safe claims dictionary missing safe wording '{needle}'"
            )

    def test_safe_claims_dictionary_has_required_unsafe_wording(self):
        text = _read(SAFE_CLAIMS_DICT).lower()
        normalized = text.replace(" / ", "/")
        required_unsafe = [
            "gold benchmark",
            "validated general detector",
            "human-audited dataset",
            "automatic peer review",
            "sota claim",
            "full cese-ocn validation",
        ]
        for needle in required_unsafe:
            assert needle in normalized, (
                f"Safe claims dictionary missing unsafe wording '{needle}'"
            )
