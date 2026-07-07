# Table 8 — Small Targeted Human Audit

**Status: Staged, not executed.**

A small targeted human audit protocol is prepared with 6 sampling buckets:
1. Top-20 queue candidates
2. Top-50 strong-action candidates
3. R4 false positives
4. R4 false negatives
5. Mild-vs-strong boundary cases
6. Contradiction confusion cases

**Audit packet:** 111 candidates selected, `data/private_audit/v3_17_audit_packet/audit_packet_private.csv` (gitignored, contains raw claim/evidence text for human review only).

**Protocol:** Two-annotator independent review followed by adjudication. Agreement metrics to be reported in `experiments/human_audit_v1/audit_agreement_summary.json` when executed.

**Current status:** The audit has **not been executed**. `human_audited=False` for all 444 candidates. `gold_label` is empty for all 444 candidates. No human-audited benchmark results are reported.

**Final Gate:** WARNING 6.4 (human audit staged, not executed).

[Source: docs/human_audit_protocol_v1.md; experiments/human_audit_v1_pending/audit_pending_summary.md; reports/final_perfect_state_gate_v3_17.md]
