import csv
from pathlib import Path


ROOT = Path(r"D:\ocn")
OUT_DIR = ROOT / "reports" / "simclaim_hardpair_v2b"
OUT_CSV = OUT_DIR / "small_data_iteration_comparison.csv"
OUT_MD = OUT_DIR / "final_small_data_readout.md"

V1_COMP = ROOT / "reports" / "simclaim_detemplate_v1_150" / "small_eval_llm_vs_traditional_comparison.csv"
V2_TRAD = ROOT / "experiments" / "simclaim_hardpair_v2_small_baselines" / "metrics" / "hardpair_v2_small_data_baseline_metrics.csv"
V2B_TRAD = ROOT / "experiments" / "simclaim_hardpair_v2b_small_baselines" / "metrics" / "hardpair_v2b_small_data_baseline_metrics.csv"
V2B_LLM = ROOT / "experiments" / "simclaim_hardpair_v2b_llm_small_eval" / "metrics" / "hardpair_v2b_llm_small_eval_metrics.csv"
V2B_SUMMARY = ROOT / "reports" / "simclaim_hardpair_v2b" / "hardpair_v2b_summary.json"

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


def best_macro(rows, target, **filters):
    sub = [r for r in rows if r.get("split") == "test" and r.get("target") == target]
    for key, value in filters.items():
        sub = [r for r in sub if r.get(key) == value]
    if not sub:
        return None
    return max(sub, key=lambda r: float(r["macro_f1"]))


def get_llm(rows, target, setting):
    sub = [r for r in rows if r["target"] == target and r["setting"] == setting]
    return sub[0] if sub else None


def main():
    v1 = read_csv(V1_COMP)
    v2 = read_csv(V2_TRAD)
    v2b = read_csv(V2B_TRAD)
    llm = read_csv(V2B_LLM)

    rows = []
    for target in TARGETS:
        v1_row = next((r for r in v1 if r["target"] == target), {})
        v2_claim = best_macro(v2, target, text_view="claim_only")
        v2b_claim = best_macro(v2b, target, text_view="claim_only")
        v2b_ce = best_macro(v2b, target, text_view="claim_evidence")
        v2b_ev = best_macro(v2b, target, text_view="evidence_only")
        l_ce = get_llm(llm, target, "claim_evidence")
        l_claim = get_llm(llm, target, "claim_only")
        l_ev = get_llm(llm, target, "evidence_only")
        rows.append({
            "target": target,
            "v1_traditional_claim_only_macro_f1": v1_row.get("traditional_claim_only_best_macro_f1", ""),
            "v2_traditional_claim_only_macro_f1": v2_claim["macro_f1"] if v2_claim else "",
            "v2b_traditional_claim_only_macro_f1": v2b_claim["macro_f1"] if v2b_claim else "",
            "v2b_traditional_claim_evidence_macro_f1": v2b_ce["macro_f1"] if v2b_ce else "",
            "v2b_traditional_evidence_only_macro_f1": v2b_ev["macro_f1"] if v2b_ev else "",
            "v2b_llm_claim_evidence_macro_f1": l_ce["macro_f1"] if l_ce else "",
            "v2b_llm_claim_only_macro_f1": l_claim["macro_f1"] if l_claim else "",
            "v2b_llm_evidence_only_macro_f1": l_ev["macro_f1"] if l_ev else "",
            "v2b_llm_ce_minus_claim_only": f"{float(l_ce['macro_f1']) - float(l_claim['macro_f1']):.6f}" if l_ce and l_claim else "",
        })
    write_csv(OUT_CSV, rows)

    lines = []
    lines.append("# Final small-data readout: v1 → v2 → v2b")
    lines.append("")
    lines.append("## Bottom line")
    lines.append("")
    lines.append("The scaffold is now usable for pipeline validation, but it is not yet strong enough for a top-tier final experiment. The remaining blocker is claim-only leakage, especially for escalation.")
    lines.append("")
    lines.append("## What passed")
    lines.append("")
    lines.append("- Data pipeline runs end-to-end.")
    lines.append("- Hard-pair v2b has 268 rows from 67 evidence groups.")
    lines.append("- Four labels are exactly balanced: 67 each.")
    lines.append("- Source trace completeness is 100%.")
    lines.append("- Duplicate claims are 0.")
    lines.append("- Prefix-only leakage is low for 4-class candidate labels.")
    lines.append("")
    lines.append("## What did not pass yet")
    lines.append("")
    lines.append("- LLM claim+evidence is not clearly better than LLM claim-only.")
    lines.append("- Traditional claim-only remains high for escalation.")
    lines.append("- Therefore the dataset still allows too much inference from claim wording alone.")
    lines.append("")
    lines.append("## Metrics")
    lines.append("")
    lines.append("| target | v1 trad claim-only | v2 trad claim-only | v2b trad claim-only | v2b trad claim+evidence | v2b LLM claim+evidence | v2b LLM claim-only | LLM CE - claim-only |")
    lines.append("|---|---:|---:|---:|---:|---:|---:|---:|")
    for r in rows:
        lines.append(
            f"| {r['target']} | {r['v1_traditional_claim_only_macro_f1']} | {r['v2_traditional_claim_only_macro_f1']} | "
            f"{r['v2b_traditional_claim_only_macro_f1']} | {r['v2b_traditional_claim_evidence_macro_f1']} | "
            f"{r['v2b_llm_claim_evidence_macro_f1']} | {r['v2b_llm_claim_only_macro_f1']} | {r['v2b_llm_ce_minus_claim_only']} |"
        )
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("Do not expand this exact generation strategy to 600 yet. Use v2b as the working scaffold, then make v3 with escalation-specific counterfactual decoys.")
    lines.append("")
    lines.append("## Concrete next step")
    lines.append("")
    lines.append("Create v3 where each evidence group includes supported and contradiction claims that deliberately share the same scope/action vocabulary as mild/strong claims, while mild/strong claims use more subtle wording. The explicit target is:")
    lines.append("")
    lines.append("- traditional claim-only macro-F1 <= 0.65 for escalation and candidate labels;")
    lines.append("- LLM claim+evidence macro-F1 at least 0.05 above LLM claim-only;")
    lines.append("- evidence-only near chance;")
    lines.append("- source trace still 100%;")
    lines.append("- no gold/human-audited flags.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    lines.append(f"- comparison_csv: `{OUT_CSV}`")
    lines.append("- v2b_candidates: `D:\\ocn\\data\\simclaim_hardpair_v2b\\candidates\\simclaim_hardpair_v2b_268.csv`")
    lines.append("- v2b_traditional_metrics: `D:\\ocn\\experiments\\simclaim_hardpair_v2b_small_baselines\\metrics\\hardpair_v2b_small_data_baseline_metrics.csv`")
    lines.append("- v2b_llm_metrics: `D:\\ocn\\experiments\\simclaim_hardpair_v2b_llm_small_eval\\metrics\\hardpair_v2b_llm_small_eval_metrics.csv`")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
