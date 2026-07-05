# Boundary Rules v1 — FROZEN

**Version:** 1.0 (frozen)
**Date:** 2026-07-04
**Status:** FROZEN — do not modify after annotator training begins.

This file operationalizes the six hardest boundaries in the four-class taxonomy. Each boundary has: decision rule, signal words, common mistake, example, and what the annotator should write in `rationale_one_sentence`.

---

## Boundary 1: `supported` vs `mild_scope_overclaim`

### Decision rule
- If the claim **adds a scope/precision detail not in evidence** (e.g., "as the main comparison basis," "multi-stage," "across domains," "and five starting conditions") **without** asserting action/deployment/safety consequences → `mild_scope_overclaim`.
- If the claim **matches the evidence's scope and strength** (paraphrasing allowed, no added scope details) → `supported`.

### Signal words suggesting mild (scope expansion)
- "as the main comparison basis"
- "multi-stage," "multi-domain," "cross-domain"
- "and five starting conditions," "and environment configurations"
- "comprehensive," "broad" (when applied to scope, not action)
- "during evaluation," "for the reported comparison" (when these framings are not in evidence)

### Common mistake
Annotators often over-label modest paraphrases as `mild_scope_overclaim`. A paraphrase that preserves scope and strength is `supported`, not `mild`. Only label `mild` when the claim **adds** a scope/precision detail the evidence does not support.

### Example
- **supported:** Evidence "We evaluate six frontier AI systems under matched prompts and budgets." → Claim "The study evaluates six frontier AI systems under matched prompts and budgets." (paraphrase, no scope added)
- **mild:** Evidence "We extend the benchmark with Success Rate and All-Core Pass Rate to assess robustness and performance balance across multiple dimensions." → Claim "The benchmark adds Success Rate and All-Core Pass Rate to assess robustness and performance balance **as the main comparison basis**." (scope detail "as the main comparison basis" added)

### What to write in `rationale_one_sentence`
- For supported: "Evidence directly supports the claim as stated including its strength; no over-extension of scope or action."
- For mild: "Claim adds [specific scope detail] not in evidence; scope/precision over-extension without action/deployment/safety conclusion."

---

## Boundary 2: `mild_scope_overclaim` vs `strong_action_overclaim`

**This is the hardest boundary in the taxonomy.** 12/25 questionable/unclear cases in the author sanity audit were mild-vs-strong confusions.

### Decision rule
- If the claim asserts an **action/deployment/safety/guarantee/operational/policy/generalization conclusion** that the evidence cannot justify → `strong_action_overclaim`.
- If the claim **only expands scope/breadth/precision** without action/deployment/safety consequences → `mild_scope_overclaim`.

### Signal words suggesting strong (action/deployment/safety)
- **Deployment:** deploy, deployment, production, real-world, operational, physical plant trials
- **Safety:** safety, guarantee, ensure, certify, reliable, reliability
- **Policy:** policy, recommend, should, must, need to
- **Generalization:** generaliz, cross-domain, broad, universal, scalable
- **Strength:** outperforms, dominates, superior, state-of-the-art, robust, comprehensive, mature
- **Theoretical:** theoretically justified, provably, proves
- **Action:** achieves, enables, allows, permits, supports the use of, can be used, suitable for, ready for, validates (in operational sense)

### Signal words suggesting mild (scope only)
- "as the main comparison basis," "multi-stage," "across domains"
- "and five starting conditions," "and environment configurations"
- scope/breadth/precision adjectives without action consequences

### Common mistake
Annotators often misclassify claims that **describe what the paper does** ("presents," "evaluates," "reports") without explicit action language. If the claim only describes methodology without asserting action/deployment consequences, it is more likely `mild` or `supported`. However, if the claim frames the methodology as a *contribution that enables* something beyond what the evidence supports, it may still be `strong_action_overclaim`.

### Example
- **mild:** Evidence "tested on unseen tasks in simulation" → Claim "tested on unseen **multi-stage** tasks during evaluation" (scope adjective added, no action conclusion)
- **strong:** Evidence "outperforms existing methods in numerical experiments" → Claim "outperforms existing methods in numerical experiments and **direct physical plant trials**" (operational deployment escalation)

### What to write in `rationale_one_sentence`
- For mild: "Claim adds [scope detail] not in evidence; scope/precision over-extension without action/deployment/safety conclusion."
- For strong: "Evidence limited to [local/experimental scope]; claim asserts [action/deployment/safety conclusion] — action/strength escalation beyond evidence scope."

### If unsure
Mark `confusion_if_any = mild_vs_strong` and pick the label you lean toward. This is more informative than `unsure`.

---

## Boundary 3: `strong_action_overclaim` vs `contradiction_candidate`

### Decision rule
- If the claim and evidence point in **opposite directions** on the same metric, number, entity, or conclusion (including detail-swapping) → `contradiction_candidate`.
- If the claim's direction is **consistent** with evidence but its **strength** (action/deployment/safety assertion) exceeds what the evidence warrants → `strong_action_overclaim`.

### Signal words suggesting contradiction (directional conflict)
- Different number for the same metric (e.g., evidence "24.5%", claim "above 30%")
- Different entity name (e.g., evidence "IPPO and PQN", claim "PPO-RNN and SAC")
- Different metric name (e.g., evidence "Success Rate", claim "Lane Distance")
- Opposite trend (e.g., evidence "does not saturate", claim "saturates")
- Opposite conclusion (e.g., evidence "uncertain", claim "clear")

### Signal words suggesting strong (strength escalation, no directional conflict)
- "outperforms" (when evidence also says outperforms, but claim adds broader scope)
- "ready for," "suitable for," "can be used" (when evidence is local/experimental)
- "theoretically justified," "provably" (when evidence is empirical only)
- "direct physical plant trials" (when evidence is numerical only)

### Common mistake
Annotators often misclassify **number inflation** (e.g., 90% → 95%) as `strong_action_overclaim`. Number inflation on the same metric is `contradiction_candidate` (factual mismatch), not `strong_action_overclaim` (strength escalation). The distinction: if the **number itself** is wrong, it is contradiction; if the **strength framing** around the number is excessive but the number matches, it is strong_action.

### Example
- **strong:** Evidence "outperforms existing methods in numerical experiments" → Claim "outperforms existing methods in numerical experiments and direct physical plant trials" (direction aligns, strength excessive)
- **contradiction:** Evidence "accuracy is 24.5%" → Claim "accuracy is above 30%" (number conflict on the same metric)

### What to write in `rationale_one_sentence`
- For strong: "Direction consistent with evidence but strength excessive; evidence limited to [scope], claim asserts [stronger conclusion]."
- For contradiction: "Directional conflict on [same metric/number/entity]; evidence says [X], claim says [Y] — [opposite/inflated/swapped]."

---

## Boundary 4: `contradiction_candidate` vs `mild_scope_overclaim`

### Decision rule
- If the claim **swaps** a specific detail (number, entity name, metric name) relative to evidence on the same topic → `contradiction_candidate`.
- If the claim **adds** a scope/precision detail without conflicting with evidence → `mild_scope_overclaim`.

### Signal words suggesting contradiction (detail-swap)
- Number swap: evidence "2,000 episodes" → claim "20,000 episodes"
- Entity swap: evidence "IPPO and PQN" → claim "PPO-RNN and SAC"
- Metric swap: evidence "Success Rate" → claim "Lane Distance"
- Trend swap: evidence "does not saturate" → claim "saturates"

### Signal words suggesting mild (scope addition, no swap)
- "as the main comparison basis" (added framing, no swap)
- "multi-stage" (added adjective, no swap)
- "and five starting conditions" (added detail, no swap)

### Common mistake
Annotators often treat detail-swaps as `mild_scope_overclaim` because no explicit "however" / "but" language is present. Detail-swapping IS contradiction, even without contradiction cue words.

### Example
- **mild:** Evidence "tested on unseen tasks" → Claim "tested on unseen **multi-stage** tasks" (scope adjective added, no swap)
- **contradiction:** Evidence "Success Rate and All-Core Pass Rate" → Claim "Lane Distance and Map Coverage Rate" (metric names swapped on the same topic)

### What to write in `rationale_one_sentence`
- For mild: "Claim adds [scope detail] not in evidence; no directional conflict, no detail-swap."
- For contradiction: "Claim swaps [specific detail] relative to evidence on the same topic; detail-swap is contradiction."

---

## Boundary 5: Evidence Too Short / Context Missing

### Decision rule
- If the evidence excerpt is **too short** (e.g., under ~15 words) or **truncated mid-sentence**, such that you genuinely cannot tell whether the claim over-extends the evidence → `unsure` with `confusion_if_any = evidence_insufficient_context`.
- If the evidence is short but **still sufficient** to judge the claim → use the normal decision tree (Steps 1-4).

### Signal words suggesting evidence-insufficient-context
- Evidence is under 15 words
- Evidence ends mid-sentence (e.g., "calibrating agent behaviors, inte-")
- Evidence lacks the specific detail the claim references (e.g., claim says "and environment configurations" but evidence only says "matched prompts and budgets" — could be implied, could be added)

### Common mistake
Annotators often **force a label** on short-evidence cases. If the evidence excerpt is genuinely too short to tell whether the claim over-extends, `unsure` with `evidence_insufficient_context` is the correct response. Forcing a label produces noise.

### Example
- **Evidence (11 words):** "We evaluate six frontier AI systems under matched prompts and budgets."
- **Claim:** "The study evaluates six frontier AI systems under matched prompts, budgets, **and environment configurations** for the reported cyber-range comparison."
- **Issue:** The claim adds "and environment configurations" and "for the reported cyber-range comparison" — the evidence is too short to tell whether these are implied by the full paper or are scope additions. → `unsure` with `evidence_insufficient_context`, OR lean `mild_scope_overclaim` with `confusion_if_any = supported_vs_mild`.

### What to write in `rationale_one_sentence`
- "Evidence excerpt is too short/truncated to judge whether claim over-extends; specifically, [what is missing]."

---

## Boundary 6: When to Use `unsure`

### Decision rule
Use `unsure` **only** when:
1. You have applied the decision tree (Steps 1-5) and still cannot decide, OR
2. The evidence is too short/truncated to judge (Boundary 5), OR
3. The case sits on a genuine boundary between two adjacent classes and you cannot pick a leaning label.

**Do NOT use `unsure` as a default for hard cases.** If you can narrow it to two adjacent classes, **pick the one you lean toward** and note the confusion in `confusion_if_any` — this is more informative than `unsure`.

### When `unsure` is appropriate
- Evidence is truncated mid-sentence and the missing context is needed to judge
- The case is on a genuine mild/strong boundary and you have no leaning
- The case is on a genuine strong/contradiction boundary and you have no leaning

### When `unsure` is NOT appropriate
- You are tired and want to skip a hard case → take a break instead
- You think the label might be wrong → pick your best guess with a confusion note
- You want to defer to the adjudicator → pick your best guess with `needs_adjudication = yes`

### What to write in `rationale_one_sentence` when `unsure`
- "Cannot decide between [class A] and [class B] because [specific reason]; the case sits on a genuine boundary."
- "Evidence excerpt is too short to judge whether [specific claim detail] is supported or added."

### What to write in `confusion_if_any` when `unsure`
- `supported_vs_mild` (if confused between these two)
- `mild_vs_strong` (if confused between these two)
- `strong_vs_contradiction` (if confused between these two)
- `evidence_insufficient_context` (if evidence is too short/truncated)
- `other` (if confused between non-adjacent classes, e.g., supported vs contradiction — this is unusual and may indicate the case needs re-reading)
