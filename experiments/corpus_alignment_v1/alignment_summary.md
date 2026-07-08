# Corpus Alignment Pilot — Summary (v1)

Generated: 2026-07-08T09:34:19.102909+00:00
Source: `audit_packet_alignment_pilot_completed.xlsx`
N_pilot: 30

## Status

- **Pilot executed:** YES
- **Human-audited validation claimed:** NO (this is an alignment pilot, not a label audit)

## Metrics

### Primary decision metrics (split)

| metric | value | meaning |
|---|---|---|
| claim_evidence_label_eligible_rate | 1.0 | 语料关联性 related AND 是否可进入标签判断 == 是 |
| selected_evidence_system_eval_eligible_rate | 0.1 | selected_evidence关联性 in related set (non-empty/usable) |
| selected_evidence_missing_or_short_rate | 0.9 | selected_evidence关联性 == 为空或太短 |

### Corpus alignment distribution

| metric | value |
|---|---|
| n_pilot | 30 |
| pair_valid_rate | 1.0 |
| topic_only_rate | 0.0 |
| unrelated_rate | 0.0 |
| insufficient_context_rate | 0.0 |
| selected_evidence_alignment_rate | 0.1 |
| needs_second_review_rate | 0.0 |

### Legacy / compatibility

| metric | value | status |
|---|---|---|
| label_eligible_rate | 1.0 | legacy/compatibility — not the sole decision metric |

## Corpus alignment distribution (语料关联性)

| label | count |
|---|---|
| 明确相关 | 30 |

## Selected evidence alignment distribution (selected_evidence关联性)

| label | count |
|---|---|
| 为空或太短 | 27 |
| 和claim弱相关 | 3 |

## Eligible distribution (是否可进入标签判断)

| label | count |
|---|---|
| 是 | 30 |

## Decision

### Part 1 — claim-evidence label audit (primary)

- **tier:** proceed_full_label_audit
- **claim_evidence_label_eligible_rate:** 1.0
- **threshold:** >= 0.85
- **recommendation:** Pilot suggests the audit packet is ready for formal 111-item human label audit. Proceed with the full label audit.

### Part 2 — selected_evidence system evaluation (secondary)

- **selected_evidence_system_eval_eligible_rate:** 0.1
- **selected_evidence_status:** insufficient
- **note:** selected_evidence_system_eval_eligible_rate = 0.1000 is low (< 0.5). Do NOT conclude the model label evaluation failed. Report 'selected_evidence coverage/alignment insufficient' and treat as an evidence-selection failure to analyze separately from the label-audit decision.

## Safe wording

- 「corpus alignment pilot, N=30」
- 「claim_evidence_label_eligible_rate = 1.0 on the pilot subset」
- 「selected_evidence_system_eval_eligible_rate = 0.1 (evidence-selection coverage)」
- 「small targeted alignment check, not a gold benchmark」

### Forbidden wording (禁止的措辞)

| Unsafe wording (forbidden) | Why forbidden |
|---|---|
| 「human-validated dataset」 | alignment pilot, not label audit |
| 「human-audited validation」 | only alignment pilot |
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
- no_raw_text_in_output: True (hash-only in cases CSV)

