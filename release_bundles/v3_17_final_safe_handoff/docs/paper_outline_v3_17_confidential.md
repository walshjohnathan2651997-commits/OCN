# Paper Outline — V3.17 Confidential Lightweight

**Authority:** This outline freezes the paper structure for V3.17. All
section titles, RQ numbering, contribution claims, and result
narratives are fixed here. Any change requires updating this document
and the result narrative freeze.

**Scope:** V3.17 Confidential Lightweight mainline only. Does not
apply to legacy V2 pilot or future full CESE-OCN neural architecture.

---

## Title candidates

1. **Local Evidence Canonicalization for Confidential Simulation-Claim Review Queues**
2. **Retrieval-to-Screening Format Shift in Local PDF Claim Review**

Candidate 1 is preferred (emphasizes the method and the setting).
Candidate 2 is acceptable (emphasizes the problem).

---

## Abstract structure

The abstract must contain, in order:

1. **Problem:** Simulation-claim review requires screening claims
   against source PDF evidence, but retrieved PDF chunks are in the
   wrong format for downstream screening models.
2. **Confidential/no-API setting:** The deployment scenario prohibits
   API egress, network access, and model training — all processing
   must be local and auditable.
3. **Controlled silver diagnostic:** We evaluate on a 444-candidate
   controlled silver diagnostic set (111 groups × 4 labels), not a
   gold benchmark.
4. **Retrieval-to-screening format shift:** We identify the format
   mismatch between raw PDF chunks (long, noisy) and screening-format
   evidence (short, clean) as a key failure mode.
5. **Evidence canonicalization:** We propose deterministic evidence
   canonicalization as a no-API bridge, improving oracle recall from
   0.043 (raw chunks) to 0.387 (best canonicalizer).
6. **Second-stage review queue:** We build a conservative review queue
   (precision@20 = 0.45) that augments human review without claiming
   to replace it.
7. **Limitations:** Silver labels, no human audit, six domains only,
   not a general detector.

The abstract must **not** contain: gold benchmark, SOTA, automatic
peer review, general detector.

See: `paper_assets/v3_17_confidential/abstract_draft.md`

---

## Research questions

| RQ | Question | Section |
|---|---|---|
| RQ1 | Can local PDF retrieval recover source-traceable evidence? | §4.1 |
| RQ2 | How much does raw PDF chunk format hurt downstream screening? | §4.2 |
| RQ3 | Does canonicalization restore screening-compatible evidence? | §4.3 |
| RQ4 | Which canonicalizer variant is most robust? | §4.3 |
| RQ5 | Can conservative ranking support human review queues? | §4.4 |
| RQ6 | Are results robust to leakage/shortcut audits? | §4.5 |
| RQ7 | What is the complexity-vs-utility tradeoff? | §4.6 |

---

## Section outline

### §1 Introduction

- Simulation-claim review problem: claims about autonomous driving,
  policy simulation, digital twin, cyber defense, MARL, robotics must
  be checked against source PDFs.
- Confidential setting: no API, no network, no training, no data
  egress. All processing local and auditable.
- Contribution: identify retrieval-to-screening format shift; propose
  deterministic canonicalization as no-API bridge; evaluate frozen R4
  screening + conservative queueing on controlled silver diagnostic;
  provide leakage/error/metric/release audits.
- **Not** a gold benchmark, SOTA detector, automatic peer reviewer, or
  general detector.

See: `paper_assets/v3_17_confidential/contribution_bullets.md`

### §2 Related Work

- Fact-checking and claim verification (FEVER, SciFact, VitaminC) —
  note these use external curated benchmarks and often API-based models.
- Information retrieval for evidence finding — BM25, dense retrieval.
  Note: dense retrieval requires model training/API; BM25 is auditable.
- Canonicalization in NLP — text normalization, sentence extraction.
  Note: prior work targets readability, not screening-format bridge.
- Review queues in clinical/legal NLP — triage, prioritization.
  Note: prior work assumes gold labels; we use silver labels.

### §3 Methods

#### §3.1 Dataset

- SimClaim Strict Silver Diagnostic Set v1: 444 candidates, 111 groups,
  4 labels (supported, mild_scope_overclaim,
  strong_action_overclaim, contradiction_candidate).
- 6 domains: autonomous_driving (140), policy_simulation (84),
  digital_twin (68), cyber_defense (64), marl (52), robotics (36).
- `human_audited=False` for all 444 rows; `gold_label` and
  `final_label` empty; `silver_label_source=candidate_label_guess`.
- **Not** a gold benchmark, not human-audited, not natural prevalence.
- SHA256: `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812`

See: `docs/dataset_version_lock_v3_17.md`

#### §3.2 Pipeline

1. PDF sentence corpus (local extraction, no OCR by default)
2. BM25 retrieval (claim_text query only; oracle/evidence for eval only)
3. Evidence canonicalization (deterministic selectors, no training)
4. Frozen R4 screening (no threshold tuning, no retraining)
5. Conservative risk ranking (G_conservative_precision variant)
6. Review queue output (top-100 for human review)

#### §3.3 Canonicalization

- 8 selector variants: raw_top1_chunk, cleaned_top1_chunk,
  first_sentence_top1, best_sentence_top1_overlap,
  best_sentence_top5_overlap, three_sentence_window_top5,
  sentence_bm25_top1 (blocked), window_bm25_top1 (blocked).
- Selection uses only claim_text and retrieved chunks; never uses
  oracle evidence, labels, or human_audited flags.

#### §3.4 R4 Screening (frozen)

- Frozen R4 routing with fixed thresholds (t_contra, t_strong, t_svm).
- No threshold tuning on test; no retraining on silver labels.
- R4 is an offline, auditable, second-stage strong_action screening
  router — **not** a standalone detector.

#### §3.5 Risk Ranking

- 8 ranking variants (A-H) evaluated on precision@k and recall@k.
- G_conservative_precision: filter by strong_action_flag + p_contra
  guard, then rank by p_strong - entropy.

### §4 Results

#### §4.1 RQ1: PDF retrieval

- BM25 recall@1 = 0.716, recall@5 = 0.973, recall@10 = 0.980, MRR = 0.826.
- Oracle match rate = 0.991.
- PDF coverage = 1.0 (69/69 PDFs found).
- Source: `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json`
- **Blocked:** sentence/window BM25 on real data (missing PDF corpus).
  Toy results show sentence-level outperforms window-level.

#### §4.2 RQ2: Format shift hurts

- raw_top1_chunk oracle_recall = 0.043 (only 4.3% match oracle).
- 91% of raw chunks are >60 words (too long for screening format).
- Source: `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`

#### §4.3 RQ3 + RQ4: Canonicalization

- best_sentence_top5_overlap: oracle_recall = 0.387 (9x improvement
  over raw_top1_chunk = 0.043), mean_overlap = 0.524.
- 0% of selected evidence is >60 words (vs 91% for raw chunks).
- Selector ranking by oracle_recall:
  1. best_sentence_top5_overlap: 0.387
  2. best_sentence_top1_overlap: 0.221
  3. three_sentence_window_top5: 0.203
  4. raw_top1_chunk: 0.043
  5. first_sentence_top1: 0.027
  6. sentence_bm25_top1: BLOCKED (missing PDF corpus)
  7. window_bm25_top1: BLOCKED (missing PDF corpus)
- Source: `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv`
- **Blocked:** format-shift R4 eval (sklearn version mismatch).
  Variant inputs generated (3552 rows, 8 variants × 444 candidates).

#### §4.4 RQ5: Conservative ranking

- G_conservative_precision: precision@20 = 0.45 (best), recall@100 = 0.330.
- Baseline (A_flag_only): precision@20 = 0.35, recall@100 = 0.330.
- Queue metrics: precision@100 = 0.37, recall@100 = 0.339.
- Frozen R4: strong_F1 = 0.4503, 95% CI [0.4086, 0.4833].
- Source: `experiments/canonicalized_risk_ranking_v1/risk_ranking_results_by_variant.csv`,
  `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`

#### §4.5 RQ6: Leakage audit

- 12 checks: 11 PASS + 1 SKIP = overall PASS.
- Claim-only strong_F1 = 0.2448 (ratio to R4 = 0.5436, below 0.8 WARNING).
- Shuffled evidence: correct/shuffled ratio = 45.94x.
- Cue words: max_cue_ratio = 1.6075 (below threshold).
- Group split integrity: cross_groups = 0.
- Source: `experiments/leakage_audit_v1/audit_summary.md`

#### §4.6 RQ7: Complexity-vs-utility

- Deterministic canonicalization: Pareto optimal (privacy=1,
  auditability=1, simplicity=1, reproducibility=1).
- Learned selector/ranker: dominated (auditability=0.5,
  reproducibility=0.5).
- External LLM: unavailable (privacy=0).
- Source: `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
- **Caveat:** Does not prove rules generally beat learned models;
  deployment-specific tradeoff.

### §5 Error Taxonomy

- 9 error types tagged.
- Top: mild_vs_strong_boundary (38.83%), weak_selector_overlap
  (34.57%), supported_overflag (32.98%).
- Source: `experiments/error_taxonomy_v1/error_taxonomy_summary.csv`

### §6 Discussion

- Reviewer risk register: `docs/reviewer_risk_register_v3_17.md`
- Key risks: silver labels (R01), template cues (R02), no human audit
  (R06), full CESE-OCN not validated (R10).
- Safe responses prepared in `docs/reviewer_response_playbook_v3_17.md`.

### §7 Limitations

See: `paper_assets/v3_17_confidential/limitations_draft.md`

### §8 Future Work

- Full CESE-OCN neural architecture (future, not current claim).
- Human audit completion (protocol built, labels pending).
- LLM/VLM baselines if confidentiality constraints relaxed.
- Real PDF corpus for sentence/window BM25.

---

## Tables (paper assets)

| Table | Title | Source |
|---|---|---|
| Table 1 | Dataset summary | `paper_assets/v3_17_confidential/tables/table1_dataset_summary.md` |
| Table 2 | Retrieval recall | `paper_assets/v3_17_confidential/tables/table2_retrieval_recall.md` |
| Table 3 | Format-shift ablation | `paper_assets/v3_17_confidential/tables/table3_format_shift_ablation.md` |
| Table 4 | Canonicalizer ablation | `paper_assets/v3_17_confidential/tables/table4_canonicalizer_ablation.md` |
| Table 5 | Review queue | `paper_assets/v3_17_confidential/tables/table5_review_queue.md` |
| Table 6 | Leakage audit | `paper_assets/v3_17_confidential/tables/table6_leakage_audit.md` |
| Table 7 | Complexity-utility | `paper_assets/v3_17_confidential/tables/table7_complexity_utility.md` |
| Table 8 | Human audit (if available) | `paper_assets/v3_17_confidential/tables/table8_human_audit_if_available.md` |

## Figures

- Figure 1: Pipeline ASCII diagram — `paper_assets/v3_17_confidential/figures/pipeline_ascii.md`
- Figure 2: SmartQueue bucket counts — `paper_assets/v3_17_confidential/figures/smartqueue_bucket_counts.csv`
- Figure 3: Queue precision-recall — `paper_assets/v3_17_confidential/figures/queue_precision_recall_data.csv`
- Figure 4: Format-shift bar — `paper_assets/v3_17_confidential/figures/format_shift_bar_data.csv`

---

## Forbidden claims (do NOT make)

- "gold benchmark" — dataset is silver
- "human-audited benchmark" — human_audited=False for all rows
- "SOTA" / "state-of-the-art" — not SOTA
- "automatic peer reviewer" — not automatic peer review
- "validated general detector" — six domains only
- "full CESE-OCN validated" — future architecture
- "outperforms LLMs" — no LLM baseline; deployment-specific tradeoff

## Required caveats

Every results section must include:

> We use a source-traceable controlled silver diagnostic set. The
> labels are not gold or human-audited, and results should not be
> interpreted as benchmark-level model validation.
