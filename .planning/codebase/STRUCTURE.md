---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
# Codebase Structure

**Analysis Date:** 2026-10-22

## Directory Layout

```
screens/
├── autoascend/              # The NetHack bot (ported AutoAscend), core logic
│   ├── combat/              # Fight heuristics, monster utils, RL scoring hook
│   ├── glyph/               # NLE glyph/symbol constants and monster flags
│   ├── item/                # Inventory, item model, item priorities
│   ├── monster_tracker/     # Monster tracking across frames, kernels
│   ├── objects/             # NetHack object data tables
│   └── soko_solver/         # Sokoban search and maps
├── nethack_screensaver/     # Terminal screensaver: player, game runner, pacing, render
├── bench/                   # Bench server: HTTP, scheduler, workers, store, stats, MCP
│   └── static/              # Dashboard page (index.html)
├── bin/                     # nethack-screensaver launcher (bash)
├── zsh/                     # Idle hook for ~/.zshrc
├── scripts/                 # benchmark.py fallback runner
├── tests/                   # pytest suite (+ data/ fixtures)
│   └── data/                # Saved NLE arrays, Sokoban JSON, bench log samples
├── docs/                    # STATUS, ROADMAP, ASCENSION-GUIDE, superpowers plans & specs
│   ├── superpowers/plans/   # Dated implementation plans
│   └── superpowers/specs/   # Dated design specs
├── .claude/                 # Claude Code project settings (settings.local.json)
├── .planning/codebase/      # Generated codebase maps (this document lives here)
├── pyproject.toml           # Package metadata, dependencies, pytest config
├── uv.lock                  # Locked dependencies (uv)
├── .python-version          # Python version pin for uv
├── .mcp.json                # MCP server registration (screens-bench)
├── README.md                # User guide: install, config, develop, bench
├── CHANGELOG.md             # Release notes
├── handoff.txt              # Working copy of docs/STATUS.md (handoff between sessions)
└── .gitignore
```

## Directory Purposes

**`autoascend/`:**
- Purpose: the bot. Every per-game decision lives here.
- Contains: `agent.py` (decision loop, largest module at 1646 lines), `global_logic.py` (milestones, ~900 lines), `exploration_logic.py`, `character.py`, `level.py`, `env_wrapper.py`, `plans.py`, `strategy.py`, `ladder.py`, `stats_logger.py`, `utils.py`, `exceptions.py`, `PORTING.md` (port notes, benchmark history), `LICENSE` (MIT).
- Key files: `autoascend/agent.py`, `autoascend/global_logic.py`, `autoascend/plans.py`, `autoascend/env_wrapper.py`, `autoascend/ladder.py`.
- Package marker: `autoascend/__init__.py` (imports nothing heavy, per `nethack_screensaver/config.py` comment).

**`autoascend/combat/`:**
- Purpose: monster fighting and movement priorities.
- Contains: `fight_heur.py`, `movement_priority.py`, `monster_utils.py`, `rl_scoring.py`, `utils.py`.
- Key files: `autoascend/combat/fight_heur.py` (tested in `tests/test_fight_heur.py`).

**`autoascend/item/`:**
- Purpose: inventory model and item decisions.
- Contains: `inventory.py` (`Inventory`), `inventory_items.py`, `item.py` (`Item`), `item_manager.py` (`ItemManager`, `ContainerContent`), `item_priority_base.py`, `utils.py`.
- Key files: `autoascend/item/inventory.py`. Item priorities for the game are in `autoascend/global_logic.py` (`ItemPriority`, line 64).

**`autoascend/glyph/`:**
- Purpose: map NLE glyph ids to meanings (monsters, colours, hunger, shop).
- Contains: `monster.py`, `monflag.py`, `screen_symbols.py`, `screen_symbol_consts.py`, `__init__.py` (exports `MON`, `C`, `G`, `WEA`, `SHOP`, `Hunger`).

**`autoascend/monster_tracker/`:**
- Purpose: keep track of monsters between observations.
- Contains: `monster_tracker.py`, `kernels.py`, `__init__.py` (exports `MonsterTracker`, `disappearance_mask`).

**`autoascend/objects/`:**
- Purpose: NetHack object data (names, weights, flags) used by items and inventory.
- Contains: `data.py`, `utils.py`.

**`autoascend/soko_solver/`:**
- Purpose: solve Sokoban levels.
- Contains: `search.py`, `maps.py`.
- Tested by: `tests/test_soko_search.py`, `tests/test_soko_solver.py`, data in `tests/data/soko_real_*.json`.

**`nethack_screensaver/`:**
- Purpose: the product layer: run games forever in a terminal, pace them, render, log.
- Contains: `player.py` (main loop), `game.py` (`run_game`, `GameResult`, `role_abbrev`), `config.py`, `pacing.py` (`Pacer`, `QUIET_FRAMES`), `render.py` (`Renderer`, `format_status`, `format_reveal`), `gamelog.py` (`append_result`, `read_stats`, `LogStats`), `paths.py` (`config_path`, `state_dir`).
- Key files: `nethack_screensaver/game.py`, `nethack_screensaver/player.py`.

**`bench/`:**
- Purpose: measurement service for bot changes. Plays seeded games per commit, stores them, judges experiments, serves a dashboard and an MCP tool set.
- Contains:
  - `cli.py`: `screens-bench` entry point (`serve`, `wait`, `prune`, `import`).
  - `server.py`: `App` (business methods) and `make_handler` / `serve` (HTTP routes under `/api/jobs`, `/api/import`, `/`).
  - `scheduler.py`: `Scheduler` (slots, dispatch, collect, verdict, death guard).
  - `runner.py`: `ProcessWorker`, a child process per slot.
  - `worker.py`: the child script (`play [seed]` protocol).
  - `gitrefs.py`: ref resolution and worktree lifecycle (`ensure_worktree`, `prune`).
  - `store.py`: `Store` (SQLite schema, games, jobs, reference games).
  - `stats.py`: `wilson`, `newcombe`, `judge`, `judge_paired`, checkpoints.
  - `metrics.py`: `METRICS` registry, `killer`, `evaluate`.
  - `report.py`: `summary`, `compare`, `ladder_rows`.
  - `filters.py`: `parse_where` for game queries.
  - `importers.py`: xlog and dumplog import, parsing.
  - `reference.py`: yardstick summary of real ascensions.
  - `mcp_server.py`: MCP tools.
  - `static/index.html`: dashboard page served at `/`.
- Key files: `bench/server.py`, `bench/scheduler.py`, `bench/store.py`, `bench/metrics.py`.

**`bin/`:**
- Purpose: executable launchers.
- Contains: `nethack-screensaver` (bash script; resolves the repo from its own path, finds `.venv/bin/python`).

**`zsh/`:**
- Purpose: shell integration.
- Contains: `nethack-screensaver.zsh` (sets `TMOUT` and `TRAPALRM`; source it from `~/.zshrc`).

**`scripts/`:**
- Purpose: standalone tools.
- Contains: `benchmark.py` (parallel game runner using `run_game`, used as a fallback to the bench server).

**`tests/`:**
- Purpose: pytest suite. Default run skips `slow` tests (`pyproject.toml` `addopts`).
- Contains: unit tests named `test_<module>.py` for autoascend and nethack_screensaver modules, `test_bench_*.py` for the bench, shared fixtures in `conftest.py`, fakes in `bench_fakes.py` and `fake_player.py`.
- Data: `tests/data/` holds saved NLE observation arrays (`*.npy`), Sokoban maps (`soko_real_*.json`), and bench log samples (`bench_xlog_sample.txt`, `bench_dumplog_sample.txt`).

**`docs/`:**
- Purpose: project memory and plans.
- Contains: `STATUS.md` (current state), `ROADMAP.md` (sub-projects 0-8), `ASCENSION-GUIDE.md` (route reference), `superpowers/plans/` and `superpowers/specs/` (dated `YYYY-MM-DD-<topic>` files).

## Key File Locations

**Entry Points:**
- `nethack_screensaver/player.py`: screensaver main loop (`python -m nethack_screensaver.player`).
- `bin/nethack-screensaver`: launcher used by the zsh hook.
- `zsh/nethack-screensaver.zsh`: idle hook.
- `bench/cli.py`: `main` for `screens-bench`.
- `bench/worker.py`: bench child process.
- `bench/mcp_server.py`: MCP server.
- `scripts/benchmark.py`: fallback benchmark runner.

**Configuration:**
- `pyproject.toml`: dependencies, scripts, pytest markers, wheel packages.
- `uv.lock`: locked dependency versions.
- `.python-version`: Python pin.
- `.mcp.json`: MCP server command for `screens-bench`.
- `.claude/settings.local.json`: local Claude Code settings.
- `~/.config/nethack-screensaver/config.toml` (user, outside repo): read by `nethack_screensaver/config.py`.

**Core Logic:**
- `autoascend/agent.py`: decision loop and actions.
- `autoascend/global_logic.py`: milestone logic.
- `autoascend/exploration_logic.py`: exploration.
- `autoascend/plans.py`: strategies and milestone plans.
- `autoascend/ladder.py`: ascension ladder rungs.
- `nethack_screensaver/game.py`: game runner and `GameResult`.
- `bench/scheduler.py`: experiment scheduling and judging.

**Testing:**
- `tests/conftest.py`: shared fixtures (imports `bench_fakes`, `Store`, `Scheduler`, `App`).
- `tests/test_bench_e2e.py`: end-to-end bench test with real worker processes.
- `tests/test_game.py`, `tests/test_env_wrapper.py`: game runner and wrapper tests.
- `tests/test_ladder.py`, `tests/test_plans.py`: ladder and plan tests.

**Documentation:**
- `README.md`: install, configure, develop, bench usage.
- `docs/STATUS.md`: current status and next steps (also copied to `handoff.txt`).
- `docs/ROADMAP.md`: plan of sub-projects.
- `autoascend/PORTING.md`: port notes and experiment results (referenced by README; not present as a tracked file in the checked-in tree listing, verify before linking).

## Special Directories

**`.venv/`:**
- Purpose: virtual environment created by `uv sync`. The launcher requires it at `$REPO/.venv/bin/python`.
- Generated: Yes.
- Committed: No.

**`.planning/`:**
- Purpose: GSD planning and generated codebase maps (`.planning/codebase/`).
- Generated: Yes (by mapping commands).
- Committed: Not decided in this repository; check `.gitignore` before committing.

**`bench/static/`:**
- Purpose: static HTML for the bench dashboard, served by `bench/server.py`.
- Generated: No.
- Committed: Yes.

**External data outside the repo (not created by the code in the repo):**
- `~/.local/state/nethack-screensaver/` holds `games.jsonl` and `player.log` (`nethack_screensaver/paths.py`).
- `~/.local/share/screens-bench/results.db` holds the SQLite store (`bench/cli.py:18`).
- `~/.cache/screens-bench/` holds the import fetch cache and worktrees (`bench/cli.py:19`).
- `/ssd2/nethackFiles/` holds NLD-NAO unpacked human games used in analysis (from `docs/STATUS.md`). Not part of the repo.

## Naming Conventions

**Files:**
- Python modules: `snake_case.py`, e.g. `global_logic.py`, `env_wrapper.py`, `monster_tracker.py`.
- Tests: `tests/test_<module>.py`; bench tests are prefixed `test_bench_`.
- Documentation: `UPPERCASE.md` at the root or in `docs/` (`README.md`, `STATUS.md`, `ROADMAP.md`); dated plans and specs `YYYY-MM-DD-<topic>.md` under `docs/superpowers/`.
- Launchers: kebab-case, no extension (`bin/nethack-screensaver`).

**Directories:**
- Python packages: lowercase single word or `snake_case` (`autoascend`, `nethack_screensaver`, `monster_tracker`, `soko_solver`).
- Data directories: `data/` under `tests/` and `autoascend/objects/`.

**Symbols:**
- Classes: `PascalCase` (`Agent`, `GameResult`, `ProcessWorker`, `Scheduler`).
- Functions: `snake_case`, with `_` prefix for module-private helpers (`_strategy_and_plan`, `_ladder`, `_git`).
- Constants: `UPPER_SNAKE_CASE` (`DEPTH`, `AGENT_ARGS`, `STRATEGIES`, `RUNGS`, `METRICS`, `MAX_DEATHS_IN_ROW`).
- Strategy and metric names: lowercase short words (`pilgrim`, `daredevil`, `sightseer`, `treasure`; metric `dlvl6`, `rung`).

## Where to Add New Code

**New bot behaviour (a combat rule, an item rule, a movement rule):**
- Primary code: the matching sub-package, e.g. `autoascend/combat/fight_heur.py` for fights, `autoascend/item/inventory.py` for inventory, `autoascend/exploration_logic.py` for exploration.
- Hook it into the decision loop in `autoascend/agent.py` (`Agent.main`), or into a milestone in `autoascend/global_logic.py`.
- Tests: `tests/test_<module>.py` (e.g. `tests/test_fight_heur.py`, `tests/test_inventory_unload.py`).

**New strategy or milestone:**
- Add a `Milestone` value and a `STRATEGIES` entry in `autoascend/plans.py`. Handle the milestone in `autoascend/global_logic.py`.
- Update `choose_strategy` in `autoascend/plans.py` if it changes the random mix.
- Tests: `tests/test_plans.py`.

**New ladder rung:**
- Add to `RUNGS` in `autoascend/ladder.py`. Tests: `tests/test_ladder.py`. The bench picks up `rung<N>` metrics from `autoascend/ladder.py`.

**New per-game field:**
- Add to `GameResult` in `nethack_screensaver/game.py` with a default value. Tests: `tests/test_game.py`, `tests/test_gamelog.py`.

**New bench metric:**
- Add one entry to `METRICS` in `bench/metrics.py`. Tests: `tests/test_bench_metrics.py`.

**New screensaver setting:**
- Add to `Config` and `load_config` in `nethack_screensaver/config.py`. Document in `README.md`. Tests: `tests/test_config.py`.

**New rendering or pacing behaviour:**
- Renderer: `nethack_screensaver/render.py`. Pacing: `nethack_screensaver/pacing.py`. Tests: `tests/test_render.py`, `tests/test_pacing.py`.

**New bench HTTP route or API:**
- Business logic in `App` (`bench/server.py`), route in `make_handler`, MCP wrapper in `bench/mcp_server.py`. Tests: `tests/test_bench_server.py`, `tests/test_bench_mcp.py`.

**New bench storage table or column:**
- `bench/store.py` (`_SCHEMA`, bump `SCHEMA_VERSION` if needed). Tests: `tests/test_bench_store.py`.

**New import source:**
- `bench/importers.py`; reference summary in `bench/reference.py`. Fixtures in `tests/data/`. Tests: `tests/test_bench_importers.py`.

**Utilities:**
- Bot helpers: `autoascend/utils.py`. Glyph helpers: `autoascend/glyph/`. Object data: `autoascend/objects/`.
- Screensaver helpers: `nethack_screensaver/paths.py`. Bench helpers: `bench/filters.py`, `bench/gitrefs.py`.

**New test data:**
- Under `tests/data/`. Load it from tests the way the existing ones do (see `tests/conftest.py`).

## Special Notes for Planning

- Code the bench measures must be committed. Create work on a branch and commit before starting an experiment (README, `docs/STATUS.md`).
- Keep `autoascend/plans.py` and `autoascend/ladder.py` light: they are imported by the config loader and the bench.
- The bench worker imports only `nethack_screensaver.game` and `autoascend`; do not add `bench` imports to those packages.

---

*Structure analysis: 2026-10-22*
