# Next-Phase Benchmark Expansion Plan & Annotation Package

> Status: planning document for the post-pilot (submission-grade) phase.
> This is NOT a paper result. The current `clean_v2` release (n_test=16,
> `paper_ready=false`) remains a pilot diagnostic; this document defines
> what must be true before any result is reported as submission-grade.

## 1. Why a new phase is required (pilot diagnosis)

The `clean_v2` pilot release exposed four credibility gaps that disqualify
the current numbers from being reported as main results:

| Gap | Evidence (from `release/`) | Consequence |
|-----|----------------------------|-------------|
| Sample size | n_train=48, n_dev=16, n_test=16; all `oracle` source_type | n_test<30 → metrics are pilot_only, no statistical claim possible |
| Probability collapse | `error_analysis.md`: prob_mean=0.316, prob_std=0.0079, prob_min=0.3002, prob_max=0.3346 | Operating threshold 0.325 sits inside a 0.03-wide band; F1 swings 0.6667→0.2222→0.0000 across a 0.025 threshold move |
| No human audit | `human_audited_count=0`; `contradiction_positive_count=0` | Labels are template-derived, not adjudicated; no κ, no contradiction-positive stratum |
| Evidence-mode gap | `source_type_counts={oracle:80}`; `oracle_extracted/comparison_results.json` incomplete | Cannot demonstrate the model is necessary vs. an oracle-only pipeline |

These are recorded as `blocking_reasons` in `release/RESULTS_MANIFEST.json`
and must NOT be cleared by toggling flags; they must be cleared by data.

## 2. Benchmark expansion targets (submission-grade)

### 2.1 Scale and splits

| Target | Pilot | Submission-grade | Rationale |
|--------|-------|------------------|-----------|
| Total annotated | 80 | 600–800 | Enough for n_test≥150 after 70/15/15 split |
| n_test | 16 | ≥150 | Required for bootstrap CI width ≤ 0.05 on F1 |
| Human-audited | 0 | 100% of test + 30% of train (stratified) | Adjudicated gold for every reported number |
| Contradiction-positive | 0 | ≥30% of test | Powers `contradiction_f1` and error analysis |
| Annotators / sample | 1 (template) | ≥3 independent + 1 adjudicator | κ≥0.6 gate |

### 2.2 Domain and source-type coverage

Domains (from `simclaim_eval_schema.json` enum) must be balanced, not the
current academic_claim-heavy pilot:

- `controlled_simulation`, `cyber_defense`, `academic_claim`,
  `wargaming`, `digital_twin` — target ≥120 samples each.

Source-type triples (the `oracle / extracted / confidence_aware` axis in
`schemas/simclaim_eval_schema.json`):

- For each `logical_sample_id`, produce three rows sharing a stable
  prefix (`claim-0001`, `claim-0001-extracted`, `claim-0001-confaware`).
- `oracle`: human gold evidence (current pilot).
- `extracted`: pipeline-extracted evidence (run `scripts/build_source_triples.py`).
- `confidence_aware`: extracted + confidence lower-bound applied
  (exercises `confidence_lower_bound` loss).
- This unblocks `oracle_extracted_confidence.md` and the
  `oracle/extracted/confidence-aware` comparison mandated by the spec.

### 2.3 Contradiction-positive construction

Adversarial/contradiction samples are generated via
`scripts/build_adversarial_splits.py` and must be human-adjudicated:

- ≥30% of test set has `contradiction_label=1`.
- `escalation_type` populated for every `escalation_label=1` sample
  (scope/causal/action/certainty).
- Stratify so each of the 4 dimensions appears as the escalation driver
  in ≥15% of positives.

## 3. Annotation package (reuse existing infrastructure)

The annotation package already exists; this phase extends data volume,
not schema. Do NOT fork new templates.

### 3.1 Canonical schema (already in repo)

- Field schema: [schemas/simclaim_eval_schema.json](../schemas/simclaim_eval_schema.json)
  — JSON Schema draft 2020-12, validates `source_type`,
  `evidence_vector` (8 dims), `claim_tiers`/`support_tiers` (4 dims,
  0–4), `contradiction_label`, `escalation_label`, `escalation_type`,
  `evidence_gap_labels`, `tier_exceedance_gap_labels`, `parent_sample_id`.
- Annotation guide: [docs/annotation_guide.md](annotation_guide.md) and
  [schemas/annotation_guide.md](../schemas/annotation_guide.md) — tier
  anchors 0–4, the "non-contradiction ≠ support" core principle.
- Minimal field reference:
  [schemas/pilot_annotation_minimal_schema.md](../schemas/pilot_annotation_minimal_schema.md)
- Template (CSV/JSONL):
  [data/templates/pilot_annotation_template.csv](../data/templates/pilot_annotation_template.csv)
  and `pilot_annotation_template.jsonl` — already contain all 40 fields
  including `annotator_id`, `annotation_round`, `agreement_score`,
  `is_human_audited`, `evidence_spans`, `extraction_method`.

### 3.2 Submission-grade annotation workflow

```
1. Author claim-evidence pairs (claim text + gold evidence) per domain
   → data/annotations/submission_raw.jsonl
2. For each pair, generate extracted + confidence_aware variants
   → scripts/build_source_triples.py
   → produces data/derived/submission_triples.jsonl
3. Distribute to ≥3 annotators using the template (blinded to gold
   tiers; they label claim_tiers, support_tiers, contradiction_label,
   escalation_label, evidence_gap_labels, evidence_spans)
   → data/annotations/submission_ann_{01,02,03}.jsonl
4. Compute inter-annotator agreement
   → scripts/compute_annotation_agreement.py
   → outputs/paper/agreement_report.json (κ per dim; gate κ≥0.6)
5. Adjudicate disagreements → data/annotations/submission_adjudicated.jsonl
6. Import + validate against schema
   → scripts/import_annotations.py
   → cese/data/annotation_io.py (schema validation)
7. Build splits (stratified by domain × source_type × contradiction)
   → scripts/build_paper_splits.py
   → data/clean_v3_split/{train,dev,test}.jsonl
8. Collate → data/clean_v3_all.jsonl; re-run release pipeline
```

### 3.3 Quality-control gates (hard requirements)

- κ (Cohen / Fleiss) ≥ 0.6 on each of the 8 evidence_vector dims and 4
  tier dims; below-gate dims are dropped from reporting with a documented
  reason.
- Every test sample adjudicated; train/dev ≥30% adjudicated.
- `is_human_audited=true` for 100% of test rows (checked by
  `scripts/audit_dataset.py --require-multi-annotator`).
- Schema validation: every JSONL line must pass
  `simclaim_eval_schema.json` (run `tests/test_schema.py`).

## 4. Baseline expansion roadmap

The spec calls for strong baselines; current status after this iteration:

| Baseline | Status | Next step |
|----------|--------|-----------|
| Lexical cue (LR over hand-crafted features) | ✅ implemented, offline | rerun on clean_v3 |
| Logistic regression (evidence vector) | ✅ implemented, offline | rerun on clean_v3 |
| Random forest (evidence vector) | ✅ implemented, offline | rerun on clean_v3 |
| Gradient boosting (evidence vector) | ✅ implemented, offline | rerun on clean_v3 |
| RAG-LLM baseline | requires API key | run once API available; config in `configs/paper_baselines.yaml` |
| Structured LLM judge | requires API key | run once API available |
| NLI baseline (`cese/baselines/nli_baseline.py`) | implemented | enable in `configs/baselines_clean_v2.yaml`, run offline |
| Scifact verifier | implemented | enable, run offline |
| ARES-style / RAGAS-style evaluators | implemented | enable, run offline |
| Pairwise LLM judge | requires API | run once API available |

Priority: enable the three offline-implemented but not-yet-run baselines
(NLI, scifact, ARES/RAGAS) on clean_v3 so the main-results table has
≥6 non-CESE rows without API access.

## 5. Model improvement roadmap (addresses probability collapse)

The `error_analysis.md` diagnosis (`threshold_too_high`,
`prob_distribution_narrow`, `support_branch_too_conservative`) points to
three fixes, in priority order:

1. **Support branch recalibration.** prob_std=0.0079 means the support
   branch outputs near-constant logits; the ordinal head cannot
   discriminate. Investigate `cese/models/evidence_branch.py` and the
   ordinal loss weighting in `cese/losses/ordinal_losses.py` — likely
   the support branch is dominated by the constant-feature regime of
   n_train=48.
2. **Training data scale.** clean_v3 (600–800) should widen the
   feature distribution; re-evaluate prob_std after retraining.
3. **Encoder upgrade.** Replace `test-stub` encoder (used in
   `configs/ablations_clean_v2.yaml` for offline ablations) with a real
   encoder once network/cache is available; the paper-full profile uses
   `distilbert-base-uncased`.

## 6. Success criteria for the submission-grade release

A release may set `paper_ready=true` only when ALL hold:

1. n_test ≥ 150; bootstrap CI half-width ≤ 0.05 on escalation_f1.
2. `human_audited_count` = 100% of test; `contradiction_positive_count`
   ≥ 30% of test.
3. Inter-annotator κ ≥ 0.6 on every reported dimension.
4. `source_type` coverage: oracle + extracted + confidence_aware all
   present with ≥150 samples each; `oracle_extracted_confidence.md`
   complete.
5. ≥6 baselines run (3 sklearn + ≥3 of NLI/scifact/ARES/RAGAS/LLM).
6. Calibration ablation: no_calibration / separate_thresholds /
   shared_threshold all present with n>0.
7. Constraint ablation: no_constraint / monotonicity_only /
   hard_truncation / full all present with n>0.
8. `main_results / error_analysis / threshold_sensitivity / eval_test`
   four-table metric consistency (already enforced this iteration).
9. `prob_std > 0.05` (probability distribution no longer collapsed).

Until then, every table carries the
"Pilot pipeline validation only. Not submission-ready" banner and
`paper_ready` stays `false`.

## 7. Pointers into the existing code

| Concern | File |
|---------|------|
| Schema validation | `cese/data/annotation_io.py`, `tests/test_schema.py` |
| Annotation import | `scripts/import_annotations.py` |
| Agreement / κ | `scripts/compute_annotation_agreement.py` |
| Triple construction (oracle/extracted/confaware) | `scripts/build_source_triples.py`, `scripts/build_oracle_extracted_pairs.py` |
| Adversarial / contradiction splits | `scripts/build_adversarial_splits.py` |
| Paper splits | `scripts/build_paper_splits.py` |
| Audit / paper-readiness gate | `scripts/audit_dataset.py`, `scripts/check_paper_readiness.py` |
| Release bundle + manifest | `scripts/build_release_bundle.py`, `scripts/run_release_pipeline.py` |
| Table generation (consistency) | `scripts/generate_tables.py` |
| Baseline registry | `cese/baselines/__init__.py` (`BASELINE_STATUS_REGISTRY`) |
