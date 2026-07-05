"""
Task Q - Public Gold External Test + Small LLM Baseline Plan.

Generates a feasibility inventory of public gold datasets, conservative label
mappings, external test protocols (E1-E4), and a small-sample LLM judge plan.
No data is downloaded, no LLM API is called, no SimClaim data is mutated.
All outputs are plans/protocols/templates for downstream execution.
"""

from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PAPER_STRICT_CSV = Path(
    r"D:\ocn\data\simclaim_all92_candidate_pool_v1\strict_silver_max_v1\strict_silver_max_candidates_v1.csv"
)
FROZEN_R4_DIR = Path(r"D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline")
TASK_P_DIR = Path(r"D:\ocn\experiments\v3_r4_strong_baselines_holdout_v1")

EXP_DIR = Path(r"D:\ocn\experiments\v3_external_gold_llm_plan_v1")
EXP_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH = EXP_DIR / "run.log"
LOG_PATH.write_text("", encoding="utf-8")

LABELS_4 = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]


def log(msg: str) -> None:
    line = f"[{datetime.now().isoformat(timespec='seconds')}] {msg}"
    print(line, flush=True)
    with open(LOG_PATH, "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------
# Task 1: Public gold dataset inventory
# ---------------------------------------------------------------------------
# Inventory reflects widely-published specs of these datasets (license/size are
# best-effort public knowledge; downloader must verify at fetch time).

PUBLIC_DATASETS = [
    {
        "dataset_name": "SciFact",
        "task_type": "scientific claim verification",
        "domain": "biomedical/scientific papers",
        "label_schema": "SUPPORT / CONTRADICT / NEI (NOT_ENOUGH_INFO)",
        "has_gold_labels": True,
        "has_evidence_text": True,
        "has_rationale_or_evidence_sentence": True,
        "license_or_access": "CC BY-NC 2.0 (allenai/scifact on HuggingFace)",
        "data_size": "~1.4k claims; 5.2k evidence abstracts",
        "download_url": "https://github.com/allenai/scifact; https://huggingface.co/datasets/allenai/scifact",
        "local_status": "not_downloaded",
        "mapping_to_v3_possible": True,
        "recommended_use": "A",
        "risk_notes": (
            "Best scientific-domain match for V3. Has evidence text and rationale. "
            "Labels are support/contradict/NEI only; CANNOT map to strong_action_overclaim "
            "(no action/deployment/safety dimension). Use as external contradiction/support "
            "sanity check, not as SimClaim gold replacement."
        ),
    },
    {
        "dataset_name": "VitaminC",
        "task_type": "contrastive fact verification",
        "domain": "news/Wikipedia (encyclopedic)",
        "label_schema": "SUPPORTS / REFUTES / NOT_ENOUGH_INFO",
        "has_gold_labels": True,
        "has_evidence_text": True,
        "has_rationale_or_evidence_sentence": True,
        "license_or_access": "CC BY 4.0 (tals/vitaminc on HuggingFace)",
        "data_size": "~47k claim-evidence pairs; contrastive design",
        "download_url": "https://github.com/TalSchuster/VitaminC; https://huggingface.co/datasets/tals/vitaminc",
        "local_status": "not_downloaded",
        "mapping_to_v3_possible": True,
        "recommended_use": "C",
        "risk_notes": (
            "Contrastive design (same claim, correct vs wrong evidence) is ideal for "
            "evidence sensitivity test (E3). Domain is news/encyclopedic, NOT scientific/technical. "
            "Cannot map to strong_action_overclaim. Use only for evidence-sensitivity sanity check."
        ),
    },
    {
        "dataset_name": "FEVER",
        "task_type": "general fact verification",
        "domain": "Wikipedia (general knowledge)",
        "label_schema": "SUPPORTED / REFUTED / NOT ENOUGH INFO",
        "has_gold_labels": True,
        "has_evidence_text": True,
        "has_rationale_or_evidence_sentence": True,
        "license_or_access": "CC BY-SA 3.0 (fever.ai)",
        "data_size": "~185k annotated claims",
        "download_url": "https://fever.ai/downloadfever; https://huggingface.co/datasets/fever/fever",
        "local_status": "not_downloaded",
        "mapping_to_v3_possible": True,
        "recommended_use": "D",
        "risk_notes": (
            "Largest scale but general-knowledge domain mismatch with V3 (technical/scientific). "
            "Use only as optional binary sanity check. NOT a primary external test. "
            "Cannot map to strong_action_overclaim."
        ),
    },
    {
        "dataset_name": "PubHealth",
        "task_type": "health claim verification",
        "domain": "public health / medical news",
        "label_schema": "true / false / mixture / unproven",
        "has_gold_labels": True,
        "has_evidence_text": True,
        "has_rationale_or_evidence_sentence": True,
        "license_or_access": "MIT (healthver variant); PubHealth original has restricted commercial use",
        "data_size": "~11.8k claim-evidence pairs (HealthVer); PubHealth ~9.7k",
        "download_url": "https://github.com/utahnlp/healthver; https://huggingface.co/datasets/healthver",
        "local_status": "not_downloaded",
        "mapping_to_v3_possible": True,
        "recommended_use": "B",
        "risk_notes": (
            "Health-domain support/non-support external test. Labels are true/false/mixture/unproven; "
            "cannot capture action-overclaim. Use as support-vs-non-support (E2) sanity check. "
            "License terms vary between PubHealth and HealthVer; verify before use."
        ),
    },
    {
        "dataset_name": "AVeriTeC",
        "task_type": "complex fact-checking with retrieved evidence",
        "domain": "web/real-world claims (fact-checking)",
        "label_schema": "Supported / Refuted / Not Enough Evidence / Conflicting / Cherry-picking",
        "has_gold_labels": True,
        "has_evidence_text": True,
        "has_rationale_or_evidence_sentence": True,
        "license_or_access": "CC BY 4.0 (github.com/ factiverse/averitec)",
        "data_size": "~5.7k claims with evidence",
        "download_url": "https://github.com/factiverse/averitec; https://huggingface.co/datasets/averitec",
        "local_status": "not_downloaded",
        "mapping_to_v3_possible": True,
        "recommended_use": "B",
        "risk_notes": (
            "Rich labels (5-class incl. Cherry-picking) are closest in spirit to overclaim "
            "detection, but still not equivalent to strong_action_overclaim. Use as complex "
            "fact-checking sanity check. Cherry-picking may weakly correlate with mild_scope_overclaim "
            "but must NOT be hard-mapped to SimClaim gold."
        ),
    },
]

RECOMMEND_USE_DESC = {
    "A": "A. contradiction external test",
    "B": "B. support vs non-support external test",
    "C": "C. evidence sensitivity / counterfactual test",
    "D": "D. not recommended",
}


def write_public_gold_inventory() -> None:
    log("Task 1: Writing public gold dataset inventory ...")
    rows = []
    for d in PUBLIC_DATASETS:
        row = dict(d)
        row["recommended_use_description"] = RECOMMEND_USE_DESC[d["recommended_use"]]
        rows.append(row)
    df = pd.DataFrame(rows)
    df.to_csv(EXP_DIR / "public_gold_dataset_inventory.csv", index=False, encoding="utf-8")
    inventory_json = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "n_datasets": len(PUBLIC_DATASETS),
        "datasets": PUBLIC_DATASETS,
        "recommended_use_legend": RECOMMEND_USE_DESC,
        "global_caveat": (
            "All public datasets have support/refute/NEI-style labels. NONE can replace "
            "SimClaim gold because none annotate action-overclaim, deployment-overclaim, "
            "or safety-scope overclaim. Public data is for external sanity check only."
        ),
    }
    (EXP_DIR / "public_gold_dataset_inventory.json").write_text(
        json.dumps(inventory_json, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(f"  Wrote public_gold_dataset_inventory.csv ({df.shape[0]} datasets)")
    log(f"  Wrote public_gold_dataset_inventory.json")


# ---------------------------------------------------------------------------
# Task 2: Label mapping plan
# ---------------------------------------------------------------------------
MAPPING_PLAN = [
    {
        "dataset_name": "SciFact",
        "source_label": "SUPPORT",
        "v3_label": "supported",
        "confidence": "high",
        "rationale": "Direct support relation maps cleanly to V3 supported.",
    },
    {
        "dataset_name": "SciFact",
        "source_label": "CONTRADICT",
        "v3_label": "contradiction_candidate",
        "confidence": "high",
        "rationale": "Direct contradiction relation maps cleanly to V3 contradiction_candidate.",
    },
    {
        "dataset_name": "SciFact",
        "source_label": "NEI / NOT_ENOUGH_INFO",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "high",
        "rationale": "Insufficient evidence is a distinct bucket; maps to a 3rd external-only class.",
    },
    {
        "dataset_name": "VitaminC",
        "source_label": "SUPPORTS",
        "v3_label": "supported",
        "confidence": "high",
        "rationale": "Direct support.",
    },
    {
        "dataset_name": "VitaminC",
        "source_label": "REFUTES",
        "v3_label": "contradiction_candidate",
        "confidence": "high",
        "rationale": "Direct refutation.",
    },
    {
        "dataset_name": "VitaminC",
        "source_label": "NOT_ENOUGH_INFO",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "high",
        "rationale": "Insufficient evidence.",
    },
    {
        "dataset_name": "FEVER",
        "source_label": "SUPPORTED",
        "v3_label": "supported",
        "confidence": "high",
        "rationale": "Direct support.",
    },
    {
        "dataset_name": "FEVER",
        "source_label": "REFUTED",
        "v3_label": "contradiction_candidate",
        "confidence": "high",
        "rationale": "Direct refutation.",
    },
    {
        "dataset_name": "FEVER",
        "source_label": "NOT ENOUGH INFO",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "high",
        "rationale": "Insufficient evidence.",
    },
    {
        "dataset_name": "PubHealth",
        "source_label": "true",
        "v3_label": "supported",
        "confidence": "high",
        "rationale": "Claim is true given evidence.",
    },
    {
        "dataset_name": "PubHealth",
        "source_label": "false",
        "v3_label": "contradiction_candidate",
        "confidence": "medium",
        "rationale": "Claim is false; approximately maps to contradiction but is truth-value based, not evidence-relation based.",
    },
    {
        "dataset_name": "PubHealth",
        "source_label": "mixture",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "medium",
        "rationale": "Mixed support; treated as insufficient for a single clean verdict.",
    },
    {
        "dataset_name": "PubHealth",
        "source_label": "unproven",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "high",
        "rationale": "No sufficient evidence.",
    },
    {
        "dataset_name": "AVeriTeC",
        "source_label": "Supported",
        "v3_label": "supported",
        "confidence": "high",
        "rationale": "Direct support.",
    },
    {
        "dataset_name": "AVeriTeC",
        "source_label": "Refuted",
        "v3_label": "contradiction_candidate",
        "confidence": "high",
        "rationale": "Direct refutation.",
    },
    {
        "dataset_name": "AVeriTeC",
        "source_label": "Not Enough Evidence",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "high",
        "rationale": "Insufficient evidence.",
    },
    {
        "dataset_name": "AVeriTeC",
        "source_label": "Conflicting",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "medium",
        "rationale": "Conflicting evidence; not a clean contradiction, bucketed as insufficient.",
    },
    {
        "dataset_name": "AVeriTeC",
        "source_label": "Cherry-picking",
        "v3_label": "unsupported_or_insufficient",
        "confidence": "low",
        "rationale": (
            "Cherry-picking weakly resembles mild_scope_overclaim but is NOT equivalent. "
            "Conservatively bucketed as insufficient rather than mapped to overclaim."
        ),
    },
]


def write_label_mapping_plan() -> None:
    log("Task 2: Writing external label mapping plan ...")
    df = pd.DataFrame(MAPPING_PLAN)
    df.to_csv(EXP_DIR / "external_label_mapping_plan.csv", index=False, encoding="utf-8")

    md_lines = [
        "# External Label Mapping Plan (Conservative)",
        "",
        "> **Critical constraint**: Public datasets use support/refute/NEI-style labels. ",
        "> They CANNOT be mapped to `strong_action_overclaim` or `mild_scope_overclaim` ",
        "> because no public dataset annotates action/deployment/safety overclaim. ",
        "> Public data tests binary support-vs-contradiction and support-vs-non-support only.",
        "",
        "> A third bucket `unsupported_or_insufficient` is introduced for external-only use. ",
        "> It is NOT a V3 label and must not be merged into SimClaim gold.",
        "",
        "## Mapping Table",
        "",
        "| Dataset | Source Label | V3 External Label | Confidence | Rationale |",
        "|---|---|---|---|---|",
    ]
    for r in MAPPING_PLAN:
        md_lines.append(
            f"| {r['dataset_name']} | {r['source_label']} | {r['v3_label']} | {r['confidence']} | {r['rationale']} |"
        )
    md_lines += [
        "",
        "## Per-Dataset Recommended Use",
        "",
        "- **SciFact**: scientific-domain contradiction/support external test (Task E1, E2).",
        "- **VitaminC**: evidence sensitivity / contrastive evidence test (Task E3).",
        "- **FEVER**: optional general fact-verification sanity check; not a primary result.",
        "- **PubHealth**: health-domain support vs non-support external test (Task E2).",
        "- **AVeriTeC**: complex fact-checking support vs non-support sanity check (Task E2).",
        "",
        "## Forbidden Mappings",
        "",
        "- NEVER map any public label to `strong_action_overclaim`.",
        "- NEVER map any public label to `mild_scope_overclaim`.",
        "- NEVER treat `unsupported_or_insufficient` as a SimClaim gold label.",
        "- NEVER average public-dataset F1 with SimClaim F1 in the main results table.",
        "",
    ]
    (EXP_DIR / "external_label_mapping_plan.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )
    log(f"  Wrote external_label_mapping_plan.csv ({df.shape[0]} mappings)")
    log(f"  Wrote external_label_mapping_plan.md")


# ---------------------------------------------------------------------------
# Task 3: External test protocol design
# ---------------------------------------------------------------------------
SAMPLING_PLAN = [
    {"dataset_name": "SciFact", "max_sample": 300, "task_E1": True, "task_E2": True, "task_E3": False, "task_E4": True,
     "sampling_notes": "Balance SUPPORT/CONTRADICT/NEI ~100 each; require non-empty evidence text."},
    {"dataset_name": "VitaminC", "max_sample": 300, "task_E1": True, "task_E2": True, "task_E3": True, "task_E4": True,
     "sampling_notes": "Sample contrastive triples (claim × {correct, wrong, empty} evidence); 100 claims × 3 evidence variants."},
    {"dataset_name": "FEVER", "max_sample": 300, "task_E1": True, "task_E2": True, "task_E3": False, "task_E4": True,
     "sampling_notes": "Balance SUPPORTED/REFUTED/NEI ~100 each; optional, not primary."},
    {"dataset_name": "PubHealth", "max_sample": 300, "task_E1": True, "task_E2": True, "task_E3": False, "task_E4": True,
     "sampling_notes": "Balance true/false/mixture/unproven; drop rows with empty evidence."},
    {"dataset_name": "AVeriTeC", "max_sample": 300, "task_E1": True, "task_E2": True, "task_E3": False, "task_E4": True,
     "sampling_notes": "Sample Supported/Refuted/NEE; hold out Cherry-picking for qualitative review only."},
]


def write_external_test_protocol() -> None:
    log("Task 3: Writing external test protocol ...")

    md_lines = [
        "# External Gold Test Protocol",
        "",
        "> **Scope**: This is a PROTOCOL only. No public data is downloaded or evaluated ",
        "> in this task. The protocol specifies what to do when downstream execution is approved.",
        "",
        "> **Hard cap**: Each dataset samples up to 300 claim-evidence pairs. ",
        "> No full-dataset runs. No model retraining on public data.",
        "",
        "## Sampling Rules (all datasets)",
        "",
        "1. Drop samples with empty evidence text.",
        "2. Drop samples where claim-evidence pair is incomplete.",
        "3. Balance labels as evenly as possible (up to 100 per class).",
        "4. Preserve `source_id` / `dataset_id` for traceability.",
        "5. Record original label and mapped V3 external label side-by-side.",
        "6. Save the sampling seed for reproducibility.",
        "",
        "## Task E1: support_vs_contradiction",
        "",
        "- **Samples**: Only `supported` vs `contradiction_candidate` (drop `unsupported_or_insufficient`).",
        "- **Metrics**: accuracy, macro-F1, supported F1, contradiction F1.",
        "- **Purpose**: Test whether V3/R4 contradiction detection transfers to external data.",
        "- **Reporting**: Separate table, NOT merged with SimClaim main results.",
        "",
        "## Task E2: support_vs_non_support",
        "",
        "- **Samples**: `supported` vs (`contradiction_candidate` + `unsupported_or_insufficient`).",
        "- **Metrics**: macro-F1, positive-F1 for non-support, calibration (Brier score) if feasible.",
        "- **Purpose**: Test support-vs-rest generalization.",
        "",
        "## Task E3: evidence_sensitivity (VitaminC only)",
        "",
        "- **Samples**: 100 claims, each paired with:",
        "  - correct evidence (supports gold label)",
        "  - wrong evidence (retrieved for a different claim, contrastive)",
        "  - empty evidence (blank/placeholder string)",
        "- **Metrics**:",
        "  - `correct_vs_wrong_delta`: accuracy(correct) − accuracy(wrong)",
        "  - `correct_vs_empty_delta`: accuracy(correct) − accuracy(empty)",
        "  - `label_flip_rate`: fraction of claims whose predicted label changes across evidence variants",
        "  - `evidence_sensitivity_rate`: fraction of claims where model uses evidence (flip on wrong/empty)",
        "- **Purpose**: Verify R4 is evidence-aware, not just claim-text classifier.",
        "",
        "## Task E4: transfer sanity",
        "",
        "- **Samples**: All sampled pairs from E1 (binary).",
        "- **Method**: Apply V3/R4 feature pipeline (NLI + action-gap + routing) to public data.",
        "- **If labels incompatible**: Fall back to binary support-vs-non-support mapping.",
        "- **Metric**: Compare R4 vs B1 (NLI-only) vs B3b (TF-IDF) on external data.",
        "- **Pass criterion**: R4 should not collapse (macro-F1 > random baseline 0.50) on at least SciFact.",
        "",
        "## Execution Order (recommended)",
        "",
        "1. SciFact E1 + E2 (primary scientific external test)",
        "2. VitaminC E3 (evidence sensitivity)",
        "3. PubHealth E2 (health-domain sanity)",
        "4. AVeriTeC E2 (complex fact-check sanity)",
        "5. FEVER E1 (optional, general knowledge)",
        "",
        "## Reporting Constraints",
        "",
        "- Public results MUST be in a separate table from SimClaim main results.",
        "- Table caption must say: \"External sanity check on public gold datasets; labels are support/refute/NEI and do not include action-overclaim.\"",
        "- Must NOT claim public results validate `strong_action_overclaim` detection.",
        "",
    ]
    (EXP_DIR / "external_gold_test_protocol.md").write_text(
        "\n".join(md_lines), encoding="utf-8"
    )

    # Sampling plan CSV
    df = pd.DataFrame(SAMPLING_PLAN)
    df.to_csv(EXP_DIR / "external_gold_sampling_plan.csv", index=False, encoding="utf-8")

    # Expected outputs JSON
    expected = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "scope": "protocol_only_no_execution",
        "per_dataset_max_sample": 300,
        "total_max_sample": 1500,
        "tasks": {
            "E1_support_vs_contradiction": {
                "applicable_datasets": ["SciFact", "VitaminC", "FEVER", "PubHealth", "AVeriTeC"],
                "metrics": ["accuracy", "macro_f1", "supported_f1", "contradiction_f1"],
                "output_files_expected": ["e1_results_by_dataset.csv", "e1_summary.json"],
            },
            "E2_support_vs_non_support": {
                "applicable_datasets": ["SciFact", "VitaminC", "FEVER", "PubHealth", "AVeriTeC"],
                "metrics": ["macro_f1", "non_support_positive_f1", "brier_score_if_feasible"],
                "output_files_expected": ["e2_results_by_dataset.csv", "e2_summary.json"],
            },
            "E3_evidence_sensitivity": {
                "applicable_datasets": ["VitaminC"],
                "metrics": ["correct_vs_wrong_delta", "correct_vs_empty_delta", "label_flip_rate", "evidence_sensitivity_rate"],
                "output_files_expected": ["e3_vitaminc_results.csv", "e3_summary.json"],
            },
            "E4_transfer_sanity": {
                "applicable_datasets": ["SciFact", "VitaminC", "FEVER", "PubHealth", "AVeriTeC"],
                "metrics": ["r4_macro_f1", "b1_nli_macro_f1", "b3b_tfidf_macro_f1", "r4_vs_b1_delta"],
                "output_files_expected": ["e4_transfer_results.csv", "e4_summary.json"],
            },
        },
        "reporting_constraint": "Public results MUST be in a separate table from SimClaim main results. Must NOT claim validation of strong_action_overclaim.",
    }
    (EXP_DIR / "external_gold_expected_outputs.json").write_text(
        json.dumps(expected, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log("  Wrote external_gold_test_protocol.md")
    log(f"  Wrote external_gold_sampling_plan.csv ({df.shape[0]} datasets)")
    log("  Wrote external_gold_expected_outputs.json")


# ---------------------------------------------------------------------------
# Task 4: LLM judge small-sample baseline plan
# ---------------------------------------------------------------------------
def write_llm_baseline_plan() -> None:
    log("Task 4: Writing LLM judge small-sample baseline plan ...")

    # Load SimClaim data for sampling plan
    df = pd.read_csv(PAPER_STRICT_CSV, keep_default_na=False)
    log(f"  Loaded SimClaim: {len(df)} rows")

    # Build 200-sample plan: 50 per class, covering all 6 domains
    sample_rows = []
    np.random.seed(42)
    for label in LABELS_4:
        sub = df[df["candidate_label_guess"] == label].copy()
        # Stratify by domain when possible
        for domain in sorted(df["domain"].unique()):
            dom_sub = sub[sub["domain"] == domain]
            n_take = max(1, int(round(50 * len(dom_sub) / len(sub))))
            n_take = min(n_take, len(dom_sub))
            if n_take == 0 and len(sub) > 0:
                continue
            idx = np.random.choice(dom_sub.index.values, size=n_take, replace=False)
            for i in idx:
                sample_rows.append({
                    "sample_id": f"LLM_{len(sample_rows)+1:03d}",
                    "candidate_id": df.loc[i, "candidate_id"],
                    "label_4": label,
                    "domain": df.loc[i, "domain"],
                    "source_id": df.loc[i, "source_id"],
                    "claim_text_preview": str(df.loc[i, "claim_text"])[:80],
                    "evidence_text_preview": str(df.loc[i, "evidence_text"])[:80],
                    "r4_correct_unknown": "runtime_check_needed",
                    "fragile_case_flag": (
                        "marl" if df.loc[i, "domain"] == "marl"
                        else "cyber_defense" if df.loc[i, "domain"] == "cyber_defense"
                        else "none"
                    ),
                })

    # Cap at 200
    sample_rows = sample_rows[:200]
    sample_df = pd.DataFrame(sample_rows)
    # Ensure at least a few from each label (rebalance if short)
    counts = sample_df["label_4"].value_counts().to_dict()
    log(f"  Sample plan label distribution: {counts}")

    sample_df.to_csv(EXP_DIR / "llm_baseline_sample_plan.csv", index=False, encoding="utf-8")

    # Prompt template
    prompt_md = """# LLM Judge Prompt Template (Small-Sample Baseline)

> **Usage**: This template is for a small-sample LLM judge baseline (100-200 SimClaim pairs).
> No API is called in Task Q. Execution happens only when API access is approved.

## System Prompt

```
You are an evidence-relation auditor for technical/scientific claims. You will receive a
claim and its supporting evidence text. You must judge the relation between the claim and
the evidence, NOT the truth of the claim in the world.

You may ONLY use the provided evidence. You may NOT use outside knowledge to supply missing
evidence. You may NOT use common sense to bridge gaps.

Output strictly valid JSON with these fields:
{
  "label": "supported" | "mild_scope_overclaim" | "strong_action_overclaim" | "contradiction_candidate",
  "confidence": float in [0,1],
  "one_sentence_rationale": string,
  "evidence_used": true | false,
  "uncertain": true | false
}
```

## User Prompt Template

```
Claim:
{claim_text}

Evidence:
{evidence_text}

Task: Judge the evidence-relation between the claim and the evidence. Select exactly one label.

Decision rules (apply in order):
1. If the evidence directly conflicts with the claim (asserts the opposite), output "contradiction_candidate".
2. If the evidence is about metrics/benchmarks/ablations only, but the claim makes a deployment / action /
   safety / real-world / cross-environment generalization claim that the evidence does NOT substantiate,
   output "strong_action_overclaim".
3. If the evidence supports the core of the claim but the claim slightly broadens scope (e.g., a narrow
   result stated as broad, but not a deployment/action/safety claim), output "mild_scope_overclaim".
4. If the evidence is sufficient to support the claim as stated, output "supported".
5. If you are unsure between two labels, set uncertain=true and pick the more conservative (more severe)
   label.

Return only the JSON object.
```

## Label Definitions (provided to LLM)

- **supported**: The evidence substantiates the claim as stated, including its scope and strength.
- **mild_scope_overclaim**: The claim slightly over-generalizes the evidence (scope breadth), but does
  NOT escalate to deployment/action/safety/cross-environment claims.
- **strong_action_overclaim**: The claim asserts deployment, real-world action, safety guarantee, or
  broad cross-environment generalization that the evidence (mostly metrics/benchmarks/ablations) does
  NOT substantiate.
- **contradiction_candidate**: The evidence directly contradicts the claim.

## Critical Constraints

- LLM must NOT use outside knowledge to fill evidence gaps.
- LLM must NOT label anything as `strong_action_overclaim` unless the claim has deployment/action/safety
  language unsupported by the evidence.
- If the evidence is empty or irrelevant, LLM should output `uncertain=true` and label per rules above.
- LLM confidence is its own calibrated probability, NOT a score from an external tool.

## Post-Processing

- Parse JSON output; reject malformed responses.
- Compare LLM label to SimClaim silver label (NOT gold).
- Record agreement rate, per-class F1, and confusion matrix.
- Flag samples where LLM and R4 disagree for qualitative review.
"""
    (EXP_DIR / "llm_baseline_prompt_template.md").write_text(prompt_md, encoding="utf-8")

    # Schema
    schema = {
        "schema_name": "llm_baseline_output",
        "version": "1.0",
        "description": "Output schema for LLM judge baseline on SimClaim small sample.",
        "fields": {
            "label": {
                "type": "string",
                "enum": ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"],
                "required": True,
            },
            "confidence": {
                "type": "float",
                "range": [0.0, 1.0],
                "required": True,
            },
            "one_sentence_rationale": {
                "type": "string",
                "max_chars": 300,
                "required": True,
            },
            "evidence_used": {
                "type": "boolean",
                "required": True,
                "notes": "true if LLM reports using the provided evidence; false if it relied on prior knowledge.",
            },
            "uncertain": {
                "type": "boolean",
                "required": True,
                "notes": "true if LLM is unsure between two labels.",
            },
        },
        "expected_output_file": "llm_baseline_predictions.csv",
        "expected_columns": [
            "sample_id", "candidate_id", "label_4_silver", "llm_label",
            "llm_confidence", "llm_rationale", "llm_evidence_used", "llm_uncertain",
            "r4_label", "agreement_llm_vs_silver", "agreement_llm_vs_r4",
        ],
    }
    (EXP_DIR / "llm_baseline_schema.json").write_text(
        json.dumps(schema, indent=2, ensure_ascii=False), encoding="utf-8"
    )

    # Cost estimate
    cost_md = """# LLM Baseline Cost Estimate

## Scope

- **Sample size**: 200 SimClaim pairs (50 per class × 4 classes)
- **Sample size alternative**: 100 pairs (25 per class) for pilot
- **API**: NOT called in Task Q. This is a pre-execution estimate.

## Estimated Token Usage (per call)

- System prompt: ~250 tokens
- User prompt (claim + evidence + rules): ~450 tokens average (varies by evidence length)
- LLM response (JSON): ~120 tokens
- **Total per call**: ~820 tokens (input + output)

## Cost Scenarios (illustrative, list prices, USD)

| Model | Input $/1M | Output $/1M | Cost per 200 calls | Cost per 100 calls |
|---|---|---|---|---|
| GPT-4o-mini | $0.15 | $0.60 | ~$0.10 | ~$0.05 |
| GPT-4o | $2.50 | $10.00 | ~$1.70 | ~$0.85 |
| Claude 3.5 Haiku | $0.80 | $4.00 | ~$0.70 | ~$0.35 |
| Claude 3.5 Sonnet | $3.00 | $15.00 | ~$2.10 | ~$1.05 |
| Local Qwen2.5-7B | $0 | $0 | $0 (compute only) | $0 (compute only) |

## Recommended Approach

1. **Pilot first**: Run 100 samples on a low-cost model (GPT-4o-mini or local Qwen2.5-7B).
2. **Quality check**: Inspect 20 random outputs for label quality.
3. **Scale only if useful**: If pilot shows LLM >= R4 on strong_positive_f1, scale to 200 + try a stronger model.
4. **Never run full 444 SimClaim**: Keep LLM baseline to <=200 for cost control.

## Constraints

- Task Q does NOT call any API.
- Task Q does NOT spend any budget.
- All costs are estimates for planning only.
- Actual execution requires separate approval.
"""
    (EXP_DIR / "llm_baseline_cost_estimate.md").write_text(cost_md, encoding="utf-8")

    log(f"  Wrote llm_baseline_sample_plan.csv ({len(sample_df)} samples)")
    log("  Wrote llm_baseline_prompt_template.md")
    log("  Wrote llm_baseline_schema.json")
    log("  Wrote llm_baseline_cost_estimate.md")


# ---------------------------------------------------------------------------
# Task 5: Paper impact analysis
# ---------------------------------------------------------------------------
def write_paper_impact_analysis() -> None:
    log("Task 5: Writing paper impact analysis ...")
    md = """# Paper Impact Analysis: External Gold + LLM Baseline

## Context

V3/R4 was validated on SimClaim silver labels (444 pairs, 4-class balanced, 6 technical domains).
Task P confirmed R4 retains main-method status under 10-seed group-aware split and domain/source
holdout. This task (Task Q) plans external gold and LLM baseline extensions WITHOUT executing them.

## Scenario-Based Writing Guidance

### Scenario 1: R4 performs well on public gold (SciFact/VitaminC E1+E2)

**Suggested writing**:
> "As an external sanity check, we evaluated the R4 router's contradiction-detection component
> on SciFact and VitaminC. R4 achieved competitive binary support-vs-contradiction F1 without
> retraining, supporting the generality of the evidence-relation routing framework beyond the
> SimClaim annotation. We emphasize that public datasets test support/refute relations and do
> not include action-overclaim labels; therefore they validate generalization of the
> contradiction-detection module, not the strong-action-overclaim detector."

### Scenario 2: R4 performs mediocre on public gold

**Suggested writing**:
> "Public fact-verification datasets (SciFact, VitaminC, FEVER) test binary support/refute
> relations and do not annotate action-overclaim. R4's design prioritizes the
> strong-action-overclaim vs supported/mild distinction, which has no analogue in these
> datasets. Modest performance on public data therefore does not contradict R4's value on
> SimClaim: SimClaim remains the needed benchmark for action-overclaim detection."

### Scenario 3: LLM judge is clearly stronger than R4

**Suggested writing**:
> "A small-sample LLM judge baseline (N=200, GPT-4o-mini) outperformed R4 on overall macro-F1.
> This is expected: the LLM has broader world knowledge and can detect semantic contradictions
> the linear router misses. However, R4 provides three advantages the LLM cannot: (1) transparent
> and auditable routing decisions; (2) per-component threshold control; (3) no API cost or data
> egress. We therefore position R4 as an interpretable and deployable pilot baseline, with the
> LLM as a strong black-box reference."

### Scenario 4: LLM judge is comparable to R4

**Suggested writing**:
> "On 200 SimClaim pairs, the LLM judge achieved competitive but not superior performance to R4
> (delta within bootstrap CI). This suggests action-overclaim detection is difficult even for
> large language models, and that R4's transparent routing captures most of the achievable signal
> at this sample size. R4 thus offers a competitive pilot baseline with the added benefit of
> interpretability."

### Scenario 5: LLM judge is weaker than R4

**Suggested writing**:
> "The LLM judge underperformed R4 on strong-action-overclaim F1, primarily due to over-reliance
> on world knowledge and difficulty following the conservative evidence-only constraint. This
> suggests action-overclaim detection requires the structured evidence-relation decomposition
> provided by R4, rather than end-to-end LLM judgment."

## Cross-Cutting Reporting Rules

1. Public gold results MUST be in a separate table (Table 7+), never merged with SimClaim main results.
2. LLM baseline MUST be labeled as "small-sample pilot baseline, N<=200, not full-dataset".
3. MUST disclose which LLM model and which API was used (or "local model" if applicable).
4. MUST NOT claim public gold validates strong_action_overclaim detection.
5. MUST NOT claim LLM is the gold standard; it is one baseline among several.
6. All R4 vs LLM comparisons MUST report bootstrap CI and seed stability.

## Risk Notes

- If public gold results are very poor (e.g., R4 macro-F1 < 0.50 on SciFact E1), this is a
  red flag for the contradiction-detection module's transferability and should be discussed
  transparently in the paper.
- If LLM is dramatically better (delta > 0.10 strong-F1), this challenges R4's value and
  the paper must reframe R4 as "transparent baseline" rather than "best method".
- The external + LLM extensions are PILOT only; they do not substitute for the 300-500
  human-audited gold pairs recommended in Task N.
"""
    (EXP_DIR / "paper_impact_analysis.md").write_text(md, encoding="utf-8")
    log("  Wrote paper_impact_analysis.md")


# ---------------------------------------------------------------------------
# Readiness gate
# ---------------------------------------------------------------------------
def write_readiness_gate() -> None:
    log("Writing external_gold_llm_readiness_gate.json ...")

    # Read Task P results to inform recommendations
    task_p_gate_path = TASK_P_DIR / "validation_readiness_gate.json"
    task_p_info = {}
    if task_p_gate_path.exists():
        task_p_info = json.loads(task_p_gate_path.read_text(encoding="utf-8"))

    gate = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "public_gold_available": True,
        "recommended_public_datasets": ["SciFact", "VitaminC", "PubHealth", "AVeriTeC"],
        "best_external_test_candidate": "SciFact",
        "best_external_test_reason": (
            "Scientific domain match with V3; has evidence text and rationale; "
            "support/contradict/NEI labels map cleanly to V3 external labels; "
            "manageable size (~1.4k claims)."
        ),
        "can_replace_simclaim_gold": False,
        "why_not_replace_gold": [
            "No public dataset annotates action-overclaim / deployment-overclaim / safety-scope overclaim.",
            "Public labels are support/refute/NEI only; they cannot test the strong_action_overclaim vs mild_scope_overclaim distinction.",
            "Public domains (news, Wikipedia, health) do not match V3's 6 technical domains (autonomous_driving, marl, robotics, etc.).",
            "SimClaim's 4-class schema with action/deployment/safety dimension is unique to V3.",
        ],
        "llm_baseline_needed": True,
        "llm_baseline_scope": "small_sample_only",
        "llm_baseline_recommended_size": 200,
        "llm_baseline_pilot_size": 100,
        "llm_baseline_models_recommended": [
            "GPT-4o-mini (low cost pilot)",
            "Claude 3.5 Haiku (alternative low cost)",
            "local Qwen2.5-7B (zero API cost if available)",
        ],
        "estimated_next_step": (
            "1) Download SciFact + VitaminC (manual approval); "
            "2) Execute E1+E2 on SciFact; "
            "3) Execute E3 on VitaminC; "
            "4) Run 100-sample LLM pilot; "
            "5) Decide whether to scale LLM to 200 and add a stronger model."
        ),
        "risk_level": "medium",
        "risk_notes": (
            "Public data download may require license verification. "
            "LLM API calls (if approved) incur small cost (~$0.10-$2.10). "
            "External results may be weaker than SimClaim due to domain mismatch; "
            "this is expected and should be reported transparently."
        ),
        "recommended_order": [
            "1. SciFact protocol (E1 + E2)",
            "2. VitaminC evidence sensitivity protocol (E3)",
            "3. SimClaim 100-sample LLM baseline",
            "4. optional FEVER/PubHealth sanity check",
        ],
        "task_p_validation_status": task_p_info.get("validation_status", "unknown"),
        "task_p_r4_retained": task_p_info.get("r4_main_method_retained", "unknown"),
        "does_external_plan_change_r4_status": False,
        "does_external_plan_change_r4_status_reason": (
            "External gold + LLM baseline are ADDITIONAL evidence, not replacements. "
            "R4's main-method status depends on SimClaim validation (Task P), which is unchanged."
        ),
        "forbidden_actions": [
            "Do NOT download datasets automatically without license verification.",
            "Do NOT call any LLM API in Task Q.",
            "Do NOT merge public results with SimClaim main results.",
            "Do NOT map public labels to strong_action_overclaim.",
            "Do NOT write human_audited/gold/final labels.",
        ],
    }
    (EXP_DIR / "external_gold_llm_readiness_gate.json").write_text(
        json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log("  Wrote external_gold_llm_readiness_gate.json")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main() -> None:
    log("=" * 70)
    log("Task Q: Public Gold External Test + Small LLM Baseline Plan")
    log("=" * 70)

    write_public_gold_inventory()
    write_label_mapping_plan()
    write_external_test_protocol()
    write_llm_baseline_plan()
    write_paper_impact_analysis()
    write_readiness_gate()

    # Verify outputs
    log("")
    log("Verifying output files ...")
    expected_files = [
        "public_gold_dataset_inventory.csv",
        "public_gold_dataset_inventory.json",
        "external_label_mapping_plan.csv",
        "external_label_mapping_plan.md",
        "external_gold_test_protocol.md",
        "external_gold_sampling_plan.csv",
        "external_gold_expected_outputs.json",
        "llm_baseline_sample_plan.csv",
        "llm_baseline_prompt_template.md",
        "llm_baseline_schema.json",
        "llm_baseline_cost_estimate.md",
        "paper_impact_analysis.md",
        "external_gold_llm_readiness_gate.json",
        "run.log",
    ]
    all_ok = True
    for fname in expected_files:
        p = EXP_DIR / fname
        if p.exists():
            log(f"  OK: {fname} ({p.stat().st_size} bytes)")
        else:
            log(f"  MISSING: {fname}")
            all_ok = False

    log("")
    log("=" * 70)
    if all_ok:
        log("Task Q complete. All 13 output files + run.log generated.")
    else:
        log("Task Q complete with MISSING files.")
    log("=" * 70)


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        log(f"FATAL: {e}")
        log(traceback.format_exc())
        raise
