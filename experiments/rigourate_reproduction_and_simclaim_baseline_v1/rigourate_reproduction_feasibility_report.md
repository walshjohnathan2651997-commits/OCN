# RIGOURATE Reproduction Feasibility Report

**Audit date:** 2026-07-05
**Paper:** RIGOURATE — arXiv:2601.04350v2 [cs.CL] 12 Jan 2026
**Venue:** Findings of ACL 2026
**Authors:** Joseph James (Sheffield), Chenghao Xiao (Durham), Yucheng Li (Surrey), Nafise Sadat Moosavi (Sheffield), Chenghua Lin (Manchester)
**Auditor:** CESE-OCN automated audit (no API calls)

## 1. Audit scope

This report records whether a full official reproduction of RIGOURATE is possible from public resources as of 2026-07-05. The audit covers:
- arXiv paper text (full content)
- ACL Anthology entry (camera-ready, supplementary)
- GitHub (code, scripts, runnable example)
- HuggingFace (model weights, dataset)
- Author homepages and institutional pages (release pointers)
- Supplementary material (appendix, dataset card, model card, license)

The audit is read-only and uses public web search and direct URL inspection. No email was sent to authors; no API was called.

## 2. Resource inventory summary

| Resource | Status | Notes |
| --- | --- | --- |
| arXiv paper text | Available | arXiv:2601.04350v2 [cs.CL] 12 Jan 2026, full text accessible |
| ACL Anthology entry | Pending publication | Findings of ACL 2026; anthology entry not yet indexed as of audit date |
| GitHub repository | Not available | arXiv v2 contains placeholder string `[Github/HF Link]` |
| HuggingFace model | Not available | No matching model found under "RIGOURATE" or author names |
| HuggingFace dataset | Not available | No matching dataset found |
| Training data | Not available | 10K+ claim-evidence sets described in paper but not released |
| Annotation scripts | Not available | LLM annotator + peer-review calibration pipeline not released |
| Fine-tuned reranker | Not available | Model weights not released |
| Fine-tuned scorer | Not available | Model weights not released |
| Supplementary material | Not available | No appendix / dataset card / model card located |
| License | Unknown | No license specified because no artifacts released |
| Runnable example | Not available | No code/data/model to construct one |

Full inventory: see `official_resource_inventory.csv`.

## 3. Method summary (from paper text only)

RIGOURATE is a two-stage multimodal approach to scientific overstatement scoring:

1. **Stage 1 — Evidence retrieval.** A fine-tuned multimodal reranker retrieves supporting evidence passages from full scientific papers (ICLR/NeurIPS) given a scientific claim.
2. **Stage 2 — Overstatement scoring.** A fine-tuned model assigns a continuous overstatement score in [0, 1] to the (claim, retrieved evidence) pair.

Training data: 10K+ claim-evidence sets from ICLR/NeurIPS papers, annotated by 8 LLM annotators with peer-review calibration, plus human evaluation.

Output: a single continuous overstatement score per claim-evidence pair. Higher score = more overstatement.

## 4. Feasibility conclusion

**Status: blocked.**

A full official reproduction is **not currently possible** from public resources as of 2026-07-05. The arXiv v2 paper still carries the placeholder string `[Github/HF Link]` in place of a concrete code/data/model URL. No GitHub repository, HuggingFace model, HuggingFace dataset, supplementary material, or runnable example has been located via web search of arXiv, GitHub, HuggingFace, ACL Anthology, and author institutional pages.

The only publicly available asset is the paper text itself, which describes the method but does not include sufficient artifacts to reproduce the fine-tuned reranker, the fine-tuned scorer, the 10K+ training set, or the annotation pipeline.

## 5. What is possible without official artifacts

Given the blocked status, the task spec section IV authorizes constructing a **RIGOURATE-style scalar overstatement proxy baseline** that:

- Uses publicly available SimClaim data (444 pairs) — **not** the RIGOURATE 10K+ set.
- Outputs a continuous or ordinal scalar overstatement score.
- Does NOT claim to be official RIGOURATE.
- Is labeled as "RIGOURATE-style scalar proxy" or "scalar overstatement baseline" in all outputs.

Three proxy variants will be constructed (see section IV outputs):
- **A. rule_scalar_score** — cue-based scalar score on action/deployment/safety/policy/generalization/guarantee/always/fully/replace + evidence-limitation cues, output 0-3.
- **B. nli_scalar_score** — reuses HCM/NLI features (s_correct, contradiction, margin, entropy); blocked_reason recorded if features missing.
- **C. llm_scalar_proxy** — uses existing parsed LLM outputs (supported=0, mild=1, strong=2, contradiction=3); labeled as LLM-label-derived proxy only.

## 6. Prohibitions enforced

- The proxy MUST NOT be claimed as official RIGOURATE.
- The proxy MUST NOT be reported as a successful reproduction.
- No paid API will be called.
- No original data or V3.12 paper will be modified.
- No gold will be created.
- Silver labels will not be written as gold.

## 7. Recommended next actions (out-of-task, for advisor)

- Re-audit arXiv for v3 or later versions that may replace the placeholder URL.
- Email the corresponding author (Joseph James, Sheffield) to request code/data release status.
- Monitor ACL Anthology for the camera-ready supplementary material.
- Monitor OpenReview for any ICLR/NeurIPS dataset release.

## 8. Conclusion

**Full official reproduction: blocked.**
**Partial official reproduction: blocked.** (No artifacts available beyond paper text.)
**Proxy baseline construction: authorized by task spec, will proceed under section IV.**

The next section (§2 Method Dissection) extracts the full method from the paper text alone, and section IV proceeds with proxy baseline construction.
