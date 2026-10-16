import os
from pathlib import Path

APP = "nethack-screensaver"


def config_path() -> Path:
    base = os.environ.get("XDG_CONFIG_HOME") or Path.home() / ".config"
    return Path(base) / APP / "config.toml"


def state_dir() -> Path:
    base = os.environ.get("XDG_STATE_HOME") or Path.home() / ".local" / "state"
    d = Path(base) / APP
    d.mkdir(parents=True, exist_ok=True)
    return d
