---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
# Technology Stack

**Analysis Date:** 2026-11-12

## Languages

**Primary:**
- Python 3.13 (`requires-python = ">=3.13,<3.14"` in `pyproject.toml`; pinned via `.python-version`) - all bot logic in `autoascend/`, the screensaver front end in `nethack_screensaver/`, the benchmark system in `bench/`, and helper scripts in `scripts/`
- Python test code in `tests/` (pytest)

**Secondary:**
- C - a small LD_PRELOAD shim compiled at runtime from a string literal in `nethack_screensaver/fixed_clock.py` (`cc -O2 -shared -fPIC`), replacing libc `time()` for seeded games
- C (NetHack 3.6 / 5.0 sources, vendored) - game engine under `reference/nethack-3.6.6/`, `reference/nethack-5.0.0/`, and the NLE build tree `reference/nle-src/`
- Zsh - shell hook in `zsh/nethack-screensaver.zsh` (idle-prompt trigger)
- Bash - launcher `bin/nethack-screensaver`

## Runtime

**Environment:**
- CPython 3.13 (uv-managed; the local `.venv/pyvenv.cfg` points at `~/.local/share/uv/python/cpython-3.13-linux-x86_64-gnu`)
- Target platform: Linux with a zsh terminal (`uname` platform in project environment is Linux; the zsh hook and `/proc`-style tooling assume POSIX)
- The NetHack engine itself is provided by NLE (NetHack Learning Environment) compiled from source; `nle.nethack` is imported throughout `autoascend/glyph/`

**Package Manager:**
- uv (`uv 0.12.10` recorded in `.venv/pyvenv.cfg`)
- Lockfile: present - `uv.lock` (root of repo)
- NLE is not on PyPI for this fork; `pyproject.toml` resolves it from a local path: `[tool.uv.sources] nle = { path = "reference/nle-src" }` (branch `screens-nh5`, NetHack 5.0)

## Frameworks

**Core:**
- NLE (NetHack Learning Environment) - Gym-style environment wrapping NetHack; `nle` package, built from `reference/nle-src` (`autoascend/env_wrapper.py` is the bot-side wrapper)
- NetHack 5.0 (via the local NLE build) - the bot's game target; `autoascend/glyph/nh5.py` holds version-specific glyph handling. NetHack 3.6.6 sources are also vendored in `reference/nethack-3.6.6/` for comparison (README benchmarks cite NetHack 3.6)
- `http.server` (stdlib) - benchmark dashboard/API server in `bench/server.py` (`ThreadingHTTPServer`)
- `mcp` 2.3.0 (`mcp>=2.3`, bench dependency group) - MCP server exposing bench tools in `bench/mcp_server.py` (`@mcp.tool()` decorators)

**Testing:**
- pytest 9.1.1 (`pytest>=8` in dev group) - configured in `pyproject.toml` `[tool.pytest.ini_options]`; default `addopts = "-m 'not slow'"`, `slow` marker = games that take minutes
- Test fixtures: `tests/conftest.py`, `tests/fake_player.py`, `tests/bench_fakes.py`

**Build/Dev:**
- hatchling - build backend (`[build-system]` in `pyproject.toml`); wheel packages: `autoascend`, `nethack_screensaver`, `bench`
- uv - dependency resolution, sync, and `uv run` entry point
- cmake/pip build for NLE (`reference/nle-src/CMakeLists.txt`, `reference/nle-src/pyproject.toml`)
- Console script: `screens-bench = "bench.cli:main"` (`[project.scripts]`)

## Key Dependencies

**Critical:**
- `nle` (local path, NetHack 5.0 branch) - the game engine; without it nothing runs
- `numpy` 2.5.4 (lock; constraint `>=2.0`) - tty-char/glyph arrays throughout `autoascend/`, `nethack_screensaver/`
- `numba` 0.68.0 (lock; constraint `>=0.61`) - JIT kernels in `autoascend/monster_tracker/kernels.py`, and imported in other hot paths
- `opencv-python-headless` 5.0.0.93 (lock; constraint `>=4.10`) - imaging on rendered screen arrays (`cv2` imports)
- `scipy` 1.18.1 (lock; constraint `>=1.14`) - numerical helpers
- `toolz` 1.2.0 (lock; constraint `>=1.0`) - functional utilities

**Infrastructure:**
- `mcp` 2.3.0 (lock) - bench MCP server (`bench/mcp_server.py`), bench dependency group only
- Standard library heavy use: `sqlite3` (`bench/store.py`, `scripts/nld_study.py`), `urllib` (`bench/importers.py`, `bench/cli.py`, `scripts/*`), `subprocess` (git and child game processes), `tomllib` (`nethack_screensaver/config.py`), `multiprocessing` / `concurrent` (`bench/worker.py`, `bench/scheduler.py`)
- `pytest` 9.1.1 - test runner (dev group)

## Configuration

**Environment:**
- No `.env` file is present in the repository root (checked by existence only; contents not read)
- Runtime environment variables read by code:
  - `XDG_CONFIG_HOME` / `XDG_STATE_HOME` / `XDG_CACHE_HOME` - base dirs (`nethack_screensaver/paths.py`, `nethack_screensaver/fixed_clock.py`)
  - `NETHACK_SCREENSAVER_IDLE` - idle seconds before the zsh hook starts the game (README; read by `zsh/nethack-screensaver.zsh`)
  - `NLE_FIXED_TIME` - seed time consumed by the LD_PRELOAD shim (`nethack_screensaver/fixed_clock.py`)
  - `LD_PRELOAD` - checked to detect the shim (`nethack_screensaver/fixed_clock.py`)
  - `SCREENS_BENCH_URL` (default `http://127.0.0.1:8765`), `SCREENS_BENCH_DATA` (default `~/.local/share/screens-bench`), `SCREENS_BENCH_CACHE` (default `~/.cache/screens-bench`), `SCREENS_BENCH_PYTHON` (worker interpreter; `bench/cli.py`, `bench/mcp_server.py`, `bench/runner.py`)
  - `PYTHONHASHSEED=0`, `PYTHONPATH` - set by runner/script subprocess launches for determinism
  - Debug/scenario knobs in `scripts/scenario_run.py`: `SCENARIO_HOOK`, `SHOW_N`, `SCENARIO_TAIL`, `SCENARIO_EVENTS`, `SCENARIO_GREP`

**User config file (optional):**
- `~/.config/nethack-screensaver/config.toml` - parsed with `tomllib`; schema and defaults in `nethack_screensaver/config.py` (`delay`, `fast_delay`, `level_pause`, `end_pause`, `status_line`, `role`, `strategy`, `reveal_goal`)

**Build:**
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

**Development:**
- Linux, Python 3.13, uv
- A C toolchain (`cc`) for the fixed-clock LD_PRELOAD shim and for building NLE
- `nm` (binutils) for `nethack_screensaver/dungeon_truth.py` symbol lookup
- `git` on PATH (bench uses `git -C <repo>` through `bench/gitrefs.py`)
- Optional: a local Ollama server on `localhost:11434` for the wiki sweep / triage scripts (see INTEGRATIONS.md)
- The zsh shell for the idle hook (`zsh/nethack-screensaver.zsh`)

**Production (screensaver use):**
- Runs locally in the user's terminal; no server deployment, no container, no CI config present in the repository

---

*Stack analysis: 2026-11-12*
