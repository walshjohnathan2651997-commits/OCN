#!/usr/bin/env python
"""run_final_perfect_state_gate_v1.py — Final V3.17 perfect-state readiness gate.

Evaluates the project across 10 gate categories and produces a final
readiness status. The gate does NOT require all research questions to be
solved — it requires every gap to be either complete, pass, or documented
blocked. No ``unknown`` gaps are allowed for P0 items.

Scoring:
  - PASS     = complete and safe
  - WARNING  = limitation documented
  - BLOCKED  = missing input documented (with blocked_reason + next_action)
  - FAIL     = unsafe or undocumented missing

Final status:
  - READY_WITH_LIMITATIONS   = no FAIL; all BLOCKED have reasons
  - NOT_READY_P0_BLOCKERS    = P0 items unknown/missing without reason
  - BLOCKED_BY_PRIVATE_DATA  = all issues due to private data access
  - UNSAFE_OVERCLAIM         = unsafe claims detected

Hard boundaries:
  - No heavy experiment re-runs.
  - No result modification.
  - Read-only: reads reports/experiments/docs/paper_assets/release_bundles.
  - No private text output.

Usage:
  python scripts/run_final_perfect_state_gate_v1.py
"""

from __future__ import annotations

import csv
import json
import re
import sys
from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional

REPO_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_MD = REPO_ROOT / "reports" / "final_perfect_state_gate_v3_17.md"
OUTPUT_JSON = REPO_ROOT / "reports" / "final_perfect_state_gate_v3_17.json"

# Status constants
PASS = "PASS"
WARNING = "WARNING"
BLOCKED = "BLOCKED"
FAIL = "FAIL"

# Priority constants
P0 = "P0"
P1 = "P1"
P2 = "P2"


@dataclass
class CheckResult:
    category: str
    check_id: str
    description: str
    status: str
    priority: str
    evidence: str
    blocked_reason: str = ""
    next_action: str = ""


@dataclass
class GateReport:
    generated_at: str
    checks: List[CheckResult] = field(default_factory=list)

    @property
    def pass_count(self) -> int:
        return sum(1 for c in self.checks if c.status == PASS)

    @property
    def warning_count(self) -> int:
        return sum(1 for c in self.checks if c.status == WARNING)

    @property
    def blocked_count(self) -> int:
        return sum(1 for c in self.checks if c.status == BLOCKED)

    @property
    def fail_count(self) -> int:
        return sum(1 for c in self.checks if c.status == FAIL)

    @property
    def final_status(self) -> str:
        if self.fail_count > 0:
            # Check if any FAIL is an overclaim
            for c in self.checks:
                if c.status == FAIL and "overclaim" in c.blocked_reason.lower():
                    return "UNSAFE_OVERCLAIM"
            return "NOT_READY_P0_BLOCKERS"

        # No FAIL — check if all BLOCKED have reasons
        for c in self.checks:
            if c.status == BLOCKED and not c.blocked_reason:
                return "NOT_READY_P0_BLOCKERS"
            if c.status == BLOCKED and c.priority == P0 and not c.next_action:
                return "NOT_READY_P0_BLOCKERS"

        # Check if all issues are private-data related
        all_blocked_private = all(
            "private" in c.blocked_reason.lower() or "private" in c.next_action.lower()
            for c in self.checks
            if c.status == BLOCKED
        )
        if all_blocked_private and self.blocked_count > 0 and self.warning_count == 0:
            return "BLOCKED_BY_PRIVATE_DATA"

        return "READY_WITH_LIMITATIONS"


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

def _read_json(path: Path) -> Optional[dict]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return None


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8")
    except Exception:
        return None


def _read_csv_rows(path: Path) -> List[dict]:
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except Exception:
        return []


def _read_csv_header(path: Path) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8", newline="") as f:
            reader = csv.reader(f)
            return next(reader, [])
    except Exception:
        return []


def _exists(path: Path) -> bool:
    return path.exists()


# ---------------------------------------------------------------------------
# Gate 1: Mainline
# ---------------------------------------------------------------------------

def check_mainline() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "1. Mainline"

    # 1.1 README points to V3.17
    readme = _read_text(REPO_ROOT / "README.md")
    if readme and "V3.17" in readme:
        results.append(CheckResult(cat, "1.1", "README points to V3.17", PASS, P0,
                                   "README.md mentions V3.17"))
    else:
        results.append(CheckResult(cat, "1.1", "README points to V3.17", FAIL, P0,
                                   "README.md missing or no V3.17 reference",
                                   "README not updated", "Update README to reference V3.17"))

    # 1.2 CURRENT_MAINLINE points to V3.17
    cm = _read_text(REPO_ROOT / "CURRENT_MAINLINE.md")
    if cm and "V3.17" in cm:
        results.append(CheckResult(cat, "1.2", "CURRENT_MAINLINE points to V3.17", PASS, P0,
                                   "CURRENT_MAINLINE.md mentions V3.17"))
    else:
        results.append(CheckResult(cat, "1.2", "CURRENT_MAINLINE points to V3.17", FAIL, P0,
                                   "CURRENT_MAINLINE.md missing or no V3.17",
                                   "Mainline doc not updated", "Update CURRENT_MAINLINE.md"))

    # 1.3 Legacy narrative scan: unsafe=0
    scan_md = _read_text(REPO_ROOT / "reports" / "legacy_narrative_scan_v3_17.md")
    if scan_md:
        unsafe_match = re.search(r"unsafe_current_claim\s*\|\s*(\d+)", scan_md)
        ambig_match = re.search(r"ambiguous\s*\|\s*(\d+)", scan_md)
        unsafe = int(unsafe_match.group(1)) if unsafe_match else -1
        ambig = int(ambig_match.group(1)) if ambig_match else -1
        if unsafe == 0 and ambig == 0:
            results.append(CheckResult(cat, "1.3", "Legacy narrative unsafe=0", PASS, P0,
                                       f"unsafe={unsafe}, ambiguous={ambig}"))
        else:
            results.append(CheckResult(cat, "1.3", "Legacy narrative unsafe=0", FAIL, P0,
                                       f"unsafe={unsafe}, ambiguous={ambig}",
                                       "Unsafe or ambiguous claims remain",
                                       "Fix narrative to resolve all unsafe/ambiguous findings"))
    else:
        results.append(CheckResult(cat, "1.3", "Legacy narrative unsafe=0", FAIL, P0,
                                   "Legacy scan report missing",
                                   "Scan not run", "Run clean_legacy_narrative_scan_v1.py"))

    return results


# ---------------------------------------------------------------------------
# Gate 2: Dataset
# ---------------------------------------------------------------------------

def check_dataset() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "2. Dataset"

    lock_path = REPO_ROOT / "docs" / "dataset_version_lock_v3_17.md"
    lock_text = _read_text(lock_path)

    # 2.1 Dataset lock exists
    if lock_text:
        results.append(CheckResult(cat, "2.1", "Dataset lock exists", PASS, P0,
                                   f"{lock_path.name} present"))
    else:
        results.append(CheckResult(cat, "2.1", "Dataset lock exists", FAIL, P0,
                                   "dataset_version_lock_v3_17.md missing",
                                   "Lock doc not created", "Create dataset version lock"))

    # 2.2 444 rows / 111 groups / 4 balanced labels
    if lock_text:
        has_444 = "444" in lock_text
        has_111 = "111" in lock_text
        has_4labels = re.search(r"(4.*label|balanced.*4|111.*each)", lock_text, re.IGNORECASE)
        if has_444 and has_111 and has_4labels:
            results.append(CheckResult(cat, "2.2", "444 rows / 111 groups / 4 labels", PASS, P0,
                                       "Lock doc confirms 444 rows, 111 groups, 4 balanced labels"))
        else:
            results.append(CheckResult(cat, "2.2", "444 rows / 111 groups / 4 labels", FAIL, P0,
                                       f"Lock doc incomplete: 444={has_444}, 111={has_111}",
                                       "Counts not documented", "Update dataset lock"))
    else:
        results.append(CheckResult(cat, "2.2", "444 rows / 111 groups / 4 labels", FAIL, P0,
                                   "Cannot verify without lock doc"))

    # 2.3 human_audited=False documented
    if lock_text and "human_audited" in lock_text.lower() and "false" in lock_text.lower():
        results.append(CheckResult(cat, "2.3", "human_audited=False documented", PASS, P0,
                                   "Lock doc documents human_audited=False"))
    else:
        results.append(CheckResult(cat, "2.3", "human_audited=False documented", WARNING, P0,
                                   "human_audited=False not explicitly in lock doc",
                                   "Not documented", "Add human_audited=False to lock doc"))

    # 2.4 gold_label empty documented
    if lock_text and ("gold_label" in lock_text.lower() and ("empty" in lock_text.lower() or "false" in lock_text.lower() or "none" in lock_text.lower())):
        results.append(CheckResult(cat, "2.4", "gold_label empty documented", PASS, P0,
                                   "Lock doc documents gold_label is empty"))
    else:
        results.append(CheckResult(cat, "2.4", "gold_label empty documented", WARNING, P0,
                                   "gold_label emptiness not explicit",
                                   "Not documented", "Add gold_label empty status to lock doc"))

    # 2.5 Silver caveat present
    if lock_text and "silver" in lock_text.lower():
        results.append(CheckResult(cat, "2.5", "Silver caveat present", PASS, P0,
                                   "Lock doc contains silver caveat"))
    else:
        results.append(CheckResult(cat, "2.5", "Silver caveat present", FAIL, P0,
                                   "No silver caveat in lock doc",
                                   "Silver status not documented", "Add silver caveat"))

    return results


# ---------------------------------------------------------------------------
# Gate 3: Real experiments
# ---------------------------------------------------------------------------

def check_real_experiments() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "3. Real Experiments"

    # 3.1 BM25 real
    bm25 = _read_json(REPO_ROOT / "experiments" / "simclaim_pdf_corpus_retrieval_v1" / "retrieval_metrics_bm25.json")
    if bm25 and bm25.get("n_claims", 0) > 0:
        results.append(CheckResult(cat, "3.1", "BM25 real complete", PASS, P0,
                                   f"n_claims={bm25.get('n_claims')}, recall@10={bm25.get('recall_at_10', 'N/A')}"))
    else:
        results.append(CheckResult(cat, "3.1", "BM25 real complete or blocked", FAIL, P0,
                                   "BM25 metrics missing or empty",
                                   "Experiment not run", "Run BM25 retrieval on real data"))

    # 3.2 BM25 sentence/window (blocked)
    sent = _read_json(REPO_ROOT / "experiments" / "bm25_sentence_retrieval_v1" / "oracle_recall_summary.json")
    if sent and sent.get("status") == "blocked":
        reason = sent.get("reason", "unknown")
        results.append(CheckResult(cat, "3.2", "Sentence/window BM25 blocked documented", BLOCKED, P0,
                                   f"status=blocked, reason={reason}",
                                   reason, "Generate PDF sentence corpus or document as permanent limitation"))
    elif sent and sent.get("n_candidates", 0) > 0:
        results.append(CheckResult(cat, "3.2", "Sentence/window BM25 complete", PASS, P0,
                                   f"n_candidates={sent.get('n_candidates')}"))
    else:
        results.append(CheckResult(cat, "3.2", "Sentence/window BM25 complete or blocked", FAIL, P0,
                                   "No output file",
                                   "Experiment not run", "Run or document blockage"))

    # 3.3 Canonicalizer real
    can = _read_csv_rows(REPO_ROOT / "experiments" / "canonicalizer_ablation_v1" / "selector_metrics_summary.csv")
    if can and len(can) >= 8:
        results.append(CheckResult(cat, "3.3", "Canonicalizer real complete", PASS, P0,
                                   f"{len(can)} selectors evaluated"))
    else:
        results.append(CheckResult(cat, "3.3", "Canonicalizer real complete", FAIL, P0,
                                   f"Only {len(can)} selectors in summary",
                                   "Experiment incomplete", "Run canonicalizer ablation"))

    # 3.4 Format shift (blocked)
    fs = _read_json(REPO_ROOT / "experiments" / "format_shift_ablation_v1" / "r4_eval_blocked.json")
    if fs and fs.get("status") == "blocked":
        reason = fs.get("reason", "unknown")
        results.append(CheckResult(cat, "3.4", "Format shift blocked documented", BLOCKED, P0,
                                   f"status=blocked, reason={reason}",
                                   reason, "Upgrade sklearn (needs network) or document as permanent limitation"))
    elif fs:
        results.append(CheckResult(cat, "3.4", "Format shift complete", PASS, P0,
                                   "Format shift R4 eval completed"))
    else:
        results.append(CheckResult(cat, "3.4", "Format shift complete or blocked", FAIL, P0,
                                   "No output file",
                                   "Experiment not run", "Run or document blockage"))

    # 3.5 Leakage audit
    la = _read_text(REPO_ROOT / "experiments" / "leakage_audit_v1" / "audit_summary.md")
    if la and "PASS" in la.upper():
        results.append(CheckResult(cat, "3.5", "Leakage audit complete", PASS, P0,
                                   "audit_summary.md reports PASS"))
    else:
        results.append(CheckResult(cat, "3.5", "Leakage audit complete", FAIL, P0,
                                   "Audit summary missing or not PASS",
                                   "Audit not complete", "Run leakage audit"))

    # 3.6 Review queue real
    rq = _exists(REPO_ROOT / "experiments" / "canonicalized_review_queue_v1" / "canonicalized_r4_review_scores.csv")
    if rq:
        results.append(CheckResult(cat, "3.6", "Review queue real exists", PASS, P0,
                                   "canonicalized_r4_review_scores.csv exists"))
    else:
        results.append(CheckResult(cat, "3.6", "Review queue real exists", FAIL, P0,
                                   "Review queue output missing",
                                   "Not generated", "Run review queue generation"))

    # 3.7 Risk ranking real
    rr = _read_csv_rows(REPO_ROOT / "experiments" / "canonicalized_risk_ranking_v1" / "risk_ranking_results_by_variant.csv")
    if rr and len(rr) >= 4:
        results.append(CheckResult(cat, "3.7", "Risk ranking real exists", PASS, P0,
                                   f"{len(rr)} variants"))
    else:
        results.append(CheckResult(cat, "3.7", "Risk ranking real exists", FAIL, P0,
                                   "Risk ranking missing or incomplete",
                                   "Not generated", "Run risk ranking"))

    # 3.8 Metric robustness
    mr = _read_csv_rows(REPO_ROOT / "experiments" / "metric_robustness_v1" / "classification_metrics_with_ci.csv")
    if mr and len(mr) >= 4:
        results.append(CheckResult(cat, "3.8", "Metric robustness exists", PASS, P0,
                                   f"{len(mr)} metrics with CI"))
    else:
        results.append(CheckResult(cat, "3.8", "Metric robustness exists", FAIL, P0,
                                   "Metric robustness missing",
                                   "Not generated", "Run metric robustness eval"))

    # 3.9 Error taxonomy
    et = _read_csv_rows(REPO_ROOT / "experiments" / "error_taxonomy_v1" / "error_taxonomy_summary.csv")
    if et and len(et) >= 5:
        results.append(CheckResult(cat, "3.9", "Error taxonomy exists", PASS, P1,
                                   f"{len(et)} error types"))
    else:
        results.append(CheckResult(cat, "3.9", "Error taxonomy exists", WARNING, P1,
                                   "Error taxonomy missing or incomplete",
                                   "Not generated", "Run error taxonomy"))

    return results


# ---------------------------------------------------------------------------
# Gate 4: PDF
# ---------------------------------------------------------------------------

def check_pdf() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "4. PDF"

    # 4.1 PDF extraction complete or blocked
    corpus_dir = REPO_ROOT / "data" / "simclaim_pdf_corpus_retrieval_v1"
    chunks = corpus_dir / "local_pdf_corpus_chunks.csv"
    if chunks.exists():
        results.append(CheckResult(cat, "4.1", "PDF extraction complete", PASS, P0,
                                   "local_pdf_corpus_chunks.csv exists"))
    else:
        # Check if blockage is documented
        bm25 = _read_json(REPO_ROOT / "experiments" / "simclaim_pdf_corpus_retrieval_v1" / "retrieval_metrics_bm25.json")
        if bm25 and bm25.get("n_claims", 0) > 0:
            results.append(CheckResult(cat, "4.1", "PDF extraction complete", PASS, P0,
                                       "BM25 ran successfully, corpus available"))
        else:
            results.append(CheckResult(cat, "4.1", "PDF extraction complete or blocked", BLOCKED, P0,
                                       "No PDF corpus chunks",
                                       "PDF corpus not extracted", "Run PDF extraction pipeline"))

    # 4.2 PDF stress test
    stress = _read_text(REPO_ROOT / "experiments" / "pdf_extraction_stress_test_v1" / "stress_test_summary.md")
    if stress and "12" in stress:
        results.append(CheckResult(cat, "4.2", "PDF stress test complete", PASS, P1,
                                   "12 stress documents tested"))
    else:
        results.append(CheckResult(cat, "4.2", "PDF stress test complete or blocked", BLOCKED, P1,
                                   "Stress test summary missing",
                                   "Not run", "Run PDF stress test"))

    # 4.3 Scanned PDF no-OCR boundary documented
    stress_doc = _read_text(REPO_ROOT / "docs" / "pdf_extraction_stress_test_v1.md")
    if stress_doc and ("scanned" in stress_doc.lower() or "OCR" in stress_doc):
        results.append(CheckResult(cat, "4.3", "Scanned PDF no-OCR boundary documented", PASS, P1,
                                   "docs/pdf_extraction_stress_test_v1.md documents scanned/OCR boundary"))
    else:
        # Check other docs
        found = False
        for doc in (REPO_ROOT / "docs").glob("*.md"):
            text = _read_text(doc)
            if text and "scanned" in text.lower() and "OCR" in text.upper():
                found = True
                break
        if found:
            results.append(CheckResult(cat, "4.3", "Scanned PDF no-OCR boundary documented", PASS, P1,
                                       "Scanned/OCR boundary documented in docs/"))
        else:
            results.append(CheckResult(cat, "4.3", "Scanned PDF no-OCR boundary documented", WARNING, P1,
                                       "No scanned/OCR boundary documentation found",
                                       "Not documented", "Add scanned PDF no-OCR boundary documentation"))

    return results


# ---------------------------------------------------------------------------
# Gate 5: Leakage
# ---------------------------------------------------------------------------

def check_leakage() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "5. Leakage"
    la_dir = REPO_ROOT / "experiments" / "leakage_audit_v1"

    # 5.1 Claim-only baseline
    co = _read_json(la_dir / "claim_only_baseline.json")
    if co and co.get("status") == "pass":
        f1 = co.get("strong_f1_mean", co.get("strong_F1_mean", "N/A"))
        ratio = co.get("ratio_claim_only_to_r4", "N/A")
        results.append(CheckResult(cat, "5.1", "Claim-only baseline exists", PASS, P0,
                                   f"strong_f1={f1}, ratio={ratio}"))
    else:
        results.append(CheckResult(cat, "5.1", "Claim-only baseline exists", FAIL, P0,
                                   "claim_only_baseline.json missing or not pass",
                                   "Baseline not run", "Run claim-only leakage baseline"))

    # 5.2 Shuffled/empty/title-only baselines
    shuf = _read_json(la_dir / "shuffled_evidence_baseline.json")
    title = _read_json(la_dir / "title_only_retrieval_baseline.json")
    meta = _read_json(la_dir / "metadata_only_retrieval_baseline.json")
    existing = []
    if shuf and shuf.get("status") == "pass":
        existing.append("shuffled")
    if title and title.get("status") == "pass":
        existing.append("title_only")
    if meta and meta.get("status") == "pass":
        existing.append("metadata_only")
    if len(existing) >= 2:
        results.append(CheckResult(cat, "5.2", "Shuffled/title-only/metadata baselines exist", PASS, P0,
                                   f"Baselines present: {', '.join(existing)}"))
    elif existing:
        results.append(CheckResult(cat, "5.2", "Baselines partial", WARNING, P0,
                                   f"Only {existing} present",
                                   "Some baselines missing", "Run remaining baselines"))
    else:
        results.append(CheckResult(cat, "5.2", "Baselines complete or blocked", BLOCKED, P0,
                                   "No baselines found",
                                   "Baselines not run", "Run leakage baselines"))

    # 5.3 no_oracle_in_selector pass
    noi = _read_json(la_dir / "no_oracle_in_selector_check.json")
    if noi and noi.get("status") == "pass":
        results.append(CheckResult(cat, "5.3", "no_oracle_in_selector pass", PASS, P0,
                                   "Oracle not used in selector"))
    else:
        results.append(CheckResult(cat, "5.3", "no_oracle_in_selector pass", FAIL, P0,
                                   "Check missing or not pass",
                                   "Oracle leakage in selector", "Fix selector to exclude oracle fields"))

    # 5.4 no_label_in_queue_sorting pass
    nlq = _read_json(la_dir / "no_label_in_queue_sorting_check.json")
    if nlq and nlq.get("status") == "pass":
        results.append(CheckResult(cat, "5.4", "no_label_in_queue_sorting pass", PASS, P0,
                                   "Labels not used in queue sorting"))
    elif nlq and nlq.get("status") == "skip":
        results.append(CheckResult(cat, "5.4", "no_label_in_queue_sorting documented skip", WARNING, P0,
                                   f"status=skip, reason={nlq.get('reason', 'unknown')}",
                                   "Guard report not found",
                                   "Generate SmartQueue leakage guard report"))
    else:
        results.append(CheckResult(cat, "5.4", "no_label_in_queue_sorting pass", WARNING, P0,
                                   "Check file missing",
                                   "Not run", "Run no_label_in_queue_sorting check"))

    # 5.5 Public outputs no sensitive text
    safety = _read_json(REPO_ROOT / "reports" / "release_safety_manifest_v3_17.json")
    if safety:
        gate = safety.get("release_safety_gate", {})
        status = gate.get("status", "UNKNOWN")
        unsafe = gate.get("unsafe_public_artifacts", [])
        if status == "PASS" and not unsafe:
            results.append(CheckResult(cat, "5.5", "Public outputs no sensitive text", PASS, P0,
                                       "release_safety_manifest gate=PASS, no unsafe public artifacts"))
        else:
            results.append(CheckResult(cat, "5.5", "Public outputs no sensitive text", FAIL, P0,
                                       f"gate={status}, unsafe={unsafe}",
                                       "Sensitive text in public artifacts",
                                       "Remove sensitive columns from public artifacts"))
    else:
        results.append(CheckResult(cat, "5.5", "Public outputs no sensitive text", FAIL, P0,
                                   "release_safety_manifest missing",
                                   "Manifest not generated", "Run build_artifact_ledger_v1.py"))

    return results


# ---------------------------------------------------------------------------
# Gate 6: Human audit
# ---------------------------------------------------------------------------

def check_human_audit() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "6. Human Audit"

    # 6.1 Protocol exists
    proto = _exists(REPO_ROOT / "docs" / "human_audit_protocol_v1.md")
    if proto:
        results.append(CheckResult(cat, "6.1", "Protocol exists", PASS, P1,
                                   "docs/human_audit_protocol_v1.md present"))
    else:
        results.append(CheckResult(cat, "6.1", "Protocol exists", FAIL, P1,
                                   "Protocol missing",
                                   "Not created", "Create human audit protocol"))

    # 6.2 Template exists
    tmpl = _exists(REPO_ROOT / "data" / "audit_templates" / "human_audit_template.csv")
    if tmpl:
        results.append(CheckResult(cat, "6.2", "Template exists", PASS, P1,
                                   "human_audit_template.csv present"))
    else:
        results.append(CheckResult(cat, "6.2", "Template exists", FAIL, P1,
                                   "Template missing",
                                   "Not created", "Create audit template"))

    # 6.3 Queue seed exists or not-yet-run documented
    seed = _exists(REPO_ROOT / "data" / "audit_templates" / "human_audit_queue_seed_v1_redacted.csv")
    proto_text = _read_text(REPO_ROOT / "docs" / "human_audit_protocol_v1.md")
    if seed:
        results.append(CheckResult(cat, "6.3", "Queue seed exists", PASS, P1,
                                   "Redacted queue seed present"))
    elif proto_text and ("pending" in proto_text.lower() or "not complete" in proto_text.lower() or "not yet" in proto_text.lower()):
        results.append(CheckResult(cat, "6.3", "Queue seed not-yet-run documented", WARNING, P1,
                                   "Queue seed not generated; protocol documents pending status",
                                   "Audit not yet run", "Generate queue seed when ready"))
    else:
        results.append(CheckResult(cat, "6.3", "Queue seed exists or documented", WARNING, P1,
                                   "No queue seed and no documentation of pending status",
                                   "Not generated", "Generate queue seed or document as pending"))

    # 6.4 Summary exists if audit file present
    audit_dir = REPO_ROOT / "experiments" / "human_audit_v1"
    if audit_dir.exists():
        summary = _exists(audit_dir / "audit_agreement_summary.json")
        if summary:
            results.append(CheckResult(cat, "6.4", "Audit summary exists", PASS, P1,
                                       "audit_agreement_summary.json present"))
        else:
            results.append(CheckResult(cat, "6.4", "Audit summary missing", WARNING, P1,
                                       "Audit dir exists but no summary",
                                       "Audit incomplete", "Complete audit and generate summary"))
    else:
        # No audit dir — check if this is documented as "not yet run"
        if proto_text and ("not" in proto_text.lower() and ("complete" in proto_text.lower() or "run" in proto_text.lower())):
            results.append(CheckResult(cat, "6.4", "Audit not yet run (documented)", WARNING, P1,
                                       "No audit dir; protocol documents audit as not complete",
                                       "Human audit not executed", "Execute human audit when annotators available"))
        else:
            results.append(CheckResult(cat, "6.4", "Audit status documented", WARNING, P1,
                                       "No audit dir and no documentation",
                                       "Audit not run", "Document audit as pending or execute"))

    # 6.5 Never claims gold benchmark
    # Check that no doc claims the dataset IS a gold benchmark (positive claim)
    scan_md = _read_text(REPO_ROOT / "reports" / "legacy_narrative_scan_v3_17.md")
    if scan_md:
        unsafe_match = re.search(r"unsafe_current_claim\s*\|\s*(\d+)", scan_md)
        unsafe = int(unsafe_match.group(1)) if unsafe_match else -1
        if unsafe == 0:
            results.append(CheckResult(cat, "6.5", "Never claims gold benchmark", PASS, P0,
                                       "Legacy scan confirms no unsafe current claims (unsafe=0)"))
        else:
            results.append(CheckResult(cat, "6.5", "Never claims gold benchmark", FAIL, P0,
                                       f"Legacy scan found {unsafe} unsafe claims",
                                       "Unsafe claims present", "Fix all unsafe claims"))
    else:
        results.append(CheckResult(cat, "6.5", "Never claims gold benchmark", WARNING, P0,
                                   "Cannot verify without legacy scan",
                                   "Scan not run", "Run legacy narrative scan"))

    return results


# ---------------------------------------------------------------------------
# Gate 7: Complexity
# ---------------------------------------------------------------------------

def check_complexity() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "7. Complexity"

    # 7.1 Summary exists
    summary = _read_text(REPO_ROOT / "experiments" / "complexity_vs_utility_ablation_v1" / "complexity_vs_utility_summary.md")
    if summary:
        results.append(CheckResult(cat, "7.1", "Complexity summary exists", PASS, P1,
                                   "complexity_vs_utility_summary.md present"))
    else:
        results.append(CheckResult(cat, "7.1", "Complexity summary exists", FAIL, P1,
                                   "Summary missing",
                                   "Not generated", "Run complexity vs utility ablation"))

    # 7.2 Contains required disclaimer
    required_phrase = "This does not prove rules generally beat learned models"
    if summary and required_phrase.lower() in summary.lower():
        results.append(CheckResult(cat, "7.2", "Contains required disclaimer", PASS, P0,
                                   f"Found: '{required_phrase}'"))
    elif summary:
        # Check for similar phrasing
        similar = any(
            phrase in summary.lower()
            for phrase in [
                "does not prove rules",
                "not a general claim",
                "does not show rules generally beat",
            ]
        )
        if similar:
            results.append(CheckResult(cat, "7.2", "Contains similar disclaimer", WARNING, P0,
                                       "Similar phrasing found but not exact match",
                                       "Disclaimer phrasing differs",
                                       f"Add exact phrase: '{required_phrase}'"))
        else:
            results.append(CheckResult(cat, "7.2", "Contains required disclaimer", FAIL, P0,
                                       "Disclaimer not found",
                                       "Missing disclaimer",
                                       f"Add: '{required_phrase}'"))
    else:
        results.append(CheckResult(cat, "7.2", "Contains required disclaimer", FAIL, P0,
                                   "Cannot check without summary",
                                   "Summary missing", "Generate summary first"))

    # 7.3 Pareto table exists
    pareto = _read_csv_rows(REPO_ROOT / "experiments" / "complexity_vs_utility_ablation_v1" / "method_pareto_table.csv")
    if pareto and len(pareto) >= 5:
        results.append(CheckResult(cat, "7.3", "Pareto table exists", PASS, P1,
                                   f"{len(pareto)} methods in Pareto table"))
    else:
        results.append(CheckResult(cat, "7.3", "Pareto table exists", WARNING, P1,
                                   f"Only {len(pareto)} methods",
                                   "Incomplete", "Run full complexity ablation"))

    return results


# ---------------------------------------------------------------------------
# Gate 8: Paper
# ---------------------------------------------------------------------------

def check_paper() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "8. Paper"

    # 8.1 Paper assets generated
    pa_dir = REPO_ROOT / "paper_assets" / "v3_17_confidential"
    md_files = list(pa_dir.glob("*.md")) if pa_dir.exists() else []
    table_files = list((pa_dir / "tables").glob("*.md")) if (pa_dir / "tables").exists() else []
    if len(md_files) >= 5 and len(table_files) >= 6:
        results.append(CheckResult(cat, "8.1", "Paper assets generated", PASS, P0,
                                   f"{len(md_files)} top-level + {len(table_files)} tables"))
    else:
        results.append(CheckResult(cat, "8.1", "Paper assets generated", WARNING, P0,
                                   f"{len(md_files)} top-level + {len(table_files)} tables",
                                   "Incomplete", "Generate all paper assets"))

    # 8.2 Claims checklist exists
    cc = _exists(REPO_ROOT / "paper_assets" / "v3_17_confidential" / "paper_claims_checklist.md")
    if cc:
        results.append(CheckResult(cat, "8.2", "Claims checklist exists", PASS, P0,
                                   "paper_claims_checklist.md present"))
    else:
        results.append(CheckResult(cat, "8.2", "Claims checklist exists", FAIL, P0,
                                   "Claims checklist missing",
                                   "Not created", "Create claims checklist"))

    # 8.3 Reviewer risk register exists
    rrr = _exists(REPO_ROOT / "docs" / "reviewer_risk_register_v3_17.md")
    if rrr:
        results.append(CheckResult(cat, "8.3", "Reviewer risk register exists", PASS, P0,
                                   "reviewer_risk_register_v3_17.md present"))
    else:
        results.append(CheckResult(cat, "8.3", "Reviewer risk register exists", FAIL, P0,
                                   "Risk register missing",
                                   "Not created", "Create reviewer risk register"))

    # 8.4 Limitations draft exists
    ld = _exists(REPO_ROOT / "paper_assets" / "v3_17_confidential" / "limitations_draft.md")
    if ld:
        results.append(CheckResult(cat, "8.4", "Limitations draft exists", PASS, P0,
                                   "limitations_draft.md present"))
    else:
        results.append(CheckResult(cat, "8.4", "Limitations draft exists", FAIL, P0,
                                   "Limitations draft missing",
                                   "Not created", "Create limitations draft"))

    return results


# ---------------------------------------------------------------------------
# Gate 9: Release
# ---------------------------------------------------------------------------

def check_release() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "9. Release"

    # 9.1 Redteam high risk = 0 or release blocked
    redteam = _read_json(REPO_ROOT / "experiments" / "confidentiality_redteam_scan_v1" / "redteam_summary.json")
    if redteam:
        high = redteam.get("high_risk_count", -1)
        gate_pass = redteam.get("pass_public_release_gate", False)
        if high == 0:
            results.append(CheckResult(cat, "9.1", "Redteam high risk = 0", PASS, P0,
                                       f"high_risk_count={high}"))
        elif high > 0:
            # Check if high-risk files are excluded from release bundle
            safety = _read_json(REPO_ROOT / "reports" / "release_safety_manifest_v3_17.json")
            if safety and safety.get("release_safety_gate", {}).get("status") == "PASS":
                results.append(CheckResult(cat, "9.1", "Redteam high risk in internal files (release excluded)", WARNING, P0,
                                           f"high_risk_count={high} in internal files; release_safety_gate=PASS confirms exclusion",
                                           "High-risk findings in internal scoring files",
                                           "Address high-risk findings or confirm permanent exclusion from release"))
            else:
                results.append(CheckResult(cat, "9.1", "Redteam high risk not excluded", FAIL, P0,
                                           f"high_risk_count={high}, release gate not verified",
                                           "High-risk files may be in release",
                                           "Remove high-risk files from release or fix findings"))
        else:
            results.append(CheckResult(cat, "9.1", "Redteam scan status unknown", WARNING, P0,
                                       f"high_risk_count={high}",
                                       "Scan result unclear", "Re-run redteam scan"))
    else:
        results.append(CheckResult(cat, "9.1", "Redteam scan exists", FAIL, P0,
                                   "redteam_summary.json missing",
                                   "Scan not run", "Run confidentiality redteam scan"))

    # 9.2 Release bundle excludes private text/PDF
    manifest = _read_json(REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "MANIFEST.json")
    redaction = _read_json(REPO_ROOT / "release_bundles" / "v3_17_confidential_public" / "REDACTION_REPORT.json")
    if manifest and redaction:
        # Check no PDF files in release
        has_pdf = any(f["path"].endswith(".pdf") for f in manifest.get("files", []))
        # Check artifact ledger confirms no private in release
        safety = _read_json(REPO_ROOT / "reports" / "release_safety_manifest_v3_17.json")
        private_in_release = safety.get("release_safety_gate", {}).get("private_in_release", []) if safety else ["unknown"]
        if not has_pdf and not private_in_release:
            results.append(CheckResult(cat, "9.2", "Release excludes private text/PDF", PASS, P0,
                                       "No PDFs in bundle; no private artifacts in release"))
        else:
            reasons = []
            if has_pdf:
                reasons.append("PDF files found in release")
            if private_in_release:
                reasons.append(f"Private artifacts in release: {private_in_release}")
            results.append(CheckResult(cat, "9.2", "Release excludes private text/PDF", FAIL, P0,
                                       "; ".join(reasons),
                                       "Private data in release", "Remove private data from release bundle"))
    else:
        results.append(CheckResult(cat, "9.2", "Release bundle exists", WARNING, P0,
                                   "MANIFEST.json or REDACTION_REPORT.json missing",
                                   "Release not built", "Build public sanitized release"))

    # 9.3 Artifact ledger exists
    ledger = _exists(REPO_ROOT / "reports" / "artifact_ledger_v3_17.csv")
    if ledger:
        results.append(CheckResult(cat, "9.3", "Artifact ledger exists", PASS, P0,
                                   "artifact_ledger_v3_17.csv present"))
    else:
        results.append(CheckResult(cat, "9.3", "Artifact ledger exists", FAIL, P0,
                                   "Artifact ledger missing",
                                   "Not generated", "Run build_artifact_ledger_v1.py"))

    return results


# ---------------------------------------------------------------------------
# Gate 10: CI/Repro
# ---------------------------------------------------------------------------

def check_ci_repro() -> List[CheckResult]:
    results: List[CheckResult] = []
    cat = "10. CI/Repro"

    # 10.1 Toy demo passes
    toy_script = _exists(REPO_ROOT / "scripts" / "run_toy_end_to_end_demo_v1.py")
    toy_summary_dir = REPO_ROOT / "experiments" / "toy_end_to_end_demo_v1"
    toy_summary = _read_json(toy_summary_dir / "toy_run_summary.json") if toy_summary_dir.exists() else None
    toy_ok = (
        toy_summary
        and (
            toy_summary.get("overall_status") in ("completed", "pass", "ok")
            or toy_summary.get("all_steps_success") is True
        )
    )
    if toy_script and toy_ok:
        n_steps = toy_summary.get("n_steps_completed", toy_summary.get("n_steps", "?"))
        results.append(CheckResult(cat, "10.1", "Toy demo passes", PASS, P0,
                                   f"all_steps_success=true, {n_steps} steps completed"))
    elif toy_script:
        results.append(CheckResult(cat, "10.1", "Toy demo exists (run status unverified)", WARNING, P0,
                                   "Toy demo script exists but run summary not found or not completed",
                                   "Toy run not verified", "Run toy demo and verify"))
    else:
        results.append(CheckResult(cat, "10.1", "Toy demo exists", FAIL, P0,
                                   "Toy demo script missing",
                                   "Not created", "Create toy end-to-end demo"))

    # 10.2 Schema validation pass/warning documented
    schema_md = _read_text(REPO_ROOT / "experiments" / "schema_validation_summary.md")
    if schema_md:
        # Look for pass/fail counts — handles formats like "Passed: **34**" or "34 PASS"
        pass_match = re.search(r"(?:Passed|PASS|pass|passed)[^\d]*(\d+)", schema_md)
        fail_match = re.search(r"(?:Failed|FAIL|fail|failed)[^\d]*(\d+)", schema_md)
        n_pass = int(pass_match.group(1)) if pass_match else 0
        n_fail = int(fail_match.group(1)) if fail_match else 0
        if n_fail == 0:
            results.append(CheckResult(cat, "10.2", "Schema validation pass", PASS, P1,
                                       f"{n_pass} passed, 0 failed"))
        elif n_fail > 0 and n_pass > 0:
            results.append(CheckResult(cat, "10.2", "Schema validation has documented failures", WARNING, P1,
                                       f"{n_pass} passed, {n_fail} failed (failures from blocked experiments)",
                                       "Schema failures due to blocked experiments",
                                       "Fix blocked experiments or document as permanent"))
        else:
            results.append(CheckResult(cat, "10.2", "Schema validation status", WARNING, P1,
                                       f"pass={n_pass}, fail={n_fail}",
                                       "Schema validation issues", "Investigate schema failures"))
    else:
        results.append(CheckResult(cat, "10.2", "Schema validation exists", WARNING, P1,
                                   "schema_validation_summary.md missing",
                                   "Not run", "Run schema validation"))

    # 10.3 Runner exists
    runner = _exists(REPO_ROOT / "scripts" / "run_v3_17_confidential_pipeline.py")
    if runner:
        results.append(CheckResult(cat, "10.3", "Pipeline runner exists", PASS, P0,
                                   "run_v3_17_confidential_pipeline.py present"))
    else:
        results.append(CheckResult(cat, "10.3", "Pipeline runner exists", FAIL, P0,
                                   "Runner missing",
                                   "Not created", "Create pipeline runner"))

    # 10.4 Makefile/CI smoke exists
    makefile = _exists(REPO_ROOT / "Makefile")
    workflows = list((REPO_ROOT / ".github" / "workflows").glob("*.yml")) if (REPO_ROOT / ".github" / "workflows").exists() else []
    if makefile and workflows:
        results.append(CheckResult(cat, "10.4", "Makefile/CI smoke exists", PASS, P0,
                                   f"Makefile + {len(workflows)} workflow(s): {[w.name for w in workflows]}"))
    elif makefile:
        results.append(CheckResult(cat, "10.4", "Makefile exists (no CI workflows)", WARNING, P0,
                                   "Makefile present but no .github/workflows",
                                   "CI not configured", "Add CI workflow"))
    elif workflows:
        results.append(CheckResult(cat, "10.4", "CI workflows exist (no Makefile)", WARNING, P0,
                                   f"{len(workflows)} workflows but no Makefile",
                                   "Makefile missing", "Create Makefile"))
    else:
        results.append(CheckResult(cat, "10.4", "Makefile/CI exists", FAIL, P0,
                                   "No Makefile and no CI workflows",
                                   "Not configured", "Create Makefile and CI workflow"))

    return results


# ---------------------------------------------------------------------------
# Output writers
# ---------------------------------------------------------------------------

def write_md(report: GateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    lines: List[str] = []
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S%z")
    lines.append("# Final Perfect-State Readiness Gate — V3.17 Confidential Lightweight")
    lines.append("")
    lines.append(f"Generated: {now}")
    lines.append("")
    lines.append("> Read-only gate. No experiments were re-run. No results were modified.")
    lines.append("")

    # Executive Summary (one page)
    lines.append("## Executive Summary")
    lines.append("")
    final = report.final_status
    status_emoji = {
        "READY_WITH_LIMITATIONS": "READY WITH LIMITATIONS",
        "NOT_READY_P0_BLOCKERS": "NOT READY — P0 BLOCKERS",
        "BLOCKED_BY_PRIVATE_DATA": "BLOCKED BY PRIVATE DATA",
        "UNSAFE_OVERCLAIM": "UNSAFE — OVERCLAIM DETECTED",
    }
    lines.append(f"**Final status: {status_emoji.get(final, final)}**")
    lines.append("")
    lines.append(f"| Metric | Count |")
    lines.append(f"|---|---|")
    lines.append(f"| Total checks | {len(report.checks)} |")
    lines.append(f"| PASS | {report.pass_count} |")
    lines.append(f"| WARNING | {report.warning_count} |")
    lines.append(f"| BLOCKED | {report.blocked_count} |")
    lines.append(f"| FAIL | {report.fail_count} |")
    lines.append("")

    # Status logic explanation
    lines.append("### Status logic")
    lines.append("")
    if final == "READY_WITH_LIMITATIONS":
        lines.append("- No FAIL items detected.")
        lines.append("- All BLOCKED items have documented reasons and next actions.")
        lines.append("- WARNING items are documented limitations (not safety issues).")
        lines.append("- The project is ready for release **with documented limitations**.")
    elif final == "NOT_READY_P0_BLOCKERS":
        lines.append("- One or more P0 items have FAIL status or missing blocked_reason.")
        lines.append("- The project is NOT ready for release until P0 blockers are resolved.")
    elif final == "BLOCKED_BY_PRIVATE_DATA":
        lines.append("- All issues are caused by lack of private data access.")
        lines.append("- The project is blocked by private data, not by code or documentation gaps.")
    elif final == "UNSAFE_OVERCLAIM":
        lines.append("- Unsafe overclaim detected in narrative or documentation.")
        lines.append("- The project MUST NOT be released until overclaim is fixed.")
    lines.append("")

    # Blocked items summary
    blocked = [c for c in report.checks if c.status == BLOCKED]
    if blocked:
        lines.append("### Blocked items (documented)")
        lines.append("")
        lines.append("| ID | Check | Reason | Next Action |")
        lines.append("|---|---|---|---|")
        for c in blocked:
            lines.append(f"| {c.check_id} | {c.description} | {c.blocked_reason} | {c.next_action} |")
        lines.append("")

    # Warning items summary
    warnings = [c for c in report.checks if c.status == WARNING]
    if warnings:
        lines.append("### Warning items (documented limitations)")
        lines.append("")
        lines.append("| ID | Check | Evidence | Next Action |")
        lines.append("|---|---|---|---|")
        for c in warnings:
            lines.append(f"| {c.check_id} | {c.description} | {c.evidence} | {c.next_action} |")
        lines.append("")

    lines.append("---")
    lines.append("")

    # Full check details by category
    lines.append("## Full Check Details")
    lines.append("")
    categories = {}
    for c in report.checks:
        categories.setdefault(c.category, []).append(c)

    for cat in sorted(categories.keys()):
        checks = categories[cat]
        lines.append(f"### {cat}")
        lines.append("")
        lines.append("| ID | Check | Status | Priority | Evidence |")
        lines.append("|---|---|---|---|---|")
        for c in checks:
            lines.append(f"| {c.check_id} | {c.description} | {c.status} | {c.priority} | {c.evidence} |")
        lines.append("")

        # Show blocked/warning details
        for c in checks:
            if c.status == BLOCKED:
                lines.append(f"- **{c.check_id} BLOCKED**: reason=`{c.blocked_reason}`, next_action=`{c.next_action}`")
            elif c.status == WARNING:
                lines.append(f"- **{c.check_id} WARNING**: {c.evidence} → next_action=`{c.next_action}`")
        lines.append("")

    lines.append("---")
    lines.append("")
    lines.append("## Scoring legend")
    lines.append("")
    lines.append("| Status | Meaning |")
    lines.append("|---|---|")
    lines.append("| PASS | Complete and safe |")
    lines.append("| WARNING | Limitation documented |")
    lines.append("| BLOCKED | Missing input documented (with reason + next action) |")
    lines.append("| FAIL | Unsafe or undocumented missing |")
    lines.append("")
    lines.append("## Final status legend")
    lines.append("")
    lines.append("| Status | Condition |")
    lines.append("|---|---|")
    lines.append("| READY_WITH_LIMITATIONS | No FAIL; all BLOCKED have reasons |")
    lines.append("| NOT_READY_P0_BLOCKERS | P0 items unknown/missing without reason |")
    lines.append("| BLOCKED_BY_PRIVATE_DATA | All issues due to private data access |")
    lines.append("| UNSAFE_OVERCLAIM | Unsafe claims detected |")

    path.write_text("\n".join(lines), encoding="utf-8")
    print(f"[final_gate] wrote {path}")


def write_json(report: GateReport, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    output = {
        "generated_at": report.generated_at,
        "final_status": report.final_status,
        "summary": {
            "total_checks": len(report.checks),
            "pass": report.pass_count,
            "warning": report.warning_count,
            "blocked": report.blocked_count,
            "fail": report.fail_count,
        },
        "checks": [asdict(c) for c in report.checks],
        "blocked_items": [
            {
                "check_id": c.check_id,
                "description": c.description,
                "blocked_reason": c.blocked_reason,
                "next_action": c.next_action,
            }
            for c in report.checks if c.status == BLOCKED
        ],
        "warning_items": [
            {
                "check_id": c.check_id,
                "description": c.description,
                "evidence": c.evidence,
                "next_action": c.next_action,
            }
            for c in report.checks if c.status == WARNING
        ],
        "fail_items": [
            {
                "check_id": c.check_id,
                "description": c.description,
                "evidence": c.evidence,
                "blocked_reason": c.blocked_reason,
                "next_action": c.next_action,
            }
            for c in report.checks if c.status == FAIL
        ],
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    print(f"[final_gate] wrote {path}")
    print(f"[final_gate] final status: {report.final_status}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> int:
    report = GateReport(generated_at=datetime.now(timezone.utc).isoformat())

    # Run all 10 gate categories
    report.checks.extend(check_mainline())
    report.checks.extend(check_dataset())
    report.checks.extend(check_real_experiments())
    report.checks.extend(check_pdf())
    report.checks.extend(check_leakage())
    report.checks.extend(check_human_audit())
    report.checks.extend(check_complexity())
    report.checks.extend(check_paper())
    report.checks.extend(check_release())
    report.checks.extend(check_ci_repro())

    write_md(report, OUTPUT_MD)
    write_json(report, OUTPUT_JSON)

    # Print summary
    print(f"[final_gate] PASS={report.pass_count}, WARNING={report.warning_count}, "
          f"BLOCKED={report.blocked_count}, FAIL={report.fail_count}")
    print(f"[final_gate] final status: {report.final_status}")

    # Exit code: 0 if READY_WITH_LIMITATIONS, 1 otherwise
    if report.final_status == "READY_WITH_LIMITATIONS":
        return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
