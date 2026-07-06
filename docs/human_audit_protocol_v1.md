# Human Audit Protocol v1 (Small Targeted Audit)

## Purpose

This protocol defines a **small targeted human audit** of the V3.17 silver
diagnostic candidate pool. The audit is **not** a gold benchmark and must not be
described as one. Its only purpose is to provide directional evidence on whether
the top of the review queue and the `strong_action_overclaim` label direction are
reliable enough to support downstream diagnostic claims.

The 444-candidate pool is silver-labeled (`candidate_label_guess`), all rows have
`human_audited=False`, and `gold_label` is empty. This audit does **not** change
that. It produces a small set of auditor labels over a targeted sample, kept
private (hash-only in any public artifact).

## Scope

- Target sample size: **80–120 candidates** (default 120, configurable via `--n`).
- Sample source: 444-candidate `strict_silver_max_candidates_v1.csv` plus
  `canonicalized_r4_review_scores.csv`, `review_queue_top100_best.csv`, and
  `error_cases_redacted.csv`.
- The audit is a **directional reliability check**, not coverage of the dataset.

## What This Audit Is Not

- Not a gold benchmark.
- Not a human-validated dataset.
- Not a basis for changing `silver_label` or `candidate_label_guess` in the
  original CSV.
- Not a basis for filling `gold_label`.
- Not coverage of all 444 candidates.
- Not used for scoring, ranking, or feature engineering.

## Sampling Focus

The seed queue is built to over-sample the cases that matter most for
directional reliability. Sampling buckets (allocation is approximate; the build
script enforces a hard cap of 2 candidates per `target_candidate_group_id`):

1. **Top-20 review queue** — all candidates in the top 20 of the canonicalized
   review queue. This tests whether the head of the queue is directionally
   correct.
2. **Top-50 review queue restricted to `strong_action_overclaim`** — strong
   action is the highest-stakes label for the paper; we want extra coverage in
   the top 50.
3. **R4 false positives (FP)** — candidates whose `true_label` (silver) is not
   `strong_action_overclaim` but whose R4 prediction is. Sampled from
   `error_cases_redacted.csv` where `error_category == "FP"`.
4. **R4 false negatives (FN)** — candidates whose `true_label` (silver) is
   `strong_action_overclaim` but whose R4 prediction is not. Sampled from
   `error_cases_redacted.csv` where `error_category == "FN"`.
5. **Mild vs strong boundary** — candidates tagged `mild_vs_strong_boundary`
   in `error_type_tags`. These are the cases where the mild/strong line is
   most likely to be disputed.
6. **Contradiction confusion** — candidates tagged `contradiction_confusion`
   in `error_type_tags`. These are the cases where contradiction and strong
   action are most often conflated.

Sampling is deterministic (fixed seed) and group-aware: each
`target_candidate_group_id` contributes at most 2 candidates to the audit seed,
so the audit is not dominated by a few large groups.

## Audit Labels

Auditors assign exactly one of the following labels per candidate:

| Label | Meaning |
|-------|---------|
| `supported` | The claim is supported by the cited evidence at the stated scope. |
| `mild_scope_overclaim` | The claim slightly overstates scope but the direction is right. |
| `strong_action_overclaim` | The claim substantially overstates an action, result, or capability. |
| `contradiction_candidate` | The claim is contradicted by (or cannot be reconciled with) the evidence. |
| `uncertain_insufficient_context` | The auditor cannot decide with the available context. |

`uncertain_insufficient_context` is a legitimate label, not a fallback. If the
auditor cannot decide, they must use it rather than forcing a guess.

## Per-Record Fields

Each audit record (row in the filled audit CSV) must contain:

- `audit_item_id` — stable ID for this audit row.
- `candidate_id` — the candidate being audited.
- `target_candidate_group_id` — the group the candidate belongs to.
- `source_hash` — hash of the source document identifier (already in candidate CSV).
- `claim_text_hash` — `claim_text_sha256` from the candidate CSV (no raw text).
- `evidence_text_hash` — `evidence_text_sha256` from the candidate CSV (no raw text).
- `model_pred` — R4 predicted label.
- `silver_label` — `candidate_label_guess` from the candidate CSV.
- `queue_rank` — rank in the review queue (0 if not in queue).
- `queue_source` — which sampling bucket this candidate came from.
- `auditor_label` — one of the 5 audit labels above.
- `auditor_confidence` — integer 1–5 (1=very unsure, 5=very confident).
- `audit_notes` — short free-text note (auditor should avoid pasting raw claim/evidence).
- `disagreement_reason` — if `auditor_label != silver_label`, a short reason.
- `requires_second_review` — `True`/`False`. Must be `True` when
  `auditor_confidence <= 2` or when `auditor_label != silver_label` and the
  disagreement is on the supported vs strong_action_overclaim axis.
- `human_audited` — `True` once the row has been filled by an auditor.
- `created_at` — ISO-8601 timestamp of the audit row.

## Confidentiality

- The audit template and seed queue **must not** contain raw `claim_text` or
  `evidence_text`. Only hashes.
- If an auditor wants a private copy of the audit table that joins back to raw
  text for convenience, that file must live under `data/private_audit/` and is
  gitignored. The repo never commits raw text.
- Public/redacted audit summaries use only hashes, ranks, predicted/silver/
  auditor labels, and aggregate counts.

## Workflow

1. Run `scripts/build_human_audit_queue_v1.py` to produce
   `data/audit_templates/human_audit_queue_seed_v1.csv` (private, may join to
   raw text via `data/private_audit/`) and
   `data/audit_templates/human_audit_queue_seed_v1_redacted.csv` (public,
   hash-only).
2. An auditor fills `auditor_label`, `auditor_confidence`, `audit_notes`,
   `disagreement_reason`, `requires_second_review`, and sets `human_audited=True`
   for each row.
3. Optionally, a second auditor independently re-audits any row with
   `requires_second_review=True`. Adjudication is recorded in
   `disagreement_reason` or a new column in the private audit table.
4. Run `scripts/summarize_human_audit_v1.py` on the filled audit CSV to produce
   `experiments/human_audit_v1/` with agreement summary, confusion matrix,
   redacted disagreement cases, and `audit_summary.md`.

## What the Summary May and May Not Claim

**Allowed** (safe wording):
- "small targeted audit, not a gold benchmark"
- "directional reliability check on the top of the review queue"
- "auditor agreement with silver on the audited subset was X%"
- "strong_action precision in the top-20 audited subset was Y"

**Forbidden** (unsafe wording):
- "human-validated dataset"
- "gold benchmark"
- "the silver labels are correct"
- "the model generalizes to real claims"
- "SOTA"

The audit exists to support directional reliability claims about the top queue
and the `strong_action_overclaim` direction, nothing more.
