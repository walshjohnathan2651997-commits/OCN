# Annotation Guide (CESE-OCN / SimClaim-Eval)

This guide defines how to annotate claim–evidence pairs so the ordinal
tiers are a **measurement instrument** (reproducible, auditable), not a
free-form judgment. For the field-level schema see
[schemas/pilot_annotation_minimal_schema.md](../schemas/pilot_annotation_minimal_schema.md)
and [schemas/annotation_guide.md](../schemas/annotation_guide.md).

## 1. Core principle

> **Factual non-contradiction does NOT imply ordinal support.**

A claim that is "not contradicted" by the evidence is NOT automatically
supported at the claimed strength. Evidence that merely does not
contradict a "decisive" (tier 4) claim still yields `support_tiers = 0`
or `1` if it provides no positive backing. `support_tiers` is the
strength the evidence **positively establishes**, never the absence of
refutation. This is the single most common annotation error.

## 2. Claim tier anchors (0–4)

`claim_tiers[dim]` = the strength **asserted** by the claim text on
dimension `dim`.

| Tier | Anchor | Example cue |
|------|--------|--------------|
| 0 | silent / not addressed | The claim says nothing about this dim. |
| 1 | weak / anecdotal | "we observed", "in one run" |
| 2 | moderate / partial | "across several tests", "generally" |
| 3 | strong / multi-line | "robustly across all evaluated settings" |
| 4 | decisive / absolute | "always", "guarantees", "100%", "proves" |

Cue words are **signals, not definitions**. A claim without cue words
can still be tier 4 if it asserts an absolute outcome; a claim with
"always" used rhetorically (not as a coverage claim) may be lower.

## 3. Support tier anchors (0–4)

`support_tiers[dim]` = the strength the evidence **actually
establishes** on dimension `dim`. Apply the core principle: default to
0 and raise only when the evidence positively backs the dim.

| Tier | Anchor | Required evidence |
|------|--------|-------------------|
| 0 | none | No evidence addresses this dim. |
| 1 | weak | A single data point / one anecdotal mention. |
| 2 | moderate | Partial coverage: some sub-scenarios or one controlled comparison. |
| 3 | strong | Multiple lines of evidence spanning the claim's scope with quantified results. |
| 4 | decisive | Conclusive: exhaustive coverage, no reasonable counter-evidence, causal identification. |

`evidence_confidence[dim]` records how confident the annotator is in
their own rating; `1.0` for oracle human annotation.

## 4. Contradiction vs escalation (must be reported separately)

These are **distinct** labels and must be annotated independently.

- **`contradiction_label` (0/1)**: the evidence **directly refutes** the
  claim (e.g. claim says "zero false positives", evidence reports
  FPR=0.18). A contradiction is a factual conflict, not merely
  insufficient support.
- **`escalation_label` (0/1)**: `claim_tiers[dim] > support_tiers[dim]`
  for at least one `dim`. This is an **ordinal overclaim**: the claim
  is stronger than the evidence supports, even if nothing is
  contradicted.

Key cases:
- Evidence is silent ⇒ `contradiction=0`, but `escalation=1` if the
  claim is tier ≥ 2 (unsupported strength is an overclaim).
- Evidence contradicts ⇒ `contradiction=1`; escalation is determined
  separately by the tier comparison (usually also 1).
- Evidence fully supports a tier-2 claim ⇒ `contradiction=0`,
  `escalation=0`.

Never derive `contradiction_label` from the tiers; it is a factual
judgment about whether the evidence refutes the claim.

## 5. Per-dimension required evidence

Each of the four claim dimensions has a specific evidence requirement.
`support_tiers[dim]` may exceed 0 only when the listed evidence is
present.

### 5.1 `scope` (coverage / breadth)
- **Required evidence**: the evaluation spans the full scope the claim
  asserts (all stated populations, scenarios, operating regimes).
- Tier ≥ 3 requires multiple distinct sub-scenarios with results.
- Tier 4 requires exhaustive coverage with no untested sub-scope.
- **Gap label**: `coverage_missing` when the evidence covers only a
  subset of the claimed scope.

### 5.2 `causal` (causal identification)
- **Required evidence**: a counterfactual / control group / instrumental
  argument, not merely a correlation.
- Tier ≥ 2 requires at least one controlled comparison.
- Tier ≥ 3 requires a counterfactual or ablation isolating the cause.
- Tier 4 requires causal identification ruling out confounders.
- **Gap label**: `causal_missing` when only correlational evidence is
  offered for a causal claim.

### 5.3 `action` (deployability / recommendation)
- **Required evidence**: the system is shown to perform under
  deployment-relevant conditions (real pipeline, not just offline
  metrics), with downside/failure characterization.
- Tier ≥ 2 requires deployment-relevant evaluation.
- Tier ≥ 3 requires failure-mode and cost analysis.
- Tier 4 requires proven deployment with monitored outcomes.
- **Gap label**: `action_missing` when only offline metrics are offered
  for a deployment claim.

### 5.4 `certainty` (uncertainty quantification)
- **Required evidence**: uncertainty is quantified or bounded (error
  bars, confidence intervals, calibrated probabilities).
- Tier ≥ 2 requires reported uncertainty on the headline metric.
- Tier ≥ 3 requires calibrated / propagated uncertainty.
- Tier 4 requires rigorous uncertainty bounds with sensitivity
  analysis.
- **Gap label**: `uncertainty_missing` when a certainty claim is made
  with no quantified uncertainty.

## 6. Bounded rewrite (`rewrite_target`)

When `escalation_label=1`, write a `rewrite_target` that the evidence
**actually supports**. The rewrite must:

1. Stay within the supported scope (cap each dim at `support_tiers`).
2. Keep the same subject/system as the original claim.
3. Be falsifiable — state the measured numbers, not a vague softening.
4. Not introduce new claims the evidence does not address.

Bad: `"The system is somewhat reliable."` (vague, no anchor).
Good: `"The IDS achieves TPR=0.73 and FPR=0.18 on 200 attack traces;
zero false positives is not supported by the evaluation."`

Leave `rewrite_target` blank only when no defensible rewrite exists
(e.g. the evidence is entirely off-topic).

## 7. `evidence_gap_labels` trigger rules

`evidence_gap_labels` lists which evidence dimensions are missing
relative to the claim's demands. Trigger rules (one label per missing
dim):

| Label | Trigger |
|-------|---------|
| `coverage_missing` | `scope` claim ≥ 2 but evidence covers only a subset. |
| `causal_missing` | `causal` claim ≥ 2 but no counterfactual/control. |
| `action_missing` | `action` claim ≥ 2 but only offline metrics. |
| `uncertainty_missing` | `certainty` claim ≥ 2 but no quantified uncertainty. |
| `traceability_missing` | No provenance trail (citations/logs/code). |
| `boundary_missing` | Evidence over-generalizes beyond its stated domain. |

For pilot, every overclaim row MUST fill `evidence_gap_labels` (a
schema violation otherwise). Empty list is valid only when
`escalation_label=0`.

## 8. Annotating `source_type`

Three source types share a `logical_sample_id`; all three must stay in
the same split (see `build_paper_splits.py`).

- **`oracle`**: human annotator with full access to claim + evidence +
  source artifacts. `evidence_confidence` = 1.0. This is the gold
  standard.
- **`extracted`**: annotator (or pipeline) sees ONLY `evidence_text`,
  no claim-side labels. Produces `evidence_vector` /
  `evidence_confidence` from the text. `claim_tiers` /
  `support_tiers` / `escalation_label` are inherited from the oracle
  row of the same `logical_sample_id` — do NOT re-annotate them. This
  measures extraction quality.
- **`confidence_aware`**: extends `extracted` with a per-dimension
  confidence lower-bound. The annotator records both a point estimate
  and an interval `[low, high]` for each evidence dim. `claim_tiers` /
  `support_tiers` are again inherited from oracle.

Never let the extracted/confidence_aware annotator see the oracle
`support_tiers` — that would leak the gold answer into the extraction
measurement.

## 9. Adjudication workflow

When two annotators disagree, the lead adjudicates and records:

- `disagreement_fields`: dotted paths that differed (e.g.
  `claim_tiers.scope`, `support_tiers.scope`).
- `adjudicated_by`: lead annotator id.
- `adjudication_notes`: one-line rationale.
- `final_record_patch`: the resolved values.
- `adjudicated: true` on the final record (so
  `compute_annotation_agreement.py` counts it in `adjudication_rate`).

See `scripts/adjudicate_annotations.py`.

## 10. Stage-wise annotation structure

Raw annotator judgments are stored under stage blocks (not flattened
onto the gold record). Each annotation file row carries:

- `stage_1_claim`: `claim_family`, `claim_tiers`.
- `stage_2_evidence`: `support_tiers`, `evidence_available`.
- `stage_3_labels`: `contradiction_label`, `escalation_label`,
  `escalation_type`.
- `stage_4_rewrite`: `rewrite_target`, `evidence_gap_labels`.

`compute_annotation_agreement.py --annotations a.jsonl b.jsonl`
computes stage-wise agreement (weighted kappa per dim, Cohen's kappa
per binary label, adjudication rate) from these blocks.
