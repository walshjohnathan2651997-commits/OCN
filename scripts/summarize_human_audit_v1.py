#!/usr/bin/env python
"""summarize_human_audit_v1.py — Summarize a filled human audit CSV.

Reads an audit CSV (filled by an auditor — every row has auditor_label and
auditor_confidence) and writes summary artifacts to
experiments/human_audit_v1/:

  audit_agreement_summary.json     — overall metrics
  audit_confusion_matrix.csv       — silver_label x auditor_label
  audit_disagreement_cases_redacted.csv  — hash-only disagreement rows
  audit_summary.md                 — narrative with safe/unsafe wording

Metrics:
  - silver_vs_auditor_agreement        — exact match rate (excluding uncertain)
  - strong_action_precision_in_top20   — of top20 rows where auditor says
    strong_action_overclaim, how many did silver also call strong_action?
  - strong_action_precision_in_top50   — same for queue_rank <= 50
  - major_disagreement_rate            — rows where auditor and silver disagree
    on the supported vs strong_action_overclaim axis
  - uncertain_rate                     — rows with auditor_label ==
    uncertain_insufficient_context

Hard boundaries:
  - no API, no network, no training
  - no original CSV modification, no gold_label fill
  - no raw claim/evidence text in any output (hash-only)
  - the audit is a directional reliability check, NOT a gold benchmark

Usage:
  python scripts/summarize_human_audit_v1.py \\
      --audit-csv data/audit_templates/human_audit_queue_seed_v1.csv \\
      --config configs/v3_17_confidential_default.yaml
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from collections import Counter, defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import (  # noqa: E402
    load_and_validate, resolve_path, write_run_config, print_guards,
)

VALID_AUDITOR_LABELS = {
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
    "uncertain_insufficient_context",
}

# Columns allowed in the redacted disagreement CSV (no identifiers, no raw text).
REDACTED_DISAGREEMENT_COLUMNS = [
    "audit_item_id",
    "source_hash",
    "claim_text_hash",
    "evidence_text_hash",
    "model_pred",
    "silver_label",
    "auditor_label",
    "auditor_confidence",
    "queue_rank",
    "queue_source",
    "disagreement_reason",
]

CONFUSION_COLUMNS = ["silver_label", "auditor_label", "n"]


def read_csv_rows(path: Path) -> list[dict]:
    # utf-8-sig strips a leading BOM if present (some V3.17 CSVs ship with one).
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def parse_int(s: str, default: int = 0) -> int:
    try:
        return int(s)
    except (TypeError, ValueError):
        return default


def parse_bool(s: str) -> bool:
    return str(s).strip().lower() in {"true", "1", "yes", "y"}


def is_filled(row: dict) -> bool:
    """A row counts as filled if it has an auditor label and confidence."""
    label = (row.get("auditor_label") or "").strip()
    conf = (row.get("auditor_confidence") or "").strip()
    return bool(label and conf)


def compute_metrics(rows: list[dict]) -> dict:
    n_filled = len(rows)
    if n_filled == 0:
        return {
            "n_filled": 0,
            "silver_vs_auditor_agreement": None,
            "strong_action_precision_in_top20": None,
            "strong_action_precision_in_top50": None,
            "major_disagreement_rate": None,
            "uncertain_rate": None,
            "n_uncertain": 0,
            "n_disagreement": 0,
            "n_major_disagreement": 0,
            "note": "no filled rows",
        }

    # Agreement (exclude uncertain from denominator, per protocol).
    n_uncertain = sum(
        1 for r in rows
        if (r.get("auditor_label") or "").strip() == "uncertain_insufficient_context"
    )
    n_decided = n_filled - n_uncertain
    n_agree = 0
    for r in rows:
        a_label = (r.get("auditor_label") or "").strip()
        if a_label == "uncertain_insufficient_context":
            continue
        silver = (r.get("silver_label") or "").strip()
        if a_label == silver:
            n_agree += 1
    agreement = (n_agree / n_decided) if n_decided > 0 else None

    # Strong-action precision in top20 / top50.
    def strong_action_precision(max_rank: int) -> float | None:
        # Among rows with queue_rank <= max_rank AND auditor_label ==
        # strong_action_overclaim, fraction where silver_label ==
        # strong_action_overclaim.
        subset = [
            r for r in rows
            if parse_int(r.get("queue_rank", "0")) <= max_rank
            and (r.get("auditor_label") or "").strip() == "strong_action_overclaim"
        ]
        if not subset:
            return None
        tp = sum(
            1 for r in subset
            if (r.get("silver_label") or "").strip() == "strong_action_overclaim"
        )
        return tp / len(subset)

    p_top20 = strong_action_precision(20)
    p_top50 = strong_action_precision(50)

    # Disagreement (any) and major disagreement (supported vs strong axis).
    n_disagreement = 0
    n_major_disagreement = 0
    major_axis = {"supported", "strong_action_overclaim"}
    for r in rows:
        a_label = (r.get("auditor_label") or "").strip()
        silver = (r.get("silver_label") or "").strip()
        if a_label == "uncertain_insufficient_context":
            continue
        if a_label != silver:
            n_disagreement += 1
            if a_label in major_axis and silver in major_axis and a_label != silver:
                n_major_disagreement += 1

    major_disagreement_rate = (
        n_major_disagreement / n_decided if n_decided > 0 else None
    )
    disagreement_rate = n_disagreement / n_decided if n_decided > 0 else None
    uncertain_rate = n_uncertain / n_filled if n_filled > 0 else None

    return {
        "n_filled": n_filled,
        "n_decided": n_decided,
        "n_uncertain": n_uncertain,
        "n_disagreement": n_disagreement,
        "n_major_disagreement": n_major_disagreement,
        "silver_vs_auditor_agreement": round(agreement, 4) if agreement is not None else None,
        "any_disagreement_rate": round(disagreement_rate, 4) if disagreement_rate is not None else None,
        "major_disagreement_rate": round(major_disagreement_rate, 4) if major_disagreement_rate is not None else None,
        "uncertain_rate": round(uncertain_rate, 4) if uncertain_rate is not None else None,
        "strong_action_precision_in_top20": (
            round(p_top20, 4) if p_top20 is not None else None
        ),
        "strong_action_precision_in_top50": (
            round(p_top50, 4) if p_top50 is not None else None
        ),
    }


def build_confusion_matrix(rows: list[dict]) -> list[dict]:
    """silver_label x auditor_label counts."""
    cell: dict[tuple[str, str], int] = defaultdict(int)
    for r in rows:
        silver = (r.get("silver_label") or "").strip() or "(missing)"
        a_label = (r.get("auditor_label") or "").strip() or "(missing)"
        cell[(silver, a_label)] += 1
    out: list[dict] = []
    for (silver, a_label), n in sorted(cell.items()):
        out.append({
            "silver_label": silver,
            "auditor_label": a_label,
            "n": n,
        })
    return out


def build_disagreement_rows(rows: list[dict]) -> list[dict]:
    """Redacted disagreement rows (no candidate_id, no group_id, no raw text)."""
    out: list[dict] = []
    for r in rows:
        a_label = (r.get("auditor_label") or "").strip()
        silver = (r.get("silver_label") or "").strip()
        if a_label == "uncertain_insufficient_context":
            continue
        if a_label == silver:
            continue
        out.append({
            "audit_item_id": r.get("audit_item_id", ""),
            "source_hash": r.get("source_hash", ""),
            "claim_text_hash": r.get("claim_text_hash", ""),
            "evidence_text_hash": r.get("evidence_text_hash", ""),
            "model_pred": r.get("model_pred", ""),
            "silver_label": silver,
            "auditor_label": a_label,
            "auditor_confidence": r.get("auditor_confidence", ""),
            "queue_rank": r.get("queue_rank", ""),
            "queue_source": r.get("queue_source", ""),
            "disagreement_reason": r.get("disagreement_reason", ""),
        })
    return out


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in columns})


def write_summary_md(path: Path, metrics: dict,
                     confusion: list[dict], n_disagreement_rows: int) -> None:
    lines: list[str] = []
    lines.append("# Human Audit Summary (v1)")
    lines.append("")
    lines.append(f"Generated: {datetime.now(timezone.utc).isoformat()}")
    lines.append("")
    lines.append("## Disclaimer")
    lines.append("")
    lines.append("This is a **small targeted audit, not a gold benchmark**.")
    lines.append("Do not claim human-audited dataset.")
    lines.append("Use it only to support directional reliability of the top")
    lines.append("review queue and silver labels.")
    lines.append("")
    lines.append("## Safe vs Unsafe Wording")
    lines.append("")
    lines.append("**Safe** (allowed):")
    lines.append("- \"small targeted audit, not a gold benchmark\"")
    lines.append("- \"directional reliability check on the top of the review queue\"")
    lines.append("- \"auditor agreement with silver on the audited subset was X%\"")
    lines.append("- \"strong_action precision in the top-20 audited subset was Y\"")
    lines.append("")
    lines.append("**Unsafe** (forbidden):")
    lines.append("- \"human-validated dataset\"")
    lines.append("- \"gold benchmark\"")
    lines.append("- \"the silver labels are correct\"")
    lines.append("- \"the model generalizes to real claims\"")
    lines.append("- \"SOTA\"")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append(f"- n_filled: {metrics.get('n_filled')}")
    lines.append(f"- n_decided (excluding uncertain): {metrics.get('n_decided')}")
    lines.append(f"- n_uncertain: {metrics.get('n_uncertain')}")
    lines.append(f"- n_disagreement (any): {metrics.get('n_disagreement')}")
    lines.append(f"- n_major_disagreement (supported vs strong axis): "
                 f"{metrics.get('n_major_disagreement')}")
    lines.append("")
    lines.append("| Metric | Value |")
    lines.append("|--------|-------|")
    for k in [
        "silver_vs_auditor_agreement",
        "any_disagreement_rate",
        "major_disagreement_rate",
        "uncertain_rate",
        "strong_action_precision_in_top20",
        "strong_action_precision_in_top50",
    ]:
        v = metrics.get(k)
        lines.append(f"| {k} | {v if v is not None else 'n/a'} |")
    lines.append("")
    lines.append("## Silver x Auditor Confusion Matrix")
    lines.append("")
    lines.append("| silver_label | auditor_label | n |")
    lines.append("|--------------|---------------|---|")
    for c in confusion:
        lines.append(f"| {c['silver_label']} | {c['auditor_label']} | {c['n']} |")
    lines.append("")
    lines.append(f"## Disagreement Cases (redacted, hash-only)")
    lines.append("")
    lines.append(f"{n_disagreement_rows} disagreement rows written to "
                 "`audit_disagreement_cases_redacted.csv`. No raw text, no "
                 "candidate_id, no target_candidate_group_id.")
    lines.append("")
    lines.append("## Methodology Notes")
    lines.append("")
    lines.append("- Agreement excludes `uncertain_insufficient_context` rows from")
    lines.append("  the denominator, per protocol.")
    lines.append("- Major disagreement is restricted to the")
    lines.append("  supported vs strong_action_overclaim axis (the highest-stakes")
    lines.append("  axis for the paper).")
    lines.append("- Strong-action precision in top20/top50 is computed over rows")
    lines.append("  with queue_rank <= 20 / 50 and auditor_label == ")
    lines.append("  strong_action_overclaim. It measures whether silver also")
    lines.append("  called these rows strong_action_overclaim. n/a if no such rows.")
    lines.append("- All outputs are hash-only. No raw claim or evidence text is")
    lines.append("  written by this script.")
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def run(args) -> int:
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    audit_csv = Path(args.audit_csv)
    if not audit_csv.is_absolute():
        audit_csv = (Path(__file__).resolve().parent.parent / audit_csv)
    if not audit_csv.exists():
        print(f"ERROR: audit csv not found: {audit_csv}", file=sys.stderr)
        return 2

    rows = read_csv_rows(audit_csv)
    print(f"loaded {len(rows)} audit rows from {audit_csv}", flush=True)

    filled_rows = [r for r in rows if is_filled(r)]
    print(f"filled rows: {len(filled_rows)}", flush=True)

    # Validate auditor labels.
    bad = [r for r in filled_rows
           if (r.get("auditor_label") or "").strip() not in VALID_AUDITOR_LABELS]
    if bad:
        sample = [(r.get("audit_item_id"), r.get("auditor_label"))
                  for r in bad[:5]]
        print(f"ERROR: {len(bad)} rows have invalid auditor_label. "
              f"First 5: {sample}", file=sys.stderr)
        return 3

    metrics = compute_metrics(filled_rows)
    confusion = build_confusion_matrix(filled_rows)
    disagreement_rows = build_disagreement_rows(filled_rows)

    out_dir = Path(args.out_dir)
    if not out_dir.is_absolute():
        out_dir = Path(__file__).resolve().parent.parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    summary_json_path = out_dir / "audit_agreement_summary.json"
    confusion_csv_path = out_dir / "audit_confusion_matrix.csv"
    disagreement_csv_path = out_dir / "audit_disagreement_cases_redacted.csv"
    summary_md_path = out_dir / "audit_summary.md"

    summary_payload = {
        "script_name": "summarize_human_audit_v1.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "audit_csv": str(audit_csv),
        "n_loaded": len(rows),
        "n_filled": len(filled_rows),
        "metrics": metrics,
        "disclaimer": (
            "Small targeted audit, not a gold benchmark. "
            "Directional reliability check only. "
            "Do not claim human-validated dataset."
        ),
        "guards": {
            "no_api": config.get("no_api"),
            "no_network": config.get("no_network"),
            "no_training": config.get("no_training"),
            "no_original_data_modification": config.get(
                "no_original_data_modification", True
            ),
        },
        "no_raw_text_in_outputs": True,
    }
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(summary_payload, f, indent=2, ensure_ascii=False)

    write_csv(confusion_csv_path, confusion, CONFUSION_COLUMNS)
    write_csv(disagreement_csv_path, disagreement_rows,
              REDACTED_DISAGREEMENT_COLUMNS)
    write_summary_md(summary_md_path, metrics, confusion, len(disagreement_rows))

    print(f"wrote {summary_json_path}", flush=True)
    print(f"wrote {confusion_csv_path}", flush=True)
    print(f"wrote {disagreement_csv_path}", flush=True)
    print(f"wrote {summary_md_path}", flush=True)

    # Redaction check: no raw-text columns in any output.
    forbidden = {"claim_text", "evidence_text", "selected_evidence",
                 "candidate_id", "target_candidate_group_id"}
    for p in [confusion_csv_path, disagreement_csv_path]:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header_set = set(reader.fieldnames or [])
            leak = header_set & forbidden
            assert not leak, f"forbidden columns in {p}: {leak}"
    print("redaction check: PASS", flush=True)

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--audit-csv", required=True,
                        help="Path to filled audit CSV")
    parser.add_argument("--config", default=None,
                        help="Path to YAML config")
    parser.add_argument("--out-dir", default="experiments/human_audit_v1",
                        help="Output directory")
    parser.add_argument("--toy_mode", action="store_true",
                        help="Use toy demo config")
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
