---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
# Coding Conventions

**Analysis Date:** 2026-10-22

## Naming Patterns

**Files:**
- Lowercase snake_case modules throughout: `autoascend/exploration_logic.py`, `autoascend/monster_tracker/monster_tracker.py`, `bench/mcp_server.py`, `nethack_screensaver/pacing.py`
- Packages are directories with an `__init__.py`: `autoascend/combat/__init__.py`, `autoascend/item/__init__.py`, `bench/__init__.py`
- Tests are `tests/test_<module>.py` (e.g. `tests/test_bench_store.py` for `bench/store.py`); shared test helpers are `tests/conftest.py`, `tests/bench_fakes.py`, `tests/fake_player.py`
- Entry scripts: `bin/nethack-screensaver`, `scripts/benchmark.py`; console script `screens-bench` maps to `bench.cli:main` (`pyproject.toml`)

**Functions:**
- snake_case, verb-first for actions: `prayer_trouble()` in `autoascend/agent.py`, `run_game()` in `nethack_screensaver/game.py`, `_raise_site()`, `_edit_distance()` in `autoascend/agent.py`
- Module-private helpers are prefixed with a single underscore: `_job()` in `bench/store.py`, `_valid()` in `nethack_screensaver/config.py`, `_ScreenWatchdog` in `nethack_screensaver/game.py`
- Numba-compiled kernels live in `autoascend/utils.py` (`bfs` decorated with `@nb.njit(cache=True)`)

**Variables:**
- snake_case; short coordinate names are normal in grid code (`y`, `x`, `dy`, `dx`, `py`, `px`)
- Module-level constants are UPPER_SNAKE_CASE: `UNSTICK_AFTER`, `CANNOT_KICK` (`autoascend/agent.py`), `MAX_SECONDS`, `ROLES` (`nethack_screensaver/config.py`), `SCHEMA_VERSION`, `END_STATES` (`bench/store.py`), `ANTS` (`bench/metrics.py`)

**Types:**
- Classes are PascalCase: `Agent`, `Level`, `Inventory`, `ItemManager` (`autoascend/`), `FakeWorker` (`tests/bench_fakes.py`), `Store` (`bench/store.py`), `Config` (`nethack_screensaver/config.py`)
- Exceptions are PascalCase and subclass `Exception` directly, grouped in `autoascend/exceptions.py`: `AgentFinished`, `AgentPanic`, `AgentChangeStrategy`
- Value records use `namedtuple` (`BLStats` in `autoascend/agent.py`) or `@dataclass(frozen=True)` (`Config` in `nethack_screensaver/config.py`, `Metric` in `bench/metrics.py`)
- Enums use `enum`-style classes such as `Milestone` referenced in `autoascend/plans.py`

## Code Style

**Formatting:**
- No formatter configuration is committed (no `pyproject.toml` `[tool.ruff]`/`[tool.black]` section, no `.editorconfig`, no `.pre-commit-config.yaml`).
- Observed style: 4-space indentation, double quotes in most modules, single quotes in `autoascend/` and `autoascend/item/`. Match the surrounding file rather than imposing one quote style.
- Line length is loose: long lines of 100-140 characters are common (e.g. the `BLStats` namedtuple field list in `autoascend/agent.py`). Wrap new code at roughly 100 to 110 columns.
- Blank lines: two blank lines between top-level definitions, one between methods.

**Linting:**
- No linter is configured in the repository. Do not assume ruff/flake8 rules are enforced.
- Existing suppression comments that do appear: `# noqa: F401` in `tests/test_imports.py` (intentional side-effect import).
- Wildcard imports are used to re-export constants in `autoascend/glyph/screen_symbols.py` (`from .screen_symbol_consts import *`) and `autoascend/objects/__init__.py`. Do not add new wildcard imports in new code; import names explicitly.

**Type hints:**
- Hints are sparse. Newer `bench/` code uses them (`Callable`, `Any` in `bench/metrics.py`; `-> ` return annotations in `bench/server.py`). `autoascend/` is mostly unannotated.
- For new `bench/` code, annotate public function signatures. For `autoascend/`, follow the unannotated style of the file being edited.

## Import Organization

**Order (observed):**
1. Standard library (`contextlib`, `traceback`, `re`, `collections`, `functools`, `json`, `sqlite3`, `threading`, `pathlib`)
2. Third-party (`nle.nethack`, `numpy`, `numba`, `cv2`, `toolz`, `pytest`)
3. Local relative imports (`from . import combat`, `from .exceptions import AgentPanic`)

Example from `autoascend/agent.py`:

```python
import contextlib
import traceback
import re
from collections import namedtuple, Counter, defaultdict

import nle.nethack as nh
import numpy as np

from . import combat
from .exceptions import AgentPanic, AgentFinished, AgentChangeStrategy
```

**Test imports** (`tests/test_bench_server.py`, `tests/test_game.py`): stdlib, then `pytest`, then project modules. Test modules import project code with absolute imports (`from bench.store import Store`, `from nethack_screensaver import game`). Helpers under `tests/` are imported by bare module name (`from bench_fakes import FakeWorker, game`), which works because pytest puts `tests/` on the path.

**Path Aliases:** None. All imports are package-relative or absolute from the repo root.

## Error Handling

**Patterns:**
- Game-control flow uses custom exceptions for non-error exits. The agent raises `AgentFinished` to end a game, `AgentChangeStrategy` to switch plans, and `AgentPanic` to abandon the current action and let the main loop retry. Catch these narrowly, as in `autoascend/agent.py` around the `except AgentChangeStrategy as e:` blocks.
- Broad catches are allowed only where the code must not crash the host, and they are commented. Example from `autoascend/global_logic.py`: `except Exception:  # measuring must never end a game`. Keep any new broad catch next to a one-line comment that explains why.
- Crash reports capture the bot frames that raised. `_raise_site()` in `autoascend/agent.py` builds a `file:line function` chain from a traceback, filtered to `autoascend` frames. Reuse it for crash reporting instead of formatting tracebacks by hand.
- Bench store errors fail loudly on incompatible state: `Store.__init__` in `bench/store.py` raises `RuntimeError` when the on-disk schema version differs from `SCHEMA_VERSION`.
- Database writes run inside `with self._db:` blocks, and all access is serialized with `self._lock` (an `RLock`), as in `bench/store.py`.
- Metric evaluation treats a missing field as "skip this metric for this game": a `KeyError` is caught per metric in `bench/metrics.py`. Do the same when reading stored game JSON, since older games lack newer fields.

**Validation:**
- Config values are validated on load in `nethack_screensaver/config.py` (`_valid()`), and out-of-range values are clamped to `MAX_SECONDS`. Add new config keys through that path.

## Logging

**Framework:** None. The project does not use the `logging` module. Output goes through `print()` and the game UI.

**Patterns:**
- Debug output inside the agent is a bare `print(f'PANIC!!!! : {exc}')` (`autoascend/agent.py`). Do not add new `print` calls to library code; return or record data instead.
- Game statistics are recorded through `autoascend/stats_logger.py` and `nethack_screensaver/gamelog.py`, not by printing.
- The bench CLI (`bench/cli.py`) and the scripts under `scripts/` print user-facing output directly. `print` is acceptable there.
- Commented-out debug prints are left in place in `autoascend/combat/fight_heur.py` and `autoascend/item/inventory.py`. Do not copy this pattern.

## Comments

**When to Comment:**
- Comments explain *why* a threshold or workaround exists, with the source behaviour in mind. Examples: `# steps without game time after which the bot lets a turn pass` above `UNSTICK_AFTER` in `autoascend/agent.py`; `# NetHack's answers to #kick when it refuses` above `CANNOT_KICK`; `# a commit from before seeding leaves it out` in `tests/bench_fakes.py`.
- Keep inline comments for game-rule references (NetHack wiki sections are cited in `prayer_trouble()` docstring in `autoascend/agent.py`).

**Docstrings:**
- Module docstrings are common and describe the module's purpose and contract, e.g. `bench/store.py`, `bench/metrics.py`, `nethack_screensaver/config.py`.
- Function docstrings are one or two sentences in imperative or descriptive form, e.g. `"""Pray for low HP (upstream thresholds) or severe hunger with nothing to eat."""`. No Sphinx or Google-style sections are used.
- Do not add a docstring to trivial private helpers.

## Function Design

**Size:** Core agent logic in `autoascend/agent.py` is large and stateful. New logic should go into the focused module that owns it (`autoascend/combat/`, `autoascend/item/`, `autoascend/exploration_logic.py`), not into `Agent`.

**Parameters:**
- Keyword-only parameters are used for tuning flags in utility code: `bfs(y, x, *, walkable, walkable_diagonally, can_squeeze)` in `autoascend/utils.py`.
- Test fixtures and helpers take explicit arguments (`bench_app(tmp_path, bench_repo)`).

**Return Values:**
- Plain data returned as dicts from bench code (`Store.games()` returns dict lists, `bench/metrics.py` metric functions return `bool` or `number`).
- Game results are dataclass or namedtuple objects that are serialized with `dataclasses.asdict` and `json.dumps` (see `nethack_screensaver/game.py` and `tests/test_game.py`). Keep results JSON-serializable.

## Module Design

**Exports:**
- Modules expose functions and classes directly. There is no `__all__` convention in the project code.
- Strategy and plan registration is by dict: `STRATEGIES` in `autoascend/plans.py` maps names to `StrategySpec` values, and tests extend it with `monkeypatch.setitem` (see `tests/test_game.py`). Register new strategies there.
- Bench metrics are registered by adding one entry to `METRICS` in `bench/metrics.py`.

**Barrel Files:**
- `__init__.py` files re-export selectively (`autoascend/glyph/__init__.py`, `autoascend/item/__init__.py`). Import from the submodule when the name is not re-exported.

**Repository conventions worth following:**
- Keep `autoascend/` free of heavy optional dependencies. `tests/test_imports.py` fails if `torch`, `ray`, `matplotlib`, `seaborn`, `pandas`, `nltk`, or `gym` get imported.
- The ascension route is the only plan that counts (see `docs/ASCENSION-GUIDE.md`). New strategy code should target that route.

---

*Convention analysis: 2026-10-22*
