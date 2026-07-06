"""Tests for P6-3: CSV -> JSONL annotation import robustness.

Verifies:
- CSV with empty escalation_label imports (label becomes None).
- evidence_vector 8 core fields are parsed as float.
- claim_tiers / support_tiers parsed as int.
- evidence_gap_labels supports comma OR semicolon separators.
- annotation.annotators supports single or semicolon-separated multi.
- annotation metadata correctly enters nested annotation block.
- Imported JSONL can be passed to fill_escalation_labels to fill labels.
- Validation failure message includes row number + field.

ocn-29: Most tests now run IN-PROCESS via ``ia._row_to_record(row)`` +
``ClaimEvidenceSample(**rec)`` instead of spawning a subprocess per
case. Only ONE subprocess smoke test remains, and it uses a log file
(NOT ``capture_output=True``) so a closed pipe under TRAE / pytest /
timeout-wrapper cannot deadlock the suite. This drops the per-file
subprocess spawn count from ~15 to 1.
"""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

SCRIPTS_DIR = ROOT / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

import import_annotations as ia
import fill_escalation_labels as fel
from cese.data.schema import ClaimEvidenceSample


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

# Column order matches data/templates/pilot_annotation_template.csv.
COLUMNS = [
    "sample_id", "logical_sample_id", "domain", "source_type",
    "claim_text", "evidence_text", "claim_family", "template_id", "split",
    "evidence_vector.alignment", "evidence_vector.transparency",
    "evidence_vector.coverage", "evidence_vector.traceability",
    "evidence_vector.boundary", "evidence_vector.uncertainty",
    "evidence_vector.causal_id", "evidence_vector.risk_utility",
    "evidence_confidence.alignment", "evidence_confidence.transparency",
    "evidence_confidence.coverage", "evidence_confidence.traceability",
    "evidence_confidence.boundary", "evidence_confidence.uncertainty",
    "evidence_confidence.causal_id", "evidence_confidence.risk_utility",
    "claim_tiers.scope", "claim_tiers.causal",
    "claim_tiers.action", "claim_tiers.certainty",
    "support_tiers.scope", "support_tiers.causal",
    "support_tiers.action", "support_tiers.certainty",
    "contradiction_label", "escalation_label",
    "escalation_type", "evidence_gap_labels", "rewrite_target",
    "annotator_id", "annotation_round", "agreement_score",
    "is_human_audited", "evidence_spans", "extraction_method",
]


def _base_row(sample_id: str = "s1", **overrides) -> dict:
    row = {col: "" for col in COLUMNS}
    row.update({
        "sample_id": sample_id,
        "logical_sample_id": sample_id,
        "domain": "academic_claim",
        "source_type": "oracle",
        "claim_text": f"claim {sample_id}",
        "evidence_text": f"evidence {sample_id}",
        "claim_family": "descriptive",
        "template_id": "tpl-test",
        "split": "train",
        "contradiction_label": "0",
        "annotator_id": "ann-01",
        "annotation_round": "1",
        "is_human_audited": "0",
    })
    # Fill evidence vector + confidence with defaults 1.0.
    for d in ["alignment", "transparency", "coverage", "traceability",
              "boundary", "uncertainty", "causal_id", "risk_utility"]:
        row[f"evidence_vector.{d}"] = "1.0"
        row[f"evidence_confidence.{d}"] = "1.0"
    # Default tiers: claim=support=0 (no overclaim -> label 0).
    for d in ["scope", "causal", "action", "certainty"]:
        row[f"claim_tiers.{d}"] = "0"
        row[f"support_tiers.{d}"] = "0"
    row.update(overrides)
    return row


def _write_csv(path: Path, rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=COLUMNS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def _row_to_validated_record(row: dict) -> dict:
    """Convert a CSV row to a validated record IN-PROCESS.

    Mirrors what ``scripts/import_annotations.py`` does internally
    (``_row_to_record`` + ``ClaimEvidenceSample(**rec)``) but without
    spawning a subprocess. Raises on validation failure so tests can
    assert ``pytest.raises`` for invalid rows.
    """
    rec = ia._row_to_record(row)
    # Will raise ValidationError on schema violations.
    ClaimEvidenceSample(**rec)
    return rec


def _load_jsonl(path: Path) -> list[dict]:
    out = []
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# ---------------------------------------------------------------------------
# empty escalation_label
# ---------------------------------------------------------------------------


def test_csv_empty_label_imports_as_none():
    """CSV row with empty escalation_label must import successfully and
    record escalation_label=None so fill_escalation_labels fills it."""
    row = _base_row("s1", escalation_label="")
    rec = _row_to_validated_record(row)
    # Empty label must be None (not default 0, which would conflict with
    # tier-derived labels).
    assert rec["escalation_label"] is None


def test_csv_na_label_imports_as_none():
    """CSV row with 'NA' escalation_label must import as None."""
    row = _base_row("s1", escalation_label="NA")
    rec = _row_to_validated_record(row)
    assert rec["escalation_label"] is None


# ---------------------------------------------------------------------------
# evidence_vector float parsing
# ---------------------------------------------------------------------------


def test_evidence_vector_fields_parsed_as_float():
    """All 8 evidence_vector fields must be parsed as float."""
    row = _base_row("s1")
    row["evidence_vector.alignment"] = "0.5"
    row["evidence_vector.transparency"] = "1"
    row["evidence_vector.coverage"] = "0.0"
    row["evidence_vector.traceability"] = "0.25"
    row["evidence_vector.boundary"] = "NA"  # -> default 0.0
    row["evidence_vector.uncertainty"] = ""
    row["evidence_vector.causal_id"] = "null"  # -> default 0.0
    row["evidence_vector.risk_utility"] = "0.75"
    rec = _row_to_validated_record(row)
    ev = rec["evidence_vector"]
    assert ev["alignment"] == 0.5
    assert isinstance(ev["alignment"], float)
    assert ev["transparency"] == 1.0
    assert isinstance(ev["transparency"], float)
    assert ev["coverage"] == 0.0
    assert ev["traceability"] == 0.25
    # NA / empty / null -> default 0.0
    assert ev["boundary"] == 0.0
    assert ev["uncertainty"] == 0.0
    assert ev["causal_id"] == 0.0
    assert ev["risk_utility"] == 0.75
    # All values must be float instances.
    for v in ev.values():
        assert isinstance(v, float), f"{v!r} is not float"


# ---------------------------------------------------------------------------
# tier fields int parsing
# ---------------------------------------------------------------------------


def test_tier_fields_parsed_as_int():
    """claim_tiers / support_tiers must be parsed as int."""
    row = _base_row("s1")
    row["claim_tiers.scope"] = "3"
    row["claim_tiers.causal"] = "2.0"  # tolerate "2.0" -> 2
    row["claim_tiers.action"] = "0"
    row["claim_tiers.certainty"] = "NA"  # -> default 0
    row["support_tiers.scope"] = "1"
    row["support_tiers.causal"] = "2"
    row["support_tiers.action"] = ""
    row["support_tiers.certainty"] = "null"  # -> default 0
    rec = _row_to_validated_record(row)
    ct = rec["claim_tiers"]
    st = rec["support_tiers"]
    assert ct["scope"] == 3
    assert isinstance(ct["scope"], int)
    assert ct["causal"] == 2  # "2.0" -> 2
    assert isinstance(ct["causal"], int)
    assert ct["action"] == 0
    assert ct["certainty"] == 0  # NA -> 0
    assert st["scope"] == 1
    assert isinstance(st["scope"], int)
    assert st["action"] == 0  # "" -> 0
    assert st["certainty"] == 0  # null -> 0


# ---------------------------------------------------------------------------
# evidence_gap_labels separator support
# ---------------------------------------------------------------------------


def test_gap_labels_comma_separator():
    """evidence_gap_labels supports comma-separated values."""
    row = _base_row("s1", escalation_label="1",
                    evidence_gap_labels="alignment_missing,coverage_missing")
    rec = _row_to_validated_record(row)
    assert rec["evidence_gap_labels"] == [
        "alignment_missing", "coverage_missing",
    ]


def test_gap_labels_semicolon_separator():
    """evidence_gap_labels supports semicolon-separated values."""
    row = _base_row("s1", escalation_label="1",
                    evidence_gap_labels="alignment_missing;coverage_missing")
    rec = _row_to_validated_record(row)
    assert rec["evidence_gap_labels"] == [
        "alignment_missing", "coverage_missing",
    ]


def test_gap_labels_mixed_separator():
    """evidence_gap_labels supports mixed comma + semicolon separators."""
    row = _base_row("s1", escalation_label="1",
                    evidence_gap_labels="alignment_missing, coverage_missing;boundary_missing")
    rec = _row_to_validated_record(row)
    assert rec["evidence_gap_labels"] == [
        "alignment_missing", "coverage_missing", "boundary_missing",
    ]


# ---------------------------------------------------------------------------
# annotation.annotators single + multi
# ---------------------------------------------------------------------------


def test_annotators_single():
    """annotation.annotators correctly captures a single annotator."""
    row = _base_row("s1", annotator_id="ann-01")
    rec = _row_to_validated_record(row)
    ann = rec["annotation"]
    assert ann["annotators"] == ["ann-01"]


def test_annotators_multi_semicolon():
    """annotation.annotators supports semicolon-separated multi-annotators."""
    row = _base_row("s1", annotator_id="ann-01;ann-02;ann-03")
    rec = _row_to_validated_record(row)
    ann = rec["annotation"]
    assert ann["annotators"] == ["ann-01", "ann-02", "ann-03"]


def test_annotation_metadata_nested_block():
    """annotation metadata fields correctly populate the nested block."""
    row = _base_row(
        "s1",
        annotator_id="ann-01;ann-02",
        annotation_round="2",
        agreement_score="0.85",
        is_human_audited="1",
        evidence_spans="span1,span2",
        extraction_method="human_oracle",
    )
    rec = _row_to_validated_record(row)
    ann = rec["annotation"]
    assert ann["annotators"] == ["ann-01", "ann-02"]
    assert ann["annotation_round"] == 2
    assert ann["agreement_score"] == 0.85
    assert ann["is_human_audited"] is True
    assert ann["evidence_spans"] == ["span1", "span2"]
    assert ann["extraction_method"] == "human_oracle"


# ---------------------------------------------------------------------------
# import -> fill_escalation_labels end-to-end (in-process)
# ---------------------------------------------------------------------------


def test_imported_jsonl_can_fill_escalation_labels():
    """Imported JSONL with empty escalation_label must be fillable by
    fill_escalation_labels (which derives labels from claim vs support
    tiers without conflicts)."""
    rows = [
        _base_row("s1",  # supported
                  **{"claim_tiers.scope": "2", "support_tiers.scope": "2"},
                  escalation_label=""),
        _base_row("s2",  # overclaim on causal
                  **{"claim_tiers.causal": "3", "support_tiers.causal": "1"},
                  escalation_label=""),
    ]
    recs = [_row_to_validated_record(r) for r in rows]
    # Both should have escalation_label=None before fill.
    assert recs[0]["escalation_label"] is None
    assert recs[1]["escalation_label"] is None
    # Run fill_escalation_labels in-process.
    filled, summary = fel.fill_escalation_labels(recs)
    assert summary["total_samples"] == 2
    assert summary["changed_labels"] == 2  # both were None, now filled
    assert filled[0]["escalation_label"] == 0  # supported
    assert filled[1]["escalation_label"] == 1  # overclaim
    assert filled[1]["escalation_type"] == ["causal"]


# ---------------------------------------------------------------------------
# validation error includes row number + field
# ---------------------------------------------------------------------------


def test_validation_error_includes_row_number(tmp_path, caplog):
    """Validation error message must include the row number so annotators
    can locate the offending row in the CSV. Uses ``ia.main`` in-process
    with ``caplog`` to capture the logger warning (no subprocess)."""
    csv_path = tmp_path / "ann.csv"
    # Row 1 valid, Row 2 has an invalid domain.
    rows = [
        _base_row("s1"),
        _base_row("s2", domain="not_a_real_domain"),
    ]
    _write_csv(csv_path, rows)
    out_path = tmp_path / "imported.jsonl"

    # Run in-process so we can capture the logger warning via caplog.
    import logging
    with caplog.at_level(logging.WARNING, logger="import_annotations"):
        ia.main(["--input", str(csv_path), "--output", str(out_path)])

    # The error log must reference "Row 2" and the offending field "domain".
    combined = caplog.text
    assert "Row 2" in combined, (
        f"error must reference row number; got:\n{combined}"
    )
    assert "domain" in combined, (
        f"error must reference offending field; got:\n{combined}"
    )
    # Only s1 should be in the output (s2 skipped).
    recs = _load_jsonl(out_path)
    assert len(recs) == 1
    assert recs[0]["sample_id"] == "s1"


# ---------------------------------------------------------------------------
# escalation_type empty + comma
# ---------------------------------------------------------------------------


def test_escalation_type_empty_or_comma():
    """escalation_type empty -> []; comma-separated -> list."""
    row_empty = _base_row("s1", escalation_type="")
    row_semi = _base_row("s2", escalation_type="scope;causal")
    rec_empty = _row_to_validated_record(row_empty)
    rec_semi = _row_to_validated_record(row_semi)
    assert rec_empty["escalation_type"] == []
    assert rec_semi["escalation_type"] == ["scope", "causal"]


# ---------------------------------------------------------------------------
# ocn-29: SINGLE subprocess smoke test (no capture_output).
# ---------------------------------------------------------------------------


def _run_subprocess_with_log(cmd, cwd, timeout, log_path):
    """Run a subprocess writing stdout/stderr to a log file (NOT a
    capture pipe). On timeout, kill the whole process tree. Returns
    (returncode, log_text_tail)."""
    import os
    import signal
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_file = log_path.open("wb")
    try:
        proc = subprocess.Popen(
            cmd, cwd=str(cwd),
            stdin=subprocess.DEVNULL,
            stdout=log_file,
            stderr=subprocess.STDOUT,
            start_new_session=True,
        )
    finally:
        log_file.close()
    try:
        proc.wait(timeout=timeout)
    except subprocess.TimeoutExpired:
        if sys.platform.startswith("win"):
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=15, check=False,
            )
        else:
            try:
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            pass
    text = log_path.read_text(encoding="utf-8", errors="replace")
    tail = text[-4000:] if len(text) > 4000 else text
    return proc.returncode, tail


def test_subprocess_smoke_import_annotations(tmp_path):
    """SINGLE subprocess smoke test (ocn-29): confirm the CLI entry
    point still works end-to-end. All other import tests run in-process.
    Uses a log file (not capture_output) so a closed pipe under TRAE /
    pytest / timeout-wrapper cannot deadlock. Tree-kills on timeout."""
    csv_path = tmp_path / "ann.csv"
    _write_csv(csv_path, [_base_row("s1", escalation_label="1")])
    out_path = tmp_path / "imported.jsonl"
    log_path = tmp_path / "import_smoke.log"
    cmd = [
        sys.executable, "-u", "scripts/import_annotations.py",
        "--input", str(csv_path),
        "--output", str(out_path),
    ]
    rc, tail = _run_subprocess_with_log(
        cmd, cwd=ROOT, timeout=120, log_path=log_path,
    )
    assert rc == 0, f"import subprocess failed (rc={rc}); log tail:\n{tail}"
    recs = _load_jsonl(out_path)
    assert len(recs) == 1
    assert recs[0]["escalation_label"] == 1


# ---------------------------------------------------------------------------
# ocn-29: subprocess timeout + tree-kill (kept from P5).
# ---------------------------------------------------------------------------


def test_subprocess_timeout_kills_process_tree(tmp_path):
    """A hanging subprocess must be killed on timeout and leave no
    lingering process. We simulate a hang with python -c 'import time;
    time.sleep(300)' and a 2s timeout."""
    import time
    sentinel = tmp_path / "started.flag"
    cmd = [
        sys.executable, "-u", "-c",
        f"open(r'{sentinel}', 'w').close(); "
        "import time; time.sleep(300)",
    ]
    log_path = tmp_path / "timeout_test.log"
    t0 = time.monotonic()
    rc, _ = _run_subprocess_with_log(
        cmd, cwd=ROOT, timeout=2, log_path=log_path,
    )
    dt = time.monotonic() - t0
    # Must return well under the 300s sleep — bounded by timeout + kill.
    assert dt < 30, f"timeout handling took too long: {dt:.1f}s"
    # Sentinel proves the child actually started (so the kill is real).
    assert sentinel.exists()
    # Killed process returns non-zero (or None-ish on some platforms;
    # the strong assertion is the wall-clock bound above).
    assert rc != 0
    # Give the OS a moment to reap the killed process.
    time.sleep(0.5)


def test_subprocess_does_not_depend_on_writable_stdout(tmp_path):
    """Even with stdout/stderr redirected to a file (not a pipe),
    import_annotations.py must complete successfully and write its
    JSONL output. This confirms the CLI never depends on a writable
    stdout pipe."""
    csv_path = tmp_path / "ann.csv"
    _write_csv(csv_path, [_base_row("s1", escalation_label="1")])
    out_path = tmp_path / "imported.jsonl"
    log_path = tmp_path / "no_stdout.log"
    cmd = [
        sys.executable, "-u", "scripts/import_annotations.py",
        "--input", str(csv_path),
        "--output", str(out_path),
    ]
    rc, _ = _run_subprocess_with_log(
        cmd, cwd=ROOT, timeout=60, log_path=log_path,
    )
    assert rc == 0
    recs = _load_jsonl(out_path)
    assert len(recs) == 1
    assert recs[0]["escalation_label"] == 1
