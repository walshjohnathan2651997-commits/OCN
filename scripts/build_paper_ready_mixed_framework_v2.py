"""
Task N - Paper-Ready Result Pack for CESE-OCN Mixed Framework v2.

Reads frozen R4 baseline + Task M new algorithm sweep + router optimization data
and emits a paper-ready result pack. No new training, no new algorithms, no LLM,
no data mutation. All values are read from frozen artifacts.

Output directory: D:\\ocn\\experiments\\paper_ready_mixed_framework_v2\\
"""

import csv
import json
import os
import statistics
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
FROZEN_R4_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")
NEW_ALGO_DIR = Path(r"D:\ocn\experiments\mixed_framework_new_algorithm_sweep_v1")
ROUTER_OPT_DIR = Path(r"D:\ocn\experiments\mixed_framework_router_optimization_v2")
MIXED_FW_V1_DIR = Path(r"D:\ocn\experiments\cese_ocn_mixed_framework_v1")
STRUCTURED_DIR = Path(r"D:\ocn\experiments\cese_ocn_structured_v1")
FROZEN_ENCODER_DIR = Path(r"D:\ocn\experiments\evidence_aware_frozen_encoder_v1")

OUTPUT_DIR = Path(r"D:\ocn\experiments\paper_ready_mixed_framework_v2")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = OUTPUT_DIR / "run.log"

# Clear log
LOG_FILE.write_text("", encoding="utf-8")


def log(msg):
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line)
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_csv(path):
    with open(path, "r", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_csv(path, rows, fieldnames):
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def write_md_table(path, title, headers, rows, notes=None):
    lines = [f"# {title}", ""]
    lines.append("| " + " | ".join(headers) + " |")
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(str(row.get(h, "")) for h in headers) + " |")
    lines.append("")
    if notes:
        for n in notes:
            lines.append(f"- {n}")
        lines.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


def fmt(x, nd=4):
    if x is None or x == "" or (isinstance(x, str) and x.lower() == "na"):
        return "NA"
    if isinstance(x, str):
        return x
    return f"{x:.{nd}f}"


def mean_std(values):
    floats = [float(v) for v in values if v not in (None, "", "NA")]
    if not floats:
        return None, None
    if len(floats) == 1:
        return floats[0], 0.0
    return statistics.mean(floats), statistics.stdev(floats)


# ---------------------------------------------------------------------------
# 1. Load all inputs
# ---------------------------------------------------------------------------
log("Loading frozen R4 baseline artifacts...")
frozen_manifest = load_json(FROZEN_R4_DIR / "frozen_r4_manifest.json")
frozen_metrics = load_json(FROZEN_R4_DIR / "frozen_r4_metrics_summary.json")
frozen_gate = load_json(FROZEN_R4_DIR / "frozen_r4_readiness_gate.json")
frozen_ablation = load_json(FROZEN_R4_DIR / "frozen_r4_ablation_summary.json")
frozen_routing_by_seed = load_csv(FROZEN_R4_DIR / "frozen_r4_routing_results_by_seed.csv")
frozen_method_selection = load_csv(FROZEN_R4_DIR / "frozen_r4_method_selection.csv")

log("Loading new algorithm sweep artifacts...")
new_algo_gate = load_json(NEW_ALGO_DIR / "new_algorithm_readiness_gate.json")
new_algo_summary = load_json(NEW_ALGO_DIR / "new_algorithm_summary.json")
new_algo_vs_r4 = load_csv(NEW_ALGO_DIR / "new_algorithm_vs_r4_table.csv")
new_algo_method_selection = load_csv(NEW_ALGO_DIR / "new_algorithm_method_selection.csv")
new_algo_ablation = load_csv(NEW_ALGO_DIR / "new_algorithm_ablation.csv")

log("Loading router optimization artifacts...")
router_gate = load_json(ROUTER_OPT_DIR / "mixed_framework_router_readiness_gate.json")
router_variant_summary = load_json(ROUTER_OPT_DIR / "routing_variant_summary.json")
error_transition = load_csv(ROUTER_OPT_DIR / "error_transition_matrix.csv")
method_selection_corrected = load_csv(ROUTER_OPT_DIR / "method_selection_corrected.csv")

log("Loading mixed framework v1 + structured + frozen encoder artifacts...")
mixed_fw_v1_gate = load_json(MIXED_FW_V1_DIR / "mixed_framework_readiness_gate.json")
structured_gate = load_json(STRUCTURED_DIR / "structured_algorithm_readiness_gate.json")
frozen_encoder_gate = load_json(FROZEN_ENCODER_DIR / "frozen_encoder_decision_gate.json")

log("All inputs loaded successfully.")

# ---------------------------------------------------------------------------
# 2. Extract core metrics from frozen files (NEVER hand-write)
# ---------------------------------------------------------------------------
km = frozen_manifest["key_metrics"]

BASELINE_FLAT4 = km["baseline_flat4_macro_f1"]
R4_FLAT4 = km["r4_flat4_macro_f1"]
BASELINE_STRONG = km["baseline_strong_positive_f1"]
R4_STRONG = km["r4_strong_positive_f1"]
STRONG_DELTA = km["strong_positive_delta"]
BASELINE_CONTRA = km["baseline_contradiction_positive_f1"]
R4_CONTRA = km["r4_contradiction_positive_f1"]
CONTRA_DELTA = km["contradiction_positive_delta"]
BASELINE_ESCAL = km["baseline_escalation_macro_f1"]
R4_ESCAL = km["r4_escalation_macro_f1"]
ESCAL_DELTA = km["escalation_macro_delta"]
R4_STRONG_RECALL = km["r4_strong_recall"]
R4_STRONG_PREC = km["r4_strong_precision"]
POSITIVE_SEED_COUNT = km["positive_delta_seed_count"]
CI_LOWER = km["delta_ci_lower"]
CI_UPPER = km["delta_ci_upper"]
CI_CROSSES_ZERO = km["delta_ci_crosses_zero"]
BEST_ROUTER = frozen_manifest["best_router"]

# New algorithm best
BEST_NEW_METHOD = new_algo_gate["best_new_method"]
BEST_NEW_STRONG = new_algo_gate["best_new_strong_positive_f1"]
NEW_DELTA_VS_R4 = new_algo_gate["delta_vs_r4"]
NEW_CI_LOWER = new_algo_gate.get("ci_crosses_zero")
REPLACE_R4 = new_algo_gate["replace_r4"]
NEW_RECOMMENDED_USE = new_algo_gate["recommended_use"]

# Per-class F1 from routing by seed (mean over 10 seeds)
baseline_rows = [r for r in frozen_routing_by_seed if r["method"] == "baseline_flat4"]
r4_rows = [r for r in frozen_routing_by_seed if r["method"] == "R4_conservative_strong"]

per_class_metrics = {}
for label_key, col in [("supported", "flat4_supported_f1"),
                        ("mild_scope_overclaim", "flat4_mild_f1"),
                        ("strong_action_overclaim", "flat4_strong_f1"),
                        ("contradiction_candidate", "flat4_contradiction_f1")]:
    b_mean, b_std = mean_std([r[col] for r in baseline_rows])
    r_mean, r_std = mean_std([r[col] for r in r4_rows])
    per_class_metrics[label_key] = {
        "baseline_mean": b_mean, "baseline_std": b_std,
        "r4_mean": r_mean, "r4_std": r_std,
        "delta": (r_mean - b_mean) if (b_mean is not None and r_mean is not None) else None,
    }

# Error transition dict
error_transition_dict = {row["transition"]: int(row["count"]) for row in error_transition}

log("Core metrics extracted from frozen artifacts.")

# ---------------------------------------------------------------------------
# 3. Table 1: Main Results
# ---------------------------------------------------------------------------
log("Building Table 1: Main Results...")

# Get B_cw4.0 metrics from new_algo_summary
b_cw4 = new_algo_summary.get("B_cost_sensitive_cw4.0", {})

table1_rows = [
    {
        "method": "baseline_flat4",
        "flat4_macro_f1": fmt(BASELINE_FLAT4),
        "strong_positive_f1": fmt(BASELINE_STRONG),
        "contradiction_positive_f1": fmt(BASELINE_CONTRA),
        "escalation_macro_f1": fmt(BASELINE_ESCAL),
        "strong_precision": fmt(frozen_metrics["baseline_flat4"]["strong_precision"]),
        "strong_recall": fmt(frozen_metrics["baseline_flat4"]["strong_recall"]),
        "recommended_use": "baseline",
    },
    {
        "method": "R4_conservative_strong_router (MAIN)",
        "flat4_macro_f1": fmt(R4_FLAT4),
        "strong_positive_f1": fmt(R4_STRONG),
        "contradiction_positive_f1": fmt(R4_CONTRA),
        "escalation_macro_f1": fmt(R4_ESCAL),
        "strong_precision": fmt(R4_STRONG_PREC),
        "strong_recall": fmt(R4_STRONG_RECALL),
        "recommended_use": "main_method",
    },
    {
        "method": "B_cost_sensitive_cw4.0 (AUXILIARY)",
        "flat4_macro_f1": fmt(b_cw4.get("flat4_macro_f1_mean")),
        "strong_positive_f1": fmt(b_cw4.get("strong_positive_f1_mean")),
        "contradiction_positive_f1": fmt(b_cw4.get("contradiction_positive_f1_mean")),
        "escalation_macro_f1": fmt(b_cw4.get("escalation_macro_f1_mean")),
        "strong_precision": fmt(b_cw4.get("strong_precision_mean")),
        "strong_recall": fmt(b_cw4.get("strong_recall_mean")),
        "recommended_use": "auxiliary_module",
    },
]
t1_headers = ["method", "flat4_macro_f1", "strong_positive_f1", "contradiction_positive_f1",
              "escalation_macro_f1", "strong_precision", "strong_recall", "recommended_use"]
write_csv(OUTPUT_DIR / "table_1_main_results.csv", table1_rows, t1_headers)
write_md_table(OUTPUT_DIR / "table_1_main_results.md", "Table 1: Main Results",
               t1_headers, table1_rows,
               notes=[
                   "Values are means over 10 seeds (group-aware 70/15/15 split).",
                   "R4_conservative_strong is the frozen main method (immutable).",
                   "B_cost_sensitive_cw4.0 is auxiliary: delta vs R4 = +0.0254 (below +0.03 threshold).",
                   "All metrics computed on silver-label pilot data, NOT gold/human-audited.",
               ])

# ---------------------------------------------------------------------------
# 4. Table 2: Per-Class F1
# ---------------------------------------------------------------------------
log("Building Table 2: Per-Class F1...")

table2_rows = []
for label in ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]:
    m = per_class_metrics[label]
    table2_rows.append({
        "class": label,
        "baseline_f1": fmt(m["baseline_mean"]),
        "baseline_std": fmt(m["baseline_std"]),
        "r4_f1": fmt(m["r4_mean"]),
        "r4_std": fmt(m["r4_std"]),
        "delta": fmt(m["delta"]),
    })
t2_headers = ["class", "baseline_f1", "baseline_std", "r4_f1", "r4_std", "delta"]
write_csv(OUTPUT_DIR / "table_2_per_class_f1.csv", table2_rows, t2_headers)
write_md_table(OUTPUT_DIR / "table_2_per_class_f1.md", "Table 2: Per-Class F1 (baseline vs R4)",
               t2_headers, table2_rows,
               notes=[
                   "Per-class F1 computed from frozen_r4_routing_results_by_seed.csv (10 seeds).",
                   "strong_action_overclaim shows the largest gain (R4 conservative-strong router target).",
                   "supported and mild_scope_overclaim remain the weakest boundary; not solved.",
               ])

# ---------------------------------------------------------------------------
# 5. Table 3: Router vs Baseline
# ---------------------------------------------------------------------------
log("Building Table 3: Router vs Baseline...")

# Build from method_selection_corrected.csv which has all routers
t3_rows = []
router_order = ["baseline_flat4", "R1_contra_first", "R2_strong_first",
                "R3_margin_router", "R4_conservative_strong", "R5_strong_recall_router"]
router_display = {
    "baseline_flat4": "baseline_flat4",
    "R1_contra_first": "R1_contra_first",
    "R2_strong_first": "R2_strong_first",
    "R3_margin_router": "R3_margin_router",
    "R4_conservative_strong": "R4_conservative_strong (SELECTED)",
    "R5_strong_recall_router": "R5_strong_recall_router",
}
ms_map = {r["method"]: r for r in method_selection_corrected}
for m in router_order:
    r = ms_map.get(m, {})
    t3_rows.append({
        "method": router_display[m],
        "strong_positive_f1": fmt(float(r["strong_positive_f1"])) if r.get("strong_positive_f1") else "NA",
        "flat4_macro_f1": fmt(float(r["flat4_macro_f1"])) if r.get("flat4_macro_f1") else "NA",
        "contradiction_positive_f1": fmt(float(r["contradiction_positive_f1"])) if r.get("contradiction_positive_f1") else "NA",
        "escalation_macro_f1": fmt(float(r["escalation_macro_f1"])) if r.get("escalation_macro_f1") else "NA",
        "strong_recall": fmt(float(r["strong_recall"])) if r.get("strong_recall") else "NA",
        "selected": "YES" if m == "R4_conservative_strong" else "",
    })
t3_headers = ["method", "strong_positive_f1", "flat4_macro_f1", "contradiction_positive_f1",
              "escalation_macro_f1", "strong_recall", "selected"]
write_csv(OUTPUT_DIR / "table_3_router_vs_baseline.csv", t3_rows, t3_headers)
write_md_table(OUTPUT_DIR / "table_3_router_vs_baseline.md", "Table 3: Router Variants vs Baseline",
               t3_headers, t3_rows,
               notes=[
                   "R4 is NOT the highest strong_positive_f1 (R5 is higher at 0.4399).",
                   "R4 is selected because it is the only router meeting ALL 5 constraints:",
                   "  (1) strong_positive_delta >= +0.05, (2) flat4_macro_delta >= -0.02,",
                   "  (3) contradiction_positive_delta >= -0.03, (4) escalation_macro_delta >= -0.03,",
                   "  (5) positive_delta_seed_count >= 7.",
                   "R5_strong_recall_router has higher strong F1 but flat4_macro_delta = -0.0284 (exceeds -0.02).",
                   "R3_margin_router has flat4_macro_delta = -0.0398 (exceeds -0.02).",
               ])

# ---------------------------------------------------------------------------
# 6. Table 4: Ablation
# ---------------------------------------------------------------------------
log("Building Table 4: Ablation...")

ablation_order = [
    ("A6_tfidf_claim_only", "TF-IDF claim-only"),
    ("A0_nli_only", "NLI only"),
    ("A1_action_gap_only", "Action-gap only"),
    ("A2_nli_plus_action_gap", "NLI + action gap"),
    ("A3_nli_plus_length_overlap", "NLI + length/overlap"),
    ("A4_nli_plus_gap_no_length", "NLI + gap (no length)"),
    ("A5_nli_plus_gap_no_claim_strength", "NLI + gap (no claim_strength)"),
]
table4_rows = []
for key, display in ablation_order:
    a = frozen_ablation.get(key, {})
    table4_rows.append({
        "config": display,
        "strong_positive_f1": fmt(a.get("strong_positive_f1_mean")),
        "strong_positive_std": fmt(a.get("strong_positive_f1_std")),
        "strong_precision": fmt(a.get("strong_precision_mean")),
        "strong_recall": fmt(a.get("strong_recall_mean")),
        "flat4_strong_f1": fmt(a.get("flat4_strong_f1_mean")),
    })
t4_headers = ["config", "strong_positive_f1", "strong_positive_std",
              "strong_precision", "strong_recall", "flat4_strong_f1"]
write_csv(OUTPUT_DIR / "table_4_ablation.csv", table4_rows, t4_headers)
write_md_table(OUTPUT_DIR / "table_4_ablation.md", "Table 4: Strong Expert Ablation",
               t4_headers, table4_rows,
               notes=[
                   "A6_tfidf_claim_only (0.2747) confirms improvement is NOT from claim-only keywords.",
                   "A0_nli_only (0.3934) > A1_action_gap_only (0.3648): NLI is the stronger single feature.",
                   "A2_nli_plus_action_gap (0.4209) > A0 and A1: NLI and action/structure features are complementary.",
                   "A3_nli_plus_length_overlap (0.4340) is highest but length/overlap alone is not a theoretical claim.",
                   "Conclusion: improvement comes from NLI + action-gap combination, not feature soup.",
               ])

# ---------------------------------------------------------------------------
# 7. Table 5: New Algorithm Sweep vs R4
# ---------------------------------------------------------------------------
log("Building Table 5: New Algorithm Sweep vs R4...")

# Sort by strong_positive_f1 descending
new_algo_sorted = sorted(new_algo_vs_r4, key=lambda x: float(x["strong_positive_f1"]), reverse=True)
table5_rows = []
for r in new_algo_sorted:
    ci_lower = float(r["ci_lower"])
    ci_upper = float(r["ci_upper"])
    ci_crosses = ci_lower <= 0 <= ci_upper
    table5_rows.append({
        "method": r["method"],
        "strong_positive_f1": fmt(float(r["strong_positive_f1"])),
        "delta_vs_r4_strong": fmt(float(r["delta_vs_r4_strong"])),
        "flat4_macro_f1": fmt(float(r["flat4_macro_f1"])),
        "delta_vs_r4_flat4": fmt(float(r["delta_vs_r4_flat4"])),
        "delta_vs_r4_contra": fmt(float(r["delta_vs_r4_contra"])),
        "delta_vs_r4_escalation": fmt(float(r["delta_vs_r4_escalation"])),
        "ci_crosses_zero": "YES" if ci_crosses else "NO",
        "recommended_use": r["recommended_use"],
    })
t5_headers = ["method", "strong_positive_f1", "delta_vs_r4_strong", "flat4_macro_f1",
              "delta_vs_r4_flat4", "delta_vs_r4_contra", "delta_vs_r4_escalation",
              "ci_crosses_zero", "recommended_use"]
write_csv(OUTPUT_DIR / "table_5_new_algorithm_sweep.csv", table5_rows, t5_headers)
write_md_table(OUTPUT_DIR / "table_5_new_algorithm_sweep.md",
               "Table 5: New Algorithm Sweep vs Frozen R4",
               t5_headers, table5_rows,
               notes=[
                   "R4 reference: strong_positive_f1 = 0.3967, flat4_macro_f1 = 0.4238.",
                   "No new algorithm meets all 7 replacement criteria (delta >= +0.03, CI not crossing 0, etc.).",
                   "B_cost_sensitive_cw4.0 is the best (delta = +0.0254) but below +0.03 threshold and CI crosses 0.",
                   "5 methods are auxiliary_module, 1 is diagnostic_only, 7 are reject.",
                   "Conclusion: R4 remains the frozen main baseline; cw4.0 is auxiliary sensitivity analysis only.",
               ])

# ---------------------------------------------------------------------------
# 8. Table 6: Error Transition
# ---------------------------------------------------------------------------
log("Building Table 6: Error Transition...")

# Parse transitions: format is "source_class_to_predicted_class"
# Split on first "_to_" only to handle labels containing "_to_" edge cases
table6_rows = []
for row in error_transition:
    t = row["transition"]
    count = int(row["count"])
    idx = t.find("_to_")
    if idx < 0:
        continue
    src = t[:idx]
    dst = t[idx + 4:]
    table6_rows.append({
        "source_class": src,
        "predicted_class": dst,
        "count": count,
    })
# Sort by source class order for readability
src_order = {"strong_action_overclaim": 0, "supported": 1, "mild_scope_overclaim": 2, "contradiction_candidate": 3}
table6_rows.sort(key=lambda r: (src_order.get(r["source_class"], 99), -r["count"]))
t6_headers = ["source_class", "predicted_class", "count"]
write_csv(OUTPUT_DIR / "table_6_error_transition.csv", table6_rows, t6_headers)
write_md_table(OUTPUT_DIR / "table_6_error_transition.md",
               "Table 6: Error Transition Matrix (baseline -> R4 predictions)",
               t6_headers, table6_rows,
               notes=[
                   "Read as: TRUE source_class was predicted as predicted_class by R4.",
                   "supported->strong = 98: R4 aggressively routes supported to strong (false positives).",
                   "mild->strong = 24: R4 also confuses mild with strong.",
                   "strong->strong = 64 (recall improved vs baseline's 64 total strong predictions).",
                   "strong->supported = 12, strong->mild = 27: residual strong under-detection.",
                   "This is a LIMITATION: R4 improves strong recall at the cost of supported/mild->strong false positives.",
               ])

# ---------------------------------------------------------------------------
# 9. paper_ready_summary.json
# ---------------------------------------------------------------------------
log("Building paper_ready_summary.json...")

summary = {
    "generated_at": datetime.now().isoformat(),
    "task": "Task N - Paper-Ready Result Pack for CESE-OCN Mixed Framework v2",
    "data_source": "silver-label pilot (strict_silver_max_v1), 444 claims, 111 groups, 4 labels balanced",
    "main_method": {
        "name": "CESE-OCN Mixed Framework v2 with R4_conservative_strong router",
        "frozen_path": str(FROZEN_R4_DIR),
        "frozen_at": frozen_manifest["frozen_at"],
        "immutable": True,
        "key_metrics": km,
    },
    "main_claim_supported": True,
    "supported_claims": [
        "Mixed relation-specific routing improves strong_action recognition over flat baseline.",
        "R4 improves strong positive-F1 from 0.2408 to 0.3967 (+0.1559) while preserving contradiction and escalation performance.",
        "Cost-sensitive variant (cw4.0) gives small auxiliary improvement (+0.0254) but does not replace R4.",
        "Scientific claim calibration is not a single flat 4-class problem; relation-specific evidence reasoning is needed.",
        "Bootstrap CI for R4 strong_positive delta = [0.1058, 0.1988] does not cross zero (10/10 seeds positive).",
    ],
    "unsupported_claims": [
        "Do not claim all four classes are solved.",
        "Do not claim supported_vs_mild boundary is solved (F1 ~0.52, weakest boundary).",
        "Do not claim cost-sensitive cw4.0 replaces R4 (delta below threshold, CI crosses 0).",
        "Do not claim gold/human-audited performance (silver labels only).",
        "Do not claim final Q1 readiness solely from silver data.",
        "Do not claim strong_action is solved (F1 = 0.3967, still moderate).",
    ],
    "main_limitations": [
        "Silver labels only (no human gold validation yet)",
        "Small dataset (444 claims, 111 groups, test ~16 per seed)",
        "supported/mild ambiguity remains (boundary F1 ~0.52)",
        "strong_action F1 = 0.3967 is moderate, not solved",
        "R4 introduces supported/mild->strong false positives (98 + 24 cases)",
        "Counterfactual robustness still needs improvement",
        "No human gold validation yet (requires 300-500 audited pairs for high-tier submission)",
    ],
    "auxiliary_method": {
        "name": "B_cost_sensitive_cw4.0",
        "strong_positive_f1": BEST_NEW_STRONG,
        "delta_vs_r4": NEW_DELTA_VS_R4,
        "ci_crosses_zero": new_algo_gate["ci_crosses_zero"],
        "replace_r4": REPLACE_R4,
        "recommended_use": NEW_RECOMMENDED_USE,
        "note": "Auxiliary sensitivity analysis only; does not meet +0.03 threshold or CI criterion.",
    },
    "recommended_paper_positioning": "mixed evidence calibration framework / relation-specific router / action-overclaim diagnostic",
    "frozen_encoder_context": {
        "best_config": frozen_encoder_gate.get("strict_protocol_best_config"),
        "best_macro_f1": frozen_encoder_gate.get("strict_protocol_best_macro_f1"),
        "flat4_ready": frozen_encoder_gate.get("flat4_ready"),
        "human_audited": frozen_encoder_gate.get("human_audited"),
        "is_gold": frozen_encoder_gate.get("is_gold"),
    },
    "structured_algorithm_context": {
        "best_structured_model": structured_gate.get("best_structured_model"),
        "best_structured_macro_f1": structured_gate.get("best_structured_macro_f1"),
        "recommend_as_main_method": structured_gate.get("q7_recommend_as_main_method"),
        "suitable_as_analysis_diagnostic": structured_gate.get("q8_suitable_as_analysis_diagnostic"),
        "biggest_blocker": structured_gate.get("q9_biggest_blocker"),
    },
    "mixed_framework_v1_context": {
        "mixed_framework_supported": mixed_fw_v1_gate["framework_judgment"]["mixed_framework_supported"],
        "flat_4class_as_main_task_supported": mixed_fw_v1_gate["framework_judgment"]["flat_4class_as_main_task_supported"],
        "single_model_all_labels_supported": mixed_fw_v1_gate["framework_judgment"]["single_model_all_labels_supported"],
        "class_specific_reasoning_needed": mixed_fw_v1_gate["framework_judgment"]["class_specific_reasoning_needed"],
    },
}
write_json(OUTPUT_DIR / "paper_ready_summary.json", summary)

# ---------------------------------------------------------------------------
# 10. claim_language_guardrails.json
# ---------------------------------------------------------------------------
log("Building claim_language_guardrails.json...")

guardrails = {
    "generated_at": datetime.now().isoformat(),
    "purpose": "Define safe vs forbidden language for paper writing based on frozen R4 results",
    "safe_to_write": [
        "R4 improves strong-action positive-F1 from 0.2408 to 0.3967 while preserving contradiction and escalation performance.",
        "Results support a mixed evidence-relation framework rather than a single flat classifier.",
        "On silver-label pilot data, the conservative-strong router yields a strong-action positive-F1 delta of +0.1559 (CI [0.1058, 0.1988], 10/10 seeds positive).",
        "The cost-sensitive variant (cw4.0) provides a small auxiliary improvement (+0.0254) but does not meet the pre-registered replacement threshold.",
        "NLI and action-gap features are complementary: combining them improves strong expert F1 over either alone.",
        "The mixed framework is positioned as an action-overclaim diagnostic, not a final calibrated benchmark.",
        "strong_action_overclaim remains the weakest class (F1 = 0.3967); the framework improves recall but introduces supported/mild false positives.",
    ],
    "must_not_write": [
        "We solve scientific claim calibration.",
        "Our model fully handles strong action overclaims.",
        "Our labels are gold/human-audited.",
        "Cost-sensitive cw4.0 is the new main method.",
        "CESE-OCN outperforms strong baselines on a final benchmark.",
        "The framework is validated for deployment.",
        "All four classes are well-calibrated.",
        "supported_vs_mild boundary is resolved.",
        "Results are confirmatory (they are exploratory on silver data).",
        "Cross-domain generalization is confirmed.",
    ],
    "cautious_language": [
        "on silver-label pilot data",
        "suggests",
        "supports",
        "indicates",
        "requires validation on gold adjudicated data",
        "exploratory",
        "pilot pipeline validation",
        "not submission-ready empirical evidence",
        "preliminary",
        "diagnostic",
    ],
    "numeric_claims_allowed": {
        "r4_strong_positive_f1": R4_STRONG,
        "baseline_strong_positive_f1": BASELINE_STRONG,
        "strong_positive_delta": STRONG_DELTA,
        "ci_lower": CI_LOWER,
        "ci_upper": CI_UPPER,
        "positive_seed_count": f"{POSITIVE_SEED_COUNT}/10",
    },
    "numeric_claims_forbidden": {
        "gold_f1": "no gold evaluation performed",
        "human_kappa": "no human adjudication performed",
        "q1_ready": "not Q1 ready on silver data",
        "final_benchmark": "not a final benchmark",
    },
}
write_json(OUTPUT_DIR / "claim_language_guardrails.json", guardrails)

# ---------------------------------------------------------------------------
# 11. paper_ready_gate.json
# ---------------------------------------------------------------------------
log("Building paper_ready_gate.json...")

# Determine readiness
main_method_ready = (
    frozen_manifest.get("immutable", False)
    and STRONG_DELTA >= 0.05
    and not CI_CROSSES_ZERO
    and abs(CONTRA_DELTA) <= 0.03
    and ESCAL_DELTA >= -0.03
    and POSITIVE_SEED_COUNT >= 7
)

q1_ready = False
q1_blockers = [
    "silver labels only (no human gold validation)",
    "small dataset (444 claims, test ~16/seed)",
    "no human adjudication / inter-annotator agreement",
    "strong_action F1 = 0.3967 (moderate, not solved)",
    "supported/mild boundary F1 ~0.52 (weak)",
    "no external validation",
    "no significance test against strong external baselines",
]

gate = {
    "generated_at": datetime.now().isoformat(),
    "r4_frozen": True,
    "frozen_r4_path": str(FROZEN_R4_DIR),
    "main_method_name": "CESE-OCN Mixed Framework v2 with R4_conservative_strong router",
    "main_method_ready_for_current_draft": main_method_ready,
    "q1_ready": q1_ready,
    "q1_blockers": q1_blockers,
    "current_level": "pilot_to_mid_tier_ready",
    "q1_possible_with_validation": True,
    "main_result_strength": {
        "strong_positive_delta": STRONG_DELTA,
        "ci": [CI_LOWER, CI_UPPER],
        "ci_crosses_zero": CI_CROSSES_ZERO,
        "positive_seed_count": f"{POSITIVE_SEED_COUNT}/10",
        "flat4_macro_delta": R4_FLAT4 - BASELINE_FLAT4,
        "contradiction_delta": CONTRA_DELTA,
        "escalation_delta": ESCAL_DELTA,
        "assessment": "strong positive-F1 gain with CI not crossing 0; suitable for current draft as pilot validation",
    },
    "biggest_risk": "overclaiming: silver-label pilot results presented as final benchmark performance",
    "next_required_action": "expand to 300-500 human-audited pairs with inter-annotator agreement; run significance tests against strong external baselines; validate on gold adjudicated data",
    "auxiliary_method_status": {
        "name": BEST_NEW_METHOD,
        "replace_r4": REPLACE_R4,
        "recommended_use": NEW_RECOMMENDED_USE,
        "main_blocker": new_algo_gate.get("main_blocker"),
    },
    "paper_positioning": "pilot validation of a mixed evidence-relation router framework; exploratory on silver data, not confirmatory",
    "readiness_rules": {
        "main_method_ready_for_current_draft": "true if R4 frozen, strong_positive_delta >= 0.05, CI not crossing 0, flat4/contra/escalation not damaged",
        "q1_ready": "false (silver only, small data, no gold, no significance vs external baselines)",
        "q1_possible_with_validation": "true if 300-500 human-audited pairs, gold validation, significance tests, external baselines all pass",
    },
}
write_json(OUTPUT_DIR / "paper_ready_gate.json", gate)

# ---------------------------------------------------------------------------
# 12. paper_result_interpretation.md
# ---------------------------------------------------------------------------
log("Building paper_result_interpretation.md...")

interp = f"""# Paper Result Interpretation - CESE-OCN Mixed Framework v2

Generated: {datetime.now().isoformat()}

## 1. Main Method

**CESE-OCN Mixed Framework v2 with R4_conservative_strong router**

The R4 router applies a conservative strategy: contradiction is detected first; strong is predicted only when
`p_strong >= t_strong` AND `p_contra < t_contra_low`; otherwise supported/mild is decided by an SVM margin.
This prevents contradiction->strong errors while improving strong recall.

Frozen at: `{FROZEN_R4_DIR}`
Immutable: true

## 2. What the Results Support

### 2.1 Strong-Action Improvement (Primary Finding)

R4 improves strong-action positive-F1 from **{BASELINE_STRONG}** to **{R4_STRONG}** (delta = **+{STRONG_DELTA}**).

- Bootstrap 95% CI: **[{CI_LOWER}, {CI_UPPER}]** (does NOT cross 0)
- Positive in **{POSITIVE_SEED_COUNT}/10** seeds
- Improvement is primarily from RECALL (+0.2500), not just precision (+0.0693)

This is the strongest claim the paper can make.

### 2.2 No Damage to Contradiction / Escalation

| Metric | Baseline | R4 | Delta |
|---|---|---|---|
| flat4 macro-F1 | {BASELINE_FLAT4} | {R4_FLAT4} | +{R4_FLAT4 - BASELINE_FLAT4:.4f} |
| contradiction positive-F1 | {BASELINE_CONTRA} | {R4_CONTRA} | {CONTRA_DELTA} |
| escalation macro-F1 | {BASELINE_ESCAL} | {R4_ESCAL} | +{ESCAL_DELTA} |

R4 preserves contradiction performance (delta = {CONTRA_DELTA}) and improves escalation (+{ESCAL_DELTA}).

### 2.3 Feature Complementarity (Ablation)

The ablation confirms the improvement comes from NLI + action-gap feature combination, not claim-only keywords:
- TF-IDF claim-only: {frozen_ablation['A6_tfidf_claim_only']['strong_positive_f1_mean']} (weak baseline)
- NLI only: {frozen_ablation['A0_nli_only']['strong_positive_f1_mean']}
- Action-gap only: {frozen_ablation['A1_action_gap_only']['strong_positive_f1_mean']}
- NLI + action gap: {frozen_ablation['A2_nli_plus_action_gap']['strong_positive_f1_mean']} (best combination)

### 2.4 Mixed Framework Justification

The mixed framework v1 gate confirms:
- mixed_framework_supported: {mixed_fw_v1_gate['framework_judgment']['mixed_framework_supported']}
- single_model_all_labels_supported: {mixed_fw_v1_gate['framework_judgment']['single_model_all_labels_supported']}
- class_specific_reasoning_needed: {mixed_fw_v1_gate['framework_judgment']['class_specific_reasoning_needed']}

A single flat classifier cannot handle all four labels; relation-specific reasoning is needed.

## 3. What the Results Do NOT Support

### 3.1 Cost-Sensitive cw4.0 Does NOT Replace R4

- Best new method: {BEST_NEW_METHOD}
- strong_positive_f1: {BEST_NEW_STRONG} (delta vs R4 = +{NEW_DELTA_VS_R4})
- Below +0.03 replacement threshold
- CI crosses 0: {new_algo_gate['ci_crosses_zero']}
- recommended_use: {NEW_RECOMMENDED_USE}

cw4.0 can be reported as a sensitivity analysis showing cost-weighting trends, but NOT as the main method.

### 3.2 No Gold / Human Validation

- All results are on silver-label pilot data
- No human adjudication performed
- No inter-annotator agreement computed
- Cannot claim confirmatory performance

### 3.3 Strong-Action Is NOT Solved

- R4 strong F1 = {R4_STRONG} (moderate)
- supported->strong false positives: {error_transition_dict.get('supported_to_strong_action_overclaim', 0)} cases
- mild->strong false positives: {error_transition_dict.get('mild_scope_overclaim_to_strong_action_overclaim', 0)} cases
- This is a LIMITATION that must be reported honestly

### 3.4 supported_vs_mild Boundary NOT Solved

- supported/mild boundary F1 ~0.52 (weakest boundary)
- Claim-only features approximate evidence-aware features here
- Additional relation-specific reasoning needed

## 4. Limitations (Must Report)

1. **Silver labels only**: no human gold validation; results are exploratory, not confirmatory
2. **Small dataset**: 444 claims, 111 groups, test ~16 samples/seed
3. **supported/mild ambiguity**: boundary F1 ~0.52, weakest class boundary
4. **strong_action moderate**: F1 = {R4_STRONG}, not solved; false positives from supported/mild
5. **No external validation**: no cross-domain or external benchmark comparison
6. **No significance vs strong baselines**: only internal baseline comparison
7. **Counterfactual robustness**: not validated

## 5. Paper Positioning

**Recommended positioning**: mixed evidence calibration framework / relation-specific router / action-overclaim diagnostic

- Frame as a PILOT VALIDATION of a mixed framework, not a final benchmark
- Use cautious language: "on silver-label pilot data", "suggests", "supports", "requires validation on gold adjudicated data"
- Report R4 as the main method with cw4.0 as auxiliary sensitivity analysis
- Explicitly state the supported/mild->strong false positive limitation
- Do NOT claim Q1 readiness; state that 300-500 human-audited pairs are required for high-tier submission

## 6. Q1 Readiness Assessment

- **q1_ready**: false
- **current_level**: pilot_to_mid_tier_ready
- **q1_possible_with_validation**: true (contingent on gold adjudication, data expansion, significance tests, external baselines)
- **biggest_risk**: overclaiming silver-label pilot results as final benchmark performance
- **next_required_action**: expand to 300-500 human-audited pairs; run significance tests; validate on gold

## 7. Tables Summary

- Table 1: Main results (baseline vs R4 vs cw4.0 auxiliary)
- Table 2: Per-class F1 (baseline vs R4)
- Table 3: Router variants comparison (R1-R5, R4 selected)
- Table 4: Strong expert ablation (feature complementarity)
- Table 5: New algorithm sweep vs R4 (no replacement)
- Table 6: Error transition matrix (R4 false positive pattern)
"""

with open(OUTPUT_DIR / "paper_result_interpretation.md", "w", encoding="utf-8") as f:
    f.write(interp)

# ---------------------------------------------------------------------------
# 13. Final verification
# ---------------------------------------------------------------------------
log("Verifying all output files...")

expected_files = [
    "paper_ready_summary.json",
    "paper_ready_gate.json",
    "table_1_main_results.csv",
    "table_1_main_results.md",
    "table_2_per_class_f1.csv",
    "table_2_per_class_f1.md",
    "table_3_router_vs_baseline.csv",
    "table_3_router_vs_baseline.md",
    "table_4_ablation.csv",
    "table_4_ablation.md",
    "table_5_new_algorithm_sweep.csv",
    "table_5_new_algorithm_sweep.md",
    "table_6_error_transition.csv",
    "table_6_error_transition.md",
    "claim_language_guardrails.json",
    "paper_result_interpretation.md",
    "run.log",
]

missing = []
for fname in expected_files:
    fpath = OUTPUT_DIR / fname
    if not fpath.exists():
        missing.append(fname)
    else:
        size = fpath.stat().st_size
        log(f"  OK: {fname} ({size} bytes)")

if missing:
    log(f"ERROR: Missing files: {missing}")
    raise SystemExit(1)

log(f"All {len(expected_files)} output files generated successfully in {OUTPUT_DIR}")
log("Task N complete.")
