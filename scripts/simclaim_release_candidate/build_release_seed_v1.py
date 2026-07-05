import csv
import hashlib
import json
import os
import re
import shutil
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
OUT_ROOT = Path(os.environ.get("SIMCLAIM_RELEASE_OUT_ROOT", str(ROOT / "data" / "simclaim_release_candidate_v1")))
RELEASE_STAGE = os.environ.get("SIMCLAIM_RELEASE_STAGE", "seed_strict_pass")
CANDIDATE_FILENAME = os.environ.get("SIMCLAIM_RELEASE_CANDIDATE_FILENAME", "candidate_master_seed.csv")
INCLUDE_GROUPS = {x.strip() for x in os.environ.get("SIMCLAIM_RELEASE_INCLUDE_GROUPS", "").split(",") if x.strip()}
EXCLUDE_GROUPS = {x.strip() for x in os.environ.get("SIMCLAIM_RELEASE_EXCLUDE_GROUPS", "").split(",") if x.strip()}
YEAR_OVERRIDES_BY_TITLE = {
    "Lights Out? Wargaming a Chinese Blockade of Taiwan": "2025",
    "NIST The Cyber Range: A Guide": "2023",
}

CANDIDATE_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
EVIDENCE_REGISTRY_CSV = ROOT / "data" / "simclaim_v4_scaffold" / "audit" / "v4_unique_evidence_registry.csv"
VALIDATION_AUDIT_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "audit" / "v4b_independent_validation_audit.csv"
LEAKAGE_AUDIT_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "audit" / "v4b_pilot_claim_only_leakage_terms.csv"
STRICT_METRIC_REPORT = ROOT / "experiments" / "simclaim_hardpair_v4b_pilot_strict_pass_baselines" / "reports" / "v4b_pilot_strict_pass_baseline_report.md"
DATASET_INFO_AUDIT = ROOT / "reports" / "simclaim_hardpair_v4b_pilot" / "v4b_dataset_information_audit_16_strict_groups.md"


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


def sha16(text):
    return hashlib.sha256((text or "").encode("utf-8")).hexdigest()[:16]


def arxiv_id(url):
    m = re.search(r"arxiv\.org/(?:abs|pdf)/([^/?#]+)", url or "", flags=re.I)
    return m.group(1).replace(".pdf", "") if m else ""


def infer_source_type(url, title):
    low = f"{url} {title}".lower()
    if "arxiv.org" in low or "openreview.net" in low or "doi.org" in low:
        return "paper"
    if any(x in low for x in ["cisa", "nist", "cdc", "mitre", "csis"]):
        return "official_report_or_advisory"
    if low.startswith("http"):
        return "webpage_or_report"
    return "unknown"


def normalize_trace_metadata(row):
    row = dict(row)
    if not row.get("source_location"):
        row["source_location"] = row.get("evidence_location") or row.get("claim_location") or ""
    if not row.get("paper_year"):
        row["paper_year"] = YEAR_OVERRIDES_BY_TITLE.get(row.get("paper_title", ""), "")
    return row


def completeness(row, fields):
    return all(str(row.get(f, "")).strip() for f in fields)


def main():
    for sub in ["sources", "evidence", "candidates", "audit", "reports", "splits"]:
        (OUT_ROOT / sub).mkdir(parents=True, exist_ok=True)

    candidates = [normalize_trace_metadata(r) for r in read_csv(CANDIDATE_CSV)]
    evidence_registry = [normalize_trace_metadata(r) for r in read_csv(EVIDENCE_REGISTRY_CSV)]
    validation = read_csv(VALIDATION_AUDIT_CSV)
    pass_groups = {r["v4_group_id"] for r in validation if r.get("validator_ok") == "true"}
    if INCLUDE_GROUPS:
        pass_groups &= INCLUDE_GROUPS
    pass_groups -= EXCLUDE_GROUPS
    strict = [
        r for r in candidates
        if r.get("claim_generation_status") == "success" and r.get("v4_group_id") in pass_groups
    ]
    strict_groups = sorted({r["v4_group_id"] for r in strict})
    strict_evidence_ids = sorted({r["evidence_registry_id"] for r in strict})
    evidence_by_id = {r["evidence_registry_id"]: r for r in evidence_registry}

    source_key_to_id = {}
    source_rows = []
    for evid_id in strict_evidence_ids:
        r = evidence_by_id[evid_id]
        key = (
            r.get("evidence_source_url", ""),
            r.get("paper_title", ""),
            r.get("paper_year", ""),
            r.get("domain", ""),
        )
        if key not in source_key_to_id:
            source_doc_id = f"SRC-{len(source_key_to_id) + 1:04d}"
            source_key_to_id[key] = source_doc_id
            related = [x for x in strict if x.get("evidence_source_url") == key[0] and x.get("paper_title") == key[1]]
            source_rows.append({
                "source_doc_id": source_doc_id,
                "domain": r.get("domain", ""),
                "title": r.get("paper_title", ""),
                "year": r.get("paper_year", ""),
                "source_type": infer_source_type(r.get("evidence_source_url", ""), r.get("paper_title", "")),
                "source_url": r.get("evidence_source_url", ""),
                "claim_source_url": r.get("claim_source_url", ""),
                "evidence_source_url": r.get("evidence_source_url", ""),
                "doi_or_arxiv": arxiv_id(r.get("evidence_source_url", "")),
                "source_hash": sha16("|".join(key)),
                "n_candidate_rows": len(related),
                "n_groups": len({x.get("v4_group_id") for x in related}),
                "group_ids": "|".join(sorted({x.get("v4_group_id") for x in related})),
                "metadata_complete": str(completeness(r, ["domain", "paper_title", "paper_year", "claim_source_url", "evidence_source_url"])).lower(),
            })

    def source_id_for(row):
        key = (
            row.get("evidence_source_url", ""),
            row.get("paper_title", ""),
            row.get("paper_year", ""),
            row.get("domain", ""),
        )
        return source_key_to_id.get(key, "")

    evidence_seed = []
    for evid_id in strict_evidence_ids:
        row = dict(evidence_by_id[evid_id])
        row["source_doc_id"] = source_id_for(row)
        row["release_stage"] = RELEASE_STAGE
        evidence_seed.append(row)

    candidate_seed = []
    for row in strict:
        out = dict(row)
        out["source_doc_id"] = source_id_for(row)
        out["claim_source_type"] = "synthetic_generated_from_locked_evidence"
        out["release_stage"] = RELEASE_STAGE
        out["is_strict_pass"] = "true"
        out["final_label"] = ""
        out["gold_label"] = ""
        if not out.get("human_audited"):
            out["human_audited"] = "false"
        candidate_seed.append(out)

    required = [
        "candidate_id", "evidence_registry_id", "source_pair_id", "domain", "paper_title", "paper_year",
        "claim_source_url", "evidence_source_url", "claim_location", "evidence_location", "source_location",
        "evidence_text", "evidence_text_sha256", "evidence_lock_status", "trace_complete", "split",
        "claim_text", "claim_text_sha256", "annotation_status", "human_audited",
    ]
    trace_audit = []
    for row in candidate_seed:
        locked_match = row.get("evidence_text", "") == row.get("evidence_text_original_locked", row.get("evidence_text", ""))
        trace_audit.append({
            "candidate_id": row.get("candidate_id", ""),
            "v4_group_id": row.get("v4_group_id", ""),
            "evidence_registry_id": row.get("evidence_registry_id", ""),
            "source_doc_id": row.get("source_doc_id", ""),
            "split": row.get("split", ""),
            "domain": row.get("domain", ""),
            "required_fields_complete": str(completeness(row, required)).lower(),
            "evidence_locked_match": str(locked_match).lower(),
            "trace_complete": row.get("trace_complete", ""),
            "admission_status": "accepted_seed" if completeness(row, required) and locked_match and row.get("trace_complete") == "true" else "blocked",
        })

    validation_seed = [r for r in validation if r.get("v4_group_id") in strict_groups]
    rejected = [r for r in validation if r.get("validator_ok") != "true"]
    admission_group_rows = []
    validation_by_group = {r.get("v4_group_id"): r for r in validation}
    for gid in sorted({r.get("v4_group_id") for r in validation}):
        v = validation_by_group[gid]
        admission_group_rows.append({
            "v4_group_id": gid,
            "admission_status": "accepted_release_checkpoint" if gid in pass_groups else "rejected_current",
            "validator_ok": v.get("validator_ok", ""),
            "validator_reason": v.get("validator_reason", ""),
            "semantic_suspicion_reasons": v.get("semantic_suspicion_reasons", ""),
        })

    write_csv(OUT_ROOT / "sources" / "source_registry_seed.csv", source_rows)
    write_csv(OUT_ROOT / "evidence" / "evidence_registry_seed.csv", evidence_seed)
    write_csv(OUT_ROOT / "candidates" / CANDIDATE_FILENAME, candidate_seed)
    write_csv(OUT_ROOT / "audit" / "source_trace_audit_seed.csv", trace_audit)
    write_csv(OUT_ROOT / "audit" / "validation_audit_seed.csv", validation_seed)
    write_csv(OUT_ROOT / "audit" / "rejected_groups_current.csv", rejected)
    write_csv(OUT_ROOT / "audit" / "admission_audit_seed.csv", admission_group_rows)
    if LEAKAGE_AUDIT_CSV.exists():
        shutil.copyfile(LEAKAGE_AUDIT_CSV, OUT_ROOT / "audit" / "leakage_audit_current.csv")
    if DATASET_INFO_AUDIT.exists():
        shutil.copyfile(DATASET_INFO_AUDIT, OUT_ROOT / "reports" / "dataset_information_audit_seed.md")

    for split in ["train", "dev", "test"]:
        write_csv(OUT_ROOT / "splits" / f"{split}.csv", [r for r in candidate_seed if r.get("split") == split])

    split_counts = Counter(r.get("split", "") for r in candidate_seed)
    domain_counts = Counter(r.get("domain", "") for r in candidate_seed)
    label_counts = Counter(r.get("candidate_label_guess", "") for r in candidate_seed)
    groups_by_split = defaultdict(set)
    for r in candidate_seed:
        groups_by_split[r.get("split", "")].add(r.get("v4_group_id", ""))

    summary = {
        "release_candidate_root": str(OUT_ROOT),
        "stage": RELEASE_STAGE,
        "candidate_rows": len(candidate_seed),
        "groups": len(strict_groups),
        "source_docs": len(source_rows),
        "evidence_records": len(evidence_seed),
        "split_rows": dict(split_counts),
        "split_groups": {k: len(v) for k, v in groups_by_split.items()},
        "domain_rows": dict(domain_counts),
        "candidate_label_rows": dict(label_counts),
        "strict_group_ids": strict_groups,
        "known_not_gold": True,
        "human_audited_true_count": sum(1 for r in candidate_seed if r.get("human_audited") == "true"),
        "final_label_nonempty_count": sum(1 for r in candidate_seed if r.get("final_label")),
    }
    (OUT_ROOT / "reports" / "seed_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    readme = [
        "# SimClaim release candidate v1 seed",
        "",
        "This directory contains the current strict-pass seed subset for SimClaim dataset construction.",
        "",
        "Important: this is an AI-preannotated candidate seed, not a human-audited gold dataset.",
        "",
        "## Contents",
        "",
        "- `sources/source_registry_seed.csv`: source-document registry for the seed subset.",
        "- `evidence/evidence_registry_seed.csv`: locked evidence records used by the seed subset.",
        f"- `candidates/{CANDIDATE_FILENAME}`: strict-pass candidate rows.",
        "- `splits/train.csv`, `splits/dev.csv`, `splits/test.csv`: current split files.",
        "- `audit/source_trace_audit_seed.csv`: row-level source and trace completeness audit.",
        "- `audit/validation_audit_seed.csv`: strict validator audit for accepted groups.",
        "- `audit/rejected_groups_current.csv`: rejected generated groups from the current pilot.",
        "- `reports/dataset_information_audit_seed.md`: detailed data information audit.",
        "",
        "## Current scale",
        "",
        f"- Candidate rows: {len(candidate_seed)}",
        f"- Groups: {len(strict_groups)}",
        f"- Source documents: {len(source_rows)}",
        f"- Evidence records: {len(evidence_seed)}",
        "",
        "## Policy",
        "",
        "- Evidence text is locked and hash-tracked.",
        "- Claims are synthetic/generated from locked evidence.",
        "- `human_audited` remains false.",
        "- `final_label` and `gold_label` remain empty.",
        "- Rejected groups must not be included without regeneration and revalidation.",
    ]
    (OUT_ROOT / "README.md").write_text("\n".join(readme), encoding="utf-8")

    card = [
        "# SimClaim release candidate v1: dataset card seed",
        "",
        "## Dataset status",
        "",
        "Seed-stage release candidate. Not a final public release and not a gold-label dataset.",
        "",
        "## Task",
        "",
        "Given a synthetic claim and locked source evidence, classify whether the claim is supported, mildly overclaims, strongly overclaims, or contradicts the evidence.",
        "",
        "## Provenance",
        "",
        "Evidence rows are trace-complete and linked to source URLs, source locations, and SHA-256 evidence hashes.",
        "",
        "## Labels",
        "",
        "- `candidate_label_guess`: AI-preannotated 4-class candidate label.",
        "- `issue_binary_label_guess`: no_issue vs issue.",
        "- `escalation_binary_label_guess`: non_escalation vs escalation.",
        "- `contradiction_binary_label_guess`: contradiction vs not_contradiction.",
        "",
        "## Known limitations",
        "",
        f"- Current checkpoint has {len(candidate_seed)} rows and {len(strict_groups)} groups.",
        "- Human audit has not been performed.",
        "- Domain coverage is not final.",
        "- The full 500-row dataset still needs staged generation, strict validation, and final packaging.",
    ]
    (OUT_ROOT / "DATASET_CARD.md").write_text("\n".join(card), encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
