# 04 — Human Audit Pending Response (Risk D)

**Risk ID:** D
**Reviewer attack:** "You report R4 strong_F1 = 0.4503 and queue precision@20 = 0.45, but no human audit has been performed. How can any quantitative result be trusted without human-adjudicated labels?"
**Severity:** High

---

## 1. Reviewer concern

The reviewer notes that `human_audited = False` for all 444 candidates and that no `audit_agreement_summary.json` exists. The reviewer may suspect that the silver labels are being treated as de-facto gold, that the reported metrics are being interpreted as benchmark-level performance, or that the missing human audit is being hidden behind a "staged" status. The reviewer may demand either a completed human audit or an explicit downgrading of every quantitative claim to silver-conditional diagnostic status.

## 2. What we agree with

We agree that no human audit has been executed. We agree that silver labels cannot substitute for human-adjudicated gold labels. We agree that every quantitative result in the manuscript is conditional on the silver labels and may shift under human adjudication. We do not contest that a reviewer is entitled to demand that all metrics be framed as silver-conditional diagnostics, not as benchmark-level validation.

## 3. Evidence we have

- **Human audit protocol.** `docs/human_audit_protocol_v1.md` documents the planned audit: small targeted audit, 80–120 candidates, 6 sampling buckets (label-stratified, boundary, queue-top, queue-mid, queue-bottom, error-rich), two-annotator independent review followed by adjudication, agreement metrics (Cohen's κ, macro F1) reported in `audit_agreement_summary.json`.
- **Audit template.** `data/audit_templates/` contains the audit CSV template with fields for annotator ID, candidate ID, claim text reference (hash only), evidence reference (hash only), annotator label, annotator confidence, and adjudication label.
- **Seed queue.** The audit seed queue is built from the canonicalized review queue output, sampling across the 6 buckets defined in the protocol.
- **Not executed.** No `audit_agreement_summary.json` exists. No `audit_adjudication_results.csv` exists. `human_audited = False` for all 444 rows in the locked dataset. `gold_label` is empty for all 444 rows.
- **Silver label source.** `silver_label_source = candidate_label_guess` for all 444 rows; the silver labels are explicitly tagged as guesses, not adjudicated labels.
- **Final gate status.** The Final Perfect State Gate reports WARNING 6.4 (human audit staged, not executed); the gate does not upgrade this to PASS.

## 4. Evidence file

- `docs/human_audit_protocol_v1.md`
- `data/audit_templates/` (audit CSV template)
- `docs/dataset_version_lock_v3_17.md` (`human_audited=False`, `gold_label` empty)
- `reports/final_perfect_state_gate_v3_17.json` (WARNING 6.4)
- `reports/current_project_status_v3_17.md`

## 5. Safe response

We answer the reviewer as follows: the human audit is staged but not executed. The protocol, template, and seed queue are prepared; no `audit_agreement_summary.json` exists; `human_audited = False` for all 444 rows and `gold_label` is empty for all 444 rows. We do not claim any human-audited validation. Every quantitative result in the manuscript (BM25 recall, canonicalizer oracle_recall, R4 strong_F1, queue precision) is conditional on the silver labels and is framed as a diagnostic, not as benchmark-level performance. The Final Perfect State Gate explicitly records this as WARNING 6.4 and does not upgrade it to PASS.

The safe empirical conclusion is therefore narrow: **the reported metrics are silver-conditional diagnostics on a controlled silver set. They are not human-audited, not gold-level, and may shift under adjudication. The human audit protocol is prepared and the audit is the next planned step; results will be reported separately when the audit is executed.**

## 6. Remaining limitation

- No human audit has been executed; no agreement metrics (Cohen's κ, macro F1) are available.
- All silver-label metrics may shift under adjudication; some labels may flip, especially near the mild-vs-strong boundary (the largest error type in the error taxonomy at 38.83%).
- The audit protocol targets 80–120 candidates, which is a sample, not a full adjudication of all 444.
- Until the audit is executed, no quantitative result can be promoted from silver-conditional diagnostic to gold-level benchmark.
- The audit protocol assumes two-annotator independent review; if annotator agreement is low, even the audited subset may not yield a clean gold subset.

## 7. Paper text to add

> "We explicitly state that no human audit has been executed. The human audit protocol (`docs/human_audit_protocol_v1.md`) defines a small targeted audit (80–120 candidates, 6 sampling buckets, two-annotator independent review followed by adjudication, agreement metrics reported in `audit_agreement_summary.json`). The audit template and seed queue are prepared, but the audit has not been run; `human_audited = False` for all 444 candidates and `gold_label` is empty for all 444 candidates. Every quantitative result in this paper is therefore a silver-conditional diagnostic, not a gold-level benchmark. The Final Perfect State Gate records this as WARNING 6.4 (human audit staged, not executed) and does not upgrade it to PASS. We do not claim any human-audited validation. The audit is the next planned step; results will be reported separately."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "human-audited dataset" | `human_audited=False` for all rows; no `audit_agreement_summary.json` |
| "human-audited validation" | audit staged, not executed |
| "gold labels" | `gold_label` empty for all rows; `silver_label_source=candidate_label_guess` |
| "annotator agreement is high" | no annotators have run; no agreement metrics exist |
| "the metrics are benchmark-level" | silver-conditional diagnostics only; not benchmark-level |

---

*End of response 04.*
