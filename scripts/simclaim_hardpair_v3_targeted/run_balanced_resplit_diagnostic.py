import csv
import importlib.util
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASELINE_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_small_data_baselines.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v3_targeted" / "candidates" / "simclaim_hardpair_v3_targeted_268.csv"

OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v3_targeted_balanced_resplit_seed50"
OUT_SPLITS = OUT_ROOT / "splits_group_stratified"
OUT_AUDIT = OUT_ROOT / "audit"
OUT_ALL_CSV = OUT_SPLITS / "all.csv"
SPLIT_AUDIT_CSV = OUT_AUDIT / "balanced_resplit_seed50_split_audit.csv"

EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v3_targeted_balanced_resplit_seed50_small_baselines"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"

METRICS_CSV = METRIC_DIR / "balanced_resplit_seed50_baseline_metrics.csv"
PER_CLASS_CSV = METRIC_DIR / "balanced_resplit_seed50_per_class_f1.csv"
PRED_CSV = PRED_DIR / "balanced_resplit_seed50_predictions.csv"
SUMMARY_JSON = REPORT_DIR / "balanced_resplit_seed50_summary.json"
REPORT_MD = REPORT_DIR / "balanced_resplit_seed50_report.md"

SEED = 50
TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]
TEXT_VIEWS = ["claim_only", "evidence_only", "claim_evidence"]
SPLIT_GROUP_COUNTS = {"train": 40, "dev": 13, "test": 14}
REPAIRED_GROUP_COUNTS = {"train": 8, "dev": 3, "test": 3}


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
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["hardpair_group_id"]].append(row)
    return groups


def group_is_repaired(items):
    return any(str(r.get("targeted_repair_applied", "")).lower() == "true" for r in items)


def build_assignment(groups):
    rng = random.Random(SEED)
    repaired = [gid for gid, items in groups.items() if group_is_repaired(items)]
    unrepaired = [gid for gid in groups if gid not in repaired]
    repaired.sort()
    unrepaired.sort()
    rng.shuffle(repaired)
    rng.shuffle(unrepaired)

    assignment = {}
    idx = 0
    for split in ["train", "dev", "test"]:
        for gid in repaired[idx:idx + REPAIRED_GROUP_COUNTS[split]]:
            assignment[gid] = split
        idx += REPAIRED_GROUP_COUNTS[split]

    idx = 0
    for split in ["train", "dev", "test"]:
        need = SPLIT_GROUP_COUNTS[split] - REPAIRED_GROUP_COUNTS[split]
        for gid in unrepaired[idx:idx + need]:
            assignment[gid] = split
        idx += need

    if len(assignment) != len(groups):
        missing = sorted(set(groups) - set(assignment))
        extra = sorted(set(assignment) - set(groups))
        raise RuntimeError(f"bad assignment: assigned={len(assignment)} groups={len(groups)} missing={missing} extra={extra}")
    return assignment


def write_splits(rows, assignment, fieldnames):
    out_rows = []
    for row in rows:
        copied = dict(row)
        copied["balanced_resplit_seed"] = str(SEED)
        copied["balanced_resplit_split"] = assignment[row["hardpair_group_id"]]
        out_rows.append(copied)

    for split in ["train", "dev", "test"]:
        part = [r for r in out_rows if r["balanced_resplit_split"] == split]
        write_csv(OUT_SPLITS / f"{split}.csv", part, fieldnames + ["balanced_resplit_seed", "balanced_resplit_split"])
        write_jsonl(OUT_SPLITS / f"{split}.jsonl", part)
    write_csv(OUT_ALL_CSV, out_rows, fieldnames + ["balanced_resplit_seed", "balanced_resplit_split"])
    write_jsonl(OUT_SPLITS / "all.jsonl", out_rows)

    audit_rows = []
    for split in ["train", "dev", "test"]:
        part = [r for r in out_rows if r["balanced_resplit_split"] == split]
        groups = sorted({r["hardpair_group_id"] for r in part})
        repaired_groups = sorted({r["hardpair_group_id"] for r in part if str(r.get("targeted_repair_applied", "")).lower() == "true"})
        audit_rows.append({
            "split": split,
            "n_rows": len(part),
            "n_groups": len(groups),
            "n_repaired_groups": len(repaired_groups),
            "groups": ";".join(groups),
            "repaired_groups": ";".join(repaired_groups),
        })
        for target in TARGETS:
            counts = Counter(r[target] for r in part)
            for label, count in sorted(counts.items()):
                audit_rows.append({
                    "split": split,
                    "target": target,
                    "label": label,
                    "count": count,
                })
    write_csv(SPLIT_AUDIT_CSV, audit_rows)
    return out_rows


def run_baselines(lib):
    train_rows = read_csv(OUT_SPLITS / "train.csv")
    dev_rows = read_csv(OUT_SPLITS / "dev.csv")
    test_rows = read_csv(OUT_SPLITS / "test.csv")
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
                row, pcs, preds = lib.score_run("simclaim_hardpair_v3_targeted_balanced_resplit_seed50", target, split, model, "claim_only", train_rows, eval_rows, y_pred)
                metric_rows.append(row)
                per_class_rows.extend(pcs)
                pred_rows.extend(preds)
            for view in TEXT_VIEWS:
                for model in ["tfidf_centroid", "multinomial_nb"]:
                    if model == "tfidf_centroid":
                        y_pred = lib.tfidf_centroid_predict(train_rows, eval_rows, target, view)
                    else:
                        y_pred = lib.multinomial_nb_predict(train_rows, eval_rows, target, view)
                    row, pcs, preds = lib.score_run("simclaim_hardpair_v3_targeted_balanced_resplit_seed50", target, split, model, view, train_rows, eval_rows, y_pred)
                    metric_rows.append(row)
                    per_class_rows.extend(pcs)
                    pred_rows.extend(preds)
    write_csv(METRICS_CSV, metric_rows)
    write_csv(PER_CLASS_CSV, per_class_rows)
    write_csv(PRED_CSV, pred_rows)
    write_report(metric_rows)


def best(metric_rows, target, predicate):
    rows = [r for r in metric_rows if r["split"] == "test" and r["target"] == target and predicate(r)]
    return max(rows, key=lambda r: float(r["macro_f1"]))


def write_report(metric_rows):
    summary = {
        "dataset": "simclaim_hardpair_v3_targeted_balanced_resplit_seed50",
        "seed": SEED,
        "split_group_counts": SPLIT_GROUP_COUNTS,
        "repaired_group_counts": REPAIRED_GROUP_COUNTS,
        "metrics_csv": str(METRICS_CSV),
        "split_audit_csv": str(SPLIT_AUDIT_CSV),
        "target_results": {},
    }
    lines = [
        "# Balanced resplit diagnostic: targeted repair seed50",
        "",
        "This is a diagnostic split only. It does not modify evidence text or generate new claims.",
        "",
        "| target | claim-only F1 | claim+evidence F1 | CE - claim | gate |",
        "|---|---:|---:|---:|---|",
    ]
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
    lines.extend([
        "",
        f"Overall gate: **{summary['overall_gate']}**",
        "",
        "If this diagnostic passes, the next step is a real v4 generation recipe applied consistently across train/dev/test. If it fails, targeted repair should remain only a diagnostic branch.",
    ])
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    for p in [OUT_SPLITS, OUT_AUDIT, METRIC_DIR, PRED_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)
    rows = read_csv(INPUT_CSV)
    fieldnames = list(rows[0].keys())
    groups = group_rows(rows)
    assignment = build_assignment(groups)
    write_splits(rows, assignment, fieldnames)
    lib = load_lib()
    run_baselines(lib)
    print(json.dumps({
        "status": "ok",
        "input_csv": str(INPUT_CSV),
        "out_all_csv": str(OUT_ALL_CSV),
        "split_audit_csv": str(SPLIT_AUDIT_CSV),
        "metrics_csv": str(METRICS_CSV),
        "report_md": str(REPORT_MD),
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
