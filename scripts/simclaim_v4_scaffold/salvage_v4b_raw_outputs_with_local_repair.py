import csv
import importlib.util
import json
from pathlib import Path


ROOT = Path(r"D:\ocn")
GEN_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_claim_generation.py"


def load_gen():
    spec = importlib.util.spec_from_file_location("v4_generation", GEN_SCRIPT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v4b_pilot"
    mod.OUT_CANDIDATES = mod.OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
    mod.OUT_JSONL = mod.OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.jsonl"
    mod.OUT_RAW = mod.OUT_ROOT / "raw_llm" / "v4b_claim_generation_raw_outputs.jsonl"
    mod.OUT_AUDIT = mod.OUT_ROOT / "audit" / "v4b_claim_generation_audit.csv"
    mod.OUT_REPORT = ROOT / "reports" / "simclaim_hardpair_v4b_pilot" / "v4b_claim_generation_report.md"
    return mod


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


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


def main():
    mod = load_gen()
    queue_rows = mod.read_csv(mod.QUEUE_CSV)
    raw_path = mod.OUT_RAW
    salvaged_payloads = {}
    repair_records_by_group = {}
    if not raw_path.exists():
        raise RuntimeError(f"raw file missing: {raw_path}")
    for line in raw_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        obj = json.loads(line)
        payload = obj.get("payload")
        gid = obj.get("v4_group_id")
        if not gid or not payload:
            continue
        repaired, repairs = mod.local_repair_payload(payload)
        ok, reason = mod.validate_payload(repaired)
        if ok:
            salvaged_payloads[gid] = repaired
            repair_records_by_group[gid] = repairs

    audits = []
    payloads = []
    for gid, payload in sorted(salvaged_payloads.items()):
        payloads.append(payload)
        audits.append({
            "v4_group_id": gid,
            "status": "success_after_local_repair",
            "attempt": "salvage",
            "reason": "ok_after_local_repair",
            "model": "deepseek-chat",
            "local_repair_records": json.dumps(repair_records_by_group.get(gid, []), ensure_ascii=False),
        })

    generated_rows = mod.materialize_rows(queue_rows, payloads, audits)
    previous = read_csv(mod.OUT_CANDIDATES) if mod.OUT_CANDIDATES.exists() else queue_rows
    by_id = {r["candidate_id"]: r for r in previous}
    selected_set = set(salvaged_payloads)
    for row in generated_rows:
        if row.get("v4_group_id") in selected_set:
            by_id[row["candidate_id"]] = row
    all_rows = [by_id.get(r["candidate_id"], r) for r in queue_rows]
    write_csv(mod.OUT_CANDIDATES, all_rows)
    mod.write_jsonl(mod.OUT_JSONL, all_rows)

    old_audits = read_csv(mod.OUT_AUDIT) if mod.OUT_AUDIT.exists() else []
    old_audits = [r for r in old_audits if r.get("v4_group_id") not in selected_set]
    write_csv(mod.OUT_AUDIT, old_audits + audits)
    mod.write_report(all_rows, old_audits + audits, len(selected_set))

    print(json.dumps({
        "status": "ok",
        "salvaged_groups": len(selected_set),
        "salvaged_rows": len(selected_set) * 4,
        "candidates_csv": str(mod.OUT_CANDIDATES),
        "audit_csv": str(mod.OUT_AUDIT),
        "report_md": str(mod.OUT_REPORT),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
