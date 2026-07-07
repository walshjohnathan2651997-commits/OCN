# Submission Claims Matrix — V3.17 Confidential Lightweight

**Manuscript:** Local Evidence Canonicalization for Offline Simulation-Claim Review Queues
**Generated:** 2026-07-07

> Every claim in the manuscript is listed below with its support status, source file, safe wording, unsafe wording (forbidden), and reviewer risk. Forbidden wording is **not** used in the manuscript; it is listed here as a guardrail.

---

## Claim matrix

| Claim | Supported? | Source file | Safe wording | Unsafe wording (forbidden) | Reviewer risk |
|---|---|---|---|---|---|
| 444-candidate controlled silver diagnostic set | Yes | `docs/dataset_version_lock_v3_17.md` | "controlled silver diagnostic set, 444 candidates, 111 groups, 4 balanced labels, not gold, not human-audited" | "gold benchmark"; "human-audited dataset" | High — reviewer may misread silver as gold |
| Retrieval-to-screening format shift exists | Yes | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` | "raw BM25 chunks achieve oracle_recall=0.043, 91% exceed 60 words; this is a format mismatch" | "retrieval is broken" | Low — empirical, well-supported |
| BM25 chunk retrieval works (recall@10=0.980) | Yes | `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json` | "BM25 chunk retrieval achieves oracle_match_rate=0.991, recall@10=0.980 on 69 PDFs / 4747 chunks" | "SOTA retrieval" | Low |
| BM25 sentence retrieval works (recall@10=0.948) | Yes | `experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json` | "sentence-level BM25 retrieval achieves recall@10=0.948, MRR=0.883 on 444 candidates" | "SOTA sentence retrieval" | Low |
| Deterministic canonicalization bridges format shift | Yes | `experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv` | "`best_sentence_top5_overlap` raises oracle_recall from 0.043 to 0.387 (9x), with 0% of selected evidence exceeding 60 words" | "canonicalization solves retrieval" | Low |
| Frozen R4 screening strong_F1=0.4503 | Yes | `experiments/metric_robustness_v1/classification_metrics_with_ci.csv` | "frozen R4 screening router achieves strong_F1=0.4503, 95% CI [0.4086, 0.4833] (group-aware bootstrap, 100 iterations)" | "validated general detector"; "SOTA detector" | High — reviewer may misread as standalone detector |
| `G_conservative_precision` precision@20=0.45 | Yes | `experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json` | "conservative precision-optimized queue achieves precision@20=0.45, recall@100=0.330" | "queue is a detector" | Medium — must emphasize second-stage |
| System is a second-stage review queue generator | Yes (by design) | `experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json` | "the system is a second-stage review queue generator, not a standalone detector; `standalone_viable=false`, `second_stage_viable=true`" | "standalone detector"; "automatic peer reviewer" | High — reviewer may misread as standalone |
| 12-check leakage audit PASS | Yes | `experiments/leakage_audit_v1/audit_summary.md` | "12 leakage checks PASS; claim-only strong_F1=0.2448 (ratio to R4=0.54, below 0.8 warning); shuffled evidence collapses 46x" | "leakage-free gold benchmark" | Low |
| 9 error types tagged | Yes | `experiments/error_taxonomy_v1/error_taxonomy_summary.csv` | "9 error types tagged; top FP cause is mild_vs_strong_boundary (38.83%)" | "comprehensive error analysis" | Low |
| Deterministic pipeline is Pareto-optimal | Yes (deployment-specific) | `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv` | "under confidential / no-API / no-training / silver-diagnostic constraints, deterministic canonicalization is Pareto-optimal against learned alternatives" | "rules generally beat learned models"; "deterministic methods are universally better" | Medium — must keep deployment-specific framing |
| PDF extraction robustness on 12 stress docs | Yes | `experiments/pdf_extraction_stress_test_v1/stress_test_summary.md` | "12 synthetic stress documents; 0 failures; engineering robustness test, not SOTA" | "SOTA PDF extraction" | Low |
| Format-shift variant construction succeeded | Yes | `experiments/format_shift_ablation_v1/format_shift_summary.json` | "8 variants × 444 candidates = 3552 rows; NLI features [3552, 7]; variant construction success" | "full format-shift evaluation completed" | Low |
| Format-shift R4 metrics blocked | Yes (blocked, documented) | `reports/format_shift_r4_eval_blocked_v3_17.md` | "Format-shift R4 metrics are not reported because frozen R4 prediction is blocked by sklearn version mismatch" | "full format-shift R4 evaluation completed"; "canonicalized format-shift metrics are validated"; "R4 format-shift result is final" | High — reviewer may misread as hidden negative result |
| Human audit protocol staged | Yes (staged, not executed) | `docs/human_audit_protocol_v1.md`; `data/audit_templates/human_audit_queue_seed_v1_redacted.csv` | "small targeted human audit protocol and seed queue prepared; audit not yet executed" | "human-audited benchmark"; "human-audited dataset"; "human-validated" | High — reviewer may misread staged as completed |
| Public release bundle safe | Yes | `reports/release_safety_manifest_v3_17.json` | "public sanitized release bundle (221 files); release_safety_gate=PASS; no raw claim/evidence/PDF text" | "release includes all data"; "no internal-only files exist" | Low |
| Redteam findings reconciled with release safety | Yes | `reports/redteam_release_reconciliation_v3_17.md` | "repo-wide redteam scan finds 3 high-risk findings in internal scoring files; all excluded from public release bundle; release_safety_gate=PASS" | "redteam scan clean"; "no internal-only findings" | Medium — must explain scope difference |

---

## Summary

- **Total claims**: 17
- **Supported**: 17 (16 supported by experiment artifacts; 1 supported by design/lock document)
- **Unsupported**: 0
- **Blocked claims**: 1 (format-shift R4 metrics — documented as permanent limitation, not reported)
- **Staged claims**: 1 (human audit — staged, not executed; manuscript reports "audit not yet executed")

## Forbidden wording (NOT used in manuscript)

- "validated general detector"
- "gold benchmark"
- "human-audited dataset"
- "human-audited benchmark"
- "human-validated"
- "SOTA" (as a positive claim)
- "automatic peer reviewer"
- "full CESE-OCN validation completed"
- "full format-shift R4 evaluation completed"
- "canonicalized format-shift metrics are validated"
- "R4 format-shift result is final"
- "rules generally beat learned models"

---

*End of claims matrix.*
