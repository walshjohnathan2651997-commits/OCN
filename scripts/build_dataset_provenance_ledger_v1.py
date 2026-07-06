#!/usr/bin/env python
"""build_dataset_provenance_ledger_v1.py — Dataset provenance ledger.

Reads the locked SimClaim Strict Silver Diagnostic Set v1 CSV and
emits three provenance artifacts:

  - reports/dataset_provenance_ledger_v3_17.json   (machine-readable)
  - reports/dataset_provenance_ledger_v3_17.md     (human-readable)
  - reports/dataset_schema_summary_v3_17.csv       (one-row schema summary)

Hard boundaries:
  - Does NOT modify the source CSV.
  - Does NOT fill final_label / gold_label.
  - Does NOT set human_audited to True.
  - Does NOT output claim_text, evidence_text, or any raw text.
    Only SHA256 hashes and aggregate counts are emitted.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import get_repo_root  # noqa: E402

_REPO_ROOT = get_repo_root()
DEFAULT_CSV = _REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"
DEFAULT_REPORTS_DIR = _REPO_ROOT / "reports"

# Fields that contain raw text — must NEVER be echoed into outputs.
REDACTED_FIELDS = {"evidence_text", "claim_text", "generation_notes", "title", "url"}


def compute_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def value_counts_dict(series: pd.Series) -> dict:
    """Return value counts as a plain dict with str keys."""
    counts = series.value_counts(dropna=False)
    return {str(k): int(v) for k, v in counts.items()}


def nonempty_count(series: pd.Series) -> int:
    """Count nonempty cells (treating empty string and whitespace as empty)."""
    s = series.astype(str).str.strip()
    return int((s != "").sum())


def bool_count(series: pd.Series, expected: bool) -> int:
    """Count cells matching a boolean expected value.

    Handles True/False, 'True'/'False', 'true'/'false', 1/0.
    """
    s = series.astype(str).str.strip().str.lower()
    target = "true" if expected else "false"
    return int((s == target).sum())


def build_ledger(csv_path: Path) -> dict:
    """Build the provenance ledger dictionary from the CSV."""
    if not csv_path.exists():
        raise FileNotFoundError(f"CSV not found: {csv_path}")

    sha256 = compute_sha256(csv_path)
    stat = csv_path.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()

    df = pd.read_csv(csv_path, keep_default_na=False)

    n_rows = len(df)
    n_cols = len(df.columns)
    columns = list(df.columns)

    # Verify no redacted fields leak into output — they exist in CSV but we
    # never copy their values into the ledger.
    leaked = REDACTED_FIELDS.intersection(set(columns))
    # (leaked just means they're present in the CSV; we still never echo them.)

    n_groups = int(df["target_candidate_group_id"].nunique()) if "target_candidate_group_id" in df.columns else 0

    label_counts = value_counts_dict(df["candidate_label_guess"]) if "candidate_label_guess" in df.columns else {}
    domain_counts = value_counts_dict(df["domain"]) if "domain" in df.columns else {}
    human_audited_counts = value_counts_dict(df["human_audited"]) if "human_audited" in df.columns else {}
    annotation_status_counts = value_counts_dict(df["annotation_status"]) if "annotation_status" in df.columns else {}
    dataset_role_counts = value_counts_dict(df["dataset_role"]) if "dataset_role" in df.columns else {}
    silver_label_source_counts = value_counts_dict(df["silver_label_source"]) if "silver_label_source" in df.columns else {}
    claim_generation_policy_counts = value_counts_dict(df["claim_generation_policy"]) if "claim_generation_policy" in df.columns else {}
    group_quality_tier_counts = value_counts_dict(df["group_quality_tier"]) if "group_quality_tier" in df.columns else {}
    leakage_category_counts = value_counts_dict(df["leakage_category"]) if "leakage_category" in df.columns else {}

    final_label_nonempty = nonempty_count(df["final_label"]) if "final_label" in df.columns else 0
    gold_label_nonempty = nonempty_count(df["gold_label"]) if "gold_label" in df.columns else 0
    source_trace_true = bool_count(df["source_trace_complete"], True) if "source_trace_complete" in df.columns else 0
    source_trace_false = bool_count(df["source_trace_complete"], False) if "source_trace_complete" in df.columns else 0
    human_audited_true = bool_count(df["human_audited"], True) if "human_audited" in df.columns else 0
    human_audited_false = bool_count(df["human_audited"], False) if "human_audited" in df.columns else 0

    # SHA uniqueness
    ev_hash_unique = int(df["evidence_text_sha256"].nunique()) if "evidence_text_sha256" in df.columns else 0
    cl_hash_unique = int(df["claim_text_sha256"].nunique()) if "claim_text_sha256" in df.columns else 0
    ev_hash_dups = n_rows - ev_hash_unique
    cl_hash_dups = n_rows - cl_hash_unique

    # Groups with four labels complete
    if "target_candidate_group_id" in df.columns and "candidate_label_guess" in df.columns:
        group_label_nunique = df.groupby("target_candidate_group_id")["candidate_label_guess"].nunique()
        groups_with_four_labels = int((group_label_nunique == 4).sum())
        groups_missing_labels = int((group_label_nunique != 4).sum())
    else:
        groups_with_four_labels = 0
        groups_missing_labels = 0

    # Duplicate hash counts (rows that are duplicates of an earlier row)
    ev_dup_rows = int(df["evidence_text_sha256"].duplicated().sum()) if "evidence_text_sha256" in df.columns else 0
    cl_dup_rows = int(df["claim_text_sha256"].duplicated().sum()) if "claim_text_sha256" in df.columns else 0

    ledger = {
        "ledger_version": "v3_17",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "dataset_name": "SimClaim Strict Silver Diagnostic Set v1",
        "dataset_role": "controlled silver diagnostic set for retrieval-to-screening format shift",
        "not_claims": [
            "gold benchmark",
            "human-audited benchmark",
            "natural prevalence dataset",
            "general scientific claim benchmark",
        ],
        "source_csv": {
            "path_repo_relative": str(csv_path.relative_to(_REPO_ROOT)).replace("\\", "/") if _REPO_ROOT in csv_path.parents else str(csv_path),
            "size_bytes": int(stat.st_size),
            "sha256": sha256,
            "mtime_utc": mtime,
            "row_count": n_rows,
            "column_count": n_cols,
        },
        "schema": {
            "columns": columns,
            "redacted_fields_present_in_csv": sorted(list(leaked)),
            "redaction_note": (
                "Fields listed in redacted_fields_present_in_csv exist in the "
                "source CSV but their raw values are NEVER copied into this "
                "ledger. Only SHA256 hashes and aggregate counts are emitted."
            ),
        },
        "statistics": {
            "rows": n_rows,
            "groups": n_groups,
            "candidate_label_guess_counts": label_counts,
            "domain_counts": domain_counts,
            "human_audited_counts": human_audited_counts,
            "human_audited_true": human_audited_true,
            "human_audited_false": human_audited_false,
            "annotation_status_counts": annotation_status_counts,
            "dataset_role_counts": dataset_role_counts,
            "final_label_nonempty": final_label_nonempty,
            "gold_label_nonempty": gold_label_nonempty,
            "source_trace_complete_true": source_trace_true,
            "source_trace_complete_false": source_trace_false,
            "silver_label_source_counts": silver_label_source_counts,
            "claim_generation_policy_counts": claim_generation_policy_counts,
            "group_quality_tier_counts": group_quality_tier_counts,
            "leakage_category_counts": leakage_category_counts,
            "evidence_text_sha256_unique": ev_hash_unique,
            "evidence_text_sha256_duplicates": ev_hash_dups,
            "evidence_text_sha256_duplicate_rows": ev_dup_rows,
            "claim_text_sha256_unique": cl_hash_unique,
            "claim_text_sha256_duplicates": cl_hash_dups,
            "claim_text_sha256_duplicate_rows": cl_dup_rows,
            "groups_with_four_labels_complete": groups_with_four_labels,
            "groups_missing_labels": groups_missing_labels,
        },
        "invariants": {
            "human_audited_all_false": human_audited_false == n_rows and human_audited_true == 0,
            "gold_label_all_empty": gold_label_nonempty == 0,
            "final_label_all_empty": final_label_nonempty == 0,
            "source_trace_complete_all_true": source_trace_true == n_rows and source_trace_false == 0,
            "silver_label_source_all_candidate_label_guess": (
                silver_label_source_counts.get("candidate_label_guess", 0) == n_rows
            ),
            "four_labels_each_111": (
                label_counts.get("supported", 0) == 111
                and label_counts.get("mild_scope_overclaim", 0) == 111
                and label_counts.get("strong_action_overclaim", 0) == 111
                and label_counts.get("contradiction_candidate", 0) == 111
            ),
            "row_count_444": n_rows == 444,
            "groups_111": n_groups == 111,
            "evidence_text_sha256_unique_is_111": ev_hash_unique == 111,
            "claim_text_sha256_unique_is_444": cl_hash_unique == 444,
        },
        "safe_caveat": (
            "We use a source-traceable controlled silver diagnostic set. "
            "The labels are not gold or human-audited, and results should "
            "not be interpreted as benchmark-level model validation."
        ),
    }
    return ledger


def write_json(ledger: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(ledger, f, indent=2, ensure_ascii=False)
    print(f"Wrote {path}")


def write_markdown(ledger: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    src = ledger["source_csv"]
    stats = ledger["statistics"]
    inv = ledger["invariants"]

    lines = []
    lines.append("# Dataset Provenance Ledger — V3.17")
    lines.append("")
    lines.append(f"**Generated (UTC):** {ledger['generated_at_utc']}")
    lines.append(f"**Ledger version:** {ledger['ledger_version']}")
    lines.append(f"**Dataset:** {ledger['dataset_name']}")
    lines.append("")
    lines.append("## Role")
    lines.append("")
    lines.append(ledger["dataset_role"])
    lines.append("")
    lines.append("## Not")
    lines.append("")
    for n in ledger["not_claims"]:
        lines.append(f"- not {n}")
    lines.append("")
    lines.append("## Safe caveat")
    lines.append("")
    lines.append(f"> {ledger['safe_caveat']}")
    lines.append("")
    lines.append("## Source CSV")
    lines.append("")
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    lines.append(f"| Path (repo-relative) | `{src['path_repo_relative']}` |")
    lines.append(f"| Size (bytes) | {src['size_bytes']} |")
    lines.append(f"| SHA256 | `{src['sha256']}` |")
    lines.append(f"| mtime (UTC) | {src['mtime_utc']} |")
    lines.append(f"| Row count | {src['row_count']} |")
    lines.append(f"| Column count | {src['column_count']} |")
    lines.append("")
    lines.append("## Statistics")
    lines.append("")
    lines.append("| Statistic | Value |")
    lines.append("|---|---|")
    lines.append(f"| rows | {stats['rows']} |")
    lines.append(f"| groups | {stats['groups']} |")
    lines.append(f"| human_audited_true | {stats['human_audited_true']} |")
    lines.append(f"| human_audited_false | {stats['human_audited_false']} |")
    lines.append(f"| final_label_nonempty | {stats['final_label_nonempty']} |")
    lines.append(f"| gold_label_nonempty | {stats['gold_label_nonempty']} |")
    lines.append(f"| source_trace_complete_true | {stats['source_trace_complete_true']} |")
    lines.append(f"| source_trace_complete_false | {stats['source_trace_complete_false']} |")
    lines.append(f"| groups_with_four_labels_complete | {stats['groups_with_four_labels_complete']} |")
    lines.append(f"| groups_missing_labels | {stats['groups_missing_labels']} |")
    lines.append(f"| evidence_text_sha256_unique | {stats['evidence_text_sha256_unique']} |")
    lines.append(f"| evidence_text_sha256_duplicates | {stats['evidence_text_sha256_duplicates']} |")
    lines.append(f"| claim_text_sha256_unique | {stats['claim_text_sha256_unique']} |")
    lines.append(f"| claim_text_sha256_duplicates | {stats['claim_text_sha256_duplicates']} |")
    lines.append("")
    lines.append("### candidate_label_guess counts")
    lines.append("")
    lines.append("| Label | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["candidate_label_guess_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### domain counts")
    lines.append("")
    lines.append("| Domain | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["domain_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### silver_label_source counts")
    lines.append("")
    lines.append("| Source | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["silver_label_source_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### claim_generation_policy counts")
    lines.append("")
    lines.append("| Policy | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["claim_generation_policy_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### human_audited counts")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["human_audited_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### annotation_status counts")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["annotation_status_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### dataset_role counts")
    lines.append("")
    lines.append("| Value | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["dataset_role_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### group_quality_tier counts")
    lines.append("")
    lines.append("| Tier | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["group_quality_tier_counts"].items()):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("### leakage_category counts")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|---|---|")
    for k, v in sorted(stats["leakage_category_counts"].items(), key=lambda x: -x[1]):
        lines.append(f"| {k} | {v} |")
    lines.append("")
    lines.append("## Invariants")
    lines.append("")
    lines.append("| Invariant | Holds |")
    lines.append("|---|---|")
    for k, v in inv.items():
        mark = "PASS" if v else "FAIL"
        lines.append(f"| {k} | {mark} |")
    lines.append("")
    lines.append("## Schema (columns)")
    lines.append("")
    lines.append("```")
    lines.append(", ".join(ledger["schema"]["columns"]))
    lines.append("```")
    lines.append("")
    lines.append("## Redaction note")
    lines.append("")
    lines.append(ledger["schema"]["redaction_note"])
    lines.append("")
    lines.append("Redacted fields present in source CSV (values NOT emitted in this ledger):")
    lines.append("")
    for f in ledger["schema"]["redacted_fields_present_in_csv"]:
        lines.append(f"- `{f}`")
    lines.append("")

    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    print(f"Wrote {path}")


def write_schema_summary_csv(ledger: dict, path: Path) -> None:
    """Write a one-row CSV summarizing the schema and key stats."""
    path.parent.mkdir(parents=True, exist_ok=True)
    src = ledger["source_csv"]
    stats = ledger["statistics"]
    inv = ledger["invariants"]

    row = {
        "dataset_name": ledger["dataset_name"],
        "ledger_version": ledger["ledger_version"],
        "generated_at_utc": ledger["generated_at_utc"],
        "csv_path_repo_relative": src["path_repo_relative"],
        "csv_size_bytes": src["size_bytes"],
        "csv_sha256": src["sha256"],
        "csv_mtime_utc": src["mtime_utc"],
        "row_count": src["row_count"],
        "column_count": src["column_count"],
        "groups": stats["groups"],
        "supported_count": stats["candidate_label_guess_counts"].get("supported", 0),
        "mild_scope_overclaim_count": stats["candidate_label_guess_counts"].get("mild_scope_overclaim", 0),
        "strong_action_overclaim_count": stats["candidate_label_guess_counts"].get("strong_action_overclaim", 0),
        "contradiction_candidate_count": stats["candidate_label_guess_counts"].get("contradiction_candidate", 0),
        "human_audited_true": stats["human_audited_true"],
        "human_audited_false": stats["human_audited_false"],
        "final_label_nonempty": stats["final_label_nonempty"],
        "gold_label_nonempty": stats["gold_label_nonempty"],
        "source_trace_complete_true": stats["source_trace_complete_true"],
        "silver_label_source_candidate_label_guess_count": stats["silver_label_source_counts"].get("candidate_label_guess", 0),
        "groups_with_four_labels_complete": stats["groups_with_four_labels_complete"],
        "groups_missing_labels": stats["groups_missing_labels"],
        "evidence_text_sha256_unique": stats["evidence_text_sha256_unique"],
        "evidence_text_sha256_duplicates": stats["evidence_text_sha256_duplicates"],
        "claim_text_sha256_unique": stats["claim_text_sha256_unique"],
        "claim_text_sha256_duplicates": stats["claim_text_sha256_duplicates"],
        "invariant_human_audited_all_false_pass": inv["human_audited_all_false"],
        "invariant_gold_label_all_empty_pass": inv["gold_label_all_empty"],
        "invariant_final_label_all_empty_pass": inv["final_label_all_empty"],
        "invariant_source_trace_complete_all_true_pass": inv["source_trace_complete_all_true"],
        "invariant_silver_label_source_all_candidate_label_guess_pass": inv["silver_label_source_all_candidate_label_guess"],
        "invariant_four_labels_each_111_pass": inv["four_labels_each_111"],
        "invariant_row_count_444_pass": inv["row_count_444"],
        "invariant_groups_111_pass": inv["groups_111"],
        "invariant_evidence_text_sha256_unique_is_111_pass": inv["evidence_text_sha256_unique_is_111"],
        "invariant_claim_text_sha256_unique_is_444_pass": inv["claim_text_sha256_unique_is_444"],
    }
    df = pd.DataFrame([row])
    df.to_csv(path, index=False, encoding="utf-8")
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser(description="Build dataset provenance ledger for V3.17.")
    parser.add_argument(
        "--csv",
        type=str,
        default=str(DEFAULT_CSV),
        help=f"Path to strict_silver CSV (default: {DEFAULT_CSV})",
    )
    parser.add_argument(
        "--reports_dir",
        type=str,
        default=str(DEFAULT_REPORTS_DIR),
        help=f"Reports directory (default: {DEFAULT_REPORTS_DIR})",
    )
    args = parser.parse_args()

    csv_path = Path(args.csv).resolve()
    reports_dir = Path(args.reports_dir).resolve()
    reports_dir.mkdir(parents=True, exist_ok=True)

    print(f"Building provenance ledger from: {csv_path}")
    ledger = build_ledger(csv_path)

    json_path = reports_dir / "dataset_provenance_ledger_v3_17.json"
    md_path = reports_dir / "dataset_provenance_ledger_v3_17.md"
    csv_out_path = reports_dir / "dataset_schema_summary_v3_17.csv"

    write_json(ledger, json_path)
    write_markdown(ledger, md_path)
    write_schema_summary_csv(ledger, csv_out_path)

    # Print summary
    print()
    print("=== Provenance ledger summary ===")
    print(f"  SHA256: {ledger['source_csv']['sha256']}")
    print(f"  rows: {ledger['statistics']['rows']}")
    print(f"  groups: {ledger['statistics']['groups']}")
    print(f"  human_audited_false: {ledger['statistics']['human_audited_false']}")
    print(f"  gold_label_nonempty: {ledger['statistics']['gold_label_nonempty']}")
    print(f"  final_label_nonempty: {ledger['statistics']['final_label_nonempty']}")
    print(f"  source_trace_complete_true: {ledger['statistics']['source_trace_complete_true']}")
    print(f"  silver_label_source=candidate_label_guess: {ledger['statistics']['silver_label_source_counts'].get('candidate_label_guess', 0)}")
    print()
    print("=== Invariants ===")
    for k, v in ledger["invariants"].items():
        mark = "PASS" if v else "FAIL"
        print(f"  [{mark}] {k}")


if __name__ == "__main__":
    main()
