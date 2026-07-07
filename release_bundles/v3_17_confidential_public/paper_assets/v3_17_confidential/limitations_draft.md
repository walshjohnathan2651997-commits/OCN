# Limitations Draft — V3.17 Confidential Lightweight

**Authority:** This is the frozen limitations section for V3.17. Each
limitation is concrete, traceable to a file or design choice, and
paired with the safe wording that must accompany it in the paper.

---

## L1 — Silver labels, not gold

- **Statement:** The 444-candidate dataset is a source-traceable
  controlled silver diagnostic. `human_audited=False` for all 444
  rows; `gold_label` and `final_label` are empty;
  `silver_label_source=candidate_label_guess` for all rows.
- **Source:** `docs/dataset_version_lock_v3_17.md`,
  `data/strict_silver_diagnostic_v1/strict_silver_diagnostic_v1.csv`
  (SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812`)
- **Implication:** All quantitative results (strong_F1, precision@k,
  oracle_recall) are diagnostic signals, not benchmark-level model
  validation.
- **Safe wording:** "We use a source-traceable controlled silver
  diagnostic set. The labels are not gold or human-audited, and
  results should not be interpreted as benchmark-level model
  validation."

## L2 — No completed human audit

- **Statement:** A small targeted human audit protocol exists
  (`docs/human_audit_protocol_v1.md`), an audit template is built
  (`data/audit_templates/human_audit_template.csv`), and 111 audit
  seeds are queued. No adjudication has been completed and no
  agreement metrics are available.
- **Source:** `docs/human_audit_protocol_v1.md`,
  `data/audit_templates/human_audit_template.csv`
- **Implication:** Silver labels cannot be upgraded to gold. Any
  future human audit must use the established protocol and report
  inter-annotator agreement before any gold-level claim is made.
- **Safe wording:** "A small targeted human audit protocol exists
  but has not been completed; the dataset remains silver-label."

## L3 — Six domains only

- **Statement:** The diagnostic covers six domains: autonomous_driving
  (140 candidates), policy_simulation (84), digital_twin (68),
  cyber_defense (64), marl (52), robotics (36).
- **Source:** `docs/dataset_version_lock_v3_17.md`
- **Implication:** The system is not a validated general detector.
  Generalization to other domains (e.g., biomedical, legal, financial
  simulation) is not supported by the current data.
- **Safe wording:** "The diagnostic covers six simulation-adjacent
  domains; generalization to other domains is not supported by the
  current data."

## L4 — Blocked experiments

- **Statement:** Two P0 experiments are blocked:
  - Sentence/window BM25 on the real PDF corpus — blocked by
    `missing_pdf_corpus` (`data/pdf_corpus_v1/sentences.jsonl` not
    generated in this run).
  - Format-shift R4 evaluation — blocked by
    `sklearn_version_mismatch` (R4 frozen artifacts pickled with
    scikit-learn 1.9.0; current environment has 1.4.1.post1).
- **Source:** `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json`,
  `experiments/format_shift_ablation_v1/r4_eval_blocked.json`
- **Implication:** The format-shift finding is supported by
  canonicalizer ablation (oracle_recall), not by end-to-end R4
  evaluation on canonicalized vs. raw evidence.
- **Safe wording:** "End-to-end format-shift R4 evaluation is blocked
  by an environment version mismatch; the format-shift finding is
  supported by canonicalizer ablation oracle recall, not by direct
  R4 F1 comparison."

## L5 — No LLM / VLM baseline

- **Statement:** No LLM or VLM baseline was run. The
  `external_llm_baseline` method in the complexity-vs-utility
  ablation is marked `unavailable` with `privacy=0` because LLM APIs
  are prohibited under the confidential / no-API constraint.
- **Source:** `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- **Implication:** We do not claim that deterministic canonicalization
  outperforms LLMs. The Pareto result is deployment-specific
  (confidential / no-API / no-training / silver diagnostic).
- **Safe wording:** "Under confidential / no-API / no-training /
  silver-diagnostic constraints, deterministic canonicalization has a
  favorable tradeoff; this does not generalize to settings with API
  access or training budget, and no LLM baseline was run."

## L6 — Second-stage queue, not standalone detector

- **Statement:** The conservative review queue produces a ranked
  top-100 list for human reviewers. At realistic prevalence (1%),
  FP/TP = 66.82, which is unusable as a standalone detector.
- **Source:** `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv`,
  `docs/reviewer_risk_register_v3_17.md` (R07)
- **Implication:** The queue augments human review; it does not
  replace adjudication.
- **Safe wording:** "The pipeline produces a second-stage review
  queue that augments human review; it is not a standalone detector
  and does not replace human adjudication."

## L7 — Frozen R4, no threshold tuning on test

- **Statement:** R4 thresholds (t_contra, t_strong, t_svm) are
  frozen. No threshold tuning on the test split; no retraining on
  silver labels. The threshold provenance specifies `source_split=dev`
  (not test).
- **Source:** `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`
- **Implication:** R4 F1 is a frozen-router evaluation, not an
  optimized-router evaluation. Tuning on test would be leakage.
- **Safe wording:** "R4 thresholds are frozen and were not tuned on
  the test split; the F1 is a frozen-router evaluation."

## L8 — Confidential constraint blocks reproducibility of some inputs

- **Statement:** Raw claim text, evidence text, and source PDFs are
  confidential and are excluded from the public release bundle. The
  public bundle includes redacted summaries, hash-only identifiers,
  and aggregate metrics.
- **Source:** `release_bundles/v3_17_confidential_public/`,
  `reports/confidentiality_redteam_scan_v3_17.md`
- **Implication:** External reviewers cannot fully reproduce the
  end-to-end pipeline without access to the confidential inputs.
  Schema validation, toy demo, and redteam scan are provided as
  reproducibility proxies.
- **Safe wording:** "Raw claim and evidence text is confidential and
  excluded from the public release; schema validation, a toy demo,
  and a redteam scan are provided as reproducibility proxies."

## L9 — Full CESE-OCN not validated

- **Statement:** V3.17 confidential lightweight is a scoped subset of
  CESE-OCN. The full CESE-OCN neural architecture (multi-stage
  shared-threshold routing) is a future architecture, not a current
  claim. There is no full shared-threshold CESE-OCN validation in
  V3.17.
- **Source:** `docs/reviewer_risk_register_v3_17.md` (R10),
  `docs/safe_claims_dictionary_v3_17.md` (U5)
- **Implication:** We do not claim CESE-OCN is validated. We claim
  only that the V3.17 scoped subset runs end-to-end on the silver
  diagnostic.
- **Safe wording:** "V3.17 confidential lightweight is a scoped
  subset of CESE-OCN, not a full validation of the CESE-OCN neural
  architecture."

---

## Required caveat (must appear at the end of the Limitations section)

> We use a source-traceable controlled silver diagnostic set. The
> labels are not gold or human-audited, and results should not be
> interpreted as benchmark-level model validation. The system is not
> a validated general detector, not SOTA, and not an automatic peer
> reviewer.
