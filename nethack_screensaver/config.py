import math
import sys
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

from autoascend.plans import STRATEGIES  # cheap: autoascend/__init__.py and plans.py import nothing heavy

# Upper bounds keep pacing below the 60 s game watchdog and out of sleep() overflow.
MAX_SECONDS = {"delay": 10.0, "fast_delay": 10.0, "level_pause": 10.0, "end_pause": 300.0}

ROLES = ("arc", "bar", "cav", "hea", "kni", "mon", "pri",
         "ran", "rog", "sam", "tou", "val", "wiz")


@dataclass(frozen=True)
class Config:
    delay: float = 0.1
    fast_delay: float = 0.005  # boring stretches (see pacing.py); = delay disables
    level_pause: float = 1.0
    end_pause: float = 5.0
    status_line: bool = False
    role: str = "random"
    strategy: str = "random"
    reveal_goal: bool = False


def _valid(name, value):
    if name in MAX_SECONDS:
        return (isinstance(value, (int, float)) and not isinstance(value, bool)
                and math.isfinite(value) and 0 <= value <= MAX_SECONDS[name])
    if name in ("status_line", "reveal_goal"):
        return isinstance(value, bool)
    if name == "strategy":
        return value == "random" or value in STRATEGIES
    if name == "role":
        return value == "random" or value in ROLES
    return False


def _warn(msg):
    print(f"nethack-screensaver: config: {msg}", file=sys.stderr)


def load_config(path: Path) -> Config:
    try:
        raw = tomllib.loads(Path(path).read_text())
    except FileNotFoundError:
        return Config()
    except (OSError, UnicodeDecodeError, tomllib.TOMLDecodeError) as e:
        _warn(f"cannot read {path}: {e}; using defaults")
        return Config()

    known = {f.name for f in fields(Config)}
    values = {}
    for key, value in raw.items():
        if key not in known:
            _warn(f"unknown key {key!r} ignored")
        elif not _valid(key, value):
            _warn(f"invalid value for {key}: {value!r}; using default")
        else:
            values[key] = float(value) if key in MAX_SECONDS else value
    return Config(**values)
