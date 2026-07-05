import importlib.util
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASE_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_pilot_small_baselines.py"

spec = importlib.util.spec_from_file_location("v4_baselines", BASE_SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v4b_pilot" / "candidates" / "simclaim_hardpair_v4b_pilot_candidates.csv"
mod.EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v4b_pilot_small_baselines"
mod.METRIC_DIR = mod.EXP_ROOT / "metrics"
mod.PRED_DIR = mod.EXP_ROOT / "predictions"
mod.REPORT_DIR = mod.EXP_ROOT / "reports"
mod.METRICS_CSV = mod.METRIC_DIR / "v4b_pilot_small_data_baseline_metrics.csv"
mod.PER_CLASS_CSV = mod.METRIC_DIR / "v4b_pilot_small_data_baseline_per_class_f1.csv"
mod.PRED_CSV = mod.PRED_DIR / "v4b_pilot_small_data_baseline_predictions.csv"
mod.SUMMARY_JSON = mod.REPORT_DIR / "v4b_pilot_small_data_baseline_summary.json"
mod.REPORT_MD = mod.REPORT_DIR / "v4b_pilot_small_data_baseline_report.md"


if __name__ == "__main__":
    mod.run()
