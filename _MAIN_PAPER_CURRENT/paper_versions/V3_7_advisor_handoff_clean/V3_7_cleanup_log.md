# V3.7 Cleanup Log — Advisor Handoff Clean

**Date:** 2026-07-04
**Source:** V3.6 (`D:\ocn\paper_versions_ordered\V3_6_case_figure_integrity_checked\`)
**Output:** V3.7 (`D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\`)
**Scope:** Final cleanup pass for advisor delivery. No new experiments, no API calls, no new data, no change to numeric results, no change to conclusions.

---

## 1. Spelling / encoding fixes

### EMNAACP → EMNLP/NAACL

- **Source of typo:** The string `EMNAACP` was found in `V3_6_case_figure_integrity_checked\V3_6_final_readiness_note.md` (3 occurrences, lines 96, 98, 102). It was a concatenation typo for `EMNLP/NAACL`.
- **V3.6 preservation:** V3.6 is preserved unchanged per user requirement. The typo in V3.6's sibling file is documented here but not fixed in V3.6.
- **V3.7 main paper check:** Verified 0 occurrences of `EMNAACP` in `CESE_OCN_V3_7_advisor_handoff_clean.md`. The main paper uses the correct `EMNLP/NAACL` form (visible in the references section, line 471: "NAACL-HLT").
- **V3.7 sibling files:** All V3.7 sibling files (advisor_cover_note.md, one_page_project_summary.md, reviewer_risk_brief.md) use the correct `EMNLP/NAACL` form. The advisor cover note explicitly mentions "EMNLP findings, NAACL findings" as candidate venues.

### Mojibake / replacement characters

- **V3.7 main paper check:** Searched for U+FFFD (replacement character, `\xef\xbf\xbd` UTF-8) — 0 occurrences in `CESE_OCN_V3_7_advisor_handoff_clean.md`.
- **V3.6 main paper check (source):** Verified 0 mojibake in V3.6 source. The copy to V3.7 preserved clean UTF-8.
- **Terminal display note:** Some terminals may display mojibake for box-drawing characters (e.g., `+---+`, `|`, `v` in Figure 2 ASCII art) when the terminal codepage is not UTF-8. This is a terminal display artifact, not a file encoding issue. The file itself is clean UTF-8.

### Other spelling

- No other spelling issues identified in the main paper. The text uses American English spelling consistently (e.g., "operationalize," "calibration," "adjudication").

## 2. Figure / table numbering unification

### Issue identified in V3.6

In V3.6, Table 2 was referenced for **both** taxonomy examples (in §I and §III.B) **and** the LLM judge comparison (in §VI.B). This created duplicate numbering.

### Fix applied in V3.7

- **Table 0** = taxonomy examples (8 cases, 2 per class). Located in §III.B. Referenced in §I contribution (i) and §I roadmap.
- **Table 1** = internal R4 targeted result (silver-label pilot, 444 claims, 10 seeds). Located in §VI.A.
- **Table 2** = LLM judge comparison on matched SimClaim samples. Located in §VI.B.
- **Table 3** = boundary audit summary (40-case author sanity audit). Located in §VI.C.

No duplicate table numbering remains.

### Figure numbering (consistent in V3.6, verified in V3.7)

- **Figure 1** = R4 method routing flow. Located in §IV.B.
- **Figure 2** = taxonomy decision tree. Located in §III.B.
- **Figure 3** = LLM vs. R4 strong_action gap. Located in §VI.B.

All figure references in the body text (§I introduction, §I roadmap, §III.B, §IV.B, §VI.B) are consistent with these assignments.

## 3. Citation placeholders

### Search performed

Searched V3.7 main paper for: `[REF]`, `TODO`, `citation needed`, `to be added`, `Author information`.

### Findings

- **`[REF]`:** 0 occurrences. All citations use numbered references `[1]`-`[26]` with a complete references section (§References).
- **`TODO`:** 0 occurrences.
- **`citation needed`:** 0 occurrences.
- **`to be added`:** 0 occurrences (after fix below).
- **`Author information`:** 1 occurrence (line 7). In V3.6 this read "Author information to be added before submission." In V3.7 this has been changed to **"Author information omitted for review draft"** per user requirement.

### References

The references section (§References) lists 26 numbered references (FEVER, SNLI, SciFact, RAGAs, ARES, G-Eval, MT-Bench, hedging detection, NLI calibration, etc.). No references are flagged as "to be finalized." No fabricated references were added in V3.7.

## 4. Version-mixup references

### V3.5 / V3.6 mentions in body text

Searched V3.7 main paper for `V3.5` and `V3.6`. Found 4 lines with mentions:

- **Line 5 (version header):** Explicitly describes V3.7 changes from V3.6. Intentional.
- **Line 121 (§III.B):** "The V3.6 case integrity audit replaced the V3.5 T2 mild case (TCB_008, number inflation...) with a clean scope-expansion case (SBV2-ALL92-G170-C02...)." Intentional historical reference explaining the case integrity audit.
- **Line 389 (§VIII limitations):** "The V3.5 root cause analysis shows that 12/25 questionable/unclear cases are genuinely hard boundary cases..." Intentional historical reference to the root cause analysis.
- **Line 425 (§VIII/appendix):** "The V3.6 appendix replaced V3.5 T2 (TCB_008, problematic number inflation) with SBV2-ALL92-G170-C02..." Intentional historical reference.

These references are **intentional** — they document the version evolution of the case integrity audit and root cause analysis. They are not version-mixup errors. They have been retained.

### Sibling file path references

The main paper references sibling files by name (e.g., `case_integrity_audit.csv`, `table_taxonomy_examples_v3_6_clean.csv`, `appendix_case_studies_v3_6_clean.md`, `high_risk_sample_bank.csv`, `trusted_case_bank.csv`, `author_sanity_audit_40.csv`). These are V3.6 filenames — they are the actual filenames in the V3.6 source directory and (where applicable) referenced as external artifacts. V3.7 does not rename these files (they are part of the V3.6 artifact set). The V3.7 output directory contains only the 7 new V3.7 files; the V3.6 artifact files remain in the V3.6 directory and are referenced by relative name in the paper.

## 5. Silver / gold preservation

### Verified

- All silver labels are explicitly labeled as silver throughout the paper.
- No claim of "gold" labels anywhere in the paper except in:
  - Explicit negation ("silver, not gold," "not as gold adjudications").
  - Future-work references to "gold adjudication," "gold pilot," "gold κ."
- The LLM under-detection finding is framed as "diagnostic evidence against silver labels, pending independent gold adjudication — not as an established property of LLM judges."
- No claim that R4 outperforms LLM judges overall. The paper explicitly states "R4 is not the strongest model on overall macro-F1 — LLM judges retain that."
- Forbidden-claims list (Appendix B) explicitly forbids "R4 outperforms GPT overall" / "R4 is stronger than LLMs on all metrics" / "silver labels are gold" / "established property of LLM judges."

## 6. New experiments / API calls / data

### Verified

- No new experiments were run for V3.7.
- No API calls were made for V3.7.
- No new data was generated for V3.7.
- No new algorithms were introduced for V3.7.
- All numeric results in V3.7 are identical to V3.6 (which are identical to V3.5 for the experiment results).

## 7. Files generated

V3.7 output directory (`D:\ocn\paper_versions_ordered\V3_7_advisor_handoff_clean\`) contains 7 files:

1. `CESE_OCN_V3_7_advisor_handoff_clean.md` — main paper (cleaned from V3.6).
2. `CESE_OCN_V3_7_advisor_handoff_clean.docx` — docx version (built via `D:\ocn\scripts\build_v3_7_docx.py`, zipfile+XML).
3. `advisor_cover_note.md` — 1121-word cover note for advisor / collaborator.
4. `one_page_project_summary.md` — one-page project summary (Title/Problem/Method/Dataset/Key results/Main limitation/Current readiness/Recommended next step).
5. `reviewer_risk_brief.md` — one-page reviewer risk brief (5 risks, each with risk / current mitigation / what would fully solve it).
6. `V3_7_cleanup_log.md` — this file.
7. `V3_7_file_manifest.csv` — manifest of all 7 files with file_name / file_type / purpose / ready_to_share / notes.

## 8. V3.6 preservation

### Verified

- V3.6 directory (`D:\ocn\paper_versions_ordered\V3_6_case_figure_integrity_checked\`) is unchanged: 10 files, total size unchanged, modification timestamps unchanged.
- The `EMNAACP` typo in V3.6's `V3_6_final_readiness_note.md` is preserved (not fixed in V3.6) per user requirement that V3.6 not be modified. The fix is documented in this log and the correct `EMNLP/NAACL` form is used in all V3.7 files.

## 9. Final checks

| # | Check | Status |
|---|---|---|
| 1 | V3.6 unchanged | ✅ Pass |
| 2 | V3.7 has 7 output files | ✅ Pass |
| 3 | EMNAACP fixed in V3.7 main paper | ✅ Pass (0 occurrences) |
| 4 | No mojibake in V3.7 main paper | ✅ Pass (0 U+FFFD) |
| 5 | Figure/table numbering unified | ✅ Pass (Table 0/1/2/3, Figure 1/2/3, no duplicates) |
| 6 | Silver not written as gold | ✅ Pass |
| 7 | No claim of R4 outperforming LLM overall | ✅ Pass |
| 8 | No new experiments/API/data | ✅ Pass |
| 9 | Docx generated | ✅ Pass (25575 bytes) |
| 10 | advisor_cover_note + one_page_summary ready to send | ✅ Pass |
