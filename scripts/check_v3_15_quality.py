"""V3.15 §12 quality checks — 10 mandatory checks."""
import os
import re
import json
import zipfile

OUT_DIR = r"D:\ocn\paper_versions_ordered\V3_15_hierarchical_taxonomy_revision"
MD = os.path.join(OUT_DIR, "CESE_OCN_V3_15_hierarchical_taxonomy_revision.md")
DOCX = os.path.join(OUT_DIR, "CESE_OCN_V3_15_hierarchical_taxonomy_revision.docx")
V3_14_MD = r"D:\ocn\paper_versions_ordered\V3_14_mainline_locked_consistency_audit\CESE_OCN_V3_14_mainline_locked.md"

with open(MD, "r", encoding="utf-8") as f:
    md = f.read()

checks = []

# Check 1: no garbled chars (no CJK, valid encoding)
cjk = re.findall(r"[\u4e00-\u9fff\ufffd]", md)
checks.append(("1. no_garbled_chars", len(cjk) == 0, "CJK/replacement chars: " + str(len(cjk))))

# Check 2: mild_scope NOT claimed naturally stable
# Allow disclaimers ("not claimed to be", "do not assume", "not a naturally stable", "no claim that")
# Violation = affirmative claim "mild_scope is naturally stable/discrete" WITHOUT negation
violations_2 = []
for line_num, line in enumerate(md.split("\n"), 1):
    if re.search(r"mild_scope[^.]*naturally (stable|discrete)", line, re.IGNORECASE):
        # Check if it's a negation/disclaimer (broadened to include "no claim that", "not claimed")
        if not re.search(r"(not|do not|don.t|never|no longer|isn.t|is not|no claim that|not claimed|do not assume).{0,60}naturally (stable|discrete)|not claimed to be|do not assume|no claim that", line, re.IGNORECASE):
            violations_2.append((line_num, line[:120]))
checks.append(("2. mild_scope_not_claimed_naturally_stable", len(violations_2) == 0, str(len(violations_2)) + " violations"))

# Check 3: four operational labels NOT deleted (all 4 must appear)
labels = ["supported", "mild_scope_overclaim", "strong_action_overclaim", "contradiction_candidate"]
missing = [l for l in labels if l not in md]
checks.append(("3. four_operational_labels_not_deleted", len(missing) == 0, "missing: " + str(missing)))

# Check 4: experimental numbers unchanged (count each preserved number)
preserved = {
    "0.3967": 15,  # V3.14 count
    "0.0769": 8,
    "0.3280": 5,
    "0.5523": 5,
    "0.3000": 4,
    "0.2408": 4,
    "0.2231": 3,
    "0.4562": 2,
    "0.2062": 2,
    "0.4238": 3,
}
num_issues = []
for num, expected in preserved.items():
    actual = md.count(num)
    # Allow >= expected (numbers may appear in new disclaimers describing preservation)
    # but flag if FEWER (means a number was removed)
    if actual < expected:
        num_issues.append(num + ": " + str(actual) + " < " + str(expected))
checks.append(("4. experimental_numbers_unchanged", len(num_issues) == 0, str(num_issues)))

# Check 5: three-class fallback NOT written as executed
# Violation = "fell back to" / "executed the fallback" / "applied the three-class" in past tense as done
fallback_executed = []
for line_num, line in enumerate(md.split("\n"), 1):
    if re.search(r"(fell back to|executed the fallback|applied the (3|three)-class fallback|downgraded to (3|three)-class)", line, re.IGNORECASE):
        fallback_executed.append((line_num, line[:120]))
checks.append(("5. three_class_fallback_not_executed", len(fallback_executed) == 0, str(fallback_executed)))

# Check 6: gold NOT claimed complete
# Violation = "gold is complete/done/finished" as a CURRENT claim (not conditional future success path)
# Allow conditional success-path language ("success path", "proceeds to", "if ... then", "will be")
gold_complete_violations = []
for line_num, line in enumerate(md.split("\n"), 1):
    # Only flag affirmative present-tense claims that gold is complete
    if re.search(r"gold (is |was |has been )(complete|done|finished|performed|executed)", line, re.IGNORECASE):
        gold_complete_violations.append((line_num, line[:120]))
    # "gold-validated" is allowed ONLY in conditional success-path context (§VII.G criterion 6)
    elif re.search(r"gold-validated|gold-confirmed", line, re.IGNORECASE):
        if not re.search(r"(success path|proceeds to|if |when |after |will be |pre-registered|criterion)", line, re.IGNORECASE):
            gold_complete_violations.append((line_num, line[:120]))
checks.append(("6. gold_not_claimed_complete", len(gold_complete_violations) == 0, str(gold_complete_violations)))

# Check 7: R4 macro-F1 < LLM fact preserved
# Must contain both "0.3280" and "0.5523" and a statement that R4 is lower
r4_lower_preserved = "0.3280" in md and "0.5523" in md and re.search(r"R4.{0,80}(lower|substantially lower|macro-F1.{0,40}0\.3280.{0,40}0\.5523)", md, re.IGNORECASE)
checks.append(("7. r4_macro_f1_below_llm_fact_preserved", r4_lower_preserved, ""))

# Check 8: non-gold checks caveat preserved (§VIII.D)
nongold_caveat = "non-gold" in md.lower() or "do not replace gold adjudication" in md.lower()
checks.append(("8. non_gold_checks_caveat_preserved", nongold_caveat, ""))

# Check 9: docx generated successfully
docx_ok = os.path.exists(DOCX) and os.path.getsize(DOCX) > 0
if docx_ok:
    try:
        with zipfile.ZipFile(DOCX, "r") as z:
            namelist = z.namelist()
            docx_ok = "word/document.xml" in namelist and z.testzip() is None
    except Exception as e:
        docx_ok = False
checks.append(("9. docx_generated_successfully", docx_ok, "size=" + str(os.path.getsize(DOCX)) if os.path.exists(DOCX) else "missing"))

# Check 10: old version files unchanged
v3_14_size = os.path.getsize(V3_14_MD)
v3_14_unchanged = v3_14_size == 142965  # known V3.14 size
checks.append(("10. old_version_files_unchanged", v3_14_unchanged, "V3.14 MD size=" + str(v3_14_size)))

# Print results
print("=" * 70)
print("V3.15 §12 Quality Checks (10 mandatory)")
print("=" * 70)
all_pass = True
for name, passed, detail in checks:
    status = "PASS" if passed else "FAIL"
    if not passed:
        all_pass = False
    print(status + " " + name + (" | " + detail if detail else ""))
print()
print("OVERALL: " + ("ALL PASS" if all_pass else "FAILURES PRESENT"))
print("=" * 70)

# Also verify readiness gate 13 fields
with open(os.path.join(OUT_DIR, "hierarchical_taxonomy_revision_gate.json"), "r", encoding="utf-8") as f:
    gate = json.load(f)
required_fields = [
    "hierarchical_taxonomy_inserted", "flat_four_class_deemphasized", "mild_as_buffer_subtype",
    "strong_action_as_high_risk_subtype", "level1_level2_mapping_created",
    "fallback_to_3class_plus_binary_defined", "numbers_unchanged", "gold_not_claimed",
    "silver_not_gold", "old_files_unchanged", "docx_generated",
    "main_remaining_risk", "next_required_action"
]
missing_fields = [f for f in required_fields if f not in gate]
print()
print("Readiness gate 13 required fields: " + ("ALL PRESENT" if not missing_fields else "MISSING: " + str(missing_fields)))
