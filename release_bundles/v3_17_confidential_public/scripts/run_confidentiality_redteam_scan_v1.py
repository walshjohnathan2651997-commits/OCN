"""
Confidentiality Red-Team Scanner v1
===================================
Aggressive leakage scanner for V3.17 release artifacts. Scans the repository
and experiment output directories for confidential PDF content, real
evidence/claim text, oracle/gold fields, and other release-gate violations.

Six scan rules:
  1. Filename risk — sensitive filenames in public dirs
  2. Field risk — text columns (claim_text, evidence_text, etc.) in public/redacted files
  3. Forbidden sorting fields — true_label/oracle_hit/etc. in smart_queue/risk_ranking outputs
  4. Long text risk — cells > 300 chars in redacted/docs files (potential source excerpt leak)
  5. URL/arxiv/source risk — real identifiers in public redacted artifacts
  6. Toy data validation — toy files must use toy_ prefix or synthetic=true

Outputs (to --output_dir, default experiments/confidentiality_redteam_scan_v1):
  redteam_findings.csv     — one row per finding
  redteam_summary.json     — counts + pass_public_release_gate
  redteam_summary.md       — human-readable grouped by risk level
  .gitignore_check.json    — missing .gitignore entries (report only, never auto-delete)

Prohibitions: no training, no API, no network, no original-data modification,
no file deletion. The scanner is strictly read-only.

Usage:
  python scripts/run_confidentiality_redteam_scan_v1.py
  python scripts/run_confidentiality_redteam_scan_v1.py --config configs/v3_17_confidential_default.yaml
  python scripts/run_confidentiality_redteam_scan_v1.py --private_hash_manifest path/to/hashes.txt
  python scripts/run_confidentiality_redteam_scan_v1.py --strict
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, print_guards  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

# ---------------- Risk levels ----------------
RISK_HIGH = "high"
RISK_MEDIUM = "medium"
RISK_LOW = "low"

# ---------------- Rule 1: Filename risk ----------------
SENSITIVE_FILENAME_KEYWORDS = [
    "real_review_queue",
    "top100",
    "evidence_text",
    "gold",
    "human_audited",
    "source_excerpt",
    "raw_pdf_text",
    "selected_evidence",
]

# ---------------- Rule 2: Field risk (text columns in public/redacted files) ----------------
SENSITIVE_TEXT_FIELDS = [
    "claim_text",
    "evidence_text",
    "selected_evidence",
    "raw_text",
    "clean_text",
    "source_excerpt",
    "full_text",
    "raw_page_text",
    "clean_page_text",
    "raw_block_text",
    "clean_block_text",
    "page_text",
    "block_text",
]

# ---------------- Rule 3: Forbidden sorting fields ----------------
FORBIDDEN_SORTING_FIELDS = [
    "true_label",
    "is_strong_action",
    "oracle_hit",
    "candidate_label_guess",
    "final_label",
    "gold_label",
    "human_audited",
]

# ---------------- Rule 5: URL/arxiv/source identifiers ----------------
URL_PATTERN = re.compile(r"https?://\S+", re.IGNORECASE)
ARXIV_ID_PATTERN = re.compile(r"\b\d{4}\.\d{4,5}\b")
SOURCE_ID_FIELDS = ["url", "source_url", "arxiv_id", "pdf_filename", "pdf_path", "source_pdf"]

# ---------------- Rule 6: Toy data validation ----------------
TOY_MARKERS = ["toy_", "synthetic", "mock", "fake", "dummy"]
TOY_REQUIRED_PREFIX = "toy_"

# ---------------- Private ignored dirs ----------------
PRIVATE_DIR_PATTERNS = [
    "private",
    ".git",
    "__pycache__",
    "node_modules",
    ".venv",
    "venv",
    "env",
]

# ---------------- .gitignore required entries ----------------
REQUIRED_GITIGNORE_ENTRIES = [
    "pdfs/",
    "private_pdfs/",
    "data/private/",
    "experiments/private/",
    "*.pdf",
    "*.docx",
    "*.xlsx",
    "*.npz",
    "*.pkl",
    "*.joblib",
]

# ---------------- Default scan dirs ----------------
DEFAULT_SCAN_DIRS = [
    "README.md",
    "CURRENT_MAINLINE.md",
    "docs/",
    "scripts/",
    "schemas/",
    "experiments/",
    "data/toy_synthetic/",
]

LONG_TEXT_THRESHOLD = 300


# ---------------- Finding dataclass ----------------

class Finding:
    __slots__ = ("path", "risk_level", "risk_type", "matched_field", "line_or_row", "message", "recommendation")

    def __init__(self, path: str, risk_level: str, risk_type: str,
                 matched_field: str, line_or_row: str, message: str, recommendation: str):
        self.path = path
        self.risk_level = risk_level
        self.risk_type = risk_type
        self.matched_field = matched_field
        self.line_or_row = line_or_row
        self.message = message
        self.recommendation = recommendation

    def to_dict(self) -> Dict[str, str]:
        return {
            "path": self.path,
            "risk_level": self.risk_level,
            "risk_type": self.risk_type,
            "matched_field": self.matched_field,
            "line_or_row": self.line_or_row,
            "message": self.message,
            "recommendation": self.recommendation,
        }


# ---------------- Path classification ----------------

def is_private_dir(path: Path) -> bool:
    """Check if path is under a private/ignored directory."""
    parts = path.parts
    for part in parts:
        part_lower = part.lower()
        for pattern in PRIVATE_DIR_PATTERNS:
            if pattern in part_lower:
                return True
    return False


def safe_rel_str(path: Path, repo_root: Path) -> str:
    """Return a relative-to-repo string if possible, else the absolute path.

    Handles scan_dirs that live outside the repo (e.g. tmp_path in tests)
    without raising ValueError.
    """
    try:
        return str(path.relative_to(repo_root))
    except ValueError:
        return str(path)


def load_private_allowlist(manifest_path: Path) -> Dict[str, str]:
    """Load a JSON manifest mapping relative paths to justification strings.

    Format: {"relative/path.csv": "justification for private intermediate use"}
    Paths in this manifest are exempt from rule3 (forbidden_sorting_field)
    HIGH-risk escalation; findings are downgraded to LOW with the justification
    attached. The files must still be excluded from public release bundles.
    """
    if not manifest_path or not manifest_path.exists():
        return {}
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            return {}
        return {str(k).replace("\\", "/"): str(v) for k, v in data.items()}
    except Exception:
        return {}


def is_toy_path(path: Path) -> bool:
    """Check if path is toy/synthetic data.

    Matches path *components* (not substrings) to avoid false positives on
    paths like 'test_real_text_without_toy_pre0/' which happen to contain
    'toy_' as a substring.
    """
    for part in path.parts:
        part_lower = part.lower()
        if part_lower == "toy_synthetic":
            return True
        if part_lower.startswith("toy_"):
            return True
        if part_lower.endswith("_toy"):
            return True
    return False


def is_redacted_filename(path: Path) -> bool:
    """Check if filename indicates a redacted/public release file."""
    return "redacted" in path.name.lower()


def is_markdown_file(path: Path) -> bool:
    return path.suffix.lower() in (".md", ".markdown")


def is_code_file(path: Path) -> bool:
    return path.suffix.lower() in (".py", ".js", ".ts", ".sh", ".yml", ".yaml")


def is_data_file(path: Path) -> bool:
    return path.suffix.lower() in (".csv", ".json", ".jsonl", ".tsv")


def is_scoring_output(path: Path) -> bool:
    """Check if file is a smart_queue or risk_ranking scoring output."""
    name = path.name.lower()
    return (
        "smart_queue_scores" in name
        or "risk_ranking_features" in name
        or "canonicalized_r4_review_scores" in name
    )


def is_public_artifact(path: Path, repo_root: Path) -> bool:
    """Determine if a file is a 'public artifact' (subject to aggressive checking).

    Public artifacts:
    - Files with 'redacted' in the name
    - Files under docs/
    - Markdown files (.md) at repo root or under docs/
    - Files under data/toy_synthetic/ (toy data, special rules)
    - Schema files (.schema.json)
    - Code files (.py, .yml) — checked for hardcoded values but not data fields

    Private (skipped):
    - Files under private/ dirs
    - Files under .git/, __pycache__/
    - Non-redacted experiment outputs (internal, not for public release)
    """
    if is_private_dir(path):
        return False

    rel_str = safe_rel_str(path, repo_root).lower().replace("\\", "/")

    # Toy data is public but has special rules
    if is_toy_path(path):
        return True

    # Redacted files are always public
    if is_redacted_filename(path):
        return True

    # Docs and markdown are public
    if rel_str.startswith("docs/") or is_markdown_file(path):
        return True

    # Schema files are public
    if path.name.endswith(".schema.json"):
        return True

    # Code files are public (checked for hardcoded secrets)
    if is_code_file(path):
        return True

    # Config files are public
    if rel_str.startswith("configs/"):
        return True

    # README and CURRENT_MAINLINE are public
    if path.name in ("README.md", "CURRENT_MAINLINE.md"):
        return True

    # Non-redacted experiment outputs are internal (not public release)
    if rel_str.startswith("experiments/"):
        return False

    return False


# ---------------- File walkers ----------------

def walk_scan_dirs(scan_dirs: List[str], repo_root: Path) -> List[Path]:
    """Walk the scan_dirs and return a list of files to check."""
    files: List[Path] = []
    for rel_dir in scan_dirs:
        target = repo_root / rel_dir
        if not target.exists():
            continue
        if target.is_file():
            if not is_private_dir(target):
                files.append(target)
        elif target.is_dir():
            for p in target.rglob("*"):
                if p.is_file() and not is_private_dir(p):
                    files.append(p)
    return sorted(set(files))


# ---------------- Rule implementations ----------------

def rule1_filename_risk(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Flag files with sensitive keywords in the filename."""
    name_lower = path.name.lower()
    for keyword in SENSITIVE_FILENAME_KEYWORDS:
        if keyword in name_lower:
            # Determine if this is a toy file (less risky)
            is_toy = is_toy_path(path)
            risk = RISK_LOW if is_toy else RISK_MEDIUM
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=risk,
                risk_type="filename_risk",
                matched_field=keyword,
                line_or_row="",
                message=f"Filename contains sensitive keyword '{keyword}'",
                recommendation=(
                    "Verify this file is NOT included in public release. "
                    "If toy/synthetic, prefix with 'toy_' to clarify."
                    if is_toy else
                    "Ensure this file is excluded from public release artifacts."
                ),
            ))


def rule2_field_risk(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Check CSV/JSON/JSONL public/redacted files for sensitive text fields."""
    if not is_data_file(path):
        return
    if not is_public_artifact(path, repo_root):
        return

    # Toy data has special handling (rule 6)
    if is_toy_path(path):
        return

    suffix = path.suffix.lower()
    if suffix == ".csv":
        _rule2_csv(path, repo_root, findings)
    elif suffix == ".json":
        _rule2_json(path, repo_root, findings)
    elif suffix == ".jsonl":
        _rule2_jsonl(path, repo_root, findings)


def _rule2_csv(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        df = pd.read_csv(path, keep_default_na=False, nrows=1)
    except Exception:
        return
    cols = set(df.columns.astype(str))
    for field in SENSITIVE_TEXT_FIELDS:
        if field in cols:
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_HIGH,
                risk_type="field_risk",
                matched_field=field,
                line_or_row="header",
                message=f"Public/redacted CSV contains text column '{field}'",
                recommendation=f"Remove column '{field}' from public release; replace with SHA-256 hash if traceability needed.",
            ))


def _rule2_json(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return
    if not isinstance(obj, dict):
        return
    for field in SENSITIVE_TEXT_FIELDS:
        if field in obj:
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_HIGH,
                risk_type="field_risk",
                matched_field=field,
                line_or_row="",
                message=f"Public/redacted JSON contains text field '{field}'",
                recommendation=f"Remove field '{field}' from public release.",
            ))


def _rule2_jsonl(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline()
        if not first_line.strip():
            return
        obj = json.loads(first_line)
    except Exception:
        return
    if not isinstance(obj, dict):
        return
    for field in SENSITIVE_TEXT_FIELDS:
        if field in obj:
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_HIGH,
                risk_type="field_risk",
                matched_field=field,
                line_or_row="line 1",
                message=f"Public/redacted JSONL contains text field '{field}'",
                recommendation=f"Remove field '{field}' from public release; use hash column instead.",
            ))


def rule3_forbidden_sorting_fields(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Check smart_queue/risk_ranking outputs for forbidden sorting fields."""
    if not is_scoring_output(path):
        return
    if path.suffix.lower() != ".csv":
        return

    try:
        df = pd.read_csv(path, keep_default_na=False, nrows=1)
    except Exception:
        return

    cols = set(df.columns.astype(str))
    for field in FORBIDDEN_SORTING_FIELDS:
        if field in cols:
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_HIGH,
                risk_type="forbidden_sorting_field",
                matched_field=field,
                line_or_row="header",
                message=f"Scoring output contains forbidden sorting field '{field}'",
                recommendation=f"Remove '{field}' from scoring output. This field must not appear in any sorting/scoring CSV.",
            ))


def rule4_long_text_risk(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Flag cells > 300 chars in redacted/docs files (potential source excerpt leak)."""
    if not is_data_file(path):
        return
    # Only check redacted files or files under docs/
    rel_str = safe_rel_str(path, repo_root).lower().replace("\\", "/")
    if not (is_redacted_filename(path) or rel_str.startswith("docs/")):
        return
    # Skip toy data
    if is_toy_path(path):
        return

    suffix = path.suffix.lower()
    if suffix == ".csv":
        _rule4_csv(path, repo_root, findings)
    elif suffix == ".jsonl":
        _rule4_jsonl(path, repo_root, findings)


def _rule4_csv(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        df = pd.read_csv(path, keep_default_na=False)
    except Exception:
        return
    for col_idx, col in enumerate(df.columns):
        for row_idx, val in enumerate(df[col]):
            val_str = str(val)
            if len(val_str) > LONG_TEXT_THRESHOLD:
                findings.append(Finding(
                    path=safe_rel_str(path, repo_root),
                    risk_level=RISK_MEDIUM,
                    risk_type="long_text_risk",
                    matched_field=str(col),
                    line_or_row=f"row {row_idx}",
                    message=f"Cell in column '{col}' has {len(val_str)} chars (threshold={LONG_TEXT_THRESHOLD}) — potential source excerpt leak",
                    recommendation="Truncate or hash the cell value. Redacted files should not contain long text excerpts.",
                ))
                break  # one finding per column is enough


def _rule4_jsonl(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                obj = json.loads(line)
                if not isinstance(obj, dict):
                    continue
                for key, val in obj.items():
                    if isinstance(val, str) and len(val) > LONG_TEXT_THRESHOLD:
                        findings.append(Finding(
                            path=safe_rel_str(path, repo_root),
                            risk_level=RISK_MEDIUM,
                            risk_type="long_text_risk",
                            matched_field=key,
                            line_or_row=f"line {line_num}",
                            message=f"JSONL field '{key}' has {len(val)} chars (threshold={LONG_TEXT_THRESHOLD}) — potential source excerpt leak",
                            recommendation="Truncate or hash the field value.",
                        ))
                        break  # one finding per line
                if line_num >= 100:  # limit scan
                    break
    except Exception:
        return


def rule5_url_arxiv_risk(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Flag real URLs, arxiv IDs, and source identifiers in public redacted artifacts."""
    if not is_data_file(path):
        return
    if not is_public_artifact(path, repo_root):
        return
    if is_toy_path(path):
        return
    if not is_redacted_filename(path):
        return  # only check redacted files for URL/arxiv risk

    suffix = path.suffix.lower()
    if suffix != ".csv":
        return

    try:
        df = pd.read_csv(path, keep_default_na=False, nrows=5)
    except Exception:
        return

    cols = set(df.columns.astype(str))
    for field in SOURCE_ID_FIELDS:
        if field in cols:
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_MEDIUM,
                risk_type="url_arxiv_source_risk",
                matched_field=field,
                line_or_row="header",
                message=f"Redacted file contains source identifier column '{field}'",
                recommendation=f"Remove or hash column '{field}' in public release.",
            ))


def rule6_toy_data_validation(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    """Validate that toy data files use toy_ prefix or synthetic=true marker."""
    if not is_data_file(path):
        return
    if not is_toy_path(path):
        return

    suffix = path.suffix.lower()
    if suffix == ".csv":
        _rule6_csv(path, repo_root, findings)
    elif suffix == ".json":
        _rule6_json(path, repo_root, findings)
    elif suffix == ".jsonl":
        _rule6_jsonl(path, repo_root, findings)


def _has_toy_marker(name: str) -> bool:
    name_lower = name.lower()
    return any(marker in name_lower for marker in TOY_MARKERS)


def _rule6_csv(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        df = pd.read_csv(path, keep_default_na=False, nrows=1)
    except Exception:
        return
    cols = set(df.columns.astype(str))
    # Check for text fields without toy_ prefix
    for field in SENSITIVE_TEXT_FIELDS:
        if field in cols:
            # This is a text field without toy_ prefix — flag as low risk
            findings.append(Finding(
                path=safe_rel_str(path, repo_root),
                risk_level=RISK_LOW,
                risk_type="toy_validation",
                matched_field=field,
                line_or_row="header",
                message=f"Toy data file has text column '{field}' without 'toy_' prefix",
                recommendation=f"Rename column to 'toy_{field}' or add 'synthetic=true' marker to the file.",
            ))
    # Check for synthetic=true column
    has_synthetic = any("synthetic" in c.lower() for c in cols)
    has_toy_cols = any(c.lower().startswith("toy_") for c in cols)
    if not has_synthetic and not has_toy_cols and cols:
        # File has no toy markers at all
        findings.append(Finding(
            path=safe_rel_str(path, repo_root),
            risk_level=RISK_LOW,
            risk_type="toy_validation",
            matched_field="",
            line_or_row="",
            message="Toy data file has no 'toy_' prefixed columns or 'synthetic=true' marker",
            recommendation="Add 'toy_' prefix to column names or include a 'synthetic=true' column.",
        ))


def _rule6_json(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception:
        return
    if not isinstance(obj, dict):
        return
    has_synthetic = obj.get("synthetic") is True or obj.get("is_toy") is True
    has_toy_keys = any(k.lower().startswith("toy_") for k in obj.keys())
    if not has_synthetic and not has_toy_keys:
        findings.append(Finding(
            path=safe_rel_str(path, repo_root),
            risk_level=RISK_LOW,
            risk_type="toy_validation",
            matched_field="",
            line_or_row="",
            message="Toy JSON file has no 'toy_' prefixed keys or 'synthetic=true' marker",
            recommendation="Add 'synthetic: true' field or prefix keys with 'toy_'.",
        ))


def _rule6_jsonl(path: Path, repo_root: Path, findings: List[Finding]) -> None:
    try:
        with open(path, "r", encoding="utf-8") as f:
            first_line = f.readline()
        if not first_line.strip():
            return
        obj = json.loads(first_line)
    except Exception:
        return
    if not isinstance(obj, dict):
        return
    has_synthetic = obj.get("synthetic") is True or obj.get("is_toy") is True
    has_toy_keys = any(k.lower().startswith("toy_") for k in obj.keys())
    if not has_synthetic and not has_toy_keys:
        findings.append(Finding(
            path=safe_rel_str(path, repo_root),
            risk_level=RISK_LOW,
            risk_type="toy_validation",
            matched_field="",
            line_or_row="line 1",
            message="Toy JSONL file has no 'toy_' prefixed keys or 'synthetic=true' marker",
            recommendation="Add 'synthetic: true' field or prefix keys with 'toy_'.",
        ))


# ---------------- Private hash manifest check ----------------

def check_private_hash_manifest(
    files: List[Path],
    manifest_path: Path,
    repo_root: Path,
    findings: List[Finding],
) -> None:
    """Check if any scanned file's SHA-256 matches a known-private hash."""
    if not manifest_path or not manifest_path.exists():
        return
    try:
        private_hashes: Set[str] = set()
        with open(manifest_path, "r", encoding="utf-8") as f:
            for line in f:
                h = line.strip().lower()
                if h and len(h) == 64:
                    private_hashes.add(h)
    except Exception:
        return
    if not private_hashes:
        return

    for path in files:
        if not path.is_file():
            continue
        try:
            h = hashlib.sha256()
            with open(path, "rb") as f:
                for chunk in iter(lambda: f.read(8192), b""):
                    h.update(chunk)
            file_hash = h.hexdigest()
            if file_hash in private_hashes:
                findings.append(Finding(
                    path=safe_rel_str(path, repo_root),
                    risk_level=RISK_HIGH,
                    risk_type="private_hash_match",
                    matched_field=file_hash,
                    line_or_row="",
                    message="File SHA-256 matches a known-private content hash",
                    recommendation="Remove this file from public release immediately.",
                ))
        except Exception:
            continue


# ---------------- .gitignore check ----------------

def check_gitignore(repo_root: Path, findings: List[Finding]) -> Dict[str, Any]:
    """Check .gitignore for required entries. Returns a report dict."""
    gitignore_path = repo_root / ".gitignore"
    existing_entries: Set[str] = set()
    if gitignore_path.exists():
        try:
            with open(gitignore_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        existing_entries.add(line)
        except Exception:
            pass

    missing: List[str] = []
    for entry in REQUIRED_GITIGNORE_ENTRIES:
        if entry not in existing_entries:
            missing.append(entry)
            findings.append(Finding(
                path=".gitignore",
                risk_level=RISK_LOW,
                risk_type="gitignore_missing",
                matched_field=entry,
                line_or_row="",
                message=f".gitignore missing required entry '{entry}'",
                recommendation=f"Add '{entry}' to .gitignore to prevent committing sensitive files.",
            ))

    return {
        "existing_count": len(existing_entries),
        "missing": missing,
        "missing_count": len(missing),
    }


# ---------------- Main scan ----------------

def run_scan(
    scan_dirs: List[str],
    repo_root: Path,
    private_hash_manifest: Optional[Path] = None,
    private_allowlist: Optional[Dict[str, str]] = None,
) -> Tuple[List[Finding], Dict[str, Any]]:
    """Run all scan rules. Returns (findings, scan_metadata)."""
    files = walk_scan_dirs(scan_dirs, repo_root)
    findings: List[Finding] = []

    # Rule 1: Filename risk (all files)
    for path in files:
        rule1_filename_risk(path, repo_root, findings)

    # Rule 2: Field risk (public/redacted data files)
    for path in files:
        rule2_field_risk(path, repo_root, findings)

    # Rule 3: Forbidden sorting fields (scoring outputs)
    for path in files:
        rule3_forbidden_sorting_fields(path, repo_root, findings)

    # Downgrade rule3 HIGH findings for allowlisted private intermediate files.
    # These files contain labels for audit/evaluation only; the leakage audit
    # confirms they are not used for sorting. They must still be excluded from
    # public release bundles.
    if private_allowlist:
        for f in findings:
            rel = f.path.replace("\\", "/")
            if rel in private_allowlist and f.risk_level == RISK_HIGH and f.risk_type == "forbidden_sorting_field":
                f.risk_level = RISK_LOW
                f.message = f"[ALLOWLISTED PRIVATE INTERMEDIATE] {f.message}"
                f.recommendation = (
                    f"Private intermediate file exempt from HIGH-risk gate. "
                    f"Justification: {private_allowlist[rel]} "
                    f"Must be excluded from public release bundles."
                )

    # Rule 4: Long text risk (redacted/docs files)
    for path in files:
        rule4_long_text_risk(path, repo_root, findings)

    # Rule 5: URL/arxiv/source risk (redacted files)
    for path in files:
        rule5_url_arxiv_risk(path, repo_root, findings)

    # Rule 6: Toy data validation
    for path in files:
        rule6_toy_data_validation(path, repo_root, findings)

    # Private hash manifest check
    if private_hash_manifest:
        check_private_hash_manifest(files, private_hash_manifest, repo_root, findings)

    # .gitignore check
    gitignore_report = check_gitignore(repo_root, findings)

    metadata = {
        "scanned_files": len(files),
        "scan_dirs": scan_dirs,
        "gitignore_report": gitignore_report,
        "private_allowlist_applied": bool(private_allowlist),
        "private_allowlist_count": len(private_allowlist) if private_allowlist else 0,
    }
    return findings, metadata


# ---------------- Output writers ----------------

def write_findings_csv(findings: List[Finding], output_path: Path) -> None:
    """Write redteam_findings.csv."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "path", "risk_level", "risk_type", "matched_field",
            "line_or_row", "message", "recommendation",
        ])
        writer.writeheader()
        for finding in findings:
            writer.writerow(finding.to_dict())


def write_summary_json(
    findings: List[Finding],
    metadata: Dict[str, Any],
    output_path: Path,
    strict: bool,
) -> Dict[str, Any]:
    """Write redteam_summary.json. Returns the summary payload."""
    high_count = sum(1 for f in findings if f.risk_level == RISK_HIGH)
    medium_count = sum(1 for f in findings if f.risk_level == RISK_MEDIUM)
    low_count = sum(1 for f in findings if f.risk_level == RISK_LOW)

    # Public release gate: pass if no high-risk findings
    # In strict mode, also fail on medium-risk
    if strict:
        pass_gate = high_count == 0 and medium_count == 0
    else:
        pass_gate = high_count == 0

    payload = {
        "scan_timestamp": datetime.now().isoformat(timespec="seconds"),
        "scanned_files": metadata["scanned_files"],
        "scan_dirs": metadata["scan_dirs"],
        "high_risk_count": high_count,
        "medium_risk_count": medium_count,
        "low_risk_count": low_count,
        "total_findings": len(findings),
        "pass_public_release_gate": pass_gate,
        "strict_mode": strict,
        "gitignore_report": metadata.get("gitignore_report", {}),
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)
    return payload


def write_summary_md(findings: List[Finding], summary: Dict[str, Any], output_path: Path) -> None:
    """Write redteam_summary.md grouped by risk level."""
    lines: List[str] = []
    lines.append("# Confidentiality Red-Team Scan Summary")
    lines.append("")
    lines.append(f"Generated: {summary['scan_timestamp']}")
    lines.append(f"Scanned files: {summary['scanned_files']}")
    lines.append("")
    lines.append("## Gate Status")
    lines.append("")
    gate = summary["pass_public_release_gate"]
    gate_str = "PASS" if gate else "FAIL"
    lines.append(f"**Public Release Gate: {gate_str}**")
    lines.append("")
    lines.append(f"- High risk findings: **{summary['high_risk_count']}**")
    lines.append(f"- Medium risk findings: **{summary['medium_risk_count']}**")
    lines.append(f"- Low risk findings: **{summary['low_risk_count']}**")
    lines.append(f"- Total findings: **{summary['total_findings']}**")
    lines.append(f"- Strict mode: {summary['strict_mode']}")
    lines.append("")

    # Group by risk level
    for risk_level, title in [(RISK_HIGH, "High Risk"), (RISK_MEDIUM, "Medium Risk"), (RISK_LOW, "Low Risk")]:
        risk_findings = [f for f in findings if f.risk_level == risk_level]
        if not risk_findings:
            lines.append(f"## {title} (0 findings)")
            lines.append("")
            lines.append("None.")
            lines.append("")
            continue

        lines.append(f"## {title} ({len(risk_findings)} findings)")
        lines.append("")
        # Group by risk_type
        by_type: Dict[str, List[Finding]] = {}
        for f in risk_findings:
            by_type.setdefault(f.risk_type, []).append(f)

        for risk_type, type_findings in sorted(by_type.items()):
            lines.append(f"### {risk_type} ({len(type_findings)})")
            lines.append("")
            for f in type_findings:
                lines.append(f"- **`{f.path}`** — `{f.matched_field}`")
                lines.append(f"  - {f.message}")
                if f.line_or_row:
                    lines.append(f"  - Location: {f.line_or_row}")
                lines.append(f"  - Recommendation: {f.recommendation}")
            lines.append("")

    # .gitignore report
    gi = summary.get("gitignore_report", {})
    if gi:
        lines.append("## .gitignore Check")
        lines.append("")
        lines.append(f"- Existing entries: {gi.get('existing_count', 0)}")
        lines.append(f"- Missing entries: {gi.get('missing_count', 0)}")
        if gi.get("missing"):
            lines.append("")
            lines.append("Missing entries:")
            for entry in gi["missing"]:
                lines.append(f"- `{entry}`")
        lines.append("")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------- Main ----------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Confidentiality red-team scanner for release artifacts"
    )
    parser.add_argument(
        "--config",
        default=None,
        help="Path to YAML config file. Default: configs/v3_17_confidential_default.yaml",
    )
    parser.add_argument(
        "--scan_dirs",
        nargs="+",
        default=DEFAULT_SCAN_DIRS,
        help="Directories/files to scan (default: README.md CURRENT_MAINLINE.md docs/ scripts/ schemas/ experiments/ data/toy_synthetic/)",
    )
    parser.add_argument(
        "--private_hash_manifest",
        default=None,
        help="Optional file of SHA-256 hashes (one per line) of known-private content to detect.",
    )
    parser.add_argument(
        "--private_allowlist",
        default=None,
        help="Optional JSON file mapping relative paths to justifications. Allowlisted "
             "private intermediate files are exempt from rule3 HIGH-risk escalation "
             "(downgraded to LOW). They must still be excluded from public release bundles.",
    )
    parser.add_argument(
        "--output_dir",
        default="experiments/confidentiality_redteam_scan_v1",
        help="Output directory (default: experiments/confidentiality_redteam_scan_v1)",
    )
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Strict mode: medium-risk findings also fail the public release gate.",
    )
    parser.add_argument(
        "--toy_mode",
        action="store_true",
        help="Use toy config (configs/toy_demo.yaml).",
    )
    parser.add_argument(
        "--scan_public_only",
        action="store_true",
        help="Scan only public-safe directories (README, docs, scripts, schemas, "
             "data/toy_synthetic, paper_assets, release_bundles). Excludes the full "
             "experiments/ directory. Use in CI to avoid scanning private intermediates.",
    )
    args = parser.parse_args()

    # If --scan_public_only, restrict scan dirs to public-safe locations
    if args.scan_public_only:
        args.scan_dirs = [
            "README.md", "CURRENT_MAINLINE.md",
            "docs/", "scripts/", "schemas/",
            "data/toy_synthetic/",
            "paper_assets/", "release_bundles/",
        ]

    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / args.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    private_manifest = Path(args.private_hash_manifest) if args.private_hash_manifest else None
    allowlist_path = Path(args.private_allowlist) if args.private_allowlist else None
    private_allowlist = load_private_allowlist(allowlist_path) if allowlist_path else None

    print(f"[redteam_scan] scan_dirs={args.scan_dirs}")
    print(f"[redteam_scan] output_dir={output_dir}")
    print(f"[redteam_scan] strict={args.strict}")
    print(f"[redteam_scan] private_hash_manifest={private_manifest}")
    print(f"[redteam_scan] private_allowlist={allowlist_path} ({len(private_allowlist) if private_allowlist else 0} entries)")

    findings, metadata = run_scan(args.scan_dirs, REPO_ROOT, private_manifest, private_allowlist)

    # Write outputs
    findings_csv = output_dir / "redteam_findings.csv"
    write_findings_csv(findings, findings_csv)
    print(f"[redteam_scan] wrote {findings_csv} ({len(findings)} findings)")

    summary_json = output_dir / "redteam_summary.json"
    summary = write_summary_json(findings, metadata, summary_json, args.strict)
    print(f"[redteam_scan] wrote {summary_json}")

    summary_md = output_dir / "redteam_summary.md"
    write_summary_md(findings, summary, summary_md)
    print(f"[redteam_scan] wrote {summary_md}")

    # Write run_config.json
    from config_utils import write_run_config
    write_run_config(output_dir, config, "run_confidentiality_redteam_scan_v1.py",
                     extra={"strict": args.strict, "scanned_files": metadata["scanned_files"]})

    # Print summary
    print(f"\n[redteam_scan] High: {summary['high_risk_count']}, "
          f"Medium: {summary['medium_risk_count']}, "
          f"Low: {summary['low_risk_count']}")
    print(f"[redteam_scan] Public release gate: {'PASS' if summary['pass_public_release_gate'] else 'FAIL'}")

    # Exit 0 if gate passes, 1 if fails
    return 0 if summary["pass_public_release_gate"] else 1


if __name__ == "__main__":
    sys.exit(main())
