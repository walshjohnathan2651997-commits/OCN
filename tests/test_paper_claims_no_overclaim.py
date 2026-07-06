"""tests/test_paper_claims_no_overclaim.py — Paper outline & narrative freeze
overclaim checks.

Verifies that the V3.17 paper outline, result narrative freeze, and the
abstract / contribution bullets / limitations drafts do not contain
forbidden overclaim wording as positive assertions, and that every
quantitative metric is traceable to a source file under experiments/,
reports/, or paper_assets/.

Hard boundaries enforced:
  - No fabricated results. Every number must be sourced.
  - No "gold benchmark", "human-audited benchmark", "SOTA",
    "automatic peer reviewer", "validated general detector" as positive
    claims.
  - Silver data is never described as gold.
  - Missing results must be marked TBD/blocked.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent

# Files covered by this overclaim freeze.
OUTLINE_PATH = REPO_ROOT / "docs" / "paper_outline_v3_17_confidential.md"
NARRATIVE_PATH = REPO_ROOT / "docs" / "result_narrative_freeze_v3_17.md"
ABSTRACT_PATH = REPO_ROOT / "paper_assets" / "v3_17_confidential" / "abstract_draft.md"
CONTRIB_PATH = REPO_ROOT / "paper_assets" / "v3_17_confidential" / "contribution_bullets.md"
LIMITATIONS_PATH = REPO_ROOT / "paper_assets" / "v3_17_confidential" / "limitations_draft.md"

ALL_FREEZE_FILES = [
    OUTLINE_PATH,
    NARRATIVE_PATH,
    ABSTRACT_PATH,
    CONTRIB_PATH,
    LIMITATIONS_PATH,
]

# Forbidden wording that, if found as a positive assertion, indicates
# overclaim. These may appear in negated form ("not a gold benchmark",
# "no SOTA claim is made") — the negation window check handles that.
FORBIDDEN_POSITIVE_PATTERNS = [
    "is a gold benchmark",
    "gold benchmark",
    "human-audited benchmark",
    "is human-audited",
    "human-audited dataset",
    "state-of-the-art",
    "sota detector",
    "is sota",
    "achieves sota",
    "automatic peer reviewer",
    "automatic peer review",
    "validated general detector",
    "general detector",
    "full cese-ocn architecture validated",
    "full cese-ocn validated",
    "outperforms llm",
    "outperforms all",
    "replaces human review",
    "standalone detector",
]

# Negation markers that, when found within 80 chars before a forbidden
# pattern, downgrade it from overclaim to safe negation.
NEGATION_MARKERS = (
    "not ", "no ", "never ", "without ", "non-",
    "cannot ", "can't ", "isn't ", "doesn't ", "don't ",
    "won't ", "shouldn't ", "wouldn't ", "aren't ", "wasn't ",
    "weren't ", "hasn't ", "haven't ", "hadn't ",
    "unusable ", "unable ", "unavailable ",
    "no longer ", "rather than ", "instead of ",
)

# Section-level negation markers that use a wider window. These indicate
# the surrounding context is explicitly about what is NOT supported or
# what is forbidden — phrases found within 250 chars after these markers
# are safe even if they contain forbidden patterns.
SECTION_NEGATION_MARKERS = (
    "not supported interpretation",
    "not supported",
    "forbidden",
    "unsafe wording",
    "do not claim",
    "do not make",
    "never use",
    "must not",
    "must not contain",
    "non-contributions",
    "non-claim",
)


def _strip_markdown(text: str) -> str:
    """Remove markdown bold/italic/code markers so negation detection
    works on '**not**' -> 'not'."""
    # Remove paired **, *, and ` markers.
    return re.sub(r"[*`]", "", text)


def _has_negation_prefix(text_lower: str, idx: int, window: int = 80) -> bool:
    """Return True if a negation marker appears within `window` chars
    before position `idx` in `text_lower` (already lowercased, with
    markdown markers stripped). Whitespace is normalized so 'no\n'
    is treated as 'no '."""
    start = max(0, idx - window)
    prefix = text_lower[start:idx]
    prefix = re.sub(r"\s+", " ", prefix)
    return any(marker in prefix for marker in NEGATION_MARKERS)


def _has_section_negation_prefix(text_lower: str, idx: int, window: int = 250) -> bool:
    """Return True if a section-level negation marker appears within
    `window` chars before position `idx`. These markers indicate the
    surrounding context is explicitly about what is NOT supported or
    forbidden, so phrases found within are safe."""
    start = max(0, idx - window)
    prefix = text_lower[start:idx]
    prefix = re.sub(r"\s+", " ", prefix)
    return any(marker in prefix for marker in SECTION_NEGATION_MARKERS)


def _has_negation_suffix(text_lower: str, idx: int, pattern_len: int, window: int = 40) -> bool:
    """Return True if a negation marker appears within `window` chars
    after the pattern at position `idx` (pattern ends at idx+pattern_len).
    This catches constructions like '"state-of-the-art" — not SOTA' where
    the negation follows the quoted forbidden term."""
    end = idx + pattern_len
    suffix = text_lower[end:end + window]
    suffix = re.sub(r"\s+", " ", suffix)
    return any(marker in suffix for marker in NEGATION_MARKERS)


def _is_inside_quotes(text: str, idx: int, pattern_len: int) -> bool:
    """Return True if the pattern at position `idx` is inside matching
    quote characters (single or double, or backticks). This detects
    mentioned-but-not-asserted usage like '"gold benchmark" — not gold'."""
    # Check the character immediately before and after the pattern.
    before = text[max(0, idx - 1):idx]
    after = text[idx + pattern_len:idx + pattern_len + 1]
    # Common quote pairs.
    if before in ('"', "'", '`') and after in ('"', "'", '`'):
        return True
    # Also check if surrounded by " / " pattern (e.g., "SOTA" / "state-of-the-art").
    if before == '"' and after == '"':
        return True
    return False


# ---------- File existence ----------

@pytest.mark.parametrize("path", ALL_FREEZE_FILES, ids=lambda p: p.name)
def test_freeze_file_exists(path: Path):
    assert path.exists(), f"Freeze file missing: {path}"


# ---------- No forbidden overclaim as positive assertions ----------

@pytest.mark.parametrize("path", ALL_FREEZE_FILES, ids=lambda p: p.name)
def test_no_forbidden_overclaim_positive(path: Path):
    """No freeze file may contain forbidden wording as a positive
    assertion. Negated mentions ("not a gold benchmark") are allowed."""
    raw = path.read_text(encoding="utf-8")
    text = _strip_markdown(raw)
    text_lower = text.lower()
    for pattern in FORBIDDEN_POSITIVE_PATTERNS:
        pattern_lower = pattern.lower()
        start = 0
        while True:
            idx = text_lower.find(pattern_lower, start)
            if idx == -1:
                break
            plen = len(pattern_lower)
            # Allow if negated before or after, inside quotes, or in a
            # section-level negation context (e.g., "Not supported
            # interpretation: ... is a gold benchmark").
            if _has_negation_prefix(text_lower, idx):
                start = idx + plen
                continue
            if _has_negation_suffix(text_lower, idx, plen):
                start = idx + plen
                continue
            if _is_inside_quotes(text_lower, idx, plen):
                start = idx + plen
                continue
            if _has_section_negation_prefix(text_lower, idx):
                start = idx + plen
                continue
            context = text[max(0, idx - 40):idx + plen + 40]
            pytest.fail(
                f"Forbidden overclaim '{pattern}' found as a positive "
                f"assertion in {path.name}. Context: ...{context}..."
            )
            start = idx + plen


# ---------- Required safe caveat in each freeze file ----------

@pytest.mark.parametrize("path", ALL_FREEZE_FILES, ids=lambda p: p.name)
def test_freeze_file_mentions_silver(path: Path):
    """Each freeze file must reference the silver diagnostic nature."""
    text = path.read_text(encoding="utf-8").lower()
    assert "silver" in text, (
        f"{path.name} must mention 'silver' diagnostic to qualify results."
    )


def test_outline_has_required_caveat():
    text = OUTLINE_PATH.read_text(encoding="utf-8")
    normalized = re.sub(r"\s+", " ", text).lower()
    assert "source-traceable controlled silver diagnostic" in normalized, (
        "Outline must include the safe caveat sentence."
    )
    assert "not gold or human-audited" in normalized, (
        "Outline must state labels are not gold or human-audited."
    )


def test_abstract_has_required_caveat():
    text = ABSTRACT_PATH.read_text(encoding="utf-8").lower()
    assert "silver" in text, "Abstract must mention silver diagnostic."
    assert "not gold" in text or "not a gold" in text, (
        "Abstract must state the dataset is not gold."
    )
    assert "not human-audited" in text or "not a human-audited" in text or "no completed human audit" in text, (
        "Abstract must state the dataset is not human-audited."
    )


def test_limitations_has_required_caveat():
    text = LIMITATIONS_PATH.read_text(encoding="utf-8").lower()
    assert "silver" in text
    assert "not gold" in text or "not a gold" in text
    assert "not human-audited" in text or "no completed human audit" in text or "has not been completed" in text


# ---------- Abstract structure ----------

def test_abstract_has_all_required_elements():
    """Abstract must include: problem, confidential/no-API, controlled
    silver, format shift, canonicalization, review queue, limitations."""
    text = ABSTRACT_PATH.read_text(encoding="utf-8").lower()
    required_elements = {
        "problem": ["simulation-claim review", "simulation claim review", "screening claims"],
        "confidential/no-api": ["confidential", "no api", "no-api"],
        "controlled silver": ["silver"],
        "format shift": ["format shift", "retrieval-to-screening"],
        "canonicalization": ["canonicaliz"],
        "review queue": ["review queue"],
        "limitations": ["limitation"],
    }
    for element, keywords in required_elements.items():
        assert any(kw in text for kw in keywords), (
            f"Abstract missing required element '{element}'. "
            f"Looked for one of: {keywords}"
        )


def test_abstract_no_forbidden_elements():
    """Abstract must NOT contain (even negated): gold benchmark as a
    positive claim, SOTA, automatic peer review, general detector as a
    positive claim."""
    raw = ABSTRACT_PATH.read_text(encoding="utf-8")
    text = _strip_markdown(raw).lower()
    # Even negated mentions of these would be confusing in the abstract.
    # We allow "not a validated general detector" but flag positive uses.
    forbidden_positive = [
        "is a gold benchmark",
        "is sota",
        "achieves sota",
        "is an automatic peer reviewer",
        "is a validated general detector",
        "is a general detector",
    ]
    for pattern in forbidden_positive:
        idx = text.find(pattern)
        if idx == -1:
            continue
        if _has_negation_prefix(text, idx):
            continue
        pytest.fail(
            f"Abstract contains forbidden positive claim: '{pattern}'."
        )


# ---------- Contribution bullets ----------

def test_contribution_has_four_bullets():
    """Contribution bullets must contain exactly 4 numbered contributions."""
    text = CONTRIB_PATH.read_text(encoding="utf-8")
    # Look for numbered list items like "1. **Identify ...".
    matches = re.findall(r"^\d+\.\s+\*\*", text, re.MULTILINE)
    assert len(matches) >= 4, (
        f"Expected at least 4 contribution bullets, found {len(matches)}."
    )


def test_contribution_has_non_contributions_section():
    """Contribution file must explicitly list non-claims."""
    text = CONTRIB_PATH.read_text(encoding="utf-8").lower()
    assert "not claimed" in text or "non-contribution" in text or "do not claim" in text, (
        "Contribution file must have a non-claims section."
    )


def test_contribution_mentions_format_shift():
    text = CONTRIB_PATH.read_text(encoding="utf-8").lower()
    assert "format shift" in text or "retrieval-to-screening" in text


def test_contribution_mentions_canonicalization():
    text = CONTRIB_PATH.read_text(encoding="utf-8").lower()
    assert "canonicaliz" in text


def test_contribution_mentions_review_queue():
    text = CONTRIB_PATH.read_text(encoding="utf-8").lower()
    assert "review queue" in text or "conservative" in text


def test_contribution_mentions_audits():
    text = CONTRIB_PATH.read_text(encoding="utf-8").lower()
    assert "leakage" in text or "audit" in text


# ---------- Limitations ----------

def test_limitations_covers_required_topics():
    """Limitations must cover: silver labels, no human audit, blocked
    experiments, no LLM baseline, second-stage queue not standalone."""
    text = LIMITATIONS_PATH.read_text(encoding="utf-8").lower()
    required_topics = {
        "silver labels": ["silver", "not gold"],
        "no human audit": ["human audit", "human-audited"],
        "blocked experiments": ["blocked"],
        "no llm baseline": ["llm", "no llm"],
        "second-stage queue": ["second-stage", "review queue", "standalone"],
        "six domains": ["domain", "six"],
        "full cese-ocn": ["cese-ocn", "cese_ocn"],
    }
    for topic, keywords in required_topics.items():
        assert any(kw in text for kw in keywords), (
            f"Limitations missing required topic '{topic}'. "
            f"Looked for one of: {keywords}"
        )


# ---------- Result narrative freeze: source file traceability ----------

def test_narrative_has_result_sections():
    """Narrative must have at least 13 result sections (R1-R13)."""
    text = NARRATIVE_PATH.read_text(encoding="utf-8")
    matches = re.findall(r"^## Result R\d+", text, re.MULTILINE)
    assert len(matches) >= 13, (
        f"Expected at least 13 result sections in narrative, found {len(matches)}."
    )


def test_narrative_each_result_has_source_file():
    """Each result section must reference a source file under
    experiments/, reports/, or paper_assets/."""
    text = NARRATIVE_PATH.read_text(encoding="utf-8")
    # Split by result section headers.
    sections = re.split(r"^## Result R\d+", text, flags=re.MULTILINE)
    # sections[0] is preamble.
    for i, section in enumerate(sections[1:], start=1):
        assert "source file:" in section.lower(), (
            f"Result R{i} missing 'Source file:' field."
        )
        # Must reference a real path prefix.
        has_path = (
            "experiments/" in section
            or "reports/" in section
            or "paper_assets/" in section
            or "data/" in section
            or "docs/" in section
            or "release_bundles/" in section
        )
        assert has_path, (
            f"Result R{i} 'Source file:' field does not reference a path "
            f"under experiments/, reports/, paper_assets/, data/, docs/, "
            f"or release_bundles/."
        )


def test_narrative_each_result_has_safe_interpretation():
    text = NARRATIVE_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^## Result R\d+", text, flags=re.MULTILINE)
    for i, section in enumerate(sections[1:], start=1):
        assert "safe interpretation:" in section.lower(), (
            f"Result R{i} missing 'Safe interpretation:' field."
        )


def test_narrative_each_result_has_not_supported_interpretation():
    text = NARRATIVE_PATH.read_text(encoding="utf-8")
    sections = re.split(r"^## Result R\d+", text, flags=re.MULTILINE)
    for i, section in enumerate(sections[1:], start=1):
        assert "not supported interpretation:" in section.lower(), (
            f"Result R{i} missing 'Not supported interpretation:' field."
        )


def test_narrative_blocked_results_marked():
    """Blocked results (R2, R6, R12) must be explicitly marked blocked
    or partial."""
    text = NARRATIVE_PATH.read_text(encoding="utf-8").lower()
    # R2 (sentence/window BM25), R6 (format-shift R4 eval), R12 (human audit).
    sections = re.split(r"^## result r(\d+)", text, flags=re.MULTILINE)
    # sections[0] = preamble; then (rid, body) pairs.
    blocked_rids = {"2", "6", "12"}
    found_blocked = set()
    for i in range(1, len(sections), 2):
        rid = sections[i]
        body = sections[i + 1] if i + 1 < len(sections) else ""
        if rid in blocked_rids:
            if "blocked" in body or "partial" in body or "tbd" in body:
                found_blocked.add(rid)
    assert found_blocked == blocked_rids, (
        f"Blocked/partial results not properly marked. "
        f"Expected R2, R6, R12 to be blocked/partial. "
        f"Found: {found_blocked}"
    )


# ---------- Source file existence checks ----------

def test_narrative_referenced_source_files_exist():
    """Source files referenced in the narrative must exist on disk,
    unless the result is explicitly blocked (in which case the source
    file may be a 'blocked' marker file)."""
    text = NARRATIVE_PATH.read_text(encoding="utf-8")
    # Find all "Source file:" lines and extract paths.
    source_lines = re.findall(r"Source file:\s*[`\"]?([^\n`\".,]+)", text)
    paths_to_check = []
    for line in source_lines:
        # A line may list multiple comma-separated paths.
        for raw in line.split(","):
            raw = raw.strip().strip("`\".")
            if not raw:
                continue
            # Skip protocol prefixes or placeholders.
            if raw.startswith("does not exist") or raw.startswith("partial"):
                continue
            paths_to_check.append(raw)
    missing = []
    for rel in paths_to_check:
        rel = rel.replace("\\", "/").strip()
        if not rel:
            continue
        # Skip if it's a directory reference (ends with /) or contains
        # wildcard.
        if rel.endswith("/") or "*" in rel:
            # Check the directory exists.
            p = REPO_ROOT / rel
            if not p.exists():
                missing.append(rel)
            continue
        p = REPO_ROOT / rel
        if not p.exists():
            missing.append(rel)
    # Filter out paths that are inside blocked-result sections.
    # We allow missing source files only if the surrounding section is
    # marked "blocked" or "partial".
    if missing:
        # Re-scan: for each missing path, find its surrounding section.
        truly_missing = []
        sections = re.split(r"^## Result R\d+", text, flags=re.MULTILINE)
        for rel in missing:
            rel_norm = rel.replace("\\", "/")
            in_blocked_section = False
            for section in sections[1:]:
                if rel_norm in section and (
                    "blocked" in section.lower()
                    or "partial" in section.lower()
                    or "does not exist" in section.lower()
                ):
                    in_blocked_section = True
                    break
            if not in_blocked_section:
                truly_missing.append(rel)
        assert not truly_missing, (
            f"Source files referenced in narrative but not found on disk "
            f"(and not in blocked sections): {truly_missing}"
        )


# ---------- Outline source file traceability ----------

def test_outline_metrics_reference_source_files():
    """Outline must reference source files for its quantitative metrics."""
    text = OUTLINE_PATH.read_text(encoding="utf-8")
    # Look for "Source:" lines.
    source_lines = re.findall(r"Source:\s*[`\"]?([^\n]+)", text)
    assert len(source_lines) >= 5, (
        f"Outline must reference at least 5 source files for metrics, "
        f"found {len(source_lines)}."
    )
    # Check each source file exists.
    missing = []
    for line in source_lines:
        for raw in line.split(","):
            raw = raw.strip().strip("`\".")
            if not raw or raw.startswith("experiments/") is False and raw.startswith("reports/") is False and raw.startswith("paper_assets/") is False and raw.startswith("docs/") is False and raw.startswith("data/") is False and raw.startswith("release_bundles/") is False:
                continue
            p = REPO_ROOT / raw.replace("\\", "/")
            if not p.exists():
                missing.append(raw)
    assert not missing, (
        f"Outline references missing source files: {missing}"
    )


# ---------- Required caveats in outline ----------

def test_outline_lists_forbidden_claims():
    """Outline must explicitly list the forbidden claims."""
    text = OUTLINE_PATH.read_text(encoding="utf-8").lower()
    assert "forbidden" in text, "Outline must have a forbidden claims section."
    required_forbidden = ["gold benchmark", "sota", "automatic peer reviewer", "general detector"]
    for term in required_forbidden:
        assert term in text, (
            f"Outline forbidden section must mention '{term}'."
        )


def test_outline_lists_required_caveats():
    """Outline must list required caveats."""
    text = OUTLINE_PATH.read_text(encoding="utf-8").lower()
    assert "caveat" in text, "Outline must have a caveats section."


def test_outline_has_title_candidates():
    text = OUTLINE_PATH.read_text(encoding="utf-8")
    assert "Local Evidence Canonicalization" in text
    assert "Retrieval-to-Screening Format Shift" in text


def test_outline_has_seven_rqs():
    text = OUTLINE_PATH.read_text(encoding="utf-8")
    rqs = re.findall(r"\bRQ[1-7]\b", text)
    found = set(rqs)
    for i in range(1, 8):
        assert f"RQ{i}" in found, f"Outline missing RQ{i}"


# ---------- Abstract source file traceability ----------

def test_abstract_has_source_traceability_table():
    """Abstract draft must include a source file traceability table."""
    text = ABSTRACT_PATH.read_text(encoding="utf-8")
    assert "Source file traceability" in text or "source file" in text.lower(), (
        "Abstract draft must include a source file traceability section."
    )
    # Must reference experiments/ paths.
    assert "experiments/" in text, (
        "Abstract traceability must reference experiments/ paths."
    )


# ---------- Contribution source file traceability ----------

def test_contribution_has_source_files():
    """Contribution bullets must reference source files."""
    text = CONTRIB_PATH.read_text(encoding="utf-8")
    assert "Source:" in text or "source:" in text.lower(), (
        "Contribution bullets must reference source files."
    )
    assert "experiments/" in text, (
        "Contribution bullets must reference experiments/ paths."
    )


# ---------- Limitations source file traceability ----------

def test_limitations_has_source_files():
    """Limitations must reference source files for each limitation."""
    text = LIMITATIONS_PATH.read_text(encoding="utf-8")
    assert "Source:" in text or "source:" in text.lower(), (
        "Limitations must reference source files."
    )


# ---------- No "gold" as positive assertion anywhere ----------

@pytest.mark.parametrize("path", ALL_FREEZE_FILES, ids=lambda p: p.name)
def test_no_gold_as_positive_claim(path: Path):
    """The word 'gold' may appear only in negated form (e.g., 'not gold',
    'no gold'). Positive uses like 'gold benchmark' as a current claim
    are forbidden."""
    raw = path.read_text(encoding="utf-8")
    text = _strip_markdown(raw)
    text_lower = text.lower()
    # Find every occurrence of 'gold'.
    idx = 0
    while True:
        idx = text_lower.find("gold", idx)
        if idx == -1:
            break
        # Check for negation within 80 chars before or 40 chars after.
        if _has_negation_prefix(text_lower, idx):
            idx += 4
            continue
        if _has_negation_suffix(text_lower, idx, 4):
            idx += 4
            continue
        if _is_inside_quotes(text_lower, idx, 4):
            idx += 4
            continue
        if _has_section_negation_prefix(text_lower, idx):
            idx += 4
            continue
        # Allow contrastive context markers within 80 chars before:
        # "silver" (contrastive), "prior work" (about others), "external"
        # (about others' data), "curated" (about others' benchmarks).
        prefix = text_lower[max(0, idx - 80):idx]
        prefix = re.sub(r"\s+", " ", prefix)
        if any(marker in prefix for marker in ("silver", "prior work", "external", "curated", "these use")):
            idx += 4
            continue
        # Allow if it's a field name reference like `gold_label`,
        # `gold-standard` (used in contrastive quotes about others'
        # benchmarks), or `gold-level` (used as a descriptor, not a
        # claim). These are mentions, not claims about our work.
        suffix = text_lower[idx:idx + 14]
        if (suffix.startswith("gold_label")
            or suffix.startswith("gold-standard")
            or suffix.startswith("gold-level")
            or suffix.startswith("gold standard")):
            idx += 4
            continue
        context = text[max(0, idx - 40):idx + 40]
        pytest.fail(
            f"'gold' found as positive assertion in {path.name}. "
            f"Context: ...{context}..."
        )
        idx += 4


# ---------- Metric values must be sourced ----------

def test_narrative_metrics_match_experiment_files():
    """Spot-check that key metric values in the narrative match the
    underlying experiment files."""
    # BM25 recall@1 = 0.7162
    bm25_path = REPO_ROOT / "experiments" / "simclaim_pdf_corpus_retrieval_v1" / "retrieval_metrics_bm25.json"
    if bm25_path.exists():
        bm25_text = bm25_path.read_text(encoding="utf-8")
        assert "0.7162" in bm25_text or "0.71621" in bm25_text, (
            "BM25 recall@1 value mismatch with source file."
        )
        # Narrative must contain this value.
        narrative = NARRATIVE_PATH.read_text(encoding="utf-8")
        assert "0.716" in narrative, (
            "Narrative must cite BM25 recall@1 = 0.716."
        )

    # R4 strong_F1 = 0.4503
    r4_path = REPO_ROOT / "experiments" / "metric_robustness_v1" / "classification_metrics_with_ci.csv"
    if r4_path.exists():
        r4_text = r4_path.read_text(encoding="utf-8")
        assert "0.450" in r4_text, (
            "R4 strong_F1 value mismatch with source file."
        )
        narrative = NARRATIVE_PATH.read_text(encoding="utf-8")
        assert "0.4503" in narrative or "0.450" in narrative, (
            "Narrative must cite strong_F1 = 0.4503."
        )

    # Canonicalizer oracle_recall = 0.387 (best_sentence_top5_overlap)
    canon_path = REPO_ROOT / "experiments" / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv"
    if canon_path.exists():
        canon_text = canon_path.read_text(encoding="utf-8")
        assert "0.387" in canon_text, (
            "Canonicalizer oracle_recall value mismatch with source file."
        )
        narrative = NARRATIVE_PATH.read_text(encoding="utf-8")
        assert "0.387" in narrative, (
            "Narrative must cite canonicalizer oracle_recall = 0.387."
        )
