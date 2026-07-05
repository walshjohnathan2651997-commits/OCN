# One-Page Project Summary — CESE-OCN V3.7

**Current version: advisor-review draft, not final submission.**

---

## Title

Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework

## Problem

Scientific claim verification is typically framed as a three-class support/refute/NEI task (FEVER, SNLI, SciFact). This framing misses the most frequent and consequential failure mode in scientific writing: evidence is topically relevant and directionally consistent, but does not justify the *strength* of the claim — particularly when a claim asserts deployment readiness, actionability, safety, policy, or broad generalization on limited experimental evidence. We call this **evidence sufficiency calibration**.

## Method

Four-class relation task: **supported**, **mild_scope_overclaim**, **strong_action_overclaim**, **contradiction_candidate**.

**CESE-OCN R4** — a mixed relation-routing framework:
1. Contradiction detector first (most separable via NLI signals).
2. Strong-action escalation under a conservative contradiction guard (prevents contradiction cases being absorbed into strong_action).
3. Supported/mild residual classifier.

Frozen mean thresholds: `t_contra=0.48`, `t_strong=0.535`, `t_svm=0.51`, `t_low`=lower guard. R4 is positioned as a **complement** to generic LLM/NLI judges, not a replacement.

## Dataset

- **SimClaim silver-label pilot**: 444 claim-evidence pairs, 111 evidence groups, 6 domains (autonomous_driving, cyber_defense, digital_twin, robotics,RL/MARL, policy/safety).
- AI-preannotated + author-screened labels (silver, **not gold**).
- Author sanity audit: 25/40 (62.5%) questionable/unclear, concentrated at mild-vs-strong and strong-vs-contradiction boundaries.
- External sanity: SciFact (271/seed) and VitaminC (300/seed) — public datasets used for transfer check, not as gold replacement.

## Key results

| Result | Value |
|---|---|
| R4 strong_action positive-F1 (444 silver pilot) | **0.3967** (baseline 0.2408, +0.1559, bootstrap CI [0.1058, 0.1988], 10/10 seeds positive) |
| R4 strong_action-F1 (matched 100) | **0.3000** |
| GPT-5.5 standard strong_action-F1 (matched 100) | 0.0769 (recall 0.04 = 1/25) |
| GPT-5.5 structured strong_action-F1 (matched 100) | 0.0769 (identical to standard) |
| DeepSeek-V3 strong_action-F1 (matched 200) | 0.0769 |
| GPT-5.5 macro-F1 (matched 100) | 0.5523 (highest overall) |
| R4 macro-F1 (matched 100) | 0.3280 (substantially lower) |
| SciFact best E1 macro-F1 | 0.6895 (NLI cross-encoder) |
| VitaminC best E1 macro-F1 | 0.6686 (NLI cross-encoder) |

**Core finding:** Under the tested prompts, generic LLM judges under-detect `strong_action_overclaim` (F1 0.0769, recall 0.04). Structured prompting did not fix this. R4 targets this gap (F1 0.3000, +0.2231 absolute) at the cost of lower overall macro-F1. R4 is a relation-specific complement, not a replacement.

## Main limitation

**All 444 SimClaim labels are silver, not gold.** The LLM under-detection finding is computed against silver labels, so it must be interpreted as diagnostic evidence against silver labels, pending independent gold adjudication — not as an established property of LLM judges. A 50-100 pair gold pilot (two-annotator independent review + adjudication) is the single highest-value next step. Other risks (LLM comparison is prompt/model/sample-specific, R4 macro-F1 lower than GPT, mild/strong boundary remains difficult, no independent adjudication) are documented in `reviewer_risk_brief.md`.

## Current readiness

- **Writing:** advisor-review draft, structurally complete (V3.7 final cleanup pass: `EMNAACP` typo fixed, table/figure numbering unified, no mojibake, no placeholder author info, docx generated).
- **Experiments:** pilot complete; no new experiments planned until gold pilot.
- **Validation:** internal R4 result + matched-sample LLM comparison + external SciFact/VitaminC sanity check done.
- **Not ready:** gold adjudication, larger LLM comparison, multi-domain expansion.

## Recommended next step

**Gold pilot (50-100 pairs, two-annotator independent review + adjudication)** targeting the 25 questionable/unclear cases in `high_risk_sample_bank.csv` plus randomly sampled clear cases. This is the single step that would most strengthen (or falsify) the central claim. If gold κ on the mild/strong boundary is ≥ 0.4, the taxonomy holds and the paper can be strengthened for submission; if κ < 0.4, the `strong_action_overclaim` class may need to be merged with `mild`, and the paper's central contribution weakens. Estimated effort: 2-4 weeks with two annotators.

---

*Enclosed files: `CESE_OCN_V3_7_advisor_handoff_clean.md` (+ `.docx`), `advisor_cover_note.md`, `reviewer_risk_brief.md`, `V3_7_cleanup_log.md`, `V3_7_file_manifest.csv`. Current version: advisor-review draft, not final submission.*
