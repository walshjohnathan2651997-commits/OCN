import importlib.util
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASE_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_claim_generation.py"

spec = importlib.util.spec_from_file_location("v4_generation", BASE_SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.OUT_ROOT = ROOT / "data" / "simclaim_hardpair_v4b_pilot"
mod.OUT_CANDIDATES = mod.OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
mod.OUT_JSONL = mod.OUT_ROOT / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.jsonl"
mod.OUT_RAW = mod.OUT_ROOT / "raw_llm" / "v4b_claim_generation_raw_outputs.jsonl"
mod.OUT_AUDIT = mod.OUT_ROOT / "audit" / "v4b_claim_generation_audit.csv"
mod.OUT_REPORT = ROOT / "reports" / "simclaim_hardpair_v4b_pilot" / "v4b_claim_generation_report.md"


if __name__ == "__main__":
    mod.main()
