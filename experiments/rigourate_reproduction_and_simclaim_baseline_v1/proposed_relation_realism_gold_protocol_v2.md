# Proposed Relation + Realism Gold Protocol V2

**Task:** RIGOURATE Reproduction + SimClaim Differentiation v1 - Section 9
**Date:** 2026-07-05
**Status:** PROPOSAL ONLY. Does NOT modify existing gold CSV. Does NOT create gold. Does NOT modify V3.12 or original data.

## 1. Purpose

This document proposes a two-layer gold annotation protocol for SimClaim, extending the existing relation-label-only gold plan with an independent claim-realism layer. The proposal is motivated by:

1. **Section 8 finding:** 21/444 (4.7%) of SimClaim silver claims have heuristic realism risk flags, with the strong_action_overclaim category at 9.0% - non-trivial enough to require explicit realism annotation.
2. **V3.13 `proposed_gold_realism_extension.md`:** Already specifies `claim_realism_score_1_to_5` and `claim_realism_issue` fields; this document operationalises those fields in a full two-layer protocol.
3. **Reviewer risk:** Reviewers may question whether SimClaim's controlled counterfactual claims are naturalistic enough to support paper conclusions. A two-layer protocol with explicit realism scores provides a falsifiable answer.

## 2. Scope

This protocol applies to the **gold adjudication stage** only. It does NOT change:
- The silver labels (already frozen).
- The frozen R4 method or thresholds.
- The V3.12 paper text.
- The four-class taxonomy boundary rules.
- The pre-registered success/downgrade criteria in §VII of the paper.

## 3. Layer 1: Relation label (unchanged from V3.12 §VII)

**Field:** `gold_relation_label`
**Values:**
- `supported` — the evidence supports the claim as stated, including its strength.
- `mild_scope_overclaim` — the claim mildly over-extends the scope of the evidence, without asserting an action/deployment/safety conclusion.
- `strong_action_overclaim` — the claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify.
- `contradiction_candidate` — the evidence contradicts the claim.

**Annotation procedure:** Two-annotator independent review followed by adjudication for gold standard, per the existing V3.12 §VII protocol. Boundary rules from the V3.12 taxonomy apply.

**Quality control:**
- Inter-annotator agreement (Cohen's kappa or Krippendorff's alpha) reported per class.
- Adjudication disagreements recorded with reasons.
- All gold labels stored separately from silver; silver labels are not visible to gold annotators.

## 4. Layer 2: Claim realism (NEW)

This is the new layer proposed by this document and by `proposed_gold_realism_extension.md`.

### 4.1 Field: `claim_realism_score_1_to_5`

**Values:** Integer 1-5.
- **1** — Clearly unrealistic. The claim would never appear in a real scientific paper. Examples: extreme superlatives without context, mechanical negation insertions, placeholder phrases.
- **2** — Mostly unrealistic. The claim has noticeable unnatural wording but is recognisable as a scientific claim.
- **3** — Borderline. The claim is plausible but has subtle unnatural cues (e.g., overly template-like opening, slightly forced action cues).
- **4** — Mostly natural. The claim reads naturally with minor quirks.
- **5** — Clearly plausible. The claim is indistinguishable from a real author-written scientific claim.

**Annotation guidance:**
- Annotators rate realism INDEPENDENTLY of the relation label. A claim can be `supported` and `realism_score=1` (unnatural but accurate) or `strong_action_overclaim` and `realism_score=5` (natural but overstated).
- Annotators should compare the claim to the kind of claims that appear in real ICLR/NeurIPS/ACL papers in the same domain.
- Realism is about *whether a real author could write this claim*, not about *whether the claim is correct*.

### 4.2 Field: `claim_realism_issue`

**Values:** Single-select from:
- `none` — no realism issue detected.
- `too_template_like` — generic opening ("The benchmark demonstrates..."), boilerplate phrasing.
- `too_extreme` — excessive superlatives, absolute claims.
- `unnatural_wording` — generic placeholder phrases, low claim-evidence vocabulary overlap.
- `not_scientific_claim` — too informal, too short, or non-scientific vocabulary.
- `contradiction_too_mechanical` — negation appears mechanically inserted to create a contradiction variant.
- `strong_action_too_forced` — action/deployment/safety cues appear appended rather than integrated.
- `mild_strong_boundary_unclear` — claim is too short or generic to clearly distinguish mild from strong.
- `ambiguous_or_vague` — claim is too vague to anchor a clear relation judgment.

**Annotation guidance:**
- Select the *primary* realism issue. If multiple issues are present, annotators record the most salient one in this field and describe others in a free-text notes field (see §4.4).
- `none` should be selected only if no realism issue is detected.

### 4.3 Field: `claim_realism_usable_for_paper`

**Values:** `yes` / `no`
- **yes** — the claim can be used in paper-valid tables and analyses (realism_score >= 3 AND no critical realism issue).
- **no** — the claim should be excluded from paper-valid tables and reported only in diagnostic/sensitivity analyses (realism_score < 3 OR a critical realism issue such as `not_scientific_claim` or `contradiction_too_mechanical`).

**Annotation guidance:**
- This is a derived field, not an independent judgment. It is computed from `claim_realism_score_1_to_5` and `claim_realism_issue` after annotation.
- Annotators do NOT set this field directly; it is computed by the analysis pipeline.

### 4.4 Field: `claim_realism_notes` (free text, optional)

Annotators may record additional observations about the claim's realism, including secondary issues, comparison to real paper claims, or domain-specific concerns.

## 5. Pre-registered realism thresholds

From `proposed_gold_realism_extension.md` (V3.13):

- **Class-level threshold:** If more than 25% of claims in any silver-label class have `claim_realism_score_1_to_5 <= 2`, that class is flagged for paper-validity review.
- **Paper-level threshold:** If more than 25% of all gold-annotated claims have `claim_realism_score_1_to_5 <= 2`, the paper's main tables must be reported with a realism caveat, and a sensitivity analysis excluding low-realism claims must be added.

These thresholds are pre-registered before gold collection and cannot be relaxed after results are known.

## 6. Annotation workflow

1. **Sampling:** All 444 silver pairs are candidates for gold annotation. Priority sampling: all 111 strong_action_overclaim cases first (highest realism risk per §8), then a stratified sample of the other three classes.
2. **Annotators:** Two independent annotators per claim, both with domain expertise in ML/NLP. A third adjudicator resolves disagreements.
3. **Blinding:** Annotators see (claim_text, evidence_text, domain) only. They do NOT see silver labels, R4 predictions, LLM predictions, or group structure.
4. **Order:** Layer 1 (relation label) and Layer 2 (realism) are annotated in separate passes to avoid anchoring. The order is randomised per annotator.
5. **Adjudication:** Disagreements in either layer are adjudicated by the third annotator. Adjudication reasons are recorded.
6. **Storage:** Gold annotations are stored in a separate CSV from silver. The silver CSV is NOT modified.

## 7. Quality control

- **Inter-annotator agreement:** Cohen's kappa for relation label (Layer 1) and for `claim_realism_usable_for_paper` (Layer 2 binary). Krippendorff's alpha for `claim_realism_score_1_to_5` (Layer 2 ordinal).
- **Adjudication rate:** Reported per class and per realism issue type.
- **Realism distribution:** Histogram of `claim_realism_score_1_to_5` per silver-label class, reported in the paper appendix.
- **Sensitivity analysis:** Main paper tables re-computed with `claim_realism_usable_for_paper = yes` filter; differences reported.

## 8. Implications for paper

- **V3.12 paper text is NOT modified** by this proposal. The protocol is specified for future gold collection.
- When gold is collected under this protocol, the paper will report:
  - Gold relation-label results in Tables G1-G3 (already pre-registered in V3.12 §VII).
  - Gold realism distribution in a new appendix table.
  - Sensitivity analysis excluding low-realism claims.
- If realism thresholds are breached, the paper will add a realism caveat to the main tables and report sensitivity results.
- If realism thresholds are NOT breached, the paper will state that SimClaim claims pass the pre-registered realism check and proceed with the main tables as-is.

## 9. Relationship to RIGOURATE realism considerations

RIGOURATE uses natural author-written claims from ICLR/NeurIPS abstracts and introductions, so realism is not a concern for RIGOURATE. SimClaim uses generated counterfactual claim variants, so realism IS a concern. This protocol is the falsifiable mechanism that addresses the realism risk: if SimClaim claims are systematically unnatural, the protocol will detect it and trigger a sensitivity analysis or a paper-level caveat.

## 10. Prohibitions

- This proposal does NOT create gold.
- This proposal does NOT modify existing silver CSVs.
- This proposal does NOT modify V3.12 paper text.
- This proposal does NOT change the frozen R4 method or thresholds.
- This proposal does NOT call any API.
- This proposal does NOT claim SimClaim claims as natural claims.
- This proposal does NOT claim silver labels as gold.

## 11. File references

- V3.13 extension spec: `D:\ocn\paper_versions_ordered\V3_13_differentiated_against_rigourate_forcebench\proposed_gold_realism_extension.md`
- Section 8 audit: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\claim_realism_audit_summary.md`
- Section 8 queue: `D:\ocn\experiments\rigourate_reproduction_and_simclaim_baseline_v1\claim_realism_audit_queue.csv`
- V3.12 §VII gold protocol: `D:\ocn\paper_versions_ordered\V3_12_with_three_credibility_checks\CESE_OCN_V3_12_with_three_credibility_checks.md`
