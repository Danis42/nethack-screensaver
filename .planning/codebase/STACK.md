---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
# Technology Stack

**Analysis Date:** 2026-10-22

## Languages

**Primary:**
- Python 3.13 (pinned `>=3.13,<3.14` in `pyproject.toml`; `.python-version` = `3.13`) - all code: `autoascend/`, `nethack_screensaver/`, `bench/`, `scripts/`, `tests/`

**Secondary:**
- Bash - launcher `bin/nethack-screensaver` (pty handling, idle-key drain, stty save/restore)
- Zsh - shell hook `zsh/nethack-screensaver.zsh` (uses `TRAPALRM` and `TMOUT` to start the screensaver after idle time)
- TOML - `pyproject.toml`, user config `~/.config/nethack-screensaver/config.toml` (parsed with `tomllib` in `nethack_screensaver/config.py`)
- SQL (SQLite dialect) - schema embedded in `bench/store.py`
- Static HTML/JS - bench status page `bench/static/index.html` (no external asset references)

## Runtime

**Environment:**
- CPython 3.13 (virtualenv at `.venv/`, created by `uv sync`)
- Target platform: a Linux/POSIX terminal (uses `pty`, `termios`, `select`, `signal`; launcher checks `-t 0`/`-t 1`)

**Package Manager:**
- `uv` (no version pinned in repo) - used for `uv sync`, `uv run`, and the `.mcp.json` server launch
- Lockfile: present (`uv.lock`, 48 locked packages)
- Build backend: `hatchling` (wheel packages: `autoascend`, `nethack_screensaver`, `bench`)

## Frameworks

**Core:**
- NetHack Learning Environment (NLE) `1.3.0` (`nle` from PyPI; locked in `uv.lock`) - the NetHack game itself, driven via `nle.env.tasks.NetHackChallenge` (`nethack_screensaver/game.py`) and `nle.nethack` action/glyph constants across `autoascend/`
- Gymnasium `1.2.0` (transitive via NLE) - env API consumed by `autoascend/env_wrapper.py`
- AutoAscend (vendored port, MIT, see `autoascend/LICENSE`, `autoascend/PORTING.md`) - the bot logic in `autoascend/agent.py` and `autoascend/strategy.py`
- MCP Python SDK `mcp 2.3.0` (dependency group `bench`) - `bench/mcp_server.py` builds an `MCPServer` (`from mcp.server.mcpserver import MCPServer`), registers tools with `@mcp.tool()`, and runs via `mcp.run()`
- Standard-library HTTP server `http.server.ThreadingHTTPServer` - bench server in `bench/server.py` (no web framework)

**Testing:**
- `pytest 9.1.1` (dev group) - config in `pyproject.toml` `[tool.pytest.ini_options]`: `testpaths = ["tests"]`, marker `slow` (real games; deselected by default via `addopts = "-m 'not slow'"`), warnings turned into errors for `overflow encountered`
- Test helpers: `tests/conftest.py`, `tests/fake_player.py`, `tests/bench_fakes.py`

**Build/Dev:**
- `hatchling` - build backend (`[build-system]` in `pyproject.toml`)
- `uv` - dependency resolution, environment sync, running scripts and the MCP server
- `numba` JIT (`@nb.njit(cache=True)`) - `autoascend/utils.py`, `autoascend/monster_tracker/kernels.py` (explicit signatures; cache writes `__pycache__`)

## Key Dependencies

**Critical (declared in `pyproject.toml` `[project] dependencies`):**
- `nle==1.3.0` - exact pin; NetHack build and env. Upgrading it changes game behavior and the NLE action/glyph API the bot depends on.
- `numpy>=2.0` (locked `2.5.4`) - tty/glyph arrays, Sokoban and map grids (`autoascend/soko_solver/`, `autoascend/utils.py`)
- `numba>=0.61` (locked `0.68.0`) - JIT kernels for monster tracking and map operations
- `opencv-python-headless>=4.10` (locked `5.0.0.93`) - `cv2` in `autoascend/utils.py`, `autoascend/exploration_logic.py`, `autoascend/combat/fight_heur.py`
- `scipy>=1.14` (locked `1.18.1`) - `scipy.signal` in `autoascend/combat/fight_heur.py`
- `toolz>=1.0` (locked `1.2.0`) - functional helpers

**Dev/bench only:**
- `pytest>=8` (locked `9.1.1`)
- `mcp>=2.3` (locked `2.3.0`) - bench MCP server for Claude (`.mcp.json`)

**Standard library used notably:**
- `sqlite3` - `bench/store.py` (results database)
- `subprocess` - `bench/gitrefs.py` (git worktrees), `bench/runner.py` (worker processes)
- `urllib.request` - `bench/importers.py` (HTTP downloads with custom User-Agent, 60 s timeout)
- `tomllib` - config parsing
- `pty`, `termios`, `select`, `signal` - running the game in a terminal (`nethack_screensaver/`, `bin/nethack-screensaver`)

## Configuration

**Environment variables (read by the code; names only):**
- `XDG_CONFIG_HOME` - base for the user config path (`nethack_screensaver/paths.py`)
- `XDG_STATE_HOME` - base for game history and logs (`nethack_screensaver/paths.py`, `bin/nethack-screensaver`); defaults to `~/.local/state`
- `NETHACK_SCREENSAVER_IDLE` - idle seconds before the zsh hook starts the game (default 300; `zsh/nethack-screensaver.zsh`)
- `NETHACK_SCREENSAVER_PLAYER` - overrides the player command in `bin/nethack-screensaver`
- `SCREENS_BENCH_DATA` - bench data dir (default `~/.local/share/screens-bench`; `bench/cli.py`, `bench/mcp_server.py`)
- `SCREENS_BENCH_CACHE` - bench cache dir for worktrees and downloads (default `~/.cache/screens-bench`; `bench/cli.py`)
- `SCREENS_BENCH_URL` - bench server URL for the MCP client (default `http://127.0.0.1:8765`; `bench/mcp_server.py`)
- `FAKE_PLAYER_PIDFILE` - test-only, `tests/fake_player.py`

**User config file (all keys optional):** `~/.config/nethack-screensaver/config.toml`, validated by `nethack_screensaver/config.py` (`Config` dataclass). Keys: `delay`, `fast_delay`, `level_pause`, `end_pause`, `status_line`, `role`, `strategy`, `reveal_goal`. Unknown keys and invalid values produce a stderr warning and fall back to defaults.

**Secrets:** No `.env` file, credential file, or secrets directory was found in the repository. No API keys are used. `.claude/settings.local.json` contains only MCP-server enablement flags.

**Build/Dev config files:**
- `pyproject.toml` - project metadata, dependencies, dependency groups, build and pytest config
- `uv.lock` - pinned dependency graph
- `.python-version` - `3.13`
- `.gitignore` - ignores `.venv/`, `__pycache__/`, `*.nbi`, `*.nbc`, `.pytest_cache/`, `.superpowers/`
- `.mcp.json` - registers the `screens-bench` MCP server (`uv run --group bench python -m bench.mcp_server`)

## Platform Requirements

**Development:**
- Python 3.13 and `uv`
- `uv sync` installs everything, including NLE 1.3.0 (which builds/bundles the NetHack game)
- A POSIX terminal for interactive runs; git available on PATH (bench uses `git worktree`)
- Commands: `uv run pytest`, `uv run pytest -m slow`, `uv run python scripts/benchmark.py -n 50 -j 8`, `uv run screens-bench serve`

**Production (end-user "deployment"):**
- Local install only. The screensaver runs from a clone at `~/screens`, started by sourcing `zsh/nethack-screensaver.zsh` from `~/.zshrc`, or manually via `bin/nethack-screensaver` (symlinkable into `~/.local/bin/`).
- Runtime state: `~/.local/state/nethack-screensaver/` (`games.jsonl`, `player.log`); bench data in `~/.local/share/screens-bench/results.db`; bench cache in `~/.cache/screens-bench/`.
- No containers, no cloud hosting, no CI configuration (no `.github/` directory present).

---

*Stack analysis: 2026-10-22*
