---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
<!-- refreshed: 2026-10-22 -->

# Codebase Concerns

**Analysis Date:** 2026-10-22

## Tech Debt

**`autoascend/agent.py` (1646 lines) is a god module:**
- Issue: The main agent loop, state parsing, combat, movement, item use, and exception policy all live in one class. Many unresolved `TODO`/`FIXME` markers sit in the hot paths, e.g. `autoascend/agent.py:352`, `:455` (`update_state()` not called on all states), `:463-464` (wishing strategy, assumed blessed), `:472` (teleport control), `:558` (`# TODO: optimize`), `:922`/`:930` (portals, one-way portals on elemental/astral planes), `:949`.
- Files: `autoascend/agent.py`
- Impact: Changes to one behaviour routinely regress another. Several planned behaviours are silently unimplemented.
- Fix approach: Split by concern (state parsing, combat, movement, item handling) behind the existing `global_logic` / `strategy` seams before adding new plans. Turn each TODO into an issue or a test first.

**`autoascend/character.py` has many unfinished parsers:**
- Issue: Long runs of stub TODOs: `autoascend/character.py:286` (levitation), `:330` (spellcaster classes other than the current ones), `:378`, `:480-492` (two-weapon, riding), `:514`-`:549` (`# TODO: implement` / empty TODO blocks).
- Files: `autoascend/character.py`
- Impact: Characters using those features are played with incomplete knowledge of their state.
- Fix approach: Prioritise by what the ascension route actually hits (riding and two-weapon are likely unused by the pilgrim plan); delete or document the rest.

**Bare `except:` in item parsing:**
- Issue: `autoascend/item/item_manager.py:174` catches everything, including `KeyboardInterrupt` and `SystemExit`. The blind-case fallback (`O.from_name('unknown')`) and the re-raise are both inside it, so a real bug is hidden whenever the character is not blind.
- Files: `autoascend/item/item_manager.py`
- Impact: Item-name parse failures can be swallowed or mis-classified; signal-driven exits can be eaten.
- Fix approach: Catch the specific parse exception type(s) and let `BaseException` propagate.

**Assertions and `assert 0` used as control flow:**
- Issue: `autoascend/agent.py` relies on `assert init_finished` (around line 1620) and `assert 0` (around line 1640) to mark impossible paths. Under `python -O` these checks disappear.
- Files: `autoascend/agent.py`
- Impact: Silent progression past an unfinished init or past a strategy that should never return.
- Fix approach: Raise explicit `RuntimeError` instead.

**Module-level mutable caches:**
- Issue: `autoascend/global_logic.py:29-34` keeps a lazily filled global `_PRIZES`, and `autoascend/plans.py` builds shared `STRATEGIES` / `DEFAULT_PLAN` objects at import time. The bench runs many games per process and reuses them.
- Files: `autoascend/global_logic.py`, `autoascend/plans.py`
- Impact: Leftover state can leak between games or seeds, which would undermine the paired bench comparisons (`bench/scheduler.py` judges experiments seed by seed).
- Fix approach: Make per-game state an attribute of the agent, or reset caches at game start, and cover it with a test.

**Duplicated status document:**
- Issue: `handoff.txt` (repo root) and `docs/STATUS.md` are both tracked and currently identical (85 lines each). The project's "save" workflow updates `handoff.txt` as a copy of `docs/STATUS.md`.
- Files: `handoff.txt`, `docs/STATUS.md`
- Impact: The copies will drift as soon as one is edited without the other.
- Fix approach: Keep `docs/STATUS.md` as the single source and make `handoff.txt` a generated copy, or drop it.

**zsh hook overwrites shell globals:**
- Issue: `zsh/nethack-screensaver.zsh` sets `TMOUT` unconditionally and defines `TRAPALRM`, replacing any idle-timeout or alarm trap the user already has.
- Files: `zsh/nethack-screensaver.zsh`
- Impact: Sourcing the hook from `~/.zshrc` can break an existing shell configuration.
- Fix approach: Only set `TMOUT` if unset, and chain to a previously defined `TRAPALRM`.

## Known Bugs and Unfinished Behaviour

**Pathing can cut diagonal corners:**
- Symptoms: The agent's path can pass diagonally between tiles that are not walkable diagonally.
- Files: `autoascend/agent.py:1050` (`FIXME: currently the path can lead through diagonally inwalkable tiles`)
- Trigger: Doorways and tight corridors; the note in the code says the agent gets unstuck only after several panics.
- Workaround: Unstick logic (`UNSTICK_AFTER = 100` in `autoascend/agent.py`) and `CANNOT_KICK` handling.

**State update not guaranteed on every path:**
- Symptoms: Stale observations can drive decisions.
- Files: `autoascend/agent.py:455` (`FIXME: self.update_state() won't be called on all states sometimes`)
- Trigger: Some state transitions skip `update_state()`.
- Workaround: None in code; the stuck-detection counter (`inactivity_counter`) eventually raises `Cyclic Panic`.

**Unhandled portal and planar levels:**
- Symptoms: Elemental and astral plane transitions are not modelled; the stair destination is recorded with a placeholder level number.
- Files: `autoascend/agent.py:919`, `:922`, `:930`, `:1604` (`# TODO: check level num`)
- Trigger: Reaching those planes (not on the pilgrim route in normal play).
- Workaround: None.

**Blind inventory parsing:**
- Symptoms: While blind, unidentifiable item names are mapped to a generic `unknown` object.
- Files: `autoascend/item/item_manager.py:170-177`
- Trigger: Blindness combined with an item name that does not parse.
- Workaround: The generic fallback above; it is the only path that does not raise.

## Security Considerations

**Bench server has no CSRF token or Origin check:**
- Risk: Any page open in the user's browser can make a cross-origin request to `http://127.0.0.1:8765`. The `Host` check in `bench/server.py` (`_refused`, around lines 170-175) blocks DNS rebinding. A cross-origin JSON `POST`/`DELETE` triggers a CORS preflight that the server never answers (`BaseHTTPRequestHandler` returns 501 to OPTIONS), so the browser does not send the write. That blocks the attack only through this indirect behaviour, not through an explicit `Origin` check; the existing test covers foreign-page requests.
- Files: `bench/server.py` (`make_handler`, `do_POST`, `do_DELETE`)
- Current mitigation: Localhost binding by default (`serve(..., host="127.0.0.1")`), a `Host` allow-list, and a required `Content-Type: application/json`.
- Recommendations: Add an explicit `Origin` check for writes and a per-start random token written to the state directory.

**Any local user can drive the bench server:**
- Risk: The bench server listens on a fixed port with no authentication. On a shared machine another local account can start jobs that run code from any benchmarked commit (`bench/runner.py` starts `bench/worker.py` with `PYTHONPATH` set to a git worktree) and can trigger network imports.
- Files: `bench/server.py`, `bench/runner.py`, `bench/gitrefs.py`
- Current mitigation: None beyond the loopback bind.
- Recommendations: Require a token as above, and document that the server executes repository code.

**Server-side fetch of user-supplied URLs:**
- Risk: `POST /api/import` with a URL makes the server fetch it (`bench/importers.py` `fetch`, `import_xlog`). Only `http(s)` schemes are accepted, but there is no host restriction, so the request can reach internal addresses from the server's network position.
- Files: `bench/server.py` (`start_import`, around line 114-120), `bench/importers.py`
- Current mitigation: Scheme check (`http`/`https` only, covered by `tests/test_bench_server.py`); localhost-only clients.
- Recommendations: Restrict import URLs to a known list of hosts (for example the hardfought/xlog hosts in `bench/importers.py`).

**Launcher word-splits an environment variable into the command:**
- Risk: `NETHACK_SCREENSAVER_PLAYER` is read with `read -r -a PLAYER <<<"$NETHACK_SCREENSAVER_PLAYER"` (`bin/nethack-screensaver`) and executed as argv. This is the user's own environment, so it is not an external attack surface, but it means any value is executed.
- Files: `bin/nethack-screensaver`
- Current mitigation: None needed for a single-user machine; it is intentional for testing.
- Recommendations: Document it as an execution hook, not a configuration value.

**Secrets handling:** No credential files, API keys or `.env` contents were found in tracked files. `.gitignore` covers `.venv/`, `__pycache__/`, `.pytest_cache/`, and `.superpowers/` only, so any future `.env` file would be committed unless added.

## Performance Bottlenecks

**Game-log stats re-read the whole file each game:**
- Problem: `read_stats` reads and parses all of `games.jsonl` before every game.
- Files: `nethack_screensaver/gamelog.py` (`read_stats`), called from `nethack_screensaver/player.py` (`main`)
- Cause: The file is append-only and never rotated, so the cost grows with every game played.
- Improvement path: Keep running totals in a small state file, or read only the tail.

**Single lock around the bench store and scheduler:**
- Problem: `bench/store.py` serialises every query behind one `RLock`, and the scheduler loop in `bench/server.py` (`loop`, every 0.2 s) holds the server lock while it ticks.
- Files: `bench/store.py` (lines 37-60), `bench/server.py` (`loop`)
- Cause: One SQLite connection shared across HTTP threads and the scheduler.
- Improvement path: One connection per thread (WAL is already enabled), and keep the scheduler's critical section short.

**Parallel games are heavy:**
- Problem: The scheduler defaults to `slots=11` (`bench/scheduler.py`), each slot a full NetHack/NLE process running under `nice`.
- Files: `bench/scheduler.py` (`Scheduler.__init__`), `bench/runner.py`
- Cause: One process per game with its own worktree.
- Improvement path: Make the slot count configurable from the CLI and default it to the core count.

**Numba and OpenCV cold start:**
- Problem: `numba` and `opencv-python-headless` are imported when a game starts, adding delay on each new process.
- Files: `pyproject.toml`, `autoascend/monster_tracker/kernels.py` (numba kernels)
- Cause: JIT compilation on first use.
- Improvement path: Cache compiled kernels, or keep one long-lived worker per slot (the bench already does this).

## Fragile Areas

**Watchdog depends on `SIGALRM` in the main thread:**
- Files: `nethack_screensaver/game.py` (`_ScreenWatchdog`, lines ~110-130; `WatchdogTimeout` raised from the alarm)
- Why fragile: `signal.signal` only works on the main thread, and any code that installs its own `SIGALRM` handler will cancel the watchdog.
- Safe modification: Keep game execution on the main thread; never call `run_game` from a thread without changing the watchdog.
- Test coverage: The paths are exercised by `@pytest.mark.slow` tests in `tests/test_game.py`, which are not run by default.

**Screensaver process lifecycle:**
- Files: `bin/nethack-screensaver`, `nethack_screensaver/player.py` (`_install_signals`, `_on_term`)
- Why fragile: The launcher relies on `SIGTERM`/`SIGHUP` raising `SystemExit`, and on the agent re-raising it (`autoascend/agent.py` `handle_exception` re-raises `SystemExit`). A change to that exception policy would leave orphaned NLE processes.
- Safe modification: Keep the `SystemExit` pass-through in `handle_exception`; test the launcher with `tests/test_launcher.py`.

**Worktree pruning can remove a worktree in use:**
- Files: `bench/gitrefs.py` (`ensure_worktree`, `prune`)
- Why fragile: `prune` removes worktrees with `git worktree remove --force` when their mtime is older than 14 days. `ensure_worktree` touches the mtime only when a worktree is requested, so a long job that keeps using one commit can have its worktree removed underneath a running worker.
- Safe modification: Touch the mtime on each game start, or skip worktrees that have a live worker.
- Test coverage: `tests/test_bench_gitrefs.py` covers pruning in isolation, not during an active job.

**Pinned runtime:**
- Files: `pyproject.toml` (`requires-python = ">=3.13,<3.14"`, `nle==1.3.0`), `uv.lock`
- Why fragile: The NetHack Learning Environment pin determines which NetHack version and screen format the parser understands. The achievement-bit table in `bench/importers.py` (`ACHIEVE_36`) assumes NetHack 3.6 layouts.
- Safe modification: Change `nle` only with the full test suite and a fresh baseline in the bench.

**Hard-coded external sources:**
- Files: `bench/importers.py` (`HARDFOUGHT_DUMPLOG` template, `USER_AGENT`), `bench/reference.py`
- Why fragile: Import and reference features depend on hardfought.org's URL layout and on its response format.
- Safe modification: Keep the import tests on the saved samples in `tests/data/` (`bench_dumplog_sample.txt`, `bench_xlog_sample.txt`).

## Scaling Limits

**Bench history:**
- Current capacity: `Scheduler` keeps only the last 500 finish times (`deque(maxlen=500)`); the store keeps every game in SQLite.
- Limit: The store has no pruning, and `ensure_worktree` keeps one worktree per benchmarked commit for up to 14 days.
- Scaling path: Add an archive or vacuum step, and keep the worktree root bounded by count as well as age.

**Game log:**
- Current capacity: Unbounded `games.jsonl` in the state directory (`nethack_screensaver/paths.py`).
- Limit: Startup time grows linearly (see Performance Bottlenecks).
- Scaling path: Rotate the file or switch to the store-style summary.

## Dependencies at Risk

**`nle==1.3.0`:**
- Risk: Pinned to an old NLE release with an upstream NetHack version that is not maintained.
- Impact: Environment changes, a changed NetHack screen format, or a broken build of the native package would stop all play.
- Migration plan: Vendor the NLE version used by the bench (`uv.lock`) so builds stay reproducible, and track upstream separately.

**`mcp>=2.3` (bench dependency group):**
- Risk: Only a lower bound is pinned.
- Impact: A future major version could change the tool interface used by `bench/mcp_server.py`.
- Migration plan: Pin an upper bound, or test the MCP tool surface in CI.

## Missing Critical Features

**No CI, lint, or type-check configuration:**
- Problem: No `.github` workflow, linter or formatter configuration, or type checker is present in the repository; the only quality gate is `pytest`.
- Blocks: Automated checks on the bench server's security-sensitive handlers and on the bare `except` above.

**No shared logging policy:**
- Problem: Errors go to `stderr` (the launcher redirects it to `player.log`), to the stats logger, and to `print` in `autoascend/agent.py` (`PANIC!!!!`). There is no single logger.
- Blocks: Diagnosing a failed unattended game from the logs alone.

## Test Coverage Gaps

**Core agent loop is untested directly:**
- What's not tested: `autoascend/agent.py` (1646 lines), `autoascend/global_logic.py` (899 lines), `autoascend/character.py`, `autoascend/exploration_logic.py`, and `autoascend/item/item_manager.py` have no dedicated test modules. Coverage comes only from the slow end-to-end tests.
- Files: `autoascend/agent.py`, `autoascend/global_logic.py`, `autoascend/character.py`, `autoascend/exploration_logic.py`, `autoascend/item/item_manager.py`
- Risk: Regressions in the main loop and strategy transitions surface only in long game runs.
- Priority: High

**Slow tests are off by default:**
- What's not tested: 13 tests are deselected by `addopts = "-m 'not slow'"` in `pyproject.toml` (real game play in `tests/test_game.py`, `tests/test_bench_e2e.py`, and the hard Sokoban cases in `tests/test_soko_search.py`).
- Files: `tests/test_game.py`, `tests/test_bench_e2e.py`, `tests/test_soko_search.py`
- Risk: The watchdog, game lifecycle and end-to-end bench paths can break without a failing default run.
- Priority: Medium

**Current default run:** `.venv/bin/python -m pytest -q` gives 247 passed, 5 skipped, 13 deselected in about 27 s on 2026-10-22.

**Bench server security:**
- What's not tested: `tests/test_bench_server.py` covers foreign-page requests (`test_requests_a_foreign_web_page_could_send_are_refused`) and non-http import URLs (`test_imports_only_fetch_http_urls`). No test covers a cross-origin `POST`/`DELETE` with a JSON content type, or an import URL pointing at an internal host.
- Files: `bench/server.py`, `tests/test_bench_server.py`
- Risk: The write protection could weaken unnoticed in a refactor.
- Priority: High

**Launcher behaviour across shells:** `tests/test_launcher.py` drives the launcher through bash and zsh pseudo-terminals. Behaviour with a shell that already defines `TMOUT` or `TRAPALRM` (see the zsh hook above) is not covered.
- Files: `zsh/nethack-screensaver.zsh`, `tests/test_launcher.py`
- Risk: Shell configuration conflicts appear only on the user's machine.
- Priority: Low

---

*Concerns audit: 2026-10-22*
