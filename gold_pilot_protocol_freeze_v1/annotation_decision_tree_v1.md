# Annotation Decision Tree v1 — FROZEN

**Version:** 1.0 (frozen)
**Date:** 2026-07-04
**Status:** FROZEN — do not modify after annotator training begins.

Apply the steps **in order**. Stop at the first step that yields a label.

---

## Decision Tree (6 Steps)

```
                      +---------------------------+
                      |   Claim-Evidence Pair     |
                      +-------------+-------------+
                                    |
                                    v
              +----------------------------------------+
              | Step 1: Directional Conflict?         |
              | Does the claim point OPPOSITE to      |
              | the evidence on the same metric,      |
              | number, entity, or conclusion?        |
              | (includes detail-swapping of numbers, |
              | names, metrics, entities)             |
              +-----------------+---------------------+
                         YES     |     NO
                +---------------+   +---------------+
                v                               v
        +----------------+        +-----------------------------+
        | contradiction_ |        | Step 2: Action/Deployment/  |
        | candidate      |        | Safety/Operational Cue?     |
        +----------------+        | (deploy, safety, guarantee, |
                                  | operational, policy, broad   |
                                  | generalization, outperforms, |
                                  | suitable for, theoretically  |
                                  | justified, ready for, etc.) |
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
                                                              |
                                                              v
                                              +---------------------------+
                                              | Step 5: Evidence too     |
                                              | short / context missing?  |
                                              | (evidence < ~15 words,   |
                                              | or truncated mid-sentence)|
                                              +-------------+-------------+
                                                  YES        |      NO
                                              +-------------+   +---------+
                                              v                          v
                                              +-------+              (use label
                                              | unsure|               from Step 4)
                                              +-------+
```

---

## Step-by-Step Operational Rules

### Step 1: Directional Conflict? → `contradiction_candidate`

**Question:** Does the claim point in the *opposite direction* from the evidence on the same metric, number, entity, or conclusion?

**Operational test — answer YES if ANY of these are true:**
- The claim cites a **different number** than the evidence for the same metric. (e.g., evidence: "6 systems", claim: "8 systems" or "2 systems"; evidence: "24.5% accuracy", claim: "above 30% accuracy"; evidence: "2,000 episodes", claim: "20,000 episodes")
- The claim cites a **different entity name**. (e.g., evidence: "IPPO and PQN", claim: "PPO-RNN and SAC"; evidence: "Success Rate and All-Core Pass Rate", claim: "Lane Distance and Map Coverage Rate")
- The claim asserts the **opposite trend** on the same finding. (e.g., evidence: "performance does not saturate", claim: "performance saturates"; evidence: "uncertain", claim: "clear"; evidence: "lack of training set", claim: "training data already available")

**If YES → `contradiction_candidate`.** Stop. Do not check Steps 2-5.
**If NO → proceed to Step 2.**

**Key insight:** The most common contradiction pattern is **detail-swapping** (changing specific numbers, names, or metrics), not explicit "however" / "but" language. Detail-swapping IS contradiction. Number inflation (90% → 95%) is contradiction (factual mismatch on the same metric), not strong_action.

### Step 2: Action/Deployment/Safety/Operational Cue Present? → Step 3 or Step 4

**Question:** Does the claim introduce any action/deployment/safety/guarantee/operational/policy/generalization language?

**Cue list (non-exhaustive):**
- **Deployment:** deploy, deployment, production, real-world, operational
- **Safety:** safety, guarantee, ensure, certify, reliable, reliability
- **Policy:** policy, recommend, should, must, need to
- **Generalization:** generaliz, cross-domain, broad, universal, scalable
- **Strength:** robust, comprehensive, mature, substantial, significantly, outperforms, dominates, superior, state-of-the-art
- **Theoretical:** theoretically justified, provably, proves
- **Action:** achieves, enables, allows, permits, supports the use of, can be used, suitable for, appropriate for, ready for
- **Invalidates:** invalidates, replaces, obsoletes, eliminates

**If YES → proceed to Step 3.**
**If NO → proceed to Step 4.**

**Key insight:** Many claims describe what the paper does ("presents", "evaluates", "reports") without explicit action language. If the claim only describes methodology without asserting action/deployment consequences, it goes to Step 4 (mild/supported). However, if the claim frames the methodology as a *contribution that enables* something beyond what the evidence supports, it may still be `strong_action_overclaim`.

### Step 3: Evidence Sufficient for Action Strength? → `strong_action_overclaim` or re-examine

**Question:** Is the evidence limited to local/experimental/simulated results, while the claim asserts a stronger action/deployment/safety/generalization conclusion?

**Operational test — answer YES (strong_action) if ANY of these are true:**
- The evidence is from a **single benchmark / single domain / controlled lab / limited metric**, while the claim asserts **deployment readiness, safety, broad generalization, or operational conclusion**.
- The evidence mentions **numerical/simulated experiments only**, while the claim asserts **physical plant trials, real-world deployment, or operational use**.
- The claim's **strength** (e.g., "theoretically justified", "outperforms", "ready for", "ensures") is beyond what the evidence's scope supports.

**If YES (evidence is local/limited, claim is strong) → `strong_action_overclaim`.**
**If NO (evidence actually supports the action claim) → re-examine as `supported` or `mild_scope_overclaim` (proceed to Step 4 to distinguish).**

**Critical distinction:** `strong_action_overclaim` does **not** require directional conflict with evidence. The claim may be directionally consistent (the evidence does support *something*), but the *strength* of the action/deployment/safety conclusion exceeds what the evidence warrants.

### Step 4: Scope Over-Extension? → `mild_scope_overclaim` or `supported`

**Question:** Does the claim expand scope, domain, population, condition, or temporal range beyond what the evidence supports, **without** asserting action/deployment/safety consequences?

**Operational test — answer YES (mild) if ANY of these are true:**
- The claim generalizes from **single-dataset** to **multi-dataset**.
- The claim expands from **single-domain** to **multi-domain**.
- The claim **adds details not in evidence** (e.g., "and five starting conditions" when evidence only says "2,000 episodes"; "as the main comparison basis" not in evidence; "multi-stage" adjective not in evidence).
- The over-extension is about **breadth/precision** rather than **action strength**.

**If YES → `mild_scope_overclaim`.**
**If NO → proceed to Step 5.**

**Key insight:** `supported` does not mean "the claim is absolutely true." It means "the evidence is sufficient for the strength of the claim as stated." A claim can be `supported` even if it is a modest factual statement.

### Step 5: Evidence Too Short / Context Missing? → `unsure` or use Step 4 label

**Question:** Is the evidence excerpt too short (e.g., under ~15 words) or truncated mid-sentence, such that you genuinely cannot tell whether the claim over-extends the evidence?

**If YES → `unsure`** (and in `rationale_one_sentence`, explain that the evidence excerpt is too short/truncated to judge; in `confusion_if_any`, note `evidence_insufficient_context`).
**If NO → use the label from Step 4** (`supported` if no scope over-extension; `mild_scope_overclaim` if scope over-extension).

**Key insight:** The decision tree cannot compensate for missing context. If the evidence excerpt is truncated, even a perfect annotator cannot reliably label the pair. Flagging these cases as `unsure` with `evidence_insufficient_context` is the correct response.

### Step 6: Still Cannot Decide? → `unsure`

If you have applied Steps 1-5 and still cannot decide (e.g., the case sits on a genuine boundary between two adjacent classes and you cannot pick a leaning label):

**→ `unsure`** (and in `rationale_one_sentence`, explain what makes the case hard; in `confusion_if_any`, note which two classes you are choosing between).

**Important:** Step 6 is a last resort. If you can narrow it to two adjacent classes, **pick the one you lean toward** and note the confusion — this is more informative than `unsure`.

---

## Quick Reference Table

| Step | Question | If YES | If NO |
|---|---|---|---|
| 1 | Directional conflict / detail-swap? | `contradiction_candidate` | → Step 2 |
| 2 | Action/deployment/safety/operational cue? | → Step 3 | → Step 4 |
| 3 | Evidence insufficient for action strength? | `strong_action_overclaim` | Re-examine as supported/mild (→ Step 4) |
| 4 | Scope over-extension without action? | `mild_scope_overclaim` | → Step 5 |
| 5 | Evidence too short / context missing? | `unsure` | Use Step 4 label (`supported`) |
| 6 | Still cannot decide after Steps 1-5? | `unsure` | (should not reach here) |
