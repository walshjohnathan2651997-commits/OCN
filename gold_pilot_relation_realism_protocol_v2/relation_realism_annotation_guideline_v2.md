# Annotation Guideline v2 — Relation + Realism (Two-Layer)

**Version:** 2.0 (DRAFT, ready for annotator training)
**Date:** 2026-07-05
**Status:** v2 DRAFT. v1 (gold_pilot_protocol_freeze_v1) is FROZEN and untouched. v2 adds Layer 2 realism on top of v1 Layer 1 relation. v2 does NOT replace v1; both versions coexist for comparison.
**Scope:** Gold pilot, 50 (claim, evidence) pairs, two independent annotators + one adjudicator. Two-layer annotation: Layer 1 relation label + Layer 2 realism score.
**Predecessor:** `D:\ocn\gold_pilot_protocol_freeze_v1\annotation_guideline_v1_frozen.md` (Layer 1 only).

---

## 0. Task in Two Sentences

You will read a **claim** and an **evidence span** from a scientific paper, and judge **two independent things**:

1. **Layer 1 (Relation):** Is the evidence sufficient for the strength of the claim as written? (Same task as v1.)
2. **Layer 2 (Realism):** Does the claim read like a natural claim a real scientist might write, or does it sound artificial / templated / forced?

**These two layers are INDEPENDENT.** A claim can be relation-correct but realism-low (e.g., a faithful paraphrase that nonetheless sounds machine-generated). A claim can be realism-high but relation-wrong (e.g., a beautifully written overclaim). You must score both layers separately.

---

## 1. Why Two Layers?

SimClaim is a **controlled counterfactual diagnostic set**. The evidence is real (from peer-reviewed papers), but the claims are AI-generated counterfactual variants: a faithful *supported* claim, a *mild_scope_overclaim*, a *strong_action_overclaim*, and a *contradiction_candidate*, all built around the same evidence.

This design is deliberate — it stress-tests R4's boundary-recognition ability under controlled conditions. But it introduces a **realism risk**: the generated claims may sound templated, mechanical, or forced. The v1 protocol only validates the relation label (Layer 1); v2 adds the realism layer (Layer 2) so we can:

- Validate that the relation taxonomy is reliably annotated (v1 goal).
- Quantify how realistic the generated claims are (v2 new goal).
- Decide which claims are safe to use as paper illustrative examples.
- Trigger a paper-claim downgrade if realism is poor (pre-registered thresholds: 25% class-level, 25% paper-level).

**Critical distinction:**

| Question | Layer | Answer type |
| --- | --- | --- |
| Does the evidence support the claim as written? | Layer 1 (Relation) | One of 4 labels (+ unsure) |
| Does the claim sound like real scientific writing? | Layer 2 (Realism) | Score 1-5 + issue type |

---

## 2. Layer 1: Relation Label (carried over from v1)

### 2.1 The five labels

The five relation labels are unchanged from v1:

1. **`supported`** — evidence is sufficient for the claim's stated strength.
2. **`mild_scope_overclaim`** — claim mildly over-extends scope (no action/deployment conclusion).
3. **`strong_action_overclaim`** — claim asserts action/deployment/safety/policy/generalization that evidence doesn't justify.
4. **`contradiction_candidate`** — evidence contradicts the claim (directional conflict, number/name/metric swap).
5. **`unsure`** — only after genuine effort; must explain in `relation_rationale_one_sentence` and note the two classes in `relation_confusion_if_any`.

Full definitions, examples, and boundary rules are in `annotation_guideline_v1_frozen.md` (v1, FROZEN). v2 does NOT redefine the labels — v1 is the authoritative source for Layer 1.

### 2.2 Layer 1 fields (in v2 template)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `annotator_relation_label` | enum | yes | One of: supported / mild_scope_overclaim / strong_action_overclaim / contradiction_candidate / unsure |
| `relation_confidence_1_to_5` | int 1-5 | yes | 1=guessing, 3=moderately confident, 5=certain |
| `relation_rationale_one_sentence` | string | yes | One sentence explaining the label choice. Cite the specific phrase that triggered the label. |
| `relation_confusion_if_any` | string | optional | Note if you were torn between two labels (e.g., "mild_vs_strong"). Blank if no confusion. |
| `needs_relation_adjudication` | yes/no | yes | "yes" if you want the adjudicator to review this case. Default "no". |

### 2.3 Layer 1 rules (carry over from v1)

- Apply the v1 decision tree (`annotation_decision_tree_v1.md`).
- Apply the v1 boundary rules (`boundary_rules_v1.md`).
- `unsure` is allowed but discouraged — prefer a leaning label with `relation_confusion_if_any` noted.
- Blank `unsure` without `relation_rationale_one_sentence` is invalid.

---

## 3. Layer 2: Realism Score (NEW in v2)

### 3.1 What "realism" means

**Realism = how natural the claim sounds as a piece of scientific writing.**

A realistic claim reads like something a real scientist might write in a paper, a review, or a technical report. An unrealistic claim sounds machine-generated, templated, mechanical, or forced.

**Realism is NOT about whether the claim is true.** A claim can be a deliberate overclaim (Layer 1 = `strong_action_overclaim`) and still be realistic — real scientists do write overclaims. A claim can be a faithful paraphrase (Layer 1 = `supported`) and still be unrealistic — if it sounds like a robot wrote it.

**Realism is NOT about whether the claim matches the evidence.** That's Layer 1. Layer 2 asks: setting aside the evidence, does this claim *as a sentence* read like scientific writing?

### 3.2 The five-point realism scale

| Score | Label | Description |
| --- | --- | --- |
| **5** | very natural | Reads like a sentence from a real scientific paper. No awkwardness, no templated feel, no forced cues. A scientist could have written this. |
| **4** | mostly natural | Reads naturally with minor awkwardness. A scientist might edit it slightly, but it's clearly scientific writing. |
| **3** | somewhat artificial but usable | Noticeably stiff or formulaic, but a reader would still understand it as a scientific claim. Acceptable for diagnostic purposes, not ideal for paper examples. |
| **2** | artificial / forced | Clearly machine-generated or templated. Sounds like a fill-in-the-blank exercise. A scientist would likely rewrite it. |
| **1** | unrealistic / unusable | So unnatural that it would not appear in any real scientific writing. Slogan-like, mechanically stitched, or nonsensical. |

### 3.3 Layer 2 fields (in v2 template)

| Field | Type | Required | Description |
| --- | --- | --- | --- |
| `claim_realism_score_1_to_5` | int 1-5 | yes | 5=very natural, 1=unrealistic (see scale above) |
| `claim_realism_issue` | enum | yes | The dominant realism issue (see §3.4). Use `none` if score >= 4. |
| `realism_rationale_one_sentence` | string | yes | One sentence explaining the realism score. Cite the specific phrase that triggered the issue. |
| `claim_usable_for_paper_example` | yes/no | yes | "yes" if you would be comfortable quoting this claim in the paper body as an illustrative example. "no" if it would embarrass the paper. |
| `needs_realism_adjudication` | yes/no | yes | "yes" if you want the adjudicator to review the realism score. Default "no". |

### 3.4 The nine `claim_realism_issue` types

Pick the **dominant** issue (the one that most lowers the realism score). If multiple issues apply, pick the most severe. If score >= 4, use `none`.

| Issue | Description | Detection cues |
| --- | --- | --- |
| `none` | No realism issue. Claim reads naturally. | Use when score >= 4. |
| `too_template_like` | Claim is obviously one of a templated quartet; reads like a fill-in-the-blank variant. | Phrases like "as the main comparison basis", "as the primary evaluation basis", or near-duplicate sentence structure across variants. |
| `too_extreme` | Claim uses overclaim words that no real scientist would use in a paper. | "always", "guarantee", "fully solves", "completely eliminates", "proves", "deployment-ready", "100%". |
| `unnatural_wording` | Claim is grammatical but awkward; sentence structure is mechanical or stitched. | Unnatural transitions, redundant qualifiers, awkward clause ordering. |
| `not_scientific_claim` | Claim sounds like a slogan, policy recommendation, or marketing line rather than a scientific claim. | "should be deployed", "we recommend", "policymakers should", "game-changer", "revolutionize". |
| `contradiction_too_mechanical` | (For contradiction candidates) The contradiction is obviously a simple negation/number-swap, not a realistic misreading. | Pure "not" insertion, number change with no other modification, metric name swap. |
| `strong_action_too_forced` | (For strong_action claims) The deployment/safety/policy language is clearly stuffed in, not naturally arising. | Deployment/safety/policy cues appear in claim but evidence is purely experimental, with no deployment context. |
| `mild_strong_boundary_unclear` | The claim sits ambiguously between mild and strong, suggesting the cue word is the only difference. | Claim differs from a sibling only by swapping "scope" cue for "action" cue. |
| `ambiguous_or_vague` | Claim is too vague to evaluate as a scientific statement. | Lacks specific subject, metric, or scope. |

### 3.5 Layer 2 rules

- **Score independently of Layer 1.** Do not let the relation label influence the realism score. A `strong_action_overclaim` can score 5 on realism; a `supported` can score 1.
- **Score the claim text alone.** Do not consult the evidence when scoring realism (you may consult it for Layer 1, but Layer 2 is about the claim as a sentence).
- **Be strict about paper examples.** `claim_usable_for_paper_example = yes` only if you would put this claim in a paper without editing. If you would rewrite it, mark "no".
- **`claim_realism_issue` is required even for high scores.** If score >= 4, use `none`. If score <= 3, you must identify a dominant issue.
- **`realism_rationale_one_sentence` must cite the specific phrase.** "Sounds weird" is not acceptable. "The phrase 'as the main comparison basis' is a fill-in-the-blank template marker" is acceptable.
- **If you mark `needs_realism_adjudication = yes`, you must explain why** in `realism_rationale_one_sentence`.

---

## 4. Independence of Layer 1 and Layer 2 — Examples

### 4.1 Relation-correct, realism-low

- Evidence: "We extend the benchmark with Success Rate and All-Core Pass Rate to assess robustness."
- Claim: "nuPlan-R adds Success Rate and All-Core Pass Rate metrics to assess planner robustness and performance balance over multiple evaluation dimensions."
- **Layer 1:** `supported` (faithful paraphrase, scope preserved).
- **Layer 2:** score 3 (`too_template_like` — reads like a generated paraphrase, "over multiple evaluation dimensions" is a stock phrase).
- **Layer 2 `claim_usable_for_paper_example`:** no (would need rewriting).

### 4.2 Relation-wrong, realism-high

- Evidence: "We evaluate on three domains: autonomous driving, robotics, and digital twin."
- Claim: "Our method generalizes robustly across all real-world deployment domains, including safety-critical autonomous systems."
- **Layer 1:** `strong_action_overclaim` (generalizes from 3 domains to "all real-world deployment domains", adds "safety-critical" framing).
- **Layer 2:** score 5 (the claim reads like a real overclaim a scientist might write in an introduction — natural phrasing, no template feel).
- **Layer 2 `claim_usable_for_paper_example`:** yes (this is exactly the kind of overclaim the paper is about).

### 4.3 Both layers low

- Evidence: "The method achieves 78.4% accuracy on the test set."
- Claim: "The method completely solves the problem and is deployment-ready with 100% reliability."
- **Layer 1:** `strong_action_overclaim` (extreme escalation).
- **Layer 2:** score 1 (`too_extreme` — "completely solves", "deployment-ready", "100% reliability" — no scientist writes this).
- **Layer 2 `claim_usable_for_paper_example`:** no (this is a strawman, not a realistic overclaim).

### 4.4 Both layers high

- Evidence: "Performance does not saturate: coordination and total reward continue improving late in training."
- Claim: "Extended training shows continued improvement in coordination and total reward, with no saturation observed in the late phase."
- **Layer 1:** `supported` (faithful paraphrase).
- **Layer 2:** score 5 (natural scientific writing).
- **Layer 2 `claim_usable_for_paper_example`:** yes.

---

## 5. Workflow per claim

1. Read the evidence and claim.
2. **Layer 1:** Apply v1 decision tree. Pick `annotator_relation_label`. Set `relation_confidence_1_to_5`. Write `relation_rationale_one_sentence`. Note `relation_confusion_if_any` if torn. Set `needs_relation_adjudication`.
3. **Layer 2:** Re-read the claim text alone (set aside the evidence). Pick `claim_realism_score_1_to_5`. Pick `claim_realism_issue`. Write `realism_rationale_one_sentence`. Set `claim_usable_for_paper_example`. Set `needs_realism_adjudication`.
4. Move to the next row.

**Estimated time per row:** 3-5 minutes (Layer 1: 2-3 min, Layer 2: 1-2 min). Total for 50 rows: ~3-4 hours per annotator.

---

## 6. What NOT to do

- Do NOT let Layer 1 influence Layer 2. Score them independently.
- Do NOT consult silver labels (they are not in your template).
- Do NOT look at the other annotator's work.
- Do NOT skip Layer 2 because Layer 1 was easy. Both layers are required for every row.
- Do NOT mark `claim_usable_for_paper_example = yes` for claims with `claim_realism_score_1_to_5 <= 2`. If the claim is unrealistic, it cannot be a paper example.
- Do NOT use `claim_realism_issue = none` for claims with score <= 3. Every low-realism claim must have an identified issue.
- Do NOT leave `realism_rationale_one_sentence` blank. Every row must have a one-sentence rationale.

---

## 7. Quality checks you should perform on your own work

Before submitting:

1. All 50 rows have both Layer 1 and Layer 2 fields filled.
2. No `annotator_relation_label` is blank.
3. No `claim_realism_score_1_to_5` is blank or out of range 1-5.
4. Every `claim_realism_score_1_to_5 <= 3` has a non-`none` `claim_realism_issue`.
5. Every `claim_realism_score_1_to_5 <= 2` has `claim_usable_for_paper_example = no`.
6. Every `realism_rationale_one_sentence` is non-blank and cites a specific phrase.
7. Every `unsure` relation label has a non-blank `relation_confusion_if_any`.

---

## 8. After submission

The adjudicator will:
1. Compute Layer 1 agreement (Cohen's κ, per-label, mild-vs-strong κ).
2. Compute Layer 2 agreement (realism score correlation, issue-type agreement, usable-for-paper agreement).
3. Adjudicate disagreements separately: Layer 1 first, then Layer 2.
4. Produce final gold with both `final_relation_label` and `final_realism_score`.
5. Apply pre-registered decision rules:
   - If `mild_vs_strong` κ < 0.4 → taxonomy revision required.
   - If `strong_action` retention < 0.40 → paper claim downgrade.
   - If class-level high-realism rate (score <= 2) > 25% → paper claim downgrade.
   - If paper-level high-realism rate > 25% → major paper downgrade.

See `relation_realism_adjudication_protocol_v2.md` and `relation_realism_agreement_plan_v2.md` for details.

---

## 9. Version control and relationship to v1

- v1 (`gold_pilot_protocol_freeze_v1`): FROZEN, Layer 1 only. **Not modified by v2.**
- v2 (this protocol): DRAFT, Layer 1 + Layer 2. **Does not replace v1.**
- v1 and v2 templates use the same 50 pilot samples (same `pilot_id`).
- v2's Layer 1 schema is a relabel of v1's schema (e.g., `annotator_label` → `annotator_relation_label`). Layer 1 definitions are unchanged from v1.
- Annotators who have already trained on v1 need only a short v2 briefing (Layer 2 addition). Annotators new to the project should train on both v1 (for Layer 1) and v2 (for Layer 2).
