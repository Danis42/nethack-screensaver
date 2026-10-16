import sys
import tomllib
from dataclasses import dataclass, fields
from pathlib import Path

ROLES = ("arc", "bar", "cav", "hea", "kni", "mon", "pri",
         "ran", "rog", "sam", "tou", "val", "wiz")


@dataclass(frozen=True)
class Config:
    delay: float = 0.1
    level_pause: float = 1.0
    end_pause: float = 5.0
    status_line: bool = False
    role: str = "random"


def _valid(name, value):
    if name in ("delay", "level_pause", "end_pause"):
        return isinstance(value, (int, float)) and not isinstance(value, bool) and value >= 0
    if name == "status_line":
        return isinstance(value, bool)
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
    except (OSError, tomllib.TOMLDecodeError) as e:
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
            values[key] = float(value) if key in ("delay", "level_pause", "end_pause") else value
    return Config(**values)
