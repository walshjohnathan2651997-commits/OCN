# RIGOURATE Method Dissection

**Source:** arXiv:2601.04350v2 [cs.CL] 12 Jan 2026 (HTML version, fetched 2026-07-05)
**Paper title:** RIGOURATE: Quantifying Scientific Exaggeration with Evidence-Aligned Claim Evaluation
**Authors:** Joseph James (Sheffield), Chenghao Xiao (Durham), Yucheng Li (Surrey), Nafise Sadat Moosavi (Sheffield), Chenghua Lin (Manchester)
**Venue:** Findings of ACL 2026
**License:** CC BY 4.0 (paper text)

> Note: This dissection is based on the publicly available arXiv v2 paper text. Code, data, and model weights are NOT publicly available (placeholder `[Github/HF Link]` in arXiv v2). Where the paper text does not specify a methodological detail, this is recorded as "not specified in paper text".

## 1. Task definition

RIGOURATE defines **two tasks** for detecting overstatement in claims extracted from the abstract and introduction of scientific papers:

1. **Evidence Retrieval.** Given a claim, retrieve all relevant evidence that directly supports the claim from the paper body.
2. **Overstatement Detection.** Given a claim and its corresponding evidence, assign a continuous score indicating the degree to which the claim's wording exceeds what the evidence supports, accompanied by a brief justification.

**Three ordinal claim states** are defined qualitatively (no numeric thresholds given in the paper text):
- **Well-stated** — the claim is fully grounded in the paper's methods, results, and reasoning without exaggeration.
- **Partially overstated** — some components are supported but others extend beyond what the evidence warrants.
- **Overstated** — the claim makes assertions not justified by the paper's evidence (limited experiments, lack of methodological detail, etc.).

The actual model output is a **continuous overstatement score in [0, 1]**, where higher = more overstatement. The qualitative three-state scheme is used for case-study illustration, not as the primary model output.

## 2. Claim source

- **Venue:** ICLR and NeurIPS papers from OpenReview.
- **Claim extraction location:** Abstract and Introduction sections only.
- **Claim authorship filter:** Only author-self-stated claims are kept (LLM annotators filter out reviewer/citation quotes).
- **Paper count:** 659 ICLR + 213 NeurIPS = 872 papers (after PDF parsing failures excluded).
- **Reviewer agreement filter:** Only papers where all reviewers assigned identical overall scores are kept, to mitigate reviewer subjectivity and improve consistency.
- **Total claim-evidence sets:** 10K+ (exact count not specified in paper text).

## 3. Evidence retrieval

- **Source:** Full paper body (excluding abstract/introduction to avoid trivial self-retrieval).
- **Modalities:** Text paragraphs, figures, tables — multimodal.
- **PDF processing:** SciPDF parser for text; PDFFigures2 (Clark and Divvala, 2016) for figures and tables.
- **Segmentation:** Papers segmented into paragraphs and further into sentences to improve retrieval precision.
- **Classification:** Each passage is classified as **relevant** (directly related to the claim) or **irrelevant**.
- **Reranker:** A fine-tuned multimodal reranker retrieves supporting evidence passages. The base model is from a range of state-of-the-art reranker / multimodal models (specific base model names not extractable from the partial paper text; check Section 4 of the full paper).
- **Fine-tuning signal:** RIGOURATE's own annotated relevant/irrelevant labels.

## 4. Claim-evidence construction

- For each claim, the framework extracts candidate evidence passages from the same paper (text, figures, tables).
- LLM annotators judge each (claim, evidence) pair for relevance and overstatement degree.
- Review comments are then incorporated as additional context to calibrate the overstatement score.
- The result is a (claim, evidence, overstatement_score, justification) tuple per annotated pair.

## 5. Overstatement score

- **Type:** Continuous scalar in [0, 1].
- **Direction:** Higher = more overstatement.
- **Generator:** A fine-tuned model (separate from the reranker) takes (claim, retrieved evidence) and outputs a score with a brief natural-language justification.
- **Calibration:** The score is calibrated using peer-review comments as additional context during LLM annotation, reducing sensitivity to individual LLM and reviewer perspectives.
- **Justification:** The model produces a brief justification alongside the score (review-informed reasoning).

## 6. LLM annotation

- **Annotator panel:** Eight LLMs used as annotators.
- **LLM role:**
  1. Identify which sentences in abstract/introduction are authors' own claims (vs. citations, reviewer quotes, etc.).
  2. Extract candidate evidence passages from the paper body.
  3. Classify each passage as relevant/irrelevant to each claim.
  4. Generate a continuous overstatement score for each (claim, evidence) pair.
  5. Generate a brief justification.
- **Specific LLM identities:** Not extractable from the partial paper text (likely listed in Section 3 or Appendix).

## 7. Peer-review calibration

- **Review source:** OpenReview peer reviews for ICLR/NeurIPS.
- **Calibration mechanism:** Each review comment is incorporated as additional context when generating the overstatement score.
- **Purpose:** Reduces sensitivity to individual LLM and reviewer perspectives; provides access to expert-written critiques of evidential sufficiency and overgeneralisation.
- **Reviewer agreement filter:** Papers with full reviewer-score agreement only (mitigates reviewer subjectivity).

## 8. Human validation

- **Type:** Targeted human evaluation of annotation quality.
- **Scope:** Validation subset (specific size not extractable from partial paper text).
- **Purpose:** Validates that LLM-annotated overstatement scores align with human judgments.

## 9. Reranker (Stage 1)

- **Architecture:** Multimodal reranker (text + figures + tables).
- **Base model:** State-of-the-art reranker / multimodal model (specific names not extractable from partial text).
- **Training:** Fine-tuned on RIGOURATE's annotated relevant/irrelevant labels.
- **Output:** Ranked list of evidence passages per claim.

## 10. Scorer (Stage 2)

- **Architecture:** Multimodal model fine-tuned for overstatement scoring.
- **Input:** (claim, retrieved evidence).
- **Output:** Continuous overstatement score in [0, 1] + brief justification.
- **Training:** Fine-tuned on RIGOURATE's annotated (claim, evidence, score, justification) tuples.

## 11. Metrics

- **Evidence retrieval:** Standard retrieval metrics (precision, recall, etc. — specific metric names not extractable from partial text; likely nDCG, MRR, Recall@K).
- **Overstatement detection:** Regression-style metrics on the continuous score (specific metric names not extractable from partial text; likely RMSE, Pearson/Spearman correlation).
- **Comparison:** Fine-tuned RIGOURATE vs. zero-shot base models.

## 12. Baselines

- Zero-shot applications of state-of-the-art reranker and multimodal models.
- Strong baselines from prior scientific claim verification work (specific names not extractable from partial text).
- The paper claims fine-tuning yields consistent improvements over base zero-shot models.

## 13. Key findings (as stated in paper)

1. Intra-paper claim-evidence alignment is a **learnable** task.
2. Fine-tuning consistently improves performance on both evidence retrieval and overstatement scoring.
3. Overstatement often stems from **missing substantive detail** and **surface-level phrasing** (case study, Table 5 in paper).
4. RIGOURATE operationalises **evidential proportionality** for clearer, more transparent scientific communication.

## 14. Overlap with CESE-OCN

| Aspect | Overlap |
| --- | --- |
| Goal | Both target evidence-to-claim strength mismatch (not factual correctness). |
| Data source | Both draw on ML/NLP papers (RIGOURATE: ICLR/NeurIPS; CESE-OCN: 6 domains including autonomous driving, NLP, CV, RL, robotics, general ML). |
| Annotation | Both use LLM annotators with author screening. |
| Validation | Both reference human evaluation. |

## 15. Differences from CESE-OCN

| Aspect | RIGOURATE | CESE-OCN |
| --- | --- | --- |
| **Output type** | Continuous overstatement score [0, 1] | Four-class relation label (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) |
| **Relation typing** | Single scalar; no relation-type decomposition | Explicit four-class taxonomy with operational decision tree |
| **High-risk action overclaim** | Not isolated as a separate class | strong_action_overclaim is the high-risk boundary class |
| **Contradiction** | Treated as a separate degree of overstatement (claims "rarely contradicted by internal evidence") | Explicitly modelled as contradiction_candidate class with a separate detector |
| **Evidence source** | Intra-paper (full paper body) | Intra-paper evidence spans (real) + generated claim variants (controlled counterfactual) |
| **Claim source** | Author-written claims from abstract/introduction | Generated claim variants instantiating specific evidence-sufficiency relations |
| **Data design** | Natural claims from real papers | Controlled counterfactual diagnostic set (real evidence + generated claims) |
| **Annotation scale** | 10K+ claim-evidence sets, 872 papers | 444 pairs, 111 evidence groups, 6 domains |
| **Reviewer integration** | Peer-review comments used as calibration signal | Not used (silver labels from LLM pre-annotation + author screening) |
| **Reranker** | Fine-tuned multimodal reranker (Stage 1) | Not present (evidence is given) |
| **Scorer** | Fine-tuned multimodal overstatement scorer (Stage 2) | Mixed relation-routing framework (R4): contradiction detector + scope-calibration residual classifier + strong-action escalation route |
| **Justification** | LLM generates brief justification alongside score | No natural-language justification; class label only |
| **Pre-registered gold protocol** | Not present (human evaluation as validation) | Pre-registered gold adjudication protocol (§VII) with frozen success/downgrade criteria |
| **Realism audit** | Not present (natural claims) | Proposed gold-realism audit (because SimClaim claims are generated) |
| **Target failure mode** | General overstatement (any rhetorical exaggeration) | High-risk action/deployment/safety/policy overclaims specifically |

## 16. Implications for CESE-OCN positioning

RIGOURATE and CESE-OCN are **complementary**, not competing:

- RIGOURATE provides a **scalar overstatement signal** that is broad-coverage and review-informed.
- CESE-OCN provides a **fine-grained relation-type decomposition** that isolates the high-risk action-overclaim class.
- A scalar score alone does not directly separate mild scope expansion from a high-risk action overclaim; a four-class taxonomy does.
- A four-class taxonomy alone does not produce a continuous severity signal; a scalar score does.
- The empirical question (does scalar suffice for high-risk action-overclaim screening?) is tested in section V of this task.

## 17. Limitations of this dissection

This dissection is based on the publicly available arXiv v2 paper text. The following details are **not specified or not extractable** from the available text and would require the full PDF or released code:

- Specific LLM identities used as annotators (8 LLMs).
- Specific base models for the reranker and scorer.
- Exact metric definitions and values for evidence retrieval.
- Exact metric definitions and values for overstatement scoring.
- Size of human evaluation subset.
- Threshold for converting continuous score to qualitative state (well-stated / partially overstated / overstated).
- Annotation agreement statistics across the 8 LLM annotators.
- Hyperparameters, training configuration, compute budget.
- License for the (unreleased) code/data/model.

These gaps do not affect the qualitative comparison with CESE-OCN, but they do affect any attempt at quantitative reproduction — which is already blocked by the absence of public code/data/model (see §1 feasibility report).
