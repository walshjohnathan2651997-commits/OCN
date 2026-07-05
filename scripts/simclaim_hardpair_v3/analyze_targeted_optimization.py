import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
DATA_CSV = ROOT / "data" / "simclaim_hardpair_v3" / "candidates" / "simclaim_hardpair_v3_268.csv"
TEST_CSV = ROOT / "data" / "simclaim_hardpair_v3" / "splits_group_stratified" / "test.csv"
TRAD_PRED = ROOT / "experiments" / "simclaim_hardpair_v3_small_baselines" / "predictions" / "hardpair_v3_small_data_baseline_predictions.csv"
TRAD_METRICS = ROOT / "experiments" / "simclaim_hardpair_v3_small_baselines" / "metrics" / "hardpair_v3_small_data_baseline_metrics.csv"
LLM_PRED = ROOT / "experiments" / "simclaim_hardpair_v3_llm_small_eval" / "predictions" / "hardpair_v3_llm_small_eval_predictions.csv"
LLM_METRICS = ROOT / "experiments" / "simclaim_hardpair_v3_llm_small_eval" / "metrics" / "hardpair_v3_llm_small_eval_metrics.csv"

AUDIT_DIR = ROOT / "data" / "simclaim_hardpair_v3" / "audit"
REPORT_DIR = ROOT / "reports" / "simclaim_hardpair_v3_targeted"
REPAIR_QUEUE = AUDIT_DIR / "v3_targeted_repair_queue.csv"
GROUP_AUDIT = AUDIT_DIR / "v3_targeted_group_risk_audit.csv"
TERM_AUDIT = AUDIT_DIR / "v3_claim_only_leakage_terms.csv"
ERROR_AUDIT = AUDIT_DIR / "v3_model_error_pattern_audit.csv"
SUMMARY_JSON = REPORT_DIR / "v3_targeted_optimization_summary.json"
REPORT_MD = REPORT_DIR / "v3_targeted_optimization_plan.md"

TARGETS = ["issue_binary_label_guess", "escalation_binary_label_guess", "candidate_label_guess"]
LABEL_COL = "candidate_label_guess"
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_-]+")


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for k in row:
                if k not in seen:
                    fieldnames.append(k)
                    seen.add(k)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def normalize(text):
    return re.sub(r"\s+", " ", text or "").strip()


def tokens(text):
    return TOKEN_RE.findall((text or "").lower())


def ngrams(tok):
    out = []
    out.extend(tok)
    out.extend([tok[i] + " " + tok[i + 1] for i in range(len(tok) - 1)])
    return out


def best_metric(metrics, target, view=None, model=None):
    sub = [r for r in metrics if r.get("split") == "test" and r.get("target") == target]
    if view is not None:
        sub = [r for r in sub if r.get("text_view") == view]
    if model is not None:
        sub = [r for r in sub if r.get("model") == model]
    return max(sub, key=lambda r: float(r["macro_f1"])) if sub else None


def pred_index(rows):
    idx = {}
    for r in rows:
        key = (r.get("candidate_id"), r.get("target"), r.get("model") or "llm", r.get("text_view") or r.get("setting"))
        idx[key] = r
    return idx


def llm_index(rows):
    idx = {}
    for r in rows:
        key = (r.get("candidate_id"), r.get("target"), r.get("setting"))
        idx[key] = r
    return idx


def term_leakage_rows(data_rows):
    test_ids = {r["candidate_id"] for r in read_csv(TEST_CSV)}
    rows = [r for r in data_rows if r["candidate_id"] in test_ids]
    by_target = []
    for target in TARGETS:
        labels = sorted(set(r[target] for r in rows))
        if len(labels) < 2:
            continue
        label_counts = Counter(r[target] for r in rows)
        term_label_counts = defaultdict(Counter)
        term_doc_counts = Counter()
        for r in rows:
            terms = set(ngrams(tokens(r["claim_text"])))
            term_doc_counts.update(terms)
            for term in terms:
                term_label_counts[term][r[target]] += 1
        for term, counts in term_label_counts.items():
            if term_doc_counts[term] < 2:
                continue
            top_label, top_count = counts.most_common(1)[0]
            purity = top_count / term_doc_counts[term]
            baseline = label_counts[top_label] / len(rows)
            lift = purity - baseline
            if lift <= 0.2:
                continue
            by_target.append({
                "target": target,
                "term": term,
                "doc_count": term_doc_counts[term],
                "top_label": top_label,
                "top_label_count": top_count,
                "purity": f"{purity:.6f}",
                "baseline_label_rate": f"{baseline:.6f}",
                "lift_over_baseline": f"{lift:.6f}",
            })
    by_target.sort(key=lambda r: (-float(r["lift_over_baseline"]), -int(r["doc_count"]), r["target"], r["term"]))
    return by_target


def build_error_audit(data_rows, trad_preds, llm_preds):
    by_id = {r["candidate_id"]: r for r in data_rows}
    test_ids = {r["candidate_id"] for r in read_csv(TEST_CSV)}
    trad_idx = pred_index(trad_preds)
    llm_idx = llm_index(llm_preds)
    rows = []

    for cid in sorted(test_ids):
        item = by_id[cid]
        for target in TARGETS:
            claim_only_correct = []
            ce_correct = []
            evidence_only_correct = []
            for model in ["tfidf_centroid", "multinomial_nb"]:
                for view, bucket in [("claim_only", claim_only_correct), ("claim_evidence", ce_correct), ("evidence_only", evidence_only_correct)]:
                    p = trad_idx.get((cid, target, model, view))
                    if p:
                        bucket.append(p.get("correct") == "true")
            for setting, bucket in [("claim_only", claim_only_correct), ("claim_evidence", ce_correct), ("evidence_only", evidence_only_correct)]:
                p = llm_idx.get((cid, target, setting))
                if p:
                    bucket.append(p.get("correct") == "true")

            llm_claim = llm_idx.get((cid, target, "claim_only"))
            llm_ce = llm_idx.get((cid, target, "claim_evidence"))
            llm_ev = llm_idx.get((cid, target, "evidence_only"))
            pattern = []
            if llm_claim and llm_ce:
                if llm_claim.get("correct") == "true" and llm_ce.get("correct") != "true":
                    pattern.append("llm_claim_only_correct_ce_wrong")
                if llm_claim.get("correct") != "true" and llm_ce.get("correct") == "true":
                    pattern.append("llm_evidence_helped")
            if sum(claim_only_correct) >= 2 and sum(ce_correct) <= 1:
                pattern.append("local_claim_only_advantage")
            if sum(evidence_only_correct) >= 2:
                pattern.append("evidence_only_prior_risk")
            rows.append({
                "candidate_id": cid,
                "hardpair_group_id": item.get("hardpair_group_id", ""),
                "target": target,
                "true_label": item.get(target, ""),
                "candidate_label_guess": item.get(LABEL_COL, ""),
                "llm_claim_only_pred": llm_claim.get("pred_label", "") if llm_claim else "",
                "llm_claim_only_correct": llm_claim.get("correct", "") if llm_claim else "",
                "llm_claim_evidence_pred": llm_ce.get("pred_label", "") if llm_ce else "",
                "llm_claim_evidence_correct": llm_ce.get("correct", "") if llm_ce else "",
                "llm_evidence_only_pred": llm_ev.get("pred_label", "") if llm_ev else "",
                "llm_evidence_only_correct": llm_ev.get("correct", "") if llm_ev else "",
                "n_claim_only_correct_signals": sum(claim_only_correct),
                "n_claim_evidence_correct_signals": sum(ce_correct),
                "n_evidence_only_correct_signals": sum(evidence_only_correct),
                "error_pattern": ";".join(pattern),
                "claim_text": item.get("claim_text", ""),
                "evidence_text_original_locked": item.get("evidence_text_original_locked", ""),
                "source_location": item.get("source_location", ""),
                "source_url": item.get("source_url", ""),
            })
    return rows


def repair_priority(row):
    score = 0
    target = row["target"]
    if target in {"escalation_binary_label_guess", "candidate_label_guess"}:
        score += 2
    if "llm_claim_only_correct_ce_wrong" in row["error_pattern"]:
        score += 4
    if "local_claim_only_advantage" in row["error_pattern"]:
        score += 3
    if row["n_claim_only_correct_signals"] and row["n_claim_evidence_correct_signals"]:
        try:
            score += max(0, int(row["n_claim_only_correct_signals"]) - int(row["n_claim_evidence_correct_signals"]))
        except Exception:
            pass
    return score


def build_repair_queue(error_rows, term_rows):
    risky_terms_by_target = defaultdict(list)
    for r in term_rows[:300]:
        risky_terms_by_target[r["target"]].append(r["term"])

    queue = []
    for r in error_rows:
        score = repair_priority(r)
        if score <= 0:
            continue
        terms = [t for t in risky_terms_by_target[r["target"]] if t in r["claim_text"].lower()]
        action = "review_only"
        if "llm_claim_only_correct_ce_wrong" in r["error_pattern"]:
            action = "rewrite_claim_to_force_evidence_comparison"
        elif "local_claim_only_advantage" in r["error_pattern"]:
            action = "reduce_claim_only_surface_cues"
        queue.append({
            "priority_score": score,
            "recommended_action": action,
            "candidate_id": r["candidate_id"],
            "hardpair_group_id": r["hardpair_group_id"],
            "target": r["target"],
            "true_label": r["true_label"],
            "candidate_label_guess": r["candidate_label_guess"],
            "error_pattern": r["error_pattern"],
            "risk_terms_in_claim": "; ".join(terms[:12]),
            "claim_text": r["claim_text"],
            "evidence_text_original_locked": r["evidence_text_original_locked"],
            "source_location": r["source_location"],
            "source_url": r["source_url"],
            "repair_rule": repair_rule_for(r["target"], r["candidate_label_guess"], r["error_pattern"]),
        })
    queue.sort(key=lambda r: (-int(r["priority_score"]), r["target"], r["candidate_id"]))
    return queue


def repair_rule_for(target, label, pattern):
    if target == "escalation_binary_label_guess":
        return (
            "Keep evidence locked. Rewrite only this group's four claims so escalation/non-escalation share similar applied/evaluation vocabulary; "
            "make escalation depend on whether the claim adds unsupported scope/action, not obvious words."
        )
    if target == "candidate_label_guess":
        return (
            "Keep evidence locked. Make the four class labels less separable by style; supported and contradiction should not be short/plain while mild/strong are broad/action-heavy."
        )
    return (
        "Keep evidence locked. Reduce claim-only cues while preserving the claim-evidence relation."
    )


def group_risk(queue):
    counts = defaultdict(lambda: {
        "hardpair_group_id": "",
        "n_flagged_rows": 0,
        "max_priority_score": 0,
        "targets": set(),
        "labels": set(),
        "candidate_ids": [],
    })
    for r in queue:
        g = counts[r["hardpair_group_id"]]
        g["hardpair_group_id"] = r["hardpair_group_id"]
        g["n_flagged_rows"] += 1
        g["max_priority_score"] = max(g["max_priority_score"], int(r["priority_score"]))
        g["targets"].add(r["target"])
        g["labels"].add(r["candidate_label_guess"])
        g["candidate_ids"].append(r["candidate_id"])
    rows = []
    for g in counts.values():
        rows.append({
            "hardpair_group_id": g["hardpair_group_id"],
            "n_flagged_rows": g["n_flagged_rows"],
            "max_priority_score": g["max_priority_score"],
            "targets": ";".join(sorted(g["targets"])),
            "labels": ";".join(sorted(g["labels"])),
            "candidate_ids": ";".join(g["candidate_ids"]),
        })
    rows.sort(key=lambda r: (-r["max_priority_score"], -r["n_flagged_rows"], r["hardpair_group_id"]))
    return rows


def main():
    AUDIT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)

    data_rows = read_csv(DATA_CSV)
    trad_preds = read_csv(TRAD_PRED)
    llm_preds = read_csv(LLM_PRED)
    trad_metrics = read_csv(TRAD_METRICS)
    llm_metrics = read_csv(LLM_METRICS)

    terms = term_leakage_rows(data_rows)
    errors = build_error_audit(data_rows, trad_preds, llm_preds)
    queue = build_repair_queue(errors, terms)
    groups = group_risk(queue)

    write_csv(TERM_AUDIT, terms)
    write_csv(ERROR_AUDIT, errors)
    write_csv(REPAIR_QUEUE, queue)
    write_csv(GROUP_AUDIT, groups)

    summary = {
        "dataset": "simclaim_hardpair_v3_268",
        "no_new_llm_calls": True,
        "n_rows": len(data_rows),
        "n_test_error_audit_rows": len(errors),
        "n_repair_queue_rows": len(queue),
        "n_high_priority_rows_score_ge_6": sum(1 for r in queue if int(r["priority_score"]) >= 6),
        "n_flagged_groups": len(groups),
        "top_flagged_groups": groups[:10],
        "current_best_dataset": str(DATA_CSV),
        "outputs": {
            "repair_queue_csv": str(REPAIR_QUEUE),
            "group_risk_audit_csv": str(GROUP_AUDIT),
            "claim_only_leakage_terms_csv": str(TERM_AUDIT),
            "model_error_pattern_audit_csv": str(ERROR_AUDIT),
            "report_md": str(REPORT_MD),
        },
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, trad_metrics, llm_metrics, terms, queue, groups)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


def write_report(summary, trad_metrics, llm_metrics, terms, queue, groups):
    lines = []
    lines.append("# v3 targeted optimization plan")
    lines.append("")
    lines.append("No new LLM calls were made. This report only analyzes existing v3 data, traditional predictions, and previous LLM predictions.")
    lines.append("")
    lines.append("## Decision")
    lines.append("")
    lines.append("Keep v3 as the current best pilot. Do not do another full-batch rewrite. The next optimization should be a targeted repair pass on flagged groups only.")
    lines.append("")
    lines.append("## Repair queue")
    lines.append("")
    lines.append(f"- Flagged rows: {summary['n_repair_queue_rows']}")
    lines.append(f"- High-priority rows, score >= 6: {summary['n_high_priority_rows_score_ge_6']}")
    lines.append(f"- Flagged groups: {summary['n_flagged_groups']}")
    lines.append("")
    lines.append("## Top risky groups")
    lines.append("")
    lines.append("| group | flagged rows | max priority | targets | labels |")
    lines.append("|---|---:|---:|---|---|")
    for g in groups[:12]:
        lines.append(f"| {g['hardpair_group_id']} | {g['n_flagged_rows']} | {g['max_priority_score']} | {g['targets']} | {g['labels']} |")
    lines.append("")
    lines.append("## Top claim-only leakage terms")
    lines.append("")
    lines.append("| target | term | top label | count | lift |")
    lines.append("|---|---|---|---:|---:|")
    for t in terms[:20]:
        lines.append(f"| {t['target']} | {t['term']} | {t['top_label']} | {t['doc_count']} | {t['lift_over_baseline']} |")
    lines.append("")
    lines.append("## Next action")
    lines.append("")
    lines.append("Run a targeted v3-repair pass only on the top flagged groups, not all 67 groups. Keep the locked evidence and source fields unchanged. The repair prompt should be group-level and should preserve labels while reducing the specific claim-only terms listed in the repair queue.")
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for k, v in summary["outputs"].items():
        lines.append(f"- {k}: `{v}`")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    main()
