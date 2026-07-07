# 07 — Release Safety Response (Risk G)

**Risk ID:** G
**Reviewer attack:** "The repo contains internal scoring files with `true_label` and `oracle_hit` columns (redteam findings). How can you guarantee the public release bundle is safe?"
**Severity:** Medium

---

## 1. Reviewer concern

The reviewer notes that a repo-wide redteam scan finds 3 high-risk `forbidden_sorting_field` findings (`true_label` in `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv`, `true_label` and `oracle_hit` in `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv`). The reviewer may suspect that the public release bundle leaks gold labels or oracle hit information, that the redteam scan is incomplete, or that the release safety gate is being gamed by scope restriction.

## 2. What we agree with

We agree that the internal scoring files contain `true_label` and `oracle_hit` fields. We agree that these fields are high-risk if exposed in a public release bundle. We agree that the redteam scan correctly flags them as `forbidden_sorting_field` findings. We do not contest that a reviewer is entitled to demand evidence that the public release bundle excludes these fields and that the release safety gate is not gamed by scope restriction.

## 3. Evidence we have

- **Redteam scan.** `scripts/run_confidentiality_redteam_scan_v1.py` performs a repo-wide scan for `forbidden_sorting_field` and other confidentiality findings. The scan finds 3 high-risk findings, all in internal scoring files used for metrics computation (not for release).
- **Release safety manifest.** `release_safety_manifest_v3_17.json` records `release_safety_gate.status = PASS` with scope = bundle-only. The manifest enumerates every artifact in the release bundle and confirms none contains `true_label`, `oracle_hit`, `claim_text`, `evidence_text`, `selected_evidence`, `raw_text`, `clean_text`, `body_text`, or `pdf_text`.
- **Bundle-only scope.** The release safety gate operates on the public release bundle, not on the entire repo. The 3 high-risk findings are in internal scoring files that are excluded from the bundle. The reconciliation report (`reports/redteam_release_reconciliation_v3_17.md`) documents this scope decision explicitly.
- **Artifact ledger.** `reports/artifact_ledger_v3_17.csv` records every artifact with `safe_to_release`, `private_sensitive`, and `in_release_bundle` flags. The 3 high-risk files are marked `safe_to_release = false`, `private_sensitive = true`, `in_release_bundle = false`.
- **Public PDF corpus is hash-only.** `data/pdf_corpus_v1/sentences.jsonl` and `windows.jsonl` are hash-only (no `raw_text`/`clean_text`); full text resides in gitignored `data/private/pdf_corpus_v1_internal/`.
- **Leakage guard report.** `experiments/bm25_sentence_retrieval_v1/leakage_guard_report.json` confirms oracle fields are used only after ranking, not as input features.
- **Final gate status.** The Final Perfect State Gate records WARNING 9.1 (redteam internal-only) — the gate does not hide the finding; it records it as a documented limitation.

## 4. Evidence file

- `reports/redteam_release_reconciliation_v3_17.md`
- `release_safety_manifest_v3_17.json`
- `reports/artifact_ledger_v3_17.csv`
- `experiments/bm25_sentence_retrieval_v1/leakage_guard_report.json`
- `reports/final_perfect_state_gate_v3_17.json` (WARNING 9.1)
- `reports/leakage_quick_scan_v3_17.md`

## 5. Safe response

We answer the reviewer as follows: the 3 high-risk `forbidden_sorting_field` findings are real and are correctly flagged by the redteam scan. They are all in internal scoring files used to compute metrics (true labels are needed for evaluation; oracle hits are needed for canonicalizer ablation). These files are excluded from the public release bundle: `safe_to_release = false`, `private_sensitive = true`, `in_release_bundle = false` in the artifact ledger. The release safety manifest confirms the bundle contains no `true_label`, `oracle_hit`, `claim_text`, `evidence_text`, `selected_evidence`, `raw_text`, `clean_text`, `body_text`, or `pdf_text` fields. The release safety gate operates on bundle-only scope; this is a deliberate scope decision, documented in the reconciliation report, not a hidden restriction. The Final Perfect State Gate records the internal-only findings as WARNING 9.1.

The safe empirical conclusion is therefore narrow: **the public release bundle is clean of forbidden fields; the 3 high-risk findings are in internal scoring files that are excluded from the bundle. The release safety gate is PASS on bundle-only scope. The internal-only high-risk findings remain a documented limitation (WARNING 9.1) and are not promoted to PASS.**

## 6. Remaining limitation

- The repo (not the bundle) contains 3 internal scoring files with `true_label` and `oracle_hit`; these are needed for metrics computation and canonicalizer ablation.
- The release safety gate is bundle-only; a stricter repo-wide gate would fail on these 3 files. The scope decision is documented but is a scope restriction.
- The redteam scan covers `forbidden_sorting_field` and related findings; it does not cover every conceivable leakage channel (e.g., indirect reconstruction from aggregated statistics).
- Public PDF corpus is hash-only; readers cannot re-run BM25 on raw text without the gitignored private corpus.
- The artifact ledger is a snapshot; future additions to the repo must be re-scanned before release.

## 7. Paper text to add

> "We clarify the release safety posture. A repo-wide redteam scan finds 3 high-risk `forbidden_sorting_field` findings (`true_label` in `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv`; `true_label` and `oracle_hit` in `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv`). These are internal scoring files used for metrics computation and canonicalizer ablation; they are excluded from the public release bundle (`safe_to_release = false`, `private_sensitive = true`, `in_release_bundle = false` in the artifact ledger). The release safety manifest (`release_safety_manifest_v3_17.json`) confirms the bundle contains no `true_label`, `oracle_hit`, `claim_text`, `evidence_text`, `selected_evidence`, `raw_text`, `clean_text`, `body_text`, or `pdf_text` fields. The release safety gate is PASS on bundle-only scope; this scope decision is documented in `reports/redteam_release_reconciliation_v3_17.md`. The Final Perfect State Gate records the internal-only findings as WARNING 9.1 and does not promote them to PASS."

## 8. What not to claim

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "the entire repo is leak-free" | 3 high-risk findings exist in internal scoring files |
| "no internal file contains true_label" | 2 internal files contain `true_label` |
| "the redteam scan is exhaustive" | scan covers `forbidden_sorting_field` and related findings; not every conceivable channel |
| "release safety is PASS unconditionally" | PASS is bundle-only scope; repo-wide scan is WARNING |
| "public PDF corpus contains raw text" | public corpus is hash-only; raw text is in gitignored private corpus |

---

*End of response 07.*
