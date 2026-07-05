import csv
from pathlib import Path


ROOT = Path(r"D:\ocn")
TRAD = ROOT / "experiments" / "simclaim_detemplate_v1_150_small_baselines" / "metrics" / "small_data_baseline_metrics.csv"
LLM = ROOT / "experiments" / "simclaim_detemplate_v1_150_llm_small_eval" / "metrics" / "llm_small_eval_metrics.csv"
OUT_DIR = ROOT / "reports" / "simclaim_detemplate_v1_150"
OUT_CSV = OUT_DIR / "small_eval_llm_vs_traditional_comparison.csv"
OUT_MD = OUT_DIR / "small_eval_llm_vs_traditional_comparison.md"


TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "candidate_label_guess",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(rows[0].keys()) if rows else []
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def max_macro(rows, **filters):
    sub = []
    for row in rows:
        if all(row.get(k) == v for k, v in filters.items()):
            sub.append(row)
    if not sub:
        return None
    return max(sub, key=lambda r: float(r["macro_f1"]))


def val(row, key):
    return row.get(key, "") if row else ""


def main():
    trad = [r for r in read_csv(TRAD) if r.get("split") == "test"]
    llm = [r for r in read_csv(LLM) if r.get("split") == "test"]
    rows = []
    for target in TARGETS:
        t_best = max_macro([r for r in trad if r["target"] == target])
        t_claim = max_macro([r for r in trad if r["target"] == target and r["text_view"] == "claim_only"])
        t_ev = max_macro([r for r in trad if r["target"] == target and r["text_view"] == "evidence_only"])
        t_ce = max_macro([r for r in trad if r["target"] == target and r["text_view"] == "claim_evidence"])
        t_prefix = max_macro([r for r in trad if r["target"] == target and r["model"] == "prefix_first4_memorize"])
        l_ce = max_macro([r for r in llm if r["target"] == target and r["setting"] == "claim_evidence"])
        l_claim = max_macro([r for r in llm if r["target"] == target and r["setting"] == "claim_only"])
        l_ev = max_macro([r for r in llm if r["target"] == target and r["setting"] == "evidence_only"])
        ce = float(val(l_ce, "macro_f1") or 0)
        lc = float(val(l_claim, "macro_f1") or 0)
        le = float(val(l_ev, "macro_f1") or 0)
        rows.append({
            "target": target,
            "traditional_best_model": val(t_best, "model"),
            "traditional_best_view": val(t_best, "text_view"),
            "traditional_best_macro_f1": val(t_best, "macro_f1"),
            "traditional_claim_only_best_macro_f1": val(t_claim, "macro_f1"),
            "traditional_claim_evidence_best_macro_f1": val(t_ce, "macro_f1"),
            "traditional_evidence_only_best_macro_f1": val(t_ev, "macro_f1"),
            "prefix_first4_macro_f1": val(t_prefix, "macro_f1"),
            "llm_claim_evidence_macro_f1": val(l_ce, "macro_f1"),
            "llm_claim_only_macro_f1": val(l_claim, "macro_f1"),
            "llm_evidence_only_macro_f1": val(l_ev, "macro_f1"),
            "llm_claim_evidence_minus_claim_only": f"{ce - lc:.6f}",
            "llm_claim_evidence_minus_evidence_only": f"{ce - le:.6f}",
        })
    write_csv(OUT_CSV, rows)
    lines = []
    lines.append("# Small eval comparison: LLM vs traditional")
    lines.append("")
    lines.append("| target | trad best | trad best F1 | trad claim-only F1 | trad claim+evidence F1 | prefix F1 | LLM claim+evidence F1 | LLM claim-only F1 | LLM evidence-only F1 | LLM CE - claim-only |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---:|---:|")
    for row in rows:
        lines.append(
            f"| {row['target']} | {row['traditional_best_model']} / {row['traditional_best_view']} | "
            f"{row['traditional_best_macro_f1']} | {row['traditional_claim_only_best_macro_f1']} | "
            f"{row['traditional_claim_evidence_best_macro_f1']} | {row['prefix_first4_macro_f1']} | "
            f"{row['llm_claim_evidence_macro_f1']} | {row['llm_claim_only_macro_f1']} | "
            f"{row['llm_evidence_only_macro_f1']} | {row['llm_claim_evidence_minus_claim_only']} |"
        )
    lines.append("")
    lines.append("Reading: prefix-only is now low, so old template-prefix leakage is mostly fixed. The remaining weakness is that claim-only remains strong, so the next data version should create harder minimal pairs where label cannot be inferred from claim style alone.")
    OUT_MD.write_text("\n".join(lines), encoding="utf-8")
    print(OUT_MD)


if __name__ == "__main__":
    main()
