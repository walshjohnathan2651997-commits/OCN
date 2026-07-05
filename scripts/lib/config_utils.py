"""config_utils.py — Shared config loading for V3.17 confidential pipeline.

Provides a single source of truth for:
  - loading YAML configs
  - resolving paths relative to project_root
  - asserting confidential guards (no_api, no_network, no_training)
  - writing run_config.json to output directories

Usage from a script in scripts/:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    from config_utils import load_and_validate, resolve_path, write_run_config, print_guards

    config = load_and_validate(args.config)
    print_guards(config)
    output_dir = resolve_path(config, "smart_queue_dir")
    write_run_config(output_dir, config, "run_lightweight_smart_queue_v1.py")
"""

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DEFAULT_CONFIG_PATH = REPO_ROOT / "configs" / "v3_17_confidential_default.yaml"
TOY_CONFIG_PATH = REPO_ROOT / "configs" / "toy_demo.yaml"

REQUIRED_CONFIG_KEYS = [
    "project_root",
    "private_pdf_dir",
    "candidate_csv",
    "pdf_corpus_dir",
    "retrieval_dir",
    "canonicalizer_dir",
    "review_queue_dir",
    "risk_ranking_dir",
    "smart_queue_dir",
    "leakage_audit_dir",
    "toy_data_dir",
]

REQUIRED_GUARDS = ["no_api", "no_network", "no_training"]

DEFAULT_FORBIDDEN_SCORING_FIELDS = [
    "true_label",
    "is_strong_action",
    "oracle_hit",
    "candidate_label_guess",
    "final_label",
    "gold_label",
    "human_audited",
    "evidence_text",
    "evidence_text_sha256",
]


def load_config(path=None):
    """Load a YAML config file. If path is None, use the default config."""
    if yaml is None:
        raise ImportError(
            "PyYAML is required for config loading. Install: pip install pyyaml"
        )
    if path is None:
        path = DEFAULT_CONFIG_PATH
    path = Path(path)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    if config is None:
        config = {}
    config["_config_source_path"] = str(path)
    return config


def resolve_path(config, key):
    """Resolve a path value from config, relative to project_root.

    Returns a Path object or None if the key is absent/None.
    Absolute paths are returned as-is; relative paths are joined to
    config['project_root'] (which itself is relative to REPO_ROOT if not
    absolute).
    """
    if key not in config:
        return None
    val = config[key]
    if val is None:
        return None
    val = Path(val)
    if val.is_absolute():
        return val
    project_root = config.get("project_root", ".")
    pr = Path(project_root)
    if not pr.is_absolute():
        pr = (REPO_ROOT / pr).resolve()
    return (pr / val).resolve()


def ensure_dir(path):
    """Create a directory (and parents) if it doesn't exist. Returns Path or None."""
    if path is None:
        return None
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def assert_confidential_guards(config):
    """Raise ValueError if any required guard is not True."""
    for guard in REQUIRED_GUARDS:
        val = config.get(guard)
        if val is not True:
            raise ValueError(
                f"Confidential guard '{guard}' must be True, got: {val!r}. "
                f"The V3.17 pipeline requires no_api=true, no_network=true, no_training=true."
            )


def write_run_config(output_dir, config, script_name, extra=None):
    """Write run_config.json to output_dir with effective config and metadata.

    extra: optional dict merged into the run_config (e.g. selected_profile,
    toy_mode flag, overridden paths).
    """
    output_dir = ensure_dir(Path(output_dir))
    run_config = {
        "script_name": script_name,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_source": config.get("_config_source_path", "unknown"),
        "guards": {g: config.get(g) for g in REQUIRED_GUARDS},
        "no_original_data_modification": config.get("no_original_data_modification", True),
        "forbidden_scoring_fields": config.get(
            "forbidden_scoring_fields", DEFAULT_FORBIDDEN_SCORING_FIELDS
        ),
        "paths": {
            k: str(config[k]) for k in REQUIRED_CONFIG_KEYS if k in config and config[k] is not None
        },
    }
    if extra:
        run_config.update(extra)
    run_config_path = output_dir / "run_config.json"
    with open(run_config_path, "w", encoding="utf-8") as f:
        json.dump(run_config, f, indent=2, ensure_ascii=False)
    return run_config_path


def print_guards(config):
    """Print the four confidential guard values at script startup."""
    print(f"no_api: {config.get('no_api')}", flush=True)
    print(f"no_network: {config.get('no_network')}", flush=True)
    print(f"no_training: {config.get('no_training')}", flush=True)
    print(f"no_original_data_modification: {config.get('no_original_data_modification', True)}", flush=True)


def load_and_validate(config_path=None, toy_mode=False):
    """Load config, validate guards, and return it.

    If config_path is None and toy_mode is True, use the toy demo config.
    If config_path is None and toy_mode is False, use the default config.
    """
    if config_path is None:
        config_path = TOY_CONFIG_PATH if toy_mode else DEFAULT_CONFIG_PATH
    config = load_config(config_path)
    assert_confidential_guards(config)
    return config


def default_config_for_toy(toy_mode):
    """Return the default config path appropriate for the toy flag."""
    return TOY_CONFIG_PATH if toy_mode else DEFAULT_CONFIG_PATH
