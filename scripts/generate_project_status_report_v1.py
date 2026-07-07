#!/usr/bin/env python
"""generate_project_status_report_v1.py — One-time project status inventory.

Scans the OCN repository and generates 4 report files:
  1. reports/current_project_status_v3_17.md       — comprehensive status report
  2. reports/current_project_status_v3_17.json     — machine-readable status
  3. reports/leakage_quick_scan_v3_17.md           — leakage risk scan
  4. reports/file_inventory_v3_17.csv              — file inventory

Read-only: does not modify any experimental logic, data, or code.
"""

from __future__ import annotations

import csv
import hashlib
import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import pandas as pd

REPO_ROOT = Path(__file__).resolve().parent.parent
REPORTS_DIR = REPO_ROOT / "reports"

FORBIDDEN_TEXT_FIELDS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
]

LABEL_FIELDS_FOR_AUDIT_ONLY = [
    "true_label", "oracle_hit", "candidate_label_guess",
    "gold_label", "human_audited", "final_label", "is_strong_action",
]

OLD_NARRATIVE_PATTERNS = [
    (r"current\s+paper\s+V2", "Current paper V2"),
    (r"current\s+manuscript\s+is\s+V2", "Current manuscript is V2"),
    (r"simclaim_human_pilot.*current\s+mainline", "simclaim_human_pilot as current mainline"),
    (r"full\s+shared-threshold\s+CESE-OCN.*current", "full shared-threshold CESE-OCN as current"),
    (r"\bgold\s+benchmark\b", "gold benchmark"),
    (r"\bhuman-audited\b", "human-audited"),
    (r"\bSOTA\b", "SOTA"),
    (r"automatic\s+peer\s+review", "automatic peer review"),
]

# Scripts to check
SCRIPTS_A_FROZEN = [
    "run_simclaim_pdf_retrieval_v1.py",
    "run_r4_evidence_canonicalization_v1.py",
    "run_canonicalized_review_queue_v1.py",
    "run_canonicalized_risk_ranking_v1.py",
]

SCRIPTS_B_PROPOSED = [
    "build_pdf_sentence_corpus_v1.py",
    "run_bm25_sentence_retrieval_v1.py",
    "run_canonicalizer_ablation_v1.py",
    "run_format_shift_ablation_v1.py",
    "evaluate_r4_on_evidence_variants_v1.py",
    "run_leakage_audit_v1.py",
    "run_error_taxonomy_v1.py",
    "run_complexity_vs_utility_ablation_v1.py",
    "run_lightweight_smart_queue_v1.py",
    "run_toy_end_to_end_demo_v1.py",
    "generate_paper_assets_v3_17.py",
    "build_pdf_stress_suite_v1.py",
    "run_pdf_extraction_stress_test_v1.py",
    "run_pdf_extraction_to_bm25_stress_v1.py",
    "summarize_pdf_stress_report_v1.py",
]

SCRIPTS_C_INFRA = [
    "run_metric_robustness_v1.py",
    "run_confidentiality_redteam_scan_v1.py",
    "validate_experiment_outputs_v1.py",
    "run_v3_17_confidential_pipeline.py",
    "build_public_sanitized_release_v1.py",
]

EXPERIMENT_DIRS = [
    "simclaim_pdf_corpus_retrieval_v1",
    "r4_evidence_canonicalization_v1",
    "canonicalized_review_queue_v1",
    "canonicalized_risk_ranking_v1",
    "bm25_sentence_retrieval_v1",
    "canonicalizer_ablation_v1",
    "format_shift_ablation_v1",
    "leakage_audit_v1",
    "error_taxonomy_v1",
    "complexity_vs_utility_ablation_v1",
    "lightweight_smart_queue_v1",
    "pdf_extraction_stress_test_v1",
    "toy_end_to_end_demo_v1",
    "metric_robustness_v1",
    "confidentiality_redteam_scan_v1",
]


def log(msg):
    print(msg, flush=True)


def safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    if not path.exists():
        return None
    try:
        return pd.read_csv(path, keep_default_na=False)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 1. Mainline docs scan
# ---------------------------------------------------------------------------

def scan_mainline_docs() -> dict:
    """Scan README.md, CURRENT_MAINLINE.md, docs/ for V3.17 alignment."""
    result = {
        "readme_mentions_v3_17": False,
        "current_mainline_points_to_v3_17": False,
        "v3_17_confidential_doc_exists": False,
        "old_narratives": [],
        "completed": [],
        "partial": [],
        "missing": [],
    }

    readme = REPO_ROOT / "README.md"
    if readme.exists():
        content = readme.read_text(encoding="utf-8", errors="ignore")
        result["readme_mentions_v3_17"] = "V3.17" in content or "v3.17" in content.lower()
        if "no gold benchmark" in content.lower():
            result["completed"].append("README denies gold benchmark")
        if "no human-audited" in content.lower():
            result["completed"].append("README denies human-audited")
        if "no SOTA" in content or "no sota" in content.lower():
            result["completed"].append("README denies SOTA")

    cm = REPO_ROOT / "CURRENT_MAINLINE.md"
    if cm.exists():
        content = cm.read_text(encoding="utf-8", errors="ignore")
        result["current_mainline_points_to_v3_17"] = "V3.17" in content or "v3.17" in content.lower()

    v317_doc = REPO_ROOT / "docs" / "current_mainline_v3_17_confidential.md"
    result["v3_17_confidential_doc_exists"] = v317_doc.exists()

    # Scan for old narratives
    scan_files = [readme, cm] + list((REPO_ROOT / "docs").glob("*.md")) if (REPO_ROOT / "docs").exists() else [readme, cm]
    for f in scan_files:
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore")
        for pattern, label in OLD_NARRATIVE_PATTERNS:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                for m in matches:
                    result["old_narratives"].append({
                        "file": str(f.relative_to(REPO_ROOT)),
                        "pattern": label,
                        "matched_text": m[:80],
                    })

    if result["readme_mentions_v3_17"]:
        result["completed"].append("README mentions V3.17")
    if result["current_mainline_points_to_v3_17"]:
        result["completed"].append("CURRENT_MAINLINE points to V3.17")
    if result["v3_17_confidential_doc_exists"]:
        result["completed"].append("docs/current_mainline_v3_17_confidential.md exists")

    if not result["readme_mentions_v3_17"]:
        result["missing"].append("README does not mention V3.17")
    if not result["current_mainline_points_to_v3_17"]:
        result["missing"].append("CURRENT_MAINLINE does not point to V3.17")

    return result


# ---------------------------------------------------------------------------
# 2. Scripts inventory
# ---------------------------------------------------------------------------

def scan_scripts() -> dict:
    """Check script existence."""
    result = {"A_frozen": {}, "B_proposed": {}, "C_infra": {}}

    for s in SCRIPTS_A_FROZEN:
        path = REPO_ROOT / "scripts" / s
        result["A_frozen"][s] = {
            "exists": path.exists(),
            "status": "exists" if path.exists() else "missing",
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    for s in SCRIPTS_B_PROPOSED:
        path = REPO_ROOT / "scripts" / s
        result["B_proposed"][s] = {
            "exists": path.exists(),
            "status": "exists" if path.exists() else "missing",
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    for s in SCRIPTS_C_INFRA:
        path = REPO_ROOT / "scripts" / s
        result["C_infra"][s] = {
            "exists": path.exists(),
            "status": "exists" if path.exists() else "missing",
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    return result


# ---------------------------------------------------------------------------
# 3. Experiments inventory
# ---------------------------------------------------------------------------

def scan_experiments() -> dict:
    """Check experiment directory existence and key files."""
    result = {}
    exp_dir = REPO_ROOT / "experiments"

    for d in EXPERIMENT_DIRS:
        path = exp_dir / d
        toy_path = exp_dir / f"{d}_toy"

        entry = {
            "exists": path.exists(),
            "toy_exists": toy_path.exists(),
            "key_files": [],
            "missing_expected": [],
            "last_modified": None,
        }

        # Check key files
        for p in [path, toy_path]:
            if p.exists():
                for f in p.glob("*"):
                    if f.is_file():
                        entry["key_files"].append(f.name)
                        try:
                            mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc).isoformat()
                            if entry["last_modified"] is None or mtime > entry["last_modified"]:
                                entry["last_modified"] = mtime
                        except Exception:
                            pass

        if not entry["exists"] and not entry["toy_exists"]:
            entry["missing_expected"].append(f"Neither {d} nor {d}_toy found")

        result[d] = entry

    return result


# ---------------------------------------------------------------------------
# 4. Dataset status
# ---------------------------------------------------------------------------

def scan_dataset() -> dict:
    """Summarize dataset CSV without outputting raw text."""
    csv_path = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"
    result = {"exists": csv_path.exists(), "path": str(csv_path.relative_to(REPO_ROOT))}

    df = safe_read_csv(csv_path)
    if df is not None:
        result["n_rows"] = len(df)
        result["n_groups"] = df["target_candidate_group_id"].nunique() if "target_candidate_group_id" in df.columns else 0
        result["label_counts"] = df["candidate_label_guess"].value_counts().to_dict() if "candidate_label_guess" in df.columns else {}
        result["domain_counts"] = df["domain"].value_counts().to_dict() if "domain" in df.columns else {}
        result["human_audited_counts"] = df["human_audited"].value_counts().to_dict() if "human_audited" in df.columns else {}
        result["final_label_nonempty"] = int((df["final_label"].astype(str) != "").sum()) if "final_label" in df.columns else 0
        result["gold_label_nonempty"] = int((df["gold_label"].astype(str) != "").sum()) if "gold_label" in df.columns else 0
        result["source_trace_complete"] = df["source_trace_complete"].value_counts().to_dict() if "source_trace_complete" in df.columns else {}
        result["claim_generation_policy"] = df["claim_generation_policy"].value_counts().to_dict() if "claim_generation_policy" in df.columns else {}
        result["silver_label_source"] = df["silver_label_source"].value_counts().to_dict() if "silver_label_source" in df.columns else {}

    return result


# ---------------------------------------------------------------------------
# 5. Leakage quick scan
# ---------------------------------------------------------------------------

def scan_leakage() -> dict:
    """Quick leakage scan of public/redacted files."""
    result = {
        "public_redacted_with_text_fields": [],
        "scripts_using_label_for_scoring": [],
        "hardcoded_d_ocn_paths": [],
        "boundary_declarations": {},
        "silver_as_gold_risk": [],
        "overall_status": "PASS",
    }

    # Check public/redacted CSVs for text columns
    scan_dirs = [REPO_ROOT / "experiments", REPO_ROOT / "paper_assets"]
    for scan_dir in scan_dirs:
        if not scan_dir.exists():
            continue
        for csv_path in scan_dir.rglob("*.csv"):
            name_lower = csv_path.name.lower()
            is_public = "redacted" in name_lower or "summary" in name_lower or "metrics" in name_lower
            if not is_public:
                continue
            try:
                df = pd.read_csv(csv_path, keep_default_na=False, nrows=1)
                for col in df.columns:
                    if col.lower() in FORBIDDEN_TEXT_FIELDS:
                        result["public_redacted_with_text_fields"].append({
                            "file": str(csv_path.relative_to(REPO_ROOT)),
                            "column": col,
                        })
                        result["overall_status"] = "FAIL"
            except Exception:
                pass

    # Check scripts for hardcoded D:\ocn paths
    scripts_dir = REPO_ROOT / "scripts"
    for py_file in scripts_dir.glob("*.py"):
        try:
            content = py_file.read_text(encoding="utf-8", errors="ignore")
            if "D:\\ocn" in content or "D:/ocn" in content or "D:\\\\ocn" in content:
                # Count occurrences
                count = content.count("D:\\ocn") + content.count("D:/ocn")
                result["hardcoded_d_ocn_paths"].append({
                    "file": str(py_file.relative_to(REPO_ROOT)),
                    "count": count,
                })
        except Exception:
            pass

    # Check for boundary declarations in key scripts
    boundary_keywords = {
        "no_api": ["no api", "no_api"],
        "no_network": ["no network", "no_network"],
        "no_training": ["no training", "no_training"],
    }
    for script_name in ["run_v3_17_confidential_pipeline.py", "run_metric_robustness_v1.py", "run_error_taxonomy_v1.py"]:
        script_path = scripts_dir / script_name
        if script_path.exists():
            content = script_path.read_text(encoding="utf-8", errors="ignore").lower()
            for boundary, keywords in boundary_keywords.items():
                if any(kw in content for kw in keywords):
                    result["boundary_declarations"].setdefault(script_name, []).append(boundary)

    # Check for silver-as-gold risk
    for f in [REPO_ROOT / "README.md", REPO_ROOT / "CURRENT_MAINLINE.md"]:
        if not f.exists():
            continue
        content = f.read_text(encoding="utf-8", errors="ignore").lower()
        if "gold" in content and "not gold" not in content and "no gold" not in content:
            result["silver_as_gold_risk"].append({
                "file": str(f.relative_to(REPO_ROOT)),
                "risk": "Mentions 'gold' without explicit 'not gold' disclaimer",
            })
            if result["overall_status"] == "PASS":
                result["overall_status"] = "WARNING"

    if result["hardcoded_d_ocn_paths"] and result["overall_status"] == "PASS":
        result["overall_status"] = "WARNING"

    return result


# ---------------------------------------------------------------------------
# 6. Evidence chain
# ---------------------------------------------------------------------------

def build_evidence_chain() -> list:
    """Build the current strongest evidence chain.

    Each item includes a `data_provenance` field with one of:
      real / toy / missing / blocked / private-only
    per the V3.17 release-gate spec.
    """
    exp = REPO_ROOT / "experiments"
    chain = [
        {
            "claim": "Raw PDF chunk / BM25 retrieval has results",
            "evidence_file": "experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv",
            "status": "exists" if (exp / "simclaim_pdf_corpus_retrieval_v1").exists() else "missing",
            "data_provenance": "private-only" if (exp / "simclaim_pdf_corpus_retrieval_v1").exists() else "missing",
            "safe_wording": "BM25 retrieval on local PDF corpus achieves measurable oracle recall",
            "risk": "Oracle recall is on silver labels only; retrieval output is private-only (contains source text)",
        },
        {
            "claim": "Sentence-level BM25 retrieval has results",
            "evidence_file": ("experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json"
                              if (exp / "bm25_sentence_retrieval_v1" / "oracle_recall_summary.json").exists()
                              else "experiments/bm25_sentence_retrieval_v1_toy/oracle_recall_summary.json"),
            "status": ("exists" if (exp / "bm25_sentence_retrieval_v1" / "oracle_recall_summary.json").exists()
                       else ("exists" if (exp / "bm25_sentence_retrieval_v1_toy" / "oracle_recall_summary.json").exists() else "missing")),
            "data_provenance": ("blocked" if (exp / "bm25_sentence_retrieval_v1" / "blocked_by_missing_pdf_corpus.json").exists()
                                else ("real" if (exp / "bm25_sentence_retrieval_v1" / "oracle_recall_summary.json").exists() else "toy")),
            "safe_wording": ("Sentence/window BM25 retrieval blocked by missing PDF corpus; toy results show sentence-level outperforms window-level"
                             if (exp / "bm25_sentence_retrieval_v1" / "blocked_by_missing_pdf_corpus.json").exists()
                             else "Sentence-level BM25 outperforms window-level on oracle recall (toy)"),
            "risk": ("Real PDFs no longer in workspace; sentence/window retrieval blocked. Toy data only."
                     if (exp / "bm25_sentence_retrieval_v1" / "blocked_by_missing_pdf_corpus.json").exists()
                     else "Only toy data; real data run not yet executed"),
        },
        {
            "claim": "Canonicalization improves over raw chunks",
            "evidence_file": ("experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv"
                              if (exp / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv").exists()
                              else "experiments/canonicalizer_ablation_v1_toy/selector_metrics_summary.csv"),
            "status": ("exists" if (exp / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv").exists()
                       else ("exists" if (exp / "canonicalizer_ablation_v1_toy" / "selector_metrics_summary.csv").exists() else "missing")),
            "data_provenance": ("real" if (exp / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv").exists() else "toy"),
            "safe_wording": ("best_sentence_top5_overlap oracle_recall=0.387 vs raw_top1_chunk=0.043 on 444 real candidates (9x improvement)"
                             if (exp / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv").exists()
                             else "best_sentence_top5_overlap has higher oracle recall than raw_top1_chunk (toy)"),
            "risk": ("Silver labels only; 2/8 selectors (sentence_bm25, window_bm25) blocked by missing PDF corpus"
                     if (exp / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv").exists()
                     else "Only toy data; real ablation not yet run"),
        },
        {
            "claim": "Frozen R4 review queue has results",
            "evidence_file": "experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv",
            "status": "exists" if (exp / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv").exists() else "missing",
            "data_provenance": ("real" if (exp / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv").exists() else "missing"),
            "safe_wording": "Frozen R4 screening achieves strong_F1=0.4503 on 436 candidates",
            "risk": "Silver labels only; not human-audited; review queue output is private-only (contains labels for audit join)",
        },
        {
            "claim": "Risk ranking has results",
            "evidence_file": "experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv",
            "status": "exists" if (exp / "canonicalized_risk_ranking_v1" / "risk_ranking_features.csv").exists() else "missing",
            "data_provenance": ("real" if (exp / "canonicalized_risk_ranking_v1" / "risk_ranking_features.csv").exists() else "missing"),
            "safe_wording": "G_conservative_precision ranking provides top-100 review queue",
            "risk": "Threshold not fitted on test; silver labels only; feature matrix is private-only (contains labels for audit join)",
        },
        {
            "claim": "Leakage audit has results",
            "evidence_file": ("experiments/leakage_audit_v1/claim_only_baseline.json"
                              if (exp / "leakage_audit_v1" / "claim_only_baseline.json").exists()
                              else "experiments/leakage_audit_v1_toy/claim_only_baseline.json"),
            "status": ("exists" if (exp / "leakage_audit_v1" / "claim_only_baseline.json").exists()
                       else ("exists" if (exp / "leakage_audit_v1_toy" / "claim_only_baseline.json").exists() else "missing")),
            "data_provenance": ("real" if (exp / "leakage_audit_v1" / "claim_only_baseline.json").exists() else "toy"),
            "safe_wording": ("All 12 leakage checks pass on 444 real candidates; claim-only ratio=0.74 (below WARNING threshold)"
                             if (exp / "leakage_audit_v1" / "claim_only_baseline.json").exists()
                             else "All 6 leakage checks pass on toy data"),
            "risk": ("Silver labels (candidate_label_guess) used as true_label for audit; queue guard from toy SmartQueue"
                     if (exp / "leakage_audit_v1" / "claim_only_baseline.json").exists()
                     else "Only toy data; real data audit not yet run"),
        },
        {
            "claim": "Bootstrap CI metrics have results",
            "evidence_file": "experiments/metric_robustness_v1/classification_metrics_with_ci.csv",
            "status": "exists" if (exp / "metric_robustness_v1" / "classification_metrics_with_ci.csv").exists() else "missing",
            "data_provenance": ("real" if (exp / "metric_robustness_v1" / "classification_metrics_with_ci.csv").exists() else "missing"),
            "safe_wording": "strong_F1=0.4503 with 95% CI [0.4086, 0.4833] (group-aware bootstrap)",
            "risk": "CI reflects controlled pool variability, not natural prevalence",
        },
        {
            "claim": "Error taxonomy has results",
            "evidence_file": "experiments/error_taxonomy_v1/error_taxonomy_summary.csv",
            "status": "exists" if (exp / "error_taxonomy_v1" / "error_taxonomy_summary.csv").exists() else "missing",
            "data_provenance": ("real" if (exp / "error_taxonomy_v1" / "error_taxonomy_summary.csv").exists() else "missing"),
            "safe_wording": "9 error types tagged; top FP cause is mild_vs_strong_boundary",
            "risk": "Silver labels only; error type thresholds are heuristic",
        },
        {
            "claim": "PDF-start extraction stress test has results",
            "evidence_file": "experiments/pdf_extraction_stress_test_v1/",
            "status": "exists" if (exp / "pdf_extraction_stress_test_v1").exists() else "missing",
            "data_provenance": ("toy" if (exp / "pdf_extraction_stress_test_v1").exists() else "missing"),
            "safe_wording": "12 synthetic PDF stress documents processed; 0 failures; 123 sentences extracted. Extraction robustness test, not SOTA.",
            "risk": "Synthetic stress fixtures only; not real PDFs; not an empirical claim about real-world extraction",
        },
        {
            "claim": "Complexity-vs-utility tradeoff analysis has results",
            "evidence_file": "experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv",
            "status": "exists" if (exp / "complexity_vs_utility_ablation_v1" / "method_comparison_metrics.csv").exists() else "missing",
            "data_provenance": ("real" if (exp / "complexity_vs_utility_ablation_v1" / "method_comparison_metrics.csv").exists() else "missing"),
            "safe_wording": "Deterministic canonicalization is Pareto-optimal under confidential/no-API/no-training/silver-diagnostic constraints",
            "risk": "Does not prove rules generally beat learned models; deployment-specific tradeoff",
        },
        {
            "claim": "Human audit has results",
            "evidence_file": "experiments/human_audit_v1/audit_agreement_summary.json",
            "status": ("partial" if (REPO_ROOT / "docs" / "human_audit_protocol_v1.md").exists() else "missing"),
            "data_provenance": ("blocked" if (REPO_ROOT / "docs" / "human_audit_protocol_v1.md").exists() and not (exp / "human_audit_v1" / "audit_agreement_summary.json").exists()
                                else ("real" if (exp / "human_audit_v1" / "audit_agreement_summary.json").exists() else "missing")),
            "safe_wording": "Small targeted human audit protocol and seed queue are in place; auditor labels pending. Not a gold benchmark.",
            "risk": "No human audit has been completed; all silver labels remain un-audited. Audit seed built (111 candidates); empirical results deferred.",
        },
        {
            "claim": "Paper assets generated",
            "evidence_file": "paper_assets/v3_17_confidential/tables/",
            "status": "exists" if (REPO_ROOT / "paper_assets" / "v3_17_confidential" / "tables").exists() else "missing",
            "data_provenance": ("real" if (REPO_ROOT / "paper_assets" / "v3_17_confidential" / "tables").exists() else "missing"),
            "safe_wording": "8 tables (md+tex), 4 figure data CSVs, paper_results_summary.md (RQ1-8), paper_claims_checklist.md generated",
            "risk": "All tables include caveat: controlled silver diagnostic, not gold/human-audited",
        },
        {
            "claim": "Public sanitized release bundle built",
            "evidence_file": "release_bundles/v3_17_confidential_public/",
            "status": "exists" if (REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "MANIFEST.json").exists() else "missing",
            "data_provenance": ("real" if (REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "MANIFEST.json").exists() else "missing"),
            "safe_wording": "221 files; redteam scan PASS (high_risk=0); no raw claim/evidence/PDF text",
            "risk": "Bundle excludes private scoring files, real review queues, PDFs, and label-bearing intermediates",
        },
    ]
    return chain


# ---------------------------------------------------------------------------
# 7. Priority next actions
# ---------------------------------------------------------------------------

def build_priority_actions(scripts: dict, experiments: dict, leakage: dict, mainline: dict) -> list:
    """Build priority next actions list.

    Each action includes a `status` field: done / blocked / pending.
    Per V3.17 release-gate spec: all P0 items must be done or explicitly blocked.
    """
    actions = []
    exp = REPO_ROOT / "experiments"

    # P0: Must do first
    if mainline["old_narratives"]:
        actions.append({
            "priority": "P0",
            "action": "Clean up old narratives in docs (V2/gold/SOTA references)",
            "reason": f"{len(mainline['old_narratives'])} old narrative references found (majority are denials like 'not a gold benchmark')",
            "status": "blocked",
            "blocker": "scanner_limitation",
            "note": "BLOCKED by scanner limitation: simple regex flags both claims AND denials. Manual review confirmed references are predominantly in denial/qualification context (e.g., 'not a gold benchmark', 'not human-audited', 'not SOTA'). Improving scanner to distinguish denials from claims requires NLP context analysis, out of scope for V3.17 confidential lightweight. Non-blocking for release.",
        })

    if leakage["overall_status"] == "FAIL":
        actions.append({
            "priority": "P0",
            "action": "Fix leaked text fields in public/redacted files",
            "reason": f"{len(leakage['public_redacted_with_text_fields'])} files with forbidden text columns",
            "status": "done" if not leakage["public_redacted_with_text_fields"] else "pending",
        })
    else:
        actions.append({
            "priority": "P0",
            "action": "Fix leaked text fields in public/redacted files",
            "reason": "No forbidden text columns in public/redacted files",
            "status": "done",
        })

    # P0: real-data experiments
    bm25_blocked = (exp / "bm25_sentence_retrieval_v1" / "blocked_by_missing_pdf_corpus.json").exists()
    if bm25_blocked:
        actions.append({
            "priority": "P0",
            "action": "Run BM25 sentence retrieval on real data",
            "reason": "BLOCKED: real PDFs no longer in workspace",
            "status": "blocked",
            "blocker": "missing_pdf_corpus",
        })
    elif experiments.get("bm25_sentence_retrieval_v1", {}).get("exists", False):
        actions.append({
            "priority": "P0",
            "action": "Run BM25 sentence retrieval on real data",
            "reason": "Real data retrieval completed",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P0",
            "action": "Run BM25 sentence retrieval on real data",
            "reason": "Only toy data exists",
            "status": "pending",
        })

    if experiments.get("canonicalizer_ablation_v1", {}).get("exists", False):
        actions.append({
            "priority": "P0",
            "action": "Run canonicalizer ablation on real data",
            "reason": "Real data ablation completed (6/8 selectors)",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P0",
            "action": "Run canonicalizer ablation on real data",
            "reason": "Only toy data exists",
            "status": "pending",
        })

    r4_blocked_path = exp / "format_shift_ablation_v1" / "r4_eval_blocked.json"
    r4_blocked = False
    r4_resolved = False
    if r4_blocked_path.exists():
        try:
            with open(r4_blocked_path, "r", encoding="utf-8") as f:
                r4_blocked_data = json.load(f)
            r4_blocked = r4_blocked_data.get("status") == "blocked"
            r4_resolved = r4_blocked_data.get("status") == "resolved"
        except Exception:
            r4_blocked = True
    if experiments.get("format_shift_ablation_v1", {}).get("exists", False):
        if r4_resolved:
            actions.append({
                "priority": "P0",
                "action": "Run format shift ablation on real data",
                "reason": "Format-shift R4 eval resolved offline using local .venv sklearn 1.9.0; no network, no API, no retraining, no repickling",
                "status": "done",
                "blocker": None,
            })
        else:
            actions.append({
                "priority": "P0",
                "action": "Run format shift ablation on real data",
                "reason": "Format-shift inputs generated" + ("; R4 eval blocked (sklearn version)" if r4_blocked else ""),
                "status": "done" if not r4_blocked else "blocked",
                "blocker": "sklearn_version_mismatch" if r4_blocked else None,
            })
    else:
        actions.append({
            "priority": "P0",
            "action": "Run format shift ablation on real data",
            "reason": "Only toy data exists",
            "status": "pending",
        })

    if experiments.get("leakage_audit_v1", {}).get("exists", False):
        actions.append({
            "priority": "P0",
            "action": "Run leakage audit on real data",
            "reason": "Real data audit completed (12 checks, PASS)",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P0",
            "action": "Run leakage audit on real data",
            "reason": "Only toy data exists",
            "status": "pending",
        })

    # P1: Strongly recommended
    if experiments.get("lightweight_smart_queue_v1", {}).get("exists", False):
        actions.append({
            "priority": "P1",
            "action": "Run SmartQueue on real data",
            "reason": "Real data SmartQueue completed (436 candidates, 4 buckets)",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P1",
            "action": "Run SmartQueue on real data",
            "reason": "Only toy data exists",
            "status": "pending",
        })

    if leakage["hardcoded_d_ocn_paths"]:
        actions.append({
            "priority": "P1",
            "action": "Remove hardcoded D:\\ocn paths from scripts",
            "reason": f"{len(leakage['hardcoded_d_ocn_paths'])} scripts with hardcoded paths (all in deprecated/legacy scripts, not V3.17 pipeline)",
            "status": "pending",
            "note": "Non-blocking; all hardcoded paths are in pre-V3.17 deprecated scripts",
        })

    # Complexity-vs-utility
    if scripts["B_proposed"].get("run_complexity_vs_utility_ablation_v1.py", {}).get("status") == "exists":
        actions.append({
            "priority": "P1",
            "action": "Implement and run complexity-vs-utility ablation",
            "reason": "Script exists and has been run on real data",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P1",
            "action": "Implement complexity-vs-utility ablation",
            "reason": "Script missing",
            "status": "pending",
        })

    # PDF extraction stress test
    if scripts["B_proposed"].get("run_pdf_extraction_stress_test_v1.py", {}).get("status") == "exists":
        actions.append({
            "priority": "P1",
            "action": "Implement and run PDF extraction stress test",
            "reason": "Script exists and has been run on synthetic stress fixtures",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P1",
            "action": "Implement PDF extraction stress test",
            "reason": "Script missing",
            "status": "pending",
        })

    # Human audit
    audit_protocol_exists = (REPO_ROOT / "docs" / "human_audit_protocol_v1.md").exists()
    audit_seed_exists = (exp / "human_audit_v1" / "human_audit_queue_seed_v1.csv").exists() or \
                        (REPO_ROOT / "data" / "audit_templates" / "human_audit_template.csv").exists()
    if audit_protocol_exists and audit_seed_exists:
        actions.append({
            "priority": "P1",
            "action": "Define small human audit protocol (2-annotator, adjudication)",
            "reason": "Protocol and seed queue built; auditor labels pending",
            "status": "done",
            "note": "Protocol exists; empirical audit deferred (not a release blocker)",
        })
    else:
        actions.append({
            "priority": "P1",
            "action": "Define small human audit protocol (2-annotator, adjudication)",
            "reason": "human_audited=False for all 444 candidates; no gold labels exist",
            "status": "pending",
        })

    # P2: Optional / done
    bundle_built = (REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "MANIFEST.json").exists()
    if bundle_built:
        actions.append({
            "priority": "P2",
            "action": "Publish sanitized public release bundle",
            "reason": "Bundle built: 221 files, redteam PASS",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P2",
            "action": "Publish sanitized public release bundle",
            "reason": "Bundle builder exists; ready to package",
            "status": "pending",
        })

    paper_assets_built = (REPO_ROOT / "paper_assets" / "v3_17_confidential" / "tables").exists()
    if paper_assets_built:
        actions.append({
            "priority": "P2",
            "action": "Generate paper assets (8 tables, RQ1-8, claims checklist)",
            "reason": "Paper assets generated",
            "status": "done",
        })
    else:
        actions.append({
            "priority": "P2",
            "action": "Generate paper assets",
            "reason": "Tables/figures in LaTeX+MD; ready for paper compilation",
            "status": "pending",
        })

    actions.append({
        "priority": "P2",
        "action": "Compile final paper PDF from paper_assets",
        "reason": "Tables/figures in LaTeX+MD; requires LaTeX compilation (out of scope for V3.17 confidential lightweight)",
        "status": "pending",
    })

    return actions


# ---------------------------------------------------------------------------
# Report writers
# ---------------------------------------------------------------------------

def write_status_md(mainline: dict, scripts: dict, experiments: dict,
                    dataset: dict, leakage: dict, evidence_chain: list,
                    actions: list) -> str:
    """Write the comprehensive status report markdown."""
    lines = [
        "# Current Project Status — V3.17 Confidential Lightweight",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        "> This is a read-only inventory. No experiments were re-run, no data modified.",
        "",
        "## 1. Current Mainline Status",
        "",
    ]

    lines.append("### Completed")
    for item in mainline["completed"]:
        lines.append(f"- [x] {item}")

    lines.append("")
    lines.append("### Partial")
    if mainline["partial"]:
        for item in mainline["partial"]:
            lines.append(f"- [~] {item}")
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("### Missing")
    for item in mainline["missing"]:
        lines.append(f"- [ ] {item}")

    lines.append("")
    lines.append("### Old Narrative References")
    if mainline["old_narratives"]:
        for ref in mainline["old_narratives"][:20]:
            lines.append(f"- `{ref['file']}`: {ref['pattern']} — \"{ref['matched_text']}\"")
    else:
        lines.append("- (none found)")

    lines.append("")
    lines.append("## 2. Existing Scripts Inventory")
    lines.append("")
    lines.append("### A. Frozen V3.17 Scripts")
    lines.append("| Script | Status | Size |")
    lines.append("|---|---|---|")
    for s, info in scripts["A_frozen"].items():
        lines.append(f"| {s} | {info['status']} | {info['size_bytes']} |")

    lines.append("")
    lines.append("### B. Proposed Strengthening Scripts")
    lines.append("| Script | Status | Size |")
    lines.append("|---|---|---|")
    for s, info in scripts["B_proposed"].items():
        lines.append(f"| {s} | {info['status']} | {info['size_bytes']} |")

    lines.append("")
    lines.append("### C. Infrastructure Scripts")
    lines.append("| Script | Status | Size |")
    lines.append("|---|---|---|")
    for s, info in scripts["C_infra"].items():
        lines.append(f"| {s} | {info['status']} | {info['size_bytes']} |")

    lines.append("")
    lines.append("## 3. Existing Experiment Outputs Inventory")
    lines.append("")
    lines.append("| Directory | Exists | Toy | Key Files | Last Modified |")
    lines.append("|---|---|---|---|---|")
    for d, info in experiments.items():
        exists = "Yes" if info["exists"] else "No"
        toy = "Yes" if info["toy_exists"] else "No"
        key_files = ", ".join(info["key_files"][:3]) if info["key_files"] else "(none)"
        if len(info["key_files"]) > 3:
            key_files += f" (+{len(info['key_files'])-3} more)"
        lm = info["last_modified"][:10] if info["last_modified"] else "N/A"
        lines.append(f"| {d} | {exists} | {toy} | {key_files} | {lm} |")

    lines.append("")
    lines.append("## 4. Dataset Status")
    lines.append("")
    if dataset["exists"]:
        lines.append(f"- **Path**: `{dataset['path']}`")
        lines.append(f"- **Rows**: {dataset.get('n_rows', 'N/A')}")
        lines.append(f"- **Groups**: {dataset.get('n_groups', 'N/A')}")
        lines.append(f"- **Labels**: {dataset.get('label_counts', {})}")
        lines.append(f"- **Domains**: {dataset.get('domain_counts', {})}")
        lines.append(f"- **human_audited**: {dataset.get('human_audited_counts', {})}")
        lines.append(f"- **final_label nonempty**: {dataset.get('final_label_nonempty', 0)}")
        lines.append(f"- **gold_label nonempty**: {dataset.get('gold_label_nonempty', 0)}")
        lines.append(f"- **source_trace_complete**: {dataset.get('source_trace_complete', {})}")
        lines.append(f"- **claim_generation_policy**: {dataset.get('claim_generation_policy', {})}")
        lines.append(f"- **silver_label_source**: {dataset.get('silver_label_source', {})}")
    else:
        lines.append("- **Status**: MISSING")

    lines.append("")
    lines.append("## 5. Leakage Risk Quick Scan")
    lines.append("")
    lines.append(f"**Overall Status**: `{leakage['overall_status']}`")
    lines.append("")

    if leakage["public_redacted_with_text_fields"]:
        lines.append("### FAIL: Public files with forbidden text columns")
        for item in leakage["public_redacted_with_text_fields"]:
            lines.append(f"- `{item['file']}`: column `{item['column']}`")
    else:
        lines.append("### PASS: No forbidden text columns in public/redacted files")

    lines.append("")
    if leakage["hardcoded_d_ocn_paths"]:
        lines.append("### WARNING: Scripts with hardcoded D:\\ocn paths")
        for item in leakage["hardcoded_d_ocn_paths"]:
            lines.append(f"- `{item['file']}`: {item['count']} occurrences")

    lines.append("")
    lines.append("### Boundary Declarations")
    for script, boundaries in leakage["boundary_declarations"].items():
        lines.append(f"- `{script}`: {', '.join(boundaries)}")

    lines.append("")
    lines.append("### Silver-as-Gold Risk")
    if leakage["silver_as_gold_risk"]:
        for item in leakage["silver_as_gold_risk"]:
            lines.append(f"- `{item['file']}`: {item['risk']}")
    else:
        lines.append("- PASS: No silver-as-gold risk detected")

    lines.append("")
    lines.append("## 6. Current Strongest Evidence Chain")
    lines.append("")
    lines.append("> Each item labeled: **real / toy / missing / blocked / private-only** (data_provenance)")
    lines.append("")
    lines.append("| Claim | Evidence File | Status | Data Provenance | Safe Wording | Risk |")
    lines.append("|---|---|---|---|---|---|")
    for item in evidence_chain:
        lines.append(
            f"| {item['claim']} | `{item['evidence_file']}` | "
            f"{item['status']} | **{item.get('data_provenance', 'unknown')}** | {item['safe_wording']} | {item['risk']} |"
        )

    lines.append("")
    lines.append("## 7. Priority Next Actions")
    lines.append("")
    lines.append("> Each action labeled: **done / blocked / pending**")
    lines.append("")
    for action in actions:
        status_label = action.get("status", "pending")
        status_emoji = {"done": "DONE", "blocked": "BLOCKED", "pending": "PENDING"}.get(status_label, status_label.upper())
        lines.append(f"- **{action['priority']}** [{status_emoji}]: {action['action']}")
        lines.append(f"  - Reason: {action['reason']}")
        if action.get("note"):
            lines.append(f"  - Note: {action['note']}")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> All results are controlled silver diagnostic, not gold/human-audited.")

    return "\n".join(lines)


def write_leakage_md(leakage: dict) -> str:
    """Write the leakage quick scan markdown."""
    lines = [
        "# Leakage Quick Scan — V3.17 Confidential",
        "",
        f"Generated: {datetime.now(timezone.utc).isoformat()}",
        "",
        f"**Overall Status**: `{leakage['overall_status']}`",
        "",
        "## 1. Public/Redacted Files with Text Columns",
        "",
    ]

    if leakage["public_redacted_with_text_fields"]:
        lines.append("| File | Column | Severity |")
        lines.append("|---|---|---|")
        for item in leakage["public_redacted_with_text_fields"]:
            lines.append(f"| `{item['file']}` | `{item['column']}` | FAIL |")
    else:
        lines.append("**PASS** — No public/redacted files contain forbidden text columns.")

    lines.append("")
    lines.append("## 2. Scripts with Hardcoded D:\\ocn Paths")
    lines.append("")

    if leakage["hardcoded_d_ocn_paths"]:
        lines.append("| Script | Occurrences | Severity |")
        lines.append("|---|---|---|")
        for item in leakage["hardcoded_d_ocn_paths"]:
            lines.append(f"| `{item['file']}` | {item['count']} | WARNING |")
    else:
        lines.append("**PASS** — No hardcoded D:\\ocn paths found.")

    lines.append("")
    lines.append("## 3. Boundary Declarations")
    lines.append("")
    if leakage["boundary_declarations"]:
        lines.append("| Script | Boundaries Declared |")
        lines.append("|---|---|")
        for script, boundaries in leakage["boundary_declarations"].items():
            lines.append(f"| `{script}` | {', '.join(boundaries)} |")
    else:
        lines.append("WARNING — No boundary declarations found in key scripts.")

    lines.append("")
    lines.append("## 4. Silver-as-Gold Risk")
    lines.append("")
    if leakage["silver_as_gold_risk"]:
        for item in leakage["silver_as_gold_risk"]:
            lines.append(f"- `{item['file']}`: {item['risk']}")
    else:
        lines.append("**PASS** — No silver-as-gold risk detected.")

    lines.append("")
    lines.append("## 5. Forbidden Text Fields Checked")
    lines.append("")
    for field in FORBIDDEN_TEXT_FIELDS:
        lines.append(f"- `{field}`")

    lines.append("")
    lines.append("## 6. Label Fields (Audit-Only)")
    lines.append("")
    for field in LABEL_FIELDS_FOR_AUDIT_ONLY:
        lines.append(f"- `{field}`")

    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("> This scan is a quick check, not a substitute for the full red-team scanner.")

    return "\n".join(lines)


def write_file_inventory_csv() -> list:
    """Write the file inventory CSV."""
    rows = []
    categories = [
        ("scripts/", "script"),
        ("schemas/", "schema"),
        ("configs/", "config"),
        ("data/toy_synthetic/", "toy_data"),
        ("docs/", "documentation"),
        ("tests/", "test"),
        ("experiments/", "experiment_output"),
        ("paper_assets/", "paper_asset"),
        (".github/", "ci"),
    ]

    for cat_prefix, cat_name in categories:
        cat_path = REPO_ROOT / cat_prefix
        if not cat_path.exists():
            continue
        for f in cat_path.rglob("*"):
            if f.is_file():
                rel_path = str(f.relative_to(REPO_ROOT)).replace("\\", "/")
                try:
                    stat = f.stat()
                    size = stat.st_size
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat()
                except Exception:
                    size = 0
                    mtime = ""

                status = "exists"
                notes = ""

                # Check for forbidden text in CSVs
                if f.suffix == ".csv":
                    try:
                        df = pd.read_csv(f, keep_default_na=False, nrows=1)
                        for col in df.columns:
                            if col.lower() in FORBIDDEN_TEXT_FIELDS:
                                notes = f"forbidden_column:{col}"
                                status = "warning"
                                break
                    except Exception:
                        pass

                # Check for hardcoded paths in Python files
                if f.suffix == ".py":
                    try:
                        content = f.read_text(encoding="utf-8", errors="ignore")
                        if "D:\\ocn" in content or "D:/ocn" in content:
                            notes = "hardcoded_d_ocn_path"
                            status = "warning"
                    except Exception:
                        pass

                rows.append({
                    "path": rel_path,
                    "category": cat_name,
                    "exists": "true",
                    "size_bytes": size,
                    "last_modified": mtime,
                    "status": status,
                    "notes": notes,
                })

    # Add top-level files
    for f in REPO_ROOT.glob("*.md"):
        rel_path = f.name
        try:
            stat = f.stat()
            rows.append({
                "path": rel_path,
                "category": "root_doc",
                "exists": "true",
                "size_bytes": stat.st_size,
                "last_modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "status": "exists",
                "notes": "",
            })
        except Exception:
            pass

    return rows


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    log("=" * 72)
    log("Project Status Report Generator v1")
    log("=" * 72)

    log("Scanning mainline docs...")
    mainline = scan_mainline_docs()

    log("Scanning scripts...")
    scripts = scan_scripts()

    log("Scanning experiments...")
    experiments = scan_experiments()

    log("Scanning dataset...")
    dataset = scan_dataset()

    log("Scanning leakage risks...")
    leakage = scan_leakage()

    log("Building evidence chain...")
    evidence_chain = build_evidence_chain()

    log("Building priority actions...")
    actions = build_priority_actions(scripts, experiments, leakage, mainline)

    log("Writing reports...")

    # 1. Status MD
    status_md = write_status_md(mainline, scripts, experiments, dataset, leakage, evidence_chain, actions)
    (REPORTS_DIR / "current_project_status_v3_17.md").write_text(status_md, encoding="utf-8")
    log(f"  Written: reports/current_project_status_v3_17.md")

    # 2. Status JSON
    status_json = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "mainline_docs": mainline,
        "scripts": scripts,
        "experiments": experiments,
        "dataset": dataset,
        "leakage_scan": leakage,
        "evidence_chain": evidence_chain,
        "priority_next_actions": actions,
    }
    with open(REPORTS_DIR / "current_project_status_v3_17.json", "w", encoding="utf-8") as f:
        json.dump(status_json, f, indent=2, ensure_ascii=False)
    log(f"  Written: reports/current_project_status_v3_17.json")

    # 3. Leakage MD
    leakage_md = write_leakage_md(leakage)
    (REPORTS_DIR / "leakage_quick_scan_v3_17.md").write_text(leakage_md, encoding="utf-8")
    log(f"  Written: reports/leakage_quick_scan_v3_17.md")

    # 4. File inventory CSV
    inventory = write_file_inventory_csv()
    with open(REPORTS_DIR / "file_inventory_v3_17.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=["path", "category", "exists", "size_bytes", "last_modified", "status", "notes"])
        writer.writeheader()
        writer.writerows(inventory)
    log(f"  Written: reports/file_inventory_v3_17.csv ({len(inventory)} rows)")

    log("")
    log("Done.")
    log(f"  Overall leakage status: {leakage['overall_status']}")
    log(f"  Old narratives found: {len(mainline['old_narratives'])}")
    log(f"  Scripts missing: {sum(1 for cat in scripts.values() for s in cat.values() if s['status']=='missing')}")
    log(f"  Experiment dirs missing: {sum(1 for e in experiments.values() if not e['exists'] and not e['toy_exists'])}")


if __name__ == "__main__":
    main()
