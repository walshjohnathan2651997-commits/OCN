# Fine-Grained Evidence-Sufficiency Relation Diagnosis for Rare High-Risk Scientific Action Overclaims

**Subtitle:** A Controlled Counterfactual Diagnostic Study of LLM Under-Detection and Screening-Oriented Routing

**Version:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit (validation-pending, protocol-locked)
**Date:** 2026-07-05

**Status:** Controlled silver-stage evidence with a pre-registered, protocol-locked gold adjudication mechanism (§VII). All numeric results in §VI are computed on the controlled silver-stage evaluation; the gold validation slots (Tables G1–G3) are designed so that gold results can be inserted without restructuring the paper. The framework, taxonomy, and frozen method are the contribution; the gold adjudication is the validation mechanism, not a pending apology.

**Changes from V3.12.1:** Differentiation revision against RIGOURATE, ForceBench, and CLAIM-BENCH — positioning, Related Work, contribution list, Abstract, Introduction, Data transparency, Discussion, and gold-realism audit only. **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning, no change to any experimental number, no change to the frozen R4 method, no change to the taxonomy boundary rules, no change to §VI numbers, no change to §VIII.D numbers, no change to the non-gold caveat, no change to the 50% retention caveat, no change to the R4 macro-F1 < LLM fact, no change to the gold-not-done fact.** The paper is repositioned from "opening a new field of scientific overstatement detection" to "fine-grained relation-type decomposition and high-risk action-overclaim screening on the existing scientific overstatement / evidence-force calibration track". §II adds a new subsection "Relation to Scientific Overstatement and Evidence-Force Calibration" with three paragraphs (RIGOURATE, ForceBench, CLAIM-BENCH) and a new Table X positioning CESE-OCN against these closest related works. The contribution list is condensed from five items to three precise items (taxonomy, diagnostic, screening-method). The Abstract and Introduction are adjusted to acknowledge prior work and remove "first to propose" framing. §V.A adds a synthetic/counterfactual transparency paragraph for SimClaim. §VIII adds a new subsection on why fine-grained relation typing is valuable. §VII adds a gold-realism audit proposal. The standalone file `proposed_gold_realism_extension.md` specifies the proposed realism-score fields. **This work does not claim to introduce scientific overstatement detection or evidence sufficiency calibration as a new field; it builds on RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35], and CLAIM-BENCH [28], and focuses on fine-grained relation typing and high-risk action-overclaim screening.** V3.12.1, V3.12, V3.11, V3.10.1, and V3.9 are preserved unchanged.

**Changes from V3.13 (RIGOURATE-Differentiated, prior release):** This version (V3.13 RIGOURATE-Differentiated + Realism-Aware) integrates the RIGOURATE Reproduction + SimClaim Differentiation v1 task results into the paper. Two structural additions only: (1) §VI.E reports a RIGOURATE-style scalar overstatement proxy baseline built on the existing SimClaim silver data and existing LLM-parsed outputs — **no paid API calls, no new experiments beyond the proxy construction, no new model training, no threshold retuning**; the proxy is explicitly labelled as a proxy and is NOT the official RIGOURATE system (official RIGOURATE code/data/model are not publicly available as of 2026-07-05); (2) §VII.J upgrades the proposed gold-realism audit to a two-layer gold protocol (Layer 1 relation label, Layer 2 claim realism), referencing `proposed_relation_realism_gold_protocol_v2.md`. §IX adds one limitation item (proxy-baseline caveat). Title changed to reflect the fine-grained relation-diagnosis positioning. **No §VI.A–§VI.D number is changed. No §VIII.D number is changed. No §VII.G criterion is changed. The R4 macro-F1 < LLM macro-F1 fact is preserved. The gold-not-done fact is preserved. The silver-not-gold fact is preserved. The SimClaim-is-counterfactual fact is preserved. The RIGOURATE-style baseline is a proxy, not an official reproduction.** V3.13 (prior), V3.12.1, V3.12, V3.11, V3.10.1, and V3.9 are preserved unchanged.

**Changes from V3.13 RIGOURATE-Differentiated + Realism-Aware (this V3.14 release):** This version (V3.14 Mainline Locked + Reviewer-Grade Consistency Audit) performs a reviewer-grade consistency audit on the V3.13 RIGOURATE-Aware text and locks the mainline as *fine-grained evidence-sufficiency relation diagnosis + rare high-risk strong_action_overclaim screening*. Changes are **wording-level and ordering-level only**: (i) a mainline-lock declaration is inserted before §III (Method) as §II.B; (ii) several over-strong phrasings are down-toned to validation-pending wording (no change to any number); (iii) the RIGOURATE / ForceBench / CLAIM-BENCH differentiation wording is sharpened in §II.A and §VI.E; (iv) the SimClaim counterfactual-data disclosure in §V.A and §IX is reinforced; (v) the two-layer gold protocol (§VII.J) wording is aligned with the frozen `gold_pilot_protocol_freeze_v1` package; (vi) the three non-gold credibility checks (§VIII.D) wording is repositioned as *robustness analyses that strengthen but do not validate*; (vii) section and table numbering is normalised. **No new experiments, no API calls, no gold annotation, no model retraining, no threshold retuning, no change to any §VI.A–§VI.D number, no change to any §VIII.D number, no change to §VII.G criteria, no new research direction, no deletion of the R4 macro-F1 < LLM fact, no deletion of the gold-not-done fact, no deletion of the silver-not-gold fact, no deletion of the SimClaim-counterfactual fact.** V3.13 RIGOURATE-Aware, V3.13 (prior), V3.12.1, V3.12, V3.11, V3.10.1, and V3.9 are preserved unchanged.

**Mainline lock (this version).** This paper is not a natural-prevalence benchmark and does not claim to replace broad scientific overstatement scoring. It studies fine-grained evidence-sufficiency relation diagnosis under a controlled counterfactual diagnostic setting, with a focus on rare high-risk strong_action_overclaim screening. The mainline is locked: subsequent revisions before gold validation may revise wording, ordering, and disclosure, but will not introduce a new research direction, will not claim natural prevalence, will not claim gold validation, and will not delete the silver-stage caveats.

**Changes from V3.11:** Insertion of three non-gold credibility checks (§VIII.D) — Evidence Necessity Check, Screening Utility Test, and Label-Shift Stress Test — based on already-existing data, predictions, and scores. **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning, no change to any experimental number, no change to the frozen R4 method, no change to the taxonomy boundary rules.** All §VI numbers (R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 values, bootstrap CI, ablation, FP/TP ratio) are preserved byte-identical from V3.11. The new §VIII.D is explicitly labeled as non-gold robustness analysis and does not replace gold adjudication. The prior §VIII.D (What Remains Unresolved) is renumbered to §VIII.E. A single sentence is added to the Abstract; one item is added to the Limitations. V3.11, V3.10.1, and V3.9 are preserved unchanged.

**Changes from V3.10.1:** Narrative and framework restructure to a high-standard positioning. No new experiments, no API calls, no gold annotation, no change to any experimental number, no change to the frozen R4 method, no change to the taxonomy boundary rules. Workshop / pilot-only / low-config language is removed from the main positioning; "not submission-ready" and "pre-gold complete draft" are replaced with "validation-pending" and "controlled silver-stage evidence." The gold validation section (§VII) is reframed as a protocol-locked validation mechanism rather than a self-denial passage. Contributions are expanded from 4 to 5 (§I). The Results section (§VI) uses "on the controlled silver-stage evaluation" as the standard qualifier. All experimental numbers (R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 values, bootstrap CI, ablation, FP/TP ratio) are preserved byte-identical from V3.10.1. V3.10.1 and V3.9 are preserved unchanged.

Author information omitted for review draft

## Abstract

Scientific claim verification is typically framed as deciding whether evidence supports or refutes a claim. We argue this framing is insufficient for scientific writing, where the most consequential failure mode is not outright contradiction but **evidence-to-claim strength mismatch**: the evidence is topically relevant, directionally consistent, and non-contradictory, yet it does not justify the *strength* of the claim — particularly when a claim asserts deployment readiness, actionability, safety, or operational conclusions on the basis of limited experimental evidence. **Building on recent work on scientific overstatement scoring and evidence-force calibration** (RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35]), **we study a fine-grained diagnostic variant of evidence-sufficiency calibration** and define a **four-class taxonomy**: supported, mild_scope_overclaim, strong_action_overclaim, and contradiction_candidate. We construct **SimClaim**, a controlled counterfactual diagnostic benchmark of 444 claim–evidence pairs across 111 evidence groups and six domains, with AI-preannotated and author-screened silver labels; evidence spans are drawn from real scientific papers while claim variants are generated to instantiate specific evidence-sufficiency relations. We propose **CESE-OCN/R4**, a structured evidence-relation screening framework that complements generic LLM/NLI judges via a contradiction detector, a scope-calibration residual classifier, and a conservative strong-action escalation route. On the controlled silver-stage evaluation, R4 improves strong_action positive-F1 from 0.2408 to 0.3967 while preserving contradiction performance; under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) consistently under-detect strong_action_overclaim (strong-F1 = 0.0769, recall 0.04), while R4 reaches strong-F1 = 0.3000 on matched samples — at the cost of lower overall macro-F1 (0.3280 vs. 0.5523), positioning R4 as a screening-oriented complement, not a replacement. Because official RIGOURATE code/data/model are not publicly available as of 2026-07-05, we construct a RIGOURATE-style scalar overstatement proxy baseline (§VI.E) — explicitly labelled as proxy, NOT the official RIGOURATE system — and show that, on the controlled silver-stage evaluation, a scalar score (whether cue-based or LLM-derived) cannot reliably distinguish mild_scope_overclaim from strong_action_overclaim (ROC-AUC ≤ 0.59) and cannot match R4's strong_action screening F1; scalar overstatement scoring and relation-specific screening are complementary. A **pre-registered two-layer gold adjudication protocol** (§VII: Layer 1 relation label + §VII.J Layer 2 claim realism, with pre-registered 25% class-level and paper-level realism thresholds) with frozen success and downgrade criteria is specified to validate the taxonomy, the strong_action retention pattern, and the claim-realism profile; gold results are inserted into Tables G1–G3 without restructuring the paper. We further report three non-gold credibility checks (§VIII.D) testing evidence necessity, screening utility, and sensitivity to simulated strong-label shift. The contribution is a fine-grained relation-type decomposition with a frozen, protocol-locked validation mechanism — not the introduction of scientific overstatement detection as a new field, and not a claim of state-of-the-art overstatement detection.

Index Terms — evidence sufficiency, claim calibration, scientific claims, action overclaim, relation-specific routing, LLM-as-judge, natural-language inference, simulation evidence.

## I. Introduction

**Recent work has begun to quantify scientific overstatement and evidence-force mismatch.** RIGOURATE [30] retrieves supporting evidence from full papers and assigns continuous overstatement scores to claims; the evidence-licensed claims perspective [31] frames scientific writing as calibrating assertion rights to available evidence; ForceBench [35] provides a contrastive evidence-force calibration stress test that fixes the cited passage and compares a calibrated claim against a force-raised claim across relation, modality, scope, temporal validity, and numeric specificity; CLAIM-BENCH [28] evaluates scientific claim-evidence extraction and validation across full papers. These lines establish scientific overstatement and evidence-force calibration as an active research track. **However, less attention has been paid to whether different overclaim relations require different diagnostic treatment, especially high-risk action/deployment overclaims.** In particular, a continuous overstatement score does not directly separate mild scope expansion from a high-risk action, deployment, safety, or generalization overclaim; a contrastive paired-claim force test does not directly perform single-instance relation typing; and a claim-evidence extraction benchmark does not isolate the evidence-to-claim strength-mismatch taxonomy.

Scientific claim verification is typically framed as a three-class task: given a claim and evidence, decide whether the evidence *supports* the claim, *refutes* it, or provides *not enough information* (NEI). This framing — introduced by FEVER [1], SNLI [2], and SciFact [3], and extended by recent scientific claim verification / claim-evidence reasoning benchmarks such as SciClaimHunt and CLAIM-BENCH [27], [28] — is effective for factual correctness, but it is **insufficient for fine-grained scientific claim calibration**. In scientific writing and AI-assisted research, the most frequent and consequential failure mode is not outright contradiction but **strength mismatch**: the evidence is topically relevant, directionally consistent, and non-contradictory, yet it does not justify the *strength* of the claim. A benchmark improvement becomes a "deployment-ready system"; a controlled simulated result becomes a "safety guarantee"; a single-domain observation becomes a "generalization claim". This mismatch is not a factual error — it is an evidence-sufficiency error, and current support/refute/NEI frameworks do not isolate it as a relation-type problem distinct from generic factual correctness.

This motivates the **evidence sufficiency calibration** task. Rather than asking only whether evidence supports or refutes a claim, we ask whether the evidence is *sufficient for the strength of the claim* — including its scope, action framing, deployment implications, safety conclusions, and generalization breadth. This framing is aligned with recent work on scientific overstatement, evidence-aligned claim evaluation, and evidence-licensed claims [30], [31]. We formulate this as a four-class relation problem: (i) **supported** — the evidence supports the claim as stated, including its strength; (ii) **mild_scope_overclaim** — the claim mildly over-extends the scope of the evidence, without asserting an action/deployment/safety conclusion; (iii) **strong_action_overclaim** — the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify; (iv) **contradiction_candidate** — the evidence contradicts the claim. Class (iii) — strong_action_overclaim — is the high-risk boundary class: the most consequential for scientific claim calibration and the hardest to detect, because the evidence is often relevant and the claim is not strictly false; it is simply stronger than the evidence warrants (Figure 2).

A natural hypothesis is that strong LLM judges (GPT-5.5, DeepSeek-V3) should handle this task well, given their broad language understanding. Recent LLM-as-judge work, however, stresses that automatic judges require careful validation against human judgments and may vary substantially by task, domain, prompt, and availability of grounded references [32]–[34]. We test this hypothesis empirically. Under the tested prompts, generic LLM judges are strong on overall support/refutation and contradiction (on the controlled silver-stage evaluation, GPT-5.5 macro-F1 = 0.5523, DeepSeek-V3 macro-F1 = 0.5270 on matched samples), but they **consistently under-detect strong_action_overclaim under both tested prompt designs**: on 100 matched SimClaim samples, both GPT-5.5 with a standard judge prompt and GPT-5.5 with a structured 5-step evidence-sufficiency decomposition prompt achieve strong_action-F1 of only 0.0769 (recall 0.04 = 1/25). DeepSeek-V3 on 200 samples achieves the same strong_action-F1 of 0.0769. The structured prompt design does *not* improve strong_action detection under this tested prompt setting (Figure 3). This is a controlled silver-stage finding; the pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this pattern is treated as validated.

We therefore position CESE-OCN/R4 as a **screening-oriented complement** to generic LLM/NLI judges, not a replacement. R4 is a mixed relation-routing framework (Figure 1): a contradiction detector handles the most separable relation first; a scope-calibration residual classifier handles supported vs. mild_scope_overclaim; and a conservative strong-action escalation route targets strong_action_overclaim specifically, under a guarded condition that prevents contradiction cases from being absorbed. On the same 100 matched samples where GPT and DeepSeek achieve strong_action-F1 0.0769, R4 achieves strong_action-F1 0.3000 on the controlled silver-stage evaluation (absolute gap +0.2231). **R4 is not the strongest model on overall macro-F1 — LLM judges retain that, with GPT-5.5 at 0.5523 vs. R4 at 0.3280 on the matched 100 — but it provides targeted screening signal on the high-risk boundary class that LLM judges miss under the tested prompts.** This positioning as a screening-oriented complement, rather than a competitive replacement, is central to the paper's contribution.

This manuscript makes **three contributions**, explicitly positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field:

1. **Taxonomy contribution.** We decompose evidence-sufficiency mismatch into **supported**, **mild_scope_overclaim**, **strong_action_overclaim**, and **contradiction_candidate**, with an operational decision tree (Figure 2), concrete examples (Table 0), and explicit boundary rules. This is a relation-type decomposition that complements continuous overstatement scoring (RIGOURATE [30]), contrastive paired-claim force testing (ForceBench [35]), and full-paper claim-evidence extraction (CLAIM-BENCH [28]); it is not a claim to introduce scientific overstatement detection as a new field. The separability of strong_action_overclaim as a reliably drawable class is a hypothesis tested by the pre-registered gold adjudication (§VII), not an assumption taken as already proven.

2. **Diagnostic contribution.** On the controlled silver-stage evaluation, we show that under tested prompts, strong LLM judges (GPT-5.5, DeepSeek-V3) can achieve higher overall macro-F1 (0.5523 / 0.5270 on matched samples) while **consistently under-detecting strong_action_overclaim** (strong-F1 = 0.0769, recall 0.04 = 1/25 across both models and both prompt designs tested). This is a controlled silver-stage diagnostic finding — not a fundamental limit of LLMs — and the pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this pattern is treated as established.

3. **Screening-method contribution.** We propose **CESE-OCN/R4**, a relation-specific screening complement that improves strong_action recall and positive-F1 (R4 strong-F1 = 0.3000 on matched 100 samples vs. LLM 0.0769; R4 strong-F1 = 0.3967 vs. flat baseline 0.2408 on the full 444) at the cost of lower overall macro-F1 (0.3280 vs. 0.5523). R4 is positioned as a screening-oriented complement to black-box LLM judges, not a competitive replacement and not a state-of-the-art overstatement detector. A pre-registered gold adjudication protocol (§VII) with frozen success and downgrade criteria specifies how the silver-stage screening claim is validated or downgraded.

The remainder of the paper is organized as follows: §II positions the work, including a new subsection on the relation to scientific overstatement and evidence-force calibration (RIGOURATE, ForceBench, CLAIM-BENCH) and a positioning table; §III formulates the task and provides taxonomy examples (Table 0) and the decision tree (Figure 2); §IV describes the CESE-OCN/R4 framework (Figure 1); §V describes the data and protocol, including a synthetic/counterfactual transparency statement for SimClaim; §VI reports controlled silver-stage results (Figure 3, Tables 1–3); **§VII specifies the pre-registered gold validation protocol, including placeholder Tables G1–G3, frozen success/downgrade criteria, and a proposed gold-realism audit extension**; §VIII discusses implications, including three non-gold credibility checks (§VIII.D) and a subsection on why fine-grained relation typing is valuable (§VIII.F); §IX states limitations; §X concludes. Case studies and detailed tables are in the appendix.

## II. Related Work and Positioning

Generic claim verification and NLI estimate whether evidence supports or contradicts a statement (FEVER [1], SNLI [2], SciFact [3]). Recent scientific claim verification datasets and claim-evidence reasoning benchmarks extend this line to larger scientific-paper settings and full-paper evidence links [27], [28]. Related claim-citation alignment systems also emphasize selective escalation from abstract-level reasoning to passage-level evidence when local evidence is insufficient [29]. These works motivate scientific claim-evidence reasoning but generally do not isolate the particular relation of evidence-to-claim *strength* mismatch.

RAG evaluation and LLM-as-judge frameworks (RAGAs [12], ARES [13], G-Eval [14], MT-Bench [15]) evaluate faithfulness, context relevance, or answer quality for generic factuality, not for the specific failure mode of evidence-claim *strength* mismatch. Recent LLM-as-judge surveys and benchmarks further caution that LLM judges need task-specific validation against human judgments, especially in high-stakes or correctness-sensitive settings [32]–[34]. Hedging detection [25] and NLI calibration [26] are related but do not introduce a strength-calibration taxonomy. CESE-OCN is complementary: it asks whether a scientific claim calibrates its strength to the evidence available, including cases where the claim is topically relevant but over-extends the action implied by the evidence.

### A. Relation to Scientific Overstatement and Evidence-Force Calibration

The closest recent lines to our framing are scientific overstatement scoring, evidence-force calibration, and scientific claim-evidence reasoning. We discuss the three closest works — RIGOURATE [30], ForceBench [35], and CLAIM-BENCH [28] — and position CESE-OCN relative to each.

**RIGOURATE [30]** retrieves supporting evidence from full papers and assigns continuous overstatement scores to scientific claims, aligning each claim with the evidence that supports (or fails to support) it. RIGOURATE is stronger than the present work along several axes: it operates on natural author-written claims at larger data scale, performs evidence retrieval from full papers, and has been validated against human overstatement judgments. We acknowledge this clearly. The difference is one of *output granularity and target*: RIGOURATE estimates the **degree of overstatement** as a score, while CESE-OCN diagnoses the **type of evidence-sufficiency mismatch** as a four-class relation. In particular, RIGOURATE does not isolate *mild scope expansion* from *high-risk action/deployment overclaim* as separate operational classes; a single overstatement score can conflate a claim that mildly over-extends scope with a claim that asserts deployment readiness, safety, or operational conclusions the evidence does not justify. CESE-OCN's contribution is to make this separation operational via the strong_action_overclaim class and a relation-specific screening route targeting it. The two approaches are complementary: a continuous score can be produced by RIGOURATE-style systems, and a relation-type decomposition can be produced by CESE-OCN, on the same claim-evidence pair.

**ForceBench [35]** is a contrastive evidence-force calibration stress test. It fixes the cited passage and compares a *calibrated claim* against a *force-raised claim* across five force dimensions — relation, modality, scope, temporal validity, and numeric specificity — testing whether a model monotonically prefers the calibrated claim over the force-raised claim. ForceBench is stronger than the present work along several axes: it provides a clean contrastive paired-claim protocol, covers five distinct force dimensions, and is cited-RAG oriented with monotonic preference as the evaluation signal. We acknowledge this clearly. The difference is one of *input form and output type*: ForceBench tests **monotonic preference between paired claims** (calibrated vs. force-raised), while CESE-OCN performs **single-instance relation typing and screening** for high-risk action-overclaim. ForceBench is cited-RAG oriented; CESE-OCN is scientific claim-evidence calibration / diagnostic screening oriented. ForceBench's contrastive design is powerful for testing whether a model *recognizes force mismatch at all*, but it does not directly output a four-class relation label on a single claim, and it does not isolate the high-risk action/deployment sub-class as a screening target. The two approaches are complementary: ForceBench-style contrastive tests can probe whether a model is force-sensitive, while CESE-OCN-style relation typing can output an operational screening label on a single claim.

**CLAIM-BENCH [28]** evaluates scientific claim-evidence extraction and validation across full papers, extending scientific claim verification to larger paper-level settings with full-paper evidence links. CLAIM-BENCH is stronger than the present work along several axes: it operates on natural full-paper claim-evidence pairs, evaluates extraction and validation jointly, and provides a larger-scale benchmark. We acknowledge this clearly. The difference is one of *primary question*: CLAIM-BENCH focuses on **whether evidence supports claims** (extraction + validation), while CESE-OCN focuses on **whether evidence is sufficient for the strength and actionability of claims** (calibration of claim strength to evidence). CLAIM-BENCH does not introduce a strength-mismatch taxonomy that separates mild scope overclaim from high-risk action overclaim; its labels are organized around support/refute/NEI-style extraction validation rather than around the action-overclaim boundary. The two approaches are complementary: CLAIM-BENCH-style extraction-validation can determine whether evidence is correctly linked to a claim, while CESE-OCN-style relation typing can diagnose whether the claim's strength is calibrated to that evidence.

**Table X. Positioning against Closest Related Work.**

| Work | Primary question | Data type | Output | Handles overclaim severity? | Separates overclaim types? | Targets action/deployment overclaim? | Our relation |
| --- | --- | --- | --- | --- | --- | --- | --- |
| RIGOURATE [30] | How overstated is this claim, given retrieved evidence? | Natural author-written claims + retrieved evidence from full papers | Continuous overstatement score | Yes (continuous score) | No (single score, no type decomposition) | No (no separate action-overclaim class) | Complementary: score + relation-type decomposition |
| ForceBench [35] | Does the model monotonically prefer calibrated vs. force-raised claims? | Contrastive paired claims (calibrated vs. force-raised) with fixed cited passage | Monotonic preference signal per force dimension | Yes (force dimensions include scope and modality) | Partial (five force dimensions, but not single-instance four-class relation) | No (no separate action-overclaim screening target) | Complementary: contrastive force-sensitivity + single-instance relation typing |
| CLAIM-BENCH [28] | Is evidence correctly extracted and does it support the claim? | Natural full-paper claim-evidence pairs | Extraction + validation label (support/refute/NEI-style) | No (not strength-calibration oriented) | No (no overclaim-type taxonomy) | No | Complementary: extraction-validation + strength-calibration typing |
| **CESE-OCN / SimClaim (this work)** | What *type* of evidence-sufficiency mismatch is this, and is it a high-risk action overclaim? | Controlled counterfactual diagnostic set (real evidence spans + generated claim variants) | Four-class relation label + strong_action screening signal | Yes (taxonomy separates severity by relation type) | Yes (four-class relation decomposition) | Yes (strong_action_overclaim is the screening target) | — |

**The controlled silver-stage evidence suggests that contradiction, scope shift, and action escalation should not be treated as identical classification errors.** Contradiction aligns naturally with NLI-style signals. Mild scope shift remains ambiguous and may require finer annotation. **Strong action overclaim sits between support and contradiction**: the evidence may support a factual finding but not the action, deployment, or generalization asserted by the claim. This is why a single flat four-class classifier under-performs on strong_action_overclaim (on the controlled silver-stage evaluation, baseline strong-F1 0.2408), and why a relation-specific router (R4, controlled silver-stage strong-F1 0.3967) is needed. Whether this pattern holds under gold adjudication is the subject of the protocol-locked validation in §VII.

This manuscript is a **framework-level contribution on the existing scientific overstatement / evidence-force calibration track**: a fine-grained relation-type decomposition with a relation-specific router, a controlled counterfactual diagnostic benchmark, and a protocol-locked validation mechanism. It is **not** a claim to introduce scientific overstatement detection or evidence sufficiency calibration as a new field, **not** a final public benchmark, **not** a human-gold evaluation, and **not** a claim that all four classes are solved. All LLM comparison results are labeled as small-sample controlled evaluation (N ≤ 200) and are never merged with SimClaim main results or claimed as gold standard.

### B. Mainline Lock Declaration

**This paper is not a natural-prevalence benchmark and does not claim to replace broad scientific overstatement scoring. It studies fine-grained evidence-sufficiency relation diagnosis under a controlled counterfactual diagnostic setting, with a focus on rare high-risk strong_action_overclaim screening.**

The mainline is locked at this version (V3.14). Subsequent revisions before gold validation may revise wording, ordering, and disclosure, but will **not**:

- introduce a new research direction beyond fine-grained relation diagnosis + strong_action_overclaim screening;
- claim natural-prevalence estimation;
- claim gold validation (gold is planned, not completed; §VII);
- delete the silver-stage caveats (§IX items 1–3);
- delete the R4 macro-F1 < LLM macro-F1 fact (§VI.B; §VIII.A; §IX item 4);
- delete the SimClaim-is-counterfactual disclosure (§V.A; §IX item 10);
- promote the RIGOURATE-style proxy baseline (§VI.E) to the official RIGOURATE system;
- promote the blocked `nli_scalar_score` baseline to a completed result;
- promote any planned baseline to a completed result;
- delete or weaken the two-layer gold protocol (§VII.J).

This mainline-lock declaration is the binding commitment for all pre-gold revisions. The pre-registered two-layer gold adjudication (§VII: Layer 1 relation label + §VII.J Layer 2 claim realism) is the protocol-locked mechanism that determines whether the silver-stage findings are treated as validated. Until gold adjudication is complete, all §VI results are reported as **controlled silver-stage evidence**, not as validated findings.

## III. Task and Problem Formulation

### A. Evidence Sufficiency Calibration Task

Each instance consists of a claim, an evidence span, and a silver candidate label in four relation classes:

- **supported**: the evidence supports the claim as stated, including its strength. This is not "the claim is absolutely true" — it means the evidence is sufficient for the strength of the claim as written.
- **mild_scope_overclaim**: the evidence supports a weaker version of the claim; the claim mildly over-extends the scope (e.g., a single-dataset result is framed as a multi-dataset result), but no action/deployment/safety conclusion is asserted.
- **strong_action_overclaim**: the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify. **strong_action_overclaim is not the same as contradiction**: the claim may be directionally consistent with the evidence, but its strength is excessive.
- **contradiction_candidate**: the evidence contradicts the claim; the claim and evidence point in opposite directions on the same metric or conclusion (including detail-swapping of numbers, names, or metrics).

Labels are treated as AI-preannotated development labels (silver), pending independent gold adjudication (§VII).

### B. Taxonomy Decision Tree (Figure 2)

To make the taxonomy operationalizable and reduce the boundary confusion identified in the author sanity audit (§V.D), we introduce a four-step decision tree for label assignment. Figure 2 shows the simplified tree; the full operational version is in `taxonomy_boundary_decision_tree.md`.

```
                       +---------------------------+
                       |   Claim-Evidence Pair     |
                       +-------------+-------------+
                                     |
                                     v
              +----------------------------------------+
              | Step 1: Directional Conflict?         |
              | Does the claim point OPPOSITE to      |
              | evidence on the same metric, number,  |
              | entity, or conclusion?                |
              | (includes detail-swapping)            |
              +-----------------+---------------------+
                          YES   |   NO
                +---------------+   +---------------+
                v                               v
        +----------------+        +-----------------------------+
        | contradiction_ |        | Step 2: Action/Deployment/  |
        | candidate      |        | Safety/Operational Cue?     |
        +----------------+        | (deploy, safety, guarantee, |
                                  | operational, policy, broad   |
                                  | generalization, outperforms, |
                                  | suitable for, theoretically  |
                                  | justified, etc.)             |
                                  +--------------+--------------+
                                          YES    |    NO
                                  +--------------+   +--------------+
                                  v                              v
                       +-------------------------+   +-----------------------+
                       | Step 3: Evidence        |   | Step 4: Scope         |
                       | Sufficient for Action   |   | Over-Extension?       |
                       | Strength?               |   | Does the claim expand |
                       | Is evidence limited to  |   | scope/domain/         |
                       | single benchmark /      |   | population/condition/ |
                       | simulation / lab /      |   | temporal range beyond |
                       | limited metric / single |   | evidence, WITHOUT     |
                       | domain, while claim     |   | action consequences?  |
                       | asserts stronger        |   +-------+---------------+
                       | action conclusion?      |    YES    |    NO
                       +-----------+-------------+   +--------+   +--------+
                              YES   |   NO            v           v
                       +------------+   +----------+ +--------+ +--------+
                       v                v          | mild_   | |        |
                +--------------+  +------------+    | scope_  | | sup-   |
                | strong_      |  | Re-examine |    | over-   | | ported |
                | action_      |  | as sup.    |    | claim   | |        |
                | overclaim    |  | or mild    |    +---------+ +--------+
                +--------------+  +------------+
```

**Figure 2.** Taxonomy decision tree (simplified). Step 1: directional conflict on the same metric/number/entity → `contradiction_candidate` (including detail-swapping). Step 2-3: action/deployment/safety/operational cue present and evidence insufficient for action strength → `strong_action_overclaim`. Step 4: scope over-extension without action consequences → `mild_scope_overclaim`; otherwise → `supported`. The full operational version with cue lists and boundary-case rules is in `taxonomy_boundary_decision_tree.md`.

**Key distinctions operationalized by this tree:**

1. **strong_action_overclaim does not require directional conflict.** The claim may align with evidence direction, but its *strength* (action/deployment/safety assertion) exceeds what the evidence warrants.
2. **contradiction_candidate is about directional conflict** on the same metric/number/entity, including detail-swapping (e.g., evidence says "6 systems", claim says "8 systems").
3. **mild_scope_overclaim is about scope/generalization over-extension** without action/deployment/safety consequences.
4. **supported means evidence is sufficient for the claim's stated strength**, not that the claim is "absolutely true."

The decision tree is a *labeling aid*, not a validated annotation scheme. Cases where the tree yields ambiguous results are flagged as boundary cases for gold adjudication (§V.D, `high_risk_sample_bank.csv`). Table 0 (below) provides 8 illustrative examples (2 per class) from the SimClaim silver set, all traceable to `strict_silver_max_candidates_v1.csv`; full versions are in `table_taxonomy_examples_v3_6_clean.csv`. The V3.6 case integrity audit replaced the V3.5 T2 mild case (TCB_008, number inflation that a reviewer would judge as contradiction) with a clean scope-expansion case (SBV2-ALL92-G170-C02, numbers match exactly, only scope adjective added) — see `case_integrity_audit.csv` for the full audit.

**Table 0. Taxonomy examples (8 cases, 2 per class, silver-label SimClaim).** See `table_taxonomy_examples_v3_6_clean.csv` for full text.

| Class | case_id | candidate_id | domain | claim (short) |
| --- | --- | --- | --- | --- |
| supported | TCB_001 | SBV2-ALL92-G215-C01 | policy_simulation | ABM discussion says decision-support effectiveness remains uncertain because calibration, data integration, and interpretation require expertise. |
| supported | TCB_004 | SBV2-ALL92-G067-C01 | cyber_defense | AgentCyberRange study evaluates six frontier AI systems under matched prompts and budgets. |
| mild_scope_overclaim | TCB_007 | SBV2-ALL92-G002-MILD | autonomous_driving | nuPlan-R adds Success Rate and All-Core Pass Rate metrics to assess planner robustness and performance balance as the main comparison basis. |
| mild_scope_overclaim | TCB_NEW_MILD_2 | SBV2-ALL92-G170-C02 | robotics | In simulation, GRaD-Nav++ reports success rates of 83% on trained tasks and 75% on unseen multi-stage tasks during evaluation. |
| strong_action_overclaim | TCB_009 | SBV2-ALL92-G215-C03 | policy_simulation | ABM discussion says decision-support effectiveness remains uncertain because calibration, data integration, interpretation, and validation require extensive expertise. |
| strong_action_overclaim | TCB_012 | SBV2-ALL92-G107-C03 | digital_twin | Approach jointly calibrates digital twin and searches for optimal control rule, outperforming existing methods in numerical biopharmaceutical experiments and direct physical plant trials. |
| contradiction_candidate | TCB_015 | SBV2-ALL92-G215-C04 | policy_simulation | ABM discussion says decision-support effectiveness is clear because calibration, data integration, and interpretation require little expertise. |
| contradiction_candidate | TCB_018 | SBV2-ALL92-G036-C04 | autonomous_driving | Bench2Drive describes official training data as already available, making method comparisons operate at algorithm level rather than system level. |

### C. Why strong_action_overclaim Is the High-Risk Boundary Class

strong_action_overclaim is the most consequential class for scientific claim calibration, because it corresponds to cases where a claim is *actionable* (deployment, policy, safety) but the evidence is *insufficient* for that action. It is also the hardest to detect, because: (1) the evidence is often relevant and non-contradictory; (2) the claim is not strictly false — it over-extends rather than fabricates; (3) generic NLI signals (entailment/contradiction) do not separate "supports a finding" from "supports the action claimed"; (4) under the tested prompts, LLM judges tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate, missing the action-escalation signal. The primary success criterion for R4 is therefore **strong_action_overclaim positive-F1**, while requiring that flat4 macro-F1, contradiction positive-F1, and escalation macro-F1 are not damaged.

**The separability of strong_action_overclaim as a reliably drawable class is a hypothesis tested by the pre-registered gold adjudication (§VII), not an assumption taken as already proven.** The author sanity audit (§V.D) flags strong_action_overclaim at 75% confusion rate; if gold adjudication reveals that the mild_vs_strong boundary is not reliably drawable (κ < 0.40), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution. The paper is explicitly designed to be downgradable per §VII.G if this occurs — this is a protocol-locked safety mechanism, not a self-denial passage.

## IV. CESE-OCN/R4: A Mixed Relation-Routing Framework

### A. Framework Overview — Why Relation-Specific Routing

The central design principle of R4 is that **different evidence relations require different signals and should not be handled by a single flat classifier**. The controlled silver-stage evidence is consistent with this: contradiction is comparatively well captured by NLI-style evidence signals (on the controlled silver-stage evaluation, NLI-only strong-F1 = 0.3934), while strong_action_overclaim requires action-aware features that NLI does not provide (action-gap-only strong-F1 = 0.3648; NLI + action-gap = 0.4209). A single flat four-class classifier conflates these signals and under-performs on the most consequential class (baseline strong-F1 = 0.2408).

R4 is therefore designed as a **relation-specific diagnostic routing framework**, not a threshold-tuned heuristic. The routing order reflects a theoretical principle: handle the most separable relation first (contradiction), then the most consequential relation under a conservative guard (strong_action), then the residual scope calibration (supported vs. mild). Thresholds are frozen operationalizations of this principle, selected on train/dev under pre-specified constraints (§IV.D) and then frozen. R4 is explicitly a **screening-oriented complement** to generic LLM/NLI judges, not a replacement — it is optimized to reduce under-detection of action/deployment overclaims while preserving contradiction performance, accepting a lower macro-F1 in exchange for higher strong_action recall.

### B. Routing Flow (Figure 1)

```
                    +-------------------------------+
                    |     Claim-Evidence Pair       |
                    +---------------+---------------+
                                    |
                                    v
              +-----------------------------------------+
              |  NLI relation features                  |
              |  + scope / action / deployment cues     |
              +-----------------------------------------+
                                    |
              +------------+--------+--------+------------+
              |                     |                    |
              v                     v                    v
         p_contra              p_strong               p_svm
       (contradiction)      (strong-action)       (supported/mild)
              |                     |                    |
              v                     v                    v
    +----------------+    +--------------------+    +---------------+
    | Route 1:       |    | Route 2:           |    | Route 3:      |
    | if p_contra    |    | if p_strong>=t_str |    | if p_svm>=tvm |
    |   >= t_contra  |    | AND p_contra<t_low |    |   supported   |
    |   -> contra    |    |   -> strong_action |    | else          |
    |                |    |                    |    |   mild_scope  |
    +-------+--------+    +---------+----------+    +-------+-------+
            |                       |                      |
            +------+-------+--------+------+-------+-------+
                   |       |        |      |
                   v       v        v      v
              +-------------------------------------+
              |              Final Label            |
              +-------------------------------------+
```

| Route | Order | Decision | Threshold (mean, 10 seeds) | Rationale |
| --- | --- | --- | --- | --- |
| Route 1 — Contradiction | 1st | if `p_contra >= t_contra` → `contradiction_candidate` | `t_contra = 0.48` | Most separable; handling first prevents absorption into strong_action or mild. |
| Route 2 — Strong-action escalation | 2nd | if `p_strong >= t_strong` AND `p_contra < t_low` → `strong_action_overclaim` | `t_strong = 0.535`, `t_low` = lower guard | Most consequential; action-gap + NLI features. Conservative guard prevents contradiction absorption. |
| Route 3 — Scope residual | 3rd | if `p_svm >= t_svm` → `supported`; else → `mild_scope_overclaim` | `t_svm = 0.51` | Least separable boundary (mild-F1 = 0.1266). SVM residual handles it last. |

**Figure 1.** R4 routing flow. The router applies three routes in order: contradiction first (the most separable relation), then strong-action escalation under a conservative contradiction guard (to prevent contradiction cases from being absorbed into strong_action), then a supported/mild residual classifier. Frozen mean thresholds: `t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`, `t_low` = lower contradiction guard.

### C. Why This Order — Theoretical Motivation

**Route 1 (Contradiction first).** Contradiction is the strongest and most separable relation in the pilot data. NLI-style signals capture it well. Handling contradiction first prevents downstream routes from absorbing contradiction cases into strong_action or mild.

**Route 2 (Strong-action escalation under a conservative guard).** strong_action_overclaim is the most consequential relation but the hardest to detect. The strong-action expert uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The conservative guard (`p_contra < t_low`) prevents contradiction cases from being absorbed into strong_action — critical because strong_action and contradiction can look similar to a strong-action expert.

**Route 3 (Scope-calibration residual).** Supported vs. mild_scope_overclaim is the residual scope-calibration problem, handled last because it is the least separable boundary (supported-F1 = 0.4424, mild-F1 = 0.1266 — the weakest boundary in the taxonomy). An SVM residual classifier handles this, acknowledging that the supported/mild boundary remains an open problem.

### D. R4 Is Intentionally Conservative

R4 is **not** optimized to maximize overall macro-F1, but to reduce under-detection of action/deployment overclaims while preserving contradiction performance. On the controlled silver-stage evaluation, R4 accepts a lower macro-F1 than a flat classifier or LLM judge (R4 macro-F1 = 0.4238 on 444 samples, 0.3280 on matched 100; GPT-5.5 = 0.5523 on matched 100). R4 accepts supported/mild → strong false positives (98 supported → strong, 24 mild → strong) in exchange for higher strong recall (0.4562 vs. baseline 0.2062). R4 is selected against 5 router variants under 5 pre-specified constraints: strong_positive_delta ≥ +0.05, flat4_macro_delta ≥ -0.02, contradiction_positive_delta ≥ -0.03, escalation_macro_delta ≥ -0.03, positive_delta_seed_count ≥ 7. R4 is the only router meeting all 5 constraints simultaneously. This conservative design is the right trade-off for a **screening-oriented complement** to LLM judges: R4 flags potential action overclaims that LLM judges miss, accepting false positives that a human reviewer (or an LLM judge on a second pass) can filter. A cost-sensitive variant (cw4.0) gives a small additional improvement (+0.0254 strong-F1) but does not meet the replacement threshold (+0.03) and is retained only as an auxiliary sensitivity analysis.

## V. Data and Experimental Protocol

### A. SimClaim Controlled Silver-Stage Diagnostic Set

The current study uses a paper-only strict silver set containing 444 claim-evidence pairs, 111 evidence groups, six domains (policy_simulation, marl, digital_twin, robotics, autonomous_driving, cyber_defense), and balanced four-way silver labels (111 per class). These labels are AI-preannotated and author-screened; they are pending independent gold adjudication (§VII). All experiments use group-aware splits so that claims derived from the same evidence group do not cross train/dev/test boundaries. Router thresholds and hyperparameters are selected on train/dev only. The reported R4 result is frozen in `D:\ocn\experiments\mixed_framework_v2_frozen_r4_baseline` and is the current main baseline for this manuscript version.

**Synthetic / counterfactual transparency statement.** SimClaim is **not** a natural-prevalence corpus of author-written claims. It is a **controlled counterfactual diagnostic set**: evidence spans are drawn from real scientific papers, while claim variants are generated to instantiate specific evidence-sufficiency relations (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate). The four-way balanced design (111 per class) is a *deliberate construction* for pressure-testing boundary recognition under matched evidence, **not** an estimate of the natural prevalence of these relations in real scientific writing. In natural scientific corpora, we expect `contradiction_candidate` and `strong_action_overclaim` to be substantially rarer than `supported` and `mild_scope_overclaim`. Consequently:

- SimClaim is appropriate for **pressure-testing boundary recognition under matched evidence** and for **controlled comparison of relation-specific routing strategies**;
- SimClaim is **not** appropriate for estimating the real-world prevalence of each evidence-sufficiency relation in scientific papers, nor for training a calibrated prior over relation frequencies;
- SimClaim's balanced design may inflate the apparent base rate of strong_action_overclaim and contradiction_candidate relative to natural corpora; downstream deployments that use R4 as a screening layer should re-calibrate the operating threshold against the target corpus's expected base rate.

This transparency statement is reflected in the §VII gold-validation protocol, which proposes a parallel **claim-realism audit** (§VII.H) so that gold adjudication assesses both relation-label agreement and claim realism/plausibility.

### B. LLM Judge Comparison Protocol

For the LLM judge comparison, we use two matched-sample subsets:

- **DeepSeek-V3 baseline (200 samples)**: a label-balanced 200-sample subset (50 per class). DeepSeek-V3 is queried via the OpenAI-compatible DeepSeek API (model: `deepseek-chat`), temperature 0, single run. Output is parsed into the same four-class label space. Results are labeled "small-sample controlled evaluation, N ≤ 200" and are never merged with SimClaim main results.
- **GPT-5.5 standard vs. structured (100 samples)**: a label-balanced 100-sample subset (25 per class), selected to overlap with the DeepSeek 200-sample set and to cover all six domains. GPT-5.5 is queried via a third-party proxy (temperature 0, single run). Two prompt strategies are compared: **Standard** (a direct judge prompt asking for a four-class label) and **Structured** (a 5-step evidence-sufficiency decomposition prompt that explicitly asks the model to check factual alignment, scope expansion, action/deployment claims, evidence sufficiency, and a final label).

R4 predictions on the same 100/200 samples are computed for matched-sample comparison. The LLM comparison is **single-run, temperature 0, no variance estimate** — an explicit limitation (§IX).

### C. External Public Dataset Transferability Probe

To probe whether the evidence-relation approach transfers to public claim-verification data, we run a small gold-derived subset evaluation on **SciFact** [3] and **VitaminC** (dev/test). This is an **external transferability probe and sanity check**, not a validation of the four-class evidence-sufficiency taxonomy. Public gold labels are preserved as original (SUPPORT / CONTRADICT-REFUTES / NEI), with a conservative derived mapping (SUPPORT → supported, CONTRADICT/REFUTES → contradiction_candidate, NEI → unsupported_or_insufficient). **No mapping to strong/mild labels is performed**, because public datasets do not contain the action-overclaim taxonomy. We evaluate four methods: TF-IDF claim+evidence, TF-IDF claim-only (leakage probe), NLI cross-encoder (`cross-encoder/nli-deberta-base`), and an R4-compatible heuristic. Five seeds are used, with ≤300 eval samples per dataset. **This probe can only test generic support/refutation transfer; it cannot validate the SimClaim evidence-sufficiency taxonomy, which requires action-overclaim labels that public datasets do not contain.**

### D. Author Sanity Audit of Silver Labels

To check whether the silver labels are prima facie plausible, we conducted a small author sanity audit of 40 silver labels. **This audit is not a substitute for independent human adjudication.** It is a qualitative sanity check by the authors to flag labels that may be questionable or unclear before independent gold validation.

**Audit protocol:** We sampled 40 cases from the 444-row silver set, oversampling strong_action_overclaim (20 cases) since it is the central class, plus 7 supported, 7 mild_scope_overclaim, and 6 contradiction_candidate. For each case, the authors assigned `author_sanity_decision` (reasonable / questionable / unclear) and `possible_confusion` (none / supported_vs_mild / mild_vs_strong / strong_vs_contradiction).

**Audit results:** 15 reasonable, 5 questionable, 20 unclear (25/40 = 62.5% flagged). strong_action_overclaim has the highest confusion rate (15/20 = 75%), mostly mild_vs_strong confusion. All 6 contradiction_candidate cases are flagged unclear, mostly strong_vs_contradiction confusion (detail-swapping missed by the audit heuristic). supported is the most stable class (7/7 reasonable).

**Root cause distribution of the 25 questionable/unclear cases:**

- mild_vs_strong_boundary_unclear: 12 cases (48%) — the core taxonomy challenge.
- strong_vs_contradiction_boundary_unclear: 6 cases (24%) — the audit heuristic missed detail-swapping; the decision tree (Figure 2, Step 1) now operationalizes detail-swapping as contradiction.
- claim_too_abstract: 5 cases (20%) — a claim generation issue, not a taxonomy issue.
- audit_heuristic_too_conservative: 2 cases (8%) — the audit was too strict, not the labels too weak.

**Interpretation:** This audit confirms that the silver labels are validation-pending. The 25 questionable/unclear cases are concentrated at the two hardest taxonomy boundaries (mild-vs-strong and strong-vs-contradiction), which is expected for an evidence-sufficiency task. The LLM under-detection finding (§VI.B) is computed against these silver labels, and the high questionable/unclear rate means the finding is **controlled silver-stage evidence, pending independent gold adjudication** — not yet an established property of LLM judges. The audit does not invalidate the framework (the relative pattern — R4 > LLM on strong_action — may hold under gold), but it bounds the strength of the claim. The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for gold adjudication priority; `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none of which are claimed as gold. The full audit is in `author_sanity_audit_40.csv`.

### E. Framing

Because the dataset is small, silver-labeled, and the author sanity audit flags substantial label uncertainty, all results are framed as **controlled silver-stage evidence**. A higher-tier confirmatory submission would require 300–500 independently adjudicated claim-evidence pairs, inter-annotator agreement statistics, significance tests against stronger external baselines, and external validation. The pre-registered gold adjudication (§VII) is the protocol-locked next step toward that target.

## VI. Results

> **All numerical results in this section are computed on the controlled silver-stage evaluation against AI-preannotated, author-screened silver labels. The pre-registered gold adjudication in §VII is the protocol-locked mechanism that determines whether these patterns are treated as validated: if gold supports the silver labels, these patterns become validated pilot findings; if not, the affected claims are downgraded according to the pre-registered criteria in §VII.G.** These are validation-pending findings; they are not gold benchmark numbers. The protocol-locked validation in §VII specifies how these numbers will be re-evaluated once gold labels are available.

### A. Internal Silver Diagnostic Results (Table 1)

The strongest controlled silver-stage result is that **on the controlled silver-stage evaluation**, R4 improves strong-action positive-F1 while preserving contradiction and escalation. Table 1 reports the main comparison among the flat baseline, frozen R4 router, and the auxiliary cost-sensitive variant. Per-class F1 and the router-selection table (R4 vs. R1/R2/R3/R5) are in `V3_1_result_tables.csv`; the bootstrap confidence interval for the strong-positive delta is [0.1058, 0.1988], positive in 10/10 random seeds.

**Table 1. Internal R4 targeted result (controlled silver-stage evaluation, 444 claims, 10 seeds).** See `table_main_results_clean.csv`.

| Method | Strong F1 | Strong Recall | Contra F1 | Flat4 F1 | Use |
| --- | --- | --- | --- | --- | --- |
| baseline_flat4 | 0.2408 | 0.2062 | 0.7308 | 0.3963 | baseline |
| **R4_conservative_strong_router (MAIN)** | **0.3967** | **0.4562** | **0.7296** | **0.4238** | **main_method** |
| B_cost_sensitive_cw4.0 (AUX) | 0.4221 | 0.4625 | 0.7296 | 0.4365 | auxiliary |

- R4 is the frozen main method (immutable). The cost-sensitive variant is auxiliary (delta vs R4 = +0.0254, below the +0.03 threshold, CI crosses zero).
- On the controlled silver-stage evaluation, the key improvement is in **strong_action_overclaim** (+0.1559 strong-F1 over baseline), with contradiction preserved (-0.0012, well within the -0.03 constraint).
- R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives) — a trade-off for improved strong recall. This is a known trade-off: R4 improves strong recall at the cost of supported/mild → strong false positives.

### B. LLM Judge Comparison (Table 2, Figure 3)

This is the central new analysis. We compare R4 against generic LLM judges on matched SimClaim samples. **All numbers in this subsection are computed on the controlled silver-stage evaluation.**

**Table 2. LLM judge comparison on matched SimClaim samples (Group C).** See `table_main_results_clean.csv`.

| Method | N | Macro-F1 | Strong F1 | Strong Recall | Contra F1 |
| --- | --- | --- | --- | --- | --- |
| GPT-5.5 standard | 100 | 0.5523 | 0.0769 | 0.04 | 0.6857 |
| GPT-5.5 structured (5-step) | 100 | 0.5543 | 0.0769 | 0.04 | 0.6857 |
| DeepSeek-V3 (matched 100) | 100 | 0.5248 | 0.0769 | 0.04 | 0.8317 |
| DeepSeek-V3 (full 200) | 200 | 0.5270 | 0.0769 | 0.04 | 0.8317 |
| R4 (matched 100) | 100 | 0.3280 | 0.3000 | — | — |
| R4 (full 200) | 200 | — | 0.3158 | — | — |

**Overall Macro-F1 (higher is better):**

```
GPT-5.5 structured  | ████████████████████████████████████████████████  0.5543
GPT-5.5 standard    | ████████████████████████████████████████████████  0.5523
DeepSeek-V3 (200)   | ██████████████████████████████████████████████   0.5270
DeepSeek-V3 (100)   | ██████████████████████████████████████████████   0.5248
R4 (matched 100)    | ██████████████████████████████                   0.3280
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Strong-Action F1 (higher is better):**

```
R4 (matched 200)    | ████████████████████████████                     0.3158
R4 (matched 100)    | ███████████████████████████                      0.3000
GPT-5.5 structured  | █                                                 0.0769
GPT-5.5 standard    | █                                                 0.0769
DeepSeek-V3 (200)   | █                                                 0.0769
DeepSeek-V3 (100)   | █                                                 0.0769
                    +------+------+------+------+------+------+------+--+
                    0.0   0.1   0.2   0.3   0.4   0.5   0.6   0.7
```

**Figure 3.** LLM vs. R4 strong_action gap on matched SimClaim samples, computed on the controlled silver-stage evaluation. LLMs (GPT-5.5 standard, GPT-5.5 structured, DeepSeek-V3) all converge on strong_action-F1 = 0.0769 (recall 0.04 = 1/25). R4 reaches strong_F1 = 0.3000 on the matched 100 and 0.3158 on the matched 200. LLMs retain substantially higher overall macro-F1 (0.5248–0.5543 vs. R4 0.3280). Interpretation: **on the controlled silver-stage evaluation, LLMs are stronger overall, but R4 targets the strong_action gap observed under the tested prompts.**

**Key findings (all computed on the controlled silver-stage evaluation):**

1. **On the controlled silver-stage evaluation, both GPT-5.5 standard and structured achieve strong_action-F1 of 0.0769 (recall 0.04 = 1/25).** This structured 5-step evidence-sufficiency decomposition prompt design **did not improve** strong_action detection under the tested setting. The structured prompt does not hurt macro-F1 (0.5543 vs. 0.5523) or contradiction-F1 (both 0.6857), but it does not improve strong_action either. GPT only flagged 7/100 samples as containing an action/deployment/safety claim in structured mode, despite 25/100 being strong_action_overclaim by silver label.
2. **DeepSeek-V3 on 200 samples also achieves strong_action-F1 0.0769** on the controlled silver-stage evaluation (precision 1.0, recall 0.04 = 1/25), while reaching macro-F1 0.5270 and contradiction-F1 0.8317 — strong overall, missing strong_action.
3. **On the controlled silver-stage evaluation, R4 provides targeted complementary value.** On the same 100 samples where GPT and DeepSeek achieve strong_F1 0.0769, R4 achieves strong_F1 = 0.3000 (absolute gap +0.2231). On the 200-sample set, R4 achieves strong_F1 = 0.3158 (absolute gap +0.2389 over DeepSeek). R4 is not stronger overall — LLM judges retain substantially higher macro-F1 (0.5523 vs. 0.3280) and contradiction-F1 — but it targets the specific relation that LLM judges miss under the tested prompts.
4. **The dominant LLM error modes on strong_action_overclaim** (on the controlled silver-stage evaluation) are over-contradiction (mapping strong_action to contradiction_candidate — the LLM treats the action over-extension as a factual mismatch), over-milding (mapping strong_action to mild_scope_overclaim — the LLM recognizes scope expansion but misses the action escalation), and over-supporting (mapping strong_action to supported — the LLM treats the relevant-but-insufficient evidence as full support). R4's error mode is different: it tends to over-route supported → strong, producing false positives rather than false negatives on strong_action. This is a complementary error profile.

**This result should not be interpreted as R4 outperforms LLM judges overall.** On the controlled silver-stage evaluation, R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted screening signal on the high-risk boundary class, at the cost of lower overall macro-F1. **Two additional prompt designs (decision-tree, few-shot) are pre-registered for gold-subset evaluation in Table G3; if either closes the strong_action gap, the under-detection claim is downgraded per §VII.G criterion 3.**

### C. Boundary Audit Summary (Table 3)

**Table 3. Boundary audit summary (40-case author sanity audit, §V.D).** See `table_main_results_clean.csv`.

| Silver label | Reasonable | Questionable | Unclear | Total | Confusion type |
| --- | --- | --- | --- | --- | --- |
| supported | 7 | 0 | 0 | 7 | none |
| mild_scope_overclaim | 3 | 0 | 4 | 7 | mild_vs_strong |
| strong_action_overclaim | 5 | 5 | 10 | 20 | mild_vs_strong |
| contradiction_candidate | 0 | 0 | 6 | 6 | strong_vs_contradiction |
| **Total** | **15** | **5** | **20** | **40** | — |

**Root causes (25 questionable/unclear cases):**

| Root cause | Cases | % | Implication |
| --- | --- | --- | --- |
| mild_vs_strong_boundary_unclear | 12 | 48% | core taxonomy challenge; needs gold adjudication |
| strong_vs_contradiction_boundary_unclear | 6 | 24% | audit missed detail-swapping; decision tree fixes this |
| claim_too_abstract | 5 | 20% | claim generation issue, not taxonomy issue |
| audit_heuristic_too_conservative | 2 | 8% | audit too strict; silver label likely defensible |

- 25/40 (62.5%) of silver labels are flagged as questionable or unclear — a real signal that silver labels require independent gold adjudication before the LLM under-detection finding can be treated as established.
- The 25 cases are *not* all label noise — they reflect a mix of taxonomy boundary issues, audit heuristic limitations, and genuinely hard cases.
- strong_action_overclaim has the highest confusion rate (15/20 = 75%), mostly mild_vs_strong confusion. This is expected: strong_action is the most subtle class, and the boundary between mild and strong is the hardest to operationalize.
- The 25 questionable/unclear cases are retained in `high_risk_sample_bank.csv` as boundary cases for gold adjudication priority; `trusted_case_bank.csv` (18 cases, ≥4 per class) provides clear illustrative cases for paper examples — none claimed as gold.

### D. External Transferability Probe

We run a small gold-derived subset evaluation on SciFact and VitaminC. **This is an external transferability probe and sanity check, not a validation of the four-class evidence-sufficiency taxonomy.** Public gold labels are preserved as original; the mapping to supported/contradiction_candidate/unsupported_or_insufficient is derived and does not map to strong/mild labels.

| Dataset | Method | E1 Macro-F1 | E2 Macro-F1 |
| --- | --- | --- | --- |
| SciFact | TF-IDF claim+evidence | 0.3350 | 0.5111 |
| SciFact | NLI cross-encoder | **0.6895** | 0.6034 |
| SciFact | R4-compatible | 0.3549 | 0.5166 |
| VitaminC | TF-IDF claim+evidence | 0.4277 | 0.5184 |
| VitaminC | NLI cross-encoder | **0.6686** | 0.5691 |
| VitaminC | R4-compatible | 0.4568 | 0.5197 |

- SciFact best E1 macro-F1: 0.6895 (NLI cross-encoder, N=271 per seed). VitaminC best E1: 0.6686 (NLI cross-encoder, N=300 per seed).
- R4-compatible underperforms NLI on public data because (a) public datasets have no action-overclaim labels, so the strong-action route is inactive and R4 reduces to its contradiction + scope components; (b) R4 was not retrained on public data. The probe confirms that the contradiction + scope components run without crash on public data, **not** that the full R4 framework transfers competitively.
- Claim-only leakage is HIGH: claim-only TF-IDF is within 0.018–0.030 of claim+evidence TF-IDF, indicating that public data rewards claim-only shortcuts.
- Evidence sensitivity (E3) on VitaminC official contrastive pairs (300 per seed): support-score delta = 0.0226 ± 0.007, sensitivity rate 46.9%. On SciFact synthetic perturbation (209 per seed): delta = 0.0056 ± 0.014, sensitivity rate 45.5% (near zero, as expected for synthetic perturbations).

**What this transferability probe does and does not show:**

- R4-compatible methods run on public data without crash (contradiction + scope components transfer).
- NLI cross-encoder is a strong generic support/refutation baseline on public data.
- Public datasets **cannot** test the four-class evidence-sufficiency taxonomy (no action-overclaim labels).
- Public datasets **cannot** replace SimClaim gold evaluation.
- Public results are **transferability probes and sanity checks**, not benchmark superiority claims.

### E. Scalar Overstatement Baseline vs. Relation-Specific Screening (RIGOURATE-style Proxy)

A natural question raised by RIGOURATE [30] and ForceBench [35] is whether a single continuous scalar overstatement score can subsume the four-class relation taxonomy and provide equivalent screening signal — particularly for the high-risk `strong_action_overclaim` boundary class. This subsection reports a controlled silver-stage evaluation of that question. **All numbers in this subsection are computed on the controlled silver-stage evaluation against AI-preannotated, author-screened silver labels.** The full audit trail is in `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\`.

**Official RIGOURATE reproduction status (BLOCKED).** As of 2026-07-05, the official RIGOURATE code, data, and fine-tuned model weights are not publicly available. The arXiv v2 paper (12 Jan 2026) carries a placeholder `[Github/HF Link]` URL that has not been replaced; no GitHub repository, HuggingFace model, dataset release, or supplementary material was located via web search. A full official reproduction was therefore not possible from public resources. We instead construct a RIGOURATE-style scalar overstatement proxy baseline and explicitly label it as a proxy, NOT as the official RIGOURATE system. The proxy baseline is documented in `baseline_build_notes.md` and `official_reproduction_status.json` (with `blocked_reason` recorded for each unavailable artifact).

**Three RIGOURATE-style scalar proxy baselines.** We construct three scalar overstatement scores on the 444 SimClaim pairs:

- **(A) `rule_scalar_score`** — a cue-based 0–3 score (0=supported, 1=mild, 2=strong, 3=contradiction) using priority scoring on action/deployment/safety/policy/generalization/guarantee/always/fully/replace cues plus evidence-limitation cues. Completed for all 444 pairs. This is a hand-crafted baseline; it is NOT the official RIGOURATE score.
- **(B) `nli_scalar_score`** — BLOCKED. The HCM/NLI feature set required for this baseline (s_correct, contradiction, margin, entropy) is not present in the current repository (the `cese_ocn_hcm_v1` directory referenced in earlier working notes does not exist in the active tree). `blocked_reason` recorded for all 444 rows in `rigourate_style_scalar_scores.csv`. We do not fabricate a result for this baseline.
- **(C) `llm_scalar_proxy`** — an LLM-label-derived 0–3 score (supported=0, mild_scope_overclaim=1, strong_action_overclaim=2, contradiction_candidate=3) computed from existing GPT/DeepSeek parsed outputs (no paid API calls; reuses `llm_parsed_outputs_100.csv` and `llm_parsed_outputs_200.csv`). Available for 200/444 matched pairs. This is an LLM-label-derived proxy, NOT a true continuous overstatement score and NOT the official RIGOURATE score.

**Binary-task evaluation (4 tasks, controlled silver-stage evaluation).** We test whether the scalar scores can separate the four relation classes on four binary tasks: (1) supported vs. overclaim (mild+strong+contra); (2) mild vs. strong; (3) strong vs. contradiction; (4) strong vs. non-strong. ROC-AUC, PR-AUC, best-threshold positive-F1, precision/recall, and threshold sensitivity are reported in `scalar_baseline_binary_results.csv` and `scalar_baseline_threshold_sweep.csv`. Summary:

| Task | Baseline | N | ROC-AUC | PR-AUC | Best F1 | Best t | Precision | Recall |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| supported_vs_overclaim | rule_scalar | 444 | 0.5136 | 0.7563 | 0.7466 | 1.0 | 0.7546 | 0.7387 |
| supported_vs_overclaim | llm_scalar | 200 | 0.8533 | 0.9267 | 0.8281 | 1.0 | 1.0000 | 0.7067 |
| mild_vs_strong | rule_scalar | 222 | 0.5062 | 0.5016 | 0.6109 | 1.0 | 0.5122 | 0.7568 |
| mild_vs_strong | llm_scalar | 100 | 0.5874 | 0.5931 | 0.5741 | 1.0 | 0.5345 | 0.6200 |
| strong_vs_contradiction | rule_scalar | 222 | 0.5233 | 0.5209 | 0.5921 | 1.0 | 0.4940 | 0.7387 |
| strong_vs_contradiction | llm_scalar | 100 | 0.8512 | 0.7985 | 0.8400 | 3.0 | 0.8400 | 0.8400 |
| strong_vs_nonstrong | rule_scalar | 444 | 0.4971 | 0.2464 | 0.3844 | 1.0 | 0.2577 | 0.7568 |
| strong_vs_nonstrong | llm_scalar | 200 | 0.5154 | 0.2505 | 0.3974 | 1.0 | 0.2925 | 0.6200 |

**Head-to-head comparison against R4 (100 matched samples, 25 strong_action each).** We compare five methods on strong_action_overclaim identification. The full per-sample predictions and metrics are in `rigourate_style_vs_r4_results.csv` and `rigourate_style_vs_r4_cases.csv`.

| Method | Strong F1 | Strong Recall | Strong Precision | TP | FP | Review Burden | Macro-F1 (aux) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| rule_scalar (proxy) | 0.1364 | 0.12 | 0.158 | 3 | 16 | 19% | 0.2591 |
| GPT-5.5 standard | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5523 |
| GPT-5.5 structured (5-step) | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5543 |
| DeepSeek-V3 | 0.0769 | 0.04 | 1.0 | 1 | 0 | 1% | 0.5248 |
| **R4 frozen** | **0.3000** | **0.36** | 0.257 | 9 | 26 | 35% | 0.3280 |

Reference (silver 444, not on matched 100): R4 strong_F1 = 0.3967, strong_recall = 0.4562, strong_precision = 0.3791, macro-F1 = 0.4238.

**Required answers (all on the controlled silver-stage evaluation, validation-pending).**

1. **Can the scalar score identify overclaim (supported vs. overclaim)?** — A cue-based scalar (`rule_scalar_score`) cannot (ROC-AUC = 0.5136, chance-level). An LLM-derived scalar (`llm_scalar_proxy`) can (ROC-AUC = 0.8533), but only because the LLM judge itself can identify supported claims well; this is a broad-severity capability, not a fine-grained relation-typing capability. **Verdict: scalar can identify overclaim only when derived from a strong LLM; pure cue-based scalar cannot.**

2. **Can the scalar score reliably distinguish mild from strong_action?** — Neither scalar variant can. `rule_scalar_score` ROC-AUC = 0.5062 (chance); `llm_scalar_proxy` ROC-AUC = 0.5874 (weak, below 0.70). The scalar compresses the action-vs-scope distinction, which is exactly the high-risk boundary the four-class taxonomy is designed to isolate. **Verdict: NO. This is the critical failure mode that motivates fine-grained relation typing.**

3. **Can the scalar score replace the R4 strong_action route?** — On silver 444, R4 strong_F1 = 0.3967 vs. `rule_scalar` best-F1 = 0.3844 (R4 above by +0.0123). On matched 100, R4 strong_F1 = 0.3000 vs. `rule_scalar` = 0.1364 (R4 above by +0.1636). The `llm_scalar_proxy` appears to tie R4 on F1 (0.3974 vs. 0.3967), but its ROC-AUC on strong_vs_nonstrong is at chance (0.5154), meaning the apparent F1 is a threshold artefact, not genuine strong_action discrimination. **Verdict: NO. A scalar score cannot replace the R4 strong_action route.**

4. **Does R4 retain independent screening value on strong_action?** — Yes. R4 captures 8/24 strong_action cases that all three LLM judges (GPT standard, GPT structured, DeepSeek) miss on the matched 100. R4's strong_action F1 is 3–5× higher than any LLM judge under the tested prompts. The cost is lower overall macro-F1 (0.3280 vs. 0.5523) and higher review burden (35% vs. 1%), but this trade-off is intentional: R4 is a screening-oriented complement, not a replacement. **Verdict: YES. R4 retains clear screening value on the high-risk boundary class.**

5. **Are scalar overstatement scoring and relation-specific screening complementary?** — Yes. Scalar scores (especially LLM-derived) are good at the broad supported-vs-overclaim distinction (ROC-AUC = 0.85) and at strong-vs-contradiction (ROC-AUC = 0.85). Scalar scores CANNOT distinguish mild from strong (ROC-AUC ≤ 0.59) and cannot reliably identify strong_action (ROC-AUC ≤ 0.52 on strong_vs_nonstrong). R4 provides the missing signal: strong_F1 = 0.3967 vs. scalar/LLM ≤ 0.10 on matched samples. The two approaches address different sub-problems: scalar for broad severity ranking, relation-specific for high-risk action-overclaim screening. **This complementarity is the empirical justification for CESE-OCN's positioning as a fine-grained complement to (not replacement of) scalar overstatement scoring work like RIGOURATE.**

**Caveats (see also §IX).** (i) The RIGOURATE-style baselines are proxies, NOT the official RIGOURATE system; conclusions may shift when official RIGOURATE artifacts become available. (ii) The `nli_scalar_score` baseline is BLOCKED with `blocked_reason` recorded; no result is fabricated for it. (iii) `llm_scalar_proxy` is LLM-label-derived (mapped from predicted 4-class label), not a true continuous overstatement score; it inherits the LLM's under-detection pattern on strong_action. (iv) All evaluation is on silver labels (pre-gold); gold adjudication may shift conclusions. (v) SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus; the §VII.J realism audit addresses claim naturalness separately. (vi) The case-level analysis (`case_level_comparison.csv`, 100 matched cases) shows: both-wrong = 49/100 (dominant — both methods struggle), R4-right-scalar-wrong = 24/100, scalar-right-R4-wrong = 17/100, both-right = 10/100, mild/strong confusion = 35/100 — confirming that the mild-vs-strong boundary is the hardest distinction and that R4 and the scalar make partially non-overlapping errors.

**This subsection does not claim that R4 outperforms the official RIGOURATE system** (official RIGOURATE is not available for head-to-head comparison). It does not claim that scalar scoring is unnecessary (the LLM-derived scalar achieves ROC-AUC = 0.85 on the broad supported-vs-overclaim task). It claims only that, on the controlled silver-stage evaluation of the SimClaim diagnostic set, a scalar score — whether cue-based or LLM-derived — cannot reliably distinguish mild from strong_action, and R4 retains targeted screening value on the high-risk boundary class. This is a controlled silver-stage finding; the pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this pattern is treated as validated.

## VII. Pre-Registered Gold Validation Protocol

> This section specifies the protocol-locked gold validation: why gold is needed, what it will test, what metrics it will report, and what happens to the paper's claims if gold does not support the current silver-stage taxonomy. **No gold annotation has been performed.** All entries in Tables G1–G3 are marked `TO_BE_FILLED_AFTER_GOLD`. The pre-registered success and downgrade criteria are frozen in `gold_validation_protocol_section.md`. This section is the validation-pending protocol; the results will be filled in after the 50-sample gold pilot is completed. This is a protocol-locked validation mechanism, not a post-hoc tuning loop.

### A. Why Gold Is Needed

All 444 SimClaim labels are currently **silver** (AI-preannotated, author-screened). The author sanity audit (§V.D) flags 25/40 (62.5%) of audited silver labels as questionable or unclear, with strong_action_overclaim showing a 75% confusion rate. Every numeric result in §VI — on the controlled silver-stage evaluation, R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769, the +0.2231 gap — is computed against these silver labels. Without independent gold adjudication, we cannot tell whether the central silver-stage finding (R4 targets a relation that LLM judges miss under the tested prompts) reflects a real property of LLM judges or an artifact of silver label noise concentrated at the mild_vs_strong boundary. Gold adjudication is therefore the single most consequential next step — and it is pre-registered to ensure it is a validation mechanism, not a tuning opportunity.

### B. Gold Is for Validation, Not for Tuning

Gold labels will **not** be used to re-tune R4 thresholds, re-fit the decision tree, re-select router variants, or modify the taxonomy boundary rules. R4 thresholds (`t_contra = 0.48`, `t_strong = 0.535`, `t_svm = 0.51`) and the four-step decision tree (Figure 2) are already frozen. Gold labels will be used **only** as an independent evaluation reference against which the frozen silver-stage R4 and the frozen silver-stage LLM judge predictions are scored. This separation is essential: if gold were used to re-tune the method, the resulting numbers would no longer be a valid test of the silver-stage finding.

### C. Silver-Stage Evidence Is Frozen

The following silver-stage artifacts are frozen as of V3.10 and will not be regenerated, re-tuned, or modified in response to gold results:

- The 444-row SimClaim silver-label pilot set and its group-aware train/dev/test splits.
- The R4 frozen thresholds and the routing order (Figure 1).
- The four-step decision tree (Figure 2) and the boundary rules in `taxonomy_boundary_decision_tree.md`.
- The frozen R4 predictions on the 100 and 200 matched LLM-comparison samples.
- The frozen LLM judge predictions (DeepSeek-V3 200, GPT-5.5 standard 100, GPT-5.5 structured 100).
- The author sanity audit results (40 cases) and the 25 questionable/unclear root-cause distribution.

If gold adjudication reveals a serious taxonomy problem (e.g., mild_vs_strong κ < 0.40 — see §VII.G), the response is **not** to re-tune against gold, but to **revise the taxonomy and re-frame the paper's claims** — explicitly downgrading or retracting the strong_action class if the boundary is not reliably drawable. This is the protocol-locked safety mechanism.

### D. What Gold Will Test

The planned gold validation tests six pre-registered hypotheses, each tied to a specific silver-stage claim in this manuscript:

1. **H1 — Annotator agreement is sufficient to support the four-class taxonomy.** The silver-stage claim is that the four classes (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) are reliably distinguishable by trained annotators using the frozen decision tree. The pre-registered threshold is overall agreement ≥ 0.70 and Cohen's κ ≥ 0.45 (Table G1).
2. **H2 — The mild_vs_strong boundary is reliably drawable.** This is the boundary with the highest silver-stage confusion (12/25 questionable/unclear cases, 75% strong_action confusion rate). The pre-registered threshold is mild_vs_strong κ ≥ 0.40. Failure here triggers taxonomy revision (§VII.G).
3. **H3 — Silver labels are substantially consistent with gold labels.** The silver-stage finding (R4 > LLM on strong_action) is computed against silver. If silver-gold agreement is high, the silver-stage finding is supported; if not, the finding is downgraded. The pre-registered threshold is silver-gold agreement ≥ 0.70 and strong_action retention rate ≥ 0.60 (Table G2).
4. **H4 — The LLM under-detection pattern survives gold.** The silver-stage finding is that LLM judges (GPT-5.5, DeepSeek-V3) under-detect strong_action_overclaim (strong_F1 = 0.0769, recall 0.04). Gold will re-score the same frozen LLM predictions against gold labels. If LLM strong recall remains low (e.g., ≤ 0.20), the silver-stage finding is supported.
5. **H5 — R4 provides targeted complementary value on strong_action under gold.** The silver-stage finding is that R4 achieves strong_F1 = 0.3000 vs. LLM 0.0769 on matched 100. Gold will re-score the same frozen R4 predictions. The pre-registered expectation is that R4 strong recall remains meaningfully higher than LLM strong recall.
6. **H6 — R4 or an LLM+R4 hybrid improves screening recall.** A practical use of R4 is as a screening layer that flags potential action overclaims for human or LLM review. Gold will report false positives per true positive (Table G3) to test whether R4's false-positive cost is acceptable for this screening use.

### E. What Gold Will Report

Gold will populate three placeholder tables:

- **Table G1 (Annotation agreement)** — overall agreement, Cohen's κ, optional Krippendorff's α, per-boundary κ (supported_vs_mild, mild_vs_strong, strong_vs_contradiction), and unsure rate. See `gold_validation_placeholder_tables.csv`.
- **Table G2 (Silver-gold consistency)** — silver-gold agreement, strong_action retention rate, mild-to-strong shift, strong-to-mild shift, contradiction retention rate. See `gold_validation_placeholder_tables.csv`.
- **Table G3 (Gold-subset model evaluation)** — for each method (Flat baseline, NLI baseline, GPT standard, GPT decision-tree prompt, GPT few-shot prompt, DeepSeek, R4, LLM+R4 hybrid): macro-F1, strong precision, strong recall, strong F1, contradiction F1, false positives per true positive, status. See `gold_validation_placeholder_tables.csv`.

All entries are currently `TO_BE_FILLED_AFTER_GOLD`. No numeric values are pre-filled or guessed.

### F. Gold Subset

The gold pilot will use a 50-sample subset (`gold_pilot_candidate_50.csv`): 25 high-risk samples from `high_risk_sample_bank.csv` (concentrated at the mild_vs_strong and strong_vs_contradiction boundaries), 16 trusted samples from `trusted_case_bank.csv`, and 9 random samples from the remaining silver pool. Two annotators independently label under the frozen protocol; disagreements are adjudicated by a third annotator. Silver labels are hidden from annotators during labeling (`pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`). The adjudication protocol is in `adjudication_protocol_v1.md`. The 50-sample size is a pilot — it is sufficient to estimate per-boundary κ and to detect fatal taxonomy problems; a confirmatory study (300–500 pairs) is a separate follow-up effort. If the 50-sample pilot passes, the paper proceeds to the confirmatory study; if it fails, the taxonomy is revised first.

### G. Pre-Registered Downgrade Criteria

The following downgrade rules are **pre-registered** and frozen in `gold_validation_protocol_section.md`:

1. **mild_vs_strong κ < 0.40 → taxonomy must be revised.** If the mild_vs_strong boundary is not reliably drawable, the strong_action_overclaim class may need to be merged with mild_scope_overclaim, weakening the paper's central contribution. The paper would be re-framed as a three-class framework (supported / scope_overclaim / contradiction_candidate) rather than a four-class framework.
2. **strong_action retention < 0.50 → paper claim downgraded.** If gold labels convert most silver-stage strong_action cases to mild, the silver-stage finding (R4 > LLM on strong_action) becomes a finding about scope overclaim, not action overclaim. The paper would be re-framed accordingly.
3. **GPT few-shot or decision-tree prompt fixes strong_action → LLM under-detection claim downgraded.** If a different prompt design closes the strong_action gap, the silver-stage finding is prompt-specific rather than pattern-specific.
4. **R4 false positives too high → screening claim downgraded.** If R4 produces more than 10 false positives per true positive on gold, the screening use case is not viable.
5. **LLM+R4 hybrid gives no screening gain → complementarity claim downgraded.** If combining LLM and R4 does not improve screening recall over R4 alone, the complementarity positioning is weakened.
6. **mild_vs_strong κ ≥ 0.40 and strong_action retention ≥ 0.60 and LLM strong recall remains low → silver-stage findings supported.** This is the success path: the paper proceeds to a confirmatory submission with gold-validated numbers.

### H. Closing Position

**The downgrade criteria in §VII.G specify what happens if gold does not support the silver-stage findings.** Until gold results are available, all claims in this manuscript should be read as controlled silver-stage evidence, not as established properties of LLM judges or as a validated taxonomy. The gold validation slots (Tables G1–G3) are designed so that gold results can be inserted without restructuring the paper; if gold does not support the current taxonomy, the paper will be downgraded per §VII.G rather than re-tuned against gold. This is what "protocol-locked validation" means: the validation mechanism is fixed before the result is known.

### I. Proposed Gold-Realism Audit Extension

Because SimClaim uses generated counterfactual claim variants (§V.A), gold validation should assess both **relation-label agreement** and **claim realism / plausibility**. A claim variant may receive a unanimous relation label from two annotators yet still be too template-like, too extreme, or unnaturally worded to stand as a plausible scientific claim. If a substantial fraction of strong_action_overclaim cases are flagged as unrealistic, the silver-stage screening finding (R4 > LLM on strong_action) may hold on the diagnostic set but fail to transfer to natural scientific writing — a scope-limiting risk that the §VII.G downgrade criteria alone do not cover.

We therefore propose a **parallel gold-realism audit** with two fields per claim, collected alongside (not replacing) the relation label:

- **`claim_realism_score_1_to_5`** (integer 1–5): 1 = clearly unrealistic / not a scientific claim, 5 = clearly a plausible scientific claim a researcher might write.
- **`claim_realism_issue`** (single categorical tag): `none` | `too_template_like` | `too_extreme` | `unnatural_wording` | `not_scientific_claim` | `ambiguous_or_vague`.

The proposed audit protocol is:

1. Each annotator independently assigns `claim_realism_score_1_to_5` and `claim_realism_issue` for every claim in the gold pilot (not just disputed cases).
2. After adjudication, the gold set carries a final `claim_realism_score_1_to_5` (mean of the two annotators' scores, or adjudicated value if they disagree by ≥ 2 points) and a final `claim_realism_issue` (adjudicated).
3. Pre-registered realism reporting thresholds:
   - **Low-realism flag**: `claim_realism_score_1_to_5 ≤ 2` OR `claim_realism_issue ≠ none`.
   - **Class-level realism check**: if > 25% of claims in any class (especially strong_action_overclaim) receive a low-realism flag, the paper adds an explicit "realism caveat" to the corresponding §VI result and the §VIII screening-utility claim.
   - **Paper-level realism check**: if > 25% of all claims receive a low-realism flag, the paper's main claims are downgraded from "controlled silver-stage evidence on a diagnostic set" to "controlled silver-stage evidence on a synthetic diagnostic set with limited natural-claim transferability," and an additional §IX limitation item is added.

The realism-audit fields are **proposed** here, not yet collected. They are specified in the standalone file `proposed_gold_realism_extension.md` for annotator training and pilot protocol inclusion. The existing gold-pilot CSVs (`pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`, `adjudication_template.csv`) are **not** modified in V3.13; the realism fields will be added when the gold pilot is run.

This proposal does not change any §VI number, does not change any §VIII.D result, does not replace the §VII.G downgrade criteria, and does not constitute gold annotation. It is a protocol-level extension specifying what the gold pilot will additionally measure.

### J. Two-Layer Gold Protocol (Relation + Realism) — Upgraded from §VII.I

§VII.I proposed a parallel realism audit with two fields (`claim_realism_score_1_to_5`, `claim_realism_issue`). Building on that proposal and on the RIGOURATE-style baseline task's §9 gold-protocol extension (`D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\proposed_relation_realism_gold_protocol_v2.md`), we now specify a **two-layer gold protocol** that makes the relation label and the realism audit first-class annotation layers. **This is a protocol-level upgrade only — no gold annotation has been performed; no existing gold CSV is modified; no silver CSV is modified; the §VII.G downgrade criteria are not relaxed.** Layer 1 (relation label) is operationalised by the frozen `gold_pilot_protocol_freeze_v1` package (`D:\ocn\gold_pilot_protocol_freeze_v1\`, dated 2026-07-04, status: PROTOCOL FROZEN, annotation NOT begun), which contains the frozen annotation guideline, decision tree, boundary rules, 20 worked positive/negative examples, annotator training packet, two independent blind annotation templates (A and B with silver labels excluded), adjudication protocol, and agreement metric plan. Layer 2 (claim realism) extends the Layer 1 protocol with the three realism fields specified below; the Layer 2 protocol is to be run as a separate pass on the same annotated sample, with the same blinding and adjudication procedure.

**Why two layers.** SimClaim is a controlled counterfactual diagnostic set (§V.A): evidence spans are real, but claim variants are generated to instantiate specific evidence-sufficiency relations. Gold validation therefore has two distinct jobs: (Layer 1) verify that the *relation label* is reliably drawable by independent annotators using the frozen decision tree; (Layer 2) verify that the *claim itself* is realistic enough that a finding which holds on the diagnostic set is not an artefact of unnatural claim wording. Layer 1 without Layer 2 would allow a unanimous-but-unnatural claim to count as validated; Layer 2 without Layer 1 would allow a natural-but-mislabelled claim to count as validated. The two layers are independent by design.

**Layer 1 — relation label (unchanged from §VII).**

- **Field:** `gold_relation_label`
- **Values:** `supported` / `mild_scope_overclaim` / `strong_action_overclaim` / `contradiction_candidate`
- **Procedure:** Two-annotator independent review followed by adjudication for gold standard, per the existing §VII protocol. Boundary rules from the V3.12 taxonomy apply. Annotators see (claim_text, evidence_text, domain) only; silver labels, R4 predictions, LLM predictions, and group structure are hidden.
- **Quality control:** Cohen's κ (per class, per boundary) and Krippendorff's α reported. Adjudication disagreements recorded with reasons. The §VII.G downgrade criteria (mild_vs_strong κ < 0.40 → taxonomy revised; strong_action retention < 0.50 → claim downgraded) apply to Layer 1.

**Layer 2 — claim realism (NEW, operationalised from §VII.I).**

- **Field 2a:** `claim_realism_score_1_to_5` (integer 1–5).
  - 1 = clearly unrealistic (would never appear in a real scientific paper; extreme superlatives, mechanical negation insertions, placeholder phrasing).
  - 2 = mostly unrealistic (noticeable unnatural wording but recognisable as a scientific claim).
  - 3 = borderline (plausible with subtle unnatural cues — overly template-like opening, slightly forced action cues).
  - 4 = mostly natural (reads naturally with minor quirks).
  - 5 = clearly plausible (indistinguishable from a real author-written scientific claim).
  - Annotators rate realism INDEPENDENTLY of the relation label. A claim can be `supported` and `realism_score=1` (unnatural but accurate) or `strong_action_overclaim` and `realism_score=5` (natural but overstated). Realism is about *whether a real author could write this claim*, not about *whether the claim is correct*.

- **Field 2b:** `claim_realism_issue` (single-select categorical).
  - `none` / `too_template_like` / `too_extreme` / `unnatural_wording` / `not_scientific_claim` / `contradiction_too_mechanical` / `strong_action_too_forced` / `mild_strong_boundary_unclear` / `ambiguous_or_vague`.
  - Select the *primary* realism issue. If multiple issues are present, annotators record the most salient one in this field and describe others in a free-text notes field.

- **Field 2c:** `claim_realism_usable_for_paper` (`yes` / `no`, derived not annotated).
  - `yes` — claim can be used in paper-valid tables and analyses (realism_score ≥ 3 AND no critical realism issue).
  - `no` — claim should be excluded from paper-valid tables and reported only in diagnostic/sensitivity analyses (realism_score < 3 OR a critical realism issue such as `not_scientific_claim` or `contradiction_too_mechanical`).
  - This is a derived field computed by the analysis pipeline after annotation; annotators do NOT set it directly.

**Annotation workflow.**

1. **Sampling:** All 444 silver pairs are candidates for gold annotation. Priority sampling: all 111 `strong_action_overclaim` cases first (highest realism risk per the §8 audit: 9.0% heuristic realism flag rate vs. 4.7% overall), then a stratified sample of the other three classes.
2. **Annotators:** Two independent annotators per claim, both with domain expertise in ML/NLP. A third adjudicator resolves disagreements in either layer.
3. **Blinding:** Annotators see (claim_text, evidence_text, domain) only. Silver labels, R4 predictions, LLM predictions, and group structure are hidden.
4. **Order:** Layer 1 (relation label) and Layer 2 (realism) are annotated in **separate passes** to avoid anchoring. Order is randomised per annotator.
5. **Adjudication:** Disagreements in either layer are adjudicated by the third annotator. Adjudication reasons are recorded.
6. **Storage:** Gold annotations are stored in a separate CSV from silver. The silver CSV is NOT modified.

**Pre-registered realism thresholds (frozen before gold collection).**

- **Class-level threshold:** If more than 25% of claims in any silver-label class have `claim_realism_score_1_to_5 ≤ 2`, that class is flagged for paper-validity review. The paper adds an explicit "realism caveat" to the corresponding §VI result and the §VIII screening-utility claim.
- **Paper-level threshold:** If more than 25% of all gold-annotated claims have `claim_realism_score_1_to_5 ≤ 2`, the paper's main claims are downgraded from "controlled silver-stage evidence on a diagnostic set" to "controlled silver-stage evidence on a synthetic diagnostic set with limited natural-claim transferability," and an additional §IX limitation item is added.

These thresholds are pre-registered before gold collection and cannot be relaxed after results are known.

**Heuristic realism pre-screen (already conducted, NOT gold).** A heuristic pattern-based realism audit on all 444 SimClaim silver claims (`claim_realism_audit_queue.csv`, `claim_realism_audit_summary.md`) flagged 21/444 (4.7%) at the paper level and 10/111 (9.0%) for the `strong_action_overclaim` class. Both are below the 25% pre-registered threshold, but the `strong_action_overclaim` rate is non-trivial and motivates prioritising that class in gold sampling. **This heuristic pre-screen is NOT gold and does NOT pre-judge the gold result; it only informs the sampling order.**

**Implications for paper.**

- This proposal does NOT create gold.
- This proposal does NOT modify existing silver CSVs.
- This proposal does NOT modify V3.12 paper text.
- This proposal does NOT change the frozen R4 method or thresholds.
- This proposal does NOT call any API.
- This proposal does NOT claim SimClaim claims as natural claims.
- This proposal does NOT claim silver labels as gold.
- When gold is collected under this two-layer protocol, the paper will report: (a) gold relation-label results in Tables G1–G3 (already pre-registered in §VII); (b) gold realism distribution in a new appendix table; (c) sensitivity analysis excluding low-realism claims.
- If realism thresholds are breached, the paper adds a realism caveat and reports sensitivity results.
- If realism thresholds are NOT breached, the paper states that SimClaim claims pass the pre-registered realism check and proceeds with the main tables as-is.

**Relationship to RIGOURATE realism considerations.** RIGOURATE uses natural author-written claims from ICLR/NeurIPS abstracts and introductions, so realism is not a concern for RIGOURATE. SimClaim uses generated counterfactual claim variants, so realism IS a concern. This two-layer protocol is the falsifiable mechanism that addresses the realism risk: if SimClaim claims are systematically unnatural, the protocol will detect it and trigger a sensitivity analysis or a paper-level caveat.

## VIII. Discussion

### A. What R4 Adds Despite Lower Macro-F1

A natural objection to the under-detection finding is: "LLMs have higher macro-F1, so they are better overall." This objection is correct — on the controlled silver-stage evaluation, LLM judges **are** better overall (GPT-5.5 macro-F1 = 0.5523 vs. R4 = 0.3280 on matched 100 samples, a 0.22 gap). We do not dispute this. The point is that macro-F1 averages over four classes, three of which (supported, mild_scope_overclaim, contradiction_candidate) are well-handled by LLM judges. The fourth class — strong_action_overclaim — is the high-risk boundary class for scientific claim calibration, because it corresponds to cases where a claim is *actionable* but the evidence is *insufficient* for that action. A model that misses strong_action_overclaim may fail on cases that are consequential for scientific writing quality, even if its overall macro-F1 is high.

R4's value is **relation-specific**: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. This is a screening-oriented complement, not a competitive one. A combined system — LLM judge for supported/mild/contradiction, R4 for strong_action — could potentially exploit this complementarity, though we leave that to future work.

**R4 is not intended to maximize overall macro-F1. Its role is to screen for strong_action_overclaim candidates missed by LLM judges.** On the controlled silver-stage evaluation, R4 produces approximately 122 false positives (98 supported → strong + 24 mild → strong) against about 25 true strong_action cases in the silver-stage matched analysis, yielding an estimated FP/TP ratio around 4.9. **This is not acceptable as a final automatic labeler, but is acceptable as a high-recall screening layer for human or LLM-assisted review.** Whether the macro-F1 gap is an acceptable trade-off depends on the downstream use case — for action-overclaim monitoring where missing a strong_action case is costly, the trade-off is favorable; for generic claim verification, an LLM judge alone is preferable. The screening viability will be re-evaluated under gold in Table G3 (FP/TP ratio against gold labels, pre-registered threshold ≤ 10 in §VII.G).

### B. Why strong_action Is Difficult for LLM Judges

Action-overclaim is the core hard case because it sits between support and contradiction. The evidence is relevant and non-contradictory, but it does not justify the action, deployment, safety, or generalization asserted by the claim. Generic NLI signals do not separate "supports a finding" from "supports the action claimed", because both are entailment-like at the factual level. LLM judges, trained on generic factuality, tend to map these cases to supported, mild_scope_overclaim, or contradiction_candidate — all of which miss the action-escalation signal.

The pattern is observed across the two tested models. Both GPT-5.5 and DeepSeek-V3 converge on strong_F1 = 0.0769 (recall = 0.04 = 1/25) on the controlled silver-stage evaluation, and this structured 5-step decomposition prompt design does not change this. This suggests an under-detection pattern observed under the tested prompts, not a single-model quirk. We do not claim this is a fundamental limit of LLMs — it is prompt/model/sample specific and computed against silver labels (which the author sanity audit flags as 62.5% questionable/unclear) — but under the tested prompts, the pattern is observed across the two tested models and suggests that a relation-specific router can complement black-box LLM judges. R4's design directly addresses this: the strong-action escalation route uses action-gap features (the gap between the action implied by the claim and the action supported by the evidence) in addition to NLI signals. The ablation confirms that NLI and action-gap features are complementary: combining them improves strong expert F1 over either alone (0.4209 vs. 0.3934 NLI-only, 0.3648 action-gap-only). Other prompt designs (few-shot, chain-of-thought, tool-augmented) remain untested and might behave differently. **The pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this silver-stage pattern is treated as established.**

### C. Boundary Cases Are Part of Evidence Sufficiency

A reviewer might argue that the 25/40 questionable/unclear audit rate means the taxonomy is too subjective to be useful. We disagree, but we state the argument carefully.

Evidence sufficiency calibration is *inherently a boundary task*. The four classes are not disjoint categories with sharp edges — they are regions on a continuous space of claim-evidence strength mismatch. The hardest boundaries (mild-vs-strong, strong-vs-contradiction) are where the taxonomy is most useful *and* most uncertain. A 62.5% questionable/unclear rate on an audit that *deliberately oversampled* strong_action_overclaim (20/40 = 50% of the audit sample, vs. 25% in the balanced set) is not evidence that the taxonomy is broken — it is evidence that the taxonomy surfaces the cases where human judgment is most needed.

The root cause analysis supports this interpretation: 12/25 (48%) are mild_vs_strong_boundary_unclear (the core taxonomy challenge, expected to be hard); 6/25 (24%) are strong_vs_contradiction_boundary_unclear (the audit heuristic missed detail-swapping; the decision tree now operationalizes this); 5/25 (20%) are claim_too_abstract (a claim generation issue, not a taxonomy issue); 2/25 (8%) are audit_heuristic_too_conservative (the audit was too strict, not the labels too weak). Only a small fraction are candidates for *likely label noise*. The majority are genuinely hard boundary cases that any annotation scheme would struggle with. This means: (1) the aggregate silver-stage pattern (R4 > LLM on strong_action) may hold even if individual labels shift under gold adjudication — but this is not guaranteed and is the subject of §VII; (2) the paper's claims are limited to aggregate silver-stage findings, not individual case correctness; (3) trusted cases (`trusted_case_bank.csv`) are used for paper examples; high-risk cases (`high_risk_sample_bank.csv`) are used for risk disclosure. The paper does not hide the 25 questionable/unclear cases — it reports them, diagnoses their root causes, and flags them as gold adjudication priority.

### D. Robustness and Credibility Checks Before Gold Adjudication

**These checks are non-gold robustness analyses that strengthen but do not validate. They do not replace gold adjudication (§VII).** All numeric results in this subsection are computed on already-existing silver-stage data, predictions, and scores — no new experiments, no API calls, no new model training, no threshold retuning, and no gold annotation. The three checks below test whether V3.11's main claims are (i) evidence-dependent rather than claim-only shortcuts, (ii) screening-useful despite R4's lower macro-F1, and (iii) robust to simulated strong-label shift of the kind gold adjudication may induce. They strengthen the silver-stage *relative* pattern (R4 > LLM on strong_action); they do not validate absolute numbers, which remain silver-stage pending §VII.

#### A. Evidence Necessity Check

This check tests whether the task and method are evidence-dependent rather than claim-only shortcuts. We use a two-layer analysis on existing data: (Layer A) a pre-existing NLI audit on 444 SimClaim samples comparing model accuracy under correct vs. perturbed evidence, and (Layer B) a TF-IDF cosine similarity sanity check between claim and evidence under each condition.

Under Layer A (NLI audit, 444 samples), correct-evidence accuracy is 0.4324, while perturbed conditions drop substantially: empty evidence = 0.2545, shuffled evidence = 0.3851, same-domain wrong evidence = 0.2568. The accuracy drops under perturbation (correct→empty: −0.1779, correct→same_domain_wrong: −0.1757, correct→shuffled: −0.0473) suggest the task is evidence-sensitive: perturbing the evidence changes the calibration outcome, which is inconsistent with a claim-only shortcut.

Under Layer B (TF-IDF cosine similarity, same 444 samples), correct-evidence mean similarity is 0.4131, while empty evidence = 0.0000 and same-domain wrong evidence = 0.0124. The shuffled-evidence TF-IDF cosine is identical to correct-evidence by construction, because TF-IDF is a bag-of-words representation and shuffled evidence preserves the same token multiset; the shuffled condition is therefore discriminated by the Layer A NLI audit (which is order-sensitive), not by Layer B. The TF-IDF/NLI correlation across conditions is r = −0.2736, which is expected rather than contradictory: TF-IDF measures surface lexical overlap, while NLI s_correct measures semantic entailment (which can hold even with low lexical overlap, e.g., paraphrase or abstraction). The two signals probe different dimensions of the claim–evidence relation and are complementary, not redundant.

**Interpretation.** The evidence perturbation results *suggest* the task is evidence-sensitive and that the method responds to evidence content. We do *not* claim this proves R4 fully relies on evidence in all cases — Layer A uses a pre-existing audit on the same SimClaim backbone but an earlier dataset version, and Layer B is a surface-level sanity check. The combined pattern (audit accuracy drops + TF-IDF similarity drops under content-changing perturbation) is consistent with evidence dependence and rules out the strongest form of claim-only shortcut, but does not establish full evidence reliance.

#### B. Screening Utility Test

This check tests whether R4 is useful as a screening-oriented complement for strong_action_overclaim, despite its lower overall macro-F1. Using frozen R4 predictions on the matched-100 set (25 true strong_action samples):

- R4 predicted strong = 35; TP = 9; FP = 26; FN = 16.
- Precision = 0.257; recall = 0.360; positive-F1 = 0.300.
- FP/TP ratio = 2.89, below the pre-registered threshold of 10 (§VII.G).
- Review burden = 35.0% (a human reviewer would need to check 35 of 100 samples).
- R4 captures 8 strong_action cases that both tested LLM judges missed on the same matched-100 set.

The actual false-positive breakdown by original silver class is: supported → strong = 12, mild_scope_overclaim → strong = 13, contradiction_candidate → strong = 1 (total FP = 26). The remaining 9 R4-predicted-strong samples whose silver label is strong_action_overclaim are true positives, not false positives.

**Interpretation.** R4 provides targeted recall-improving screening signal for strong_action_overclaim: it captures 8 cases the tested LLM judges missed, at an FP/TP ratio of 2.89 (below the pre-registered screening threshold). R4 is *not* a final automatic labeler — the 26 false positives require human or LLM-assisted adjudication, which is exactly the gold validation protocol in §VII. We do *not* claim R4 is a high-recall detector without qualification: recall is 0.360 (9/25), which is a moderate, not high, recall rate. The screening value is operational (FP/TP below threshold, captures LLM-missed cases), not a claim that R4 is a standalone strong_action detector. All counts depend on silver labels and may shift under gold adjudication.

#### C. Label-Shift Stress Test

This check tests how much the silver-stage strong_action screening claim can withstand if gold adjudication relabels a fraction of silver strong_action as mild_scope_overclaim. For each retention rate r, we randomly relabel (1−r) of silver strong_action as mild_scope, recompute binary strong_action F1 for R4 and the LLM judge, and repeat for 1000 bootstrap resamples on the matched-100 set (n_strong = 25). R4 predictions and LLM predictions are not retrained or retuned.

| Retention | R4 F1 (mean, 95% CI) | LLM F1 (mean) | Δ(R4−LLM) | Δ 95% CI | R4 wins % | Statistical strength |
|---|---|---|---|---|---|---|
| 70% | 0.2451 [0.1509, 0.3028] | 0.0759 | +0.1692 | [+0.083, +0.264] | 100.0% | robust |
| 60% | 0.2184 [0.1200, 0.3200] | 0.0776 | +0.1408 | [+0.035, +0.280] | 98.6% | marginal-positive (CI lower bound just above 0) |
| 50% | 0.1843 [0.0851, 0.2979] | 0.0706 | +0.1137 | [−0.026, +0.255] | 94.2% | positive but statistically weaker / CI crosses zero |
| 40% | 0.1612 [0.0444, 0.2667] | 0.0776 | +0.0835 | [−0.093, +0.222] | 70.1% | not significant (CI crosses zero) |

The break-even retention — where the Δ 95% CI first crosses zero — is approximately 0.5. At 70% retention, the R4 advantage is robust. At 60% retention, the R4 advantage is marginal-positive: the point estimate is +0.1408 and R4 wins 98.6% of bootstraps, but the CI lower bound (+0.035) is just above zero, so this should be read as a directional signal rather than a fully confirmed effect. At 50% retention, the point estimate remains positive (+0.1137) and R4 wins 94.2% of bootstraps, but the Δ 95% CI crosses zero ([−0.026, +0.255]); this is a positive-but-statistically-weaker result and must *not* be reported as a robust pass. Below 50% retention, the CI clearly crosses zero and the advantage is not statistically distinguishable from zero.

The point-estimate dominance persists down to low retention because the LLM judge's strong_action F1 is already near zero (~0.077) under the tested prompts: shrinking the positive set hurts R4's precision but cannot help the LLM, which rarely predicts strong_action at all. However, point-estimate dominance is not the same as statistical robustness — at 50% retention the CI crosses zero, so the advantage is directional, not confirmed.

**Interpretation.** If gold strong_action retention is around 60% or higher, the silver-stage screening claim has stronger support; at 50%, the point estimate remains positive but uncertainty crosses zero; below 50%, the paper should downgrade according to the pre-registered criteria in §VII.G. This sets a quantitative gold-pilot success bar: gold retention ≥ 70% → robust; 60% → marginal-positive; 50% → positive-but-weaker (CI crosses zero); < 50% → downgrade per §VII.G. The simulated label shift is a sensitivity probe, not gold data; it does not replace gold adjudication.

#### Summary of §VIII.D

The three checks provide complementary non-gold support: (A) the task is evidence-sensitive, not a claim-only shortcut; (B) R4 provides targeted recall-improving screening signal for strong_action_overclaim at an operationally acceptable FP/TP ratio; (C) the silver-stage screening claim has quantified robustness to simulated strong-label shift, with a pre-registered break-even threshold (~50% retention) that ties directly to the §VII.G downgrade criteria. These strengthen the high-standard framework by (i) grounding the task in evidence dependence, (ii) giving R4's screening role operational meaning, and (iii) quantifying the gold risk via a retention threshold. They do not validate absolute numbers, do not replace gold adjudication, and do not change the fact that R4's overall macro-F1 remains lower than the LLM judges.

### E. What Remains Unresolved

The most consequential unresolved issue is **independent gold adjudication** (specified in §VII, not yet performed). All 444 SimClaim labels are still silver. The V3.5 root cause analysis shows that 12/25 questionable/unclear cases are *genuinely hard boundary cases* (mild_vs_strong), which means even independent annotators may disagree on these cases. The decision tree (Figure 2) operationalizes the boundary but does not resolve it — 12 cases remain ambiguous even with the decision tree. If gold adjudication reveals that the mild/strong boundary is not reliably drawable (κ < 0.4 on this boundary), the strong_action_overclaim class itself may need to be merged with mild, which would weaken the paper's central contribution.

The decision tree is a *labeling aid*, not a validated annotation scheme. It has not been tested against gold labels (because no gold labels exist yet). It may misclassify cases that the decision tree's steps yield ambiguous results for, over-operationalize boundaries that are actually more nuanced, or introduce new biases (e.g., treating all detail-swapping as contradiction, when some detail-swapping may be mild or strong). The 18 trusted illustrative cases are *not* gold — "reasonable" by author audit is not the same as "correct" by independent adjudication. A small fraction of questionable/unclear cases (5/25) are `claim_too_abstract`, indicating that the claim generation process sometimes produces claims too abstract to clearly map to the taxonomy. These are claim generation problems, not taxonomy problems, but they affect label quality. Until gold adjudication (§VII), decision-tree validation, prompt robustness sweeps, and open-source LLM replications are completed, the current results are reported as controlled silver-stage evidence, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall.

### F. Why Fine-Grained Relation Typing Is Valuable

A natural question is: *why decompose evidence-sufficiency mismatch into four relation types at all, rather than producing a single continuous overstatement score (as in RIGOURATE [30]) or a contrastive preference signal (as in ForceBench [35])?* The answer is that **different overclaim relations have different risk semantics and different downstream screening needs**, and a single score or paired-claim preference can collapse distinct failure modes.

Unified overstatement scores are useful, but they may collapse different failure modes:

- **mild_scope_overclaim**: the claim mildly over-extends the scope of the evidence — a writing-strength issue. The evidence supports a finding, but the claim generalizes slightly beyond it. The downstream intervention is editorial: tone down the claim, hedge the scope, or add a qualifier.
- **strong_action_overclaim**: the claim asserts an action, deployment, safety, policy, or operational conclusion that the evidence does not justify — a *risk-bearing* issue. The downstream intervention is not just editorial; the claim may mislead deployment decisions, safety assessments, or policy framing if left unchecked. The cost of a missed strong_action_overclaim is qualitatively different from the cost of a missed mild_scope_overclaim.
- **contradiction_candidate**: the evidence conflicts with the claim on a factual or directional dimension — a *correctness* issue. The downstream intervention is to fix the claim or fix the evidence; this is the relation most aligned with traditional NLI/claim-verification.

Therefore, **strong_action_overclaim is not just "a mild overclaim with a higher score"** — it is a relation with different risk semantics and different screening needs. A continuous score cannot distinguish "this claim is slightly too strong" from "this claim asserts deployment readiness the evidence does not support" without an additional relation-type layer. A contrastive paired-claim test can probe force-sensitivity but does not, by itself, output which type of mismatch a single claim has. This is why a relation-type decomposition — supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate — is operationally valuable: it lets a screening system flag the high-risk action-overclaim sub-class for priority review, rather than mixing it with milder scope-expansion cases that need only editorial intervention.

This argument is the *taxonomy-level* reason for the four-class decomposition, independent of any particular model's performance on it. The §VI silver-stage results show that R4 exploits this decomposition to improve strong_action recall at the cost of macro-F1, but the taxonomy-level argument does not depend on R4 specifically — any downstream system that needs to flag high-risk action overclaims separately from mild scope expansion benefits from this decomposition. Whether the four-class decomposition is reliably drawable by human annotators is the subject of the §VII gold adjudication.

## IX. Limitations

This work is a **framework-level contribution with controlled silver-stage evidence**, not a confirmatory benchmark. The limitations below define the boundary of what the current results do and do not support.

1. **Silver labels are validation-pending, not gold.** The current dataset uses AI-preannotated, author-screened silver labels, not fully adjudicated gold. The author sanity audit (§V.D) flags 25/40 (62.5%) of silver labels as questionable or unclear, with strong_action_overclaim having a 75% confusion rate. All numeric results are controlled silver-stage findings. We do not claim gold/human-audited performance, human kappa, or final benchmark status from silver data alone. The LLM under-detection finding (§VI.B) is computed against these silver labels and must be interpreted as controlled silver-stage evidence, pending independent gold adjudication (§VII).

2. **Author sanity audit is preliminary, not independent adjudication.** The audit in §V.D is a qualitative plausibility check by the authors, not independent human annotation with reported inter-annotator agreement. It flags label uncertainty but does not resolve it. Independent gold adjudication (two-annotator + adjudication, with Cohen's κ or Krippendorff's α) is required before the LLM under-detection finding can be treated as established. The planned gold pilot will prioritize the boundary cases in `high_risk_sample_bank.csv`, using the decision tree (Figure 2) as a starting operationalization.

3. **LLM results are prompt/model/sample specific.** The GPT-5.5 and DeepSeek-V3 results are single-run, temperature 0, on ≤200 samples, under specific prompts. A different model, prompt, or sample may behave differently. We do not claim that "LLMs cannot solve strong_action_overclaim" — only that under the tested prompts, on the current silver diagnostic set, the pattern is observed across the two tested models. The structured 5-step decomposition result is a single prompt design; other decompositions (few-shot, chain-of-thought, tool-augmented) are untested and might behave differently.

4. **R4 is not a general-purpose LLM judge replacement.** On matched 100 samples (controlled silver-stage evaluation), R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523 (gap 0.22). R4 is a relation-specific screening-oriented complement, not a general-purpose classifier. It sacrifices macro-F1 for strong_action recall. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted screening signal on the strong_action_overclaim relation, at the cost of lower overall macro-F1. R4 over-routes supported → strong (98 false positives) and mild → strong (24 false positives), a trade-off for improved strong recall.

5. **Taxonomy boundary remains challenging.** The mild/strong boundary remains the central annotation challenge. The audit shows 12/25 questionable/unclear cases are mild_vs_strong_boundary_unclear, and strong_action has a 75% confusion rate. The decision tree (Figure 2) operationalizes the boundary, but 12 cases remain genuinely ambiguous. The strong_action numeric results (on the controlled silver-stage evaluation, R4 strong-F1 = 0.3967, LLM strong-F1 = 0.0769) should be read as controlled silver-stage evidence on a hard boundary, not as stable benchmark numbers. The planned gold pilot (§VII) will use two annotators with adjudication specifically on mild-vs-strong cases, and report inter-annotator agreement separately for this boundary.

6. **External transferability probe does not validate the four-class taxonomy.** SciFact and VitaminC use support/refute/NEI labels and do not contain action-overclaim or scope-overclaim labels. External results validate only generic support/refutation transfer and evidence-sensitivity sanity, **not** the SimClaim-specific four-class escalation task. Public data cannot replace SimClaim gold evaluation. R4-compatible underperforms NLI on public data because the strong-action route is inactive by design.

7. **This manuscript is a framework-level contribution with a protocol-locked validation mechanism.** The gold validation section (§VII) is specified but not yet populated; all gold-related entries are marked `TO_BE_FILLED_AFTER_GOLD`. Final submission claims will be revised after gold results are available. If gold does not support the current taxonomy, the paper will be downgraded per the pre-registered criteria in §VII.G rather than re-tuned against gold. This is the protocol-locked safety mechanism.

8. **The three credibility checks in §VIII.D are non-gold robustness analyses and do not replace independent gold adjudication.** The Evidence Necessity Check (§VIII.D.A) uses a pre-existing NLI audit on the same SimClaim backbone but an earlier dataset version, and the TF-IDF sanity check is a surface-level probe; together they *suggest* evidence sensitivity but do not prove full evidence reliance. The Screening Utility Test (§VIII.D.B) reports FP/TP and recall computed against silver labels, which may shift under gold. The Label-Shift Stress Test (§VIII.D.C) is a simulated sensitivity probe — the relabeled strong_action samples are *not* gold data, and the 50% retention result has a Δ 95% CI that crosses zero and must not be reported as a robust pass. None of these checks validate absolute numbers or substitute for the §VII gold adjudication.

9. **Differentiation from RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not empirical-headto-head.** This work does not run a direct experimental comparison against RIGOURATE [30], ForceBench [35], or CLAIM-BENCH [28]. The positioning in §II.A and Table X is based on the published formulations of those systems and on the conceptual output-type / input-form differences. A direct head-to-head evaluation would require running RIGOURATE-style scoring, ForceBench-style contrastive preference, and CLAIM-BENCH-style extraction-validation on SimClaim, which is outside the scope of this paper. The "complementary" relation claimed in §II.A is therefore a *conceptual* complementarity, not an empirically demonstrated one. Until a head-to-head evaluation is performed, the differentiation claim should be read as a positioning argument, not as a benchmarked advantage.

10. **SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus.** As stated in §V.A, SimClaim's four-way balanced design is a deliberate construction for pressure-testing boundary recognition under matched evidence; it does not estimate the natural prevalence of strong_action_overclaim or contradiction_candidate in real scientific writing. The proposed gold-realism audit (§VII.I, `proposed_gold_realism_extension.md`) is a protocol-level extension to assess claim realism alongside relation-label agreement, but it has not yet been run. Until the realism audit is completed, the silver-stage screening finding (R4 > LLM on strong_action) should be read as holding on the *diagnostic* set, with limited natural-claim transferability evidence. If the realism audit flags > 25% of strong_action_overclaim cases as low-realism, the screening claim will be downgraded per §VII.I.

11. **The RIGOURATE-style scalar baseline (§VI.E) is a proxy, not an official RIGOURATE reproduction.** As of 2026-07-05, the official RIGOURATE code, data, and fine-tuned model weights are not publicly available (arXiv v2 carries a placeholder `[Github/HF Link]` URL). The §VI.E scalar baselines (rule_scalar_score, llm_scalar_proxy) are explicitly labelled as proxy; the nli_scalar_score baseline is BLOCKED with `blocked_reason` recorded (HCM/NLI features not present in the active repository). Conclusions in §VI.E — that a scalar score cannot reliably distinguish mild from strong_action and that R4 retains targeted screening value — may shift when official RIGOURATE artifacts become available and a head-to-head comparison is possible. The §VI.E comparison against RIGOURATE, ForceBench, and CLAIM-Bench remains positioning-level for those three systems; only the proxy scalar baseline is empirically compared here, and it is NOT the official RIGOURATE system. We do not claim that R4 outperforms the official RIGOURATE system; we claim only that, on the controlled silver-stage evaluation of the SimClaim diagnostic set, a scalar score — whether cue-based or LLM-derived — cannot reliably distinguish mild from strong_action, and R4 retains targeted screening value on the high-risk boundary class.

Additional practical limitations: (a) small dataset (444 pairs, ~16 test per seed); (b) single-run LLM comparison with no variance estimate; (c) GPT-5.5 accessed via third-party proxy, not official OpenAI API; (d) cross-domain generalization is not confirmed beyond the six SimClaim domains; (e) LLM judge results are labeled "small-sample controlled evaluation, N ≤ 200" and are never merged with SimClaim main results or claimed as gold standard; (f) the comparison against RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not a head-to-head empirical benchmark; (g) the RIGOURATE-style scalar baselines in §VI.E are proxies, not official RIGOURATE; (h) the nli_scalar_score baseline is BLOCKED with `blocked_reason` recorded; (i) the heuristic realism pre-screen (§VII.J) is pattern-based and NOT a substitute for human realism annotation.

These limitations bound the strength of the claims — they do not invalidate the framework. The contribution is a falsifiable framework, a frozen main method whose numeric claims are constrained by the paper-ready result pack, and a protocol-locked validation mechanism — positioned as a screening-oriented complement to LLM judges rather than a competitive replacement.

## X. Conclusion

This work frames CESE-OCN as a **fine-grained evidence-sufficiency relation diagnosis framework** for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field. The core thesis is that scientific claim verification should not only ask whether evidence is related to a claim, but whether the evidence is *sufficient for the strength of the claim* — in particular when the claim asserts action, deployment, safety, or generalization conclusions; and that this calibration question benefits from a *relation-type decomposition* (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) rather than a single continuous overstatement score alone.

On the controlled silver-stage evaluation, the frozen R4 conservative strong router provides targeted value for **strong_action_overclaim**: it improves strong-action positive-F1 from 0.2408 to 0.3967 (+0.1559, CI [0.1058, 0.1988], 10/10 seeds positive) on the silver-label pilot set, while preserving contradiction and escalation performance. On matched-sample LLM judge comparisons, under the tested prompts, both GPT-5.5 (standard and structured) and DeepSeek-V3 under-detect strong_action_overclaim (strong_F1 = 0.0769, recall 0.04 = 1/25), while R4 achieves strong_F1 = 0.3000 (absolute gap +0.2231) on the same samples. This structured 5-step decomposition prompt design does not improve strong_action detection, suggesting that this prompt-engineering approach alone does not fix the under-detection pattern under the tested setting.

**R4 is positioned as a screening-oriented complement to black-box LLM judges, not a replacement and not a state-of-the-art overstatement detector.** On the controlled silver-stage evaluation, LLM judges retain substantially higher overall macro-F1 (GPT-5.5: 0.5523 vs. R4: 0.3280 on matched 100) and contradiction-F1; R4 targets the specific high-risk boundary class they miss under the tested prompts, at the cost of lower macro-F1. The external transferability probe on SciFact and VitaminC shows R4-compatible methods run on public data but underperform NLI cross-encoders on generic support/refutation; public data cannot test the four-class evidence-sufficiency taxonomy.

**The differentiation against RIGOURATE [30], ForceBench [35], and CLAIM-BENCH [28] is positioning-level (§II.A, Table X): CESE-OCN outputs a four-class relation label on a single claim and targets the high-risk action-overclaim sub-class as a screening target, complementing continuous overstatement scoring, contrastive paired-claim force testing, and full-paper claim-evidence extraction.** This is a conceptual complementarity, not an empirically benchmarked head-to-head advantage (§IX item 9). The §VI.E RIGOURATE-style scalar proxy baseline — explicitly labelled as proxy, NOT the official RIGOURATE system (official code/data/model not publicly available as of 2026-07-05) — provides controlled silver-stage evidence that a scalar score cannot reliably distinguish mild from strong_action (ROC-AUC ≤ 0.59) and that R4 retains targeted screening value on the high-risk boundary class (R4 strong_F1 = 0.3967 vs. rule_scalar best-F1 = 0.3844 on silver 444; R4 strong_F1 = 0.3000 vs. rule_scalar = 0.1364 on matched 100). This complementarity is the empirical motivation for CESE-OCN's four-class decomposition, but it is validation-pending: the proxy is not the official RIGOURATE system, the nli_scalar_score baseline is BLOCKED with `blocked_reason` recorded, and all evaluation is on silver labels (pre-gold).

The result is **validation-pending**. The author sanity audit flags 62.5% of silver labels as questionable or unclear, reinforcing that the pre-registered gold adjudication (§VII) — now upgraded to a two-layer gold protocol (§VII.J: Layer 1 relation label + Layer 2 claim realism, with pre-registered 25% class-level and paper-level realism thresholds) — is the protocol-locked mechanism that determines whether the LLM under-detection finding is treated as established. The paper is reported with clear silver-label boundaries, without claims of final benchmark readiness, and without claims that R4 outperforms LLM judges overall. R4 provides targeted value for strong_action_overclaim detection and evidence sufficiency calibration — as a screening-oriented complement to LLM judges, not a replacement. **The controlled silver-stage evidence motivates the protocol-locked gold validation rather than replacing it.**

## Appendix A. Case Studies

See `appendix_case_studies_v3_6_clean.md` for 8 detailed case studies: 4 trusted cases (one per class) and 4 boundary cases (mild vs. strong, strong vs. contradiction, supported vs. mild / evidence-context-missing, claim-too-abstract). All 8 cases have traceable candidate_ids in `strict_silver_max_candidates_v1.csv`. Boundary cases are used to illustrate task difficulty, not to support strong claims. The V3.6 appendix replaced V3.5 T2 (TCB_008, problematic number inflation) with SBV2-ALL92-G170-C02 (clean scope expansion), and replaced V3.5 B4 (placeholder with no real candidate_id) with HRC_001 = SBV2-ALL92-G003-STRONG (real case, claim_too_abstract root_cause) — see `case_integrity_audit.csv` for the full audit.

## Appendix B. Language Guardrails

### Safe claims (allowed in the paper):

- "On the controlled silver-stage evaluation, R4 improves strong-action positive-F1 from 0.2408 to 0.3967 while preserving contradiction and escalation performance."
- "On the controlled silver-stage evaluation, the conservative-strong router yields a strong-action positive-F1 delta of +0.1559 (CI [0.1058, 0.1988], 10/10 seeds positive)."
- "Under the tested prompts, generic LLM judges (GPT-5.5, DeepSeek-V3) under-detect strong_action_overclaim on the controlled silver-stage evaluation — a validation-pending finding."
- "This structured evidence-sufficiency prompt design did not improve strong_action detection under the tested setting; other prompt designs remain untested."
- "R4 complements black-box LLM judges on the strong_action_overclaim relation, rather than replacing them — pending gold validation."
- "R4's macro-F1 is substantially lower than LLM judges (0.3280 vs. 0.5523 on matched 100); R4 is a screening-oriented complement, not a general-purpose classifier."
- "Evidence sufficiency rather than generic factuality is the target of this framework."
- "The author sanity audit flags 62.5% of silver labels as questionable or unclear; the pre-registered gold adjudication (§VII) is the protocol-locked validation mechanism."
- "The framework is positioned as a controlled silver-stage action-overclaim diagnostic with a protocol-locked validation mechanism."
- "The controlled silver-stage evidence motivates the protocol-locked gold validation rather than replacing it."

### Forbidden claims (must NOT appear in the paper):

- "We solve scientific claim calibration." / "Our model fully handles strong action overclaims."
- "Our labels are gold / human-audited." / "GPT can be used as gold label."
- "Proves LLMs cannot detect strong_action_overclaim." / "All LLMs are bad at this task."
- "Established LLM blind spot." (use "under-detection pattern observed under the tested prompts, validation-pending" instead)
- "Validated taxonomy." (use "frozen taxonomy pending protocol-locked gold validation" instead)
- "Final proof." (use "controlled silver-stage evidence" instead)
- "Gold benchmark." (use "controlled silver-stage diagnostic" instead)
- "R4 outperforms GPT overall." / "R4 is stronger than LLMs on all metrics."
- "Cost-sensitive cw4.0 is the new main method."
- "CESE-OCN outperforms strong baselines on a final benchmark."
- "The framework is validated for deployment." / "All four classes are well-calibrated."
- "supported_vs_mild boundary is resolved." / "Cross-domain generalization is confirmed."
- "SOTA / state-of-the-art." / "Fully solved."
- "Systematic blind spot" (use "under-detection pattern observed under the tested prompts" instead).
- "Submission-ready / final benchmark complete." (this is a framework-level contribution with a protocol-locked validation mechanism; gold validation is planned but not completed)
- "Workshop / pilot-only / low-config positioning." (this is a high-standard framework contribution)
- "We introduce scientific overstatement detection / evidence sufficiency calibration as a new field." (this work builds on RIGOURATE [30], evidence-licensed claims [31], ForceBench [35], and CLAIM-BENCH [28]; it is a fine-grained relation-type decomposition on the existing track, not a new field)
- "First work / first benchmark / first to propose evidence sufficiency calibration." (use "fine-grained diagnostic variant of evidence-sufficiency calibration" instead)
- "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH." (the differentiation is positioning-level, not a head-to-head empirical benchmark; §II.A, Table X, §IX item 9)
- "SimClaim is a natural-prevalence corpus." (SimClaim is a controlled counterfactual diagnostic set; §V.A)
- "The silver-stage screening finding transfers to natural scientific writing." (the proposed gold-realism audit §VII.I has not yet been run; natural-claim transferability is not established)

### Preferred language:

- "under the tested prompts" / "under this tested setting"
- "on the controlled silver-stage evaluation" / "on the 100 matched samples"
- "single-run, temperature 0, no variance estimate"
- "prompt/model/sample specific"
- "under-detection pattern observed under the tested prompts" (NOT "systematic blind spot", NOT "established")
- "on the controlled silver-stage evaluation" / "AI-preannotated, author-screened labels"
- "framework-level contribution" / "validation-pending"
- "suggests" / "is consistent with" / "does not support"
- "screening-oriented complement to black-box LLM judges"
- "protocol-locked validation mechanism" / "pre-registered adjudication"
- "high-risk boundary class" / "controlled silver-stage evidence"
