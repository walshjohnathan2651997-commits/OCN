"""config_utils.py — Shared config loading for V3.17 confidential pipeline.

Provides a single source of truth for:
  - loading YAML configs
  - resolving paths relative to project_root
  - asserting confidential guards (no_api, no_network, no_training)
  - writing run_config.json to output directories
  - detecting private-data mode
  - blocking network requests outside private mode

Usage from a script in scripts/:

    import sys
    from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parent / "lib"))
    from config_utils import (
        get_repo_root, load_and_validate, resolve_path,
        write_run_config, print_guards, detect_private_mode,
        fail_if_network_requested,
    )

    repo = get_repo_root()
    config = load_and_validate(args.config)
    print_guards(config)
    output_dir = resolve_path(config, "smart_queue_dir")
    write_run_config(output_dir, config, "run_lightweight_smart_queue_v1.py")
"""

import json
import os
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
PATHS_CONFIG_PATH = REPO_ROOT / "configs" / "v3_17_paths.yaml"

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

# Environment variable that must be set to "true" (case-insensitive) for
# any private-data / real-data operation. This is the single gate that
# prevents accidental real-mode runs in CI.
PRIVATE_MODE_ENV_VAR = "OCN_ALLOW_PRIVATE_DATA"


def get_repo_root() -> Path:
    """Return the repository root directory.

    The repo root is determined by the location of this module
    (scripts/lib/config_utils.py → repo root is two parents up).
    This avoids any dependency on the current working directory.
    """
    return REPO_ROOT


def resolve_path(path, repo_root=None):
    """Resolve a path to an absolute Path.

    ``path`` may be:
      - a string or Path (relative or absolute)
      - a config dict with a 'project_root' key (legacy signature; the
        first positional arg is treated as the config dict and ``key``
        is required — but this overload is deprecated, prefer the
        explicit (path, repo_root) signature)

    When ``path`` is relative, it is joined to ``repo_root`` (which
    defaults to ``get_repo_root()`` if not provided).

    Returns None if ``path`` is None.
    """
    if path is None:
        return None
    # Legacy dict-based signature: resolve_path(config, key)
    if isinstance(path, dict):
        config = path
        key = repo_root  # second positional arg is the key in legacy mode
        if key is None or key not in config:
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
    # Modern signature: resolve_path(path_string, repo_root)
    p = Path(path)
    if p.is_absolute():
        return p
    base = repo_root if repo_root is not None else REPO_ROOT
    return (Path(base) / p).resolve()


def ensure_dir(path):
    """Create a directory (and parents) if it doesn't exist. Returns Path or None."""
    if path is None:
        return None
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def load_yaml_config(path):
    """Load a YAML config file and return a dict.

    If ``path`` is None, returns an empty dict.
    Relative paths are resolved against REPO_ROOT.
    """
    if yaml is None:
        raise ImportError(
            "PyYAML is required for config loading. Install: pip install pyyaml"
        )
    if path is None:
        return {}
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


def load_config(path=None):
    """Load a YAML config file. If path is None, use the default config."""
    if path is None:
        path = DEFAULT_CONFIG_PATH
    return load_yaml_config(path)


def assert_confidential_guards(config):
    """Raise ValueError if any required guard is not True."""
    for guard in REQUIRED_GUARDS:
        val = config.get(guard)
        if val is not True:
            raise ValueError(
                f"Confidential guard '{guard}' must be True, got: {val!r}. "
                f"The V3.17 pipeline requires no_api=true, no_network=true, no_training=true."
            )


def write_run_config(output_dir, config, script_name=None, extra=None):
    """Write run_config.json to output_dir with effective config and metadata.

    extra: optional dict merged into the run_config (e.g. selected_profile,
    toy_mode flag, overridden paths).
    """
    output_dir = ensure_dir(Path(output_dir))
    # config may be a dict from load_config, or None (use defaults)
    if config is None:
        config = {}
    run_config = {
        "script_name": script_name or "unknown",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "config_source": config.get("_config_source_path", "defaults"),
        "guards": {g: config.get(g) for g in REQUIRED_GUARDS},
        "no_original_data_modification": config.get("no_original_data_modification", True),
        "forbidden_scoring_fields": config.get(
            "forbidden_scoring_fields", DEFAULT_FORBIDDEN_SCORING_FIELDS
        ),
        "paths": {
            k: str(config[k]) for k in REQUIRED_CONFIG_KEYS
            if k in config and config[k] is not None
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
    if config is None:
        config = {}
    print(f"no_api: {config.get('no_api', True)}", flush=True)
    print(f"no_network: {config.get('no_network', True)}", flush=True)
    print(f"no_training: {config.get('no_training', True)}", flush=True)
    print(f"no_original_data_modification: {config.get('no_original_data_modification', True)}", flush=True)


def detect_private_mode(args=None, config=None) -> bool:
    """Detect whether private/real-data mode is explicitly enabled.

    Private mode is enabled if ANY of:
      1. ``args`` has ``allow_private_data=True`` (argparse --allow_private_data true)
      2. ``config`` dict has ``allow_private_data=True``
      3. Environment variable ``OCN_ALLOW_PRIVATE_DATA`` is set to "true"
         (case-insensitive)

    Otherwise, private mode is OFF (the default, safe state).
    """
    # Check argparse args
    if args is not None:
        val = getattr(args, "allow_private_data", None)
        if isinstance(val, str):
            if val.strip().lower() in ("true", "1", "yes"):
                return True
        elif val is True:
            return True
    # Check config dict
    if config is not None:
        val = config.get("allow_private_data")
        if isinstance(val, str):
            if val.strip().lower() in ("true", "1", "yes"):
                return True
        elif val is True:
            return True
    # Check environment variable
    env_val = os.environ.get(PRIVATE_MODE_ENV_VAR, "").strip().lower()
    if env_val in ("true", "1", "yes"):
        return True
    return False


def fail_if_network_requested(args=None, config=None) -> None:
    """Block network/API requests unless private mode is explicitly enabled.

    Raises PermissionError if private mode is OFF and the args/config
    indicate that network or API access is requested.

    This is the runtime gate that prevents accidental real-mode runs.
    Scripts that have --allow_private_data flags should call this at
    startup to enforce the boundary.
    """
    if detect_private_mode(args=args, config=config):
        return
    # If private mode is OFF, check if network/API is being requested
    if args is not None:
        for attr in ("allow_network", "allow_api", "use_network", "use_api"):
            val = getattr(args, attr, None)
            if val in (True, "true", "True", "1", "yes"):
                raise PermissionError(
                    f"Network/API access requested (--{attr}={val}) but "
                    f"private mode is not enabled. Set "
                    f"--allow_private_data true or environment variable "
                    f"{PRIVATE_MODE_ENV_VAR}=true to enable real-data mode."
                )
    if config is not None:
        for key in ("allow_network", "allow_api", "use_network", "use_api"):
            val = config.get(key)
            if val in (True, "true", "True", "1", "yes"):
                raise PermissionError(
                    f"Network/API access requested (config {key}={val}) but "
                    f"private mode is not enabled. Set "
                    f"--allow_private_data true or environment variable "
                    f"{PRIVATE_MODE_ENV_VAR}=true to enable real-data mode."
                )


def load_and_validate(config_path=None, toy_mode=False):
    """Load config, validate guards, and return it.

    If config_path is None and toy_mode is True, use the toy demo config.
    If config_path is None and toy_mode is False, use the default config.
    If the default config file does not exist, return a minimal default
    dict with guards set to True (so scripts can run without a YAML config
    by falling back to repo-root-relative path defaults).
    """
    if config_path is None:
        config_path = TOY_CONFIG_PATH if toy_mode else DEFAULT_CONFIG_PATH
    config_path = Path(config_path)
    if not config_path.is_absolute():
        config_path = (REPO_ROOT / config_path).resolve()
    if not config_path.exists():
        # Fall back to a minimal default so scripts can run without a YAML
        # config file. Guards are True by default (safe / no-API mode).
        return {
            "project_root": str(REPO_ROOT),
            "no_api": True,
            "no_network": True,
            "no_training": True,
            "no_original_data_modification": True,
            "_config_source_path": "fallback_defaults",
        }
    config = load_yaml_config(config_path)
    assert_confidential_guards(config)
    return config


def default_config_for_toy(toy_mode):
    """Return the default config path appropriate for the toy flag."""
    return TOY_CONFIG_PATH if toy_mode else DEFAULT_CONFIG_PATH


def load_paths_config(path=None):
    """Load the v3_17_paths.yaml config and return it as a dict.

    If the file doesn't exist, returns a minimal default with repo-root-
    relative paths. This is the single source of truth for path layout.
    """
    if path is None:
        path = PATHS_CONFIG_PATH
    path = Path(path)
    if not path.is_absolute():
        path = (REPO_ROOT / path).resolve()
    if not path.exists():
        # Fallback defaults (must match configs/v3_17_paths.yaml)
        return {
            "candidate_csv": "data/simclaim_all92_candidate_pool_v1/strict_silver_max_v1/strict_silver_max_candidates_v1.csv",
            "pdf_dir": "data/source_bank_v2/pdfs",
            "pdf_corpus_dir": "data/simclaim_pdf_corpus_retrieval_v1",
            "experiments_dir": "experiments",
            "paper_assets_dir": "paper_assets/v3_17_confidential",
            "reports_dir": "reports",
            "release_dir": "release_bundles/v3_17_confidential_public",
        }
    return load_yaml_config(path)
