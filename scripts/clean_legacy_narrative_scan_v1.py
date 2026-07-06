#!/usr/bin/env python
"""clean_legacy_narrative_scan_v1.py — Legacy narrative scanner for V3.17.

Scans README.md, CURRENT_MAINLINE.md, docs/, paper_assets/, and reports/
for residual legacy narrative keywords and classifies each hit:

  - safe_negation        — "not gold", "not SOTA", "do not claim X"
  - legacy_section       — appears under a Legacy/Archive/History header
  - future_work          — appears under a Future Work header
  - unsafe_current_claim — positive assertion that conflicts with V3.17
                           (e.g., "current mainline is V2", "is a gold
                           benchmark", "achieves SOTA")
  - ambiguous            — needs human review

Outputs:
  reports/legacy_narrative_scan_v3_17.csv  — one row per finding
  reports/legacy_narrative_scan_v3_17.md   — grouped summary + counts

Hard boundaries: read-only. Does not modify any scanned file.
Usage:
  python scripts/clean_legacy_narrative_scan_v1.py
  python scripts/clean_legacy_narrative_scan_v1.py --strict
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional, Tuple

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

SCAN_TARGETS: List[str] = [
    "README.md",
    "CURRENT_MAINLINE.md",
    "docs/",
    "paper_assets/",
    "reports/",
]

# Keywords that indicate legacy / unsafe narrative. Each entry is
# (pattern, label) where pattern is a compiled regex and label is a short
# human-readable tag for the matched_phrase column.
KEYWORD_PATTERNS: List[Tuple[re.Pattern, str]] = [
    (re.compile(r"current\s+paper\s+V2", re.IGNORECASE), "current_paper_V2"),
    (re.compile(r"current\s+manuscript\s+is\s+V2", re.IGNORECASE), "current_manuscript_is_V2"),
    (re.compile(r"simclaim_human_pilot\s+current\s+mainline", re.IGNORECASE), "simclaim_human_pilot_current_mainline"),
    (re.compile(r"full\s+shared-threshold\s+CESE-OCN", re.IGNORECASE), "full_shared_threshold_CESE_OCN"),
    (re.compile(r"\bgold\s+benchmark\b", re.IGNORECASE), "gold_benchmark"),
    (re.compile(r"\bhuman[- ]?audited\b", re.IGNORECASE), "human_audited"),
    (re.compile(r"\bSOTA\b"), "SOTA"),
    (re.compile(r"\bstate-of-the-art\b", re.IGNORECASE), "state_of_the_art"),
    (re.compile(r"\bautomatic\s+peer\s+review(?:er)?\b", re.IGNORECASE), "automatic_peer_review"),
    (re.compile(r"\bstandalone\s+detector\b", re.IGNORECASE), "standalone_detector"),
    (re.compile(r"\bgeneral\s+scientific\s+overstatement\s+detector\b", re.IGNORECASE), "general_scientific_overstatement_detector"),
]

# Negation markers — if any appears within NEGATION_WINDOW chars before
# the keyword, the hit is likely a safe negation.
NEGATION_MARKERS = [
    "not ", "is not ", "are not ", "do not ", "don't ", "never ",
    "no ", "without ", "cannot ", "fails to ", "isn't ", "aren't ",
    "is **not** ", "are **not** ", "do **not** ", "**not** ",
    "**not** ", "isn't a ", "isn't an ", "are not a ", "are not an ",
    # Factual-false markers (e.g., "viability is false")
    "is false", "are false", "is true only", "viability is false",
    # Downgrade markers
    "not paper-ready", "not paper ready", "disclaims", "disclaim",
    "missing", "absent", "not yet", "denies", "denied",
    # Chinese negation
    "不是", "不能", "没有", "未",
]
NEGATION_WINDOW = 80

# Post-keyword negation markers — checked within NEGATION_WINDOW chars
# AFTER the keyword. Catches cases like "gold benchmark (NOT paper-ready)"
# or "SOTA benchmark." where the previous line had "is **NOT** a".
POST_NEGATION_MARKERS = [
    "is false", "are false", "(not ", "(not)", "not paper-ready",
    "not paper ready", "(NOT ", "(NOT)",
]

# Bold-text section markers (not markdown headers but act like them).
# Lines starting with these get treated as section boundaries.
BOLD_SECTION_PATTERNS = [
    re.compile(r"^\*\*Forbidden\b", re.IGNORECASE),
    re.compile(r"^\*\*Allowed\b", re.IGNORECASE),
    re.compile(r"^\*\*Do\s+not\b", re.IGNORECASE),
    re.compile(r"^\*\*Not\s+safe\b", re.IGNORECASE),
    re.compile(r"^\*\*Safe\b", re.IGNORECASE),
    re.compile(r"^Do\s+\*\*not\*\*", re.IGNORECASE),
]

# Full-line negation markers — if ANY of these appears on the same line
# as the keyword, the hit is safe_negation regardless of distance.
# These are strong negation phrases that clearly downgrade the keyword.
FULL_LINE_NEGATION_MARKERS = [
    "is false", "are false", "is untrue", "unusable", "not usable",
    "denies", "denied", "disclaims", "disclaim",
    "do not claim", "don't claim", "cannot claim",
    "not a gold", "not a sota", "not sota",
    "not human-audited", "not a human-audited",
    "not automatic", "not a standalone",
    "not full cese-ocn", "not a full",
]

# Section-header markers that indicate legacy / archive / future-work
# context. If the nearest preceding markdown header contains any of
# these, the hit inherits that classification (unless it's a positive
# assertion).
LEGACY_HEADER_KEYWORDS = [
    "legacy", "archive", "history", "historical", "deprecated",
    "superseded", "older", "outdated", "stale", "do not use",
    "not safe", "do not claim", "forbidden", "unsafe",
    "old narrative", "narrative reference", "not current",
]
FUTURE_WORK_HEADER_KEYWORDS = [
    "future work", "future architecture", "future direction",
    "roadmap", "not yet", "planned", "future",
    "next phase", "upgrade", "expansion",
]

# Positive-assertion markers — if the line contains any of these near
# the keyword, the hit is likely an unsafe current claim.
POSITIVE_ASSERTION_MARKERS = [
    "is a ", "is an ", "are a ", "are an ",
    "achieves", "achieved", "proves", "proven", "validated",
    "we propose", "we present", "we introduce", "we demonstrate",
    "this paper presents", "this work presents",
    "current empirical mainline is",
    "current mainline is",
    "current paper is",
    "current manuscript is",
    "we are the first",
    "outperforms", "beats", "superior to",
]

# Section-header regex (markdown ## / ### / etc.)
SECTION_HEADER_RE = re.compile(r"^(#{1,6})\s+(.+?)\s*$")

# Lines that are clearly code/config identifiers, not prose claims.
# e.g., human_audited=False, human_audited column name in a table
CODE_IDENTIFIER_RE = re.compile(
    r"(human_audited\s*=\s*False|human_audited\s*=\s*True|"
    r"`human_audited`|human_audited\b(?=\s*[|,}])|"
    r"\|\s*human_audited\s*\|)"
)


# ---------------------------------------------------------------------------
# Finding dataclass
# ---------------------------------------------------------------------------

@dataclass
class Finding:
    path: str
    line_number: int
    matched_phrase: str
    context: str
    classification: str
    recommended_action: str

    def to_dict(self) -> dict:
        return {
            "path": self.path,
            "line_number": self.line_number,
            "matched_phrase": self.matched_phrase,
            "context": self.context,
            "classification": self.classification,
            "recommended_action": self.recommended_action,
        }


# ---------------------------------------------------------------------------
# Path helpers
# ---------------------------------------------------------------------------

def _is_excluded(path: Path) -> bool:
    """Skip private / build / cache directories and the scanner's own
    output files (avoids a feedback loop where the scan report contains
    the keywords it scanned for)."""
    parts = path.parts
    for part in parts:
        plower = part.lower()
        if plower in (".git", "__pycache__", "node_modules", ".venv", "venv"):
            return True
        if plower == "release_bundles":
            # Derived artifact; source docs are scanned directly.
            return True
        if plower.startswith("private_") or plower.endswith("_private"):
            return True
    # Exclude the scanner's own output files to prevent feedback loops
    name = path.name.lower()
    if name.startswith("legacy_narrative_scan_v3_17"):
        return True
    return False


def _collect_files() -> List[Path]:
    files: List[Path] = []
    for target in SCAN_TARGETS:
        full = REPO_ROOT / target
        if not full.exists():
            continue
        if full.is_file():
            if not _is_excluded(full) and full.suffix.lower() == ".md":
                files.append(full)
        else:
            for p in full.rglob("*"):
                if not p.is_file():
                    continue
                if _is_excluded(p):
                    continue
                if p.suffix.lower() != ".md":
                    continue
                files.append(p)
    return sorted(set(files))


def _rel(path: Path) -> str:
    try:
        return str(path.relative_to(REPO_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path)


# ---------------------------------------------------------------------------
# Classification logic
# ---------------------------------------------------------------------------

def _find_ancestor_headers(lines: List[str], line_idx: int) -> List[str]:
    """Walk backward from line_idx and collect ALL ancestor markdown
    headers (any level) AND bold-text section markers. Returns a list
    from nearest to farthest.

    This is important because a line under `### U6:` inside `## Unsafe
    Claims` needs BOTH headers to classify correctly — the nearest
    header (`### U6:`) is just an identifier, but the parent (`## Unsafe
    Claims`) carries the section semantics.

    Also recognizes bold-text section markers like `**Forbidden**` or
    `**Do not**` which act as section boundaries in some docs even
    though they're not markdown headers.
    """
    headers: List[str] = []
    for i in range(line_idx, -1, -1):
        line_stripped = lines[i].rstrip()
        m = SECTION_HEADER_RE.match(line_stripped)
        if m:
            headers.append(m.group(2).strip())
            continue
        # Check bold-text section markers (also handle blockquoted bold:
        # "> **Legacy data card.**" should be recognized as a section)
        line_unquoted = line_stripped.lstrip("> ").rstrip()
        for pat in BOLD_SECTION_PATTERNS:
            if pat.match(line_unquoted):
                headers.append(line_unquoted.strip())
                break
        else:
            # Also recognize blockquoted legacy/deprecation notices that
            # start with **Legacy** or **Superseded** (not in the standard
            # BOLD_SECTION_PATTERNS which focus on forbidden/allowed).
            if line_unquoted.startswith("**Legacy") or line_unquoted.startswith("**Superseded"):
                headers.append(line_unquoted.strip())
    return headers


def _find_nearest_header(lines: List[str], line_idx: int) -> Optional[str]:
    """Walk backward from line_idx to find the nearest markdown header."""
    headers = _find_ancestor_headers(lines, line_idx)
    return headers[0] if headers else None


def _any_header_contains(headers: List[str], keywords: List[str]) -> bool:
    """Check if any header in the list contains any of the keywords."""
    for header in headers:
        hlower = header.lower()
        if any(kw in hlower for kw in keywords):
            return True
    return False


def _header_contains(header: Optional[str], keywords: List[str]) -> bool:
    if not header:
        return False
    hlower = header.lower()
    return any(kw in hlower for kw in keywords)


def _has_negation_before(line: str, match_start: int) -> bool:
    """Check if a negation marker appears within NEGATION_WINDOW chars
    before the keyword."""
    window_start = max(0, match_start - NEGATION_WINDOW)
    prefix = line[window_start:match_start].lower()
    return any(marker in prefix for marker in NEGATION_MARKERS)


def _has_negation_after(line: str, match_end: int) -> bool:
    """Check if a post-negation marker appears within NEGATION_WINDOW
    chars after the keyword. Catches patterns like:
        "gold benchmark (NOT paper-ready)"
        "SOTA benchmark."  (where prev line had "is **NOT** a")
    """
    window_end = min(len(line), match_end + NEGATION_WINDOW)
    suffix = line[match_end:window_end].lower()
    return any(marker in suffix for marker in POST_NEGATION_MARKERS)


def _has_negation_in_prev_line(lines: List[str], line_idx_0: int) -> bool:
    """Check if the previous line ends with a negation marker (for
    line-split negation like 'is **NOT** a\\nSOTA benchmark.').

    Also handles list-continuation negation where the previous line
    contains a negation marker AND ends with a comma or conjunction
    (e.g., 'It is **not** a gold benchmark, SOTA\\ndetector, or ...').
    In that case the negation scope carries over to the next line.
    """
    if line_idx_0 <= 0:
        return False
    prev = lines[line_idx_0 - 1].rstrip().lower()
    if not prev:
        return False
    # Check if the previous line ends with a negation marker
    for marker in NEGATION_MARKERS:
        if prev.endswith(marker.strip()):
            return True
    # Also check if the last 80 chars of the previous line contain a marker
    tail = prev[-NEGATION_WINDOW:] if len(prev) > NEGATION_WINDOW else prev
    # Only count it if the marker is at the end of the line (continuation)
    for marker in ["not a", "not an", "**not** a", "**not** an", "not the"]:
        if prev.endswith(marker):
            return True
    # List-continuation negation: previous line has a negation marker
    # AND ends with a comma or conjunction, indicating the negated list
    # continues onto the next line.
    prev_has_negation = any(marker in prev for marker in NEGATION_MARKERS)
    ends_with_continuation = (
        prev.endswith(",")
        or prev.endswith(" or")
        or prev.endswith(" and")
    )
    if prev_has_negation and ends_with_continuation:
        return True
    # Also: if the previous line has a negation marker AND does NOT end
    # with sentence-terminating punctuation (. ! ? : ;), the sentence
    # likely continues onto the next line, carrying the negation scope.
    # This catches cases like:
    #   '... It is **not** a gold benchmark, SOTA'
    #   'detector, or automatic peer reviewer.'
    if prev_has_negation:
        if not (prev.endswith(".") or prev.endswith("!")
                or prev.endswith("?") or prev.endswith(":")
                or prev.endswith(";")):
            return True
    return False


def _has_full_line_negation(line: str) -> bool:
    """Check if the line contains a strong full-line negation marker
    anywhere (not just near the keyword). Catches cases like:
        'Standalone viability is false. ... unusable as a standalone detector.'
    where the negation is far from the keyword but clearly on the same line.
    """
    line_lower = line.lower()
    return any(marker in line_lower for marker in FULL_LINE_NEGATION_MARKERS)


def _has_future_context_before(line: str, match_start: int) -> bool:
    """Check if future-work context markers appear before the keyword."""
    window_start = max(0, match_start - NEGATION_WINDOW)
    prefix = line[window_start:match_start].lower()
    future_markers = [
        "may seed", "may become", "may be", "might become",
        "to be constructed", "planned", "will become",
        "once audited", "after audit", "future",
    ]
    return any(marker in prefix for marker in future_markers)


def _has_external_context(line: str, match_start: int) -> bool:
    """Check if 'external' appears before 'gold benchmark' — this means
    the line is talking about EXTERNAL benchmarks, not claiming to be one."""
    window_start = max(0, match_start - 40)
    prefix = line[window_start:match_start].lower()
    return "external" in prefix


def _in_unsafe_wording_table(lines: List[str], line_idx_0: int) -> bool:
    """Check if the current line is inside a markdown table whose header
    contains an 'Unsafe wording' column. Such tables explicitly list unsafe
    phrases as examples of what NOT to say, so any keyword hit in a table
    row under that header is safe_negation (it's a warning, not a claim).

    Walks backward from line_idx_0 looking for a table header row (a line
    starting with '|' that contains 'unsafe') within the same table block.
    """
    if line_idx_0 < 0 or line_idx_0 >= len(lines):
        return False
    # Only consider lines that are themselves table rows
    cur = lines[line_idx_0].lstrip()
    if not cur.startswith("|"):
        return False
    # Walk backward through consecutive table rows to find the header
    for i in range(line_idx_0, max(line_idx_0 - 20, -1), -1):
        if i < 0:
            break
        row = lines[i].lstrip()
        if not row.startswith("|"):
            # Left the table block without finding an unsafe header
            return False
        # Check if this row is the header containing "unsafe"
        if "unsafe" in row.lower():
            return True
    return False


def _has_unsafe_label_prefix(line: str, match_start: int) -> bool:
    """Check if the line has an explicit 'Unsafe:' label prefix before
    the keyword, e.g., '- **Unsafe**: "BM25 is SOTA for ...' or
    '**Unsafe**: "gold benchmark"'. Such lines are listing examples of
    unsafe wording, so the keyword hit is safe_negation.
    """
    prefix = line[:match_start].lower()
    # Look for the unsafe-label marker in the prefix
    unsafe_label_markers = [
        "- **unsafe**:",
        "**unsafe**:",
        "- **unsafe wording**:",
        "**unsafe wording**:",
        "- unsafe:",
        "unsafe wording:",
    ]
    return any(marker in prefix for marker in unsafe_label_markers)


def _has_positive_assertion(line: str, match_start: int, match_end: int) -> bool:
    """Check if a positive-assertion marker appears on the same line near
    the keyword."""
    line_lower = line.lower()
    # Check the whole line for positive-assertion markers
    for marker in POSITIVE_ASSERTION_MARKERS:
        if marker in line_lower:
            return True
    return False


def _is_code_identifier(line: str, match_start: int, match_end: int) -> bool:
    """Check if the match is a code identifier (e.g., human_audited=False)
    rather than a prose claim."""
    # Look at a small window around the match
    window_start = max(0, match_start - 10)
    window_end = min(len(line), match_end + 30)
    window = line[window_start:window_end]
    return bool(CODE_IDENTIFIER_RE.search(window))


def classify_finding(
    line: str,
    match_start: int,
    match_end: int,
    ancestor_headers: List[str],
    keyword_label: str,
    lines: Optional[List[str]] = None,
    line_idx_0: int = 0,
) -> str:
    """Classify a keyword match into one of the 5 categories.

    `ancestor_headers` is a list from nearest to farthest (e.g.,
    ["U6: ...", "Unsafe Claims (Do NOT make)", "Paper Claims Checklist"]).
    We check ALL ancestors for section context, not just the nearest one.

    `lines` and `line_idx_0` are passed to enable cross-line negation
    detection (e.g., when a negation marker is on the previous line).
    """
    # Code identifiers (e.g., human_audited=False) are always safe.
    if _is_code_identifier(line, match_start, match_end):
        return "safe_negation"

    # Lines inside a table with an "Unsafe wording" header column are
    # explicitly listing unsafe phrases as warnings — safe_negation.
    if lines is not None and _in_unsafe_wording_table(lines, line_idx_0):
        return "safe_negation"

    # Lines with an explicit "- **Unsafe**:" or "**Unsafe**:" prefix are
    # labeling the following content as an example of unsafe wording —
    # safe_negation.
    if _has_unsafe_label_prefix(line, match_start):
        return "safe_negation"

    has_negation = _has_negation_before(line, match_start)
    has_negation_after = _has_negation_after(line, match_end)
    has_negation_prev = (
        lines is not None and _has_negation_in_prev_line(lines, line_idx_0)
    )
    has_full_negation = _has_full_line_negation(line)
    has_any_negation = (
        has_negation or has_negation_after or has_negation_prev
        or has_full_negation
    )

    has_positive = _has_positive_assertion(line, match_start, match_end)
    has_future_ctx = _has_future_context_before(line, match_start)
    has_external_ctx = _has_external_context(line, match_start)
    in_legacy = _any_header_contains(ancestor_headers, LEGACY_HEADER_KEYWORDS)
    in_future = _any_header_contains(ancestor_headers, FUTURE_WORK_HEADER_KEYWORDS)

    # Lines that quote an unsafe claim as an example (e.g., "This is a gold
    # benchmark.") inside an Unsafe Claims section are safe — they are
    # warnings, not assertions.
    in_unsafe_section = _any_header_contains(ancestor_headers, ["unsafe"])
    if in_unsafe_section:
        return "safe_negation"

    # Lines inside a Forbidden / Do not / Not safe bold section are safe
    in_forbidden_bold = _any_header_contains(
        ancestor_headers, ["forbidden", "do not", "not safe"]
    )
    if in_forbidden_bold:
        return "safe_negation"

    # Positive assertion in a non-legacy, non-future section → unsafe
    if has_positive and not has_any_negation and not in_legacy and not in_future:
        return "unsafe_current_claim"

    # Positive assertion even in legacy/future is suspicious if it asserts
    # "current" — but if the section is explicitly legacy/future, the
    # context already downgrades it.
    if has_positive and not has_any_negation and (in_legacy or in_future):
        # "current mainline is V2" in a legacy section is still legacy
        return "legacy_section" if in_legacy else "future_work"

    # Negation present → safe
    if has_any_negation:
        return "safe_negation"

    # No negation, no positive assertion — context decides
    if in_legacy:
        return "legacy_section"
    if in_future:
        return "future_work"
    if has_future_ctx:
        return "future_work"
    if has_external_ctx:
        # "external gold benchmark" is talking about external benchmarks,
        # not claiming to be one.
        return "safe_negation"

    # No context signals — needs human review
    return "ambiguous"


def recommend_action(classification: str) -> str:
    return {
        "safe_negation": "Keep as-is (safe negation).",
        "legacy_section": "Keep in legacy section.",
        "future_work": "Keep as future work.",
        "unsafe_current_claim": (
            "DOWNGRADE: rephrase as legacy/future_work, add explicit "
            "negation, or move to a Legacy section header."
        ),
        "ambiguous": (
            "REVIEW: clarify whether this is current or legacy. Add "
            "negation or move under a Legacy/Future Work header."
        ),
    }.get(classification, "REVIEW.")


# ---------------------------------------------------------------------------
# Scanner
# ---------------------------------------------------------------------------

def scan_file(path: Path) -> List[Finding]:
    """Scan a single markdown file for legacy narrative keywords."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return []

    lines = text.splitlines()
    findings: List[Finding] = []

    for line_idx, line in enumerate(lines, start=1):
        for pattern, label in KEYWORD_PATTERNS:
            for m in pattern.finditer(line):
                match_start = m.start()
                match_end = m.end()
                matched_text = m.group(0)

                ancestor_headers = _find_ancestor_headers(lines, line_idx - 1)
                classification = classify_finding(
                    line, match_start, match_end, ancestor_headers, label,
                    lines=lines, line_idx_0=line_idx - 1,
                )

                # Build a short context snippet (the full line, trimmed)
                context = line.strip()
                if len(context) > 200:
                    context = context[:197] + "..."

                findings.append(Finding(
                    path=_rel(path),
                    line_number=line_idx,
                    matched_phrase=matched_text,
                    context=context,
                    classification=classification,
                    recommended_action=recommend_action(classification),
                ))

    return findings


def scan_all() -> List[Finding]:
    files = _collect_files()
    all_findings: List[Finding] = []
    for path in files:
        all_findings.extend(scan_file(path))
    return all_findings


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_csv(findings: List[Finding], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "path", "line_number", "matched_phrase",
                "context", "classification", "recommended_action",
            ],
        )
        writer.writeheader()
        for finding in findings:
            writer.writerow(finding.to_dict())


def write_markdown(findings: List[Finding], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Count by classification
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.classification] = counts.get(f.classification, 0) + 1

    # Count by file (unsafe + ambiguous only)
    unsafe_or_ambiguous = [
        f for f in findings
        if f.classification in ("unsafe_current_claim", "ambiguous")
    ]

    lines: List[str] = []
    lines.append("# Legacy Narrative Scan — V3.17 Confidential Lightweight")
    lines.append("")
    lines.append(
        f"Generated: {datetime.now(timezone.utc).isoformat()}"
    )
    lines.append("")
    lines.append("> Read-only scan. No files were modified.")
    lines.append("")
    lines.append("## Summary")
    lines.append("")
    lines.append("| Classification | Count |")
    lines.append("|---|---|")
    total = 0
    for cls in ["safe_negation", "legacy_section", "future_work",
                "unsafe_current_claim", "ambiguous"]:
        n = counts.get(cls, 0)
        lines.append(f"| {cls} | {n} |")
        total += n
    lines.append(f"| **total** | **{total}** |")
    lines.append("")
    lines.append("## Gate status")
    lines.append("")
    unsafe_count = counts.get("unsafe_current_claim", 0)
    ambiguous_count = counts.get("ambiguous", 0)
    if unsafe_count == 0 and ambiguous_count == 0:
        lines.append("- **unsafe_current_claim = 0**: PASS")
        lines.append("- **ambiguous = 0**: PASS")
        lines.append("- Overall: PASS (all hits are safe_negation, legacy, or future_work)")
    else:
        lines.append(f"- **unsafe_current_claim = {unsafe_count}**: " +
                     ("PASS" if unsafe_count == 0 else "FAIL"))
        lines.append(f"- **ambiguous = {ambiguous_count}**: " +
                     ("PASS" if ambiguous_count == 0 else "REVIEW NEEDED"))
        lines.append("- Overall: " + ("PASS" if unsafe_count == 0 else "FAIL"))
    lines.append("")

    if unsafe_or_ambiguous:
        lines.append("## Findings requiring action")
        lines.append("")
        lines.append("| Path | Line | Phrase | Classification | Context |")
        lines.append("|---|---|---|---|---|")
        for f in unsafe_or_ambiguous:
            ctx = f.context.replace("|", "\\|")
            if len(ctx) > 120:
                ctx = ctx[:117] + "..."
            lines.append(
                f"| {f.path} | {f.line_number} | {f.matched_phrase} | "
                f"{f.classification} | {ctx} |"
            )
        lines.append("")

    # Group all findings by classification for transparency
    lines.append("## All findings by classification")
    lines.append("")
    for cls in ["unsafe_current_claim", "ambiguous",
                "safe_negation", "legacy_section", "future_work"]:
        cls_findings = [f for f in findings if f.classification == cls]
        if not cls_findings:
            continue
        lines.append(f"### {cls} ({len(cls_findings)})")
        lines.append("")
        lines.append("| Path | Line | Phrase | Context |")
        lines.append("|---|---|---|---|")
        for f in cls_findings:
            ctx = f.context.replace("|", "\\|")
            if len(ctx) > 120:
                ctx = ctx[:117] + "..."
            lines.append(
                f"| {f.path} | {f.line_number} | {f.matched_phrase} | {ctx} |"
            )
        lines.append("")

    lines.append("## Scanned files")
    lines.append("")
    files = sorted({f.path for f in findings})
    if files:
        for p in files:
            lines.append(f"- `{p}`")
    else:
        lines.append("(no findings — all scanned files are clean)")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")


def write_run_config(out_path: Path, strict: bool, findings: List[Finding]) -> None:
    """Write a small run_config.json for audit trail."""
    counts: dict[str, int] = {}
    for f in findings:
        counts[f.classification] = counts.get(f.classification, 0) + 1
    config = {
        "script": "scripts/clean_legacy_narrative_scan_v1.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "scan_targets": SCAN_TARGETS,
        "strict": strict,
        "counts": counts,
        "total_findings": len(findings),
        "unsafe_current_claim_count": counts.get("unsafe_current_claim", 0),
        "ambiguous_count": counts.get("ambiguous", 0),
        "gate_pass": counts.get("unsafe_current_claim", 0) == 0,
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Scan for legacy narrative in V3.17 docs."
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Treat ambiguous findings as failures (exit 1).",
    )
    parser.add_argument(
        "--output_dir", default="reports",
        help="Output directory (default: reports/).",
    )
    args = parser.parse_args()

    print("[legacy_scan] scanning README.md, CURRENT_MAINLINE.md, docs/, paper_assets/, reports/...")
    findings = scan_all()

    out_dir = REPO_ROOT / args.output_dir
    csv_path = out_dir / "legacy_narrative_scan_v3_17.csv"
    md_path = out_dir / "legacy_narrative_scan_v3_17.md"
    config_path = out_dir / "legacy_narrative_scan_v3_17_run_config.json"

    write_csv(findings, csv_path)
    write_markdown(findings, md_path)
    write_run_config(config_path, args.strict, findings)

    counts: dict[str, int] = {}
    for f in findings:
        counts[f.classification] = counts.get(f.classification, 0) + 1

    print(f"[legacy_scan] wrote {csv_path.relative_to(REPO_ROOT)} ({len(findings)} findings)")
    print(f"[legacy_scan] wrote {md_path.relative_to(REPO_ROOT)}")
    print(f"[legacy_scan] wrote {config_path.relative_to(REPO_ROOT)}")
    print()
    print(f"  safe_negation:        {counts.get('safe_negation', 0)}")
    print(f"  legacy_section:       {counts.get('legacy_section', 0)}")
    print(f"  future_work:          {counts.get('future_work', 0)}")
    print(f"  unsafe_current_claim: {counts.get('unsafe_current_claim', 0)}")
    print(f"  ambiguous:            {counts.get('ambiguous', 0)}")

    unsafe = counts.get("unsafe_current_claim", 0)
    ambiguous = counts.get("ambiguous", 0)

    if unsafe > 0:
        print(f"\n[legacy_scan] FAIL: {unsafe} unsafe_current_claim(s) found.")
        return 1
    if args.strict and ambiguous > 0:
        print(f"\n[legacy_scan] FAIL (strict): {ambiguous} ambiguous finding(s) need review.")
        return 1

    print("\n[legacy_scan] PASS: unsafe_current_claim = 0.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
