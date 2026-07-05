# Updated Project Mainline Summary (Post-Realignment v1)

**Date:** 2026-07-05
**Realignment basis:** V3.17 baseline frozen metrics + V3.18 intelligent upgrade negative result + canonicalized R4 evidence-sufficiency pipeline
**Supersedes:** `project_synthesis/current_project_state_consolidation_clean_v1/current_mainline_assessment.md` (which anchored on V3.15 hierarchical taxonomy)

---

## 1. Current Mainline (Authoritative)

The current mainline is the **offline PDF-corpus evidence-sufficiency screening framework**:

```
PDF corpus
  -> BM25 top-k retrieval
  -> evidence canonicalization (best_sentence_top5_overlap)
  -> CESE-OCN / R4 relation-specific screening (restored R4, 10 seeds, per-seed thresholds)
  -> risk ranking (G_conservative_precision)
  -> second-stage human review queue
```

This mainline is **offline, auditable, and second-stage**. It is not a general-purpose LLM reviewer, not a natural-prevalence benchmark, and not a standalone end-to-end automatic review system.

## 2. Selected Method Version

**Selected: V3.17 baseline**

- BM25 top-k retrieval over the SimClaim PDF corpus
- `best_sentence_top5_overlap` evidence canonicalization (simple overlap-based selector from top-5 BM25 chunks)
- Restored R4 screening router (10 seeds [11, 22, 33, 44, 55, 66, 77, 88, 99, 111], per-seed thresholds, majority-vote aggregation, prefer test split with dev fallback)
- `G_conservative_precision` risk ranking variant
- Second-stage review queue (top-100 prioritized candidates)

**Frozen V3.17 baseline metrics (436 eval candidates):**

| Metric | Value |
|---|---|
| strong_F1 | 0.4503 |
| strong_recall | 0.7064 |
| strong_precision | 0.3305 |
| macro_F1 | 0.3847 |
| precision@20 | 0.45 |
| recall@100 | 0.3303 |
| FP/TP @ 5% prevalence | 11.24 |
| standalone viable | false |
| second-stage viable | true |

**Raw BM25 top1 baseline (for contrast):** strong_F1 = 0.1806 — raw retrieved chunks degrade R4 screening badly.

## 3. Core Contributions (Re-aligned)

1. **Discovery: raw PDF chunks break downstream strong_action screening.** Raw BM25 top1 chunks feed R4 a strong_F1 of only 0.1806, well below the oracle-span strong_F1 of 0.4257. The format shift (metadata + length + multi-sentence concatenation) is the dominant cause, confirmed by ablation (oracle_lengthened drops strong_F1 to 0.0938).
2. **Evidence canonicalization is the retrieval-to-screening bridge.** `best_sentence_top5_overlap` canonicalization restores strong_F1 to 0.4503, a +0.2697 gain over raw BM25 top1, and is only -0.0246 below oracle span. Simple overlap-based canonicalization is robust; complex learned selectors did not improve over it (see V3.18).
3. **R4 is positioned as an offline, auditable, second-stage strong_action screening router.** R4 is not a standalone detector, not a flat 4-class best classifier, and not a competitive replacement for LLM judges overall. R4's value is targeted Level-2 strong_action screening signal at the cost of lower overall macro_F1.

## 4. V3.18 Intelligent Upgrade — Exploratory Negative Ablation

The V3.18 intelligent upgrade attempted to replace the handcrafted evidence selector and risk ranker with sklearn learned models (LogisticRegression / RandomForest / HistGradientBoosting, group-aware split).

**Result: NEGATIVE.** Both modules failed to improve over V3.17 baseline:

| Module | V3.17 baseline | V3.18 learned | Gap | Pass? |
|---|---|---|---|---|
| Evidence selector (strong_F1) | 0.4503 | 0.4444 | -0.006 | false |
| Risk ranker (precision@20) | 0.45 | 0.35 | -0.10 | false |
| Risk ranker (FP/TP @ 5%) | 11.24 | 2.00 | -9.24 (better) | partial |

`supports_v3_18_intelligent_upgrade = false`; `best_overall_method = V3.17_baseline`.

V3.18 is retained as an **exploratory negative ablation** for §VIII limitations / §IX future work. It is **NOT** the selected main method and does NOT replace V3.17.

## 5. Deprecated / Historical Versions

The following are deprecated as mainline anchors but retained for traceability:

- **V3.7 advisor-handoff paper draft** — historical paper version; not the current selected method
- **V3.15 hierarchical taxonomy revision** — paper-level interpretation; retained as paper framing, not as the empirical mainline
- **V3.16 no-gold evidence integration** — historical revision plan; superseded
- **mixed_framework_v2_frozen_r4_baseline** — historical frozen R4 baseline using frozen reference thresholds; current mainline uses restored R4 (per-seed thresholds) via `canonicalized_review_queue_v1`
- **paper_ready_mixed_framework_v2** — historical paper-ready pack; superseded by V3.17 baseline + V3.18 ablation results
- **Overnight non-API compute pipeline (Tasks A–H)** — historical diagnostic pipeline; results remain valid as supporting evidence but do not define the mainline

## 6. What This Project Is — and Is Not

**Is:**
- An offline PDF-corpus evidence-sufficiency screening framework
- A second-stage screening router (R4) for strong_action overclaim detection
- A controlled silver diagnostic test set (SimClaim, 444 pairs, 111 groups, 6 domains)
- A demonstration that evidence canonicalization is the critical bridge between BM25 retrieval and R4 screening

**Is NOT:**
- A general-purpose LLM reviewer
- A natural-prevalence benchmark
- A claim that R4 overall beats LLM (R4 macro_F1 = 0.3280 < LLM = 0.5523 on matched 100)
- A gold-validated taxonomy (gold adjudication NOT begun)
- A standalone end-to-end automatic review system
- A claim that learned selector/ranker improves the main method (V3.18 negative)

## 7. SimClaim Positioning

SimClaim is a **controlled silver diagnostic test set**:
- 444 claim-evidence pairs, 111 evidence groups, 6 domains, balanced 1:1:1:1 across four operational labels
- Uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence
- NOT a natural-prevalence corpus — the balanced design is deliberate for diagnostic pressure-testing
- Silver labels (AI-preannotated); gold adjudication pending (§VII protocol planned, NOT begun)
- `safe_as_diagnostic_set = true`; `safe_as_naturalistic = false`

## 8. Recommended Next Steps

1. **Evidence-force contrastive feature** (lowest cost, no API) — extend the V3.17 selector with contrastive NLI features (correct evidence vs forced-wrong evidence) to attempt a positive selector upgrade.
2. **Local LLM baseline pilot** (medium cost, no API) — pre-registered 120-pair pilot using a local model (e.g. Qwen-7B / Llama-3-8B) as a comparison baseline; see `project_synthesis/local_llm_baseline_feasibility_note_v1/`.
3. **Gold adjudication** (highest cost, decisive) — execute the §VII 50-pair two-layer gold pilot to resolve silver-label noise; this is the only mechanism that can validate or downgrade the Level-2 strong_action boundary.

## 9. Authoritative Output Locations

| Artifact | Path |
|---|---|
| V3.17 frozen baseline metrics | `experiments/v3_18_intelligent_upgrade_v1/v3_17_frozen_baseline_metrics.json` |
| V3.18 intelligent upgrade gate | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_gate.json` |
| V3.18 intelligent upgrade report | `experiments/v3_18_intelligent_upgrade_v1/v3_18_intelligent_upgrade_report.md` |
| Evidence canonicalization gate | `experiments/r4_evidence_canonicalization_v1/evidence_canonicalization_gate.json` |
| Canonicalized review queue gate | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` |
| Risk ranking gate | `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` |
| Realignment gate (this task) | `project_synthesis/mainline_realignment_v1/mainline_realignment_gate.json` |

## 10. Prohibitions Enforced

- no experiment data modification
- no experiment rerun
- no paper body modification
- no file deletion
- no API calls
- no network
- no silver-as-gold
- no natural-distribution claim
- no R4 retraining / threshold change
- no learned-upgrade-as-main-method claim
- no raw-BM25-solves-screening claim
