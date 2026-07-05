#!/usr/bin/env python
"""run_leakage_audit_v1.py — Leakage audit for V3.17 pipeline.

7 checks:
1. claim-only baseline — is claim_text alone too predictive?
2. title-only retrieval — is title alone too strong for retrieval?
3. metadata-only retrieval — is metadata alone too strong?
4. label lexical cues — do labels have obvious lexical patterns?
5. group split integrity — do groups cross train/test?
6. selector oracle check — does selector read oracle_hit/true_label?
7. queue forbidden fields check — does SmartQueue read forbidden fields?

Hard boundaries: no network, no API, no training, no data modification.
"""

import argparse
import csv
import json
import re
import sys
from collections import Counter, defaultdict
from pathlib import Path

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402

FORBIDDEN_SELECTOR_FIELDS = {
    "true_label", "candidate_label_guess", "gold_label", "human_audited",
    "oracle_hit", "final_label",
}

FORBIDDEN_QUEUE_FIELDS = {
    "true_label", "is_strong_action", "oracle_hit",
    "candidate_label_guess", "final_label", "gold_label",
    "human_audited", "evidence_text", "evidence_text_sha256",
}

_TOKEN_RE = re.compile(r"[a-z0-9]+")
_STOP = {"a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were", "be"}


def log(msg):
    print(msg, flush=True)


def tokenize(text):
    return [w for w in _TOKEN_RE.findall(text.lower()) if w not in _STOP]


# ---------------------------------------------------------------------------
# Check 1: claim-only baseline
# ---------------------------------------------------------------------------

def check_claim_only_baseline(candidates, true_labels):
    """Check if claim_text alone is too predictive of the label.

    Method: compute claim_text token overlap between candidates with the
    same label vs different labels. If same-label overlap is much higher,
    claim_text may contain label leaks.
    """
    log("  [Check 1] Claim-only baseline ...")
    by_label = defaultdict(list)
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if lab:
            by_label[lab].append(tokenize(c["claim_text"]))

    if len(by_label) < 2:
        return {"status": "skip", "reason": "fewer than 2 labels", "same_label_overlap": 0, "cross_label_overlap": 0}

    # Same-label average overlap
    same_overlaps = []
    for lab, token_lists in by_label.items():
        for i in range(len(token_lists)):
            for j in range(i + 1, len(token_lists)):
                s1, s2 = set(token_lists[i]), set(token_lists[j])
                if s1 and s2:
                    same_overlaps.append(len(s1 & s2) / len(s1 | s2))

    # Cross-label average overlap
    cross_overlaps = []
    labels = list(by_label.keys())
    for li in range(len(labels)):
        for lj in range(li + 1, len(labels)):
            for t1 in by_label[labels[li]]:
                for t2 in by_label[labels[lj]]:
                    s1, s2 = set(t1), set(t2)
                    if s1 and s2:
                        cross_overlaps.append(len(s1 & s2) / len(s1 | s2))

    same_avg = sum(same_overlaps) / len(same_overlaps) if same_overlaps else 0
    cross_avg = sum(cross_overlaps) / len(cross_overlaps) if cross_overlaps else 0
    ratio = same_avg / cross_avg if cross_avg > 1e-10 else 0

    status = "pass" if ratio < 2.0 else "warning"
    if ratio >= 3.0:
        status = "fail"

    return {
        "status": status,
        "same_label_overlap": round(same_avg, 6),
        "cross_label_overlap": round(cross_avg, 6),
        "ratio": round(ratio, 6),
        "threshold_warning": 2.0,
        "threshold_fail": 3.0,
    }


# ---------------------------------------------------------------------------
# Check 2: title-only retrieval
# ---------------------------------------------------------------------------

def check_title_only_retrieval(candidates):
    """Check if title alone retrieves evidence too well.

    Method: compute token overlap between title and evidence_text.
    If very high, title may leak evidence content.
    """
    log("  [Check 2] Title-only retrieval ...")
    overlaps = []
    for c in candidates:
        title = c.get("title", "") or c.get("pdf_filename", "").replace(".pdf", "")
        evidence = c.get("evidence_text", "")
        if title and evidence:
            t1, t2 = set(tokenize(title)), set(tokenize(evidence))
            if t1 and t2:
                overlaps.append(len(t1 & t2) / len(t1 | t2))

    if not overlaps:
        return {"status": "skip", "reason": "no title/evidence pairs", "mean_overlap": 0}

    mean_ov = sum(overlaps) / len(overlaps)
    status = "pass" if mean_ov < 0.3 else "warning"
    if mean_ov >= 0.5:
        status = "fail"

    return {
        "status": status,
        "mean_overlap": round(mean_ov, 6),
        "max_overlap": round(max(overlaps), 6),
        "threshold_warning": 0.3,
        "threshold_fail": 0.5,
    }


# ---------------------------------------------------------------------------
# Check 3: metadata-only retrieval
# ---------------------------------------------------------------------------

def check_metadata_only_retrieval(candidates):
    """Check if metadata (page_number, pdf_filename) alone is too predictive.

    Method: check if candidates from the same page tend to have the same label.
    If so, page metadata may leak the label.
    """
    log("  [Check 3] Metadata-only retrieval ...")
    by_page = defaultdict(list)
    for c in candidates:
        key = (c.get("pdf_filename", ""), c.get("page_number", 0))
        lab = c.get("_true_label", "")
        if lab:
            by_page[key].append(lab)

    if not by_page:
        return {"status": "skip", "reason": "no page metadata", "mean_page_purity": 0}

    purities = []
    for key, labels in by_page.items():
        if len(labels) > 1:
            most_common = Counter(labels).most_common(1)[0][1]
            purities.append(most_common / len(labels))

    if not purities:
        return {"status": "pass", "reason": "no multi-candidate pages", "mean_page_purity": 0}

    mean_purity = sum(purities) / len(purities)
    status = "pass" if mean_purity < 0.7 else "warning"
    if mean_purity >= 0.9:
        status = "fail"

    return {
        "status": status,
        "mean_page_purity": round(mean_purity, 6),
        "n_multi_candidate_pages": len(purities),
        "threshold_warning": 0.7,
        "threshold_fail": 0.9,
    }


# ---------------------------------------------------------------------------
# Check 4: label lexical cues
# ---------------------------------------------------------------------------

def check_label_lexical_cues(candidates, true_labels):
    """Check if labels have obvious lexical patterns in claim_text.

    Method: for each label, find tokens that appear much more frequently
    in that label's claims vs other labels.
    """
    log("  [Check 4] Label lexical cues ...")
    by_label = defaultdict(list)
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if lab:
            by_label[lab].append(tokenize(c["claim_text"]))

    if len(by_label) < 2:
        return {"status": "skip", "reason": "fewer than 2 labels", "top_cues": {}}

    # Count token frequencies per label
    label_token_counts = {}
    for lab, token_lists in by_label.items():
        counts = Counter()
        for tokens in token_lists:
            counts.update(tokens)
        label_token_counts[lab] = counts

    # Find overrepresented tokens per label
    top_cues = {}
    for lab in by_label:
        lab_count = label_token_counts[lab]
        other_count = Counter()
        for other_lab in by_label:
            if other_lab != lab:
                other_count += label_token_counts[other_lab]
        n_lab = sum(len(tl) for tl in by_label[lab])
        n_other = sum(len(tl) for tl in by_label[other_lab] for other_lab in by_label if other_lab != lab)
        cues = []
        for token, count in lab_count.most_common(20):
            other = other_count.get(token, 0)
            if count < 2:
                continue
            lab_rate = count / max(n_lab, 1)
            other_rate = other / max(n_other, 1)
            if other_rate < 1e-10 and lab_rate > 0.01:
                cues.append({"token": token, "lab_count": count, "other_count": other, "lab_rate": round(lab_rate, 4)})
            elif lab_rate / other_rate > 5 and lab_rate > 0.05:
                cues.append({"token": token, "lab_count": count, "other_count": other, "ratio": round(lab_rate / other_rate, 2)})
        top_cues[lab] = cues[:5]

    # Status: fail if any label has strong cues
    max_cues = max(len(v) for v in top_cues.values()) if top_cues else 0
    status = "pass" if max_cues <= 2 else "warning"
    if max_cues >= 5:
        status = "fail"

    return {"status": status, "top_cues": top_cues, "max_cues_per_label": max_cues}


# ---------------------------------------------------------------------------
# Check 5: group split integrity
# ---------------------------------------------------------------------------

def check_group_split_integrity(candidates):
    """Check if same target_candidate_group_id crosses train/test splits."""
    log("  [Check 5] Group split integrity ...")
    group_splits = defaultdict(set)
    for c in candidates:
        gid = c.get("target_candidate_group_id", "")
        role = c.get("dataset_role", "") or c.get("split", "")
        if gid and role:
            group_splits[gid].add(role)

    if not group_splits:
        return {"status": "skip", "reason": "no split info available", "cross_split_groups": 0}

    cross = {gid: list(splits) for gid, splits in group_splits.items() if len(splits) > 1}
    status = "pass" if not cross else "fail"

    return {
        "status": status,
        "n_groups": len(group_splits),
        "n_cross_split_groups": len(cross),
        "cross_split_groups": cross if cross else {},
    }


# ---------------------------------------------------------------------------
# Check 6: selector oracle check
# ---------------------------------------------------------------------------

def check_no_oracle_in_selector(canonicalizer_guard_path):
    """Verify selector doesn't read oracle_hit/true_label."""
    log("  [Check 6] No oracle in selector ...")
    if not canonicalizer_guard_path or not Path(canonicalizer_guard_path).exists():
        return {"status": "skip", "reason": "guard report not found", "path": str(canonicalizer_guard_path)}

    with open(canonicalizer_guard_path, "r", encoding="utf-8") as f:
        guard = json.load(f)

    oracle_used = guard.get("oracle_used_for_selection", True)
    labels_used = guard.get("labels_used_for_selection", True)

    status = "pass" if (not oracle_used and not labels_used) else "fail"

    return {
        "status": status,
        "oracle_used_for_selection": oracle_used,
        "labels_used_for_selection": labels_used,
        "forbidden_fields": guard.get("forbidden_fields_for_selection", []),
        "path": str(canonicalizer_guard_path),
    }


# ---------------------------------------------------------------------------
# Check 7: queue forbidden fields check
# ---------------------------------------------------------------------------

def check_no_label_in_queue_sorting(queue_guard_path):
    """Verify SmartQueue doesn't sort by forbidden fields."""
    log("  [Check 7] No label in queue sorting ...")
    if not queue_guard_path or not Path(queue_guard_path).exists():
        return {"status": "skip", "reason": "guard report not found", "path": str(queue_guard_path)}

    with open(queue_guard_path, "r", encoding="utf-8") as f:
        guard = json.load(f)

    true_label_sort = guard.get("true_label_used_for_sorting", True)
    oracle_sort = guard.get("oracle_hit_used_for_sorting", True)
    evidence_sort = guard.get("evidence_text_used_for_sorting", True)

    status = "pass" if (not true_label_sort and not oracle_sort and not evidence_sort) else "fail"

    return {
        "status": status,
        "true_label_used_for_sorting": true_label_sort,
        "oracle_hit_used_for_sorting": oracle_sort,
        "evidence_text_used_for_sorting": evidence_sort,
        "allowed_sort_fields": guard.get("allowed_sort_fields", []),
        "forbidden_sort_fields": guard.get("forbidden_sort_fields", []),
        "path": str(queue_guard_path),
    }


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates_with_labels(csv_path):
    """Load candidate CSV with labels for audit."""
    candidates = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rec = {
                "candidate_id": row.get("candidate_id", ""),
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "claim_text": row.get("claim_text", ""),
                "title": row.get("title", "") or row.get("pdf_filename", "").replace(".pdf", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row["page_number"]) if str(row.get("page_number", "")).isdigit() else 0,
                "evidence_text": row.get("evidence_text", ""),
                "dataset_role": row.get("dataset_role", "") or row.get("split", ""),
                "_true_label": row.get("true_label", "") or row.get("final_label", "") or row.get("gold_label", ""),
            }
            candidates.append(rec)
    return candidates


def load_toy_candidates_with_mock_labels(csv_path):
    """Load toy candidates with synthetic labels for audit testing."""
    candidates = []
    toy_labels = ["supported", "strong_action_overclaim", "strong_action_overclaim",
                  "mild_scope_overclaim", "supported", "contradiction_candidate"]
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for i, row in enumerate(reader):
            rec = {
                "candidate_id": row.get("candidate_id", ""),
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "claim_text": row.get("claim_text", ""),
                "title": row.get("pdf_filename", "").replace(".pdf", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row["page_number"]) if str(row.get("page_number", "")).isdigit() else 0,
                "evidence_text": row.get("evidence_text", ""),
                "dataset_role": "test",
                "_true_label": toy_labels[i] if i < len(toy_labels) else "supported",
            }
            candidates.append(rec)
    return candidates


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_lexical_csv(filepath, lexical_result):
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["label", "token", "lab_count", "other_count", "ratio_or_rate"])
        for lab, cues in lexical_result.get("top_cues", {}).items():
            for cue in cues:
                ratio = cue.get("ratio", cue.get("lab_rate", 0))
                writer.writerow([lab, cue["token"], cue["lab_count"], cue["other_count"], ratio])


def write_audit_summary(filepath, results):
    lines = [
        "# Leakage Audit Summary",
        "",
        f"Generated: {results.get('timestamp', '')}",
        "",
        "## Check Results",
        "",
        "| # | Check | Status | Key Metric |",
        "|---|-------|--------|------------|",
    ]
    checks = [
        ("1", "Claim-only baseline", results.get("claim_only", {})),
        ("2", "Title-only retrieval", results.get("title_only", {})),
        ("3", "Metadata-only retrieval", results.get("metadata_only", {})),
        ("4", "Label lexical cues", results.get("lexical_cues", {})),
        ("5", "Group split integrity", results.get("group_split", {})),
        ("6", "No oracle in selector", results.get("selector_oracle", {})),
        ("7", "No label in queue sorting", results.get("queue_forbidden", {})),
    ]
    for num, name, res in checks:
        status = res.get("status", "skip")
        metric = ""
        if "ratio" in res:
            metric = f"ratio={res['ratio']}"
        elif "mean_overlap" in res:
            metric = f"mean_overlap={res['mean_overlap']}"
        elif "mean_page_purity" in res:
            metric = f"purity={res['mean_page_purity']}"
        elif "max_cues_per_label" in res:
            metric = f"max_cues={res['max_cues_per_label']}"
        elif "n_cross_split_groups" in res:
            metric = f"cross_groups={res['n_cross_split_groups']}"
        lines.append(f"| {num} | {name} | {status} | {metric} |")

    lines.extend([
        "",
        "## Forbidden Fields (selector)",
        "",
        "- " + "\n- ".join(sorted(FORBIDDEN_SELECTOR_FIELDS)) if FORBIDDEN_SELECTOR_FIELDS else "- (none)",
        "",
        "## Forbidden Fields (queue sorting)",
        "",
        "- " + "\n- ".join(sorted(FORBIDDEN_QUEUE_FIELDS)) if FORBIDDEN_QUEUE_FIELDS else "- (none)",
        "",
    ])
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Leakage audit for V3.17 pipeline.")
    parser.add_argument("--candidate_csv", default=None)
    parser.add_argument("--canonicalizer_guard", default=None)
    parser.add_argument("--queue_guard", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    # --- Load config ---
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    output_dir = Path(args.output_dir) if args.output_dir else resolve_path(config, "leakage_audit_dir")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        candidate_csv = "data/toy_synthetic/toy_candidates_v1.csv"
        canonicalizer_guard = "experiments/canonicalizer_ablation_v1_toy/leakage_guard_report.json"
        queue_guard = "experiments/lightweight_smart_queue_v1_toy/leakage_guard_report.json"
        print("[toy_mode] Using toy inputs")
    else:
        candidate_csv = args.candidate_csv or str(resolve_path(config, "candidate_csv") or "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv")
        canon_dir = resolve_path(config, "canonicalizer_dir") or Path("experiments/canonicalizer_ablation_v1")
        queue_dir = resolve_path(config, "smart_queue_dir") or Path("experiments/lightweight_smart_queue_v1")
        canonicalizer_guard = args.canonicalizer_guard or str(canon_dir / "leakage_guard_report.json")
        queue_guard = args.queue_guard or str(queue_dir / "leakage_guard_report.json")

    # --- Load data ---
    print(f"Loading candidates from {candidate_csv}")
    if args.toy_mode:
        candidates = load_toy_candidates_with_mock_labels(candidate_csv)
    else:
        candidates = load_candidates_with_labels(candidate_csv)
    print(f"  {len(candidates)} candidates loaded")

    true_labels = {c["candidate_id"]: c["_true_label"] for c in candidates if c["_true_label"]}
    print(f"  {len(true_labels)} true_labels for audit")

    # --- Run 7 checks ---
    print("\nRunning 7 leakage checks ...")
    from datetime import datetime, timezone
    timestamp = datetime.now(timezone.utc).isoformat()

    claim_only = check_claim_only_baseline(candidates, true_labels)
    title_only = check_title_only_retrieval(candidates)
    metadata_only = check_metadata_only_retrieval(candidates)
    lexical_cues = check_label_lexical_cues(candidates, true_labels)
    group_split = check_group_split_integrity(candidates)
    selector_oracle = check_no_oracle_in_selector(canonicalizer_guard)
    queue_forbidden = check_no_label_in_queue_sorting(queue_guard)

    # --- Write outputs ---
    write_json(output_dir / "claim_only_baseline.json", claim_only)
    write_json(output_dir / "title_only_retrieval_baseline.json", title_only)
    write_json(output_dir / "metadata_only_retrieval_baseline.json", metadata_only)
    write_lexical_csv(output_dir / "lexical_overlap_by_label.csv", lexical_cues)
    write_json(output_dir / "group_split_integrity.json", group_split)
    write_json(output_dir / "no_oracle_in_selector_check.json", selector_oracle)
    write_json(output_dir / "no_label_in_queue_sorting_check.json", queue_forbidden)

    all_results = {
        "timestamp": timestamp,
        "claim_only": claim_only,
        "title_only": title_only,
        "metadata_only": metadata_only,
        "lexical_cues": lexical_cues,
        "group_split": group_split,
        "selector_oracle": selector_oracle,
        "queue_forbidden": queue_forbidden,
    }
    write_audit_summary(output_dir / "audit_summary.md", all_results)

    print(f"\nWrote 8 files to {output_dir}")
    print("\nCheck summary:")
    for name, res in [("claim_only", claim_only), ("title_only", title_only),
                       ("metadata_only", metadata_only), ("lexical_cues", lexical_cues),
                       ("group_split", group_split), ("selector_oracle", selector_oracle),
                       ("queue_forbidden", queue_forbidden)]:
        print(f"  {name}: {res.get('status', 'skip')}")
    write_run_config(output_dir, config, "run_leakage_audit_v1.py",
                     extra={"toy_mode": args.toy_mode})
    print("Wrote run_config.json")
    print("Done.")


if __name__ == "__main__":
    main()
