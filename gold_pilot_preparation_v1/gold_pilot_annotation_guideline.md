# Gold Pilot Annotation Guideline — CESE-OCN Evidence Sufficiency Calibration

**Version:** 1.0
**Date:** 2026-07-04
**Purpose:** Independent two-annotator gold pilot for evidence sufficiency calibration. This guideline describes how to assign one of five labels to a (claim, evidence) pair.

---

## 1. Task definition

You will be given a **claim** and an **evidence span** from a scientific paper. Your task is to judge whether the evidence is **sufficient for the strength of the claim** — not just whether the evidence is topically relevant, but whether it justifies the claim as stated, including its scope, action framing, deployment implications, safety conclusions, and generalization breadth.

This is **not** a fact-checking task. You are not judging whether the claim is true in an absolute sense. You are judging whether the *evidence provided* is *sufficient for the strength of the claim as written*.

## 2. The five labels

| Label | Meaning |
|---|---|
| `supported` | The evidence supports the claim as stated, including its strength. The claim does not over-extend the evidence. |
| `mild_scope_overclaim` | The claim mildly over-extends the scope of the evidence (e.g., single-dataset result framed as multi-dataset, single-domain as multi-domain), but no action/deployment/safety conclusion is asserted. |
| `strong_action_overclaim` | The claim asserts an action, deployment, safety, policy, generalization, guarantee, or operational conclusion that the evidence does not justify. The claim may be directionally consistent with the evidence, but its *strength* is excessive. |
| `contradiction_candidate` | The evidence contradicts the claim. The claim and evidence point in opposite directions on the same metric, number, entity, or conclusion (including detail-swapping of numbers, names, or metrics). |
| `unsure` | You genuinely cannot decide. Use this only when you have read the evidence and claim carefully and still cannot place the pair in one of the four classes. |

**`unsure` is allowed** but will be analyzed separately. Do not force a label if you are genuinely uncertain. However, if you can narrow it to two adjacent classes (e.g., "mild or strong"), pick the one you lean toward and note the confusion in the `confusion_if_any` field.

## 3. Decision tree

Use this four-step decision tree. Steps are applied in order.

```
                       +---------------------------+
                       |   Claim-Evidence Pair     |
                       +-------------+-------------+
                                     |
                                     v
              +----------------------------------------+
              | Step 1: Directional Conflict?         |
              | Does the claim point OPPOSITE to      |
              | evidence on the same metric, number,  |
              | entity, or conclusion?                |
              | (includes detail-swapping of numbers, |
              | names, metrics, entities)             |
              +-----------------+---------------------+
                          YES   |   NO
                +---------------+   +---------------+
                v                               v
        +----------------+        +-----------------------------+
        | contradiction_ |        | Step 2: Action/Deployment/  |
        | candidate      |        | Safety/Operational Cue?     |
        +----------------+        | (deploy, safety, guarantee, |
                                  | operational, policy, broad   |
                                  | generalization, outperforms, |
                                  | suitable for, theoretically  |
                                  | justified, etc.)             |
                                  +--------------+--------------+
                                          YES    |    NO
                                  +--------------+   +--------------+
                                  v                              v
                       +-------------------------+   +-----------------------+
                       | Step 3: Evidence        |   | Step 4: Scope         |
                       | Sufficient for Action   |   | Over-Extension?       |
                       | Strength?               |   | Does the claim expand |
                       | Is evidence limited to  |   | scope/domain/         |
                       | single benchmark /      |   | population/condition/ |
                       | simulation / lab /      |   | temporal range beyond |
                       | limited metric / single |   | evidence, WITHOUT     |
                       | domain, while claim     |   | action consequences?  |
                       | asserts stronger        |   +-------+---------------+
                       | action conclusion?      |    YES    |    NO
                       +-----------+-------------+   +--------+   +--------+
                              YES   |   NO            v           v
                       +------------+   +----------+ +--------+ +--------+
                       v                v          | mild_   | |        |
                +--------------+  +------------+    | scope_  | | sup-   |
                | strong_      |  | Re-examine |    | over-   | | ported |
                | action_      |  | as sup.    |    | claim   | |        |
                | overclaim    |  | or mild    |    +---------+ +--------+
                +--------------+  +------------+
```

### Step 1: Directional conflict?

Check whether the claim and evidence point in **opposite directions** on the same metric, number, entity, or conclusion. This includes:
- Evidence says "24.5% accuracy" and claim says "above 30% accuracy" (number swap on the same metric).
- Evidence says "IPPO and PQN" and claim says "PPO-RNN and SAC" (entity name swap).
- Evidence says "uncertain" and claim says "clear" (directional flip on the same finding).
- Evidence says "lack of training set" and claim says "training data already available" (factual contradiction on the same fact).

If YES → `contradiction_candidate`. If NO → go to Step 2.

### Step 2: Action/Deployment/Safety/Operational cue?

Check whether the claim asserts an **action, deployment, safety, policy, generalization, guarantee, or operational conclusion**. Cue words include: deploy, deployment, safety, guarantee, operational, policy, broad generalization, outperforms, suitable for, theoretically justified, ready for, ready to, can be used to, enables, ensures, demonstrates, proves (in an operational/deployment sense).

If the claim is only about a *finding* (e.g., "the method achieves 83% success rate") without an action/deployment/safety conclusion → go to Step 4.
If the claim asserts an action/deployment/safety/operational conclusion → go to Step 3.

### Step 3: Evidence sufficient for action strength?

Check whether the evidence is **sufficient for the strength of the action conclusion**. If the evidence is limited to:
- a single benchmark / simulation / lab experiment, while the claim asserts deployment readiness or broad generalization;
- a controlled setting, while the claim asserts safety or operational conclusions;
- a specific metric, while the claim asserts "outperforms" or "ready for" broader use;

then the evidence is **not sufficient** for the action strength → `strong_action_overclaim`.

If the evidence does support the action conclusion as stated → re-examine as `supported` or `mild_scope_overclaim` (depending on Step 4).

### Step 4: Scope over-extension?

Check whether the claim **expands the scope** (domain, population, condition, temporal range, dataset breadth) beyond the evidence, **without** action/deployment/safety consequences. Examples:
- Evidence: "tested on Domain A." Claim: "generalizes across domains." (scope expansion without action conclusion)
- Evidence: "single dataset." Claim: "multi-dataset result." (scope expansion without action conclusion)

If YES → `mild_scope_overclaim`. If NO → `supported`.

## 4. Boundary rules

### supported vs mild_scope_overclaim

- `supported`: the claim matches the evidence's scope and strength. No over-extension.
- `mild_scope_overclaim`: the claim adds a scope/precision detail not in evidence (e.g., "as the main comparison basis," "multi-stage," "across domains") but no action/deployment/safety conclusion.

**Key question:** Does the claim add a scope/precision detail the evidence does not support, without asserting an action conclusion? If yes → mild. If no → supported.

### mild_scope_overclaim vs strong_action_overclaim

- `mild_scope_overclaim`: scope over-extension only. No action/deployment/safety/operational cue.
- `strong_action_overclaim`: the claim asserts an action/deployment/safety/operational conclusion the evidence does not justify.

**Key question:** Does the claim assert an action/deployment/safety/operational conclusion (deploy, guarantee, safety, ready for, outperforms, operational, etc.)? If yes → check if evidence supports that action strength (Step 3). If no → mild.

This is the **hardest boundary**. If you are genuinely unsure whether a phrase counts as an "action cue," mark `confusion_if_any = mild_vs_strong` and pick the label you lean toward.

### strong_action_overclaim vs contradiction_candidate

- `strong_action_overclaim`: the evidence may align with the claim's direction, but the claim's *strength* (action/deployment/safety assertion) exceeds what the evidence warrants. No directional conflict.
- `contradiction_candidate`: the evidence points in the *opposite direction* on the same metric/number/entity/conclusion. The claim is not just too strong — it conflicts.

**Key question:** Is there a directional conflict on the same metric/number/entity/fact? If yes → contradiction. If no (direction aligns, only strength is excessive) → strong_action.

## 5. What to do when unsure

If you have read the evidence and claim carefully and still cannot decide:
1. Mark `annotator_label = unsure`.
2. In `rationale_one_sentence`, explain what makes the case hard (e.g., "Evidence mentions numerical experiments but claim adds 'physical plant trials' — unclear if this is escalation or contradiction").
3. In `confusion_if_any`, note which two classes you are choosing between.
4. In `needs_adjudication`, mark `yes`.

**Do not force a label.** `unsure` is a valid answer and will be analyzed separately. However, if you can narrow it to two adjacent classes, pick the one you lean toward and note the confusion — this is more informative than `unsure`.

## 6. What annotators must NOT do

1. **Do not reference model predictions.** You are not given model predictions, and you must not seek them out. The task is to judge evidence-claim sufficiency from the text alone.
2. **Do not reference silver labels.** You are not given silver labels, and you must not seek them out. The task is to provide independent labels.
3. **Do not guess author intent.** Judge the (claim, evidence) pair as written, not what you think the author "meant to say."
4. **Do not use external knowledge.** Judge only based on the evidence span provided. Do not look up the paper, do not search for the claim online, do not use your knowledge of the domain.
5. **Do not collaborate with the other annotator.** Each annotator works independently. Adjudication happens after both annotators submit.
6. **Do not skip the rationale.** Every pair must have a one-sentence rationale explaining your labeling decision.

## 7. Required fields (per pair)

For each (claim, evidence) pair, you must fill:

| Field | Description |
|---|---|
| `annotator_label` | One of: `supported`, `mild_scope_overclaim`, `strong_action_overclaim`, `contradiction_candidate`, `unsure`. |
| `confidence_1_to_5` | 1 = very uncertain, 5 = very confident. |
| `rationale_one_sentence` | One sentence explaining why you chose this label. |
| `confusion_if_any` | One of: `none`, `supported_vs_mild`, `mild_vs_strong`, `strong_vs_contradiction`, `evidence_insufficient_context`, `other`. If you are confused between two classes, name them here. |
| `needs_adjudication` | `yes` or `no`. Mark `yes` if you think this case needs a third-party adjudicator (e.g., you marked `unsure`, or you are uneasy with your label). |

## 8. Examples (illustrative, not from the pilot set)

**Example A — supported:**
- Evidence: "We evaluate six frontier AI systems under matched prompts and budgets."
- Claim: "The study evaluates six frontier AI systems under matched prompts and budgets."
- Label: `supported`. Rationale: "Evidence directly supports the claim as stated, including its scope and strength; no over-extension."

**Example B — mild_scope_overclaim:**
- Evidence: "We extend the benchmark with Success Rate and All-Core Pass Rate to assess robustness and performance balance across multiple dimensions."
- Claim: "The benchmark adds Success Rate and All-Core Pass Rate to assess robustness and performance balance as the main comparison basis."
- Label: `mild_scope_overclaim`. Rationale: "Claim adds 'as the main comparison basis' framing not in evidence; scope/precision over-extension without action conclusion."

**Example C — strong_action_overclaim:**
- Evidence: "This approach outperforms existing methods in extensive numerical experiments based on the biopharmaceutical manufacturing domain."
- Claim: "The approach outperforms existing methods in numerical biopharmaceutical experiments and direct physical plant trials."
- Label: `strong_action_overclaim`. Rationale: "Evidence mentions numerical experiments only; claim asserts 'direct physical plant trials' — operational/deployment escalation beyond evidence scope."

**Example D — contradiction_candidate:**
- Evidence: "The effectiveness remains uncertain because calibration, data integration, and interpretation require expertise."
- Claim: "The effectiveness is clear because calibration, data integration, and interpretation require little expertise."
- Label: `contradiction_candidate`. Rationale: "Claim says effectiveness is 'clear' and requires 'little expertise'; evidence says 'uncertain' and requires 'expertise' — directional conflict on the same finding."

## 9. Workflow

1. Read the evidence span carefully.
2. Read the claim carefully.
3. Apply the decision tree (Steps 1 → 2 → 3 → 4).
4. Assign a label.
5. Write a one-sentence rationale.
6. Note any confusion in `confusion_if_any`.
7. Mark `needs_adjudication` if you are unsure.
8. Move to the next pair.

Work at your own pace. There is no time limit. If you are tired, take a break — fatigue leads to low-quality labels.

## 10. After annotation

After both annotators submit, an adjudicator will:
1. Compare annotator A and annotator B labels.
2. For pairs where A and B agree: confirm the label (or override if both are wrong).
3. For pairs where A and B disagree: read both rationales, read the evidence and claim, and assign an `adjudicated_label`.
4. Mark `final_use_recommendation` for each pair (usable_for_gold_eval / boundary_case_only / exclude_due_to_unclear_evidence / taxonomy_revision_needed).

The adjudicator's labels will be used as the gold pilot labels for inter-annotator agreement statistics. **The adjudicator must not be one of the two annotators.**
