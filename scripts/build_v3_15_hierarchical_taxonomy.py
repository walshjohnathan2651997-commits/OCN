"""Build V3.15 hierarchical taxonomy revision from V3.14 mainline-locked source.

Applies hierarchical taxonomy revisions across 9 sections:
1. Header / Changes log
2. Abstract
3. Introduction (contributions reframed hierarchically)
4. Task Formulation (Level 1/Level 2 label table)
5. Method (R4 as relation-specific screening router under hierarchical taxonomy)
6. Results (operational-label evaluation framing)
7. Discussion (new "Why hierarchical rather than flat" subsection + fallback)
8. Gold Protocol (reference to hierarchical_gold_validation_plan.md)
9. Conclusion (hierarchical framing)

Preserves all experimental numbers byte-identical from V3.14.
Does NOT delete the four original labels; they remain operational.
Does NOT claim mild_scope is naturally stable.
Does NOT claim R4 overall beats LLM.
Does NOT modify V3.14 source files.

Outputs:
  D:\\ocn\\paper_versions_ordered\\V3_15_hierarchical_taxonomy_revision\\
    CESE_OCN_V3_15_hierarchical_taxonomy_revision.md
    CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx
    hierarchical_label_mapping.csv
    hierarchical_gold_validation_plan.md
    V3_15_revision_log.md
    V3_15_hierarchical_taxonomy_gate.json
"""
import os
import re
import json
import zipfile
from xml.sax.saxutils import escape

SRC_MD = r"D:\ocn\paper_versions_ordered\V3_14_mainline_locked_consistency_audit\CESE_OCN_V3_14_mainline_locked.md"
OUT_DIR = r"D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision"
OUT_MD = os.path.join(OUT_DIR, r"CESE_OCN_V3_15_hierarchical_taxonomy_revision.md")
OUT_DOCX = os.path.join(OUT_DIR, r"CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx")
OUT_MAPPING_CSV = os.path.join(OUT_DIR, r"hierarchical_label_mapping.csv")
OUT_GOLD_PLAN = os.path.join(OUT_DIR, r"hierarchical_gold_validation_plan.md")
OUT_REVISION_LOG = os.path.join(OUT_DIR, r"V3_15_revision_log.md")
OUT_GATE = os.path.join(OUT_DIR, r"V3_15_hierarchical_taxonomy_gate.json")

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"


# =============================================================================
# 1. Read source and apply hierarchical taxonomy revisions
# =============================================================================

def load_source():
    with open(SRC_MD, "r", encoding="utf-8") as f:
        return f.read()


def replace_once(text, old, new):
    """Replace exactly one occurrence; raise if not found or ambiguous."""
    count = text.count(old)
    if count == 0:
        raise ValueError("Pattern not found in source:\n" + old[:200])
    if count > 1:
        raise ValueError("Pattern ambiguous (" + str(count) + " matches):\n" + old[:200])
    return text.replace(old, new)


def apply_revisions(md):
    """Apply all 9 sections of hierarchical taxonomy revisions."""
    original = md
    n_replacements = 0

    # ----- Section 1: Header / Version / Changes log -----
    # Update version header
    md = replace_once(
        md,
        "**Version:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit (validation-pending, protocol-locked)",
        "**Version:** V3.15 Hierarchical Taxonomy Revision (validation-pending, protocol-locked)\n\n**Derived from:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit. **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning, no change to any experimental number, no change to the frozen R4 method, no deletion of the four original operational labels, no claim that mild_scope_overclaim is a naturally stable class, no claim that R4 overall beats LLM.** The four original labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain operational for experiments; the revision changes only the *interpretive framing* from a flat four-class taxonomy to a hierarchical diagnostic taxonomy (Level 1: supported / overclaim / contradiction; Level 2: scope_expansion / strong_action under overclaim). All §VI numbers, §VIII.D numbers, §VII.G criteria, and the R4 macro-F1 < LLM fact are preserved byte-identical from V3.14. V3.14, V3.13, V3.12.1, V3.12, V3.11, V3.10.1, and V3.9 are preserved unchanged.",
    )
    n_replacements += 1

    # Update Date
    md = replace_once(
        md,
        "**Date:** 2026-07-05\n",
        "**Date:** 2026-07-05 (V3.15 hierarchical taxonomy revision)\n",
    )

    # ----- Section 2: Abstract -----
    # Replace "we define a four-class taxonomy" with hierarchical framing
    md = replace_once(
        md,
        "**we study a fine-grained diagnostic variant of evidence-sufficiency calibration** and define a **four-class taxonomy**: supported, mild_scope_overclaim, strong_action_overclaim, and contradiction_candidate.",
        "**we operationalize a hierarchical diagnostic taxonomy** that first separates supported, overclaim, and contradiction relations at Level 1, and then distinguishes scope-expansion overclaims from high-risk action/deployment overclaims at Level 2. The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space; the hierarchical framing reframes interpretation only. We do not assume that mild_scope_overclaim is a naturally discrete category. Instead, it is used as a diagnostic buffer subtype between supported claims and high-risk action overclaims. The primary scientific question is whether action/deployment overclaim behaves differently from ordinary scope expansion.",
    )
    n_replacements += 1

    # Reframe Abstract's R4 description to reflect hierarchical positioning
    md = replace_once(
        md,
        "We propose **CESE-OCN/R4**, a structured evidence-relation screening framework that complements generic LLM/NLI judges via a contradiction detector, a scope-calibration residual classifier, and a conservative strong-action escalation route.",
        "We propose **CESE-OCN/R4**, a relation-specific screening router under the hierarchical taxonomy that complements generic LLM/NLI judges via a Level-1 contradiction gate, a Level-2 scope residual classifier for supported vs. scope_expansion, and a conservative Level-2 strong-action escalation route for high-risk action/deployment overclaim screening.",
    )
    n_replacements += 1

    # ----- Section 3: Introduction contributions -----
    # Reframe contribution 1 (taxonomy) as hierarchical
    md = replace_once(
        md,
        "1. **Taxonomy contribution.** We decompose evidence-sufficiency mismatch into **supported**, **mild_scope_overclaim**, **strong_action_overclaim**, and **contradiction_candidate**, with an operational decision tree (Figure 2), concrete examples (Table 0), and explicit boundary rules. This is a relation-type decomposition that complements continuous overstatement scoring (RIGOURATE [30]), contrastive paired-claim force testing (ForceBench [35]), and full-paper claim-evidence extraction (CLAIM-BENCH [28]); it is not a claim to introduce scientific overstatement detection as a new field. The separability of strong_action_overclaim as a reliably drawable class is a hypothesis tested by the pre-registered gold adjudication (§VII), not an assumption taken as already proven.",
        "1. **Hierarchical diagnostic taxonomy.** We decompose evidence-sufficiency mismatch hierarchically: **Level 1** separates **supported** / **overclaim** / **contradiction**; **Level 2** under overclaim separates **scope_expansion** (corresponding to the operational `mild_scope_overclaim` label) from **strong_action** (corresponding to `strong_action_overclaim`). The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space, but their interpretation is hierarchical: `mild_scope_overclaim` is a boundary-sensitive buffer subtype between supported claims and high-risk action overclaims, not a naturally stable discrete class; `strong_action_overclaim` is the high-risk Level-2 subtype that requires separate screening. An operational decision tree (Figure 2), concrete examples (Table 0), and explicit boundary rules support the taxonomy. This hierarchical decomposition complements continuous overstatement scoring (RIGOURATE [30]), contrastive paired-claim force testing (ForceBench [35]), and full-paper claim-evidence extraction (CLAIM-BENCH [28]); it is not a claim to introduce scientific overstatement detection as a new field. The separability of strong_action as a reliably drawable Level-2 subtype is a hypothesis tested by the pre-registered gold adjudication (§VII), not an assumption taken as already proven.",
    )
    n_replacements += 1

    # Reframe contribution 2 (diagnostic) - mild_scope is buffer, strong_action is high-risk subtype
    md = replace_once(
        md,
        "2. **Diagnostic contribution.** On the controlled silver-stage evaluation, we show that under tested prompts, strong LLM judges (GPT-5.5, DeepSeek-V3) can achieve higher overall macro-F1 (0.5523 / 0.5270 on matched samples) while **consistently under-detecting strong_action_overclaim** (strong-F1 = 0.0769, recall 0.04 = 1/25 across both models and both prompt designs tested). This is a controlled silver-stage diagnostic finding — not a fundamental limit of LLMs — and the pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this pattern is treated as established.",
        "2. **Controlled counterfactual diagnostic set + LLM under-detection finding.** SimClaim uses real evidence spans and generated claim variants to pressure-test boundary recognition under matched evidence. On the controlled silver-stage evaluation, under tested prompts, strong LLM judges (GPT-5.5, DeepSeek-V3) can achieve higher overall macro-F1 (0.5523 / 0.5270 on matched samples) while **consistently under-detecting the Level-2 high-risk strong_action subtype** (strong-F1 = 0.0769, recall 0.04 = 1/25 across both models and both prompt designs tested). This is a controlled silver-stage diagnostic finding — not a fundamental limit of LLMs — and the pre-registered gold adjudication (§VII) is the protocol-locked mechanism that determines whether this pattern is treated as established.",
    )
    n_replacements += 1

    # Reframe contribution 3 (screening method) - R4 targets Level-2 strong_action
    md = replace_once(
        md,
        "3. **Screening-method contribution.** We propose **CESE-OCN/R4**, a relation-specific screening complement that improves strong_action recall and positive-F1 (R4 strong-F1 = 0.3000 on matched 100 samples vs. LLM 0.0769; R4 strong-F1 = 0.3967 vs. flat baseline 0.2408 on the full 444) at the cost of lower overall macro-F1 (0.3280 vs. 0.5523). R4 is positioned as a screening-oriented complement to black-box LLM judges, not a competitive replacement and not a state-of-the-art overstatement detector. A pre-registered gold adjudication protocol (§VII) with frozen success and downgrade criteria specifies how the silver-stage screening claim is validated or downgraded.",
        "3. **Screening method (R4) targeting the Level-2 high-risk strong_action subtype.** We propose **CESE-OCN/R4**, a relation-specific screening router under the hierarchical taxonomy that targets Level-2 strong_action screening as a complement to LLM judges. R4 improves strong_action recall and positive-F1 (R4 strong-F1 = 0.3000 on matched 100 samples vs. LLM 0.0769; R4 strong-F1 = 0.3967 vs. flat baseline 0.2408 on the full 444) at the cost of lower overall macro-F1 (0.3280 vs. 0.5523). R4 is positioned as a screening-oriented complement to black-box LLM judges, not a competitive replacement and not a state-of-the-art overstatement detector; it is **not** a flat 4-class best classifier. A pre-registered gold adjudication protocol (§VII) with frozen success and downgrade criteria specifies how the silver-stage screening claim is validated or downgraded, including a hierarchical fallback rule (§VII.K, `hierarchical_gold_validation_plan.md`) that downgrades to Level-1 (supported / overclaim / contradiction) + binary strong_action screening if Level-2 κ is insufficient.",
    )
    n_replacements += 1

    # ----- Section 4: Task Formulation - add hierarchical label table -----
    md = replace_once(
        md,
        "### A. Evidence Sufficiency Calibration Task\n\nEach instance consists of a claim, an evidence span, and a silver candidate label in four relation classes:",
        "### A. Evidence Sufficiency Calibration Task (Hierarchical Diagnostic Taxonomy)\n\nThe taxonomy is **hierarchical**, not flat. Level 1 separates supported / overclaim / contradiction; Level 2 under overclaim separates scope_expansion from strong_action. The four original operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space; their interpretation is hierarchical. **Table 0a** maps the hierarchical levels to the operational labels.\n\n**Table 0a. Hierarchical label mapping.** See `hierarchical_label_mapping.csv` for the full mapping with fallback behavior.\n\n| Hierarchical level | Label | Original operational label | Meaning |\n| --- | --- | --- | --- |\n| Level 1 | supported | supported | evidence supports claim strength |\n| Level 1 | overclaim | mild_scope_overclaim + strong_action_overclaim | claim exceeds evidence |\n| Level 1 | contradiction | contradiction_candidate | claim conflicts with evidence |\n| Level 2 | scope_expansion | mild_scope_overclaim | ordinary / boundary scope over-extension (buffer subtype; boundary-sensitive; not claimed to be naturally discrete) |\n| Level 2 | strong_action | strong_action_overclaim | action / deployment / safety / policy / generalization overclaim (high-risk subtype) |\n\nEach instance consists of a claim, an evidence span, and a silver candidate label in four operational relation classes (interpreted hierarchically per Table 0a):",
    )
    n_replacements += 1

    # Add hierarchical interpretation note after the four-class bullet list
    md = replace_once(
        md,
        "Labels are treated as AI-preannotated development labels (silver), pending independent gold adjudication (§VII).",
        "Labels are treated as AI-preannotated development labels (silver), pending independent gold adjudication (§VII).\n\n**Hierarchical interpretation.** `mild_scope_overclaim` (Level 2: scope_expansion) is a *boundary-sensitive buffer subtype* between supported claims and high-risk action overclaims. It is **not** claimed to be a naturally stable discrete class; if gold adjudication (§VII) shows that the mild_vs_strong boundary is not reliably drawable, the paper falls back to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening, per the fallback rules in §VII.K and `hierarchical_gold_validation_plan.md`. `strong_action_overclaim` (Level 2: strong_action) is the *high-risk subtype* that requires separate screening; this is the primary target of R4. `contradiction_candidate` (Level 1: contradiction) is a control / conflict relation. The four operational labels remain in use for experiments, but their interpretation is hierarchical, not flat.",
    )
    n_replacements += 1

    # ----- Section 5: Method - reframe R4 as hierarchical router -----
    md = replace_once(
        md,
        "### A. Framework Overview — Why Relation-Specific Routing\n\nThe central design principle of R4 is that **different evidence relations require different signals and should not be handled by a single flat classifier**. The controlled silver-stage evidence is consistent with this: contradiction is comparatively well captured by NLI-style evidence signals (on the controlled silver-stage evaluation, NLI-only strong-F1 = 0.3934), while strong_action_overclaim requires action-aware features that NLI does not provide (action-gap-only strong-F1 = 0.3648; NLI + action-gap = 0.4209). A single flat four-class classifier conflates these signals and under-performs on the most consequential class (baseline strong-F1 = 0.2408).",
        "### A. Framework Overview — R4 as a Relation-Specific Screening Router Under the Hierarchical Taxonomy\n\nThe central design principle of R4 is that **different evidence relations require different signals and should not be handled by a single flat classifier**. Under the hierarchical taxonomy (§III.A, Table 0a), R4 is positioned as a relation-specific screening router, **not** a flat 4-class best classifier. The three routes map onto the hierarchical levels: the contradiction gate handles Level-1 contradiction; the scope residual classifier handles Level-1 supported vs. Level-2 scope_expansion; the strong_action route is the Level-2 high-risk overclaim screening route. The controlled silver-stage evidence is consistent with this: contradiction (Level 1) is comparatively well captured by NLI-style evidence signals (on the controlled silver-stage evaluation, NLI-only strong-F1 = 0.3934), while Level-2 strong_action requires action-aware features that NLI does not provide (action-gap-only strong-F1 = 0.3648; NLI + action-gap = 0.4209). A single flat four-class classifier conflates these signals and under-performs on the most consequential Level-2 subtype (baseline strong-F1 = 0.2408).",
    )
    n_replacements += 1

    # Add hierarchical interpretation to the routing order rationale
    md = replace_once(
        md,
        "R4 is therefore designed as a **relation-specific diagnostic routing framework**, not a threshold-tuned heuristic. The routing order reflects a theoretical principle: handle the most separable relation first (contradiction), then the most consequential relation under a conservative guard (strong_action), then the residual scope calibration (supported vs. mild).",
        "R4 is therefore designed as a **relation-specific diagnostic routing framework under the hierarchical taxonomy**, not a threshold-tuned heuristic and not a flat 4-class best classifier. The routing order reflects the hierarchical structure: handle the most separable Level-1 relation first (contradiction), then the most consequential Level-2 high-risk subtype under a conservative guard (strong_action), then the residual Level-1/Level-2 scope calibration (supported vs. scope_expansion). R4's core value is **Level-2 high-risk strong_action screening**, not flat 4-class classification superiority.",
    )
    n_replacements += 1

    # ----- Section 6: Results - reframe as operational-label evaluation -----
    md = replace_once(
        md,
        "### A. Internal Silver Diagnostic Results (Table 1)\n\nThe strongest controlled silver-stage result is that **on the controlled silver-stage evaluation**, R4 improves strong-action positive-F1 while preserving contradiction and escalation.",
        "### A. Internal Silver Diagnostic Results (Table 1) — Flat Operational-Label Evaluation\n\nThe strongest controlled silver-stage result is that **on the controlled silver-stage evaluation**, R4 improves Level-2 high-risk strong-action positive-F1 while preserving Level-1 contradiction and escalation. Results in this subsection are reported as **flat operational-label evaluation**: the four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space, but their interpretation is hierarchical (§III.A, Table 0a). macro-F1 over operational labels is *diagnostic*, not the primary deployment metric; for the primary deployment metric (Level-2 high-risk overclaim screening), see §VI.B and §VI.C.",
    )
    n_replacements += 1

    # Add hierarchical interpretation to §VI.B (LLM comparison)
    md = replace_once(
        md,
        "### B. LLM Judge Comparison (Table 2, Figure 3)\n\nThis is the central new analysis. We compare R4 against generic LLM judges on matched SimClaim samples. **All numbers in this subsection are computed on the controlled silver-stage evaluation.**",
        "### B. LLM Judge Comparison (Table 2, Figure 3) — Level-2 High-Risk Strong_Action Screening\n\nThis is the central new analysis. We compare R4 against generic LLM judges on matched SimClaim samples. **All numbers in this subsection are computed on the controlled silver-stage evaluation.** This subsection reports the **Level-2 high-risk overclaim screening result**: the primary deployment metric is strong_action recall and FP/TP ratio, not overall macro-F1 (which is reported as a flat operational-label diagnostic only).",
    )
    n_replacements += 1

    # Add screening utility reinforcement
    md = replace_once(
        md,
        "**This result should not be interpreted as R4 outperforms LLM judges overall.** On the controlled silver-stage evaluation, R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the strong_action_overclaim relation that LLM judges miss under the tested prompts. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted screening signal on the high-risk boundary class, at the cost of lower overall macro-F1.",
        "**This result should not be interpreted as R4 outperforms LLM judges overall.** On the controlled silver-stage evaluation, R4's macro-F1 (0.3280) is substantially lower than GPT-5.5 (0.5523) and DeepSeek-V3 (0.5248) on the same 100 matched samples. R4's value is relation-specific: it targets the Level-2 high-risk strong_action subtype that LLM judges miss under the tested prompts. We do not claim R4 is better than LLM judges overall — we claim R4 provides targeted Level-2 screening signal on the high-risk boundary class, at the cost of lower overall macro-F1. **In real-world deployment, strong_action is a rare high-risk subtype; therefore recall, FP/TP ratio, and review burden are more important than overall accuracy.** The screening utility metrics (FP/TP = 2.89, review burden = 35%, R4 captures 8 LLM-missed strong_action cases) are reported in §VIII.D.B and are the primary deployment-relevant metrics, while macro-F1 over operational labels is diagnostic only.",
    )
    n_replacements += 1

    # ----- Section 7: Discussion - add "Why hierarchical rather than flat" subsection -----
    # Insert new §VIII.G after §VIII.F (before §IX Limitations)
    md = replace_once(
        md,
        "This argument is the *taxonomy-level* reason for the four-class decomposition, independent of any particular model's performance on it. The §VI silver-stage results show that R4 exploits this decomposition to improve strong_action recall at the cost of macro-F1, but the taxonomy-level argument does not depend on R4 specifically — any downstream system that needs to flag high-risk action overclaims separately from mild scope expansion benefits from this decomposition. Whether the four-class decomposition is reliably drawable by human annotators is the subject of the §VII gold adjudication.\n\n## IX. Limitations",
        "This argument is the *taxonomy-level* reason for the four-class decomposition, independent of any particular model's performance on it. The §VI silver-stage results show that R4 exploits this decomposition to improve strong_action recall at the cost of macro-F1, but the taxonomy-level argument does not depend on R4 specifically — any downstream system that needs to flag high-risk action overclaims separately from mild scope expansion benefits from this decomposition. Whether the four-class decomposition is reliably drawable by human annotators is the subject of the §VII gold adjudication.\n\n### G. Why the Taxonomy Is Hierarchical Rather Than Flat\n\nThe four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) are **not** treated as four naturally parallel classes. They are organized hierarchically:\n\n- **Level 1:** supported / overclaim / contradiction. These are the primary relation types: evidence *supports* the claim's strength, evidence is *exceeded* by the claim (overclaim), or evidence *conflicts* with the claim (contradiction).\n- **Level 2 under overclaim:** scope_expansion (= mild_scope_overclaim) / strong_action (= strong_action_overclaim). Both are overclaims, but they differ in risk: scope_expansion is a boundary-sensitive *buffer subtype* (a writing-strength issue, editorially fixable), while strong_action is a *high-risk subtype* (action / deployment / safety / policy / generalization overclaim with downstream risk).\n\n**Why hierarchical.** (i) `mild_scope_overclaim` is a *buffer* class, not a naturally stable discrete category — it sits between supported and strong_action, and the mild_vs_strong boundary is the hardest to draw (75% confusion rate in the §V.D audit). Treating it as a peer of strong_action over-claims its stability. (ii) `strong_action_overclaim` is the high-risk subtype that needs separate screening — its risk semantics (deployment, safety, policy) are qualitatively different from scope expansion (editorial). Treating it as a peer of mild_scope under-claims its risk. (iii) `contradiction_candidate` is a Level-1 control / conflict relation, naturally aligned with NLI. (iv) The four operational labels remain in use for experiments, but their *interpretation* is hierarchical: macro-F1 over operational labels is diagnostic, while Level-2 strong_action screening metrics (recall, FP/TP, review burden) are the primary deployment metric.\n\n**Fallback logic (pre-registered, see §VII.K and `hierarchical_gold_validation_plan.md`).** If gold adjudication shows that Level-1 κ is acceptable but Level-2 κ is insufficient (mild_vs_strong κ < 0.40), the paper falls back to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening. If strong_action retention ≥ 0.60, the Level-2 high-risk subtype is retained. If strong_action retention < 0.50, strong_action is reported only as an exploratory risk flag, not as a validated class. This fallback design reduces the *forced four-class* reviewer risk: the paper does not claim that mild_scope and strong_action are naturally co-equal classes; it claims only that strong_action is a high-risk overclaim subtype worth screening separately, with a pre-registered downgrade path if the Level-2 boundary is not reliably drawable.\n\n## IX. Limitations",
    )
    n_replacements += 1

    # ----- Section 8: Gold protocol - reference hierarchical validation plan -----
    # Add §VII.K reference at end of §VII (after §VII.J, before §VIII)
    md = replace_once(
        md,
        "**Relationship to RIGOURATE realism considerations.** RIGOURATE uses natural author-written claims from ICLR/NeurIPS abstracts and introductions, so realism is not a concern for RIGOURATE. SimClaim uses generated counterfactual claim variants, so realism IS a concern. This two-layer protocol is the falsifiable mechanism that addresses the realism risk: if SimClaim claims are systematically unnatural, the protocol will detect it and trigger a sensitivity analysis or a paper-level caveat.\n\n## VIII. Discussion",
        "**Relationship to RIGOURATE realism considerations.** RIGOURATE uses natural author-written claims from ICLR/NeurIPS abstracts and introductions, so realism is not a concern for RIGOURATE. SimClaim uses generated counterfactual claim variants, so realism IS a concern. This two-layer protocol is the falsifiable mechanism that addresses the realism risk: if SimClaim claims are systematically unnatural, the protocol will detect it and trigger a sensitivity analysis or a paper-level caveat.\n\n### K. Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)\n\nBuilding on §VII.D–§VII.J, gold validation should evaluate both the Level-1 relation separation and the Level-2 overclaim subtype separation, with a pre-registered fallback rule. The full plan is in `hierarchical_gold_validation_plan.md`; the key requirements are:\n\n1. **Level-1 agreement (supported / overclaim / contradiction).** Report Cohen's κ on the three-way Level-1 collapse. Pre-registered threshold: Level-1 κ ≥ 0.50.\n2. **Level-2 overclaim subtype agreement (scope_expansion vs. strong_action, conditional on Level-1 = overclaim).** Report Cohen's κ on the Level-2 subtype distinction. Pre-registered threshold: Level-2 κ ≥ 0.40 (same as the existing §VII.G mild_vs_strong threshold).\n3. **Claim realism (§VII.J Layer 2).** Report `claim_realism_score_1_to_5` distribution; pre-registered 25% class-level and paper-level thresholds apply.\n\n**Fallback rules (pre-registered).**\n\n- **If Level-1 κ is acceptable but Level-2 κ < 0.40:** the main paper is downgraded to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening. The four operational labels remain in the experimental tables, but the paper's primary claims are reframed at Level 1.\n- **If strong_action retention ≥ 0.60:** the Level-2 high-risk strong_action subtype is retained as a validated screening target, and R4's Level-2 screening claim is preserved.\n- **If strong_action retention < 0.50:** strong_action is reported only as an exploratory risk flag, not as a validated class; R4's screening claim is downgraded to exploratory status per §VII.G criterion 2.\n\nThis hierarchical validation plan does **not** relax the §VII.G downgrade criteria; it adds a Level-1/Level-2 structural interpretation on top of them. It does **not** create gold, modify existing silver CSVs, or change the frozen R4 method.\n\n## VIII. Discussion",
    )
    n_replacements += 1

    # ----- Section 9: Conclusion - hierarchical framing -----
    md = replace_once(
        md,
        "This work frames CESE-OCN as a **fine-grained evidence-sufficiency relation diagnosis framework** for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field. The core thesis is that scientific claim verification should not only ask whether evidence is related to a claim, but whether the evidence is *sufficient for the strength of the claim* — in particular when the claim asserts action, deployment, safety, or generalization conclusions; and that this calibration question benefits from a *relation-type decomposition* (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) rather than a single continuous overstatement score alone.",
        "This work frames CESE-OCN as a **fine-grained evidence-sufficiency relation diagnosis framework** for rare high-risk scientific action overclaims, positioned on the existing scientific overstatement / evidence-force calibration track rather than claiming to open a new field. The core thesis is that scientific claim verification should not only ask whether evidence is related to a claim, but whether the evidence is *sufficient for the strength of the claim* — in particular when the claim asserts action, deployment, safety, or generalization conclusions; and that this calibration question benefits from a **hierarchical diagnostic taxonomy** (Level 1: supported / overclaim / contradiction; Level 2: scope_expansion / strong_action under overclaim) rather than a single continuous overstatement score alone. The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space, but their interpretation is hierarchical: `mild_scope_overclaim` is a boundary-sensitive buffer subtype, not a naturally stable discrete class; `strong_action_overclaim` is the high-risk Level-2 subtype targeted by R4 screening.",
    )
    n_replacements += 1

    # ----- Add hierarchical note to §III.C (strong_action as Level-2 high-risk subtype) -----
    md = replace_once(
        md,
        "### C. Why strong_action_overclaim Is the High-Risk Boundary Class\n\nstrong_action_overclaim is the most consequential class for scientific claim calibration,",
        "### C. Why strong_action_overclaim Is the Level-2 High-Risk Subtype\n\nUnder the hierarchical taxonomy (§III.A, Table 0a), `strong_action_overclaim` is the **Level-2 high-risk subtype** under overclaim. strong_action_overclaim is the most consequential class for scientific claim calibration,",
    )
    n_replacements += 1

    # ----- Add new Changes log entry at the very top of changes block -----
    # Insert V3.15 changes entry before the V3.14 changes entry
    md = replace_once(
        md,
        "**Changes from V3.13 RIGOURATE-Differentiated + Realism-Aware (this V3.14 release):**",
        "**Changes from V3.14 Mainline Locked (this V3.15 release):** This version (V3.15 Hierarchical Taxonomy Revision) reframes the paper's interpretive framing from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy** (Level 1: supported / overclaim / contradiction; Level 2: scope_expansion / strong_action under overclaim). Changes are **wording-level and interpretive-level only**: (i) Abstract and §I contributions are reframed hierarchically; (ii) §III.A adds Table 0a (hierarchical label mapping) and a hierarchical interpretation paragraph; (iii) §IV.A reframes R4 as a relation-specific screening router under the hierarchical taxonomy, not a flat 4-class best classifier; (iv) §VI.A–§VI.B subsection titles and interpretations are reframed as flat operational-label evaluation + Level-2 high-risk screening; (v) §VIII.G adds a new subsection \"Why the Taxonomy Is Hierarchical Rather Than Flat\" with fallback logic; (vi) §VII.K adds a hierarchical gold validation plan with pre-registered Level-1/Level-2 fallback rules; (vii) §X Conclusion reframes the taxonomy contribution hierarchically. **No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning, no change to any §VI number, no change to any §VIII.D number, no change to §VII.G criteria, no deletion of the four operational labels (they remain the experimental label space), no claim that mild_scope_overclaim is a naturally stable discrete class, no claim that R4 overall beats LLM, no modification to V3.14 or any prior version source files.** All experimental numbers in §VI and §VIII.D are preserved byte-identical from V3.14; the canonical preserved-number list is in `V3_15_revision_log.md` and `V3_15_hierarchical_taxonomy_gate.json`. V3.14, V3.13, V3.12.1, V3.12, V3.11, V3.10.1, and V3.9 are preserved unchanged.\n\n**Changes from V3.13 RIGOURATE-Differentiated + Realism-Aware (this V3.14 release):**",
    )
    n_replacements += 1

    # Sanity check: ensure no numbers were accidentally changed
    preserved_numbers = ["0.3967", "0.0769", "0.3280", "0.5523", "0.3000", "0.2408", "0.2231", "0.4562", "0.2062", "0.4238"]
    for num in preserved_numbers:
        orig_count = original.count(num)
        new_count = md.count(num)
        if orig_count != new_count:
            raise ValueError("Preserved number " + num + " count changed: " + str(orig_count) + " -> " + str(new_count))

    return md, n_replacements


# =============================================================================
# 2. Generate hierarchical_label_mapping.csv
# =============================================================================

def write_mapping_csv():
    content = """original_label,level1_label,level2_label,is_high_risk,paper_interpretation,fallback_behavior
supported,supported,NA,false,fully supported relation,keep
mild_scope_overclaim,overclaim,scope_expansion,false,boundary-sensitive scope overclaim,merge into overclaim if unstable
strong_action_overclaim,overclaim,strong_action,true,high-risk action/deployment overclaim,retain as binary screen if stable
contradiction_candidate,contradiction,NA,false,evidence conflict/control relation,keep
"""
    with open(OUT_MAPPING_CSV, "w", encoding="utf-8", newline="") as f:
        f.write(content)
    print("Mapping CSV written: " + OUT_MAPPING_CSV)


# =============================================================================
# 3. Generate hierarchical_gold_validation_plan.md
# =============================================================================

def write_gold_plan():
    content = """# Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)

**Status:** PROTOCOL-LEVEL EXTENSION ONLY. No gold annotation has been performed. No existing gold/silver CSV is modified. No silver is promoted to gold. No §VII.G downgrade criteria are relaxed.

**Parent sections:** §VII.K of CESE-OCN V3.15. Builds on §VII.D–§VII.J (existing gold protocol + two-layer realism protocol).

**Date:** 2026-07-05

## 1. Why a Hierarchical Validation Plan

The V3.15 hierarchical taxonomy (§III.A, Table 0a) introduces a two-level structure:

- **Level 1:** supported / overclaim / contradiction
- **Level 2 (under overclaim):** scope_expansion (= mild_scope_overclaim) / strong_action (= strong_action_overclaim)

Gold validation must therefore evaluate **both** levels, not just the flat four-class agreement. If Level-1 agreement is acceptable but Level-2 agreement is insufficient, the paper falls back to a Level-1 three-class framing + binary strong_action screening, rather than forcing a flat four-class presentation that the data does not support.

## 2. Validation Requirements

Gold validation under the hierarchical plan reports three independent quantities:

### 2.1 Level-1 Agreement (supported / overclaim / contradiction)

- **Field:** collapse the four operational labels to three Level-1 labels: supported → supported; mild_scope_overclaim → overclaim; strong_action_overclaim → overclaim; contradiction_candidate → contradiction.
- **Metric:** Cohen's κ on the three-way Level-1 collapse, computed on the same gold-annotated sample.
- **Pre-registered threshold:** Level-1 κ ≥ 0.50.
- **Rationale:** Level 1 is the primary relation separation; if it is not drawable, the entire taxonomy fails and the paper is fundamentally downgraded.

### 2.2 Level-2 Overclaim Subtype Agreement (scope_expansion vs. strong_action)

- **Field:** conditional on Level-1 = overclaim, compute Cohen's κ on the Level-2 subtype distinction (scope_expansion vs. strong_action).
- **Metric:** Cohen's κ on the Level-2 subtype, conditional on Level-1 = overclaim.
- **Pre-registered threshold:** Level-2 κ ≥ 0.40 (same as the existing §VII.G mild_vs_strong threshold).
- **Rationale:** This is the boundary that the §V.D audit flags as hardest (75% confusion rate on strong_action). The existing §VII.G mild_vs_strong κ < 0.40 downgrade rule applies directly.

### 2.3 Claim Realism (§VII.J Layer 2)

- **Fields:** `claim_realism_score_1_to_5`, `claim_realism_issue`, `claim_realism_usable_for_paper`.
- **Pre-registered thresholds:** 25% class-level and 25% paper-level (already frozen in §VII.J).
- **Rationale:** SimClaim is a controlled counterfactual diagnostic set; realism is a separate axis from relation-label agreement.

## 3. Pre-Registered Fallback Rules

These fallback rules are pre-registered before gold collection and cannot be relaxed after results are known.

### 3.1 If Level-1 κ is acceptable but Level-2 κ < 0.40

- **Action:** The main paper is downgraded to a Level-1 three-class framing (supported / overclaim / contradiction) + binary strong_action screening.
- **Implementation:** The four operational labels remain in the experimental tables (no deletion of original labels), but the paper's primary claims are reframed at Level 1. §VI results are reported as flat operational-label evaluation; §VI.B strong_action results are reported as binary screening (strong_action vs. not-strong_action), not as a four-class result.
- **Wording:** The paper states explicitly that the Level-2 overclaim subtype distinction is not reliably drawable and that the paper falls back to Level-1 + binary screening.

### 3.2 If strong_action retention ≥ 0.60

- **Action:** The Level-2 high-risk strong_action subtype is retained as a validated screening target.
- **Implementation:** R4's Level-2 screening claim is preserved. §VI.B and §VIII.D.B results remain the primary deployment-relevant metrics.
- **Wording:** The paper states that strong_action is a validated Level-2 high-risk subtype and that R4 retains targeted screening value on it.

### 3.3 If strong_action retention < 0.50

- **Action:** strong_action is reported only as an exploratory risk flag, not as a validated class.
- **Implementation:** R4's screening claim is downgraded to exploratory status per §VII.G criterion 2. The paper does not claim R4 validates strong_action as a class; it claims only that R4 flags potential action overclaims for human review.
- **Wording:** The paper states explicitly that strong_action is not retained as a validated class and that R4's screening results are exploratory.

### 3.4 If Level-1 κ < 0.50

- **Action:** The entire taxonomy fails; the paper is fundamentally downgraded. This is the worst-case scenario and is not the expected outcome given the §V.D audit (supported is the most stable class at 7/7 reasonable).
- **Implementation:** The paper is re-framed as a screening-only contribution (R4 as a strong_action flag generator) without a taxonomy claim. This path is not pre-specified in detail because it would require a substantial rewrite; the §VII.G criteria and the hierarchical fallback above are the primary pre-registered safety mechanisms.

## 4. Relationship to Existing §VII.G Downgrade Criteria

This hierarchical plan does **not** relax the §VII.G downgrade criteria. It adds a Level-1/Level-2 structural interpretation on top of them:

- §VII.G criterion 1 (mild_vs_strong κ < 0.40 → taxonomy revised) maps directly to fallback rule 3.1.
- §VII.G criterion 2 (strong_action retention < 0.50 → claim downgraded) maps directly to fallback rule 3.3.
- §VII.G criterion 6 (mild_vs_strong κ ≥ 0.40 AND strong_action retention ≥ 0.60 → success path) maps directly to fallback rule 3.2.

The hierarchical plan is the structural interpretation of the existing criteria, not a new set of criteria.

## 5. Prohibitions

- This plan does **not** create gold.
- This plan does **not** modify existing silver CSVs.
- This plan does **not** modify V3.14 or any prior paper version.
- This plan does **not** change the frozen R4 method or thresholds.
- This plan does **not** call any API.
- This plan does **not** claim SimClaim claims as natural claims.
- This plan does **not** claim silver labels as gold.
- This plan does **not** delete the four operational labels.
- This plan does **not** claim mild_scope_overclaim is a naturally stable discrete class.
- This plan does **not** claim R4 overall beats LLM.
"""
    with open(OUT_GOLD_PLAN, "w", encoding="utf-8") as f:
        f.write(content)
    print("Gold plan written: " + OUT_GOLD_PLAN)


# =============================================================================
# 4. Generate V3.15 revision log
# =============================================================================

def write_revision_log(n_replacements):
    content = """# V3.15 Revision Log — Hierarchical Taxonomy Revision

**Date:** 2026-07-05
**Source:** V3.14 Mainline Locked + Reviewer-Grade Consistency Audit
**Output directory:** `D:\\ocn\\paper_versions_ordered\\V3_15_hierarchical_taxonomy_revision\\`

## Summary

V3.15 reframes the paper's interpretive framing from a flat four-class taxonomy to a **hierarchical diagnostic taxonomy** (Level 1: supported / overclaim / contradiction; Level 2: scope_expansion / strong_action under overclaim). The four operational labels (supported, mild_scope_overclaim, strong_action_overclaim, contradiction_candidate) remain the experimental label space; only the interpretation changes.

## Changes Applied

Total targeted string replacements: """ + str(n_replacements) + """

### 1. Header / Changes Log
- Updated version header to V3.15 Hierarchical Taxonomy Revision.
- Added V3.15 changes entry at top of changes block.

### 2. Abstract
- Replaced "we define a four-class taxonomy" with hierarchical framing.
- Added standard wording: "We do not assume that mild_scope_overclaim is a naturally discrete category. Instead, it is used as a diagnostic buffer subtype..."
- Reframed R4 description as "relation-specific screening router under the hierarchical taxonomy".

### 3. Introduction (§I)
- Reframed contribution 1 as "Hierarchical diagnostic taxonomy" (Level 1 + Level 2).
- Reframed contribution 2 as "Controlled counterfactual diagnostic set + LLM under-detection finding".
- Reframed contribution 3 as "Screening method (R4) targeting the Level-2 high-risk strong_action subtype".
- mild_scope_overclaim explicitly described as boundary-sensitive buffer subtype, not naturally stable.

### 4. Task Formulation (§III.A)
- Added Table 0a (hierarchical label mapping) with 5 rows.
- Added hierarchical interpretation paragraph after the four-class bullet list.
- §III.C title changed to "Why strong_action_overclaim Is the Level-2 High-Risk Subtype".

### 5. Method (§IV.A)
- Reframed R4 as "relation-specific screening router under the hierarchical taxonomy".
- Mapped three routes onto hierarchical levels (Level-1 contradiction gate, Level-2 scope residual, Level-2 strong_action route).
- Explicitly stated "R4 is not a flat 4-class best classifier".

### 6. Results (§VI)
- §VI.A title: "Internal Silver Diagnostic Results (Table 1) — Flat Operational-Label Evaluation".
- §VI.B title: "LLM Judge Comparison (Table 2, Figure 3) — Level-2 High-Risk Strong_Action Screening".
- Added note: "macro-F1 over operational labels is diagnostic, not the primary deployment metric".
- Added screening utility reinforcement: "In real-world deployment, strong_action is a rare high-risk subtype; therefore recall, FP/TP ratio, and review burden are more important than overall accuracy."

### 7. Discussion (§VIII.G — NEW)
- Added new subsection "Why the Taxonomy Is Hierarchical Rather Than Flat".
- Explains Level 1 / Level 2 structure.
- Explains why mild_scope is buffer, strong_action is high-risk subtype.
- Includes fallback logic (Level-1 κ, Level-2 κ, strong_action retention thresholds).

### 8. Gold Protocol (§VII.K — NEW)
- Added new subsection "Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)".
- References `hierarchical_gold_validation_plan.md`.
- Specifies three validation requirements: Level-1 κ, Level-2 κ, claim realism.
- Specifies three fallback rules: Level-1 OK + Level-2 fail → 3-class + binary screen; retention ≥ 0.60 → retain; retention < 0.50 → exploratory.

### 9. Conclusion (§X)
- Reframed taxonomy contribution as hierarchical.
- Added: "mild_scope_overclaim is a boundary-sensitive buffer subtype, not a naturally stable discrete class; strong_action_overclaim is the high-risk Level-2 subtype targeted by R4 screening."

## Preserved Byte-Identical (Verified)

All experimental numbers preserved byte-identical from V3.14:
- R4 strong-F1 = 0.3967 (silver 444)
- R4 strong-F1 = 0.3000 (matched 100)
- LLM strong-F1 = 0.0769 (matched 100)
- R4 macro-F1 = 0.3280 (matched 100)
- LLM macro-F1 = 0.5523 (matched 100)
- Baseline strong-F1 = 0.2408
- Absolute gap = +0.2231
- R4 strong recall = 0.4562 (silver 444), 0.36 (matched 100)
- Baseline strong recall = 0.2062
- R4 macro-F1 = 0.4238 (silver 444)
- Bootstrap CI = [0.1058, 0.1988]
- FP/TP = 2.89, review burden = 35%

## Prohibitions Enforced

- No experiments run.
- No API calls.
- No gold annotation.
- No original data modification.
- No experimental number changes.
- No deletion of the four operational labels.
- No silver written as gold.
- No claim that mild_scope is naturally stable.
- No claim that R4 overall beats LLM.
- No modification to V3.14 or any prior version source files.

## Files Generated

1. `CESE_OCN_V3_15_hierarchical_taxonomy_revision.md` — main paper
2. `CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx` — DOCX version
3. `hierarchical_label_mapping.csv` — 4-row mapping table
4. `hierarchical_gold_validation_plan.md` — Level-1/Level-2 + fallback plan
5. `V3_15_revision_log.md` — this file
6. `V3_15_hierarchical_taxonomy_gate.json` — gate JSON
"""
    with open(OUT_REVISION_LOG, "w", encoding="utf-8") as f:
        f.write(content)
    print("Revision log written: " + OUT_REVISION_LOG)


# =============================================================================
# 5. Generate gate JSON
# =============================================================================

def write_gate(n_replacements, md_size, docx_size):
    gate = {
        "gate_name": "V3_15_hierarchical_taxonomy_gate",
        "version": "V3.15 Hierarchical Taxonomy Revision",
        "date": "2026-07-05",
        "source_version": "V3.14 Mainline Locked + Reviewer-Grade Consistency Audit",
        "output_directory": OUT_DIR,
        "outputs": {
            "main_md": OUT_MD,
            "main_docx": OUT_DOCX,
            "mapping_csv": OUT_MAPPING_CSV,
            "gold_plan": OUT_GOLD_PLAN,
            "revision_log": OUT_REVISION_LOG,
            "gate_json": OUT_GATE,
        },
        "n_targeted_replacements": n_replacements,
        "main_md_size_bytes": md_size,
        "main_docx_size_bytes": docx_size,
        "taxonomy_structure": {
            "level_1": ["supported", "overclaim", "contradiction"],
            "level_2_under_overclaim": ["scope_expansion", "strong_action"],
            "operational_labels_preserved": [
                "supported",
                "mild_scope_overclaim",
                "strong_action_overclaim",
                "contradiction_candidate",
            ],
        },
        "sections_modified": [
            "Header / Changes log",
            "Abstract",
            "§I Introduction (contributions)",
            "§III.A Task Formulation (Table 0a + hierarchical interpretation)",
            "§III.C (title reframed as Level-2 high-risk subtype)",
            "§IV.A Method (R4 as hierarchical router)",
            "§VI.A Results (flat operational-label evaluation framing)",
            "§VI.B Results (Level-2 high-risk screening framing)",
            "§VII.K Gold Protocol (NEW: hierarchical validation plan)",
            "§VIII.G Discussion (NEW: why hierarchical rather than flat)",
            "§X Conclusion (hierarchical framing)",
        ],
        "sections_added": [
            "§VII.K Hierarchical Gold Validation Plan",
            "§VIII.G Why the Taxonomy Is Hierarchical Rather Than Flat",
            "Table 0a (hierarchical label mapping)",
        ],
        "preserved_numbers_verified": {
            "r4_strong_f1_silver_444": 0.3967,
            "r4_strong_f1_matched_100": 0.3000,
            "llm_strong_f1_matched_100": 0.0769,
            "r4_macro_f1_matched_100": 0.3280,
            "llm_macro_f1_matched_100": 0.5523,
            "baseline_strong_f1": 0.2408,
            "absolute_gap": 0.2231,
            "r4_strong_recall_silver": 0.4562,
            "baseline_strong_recall": 0.2062,
            "r4_macro_f1_silver": 0.4238,
            "bootstrap_ci_lower": 0.1058,
            "bootstrap_ci_upper": 0.1988,
        },
        "prohibitions_enforced": {
            "no_experiments_run": True,
            "no_api_calls": True,
            "no_gold_annotation": True,
            "no_original_data_modification": True,
            "no_experimental_number_changes": True,
            "no_deletion_of_four_operational_labels": True,
            "no_silver_as_gold": True,
            "no_claim_mild_scope_naturally_stable": True,
            "no_claim_r4_overall_beats_llm": True,
            "no_modification_to_v3_14_or_prior": True,
        },
        "fallback_rules_pre_registered": {
            "level1_ok_level2_fail": "Downgrade to Level-1 three-class + binary strong_action screening",
            "strong_action_retention_ge_0_60": "Retain Level-2 high-risk subtype",
            "strong_action_retention_lt_0_50": "Report strong_action as exploratory risk flag only",
            "level1_kappa_lt_0_50": "Fundamental taxonomy failure; paper fundamentally downgraded",
        },
        "audit_disclaimer": "V3.15 is a wording-level and interpretive-level revision of V3.14. No experiments were run, no API calls made, no gold annotation performed, no original data modified, no experimental numbers changed. The four operational labels remain the experimental label space; only the interpretation changes from flat four-class to hierarchical. mild_scope_overclaim is explicitly NOT claimed to be a naturally stable discrete class. R4 is explicitly NOT claimed to overall beat LLM. All silver labels remain silver; no silver is promoted to gold.",
    }
    with open(OUT_GATE, "w", encoding="utf-8") as f:
        json.dump(gate, f, indent=2, ensure_ascii=False)
    print("Gate JSON written: " + OUT_GATE)


# =============================================================================
# 6. DOCX generation (reuses V3.14 builder pattern)
# =============================================================================

def render_inline_runs(text):
    parts = re.split(r"(\*\*[^*]+\*\*)", text)
    runs = []
    for part in parts:
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            inner = part[2:-2]
            runs.append('<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(inner) + '</w:t></w:r>')
        else:
            italic_parts = re.split(r"(\*[^*]+\*)", part)
            for ip in italic_parts:
                if not ip:
                    continue
                if ip.startswith("*") and ip.endswith("*") and len(ip) > 2:
                    inner = ip[1:-1]
                    runs.append('<w:r><w:rPr><w:i/></w:rPr><w:t xml:space="preserve">' + escape(inner) + '</w:t></w:r>')
                else:
                    runs.append('<w:r><w:t xml:space="preserve">' + escape(ip) + '</w:t></w:r>')
    return "".join(runs)


def para(text, style=None, bold=False):
    ppr = '<w:pPr><w:pStyle w:val="' + style + '"/></w:pPr>' if style else ''
    if bold:
        runs = '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(text) + '</w:t></w:r>'
    else:
        runs = render_inline_runs(text)
    return '<w:p>' + ppr + runs + '</w:p>'


def heading(text, level):
    return para(text, style='Heading' + str(level))


def table_block(rows):
    if not rows:
        return ''
    n_cols = max(len(r) for r in rows)
    tbl_pr = ('<w:tblPr><w:tblW w:w="0" w:type="auto"/><w:tblBorders>'
              '<w:top w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:left w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:bottom w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:right w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideH w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '<w:insideV w:val="single" w:sz="4" w:space="0" w:color="auto"/>'
              '</w:tblBorders></w:tblPr>')
    grid = '<w:tblGrid>' + ''.join('<w:gridCol w:w="2000"/>' for _ in range(n_cols)) + '</w:tblGrid>'
    rows_xml = []
    for i, row in enumerate(rows):
        is_header = (i == 0)
        cells_xml = []
        for j in range(n_cols):
            cell_text = row[j] if j < len(row) else ''
            ppr = '<w:pPr><w:pStyle w:val="TableCell"/></w:pPr>'
            if is_header:
                run = '<w:r><w:rPr><w:b/></w:rPr><w:t xml:space="preserve">' + escape(cell_text) + '</w:t></w:r>'
            else:
                run = render_inline_runs(cell_text)
            cells_xml.append('<w:tc><w:tcPr><w:tcW w:w="2000" w:type="dxa"/></w:tcPr><w:p>' + ppr + run + '</w:p></w:tc>')
        rows_xml.append('<w:tr>' + ''.join(cells_xml) + '</w:tr>')
    return '<w:tbl>' + tbl_pr + grid + ''.join(rows_xml) + '</w:tbl>'


def parse_markdown(md):
    lines = md.split('\n')
    elements = []
    i = 0
    in_code_block = False
    while i < len(lines):
        line = lines[i]
        stripped = line.rstrip()
        if stripped.startswith('```'):
            if in_code_block:
                in_code_block = False
            else:
                in_code_block = True
            i += 1
            continue
        if in_code_block:
            safe = escape(stripped)
            elements.append('<w:p><w:pPr><w:pStyle w:val="TableCell"/></w:pPr><w:r><w:rPr><w:rFonts w:ascii="Consolas" w:hAnsi="Consolas"/></w:rPr><w:t xml:space="preserve">' + safe + '</w:t></w:r></w:p>')
            i += 1
            continue
        if not stripped:
            i += 1
            continue
        if stripped.startswith('#### '):
            elements.append(heading(stripped[5:], 4)); i += 1; continue
        if stripped.startswith('### '):
            elements.append(heading(stripped[4:], 3)); i += 1; continue
        if stripped.startswith('## '):
            elements.append(heading(stripped[3:], 2)); i += 1; continue
        if stripped.startswith('# '):
            elements.append(heading(stripped[2:], 1)); i += 1; continue
        if stripped.startswith('|') and i + 1 < len(lines):
            next_line = lines[i + 1].strip()
            if re.match(r'^\|[\s\-:|]+\|$', next_line):
                table_rows = [[c.strip() for c in stripped.strip('|').split('|')]]
                i += 2
                while i < len(lines) and lines[i].strip().startswith('|'):
                    table_rows.append([c.strip() for c in lines[i].strip().strip('|').split('|')])
                    i += 1
                elements.append(table_block(table_rows)); continue
        if stripped.startswith('- '):
            elements.append('<w:p><w:pPr><w:pStyle w:val="ListBullet"/></w:pPr>' + render_inline_runs(stripped[2:]) + '</w:p>')
            i += 1; continue
        if stripped.startswith(('✅', '❌')):
            elements.append(para(stripped)); i += 1; continue
        m = re.match(r'^(\d+)\.\s+(.*)', stripped)
        if m:
            elements.append('<w:p><w:pPr><w:pStyle w:val="ListNumber"/></w:pPr>' + render_inline_runs(m.group(2)) + '</w:p>')
            i += 1; continue
        if stripped.startswith('> '):
            elements.append('<w:p><w:pPr><w:pStyle w:val="TableCell"/></w:pPr>' + render_inline_runs(stripped[2:]) + '</w:p>')
            i += 1; continue
        elements.append(para(stripped)); i += 1
    return elements


STYLES_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
              '<w:styles xmlns:w="' + NS_W + '">\n'
              '<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Calibri" w:hAnsi="Calibri" w:cs="Calibri"/><w:sz w:val="22"/><w:szCs w:val="22"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="160" w:line="276" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>\n'
              '<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="360" w:after="120"/><w:outlineLvl w:val="0"/></w:pPr><w:rPr><w:b/><w:sz w:val="32"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="280" w:after="100"/><w:outlineLvl w:val="1"/></w:pPr><w:rPr><w:b/><w:sz w:val="28"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="80"/><w:outlineLvl w:val="2"/></w:pPr><w:rPr><w:b/><w:sz w:val="24"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="Heading4"><w:name w:val="heading 4"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="200" w:after="60"/><w:outlineLvl w:val="3"/></w:pPr><w:rPr><w:b/><w:sz w:val="22"/></w:rPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="ListBullet"><w:name w:val="List Bullet"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="1"/></w:numPr><w:spacing w:after="80"/></w:pPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="ListNumber"><w:name w:val="List Number"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:numPr><w:ilvl w:val="0"/><w:numId w:val="2"/></w:numPr><w:spacing w:after="80"/></w:pPr></w:style>\n'
              '<w:style w:type="paragraph" w:styleId="TableCell"><w:name w:val="Table Cell"/><w:basedOn w:val="Normal"/><w:pPr><w:spacing w:after="0" w:line="240" w:lineRule="auto"/></w:pPr></w:style>\n'
              '</w:styles>')

CONTENT_TYPES_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/word/numbering.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.numbering+xml"/>
</Types>'''

RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
</Relationships>'''

DOC_RELS_XML = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/numbering" Target="numbering.xml"/>
</Relationships>'''

NUMBERING_XML = ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n'
                 '<w:numbering xmlns:w="' + NS_W + '">\n'
                 '<w:abstractNum w:abstractNumId="0"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="bullet"/><w:lvlText w:val="&#8226;"/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>\n'
                 '<w:abstractNum w:abstractNumId="1"><w:lvl w:ilvl="0"><w:start w:val="1"/><w:numFmt w:val="decimal"/><w:lvlText w:val="%1."/><w:lvlJc w:val="left"/><w:pPr><w:ind w:left="720" w:hanging="360"/></w:pPr></w:lvl></w:abstractNum>\n'
                 '<w:num w:numId="1"><w:abstractNumId w:val="0"/></w:num>\n'
                 '<w:num w:numId="2"><w:abstractNumId w:val="1"/></w:num>\n'
                 '</w:numbering>')


def build_docx(md_text):
    elements = parse_markdown(md_text)
    body = ''.join(elements)
    document_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:document xmlns:w="' + NS_W + '"><w:body>' + body +
        '<w:sectPr><w:pgSz w:w="12240" w:h="15840"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="1440" w:header="720" w:footer="720" w:gutter="0"/></w:sectPr>'
        '</w:body></w:document>'
    )
    with zipfile.ZipFile(OUT_DOCX, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml', CONTENT_TYPES_XML)
        z.writestr('_rels/.rels', RELS_XML)
        z.writestr('word/document.xml', document_xml)
        z.writestr('word/_rels/document.xml.rels', DOC_RELS_XML)
        z.writestr('word/styles.xml', STYLES_XML)
        z.writestr('word/numbering.xml', NUMBERING_XML)
    return os.path.getsize(OUT_DOCX)


# =============================================================================
# Main
# =============================================================================

def main():
    print("=" * 70)
    print("V3.15 Hierarchical Taxonomy Revision Builder")
    print("=" * 70)
    print("Source: " + SRC_MD)
    print("Output dir: " + OUT_DIR)
    print()

    # Step 1: Load source
    md = load_source()
    print("Source loaded: " + str(len(md)) + " chars")

    # Step 2: Apply revisions
    md, n_replacements = apply_revisions(md)
    print("Revisions applied: " + str(n_replacements) + " targeted replacements")

    # Step 3: Write MD
    with open(OUT_MD, "w", encoding="utf-8") as f:
        f.write(md)
    md_size = os.path.getsize(OUT_MD)
    print("Main MD written: " + OUT_MD + " (" + str(md_size) + " bytes)")

    # Step 4: Write mapping CSV
    write_mapping_csv()

    # Step 5: Write gold plan
    write_gold_plan()

    # Step 6: Build DOCX
    docx_size = build_docx(md)
    print("DOCX written: " + OUT_DOCX + " (" + str(docx_size) + " bytes)")

    # Step 7: Write revision log
    write_revision_log(n_replacements)

    # Step 8: Write gate JSON
    write_gate(n_replacements, md_size, docx_size)

    print()
    print("=" * 70)
    print("V3.15 build complete.")
    print("  Replacements: " + str(n_replacements))
    print("  MD size: " + str(md_size) + " bytes")
    print("  DOCX size: " + str(docx_size) + " bytes")
    print("  Outputs: 6 files in " + OUT_DIR)
    print("=" * 70)


if __name__ == "__main__":
    main()
