# V3.16 Change Log

**Version:** V3.16 No-Gold Evidence Integration
**Date:** 2026-07-05
**Base version:** V3.15 Hierarchical Taxonomy Revision
**Output directory:** `D:\ocn\paper_versions_ordered\V3_16_no_gold_evidence_integration\`

---

## 1. Summary

This version integrates the no-gold evidence integration plan (`D:\ocn\project_synthesis\no_gold_evidence_integration_v3_16_plan\`) into the paper as **wording-level and insertion-level edits only**. No new experiments, no API calls, no gold annotation, no new model training, no threshold retuning.

---

## 2. Inserted content

| # | Section | Insertion | Anchor |
| --- | --- | --- | --- |
| 1 | Header | V3.16 changes paragraph | before "Author information omitted" |
| 2 | Header | Version line updated to V3.16 | top of file |
| 3 | Header | Date line updated to V3.16 | top of file |
| 4 | Abstract | One no-gold support sentence (scalar cannot replace; low-prevalence supports R4 only as second-stage) | before "A pre-registered two-layer gold adjudication protocol" |
| 5 | §I Introduction | One paragraph on three alternatives (scalar, LLM judge, low-prevalence simulation); silver-stage caveat | after "This motivates the evidence sufficiency calibration task" paragraph |
| 6 | §II.A Related Work | SciFact / VitaminC positioning paragraph; RIGOURATE-is-closest-prior-work statement; ForceBench blocked note | before "### B. Mainline Lock Declaration" |
| 7 | §V.A Data | Heuristic realism auto-audit paragraph (0.2% high-risk, 2.0% medium-risk) | before "### B. LLM Judge Comparison Protocol" |
| 8 | §VI.F Results (NEW) | Scalar vs R4 vs LLM consolidated head-to-head (Table 2b; 9-row comparison) | after §VI.E, before "## VII" |
| 9 | §VI.G Results (NEW) | Low-prevalence screening simulation (Table 2c; 6 prevalence levels; 4 required answers) | after §VI.F, before "## VII" |
| 10 | §VIII.H Discussion (NEW) | Two-stage deployment recommendation (LLM first stage + R4 second stage) | before "## IX. Limitations" |
| 11 | §IX Limitations | Three new items (12 ForceBench blocked; 13 simulation not natural; 14 mild_vs_strong unresolved) | before "## X. Conclusion" |
| 12 | §X Conclusion | "No-gold evidence integration" reinforcing paragraph | before "## Appendix A" |

---

## 3. Preserved numbers (byte-identical from V3.15)

- R4 strong-F1 = 0.3967 (silver 444)
- R4 strong-recall = 0.4562 (silver 444)
- R4 macro-F1 = 0.4238 (silver 444) / 0.3280 (matched 100)
- baseline_flat4 strong-F1 = 0.2408
- LLM (GPT-5.5 / DeepSeek-V3) strong-F1 = 0.0769 (matched 100/200)
- LLM strong-recall = 0.04
- R4 strong-F1 = 0.3000 (matched 100) / 0.3158 (matched 200)
- GPT-5.5 macro-F1 = 0.5523 (matched 100)
- DeepSeek-V3 macro-F1 = 0.5270 (200) / 0.5248 (matched 100)
- R4 captures 8/24 LLM-missed strong_action cases (matched 100)
- rule_scalar mild_vs_strong ROC-AUC = 0.5054 (222 samples) / 0.5062 (alt calculation)
- llm_scalar_proxy mild_vs_strong ROC-AUC = 0.5874 (100 samples)
- Realism audit: 0.2% high-risk, 2.0% medium-risk (444 claims)
- Low-prevalence R4 recall: 0.3626 (1%), 0.3606 (3%), 0.3585 (5%), 0.3632 (10%), 0.3621 (15%), 0.3605 (20%)
- Low-prevalence FP/TP: 158.3 (1%), 44.7 (3%), 25.6 (5%), 11.7 (10%), 7.4 (15%), 5.2 (20%)

---

## 4. Forbidden phrases (verified absent)

- "R4 beats LLM overall"
- "official RIGOURATE reproduction completed"
- "gold validated"
- "natural prevalence corpus"
- "SimClaim reflects real-world class distribution"
- "mild/strong boundary is naturally objective"
- "R4 detects high-risk overclaims as standalone detector"

---

## 5. Garbled char check

Verified: 0 garbled characters (搂, 魏, 鈮, 鈭, 鈥, etc.) in the V3.16 .md file.

---

## 6. Quality checks

- No new experiments: PASS
- No API calls: PASS
- No gold annotation: PASS
- No new model training: PASS
- No threshold retuning: PASS
- No change to any §VI number: PASS
- No change to any §VIII.D number: PASS
- No change to §VII.G criteria: PASS
- No claim that R4 beats LLM overall: PASS
- No claim of official RIGOURATE reproduction: PASS
- No claim of gold validation: PASS
- No claim that SimClaim reflects natural class distribution: PASS
- No claim that mild/strong boundary is naturally objective: PASS
- No claim that R4 detects high-risk overclaims as standalone detector: PASS
- JSON / CSV / MD readable: PASS
- No garbled chars: PASS

---

## 7. Output files

1. `CESE_OCN_V3_16_no_gold_evidence_integration.md` — paper main text
2. `CESE_OCN_V3_16_no_gold_evidence_integration.docx` — docx export
3. `V3_16_change_log.md` — this file
4. `V3_16_consistency_gate.json` — consistency gate
