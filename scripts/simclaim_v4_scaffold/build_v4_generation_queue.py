import csv
import hashlib
import json
import random
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
REGISTRY_CSV = ROOT / "data" / "simclaim_v4_scaffold" / "audit" / "v4_unique_evidence_registry.csv"
OUT_ROOT = ROOT / "data" / "simclaim_v4_scaffold" / "generation_queue"
REPORT_DIR = ROOT / "reports" / "simclaim_v4_scaffold"

GROUP_QUEUE_CSV = OUT_ROOT / "v4_generation_queue_150_groups.csv"
CANDIDATE_SLOT_CSV = OUT_ROOT / "v4_generation_queue_600_candidate_slots.csv"
SPLIT_AUDIT_CSV = OUT_ROOT / "v4_generation_queue_split_audit.csv"
SUMMARY_JSON = OUT_ROOT / "v4_generation_queue_summary.json"
REPORT_MD = REPORT_DIR / "v4_generation_queue_report.md"

SEED = 50
N_GROUPS_TARGET = 150
SPLIT_COUNTS = {"train": 90, "dev": 30, "test": 30}
LABEL_SLOTS = [
    ("supported", "same evidence meaning; no overclaim"),
    ("mild_scope_overclaim", "slightly broader scope than evidence supports"),
    ("strong_action_overclaim", "action/policy recommendation stronger than evidence supports"),
    ("contradiction_candidate", "claim conflicts with evidence"),
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
                    seen.add(key)
                    fieldnames.append(key)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def select_groups(registry):
    trace = [r for r in registry if r.get("trace_complete") == "true" and r.get("evidence_text", "").strip()]
    current = [r for r in trace if r.get("in_current_v3") == "true"]
    new = [r for r in trace if r.get("in_current_v3") != "true"]
    current.sort(key=lambda r: r["evidence_registry_id"])

    need_new = N_GROUPS_TARGET - len(current)
    if need_new < 0:
        selected = current[:N_GROUPS_TARGET]
    else:
        by_domain = defaultdict(list)
        for r in new:
            by_domain[r.get("domain") or "unknown"].append(r)
        rng = random.Random(SEED)
        for items in by_domain.values():
            items.sort(key=lambda r: r["evidence_registry_id"])
            rng.shuffle(items)
        domains = sorted(by_domain, key=lambda d: (-len(by_domain[d]), d))
        picked = []
        while len(picked) < need_new:
            progressed = False
            for domain in domains:
                if by_domain[domain] and len(picked) < need_new:
                    picked.append(by_domain[domain].pop(0))
                    progressed = True
            if not progressed:
                break
        selected = current + picked
    if len(selected) < N_GROUPS_TARGET:
        raise RuntimeError(f"not enough trace-complete evidence groups: selected={len(selected)} target={N_GROUPS_TARGET}")
    return selected[:N_GROUPS_TARGET]


def assign_splits(groups):
    rng = random.Random(SEED)
    by_domain = defaultdict(list)
    for group in groups:
        by_domain[group.get("domain") or "unknown"].append(group)
    for items in by_domain.values():
        items.sort(key=lambda r: r["v4_group_id"])
        rng.shuffle(items)

    split_order = ["train", "train", "train", "dev", "test"]
    split_counts = Counter()
    cursor = 0
    ordered = []
    for domain in sorted(by_domain, key=lambda d: (-len(by_domain[d]), d)):
        ordered.extend(by_domain[domain])

    for group in ordered:
        assigned = None
        for _ in range(len(split_order) * 2):
            split = split_order[cursor % len(split_order)]
            cursor += 1
            if split_counts[split] < SPLIT_COUNTS[split]:
                assigned = split
                break
        if assigned is None:
            for split in ["train", "dev", "test"]:
                if split_counts[split] < SPLIT_COUNTS[split]:
                    assigned = split
                    break
        if assigned is None:
            raise RuntimeError("split assignment overflow")
        group["split"] = assigned
        split_counts[assigned] += 1
    if dict(split_counts) != SPLIT_COUNTS:
        raise RuntimeError(f"bad split counts: {dict(split_counts)} expected={SPLIT_COUNTS}")
    return groups


def build_group_queue(selected):
    groups = []
    for i, r in enumerate(selected, 1):
        evidence_text = r.get("evidence_text", "")
        group = {
            "v4_group_id": f"V4-G{i:03d}",
            "evidence_registry_id": r.get("evidence_registry_id", ""),
            "queue_role": "v3_seed_evidence" if r.get("in_current_v3") == "true" else "new_expansion_evidence",
            "domain": r.get("domain", ""),
            "paper_title": r.get("paper_title", ""),
            "paper_year": r.get("paper_year", ""),
            "source_pair_id": r.get("source_pair_id", ""),
            "claim_source_url": r.get("claim_source_url", ""),
            "evidence_source_url": r.get("evidence_source_url", ""),
            "claim_location": r.get("claim_location", ""),
            "evidence_location": r.get("evidence_location", ""),
            "source_location": r.get("source_location", ""),
            "evidence_text": evidence_text,
            "evidence_text_sha256": hashlib.sha256(evidence_text.encode("utf-8")).hexdigest(),
            "evidence_lock_status": "locked_original_from_registry",
            "evidence_fidelity_policy": "do_not_modify_evidence_text",
            "trace_complete": r.get("trace_complete", ""),
            "origin_files": r.get("origin_files", ""),
            "v4_generation_status": "pending",
            "v4_recipe_version": "v4_scaffold_neutral_claim_slots_seed50",
        }
        groups.append(group)
    return assign_splits(groups)


def build_candidate_slots(groups):
    rows = []
    for group in groups:
        for idx, (label, description) in enumerate(LABEL_SLOTS, 1):
            issue_binary = "no_issue" if label == "supported" else "issue"
            escalation_binary = "non_escalation" if label in {"supported", "contradiction_candidate"} else "escalation"
            contradiction_binary = "contradiction" if label == "contradiction_candidate" else "not_contradiction"
            row = dict(group)
            row.update({
                "candidate_id": f"{group['v4_group_id']}-{idx}",
                "candidate_label_guess": label,
                "candidate_slot_description": description,
                "issue_binary_label_guess": issue_binary,
                "escalation_binary_label_guess": escalation_binary,
                "contradiction_binary_label_guess": contradiction_binary,
                "claim_text": "",
                "claim_generation_status": "pending",
                "claim_generation_policy": "generate_claim_only; preserve_locked_evidence; neutralize_surface_style_across_labels",
                "annotation_status": "not_started",
                "human_audited": "false",
                "final_label": "",
                "gold_label": "",
            })
            rows.append(row)
    return rows


def write_split_audit(groups, slots):
    audit = []
    for split in ["train", "dev", "test"]:
        gs = [g for g in groups if g["split"] == split]
        ss = [s for s in slots if s["split"] == split]
        audit.append({
            "split": split,
            "n_groups": len(gs),
            "n_candidate_slots": len(ss),
            "n_v3_seed_evidence": sum(1 for g in gs if g["queue_role"] == "v3_seed_evidence"),
            "n_new_expansion_evidence": sum(1 for g in gs if g["queue_role"] == "new_expansion_evidence"),
            "n_domains": len({g["domain"] for g in gs}),
        })
        for domain, count in Counter(g["domain"] or "unknown" for g in gs).most_common():
            audit.append({"split": split, "domain": domain, "n_groups": count})
        for label, count in Counter(s["candidate_label_guess"] for s in ss).most_common():
            audit.append({"split": split, "candidate_label_guess": label, "n_candidate_slots": count})
    write_csv(SPLIT_AUDIT_CSV, audit)


def write_report(groups, slots):
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    role_counts = Counter(g["queue_role"] for g in groups)
    domain_counts = Counter(g["domain"] or "unknown" for g in groups)
    split_counts = Counter(g["split"] for g in groups)
    lines = [
        "# v4 generation queue report",
        "",
        "This is a scaffold only. It creates a locked-evidence generation queue and candidate slots. It does not generate claims, modify evidence, annotate, train, or run LLM evaluation.",
        "",
        "## Summary",
        "",
        f"- Evidence groups selected: {len(groups)}",
        f"- Candidate slots created: {len(slots)}",
        f"- Evidence lock status: locked original text",
        f"- Source trace: required complete for all selected groups",
        f"- Split seed: {SEED}",
        "",
        "## Evidence role counts",
        "",
        "| role | groups |",
        "|---|---:|",
    ]
    for role, count in role_counts.most_common():
        lines.append(f"| {role} | {count} |")
    lines.extend([
        "",
        "## Split counts",
        "",
        "| split | groups | candidate slots |",
        "|---|---:|---:|",
    ])
    for split in ["train", "dev", "test"]:
        lines.append(f"| {split} | {split_counts[split]} | {split_counts[split] * len(LABEL_SLOTS)} |")
    lines.extend([
        "",
        "## Domain counts",
        "",
        "| domain | groups |",
        "|---|---:|",
    ])
    for domain, count in domain_counts.most_common():
        lines.append(f"| {domain} | {count} |")
    lines.extend([
        "",
        "## Next step",
        "",
        "The next executable step is v4 claim generation for the 600 pending slots. The generation prompt must keep all four labels stylistically neutral and must not modify evidence text.",
        "",
        "Recommended gate after generation:",
        "",
        "- evidence unchanged rate = 100%",
        "- source trace complete rate = 100%",
        "- duplicate claim risk near 0",
        "- claim+evidence beats claim-only under group-level robust evaluation",
        "- LLM comparison only after traditional gate passes",
        "",
        "## Output files",
        "",
        f"- Group queue: `{GROUP_QUEUE_CSV}`",
        f"- Candidate slot queue: `{CANDIDATE_SLOT_CSV}`",
        f"- Split audit: `{SPLIT_AUDIT_CSV}`",
    ])
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


def main():
    OUT_ROOT.mkdir(parents=True, exist_ok=True)
    registry = read_csv(REGISTRY_CSV)
    selected = select_groups(registry)
    groups = build_group_queue(selected)
    slots = build_candidate_slots(groups)
    write_csv(GROUP_QUEUE_CSV, groups)
    write_csv(CANDIDATE_SLOT_CSV, slots)
    write_split_audit(groups, slots)
    summary = {
        "status": "ok",
        "seed": SEED,
        "n_groups": len(groups),
        "n_candidate_slots": len(slots),
        "role_counts": dict(Counter(g["queue_role"] for g in groups)),
        "split_group_counts": dict(Counter(g["split"] for g in groups)),
        "label_slot_counts": dict(Counter(s["candidate_label_guess"] for s in slots)),
        "group_queue_csv": str(GROUP_QUEUE_CSV),
        "candidate_slot_csv": str(CANDIDATE_SLOT_CSV),
        "split_audit_csv": str(SPLIT_AUDIT_CSV),
        "report_md": str(REPORT_MD),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    write_report(groups, slots)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
