# Corpus Alignment Pilot — Pending Summary (v1)

Generated: 2026-07-08T06:28:47.807543+00:00

## Status

- **Pilot packet prepared:** YES
- **Pilot executed:** NO
- **Human-audited validation claimed:** NO
- **Reason:** --pending flag passed

## What exists

- Pilot sheet (gitignored, private): `data/private_audit/v3_17_audit_packet/audit_packet_alignment_pilot_zh_bilingual.xlsx`
- Pilot CSV (gitignored, private): `data/private_audit/v3_17_audit_packet/audit_packet_alignment_pilot_zh_bilingual.csv`
- Annotation guide: `docs/corpus_alignment_audit_guide_zh_v1.md`
- Label map: `data/audit_templates/corpus_alignment_label_map_zh_v1.csv`
- Summarize script: `scripts/summarize_corpus_alignment_pilot_v1.py`

## What does NOT exist

- No `alignment_summary.json` (pilot not executed)
- No `alignment_summary.md` (pilot not executed)
- No `alignment_cases_redacted.csv` (pilot not executed)
- No `label_eligible_rate` computed (pilot not executed)
- No human-audited validation (pilot not executed)

## Decision rule (to be applied after pilot completion)

| label_eligible_rate | recommendation |
|---|---|
| >= 0.85 | proceed with full 111-item human label audit |
| 0.70 ~ 0.85 | label only eligible subset; rest as corpus noise analysis |
| < 0.70 | stop formal label audit; pivot to corpus alignment / silver diagnostic failure analysis |

## Safe wording

- 「corpus alignment pilot packet prepared; pilot not yet executed.」
- 「no human-audited validation claimed.」
- 「this is a targeted alignment check, not a gold benchmark.」

### Forbidden wording (禁止的措辞)

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| 「human-validated dataset」 | pilot not executed |
| 「human-audited validation」 | pilot not executed |
| 「gold benchmark」 | silver diagnostic; not gold |
| 「the silver labels are correct」 | no audit has verified them |
| 「SOTA」 | no gold comparison; silver diagnostic only |
| 「automatic peer reviewer」 | not an automatic peer reviewer |
| 「general detector」 | not a validated general detector |

## Guards

- no_api: True
- no_network: True
- no_training: True
- no_original_data_modification: True

## Next step

An auditor fills `语料关联性`, `selected_evidence关联性`, `是否可进入标签判断`, and `不可判原因` (when 否) in the pilot xlsx, saves as `audit_packet_alignment_pilot_completed.xlsx`, then runs:

```
python scripts/summarize_corpus_alignment_pilot_v1.py \
    --completed_alignment_xlsx data/private_audit/v3_17_audit_packet/audit_packet_alignment_pilot_completed.xlsx
```
