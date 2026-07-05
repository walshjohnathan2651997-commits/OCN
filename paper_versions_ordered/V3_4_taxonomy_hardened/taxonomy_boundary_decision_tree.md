# Taxonomy Boundary Decision Tree for Evidence Sufficiency Calibration

**Version:** V3.4
**Purpose:** Provide an operational, reproducible procedure for assigning one of four evidence-sufficiency labels to a claim-evidence pair. This decision tree is designed to reduce the mild-vs-strong and strong-vs-contradiction boundary confusion identified in the author sanity audit (§V.D).

**Important:** This decision tree is a *labeling aid*, not a gold standard. It operationalizes the taxonomy but does not resolve all boundary cases. Cases where the decision tree yields ambiguous results should be flagged as boundary cases for future gold adjudication.

---

## The Four Labels

| Label | Core Definition |
|---|---|
| **supported** | Evidence is sufficient for the claim's stated strength (not "absolutely true"). |
| **mild_scope_overclaim** | Claim mildly over-extends scope/domain/generality, but no action/deployment/safety conclusion asserted. |
| **strong_action_overclaim** | Claim asserts an action/deployment/safety/guarantee/operational/policy conclusion that evidence cannot justify. Direction may be consistent; strength is excessive. |
| **contradiction_candidate** | Evidence contradicts the claim; directions conflict on the same metric or conclusion. |

---

## Decision Tree (Step-by-Step)

```
                        ┌─────────────────────────────┐
                        │  Claim-Evidence Pair         │
                        └──────────────┬──────────────┘
                                       │
                                       v
                   ┌────────────────────────────────────┐
                   │  Step 1: Directional Conflict?      │
                   │  Does the claim point in the        │
                   │  OPPOSITE direction from the        │
                   │  evidence on the same metric,       │
                   │  number, entity, or conclusion?     │
                   └──────────────┬─────────────────────┘
                          YES     │     NO
                          ┌───────┘     └────────┐
                          v                      v
              ┌──────────────────┐   ┌────────────────────────┐
              │ contradiction_   │   │  Step 2: Action/        │
              │ candidate        │   │  Deployment/Safety/     │
              └──────────────────┘   │  Guarantee/Operational  │
                                     │  Cue Present?            │
                                     │                          │
                                     │  Does the claim introduce│
                                     │  any of:                 │
                                     │  - deployment readiness  │
                                     │  - safety guarantee      │
                                     │  - operational conclusion│
                                     │  - policy prescription   │
                                     │  - real-world control    │
                                     │  - broad generalization  │
                                     │  - action recommendation │
                                     │  - "theoretically        │
                                     │    justified" / "provably"│
                                     │  - "outperforms" /        │
                                     │    "dominates"            │
                                     │  - "ready for" /          │
                                     │    "suitable for"         │
                                     └────────────┬─────────────┘
                                          YES     │     NO
                                          ┌───────┘     └────────┐
                                          v                      v
                              ┌─────────────────────┐  ┌─────────────────────┐
                              │  Step 3: Evidence    │  │  Step 4: Scope      │
                              │  Sufficient for      │  │  Over-Extension?    │
                              │  Action Strength?    │  │                     │
                              │                      │  │  Does the claim     │
                              │  Is the evidence     │  │  expand scope,      │
                              │  limited to:         │  │  domain, population,│
                              │  - single benchmark  │  │  condition, or      │
                              │  - simulation only   │  │  temporal range     │
                              │  - controlled lab    │  │  beyond what        │
                              │  - limited metric    │  │  evidence supports, │
                              │    improvement       │  │  WITHOUT action     │
                              │  - single domain     │  │  consequences?      │
                              │                      │  │                     │
                              │  while the claim     │  └─────────┬───────────┘
                              │  asserts a stronger  │      YES   │   NO
                              │  action/deployment/  │      ┌────┘   └────┐
                              │  safety conclusion?  │      v            v
                              └──────────┬───────────┘  ┌────────┐  ┌────────┐
                                    YES  │  NO           │ mild_  │  │        │
                                    ┌────┘   └────┐       │ scope_ │  │ sup-   │
                                    v             v      │ over-  │  │ ported │
                            ┌─────────────┐ ┌──────────┐ │ claim  │  └────────┘
                            │ strong_     │ │ Re-examine│ └────────┘
                            │ action_     │ │ for mild  │
                            │ overclaim   │ │ or sup.   │
                            └─────────────┘ └──────────┘
```

---

## Step-by-Step Operational Rules

### Step 1: Directional Conflict? → contradiction_candidate

**Question:** Does the claim point in the *opposite direction* from the evidence on the same metric, number, entity, or conclusion?

**Operational test:**
- Does the claim cite a *different number* than the evidence for the same metric? (e.g., evidence: "6 systems", claim: "8 systems" or "2 systems")
- Does the claim cite a *different entity name*? (e.g., evidence: "IPPO and PQN", claim: "PPO-RNN and SAC")
- Does the claim cite a *different metric*? (e.g., evidence: "Success Rate and All-Core Pass Rate", claim: "Lane Distance and Map Coverage Rate")
- Does the claim assert the *opposite trend*? (e.g., evidence: "performance does not saturate", claim: "performance saturates")

**If YES → `contradiction_candidate`.**
**If NO → proceed to Step 2.**

**Key insight from audit:** The most common contradiction pattern in SimClaim is *detail-swapping* (changing specific numbers, names, or metrics), not explicit "however" or "but" language. The audit heuristic missed this pattern because it looked for explicit contradiction cues. Detail-swapping IS contradiction.

### Step 2: Action/Deployment/Safety/Operational Cue Present? → Step 3 or Step 4

**Question:** Does the claim introduce any action/deployment/safety/guarantee/operational/policy/generalization language?

**Cue list (non-exhaustive):**
- Deployment: "deploy", "deployment", "production", "real-world", "operational"
- Safety: "safety", "guarantee", "ensure", "certify", "reliable", "reliability"
- Policy: "policy", "recommend", "should", "must", "need to"
- Generalization: "generaliz", "cross-domain", "broad", "universal", "scalable"
- Strength: "robust", "comprehensive", "mature", "substantial", "significantly", "outperforms", "dominates", "superior", "state-of-the-art"
- Theoretical: "theoretically justified", "provably", "proves"
- Action: "achieves", "enables", "allows", "permits", "supports the use of", "can be used", "suitable for", "appropriate for"
- Invalidates: "invalidates", "replaces", "obsoletes", "eliminates"

**If YES → proceed to Step 3.**
**If NO → proceed to Step 4.**

**Key insight from audit:** Many claims describe what the paper does ("presents", "evaluates", "reports") without explicit action language. These are harder to classify. If the claim only describes methodology without asserting action/deployment consequences, it is more likely mild or supported. However, if the claim frames the methodology as a *contribution that enables* something beyond what the evidence supports, it may still be strong_action.

### Step 3: Evidence Sufficient for Action Strength? → strong_action_overclaim or re-examine

**Question:** Is the evidence limited to local/experimental/simulated results, while the claim asserts a stronger action/deployment/safety/generalization conclusion?

**Operational test:**
- Is the evidence from a *single benchmark*, *single domain*, *controlled lab setting*, or *limited metric improvement*?
- Does the claim promote this into a *deployment*, *safety*, *policy*, *generalization*, or *operational* conclusion?
- Is the claim's *strength* (e.g., "theoretically justified", "outperforms", "ready for") beyond what the evidence's scope supports?

**If YES (evidence is local/limited, claim is strong) → `strong_action_overclaim`.**
**If NO (evidence actually supports the action claim) → re-examine as `supported` or `mild_scope_overclaim`.**

**Critical distinction:** strong_action_overclaim does NOT require directional conflict with evidence. The claim may be directionally consistent (the evidence does support *something*), but the *strength* of the action/deployment/safety conclusion exceeds what the evidence warrants.

### Step 4: Scope Over-Extension? → mild_scope_overclaim or supported

**Question:** Does the claim expand scope, domain, population, condition, or temporal range beyond what the evidence supports, *without* asserting action/deployment/safety consequences?

**Operational test:**
- Does the claim generalize from single-dataset to multi-dataset?
- Does the claim expand from single-domain to multi-domain?
- Does the claim add details not in evidence (e.g., "and five starting conditions" when evidence only says "2,000 episodes")?
- Is the over-extension about *breadth/precision* rather than *action strength*?

**If YES → `mild_scope_overclaim`.**
**If NO → `supported`.**

**Key insight:** `supported` does not mean "the claim is absolutely true." It means "the evidence is sufficient for the strength of the claim as stated." A claim can be `supported` even if it is a modest factual statement.

---

## Boundary Cases: Why They Are Hard

### Mild vs. Strong Boundary

This is the hardest boundary (12/25 questionable/unclear cases in the audit). The distinction is:

- **mild_scope_overclaim**: scope/breadth/precision over-extension *without* action/deployment/safety consequences.
- **strong_action_overclaim**: action/deployment/safety/generalization conclusion that evidence cannot justify.

A claim that adds "and five starting conditions" to evidence that only mentions "2,000 episodes" is *mild* (precision over-extension). A claim that turns "2,000 episodes on a physical system" into "validated for deployment readiness" is *strong* (action over-extension).

The boundary is unclear when a claim has *some* scope expansion *and* *some* action framing, but neither is dominant. These cases should be flagged as boundary cases for gold adjudication.

### Strong vs. Contradiction Boundary

This boundary was the source of 6/25 questionable/unclear cases in the audit. The distinction is:

- **contradiction_candidate**: directions *conflict* on the same metric/number/entity. The claim asserts the opposite of what evidence supports.
- **strong_action_overclaim**: directions may *align*, but the claim's *strength* exceeds what evidence warrants.

A claim that says "accuracy is 95%" when evidence says "accuracy is 90%" is *contradiction* (number conflict). A claim that says "the system is deployment-ready" when evidence says "accuracy improved on benchmark X" is *strong_action* (strength over-extension, no directional conflict).

The boundary is unclear when a claim *inflates a number* (e.g., 90%→95%) — this could be read as contradiction (factual mismatch) or strong_action (inflating the strength of the result). The decision tree treats number inflation as contradiction (Step 1), but acknowledges this is a boundary case.

---

## What This Decision Tree Does NOT Resolve

1. **Claims that describe methodology without action language.** Some claims say "the paper presents X" without asserting action consequences. The decision tree routes these to Step 4 (mild/supported), but the silver label may be strong_action if the claim's *framing* implies significance beyond evidence. This requires human judgment.

2. **Number inflation.** A claim that inflates a metric (e.g., 90%→95%) is treated as contradiction by Step 1, but could be argued as strong_action (strength inflation). Gold adjudication should decide.

3. **Claims with implicit action framing.** A claim that says "the method is a step toward low-code applications" has implicit action framing but no explicit deployment/safety language. Step 2 may miss this. The cue list is non-exhaustive.

4. **Evidence that is too short or lacks context.** Some evidence excerpts are truncated. The decision tree cannot compensate for missing context. These cases should be flagged as `evidence_too_short_or_context_missing`.

---

## Recommended Use

1. **For future gold annotation:** Use this decision tree as the annotation guide. Annotators should apply Steps 1-4 in order, then flag any case where the result is ambiguous as a boundary case.

2. **For paper case selection:** Use this decision tree to identify cases where the label is *clear* (all steps yield unambiguous results) vs. *boundary* (steps yield ambiguous results). Trusted case bank (§V.D) should only include clear cases.

3. **For reviewer defense:** This decision tree demonstrates that the taxonomy is *operationalizable*, not purely subjective. The 25 questionable/unclear audit cases are boundary cases where the decision tree yields ambiguous results — this is expected for a hard task and does not invalidate the taxonomy.
