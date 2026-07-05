# V3.13 Revision Log

**Date:** 2026-07-05
**Source version:** V3.12.1 (`D:\ocn\paper_versions_ordered\V3_12_1_advisor_send_clean\`)
**Output version:** V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH
**Output directory:** `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\`

## Summary of Changes

V3.13 is a **differentiation revision against RIGOURATE, ForceBench, and CLAIM-BENCH**. The paper is repositioned from "opening a new field of scientific overstatement detection" to "fine-grained relation-type decomposition and high-risk action-overclaim screening on the existing scientific overstatement / evidence-force calibration track". No new experiments, no API calls, no gold annotation, no number changes.

## 1. Version Header (lines 3–8)

- **Changed:** Version string from `V3.12.1 Advisor Send Clean` to `V3.13 Differentiated Against RIGOURATE / ForceBench / CLAIM-BENCH`.
- **Changed:** Date from `2026-07-04` to `2026-07-05`.
- **Added:** A new `**Changes from V3.12.1:**` paragraph describing the differentiation revision scope. The paragraph explicitly states: no new experiments, no API calls, no gold annotation, no number changes, no threshold retuning. It also states: "This work does not claim to introduce scientific overstatement detection or evidence sufficiency calibration as a new field; it builds on RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35], and CLAIM-BENCH [28], and focuses on fine-grained relation typing and high-risk action-overclaim screening."
- **Preserved:** `**Changes from V3.11:**`, `**Changes from V3.10.1:**` paragraphs unchanged. The `**Changes from V3.12:**` paragraph was removed to keep the header readable; V3.12 → V3.12.1 → V3.13 lineage is preserved through the V3.12.1 paragraph.

## 2. Abstract (line 18)

- **Added:** "Building on recent work on scientific overstatement scoring and evidence-force calibration (RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35])" as an acknowledgment of prior work.
- **Changed:** "We formulate this as a distinct task, **evidence sufficiency calibration**" → "we study a fine-grained diagnostic variant of evidence-sufficiency calibration" (removes "distinct task" framing).
- **Added:** "controlled counterfactual diagnostic benchmark" + "; evidence spans are drawn from real scientific papers while claim variants are generated to instantiate specific evidence-sufficiency relations" (transparency about the synthetic/counterfactual nature of SimClaim).
- **Changed:** Final sentence from "framework-level and taxonomy-level: a falsifiable evidence-sufficiency calibration framework..." to "fine-grained relation-type decomposition with a frozen, protocol-locked validation mechanism — not the introduction of scientific overstatement detection as a new field, and not a claim of state-of-the-art overstatement detection."
- **Preserved:** All numeric values (0.2408, 0.3967, 0.0769, 0.3000, 0.3280, 0.5523, 0.04, 100, 200, 444, 111, six domains) byte-identical from V3.12.1.

## 3. §I Introduction (lines 22–42)

- **Added:** A new opening paragraph (line 24) acknowledging recent work: "Recent work has begun to quantify scientific overstatement and evidence-force mismatch. RIGOURATE [30]... ForceBench [35]... CLAIM-BENCH [28]... These lines establish scientific overstatement and evidence-force calibration as an active research track. However, less attention has been paid to whether different overclaim relations require different diagnostic treatment, especially high-risk action/deployment overclaims."
- **Changed:** The original first paragraph (line 26) is preserved, but the last sentence now reads "...do not isolate it as a relation-type problem distinct from generic factual correctness" (was "...do not isolate it").
- **Changed:** "insufficient for scientific claim calibration" → "insufficient for fine-grained scientific claim calibration" (line 26).
- **Replaced:** The 5-contribution list (lines 32–42 in V3.12.1) is replaced by a 3-contribution list:
  1. **Taxonomy contribution** (decomposition, complementary to RIGOURATE/ForceBench/CLAIM-BENCH)
  2. **Diagnostic contribution** (LLM under-detection finding, controlled silver-stage)
  3. **Screening-method contribution** (R4 as screening-oriented complement, not SOTA)
- **Changed:** Organization paragraph (line 42) updated to reflect new §II.A subsection, Table X, §V.A transparency statement, §VII.I realism audit, §VIII.F fine-grained typing subsection.

## 4. §II Related Work (lines 44–71)

- **Replaced:** The brief RIGOURATE paragraph (line 52 in V3.12.1) is replaced by a new subsection `### A. Relation to Scientific Overstatement and Evidence-Force Calibration` containing:
  - Intro paragraph naming RIGOURATE, ForceBench, CLAIM-BENCH
  - RIGOURATE paragraph: acknowledges strengths (natural claims, larger scale, retrieval, human validation), states difference (degree vs. type), explicitly states RIGOURATE does not isolate mild scope from high-risk action overclaim.
  - ForceBench paragraph: acknowledges strengths (contrastive paired-claim, five force dimensions, cited-RAG oriented), states difference (monotonic preference vs. single-instance relation typing), explicitly states ForceBench does not output four-class relation label.
  - CLAIM-BENCH paragraph: acknowledges strengths (natural full-paper pairs, extraction+validation, larger scale), states difference (whether evidence supports claims vs. whether evidence is sufficient for strength/actionability).
  - Table X (positioning table) with 7 columns × 4 rows.
  - Positioning summary paragraph.
- **Preserved:** Lines 46–50 (Generic claim verification + RAG evaluation paragraphs) unchanged.
- **Added:** "framework-level contribution on the existing scientific overstatement / evidence-force calibration track" + "It is **not** a claim to introduce scientific overstatement detection or evidence sufficiency calibration as a new field" (line 71).

## 5. §V.A SimClaim (lines 236–246)

- **Added:** A new `**Synthetic / counterfactual transparency statement.**` paragraph (line 240) explicitly stating:
  - SimClaim is **not** a natural-prevalence corpus of author-written claims.
  - It is a **controlled counterfactual diagnostic set**: evidence from real papers, claim variants generated.
  - The four-way balanced design is a *deliberate construction*, not natural prevalence.
  - In natural corpora, `contradiction_candidate` and `strong_action_overclaim` should be rarer.
  - Three bullet points specifying what SimClaim is / is not appropriate for.
  - Cross-reference to §VII.I realism audit.

## 6. §VII Pre-Registered Gold Validation Protocol

- **Added:** New subsection `### I. Proposed Gold-Realism Audit Extension` (lines 470–490) specifying:
  - `claim_realism_score_1_to_5` field (integer 1–5)
  - `claim_realism_issue` field (categorical: none / too_template_like / too_extreme / unnatural_wording / not_scientific_claim / ambiguous_or_vague)
  - Annotator protocol (independent, blind, adjudication rules)
  - Pre-registered reporting thresholds (25% class-level, 25% paper-level)
  - Explicit statement that existing gold-pilot CSVs are NOT modified in V3.13.

## 7. §VIII Discussion

- **Added:** New subsection `### F. Why Fine-Grained Relation Typing Is Valuable` (lines 549–561) explaining why the four-class decomposition is operationally valuable independent of any particular model:
  - mild_scope_overclaim = writing-strength issue (editorial intervention)
  - strong_action_overclaim = risk-bearing issue (deployment/safety/policy intervention)
  - contradiction_candidate = correctness issue (fix claim or evidence)
  - "strong_action_overclaim is not just 'a mild overclaim with a higher score'"
  - Continuous scores and contrastive preference tests cannot, by themselves, output which type of mismatch a single claim has.
  - The taxonomy-level argument does not depend on R4 specifically.

## 8. §IX Limitations (lines 563–609)

- **Added:** Item 9 (new): "Differentiation from RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not empirical head-to-head."
- **Added:** Item 10 (new): "SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus." (with realism audit cross-reference).
- **Added:** "(f)" to practical limitations: "the comparison against RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not a head-to-head empirical benchmark."

## 9. §X Conclusion (lines 613–623)

- **Changed:** First sentence from "evidence sufficiency calibration framework, rather than a generic claim verification system" to "fine-grained evidence-sufficiency relation diagnosis framework for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field."
- **Added:** "and that this calibration question benefits from a *relation-type decomposition*... rather than a single continuous overstatement score alone."
- **Changed:** "R4 is positioned as a screening-oriented complement to black-box LLM judges, not a replacement" → "...not a replacement and not a state-of-the-art overstatement detector."
- **Added:** New paragraph (line 621) explicitly stating the differentiation against RIGOURATE/ForceBench/CLAIM-BENCH is positioning-level, with cross-reference to §II.A, Table X, §IX item 9.
- **Added:** "now extended with a proposed claim-realism audit (§VII.I)" to the validation-pending paragraph.

## 10. Appendix B Language Guardrails (lines 662–666)

- **Added:** 5 new forbidden claims:
  - "We introduce scientific overstatement detection / evidence sufficiency calibration as a new field."
  - "First work / first benchmark / first to propose evidence sufficiency calibration."
  - "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH."
  - "SimClaim is a natural-prevalence corpus."
  - "The silver-stage screening finding transfers to natural scientific writing."

## 11. Standalone Files Generated

- `proposed_gold_realism_extension.md` — Standalone specification of the realism audit fields, annotator protocol, and pre-registered thresholds. Referenced from §VII.I.
- `V3_13_strengthening_plan_after_related_work_shift.md` — P0/P1/P2/P3 priority roadmap after the Related Work shift. P0 = pre-advisor-send; P1 = pre-gold-pilot; P2 = pre-confirmatory-submission; P3 = future work.
- `V3_13_revision_log.md` — This file.
- `V3_13_readiness_gate.json` — Machine-readable readiness gate.
- `advisor_cover_note_cn_v3_13.md` — Chinese advisor cover note.
- `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.docx` — Docx build.

## What Was NOT Changed

- **No experimental numbers changed.** All §VI numbers (R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 0.3280/0.5523, bootstrap CI [0.1058, 0.1988], FP/TP ratio, etc.) are preserved byte-identical from V3.12.1.
- **No §VIII.D numbers changed.** All §VIII.D.A/B/C results (TF-IDF/NLI audit, screening utility, label-shift stress test) are preserved byte-identical from V3.12.1.
- **No silver written as gold.** All silver-stage results retain the "controlled silver-stage evaluation" qualifier.
- **No §VII.G downgrade criteria changed.** The 6 original criteria are preserved.
- **No prior paper version modified.** V3.12.1, V3.12, V3.11, V3.10.1, V3.9 are all preserved unchanged.
- **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning.**
- **No "first to propose" / "novel task" / "new field" / "SOTA" phrasing in the body.** The only occurrences of these phrases are in negations ("not a claim to introduce...") or in the Forbidden claims list (Appendix B).

## Quality Verification

1. **Differentiation explicit:** §II.A + Table X + §VIII.F + §X all explicitly position CESE-OCN against RIGOURATE, ForceBench, CLAIM-BENCH. ✓
2. **No "first to propose" framing:** Body text uses "fine-grained diagnostic variant of evidence-sufficiency calibration" / "on the existing... track" / "complementary to" instead. ✓
3. **SimClaim transparency:** §V.A explicitly states SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus. ✓
4. **Realism audit specified:** §VII.I + `proposed_gold_realism_extension.md` specify the realism audit fields, protocol, and pre-registered thresholds. Existing gold-pilot CSVs unchanged. ✓
5. **All experimental numbers preserved:** Spot-checked R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 0.3280/0.5523, bootstrap CI [0.1058, 0.1988], FP/TP 2.89, retention break-even ~0.5, 50% CI [-0.026, +0.255]. All byte-identical. ✓
6. **Non-gold caveat preserved:** §VIII.D header, §IX item 8, §VII.H all retain "non-gold robustness analysis, does not replace gold adjudication." ✓
7. **50% retention caveat preserved:** §VIII.D.C "positive but statistically weaker / CI crosses zero" wording preserved. ✓
8. **R4 macro-F1 < LLM fact preserved:** §VI.B, §VIII.A, §X all retain "R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523". ✓
9. **Gold-not-done fact preserved:** §VII, §IX item 1, §X all retain "gold validation is planned but not completed." ✓
10. **No workshop / pilot-only / low-config positioning:** §X and §IX retain high-standard framework positioning from V3.10.1+. ✓

## Forbidden Actions Check

- ❌ Did NOT run new experiments.
- ❌ Did NOT call any API.
- ❌ Did NOT perform gold annotation.
- ❌ Did NOT change any experimental number.
- ❌ Did NOT write silver as gold.
- ❌ Did NOT modify V3.12.1, V3.12, V3.11, V3.10.1, or V3.9 source files.
- ❌ Did NOT use workshop / pilot-only / low-config positioning.
- ❌ Did NOT claim to introduce scientific overstatement detection / evidence sufficiency calibration as a new field.
- ❌ Did NOT modify existing gold-pilot CSVs (`pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`, `adjudication_template.csv`).
- ❌ Did NOT claim natural-claim transferability (realism audit is proposed, not run).
- ❌ Did NOT claim empirical head-to-head advantage over RIGOURATE / ForceBench / CLAIM-BENCH (positioning-level only, explicitly stated in §IX item 9).
