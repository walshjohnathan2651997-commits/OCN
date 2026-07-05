import csv
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd


ROOT = Path(r"D:\ocn")
DATA_ROOT = ROOT / "data" / "simclaim_mvp_expansion_v1_150"
EXP_ROOT = ROOT / "experiments" / "llm_baseline_v1_150"
INPUT_DIR = EXP_ROOT / "inputs"
PROMPT_DIR = EXP_ROOT / "prompts"
REPORT_DIR = EXP_ROOT / "reports"

TRAIN_PATH = DATA_ROOT / "splits" / "train.csv"
DEV_PATH = DATA_ROOT / "splits" / "dev.csv"
TEST_PATH = DATA_ROOT / "splits" / "test.csv"

TARGETS = {
    "escalation_binary_label_guess": {
        "name": "Escalation Detection",
        "label0": "0 = the claim is bounded/supported by the evidence",
        "label1": "1 = the claim overstates the evidence in scope, causality, actionability, or certainty",
    },
    "issue_binary_label_guess": {
        "name": "Issue Detection",
        "label0": "0 = supported / no issue",
        "label1": "1 = any problem exists, including overclaim or contradiction",
    },
}

SETTINGS = [
    "zero_shot_claim_evidence",
    "zero_shot_claim_only",
    "zero_shot_evidence_only",
    "zero_shot_prefix_stripped",
    "few_shot_claim_evidence",
    "few_shot_prefix_stripped",
]

PREFIX_PATTERNS = [
    r"^\s*the passage reports that\s+",
    r"^\s*a bounded reading of the evidence is that\s+",
    r"^\s*the study demonstrates that\s+",
    r"^\s*the claim moves from the reported setting to .*? interpretation:\s+",
    r"^\s*the claim suggests broader .*? establishes:\s+",
]


def strip_prefix(text):
    out = str(text)
    low = out.lower()
    for pat in PREFIX_PATTERNS:
        m = re.match(pat, low, flags=re.IGNORECASE)
        if m:
            out = out[m.end() :]
            break
    out = re.sub(r"\s*this result can be generalized to broader settings\.?\s*$", "", out, flags=re.IGNORECASE)
    return out.strip()


def read_split(path, split):
    df = pd.read_csv(path, dtype=str).fillna("")
    df["eval_split"] = split
    return df


def pick_few_shots(train_df, target):
    # Stable, compact, balanced examples. Avoid risky rows when possible.
    rows = []
    for label in ["0", "1"]:
        subset = train_df[train_df[target].astype(str) == label].copy()
        subset["risk"] = subset["quality_flags"].astype(str).str.contains(
            "needs_human_review|contradiction_uncertain|evidence_too_short|possible_metadata_leakage",
            case=False,
            regex=True,
        )
        subset = subset.sort_values(["risk", "candidate_id"])
        rows.extend(subset.head(2).to_dict("records"))
    return rows


def system_prompt(target):
    info = TARGETS[target]
    return (
        "You are evaluating whether a scientific paper claim is supported by a quoted evidence passage. "
        "Return only valid JSON with keys: label, confidence, rationale. "
        "label must be 0 or 1. confidence must be a number from 0 to 1. "
        "Do not use prior knowledge; use only the provided claim and evidence."
        f"\nTask: {info['name']}.\n{info['label0']}.\n{info['label1']}."
    )


def example_block(examples, target, prefix_stripped=False):
    if not examples:
        return ""
    lines = ["Examples:"]
    for i, ex in enumerate(examples, 1):
        claim = strip_prefix(ex["claim_text"]) if prefix_stripped else ex["claim_text"]
        lines.append(
            f"Example {i}\n"
            f"Claim: {claim}\n"
            f"Evidence: {ex['evidence_text']}\n"
            f"Answer: {{\"label\": {int(ex[target])}, \"confidence\": 0.90, \"rationale\": \"training example\"}}"
        )
    return "\n\n".join(lines)


def user_prompt(row, target, setting, few_shots):
    prefix_stripped = "prefix_stripped" in setting
    claim = strip_prefix(row["claim_text"]) if prefix_stripped else row["claim_text"]
    evidence = row["evidence_text"]
    blocks = []
    if setting.startswith("few_shot"):
        blocks.append(example_block(few_shots, target, prefix_stripped=prefix_stripped))
    if setting == "zero_shot_claim_only":
        blocks.append(
            "Classify using only the claim text. This is a leakage-control diagnostic.\n"
            f"Claim: {claim}"
        )
    elif setting == "zero_shot_evidence_only":
        blocks.append(
            "Classify using only the evidence text. This is a leakage-control diagnostic.\n"
            f"Evidence: {evidence}"
        )
    else:
        blocks.append(
            "Classify the candidate.\n"
            f"Claim: {claim}\n"
            f"Evidence: {evidence}"
        )
    blocks.append(
        "Return exactly one JSON object like: "
        "{\"label\": 0, \"confidence\": 0.73, \"rationale\": \"brief reason\"}"
    )
    return "\n\n".join([b for b in blocks if b])


def estimate_tokens(text):
    return max(1, round(len(str(text)) / 4))


def write_jsonl(path, rows):
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")


def write_csv(path, rows, fields):
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main():
    INPUT_DIR.mkdir(parents=True, exist_ok=True)
    PROMPT_DIR.mkdir(parents=True, exist_ok=True)
    REPORT_DIR.mkdir(parents=True, exist_ok=True)
    generated_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    train = read_split(TRAIN_PATH, "train")
    dev = read_split(DEV_PATH, "dev")
    test = read_split(TEST_PATH, "test")
    eval_sets = [("dev", dev), ("test", test)]

    all_requests = []
    manifest_rows = []
    few_shot_by_target = {target: pick_few_shots(train, target) for target in TARGETS}

    for target in TARGETS:
        (PROMPT_DIR / f"system_{target}.txt").write_text(system_prompt(target), encoding="utf-8")
        few_shot_path = PROMPT_DIR / f"few_shot_examples_{target}.json"
        few_shot_path.write_text(json.dumps(few_shot_by_target[target], ensure_ascii=False, indent=2), encoding="utf-8")
        for setting in SETTINGS:
            setting_rows = []
            for split_name, df in eval_sets:
                for _, row in df.iterrows():
                    request_id = f"{target}__{setting}__{split_name}__{row['candidate_id']}"
                    sys_p = system_prompt(target)
                    usr_p = user_prompt(row, target, setting, few_shot_by_target[target])
                    item = {
                        "request_id": request_id,
                        "target": target,
                        "setting": setting,
                        "eval_split": split_name,
                        "candidate_id": row["candidate_id"],
                        "source_pair_id": row.get("source_pair_id", ""),
                        "split_group_id": row.get("split_group_id", ""),
                        "domain": row.get("domain", ""),
                        "candidate_label_guess": row.get("candidate_label_guess", ""),
                        "gold_proxy_label": int(row[target]),
                        "system_prompt": sys_p,
                        "user_prompt": usr_p,
                        "estimated_prompt_tokens": estimate_tokens(sys_p) + estimate_tokens(usr_p),
                        "claim_text": row["claim_text"],
                        "claim_text_prefix_stripped": strip_prefix(row["claim_text"]),
                        "evidence_text": row["evidence_text"],
                    }
                    setting_rows.append(item)
                    all_requests.append(item)
            out = INPUT_DIR / f"requests_{target}_{setting}.jsonl"
            write_jsonl(out, setting_rows)
            manifest_rows.append(
                {
                    "target": target,
                    "setting": setting,
                    "request_file": str(out),
                    "n_requests": len(setting_rows),
                    "estimated_prompt_tokens": sum(r["estimated_prompt_tokens"] for r in setting_rows),
                }
            )

    all_path = INPUT_DIR / "requests_all.jsonl"
    write_jsonl(all_path, all_requests)
    write_csv(
        INPUT_DIR / "request_manifest.csv",
        manifest_rows,
        ["target", "setting", "request_file", "n_requests", "estimated_prompt_tokens"],
    )

    preflight = {
        "generated_at_utc": generated_at,
        "train_rows": len(train),
        "dev_rows": len(dev),
        "test_rows": len(test),
        "targets": list(TARGETS.keys()),
        "settings": SETTINGS,
        "total_requests": len(all_requests),
        "estimated_prompt_tokens_total": sum(r["estimated_prompt_tokens"] for r in all_requests),
        "all_requests_file": str(all_path),
        "label_warning": "Labels are AI-preannotated proxy labels, not gold.",
    }
    (REPORT_DIR / "input_preparation_summary.json").write_text(json.dumps(preflight, ensure_ascii=False, indent=2), encoding="utf-8")

    report = [
        "# LLM Baseline v1 150 - Input Preparation",
        "",
        f"Generated at UTC: {generated_at}",
        "",
        f"- Total requests: {len(all_requests)}",
        f"- Estimated prompt tokens: {preflight['estimated_prompt_tokens_total']}",
        "- Targets: escalation_binary_label_guess, issue_binary_label_guess",
        "- Settings: zero-shot/few-shot, claim-only/evidence-only/claim+evidence/prefix-stripped",
        "",
        "This package is ready for a real LLM provider. Labels are proxy AI-preannotations, not gold.",
    ]
    (REPORT_DIR / "input_preparation_report.md").write_text("\n".join(report) + "\n", encoding="utf-8")

    print(json.dumps(preflight, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
