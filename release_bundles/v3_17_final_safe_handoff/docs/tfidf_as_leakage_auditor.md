# TF-IDF as a lexical leakage auditor for SimClaim

## Position

TF-IDF should not be treated only as a weak baseline to defeat. In the SimClaim setting, claim-only TF-IDF is useful as a leakage auditor: if a shallow lexical model can predict the candidate label from the claim alone, the sample may contain claim-side cues that reduce the need to inspect evidence.

The current research question is therefore not:

```text
Can CESE-OCN always beat TF-IDF on small pilot data?
```

The more appropriate question is:

```text
Which candidate groups actually require evidence-conditioned reasoning, and which groups are still solvable from claim wording alone?
```

## Current checkpoint

The current audited checkpoint is:

```text
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass
```

It contains:

- 76 candidate rows
- 19 template/evidence groups
- 19 rows per candidate label class
- complete source trace fields
- no human-audited gold labels

The TF-IDF leakage audit script is:

```text
D:\ocn\scripts\audit_tfidf_leakage.py
```

Primary outputs:

```text
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass\reports\tfidf_leakage_audit.json
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass\reports\tfidf_leakage_audit.md
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass\reports\tfidf_leakage_cases.csv
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass\audit\tfidf_leakage_group_risk.csv
```

## Audit protocol

The audit uses leave-one-group-out validation by `v4_group_id`.

For each held-out group, all rows from that group are excluded from training. This is stricter than the ordinary train/dev/test pilot gate and is intended to detect whether patterns generalize across groups.

The audit runs three TF-IDF views:

- claim-only
- claim+evidence
- evidence-only

For every sample and target, it records:

- `claim_only_correct`
- `claim_evidence_correct`
- `claim_only_wrong_but_claim_evidence_correct`
- `claim_only_correct_but_claim_evidence_wrong`

The main target for leakage admission is:

```text
candidate_label_guess
```

The binary targets are still reported, but they are secondary because they are easier and more sensitive to class imbalance.

## Current finding

Under leave-one-group-out validation, the current checkpoint still shows strong claim-side lexical signal. On the primary 4-class target, the audit found:

```text
A: claim-only correct and claim+evidence correct = 21
B: claim-only wrong but claim+evidence correct = 4
C: both wrong = 40
D: claim-only correct but claim+evidence wrong = 11
```

The B cases are the most valuable for the final SimClaim benchmark because they are the clearest evidence-necessary samples.

The current group-level lexical leakage risk rule is:

```text
lexical_leakage_risk = true
if primary-target claim-only TF-IDF group accuracy >= 0.75
```

Current high-risk groups:

```text
V4-G002
V4-G009
V4-G011
```

These groups should not enter the paper-full final set unchanged. They should be rewritten, replaced, or held out as diagnostic leakage examples.

## Why this matters

Small-data TF-IDF can perform well for the wrong reason. If claim wording repeatedly exposes the label, then a classifier can appear strong without performing evidence-conditioned calibration.

Examples of risky patterns include:

- fixed template tails, such as repeated "within the same described research context"
- label-specific scope words, such as "selected", "scenarios", "all", "most", or "complete"
- contradiction cues that rely on obvious negation or antonyms rather than evidence comparison
- strong-overclaim cues that rely on broad universal claims rather than fine-grained source mismatch

The goal is not to remove every easy sample. Some easy supported or contradiction examples are useful for calibration. The goal is to prevent the final benchmark from being dominated by examples where the claim alone is enough.

## Admission rule for paper-full data

For each generated batch:

1. Run the strict source-trace and semantic validator.
2. Run the TF-IDF leakage audit.
3. Mark groups with high claim-only accuracy as `lexical_leakage_risk`.
4. Prioritize B cases for final admission.
5. Rewrite or replace high-risk groups before they enter the final paper-full set.

Recommended admission categories:

```text
accept_candidate:
  strict validator passes
  source trace complete
  evidence locked
  no group-level lexical leakage risk

rewrite_or_replace:
  strict validator passes
  but claim-only TF-IDF group accuracy >= 0.75

priority_expand:
  group contains B cases
  claim-only wrong but claim+evidence correct
```

## Paper narrative

Avoid claiming that the method already beats every lexical baseline on all small-data settings.

A safer and more accurate framing is:

```text
TF-IDF is a strong lexical baseline under small-data conditions. Rather than treating it as a weak comparator, we use claim-only TF-IDF as a lexical leakage auditor. The next SimClaim construction stage filters shallow claim-side cues and emphasizes evidence-necessary cases where claim-only models fail but evidence-conditioned models succeed.
```

This framing fits the actual project better than forcing a premature "we beat all baselines" claim.

