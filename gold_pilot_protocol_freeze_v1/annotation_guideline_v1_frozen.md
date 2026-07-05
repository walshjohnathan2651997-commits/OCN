# Annotation Guideline v1 — FROZEN

**Version:** 1.0 (frozen)
**Date:** 2026-07-04
**Status:** FROZEN — do not modify after annotator training begins. Any change requires a new version (v2) and re-training.
**Scope:** Gold pilot, 50 (claim, evidence) pairs, two independent annotators + one adjudicator.

---

## 0. Task in One Sentence

You will read a **claim** and an **evidence span** from a scientific paper, and judge whether the evidence is **sufficient for the strength of the claim as written** — not whether the claim is absolutely true, and not whether the evidence is topically relevant.

This is an **evidence-sufficiency** task, not a fact-checking task.

---

## 1. The Five Labels

### 1.1 `supported`

- **Definition:** The evidence is sufficient for the claim's stated strength (scope, action framing, deployment implications, etc.). The claim does not over-extend the evidence.
- **When to use:** The claim matches the evidence's scope and strength. Numbers, entities, metrics, and direction all align. The claim may paraphrase the evidence but does not add unsupported details.
- **When NOT to use:** The claim adds scope/precision details not in evidence (→ mild), asserts action/deployment/safety conclusions beyond evidence (→ strong), or conflicts directionally with evidence (→ contradiction).
- **Common confusion:** Annotators often over-label modest paraphrases as `mild_scope_overclaim`. A paraphrase that preserves scope and strength is `supported`, not `mild`. `supported` does **not** mean "absolutely true" — it means "evidence is sufficient for the claim as stated."
- **Short example:**
  - Evidence: "We evaluate six frontier AI systems under matched prompts and budgets."
  - Claim: "The study evaluates six frontier AI systems under matched prompts and budgets."
  - Label: `supported`.
- **Annotator warning:** Do not require the claim to be a verbatim copy of the evidence. Paraphrasing is allowed as long as scope and strength are preserved.

### 1.2 `mild_scope_overclaim`

- **Definition:** The claim mildly over-extends the **scope** of the evidence (single-dataset → multi-dataset, single-domain → multi-domain, adds precision details not in evidence), but asserts **no** action/deployment/safety/operational conclusion.
- **When to use:** The claim adds a scope/precision detail (e.g., "as the main comparison basis," "multi-stage," "across domains," "and five starting conditions") that the evidence does not support, AND the claim does not assert action/deployment/safety consequences.
- **When NOT to use:** If the claim asserts an action/deployment/safety/operational conclusion (→ strong). If the claim only paraphrases without adding scope (→ supported). If the claim conflicts directionally with evidence on numbers/entities/metrics (→ contradiction).
- **Common confusion:** The boundary between `mild_scope_overclaim` and `strong_action_overclaim` is the **hardest boundary** in this taxonomy. The key question: does the claim assert an **action/deployment/safety/operational** conclusion, or merely expand **scope/breadth/precision**? If action/deployment/safety → strong. If only scope/breadth → mild.
- **Short example:**
  - Evidence: "We extend the benchmark with Success Rate and All-Core Pass Rate to assess robustness and performance balance across multiple dimensions."
  - Claim: "The benchmark adds Success Rate and All-Core Pass Rate to assess robustness and performance balance **as the main comparison basis**."
  - Label: `mild_scope_overclaim` (scope/precision expansion "as the main comparison basis" not in evidence; no action conclusion).
- **Annotator warning:** If you are unsure whether a phrase counts as "scope expansion" (mild) or "action framing" (strong), mark `confusion_if_any = mild_vs_strong` and pick the label you lean toward.

### 1.3 `strong_action_overclaim`

- **Definition:** The claim asserts an **action, deployment, safety, policy, generalization, guarantee, or operational** conclusion that the evidence does not justify. The claim's direction may be consistent with the evidence, but its **strength** is excessive.
- **When to use:** The claim promotes local/experimental/simulated results into deployment readiness, safety conclusions, broad generalization, operational framing, or action recommendations that the evidence's scope cannot support.
- **When NOT to use:** If the claim only expands scope without action consequences (→ mild). If the claim conflicts directionally with evidence on the same metric/number/entity (→ contradiction). If the evidence actually supports the action conclusion as stated (→ supported).
- **Common confusion:** (a) Confusing strength escalation (strong) with scope expansion (mild) — see boundary rule §4.2. (b) Confusing strength escalation (strong) with directional conflict (contradiction) — see boundary rule §4.3. `strong_action_overclaim` does **not** require directional conflict; the claim and evidence may point the same way, just with different strengths.
- **Short example:**
  - Evidence: "This approach outperforms existing methods in extensive numerical experiments based on the biopharmaceutical manufacturing domain."
  - Claim: "The approach outperforms existing methods in numerical biopharmaceutical experiments and **direct physical plant trials**."
  - Label: `strong_action_overclaim` (evidence mentions numerical experiments only; claim asserts "direct physical plant trials" — operational deployment escalation; direction consistent but strength excessive).
- **Annotator warning:** Look for cue words: deploy, deployment, safety, guarantee, operational, policy, broad generalization, outperforms, suitable for, theoretically justified, ready for, can be used to, enables, ensures, demonstrates, proves (in operational/deployment sense). If these appear and the evidence is local/experimental, lean `strong_action_overclaim`.

### 1.4 `contradiction_candidate`

- **Definition:** The evidence **contradicts** the claim. The claim and evidence point in **opposite directions** on the same metric, number, entity, or conclusion — including **detail-swapping** of numbers, names, or metrics.
- **When to use:** The claim cites a different number than the evidence for the same metric (e.g., evidence "24.5% accuracy" vs claim "above 30% accuracy"); swaps entity names (e.g., evidence "IPPO and PQN" vs claim "PPO-RNN and SAC"); swaps metric names; or asserts the opposite trend (e.g., evidence "performance does not saturate" vs claim "performance saturates").
- **When NOT to use:** If the claim is directionally consistent with evidence but only stronger (→ strong_action_overclaim). If the claim only expands scope (→ mild_scope_overclaim). If the claim matches evidence (→ supported).
- **Common confusion:** The boundary between `strong_action_overclaim` and `contradiction_candidate` is the second-hardest boundary. The key question: is there a **directional conflict** on the same metric/number/entity/fact, or is the claim just **too strong** while pointing the same direction? Number inflation (90%→95%) is treated as `contradiction_candidate` (factual mismatch on the same metric), not `strong_action_overclaim`.
- **Short example:**
  - Evidence: "The effectiveness remains uncertain because calibration, data integration, and interpretation require expertise."
  - Claim: "The effectiveness is **clear** because calibration, data integration, and interpretation require **little expertise**."
  - Label: `contradiction_candidate` (directional conflict on the same finding: "uncertain" vs "clear", "expertise" vs "little expertise").
- **Annotator warning:** The most common contradiction pattern in this dataset is **detail-swapping** (changing specific numbers, names, or metrics), NOT explicit "however" / "but" language. If the claim cites a different number/name/metric than the evidence for the same thing, that is contradiction, even if no contradiction cue word is present.

### 1.5 `unsure`

- **Definition:** You have read the evidence and claim carefully and still cannot place the pair in one of the four classes.
- **When to use:** Only after genuine effort. You have applied the decision tree (§2) and still cannot decide.
- **When NOT to use:** As a default for hard cases. If you can narrow it to two adjacent classes (e.g., "mild or strong"), **pick the one you lean toward** and note the confusion in `confusion_if_any` — this is more informative than `unsure`.
- **Common confusion:** Annotators sometimes use `unsure` to avoid making a hard mild-vs-strong call. This is acceptable but less informative than picking a leaning label with a confusion note. Reserve `unsure` for cases where you genuinely cannot narrow it to two classes.
- **Short example:**
  - Evidence: "Performance does not saturate: coordination and total reward continue improving late in training, and total reward remains well below the maximum achievable score."
  - Claim: "Extended training shows saturated performance, with coordination and total reward reaching the maximum score by the late phase."
  - Possible label: `unsure` (could be contradiction — "does not saturate" vs "saturated"; or could be strong_action — strength escalation; the boundary is genuinely fuzzy here).
- **Annotator warning:** If you mark `unsure`, you **must** explain what makes the case hard in `rationale_one_sentence` and note which two classes you are choosing between in `confusion_if_any`. Blank `unsure` without explanation is invalid.

---

## 2. Important Principles

1. **`supported` is not absolute truth.** It means "evidence is sufficient for the claim as stated." A modest factual claim can be `supported` even if the underlying paper has limitations.
2. **`mild_scope_overclaim` is about scope/breadth/precision, not action.** No action/deployment/safety consequences asserted.
3. **`strong_action_overclaim` is about action/deployment/safety/operational strength.** Direction may align with evidence; strength is excessive.
4. **`contradiction_candidate` is about directional conflict.** Numbers, names, metrics, or conclusions point in opposite directions. Detail-swapping IS contradiction.
5. **`unsure` is allowed but must be explained.** Do not force a label, but also do not use `unsure` as a default for hard cases — pick a leaning label with a confusion note when possible.

---

## 3. What Annotators Must NOT Do

1. **Do not reference silver labels.** You are not given silver labels, and you must not seek them out. The task is to provide independent labels.
2. **Do not reference model predictions.** You are not given model predictions, and you must not seek them out.
3. **Do not reference the paper.** Do not look up the paper, do not search for the claim online, do not use external knowledge. Judge only based on the evidence span provided.
4. **Do not guess author intent.** Judge the (claim, evidence) pair as written, not what you think the author "meant to say."
5. **Do not collaborate with the other annotator.** Each annotator works independently. Adjudication happens after both annotators submit.
6. **Do not skip the rationale.** Every pair must have a one-sentence rationale explaining your labeling decision.
7. **Do not treat silver labels as gold.** Silver labels are AI-preannotated and author-screened. They are NOT gold. Your independent labels may disagree with silver — that is the point of this pilot.

---

## 4. Required Fields (per pair)

| Field | Description |
|---|---|
| `annotator_label` | One of: `supported`, `mild_scope_overclaim`, `strong_action_overclaim`, `contradiction_candidate`, `unsure`. |
| `confidence_1_to_5` | 1 = very uncertain, 5 = very confident. |
| `rationale_one_sentence` | One sentence explaining why you chose this label. |
| `confusion_if_any` | One of: `none`, `supported_vs_mild`, `mild_vs_strong`, `strong_vs_contradiction`, `evidence_insufficient_context`, `other`. If confused between two classes, name them here. |
| `needs_adjudication` | `yes` or `no`. Mark `yes` if you marked `unsure`, or if you are uneasy with your label. |

---

## 5. Workflow

1. Read the evidence span carefully.
2. Read the claim carefully.
3. Apply the decision tree (§2 of `annotation_decision_tree_v1.md`) — Steps 1 → 2 → 3 → 4 → 5 → 6.
4. Assign a label.
5. Write a one-sentence rationale.
6. Note any confusion in `confusion_if_any`.
7. Mark `needs_adjudication` if you are unsure.
8. Move to the next pair.

Work at your own pace. There is no time limit. If you are tired, take a break — fatigue leads to low-quality labels.

---

## 6. After Annotation

After both annotators submit, an adjudicator (who is NOT one of the two annotators) will:
1. Compare annotator A and annotator B labels.
2. For pairs where A and B agree: confirm the label (or override if both are wrong).
3. For pairs where A and B disagree: read both rationales, read the evidence and claim, and assign an `adjudicated_label`.
4. Mark `final_use_recommendation` for each pair.

The adjudicator's labels will be used as the gold pilot labels for inter-annotator agreement statistics.

See `adjudication_protocol_v1.md` for full details.
