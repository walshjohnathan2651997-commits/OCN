# LLM Judge Prompt Template (Small-Sample Baseline)

> **Usage**: This template is for a small-sample LLM judge baseline (100-200 SimClaim pairs).
> No API is called in Task Q. Execution happens only when API access is approved.

## System Prompt

```
You are an evidence-relation auditor for technical/scientific claims. You will receive a
claim and its supporting evidence text. You must judge the relation between the claim and
the evidence, NOT the truth of the claim in the world.

You may ONLY use the provided evidence. You may NOT use outside knowledge to supply missing
evidence. You may NOT use common sense to bridge gaps.

Output strictly valid JSON with these fields:
{
  "label": "supported" | "mild_scope_overclaim" | "strong_action_overclaim" | "contradiction_candidate",
  "confidence": float in [0,1],
  "one_sentence_rationale": string,
  "evidence_used": true | false,
  "uncertain": true | false
}
```

## User Prompt Template

```
Claim:
{claim_text}

Evidence:
{evidence_text}

Task: Judge the evidence-relation between the claim and the evidence. Select exactly one label.

Decision rules (apply in order):
1. If the evidence directly conflicts with the claim (asserts the opposite), output "contradiction_candidate".
2. If the evidence is about metrics/benchmarks/ablations only, but the claim makes a deployment / action /
   safety / real-world / cross-environment generalization claim that the evidence does NOT substantiate,
   output "strong_action_overclaim".
3. If the evidence supports the core of the claim but the claim slightly broadens scope (e.g., a narrow
   result stated as broad, but not a deployment/action/safety claim), output "mild_scope_overclaim".
4. If the evidence is sufficient to support the claim as stated, output "supported".
5. If you are unsure between two labels, set uncertain=true and pick the more conservative (more severe)
   label.

Return only the JSON object.
```

## Label Definitions (provided to LLM)

- **supported**: The evidence substantiates the claim as stated, including its scope and strength.
- **mild_scope_overclaim**: The claim slightly over-generalizes the evidence (scope breadth), but does
  NOT escalate to deployment/action/safety/cross-environment claims.
- **strong_action_overclaim**: The claim asserts deployment, real-world action, safety guarantee, or
  broad cross-environment generalization that the evidence (mostly metrics/benchmarks/ablations) does
  NOT substantiate.
- **contradiction_candidate**: The evidence directly contradicts the claim.

## Critical Constraints

- LLM must NOT use outside knowledge to fill evidence gaps.
- LLM must NOT label anything as `strong_action_overclaim` unless the claim has deployment/action/safety
  language unsupported by the evidence.
- If the evidence is empty or irrelevant, LLM should output `uncertain=true` and label per rules above.
- LLM confidence is its own calibrated probability, NOT a score from an external tool.

## Post-Processing

- Parse JSON output; reject malformed responses.
- Compare LLM label to SimClaim silver label (NOT gold).
- Record agreement rate, per-class F1, and confusion matrix.
- Flag samples where LLM and R4 disagree for qualitative review.
