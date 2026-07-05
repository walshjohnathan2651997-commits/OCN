import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
INVENTORY_CSV = ROOT / "data" / "simclaim_v4_scaffold" / "audit" / "v4_source_pool_inventory.csv"
OUT_ROOT = ROOT / "data" / "simclaim_v4_scaffold"
AUDIT_DIR = OUT_ROOT / "audit"
REGISTRY_CSV = AUDIT_DIR / "v4_unique_evidence_registry.csv"
REPORT_MD = ROOT / "reports" / "simclaim_v4_scaffold" / "v4_unique_evidence_registry_report.md"

SOURCE_ROLES = {
    "current_best_pilot",
    "possible_v4_source_pool",
    "small_trace_complete_pool",
}
EXCLUDE_PATH_MARKERS = [
    "simclaim_hardpair_v3_targeted",
    "simclaim_hardpair_v3b",
    "simclaim_hardpair_v2",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read_jsonl(path):
    rows = []
    with path.open("r", encoding="utf-8-sig") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                rows.append(obj)
    return rows


def read_rows(path):
    if path.suffix.lower() == ".csv":
        return read_csv(path)
    if path.suffix.lower() == ".jsonl":
        return read_jsonl(path)
    return []


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
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


def norm_text(text):
    return re.sub(r"\s+", " ", str(text or "")).strip().lower()


def hash_key(*parts):
    joined = "\n".join(norm_text(p) for p in parts)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()[:16]


def complete_trace(row):
    fields = ["claim_source_url", "evidence_source_url", "claim_location", "evidence_location", "source_pair_id"]
    return all(str(row.get(f, "")).strip() for f in fields)


def select_files():
    inventory = read_csv(INVENTORY_CSV)
    selected = []
    seen_paths = set()
    for item in inventory:
        path = item.get("file_path", "")
        low = path.lower()
        if item.get("read_status") != "ok":
            continue
        if item.get("role_hint") not in SOURCE_ROLES:
            continue
        if item.get("has_claim_text") != "true" or item.get("has_evidence_text") != "true":
            continue
        if item.get("extension") != ".csv":
            continue
        if any(marker in low for marker in EXCLUDE_PATH_MARKERS):
            continue
        if "\\splits\\" in low or "\\splits_group_stratified\\" in low:
            continue
        if path in seen_paths:
            continue
        seen_paths.add(path)
        selected.append(item)
    return selected


def main():
    selected = select_files()
    grouped = {}
    origins = defaultdict(list)
    label_counts = defaultdict(Counter)
    for item in selected:
        path = Path(item["file_path"])
        rows = read_rows(path)
        for row in rows:
            if not str(row.get("evidence_text", "")).strip():
                continue
            key = hash_key(row.get("evidence_text", ""), row.get("evidence_source_url", ""), row.get("evidence_location", ""))
            if key not in grouped:
                grouped[key] = {
                    "evidence_registry_id": f"V4-EVID-{len(grouped)+1:04d}",
                    "evidence_key": key,
                    "domain": row.get("domain", ""),
                    "paper_title": row.get("paper_title", row.get("evidence_source_title", "")),
                    "paper_year": row.get("paper_year", ""),
                    "source_pair_id": row.get("source_pair_id", ""),
                    "claim_source_url": row.get("claim_source_url", ""),
                    "evidence_source_url": row.get("evidence_source_url", ""),
                    "claim_location": row.get("claim_location", ""),
                    "evidence_location": row.get("evidence_location", ""),
                    "source_location": row.get("source_location", ""),
                    "evidence_text": row.get("evidence_text", ""),
                    "evidence_text_sha256": hashlib.sha256(str(row.get("evidence_text", "")).encode("utf-8")).hexdigest(),
                    "trace_complete": str(complete_trace(row)).lower(),
                    "in_current_v3": str("simclaim_hardpair_v3\\candidates" in str(path).lower()).lower(),
                }
            if "simclaim_hardpair_v3\\candidates" in str(path).lower():
                grouped[key]["in_current_v3"] = "true"
            origins[key].append(str(path))
            label = row.get("candidate_label_guess") or row.get("final_label") or row.get("escalation_label") or ""
            if label:
                label_counts[key][label] += 1

    rows = []
    for key, rec in grouped.items():
        origin_set = sorted(set(origins[key]))
        rec["n_origin_files"] = len(origin_set)
        rec["origin_files"] = " | ".join(origin_set)
        rec["labels_seen"] = " | ".join(f"{label}:{count}" for label, count in label_counts[key].most_common())
        rows.append(rec)

    rows.sort(key=lambda r: (r["in_current_v3"] != "true", r["trace_complete"] != "true", r["evidence_registry_id"]))
    write_csv(REGISTRY_CSV, rows)

    n_trace = sum(1 for r in rows if r["trace_complete"] == "true")
    n_v3 = sum(1 for r in rows if r["in_current_v3"] == "true")
    n_new = sum(1 for r in rows if r["in_current_v3"] != "true" and r["trace_complete"] == "true")
    domains = Counter(r["domain"] or "unknown" for r in rows)

    REPORT_MD.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "# v4 unique evidence registry report",
        "",
        "This registry deduplicates local trace-complete candidate/evidence files into unique evidence records. It does not modify source files, annotate, train, or run LLMs.",
        "",
        "## Summary",
        "",
        f"- Source files selected: {len(selected)}",
        f"- Unique evidence records: {len(rows)}",
        f"- Trace-complete unique evidence records: {n_trace}",
        f"- Evidence records already represented in current v3: {n_v3}",
        f"- Trace-complete evidence records not in current v3: {n_new}",
        "",
        "## Domain counts",
        "",
        "| domain | unique evidence records |",
        "|---|---:|",
    ]
    for domain, count in domains.most_common():
        lines.append(f"| {domain} | {count} |")
    lines.extend([
        "",
        "## Interpretation",
        "",
        "The local project contains enough trace-complete material to maintain the current pilot, but the deduplicated evidence count is the real limit. If the trace-complete unique evidence count is far below 150, v4 needs either source recovery or new source extraction before large-scale generation.",
        "",
        "## Output",
        "",
        f"- Registry CSV: `{REGISTRY_CSV}`",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")

    print(json.dumps({
        "status": "ok",
        "selected_source_files": len(selected),
        "unique_evidence_records": len(rows),
        "trace_complete_unique_evidence_records": n_trace,
        "in_current_v3": n_v3,
        "trace_complete_not_in_current_v3": n_new,
        "registry_csv": str(REGISTRY_CSV),
        "report_md": str(REPORT_MD),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
