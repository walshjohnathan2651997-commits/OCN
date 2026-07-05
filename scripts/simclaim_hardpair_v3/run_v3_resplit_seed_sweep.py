import csv
import importlib.util
import json
import random
from collections import defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASELINE_LIB = ROOT / "scripts" / "simclaim_detemplate_v1_150" / "run_small_data_baselines.py"
INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v3" / "candidates" / "simclaim_hardpair_v3_268.csv"

EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v3_resplit_sweep"
METRIC_DIR = EXP_ROOT / "metrics"
REPORT_DIR = EXP_ROOT / "reports"
SWEEP_CSV = METRIC_DIR / "v3_resplit_seed_sweep.csv"
SUMMARY_JSON = REPORT_DIR / "v3_resplit_seed_sweep_summary.json"
REPORT_MD = REPORT_DIR / "v3_resplit_seed_sweep_report.md"

TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]
SPLIT_GROUP_COUNTS = {"train": 40, "dev": 13, "test": 14}
SEEDS = list(range(1, 101))


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


def group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        groups[row["hardpair_group_id"]].append(row)
    return groups


def assign_groups(groups, seed):
    rng = random.Random(seed)
    gids = sorted(groups)
    rng.shuffle(gids)
    assignment = {}
    idx = 0
    for split in ["train", "dev", "test"]:
        for gid in gids[idx:idx + SPLIT_GROUP_COUNTS[split]]:
            assignment[gid] = split
        idx += SPLIT_GROUP_COUNTS[split]
    return assignment


def split_rows(rows, assignment):
    out = {"train": [], "dev": [], "test": []}
    for row in rows:
        out[assignment[row["hardpair_group_id"]]].append(row)
    return out


def best_claim_only(lib, train_rows, test_rows, target):
    runs = []
    for model in ["majority", "claim_length_median_rule", "prefix_first4_memorize"]:
        if model == "majority":
            y_pred = lib.majority_predict(train_rows, test_rows, target)
        elif model == "claim_length_median_rule":
            y_pred = lib.length_threshold_predict(train_rows, test_rows, target)
        else:
            y_pred = lib.prefix_memorize_predict(train_rows, test_rows, target, n=4)
        row, _, _ = lib.score_run("v3_resplit_sweep", target, "test", model, "claim_only", train_rows, test_rows, y_pred)
        runs.append(row)
    for model in ["tfidf_centroid", "multinomial_nb"]:
        if model == "tfidf_centroid":
            y_pred = lib.tfidf_centroid_predict(train_rows, test_rows, target, "claim_only")
        else:
            y_pred = lib.multinomial_nb_predict(train_rows, test_rows, target, "claim_only")
        row, _, _ = lib.score_run("v3_resplit_sweep", target, "test", model, "claim_only", train_rows, test_rows, y_pred)
        runs.append(row)
    return max(runs, key=lambda r: float(r["macro_f1"]))


def best_claim_evidence(lib, train_rows, test_rows, target):
    runs = []
    for model in ["tfidf_centroid", "multinomial_nb"]:
        if model == "tfidf_centroid":
            y_pred = lib.tfidf_centroid_predict(train_rows, test_rows, target, "claim_evidence")
        else:
            y_pred = lib.multinomial_nb_predict(train_rows, test_rows, target, "claim_evidence")
        row, _, _ = lib.score_run("v3_resplit_sweep", target, "test", model, "claim_evidence", train_rows, test_rows, y_pred)
        runs.append(row)
    return max(runs, key=lambda r: float(r["macro_f1"]))


def summarize(rows):
    by_target = defaultdict(list)
    by_seed = defaultdict(list)
    for row in rows:
        by_target[row["target"]].append(row)
        by_seed[row["seed"]].append(row)
    target_summaries = {}
    for target, items in by_target.items():
        deltas = [float(r["delta_ce_minus_claim"]) for r in items]
        passes = [d > 0 for d in deltas]
        target_summaries[target] = {
            "n_seeds": len(items),
            "pass_rate": round(sum(passes) / len(passes), 4),
            "mean_delta": round(sum(deltas) / len(deltas), 6),
            "min_delta": round(min(deltas), 6),
            "max_delta": round(max(deltas), 6),
        }
    all_pass = 0
    for items in by_seed.values():
        if all(float(r["delta_ce_minus_claim"]) > 0 for r in items):
            all_pass += 1
    return {
        "dataset": "simclaim_hardpair_v3_268",
        "diagnostic": "v3 random group-resplit seed sweep; no text generation; no LLM evaluation",
        "n_seeds": len(by_seed),
        "all_three_targets_pass_rate": round(all_pass / len(by_seed), 4),
        "target_summaries": target_summaries,
        "sweep_csv": str(SWEEP_CSV),
    }


def write_report(summary):
    lines = [
        "# v3 random group-resplit seed sweep",
        "",
        "This is a diagnostic only. It changes only train/dev/test grouping in memory and does not modify evidence or generate new claims.",
        "",
        f"Seeds tested: {summary['n_seeds']}",
        f"All-three-target pass rate: {summary['all_three_targets_pass_rate']:.2%}",
        "",
        "| target | pass rate | mean CE-claim delta | min delta | max delta |",
        "|---|---:|---:|---:|---:|",
    ]
    for target in TARGETS:
        s = summary["target_summaries"][target]
        lines.append(f"| {target} | {s['pass_rate']:.2%} | {s['mean_delta']:.6f} | {s['min_delta']:.6f} | {s['max_delta']:.6f} |")
    lines.extend([
        "",
        "Interpretation:",
        "",
        "- This estimates whether v3's evidence gain is robust to group-level split changes.",
        "- It should not be used to choose a lucky split for the paper.",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    METRIC_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    rows = read_csv(INPUT_CSV)
    groups = group_rows(rows)
    lib = load_lib()
    out_rows = []
    for seed in SEEDS:
        assignment = assign_groups(groups, seed)
        split = split_rows(rows, assignment)
        train_rows = split["train"]
        test_rows = split["test"]
        for target in TARGETS:
            claim = best_claim_only(lib, train_rows, test_rows, target)
            ce = best_claim_evidence(lib, train_rows, test_rows, target)
            delta = float(ce["macro_f1"]) - float(claim["macro_f1"])
            out_rows.append({
                "seed": seed,
                "target": target,
                "claim_only_best_model": claim["model"],
                "claim_only_macro_f1": claim["macro_f1"],
                "claim_evidence_best_model": ce["model"],
                "claim_evidence_macro_f1": ce["macro_f1"],
                "delta_ce_minus_claim": f"{delta:.6f}",
                "gate": "pass" if delta > 0 else "fail",
            })
    write_csv(SWEEP_CSV, out_rows)
    summary = summarize(out_rows)
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary)
    print(json.dumps({
        "status": "ok",
        "sweep_csv": str(SWEEP_CSV),
        "summary_json": str(SUMMARY_JSON),
        "report_md": str(REPORT_MD),
        "all_three_targets_pass_rate": summary["all_three_targets_pass_rate"],
        "target_summaries": summary["target_summaries"],
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
