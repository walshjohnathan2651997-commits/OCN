#!/usr/bin/env python
"""run_format_shift_ablation_v1.py — Evidence format-shift ablation.

Constructs 8 evidence variants to prove that screening failure comes
from evidence format shift (lengthening, metadata contamination), not
from simple retrieval failure.

Hard boundaries:
  - no network, no API, no cloud
  - no model training
  - no R4 threshold changes
  - no original data modification
  - no label fields used for variant construction
  - oracle_clean is diagnostic upper-bound only, NOT production
"""

import argparse
import csv
import hashlib
import json
import re
import sys
from collections import defaultdict
from pathlib import Path

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402
from schema_utils import (  # noqa: E402
    validate_csv_file,
    validate_redacted_csv_file,
    write_schema_validation_report,
)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

CONFIG = {
    "no_network": True,
    "no_api": True,
    "no_training": True,
    "no_threshold_change": True,
}

FORBIDDEN_VARIANT_FIELDS = {
    "true_label",
    "candidate_label_guess",
    "gold_label",
    "human_audited",
    "oracle_hit",
    "final_label",
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "contradiction_binary_label_guess",
}

VARIANT_NAMES = [
    "oracle_clean",
    "oracle_plus_metadata",
    "oracle_lengthened",
    "oracle_plus_metadata_lengthened",
    "raw_bm25_top1_chunk",
    "cleaned_bm25_top1_chunk",
    "canonicalized_best_sentence_top5",
    "canonicalized_three_sentence_window_top5",
]

_HYPHEN_RE = re.compile(r"-\s*\n\s*")
_WS_RE = re.compile(r"\s+")
_PAGE_NUM_RE = re.compile(r"\b\d+\s*/\s*\d+\b")


def sha256_text(text):
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def clean_chunk_text(text):
    if not text:
        return ""
    text = _HYPHEN_RE.sub("", text)
    text = _PAGE_NUM_RE.sub("", text)
    text = _WS_RE.sub(" ", text).strip()
    return text


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates(csv_path):
    """Load candidate CSV. Reads allowed fields only."""
    fields_actually_read = [
        "candidate_id", "target_candidate_group_id", "claim_text",
        "title", "pdf_filename", "page_number", "evidence_text",
        "evidence_text_sha256",
    ]
    forbidden = FORBIDDEN_VARIANT_FIELDS & set(fields_actually_read)
    if forbidden:
        raise AssertionError(f"FATAL: forbidden fields read: {forbidden}")

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
                "evidence_text_sha256": row.get("evidence_text_sha256", ""),
            }
            if not rec["evidence_text_sha256"] and rec["evidence_text"]:
                rec["evidence_text_sha256"] = sha256_text(rec["evidence_text"])
            candidates.append(rec)
    return candidates


def load_chunk_retrieval(csv_path):
    """Load chunk retrieval CSV. Returns dict: candidate_id -> sorted list of chunks."""
    by_cand = defaultdict(list)
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            by_cand[row["candidate_id"]].append({
                "candidate_id": row["candidate_id"],
                "rank": int(row.get("rank", 0)),
                "chunk_id": row.get("chunk_id", ""),
                "retrieved_text": row.get("retrieved_text", ""),
                "page_number": int(row.get("page_number", 0)) if str(row.get("page_number", "")).isdigit() else 0,
            })
    for cid in by_cand:
        by_cand[cid].sort(key=lambda x: x["rank"])
    return dict(by_cand)


def load_selector_variants(csv_path):
    """Load selector_variant_evidence.csv. Returns dict: (candidate_id, selector) -> evidence."""
    lookup = {}
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = (row["candidate_id"], row["selector"])
            lookup[key] = {
                "selected_evidence": row.get("selected_evidence", ""),
                "selected_chunk_id": row.get("selected_chunk_id", ""),
                "selected_rank": int(row.get("selected_rank", 0)) if str(row.get("selected_rank", "")).isdigit() else 0,
                "selected_page_number": int(row.get("selected_page_number", 0)) if str(row.get("selected_page_number", "")).isdigit() else 0,
                "n_words": int(row.get("n_words", 0)) if str(row.get("n_words", "")).isdigit() else 0,
            }
    return lookup


def build_toy_chunk_retrieval(sentence_jsonl_path, candidates):
    """Build pseudo chunk retrieval from toy sentence corpus."""
    import json as _json
    sentences = []
    with open(sentence_jsonl_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            sentences.append(_json.loads(line))

    chunks_by_paper_page = defaultdict(list)
    for s in sentences:
        chunks_by_paper_page[(s["paper_id"], s["page_number"])].append(s)

    _TOKEN_RE = re.compile(r"[a-z0-9]+")
    _STOP = {"a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of", "with", "is", "are", "was", "were"}

    def tok(t):
        return [w for w in _TOKEN_RE.findall(t.lower()) if w not in _STOP]

    by_cand = defaultdict(list)
    for cand in candidates:
        cid = cand["candidate_id"]
        claim_t = tok(cand["claim_text"])
        pdf_name = cand["pdf_filename"].replace(".pdf", "")
        candidate_chunks = []
        for (paper_id, page_num), sent_list in chunks_by_paper_page.items():
            if paper_id == pdf_name:
                chunk_text = " ".join(s["clean_text"] for s in sent_list)
                ct = tok(chunk_text)
                overlap = len(set(claim_t) & set(ct))
                score = 2.0 * overlap / (len(set(claim_t)) + len(set(ct))) if (claim_t and ct) else 0.0
                candidate_chunks.append({
                    "candidate_id": cid,
                    "rank": 0,
                    "chunk_id": f"{paper_id}_p{page_num}_c0",
                    "retrieved_text": chunk_text,
                    "page_number": page_num,
                    "_score": score,
                })
        candidate_chunks.sort(key=lambda x: x["_score"], reverse=True)
        for i, ch in enumerate(candidate_chunks, 1):
            ch["rank"] = i
            del ch["_score"]
        by_cand[cid] = candidate_chunks
    return dict(by_cand)


# ---------------------------------------------------------------------------
# Variant construction
# ---------------------------------------------------------------------------

def build_metadata_header(cand):
    """Build lightweight metadata prefix. No labels."""
    title = cand.get("title", "") or "unknown"
    page = cand.get("page_number", 0)
    return f"Title: {title} Page: {page} Section: unknown"


def get_adjacent_text_for_lengthening(cand, chunk_retrieval):
    """Get adjacent retrieved text (rank=2) to simulate lengthening."""
    chunks = chunk_retrieval.get(cand["candidate_id"], [])
    if len(chunks) >= 2:
        return chunks[1]["retrieved_text"]
    return ""


def construct_variants(cand, chunk_retrieval, selector_lookup):
    """Construct all 8 evidence variants for a candidate."""
    cid = cand["candidate_id"]
    evidence_text = cand["evidence_text"]
    metadata = build_metadata_header(cand)
    adjacent = get_adjacent_text_for_lengthening(cand, chunk_retrieval)

    variants = []

    # 1. oracle_clean — diagnostic upper-bound
    variants.append({
        "candidate_id": cid,
        "variant": "oracle_clean",
        "evidence_input": evidence_text,
        "source": "candidate_csv.evidence_text",
        "uses_oracle_text": True,
        "contains_metadata": False,
        "is_lengthened": False,
    })

    # 2. oracle_plus_metadata
    variants.append({
        "candidate_id": cid,
        "variant": "oracle_plus_metadata",
        "evidence_input": f"{metadata}\n{evidence_text}" if evidence_text else metadata,
        "source": "candidate_csv.evidence_text + metadata",
        "uses_oracle_text": True,
        "contains_metadata": True,
        "is_lengthened": False,
    })

    # 3. oracle_lengthened
    lengthened = (evidence_text + " " + adjacent).strip() if adjacent else evidence_text
    variants.append({
        "candidate_id": cid,
        "variant": "oracle_lengthened",
        "evidence_input": lengthened,
        "source": "candidate_csv.evidence_text + adjacent_chunk",
        "uses_oracle_text": True,
        "contains_metadata": False,
        "is_lengthened": True,
    })

    # 4. oracle_plus_metadata_lengthened
    variants.append({
        "candidate_id": cid,
        "variant": "oracle_plus_metadata_lengthened",
        "evidence_input": f"{metadata}\n{lengthened}" if lengthened else metadata,
        "source": "candidate_csv.evidence_text + metadata + adjacent_chunk",
        "uses_oracle_text": True,
        "contains_metadata": True,
        "is_lengthened": True,
    })

    # 5. raw_bm25_top1_chunk
    chunks = chunk_retrieval.get(cid, [])
    raw_text = chunks[0]["retrieved_text"] if chunks else ""
    raw_rank = chunks[0]["rank"] if chunks else 0
    variants.append({
        "candidate_id": cid,
        "variant": "raw_bm25_top1_chunk",
        "evidence_input": raw_text,
        "source": f"chunk_retrieval rank={raw_rank}",
        "uses_oracle_text": False,
        "contains_metadata": False,
        "is_lengthened": False,
    })

    # 6. cleaned_bm25_top1_chunk
    cleaned_text = clean_chunk_text(raw_text)
    variants.append({
        "candidate_id": cid,
        "variant": "cleaned_bm25_top1_chunk",
        "evidence_input": cleaned_text,
        "source": "chunk_retrieval rank=1 (cleaned)",
        "uses_oracle_text": False,
        "contains_metadata": False,
        "is_lengthened": False,
    })

    # 7. canonicalized_best_sentence_top5
    sel = selector_lookup.get((cid, "best_sentence_top5_overlap"), {})
    variants.append({
        "candidate_id": cid,
        "variant": "canonicalized_best_sentence_top5",
        "evidence_input": sel.get("selected_evidence", ""),
        "source": "canonicalizer_ablation best_sentence_top5_overlap",
        "uses_oracle_text": False,
        "contains_metadata": False,
        "is_lengthened": False,
    })

    # 8. canonicalized_three_sentence_window_top5
    sel = selector_lookup.get((cid, "three_sentence_window_top5"), {})
    variants.append({
        "candidate_id": cid,
        "variant": "canonicalized_three_sentence_window_top5",
        "evidence_input": sel.get("selected_evidence", ""),
        "source": "canonicalizer_ablation three_sentence_window_top5",
        "uses_oracle_text": False,
        "contains_metadata": False,
        "is_lengthened": False,
    })

    # Add computed fields
    for v in variants:
        v["evidence_input_sha256"] = sha256_text(v["evidence_input"])
        v["n_words"] = len(v["evidence_input"].split()) if v["evidence_input"] else 0

    return variants


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def write_inputs_csv(filepath, all_variants):
    fields = [
        "candidate_id", "variant", "evidence_input", "evidence_input_sha256",
        "n_words", "source", "uses_oracle_text", "contains_metadata", "is_lengthened",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for v in all_variants:
            writer.writerow({k: v[k] for k in fields})


def write_redacted_csv(filepath, all_variants):
    fields = [
        "candidate_id", "variant", "evidence_input_sha256",
        "n_words", "source", "uses_oracle_text", "contains_metadata", "is_lengthened",
    ]
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for v in all_variants:
            writer.writerow({k: v[k] for k in fields})


def write_config_json(filepath):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(CONFIG, f, indent=2, ensure_ascii=False)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Evidence format-shift ablation: construct 8 variants."
    )
    parser.add_argument("--candidate_csv", default=None)
    parser.add_argument("--chunk_retrieval_csv", default=None)
    parser.add_argument("--selector_variant_csv", default=None)
    parser.add_argument("--output_dir", default=None)
    parser.add_argument("--config", default=None, help="Path to YAML config")
    parser.add_argument("--toy_mode", action="store_true")
    args = parser.parse_args()

    # --- Load config ---
    config = load_and_validate(args.config, toy_mode=args.toy_mode)
    print_guards(config)

    if args.output_dir:
        output_dir = Path(args.output_dir)
    elif args.toy_mode:
        output_dir = Path("experiments/format_shift_ablation_v1_toy")
    else:
        output_dir = Path("experiments/format_shift_ablation_v1")
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.toy_mode:
        candidate_csv = "data/toy_synthetic/toy_candidates_v1.csv"
        sentence_jsonl = "data/pdf_corpus_toy_v1/sentences.jsonl"
        selector_variant_csv = "experiments/canonicalizer_ablation_v1_toy/selector_variant_evidence.csv"
        print("[toy_mode] Using toy inputs")
    else:
        candidate_csv = args.candidate_csv or str(resolve_path(config, "candidate_csv") or "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv")
        canon_dir = resolve_path(config, "canonicalizer_dir") or Path("experiments/canonicalizer_ablation_v1")
        selector_variant_csv = args.selector_variant_csv or str(canon_dir / "selector_variant_evidence.csv")

    # --- Load inputs ---
    print(f"Loading candidates from {candidate_csv}")
    candidates = load_candidates(candidate_csv)
    print(f"  {len(candidates)} candidates loaded")

    if args.toy_mode:
        print(f"Building toy chunk retrieval from {sentence_jsonl}")
        chunk_retrieval = build_toy_chunk_retrieval(sentence_jsonl, candidates)
    else:
        print(f"Loading chunk retrieval from {args.chunk_retrieval_csv}")
        chunk_retrieval = load_chunk_retrieval(args.chunk_retrieval_csv)
    print(f"  {len(chunk_retrieval)} candidates with chunk retrieval")

    print(f"Loading selector variants from {selector_variant_csv}")
    selector_lookup = load_selector_variants(selector_variant_csv)
    print(f"  {len(selector_lookup)} (candidate, selector) pairs loaded")

    # --- Construct variants ---
    print(f"\nConstructing {len(VARIANT_NAMES)} variants ...")
    all_variants = []
    for cand in candidates:
        variants = construct_variants(cand, chunk_retrieval, selector_lookup)
        all_variants.extend(variants)

    # --- Summary ---
    print("\nVariant summary:")
    for vn in VARIANT_NAMES:
        vn_variants = [v for v in all_variants if v["variant"] == vn]
        n = len(vn_variants)
        mean_words = sum(v["n_words"] for v in vn_variants) / n if n else 0
        n_empty = sum(1 for v in vn_variants if v["n_words"] == 0)
        print(f"  {vn}: n={n}, mean_n_words={mean_words:.1f}, empty={n_empty}")

    # --- Write outputs ---
    inputs_csv = output_dir / "format_shift_inputs.csv"
    write_inputs_csv(inputs_csv, all_variants)
    print(f"\nWrote {inputs_csv}")

    redacted_csv = output_dir / "format_shift_inputs_redacted.csv"
    write_redacted_csv(redacted_csv, all_variants)
    print(f"Wrote {redacted_csv}")

    config_json = output_dir / "format_shift_config.json"
    write_config_json(config_json)
    print(f"Wrote {config_json}")

    # --- Schema validation ---
    schema_reports = [
        validate_csv_file(inputs_csv, "format_shift_inputs"),
        validate_redacted_csv_file(redacted_csv, "format_shift_inputs"),
    ]
    write_schema_validation_report(
        output_dir, schema_reports, script_name="run_format_shift_ablation_v1.py"
    )
    print(f"Wrote schema_validation_report.json")

    write_run_config(output_dir, config, "run_format_shift_ablation_v1.py",
                     extra={"toy_mode": args.toy_mode})
    print(f"Wrote run_config.json")

    print("\nNote: oracle_clean is diagnostic upper-bound, NOT production.")
    print("      canonicalized_best_sentence_top5 is the production-like selector.")
    print("Done.")


if __name__ == "__main__":
    main()
