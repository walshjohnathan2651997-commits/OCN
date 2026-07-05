# Dataset Construction Risk Audit — V3.14 Mainline Locked

**Date:** 2026-07-05
**Version:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Source:** §V.A, §VII.J, §IX of CESE_OCN_V3_14_mainline_locked.md; `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\claim_realism_audit_queue.csv`; `D:\ocn\gold_pilot_protocol_freeze_v1\gold_pilot_protocol_freeze_report.md`.

This audit documents the dataset construction risks for SimClaim and provides a paste-ready English Data Limitation paragraph for the paper.

---

## 1. Evidence comes from real scientific papers

**Fact:** SimClaim's evidence spans are drawn from real scientific papers.

- **Source:** 111 evidence groups across 6 domains (autonomous_driving, cyber_defense, digital_twin, healthcare_ai, llm_safety, robotics).
- **Extraction:** Evidence spans are extracted (not retrieved) from the paper body, with page-level source tracking (`page_number`, `source_location`).
- **Provenance:** Each evidence span has a `source_id`, `arxiv_id`, `pdf_filename`, and `evidence_text_sha256` for traceability.
- **No fabrication:** Evidence text is verbatim from the source paper; no paraphrasing or summarisation at the evidence-extraction stage.

**Risk:** Low. Evidence is real and traceable.

---

## 2. Claims are generated counterfactual variants

**Fact:** SimClaim's claims are NOT natural author-written claims. They are generated counterfactual variants designed to instantiate specific evidence-sufficiency relations.

- **Generation policy:** `same_frame_four_variant_generation` — for each evidence group, four claim variants are generated to instantiate the four relation classes (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate).
- **Generation status:** `claim_generation_status = success` for all 444 pairs; `claim_generation_policy = same_frame_four_variant_generation`.
- **Annotation status:** `annotation_status = ai_preannotated`; `human_audited = False`.
- **Silver label source:** `candidate_label_guess` (AI-preannotated, author-screened). The `final_label` and `gold_label` fields are EMPTY (silver is pre-gold).

**Risk:** HIGH. Generated claims may be:
- Too template-like (overly uniform opening phrasing).
- Too extreme (superlatives inserted mechanically).
- Unnatural in wording (placeholder phrasing, mechanical negation insertions).
- Not recognizable as scientific claims (too abstract or too forced).

**Mitigation:** §VII.J two-layer gold protocol includes Layer 2 (claim realism) with `claim_realism_score_1_to_5`, `claim_realism_issue`, and `claim_realism_usable_for_paper` fields. A heuristic pattern-based pre-screen (`claim_realism_audit_queue.csv`) flagged 21/444 (4.7%) overall and 10/111 (9.0%) for `strong_action_overclaim` — both below the 25% pre-registered threshold, but the `strong_action_overclaim` rate is non-trivial.

---

## 3. Four-class balanced design is diagnostic, not natural prevalence

**Fact:** SimClaim's 1:1:1:1 balanced design (111 per class) is a deliberate construction for pressure-testing boundary recognition under matched evidence.

- **Design rationale:** By holding the evidence group fixed and varying only the claim variant, SimClaim isolates the claim-side signal that determines the relation class. This enables controlled diagnosis of relation-type separability.
- **NOT a prevalence estimate:** The balanced design does NOT estimate the natural prevalence of these relations in real scientific writing.

**Risk:** MEDIUM. If a reader misinterprets the balanced design as a natural prevalence estimate, they may draw incorrect conclusions about the real-world frequency of `strong_action_overclaim` or `contradiction_candidate`.

**Mitigation:** §V.A explicitly states: "SimClaim is not a natural-prevalence corpus of author-written claims. It is a controlled counterfactual diagnostic set... The four-way balanced design (111 per class) is a deliberate construction for pressure-testing boundary recognition under matched evidence, not an estimate of the natural prevalence of these relations in real scientific writing."

---

## 4. SimClaim cannot represent real-world class proportions

**Fact:** SimClaim cannot be used to estimate the real-world prevalence of any relation class.

- **In natural scientific corpora:** We expect `supported` to be the most prevalent class (most claims in real papers are supported by their evidence). We expect `contradiction_candidate` and `strong_action_overclaim` to be substantially rarer (authors rarely contradict their own evidence or over-claim to the point of asserting deployment/safety/generalization that the evidence does not justify).
- **In SimClaim:** All four classes are equally represented (111 each) by construction.
- **Implication:** Any per-class metric on SimClaim (precision, recall, F1) is a *diagnostic-stage* metric on a balanced diagnostic set, NOT an estimate of real-world performance.

**Risk:** MEDIUM. Reviewers may ask "how would R4 perform on a natural-prevalence corpus where strong_action is rare?" The answer is: SimClaim cannot answer this question; a follow-up natural-prevalence study is required.

**Mitigation:** §IX item 10 explicitly states: "SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus... SimClaim is appropriate for pressure-testing boundary recognition under matched evidence and for controlled comparison of relation-specific routing strategies; it is not appropriate for estimating the real-world prevalence of each evidence-sufficiency relation in scientific papers."

---

## 5. Contradiction and strong_action are rarer in the real world

**Fact:** In real scientific writing, `contradiction_candidate` and `strong_action_overclaim` are expected to be substantially rarer than `supported` and `mild_scope_overclaim`.

- **Contradiction:** Authors rarely contradict their own evidence in the same paper; contradictions are more common across papers (paper A contradicts paper B) than within a paper.
- **Strong_action_overclaim:** Authors occasionally over-claim scope (mild_scope_overclaim), but asserting deployment/safety/generalization that the evidence does not justify is rarer and more consequential.
- **Prevalence implication:** A screening system deployed on real scientific writing would see far fewer `strong_action_overclaim` cases than SimClaim's 25% rate. The screening precision on real data may be lower (more false positives per true positive) because the base rate is lower.

**Risk:** MEDIUM. The §VIII.D.B Screening Utility Test (FP/TP = 2.89 on SimClaim) may under-estimate the FP/TP ratio on real data where strong_action is rarer.

**Mitigation:** §IX item 10 notes that SimClaim is not for prevalence estimation. The §VII.J two-layer gold protocol includes a realism audit to assess whether SimClaim claims are naturalistic enough to support the screening claim. A follow-up natural-prevalence study is explicitly listed as future work.

---

## 6. Gold should validate relation label + claim realism

**Fact:** The pre-registered gold protocol is two-layer (§VII.J):

- **Layer 1 (relation label):** Two-annotator independent review + adjudication, using the frozen decision tree and boundary rules. Silver labels, R4 predictions, LLM predictions, and group structure are hidden. Cohen's κ and Krippendorff's α are reported per class and per boundary. The §VII.G downgrade criteria apply (mild_vs_strong κ < 0.40 → taxonomy revised; strong_action retention < 0.50 → claim downgraded).
- **Layer 2 (claim realism):** `claim_realism_score_1_to_5`, `claim_realism_issue` (9 categorical values), `claim_realism_usable_for_paper` (derived). Annotators rate realism INDEPENDENTLY of the relation label. Pre-registered 25% class-level and 25% paper-level realism thresholds trigger caveats or downgrades.

**Operationalisation:** Layer 1 is operationalised by the frozen `gold_pilot_protocol_freeze_v1` package (2026-07-04, status: PROTOCOL FROZEN, annotation NOT begun), which contains the frozen annotation guideline, decision tree, boundary rules, 20 worked positive/negative examples, annotator training packet, two independent blind annotation templates (A and B with silver labels excluded), adjudication protocol, and agreement metric plan. Layer 2 extends Layer 1 with the three realism fields, run as a separate pass on the same annotated sample.

**Risk:** LOW (protocol is frozen and pre-registered). The main risk is that gold annotation has not begun; all §VI results remain silver-stage.

---

## 7. Natural prevalence requires a future separate study

**Fact:** SimClaim cannot answer natural-prevalence questions. A separate study is required.

- **What a natural-prevalence study would look like:** Sample claims from real scientific papers (e.g., ICLR/NeurIPS abstracts and introductions, similar to RIGOURATE [30]), pair each claim with its in-paper evidence, and label the relation class using the frozen taxonomy. The resulting class distribution would estimate real-world prevalence.
- **Why this is future work:** Such a study requires (a) a claim extraction pipeline from full papers, (b) an evidence retrieval pipeline (RIGOURATE uses a fine-tuned reranker), (c) a much larger annotation budget, and (d) a different sampling strategy (natural sampling, not balanced).
- **Relationship to RIGOURATE:** RIGOURATE [30] already operates on natural author-written claims at larger scale. A future CESE-OCN natural-prevalence study would complement RIGOURATE by adding the four-class relation typing on top of natural claims.

**Risk:** LOW for the current paper (SimClaim is explicitly diagnostic). The risk is that the paper's screening claim may not transfer to natural-prevalence corpora; this is acknowledged in §IX item 10 and addressed by the §VII.J realism audit.

---

## 8. Paste-ready English Data Limitation paragraph

The following paragraph can be pasted directly into the paper's §IX Limitations or §V.A Data section:

> **Data Limitation.** SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus of author-written claims. Evidence spans are drawn verbatim from real scientific papers across six domains (autonomous driving, cyber defense, digital twin, healthcare AI, LLM safety, robotics), with full source traceability (`source_id`, `arxiv_id`, `page_number`, `evidence_text_sha256`). Claim variants, however, are generated counterfactual variants designed to instantiate specific evidence-sufficiency relations under a `same_frame_four_variant_generation` policy: for each evidence group, four claim variants are generated to cover the four relation classes (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate). The four-way balanced design (111 pairs per class) is a deliberate construction for pressure-testing boundary recognition under matched evidence; it does not estimate the natural prevalence of these relations in real scientific writing. In natural scientific corpora, we expect `supported` to be the most prevalent class and `contradiction_candidate` and `strong_action_overclaim` to be substantially rarer, since authors rarely contradict their own evidence or assert deployment, safety, or generalization conclusions that the evidence does not justify. Consequently, per-class metrics on SimClaim (precision, recall, F1) are diagnostic-stage metrics on a balanced diagnostic set, not estimates of real-world performance; the screening FP/TP ratio (2.89 on SimClaim) may under-estimate the ratio on natural-prevalence data where `strong_action_overclaim` has a lower base rate. All SimClaim labels are AI-preannotated and author-screened silver labels (`candidate_label_guess`); no gold annotation has been performed. The pre-registered two-layer gold protocol (§VII: Layer 1 relation label + §VII.J Layer 2 claim realism, with pre-registered 25% class-level and paper-level realism thresholds) is the falsifiable mechanism that determines whether SimClaim claims are naturalistic enough to support the paper's screening claim. A heuristic pattern-based realism pre-screen flagged 21/444 (4.7%) of SimClaim silver claims overall and 10/111 (9.0%) for the `strong_action_overclaim` class; both are below the 25% pre-registered threshold, but the `strong_action_overclaim` rate is non-trivial and motivates prioritising that class in gold sampling. A future natural-prevalence study — sampling claims from real scientific papers and labelling relation classes using the frozen taxonomy — is required to estimate real-world class proportions and to test whether the silver-stage screening finding transfers to natural scientific writing. This natural-prevalence study is explicitly listed as future work and is not part of the current paper's claims.

---

## 9. Summary

| Risk dimension | Risk level | Mitigation |
| --- | --- | --- |
| Evidence reality | LOW | Evidence is verbatim from real papers; full traceability |
| Claim artificiality | HIGH | §VII.J Layer 2 realism audit; pre-registered 25% thresholds |
| Balanced design misinterpretation | MEDIUM | §V.A explicit disclosure; "not a natural-prevalence corpus" |
| Real-world prevalence estimation | MEDIUM | §IX item 10; future natural-prevalence study listed |
| Contradiction/strong_action rarity in real world | MEDIUM | §IX item 10; FP/TP may under-estimate on natural data |
| Gold protocol completeness | LOW (protocol) / HIGH (not yet run) | Two-layer protocol frozen; gold_pilot_protocol_freeze_v1 (2026-07-04, annotation NOT begun) |
| Natural prevalence transfer | LOW for current paper | SimClaim is explicitly diagnostic; transferability not claimed |
