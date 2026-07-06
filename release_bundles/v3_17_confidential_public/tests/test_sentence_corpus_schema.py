"""Tests: PDF sentence corpus JSONL schema.

Verifies that the sentence corpus produced by
build_pdf_sentence_corpus_v1.py (in toy mode) has the required schema:
every sentence row has the expected fields with valid values.

This test does NOT require real PDFs — it runs the builder in toy_mode.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
CORPUS_DIR = REPO_ROOT / "data" / "pdf_corpus_toy_v1"
SENTENCES_PATH = CORPUS_DIR / "sentences.jsonl"

REQUIRED_SENTENCE_FIELDS = [
    "paper_id",
    "pdf_filename",
    "page_number",
    "block_id",
    "sentence_id",
    "unit_id",
    "raw_text",
    "clean_text",
    "n_chars",
    "n_words",
    "section_hint",
]

VALID_SECTION_HINTS = {
    "unknown", "abstract", "introduction", "methods", "method",
    "experiments", "results", "result", "discussion", "conclusion",
    "references", "related_work", "background", "evaluation", "appendix",
}

MIN_SENTENCE_WORDS = 3  # builder skips very short sentences


def _ensure_corpus_exists():
    """Run the corpus builder in toy_mode if sentences.jsonl doesn't exist."""
    if SENTENCES_PATH.exists():
        return
    cmd = [
        sys.executable,
        str(REPO_ROOT / "scripts" / "build_pdf_sentence_corpus_v1.py"),
        "--toy_mode",
        "--output_dir", "data/pdf_corpus_toy_v1",
    ]
    # Per project constraint: avoid capture_output=True in tests.
    result = subprocess.run(
        cmd,
        cwd=str(REPO_ROOT),
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )
    assert result.returncode == 0, f"Corpus builder exited with code {result.returncode}"
    assert SENTENCES_PATH.exists(), "sentences.jsonl not produced by builder"


@pytest.fixture(scope="module", autouse=True)
def sentence_corpus():
    _ensure_corpus_exists()
    return SENTENCES_PATH


def _load_sentences():
    """Load all sentence rows from the toy corpus."""
    rows = []
    with open(SENTENCES_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                rows.append(json.loads(line))
    return rows


class TestSentenceCorpusSchema:
    """Every sentence row must have the required fields with valid types."""

    def test_sentences_file_exists(self, sentence_corpus):
        assert sentence_corpus.exists()

    def test_sentences_not_empty(self, sentence_corpus):
        rows = _load_sentences()
        assert len(rows) > 0, "Sentence corpus is empty"

    def test_required_fields_present(self, sentence_corpus):
        rows = _load_sentences()
        for i, row in enumerate(rows):
            for field in REQUIRED_SENTENCE_FIELDS:
                assert field in row, f"Row {i} missing field: {field}"

    def test_unit_id_format(self, sentence_corpus):
        """unit_id must follow paper_id::pN::bN::sN format."""
        rows = _load_sentences()
        for i, row in enumerate(rows):
            uid = row["unit_id"]
            parts = uid.split("::")
            assert len(parts) == 4, \
                f"Row {i}: unit_id '{uid}' should have 4 ::-separated parts"
            assert parts[1].startswith("p"), \
                f"Row {i}: page part '{parts[1]}' should start with 'p'"
            assert parts[2].startswith("b"), \
                f"Row {i}: block part '{parts[2]}' should start with 'b'"
            assert parts[3].startswith("s"), \
                f"Row {i}: sentence part '{parts[3]}' should start with 's'"

    def test_section_hint_valid(self, sentence_corpus):
        rows = _load_sentences()
        for i, row in enumerate(rows):
            hint = row["section_hint"]
            assert hint in VALID_SECTION_HINTS, \
                f"Row {i}: section_hint '{hint}' not in valid set"

    def test_n_words_positive(self, sentence_corpus):
        rows = _load_sentences()
        for i, row in enumerate(rows):
            assert row["n_words"] > 0, f"Row {i}: n_words must be positive"
            assert row["n_words"] >= MIN_SENTENCE_WORDS, \
                f"Row {i}: n_words={row['n_words']} below minimum {MIN_SENTENCE_WORDS}"

    def test_n_chars_matches_text(self, sentence_corpus):
        rows = _load_sentences()
        for i, row in enumerate(rows):
            expected = len(row["clean_text"])
            assert row["n_chars"] == expected, \
                f"Row {i}: n_chars={row['n_chars']} != len(clean_text)={expected}"

    def test_sentence_ids_unique_per_paper(self, sentence_corpus):
        """sentence_id must be unique within each paper (unit_id is the global key)."""
        rows = _load_sentences()
        by_paper = {}
        for row in rows:
            by_paper.setdefault(row["paper_id"], []).append(row["sentence_id"])
        for paper_id, ids in by_paper.items():
            assert len(ids) == len(set(ids)), \
                f"Duplicate sentence_id within paper {paper_id}"

    def test_unit_ids_unique(self, sentence_corpus):
        rows = _load_sentences()
        uids = [row["unit_id"] for row in rows]
        assert len(uids) == len(set(uids)), "Duplicate unit_id values"


class TestSentenceCorpusNoLeakage:
    """Sentence corpus must not contain label or evidence_text fields."""

    FORBIDDEN_CORPUS_FIELDS = {
        "true_label", "gold_label", "final_label", "human_audited",
        "oracle_hit", "candidate_label_guess", "evidence_text",
        "evidence_text_sha256", "is_strong_action", "escalation_type",
    }

    def test_no_forbidden_fields(self, sentence_corpus):
        rows = _load_sentences()
        for i, row in enumerate(rows):
            for field in self.FORBIDDEN_CORPUS_FIELDS:
                assert field not in row, \
                    f"Row {i}: forbidden field '{field}' present in sentence corpus"

    def test_corpus_no_label_reference(self, sentence_corpus):
        """Source builder must not reference label fields."""
        builder = REPO_ROOT / "scripts" / "build_pdf_sentence_corpus_v1.py"
        source = builder.read_text(encoding="utf-8")
        # Forbidden field names should only appear in comments/docstrings, not as
        # actual dictionary keys being written to the corpus.
        for field in ["true_label", "gold_label", "evidence_text"]:
            # Allow the field name in comments/docstrings (after # or """) but
            # not as a dict key being assigned to a row.
            assert f'row["{field}"]' not in source, \
                f"{field} must not be written to corpus rows"
            assert f"'{field}':" not in source.replace(f'# {field}', "").replace(f'"{field}"', "forbidden"), \
                f"{field} should not appear as a row key in corpus builder"
