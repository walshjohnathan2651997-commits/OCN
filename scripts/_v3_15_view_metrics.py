"""Quick view of V3.15 metrics for report generation."""
import pandas as pd

df = pd.read_csv(r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\low_prevalence_screening_metrics.csv")

print("=== All methods at key prevalences ===")
for p in [0.01, 0.03, 0.05, 0.10, 0.15, 0.20, 0.25]:
    print(f"\n--- prevalence={p} ---")
    sub = df[df["prevalence"] == p]
    print(sub[["method", "recall_mean", "precision_mean", "positive_f1_mean",
               "fp_tp_ratio_median", "review_burden_mean",
               "number_needed_to_review_per_true_strong_mean", "accuracy_mean"]].to_string(index=False))

print("\n=== LLM-missed strong captured by R4 ===")
for p in [0.01, 0.03, 0.05, 0.10, 0.25]:
    sub = df[(df["prevalence"] == p) & (df["method"] == "r4")]
    if len(sub) > 0:
        row = sub.iloc[0]
        print(f"prev={p}: llm_missed_captured_by_r4_mean={row['llm_missed_strong_captured_by_r4_mean']:.3f}, missed_by_all_mean={row['strong_cases_missed_by_all_methods_mean']:.3f}")

print("\n=== Review budget curve (R4, prev=0.05) ===")
budget = pd.read_csv(r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\review_budget_curve.csv")
r4_budget = budget[(budget["method"] == "r4") & (budget["prevalence"] == 0.05)]
print(r4_budget[["review_budget", "n_reviewed_median", "strong_recall_at_budget_mean",
                  "precision_at_budget_mean", "fp_tp_at_budget_mean"]].to_string(index=False))

print("\n=== Review budget curve (R4 vs LLM, prev=0.05, budget=0.10) ===")
sub = budget[(budget["prevalence"] == 0.05) & (budget["review_budget"] == 0.10)]
print(sub[["method", "strong_recall_at_budget_mean", "precision_at_budget_mean", "fp_tp_at_budget_mean"]].to_string(index=False))
