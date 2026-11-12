---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
# Coding Conventions

**Analysis Date:** 2026-11-12

## Naming Patterns

**Files:**
- Python modules are lowercase snake_case: `autoascend/castle.py`, `autoascend/monster_tracker/kernels.py`, `bench/scheduler.py`.
- Packages are directories with an `__init__.py`: `autoascend/combat/__init__.py`, `autoascend/item/__init__.py`, `autoascend/glyph/__init__.py`.
- Tests are `tests/test_<module>.py` mirroring the module name: `tests/test_castle.py` covers `autoascend/castle.py`, `tests/test_bench_store.py` covers `bench/store.py`. Shared test helpers are plain modules in `tests/` (`tests/bench_fakes.py`, `tests/fake_player.py`), not `conftest` imports.
- Scripts under `scripts/` are standalone CLI entry points (`scripts/benchmark.py`, `scripts/staged_run.py`, `scripts/replay_check.py`).
- Non-Python: `bin/nethack-screensaver` (launcher), `zsh/nethack-screensaver.zsh`.

**Functions:**
- snake_case, verb-first for actions: `melee_monster_priority` (`autoascend/combat/fight_heur.py`), `seen_courtyard` (`tests/test_castle.py`), `items_to_unload` (`autoascend/item/inventory.py`).
- Private helpers use a leading underscore: `_item` (`tests/test_inventory_unload.py`), `_game` (`tests/test_bench_store.py`).
- Predicates read as questions or `is_`/`has_`/`can_` prefixes: `is_monster_faster`, `is_dangerous_monster` (`autoascend/combat/monster_utils.py`), `is_unambiguous`, `can_be_dropped_from_inventory` (`autoascend/item/item.py`).
- Test functions are `test_<behaviour in words>`, often long and descriptive: `test_unload_drops_heaviest_spare_items_first_and_food_last`, `test_store_survives_reopening`.

**Variables:**
- snake_case locals. Short coordinate names are the norm in grid code: `y`, `x`, `dy`, `dx`, `p` for a position tuple. Screen coordinates are `(y, x)` tuples throughout.
- Module-level constants are UPPER_SNAKE_CASE: `EYE_CORPSE_MAX_AGE`, `TELEPATHY_MESSAGES`, `MAP`, `WIDTH`, `ORIGIN` (`autoascend/castle.py`), `SHAPE` (`tests/test_castle.py`).
- Game monster/object names are lowercase strings matching NetHack's own names: `EYE = 'floating eye'`, `'food ration'`, `'long sword'`.
- Single-quoted and double-quoted strings are both used; no enforced quote style.

**Types:**
- Type hints are rare. Only about 11 files under `autoascend/` contain `->` annotations. Assume untyped code unless the surrounding module already annotates.
- Lightweight records use `dataclasses.dataclass` in `bench/` and `nethack_screensaver/` (15 occurrences) and `SimpleNamespace` in tests for fake objects.
- Classes are CapWords: `Item` (`autoascend/item/item.py`), `Scheduler` (`bench/scheduler.py`), `FakeWorker` (`tests/bench_fakes.py`), `AgentFinished` (`autoascend/exceptions.py`).

## Code Style

**Formatting:**
- No formatter configured in `pyproject.toml`. No `.prettierrc`, `ruff`, `black`, or `.editorconfig` detected.
- Observed style: 4-space indent, lines commonly up to about 120 columns (`autoascend/castle.py` docstring lines, `tests/test_castle.py`), with backslash continuations used for long imports and assignments: `from .monster_utils import is_monster_faster, ... \` in `autoascend/combat/fight_heur.py`.
- Keep the existing style of the file you edit; do not reformat unrelated code.

**Linting:**
- No linter configured (no ruff/flake8/pylint/mypy config in `pyproject.toml`).
- Only enforced check is pytest's `filterwarnings = ["error:overflow encountered:RuntimeWarning"]` in `pyproject.toml`: numeric overflow warnings fail tests.

**Dead code:**
- Commented-out debug prints and alternate branches are left in place: e.g. `# print('--------------', dy, dx)` in `autoascend/combat/fight_heur.py`, and `# if not wielding_melee_weapon(agent):` above a live `ret -= 5` line. Do not add more; remove commented code you touch when it is clearly obsolete.

## Import Organization

**Order (observed in `autoascend/combat/fight_heur.py`, `bench/server.py`, `tests/test_castle.py`):**
1. Standard library (`import subprocess`, `import threading`, `from collections import defaultdict`).
2. Third-party (`import numpy as np`, `from scipy import signal`, `import nle.nethack as nh`, `import pytest`).
3. Project imports, absolute or relative (see below).

Separate groups with one blank line.

**Relative vs absolute:**
- Inside the `autoascend` package, relative imports are the norm: `from ..glyph import G, MON`, `from .utils import ...` (about 86 relative imports in the package).
- Tests and `bench/` use absolute imports: `from autoascend import castle`, `from bench.store import Store`.
- Tests import shared helpers as top-level modules: `from bench_fakes import FakeWorker, game`.
- Some tests add `scripts/` to `sys.path` manually: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))` in `tests/test_nld_study.py` and `tests/test_seeded_scripts.py`. Prefer importing from `autoascend`/`bench`; avoid adding more `sys.path` hacks.

**Path aliases:** None.

## Module Structure

**Module docstrings:** Present in about 42 files under `autoascend/`, `bench/`, and `nethack_screensaver/`. Used to record game-mechanics facts with source references, for example `autoascend/castle.py` cites NetHack 5.0 `dat/castle.lua` and `trap.c` line-level behaviour. Follow this pattern when a module encodes non-obvious game rules: state the rule and cite the NetHack source file (and function/line if known).

**Constants blocks:** Game data is declared as module-level tuples and dicts at the top of the module (`MAP`, `KEY_SQUARES` in `autoascend/castle.py`; `TELEPATHY_MESSAGES` in `autoascend/telepathy.py`), followed by functions.

**Barrel files:** `__init__.py` files re-export the public names of their package (see `autoascend/item/__init__.py`, `autoascend/objects/__init__.py`, `autoascend/glyph/__init__.py`). Add new public names there when other packages need them.

## Error Handling

**Control-flow exceptions:**
- Agent control flow uses custom exception classes in `autoascend/exceptions.py`: `AgentFinished`, `AgentPanic`, `AgentChangeStrategy`. Raise these to unwind to the strategy loop rather than returning error codes.
- Generator-based strategies signal completion with `StopIteration`. The pattern `except StopIteration as e:` appears throughout `autoascend/strategy.py` and `autoascend/utils.py` to read a generator's return value.

**Narrow exceptions at I/O boundaries:**
- Catch specific types with an inline comment explaining why: `except (OSError, ValueError):  # missing file, network error: retried next time` (`bench/importers.py`), `except KeyError:  # a game without the metric's field` (`bench/scheduler.py`), `except ValueError:` in `bench/filters.py`.
- Follow this form for new code.

**Bare except (avoid):**
- `autoascend/item/item_manager.py` uses a bare `except:` with a TODO for the blind case. Do not copy this; use `except Exception:` at minimum, and scope it to the expected failure.

**Validation:** Inputs to the bench server and CLI are validated in place (`bench/filters.py`, `bench/cli.py`) rather than through a schema library.

## Logging

**Framework:** None. No `logging` module use detected in `autoascend/`, `bench/`, or `nethack_screensaver/`.

**Patterns:**
- The CLI in `bench/cli.py` writes user-facing output with `print(...)`, with `flush=True` for server start-up lines.
- Scripts in `scripts/` print JSON lines (`print(json.dumps(asdict(r)))` in `scripts/staged_run.py`) so output is machine-consumable. Keep that contract when extending a script.
- Game-run statistics go to `autoascend/stats_logger.py`, not to stdout.

## Comments

**When to comment:**
- Explain game-rule rationale and cite sources (see module docstrings above).
- Reference staged seed results where a rule was derived from a replay, e.g. `# staged seed 1` in `tests/test_castle.py`.
- Mark known gaps with `# TODO:` (e.g. `autoascend/item/item_manager.py`).

**Caution on references:** Several comments and docstrings cite `.planning/STATE.md` (e.g. `autoascend/castle.py` header) and "staged seeds" results. The `.planning/` tree was reset (commit `af6684a`), so those citations may not resolve. When writing new comments, cite the NetHack source file and function, or a path that exists in the repo (`.planning/research/` for notes).

**JSDoc/TSDoc:** Not applicable. Python docstrings are used instead: triple-double-quoted, a one-line summary then a bullet list for facts (see `autoascend/castle.py`). Test helper functions use one-line docstrings (`seen_courtyard` in `tests/test_castle.py`).

## Function Design

**Size:** Large functions are common in the agent logic (strategy, combat priority). Prefer extracting pure helpers that take `(agent, monsters, monster)` or plain numpy masks, as the combat and castle modules do, so they can be unit tested without a live game.

**Parameters:** Pass the `agent` object explicitly to combat and item helpers (`melee_monster_priority(agent, monsters, monster)`). Monster entries are tuples `(_, y, x, mon, _)`.

**Return values:** Return `None` for "unknown" when the value cannot be determined (`castle.frame(...)` returns `True`, `False`, or `None`). Document tri-state returns in the docstring.

**Grid data:** Use numpy boolean arrays of shape `(21, 79)` for screen masks (`SHAPE` in `tests/test_castle.py`). Index with `(y, x)` tuples.

## Module Design

**Exports:** No `__all__` convention detected. Public names are plain module-level identifiers.

**Dataclasses over dicts** for structured records in `bench/` (`dataclass` used in 15 places). Stored game records in `bench/store.py` are dicts, though (`{"max_depth": ..., "end_reason": ...}`); keep the dict shape when touching them.

**Serialization:** Store and report layers use JSON and SQLite (`bench/store.py`, `tests/test_bench_store.py` uses `sqlite3` directly).

---

*Convention analysis: 2026-11-12*
