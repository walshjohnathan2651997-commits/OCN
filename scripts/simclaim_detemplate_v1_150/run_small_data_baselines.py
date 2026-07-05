import csv
import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data" / "simclaim_detemplate_v1_150"
SPLIT_ROOT = DATA_ROOT / "splits_group_stratified"
EXP_ROOT = ROOT / "experiments" / "simclaim_detemplate_v1_150_small_baselines"
METRIC_DIR = EXP_ROOT / "metrics"
PRED_DIR = EXP_ROOT / "predictions"
REPORT_DIR = EXP_ROOT / "reports"

METRICS_CSV = METRIC_DIR / "small_data_baseline_metrics.csv"
PER_CLASS_CSV = METRIC_DIR / "small_data_baseline_per_class_f1.csv"
PRED_CSV = PRED_DIR / "small_data_baseline_predictions.csv"
SUMMARY_JSON = REPORT_DIR / "small_data_baseline_summary.json"
REPORT_MD = REPORT_DIR / "small_data_baseline_report.md"

TARGETS = [
    "issue_binary_label_guess",
    "escalation_binary_label_guess",
    "candidate_label_guess",
]

TEXT_VIEWS = [
    "claim_only",
    "evidence_only",
    "claim_evidence",
]

TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]+")
NUMBER_RE = re.compile(r"\b\d+(?:\.\d+)?\b")
STOPWORDS = {
    "a", "an", "and", "are", "as", "at", "be", "by", "for", "from", "in", "into",
    "is", "it", "of", "on", "or", "that", "the", "their", "this", "to", "was",
    "were", "with", "within", "same", "described", "research", "context",
}
NEGATION_TERMS = {"no", "not", "never", "without", "cannot", "absent", "different", "inaccurate", "unrealistic", "underperforms"}


def ensure_dirs():
    for p in [METRIC_DIR, PRED_DIR, REPORT_DIR]:
        p.mkdir(parents=True, exist_ok=True)


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


def normalize_space(text):
    return re.sub(r"\s+", " ", (text or "")).strip()


def tokenize(text):
    return TOKEN_RE.findall((text or "").lower())


def content_tokens(text):
    return [tok for tok in tokenize(text) if tok not in STOPWORDS and len(tok) > 2]


def numbers(text):
    return NUMBER_RE.findall((text or "").lower())


def ngrams(tokens):
    out = []
    out.extend(tokens)
    out.extend([tokens[i] + "__" + tokens[i + 1] for i in range(len(tokens) - 1)])
    return out


def text_for_view(row, view):
    claim = row.get("claim_text", "")
    evidence = row.get("evidence_text", "")
    if view == "claim_only":
        return claim
    if view == "evidence_only":
        return evidence
    return "claim: " + claim + " evidence: " + evidence


def prefix_key(text, n=4):
    clean = normalize_space(re.sub(r"[^\w\s:-]", " ", (text or "").lower()))
    return " ".join(clean.split()[:n])


def labels_for(rows, target):
    return [(r.get(target) or "").strip() for r in rows]


def accuracy(y_true, y_pred):
    return sum(1 for a, b in zip(y_true, y_pred) if a == b) / len(y_true) if y_true else 0.0


def f1_by_class(y_true, y_pred):
    labels = sorted(set(y_true) | set(y_pred))
    out = {}
    for label in labels:
        tp = sum(1 for a, b in zip(y_true, y_pred) if a == label and b == label)
        fp = sum(1 for a, b in zip(y_true, y_pred) if a != label and b == label)
        fn = sum(1 for a, b in zip(y_true, y_pred) if a == label and b != label)
        precision = tp / (tp + fp) if tp + fp else 0.0
        recall = tp / (tp + fn) if tp + fn else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if precision + recall else 0.0
        out[label] = {"precision": precision, "recall": recall, "f1": f1, "support": sum(1 for x in y_true if x == label)}
    return out


def macro_f1(y_true, y_pred):
    vals = f1_by_class(y_true, y_pred)
    return sum(v["f1"] for v in vals.values()) / len(vals) if vals else 0.0


def majority_predict(train_rows, eval_rows, target):
    majority = Counter(labels_for(train_rows, target)).most_common(1)[0][0]
    return [majority for _ in eval_rows]


def prefix_memorize_predict(train_rows, eval_rows, target, n=4):
    default = Counter(labels_for(train_rows, target)).most_common(1)[0][0]
    by_key = defaultdict(Counter)
    for row in train_rows:
        by_key[prefix_key(row.get("claim_text", ""), n)][(row.get(target) or "").strip()] += 1
    mapping = {k: c.most_common(1)[0][0] for k, c in by_key.items()}
    return [mapping.get(prefix_key(row.get("claim_text", ""), n), default) for row in eval_rows]


def length_threshold_predict(train_rows, eval_rows, target):
    train_labels = labels_for(train_rows, target)
    if set(train_labels) - {"0", "1"}:
        return majority_predict(train_rows, eval_rows, target)
    lengths = [len(row.get("claim_text", "")) for row in train_rows]
    threshold = sorted(lengths)[len(lengths) // 2]
    pred_train = ["1" if len(row.get("claim_text", "")) > threshold else "0" for row in train_rows]
    if accuracy(train_labels, pred_train) < 0.5:
        pred_train = ["0" if p == "1" else "1" for p in pred_train]
        flip = True
    else:
        flip = False
    preds = ["1" if len(row.get("claim_text", "")) > threshold else "0" for row in eval_rows]
    if flip:
        preds = ["0" if p == "1" else "1" for p in preds]
    return preds


def build_vocab(train_rows, view, max_features=4500):
    doc_freq = Counter()
    term_freq = Counter()
    for row in train_rows:
        terms = ngrams(tokenize(text_for_view(row, view)))
        term_freq.update(terms)
        doc_freq.update(set(terms))
    vocab_terms = sorted(doc_freq, key=lambda t: (-term_freq[t], t))[:max_features]
    vocab = {term: i for i, term in enumerate(vocab_terms)}
    n_docs = len(train_rows)
    idf = {term: math.log((1 + n_docs) / (1 + doc_freq[term])) + 1.0 for term in vocab}
    return vocab, idf


def tfidf_vec(text, vocab, idf):
    counts = Counter(ngrams(tokenize(text)))
    vec = {}
    norm_sq = 0.0
    for term, count in counts.items():
        if term not in vocab:
            continue
        val = (1.0 + math.log(count)) * idf[term]
        idx = vocab[term]
        vec[idx] = val
        norm_sq += val * val
    norm = math.sqrt(norm_sq) or 1.0
    return {idx: val / norm for idx, val in vec.items()}


def dot(a, b):
    if len(a) > len(b):
        a, b = b, a
    return sum(val * b.get(idx, 0.0) for idx, val in a.items())


def tfidf_centroid_predict(train_rows, eval_rows, target, view):
    vocab, idf = build_vocab(train_rows, view)
    class_sums = defaultdict(Counter)
    class_counts = Counter()
    for row in train_rows:
        label = (row.get(target) or "").strip()
        class_counts[label] += 1
        vec = tfidf_vec(text_for_view(row, view), vocab, idf)
        for idx, val in vec.items():
            class_sums[label][idx] += val
    centroids = {}
    for label, vec in class_sums.items():
        mean_vec = {idx: val / class_counts[label] for idx, val in vec.items()}
        norm = math.sqrt(sum(v * v for v in mean_vec.values())) or 1.0
        centroids[label] = {idx: val / norm for idx, val in mean_vec.items()}
    preds = []
    for row in eval_rows:
        vec = tfidf_vec(text_for_view(row, view), vocab, idf)
        preds.append(max(centroids, key=lambda label: dot(vec, centroids[label])))
    return preds


def multinomial_nb_predict(train_rows, eval_rows, target, view, alpha=0.7):
    class_doc_counts = Counter()
    class_token_counts = defaultdict(Counter)
    vocab = set()
    for row in train_rows:
        label = (row.get(target) or "").strip()
        class_doc_counts[label] += 1
        terms = ngrams(tokenize(text_for_view(row, view)))
        class_token_counts[label].update(terms)
        vocab.update(terms)
    vocab_size = len(vocab) or 1
    total_docs = len(train_rows)
    class_total_tokens = {label: sum(counts.values()) for label, counts in class_token_counts.items()}
    labels = sorted(class_doc_counts)
    preds = []
    for row in eval_rows:
        terms = ngrams(tokenize(text_for_view(row, view)))
        scores = {}
        for label in labels:
            scores[label] = math.log(class_doc_counts[label] / total_docs)
            denom = class_total_tokens[label] + alpha * vocab_size
            counts = class_token_counts[label]
            for term in terms:
                scores[label] += math.log((counts[term] + alpha) / denom)
        preds.append(max(scores, key=scores.get))
    return preds


def pair_features(row):
    claim_tokens = content_tokens(row.get("claim_text", ""))
    evidence_tokens = content_tokens(row.get("evidence_text", ""))
    claim_set = set(claim_tokens)
    evidence_set = set(evidence_tokens)
    overlap = claim_set & evidence_set
    union = claim_set | evidence_set
    claim_only = claim_set - evidence_set
    evidence_only = evidence_set - claim_set

    claim_nums = set(numbers(row.get("claim_text", "")))
    evidence_nums = set(numbers(row.get("evidence_text", "")))
    num_union = claim_nums | evidence_nums
    num_overlap = claim_nums & evidence_nums

    claim_neg = sum(1 for tok in claim_tokens if tok in NEGATION_TERMS)
    evidence_neg = sum(1 for tok in evidence_tokens if tok in NEGATION_TERMS)

    def safe(num, den):
        return num / den if den else 0.0

    return [
        safe(len(overlap), len(claim_set)),
        safe(len(overlap), len(evidence_set)),
        safe(len(overlap), len(union)),
        safe(len(claim_only), len(claim_set)),
        safe(len(evidence_only), len(evidence_set)),
        safe(len(num_overlap), len(num_union)),
        1.0 if claim_nums and evidence_nums and claim_nums != evidence_nums else 0.0,
        float(claim_neg),
        float(abs(claim_neg - evidence_neg)),
        safe(len(claim_tokens), len(evidence_tokens)),
        float(len(claim_set)),
    ]


def pair_interaction_centroid_predict(train_rows, eval_rows, target):
    labels = sorted(set(labels_for(train_rows, target)))
    if not labels:
        return []
    train_vecs = [pair_features(row) for row in train_rows]
    n_features = len(train_vecs[0]) if train_vecs else 0
    means = [
        sum(vec[i] for vec in train_vecs) / len(train_vecs)
        for i in range(n_features)
    ]
    stds = []
    for i in range(n_features):
        var = sum((vec[i] - means[i]) ** 2 for vec in train_vecs) / len(train_vecs)
        stds.append(math.sqrt(var) or 1.0)

    def scale(vec):
        return [(vec[i] - means[i]) / stds[i] for i in range(n_features)]

    sums = {label: [0.0] * n_features for label in labels}
    counts = Counter()
    for row, vec in zip(train_rows, train_vecs):
        label = (row.get(target) or "").strip()
        counts[label] += 1
        scaled = scale(vec)
        for i, val in enumerate(scaled):
            sums[label][i] += val
    centroids = {
        label: [val / counts[label] for val in sums[label]]
        for label in labels
        if counts[label]
    }
    default = Counter(labels_for(train_rows, target)).most_common(1)[0][0]
    preds = []
    for row in eval_rows:
        vec = scale(pair_features(row))
        if not centroids:
            preds.append(default)
            continue
        preds.append(min(
            centroids,
            key=lambda label: sum((vec[i] - centroids[label][i]) ** 2 for i in range(n_features)),
        ))
    return preds


def score_run(dataset, target, split, model, view, train_rows, eval_rows, y_pred):
    y_true = labels_for(eval_rows, target)
    class_stats = f1_by_class(y_true, y_pred)
    positive_f1 = class_stats.get("1", {}).get("f1", "")
    row = {
        "dataset": dataset,
        "target": target,
        "split": split,
        "model": model,
        "text_view": view,
        "n_train": len(train_rows),
        "n_eval": len(eval_rows),
        "accuracy": f"{accuracy(y_true, y_pred):.6f}",
        "macro_f1": f"{macro_f1(y_true, y_pred):.6f}",
        "positive_class_f1": f"{positive_f1:.6f}" if positive_f1 != "" else "",
        "eval_label_distribution": json.dumps(dict(Counter(y_true)), ensure_ascii=False),
    }
    per_class = []
    for label, stats in class_stats.items():
        out = dict(row)
        out.update({
            "label": label,
            "precision": f"{stats['precision']:.6f}",
            "recall": f"{stats['recall']:.6f}",
            "class_f1": f"{stats['f1']:.6f}",
            "support": stats["support"],
        })
        per_class.append(out)
    preds = []
    for r, true, pred in zip(eval_rows, y_true, y_pred):
        preds.append({
            "candidate_id": r.get("candidate_id", ""),
            "target": target,
            "split": split,
            "model": model,
            "text_view": view,
            "true_label": true,
            "pred_label": pred,
            "correct": str(true == pred).lower(),
        })
    return row, per_class, preds


def run():
    ensure_dirs()
    train_rows = read_csv(SPLIT_ROOT / "train.csv")
    dev_rows = read_csv(SPLIT_ROOT / "dev.csv")
    test_rows = read_csv(SPLIT_ROOT / "test.csv")
    eval_sets = {"dev": dev_rows, "test": test_rows}

    metric_rows = []
    per_class_rows = []
    pred_rows = []

    for target in TARGETS:
        for split, eval_rows in eval_sets.items():
            for model in ["majority", "claim_length_median_rule", "prefix_first4_memorize"]:
                if model == "majority":
                    y_pred = majority_predict(train_rows, eval_rows, target)
                elif model == "claim_length_median_rule":
                    y_pred = length_threshold_predict(train_rows, eval_rows, target)
                else:
                    y_pred = prefix_memorize_predict(train_rows, eval_rows, target, n=4)
                row, pcs, preds = score_run(
                    "simclaim_detemplate_v1_150_group_stratified",
                    target,
                    split,
                    model,
                    "claim_only",
                    train_rows,
                    eval_rows,
                    y_pred,
                )
                metric_rows.append(row)
                per_class_rows.extend(pcs)
                pred_rows.extend(preds)

            for view in TEXT_VIEWS:
                for model in ["tfidf_centroid", "multinomial_nb"]:
                    if model == "tfidf_centroid":
                        y_pred = tfidf_centroid_predict(train_rows, eval_rows, target, view)
                    else:
                        y_pred = multinomial_nb_predict(train_rows, eval_rows, target, view)
                    row, pcs, preds = score_run(
                        "simclaim_detemplate_v1_150_group_stratified",
                        target,
                        split,
                        model,
                        view,
                        train_rows,
                        eval_rows,
                        y_pred,
                    )
                    metric_rows.append(row)
                    per_class_rows.extend(pcs)
                    pred_rows.extend(preds)

    write_csv(METRICS_CSV, metric_rows)
    write_csv(PER_CLASS_CSV, per_class_rows)
    write_csv(PRED_CSV, pred_rows)
    write_summary(metric_rows)


def write_summary(metric_rows):
    best = {}
    for row in metric_rows:
        if row["split"] != "test":
            continue
        key = row["target"]
        score = float(row["macro_f1"])
        if key not in best or score > float(best[key]["macro_f1"]):
            best[key] = row
    prefix = [
        row for row in metric_rows
        if row["split"] == "test" and row["model"] == "prefix_first4_memorize"
    ]
    summary = {
        "dataset": "simclaim_detemplate_v1_150_group_stratified",
        "best_test_by_target": best,
        "test_prefix_first4": prefix,
        "metrics_csv": str(METRICS_CSV),
        "per_class_csv": str(PER_CLASS_CSV),
        "predictions_csv": str(PRED_CSV),
        "report_md": str(REPORT_MD),
    }
    SUMMARY_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = []
    lines.append("# Small-data baseline report: detemplated v1 150")
    lines.append("")
    lines.append("Split: `data/simclaim_detemplate_v1_150/splits_group_stratified`.")
    lines.append("")
    lines.append("## Best test result by target")
    lines.append("")
    lines.append("| target | best model | view | acc | macro-F1 | positive F1 |")
    lines.append("|---|---|---|---:|---:|---:|")
    for target, row in best.items():
        lines.append(
            f"| {target} | {row['model']} | {row['text_view']} | "
            f"{row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |"
        )
    lines.append("")
    lines.append("## Prefix-only leakage check, test split")
    lines.append("")
    lines.append("| target | acc | macro-F1 | positive F1 |")
    lines.append("|---|---:|---:|---:|")
    for row in prefix:
        lines.append(f"| {row['target']} | {row['accuracy']} | {row['macro_f1']} | {row['positive_class_f1']} |")
    lines.append("")
    lines.append("## Interpretation")
    lines.append("")
    lines.append("- If prefix-only macro-F1 is far below the best claim+evidence model, template leakage is no longer dominating.")
    lines.append("- These are still AI-preannotated scaffold labels, not gold labels.")
    REPORT_MD.write_text("\n".join(lines), encoding="utf-8")


if __name__ == "__main__":
    run()
