# Complexity-vs-Utility Claims Checklist

Generated: 2026-07-06T17:58:16.172832+00:00

## Safe Claims (allowed)

- "Under confidential/no-API/no-training constraints, deterministic
  canonicalization has a better performance-privacy-auditability-cost
  tradeoff than higher-complexity variants."
- "Deployment-specific tradeoff: the deterministic pipeline is
  preferable in this setting, not in general."
- "SmartQueue is a routing/usability layer, not a new model."
- "Learned selector (RF) did not improve over frozen baseline
  (strong_F1 gap = -0.0059) on this silver diagnostic set."
- "Learned ranker (LogReg) did not improve over G_conservative_precision
  (precision@20 gap = -0.10) on this silver diagnostic set."
- "External LLM baseline was not run due to no-API guard; it is listed
  for tradeoff reference only."
- "The deterministic pipeline is auditable end-to-end: every selection
  and ranking step is deterministic and inspectable."

## Unsafe Claims (forbidden)

- "Simple methods generally beat intelligent methods."
- "Rules beat learning."
- "BM25 beats LLMs."
- "The deterministic pipeline is optimal."
- "SOTA."
- "Learned methods are useless."
- "The silver diagnostic results generalize to real-world claims."
- "SmartQueue improves over G_conservative_precision" (it does not
  improve precision@20; it improves usability only).

## Required Disclaimers for Any Paper Use

1. "This is a controlled silver diagnostic, not a gold benchmark."
2. "Results reflect a balanced 4-class silver pool and do NOT represent
   real-world claim prevalence."
3. "The deterministic-vs-learned comparison is deployment-specific and
   does not generalize beyond the confidential/no-API setting."
4. "Learned variants were trained on silver labels with group-aware
   splitting; no gold labels were used."

## SmartQueue Wording

If SmartQueue does not improve the headline precision@20 over
G_conservative_precision, state clearly:
- "SmartQueue is a routing/usability layer (bucket assignment, group
  diversity, multi-profile support), not a new ranking model."
- "SmartQueue does not improve precision@20; it improves review
  usability by routing candidates to review buckets and enforcing group
  diversity."

Do NOT claim:
- "SmartQueue improves ranking quality."
- "SmartQueue is a better ranker than G_conservative_precision."

## Utility Score Disclaimer

Utility score is diagnostic aggregation, not a benchmark metric.
It is a weighted sum of performance, privacy, auditability, simplicity,
and reproducibility scores. The weights reflect deployment priorities
(confidential pipeline → privacy and auditability weighted higher).
Different weight choices would yield different utility rankings. The
utility score is NOT comparable to strong_F1 or precision@20 and should
NOT be reported as a performance metric.
