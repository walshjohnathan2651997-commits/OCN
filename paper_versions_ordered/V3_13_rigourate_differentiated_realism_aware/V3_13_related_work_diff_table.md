# V3.13 Related Work Differentiation Table (RIGOURATE-Differentiated + Realism-Aware)

**Date:** 2026-07-05
**Source:** §II.A and Table X of CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md; `D:\ocn\docs\rigourate_reproduction_and_simclaim_baseline_v1\rigourate_forcebench_claimbench_related_work_insert.md`.

This standalone table organises the differentiation between CESE-OCN and the three closest related works: RIGOURATE [30], ForceBench [35], and CLAIM-BENCH [28]. It is intended as a quick-reference companion to §II.A of the paper.

---

## 1. Side-by-side comparison

| Dimension | RIGOURATE [30] | ForceBench [35] | CLAIM-BENCH [28] | CESE-OCN (this work) |
| --- | --- | --- | --- | --- |
| **Primary question** | How overstated is this claim, given retrieved evidence? | Does the model monotonically prefer calibrated vs. force-raised claims? | Is evidence correctly extracted and does it support the claim? | What *type* of evidence-sufficiency mismatch is this, and is it a high-risk action overclaim? |
| **Output representation** | Continuous overstatement score [0, 1] + justification | Contrastive preference signal (calibrated vs. force-raised) per force dimension | Document-level claim-evidence extraction + validation label (support/refute/NEI-style) | Four-class relation label (supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate) + strong_action screening signal |
| **Task formulation** | Scalar severity regression | Paired-claim preference | Extraction + validation | Single-instance relation typing + screening |
| **High-risk action overclaim** | Not isolated as a separate class | One of five force dimensions (scope) | Not isolated | Isolated as `strong_action_overclaim` (the high-risk boundary class); R4 has a dedicated escalation route |
| **Contradiction** | Treated as a rare edge case | One force dimension (relation) | Standard support/refute | Explicitly modelled with a dedicated detector (Route 1) |
| **Evidence source** | Full paper body (text + figures + tables), retrieved by fine-tuned reranker | Fixed cited passage | Full paper | Real evidence spans from scientific papers (extracted, not retrieved) |
| **Claim source** | Natural author-written claims (ICLR/NeurIPS abstracts + introductions) | Constructed paired claims (calibrated + force-raised) | Natural author-written claims | Generated counterfactual claim variants (controlled) |
| **Annotation** | 8 LLM annotators + peer-review calibration + human evaluation | Constructed paired claims | Expert annotation | AI pre-annotation + author screening (silver); pre-registered two-layer gold protocol (Layer 1 relation + Layer 2 realism) |
| **Scale** | 10K+ claim-evidence sets, 872 papers (659 ICLR + 213 NeurIPS) | (per-paper contrastive pairs) | (per-paper) | 444 pairs, 111 evidence groups, 6 domains |
| **Code/data release status (as of 2026-07-05)** | BLOCKED — arXiv v2 (12 Jan 2026) carries placeholder `[Github/HF Link]`; no public GitHub/HuggingFace/dataset found | (per-paper) | (per-paper) | Silver data in repo; gold protocol pre-registered; RIGOURATE-style proxy baseline in §VI.E (proxy, NOT official RIGOURATE) |
| **Realism risk** | Low (natural author-written claims) | Low (constructed paired claims) | Low (natural claims) | Non-trivial (controlled counterfactual claim variants); heuristic pre-screen: 4.7% overall, 9.0% for strong_action; two-layer gold protocol with 25% realism thresholds |
| **Empirical comparison to CESE-OCN** | Not available (official artifacts BLOCKED); proxy scalar baseline in §VI.E cannot distinguish mild from strong (ROC-AUC ≤ 0.59) and cannot match R4 strong_action F1 | Positioning-level only; no head-to-head | Positioning-level only; no head-to-head | — |
| **Relation to CESE-OCN** | Complementary: scalar severity + relation-type decomposition | Complementary: contrastive preference + single-instance typing | Sequential: extraction-validation feeds strength-calibration typing | — |

---

## 2. Key differentiation paragraphs (from §II.A)

### RIGOURATE [30]
RIGOURATE retrieves supporting evidence from full papers and assigns continuous overstatement scores to scientific claims, aligning each claim with the evidence that supports (or fails to support) it. RIGOURATE is stronger than the present work along several axes: it operates on natural author-written claims at larger data scale, performs evidence retrieval from full papers, and has been validated against human overstatement judgments. We acknowledge this clearly. The difference is one of *output granularity and target*: RIGOURATE estimates the **degree of overstatement** as a score, while CESE-OCN diagnoses the **type of evidence-sufficiency mismatch** as a four-class relation. In particular, RIGOURATE does not isolate *mild scope expansion* from *high-risk action/deployment overclaim* as separate operational classes; a single overstatement score can conflate a claim that mildly over-extends scope with a claim that asserts deployment readiness, safety, or operational conclusions the evidence does not justify. CESE-OCN's contribution is to make this separation operational via the `strong_action_overclaim` class and a relation-specific screening route targeting it. The two approaches are complementary: a continuous score can be produced by RIGOURATE-style systems, and a relation-type decomposition can be produced by CESE-OCN, on the same claim-evidence pair.

### ForceBench [35]
ForceBench is a contrastive evidence-force calibration stress test. It fixes the cited passage and compares a *calibrated claim* against a *force-raised claim* across five force dimensions — relation, modality, scope, temporal validity, and numeric specificity — testing whether a model monotonically prefers the calibrated claim over the force-raised claim. ForceBench is stronger than the present work along several axes: it provides a clean contrastive paired-claim protocol, covers five distinct force dimensions, and is cited-RAG oriented with monotonic preference as the evaluation signal. We acknowledge this clearly. The difference is one of *input form and output type*: ForceBench tests **monotonic preference between paired claims** (calibrated vs. force-raised), while CESE-OCN performs **single-instance relation typing and screening** for high-risk action-overclaim. ForceBench is cited-RAG oriented; CESE-OCN is scientific claim-evidence calibration / diagnostic screening oriented. ForceBench's contrastive design is powerful for testing whether a model *recognizes force mismatch at all*, but it does not directly output a four-class relation label on a single claim, and it does not isolate the high-risk action/deployment sub-class as a screening target. The two approaches are complementary: ForceBench-style contrastive tests can probe whether a model is force-sensitive, while CESE-OCN-style relation typing can output an operational screening label on a single claim.

### CLAIM-BENCH [28]
CLAIM-BENCH evaluates scientific claim-evidence extraction and validation across full papers, extending scientific claim verification to larger paper-level settings with full-paper evidence links. CLAIM-BENCH is stronger than the present work along several axes: it operates on natural full-paper claim-evidence pairs, evaluates extraction and validation jointly, and provides a larger-scale benchmark. We acknowledge this clearly. The difference is one of *primary question*: CLAIM-BENCH focuses on **whether evidence supports claims** (extraction + validation), while CESE-OCN focuses on **whether evidence is sufficient for the strength and actionability of claims** (calibration of claim strength to evidence). CLAIM-BENCH does not introduce a strength-mismatch taxonomy that separates mild scope overclaim from high-risk action overclaim; its labels are organized around support/refute/NEI-style extraction validation rather than around the action-overclaim boundary. The two approaches are complementary: CLAIM-BENCH-style extraction-validation can determine whether evidence is correctly linked to a claim, while CESE-OCN-style relation typing can diagnose whether the claim's strength is calibrated to that evidence.

### CESE-OCN differentiation summary
CESE-OCN differs from RIGOURATE, ForceBench, and CLAIM-BENCH in three specific ways. First, the **output representation** is a four-class relation label rather than a continuous scalar (RIGOURATE), a contrastive preference (ForceBench), or a document-level extraction/validation (CLAIM-BENCH). The four-class decomposition isolates `strong_action_overclaim` as a separate high-risk boundary class. Second, the **screening orientation** is explicit: R4 is designed as a screening-oriented complement to generic LLM/NLI judges, trading overall macro-F1 for targeted strong_action positive-F1 (R4 strong-F1 = 0.3967 vs. LLM strong-F1 = 0.0769 on matched samples), at the cost of higher review burden. Third, the **data design** is controlled counterfactual: SimClaim pairs real evidence spans from scientific papers with generated claim variants that instantiate specific evidence-sufficiency relations, enabling controlled diagnosis of relation-type separability — in contrast to RIGOURATE's natural author-written claims, ForceBench's paired-claim contrastive design, and CLAIM-BENCH's full-paper extraction setup. The §VI.E RIGOURATE-style scalar proxy baseline provides controlled silver-stage evidence that a scalar score cannot reliably distinguish `mild_scope_overclaim` from `strong_action_overclaim` (ROC-AUC ≤ 0.59) and cannot match R4's strong_action screening F1, providing empirical support for the four-class decomposition.

---

## 3. Prohibitions enforced

- No claim that CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH (the differentiation is positioning-level, not a head-to-head empirical benchmark; §IX item 9).
- No claim that the RIGOURATE-style proxy baseline is the official RIGOURATE system (§VI.E; §IX item 11).
- No claim that SimClaim is a natural-prevalence corpus (§V.A; §IX item 10).
- No claim that the silver-stage screening finding transfers to natural scientific writing (§IX item 10; §VII.J realism audit pending).
- No claim of being the first to propose scientific overstatement detection or evidence-force calibration (§I; §II.A; Appendix B forbidden claims).
