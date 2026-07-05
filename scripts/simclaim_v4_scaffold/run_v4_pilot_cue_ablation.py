import csv
import importlib.util
import json
import re
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASELINE_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_small_data_baselines.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v4_pilot" / "candidates" / "simclaim_hardpair_v4_pilot_candidates.csv"

OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v4_pilot_cue_ablation"
OUT_CANDIDATES = OUT_ROOT / "candidates" / "simclaim_hardpair_v4_pilot_cue_ablation_candidates.csv"
OUT_AUDIT = OUT_ROOT / "audit" / "cue_ablation_audit.csv"

EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v4_pilot_cue_ablation_small_baselines"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"
METRICS_CSV = METRIC_DIR / "cue_ablation_baseline_metrics.csv"
PER_CLASS_CSV = METRIC_DIR / "cue_ablation_per_class_f1.csv"
PRED_CSV = PRED_DIR / "cue_ablation_predictions.csv"
SUMMARY_JSON = REPORT_DIR / "cue_ablation_summary.json"
REPORT_MD = REPORT_DIR / "cue_ablation_report.md"

TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]
TEXT_VIEWS = ["claim_only", "evidence_only", "claim_evidence"]

HIGH_RISK_TERMS = [
    "across",
    "generally",
    "varied",
    "diverse",
    "operational",
    "general",
    "guide",
    "guides",
    "guiding",
    "establish",
    "establishes",
    "established",
    "establishing",
    "making",
    "practical",
    "routine",
    "central",
    "without",
    "only",
    "excluding",
    "fewer",
    "less",
    "not",
    "therefore",
    "need",
    "needs",
    "should",
    "must",
    "policy",
    "deployment",
    "recommend",
    "recommended",
    "production",
    "sufficient",
]


def load_lib():
    spec = importlib.util.spec_from_file_location("baseline_lib", BASELINE_LIB)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
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


def normalize_space(text):
    return re.sub(r"\s+", " ", str(text or "")).strip()


def mask_cues(text):
    original = str(text or "")
    out = original
    hits = []
    for term in sorted(HIGH_RISK_TERMS, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(term)}\b", flags=re.IGNORECASE)
        if pattern.search(out):
            hits.append(term)
            out = pattern.sub("", out)
    out = normalize_space(out)
    out = re.sub(r"\s+,", ",", out)
    out = re.sub(r"\s+\.", ".", out)
    out = re.sub(r",\s*,", ",", out)
    out = re.sub(r"\s+and\s+\.", ".", out)
    out = normalize_space(out)
    return out, sorted(set(hits))


def materialize_ablation():
    rows = [r for r in read_csv(INPUT_CSV) if r.get("claim_generation_status") == "success"]
    out_rows = []
    audit = []
    for row in rows:
        copied = dict(row)
        masked, hits = mask_cues(row.get("claim_text", ""))
        copied["claim_text_original_before_cue_ablation"] = row.get("claim_text", "")
        copied["claim_text"] = masked
        copied["cue_ablation_applied"] = "true" if hits else "false"
        copied["cue_ablation_terms"] = ";".join(hits)
        copied["cue_ablation_policy"] = "diagnostic_only_not_final_dataset"
        out_rows.append(copied)
        audit.append({
            "candidate_id": row.get("candidate_id", ""),
            "v4_group_id": row.get("v4_group_id", ""),
            "candidate_label_guess": row.get("candidate_label_guess", ""),
            "terms_removed": ";".join(hits),
            "n_terms_removed": len(hits),
            "original_claim_text": row.get("claim_text", ""),
            "ablated_claim_text": masked,
            "evidence_unchanged": str(row.get("evidence_text", "") == copied.get("evidence_text", "")).lower(),
        })
    write_csv(OUT_CANDIDATES, out_rows)
    write_csv(OUT_AUDIT, audit)
    return out_rows, audit


def best(rows, target, predicate):
    sub = [r for r in rows if r["split"] == "test" and r["target"] == target and predicate(r)]
    return max(sub, key=lambda r: float(r["macro_f1"]))


def run_baselines(rows):
    for p in [METRIC_DIR, PRED_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    train_rows = [r for r in rows if r.get("split") == "train"]
    dev_rows = [r for r in rows if r.get("split") == "dev"]
    test_rows = [r for r in rows if r.get("split") == "test"]
    lib = load_lib()
    eval_sets = {"dev": dev_rows, "test": test_rows}
    metric_rows, per_class_rows, pred_rows = [], [], []
    for target in TARGETS:
        for split, eval_rows in eval_sets.items():
            for model in ["majority", "claim_length_median_rule", "prefix_first4_memorize"]:
                if model == "majority":
                    y_pred = lib.majority_predict(train_rows, eval_rows, target)
                elif model == "claim_length_median_rule":
                    y_pred = lib.length_threshold_predict(train_rows, eval_rows, target)
                else:
                    y_pred = lib.prefix_memorize_predict(train_rows, eval_rows, target, n=4)
                row, pcs, preds = lib.score_run("simclaim_hardpair_v4_pilot_cue_ablation", target, split, model, "claim_only", train_rows, eval_rows, y_pred)
                metric_rows.append(row); per_class_rows.extend(pcs); pred_rows.extend(preds)
            for view in TEXT_VIEWS:
                for model in ["tfidf_centroid", "multinomial_nb"]:
                    if model == "tfidf_centroid":
                        y_pred = lib.tfidf_centroid_predict(train_rows, eval_rows, target, view)
                    else:
                        y_pred = lib.multinomial_nb_predict(train_rows, eval_rows, target, view)
                    row, pcs, preds = lib.score_run("simclaim_hardpair_v4_pilot_cue_ablation", target, split, model, view, train_rows, eval_rows, y_pred)
                    metric_rows.append(row); per_class_rows.extend(pcs); pred_rows.extend(preds)
    write_csv(METRICS_CSV, metric_rows)
    write_csv(PER_CLASS_CSV, per_class_rows)
    write_csv(PRED_CSV, pred_rows)
    write_report(metric_rows, rows, train_rows, dev_rows, test_rows)


def write_report(metric_rows, rows, train_rows, dev_rows, test_rows):
    lines = [
        "# v4 pilot cue-ablation diagnostic baseline",
        "",
        "This is a diagnostic dataset only. It removes known claim-only leakage cues from generated claims and preserves locked evidence text.",
        "",
        f"- Rows: {len(rows)}",
        f"- Groups: {len({r['v4_group_id'] for r in rows})}",
        f"- Split rows: train={len(train_rows)}, dev={len(dev_rows)}, test={len(test_rows)}",
        "",
        "| target | claim-only F1 | claim+evidence F1 | CE - claim | gate |",
        "|---|---:|---:|---:|---|",
    ]
    summary = {
        "dataset": "simclaim_hardpair_v4_pilot_cue_ablation",
        "n_rows": len(rows),
        "n_groups": len({r["v4_group_id"] for r in rows}),
        "target_results": {},
    }
    all_pass = True
    for target in TARGETS:
        claim = best(metric_rows, target, lambda r: r["text_view"] == "claim_only")
        ce = best(metric_rows, target, lambda r: r["text_view"] == "claim_evidence")
        delta = float(ce["macro_f1"]) - float(claim["macro_f1"])
        gate = "pass" if delta > 0 else "fail"
        all_pass = all_pass and delta > 0
        summary["target_results"][target] = {
            "claim_only_best": claim,
            "claim_evidence_best": ce,
            "delta_ce_minus_claim": round(delta, 6),
            "gate": gate,
        }
        lines.append(f"| {target} | {claim['macro_f1']} | {ce['macro_f1']} | {delta:.6f} | {gate} |")
    summary["overall_gate"] = "pass" if all_pass else "fail"
    summary["metrics_csv"] = str(METRICS_CSV)
    summary["report_md"] = str(REPORT_MD)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    lines.extend(["", f"Overall gate: **{summary['overall_gate']}**"])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows, audit = materialize_ablation()
    run_baselines(rows)
    print(json.dumps({
        "status": "ok",
        "rows": len(rows),
        "groups": len({r["v4_group_id"] for r in rows}),
        "rows_with_cues_removed": sum(1 for r in rows if r.get("cue_ablation_applied") == "true"),
        "candidates_csv": str(OUT_CANDIDATES),
        "audit_csv": str(OUT_AUDIT),
        "metrics_csv": str(METRICS_CSV),
        "report_md": str(REPORT_MD),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
