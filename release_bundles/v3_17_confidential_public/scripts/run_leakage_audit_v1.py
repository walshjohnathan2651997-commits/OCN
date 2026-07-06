#!/usr/bin/env python
"""run_leakage_audit_v1.py — Leakage / shortcut / dataset-contingency audit.

Audits the 444-candidate controlled silver diagnostic set for:
1. claim-only baseline — is claim_text alone too predictive? (TF-IDF + LR)
2. empty evidence baseline — does screening degrade with empty evidence?
3. shuffled evidence baseline — does screening degrade with shuffled evidence?
4. title-only retrieval — is title alone too strong for retrieval?
5. metadata-only retrieval — is metadata alone too predictive?
6. lexical overlap by label — claim-evidence overlap distribution per label
7. cue words by label — action / certainty / deployment / safety cue rates
8. group split integrity — do groups cross train/test?
9. generation policy distribution — policy × label, domain × label crosstabs
10. no oracle in selector — does selector read oracle_hit/true_label?
11. no label in queue sorting — does SmartQueue sort by forbidden fields?

Hard boundaries:
  - no network, no API, no training of new models beyond audit-only LR
  - no original data modification, no auto label change, no gold_label fill
  - true_label/candidate_label_guess used for audit statistics ONLY
  - no claim/evidence raw text in public/redacted outputs

Usage:
  python scripts/run_leakage_audit_v1.py --config configs/v3_17_confidential_default.yaml
  python scripts/run_leakage_audit_v1.py --toy_mode
"""

from __future__ import annotations

import argparse
import csv
import json
import math
import random
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

# Shared config utilities
sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
from config_utils import load_and_validate, resolve_path, write_run_config, print_guards  # noqa: E402
from schema_utils import validate_json_file, write_schema_validation_report  # noqa: E402

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
_STOP = {
    "a", "an", "the", "and", "or", "in", "on", "at", "to", "for", "of",
    "with", "is", "are", "was", "were", "be", "this", "that", "these",
    "those", "it", "its", "as", "by", "from", "we", "our", "their",
}

# Cue word lists for lexical cue audit
ACTION_CUES = {
    "perform", "performs", "performed", "performing",
    "execute", "executes", "executed", "executing",
    "achieve", "achieves", "achieved", "achieving",
    "improve", "improves", "improved", "improving",
    "enhance", "enhances", "enhanced", "enhancing",
    "enable", "enables", "enabled", "enabling",
    "ensure", "ensures", "ensured", "ensuring",
    "guarantee", "guarantees", "guaranteed",
    "demonstrate", "demonstrates", "demonstrated",
    "show", "shows", "showed", "shown",
    "prove", "proves", "proved", "proven",
    "establish", "establishes", "established",
    "implement", "implements", "implemented",
    "deploy", "deploys", "deployed",
}

CERTAINTY_CUES = {
    "always", "never", "must", "cannot", "can't", "will", "would",
    "definitely", "clearly", "obviously", "certainly", "undoubtedly",
    "proven", "guaranteed", "assured", "inevitable", "unavoidable",
    "absolutely", "completely", "fully", "perfectly", "flawless",
}

DEPLOYMENT_CUES = {
    "deploy", "deployment", "production", "real-world", "real-time",
    "real time", "online", "operational", "field", "live",
    "in-the-wild", "practical", "industry", "industrial",
    "commercial", "product", "shipping", "released",
}

SAFETY_CUES = {
    "safe", "safety", "risk", "hazard", "danger", "dangerous",
    "failure", "accident", "harm", "harmful", "secure", "security",
    "robust", "robustness", "reliable", "reliability",
    "collision", "crash", "malfunction", "vulnerability",
}

STRONG_LABEL = "strong_action_overclaim"


def log(msg):
    print(msg, flush=True)


def tokenize(text):
    return [w for w in _TOKEN_RE.findall((text or "").lower()) if w not in _STOP]


def tokenize_with_stop(text):
    """Tokenize without stopword removal (for TF-IDF)."""
    return _TOKEN_RE.findall((text or "").lower())


def sha256_text(text):
    import hashlib
    if text is None:
        text = ""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def jaccard(a, b):
    s1, s2 = set(a), set(b)
    if not s1 or not s2:
        return 0.0
    return len(s1 & s2) / len(s1 | s2)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

def load_candidates_with_labels(csv_path):
    """Load candidate CSV with labels and all audit-relevant fields."""
    candidates = []
    with open(csv_path, "r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Use candidate_label_guess as the audit label (silver label)
            # This is explicitly allowed: "true_label/candidate_label_guess
            # 只用于 audit 统计，不用于 selection/ranking"
            audit_label = (
                row.get("true_label", "")
                or row.get("final_label", "")
                or row.get("gold_label", "")
                or row.get("candidate_label_guess", "")
            )
            rec = {
                "candidate_id": row.get("candidate_id", ""),
                "target_candidate_group_id": row.get("target_candidate_group_id", ""),
                "claim_text": row.get("claim_text", ""),
                "title": row.get("title", "") or row.get("pdf_filename", "").replace(".pdf", ""),
                "pdf_filename": row.get("pdf_filename", ""),
                "page_number": int(row["page_number"]) if str(row.get("page_number", "")).isdigit() else 0,
                "evidence_text": row.get("evidence_text", ""),
                "domain": row.get("domain", ""),
                "claim_generation_policy": row.get("claim_generation_policy", ""),
                "silver_label_source": row.get("silver_label_source", ""),
                "dataset_role": row.get("dataset_role", "") or row.get("split", ""),
                "_true_label": audit_label,
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
                "domain": "toy_domain",
                "claim_generation_policy": "toy_policy",
                "silver_label_source": "candidate_label_guess",
                "dataset_role": "test",
                "_true_label": toy_labels[i] if i < len(toy_labels) else "supported",
            }
            candidates.append(rec)
    return candidates


# ---------------------------------------------------------------------------
# Check 1: claim-only baseline (TF-IDF + LogisticRegression)
# ---------------------------------------------------------------------------

def check_claim_only_baseline_tfidf(candidates, true_labels):
    """Train a TF-IDF + LogisticRegression on claim_text alone with group-aware
    cross-validation. If claim-only performance approaches R4, the dataset may
    contain generation-policy shortcuts in claim_text.

    Metrics: strong_F1 (binary F1 for strong_action_overclaim),
    macro_F1, P@20 (precision in top-20 by predicted strong probability).

    Uses GroupKFold by target_candidate_group_id to prevent group leakage.
    """
    log("  [Check 1] Claim-only baseline (TF-IDF + LR, group-aware) ...")

    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import GroupKFold
    from sklearn.metrics import f1_score
    import numpy as np

    # Prepare data
    ids = []
    texts = []
    labels = []
    groups = []
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if not lab or not c["claim_text"].strip():
            continue
        ids.append(c["candidate_id"])
        texts.append(c["claim_text"])
        labels.append(lab)
        groups.append(c["target_candidate_group_id"])

    n = len(texts)
    if n < 20 or len(set(labels)) < 2:
        return {
            "status": "skip",
            "reason": f"insufficient data ({n} samples, {len(set(labels))} labels)",
            "strong_f1": 0, "macro_f1": 0, "p_at_20": 0,
        }

    labels = np.array(labels)
    groups = np.array(groups)

    # Binary strong_action label for strong_F1
    binary_labels = (labels == STRONG_LABEL).astype(int)

    # GroupKFold (5 folds or fewer if not enough groups)
    n_splits = min(5, len(set(groups)))
    if n_splits < 2:
        return {
            "status": "skip",
            "reason": f"insufficient groups ({n_splits})",
            "strong_f1": 0, "macro_f1": 0, "p_at_20": 0,
        }

    gkf = GroupKFold(n_splits=n_splits)

    fold_strong_f1 = []
    fold_macro_f1 = []
    fold_p_at_20 = []
    all_pred_proba_strong = np.zeros(n)

    for fold_idx, (train_idx, test_idx) in enumerate(gkf.split(texts, labels, groups)):
        train_texts = [texts[i] for i in train_idx]
        test_texts = [texts[i] for i in test_idx]
        y_train = labels[train_idx]
        y_test = labels[test_idx]
        y_train_bin = binary_labels[train_idx]
        y_test_bin = binary_labels[test_idx]

        # TF-IDF features (unigrams + bigrams)
        vectorizer = TfidfVectorizer(
            max_features=5000,
            ngram_range=(1, 2),
            sublinear_tf=True,
            token_pattern=r"[a-z0-9]+",
            stop_words="english",
        )
        X_train = vectorizer.fit_transform(train_texts)
        X_test = vectorizer.transform(test_texts)

        # Multinomial LR for macro_F1
        try:
            lr_multi = LogisticRegression(
                max_iter=1000, C=1.0, random_state=42,
                class_weight="balanced",
            )
            lr_multi.fit(X_train, y_train)
            y_pred = lr_multi.predict(X_test)
            fold_macro_f1.append(f1_score(y_test, y_pred, average="macro"))

            # Predicted probabilities for strong class
            classes = list(lr_multi.classes_)
            if STRONG_LABEL in classes:
                strong_idx = classes.index(STRONG_LABEL)
                proba = lr_multi.predict_proba(X_test)[:, strong_idx]
            else:
                proba = np.zeros(len(test_idx))
        except Exception as e:
            log(f"    fold {fold_idx}: LR multi failed: {e}")
            fold_macro_f1.append(0.0)
            proba = np.zeros(len(test_idx))

        # Binary LR for strong_F1 and P@20
        try:
            lr_bin = LogisticRegression(
                max_iter=1000, C=1.0, random_state=42,
                class_weight="balanced",
            )
            lr_bin.fit(X_train, y_train_bin)
            y_pred_bin = lr_bin.predict(X_test)
            fold_strong_f1.append(f1_score(y_test_bin, y_pred_bin))
            proba_bin = lr_bin.predict_proba(X_test)[:, 1]
        except Exception as e:
            log(f"    fold {fold_idx}: LR binary failed: {e}")
            fold_strong_f1.append(0.0)
            proba_bin = np.zeros(len(test_idx))

        # P@20: precision in top-20 by predicted strong probability
        # (use binary LR proba; if < 20 in test, use all)
        if len(test_idx) > 0:
            k = min(20, len(test_idx))
            top_k_idx = np.argsort(-proba_bin)[:k]
            p_at_20 = y_test_bin[top_k_idx].mean()
            fold_p_at_20.append(p_at_20)

        # Store proba for out-of-fold predictions
        all_pred_proba_strong[test_idx] = proba_bin

    strong_f1_mean = np.mean(fold_strong_f1) if fold_strong_f1 else 0.0
    strong_f1_std = np.std(fold_strong_f1) if fold_strong_f1 else 0.0
    macro_f1_mean = np.mean(fold_macro_f1) if fold_macro_f1 else 0.0
    macro_f1_std = np.std(fold_macro_f1) if fold_macro_f1 else 0.0
    p_at_20_mean = np.mean(fold_p_at_20) if fold_p_at_20 else 0.0
    p_at_20_std = np.std(fold_p_at_20) if fold_p_at_20 else 0.0

    # CI: mean ± 1.96 * std / sqrt(n_folds) — rough normal CI
    n_folds = len(fold_strong_f1)
    ci_factor = 1.96 / math.sqrt(n_folds) if n_folds > 0 else 0

    # Compare against R4 strong_F1 = 0.4503 (from metric_robustness_v1)
    R4_STRONG_F1 = 0.4503
    ratio_to_r4 = strong_f1_mean / R4_STRONG_F1 if R4_STRONG_F1 > 0 else 0

    # Status: WARNING if claim-only strong_F1 >= 0.8 * R4 strong_F1
    # FAIL if claim-only >= R4
    if strong_f1_mean >= R4_STRONG_F1:
        status = "fail"
    elif ratio_to_r4 >= 0.8:
        status = "warning"
    else:
        status = "pass"

    return {
        "status": status,
        "method": "TF-IDF (unigram+bigram, 5000 features) + LogisticRegression (balanced, group-aware GroupKFold)",
        "n_samples": n,
        "n_groups": len(set(groups)),
        "n_folds": n_folds,
        "strong_f1_mean": round(float(strong_f1_mean), 4),
        "strong_f1_std": round(float(strong_f1_std), 4),
        "strong_f1_ci95_low": round(float(max(0, strong_f1_mean - ci_factor * strong_f1_std)), 4),
        "strong_f1_ci95_high": round(float(min(1, strong_f1_mean + ci_factor * strong_f1_std)), 4),
        "macro_f1_mean": round(float(macro_f1_mean), 4),
        "macro_f1_std": round(float(macro_f1_std), 4),
        "p_at_20_mean": round(float(p_at_20_mean), 4),
        "p_at_20_std": round(float(p_at_20_std), 4),
        "r4_strong_f1_reference": R4_STRONG_F1,
        "ratio_claim_only_to_r4": round(float(ratio_to_r4), 4),
        "threshold_warning_ratio": 0.8,
        "threshold_fail_ratio": 1.0,
        "fold_strong_f1": [round(float(x), 4) for x in fold_strong_f1],
        "fold_macro_f1": [round(float(x), 4) for x in fold_macro_f1],
    }


# ---------------------------------------------------------------------------
# Check 2: empty evidence baseline
# ---------------------------------------------------------------------------

def check_empty_evidence_baseline(candidates, true_labels):
    """Compute claim-evidence overlap with empty evidence (should be ~0).

    Proxy for screening utility: if the screening pipeline is evidence-sensitive,
    empty evidence should produce near-zero overlap/utility. If overlap with
    correct evidence is also near-zero, the pipeline may not be using evidence.

    Metric: mean Jaccard overlap of claim tokens with evidence tokens.
    """
    log("  [Check 2] Empty evidence baseline ...")
    correct_overlaps = []
    empty_overlaps = []
    for c in candidates:
        claim_tokens = tokenize(c["claim_text"])
        evidence_tokens = tokenize(c["evidence_text"])
        correct_overlaps.append(jaccard(claim_tokens, evidence_tokens))
        empty_overlaps.append(0.0)  # empty evidence → zero overlap by definition

    mean_correct = sum(correct_overlaps) / len(correct_overlaps) if correct_overlaps else 0
    mean_empty = 0.0

    # Status: pass if correct evidence overlap > 0.05 (some signal)
    # warning if correct ≈ 0 (evidence not informative)
    status = "pass" if mean_correct > 0.05 else "warning"

    return {
        "status": status,
        "method": "Jaccard token overlap (claim vs evidence); empty evidence → 0 by construction",
        "n_samples": len(candidates),
        "mean_correct_evidence_overlap": round(mean_correct, 6),
        "mean_empty_evidence_overlap": mean_empty,
        "note": "Empty evidence produces zero overlap by definition. "
                "This check verifies correct evidence has non-trivial overlap.",
    }


# ---------------------------------------------------------------------------
# Check 3: shuffled evidence baseline
# ---------------------------------------------------------------------------

def check_shuffled_evidence_baseline(candidates, true_labels):
    """Compute claim-evidence overlap with shuffled evidence (from other groups).

    If shuffled evidence overlap is close to correct evidence overlap, the
    pipeline may not be evidence-sensitive. Correct evidence should have
    higher overlap than cross-group shuffled evidence.
    """
    log("  [Check 3] Shuffled evidence baseline ...")
    random.seed(42)

    # Shuffle evidence across groups (not within same group)
    by_group = defaultdict(list)
    for c in candidates:
        by_group[c["target_candidate_group_id"]].append(c)

    group_ids = list(by_group.keys())
    if len(group_ids) < 2:
        return {"status": "skip", "reason": "fewer than 2 groups", "mean_correct_overlap": 0, "mean_shuffled_overlap": 0}

    # For each candidate, pick a random evidence from a DIFFERENT group
    correct_overlaps = []
    shuffled_overlaps = []
    same_domain_shuffled_overlaps = []

    # Build domain-grouped index for same-domain shuffle
    by_domain = defaultdict(list)
    for c in candidates:
        by_domain[c["domain"]].append(c)

    for c in candidates:
        claim_tokens = tokenize(c["claim_text"])
        correct_ev_tokens = tokenize(c["evidence_text"])
        correct_overlaps.append(jaccard(claim_tokens, correct_ev_tokens))

        # Cross-group shuffle: pick random candidate from different group
        other_group_candidates = [
            x for g in group_ids if g != c["target_candidate_group_id"]
            for x in by_group[g]
        ]
        if other_group_candidates:
            shuffled = random.choice(other_group_candidates)
            shuffled_ev_tokens = tokenize(shuffled["evidence_text"])
            shuffled_overlaps.append(jaccard(claim_tokens, shuffled_ev_tokens))

        # Same-domain shuffled: pick random candidate from same domain, different group
        same_domain_others = [
            x for x in by_domain.get(c["domain"], [])
            if x["target_candidate_group_id"] != c["target_candidate_group_id"]
        ]
        if same_domain_others:
            shuffled_sd = random.choice(same_domain_others)
            sd_ev_tokens = tokenize(shuffled_sd["evidence_text"])
            same_domain_shuffled_overlaps.append(jaccard(claim_tokens, sd_ev_tokens))

    mean_correct = sum(correct_overlaps) / len(correct_overlaps) if correct_overlaps else 0
    mean_shuffled = sum(shuffled_overlaps) / len(shuffled_overlaps) if shuffled_overlaps else 0
    mean_same_domain = sum(same_domain_shuffled_overlaps) / len(same_domain_shuffled_overlaps) if same_domain_shuffled_overlaps else 0

    # Status: pass if correct >> shuffled (ratio > 2)
    # warning if ratio 1.5-2, fail if ratio < 1.5
    ratio = mean_correct / mean_shuffled if mean_shuffled > 1e-10 else 999
    if ratio < 1.5:
        status = "warning"
    else:
        status = "pass"

    # Also check title-only: claim vs title overlap
    title_overlaps = []
    for c in candidates:
        claim_tokens = tokenize(c["claim_text"])
        title_tokens = tokenize(c["title"])
        title_overlaps.append(jaccard(claim_tokens, title_tokens))
    mean_title = sum(title_overlaps) / len(title_overlaps) if title_overlaps else 0

    return {
        "status": status,
        "method": "Jaccard token overlap; shuffled = evidence from different group (seed=42)",
        "n_samples": len(candidates),
        "mean_correct_evidence_overlap": round(mean_correct, 6),
        "mean_cross_group_shuffled_overlap": round(mean_shuffled, 6),
        "mean_same_domain_shuffled_overlap": round(mean_same_domain, 6),
        "mean_title_only_overlap": round(mean_title, 6),
        "ratio_correct_to_shuffled": round(ratio, 4) if ratio < 999 else 999,
        "threshold_warning_ratio": 1.5,
        "expected_ordering": "correct > same_domain_shuffled > cross_group_shuffled > title_only",
        "ordering_holds": (
            mean_correct > mean_same_domain
            and mean_same_domain >= mean_shuffled
        ),
    }


# ---------------------------------------------------------------------------
# Check 4: title-only retrieval (existing, enhanced)
# ---------------------------------------------------------------------------

def check_title_only_retrieval(candidates):
    """Check if title alone retrieves evidence too well."""
    log("  [Check 4] Title-only retrieval ...")
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
# Check 5: metadata-only retrieval (existing, enhanced)
# ---------------------------------------------------------------------------

def check_metadata_only_retrieval(candidates):
    """Check if metadata (page_number, pdf_filename) alone is too predictive."""
    log("  [Check 5] Metadata-only retrieval ...")
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
# Check 6: lexical overlap by label (enhanced)
# ---------------------------------------------------------------------------

def check_lexical_overlap_by_label(candidates, true_labels):
    """For each label, compute claim-evidence overlap stats, claim length stats."""
    log("  [Check 6] Lexical overlap by label ...")
    by_label = defaultdict(list)
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if lab:
            by_label[lab].append(c)

    if len(by_label) < 2:
        return {"status": "skip", "reason": "fewer than 2 labels", "by_label_stats": {}}

    by_label_stats = {}
    for lab, cands in by_label.items():
        overlaps = []
        claim_lengths = []
        for c in cands:
            claim_tokens = tokenize(c["claim_text"])
            ev_tokens = tokenize(c["evidence_text"])
            overlaps.append(jaccard(claim_tokens, ev_tokens))
            claim_lengths.append(len(claim_tokens))

        by_label_stats[lab] = {
            "n": len(cands),
            "mean_claim_evidence_overlap": round(sum(overlaps) / len(overlaps), 6) if overlaps else 0,
            "mean_claim_tokens": round(sum(claim_lengths) / len(claim_lengths), 2) if claim_lengths else 0,
            "median_claim_tokens": sorted(claim_lengths)[len(claim_lengths) // 2] if claim_lengths else 0,
        }

    # Status: warning if overlap varies > 2x across labels
    overlaps = [v["mean_claim_evidence_overlap"] for v in by_label_stats.values()]
    if overlaps:
        ratio = max(overlaps) / min(overlaps) if min(overlaps) > 1e-10 else 999
    else:
        ratio = 0
    status = "pass" if ratio < 2 else "warning"

    return {"status": status, "by_label_stats": by_label_stats, "overlap_ratio_across_labels": round(ratio, 4) if ratio < 999 else 999}


def write_lexical_overlap_csv(filepath, lexical_result):
    """Write lexical_overlap_by_label.csv with per-label stats."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "label", "n", "mean_claim_evidence_overlap",
            "mean_claim_tokens", "median_claim_tokens",
        ])
        for lab, stats in lexical_result.get("by_label_stats", {}).items():
            writer.writerow([
                lab, stats["n"], stats["mean_claim_evidence_overlap"],
                stats["mean_claim_tokens"], stats["median_claim_tokens"],
            ])


# ---------------------------------------------------------------------------
# Check 7: cue words by label (NEW)
# ---------------------------------------------------------------------------

def check_cue_words_by_label(candidates, true_labels):
    """For each label, compute action / certainty / deployment / safety cue rates."""
    log("  [Check 7] Cue words by label ...")
    by_label = defaultdict(list)
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if lab:
            by_label[lab].append(c)

    if len(by_label) < 2:
        return {"status": "skip", "reason": "fewer than 2 labels", "by_label_cues": {}}

    by_label_cues = {}
    for lab, cands in by_label.items():
        action_rates = []
        certainty_rates = []
        deployment_rates = []
        safety_rates = []
        for c in cands:
            tokens = set(tokenize_with_stop(c["claim_text"]))
            n = max(len(tokens), 1)
            action_rates.append(len(tokens & ACTION_CUES) / n)
            certainty_rates.append(len(tokens & CERTAINTY_CUES) / n)
            deployment_rates.append(len(tokens & DEPLOYMENT_CUES) / n)
            safety_rates.append(len(tokens & SAFETY_CUES) / n)

        by_label_cues[lab] = {
            "n": len(cands),
            "mean_action_cue_rate": round(sum(action_rates) / len(action_rates), 6),
            "mean_certainty_cue_rate": round(sum(certainty_rates) / len(certainty_rates), 6),
            "mean_deployment_cue_rate": round(sum(deployment_rates) / len(deployment_rates), 6),
            "mean_safety_cue_rate": round(sum(safety_rates) / len(safety_rates), 6),
        }

    # Status: warning if any cue rate varies > 3x across labels
    max_ratio = 1.0
    for cue_key in ["mean_action_cue_rate", "mean_certainty_cue_rate", "mean_deployment_cue_rate", "mean_safety_cue_rate"]:
        vals = [v[cue_key] for v in by_label_cues.values()]
        if vals and min(vals) > 1e-10:
            ratio = max(vals) / min(vals)
            max_ratio = max(max_ratio, ratio)

    status = "pass" if max_ratio < 3 else "warning"
    return {"status": status, "by_label_cues": by_label_cues, "max_cue_ratio_across_labels": round(max_ratio, 4)}


def write_cue_words_csv(filepath, cue_result):
    """Write cue_words_by_label.csv."""
    with open(filepath, "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "label", "n",
            "mean_action_cue_rate", "mean_certainty_cue_rate",
            "mean_deployment_cue_rate", "mean_safety_cue_rate",
        ])
        for lab, stats in cue_result.get("by_label_cues", {}).items():
            writer.writerow([
                lab, stats["n"],
                stats["mean_action_cue_rate"], stats["mean_certainty_cue_rate"],
                stats["mean_deployment_cue_rate"], stats["mean_safety_cue_rate"],
            ])


# ---------------------------------------------------------------------------
# Check 8: label lexical cues — top unigrams/bigrams (enhanced)
# ---------------------------------------------------------------------------

def check_label_lexical_cues(candidates, true_labels):
    """Find tokens/bigrams overrepresented in each label's claims."""
    log("  [Check 8] Label lexical cues (unigrams + bigrams) ...")
    by_label = defaultdict(list)
    for c in candidates:
        lab = true_labels.get(c["candidate_id"], "")
        if lab:
            by_label[lab].append(tokenize(c["claim_text"]))

    if len(by_label) < 2:
        return {"status": "skip", "reason": "fewer than 2 labels", "top_cues": {}}

    label_token_counts = {}
    label_bigram_counts = {}
    for lab, token_lists in by_label.items():
        uc = Counter()
        bc = Counter()
        for tokens in token_lists:
            uc.update(tokens)
            # Bigrams
            for i in range(len(tokens) - 1):
                bc[(tokens[i], tokens[i + 1])] += 1
        label_token_counts[lab] = uc
        label_bigram_counts[lab] = bc

    # Find overrepresented unigrams per label
    top_cues = {}
    for lab in by_label:
        lab_count = label_token_counts[lab]
        other_count = Counter()
        for other_lab in by_label:
            if other_lab != lab:
                other_count += label_token_counts[other_lab]
        n_lab = sum(len(tl) for tl in by_label[lab])
        n_other = sum(sum(len(tl) for tl in by_label[ol]) for ol in by_label if ol != lab)
        cues = []
        for token, count in lab_count.most_common(30):
            other = other_count.get(token, 0)
            if count < 2:
                continue
            lab_rate = count / max(n_lab, 1)
            other_rate = other / max(n_other, 1)
            if other_rate < 1e-10 and lab_rate > 0.01:
                cues.append({"token": token, "lab_count": count, "other_count": other, "lab_rate": round(lab_rate, 4)})
            elif lab_rate / max(other_rate, 1e-10) > 5 and lab_rate > 0.03:
                cues.append({"token": token, "lab_count": count, "other_count": other, "ratio": round(lab_rate / max(other_rate, 1e-10), 2)})
        top_cues[lab] = cues[:5]

    max_cues = max(len(v) for v in top_cues.values()) if top_cues else 0
    status = "pass" if max_cues <= 2 else "warning"
    if max_cues >= 5:
        status = "fail"

    return {"status": status, "top_cues": top_cues, "max_cues_per_label": max_cues}


# ---------------------------------------------------------------------------
# Check 9: group split integrity (existing)
# ---------------------------------------------------------------------------

def check_group_split_integrity(candidates):
    """Check if same target_candidate_group_id crosses train/test splits."""
    log("  [Check 9] Group split integrity ...")
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
# Check 10: generation policy distribution (NEW)
# ---------------------------------------------------------------------------

def check_generation_policy_distribution(candidates):
    """Compute policy × label and domain × label crosstabs."""
    log("  [Check 10] Generation policy distribution ...")
    policy_label = defaultdict(lambda: defaultdict(int))
    domain_label = defaultdict(lambda: defaultdict(int))
    silver_source = Counter()
    policy_counts = Counter()
    domain_counts = Counter()

    for c in candidates:
        pol = c.get("claim_generation_policy", "unknown")
        dom = c.get("domain", "unknown")
        lab = c.get("_true_label", "unknown")
        src = c.get("silver_label_source", "unknown")
        policy_label[pol][lab] += 1
        domain_label[dom][lab] += 1
        silver_source[src] += 1
        policy_counts[pol] += 1
        domain_counts[dom] += 1

    # Check: does any policy correspond to only certain labels?
    policy_label_concentration = {}
    for pol, lab_counts in policy_label.items():
        total = sum(lab_counts.values())
        if total == 0:
            continue
        max_frac = max(lab_counts.values()) / total
        policy_label_concentration[pol] = {
            "n": total,
            "max_label_fraction": round(max_frac, 4),
            "labels": dict(lab_counts),
        }

    # Status: warning if any policy has > 60% concentration in one label
    # (for a 4-label balanced set, expected concentration is 25%)
    max_concentration = max(
        (v["max_label_fraction"] for v in policy_label_concentration.values()),
        default=0,
    )
    status = "pass" if max_concentration < 0.6 else "warning"

    return {
        "status": status,
        "n_policies": len(policy_counts),
        "n_domains": len(domain_counts),
        "policy_counts": dict(policy_counts),
        "domain_counts": dict(domain_counts),
        "silver_label_source_counts": dict(silver_source),
        "policy_label_crosstab": {k: dict(v) for k, v in policy_label.items()},
        "domain_label_crosstab": {k: dict(v) for k, v in domain_label.items()},
        "policy_label_concentration": policy_label_concentration,
        "max_policy_label_concentration": round(max_concentration, 4),
        "expected_concentration": 0.25,
        "threshold_warning": 0.6,
    }


# ---------------------------------------------------------------------------
# Check 11: no oracle in selector (existing)
# ---------------------------------------------------------------------------

def check_no_oracle_in_selector(canonicalizer_guard_path):
    """Verify selector doesn't read oracle_hit/true_label."""
    log("  [Check 11] No oracle in selector ...")
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
# Check 12: no label in queue sorting (existing)
# ---------------------------------------------------------------------------

def check_no_label_in_queue_sorting(queue_guard_path):
    """Verify SmartQueue doesn't sort by forbidden fields."""
    log("  [Check 12] No label in queue sorting ...")
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
# Output
# ---------------------------------------------------------------------------

def write_json(filepath, data):
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def write_audit_summary(filepath, results):
    """Write enhanced audit_summary.md with overall status and safe/unsafe wording."""
    checks = [
        ("1", "Claim-only baseline (TF-IDF+LR)", results.get("claim_only", {})),
        ("2", "Empty evidence baseline", results.get("empty_evidence", {})),
        ("3", "Shuffled evidence baseline", results.get("shuffled_evidence", {})),
        ("4", "Title-only retrieval", results.get("title_only", {})),
        ("5", "Metadata-only retrieval", results.get("metadata_only", {})),
        ("6", "Lexical overlap by label", results.get("lexical_overlap", {})),
        ("7", "Cue words by label", results.get("cue_words", {})),
        ("8", "Label lexical cues", results.get("lexical_cues", {})),
        ("9", "Group split integrity", results.get("group_split", {})),
        ("10", "Generation policy distribution", results.get("policy_dist", {})),
        ("11", "No oracle in selector", results.get("selector_oracle", {})),
        ("12", "No label in queue sorting", results.get("queue_forbidden", {})),
    ]

    # Determine overall status
    statuses = [c[2].get("status", "skip") for c in checks]
    if any(s == "fail" for s in statuses):
        overall = "FAIL"
    elif any(s == "warning" for s in statuses):
        overall = "WARNING"
    else:
        overall = "PASS"

    # Find strongest leakage concern
    strongest = "none"
    strongest_detail = ""
    co = results.get("claim_only", {})
    if co.get("status") in ("warning", "fail"):
        strongest = "claim-only shortcut"
        strongest_detail = (
            f"claim-only TF-IDF+LR strong_F1={co.get('strong_f1_mean', 0)} "
            f"(ratio to R4={co.get('ratio_claim_only_to_r4', 0)})"
        )
    se = results.get("shuffled_evidence", {})
    if se.get("status") == "warning":
        if strongest == "none":
            strongest = "evidence insensitivity"
            strongest_detail = (
                f"correct evidence overlap={se.get('mean_correct_evidence_overlap', 0)} "
                f"vs shuffled={se.get('mean_cross_group_shuffled_overlap', 0)}"
            )
    lc = results.get("lexical_cues", {})
    if lc.get("status") in ("warning", "fail"):
        if strongest == "none":
            strongest = "lexical cue leakage"
            strongest_detail = f"max_cues_per_label={lc.get('max_cues_per_label', 0)}"
    pd = results.get("policy_dist", {})
    if pd.get("status") == "warning":
        if strongest == "none":
            strongest = "policy-label concentration"
            strongest_detail = f"max_concentration={pd.get('max_policy_label_concentration', 0)}"

    lines = [
        "# Leakage Audit Summary",
        "",
        f"Generated: {results.get('timestamp', '')}",
        "",
        f"## Overall Status: **{overall}**",
        "",
        f"**Strongest leakage concern**: {strongest}",
        f"",
        f"  {strongest_detail}" if strongest_detail else "  (no significant concern detected)",
        "",
        "## What This Means for Paper Wording",
        "",
        "**Safe wording** (allowed):",
        "- \"controlled silver diagnostic\"",
        "- \"silver-labeled retrieval-to-screening diagnostic\"",
        "- \"not a gold benchmark\"",
        "- \"not human-audited\"",
        "- \"not a validated general detector\"",
        "",
        "**Unsafe wording** (forbidden):",
        "- \"gold benchmark\"",
        "- \"validated general detector\"",
        "- \"human-audited\"",
        "- \"SOTA\"",
        "- \"generalizes to real claims\"",
        "",
        "If overall status is WARNING or FAIL, the dataset shows evidence of",
        "shortcuts or label contingencies. R4 results on this set should be",
        "interpreted as diagnostic (does the pipeline run end-to-end?), not as",
        "generalization performance.",
        "",
        "## Check Results",
        "",
        "| # | Check | Status | Key Metric |",
        "|---|-------|--------|------------|",
    ]

    for num, name, res in checks:
        status = res.get("status", "skip")
        metric = ""
        if "strong_f1_mean" in res:
            metric = f"strong_F1={res['strong_f1_mean']} (ratio to R4={res.get('ratio_claim_only_to_r4', '?')})"
        elif "mean_correct_evidence_overlap" in res and "mean_empty_evidence_overlap" in res:
            metric = f"correct_overlap={res['mean_correct_evidence_overlap']}"
        elif "mean_correct_evidence_overlap" in res:
            metric = f"correct={res['mean_correct_evidence_overlap']}, shuffled={res.get('mean_cross_group_shuffled_overlap', '?')}"
        elif "ratio" in res:
            metric = f"ratio={res['ratio']}"
        elif "mean_overlap" in res:
            metric = f"mean_overlap={res['mean_overlap']}"
        elif "mean_page_purity" in res:
            metric = f"purity={res['mean_page_purity']}"
        elif "max_cues_per_label" in res:
            metric = f"max_cues={res['max_cues_per_label']}"
        elif "overlap_ratio_across_labels" in res:
            metric = f"overlap_ratio={res['overlap_ratio_across_labels']}"
        elif "max_cue_ratio_across_labels" in res:
            metric = f"max_cue_ratio={res['max_cue_ratio_across_labels']}"
        elif "n_cross_split_groups" in res:
            metric = f"cross_groups={res['n_cross_split_groups']}"
        elif "max_policy_label_concentration" in res:
            metric = f"max_concentration={res['max_policy_label_concentration']}"
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
        "## Methodology Notes",
        "",
        "- claim-only baseline uses TF-IDF (unigram+bigram, 5000 features) +",
        "  LogisticRegression with GroupKFold (group-aware cross-validation).",
        "- Evidence sanity baselines use Jaccard token overlap as a proxy for",
        "  screening utility (frozen R4 eval is blocked by sklearn version mismatch).",
        "- Cue word rates are computed against fixed heuristic word lists",
        "  (action, certainty, deployment, safety). These are diagnostic, not",
        "  comprehensive.",
        "- Policy-label concentration tests whether certain generation policies",
        "  are biased toward certain labels (expected: 25% for balanced 4-label).",
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
    print(f"  {len(true_labels)} labels for audit (source: candidate_label_guess / silver)")

    # --- Run 12 checks ---
    print("\nRunning 12 leakage checks ...")
    timestamp = datetime.now(timezone.utc).isoformat()

    claim_only = check_claim_only_baseline_tfidf(candidates, true_labels)
    empty_evidence = check_empty_evidence_baseline(candidates, true_labels)
    shuffled_evidence = check_shuffled_evidence_baseline(candidates, true_labels)
    title_only = check_title_only_retrieval(candidates)
    metadata_only = check_metadata_only_retrieval(candidates)
    lexical_overlap = check_lexical_overlap_by_label(candidates, true_labels)
    cue_words = check_cue_words_by_label(candidates, true_labels)
    lexical_cues = check_label_lexical_cues(candidates, true_labels)
    group_split = check_group_split_integrity(candidates)
    policy_dist = check_generation_policy_distribution(candidates)
    selector_oracle = check_no_oracle_in_selector(canonicalizer_guard)
    queue_forbidden = check_no_label_in_queue_sorting(queue_guard)

    # --- Write outputs (11 files + audit_summary.md) ---
    write_json(output_dir / "claim_only_baseline.json", claim_only)
    write_json(output_dir / "empty_evidence_baseline.json", empty_evidence)
    write_json(output_dir / "shuffled_evidence_baseline.json", shuffled_evidence)
    write_json(output_dir / "title_only_retrieval_baseline.json", title_only)
    write_json(output_dir / "metadata_only_retrieval_baseline.json", metadata_only)
    write_lexical_overlap_csv(output_dir / "lexical_overlap_by_label.csv", lexical_overlap)
    write_cue_words_csv(output_dir / "cue_words_by_label.csv", cue_words)
    write_json(output_dir / "group_split_integrity.json", group_split)
    write_json(output_dir / "generation_policy_distribution.json", policy_dist)
    write_json(output_dir / "no_oracle_in_selector_check.json", selector_oracle)
    write_json(output_dir / "no_label_in_queue_sorting_check.json", queue_forbidden)

    all_results = {
        "timestamp": timestamp,
        "claim_only": claim_only,
        "empty_evidence": empty_evidence,
        "shuffled_evidence": shuffled_evidence,
        "title_only": title_only,
        "metadata_only": metadata_only,
        "lexical_overlap": lexical_overlap,
        "cue_words": cue_words,
        "lexical_cues": lexical_cues,
        "group_split": group_split,
        "policy_dist": policy_dist,
        "selector_oracle": selector_oracle,
        "queue_forbidden": queue_forbidden,
    }
    write_audit_summary(output_dir / "audit_summary.md", all_results)

    print(f"\nWrote 12 files to {output_dir}")
    print("\nCheck summary:")
    for name, res in [
        ("claim_only", claim_only),
        ("empty_evidence", empty_evidence),
        ("shuffled_evidence", shuffled_evidence),
        ("title_only", title_only),
        ("metadata_only", metadata_only),
        ("lexical_overlap", lexical_overlap),
        ("cue_words", cue_words),
        ("lexical_cues", lexical_cues),
        ("group_split", group_split),
        ("policy_dist", policy_dist),
        ("selector_oracle", selector_oracle),
        ("queue_forbidden", queue_forbidden),
    ]:
        print(f"  {name}: {res.get('status', 'skip')}")

    # --- Schema validation ---
    schema_reports = [
        validate_json_file(output_dir / "claim_only_baseline.json", "leakage_audit"),
        validate_json_file(output_dir / "empty_evidence_baseline.json", "leakage_audit"),
        validate_json_file(output_dir / "shuffled_evidence_baseline.json", "leakage_audit"),
        validate_json_file(output_dir / "title_only_retrieval_baseline.json", "leakage_audit"),
        validate_json_file(output_dir / "metadata_only_retrieval_baseline.json", "leakage_audit"),
        validate_json_file(output_dir / "group_split_integrity.json", "leakage_audit"),
        validate_json_file(output_dir / "generation_policy_distribution.json", "leakage_audit"),
        validate_json_file(output_dir / "no_oracle_in_selector_check.json", "leakage_audit"),
        validate_json_file(output_dir / "no_label_in_queue_sorting_check.json", "leakage_audit"),
    ]
    write_schema_validation_report(
        output_dir, schema_reports, script_name="run_leakage_audit_v1.py"
    )
    print("Wrote schema_validation_report.json")

    write_run_config(output_dir, config, "run_leakage_audit_v1.py",
                     extra={"toy_mode": args.toy_mode, "n_checks": 12})
    print("Wrote run_config.json")
    print("Done.")


if __name__ == "__main__":
    main()
