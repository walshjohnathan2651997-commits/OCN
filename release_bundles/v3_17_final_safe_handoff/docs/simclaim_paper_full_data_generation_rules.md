# SimClaim paper-full data generation rules

## Purpose

The paper-full dataset should test evidence-conditioned claim calibration, not shallow claim-template recognition.

The central rule is:

```text
The claim alone should not reliably reveal the label.
The claim-evidence relation should determine the label.
```

## Admission pipeline

Every generated batch should pass these gates before entering the paper-full candidate pool:

1. Source trace complete
2. Evidence text locked and hash-matched
3. Four labels present for each evidence group
4. No duplicate claim text inside a group
5. Strict semantic validation passes
6. TF-IDF leakage audit passes
7. Group is not marked `lexical_leakage_risk`

The current admission gate script is:

```text
D:\ocn\scripts\build_paper_full_admission_gate.py
```

The current TF-IDF leakage audit script is:

```text
D:\ocn\scripts\audit_tfidf_leakage.py
```

## Hard generation rules

Do not use label-revealing words or phrases, including:

```text
always
never
guarantee
guarantees
fully replace
complete framework
must
should
need to
recommended
policy
deployment
all settings
all domains
most settings
most domains
across most applications
```

Do not use generic template tails such as:

```text
within the same described research context
same described research context
described research context
```

Those phrases were useful for early style control, but the TF-IDF audit showed they become template pollution.

## Soft cue balancing

Some words are not always forbidden, but they become risky if they appear in only one label variant inside a group:

```text
selected
additional
scenario
scenarios
real-world
driving
related
adjacent
tasks
contexts
setting
beyond
outside
use
can
generally
varied
diverse
without
only
excluding
fewer
less
not
```

If one of these appears, it should either:

- appear across multiple labels in a balanced way; or
- be replaced with a label-neutral factual slot.

## Preferred claim construction

For a group of four claims from the same evidence:

```text
same subject
+ same main verb phrase
+ short factual slot that changes the evidence relation
+ no repeated boilerplate tail
```

The four claims should have similar length, syntax, and formality. The difference should come from the factual relation to evidence, not from obvious label vocabulary.

## What to prioritize

The most valuable samples are B-type evidence-needed cases:

```text
claim-only TF-IDF wrong
claim+evidence TF-IDF correct
```

These cases are the clearest signs that the claim alone is insufficient and that evidence is doing useful work.

## What to rewrite or hold out

Groups should be rewritten or held out if:

```text
primary-target claim-only TF-IDF group accuracy >= 0.75
```

The current high-risk groups are:

```text
V4-G002
V4-G009
V4-G011
```

They passed earlier strict validation but should not enter the paper-full final set unchanged.

## Current safe local candidate pool

The current leakage-filtered candidate pool is:

```text
D:\ocn\data\simclaim_release_candidate_v1_19_gate_pass\candidates\candidate_master_leakage_filtered_64.csv
```

It contains:

- 64 rows
- 16 groups
- balanced 4-class candidate labels
- complete trace fields
- no human-audited gold labels

This is the safer local pool for the next paper-full candidate audit stage.

