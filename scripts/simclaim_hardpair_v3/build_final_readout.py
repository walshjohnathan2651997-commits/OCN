import csv
import json
from pathlib import Path


ROOT = Path(r"D:\ocn")
OUT_DIR = ROOT / "reports" / "simclaim_hardpair_v3"
OUT_CSV = OUT_DIR / "v3_final_metric_readout.csv"
OUT_MD = OUT_DIR / "v3_final_readout.md"

V3_SUMMARY = OUT_DIR / "v3_summary.json"
V2B_COMPARISON = ROOT / "reports" / "simclaim_hardpair_v2b" / "small_data_iteration_comparison.csv"
V3_TRAD = ROOT / "experiments" / "simclaim_hardpair_v3_small_baselines" / "metrics" / "hardpair_v3_small_data_baseline_metrics.csv"
V3_LLM = ROOT / "experiments" / "simclaim_hardpair_v3_llm_small_eval" / "metrics" / "hardpair_v3_llm_small_eval_metrics.csv"

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


def best(rows, target, **filters):
    sub = [r for r in rows if r.get("split") == "test" and r.get("target") == target]
    for k, v in filters.items():
        sub = [r for r in sub if r.get(k) == v]
    return max(sub, key=lambda r: float(r["macro_f1"])) if sub else None


def llm(rows, target, setting):
    sub = [r for r in rows if r["target"] == target and r["setting"] == setting]
    return sub[0] if sub else None


def f(row, key):
    return row.get(key, "") if row else ""


def main():
    summary = json.loads(V3_SUMMARY.read_text(encoding="utf-8"))
    v2b = read_csv(V2B_COMPARISON)
    trad = read_csv(V3_TRAD)
    llm_rows = read_csv(V3_LLM)

    rows = []
    for target in TARGETS:
        prior = next((r for r in v2b if r["target"] == target), {})
        t_claim = best(trad, target, text_view="claim_only")
        t_ce = best(trad, target, text_view="claim_evidence")
        t_ev = best(trad, target, text_view="evidence_only")
        l_ce = llm(llm_rows, target, "claim_evidence")
        l_claim = llm(llm_rows, target, "claim_only")
        l_ev = llm(llm_rows, target, "evidence_only")
        t_delta = float(f(t_ce, "macro_f1") or 0) - float(f(t_claim, "macro_f1") or 0)
        l_delta = float(f(l_ce, "macro_f1") or 0) - float(f(l_claim, "macro_f1") or 0)
        rows.append({
            "target": target,
            "v2b_traditional_claim_only_macro_f1": prior.get("v2b_traditional_claim_only_macro_f1", ""),
            "v3_traditional_claim_only_macro_f1": f(t_claim, "macro_f1"),
            "v3_traditional_claim_evidence_macro_f1": f(t_ce, "macro_f1"),
            "v3_traditional_evidence_only_macro_f1": f(t_ev, "macro_f1"),
            "v3_traditional_ce_minus_claim_only": f"{t_delta:.6f}",
            "v2b_llm_claim_only_macro_f1": prior.get("v2b_llm_claim_only_macro_f1", ""),
            "v3_llm_claim_only_macro_f1": f(l_claim, "macro_f1"),
            "v3_llm_claim_evidence_macro_f1": f(l_ce, "macro_f1"),
            "v3_llm_evidence_only_macro_f1": f(l_ev, "macro_f1"),
            "v3_llm_ce_minus_claim_only": f"{l_delta:.6f}",
        })
    write_csv(OUT_CSV, rows)

    lines = []
    lines.append("# SimClaim v3 final readout")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append("v3 is a real improvement and is now a credible small-sample scaffold. It is not yet a final 600-row expansion recipe, because LLM claim+evidence is still not consistently above claim-only for all targets.")
    lines.append("")
    lines.append("## Fidelity status")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Evidence groups: {summary['n_groups']}")
    lines.append(f"- Label balance: {summary['label_counts']}")
    lines.append(f"- Evidence locked unchanged rate: {summary['evidence_locked_unchanged_rate']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Duplicate claim rows: {summary['duplicate_claim_rows']}")
    lines.append(f"- Generation status: {summary['generation_status_counts']}")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("| target | v2b trad claim-only | v3 trad claim-only | v3 trad claim+evidence | trad CE - claim | v3 LLM claim-only | v3 LLM claim+evidence | LLM CE - claim |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        lines.append(
            f"| {r['target']} | {r['v2b_traditional_claim_only_macro_f1']} | {r['v3_traditional_claim_only_macro_f1']} | "
            f"{r['v3_traditional_claim_evidence_macro_f1']} | {r['v3_traditional_ce_minus_claim_only']} | "
            f"{r['v3_llm_claim_only_macro_f1']} | {r['v3_llm_claim_evidence_macro_f1']} | {r['v3_llm_ce_minus_claim_only']} |"
        )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("Use v3 as the current best pilot dataset. Do not expand directly to 600 yet. The next move is not to rewrite evidence; it is to add a targeted v3b pass for candidate-label and escalation cases where LLM claim-only remains competitive.")
    lines.append("")
    lines.append("## What improved")
    lines.append("")
    lines.append("- Original evidence is preserved and hash-audited.")
    lines.append("- Candidate claim-only leakage is much lower in traditional baselines.")
    lines.append("- Traditional claim+evidence is now better than claim-only for all three targets.")
    lines.append("- LLM issue shows a meaningful gain from evidence.")
    lines.append("")
    lines.append("## Remaining blocker")
    lines.append("")
    lines.append("- LLM escalation gain is nearly zero.")
    lines.append("- LLM 4-class candidate is still slightly better with claim-only than claim+evidence.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- final_metric_csv: `{OUT_CSV}`")
    lines.append("- candidates: `D:\\ocn\\data\\simclaim_hardpair_v3\\candidates\\simclaim_hardpair_v3_268.csv`")
    lines.append("- fidelity_audit: `D:\\ocn\\data\\simclaim_hardpair_v3\\audit\\v3_fidelity_quality_audit.csv`")
    lines.append("- traditional_metrics: `D:\\ocn\\experiments\\simclaim_hardpair_v3_small_baselines\\metrics\\hardpair_v3_small_data_baseline_metrics.csv`")
    lines.append("- llm_metrics: `D:\\ocn\\experiments\\simclaim_hardpair_v3_llm_small_eval\\metrics\\hardpair_v3_llm_small_eval_metrics.csv`")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
