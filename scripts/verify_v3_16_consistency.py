"""Verify V3.16 consistency: forbidden phrases must NOT appear as positive claims.

The V3.16 changes paragraph contains enumeration like "no claim that R4 beats LLM
overall, no claim of ...". These are *negative* statements, not positive violations.
We check the 60-character context before each occurrence for a negation qualifier.
"""
import json
import re
import sys
from pathlib import Path

OUT_DIR = Path(r"D:\ocn\paper_versions_ordered\V3_16_no_gold_evidence_integration")
MD = OUT_DIR / "CESE_OCN_V3_16_no_gold_evidence_integration.md"
GATE = OUT_DIR / "V3_16_consistency_gate.json"

text = MD.read_text(encoding="utf-8")
text_lower = text.lower()

# (phrase, [allowed_negation_prefixes])
# A match is OK if any of the allowed prefixes appears in the 60-char window
# immediately before the phrase occurrence.
forbidden_checks = [
    ("r4 beats llm overall",
     ["no claim that ", "not ", "never "]),
    ("official rigourate reproduction completed",
     []),
    ("gold validated",
     []),
    ("natural prevalence corpus",
     ["not a natural-prevalence corpus", "not a natural prevalence corpus", "not "]),
    ("simclaim reflects real-world class distribution",
     ["no claim that ", "not ", "never "]),
    ("mild/strong boundary is naturally objective",
     ["no claim that ", "not ", "never "]),
    ("r4 detects high-risk overclaims as standalone detector",
     ["no claim that ", "not ", "never "]),
]

print("=" * 70)
print("V3.16 CONSISTENCY VERIFICATION — Forbidden phrases in context")
print("=" * 70)
all_ok = True
results = {}
for phrase, allowed_prefixes in forbidden_checks:
    occurrences = []
    start = 0
    while True:
        idx = text_lower.find(phrase, start)
        if idx == -1:
            break
        ctx_start = max(0, idx - 60)
        context = text_lower[ctx_start:idx]
        is_qualified = any(prefix in context for prefix in allowed_prefixes) if allowed_prefixes else False
        occurrences.append({
            "pos": idx,
            "qualified": is_qualified,
            "context": context[-40:],
        })
        start = idx + len(phrase)

    bad = [o for o in occurrences if not o["qualified"]]
    status = "PASS" if not bad else "FAIL"
    if bad:
        all_ok = False
    print(f"[{status}] '{phrase}': {len(occurrences)} total, {len(bad)} unqualified")
    for o in bad:
        print(f"    pos {o['pos']}: ...{o['context']!r}")
    results[phrase] = (len(bad) == 0)

print("=" * 70)
print(f"Overall forbidden-phrase check: {'ALL PASS' if all_ok else 'SOME FAILED'}")
print("=" * 70)

# Garbled char check
garbled_chars = ["搂", "魏", "鈮", "鈭", "鈥", "锛", "鏍", "璁", "瀹", "鐢", "鐨", "銆"]
garbled_found = [c for c in garbled_chars if c in text]
garbled_zero = len(garbled_found) == 0
print(f"Garbled chars: {'NONE' if garbled_zero else garbled_found}")

# Key numbers check
key_numbers = {
    "rule_scalar_mild_vs_strong_roc": "0.5054" in text or "0.5062" in text,
    "llm_scalar_proxy_mild_vs_strong_roc": "0.5874" in text,
    "r4_strong_f1": "0.3967" in text,
    "rule_scalar_strong_f1": "0.2996" in text,
    "llm_strong_f1": "0.0769" in text,
    "r4_captures_8_of_24": "8/24" in text,
    "realism_high_risk_0_2pct": "0.2%" in text,
    "realism_medium_risk_2_0pct": "2.0%" in text,
    "low_prev_recall_0_36": "0.3626" in text or "0.3632" in text,
    "fp_tp_1pct_158_3": "158.3" in text,
    "fp_tp_5pct_25_6": "25.6" in text,
    "fp_tp_10pct_11_7": "11.7" in text,
    "fp_tp_15pct_7_4": "7.4" in text,
    "fp_tp_20pct_5_2": "5.2" in text,
}
key_numbers_verified = all(key_numbers.values())
print(f"Key numbers verified: {key_numbers_verified}")
for k, v in key_numbers.items():
    print(f"  [{'OK' if v else 'MISS'}] {k}")

# Update gate JSON
gate = json.loads(GATE.read_text(encoding="utf-8"))
gate["garbled_chars_zero"] = garbled_zero
gate["key_numbers_verified"] = key_numbers_verified
gate["no_gold_claim"] = results.get("gold validated", True)
gate["no_official_rigourate_claim"] = results.get("official rigourate reproduction completed", True)
gate["no_natural_distribution_claim"] = (
    results.get("natural prevalence corpus", True) and
    results.get("simclaim reflects real-world class distribution", True)
)
gate["no_r4_overall_beats_llm_claim"] = results.get("r4 beats llm overall", True)
gate["low_prevalence_numbers_correct"] = all([
    "158.3" in text, "25.6" in text, "11.7" in text, "7.4" in text, "5.2" in text
])
gate["forbidden_phrases_check"] = {
    "r4_beats_llm_overall": results.get("r4 beats llm overall", True),
    "official_rigourate_reproduction": results.get("official rigourate reproduction completed", True),
    "gold_validated": results.get("gold validated", True),
    "natural_prevalence_corpus": results.get("natural prevalence corpus", True),
    "simclaim_reflects_real_world": results.get("simclaim reflects real-world class distribution", True),
    "mild_strong_naturally_objective": results.get("mild/strong boundary is naturally objective", True),
    "r4_standalone_detector": results.get("r4 detects high-risk overclaims as standalone detector", True),
}
gate["recommended_current_version"] = "V3.16"

GATE.write_text(json.dumps(gate, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"\nUpdated: {GATE.name}")

print(f"\n{'='*70}")
print(f"FINAL: {'ALL CHECKS PASS' if all_ok and garbled_zero and key_numbers_verified else 'SOME FAILED'}")
print(f"{'='*70}")

sys.exit(0 if (all_ok and garbled_zero and key_numbers_verified) else 1)
