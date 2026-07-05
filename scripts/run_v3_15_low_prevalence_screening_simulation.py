"""V3.15 Low-Prevalence Screening Simulation + Natural Distribution Stress Test.

Simulates realistic scientific writing distribution where strong_action_overclaim
is rare. Uses existing R4/LLM predictions on matched-100 samples. No gold, no API,
no new model training, no threshold retuning, no original data modification.

Outputs:
  - low_prevalence_sample_manifest.csv  (simulation_id, prevalence, sample_id, ...)
  - low_prevalence_screening_metrics.csv (per method × prevalence summary)
  - low_prevalence_screening_summary.json (aggregate summary)
  - review_budget_curve.csv (review budget sweep)
"""
import csv
import json
import os
import random
from collections import Counter, defaultdict
from statistics import mean, median

import pandas as pd

# Configuration
INPUT_CSV = r"D:\ocn\experiments\gpt_structured_judge_probe_v1\gpt_vs_r4_deepseek_comparison.csv"
OUT_DIR = r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation"
MANIFEST_CSV = os.path.join(OUT_DIR, "low_prevalence_sample_manifest.csv")
METRICS_CSV = os.path.join(OUT_DIR, "low_prevalence_screening_metrics.csv")
SUMMARY_JSON = os.path.join(OUT_DIR, "low_prevalence_screening_summary.json")
BUDGET_CSV = os.path.join(OUT_DIR, "review_budget_curve.csv")

PREVALENCES = [0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25]
N_BOOTSTRAP = 1000
SIM_N = 1000  # simulated population size per bootstrap (large enough for 1% prevalence)
NONSTRONG_RATIOS = {"supported": 0.80, "mild_scope_overclaim": 0.15, "contradiction_candidate": 0.05}
RANDOM_SEED = 20260705

# Review budget sweep (fractions of total population to review)
REVIEW_BUDGETS = [0.01, 0.03, 0.05, 0.10, 0.20, 0.30, 0.40, 0.50]

METHODS = ["r4", "gpt_standard", "gpt_structured", "deepseek"]
METHOD_LABEL_COLS = {
    "r4": "r4_label",
    "gpt_standard": "gpt_standard_label",
    "gpt_structured": "gpt_structured_label",
    "deepseek": "deepseek_label",
}

STRONG = "strong_action_overclaim"


def load_base_data():
    df = pd.read_csv(INPUT_CSV, keep_default_na=False)
    # Verify columns
    required = ["sample_id", "candidate_id", "label_4_silver"] + list(METHOD_LABEL_COLS.values())
    for col in required:
        if col not in df.columns:
            raise ValueError(f"Missing column: {col}")
    return df


def build_class_pools(df):
    """Build per-silver-label pools of rows (with their method predictions)."""
    pools = {}
    for label in ["supported", "mild_scope_overclaim", STRONG, "contradiction_candidate"]:
        sub = df[df["label_4_silver"] == label]
        pools[label] = sub.to_dict("records")
    return pools


def sample_composition(prevalence, n_total):
    """Determine number of each class given prevalence of strong_action."""
    n_strong = max(1, round(n_total * prevalence))  # at least 1 strong
    n_nonstrong = n_total - n_strong
    n_supported = round(n_nonstrong * NONSTRONG_RATIOS["supported"])
    n_mild = round(n_nonstrong * NONSTRONG_RATIOS["mild_scope_overclaim"])
    n_contradiction = n_nonstrong - n_supported - n_mild
    # Guard against negatives from rounding
    if n_contradiction < 0:
        n_supported += n_contradiction
        n_contradiction = 0
    return {
        STRONG: n_strong,
        "supported": n_supported,
        "mild_scope_overclaim": n_mild,
        "contradiction_candidate": n_contradiction,
    }


def draw_bootstrap_sample(pools, composition, rng):
    """Draw one bootstrap sample by sampling with replacement from each class pool."""
    sample = []
    for label, n in composition.items():
        pool = pools[label]
        if not pool:
            continue
        for _ in range(n):
            sample.append(rng.choice(pool))
    return sample


def compute_screening_metrics(sample, method):
    """Compute screening metrics for a method on a sample."""
    label_col = METHOD_LABEL_COLS[method]
    tp = fp = fn = tn = 0
    llm_missed_strong_captured_by_r4 = 0
    strong_cases_missed_by_all = 0
    for row in sample:
        silver = row["label_4_silver"]
        pred = row[label_col]
        if silver == STRONG:
            if pred == STRONG:
                tp += 1
            else:
                fn += 1
        else:
            if pred == STRONG:
                fp += 1
            else:
                tn += 1
    # LLM-missed strong captured by R4: only meaningful when method != r4
    # We compute separately for r4 capture of LLM misses in aggregate function
    recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    fp_tp = (fp / tp) if tp > 0 else float("inf")
    review_burden = (tp + fp) / len(sample) if sample else 0.0
    nnr = (tp + fp) / tp if tp > 0 else float("inf")  # number needed to review per true strong
    accuracy = (tp + tn) / len(sample) if sample else 0.0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "tn": tn,
        "recall": recall,
        "precision": precision,
        "positive_f1": f1,
        "fp_tp_ratio": fp_tp,
        "review_burden": review_burden,
        "number_needed_to_review_per_true_strong": nnr,
        "accuracy": accuracy,
    }


def compute_llm_missed_captured_by_r4(sample):
    """For each strong case, check if all 3 LLM methods missed it but R4 caught it."""
    llm_methods = ["gpt_standard", "gpt_structured", "deepseek"]
    captured = 0
    missed_by_all = 0
    for row in sample:
        if row["label_4_silver"] != STRONG:
            continue
        llm_all_missed = all(row[METHOD_LABEL_COLS[m]] != STRONG for m in llm_methods)
        r4_caught = row["r4_label"] == STRONG
        if llm_all_missed and r4_caught:
            captured += 1
        if llm_all_missed and not r4_caught:
            missed_by_all += 1
    return captured, missed_by_all


def aggregate_metrics(boot_metrics_list):
    """Aggregate a list of per-bootstrap metric dicts into mean/median/CI."""
    agg = {}
    keys_to_agg = ["tp", "fp", "fn", "tn", "recall", "precision", "positive_f1",
                   "fp_tp_ratio", "review_burden", "number_needed_to_review_per_true_strong",
                   "accuracy"]
    for key in keys_to_agg:
        vals = [m[key] for m in boot_metrics_list]
        vals_sorted = sorted(vals)
        # Remove inf for mean computation
        finite_vals = [v for v in vals if v != float("inf")]
        agg[key + "_mean"] = mean(finite_vals) if finite_vals else float("inf")
        agg[key + "_median"] = median(finite_vals) if finite_vals else float("inf")
        # 95% CI via percentile
        if finite_vals:
            n = len(finite_vals)
            lo_idx = int(0.025 * n)
            hi_idx = int(0.975 * n)
            agg[key + "_ci_lo"] = finite_vals[lo_idx]
            agg[key + "_ci_hi"] = finite_vals[min(hi_idx, n - 1)]
        else:
            agg[key + "_ci_lo"] = float("inf")
            agg[key + "_ci_hi"] = float("inf")
    return agg


def write_manifest(manifest_rows):
    """Write the manifest CSV (one row per sample × simulation)."""
    fields = ["simulation_id", "prevalence", "bootstrap_iter", "sample_id", "candidate_id",
              "silver_label", "r4_label", "gpt_standard_label", "gpt_structured_label",
              "deepseek_label", "included_as_strong", "included_as_nonstrong"]
    # Manifest is huge (7 prev × 1000 boot × 1000 sample = 7M rows); write per-simulation summary instead
    # Actually, write per-simulation aggregated manifest (7 prev × 1000 = 7000 rows with composition)
    manifest_summary_fields = ["simulation_id", "prevalence", "bootstrap_iter",
                               "n_strong", "n_supported", "n_mild", "n_contradiction", "n_total"]
    with open(MANIFEST_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=manifest_summary_fields)
        w.writeheader()
        for row in manifest_rows:
            w.writerow(row)


def write_metrics_csv(metrics_rows):
    """Write per-method × prevalence metrics CSV."""
    if not metrics_rows:
        return
    # Use union of all keys, with method and prevalence first
    all_keys = set()
    for row in metrics_rows:
        all_keys.update(row.keys())
    # Ordered: method, prevalence, then key metrics, then the rest
    priority_keys = ["method", "prevalence",
                     "tp_mean", "fp_mean", "fn_mean", "tn_mean",
                     "recall_mean", "recall_ci_lo", "recall_ci_hi",
                     "precision_mean", "precision_ci_lo", "precision_ci_hi",
                     "positive_f1_mean", "positive_f1_ci_lo", "positive_f1_ci_hi",
                     "fp_tp_ratio_mean", "fp_tp_ratio_median", "fp_tp_ratio_ci_lo", "fp_tp_ratio_ci_hi",
                     "review_burden_mean", "review_burden_ci_lo", "review_burden_ci_hi",
                     "number_needed_to_review_per_true_strong_mean",
                     "number_needed_to_review_per_true_strong_median",
                     "number_needed_to_review_per_true_strong_ci_lo",
                     "number_needed_to_review_per_true_strong_ci_hi",
                     "accuracy_mean", "accuracy_ci_lo", "accuracy_ci_hi",
                     "llm_missed_strong_captured_by_r4_mean",
                     "strong_cases_missed_by_all_methods_mean"]
    fields = [k for k in priority_keys if k in all_keys]
    # Append remaining keys
    for k in sorted(all_keys):
        if k not in fields:
            fields.append(k)
    with open(METRICS_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        w.writeheader()
        for row in metrics_rows:
            w.writerow(row)


def compute_review_budget_curve(pools, prevalences, budgets, rng_seed=RANDOM_SEED):
    """Compute review budget curve: at each review budget, what recall/precision do we get?

    Uses discrete-priority ordering for R4 (predicted strong > contradiction > mild > supported)
    and for LLMs (predicted strong > contradiction > mild > supported).
    This is a discrete-priority approximation since we don't have continuous scores.
    """
    rng = random.Random(rng_seed)
    results = []
    priority_order = {
        STRONG: 0,
        "contradiction_candidate": 1,
        "mild_scope_overclaim": 2,
        "supported": 3,
    }
    n_budget_boot = 200  # fewer bootstraps for budget curve (computationally heavier)
    for prev in prevalences:
        composition = sample_composition(prev, SIM_N)
        for boot in range(n_budget_boot):
            sample = draw_bootstrap_sample(pools, composition, rng)
            n_total = len(sample)
            n_true_strong = sum(1 for r in sample if r["label_4_silver"] == STRONG)
            for method in METHODS:
                label_col = METHOD_LABEL_COLS[method]
                # Sort sample by priority (predicted strong first, then contradiction, etc.)
                sorted_sample = sorted(sample, key=lambda r: priority_order.get(r[label_col], 99))
                for budget in budgets:
                    n_review = max(1, round(n_total * budget))
                    reviewed = sorted_sample[:n_review]
                    tp = sum(1 for r in reviewed if r["label_4_silver"] == STRONG and r[label_col] == STRONG)
                    # Actually for screening, "captured" means: among reviewed (top-n by priority),
                    # how many true strong did we find? This is recall_at_budget = tp / n_true_strong
                    # But "predicted strong" reviewed = those we flagged for review
                    # In discrete-priority: we review top-n by predicted priority
                    # tp = true strong in reviewed set
                    tp_in_reviewed = sum(1 for r in reviewed if r["label_4_silver"] == STRONG)
                    fp_in_reviewed = sum(1 for r in reviewed if r["label_4_silver"] != STRONG)
                    recall_at_budget = tp_in_reviewed / n_true_strong if n_true_strong > 0 else 0.0
                    precision_at_budget = tp_in_reviewed / n_review if n_review > 0 else 0.0
                    fp_tp_at_budget = (fp_in_reviewed / tp_in_reviewed) if tp_in_reviewed > 0 else float("inf")
                    results.append({
                        "method": method,
                        "prevalence": prev,
                        "review_budget": budget,
                        "bootstrap_iter": boot,
                        "n_reviewed": n_review,
                        "n_true_strong": n_true_strong,
                        "strong_recall_at_budget": recall_at_budget,
                        "precision_at_budget": precision_at_budget,
                        "fp_tp_at_budget": fp_tp_at_budget,
                        "tp_in_reviewed": tp_in_reviewed,
                        "fp_in_reviewed": fp_in_reviewed,
                    })
    return results


def aggregate_budget_curve(budget_results):
    """Aggregate budget results across bootstraps."""
    agg = defaultdict(list)
    for r in budget_results:
        key = (r["method"], r["prevalence"], r["review_budget"])
        agg[key].append(r)
    rows = []
    for (method, prev, budget), items in agg.items():
        recalls = [it["strong_recall_at_budget"] for it in items]
        precisions = [it["precision_at_budget"] for it in items]
        fp_tps = [it["fp_tp_at_budget"] for it in items if it["fp_tp_at_budget"] != float("inf")]
        rows.append({
            "method": method,
            "prevalence": prev,
            "review_budget": budget,
            "n_reviewed_median": median([it["n_reviewed"] for it in items]),
            "strong_recall_at_budget_mean": mean(recalls),
            "strong_recall_at_budget_ci_lo": sorted(recalls)[int(0.025 * len(recalls))],
            "strong_recall_at_budget_ci_hi": sorted(recalls)[int(0.975 * len(recalls))],
            "precision_at_budget_mean": mean(precisions),
            "fp_tp_at_budget_mean": mean(fp_tps) if fp_tps else float("inf"),
            "notes": "discrete-priority approximation (predicted strong > contradiction > mild > supported)",
        })
    return rows


def main():
    print("Loading base data...")
    df = load_base_data()
    print(f"Loaded {len(df)} matched samples")
    print(f"Silver distribution: {Counter(df['label_4_silver'])}")

    pools = build_class_pools(df)
    print(f"Class pool sizes: { {k: len(v) for k, v in pools.items()} }")

    rng = random.Random(RANDOM_SEED)

    # Phase 1: Build manifest + compute metrics
    print("\nPhase 1: Building low-prevalence simulations...")
    manifest_rows = []
    metrics_rows = []
    summary = {
        "simulation_config": {
            "n_bootstrap": N_BOOTSTRAP,
            "sim_n": SIM_N,
            "prevalences": PREVALENCES,
            "nonstrong_ratios": NONSTRONG_RATIOS,
            "random_seed": RANDOM_SEED,
            "base_data": INPUT_CSV,
            "base_data_n": len(df),
            "base_data_silver_distribution": dict(Counter(df["label_4_silver"])),
        },
        "methods": METHODS,
        "results_by_prevalence": {},
    }

    for prev in PREVALENCES:
        composition = sample_composition(prev, SIM_N)
        print(f"  prevalence={prev:.2f}: composition={composition}")
        boot_metrics = {m: [] for m in METHODS}
        llm_captured = []
        missed_by_all = []
        for boot in range(N_BOOTSTRAP):
            sim_id = f"SIM_prev{int(prev*100):02d}_boot{boot:04d}"
            sample = draw_bootstrap_sample(pools, composition, rng)
            # Manifest (summary per simulation)
            manifest_rows.append({
                "simulation_id": sim_id,
                "prevalence": prev,
                "bootstrap_iter": boot,
                "n_strong": composition[STRONG],
                "n_supported": composition["supported"],
                "n_mild": composition["mild_scope_overclaim"],
                "n_contradiction": composition["contradiction_candidate"],
                "n_total": len(sample),
            })
            for method in METHODS:
                m = compute_screening_metrics(sample, method)
                boot_metrics[method].append(m)
            cap, missed = compute_llm_missed_captured_by_r4(sample)
            llm_captured.append(cap)
            missed_by_all.append(missed)
        # Aggregate
        prev_summary = {"prevalence": prev, "composition": composition}
        for method in METHODS:
            agg = aggregate_metrics(boot_metrics[method])
            row = {"method": method, "prevalence": prev}
            for k, v in agg.items():
                row[k] = v
            row["llm_missed_strong_captured_by_r4_mean"] = mean(llm_captured)
            row["strong_cases_missed_by_all_methods_mean"] = mean(missed_by_all)
            metrics_rows.append(row)
            prev_summary[method] = {
                "recall_mean": agg["recall_mean"],
                "precision_mean": agg["precision_mean"],
                "positive_f1_mean": agg["positive_f1_mean"],
                "fp_tp_ratio_mean": agg["fp_tp_ratio_mean"],
                "fp_tp_ratio_median": agg["fp_tp_ratio_median"],
                "review_burden_mean": agg["review_burden_mean"],
                "nnr_mean": agg["number_needed_to_review_per_true_strong_mean"],
                "accuracy_mean": agg["accuracy_mean"],
                "llm_missed_captured_by_r4_mean": mean(llm_captured),
            }
        summary["results_by_prevalence"][f"prev_{int(prev*100):02d}"] = prev_summary

    print(f"\nWriting manifest ({len(manifest_rows)} rows)...")
    write_manifest(manifest_rows)
    print(f"Writing metrics ({len(metrics_rows)} rows)...")
    write_metrics_csv(metrics_rows)

    print(f"Writing summary JSON...")
    with open(SUMMARY_JSON, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    # Phase 2: Review budget curve
    print("\nPhase 2: Computing review budget curve...")
    budget_results = compute_review_budget_curve(pools, PREVALENCES, REVIEW_BUDGETS)
    budget_agg = aggregate_budget_curve(budget_results)
    print(f"Writing budget curve ({len(budget_agg)} rows)...")
    budget_fields = ["method", "prevalence", "review_budget", "n_reviewed_median",
                     "strong_recall_at_budget_mean", "strong_recall_at_budget_ci_lo",
                     "strong_recall_at_budget_ci_hi", "precision_at_budget_mean",
                     "fp_tp_at_budget_mean", "notes"]
    with open(BUDGET_CSV, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=budget_fields)
        w.writeheader()
        for row in budget_agg:
            w.writerow(row)

    print("\nDone.")
    print(f"  Manifest: {MANIFEST_CSV}")
    print(f"  Metrics:  {METRICS_CSV}")
    print(f"  Summary:  {SUMMARY_JSON}")
    print(f"  Budget:   {BUDGET_CSV}")


if __name__ == "__main__":
    main()
