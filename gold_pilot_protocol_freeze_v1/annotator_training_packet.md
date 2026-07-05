# Annotator Training Packet — Gold Pilot v1

**Version:** 1.0
**Date:** 2026-07-04
**Audience:** Two independent annotators (Annotator A and Annotator B). No prior project knowledge required.

---

## 1. Welcome

You are about to participate in a **gold pilot annotation study** for a research project on evidence sufficiency calibration for scientific claims. Your labels will help establish whether the project's four-class taxonomy can be reliably applied by independent human annotators.

This packet is designed to be self-contained. You do not need prior knowledge of the project, the domain, or the papers involved. Everything you need is in this packet and the files it references.

---

## 2. Task Purpose

You will read **50 pairs** of (claim, evidence). For each pair, you will judge whether the evidence is **sufficient for the strength of the claim as written**.

This is **not** a fact-checking task. You are not judging whether the claim is true in an absolute sense. You are judging whether the **evidence provided** is **sufficient for the strength of the claim as stated**.

There are **four labels** plus an `unsure` option:

| Label | Plain-English meaning |
|---|---|
| `supported` | The evidence is enough for what the claim says. The claim does not over-reach. |
| `mild_scope_overclaim` | The claim slightly over-reaches on scope (e.g., single dataset framed as multi-dataset), but does not assert action/deployment/safety conclusions. |
| `strong_action_overclaim` | The claim asserts an action/deployment/safety/generalization conclusion that the evidence does not justify. The claim may point the same direction as the evidence, but it is too strong. |
| `contradiction_candidate` | The evidence contradicts the claim. They point in opposite directions on the same number, name, metric, or conclusion. Includes detail-swapping (changing specific numbers/names/metrics). |
| `unsure` | You genuinely cannot decide after careful reading. |

---

## 3. What You Must NOT Do

1. **Do not look at silver labels.** You are not given them. Do not seek them out. Your job is to provide **independent** labels.
2. **Do not look at the paper.** Do not search for the claim online. Do not use external knowledge. Judge only based on the evidence span provided.
3. **Do not use AI models or tools.** No ChatGPT, no Claude, no LLMs. Your judgment must be your own.
4. **Do not collaborate with the other annotator.** You work independently. No discussing cases, no sharing labels, no comparing notes. Adjudication happens after both submit.
5. **Do not guess author intent.** Judge the (claim, evidence) pair **as written**, not what you think the author "meant to say."
6. **Do not skip the rationale.** Every pair must have a one-sentence rationale explaining your labeling decision.
7. **Do not treat any existing label as ground truth.** The project has AI-preannotated "silver" labels, but they are NOT gold. Your independent labels may disagree — that is the point of this pilot.

---

## 4. What You Must Do

For each of the 50 pairs:

1. **Read the evidence span carefully.**
2. **Read the claim carefully.**
3. **Apply the decision tree** (in `annotation_decision_tree_v1.md`) — Steps 1 → 2 → 3 → 4 → 5 → 6, in order. Stop at the first step that yields a label.
4. **Assign a label** (`supported`, `mild_scope_overclaim`, `strong_action_overclaim`, `contradiction_candidate`, or `unsure`).
5. **Write a one-sentence rationale** in the `rationale_one_sentence` field. Explain **why** you chose this label, not just what label you chose.
6. **Note any confusion** in `confusion_if_any` (e.g., `mild_vs_strong` if you were torn between mild and strong).
7. **Mark `needs_adjudication`** as `yes` if you marked `unsure` or if you are uneasy with your label.
8. **Move to the next pair.**

---

## 5. How to Use the Decision Tree

The decision tree has 6 steps. Apply them in order:

1. **Directional conflict?** Does the claim cite a different number/name/metric than the evidence, or assert the opposite trend? → If yes: `contradiction_candidate`.
2. **Action/deployment/safety cue?** Does the claim use words like deploy, safety, guarantee, operational, outperforms, ready for, theoretically justified? → If yes: go to Step 3. If no: go to Step 4.
3. **Evidence sufficient for action strength?** Is the evidence local/experimental/simulated while the claim asserts deployment/safety/generalization? → If yes: `strong_action_overclaim`.
4. **Scope over-extension?** Does the claim expand scope (single → multi, adds details not in evidence) without action consequences? → If yes: `mild_scope_overclaim`. If no: go to Step 5.
5. **Evidence too short?** Is the evidence excerpt under ~15 words or truncated, such that you cannot tell? → If yes: `unsure` with `evidence_insufficient_context`.
6. **Still cannot decide?** → `unsure` (last resort; pick a leaning label with a confusion note if possible).

Full details and examples: `annotation_decision_tree_v1.md`.

---

## 6. The Hardest Boundaries

Two boundaries are genuinely hard. If you are stuck on them, you are not alone — the project's author sanity audit found these to be the most confusing boundaries:

### mild vs strong (hardest)
- **mild:** scope/breadth/precision expansion, no action/deployment/safety conclusion.
- **strong:** action/deployment/safety/operational conclusion that evidence cannot justify.
- **Key question:** Does the claim assert an **action/deployment/safety** conclusion, or merely expand **scope/breadth**? If action → strong. If scope only → mild.
- **If unsure:** pick the one you lean toward, mark `confusion_if_any = mild_vs_strong`.

### strong vs contradiction (second hardest)
- **strong:** direction aligns with evidence, but strength is excessive.
- **contradiction:** direction conflicts on the same number/name/metric/conclusion.
- **Key question:** Is there a **directional conflict** on the same specific thing, or is the claim just **too strong** while pointing the same way? If directional conflict → contradiction. If strength only → strong.
- **Number inflation (90% → 95%)** is contradiction (factual mismatch), not strong (strength escalation).
- **If unsure:** pick the one you lean toward, mark `confusion_if_any = strong_vs_contradiction`.

---

## 7. Examples (from `label_positive_negative_examples.csv`)

Read `label_positive_negative_examples.csv` for 20 worked examples (3 positive + 2 negative/near-miss per class). All examples are from real candidates in the project's dataset.

**Quick illustration:**

- **supported:** Evidence "We evaluate six frontier AI systems under matched prompts and budgets." → Claim "The study evaluates six frontier AI systems under matched prompts and budgets." (paraphrase, no over-reach)

- **mild:** Evidence "...to assess robustness and performance balance across multiple dimensions." → Claim "...to assess robustness and performance balance **as the main comparison basis**." (scope detail added)

- **strong:** Evidence "outperforms existing methods in numerical experiments" → Claim "outperforms existing methods in numerical experiments and **direct physical plant trials**" (operational escalation)

- **contradiction:** Evidence "effectiveness remains uncertain" → Claim "effectiveness is **clear**" (directional flip on the same finding)

---

## 8. Time and Pace

- **Estimated time:** 50 pairs × ~5 minutes/pair = ~4 hours total.
- **Recommended pace:** Work in sessions of 1-2 hours (10-25 pairs), then take a break. Fatigue leads to low-quality labels.
- **No time limit:** There is no deadline pressure. Quality matters more than speed.
- **You can spread it over multiple days** if needed. Just do not discuss cases with anyone (especially not the other annotator) between sessions.

---

## 9. Submission

1. You will receive a CSV file: `pilot_50_blind_annotation_A.csv` (or `_B.csv` for Annotator B).
2. Fill in the 5 empty columns for each row: `annotator_label`, `confidence_1_to_5`, `rationale_one_sentence`, `confusion_if_any`, `needs_adjudication`.
3. Do **not** modify the first 5 columns (`pilot_id`, `candidate_id`, `domain`, `evidence_text`, `claim_text`).
4. Do **not** add or delete rows.
5. Save the file as `pilot_50_blind_annotation_A_filled.csv` (or `_B_filled.csv`).
6. Submit the filled CSV to the adjudicator.

---

## 10. What Happens After Submission

After both annotators submit, an adjudicator (who is NOT one of the two annotators) will:
1. Compare your labels with the other annotator's labels.
2. For pairs where you agree: confirm the label (or override if both are wrong).
3. For pairs where you disagree: read both rationales, read the evidence and claim, and assign an `adjudicated_label`.
4. The adjudicator's labels become the **gold pilot labels** used for agreement statistics (Cohen's kappa, per-boundary agreement, etc.).

You will **not** see the other annotator's labels or the adjudicated labels during annotation. You may see aggregate statistics (e.g., overall agreement rate) after the pilot is complete, but not per-pair results.

---

## 11. Contact

If you have questions about the task, the decision tree, or the examples, contact:

- **Contact person:** [PLACEHOLDER — to be filled by project lead]
- **Email:** [PLACEHOLDER]
- **Response time:** [PLACEHOLDER]

Do **not** contact the other annotator. Do **not** discuss specific cases with anyone except the contact person above, and only about clarifying the task instructions (not about specific labels for specific pairs).

---

## 12. Quick Checklist Before You Start

- [ ] I have read this training packet.
- [ ] I have read `annotation_guideline_v1_frozen.md`.
- [ ] I have read `annotation_decision_tree_v1.md`.
- [ ] I have read `boundary_rules_v1.md`.
- [ ] I have read `label_positive_negative_examples.csv` (20 worked examples).
- [ ] I understand I must NOT look at silver labels, the paper, or use AI tools.
- [ ] I understand I must NOT collaborate with the other annotator.
- [ ] I understand every pair needs a one-sentence rationale.
- [ ] I understand `unsure` is allowed but should be explained.
- [ ] I have the CSV file (`pilot_50_blind_annotation_A.csv` or `_B.csv`).
- [ ] I know the submission format (fill 5 columns, save as `_filled.csv`).

When all boxes are checked, you are ready to begin. Good luck, and thank you for contributing to this pilot.
