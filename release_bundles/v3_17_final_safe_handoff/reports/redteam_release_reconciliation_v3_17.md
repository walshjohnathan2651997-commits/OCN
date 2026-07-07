# Redteam Release Reconciliation — V3.17 Confidential

**Generated:** 2026-07-07
**Mainline:** V3.17 Confidential Lightweight
**Status:** WARNING documented (not FAIL)

## 1. Purpose

Reconcile the apparent conflict between two safety signals in the Final Perfect-State Gate:

| Signal | Source | Value |
|--------|--------|-------|
| Redteam scan | `experiments/confidentiality_redteam_scan_v1/redteam_summary.json` | `high_risk_count=3`, `pass_public_release_gate=false` |
| Release safety manifest | `reports/release_safety_manifest_v3_17.json` | `release_safety_gate.status=PASS` |

## 2. Why the Two Signals Are Not Contradictory

The two signals measure **different scopes**:

- **Redteam scan** is a **repo-wide read-only scan**. It flags any file under the scanned directories that contains forbidden sorting fields (`true_label`, `oracle_hit`) in CSV headers. Its gate (`pass_public_release_gate = high_risk_count == 0`) fails whenever any internal file contains these columns, regardless of whether that file is included in the public release bundle.

- **Release safety manifest** operates **only on the public release bundle**. It classifies each of the 54 tracked artifacts by release safety and confirms none of the private/internal files appear in the bundle.

The conflict is resolved by classifying each high-risk finding and verifying release-bundle exclusion.

## 3. High-Risk Findings Classification

### Summary

| Classification | Count |
|----------------|-------|
| `public_release_leak` | 0 |
| `internal_only_excluded_from_release` | 3 |
| `false_positive_documented` | 0 |
| `needs_manual_review` | 0 |
| **Total** | **3** |

### HR-001: `experiments/canonicalized_review_queue_v1/canonicalized_r4_review_scores.csv`

| Field | Value |
|-------|-------|
| Risk type | `forbidden_sorting_field` |
| Matched pattern | `true_label` (CSV header) |
| Context (redacted) | CSV header contains column `true_label`. No claim/evidence/raw text disclosed. |
| Public or internal | **internal** |
| Included in release bundle | **false** |
| Classification | `internal_only_excluded_from_release` |

**Release bundle verification:** Grep of `release_bundles/v3_17_confidential_public/MANIFEST.json` for `canonicalized_r4_review_scores` returned no matches. The file is also listed in `release_safety_manifest_v3_17.json` under `private_sensitive` (artifact_id `A050_review_queue_scores`) and `contains_raw_text` (detected_columns: `selected_evidence`).

**Why internal is acceptable:** This is an internal scoring artifact used by the canonicalized review queue pipeline. The `true_label` column is used **only** for post-hoc metric computation (precision@k, recall@k), never for sorting or routing. The SmartQueue leakage guard (`experiments/lightweight_smart_queue_v1/leakage_guard_report.json`) confirms `labels_used_for_sorting=false` and `true_label_used_for_metrics_only=true`. Removing `true_label` would break metric reproducibility.

**Why the release bundle remains safe:** The `build_public_sanitized_release_v1.py` script only copies files from explicit inclusion lists (`SAFE_SCRIPTS`, `AGGREGATE_METRIC_FILES`, `REDACTED_AUDIT_FILES`, `TOY_EXPERIMENT_DIRS`, paper_assets, `SAFE_DOCS`, configs, tests). `canonicalized_review_queue_v1/` is not in any inclusion list. Additionally, `has_forbidden_text_columns()` excludes this file because it contains the `selected_evidence` column. Defense-in-depth: a new `FORBIDDEN_SORTING_COLUMNS` check excludes any CSV with `true_label`/`oracle_hit` columns.

### HR-002: `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv` (true_label)

| Field | Value |
|-------|-------|
| Risk type | `forbidden_sorting_field` |
| Matched pattern | `true_label` (CSV header) |
| Context (redacted) | CSV header contains column `true_label`. No claim/evidence/raw text disclosed. |
| Public or internal | **internal** |
| Included in release bundle | **false** |
| Classification | `internal_only_excluded_from_release` |

**Release bundle verification:** Grep of `release_bundles/v3_17_confidential_public/MANIFEST.json` for `risk_ranking_features` returned no matches. The file is not listed in any section of `release_safety_manifest_v3_17.json`. It is an internal analysis artifact not tracked by the artifact ledger (only `risk_ranking_results_by_variant.csv` and `risk_ranking_report.md` are tracked as safe_to_release).

**Why internal is acceptable:** This is an internal risk-ranking feature matrix used for diagnostic analysis. The `true_label` column is used **only** for post-hoc evaluation of ranking quality. The risk ranking pipeline sorts by `risk_score` (a derived feature), not by `true_label`.

**Why the release bundle remains safe:** `canonicalized_risk_ranking_v1/` is not in any inclusion list of `build_public_sanitized_release_v1.py`. Only `risk_ranking_results_by_variant.csv` (artifact A052) and `risk_ranking_report.md` (artifact A053) are tracked as safe_to_release. Defense-in-depth: `FORBIDDEN_SORTING_COLUMNS` check added to build script.

### HR-003: `experiments/canonicalized_risk_ranking_v1/risk_ranking_features.csv` (oracle_hit)

| Field | Value |
|-------|-------|
| Risk type | `forbidden_sorting_field` |
| Matched pattern | `oracle_hit` (CSV header) |
| Context (redacted) | CSV header contains column `oracle_hit`. No claim/evidence/raw text disclosed. |
| Public or internal | **internal** |
| Included in release bundle | **false** |
| Classification | `internal_only_excluded_from_release` |

**Release bundle verification:** Same file as HR-002. Grep of MANIFEST.json returned no matches.

**Why internal is acceptable:** The `oracle_hit` column is a diagnostic flag indicating whether the ranking oracle would have selected the same candidate. It is used **only** for post-hoc evaluation, never for ranking or routing.

**Why the release bundle remains safe:** Same as HR-002. Defense-in-depth: `FORBIDDEN_SORTING_COLUMNS` check added to build script.

## 4. Release Bundle Safety Confirmation

| Check | Result |
|-------|--------|
| Release bundle manifest | `release_bundles/v3_17_confidential_public/MANIFEST.json` |
| Total files in bundle | 224 |
| High-risk files in bundle | **0** |
| Verification method | Grep of MANIFEST.json paths for `canonicalized_r4_review_scores` and `risk_ranking_features` — no matches |
| Release safety manifest status | **PASS** |
| Unsafe public artifacts | 0 |
| Private in release | 0 |

## 5. Final Gate Impact

| Aspect | Value |
|--------|-------|
| Previous status | WARNING (check 9.1: redteam `high_risk_count=3` but `release_safety_gate=PASS`) |
| Reconciled status | **WARNING documented** — internal-only high-risk findings are classified and excluded from public release. Final Gate should remain WARNING (documented limitation) but NOT FAIL. |
| Rationale | The hard constraint is that public release must not contain high-risk files. This is satisfied (0 high-risk files in bundle). The internal high-risk findings are legitimate diagnostic artifacts that use `true_label`/`oracle_hit` only for post-hoc metric computation, never for sorting. Removing them would break metric reproducibility. The SmartQueue leakage guard confirms `labels_used_for_sorting=false`. |

## 6. Defense-in-Depth Actions

1. **Added `FORBIDDEN_SORTING_COLUMNS` check to `build_public_sanitized_release_v1.py`** — any CSV containing `true_label`, `oracle_hit`, `candidate_label_guess`, `final_label`, `gold_label`, or `human_audited` columns is excluded from the public release bundle, even if added to an inclusion list in the future.

2. **Added missing `.gitignore` entries** — `pdfs/`, `private_pdfs/`, `data/private/`, `experiments/private/`, `*.pdf`, `*.docx`, `*.xlsx`, `*.npz`, `*.pkl`, `*.joblib`, `*.zip`.

## 7. Conclusion

The redteam `pass_public_release_gate=false` and release safety `PASS` are **not contradictory**. They measure different scopes (repo-wide vs. release-bundle-only). All 3 high-risk findings are internal-only diagnostic artifacts that are excluded from the public release bundle by inclusion-list filtering, forbidden-text-column checks, and the new forbidden-sorting-column defense-in-depth check. The public release bundle contains 0 high-risk files. The Final Gate should retain WARNING (documented) but not FAIL.
