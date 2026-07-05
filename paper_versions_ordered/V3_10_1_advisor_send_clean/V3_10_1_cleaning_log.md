# V3.10.1 Cleaning Log

**Source:** V3.10 Advisor-Ready Silver-Stage
**Target:** V3.10.1 Advisor-Send Encoding-Verified Clean
**Date:** 2026-07-04
**Pass type:** Encoding clean + format verification + advisor-send package assembly.
**No change to paper mainline, no change to any experimental number, no change to taxonomy, no change to positioning, no new experiments, no API calls, no gold annotation, no silver-to-gold relabeling. V3.10 is preserved unchanged.**

---

## 1. Mojibake scan — full V3.10 directory

**Patterns searched (17 total — listed here by description, not by literal glyph, to keep this log itself mojibake-free):**
- Pattern 1: garbled section sign / curly quote artifact (byte sequence from mis-decoded U+00A7 or U+201C/U+201D)
- Pattern 2: garbled section sign variant (byte sequence from mis-decoded U+00A7)
- Pattern 3: garbled kappa (byte sequence from mis-decoded U+03BA)
- Pattern 4: garbled greater-or-equal (byte sequence from mis-decoded U+2265)
- Pattern 5: garbled dash variant (byte sequence from mis-decoded U+2014 or U+2013)
- Pattern 6: garbled en-dash / quote artifact (byte sequence from mis-decoded U+2013 or U+2018)
- Pattern 7: garbled em-dash variant (byte sequence from mis-decoded U+2014)
- Pattern 8: garbled bracket artifact (byte sequence from mis-decoded U+005B/U+005D)
- Pattern 9: garbled quote variant (byte sequence from mis-decoded U+201C/U+201D)
- Pattern 10: garbled whitespace artifact (byte sequence from mis-decoded U+00A0)
- Pattern 11: garbled comma artifact (byte sequence from mis-decoded U+FF0C or U+002C)
- Pattern 12: garbled period artifact (byte sequence from mis-decoded U+3002 or U+002E)
- Pattern 13: garbled bullet artifact (byte sequence from mis-decoded U+2022)
- Pattern 14: garbled definition artifact (byte sequence from mis-decoded U+2261 or U+2255)
- Pattern 15: garbled quote variant 2 (byte sequence from mis-decoded U+2018/U+2019)
- Pattern 16: garbled positional artifact (byte sequence from mis-decoded positional punctuation)
- Pattern 17: garbled timestamp artifact (byte sequence from mis-decoded date/time separators)

**Search method:** `ripgrep` over the entire `V3_10_advisor_ready_silver_stage\` directory, plus a Python `Counter`-based non-ASCII inventory of every file.

**Result:** **0 matches** across all V3.10 files (md, docx XML parts, advisor note, revision log, readiness gate JSON).

**Conclusion:** V3.10 was already encoding-clean. V3.10.1 inherits the clean content and adds a verification stamp.

---

## 2. Non-ASCII character inventory (main md)

All non-ASCII characters in `CESE_OCN_V3_10_1_advisor_send_clean.md` are legitimate typographic / scientific symbols:

| Codepoint | Glyph | Count | Usage |
|-----------|-------|-------|-------|
| U+2588 | █ | 277 | ASCII-art decision trees / routing diagrams |
| U+2014 | — | 92 | Em dash, parenthetical asides |
| U+00A7 | § | 60 | Section sign (§VI, §VII, §VIII.A, etc.) |
| U+2192 | → | 28 | Right arrow, routing descriptions |
| U+2265 | ≥ | 14 | Greater-or-equal, thresholds and criteria |
| U+03BA | κ | 11 | Cohen's kappa, inter-annotator agreement |
| U+2264 | ≤ | 7 | Less-or-equal, FP/TP thresholds |
| U+2013 | – | 4 | En dash, ranges (e.g., Tables G1–G3) |
| U+00B1 | ± | 2 | Plus-minus, CI bounds |
| U+03B1 | α | 2 | Alpha, significance level |

**No garbled bytes, no BOM, no double-encoded sequences.**

---

## 3. BOM check

All V3.10.1 output files verified to start with their intended first character (not U+FEFF):
- Main md starts with `# Evidence Sufficiency...`
- Advisor note starts with `# 导师审阅说明...`
- Cleaning log starts with `# V3.10.1 Cleaning Log`
- Readiness gate JSON starts with `{`

---

## 4. Content integrity checks

### 4.1 File sizes (must not be abnormally short)

| File | V3.10 size | V3.10.1 size | Status |
|------|-----------|-------------|--------|
| Main .md | 83393 bytes | 84688 bytes | OK (larger, due to added changes note + longer version string) |
| Main .docx | 31560 bytes | 31792 bytes | OK (larger, mirrors md growth) |
| Advisor note | 7233 bytes | 7377 bytes | OK (larger, due to version string update) |

No file is abnormally short. Content is preserved.

### 4.2 `pre-gold` occurrence count

- V3.10: 4 occurrences (Abstract, §VI opener, §VII opener, §X Conclusion)
- V3.10.1: **4 occurrences** (same four locations, unchanged)

### 4.3 Experimental numbers — unchanged

The following key numbers were verified to be byte-identical between V3.10 and V3.10.1 (the V3.10.1 pass did not touch the body of §VI or any results table):
- R4 strong_F1 = 0.3967
- LLM strong_F1 = 0.0769
- R4 baseline strong_F1 = 0.2408
- R4 macro_F1 (matched 100) = 0.3280
- GPT-5.5 macro_F1 (matched 100) = 0.5523
- DeepSeek macro_F1 (200) = 0.5270
- Bootstrap CI = [0.1058, 0.1988]
- Seeds positive = 10/10
- Ablation: A0=0.3934, A1=0.3648, A2=0.4209
- FP/TP ratio ≈ 4.9 (122 FP / ~25 true strong_action)
- Author sanity audit: 25/40 (62.5%) questionable

### 4.4 No new gold/final/human fields

- No `gold_label`, `final_label`, or `human_audited` field added anywhere.
- Tables G1–G3 still marked `TO_BE_FILLED_AFTER_GOLD`.
- No silver label relabeled as gold.

---

## 5. JSON validation

`V3_10_1_readiness_gate.json` validated with `json.load()` — parses without error.

---

## 6. Version-string updates (only metadata, not mainline)

The only textual changes from V3.10 to V3.10.1 are:
1. Title page version line: `V3.10` → `V3.10.1 ... (advisor send, encoding-verified clean)`
2. Appended a `**Changes from V3.10 (V3.10.1):**` paragraph documenting the clean pass.
3. Advisor cover note header version reference updated to V3.10.1.
4. Advisor cover note file-path references updated to the V3.10.1 directory.

**No sentence in the paper mainline (Abstract through Conclusion, §I–§X, Appendices) was altered.**

---

## 7. Source preservation

- `D:\ocn\paper_versions_ordered\V3_10_advisor_ready_silver_stage\` — preserved unchanged (read-only source for this pass).
- `D:\ocn\paper_versions_ordered\V3_9_pre_gold_complete\` — preserved unchanged.
- V3.8 and earlier — not touched.

---

## 8. Final verification summary

| Check | Result |
|-------|--------|
| Mojibake search (17 patterns, full V3.10 dir) | 0 matches |
| Mojibake search (17 patterns, V3.10.1 outputs) | 0 matches |
| BOM in any output file | None |
| Main md size vs V3.10 | 84688 ≥ 83393 (not shorter) |
| Main docx size vs V3.10 | 31792 ≥ 31560 (not shorter) |
| `pre-gold` count | 4 (unchanged) |
| Experimental numbers | Unchanged (byte-identical in body) |
| New gold/final/human fields | None added |
| JSON valid | Yes |
| Advisor note is normal Chinese | Yes, no mojibake |
| V3.10 modified | No |
| V3.9 / V3.8 modified | No |
| Experiments / API / gold | Not run |

---

## 9. Recommendation

**V3.10.1 is the advisor-send copy.** It is encoding-verified clean, content-identical to V3.10 in the paper mainline, and safe to send to the advisor.
