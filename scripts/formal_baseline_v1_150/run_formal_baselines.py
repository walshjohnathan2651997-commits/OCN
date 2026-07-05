import csv
import json
import math
import random
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data" / "simclaim_mvp_expansion_v1_150"
EXP_ROOT = ROOT / "experiments" / "formal_baseline_v1_150"
INPUT_DIR = EXP_ROOT / "inputs"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
ERROR_DIR = EXP_ROOT / "errors"
REPORT_DIR = EXP_ROOT / "reports"

TRAIN_PATH = DATA_ROOT / "splits" / "train.csv"
DEV_PATH = DATA_ROOT / "splits" / "dev.csv"
TEST_PATH = DATA_ROOT / "splits" / "test.csv"
ALL_PATH = DATA_ROOT / "candidates" / "simclaim_mvp_expansion_candidates_150.csv"
PAPER_PATH = DATA_ROOT / "paper_facing_schema" / "simclaim_mvp_expansion_150_paper_facing.csv"

SEED = 50
RNG = np.random.default_rng(SEED)
random.seed(SEED)


TARGETS = [
    "escalation_binary_label_guess",
    "issue_binary_label_guess",
]

TEXT_VIEWS = [
    "claim_only",
    "evidence_only",
    "claim_evidence",
    "claim_evidence_plus_overlap",
]

MODELS = [
    "majority",
    "claim_length_median_rule",
    "tfidf_centroid",
    "tfidf_logistic_l2",
    "tfidf_linear_svm_hinge",
]

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]+")


def ensure_dirs():
    for p in [INPUT_DIR, METRIC_DIR, PRED_DIR, ERROR_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)


def copy_inputs():
    for src, name in [
        (TRAIN_PATH, "train.csv"),
        (DEV_PATH, "dev.csv"),
        (TEST_PATH, "test.csv"),
        (ALL_PATH, "all_candidates_150.csv"),
        (PAPER_PATH, "paper_facing_150.csv"),
    ]:
        dst = INPUT_DIR / name
        dst.write_bytes(src.read_bytes())


def read_split(path, split):
    df = pd.read_csv(path, dtype=str).fillna("")
    df["eval_split"] = split
    return df


def tokenize(text):
    return TOKEN_RE.findall(str(text).lower())


def word_ngrams(tokens, ngram_range=(1, 2)):
    out = []
    lo, hi = ngram_range
    for n in range(lo, hi + 1):
        if len(tokens) < n:
            continue
        for i in range(len(tokens) - n + 1):
            out.append("__".join(tokens[i : i + n]))
    return out


def text_for_view(row, view):
    claim = str(row.get("claim_text", ""))
    evidence = str(row.get("evidence_text", ""))
    if view == "claim_only":
        return claim
    if view == "evidence_only":
        return evidence
    return f"claim: {claim} evidence: {evidence}"


def overlap_features(df, train_stats=None):
    vals = []
    for _, row in df.iterrows():
        claim_tokens = set(tokenize(row.get("claim_text", "")))
        evidence_tokens = set(tokenize(row.get("evidence_text", "")))
        inter = claim_tokens & evidence_tokens
        union = claim_tokens | evidence_tokens
        claim_len = len(str(row.get("claim_text", "")))
        evidence_len = len(str(row.get("evidence_text", "")))
        claim_words = len(tokenize(row.get("claim_text", "")))
        evidence_words = len(tokenize(row.get("evidence_text", "")))
        jaccard = len(inter) / len(union) if union else 0.0
        claim_covered = len(inter) / len(claim_tokens) if claim_tokens else 0.0
        evidence_covered = len(inter) / len(evidence_tokens) if evidence_tokens else 0.0
        vals.append(
            [
                claim_len,
                evidence_len,
                evidence_len - claim_len,
                claim_words,
                evidence_words,
                evidence_words - claim_words,
                jaccard,
                claim_covered,
                evidence_covered,
            ]
        )
    arr = np.asarray(vals, dtype=float)
    if train_stats is None:
        mean = arr.mean(axis=0)
        std = arr.std(axis=0)
        std[std == 0] = 1.0
        train_stats = (mean, std)
    mean, std = train_stats
    return (arr - mean) / std, train_stats


class TfidfVectorizerLite:
    def __init__(self, max_features=4000, min_df=1, ngram_range=(1, 2)):
        self.max_features = max_features
        self.min_df = min_df
        self.ngram_range = ngram_range
        self.vocab_ = {}
        self.idf_ = None

    def fit(self, texts):
        doc_freq = Counter()
        term_freq = Counter()
        for text in texts:
            terms = word_ngrams(tokenize(text), self.ngram_range)
            term_freq.update(terms)
            doc_freq.update(set(terms))
        candidates = [
            term
            for term, df in doc_freq.items()
            if df >= self.min_df
        ]
        candidates.sort(key=lambda term: (-term_freq[term], term))
        candidates = candidates[: self.max_features]
        self.vocab_ = {term: i for i, term in enumerate(candidates)}
        n_docs = len(list(texts)) if not isinstance(texts, list) else len(texts)
        self.idf_ = np.ones(len(self.vocab_), dtype=float)
        for term, idx in self.vocab_.items():
            self.idf_[idx] = math.log((1 + n_docs) / (1 + doc_freq[term])) + 1.0
        return self

    def transform(self, texts):
        x = np.zeros((len(texts), len(self.vocab_)), dtype=float)
        for i, text in enumerate(texts):
            counts = Counter(word_ngrams(tokenize(text), self.ngram_range))
            for term, count in counts.items():
                idx = self.vocab_.get(term)
                if idx is not None:
                    x[i, idx] = 1.0 + math.log(count)
        if self.idf_ is not None and len(self.idf_):
            x *= self.idf_
        norms = np.linalg.norm(x, axis=1, keepdims=True)
        norms[norms == 0] = 1.0
        return x / norms


def build_features(train_df, eval_df, view):
    train_texts = [text_for_view(row, view) for _, row in train_df.iterrows()]
    eval_texts = [text_for_view(row, view) for _, row in eval_df.iterrows()]
    vectorizer = TfidfVectorizerLite(max_features=4000, min_df=1, ngram_range=(1, 2))
    vectorizer.fit(list(train_texts))
    x_train = vectorizer.transform(list(train_texts))
    x_eval = vectorizer.transform(list(eval_texts))
    meta = {"vocab_size": len(vectorizer.vocab_), "features": "tfidf_word_1_2grams"}
    if view == "claim_evidence_plus_overlap":
        train_overlap, stats = overlap_features(train_df)
        eval_overlap, _ = overlap_features(eval_df, stats)
        x_train = np.hstack([x_train, train_overlap])
        x_eval = np.hstack([x_eval, eval_overlap])
        meta["features"] = "tfidf_word_1_2grams_plus_overlap_numeric"
        meta["overlap_feature_count"] = train_overlap.shape[1]
    return x_train, x_eval, meta


def majority_predict(y_train, n):
    counts = Counter(y_train)
    majority = sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]
    return np.full(n, majority, dtype=int)


def length_rule_predict(train_df, eval_df, y_train):
    lengths = train_df["claim_text"].astype(str).str.len().to_numpy()
    threshold = float(np.median(lengths))
    train_pred = (lengths > threshold).astype(int)
    # If the direction is inverted on train, flip it.
    acc = (train_pred == y_train).mean()
    flip = acc < 0.5
    pred = (eval_df["claim_text"].astype(str).str.len().to_numpy() > threshold).astype(int)
    if flip:
        pred = 1 - pred
    return pred


def centroid_predict(x_train, y_train, x_eval):
    classes = [0, 1]
    centroids = []
    for c in classes:
        rows = x_train[y_train == c]
        if len(rows) == 0:
            centroids.append(np.zeros(x_train.shape[1]))
        else:
            centroid = rows.mean(axis=0)
            norm = np.linalg.norm(centroid)
            if norm > 0:
                centroid = centroid / norm
            centroids.append(centroid)
    scores = np.vstack([x_eval @ centroids[0], x_eval @ centroids[1]]).T
    return np.argmax(scores, axis=1)


def class_weights(y):
    counts = Counter(y)
    total = len(y)
    return np.asarray([total / (2 * counts[int(v)]) for v in y], dtype=float)


def sigmoid(z):
    z = np.clip(z, -40, 40)
    return 1.0 / (1.0 + np.exp(-z))


def fit_logistic(x, y, epochs=900, lr=0.35, l2=1e-4):
    n, d = x.shape
    w = RNG.normal(0, 0.01, size=d)
    prior = np.clip(y.mean(), 1e-4, 1 - 1e-4)
    b = math.log(prior / (1 - prior))
    weights = class_weights(y)
    for epoch in range(epochs):
        p = sigmoid(x @ w + b)
        err = (p - y) * weights
        grad_w = (x.T @ err) / n + l2 * w
        grad_b = err.mean()
        step = lr / math.sqrt(1 + epoch / 80)
        w -= step * grad_w
        b -= step * grad_b
    return w, b


def logistic_predict(x_train, y_train, x_eval):
    w, b = fit_logistic(x_train, y_train)
    p = sigmoid(x_eval @ w + b)
    return (p >= 0.5).astype(int), p


def fit_linear_svm(x, y, epochs=900, lr=0.25, l2=1e-4):
    y2 = np.where(y == 1, 1.0, -1.0)
    n, d = x.shape
    w = RNG.normal(0, 0.01, size=d)
    b = 0.0
    weights = class_weights(y)
    for epoch in range(epochs):
        margins = y2 * (x @ w + b)
        active = margins < 1
        if np.any(active):
            coeff = -y2[active] * weights[active]
            grad_w = (x[active].T @ coeff) / n + l2 * w
            grad_b = coeff.mean()
        else:
            grad_w = l2 * w
            grad_b = 0.0
        step = lr / math.sqrt(1 + epoch / 80)
        w -= step * grad_w
        b -= step * grad_b
    return w, b


def svm_predict(x_train, y_train, x_eval):
    w, b = fit_linear_svm(x_train, y_train)
    score = x_eval @ w + b
    return (score >= 0).astype(int), score


def confusion(y_true, y_pred):
    out = {(0, 0): 0, (0, 1): 0, (1, 0): 0, (1, 1): 0}
    for a, b in zip(y_true, y_pred):
        out[(int(a), int(b))] += 1
    return out


def compute_metrics(y_true, y_pred):
    y_true = np.asarray(y_true, dtype=int)
    y_pred = np.asarray(y_pred, dtype=int)
    cm = confusion(y_true, y_pred)
    accuracy = float((y_true == y_pred).mean()) if len(y_true) else 0.0
    per_class = {}
    f1s = []
    for c in [0, 1]:
        tp = cm[(c, c)]
        fp = sum(cm[(a, c)] for a in [0, 1] if a != c)
        fn = sum(cm[(c, b)] for b in [0, 1] if b != c)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
        per_class[str(c)] = {
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1": round(f1, 4),
            "support": int(sum(y_true == c)),
        }
        f1s.append(f1)
    return {
        "accuracy": round(accuracy, 4),
        "macro_f1": round(sum(f1s) / 2, 4),
        "class0_precision": per_class["0"]["precision"],
        "class0_recall": per_class["0"]["recall"],
        "class0_f1": per_class["0"]["f1"],
        "class1_precision": per_class["1"]["precision"],
        "class1_recall": per_class["1"]["recall"],
        "class1_f1": per_class["1"]["f1"],
        "per_class": per_class,
        "tn": cm[(0, 0)],
        "fp": cm[(0, 1)],
        "fn": cm[(1, 0)],
        "tp": cm[(1, 1)],
    }


def run_one(train_df, eval_df, target, view, model):
    y_train = train_df[target].astype(int).to_numpy()
    y_eval = eval_df[target].astype(int).to_numpy()
    score = np.zeros(len(eval_df), dtype=float)
    meta = {}
    if model == "majority":
        pred = majority_predict(y_train, len(eval_df))
        score = pred.astype(float)
        meta = {"features": "none"}
    elif model == "claim_length_median_rule":
        pred = length_rule_predict(train_df, eval_df, y_train)
        score = pred.astype(float)
        meta = {"features": "claim_length_only"}
    else:
        x_train, x_eval, meta = build_features(train_df, eval_df, view)
        if model == "tfidf_centroid":
            pred = centroid_predict(x_train, y_train, x_eval)
            score = pred.astype(float)
        elif model == "tfidf_logistic_l2":
            pred, score = logistic_predict(x_train, y_train, x_eval)
        elif model == "tfidf_linear_svm_hinge":
            pred, score = svm_predict(x_train, y_train, x_eval)
        else:
            raise ValueError(model)
    metrics = compute_metrics(y_eval, pred)
    return pred, score, metrics, meta


def write_csv(path, rows, fieldnames):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def risk_flag(row):
    flags = str(row.get("quality_flags", ""))
    risk_terms = ["needs_human_review", "contradiction_uncertain", "evidence_too_short", "possible_metadata_leakage"]
    found = [x for x in risk_terms if x in flags]
    return "|".join(found)


def main():
    ensure_dirs()
    copy_inputs()
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    train_df = read_split(TRAIN_PATH, "train")
    dev_df = read_split(DEV_PATH, "dev")
    test_df = read_split(TEST_PATH, "test")
    all_df = pd.concat([train_df, dev_df, test_df], ignore_index=True)

    metric_rows = []
    confusion_rows = []
    per_class_rows = []
    prediction_rows = []

    eval_sets = [("dev", dev_df), ("test", test_df)]

    for target in TARGETS:
        for view in TEXT_VIEWS:
            for model in MODELS:
                if model in {"majority", "claim_length_median_rule"} and view != "claim_evidence":
                    continue
                for split_name, eval_df in eval_sets:
                    pred, score, met, meta = run_one(train_df, eval_df, target, view, model)
                    metric_rows.append(
                        {
                            "generated_at_utc": generated_at,
                            "target": target,
                            "input_view": view,
                            "model": model,
                            "eval_split": split_name,
                            "n_train": len(train_df),
                            "n_eval": len(eval_df),
                            "accuracy": met["accuracy"],
                            "macro_f1": met["macro_f1"],
                            "class0_precision": met["class0_precision"],
                            "class0_recall": met["class0_recall"],
                            "class0_f1": met["class0_f1"],
                            "class1_precision": met["class1_precision"],
                            "class1_recall": met["class1_recall"],
                            "class1_f1": met["class1_f1"],
                            "feature_info_json": json.dumps(meta, ensure_ascii=False),
                            "notes": "formal small-data baseline; labels are AI-preannotated, not gold",
                        }
                    )
                    confusion_rows.append(
                        {
                            "target": target,
                            "input_view": view,
                            "model": model,
                            "eval_split": split_name,
                            "tn": met["tn"],
                            "fp": met["fp"],
                            "fn": met["fn"],
                            "tp": met["tp"],
                        }
                    )
                    for cls, vals in met["per_class"].items():
                        row = {
                            "target": target,
                            "input_view": view,
                            "model": model,
                            "eval_split": split_name,
                            "class_label": cls,
                        }
                        row.update(vals)
                        per_class_rows.append(row)
                    for i, (_, row) in enumerate(eval_df.iterrows()):
                        prediction_rows.append(
                            {
                                "target": target,
                                "input_view": view,
                                "model": model,
                                "eval_split": split_name,
                                "candidate_id": row.get("candidate_id", ""),
                                "source_pair_id": row.get("source_pair_id", ""),
                                "split_group_id": row.get("split_group_id", ""),
                                "domain": row.get("domain", ""),
                                "candidate_label_guess": row.get("candidate_label_guess", ""),
                                "gold_proxy_label": int(row[target]),
                                "pred_label": int(pred[i]),
                                "score": round(float(score[i]), 6),
                                "is_error": int(int(row[target]) != int(pred[i])),
                                "risk_flags": risk_flag(row),
                                "claim_text": row.get("claim_text", ""),
                                "evidence_text": row.get("evidence_text", ""),
                            }
                        )

    metric_fields = [
        "generated_at_utc",
        "target",
        "input_view",
        "model",
        "eval_split",
        "n_train",
        "n_eval",
        "accuracy",
        "macro_f1",
        "class0_precision",
        "class0_recall",
        "class0_f1",
        "class1_precision",
        "class1_recall",
        "class1_f1",
        "feature_info_json",
        "notes",
    ]
    write_csv(METRIC_DIR / "formal_baseline_metrics.csv", metric_rows, metric_fields)
    write_csv(METRIC_DIR / "confusion_matrices.csv", confusion_rows, ["target", "input_view", "model", "eval_split", "tn", "fp", "fn", "tp"])
    write_csv(
        METRIC_DIR / "per_class_metrics.csv",
        per_class_rows,
        ["target", "input_view", "model", "eval_split", "class_label", "precision", "recall", "f1", "support"],
    )
    write_csv(
        PRED_DIR / "predictions_all.csv",
        prediction_rows,
        [
            "target",
            "input_view",
            "model",
            "eval_split",
            "candidate_id",
            "source_pair_id",
            "split_group_id",
            "domain",
            "candidate_label_guess",
            "gold_proxy_label",
            "pred_label",
            "score",
            "is_error",
            "risk_flags",
            "claim_text",
            "evidence_text",
        ],
    )

    error_rows = [r for r in prediction_rows if r["is_error"] == 1]
    write_csv(
        ERROR_DIR / "error_cases_all.csv",
        error_rows,
        [
            "target",
            "input_view",
            "model",
            "eval_split",
            "candidate_id",
            "source_pair_id",
            "split_group_id",
            "domain",
            "candidate_label_guess",
            "gold_proxy_label",
            "pred_label",
            "score",
            "is_error",
            "risk_flags",
            "claim_text",
            "evidence_text",
        ],
    )

    # Pick best non-diagnostic model by dev macro-F1 per target.
    best_by_target = []
    for target in TARGETS:
        candidates = [
            r for r in metric_rows
            if r["target"] == target
            and r["eval_split"] == "dev"
            and r["model"] not in {"majority", "claim_length_median_rule"}
        ]
        candidates.sort(key=lambda r: (-float(r["macro_f1"]), -float(r["accuracy"]), r["model"], r["input_view"]))
        if candidates:
            best = candidates[0]
            matching_test = [
                r for r in metric_rows
                if r["target"] == target
                and r["eval_split"] == "test"
                and r["model"] == best["model"]
                and r["input_view"] == best["input_view"]
            ][0]
            best_by_target.append(
                {
                    "target": target,
                    "selected_by": "dev_macro_f1",
                    "model": best["model"],
                    "input_view": best["input_view"],
                    "dev_macro_f1": best["macro_f1"],
                    "dev_accuracy": best["accuracy"],
                    "test_macro_f1": matching_test["macro_f1"],
                    "test_accuracy": matching_test["accuracy"],
                    "test_class0_f1": matching_test["class0_f1"],
                    "test_class1_f1": matching_test["class1_f1"],
                }
            )
    write_csv(
        METRIC_DIR / "best_by_dev_summary.csv",
        best_by_target,
        [
            "target",
            "selected_by",
            "model",
            "input_view",
            "dev_macro_f1",
            "dev_accuracy",
            "test_macro_f1",
            "test_accuracy",
            "test_class0_f1",
            "test_class1_f1",
        ],
    )

    # Ablation summary for test split: best per view among learned models.
    ablation_rows = []
    for target in TARGETS:
        for view in TEXT_VIEWS:
            candidates = [
                r for r in metric_rows
                if r["target"] == target
                and r["eval_split"] == "test"
                and r["input_view"] == view
                and r["model"] in {"tfidf_centroid", "tfidf_logistic_l2", "tfidf_linear_svm_hinge"}
            ]
            candidates.sort(key=lambda r: (-float(r["macro_f1"]), -float(r["accuracy"]), r["model"]))
            if candidates:
                top = candidates[0]
                ablation_rows.append(
                    {
                        "target": target,
                        "input_view": view,
                        "best_model_on_test_for_view": top["model"],
                        "test_accuracy": top["accuracy"],
                        "test_macro_f1": top["macro_f1"],
                        "test_class0_f1": top["class0_f1"],
                        "test_class1_f1": top["class1_f1"],
                    }
                )
    write_csv(
        METRIC_DIR / "ablation_summary.csv",
        ablation_rows,
        ["target", "input_view", "best_model_on_test_for_view", "test_accuracy", "test_macro_f1", "test_class0_f1", "test_class1_f1"],
    )

    # Risk error summary.
    risk_summary = []
    for target in TARGETS:
        primary = next((r for r in best_by_target if r["target"] == target), None)
        if not primary:
            continue
        selected_errors = [
            r for r in error_rows
            if r["target"] == target
            and r["eval_split"] == "test"
            and r["model"] == primary["model"]
            and r["input_view"] == primary["input_view"]
        ]
        flag_counts = Counter()
        for r in selected_errors:
            if r["risk_flags"]:
                flag_counts.update(r["risk_flags"].split("|"))
            else:
                flag_counts.update(["no_risk_flag"])
        for flag, count in flag_counts.items():
            risk_summary.append({"target": target, "selected_model": primary["model"], "selected_view": primary["input_view"], "risk_flag": flag, "test_error_count": count})
    write_csv(METRIC_DIR / "risk_error_summary.csv", risk_summary, ["target", "selected_model", "selected_view", "risk_flag", "test_error_count"])

    config = {
        "generated_at_utc": generated_at,
        "seed": SEED,
        "source_dataset": str(ALL_PATH),
        "train": str(TRAIN_PATH),
        "dev": str(DEV_PATH),
        "test": str(TEST_PATH),
        "targets": TARGETS,
        "text_views": TEXT_VIEWS,
        "models": MODELS,
        "dependency_note": "Implemented with numpy/pandas because sklearn/scipy were unavailable in the local runtime.",
        "label_warning": "Labels are AI-preannotated proxy labels, not gold or human-audited labels.",
    }
    (REPORT_DIR / "run_config.json").write_text(json.dumps(config, ensure_ascii=False, indent=2), encoding="utf-8")

    report_lines = [
        "# Formal Baseline v1 150 Report",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "## Scope",
        "",
        "- Dataset: `simclaim_mvp_expansion_v1_150`",
        "- Train/dev/test: 90 / 30 / 30",
        "- Models: majority, claim-length rule, TF-IDF centroid, TF-IDF logistic L2, TF-IDF linear SVM hinge",
        "- Labels are AI-preannotated proxy labels, not gold.",
        "- No original dataset files were modified.",
        "",
        "## Best learned models selected by dev macro-F1",
        "",
        "| target | model | input_view | dev macro-F1 | test macro-F1 | test accuracy | test class0 F1 | test class1 F1 |",
        "|---|---|---|---:|---:|---:|---:|---:|",
    ]
    for row in best_by_target:
        report_lines.append(
            f"| {row['target']} | {row['model']} | {row['input_view']} | {row['dev_macro_f1']} | {row['test_macro_f1']} | {row['test_accuracy']} | {row['test_class0_f1']} | {row['test_class1_f1']} |"
        )
    report_lines.extend(
        [
            "",
            "## Test ablation summary",
            "",
            "| target | input_view | best model | test macro-F1 | test accuracy |",
            "|---|---|---|---:|---:|",
        ]
    )
    for row in ablation_rows:
        report_lines.append(
            f"| {row['target']} | {row['input_view']} | {row['best_model_on_test_for_view']} | {row['test_macro_f1']} | {row['test_accuracy']} |"
        )
    report_lines.extend(
        [
            "",
            "## Interpretation guardrails",
            "",
            "- These are formal small-data baselines, but still use AI-preannotated proxy labels.",
            "- Results show whether the 150-row scaffold contains learnable signal.",
            "- Scores should not be reported as final paper performance until labels are audited.",
            "- Dev/test have only 30 rows each, so a single error changes accuracy by 3.33 percentage points.",
            "",
            "## Output files",
            "",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\metrics\\formal_baseline_metrics.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\metrics\\best_by_dev_summary.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\metrics\\ablation_summary.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\metrics\\confusion_matrices.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\errors\\error_cases_all.csv`",
        ]
    )
    (REPORT_DIR / "formal_baseline_report.md").write_text("\n".join(report_lines) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "generated_at_utc": generated_at,
                "metric_rows": len(metric_rows),
                "prediction_rows": len(prediction_rows),
                "error_rows": len(error_rows),
                "best_by_target": best_by_target,
                "metrics_csv": str(METRIC_DIR / "formal_baseline_metrics.csv"),
                "report": str(REPORT_DIR / "formal_baseline_report.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
