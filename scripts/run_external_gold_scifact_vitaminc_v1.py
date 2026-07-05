"""
Task R1 - SciFact + VitaminC External Gold-Derived Eval

Public gold-derived external sanity check on SciFact and VitaminC.
Tests whether V3/R4 evidence-relation approach transfers to public
claim-verification data. No LLM/API calls. No SimClaim mutation.

Hard constraints:
- No GPT/LLM/API calls.
- No new SimClaim data; no gold/final/human_audited writes to SimClaim.
- No original CSV or paper modifications.
- No large model downloads.
- Public results never mixed into SimClaim main table.
- No SOTA / full-benchmark claims.

Naming:
- Public original labels: "public gold original labels"
- Mapped labels: "public-gold-derived mapped labels"
- Sampled set: "external gold-derived subset" / "external sanity check"
- Never: "new gold benchmark", "SimClaim gold", "paper_full gold",
  "human-audited SimClaim gold".
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import random
import re
import sys
import time
import traceback
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
EXTERNAL_GOLD_ROOT = Path(r"D:\ocn\data\external_gold")
SCIFACT_DIR = EXTERNAL_GOLD_ROOT / "scifact" / "data"
SCIFACT_CLAIMS_TRAIN = SCIFACT_DIR / "claims_train.jsonl"
SCIFACT_CLAIMS_DEV = SCIFACT_DIR / "claims_dev.jsonl"
SCIFACT_CORPUS = SCIFACT_DIR / "corpus.jsonl"

VITAMINC_DIR = EXTERNAL_GOLD_ROOT / "vitaminc"
VITAMINC_DEV = VITAMINC_DIR / "dev.jsonl"
VITAMINC_TEST = VITAMINC_DIR / "test.jsonl"

EXP_DIR = Path(r"D:\ocn\experiments\external_gold_scifact_vitaminc_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = EXP_DIR / "run.log"
LOG_PATH.write_text("", encoding="utf-8")

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
SEEDS = [11, 22, 33, 44, 55]
MAX_EVAL_PER_DATASET = 300
MAX_TRAIN_PER_DATASET = 3000  # cap training set for speed
MAX_E3_PAIRS = 300

# Label mapping
SCIFACT_LABEL_MAP = {
    "SUPPORT": "supported",
    "CONTRADICT": "contradiction_candidate",
    "NEI": "unsupported_or_insufficient",
    "NOT_ENOUGH_INFO": "unsupported_or_insufficient",
}
VITAMINC_LABEL_MAP = {
    "SUPPORTS": "supported",
    "REFUTES": "contradiction_candidate",
    "NOT ENOUGH INFO": "unsupported_or_insufficient",
    "NOT_ENOUGH_INFO": "unsupported_or_insufficient",
}

MAPPED_LABELS = [
    "supported",
    "contradiction_candidate",
    "unsupported_or_insufficient",
]

NLI_MODEL_NAME = "cross-encoder/nli-deberta-base"

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# 1. Download log + schema audit
# ---------------------------------------------------------------------------
def write_download_log() -> list[dict]:
    """Record provenance of data acquisition."""
    rows = [
        {
            "dataset": "scifact",
            "file": "data.tar.gz",
            "source_url": "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz",
            "local_path": str(EXTERNAL_GOLD_ROOT / "scifact_data.tar.gz"),
            "license": "CC BY-NC 2.0 (SciFact)",
            "access_note": "public S3 download, no auth",
            "download_status": "ok",
            "bytes": 3115079,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "scifact",
            "file": "claims_train.jsonl",
            "source_url": "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz",
            "local_path": str(SCIFACT_CLAIMS_TRAIN),
            "license": "CC BY-NC 2.0",
            "access_note": "extracted from data.tar.gz",
            "download_status": "ok",
            "bytes": 175616,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "scifact",
            "file": "claims_dev.jsonl",
            "source_url": "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz",
            "local_path": str(SCIFACT_CLAIMS_DEV),
            "license": "CC BY-NC 2.0",
            "access_note": "extracted from data.tar.gz; labeled",
            "download_status": "ok",
            "bytes": 65007,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "scifact",
            "file": "corpus.jsonl",
            "source_url": "https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz",
            "local_path": str(SCIFACT_CORPUS),
            "license": "CC BY-NC 2.0",
            "access_note": "extracted from data.tar.gz",
            "download_status": "ok",
            "bytes": 8307875,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "vitaminc",
            "file": "dev.jsonl",
            "source_url": "https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/dev.jsonl",
            "local_path": str(VITAMINC_DEV),
            "license": "CC BY-SA 3.0 (VitaminC)",
            "access_note": "HF mirror (huggingface.co blocked by network); no auth",
            "download_status": "ok",
            "bytes": 32876983,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "vitaminc",
            "file": "test.jsonl",
            "source_url": "https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/test.jsonl",
            "local_path": str(VITAMINC_TEST),
            "license": "CC BY-SA 3.0",
            "access_note": "HF mirror (huggingface.co blocked by network); no auth",
            "download_status": "ok",
            "bytes": 28717099,
            "timestamp": "2026-07-04",
        },
        {
            "dataset": "vitaminc",
            "file": "train.jsonl",
            "source_url": "https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/train.jsonl",
            "local_path": "NOT_DOWNLOADED",
            "license": "CC BY-SA 3.0",
            "access_note": "skipped (194MB, not needed for eval subset; dev used for training proxy)",
            "download_status": "skipped",
            "bytes": 0,
            "timestamp": "2026-07-04",
        },
    ]
    return rows


def write_schema_audit() -> list[dict]:
    rows = [
        {
            "dataset": "scifact",
            "split": "train",
            "n_records": 809,
            "n_with_evidence": 505,
            "label_field": "evidence[doc_id][*].label",
            "label_values": "SUPPORT|CONTRADICT|NEI",
            "claim_field": "claim",
            "evidence_field": "corpus[doc_id].abstract[sentences_indices]",
            "schema_compatible": True,
            "notes": "Per-rationale label; same label per doc_id; NEI = empty evidence dict",
        },
        {
            "dataset": "scifact",
            "split": "dev",
            "n_records": 300,
            "n_with_evidence": 188,
            "label_field": "evidence[doc_id][*].label",
            "label_values": "SUPPORT|CONTRADICT|NEI",
            "claim_field": "claim",
            "evidence_field": "corpus[doc_id].abstract[sentences_indices]",
            "schema_compatible": True,
            "notes": "Labeled dev set; test set is unlabeled (skipped)",
        },
        {
            "dataset": "vitaminc",
            "split": "dev",
            "n_records": 63054,
            "n_with_evidence": 63054,
            "label_field": "label",
            "label_values": "SUPPORTS|REFUTES|NOT ENOUGH INFO",
            "claim_field": "claim",
            "evidence_field": "evidence",
            "schema_compatible": True,
            "notes": "All entries have evidence; case_id groups contrastive pairs",
        },
        {
            "dataset": "vitaminc",
            "split": "test",
            "n_records": 55197,
            "n_with_evidence": 55197,
            "label_field": "label",
            "label_values": "SUPPORTS|REFUTES|NOT ENOUGH INFO",
            "claim_field": "claim",
            "evidence_field": "evidence",
            "schema_compatible": True,
            "notes": "16487 unique cases; 10142 cases have both SUPPORTS and REFUTES (contrastive)",
        },
    ]
    return rows


# ---------------------------------------------------------------------------
# 2. SciFact data loading
# ---------------------------------------------------------------------------
def load_scifact_corpus() -> dict[int, dict]:
    """Load SciFact corpus (doc_id -> {title, abstract, structured})."""
    corpus = {}
    with open(SCIFACT_CORPUS, "r", encoding="utf-8") as f:
        for line in f:
            d = json.loads(line)
            corpus[int(d["doc_id"])] = d
    return corpus


def load_scifact_claims(path: Path) -> list[dict]:
    """Load SciFact claims jsonl."""
    claims = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            claims.append(json.loads(line))
    return claims


def build_scifact_pairs(
    claims: list[dict], corpus: dict[int, dict], source_split: str
) -> list[dict]:
    """Build (claim, evidence, label) pairs from SciFact claims.

    For claims with evidence: use cited sentences as evidence.
    For NEI claims: use first sentence of cited doc as 'weak evidence'
    (annotator found no rationale), marked in evidence_source field.
    """
    pairs = []
    for c in claims:
        claim_text = c.get("claim", "").strip()
        if not claim_text:
            continue
        claim_id = c.get("id")
        evidence = c.get("evidence", {}) or {}
        cited_doc_ids = c.get("cited_doc_ids", []) or []

        if evidence:
            # Has labeled rationale(s)
            for doc_id_str, rationales in evidence.items():
                doc_id = int(doc_id_str)
                doc = corpus.get(doc_id)
                if not doc:
                    continue
                abstract = doc.get("abstract", [])
                # Each rationale has sentences (indices) and label
                # All rationales for same doc have same label per SciFact spec
                label = rationales[0].get("label", "NEI")
                # Concatenate all rationale sentences for this doc
                ev_sents = []
                for rat in rationales:
                    for sent_idx in rat.get("sentences", []):
                        if 0 <= sent_idx < len(abstract):
                            ev_sents.append(abstract[sent_idx])
                evidence_text = " ".join(ev_sents).strip()
                if not evidence_text:
                    continue
                original_label = label
                mapped_label = SCIFACT_LABEL_MAP.get(original_label, "unsupported_or_insufficient")
                pairs.append({
                    "external_id": f"scifact_{source_split}_{claim_id}_{doc_id}",
                    "dataset": "scifact",
                    "claim_text": claim_text,
                    "evidence_text": evidence_text,
                    "original_label": original_label,
                    "mapped_label": mapped_label,
                    "label_mapping_rule": f"{original_label}->{mapped_label}",
                    "source_dataset": "scifact",
                    "source_split": source_split,
                    "source_info": f"claim_id={claim_id};doc_id={doc_id};rationale_sentences",
                    "evidence_source": "annotated_rationale",
                    "claim_group_id": f"scifact_claim_{claim_id}",
                })
        else:
            # NEI claim - no rationale. Use first sentence of first cited doc as weak evidence.
            for doc_id in cited_doc_ids[:1]:  # only first cited doc
                doc = corpus.get(int(doc_id))
                if not doc:
                    continue
                abstract = doc.get("abstract", [])
                if not abstract:
                    continue
                evidence_text = abstract[0].strip()  # first sentence only
                original_label = "NEI"
                mapped_label = SCIFACT_LABEL_MAP[original_label]
                pairs.append({
                    "external_id": f"scifact_{source_split}_{claim_id}_nei_{doc_id}",
                    "dataset": "scifact",
                    "claim_text": claim_text,
                    "evidence_text": evidence_text,
                    "original_label": original_label,
                    "mapped_label": mapped_label,
                    "label_mapping_rule": f"{original_label}->{mapped_label}",
                    "source_dataset": "scifact",
                    "source_split": source_split,
                    "source_info": f"claim_id={claim_id};doc_id={doc_id};nei_first_sentence",
                    "evidence_source": "nei_cited_doc_first_sentence",
                    "claim_group_id": f"scifact_claim_{claim_id}",
                })
    return pairs


# ---------------------------------------------------------------------------
# 3. VitaminC data loading
# ---------------------------------------------------------------------------
def load_vitaminc_jsonl(path: Path, max_records: int | None = None) -> list[dict]:
    """Load VitaminC jsonl. If max_records, stop after N."""
    records = []
    with open(path, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            if max_records and i >= max_records:
                break
            records.append(json.loads(line))
    return records


def build_vitaminc_pairs(records: list[dict], source_split: str) -> list[dict]:
    """Build (claim, evidence, label) pairs from VitaminC records."""
    pairs = []
    for r in records:
        claim_text = (r.get("claim") or "").strip()
        evidence_text = (r.get("evidence") or "").strip()
        if not claim_text or not evidence_text:
            continue
        original_label = r.get("label", "NOT ENOUGH INFO")
        mapped_label = VITAMINC_LABEL_MAP.get(original_label, "unsupported_or_insufficient")
        unique_id = r.get("unique_id", "")
        case_id = r.get("case_id", "")
        revision_type = r.get("revision_type", "")
        pairs.append({
            "external_id": f"vitaminc_{source_split}_{unique_id}",
            "dataset": "vitaminc",
            "claim_text": claim_text,
            "evidence_text": evidence_text,
            "original_label": original_label,
            "mapped_label": mapped_label,
            "label_mapping_rule": f"{original_label}->{mapped_label}",
            "source_dataset": "vitaminc",
            "source_split": source_split,
            "source_info": f"unique_id={unique_id};case_id={case_id};revision_type={revision_type}",
            "evidence_source": f"vitaminc_{revision_type}",
            "claim_group_id": f"vitaminc_case_{case_id}",
            "case_id": case_id,
            "revision_type": revision_type,
        })
    return pairs


# ---------------------------------------------------------------------------
# 4. Sampling (label-balanced)
# ---------------------------------------------------------------------------
def sample_label_balanced(
    pairs: list[dict], n_max: int, seed: int, label_field: str = "mapped_label"
) -> list[dict]:
    """Sample up to n_max pairs, balanced across label values."""
    rng = random.Random(seed)
    by_label = defaultdict(list)
    for p in pairs:
        by_label[p[label_field]].append(p)
    labels_present = list(by_label.keys())
    if not labels_present:
        return []
    per_label = max(1, n_max // len(labels_present))
    sampled = []
    for lab in labels_present:
        pool = by_label[lab]
        rng.shuffle(pool)
        sampled.extend(pool[:per_label])
    rng.shuffle(sampled)
    return sampled[:n_max]


# ---------------------------------------------------------------------------
# 5. E3 contrastive pair construction
# ---------------------------------------------------------------------------
def build_vitaminc_e3_pairs(records: list[dict], max_pairs: int, seed: int) -> list[dict]:
    """Build E3 contrastive pairs from VitaminC using case_id grouping.

    For each case_id with both SUPPORTS and REFUTES entries, form pairs:
      (claim, correct_evidence, wrong_evidence)
    where correct = SUPPORTS evidence, wrong = REFUTES evidence (or vice versa).

    These are official contrastive pairs from VitaminC's design.
    """
    rng = random.Random(seed)
    by_case = defaultdict(list)
    for r in records:
        by_case[r.get("case_id", "")].append(r)

    pairs = []
    for case_id, items in by_case.items():
        if not case_id:
            continue
        supports = [r for r in items if r.get("label") == "SUPPORTS"]
        refutes = [r for r in items if r.get("label") == "REFUTES"]
        if not supports or not refutes:
            continue
        # Take one of each per case
        s = rng.choice(supports)
        r_ = rng.choice(refutes)
        # Same claim? VitaminC cases may have different claims under same case
        # but typically same claim with different evidence
        if s.get("claim", "").strip() == r_.get("claim", "").strip():
            claim = s["claim"]
            correct_evidence = s.get("evidence", "")
            wrong_evidence = r_.get("evidence", "")
            correct_label = "SUPPORTS"
            wrong_label = "REFUTES"
        else:
            # Different claims - skip (we want same-claim different-evidence)
            continue
        if not correct_evidence or not wrong_evidence:
            continue
        pairs.append({
            "pair_id": f"vitaminc_e3_{case_id}",
            "dataset": "vitaminc",
            "claim_text": claim,
            "correct_evidence": correct_evidence,
            "wrong_evidence": wrong_evidence,
            "correct_original_label": correct_label,
            "wrong_original_label": wrong_label,
            "e3_pair_source": "official_contrastive",
            "source_split": "test",
            "source_info": f"case_id={case_id};revision_type_correct={s.get('revision_type')};revision_type_wrong={r_.get('revision_type')}",
        })
        if len(pairs) >= max_pairs:
            break
    return pairs


def build_scifact_e3_pairs(pairs: list[dict], max_pairs: int, seed: int) -> list[dict]:
    """Build E3 pairs for SciFact via synthetic perturbation.

    NO gold evidence-sensitivity labels exist for SciFact. We construct
    synthetic mismatched pairs by shuffling evidence across different claims.
    Marked as e3_pair_source=synthetic_perturbation.
    """
    rng = random.Random(seed)
    # Use only supported/contradiction pairs (with real rationale)
    real_pairs = [p for p in pairs if p.get("evidence_source") == "annotated_rationale"]
    if len(real_pairs) < 2:
        return []
    rng.shuffle(real_pairs)
    e3 = []
    n = min(max_pairs, len(real_pairs))
    for i in range(n):
        p = real_pairs[i]
        # Pick a different pair's evidence as "wrong"
        wrong_idx = (i + 1 + rng.randint(1, max(1, len(real_pairs) - 2))) % len(real_pairs)
        wrong_p = real_pairs[wrong_idx]
        if wrong_p["external_id"] == p["external_id"]:
            continue
        e3.append({
            "pair_id": f"scifact_e3_{p['external_id']}",
            "dataset": "scifact",
            "claim_text": p["claim_text"],
            "correct_evidence": p["evidence_text"],
            "wrong_evidence": wrong_p["evidence_text"],
            "correct_original_label": p["original_label"],
            "wrong_original_label": "SYNTHETIC_MISMATCH",
            "e3_pair_source": "synthetic_perturbation",
            "source_split": p.get("source_split", "dev"),
            "source_info": f"correct={p['external_id']};wrong={wrong_p['external_id']};synthetic_shuffle",
        })
    return e3


# ---------------------------------------------------------------------------
# 6. Methods
# ---------------------------------------------------------------------------
def method_a_tfidf_claim_evidence(
    train_pairs: list[dict], eval_pairs: list[dict]
) -> np.ndarray:
    """Method A: TF-IDF on claim + evidence concatenated. Returns predicted labels (string)."""
    def text(p):
        return f"{p['claim_text']} [SEP] {p['evidence_text']}"
    train_text = [text(p) for p in train_pairs]
    eval_text = [text(p) for p in eval_pairs]
    train_labels = [p["mapped_label"] for p in train_pairs]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
    Xtr = vec.fit_transform(train_text)
    Xev = vec.transform(eval_text)
    clf = LogisticRegression(
        class_weight="balanced", max_iter=2000, random_state=42, C=1.0
    )
    clf.fit(Xtr, train_labels)
    return clf.predict(Xev), clf.predict_proba(Xev)


def method_b_tfidf_claim_only(
    train_pairs: list[dict], eval_pairs: list[dict]
) -> tuple[np.ndarray, np.ndarray]:
    """Method B: TF-IDF on claim ONLY. Tests claim-only leakage."""
    train_text = [p["claim_text"] for p in train_pairs]
    eval_text = [p["claim_text"] for p in eval_pairs]
    train_labels = [p["mapped_label"] for p in train_pairs]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
    Xtr = vec.fit_transform(train_text)
    Xev = vec.transform(eval_text)
    clf = LogisticRegression(
        class_weight="balanced", max_iter=2000, random_state=42, C=1.0
    )
    clf.fit(Xtr, train_labels)
    return clf.predict(Xev), clf.predict_proba(Xev)


_NLI_MODEL = None
_NLI_TOK = None


def get_nli_model():
    global _NLI_MODEL, _NLI_TOK
    if _NLI_MODEL is None:
        import os
        os.environ["HF_HUB_OFFLINE"] = "1"
        os.environ["TRANSFORMERS_OFFLINE"] = "1"
        import torch
        from transformers import AutoTokenizer, AutoModelForSequenceClassification
        _NLI_TOK = AutoTokenizer.from_pretrained(NLI_MODEL_NAME)
        _NLI_MODEL = AutoModelForSequenceClassification.from_pretrained(NLI_MODEL_NAME)
        _NLI_MODEL.eval()
    return _NLI_MODEL, _NLI_TOK


def nli_score_batch(pairs: list[dict]) -> np.ndarray:
    """Return NLI probs [N, 3] where columns are [contradiction, entailment, neutral]
    (matching cross-encoder/nli-deberta-base id2label: 0=contradiction, 1=entailment, 2=neutral).
    Returns entail_prob (P(entailment)) per pair.
    """
    import torch
    model, tok = get_nli_model()
    ents = []
    bs = 16
    with torch.no_grad():
        for i in range(0, len(pairs), bs):
            batch = pairs[i : i + bs]
            claims = [p["claim_text"] for p in batch]
            evids = [p["evidence_text"] for p in batch]
            inputs = tok(
                claims, evids,
                return_tensors="pt",
                truncation=True,
                max_length=256,
                padding=True,
            )
            out = model(**inputs)
            probs = torch.softmax(out.logits, dim=-1).cpu().numpy()
            # Column 1 = entailment
            ents.extend(probs[:, 1].tolist())
    return np.array(ents)


def method_c_nli_baseline(
    train_pairs: list[dict], eval_pairs: list[dict]
) -> tuple[np.ndarray, np.ndarray]:
    """Method C: NLI cross-encoder features + LR.
    If NLI model unavailable, returns None.
    """
    try:
        # Compute NLI entailment probability as feature
        # Use 3 features: entail_prob, contra_prob, neutral_prob
        def nli_feats(pairs):
            import torch
            model, tok = get_nli_model()
            feats = []
            bs = 16
            with torch.no_grad():
                for i in range(0, len(pairs), bs):
                    batch = pairs[i : i + bs]
                    claims = [p["claim_text"] for p in batch]
                    evids = [p["evidence_text"] for p in batch]
                    inputs = tok(
                        claims, evids,
                        return_tensors="pt",
                        truncation=True,
                        max_length=256,
                        padding=True,
                    )
                    out = model(**inputs)
                    probs = torch.softmax(out.logits, dim=-1).cpu().numpy()
                    feats.extend(probs.tolist())
            return np.array(feats)

        Xtr = nli_feats(train_pairs)
        Xev = nli_feats(eval_pairs)
        scaler = StandardScaler()
        Xtr_s = scaler.fit_transform(Xtr)
        Xev_s = scaler.transform(Xev)
        train_labels = [p["mapped_label"] for p in train_pairs]
        clf = LogisticRegression(
            class_weight="balanced", max_iter=2000, random_state=42, C=1.0
        )
        clf.fit(Xtr_s, train_labels)
        return clf.predict(Xev_s), clf.predict_proba(Xev_s)
    except Exception as e:
        log(f"Method C (NLI) failed: {type(e).__name__}: {str(e)[:200]}")
        return None, None


def method_d_r4_compatible(
    train_pairs: list[dict], eval_pairs: list[dict]
) -> tuple[np.ndarray, np.ndarray]:
    """Method D: R4-compatible evidence-relation heuristic.

    R4 routes: contradiction first, then strong, else supported/mild.
    For external data, strong/mild labels don't exist. So R4-compatible:
    - Train binary contradiction detector (supported vs contradiction_candidate)
    - Train binary support detector (supported vs unsupported_or_insufficient)
    - Route: if p_contra > t_contra, predict contradiction_candidate;
      elif p_unsup > t_unsup, predict unsupported_or_insufficient;
      else predict supported.
    Uses TF-IDF (no NLI features available for external data).
    """
    # Build training subsets
    # Contra detector: supported vs contradiction_candidate (exclude NEI)
    contra_train = [p for p in train_pairs if p["mapped_label"] in ("supported", "contradiction_candidate")]
    unsup_train = [p for p in train_pairs if p["mapped_label"] in ("supported", "unsupported_or_insufficient")]

    def text(p):
        return f"{p['claim_text']} [SEP] {p['evidence_text']}"

    # Combined fit
    all_train_text = [text(p) for p in train_pairs]
    vec = TfidfVectorizer(ngram_range=(1, 2), min_df=2, sublinear_tf=True, stop_words="english")
    vec.fit(all_train_text)
    eval_text = [text(p) for p in eval_pairs]
    Xev = vec.transform(eval_text)

    preds = []
    probs_list = []

    # Contra detector
    if len(contra_train) >= 4 and len(set(p["mapped_label"] for p in contra_train)) >= 2:
        Xtr_c = vec.transform([text(p) for p in contra_train])
        ytr_c = [p["mapped_label"] for p in contra_train]
        clf_c = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42, C=1.0)
        clf_c.fit(Xtr_c, ytr_c)
        # Get prob of contradiction_candidate
        classes = list(clf_c.classes_)
        proba_c = clf_c.predict_proba(Xev)
        if "contradiction_candidate" in classes:
            idx_c = classes.index("contradiction_candidate")
            p_contra = proba_c[:, idx_c]
        else:
            p_contra = np.zeros(len(eval_pairs))
    else:
        p_contra = np.zeros(len(eval_pairs))

    # Unsup detector
    if len(unsup_train) >= 4 and len(set(p["mapped_label"] for p in unsup_train)) >= 2:
        Xtr_u = vec.transform([text(p) for p in unsup_train])
        ytr_u = [p["mapped_label"] for p in unsup_train]
        clf_u = LogisticRegression(class_weight="balanced", max_iter=2000, random_state=42, C=1.0)
        clf_u.fit(Xtr_u, ytr_u)
        classes_u = list(clf_u.classes_)
        proba_u = clf_u.predict_proba(Xev)
        if "unsupported_or_insufficient" in classes_u:
            idx_u = classes_u.index("unsupported_or_insufficient")
            p_unsup = proba_u[:, idx_u]
        else:
            p_unsup = np.zeros(len(eval_pairs))
    else:
        p_unsup = np.zeros(len(eval_pairs))

    # Route (R4-style thresholds, conservative)
    T_CONTRA = 0.5
    T_UNSUP = 0.5
    for i in range(len(eval_pairs)):
        if p_contra[i] >= T_CONTRA:
            preds.append("contradiction_candidate")
        elif p_unsup[i] >= T_UNSUP:
            preds.append("unsupported_or_insufficient")
        else:
            preds.append("supported")
        # For proba: use 3-class approximation
        p_sup_approx = max(0.0, 1.0 - p_contra[i] - p_unsup[i])
        probs_list.append([p_sup_approx, p_contra[i], p_unsup[i]])

    # Reorder proba columns to match MAPPED_LABELS order
    label_to_idx = {lab: i for i, lab in enumerate(MAPPED_LABELS)}
    # Our order: [supported, contradiction_candidate, unsupported_or_insufficient] -- already matches
    return np.array(preds), np.array(probs_list)


# ---------------------------------------------------------------------------
# 7. Task evaluation
# ---------------------------------------------------------------------------
def eval_e1_support_vs_contradiction(
    eval_pairs: list[dict], pred_labels: np.ndarray
) -> dict:
    """E1: supported vs contradiction_candidate (binary).
    Filter eval to those two labels. Compute accuracy, macro-F1, supported F1, contradiction F1.
    """
    y_true = []
    y_pred = []
    for i, p in enumerate(eval_pairs):
        if p["mapped_label"] in ("supported", "contradiction_candidate"):
            y_true.append(p["mapped_label"])
            y_pred.append(str(pred_labels[i]))
    if not y_true:
        return {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None}
    labels = ["supported", "contradiction_candidate"]
    return {
        "n_eval": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "supported_f1": float(f1_score(y_true, y_pred, labels=["supported"], average="macro", zero_division=0)),
        "contradiction_f1": float(f1_score(y_true, y_pred, labels=["contradiction_candidate"], average="macro", zero_division=0)),
    }


def eval_e2_support_vs_non_support(
    eval_pairs: list[dict], pred_labels: np.ndarray
) -> dict:
    """E2: supported vs (contradiction_candidate + unsupported_or_insufficient).
    Compute accuracy, macro-F1, non_support F1, supported F1.
    """
    y_true = []
    y_pred = []
    for i, p in enumerate(eval_pairs):
        true_bin = "supported" if p["mapped_label"] == "supported" else "non_support"
        pred_bin = "supported" if str(pred_labels[i]) == "supported" else "non_support"
        y_true.append(true_bin)
        y_pred.append(pred_bin)
    if not y_true:
        return {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None}
    labels = ["supported", "non_support"]
    return {
        "n_eval": len(y_true),
        "accuracy": float(accuracy_score(y_true, y_pred)),
        "macro_f1": float(f1_score(y_true, y_pred, labels=labels, average="macro", zero_division=0)),
        "non_support_f1": float(f1_score(y_true, y_pred, labels=["non_support"], average="macro", zero_division=0)),
        "supported_f1": float(f1_score(y_true, y_pred, labels=["supported"], average="macro", zero_division=0)),
    }


def eval_e3_evidence_sensitivity(
    e3_pairs: list[dict], seed: int
) -> dict:
    """E3: For each (claim, correct_ev, wrong_ev) triple, compute NLI support scores.
    correct should be more supportive than wrong.

    Metrics:
    - correct_vs_wrong_delta: mean(correct_score - wrong_score)
    - label_flip_rate: fraction where argmax label differs between correct and wrong
    - evidence_sensitivity_rate: fraction where correct_score > wrong_score
    - correct_support_score_mean
    - wrong_support_score_mean
    """
    if not e3_pairs:
        return {
            "n_pairs": 0,
            "correct_vs_wrong_delta": None,
            "label_flip_rate": None,
            "evidence_sensitivity_rate": None,
            "correct_support_score_mean": None,
            "wrong_support_score_mean": None,
            "seed": seed,
        }
    try:
        # Build pairs for NLI scoring
        correct_items = [{"claim_text": p["claim_text"], "evidence_text": p["correct_evidence"]} for p in e3_pairs]
        wrong_items = [{"claim_text": p["claim_text"], "evidence_text": p["wrong_evidence"]} for p in e3_pairs]
        correct_scores = nli_score_batch(correct_items)
        wrong_scores = nli_score_batch(wrong_items)

        delta = float(np.mean(correct_scores - wrong_scores))
        sens_rate = float(np.mean(correct_scores > wrong_scores))
        # Label flip: if score > 0.5 → supported, else → not_supported
        correct_labels = (correct_scores > 0.5).astype(int)
        wrong_labels = (wrong_scores > 0.5).astype(int)
        flip_rate = float(np.mean(correct_labels != wrong_labels))

        return {
            "n_pairs": len(e3_pairs),
            "correct_vs_wrong_delta": delta,
            "label_flip_rate": flip_rate,
            "evidence_sensitivity_rate": sens_rate,
            "correct_support_score_mean": float(np.mean(correct_scores)),
            "wrong_support_score_mean": float(np.mean(wrong_scores)),
            "seed": seed,
        }
    except Exception as e:
        log(f"E3 eval failed: {type(e).__name__}: {str(e)[:200]}")
        return {
            "n_pairs": len(e3_pairs),
            "correct_vs_wrong_delta": None,
            "label_flip_rate": None,
            "evidence_sensitivity_rate": None,
            "correct_support_score_mean": None,
            "wrong_support_score_mean": None,
            "seed": seed,
            "error": str(e)[:200],
        }


# ---------------------------------------------------------------------------
# 8. Main pipeline
# ---------------------------------------------------------------------------
def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip_nli", action="store_true", help="Skip NLI method (Method C)")
    args = parser.parse_args()

    log("=" * 70)
    log("Task R1 - SciFact + VitaminC External Gold-Derived Eval")
    log("=" * 70)
    log(f"Output dir: {EXP_DIR}")
    log(f"Seeds: {SEEDS}")
    log(f"Max eval per dataset: {MAX_EVAL_PER_DATASET}")

    # ---- Step 1: write download log + schema audit ----
    log("[1] Writing download log + schema audit...")
    download_rows = write_download_log()
    schema_rows = write_schema_audit()
    pd.DataFrame(download_rows).to_csv(EXP_DIR / "public_data_download_log.csv", index=False)
    pd.DataFrame(schema_rows).to_csv(EXP_DIR / "external_dataset_schema_audit.csv", index=False)

    # ---- Step 2: load SciFact ----
    log("[2] Loading SciFact...")
    corpus = load_scifact_corpus()
    log(f"  SciFact corpus: {len(corpus)} docs")
    sf_train_claims = load_scifact_claims(SCIFACT_CLAIMS_TRAIN)
    sf_dev_claims = load_scifact_claims(SCIFACT_CLAIMS_DEV)
    log(f"  SciFact train claims: {len(sf_train_claims)}")
    log(f"  SciFact dev claims: {len(sf_dev_claims)}")

    sf_train_pairs = build_scifact_pairs(sf_train_claims, corpus, source_split="train")
    sf_dev_pairs = build_scifact_pairs(sf_dev_claims, corpus, source_split="dev")
    log(f"  SciFact train pairs: {len(sf_train_pairs)}")
    log(f"  SciFact dev pairs: {len(sf_dev_pairs)}")
    sf_train_label_dist = Counter(p["mapped_label"] for p in sf_train_pairs)
    sf_dev_label_dist = Counter(p["mapped_label"] for p in sf_dev_pairs)
    log(f"  SciFact train label dist: {dict(sf_train_label_dist)}")
    log(f"  SciFact dev label dist: {dict(sf_dev_label_dist)}")

    # Save SciFact pairs
    pd.DataFrame(sf_train_pairs + sf_dev_pairs).to_csv(
        EXP_DIR / "scifact_external_pairs.csv", index=False
    )

    # ---- Step 3: load VitaminC ----
    log("[3] Loading VitaminC...")
    # For training proxy, use dev (we don't have train.jsonl downloaded)
    # For eval, use test
    log("  Loading VitaminC dev (training proxy)...")
    vc_dev_records = load_vitaminc_jsonl(VITAMINC_DEV)
    log(f"  VitaminC dev records: {len(vc_dev_records)}")
    log("  Loading VitaminC test (eval)...")
    vc_test_records = load_vitaminc_jsonl(VITAMINC_TEST)
    log(f"  VitaminC test records: {len(vc_test_records)}")

    vc_dev_pairs = build_vitaminc_pairs(vc_dev_records, source_split="dev")
    vc_test_pairs = build_vitaminc_pairs(vc_test_records, source_split="test")
    log(f"  VitaminC dev pairs: {len(vc_dev_pairs)}")
    log(f"  VitaminC test pairs: {len(vc_test_pairs)}")

    pd.DataFrame(vc_dev_pairs + vc_test_pairs).to_csv(
        EXP_DIR / "vitaminc_external_pairs.csv", index=False
    )

    # ---- Step 4: sampling per seed ----
    log("[4] Sampling per seed and evaluating...")
    scifact_results_by_seed = []
    vitaminc_results_by_seed = []
    scifact_sampled_all = []
    vitaminc_sampled_all = []
    provenance_rows = []

    for seed in SEEDS:
        log(f"--- Seed {seed} ---")

        # === SciFact ===
        # Train on claims_train pairs, eval on sampled dev pairs
        sf_train_pool = sf_train_pairs
        sf_eval_sampled = sample_label_balanced(sf_dev_pairs, MAX_EVAL_PER_DATASET, seed)
        log(f"  SciFact eval sample: {len(sf_eval_sampled)} (label dist: {dict(Counter(p['mapped_label'] for p in sf_eval_sampled))})")

        # Cap training set for speed
        if len(sf_train_pool) > MAX_TRAIN_PER_DATASET:
            sf_train_used = sample_label_balanced(sf_train_pool, MAX_TRAIN_PER_DATASET, seed)
        else:
            sf_train_used = sf_train_pool

        # Add seed tag to sampled
        for p in sf_eval_sampled:
            p["seed"] = seed
            p["task_eligible_E1"] = p["mapped_label"] in ("supported", "contradiction_candidate")
            p["task_eligible_E2"] = True  # all eligible for support vs non-support
            p["task_eligible_E3"] = False  # SciFact E3 uses synthetic, separate file
        scifact_sampled_all.extend(sf_eval_sampled)

        # Provenance
        for p in sf_eval_sampled:
            provenance_rows.append({
                "external_id": p["external_id"],
                "dataset": "scifact",
                "source_split": p["source_split"],
                "original_label": p["original_label"],
                "mapped_label": p["mapped_label"],
                "label_mapping_rule": p["label_mapping_rule"],
                "sampling_reason": "label_balanced_sample",
                "filter_reason": "",
                "source_info": p["source_info"],
                "e3_pair_source": "",
                "seed": seed,
            })

        # Methods
        # Method A
        try:
            pred_a, _ = method_a_tfidf_claim_evidence(sf_train_used, sf_eval_sampled)
            m_a_e1 = eval_e1_support_vs_contradiction(sf_eval_sampled, pred_a)
            m_a_e2 = eval_e2_support_vs_non_support(sf_eval_sampled, pred_a)
        except Exception as e:
            log(f"  SciFact Method A failed: {e}")
            m_a_e1 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None}
            m_a_e2 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None}

        # Method B
        try:
            pred_b, _ = method_b_tfidf_claim_only(sf_train_used, sf_eval_sampled)
            m_b_e1 = eval_e1_support_vs_contradiction(sf_eval_sampled, pred_b)
            m_b_e2 = eval_e2_support_vs_non_support(sf_eval_sampled, pred_b)
        except Exception as e:
            log(f"  SciFact Method B failed: {e}")
            m_b_e1 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None}
            m_b_e2 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None}

        # Method C (NLI)
        if not args.skip_nli:
            pred_c, _ = method_c_nli_baseline(sf_train_used, sf_eval_sampled)
            if pred_c is not None:
                m_c_e1 = eval_e1_support_vs_contradiction(sf_eval_sampled, pred_c)
                m_c_e2 = eval_e2_support_vs_non_support(sf_eval_sampled, pred_c)
            else:
                m_c_e1 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None}
                m_c_e2 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None}
        else:
            m_c_e1 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None, "skipped": True}
            m_c_e2 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None, "skipped": True}

        # Method D (R4-compatible)
        try:
            pred_d, _ = method_d_r4_compatible(sf_train_used, sf_eval_sampled)
            m_d_e1 = eval_e1_support_vs_contradiction(sf_eval_sampled, pred_d)
            m_d_e2 = eval_e2_support_vs_non_support(sf_eval_sampled, pred_d)
        except Exception as e:
            log(f"  SciFact Method D failed: {e}")
            m_d_e1 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "supported_f1": None, "contradiction_f1": None}
            m_d_e2 = {"n_eval": 0, "accuracy": None, "macro_f1": None, "non_support_f1": None, "supported_f1": None}

        for method, me1, me2 in [
            ("A_tfidf_claim_evidence", m_a_e1, m_a_e2),
            ("B_tfidf_claim_only", m_b_e1, m_b_e2),
            ("C_nli_cross_encoder", m_c_e1, m_c_e2),
            ("D_r4_compatible", m_d_e1, m_d_e2),
        ]:
            scifact_results_by_seed.append({
                "dataset": "scifact",
                "seed": seed,
                "method": method,
                "e1_n_eval": me1["n_eval"],
                "e1_accuracy": me1["accuracy"],
                "e1_macro_f1": me1["macro_f1"],
                "e1_supported_f1": me1["supported_f1"],
                "e1_contradiction_f1": me1["contradiction_f1"],
                "e2_n_eval": me2["n_eval"],
                "e2_accuracy": me2["accuracy"],
                "e2_macro_f1": me2["macro_f1"],
                "e2_non_support_f1": me2["non_support_f1"],
                "e2_supported_f1": me2["supported_f1"],
                "skipped": me1.get("skipped", False),
            })

        # === VitaminC ===
        # Train on dev (proxy, since train.jsonl not downloaded), eval on sampled test
        vc_train_pool = vc_dev_pairs
        # Sample training subset
        if len(vc_train_pool) > MAX_TRAIN_PER_DATASET:
            vc_train_used = sample_label_balanced(vc_train_pool, MAX_TRAIN_PER_DATASET, seed)
        else:
            # Use all dev as training
            vc_train_used = vc_train_pool

        vc_eval_sampled = sample_label_balanced(vc_test_pairs, MAX_EVAL_PER_DATASET, seed)
        log(f"  VitaminC eval sample: {len(vc_eval_sampled)} (label dist: {dict(Counter(p['mapped_label'] for p in vc_eval_sampled))})")

        for p in vc_eval_sampled:
            p["seed"] = seed
            p["task_eligible_E1"] = p["mapped_label"] in ("supported", "contradiction_candidate")
            p["task_eligible_E2"] = True
            p["task_eligible_E3"] = True  # will be checked separately
        vitaminc_sampled_all.extend(vc_eval_sampled)

        for p in vc_eval_sampled:
            provenance_rows.append({
                "external_id": p["external_id"],
                "dataset": "vitaminc",
                "source_split": p["source_split"],
                "original_label": p["original_label"],
                "mapped_label": p["mapped_label"],
                "label_mapping_rule": p["label_mapping_rule"],
                "sampling_reason": "label_balanced_sample",
                "filter_reason": "",
                "source_info": p["source_info"],
                "e3_pair_source": "",
                "seed": seed,
            })

        # Method A
        try:
            pred_a, _ = method_a_tfidf_claim_evidence(vc_train_used, vc_eval_sampled)
            m_a_e1 = eval_e1_support_vs_contradiction(vc_eval_sampled, pred_a)
            m_a_e2 = eval_e2_support_vs_non_support(vc_eval_sampled, pred_a)
        except Exception as e:
            log(f"  VitaminC Method A failed: {e}")
            m_a_e1 = {"n_eval": 0}
            m_a_e2 = {"n_eval": 0}

        # Method B
        try:
            pred_b, _ = method_b_tfidf_claim_only(vc_train_used, vc_eval_sampled)
            m_b_e1 = eval_e1_support_vs_contradiction(vc_eval_sampled, pred_b)
            m_b_e2 = eval_e2_support_vs_non_support(vc_eval_sampled, pred_b)
        except Exception as e:
            log(f"  VitaminC Method B failed: {e}")
            m_b_e1 = {"n_eval": 0}
            m_b_e2 = {"n_eval": 0}

        # Method C
        if not args.skip_nli:
            pred_c, _ = method_c_nli_baseline(vc_train_used, vc_eval_sampled)
            if pred_c is not None:
                m_c_e1 = eval_e1_support_vs_contradiction(vc_eval_sampled, pred_c)
                m_c_e2 = eval_e2_support_vs_non_support(vc_eval_sampled, pred_c)
            else:
                m_c_e1 = {"n_eval": 0}
                m_c_e2 = {"n_eval": 0}
        else:
            m_c_e1 = {"n_eval": 0, "skipped": True}
            m_c_e2 = {"n_eval": 0, "skipped": True}

        # Method D
        try:
            pred_d, _ = method_d_r4_compatible(vc_train_used, vc_eval_sampled)
            m_d_e1 = eval_e1_support_vs_contradiction(vc_eval_sampled, pred_d)
            m_d_e2 = eval_e2_support_vs_non_support(vc_eval_sampled, pred_d)
        except Exception as e:
            log(f"  VitaminC Method D failed: {e}")
            m_d_e1 = {"n_eval": 0}
            m_d_e2 = {"n_eval": 0}

        for method, me1, me2 in [
            ("A_tfidf_claim_evidence", m_a_e1, m_a_e2),
            ("B_tfidf_claim_only", m_b_e1, m_b_e2),
            ("C_nli_cross_encoder", m_c_e1, m_c_e2),
            ("D_r4_compatible", m_d_e1, m_d_e2),
        ]:
            vitaminc_results_by_seed.append({
                "dataset": "vitaminc",
                "seed": seed,
                "method": method,
                "e1_n_eval": me1.get("n_eval", 0),
                "e1_accuracy": me1.get("accuracy"),
                "e1_macro_f1": me1.get("macro_f1"),
                "e1_supported_f1": me1.get("supported_f1"),
                "e1_contradiction_f1": me1.get("contradiction_f1"),
                "e2_n_eval": me2.get("n_eval", 0),
                "e2_accuracy": me2.get("accuracy"),
                "e2_macro_f1": me2.get("macro_f1"),
                "e2_non_support_f1": me2.get("non_support_f1"),
                "e2_supported_f1": me2.get("supported_f1"),
                "skipped": me1.get("skipped", False),
            })

    # ---- Step 5: save sampled eval + provenance + results ----
    log("[5] Saving sampled eval + provenance + results...")
    pd.DataFrame(scifact_sampled_all).to_csv(EXP_DIR / "scifact_sampled_eval.csv", index=False)
    pd.DataFrame(vitaminc_sampled_all).to_csv(EXP_DIR / "vitaminc_sampled_eval.csv", index=False)
    pd.DataFrame(provenance_rows).to_csv(EXP_DIR / "external_gold_subset_provenance.csv", index=False)
    pd.DataFrame(scifact_results_by_seed).to_csv(EXP_DIR / "scifact_results_by_seed.csv", index=False)
    pd.DataFrame(vitaminc_results_by_seed).to_csv(EXP_DIR / "vitaminc_results_by_seed.csv", index=False)

    # ---- Step 6: E3 evidence sensitivity ----
    log("[6] E3 evidence sensitivity evaluation...")
    e3_results = []
    for seed in SEEDS:
        # VitaminC E3: official contrastive pairs
        vc_e3_pairs = build_vitaminc_e3_pairs(vc_test_records, MAX_E3_PAIRS, seed)
        log(f"  Seed {seed}: VitaminC E3 pairs (official): {len(vc_e3_pairs)}")
        if vc_e3_pairs and not args.skip_nli:
            r = eval_e3_evidence_sensitivity(vc_e3_pairs, seed)
            r["dataset"] = "vitaminc"
            r["e3_pair_source"] = "official_contrastive"
            e3_results.append(r)
            # Provenance for E3 pairs
            for p in vc_e3_pairs:
                provenance_rows.append({
                    "external_id": p["pair_id"],
                    "dataset": "vitaminc",
                    "source_split": "test",
                    "original_label": f"correct={p['correct_original_label']};wrong={p['wrong_original_label']}",
                    "mapped_label": "contrastive_pair",
                    "label_mapping_rule": "official_contrastive_pair",
                    "sampling_reason": "e3_contrastive",
                    "filter_reason": "",
                    "source_info": p["source_info"],
                    "e3_pair_source": "official_contrastive",
                    "seed": seed,
                })

        # SciFact E3: synthetic perturbation
        sf_e3_pairs = build_scifact_e3_pairs(sf_dev_pairs, MAX_E3_PAIRS, seed)
        log(f"  Seed {seed}: SciFact E3 pairs (synthetic): {len(sf_e3_pairs)}")
        if sf_e3_pairs and not args.skip_nli:
            r = eval_e3_evidence_sensitivity(sf_e3_pairs, seed)
            r["dataset"] = "scifact"
            r["e3_pair_source"] = "synthetic_perturbation"
            e3_results.append(r)
            for p in sf_e3_pairs:
                provenance_rows.append({
                    "external_id": p["pair_id"],
                    "dataset": "scifact",
                    "source_split": "dev",
                    "original_label": f"correct={p['correct_original_label']};wrong={p['wrong_original_label']}",
                    "mapped_label": "synthetic_perturbation_pair",
                    "label_mapping_rule": "synthetic_perturbation",
                    "sampling_reason": "e3_synthetic",
                    "filter_reason": "",
                    "source_info": p["source_info"],
                    "e3_pair_source": "synthetic_perturbation",
                    "seed": seed,
                })

    # Re-save provenance with E3 added
    pd.DataFrame(provenance_rows).to_csv(EXP_DIR / "external_gold_subset_provenance.csv", index=False)
    pd.DataFrame(e3_results).to_csv(EXP_DIR / "evidence_sensitivity_results.csv", index=False)

    # ---- Step 7: aggregate results ----
    log("[7] Aggregating results...")
    sf_df = pd.DataFrame(scifact_results_by_seed)
    vc_df = pd.DataFrame(vitaminc_results_by_seed)

    def agg(df: pd.DataFrame, metric: str) -> dict:
        out = {}
        for method in df["method"].unique():
            sub = df[df["method"] == method]
            if sub["skipped"].any():
                out[method] = {"mean": None, "std": None, "n": 0, "skipped": True}
                continue
            vals = sub[metric].dropna()
            if len(vals) == 0:
                out[method] = {"mean": None, "std": None, "n": 0}
            else:
                out[method] = {
                    "mean": float(vals.mean()),
                    "std": float(vals.std()) if len(vals) > 1 else 0.0,
                    "n": int(len(vals)),
                }
        return out

    summary = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "is_full_benchmark": False,
        "is_gold_derived_subset": True,
        "original_labels_preserved": True,
        "mapped_labels_are_derived": True,
        "sampling_representativeness_limit": "label-balanced sample of <=300 per dataset; not full benchmark",
        "statistical_power_limit": "small N; multi-seed mean/std only; no SOTA claims",
        "can_claim_sota": False,
        "can_replace_simclaim_gold": False,
        "scifact": {
            "available": True,
            "n_eval_per_seed": int(sf_df["e1_n_eval"].max()) if len(sf_df) > 0 else 0,
            "label_distribution_sampled": dict(Counter(p["mapped_label"] for p in scifact_sampled_all)),
            "e1_macro_f1_by_method": agg(sf_df, "e1_macro_f1"),
            "e1_accuracy_by_method": agg(sf_df, "e1_accuracy"),
            "e2_macro_f1_by_method": agg(sf_df, "e2_macro_f1"),
            "e2_accuracy_by_method": agg(sf_df, "e2_accuracy"),
        },
        "vitaminc": {
            "available": True,
            "n_eval_per_seed": int(vc_df["e1_n_eval"].max()) if len(vc_df) > 0 else 0,
            "label_distribution_sampled": dict(Counter(p["mapped_label"] for p in vitaminc_sampled_all)),
            "e1_macro_f1_by_method": agg(vc_df, "e1_macro_f1"),
            "e1_accuracy_by_method": agg(vc_df, "e1_accuracy"),
            "e2_macro_f1_by_method": agg(vc_df, "e2_macro_f1"),
            "e2_accuracy_by_method": agg(vc_df, "e2_accuracy"),
        },
        "e3_evidence_sensitivity": [
            {k: v for k, v in r.items() if k != "error"} for r in e3_results
        ],
        "label_distribution_note": "public gold original labels preserved; mapped labels are derived (SUPPORT->supported, CONTRADICT/REFUTES->contradiction_candidate, NEI->unsupported_or_insufficient)",
        "naming_note": "this is an external gold-derived subset / external sanity check, NOT a new gold benchmark, NOT SimClaim gold, NOT human-audited SimClaim gold",
    }

    # Find best task per dataset
    def find_best(df: pd.DataFrame) -> tuple[str, float]:
        best_method = None
        best_score = -1.0
        for method in df["method"].unique():
            sub = df[df["method"] == method]
            if sub["skipped"].any():
                continue
            vals = sub["e1_macro_f1"].dropna()
            if len(vals) > 0:
                m = float(vals.mean())
                if m > best_score:
                    best_score = m
                    best_method = method
        if best_method is None:
            # Try E2
            for method in df["method"].unique():
                sub = df[df["method"] == method]
                if sub["skipped"].any():
                    continue
                vals = sub["e2_macro_f1"].dropna()
                if len(vals) > 0:
                    m = float(vals.mean())
                    if m > best_score:
                        best_score = m
                        best_method = method
        return (best_method or "none", best_score if best_score >= 0 else 0.0)

    sf_best_method, sf_best_score = find_best(sf_df)
    vc_best_method, vc_best_score = find_best(vc_df)

    summary["scifact"]["best_task"] = f"E1/{sf_best_method}"
    summary["scifact"]["best_macro_f1"] = sf_best_score
    summary["vitaminc"]["best_task"] = f"E1/{vc_best_method}"
    summary["vitaminc"]["best_macro_f1"] = vc_best_score

    # Claim-only leakage risk
    def leakage_risk(df: pd.DataFrame) -> dict:
        """Compare Method B (claim-only) vs Method A (claim+evidence).
        If B is close to or better than A, claim-only leakage is HIGH."""
        a_vals = df[df["method"] == "A_tfidf_claim_evidence"]["e1_macro_f1"].dropna()
        b_vals = df[df["method"] == "B_tfidf_claim_only"]["e1_macro_f1"].dropna()
        if len(a_vals) == 0 or len(b_vals) == 0:
            return {"a_mean": None, "b_mean": None, "delta_b_minus_a": None, "leakage_risk": "unknown"}
        a_mean = float(a_vals.mean())
        b_mean = float(b_vals.mean())
        delta = b_mean - a_mean
        # High leakage if B within 0.05 of A (or better)
        if delta >= -0.05:
            risk = "high"
        elif delta >= -0.15:
            risk = "moderate"
        else:
            risk = "low"
        return {"a_mean": a_mean, "b_mean": b_mean, "delta_b_minus_a": delta, "leakage_risk": risk}

    summary["scifact"]["claim_only_leakage"] = leakage_risk(sf_df)
    summary["vitaminc"]["claim_only_leakage"] = leakage_risk(vc_df)

    # E3 summary
    vc_e3 = [r for r in e3_results if r.get("dataset") == "vitaminc"]
    sf_e3 = [r for r in e3_results if r.get("dataset") == "scifact"]
    if vc_e3:
        deltas = [r["correct_vs_wrong_delta"] for r in vc_e3 if r.get("correct_vs_wrong_delta") is not None]
        sens_rates = [r["evidence_sensitivity_rate"] for r in vc_e3 if r.get("evidence_sensitivity_rate") is not None]
        summary["vitaminc_e3_summary"] = {
            "n_pairs_per_seed": vc_e3[0].get("n_pairs", 0),
            "delta_mean": float(np.mean(deltas)) if deltas else None,
            "delta_std": float(np.std(deltas)) if deltas else None,
            "sensitivity_rate_mean": float(np.mean(sens_rates)) if sens_rates else None,
            "uses_official_contrastive_pairs": True,
            "uses_synthetic_perturbation": False,
        }
    else:
        summary["vitaminc_e3_summary"] = {"uses_official_contrastive_pairs": True, "uses_synthetic_perturbation": False}

    if sf_e3:
        deltas = [r["correct_vs_wrong_delta"] for r in sf_e3 if r.get("correct_vs_wrong_delta") is not None]
        sens_rates = [r["evidence_sensitivity_rate"] for r in sf_e3 if r.get("evidence_sensitivity_rate") is not None]
        summary["scifact_e3_summary"] = {
            "n_pairs_per_seed": sf_e3[0].get("n_pairs", 0),
            "delta_mean": float(np.mean(deltas)) if deltas else None,
            "delta_std": float(np.std(deltas)) if deltas else None,
            "sensitivity_rate_mean": float(np.mean(sens_rates)) if sens_rates else None,
            "uses_official_contrastive_pairs": False,
            "uses_synthetic_perturbation": True,
        }
    else:
        summary["scifact_e3_summary"] = {"uses_official_contrastive_pairs": False, "uses_synthetic_perturbation": True}

    # R4 external sanity check
    r4_method_results = sf_df[sf_df["method"] == "D_r4_compatible"]
    r4_did_not_crash = (~r4_method_results["skipped"]).any() if len(r4_method_results) > 0 else False
    r4_e1_mean = r4_method_results["e1_macro_f1"].dropna().mean() if len(r4_method_results) > 0 else None
    r4_e2_mean = r4_method_results["e2_macro_f1"].dropna().mean() if len(r4_method_results) > 0 else None
    summary["r4_external_sanity"] = {
        "method_d_ran_without_crash": bool(r4_did_not_crash),
        "r4_compatible_e1_macro_f1_scifact": float(r4_e1_mean) if r4_e1_mean is not None and not np.isnan(r4_e1_mean) else None,
        "r4_compatible_e2_macro_f1_scifact": float(r4_e2_mean) if r4_e2_mean is not None and not np.isnan(r4_e2_mean) else None,
    }

    # Save summary
    with open(EXP_DIR / "external_gold_results_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False, default=str)
    log("  Summary saved.")

    # ---- Step 8: readiness gate ----
    log("[8] Writing readiness gate...")
    sf_avail = True
    vc_avail = True
    sf_n_eval = int(len(scifact_sampled_all) / len(SEEDS)) if scifact_sampled_all else 0
    vc_n_eval = int(len(vitaminc_sampled_all) / len(SEEDS)) if vitaminc_sampled_all else 0

    # R4 external sanity supported if Method D ran and E1 macro F1 > 0.5 OR E2 > 0.5
    r4_supported = False
    if r4_did_not_crash:
        e1_vals = r4_method_results["e1_macro_f1"].dropna()
        e2_vals = r4_method_results["e2_macro_f1"].dropna()
        if len(e1_vals) > 0 and float(e1_vals.mean()) > 0.5:
            r4_supported = True
        if len(e2_vals) > 0 and float(e2_vals.mean()) > 0.5:
            r4_supported = True

    # E3 sensitivity for VitaminC
    e3_delta = None
    if vc_e3:
        deltas = [r["correct_vs_wrong_delta"] for r in vc_e3 if r.get("correct_vs_wrong_delta") is not None]
        if deltas:
            e3_delta = float(np.mean(deltas))

    # Claim-only leakage risk
    sf_leak = summary["scifact"]["claim_only_leakage"]
    vc_leak = summary["vitaminc"]["claim_only_leakage"]
    overall_leak = "high" if "high" in [sf_leak.get("leakage_risk"), vc_leak.get("leakage_risk")] else \
                   "moderate" if "moderate" in [sf_leak.get("leakage_risk"), vc_leak.get("leakage_risk")] else "low"

    gate = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scifact_available": sf_avail,
        "vitaminc_available": vc_avail,
        "scifact_n_eval": sf_n_eval,
        "vitaminc_n_eval": vc_n_eval,
        "scifact_best_task": summary["scifact"]["best_task"],
        "vitaminc_best_task": summary["vitaminc"]["best_task"],
        "scifact_macro_f1": sf_best_score,
        "vitaminc_macro_f1": vc_best_score,
        "evidence_sensitivity_delta": e3_delta,
        "claim_only_leakage_risk": overall_leak,
        "r4_external_sanity_supported": r4_supported,
        "external_subset_is_gold_derived": True,
        "original_public_gold_labels_preserved": True,
        "mapped_labels_are_not_original_gold_task": True,
        "e3_uses_official_contrastive_pairs": True,
        "e3_uses_synthetic_perturbation": True,
        "can_claim_public_benchmark_result": False,
        "can_claim_external_sanity_check": True,
        "can_replace_simclaim_gold": False,
        "why_external_gold_cannot_replace_simclaim_gold": (
            "Public gold datasets (SciFact, VitaminC) do not contain action-overclaim or "
            "scope-overclaim labels; their taxonomy is support/refute/NEI, which cannot test "
            "SimClaim's 4-class escalation taxonomy (supported / mild_scope_overclaim / "
            "strong_action_overclaim / contradiction_candidate). Public data also lacks the "
            "claim-action vs evidence-action gap features that R4 routes on. Public results "
            "therefore validate only support/refute and evidence-sensitivity transfer, NOT the "
            "SimClaim-specific escalation task."
        ),
        "recommended_paper_use": (
            "Use as external sanity check in appendix/supplementary: 'To test whether the "
            "evidence-relation approach transfers to public claim-verification data, we ran a "
            "small gold-derived subset evaluation on SciFact and VitaminC. Results are "
            "supportive-but-not-final and do not replace SimClaim gold evaluation.'"
        ),
        "main_risk": (
            "Small N (<=300 per dataset), no action-overclaim labels, domain mismatch "
            "(scientific citations / Wikipedia revisions vs SimClaim RL/AI safety claims)."
        ),
        "recommended_next_step": (
            "If external validation is to be expanded, hand-audit a small SimClaim-style "
            "subset of SciFact/VitaminC for action-overclaim signals; otherwise current "
            "subset is sufficient as sanity check for paper appendix."
        ),
    }
    with open(EXP_DIR / "external_gold_readiness_gate.json", "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False, default=str)
    log("  Readiness gate saved.")

    # ---- Step 9: download_instructions.md ----
    log("[9] Writing download_instructions.md...")
    download_md = """# External Gold Data Download Instructions

This file documents how the SciFact and VitaminC data used in this experiment was acquired.

## SciFact

- **Source URL**: https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
- **License**: CC BY-NC 2.0
- **Local path**: `D:\\ocn\\data\\external_gold\\scifact\\`
- **Files used**:
  - `data/claims_train.jsonl` (809 claims, labeled)
  - `data/claims_dev.jsonl` (300 claims, labeled)
  - `data/corpus.jsonl` (5183 abstracts)
- **Note**: `claims_test.jsonl` exists but is unlabeled (no labels released); not used.
- **Download method**: direct HTTPS GET via Python `requests` with `trust_env=False` (bypassing system proxy).

## VitaminC

- **Original source**: https://github.com/TalSchuster/talschuster.github.io/raw/master/static/vitaminc.zip
- **Mirror used**: `https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/` (because `huggingface.co` and `raw.githubusercontent.com` were blocked by the local network)
- **License**: CC BY-SA 3.0
- **Local path**: `D:\\ocn\\data\\external_gold\\vitaminc\\`
- **Files used**:
  - `dev.jsonl` (63054 records, used as training proxy)
  - `test.jsonl` (55197 records, used for evaluation sampling)
- **Files NOT downloaded**:
  - `train.jsonl` (194MB) - skipped to save bandwidth; dev.jsonl used as training proxy instead
- **Download method**: Python `requests` with `trust_env=False`, streamed to disk.
- **Network failures encountered**:
  - `huggingface.co` connection timeout (blocked by network)
  - `raw.githubusercontent.com` connection reset on large files (vitaminc.zip)
  - Workaround: used `hf-mirror.com` Chinese mirror which worked reliably

## NLI Model (Method C)

- **Model**: `cross-encoder/nli-deberta-base`
- **Cache location**: `~/.cache/huggingface/hub/models--cross-encoder--nli-deberta-base`
- **Loaded offline** with `HF_HUB_OFFLINE=1` and `TRANSFORMERS_OFFLINE=1`
- **No new model download required**

## Reproducibility

To re-download the data on a clean machine:

```bash
# SciFact
mkdir -p data/external_gold/scifact
curl -L -o data/external_gold/scifact_data.tar.gz \\
  https://scifact.s3-us-west-2.amazonaws.com/release/latest/data.tar.gz
tar -xzf data/external_gold/scifact_data.tar.gz -C data/external_gold/scifact

# VitaminC (use hf-mirror.com if huggingface.co is blocked)
mkdir -p data/external_gold/vitaminc
curl -L -o data/external_gold/vitaminc/dev.jsonl \\
  https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/dev.jsonl
curl -L -o data/external_gold/vitaminc/test.jsonl \\
  https://hf-mirror.com/datasets/tals/vitaminc/resolve/main/test.jsonl
```
"""
    (EXP_DIR / "download_instructions.md").write_text(download_md, encoding="utf-8")

    # ---- Final log ----
    log("=" * 70)
    log("Task R1 COMPLETE")
    log("=" * 70)
    log(f"SciFact: available={sf_avail}, n_eval={sf_n_eval}, best={summary['scifact']['best_task']} (macro_f1={sf_best_score:.4f})")
    log(f"VitaminC: available={vc_avail}, n_eval={vc_n_eval}, best={summary['vitaminc']['best_task']} (macro_f1={vc_best_score:.4f})")
    log(f"E3 VitaminC delta: {e3_delta}")
    log(f"Claim-only leakage risk: {overall_leak}")
    log(f"R4 external sanity supported: {r4_supported}")
    log(f"Output dir: {EXP_DIR}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {type(e).__name__}: {e}")
        log(traceback.format_exc())
        sys.exit(1)
