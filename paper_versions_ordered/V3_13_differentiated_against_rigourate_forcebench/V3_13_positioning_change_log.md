# V3.13 Positioning Change Log (V3.12.1 → V3.13)

**Date:** 2026-07-05
**Source version:** V3.12.1 (`D:\ocn\paper_versions_ordered\V3_12_1_advisor_send_clean\`)
**Target version:** V3.13 (`D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\`)
**Scope:** Positioning-level changes only. This log focuses on the *positioning narrative* shift; the full per-line revision log is in `V3_13_revision_log.md`.

## 1. The Positioning Shift in One Sentence

**V3.12.1 positioning:** "CESE-OCN is an evidence sufficiency calibration framework introducing a new task and four-class taxonomy."

**V3.13 positioning:** "CESE-OCN is a fine-grained relation-type decomposition and high-risk action-overclaim screening complement on the *existing* scientific overstatement / evidence-force calibration track, building on RIGOURATE, ForceBench, and CLAIM-BENCH."

## 2. Why the Shift Was Needed

V3.12.1 carried a同质化风险 (homogeneity risk): the paper claimed to introduce evidence sufficiency calibration as a distinct task, but RIGOURATE [30] already quantifies scientific overstatement, ForceBench [35] already tests evidence-force mismatch contrastively, and CLAIM-BENCH [28] already evaluates scientific claim-evidence reasoning. Without explicit positive positioning against these works, the paper's contribution could be misread as "ignoring prior work" or "claiming a new field that already exists."

V3.13 makes the differentiation explicit and positive: we acknowledge the prior works' strengths, state precisely what CESE-OCN adds (relation-type decomposition, strong_action_overclaim screening), and frame the contribution as complementary rather than competing.

## 3. Positioning Changes by Section

### 3.1 Title-Level Positioning (Abstract)

| V3.12.1 | V3.13 |
| --- | --- |
| "We formulate this as a distinct task, **evidence sufficiency calibration**" | "Building on recent work on scientific overstatement scoring and evidence-force calibration (RIGOURATE [30], the evidence-licensed claims perspective [31], ForceBench [35]), we study a fine-grained diagnostic variant of evidence-sufficiency calibration" |
| "The contribution is framework-level and taxonomy-level: a falsifiable evidence-sufficiency calibration framework..." | "The contribution is a fine-grained relation-type decomposition with a frozen, protocol-locked validation mechanism — not the introduction of scientific overstatement detection as a new field, and not a claim of state-of-the-art overstatement detection." |

### 3.2 Introduction Opening (§I)

| V3.12.1 | V3.13 |
| --- | --- |
| Opens with: "Scientific claim verification is typically framed as a three-class task..." (implies the field is blank) | Opens with: "Recent work has begun to quantify scientific overstatement and evidence-force mismatch. RIGOURATE [30]... ForceBench [35]... CLAIM-BENCH [28]... However, less attention has been paid to whether different overclaim relations require different diagnostic treatment, especially high-risk action/deployment overclaims." |

### 3.3 Contribution List

| V3.12.1 (5 contributions) | V3.13 (3 contributions) |
| --- | --- |
| 1. Problem formulation (implies new task) | (merged into the new framing) |
| 2. Four-class taxonomy | **1. Taxonomy contribution** (decomposition, complementary to RIGOURATE / ForceBench / CLAIM-BENCH) |
| 3. Controlled diagnostic benchmark | (merged into 1 and 2) |
| 4. Structured screening framework | **3. Screening-method contribution** (R4 as complement, not SOTA) |
| 5. Controlled silver-stage evidence + pre-registered validation | **2. Diagnostic contribution** (LLM under-detection, controlled silver-stage) |
| (implicit "first to propose" tone) | Explicit: "positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field" |

### 3.4 Related Work (§II.A — NEW)

V3.12.1 had a single brief paragraph mentioning RIGOURATE. V3.13 adds a full subsection `### A. Relation to Scientific Overstatement and Evidence-Force Calibration` with:
- Three positive-acknowledgment paragraphs (RIGOURATE, ForceBench, CLAIM-BENCH), each stating the prior work's strengths first, then the difference, then the complementarity.
- Table X (positioning table, 4 rows × 7 columns).
- A closing paragraph explicitly stating the contribution is on the existing track, not a new field.

### 3.5 Data Section (§V.A — NEW Transparency Statement)

V3.12.1 described SimClaim's data scale and balanced design without explicitly stating it is a controlled counterfactual set. V3.13 adds a `**Synthetic / counterfactual transparency statement.**` paragraph explicitly stating:
- SimClaim is **not** a natural-prevalence corpus of author-written claims.
- It is a **controlled counterfactual diagnostic set**: evidence spans from real papers, claim variants generated.
- The four-way balanced design is a *deliberate construction*, not natural prevalence.
- SimClaim is appropriate for pressure-testing boundary recognition, NOT for estimating real-world prevalence.
- Cross-reference to §VII.I realism audit.

### 3.6 Discussion (§VIII.F — NEW)

V3.13 adds a new subsection `### F. Why Fine-Grained Relation Typing Is Valuable` arguing that different overclaim relations have different risk semantics (writing-strength vs. risk-bearing vs. correctness) and that a continuous score alone cannot distinguish them. This supports the taxonomy-level argument independent of R4's performance.

### 3.7 Gold Protocol (§VII.I — NEW)

V3.13 adds a new subsection `### I. Proposed Gold-Realism Audit Extension` specifying the `claim_realism_score_1_to_5` and `claim_realism_issue` fields, annotator protocol, and pre-registered 25% class-level and 25% paper-level realism thresholds. This addresses the natural-claim transferability risk surfaced by the §V.A transparency statement.

### 3.8 Limitations (§IX)

V3.13 adds two new items:
- **Item 9:** "Differentiation from RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not empirical head-to-head."
- **Item 10:** "SimClaim is a controlled counterfactual diagnostic set, not a natural-prevalence corpus."

And adds practical limitation (f): "the comparison against RIGOURATE / ForceBench / CLAIM-BENCH is positioning-level, not a head-to-head empirical benchmark."

### 3.9 Conclusion (§X)

V3.13 rewrites the first sentence to: "fine-grained evidence-sufficiency relation diagnosis framework for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field." Adds an explicit paragraph stating the differentiation is positioning-level with cross-reference to §IX item 9.

### 3.10 Language Guardrails (Appendix B)

V3.13 adds 5 new forbidden claims:
- "We introduce scientific overstatement detection / evidence sufficiency calibration as a new field."
- "First work / first benchmark / first to propose evidence sufficiency calibration."
- "CESE-OCN outperforms RIGOURATE / ForceBench / CLAIM-BENCH."
- "SimClaim is a natural-prevalence corpus."
- "The silver-stage screening finding transfers to natural scientific writing."

## 4. What Did NOT Change (Positioning-Relevant)

- **All experimental numbers preserved byte-identical** from V3.12.1: R4 strong-F1 0.3967, LLM strong-F1 0.0769, R4 macro-F1 0.3280, GPT-5.5 macro-F1 0.5523, bootstrap CI [0.1058, 0.1988], FP/TP 2.89, 50% retention CI [-0.026, +0.255], 62.5% audit questionable/unclear.
- **R4 macro-F1 < LLM fact preserved.** The paper still says "R4 macro-F1 = 0.3280 vs. GPT-5.5 = 0.5523" and "R4 is positioned as a screening-oriented complement, not a replacement and not a state-of-the-art overstatement detector."
- **Gold-not-done fact preserved.** §VII, §IX item 1, §X all retain "gold validation is planned but not completed."
- **Non-gold caveat preserved.** §VIII.D, §IX item 8, §VII.H all retain "non-gold robustness analysis, does not replace gold adjudication."
- **50% retention caveat preserved.** §VIII.D.C "positive but statistically weaker / CI crosses zero" wording preserved.
- **No prior version modified.** V3.12.1, V3.12, V3.11, V3.10.1, V3.9 all preserved unchanged.

## 5. Positioning Risk After V3.13

| Risk | Status after V3.13 | Mitigation |
| --- | --- | --- |
| 同质化风险 (homogeneity with RIGOURATE / ForceBench / CLAIM-BENCH) | **Reduced.** §II.A + Table X make the differentiation explicit and positive. | P0 polish; P2 empirical head-to-head (plan-only). |
| 首创大方向表述 (residual "first to propose" framing) | **Eliminated.** Body text uses "fine-grained diagnostic variant on the existing track." Forbidden-claims list updated. | P0.5 re-read. |
| SimClaim 自然性风险 (natural-prevalence claim) | **Addressed.** §V.A counterfactual transparency + §VII.I realism audit. | P1 gold pilot with realism audit. |
| Empirical head-to-head 缺失 (no empirical comparison) | **Acknowledged.** §IX item 9 states positioning-level only. | P2 RIGOURATE-style baseline (plan-only). |
| Prompt-robustness 缺失 (LLM under-detection may be prompt artifact) | **Acknowledged.** §IX item 3 retains "under the tested prompts." | P3 few-shot / CoT (plan-only). |
| Low-prevalence 缺失 (screening utility bounded to balanced set) | **Acknowledged.** §V.A states design is balanced, not natural. | P4 prevalence simulation (plan-only). |

## 6. Net Effect on Paper Positioning

After V3.13, the paper's positioning is:

- **Modest and defensible:** "fine-grained relation-type decomposition on the existing track" — no overclaim of opening a new field.
- **Empirically honest:** all numbers preserved; silver-stage qualifier retained; gold not done; R4 macro-F1 < LLM; non-gold caveat retained.
- **Differentiated:** §II.A + Table X make the complementarity to RIGOURATE / ForceBench / CLAIM-BENCH explicit.
- **Transparent about SimClaim:** §V.A counterfactual transparency statement; §VII.I realism audit proposed.
- **Forward-looking:** P0–P4 strengthening plan specifies what would be done in V3.14+ to convert positioning-level claims to empirical claims.

The paper is ready for advisor review with the new positioning.
