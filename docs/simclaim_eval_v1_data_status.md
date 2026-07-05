# SimClaim-Eval v1 Data Status

This document records the **current data layer hierarchy** for the CESE-OCN project
and the restrictions that apply to each layer. It exists to prevent the round1
seed set from leaking into paper-valid outputs or being mistaken for a gold
benchmark.

## Current data layers

### 1. `simclaim_human_pilot` — existing paper line

- Location: `data/human_pilot/`, `release_simclaim_human_pilot/`
- Role: controlled pilot diagnostic validation, the existing paper line.
- Status: this is the only dataset that may feed `release_simclaim_human_pilot/`
  main tables (subject to its own pilot-vs-paper_full gating rules).
- paper-valid: governed by the existing pilot/paper_full ruleset, not by this
  document.
- human-audited: governed by the existing pilot/paper_full ruleset.

### 2. `simclaim_eval_v1/round1_seed` — newly imported seed set

- Location: `data/simclaim_eval_v1/round1_seed/`
- Role: seed set for annotation guideline refinement and controlled pipeline
  testing.
- Source: `simclaim_round1_user_confirmed_adjudicated.zip` (user-confirmed
  GPT-adjudicated labels, created 2026-06-29).
- Composition: 42 samples; 31 escalation-positive, 11 escalation-negative,
  0 contradiction-positive.
- Label provenance: GPT `annotator_01` + CODEX `annotator_02` + GPT
  adjudication + user final confirmation of the 4-item final-check queue.
- Frozen fields (every record):
  - `human_audited = false`
  - `gold_label = false`
  - `paper_valid = false`
  - `main_text_allowed = false`
- `label_source = user_confirmed_gpt_adjudicated_round1`
- `annotation_status = user_confirmed_adjudicated_seed`

**Important caveat:** `user_confirmed=true` does **not** imply
`human_audited=true` in the paper sense. "User-confirmed" means a single
reviewer signed off on the GPT-adjudicated labels for internal round1 use; it
is **not** dual-human annotation, **not** domain-expert adjudication, and
**not** a paper-grade gold audit.

### 3. `simclaim_eval_v1_core` — future human-audited core

- Location: to be created under `data/simclaim_eval_v1/core/`.
- Role: to be constructed from human-audited source-paired samples.
- Status: not yet built. This is the future paper-grade benchmark candidate.

## Allowed use of `round1_seed`

- annotation guideline refinement
- pipeline smoke test
- candidate quality inspection
- weak controlled training / debug **only if explicitly marked** as
  non-paper-valid

## Forbidden use of `round1_seed`

- main paper evaluation
- benchmark claim
- human-audited test set
- external validation
- final gold labels
- paper-ready evidence

## Hard separation rules

The following actions are explicitly forbidden:

1. Do **not** merge `round1_seed` into `data/human_pilot` or any
   `human_pilot`-derived split.
2. Do **not** overwrite `release_simclaim_human_pilot/` outputs with
   `round1_seed` data.
3. Do **not** modify the audit-fixed `.docx` annotation guide.
4. Do **not** run model training against `round1_seed` and report results as
   main paper results.
5. Do **not** set `paper_ready=true` or `paper_valid=true` on any artifact
   derived from `round1_seed`.
6. Do **not** add `round1_seed`-derived tables to `main_tables/` or
   `supplementary_tables/` of the paper package.
7. Do **not** relabel `user_confirmed` as `human_audited` in any downstream
   artifact.

## Forbidden terminology for `round1_seed`

When describing the round1 seed set, the following terms are **forbidden**:

- "benchmark"
- "gold"
- "human-audited"
- "paper-ready"
- "external validation"

Permitted phrasings:

- "user-confirmed GPT-adjudicated round1 seed set"
- "internal seed set for annotation guideline refinement"
- "non-paper-valid controlled diagnostic set"

## Cross-reference

- Dataset card: `data/simclaim_eval_v1/round1_seed/dataset_card.md`
- Manifest: `data/simclaim_eval_v1/round1_seed/manifests/round1_seed_manifest.json`
- Validation report: `data/simclaim_eval_v1/round1_seed/reports/round1_seed_validation_report.{json,md}`
- Validation script: `scripts/validate_round1_seed_import.py`
- Generation script: `scripts/generate_round1_seed_processed.py`
