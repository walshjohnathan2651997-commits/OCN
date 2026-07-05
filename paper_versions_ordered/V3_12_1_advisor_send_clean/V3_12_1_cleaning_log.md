# V3.12.1 Cleaning Log

**Version:** V3.12.1 Advisor Send Clean
**Date:** 2026-07-04
**Base version:** V3.12 With Three Credibility Checks
**Type of change:** Encoding clean + minor wording stabilization only (no experimental changes, no structural changes)

---

## 1. Mojibake Scan

A full scan was performed for the 19 user-listed mojibake characters plus 6 additional common mojibake markers (Ã, â, ï, ¿, ½, U+FFFD replacement character).

| Mojibake character | Unicode | Source (UTF-8 misread as GBK) | Hits in V3.12 |
|---|---|---|---|
| 鈥 | U+9225 | from ' " — (U+2018/2019/201C/201D/2014) | 0 |
| 搂 | U+6367 | from § (U+00A7) | 0 |
| 魏 | U+9B4F | from κ (U+03BA) | 0 |
| 鈮 | U+922E | from ≥ (U+2265) | 0 |
| 鈭 | U+922D | from − (U+2212) | 0 |
| 螖 | U+8796 | from Δ (U+0394) | 0 |
| 寮 | U+5BEE | — | 0 |
| 涓 | U+6D93 | — | 0 |
| 閳 | U+95B3 | — | 0 |
| 鎼 | U+93FC | — | 0 |
| 榄 | U+6984 | — | 0 |
| 脗 | U+8117 | — | 0 |
| 锛 | U+951B | — | 0 |
| 銆 | U+9286 | — | 0 |
| 绋 | U+7ECB | — | 0 |
| 瀹 | U+7039 | — | 0 |
| 鍚 | U+935A | — | 0 |
| 浣 | U+6D63 | — | 0 |
| 鏄 | U+93C4 | — | 0 |
| Ã | U+00C3 | UTF-8 misread as Latin-1 | 0 |
| â | U+00E2 | UTF-8 misread as Latin-1 | 0 |
| ï | U+00EF | UTF-8 misread as Latin-1 | 0 |
| ¿ | U+00BF | UTF-8 misread as Latin-1 | 0 |
| ½ | U+00BD | UTF-8 misread as Latin-1 | 0 |
| U+FFFD | — | replacement character | 0 |

**Result: 0 mojibake hits.** V3.12 was already clean UTF-8 with proper Unicode characters. The proper Unicode characters present in the file are:

| Proper character | Unicode | Count | Meaning |
|---|---|---|---|
| § | U+00A7 | 75 | section sign |
| κ | U+03BA | 11 | kappa |
| Δ | U+0394 | 5 | delta |
| ≥ | U+2265 | 15 | greater-or-equal |
| − | U+2212 | 9 | minus sign |
| — | U+2014 | 109 | em dash |
| – | U+2013 | 15 | en dash |

No replacement was needed. The file was already encoding-clean.

## 2. Wording Stabilization

Two occurrences of "systematically under-detect" were softened to "consistently under-detect" to avoid over-strong language. The qualifier "under the tested prompts" / "under both tested prompt designs" was already present in both contexts, so no additional qualifier was added (avoiding redundancy).

| Location | Before | After |
|---|---|---|
| Abstract (line 16) | "generic LLM judges (GPT-5.5, DeepSeek-V3) **systematically under-detect** strong_action_overclaim" | "generic LLM judges (GPT-5.5, DeepSeek-V3) **consistently under-detect** strong_action_overclaim" |
| §I Introduction (line 26) | "they **systematically under-detect strong_action_overclaim under both tested prompt designs**" | "they **consistently under-detect strong_action_overclaim under both tested prompt designs**" |

**Main conclusion preserved:** The strong_action under-detection finding (LLM strong-F1 = 0.0769, recall 0.04; R4 strong-F1 = 0.3000) is unchanged. Only the adverb "systematically" → "consistently" was softened; the factual claim, the numbers, and the "under-detect" verb are all preserved.

## 3. Version Header Update

- **Before:** "V3.12 With Three Credibility Checks (validation-pending, protocol-locked)"
- **After:** "V3.12.1 Advisor Send Clean (validation-pending, protocol-locked)"
- **Added:** "Changes from V3.12" paragraph documenting the encoding-clean and wording-stabilization nature of this revision.

## 4. What Was NOT Changed

| Item | Status |
|---|---|
| §VI Results numbers (R4 strong-F1 0.3967, LLM 0.0769, macro-F1 0.3280/0.5523, etc.) | Preserved byte-identical |
| §VIII.D Three Core Credibility Checks | Preserved unchanged |
| Non-gold caveat ("These checks are non-gold robustness analyses") | Preserved |
| 50% retention caveat ("must *not* be reported as a robust pass") | Preserved |
| R4 macro-F1 < LLM fact (0.3280 vs 0.5523) | Preserved |
| Gold not yet performed fact | Preserved |
| §VII Pre-Registered Gold Validation Protocol | Unchanged |
| Frozen R4 thresholds | Unchanged |
| Taxonomy boundary rules | Unchanged |
| V3.12 source file | Preserved unchanged |
| V3.11, V3.10.1, V3.9 source files | Preserved unchanged |

## 5. Quality Verification

| Check | Result |
|---|---|
| Mojibake character scan (25 patterns) | 0 hits |
| md file size | 93772 bytes (V3.12: 93389 bytes; +383 bytes from version header + wording changes) |
| docx file size | 34118 bytes (V3.12: 33849 bytes; +269 bytes) |
| §VIII.D present | Yes |
| Non-gold caveat present | Yes |
| 50% retention caveat present | Yes |
| R4 macro-F1 0.3280 vs GPT 0.5523 present | Yes |
| Gold not done fact present | Yes |
| V3.12 unchanged | Yes (82599 → not touched; V3.12 md = 93389 bytes, not modified) |

## 6. Forbidden Actions Check

| Forbidden action | Status |
|---|---|
| Modify V3.12 original files | NOT done |
| Run experiments | NOT done |
| Call API | NOT done |
| Do gold annotation | NOT done |
| Change experimental numbers | NOT done |
| Delete three credibility checks | NOT done |
| Write non-gold as gold | NOT done |
| Delete R4 macro-F1 < LLM fact | NOT done |
| Delete 50% retention caveat | NOT done |
