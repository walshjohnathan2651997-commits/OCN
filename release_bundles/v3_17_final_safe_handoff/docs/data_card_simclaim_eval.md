# Data Card — `simclaim_eval`

> **Legacy data card.** This card describes the older `simclaim_eval`
> dataset, which is **not** the V3.17 Confidential Lightweight mainline
> dataset. The current mainline uses `strict_silver_max_v1` (444
> candidates, `human_audited=False` for all rows, controlled silver
> diagnostic — **not** human-audited, **not** gold). This card is
> retained for historical reference only.

> **Scope**: this card describes the **`simclaim_eval`** dataset, the
> evaluation benchmark accompanying the CESE-OCN paper. The pilot
> diagnostic dataset (`data/pilot.jsonl`, 20 records) is a small-scale
> smoke test of the same schema and is **NOT** the paper dataset; it
> must not be reported as paper results.

---

## 1. Dataset purpose

`simclaim_eval` is a benchmark for auditing whether an LLM-generated
**technical claim** is over-claimed relative to the **evidence** it
cites. Each record pairs a claim with evidence and a human-audited
ordinal tier structure across four claim dimensions
(`scope`, `causal`, `action`, `certainty`) and matching support tiers.

The benchmark supports:

- training and evaluating the CESE-OCN ordinal calibrator;
- comparing against rule / NLI / RAG-LLM / structured LLM judge baselines;
- measuring calibration, monotonicity, and truncation safety under
  confidence-lower-bound perturbations;
- error analysis by dimension, source mode, domain, and held-out split.

> **CESE-OCN audits support capacity; it does NOT replace domain expert
> review, causal identification, or deployment decision analysis.**

---

## 2. Domains

The schema currently accepts the following domains; every paper table and annotation export must use these exact values:

- `controlled_simulation` — controlled simulation claims and evidence.
- `cyber_defense` — cyber-defense and autonomous-defense claims.
- `academic_claim` — claims distilled from academic or technical reports.
- `wargaming` — simulation and wargaming scenarios.
- `digital_twin` — digital-twin scenarios and deployment claims.

Each record carries a `domain` field. The `test_domain_heldout` adversarial split holds out one or more domains entirely from train to measure cross-domain generalization.

---

## 3. Claim families

Claims are typed by the kind of over-claim risk they carry:

| `claim_family` | Description |
|-----------------|-------------|
| `autonomous_cyber_defense_marl` | Canonical clean-v2 family for autonomous cyber-defense MARL claims. |
| `cyber_acd_gym` | Canonical clean-v2 family for Cyber ACD Gym claims. |
| `cooperative_ai_generalization` | Canonical clean-v2 family for cooperative-AI generalization claims. |
| `cooperative_marl_benchmark` | Canonical clean-v2 family for cooperative-MARL benchmark claims. |
| `descriptive`, `scope`, `robustness`, `causal`, `recommendation`, `certainty`, `falsehood`, `vague` | Legacy families retained for pilot and backward-compatible data. |

`escalation_label = 1` iff `claim_tiers[dim] > support_tiers[dim]` for
any `dim`. `escalation_type` lists the dimensions that escalated.

---

## 4. Source modes

Each record is annotated with `source_type` ∈
{`oracle`, `extracted`, `confidence_aware`}:

- **`oracle`** — evidence and tiers come from the gold annotation
  (perfect extraction). Upper bound on model performance.
- **`extracted`** — evidence is extracted by the system's evidence
  retriever / parser under a fixed pipeline (realistic noise).
- **`confidence_aware`** — evidence is extracted AND a confidence
  lower-bound vector is provided; the model must remain safe under the
  lower bound. This is the deployment-realistic condition.

The `oracle` / `extracted` / `confidence_aware` triple on the **same
model and same samples** is required for paper_full (see
`scripts/run_oracle_extracted_comparison.py`).

---

## 5. Annotation stages

Annotation follows a four-stage pipeline so that each stage is auditable
independently (see [docs/annotation_guide.md](annotation_guide.md) and
[schemas/pilot_annotation_minimal_schema.md](../schemas/pilot_annotation_minimal_schema.md)):

1. **`stage_1_claim`** — `claim_family` and `claim_tiers` (0–4 per dim).
2. **`stage_2_evidence`** — `support_tiers` (0–4 per dim) and the
   `evidence_available` feature flags (`coverage`, `boundary`,
   `uncertainty`).
3. **`stage_3_labels`** — `contradiction_label` (factual refutation)
   and `escalation_label` / `escalation_type` (ordinal over-claim).
   Contradiction and escalation are **separate** judgments.
4. **`stage_4_rewrite`** — `rewrite_target` (bounded rewrite that
   aligns the claim with the evidence) and `evidence_gap_labels`
   (coverage_missing / boundary_missing / uncertainty_missing /
   causal_id_missing).

> **Core principle**: factual non-contradiction does NOT imply ordinal
> support. Evidence that merely fails to refute a tier-4 claim still
> yields `support_tiers = 0`/`1` if it provides no positive backing.

---

## 6. Agreement statistics

Inter-annotator agreement is reported **stage-wise** in
`outputs/paper/agreement_report.json` (pilot: `outputs/pilot/agreement_report.json`):

- `stage_1_claim_tiers.weighted_kappa_by_dim` — per-dimension quadratic-weighted kappa.
- `stage_1_claim_tiers.adjacent_agreement_by_dim` — adjacent-tier agreement rate.
- `stage_2_support_tiers.weighted_kappa_by_dim` and `feature_level_f1`.
- `stage_3_labels.cohen_kappa_escalation` and `cohen_kappa_contradiction`
  (reported **separately** — escalation and contradiction are distinct
  constructs and must not be merged).
- `stage_3_labels.adjudication_rate` — fraction of double-annotated
  items sent to adjudication.
- `stage_4_rewrite.rewrite_present_rate` and `gap_label_f1`.

Paper_full blocking thresholds (see `scripts/audit_dataset.py`):

- `n_double_annotated >= 50`
- `min(weighted_kappa_by_dim) >= 0.45`
- `cohen_kappa_escalation >= 0.5`
- `adjudication_rate` present (adjudication workflow completed).

Pilot may fall below these thresholds but only emits warnings.

---

## 7. Known limitations

- **Synthetic + paraphrased claims**: claims are synthetic or
  paraphrased from public technical reports. They do not cover the full
  distribution of real-world LLM outputs; generalization to
  out-of-distribution claim styles is not guaranteed.
- **Causal identification**: `causal` tier 4 ("decisive") requires
  causal identification, which the benchmark approximates via control
  narration. The benchmark does NOT perform real causal inference;
  causal claims marked tier 4 are best-effort labels, not causal
  identifications.
- **Extraction noise**: `extracted` and `confidence_aware` source modes
  inherit noise from the evidence retriever. A model that performs
  better on `oracle` than `extracted` is partly measuring extraction
  quality, not only calibration.
- **Graph CESE**: graph-structured evidence is an extension and is NOT
  part of the main results unless `scripts/check_graph_claims.py` passes
  all six gates (real graph data, non-synthetic relation vocab,
  relation ablation, test evaluation, valid metrics, beats vector CESE
  on a pre-registered metric).
- **Held-out splits**: `test_template_heldout` and `test_domain_heldout`
  measure specific generalization axes; they do not certify
  deployment-ready robustness.
- **Annotation scope**: human auditors label claim/support tiers and
  labels; they do NOT verify the real-world truth of the underlying
  technical reports.

---

## 8. License

- **Dataset**: released under a permissive license for research use
  (CC-BY-4.0). See `LICENSE` for the authoritative text.
- **Code**: see repository `LICENSE`.
- Third-party model outputs used as raw material (where applicable)
  remain under their original licenses; only the audit annotations and
  schema are released under CC-BY-4.0.

---

## 9. Intended use

- Research on calibrated ordinal claim-evidence auditing.
- Benchmarking LLM-output factuality / over-claim detection methods that
  operate on structured claim dimensions.
- Studying calibration, monotonicity, and truncation safety in
  support-estimation models.

---

## 10. Out-of-scope use

- **NOT** a deployment decision system. CESE-OCN outputs are audit
  signals, not deployment verdicts.
- **NOT** a replacement for domain expert review. High-stakes decisions
  require human review.
- **NOT** a causal identification tool. The `causal` tier is a label of
  the claim's causal strength, not a causal effect estimate.
- **NOT** a general-purpose factuality checker. It operates on the four
  claim dimensions and eight evidence dimensions defined in the schema.
- **NOT** certified for cross-domain deployment without re-fitting the
  shared-threshold calibrator on a dev split from the target domain.

---

## 11. Ethical considerations

- **No personal data**: claims are synthetic or paraphrased from public
  technical reports; no personal data is stored.
- **No user-generated content**: the benchmark does not contain
  end-user prompts or private conversations.
- **Annotator welfare**: annotators were provided with a written guide
  (`docs/annotation_guide.md`), worked in fixed sessions, and were
  compensated at or above local fair-rate. Adjudication followed a
  fixed protocol documented in the paper.
- **Dual-use**: the benchmark could be used to evade detection of
  over-claiming. We release it under a research-use license and document
  this risk; we do not provide evasion tooling.
- **Audit, not verdict**: re-iterating the core boundary —
  > **CESE-OCN audits support capacity; it does not replace domain
  > expert review, causal identification, or deployment decision
  > analysis.**
