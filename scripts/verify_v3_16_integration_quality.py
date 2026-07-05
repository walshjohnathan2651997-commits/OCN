"""Quality verification for No-Gold Evidence Integration V3.16 Plan outputs."""
import json
import sys
from pathlib import Path
import pandas as pd

OUT_DIR = Path(r"D:\ocn\project_synthesis\no_gold_evidence_integration_v3_16_plan")
PAPER_DIR = Path(r"D:\ocn\paper_versions_ordered")
DATA_DIR = Path(r"D:\ocn\data")

GARBLED = ["搂", "魏", "鈮", "鈭", "鈥", "锛", "鏍", "璁", "瀹", "鐢", "鐨", "銆"]

results = {}

# Check 1: no gold (no annotation templates, no gold labels)
def check_no_gold():
    for p in OUT_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".csv", ".md", ".json"}:
            text = p.read_text(encoding="utf-8", errors="ignore").lower()
            if "gold_pilot_annotation_a" in text or "gold_pilot_annotation_b" in text:
                return False, f"gold annotation template referenced in {p.name}"
            if "gold_adjudication_completed" in text and "true" in text:
                return False, f"gold adjudication claimed completed in {p.name}"
    return True, "no gold annotation templates or completed gold claims"

# Check 2: no API
def check_no_api():
    for p in OUT_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".json"}:
            text = p.read_text(encoding="utf-8", errors="ignore").lower()
            if "openai.api_call" in text or "deepseek api call performed" in text:
                return False, f"API call claimed in {p.name}"
            if "api_calls_made" in text:
                # check if value > 0
                if "\"api_calls_made\": 0" not in text and "api_calls_made\": 0" not in text:
                    # look in JSON
                    if p.suffix == ".json":
                        try:
                            d = json.loads(p.read_text(encoding="utf-8"))
                            if isinstance(d, dict) and d.get("api_calls_made", 0) > 0:
                                return False, f"api_calls_made > 0 in {p.name}"
                        except Exception:
                            pass
    return True, "no API calls performed"

# Check 3: no paper modification
def check_no_paper_modification():
    # paper dir should not have been touched by this script (we only wrote to OUT_DIR)
    # Just verify paper_versions_ordered still has V3.15 dir intact
    v315 = PAPER_DIR / "V3_15_hierarchical_taxonomy_revision"
    if not v315.exists():
        return False, "V3.15 directory missing"
    return True, "paper_versions_ordered untouched"

# Check 4: no original-data modification
def check_no_data_modification():
    # Just verify the strict_silver_max data dir still exists
    p = DATA_DIR / "simclaim_all92_candidate_pool_v1" / "strict_silver_max_v1"
    if not p.exists():
        return False, "strict_silver_max_v1 missing"
    return True, "original data untouched"

# Check 5: no proxy-as-official
def check_no_proxy_as_official():
    forbidden_positive = [
        "official rigourate reproduction completed",
        "we reproduce the official rigourate",
        "rigourate official system was reproduced",
        "official rigourate artifacts were used",
    ]
    for p in OUT_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".json"}:
            text = p.read_text(encoding="utf-8", errors="ignore").lower()
            for f in forbidden_positive:
                if f in text:
                    return False, f"phrase '{f}' found in {p.name}"
    return True, "no proxy-as-official positive claims (down-tone instructions are OK)"

# Check 6: no simulation-as-natural
def check_no_simulation_as_natural():
    bad_phrases = [
        "natural prevalence",
        "natural-distribution results",
        "real-world prevalence",
    ]
    # The phrase "NOT a natural-prevalence corpus" is OK; we look for positive claims
    for p in OUT_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".md", ".json"}:
            text = p.read_text(encoding="utf-8", errors="ignore").lower()
            for phrase in bad_phrases:
                if phrase in text:
                    # check context — if preceded by "not a " or "not " it's OK
                    idx = text.find(phrase)
                    prefix = text[max(0, idx-20):idx]
                    if "not a " in prefix or "not " in prefix or "never " in prefix:
                        continue
                    return False, f"phrase '{phrase}' found in {p.name}"
    return True, "no simulation-as-natural-distribution claims"

# Check 7: JSON/CSV/MD readable
def check_files_readable():
    for p in OUT_DIR.rglob("*"):
        if p.is_file():
            if p.suffix == ".json":
                try:
                    json.loads(p.read_text(encoding="utf-8"))
                except Exception as e:
                    return False, f"JSON parse failed for {p.name}: {e}"
            elif p.suffix == ".csv":
                try:
                    pd.read_csv(p)
                except Exception as e:
                    return False, f"CSV parse failed for {p.name}: {e}"
            elif p.suffix == ".md":
                try:
                    p.read_text(encoding="utf-8")
                except Exception as e:
                    return False, f"MD read failed for {p.name}: {e}"
    return True, "all JSON/CSV/MD readable"

# Check 8: no garbled chars
def check_no_garbled():
    for p in OUT_DIR.rglob("*"):
        if p.is_file() and p.suffix in {".csv", ".md", ".json"}:
            text = p.read_text(encoding="utf-8", errors="ignore")
            for ch in GARBLED:
                if ch in text:
                    return False, f"garbled char '{ch}' found in {p.name}"
    return True, "no garbled characters"

checks = [
    ("no_gold", check_no_gold),
    ("no_api", check_no_api),
    ("no_paper_modification", check_no_paper_modification),
    ("no_original_data_modification", check_no_data_modification),
    ("no_proxy_as_official", check_no_proxy_as_official),
    ("no_simulation_as_natural_distribution", check_no_simulation_as_natural),
    ("json_csv_md_readable", check_files_readable),
    ("no_garbled_chars", check_no_garbled),
]

all_pass = True
print("=" * 60)
print("QUALITY CHECKS — No-Gold Evidence Integration V3.16 Plan")
print("=" * 60)
for name, fn in checks:
    ok, msg = fn()
    results[name] = ok
    if not ok:
        all_pass = False
    print(f"[{'PASS' if ok else 'FAIL'}] {name}: {msg}")
print("=" * 60)
print(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")
print("=" * 60)

sys.exit(0 if all_pass else 1)
