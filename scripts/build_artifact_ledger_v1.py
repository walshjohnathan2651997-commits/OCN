#!/usr/bin/env python
"""build_artifact_ledger_v1.py — Build V3.17 artifact ledger.

Reads ``artifacts_manifest_v3_17.yaml``, scans each artifact for
sensitive columns, and generates:

  - ``reports/artifact_ledger_v3_17.csv``  — one row per artifact
  - ``reports/artifact_ledger_v3_17.md``   — grouped summary
  - ``reports/release_safety_manifest_v3_17.json`` — release gate

Hard boundaries:
  - Read-only scan; does not modify any artifact.
  - Does not re-run heavy experiments.
  - Does not access private PDFs or raw claim/evidence text.
  - Sensitive-column detection is header-only (does not read row data).

Usage:
  python scripts/build_artifact_ledger_v1.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore

REPO_ROOT = Path(__file__).resolve().parent.parent
MANIFEST_PATH = REPO_ROOT / "artifacts_manifest_v3_17.yaml"
OUTPUT_CSV = REPO_ROOT / "reports" / "artifact_ledger_v3_17.csv"
OUTPUT_MD = REPO_ROOT / "reports" / "artifact_ledger_v3_17.md"
OUTPUT_JSON = REPO_ROOT / "reports" / "release_safety_manifest_v3_17.json"

# Sensitive text columns — checked against CSV headers.
SENSITIVE_TEXT_COLUMNS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "body_text", "pdf_text",
    "generation_notes", "title", "url",
]

# Label columns — indicate the artifact contains silver/gold labels.
LABEL_COLUMNS = [
    "true_label", "candidate_label_guess", "final_label",
    "gold_label", "human_audited", "silver_label_source",
]

# Oracle columns — indicate the artifact contains oracle evaluation.
ORACLE_COLUMNS = [
    "oracle_hit", "oracle_match", "oracle_recall",
    "oracle_evidence", "oracle_hash",
]

# Hash-only column patterns — indicate hash-only (safe) identifiers.
HASH_COLUMN_PATTERNS = [
    re.compile(r".*_sha256$", re.IGNORECASE),
    re.compile(r".*_hash$", re.IGNORECASE),
    re.compile(r".*_hash_\d+$", re.IGNORECASE),
]


@dataclass
class ArtifactRecord:
    artifact_id: str
    path: str
    artifact_type: str
    public_safe: bool
    private_sensitive: bool
    generated_by_script: str
    input_artifacts: str
    run_mode: str
    contains_raw_text: bool
    contains_hash_only: bool
    contains_labels: bool
    contains_oracle_eval: bool
    safe_to_release: bool
    notes: str
    exists: bool
    detected_sensitive_columns: str
    detected_label_columns: str
    detected_oracle_columns: str


def load_manifest() -> dict:
    """Load the YAML manifest."""
    if not MANIFEST_PATH.exists():
        print(f"[artifact_ledger] ERROR: manifest not found: {MANIFEST_PATH}")
        sys.exit(1)
    if yaml is None:
        print("[artifact_ledger] ERROR: PyYAML not installed. pip install pyyaml")
        sys.exit(1)
    with open(MANIFEST_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def read_csv_header(path: Path) -> Optional[List[str]]:
    """Read the header row of a CSV file. Returns None if the file
    cannot be read as CSV."""
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            header = next(reader, None)
            return header
    except Exception:
        return None


def read_json_keys(path: Path) -> Optional[List[str]]:
    """Read the top-level keys of a JSON file. Returns None if the
    file cannot be read as JSON."""
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, dict):
            return list(data.keys())
        return None
    except Exception:
        return None


def check_md_for_raw_text(path: Path) -> bool:
    """Check if a markdown file appears to contain raw claim/evidence
    text. Looks for long quoted strings or evidence-like patterns."""
    try:
        text = path.read_text(encoding="utf-8")
    except Exception:
        return False
    # Check for common raw-text indicators:
    # - Lines with > 200 chars of non-markdown text (likely raw evidence)
    # - Repeated claim/evidence field references with values
    for line in text.split("\n"):
        stripped = line.strip()
        if len(stripped) > 300 and not stripped.startswith("|"):
            # Long line that's not a table row — might be raw text
            if not stripped.startswith("#") and not stripped.startswith("-"):
                return True
    return False


def scan_artifact(artifact_def: dict) -> ArtifactRecord:
    """Scan a single artifact and return its record."""
    path_str = artifact_def["path"]
    path = REPO_ROOT / path_str
    exists = path.exists()

    # Start with manifest-declared fields
    public_safe = artifact_def.get("public_safe", False)
    private_sensitive = artifact_def.get("private_sensitive", False)

    contains_raw_text = False
    contains_hash_only = False
    contains_labels = False
    contains_oracle_eval = False

    detected_sensitive: List[str] = []
    detected_labels: List[str] = []
    detected_oracle: List[str] = []

    if exists and path.is_file():
        suffix = path.suffix.lower()

        if suffix == ".csv":
            header = read_csv_header(path)
            if header:
                header_lower = [h.strip().lower() for h in header]
                # Check for sensitive text columns
                for col in SENSITIVE_TEXT_COLUMNS:
                    if col in header_lower:
                        detected_sensitive.append(col)
                        contains_raw_text = True
                # Check for label columns
                for col in LABEL_COLUMNS:
                    if col in header_lower:
                        detected_labels.append(col)
                        contains_labels = True
                # Check for oracle columns
                for col in ORACLE_COLUMNS:
                    if col in header_lower:
                        detected_oracle.append(col)
                        contains_oracle_eval = True
                # Check for hash-only columns
                has_hash = any(
                    any(p.match(h) for p in HASH_COLUMN_PATTERNS)
                    for h in header_lower
                )
                if has_hash and not contains_raw_text:
                    contains_hash_only = True

        elif suffix == ".json":
            keys = read_json_keys(path)
            if keys:
                keys_lower = [k.strip().lower() for k in keys]
                # Check for sensitive keys in JSON
                for col in SENSITIVE_TEXT_COLUMNS:
                    if col in keys_lower:
                        detected_sensitive.append(col)
                        contains_raw_text = True
                for col in LABEL_COLUMNS:
                    if col in keys_lower:
                        detected_labels.append(col)
                        contains_labels = True
                for col in ORACLE_COLUMNS:
                    if col in keys_lower:
                        detected_oracle.append(col)
                        contains_oracle_eval = True

        elif suffix in (".md", ".markdown"):
            if check_md_for_raw_text(path):
                contains_raw_text = True

    # Determine safe_to_release:
    # - Must be public_safe=true (declared)
    # - Must NOT contain raw text (detected)
    # - Must NOT be private_sensitive
    # - Must exist (or be a blocked artifact with status-only output)
    safe_to_release = (
        public_safe
        and not private_sensitive
        and not contains_raw_text
        and exists
    )

    return ArtifactRecord(
        artifact_id=artifact_def["artifact_id"],
        path=path_str,
        artifact_type=artifact_def.get("artifact_type", "unknown"),
        public_safe=public_safe,
        private_sensitive=private_sensitive,
        generated_by_script=artifact_def.get("generated_by_script", ""),
        input_artifacts=artifact_def.get("input_artifacts", ""),
        run_mode=artifact_def.get("run_mode", "unknown"),
        contains_raw_text=contains_raw_text,
        contains_hash_only=contains_hash_only,
        contains_labels=contains_labels,
        contains_oracle_eval=contains_oracle_eval,
        safe_to_release=safe_to_release,
        notes=artifact_def.get("notes", ""),
        exists=exists,
        detected_sensitive_columns=", ".join(detected_sensitive),
        detected_label_columns=", ".join(detected_labels),
        detected_oracle_columns=", ".join(detected_oracle),
    )


def build_ledger(manifest: dict) -> List[ArtifactRecord]:
    """Build the full artifact ledger from the manifest."""
    records: List[ArtifactRecord] = []
    for group in manifest.get("artifact_groups", []):
        for artifact_def in group.get("artifacts", []):
            record = scan_artifact(artifact_def)
            records.append(record)
    return records


def write_csv(records: List[ArtifactRecord], path: Path) -> None:
    """Write the ledger as CSV."""
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = [
        "artifact_id", "path", "artifact_type", "public_safe",
        "private_sensitive", "generated_by_script", "input_artifacts",
        "run_mode", "contains_raw_text", "contains_hash_only",
        "contains_labels", "contains_oracle_eval", "safe_to_release",
        "exists", "detected_sensitive_columns", "detected_label_columns",
        "detected_oracle_columns", "notes",
    ]
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in records:
            row = asdict(r)
            # Convert booleans to lowercase strings for CSV readability
            for key in fieldnames:
                if isinstance(row[key], bool):
                    row[key] = str(row[key]).lower()
            writer.writerow(row)
    print(f"[artifact_ledger] wrote {path} ({len(records)} artifacts)")


def write_md(records: List[ArtifactRecord], path: Path) -> None:
    """Write the ledger as a grouped markdown report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    lines.append("# Artifact Ledger — V3.17 Confidential Lightweight")
    lines.append("")
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("> Read-only scan. No artifacts were modified.")
    lines.append("")

    # Summary counts
    total = len(records)
    n_exists = sum(1 for r in records if r.exists)
    n_safe = sum(1 for r in records if r.safe_to_release)
    n_private = sum(1 for r in records if r.private_sensitive)
    n_raw_text = sum(1 for r in records if r.contains_raw_text)
    n_blocked = sum(1 for r in records if r.run_mode == "blocked")

    lines.append("## Summary")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|---|---|")
    lines.append(f"| Total artifacts | {total} |")
    lines.append(f"| Exists on disk | {n_exists} |")
    lines.append(f"| Safe to release | {n_safe} |")
    lines.append(f"| Private/sensitive | {n_private} |")
    lines.append(f"| Contains raw text | {n_raw_text} |")
    lines.append(f"| Blocked run mode | {n_blocked} |")
    lines.append("")

    # Release safety gate
    lines.append("## Release Safety Gate")
    lines.append("")
    unsafe_public = [
        r for r in records
        if r.public_safe and r.contains_raw_text
    ]
    private_in_release = [
        r for r in records
        if r.private_sensitive and r.safe_to_release
    ]
    if unsafe_public:
        lines.append(f"**FAIL**: {len(unsafe_public)} artifact(s) declared public_safe "
                     f"but contain raw text:")
        for r in unsafe_public:
            lines.append(f"- `{r.artifact_id}` ({r.path}): "
                         f"{r.detected_sensitive_columns}")
        lines.append("")
    else:
        lines.append("**PASS**: No public_safe artifact contains raw text.")
        lines.append("")

    if private_in_release:
        lines.append(f"**FAIL**: {len(private_in_release)} private artifact(s) "
                     f"marked safe_to_release:")
        for r in private_in_release:
            lines.append(f"- `{r.artifact_id}` ({r.path})")
        lines.append("")
    else:
        lines.append("**PASS**: No private_sensitive artifact is marked safe_to_release.")
        lines.append("")

    overall = "PASS" if not unsafe_public and not private_in_release else "FAIL"
    lines.append(f"**Overall: {overall}**")
    lines.append("")
    lines.append("---")
    lines.append("")

    # Full ledger table
    lines.append("## Full Artifact Ledger")
    lines.append("")
    lines.append("| ID | Path | Type | Run Mode | Raw Text | Labels | Oracle | Safe to Release | Notes |")
    lines.append("|---|---|---|---|---|---|---|---|---|")
    for r in records:
        exists_str = "" if r.exists else " **[MISSING]**"
        raw_str = "yes" if r.contains_raw_text else "no"
        label_str = "yes" if r.contains_labels else "no"
        oracle_str = "yes" if r.contains_oracle_eval else "no"
        safe_str = "yes" if r.safe_to_release else "no"
        notes_short = r.notes[:60] + "..." if len(r.notes) > 60 else r.notes
        lines.append(
            f"| {r.artifact_id} | `{r.path}`{exists_str} | {r.artifact_type} | "
            f"{r.run_mode} | {raw_str} | {label_str} | {oracle_str} | "
            f"{safe_str} | {notes_short} |"
        )
    lines.append("")

    # Sensitive column detection details
    lines.append("## Sensitive Column Detection Details")
    lines.append("")
    flagged = [r for r in records if r.detected_sensitive_columns or r.detected_label_columns or r.detected_oracle_columns]
    if flagged:
        lines.append("| ID | Sensitive Columns | Label Columns | Oracle Columns |")
        lines.append("|---|---|---|---|")
        for r in flagged:
            lines.append(
                f"| {r.artifact_id} | {r.detected_sensitive_columns or '—'} | "
                f"{r.detected_label_columns or '—'} | "
                f"{r.detected_oracle_columns or '—'} |"
            )
    else:
        lines.append("No artifacts with detected sensitive/label/oracle columns.")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[artifact_ledger] wrote {path}")


def write_release_safety_json(
    records: List[ArtifactRecord],
    manifest: dict,
    path: Path,
) -> None:
    """Write the release safety manifest as JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)

    safe_to_release = [
        {"artifact_id": r.artifact_id, "path": r.path, "type": r.artifact_type}
        for r in records if r.safe_to_release
    ]
    private_sensitive = [
        {"artifact_id": r.artifact_id, "path": r.path, "type": r.artifact_type}
        for r in records if r.private_sensitive
    ]
    contains_raw_text = [
        {"artifact_id": r.artifact_id, "path": r.path,
         "detected_columns": r.detected_sensitive_columns}
        for r in records if r.contains_raw_text
    ]
    blocked = [
        {"artifact_id": r.artifact_id, "path": r.path}
        for r in records if r.run_mode == "blocked"
    ]
    missing = [
        {"artifact_id": r.artifact_id, "path": r.path}
        for r in records if not r.exists
    ]

    # Safety gate checks
    unsafe_public = [
        r.artifact_id for r in records
        if r.public_safe and r.contains_raw_text
    ]
    private_in_release = [
        r.artifact_id for r in records
        if r.private_sensitive and r.safe_to_release
    ]

    gate_pass = len(unsafe_public) == 0 and len(private_in_release) == 0

    output = {
        "manifest_version": manifest.get("manifest_version", "1.0"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mainline": manifest.get("mainline", "V3.17 Confidential Lightweight"),
        "summary": {
            "total_artifacts": len(records),
            "exists_on_disk": sum(1 for r in records if r.exists),
            "safe_to_release_count": len(safe_to_release),
            "private_sensitive_count": len(private_sensitive),
            "contains_raw_text_count": len(contains_raw_text),
            "blocked_count": len(blocked),
            "missing_count": len(missing),
        },
        "release_safety_gate": {
            "status": "PASS" if gate_pass else "FAIL",
            "unsafe_public_artifacts": unsafe_public,
            "private_in_release": private_in_release,
        },
        "safe_to_release": safe_to_release,
        "private_sensitive": private_sensitive,
        "contains_raw_text": contains_raw_text,
        "blocked_artifacts": blocked,
        "missing_artifacts": missing,
    }

    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[artifact_ledger] wrote {path}")
    print(f"[artifact_ledger] release safety gate: {output['release_safety_gate']['status']}")


def main() -> int:
    manifest = load_manifest()
    records = build_ledger(manifest)
    write_csv(records, OUTPUT_CSV)
    write_md(records, OUTPUT_MD)
    write_release_safety_json(records, manifest, OUTPUT_JSON)

    # Exit code: 0 if gate passes, 1 if fails
    unsafe_public = [
        r for r in records if r.public_safe and r.contains_raw_text
    ]
    private_in_release = [
        r for r in records if r.private_sensitive and r.safe_to_release
    ]
    if unsafe_public or private_in_release:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
