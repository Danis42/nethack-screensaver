---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
# Codebase Concerns

**Analysis Date:** 2026-11-12

## Tech Debt

**Reproducibility: NLE dependency points at a gitignored local build:**
- Issue: `pyproject.toml` pins `nle` to `path = "reference/nle-src"` (a NetHack 5 NLE build), but `.gitignore` excludes `reference/`. A fresh clone cannot run `uv sync` until that directory is rebuilt by hand.
- Files: `pyproject.toml`, `.gitignore`, `reference/nle-src/`
- Impact: Only the original machine can install the project. Tests, the screensaver and the bench server all fail to start elsewhere.
- Fix approach: Document the NLE build steps in `README.md` (currently only says `uv sync`), or publish the `screens-nh5` NLE branch as a git source in `[tool.uv.sources]`.

**Hard-coded local paths:**
- Issue: `.mcp.json` sets `SCREENS_BENCH_PYTHON` to `~/.cache/screens-nh5/venv/bin/python`.
- Files: `.mcp.json`, `bench/mcp_server.py`
- Impact: The MCP bench tools break on any other user or machine.
- Fix approach: Read the interpreter path from a relative location or environment variable with a documented default, and keep machine-specific values in `.claude/settings.local.json`.

**Large monolithic modules:**
- Issue: `autoascend/agent.py` (2142 lines) and `autoascend/global_logic.py` (1362 lines) hold most of the decision logic. `autoascend/character.py` (656 lines) and `autoascend/exploration_logic.py` (534 lines) are also large.
- Files: `autoascend/agent.py`, `autoascend/global_logic.py`, `autoascend/character.py`, `autoascend/exploration_logic.py`
- Impact: Changes to one behavior (combat, prayer, item use) easily touch shared state. Git history shows `agent.py` changed in 46 commits and `global_logic.py` in about 47 recent edits, which makes merge and regression risk high.
- Fix approach: Extract cohesive units (prayer, Elbereth/escape, shop/item handling) into the existing submodules (`autoascend/combat/`, `autoascend/item/`) and keep `agent.py` as orchestration only.

**Unfinished TODOs and placeholders in game logic:**
- Issue: At least 60 `TODO` comments across `autoascend/`, mostly in `character.py` (lines 304-632, many empty `# TODO:` stubs in the weapon and damage code), `agent.py` (teleport control, portals, one-way portals, intrinsics), `exploration_logic.py` (wizard's tower, portals, pits) and `fight_heur.py`.
- Files: `autoascend/character.py`, `autoascend/agent.py`, `autoascend/exploration_logic.py`, `autoascend/combat/fight_heur.py`, `autoascend/item/inventory_items.py` (line 102, twoweapon support)
- Impact: Some unhandled states (two-weapon, riding, levitation, polymorph into handless forms) are silently unsupported.
- Fix approach: Turn the TODOs that affect gameplay into tracked issues, and add a test or explicit fallback for each unsupported state.

**Placeholder constant in level logic:**
- Issue: `PLANE = 1000  # TODO: fill with actual value` in `autoascend/level.py`.
- Files: `autoascend/level.py` (line 15); used in `autoascend/agent.py` (line 2100, `# TODO: check level num`)
- Impact: Planar-level detection is unreliable.
- Fix approach: Use the real Elemental/Astral plane depth values from `reference/nethack-5.0.0`.

**Assertions used for control flow:**
- Issue: `assert dir, glyph  # TODO: portals` appears in `autoascend/exploration_logic.py` (lines 35 and 115). `assert dis[to_y, to_x] != -1` is used in `autoascend/agent.py` (around line 1265).
- Files: `autoascend/exploration_logic.py`, `autoascend/agent.py`
- Impact: Under `python -O` these checks disappear. Unexpected glyphs (portals) crash instead of being handled.
- Fix approach: Replace with explicit branches that log and return a fallback action.

**Duplicate and dead code paths:**
- Issue: `autoascend/combat/rl_scoring.py` (lines 94-99) has a commented-out pickle/base64 export that writes to `/tmp/vis/observations.txt`. `scripts/` contains many overlapping analysis tools (`seeded_report.py`, `nld_study.py`, `fixes_triage.py`, `fixes_shortlist.py`, `bench_watch.py`).
- Files: `autoascend/combat/rl_scoring.py`, `scripts/`
- Impact: Extra maintenance surface and confusion about which script is current.
- Fix approach: Delete the commented export and consolidate the scripts, or document their status in `scripts/README` (none exists).

## Known Bugs

**Elbereth-ignoring monsters defeat the castle plan:**
- Symptoms: Recent state notes record minotaur and castle failures (6/14 castle failures, castle score 7/20 vs 8/20 after the float-past change). A staged fix "castle-elb11 (Elbereth-ignorer fix, 8/20)" is recorded in git history but the cause is noted only as "Elbereth-ignorer bug found".
- Files: `autoascend/castle.py`, `autoascend/combat/fight_heur.py`, `autoascend/combat/stair_escape.py`, `scripts/staged_run.py`
- Trigger: Entering the castle stage with minotaurs or other Elbereth-ignoring monsters nearby.
- Workaround: None recorded in the code. The staged fix is not on `main` history beyond the staging commit.

**`--More--` handling may send a stray key:**
- Symptoms: `autoascend/agent.py` (around line 423) strips `--More--` from the message without sending a key, with a FIXME noting it is "too risky to change". The worst case is an `Unknown command ' '` message.
- Files: `autoascend/agent.py`
- Trigger: Any message that ends in `--More--` when the environment is not waiting for input.
- Workaround: The bot tolerates the unknown-command message.

**Diagonal paths through inwalkable tiles:**
- Symptoms: `autoascend/agent.py` (around line 1265) notes that the BFS path can cut diagonally through inwalkable tiles. The bot recovers through "panic exceptions", so it wastes turns and can stall in doorways.
- Files: `autoascend/agent.py`, `autoascend/utils.py`
- Trigger: Moving through doorways or tight corners.
- Workaround: Stuck detection in `autoascend/stuck.py`.

**Silent error swallowing in the screensaver:**
- Symptoms: Many `except Exception:` blocks in `nethack_screensaver/game.py` (lines 119, 136, 143, 211, 219, 232, 239, 398) and `autoascend/global_logic.py` (lines 555, 724) hide failures. Comments say "agent never started" or "measuring must never end a game". Bare `except:` in `autoascend/item/item_manager.py` (line 195) also catches `KeyboardInterrupt`.
- Files: `nethack_screensaver/game.py`, `autoascend/global_logic.py`, `autoascend/item/item_manager.py`, `autoascend/env_wrapper.py` (line 102), `autoascend/agent.py` (lines 379, 1208, 1507, 2142 use bare `pass`)
- Trigger: Any unexpected exception in these paths.
- Impact: Crashes in the idle screensaver or the bench worker leave no trace in `~/.local/state/nethack-screensaver/player.log` beyond what the caller logs.
- Fix approach: Narrow the exceptions, log tracebacks at least at debug level, and replace bare `except:` with `except Exception:`.

**Placeholder map data:**
- Symptoms: `autoascend/soko_solver/maps.py` contains `.0.0.0.0.` runs that look like map tokens rather than walls. Not verified as a bug, but worth checking.
- Files: `autoascend/soko_solver/maps.py` (line 589)
- Trigger: Sokoban solver on that map.
- Workaround: Covered only by `tests/test_soko_solver.py` and `tests/test_soko_search.py`.

## Security Considerations

**Bench server has no authentication and runs commands from HTTP requests:**
- Risk: `bench/server.py` accepts JSON POSTs that start jobs, import external xlog URLs (`start_import` fetches `http(s)` URLs), and shut down the server. The only protection is a `Host` header check against `127.0.0.1` and `localhost`.
- Files: `bench/server.py` (lines 186-189, 264-271), `bench/importers.py`, `bench/cli.py`
- Current mitigation: Binds to `127.0.0.1` by default and rejects non-local `Host` headers, which blocks ordinary DNS-rebinding and cross-site browser requests.
- Recommendations: Add a per-session token for mutating endpoints (`/api/shutdown`, start and import calls). Validate `Origin` as well as `Host`. Restrict the xlog importer to an allow-list of hosts.

**Runtime C compilation and shared-object preloading:**
- Risk: `nethack_screensaver/fixed_clock.py` compiles C source with `cc` and loads it through `LD_PRELOAD` into every worker process. The `.so` is cached in `~/.cache/screens/` by a SHA-1 of the source, so a tampered cache file would run arbitrary code in every worker.
- Files: `nethack_screensaver/fixed_clock.py` (lines 40-60, 73-80 `preload_env`)
- Current mitigation: Cache is per-user and keyed by content digest. The source is embedded in the module.
- Recommendations: Verify the cached library's digest before loading, not only its file name. Keep the cache directory mode `0700`.

**Shell and subprocess calls with external input:**
- Risk: `scripts/scenario_run.py` (line 75) runs `exec(open(os.environ["SCENARIO_HOOK"]).read())` in-process. `nethack_screensaver/dungeon_truth.py` runs `nm -D` on a library path. `bench/gitrefs.py` builds `git` arguments from user-supplied refs (list form, so no shell injection, but refs starting with `-` are not rejected).
- Files: `scripts/scenario_run.py`, `nethack_screensaver/dungeon_truth.py`, `bench/gitrefs.py`, `bench/server.py` (`start_experiment`, `start_baseline`)
- Current mitigation: `SCENARIO_HOOK` is opt-in debug input. Subprocess calls avoid `shell=True`.
- Recommendations: Reject refs that begin with `-` before passing them to `git rev-parse`. Keep `SCENARIO_HOOK` debug-only and document it as arbitrary code execution.

**Local LLM sweep endpoint:**
- Risk: `scripts/wiki_sweep/ollama_sweep.py` posts to `http://localhost:11434/api/generate` with no auth. Input wiki text is sent to a model and the output is written as JSONL that other scripts may trust.
- Files: `scripts/wiki_sweep/ollama_sweep.py` (line 32)
- Current mitigation: Localhost only.
- Recommendations: Treat model output as untrusted before it reaches `autoascend/` data files.

**Secrets handling:**
- Risk: No secrets are tracked. `.gitignore` excludes `.venv/`, `reference/`, and `archive/` (which holds a 86 MB `screens-v0-final.tar.gz`). `.claude/settings.local.json` and `.gsd/dispatch-isolation-sentinel.json` are present in the working tree.
- Files: `.gitignore`, `archive/`, `.claude/settings.local.json`
- Current mitigation: `archive/` and `reference/` are ignored.
- Recommendations: Confirm `.claude/settings.local.json` is ignored before committing new settings. Add `.gsd/` and `.worktrees/` checks to CI if it is ever added.

## Performance Bottlenecks

**Per-move BFS and full-grid numpy work in the agent:**
- Problem: `autoascend/agent.py` runs `self.bfs(...)` on demand (line 1265) and builds `ignore_mask` with `utils.isin(...)` each state update (line 640). The source comments say `# TODO: optimize` (line 639), and `autoascend/combat/movement_priority.py` has two more `# TODO: optimize` markers (lines 8, 23).
- Files: `autoascend/agent.py`, `autoascend/combat/movement_priority.py`, `autoascend/utils.py` (lines 113, 121)
- Cause: Recomputation per step on the full 21x79 map, plus Python-level loops.
- Improvement path: Cache BFS distance maps per level and invalidate on map change. Use the numba dependency (already in `pyproject.toml`) for the hot loops.

**Benchmark throughput limits:**
- Problem: `bench/scheduler.py` runs one worker process per slot, each with `OMP_NUM_THREADS=1` and `nice=10` (`bench/runner.py`). The README notes workers were previously oversubscribed.
- Files: `bench/scheduler.py`, `bench/runner.py`, `bench/worker.py`
- Cause: Each game is a full NLE rollout with a 120-second watchdog (`scripts/scenario_run.py`).
- Improvement path: Size the worker pool from CPU count in `bench/cli.py`, and use `scripts/seeded_report.py` results to decide when to stop a baseline early.

## Fragile Areas

**Monster tracking and hallucination:**
- Files: `autoascend/monster_tracker/monster_tracker.py` (line 88), `autoascend/glyph/monster.py`, `autoascend/glyph/monflag.py`
- Why fragile: Under hallucination, glyphs are random. The tracker has a `# TODO: on hallu no monsters are peaceful` note. `autoascend/item/item_manager.py` clears `glyph` when hallucinating, which changes parsing paths.
- Safe modification: Test with `tests/test_monster_tracker.py` and add a hallucination case before changing any tracker logic.
- Test coverage: No test covers hallucination in combat decisions.

**Item name parsing:**
- Files: `autoascend/item/item_manager.py` (`get_item_from_text`, around lines 185-200), `autoascend/item/item.py`, `autoascend/item/inventory.py`
- Why fragile: Parsing relies on NetHack message text. A bare `except:` falls back to an `unknown` object when blind. The TODO notes "it may not work as expected" for shields, gems and potions.
- Safe modification: Use `tests/test_item_text.py` and `tests/test_scrolls.py` as regression fixtures; add the message string as a fixture before changing parsing.
- Test coverage: Only the cases in the existing item tests.

**Shared mutable state across the agent:**
- Files: `autoascend/agent.py`, `autoascend/global_logic.py`, `autoascend/level.py`, `autoascend/plans.py`
- Why fragile: `agent.py` relies on `level.items` being updated as a side effect of `check_items` (comment near line 719). A FIXME at line 527 notes that `update_state()` is not always called. Plans (`autoascend/plans.py`, `autoascend/strategy.py`) depend on these updates.
- Safe modification: Make `update_state()` the single entry point before any new state read. Add a test that asserts the call order.
- Test coverage: `tests/test_plans.py` and `tests/test_game.py` cover the main flows only.

**Screensaver process model:**
- Files: `zsh/nethack-screensaver.zsh`, `bin/nethack-screensaver`, `nethack_screensaver/game.py`, `nethack_screensaver/staging.py`
- Why fragile: The idle hook runs the game from `TRAPALRM`, which fires inside the zsh line editor. Any exception or long-running game blocks the prompt until the game exits.
- Safe modification: Keep the hook thin and test changes with `tests/test_launcher.py`.

**Sokoban solver timing:**
- Files: `autoascend/soko_solver/search.py`, `autoascend/soko_solver/__init__.py` (line 34 bare `pass`), `tests/test_soko_search.py`
- Why fragile: The solver has a 10-second search cap. `tests/test_soko_search.py` marks the large case `TOO_BIG` as `xfail` and relies on a stored solution for it. Stored solutions must match the NetHack 5 map layouts (`tests/test_soko_search.py` skips when none exists).
- Safe modification: Regenerate stored solutions only after changing the map data in `autoascend/soko_solver/maps.py`.

## Scaling Limits

**Single-machine, single-user state:**
- Current capacity: Bench results go to `~/.local/share/screens-bench/results.db` (SQLite). Game history goes to `~/.local/state/nethack-screensaver/games.jsonl`.
- Limit: `games.jsonl` is append-only with no rotation. `bench/store.py` loads all games for a commit into memory (`store.games(sha)` in `bench/server.py`).
- Scaling path: Add rotation for `games.jsonl`, and page queries in `bench/store.py` by commit.

**Worktree accumulation:**
- Current capacity: One git worktree per benchmarked commit under `~/.cache/screens-bench/`. `bench/gitrefs.py` prunes worktrees older than 14 days.
- Limit: `prune()` only runs on demand; a long-running server keeps every worktree until the next prune.
- Scaling path: Call `prune()` from the scheduler on a timer.

## Dependencies at Risk

**NLE (NetHack Learning Environment) from a local NetHack 5 branch:**
- Risk: `pyproject.toml` pins `nle` to a local path build of the `screens-nh5` branch, not a released version. The README targets NLE 1.3.0 and NetHack 3.6 benchmarks, but the research notes (`.planning/research/`) target NetHack 5.0.0.
- Impact: Behavior differences between NetHack 3.6 and 5.0 (for example Sokoban layouts and monster flags) can silently change results.
- Migration plan: Pick one target version, document it in `README.md`, and gate version-specific data (`autoascend/objects/data.py`, `autoascend/soko_solver/maps.py`) on it.

**Python version pinned to 3.13 only:**
- Risk: `pyproject.toml` sets `requires-python = ">=3.13,<3.14"`, and `.python-version` pins the interpreter.
- Impact: Any system without 3.13 cannot run the project.
- Migration plan: Widen once NLE supports later Python versions.

**`numba` and `opencv-python-headless` build dependencies:**
- Risk: Both are large native dependencies. `uv.lock` (74 KB) pins them, but `numba>=0.61` is a loose lower bound.
- Impact: Upgrades can change JIT behavior in `autoascend/monster_tracker/kernels.py`.
- Migration plan: Pin exact versions in tests that cover the kernels.

## Missing Critical Features

**No CI configuration:**
- Problem: No `.github/workflows`, `tox.ini`, or other CI config is tracked. Tests run only by hand (`uv run pytest`, `uv run pytest -m slow`).
- Blocks: Regressions in `autoascend/` are caught only when someone runs the suite. The Elbereth regression above is an example of drift that a CI benchmark gate could catch.

**No documentation of the bench data schema:**
- Problem: `bench/store.py`, `bench/importers.py`, and `bench/report.py` define record shapes that `scripts/seeded_report.py` and the MCP tools depend on, with no written schema.
- Blocks: New metrics (`bench/metrics.py`) are hard to add without reading the store code.

**Documentation drift on project goals:**
- Problem: `README.md` says "Ascension is out of reach for this bot" and reports NetHack 3.6 benchmarks. `.planning/research/external/PROMPTS.md` says the bot "aims for a real ascension" on NetHack 5.0.0. `CHANGELOG.md` describes 0.2.0 targets as realistic.
- Blocks: Planning agents read different goals depending on which file they load.

## Test Coverage Gaps

**Real-game and Elbereth behavior:**
- What's not tested: Combat decisions against Elbereth-ignoring monsters (minotaurs, `@` humans, shopkeepers) at the castle stage.
- Files: `autoascend/castle.py`, `autoascend/combat/fight_heur.py`, `tests/test_castle.py`
- Risk: The known castle regression is not caught by unit tests.
- Priority: High

**Hallucination:**
- What's not tested: Monster and item decisions while hallucinating.
- Files: `autoascend/monster_tracker/monster_tracker.py`, `autoascend/item/item_manager.py`
- Risk: Random glyphs cause wrong peaceful/hostile decisions.
- Priority: Medium

**Screensaver failure paths:**
- What's not tested: The `except Exception:` branches in `nethack_screensaver/game.py` (agent crash, ladder fallback, inventory half-parsed).
- Files: `nethack_screensaver/game.py`, `tests/test_game.py`
- Risk: Crashes that should exit cleanly instead leave the terminal in an odd state.
- Priority: Medium

**Slow tests excluded by default:**
- What's not tested by default: `pyproject.toml` deselects tests marked `slow` (16 deselected in collection). Real game playthroughs run only with `uv run pytest -m slow`.
- Files: `pyproject.toml`, `tests/test_seeded_scripts.py`, `tests/test_replay.py`
- Risk: Breakage in full-game flows is not seen during normal development.
- Priority: Medium

**Bench server security:**
- What's not tested: Token or origin checks beyond the `Host` header (none exist yet). The `bench/server.py` shutdown path is covered only through `tests/test_bench_server.py`.
- Files: `bench/server.py`, `tests/test_bench_server.py`
- Risk: A local page or process can start jobs or shut the server down.
- Priority: Low

---

*Concerns audit: 2026-11-12*
