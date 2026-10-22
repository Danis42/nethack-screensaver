---
last_mapped_commit: 9ff6a6ff76cd4517f68a51c62a15a3b6b98ba387
last_mapped_at: 2026-10-22
---
# Testing Patterns

**Analysis Date:** 2026-10-22

## Test Framework

**Runner:**
- pytest `>=8` (dev dependency group in `pyproject.toml`)
- Config: `[tool.pytest.ini_options]` in `pyproject.toml`
- Python `3.13` (`.python-version`)

**Pytest settings (from `pyproject.toml`):**
- `testpaths = ["tests"]`
- Marker `slow` is declared as "plays real games (minutes)"
- `addopts = "-m 'not slow'"`: slow tests are skipped by default
- `filterwarnings = ["error:overflow encountered:RuntimeWarning"]`: numpy overflow warnings fail the test

**Assertion Library:**
- Plain `assert` statements with pytest's rewriting. `pytest.raises` for expected exceptions (`tests/test_game.py`).

**Run Commands:**

```bash
uv run pytest                          # Fast tests (slow excluded by addopts)
uv run pytest -m slow                  # Real-game tests, minutes each
uv run pytest tests/test_bench_store.py  # One module
uv run pytest -k outcome               # Filter by name
uv run python scripts/benchmark.py -n 50 -j 8   # Benchmark run, not a test
```

(Commands from `README.md`. No coverage tool is configured, so there is no coverage command.)

## Test File Organization

**Location:**
- All tests are in a single top-level `tests/` directory, separate from source. There are no co-located `test_*.py` files.
- Test data lives in `tests/data/` (`.txt` log samples, `.json` soko maps, `.npy` tty char arrays).

**Naming:**
- `test_<area>.py`. Bench tests are prefixed `test_bench_` (`test_bench_server.py`, `test_bench_scheduler.py`, `test_bench_stats.py`). Game-side tests use the module name (`test_game.py`, `test_ladder.py`, `test_soko_solver.py`).
- Test functions are `test_<behaviour in words>`: `test_games_are_stored_per_commit_oldest_first`, `test_store_survives_reopening`, `test_watchdog_rearmed_by_changes_does_not_fire` (`tests/test_bench_store.py`, `tests/test_game.py`).

**Structure:**

```
tests/
├── conftest.py               # Shared bench fixtures: bench_repo, bench_app, bench_url
├── bench_fakes.py            # FakeWorker and game() factory (imported by name)
├── fake_player.py            # Fake game player for game-level tests
├── test_bench_*.py           # Bench server, store, scheduler, MCP, importers, e2e
├── test_game.py              # nethack_screensaver.game, incl. @pytest.mark.slow tests
├── test_<module>.py          # One file per autoascend/ or nethack_screensaver/ module
└── data/                     # Recorded inputs (logs, maps, arrays)
```

## Test Structure

**Suite Organization:**
Flat module-level test functions are the norm. Classes are not used for grouping. Parametrized cases use `@pytest.mark.parametrize` (17 uses across the suite) with a tuple table. From `tests/test_game.py`:

```python
@pytest.mark.parametrize("strategy,reason,loot,expected", [
    ("sightseer", "ESCAPED: escaped the dungeon", False, "escaped"),
    ("treasure", "ESCAPED: escaped the dungeon", True, "escaped with loot"),
    ("pilgrim", "watchdog", False, "crashed"),
])
def test_outcome(strategy, reason, loot, expected):
    assert game.outcome(strategy, reason, 7, loot) == expected
```

**Patterns:**
- Arrange in the test body: create a `Store(tmp_path / "r.db")`, add rows, then assert on query results. See `tests/test_bench_store.py`.
- Use `tmp_path` for every on-disk artifact. Never write to the repo or a fixed path.
- Teardown is by fixture `yield` (see `bench_url` in `tests/conftest.py`: start the server, `yield`, then `stop.set()`, `httpd.shutdown()`, `httpd.server_close()`).
- Timing-sensitive code is tested with real short sleeps, not clocks (`tests/test_game.py` watchdog tests sleep 0.4 to 3 seconds).

**Assertion pattern:**
- Use assert messages to show context when the value is opaque: `assert result.end_reason == ... , result.end_reason` (`tests/test_game.py`), `assert depths` message on the progress test.

## Fixtures

**Shared fixtures (`tests/conftest.py`):**
- `bench_repo(tmp_path)`: creates a real git repository with two commits on `main` and a `feature` branch at `HEAD~1`. It uses `subprocess` with `git -C`. Use this fixture when a test needs real git history.
- `bench_app(tmp_path, bench_repo)`: an `App` backed by a `Store`, a `Scheduler` with 16 slots, and a `FakeWorker` that plays instantly.
- `bench_url(bench_app)`: serves `bench_app` on `port=0` in a daemon thread and yields the base URL.

**Module-local fixtures:**
- `url(bench_url, monkeypatch)` in `tests/test_bench_mcp.py` extends the shared URL fixture. Module fixtures build on `conftest.py` fixtures; do not duplicate their setup.

**Test doubles (`tests/bench_fakes.py`):**
- `FakeWorker(sha, make, log, seeded=True)` plays instantly. Each `play(seed)` calls `make(sha, index)` and records the seed. Use `results()` to drain pending results. `alive()` and `close()` mirror the real worker interface.
- `game(depth)` returns a minimal game-result dict with `max_depth`, `end_reason`, and `outcome`.

**Data files:**
- Recorded inputs are in `tests/data/`: `bench_dumplog_sample.txt`, `bench_xlog_sample.txt` (used by `tests/test_bench_importers.py`), `soko_real_between_pits.json` and `soko_real_bottom_timeout.json` (used by `tests/test_soko_search.py`/`test_soko_solver.py`), `escaped_tty_chars.npy` and `final_tty_chars.npy` (used by `tests/test_render.py`). Load them relative to the test file (`Path(__file__).parent / "data"`).
- New recorded fixtures go in `tests/data/`, and should be small.

## Mocking

**Framework:** `pytest` `monkeypatch`. `unittest.mock` is not used in the project.

**Patterns:**

```python

# Swap a registry entry for one test (tests/test_game.py)

monkeypatch.setitem(STRATEGIES, "test_escape",
                    StrategySpec("test_escape", "Test", "escape the dungeon",
                                 (M.RETURN_TO_SURFACE, M.LEAVE_DUNGEON)))
```

```python

# Replace a worker factory with an instant fake (tests/conftest.py)

sched = Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=16)
```

**What to Mock:**
- Worker processes and the game engine in bench tests: use `FakeWorker` so the scheduler and server run without playing games.
- Strategy and config registries: use `monkeypatch.setitem` on the dict.
- Time-dependent or environment-dependent values: monkeypatch them rather than sleeping when possible.

**What NOT to Mock:**
- Git: `bench_repo` builds a real repository. Do not fake `git` output.
- SQLite: `Store` tests use a real database file in `tmp_path`.
- The HTTP server: `bench_url` runs the real `ThreadingHTTPServer` on an ephemeral port.
- NetHack itself: game-level behaviour is covered by the real `nle` environment in `slow` tests (`tests/test_game.py`), not by fakes.

## Fixtures and Factories

**Test Data:**
Small dict factories build result rows. From `tests/test_bench_store.py`:

```python
def _game(depth=3, **extra):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", **extra}
```

Use this shape: a `_name(...)` helper with defaults and `**extra` for overrides.

**Location:**
- Shared factories: `tests/bench_fakes.py`
- Per-module factories: defined at the top of the test module with a leading underscore

## Coverage

**Requirements:** None enforced. No `pytest-cov` dependency and no coverage threshold are configured.

**View Coverage:**

```bash
uv run --with pytest-cov pytest --cov=autoascend --cov=bench --cov=nethack_screensaver
```

(Not run by the project. Use it ad hoc only.)

## Test Types

**Unit Tests:**
- The majority of the suite (about 212 `test_` functions). They cover pure logic: bench metrics, filters, stats, store, scheduler, gitrefs, importers, config validation, and soko solver search.
- Use `FakeWorker` and `tmp_path` so they run in seconds.

**Integration Tests:**
- Bench end-to-end (`tests/test_bench_e2e.py`): the scheduler, server, and store together, with fake workers.
- MCP (`tests/test_bench_mcp.py`): tools driven over the running HTTP server.
- Launcher (`tests/test_launcher.py`) and env wrapper (`tests/test_env_wrapper.py`) exercise the real wiring.

**Slow / Real-Game Tests:**
- Marked `@pytest.mark.slow` in `tests/test_game.py`. They run real headless NetHack games via `nle` and take 10 to 40 seconds per game.
- Run with `uv run pytest -m slow`. Assertions check invariants: no exception end reason, progress past Dlvl 3 in at least one of four games (`test_agent_makes_progress`), and that results serialize to JSON.
- Keep new slow tests in this file or a sibling file with the same marker. Do not run them by default.

**E2E Tests:**
- Not a separate framework. `tests/test_bench_e2e.py` is the bench end-to-end test and uses in-process fakes, not a browser.

## Common Patterns

**Async / Concurrency Testing:**
- The bench server runs in a thread. Tests drive the scheduler by ticking it under the app lock. `run_until_idle(app, ticks=3000)` in `tests/conftest.py` loops `app.scheduler.tick()` while holding `app.lock` and raises `AssertionError("job did not finish")` if the job never ends. Use this helper instead of sleeping for job completion.
- Threads started for servers must be daemon threads and must be shut down in fixture teardown.

**Error Testing:**

```python
def test_job_lifecycle(tmp_path):
    ...
    with pytest.raises(RuntimeError):   # schema mismatch case
        Store(path)
```

Use `pytest.raises` with the specific exception type, then assert on state afterward. For the game watchdog, `pytest.raises(game.WatchdogTimeout)` wraps the context manager (`tests/test_game.py`).

**Process and filesystem:**
- Invoke git with `subprocess.run(..., check=True, capture_output=True)` as in `tests/conftest.py::git`. Set `user.email` and `user.name` inside the temp repo; never rely on the host git config.

## Guidance for New Tests

- Put a bench test in `tests/test_bench_<area>.py`, and a game-module test in `tests/test_<module>.py`.
- Reuse `bench_app`, `bench_repo`, and `bench_url` from `tests/conftest.py` before writing new setup.
- Put any new fake in `tests/bench_fakes.py`, and import it by name.
- Mark anything that launches NetHack with `@pytest.mark.slow`.
- Add a parametrized case table for behaviour that is a mapping (outcomes, classifications) rather than separate functions.
- Keep tests free of network access and of writes outside `tmp_path`.

---

*Testing analysis: 2026-10-22*
