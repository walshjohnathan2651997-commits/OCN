# Proposed Gold-Realism Audit Extension (V3.13)

**Purpose.** This file specifies the proposed `claim_realism_score_1_to_5` and `claim_realism_issue` fields for the gold pilot, referenced from §VII.I of the V3.13 paper. It is a **protocol-level proposal**, not a populated data file. No existing gold-pilot CSV is modified in V3.13.

**Why this audit is needed.** SimClaim is a controlled counterfactual diagnostic set (§V.A): evidence spans come from real scientific papers, but claim variants are generated to instantiate specific evidence-sufficiency relations. Two annotators may agree on a relation label for a claim that is nonetheless too template-like, too extreme, or unnaturally worded to stand as a plausible scientific claim. If a substantial fraction of `strong_action_overclaim` cases are flagged as unrealistic, the silver-stage screening finding (R4 > LLM on strong_action) may hold on the diagnostic set but fail to transfer to natural scientific writing — a scope-limiting risk that the §VII.G downgrade criteria alone do not cover.

## Fields to Add (per claim, alongside the relation label)

### Field 1: `claim_realism_score_1_to_5`

- **Type:** integer, 1 to 5
- **Definition:** How plausible is this claim as a piece of real scientific writing?
  - **5** — clearly a plausible scientific claim a researcher might write
  - **4** — mostly plausible, minor wording awkwardness
  - **3** — borderline plausible, but with noticeable template-like or extreme phrasing
  - **2** — largely implausible as a real scientific claim
  - **1** — clearly unrealistic / not a scientific claim
- **Annotator instruction:** Score the *realism* of the claim text itself, NOT whether the relation label is correct. A claim can have a unanimous relation label and still receive a low realism score.

### Field 2: `claim_realism_issue`

- **Type:** single categorical tag (string)
- **Allowed values:**
  - `none` — no realism issue detected
  - `too_template_like` — the claim follows an obvious template / formulaic structure that real scientific writing would rarely use
  - `too_extreme` — the claim is too strong / extreme in a way real scientific writing would rarely use (e.g., "proves", "guarantees", "fully solves")
  - `unnatural_wording` — the claim is grammatically or stylistically awkward in a way real scientific writing would rarely use
  - `not_scientific_claim` — the claim does not read as a scientific claim at all (e.g., reads as a marketing slogan, a tweet, or a non-scientific statement)
  - `ambiguous_or_vague` — the claim is too vague or ambiguous to evaluate for realism
- **Annotator instruction:** Pick exactly one tag. If multiple apply, pick the most salient. If no issue, use `none`.

## Annotator Protocol

1. **Independent annotation.** Each annotator (A and B) independently assigns `claim_realism_score_1_to_5` and `claim_realism_issue` for **every claim** in the gold pilot (not just disputed cases).
2. **Blind to model predictions.** Annotators are blind to R4 and LLM predictions, and blind to the silver label, exactly as in the existing relation-label annotation protocol.
3. **Adjudication.** After both annotators complete the realism fields:
   - `claim_realism_score_1_to_5` (final): if the two annotators disagree by ≤ 1 point, take the mean (rounded to nearest integer); if they disagree by ≥ 2 points, the adjudicator assigns the final score.
   - `claim_realism_issue` (final): if the two annotators agree, use that tag; if they disagree, the adjudicator picks one (or `none` if both are unreasonable).
4. **No modification of relation labels.** The realism audit does NOT change the relation label (`supported` / `mild_scope_overclaim` / `strong_action_overclaim` / `contradiction_candidate`). A claim may have a unanimous relation label AND a low realism score; both are reported.

## Pre-Registered Realism Reporting Thresholds

These thresholds are **pre-registered** in V3.13 and will be applied to the gold pilot results when available.

- **Low-realism flag (per claim):** `claim_realism_score_1_to_5 ≤ 2` OR `claim_realism_issue ≠ none`.

- **Class-level realism check (per class):** If > 25% of claims in any class (especially `strong_action_overclaim`) receive a low-realism flag:
  - The paper adds an explicit "realism caveat" to the corresponding §VI result for that class.
  - The §VIII.D.B screening-utility claim for `strong_action_overclaim` adds an explicit qualifier: "the screening finding holds on the diagnostic set; realism audit flagged X% of strong_action_overclaim cases as low-realism, so natural-claim transferability is not established."

- **Paper-level realism check (overall):** If > 25% of all gold-pilot claims receive a low-realism flag:
  - The paper's main claims are downgraded from "controlled silver-stage evidence on a diagnostic set" to "controlled silver-stage evidence on a synthetic diagnostic set with limited natural-claim transferability."
  - An additional §IX Limitations item is added stating the paper-level realism limitation explicitly.
  - The Abstract adds: "SimClaim is a controlled counterfactual diagnostic set; gold-realism audit flagged X% of claims as low-realism, so the screening finding is bounded to the diagnostic setting."

- **Per-class realism distribution table:** The gold pilot will report, for each of the four classes:
  - mean `claim_realism_score_1_to_5`
  - % of claims with `claim_realism_score_1_to_5 ≤ 2`
  - % of claims with `claim_realism_issue ≠ none`
  - distribution of `claim_realism_issue` tags (excluding `none`)

## What This Audit Does NOT Do

- **Does not replace the §VII.G downgrade criteria.** The realism audit is an *additional* check, not a substitute for the relation-label agreement checks (Cohen's κ, retention rate, etc.) in §VII.G.
- **Does not modify existing gold-pilot CSVs in V3.13.** The realism fields will be added as new columns when the gold pilot is actually run. The existing `pilot_50_blind_annotation_A.csv`, `pilot_50_blind_annotation_B.csv`, and `adjudication_template.csv` are unchanged in V3.13.
- **Does not change any §VI or §VIII.D number.** The realism audit is a forward-looking protocol; no V3.13 numeric result depends on it.
- **Does not constitute gold annotation.** V3.13 has not run the gold pilot; this is a protocol-level specification of what the gold pilot will additionally measure.
- **Does not claim natural-claim transferability.** Until the realism audit is run and the results are evaluated against the pre-registered thresholds, the silver-stage screening finding is bounded to the diagnostic set.

## File-Level Provenance

- **Specified in:** V3.13 §VII.I (Proposed Gold-Realism Audit Extension)
- **Standalone file:** `proposed_gold_realism_extension.md` (this file)
- **Source paper:** `CESE_OCN_V3_13_differentiated_against_rigourate_forcebench.md`
- **References:** §V.A (SimClaim synthetic/counterfactual transparency), §VII.G (downgrade criteria), §VIII.D.B (screening utility), §IX item 10 (SimClaim is a controlled counterfactual diagnostic set)
- **Status:** Proposed, not yet collected. No gold pilot has been run as of V3.13.
