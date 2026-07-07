# SimClaim-Eval v1 Annotation Guidelines

**Version:** v1.0
**Status:** guideline refinement draft, calibrated against the SimClaim-Eval v1 round1 seed set (42 samples, user-confirmed GPT-adjudicated).
**Not for:** this guideline must not be used to claim that round1_seed is a benchmark, gold test, or human-audited set.

---

## 1. Task Definition

**Simulation claim–evidence auditing** is the task of deciding whether a **claim's strength exceeds the support capacity of its cited evidence**.

For each `(claim, evidence)` pair, the annotator assigns four **claim_tier** values (how strong the claim is on each dimension) and four **support_tier** values (how strong the evidence support actually is on each dimension). An **escalation** is recorded on any dimension where `claim_tier > support_tier`.

> The audit judges **support capacity**, not truth. The question is *not* "is this claim true?" but **"does the cited evidence carry the weight this claim places on it?"**

This is a *tier-exceedance* ordinal task, not a 3-way NLI entailment task. There is no neutral class; absence of overclaim is recorded as `escalation_label=0` with `escalation_type=none`.

---

## 2. The Four Tier Dimensions

Each `(claim, evidence)` pair is audited on four independent dimensions. A claim can overclaim on one dimension while being well-supported on another.

| Dimension | Question it answers |
| --- | --- |
| **scope** | How broad / general / deployment-level is the statement? Does the evidence cover that breadth? |
| **causal** | Does the claim assert a causal or mechanistic relationship? Does the evidence justify that causal strength? |
| **action** | Does the claim imply an actionable prescription / deployment / policy recommendation? Does the evidence support that level of actionability? |
| **certainty** | How confident / definite is the claim's phrasing? Does the evidence provide that level of certainty? |

Each dimension has a **claim side** (`claim_scope_tier`, `claim_causal_tier`, `claim_action_tier`, `claim_certainty_tier`) and a **support side** (`support_scope_tier`, `support_causal_tier`, `support_action_tier`, `support_certainty_tier`).

---

## 3. Tier Values

All eight tier fields use the same 4-point ordinal scale, in `[0, 3]`:

| Tier | Label | Meaning |
| --- | --- | --- |
| **0** | none / not present | The dimension is not articulated in the text. |
| **1** | weak / narrow / suggestive | The dimension is present only weakly, narrowly, or by suggestion. |
| **2** | moderate / bounded but meaningful | The dimension is present in a bounded but clearly meaningful way (most round1_seed samples live here). |
| **3** | strong / broad / deployment-level / high-certainty | The dimension is asserted broadly, deployment-grade, or with high epistemic certainty. |

> The round1_seed validation requires every tier field to lie in `[0, 3]`. Tier=0 is valid and common on the support side (e.g., `support_causal_tier=0` when evidence provides no causal mechanism).

---

## 4. `escalation_label` Derivation Rule

`escalation_label` is **derived**, not annotated independently. It is `1` if and only if **at least one** dimension shows claim exceeding support:

```text
escalation_label = 1 if any(claim_tier[d] > support_tier[d]) for d in {scope, causal, action, certainty}
escalation_label = 0 otherwise
```

If `escalation_label=0`, then `escalation_type` must be `none`.
If `escalation_label=1`, then `escalation_type` records *which* dimension(s) overclaim.

The round1_seed validation script enforces this derivation rule on every record. Hand-editing `escalation_label` to a value inconsistent with the tier matrix is an audit error.

---

## 5. `escalation_type` Rule

`escalation_type` is a categorical tag recording which dimension(s) overclaim. The allowed values are:

| `escalation_type` | Meaning |
| --- | --- |
| `none` | No dimension overclaims (`escalation_label=0`). |
| `scope` | Only the scope dimension overclaims. |
| `causal` | Only the causal dimension overclaims. |
| `action` | Only the action dimension overclaims. |
| `certainty` | Only the certainty dimension overclaims. |
| `multi` | Two or more dimensions overclaim simultaneously. |

If exactly one dimension overclaims, use that dimension's label. If two or more overclaim, use `multi`. The round1_seed set has `multi` as the dominant escalation_type (24/31 escalation-positive samples), reflecting that real-world simulation overclaims typically conflate scope, certainty, and actionability in a single sentence.

---

## 6. `contradiction_label` Rule

`contradiction_label` is `1` **only when the cited evidence explicitly rebuts or refutes the claim**, not when it merely fails to support it.

| Situation | `contradiction_label` |
| --- | --- |
| Evidence directly refutes the claim ("the simulation showed X, contradicting the claim's Y") | `1` |
| Evidence provides no mechanism / data for the claim's strength, but does not refute it | `0` |
| Evidence is too vague, short, or noisy to either support or refute | `0` |
| Evidence supports a strictly weaker version of the claim but not the strong version asserted | `0` (this is an overclaim, recorded by `escalation_label=1`, not a contradiction) |

> **Insufficient evidence is NOT contradiction.** An overclaim where evidence is silent is `escalation_label=1, contradiction_label=0`. A contradiction requires positive evidence against the claim.

---

## 7. Per-Dimension Examples from round1_seed

All examples below are real samples from the SimClaim-Eval v1 round1_seed set (`data/simclaim_eval_v1/round1_seed/processed/round1_seed_adjudicated.jsonl`). Sample text is truncated for readability; the full text is recoverable from the JSONL by `sample_id`.

### 7.1 Scope Dimension

**Supported example** — `CAND0001` [scenario_specific_supported_control, wargaming]
- `claim_scope_tier=2`, `support_scope_tier=2`
- The claim ("CSIS designed a wargame ... ran it 24 times ... Taiwan survived as autonomous entity in most scenarios") is bounded to a specific 24-run wargame, and the evidence describes exactly that 24-run wargame with its scenario-specific outcomes. The breadth of the claim matches the breadth of the evidence.

**Overclaim example** — `CAND0002` [scenario_scope_overclaim, wargaming]
- `claim_scope_tier=2`, `support_scope_tier=1`
- The claim ("A Chinese blockade of Taiwan could see the greatest naval battles since World War II. Twenty-six wargames illustrated the risks ...") asserts a broad historical-scope consequence, but the cited evidence describes the *scenario setup* of military drills, not the *conclusion* that those would be "the greatest naval battles since WWII". The evidence supports the wargame-existence claim but not the broad-scope escalation framing.

**Borderline example** — `CAND0035` [strong_language_supported, cyber_emulation]
- `claim_scope_tier=2`, `support_scope_tier=2`
- The claim ("Apache Caldera is a cybersecurity framework that empowers practitioners to save time, money, and energy through automated security assessments") uses broad marketing language, but the cited MITRE platform documentation describes exactly that platform's automated adversary-emulation scope. The strong language is supported; this is **not** an overclaim despite the marketing register. This is the canonical case for the "strong-language-supported" hard_case_type.

### 7.2 Causal Dimension

**Supported example** — `NEWCAND021` [strong_language_supported, traffic_simulation]
- `claim_causal_tier=2`, `support_causal_tier=2`
- The claim ("Simulation has the potential to massively scale evaluation of self-driving systems enabling rapid development as well as safe deployment") posits a causal/mechanistic link between simulation and scaling. The cited paper describes the simulation setup, metrics, and shows the approach generates more realistic scenarios than baselines — a moderate causal claim matched by moderate causal evidence.

**Overclaim example** — `CAND0035` [strong_language_supported, cyber_emulation]
- `claim_causal_tier=2`, `support_causal_tier=1`
- Same sample as the scope-borderline example. The marketing claim implies Caldera "empowers practitioners to save time, money, and energy", which is a causal efficiency claim. The platform documentation describes capabilities but provides no measured efficiency outcome. Causal strength of the claim (2) exceeds the causal support (1) even though scope is matched.

**Borderline example** — `NEWCAND023` [insufficient_not_contradiction, traffic_simulation]
- `claim_causal_tier=2`, `support_causal_tier=2`
- The claim ("TRAFFIC SIM can be used to generate synthetic training data for learning better motion planners") makes a moderate causal claim about data→planner improvement. The evidence describes TrafficSim's approach and shows scenario realism, but does **not** directly measure downstream planner improvement. The causal support is bounded but present (matched at tier 2); this is the canonical "insufficient-but-not-contradiction" boundary.

### 7.3 Action Dimension

**Supported example** — `CAND0082` [cyber_actionability_supported_or_boundary, cyber_training]
- `claim_action_tier=2`, `support_action_tier=2`
- The claim ("Enables your team to perform automated testing of cyber defenses, to include network & host defenses, logging & sensors, analytics & alerting, and automated response") prescribes concrete defensive-testing actions. The cited cyber-range documentation describes exactly that interactive, hands-on testing capability. Actionability matched.

**Overclaim example** — `CAND0081` [cyber_actionability_overclaim, cyber_training]
- `claim_action_tier=2`, `support_action_tier=1`
- The claim text is identical to CAND0082 (same Caldera-style marketing of "automated testing of cyber defenses"), but here the cited evidence is a high-level discussion of the *gap* between technical cyber exercises and strategic tabletop exercises — it acknowledges the existence of such tools without supporting the prescription that "your team can perform automated testing". Actionability overclaim.

**Borderline example** — `CAND0006` [digital_twin_actionability_boundary, digital_twin]
- `claim_action_tier=2`, `support_action_tier=2`
- The claim ("In advanced applications, digital twins would also use simulation, machine learning and reasoning to support decision-making") is a moderate, hedged actionability claim. The cited digital-twin report discusses decision-support use cases but emphasizes uncertainty quantification as a precondition. The action prescription is bounded on both sides (tier 2); the borderline concern is whether "support decision-making" is fully actionable without the uncertainty caveat, which keeps this from being a clean overclaim.

### 7.4 Certainty Dimension

**Supported example** — `CAND0001` [scenario_specific_supported_control, wargaming]
- `claim_certainty_tier=2`, `support_certainty_tier=2`
- The claim is phrased in scenario-specific, hedged terms ("Although Taiwan survived ... in most scenarios, losses ... were heavy"). The evidence describes the same hedged scenario outcomes. Certainty of the claim matches certainty of the evidence.

**Overclaim example** — `CAND0002` [scenario_scope_overclaim, wargaming]
- `claim_certainty_tier=2`, `support_certainty_tier=1`
- The claim phrasing ("could see the greatest naval battles since World War II") asserts a high-magnitude historical consequence with confidence. The cited evidence is descriptive of drills and exercises without quantifying the magnitude of any naval engagement. The claim's certainty exceeds what the evidence establishes.

**Borderline example** — `CAND0035` [strong_language_supported, cyber_emulation]
- `claim_certainty_tier=2`, `support_certainty_tier=2`
- The claim uses strong register ("empowers", "save time, money, and energy"). The platform documentation supports this register as the platform's stated purpose. Certainty is matched at tier 2. The marketing register alone does **not** create a certainty overclaim when the evidence is also a platform-description at the same register; this is the rule that separates `strong_language_supported` from genuine certainty overclaims.

---

## 8. Boundary Clarifications

These five boundary cases caused the most disagreement between annotator_01 and annotator_02 in round1, and are the focus of the round2 candidate expansion.

### 8.1 Scope vs Certainty

A claim can use high-certainty language ("will", "the greatest") without making a broad-scope claim, and vice versa. Audit them separately:

- **scope** answers *how broadly the claim generalizes*.
- **certainty** answers *how confident the claim's phrasing is*.

`CAND0002` is the canonical example: high-certainty register ("the greatest naval battles since WWII") **and** broad-scope framing (generalizing from 26 wargames to historical magnitude). Both dimensions overclaim independently.

### 8.2 Actionability vs Scope

A claim can be **broad in scope without being actionable** ("simulation will transform every field") and **actionable without being broad** ("use Caldera to test your blue team"). Audit them separately:

- **scope** answers *how broadly the claim generalizes*.
- **action** answers *whether the claim prescribes a concrete step / deployment / policy*.

`CAND0082` is a clean actionability-supported case (the prescription is concrete and matched by the evidence). `CAND0058` [policy_actionability_overclaim] is a case where the claim prescribes policy changes based on a wargame series whose evidence is descriptive of operational challenges but does not directly validate the proposed policy actions.

### 8.3 Causal Overclaim vs Insufficient Evidence

A causal overclaim is `claim_causal_tier > support_causal_tier` — the claim asserts a causal mechanism that the evidence does not bear out. This is **not** the same as "insufficient evidence":

- **causal overclaim**: the evidence provides *some* causal signal but not at the strength claimed.
- **insufficient evidence**: the evidence provides *no usable causal signal at all* — the claim may or may not be true, but the cited text simply does not address the causal mechanism.

`NEWCAND023` is the canonical "insufficient-not-contradiction" case: the claim posits downstream planner improvement; the evidence addresses scenario realism but not planner improvement. The causal tier is matched at 2 because both sides are bounded — this is a borderline *insufficient* case, not a clean causal overclaim. Annotators should distinguish these.

### 8.4 Contradiction vs Unsupported / Insufficient

This is the most important boundary and the one the round1_seed set is *weakest* on (`contradiction_label=1` count is 0 — see §9). The three states are:

| State | `escalation_label` | `contradiction_label` | Diagnostic |
| --- | --- | --- | --- |
| Supported | 0 | 0 | Evidence carries the claim's weight. |
| Overclaim / Unsupported / Insufficient | 1 | 0 | Evidence does not carry the claim's weight, but does not refute it. |
| Direct contradiction | 0 or 1 | 1 | Evidence explicitly rebuts the claim. |

`contradiction_label=1` requires **positive textual evidence against the claim**, not merely absence of support. The round1_seed set has zero such samples; round2 must add at least 15 contradiction-positive candidates to close this gap.

### 8.5 "Strong-language-supported" is NOT Overclaim

When a claim uses marketing / promotional register ("empowers", "transforms", "massively scales") **and** the cited evidence is at the same register (platform documentation, vendor whitepaper, or paper abstract making the same claim), the strong language is **supported at that register**. This is the `strong_language_supported` hard_case_type (6 samples in round1_seed).

This becomes an overclaim **only when**:
- the claim's strong register implies a **causal** or **deployment** claim that the documentation does not make, or
- the claim's strong register is broader in **scope** than the documented capability.

`CAND0035` is supported (certainty matched at 2) but overclaims on causal (claim_causal=2 > support_causal=1) — the marketing register is supported, but the implied efficiency mechanism is not. Annotators should resist the heuristic "marketing language = overclaim" and instead check each dimension's tier matrix.

---

## 9. Round1 Limitations

These limitations are recorded in `data/simclaim_eval_v1/round1_seed/manifests/round1_seed_manifest.json` and must be respected by any downstream use:

1. **`contradiction_label=1` count is 0.** Round1 contains no direct-contradiction samples. Any pipeline output that requires contradiction positives (e.g., 3-way NLI-style evaluation, contradiction detection head) cannot be validated on round1_seed alone.
2. **Round1 is not sufficient to train a formal model.** With n=42 and zero contradiction positives, any model trained on round1_seed would overfit the overclaim class and have no signal for contradiction.
3. **Round1 is not sufficient for paper main results.** Every record has `paper_valid=false` and `main_text_allowed=false`. Round1 outputs are seed-set diagnostics, not paper-valid evaluation.
4. **Round1 is for:** annotation guideline refinement, seed-set inspection, and pipeline smoke tests only. Any other use requires explicit re-flagging.
5. **`user_confirmed=true` does not imply `human_audited=true`.** Round1 labels are GPT-annotated + GPT-adjudicated + user-final-confirmed, not dual-human-audited gold.
6. **Coverage gaps.** `noisy_evidence` (n=1), `insufficient_not_contradiction` (n=4), `cue_free_overclaim` (n=0), and `contradiction_positive` (n=0) are all under-represented; these are the explicit targets of the round2 expansion plan in `data/simclaim_eval_v1/round2_candidates/candidate_targets_round2.md`.

---

## 10. Cross-References

- Round1 seed set: `data/simclaim_eval_v1/round1_seed/`
- Round1 manifest: `data/simclaim_eval_v1/round1_seed/manifests/round1_seed_manifest.json`
- Round1 validation report: `data/simclaim_eval_v1/round1_seed/reports/round1_seed_validation_report.md`
- Round1 coverage gap report: `data/simclaim_eval_v1/round1_seed/reports/round1_coverage_gap_report.md`
- Round2 candidate expansion plan: `data/simclaim_eval_v1/round2_candidates/`
- Data status overview: `docs/simclaim_eval_v1_data_status.md`
- Machine-readable guideline: `docs/annotation_guidelines_simclaim_eval_v1.json`
