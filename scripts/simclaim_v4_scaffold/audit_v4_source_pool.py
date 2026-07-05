import csv
import json
from collections import Counter
from pathlib import Path


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data"
OUT_ROOT = ROOT / "data" / "simclaim_v4_scaffold"
AUDIT_DIR = OUT_ROOT / "audit"
REPORT_DIR = ROOT / "reports" / "simclaim_v4_scaffold"
INVENTORY_CSV = AUDIT_DIR / "v4_source_pool_inventory.csv"
REPORT_MD = REPORT_DIR / "v4_source_pool_readiness.md"

KEYWORDS = [
    "simclaim",
    "candidate",
    "human_audit",
    "hardpair",
    "mvp",
    "eval",
    "annotation",
]
TEXT_FIELDS = ["claim_text", "evidence_text"]
TRACE_FIELDS = ["claim_source_url", "evidence_source_url", "claim_location", "evidence_location", "source_pair_id"]
LABEL_FIELDS = ["candidate_label_guess", "final_label", "gold_label", "escalation_label", "escalation_binary_label_guess", "issue_binary_label_guess"]
QUALITY_FIELDS = ["trace_quality", "semantic_quality", "source_trace_complete", "source_trace_status", "source_trace_score"]


def iter_candidate_files():
    for path in DATA_ROOT.rglob("*"):
        if not path.is_file():
            continue
        if path.suffix.lower() not in {".csv", ".jsonl"}:
            continue
        low = path.name.lower()
        if any(k in low for k in KEYWORDS) or any(k in str(path.parent).lower() for k in KEYWORDS):
            yield path


def read_csv_rows(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl_rows(path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    rows.append(obj)
            except json.JSONDecodeError:
                continue
    return rows


def read_rows(path):
    if path.suffix.lower() == ".csv":
        return read_csv_rows(path)
    return read_jsonl_rows(path)


def nonempty(row, field):
    return bool(str(row.get(field, "")).strip())


def completeness(rows, fields):
    if not rows:
        return 0.0
    ok = 0
    for row in rows:
        if all(nonempty(row, f) for f in fields):
            ok += 1
    return ok / len(rows)


def any_field(columns, fields):
    return any(f in columns for f in fields)


def unique_count(rows, field):
    if not rows or field not in rows[0]:
        return 0
    return len({str(r.get(field, "")).strip() for r in rows if str(r.get(field, "")).strip()})


def role_for(path, row):
    p = str(path).lower()
    rows = int(row["row_count"])
    trace_rate = float(row["full_trace_complete_rate"])
    has_labels = row["has_candidate_label_guess"] == "true" or row["has_final_label"] == "true"
    if "simclaim_hardpair_v3\\candidates" in p:
        return "current_best_pilot"
    if "simclaim_hardpair_v3_targeted" in p:
        return "rejected_targeted_diagnostic"
    if "simclaim_hardpair_v3b" in p or "simclaim_hardpair_v2" in p:
        return "older_generated_branch"
    if "human_audit_round1_150_from_588_optimized_v2" in p:
        return "588_derivative_trace_incomplete"
    if rows >= 100 and trace_rate >= 0.9 and has_labels:
        return "possible_v4_source_pool"
    if rows >= 50 and has_labels:
        return "possible_v4_source_needs_trace_check"
    if rows >= 10 and trace_rate >= 0.9:
        return "small_trace_complete_pool"
    return "supporting_or_low_priority"


def score(row):
    s = 0
    rows = int(row["row_count"])
    if rows >= 100:
        s += 20
    elif rows >= 50:
        s += 10
    if row["has_claim_text"] == "true":
        s += 10
    if row["has_evidence_text"] == "true":
        s += 10
    if row["has_source_pair_id"] == "true":
        s += 10
    if row["has_claim_source_url"] == "true":
        s += 6
    if row["has_evidence_source_url"] == "true":
        s += 6
    if row["has_claim_location"] == "true":
        s += 5
    if row["has_evidence_location"] == "true":
        s += 5
    if row["has_candidate_label_guess"] == "true":
        s += 8
    if row["has_final_label"] == "true":
        s += 8
    if float(row["full_trace_complete_rate"]) >= 0.9:
        s += 15
    if row["role_hint"] == "current_best_pilot":
        s += 30
    if row["role_hint"] == "possible_v4_source_pool":
        s += 25
    if row["role_hint"] == "588_derivative_trace_incomplete":
        s += 5
    return s


def audit_file(path):
    try:
        rows = read_rows(path)
    except Exception as exc:
        return {
            "file_path": str(path),
            "read_status": "error",
            "read_error": str(exc),
            "row_count": 0,
            "column_count": 0,
        }
    if not rows:
        return {
            "file_path": str(path),
            "read_status": "empty",
            "read_error": "",
            "row_count": 0,
            "column_count": 0,
        }
    columns = []
    seen = set()
    for row in rows[:100]:
        for key in row:
            if key not in seen:
                seen.add(key)
                columns.append(key)
    colset = set(columns)
    out = {
        "file_path": str(path),
        "file_name": path.name,
        "extension": path.suffix.lower(),
        "read_status": "ok",
        "read_error": "",
        "row_count": len(rows),
        "column_count": len(columns),
        "unique_evidence_text": unique_count(rows, "evidence_text"),
        "unique_claim_text": unique_count(rows, "claim_text"),
        "unique_source_pair_id": unique_count(rows, "source_pair_id"),
        "unique_hardpair_group_id": unique_count(rows, "hardpair_group_id"),
        "claim_evidence_complete_rate": round(completeness(rows, TEXT_FIELDS), 4),
        "full_trace_complete_rate": round(completeness(rows, TRACE_FIELDS), 4),
        "has_claim_text": str("claim_text" in colset).lower(),
        "has_evidence_text": str("evidence_text" in colset).lower(),
        "has_source_pair_id": str("source_pair_id" in colset).lower(),
        "has_claim_source_url": str("claim_source_url" in colset).lower(),
        "has_evidence_source_url": str("evidence_source_url" in colset).lower(),
        "has_claim_location": str("claim_location" in colset).lower(),
        "has_evidence_location": str("evidence_location" in colset).lower(),
        "has_candidate_label_guess": str("candidate_label_guess" in colset).lower(),
        "has_final_label": str("final_label" in colset).lower(),
        "has_human_audited": str("human_audited" in colset).lower(),
        "has_quality_fields": str(any_field(colset, QUALITY_FIELDS)).lower(),
        "label_fields_present": "|".join([f for f in LABEL_FIELDS if f in colset]),
        "quality_fields_present": "|".join([f for f in QUALITY_FIELDS if f in colset]),
        "columns": "|".join(columns),
    }
    out["role_hint"] = role_for(path, out)
    out["priority_score"] = score(out)
    return out


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fieldnames = []
    seen = set()
    for row in rows:
        for key in row:
            if key not in seen:
                seen.add(key)
                fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_report(rows):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    usable = [r for r in rows if r.get("read_status") == "ok" and r.get("has_claim_text") == "true" and r.get("has_evidence_text") == "true"]
    roles = Counter(r.get("role_hint", "") for r in rows)
    top = sorted(usable, key=lambda r: int(r.get("priority_score", 0)), reverse=True)[:15]
    possible = [r for r in usable if r.get("role_hint") in {"possible_v4_source_pool", "current_best_pilot", "possible_v4_source_needs_trace_check", "588_derivative_trace_incomplete"}]

    lines = [
        "# v4 source-pool readiness audit",
        "",
        "This audit only inventories existing local CSV/JSONL files. It does not modify source data, train models, annotate, or run LLM generation.",
        "",
        "## Summary",
        "",
        f"- Files audited: {len(rows)}",
        f"- Files with claim/evidence text: {len(usable)}",
        f"- Possible v4-relevant pools: {len(possible)}",
        "",
        "## Role counts",
        "",
        "| role | count |",
        "|---|---:|",
    ]
    for role, count in roles.most_common():
        lines.append(f"| {role} | {count} |")

    lines.extend([
        "",
        "## Top candidate/source files",
        "",
        "| rank | role | rows | unique evidence | trace rate | file |",
        "|---:|---|---:|---:|---:|---|",
    ])
    for i, r in enumerate(top, 1):
        lines.append(
            f"| {i} | {r.get('role_hint','')} | {r.get('row_count','')} | {r.get('unique_evidence_text','')} | {r.get('full_trace_complete_rate','')} | `{r.get('file_path','')}` |"
        )

    lines.extend([
        "",
        "## Readiness interpretation",
        "",
        "- The current hardpair v3 dataset remains the best pilot artifact.",
        "- The 150-row file derived from the missing 588 master has useful content but incomplete source trace fields, so it should not be promoted directly as a paper-ready master.",
        "- For Q1-level work, v4 should expand from trace-complete evidence groups and evaluate robustness across group splits.",
        "",
        "## Recommended next action",
        "",
        "Build a v4 generation queue from trace-complete source/evidence groups first. If enough groups are not available locally, recover or reconstruct source trace before generating more candidates.",
        "",
        "## Output",
        "",
        f"- Inventory CSV: `{INVENTORY_CSV}`",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = [audit_file(path) for path in iter_candidate_files()]
    rows = sorted(rows, key=lambda r: (int(r.get("priority_score", 0)), int(r.get("row_count", 0))), reverse=True)
    write_csv(INVENTORY_CSV, rows)
    write_report(rows)
    print(json.dumps({
        "status": "ok",
        "files_audited": len(rows),
        "inventory_csv": str(INVENTORY_CSV),
        "report_md": str(REPORT_MD),
        "top_files": [
            {
                "file_path": r.get("file_path"),
                "role_hint": r.get("role_hint"),
                "row_count": r.get("row_count"),
                "full_trace_complete_rate": r.get("full_trace_complete_rate"),
                "priority_score": r.get("priority_score"),
            }
            for r in rows[:10]
        ],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
