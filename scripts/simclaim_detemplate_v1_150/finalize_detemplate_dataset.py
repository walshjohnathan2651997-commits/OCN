import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
SOURCE_SPLITS = ROOT / "data" / "simclaim_mvp_expansion_v1_150" / "splits"
DATA_ROOT = ROOT / "data" / "simclaim_detemplate_v1_150"
CANDIDATE_CSV = DATA_ROOT / "candidates" / "simclaim_detemplate_candidates_150.csv"
CANDIDATE_JSONL = DATA_ROOT / "candidates" / "simclaim_detemplate_candidates_150.jsonl"
SPLITS_ORIGINAL = DATA_ROOT / "splits"
SPLITS_STRATIFIED = DATA_ROOT / "splits_group_stratified"
AUDIT_ROOT = DATA_ROOT / "audit"
REPORT_ROOT = ROOT / "reports" / "simclaim_detemplate_v1_150"

QUALITY_AUDIT = AUDIT_ROOT / "detemplate_quality_audit.csv"
SPLIT_AUDIT = AUDIT_ROOT / "detemplate_split_distribution_audit.csv"
PREFIX_ORIGINAL = REPORT_ROOT / "prefix_leakage_after_detemplate_original_split.csv"
PREFIX_STRATIFIED = REPORT_ROOT / "prefix_leakage_after_detemplate_group_stratified_split.csv"
SUMMARY_JSON = REPORT_ROOT / "detemplate_summary.json"
REPORT_MD = REPORT_ROOT / "detemplate_report.md"


BANNED_CUES = [
    "the passage reports",
    "the paper reports",
    "a bounded reading",
    "bounded rewrite",
    "the study demonstrates",
    "this result can be generalized",
    "broader settings",
    "the claim suggests",
    "the claim moves",
    "opposite",
    "contradiction",
    "contradicts",
    "deployment-ready",
    "can be directly deployed",
    "ready for deployment",
    "policy action",
    "safety-certified",
]

TARGETS = [
    "escalation_binary_label_guess",
    "issue_binary_label_guess",
    "contradiction_binary_label_guess",
    "candidate_label_guess",
]


def read_csv(path):
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def write_csv(path, rows, fieldnames=None):
    path.parent.mkdir(parents=True, exist_ok=True)
    if fieldnames is None:
        fieldnames = []
        seen = set()
        for row in rows:
            for key in row:
                if key not in seen:
                    fieldnames.append(key)
                    seen.add(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow(row)


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def normalize_risk(text):
    value = normalize_space(text).lower()
    if not value:
        return "unknown"
    if "high" in value:
        return "high"
    if "moderate" in value or "medium" in value:
        return "medium"
    if "low" in value:
        return "low"
    return "medium"


def banned_hits(text):
    lower = (text or "").lower()
    return [cue for cue in BANNED_CUES if cue in lower]


def word_count(text):
    return len(re.findall(r"\b[\w-]+\b", text or ""))


def prefix_key(text, mode):
    clean = normalize_space(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
    words = clean.split()
    if mode == "first1":
        return " ".join(words[:1])
    if mode == "first4":
        return " ".join(words[:4])
    if mode == "first6":
        return " ".join(words[:6])
    if mode == "first10":
        return " ".join(words[:10])
    raise ValueError(mode)


def original_membership():
    membership = {}
    for split in ["train", "dev", "test"]:
        for row in read_csv(SOURCE_SPLITS / f"{split}.csv"):
            cid = row.get("candidate_id") or row.get("expand_id")
            if cid:
                membership[cid] = split
    return membership


def group_rows(rows):
    groups = defaultdict(list)
    for row in rows:
        gid = row.get("split_group_id") or row.get("source_pair_id") or row.get("candidate_id")
        groups[gid].append(row)
    return groups


def make_group_stratified_membership(rows):
    groups = group_rows(rows)
    labels = sorted(Counter(r.get("candidate_label_guess", "") for r in rows))
    split_names = ["train", "dev", "test"]
    target_size = {"train": 90, "dev": 30, "test": 30}
    global_label_counts = Counter(r.get("candidate_label_guess", "") for r in rows)
    target_label_counts = {
        split: {
            label: max(1, round(global_label_counts[label] * target_size[split] / len(rows)))
            for label in labels
        }
        for split in split_names
    }

    split_counts = Counter()
    split_label_counts = {split: Counter() for split in split_names}
    membership_by_group = {}

    def rarity_score(group):
        score = 0.0
        for row in group:
            label = row.get("candidate_label_guess", "")
            score += 1.0 / max(1, global_label_counts[label])
        return score

    ordered = sorted(
        groups.items(),
        key=lambda kv: (-rarity_score(kv[1]), kv[0]),
    )

    def assignment_loss(counts, label_counts):
        loss = 0.0
        for split in split_names:
            loss += 4.0 * ((counts[split] - target_size[split]) / max(1, target_size[split])) ** 2
            for label in labels:
                desired = target_label_counts[split][label]
                loss += ((label_counts[split][label] - desired) / max(1, desired)) ** 2
        return loss

    for gid, group in ordered:
        group_label_counts = Counter(r.get("candidate_label_guess", "") for r in group)
        best_split = None
        best_score = None
        for split in split_names:
            projected_counts = Counter(split_counts)
            projected_labels = {s: Counter(split_label_counts[s]) for s in split_names}
            projected_counts[split] += len(group)
            projected_labels[split].update(group_label_counts)
            loss = assignment_loss(projected_counts, projected_labels)
            overrun = max(0, projected_counts[split] - target_size[split])
            tie = (loss + overrun * 100.0, split_names.index(split))
            if best_score is None or tie < best_score:
                best_score = tie
                best_split = split
        membership_by_group[gid] = best_split
        split_counts[best_split] += len(group)
        split_label_counts[best_split].update(group_label_counts)

    membership = {}
    for gid, group in groups.items():
        split = membership_by_group[gid]
        for row in group:
            membership[row.get("candidate_id") or row.get("expand_id")] = split
    return membership


def write_splits(rows, membership, out_dir, fieldnames):
    counts = {}
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if membership.get(r.get("candidate_id") or r.get("expand_id")) == split]
        counts[split] = len(split_rows)
        write_csv(out_dir / f"{split}.csv", split_rows, fieldnames)
        write_jsonl(out_dir / f"{split}.jsonl", split_rows)
    write_csv(out_dir / "all.csv", rows, fieldnames)
    write_jsonl(out_dir / "all.jsonl", rows)
    return counts


def split_distribution(rows, membership, split_name):
    out = []
    for split in ["train", "dev", "test"]:
        split_rows = [r for r in rows if membership.get(r.get("candidate_id") or r.get("expand_id")) == split]
        for target in TARGETS:
            counts = Counter(r.get(target, "") for r in split_rows)
            for label, count in sorted(counts.items()):
                out.append({
                    "split_scheme": split_name,
                    "split": split,
                    "target": target,
                    "label": label,
                    "count": count,
                })
    return out


def macro_f1(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    if not labels:
        return 0.0
    f1s = []
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1s.append((2 * precision * recall / (precision + recall)) if precision + recall else 0.0)
    return sum(f1s) / len(f1s)


def accuracy(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0.0


def train_prefix_classifier(train_rows, target, mode):
    default = Counter((r.get(target) or "").strip() for r in train_rows).most_common(1)[0][0]
    by_key = defaultdict(Counter)
    for row in train_rows:
        by_key[prefix_key(row.get("claim_text", ""), mode)][(row.get(target) or "").strip()] += 1
    return {k: c.most_common(1)[0][0] for k, c in by_key.items()}, default


def prefix_diag(rows, membership, split_scheme, out_path):
    by_split = {"train": [], "dev": [], "test": []}
    for row in rows:
        split = membership.get(row.get("candidate_id") or row.get("expand_id"))
        if split in by_split:
            by_split[split].append(row)
    diag = []
    for target in TARGETS:
        for mode in ["first1", "first4", "first6", "first10"]:
            mapping, default = train_prefix_classifier(by_split["train"], target, mode)
            for split in ["dev", "test"]:
                eval_rows = by_split[split]
                y_true = [(r.get(target) or "").strip() for r in eval_rows]
                y_pred = [mapping.get(prefix_key(r.get("claim_text", ""), mode), default) for r in eval_rows]
                keys = [prefix_key(r.get("claim_text", ""), mode) for r in eval_rows]
                diag.append({
                    "dataset": "simclaim_detemplate_v1_150",
                    "split_scheme": split_scheme,
                    "target": target,
                    "prefix_mode": mode,
                    "eval_split": split,
                    "n_train": len(by_split["train"]),
                    "n_eval": len(eval_rows),
                    "eval_class_count": len(set(y_true)),
                    "accuracy": f"{accuracy(y_true, y_pred):.6f}",
                    "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
                    "n_unique_eval_prefixes": len(set(keys)),
                    "top_eval_prefix_share": f"{(Counter(keys).most_common(1)[0][1] / len(keys)):.6f}" if keys else "0.000000",
                })
    write_csv(out_path, diag)
    return diag


def quality_audit(rows):
    out = []
    for row in rows:
        claim = row.get("claim_text", "")
        original = row.get("claim_text_original_template", "")
        hits = banned_hits(claim)
        out.append({
            "candidate_id": row.get("candidate_id", ""),
            "variant_type": row.get("variant_type", ""),
            "candidate_label_guess": row.get("candidate_label_guess", ""),
            "word_count": word_count(claim),
            "unchanged_from_template_claim": str(normalize_space(claim).lower() == normalize_space(original).lower()).lower(),
            "banned_cue_hit_count": len(hits),
            "banned_cue_hits": "; ".join(hits),
            "prefix_first1": prefix_key(claim, "first1"),
            "prefix_first4": prefix_key(claim, "first4"),
            "prefix_first6": prefix_key(claim, "first6"),
            "leakage_risk_after_rewrite": row.get("leakage_risk_after_rewrite", ""),
            "detemplate_status": row.get("detemplate_status", ""),
            "source_trace_status": row.get("source_trace_status", ""),
            "claim_text_original_template": original,
            "claim_text_detemplated": claim,
            "detemplate_semantic_notes": row.get("detemplate_semantic_notes", ""),
        })
    write_csv(QUALITY_AUDIT, out)
    return out


def summarize(rows, quality_rows, original_counts, strat_counts, diag_original, diag_stratified):
    n = len(rows)
    status_counts = Counter(r.get("detemplate_status", "") for r in rows)
    risk_counts = Counter(r.get("leakage_risk_after_rewrite", "") for r in rows)
    variant_counts = Counter(r.get("variant_type", "") for r in rows)
    banned_rows = sum(int(r["banned_cue_hit_count"]) > 0 for r in quality_rows)
    unchanged_rows = sum(r["unchanged_from_template_claim"] == "true" for r in quality_rows)
    source_trace_complete = sum(
        1 for r in rows
        if r.get("claim_source_url") and r.get("evidence_source_url") and r.get("source_location")
    )

    def worst_meaningful(diag):
        meaningful = [
            d for d in diag
            if d["eval_split"] == "test"
            and d["prefix_mode"] in ("first4", "first6")
            and int(d["eval_class_count"]) >= 2
        ]
        return max([float(d["macro_f1"]) for d in meaningful], default=0.0)

    summary = {
        "dataset": "simclaim_detemplate_v1_150",
        "n_rows": n,
        "original_split_counts": original_counts,
        "group_stratified_split_counts": strat_counts,
        "detemplate_status_counts": dict(status_counts),
        "leakage_risk_after_rewrite_counts": dict(risk_counts),
        "variant_counts": dict(variant_counts),
        "banned_cue_rows_after_rewrite": banned_rows,
        "unchanged_rows_after_rewrite": unchanged_rows,
        "source_trace_complete_rate": round(source_trace_complete / n, 6) if n else 0,
        "worst_meaningful_test_prefix_macro_f1_original_split": round(worst_meaningful(diag_original), 6),
        "worst_meaningful_test_prefix_macro_f1_group_stratified": round(worst_meaningful(diag_stratified), 6),
        "outputs": {
            "candidates_csv": str(CANDIDATE_CSV),
            "original_splits_dir": str(SPLITS_ORIGINAL),
            "group_stratified_splits_dir": str(SPLITS_STRATIFIED),
            "quality_audit_csv": str(QUALITY_AUDIT),
            "split_distribution_audit_csv": str(SPLIT_AUDIT),
            "prefix_original_split_csv": str(PREFIX_ORIGINAL),
            "prefix_group_stratified_csv": str(PREFIX_STRATIFIED),
            "summary_json": str(SUMMARY_JSON),
            "report_md": str(REPORT_MD),
        },
        "recommended_next_step": (
            "Run formal traditional and LLM baselines on splits_group_stratified. "
            "Use this set as scaffold only; do not mark gold or paper_valid until human audit."
        ),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(summary, diag_original, diag_stratified)
    return summary


def write_report(summary, diag_original, diag_stratified):
    lines = []
    lines.append("# SimClaim detemplate v1 150 report")
    lines.append("")
    lines.append("This is the small-data scaffold version: claims were detemplated, source trace and labels were preserved, and a new group-level stratified split was added for usable evaluation.")
    lines.append("")
    lines.append("## Hard status")
    lines.append("")
    lines.append(f"- Rows: {summary['n_rows']}")
    lines.append(f"- Rewrite status: {summary['detemplate_status_counts']}")
    lines.append(f"- Risk buckets: {summary['leakage_risk_after_rewrite_counts']}")
    lines.append(f"- Banned template cue rows after rewrite: {summary['banned_cue_rows_after_rewrite']}")
    lines.append(f"- Unchanged rows after rewrite: {summary['unchanged_rows_after_rewrite']}")
    lines.append(f"- Source trace complete rate: {summary['source_trace_complete_rate']}")
    lines.append(f"- Original split counts: {summary['original_split_counts']}")
    lines.append(f"- Group-stratified split counts: {summary['group_stratified_split_counts']}")
    lines.append("")
    lines.append("## What changed")
    lines.append("")
    lines.append("- Original split is preserved for compatibility.")
    lines.append("- `splits_group_stratified` is added because the original dev/test split has no contradiction examples.")
    lines.append("- No row is gold, human audited, paper valid, or release-ready.")
    lines.append("")
    lines.append("## Prefix leakage summary")
    lines.append("")
    lines.append(f"- Worst meaningful test prefix macro-F1, original split: {summary['worst_meaningful_test_prefix_macro_f1_original_split']}")
    lines.append(f"- Worst meaningful test prefix macro-F1, group-stratified split: {summary['worst_meaningful_test_prefix_macro_f1_group_stratified']}")
    lines.append("")
    lines.append("## Group-stratified prefix diagnostics")
    lines.append("")
    lines.append("| target | prefix | split | classes | acc | macro-F1 | unique prefixes | top prefix share |")
    lines.append("|---|---:|---|---:|---:|---:|---:|---:|")
    for d in diag_stratified:
        lines.append(
            f"| {d['target']} | {d['prefix_mode']} | {d['eval_split']} | {d['eval_class_count']} | "
            f"{d['accuracy']} | {d['macro_f1']} | {d['n_unique_eval_prefixes']} | {d['top_eval_prefix_share']} |"
        )
    lines.append("")
    lines.append("## Files")
    lines.append("")
    for key, value in summary["outputs"].items():
        lines.append(f"- {key}: `{value}`")
    lines.append("")
    lines.append("## Recommended next step")
    lines.append("")
    lines.append(summary["recommended_next_step"])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    rows = read_csv(CANDIDATE_CSV)
    fieldnames = list(rows[0].keys())
    if "leakage_risk_after_rewrite_raw" not in fieldnames:
        fieldnames.append("leakage_risk_after_rewrite_raw")

    for row in rows:
        raw = row.get("leakage_risk_after_rewrite", "")
        row["leakage_risk_after_rewrite_raw"] = raw
        row["leakage_risk_after_rewrite"] = normalize_risk(raw)

    write_csv(CANDIDATE_CSV, rows, fieldnames)
    write_jsonl(CANDIDATE_JSONL, rows)

    original = original_membership()
    stratified = make_group_stratified_membership(rows)
    original_counts = write_splits(rows, original, SPLITS_ORIGINAL, fieldnames)
    strat_counts = write_splits(rows, stratified, SPLITS_STRATIFIED, fieldnames)

    quality_rows = quality_audit(rows)
    split_rows = split_distribution(rows, original, "original") + split_distribution(rows, stratified, "group_stratified")
    write_csv(SPLIT_AUDIT, split_rows)
    diag_original = prefix_diag(rows, original, "original", PREFIX_ORIGINAL)
    diag_stratified = prefix_diag(rows, stratified, "group_stratified", PREFIX_STRATIFIED)
    summary = summarize(rows, quality_rows, original_counts, strat_counts, diag_original, diag_stratified)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
