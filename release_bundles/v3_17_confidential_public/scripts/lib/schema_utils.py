"""
Schema utilities for V3.17 confidential lightweight pipeline outputs.

Loads JSON schemas from schemas/ and validates DataFrames (CSV outputs) or
dicts (JSON/JSONL outputs) against them. Writes per-directory validation
reports so a failed validation is visible next to the offending output.

Public API:
    load_schema(schema_name)
    validate_dataframe_columns(df, schema_name, strict=False)
    validate_required_columns(df, required_columns)
    validate_dict_keys(d, schema_name, strict=False)
    write_schema_validation_report(output_dir, reports, script_name=None)

Schema files live in REPO_ROOT/schemas/*.schema.json. Each schema has:
    name, version, description, file_format,
    required_columns, optional_columns,
    forbidden_columns_for_public_release, forbidden_columns_for_scoring,
    hash_columns, text_columns, redaction_required
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCHEMAS_DIR = REPO_ROOT / "schemas"

# Canonical 9 leak-protection fields. Mirrored in configs/*.yaml under
# forbidden_scoring_fields and in tests/test_no_leakage_fields.py.
FORBIDDEN_SCORING_FIELDS: List[str] = [
    "true_label",
    "is_strong_action",
    "oracle_hit",
    "candidate_label_guess",
    "final_label",
    "gold_label",
    "human_audited",
    "evidence_text",
    "evidence_text_sha256",
]

REQUIRED_SCHEMA_KEYS = {
    "name",
    "version",
    "description",
    "required_columns",
    "optional_columns",
    "forbidden_columns_for_public_release",
    "forbidden_columns_for_scoring",
    "hash_columns",
    "text_columns",
    "redaction_required",
}


class SchemaError(Exception):
    """Raised when a schema file is missing, malformed, or fails registry invariants."""


class ValidationError(Exception):
    """Raised when a DataFrame or dict fails schema validation (strict mode)."""


# ---------------- Schema loading ----------------

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load a schema JSON file by name.

    Args:
        schema_name: Schema identifier. Accepts both bare names ("smart_queue_scores")
            and filename forms ("smart_queue_scores.schema.json").

    Returns:
        Parsed schema dict.

    Raises:
        SchemaError: If the schema file does not exist or is missing required keys.
    """
    if not schema_name:
        raise SchemaError("schema_name is required")
    # Normalize: strip .schema.json / .json suffix
    name = schema_name
    if name.endswith(".schema.json"):
        name = name[: -len(".schema.json")]
    elif name.endswith(".json"):
        name = name[: -len(".json")]
    path = SCHEMAS_DIR / f"{name}.schema.json"
    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")
    try:
        with open(path, "r", encoding="utf-8") as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Schema file {path} is not valid JSON: {e}") from e
    # Validate required metadata
    missing = REQUIRED_SCHEMA_KEYS - set(schema.keys())
    if missing:
        raise SchemaError(
            f"Schema {name} is missing required keys: {sorted(missing)}"
        )
    if schema.get("name") != name:
        raise SchemaError(
            f"Schema {name}: 'name' field ('{schema.get('name')}') does not match filename"
        )
    # SmartQueue and any per-candidate scoring schema must enforce the 9
    # forbidden scoring fields.
    if name == "smart_queue_scores":
        forbidden = set(schema.get("forbidden_columns_for_scoring", []))
        missing_forbidden = set(FORBIDDEN_SCORING_FIELDS) - forbidden
        if missing_forbidden:
            raise SchemaError(
                f"Schema {name} forbidden_columns_for_scoring is missing required "
                f"fields: {sorted(missing_forbidden)}"
            )
    return schema


def list_schemas() -> List[str]:
    """Return the list of registered schema names (filename stems)."""
    if not SCHEMAS_DIR.exists():
        return []
    return sorted(
        p.stem[: -len(".schema")]
        for p in SCHEMAS_DIR.glob("*.schema.json")
    )


# ---------------- DataFrame validation ----------------

def validate_required_columns(
    df: pd.DataFrame, required_columns: List[str]
) -> Dict[str, Any]:
    """Check that all required_columns are present in df.columns.

    Returns a report dict with keys: ok (bool), missing (list), present (list).
    Never raises — callers decide what to do with the report.
    """
    cols = set(df.columns.astype(str))
    required = list(required_columns or [])
    missing = [c for c in required if c not in cols]
    return {
        "ok": len(missing) == 0,
        "missing": missing,
        "present": [c for c in required if c in cols],
    }


def validate_dataframe_columns(
    df: pd.DataFrame,
    schema_name: str,
    strict: bool = False,
) -> Dict[str, Any]:
    """Validate a DataFrame against a registered schema.

    Checks performed:
        1. All required_columns are present.
        2. No forbidden_columns_for_scoring are present (the 9 leak fields).
        3. If strict=True, no columns outside required+optional are present.

    Args:
        df: DataFrame to validate.
        schema_name: Schema name (e.g. "smart_queue_scores").
        strict: If True, presence of any column not in required_columns or
            optional_columns raises ValidationError.

    Returns:
        Report dict with keys: schema, ok, required, forbidden_scoring_present,
        unexpected (strict only), n_rows, n_cols.

    Raises:
        SchemaError: If the schema cannot be loaded.
        ValidationError: If strict=True and unexpected columns are present.
    """
    schema = load_schema(schema_name)
    required = schema.get("required_columns", [])
    optional = schema.get("optional_columns", [])
    forbidden_scoring = schema.get("forbidden_columns_for_scoring", [])

    cols = list(df.columns.astype(str))
    cols_set = set(cols)

    required_report = validate_required_columns(df, required)
    forbidden_present = [c for c in forbidden_scoring if c in cols_set]
    allowed = set(required) | set(optional)
    unexpected = [c for c in cols if c not in allowed]

    report: Dict[str, Any] = {
        "schema": schema_name,
        "schema_version": schema.get("version"),
        "ok": required_report["ok"] and len(forbidden_present) == 0,
        "n_rows": int(len(df)),
        "n_cols": int(len(cols)),
        "columns": cols,
        "required_missing": required_report["missing"],
        "forbidden_scoring_present": forbidden_present,
        "unexpected_columns": unexpected if strict else [],
        "strict": bool(strict),
    }

    if strict and unexpected:
        raise ValidationError(
            f"DataFrame has columns not declared in schema '{schema_name}': {unexpected}"
        )
    return report


def validate_dict_keys(
    d: Dict[str, Any],
    schema_name: str,
    strict: bool = False,
) -> Dict[str, Any]:
    """Validate a dict (parsed JSON/JSONL record) against a schema.

    Same semantics as validate_dataframe_columns but for dict keys. Used for
    JSON/JSONL outputs (pdf_sentence_corpus, leakage_audit).
    """
    schema = load_schema(schema_name)
    required = schema.get("required_columns", [])
    optional = schema.get("optional_columns", [])
    forbidden_scoring = schema.get("forbidden_columns_for_scoring", [])

    keys = list(d.keys()) if isinstance(d, dict) else []
    keys_set = set(keys)

    missing = [k for k in required if k not in keys_set]
    forbidden_present = [k for k in forbidden_scoring if k in keys_set]
    allowed = set(required) | set(optional)
    unexpected = [k for k in keys if k not in allowed]

    report: Dict[str, Any] = {
        "schema": schema_name,
        "schema_version": schema.get("version"),
        "ok": len(missing) == 0 and len(forbidden_present) == 0,
        "keys": keys,
        "required_missing": missing,
        "forbidden_scoring_present": forbidden_present,
        "unexpected_keys": unexpected if strict else [],
        "strict": bool(strict),
    }

    if strict and unexpected:
        raise ValidationError(
            f"Dict has keys not declared in schema '{schema_name}': {unexpected}"
        )
    return report


def validate_redacted_file(
    df: pd.DataFrame,
    schema_name: str,
) -> Dict[str, Any]:
    """Check that a redacted/public DataFrame has no text or forbidden columns.

    Verifies:
        1. No column in schema.forbidden_columns_for_public_release is present.
        2. No column in schema.text_columns is present.
        3. No column in schema.forbidden_columns_for_scoring is present.
    """
    schema = load_schema(schema_name)
    forbidden_public = schema.get("forbidden_columns_for_public_release", [])
    text_cols = schema.get("text_columns", [])
    forbidden_scoring = schema.get("forbidden_columns_for_scoring", [])

    cols = list(df.columns.astype(str))
    cols_set = set(cols)

    leaked_public = [c for c in forbidden_public if c in cols_set]
    leaked_text = [c for c in text_cols if c in cols_set]
    leaked_scoring = [c for c in forbidden_scoring if c in cols_set]

    return {
        "schema": schema_name,
        "schema_version": schema.get("version"),
        "ok": len(leaked_public) == 0 and len(leaked_text) == 0 and len(leaked_scoring) == 0,
        "leaked_public_columns": leaked_public,
        "leaked_text_columns": leaked_text,
        "leaked_scoring_columns": leaked_scoring,
        "columns": cols,
    }


# ---------------- Report writing ----------------

def write_schema_validation_report(
    output_dir: Union[str, Path],
    reports: List[Dict[str, Any]],
    script_name: Optional[str] = None,
) -> Path:
    """Write a per-directory schema validation report.

    Writes schema_validation_report.json with: script_name, timestamp,
    n_reports, n_ok, n_fail, reports[].

    Args:
        output_dir: Directory to write the report into. Created if missing.
        reports: List of report dicts from validate_dataframe_columns /
            validate_dict_keys / validate_redacted_file.
        script_name: Optional name of the producing script.

    Returns:
        Path to the written report file.
    """
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    n_ok = sum(1 for r in reports if r.get("ok"))
    n_fail = len(reports) - n_ok
    payload = {
        "script_name": script_name,
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "n_reports": len(reports),
        "n_ok": n_ok,
        "n_fail": n_fail,
        "all_ok": n_fail == 0,
        "reports": reports,
    }
    report_path = out / "schema_validation_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False, default=str)
    return report_path


def validate_csv_file(
    csv_path: Union[str, Path],
    schema_name: str,
    strict: bool = False,
) -> Dict[str, Any]:
    """Convenience: load a CSV and validate against a schema.

    Returns a report dict enriched with file_path and file_exists fields.
    If the file does not exist, returns ok=False with file_exists=False.
    """
    p = Path(csv_path)
    if not p.exists():
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": False,
            "ok": False,
            "error": "file not found",
        }
    try:
        df = pd.read_csv(p, keep_default_na=False)
    except Exception as e:
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "error": f"failed to read CSV: {e}",
        }
    report = validate_dataframe_columns(df, schema_name, strict=strict)
    report["file_path"] = str(p)
    report["file_exists"] = True
    return report


def validate_redacted_csv_file(
    csv_path: Union[str, Path],
    schema_name: str,
) -> Dict[str, Any]:
    """Convenience: load a redacted CSV and validate that no text/forbidden
    columns are present.

    Returns a report dict enriched with file_path and file_exists fields.
    If the file does not exist, returns ok=False with file_exists=False.
    """
    p = Path(csv_path)
    if not p.exists():
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": False,
            "ok": False,
            "is_redacted": True,
            "error": "file not found",
        }
    try:
        df = pd.read_csv(p, keep_default_na=False)
    except Exception as e:
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "is_redacted": True,
            "error": f"failed to read CSV: {e}",
        }
    report = validate_redacted_file(df, schema_name)
    report["file_path"] = str(p)
    report["file_exists"] = True
    report["is_redacted"] = True
    return report


def validate_jsonl_file(
    jsonl_path: Union[str, Path],
    schema_name: str,
    strict: bool = False,
    max_records: Optional[int] = None,
) -> Dict[str, Any]:
    """Convenience: load a JSONL file and validate first record against schema.

    Returns a report dict enriched with file_path, file_exists, n_records.
    """
    p = Path(jsonl_path)
    if not p.exists():
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": False,
            "ok": False,
            "error": "file not found",
        }
    records: List[Dict[str, Any]] = []
    try:
        with open(p, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                records.append(json.loads(line))
                if max_records is not None and len(records) >= max_records:
                    break
    except Exception as e:
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "error": f"failed to read JSONL: {e}",
        }
    if not records:
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "error": "empty JSONL file",
            "n_records": 0,
        }
    report = validate_dict_keys(records[0], schema_name, strict=strict)
    report["file_path"] = str(p)
    report["file_exists"] = True
    report["n_records"] = len(records)
    return report


def validate_json_file(
    json_path: Union[str, Path],
    schema_name: str,
    strict: bool = False,
) -> Dict[str, Any]:
    """Convenience: load a JSON file and validate top-level keys against schema."""
    p = Path(json_path)
    if not p.exists():
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": False,
            "ok": False,
            "error": "file not found",
        }
    try:
        with open(p, "r", encoding="utf-8") as f:
            obj = json.load(f)
    except Exception as e:
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "error": f"failed to read JSON: {e}",
        }
    if not isinstance(obj, dict):
        return {
            "schema": schema_name,
            "file_path": str(p),
            "file_exists": True,
            "ok": False,
            "error": f"top-level JSON is {type(obj).__name__}, expected object",
        }
    report = validate_dict_keys(obj, schema_name, strict=strict)
    report["file_path"] = str(p)
    report["file_exists"] = True
    return report
