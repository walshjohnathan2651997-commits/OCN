import importlib.util
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASE_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "analyze_v4_pilot_leakage.py"

spec = importlib.util.spec_from_file_location("v4_leakage", BASE_SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.CANDIDATES_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
mod.METRICS_REPORT = ROOT / "experiments" / "simclaim_hardpair_v4b_pilot_small_baselines" / "reports" / "v4b_pilot_small_data_baseline_report.md"
mod.OUT_AUDIT = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "audit" / "v4b_pilot_claim_only_leakage_terms.csv"
mod.OUT_REPORT = ROOT / "reports" / "simclaim_hardpair_v4b_pilot" / "v4b_pilot_gate_and_leakage_report.md"
mod.OUT_SUMMARY = ROOT / "reports" / "simclaim_hardpair_v4b_pilot" / "v4b_pilot_gate_and_leakage_summary.json"


if __name__ == "__main__":
    mod.main()
