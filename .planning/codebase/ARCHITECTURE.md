---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
<!-- refreshed: 2026-10-22 -->

# Architecture

**Analysis Date:** 2026-10-22

## System Overview

```text
┌────────────────────────────────────────────────────────────────────────────┐
│ Entry points                                                               │
│  zsh hook  `zsh/nethack-screensaver.zsh` (TRAPALRM after idle)            │
│  launcher  `bin/nethack-screensaver` (bash, owns the tty)                  │
│  CLI       `bench/cli.py` (`screens-bench`)   MCP `bench/mcp_server.py`    │
│  script    `scripts/benchmark.py`                                          │
└───────┬───────────────────────┬────────────────────────────┬───────────────┘
        │ player process        │ bench server (HTTP, threads)│ MCP → HTTP
        ▼                       ▼                            ▼
┌───────────────────────────┐  ┌─────────────────────────────────────────────┐
│ nethack_screensaver       │  │ bench                                       │
│  player.py  (loop, render)│  │  server.py (App, routes) → scheduler.py     │
│  game.py    (run_game)    │  │  scheduler.py (slots, jobs, verdicts)       │
│  pacing / render / config │  │  runner.py (ProcessWorker per slot)         │
│  gamelog.py (games.jsonl) │  │  gitrefs.py (commit → git worktree)         │
└─────────────┬─────────────┘  │  worker.py (child: plays games, JSON out)  │
              │ EnvWrapper     │  store.py (SQLite) stats.py metrics.py      │
              ▼                │  report.py importers.py reference.py       │
┌───────────────────────────┐  └──────────┬──────────────────────────────────┘
│ autoascend (the bot)      │             │ child process, PYTHONPATH=worktree
│  env_wrapper.py           │◄────────────┘ (runs game code of the commit)
│  agent.py  (Agent.main)   │
│   ├ global_logic.py       │──► plans.py (milestone plans), ladder.py (rungs)
│   ├ exploration_logic.py  │
│   ├ combat/, item/        │
│   ├ monster_tracker/      │
│   └ strategy.py (Strategy)│
│  level.py, character.py   │
└─────────────┬─────────────┘
              ▼
   NLE `NetHackChallenge` (`nle==1.3.0`, the NetHack game itself)
```

## Component Responsibilities

| Component | Responsibility | File |
|-----------|----------------|------|
| Zsh idle hook | Starts the launcher after `NETHACK_SCREENSAVER_IDLE` seconds at the prompt | `zsh/nethack-screensaver.zsh` |
| Launcher | Checks for a TTY, runs the player, drains keys, kills the child on exit | `bin/nethack-screensaver` |
| Player loop | Forever plays games, paces frames, renders, appends results | `nethack_screensaver/player.py` |
| Game runner | Creates the NLE env, picks strategy/plan, runs the bot, builds `GameResult` | `nethack_screensaver/game.py` |
| Pacing / config / paths | Frame delays by quiet time and level change; TOML config; XDG paths | `nethack_screensaver/pacing.py`, `config.py`, `paths.py` |
| Rendering | Status line, reveal screen, frame output | `nethack_screensaver/render.py` |
| Game log | Appends `GameResult` JSON lines, reads aggregate stats | `nethack_screensaver/gamelog.py` |
| Env wrapper | Resets NLE until the role matches, owns the `Agent`, forwards steps | `autoascend/env_wrapper.py` |
| Agent | Main decision loop: observe, choose action, step the env, handle panics | `autoascend/agent.py` |
| Global logic | Chooses the current milestone of the plan and the target (stairs, Sokoban, Minetown) | `autoascend/global_logic.py` |
| Plans | Strategy definitions as ordered milestone tuples; race/role choice | `autoascend/plans.py` |
| Ladder | Ascension ladder: 17 rungs, first turn of each, recorded per game | `autoascend/ladder.py` |
| Strategy wrapper | Generator-based conditional actions (`Strategy.wrap`) | `autoascend/strategy.py` |
| Exploration | Map exploration and frontier/stairs search | `autoascend/exploration_logic.py` |
| Combat | Fight heuristics, monster priorities, RL scoring hook | `autoascend/combat/` |
| Items | Inventory model, item priorities, containers, unloading | `autoascend/item/` |
| Monster tracking | Tracks monsters across frames; numba-style kernels | `autoascend/monster_tracker/` |
| Bench CLI | `serve`, `wait`, `prune`, `import` subcommands; wires the server | `bench/cli.py` |
| Bench HTTP server | Routes for jobs, experiments, dashboard, history, imports | `bench/server.py` |
| Bench scheduler | Hands seeded games to worker slots, judges experiments, stops deaths-in-a-row | `bench/scheduler.py` |
| Bench workers | One child process per slot, bound to a commit's worktree | `bench/runner.py`, `bench/worker.py` |
| Git refs / worktrees | Resolves refs to SHAs, creates and prunes detached worktrees | `bench/gitrefs.py` |
| Bench store | SQLite: games per SHA, jobs, reference (real) games | `bench/store.py` |
| Stats and metrics | Wilson/Newcombe intervals, paired verdicts, per-game metrics | `bench/stats.py`, `bench/metrics.py` |
| Reports | Dashboard summaries, ladder table, A/B comparison | `bench/report.py` |
| Importers | Loads real ascensions from xlogfiles and dumplogs | `bench/importers.py`, `bench/reference.py` |
| MCP server | Exposes bench operations as tools to Claude, via the HTTP API | `bench/mcp_server.py` |

## Pattern Overview

**Overall:** Three-package Python monolith in one repository. `autoascend` is a bot library, `nethack_screensaver` is the terminal product that runs it, and `bench` is a measurement service that runs the bot in child processes against git commits.

**Key Characteristics:**
- Dependency direction is one way: `nethack_screensaver` and `bench` import from `autoascend`; `autoascend` imports nothing from the other two.
- The bench worker must stay independent of the `bench` package, because it runs the game code of old commits (`bench/worker.py` docstring). Only `autoascend` modules are imported by the child.
- Each game is a self-contained run: a new `Agent`, `GlobalLogic`, and `Character` per game (created in `EnvWrapper.main`, `autoascend/env_wrapper.py`).
- Behaviour is data-driven: a strategy is a tuple of `Milestone` values in `autoascend/plans.py`; adding a strategy means adding an entry to `STRATEGIES`.
- Runs are seeded in the bench (`run_game(seed=...)` sets NLE initial seeds), so two commits can be compared seed by seed.

## Layers

**Process / UI layer (nethack_screensaver):**
- Purpose: keep a terminal showing a game, pace it, and log results.
- Location: `nethack_screensaver/`, `bin/nethack-screensaver`, `zsh/nethack-screensaver.zsh`
- Contains: loop, renderer, config, pacing, paths, game log.
- Depends on: `autoascend.env_wrapper`, `autoascend.global_logic.Milestone`, `autoascend.plans`.
- Used by: the zsh hook and launcher; `scripts/benchmark.py`; bench worker (`bench/worker.py` imports `nethack_screensaver.game.run_game`).

**Bot layer (autoascend):**
- Purpose: decide every NetHack action.
- Location: `autoascend/`
- Contains: `Agent` (decision loop), `GlobalLogic` (milestones), `ExplorationLogic`, `Character`, `Level`, `Inventory`/`ItemManager`, `MonsterTracker`, combat heuristics, soko solver (`autoascend/soko_solver/`), ladder.
- Depends on: `nle.nethack` (actions, glyph constants), numpy, numba, scipy, opencv (see `pyproject.toml`).
- Used by: `nethack_screensaver`, `bench` (via `autoascend.ladder` and `autoascend.metrics` inputs), tests.

**Measurement layer (bench):**
- Purpose: play many games per commit, store them, compare commits, and serve results.
- Location: `bench/`, plus `bench/static/index.html` (dashboard page).
- Contains: HTTP server, scheduler, worker processes, SQLite store, stats, reports, MCP server.
- Depends on: `autoascend.ladder.RUNGS` (`bench/metrics.py`, `bench/report.py`), git CLI, stdlib `http.server`, `sqlite3`, optional `mcp` package (bench dependency group).
- Used by: `screens-bench` script, `.mcp.json` server entry, tests.

## Data Flow

### Primary Request Path: one screensaver game

1. Idle timer fires `TRAPALRM` in `zsh/nethack-screensaver.zsh`, which runs `bin/nethack-screensaver`.
2. The launcher starts `python -m nethack_screensaver.player` from `.venv` (`bin/nethack-screensaver`).
3. `player.py` loads `Config` (`nethack_screensaver/config.py`) and calls `game.run_game(...)` in a loop.
4. `run_game` (`nethack_screensaver/game.py`) builds `NetHackChallenge(no_progress_timeout=1000)` and wraps it in `EnvWrapper` (`autoascend/env_wrapper.py`).
5. `EnvWrapper.main` resets the env, calls `choose_plan(obs)` (strategy and plan from `autoascend/plans.py`, using the role and race from the welcome message), then creates `Agent(self, **agent_args)` and calls `agent.main()` (`autoascend/agent.py:1595`).
6. `Agent.main` loops: each step observes, updates `Level`, `Character`, `Inventory`, `MonsterTracker`, asks `GlobalLogic` for the current milestone, and issues an action via `Agent.step` (`autoascend/agent.py:413`).
7. Each frame is passed to `on_frame` and `on_step`, which update `max_depth`, `turns`, and `xp_level` in `game.py`; `player.py` renders it (`render.py`) and paces it (`pacing.py`).
8. On game over, `run_game` returns a `GameResult` (`nethack_screensaver/game.py:32`), and `gamelog.append_result` writes a JSON line to `~/.local/state/nethack-screensaver/games.jsonl`.

### Secondary Flow: one bench experiment

1. `screens-bench serve` (`bench/cli.py:35`) builds `Store`, `Scheduler`, and `App`, then `serve` starts the HTTP server (`bench/server.py:245`).
2. A request such as `POST /api/jobs` reaches `App`, which resolves the ref with `gitrefs.resolve` and submits a job with `Scheduler.submit` (`bench/scheduler.py:34`).
3. `Scheduler.tick` (`bench/scheduler.py:49`) assigns the next unplayed seed of each needed SHA to a free slot. `_dispatch` calls `spawn(sha)`.
4. `spawn` uses `gitrefs.ensure_worktree` to get a detached worktree of that commit and starts a `ProcessWorker` (`bench/runner.py:12`) with `PYTHONPATH` set to the worktree. The child is `bench/worker.py`.
5. The worker reads `play [seed]` lines on stdin, calls `nethack_screensaver.game.run_game(seed=...)`, and prints one JSON `GameResult` line on stdout. Game output goes to stderr and the worker log.
6. A reader thread in `ProcessWorker` queues results. `Scheduler._collect` stores each game via `Store` (SQLite table `games`, JSON column).
7. For experiments, `Scheduler._judge` calls `stats.judge_paired` at checkpoints (192/384/576/1152 games per side). The verdict and dashboard data come from `bench/report.py` and `bench/metrics.py`.
8. The MCP tools in `bench/mcp_server.py` call the same HTTP routes via `_call`; `_ensure_server` starts the server if needed.

### Tertiary Flow: imports of real games

1. `screens-bench import xlog|dumplogs` (`bench/cli.py:71`) calls `bench/importers.py`, which fetches URLs with a cache (`fetch`, `min_interval=1.0`).
2. Parsed games go into the `reference_games` table; `bench/reference.py` summarises them as the yardstick.

**State Management:**
- Game state lives in the NLE env and the `Agent` object for one game; nothing is shared between games in one process except module-level constants.
- Bench state lives in SQLite (`~/.local/share/screens-bench/results.db`, per `bench/cli.py:18`), in-memory `Scheduler` slots, and `App.imports`. `App.lock` (RLock) guards calls from HTTP threads.
- Player config comes from `~/.config/nethack-screensaver/config.toml` (`nethack_screensaver/paths.py`).

## Key Abstractions

**Agent:**
- Purpose: the bot's per-game decision loop and action API.
- Examples: `autoascend/agent.py` (class `Agent` at line 76).
- Pattern: holds sub-systems (`Inventory`, `Character`, `ExplorationLogic`, `GlobalLogic`, `MonsterTracker`) as attributes; receives `plan` in its constructor.

**Plan and Milestone:**
- Purpose: an ordered list of goals that defines a strategy.
- Examples: `autoascend/plans.py` (`Milestone` IntEnum at line 8, `Plan` at line 23, `STRATEGIES` at line 88, `DEFAULT_PLAN` is pilgrim).
- Pattern: `Plan` advances an index as milestones complete; `ProgressWatch` tracks stalls. `plan_for(name, race)` returns the milestone tuple.

**Strategy (generator wrapper):**
- Purpose: a conditional action that yields once to say whether it applies, then acts.
- Examples: `autoascend/strategy.py` (`Strategy.wrap`), used in `autoascend/item/inventory.py` and `autoascend/agent.py`.
- Pattern: decorate a generator function with `@Strategy.wrap`; the first yield returns the entry condition.

**Ladder rung:**
- Purpose: the 17-step ascension ladder; each game records the first turn it reached each rung.
- Examples: `autoascend/ladder.py` (`Rung`, `Facts`, `Ladder`, `RUNGS`, `BY_KEY`).
- Pattern: pure functions over `Facts` observed from the game; `GameResult.ladder` and `GameResult.rung` store the result.

**GameResult:**
- Purpose: the one record a game produces; shared by the screensaver log, the bench worker, and the store.
- Examples: `nethack_screensaver/game.py:32`; read back in `nethack_screensaver/gamelog.py` and `bench/metrics.py`.
- Pattern: plain dataclass, serialised with `asdict`. Older stored games lack newer fields, and metrics skip them (`bench/metrics.py` docstring).

**Metric:**
- Purpose: a per-game measure the bench compares (rate or median).
- Examples: `bench/metrics.py` (`Metric` at line 29, `METRICS` registry, `evaluate`).
- Pattern: add one entry to `METRICS` to add a metric.

## Entry Points

**Screensaver player:**
- Location: `nethack_screensaver/player.py` (`python -m nethack_screensaver.player`).
- Triggers: `bin/nethack-screensaver`, which runs when the zsh idle hook fires.
- Responsibilities: forever play, pace, render, log; exit on keypress via the launcher.

**Launcher:**
- Location: `bin/nethack-screensaver`; can be symlinked into `~/.local/bin/`.
- Triggers: zsh `TRAPALRM` hook (`zsh/nethack-screensaver.zsh`) or the user.
- Responsibilities: requires a TTY, picks python (or `NETHACK_SCREENSAVER_PLAYER`), drains input, terminates the child.

**Bench CLI:**
- Location: `bench/cli.py:92` (`main`), installed as `screens-bench` (`pyproject.toml`).
- Triggers: user shell, `uv run screens-bench serve|wait|prune|import`.
- Responsibilities: start the server (default port 8765), wait on jobs, prune worktrees, import reference games.

**Bench worker:**
- Location: `bench/worker.py` (`main` at line 21).
- Triggers: `ProcessWorker` spawns it as a subprocess with the commit's worktree on `PYTHONPATH`.
- Responsibilities: play one game per `play [seed]` line; stdout carries only JSON results.

**Bench MCP server:**
- Location: `bench/mcp_server.py` (`main` at line 120), registered in `.mcp.json` as `screens-bench`.
- Triggers: Claude Code MCP client.
- Responsibilities: tool wrappers (`bench_baseline`, `bench_experiment`, `bench_results`, ...) over the HTTP API.

**Benchmark script:**
- Location: `scripts/benchmark.py`; calls `nethack_screensaver.game.run_game` directly.
- Triggers: `uv run python scripts/benchmark.py -n 50 -j 8` (README fallback).

## Architectural Constraints

- **Threading:** The game is single-threaded. `nethack_screensaver/game.py` uses a SIGALRM-based `_ScreenWatchdog` (raises `WatchdogTimeout`, a `KeyboardInterrupt` subclass, so the agent never swallows it). The bench server runs HTTP handlers in threads, with `App.lock` (RLock) around scheduler and store calls; each `ProcessWorker` has a daemon reader thread (`bench/runner.py`).
- **Process isolation:** Bench games run in child processes, one per scheduler slot (default 11, `bench/cli.py:23`), started with `nice`. A worker crash is contained and recorded as a crash (`Scheduler._worker_died`).
- **Global state:** `autoascend/plans.py` holds the `STRATEGIES` registry and `DEFAULT_PLAN`; `autoascend/global_logic.py` has `_prize_objects`; `bench/metrics.py` holds the `METRICS` registry; `bench/cli.py` sets `DATA` and `CACHE` from environment variables at import time.
- **Circular imports:** Not detected. `autoascend/agent.py` imports `item/inventory.py`, and `inventory.py` imports `Character`, but neither imports `agent`. `env_wrapper.py` is the only module that imports `agent` (`autoascend/env_wrapper.py:9`).
- **Import cost:** `nethack_screensaver/config.py` imports `autoascend.plans` only, to avoid loading NLE for the config (comment at line 7). Keep `plans.py` free of heavy imports.
- **Commit-scoped code:** The bench measures only committed code (README and `bench/gitrefs.py`). Uncommitted changes are invisible to it.
- **Python and NLE:** Python 3.13 only (`requires-python = ">=3.13,<3.14"`), pinned `nle==1.3.0`.

## Anti-Patterns

### Importing `bench` from the game code

**What happens:** Code under `autoascend/` or `nethack_screensaver/` imports from `bench`.
**Why it's wrong:** The bench worker runs the game code of old commits, which may not have the `bench` package (`bench/worker.py` docstring). The bench already imports `autoascend.ladder` (`bench/metrics.py`, `bench/report.py`), so the dependency is one way only.
**Do this instead:** Put shared data types in `autoascend/` or `nethack_screensaver/` (as `GameResult` is in `nethack_screensaver/game.py`) and import them from `bench`.

### Adding a second runtime path for games

**What happens:** Game logic is run from a new script rather than through `run_game` / `EnvWrapper`.
**Why it's wrong:** `run_game` is where seeding, watchdog, strategy choice, ladder recording, and `GameResult` creation are wired. Skipping it means results cannot be compared in the bench.
**Do this instead:** Call `nethack_screensaver.game.run_game(seed=..., strategy=...)`, as `scripts/benchmark.py` and `bench/worker.py` do.

### Editing `GameResult` without defaults

**What happens:** A new field is added to `GameResult` with no default.
**Why it's wrong:** Older stored games, in `games.jsonl` and in the SQLite `games` table, lack the field, and loading them fails.
**Do this instead:** Give the field a default (as `ladder`, `rung`, `seed` have, `nethack_screensaver/game.py:32`) and let metrics skip missing fields (`bench/metrics.py`).

## Error Handling

**Strategy:** Errors inside the bot become `AgentPanic` and trigger a replan instead of a crash. Hard stalls end the game.

**Patterns:**
- `EnvWrapper` passes `panic_on_errors=True` (`nethack_screensaver/game.py`, `AGENT_ARGS`); `Agent` records each panic in `all_panics` and replans (`autoascend/agent.py:76`).
- Exceptions are defined in `autoascend/exceptions.py` (`AgentPanic`, `AgentFinished`, `AgentChangeStrategy`).
- NLE's `no_progress_timeout=1000` and the bot's cyclic-panic guard end stuck games.
- `unsticks` counts turns where NetHack refused an action and the bot let time pass.
- Bench: `MAX_DEATHS_IN_ROW = 3` in `bench/scheduler.py` stops a job after repeated worker deaths. `ProcessWorker` turns bad stdout lines into errors and `Scheduler` records crashes.
- Screensaver: `player.py` logs errors to `~/.local/state/nethack-screensaver/player.log`.

## Cross-Cutting Concerns

**Logging:** `Agent` uses `verbose` flag and `StatsLogger` (`autoascend/stats_logger.py`). The player writes `player.log`. The bench writes per-worker stderr logs through `ProcessWorker(log_path)`.
**Validation:** Config values are validated in `nethack_screensaver/config.py` (e.g. the `strategy` check against `STRATEGIES`, line 35). Bench inputs are checked in `App.start_baseline` (e.g. `games >= 1`).
**Authentication:** Not applicable. The bench HTTP server binds to `127.0.0.1` by default (`bench/server.py:245`).

---

*Architecture analysis: 2026-10-22*
