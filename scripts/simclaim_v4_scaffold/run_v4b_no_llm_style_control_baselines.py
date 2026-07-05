import importlib.util
from pathlib import Path


ROOT = Path(r"D:\ocn")
BASE_SCRIPT = ROOT / "scripts" / "simclaim_v4_scaffold" / "run_v4_pilot_small_baselines.py"

spec = importlib.util.spec_from_file_location("v4_baselines", BASE_SCRIPT)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

mod.INPUT_CSV = ROOT / "data" / "simclaim_hardpair_v4b_no_llm_style_control" / "candidates" / "simclaim_hardpair_v4b_no_llm_style_control_600.csv"
mod.EXP_ROOT = ROOT / "experiments" / "simclaim_hardpair_v4b_no_llm_style_control_baselines"
mod.METRIC_DIR = mod.EXP_ROOT / "metrics"
mod.PRED_DIR = mod.EXP_ROOT / "predictions"
mod.REPORT_DIR = mod.EXP_ROOT / "reports"
mod.METRICS_CSV = mod.METRIC_DIR / "style_control_baseline_metrics.csv"
mod.PER_CLASS_CSV = mod.METRIC_DIR / "style_control_per_class_f1.csv"
mod.PRED_CSV = mod.PRED_DIR / "style_control_predictions.csv"
mod.SUMMARY_JSON = mod.REPORT_DIR / "style_control_summary.json"
mod.REPORT_MD = mod.REPORT_DIR / "style_control_report.md"


if __name__ == "__main__":
    mod.run()
