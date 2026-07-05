# SimClaim-Eval v1 Current Data Status Lock

**Locked at (UTC):** 2026-06-30T11:30:00Z
**Status:** Data expansion paused. No further round2 expansion, no annotation of round2 candidates, no model training, no CESE evaluation, no main_results generation.

This document locks the current state of all SimClaim data lines to prevent accidental mixing of `human_pilot`, `round1_seed`, and `round2_batch01_annotation_ready_v1`.

---

## Three data lines (must not be mixed)

### 1. simclaim_human_pilot (paper main line)

**Path:** `release_simclaim_human_pilot/`

**Status:**
- 150 controlled pilot diagnostic validation samples.
- Current paper main line.
- **Do not modify.**
- **Do not mix into round1 or round2.**

**Frozen fields:**
- `paper_valid` = false (pilot pipeline validation only, not paper-full)
- `human_audited` = false (single-annotator pilot, not dual-human audited)
- `metric_valid` = true (metrics are internally valid)
- `dataset_role` = controlled pilot diagnostic validation

**Intended use:**
- Pilot pipeline validation.
- Diagnostic baselines (TF-IDF, SVM, CESE).
- Multiseed stability and delexicalization controls.
- **Not** a human-audited benchmark.
- **Not** external validation.

**Key artifacts:**
- `results.md` (43 KB) - pilot results summary.
- `baselines_results.json` (51 KB) - baseline metrics.
- `multiseed.log` / `multiseed_results.csv` - stability validation.
- `paper_readiness_report.json` / `.md` - paper readiness gate status.
- `bootstrap_ci.json`, `paired_significance.json` - confidence intervals and significance tests.
- `delexicalized_eval/` - delexicalization control results.

**Current paper readiness (per `paper_readiness_report.json`):**
- `paper_ready` = false (pilot mode, not paper-full).
- Missing: human-audited gold, larger test set, strong baselines (BERT/RoBERTa/DeBERTa), OOD validation.

---

### 2. round1_seed (user-confirmed GPT-adjudicated seed)

**Path:** `data/simclaim_eval_v1/round1_seed/`

**Status:**
- 42 rows.
- User-confirmed GPT-adjudicated seed labels.
- `final_label` = true (final for the internal round1 seed set only).
- `user_confirmed` = true (user confirmed the final-check queue).
- `human_audited` = **false** (NOT human-audited).
- `gold_label` = **false** (NOT gold).
- `paper_valid` = **false** (NOT paper-valid).
- `main_text_allowed` = **false** (NOT for main text tables).
- `label_source` = `user_confirmed_gpt_adjudicated_round1`.
- `annotation_status` = `user_confirmed_adjudicated_seed`.

**Intended use:**
- Annotation guideline refinement.
- Pipeline smoke test.
- Candidate quality inspection.
- Weak controlled training/debug **if explicitly marked**.

**Forbidden use:**
- Main paper evaluation.
- Benchmark claim.
- Human-audited test set.
- External validation.
- Final gold labels.
- paper_ready evidence.

**Important scope note:**
These labels are **user-confirmed GPT-adjudicated round1 seed labels**. They are final labels for the internal round1 seed set only. They are **not** dual-human audited gold labels. Describe them as:
> user-confirmed GPT-adjudicated round1 seed labels

Do **not** describe them as:
- human-audited benchmark
- gold test set
- final paper benchmark
- external validation set

**Key artifacts:**
- `processed/round1_seed_adjudicated.csv` (45 KB) - 42 rows, 34 fields.
- `processed/round1_seed_adjudicated.jsonl` (75 KB) - JSONL format.
- `manifests/round1_seed_manifest.json` - manifest with by_domain/by_hard_case_type/by_escalation_type.
- `dataset_card.md` - dataset card.
- `reports/round1_coverage_gap_report.md` / `.json` - coverage gap analysis.
- `reports/round1_seed_validation_report.md` / `.json` - 13-check validation (all PASS).
- `raw/` - original user-confirmed package files.

**Distribution summary:**
- Total: 42
- Escalation label = 1: 31
- Escalation label = 0: 11
- Contradiction label = 1: 0
- By domain: wargaming 10, cyber_training 10, digital_twin 7, traffic_simulation 4, cyber_emulation 3, cyber_wargaming 3, epidemic_policy 3, public_health_tabletop 2.
- By hard_case_type: scenario_scope_overclaim 10, strong_language_supported 6, policy_actionability_overclaim 6, cyber_actionability_overclaim 3, insufficient_not_contradiction 4, noisy_evidence 1, others.

---

### 3. round2_batch01_annotation_ready_v1 (annotation-ready candidates, NOT yet annotated)

**Path:** `data/simclaim_eval_v1/round2_candidates/batch01_annotation_ready_v1/`

**Status:**
- 14 rows.
- Annotation-ready candidates only.
- `annotation_status` = `candidate_unreviewed`.
- `final_label` = **false** (NOT final).
- `human_audited` = **false** (NOT human-audited).
- `gold_label` = **false** (NOT gold).
- `paper_valid` = **false** (NOT paper-valid).
- `main_text_allowed` = **false** (NOT for main text tables).

**Composition:**
- 9 strict_dedup rows (from GPT-reviewed batch01 candidates).
- 5 recut unique additions (R2B01-002, R2B01-003, R2B01-033, R2B01-050, R2B01-055, passed both recut and GPT review).

**Excluded from main table (NOT in the 14 rows):**
- 3 optional duplicate review rows (R2B01-038, R2B01-052, R2B01-053) in `optional_review/`.
- 2 not-ready rejected rows (R2B01-046, R2B01-056) in `rejected/`.

**Intended use:**
- Annotation preparation.
- Source-trace review.
- Candidate review.

**Forbidden use:**
- Human-audited test set.
- Gold labels.
- Main paper evaluation.
- Benchmark.
- Model training without explicit weak/debug flag.
- Merging optional duplicates without explicit review.

**Important scope note:**
These 14 rows are **annotation-ready candidates**. They have **not** been annotated yet. They are **not** final labels, **not** human-audited, **not** gold, **not** paper-valid. The annotation has been **paused** per this status lock.

**Key artifacts:**
- `candidates/round2_batch01_annotation_ready_v1.csv` (14 rows).
- `optional_review/recut_optional_duplicate_review_before_merge.csv` (3 rows).
- `rejected/recut_not_ready_after_gpt_review.csv` (2 rows).
- `reports/round2_batch01_annotation_ready_v1_report.md`.
- `manifests/round2_batch01_annotation_ready_v1_manifest.json`.
- `main_csv_sha256` = `8250e4fa47488bdc7fb9b3fa98b0dbbcc1cecdf8253b647ec6d12020b63199b9`.

---

## Data line separation matrix

| Dimension | human_pilot | round1_seed | round2_batch01_v1 |
| --- | --- | --- | --- |
| **Path** | `release_simclaim_human_pilot/` | `data/simclaim_eval_v1/round1_seed/` | `data/simclaim_eval_v1/round2_candidates/batch01_annotation_ready_v1/` |
| **n_samples** | 150 | 42 | 14 |
| **label_source** | (pilot annotation) | user_confirmed_gpt_adjudicated_round1 | (none - candidate_unreviewed) |
| **final_label** | (per row) | true | **false** |
| **human_audited** | false | **false** | **false** |
| **gold_label** | false | **false** | **false** |
| **paper_valid** | false | **false** | **false** |
| **main_text_allowed** | false | **false** | **false** |
| **annotation_status** | (pilot) | user_confirmed_adjudicated_seed | candidate_unreviewed |
| **Annotated?** | Yes (pilot) | Yes (GPT-adjudicated, user-confirmed) | **No** (candidates only) |
| **Use for paper?** | Pilot results only | No | No |
| **Mix allowed?** | No | No | No |

---

## What is locked

Per this status lock:

1. **No further round2 expansion.** Do not start `batch02`. The next step after unfreezing would be to annotate the 14 `batch01_annotation_ready_v1` candidates, not to collect more candidates.
2. **No annotation of round2 candidates.** The 14 candidates remain `candidate_unreviewed`. Do not assign final labels.
3. **No model training.** No training on any of the three data lines without explicit unfreeze.
4. **No CESE evaluation.** No CESE evaluation runs on round1_seed or round2 candidates.
5. **No main_results generation.** No new main_results tables from round1 or round2 data.
6. **No modification of release_simclaim_human_pilot.** The paper main line is frozen.
7. **No modification of audit-fixed docx.** The annotation guide is frozen.
8. **No mixing of data lines.** The three data lines must remain separate. Do not merge round1_seed into human_pilot, do not merge round2 candidates into round1_seed, do not merge round2 candidates into human_pilot.
9. **No relabeling.** round1_seed labels remain user-confirmed GPT-adjudicated; they are not human-audited gold. round2 candidates remain `candidate_unreviewed`; they are not final labels.
10. **No benchmark claim.** None of the three data lines are benchmarks. human_pilot is pilot validation; round1_seed is seed; round2 is candidates.

---

## To unfreeze (future)

Before resuming data expansion, annotation, or training:

1. Confirm the 14 `batch01_annotation_ready_v1` candidates pass human review.
2. Annotate the 14 candidates with dual-annotator + adjudication protocol.
3. Only after annotation is complete, consider merging into a `simclaim_eval_v1_core` set.
4. Only after `simclaim_eval_v1_core` is human-audited, consider training or evaluation.
5. Do **not** merge `round1_seed` (GPT-adjudicated) with `simclaim_eval_v1_core` (human-audited) without explicit provenance tracking.

---

## Provenance

- This status lock was generated by reading:
  - `data/simclaim_eval_v1/round1_seed/manifests/round1_seed_manifest.json`
  - `data/simclaim_eval_v1/round2_candidates/batch01_annotation_ready_v1/manifests/round2_batch01_annotation_ready_v1_manifest.json`
  - `release_simclaim_human_pilot/` (file listing)
  - `docs/annotation_guidelines_simclaim_eval_v1.md`
- No files were modified during this status lock.
- No model was trained.
- No data was expanded.
