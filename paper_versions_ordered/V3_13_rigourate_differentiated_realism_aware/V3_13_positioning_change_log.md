# V3.13 Positioning Change Log (RIGOURATE-Differentiated + Realism-Aware)

**From:** V3.12 (CESE_OCN_V3_12_with_three_credibility_checks.md)
**To:** V3.13 RIGOURATE-Differentiated + Realism-Aware (CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md)
**Date:** 2026-07-05
**Operator:** CESE-OCN automated revision pipeline (no paid API calls)
**Scope:** Positioning-level revision + integration of RIGOURATE-style proxy baseline results + two-layer gold protocol upgrade. **No new experiments, no API calls, no gold annotation, no model retraining, no threshold retuning, no change to any experimental number in §VI.A–§VI.D or §VIII.D.**

---

## 1. Title change

| Version | Title |
| --- | --- |
| V3.12 | Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework |
| V3.13 (prior) | Evidence Sufficiency Calibration for Scientific Claims: A Mixed Relation-Routing Framework |
| **V3.13 RIGOURATE-Differentiated + Realism-Aware (this version)** | **Fine-Grained Evidence-Sufficiency Relation Diagnosis for Rare High-Risk Scientific Action Overclaims** |

**Subtitle (new):** A Controlled Counterfactual Diagnostic Study of LLM Under-Detection and Screening-Oriented Routing.

**Rationale:** The new title foregrounds the actual contribution — fine-grained relation diagnosis for a rare high-risk sub-class (strong_action_overclaim) — and removes the broad "evidence sufficiency calibration for scientific claims" framing that risks overlapping with RIGOURATE / ForceBench / CLAIM-BENCH positioning. The subtitle makes the controlled counterfactual diagnostic study design and the screening-oriented routing contribution explicit.

---

## 2. Positioning shift

| Dimension | V3.12 positioning | V3.13 RIGOURATE-Differentiated + Realism-Aware positioning |
| --- | --- | --- |
| Field claim | Implicitly opens "evidence sufficiency calibration" as a new task | Explicitly builds on the existing scientific overstatement / evidence-force calibration track (RIGOURATE [30], evidence-licensed claims [31], ForceBench [35], CLAIM-BENCH [28]); does NOT claim to open a new field |
| Contribution framing | 5 contributions (taxonomy + diagnostic + screening + protocol + transferability) | 3 contributions (taxonomy + diagnostic + screening-method); protocol and transferability are supporting, not headline |
| Output representation | "Four-class relation label" (generic) | "Four-class relation label" explicitly contrasted with RIGOURATE's continuous scalar, ForceBench's contrastive preference, and CLAIM-BENCH's extraction-validation |
| Data framing | "SimClaim silver set" (generic) | "SimClaim controlled counterfactual diagnostic set" — explicitly NOT a natural-prevalence corpus; balanced 1:1:1:1 is a deliberate construction for boundary pressure-testing, not a natural prevalence estimate |
| R4 positioning | "Mixed relation-routing framework" | "Screening-oriented complement to generic LLM/NLI judges, not a replacement and not a state-of-the-art overstatement detector" |
| Gold validation | Single-layer relation-label adjudication | Two-layer gold protocol: Layer 1 relation label + Layer 2 claim realism (§VII.J), with pre-registered 25% class-level and paper-level realism thresholds |
| RIGOURATE comparison | None (positioning-level only) | §VI.E RIGOURATE-style scalar proxy baseline (proxy, NOT official RIGOURATE); official reproduction BLOCKED with `blocked_reason` recorded |

---

## 3. Section-by-section changes from V3.12

### §Abstract
- Added: "Building on recent work on scientific overstatement scoring and evidence-force calibration (RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35])".
- Added: SimClaim explicitly described as "controlled counterfactual diagnostic benchmark... evidence spans are drawn from real scientific papers while claim variants are generated to instantiate specific evidence-sufficiency relations".
- Added: RIGOURATE-style scalar proxy baseline paragraph (§VI.E reference; proxy NOT official RIGOURATE; scalar cannot distinguish mild from strong; scalar and R4 complementary).
- Changed: "pre-registered gold adjudication protocol" → "pre-registered two-layer gold adjudication protocol (§VII: Layer 1 relation label + §VII.J Layer 2 claim realism, with pre-registered 25% class-level and paper-level realism thresholds)".
- Removed: any implication of opening a new field; any "first to propose" framing.

### §I. Introduction
- First paragraph rewritten: opens with "Recent work has begun to quantify scientific overstatement and evidence-force mismatch. RIGOURATE [30] retrieves supporting evidence... ForceBench [35] provides a contrastive evidence-force calibration stress test... CLAIM-BENCH [28] evaluates scientific claim-evidence extraction and validation across full papers. These lines establish scientific overstatement and evidence-force calibration as an active research track. However, less attention has been paid to whether different overclaim relations require different diagnostic treatment, especially high-risk action/deployment overclaims."
- Contribution list condensed from 5 to 3: (1) Taxonomy contribution; (2) Diagnostic contribution; (3) Screening-method contribution.
- Each contribution explicitly positioned as "on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field".

### §II. Related Work and Positioning
- New §II.A "Relation to Scientific Overstatement and Evidence-Force Calibration" with three paragraphs (RIGOURATE, ForceBench, CLAIM-BENCH).
- Each paragraph explicitly acknowledges the related work's strengths (RIGOURATE: natural author-written claims, larger scale, human validation; ForceBench: clean contrastive paired-claim protocol, five force dimensions; CLAIM-BENCH: natural full-paper claim-evidence pairs, extraction + validation joint evaluation).
- Each paragraph states the conceptual complementarity (RIGOURATE: scalar severity vs. relation typing; ForceBench: contrastive preference vs. single-instance typing; CLAIM-BENCH: extraction-validation vs. strength-calibration typing).
- New Table X positioning CESE-OCN against RIGOURATE / ForceBench / CLAIM-BENCH along 7 dimensions.

### §V. Data and Experimental Protocol
- §V.A adds "Synthetic / counterfactual transparency statement": SimClaim is NOT a natural-prevalence corpus; it is a controlled counterfactual diagnostic set; balanced 1:1:1:1 is a deliberate construction; in natural corpora, supported should be most prevalent and strong_action/contradiction should be rare; SimClaim is for pressure-testing boundary recognition under matched evidence, NOT for estimating natural prevalence.

### §VI. Results
- §VI.A–§VI.D: byte-identical to V3.12 (no change to any number).
- **§VI.E (NEW): Scalar Overstatement Baseline vs. Relation-Specific Screening (RIGOURATE-style Proxy)** — reports the RIGOURATE-style scalar proxy baseline results from the RIGOURATE Reproduction + SimClaim Differentiation v1 task:
  - Official RIGOURATE reproduction status (BLOCKED; arXiv v2 placeholder URL; no public code/data/model).
  - Three proxy baselines: (A) rule_scalar_score completed for 444 pairs; (B) nli_scalar_score BLOCKED with `blocked_reason`; (C) llm_scalar_proxy completed for 200/444 matched pairs.
  - 4 binary-task evaluation table (supported_vs_overclaim, mild_vs_strong, strong_vs_contradiction, strong_vs_nonstrong) with ROC-AUC, PR-AUC, best-F1, precision, recall.
  - 5-method head-to-head comparison table (rule_scalar, GPT standard, GPT structured, DeepSeek, R4 frozen) on 100 matched samples.
  - 5 required answers: (Q1) scalar can identify overclaim only when LLM-derived; (Q2) scalar cannot distinguish mild from strong; (Q3) scalar cannot replace R4 strong_action route; (Q4) R4 retains screening value (captures 8/24 LLM-missed strong_action); (Q5) scalar and relation-specific screening are complementary.
  - Caveats: proxy NOT official RIGOURATE; nli_scalar_score BLOCKED; silver-only; SimClaim is counterfactual; case-level analysis shows 49/100 both-wrong, 35/100 mild/strong confusion.

### §VII. Pre-Registered Gold Validation Protocol
- §VII.A–§VII.I: byte-identical to V3.13 (prior) — no change to §VII.G downgrade criteria.
- **§VII.J (NEW): Two-Layer Gold Protocol (Relation + Realism) — Upgraded from §VII.I** — operationalises the §VII.I proposal into a two-layer protocol:
  - Layer 1: relation label (unchanged from §VII).
  - Layer 2: claim realism (NEW) — `claim_realism_score_1_to_5`, `claim_realism_issue` (9 categorical values), `claim_realism_usable_for_paper` (derived).
  - Annotation workflow: priority sampling (111 strong_action first), two-annotator + adjudication, blinding, separate passes for Layer 1 and Layer 2.
  - Pre-registered realism thresholds: 25% class-level, 25% paper-level (frozen before gold collection).
  - Heuristic realism pre-screen (already conducted, NOT gold): 21/444 (4.7%) overall, 10/111 (9.0%) for strong_action — both below 25% threshold but strong_action rate is non-trivial.
  - Relationship to RIGOURATE: RIGOURATE uses natural author-written claims so realism is not a concern; SimClaim uses generated counterfactual claim variants so realism IS a concern; the two-layer protocol is the falsifiable mechanism.

### §VIII. Discussion
- §VIII.A–§VIII.F: byte-identical to V3.13 (prior).
- §VIII.F already explicitly discusses "Unified overstatement scores are useful, but they may collapse different failure modes" and "strong_action_overclaim is not just 'a mild overclaim with a higher score'" — these points are reinforced by the new §VI.E empirical evidence.

### §IX. Limitations
- Items 1–10: byte-identical to V3.13 (prior).
- **Item 11 (NEW): The RIGOURATE-style scalar baseline (§VI.E) is a proxy, not an official RIGOURATE reproduction.** Documents the BLOCKED status of official RIGOURATE artifacts, the proxy labelling, the BLOCKED nli_scalar_score baseline, and the caveat that conclusions may shift when official RIGOURATE becomes available.
- Additional practical limitations: items (g) RIGOURATE-style baselines are proxies; (h) nli_scalar_score BLOCKED; (i) heuristic realism pre-screen is pattern-based, NOT a substitute for human realism annotation.

### §X. Conclusion
- Added paragraph on §VI.E RIGOURATE-style scalar proxy baseline results (proxy NOT official RIGOURATE; scalar cannot distinguish mild from strong; R4 retains screening value; complementarity is empirical motivation for four-class decomposition; validation-pending).
- Updated gold validation reference: "pre-registered gold adjudication (§VII) — now upgraded to a two-layer gold protocol (§VII.J: Layer 1 relation label + Layer 2 claim realism, with pre-registered 25% class-level and paper-level realism thresholds)".

### Appendix B. Language Guardrails
- "Forbidden claims" list now includes: "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH", "SimClaim is a natural-prevalence corpus", "The silver-stage screening finding transfers to natural scientific writing", "We introduce scientific overstatement detection / evidence sufficiency calibration as a new field", "First work / first benchmark / first to propose evidence sufficiency calibration".

---

## 4. What did NOT change (frozen from V3.12 / V3.13 prior)

- All §VI.A–§VI.D numbers (R4 strong-F1 0.3967, LLM strong-F1 0.0769, macro-F1 values, bootstrap CI, ablation, FP/TP ratio).
- All §VIII.D numbers (Evidence Necessity Check, Screening Utility Test, Label-Shift Stress Test).
- The frozen R4 method (thresholds t_contra=0.48, t_strong=0.535, t_svm=0.51; routing order; contradiction-gated escalation).
- The four-step taxonomy decision tree (Figure 2) and boundary rules.
- The §VII.G pre-registered downgrade criteria (mild_vs_strong κ < 0.40 → taxonomy revised; strong_action retention < 0.50 → claim downgraded; etc.).
- The R4 macro-F1 < LLM macro-F1 fact (0.3280 vs. 0.5523 on matched 100).
- The gold-not-done fact (all entries in Tables G1–G3 are `TO_BE_FILLED_AFTER_GOLD`).
- The silver-not-gold fact (all 444 SimClaim labels are AI-preannotated, author-screened silver).
- The SimClaim-is-counterfactual fact (§V.A transparency statement).
- The author sanity audit results (40 cases, 25 questionable/unclear, 62.5% flag rate).
- The LLM judge results labelling ("small-sample controlled evaluation, N ≤ 200"; never merged with SimClaim main results; never claimed as gold standard).

---

## 5. Prohibitions enforced (all verified PASS)

1. No new experiments (only proxy baseline construction on existing data) — PASS.
2. No paid API calls — PASS.
3. No gold annotation — PASS.
4. No modification of original data — PASS.
5. No modification of V3.12 — PASS (V3.12 file untouched).
6. No proxy written as official RIGOURATE — PASS (all proxy outputs explicitly labelled).
7. No blocked plan written as completed result — PASS (nli_scalar_score BLOCKED with `blocked_reason`; no result fabricated).
8. No silver written as gold — PASS.
9. No claim of being the first to propose scientific overstatement / evidence-force calibration — PASS.
10. No deletion of the R4 macro-F1 < LLM fact — PASS.
11. No deletion of the gold-not-done fact — PASS.

---

## 6. File inventory (this version)

- `CESE_OCN_V3_13_rigourate_differentiated_realism_aware.md` — main paper draft.
- `CESE_OCN_V3_13_rigourate_differentiated_realism_aware.docx` — docx export.
- `V3_13_positioning_change_log.md` — this file.
- `V3_13_related_work_diff_table.md` — RIGOURATE / ForceBench / CLAIM-BENCH / CESE-OCN comparison table (standalone).
- `V3_13_claims_allowed_for_paper.md` — list of allowed and forbidden claims for this version.
- `V3_13_advisor_cover_note_cn.md` — advisor cover note in Chinese.

---

## 7. Relationship to prior V3.13 release

The prior V3.13 release (`V3_13_differentiated_against_rigourate_forcebench/`) is preserved unchanged. This version (V3.13 RIGOURATE-Differentiated + Realism-Aware) is a separate output directory (`V3_13_rigourate_differentiated_realism_aware/`) that builds on the prior V3.13 by integrating the RIGOURATE-style proxy baseline results (§VI.E) and upgrading the gold-realism audit (§VII.I) to a two-layer gold protocol (§VII.J). The prior V3.13's positioning, Related Work, Abstract, Introduction, Data transparency, and Discussion are preserved; this version adds §VI.E, §VII.J, §IX item 11, and updates the Abstract, §X Conclusion, and title to reflect the integration.
