# V3.17 Confidential Lightweight — One-Page Status Card

> **Mandatory framing.** This is a **controlled silver diagnostic study**, not a gold benchmark. The system is a second-stage review queue generator, not a standalone detector. **Not SOTA. Not an automatic peer reviewer. Not a validated general detector.**

Generated: 2026-07-08
Mainline: V3.17 Confidential Lightweight
Remote HEAD: `adcf485eeb9621fbd828ec7741ab508f66c8f9eb`

---

## Project status

**READY WITH LIMITATIONS.** Final perfect-state gate passes with two documented warnings (human audit staged-not-executed; internal-file high-risk findings excluded from release bundle). No FAIL, no BLOCKED. Submission manuscript frozen (v2 Final Freeze).

## Final gate counts

| Metric | Count |
|---|---|
| Total checks | 44 |
| PASS | 42 |
| WARNING | 2 |
| BLOCKED | 0 |
| FAIL | 0 |

- Warning 6.4 — Human audit summary missing (protocol staged, not executed).
- Warning 9.1 — Redteam high-risk in internal scoring files (3 findings, all `forbidden_sorting_field` in internal-only files; release-safety gate PASS confirms exclusion from public bundle).

[Source: reports/final_perfect_state_gate_v3_17.md]

## Main contribution

A deterministic, no-API, no-training **evidence canonicalization** method that bridges the **retrieval-to-screening format shift** between long BM25 PDF chunks and short screening-format evidence, plus a conservative precision-optimized review queue that augments human adjudication. Under the confidential / no-API / no-training / silver-diagnostic constraint set, deterministic canonicalization is Pareto-optimal against learned alternatives.

## Dataset status

- **SimClaim Strict Silver Diagnostic Set v1** — 444 rows, 111 groups, 4 balanced labels, 6 domains.
- `human_audited = False` for all 444 rows. `gold_label` never populated. `silver_label_source = candidate_label_guess`.
- SHA256 `13d6c66171cf54e1a456d5ef8674f00f91939aa79a60f0c65066f2a3ebe0a812`, locked.
- **Controlled silver diagnostic, not gold, not human-audited.**

[Source: docs/dataset_version_lock_v3_17.md]

## Key results

| Result | Value | Source |
|---|---|---|
| BM25 chunk oracle match rate | 0.991 | experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json |
| BM25 chunk recall@10 | 0.980 | experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_metrics_bm25.json |
| BM25 sentence recall@10 | 0.948 | experiments/bm25_sentence_retrieval_v1/oracle_recall_summary.json |
| Canonicalizer oracle_recall (best) | 0.387 (9x over raw 0.043) | experiments/canonicalizer_ablation_v1/selector_metrics_summary.csv |
| R4 strong_F1 (frozen router) | 0.4503, 95% CI [0.4086, 0.4833] | experiments/metric_robustness_v1/classification_metrics_with_ci.csv |
| Format-shift canonicalized strong_F1 | 0.4615 (+0.186 over raw BM25) | experiments/format_shift_ablation_v1/format_shift_metrics.csv |
| Format-shift R4 eval status | **resolved** (offline sklearn 1.9.0) | experiments/format_shift_ablation_v1/r4_eval_blocked.json |
| Review queue precision@20 (best) | 0.45 (+0.10 over baseline) | experiments/canonicalized_risk_ranking_v1/risk_ranking_gate.json |
| Review queue viability | second-stage only (standalone=false) | experiments/canonicalized_review_queue_v1/canonicalized_review_queue_gate.json |
| Leakage audit | PASS (12 checks) | experiments/leakage_audit_v1/audit_summary.md |
| Claim-only strong_F1 / R4 ratio | 0.2448 / 0.5436 (below 0.8 warning) | experiments/leakage_audit_v1/claim_only_baseline.json |

## Human audit status

**STAGED, NOT EXECUTED.** A 111-candidate targeted audit packet exists (`data/private_audit/v3_17_audit_packet/audit_packet_private.csv`, gitignored) across 6 domains with a two-annotator protocol, but no human annotator has filled `auditor_label`. No human-audited benchmark results are reported. This is Final Gate WARNING 6.4.

[Source: docs/human_audit_protocol_v1.md; data/audit_templates/human_audit_queue_seed_v1_redacted.csv]

## Release safety status

- **Release safety gate: PASS.** 54 artifacts tracked; 46 safe-to-release; 8 private-sensitive (raw text); 1 genuinely blocked (BM25 sentence corpus needs PDF corpus).
- Public release bundle: 254 files, red-team PASS (high_risk=0 in bundle scope).
- No PDF, no raw claim/evidence text, no pkl/joblib/npz/docx/xlsx, no private audit CSV in bundle.

[Source: reports/release_safety_manifest_v3_17.json; release_bundles/v3_17_confidential_public/REDACTION_REPORT.json]

## Known limitations

1. Silver labels (not gold); results are diagnostic, not benchmark-level.
2. Human audit not executed (staged only).
3. Six domains only; not a validated general detector across all simulation-claim domains.
4. Format-shift R4 eval completed offline with project-local `.venv` sklearn 1.9.0 (frozen R4 artifacts); diagnostic, not benchmark-level.
5. Review queue is second-stage only; not a standalone detector and does not replace adjudication.
6. Confidentiality is a deployment constraint, not the empirical contribution.

## What can be claimed

- A controlled silver diagnostic study of retrieval-to-screening format shift.
- Deterministic evidence canonicalization improves oracle_recall 9x and produces screening-format evidence.
- Format-shift R4 evaluation resolved offline; canonicalized strong_F1 close to oracle upper bound.
- A conservative review queue augments human review as a second-stage prioritizer.
- A 12-check leakage audit found no significant shortcuts.
- Pareto-optimal deterministic methods under the no-API / no-training / silver-diagnostic constraint set.

## What cannot be claimed

- **Not a gold benchmark.** (silver labels, not human-audited)
- **Not SOTA** on simulation-claim screening.
- **Not an automatic peer reviewer.**
- **Not a validated general detector.**
- **Not full CESE-OCN neural architecture validation.**
- No completed human audit / no human-audited dataset claim.
- No claim that R4 is shortcut-free; only that the leakage audit passed its 12 checks.
- No claim that format-shift metrics are validated (they are diagnostic, silver-label).

## Next recommended action

1. Recruit a human annotator to complete `audit_packet_private.csv` (111 candidates), then run `summarize_human_audit_v1.py` and re-run the final gate to clear WARNING 6.4.
2. If a human audit is completed, integrate results into the manuscript (Task Pack 4) without gold-benchmark wording.
3. Otherwise, the project is ready for submission **with documented limitations**.
