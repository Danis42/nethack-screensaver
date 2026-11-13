<!-- GSD:project-start source:PROJECT.md -->

## Project

**NetHack Screensaver: Ascension**

A terminal screensaver that plays NetHack 5.0 after the zsh prompt has been idle, driven by
AutoAscend, a hand-written rule/strategy bot ported to Python 3.13 / NLE 1.3.0. A benchmark
system (`bench/`) plays thousands of headless games per git commit and compares versions.
The project now aims at one goal: make the bot ascend. It's for the owner's own terminal and
curiosity, not for a product or for customers.

**Core Value:** **The bot wins one fresh, clean game of NetHack 5.0 (ascends) with no human input, no rewinds
and no reseeding. Every claim of progress toward it can be checked.**

### Constraints

- **Game:** NetHack 5.0 via the local NLE 1.3.0 build (`reference/nle-src`, branch `screens-nh5`) — that's what the screensaver plays
- **Language/runtime:** Python 3.13 with uv; the existing `autoascend` / `nethack_screensaver` / `bench` packages — existing code and tooling
- **Hardware:** one local Linux machine; bench has 10 worker slots — this limits how many games each experiment can play
- **Determinism:** the bench must stay deterministic per seed (no randomness that breaks A/A comparison); any non-deterministic component (e.g. an LLM) needs a plan for measurement
- **Proof:** no progress claim without a job ID, commit or query result the owner can check — trust was broken last time
- **Clean goal:** the final ascension must be one straight game with no human input, rewind or reseed
- **No additional cost:** LLM work uses local models (Ollama on an RTX 4070 Ti, 12 GB VRAM, 32 GB RAM) and the existing Claude subscription via Claude Code; no paid API tokens or cloud services. One exception (owner-approved 2026-11-13): free-tier cloud LLM APIs may be used for small research and well-defined helper jobs, if (1) prompts carry public content only (NetHack facts, wiki text), never repo code, bench data or personal details; (2) answers are leads, verified against the 5.0 source or the web before the bot relies on them; (3) nothing in game play or bench measurement depends on them; (4) the client tool is scanned (SkillSpector) before install
- **Exploits need approval:** farming or exploits are allowed in principle, but each one is proposed to the owner first so they can judge the behaviour

<!-- GSD:project-end -->

<!-- GSD:stack-start source:codebase/STACK.md -->

## Technology Stack

## Languages

- Python 3.13 (`requires-python = ">=3.13,<3.14"` in `pyproject.toml`; pinned via `.python-version`) - all bot logic in `autoascend/`, the screensaver front end in `nethack_screensaver/`, the benchmark system in `bench/`, and helper scripts in `scripts/`
- Python test code in `tests/` (pytest)
- C - a small LD_PRELOAD shim compiled at runtime from a string literal in `nethack_screensaver/fixed_clock.py` (`cc -O2 -shared -fPIC`), replacing libc `time()` for seeded games
- C (NetHack 3.6 / 5.0 sources, vendored) - game engine under `reference/nethack-3.6.6/`, `reference/nethack-5.0.0/`, and the NLE build tree `reference/nle-src/`
- Zsh - shell hook in `zsh/nethack-screensaver.zsh` (idle-prompt trigger)
- Bash - launcher `bin/nethack-screensaver`

## Runtime

- CPython 3.13 (uv-managed; the local `.venv/pyvenv.cfg` points at `~/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu`)
- Target platform: Linux with a zsh terminal (`uname` platform in project environment is Linux; the zsh hook and `/proc`-style tooling assume POSIX)
- The NetHack engine itself is provided by NLE (NetHack Learning Environment) compiled from source; `nle.nethack` is imported throughout `autoascend/glyph/`
- uv (`uv 0.12.10` recorded in `.venv/pyvenv.cfg`)
- Lockfile: present - `uv.lock` (root of repo)
- NLE is not on PyPI for this fork; `pyproject.toml` resolves it from a local path: `[tool.uv.sources] nle = { path = "reference/nle-src" }` (branch `screens-nh5`, NetHack 5.0)

## Frameworks

- NLE (NetHack Learning Environment) - Gym-style environment wrapping NetHack; `nle` package, built from `reference/nle-src` (`autoascend/env_wrapper.py` is the bot-side wrapper)
- NetHack 5.0 (via the local NLE build) - the bot's game target; `autoascend/glyph/nh5.py` holds version-specific glyph handling. NetHack 3.6.6 sources are also vendored in `reference/nethack-3.6.6/` for comparison (README benchmarks cite NetHack 3.6)
- `http.server` (stdlib) - benchmark dashboard/API server in `bench/server.py` (`ThreadingHTTPServer`)
- `mcp` 2.3.0 (`mcp>=2.3`, bench dependency group) - MCP server exposing bench tools in `bench/mcp_server.py` (`@mcp.tool()` decorators)
- pytest 9.1.1 (`pytest>=8` in dev group) - configured in `pyproject.toml` `[tool.pytest.ini_options]`; default `addopts = "-m 'not slow'"`, `slow` marker = games that take minutes
- Test fixtures: `tests/conftest.py`, `tests/fake_player.py`, `tests/bench_fakes.py`
- hatchling - build backend (`[build-system]` in `pyproject.toml`); wheel packages: `autoascend`, `nethack_screensaver`, `bench`
- uv - dependency resolution, sync, and `uv run` entry point
- cmake/pip build for NLE (`reference/nle-src/CMakeLists.txt`, `reference/nle-src/pyproject.toml`)
- Console script: `screens-bench = "bench.cli:main"` (`[project.scripts]`)

## Key Dependencies

- `nle` (local path, NetHack 5.0 branch) - the game engine; without it nothing runs
- `numpy` 2.5.4 (lock; constraint `>=2.0`) - tty-char/glyph arrays throughout `autoascend/`, `nethack_screensaver/`
- `numba` 0.68.0 (lock; constraint `>=0.61`) - JIT kernels in `autoascend/monster_tracker/kernels.py`, and imported in other hot paths
- `opencv-python-headless` 5.0.0.93 (lock; constraint `>=4.10`) - imaging on rendered screen arrays (`cv2` imports)
- `scipy` 1.18.1 (lock; constraint `>=1.14`) - numerical helpers
- `toolz` 1.2.0 (lock; constraint `>=1.0`) - functional utilities
- `mcp` 2.3.0 (lock) - bench MCP server (`bench/mcp_server.py`), bench dependency group only
- Standard library heavy use: `sqlite3` (`bench/store.py`, `scripts/nld_study.py`), `urllib` (`bench/importers.py`, `bench/cli.py`, `scripts/*`), `subprocess` (git and child game processes), `tomllib` (`nethack_screensaver/config.py`), `multiprocessing` / `concurrent` (`bench/worker.py`, `bench/scheduler.py`)
- `pytest` 9.1.1 - test runner (dev group)

## Configuration

- No `.env` file is present in the repository root (checked by existence only; contents not read)
- Runtime environment variables read by code:
- `~/.config/nethack-screensaver/config.toml` - parsed with `tomllib`; schema and defaults in `nethack_screensaver/config.py` (`delay`, `fast_delay`, `level_pause`, `end_pause`, `status_line`, `role`, `strategy`, `reveal_goal`)
- `pyproject.toml` - project metadata, dependencies, hatch wheel targets, pytest config, uv sources
- `uv.lock` - pinned resolution
- `.python-version` - `3.13`
- `reference/nle-src/CMakeLists.txt`, `reference/nle-src/pyproject.toml` - NLE native build
- `.mcp.json` - registers the bench MCP server for Claude Code (`bench/mcp_server.py`)
- `.gitignore` - excludes generated and local state (includes `archive/`)

## Persistent State and Storage Locations

- Game history: `~/.local/state/nethack-screensaver/games.jsonl` (`nethack_screensaver/paths.py`, `nethack_screensaver/gamelog.py`)
- Error log: `~/.local/state/nethack-screensaver/player.log`
- Bench SQLite database: under `SCREENS_BENCH_DATA` (default `~/.local/share/screens-bench`); schema in `bench/store.py` (tables `meta`, `games`, `jobs`, `reference_games`)
- Bench worktrees and cache: `~/.cache/screens-bench/` (each committed ref runs from its own git worktree)
- Fixed-clock shim cache: `$XDG_CACHE_HOME/screens` (default `~/.cache/screens`) (`nethack_screensaver/fixed_clock.py`)

## Platform Requirements

- Linux, Python 3.13, uv
- A C toolchain (`cc`) for the fixed-clock LD_PRELOAD shim and for building NLE
- `nm` (binutils) for `nethack_screensaver/dungeon_truth.py` symbol lookup
- `git` on PATH (bench uses `git -C <repo>` through `bench/gitrefs.py`)
- Optional: a local Ollama server on `localhost:11434` for the wiki sweep / triage scripts (see INTEGRATIONS.md)
- The zsh shell for the idle hook (`zsh/nethack-screensaver.zsh`)
- Runs locally in the user's terminal; no server deployment, no container, no CI config present in the repository

<!-- GSD:stack-end -->

<!-- GSD:conventions-start source:CONVENTIONS.md -->

## Conventions

## Naming Patterns

- Python modules are lowercase snake_case: `autoascend/castle.py`, `autoascend/monster_tracker/kernels.py`, `bench/scheduler.py`.
- Packages are directories with an `__init__.py`: `autoascend/combat/__init__.py`, `autoascend/item/__init__.py`, `autoascend/glyph/__init__.py`.
- Tests are `tests/test_<module>.py` mirroring the module name: `tests/test_castle.py` covers `autoascend/castle.py`, `tests/test_bench_store.py` covers `bench/store.py`. Shared test helpers are plain modules in `tests/` (`tests/bench_fakes.py`, `tests/fake_player.py`), not `conftest` imports.
- Scripts under `scripts/` are standalone CLI entry points (`scripts/benchmark.py`, `scripts/staged_run.py`, `scripts/replay_check.py`).
- Non-Python: `bin/nethack-screensaver` (launcher), `zsh/nethack-screensaver.zsh`.
- snake_case, verb-first for actions: `melee_monster_priority` (`autoascend/combat/fight_heur.py`), `seen_courtyard` (`tests/test_castle.py`), `items_to_unload` (`autoascend/item/inventory.py`).
- Private helpers use a leading underscore: `_item` (`tests/test_inventory_unload.py`), `_game` (`tests/test_bench_store.py`).
- Predicates read as questions or `is_`/`has_`/`can_` prefixes: `is_monster_faster`, `is_dangerous_monster` (`autoascend/combat/monster_utils.py`), `is_unambiguous`, `can_be_dropped_from_inventory` (`autoascend/item/item.py`).
- Test functions are `test_<behaviour in words>`, often long and descriptive: `test_unload_drops_heaviest_spare_items_first_and_food_last`, `test_store_survives_reopening`.
- snake_case locals. Short coordinate names are the norm in grid code: `y`, `x`, `dy`, `dx`, `p` for a position tuple. Screen coordinates are `(y, x)` tuples throughout.
- Module-level constants are UPPER_SNAKE_CASE: `EYE_CORPSE_MAX_AGE`, `TELEPATHY_MESSAGES`, `MAP`, `WIDTH`, `ORIGIN` (`autoascend/castle.py`), `SHAPE` (`tests/test_castle.py`).
- Game monster/object names are lowercase strings matching NetHack's own names: `EYE = 'floating eye'`, `'food ration'`, `'long sword'`.
- Single-quoted and double-quoted strings are both used; no enforced quote style.
- Type hints are rare. Only about 11 files under `autoascend/` contain `->` annotations. Assume untyped code unless the surrounding module already annotates.
- Lightweight records use `dataclasses.dataclass` in `bench/` and `nethack_screensaver/` (15 occurrences) and `SimpleNamespace` in tests for fake objects.
- Classes are CapWords: `Item` (`autoascend/item/item.py`), `Scheduler` (`bench/scheduler.py`), `FakeWorker` (`tests/bench_fakes.py`), `AgentFinished` (`autoascend/exceptions.py`).

## Code Style

- No formatter configured in `pyproject.toml`. No `.prettierrc`, `ruff`, `black`, or `.editorconfig` detected.
- Observed style: 4-space indent, lines commonly up to about 120 columns (`autoascend/castle.py` docstring lines, `tests/test_castle.py`), with backslash continuations used for long imports and assignments: `from .monster_utils import is_monster_faster, ... \` in `autoascend/combat/fight_heur.py`.
- Keep the existing style of the file you edit; do not reformat unrelated code.
- No linter configured (no ruff/flake8/pylint/mypy config in `pyproject.toml`).
- Only enforced check is pytest's `filterwarnings = ["error:overflow encountered:RuntimeWarning"]` in `pyproject.toml`: numeric overflow warnings fail tests.
- Commented-out debug prints and alternate branches are left in place: e.g. `# print('--------------', dy, dx)` in `autoascend/combat/fight_heur.py`, and `# if not wielding_melee_weapon(agent):` above a live `ret -= 5` line. Do not add more; remove commented code you touch when it is clearly obsolete.

## Import Organization

- Inside the `autoascend` package, relative imports are the norm: `from ..glyph import G, MON`, `from .utils import ...` (about 86 relative imports in the package).
- Tests and `bench/` use absolute imports: `from autoascend import castle`, `from bench.store import Store`.
- Tests import shared helpers as top-level modules: `from bench_fakes import FakeWorker, game`.
- Some tests add `scripts/` to `sys.path` manually: `sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))` in `tests/test_nld_study.py` and `tests/test_seeded_scripts.py`. Prefer importing from `autoascend`/`bench`; avoid adding more `sys.path` hacks.

## Module Structure

## Error Handling

- Agent control flow uses custom exception classes in `autoascend/exceptions.py`: `AgentFinished`, `AgentPanic`, `AgentChangeStrategy`. Raise these to unwind to the strategy loop rather than returning error codes.
- Generator-based strategies signal completion with `StopIteration`. The pattern `except StopIteration as e:` appears throughout `autoascend/strategy.py` and `autoascend/utils.py` to read a generator's return value.
- Catch specific types with an inline comment explaining why: `except (OSError, ValueError):  # missing file, network error: retried next time` (`bench/importers.py`), `except KeyError:  # a game without the metric's field` (`bench/scheduler.py`), `except ValueError:` in `bench/filters.py`.
- Follow this form for new code.
- `autoascend/item/item_manager.py` uses a bare `except:` with a TODO for the blind case. Do not copy this; use `except Exception:` at minimum, and scope it to the expected failure.

## Logging

- The CLI in `bench/cli.py` writes user-facing output with `print(...)`, with `flush=True` for server start-up lines.
- Scripts in `scripts/` print JSON lines (`print(json.dumps(asdict(r)))` in `scripts/staged_run.py`) so output is machine-consumable. Keep that contract when extending a script.
- Game-run statistics go to `autoascend/stats_logger.py`, not to stdout.

## Comments

- Explain game-rule rationale and cite sources (see module docstrings above).
- Reference staged seed results where a rule was derived from a replay, e.g. `# staged seed 1` in `tests/test_castle.py`.
- Mark known gaps with `# TODO:` (e.g. `autoascend/item/item_manager.py`).

## Function Design

## Module Design

<!-- GSD:conventions-end -->

<!-- GSD:architecture-start source:ARCHITECTURE.md -->

## Architecture

## System Overview

```text

```

## Pattern Overview

- The bot is a hand-written priority/strategy system, not a learned policy. Decisions are made by `Strategy` objects that are generator-based (`autoascend/strategy.py`), and by `Agent.preempt(...)` interrupts (`autoascend/agent.py`, `Agent.preempt` at ~line 325).
- High-level goals are ordered lists of `Milestone` values. Each named strategy is a tuple of milestones in `autoascend/plans.py` (`STRATEGIES`, `DEFAULT_PLAN`, `choose_strategy`). The `GlobalLogic` class in `autoascend/global_logic.py` (`class GlobalLogic`, ~line 227) turns the current milestone into concrete actions.
- The game is accessed through a single gymnasium-style adapter, `autoascend/env_wrapper.py` (`EnvWrapper.step`), which feeds observations into `Agent.update`. The agent calls back into the wrapper through `on_step`, `choose_plan`, and `prepare` callables that `nethack_screensaver/game.py` injects.
- Pure logic modules are kept free of game access so they can be unit-tested and imported by the bench server. Examples: `autoascend/boulders.py` ("standard library + numpy only, no game access"), `autoascend/digging.py`, `autoascend/prayer.py`, `autoascend/ladder.py` ("standard library only, so the bench server can import the rung list"), `autoascend/castle.py`, `autoascend/passtune.py`, `autoascend/medusa.py`, `autoascend/quest_portal.py`, `autoascend/stuck.py`.
- Dependencies point one way. `nethack_screensaver` and `bench` import from `autoascend`. `autoascend` does not import from `nethack_screensaver` or `bench` (verified by grep: no matches in `autoascend/`). The one exception is `bench/` importing `nethack_screensaver.fixed_clock`.
- Process isolation for benchmarking. Each game batch runs in a child Python process (`bench/worker.py`) whose `PYTHONPATH` points at a git worktree of the commit under test. The bench server itself never imports game code from the working tree being edited.

## Layers

- Purpose: Start the screensaver on idle, own the terminal, exit on keypress.
- Location: `zsh/nethack-screensaver.zsh`, `bin/nethack-screensaver`
- Contains: zsh `TMOUT`/`TRAPALRM` hook; bash launcher that sets raw mode, backgrounds the Python player under `nice -n 10`, and drains input on exit.
- Depends on: `.venv/bin/python` created by `uv sync`.
- Used by: the user's `~/.zshrc` (`source ~/screens/zsh/nethack-screensaver.zsh`).
- Purpose: Loop forever: play one game, record it, show it, pause, repeat.
- Location: `nethack_screensaver/`
- Contains: `player.py` (`main()` loop), `game.py` (`run_game`, `GameResult`, watchdog, death context), `render.py` (`Renderer`, `format_status`, `format_reveal`), `pacing.py` (`Pacer` fast-forward), `config.py` (`Config`, `load_config`), `paths.py` (`config_path`, `state_dir`), `gamelog.py` (`append_result`, `read_stats`), `snapshots.py`, `dungeon_truth.py`, `fixed_clock.py`, `staging.py`.
- Depends on: `autoascend` (plans, env wrapper, global logic, item), `nle`.
- Used by: `bin/nethack-screensaver` (as `python -m nethack_screensaver.player`), and by `bench/worker.py` (which calls `game.run_game` directly).
- Purpose: Perceive the screen, maintain game state, and choose actions.
- Location: `autoascend/`
- Contains:
- Depends on: `nle.nethack`, `numpy`, `cv2` (in `exploration_logic.py`), `scipy`, `numba` (via dependencies in `pyproject.toml`).
- Used by: `nethack_screensaver/game.py`, `scripts/`, `tests/`, and `bench/` (only `autoascend.ladder.RUNGS` and `autoascend.objects`).
- Purpose: Play bot games per commit at scale, persist results, judge experiments, and expose the results over HTTP and MCP.
- Location: `bench/`
- Contains:
- Depends on: stdlib, `mcp` (bench dependency group), `autoascend.ladder`, `nethack_screensaver.fixed_clock`.
- Used by: the user through `uv run screens-bench serve` and by Claude through `.mcp.json`.
- Purpose: Research tooling, one-off studies, and benchmarks. Not part of the installed package.
- Location: `scripts/`
- Contains: `benchmark.py` (headless benchmark, `-n`, `-j`), `scenario_run.py` + `scenario_lib.py`, `staged_run.py`, `seeded_report.py`, `replay_check.py`, `rewind.py`, `handplay.py`, `nld_study.py`, `bench_watch.py`, `fixes_triage.py`, `fixes_shortlist.py`, `item_selftest.py`, `gen_objects_data.py`, `wiki_sweep/`.
- Depends on: `autoascend`, `nethack_screensaver`, `bench` as needed.
- Used by: developers directly (`uv run python scripts/<name>.py`).

## Data Flow

### Primary Request Path (screensaver game loop)

### Bench Path (commit comparison)

### Strategy Decision Flow (inside the bot)

### State Management

- The game state lives in the NLE environment. The bot rebuilds its view on each step in `Agent.update` / `update_state` (`autoascend/agent.py`, ~lines 511 and 601): `blstats`, glyphs, `Level` objects per dungeon level, `Character`, `Inventory`, and `MonsterTracker`.
- Per-game mutable state is held on the `Agent` instance and the `GlobalLogic` instance. Nothing is stored between games in the bot itself.
- Cross-game state is written to files only: `games.jsonl` (screensaver), `results.db` (bench), and the per-commit worktree cache under `~/.cache/screens-bench/`.

## Key Abstractions

- Purpose: Owns the bot's perception and action primitives for one game (move, fight, pray, eat, dig, engrave, kick, search, `go_to`, `bfs`, `path`).
- Examples: `autoascend/agent.py` (class `Agent`, ~line 140).
- Pattern: A large stateful controller. It is a central object that most behaviour modules call. It is effectively a god object. About 2100 lines.
- Purpose: Maps the current `Milestone` to the strategy that should run, and tracks milestone completion.
- Examples: `autoascend/global_logic.py` (class `GlobalLogic`, ~line 227; `ItemPriority`, ~line 94; helpers `dive_stairs`, `sokoban_board`, `is_stoning_cure`).
- Pattern: State machine over `Milestone` values with a generator-based strategy per milestone.
- Purpose: Ordered goals for one secret strategy, such as "be on first level", "find Sokoban", "solve Sokoban", "find Minetown", "dive", "leave dungeon".
- Examples: `autoascend/plans.py` (`M = Milestone`, `STRATEGIES`, `plan_for`, `choose_strategy`), `autoascend/ladder.py` (`RUNGS`, 17 rungs).
- Pattern: Data-driven plan tables. Strategy changes are data edits, not new control flow.
- Purpose: Pair an entry condition with an action generator. The generator yields `False` to decline and `True` to commit.
- Examples: `autoascend/strategy.py` (class `Strategy`, `Strategy.wrap` decorator), used throughout `autoascend/global_logic.py`, `autoascend/combat/`, `autoascend/exploration_logic.py`.
- Pattern: Condition-then-action generators. The docstring in `autoascend/strategy.py` gives the contract.
- Purpose: Adapts NLE 1.3.0 (gymnasium API) to the agent. Owns the `Agent` instance and the `on_step`/`choose_plan` hooks. Sets `end_reason`.
- Examples: `autoascend/env_wrapper.py` (`EnvWrapper.main`, `reset`, `step`, `_parse_end_reason`, `debug_tiles`, `debug_log`).
- Pattern: Adapter with callback injection.
- Purpose: Single record for one finished game, used by the screensaver log, the bench worker, and the reports.
- Examples: `nethack_screensaver/game.py` (`GameResult` dataclass, ~line 48). `bench/worker.py` serialises it with `dataclasses.asdict`.
- Pattern: Dataclass as a shared contract between packages. Fields are added with defaults so old log lines still load.
- Purpose: Screensaver settings from `~/.config/nethack-screensaver/config.toml`.
- Examples: `nethack_screensaver/config.py` (`Config`, `load_config`).
- Pattern: Dataclass plus TOML loader (`tomllib`), with defaults.
- Purpose: Persistence (`Store`, SQLite tables for games, jobs, references) and the API surface (`App`, with `start_baseline`, `start_experiment`, `dashboard`, `results`, `games`, `start_import`).
- Examples: `bench/store.py` (`Store`, `END_STATES`), `bench/server.py` (`App`, `make_handler`, `serve`).
- Pattern: Thin service layer plus `http.server` handler. Writes are guarded by `app.lock`.
- Purpose: Run game jobs in parallel slots, one subprocess per slot, with judgement after each batch.
- Examples: `bench/scheduler.py` (`Scheduler`, `_Slot`), `bench/runner.py` (`ProcessWorker`, `play`, `results`, `alive`, `close`).
- Pattern: Worker pool with a line-delimited JSON protocol over stdin/stdout.
- Purpose: Turn game results into the metric used for a decision (default "reached Dlvl 6+"), with paired statistics.
- Examples: `bench/metrics.py` (`METRICS`, `evaluate`, `orient`, `killer`), `bench/stats.py` (`judge_paired`, `newcombe`, `Z95`).
- Pattern: Metric registry plus sequential-checkpoint judging.

## Entry Points

- Location: `bin/nethack-screensaver` (bash). Also `zsh/nethack-screensaver.zsh`, which sets `TMOUT` and `TRAPALRM`.
- Triggers: Idle timer at the zsh prompt (default 300 s, `NETHACK_SCREENSAVER_IDLE`), or manual run after `ln -s` into `~/.local/bin/`.
- Responsibilities: Own the tty, start the player, exit on key or when the player stops.
- Location: `nethack_screensaver/player.py` (`main`, also runnable with `python -m nethack_screensaver.player`).
- Triggers: Launcher. Also `NETHACK_SCREENSAVER_PLAYER` env var overrides the command (used by tests).
- Responsibilities: Infinite game loop, rendering, pacing, game log.
- Location: `bench/cli.py` (`main`, registered as `screens-bench` in `pyproject.toml` `[project.scripts]`).
- Triggers: `uv run screens-bench serve`, or import/prune subcommands.
- Responsibilities: Start the HTTP server and scheduler, import real ascension data, prune worktrees.
- Location: `bench/worker.py`.
- Triggers: Started by `bench/runner.py` (`ProcessWorker`) with the commit's worktree on `PYTHONPATH`.
- Responsibilities: Read `play [seed]` lines, call `nethack_screensaver.game.run_game`, print one JSON result per line. It must not import `bench`, because old commits do not have that package.
- Location: `bench/mcp_server.py` (`if __name__ == "__main__"`), configured in `.mcp.json` as `screens-bench`.
- Triggers: Claude Code startup, via `uv run --group bench python -m bench.mcp_server`.
- Responsibilities: Expose bench operations as MCP tools over the HTTP API.
- Location: `scripts/benchmark.py`, `scripts/scenario_run.py`, `scripts/staged_run.py`, `scripts/handplay.py`, and others (see Layers).
- Triggers: Manual, `uv run python scripts/<name>.py`.

## Architectural Constraints

- **Threading:** Single-threaded bot. `nethack_screensaver/game.py` uses a `SIGALRM`-based screen watchdog (`_ScreenWatchdog`, `WatchdogTimeout`, default 60 s). The screensaver player installs `SIGTERM`/`SIGHUP`/`SIGWINCH` handlers (`player._install_signals`). Bench parallelism is process-based (`ProcessWorker` per slot), with reader threads only for pipe reading (`bench/runner.py`, `bench/scheduler.py`) and a `threading.Lock` on `App`.
- **Global state:** Module-level constants and tables are used heavily, for example `autoascend/plans.py` (`STRATEGIES`, `ROLE_TIERS`), `autoascend/agent.py` (`UNSTICK_AFTER`, `CANNOT_KICK`), `autoascend/objects/data.py`. `nethack_screensaver/game.py` sets `CHARACTER`, `AGENT_ARGS`, and `FARMING` at module level. `autoascend/glyph/` holds glyph tables. Game state is per-`Agent`, not module-level.
- **Circular imports:** None found between `autoascend` and `nethack_screensaver`/`bench`. Within `autoascend`, `agent.py` imports most behaviour modules, and those modules call back into the agent through the instance they are given. Keep behaviour modules free of `agent` imports to avoid cycles.
- **Environment coupling:** The bot is tied to the NetHack 5.0 build at `reference/nle-src` (branch `screens-nh5`, from `pyproject.toml` `[tool.uv.sources]`). `autoascend/castle.py`, `autoascend/medusa.py`, and `autoascend/passtune.py` cite NetHack 5 source (`dat/castle.lua`, `dig.c`). `bench/cli.py` allows a different worker interpreter through `SCREENS_BENCH_PYTHON`, because the NLE version decides the NetHack version.
- **Determinism:** Seeded games need `fixed_clock.pin(seed)` and `fix_moon_phase`. `bench/runner.py` sets `PYTHONHASHSEED=0` and single-thread BLAS env vars so that results repeat.
- **Staged games:** `nethack_screensaver/staging.py` plays in wizard mode from a chosen situation. It is for research and benchmarks only and is never used in natural play, per its module docstring.

## Anti-Patterns

### Large controller objects

### Bench code importing the working tree

### Module-level dependency on the bench package

## Error Handling

- `panic_on_errors=True` turns upstream assertions into `AgentPanic` (`autoascend/exceptions.py`). `Agent.handle_exception` replans and continues. `Agent.main` raises `RuntimeError("Cyclic Panic ...")` after 5 iterations with no game progress (`autoascend/agent.py`, `main`).
- `run_game` (`nethack_screensaver/game.py`) catches `WatchdogTimeout` and generic `Exception` so that one bad game never stops the screensaver. The error text goes to `end_reason` and into `GameResult`.
- `player.main` writes game results even when a game ends badly, and sleeps before starting the next one.
- `bin/nethack-screensaver` reports player exit status and keeps the message on screen for 3 s.
- Bench worker failures are handled by `Scheduler._worker_died` (`bench/scheduler.py`), which re-queues or ends the job, and `Store.interrupt_unfinished` at startup (`bench/cli.py`, `build_app`).

## Cross-Cutting Concerns

<!-- GSD:architecture-end -->

<!-- GSD:skills-start source:skills/ -->

## Project Skills

No project skills found. Add skills to any of: `.claude/skills/`, `.agents/skills/`, `.cursor/skills/`, `.github/skills/`, or `.codex/skills/` with a `SKILL.md` index file.
<!-- GSD:skills-end -->

<!-- GSD:workflow-start source:GSD defaults -->

## GSD Workflow Enforcement

Before using Edit, Write, or other file-changing tools, start work through a GSD command so planning artifacts and execution context stay in sync.

Use these entry points:
- `/gsd-fast` for a trivial task inline, with no subagents and no PLAN.md
- `/gsd-quick` for small fixes, doc updates, and ad-hoc tasks
- `/gsd-debug` for investigation and bug fixing
- `/gsd-execute-phase` for planned phase work

Do not make direct repo edits outside a GSD workflow unless the user explicitly asks to bypass it.
<!-- GSD:workflow-end -->

<!-- GSD:profile-start -->

## Developer Profile

> Profile not yet configured. Run `/gsd-profile-user` to generate your developer profile.
> This section is managed by `generate-claude-profile` -- do not edit manually.
<!-- GSD:profile-end -->
