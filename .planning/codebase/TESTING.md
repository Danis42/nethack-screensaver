---
last_mapped_commit: af6684a5bece0253790adedfb6da502a2583b869
last_mapped_at: 2026-11-12
---
# Testing Patterns

**Analysis Date:** 2026-11-12

## Test Framework

**Runner:**
- pytest `>=8` (dev dependency group in `pyproject.toml`), plus `{include-group = "bench"}`.
- Config: `[tool.pytest.ini_options]` in `pyproject.toml`
  - `testpaths = ["tests"]`
  - `markers = ["slow: plays real games (minutes)"]`
  - `addopts = "-m 'not slow'"` (slow tests are deselected by default)
  - `filterwarnings = ["error:overflow encountered:RuntimeWarning"]`
- Shared fixtures: `tests/conftest.py`.
- Python: `.python-version` pins 3.13; `requires-python = ">=3.13,<3.14"`.

**Assertion Library:**
- Plain `assert` statements (pytest rewriting). Numeric comparisons use `np.testing` and `pytest.approx` where relevant (`np.testing`/`pytest.raises` appear in about 30 places across `tests/`).
- Expected-failure marker used once: `pytest.mark.xfail`.

**Run Commands:**
```bash
uv run pytest                  # fast tests (slow deselected by addopts)
uv run pytest -m slow          # plays real games (minutes)
uv run pytest tests/test_castle.py            # single module
uv run pytest -k unload        # by name substring
uv run pytest -p no:cacheprovider   # if .pytest_cache is unwanted
```
Source: `README.md` lines 60-61 for the first two. Coverage and watch commands are not configured; none detected.

## Test File Organization

**Location:**
- All tests live in a single top-level `tests/` directory, separate from source. There are no co-located `test_*.py` files in `autoascend/`, `bench/`, or `nethack_screensaver/`.
- `tests/` has no `__init__.py`; pytest uses rootdir-based discovery, and helper modules are imported by bare name (`from bench_fakes import ...`).

**Naming:**
- `test_<area>.py` matching the module under test: `test_castle.py`, `test_fight_heur.py`, `test_inventory_unload.py`, `test_bench_*.py` for the `bench/` package, `test_soko_search.py` / `test_soko_solver.py` for `autoascend/soko_solver/`.
- Test functions: `test_<behaviour>` (no classes observed).

**Structure:**
```
tests/
├── conftest.py              # bench fixtures (bench_repo, bench_app, bench_url) and run_until_idle()
├── bench_fakes.py           # FakeWorker, game() helpers for bench tests
├── fake_player.py           # fake player object for autoascend tests
├── data/                    # recorded fixtures: *.txt dumplog/xlog samples, *.npy tty char grids, soko_*.json
├── test_<module>.py         # one file per module, ~57 files
```

## Test Structure

**Suite Organization:**
Flat module-level functions; no `class Test*` groups. A test typically builds inputs, calls one function, and asserts several related facts on one or two lines. Example from `tests/test_bench_store.py`:
```python
def test_games_are_stored_per_commit_oldest_first(tmp_path):
    store = Store(tmp_path / "r.db")
    for depth in (1, 2, 3):
        store.add_game("aaa", None, _game(depth))
    store.add_game("bbb", 7, _game(9))
    assert store.count("aaa") == 3 and store.count("bbb") == 1 and store.count("ccc") == 0
    assert [g["max_depth"] for g in store.games("aaa")] == [1, 2, 3]
```

**Patterns:**
- Setup: small module-level helpers that build fixtures (`_item(name, weight, ...)` in `tests/test_inventory_unload.py`, `_game(depth=3, **extra)` in `tests/test_bench_store.py`, `seen_courtyard(flipped, x_range)` in `tests/test_castle.py`).
- Pytest fixtures for heavier resources: 6 `@pytest.fixture` definitions. In `tests/conftest.py`, `bench_repo` builds a real temporary git repo with two commits; `bench_app` wires `Store`, `Scheduler`, and `App`; `bench_url` starts the HTTP server on port 0 and shuts it down on teardown (`yield` then `httpd.shutdown()`).
- Teardown: `yield`-style fixtures (`bench_url`). Otherwise rely on `tmp_path` cleanup.
- Polling helper: `run_until_idle(app, ticks=3000)` in `tests/conftest.py` ticks the scheduler under `app.lock` until the job finishes, else raises `AssertionError`. Reuse it instead of sleeping.
- Assertions: chain related checks with `and` on one line for state (`assert store.count(...) == 3 and ...`); use separate asserts for distinct behaviours.

## Parametrization

- `@pytest.mark.parametrize` is used 17 times. Prefer it for table-driven cases (same logic, many inputs).
- Loops over variants are also used when a test checks both orientations of a map: `for flipped in (False, True):` in `tests/test_castle.py`.

## Mocking

**Framework:** Hand-rolled fakes, not `unittest.mock`/`MagicMock` (zero occurrences). `monkeypatch` is used 68 times for patching attributes, env vars, and module globals.

**Patterns:**
```python
# Lightweight stand-ins for game objects (tests/test_inventory_unload.py)
from types import SimpleNamespace

def _item(name, weight, category=nh.TOOL_CLASS, equipped=False, droppable=True):
    return SimpleNamespace(name=name, category=category, equipped=equipped,
                           weight=lambda: weight, can_be_dropped_from_inventory=lambda: droppable)
```
```python
# Injected fake worker for the scheduler (tests/conftest.py)
sched = Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=16)
```
- Use `monkeypatch.setattr(module, "name", value)` to replace module-level functions or constants; use `monkeypatch.setenv` / `delenv` for environment (monkeypatch is the default; no other mock library is used).
- Use `capsys` (134 uses) to assert on printed output from CLI and scripts rather than patching `print`.

**What to Mock:**
- Game/NetHack state: build `SimpleNamespace` objects or use `tests/fake_player.py` instead of starting NLE.
- Worker processes and external runners in bench tests: inject a `FakeWorker` factory (see `tests/bench_fakes.py`).
- Time: use `autoascend`/`nethack_screensaver` fixed-clock helpers (`tests/test_fixed_clock.py` covers `nethack_screensaver/fixed_clock.py`) rather than wall-clock time.

**What NOT to Mock:**
- Filesystem and SQLite: use `tmp_path` and a real `Store` (`tests/test_bench_store.py` reopens the real DB file).
- Git: `tests/conftest.py` creates real git repositories with `subprocess` (`git init`, commits, branches). Keep this real.
- numpy masks and grid geometry: pass real arrays (`np.zeros(SHAPE, bool)`), as `tests/test_castle.py` does.
- Recorded game output: use the files in `tests/data/` (e.g. `bench_xlog_sample.txt`, `final_tty_chars.npy`, `soko_real_bottom_timeout.json`) so tests run against real NetHack text and screens.

## Fixtures and Factories

**Test Data:**
- Recorded NetHack data in `tests/data/`: text logs (`bench_dumplog_sample.txt`, `bench_xlog_sample.txt`), terminal character grids (`escaped_tty_chars.npy`, `final_tty_chars.npy`), and Sokoban fixtures (`soko_real_between_pits.json`, `soko_real_bottom_timeout.json`).
- Load them relative to the test file (`Path(__file__).parent / "data" / ...`). Do not hard-code absolute paths.
- Game-fact constants (map layouts, square coordinates) live in the source module and are imported by tests (`castle.MAP`, `castle.KEY_SQUARES`), so tests track the source of truth.

**Factories:**
- `game(depth, **extra)` in `tests/bench_fakes.py` and `_game(...)` in `tests/test_bench_store.py` build bench run records with default fields.
- `_item(...)` builds fake inventory items.

**Location:**
- Shared fixtures: `tests/conftest.py`. Shared fakes: `tests/bench_fakes.py`, `tests/fake_player.py`. Per-test helpers stay in their own test module.

## Coverage

**Requirements:** None enforced. No `--cov` setting in `pyproject.toml`, no `.coveragerc`, no CI config detected.

**View Coverage:**
```bash
uv run --with pytest-cov pytest --cov=autoascend --cov=bench --cov=nethack_screensaver
```
(`pytest-cov` is not a declared dependency; this uses `uv run --with` for an ad-hoc run.)

## Test Types

**Unit Tests:**
- The majority of the 497 `def test_` functions. Pure logic over castle geometry, item priorities, inventory selection, combat heuristics, soko search, bench storage and metrics.
- Keep them fast; they run under the default `addopts`.

**Integration Tests:**
- Bench end-to-end and server tests: `tests/test_bench_e2e.py`, `tests/test_bench_server.py`, `tests/test_bench_mcp.py`, `tests/test_bench_runner.py`, `tests/test_bench_gitrefs.py`. They use the real Store, Scheduler, git repo, and an HTTP server on an ephemeral port.
- Replay and seeded-script tests: `tests/test_replay.py`, `tests/test_seeded_scripts.py`, `tests/test_nld_study.py`, `tests/test_launcher.py`.

**Slow Tests (`@pytest.mark.slow`):**
- 10 tests marked `slow` play real NetHack games via NLE and take minutes. Found in `tests/test_bench_e2e.py`, `tests/test_soko_search.py`, `tests/test_replay.py`, `tests/test_game.py`, `tests/test_accessories.py`, `tests/test_item_text.py`.
- Run with `uv run pytest -m slow`. Mark any new test that starts a game with `@pytest.mark.slow`, or it will run in the fast suite.

**E2E Tests:** Not using a browser framework. `bench/static/index.html` is not tested by an automated browser test.

## Common Patterns

**Async / concurrency testing:**
- No `asyncio` tests. Concurrency is polled, not awaited: use `run_until_idle` (ticks the scheduler under `app.lock`) and bounded loops that raise `AssertionError` on timeout.
- Servers: start on `port=0`, read `httpd.server_address[1]`, and shut down in fixture teardown (`tests/conftest.py`).

**Error testing:**
```python
# Prefer pytest.raises for expected exceptions
with pytest.raises(ValueError):
    parse(...)
```
- Control-flow exceptions (`AgentFinished`, `AgentPanic`) are asserted by type.
- Use `pytest.mark.xfail` with a reason only for known bugs; one instance exists.

**Output testing:** Use `capsys.readouterr()` to assert on printed output (see the 134 `capsys` uses across `tests/`).

**Filesystem testing:**
- Always `tmp_path` (286 uses). Never write into the repo from a test.

**Warnings:** Numeric overflow warnings are errors (`filterwarnings` in `pyproject.toml`). A test that triggers an overflow must handle it explicitly.

## Gaps

- No coverage measurement or threshold.
- No linter or type-check step in the test workflow.
- The slow suite is not run by default; regressions in full-game behaviour surface only when `-m slow` is run manually.
- `scripts/` modules are tested only where a test file imports them (`tests/test_nld_study.py`, `tests/test_seeded_scripts.py`); most scripts have no test.

---

*Testing analysis: 2026-11-12*
