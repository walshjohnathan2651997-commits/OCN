# Reviewer Risk Table (Paper Asset) — V3.17 Confidential Lightweight

<!-- Generated (UTC): 2026-07-06T20:14:30.819883+00:00 -->
<!-- Auto-filled from reports/current_project_status_v3_17.json -->

<!-- Caveat: This table documents anticipated reviewer risks and the
current evidence status. It is NOT a benchmark claim. The dataset is
a controlled silver diagnostic, not gold or human-audited. -->

| risk_id | severity | status | reviewer_attack | paper_section | remaining_limitation |
|---|---|---|---|---|---|
| R01 | high | done | Dataset is GPT/silver and shortcut-prone. | Limitations + Dataset Description | Human audit is not complete (protocol built, labels pending). Silver labels may still contain annotation artifacts no... |
| R02 | high | done | R4 may learn template cues from the silver generation process. | Limitations + Leakage Audit | Cue audits are heuristic (keyword lists, overlap ratios). Subtle semantic cues not captured by lexical audits may sti... |
| R03 | medium | done | Retrieval success may be oracle-biased (oracle evidence leaks into retrieval ranking). | Methods + Leakage Audit | Oracle recall is computed on silver labels. If silver labels are wrong, oracle recall may be mismeasured. Does not af... |
| R04 | medium | done | BM25 and simple rules are not novel; contribution is unclear. | Introduction + Related Work + Discussion | The complexity-vs-utility analysis is deployment-specific. It does not prove deterministic rules generally outperform... |
| R05 | medium | done | Why no LLM / VLM baseline? Stronger models may trivially outperform. | Discussion + Limitations | No head-to-head comparison with LLM/VLM baselines on this dataset. If confidentiality constraints are relaxed in futu... |
| R06 | high | partial | No human audit; silver labels may be systematically wrong. | Limitations + Future Work | Human audit pending. All silver labels remain un-audited. Until audit is complete, results are format-shift diagnosti... |
| R07 | medium | done | PDF extraction is unreliable; results may be artifacts of extraction errors. | Methods + Limitations | Stress test uses synthetic fixtures, not real PDFs. Real PDF corpus is missing from the workspace, so sentence-level ... |
| R08 | medium | done | System may be misconstrued as a general-purpose overstatement detector for scientific claims. | Introduction + Scope + Limitations | Six domains only. Generalization to biology, medicine, physics, or social science claims is not tested and not claimed. |
| R09 | medium | done | Sample size (444 candidates, 111 groups) is too small for reliable conclusions. | Methods + Limitations | Bootstrap CIs reflect controlled-pool variability only. Larger datasets with natural prevalence would be needed for p... |
| R10 | high | done | Full CESE-OCN neural architecture is not validated; the paper implies it is. | Introduction + Scope + Future Work | Full CESE-OCN neural architecture validation is future work. V3.17 does not claim neural-architecture-level results. |

**Status legend:** done = evidence complete; partial = evidence incomplete;
blocked = blocked by documented blocker; missing = evidence absent;
pending = planned, not started.

**Safe caveat:** We use a source-traceable controlled silver diagnostic
set. The labels are not gold or human-audited, and results should not be
interpreted as benchmark-level model validation.
