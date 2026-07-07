# Reviewer Risk Register — V3.17 Confidential Lightweight

**Generated (UTC):** 2026-07-06T20:14:30.819883+00:00
**Source:** `reports/current_project_status_v3_17.json` (auto-filled status)

**Purpose:** Anticipate reviewer attacks on the V3.17 paper and prepare
evidence-backed safe responses. Each risk has a severity, the evidence
needed to address it, the current evidence file, the current status,
a safe response, the paper section to address, and the remaining limitation.

**Hard boundaries:** No exaggeration. No fabricated experiments.
Missing results are marked `missing` or `blocked`. Silver data is never
called gold.

---

## Summary table

| risk_id | severity | status | reviewer_attack |
|---|---|---|---|
| R01 | high | done | Dataset is GPT/silver and shortcut-prone. |
| R02 | high | done | R4 may learn template cues from the silver generation process. |
| R03 | medium | done | Retrieval success may be oracle-biased (oracle evidence leaks into retrieval ranking). |
| R04 | medium | done | BM25 and simple rules are not novel; contribution is unclear. |
| R05 | medium | done | Why no LLM / VLM baseline? Stronger models may trivially outperform. |
| R06 | high | partial | No human audit; silver labels may be systematically wrong. |
| R07 | medium | done | PDF extraction is unreliable; results may be artifacts of extraction errors. |
| R08 | medium | done | System may be misconstrued as a general-purpose overstatement detector for scientific claims. |
| R09 | medium | done | Sample size (444 candidates, 111 groups) is too small for reliable conclusions. |
| R10 | high | done | Full CESE-OCN neural architecture is not validated; the paper implies it is. |

---

## Risk details

### R01 — Dataset is GPT/silver and shortcut-prone.

- **severity:** high
- **status:** done
- **status_source:** priority action 'Run leakage audit on real data': done
- **evidence_needed:** Leakage audit, claim-only baseline, human audit protocol, dataset version lock.
- **current_evidence_file:**
  - `experiments/leakage_audit_v1/audit_summary.md`
  - `experiments/leakage_audit_v1/claim_only_baseline.json`
  - `docs/human_audit_protocol_v1.md`
  - `docs/dataset_version_lock_v3_17.md`
- **safe_response:** We acknowledge the dataset is a controlled silver diagnostic set, not a gold benchmark. Labels are AI-preannotated (annotation_status=ai_preannotated, human_audited=False for all 444 rows). We mitigate shortcut risk with a 12-check leakage audit (claim-only baseline, shuffled/empty/title-only evidence, lexical overlap, cue words), a dataset version lock recording SHA256 and all invariants, and a small targeted human audit protocol. Results are reported as format-shift diagnostic findings, not benchmark-level model validation.
- **paper_section_to_address:** Limitations + Dataset Description
- **remaining_limitation:** Human audit is not complete (protocol built, labels pending). Silver labels may still contain annotation artifacts not detected by automated checks.

### R02 — R4 may learn template cues from the silver generation process.

- **severity:** high
- **status:** done
- **status_source:** priority action 'Run leakage audit on real data': done
- **evidence_needed:** Claim-only baseline, shuffled/empty/title-only evidence baselines, lexical cue audit, cue words by label.
- **current_evidence_file:**
  - `experiments/leakage_audit_v1/claim_only_baseline.json`
  - `experiments/leakage_audit_v1/shuffled_evidence_baseline.json`
  - `experiments/leakage_audit_v1/empty_evidence_baseline.json`
  - `experiments/leakage_audit_v1/title_only_retrieval_baseline.json`
  - `experiments/leakage_audit_v1/cue_words_by_label.csv`
  - `experiments/leakage_audit_v1/lexical_overlap_by_label.csv`
- **safe_response:** We check template-cue risk with four evidence-degradation baselines: claim-only (no evidence), shuffled evidence, empty evidence, and title-only retrieval. If claim-only performance approaches full-evidence performance, the model is likely using claim cues rather than evidence. We also audit cue words by label and lexical overlap. If any check exceeds the WARNING threshold, we restrict conclusions to format-shift diagnostic and explicitly state the model may be cue-dependent.
- **paper_section_to_address:** Limitations + Leakage Audit
- **remaining_limitation:** Cue audits are heuristic (keyword lists, overlap ratios). Subtle semantic cues not captured by lexical audits may still exist. Complete mitigation requires human adjudication.

### R03 — Retrieval success may be oracle-biased (oracle evidence leaks into retrieval ranking).

- **severity:** medium
- **status:** done
- **status_source:** priority action 'Run leakage audit on real data': done
- **evidence_needed:** No-oracle-in-selector check, no-label-in-queue-sorting check, retrieval ranking provenance.
- **current_evidence_file:**
  - `experiments/leakage_audit_v1/no_oracle_in_selector_check.json`
  - `experiments/leakage_audit_v1/no_label_in_queue_sorting_check.json`
  - `experiments/simclaim_pdf_corpus_retrieval_v1/retrieval_results_bm25.csv`
- **safe_response:** Retrieval ranking uses only claim_text as the query. Oracle evidence and evidence_text are used ONLY for evaluation (computing oracle recall), never for ranking or selection. The no_oracle_in_selector_check and no_label_in_queue_sorting_check guards verify that neither oracle evidence nor labels leak into the selector or queue sorting. The leakage audit confirms these guards pass.
- **paper_section_to_address:** Methods + Leakage Audit
- **remaining_limitation:** Oracle recall is computed on silver labels. If silver labels are wrong, oracle recall may be mismeasured. Does not affect the no-leakage guarantee of the ranking itself.

### R04 — BM25 and simple rules are not novel; contribution is unclear.

- **severity:** medium
- **status:** done
- **status_source:** priority action 'Implement and run complexity-vs-utility ablation': done
- **evidence_needed:** Complexity-vs-utility ablation, method comparison metrics, Pareto table.
- **current_evidence_file:**
  - `experiments/complexity_vs_utility_ablation_v1/method_comparison_metrics.csv`
  - `experiments/complexity_vs_utility_ablation_v1/method_pareto_table.csv`
  - `experiments/complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md`
- **safe_response:** The contribution is NOT BM25 itself. The contribution is (1) identifying the retrieval-to-screening format shift as a failure mode in confidential local PDF review, (2) using auditable deterministic canonicalization to bridge raw PDF chunks to screening-format evidence, and (3) demonstrating the performance-privacy-auditability-cost tradeoff under no-API/no-training/confidential constraints. BM25 is used as a well-understood, auditable retriever; the novelty is in the pipeline architecture and the format-shift diagnosis, not the retriever.
- **paper_section_to_address:** Introduction + Related Work + Discussion
- **remaining_limitation:** The complexity-vs-utility analysis is deployment-specific. It does not prove deterministic rules generally outperform learned models; it shows they are Pareto-optimal under the stated constraints.

### R05 — Why no LLM / VLM baseline? Stronger models may trivially outperform.

- **severity:** medium
- **status:** done
- **status_source:** priority action 'Implement and run complexity-vs-utility ablation': done
- **evidence_needed:** Complexity-vs-utility analysis, deployment constraint documentation, safe claims dictionary.
- **current_evidence_file:**
  - `experiments/complexity_vs_utility_ablation_v1/complexity_vs_utility_summary.md`
  - `experiments/complexity_vs_utility_ablation_v1/complexity_cost_audit.csv`
  - `docs/safe_claims_dictionary_v3_17.md`
- **safe_response:** The deployment scenario is confidential local PDF review: no API, no network, no model training, no data egress. LLM/VLM baselines require API egress or local GPU inference that violates the confidentiality constraint. The complexity-vs-utility analysis explicitly compares methods on the performance-privacy-auditability-cost Pareto frontier and shows where learned models would fit if the confidentiality constraint were relaxed. We do NOT claim deterministic rules universally outperform LLMs; we claim they are the appropriate choice under the stated constraints.
- **paper_section_to_address:** Discussion + Limitations
- **remaining_limitation:** No head-to-head comparison with LLM/VLM baselines on this dataset. If confidentiality constraints are relaxed in future work, LLM baselines should be added.

### R06 — No human audit; silver labels may be systematically wrong.

- **severity:** high
- **status:** partial
- **status_source:** evidence chain: Small targeted human audit protocol and seed queue are in place; auditor labels ...
- **evidence_needed:** Human audit protocol, audit seed queue, audit agreement summary (if available).
- **current_evidence_file:**
  - `docs/human_audit_protocol_v1.md`
  - `data/audit_templates/human_audit_template.csv`
  - `scripts/build_human_audit_queue_v1.py`
  - `experiments/human_audit_v1/audit_agreement_summary.json`
- **safe_response:** We acknowledge the human audit is not complete. The protocol (2-annotator independent review + adjudication) and seed queue (111 redacted candidates) are in place, but auditor labels are pending. We explicitly list this as a limitation in the paper. When the small targeted audit is complete, it will be described as a targeted reliability check, NOT a gold benchmark. No silver label will be re-described as gold or human-validated.
- **paper_section_to_address:** Limitations + Future Work
- **remaining_limitation:** Human audit pending. All silver labels remain un-audited. Until audit is complete, results are format-shift diagnostic only, not benchmark-level validation.

### R07 — PDF extraction is unreliable; results may be artifacts of extraction errors.

- **severity:** medium
- **status:** done
- **status_source:** priority action 'Implement and run PDF extraction stress test': done
- **evidence_needed:** PDF stress test report, extraction quality metrics, failure case analysis.
- **current_evidence_file:**
  - `experiments/pdf_extraction_stress_test_v1/stress_test_summary.md`
  - `experiments/pdf_extraction_stress_test_v1/extraction_quality_metrics.csv`
  - `experiments/pdf_extraction_stress_test_v1/failure_cases_redacted.csv`
  - `docs/pdf_extraction_stress_test_v1.md`
- **safe_response:** We test PDF extraction robustness with 12 synthetic stress documents covering multi-column, table-heavy, scanned-image, math-heavy, and mixed-layout cases. The stress test reports extraction quality metrics and failure cases. Scanned PDFs are detected and reported only; no OCR is applied by default (OCR would require additional validation and is out of scope). The stress test is an extraction robustness check, NOT a SOTA extraction claim.
- **paper_section_to_address:** Methods + Limitations
- **remaining_limitation:** Stress test uses synthetic fixtures, not real PDFs. Real PDF corpus is missing from the workspace, so sentence-level BM25 retrieval on real data is blocked. Extraction failures on real-world PDFs may differ from synthetic stress results.

### R08 — System may be misconstrued as a general-purpose overstatement detector for scientific claims.

- **severity:** medium
- **status:** done
- **status_source:** scope docs verified
- **evidence_needed:** Scope statement in README, current mainline doc, safe claims dictionary, dataset version lock.
- **current_evidence_file:**
  - `docs/current_mainline_v3_17_confidential.md`
  - `docs/safe_claims_dictionary_v3_17.md`
  - `docs/dataset_version_lock_v3_17.md`
  - `README.md`
- **safe_response:** We explicitly state the system is NOT a general scientific overstatement detector. It is a simulation/confidential local review queue for the retrieval-to-screening format-shift problem. The dataset covers six domains (autonomous driving, policy simulation, digital twin, cyber defense, MARL, robotics); results should not be generalized to other scientific domains. The safe claims dictionary and dataset version lock enforce this scope.
- **paper_section_to_address:** Introduction + Scope + Limitations
- **remaining_limitation:** Six domains only. Generalization to biology, medicine, physics, or social science claims is not tested and not claimed.

### R09 — Sample size (444 candidates, 111 groups) is too small for reliable conclusions.

- **severity:** medium
- **status:** done
- **status_source:** experiments/metric_robustness_v1/
- **evidence_needed:** Bootstrap CI metrics, dataset version lock, metric robustness summary.
- **current_evidence_file:**
  - `experiments/metric_robustness_v1/classification_metrics_with_ci.csv`
  - `experiments/metric_robustness_v1/queue_metrics_with_ci.csv`
  - `experiments/metric_robustness_v1/robustness_summary.md`
  - `docs/dataset_version_lock_v3_17.md`
- **safe_response:** The 444-candidate set is a controlled diagnostic, not a prevalence benchmark. We report group-aware bootstrap 95% CIs for all headline metrics. The CIs reflect variability within the controlled candidate pool, NOT natural prevalence. We explicitly state this in the metric robustness report and dataset version lock. Conclusions are framed as format-shift diagnostic findings on this controlled pool, not as population-level claims.
- **paper_section_to_address:** Methods + Limitations
- **remaining_limitation:** Bootstrap CIs reflect controlled-pool variability only. Larger datasets with natural prevalence would be needed for population-level claims.

### R10 — Full CESE-OCN neural architecture is not validated; the paper implies it is.

- **severity:** high
- **status:** done
- **status_source:** scope docs verified
- **evidence_needed:** Current mainline doc marking full CESE-OCN as future architecture, README scope statement.
- **current_evidence_file:**
  - `docs/current_mainline_v3_17_confidential.md`
  - `README.md`
  - `docs/safe_claims_dictionary_v3_17.md`
- **safe_response:** We explicitly state there is no full shared-threshold CESE-OCN validation in V3.17; the full architecture is future work, not the current claim. The current claim is the V3.17 Confidential Lightweight Local Review Queue pipeline (deterministic canonicalization + frozen R4 + SmartQueue). The README, current mainline doc, and safe claims dictionary all mark full CESE-OCN as future work. No result from the full neural architecture is reported in V3.17 paper assets.
- **paper_section_to_address:** Introduction + Scope + Future Work
- **remaining_limitation:** Full CESE-OCN neural architecture validation is future work. V3.17 does not claim neural-architecture-level results.

---

## Severity legend

- **high:** Likely reviewer attack; must have safe response + paper section.
- **medium:** Possible reviewer attack; should have safe response.
- **low:** Unlikely attack; documented for completeness.

## Status legend

- **done:** Evidence exists and is complete.
- **partial:** Evidence exists but is incomplete (e.g., protocol built, audit pending).
- **blocked:** Evidence is blocked by a documented blocker.
- **missing:** Evidence does not exist.
- **pending:** Evidence is planned but not started.
- **unknown:** Status could not be determined from the status JSON.

## Related artifacts

- Response playbook: `docs/reviewer_response_playbook_v3_17.md`
- Paper table: `paper_assets/v3_17_confidential/reviewer_risk_table.md`
- Status source: `reports/current_project_status_v3_17.json`
- Safe claims dictionary: `docs/safe_claims_dictionary_v3_17.md`
- Dataset version lock: `docs/dataset_version_lock_v3_17.md`
