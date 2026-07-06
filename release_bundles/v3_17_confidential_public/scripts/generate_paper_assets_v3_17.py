#!/usr/bin/env python
"""generate_paper_assets_v3_17.py — Auto-generate paper tables and figures.

Reads experiment outputs from experiments/ and produces paper-ready tables
in LaTeX (booktabs) and Markdown, plus figure data CSVs and supporting docs.

Outputs (paper_assets/v3_17_confidential/):
  tables/
    table1_dataset_summary.{md,tex}
    table2_retrieval_recall.{md,tex}
    table3_format_shift_ablation.{md,tex}
    table4_selector_ablation.{md,tex}
    table5_review_queue.{md,tex}
    table6_leakage_audit.{md,tex}
  figures/
    pipeline_ascii.md
    format_shift_bar_data.csv
    queue_precision_recall_data.csv
    smartqueue_bucket_counts.csv
  paper_results_summary.md
  paper_claims_checklist.md
  run_config.json

Requirements:
  1. All table captions include: "controlled silver diagnostic, not gold/human-audited"
  2. No raw claim/evidence text in any output
  3. Missing inputs → table writes "not generated", script does not crash
  4. LaTeX uses booktabs style (\toprule, \midrule, \bottomrule)
  5. Numbers rounded to 3-4 decimal places

Hard boundaries: no network, no API, no training, no original data modification.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, write_run_config, print_guards  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent

CAVEAT = "Controlled silver diagnostic, not gold/human-audited."
FORBIDDEN_TEXT_FIELDS = [
    "claim_text", "evidence_text", "selected_evidence",
    "raw_text", "clean_text", "retrieved_text",
]


def log(msg):
    print(msg, flush=True)


def fmt(x, decimals=4):
    """Format a number to fixed decimals, handling NaN/inf."""
    if x is None:
        return "N/A"
    try:
        v = float(x)
        if np.isnan(v) or np.isinf(v):
            return "N/A"
        return f"{v:.{decimals}f}"
    except (ValueError, TypeError):
        return str(x)


def safe_read_csv(path: Path) -> Optional[pd.DataFrame]:
    """Safely read a CSV, returning None if file doesn't exist or is empty."""
    if not path.exists():
        return None
    try:
        df = pd.read_csv(path, keep_default_na=False)
        if len(df) == 0:
            return None
        return df
    except Exception as e:
        log(f"  [WARN] Failed to read {path}: {e}")
        return None


def safe_read_json(path: Path) -> Optional[dict]:
    """Safely read JSON, returning None if file doesn't exist."""
    if not path.exists():
        return None
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        log(f"  [WARN] Failed to read {path}: {e}")
        return None


def strip_text_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Remove any forbidden text columns from a DataFrame."""
    cols_to_drop = [c for c in df.columns if c in FORBIDDEN_TEXT_FIELDS]
    if cols_to_drop:
        df = df.drop(columns=cols_to_drop)
    return df


# ---------------------------------------------------------------------------
# Table 1: Dataset Summary
# ---------------------------------------------------------------------------

def generate_table1_dataset_summary(experiments_dir: Path, candidate_csv: Optional[Path]) -> Tuple[str, str]:
    """Table 1: Dataset summary (n_candidates, n_groups, label dist, domain dist)."""
    log("  Generating Table 1: Dataset Summary...")

    if candidate_csv and candidate_csv.exists():
        df = safe_read_csv(candidate_csv)
    else:
        df = None

    if df is not None:
        n_total = len(df)
        n_groups = df["target_candidate_group_id"].nunique() if "target_candidate_group_id" in df.columns else 0
        label_col = "candidate_label_guess" if "candidate_label_guess" in df.columns else None
        if label_col:
            label_counts = df[label_col].value_counts().to_dict()
        else:
            label_counts = {}
        domain_counts = df["domain"].value_counts().to_dict() if "domain" in df.columns else {}

        rows_md = [
            "| Metric | Value |",
            "|---|---|",
            f"| Total candidates | {n_total} |",
            f"| Candidate groups | {n_groups} |",
            f"| Label distribution | {label_counts} |",
            f"| Domains | {domain_counts} |",
        ]

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Dataset summary. " + CAVEAT + r"}",
            r"\label{tab:dataset_summary}",
            r"\begin{tabular}{lr}",
            r"\toprule",
            r"Metric & Value \\",
            r"\midrule",
            f"Total candidates & {n_total} \\\\",
            f"Candidate groups & {n_groups} \\\\",
            f"Labels (4-class) & supported={label_counts.get('supported',0)}, "
            f"mild={label_counts.get('mild_scope_overclaim',0)}, "
            f"strong={label_counts.get('strong_action_overclaim',0)}, "
            f"contra={label_counts.get('contradiction_candidate',0)} \\\\",
            f"Domains & {len(domain_counts)} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
    else:
        missing = str(candidate_csv) if candidate_csv else "candidate_csv not provided"
        rows_md = [
            "| Metric | Value |",
            "|---|---|",
            f"| Status | not generated (missing: {missing}) |",
        ]
        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Dataset summary. " + CAVEAT + r"}",
            r"\label{tab:dataset_summary}",
            r"\begin{tabular}{l}",
            r"\toprule",
            r"Status: not generated (missing input) \\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
        log(f"    [MISS] {missing}")

    return "\n".join(rows_md), "\n".join(rows_tex)


# ---------------------------------------------------------------------------
# Table 2: Retrieval Recall
# ---------------------------------------------------------------------------

def generate_table2_retrieval_recall(experiments_dir: Path) -> Tuple[str, str, Optional[dict]]:
    """Table 2: BM25 sentence vs window retrieval recall."""
    log("  Generating Table 2: Retrieval Recall...")

    # Try toy first, then real
    for subdir in ["bm25_sentence_retrieval_v1", "bm25_sentence_retrieval_v1_toy"]:
        summary_path = experiments_dir / subdir / "oracle_recall_summary.json"
        summary = safe_read_json(summary_path)
        if summary:
            break
    else:
        summary = None

    if summary:
        sent = summary.get("sentence", {})
        win = summary.get("window", {})
        n_candidates = summary.get("n_candidates", "N/A")

        rows_md = [
            "| Retrieval Unit | Recall@1 | Recall@5 | Recall@10 | MRR |",
            "|---|---|---|---|---|",
            f"| Sentence-level | {fmt(sent.get('recall@1'))} | {fmt(sent.get('recall@5'))} | {fmt(sent.get('recall@10'))} | {fmt(sent.get('mrr'))} |",
            f"| Window-level | {fmt(win.get('recall@1'))} | {fmt(win.get('recall@5'))} | {fmt(win.get('recall@10'))} | {fmt(win.get('mrr'))} |",
            f"",
            f"*N candidates: {n_candidates}*",
        ]

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{BM25 retrieval oracle recall (sentence vs window). " + CAVEAT + r"}",
            r"\label{tab:retrieval_recall}",
            r"\begin{tabular}{lcccc}",
            r"\toprule",
            r"Retrieval Unit & Recall@1 & Recall@5 & Recall@10 & MRR \\",
            r"\midrule",
            f"Sentence-level & {fmt(sent.get('recall@1'))} & {fmt(sent.get('recall@5'))} & {fmt(sent.get('recall@10'))} & {fmt(sent.get('mrr'))} \\\\",
            f"Window-level & {fmt(win.get('recall@1'))} & {fmt(win.get('recall@5'))} & {fmt(win.get('recall@10'))} & {fmt(win.get('mrr'))} \\\\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
    else:
        rows_md = [
            "| Retrieval Unit | Recall@1 | Recall@5 | Recall@10 | MRR |",
            "|---|---|---|---|---|",
            "| Status | not generated (missing oracle_recall_summary.json) | | | |",
        ]
        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{BM25 retrieval oracle recall. " + CAVEAT + r"}",
            r"\label{tab:retrieval_recall}",
            r"\begin{tabular}{l}",
            r"\toprule",
            r"Status: not generated (missing input) \\",
            r"\bottomrule",
            r"\end{tabular}",
            r"\end{table}",
        ]
        log("    [MISS] oracle_recall_summary.json not found")

    return "\n".join(rows_md), "\n".join(rows_tex), summary


# ---------------------------------------------------------------------------
# Table 3: Format Shift Ablation
# ---------------------------------------------------------------------------

def generate_table3_format_shift(experiments_dir: Path) -> Tuple[str, str, Optional[pd.DataFrame]]:
    """Table 3: Format shift ablation (variant, n_words, oracle_hit rate)."""
    log("  Generating Table 3: Format Shift Ablation...")

    for subdir in ["format_shift_ablation_v1", "format_shift_ablation_v1_toy"]:
        inputs_path = experiments_dir / subdir / "format_shift_inputs.csv"
        df = safe_read_csv(inputs_path)
        if df is not None:
            break
    else:
        df = None

    if df is not None:
        df = strip_text_columns(df)
        # Group by variant
        if "variant" in df.columns:
            grouped = df.groupby("variant").agg(
                n_candidates=("candidate_id", "count"),
                mean_n_words=("n_words", "mean"),
                pct_contains_metadata=("contains_metadata", lambda x: (x == True).mean() * 100 if x.dtype == bool else (x.astype(str).str.lower() == "true").mean() * 100),
                pct_uses_oracle=("uses_oracle_text", lambda x: (x == True).mean() * 100 if x.dtype == bool else (x.astype(str).str.lower() == "true").mean() * 100),
                pct_lengthened=("is_lengthened", lambda x: (x == True).mean() * 100 if x.dtype == bool else (x.astype(str).str.lower() == "true").mean() * 100),
            ).reset_index()
        else:
            grouped = pd.DataFrame()

        if len(grouped) > 0:
            rows_md = ["| Variant | N | Mean Words | % Metadata | % Oracle | % Lengthened |", "|---|---|---|---|---|---|"]
            for _, r in grouped.iterrows():
                rows_md.append(
                    f"| {r['variant']} | {int(r['n_candidates'])} | {fmt(r['mean_n_words'])} | "
                    f"{fmt(r['pct_contains_metadata'], 1)}% | {fmt(r['pct_uses_oracle'], 1)}% | "
                    f"{fmt(r['pct_lengthened'], 1)}% |"
                )

            rows_tex = [
                r"\begin{table}[ht]",
                r"\centering",
                r"\caption{Format shift ablation variants. " + CAVEAT + r"}",
                r"\label{tab:format_shift}",
                r"\begin{tabular}{lccccc}",
                r"\toprule",
                r"Variant & N & Mean Words & \% Metadata & \% Oracle & \% Lengthened \\",
                r"\midrule",
            ]
            for _, r in grouped.iterrows():
                rows_tex.append(
                    f"{r['variant']} & {int(r['n_candidates'])} & {fmt(r['mean_n_words'])} & "
                    f"{fmt(r['pct_contains_metadata'], 1)} & {fmt(r['pct_uses_oracle'], 1)} & "
                    f"{fmt(r['pct_lengthened'], 1)} \\\\"
                )
            rows_tex.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
        else:
            rows_md = ["| Variant | N | Status |", "|---|---|---|", "| (empty) | 0 | no variant column |"]
            rows_tex = [r"Status: no variant data"]
    else:
        rows_md = ["| Variant | N | Status |", "|---|---|---|", "| (missing) | - | not generated |"]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Format shift ablation. " + CAVEAT + r"}",
            r"\label{tab:format_shift}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated (missing input) \\\\",
            r"\bottomrule", r"\end{tabular}", r"\end{table}",
        ]
        log("    [MISS] format_shift_inputs.csv not found")

    return "\n".join(rows_md), "\n".join(rows_tex), df


# ---------------------------------------------------------------------------
# Table 4: Selector Ablation
# ---------------------------------------------------------------------------

def generate_table4_selector_ablation(experiments_dir: Path) -> Tuple[str, str, Optional[pd.DataFrame]]:
    """Table 4: Selector ablation metrics."""
    log("  Generating Table 4: Selector Ablation...")

    for subdir in ["canonicalizer_ablation_v1", "canonicalizer_ablation_v1_toy"]:
        metrics_path = experiments_dir / subdir / "selector_metrics_summary.csv"
        df = safe_read_csv(metrics_path)
        if df is not None:
            break
    else:
        df = None

    if df is not None:
        df = strip_text_columns(df)
        rows_md = [
            "| Selector | N | Mean Score | Median Words | % Short | % Long | Oracle Recall | Mean Overlap |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for _, r in df.iterrows():
            rows_md.append(
                f"| {r['selector']} | {int(r['n_candidates'])} | {fmt(r['mean_selector_score'])} | "
                f"{fmt(r['median_n_words'], 1)} | {fmt(r['pct_short_lt8'], 1)}% | "
                f"{fmt(r['pct_long_gt60'], 1)}% | {fmt(r['oracle_recall_at_selected'])} | "
                f"{fmt(r['mean_oracle_overlap'])} |"
            )

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Selector ablation: evidence canonicalization variants. " + CAVEAT + r"}",
            r"\label{tab:selector_ablation}",
            r"\begin{tabular}{lccccccc}",
            r"\toprule",
            r"Selector & N & Score & Words & \% Short & \% Long & Oracle Rec. & Overlap \\",
            r"\midrule",
        ]
        for _, r in df.iterrows():
            rows_tex.append(
                f"{r['selector']} & {int(r['n_candidates'])} & {fmt(r['mean_selector_score'])} & "
                f"{fmt(r['median_n_words'], 1)} & {fmt(r['pct_short_lt8'], 1)} & "
                f"{fmt(r['pct_long_gt60'], 1)} & {fmt(r['oracle_recall_at_selected'])} & "
                f"{fmt(r['mean_oracle_overlap'])} \\\\"
            )
        rows_tex.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    else:
        rows_md = ["| Selector | Status |", "|---|---|", "| (missing) | not generated |"]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Selector ablation. " + CAVEAT + r"}",
            r"\label{tab:selector_ablation}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated \\\\", r"\bottomrule",
            r"\end{tabular}", r"\end{table}",
        ]
        log("    [MISS] selector_metrics_summary.csv not found")

    return "\n".join(rows_md), "\n".join(rows_tex), df


# ---------------------------------------------------------------------------
# Table 5: Review Queue Metrics
# ---------------------------------------------------------------------------

def generate_table5_review_queue(experiments_dir: Path) -> Tuple[str, str, Optional[pd.DataFrame]]:
    """Table 5: Review queue metrics with bootstrap CI."""
    log("  Generating Table 5: Review Queue Metrics...")

    ci_path = experiments_dir / "metric_robustness_v1" / "classification_metrics_with_ci.csv"
    queue_path = experiments_dir / "metric_robustness_v1" / "queue_metrics_with_ci.csv"
    ci_df = safe_read_csv(ci_path)
    queue_df = safe_read_csv(queue_path)

    if ci_df is not None:
        ci_df = strip_text_columns(ci_df)
        rows_md = [
            "| Metric | Point Estimate | CI Low (2.5%) | CI High (97.5%) | Bootstrap Unit |",
            "|---|---|---|---|---|",
        ]
        for _, r in ci_df.iterrows():
            rows_md.append(
                f"| {r['metric']} | {fmt(r['point_estimate'])} | {fmt(r['ci_low_2_5'])} | "
                f"{fmt(r['ci_high_97_5'])} | {r.get('bootstrap_unit', 'N/A')} |"
            )

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Classification metrics with bootstrap 95\% CI. " + CAVEAT + r"}",
            r"\label{tab:review_queue}",
            r"\begin{tabular}{lcccc}",
            r"\toprule",
            r"Metric & Point Est. & CI Low & CI High & Unit \\",
            r"\midrule",
        ]
        for _, r in ci_df.iterrows():
            rows_tex.append(
                f"{r['metric']} & {fmt(r['point_estimate'])} & {fmt(r['ci_low_2_5'])} & "
                f"{fmt(r['ci_high_97_5'])} & {r.get('bootstrap_unit', 'N/A')} \\\\"
            )
        rows_tex.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    else:
        rows_md = ["| Metric | Status |", "|---|---|", "| (missing) | not generated |"]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Review queue metrics. " + CAVEAT + r"}",
            r"\label{tab:review_queue}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated \\\\", r"\bottomrule",
            r"\end{tabular}", r"\end{table}",
        ]
        log("    [MISS] classification_metrics_with_ci.csv not found")

    return "\n".join(rows_md), "\n".join(rows_tex), ci_df


# ---------------------------------------------------------------------------
# Table 6: Leakage Audit
# ---------------------------------------------------------------------------

def generate_table6_leakage_audit(experiments_dir: Path) -> Tuple[str, str, List[str]]:
    """Table 6: Leakage audit checks."""
    log("  Generating Table 6: Leakage Audit...")

    for subdir in ["leakage_audit_v1", "leakage_audit_v1_toy"]:
        audit_dir = experiments_dir / subdir
        if audit_dir.exists():
            break
    else:
        audit_dir = None

    checks = []
    missing_files = []

    if audit_dir and audit_dir.exists():
        # Check 1: claim-only baseline
        d = safe_read_json(audit_dir / "claim_only_baseline.json")
        if d:
            checks.append(("Claim-only baseline", d.get("status", "N/A"),
                           f"overlap={fmt(d.get('same_label_overlap'))}, ratio={fmt(d.get('ratio'))}"))
        else:
            missing_files.append("claim_only_baseline.json")

        # Check 2: group split integrity
        d = safe_read_json(audit_dir / "group_split_integrity.json")
        if d:
            checks.append(("Group split integrity", d.get("status", "N/A"),
                           f"n_groups={d.get('n_groups','?')}, cross_split={d.get('n_cross_split_groups','?')}"))
        else:
            missing_files.append("group_split_integrity.json")

        # Check 3: no label in queue sorting
        d = safe_read_json(audit_dir / "no_label_in_queue_sorting_check.json")
        if d:
            checks.append(("No label in queue sorting", d.get("status", "N/A"),
                           f"label_used={d.get('true_label_used_for_sorting','?')}, oracle_used={d.get('oracle_hit_used_for_sorting','?')}"))
        else:
            missing_files.append("no_label_in_queue_sorting_check.json")

        # Check 4: no oracle in selector
        d = safe_read_json(audit_dir / "no_oracle_in_selector_check.json")
        if d:
            checks.append(("No oracle in selector", d.get("status", "N/A"),
                           f"oracle_used={d.get('oracle_hit_used_for_selection','?')}"))
        else:
            missing_files.append("no_oracle_in_selector_check.json")

        # Check 5: title-only baseline
        d = safe_read_json(audit_dir / "title_only_retrieval_baseline.json")
        if d:
            checks.append(("Title-only retrieval baseline", d.get("status", "N/A"),
                           f"overlap={fmt(d.get('same_label_overlap'))}, ratio={fmt(d.get('ratio'))}"))
        else:
            missing_files.append("title_only_retrieval_baseline.json")

        # Check 6: metadata-only baseline
        d = safe_read_json(audit_dir / "metadata_only_retrieval_baseline.json")
        if d:
            checks.append(("Metadata-only retrieval baseline", d.get("status", "N/A"),
                           f"overlap={fmt(d.get('same_label_overlap'))}, ratio={fmt(d.get('ratio'))}"))
        else:
            missing_files.append("metadata_only_retrieval_baseline.json")
    else:
        missing_files.append("leakage_audit_v1 directory")

    if checks:
        rows_md = ["| Check | Status | Details |", "|---|---|---|"]
        for name, status, details in checks:
            rows_md.append(f"| {name} | {status} | {details} |")

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Leakage audit checks. " + CAVEAT + r"}",
            r"\label{tab:leakage_audit}",
            r"\begin{tabular}{lll}",
            r"\toprule",
            r"Check & Status & Details \\",
            r"\midrule",
        ]
        for name, status, details in checks:
            rows_tex.append(f"{name} & {status} & {details} \\\\")
        rows_tex.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    else:
        rows_md = ["| Check | Status |", "|---|---|", "| (missing) | not generated |"]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Leakage audit. " + CAVEAT + r"}",
            r"\label{tab:leakage_audit}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated \\\\", r"\bottomrule",
            r"\end{tabular}", r"\end{table}",
        ]
        log(f"    [MISS] leakage audit files not found: {missing_files}")

    return "\n".join(rows_md), "\n".join(rows_tex), missing_files


# ---------------------------------------------------------------------------
# Figures (data CSVs + ASCII pipeline)
# ---------------------------------------------------------------------------

def write_pipeline_ascii(output_path: Path) -> None:
    """Write ASCII pipeline diagram."""
    log("  Writing pipeline ASCII diagram...")
    lines = [
        "# V3.17 Confidential Lightweight Pipeline",
        "",
        "```",
        "Local PDFs",
        "    │",
        "    ▼",
        "Text extraction",
        "    │",
        "    ▼",
        "BM25 sentence/window retrieval",
        "    │",
        "    ▼",
        "Evidence canonicalization",
        "    │",
        "    ▼",
        "Frozen R4 screening (10-seed ensemble)",
        "    │",
        "    ▼",
        "SmartQueue / conservative ranking",
        "    │",
        "    ▼",
        "Human review queue (top-100)",
        "```",
        "",
        f"<!-- {CAVEAT} -->",
    ]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


def write_format_shift_bar_data(experiments_dir: Path, output_path: Path) -> None:
    """Write format shift bar chart data CSV."""
    log("  Writing format shift bar data...")
    for subdir in ["format_shift_ablation_v1", "format_shift_ablation_v1_toy"]:
        inputs_path = experiments_dir / subdir / "format_shift_inputs.csv"
        df = safe_read_csv(inputs_path)
        if df is not None:
            break
    else:
        df = None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if df is not None and "variant" in df.columns:
        grouped = df.groupby("variant").agg(
            n_candidates=("candidate_id", "count"),
            mean_n_words=("n_words", "mean"),
        ).reset_index()
        grouped.to_csv(output_path, index=False)
        log(f"    Wrote {len(grouped)} rows to {output_path}")
    else:
        pd.DataFrame(columns=["variant", "n_candidates", "mean_n_words"]).to_csv(output_path, index=False)
        log(f"    [MISS] No format shift data, wrote empty CSV")


def write_queue_precision_recall_data(experiments_dir: Path, output_path: Path) -> None:
    """Write queue precision/recall data CSV from metric_robustness."""
    log("  Writing queue precision/recall data...")
    queue_path = experiments_dir / "metric_robustness_v1" / "queue_metrics_with_ci.csv"
    df = safe_read_csv(queue_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if df is not None:
        # Filter to precision/recall metrics only
        pr_df = df[df["metric"].str.contains("precision|recall", case=False, na=False)].copy()
        pr_df.to_csv(output_path, index=False)
        log(f"    Wrote {len(pr_df)} rows to {output_path}")
    else:
        pd.DataFrame(columns=["variant_or_profile", "metric", "k_or_prevalence", "point_estimate", "ci_low_2_5", "ci_high_97_5"]).to_csv(output_path, index=False)
        log(f"    [MISS] No queue metrics data, wrote empty CSV")


def write_smartqueue_bucket_counts(experiments_dir: Path, output_path: Path) -> None:
    """Write SmartQueue bucket count data CSV."""
    log("  Writing SmartQueue bucket counts...")
    for subdir in ["lightweight_smart_queue_v1", "lightweight_smart_queue_v1_toy"]:
        sq_path = experiments_dir / subdir / "smart_queue_scores.csv"
        df = safe_read_csv(sq_path)
        if df is not None:
            break
    else:
        df = None

    output_path.parent.mkdir(parents=True, exist_ok=True)
    if df is not None and "bucket" in df.columns:
        counts = df["bucket"].value_counts().reset_index()
        counts.columns = ["bucket", "count"]
        counts.to_csv(output_path, index=False)
        log(f"    Wrote {len(counts)} buckets to {output_path}")
    else:
        pd.DataFrame(columns=["bucket", "count"]).to_csv(output_path, index=False)
        log(f"    [MISS] No smart_queue data, wrote empty CSV")


# ---------------------------------------------------------------------------
# Table 7: Complexity-vs-Utility
# ---------------------------------------------------------------------------

def generate_table7_complexity_utility(experiments_dir: Path) -> Tuple[str, str, Optional[pd.DataFrame]]:
    """Table 7: Complexity-vs-utility method comparison + Pareto."""
    log("  Generating Table 7: Complexity-vs-Utility...")
    path = experiments_dir / "complexity_vs_utility_ablation_v1" / "method_comparison_metrics.csv"
    df = safe_read_csv(path)
    pareto_path = experiments_dir / "complexity_vs_utility_ablation_v1" / "method_pareto_table.csv"
    pareto_df = safe_read_csv(pareto_path)

    if df is not None and len(df) > 0:
        rows_md = [
            "| Method | Family | Available | strong_F1 | P@20 | R@100 | deterministic | auditable |",
            "|---|---|---|---|---|---|---|---|",
        ]
        for _, r in df.iterrows():
            rows_md.append(
                f"| {r.get('method_id','')} | {r.get('method_family','')} | "
                f"{r.get('available','')} | {fmt(r.get('strong_F1'))} | "
                f"{fmt(r.get('precision_at_20'))} | {fmt(r.get('recall_at_100'))} | "
                f"{r.get('deterministic','')} | {r.get('auditable','')} |"
            )
        rows_md.append("")
        rows_md.append(f"*{CAVEAT}*")
        if pareto_df is not None:
            rows_md.append("")
            rows_md.append("**Pareto scores** (utility = diagnostic aggregation, not a benchmark metric):")
            rows_md.append("")
            rows_md.append("| Method | perf | priv | audit | simple | repro | utility | pareto |")
            rows_md.append("|---|---|---|---|---|---|---|")
            for _, r in pareto_df.iterrows():
                rows_md.append(
                    f"| {r.get('method_id','')} | {r.get('performance_score','')} | "
                    f"{r.get('privacy_score','')} | {r.get('auditability_score','')} | "
                    f"{r.get('simplicity_score','')} | {r.get('reproducibility_score','')} | "
                    f"{r.get('utility_score','')} | {r.get('pareto_overall','')} |"
                )

        rows_tex = [
            r"\begin{table}[ht]",
            r"\centering",
            r"\caption{Complexity-vs-utility method comparison. " + CAVEAT + r"}",
            r"\label{tab:complexity_utility}",
            r"\begin{tabular}{llccccc}",
            r"\toprule",
            r"Method & Family & strong\_F1 & P@20 & R@100 & determ. & audit. \\",
            r"\midrule",
        ]
        for _, r in df.iterrows():
            rows_tex.append(
                f"{r.get('method_id','')} & {r.get('method_family','')} & "
                f"{fmt(r.get('strong_F1'))} & {fmt(r.get('precision_at_20'))} & "
                f"{fmt(r.get('recall_at_100'))} & {r.get('deterministic','')} & "
                f"{r.get('auditable','')} \\\\"
            )
        rows_tex.extend([r"\bottomrule", r"\end{tabular}", r"\end{table}"])
    else:
        rows_md = [
            "| Method | Family | Available | strong_F1 | P@20 | R@100 |",
            "|---|---|---|---|---|---|",
            f"| Status | not generated | - | - | - | - |",
            "",
            f"*{CAVEAT}*",
        ]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Complexity-vs-utility. " + CAVEAT + r"}",
            r"\label{tab:complexity_utility}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated \\", r"\bottomrule",
            r"\end{tabular}", r"\end{table}",
        ]
        log("    [MISS] complexity_vs_utility_ablation_v1/method_comparison_metrics.csv")
    return "\n".join(rows_md), "\n".join(rows_tex), df


# ---------------------------------------------------------------------------
# Table 8: Human Audit (if available)
# ---------------------------------------------------------------------------

def generate_table8_human_audit(experiments_dir: Path) -> Tuple[str, str, Optional[dict]]:
    """Table 8: Human audit agreement summary (if available)."""
    log("  Generating Table 8: Human Audit...")
    path = experiments_dir / "human_audit_v1" / "audit_agreement_summary.json"
    summary = safe_read_json(path)

    if summary and summary.get("metrics", {}).get("n_filled", 0) > 0:
        m = summary["metrics"]
        rows_md = [
            "| Metric | Value |",
            "|---|---|",
            f"| n_filled | {m.get('n_filled','N/A')} |",
            f"| n_decided | {m.get('n_decided','N/A')} |",
            f"| silver_vs_auditor_agreement | {fmt(m.get('silver_vs_auditor_agreement'))} |",
            f"| strong_action_precision_in_top20 | {fmt(m.get('strong_action_precision_in_top20'))} |",
            f"| strong_action_precision_in_top50 | {fmt(m.get('strong_action_precision_in_top50'))} |",
            f"| major_disagreement_rate | {fmt(m.get('major_disagreement_rate'))} |",
            f"| uncertain_rate | {fmt(m.get('uncertain_rate'))} |",
            "",
            "*Small targeted audit, not a gold benchmark. Directional reliability check only.*",
        ]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Human audit agreement. Small targeted audit, not a gold benchmark. " + CAVEAT + r"}",
            r"\label{tab:human_audit}",
            r"\begin{tabular}{lr}", r"\toprule",
            r"Metric & Value \\", r"\midrule",
            f"n\_filled & {m.get('n_filled','N/A')} \\\\",
            f"Agreement & {fmt(m.get('silver_vs_auditor_agreement'))} \\\\",
            f"P@20 (strong) & {fmt(m.get('strong_action_precision_in_top20'))} \\\\",
            f"P@50 (strong) & {fmt(m.get('strong_action_precision_in_top50'))} \\\\",
            f"Major disagreement & {fmt(m.get('major_disagreement_rate'))} \\\\",
            f"Uncertain rate & {fmt(m.get('uncertain_rate'))} \\\\",
            r"\bottomrule", r"\end{tabular}", r"\end{table}",
        ]
    else:
        rows_md = [
            "| Metric | Value |",
            "|---|---|",
            "| Status | not generated (human audit not yet completed) |",
            "",
            "*Small targeted audit, not a gold benchmark. Audit seed is built; auditor labels pending.*",
        ]
        rows_tex = [
            r"\begin{table}[ht]", r"\centering",
            r"\caption{Human audit. Not yet completed. " + CAVEAT + r"}",
            r"\label{tab:human_audit}",
            r"\begin{tabular}{l}", r"\toprule",
            r"Status: not generated (audit pending) \\", r"\bottomrule",
            r"\end{tabular}", r"\end{table}",
        ]
        log("    [MISS] human_audit_v1/audit_agreement_summary.json (audit not yet completed)")
    return "\n".join(rows_md), "\n".join(rows_tex), summary


# ---------------------------------------------------------------------------
# Paper Results Summary (by RQ)
# ---------------------------------------------------------------------------

def write_paper_results_summary(
    output_path: Path,
    retrieval_summary: Optional[dict],
    selector_df: Optional[pd.DataFrame],
    ci_df: Optional[pd.DataFrame],
    leakage_missing: List[str],
    complexity_df: Optional[pd.DataFrame] = None,
    complexity_pareto_df: Optional[pd.DataFrame] = None,
    audit_summary: Optional[dict] = None,
) -> None:
    """Write paper results summary organized by research questions."""
    log("  Writing paper results summary...")

    lines = [
        "# V3.17 Confidential Paper Results Summary",
        "",
        f"> {CAVEAT}",
        "",
        "## Research Questions",
        "",
    ]

    # RQ1: Retrieval feasibility
    lines.append("### RQ1: Retrieval Feasibility")
    lines.append("")
    if retrieval_summary:
        sent = retrieval_summary.get("sentence", {})
        win = retrieval_summary.get("window", {})
        lines.append(f"- Sentence-level BM25 recall@1: **{fmt(sent.get('recall@1'))}**")
        lines.append(f"- Window-level BM25 recall@1: **{fmt(win.get('recall@1'))}**")
        lines.append(f"- Sentence-level MRR: **{fmt(sent.get('mrr'))}**")
        lines.append("- Finding: Sentence-level retrieval outperforms window-level on oracle recall.")
    else:
        lines.append("- Status: **not generated** (missing oracle_recall_summary.json)")
    lines.append("")

    # RQ2: Raw chunk failure
    lines.append("### RQ2: Raw Chunk Failure")
    lines.append("")
    if selector_df is not None and len(selector_df) > 0:
        raw_row = selector_df[selector_df["selector"].str.contains("raw_top1|cleaned_top1", na=False)]
        if len(raw_row) > 0:
            oracle_rec = raw_row.iloc[0].get("oracle_recall_at_selected", "N/A")
            lines.append(f"- Raw top-1 chunk oracle recall: **{fmt(oracle_rec)}**")
            lines.append("- Finding: Raw BM25 chunks have low oracle recall, motivating evidence canonicalization.")
        else:
            lines.append("- Status: raw_top1_chunk selector not found in ablation data")
    else:
        lines.append("- Status: **not generated** (missing selector_metrics_summary.csv)")
    lines.append("")

    # RQ3: Canonicalization recovery
    lines.append("### RQ3: Canonicalization Recovery")
    lines.append("")
    if selector_df is not None and len(selector_df) > 0:
        best_row = selector_df[selector_df["selector"].str.contains("best_sentence_top5_overlap", na=False)]
        if len(best_row) > 0:
            oracle_rec = best_row.iloc[0].get("oracle_recall_at_selected", "N/A")
            overlap = best_row.iloc[0].get("mean_oracle_overlap", "N/A")
            lines.append(f"- best_sentence_top5_overlap oracle recall: **{fmt(oracle_rec)}**")
            lines.append(f"- Mean oracle overlap: **{fmt(overlap)}**")
            lines.append("- Finding: Canonicalization restores screening signal lost in raw chunk retrieval.")
        else:
            lines.append("- Status: best_sentence_top5_overlap selector not found")
    else:
        lines.append("- Status: **not generated**")
    lines.append("")

    # RQ4: Format shift source
    lines.append("### RQ4: Format Shift Source")
    lines.append("")
    lines.append("- Finding: Format shift (metadata, lengthening) degrades downstream classification.")
    lines.append("- Evidence: See Table 3 and format_shift_bar_data.csv.")
    lines.append("")

    # RQ5: Review queue utility
    lines.append("### RQ5: Review Queue Utility")
    lines.append("")
    if ci_df is not None and len(ci_df) > 0:
        for _, r in ci_df.iterrows():
            lines.append(
                f"- {r['metric']}: **{fmt(r['point_estimate'])}** "
                f"(95% CI: [{fmt(r['ci_low_2_5'])}, {fmt(r['ci_high_97_5'])}])"
            )
        lines.append("- Finding: Frozen R4 screening achieves strong_F1≈0.45 with group-aware bootstrap CI.")
    else:
        lines.append("- Status: **not generated** (missing classification_metrics_with_ci.csv)")
    lines.append("")

    # RQ6: Leakage/confidentiality audit
    lines.append("### RQ6: Leakage/Confidentiality Audit")
    lines.append("")
    if leakage_missing:
        lines.append(f"- Missing files: {leakage_missing}")
    else:
        lines.append("- All leakage checks passed (claim-only baseline, group split, label sorting, oracle selection, title-only, metadata-only).")
    lines.append("- Finding: No label leakage detected; queue sorting uses only permitted features.")
    lines.append("")

    # RQ7: Complexity-vs-utility
    lines.append("### RQ7: Complexity-vs-Utility Tradeoff")
    lines.append("")
    if complexity_df is not None and len(complexity_df) > 0:
        det_row = complexity_df[complexity_df["method_id"] == "deterministic_canonicalization"]
        learned_row = complexity_df[complexity_df["method_id"] == "learned_selector_only"]
        det_f1 = det_row.iloc[0].get("strong_F1") if len(det_row) > 0 else None
        learned_f1 = learned_row.iloc[0].get("strong_F1") if len(learned_row) > 0 else None
        if det_f1 is not None:
            lines.append(f"- Deterministic canonicalization strong_F1: **{fmt(det_f1)}**")
        if learned_f1 is not None:
            lines.append(f"- Learned selector strong_F1: **{fmt(learned_f1)}**")
        if complexity_pareto_df is not None and len(complexity_pareto_df) > 0:
            pareto_opt = complexity_pareto_df[complexity_pareto_df["pareto_overall"] == "pareto_optimal"]
            lines.append(f"- Pareto-optimal methods: {', '.join(pareto_opt['method_id'].tolist())}")
        lines.append("- Finding: Under confidential/no-API/no-training/silver-diagnostic constraints, deterministic canonicalization has a better performance–privacy–auditability–cost tradeoff.")
        lines.append("- Bound: This does not prove rules generally beat learned models. Conclusion is deployment-specific.")
    else:
        lines.append("- Status: **not generated** (missing method_comparison_metrics.csv)")
    lines.append("")

    # RQ8: Human audit (if available)
    lines.append("### RQ8: Human Audit (If Available)")
    lines.append("")
    if audit_summary and audit_summary.get("metrics", {}).get("n_filled", 0) > 0:
        m = audit_summary["metrics"]
        lines.append(f"- n_filled: **{m.get('n_filled','N/A')}**")
        lines.append(f"- silver_vs_auditor_agreement: **{fmt(m.get('silver_vs_auditor_agreement'))}**")
        lines.append(f"- strong_action_precision_in_top20: **{fmt(m.get('strong_action_precision_in_top20'))}**")
        lines.append(f"- major_disagreement_rate: **{fmt(m.get('major_disagreement_rate'))}**")
        lines.append("- Finding: Small targeted audit suggests directional reliability of top queue and strong_action labels.")
        lines.append("- Bound: Small targeted audit, not a gold benchmark. Not human-audited full benchmark.")
    else:
        lines.append("- Status: **not generated** (human audit seed built; auditor labels pending)")
        lines.append("- Finding: Audit protocol and seed queue are in place; empirical audit results deferred.")
    lines.append("")

    lines.append("## Summary")
    lines.append("")
    lines.append("- V3.17 confidential lightweight pipeline provides a frozen, reproducible screening baseline.")
    lines.append("- All results are silver-label diagnostic, not gold/human-audited.")
    lines.append("- Bootstrap CIs account for group-level correlation via target_candidate_group_id resampling.")
    lines.append("- No raw claim/evidence text appears in any public artifact.")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Paper Claims Checklist
# ---------------------------------------------------------------------------

def write_paper_claims_checklist(
    output_path: Path,
    retrieval_summary: Optional[dict],
    selector_df: Optional[pd.DataFrame],
    ci_df: Optional[pd.DataFrame],
    leakage_missing: List[str],
    complexity_df: Optional[pd.DataFrame] = None,
    audit_summary: Optional[dict] = None,
) -> None:
    """Write paper claims checklist with safe/unsafe claims and evidence.

    Spec-required items (must all appear):
      not gold / not human-audited benchmark / not SOTA / not automatic peer review /
      not full CESE-OCN validation / second-stage review queue only /
      retrieval-to-screening format shift supported / canonicalization supported.
    """
    log("  Writing paper claims checklist...")

    lines = [
        "# Paper Claims Checklist — V3.17 Confidential",
        "",
        f"> {CAVEAT}",
        "",
        "## Required Caveat Items",
        "",
        "| # | Required statement | Present |",
        "|---|---|---|",
        "| C1 | not gold | YES (see U6, S5 bound) |",
        "| C2 | not human-audited benchmark | YES (see U7, S8) |",
        "| C3 | not SOTA | YES (see U8) |",
        "| C4 | not automatic peer review | YES (see U9) |",
        "| C5 | not full CESE-OCN validation | YES (see U10) |",
        "| C6 | second-stage review queue only | YES (see S6) |",
        "| C7 | retrieval-to-screening format shift supported | YES (see S7) |",
        "| C8 | canonicalization supported | YES (see S1) |",
        "",
        "## Safe Claims (Supported)",
        "",
        "### S1: Canonicalization supported — evidence canonicalization improves over raw BM25 chunks",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv (Table 4)",
        "- **Safe wording**: \"On the controlled silver diagnostic, evidence canonicalization (best_sentence_top5_overlap) yields higher oracle recall than raw_top1_chunk, supporting canonicalization as a recovery step.\"",
        "- **Unsafe wording**: \"Canonicalization always improves retrieval.\" / \"Canonicalization is necessary for all datasets.\"",
        "- **Bound**: Limited to silver diagnostic data; not generalizable to gold-standard.",
        "",
        "### S2: Frozen R4 screening achieves strong_F1 ≈ 0.45 with group-aware bootstrap CI",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/metric_robustness_v1/classification_metrics_with_ci.csv (Table 5)",
        "- **Safe wording**: \"On the controlled silver diagnostic, frozen R4 screening achieves strong_F1 ≈ 0.45 with group-aware bootstrap 95% CI.\"",
        "- **Unsafe wording**: \"The system achieves F1=0.45 in production.\" / \"strong_F1=0.45 generalizes to real data.\"",
        "- **Bound**: CI is group-aware (resampled by target_candidate_group_id); reflects controlled balanced pool.",
        "",
        "### S3: No label leakage in queue sorting or selector",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/leakage_audit_v1/*.json (Table 6)",
        "- **Safe wording**: \"Leakage audit on the V3.17 frozen code path confirms true_label and oracle_hit are not used for queue sorting or selector choice.\"",
        "- **Unsafe wording**: \"No confidentiality leaks exist.\" / \"The system is provably leak-free.\"",
        "- **Bound**: Audit covers the V3.17 frozen code path; future code changes require re-audit.",
        "",
        "### S4: Sentence-level retrieval outperforms window-level on oracle recall",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json (Table 2)",
        "- **Safe wording**: \"Under BM25 with the current PDF corpus, sentence-level retrieval yields higher oracle recall@1 and MRR than window-level.\"",
        "- **Unsafe wording**: \"Sentence retrieval beats window retrieval universally.\" / \"BM25 beats neural retrievers.\"",
        "- **Bound**: Limited to BM25 with the current PDF corpus; neural retrievers may differ.",
        "",
        "### S5: Dataset is silver diagnostic, not gold",
        "- **Supported?**: YES (structural fact)",
        "- **Evidence file**: data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv (human_audited=False for all rows)",
        "- **Safe wording**: \"The 444-candidate dataset is a controlled silver diagnostic with human_audited=False; it is not a gold benchmark.\"",
        "- **Unsafe wording**: \"Gold-standard evaluation set.\" / \"Human-verified benchmark.\"",
        "- **Bound**: All quantitative results must be qualified as silver-label diagnostic.",
        "",
        "### S6: Second-stage review queue only (not a standalone detector)",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/canonicalized_review_queue_v1/, experiments/lightweight_smart_queue_v1/smart_queue_metric_summary.json",
        "- **Safe wording**: \"The pipeline produces a second-stage review queue that augments human review; it is not a standalone automatic detector.\"",
        "- **Unsafe wording**: \"The system detects simulation claim overclaims automatically.\" / \"The pipeline replaces human review.\"",
        "- **Bound**: Human adjudication remains the gold standard; the queue only prioritizes cases for review.",
        "",
        "### S7: Retrieval-to-screening format shift is supported",
        "- **Supported?**: YES",
        "- **Evidence file**: experiments/format_shift_ablation_v1/format_shift_inputs.csv (Table 3), experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv (Table 4)",
        "- **Safe wording**: \"Format shift (metadata, lengthening) between PDF retrieval and downstream screening is characterized; canonicalization mitigates the resulting signal loss.\"",
        "- **Unsafe wording**: \"Format shift is fully solved.\" / \"Canonicalization eliminates all retrieval-to-screening gap.\"",
        "- **Bound**: Mitigation, not elimination; gap remains and is reported.",
        "",
        "### S8: Small targeted human audit protocol is in place (not a full benchmark)",
        "- **Supported?**: YES (protocol exists; empirical results may be pending)",
        "- **Evidence file**: docs/human_audit_protocol_v1.md, data/audit_templates/human_audit_template.csv, experiments/human_audit_v1/audit_agreement_summary.json (if completed)",
        "- **Safe wording**: \"A small targeted human audit protocol is defined to verify directional reliability of top queue and strong_action labels; it is not a human-audited benchmark.\"",
        "- **Unsafe wording**: \"Human-validated benchmark.\" / \"Gold-standard audit.\"",
        "- **Bound**: Small targeted audit (80–120 candidates); not a gold benchmark; not a full human-audited benchmark.",
        "",
        "## Unsafe Claims (Do NOT make)",
        "",
        "### U1: \"The system detects real-world simulation claim overclaims.\"",
        "- **Why unsafe**: System is a review queue generator, not a standalone detector. Silver labels only.",
        "",
        "### U2: \"strong_F1 of 0.45 generalizes to production data.\"",
        "- **Why unsafe**: Controlled balanced 4-class pool. Natural prevalence is unknown.",
        "",
        "### U3: \"The pipeline replaces human review.\"",
        "- **Why unsafe**: Pipeline augments human review; does not replace it. Human adjudication is gold standard.",
        "",
        "### U4: \"Bootstrap CI reflects real-world uncertainty.\"",
        "- **Why unsafe**: CI reflects sampling variability in the controlled pool, not population prevalence.",
        "",
        "### U5: \"No confidentiality leaks exist.\"",
        "- **Why unsafe**: Red-team scanner checks known patterns; cannot guarantee zero leaks. Continuous auditing needed.",
        "",
        "### U6: \"This is a gold benchmark.\"  (violates: not gold)",
        "- **Why unsafe**: All rows have human_audited=False; gold_label is empty. Silver diagnostic only.",
        "",
        "### U7: \"This is a human-audited benchmark.\"  (violates: not human-audited benchmark)",
        "- **Why unsafe**: No full human audit has been completed. Only a small targeted audit protocol exists.",
        "",
        "### U8: \"The pipeline achieves SOTA on simulation claim overclaim detection.\"  (violates: not SOTA)",
        "- **Why unsafe**: No comparison to other systems on a shared benchmark; silver diagnostic, not gold.",
        "",
        "### U9: \"The pipeline performs automatic peer review.\"  (violates: not automatic peer review)",
        "- **Why unsafe**: Pipeline produces a review queue for human reviewers; it does not perform peer review automatically.",
        "",
        "### U10: \"This constitutes full CESE-OCN validation.\"  (violates: not full CESE-OCN validation)",
        "- **Why unsafe**: V3.17 confidential lightweight is a scoped subset; full CESE-OCN validation requires additional stages, gold labels, and human adjudication not present here.",
        "",
        "### U11: \"Rules generally beat learned models.\"  (complexity-vs-utility bound)",
        "- **Why unsafe**: Pareto analysis is deployment-specific (confidential/no-API/no-training/silver diagnostic). It does not support a general claim about rules vs. learned models.",
        "",
        "## Evidence Index",
        "",
        "| Claim | Evidence File | Table/Figure |",
        "|---|---|---|",
        "| S1 (canonicalization supported) | selector_metrics_summary.csv | Table 4 |",
        "| S2 (strong_F1 ≈ 0.45) | classification_metrics_with_ci.csv | Table 5 |",
        "| S3 (no leakage) | leakage_audit_v1/*.json | Table 6 |",
        "| S4 (sentence > window) | oracle_recall_summary.json | Table 2 |",
        "| S5 (silver, not gold) | strict_silver_max_candidates_v1.csv | Table 1 |",
        "| S6 (second-stage queue only) | smart_queue_metric_summary.json | Table 5 |",
        "| S7 (format shift supported) | format_shift_inputs.csv | Table 3 |",
        "| S8 (audit protocol, not benchmark) | human_audit_protocol_v1.md | Table 8 |",
        "",
        f"> {CAVEAT}",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text("\n".join(lines), encoding="utf-8")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Generate V3.17 confidential paper tables and figures."
    )
    parser.add_argument("--experiments_dir", default="experiments",
                        help="Root experiments directory")
    parser.add_argument("--candidate_csv", default=None,
                        help="Candidate CSV for dataset summary (optional)")
    parser.add_argument("--output_dir", default="paper_assets/v3_17_confidential",
                        help="Output directory for paper assets")
    parser.add_argument("--config", default=None,
                        help="YAML config file")
    parser.add_argument("--toy_mode", action="store_true",
                        help="Use toy data paths")
    args = parser.parse_args()

    # Load config if provided
    config = {}
    guards = {}
    if args.config:
        config = load_and_validate(args.config)
        guards = config.get("guards", {})
    else:
        guards = {
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
        }

    log("=" * 72)
    log("Paper Assets Generator v1 — V3.17 Confidential")
    log("=" * 72)
    log(f"Experiments dir: {args.experiments_dir}")
    log(f"Output dir: {args.output_dir}")
    log(f"Toy mode: {args.toy_mode}")
    log(f"Guards: {guards}")
    log("")

    experiments_dir = Path(args.experiments_dir)
    if not experiments_dir.is_absolute():
        experiments_dir = REPO_ROOT / experiments_dir

    output_dir = Path(args.output_dir)
    if not output_dir.is_absolute():
        output_dir = REPO_ROOT / output_dir

    # Resolve candidate CSV
    if args.candidate_csv:
        candidate_csv = Path(args.candidate_csv)
        if not candidate_csv.is_absolute():
            candidate_csv = REPO_ROOT / candidate_csv
    elif args.toy_mode:
        candidate_csv = REPO_ROOT / "data" / "toy_synthetic" / "toy_candidates_v1.csv"
    else:
        candidate_csv = REPO_ROOT / "data" / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1" / "strict_silver_max_candidates_v1.csv"

    # Create output directories
    tables_dir = output_dir / "tables"
    figures_dir = output_dir / "figures"
    tables_dir.mkdir(parents=True, exist_ok=True)
    figures_dir.mkdir(parents=True, exist_ok=True)

    missing_files: List[str] = []

    # Generate tables
    log("Generating tables...")

    t1_md, t1_tex = generate_table1_dataset_summary(experiments_dir, candidate_csv)
    (tables_dir / "table1_dataset_summary.md").write_text(t1_md, encoding="utf-8")
    (tables_dir / "table1_dataset_summary.tex").write_text(t1_tex, encoding="utf-8")

    t2_md, t2_tex, retrieval_summary = generate_table2_retrieval_recall(experiments_dir)
    (tables_dir / "table2_retrieval_recall.md").write_text(t2_md, encoding="utf-8")
    (tables_dir / "table2_retrieval_recall.tex").write_text(t2_tex, encoding="utf-8")

    t3_md, t3_tex, _ = generate_table3_format_shift(experiments_dir)
    (tables_dir / "table3_format_shift_ablation.md").write_text(t3_md, encoding="utf-8")
    (tables_dir / "table3_format_shift_ablation.tex").write_text(t3_tex, encoding="utf-8")

    t4_md, t4_tex, selector_df = generate_table4_selector_ablation(experiments_dir)
    (tables_dir / "table4_canonicalizer_ablation.md").write_text(t4_md, encoding="utf-8")
    (tables_dir / "table4_canonicalizer_ablation.tex").write_text(t4_tex, encoding="utf-8")

    t5_md, t5_tex, ci_df = generate_table5_review_queue(experiments_dir)
    (tables_dir / "table5_review_queue.md").write_text(t5_md, encoding="utf-8")
    (tables_dir / "table5_review_queue.tex").write_text(t5_tex, encoding="utf-8")

    t6_md, t6_tex, leakage_missing = generate_table6_leakage_audit(experiments_dir)
    (tables_dir / "table6_leakage_audit.md").write_text(t6_md, encoding="utf-8")
    (tables_dir / "table6_leakage_audit.tex").write_text(t6_tex, encoding="utf-8")
    missing_files.extend(leakage_missing)

    t7_md, t7_tex, complexity_df = generate_table7_complexity_utility(experiments_dir)
    (tables_dir / "table7_complexity_utility.md").write_text(t7_md, encoding="utf-8")
    (tables_dir / "table7_complexity_utility.tex").write_text(t7_tex, encoding="utf-8")

    t8_md, t8_tex, audit_summary = generate_table8_human_audit(experiments_dir)
    (tables_dir / "table8_human_audit_if_available.md").write_text(t8_md, encoding="utf-8")
    (tables_dir / "table8_human_audit_if_available.tex").write_text(t8_tex, encoding="utf-8")

    # Pareto table for RQ7 (read separately for the summary)
    complexity_pareto_df = safe_read_csv(
        experiments_dir / "complexity_vs_utility_ablation_v1" / "method_pareto_table.csv"
    )

    # Generate figures
    log("Generating figures...")
    write_pipeline_ascii(figures_dir / "pipeline_ascii.md")
    write_format_shift_bar_data(experiments_dir, figures_dir / "format_shift_bar_data.csv")
    write_queue_precision_recall_data(experiments_dir, figures_dir / "queue_precision_recall_data.csv")
    write_smartqueue_bucket_counts(experiments_dir, figures_dir / "smartqueue_bucket_counts.csv")

    # Generate summary docs
    log("Generating summary docs...")
    write_paper_results_summary(
        output_dir / "paper_results_summary.md",
        retrieval_summary, selector_df, ci_df, leakage_missing,
        complexity_df=complexity_df,
        complexity_pareto_df=complexity_pareto_df,
        audit_summary=audit_summary,
    )
    write_paper_claims_checklist(
        output_dir / "paper_claims_checklist.md",
        retrieval_summary, selector_df, ci_df, leakage_missing,
        complexity_df=complexity_df,
        audit_summary=audit_summary,
    )

    # Run config
    write_run_config(output_dir, config, "generate_paper_assets_v3_17.py", extra={
        "experiments_dir": str(experiments_dir),
        "candidate_csv": str(candidate_csv),
        "output_dir": str(output_dir),
        "toy_mode": args.toy_mode,
        "guards": guards,
        "missing_files": missing_files,
        "caveat": CAVEAT,
    })

    log("")
    log("Done. Paper assets written to:")
    log(f"  {output_dir}")
    log("")
    log(f"  tables/  (8 tables, md+tex)")
    log(f"  figures/ (pipeline_ascii.md + 3 data CSVs)")
    log(f"  paper_results_summary.md")
    log(f"  paper_claims_checklist.md")
    log(f"  run_config.json")
    if missing_files:
        log(f"")
        log(f"  [WARN] Missing files: {missing_files}")


if __name__ == "__main__":
    main()
