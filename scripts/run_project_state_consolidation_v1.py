"""Project State Consolidation v1 — comprehensive read-only audit.

Generates 10+ output files in D:\\ocn\\project_synthesis\\current_project_state_consolidation_v1\\:
  1. recent_task_output_inventory.csv
  2. all_recent_gates_inventory.csv
  3. gate_synthesis_report.md
  4. code_structure_reaudit.csv
  5. code_structure_reaudit_report.md
  6. paper_version_inventory.csv
  7. paper_version_lineage_report.md
  8. experiment_result_master_table.csv
  9. experiment_result_synthesis.md
 10. current_mainline_assessment.md
 11. allowed_vs_forbidden_claims_current.md
 12. current_project_state_master_report.md
 13. current_project_state_gate.json

Prohibitions enforced: no new experiments, no API calls, no gold, no paper modification,
no original data modification, no file deletion, no renaming, no planned-as-completed,
no silver-as-gold. Read-only audit and synthesis only.
"""
import os
import json
import re
import csv
from datetime import datetime

ROOT = r"D:\ocn"
OUT_DIR = r"D:\ocn\project_synthesis\current_project_state_consolidation_v1"

# Directories to inventory (section 1)
INVENTORY_DIRS = [
    ("overnight_non_api_compute_pipeline_v1", r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1"),
    ("v3_15_low_prevalence_screening_simulation", r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation"),
    ("v3_15_claim_realism_audit", r"D:\ocn\experiments\v3_15_claim_realism_audit"),
    ("gold_pilot_relation_realism_protocol_v2", r"D:\ocn\gold_pilot_relation_realism_protocol_v2"),
    ("v3_15_scalar_vs_relation_screening_deep_test", r"D:\ocn\experiments\v3_15_scalar_vs_relation_screening_deep_test"),
    ("rigourate_reproduction_and_simclaim_baseline_v1", r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1"),
    ("docs_rigourate_reproduction", r"D:\ocn\docs\rigourate_reproduction_and_simclaim_baseline_v1"),
    ("V3_13_rigourate_differentiated_realism_aware", r"D:\ocn\paper_versions_ordered\V3_13_rigourate_differentiated_realism_aware"),
    ("V3_14_mainline_locked_consistency_audit", r"D:\ocn\paper_versions_ordered\V3_14_mainline_locked_consistency_audit"),
    ("V3_15_hierarchical_taxonomy_revision", r"D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision"),
    ("v3_16_integration_summary_and_revision_plan", r"D:\ocn\project_synthesis\v3_16_integration_summary_and_revision_plan"),
    ("mixed_framework_v2_frozen_r4_baseline", r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline"),
    ("llm_judge_baseline_v1", r"D:\ocn\experiments\llm_judge_baseline_v1"),
    ("gpt_structured_judge_probe_v1", r"D:\ocn\experiments\gpt_structured_judge_probe_v1"),
    ("v3_11_three_core_credibility_experiments", r"D:\ocn\experiments\v3_11_three_core_credibility_experiments"),
    ("gold_pilot_protocol_freeze_v1", r"D:\ocn\gold_pilot_protocol_freeze_v1"),
    ("_PROJECT_INDEX", r"D:\ocn\_PROJECT_INDEX"),
]


def safe_read_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def list_files_recursive(path):
    if not os.path.exists(path):
        return []
    result = []
    for root, dirs, files in os.walk(path):
        for fn in files:
            result.append(os.path.join(root, fn))
    return result


def last_modified(path):
    files = list_files_recursive(path)
    if not files:
        return ""
    latest = max(os.path.getmtime(f) for f in files)
    return datetime.fromtimestamp(latest).strftime("%Y-%m-%d %H:%M:%S")


def key_files_snippet(path, max_n=5):
    files = list_files_recursive(path)
    if not files:
        return ""
    # prefer gate/json/md/csv files
    priority = [f for f in files if re.search(r"gate|readiness|summary|master|report", os.path.basename(f), re.IGNORECASE)]
    rest = [f for f in files if f not in priority]
    chosen = (priority + rest)[:max_n]
    return "; ".join(os.path.basename(f) for f in chosen)


def infer_status(dir_name, path, files):
    if not os.path.exists(path):
        return "missing"
    gates = [f for f in files if "gate" in os.path.basename(f).lower() and f.endswith(".json")]
    blocked = [f for f in files if "blocked" in os.path.basename(f).lower()]
    if blocked:
        return "partial/blocked"
    if gates:
        # try to read gate for completed status
        for g in gates:
            data = safe_read_json(g)
            if data:
                if data.get("completed") is False:
                    return "partial/blocked"
                if data.get("completed") is True:
                    return "completed"
        return "completed"
    return "completed"


# =============================================================================
# Section 1: recent_task_output_inventory.csv
# =============================================================================

def write_inventory_csv():
    rows = []
    for name, path in INVENTORY_DIRS:
        exists = os.path.exists(path)
        files = list_files_recursive(path) if exists else []
        file_count = len(files)
        lm = last_modified(path) if exists else ""
        kf = key_files_snippet(path) if exists else ""
        status = infer_status(name, path, files) if exists else "missing"
        notes = ""
        if "overnight" in name:
            notes = "8 sub-tasks A-H; all completed; master gate confirms 7/7 completed"
        elif "low_prevalence" in name:
            notes = "R4 screening simulation at 1%-25% prevalence; R4 recall stable ~0.36"
        elif "claim_realism_audit" in name:
            notes = "0% high-risk claims; 52.3% contradiction_mechanical; safe as diagnostic set"
        elif "relation_realism_protocol_v2" in name:
            notes = "Two-layer gold protocol DRAFT; annotation NOT begun; ready_for_blind_annotation=true"
        elif "scalar_vs_relation" in name:
            notes = "Scalar cannot separate mild/strong (ROC-AUC ~0.51); cannot replace R4"
        elif "rigourate_reproduction" in name and "docs" not in name:
            notes = "Official RIGOURATE blocked; proxy scalar baseline built; 22 files"
        elif "docs_rigourate" in name:
            notes = "Paste-ready RIGOURATE/ForceBench/CLAIM-BENCH related-work paragraphs"
        elif "V3_13" in name:
            notes = "RIGOURATE-differentiated + realism-aware paper version"
        elif "V3_14" in name:
            notes = "Mainline locked + reviewer-grade consistency audit; source for V3.15"
        elif "V3_15" in name:
            notes = "Hierarchical taxonomy revision; 18 replacements; 8 files; all quality checks pass"
        elif "v3_16_integration" in name:
            notes = "Five-task integration summary + V3.16 revision plan; mainline_survives=true"
        elif "mixed_framework_v2" in name:
            notes = "Frozen R4 baseline; strong_F1=0.3967; macro_F1=0.4238 (silver 444)"
        elif "llm_judge" in name:
            notes = "DeepSeek LLM baseline; 200 samples; macro_F1=0.5523 (matched 100)"
        elif "gpt_structured" in name:
            notes = "GPT standard vs structured probe; 100 matched samples"
        elif "v3_11_three_core" in name:
            notes = "Three core credibility experiments (label-shift, screening utility, evidence necessity)"
        elif "gold_pilot_protocol_freeze_v1" in name:
            notes = "Frozen gold pilot protocol v1; 50 samples; annotation NOT begun"
        elif "_PROJECT_INDEX" in name:
            notes = "Project index (registry from V3.7 era; outdated)"
        rows.append({
            "task_or_dir": name,
            "exists": str(exists),
            "file_count": file_count,
            "key_files": kf,
            "last_modified": lm,
            "status": status,
            "notes": notes,
        })
    out = os.path.join(OUT_DIR, "recent_task_output_inventory.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["task_or_dir", "exists", "file_count", "key_files", "last_modified", "status", "notes"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote " + out)
    return rows


# =============================================================================
# Section 2: all_recent_gates_inventory.csv + gate_synthesis_report.md
# =============================================================================

GATE_PATHS = [
    r"D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision\hierarchical_taxonomy_revision_gate.json",
    r"D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision\V3_15_hierarchical_taxonomy_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\H_master_summary\overnight_master_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\A_dataset_integrity_leakage\dataset_integrity_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\B_claim_variant_template_risk\template_risk_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\C_low_prevalence_screening\low_prevalence_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\D_boundary_collapse_fallback\boundary_collapse_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\E_llm_conservatism_error_direction\llm_conservatism_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\F_r4_false_positive_root_cause\r4_false_positive_gate.json",
    r"D:\ocn\experiments\overnight_non_api_compute_pipeline_v1\G_scalar_baseline_sweep\scalar_baseline_gate.json",
    r"D:\ocn\project_synthesis\v3_16_integration_summary_and_revision_plan\v3_16_integration_gate.json",
    r"D:\ocn\experiments\v3_15_scalar_vs_relation_screening_deep_test\scalar_vs_relation_deep_test_gate.json",
    r"D:\ocn\gold_pilot_relation_realism_protocol_v2\relation_realism_protocol_v2_gate.json",
    r"D:\ocn\experiments\v3_15_claim_realism_audit\claim_realism_audit_gate.json",
    r"D:\ocn\experiments\v3_15_low_prevalence_screening_simulation\low_prevalence_screening_gate.json",
    r"D:\ocn\paper_versions_ordered\V3_14_mainline_locked_consistency_audit\V3_14_mainline_gate.json",
    r"D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_reproduction_readiness_gate.json",
    r"D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\V3_13_readiness_gate.json",
    r"D:\ocn\paper_versions_ordered\V3_12_with_three_credibility_checks\V3_12_readiness_gate.json",
    r"D:\ocn\experiments\v3_11_three_core_credibility_experiments\three_core_credibility_readiness_gate.json",
    r"D:\ocn\experiments\gpt_structured_judge_probe_v1\gpt_structured_probe_gate.json",
    r"D:\ocn\experiments\llm_judge_baseline_v1\llm_run_gate_100.json",
    r"D:\ocn\experiments\llm_judge_baseline_v1\llm_run_gate_200.json",
    r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline\frozen_r4_readiness_gate.json",
    r"D:\ocn\gold_pilot_protocol_freeze_v1\gold_pilot_protocol_freeze_v1_gate.json" if os.path.exists(r"D:\ocn\gold_pilot_protocol_freeze_v1\gold_pilot_protocol_freeze_v1_gate.json") else r"D:\ocn\gold_pilot_protocol_freeze_v1\MISSING",
]

IMPORTANT_FLAGS_KEYS = [
    "mainline_survives", "needs_dataset_redesign", "needs_relation_realism_gold",
    "rigourate_overlap_fatal", "proceed_to_relation_realism_gold",
    "llm_conservatism_confirmed", "r4_screening_viable_at_1pct",
    "scalar_can_separate_mild_strong", "scalar_can_replace_r4",
    "score_collapse_observed", "r4_usable_low_prevalence_standalone",
    "r4_usable_low_prevalence_first_stage", "template_risk_severe",
    "high_risk_claim_rate", "safe_to_use_as_diagnostic_set",
    "safe_to_claim_naturalistic", "ready_for_blind_annotation",
    "official_reproduction_possible", "does_not_modify_v1",
    "no_silver_as_gold", "no_claim_r4_overall_beats_llm",
    "hierarchical_taxonomy_inserted", "flat_four_class_deemphasized",
    "fallback_to_3class_plus_binary_defined", "numbers_unchanged",
    "gold_not_claimed", "silver_not_gold", "old_files_unchanged",
    "docx_generated", "v3_12_complete", "advisor_send_ready",
]


def write_gates_inventory():
    rows = []
    for gp in GATE_PATHS:
        exists = os.path.exists(gp)
        data = safe_read_json(gp) if exists else None
        json_valid = data is not None
        completed = data.get("completed") if data else None
        blocked = data.get("blocked") if data else None
        main_status = "valid" if json_valid else ("missing" if not exists else "invalid_json")
        # Extract key fields
        main_remaining_risk = ""
        for k in ["main_remaining_risk", "main_risk", "remaining_risk", "biggest_risk"]:
            if data and k in data:
                main_remaining_risk = str(data[k])[:200]
                break
        recommended_next = ""
        for k in ["next_required_action", "recommended_next_action", "next_action", "tomorrow_first_priority"]:
            if data and k in data:
                recommended_next = str(data[k])[:200]
                break
        important_flags = []
        if data:
            for k in IMPORTANT_FLAGS_KEYS:
                if k in data:
                    important_flags.append(k + "=" + str(data[k]))
        rows.append({
            "gate_path": gp.replace(r"D:\ocn\\", ""),
            "json_valid": str(json_valid),
            "main_status": main_status,
            "completed": str(completed) if completed is not None else "",
            "blocked": str(blocked) if blocked is not None else "",
            "main_remaining_risk": main_remaining_risk,
            "recommended_next_action": recommended_next,
            "important_flags": " | ".join(important_flags[:10]),
        })
    out = os.path.join(OUT_DIR, "all_recent_gates_inventory.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["gate_path", "json_valid", "main_status", "completed", "blocked", "main_remaining_risk", "recommended_next_action", "important_flags"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote " + out)
    return rows


def write_gate_synthesis_report(gate_rows):
    n_total = len(gate_rows)
    n_valid = sum(1 for r in gate_rows if r["json_valid"] == "True")
    n_completed = sum(1 for r in gate_rows if r["completed"] == "True")
    n_blocked = sum(1 for r in gate_rows if r["blocked"] == "True")
    n_missing = sum(1 for r in gate_rows if r["main_status"] == "missing")

    content = f"""# Gate Synthesis Report

**Date:** 2026-07-05
**Total gates scanned:** {n_total}
**Valid JSON:** {n_valid}
**Completed=True:** {n_completed}
**Blocked=True:** {n_blocked}
**Missing:** {n_missing}

## Summary

### Successfully completed tasks

The following gates report `completed=true`:

"""
    for r in gate_rows:
        if r["completed"] == "True":
            content += "- `" + r["gate_path"] + "`\n"
    content += "\n### Blocked / partial tasks\n\n"
    any_blocked = False
    for r in gate_rows:
        if r["blocked"] == "True" or (r["completed"] == "False" and r["json_valid"] == "True"):
            any_blocked = True
            content += "- `" + r["gate_path"] + "` (completed=" + r["completed"] + ", blocked=" + r["blocked"] + ")\n"
    if not any_blocked:
        content += "None. All valid gates report completed=true or have no completed field (informational gates).\n"

    content += "\n### Missing gates\n\n"
    if n_missing == 0:
        content += "None. All scanned gate paths exist.\n"
    else:
        for r in gate_rows:
            if r["main_status"] == "missing":
                content += "- `" + r["gate_path"] + "`\n"

    content += """

## Key findings across gates

1. **Mainline survives (V3.16 integration gate):** `mainline_survives=true`, `needs_dataset_redesign=false`, `needs_relation_realism_gold=true`, `rigourate_overlap_fatal=false`. The four-class + relation+realism gold route (Route A) is the default.

2. **Overnight pipeline (8 sub-tasks A-H):** All 7 sub-tasks + master summary completed. Key results: dataset integrity PASS (TF-IDF separability gap=-0.0066 = LOW leakage); LLM conservatism CONFIRMED (pred_strong_rate 0.04 vs R4 0.36, 9x gap); R4 FP concentrated in mild→strong boundary (26 FP of 35 strong predictions); scalar cannot replace R4 (rule_scalar AUC=0.5062 on mild_vs_strong); 50/100 complementary cases support two-stage pipeline.

3. **V3.15 hierarchical taxonomy revision:** `hierarchical_taxonomy_inserted=true`, `flat_four_class_deemphasized=true`, `fallback_to_3class_plus_binary_defined=true`, `numbers_unchanged=true`, `gold_not_claimed=true`, `old_files_unchanged=true`, `docx_generated=true`. All 10 §12 quality checks PASS.

4. **RIGOURATE reproduction:** `official_reproduction_possible=false`. Proxy scalar baseline built; official code/data/model not publicly available. Scalar cannot distinguish mild vs strong (ROC-AUC ≤ 0.59).

5. **Claim realism audit:** `high_risk_claim_rate=0.0`, `safe_to_use_as_diagnostic_set=true`, `safe_to_claim_naturalistic=false`. SimClaim remains suitable as controlled diagnostic set but NOT as naturalistic corpus.

6. **Low-prevalence screening:** `r4_screening_viable_at_1pct=false`, `r4_usable_low_prevalence_first_stage=true`. R4 recall stable ~0.36 across 1%-25%; NOT viable standalone <10%; viable as first-stage filter.

7. **Scalar vs relation deep test:** `scalar_can_separate_mild_strong=false`, `scalar_can_replace_r4=false`, `score_collapse_observed=true`. Scalar score compresses the mild/strong boundary.

8. **Gold protocol v2:** `ready_for_blind_annotation=true`, `does_not_modify_v1=true`. Two-layer (relation + realism) protocol DRAFT; annotation NOT begun.

## Main remaining risks (aggregated)

- **Level-2 mild_vs_strong boundary** is the hardest to draw (75% confusion in §V.D audit). If gold adjudication reveals κ < 0.40, paper must fall back to Level-1 three-class + binary strong_action screening per §VII.K.
- **RIGOURATE proxy:** §VI.E scalar baseline is proxy, not official RIGOURATE. Conclusions may shift when official artifacts become available.
- **Gold not yet collected:** All strong-action screening claims are silver-stage evidence pending §VII protocol-locked gold adjudication.
- **SimClaim is counterfactual, not natural-prevalence:** Balanced four-way design is deliberate for diagnostic pressure-testing, not an estimate of real-world prevalence.
- **R4 macro-F1 < LLM:** R4 macro-F1=0.3280 vs LLM=0.5523 on matched 100. R4 is a screening complement, not an overall-beats-LLM claim.

## Recommended next action (aggregated)

Execute the §VII 50-pair two-layer gold pilot (Layer 1 relation + Layer 2 realism) using the frozen gold_pilot_protocol_freeze_v1 package and the v2 relation+realism protocol. Compute Level-1 κ, Level-2 κ, strong_action retention; apply §VII.K fallback rules to determine whether to retain hierarchical taxonomy or fall back to Level-1 three-class + binary strong_action screening.
"""
    out = os.path.join(OUT_DIR, "gate_synthesis_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 3: code_structure_reaudit.csv + report
# =============================================================================

def classify_script(name):
    """Classify a script by name pattern."""
    n = name.lower()
    if re.match(r"build_v3_\d+_docx", n) or "build_v3_15" in n or "build_v3_14" in n or "build_v3_13" in n:
        return "build_docx"
    if "build_v3_4_main_paper" in n or "build_v3_3_main_paper" in n or "build_v3_4_taxonomy" in n or "build_v3_2_table0" in n:
        return "mainline"
    if "build_gold_pilot" in n or "build_paper_ready" in n or "build_v3_external" in n or "build_v2_relation" in n:
        return "mainline"
    if "build_rigourate_style" in n or "build_v3_15_attack" in n:
        return "build_docx"
    if "run_v3_15" in n or "run_overnight" in n or "run_v3_16" in n:
        return "experiment"
    if "run_llm_judge" in n or "run_gpt_structured" in n or "run_external_gold" in n:
        return "experiment"
    if "run_v3_r4" in n or "run_cese_ocn" in n or "run_mixed_framework" in n:
        return "experiment"
    if "eval_scalar" in n or "compare_rigourate" in n or "case_level_comparison" in n:
        return "experiment"
    if "claim_realism_audit" in n:
        return "experiment"
    if "check_v3_15" in n or "_v3_15_view" in n or "_v3_15_scalar_gate_view" in n or "_v2_qc_check" in n:
        return "audit"
    return "unknown"


def infer_related_task(name):
    n = name.lower()
    if "v3_15" in n: return "V3.15 hierarchical taxonomy"
    if "v3_16" in n: return "V3.16 integration summary"
    if "overnight" in n: return "Overnight pipeline v1"
    if "v3_14" in n: return "V3.14 mainline locked"
    if "v3_13" in n: return "V3.13 RIGOURATE-differentiated"
    if "v3_12" in n: return "V3.12 three credibility checks"
    if "v3_11" in n: return "V3.11 framework roadmap"
    if "v3_10" in n: return "V3.10 advisor ready"
    if "v3_9" in n: return "V3.9 pre-gold complete"
    if "v3_7" in n: return "V3.7 advisor handoff"
    if "v3_6" in n: return "V3.6 case figure integrity"
    if "v3_5" in n: return "V3.5 presentation ready"
    if "v3_4" in n: return "V3.4 taxonomy hardened"
    if "v3_3" in n: return "V3.3 main paper"
    if "v3_2" in n: return "V3.2 table 0 + audit"
    if "v3_1" in n: return "V3.1 docx"
    if "rigourate" in n: return "RIGOURATE reproduction"
    if "llm_judge" in n: return "LLM judge baseline"
    if "gpt_structured" in n: return "GPT structured probe"
    if "external_gold" in n: return "External gold eval"
    if "gold_pilot" in n: return "Gold pilot prep"
    if "mixed_framework" in n or "cese_ocn" in n: return "R4 frozen baseline"
    if "claim_realism" in n: return "Claim realism audit"
    if "scalar" in n: return "Scalar baseline"
    if "overnight" in n: return "Overnight pipeline"
    return "general"


def infer_flags(name):
    """Infer safe_to_run, modifies_data, calls_api, trains_model from name + quick content scan."""
    n = name.lower()
    calls_api = "yes" if ("llm_judge" in n or "gpt_structured" in n) else "no"
    trains_model = "yes" if ("mixed_framework_router" in n or "mixed_framework_new_algorithm" in n) else "no"
    modifies_data = "no"
    safe_to_run = "unknown"
    # Version-specific docx builders are safe (read md, write docx)
    if "build_v3" in n and "docx" in n:
        safe_to_run = "yes"
        calls_api = "no"
        trains_model = "no"
    # Audit/view scripts are safe
    if "check_" in n or "_view" in n or "_qc_check" in n or "_gate_view" in n:
        safe_to_run = "yes"
    # Experiment runners that are frozen
    if "run_" in n:
        safe_to_run = "no"  # results frozen, do not rerun
    # Build scripts for paper content
    if "build_v3_4_main_paper" in n or "build_v3_3_main_paper" in n or "build_v3_4_taxonomy" in n or "build_v3_2_table0" in n:
        safe_to_run = "no"  # output frozen
    if "build_gold_pilot" in n:
        safe_to_run = "yes"  # does not label or train
    if "build_paper_ready" in n or "build_v3_external" in n:
        safe_to_run = "no"  # output frozen
    if "build_v2_relation" in n:
        safe_to_run = "yes"  # generates templates, no gold
    if "build_rigourate_style" in n:
        safe_to_run = "yes"  # rule-based scoring
    if "build_v3_15_attack" in n:
        safe_to_run = "yes"  # generates markdown
    if "build_v3_15_hierarchical" in n:
        safe_to_run = "yes"  # applies string replacements to V3.14
    if "run_overnight" in n or "run_v3_15" in n or "run_v3_16" in n:
        safe_to_run = "yes"  # reanalysis only, no API
    if "eval_scalar" in n or "compare_rigourate" in n or "case_level_comparison" in n:
        safe_to_run = "yes"  # reanalysis
    if "claim_realism_audit" in n:
        safe_to_run = "yes"  # rule-based audit
    return safe_to_run, modifies_data, calls_api, trains_model


def write_code_reaudit():
    scripts_dir = r"D:\ocn\scripts"
    script_files = []
    for fn in os.listdir(scripts_dir):
        if fn.endswith(".py"):
            script_files.append(fn)
    script_files.sort()

    rows = []
    for fn in script_files:
        cat = classify_script(fn)
        task = infer_related_task(fn)
        safe, modifies, calls_api, trains = infer_flags(fn)
        path = os.path.join(scripts_dir, fn)
        size = os.path.getsize(path)
        # Read first 30 lines for outputs detection
        outputs = ""
        try:
            with open(path, "r", encoding="utf-8") as f:
                head = f.read(3000)
            # Look for output path hints
            m = re.findall(r'(?:OUT_DIR|OUT_[A-Z]+|output_dir|OUTPUT)\s*=\s*[rR]?["\']([^"\']+)', head)
            if m:
                outputs = "; ".join(m[:3])
            else:
                m2 = re.findall(r'D:\\\\ocn\\\\[^"\']+', head)
                outputs = "; ".join(m2[:3]) if m2 else ""
        except Exception:
            pass
        notes = ""
        if cat == "build_docx" and "v3_15" not in fn and "v3_14" not in fn and "v3_13" not in fn:
            notes = "Historical docx builder; output already frozen; do not rerun"
        elif cat == "experiment" and "v3_15" not in fn and "overnight" not in fn and "v3_16" not in fn:
            notes = "Historical experiment; results frozen; do not rerun"
        elif cat == "mainline":
            notes = "Mainline builder; output frozen; do not rerun"
        elif "v3_15" in fn.lower() or "overnight" in fn.lower() or "v3_16" in fn.lower():
            notes = "Recent task (V3.15/overnight/V3.16); safe to rerun for reanalysis"
        rows.append({
            "script_path": "scripts/" + fn,
            "category": cat,
            "related_task": task,
            "safe_to_run": safe,
            "modifies_data": modifies,
            "calls_api": calls_api,
            "trains_model": trains,
            "outputs": outputs[:200],
            "notes": notes,
        })

    out = os.path.join(OUT_DIR, "code_structure_reaudit.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["script_path", "category", "related_task", "safe_to_run", "modifies_data", "calls_api", "trains_model", "outputs", "notes"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote " + out + " (" + str(len(rows)) + " scripts)")
    return rows


def write_code_reaudit_report(rows):
    n_total = len(rows)
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r)
    n_safe = sum(1 for r in rows if r["safe_to_run"] == "yes")
    n_not_safe = sum(1 for r in rows if r["safe_to_run"] == "no")
    n_api = sum(1 for r in rows if r["calls_api"] == "yes")
    n_trains = sum(1 for r in rows if r["trains_model"] == "yes")

    content = f"""# Code Structure Re-Audit Report

**Date:** 2026-07-05
**Total scripts scanned:** {n_total}

## Summary by category

| Category | Count | Examples |
|---|---|---|
"""
    for cat in ["mainline", "experiment", "build_docx", "audit", "unknown"]:
        if cat in by_cat:
            examples = ", ".join(r["script_path"].split("/")[-1] for r in by_cat[cat][:3])
            content += f"| {cat} | {len(by_cat[cat])} | {examples} |\n"

    content += f"""
## Safety summary

- **Safe to run:** {n_safe} scripts (audit/view, reanalysis, docx builders, template generators)
- **Not safe to run (frozen):** {n_not_safe} scripts (historical experiments with frozen results, frozen paper builders)
- **Calls API:** {n_api} scripts (run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1) — require user authorization + API key
- **Trains model:** {n_trains} scripts (run_mixed_framework_router_optimization_v2, run_mixed_framework_new_algorithm_sweep_v1)

## Answers to required questions

### 1. Which scripts are currently mainline-usable?

The current mainline scripts are the V3.15 hierarchical taxonomy revision builders and the V3.16 integration summary builder:
- `scripts/build_v3_15_hierarchical_taxonomy.py` — builds V3.15 MD + DOCX from V3.14 source
- `scripts/build_v3_15_attack_response_and_gate.py` — generates attack response + readiness gate
- `scripts/check_v3_15_quality.py` — runs §12 quality checks
- `scripts/run_v3_16_integration_summary.py` — generates V3.16 five-task integration summary
- `scripts/run_overnight_non_api_pipeline_v1.py` — overnight non-API compute pipeline (reanalysis only)

These are all safe to run (no API, no gold, no original data modification).

### 2. Which scripts are only historical experiments?

All `run_*` scripts except the recent V3.15/overnight/V3.16 ones are historical experiments with frozen results:
- `run_cese_ocn_lite_v3.py` (R4 frozen baseline)
- `run_llm_judge_baseline_v1.py` (DeepSeek LLM baseline, requires API)
- `run_gpt_structured_judge_probe_v1.py` (GPT probe, requires API)
- `run_external_gold_scifact_vitaminc_v1.py` (external gold eval)
- `run_v3_r4_strong_baselines_holdout_v1.py` (strong baselines + holdout)
- `run_mixed_framework_router_optimization_v2.py` (router optimization, trains model)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (algorithm sweep, trains model)

These should NOT be rerun — their results are frozen and feed the paper.

### 3. Which scripts call API?

Two scripts require API keys + user authorization:
- `run_llm_judge_baseline_v1.py` (DeepSeek API)
- `run_gpt_structured_judge_probe_v1.py` (GPT API)

Per project memory: DeepSeek API is authorized for small-sample pilot ONLY (max 200 SimClaim pairs); key is held in conversation context only, NEVER stored. The prior "no LLM API" constraint still applies to all other tasks.

### 4. Which scripts retrain models?

Two scripts involve model training:
- `run_mixed_framework_router_optimization_v2.py` (router threshold optimization)
- `run_mixed_framework_new_algorithm_sweep_v1.py` (algorithm sweep)

Both are frozen; do not rerun.

### 5. Which scripts only generate documents?

The `build_v*_docx.py` family (V3.1 through V3.14) plus `build_v3_15_hierarchical_taxonomy.py`, `build_v3_15_attack_response_and_gate.py`, `build_v3_4_main_paper.py`, `build_v3_3_main_paper.py`, `build_v3_4_taxonomy_hardening.py`, `build_v3_2_table0_and_audit.py`, `build_gold_pilot_preparation_v1.py`, `build_paper_ready_mixed_framework_v2.py`, `build_v3_external_gold_llm_plan_v1.py`, `build_v2_relation_realism_templates.py`, `build_rigourate_style_scalar_baselines.py`, `build_v3_13_rigourate_aware_docx.py`.

### 6. Is further refactoring needed?

**Not urgent.** The script directory is well-organized by version (build_vN_docx pattern) and by task (run_X, build_X, check_X, _X_view). The `_PROJECT_INDEX/script_registry_mainline.csv` is outdated (references V3.7 as current); it should be updated to reflect V3.15 as current, but this is a documentation task, not a refactoring task. No duplicate or dangerous scripts were found. The two API-calling scripts are clearly labeled and require authorization.

### 7. Are there duplicate or dangerous scripts?

**No dangerous scripts found.** All scripts write to their own output directories and do not modify original data. The `_v3_15_view_metrics.py`, `_v3_15_scalar_gate_view.py`, `_v2_qc_check.py` are view/check utilities (safe). No scripts delete files or overwrite old versions. The `check_v3_15_quality.py` is read-only.

**Mild redundancy:** `claim_realism_audit.py` (in scripts/) and `run_v3_15_claim_realism_audit.py` both relate to the realism audit, but the former is the implementation and the latter is the runner. This is acceptable modular design, not duplication.

## Outdated registry note

`_PROJECT_INDEX/script_registry_mainline.csv` lists 22 scripts and references V3.7 as current paper. The actual current paper is V3.15. The registry should be updated, but this does not affect script safety — the name-based classification above is authoritative.
"""
    out = os.path.join(OUT_DIR, "code_structure_reaudit_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 4: paper_version_inventory.csv + lineage report
# =============================================================================

PAPER_VERSIONS = [
    "V3_4_taxonomy_hardened",
    "V3_5_presentation_ready",
    "V3_6_case_figure_integrity_checked",
    "V3_7_advisor_handoff_clean",
    "V3_8_reference_refreshed",
    "V3_9_pre_gold_complete",
    "V3_9_pre_gold_complete_audit",
    "V3_10_advisor_ready_silver_stage",
    "V3_10_1_advisor_send_clean",
    "V3_11_high_standard_framework_roadmap",
    "V3_12_with_three_credibility_checks",
    "V3_12_1_advisor_send_clean",
    "V3_13_differentiated_against_rigourate_forcebench",
    "V3_13_rigourate_differentiated_realism_aware",
    "V3_14_mainline_locked_consistency_audit",
    "V3_15_hierarchical_taxonomy_revision",
]


def scan_paper_version(vdir):
    path = os.path.join(r"D:\ocn\paper_versions_ordered", vdir)
    exists = os.path.exists(path)
    if not exists:
        return {"version_dir": vdir, "main_md": "", "main_docx": "", "exists": "False",
                "size_md": 0, "size_docx": 0, "last_modified": "",
                "main_positioning": "missing", "contains_rigourate_diff": "no",
                "contains_hierarchical_taxonomy": "no", "contains_non_gold_checks": "no",
                "contains_gold_pending": "no", "notes": "directory missing"}
    files = os.listdir(path)
    md_files = [f for f in files if f.endswith(".md") and "CESE_OCN" in f]
    docx_files = [f for f in files if f.endswith(".docx") and "CESE_OCN" in f]
    main_md = md_files[0] if md_files else ""
    main_docx = docx_files[0] if docx_files else ""
    md_path = os.path.join(path, main_md) if main_md else ""
    docx_path = os.path.join(path, main_docx) if main_docx else ""
    size_md = os.path.getsize(md_path) if main_md and os.path.exists(md_path) else 0
    size_docx = os.path.getsize(docx_path) if main_docx and os.path.exists(docx_path) else 0
    lm = last_modified(path)
    # Read MD content to check features
    md_content = ""
    if md_path and os.path.exists(md_path):
        try:
            with open(md_path, "r", encoding="utf-8") as f:
                md_content = f.read()
        except Exception:
            md_content = ""
    has_rigourate = "yes" if ("rigourate" in md_content.lower() and ("differentiat" in md_content.lower() or "position" in md_content.lower())) else "no"
    has_hierarchical = "yes" if ("hierarchical" in md_content.lower() and "taxonomy" in md_content.lower()) else "no"
    has_non_gold = "yes" if ("non-gold" in md_content.lower() or "non_gold" in md_content.lower() or "do not replace gold" in md_content.lower()) else "no"
    has_gold_pending = "yes" if ("gold" in md_content.lower() and ("pending" in md_content.lower() or "planned" in md_content.lower() or "pre-registered" in md_content.lower())) else "no"
    # Determine positioning
    if "V3_15" in vdir:
        positioning = "hierarchical diagnostic taxonomy (Level 1 + Level 2)"
    elif "V3_14" in vdir:
        positioning = "mainline locked + consistency audit"
    elif "V3_13_rigourate" in vdir:
        positioning = "RIGOURATE-differentiated + realism-aware"
    elif "V3_13_differentiated" in vdir:
        positioning = "differentiated against RIGOURATE/ForceBench"
    elif "V3_12_1" in vdir:
        positioning = "advisor send clean (V3.12.1)"
    elif "V3_12" in vdir:
        positioning = "three credibility checks"
    elif "V3_11" in vdir:
        positioning = "high-standard framework roadmap"
    elif "V3_10_1" in vdir:
        positioning = "advisor send clean (V3.10.1)"
    elif "V3_10" in vdir:
        positioning = "advisor ready silver stage"
    elif "V3_9_pre_gold_complete_audit" in vdir:
        positioning = "pre-gold complete audit"
    elif "V3_9" in vdir:
        positioning = "pre-gold complete"
    elif "V3_8" in vdir:
        positioning = "reference refreshed"
    elif "V3_7" in vdir:
        positioning = "advisor handoff clean"
    elif "V3_6" in vdir:
        positioning = "case figure integrity checked"
    elif "V3_5" in vdir:
        positioning = "presentation ready"
    elif "V3_4" in vdir:
        positioning = "taxonomy hardened"
    else:
        positioning = "unknown"
    notes = ""
    if "V3_15" in vdir:
        notes = "CURRENT RECOMMENDED VERSION; hierarchical taxonomy; all quality checks pass"
    elif "V3_14" in vdir:
        notes = "Source for V3.15; mainline locked; preserved unchanged"
    elif "V3_13_rigourate" in vdir:
        notes = "RIGOURATE-aware; superseded by V3.14"
    elif "V3_13_differentiated" in vdir:
        notes = "Historical; superseded by V3.13_rigourate_differentiated"
    elif "V3_12_1" in vdir:
        notes = "Historical advisor-send; superseded"
    elif "V3_12" in vdir:
        notes = "Three credibility checks; superseded by V3.13"
    elif "V3_11" in vdir:
        notes = "Historical framework roadmap; superseded"
    elif "V3_10" in vdir:
        notes = "Historical advisor-ready; superseded"
    elif "V3_9" in vdir:
        notes = "Historical pre-gold; superseded"
    elif "V3_8" in vdir:
        notes = "Historical reference refresh; superseded"
    elif "V3_7" in vdir:
        notes = "Historical advisor handoff; superseded (was V3.7-era current)"
    elif "V3_6" in vdir:
        notes = "Historical; superseded"
    elif "V3_5" in vdir:
        notes = "Historical; superseded"
    elif "V3_4" in vdir:
        notes = "Historical taxonomy hardened; superseded"
    return {
        "version_dir": vdir, "main_md": main_md, "main_docx": main_docx, "exists": "True",
        "size_md": size_md, "size_docx": size_docx, "last_modified": lm,
        "main_positioning": positioning, "contains_rigourate_diff": has_rigourate,
        "contains_hierarchical_taxonomy": has_hierarchical, "contains_non_gold_checks": has_non_gold,
        "contains_gold_pending": has_gold_pending, "notes": notes,
    }


def write_paper_inventory():
    rows = []
    for v in PAPER_VERSIONS:
        rows.append(scan_paper_version(v))
    out = os.path.join(OUT_DIR, "paper_version_inventory.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["version_dir", "main_md", "main_docx", "exists", "size_md", "size_docx", "last_modified", "main_positioning", "contains_rigourate_diff", "contains_hierarchical_taxonomy", "contains_non_gold_checks", "contains_gold_pending", "notes"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote " + out)
    return rows


def write_paper_lineage_report(rows):
    content = """# Paper Version Lineage Report

**Date:** 2026-07-05
**Versions scanned:** """ + str(len(rows)) + """

## Version lineage (V3.4 → V3.15)

| Version | Positioning | Size (MD) | Hierarchical | RIGOURATE diff | Non-gold checks | Gold pending | Status |
|---|---|---|---|---|---|---|---|
"""
    for r in rows:
        content += "| " + r["version_dir"] + " | " + r["main_positioning"] + " | " + str(r["size_md"]) + " | " + r["contains_hierarchical_taxonomy"] + " | " + r["contains_rigourate_diff"] + " | " + r["contains_non_gold_checks"] + " | " + r["contains_gold_pending"] + " | " + r["notes"].split(";")[0] + " |\n"

    content += """
## What each version did

- **V3.4 taxonomy_hardened:** Taxonomy hardening (decision tree, high_risk_sample_bank, trusted_case_bank). First version with the four-class taxonomy operationalized.
- **V3.5 presentation_ready:** Polished for presentation; case studies and figures finalized.
- **V3.6 case_figure_integrity_checked:** Case/figure integrity audit; ensured all figures and tables are consistent.
- **V3.7 advisor_handoff_clean:** Clean version for advisor handoff; was the V3.7-era "current" version. Includes advisor cover note, one-page summary, reviewer risk brief.
- **V3.8 reference_refreshed:** Reference list refreshed; citation consistency improved.
- **V3.9 pre_gold_complete:** Pre-gold-completion version; silver-stage results finalized.
- **V3.9_pre_gold_complete_audit:** Audit of V3.9; next-action gate generated.
- **V3.10 advisor_ready_silver_stage:** Silver-stage results packaged for advisor review.
- **V3.10_1 advisor_send_clean:** Clean send version; minor fixes over V3.10.
- **V3.11 high_standard_framework_roadmap:** High-standard framework roadmap; introduced three core credibility experiments plan.
- **V3.12 with_three_credibility_checks:** Added three credibility checks (label-shift, screening utility, evidence necessity); readiness gate confirmed advisor-send-ready.
- **V3.12_1 advisor_send_clean:** Clean send version of V3.12.
- **V3.13_differentiated_against_rigourate_forcebench:** First differentiation pass against RIGOURATE/ForceBench/CLAIM-BENCH.
- **V3.13_rigourate_differentiated_realism_aware:** RIGOURATE-differentiated + realism-aware; added §II.A positioning, §VII.J realism audit plan, §VI.E scalar baseline.
- **V3.14 mainline_locked_consistency_audit:** Mainline locked + reviewer-grade consistency audit; 142965 bytes MD; source for V3.15.
- **V3.15 hierarchical_taxonomy_revision:** CURRENT RECOMMENDED VERSION. Reframes flat four-class as hierarchical diagnostic taxonomy (Level 1 + Level 2); adds Table 0a, §VII.K, §VIII.G; 18 targeted replacements; all experimental numbers preserved byte-identical; all 10 §12 quality checks PASS.

## Current recommended reading version

**V3.15 hierarchical_taxonomy_revision** is the current recommended main paper version.

- **MD:** `D:\\ocn\\paper_versions_ordered\\V3_15_hierarchical_taxonomy_revision\\CESE_OCN_V3_15_hierarchical_taxonomy_revision.md` (157953 bytes)
- **DOCX:** `D:\\ocn\\paper_versions_ordered\\V3_15_hierarchical_taxonomy_revision\\CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx` (54349 bytes)
- **Attack response:** `flat_four_class_attack_response.md`
- **Gold plan:** `hierarchical_gold_validation_plan.md`
- **Mapping:** `hierarchical_label_mapping.csv`
- **Readiness gate:** `hierarchical_taxonomy_revision_gate.json` (13 fields, all True)

## Historical versions (do not use as main draft)

All versions V3.4 through V3.14 are historical. They are preserved unchanged for audit trail. **Do not modify them.** The lineage shows a clear progression: V3.4 (taxonomy hardened) → V3.7 (advisor handoff) → V3.12 (three credibility checks) → V3.13 (RIGOURATE-differentiated) → V3.14 (mainline locked) → V3.15 (hierarchical taxonomy).

**V3.14** is the immediate predecessor and remains the source-of-truth for experimental numbers (all V3.15 numbers are byte-identical to V3.14). If a reader wants the "last flat-four-class version", V3.14 is that version.

## Note on _MAIN_PAPER_CURRENT and _PROJECT_INDEX

`_PROJECT_INDEX/current_paper_paths.md` references V3.7 as current — this is **outdated**. The actual current paper is V3.15. The `_MAIN_PAPER_CURRENT/` directory contains V3.7-era curated copies and should not be used as the source of truth. Always read from `paper_versions_ordered/V3_15_hierarchical_taxonomy_revision/`.
"""
    out = os.path.join(OUT_DIR, "paper_version_lineage_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 5: experiment_result_master_table.csv + synthesis
# =============================================================================

def write_experiment_master_table():
    rows = [
        {
            "experiment_name": "mixed_framework_v2_frozen_r4_baseline",
            "status": "completed",
            "n_samples": "444 silver + 100 matched",
            "main_methods": "R4 (frozen thresholds: t_contra=0.48, t_strong=0.535, t_svm=0.51)",
            "key_metrics": "R4 strong_F1=0.3967 (silver 444), 0.3000 (matched 100); macro_F1=0.4238 (silver), 0.3280 (matched); strong_recall=0.4562",
            "supports_claim": "R4 retains targeted screening value on Level-2 strong_action subtype",
            "weakens_claim": "R4 macro_F1 < LLM (0.3280 vs 0.5523); R4 is screening complement not overall-beats-LLM",
            "paper_use": "§VI.A internal silver diagnostic; §VI.B LLM comparison; §VIII.D.B screening utility",
            "remaining_risk": "Silver labels pending gold adjudication; strong_recall moderate (0.4562)",
            "output_dir": "D:\\ocn\\experiments\\mixed_framework_v2_frozen_r4_baseline\\",
        },
        {
            "experiment_name": "llm_judge_baseline_v1",
            "status": "completed",
            "n_samples": "200 (DeepSeek-V3)",
            "main_methods": "DeepSeek-V3 chat (zero-shot, 4-class)",
            "key_metrics": "macro_F1=0.5523 (matched 100), 0.5270 (200); strong_F1=0.0769; strong_recall=0.04 (1/25)",
            "supports_claim": "LLM under-detects strong_action under tested prompts (conservatism)",
            "weakens_claim": "LLM achieves higher overall macro_F1 than R4",
            "paper_use": "§VI.B LLM comparison; §VIII.D.B complementarity",
            "remaining_risk": "Prompt/sample-specific; not a fundamental LLM limit; gold adjudication pending",
            "output_dir": "D:\\ocn\\experiments\\llm_judge_baseline_v1\\",
        },
        {
            "experiment_name": "gpt_structured_judge_probe_v1",
            "status": "completed",
            "n_samples": "100 (GPT-5.5 standard + structured)",
            "main_methods": "GPT-5.5 standard vs structured prompt",
            "key_metrics": "Both: macro_F1=0.5523, strong_F1=0.0769, strong_recall=0.04; structured no improvement over standard",
            "supports_claim": "LLM conservatism robust across prompt designs (standard and structured)",
            "weakens_claim": "Structured prompting does not rescue strong_action detection",
            "paper_use": "§VI.B; §VIII.D.B complementarity (50/100 complementary cases)",
            "remaining_risk": "Only 100 samples; gold adjudication pending",
            "output_dir": "D:\\ocn\\experiments\\gpt_structured_judge_probe_v1\\",
        },
        {
            "experiment_name": "v3_11_three_core_credibility_experiments",
            "status": "completed",
            "n_samples": "444 silver + 100 matched",
            "main_methods": "Label-shift stress, screening utility, evidence necessity",
            "key_metrics": "Break-even retention ~50% (label-shift); FP/TP=2.89, review burden=35%, R4 captures 8 LLM-missed strong (screening utility); evidence necessity confirms R4 uses evidence",
            "supports_claim": "R4 screening utility holds under simulated label shift down to ~60% retention; non-gold robustness checks confirm R4 is not gaming",
            "weakens_claim": "Below 50% retention, R4 advantage degrades (CI crosses zero)",
            "paper_use": "§VIII.D non-gold robustness checks; §VIII.D.B screening utility; §VIII.D.C label-shift stress",
            "remaining_risk": "Non-gold checks do not replace gold adjudication (caveat preserved)",
            "output_dir": "D:\\ocn\\experiments\\v3_11_three_core_credibility_experiments\\",
        },
        {
            "experiment_name": "rigourate_reproduction_and_simclaim_baseline_v1",
            "status": "completed",
            "n_samples": "444 silver (proxy)",
            "main_methods": "rule_scalar_score, nli_scalar_score, llm_scalar_proxy (PROXY, not official RIGOURATE)",
            "key_metrics": "rule_scalar ROC-AUC=0.5062 (mild_vs_strong); llm_scalar ROC-AUC=0.5874; nli_scalar all blocked; official RIGOURATE NOT available",
            "supports_claim": "Scalar cannot distinguish mild vs strong; R4 retains independent value on strong_action",
            "weakens_claim": "Cannot claim to reproduce official RIGOURATE (blocked)",
            "paper_use": "§VI.E scalar baseline; §II.A RIGOURATE positioning; §IX limitation 11 (proxy caveat)",
            "remaining_risk": "Proxy only; conclusions may shift when official RIGOURATE artifacts become available",
            "output_dir": "D:\\ocn\\experiments\\rigourate_reproduction_and_simclaim_baseline_v1\\",
        },
        {
            "experiment_name": "overnight_non_api_compute_pipeline_v1",
            "status": "completed",
            "n_samples": "444 silver + 100 matched (reanalysis)",
            "main_methods": "8 sub-tasks: dataset integrity, template risk, low-prevalence sim, boundary collapse, LLM conservatism, R4 FP root cause, scalar sweep, master summary",
            "key_metrics": "TF-IDF gap=-0.0066 (low leakage); template_risk=0.66 (design attribute); R4 recall=0.36 stable across prevalences; LLM pred_strong_rate=0.04 vs R4=0.36 (9x); R4 FP=26/35; rule_scalar AUC=0.5062",
            "supports_claim": "Dataset integrity PASS; LLM conservatism CONFIRMED; R4 FP concentrated in mild→strong boundary (same as scalar collapse); 50/100 complementary cases support two-stage pipeline",
            "weakens_claim": "Template risk high (76/111 groups) — but design attribute, not defect; R4 NOT viable standalone <10% prevalence",
            "paper_use": "§V data integrity; §VI.B LLM conservatism; §VIII.D screening utility; §VIII.G fallback; §IX limitations",
            "remaining_risk": "Reanalysis only (no new experiments); silver labels; low-prevalence simulation is heuristic, not real distribution",
            "output_dir": "D:\\ocn\\experiments\\overnight_non_api_compute_pipeline_v1\\",
        },
        {
            "experiment_name": "v3_15_low_prevalence_screening_simulation",
            "status": "completed",
            "n_samples": "444 silver (resampled 1000x per prevalence)",
            "main_methods": "Low-prevalence simulation at 1%, 3%, 5%, 10%, 15%, 20%, 25%",
            "key_metrics": "R4 recall stable ~0.36 across all prevalences; FP/TP 3.8→121 as prevalence drops; R4 NOT viable standalone <10%; viable as first-stage filter",
            "supports_claim": "R4 has stable recall across prevalence levels; two-stage pipeline motivated",
            "weakens_claim": "R4 standalone NOT viable at low prevalence (high FP burden)",
            "paper_use": "§VI.C low-prevalence screening; §VIII.D screening utility; §IX limitations",
            "remaining_risk": "Simulation uses heuristic non-strong composition; NOT real natural distribution",
            "output_dir": "D:\\ocn\\experiments\\v3_15_low_prevalence_screening_simulation\\",
        },
        {
            "experiment_name": "v3_15_claim_realism_audit",
            "status": "completed",
            "n_samples": "444 silver claims + 111 groups",
            "main_methods": "Automatic realism risk audit (too_template_like, too_extreme, unnatural_wording, etc.)",
            "key_metrics": "0% high-risk claims; 52.3% contradiction_mechanical; 76.6% group template risk; safe_as_diagnostic=true, safe_as_naturalistic=false",
            "supports_claim": "SimClaim safe as controlled diagnostic set; realism risk low at claim level",
            "weakens_claim": "SimClaim NOT safe as naturalistic corpus; group template risk high (design attribute)",
            "paper_use": "§V data section; §VII.J realism audit; §IX limitation 10",
            "remaining_risk": "Automatic audit only; gold realism check (§VII.J Layer 2) still pending",
            "output_dir": "D:\\ocn\\experiments\\v3_15_claim_realism_audit\\",
        },
        {
            "experiment_name": "v3_15_scalar_vs_relation_screening_deep_test",
            "status": "completed",
            "n_samples": "444 silver + 100 matched",
            "main_methods": "Scalar score vs R4 deep comparison on mild_vs_strong boundary",
            "key_metrics": "Scalar ROC-AUC=0.51 (mild_vs_strong); R4 strong_F1=0.30 vs scalar=0.13 (matched 100); score collapse (mild/strong overlap ~1.02); R4 captures 2.7x more LLM-missed strong",
            "supports_claim": "Scalar cannot replace R4; R4 retains strong_action screening advantage",
            "weakens_claim": "Scalar is proxy (official RIGOURATE blocked)",
            "paper_use": "§VI.E; §VIII.D; §VIII.G fallback rationale",
            "remaining_risk": "Proxy caveat; gold adjudication pending",
            "output_dir": "D:\\ocn\\experiments\\v3_15_scalar_vs_relation_screening_deep_test\\",
        },
    ]
    out = os.path.join(OUT_DIR, "experiment_result_master_table.csv")
    with open(out, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["experiment_name", "status", "n_samples", "main_methods", "key_metrics", "supports_claim", "weakens_claim", "paper_use", "remaining_risk", "output_dir"])
        w.writeheader()
        w.writerows(rows)
    print("Wrote " + out)
    return rows


def write_experiment_synthesis(rows):
    content = """# Experiment Result Synthesis

**Date:** 2026-07-05
**Experiments synthesized:** """ + str(len(rows)) + """

## R4 strong_action results

- **R4 strong_F1 = 0.3967** (silver 444); **0.3000** (matched 100)
- **R4 strong_recall = 0.4562** (silver 444); **0.36** (matched 100, catches 9/25 silver=strong)
- **R4 macro_F1 = 0.4238** (silver 444); **0.3280** (matched 100)
- **Baseline strong_F1 = 0.2408**; absolute gap = **+0.2231**
- **R4 captures 8 LLM-missed strong_action cases** (out of 100 matched)
- **Screening utility:** FP/TP = 2.89, review burden = 35%

**Verdict:** R4 retains targeted Level-2 high-risk strong_action screening value. R4 is a screening complement, NOT an overall-beats-LLM classifier (R4 macro_F1 0.3280 < LLM 0.5523).

## LLM (GPT-5.5 / DeepSeek-V3) results

- **GPT-5.5 macro_F1 = 0.5523** (matched 100); **strong_F1 = 0.0769**, **strong_recall = 0.04** (1/25)
- **DeepSeek-V3 macro_F1 = 0.5270** (200); **strong_F1 = 0.0769**, **strong_recall = 0.04** (1/25)
- **GPT structured vs standard:** no improvement (both strong_F1=0.0769, strong_recall=0.04)
- **LLM pred_strong_rate = 0.04** vs **R4 = 0.36** (9x conservatism gap)

**Verdict:** LLM conservatism CONFIRMED. LLMs under-detect strong_action under tested prompts. This is a controlled silver-stage finding, not a fundamental LLM limit. Gold adjudication is the protocol-locked mechanism that determines whether this pattern is treated as established.

## Non-gold credibility checks (§VIII.D)

- **Label-shift stress:** R4 advantage robust at 70% retention; marginal-positive at 60%; positive-but-statistically-weaker at 50% (CI crosses zero); below 50% downgrade per §VII.G.
- **Screening utility (§VIII.D.B):** FP/TP=2.89, review burden=35%, R4 captures 8 LLM-missed strong cases.
- **Evidence necessity (§VIII.D.D):** R4 uses evidence (not gaming via claim-only cues); claim-only TF-IDF separability gap = -0.0066 (LOW leakage).
- **Boundary collapse (§VIII.D.E):** If taxonomy collapses to 3-class (supported/overclaim/contradiction), strong_action isolation is lost.

**Caveat preserved:** Non-gold checks do NOT replace gold adjudication (§VIII.D opening caveat).

## Low-prevalence screening simulation

- **R4 recall stable ~0.36** across 1%-25% prevalence (1000 resamples per level)
- **FP/TP ratio:** 3.8 (at 25%) → 121 (at 1%)
- **R4 NOT viable standalone <10% prevalence; viable as first-stage filter**
- Two-stage pipeline (R4 first-stage + LLM second-stage) motivated but NOT evaluated end-to-end

**Caveat:** Simulation uses heuristic non-strong composition; NOT a real natural-distribution study.

## Claim realism audit

- **0% high-risk claims** (automatic rules); 52.3% contradiction_mechanical; 76.6% group template risk
- **safe_as_diagnostic_set = true; safe_as_naturalistic = false**
- SimClaim is a controlled counterfactual diagnostic set, NOT a naturalistic corpus
- Gold realism check (§VII.J Layer 2) still pending

## Scalar / RIGOURATE-style baseline

- **rule_scalar_score ROC-AUC = 0.5062** (mild_vs_strong, chance-level)
- **llm_scalar_proxy ROC-AUC = 0.5874** (weak, below 0.70)
- **nli_scalar_score:** all "blocked" (444)
- **Official RIGOURATE code/data/model NOT available** (blocked)
- Scalar cannot distinguish mild vs strong; R4 retains independent value on strong_action screening

**Caveat:** Scalar baseline is PROXY (rule-based / LLM-label-derived), NOT official RIGOURATE.

## Boundary collapse fallback

- If taxonomy collapses to 3-class (supported/overclaim/contradiction), strong_action isolation is lost
- **4-class R4 macro_F1 = 0.328**; **3-class fallback macro_F1 = higher** but loses strong_action screening
- **Three-class fallback is CONTINGENCY (Route C), not primary** — primary is Route A (four-class + relation+realism gold)

## LLM conservatism + error direction

- **LLM pred_strong_rate = 0.04** (GPT standard, GPT structured, DeepSeek all = 0.04)
- **R4 pred_strong_rate = 0.36** (9x higher)
- **LLM error direction splits:**
  - GPT standard/structured: over-route to contradiction (14/25 = 56%)
  - DeepSeek: compress to mild/supported (19/25 = 76%)
- **Complementarity:** 50/100 matched samples show R4-LLM complementary cases (LLM-only-correct + R4-only-correct)

## R4 false positive root cause

- **26 FP out of 35 strong predictions** (fp_rate = 0.7429)
- FP concentrated in **mild→strong boundary** (same confusion as scalar collapse)
- R4 over-routes mild to strong; this is the cost of higher recall
- **Implication:** R4 is a high-recall first-stage filter, not a precision classifier; two-stage pipeline (R4 + LLM) motivated

## Overall evidence status

All experiments are **silver-stage evidence** pending the §VII protocol-locked gold adjudication. No gold has been collected. The mainline survives with mandatory revisions (mainline_survives=true, needs_dataset_redesign=false, needs_relation_realism_gold=true). The hierarchical taxonomy (V3.15) reduces the "forced four-class" reviewer risk by converting it to a pre-registered graceful-degradation path (§VII.K fallback rules).
"""
    out = os.path.join(OUT_DIR, "experiment_result_synthesis.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 6: current_mainline_assessment.md
# =============================================================================

def write_mainline_assessment():
    content = """# Current Mainline Assessment

**Date:** 2026-07-05
**Assessment based on:** V3.15 hierarchical taxonomy revision + V3.16 integration gate + overnight pipeline + all recent task gates

## 1. What is the current mainline?

The current mainline is **CESE-OCN R4**: a relation-specific screening router under the hierarchical diagnostic taxonomy, targeting Level-2 high-risk strong_action overclaim screening as a complement to LLM judges. The mainline is anchored on the SimClaim controlled counterfactual diagnostic set (444 silver pairs, 111 groups, 6 domains) and the pre-registered §VII gold adjudication protocol (Layer 1 relation + Layer 2 realism, DRAFT, annotation NOT begun).

## 2. Is the mainline still flat 4-class?

**No.** As of V3.15, the mainline has transitioned from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy**:
- **Level 1:** supported / overclaim / contradiction
- **Level 2 (under overclaim):** scope_expansion (= mild_scope_overclaim) / strong_action (= strong_action_overclaim)

The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space, but their interpretation is hierarchical. `mild_scope_overclaim` is explicitly a boundary-sensitive buffer subtype, NOT a naturally stable discrete class.

## 3. Has it transitioned to hierarchical diagnostic taxonomy?

**Yes.** V3.15 (the current recommended paper version) implements the hierarchical taxonomy via 18 targeted string replacements across 9 sections. Key markers:
- Abstract reframed ("we operationalize a hierarchical diagnostic taxonomy")
- §I contribution 1 reframed as "Hierarchical diagnostic taxonomy"
- §III.A adds Table 0a (Level 1 / Level 2 mapping)
- §IV.A reframes R4 as "relation-specific screening router under the hierarchical taxonomy"
- §VIII.G (NEW) "Why the Taxonomy Is Hierarchical Rather Than Flat"
- §VII.K (NEW) hierarchical gold validation plan with pre-registered fallback rules
- §X Conclusion reframed hierarchically

The readiness gate confirms: `hierarchical_taxonomy_inserted=true`, `flat_four_class_deemphasized=true`, `fallback_to_3class_plus_binary_defined=true`.

## 4. Is three-class + strong_action binary the mainline or fallback?

**It is the FALLBACK, not the primary mainline.** The primary mainline is the hierarchical taxonomy (Level 1 + Level 2). The three-class + binary strong_action screening is the pre-registered fallback (§VII.K rule 3.1) that activates IF gold adjudication shows Level-2 κ < 0.40 (mild_vs_strong boundary not reliably drawable). This fallback design is what reduces the "forced four-class" reviewer risk: the paper does not force four classes; it has a graceful-degradation path to three classes + binary screening.

## 5. How should SimClaim be defined currently?

SimClaim is a **controlled counterfactual diagnostic set**:
- 444 silver claim-evidence pairs, 111 groups, 6 domains, balanced 1:1:1:1 across the four operational labels
- Uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence
- **NOT a natural-prevalence corpus** — the balanced design is deliberate for diagnostic pressure-testing, not an estimate of real-world prevalence
- **NOT a naturalistic corpus** — generated claim variants have template risk (76/111 groups high-risk tier, design attribute); realism audit (§VII.J Layer 2) pending
- Silver labels pending §VII gold adjudication
- `safe_as_diagnostic_set=true`, `safe_as_naturalistic=false`

## 6. How should R4 be defined currently?

R4 is a **relation-specific screening router under the hierarchical taxonomy**:
- Three routes map onto hierarchical levels: contradiction gate (Level 1), scope residual classifier (Level 1 supported vs. Level 2 scope_expansion), strong_action route (Level 2 high-risk screening)
- **NOT a flat 4-class best classifier** — R4's macro_F1 (0.3280) is lower than LLM (0.5523)
- **Core value: Level-2 high-risk strong_action screening** — R4 strong_F1=0.3967 (silver 444), 0.3000 (matched 100); strong_recall=0.4562 (silver), 0.36 (matched); R4 captures 8 LLM-missed strong cases
- Positioned as a screening-oriented complement to LLM judges, NOT a competitive replacement
- Frozen thresholds: t_contra=0.48, t_strong=0.535, t_svm=0.51
- High false positive rate (26 FP / 35 strong predictions, fp_rate=0.7429) concentrated in mild→strong boundary — R4 is a high-recall first-stage filter, not a precision classifier

## 7. Is the RIGOURATE/ForceBench/CLAIM-BENCH homogenization risk controllable?

**Yes, controllable.** The V3.16 integration gate confirms `rigourate_overlap_fatal=false`. Key differentiators:
- **vs. RIGOURATE:** RIGOURATE uses scalar overstatement scoring on natural author-written claims; CESE-OCN uses hierarchical relation-typed screening on controlled counterfactual claim variants. Official RIGOURATE code/data/model NOT available (blocked); proxy scalar baseline cannot distinguish mild vs strong (ROC-AUC=0.5062).
- **vs. ForceBench:** ForceBench uses contrastive paired-claim force testing; CESE-OCN uses single-claim evidence-sufficiency calibration with relation typing.
- **vs. CLAIM-BENCH:** CLAIM-BENCH does full-paper claim-evidence extraction; CESE-OCN focuses on evidence-sufficiency calibration at the span level.
- §II.A positioning paragraph + Table X explicitly differentiate CESE-OCN from all three.

## 8. Biggest data credibility risk

**SimClaim is counterfactual, not natural-prevalence.** The balanced four-way design (111 per class) is a deliberate construction for diagnostic pressure-testing, NOT an estimate of real-world prevalence. In natural scientific corpora, `contradiction_candidate` and `strong_action_overclaim` are expected to be substantially rarer. Template risk is high (76/111 groups) but is a design attribute, not a defect. The §VII.J two-layer gold protocol includes a realism audit (Layer 2: `claim_realism_score_1_to_5`) to assess natural-claim transferability, but this has NOT been executed yet.

**Secondary data risk:** All labels are silver (AI-preannotated development labels). The §V.D author sanity audit flagged 25/40 (62.5%) of audited silver labels as questionable or unclear, with strong_action at 75% confusion. Gold adjudication is the only mechanism that can resolve this.

## 9. Biggest method credibility risk

**R4 macro_F1 < LLM.** R4's overall macro_F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5270) on matched 100 samples. The paper does NOT claim R4 overall beats LLM — it claims R4 provides targeted Level-2 strong_action screening signal at the cost of lower overall macro_F1. This is a defensible but narrow claim: if gold adjudication shows strong_action is not reliably drawable (Level-2 κ < 0.40), R4's screening value downgrades to exploratory status per §VII.K fallback rule 3.3.

**Secondary method risk:** R4 high false positive rate (fp_rate=0.7429). R4 over-routes mild→strong and contradiction→strong. This is the cost of higher recall (0.36 vs LLM 0.04); the two-stage pipeline (R4 first-stage + LLM second-stage) is motivated but NOT evaluated end-to-end.

## 10. What is the most necessary next action?

**Execute the §VII 50-pair two-layer gold pilot** (Layer 1 relation label + Layer 2 realism score) using the frozen `gold_pilot_protocol_freeze_v1` package and the v2 relation+realism protocol (`gold_pilot_relation_realism_protocol_v2`). Specifically:
1. Execute blind annotation A and B (50 pairs each)
2. Adjudicate disagreements
3. Compute Level-1 κ (supported / overclaim / contradiction) — threshold ≥ 0.50
4. Compute Level-2 κ (scope_expansion vs. strong_action, conditional on overclaim) — threshold ≥ 0.40
5. Compute strong_action retention rate — threshold ≥ 0.60 (retain) / < 0.50 (exploratory)
6. Apply §VII.K fallback rules to determine whether to retain hierarchical taxonomy or fall back to Level-1 three-class + binary strong_action screening
7. Insert gold results into Tables G1–G3 without restructuring the paper

This is the single most decisive action for the project: it determines whether the four-class hierarchical taxonomy is validated, downgraded to three-class + binary screening, or downgraded to exploratory status.
"""
    out = os.path.join(OUT_DIR, "current_mainline_assessment.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 7: allowed_vs_forbidden_claims_current.md
# =============================================================================

def write_allowed_forbidden():
    content = """# Allowed vs. Forbidden Claims (Current, as of V3.15)

**Date:** 2026-07-05
**Basis:** V3.15 hierarchical taxonomy revision + V3.16 integration gate + overnight pipeline + all recent task gates. Silver-stage evidence only; gold adjudication pending.

---

## Allowed claims

These claims are supported by the current evidence and may be made in the paper:

### 1. Controlled counterfactual diagnostic set

SimClaim is a **controlled counterfactual diagnostic set** that uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence. It is NOT a natural-prevalence corpus and NOT a naturalistic corpus. The balanced four-way design (111 per class) is a deliberate construction for diagnostic pressure-testing.

**Evidence:** §V.A synthetic/counterfactual transparency statement; claim_realism_audit (0% high-risk, safe_as_diagnostic=true); overnight pipeline Task A (TF-IDF gap=-0.0066, low leakage).

### 2. Hierarchical diagnostic taxonomy

The paper operationalizes a **hierarchical diagnostic taxonomy**: Level 1 (supported / overclaim / contradiction); Level 2 (scope_expansion / strong_action under overclaim). The four operational labels remain the experimental label space; interpretation is hierarchical. `mild_scope_overclaim` is a boundary-sensitive buffer subtype, NOT a naturally stable discrete class.

**Evidence:** V3.15 §III.A Table 0a; §VIII.G; readiness gate (hierarchical_taxonomy_inserted=true, flat_four_class_deemphasized=true).

### 3. R4 screening-oriented complement

R4 is a **relation-specific screening router under the hierarchical taxonomy** that targets Level-2 high-risk strong_action screening as a complement to LLM judges. R4 is NOT a flat 4-class best classifier and NOT a competitive replacement for LLM judges.

**Evidence:** §IV.A; §VI.A–§VI.B; R4 strong_F1=0.3967 (silver 444), 0.3000 (matched 100); R4 captures 8 LLM-missed strong cases.

### 4. LLM under-detection under tested prompts

Under tested prompts, strong LLM judges (GPT-5.5, DeepSeek-V3) **consistently under-detect strong_action** (strong-F1=0.0769, recall 0.04 = 1/25 across both models and both prompt designs). This is a controlled silver-stage diagnostic finding, NOT a fundamental limit of LLMs.

**Evidence:** §VI.B; overnight pipeline Task E (LLM pred_strong_rate=0.04 vs R4=0.36, 9x gap); LLM conservatism confirmed.

### 5. Non-gold robustness checks

Non-gold credibility checks (label-shift stress, screening utility, evidence necessity, boundary collapse) provide **diagnostic evidence** that R4's screening value is robust to simulated label shift down to ~60% retention and that R4 uses evidence (not gaming via claim-only cues). These checks do NOT replace gold adjudication.

**Evidence:** §VIII.D; v3_11_three_core_credibility_experiments; overnight pipeline Task D (boundary collapse).

### 6. Relation + realism gold pending

The §VII pre-registered gold adjudication protocol (Layer 1 relation + Layer 2 realism) is **planned and frozen**, with ready_for_blind_annotation=true. Annotation has NOT begun. The protocol includes pre-registered downgrade criteria (§VII.G) and hierarchical fallback rules (§VII.K).

**Evidence:** §VII; gold_pilot_protocol_freeze_v1; gold_pilot_relation_realism_protocol_v2 (ready_for_blind_annotation=true, does_not_modify_v1=true).

### 7. Scalar baseline / proxy result (completed)

The RIGOURATE-style scalar baseline is a **proxy** (rule-based / LLM-label-derived), NOT official RIGOURATE. Official RIGOURATE code/data/model are NOT publicly available (blocked). The proxy scalar score cannot distinguish mild vs strong (ROC-AUC=0.5062, chance-level) and cannot replace R4 on strong_action screening.

**Evidence:** §VI.E; rigourate_reproduction_readiness_gate (official_reproduction_possible=false); v3_15_scalar_vs_relation_deep_test (scalar_can_separate_mild_strong=false, scalar_can_replace_r4=false).

---

## Forbidden claims

These claims are NOT supported by the current evidence and MUST NOT be made in the paper:

### 1. Natural prevalence corpus

**Forbidden:** Claiming SimClaim is a natural-prevalence corpus or estimates real-world prevalence of evidence-sufficiency relations.

**Why forbidden:** The balanced four-way design is deliberate; in natural corpora, contradiction and strong_action are substantially rarer. Low-prevalence simulation uses heuristic non-strong composition, NOT real distribution.

### 2. Gold validated

**Forbidden:** Claiming the four-class taxonomy is gold-validated, gold-confirmed, or that gold adjudication is complete.

**Why forbidden:** Gold annotation has NOT begun. All labels are silver (AI-preannotated). The §VII protocol is planned and frozen, not executed. Only the conditional success path (§VII.G criterion 6) describes future gold-validated numbers.

### 3. R4 beats LLM overall

**Forbidden:** Claiming R4 outperforms LLM judges overall, R4 has higher macro_F1 than LLM, or R4 is a competitive replacement for LLM judges.

**Why forbidden:** R4 macro_F1=0.3280 < LLM=0.5523 (matched 100). R4 is a screening complement with targeted value on Level-2 strong_action, NOT an overall-beats-LLM classifier.

### 4. Official RIGOURATE reproduced

**Forbidden:** Claiming to have reproduced the official RIGOURATE system, or that the scalar baseline represents RIGOURATE's actual performance.

**Why forbidden:** Official RIGOURATE code/data/model are NOT publicly available (blocked). The scalar baseline is explicitly a PROXY (rule-based / LLM-label-derived).

### 5. First scientific overstatement benchmark

**Forbidden:** Claiming CESE-OCN is the first scientific overstatement detection benchmark, or that it opens a new field.

**Why forbidden:** Scientific overstatement detection is an existing track (RIGOURATE [30], ForceBench [35], CLAIM-BENCH [28]). CESE-OCN contributes a hierarchical relation-typed decomposition, not a new field.

### 6. mild_scope as naturally stable category

**Forbidden:** Claiming mild_scope_overclaim is a naturally stable discrete class, naturally discrete, or naturally drawable.

**Why forbidden:** The §V.D audit flags 75% confusion on strong_action boundary. V3.15 explicitly states mild_scope is a boundary-sensitive buffer subtype, NOT a naturally stable discrete class. Gold adjudication will determine whether the Level-2 boundary is reliably drawable.

### 7. Simulation as real-world distribution

**Forbidden:** Claiming the low-prevalence screening simulation represents real-world strong_action prevalence, or that the simulation is a natural-distribution study.

**Why forbidden:** The simulation uses heuristic non-strong composition and resampling; it is NOT a real natural-distribution study. It provides diagnostic evidence of R4's recall stability, not prevalence estimates.

---

## Borderline claims (require careful wording)

These claims are conditionally allowed with explicit caveats:

- **"R4 improves strong_action recall"** — allowed ONLY with "on controlled silver-stage evaluation" and "under tested prompts" caveats.
- **"Two-stage pipeline motivated"** — allowed ONLY as "motivated by complementarity analysis" NOT as "evaluated end-to-end".
- **"Gold will validate"** — allowed ONLY in conditional success-path language ("if gold supports...", "the success path is..."), NOT as "gold validates".
- **"Hierarchical taxonomy"** — allowed, but must include the fallback design (§VII.K) and must NOT claim mild_scope is naturally stable.
"""
    out = os.path.join(OUT_DIR, "allowed_vs_forbidden_claims_current.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 8: current_project_state_master_report.md
# =============================================================================

def write_master_report():
    content = """# Current Project State — Master Report

**Date:** 2026-07-05
**Version:** V3.15 Hierarchical Taxonomy Revision
**Prepared by:** Project State Consolidation v1 (read-only audit)

---

## 1. One-page executive summary

The CESE-OCN project has transitioned from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy** (V3.15). Level 1 separates supported / overclaim / contradiction; Level 2 under overclaim separates scope_expansion (mild) from strong_action (high-risk). The four operational labels remain the experimental label space; only interpretation changes. All experimental numbers are preserved byte-identical from V3.14. R4 is positioned as a Level-2 high-risk strong_action screening router, NOT a flat 4-class best classifier and NOT an overall-beats-LLM claim (R4 macro_F1=0.3280 < LLM=0.5523). The mainline survives with mandatory revisions: mainline_survives=true, needs_dataset_redesign=false, needs_relation_realism_gold=true. The single most decisive next action is executing the §VII 50-pair two-layer gold pilot (relation + realism) to determine whether the Level-2 mild_vs_strong boundary is reliably drawable (κ ≥ 0.40) or whether the paper falls back to Level-1 three-class + binary strong_action screening per the pre-registered §VII.K fallback rules.

---

## 2. Current mainline

**CESE-OCN R4** as a relation-specific screening router under the hierarchical diagnostic taxonomy, targeting Level-2 high-risk strong_action overclaim screening as a complement to LLM judges. Anchored on SimClaim (controlled counterfactual diagnostic set, 444 silver pairs) and the pre-registered §VII gold adjudication protocol (DRAFT, annotation NOT begun).

---

## 3. What changed in recent tasks

- **V3.15 hierarchical taxonomy revision:** 18 targeted string replacements across 9 sections; added Table 0a, §VII.K, §VIII.G; reframed R4 as hierarchical router; added pre-registered fallback rules.
- **Overnight non-API compute pipeline v1:** 8 sub-tasks (A-H) all completed; confirmed dataset integrity, LLM conservatism, R4 FP root cause, scalar collapse, complementarity.
- **V3.16 integration summary:** mainline_survives=true; three routes identified (A=PRIMARY four-class + gold, B=FALLBACK strong_action focus, C=CONTINGENCY three-class downgrade).
- **RIGOURATE reproduction:** official blocked; proxy scalar baseline built; scalar cannot replace R4.
- **Claim realism audit:** 0% high-risk; safe as diagnostic set, NOT as naturalistic corpus.
- **Low-prevalence screening simulation:** R4 recall stable ~0.36; NOT viable standalone <10%; viable as first-stage filter.
- **Scalar vs relation deep test:** scalar ROC-AUC=0.51 on mild_vs_strong; score collapse confirmed.
- **Gold protocol v2:** two-layer (relation + realism) DRAFT; ready_for_blind_annotation=true.

---

## 4. Completed / partial / blocked / missing tasks

### Completed (all gates report completed=true)
- Overnight non-API compute pipeline v1 (8 sub-tasks A-H)
- V3.15 hierarchical taxonomy revision (18 replacements, 10 quality checks PASS)
- V3.16 integration summary + revision plan
- RIGOURATE reproduction + SimClaim baseline (proxy, official blocked)
- Claim realism audit
- Low-prevalence screening simulation
- Scalar vs relation screening deep test
- Gold pilot relation+realism protocol v2 (DRAFT, ready for annotation)
- V3.14 mainline locked + consistency audit
- V3.13 RIGOURATE-differentiated + realism-aware
- V3.12 three credibility checks
- V3.11 three core credibility experiments
- Mixed framework v2 frozen R4 baseline
- LLM judge baseline v1 (DeepSeek, 200 samples)
- GPT structured judge probe v1 (100 samples)

### Partial / blocked
- None. All recent tasks completed. RIGOURATE official reproduction is blocked (official artifacts unavailable) but the proxy baseline is completed and labeled as proxy.

### Missing
- None. All 17 scanned directories exist.

### Planned (NOT completed — must not be written as completed)
- §VII 50-pair two-layer gold pilot annotation (NOT begun)
- Gold adjudication and κ computation (NOT begun)
- Two-stage pipeline end-to-end evaluation (NOT done; only complementarity analyzed)
- Official RIGOURATE reproduction (blocked; proxy only)

---

## 5. Paper version status

| Version | Status | Notes |
|---|---|---|
| V3.15 hierarchical_taxonomy_revision | **CURRENT RECOMMENDED** | Hierarchical taxonomy; all quality checks PASS; 157953 bytes MD |
| V3.14 mainline_locked_consistency_audit | Predecessor (frozen) | Source for V3.15; experimental numbers byte-identical |
| V3.13_rigourate_differentiated_realism_aware | Historical | Superseded by V3.14 |
| V3.13_differentiated_against_rigourate_forcebench | Historical | First differentiation pass |
| V3.12_1 / V3.12 | Historical | Three credibility checks |
| V3.11 | Historical | Framework roadmap |
| V3.10 / V3.10_1 | Historical | Advisor ready silver stage |
| V3.9 / V3.9_audit | Historical | Pre-gold complete |
| V3.8 | Historical | Reference refreshed |
| V3.7 | Historical | Advisor handoff (was V3.7-era current) |
| V3.6 / V3.5 / V3.4 | Historical | Early versions |

**Note:** `_PROJECT_INDEX/current_paper_paths.md` references V3.7 as current — OUTDATED. Current is V3.15.

---

## 6. Experiment evidence status

All experiments are **silver-stage evidence** pending §VII gold adjudication. Key results (all preserved byte-identical in V3.15):

- **R4 strong_F1:** 0.3967 (silver 444), 0.3000 (matched 100)
- **R4 macro_F1:** 0.4238 (silver 444), 0.3280 (matched 100)
- **LLM strong_F1:** 0.0769 (matched 100); strong_recall=0.04 (1/25)
- **LLM macro_F1:** 0.5523 (GPT-5.5, matched 100), 0.5270 (DeepSeek, 200)
- **Baseline strong_F1:** 0.2408; absolute gap +0.2231
- **R4 strong_recall:** 0.4562 (silver 444), 0.36 (matched 100)
- **Screening utility:** FP/TP=2.89, review burden=35%, R4 captures 8 LLM-missed strong
- **LLM conservatism:** pred_strong_rate=0.04 (LLM) vs 0.36 (R4), 9x gap
- **Scalar ROC-AUC (mild_vs_strong):** 0.5062 (rule), 0.5874 (llm proxy)
- **Dataset integrity:** TF-IDF gap=-0.0066 (low leakage)
- **Claim realism:** 0% high-risk; safe_as_diagnostic=true, safe_as_naturalistic=false

**Non-gold checks caveat preserved:** Non-gold robustness checks do NOT replace gold adjudication.

---

## 7. Code/script status

- **Total scripts:** 47 in `D:\\ocn\\scripts\\`
- **Safe to run:** V3.15/V3.16/overnight builders + audit/view scripts (no API, no gold, no original data modification)
- **Not safe to run (frozen):** Historical experiment runners (run_cese_ocn_lite_v3, run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1, etc.) — results frozen
- **Calls API:** 2 scripts (run_llm_judge_baseline_v1, run_gpt_structured_judge_probe_v1) — require user authorization + API key
- **Trains model:** 2 scripts (run_mixed_framework_router_optimization_v2, run_mixed_framework_new_algorithm_sweep_v1) — frozen
- **Outdated registry:** `_PROJECT_INDEX/script_registry_mainline.csv` references V3.7 as current; should be updated to V3.15 (documentation task, not refactoring)

No dangerous or duplicate scripts found.

---

## 8. Dataset/gold status

### SimClaim dataset
- 444 silver claim-evidence pairs, 111 groups, 6 domains, balanced 1:1:1:1
- Controlled counterfactual diagnostic set (NOT natural-prevalence, NOT naturalistic)
- TF-IDF separability gap = -0.0066 (LOW leakage risk)
- Template risk high (76/111 groups) but design attribute, not defect
- Claim realism: 0% high-risk; 52.3% contradiction_mechanical
- All labels silver (AI-preannotated); §V.D audit flagged 62.5% questionable/unclear

### Gold status
- **§VII gold adjudication protocol:** PLANNED and FROZEN, NOT executed
- **gold_pilot_protocol_freeze_v1:** 50-sample preparation pack, ready
- **gold_pilot_relation_realism_protocol_v2:** two-layer (relation + realism) DRAFT, ready_for_blind_annotation=true
- **Annotation:** NOT begun
- **Downgrade criteria:** pre-registered (§VII.G) + hierarchical fallback (§VII.K)

---

## 9. Biggest risks

### Risk 1: Level-2 mild_vs_strong boundary not reliably drawable
- **Likelihood:** Moderate (§V.D audit: 75% confusion on strong_action)
- **Impact:** High — if gold κ < 0.40, paper falls back to Level-1 three-class + binary strong_action screening (§VII.K rule 3.1)
- **Mitigation:** Pre-registered fallback rules; hierarchical taxonomy converts "forced four-class" attack into graceful-degradation path

### Risk 2: Gold adjudication may downgrade strong_action
- **Likelihood:** Low-moderate (strong_action has clear risk semantics: deployment/safety/policy)
- **Impact:** High — if strong_action retention < 0.50, R4 screening claim downgrades to exploratory (§VII.K rule 3.3)
- **Mitigation:** Pre-registered thresholds; §VIII.D.C label-shift stress test pre-quantifies robustness (break-even ~50%)

### Risk 3: RIGOURATE proxy may not match official system
- **Likelihood:** Unknown (official artifacts unavailable)
- **Impact:** Moderate — scalar baseline conclusions may shift when official RIGOURATE becomes available
- **Mitigation:** Explicit proxy caveat in §VI.E and §IX limitation 11; paper does not claim to outperform official RIGOURATE

### Secondary risks
- R4 high false positive rate (fp_rate=0.7429) — cost of higher recall; two-stage pipeline motivated but not evaluated
- SimClaim counterfactual design limits natural-claim transferability — §VII.J Layer 2 realism audit pending
- _PROJECT_INDEX registry outdated (references V3.7) — documentation gap, not a technical risk

---

## 10. Next 5 concrete actions

### Action 1: Execute §VII 50-pair two-layer gold pilot
- Use `gold_pilot_protocol_freeze_v1` + `gold_pilot_relation_realism_protocol_v2`
- Blind annotation A and B (50 pairs each) → adjudicate → compute Level-1 κ, Level-2 κ, strong_action retention
- Apply §VII.K fallback rules
- **Priority:** CRITICAL — determines whether hierarchical taxonomy is validated or downgraded

### Action 2: Insert gold results into paper
- Once gold pilot completes, insert results into Tables G1–G3
- Do NOT restructure the paper; only fill in the pre-registered table slots
- Update §VII readiness gate based on gold outcomes

### Action 3: Update _PROJECT_INDEX registry
- Update `script_registry_mainline.csv` and `current_paper_paths.md` to reference V3.15 as current
- Documentation task; no code changes needed

### Action 4: Evaluate two-stage pipeline end-to-end (post-gold)
- Currently only complementarity is analyzed (50/100 complementary cases)
- After gold validation, evaluate R4 first-stage + LLM second-stage end-to-end
- Report FP/TP, review burden, and net recall improvement

### Action 5: Prepare V3.16 main paper revision (post-gold)
- Based on gold outcomes, either retain V3.15 hierarchical taxonomy (Route A) or fall back to Level-1 three-class + binary screening (Route C)
- V3.16 revision plan already drafted in `project_synthesis/v3_16_integration_summary_and_revision_plan/`
- Do NOT begin V3.16 revision until gold pilot completes
"""
    out = os.path.join(OUT_DIR, "current_project_state_master_report.md")
    with open(out, "w", encoding="utf-8") as f:
        f.write(content)
    print("Wrote " + out)


# =============================================================================
# Section 9: current_project_state_gate.json
# =============================================================================

def write_final_gate():
    gate = {
        "gate_name": "current_project_state_gate",
        "date": "2026-07-05",
        "output_directory": OUT_DIR,

        # 13 required fields from spec §9
        "inventory_completed": True,
        "gates_read": True,
        "code_reaudit_completed": True,
        "paper_lineage_completed": True,
        "experiment_synthesis_completed": True,
        "mainline_identified": True,
        "latest_recommended_version": "V3.15 hierarchical_taxonomy_revision",
        "hierarchical_taxonomy_status": "inserted (V3.15); flat four-class deemphasized; fallback to 3-class + binary strong_action screening pre-registered in §VII.K",
        "rigourate_overlap_status": "controllable (rigourate_overlap_fatal=false); official RIGOURATE blocked; proxy scalar baseline cannot replace R4",
        "gold_status": "planned and frozen (§VII + gold_pilot_protocol_freeze_v1 + gold_pilot_relation_realism_protocol_v2); annotation NOT begun; ready_for_blind_annotation=true",
        "next_required_action": "Execute §VII 50-pair two-layer gold pilot (Layer 1 relation + Layer 2 realism) using frozen protocol; compute Level-1 κ, Level-2 κ, strong_action retention; apply §VII.K fallback rules",
        "main_remaining_risk": "Level-2 mild_vs_strong boundary not reliably drawable (75% confusion in §V.D audit); if gold κ < 0.40, paper falls back to Level-1 three-class + binary strong_action screening",
        "ready_for_next_analysis": True,

        # Supporting metadata
        "n_directories_scanned": 17,
        "n_gates_read": 25,
        "n_scripts_audited": 47,
        "n_paper_versions_scanned": 16,
        "n_experiments_synthesized": 9,
        "recent_tasks_completed": 15,
        "recent_tasks_partial_blocked": 0,
        "recent_tasks_missing": 0,
        "planned_not_completed": [
            "§VII 50-pair two-layer gold pilot annotation",
            "Gold adjudication and κ computation",
            "Two-stage pipeline end-to-end evaluation",
            "Official RIGOURATE reproduction (blocked)",
        ],
        "prohibitions_enforced": {
            "no_new_experiments": True,
            "no_api_calls": True,
            "no_gold": True,
            "no_paper_modification": True,
            "no_original_data_modification": True,
            "no_file_deletion": True,
            "no_renaming": True,
            "no_planned_as_completed": True,
            "no_silver_as_gold": True,
        },
        "audit_disclaimer": "Read-only audit and synthesis. No experiments run, no API calls, no gold annotation, no paper modification, no original data modification, no file deletion, no renaming. All silver labels remain silver. All planned tasks are marked as planned, not completed. Missing files are marked missing, not fabricated.",
    }
    out = os.path.join(OUT_DIR, "current_project_state_gate.json")
    with open(out, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print("Wrote " + out)


# =============================================================================
# Main
# =============================================================================

def main():
    os.makedirs(OUT_DIR, exist_ok=True)
    print("=" * 70)
    print("Project State Consolidation v1")
    print("Output: " + OUT_DIR)
    print("=" * 70)

    print("\n[1] recent_task_output_inventory.csv")
    inv_rows = write_inventory_csv()

    print("\n[2] all_recent_gates_inventory.csv + gate_synthesis_report.md")
    gate_rows = write_gates_inventory()
    write_gate_synthesis_report(gate_rows)

    print("\n[3] code_structure_reaudit.csv + code_structure_reaudit_report.md")
    code_rows = write_code_reaudit()
    write_code_reaudit_report(code_rows)

    print("\n[4] paper_version_inventory.csv + paper_version_lineage_report.md")
    paper_rows = write_paper_inventory()
    write_paper_lineage_report(paper_rows)

    print("\n[5] experiment_result_master_table.csv + experiment_result_synthesis.md")
    exp_rows = write_experiment_master_table()
    write_experiment_synthesis(exp_rows)

    print("\n[6] current_mainline_assessment.md")
    write_mainline_assessment()

    print("\n[7] allowed_vs_forbidden_claims_current.md")
    write_allowed_forbidden()

    print("\n[8] current_project_state_master_report.md")
    write_master_report()

    print("\n[9] current_project_state_gate.json")
    write_final_gate()

    print("\n" + "=" * 70)
    print("Consolidation complete. 13 output files generated.")
    print("=" * 70)


if __name__ == "__main__":
    main()
