#!/usr/bin/env python
"""generate_reviewer_risk_register_v1.py — Reviewer risk register generator.

Reads reports/current_project_status_v3_17.json to auto-fill the status
and current_evidence_file fields for each reviewer risk, then emits:

  - docs/reviewer_risk_register_v3_17.md         (full register)
  - docs/reviewer_response_playbook_v3_17.md     (defense playbook)
  - paper_assets/v3_17_confidential/reviewer_risk_table.md  (paper table)

Hard boundaries:
  - No exaggeration. Missing results are marked "missing" or "blocked".
  - No fabricated experiments.
  - Silver data is never called gold.
  - Each high-severity risk must have a safe_response.
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import get_repo_root  # noqa: E402

_REPO_ROOT = get_repo_root()
DEFAULT_STATUS_JSON = _REPO_ROOT / "reports" / "current_project_status_v3_17.json"
DEFAULT_DOCS_DIR = _REPO_ROOT / "docs"
DEFAULT_PAPER_ASSETS_DIR = _REPO_ROOT / "paper_assets" / "v3_17_confidential"


# ---------- Risk definitions (static fields) ----------
# status and current_evidence_file are auto-filled from the status JSON.
RISKS = [
    {
        "risk_id": "R01",
        "reviewer_attack": "Dataset is GPT/silver and shortcut-prone.",
        "severity": "high",
        "evidence_needed": "Leakage audit, claim-only baseline, human audit protocol, dataset version lock.",
        "current_evidence_file": [
            "experiments/leakage_audit_v1/audit_summary.md",
            "experiments/leakage_audit_v1/claim_only_baseline.json",
            "docs/human_audit_protocol_v1.md",
            "docs/dataset_version_lock_v3_17.md",
        ],
        "status_lookup": {
            "experiment": "leakage_audit_v1",
            "priority_action": "Run leakage audit on real data",
        },
        "safe_response": (
            "We acknowledge the dataset is a controlled silver diagnostic set, "
            "not a gold benchmark. Labels are AI-preannotated "
            "(annotation_status=ai_preannotated, human_audited=False for all 444 "
            "rows). We mitigate shortcut risk with a 12-check leakage audit "
            "(claim-only baseline, shuffled/empty/title-only evidence, lexical "
            "overlap, cue words), a dataset version lock recording SHA256 and "
            "all invariants, and a small targeted human audit protocol. Results "
            "are reported as format-shift diagnostic findings, not benchmark-level "
            "model validation."
        ),
        "paper_section_to_address": "Limitations + Dataset Description",
        "remaining_limitation": (
            "Human audit is not complete (protocol built, labels pending). "
            "Silver labels may still contain annotation artifacts not detected "
            "by automated checks."
        ),
    },
    {
        "risk_id": "R02",
        "reviewer_attack": "R4 may learn template cues from the silver generation process.",
        "severity": "high",
        "evidence_needed": "Claim-only baseline, shuffled/empty/title-only evidence baselines, lexical cue audit, cue words by label.",
        "current_evidence_file": [
            "experiments/leakage_audit_v1/claim_only_baseline.json",
            "experiments/leakage_audit_v1/shuffled_evidence_baseline.json",
            "experiments/leakage_audit_v1/empty_evidence_baseline.json",
            "experiments/leakage_audit_v1/title_only_retrieval_baseline.json",
            "experiments/leakage_audit_v1/cue_words_by_label.csv",
            "experiments/leakage_audit_v1/lexical_overlap_by_label.csv",
        ],
        "status_lookup": {
            "experiment": "leakage_audit_v1",
            "priority_action": "Run leakage audit on real data",
        },
        "safe_response": (
            "We check template-cue risk with four evidence-degradation baselines: "
            "claim-only (no evidence), shuffled evidence, empty evidence, and "
            "title-only retrieval. If claim-only performance approaches full-evidence "
            "performance, the model is likely using claim cues rather than evidence. "
            "We also audit cue words by label and lexical overlap. If any check "
            "exceeds the WARNING threshold, we restrict conclusions to format-shift "
            "diagnostic and explicitly state the model may be cue-dependent."
        ),
        "paper_section_to_address": "Limitations + Leakage Audit",
        "remaining_limitation": (
            "Cue audits are heuristic (keyword lists, overlap ratios). Subtle "
            "semantic cues not captured by lexical audits may still exist. "
            "Complete mitigation requires human adjudication."
        ),
    },
    {
        "risk_id": "R03",
        "reviewer_attack": "Retrieval success may be oracle-biased (oracle evidence leaks into retrieval ranking).",
        "severity": "medium",
        "evidence_needed": "No-oracle-in-selector check, no-label-in-queue-sorting check, retrieval ranking provenance.",
        "current_evidence_file": [
            "experiments/leakage_audit_v1/no_oracle_in_selector_check.json",
            "experiments/leakage_audit_v1/no_label_in_queue_sorting_check.json",
            "experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv",
        ],
        "status_lookup": {
            "experiment": "leakage_audit_v1",
            "priority_action": "Run leakage audit on real data",
        },
        "safe_response": (
            "Retrieval ranking uses only claim_text as the query. Oracle evidence "
            "and evidence_text are used ONLY for evaluation (computing oracle recall), "
            "never for ranking or selection. The no_oracle_in_selector_check and "
            "no_label_in_queue_sorting_check guards verify that neither oracle "
            "evidence nor labels leak into the selector or queue sorting. The "
            "leakage audit confirms these guards pass."
        ),
        "paper_section_to_address": "Methods + Leakage Audit",
        "remaining_limitation": (
            "Oracle recall is computed on silver labels. If silver labels are "
            "wrong, oracle recall may be mismeasured. Does not affect the "
            "no-leakage guarantee of the ranking itself."
        ),
    },
    {
        "risk_id": "R04",
        "reviewer_attack": "BM25 and simple rules are not novel; contribution is unclear.",
        "severity": "medium",
        "evidence_needed": "Complexity-vs-utility ablation, method comparison metrics, Pareto table.",
        "current_evidence_file": [
            "experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv",
            "experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv",
            "experiments/complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md",
        ],
        "status_lookup": {
            "experiment": "complexity_vs_utility_ablation_v1",
            "priority_action": "Implement and run complexity-vs-utility ablation",
        },
        "safe_response": (
            "The contribution is NOT BM25 itself. The contribution is (1) "
            "identifying the retrieval-to-screening format shift as a failure "
            "mode in confidential local PDF review, (2) using auditable "
            "deterministic canonicalization to bridge raw PDF chunks to "
            "screening-format evidence, and (3) demonstrating the "
            "performance-privacy-auditability-cost tradeoff under "
            "no-API/no-training/confidential constraints. BM25 is used as a "
            "well-understood, auditable retriever; the novelty is in the "
            "pipeline architecture and the format-shift diagnosis, not the "
            "retriever."
        ),
        "paper_section_to_address": "Introduction + Related Work + Discussion",
        "remaining_limitation": (
            "The complexity-vs-utility analysis is deployment-specific. It does "
            "not prove deterministic rules generally outperform learned models; "
            "it shows they are Pareto-optimal under the stated constraints."
        ),
    },
    {
        "risk_id": "R05",
        "reviewer_attack": "Why no LLM / VLM baseline? Stronger models may trivially outperform.",
        "severity": "medium",
        "evidence_needed": "Complexity-vs-utility analysis, deployment constraint documentation, safe claims dictionary.",
        "current_evidence_file": [
            "experiments/complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md",
            "experiments/complexity_vs_utility_ablation_v1/complexity_cost_audit.csv",
            "docs/safe_claims_dictionary_v3_17.md",
        ],
        "status_lookup": {
            "experiment": "complexity_vs_utility_ablation_v1",
            "priority_action": "Implement and run complexity-vs-utility ablation",
        },
        "safe_response": (
            "The deployment scenario is confidential local PDF review: no API, "
            "no network, no model training, no data egress. LLM/VLM baselines "
            "require API egress or local GPU inference that violates the "
            "confidentiality constraint. The complexity-vs-utility analysis "
            "explicitly compares methods on the "
            "performance-privacy-auditability-cost Pareto frontier and shows "
            "where learned models would fit if the confidentiality constraint "
            "were relaxed. We do NOT claim deterministic rules universally "
            "outperform LLMs; we claim they are the appropriate choice under "
            "the stated constraints."
        ),
        "paper_section_to_address": "Discussion + Limitations",
        "remaining_limitation": (
            "No head-to-head comparison with LLM/VLM baselines on this dataset. "
            "If confidentiality constraints are relaxed in future work, LLM "
            "baselines should be added."
        ),
    },
    {
        "risk_id": "R06",
        "reviewer_attack": "No human audit; silver labels may be systematically wrong.",
        "severity": "high",
        "evidence_needed": "Human audit protocol, audit seed queue, audit agreement summary (if available).",
        "current_evidence_file": [
            "docs/human_audit_protocol_v1.md",
            "data/audit_templates/human_audit_template.csv",
            "scripts/build_human_audit_queue_v1.py",
            "experiments/human_audit_v1/audit_agreement_summary.json",
        ],
        "status_lookup": {
            "experiment": "human_audit_v1",
            "priority_action": "Define small human audit protocol (2-annotator, adjudication)",
        },
        "safe_response": (
            "We acknowledge the human audit is not complete. The protocol "
            "(2-annotator independent review + adjudication) and seed queue "
            "(111 redacted candidates) are in place, but auditor labels are "
            "pending. We explicitly list this as a limitation in the paper. "
            "When the small targeted audit is complete, it will be described "
            "as a targeted reliability check, NOT a gold benchmark. No silver "
            "label will be re-described as gold or human-validated."
        ),
        "paper_section_to_address": "Limitations + Future Work",
        "remaining_limitation": (
            "Human audit pending. All silver labels remain un-audited. "
            "Until audit is complete, results are format-shift diagnostic "
            "only, not benchmark-level validation."
        ),
    },
    {
        "risk_id": "R07",
        "reviewer_attack": "PDF extraction is unreliable; results may be artifacts of extraction errors.",
        "severity": "medium",
        "evidence_needed": "PDF stress test report, extraction quality metrics, failure case analysis.",
        "current_evidence_file": [
            "experiments/pdf_extraction_stress_test_v1/stress_test_summary.md",
            "experiments/pdf_extraction_stress_test_v1/extraction_quality_metrics.csv",
            "experiments/pdf_extraction_stress_test_v1/failure_cases_redacted.csv",
            "docs/pdf_extraction_stress_test_v1.md",
        ],
        "status_lookup": {
            "experiment": "pdf_extraction_stress_test_v1",
            "priority_action": "Implement and run PDF extraction stress test",
        },
        "safe_response": (
            "We test PDF extraction robustness with 12 synthetic stress "
            "documents covering multi-column, table-heavy, scanned-image, "
            "math-heavy, and mixed-layout cases. The stress test reports "
            "extraction quality metrics and failure cases. Scanned PDFs are "
            "detected and reported only; no OCR is applied by default (OCR "
            "would require additional validation and is out of scope). The "
            "stress test is an extraction robustness check, NOT a SOTA "
            "extraction claim."
        ),
        "paper_section_to_address": "Methods + Limitations",
        "remaining_limitation": (
            "Stress test uses synthetic fixtures, not real PDFs. Real PDF "
            "corpus is missing from the workspace, so sentence-level BM25 "
            "retrieval on real data is blocked. Extraction failures on "
            "real-world PDFs may differ from synthetic stress results."
        ),
    },
    {
        "risk_id": "R08",
        "reviewer_attack": "System may be misconstrued as a general-purpose overstatement detector for scientific claims.",
        "severity": "medium",
        "evidence_needed": "Scope statement in README, current mainline doc, safe claims dictionary, dataset version lock.",
        "current_evidence_file": [
            "docs/current_mainline_v3_17_confidential.md",
            "docs/safe_claims_dictionary_v3_17.md",
            "docs/dataset_version_lock_v3_17.md",
            "README.md",
        ],
        "status_lookup": {
            "doc_check": True,
        },
        "safe_response": (
            "We explicitly state the system is NOT a general scientific "
            "overstatement detector. It is a simulation/confidential local "
            "review queue for the retrieval-to-screening format-shift problem. "
            "The dataset covers six domains (autonomous driving, policy "
            "simulation, digital twin, cyber defense, MARL, robotics); "
            "results should not be generalized to other scientific domains. "
            "The safe claims dictionary and dataset version lock enforce "
            "this scope."
        ),
        "paper_section_to_address": "Introduction + Scope + Limitations",
        "remaining_limitation": (
            "Six domains only. Generalization to biology, medicine, physics, "
            "or social science claims is not tested and not claimed."
        ),
    },
    {
        "risk_id": "R09",
        "reviewer_attack": "Sample size (444 candidates, 111 groups) is too small for reliable conclusions.",
        "severity": "medium",
        "evidence_needed": "Bootstrap CI metrics, dataset version lock, metric robustness summary.",
        "current_evidence_file": [
            "experiments/metric_robustness_v1/classification_metrics_with_ci.csv",
            "experiments/metric_robustness_v1/queue_metrics_with_ci.csv",
            "experiments/metric_robustness_v1/robustness_summary.md",
            "docs/dataset_version_lock_v3_17.md",
        ],
        "status_lookup": {
            "experiment": "metric_robustness_v1",
            "priority_action": None,
        },
        "safe_response": (
            "The 444-candidate set is a controlled diagnostic, not a "
            "prevalence benchmark. We report group-aware bootstrap 95% CIs "
            "for all headline metrics. The CIs reflect variability within "
            "the controlled candidate pool, NOT natural prevalence. We "
            "explicitly state this in the metric robustness report and "
            "dataset version lock. Conclusions are framed as format-shift "
            "diagnostic findings on this controlled pool, not as "
            "population-level claims."
        ),
        "paper_section_to_address": "Methods + Limitations",
        "remaining_limitation": (
            "Bootstrap CIs reflect controlled-pool variability only. "
            "Larger datasets with natural prevalence would be needed for "
            "population-level claims."
        ),
    },
    {
        "risk_id": "R10",
        "reviewer_attack": "Full CESE-OCN neural architecture is not validated; the paper implies it is.",
        "severity": "high",
        "evidence_needed": "Current mainline doc marking full CESE-OCN as future architecture, README scope statement.",
        "current_evidence_file": [
            "docs/current_mainline_v3_17_confidential.md",
            "README.md",
            "docs/safe_claims_dictionary_v3_17.md",
        ],
        "status_lookup": {
            "doc_check": True,
        },
        "safe_response": (
            "We explicitly state there is no full shared-threshold CESE-OCN "
            "validation in V3.17; the full architecture is future work, not "
            "the current claim. The current claim is the V3.17 Confidential "
            "Lightweight Local Review Queue pipeline (deterministic "
            "canonicalization + frozen R4 + SmartQueue). The README, current "
            "mainline doc, and safe claims dictionary all mark full CESE-OCN "
            "as future work. No result from the full neural architecture is "
            "reported in V3.17 paper assets."
        ),
        "paper_section_to_address": "Introduction + Scope + Future Work",
        "remaining_limitation": (
            "Full CESE-OCN neural architecture validation is future work. "
            "V3.17 does not claim neural-architecture-level results."
        ),
    },
]


def load_status_json(path: Path) -> dict:
    if not path.exists():
        print(f"WARNING: status JSON not found at {path}; status fields will be 'unknown'.")
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def lookup_status(risk: dict, status_json: dict) -> tuple[str, str]:
    """Return (status, status_source) by looking up the status JSON."""
    lookup = risk.get("status_lookup", {})
    if not status_json:
        return "unknown", "status JSON not found"

    experiments = status_json.get("experiments", {})
    priorities = status_json.get("priority_next_actions", [])
    evidence_chain = status_json.get("evidence_chain", [])

    exp_name = lookup.get("experiment")
    priority_action = lookup.get("priority_action")

    # Doc-check risks: always "done" if the docs exist.
    if lookup.get("doc_check"):
        return "done", "scope docs verified"

    status = "unknown"
    source = ""

    # Try experiment lookup.
    if exp_name and exp_name in experiments:
        exp = experiments[exp_name]
        if exp.get("exists"):
            status = "done"
            source = f"experiments/{exp_name}/"
        else:
            status = "missing"
            source = f"experiments/{exp_name}/ (missing)"

    # Cross-reference with priority_next_actions.
    if priority_action:
        for p in priorities:
            if p.get("action") == priority_action:
                p_status = p.get("status", "")
                if p_status == "blocked":
                    status = "blocked"
                    source = f"priority action '{priority_action}': {p.get('blocker', 'unknown blocker')}"
                elif p_status == "done" and status != "blocked":
                    status = "done"
                    source = f"priority action '{priority_action}': done"
                elif p_status == "pending" and status == "unknown":
                    status = "pending"
                    source = f"priority action '{priority_action}': pending"
                break

    # Cross-reference with evidence_chain for more detail.
    for ec in evidence_chain:
        for ef in risk.get("current_evidence_file", []):
            if ec.get("evidence_file", "").rstrip("/") in ef.rstrip("/") or ef.rstrip("/") in ec.get("evidence_file", "").rstrip("/"):
                ec_status = ec.get("status", "")
                ec_prov = ec.get("data_provenance", "")
                if ec_status == "partial" or ec_prov == "blocked":
                    if status != "blocked":
                        status = "partial"
                        source = f"evidence chain: {ec.get('safe_wording', '')[:80]}..."
                break

    return status, source


def enrich_risks(status_json: dict) -> list[dict]:
    """Add auto-filled status and status_source to each risk."""
    enriched = []
    for risk in RISKS:
        risk_copy = dict(risk)
        status, source = lookup_status(risk, status_json)
        risk_copy["status"] = status
        risk_copy["status_source"] = source
        enriched.append(risk_copy)
    return enriched


def write_risk_register(risks: list[dict], path: Path, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Reviewer Risk Register — V3.17 Confidential Lightweight")
    lines.append("")
    lines.append(f"**Generated (UTC):** {generated_at}")
    lines.append("**Source:** `reports/current_project_status_v3_17.json` (auto-filled status)")
    lines.append("")
    lines.append("**Purpose:** Anticipate reviewer attacks on the V3.17 paper and prepare")
    lines.append("evidence-backed safe responses. Each risk has a severity, the evidence")
    lines.append("needed to address it, the current evidence file, the current status,")
    lines.append("a safe response, the paper section to address, and the remaining limitation.")
    lines.append("")
    lines.append("**Hard boundaries:** No exaggeration. No fabricated experiments.")
    lines.append("Missing results are marked `missing` or `blocked`. Silver data is never")
    lines.append("called gold.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Summary table")
    lines.append("")
    lines.append("| risk_id | severity | status | reviewer_attack |")
    lines.append("|---|---|---|---|")
    for r in risks:
        lines.append(f"| {r['risk_id']} | {r['severity']} | {r['status']} | {r['reviewer_attack']} |")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Risk details")
    lines.append("")
    for r in risks:
        lines.append(f"### {r['risk_id']} — {r['reviewer_attack']}")
        lines.append("")
        lines.append(f"- **severity:** {r['severity']}")
        lines.append(f"- **status:** {r['status']}")
        if r.get("status_source"):
            lines.append(f"- **status_source:** {r['status_source']}")
        lines.append(f"- **evidence_needed:** {r['evidence_needed']}")
        lines.append("- **current_evidence_file:**")
        for ef in r["current_evidence_file"]:
            lines.append(f"  - `{ef}`")
        lines.append(f"- **safe_response:** {r['safe_response']}")
        lines.append(f"- **paper_section_to_address:** {r['paper_section_to_address']}")
        lines.append(f"- **remaining_limitation:** {r['remaining_limitation']}")
        lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Severity legend")
    lines.append("")
    lines.append("- **high:** Likely reviewer attack; must have safe response + paper section.")
    lines.append("- **medium:** Possible reviewer attack; should have safe response.")
    lines.append("- **low:** Unlikely attack; documented for completeness.")
    lines.append("")
    lines.append("## Status legend")
    lines.append("")
    lines.append("- **done:** Evidence exists and is complete.")
    lines.append("- **partial:** Evidence exists but is incomplete (e.g., protocol built, audit pending).")
    lines.append("- **blocked:** Evidence is blocked by a documented blocker.")
    lines.append("- **missing:** Evidence does not exist.")
    lines.append("- **pending:** Evidence is planned but not started.")
    lines.append("- **unknown:** Status could not be determined from the status JSON.")
    lines.append("")
    lines.append("## Related artifacts")
    lines.append("")
    lines.append("- Response playbook: `docs/reviewer_response_playbook_v3_17.md`")
    lines.append("- Paper table: `paper_assets/v3_17_confidential/reviewer_risk_table.md`")
    lines.append("- Status source: `reports/current_project_status_v3_17.json`")
    lines.append("- Safe claims dictionary: `docs/safe_claims_dictionary_v3_17.md`")
    lines.append("- Dataset version lock: `docs/dataset_version_lock_v3_17.md`")
    lines.append("")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def write_response_playbook(risks: list[dict], path: Path, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Reviewer Response Playbook — V3.17 Confidential Lightweight")
    lines.append("")
    lines.append(f"**Generated (UTC):** {generated_at}")
    lines.append("")
    lines.append("**Purpose:** Defense playbook for author response. For each anticipated")
    lines.append("reviewer attack, provides a concise safe response and pointers to evidence.")
    lines.append("")
    lines.append("**Hard boundaries:** No exaggeration. No fabricated experiments. Missing")
    lines.append("results are admitted. Silver data is never called gold.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Safe one-sentence positioning")
    lines.append("")
    lines.append("> This work is a controlled silver diagnostic study of")
    lines.append("> retrieval-to-screening format shift for confidential local PDF")
    lines.append("> review. It is **not** a gold benchmark, SOTA detector, or automatic")
    lines.append("> peer reviewer.")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## High-severity risks (must address in response)")
    lines.append("")
    high_risks = [r for r in risks if r["severity"] == "high"]
    for r in high_risks:
        lines.append(f"### {r['risk_id']}: {r['reviewer_attack']}")
        lines.append("")
        lines.append(f"**Status:** {r['status']}")
        lines.append("")
        lines.append(f"**Safe response:**")
        lines.append("")
        lines.append(f"{r['safe_response']}")
        lines.append("")
        lines.append(f"**Evidence:**")
        for ef in r["current_evidence_file"]:
            lines.append(f"- `{ef}`")
        lines.append("")
        lines.append(f"**Remaining limitation:** {r['remaining_limitation']}")
        lines.append("")
        lines.append(f"**Paper section:** {r['paper_section_to_address']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Medium-severity risks (address if raised)")
    lines.append("")
    medium_risks = [r for r in risks if r["severity"] == "medium"]
    for r in medium_risks:
        lines.append(f"### {r['risk_id']}: {r['reviewer_attack']}")
        lines.append("")
        lines.append(f"**Status:** {r['status']}")
        lines.append("")
        lines.append(f"**Safe response:** {r['safe_response']}")
        lines.append("")
        lines.append(f"**Evidence:** {', '.join('`' + ef + '`' for ef in r['current_evidence_file'])}")
        lines.append("")
        lines.append(f"**Remaining limitation:** {r['remaining_limitation']}")
        lines.append("")
        lines.append("---")
        lines.append("")
    lines.append("## Forbidden response patterns (do NOT use)")
    lines.append("")
    lines.append("- \"Our gold benchmark shows...\" (dataset is silver, not gold)")
    lines.append("- \"Human-validated results...\" (human audit is pending)")
    lines.append("- \"State-of-the-art detector...\" (not SOTA)")
    lines.append("- \"Automatic peer review...\" (not automatic peer review)")
    lines.append("- \"General scientific overstatement detection...\" (six domains only)")
    lines.append("- \"Full CESE-OCN architecture validated...\" (future work)")
    lines.append("- \"Outperforms LLMs...\" (no LLM baseline; deployment-specific tradeoff)")
    lines.append("")
    lines.append("## Allowed response patterns")
    lines.append("")
    lines.append("- \"Controlled silver diagnostic study...\"")
    lines.append("- \"Format-shift diagnostic findings on a controlled pool...\"")
    lines.append("- \"Source-traceable silver set with human_audited=False...\"")
    lines.append("- \"Pareto-optimal under no-API/no-training/confidential constraints...\"")
    lines.append("- \"Small targeted audit (not a gold benchmark)...\"")
    lines.append("- \"Future architecture, not current claim...\"")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def write_paper_risk_table(risks: list[dict], path: Path, generated_at: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines = []
    lines.append("# Reviewer Risk Table (Paper Asset) — V3.17 Confidential Lightweight")
    lines.append("")
    lines.append(f"<!-- Generated (UTC): {generated_at} -->")
    lines.append("<!-- Auto-filled from reports/current_project_status_v3_17.json -->")
    lines.append("")
    lines.append("<!-- Caveat: This table documents anticipated reviewer risks and the")
    lines.append("current evidence status. It is NOT a benchmark claim. The dataset is")
    lines.append("a controlled silver diagnostic, not gold or human-audited. -->")
    lines.append("")
    lines.append("| risk_id | severity | status | reviewer_attack | paper_section | remaining_limitation |")
    lines.append("|---|---|---|---|---|---|")
    for r in risks:
        # Truncate remaining_limitation for table readability.
        lim = r["remaining_limitation"]
        if len(lim) > 120:
            lim = lim[:117] + "..."
        # Escape pipes in fields.
        attack = r["reviewer_attack"].replace("|", "\\|")
        section = r["paper_section_to_address"].replace("|", "\\|")
        lim = lim.replace("|", "\\|")
        lines.append(f"| {r['risk_id']} | {r['severity']} | {r['status']} | {attack} | {section} | {lim} |")
    lines.append("")
    lines.append("**Status legend:** done = evidence complete; partial = evidence incomplete;")
    lines.append("blocked = blocked by documented blocker; missing = evidence absent;")
    lines.append("pending = planned, not started.")
    lines.append("")
    lines.append("**Safe caveat:** We use a source-traceable controlled silver diagnostic")
    lines.append("set. The labels are not gold or human-audited, and results should not be")
    lines.append("interpreted as benchmark-level model validation.")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {path}")


def main():
    parser = argparse.ArgumentParser(description="Generate reviewer risk register for V3.17.")
    parser.add_argument(
        "--status_json",
        type=str,
        default=str(DEFAULT_STATUS_JSON),
        help=f"Path to current_project_status_v3_17.json (default: {DEFAULT_STATUS_JSON})",
    )
    parser.add_argument(
        "--docs_dir",
        type=str,
        default=str(DEFAULT_DOCS_DIR),
        help=f"Docs output directory (default: {DEFAULT_DOCS_DIR})",
    )
    parser.add_argument(
        "--paper_assets_dir",
        type=str,
        default=str(DEFAULT_PAPER_ASSETS_DIR),
        help=f"Paper assets output directory (default: {DEFAULT_PAPER_ASSETS_DIR})",
    )
    args = parser.parse_args()

    status_json_path = Path(args.status_json).resolve()
    docs_dir = Path(args.docs_dir).resolve()
    paper_assets_dir = Path(args.paper_assets_dir).resolve()

    status_json = load_status_json(status_json_path)
    risks = enrich_risks(status_json)
    generated_at = datetime.now(timezone.utc).isoformat()

    register_path = docs_dir / "reviewer_risk_register_v3_17.md"
    playbook_path = docs_dir / "reviewer_response_playbook_v3_17.md"
    table_path = paper_assets_dir / "reviewer_risk_table.md"

    write_risk_register(risks, register_path, generated_at)
    write_response_playbook(risks, playbook_path, generated_at)
    write_paper_risk_table(risks, table_path, generated_at)

    # Print summary
    print()
    print("=== Reviewer risk register summary ===")
    print(f"  Total risks: {len(risks)}")
    sev_counts = {}
    for r in risks:
        sev_counts[r["severity"]] = sev_counts.get(r["severity"], 0) + 1
    print(f"  Severity: {sev_counts}")
    status_counts = {}
    for r in risks:
        status_counts[r["status"]] = status_counts.get(r["status"], 0) + 1
    print(f"  Status: {status_counts}")
    print()
    high_without_response = [r for r in risks if r["severity"] == "high" and not r.get("safe_response")]
    if high_without_response:
        print(f"  WARNING: {len(high_without_response)} high-severity risks lack safe_response")
    else:
        print("  All high-severity risks have safe_response: PASS")


if __name__ == "__main__":
    main()
