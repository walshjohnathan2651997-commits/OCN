# Official Reproduction Run Log

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 — Section 3 Official Reproduction Attempt
**Date:** 2026-07-05
**Operator:** CESE-OCN automated audit (no API calls)

## 1. Objective

Attempt a minimal official reproduction of RIGOURATE (arXiv:2601.04350v2, Findings of ACL 2026) from public resources, following the README of the official GitHub/HuggingFace repository if one exists.

If the repository is incomplete or unavailable, explicitly record:
> official reproduction not currently possible from public repository

## 2. Pre-attempt audit (from §1 Official Resource Audit)

| Resource | Available? |
| --- | --- |
| arXiv paper text | Yes |
| GitHub repository | No (placeholder `[Github/HF Link]` in arXiv v2) |
| HuggingFace model | No |
| HuggingFace dataset | No |
| Supplementary material | No |
| Annotation scripts | No |
| Fine-tuned reranker weights | No |
| Fine-tuned scorer weights | No |
| Training data (10K+ claim-evidence sets) | No |
| License | Unknown |

Full inventory: see `official_resource_inventory.csv`.
Feasibility conclusion: **blocked**.

## 3. Reproduction attempt

### 3.1 Step 1 — Locate official repository

**Action:** Web search for "RIGOURATE" + author names + "GitHub" / "HuggingFace".
**Result:** No concrete GitHub or HuggingFace repository found.
**Detail:** arXiv v2 (12 Jan 2026) abstract concludes with the literal placeholder string:
> All code, models, and annotation scripts will be made publicly available [Github/HF Link].

The placeholder has not been replaced as of audit date 2026-07-05 (almost 6 months after arXiv v2 posting).

### 3.2 Step 2 — Locate ACL Anthology camera-ready

**Action:** Search ACL Anthology for "RIGOURATE" and author names.
**Result:** Findings of ACL 2026 entry not yet indexed as of 2026-07-05. Camera-ready supplementary (if any) not available.

### 3.3 Step 3 — Attempt to clone repository

**Action:** No concrete URL to clone. Step skipped.
**Result:** Not executed.

### 3.4 Step 4 — Attempt minimal end-to-end example

**Action:** No code, data, or model available. Step skipped.
**Result:** Not executed.

### 3.5 Step 5 — Verify against published metrics

**Action:** No model output to compare. Step skipped.
**Result:** Not executed.

## 4. Outcome

> **official reproduction not currently possible from public repository**

The official RIGOURATE code, data, models, annotation scripts, and supplementary material are not publicly available as of 2026-07-05. The arXiv v2 paper contains a placeholder URL (`[Github/HF Link]`) that has not been replaced. No GitHub repository, HuggingFace model, or HuggingFace dataset has been located via web search.

## 5. Environment (recorded for completeness, though no run was possible)

- Operating system: Windows 11 Pro
- Python: D:\ocn\.venv\Scripts\python.exe (numpy, pandas, sklearn, scipy available)
- No RIGOURATE-specific dependencies installable (no requirements.txt available)

## 6. Errors encountered

- **Error 1:** Placeholder URL `[Github/HF Link]` in arXiv v2 cannot be resolved to a concrete repository.
- **Error 2:** No ACL Anthology camera-ready available as of 2026-07-05.
- **Error 3:** No supplementary material available.

None of these errors are fixable on our side. They are all upstream release-blocked.

## 7. Recommended next actions (out-of-task, for advisor)

- **Email corresponding author** (Joseph James, jhfjames1@sheffield.ac.uk; Chenghua Lin, chenghua.lin@manchester.ac.uk) to request:
  - Expected public release date for code/data/model.
  - Whether a minimal reproducible example can be shared under NDA for academic verification.
  - Whether the 10K+ dataset can be released in a reduced form (e.g., 1K claim-evidence sets) for benchmarking.
- **Re-audit arXiv** for v3 or later versions that may replace the placeholder URL.
- **Monitor ACL Anthology** for the camera-ready supplementary material.
- **Monitor HuggingFace** for new models/datasets under author names.
- **OpenReview watch:** ICLR 2026 / NeurIPS 2025 datasets track for any RIGOURATE release.

## 8. Fallback path (authorized by task spec section IV)

Since the official reproduction is blocked, the task spec authorizes constructing a **RIGOURATE-style scalar overstatement proxy baseline** on the SimClaim 444-pair dataset. The proxy MUST NOT be claimed as official RIGOURATE. See section IV outputs for proxy construction.

## 9. Prohibitions enforced

- Did not claim a successful reproduction.
- Did not fabricate any reproduction result.
- Did not call any paid API.
- Did not modify V3.12 or original data.
- Did not create gold.
- Did not write silver as gold.
- Recorded `blocked_reason` for every unavailable artifact.

## 10. Conclusion

**Official reproduction status: blocked.**
**Official reproduction not currently possible from public repository.**
**Proxy baseline path authorized and will proceed under section IV.**
