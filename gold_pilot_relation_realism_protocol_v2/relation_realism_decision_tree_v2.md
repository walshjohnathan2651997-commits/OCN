# Decision Tree v2 — Relation + Realism (Two Independent Trees)

**Version:** 2.0 (DRAFT)
**Date:** 2026-07-05
**Status:** v2 DRAFT. v1 (`annotation_decision_tree_v1.md`) is FROZEN and untouched. v2 contains TWO independent decision trees: Tree A (relation, carried over from v1) + Tree B (realism, NEW in v2).
**Predecessor:** `D:\ocn\gold_pilot_protocol_freeze_v1\annotation_decision_tree_v1.md`

---

## How to use this document

For each (claim, evidence) pair, you will walk through **two decision trees independently**:

1. **Tree A (Relation)** — using both evidence and claim. Determines `annotator_relation_label`.
2. **Tree B (Realism)** — using claim text only (set the evidence aside). Determines `claim_realism_score_1_to_5` and `claim_realism_issue`.

**The trees are independent.** Do not let Tree A's outcome influence Tree B. A claim that is `strong_action_overclaim` in Tree A can score 5 (very natural) in Tree B. A claim that is `supported` in Tree A can score 1 (unrealistic) in Tree B.

---

# Tree A: Relation Decision Tree (carried over from v1)

This is the same 6-step decision tree as v1, reproduced here for annotator convenience. **The authoritative source is `annotation_decision_tree_v1.md`.** If this v2 reproduction and v1 ever conflict, v1 wins.

## Step A1: Is there a directional conflict on the same metric, number, entity, or fact?

- **Yes** → `contradiction_candidate`. (Example: evidence "24.5% accuracy" vs claim "above 30% accuracy"; evidence "IPPO and PQN" vs claim "PPO-RNN and SAC"; evidence "performance does not saturate" vs claim "performance saturates".)
- **No** → go to Step A2.

**Detail-swap rule:** If the claim cites a different number/name/metric than the evidence for the same thing, that is `contradiction_candidate`, even if no contradiction cue word is present. Number inflation (90%→95%) is `contradiction_candidate`, not `strong_action_overclaim`.

## Step A2: Does the claim assert an action, deployment, safety, policy, generalization, guarantee, or operational conclusion?

Look for cue words: deploy, deployment, safety, guarantee, operational, policy, broad generalization, suitable for, ready for, can be used to, enables, ensures, demonstrates, proves (in operational/deployment sense).

- **Yes** → go to Step A3.
- **No** → go to Step A4.

## Step A3: Does the evidence justify the action/deployment/safety conclusion as stated?

- **Yes, evidence explicitly supports the action conclusion** → `supported`. (Rare: the evidence itself discusses deployment/safety and the claim matches.)
- **No, evidence is local/experimental/simulated but claim extrapolates to deployment/safety/policy** → `strong_action_overclaim`.

## Step A4: Does the claim expand the scope, breadth, or precision of the evidence?

Look for: single-dataset → multi-dataset, single-domain → multi-domain, adds precision details ("as the main comparison basis", "multi-stage", "across domains", "and five starting conditions").

- **Yes, claim adds scope/precision not in evidence, but no action conclusion** → `mild_scope_overclaim`.
- **No, claim matches evidence's scope and strength** → `supported`.

## Step A5: Is the evidence too short or context too missing to judge?

- **Yes** → mark `unsure` with `relation_confusion_if_any = evidence_insufficient_context`. Explain in `relation_rationale_one_sentence`.
- **No** → go to Step A6.

## Step A6: After applying Steps A1-A4, are you still torn between two adjacent labels?

- **Yes** → pick the label you lean toward and note the confusion in `relation_confusion_if_any` (e.g., "mild_vs_strong", "strong_vs_contradiction"). This is more informative than `unsure`.
- **No, you have a clear label** → use it.

**`unsure` is a last resort.** Use it only if you genuinely cannot narrow to two classes. Blank `unsure` without `relation_rationale_one_sentence` is invalid.

---

## Tree A boundary rules (see `boundary_rules_v1.md` for full version)

1. **`supported` vs `mild_scope_overclaim`:** Paraphrase that preserves scope = `supported`. Adding scope/precision detail not in evidence = `mild`.
2. **`mild_scope_overclaim` vs `strong_action_overclaim` (HARDEST boundary):** Scope expansion only = `mild`. Action/deployment/safety/policy/generalization conclusion = `strong`. The cue word "deployment/safety/policy" tips it to `strong`.
3. **`strong_action_overclaim` vs `contradiction_candidate`:** Directional conflict on same metric/number/entity = `contradiction`. Same direction, just too strong = `strong_action`. Number inflation (90%→95%) = `contradiction`.
4. **`contradiction_candidate` vs `mild_scope_overclaim`:** Detail-swap of numbers/names/metrics = `contradiction`. Scope expansion without detail-swap = `mild`.
5. **Evidence too short:** Mark `unsure` with `evidence_insufficient_context`.
6. **`unsure`:** Last resort. Pick a leaning label with `relation_confusion_if_any` if possible.

---

# Tree B: Realism Decision Tree (NEW in v2)

This tree scores **how natural the claim sounds as scientific writing**, independent of whether the claim is relation-correct. Use **only the claim text** (set the evidence aside).

## Step B1: Read the claim as a standalone sentence. Does it sound like something a real scientist would write in a paper, review, or technical report?

- **Yes, completely natural** → score 5, `claim_realism_issue = none`. Done.
- **Mostly natural, minor awkwardness** → score 4, `claim_realism_issue = none`. Done.
- **Noticeably stiff or formulaic** → go to Step B2.
- **Clearly artificial or forced** → go to Step B2.
- **Unrealistic / unusable as scientific writing** → go to Step B2.

## Step B2: Identify the dominant realism issue (pick ONE — the most severe)

Walk through these in order. Pick the **first** one that applies.

### B2a: Is the claim using extreme words that no real scientist would write?

Look for: "always", "guarantee", "fully solves", "completely eliminates", "proves", "deployment-ready", "100% reliability", "foolproof", "perfect", "flawless".

- **Yes** → score 1-2, `claim_realism_issue = too_extreme`. Cite the extreme word in `realism_rationale_one_sentence`. Done.

### B2b: Does the claim sound like a slogan, policy recommendation, or marketing line rather than a scientific claim?

Look for: "should be deployed", "we recommend", "policymakers should", "game-changer", "revolutionize", "cutting-edge", "next-generation", "paradigm shift", "unlock", "holy grail", "silver bullet", "groundbreaking".

- **Yes** → score 1-2, `claim_realism_issue = not_scientific_claim`. Cite the slogan phrase. Done.

### B2c: Does the claim read like a fill-in-the-blank template, obviously one of a quartet of near-identical variants?

Look for: stock phrases like "as the main comparison basis", "as the primary evaluation basis", "as the key basis", "in all contexts", "under all conditions", "without any caveat", "across all", "as the sole", "the paper asserts that", "the paper claims that". Also flag if the sentence structure feels mechanically generated (e.g., subject-verb-object with no natural flow).

- **Yes** → score 2-3, `claim_realism_issue = too_template_like`. Cite the stock phrase. Done.

### B2d: Is the claim grammatical but awkward — mechanical sentence structure, unnatural transitions, redundant qualifiers?

Look for: awkward clause ordering, redundant qualifiers ("very highly robust"), unnatural transitions, stitched-together phrases.

- **Yes** → score 2-3, `claim_realism_issue = unnatural_wording`. Cite the awkward phrase. Done.

### B2e: (For contradiction candidates only) Is the contradiction obviously a simple negation, number-swap, or metric-swap — with no realistic misreading pattern?

Look for: pure "not" insertion ("The method works" → "The method does not work"), number change with no other modification ("78.4%" → "30%"), metric name swap.

- **Yes** → score 2-3, `claim_realism_issue = contradiction_too_mechanical`. Cite the mechanical swap. Done.
- **No, the contradiction reads like a realistic misreading** → score 4-5, `claim_realism_issue = none`. Done.

### B2f: (For strong_action claims only) Is the deployment/safety/policy language clearly stuffed in, with no natural motivation from the claim's own content?

Look for: deployment/safety/policy cues appear in the claim but the claim's subject is purely experimental/local, with no deployment context established. The action language feels "dropped in" rather than naturally arising.

- **Yes** → score 2-3, `claim_realism_issue = strong_action_too_forced`. Cite the forced cue. Done.
- **No, the action language flows naturally from the claim's content** → score 4-5, `claim_realism_issue = none`. Done.

### B2g: Does the claim sit ambiguously between mild and strong, suggesting the cue word is the only difference?

Look for: claim differs from a hypothetical sibling only by swapping a "scope" cue ("as the main comparison basis") for an "action" cue ("for safety-critical deployment"). The boundary feels arbitrary.

- **Yes** → score 3, `claim_realism_issue = mild_strong_boundary_unclear`. Cite the cue word. Done.

### B2h: Is the claim too vague to evaluate as a scientific statement — lacks specific subject, metric, or scope?

Look for: claims like "The approach is good for many applications" — no specific subject, metric, or scope.

- **Yes** → score 2-3, `claim_realism_issue = ambiguous_or_vague`. Cite the vague phrase. Done.

### B2i: None of the above — but the claim still feels artificial.

- → score 3, `claim_realism_issue = ambiguous_or_vague` (catch-all). Explain in `realism_rationale_one_sentence`.

## Step B3: Set `claim_usable_for_paper_example`

- If `claim_realism_score_1_to_5 >= 4` AND `claim_realism_issue = none` → `claim_usable_for_paper_example = yes`.
- If `claim_realism_score_1_to_5 <= 2` → `claim_usable_for_paper_example = no` (mandatory).
- If `claim_realism_score_1_to_5 = 3` → use judgment. "yes" only if the claim would not embarrass the paper. Default "no" if unsure.

## Step B4: Set `needs_realism_adjudication`

- "yes" if you want the adjudicator to review the realism score (e.g., you are torn between 2 and 3, or you suspect your issue type is wrong).
- "no" otherwise.

---

## Tree B worked examples

### Example B1: Realistic strong_action overclaim

- Claim: "Our method generalizes robustly across all real-world deployment domains, including safety-critical autonomous systems."
- Tree A: `strong_action_overclaim` (generalizes from local results to all real-world domains).
- Tree B:
  - Step B1: Reads naturally — a real scientist might write this in an introduction. Score 5? Or 4 (slightly strong wording "robustly across all")?
  - Decision: score 4, `claim_realism_issue = none`. `claim_usable_for_paper_example = yes`.
  - Rationale: "Claim reads like a natural overclaim a scientist might write; 'across all real-world deployment domains' is strong but plausible."

### Example B2: Templated supported claim

- Claim: "nuPlan-R adds Success Rate and All-Core Pass Rate metrics to assess planner robustness and performance balance over multiple evaluation dimensions."
- Tree A: `supported` (faithful paraphrase).
- Tree B:
  - Step B1: Noticeably formulaic. Go to Step B2.
  - Step B2c: "over multiple evaluation dimensions" is a stock phrase. Yes, template-like.
  - Decision: score 3, `claim_realism_issue = too_template_like`. `claim_usable_for_paper_example = no`.
  - Rationale: "Phrase 'over multiple evaluation dimensions' is a stock template filler; claim reads as a generated paraphrase."

### Example B3: Extreme overclaim

- Claim: "The method completely solves the problem and is deployment-ready with 100% reliability."
- Tree A: `strong_action_overclaim`.
- Tree B:
  - Step B1: Unrealistic. Go to Step B2.
  - Step B2a: "completely solves", "deployment-ready", "100% reliability" — all extreme.
  - Decision: score 1, `claim_realism_issue = too_extreme`. `claim_usable_for_paper_example = no`.
  - Rationale: "Extreme words 'completely solves', 'deployment-ready', '100% reliability' — no scientist writes this."

### Example B4: Mechanical contradiction

- Claim: "The method achieves 30% accuracy on the test set." (evidence says 78.4%)
- Tree A: `contradiction_candidate`.
- Tree B:
  - Step B1: Noticeably mechanical. Go to Step B2.
  - Step B2e: Pure number swap, no other modification.
  - Decision: score 2, `claim_realism_issue = contradiction_too_mechanical`. `claim_usable_for_paper_example = no`.
  - Rationale: "Pure number swap (78.4% → 30%) with no realistic misreading pattern; reads as a mechanical edit."

### Example B5: Forced strong_action

- Claim: "We extend the benchmark with Success Rate and All-Core Pass Rate to assess robustness for safety-critical deployment in autonomous driving."
- Tree A: `strong_action_overclaim` (evidence only mentions metric extension, no deployment).
- Tree B:
  - Step B1: The "for safety-critical deployment in autonomous driving" feels tacked on.
  - Step B2f: Strong cues ("safety-critical deployment") appear but the claim's subject is metric extension. Forced.
  - Decision: score 2, `claim_realism_issue = strong_action_too_forced`. `claim_usable_for_paper_example = no`.
  - Rationale: "'safety-critical deployment' is stuffed into a metric-extension sentence; no natural motivation."

---

## Summary table: Tree B issue → score range

| Issue | Typical score range | Description |
| --- | --- | --- |
| `none` | 4-5 | Natural scientific writing. |
| `too_extreme` | 1-2 | Extreme words no scientist would write. |
| `not_scientific_claim` | 1-2 | Slogan / marketing / policy recommendation. |
| `too_template_like` | 2-3 | Fill-in-the-blank template feel. |
| `unnatural_wording` | 2-3 | Grammatical but awkward. |
| `contradiction_too_mechanical` | 2-3 | Pure negation/number-swap. |
| `strong_action_too_forced` | 2-3 | Action language stuffed in. |
| `mild_strong_boundary_unclear` | 3 | Cue-word-only difference. |
| `ambiguous_or_vague` | 2-3 | Too vague to evaluate. |

**Note:** These are guidelines, not strict rules. A claim with `too_extreme` could score 1 (if multiple extreme words) or 2 (if one extreme word). Use your judgment.
