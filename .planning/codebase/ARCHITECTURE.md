---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
<!-- refreshed: 2026-11-12 -->
# Architecture

**Analysis Date:** 2026-11-12

## System Overview

```text
┌──────────────────────────────────────────────────────────────────────────┐
│ Shell hook / launcher                                                     │
│  `zsh/nethack-screensaver.zsh` (TRAPALRM after idle)                      │
│  `bin/nethack-screensaver` (bash: owns tty, raw mode, key-to-exit)        │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ spawns `.venv/bin/python -m nethack_screensaver.player`
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Screensaver runtime  `nethack_screensaver/`                               │
│  `player.py` loop ─► `game.py run_game()` ─► `render.py` / `pacing.py`     │
│  `config.py`, `paths.py`, `gamelog.py`, `staging.py`, `snapshots.py`      │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ builds NetHackChallenge env, wraps it
                ▼
┌──────────────────────────────────────────────────────────────────────────┐
│ Bot core  `autoascend/`                                                   │
│  `env_wrapper.py` (EnvWrapper, gymnasium adapter)                         │
│   └─► `agent.py` Agent (perception + actions, ~2100 lines)                │
│        └─► `global_logic.py` GlobalLogic (milestone -> strategy)          │
│             ├─ `plans.py` / `ladder.py` (ordered milestone plans)         │
│             ├─ `exploration_logic.py`, `combat/`, `item/`, `castle.py`... │
│             └─ `character.py`, `level.py`, `monster_tracker/`, `glyph/`   │
└───────────────┬──────────────────────────────────────────────────────────┘
                │ NLE 1.3.0 env (local build `reference/nle-src`)
                ▼
          NetHack 5.0 game process (in-process C extension)

┌──────────────────────────────────────────────────────────────────────────┐
│ Bench tooling  `bench/` (+ `screens-bench` console script)                │
│  `cli.py` -> `server.py` (HTTP JSON API, 127.0.0.1:8765)                  │
│        ├─ `scheduler.py` (job queue, judge experiments)                   │
│        │     └─ `runner.py` ProcessWorker ─► `bench/worker.py` subprocess │
│        │          (PYTHONPATH = commit worktree from `gitrefs.py`)        │
│        ├─ `store.py` (SQLite `results.db`)                                │
│        └─ `mcp_server.py` (MCP tools that call the HTTP API)              │
└──────────────────────────────────────────────────────────────────────────┘
```

Offline analysis, one-off studies and hand-play helpers live in `scripts/`. Tests live in `tests/`.

## Pattern Overview

**Overall:** Layered application around a single scripted agent. A Python package (`autoascend`) implements a rule/planner-driven bot. A separate runtime package (`nethack_screensaver`) wraps that bot for terminal use. A third package (`bench`) runs many headless games per git commit and compares results.

**Key Characteristics:**
- The bot is a hand-written priority/strategy system, not a learned policy. Decisions are made by `Strategy` objects that are generator-based (`autoascend/strategy.py`), and by `Agent.preempt(...)` interrupts (`autoascend/agent.py`, `Agent.preempt` at ~line 325).
- High-level goals are ordered lists of `Milestone` values. Each named strategy is a tuple of milestones in `autoascend/plans.py` (`STRATEGIES`, `DEFAULT_PLAN`, `choose_strategy`). The `GlobalLogic` class in `autoascend/global_logic.py` (`class GlobalLogic`, ~line 227) turns the current milestone into concrete actions.
- The game is accessed through a single gymnasium-style adapter, `autoascend/env_wrapper.py` (`EnvWrapper.step`), which feeds observations into `Agent.update`. The agent calls back into the wrapper through `on_step`, `choose_plan`, and `prepare` callables that `nethack_screensaver/game.py` injects.
- Pure logic modules are kept free of game access so they can be unit-tested and imported by the bench server. Examples: `autoascend/boulders.py` ("standard library + numpy only, no game access"), `autoascend/digging.py`, `autoascend/prayer.py`, `autoascend/ladder.py` ("standard library only, so the bench server can import the rung list"), `autoascend/castle.py`, `autoascend/passtune.py`, `autoascend/medusa.py`, `autoascend/quest_portal.py`, `autoascend/stuck.py`.
- Dependencies point one way. `nethack_screensaver` and `bench` import from `autoascend`. `autoascend` does not import from `nethack_screensaver` or `bench` (verified by grep: no matches in `autoascend/`). The one exception is `bench/` importing `nethack_screensaver.fixed_clock`.
- Process isolation for benchmarking. Each game batch runs in a child Python process (`bench/worker.py`) whose `PYTHONPATH` points at a git worktree of the commit under test. The bench server itself never imports game code from the working tree being edited.

## Layers

**Terminal entry layer (shell + bash):**
- Purpose: Start the screensaver on idle, own the terminal, exit on keypress.
- Location: `zsh/nethack-screensaver.zsh`, `bin/nethack-screensaver`
- Contains: zsh `TMOUT`/`TRAPALRM` hook; bash launcher that sets raw mode, backgrounds the Python player under `nice -n 10`, and drains input on exit.
- Depends on: `.venv/bin/python` created by `uv sync`.
- Used by: the user's `~/.zshrc` (`source ~/screens/zsh/nethack-screensaver.zsh`).

**Screensaver runtime layer:**
- Purpose: Loop forever: play one game, record it, show it, pause, repeat.
- Location: `nethack_screensaver/`
- Contains: `player.py` (`main()` loop), `game.py` (`run_game`, `GameResult`, watchdog, death context), `render.py` (`Renderer`, `format_status`, `format_reveal`), `pacing.py` (`Pacer` fast-forward), `config.py` (`Config`, `load_config`), `paths.py` (`config_path`, `state_dir`), `gamelog.py` (`append_result`, `read_stats`), `snapshots.py`, `dungeon_truth.py`, `fixed_clock.py`, `staging.py`.
- Depends on: `autoascend` (plans, env wrapper, global logic, item), `nle`.
- Used by: `bin/nethack-screensaver` (as `python -m nethack_screensaver.player`), and by `bench/worker.py` (which calls `game.run_game` directly).

**Bot core layer:**
- Purpose: Perceive the screen, maintain game state, and choose actions.
- Location: `autoascend/`
- Contains:
  - Environment adapter: `env_wrapper.py` (`EnvWrapper`).
  - Agent and perception: `agent.py` (`Agent`), `character.py`, `level.py`, `glyph/` (screen symbol decoding, `nh5.py`), `monster_tracker/`, `objects/`.
  - Strategy and planning: `global_logic.py` (`GlobalLogic`, `Milestone` usage), `plans.py`, `ladder.py`, `strategy.py`, `exceptions.py` (`AgentPanic`, `AgentFinished`, `AgentChangeStrategy`).
  - Behaviors: `exploration_logic.py`, `combat/` (`fight_heur.py`, `movement_priority.py`, `stair_escape.py`, `rl_scoring.py`), `item/` (inventory, item priorities, wishes, scrolls, accessories, shop selling), `prayer.py`, `telepathy.py`, `medusa.py`, `castle.py`, `passtune.py`, `digging.py`, `boulders.py`, `quest_portal.py`, `stuck.py`, `soko_solver/`.
  - Measurement: `stats_logger.py` (`StatsLogger`).
- Depends on: `nle.nethack`, `numpy`, `cv2` (in `exploration_logic.py`), `scipy`, `numba` (via dependencies in `pyproject.toml`).
- Used by: `nethack_screensaver/game.py`, `scripts/`, `tests/`, and `bench/` (only `autoascend.ladder.RUNGS` and `autoascend.objects`).

**Bench layer:**
- Purpose: Play bot games per commit at scale, persist results, judge experiments, and expose the results over HTTP and MCP.
- Location: `bench/`
- Contains:
  - Entry and server: `cli.py` (`main`, `build_app`, `screens-bench` script), `server.py` (`App`, `make_handler`, `serve`).
  - Scheduling: `scheduler.py` (`Scheduler`, `_Slot`, `_judge`, `_dispatch`), `runner.py` (`ProcessWorker`).
  - Persistence: `store.py` (`Store`, SQLite).
  - Analysis: `metrics.py` (`METRICS`, `evaluate`, `killer`), `stats.py` (`judge_paired`, `newcombe`, `CHECKPOINTS`), `report.py`, `filters.py` (`parse_where`).
  - Git and imports: `gitrefs.py` (`ensure_worktree`), `importers.py` (`parse_dumplog`, xlog/dumplog import), `reference.py`.
  - Clients: `mcp_server.py` (MCP `MCPServer("screens-bench")`, calls the HTTP API), `static/index.html` (dashboard served by `server.py`), `worker.py` (child process protocol).
- Depends on: stdlib, `mcp` (bench dependency group), `autoascend.ladder`, `nethack_screensaver.fixed_clock`.
- Used by: the user through `uv run screens-bench serve` and by Claude through `.mcp.json`.

**Scripts layer:**
- Purpose: Research tooling, one-off studies, and benchmarks. Not part of the installed package.
- Location: `scripts/`
- Contains: `benchmark.py` (headless benchmark, `-n`, `-j`), `scenario_run.py` + `scenario_lib.py`, `staged_run.py`, `seeded_report.py`, `replay_check.py`, `rewind.py`, `handplay.py`, `nld_study.py`, `bench_watch.py`, `fixes_triage.py`, `fixes_shortlist.py`, `item_selftest.py`, `gen_objects_data.py`, `wiki_sweep/`.
- Depends on: `autoascend`, `nethack_screensaver`, `bench` as needed.
- Used by: developers directly (`uv run python scripts/<name>.py`).

## Data Flow

### Primary Request Path (screensaver game loop)

1. Idle timer fires `TRAPALRM` and runs the launcher (`zsh/nethack-screensaver.zsh`, then `bin/nethack-screensaver`).
2. The launcher starts `nethack_screensaver.player` (`nethack_screensaver/player.py`, `main()`), with stderr appended to `~/.local/state/nethack-screensaver/player.log`.
3. `player.main` loads `Config` (`nethack_screensaver/config.py`), then imports `nethack_screensaver.game` and calls `run_game(role, on_frame, strategy)` (`nethack_screensaver/game.py`).
4. `run_game` pins the clock (`fixed_clock.pin`), creates a `NetHackChallenge` (or `staging.StagedChallenge` when staged), and wraps it in `EnvWrapper` with `on_step`, `choose_plan`, and `agent_args` (`AGENT_ARGS = dict(panic_on_errors=True, verbose=False)`).
5. `EnvWrapper.main` (`autoascend/env_wrapper.py`) resets the env, calls `choose_plan(obs)` to pick a strategy and milestone list via `autoascend/plans.py`, then constructs `agent_lib.Agent(self, plan=...)` and calls `Agent.main()`.
6. `Agent.main` (`autoascend/agent.py`, ~line 2091) runs an init block (ESC, `character.parse()`, autopickup), then loops: `self.global_logic.global_strategy().run()`. Exceptions go to `handle_exception`, which converts `AgentPanic` into a replan and raises `RuntimeError("Cyclic Panic...")` after 5 quiet iterations.
7. Each env step returns to `EnvWrapper.step` (`autoascend/env_wrapper.py`, ~line 69), which calls `on_step(obs)`. `game.py` updates depth, turns, XP, death context, the screen watchdog, and then calls `on_frame` (the player's callback).
8. `player.on_frame` computes pacing (`Pacer.update`), renders `tty_chars`/`tty_colors` with `Renderer.frame` to stdout, and sleeps `frame_delay(...)`.
9. When the game ends, `run_game` builds a `GameResult` (`nethack_screensaver/game.py`, dataclass), and `player.main` appends it to `~/.local/state/nethack-screensaver/games.jsonl` via `gamelog.append_result`, then loops.

### Bench Path (commit comparison)

1. `screens-bench serve` (`bench/cli.py`, `_serve`) builds `App(store, Scheduler(store, spawn, slots=workers), REPO, cache_dir)` via `build_app`.
2. The HTTP handler in `bench/server.py` (`make_handler`, `do_POST`) turns API calls into `App.start_baseline` or `App.start_experiment`, which call `Scheduler.submit`.
3. `Scheduler.tick`/`_dispatch` (`bench/scheduler.py`) picks queued work, calls `spawn(sha)`, which runs `gitrefs.ensure_worktree(REPO, sha, cache_dir/"worktrees")` and creates a `ProcessWorker` (`bench/runner.py`).
4. `ProcessWorker` starts `bench/worker.py` with `PYTHONPATH=<worktree>`, `PYTHONHASHSEED=0`, single BLAS threads, and `fixed_clock.preload_env`. It sends `play [seed]` lines on stdin and reads one JSON result line per game from stdout. Stderr goes to `~/.local/share/screens-bench/worker.log`.
5. Results are stored with `Store.add_game` in `~/.local/share/screens-bench/results.db`. `Scheduler._judge` compares candidate and baseline with `bench/stats.py` (`judge_paired`) and stops jobs once the result is clear (`CHECKPOINTS`: 192/384/576/1152 games per side).
6. `App.dashboard`, `App.results`, and `App.games` read from the store, and the HTTP server serves them as JSON and the static dashboard.
7. The MCP server (`bench/mcp_server.py`) calls the same HTTP API and starts the server if it is not already up (`_ensure_server`).

### Strategy Decision Flow (inside the bot)

1. `plans.choose_strategy(role, rng)` picks a secret strategy (`pilgrim`, `daredevil`, `sightseer`, `treasure`) using `ROLE_TIERS` and `TIER_WEIGHTS`, unless one is forced in config.
2. `plan_for(name, race)` gives the ordered `Milestone` tuple (`autoascend/plans.py`). `DEFAULT_PLAN` is pilgrim.
3. `GlobalLogic` (`autoascend/global_logic.py`) holds the current `milestone`, checks each milestone's condition (for example `FIND_SOKOBAN`, `SOLVE_SOKOBAN`, `DIVE`, `RETURN_TO_SURFACE`), and yields a strategy from `global_strategy()`. Specialised logic (Sokoban solver, castle, Medusa crossing, digging) is called from there.
4. Sub-strategies run as generators using the `Strategy` wrapper (`autoascend/strategy.py`), and can be preempted by `Agent.preempt` for threats (fight, emergency, stair escape, prayer, eating).

### State Management

- The game state lives in the NLE environment. The bot rebuilds its view on each step in `Agent.update` / `update_state` (`autoascend/agent.py`, ~lines 511 and 601): `blstats`, glyphs, `Level` objects per dungeon level, `Character`, `Inventory`, and `MonsterTracker`.
- Per-game mutable state is held on the `Agent` instance and the `GlobalLogic` instance. Nothing is stored between games in the bot itself.
- Cross-game state is written to files only: `games.jsonl` (screensaver), `results.db` (bench), and the per-commit worktree cache under `~/.cache/screens-bench/`.

## Key Abstractions

**`Agent`:**
- Purpose: Owns the bot's perception and action primitives for one game (move, fight, pray, eat, dig, engrave, kick, search, `go_to`, `bfs`, `path`).
- Examples: `autoascend/agent.py` (class `Agent`, ~line 140).
- Pattern: A large stateful controller. It is a central object that most behaviour modules call. It is effectively a god object. About 2100 lines.

**`GlobalLogic`:**
- Purpose: Maps the current `Milestone` to the strategy that should run, and tracks milestone completion.
- Examples: `autoascend/global_logic.py` (class `GlobalLogic`, ~line 227; `ItemPriority`, ~line 94; helpers `dive_stairs`, `sokoban_board`, `is_stoning_cure`).
- Pattern: State machine over `Milestone` values with a generator-based strategy per milestone.

**`Milestone` and plans:**
- Purpose: Ordered goals for one secret strategy, such as "be on first level", "find Sokoban", "solve Sokoban", "find Minetown", "dive", "leave dungeon".
- Examples: `autoascend/plans.py` (`M = Milestone`, `STRATEGIES`, `plan_for`, `choose_strategy`), `autoascend/ladder.py` (`RUNGS`, 17 rungs).
- Pattern: Data-driven plan tables. Strategy changes are data edits, not new control flow.

**`Strategy` (generator wrapper):**
- Purpose: Pair an entry condition with an action generator. The generator yields `False` to decline and `True` to commit.
- Examples: `autoascend/strategy.py` (class `Strategy`, `Strategy.wrap` decorator), used throughout `autoascend/global_logic.py`, `autoascend/combat/`, `autoascend/exploration_logic.py`.
- Pattern: Condition-then-action generators. The docstring in `autoascend/strategy.py` gives the contract.

**`EnvWrapper`:**
- Purpose: Adapts NLE 1.3.0 (gymnasium API) to the agent. Owns the `Agent` instance and the `on_step`/`choose_plan` hooks. Sets `end_reason`.
- Examples: `autoascend/env_wrapper.py` (`EnvWrapper.main`, `reset`, `step`, `_parse_end_reason`, `debug_tiles`, `debug_log`).
- Pattern: Adapter with callback injection.

**`GameResult`:**
- Purpose: Single record for one finished game, used by the screensaver log, the bench worker, and the reports.
- Examples: `nethack_screensaver/game.py` (`GameResult` dataclass, ~line 48). `bench/worker.py` serialises it with `dataclasses.asdict`.
- Pattern: Dataclass as a shared contract between packages. Fields are added with defaults so old log lines still load.

**`Config`:**
- Purpose: Screensaver settings from `~/.config/nethack-screensaver/config.toml`.
- Examples: `nethack_screensaver/config.py` (`Config`, `load_config`).
- Pattern: Dataclass plus TOML loader (`tomllib`), with defaults.

**`Store` and `App`:**
- Purpose: Persistence (`Store`, SQLite tables for games, jobs, references) and the API surface (`App`, with `start_baseline`, `start_experiment`, `dashboard`, `results`, `games`, `start_import`).
- Examples: `bench/store.py` (`Store`, `END_STATES`), `bench/server.py` (`App`, `make_handler`, `serve`).
- Pattern: Thin service layer plus `http.server` handler. Writes are guarded by `app.lock`.

**`Scheduler` and `ProcessWorker`:**
- Purpose: Run game jobs in parallel slots, one subprocess per slot, with judgement after each batch.
- Examples: `bench/scheduler.py` (`Scheduler`, `_Slot`), `bench/runner.py` (`ProcessWorker`, `play`, `results`, `alive`, `close`).
- Pattern: Worker pool with a line-delimited JSON protocol over stdin/stdout.

**Metrics and judging:**
- Purpose: Turn game results into the metric used for a decision (default "reached Dlvl 6+"), with paired statistics.
- Examples: `bench/metrics.py` (`METRICS`, `evaluate`, `orient`, `killer`), `bench/stats.py` (`judge_paired`, `newcombe`, `Z95`).
- Pattern: Metric registry plus sequential-checkpoint judging.

## Entry Points

**Screensaver launcher:**
- Location: `bin/nethack-screensaver` (bash). Also `zsh/nethack-screensaver.zsh`, which sets `TMOUT` and `TRAPALRM`.
- Triggers: Idle timer at the zsh prompt (default 300 s, `NETHACK_SCREENSAVER_IDLE`), or manual run after `ln -s` into `~/.local/bin/`.
- Responsibilities: Own the tty, start the player, exit on key or when the player stops.

**Screensaver player:**
- Location: `nethack_screensaver/player.py` (`main`, also runnable with `python -m nethack_screensaver.player`).
- Triggers: Launcher. Also `NETHACK_SCREENSAVER_PLAYER` env var overrides the command (used by tests).
- Responsibilities: Infinite game loop, rendering, pacing, game log.

**Bench CLI and server:**
- Location: `bench/cli.py` (`main`, registered as `screens-bench` in `pyproject.toml` `[project.scripts]`).
- Triggers: `uv run screens-bench serve`, or import/prune subcommands.
- Responsibilities: Start the HTTP server and scheduler, import real ascension data, prune worktrees.

**Bench worker:**
- Location: `bench/worker.py`.
- Triggers: Started by `bench/runner.py` (`ProcessWorker`) with the commit's worktree on `PYTHONPATH`.
- Responsibilities: Read `play [seed]` lines, call `nethack_screensaver.game.run_game`, print one JSON result per line. It must not import `bench`, because old commits do not have that package.

**MCP server:**
- Location: `bench/mcp_server.py` (`if __name__ == "__main__"`), configured in `.mcp.json` as `screens-bench`.
- Triggers: Claude Code startup, via `uv run --group bench python -m bench.mcp_server`.
- Responsibilities: Expose bench operations as MCP tools over the HTTP API.

**Batch and study scripts:**
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

**What happens:** `autoascend/agent.py` (`Agent`, ~2100 lines), `autoascend/global_logic.py` (`GlobalLogic`, ~1360 lines), and `autoascend/item/inventory.py` (~1800 lines) hold many unrelated responsibilities. Behaviour modules receive the agent and call many of its methods.
**Why it's wrong:** Changes in one behaviour can break others through shared mutable state on the agent. Tests have to build a full agent to exercise small logic.
**Do this instead:** Put pure decision logic in standalone modules with no game access, the same way `autoascend/boulders.py`, `autoascend/prayer.py`, and `autoascend/digging.py` already do. Pass only the values they need. Keep new behaviour out of `Agent` when a standalone module can own it.

### Bench code importing the working tree

**What happens:** The bench server runs games from a commit's worktree (`bench/gitrefs.py`, `ProcessWorker`), not from the current checkout.
**Why it's wrong:** Importing `bench` or other working-tree code from `bench/worker.py` breaks old commits that lack those modules.
**Do this instead:** Keep `bench/worker.py` limited to the standard library and `nethack_screensaver.game`, as its docstring requires. Put any shared contract that worker and server both need in code that exists in every commit, or in the worker's JSON output.

### Module-level dependency on the bench package

**What happens:** `bench/` imports `autoascend.ladder` and `nethack_screensaver.fixed_clock`. `nethack_screensaver/player.py` imports `autoascend.plans` at module top, with a comment saying the import is cheap.
**Why it's wrong:** Heavy imports at module top slow the bench server and the screensaver splash.
**Do this instead:** Keep `autoascend/__init__.py`, `plans.py`, and `ladder.py` free of heavy imports, as they are now. Import NLE and numpy inside functions when the module is used from light entry points, as `nethack_screensaver/player.py` does for `game.py`.

## Error Handling

**Strategy:** Errors inside the bot are converted to replans rather than crashes. Game-level failures are caught at the top and recorded as an `end_reason`.

**Patterns:**
- `panic_on_errors=True` turns upstream assertions into `AgentPanic` (`autoascend/exceptions.py`). `Agent.handle_exception` replans and continues. `Agent.main` raises `RuntimeError("Cyclic Panic ...")` after 5 iterations with no game progress (`autoascend/agent.py`, `main`).
- `run_game` (`nethack_screensaver/game.py`) catches `WatchdogTimeout` and generic `Exception` so that one bad game never stops the screensaver. The error text goes to `end_reason` and into `GameResult`.
- `player.main` writes game results even when a game ends badly, and sleeps before starting the next one.
- `bin/nethack-screensaver` reports player exit status and keeps the message on screen for 3 s.
- Bench worker failures are handled by `Scheduler._worker_died` (`bench/scheduler.py`), which re-queues or ends the job, and `Store.interrupt_unfinished` at startup (`bench/cli.py`, `build_app`).

## Cross-Cutting Concerns

**Logging:** Two channels. Game events are counted and written through `autoascend/stats_logger.py` (`StatsLogger`, `log_event`, e.g. `unstick`). Process diagnostics go to stderr, which the launcher appends to `~/.local/state/nethack-screensaver/player.log` and the bench worker to `~/.local/share/screens-bench/worker.log`. Results are JSON lines in `games.jsonl`.
**Validation:** Inputs to the bench API are parsed by `bench/filters.py` (`parse_where`) and checked in `bench/server.py` (`_refused`). Configuration is validated by `nethack_screensaver/config.py` (`load_config`).
**Authentication:** Not applicable. The bench HTTP server binds to `127.0.0.1` only (`bench/server.py`, `serve`, `host="127.0.0.1"`). Its write endpoints are refused unless the request is local (`_refused(write=True)`).

---

*Architecture analysis: 2026-11-12*
