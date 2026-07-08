# Human Audit — Pending Summary (v1)

Generated: 2026-07-08T06:06:08.863498+00:00

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
- Bilingual dropdown audit sheet (gitignored): `data/private_audit/v3_17_audit_packet/audit_packet_simple_zh_bilingual.xlsx`
- Bilingual CSV (gitignored): `data/private_audit/v3_17_audit_packet/audit_packet_simple_zh_bilingual.csv`
- Annotation guide v2: `docs/human_audit_annotation_guide_zh_v2.md`
- Label map v2: `data/audit_templates/human_audit_label_map_zh_v2.csv`
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

## Bilingual dropdown audit sheet

中文双语下拉审计表已准备好 (Chinese bilingual dropdown audit sheet prepared).
The xlsx includes dropdown lists for: 证据是否一致, 系统证据是否足够, 人工标签, 信心1到5, 是否二审.
真实人工审计尚未完成 (Real human audit not yet completed).
未声称 human-audited validation (No human-audited validation claimed).

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

An auditor fills `人工标签`, `信心1到5`, `证据是否一致`, `系统证据是否足够`, `是否二审`, and `备注` in the bilingual xlsx, saves as `audit_packet_simple_zh_bilingual_completed.xlsx`, then runs:

```
python scripts/summarize_human_audit_v1.py \
    --completed_audit_csv data/private_audit/v3_17_audit_packet/audit_packet_simple_zh_bilingual_completed.xlsx
```

