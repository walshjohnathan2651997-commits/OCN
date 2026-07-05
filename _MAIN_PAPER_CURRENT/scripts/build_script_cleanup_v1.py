"""Clean up D:\\ocn\\scripts: categorize, archive non-mainline, generate manifests.

Does NOT delete any script. Does NOT modify script logic. Only moves files
and generates documentation.
"""
import csv
import os
import shutil
from collections import defaultdict

SCRIPTS_DIR = r"D:\ocn\scripts"
ARCHIVE_BASE = r"D:\ocn\_ARCHIVE_NON_MAINLINE"
INDEX_DIR = r"D:\ocn\_PROJECT_INDEX"

# Mainline scripts to KEEP in D:\ocn\scripts
MAINLINE_SCRIPTS = {
    # Paper version generation
    "build_v3_1_docx.py",
    "build_v3_2_docx.py",
    "build_v3_3_docx.py",
    "build_v3_4_docx.py",
    "build_v3_5_docx.py",
    "build_v3_6_docx.py",
    "build_v3_7_docx.py",
    "build_v3_2_table0_and_audit.py",
    "build_v3_3_main_paper.py",
    "build_v3_4_main_paper.py",
    "build_v3_4_taxonomy_hardening.py",
    "build_gold_pilot_preparation_v1.py",
    # Mainline experiments
    "run_v3_r4_strong_baselines_holdout_v1.py",
    "run_llm_judge_baseline_v1.py",
    "run_gpt_structured_judge_probe_v1.py",
    "run_external_gold_scifact_vitaminc_v1.py",
    "run_cese_ocn_lite_v3.py",
    "run_mixed_framework_router_optimization_v2.py",
    "run_mixed_framework_new_algorithm_sweep_v1.py",
    # Mainline result organization
    "build_paper_ready_mixed_framework_v2.py",
    "build_v3_external_gold_llm_plan_v1.py",
    # This script itself (keep for traceability)
    "build_script_cleanup_v1.py",
}

# Temp scripts (by name)
TEMP_SCRIPTS = {
    "_tmp_preview.py",
    "_v36_lookup.py",
    "_v36_lookup2.py",
    "_v36_lookup_out.txt",
}


def categorize_by_pattern(name):
    """Categorize a script by its name pattern. Returns archive category or None."""
    lower = name.lower()

    # Old experiment scripts
    old_exp_patterns = [
        "cese_ocn_hcm", "cese_ocn_structured", "cese_ocn_mixed_framework_v1",
        "escalation", "evidence_conditioned", "evidence_sanity",
        "frozen_encoder", "simclaim_v4", "strong_action_broad",
        "run_baselines", "run_ablations", "run_calibration_ablation",
        "run_constraint_ablation", "run_binary_decomposition", "run_multiseed",
        "run_pilot_loop", "run_relaxed_train", "run_silver_core",
        "run_oracle", "run_paper_v2_bootstrap", "run_paper_v2_domain",
        "run_adversarial", "run_delexicalized", "run_hard_diagnostic",
        "run_human_150", "run_leakage_filtered", "run_llm_judge_stability",
        "run_smoke", "run_all_experiments", "run_stage_",
        "run_dataset_pipeline", "run_release_pipeline",
        "train_baseline", "train_cese_ocn",
        "probe_evidence_aware", "evaluate_model", "error_analysis",
        "run_strong_baselines",
    ]
    for pat in old_exp_patterns:
        if pat in lower:
            return "scripts_old_experiments"

    # Old data pipeline scripts
    old_data_patterns = [
        "build_adversarial", "build_clean_weak", "build_delexicalized",
        "build_evidence_modes", "build_hard_diagnostic", "build_lexical",
        "build_oracle", "build_paper_splits", "build_round2",
        "build_source_bank", "build_source_triples", "build_strict_silver",
        "merge_all92", "make_toy", "split_pilot",
        "generate_round1", "generate_round2", "extract_round1",
        "fill_escalation", "fit_operating", "fit_thresholds",
        "check_pilot_balance", "setup_and_check", "stage_runner",
    ]
    for pat in old_data_patterns:
        if pat in lower:
            return "scripts_old_data_pipeline"

    # Old release/annotation/audit scripts
    old_release_patterns = [
        "adjudicate", "audit_", "compute_annotation",
        "import_annotations", "validate_annotations", "validate_data",
        "validate_dataset", "validate_experiment", "validate_pipeline",
        "validate_round", "verify_recut", "verify_task",
        "build_paper_closeout", "build_paper_draft", "build_paper_full",
        "build_paper_package", "build_paper_readiness", "build_paper_table",
        "build_release", "build_cese_ocn_v2_docx",
        "build_rq_experiment", "clean_artifacts", "compute_bootstrap",
        "data_report", "export_paper", "generate_clean_reports",
        "generate_manuscript", "generate_tables", "integrate_closeout",
        "lexical_template", "package_project", "package_release",
        "paired_significance", "prepare_audit", "revise_escalation",
        "rule_based_auditor", "survey_closeout", "tfidf_leakage",
        "unify_human_150", "bootstrap_metrics", "analyze_score",
        "check_graph", "check_paper_code", "check_paper_readiness",
        "check_release_hygiene", "check_threshold",
    ]
    for pat in old_release_patterns:
        if pat in lower:
            return "scripts_old_release_annotation"

    # Default: if it starts with run_ and not in mainline, it's old experiment
    if lower.startswith("run_"):
        return "scripts_old_experiments"

    # Default: if it starts with build_ and not in mainline, check more
    if lower.startswith("build_"):
        return "scripts_old_data_pipeline"

    # Everything else goes to old_experiments as fallback
    return "scripts_old_experiments"


def main():
    # Count before
    all_files = [f for f in os.listdir(SCRIPTS_DIR) if os.path.isfile(os.path.join(SCRIPTS_DIR, f))]
    before_count = len(all_files)
    print(f"Scripts before cleanup: {before_count}")

    # Create archive subdirectories
    archive_dirs = [
        "scripts_legacy",
        "scripts_temp",
        "scripts_old_experiments",
        "scripts_old_data_pipeline",
        "scripts_old_release_annotation",
    ]
    for d in archive_dirs:
        path = os.path.join(ARCHIVE_BASE, d)
        os.makedirs(path, exist_ok=True)
        print(f"  Created/verified: {path}")

    # Categorize each file
    moves = []  # (filename, old_path, archive_path, category, reason)
    keep = []   # (filename, reason)
    legacy = []  # files that don't fit other categories

    for f in all_files:
        old_path = os.path.join(SCRIPTS_DIR, f)

        if f in MAINLINE_SCRIPTS:
            keep.append((f, "Mainline script for V3.7/gold pilot/R4/LLM/paper-ready"))
            continue

        if f in TEMP_SCRIPTS:
            category = "scripts_temp"
            reason = "Temporary debug/lookup script"
        else:
            category = categorize_by_pattern(f)
            if category == "scripts_old_experiments":
                reason = "Old experiment script, not referenced by V3.7 mainline"
            elif category == "scripts_old_data_pipeline":
                reason = "Old data pipeline script, not referenced by V3.7 mainline"
            elif category == "scripts_old_release_annotation":
                reason = "Old release/annotation/audit script, not referenced by V3.7 mainline"
            else:
                reason = "Legacy script, not mainline"
                category = "scripts_legacy"

        archive_path = os.path.join(ARCHIVE_BASE, category, f)
        moves.append((f, old_path, archive_path, category, reason))

    # Execute moves
    print(f"\nMoving {len(moves)} scripts to archive...")
    moved_count = 0
    for (f, old_path, archive_path, category, reason) in moves:
        try:
            shutil.move(old_path, archive_path)
            moved_count += 1
        except Exception as e:
            print(f"  ERROR moving {f}: {e}")

    print(f"  Moved: {moved_count}")

    # Count after
    after_files = [f for f in os.listdir(SCRIPTS_DIR) if os.path.isfile(os.path.join(SCRIPTS_DIR, f))]
    after_count = len(after_files)
    print(f"Scripts after cleanup: {after_count}")

    # Generate script_registry_mainline.csv
    registry_path = os.path.join(INDEX_DIR, "script_registry_mainline.csv")
    with open(registry_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["script_name", "location", "purpose", "input_dependency", "output_dependency", "safe_to_run", "notes"])
        
        registry_entries = [
            ("build_v3_7_docx.py", "D:\\ocn\\scripts", "Build V3.7 docx from markdown", "CESE_OCN_V3_7_advisor_handoff_clean.md", "CESE_OCN_V3_7_advisor_handoff_clean.docx", "yes", "Current main docx builder"),
            ("build_v3_6_docx.py", "D:\\ocn\\scripts", "Build V3.6 docx from markdown", "CESE_OCN_V3_6_case_figure_integrity_checked.md", "CESE_OCN_V3_6_case_figure_integrity_checked.docx", "yes", "V3.6 docx builder for traceability"),
            ("build_v3_5_docx.py", "D:\\ocn\\scripts", "Build V3.5 docx from markdown", "CESE_OCN_V3_5_presentation_ready.md", "CESE_OCN_V3_5_presentation_ready.docx", "yes", "V3.5 docx builder for traceability"),
            ("build_v3_4_docx.py", "D:\\ocn\\scripts", "Build V3.4 docx from markdown", "CESE_OCN_V3_4_taxonomy_hardened.md", "CESE_OCN_V3_4_taxonomy_hardened.docx", "yes", "V3.4 docx builder for traceability"),
            ("build_v3_3_docx.py", "D:\\ocn\\scripts", "Build V3.3 docx from markdown", "V3.3 md", "V3.3 docx", "yes", "V3.3 docx builder for traceability"),
            ("build_v3_2_docx.py", "D:\\ocn\\scripts", "Build V3.2 docx from markdown", "V3.2 md", "V3.2 docx", "yes", "V3.2 docx builder for traceability"),
            ("build_v3_1_docx.py", "D:\\ocn\\scripts", "Build V3.1 docx from markdown", "V3.1 md", "V3.1 docx", "yes", "V3.1 docx builder for traceability"),
            ("build_v3_4_main_paper.py", "D:\\ocn\\scripts", "Build V3.4 main paper content", "V3.3 sources", "V3.4 md content", "no", "Paper content builder; output already frozen"),
            ("build_v3_3_main_paper.py", "D:\\ocn\\scripts", "Build V3.3 main paper content", "V3.2 sources", "V3.3 md content", "no", "Paper content builder; output already frozen"),
            ("build_v3_4_taxonomy_hardening.py", "D:\\ocn\\scripts", "Build V3.4 taxonomy hardening (decision tree, high_risk_sample_bank)", "V3.3 + audit data", "high_risk_sample_bank.csv, trusted_case_bank.csv, taxonomy_boundary_decision_tree.md", "no", "Generated key reference files for V3.7"),
            ("build_v3_2_table0_and_audit.py", "D:\\ocn\\scripts", "Build V3.2 Table 0 and author sanity audit", "Silver data", "table_0_taxonomy_examples.csv, author_sanity_audit_40.csv", "no", "Generated taxonomy examples and audit"),
            ("build_gold_pilot_preparation_v1.py", "D:\\ocn\\scripts", "Build gold pilot preparation pack (50 samples)", "high_risk_sample_bank.csv, trusted_case_bank.csv, strict_silver_max_candidates_v1.csv", "D:\\ocn\\gold_pilot_preparation_v1\\ (8 files)", "yes", "Gold pilot prep; safe to run, does not label or train"),
            ("run_v3_r4_strong_baselines_holdout_v1.py", "D:\\ocn\\scripts", "Run strong baselines + holdout validation", "strict_silver data", "experiments\\v3_r4_strong_baselines_holdout_v1\\", "no", "Mainline experiment; results already frozen; do not rerun"),
            ("run_llm_judge_baseline_v1.py", "D:\\ocn\\scripts", "Run DeepSeek LLM judge baseline (200 samples)", "llm_baseline_sample_plan.csv", "experiments\\llm_judge_baseline_v1\\", "no", "Requires DeepSeek API key; results already frozen; do not rerun without API authorization"),
            ("run_gpt_structured_judge_probe_v1.py", "D:\\ocn\\scripts", "Run GPT standard vs structured judge probe (100 samples)", "SimClaim sample plan", "experiments\\gpt_structured_judge_probe_v1\\", "no", "Requires GPT API key; results already frozen; do not rerun without API authorization"),
            ("run_external_gold_scifact_vitaminc_v1.py", "D:\\ocn\\scripts", "Run SciFact + VitaminC external gold eval", "external_gold data", "experiments\\external_gold_scifact_vitaminc_v1\\", "no", "Mainline experiment; results already frozen; do not rerun"),
            ("run_cese_ocn_lite_v3.py", "D:\\ocn\\scripts", "Run CESE-OCN lite v3 (R4 router)", "strict_silver data", "experiments\\mixed_framework_v2_frozen_r4_baseline\\", "no", "Main R4 runner; results already frozen; do not rerun"),
            ("run_mixed_framework_router_optimization_v2.py", "D:\\ocn\\scripts", "Run router optimization v2", "strict_silver data", "experiments\\mixed_framework_router_optimization_v2\\", "no", "Router optimization; results already frozen"),
            ("run_mixed_framework_new_algorithm_sweep_v1.py", "D:\\ocn\\scripts", "Run new algorithm sweep v1", "strict_silver data", "experiments\\mixed_framework_new_algorithm_sweep_v1\\", "no", "Algorithm sweep; results already frozen"),
            ("build_paper_ready_mixed_framework_v2.py", "D:\\ocn\\scripts", "Build paper-ready result pack for mixed framework v2", "R4 frozen results + sweep results", "experiments\\paper_ready_mixed_framework_v2\\", "no", "Paper-ready pack builder; output already frozen"),
            ("build_v3_external_gold_llm_plan_v1.py", "D:\\ocn\\scripts", "Build external gold/LLM baseline plan", "V3.1 sources", "experiments\\v3_external_gold_llm_plan_v1\\", "no", "Plan builder; output already frozen"),
            ("build_script_cleanup_v1.py", "D:\\ocn\\scripts", "This script cleanup tool", "scripts directory", "Archive moves + manifests", "yes", "Reference only; cleanup already done"),
        ]
        for entry in registry_entries:
            writer.writerow(entry)
    print(f"\nWrote {registry_path}")

    # Generate script_archive_manifest.csv
    manifest_path = os.path.join(INDEX_DIR, "script_archive_manifest.csv")
    with open(manifest_path, 'w', encoding='utf-8', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(["script_name", "old_location", "archive_location", "archive_category", "reason_archived", "notes"])
        for (f, old_path, archive_path, category, reason) in moves:
            writer.writerow([f, old_path, archive_path, category, reason, ""])
    print(f"Wrote {manifest_path} ({len(moves)} entries)")

    # Print summary
    by_category = defaultdict(int)
    for (_, _, _, category, _) in moves:
        by_category[category] += 1
    print("\n=== Archive summary ===")
    for cat, cnt in sorted(by_category.items()):
        print(f"  {cat}: {cnt}")
    print(f"\nKept in scripts/: {len(keep)}")
    for (f, _) in keep:
        print(f"  {f}")

    return before_count, after_count, keep, moves


if __name__ == '__main__':
    main()
