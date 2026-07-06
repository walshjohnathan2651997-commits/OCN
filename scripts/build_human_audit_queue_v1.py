#!/usr/bin/env python
"""build_human_audit_queue_v1.py — Build a small targeted human audit seed queue.

Produces a small (default 120) targeted audit seed from the V3.17 silver
diagnostic pool. The audit is NOT a gold benchmark; it is a directional
reliability check on the top of the review queue and on the strong_action
label direction.

Sampling buckets (deterministic, seed=42, group-aware cap of 2 per
target_candidate_group_id):
  1. top20          — all candidates in review_queue_top100_best rank 1..20
  2. top50_strong   — rank 21..50 with pred_label == strong_action_overclaim
  3. r4_fp          — error_cases_redacted error_category == FP
  4. r4_fn          — error_cases_redacted error_category == FN
  5. mild_strong    — error_type_tags contains mild_vs_strong_boundary
  6. contra_conf    — error_type_tags contains contradiction_confusion

Outputs (both hash-only, no raw claim/evidence text):
  data/audit_templates/human_audit_queue_seed_v1.csv
    Full audit template columns (incl. candidate_id, target_candidate_group_id)
    for local use. Identifiers present, raw text absent.
  data/audit_templates/human_audit_queue_seed_v1_redacted.csv
    Minimal columns only (hashes, rank, pred, silver_label, queue_source).
    No candidate_id, no target_candidate_group_id — cannot be linked back.

Hard boundaries:
  - no API, no network, no training
  - no original CSV modification
  - no gold_label fill
  - no raw claim_text / evidence_text in either output

Usage:
  python scripts/build_human_audit_queue_v1.py --config configs/v3_17_confidential_default.yaml
  python scripts/build_human_audit_queue_v1.py --config configs/v3_17_confidential_default.yaml --n 100
  python scripts/build_human_audit_queue_v1.py --toy_mode
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import random
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import (  # noqa: E402
    load_and_validate, resolve_path, write_run_config, print_guards,
)

DEFAULT_N = 120
SEED = 42
MAX_PER_GROUP = 2

# Bucket caps — sum to ~120 before dedup; the global cap --n is the hard stop.
BUCKET_CAPS = {
    "top20": 20,
    "top50_strong_action": 30,
    "r4_fp": 20,
    "r4_fn": 15,
    "mild_vs_strong_boundary": 20,
    "contradiction_confusion": 15,
}

# Full template columns — what an auditor fills in.
TEMPLATE_COLUMNS = [
    "audit_item_id",
    "candidate_id",
    "target_candidate_group_id",
    "source_hash",
    "claim_text_hash",
    "evidence_text_hash",
    "model_pred",
    "silver_label",
    "queue_rank",
    "queue_source",
    "auditor_label",
    "auditor_confidence",
    "audit_notes",
    "disagreement_reason",
    "requires_second_review",
    "human_audited",
    "created_at",
]

# Redacted columns — no identifiers, only hashes + rank + pred + silver + bucket.
REDACTED_COLUMNS = [
    "audit_item_id",
    "source_hash",
    "claim_text_hash",
    "evidence_text_hash",
    "model_pred",
    "silver_label",
    "queue_rank",
    "queue_source",
]

VALID_AUDITOR_LABELS = {
    "supported",
    "mild_scope_overclaim",
    "strong_action_overclaim",
    "contradiction_candidate",
    "uncertain_insufficient_context",
}


def sha256_hex(s: str) -> str:
    return hashlib.sha256(s.encode("utf-8")).hexdigest()


def read_csv_rows(path: Path) -> list[dict]:
    # utf-8-sig strips a leading BOM if present (some V3.17 CSVs ship with one).
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        return list(reader)


def load_candidates(candidate_csv: Path) -> dict[str, dict]:
    """Load candidate CSV indexed by candidate_id. keep_default_na=False equivalent."""
    rows = read_csv_rows(candidate_csv)
    out: dict[str, dict] = {}
    for r in rows:
        cid = r.get("candidate_id", "").strip()
        if not cid:
            continue
        out[cid] = r
    return out


def load_review_queue_top100(risk_ranking_dir: Path) -> list[dict]:
    """Return rows from review_queue_top100_best.csv sorted by rank asc."""
    p = risk_ranking_dir / "review_queue_top100_best.csv"
    if not p.exists():
        return []
    rows = read_csv_rows(p)
    # Parse rank as int for stable sorting; fall back to large number.
    def rank_key(r: dict) -> tuple:
        try:
            return (0, int(r.get("rank", "9999")))
        except (TypeError, ValueError):
            return (1, 9999)
    rows.sort(key=rank_key)
    return rows


def load_review_scores(review_queue_dir: Path) -> dict[str, dict]:
    """Index canonicalized_r4_review_scores.csv by candidate_id."""
    p = review_queue_dir / "canonicalized_r4_review_scores.csv"
    if not p.exists():
        return {}
    rows = read_csv_rows(p)
    return {r["candidate_id"]: r for r in rows if r.get("candidate_id")}


def load_error_cases(error_taxonomy_dir: Path) -> list[dict]:
    """Load error_cases_redacted.csv (hash-only, no raw text)."""
    p = error_taxonomy_dir / "error_cases_redacted.csv"
    if not p.exists():
        return []
    return read_csv_rows(p)


def parse_pred_label(candidate_id: str, queue_rows: list[dict],
                     review_scores: dict[str, dict],
                     error_cases: list[dict]) -> str:
    """Best-effort lookup of pred_label for a candidate across sources."""
    for q in queue_rows:
        if q.get("candidate_id") == candidate_id and q.get("pred_label"):
            return q["pred_label"]
    rs = review_scores.get(candidate_id)
    if rs and rs.get("pred_label"):
        return rs["pred_label"]
    for e in error_cases:
        if e.get("candidate_id") == candidate_id and e.get("pred_label"):
            return e["pred_label"]
    return ""


def parse_queue_rank(candidate_id: str, queue_rows: list[dict]) -> int:
    for q in queue_rows:
        if q.get("candidate_id") == candidate_id:
            try:
                return int(q.get("rank", "0"))
            except (TypeError, ValueError):
                return 0
    return 0


def has_tag(error_type_tags: str, tag: str) -> bool:
    if not error_type_tags:
        return False
    return tag in [t.strip() for t in error_type_tags.split(";") if t.strip()]


def build_buckets(
    queue_rows: list[dict],
    error_cases: list[dict],
) -> dict[str, list[str]]:
    """Return bucket_name -> list of candidate_ids in priority order."""
    buckets: dict[str, list[str]] = {k: [] for k in BUCKET_CAPS}

    # Bucket 1: top20
    for q in queue_rows:
        try:
            rank = int(q.get("rank", "0"))
        except (TypeError, ValueError):
            continue
        if 1 <= rank <= 20:
            cid = q.get("candidate_id", "")
            if cid:
                buckets["top20"].append(cid)

    # Bucket 2: top50_strong_action — rank 21..50 with strong_action pred
    for q in queue_rows:
        try:
            rank = int(q.get("rank", "0"))
        except (TypeError, ValueError):
            continue
        if 21 <= rank <= 50 and q.get("pred_label") == "strong_action_overclaim":
            cid = q.get("candidate_id", "")
            if cid:
                buckets["top50_strong_action"].append(cid)

    # Buckets 3-6: from error_cases_redacted
    fp_ids: list[str] = []
    fn_ids: list[str] = []
    mild_strong_ids: list[str] = []
    contra_conf_ids: list[str] = []
    for e in error_cases:
        cid = e.get("candidate_id", "")
        if not cid:
            continue
        cat = e.get("error_category", "")
        tags = e.get("error_type_tags", "")
        if cat == "FP":
            fp_ids.append(cid)
        if cat == "FN":
            fn_ids.append(cid)
        if has_tag(tags, "mild_vs_strong_boundary"):
            mild_strong_ids.append(cid)
        if has_tag(tags, "contradiction_confusion"):
            contra_conf_ids.append(cid)

    buckets["r4_fp"] = fp_ids
    buckets["r4_fn"] = fn_ids
    buckets["mild_vs_strong_boundary"] = mild_strong_ids
    buckets["contradiction_confusion"] = contra_conf_ids
    return buckets


def sample_with_caps(
    buckets: dict[str, list[str]],
    candidates: dict[str, dict],
    n: int,
    bucket_caps: dict[str, int],
    max_per_group: int,
    seed: int,
) -> list[tuple[str, str]]:
    """Sample candidate_ids respecting per-bucket caps, group cap, and total n.

    Returns list of (candidate_id, queue_source) in deterministic order.
    """
    rng = random.Random(seed)
    group_count: dict[str, int] = {}
    selected: list[tuple[str, str]] = []
    seen: set[str] = set()

    for bucket_name in BUCKET_CAPS.keys():
        ids = list(buckets.get(bucket_name, []))
        # Deterministic shuffle so we don't always pick the first few of a bucket.
        rng.shuffle(ids)
        cap = bucket_caps.get(bucket_name, 0)
        taken = 0
        for cid in ids:
            if len(selected) >= n:
                break
            if taken >= cap:
                break
            if cid in seen:
                continue
            cand = candidates.get(cid)
            if not cand:
                continue
            group = cand.get("target_candidate_group_id", "")
            if group and group_count.get(group, 0) >= max_per_group:
                continue
            seen.add(cid)
            if group:
                group_count[group] = group_count.get(group, 0) + 1
            selected.append((cid, bucket_name))
            taken += 1

    return selected


def build_audit_rows(
    selected: list[tuple[str, str]],
    candidates: dict[str, dict],
    queue_rows: list[dict],
    review_scores: dict[str, dict],
    error_cases: list[dict],
) -> list[dict]:
    """Build full audit rows (template columns) for each selected candidate."""
    rows: list[dict] = []
    now = datetime.now(timezone.utc).isoformat()
    for idx, (cid, bucket_name) in enumerate(selected, start=1):
        cand = candidates[cid]
        source_id = cand.get("source_id", "")
        source_hash = sha256_hex(source_id) if source_id else ""
        claim_text_hash = cand.get("claim_text_sha256", "")
        evidence_text_hash = cand.get("evidence_text_sha256", "")
        silver_label = cand.get("candidate_label_guess", "")
        pred_label = parse_pred_label(cid, queue_rows, review_scores, error_cases)
        queue_rank = parse_queue_rank(cid, queue_rows)
        audit_item_id = f"AUDIT-V1-{idx:04d}"
        rows.append({
            "audit_item_id": audit_item_id,
            "candidate_id": cid,
            "target_candidate_group_id": cand.get("target_candidate_group_id", ""),
            "source_hash": source_hash,
            "claim_text_hash": claim_text_hash,
            "evidence_text_hash": evidence_text_hash,
            "model_pred": pred_label,
            "silver_label": silver_label,
            "queue_rank": queue_rank,
            "queue_source": bucket_name,
            "auditor_label": "",
            "auditor_confidence": "",
            "audit_notes": "",
            "disagreement_reason": "",
            "requires_second_review": "",
            "human_audited": "False",
            "created_at": now,
        })
    return rows


def write_csv(path: Path, rows: list[dict], columns: list[str]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columns, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({k: r.get(k, "") for k in columns})


def write_build_report(
    path: Path,
    rows: list[dict],
    selected: list[tuple[str, str]],
    n_target: int,
    config,
) -> None:
    """Write a small JSON build report (no raw text)."""
    bucket_counts: dict[str, int] = {}
    for _, bucket_name in selected:
        bucket_counts[bucket_name] = bucket_counts.get(bucket_name, 0) + 1
    group_counts: dict[str, int] = {}
    for r in rows:
        g = r.get("target_candidate_group_id", "")
        if g:
            group_counts[g] = group_counts.get(g, 0) + 1
    report = {
        "script_name": "build_human_audit_queue_v1.py",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "n_target": n_target,
        "n_selected": len(rows),
        "bucket_counts": bucket_counts,
        "n_unique_groups": len(group_counts),
        "max_per_group": max(group_counts.values()) if group_counts else 0,
        "disclaimer": (
            "Small targeted audit seed. NOT a gold benchmark. "
            "Directional reliability check only."
        ),
        "guards": {
            "no_api": config.get("no_api"),
            "no_network": config.get("no_network"),
            "no_training": config.get("no_training"),
            "no_original_data_modification": config.get(
                "no_original_data_modification", True
            ),
        },
        "no_raw_text_in_outputs": True,
        "redacted_columns_present": True,
    }
    with open(path, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)


def run(args) -> int:
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    candidate_csv = resolve_path(config, "candidate_csv")
    review_queue_dir = resolve_path(config, "review_queue_dir")
    risk_ranking_dir = resolve_path(config, "risk_ranking_dir")
    if risk_ranking_dir is None:
        risk_ranking_dir = review_queue_dir
    # error_taxonomy_dir is not in the canonical config — derive a default.
    error_taxonomy_dir = Path("experiments/error_taxonomy_v1")
    if not error_taxonomy_dir.is_absolute():
        error_taxonomy_dir = (Path(__file__).resolve().parent.parent /
                              error_taxonomy_dir)

    print(f"candidate_csv: {candidate_csv}", flush=True)
    print(f"review_queue_dir: {review_queue_dir}", flush=True)
    print(f"risk_ranking_dir: {risk_ranking_dir}", flush=True)
    print(f"error_taxonomy_dir: {error_taxonomy_dir}", flush=True)

    candidates = load_candidates(candidate_csv)
    queue_rows = load_review_queue_top100(risk_ranking_dir)
    review_scores = load_review_scores(review_queue_dir)
    error_cases = load_error_cases(error_taxonomy_dir)

    print(f"loaded candidates: {len(candidates)}", flush=True)
    print(f"loaded review_queue_top100 rows: {len(queue_rows)}", flush=True)
    print(f"loaded review_scores: {len(review_scores)}", flush=True)
    print(f"loaded error_cases: {len(error_cases)}", flush=True)

    buckets = build_buckets(queue_rows, error_cases)
    for name, ids in buckets.items():
        print(f"  bucket {name}: {len(ids)} candidates", flush=True)

    selected = sample_with_caps(
        buckets=buckets,
        candidates=candidates,
        n=args.n,
        bucket_caps=BUCKET_CAPS,
        max_per_group=MAX_PER_GROUP,
        seed=SEED,
    )
    print(f"selected after caps: {len(selected)}", flush=True)

    rows = build_audit_rows(
        selected=selected,
        candidates=candidates,
        queue_rows=queue_rows,
        review_scores=review_scores,
        error_cases=error_cases,
    )

    out_dir = Path("data/audit_templates")
    if not out_dir.is_absolute():
        out_dir = Path(__file__).resolve().parent.parent / out_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    seed_path = out_dir / "human_audit_queue_seed_v1.csv"
    redacted_path = out_dir / "human_audit_queue_seed_v1_redacted.csv"
    report_path = out_dir / "human_audit_queue_build_report.json"

    write_csv(seed_path, rows, TEMPLATE_COLUMNS)
    write_csv(redacted_path, rows, REDACTED_COLUMNS)
    write_build_report(report_path, rows, selected, args.n, config)

    print(f"wrote {seed_path}", flush=True)
    print(f"wrote {redacted_path}", flush=True)
    print(f"wrote {report_path}", flush=True)

    # Sanity: verify no raw text leaked.
    forbidden = {"claim_text", "evidence_text", "selected_evidence"}
    for p in [seed_path, redacted_path]:
        with open(p, "r", encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            header_set = set(reader.fieldnames or [])
            leak = header_set & forbidden
            assert not leak, f"forbidden raw-text columns in {p}: {leak}"
    print("redaction check: PASS (no raw-text columns in outputs)", flush=True)

    return 0


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default=None,
                        help="Path to YAML config (default: v3_17_confidential_default.yaml)")
    parser.add_argument("--n", type=int, default=DEFAULT_N,
                        help=f"Target sample size (default {DEFAULT_N})")
    parser.add_argument("--toy_mode", action="store_true",
                        help="Use toy demo config")
    args = parser.parse_args(argv)
    return run(args)


if __name__ == "__main__":
    sys.exit(main())
