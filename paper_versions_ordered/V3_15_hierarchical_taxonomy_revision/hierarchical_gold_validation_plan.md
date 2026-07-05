# Hierarchical Gold Validation Plan (Level-1 + Level-2 + Fallback)

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
