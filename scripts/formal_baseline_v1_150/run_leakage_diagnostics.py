import csv
import json
import math
import re
from collections import Counter, defaultdict
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data" / "simclaim_mvp_expansion_v1_150"
EXP_ROOT = ROOT / "experiments" / "formal_baseline_v1_150"
METRIC_DIR = EXP_ROOT / "metrics"
REPORT_DIR = EXP_ROOT / "reports"
DIAG_DIR = EXP_ROOT / "diagnostics"
DIAG_DIR.mkdir(parents=True, exist_ok=True)

TRAIN_PATH = DATA_ROOT / "splits" / "train.csv"
DEV_PATH = DATA_ROOT / "splits" / "dev.csv"
TEST_PATH = DATA_ROOT / "splits" / "test.csv"

TARGETS = ["escalation_binary_label_guess", "issue_binary_label_guess"]
TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z0-9_\-]+")


def read(path, split):
    df = pd.read_csv(path, dtype=str).fillna("")
    df["eval_split"] = split
    return df


def tokenize(text):
    return TOKEN_RE.findall(str(text).lower())


def prefix_key(text, kind):
    text = str(text)
    toks = tokenize(text)
    if kind == "first_4_tokens":
        return " ".join(toks[:4])
    if kind == "first_6_tokens":
        return " ".join(toks[:6])
    if kind == "first_10_tokens":
        return " ".join(toks[:10])
    if kind == "before_colon":
        return text.split(":", 1)[0].strip().lower()[:160] if ":" in text else "NO_COLON"
    raise ValueError(kind)


def majority_label(labels):
    counts = Counter(int(x) for x in labels)
    return sorted(counts.items(), key=lambda kv: (-kv[1], kv[0]))[0][0]


def metrics(y_true, y_pred):
    y_true = [int(x) for x in y_true]
    y_pred = [int(x) for x in y_pred]
    accuracy = sum(a == b for a, b in zip(y_true, y_pred)) / len(y_true)
    out = {"accuracy": round(accuracy, 4)}
    f1s = []
    for c in [0, 1]:
        tp = sum(a == c and b == c for a, b in zip(y_true, y_pred))
        fp = sum(a != c and b == c for a, b in zip(y_true, y_pred))
        fn = sum(a == c and b != c for a, b in zip(y_true, y_pred))
        p = tp / (tp + fp) if tp + fp else 0
        r = tp / (tp + fn) if tp + fn else 0
        f1 = 2 * p * r / (p + r) if p + r else 0
        out[f"class{c}_precision"] = round(p, 4)
        out[f"class{c}_recall"] = round(r, 4)
        out[f"class{c}_f1"] = round(f1, 4)
        f1s.append(f1)
    out["macro_f1"] = round(sum(f1s) / 2, 4)
    return out


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def prefix_rule(train, eval_df, target, kind):
    mapping = {}
    grouped = defaultdict(list)
    for _, row in train.iterrows():
        grouped[prefix_key(row["claim_text"], kind)].append(row[target])
    for key, labels in grouped.items():
        mapping[key] = majority_label(labels)
    fallback = majority_label(train[target])
    pred = []
    for _, row in eval_df.iterrows():
        pred.append(mapping.get(prefix_key(row["claim_text"], kind), fallback))
    return pred, mapping


def token_log_odds(train, target):
    by_class = {0: Counter(), 1: Counter()}
    doc_by_class = {0: Counter(), 1: Counter()}
    n_docs = Counter()
    for _, row in train.iterrows():
        y = int(row[target])
        toks = tokenize(row["claim_text"])
        by_class[y].update(toks)
        doc_by_class[y].update(set(toks))
        n_docs[y] += 1
    vocab = set(by_class[0]) | set(by_class[1])
    total0 = sum(by_class[0].values())
    total1 = sum(by_class[1].values())
    v = max(len(vocab), 1)
    rows = []
    for tok in vocab:
        p0 = (by_class[0][tok] + 1) / (total0 + v)
        p1 = (by_class[1][tok] + 1) / (total1 + v)
        log_odds_1 = math.log(p1 / p0)
        rows.append(
            {
                "target": target,
                "token": tok,
                "count_class0": by_class[0][tok],
                "count_class1": by_class[1][tok],
                "doc_count_class0": doc_by_class[0][tok],
                "doc_count_class1": doc_by_class[1][tok],
                "log_odds_toward_class1": round(log_odds_1, 4),
            }
        )
    rows.sort(key=lambda r: -abs(float(r["log_odds_toward_class1"])))
    return rows


def prefix_distribution(df):
    rows = []
    for kind in ["first_4_tokens", "first_6_tokens", "before_colon"]:
        groups = defaultdict(lambda: Counter())
        for _, row in df.iterrows():
            groups[prefix_key(row["claim_text"], kind)][row["candidate_label_guess"]] += 1
        for key, counts in groups.items():
            total = sum(counts.values())
            rows.append(
                {
                    "prefix_kind": kind,
                    "prefix": key,
                    "n": total,
                    "distribution_json": json.dumps(dict(counts), ensure_ascii=False),
                    "dominant_label": counts.most_common(1)[0][0],
                    "dominant_rate": round(counts.most_common(1)[0][1] / total, 4),
                }
            )
    rows.sort(key=lambda r: (-r["n"], r["prefix_kind"], r["prefix"]))
    return rows


def main():
    train = read(TRAIN_PATH, "train")
    dev = read(DEV_PATH, "dev")
    test = read(TEST_PATH, "test")
    all_df = pd.concat([train, dev, test], ignore_index=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    prefix_metric_rows = []
    prefix_map_rows = []
    for target in TARGETS:
        for kind in ["first_4_tokens", "first_6_tokens", "first_10_tokens", "before_colon"]:
            for split_name, eval_df in [("dev", dev), ("test", test)]:
                pred, mapping = prefix_rule(train, eval_df, target, kind)
                met = metrics(eval_df[target].astype(int).tolist(), pred)
                row = {
                    "generated_at_utc": generated_at,
                    "target": target,
                    "prefix_kind": kind,
                    "eval_split": split_name,
                    "n_eval": len(eval_df),
                }
                row.update(met)
                prefix_metric_rows.append(row)
            _, mapping = prefix_rule(train, dev, target, kind)
            for key, label in mapping.items():
                prefix_map_rows.append({"target": target, "prefix_kind": kind, "prefix": key, "train_majority_label": label})

    write_csv(
        METRIC_DIR / "prefix_leakage_rule_metrics.csv",
        prefix_metric_rows,
        [
            "generated_at_utc",
            "target",
            "prefix_kind",
            "eval_split",
            "n_eval",
            "accuracy",
            "macro_f1",
            "class0_precision",
            "class0_recall",
            "class0_f1",
            "class1_precision",
            "class1_recall",
            "class1_f1",
        ],
    )
    write_csv(METRIC_DIR / "prefix_rule_map.csv", prefix_map_rows, ["target", "prefix_kind", "prefix", "train_majority_label"])

    cue_rows = []
    for target in TARGETS:
        cue_rows.extend(token_log_odds(train, target)[:80])
    write_csv(
        DIAG_DIR / "claim_token_log_odds_top80.csv",
        cue_rows,
        ["target", "token", "count_class0", "count_class1", "doc_count_class0", "doc_count_class1", "log_odds_toward_class1"],
    )

    prefix_dist = prefix_distribution(all_df)
    write_csv(DIAG_DIR / "claim_prefix_distribution.csv", prefix_dist, ["prefix_kind", "prefix", "n", "distribution_json", "dominant_label", "dominant_rate"])

    # Compact report
    best_prefix = defaultdict(list)
    for row in prefix_metric_rows:
        if row["eval_split"] == "test":
            best_prefix[row["target"]].append(row)
    report = [
        "# Leakage Diagnostic Report - Formal Baseline v1 150",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        "## Main finding",
        "",
        "Claim-only TF-IDF baselines reaching 1.0 strongly suggests template/cue leakage in the current AI-preannotated candidate text.",
        "This diagnostic checks whether short claim prefixes alone can predict labels.",
        "",
        "## Prefix-only test results",
        "",
        "| target | prefix kind | test accuracy | test macro-F1 |",
        "|---|---|---:|---:|",
    ]
    for target, rows in best_prefix.items():
        rows.sort(key=lambda r: (-float(r["macro_f1"]), r["prefix_kind"]))
        for row in rows:
            report.append(f"| {target} | {row['prefix_kind']} | {row['accuracy']} | {row['macro_f1']} |")
    report.extend(
        [
            "",
            "## Interpretation",
            "",
            "- If prefix-only scores are high, current labels are strongly recoverable from claim wording alone.",
            "- That is acceptable for pipeline debugging, but not acceptable as final evidence-comparison performance.",
            "- The next dataset version should de-template claim generation or evaluate on prefix-stripped / human-rewritten claims.",
            "",
            "## Output files",
            "",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\metrics\\prefix_leakage_rule_metrics.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\diagnostics\\claim_token_log_odds_top80.csv`",
            "- `D:\\ocn\\experiments\\formal_baseline_v1_150\\diagnostics\\claim_prefix_distribution.csv`",
        ]
    )
    (REPORT_DIR / "leakage_diagnostic_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "generated_at_utc": generated_at,
                "prefix_metric_rows": len(prefix_metric_rows),
                "cue_rows": len(cue_rows),
                "prefix_distribution_rows": len(prefix_dist),
                "report": str(REPORT_DIR / "leakage_diagnostic_report.md"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
