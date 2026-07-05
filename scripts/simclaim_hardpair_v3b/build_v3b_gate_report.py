import csv
import json
from pathlib import Path


ROOT = Path(r"D:\ocn")
OUT_DIR = ROOT / "reports" / "simclaim_hardpair_v3b"
OUT_CSV = OUT_DIR / "v3b_gate_metric_comparison.csv"
OUT_MD = OUT_DIR / "v3b_gate_report.md"

V3_READOUT = ROOT / "reports" / "simclaim_hardpair_v3" / "v3_final_metric_readout.csv"
V3B_TRAD = ROOT / "experiments" / "simclaim_hardpair_v3b_small_baselines" / "metrics" / "hardpair_v3b_small_data_baseline_metrics.csv"
V3B_SUMMARY = OUT_DIR / "v3b_summary.json"

TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def best(rows, target, view):
    sub = [r for r in rows if r["split"] == "test" and r["target"] == target and r["text_view"] == view]
    return max(sub, key=lambda r: float(r["macro_f1"]))


def main():
    summary = json.loads(V3B_SUMMARY.read_text(encoding="utf-8"))
    v3 = read_csv(V3_READOUT)
    v3b = read_csv(V3B_TRAD)
    rows = []
    for target in TARGETS:
        prior = next((r for r in v3 if r["target"] == target), {})
        claim = best(v3b, target, "claim_only")
        ce = best(v3b, target, "claim_evidence")
        rows.append({
            "target": target,
            "v3_traditional_claim_only_macro_f1": prior.get("v3_traditional_claim_only_macro_f1", ""),
            "v3_traditional_claim_evidence_macro_f1": prior.get("v3_traditional_claim_evidence_macro_f1", ""),
            "v3b_traditional_claim_only_macro_f1": claim["macro_f1"],
            "v3b_traditional_claim_evidence_macro_f1": ce["macro_f1"],
            "v3b_ce_minus_claim_only": f"{float(ce['macro_f1']) - float(claim['macro_f1']):.6f}",
        })
    write_csv(OUT_CSV, rows)

    lines = []
    lines.append("# v3b gate report")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("v3b is rejected as a data-generation branch. Keep v3 as the current best pilot dataset.")
    lines.append("")
    lines.append("## Why")
    lines.append("")
    lines.append("v3b preserved evidence fidelity, but it made traditional claim-only leakage worse, especially for escalation. Because the cheap diagnostic failed, a full LLM run is not worth doing for this branch.")
    lines.append("")
    lines.append("## Fidelity status")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Evidence locked unchanged rate: {summary['evidence_locked_unchanged_rate']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Generation status: {summary['generation_status_counts']}")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("| target | v3 claim-only | v3 claim+evidence | v3b claim-only | v3b claim+evidence | v3b CE - claim |")
    lines.append("|---|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['target']} | {row['v3_traditional_claim_only_macro_f1']} | {row['v3_traditional_claim_evidence_macro_f1']} | "
            f"{row['v3b_traditional_claim_only_macro_f1']} | {row['v3b_traditional_claim_evidence_macro_f1']} | {row['v3b_ce_minus_claim_only']} |"
        )
    lines.append("")
    lines.append("## Next")
    lines.append("")
    lines.append("Do not continue v3b. The next useful path is to keep v3 and perform a smaller targeted audit/rewrite only on rows where LLM claim-only beats claim+evidence, rather than rewriting all groups.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- gate_metric_csv: `{OUT_CSV}`")
    lines.append("- current_best_dataset: `D:\\ocn\\data\\simclaim_hardpair_v3\\candidates\\simclaim_hardpair_v3_268.csv`")
    lines.append("- rejected_v3b_dataset: `D:\\ocn\\data\\simclaim_hardpair_v3b\\candidates\\simclaim_hardpair_v3b_268.csv`")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
