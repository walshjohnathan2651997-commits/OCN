# Human Audit — Pending Summary (v1)

Generated: 2026-07-07T12:50:23.985934+00:00

## Status

- **Audit packet prepared:** YES
- **Audit executed:** NO
- **Human-audited validation claimed:** NO

## What exists

- Audit protocol: `docs/human_audit_protocol_v1.md`
- Audit template: `data/audit_templates/human_audit_template.csv`
- Audit seed queue (redacted): `data/audit_templates/human_audit_queue_seed_v1_redacted.csv`
- Execution manifest (redacted): `data/audit_templates/human_audit_execution_manifest_v1_redacted.csv`
- Private audit packet (gitignored): `data/private_audit/v3_17_audit_packet/audit_packet_private.csv`
- Annotator instructions: `data/private_audit/v3_17_audit_packet/audit_instructions_for_annotators.md`
- Label decision tree: `data/private_audit/v3_17_audit_packet/audit_label_decision_tree.md`
- Synthetic examples: `data/private_audit/v3_17_audit_packet/audit_examples_synthetic_only.md`
- Completion checklist: `data/private_audit/v3_17_audit_packet/audit_completion_checklist.md`

## What does NOT exist

- No `audit_agreement_summary.json` (audit not executed)
- No `audit_confusion_matrix.csv` (audit not executed)
- No `audit_disagreement_cases_redacted.csv` (audit not executed)
- No `audit_summary.md` with agreement metrics (audit not executed)
- No human-audited validation (audit not executed)

## Safe wording

- "Audit packet prepared; audit not yet executed."
- "No human-audited validation claimed."
- "This is a targeted audit protocol, not a gold benchmark."
- "Until completed, the paper can only claim audit readiness, not human-audited validation."

## Forbidden wording

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| "human-audited dataset" | audit not executed |
| "human-audited validation" | audit not executed |
| "gold benchmark" | silver diagnostic; audit not executed |
| "the silver labels are correct" | no audit has verified them |
| "SOTA" | no gold comparison; silver diagnostic only |

## Guards

- no_api: True
- no_network: True
- no_training: True
- no_original_data_modification: True

## Next step

An auditor fills `auditor_label`, `auditor_confidence`, `audit_notes`, `disagreement_reason`, and `requires_second_review` in the private audit packet, then sets `human_audited=True` for each row. When complete, run `scripts/summarize_human_audit_v1.py --audit-csv data/private_audit/v3_17_audit_packet/audit_packet_private.csv` to produce agreement metrics.

