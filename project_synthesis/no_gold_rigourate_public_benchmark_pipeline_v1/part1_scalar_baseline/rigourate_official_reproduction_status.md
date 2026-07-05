# RIGOURATE Official Reproduction Status

**Audit date:** 2026-07-05
**Paper:** RIGOURATE, arXiv:2601.04350v2 [cs.CL] 12 Jan 2026
**Venue:** Findings of ACL 2026
**Authors:** Joseph James (Sheffield); Chenghao Xiao (Durham); Yucheng Li (Surrey); Nafise Sadat Moosavi (Sheffield); Chenghua Lin (Manchester)

## 1. Resources checked

| Resource | Location | Availability |
| --- | --- | --- |
| arXiv paper (v2) | https://arxiv.org/abs/2601.04350v2 | available |
| ACL Anthology entry | https://aclanthology.org/ | pending_publication (not indexed as of 2026-07-05) |
| Author homepages | (web search) | available (contact emails present) |
| GitHub repository | (web search) | **not_available** |
| HuggingFace model | (web search) | **not_available** |
| HuggingFace dataset | (web search) | **not_available** |
| Training data (10K+ claim-evidence sets) | (described in paper only) | **not_available** |
| Fine-tuned reranker weights | (described in paper only) | **not_available** |
| Fine-tuned scorer weights | (described in paper only) | **not_available** |
| Annotation scripts | (described in paper only) | **not_available** |
| Supplementary material | (none located) | **not_available** |
| License | (not specified) | **not_available** |

## 2. Blocked reason

The arXiv v2 (12 Jan 2026) of RIGOURATE contains a placeholder string `[Github/HF Link]` in place of the code/data/model URL. As of audit date **2026-07-05**, no concrete GitHub repository, HuggingFace model, dataset release, annotation script, supplementary material, or runnable example has been located via web search of arXiv, GitHub, HuggingFace, ACL Anthology, and author homepages.

The paper text describes:
- 10K+ claim-evidence sets annotated by 8 LLM annotators with peer-review calibration and human evaluation
- A fine-tuned multimodal reranker for evidence retrieval
- A fine-tuned model for continuous overstatement scoring (0-1)

None of these artifacts are publicly available.

## 3. Feasibility conclusion

**Status: blocked**

A full official reproduction is **not** currently possible from public resources. Only the arXiv paper text (method description) is available.

Per task spec, when official artifacts are unavailable, a RIGOURATE-style scalar proxy baseline may be constructed. The proxy MUST NOT be claimed as official RIGOURATE; it must be labeled as "RIGOURATE-style" or "scalar overstatement proxy".

## 4. Allowed conclusions

- The official RIGOURATE reproduction is **blocked**.
- A proxy baseline is **required** (this pipeline constructs one).
- No claim may be made that the proxy baseline equals official RIGOURATE.
- No claim may be made that official reproduction succeeded.

## 5. Next actions if artifacts are released

1. Re-audit arXiv for v3 or later versions that may replace the placeholder.
2. Check corresponding author email for code/data request.
3. Monitor ACL Anthology for camera-ready supplementary.
4. Monitor OpenReview for ICLR/NeurIPS dataset release.

## 6. Prohibitions enforced

- Do not claim proxy as official RIGOURATE.
- Do not fabricate reproduction success.
- Do not call paid API.
- Do not modify V3.15 paper.
- Do not modify original data.
- Do not create gold.
- Do not write silver as gold.
