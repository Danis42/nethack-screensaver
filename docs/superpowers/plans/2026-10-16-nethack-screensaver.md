# NetHack Terminal Screensaver Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** After 5 minutes idle at the zsh prompt, take over the terminal with a live NetHack game played by a ported AutoAscend bot; any key returns to the untouched prompt.

**Architecture:** AutoAscend (vendored, ported to NLE 1.3.0 / gymnasium / Python 3.13, trimmed) runs inside `nethack_screensaver.player`, which paces and renders every env step to the terminal through a pure ANSI renderer. A bash launcher owns the tty (alt screen, raw mode, keypress watch, guaranteed restore) and a zsh `TMOUT`/`TRAPALRM` hook starts it.

**Tech Stack:** Python 3.13 via `uv`, NLE 1.3.0, numpy 2, numba, opencv-python-headless, scipy, toolz, pytest; bash; zsh.

**Spec:** `docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md`

## Global Constraints

- Python `>=3.13,<3.14`, managed by `uv`; venv at `<repo>/.venv`.
- Runtime deps limited to: `nle==1.3.0`, `numpy`, `numba`, `opencv-python-headless`, `scipy`, `toolz` (gymnasium comes with nle). No torch, ray, matplotlib, seaborn, pandas, nltk, PIL, gym.
- AutoAscend vendored from `maciej-sypetkowski/autoascend` @ `8527910bd85c4d851c18ad912aae606c92cd516a`, MIT — keep its `LICENSE` as `autoascend/LICENSE`.
- Config file: `${XDG_CONFIG_HOME:-~/.config}/nethack-screensaver/config.toml`; keys `delay=0.1`, `level_pause=1.0`, `end_pause=5.0`, `status_line=false`, `role="random"`.
- Idle timeout: env var `NETHACK_SCREENSAVER_IDLE` (default `300`) read by the zsh hook. (Spec deviation: moved out of TOML so shell startup never runs Python.)
- State dir: `${XDG_STATE_HOME:-~/.local/state}/nethack-screensaver/` containing `games.jsonl` and `player.log`.
- Screen is 80×24 (NLE tty); with status line 80×25.
- Watchdog: 60 s without a screen change ends the game with `end_reason="watchdog"`.
- Terminal must always be restored, including on player crash.

## Review Focus

1. **Keypress leaking into the shell** — arrow/function keys send multi-byte escape sequences; all bytes must be swallowed, none appear on the prompt. → Task 8 launcher drains input; manual checklist item.
2. **Player crash at startup** (missing `.venv`, import error) — must restore terminal and show a one-line error, not leave a black alt screen. → Task 8 launcher handles early exit; tested with a fake player.
3. **Terminal resized mid-game or smaller than 80×24** — re-center or show "too small", never garbage. → Task 5 renderer tests (`test_too_small`, `test_invalidate_forces_full_redraw`).
4. **Corrupt/partial `games.jsonl` line** (killed mid-write) — must not crash the player on next start. → Task 4 test `test_read_stats_skips_malformed_lines`.
5. **Invalid config values** (`delay = "fast"`, unknown role) — fall back to defaults with a warning, never crash. → Task 3 tests.

---

## File Structure

```
pyproject.toml                      uv project, deps, pytest config
.python-version                     "3.13"
autoascend/                         vendored + ported agent (game logic unchanged)
  LICENSE
  env_wrapper.py                    REWRITTEN: gymnasium adapter + per-step callback
  PORTING.md                        log of every port change
nethack_screensaver/
  __init__.py
  paths.py                          config/state path resolution
  config.py                         Config dataclass + tolerant TOML loader
  gamelog.py                        GameRecord append / LogStats read
  render.py                         pure ANSI renderer + status line formatting
  game.py                           run_game(): one headless-capable AutoAscend game
  player.py                         forever loop: splash, pacing, logging, signals
bin/nethack-screensaver             bash launcher (tty owner)
zsh/nethack-screensaver.zsh         TMOUT/TRAPALRM hook
scripts/benchmark.py                multi-game headless benchmark
tests/
  test_config.py test_gamelog.py test_render.py test_game.py
  test_player.py test_launcher.py
  fake_player.py                    stand-in player for launcher tests
README.md
```

---

### Task 1: Project scaffold and vendored, trimmed AutoAscend that imports

**Files:**
- Create: `pyproject.toml`, `.python-version`, `.gitignore`, `nethack_screensaver/__init__.py`, `autoascend/PORTING.md`, `tests/test_imports.py`
- Create (vendored copy): `autoascend/**` from upstream
- Delete inside vendored copy: `autoascend/visualization/`, `autoascend/rl_utils.py`
- Modify: `autoascend/utils.py`, `autoascend/agent.py`, `autoascend/combat/rl_scoring.py`

**Interfaces:**
- Produces: importable package `autoascend` with `autoascend.agent.Agent`, `autoascend.agent.BLStats`, `autoascend.agent.G`.

- [ ] **Step 1: Ensure uv is installed**

Run: `uv --version`
If missing, ask the user to run `! sudo pacman -S uv` (needs sudo; do not run it yourself). Expected afterwards: `uv 0.12.x`.

- [ ] **Step 2: Write scaffold files**

`.python-version`:
```
3.13
```

`pyproject.toml`:
```toml
[project]
name = "nethack-screensaver"
version = "0.1.0"
description = "Terminal screensaver: AutoAscend plays NetHack"
requires-python = ">=3.13,<3.14"
dependencies = [
    "nle==1.3.0",
    "numpy>=2.0",
    "numba>=0.61",
    "opencv-python-headless>=4.10",
    "scipy>=1.14",
    "toolz>=1.0",
]

[dependency-groups]
dev = ["pytest>=8"]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["autoascend", "nethack_screensaver"]

[tool.pytest.ini_options]
testpaths = ["tests"]
markers = ["slow: plays real games (minutes)"]
addopts = "-m 'not slow'"
```

`.gitignore`:
```
.venv/
__pycache__/
*.nbi
*.nbc
.pytest_cache/
```

`nethack_screensaver/__init__.py`: empty file.

- [ ] **Step 3: Vendor AutoAscend**

```bash
cd .
git clone -q https://github.com/maciej-sypetkowski/autoascend /tmp/aa-src   # or reuse an existing clone
git -C /tmp/aa-src checkout -q 8527910bd85c4d851c18ad912aae606c92cd516a
cp -r /tmp/aa-src/autoascend ./autoascend
cp /tmp/aa-src/LICENSE ./autoascend/LICENSE
rm -rf autoascend/visualization autoascend/rl_utils.py
```

- [ ] **Step 4: Write the failing import test**

`tests/test_imports.py`:
```python
def test_autoascend_agent_imports():
    from autoascend import agent

    assert hasattr(agent, "Agent")
    assert hasattr(agent, "BLStats")


def test_no_heavy_deps_loaded():
    import sys

    import autoascend.agent  # noqa: F401

    for mod in ("torch", "ray", "matplotlib", "seaborn", "pandas", "nltk", "gym"):
        assert mod not in sys.modules, f"{mod} must not be imported"
```

- [ ] **Step 5: Install and run test to verify it fails**

Run: `uv sync && uv run pytest tests/test_imports.py -v`
Expected: FAIL (ImportError on `matplotlib` / `nltk` / `autoascend.visualization`).

- [ ] **Step 6: Trim heavy imports**

In `autoascend/utils.py`: delete `import matplotlib.pyplot as plt`, `import seaborn as sns`, and the whole `plot_dashboard` function (starts at `def plot_dashboard(fig, res):`, runs to the next top-level `def` or EOF).

In `autoascend/agent.py`: delete `import nltk`; replace the one call `nltk.edit_distance(` with `_edit_distance(` and add near the top (after imports):
```python
def _edit_distance(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]
```

In `autoascend/combat/rl_scoring.py`: delete the function `init_fight2_model` (it imports the removed `rl_utils`; its only caller in `agent.py` is already commented out).

`env_wrapper.py` still imports `visualization`; replace the whole file for now with a stub (Task 2 rewrites it):
```python
"""Replaced in Task 2."""
```

- [ ] **Step 7: Fix remaining import errors**

Run: `uv run pytest tests/test_imports.py -v`
For each ImportError/AttributeError from modern numpy/numba/opencv, fix the minimal line. Known modern-API fixes to apply if hit: `np.int`→`int`, `np.bool`→`bool`, `np.float`→`float`, `np.object`→`object`, `np.str`→`str`. Repeat until PASS. Record every change (file, line, why) as a bullet in `autoascend/PORTING.md`, which starts with:
```markdown
# AutoAscend port notes

Upstream: maciej-sypetkowski/autoascend @ 8527910 (MIT).
Target: Python 3.13, NLE 1.3.0 (gymnasium), numpy 2, modern numba/opencv.

## Removed
- visualization/, rl_utils.py, rl_scoring.init_fight2_model (torch/RL, tile viewer)
- utils.plot_dashboard (matplotlib/seaborn)
- nltk (replaced by agent._edit_distance)

## Changes
```

Expected: both tests PASS.

- [ ] **Step 8: Commit**

```bash
git add pyproject.toml uv.lock .python-version .gitignore nethack_screensaver autoascend tests/test_imports.py
git commit -m "feat: vendor AutoAscend and trim heavy dependencies"
```

---

### Task 2: Port the environment layer; play real headless games

**Files:**
- Rewrite: `autoascend/env_wrapper.py`
- Modify: `autoascend/agent.py` (BLStats construction)
- Create: `nethack_screensaver/game.py`, `tests/test_game.py`
- Modify: `autoascend/PORTING.md`

**Interfaces:**
- Consumes: `autoascend.agent.Agent`, `BLStats`, `G`.
- Produces:
  - `autoascend.env_wrapper.EnvWrapper(env, on_step: Callable[[dict], None] | None = None, step_limit: int | None = None, role: str | None = None)` with `.main()`, `.score: float`, `.end_reason: str`, `.agent`.
  - `nethack_screensaver.game.GameResult` dataclass: `role: str, race: str, alignment: str, max_depth: int, turns: int, score: int, end_reason: str`.
  - `nethack_screensaver.game.run_game(role: str | None = None, on_frame: Callable[[dict], None] | None = None, max_steps: int | None = None, watchdog_seconds: float | None = 60.0) -> GameResult`
  - `nethack_screensaver.game.role_abbrev(obs: dict) -> str` — e.g. `"Val"` from the player glyph.
  - `nethack_screensaver.game.WatchdogTimeout(KeyboardInterrupt)`.
  - Observation dict keys used downstream: `tty_chars (24,80) uint8`, `tty_colors (24,80) int8`, `blstats` (index 12 = depth, 20 = turn).

- [ ] **Step 1: Write the failing tests**

`tests/test_game.py`:
```python
import signal
import time

import pytest

from nethack_screensaver import game


def test_watchdog_fires_without_screen_change():
    wd = game._ScreenWatchdog(seconds=1)
    with pytest.raises(game.WatchdogTimeout):
        with wd:
            time.sleep(3)


def test_watchdog_rearmed_by_changes_does_not_fire():
    wd = game._ScreenWatchdog(seconds=1)
    with wd:
        for i in range(6):
            time.sleep(0.4)
            wd.screen_changed()
    assert signal.getitimer(signal.ITIMER_REAL)[0] == 0


@pytest.mark.slow
def test_headless_games_complete_without_exceptions():
    for _ in range(2):
        frames = []
        result = game.run_game(on_frame=lambda obs: frames.append(1), max_steps=3000)
        assert not result.end_reason.startswith("exception"), result.end_reason
        assert result.max_depth >= 1
        assert result.role and result.race and result.alignment
        assert len(frames) > 10


@pytest.mark.slow
def test_pinned_role():
    result = game.run_game(role="val", max_steps=200)
    assert result.role == "val"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_game.py -v -m ""`
Expected: FAIL — `ImportError: cannot import name 'game'`.

- [ ] **Step 3: Rewrite `autoascend/env_wrapper.py`**

```python
"""Adapter between NLE 1.3.0 (gymnasium API) and the AutoAscend agent.

The agent only calls step(), debug_tiles() and debug_log() on this object.
"""
import contextlib

import nle.nethack as nh

from autoascend import agent as agent_lib


def _blstats(obs):
    return agent_lib.BLStats(*obs['blstats'][:len(agent_lib.BLStats._fields)])


def _role_matches(obs, role):
    bl = _blstats(obs)
    glyph = obs['glyphs'][bl.y, bl.x]
    return nh.permonst(nh.glyph_to_mon(glyph)).mname.startswith(role)


class EnvWrapper:
    def __init__(self, env, on_step=None, step_limit=None, role=None, agent_args=None):
        self.env = env
        self.on_step = on_step
        self.step_limit = step_limit
        self.role = role
        self.agent_args = agent_args or {}
        self.agent = None
        self.last_observation = None
        self.score = 0
        self.step_count = 0
        self.end_reason = ''
        self.is_done = False

    def main(self):
        self.reset()
        self.agent = agent_lib.Agent(self, **self.agent_args)
        self.agent.main()

    def reset(self):
        while True:
            obs, _info = self.env.reset()
            if self.role is None or _role_matches(obs, self.role):
                break
        self.score = 0
        self.step_count = 0
        self.end_reason = ''
        self.is_done = False
        self.last_observation = obs

        agent_lib.G.assert_map(obs['glyphs'], obs['chars'])
        bl = _blstats(obs)
        assert obs['chars'][bl.y, bl.x] == ord('@')
        if self.on_step is not None:
            self.on_step(obs)
        return obs

    def render(self, force=False):
        pass

    def step(self, agent_action):
        obs, reward, terminated, truncated, info = self.env.step(
            self.env.actions.index(agent_action))
        done = terminated or truncated
        self.score += reward
        self.step_count += 1
        if done:
            self.end_reason = self._parse_end_reason(obs, info)
        if self.step_limit is not None and self.step_count >= self.step_limit and not done:
            self.end_reason = 'steplimit'
            done = True
        self.last_observation = obs
        if done:
            self.is_done = True
        if self.on_step is not None:
            self.on_step(obs)
        return obs, reward, done, info

    def _parse_end_reason(self, obs, info):
        status = info.get('end_status')
        status_name = getattr(status, 'name', str(status))
        try:
            words = bytes(obs['tty_chars'].reshape(-1)).decode(errors='replace') \
                .replace('You made the top ten list!', '').split()
            idx = next(i for i, w in enumerate(words) if w.startswith('Agent'))
            text = ' '.join(words[idx + 1:-2])
            first = text.split('.')[0].split()
            if 'in' in first:
                first = first[:first.index('in')]
            return f'{status_name}: {" ".join(first)}'.strip()
        except Exception:
            return status_name

    def debug_tiles(self, *args, **kwargs):
        return contextlib.nullcontext()

    def debug_log(self, *args, **kwargs):
        return contextlib.nullcontext()
```

In `autoascend/agent.py` line ~451 replace
`self.blstats = BLStats(*self.last_observation['blstats'])`
with
`self.blstats = BLStats(*self.last_observation['blstats'][:len(BLStats._fields)])`
(NLE 1.x may append extra blstats fields; AutoAscend's 26 fields are a prefix.)

- [ ] **Step 4: Write `nethack_screensaver/game.py`**

```python
"""Run one AutoAscend game on NLE, headless-capable."""
from __future__ import annotations

import signal
from dataclasses import dataclass
from typing import Callable

import nle.nethack as nh
from nle.env.tasks import NetHackChallenge

from autoascend.env_wrapper import EnvWrapper

DEPTH = 12
TURN = 20


class WatchdogTimeout(KeyboardInterrupt):
    """Raised from SIGALRM; KeyboardInterrupt so the agent never swallows it."""


@dataclass
class GameResult:
    role: str
    race: str
    alignment: str
    max_depth: int
    turns: int
    score: int
    end_reason: str


class _ScreenWatchdog:
    def __init__(self, seconds: float | None):
        self.seconds = seconds
        self._old = None

    def _fire(self, signum, frame):
        raise WatchdogTimeout()

    def __enter__(self):
        if self.seconds:
            self._old = signal.signal(signal.SIGALRM, self._fire)
            signal.setitimer(signal.ITIMER_REAL, self.seconds)
        return self

    def screen_changed(self):
        if self.seconds:
            signal.setitimer(signal.ITIMER_REAL, self.seconds)

    def __exit__(self, *exc):
        if self.seconds:
            signal.setitimer(signal.ITIMER_REAL, 0)
            signal.signal(signal.SIGALRM, self._old)
        return False


def role_abbrev(obs: dict) -> str:
    bl = obs["blstats"]
    glyph = obs["glyphs"][bl[1], bl[0]]
    if not nh.glyph_is_monster(glyph):
        return "?"
    return nh.permonst(nh.glyph_to_mon(glyph)).mname[:3].capitalize()


def run_game(
    role: str | None = None,
    on_frame: Callable[[dict], None] | None = None,
    max_steps: int | None = None,
    watchdog_seconds: float | None = 60.0,
) -> GameResult:
    env = NetHackChallenge(no_progress_timeout=1000)
    max_depth = 1
    turns = 0
    prev_chars = None
    watchdog = _ScreenWatchdog(watchdog_seconds)

    def on_step(obs):
        nonlocal max_depth, turns, prev_chars
        max_depth = max(max_depth, int(obs["blstats"][DEPTH]))
        turns = int(obs["blstats"][TURN])
        chars = obs["tty_chars"]
        if prev_chars is None or not (chars == prev_chars).all():
            watchdog.screen_changed()
            prev_chars = chars.copy()
        if on_frame is not None:
            on_frame(obs)

    wrapper = EnvWrapper(env, on_step=on_step, step_limit=max_steps, role=role,
                         agent_args=dict(panic_on_errors=False, verbose=False))
    try:
        with watchdog:
            wrapper.main()
        end_reason = wrapper.end_reason or "finished"
    except WatchdogTimeout:
        end_reason = "watchdog"
    except Exception as e:  # never let one bad game kill the screensaver
        end_reason = f"exception: {type(e).__name__}: {e}"
    finally:
        env.close()

    role_s, race, _gender, alignment = _character(wrapper)
    return GameResult(role_s, race, alignment, max_depth, turns,
                      int(wrapper.score), end_reason)


def _character(wrapper) -> tuple[str, str, str, str]:
    try:
        parts = str(wrapper.agent.character).split()[0].split("-")
        if len(parts) >= 4:
            return parts[0], parts[1], parts[2], parts[3]
    except Exception:
        pass
    return "?", "?", "?", "?"
```

- [ ] **Step 5: Run fast tests**

Run: `uv run pytest tests/test_game.py -v`
Expected: the two watchdog tests PASS (slow tests deselected).

- [ ] **Step 6: Run slow tests and port until green**

Run: `uv run pytest tests/test_game.py -v -m slow -x`
For each failure: read the traceback, fix the minimal line in `autoascend/` (NLE 1.x attribute renames, numpy 2 dtype/casting errors, numba typing errors — e.g. pass explicit `.astype(np.int16)` where a jitted `i2` signature receives another dtype), add a bullet to `PORTING.md`, re-run. Note `result.end_reason` for `exception:` games contains the cause. Expected at the end: both slow tests PASS.

- [ ] **Step 7: Commit**

```bash
git add autoascend nethack_screensaver/game.py tests/test_game.py
git commit -m "feat: port AutoAscend env layer to NLE 1.3.0 and add headless game runner"
```

---

### Task 3: Config loader

**Files:**
- Create: `nethack_screensaver/paths.py`, `nethack_screensaver/config.py`, `tests/test_config.py`

**Interfaces:**
- Produces:
  - `paths.config_path() -> Path`, `paths.state_dir() -> Path` (creates dir).
  - `config.Config` frozen dataclass: `delay: float = 0.1, level_pause: float = 1.0, end_pause: float = 5.0, status_line: bool = False, role: str = "random"`.
  - `config.ROLES: tuple[str, ...]`.
  - `config.load_config(path: Path) -> Config` — never raises; warns on stderr.

- [ ] **Step 1: Write the failing tests**

`tests/test_config.py`:
```python
from nethack_screensaver.config import Config, load_config


def test_missing_file_gives_defaults(tmp_path):
    assert load_config(tmp_path / "nope.toml") == Config()


def test_overrides(tmp_path):
    p = tmp_path / "c.toml"
    p.write_text('delay = 0.05\nstatus_line = true\nrole = "val"\nend_pause = 2\n')
    c = load_config(p)
    assert c.delay == 0.05 and c.status_line is True and c.role == "val"
    assert c.end_pause == 2.0


def test_invalid_values_fall_back(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text('delay = "fast"\nrole = "dragon"\nlevel_pause = -1\nbogus = 1\n')
    c = load_config(p)
    assert c == Config()
    err = capsys.readouterr().err
    assert "delay" in err and "role" in err and "level_pause" in err


def test_malformed_toml_gives_defaults(tmp_path, capsys):
    p = tmp_path / "c.toml"
    p.write_text("delay = = 1\n")
    assert load_config(p) == Config()
    assert "config" in capsys.readouterr().err
```

- [ ] **Step 2: Run to verify fail**

Run: `uv run pytest tests/test_config.py -v`
Expected: FAIL — `ModuleNotFoundError: nethack_screensaver.config`.

- [ ] **Step 3: Implement**

`nethack_screensaver/paths.py`:
```python
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
```

`nethack_screensaver/config.py`:
```python
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
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_config.py -v`
Expected: 4 PASS.

- [ ] **Step 5: Commit**

```bash
git add nethack_screensaver/paths.py nethack_screensaver/config.py tests/test_config.py
git commit -m "feat: add tolerant TOML config loader"
```

---

### Task 4: Game log

**Files:**
- Create: `nethack_screensaver/gamelog.py`, `tests/test_gamelog.py`

**Interfaces:**
- Consumes: `game.GameResult` (Task 2).
- Produces:
  - `gamelog.append_result(path: Path, result: GameResult, now: datetime | None = None) -> None` — writes one JSON line with keys `timestamp, role, race, alignment, max_depth, turns, score, end_reason`.
  - `gamelog.LogStats(games: int, best_depth: int)` dataclass.
  - `gamelog.read_stats(path: Path) -> LogStats`.

- [ ] **Step 1: Write the failing tests**

`tests/test_gamelog.py`:
```python
import json
from datetime import datetime, timezone

from nethack_screensaver.game import GameResult
from nethack_screensaver.gamelog import LogStats, append_result, read_stats


def _r(depth):
    return GameResult("val", "hum", "law", depth, 1234, 567, "DIED: killed by a jackal")


def test_append_and_read(tmp_path):
    p = tmp_path / "games.jsonl"
    append_result(p, _r(3), now=datetime(2026, 10, 16, tzinfo=timezone.utc))
    append_result(p, _r(9))
    lines = p.read_text().splitlines()
    assert len(lines) == 2
    rec = json.loads(lines[0])
    assert rec["role"] == "val" and rec["max_depth"] == 3
    assert rec["timestamp"].startswith("2026-10-16")
    assert read_stats(p) == LogStats(games=2, best_depth=9)


def test_read_stats_missing_file(tmp_path):
    assert read_stats(tmp_path / "x.jsonl") == LogStats(0, 0)


def test_read_stats_skips_malformed_lines(tmp_path):
    p = tmp_path / "games.jsonl"
    append_result(p, _r(4))
    with p.open("a") as f:
        f.write('{"max_depth": 99, "trunc\n')
        f.write("not json\n")
        f.write('{"max_depth": "x"}\n')
    assert read_stats(p) == LogStats(games=1, best_depth=4)
```

- [ ] **Step 2: Run to verify fail**

Run: `uv run pytest tests/test_gamelog.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

`nethack_screensaver/gamelog.py`:
```python
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from nethack_screensaver.game import GameResult


@dataclass(frozen=True)
class LogStats:
    games: int
    best_depth: int


def append_result(path: Path, result: GameResult, now: datetime | None = None) -> None:
    now = now or datetime.now(timezone.utc)
    record = {"timestamp": now.isoformat(timespec="seconds"), **asdict(result)}
    with Path(path).open("a") as f:
        f.write(json.dumps(record) + "\n")


def read_stats(path: Path) -> LogStats:
    games = best = 0
    try:
        lines = Path(path).read_text().splitlines()
    except FileNotFoundError:
        return LogStats(0, 0)
    for line in lines:
        try:
            depth = json.loads(line)["max_depth"]
        except (json.JSONDecodeError, KeyError, TypeError):
            continue
        if not isinstance(depth, int):
            continue
        games += 1
        best = max(best, depth)
    return LogStats(games, best)
```

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_gamelog.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Commit**

```bash
git add nethack_screensaver/gamelog.py tests/test_gamelog.py
git commit -m "feat: add JSONL game log"
```

---

### Task 5: ANSI renderer

**Files:**
- Create: `nethack_screensaver/render.py`, `tests/test_render.py`

**Interfaces:**
- Produces:
  - `render.Renderer()` with
    - `frame(tty_chars: np.ndarray, tty_colors: np.ndarray, cols: int, rows: int, status: str | None = None) -> str`
    - `message(text: str, cols: int, rows: int) -> str` (clears screen, centers text, invalidates)
    - `invalidate() -> None` (next `frame` is a full redraw)
  - `render.format_status(game_no: int, role: str, depth: int, turn: int, best_depth: int) -> str` → `"Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14"`.
  - `render.TOO_SMALL = "Terminal too small for NetHack (need 80x24)"`.

Color mapping (NetHack CLR_* → SGR): `0→90, 1..7→31..37, 8→39 (no color), 9..15→91..97`; `tty_colors & 15` before mapping. Non-printable chars (<32 or >126) render as space.

- [ ] **Step 1: Write the failing tests**

`tests/test_render.py`:
```python
import re

import numpy as np

from nethack_screensaver.render import TOO_SMALL, Renderer, format_status

ANSI = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")


def screen(text_rows=None):
    chars = np.full((24, 80), ord(" "), dtype=np.uint8)
    colors = np.zeros((24, 80), dtype=np.int8)
    for y, line in (text_rows or {}).items():
        chars[y, : len(line)] = list(line.encode())
    return chars, colors


def moves(out):
    return [(int(r), int(c)) for r, c in re.findall(r"\x1b\[(\d+);(\d+)H", out)]


def test_first_frame_is_full_redraw_centered():
    r = Renderer()
    chars, colors = screen({0: "Hello"})
    out = r.frame(chars, colors, cols=100, rows=30)
    assert "\x1b[2J" in out
    assert (4, 11) in moves(out)  # row 0 → (30-24)//2+1, col 0 → (100-80)//2+1
    assert "Hello" in ANSI.sub("", out)


def test_unchanged_frame_emits_nothing():
    r = Renderer()
    chars, colors = screen({0: "Hello"})
    r.frame(chars, colors, 80, 24)
    assert r.frame(chars, colors, 80, 24) == ""


def test_diff_only_rewrites_changed_span():
    r = Renderer()
    chars, colors = screen({5: "abcdef"})
    r.frame(chars, colors, 80, 24)
    chars2 = chars.copy()
    chars2[5, 2] = ord("X")
    out = r.frame(chars2, colors, 80, 24)
    assert "\x1b[2J" not in out
    assert moves(out) == [(6, 3)]
    assert ANSI.sub("", out) == "X"


def test_colors_mapped():
    r = Renderer()
    chars, colors = screen({0: "@"})
    colors[0, 0] = 1  # red
    out = r.frame(chars, colors, 80, 24)
    assert "\x1b[31m@" in out


def test_too_small():
    r = Renderer()
    chars, colors = screen()
    out = r.frame(chars, colors, cols=60, rows=20)
    assert TOO_SMALL[:40] in ANSI.sub("", out)


def test_invalidate_forces_full_redraw():
    r = Renderer()
    chars, colors = screen({0: "x"})
    r.frame(chars, colors, 80, 24)
    r.invalidate()
    assert "\x1b[2J" in r.frame(chars, colors, 80, 24)


def test_size_change_forces_full_redraw():
    r = Renderer()
    chars, colors = screen({0: "x"})
    r.frame(chars, colors, 80, 24)
    assert "\x1b[2J" in r.frame(chars, colors, 90, 30)


def test_status_line_needs_25_rows_and_is_drawn_below():
    r = Renderer()
    chars, colors = screen()
    small = r.frame(chars, colors, 80, 24, status="Game #1")
    assert TOO_SMALL[:20] in ANSI.sub("", small)
    r.invalidate()
    out = r.frame(chars, colors, 80, 25, status="Game #1")
    assert (25, 1) in moves(out) and "Game #1" in out


def test_status_line_redrawn_only_when_changed():
    r = Renderer()
    chars, colors = screen()
    r.frame(chars, colors, 80, 25, status="A")
    assert r.frame(chars, colors, 80, 25, status="A") == ""
    assert "B" in r.frame(chars, colors, 80, 25, status="B")


def test_message_centered():
    r = Renderer()
    out = r.message("hi", cols=80, rows=24)
    assert "\x1b[2J" in out and (12, 40) in moves(out)


def test_format_status():
    assert format_status(12, "Val", 7, 4310, 14) == "Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14"
```

- [ ] **Step 2: Run to verify fail**

Run: `uv run pytest tests/test_render.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

`nethack_screensaver/render.py`:
```python
"""Pure ANSI renderer for NLE's 80x24 tty observation."""
import numpy as np

W, H = 80, 24
TOO_SMALL = "Terminal too small for NetHack (need 80x24)"
CLEAR = "\x1b[0m\x1b[2J"
RESET = "\x1b[0m"


def _sgr(color: int) -> int:
    c = int(color) & 15
    if c == 0:
        return 90
    if c < 8:
        return 30 + c
    if c == 8:
        return 39
    return 90 + (c - 8)


def _ch(code: int) -> str:
    return chr(code) if 32 <= code <= 126 else " "


def format_status(game_no: int, role: str, depth: int, turn: int, best_depth: int) -> str:
    return f"Game #{game_no} · {role} · Dlvl {depth} · T:{turn} · Best: Dlvl {best_depth}"


class Renderer:
    def __init__(self):
        self.invalidate()

    def invalidate(self) -> None:
        self._chars = None
        self._colors = None
        self._status = None
        self._size = None

    def message(self, text: str, cols: int, rows: int) -> str:
        self.invalidate()
        text = text[: max(cols, 1)]
        row = rows // 2
        col = max((cols - len(text)) // 2, 0) + 1
        return f"{CLEAR}\x1b[{row};{col}H{text}"

    def frame(self, tty_chars, tty_colors, cols, rows, status=None) -> str:
        need_rows = H + (1 if status is not None else 0)
        if cols < W or rows < need_rows:
            if self._size == ("small", cols, rows):
                return ""
            out = self.message(TOO_SMALL, cols, rows)
            self._size = ("small", cols, rows)
            return out

        full = self._size != (cols, rows) or self._chars is None
        top = (rows - need_rows) // 2
        left = (cols - W) // 2
        parts = [CLEAR] if full else []
        for y in range(H):
            row_c, row_k = tty_chars[y], tty_colors[y]
            if full:
                start, end = 0, W
            else:
                diff = np.nonzero((row_c != self._chars[y]) | (row_k != self._colors[y]))[0]
                if diff.size == 0:
                    continue
                start, end = int(diff[0]), int(diff[-1]) + 1
            parts.append(f"\x1b[{top + y + 1};{left + start + 1}H")
            cur = None
            for x in range(start, end):
                sgr = _sgr(row_k[x])
                if sgr != cur:
                    parts.append(f"\x1b[{sgr}m")
                    cur = sgr
                parts.append(_ch(int(row_c[x])))
        if status is not None and (full or status != self._status):
            parts.append(f"{RESET}\x1b[{top + H + 1};{left + 1}H\x1b[2K{status[:W]}")
        self._chars = tty_chars.copy()
        self._colors = tty_colors.copy()
        self._status = status
        self._size = (cols, rows)
        if not parts:
            return ""
        out = "".join(parts)
        return out + RESET if not out.endswith(RESET) else out
```

Note for `test_diff_only_rewrites_changed_span`: the stripped output must equal `"X"` — the trailing `RESET` and the SGR codes are stripped by the regex, so the code above satisfies it.

- [ ] **Step 4: Run to verify pass**

Run: `uv run pytest tests/test_render.py -v`
Expected: 11 PASS.

- [ ] **Step 5: Commit**

```bash
git add nethack_screensaver/render.py tests/test_render.py
git commit -m "feat: add diffing ANSI renderer for NLE tty"
```

---

### Task 6: Player loop

**Files:**
- Create: `nethack_screensaver/player.py`, `tests/test_player.py`

**Interfaces:**
- Consumes: `Config`, `load_config`, `paths.config_path/state_dir`, `Renderer`, `format_status`, `run_game`, `role_abbrev`, `append_result`, `read_stats`.
- Produces:
  - `player.frame_delay(prev_depth: int | None, depth: int, cfg: Config) -> float`
  - `player.main() -> None`, runnable as `python -m nethack_screensaver.player`.

- [ ] **Step 1: Write the failing tests**

`tests/test_player.py`:
```python
from nethack_screensaver.config import Config
from nethack_screensaver.player import frame_delay


def test_normal_step_uses_delay():
    assert frame_delay(3, 3, Config(delay=0.1, level_pause=1.0)) == 0.1


def test_level_change_uses_level_pause():
    assert frame_delay(3, 4, Config(delay=0.1, level_pause=1.0)) == 1.0


def test_first_frame_uses_delay():
    assert frame_delay(None, 1, Config(delay=0.2)) == 0.2
```

- [ ] **Step 2: Run to verify fail**

Run: `uv run pytest tests/test_player.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Implement**

`nethack_screensaver/player.py`:
```python
"""Screensaver player: forever plays AutoAscend games, paced and rendered."""
import shutil
import signal
import sys
import time

from nethack_screensaver.config import Config, load_config
from nethack_screensaver.paths import config_path, state_dir
from nethack_screensaver.render import Renderer, format_status

SPLASH = "a new adventurer enters the dungeon..."


def frame_delay(prev_depth, depth, cfg: Config) -> float:
    if prev_depth is not None and depth != prev_depth:
        return cfg.level_pause
    return cfg.delay


def _size():
    s = shutil.get_terminal_size((80, 24))
    return s.columns, s.lines


def _write(out, text):
    if text:
        out.write(text)
        out.flush()


def _on_term(signum, frame):
    raise SystemExit(0)


def main() -> None:
    cfg = load_config(config_path())
    log_path = state_dir() / "games.jsonl"
    out = sys.stdout
    renderer = Renderer()
    signal.signal(signal.SIGTERM, _on_term)
    signal.signal(signal.SIGWINCH, lambda *_: renderer.invalidate())

    _write(out, renderer.message(SPLASH, *_size()))

    # Heavy imports after the splash so the user sees something immediately.
    from nethack_screensaver.game import DEPTH, TURN, role_abbrev, run_game
    from nethack_screensaver.gamelog import append_result, read_stats

    role = None if cfg.role == "random" else cfg.role
    while True:
        stats = read_stats(log_path)
        game_no = stats.games + 1
        state = {"depth": None, "role": None, "obs": None}

        def on_frame(obs):
            depth = int(obs["blstats"][DEPTH])
            if state["role"] is None:
                state["role"] = role_abbrev(obs)
            status = None
            if cfg.status_line:
                status = format_status(game_no, state["role"], depth,
                                       int(obs["blstats"][TURN]),
                                       max(stats.best_depth, depth))
            _write(out, renderer.frame(obs["tty_chars"], obs["tty_colors"], *_size(), status=status))
            time.sleep(frame_delay(state["depth"], depth, cfg))
            state["depth"] = depth

        result = run_game(role=role, on_frame=on_frame)
        append_result(log_path, result)
        time.sleep(cfg.end_pause)
        renderer.invalidate()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Run unit tests**

Run: `uv run pytest tests/test_player.py -v`
Expected: 3 PASS.

- [ ] **Step 5: Manual run**

Run in a real terminal: `uv run python -m nethack_screensaver.player` — expect splash, then a centered, colored NetHack game advancing ~10 moves/s; resize the window → re-centers; shrink below 80×24 → "too small" message; Ctrl-C/`kill` ends it. Check `~/.local/state/nethack-screensaver/games.jsonl` gets a line after a game ends (or test quickly with `delay = 0` in config).

- [ ] **Step 6: Commit**

```bash
git add nethack_screensaver/player.py tests/test_player.py
git commit -m "feat: add paced player loop with splash, logging and status line"
```

---

### Task 7: Benchmark script

**Files:**
- Create: `scripts/benchmark.py`

**Interfaces:**
- Consumes: `run_game`, `GameResult`.

- [ ] **Step 1: Write the script**

`scripts/benchmark.py`:
```python
"""Headless AutoAscend benchmark: catches silent regressions from the port.

Usage: uv run python scripts/benchmark.py -n 50 -j 8
"""
import argparse
import statistics
from collections import Counter
from multiprocessing import Pool

from nethack_screensaver.game import run_game


def _one(_):
    return run_game(watchdog_seconds=120)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-n", "--games", type=int, default=50)
    ap.add_argument("-j", "--jobs", type=int, default=4)
    args = ap.parse_args()

    results = []
    with Pool(args.jobs) as pool:
        for i, r in enumerate(pool.imap_unordered(_one, range(args.games)), 1):
            results.append(r)
            print(f"[{i}/{args.games}] {r.role} depth={r.max_depth} score={r.score} turns={r.turns} :: {r.end_reason[:80]}")

    exc = [r for r in results if r.end_reason.startswith("exception")]
    wd = [r for r in results if r.end_reason == "watchdog"]
    print()
    print(f"games            : {len(results)}")
    print(f"median score     : {statistics.median(r.score for r in results)}")
    print(f"median max depth : {statistics.median(r.max_depth for r in results)}")
    print(f"median turns     : {statistics.median(r.turns for r in results)}")
    print(f"exceptions       : {len(exc)}")
    print(f"watchdog         : {len(wd)}")
    for reason, n in Counter(r.end_reason.split(":")[1].strip()[:60] for r in exc).most_common(5):
        print(f"  {n}x {reason}")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run a short benchmark**

Run: `uv run python scripts/benchmark.py -n 8 -j 8`
Expected: completes; exceptions ≤ 1 of 8. If more, fix the top exception in `autoascend/` (record in `PORTING.md`) and re-run.

- [ ] **Step 3: Run the full benchmark and record**

Run: `uv run python scripts/benchmark.py -n 50 -j 8`
Acceptance: exceptions ≤ 5 of 50 and median max depth ≥ 4. Append the summary block to `autoascend/PORTING.md` under `## Benchmark` and report it to the user, alongside upstream AutoAscend's published NeurIPS 2021 challenge median for comparison (look it up; do not invent a number).

- [ ] **Step 4: Commit**

```bash
git add scripts/benchmark.py autoascend/PORTING.md
git commit -m "test: add headless benchmark and record port results"
```

---

### Task 8: Launcher and zsh hook

**Files:**
- Create: `bin/nethack-screensaver` (chmod +x), `zsh/nethack-screensaver.zsh`, `tests/fake_player.py`, `tests/test_launcher.py`

**Interfaces:**
- Consumes: `python -m nethack_screensaver.player` via `<repo>/.venv/bin/python`.
- Env overrides (for tests): `NETHACK_SCREENSAVER_PLAYER` = command to run instead of the player.

- [ ] **Step 1: Write the failing tests**

`tests/fake_player.py`:
```python
"""Stand-in player for launcher tests. Mode via argv[1]: 'run' or 'crash'."""
import sys
import time

if sys.argv[1] == "crash":
    print("boom", file=sys.stderr)
    sys.exit(3)
sys.stdout.write("\x1b[1;1HFAKEPLAYER")
sys.stdout.flush()
time.sleep(60)
```

`tests/test_launcher.py`:
```python
import os
import pty
import select
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LAUNCHER = ROOT / "bin" / "nethack-screensaver"


def _spawn(mode, tmp_path):
    master, slave = pty.openpty()
    env = dict(os.environ,
               XDG_STATE_HOME=str(tmp_path),
               NETHACK_SCREENSAVER_PLAYER=f"{sys.executable} {ROOT/'tests'/'fake_player.py'} {mode}")
    p = subprocess.Popen([str(LAUNCHER)], stdin=slave, stdout=slave, stderr=slave, env=env)
    os.close(slave)
    return p, master


def _read_until(master, needle, timeout=5):
    buf = b""
    end = time.time() + timeout
    while time.time() < end and needle not in buf:
        r, _, _ = select.select([master], [], [], 0.1)
        if r:
            try:
                buf += os.read(master, 4096)
            except OSError:
                break
    return buf


def test_keypress_exits_and_restores(tmp_path):
    p, m = _spawn("run", tmp_path)
    out = _read_until(m, b"FAKEPLAYER")
    assert b"\x1b[?1049h" in out and b"FAKEPLAYER" in out
    os.write(m, b"\x1b[A")  # arrow key: multi-byte
    assert p.wait(timeout=5) == 0
    rest = _read_until(m, b"\x1b[?1049l", timeout=3)
    assert b"\x1b[?1049l" in out + rest
    assert b"\x1b[?25h" in out + rest


def test_player_crash_shows_error_and_restores(tmp_path):
    p, m = _spawn("crash", tmp_path)
    out = _read_until(m, b"\x1b[?1049l", timeout=8)
    assert p.wait(timeout=8) != 0
    assert b"player.log" in out
    assert "boom" in (tmp_path / "nethack-screensaver" / "player.log").read_text()
```

- [ ] **Step 2: Run to verify fail**

Run: `uv run pytest tests/test_launcher.py -v`
Expected: FAIL — launcher not found.

- [ ] **Step 3: Implement the launcher**

`bin/nethack-screensaver`:
```bash
#!/usr/bin/env bash
# NetHack screensaver launcher: owns the tty, runs the player, exits on any key.
set -u

REPO="$(cd "$(dirname "$(readlink -f "$0")")/.." && pwd)"
STATE="${XDG_STATE_HOME:-$HOME/.local/state}/nethack-screensaver"
LOG="$STATE/player.log"
mkdir -p "$STATE"

if [[ ! -t 0 || ! -t 1 ]]; then
    echo "nethack-screensaver: needs an interactive terminal" >&2
    exit 1
fi

if [[ -n "${NETHACK_SCREENSAVER_PLAYER:-}" ]]; then
    read -r -a PLAYER <<<"$NETHACK_SCREENSAVER_PLAYER"
else
    PY="$REPO/.venv/bin/python"
    if [[ ! -x "$PY" ]]; then
        echo "nethack-screensaver: run 'uv sync' in $REPO first" >&2
        exit 1
    fi
    PLAYER=("$PY" -m nethack_screensaver.player)
fi

saved_stty="$(stty -g)"
player_pid=""

cleanup() {
    if [[ -n "$player_pid" ]] && kill -0 "$player_pid" 2>/dev/null; then
        kill -TERM "$player_pid" 2>/dev/null
        for _ in {1..10}; do
            kill -0 "$player_pid" 2>/dev/null || break
            sleep 0.1
        done
        kill -KILL "$player_pid" 2>/dev/null
        wait "$player_pid" 2>/dev/null
    fi
    stty "$saved_stty"
    printf '\e[0m\e[?25h\e[?1049l'
}
trap cleanup EXIT
trap 'exit 130' INT TERM HUP

printf '\e[?1049h\e[?25l\e[2J'
stty raw -echo

nice -n 10 "${PLAYER[@]}" </dev/null 2>>"$LOG" &
player_pid=$!

status=0
while true; do
    if IFS= read -r -s -n 1 -t 0.2 key; then
        # swallow the rest of a multi-byte key (arrows, F-keys, paste)
        while IFS= read -r -s -n 1 -t 0.05 key; do :; done
        break
    fi
    if ! kill -0 "$player_pid" 2>/dev/null; then
        wait "$player_pid"
        status=$?
        player_pid=""
        printf '\e[0m\e[2J\e[1;1Hnethack-screensaver: player exited (%d), see %s' "$status" "$LOG"
        sleep 3
        break
    fi
done
exit "$status"
```

Run: `chmod +x bin/nethack-screensaver`

- [ ] **Step 4: Run tests to verify pass**

Run: `uv run pytest tests/test_launcher.py -v`
Expected: 2 PASS.

- [ ] **Step 5: Write the zsh hook**

`zsh/nethack-screensaver.zsh`:
```zsh
# NetHack screensaver: source from ~/.zshrc.
# Starts after NETHACK_SCREENSAVER_IDLE seconds (default 300) idle at the prompt.
typeset -g _NETHACK_SCREENSAVER_BIN="${${(%):-%x}:A:h:h}/bin/nethack-screensaver"
TMOUT=${NETHACK_SCREENSAVER_IDLE:-300}

TRAPALRM() {
    [[ -o interactive && -t 0 && -t 1 ]] || return 0
    zle && zle -I
    "$_NETHACK_SCREENSAVER_BIN"
    zle && zle reset-prompt
    return 0
}
```

- [ ] **Step 6: Manual checklist (real terminal)**

Open a new zsh, then run `export NETHACK_SCREENSAVER_IDLE=10; source zsh/nethack-screensaver.zsh`. Verify:
1. After 10 s idle at the prompt the game appears.
2. Type `echo hi` (unsubmitted), wait 10 s, press a key → prompt returns with `echo hi` still in the buffer.
3. Press an arrow key to exit → no `^[[A` or stray chars on the prompt.
4. Run `sleep 30` → screensaver does NOT start during it.
5. Resize window while playing → re-centers.
6. `mv .venv .venv.bak`, trigger → error line, terminal intact; `mv` back.
7. `nethack-screensaver` run directly from the prompt works.

- [ ] **Step 7: Commit**

```bash
git add bin/nethack-screensaver zsh/nethack-screensaver.zsh tests/fake_player.py tests/test_launcher.py
git commit -m "feat: add tty-owning launcher and zsh idle hook"
```

---

### Task 9: README and install

**Files:**
- Create: `README.md`
- Modify: `docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md` (idle timeout moved to env var)

- [ ] **Step 1: Write README**

`README.md`:
````markdown
# nethack-screensaver

After 5 minutes idle at your zsh prompt, your terminal shows NetHack played by
[AutoAscend](https://github.com/maciej-sypetkowski/autoascend) (ported to
Python 3.13 / NLE 1.3.0). Any key returns to your prompt.

## Install

```sh
cd ~/screens
uv sync
echo 'source ~/screens/zsh/nethack-screensaver.zsh' >> ~/.zshrc
```

Optional: `ln -s ~/screens/bin/nethack-screensaver ~/.local/bin/` to start it manually.

## Configure

Idle time: `export NETHACK_SCREENSAVER_IDLE=300` (before sourcing the hook).

`~/.config/nethack-screensaver/config.toml` (all optional):

```toml
delay = 0.1          # seconds per move
level_pause = 1.0    # pause on a new dungeon level
end_pause = 5.0      # hold the final screen
status_line = false  # "Game #12 · Val · Dlvl 7 · T:4310 · Best: Dlvl 14"
role = "random"      # or arc bar cav hea kni mon pri ran rog sam tou val wiz
```

Game history: `~/.local/state/nethack-screensaver/games.jsonl`.
Errors: `~/.local/state/nethack-screensaver/player.log`.

## Develop

```sh
uv run pytest                 # fast tests
uv run pytest -m slow         # plays real games
uv run python scripts/benchmark.py -n 50 -j 8
```

AutoAscend is MIT licensed (`autoascend/LICENSE`); port notes in `autoascend/PORTING.md`.
````

- [ ] **Step 2: Update spec**

In the spec's Decisions table and Config section, replace the `idle_timeout` TOML key with: "Idle timeout from env var `NETHACK_SCREENSAVER_IDLE` (default 300), read by the zsh hook so shell startup never runs Python."

- [ ] **Step 3: Full test run**

Run: `uv run pytest -v && uv run pytest -m slow -v`
Expected: all PASS.

- [ ] **Step 4: Commit**

```bash
git add README.md docs/superpowers/specs/2026-10-16-nethack-screensaver-design.md
git commit -m "docs: add README and align spec with idle env var"
```
