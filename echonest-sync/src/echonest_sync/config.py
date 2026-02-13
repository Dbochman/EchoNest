"""Config loading: ~/.echonest-sync.yaml → env vars → CLI args."""

import os
from pathlib import Path

import yaml


DEFAULT_CONFIG_PATH = Path.home() / ".echonest-sync.yaml"

DEFAULTS = {
    "server": None,
    "token": None,
    "drift_threshold": 3,
}


def load_config(config_path=None, cli_overrides=None):
    """Load config with precedence: CLI args > env vars > config file > defaults."""
    config = dict(DEFAULTS)

    # 1. Config file
    path = Path(config_path) if config_path else DEFAULT_CONFIG_PATH
    if path.exists():
        try:
            with open(path) as f:
                file_config = yaml.safe_load(f) or {}
            for key in DEFAULTS:
                if key in file_config:
                    config[key] = file_config[key]
        except Exception as e:
            # Don't crash on bad config file
            import logging
            logging.getLogger(__name__).warning("Failed to read config file %s: %s", path, e)

    # 2. Env var overrides
    env_map = {
        "server": "ECHONEST_SERVER",
        "token": "ECHONEST_TOKEN",
        "drift_threshold": "ECHONEST_DRIFT_THRESHOLD",
    }
    for key, env_var in env_map.items():
        val = os.environ.get(env_var)
        if val is not None:
            if key == "drift_threshold":
                config[key] = int(val)
            else:
                config[key] = val

    # 3. CLI arg overrides
    if cli_overrides:
        for key, val in cli_overrides.items():
            if val is not None:
                config[key] = val

    return config
