# Bench Server Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A local server that plays NetHack bot games on demand per commit, stores every game, judges A/B experiments with honest error margins, shows a live status page, is driven by Claude through MCP, and imports real ascensions as a yardstick.

**Architecture:** Package `bench/` (separate from `nethack_screensaver/`). A `Store` (SQLite) holds games per commit SHA, jobs and reference games. A `Scheduler` hands one game at a time to worker slots; each slot runs `bench/worker.py` in a subprocess with `PYTHONPATH` set to a git worktree of the commit under test. An `App` exposes the logic, a stdlib `ThreadingHTTPServer` serves the JSON API and one static HTML page, and `bench/mcp_server.py` is a thin MCP client of that API.

**Tech Stack:** Python 3.13 standard library (`sqlite3`, `http.server`, `subprocess`, `urllib`), `mcp` (FastMCP) in dependency group `bench`, pytest, git worktrees, plain HTML/JS.

**Spec:** `docs/superpowers/specs/2026-10-20-bench-server-design.md`

## Global Constraints

- Only new dependency: `mcp`, in dependency group `bench` (also included in `dev` so tests can import it). Runtime dependencies of the screensaver stay unchanged.
- Server listens on `127.0.0.1:8765` by default; never on other interfaces.
- Database `~/.local/share/screens-bench/results.db` (override `SCREENS_BENCH_DATA`), cache and worktrees under `~/.cache/screens-bench/` (override `SCREENS_BENCH_CACHE`), server URL override `SCREENS_BENCH_URL`.
- Workers: default 11, started with `nice -n 10`; `run_game(watchdog_seconds=120)`.
- Checkpoints 192, 384, 576, 1152 games per side; 99% intervals at the first three, 95% at 1152; only the primary metric decides.
- `bench/worker.py` must not import anything from `bench` (old commits' worktrees do not have it).
- Never push, never add remotes (local-only repo).
- Tests: `uv run pytest -q -m ""` must stay green; new test files are flat in `tests/` named `test_bench_*.py`.
- Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.

## Review Focus

- Server restarted while a job ran: the job must show `interrupted` (not stay `running`), and its stored games must still count for the next job — tests in Task 1 (`interrupt_unfinished`) and Task 7 (`build_app`).
- Port 8765 already taken (a server already runs): `serve` must exit with a clear message, not a traceback — test in Task 7.
- The same xlogfile imported twice: no duplicate reference games — test in Task 10.
- A branch that gets new commits while its job runs: the job must keep the SHA resolved at start — test in Task 7.
- Games from older commits that lack newer `GameResult` fields (e.g. `unsticks`): metrics skip them and report how many were skipped — test in Task 3.

---

## File Structure

| File | Responsibility |
|---|---|
| `bench/__init__.py` | Package marker, one-line docstring |
| `bench/store.py` | SQLite: games, jobs, reference games, schema version |
| `bench/stats.py` | Wilson / Newcombe intervals, checkpoints, `judge()` |
| `bench/metrics.py` | Metric registry, `killer()`, `evaluate()` |
| `bench/filters.py` | `parse_where()` filter language |
| `bench/report.py` | Dashboard `summary()` and A/B `compare()` tables |
| `bench/gitrefs.py` | `resolve()`, `ensure_worktree()`, `prune()`, `history()` |
| `bench/worker.py` | Standalone game-playing subprocess (stdin "play" → JSON line) |
| `bench/runner.py` | `ProcessWorker`: one subprocess per slot |
| `bench/scheduler.py` | Jobs, dispatch, verdicts, worker deaths |
| `bench/importers.py` | xlog/dumplog fetch, parse, import |
| `bench/reference.py` | Summary of imported ascensions |
| `bench/server.py` | `App` (logic used by HTTP and tests), HTTP handler, `serve()` |
| `bench/cli.py` | `screens-bench serve / wait / prune / import ...` |
| `bench/mcp_server.py` | MCP tools over the HTTP API, auto-starts the server |
| `bench/static/index.html` | Status page |
| `.mcp.json` | Registers the MCP server for Claude Code |
| `tests/test_bench_*.py`, `tests/data/bench_*` | Tests and fixtures |

---

### Task 1: Package skeleton and Store

**Files:**
- Create: `bench/__init__.py`, `bench/store.py`, `tests/test_bench_store.py`
- Modify: `pyproject.toml`

**Interfaces:**
- Produces: `Store(path)` with `add_game(sha, job_id, result, finished_at=None) -> int`, `count(sha) -> int`, `games(sha, limit=None) -> list[dict]` (oldest first), `add_job(kind, spec) -> int`, `set_job(job_id, state, result=None)`, `job(job_id) -> dict | None`, `jobs(kind=None, limit=50) -> list[dict]` (newest first), `next_queued() -> dict | None`, `interrupt_unfinished() -> int`, `shas() -> list[dict]`, `add_reference(source, record) -> bool`, `references() -> list[dict]`, `set_dumplog(ref_id, text)`. Job dicts: `{"id", "kind", "spec", "state", "created_at", "ended_at", "result"}`. Reference dicts: `{"id", "source", "name", "starttime", "role", "turns", "record", "dumplog"}`. Constant `END_STATES = ("done", "stopped", "failed", "interrupted")`.

- [ ] **Step 1: Add the package to `pyproject.toml`**

Change the `[dependency-groups]` and wheel sections and add a script entry:

```toml
[project.scripts]
screens-bench = "bench.cli:main"

[dependency-groups]
dev = ["pytest>=8", {include-group = "bench"}]
bench = ["mcp>=1.2"]

[tool.hatch.build.targets.wheel]
packages = ["autoascend", "nethack_screensaver", "bench"]
```

Create `bench/__init__.py`:

```python
"""Bench server: plays bot games per commit, compares commits, imports real ascensions."""
```

Run: `uv sync` — Expected: installs `mcp` and its dependencies, no errors.

- [ ] **Step 2: Write the failing tests**

`tests/test_bench_store.py`:

```python
import sqlite3

import pytest

from bench.store import Store


def _game(depth=3, **extra):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", **extra}


def test_games_are_stored_per_commit_oldest_first(tmp_path):
    store = Store(tmp_path / "r.db")
    for depth in (1, 2, 3):
        store.add_game("aaa", None, _game(depth))
    store.add_game("bbb", 7, _game(9))
    assert store.count("aaa") == 3 and store.count("bbb") == 1 and store.count("ccc") == 0
    assert [g["max_depth"] for g in store.games("aaa")] == [1, 2, 3]
    assert [g["max_depth"] for g in store.games("aaa", limit=2)] == [1, 2]
    assert [s["sha"] for s in store.shas()] == ["bbb", "aaa"]


def test_store_survives_reopening(tmp_path):
    Store(tmp_path / "r.db").add_game("aaa", None, _game())
    assert Store(tmp_path / "r.db").count("aaa") == 1


def test_job_lifecycle(tmp_path):
    store = Store(tmp_path / "r.db")
    first = store.add_job("baseline", {"sha": "aaa", "games": 5})
    second = store.add_job("experiment", {"candidate": "bbb"})
    assert store.next_queued()["id"] == first
    store.set_job(first, "running", {"games": 0})
    assert store.next_queued()["id"] == second
    store.set_job(first, "done", {"games": 5})
    job = store.job(first)
    assert job["state"] == "done" and job["result"] == {"games": 5} and job["ended_at"] is not None
    assert job["spec"] == {"sha": "aaa", "games": 5}
    assert [j["id"] for j in store.jobs()] == [second, first]
    assert [j["id"] for j in store.jobs("experiment")] == [second]
    assert store.job(999) is None


def test_unfinished_jobs_become_interrupted_and_keep_their_games(tmp_path):
    store = Store(tmp_path / "r.db")
    running = store.add_job("baseline", {"sha": "aaa", "games": 5})
    store.set_job(running, "running", {})
    queued = store.add_job("baseline", {"sha": "bbb", "games": 5})
    store.add_game("aaa", running, _game())
    assert store.interrupt_unfinished() == 2
    assert store.job(running)["state"] == "interrupted"
    assert store.job(queued)["state"] == "interrupted"
    assert store.next_queued() is None
    assert store.count("aaa") == 1


def test_reference_games_are_unique_per_source_name_and_start(tmp_path):
    store = Store(tmp_path / "r.db")
    record = {"name": "player", "starttime": "1777773884", "role": "Bar", "turns": "44867"}
    assert store.add_reference("hardfought", record) is True
    assert store.add_reference("hardfought", record) is False
    assert store.add_reference("other", record) is True
    refs = store.references()
    assert len(refs) == 2 and refs[0]["turns"] == 44867 and refs[0]["dumplog"] is None
    store.set_dumplog(refs[0]["id"], "dump text")
    assert store.references()[0]["dumplog"] == "dump text"


def test_schema_version_mismatch_is_refused(tmp_path):
    Store(tmp_path / "r.db")
    db = sqlite3.connect(tmp_path / "r.db")
    db.execute("UPDATE meta SET value = '99' WHERE key = 'schema'")
    db.commit()
    db.close()
    with pytest.raises(RuntimeError, match="schema"):
        Store(tmp_path / "r.db")
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_store.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'bench.store'`

- [ ] **Step 4: Implement `bench/store.py`**

```python
"""SQLite storage for the bench server: games per commit, jobs and reference games."""
import json
import sqlite3
import threading
import time
from pathlib import Path

SCHEMA_VERSION = 1
END_STATES = ("done", "stopped", "failed", "interrupted")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY, sha TEXT NOT NULL, job_id INTEGER,
    finished_at REAL NOT NULL, json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS games_by_sha ON games (sha, id);
CREATE TABLE IF NOT EXISTS jobs (
    id INTEGER PRIMARY KEY, kind TEXT NOT NULL, spec TEXT NOT NULL, state TEXT NOT NULL,
    created_at REAL NOT NULL, ended_at REAL, result TEXT);
CREATE TABLE IF NOT EXISTS reference_games (
    id INTEGER PRIMARY KEY, source TEXT NOT NULL, name TEXT NOT NULL,
    starttime INTEGER NOT NULL, role TEXT, turns INTEGER, json TEXT NOT NULL, dumplog TEXT,
    UNIQUE (source, name, starttime));
"""


def _job(row):
    return {"id": row["id"], "kind": row["kind"], "spec": json.loads(row["spec"]),
            "state": row["state"], "created_at": row["created_at"], "ended_at": row["ended_at"],
            "result": None if row["result"] is None else json.loads(row["result"])}


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._db = sqlite3.connect(path, check_same_thread=False, timeout=30)
        self._db.row_factory = sqlite3.Row
        self._lock = threading.RLock()
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.executescript(_SCHEMA)
            with self._db:
                row = self._db.execute("SELECT value FROM meta WHERE key = 'schema'").fetchone()
                if row is None:
                    self._db.execute("INSERT INTO meta VALUES ('schema', ?)", (str(SCHEMA_VERSION),))
                elif int(row["value"]) != SCHEMA_VERSION:
                    raise RuntimeError(f"{path} has schema {row['value']}, this code expects {SCHEMA_VERSION}")

    def _one(self, sql, args=()):
        with self._lock:
            return self._db.execute(sql, args).fetchone()

    def _all(self, sql, args=()):
        with self._lock:
            return self._db.execute(sql, args).fetchall()

    def _write(self, sql, args=()):
        with self._lock, self._db:
            return self._db.execute(sql, args)

    # games

    def add_game(self, sha, job_id, result, finished_at=None):
        return self._write("INSERT INTO games (sha, job_id, finished_at, json) VALUES (?, ?, ?, ?)",
                           (sha, job_id, finished_at or time.time(), json.dumps(result))).lastrowid

    def count(self, sha):
        return self._one("SELECT COUNT(*) AS n FROM games WHERE sha = ?", (sha,))["n"]

    def games(self, sha, limit=None):
        """Results of a commit, oldest first."""
        sql, args = "SELECT json FROM games WHERE sha = ? ORDER BY id", (sha,)
        if limit is not None:
            sql, args = sql + " LIMIT ?", args + (int(limit),)
        return [json.loads(r["json"]) for r in self._all(sql, args)]

    def shas(self):
        rows = self._all("SELECT sha, COUNT(*) AS n, MAX(finished_at) AS last FROM games "
                         "GROUP BY sha ORDER BY last DESC")
        return [{"sha": r["sha"], "games": r["n"], "last": r["last"]} for r in rows]

    # jobs

    def add_job(self, kind, spec):
        return self._write("INSERT INTO jobs (kind, spec, state, created_at) VALUES (?, ?, 'queued', ?)",
                           (kind, json.dumps(spec), time.time())).lastrowid

    def set_job(self, job_id, state, result=None):
        ended = time.time() if state in END_STATES else None
        self._write("UPDATE jobs SET state = ?, ended_at = ?, result = ? WHERE id = ?",
                    (state, ended, None if result is None else json.dumps(result), job_id))

    def job(self, job_id):
        row = self._one("SELECT * FROM jobs WHERE id = ?", (job_id,))
        return None if row is None else _job(row)

    def jobs(self, kind=None, limit=50):
        if kind is None:
            rows = self._all("SELECT * FROM jobs ORDER BY id DESC LIMIT ?", (limit,))
        else:
            rows = self._all("SELECT * FROM jobs WHERE kind = ? ORDER BY id DESC LIMIT ?", (kind, limit))
        return [_job(r) for r in rows]

    def next_queued(self):
        row = self._one("SELECT * FROM jobs WHERE state = 'queued' ORDER BY id LIMIT 1")
        return None if row is None else _job(row)

    def interrupt_unfinished(self):
        """Jobs a stopped server left queued or running; returns how many were marked."""
        return self._write("UPDATE jobs SET state = 'interrupted', ended_at = ? "
                           "WHERE state IN ('queued', 'running')", (time.time(),)).rowcount

    # reference games (real ascensions)

    def add_reference(self, source, record):
        cur = self._write(
            "INSERT OR IGNORE INTO reference_games (source, name, starttime, role, turns, json) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (source, record["name"], int(record["starttime"]), record.get("role"),
             int(record.get("turns", 0)), json.dumps(record)))
        return cur.rowcount == 1

    def references(self):
        return [{"id": r["id"], "source": r["source"], "name": r["name"], "starttime": r["starttime"],
                 "role": r["role"], "turns": r["turns"], "record": json.loads(r["json"]),
                 "dumplog": r["dumplog"]}
                for r in self._all("SELECT * FROM reference_games ORDER BY id")]

    def set_dumplog(self, ref_id, text):
        self._write("UPDATE reference_games SET dumplog = ? WHERE id = ?", (text, ref_id))
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_store.py`
Expected: 6 passed

- [ ] **Step 6: Commit**

```bash
git add pyproject.toml uv.lock bench/__init__.py bench/store.py tests/test_bench_store.py
git commit -m "feat(bench): SQLite store for games, jobs and reference games

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 2: Statistics and verdicts

**Files:**
- Create: `bench/stats.py`, `tests/test_bench_stats.py`

**Interfaces:**
- Produces: `CHECKPOINTS = (192, 384, 576, 1152)`, `Z95`, `Z99`, `wilson(k, n, z) -> (lo, hi)`, `newcombe(k1, n1, k2, n2, z) -> (diff, lo, hi)` (diff = p1 − p2), `z_for(checkpoint) -> float`, `judge(k_cand, n_cand, k_base, n_base, checkpoint) -> Verdict`, `Verdict(state, checkpoint, diff, lo, hi)` with `.detectable` (half-width) and `.as_dict()`. States: `"better"`, `"worse"`, `"no measurable difference"`, `"open"`.

- [ ] **Step 1: Write the failing tests**

`tests/test_bench_stats.py`:

```python
import pytest

from bench.stats import CHECKPOINTS, Z95, judge, newcombe, wilson


def test_wilson_interval_stays_inside_0_and_1():
    lo, hi = wilson(0, 10, Z95)
    assert lo == pytest.approx(0.0, abs=1e-12) and 0.25 < hi < 0.35
    lo, hi = wilson(10, 10, Z95)
    assert 0.65 < lo < 0.75 and hi == pytest.approx(1.0)


def test_newcombe_matches_the_published_example():
    # Newcombe (1998), method 10, example (a): 56/70 vs 48/80
    diff, lo, hi = newcombe(56, 70, 48, 80, Z95)
    assert diff == pytest.approx(0.1857, abs=1e-4)
    assert lo == pytest.approx(0.0524, abs=1e-4)
    assert hi == pytest.approx(0.3339, abs=1e-4)


def test_the_lucky_choke_point_run_is_not_a_win():
    # 286 vs 262 of 576 reached Dlvl 6+; the repeat run showed it was noise
    assert judge(286, 576, 262, 576, 576).state == "open"


def test_a_big_effect_is_called_early():
    v = judge(330, 576, 262, 576, 576)
    assert v.state == "better" and v.lo > 0
    assert judge(262, 576, 330, 576, 576).state == "worse"


def test_no_difference_is_only_declared_at_the_last_checkpoint():
    assert judge(500, 1152, 500, 1152, CHECKPOINTS[-1]).state == "no measurable difference"
    assert judge(100, 192, 100, 192, 192).state == "open"


def test_verdict_reports_the_smallest_detectable_difference():
    v = judge(500, 1152, 500, 1152, 1152)
    assert 0.03 < v.detectable < 0.05
    assert v.as_dict() == {"state": v.state, "checkpoint": 1152, "diff": v.diff, "lo": v.lo,
                           "hi": v.hi, "detectable": v.detectable}


def test_empty_sides_are_rejected():
    with pytest.raises(ValueError):
        judge(0, 0, 5, 10, 192)
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_stats.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'bench.stats'`

- [ ] **Step 3: Implement `bench/stats.py`**

```python
"""Intervals for comparing rates, and the checkpoint verdicts of an experiment."""
import math
from dataclasses import asdict, dataclass

CHECKPOINTS = (192, 384, 576, 1152)
Z95 = 1.959963984540054
Z99 = 2.5758293035489004


def wilson(k, n, z):
    """Wilson score interval for k successes out of n."""
    p = k / n
    denom = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    return max(0.0, centre - half), min(1.0, centre + half)


def newcombe(k1, n1, k2, n2, z):
    """Difference p1 - p2 with Newcombe's hybrid score interval (method 10)."""
    p1, p2 = k1 / n1, k2 / n2
    l1, u1 = wilson(k1, n1, z)
    l2, u2 = wilson(k2, n2, z)
    diff = p1 - p2
    return (diff,
            diff - math.sqrt((p1 - l1) ** 2 + (u2 - p2) ** 2),
            diff + math.sqrt((u1 - p1) ** 2 + (p2 - l2) ** 2))


def z_for(checkpoint):
    """Stricter early: peeking at several checkpoints would otherwise produce false wins."""
    return Z95 if checkpoint == CHECKPOINTS[-1] else Z99


@dataclass(frozen=True)
class Verdict:
    state: str  # better | worse | no measurable difference | open
    checkpoint: int
    diff: float
    lo: float
    hi: float

    @property
    def detectable(self):
        """Half-width of the interval: smaller real differences could not be seen."""
        return (self.hi - self.lo) / 2

    def as_dict(self):
        return {**asdict(self), "detectable": self.detectable}


def judge(k_cand, n_cand, k_base, n_base, checkpoint):
    if n_cand == 0 or n_base == 0:
        raise ValueError("both sides need games")
    diff, lo, hi = newcombe(k_cand, n_cand, k_base, n_base, z_for(checkpoint))
    if lo > 0:
        state = "better"
    elif hi < 0:
        state = "worse"
    elif checkpoint == CHECKPOINTS[-1]:
        state = "no measurable difference"
    else:
        state = "open"
    return Verdict(state, checkpoint, diff, lo, hi)
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_stats.py`
Expected: 7 passed

- [ ] **Step 5: Commit**

```bash
git add bench/stats.py tests/test_bench_stats.py
git commit -m "feat(bench): Newcombe intervals and checkpoint verdicts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 3: Metrics, filters and reports

**Files:**
- Create: `bench/metrics.py`, `bench/filters.py`, `bench/report.py`, `tests/test_bench_metrics.py`

**Interfaces:**
- Consumes: `newcombe`, `Z95` from Task 2.
- Produces: `METRICS: dict[str, Metric]`, `Metric(name, description, kind, fn)` (`kind` is `"rate"` or `"median"`), `killer(game) -> str`, `evaluate(metric, games) -> dict` (rate: `{"n", "skipped", "hits", "rate"}`; median: `{"n", "skipped", "median"}`), `parse_where(where) -> Callable[[dict], bool]` (raises `ValueError` on a bad clause), `report.summary(games) -> dict` with keys `games, metrics, killers, depths, outcomes, crashes, unstuck`, `report.compare(candidate_games, baseline_games) -> list[dict]` rows `{"metric", "description", "kind", "candidate", "baseline"}` plus `diff, lo, hi` for rates.

- [ ] **Step 1: Write the failing tests**

`tests/test_bench_metrics.py`:

```python
import pytest

from bench.filters import parse_where
from bench.metrics import METRICS, evaluate, killer
from bench.report import compare, summary


def _g(depth=5, reason="DEATH: killed by a soldier ant, while fainted from lack of food",
       outcome="died on Dlvl 5", **extra):
    return {"max_depth": depth, "end_reason": reason, "outcome": outcome, "turns": 1000,
            "score": 500, "strategy": "pilgrim", "role": "val", **extra}


def test_killer_strips_the_article_and_the_circumstances():
    assert killer(_g()) == "soldier ant"
    assert killer(_g(reason="DEATH: killed by an Uruk-hai")) == "Uruk-hai"
    assert killer(_g(reason="ESCAPED: escaped the dungeon")) == ""


def test_rate_metrics():
    games = [_g(6), _g(10, reason="DEATH: killed by a wand"), _g(2, reason="exception: RuntimeError: x"),
             _g(3, reason="ESCAPED: escaped the dungeon", outcome="escaped")]
    assert evaluate(METRICS["dlvl6"], games)["hits"] == 2
    assert evaluate(METRICS["dlvl10"], games)["hits"] == 1
    assert evaluate(METRICS["ants"], games)["hits"] == 1
    assert evaluate(METRICS["rays"], games)["hits"] == 1
    assert evaluate(METRICS["crashed"], games)["hits"] == 1
    assert evaluate(METRICS["escaped"], games)["hits"] == 1
    assert evaluate(METRICS["starved"], games)["hits"] == 1
    assert evaluate(METRICS["dlvl6"], games)["rate"] == 0.5


def test_games_from_older_commits_without_a_field_are_skipped_not_counted():
    games = [_g(unsticks=2), _g(unsticks=0), _g()]  # the last game predates the field
    result = evaluate(METRICS["unstuck"], games)
    assert result == {"n": 2, "skipped": 1, "hits": 1, "rate": 0.5}


def test_median_metrics_and_empty_input():
    assert evaluate(METRICS["depth"], [_g(1), _g(5), _g(9)])["median"] == 5
    assert evaluate(METRICS["depth"], [])["median"] is None
    assert evaluate(METRICS["dlvl6"], [])["rate"] is None


def test_filters():
    games = [_g(3), _g(12, role="sam"), _g(7, reason="DEATH: killed by a giant bat")]
    pick = lambda where: [g["max_depth"] for g in games if parse_where(where)(g)]
    assert pick("max_depth>5") == [12, 7]
    assert pick("max_depth<5") == [3]
    assert pick("role=sam") == [12]
    assert pick("end_reason~BAT") == [7]
    assert pick("max_depth>5,end_reason~soldier") == [12]  # "giant bat" also contains "ant"
    assert pick("nosuchfield=1") == []
    assert pick("") == [3, 12, 7]
    with pytest.raises(ValueError):
        parse_where("max_depth>>5;drop")


def test_summary_and_compare():
    games = [_g(6), _g(2, reason="exception: RuntimeError: Cyclic Panic"), _g(6, unsticks=3)]
    s = summary(games)
    assert s["games"] == 3
    assert s["killers"][0] == ("soldier ant", 2)
    assert s["depths"] == {2: 1, 6: 2}
    assert s["outcomes"] == {"pilgrim": {"died": 3}}
    assert s["crashes"] == ["exception: RuntimeError: Cyclic Panic"]
    assert s["unstuck"][0]["unsticks"] == 3
    rows = {r["metric"]: r for r in compare(games, [_g(1), _g(1), _g(1)])}
    assert rows["dlvl6"]["diff"] > 0 and "lo" in rows["dlvl6"]
    assert "diff" not in rows["depth"]
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_metrics.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'bench.filters'`

- [ ] **Step 3: Implement `bench/metrics.py`**

```python
"""Per-game metrics the bench server compares. Adding one takes one line in METRICS.

A metric function gets one stored game (the GameResult JSON of whichever commit played it)
and returns a bool (rate) or a number (median). A game that lacks a field the function
needs (KeyError) is skipped for that metric only, so new metrics also work on old games."""
import statistics
from dataclasses import dataclass
from typing import Any, Callable

ANTS = ("soldier ant", "giant ant", "fire ant")
RAYS = ("wand", "magic missile", "bolt of", "death ray", "blast of")


def killer(game):
    """What killed the character ('soldier ant'), or '' when nothing did."""
    reason = game["end_reason"]
    if "killed by " not in reason:
        return ""
    name = reason.split("killed by ", 1)[1].split(",")[0].strip()
    for article in ("a ", "an ", "the "):
        if name.startswith(article):
            return name[len(article):]
    return name


@dataclass(frozen=True)
class Metric:
    name: str
    description: str
    kind: str  # "rate" or "median"
    fn: Callable[[dict], Any]


METRICS = {m.name: m for m in [
    Metric("dlvl6", "reached Dlvl 6+", "rate", lambda g: g["max_depth"] >= 6),
    Metric("dlvl10", "reached Dlvl 10+", "rate", lambda g: g["max_depth"] >= 10),
    Metric("escaped", "escaped the dungeon", "rate", lambda g: g["outcome"].startswith("escaped")),
    Metric("crashed", "bot crashed", "rate", lambda g: g["end_reason"].startswith("exception")),
    Metric("died", "died", "rate", lambda g: g["end_reason"].startswith("DEATH")),
    Metric("starved", "starved, or killed while fainted", "rate",
           lambda g: "starved" in g["end_reason"] or "fainted from lack of food" in g["end_reason"]),
    Metric("ants", "killed by an ant", "rate", lambda g: killer(g) in ANTS),
    Metric("rays", "killed by a wand or ray", "rate", lambda g: any(r in killer(g) for r in RAYS)),
    Metric("unstuck", "needed the unstick safety net", "rate", lambda g: g["unsticks"] > 0),
    Metric("depth", "max depth", "median", lambda g: g["max_depth"]),
    Metric("turns", "turns played", "median", lambda g: g["turns"]),
    Metric("score", "score", "median", lambda g: g["score"]),
]}


def evaluate(metric, games):
    values = []
    for game in games:
        try:
            values.append(metric.fn(game))
        except KeyError:
            pass
    skipped = len(games) - len(values)
    if metric.kind == "rate":
        hits = sum(bool(v) for v in values)
        return {"n": len(values), "skipped": skipped, "hits": hits,
                "rate": hits / len(values) if values else None}
    return {"n": len(values), "skipped": skipped,
            "median": statistics.median(values) if values else None}
```

- [ ] **Step 4: Implement `bench/filters.py`**

```python
"""Filters for games and reference games: 'max_depth>9,end_reason~ant'.

Clauses are joined by ','; each is field=value, field>value, field<value or field~substring
(case-insensitive). > and < compare numbers only. A record missing the field never matches."""
import re

_CLAUSE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*([=<>~])\s*([^=<>~]*?)\s*$")


def _number(text):
    try:
        return float(text)
    except ValueError:
        return None


def parse_where(where):
    if not where:
        return lambda record: True
    tests = []
    for clause in where.split(","):
        m = _CLAUSE.match(clause)
        if m is None:
            raise ValueError(f"bad filter clause {clause!r}; use field=value, field>n, field<n or field~text")
        tests.append(m.groups())

    def match(record):
        for field, op, raw in tests:
            if field not in record:
                return False
            value = record[field]
            if op == "~":
                if raw.lower() not in str(value).lower():
                    return False
            elif op == "=":
                want = _number(raw)
                if isinstance(value, (int, float)) and want is not None:
                    if float(value) != want:
                        return False
                elif str(value) != raw:
                    return False
            else:
                want = _number(raw)
                if want is None or not isinstance(value, (int, float)):
                    return False
                if (op == ">" and not value > want) or (op == "<" and not value < want):
                    return False
        return True

    return match
```

- [ ] **Step 5: Implement `bench/report.py`**

```python
"""Summaries of stored games: the dashboard and the A/B table of an experiment."""
from collections import Counter, defaultdict

from .metrics import METRICS, evaluate, killer
from .stats import Z95, newcombe


def summary(games):
    outcomes = defaultdict(Counter)
    for g in games:
        outcomes[g.get("strategy", "?")][g.get("outcome", "?").split(" on Dlvl")[0]] += 1
    stuck = sorted((g for g in games if g.get("unsticks", 0) > 0), key=lambda g: -g["unsticks"])
    return {
        "games": len(games),
        "metrics": {name: evaluate(m, games) for name, m in METRICS.items()},
        "killers": Counter(k for k in map(killer, games) if k).most_common(15),
        "depths": dict(sorted(Counter(g["max_depth"] for g in games).items())),
        "outcomes": {s: dict(c) for s, c in sorted(outcomes.items())},
        "crashes": [g["end_reason"] for g in games if g["end_reason"].startswith("exception")][-20:],
        "unstuck": [{k: g.get(k) for k in ("role", "max_depth", "turns", "unsticks", "end_reason")}
                    for g in stuck[:10]],
    }


def compare(candidate, baseline):
    """Every metric side by side; rates get a 95% interval (information only, not a verdict)."""
    rows = []
    for name, m in METRICS.items():
        c, b = evaluate(m, candidate), evaluate(m, baseline)
        row = {"metric": name, "description": m.description, "kind": m.kind, "candidate": c, "baseline": b}
        if m.kind == "rate" and c["n"] and b["n"]:
            row["diff"], row["lo"], row["hi"] = newcombe(c["hits"], c["n"], b["hits"], b["n"], Z95)
        rows.append(row)
    return rows
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_metrics.py`
Expected: 6 passed

- [ ] **Step 7: Commit**

```bash
git add bench/metrics.py bench/filters.py bench/report.py tests/test_bench_metrics.py
git commit -m "feat(bench): metric registry, filters and summaries

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 4: Git refs and worktrees

**Files:**
- Create: `bench/gitrefs.py`, `tests/test_bench_gitrefs.py`

**Interfaces:**
- Produces: `resolve(repo, ref) -> (sha, subject)` (raises `ValueError` with git's message), `ensure_worktree(repo, sha, root) -> Path` (creates `root/<sha>` once, touches it on every use), `prune(repo, root, max_age_days=14, now=None) -> list[str]` (removed SHAs), `history(repo, ref, limit=200) -> list[str]` (newest first).

- [ ] **Step 1: Write the failing tests**

`tests/test_bench_gitrefs.py`:

```python
import subprocess
import time

import pytest

from bench import gitrefs


def _git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    _git(repo, "config", "user.email", "t@example.com")
    _git(repo, "config", "user.name", "t")
    for text in ("one", "two"):
        (repo / "f.txt").write_text(text)
        _git(repo, "add", "f.txt")
        _git(repo, "commit", "-q", "-m", f"commit {text}")
    return repo


def test_resolve_gives_full_sha_and_subject(repo):
    sha, subject = gitrefs.resolve(repo, "main")
    assert len(sha) == 40 and subject == "commit two"
    assert gitrefs.resolve(repo, sha[:8])[0] == sha
    with pytest.raises(ValueError):
        gitrefs.resolve(repo, "no-such-branch")


def test_history_is_newest_first(repo):
    shas = gitrefs.history(repo, "main")
    assert len(shas) == 2 and shas[0] == gitrefs.resolve(repo, "main")[0]


def test_worktree_is_created_once_at_the_commit(repo, tmp_path):
    old = gitrefs.resolve(repo, "main~1")[0]
    path = gitrefs.ensure_worktree(repo, old, tmp_path / "wt")
    assert (path / "f.txt").read_text() == "one"
    assert gitrefs.ensure_worktree(repo, old, tmp_path / "wt") == path


def test_prune_removes_only_old_worktrees(repo, tmp_path):
    a = gitrefs.resolve(repo, "main~1")[0]
    b = gitrefs.resolve(repo, "main")[0]
    gitrefs.ensure_worktree(repo, a, tmp_path / "wt")
    gitrefs.ensure_worktree(repo, b, tmp_path / "wt")
    assert gitrefs.prune(repo, tmp_path / "wt", now=time.time()) == []
    assert sorted(gitrefs.prune(repo, tmp_path / "wt", now=time.time() + 15 * 86400)) == sorted([a, b])
    assert not (tmp_path / "wt" / a).exists()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_gitrefs.py`
Expected: FAIL — `ImportError: cannot import name 'gitrefs'`

- [ ] **Step 3: Implement `bench/gitrefs.py`**

```python
"""Resolve refs to commits and keep one git worktree per benchmarked commit."""
import os
import subprocess
import time
from pathlib import Path


def _git(repo, *args):
    r = subprocess.run(["git", "-C", str(repo), *args], capture_output=True, text=True)
    if r.returncode != 0:
        raise ValueError(r.stderr.strip() or f"git {' '.join(args)} failed")
    return r.stdout.strip()


def resolve(repo, ref):
    """(full sha, subject line) of a branch, tag or sha."""
    sha = _git(repo, "rev-parse", "--verify", f"{ref}^{{commit}}")
    return sha, _git(repo, "log", "-1", "--format=%s", sha)


def history(repo, ref, limit=200):
    return _git(repo, "rev-list", f"--max-count={limit}", ref).split()


def ensure_worktree(repo, sha, root):
    path = Path(root) / sha
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        _git(repo, "worktree", "add", "--detach", str(path), sha)
    os.utime(path)  # last use, for prune()
    return path


def prune(repo, root, max_age_days=14, now=None):
    now = time.time() if now is None else now
    removed = []
    root = Path(root)
    if root.exists():
        for path in sorted(root.iterdir()):
            if now - path.stat().st_mtime > max_age_days * 86400:
                _git(repo, "worktree", "remove", "--force", str(path))
                removed.append(path.name)
    _git(repo, "worktree", "prune")
    return removed
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_gitrefs.py`
Expected: 4 passed

- [ ] **Step 5: Commit**

```bash
git add bench/gitrefs.py tests/test_bench_gitrefs.py
git commit -m "feat(bench): resolve refs and keep a worktree per commit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 5: Worker script and process worker

**Files:**
- Create: `bench/worker.py`, `bench/runner.py`, `tests/test_bench_runner.py`

**Interfaces:**
- Produces: `bench/worker.py` (run as a script: reads `play` lines on stdin, writes one JSON result line per game to the original stdout; everything the game prints goes to stderr). `ProcessWorker(python, worktree, log_path, nice=10)` with `play()`, `results() -> list[dict]`, `alive() -> bool`, `close()`. `WORKER_SCRIPT` path constant.

- [ ] **Step 1: Write the failing tests**

`tests/test_bench_runner.py` (uses a fake `nethack_screensaver.game` so no real game runs):

```python
import sys
import time

from bench.runner import ProcessWorker

FAKE_GAME = '''
from dataclasses import dataclass

@dataclass
class GameResult:
    role: str
    max_depth: int
    end_reason: str

_n = [0]

def run_game(watchdog_seconds=None):
    _n[0] += 1
    print("Warning: NetHack asked for env variable ROGUEOPTS")  # noise on stdout
    if _n[0] == 3:
        raise SystemExit(1)  # the third game kills the process
    return GameResult("val", _n[0], "DEATH: killed by a newt")
'''


def _fake_worktree(tmp_path):
    pkg = tmp_path / "wt" / "nethack_screensaver"
    pkg.mkdir(parents=True)
    (pkg / "__init__.py").write_text("")
    (pkg / "game.py").write_text(FAKE_GAME)
    return tmp_path / "wt"


def _wait_for(predicate, timeout=20):
    end = time.time() + timeout
    while time.time() < end:
        value = predicate()
        if value:
            return value
        time.sleep(0.05)
    raise AssertionError("timed out")


def test_worker_plays_on_request_and_keeps_noise_out_of_results(tmp_path):
    w = ProcessWorker(sys.executable, _fake_worktree(tmp_path), tmp_path / "worker.log", nice=0)
    try:
        w.play()
        w.play()
        got = []
        _wait_for(lambda: got.extend(w.results()) or len(got) == 2)
        assert [r["max_depth"] for r in got] == [1, 2]
        assert w.alive()
    finally:
        w.close()
    assert "ROGUEOPTS" in (tmp_path / "worker.log").read_text()


def test_worker_death_is_visible(tmp_path):
    w = ProcessWorker(sys.executable, _fake_worktree(tmp_path), tmp_path / "worker.log", nice=0)
    try:
        for _ in range(3):
            w.play()
        _wait_for(lambda: not w.alive())
        assert [r["max_depth"] for r in w.results()] == [1, 2]
    finally:
        w.close()
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_runner.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'bench.runner'`

- [ ] **Step 3: Implement `bench/worker.py`**

```python
"""Plays one NetHack game per 'play' line on stdin and prints its result as one JSON line.

The bench server starts this script with PYTHONPATH pointing at a commit's worktree, so the
game code comes from that commit. It must not import the bench package: old commits do not
have it. Anything the game prints goes to stderr so stdout carries only results."""
import json
import os
import sys
from dataclasses import asdict


def main():
    results = os.fdopen(os.dup(sys.stdout.fileno()), "w")
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())  # C code printing to fd 1 lands in the log
    sys.stdout = sys.stderr
    from nethack_screensaver.game import run_game

    for line in sys.stdin:
        if line.strip() != "play":
            continue
        result = run_game(watchdog_seconds=120)
        results.write(json.dumps(asdict(result)) + "\n")
        results.flush()


if __name__ == "__main__":
    main()
```

- [ ] **Step 4: Implement `bench/runner.py`**

```python
"""Worker processes: one per slot, bound to one commit's worktree."""
import json
import os
import queue
import subprocess
import threading
from pathlib import Path

WORKER_SCRIPT = Path(__file__).with_name("worker.py")


class ProcessWorker:
    def __init__(self, python, worktree, log_path, nice=10):
        self._log = open(log_path, "a")
        env = {**os.environ, "PYTHONPATH": str(worktree)}
        cmd = [str(python), str(WORKER_SCRIPT)]
        if nice:
            cmd = ["nice", "-n", str(nice), *cmd]
        self._proc = subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                      stderr=self._log, text=True, env=env, cwd=worktree)
        self._out = queue.Queue()
        self._reader = threading.Thread(target=self._read, daemon=True)
        self._reader.start()

    def _read(self):
        for line in self._proc.stdout:
            line = line.strip()
            if not line:
                continue
            try:
                self._out.put(json.loads(line))
            except json.JSONDecodeError:
                self._log.write(f"bench: not a result line: {line[:200]}\n")

    def play(self):
        self._proc.stdin.write("play\n")
        self._proc.stdin.flush()

    def results(self):
        out = []
        while True:
            try:
                out.append(self._out.get_nowait())
            except queue.Empty:
                return out

    def alive(self):
        if self._proc.poll() is None:
            return True
        self._reader.join(timeout=2)  # collect a result printed just before dying
        return False

    def close(self):
        if self._proc.poll() is None:
            self._proc.kill()
        self._proc.wait()
        self._reader.join(timeout=2)
        self._log.close()
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_runner.py`
Expected: 2 passed

- [ ] **Step 6: Commit**

```bash
git add bench/worker.py bench/runner.py tests/test_bench_runner.py
git commit -m "feat(bench): worker subprocess that plays games of one commit

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 6: Scheduler

**Files:**
- Create: `bench/scheduler.py`, `tests/bench_fakes.py`, `tests/test_bench_scheduler.py`

**Interfaces:**
- Consumes: `Store` (Task 1), `CHECKPOINTS`, `judge` (Task 2), `METRICS`, `evaluate` (Task 3); a `spawn(sha)` callable returning an object with `play()`, `results()`, `alive()`, `close()` (Task 5's `ProcessWorker` fits).
- Produces: `Scheduler(store, spawn, slots=11)` with `submit(kind, spec) -> int`, `stop(job_id=None) -> bool`, `tick()`, `status() -> dict`, `shutdown()`, attributes `job` and `error`. Job specs: baseline `{"ref", "sha", "subject", "games"}`; experiment `{"candidate", "candidate_ref", "candidate_subject", "baseline", "baseline_ref", "baseline_subject", "metric"}` (SHAs under `candidate`/`baseline`). Experiment result: `{"checkpoints": [verdict dicts], "verdict": verdict dict}`. `status()` → `{"job": {"id", "kind", "spec", "result", "progress", "eta_seconds"} | None, "busy_workers", "slots", "games_per_minute", "error"}`; progress is `{"games", "target"}` (baseline) or `{"baseline", "candidate", "checkpoint"}` (experiment).

- [ ] **Step 1: Write the failing tests**

`tests/bench_fakes.py` (shared by the scheduler, server and MCP tests; `tests/` has no
`__init__.py`, so pytest puts `tests/` on `sys.path` and the tests import it as `bench_fakes`):

```python
"""Test doubles for the bench server: a worker that plays instantly."""


class FakeWorker:
    """Plays instantly: each play() makes one result from make(sha, index)."""

    def __init__(self, sha, make, log):
        self.sha, self.make, self.log = sha, make, log
        self.pending, self.dead, self.closed = [], False, False

    def play(self):
        if self.dead:
            raise BrokenPipeError
        self.log.append(self.sha)
        self.pending.append(self.make(self.sha, len(self.log)))

    def results(self):
        out, self.pending = self.pending, []
        return out

    def alive(self):
        return not self.dead

    def close(self):
        self.closed = True


def game(depth):
    return {"max_depth": depth, "end_reason": "DEATH: killed by a newt", "outcome": "died"}
```

`tests/test_bench_scheduler.py`:

```python
from bench_fakes import FakeWorker, game as _game
from bench.scheduler import Scheduler
from bench.store import Store


def _scheduler(tmp_path, make, slots=4):
    store = Store(tmp_path / "r.db")
    played, workers = [], []

    def spawn(sha):
        workers.append(FakeWorker(sha, make, played))
        return workers[-1]

    return Scheduler(store, spawn, slots=slots), store, played, workers


def _run(scheduler, ticks=2000):
    for _ in range(ticks):
        scheduler.tick()
        if scheduler.job is None and scheduler.store.next_queued() is None:
            return
    raise AssertionError("job did not finish")


def _experiment(scheduler, metric="dlvl6"):
    return scheduler.submit("experiment", {"candidate": "cand", "candidate_ref": "branch",
                                           "baseline": "base", "baseline_ref": "main", "metric": metric})


def test_baseline_tops_up_stored_games(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3))
    for _ in range(5):
        store.add_game("base", None, _game(3))
    job = s.submit("baseline", {"ref": "main", "sha": "base", "games": 8})
    _run(s)
    assert len(played) == 3 and store.count("base") == 8
    assert store.job(job)["state"] == "done" and store.job(job)["result"] == {"games": 8}


def test_clear_win_is_decided_at_the_first_checkpoint(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    job = _experiment(s)
    _run(s)
    result = store.job(job)["result"]
    assert result["verdict"]["state"] == "better" and result["verdict"]["checkpoint"] == 192
    assert store.count("cand") == 192 and store.count("base") == 192


def test_stored_baseline_games_are_reused(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if sha == "cand" else 1))
    for _ in range(192):
        store.add_game("base", None, _game(1))
    _experiment(s)
    _run(s)
    assert set(played) == {"cand"} and len(played) == 192


def test_no_difference_runs_to_the_last_checkpoint(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(10 if i % 2 else 1), slots=8)
    job = _experiment(s)
    _run(s, ticks=5000)
    result = store.job(job)["result"]
    assert [c["checkpoint"] for c in result["checkpoints"]] == [192, 384, 576, 1152]
    assert result["verdict"]["state"] == "no measurable difference"
    assert store.count("cand") == 1152 and store.count("base") == 1152


def test_dead_worker_is_replaced_and_the_game_replayed(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    s.submit("baseline", {"ref": "main", "sha": "base", "games": 3})
    s.tick()  # starts the job and the first game
    workers[0].pending.clear()
    workers[0].dead = True  # dies mid-game
    _run(s)
    assert store.count("base") == 3 and len(workers) == 2 and workers[0].closed


def test_three_deaths_in_a_row_fail_the_job(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=1)
    job = s.submit("baseline", {"ref": "main", "sha": "base", "games": 3})
    for _ in range(10):
        s.tick()
        if workers:
            workers[-1].pending.clear()
            workers[-1].dead = True
    assert store.job(job)["state"] == "failed"
    assert "died 3 times" in store.job(job)["result"]["error"]
    assert s.job is None


def test_stop_keeps_stored_games_and_queued_jobs_run_next(tmp_path):
    s, store, played, workers = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    first = s.submit("baseline", {"ref": "main", "sha": "base", "games": 100})
    second = s.submit("baseline", {"ref": "x", "sha": "other", "games": 2})
    for _ in range(3):
        s.tick()
    stored = store.count("base")
    assert stored > 0
    assert s.stop() is True
    assert store.job(first)["state"] == "stopped" and all(w.closed for w in workers)
    _run(s)
    assert store.count("base") == stored and store.job(second)["state"] == "done"


def test_status_reports_progress(tmp_path):
    s, store, played, _ = _scheduler(tmp_path, lambda sha, i: _game(3), slots=2)
    assert s.status()["job"] is None
    s.submit("baseline", {"ref": "main", "sha": "base", "games": 10})
    for _ in range(3):
        s.tick()
    st = s.status()
    assert st["job"]["progress"]["target"] == 10 and st["slots"] == 2
    assert 0 < st["job"]["progress"]["games"] <= 10
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_scheduler.py`
Expected: FAIL — `ModuleNotFoundError: No module named 'bench.scheduler'`

- [ ] **Step 3: Implement `bench/scheduler.py`**

```python
"""Hands out one game at a time to worker slots for the active job and judges experiments."""
import time
from collections import Counter, deque

from .metrics import METRICS, evaluate
from .stats import CHECKPOINTS, judge

MAX_DEATHS_IN_ROW = 3


class _Slot:
    def __init__(self):
        self.sha = None
        self.worker = None
        self.busy = False
        self.job_id = None


class Scheduler:
    def __init__(self, store, spawn, slots=11):
        self.store = store
        self.spawn = spawn  # spawn(sha) -> worker with play(), results(), alive(), close()
        self._slots = [_Slot() for _ in range(slots)]
        self._inflight = Counter()
        self._deaths_in_row = 0
        self._finished = deque(maxlen=500)  # finish times, for games per minute
        self.job = None
        self.error = None

    def submit(self, kind, spec):
        return self.store.add_job(kind, spec)

    def stop(self, job_id=None):
        """Stop the active job, or a queued one by id. Stored games stay."""
        if self.job is not None and job_id in (None, self.job["id"]):
            self._end("stopped", self.job["result"])
            return True
        if job_id is not None:
            job = self.store.job(job_id)
            if job is not None and job["state"] == "queued":
                self.store.set_job(job_id, "stopped")
                return True
        return False

    def tick(self):
        self._collect()
        if self.job is None:
            job = self.store.next_queued()
            if job is None:
                return
            job["result"] = {"checkpoints": []} if job["kind"] == "experiment" else {}
            job["checkpoint"] = 0
            self.store.set_job(job["id"], "running", job["result"])
            self.job, self.error, self._deaths_in_row = job, None, 0
        if self._judge():
            return
        self._dispatch()

    def shutdown(self):
        for slot in self._slots:
            if slot.worker is not None:
                slot.worker.close()
            slot.worker, slot.busy, slot.sha = None, False, None

    # internals

    def _collect(self):
        for slot in self._slots:
            if slot.worker is None:
                continue
            dead = not slot.worker.alive()
            for result in slot.worker.results():
                self.store.add_game(slot.sha, slot.job_id, result)
                self._finished.append(time.time())
                self._inflight[slot.sha] -= 1
                slot.busy = False
                self._deaths_in_row = 0
            if dead:
                self._worker_died(slot, "worker process died")

    def _worker_died(self, slot, why):
        if slot.busy:
            self._inflight[slot.sha] -= 1
        if slot.worker is not None:
            slot.worker.close()
        slot.worker, slot.busy, slot.sha = None, False, None
        self._deaths_in_row += 1
        if self._deaths_in_row >= MAX_DEATHS_IN_ROW and self.job is not None:
            self.error = f"{why}: worker died {MAX_DEATHS_IN_ROW} times in a row; see worker.log"
            self._end("failed", {**self.job["result"], "error": self.error})

    def _end(self, state, result):
        self.store.set_job(self.job["id"], state, result)
        self.job = None
        for slot in self._slots:
            if slot.busy:
                self._inflight[slot.sha] -= 1  # a game in progress is dropped
        self.shutdown()

    def _targets(self):
        spec = self.job["spec"]
        if self.job["kind"] == "baseline":
            return [(spec["sha"], spec["games"])]
        need = CHECKPOINTS[self.job["checkpoint"]]
        return [(spec["baseline"], need), (spec["candidate"], need)]  # baseline first

    def _judge(self):
        """True when the active job just ended."""
        spec = self.job["spec"]
        if self.job["kind"] == "baseline":
            stored = self.store.count(spec["sha"])
            if stored >= spec["games"]:
                self._end("done", {"games": stored})
                return True
            return False
        need = CHECKPOINTS[self.job["checkpoint"]]
        if self.store.count(spec["candidate"]) < need or self.store.count(spec["baseline"]) < need:
            return False
        metric = METRICS[spec["metric"]]
        c = evaluate(metric, self.store.games(spec["candidate"], limit=need))
        b = evaluate(metric, self.store.games(spec["baseline"], limit=need))
        verdict = judge(c["hits"], c["n"], b["hits"], b["n"], need).as_dict()
        result = self.job["result"]
        result["checkpoints"].append(verdict)
        result["verdict"] = verdict
        if verdict["state"] != "open":
            self._end("done", result)
            return True
        self.store.set_job(self.job["id"], "running", result)
        self.job["checkpoint"] += 1
        return False

    def _wanted_sha(self):
        for sha, target in self._targets():
            if self.store.count(sha) + self._inflight[sha] < target:
                return sha
        return None

    def _dispatch(self):
        for slot in self._slots:
            if self.job is None or slot.busy:
                continue
            sha = self._wanted_sha()
            if sha is None:
                return
            try:
                if slot.sha != sha:
                    if slot.worker is not None:
                        slot.worker.close()
                    slot.worker, slot.sha = None, None
                    slot.worker = self.spawn(sha)
                    slot.sha = sha
                slot.worker.play()
            except (OSError, ValueError) as e:
                self._worker_died(slot, f"cannot start a game: {e!r}")
                return
            slot.busy, slot.job_id = True, self.job["id"]
            self._inflight[sha] += 1

    def status(self):
        now = time.time()
        recent = [t for t in self._finished if now - t < 300]
        per_minute = len(recent) / ((now - recent[0]) / 60) if len(recent) >= 2 and now > recent[0] else 0.0
        job = None
        if self.job is not None:
            spec = self.job["spec"]
            if self.job["kind"] == "baseline":
                done = self.store.count(spec["sha"])
                progress = {"games": done, "target": spec["games"]}
                left = max(spec["games"] - done, 0)
            else:
                need = CHECKPOINTS[self.job["checkpoint"]]
                b = min(self.store.count(spec["baseline"]), need)
                c = min(self.store.count(spec["candidate"]), need)
                progress = {"baseline": b, "candidate": c, "checkpoint": need}
                left = 2 * need - b - c
            job = {**{k: self.job[k] for k in ("id", "kind", "spec", "result")}, "progress": progress,
                   "eta_seconds": left / per_minute * 60 if per_minute else None}
        return {"job": job, "busy_workers": sum(s.busy for s in self._slots), "slots": len(self._slots),
                "games_per_minute": per_minute, "error": self.error}
```

- [ ] **Step 4: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_scheduler.py`
Expected: 8 passed

- [ ] **Step 5: Commit**

```bash
git add bench/scheduler.py tests/bench_fakes.py tests/test_bench_scheduler.py
git commit -m "feat(bench): scheduler with checkpoint verdicts and worker restarts

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 7: App, HTTP API and CLI

**Files:**
- Create: `bench/server.py`, `bench/cli.py`, `bench/reference.py` (stub), `bench/static/index.html` (placeholder), `tests/conftest.py`, `tests/test_bench_server.py`

**Interfaces:**
- Consumes: Tasks 1–6. `importers` and `reference` are imported lazily inside the methods that use them (they arrive in Task 10).
- Produces: `App(store, scheduler, repo, cache_dir)` with `status()`, `start_baseline(ref="main", games=576)`, `start_experiment(candidate, baseline="main", metric="dlvl6")`, `stop(job_id=None)`, `job(job_id)`, `results(ref="main", metric=None)`, `games(ref="main", where=None, limit=50)`, `experiments()`, `dashboard(ref="main")`, `reference_summary()`, `reference_games(where=None, limit=50)`, `start_import(kind, url=None, limit=500)`, `loop(stop_event, interval=0.2)`. `serve(app, port=8765, host="127.0.0.1") -> (httpd, stop_event)` (raises `SystemExit` with a message when the port is taken). `cli.build_app(workers=11, data_dir=DATA, cache_dir=CACHE) -> App`. `cli.main(argv=None) -> int`. HTTP routes as in the spec: `GET /`, `GET /api/status|results|games|experiments|dashboard|metrics|reference/summary|reference/games|jobs/<id>`, `POST /api/jobs`, `POST /api/import`, `DELETE /api/jobs` (active) and `DELETE /api/jobs/<id>`. Errors: 400 `{"error"}` for bad input, 404 for unknown jobs/routes.

- [ ] **Step 1: Write the failing tests**

`tests/conftest.py` (fixtures shared by the server and MCP tests):

```python
import subprocess
import threading

import pytest

from bench_fakes import FakeWorker, game
from bench.scheduler import Scheduler
from bench.server import App, serve
from bench.store import Store


def git(repo, *args):
    subprocess.run(["git", "-C", str(repo), *args], check=True, capture_output=True)


@pytest.fixture
def bench_repo(tmp_path):
    repo = tmp_path / "repo"
    repo.mkdir()
    git(repo, "init", "-q", "-b", "main")
    git(repo, "config", "user.email", "t@example.com")
    git(repo, "config", "user.name", "t")
    for name in ("one", "two"):
        (repo / "f.txt").write_text(name)
        git(repo, "add", "f.txt")
        git(repo, "commit", "-q", "-m", name)
    git(repo, "branch", "feature", "HEAD~1")
    return repo


@pytest.fixture
def bench_app(tmp_path, bench_repo):
    store = Store(tmp_path / "r.db")
    played = []
    sched = Scheduler(store, lambda sha: FakeWorker(sha, lambda s, i: game(4), played), slots=16)
    return App(store, sched, bench_repo, tmp_path / "cache")


@pytest.fixture
def bench_url(bench_app):
    httpd, stop = serve(bench_app, port=0)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    yield f"http://127.0.0.1:{httpd.server_address[1]}"
    stop.set()
    httpd.shutdown()
    httpd.server_close()


def run_until_idle(app, ticks=3000):
    """Tick the scheduler under the app lock (the server loop ticks too) until no job is left."""
    for _ in range(ticks):
        with app.lock:
            app.scheduler.tick()
            if app.scheduler.job is None and app.store.next_queued() is None:
                return
    raise AssertionError("job did not finish")
```

`tests/test_bench_server.py`:

```python
import json
import socket
import subprocess
from urllib.error import HTTPError
from urllib.request import Request, urlopen

import pytest

from bench_fakes import game as _game
from conftest import git, run_until_idle
from bench import cli
from bench.server import serve
from bench.store import Store


def _req(url, method="GET", body=None):
    data = None if body is None else json.dumps(body).encode()
    req = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=10) as r:
            return r.status, json.loads(r.read())
    except HTTPError as e:
        return e.code, json.loads(e.read())


def test_baseline_job_stores_the_sha_resolved_at_start(bench_app, bench_repo):
    job_id = bench_app.start_baseline("main", games=3)["job_id"]
    sha = bench_app.job(job_id)["spec"]["sha"]
    (bench_repo / "f.txt").write_text("three")
    git(bench_repo, "commit", "-qam", "three")  # main moves on while the job waits
    assert bench_app.job(job_id)["spec"]["sha"] == sha != bench_app._sha("main")[0]


def test_bad_requests_are_explained(bench_app):
    with pytest.raises(ValueError):
        bench_app.start_baseline("no-such-ref")
    with pytest.raises(ValueError, match="same commit"):
        bench_app.start_experiment("main", "main")
    with pytest.raises(ValueError, match="metric"):
        bench_app.start_experiment("feature", "main", metric="depth")
    with pytest.raises(LookupError):
        bench_app.job(999)


def test_api_runs_an_experiment_end_to_end(bench_app, bench_url):
    http = bench_url
    status, body = _req(http + "/api/jobs", "POST",
                        {"kind": "experiment", "candidate": "feature", "baseline": "main"})
    assert status == 200
    job_id = body["job_id"]
    run_until_idle(bench_app)
    status, job = _req(f"{http}/api/jobs/{job_id}")
    assert status == 200 and job["state"] == "done"
    assert job["result"]["verdict"]["state"] == "no measurable difference"
    assert {r["metric"] for r in job["table"]} >= {"dlvl6", "depth"}
    assert _req(http + "/api/experiments")[1][0]["id"] == job_id
    status, dash = _req(http + "/api/dashboard")
    assert dash["games"] == 1152
    status, games = _req(http + "/api/games?ref=feature&where=max_depth>3&limit=2")
    assert games["matches"] == 1152 and len(games["games"]) == 2
    assert _req(http + "/api/results?ref=main&metric=dlvl6")[1]["hits"] == 0


def test_api_errors(bench_url):
    http = bench_url
    assert _req(http + "/api/jobs", "POST", {"kind": "nonsense"})[0] == 400
    assert _req(http + "/api/jobs/12345")[0] == 404
    assert _req(http + "/api/jobs/abc")[0] == 400
    assert _req(http + "/api/games?where=max_depth>>1")[0] == 400
    assert _req(http + "/api/nothing")[0] == 404
    assert _req(http + "/api/jobs", "DELETE")[1] == {"stopped": False}


def test_page_is_served(bench_url):
    with urlopen(bench_url + "/", timeout=10) as r:
        assert r.headers["Content-Type"].startswith("text/html")
        assert b"<title>Screens Bench</title>" in r.read()


def test_second_server_on_the_same_port_exits_with_a_message(bench_app):
    blocker = socket.socket()
    blocker.bind(("127.0.0.1", 0))
    blocker.listen()
    try:
        with pytest.raises(SystemExit, match="already running"):
            serve(bench_app, port=blocker.getsockname()[1])
    finally:
        blocker.close()


def test_build_app_marks_jobs_of_a_stopped_server_interrupted(tmp_path):
    store = Store(tmp_path / "data" / "results.db")
    job = store.add_job("baseline", {"sha": "x", "games": 5})
    store.set_job(job, "running", {})
    del store
    app = cli.build_app(workers=1, data_dir=tmp_path / "data", cache_dir=tmp_path / "cache")
    assert app.store.job(job)["state"] == "interrupted"


def test_import_results_file(tmp_path, bench_repo, monkeypatch):
    repo = bench_repo
    monkeypatch.setattr(cli, "REPO", repo)
    results = tmp_path / "old.jsonl"
    results.write_text("\n".join(json.dumps(_game(d)) for d in (3, 7)) + "\n")
    assert cli.main(["--data", str(tmp_path / "d"), "import", "results", str(results), "--ref", "main"]) == 0
    sha = subprocess.run(["git", "-C", str(repo), "rev-parse", "main"], capture_output=True, text=True).stdout.strip()
    assert Store(tmp_path / "d" / "results.db").count(sha) == 2
```

- [ ] **Step 2: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_server.py`
Expected: FAIL — `ImportError: cannot import name 'cli' from 'bench'`

- [ ] **Step 3: Implement `bench/server.py`**

```python
"""Bench server: application logic, JSON API, status page and the scheduler loop."""
import errno
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from . import gitrefs, report
from .filters import parse_where
from .metrics import METRICS, evaluate

STATIC = Path(__file__).with_name("static")


class App:
    def __init__(self, store, scheduler, repo, cache_dir):
        self.store, self.scheduler = store, scheduler
        self.repo, self.cache_dir = Path(repo), Path(cache_dir)
        self.lock = threading.RLock()
        self.imports = {"running": False, "last": None}

    def _sha(self, ref):
        return gitrefs.resolve(self.repo, ref)

    def status(self):
        with self.lock:
            return {**self.scheduler.status(), "import": dict(self.imports)}

    def start_baseline(self, ref="main", games=576):
        games = int(games)
        if games < 1:
            raise ValueError("games must be at least 1")
        sha, subject = self._sha(ref)
        with self.lock:
            return {"job_id": self.scheduler.submit(
                "baseline", {"ref": ref, "sha": sha, "subject": subject, "games": games})}

    def start_experiment(self, candidate, baseline="main", metric="dlvl6"):
        rates = [n for n, m in METRICS.items() if m.kind == "rate"]
        if metric not in rates:
            raise ValueError(f"metric must be one of {rates}")
        cand, cand_subject = self._sha(candidate)
        base, base_subject = self._sha(baseline)
        if cand == base:
            raise ValueError(f"{candidate} and {baseline} are the same commit {cand[:10]}")
        spec = {"candidate": cand, "candidate_ref": candidate, "candidate_subject": cand_subject,
                "baseline": base, "baseline_ref": baseline, "baseline_subject": base_subject,
                "metric": metric}
        with self.lock:
            return {"job_id": self.scheduler.submit("experiment", spec)}

    def stop(self, job_id=None):
        with self.lock:
            return {"stopped": self.scheduler.stop(job_id)}

    def job(self, job_id):
        job = self.store.job(int(job_id))
        if job is None:
            raise LookupError(f"no job {job_id}")
        if job["kind"] == "experiment":
            spec = job["spec"]
            n = min(self.store.count(spec["candidate"]), self.store.count(spec["baseline"]))
            job["table"] = report.compare(self.store.games(spec["candidate"], limit=n),
                                          self.store.games(spec["baseline"], limit=n))
            job["games_per_side"] = n
        return job

    def results(self, ref="main", metric=None):
        sha, subject = self._sha(ref)
        games = self.store.games(sha)
        if metric is not None:
            if metric not in METRICS:
                raise ValueError(f"unknown metric {metric!r}; known: {sorted(METRICS)}")
            return {"sha": sha, "metric": metric, **evaluate(METRICS[metric], games)}
        return {"sha": sha, "subject": subject, **report.summary(games)}

    def games(self, ref="main", where=None, limit=50):
        sha, _ = self._sha(ref)
        match = parse_where(where)
        hits = [g for g in self.store.games(sha) if match(g)]
        return {"sha": sha, "matches": len(hits), "games": hits[:int(limit)]}

    def experiments(self):
        return self.store.jobs("experiment")

    def dashboard(self, ref="main"):
        for sha in gitrefs.history(self.repo, ref):
            if self.store.count(sha):
                return {"sha": sha, "subject": self._sha(sha)[1], **report.summary(self.store.games(sha))}
        return {"sha": None, "games": 0}

    def reference_summary(self):
        from . import reference
        return reference.summary(self.store.references())

    def reference_games(self, where=None, limit=50):
        match = parse_where(where)
        hits = [r["record"] for r in self.store.references() if match(r["record"])]
        return {"matches": len(hits), "games": hits[:int(limit)]}

    def start_import(self, kind, url=None, limit=500):
        from . import importers
        if kind not in ("xlog", "dumplogs"):
            raise ValueError("kind must be xlog or dumplogs")
        if kind == "xlog" and not url:
            raise ValueError("an xlog import needs a url")
        with self.lock:
            if self.imports["running"]:
                raise ValueError("an import is already running")
            self.imports["running"] = True

        def run():
            try:
                if kind == "xlog":
                    out = importers.import_xlog(self.store, url)
                else:
                    out = importers.import_dumplogs(self.store, self.cache_dir, limit=int(limit))
                self.imports["last"] = {"kind": kind, **out}
            except Exception as e:  # shown on the page; the server keeps running
                self.imports["last"] = {"kind": kind, "error": str(e)}
            finally:
                self.imports["running"] = False

        threading.Thread(target=run, daemon=True).start()
        return {"started": kind}

    def loop(self, stop_event, interval=0.2):
        while not stop_event.is_set():
            with self.lock:
                try:
                    self.scheduler.tick()
                except Exception as e:  # keep serving; the error shows in status
                    self.scheduler.error = f"scheduler: {e!r}"
            stop_event.wait(interval)


def make_handler(app):
    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *args):
            pass

        def _send(self, status, body, content_type="application/json"):
            data = body if isinstance(body, bytes) else json.dumps(body).encode()
            self.send_response(status)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)

        def _body(self):
            length = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(body, dict):
                raise ValueError("request body must be a JSON object")
            return body

        def _handle(self, fn):
            try:
                self._send(200, fn())
            except LookupError as e:
                self._send(404, {"error": str(e)})
            except (ValueError, TypeError) as e:
                self._send(400, {"error": str(e)})

        def do_GET(self):
            url = urlparse(self.path)
            q = {k: v[0] for k, v in parse_qs(url.query).items()}
            path = url.path
            if path == "/":
                return self._send(200, (STATIC / "index.html").read_bytes(), "text/html; charset=utf-8")
            routes = {
                "/api/status": app.status,
                "/api/results": lambda: app.results(q.get("ref", "main"), q.get("metric")),
                "/api/games": lambda: app.games(q.get("ref", "main"), q.get("where"), q.get("limit", 50)),
                "/api/experiments": app.experiments,
                "/api/dashboard": lambda: app.dashboard(q.get("ref", "main")),
                "/api/metrics": lambda: {n: {"description": m.description, "kind": m.kind}
                                         for n, m in METRICS.items()},
                "/api/reference/summary": app.reference_summary,
                "/api/reference/games": lambda: app.reference_games(q.get("where"), q.get("limit", 50)),
            }
            if path in routes:
                return self._handle(routes[path])
            if path.startswith("/api/jobs/"):
                return self._handle(lambda: app.job(path.rsplit("/", 1)[1]))
            self._send(404, {"error": f"no route {path}"})

        def do_POST(self):
            path = urlparse(self.path).path
            if path == "/api/jobs":
                def start():
                    body = self._body()
                    kind = body.pop("kind", None)
                    if kind == "baseline":
                        return app.start_baseline(**body)
                    if kind == "experiment":
                        return app.start_experiment(**body)
                    raise ValueError("kind must be baseline or experiment")
                return self._handle(start)
            if path == "/api/import":
                return self._handle(lambda: app.start_import(**self._body()))
            self._send(404, {"error": f"no route {path}"})

        def do_DELETE(self):
            path = urlparse(self.path).path
            if path == "/api/jobs":
                return self._handle(app.stop)
            if path.startswith("/api/jobs/"):
                return self._handle(lambda: app.stop(int(path.rsplit("/", 1)[1])))
            self._send(404, {"error": f"no route {path}"})

    return Handler


def serve(app, port=8765, host="127.0.0.1"):
    """Start listening and the scheduler loop; the caller runs httpd.serve_forever()."""
    try:
        httpd = ThreadingHTTPServer((host, port), make_handler(app))
    except OSError as e:
        if e.errno == errno.EADDRINUSE:
            raise SystemExit(f"port {port} is taken: a bench server is probably already running "
                             f"(http://{host}:{port})")
        raise
    stop = threading.Event()
    threading.Thread(target=app.loop, args=(stop,), daemon=True).start()
    return httpd, stop
```

Create the reference stub (Task 10 replaces it) — `bench/reference.py`:

```python
"""Summary of imported real ascensions (the yardstick for the ascension ladder)."""


def summary(refs):
    return {"ascensions": len(refs)}
```

Create the page placeholder so `GET /` works now (Task 8 replaces it): `bench/static/index.html`:

```html
<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>Screens Bench</title></head>
<body><p>Screens Bench</p></body></html>
```

- [ ] **Step 4: Implement `bench/cli.py`**

```python
"""screens-bench: run the bench server, wait for jobs, prune worktrees, import data."""
import argparse
import json
import os
import sys
import time
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from . import gitrefs
from .runner import ProcessWorker
from .scheduler import Scheduler
from .server import App, serve
from .store import END_STATES, Store

REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("SCREENS_BENCH_DATA", "~/.local/share/screens-bench")).expanduser()
CACHE = Path(os.environ.get("SCREENS_BENCH_CACHE", "~/.cache/screens-bench")).expanduser()
URL = os.environ.get("SCREENS_BENCH_URL", "http://127.0.0.1:8765")


def build_app(workers=11, data_dir=DATA, cache_dir=CACHE):
    data_dir, cache_dir = Path(data_dir), Path(cache_dir)
    store = Store(data_dir / "results.db")
    store.interrupt_unfinished()

    def spawn(sha):
        worktree = gitrefs.ensure_worktree(REPO, sha, cache_dir / "worktrees")
        return ProcessWorker(Path(sys.executable), worktree, data_dir / "worker.log")

    return App(store, Scheduler(store, spawn, slots=workers), REPO, cache_dir)


def _serve(args):
    app = build_app(args.workers, args.data, args.cache)
    httpd, stop = serve(app, port=args.port)
    print(f"bench server on http://127.0.0.1:{args.port} ({args.workers} workers)", flush=True)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        with app.lock:
            app.scheduler.shutdown()
        httpd.server_close()
    return 0


def _wait(args):
    while True:
        try:
            with urlopen(f"{args.url}/api/jobs/{args.job}", timeout=30) as r:
                job = json.loads(r.read())
        except URLError as e:
            print(f"bench server not reachable at {args.url}: {e}")
            return 2
        if job["state"] in END_STATES:
            print(json.dumps({k: job.get(k) for k in ("id", "kind", "state", "spec", "result")}, indent=1))
            return 1 if job["state"] == "failed" else 0
        time.sleep(args.every)


def _prune(args):
    removed = gitrefs.prune(REPO, Path(args.cache) / "worktrees", max_age_days=args.days)
    print(f"removed {len(removed)} worktrees")
    return 0


def _import(args):
    store = Store(Path(args.data) / "results.db")
    if args.what == "results":
        sha, _ = gitrefs.resolve(REPO, args.ref)
        n = 0
        with open(args.source) as f:
            for line in f:
                if line.strip():
                    store.add_game(sha, None, json.loads(line))
                    n += 1
        print(f"stored {n} games under {sha[:10]}")
        return 0
    from . import importers
    if args.what == "xlog":
        out = importers.import_xlog(store, args.source)
    else:
        out = importers.import_dumplogs(store, Path(args.cache), limit=args.limit)
    print(json.dumps(out))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(prog="screens-bench")
    ap.add_argument("--data", default=str(DATA), help="directory of results.db and logs")
    ap.add_argument("--cache", default=str(CACHE), help="directory of worktrees and downloads")
    sub = ap.add_subparsers(dest="command", required=True)

    p = sub.add_parser("serve", help="run the bench server")
    p.add_argument("--port", type=int, default=8765)
    p.add_argument("--workers", type=int, default=11)
    p.set_defaults(fn=_serve)

    p = sub.add_parser("wait", help="block until a job ends, then print it")
    p.add_argument("job", type=int)
    p.add_argument("--url", default=URL)
    p.add_argument("--every", type=float, default=5.0)
    p.set_defaults(fn=_wait)

    p = sub.add_parser("prune", help="remove worktrees unused for some days")
    p.add_argument("--days", type=int, default=14)
    p.set_defaults(fn=_prune)

    p = sub.add_parser("import", help="import benchmark files, xlogfiles or dumplogs")
    p.add_argument("what", choices=["results", "xlog", "dumplogs"])
    p.add_argument("source", nargs="?", help="results: a .jsonl file; xlog: a URL")
    p.add_argument("--ref", default="main", help="results: commit the games were played on")
    p.add_argument("--limit", type=int, default=500, help="dumplogs: at most this many downloads")
    p.set_defaults(fn=_import)

    args = ap.parse_args(argv)
    if args.command == "import" and args.what in ("results", "xlog") and not args.source:
        ap.error(f"import {args.what} needs a source")
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
```

- [ ] **Step 5: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_server.py`
Expected: 8 passed

- [ ] **Step 6: Run the whole suite**

Run: `uv run pytest -q -m ""`
Expected: all passed (the 167 existing tests plus the new bench tests)

- [ ] **Step 7: Commit**

```bash
git add bench/server.py bench/cli.py bench/reference.py bench/static/index.html tests/conftest.py tests/test_bench_server.py
git commit -m "feat(bench): JSON API, server loop and screens-bench CLI

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 8: Status page

**Files:**
- Modify: `bench/static/index.html` (replace the placeholder)
- Test: `tests/test_bench_server.py::test_page_is_served` (already exists) plus one new assertion

**Interfaces:**
- Consumes: the JSON API of Task 7 (`/api/status`, `/api/experiments`, `/api/jobs/<id>` incl. `table`, `/api/dashboard`, `/api/metrics`, `/api/reference/summary`; `POST /api/jobs`; `DELETE /api/jobs`) and the reference summary keys of Task 10 (`ascensions, with_dumplog, with_timeline, turns{median,q1,q3}, roles, achievements, milestones[{event, median_turn, share}], reflection, magic_resistance, bag_of_holding, xl, ac, wands`).

- [ ] **Step 1: Extend the page test**

Add to `test_page_is_served` in `tests/test_bench_server.py`:

```python
        page = r.read()
        assert b"<title>Screens Bench</title>" in page
        for section in (b'id="job"', b'id="experiment"', b'id="dashboard"', b'id="history"', b'id="ascenders"'):
            assert section in page
```

(replace the existing `assert b"<title>Screens Bench</title>" in r.read()` line with these.)

Run: `uv run pytest -q tests/test_bench_server.py::test_page_is_served`
Expected: FAIL — `assert b'id="job"' in page`

- [ ] **Step 2: Write `bench/static/index.html`**

```html
<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Screens Bench</title>
<style>
:root { --bg:#f6f6f7; --fg:#1d1d1f; --muted:#6b6b70; --line:#dcdce0; --card:#fff; --good:#1a7f37; --bad:#c62828; --accent:#2f5bd3; }
@media (prefers-color-scheme: dark) {
  :root { --bg:#161618; --fg:#e8e8ea; --muted:#9a9aa0; --line:#323236; --card:#1f1f22; --good:#4cc26a; --bad:#ef6b6b; --accent:#7a9cff; }
}
body { margin:0; background:var(--bg); color:var(--fg); font:14px/1.45 system-ui, sans-serif; }
main { max-width:1100px; margin:0 auto; padding:16px; }
h1 { font-size:20px; margin:4px 0 12px; }
h2 { font-size:16px; margin:0 0 8px; }
h3 { font-size:13px; margin:12px 0 4px; color:var(--muted); text-transform:uppercase; letter-spacing:.04em; }
section { background:var(--card); border:1px solid var(--line); border-radius:8px; padding:12px 16px; margin-bottom:16px; }
table { border-collapse:collapse; width:100%; }
td, th { text-align:left; padding:3px 8px; border-bottom:1px solid var(--line); font-variant-numeric:tabular-nums; vertical-align:top; }
th { color:var(--muted); font-weight:500; }
.wrap { overflow-x:auto; }
.muted { color:var(--muted); }
.better { color:var(--good); font-weight:600; }
.worse { color:var(--bad); font-weight:600; }
.bar { display:inline-block; height:10px; background:var(--accent); vertical-align:middle; border-radius:2px; }
form { display:flex; flex-wrap:wrap; gap:6px; align-items:center; margin:8px 0 0; }
input, select, button { font:inherit; padding:3px 6px; color:var(--fg); background:var(--bg); border:1px solid var(--line); border-radius:4px; }
button { cursor:pointer; }
</style>
</head>
<body>
<main>
<h1>Screens Bench</h1>
<section id="job">
  <h2>Job</h2>
  <div id="job-body" class="muted">loading…</div>
  <form id="baseline-form">Baseline <input name="ref" value="main" size="12"> games <input name="games" value="576" size="5"> <button>Start</button></form>
  <form id="experiment-form">Experiment <input name="candidate" placeholder="branch" size="14"> vs <input name="baseline" value="main" size="12"> metric <select name="metric" id="metric-select"></select> <button>Start</button></form>
  <form id="stop-form"><button>Stop current job</button></form>
  <div id="form-error" class="worse"></div>
</section>
<section id="experiment"><h2>Experiment</h2><div id="experiment-body" class="muted">no experiment yet</div></section>
<section id="dashboard"><h2>Dashboard — newest main commit with games</h2><div id="dashboard-body" class="muted">loading…</div></section>
<section id="history"><h2>History</h2><div id="history-body" class="muted">loading…</div></section>
<section id="ascenders"><h2>Ascenders — imported real wins</h2><div id="ascenders-body" class="muted">loading…</div></section>
</main>
<script>
const $ = id => document.getElementById(id);
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;'}[c]));
const pct = x => x == null ? '–' : (100 * x).toFixed(1) + '%';
const short = sha => esc((sha || '').slice(0, 10));

async function api(path, opts) {
  const r = await fetch(path, opts);
  const body = await r.json();
  if (!r.ok) throw new Error(body.error || r.statusText);
  return body;
}

function table(head, rows) {
  return '<div class="wrap"><table><tr>' + head.map(h => `<th>${esc(h)}</th>`).join('') + '</tr>'
    + rows.map(r => '<tr>' + r.map(c => `<td>${c}</td>`).join('') + '</tr>').join('') + '</table></div>';
}

function verdictHtml(v) {
  if (!v) return '<span class="muted">open</span>';
  const cls = v.state === 'better' ? 'better' : v.state === 'worse' ? 'worse' : '';
  return `<span class="${cls}">${esc(v.state)}</span> at ${v.checkpoint} games per side: `
    + `${pct(v.diff)} [${pct(v.lo)}, ${pct(v.hi)}], smallest visible difference ${pct(v.detectable)}`;
}

function renderJob(s) {
  const j = s.job;
  let html;
  if (!j) {
    html = '<span class="muted">idle</span>';
  } else {
    const p = j.progress, sp = j.spec;
    const what = j.kind === 'baseline'
      ? `baseline <b>${esc(sp.ref)}</b> ${short(sp.sha)} — ${esc(sp.subject)}`
      : `experiment <b>${esc(sp.candidate_ref)}</b> vs <b>${esc(sp.baseline_ref)}</b> on ${esc(sp.metric)}`;
    const prog = j.kind === 'baseline'
      ? `${p.games}/${p.target} games`
      : `checkpoint ${p.checkpoint}: baseline ${p.baseline}, candidate ${p.candidate}`;
    const eta = j.eta_seconds ? `, about ${Math.max(1, Math.round(j.eta_seconds / 60))} min left` : '';
    html = `#${j.id} ${what}<br>${prog} · ${s.games_per_minute.toFixed(1)} games/min · ${s.busy_workers}/${s.slots} workers${eta}`;
    if (j.kind === 'experiment') html += '<br>verdict so far: ' + verdictHtml(j.result && j.result.verdict);
  }
  if (s.error) html += `<div class="worse">${esc(s.error)}</div>`;
  const imp = s.import || {};
  if (imp.running || imp.last) html += `<div class="muted">import: ${imp.running ? 'running…' : esc(JSON.stringify(imp.last))}</div>`;
  $('job-body').innerHTML = html;
  return Boolean(j) || Boolean(imp.running);
}

async function renderExperiment(id) {
  const job = await api('/api/jobs/' + id);
  const sp = job.spec;
  const rows = (job.table || []).map(r => r.kind === 'rate'
    ? [esc(r.description), pct(r.candidate.rate), pct(r.baseline.rate), r.diff == null ? '–' : `${pct(r.diff)} [${pct(r.lo)}, ${pct(r.hi)}]`]
    : [esc(r.description), esc(r.candidate.median), esc(r.baseline.median), '']);
  $('experiment-body').innerHTML =
    `#${job.id} <b>${esc(sp.candidate_ref)}</b> ${short(sp.candidate)} vs <b>${esc(sp.baseline_ref)}</b> ${short(sp.baseline)} — ${esc(job.state)}, ${job.games_per_side} games per side<br>`
    + `primary metric <b>${esc(sp.metric)}</b>: ${verdictHtml(job.result && job.result.verdict)}<br>`
    + '<span class="muted">The other metrics are information only (95% intervals); only the primary metric decides.</span>'
    + table(['metric', 'candidate', 'baseline', 'difference'], rows);
}

function renderDashboard(d) {
  if (!d.sha) { $('dashboard-body').innerHTML = '<span class="muted">no games stored for main yet</span>'; return; }
  const rates = Object.entries(d.metrics).filter(([, v]) => 'rate' in v)
    .map(([k, v]) => [esc(k), pct(v.rate), `${v.hits}/${v.n}` + (v.skipped ? ` (${v.skipped} without data)` : '')]);
  const most = Math.max(1, ...Object.values(d.depths));
  const depths = Object.entries(d.depths).map(([k, v]) => [esc(k), `<span class="bar" style="width:${Math.round(220 * v / most)}px"></span> ${v}`]);
  const outcomes = Object.entries(d.outcomes).map(([s, o]) => [esc(s), esc(Object.entries(o).map(([k, n]) => `${n} ${k}`).join(', '))]);
  $('dashboard-body').innerHTML = `${short(d.sha)} — ${esc(d.subject)} · ${d.games} games`
    + '<h3>Rates</h3>' + table(['metric', 'rate', 'games'], rates)
    + '<h3>Top killers</h3>' + table(['killer', 'games'], d.killers.map(([k, n]) => [esc(k), n]))
    + '<h3>Max depth</h3>' + table(['Dlvl', 'games'], depths)
    + '<h3>Outcomes per strategy</h3>' + table(['strategy', 'outcomes'], outcomes)
    + '<h3>Crashes</h3>' + (d.crashes.length ? table(['end reason'], d.crashes.map(c => [esc(c)])) : '<span class="muted">none</span>')
    + '<h3>Most unsticks</h3>' + (d.unstuck.length
      ? table(['role', 'depth', 'turns', 'unsticks', 'end'], d.unstuck.map(g => [esc(g.role), g.max_depth, g.turns, g.unsticks, esc(g.end_reason)]))
      : '<span class="muted">none</span>');
}

function renderHistory(list) {
  $('history-body').innerHTML = list.length
    ? table(['#', 'candidate', 'baseline', 'metric', 'state', 'verdict'],
        list.map(j => [j.id, esc(j.spec.candidate_ref), esc(j.spec.baseline_ref), esc(j.spec.metric), esc(j.state), verdictHtml(j.result && j.result.verdict)]))
    : '<span class="muted">no experiments yet</span>';
}

function renderAscenders(r) {
  if (!r.ascensions) {
    $('ascenders-body').innerHTML = '<span class="muted">nothing imported yet — <code>screens-bench import xlog URL</code></span>';
    return;
  }
  const t = r.turns;
  let html = `${r.ascensions} ascensions, ${r.with_dumplog} with dumplog, ${r.with_timeline} with a timeline · `
    + `turns to ascend: median ${esc(t.median)} (quartiles ${esc(t.q1)}–${esc(t.q3)})`;
  html += '<h3>Milestones (first time, median turn)</h3>' + (r.milestones.length
    ? table(['event', 'median turn', 'share of games with a timeline'], r.milestones.map(e => [esc(e.event), esc(e.median_turn), pct(e.share)]))
    : '<span class="muted">no timelines yet — <code>screens-bench import dumplogs</code></span>');
  html += '<h3>Achievements</h3>' + table(['achievement', 'share'], r.achievements.map(([a, s]) => [esc(a.replaceAll('_', ' ')), pct(s)]));
  html += '<h3>Roles</h3>' + table(['role', 'ascensions'], r.roles.map(([k, n]) => [esc(k), n]));
  if (r.with_dumplog) {
    html += '<h3>At the end</h3>' + table(['', ''], [
      ['reflection', pct(r.reflection)], ['magic resistance', pct(r.magic_resistance)],
      ['bag of holding', pct(r.bag_of_holding)], ['experience level (median)', esc(r.xl)],
      ['armour class (median)', esc(r.ac)]]);
    html += '<h3>Wands carried</h3>' + table(['wand', 'share'], r.wands.map(([w, s]) => [esc(w), pct(s)]));
  }
  $('ascenders-body').innerHTML = html;
}

let timer = null;
async function refresh() {
  clearTimeout(timer);
  let busy = false;
  try {
    const s = await api('/api/status');
    busy = renderJob(s);
    const history = await api('/api/experiments');
    renderHistory(history);
    const current = s.job && s.job.kind === 'experiment' ? s.job.id : (history[0] && history[0].id);
    if (current) await renderExperiment(current);
    renderDashboard(await api('/api/dashboard'));
    renderAscenders(await api('/api/reference/summary'));
  } catch (e) {
    $('job-body').innerHTML = `<span class="worse">${esc(e.message)}</span>`;
  }
  timer = setTimeout(refresh, busy ? 2000 : 30000);
}

async function send(path, method, body) {
  $('form-error').textContent = '';
  try {
    await api(path, {method, headers: {'Content-Type': 'application/json'}, body: body && JSON.stringify(body)});
  } catch (e) {
    $('form-error').textContent = e.message;
  }
  refresh();
}

$('baseline-form').onsubmit = e => {
  e.preventDefault();
  const f = e.target.elements;
  send('/api/jobs', 'POST', {kind: 'baseline', ref: f.ref.value, games: Number(f.games.value)});
};
$('experiment-form').onsubmit = e => {
  e.preventDefault();
  const f = e.target.elements;
  send('/api/jobs', 'POST', {kind: 'experiment', candidate: f.candidate.value, baseline: f.baseline.value, metric: f.metric.value});
};
$('stop-form').onsubmit = e => { e.preventDefault(); send('/api/jobs', 'DELETE'); };

api('/api/metrics').then(metrics => {
  $('metric-select').innerHTML = Object.entries(metrics).filter(([, m]) => m.kind === 'rate')
    .map(([n, m]) => `<option value="${esc(n)}"${n === 'dlvl6' ? ' selected' : ''}>${esc(n)} — ${esc(m.description)}</option>`).join('');
});
refresh();
</script>
</body>
</html>
```

- [ ] **Step 3: Run the test to verify it passes**

Run: `uv run pytest -q tests/test_bench_server.py::test_page_is_served`
Expected: PASS

- [ ] **Step 4: Look at the page with real data**

Run in the background: `uv run screens-bench --data /tmp/claude-1000/-home-user-screens/4a293844-eb33-4141-85e6-eea2c42956c6/scratchpad/benchdata serve --port 8799 --workers 1`
Then: `curl -s localhost:8799/api/status` — Expected: JSON with `"job": null`. Open `http://localhost:8799/` in a browser (or fetch it) and confirm the sections render without a JavaScript error (`Job` shows "idle", Ascenders shows "nothing imported yet"). Stop the server.

- [ ] **Step 5: Commit**

```bash
git add bench/static/index.html tests/test_bench_server.py
git commit -m "feat(bench): live status page

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 9: MCP server

**Files:**
- Create: `bench/mcp_server.py`, `.mcp.json`, `tests/test_bench_mcp.py`

**Interfaces:**
- Consumes: the HTTP API of Task 7.
- Produces: module `bench.mcp_server` with `URL` (module global), `mcp` (FastMCP instance), tool functions `bench_status()`, `bench_baseline(ref="main", games=576)`, `bench_experiment(candidate, baseline="main", metric="dlvl6")`, `bench_results(ref="main", metric=None)`, `bench_games(ref="main", where=None, limit=50)`, `bench_experiments()`, `bench_stop(job_id=None)`, `bench_import(kind, url=None, limit=500)`, `bench_reference(where=None, limit=50)`; each returns the API's JSON (errors as `{"error": ...}`). `main()` runs the stdio server.

- [ ] **Step 1: Write the failing test**

`tests/test_bench_mcp.py`:

```python
import asyncio

import pytest

from conftest import run_until_idle
from bench import mcp_server


@pytest.fixture
def url(bench_url, monkeypatch):
    monkeypatch.setattr(mcp_server, "URL", bench_url)
    return bench_url


def test_tools_drive_the_server(url, bench_app):
    assert mcp_server.bench_status()["job"] is None
    job_id = mcp_server.bench_baseline("main", games=3)["job_id"]
    run_until_idle(bench_app)
    assert mcp_server.bench_results("main", metric="dlvl6")["n"] == 3
    assert mcp_server.bench_games("main", where="max_depth>3")["matches"] == 3
    sha = bench_app._sha("main")[0]
    assert mcp_server.bench_experiment("main", "main")["error"].endswith("same commit " + sha[:10])
    assert mcp_server.bench_stop() == {"stopped": False}
    assert mcp_server.bench_experiments() == []
    assert mcp_server.bench_reference()["summary"] == {"ascensions": 0}
    assert job_id > 0


def test_tools_are_registered():
    names = {t.name for t in asyncio.run(mcp_server.mcp.list_tools())}
    assert names == {"bench_status", "bench_baseline", "bench_experiment", "bench_results", "bench_games",
                     "bench_experiments", "bench_stop", "bench_import", "bench_reference"}
```

- [ ] **Step 2: Run the test to verify it fails**

Run: `uv run pytest -q tests/test_bench_mcp.py`
Expected: FAIL — `ImportError: cannot import name 'mcp_server' from 'bench'`

- [ ] **Step 3: Implement `bench/mcp_server.py`**

```python
"""MCP tools for Claude: drive the bench server over its JSON API (started if not running)."""
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import quote, urlencode
from urllib.request import Request, urlopen

from mcp.server.fastmcp import FastMCP

URL = os.environ.get("SCREENS_BENCH_URL", "http://127.0.0.1:8765")
REPO = Path(__file__).resolve().parent.parent
DATA = Path(os.environ.get("SCREENS_BENCH_DATA", "~/.local/share/screens-bench")).expanduser()

mcp = FastMCP("screens-bench")


def _up():
    try:
        urlopen(URL + "/api/status", timeout=2).close()
        return True
    except (URLError, OSError):
        return False


def _ensure_server():
    if _up():
        return
    DATA.mkdir(parents=True, exist_ok=True)
    log = open(DATA / "server.log", "a")
    subprocess.Popen([sys.executable, "-m", "bench.cli", "serve"], cwd=REPO, stdout=log,
                     stderr=subprocess.STDOUT, start_new_session=True)
    for _ in range(80):
        time.sleep(0.25)
        if _up():
            return
    raise RuntimeError(f"bench server did not start; see {DATA / 'server.log'}")


def _call(method, path, body=None, query=None):
    _ensure_server()
    if query:
        path += "?" + urlencode({k: v for k, v in query.items() if v is not None})
    data = None if body is None else json.dumps(body).encode()
    req = Request(URL + path, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except HTTPError as e:
        try:
            return json.loads(e.read())
        except ValueError:
            return {"error": str(e)}


@mcp.tool()
def bench_status() -> dict:
    """Current job with progress and verdict so far, worker load, games per minute, import state."""
    return _call("GET", "/api/status")


@mcp.tool()
def bench_baseline(ref: str = "main", games: int = 576) -> dict:
    """Play `ref` until it has `games` stored games (stored games are reused). Returns job_id;
    run `uv run screens-bench wait <job_id>` as a background shell command to be notified."""
    return _call("POST", "/api/jobs", {"kind": "baseline", "ref": ref, "games": games})


@mcp.tool()
def bench_experiment(candidate: str, baseline: str = "main", metric: str = "dlvl6") -> dict:
    """A/B experiment: candidate vs baseline commit, judged on one rate metric at 192/384/576/1152
    games per side. Commit first; refs resolve to a SHA now. Returns job_id; run
    `uv run screens-bench wait <job_id>` as a background shell command to be notified."""
    return _call("POST", "/api/jobs", {"kind": "experiment", "candidate": candidate,
                                       "baseline": baseline, "metric": metric})


@mcp.tool()
def bench_results(ref: str = "main", metric: str | None = None) -> dict:
    """Summary of a commit's stored games (rates, killers, depths, outcomes, crashes), or one metric."""
    return _call("GET", "/api/results", query={"ref": ref, "metric": metric})


@mcp.tool()
def bench_games(ref: str = "main", where: str | None = None, limit: int = 50) -> dict:
    """Stored games of a commit matching a filter like 'max_depth>9,end_reason~soldier ant'."""
    return _call("GET", "/api/games", query={"ref": ref, "where": where, "limit": limit})


@mcp.tool()
def bench_experiments() -> list:
    """All experiments, newest first, with their verdicts."""
    return _call("GET", "/api/experiments")


@mcp.tool()
def bench_stop(job_id: int | None = None) -> dict:
    """Stop the active job (or a queued job by id). Stored games stay."""
    return _call("DELETE", "/api/jobs" if job_id is None else f"/api/jobs/{quote(str(job_id))}")


@mcp.tool()
def bench_import(kind: str, url: str | None = None, limit: int = 500) -> dict:
    """Import real ascensions: kind='xlog' with an xlogfile url (e.g.
    https://www.hardfought.org/xlogfiles/nethack50/xlogfile), or kind='dumplogs' to download
    dumplogs of imported ascensions (1 request per second). Runs in the background; see bench_status."""
    return _call("POST", "/api/import", {"kind": kind, "url": url, "limit": limit})


@mcp.tool()
def bench_reference(where: str | None = None, limit: int = 50) -> dict:
    """Summary of imported real ascensions plus the xlog records matching a filter (e.g. 'role=Val')."""
    return {"summary": _call("GET", "/api/reference/summary"),
            "games": _call("GET", "/api/reference/games", query={"where": where, "limit": limit})}


def main():
    mcp.run()


if __name__ == "__main__":
    main()
```

Create `.mcp.json` in the repo root:

```json
{
  "mcpServers": {
    "screens-bench": {
      "command": "uv",
      "args": ["run", "--group", "bench", "python", "-m", "bench.mcp_server"]
    }
  }
}
```

- [ ] **Step 4: Run the test to verify it passes**

Run: `uv run pytest -q tests/test_bench_mcp.py`
Expected: 2 passed

- [ ] **Step 5: Commit**

```bash
git add bench/mcp_server.py .mcp.json tests/test_bench_mcp.py
git commit -m "feat(bench): MCP tools over the bench API

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 10: Importing real ascensions

**Files:**
- Create: `bench/importers.py`, `tests/test_bench_importers.py`, `tests/data/bench_xlog_sample.txt`, `tests/data/bench_dumplog_sample.txt`
- Modify: `bench/reference.py` (replace the stub)

**Interfaces:**
- Consumes: `Store.add_reference`, `Store.references`, `Store.set_dumplog` (Task 1).
- Produces: `parse_xlog_line(line) -> dict | None`, `achievements(record) -> list[str]`, `fetch(url, cache_dir=None, min_interval=1.0) -> str` (cached when `cache_dir` is given), `import_xlog(store, url, source=None, fetcher=fetch) -> {"lines", "ascensions", "added"}`, `dumplog_url(source, record) -> str | None`, `import_dumplogs(store, cache_dir, limit=500, fetcher=fetch) -> {"fetched", "failed", "unsupported"}`, `sections(text) -> dict[str, list[str]]`, `parse_dumplog(text) -> dict` with keys `inventory, attributes, conducts, vanquished, ac, xl, events, reflection, magic_resistance, bag_of_holding, wands`. `reference.summary(refs, min_share=0.5) -> dict` with keys `ascensions, with_dumplog, with_timeline, turns, roles, achievements, milestones, reflection, magic_resistance, bag_of_holding, xl, ac, wands` (the last six only when a dumplog exists).

- [ ] **Step 1: Create the fixtures**

`tests/data/bench_xlog_sample.txt` — three lines, fields separated by TAB characters (`\t`), player names replaced by `player1`/`player2`/`player3`:

```
version=5.0.0	points=2151016	deathdnum=7	deathlev=-5	maxlvl=52	hp=153	maxhp=169	deaths=0	deathdate=20260503	birthdate=20260502	uid=5	role=Bar	race=Hum	gender=Mal	align=Cha	name=player1	death=ascended	conduct=0x2400	turns=44867	achieve=0x233c3ff	achieveX=entered_the_gnomish_mines,entered_mine_town,entered_sokoban,entered_bigroom,obtained_the_bell_of_opening,entered_gehennom,obtained_the_candelabrum_of_invocation,obtained_the_book_of_the_dead,performed_the_invocation_ritual,entered_elemental_planes,entered_astral_plane,obtained_the_amulet_of_yendor,ascended	realtime=37873	starttime=1777773884	endtime=1777862820
version=3.6.7	points=1766446	deathdnum=7	deathlev=-5	maxlvl=52	hp=35	maxhp=200	deaths=0	deathdate=20260921	birthdate=20260909	uid=5	role=Val	race=Dwa	gender=Fem	align=Law	name=player2	death=ascended	conduct=0x480	turns=37140	achieve=0xfff	realtime=264978	starttime=1788964024	endtime=1790021082
version=5.0.0	points=120	deathdnum=0	deathlev=3	maxlvl=3	hp=-1	maxhp=20	deaths=1	deathdate=20260601	birthdate=20260601	uid=5	role=Wiz	race=Elf	gender=Fem	align=Cha	name=player3	death=killed by a jackal	conduct=0x0	turns=900	achieve=0x0	realtime=600	starttime=1780000000	endtime=1780000600
```

Write it with Python so the tabs are exact:

```bash
uv run python - <<'EOF'
lines = [
 "version=5.0.0 points=2151016 deathdnum=7 deathlev=-5 maxlvl=52 hp=153 maxhp=169 deaths=0 deathdate=20260503 birthdate=20260502 uid=5 role=Bar race=Hum gender=Mal align=Cha name=player1 death=ascended conduct=0x2400 turns=44867 achieve=0x233c3ff achieveX=entered_the_gnomish_mines,entered_mine_town,entered_sokoban,entered_bigroom,obtained_the_bell_of_opening,entered_gehennom,obtained_the_candelabrum_of_invocation,obtained_the_book_of_the_dead,performed_the_invocation_ritual,entered_elemental_planes,entered_astral_plane,obtained_the_amulet_of_yendor,ascended realtime=37873 starttime=1777773884 endtime=1777862820",
 "version=3.6.7 points=1766446 deathdnum=7 deathlev=-5 maxlvl=52 hp=35 maxhp=200 deaths=0 deathdate=20260921 birthdate=20260909 uid=5 role=Val race=Dwa gender=Fem align=Law name=player2 death=ascended conduct=0x480 turns=37140 achieve=0xfff realtime=264978 starttime=1788964024 endtime=1790021082",
 "version=5.0.0 points=120 deathdnum=0 deathlev=3 maxlvl=3 hp=-1 maxhp=20 deaths=1 deathdate=20260601 birthdate=20260601 uid=5 role=Wiz race=Elf gender=Fem align=Cha name=player3 death=killed_by_a_jackal conduct=0x0 turns=900 achieve=0x0 realtime=600 starttime=1780000000 endtime=1780000600",
]
with open("tests/data/bench_xlog_sample.txt", "w") as f:
    for line in lines:
        f.write("\t".join(line.split(" ")).replace("killed_by_a_jackal", "killed by a jackal") + "\n")
EOF
```

`tests/data/bench_dumplog_sample.txt` (shortened NetHack 5.0 dumplog, name replaced):

```
Unix NetHack Version 5.0.0-0 post-release - last build Sep 14 2026 19:18:36.

Game began 2026-09-17 11:16:10, ended 2026-09-20 23:08:45.

player1, chaotic male orcish Barbarian

Inventory:
 Amulets  ('"')
  L - an uncursed amulet of life saving (being worn)
 Armor    ('[')
  E - a blessed greased fireproof +4 cloak of magic resistance (being worn)
 Wands    ('/')
  b - a wand of digging (0:3)
  c - a blessed wand of death (0:5)
 Tools    ('(')
  h - a bag of holding

Contents of the bag of holding:
  m - a wand of teleportation (0:4)

Background:
 You were a Slayer, a level 25 male orcish Barbarian.
 You were in the endgame, on the Astral Plane.

Basics:
 You had 83 out of 110 hit points.
 Your armor class was -38.

Final Attributes:
 You were magic-protected.
 You were fire resistant.
 You had reflection.

Major events:
 Turn
    1: player1 the chaotic male orcish Barbarian entered the dungeon
  435: entered the Gnomish Mines
 2976: reached Mine Town
10483: acquired the Mines' End luckstone
15652: entered Sokoban
59166: killed Famine
59189: killed Famine (2nd time)
59302: ascended

Voluntary challenges:
 You engraved Elbereth 26 times.
 You used 2 wishes.

Vanquished creatures:
  Death (3 times)
  2 jackals
1840 creatures vanquished.
```

- [ ] **Step 2: Write the failing tests**

`tests/test_bench_importers.py`:

```python
from pathlib import Path

import pytest

from bench import importers, reference
from bench.store import Store

DATA = Path(__file__).parent / "data"
XLOG = (DATA / "bench_xlog_sample.txt").read_text()
DUMP = (DATA / "bench_dumplog_sample.txt").read_text()


def test_xlog_lines_with_tabs_and_colons():
    first = importers.parse_xlog_line(XLOG.splitlines()[0])
    assert first["name"] == "player1" and first["death"] == "ascended" and first["turns"] == "44867"
    old = importers.parse_xlog_line("version=3.4.3:name=x:death=ascended:turns=50000:starttime=1")
    assert old["turns"] == "50000"
    assert importers.parse_xlog_line("garbage without fields") is None


def test_achievements_from_names_or_3_6_bits():
    lines = [importers.parse_xlog_line(l) for l in XLOG.splitlines()]
    assert "entered_gehennom" in importers.achievements(lines[0])
    bits = importers.achievements(lines[1])  # 0xfff in NetHack 3.6
    assert {"obtained_the_bell_of_opening", "defeated_medusa", "ascended"} <= set(bits)
    assert importers.achievements(lines[2]) == []


def test_import_xlog_keeps_ascensions_once(tmp_path):
    store = Store(tmp_path / "r.db")
    fetch = lambda url, cache_dir=None: XLOG
    url = "https://www.hardfought.org/xlogfiles/nethack50/xlogfile"
    assert importers.import_xlog(store, url, fetcher=fetch) == {"lines": 3, "ascensions": 2, "added": 2}
    assert importers.import_xlog(store, url, fetcher=fetch)["added"] == 0
    refs = store.references()
    assert [r["source"] for r in refs] == ["hardfought", "hardfought"]
    assert "ascended" in refs[0]["record"]["achievements"]


def test_dumplog_url_and_import(tmp_path):
    store = Store(tmp_path / "r.db")
    importers.import_xlog(store, "https://www.hardfought.org/x", fetcher=lambda url, cache_dir=None: XLOG)
    importers.import_xlog(store, "https://example.org/xlogfile", fetcher=lambda url, cache_dir=None: XLOG)
    asked = []

    def fetch(url, cache_dir=None):
        asked.append(url)
        if "player2" in url:
            raise OSError("404")
        return DUMP

    out = importers.import_dumplogs(store, tmp_path / "cache", limit=10, fetcher=fetch)
    assert out == {"fetched": 1, "failed": 1, "unsupported": 2}
    assert asked[0] == "https://www.hardfought.org/userdata/p/player1/nethack/dumplog/1777773884.nh.txt"
    assert sum(r["dumplog"] is not None for r in store.references()) == 1


def test_fetch_caches_and_throttles(tmp_path, monkeypatch):
    calls = []

    class Response:
        def __init__(self, url):
            self.url = url
        def read(self):
            return b"body"
        def __enter__(self):
            return self
        def __exit__(self, *a):
            return False

    monkeypatch.setattr(importers, "urlopen", lambda req, timeout: calls.append(req.full_url) or Response(req.full_url))
    sleeps = []
    monkeypatch.setattr(importers.time, "sleep", lambda s: sleeps.append(s))
    assert importers.fetch("https://a/1", tmp_path) == "body"
    assert importers.fetch("https://a/1", tmp_path) == "body"  # cached
    assert importers.fetch("https://a/2", tmp_path) == "body"
    assert calls == ["https://a/1", "https://a/2"] and sleeps and sleeps[-1] <= 1.0
    assert importers.fetch("https://a/3") == "body"  # no cache dir: always downloads


def test_parse_dumplog():
    d = importers.parse_dumplog(DUMP)
    assert d["ac"] == -38 and d["xl"] == 25
    assert d["reflection"] and d["magic_resistance"] and d["bag_of_holding"]
    assert d["wands"] == ["death", "digging", "teleportation"]
    assert d["events"][1] == (435, "entered the Gnomish Mines")
    assert d["events"][-1] == (59302, "ascended")
    assert d["vanquished"] == 1840
    assert "You used 2 wishes." in d["conducts"]


def test_reference_summary(tmp_path):
    store = Store(tmp_path / "r.db")
    importers.import_xlog(store, "https://www.hardfought.org/x", fetcher=lambda url, cache_dir=None: XLOG)
    store.set_dumplog(store.references()[0]["id"], DUMP)
    s = reference.summary(store.references())
    assert s["ascensions"] == 2 and s["with_dumplog"] == 1 and s["with_timeline"] == 1
    assert s["turns"]["median"] == pytest.approx((44867 + 37140) / 2)
    assert dict(s["roles"]) == {"Bar": 1, "Val": 1}
    events = [m["event"] for m in s["milestones"]]
    assert events.index("entered the Gnomish Mines") < events.index("entered Sokoban")
    assert "killed Famine" in events and "killed Famine (2nd time)" not in events
    assert s["reflection"] == 1.0 and s["ac"] == -38 and ("death", 1.0) in s["wands"]
    assert reference.summary([]) == {"ascensions": 0}
```

- [ ] **Step 3: Run the tests to verify they fail**

Run: `uv run pytest -q tests/test_bench_importers.py`
Expected: FAIL — `ImportError: cannot import name 'importers' from 'bench'`

- [ ] **Step 4: Implement `bench/importers.py`**

```python
"""Import real ascensions from public NetHack servers: xlogfiles and dumplogs."""
import hashlib
import re
import time
from pathlib import Path
from urllib.parse import urlparse
from urllib.request import Request, urlopen

USER_AGENT = "screens-bench (local NetHack bot research; 1 request per second)"
HARDFOUGHT_DUMPLOG = "https://www.hardfought.org/userdata/{initial}/{name}/nethack/dumplog/{starttime}.nh.txt"

# NetHack 3.6 'achieve' bits; newer servers write the names in 'achieveX'
ACHIEVE_36 = {
    0x001: "obtained_the_bell_of_opening", 0x002: "entered_gehennom",
    0x004: "obtained_the_candelabrum_of_invocation", 0x008: "obtained_the_book_of_the_dead",
    0x010: "performed_the_invocation_ritual", 0x020: "obtained_the_amulet_of_yendor",
    0x040: "entered_elemental_planes", 0x080: "entered_astral_plane", 0x100: "ascended",
    0x200: "obtained_the_luckstone_from_the_mines", 0x400: "obtained_the_sokoban_prize",
    0x800: "defeated_medusa",
}

_last_request = [0.0]


def fetch(url, cache_dir=None, min_interval=1.0):
    """Download text; with cache_dir each URL is fetched only once. At most one request per second."""
    cache = None
    if cache_dir is not None:
        cache = Path(cache_dir) / "downloads" / hashlib.sha1(url.encode()).hexdigest()
        if cache.exists():
            return cache.read_text(errors="replace")
    wait = _last_request[0] + min_interval - time.monotonic()
    if wait > 0:
        time.sleep(wait)
    try:
        with urlopen(Request(url, headers={"User-Agent": USER_AGENT}), timeout=60) as r:
            text = r.read().decode("utf-8", errors="replace")
    finally:
        _last_request[0] = time.monotonic()
    if cache is not None:
        cache.parent.mkdir(parents=True, exist_ok=True)
        cache.write_text(text)
    return text


def parse_xlog_line(line):
    """One xlogfile record as a dict of strings (fields split by TAB, or ':' in old files)."""
    sep = "\t" if "\t" in line else ":"
    record = dict(f.split("=", 1) for f in line.rstrip("\n").split(sep) if "=" in f)
    return record if "name" in record and "death" in record else None


def achievements(record):
    if record.get("achieveX"):
        return record["achieveX"].split(",")
    bits = int(record.get("achieve", "0"), 16)
    return [name for bit, name in sorted(ACHIEVE_36.items()) if bits & bit]


def _source(url):
    host = urlparse(url).hostname or "unknown"
    return "hardfought" if host.endswith("hardfought.org") else host


def import_xlog(store, url, source=None, fetcher=fetch):
    source = source or _source(url)
    lines = ascensions = added = 0
    for line in fetcher(url, None).splitlines():
        record = parse_xlog_line(line)
        if record is None:
            continue
        lines += 1
        if record["death"] != "ascended" or "starttime" not in record:
            continue
        ascensions += 1
        record["achievements"] = achievements(record)
        added += store.add_reference(source, record)
    return {"lines": lines, "ascensions": ascensions, "added": added}


def dumplog_url(source, record):
    if source == "hardfought":
        name = record["name"]
        return HARDFOUGHT_DUMPLOG.format(initial=name[0], name=name, starttime=record["starttime"])
    return None


def import_dumplogs(store, cache_dir, limit=500, fetcher=fetch):
    out = {"fetched": 0, "failed": 0, "unsupported": 0}
    for ref in store.references():
        if ref["dumplog"] is not None:
            continue
        url = dumplog_url(ref["source"], ref["record"])
        if url is None:
            out["unsupported"] += 1
            continue
        if out["fetched"] + out["failed"] >= limit:
            break
        try:
            text = fetcher(url, cache_dir)
        except (OSError, ValueError):  # missing file, network error: retried next time
            out["failed"] += 1
            continue
        store.set_dumplog(ref["id"], text)
        out["fetched"] += 1
    return out


_HEADING = re.compile(r"^(\S[^:]*):\s*$")
_ITEM = re.compile(r"^\s+[a-zA-Z$#] - (.*)$")
_EVENT = re.compile(r"^\s*(\d+): (.*)$")
_WAND = re.compile(r"wand of ([a-z ]+?)(?: \(|$| named| called)")


def sections(text):
    out, current = {}, None
    for line in text.splitlines():
        m = _HEADING.match(line)
        if m:
            current = m.group(1)
            out[current] = []
        elif current is not None:
            out[current].append(line)
    return out


def _int(match):
    return int(match.group(1)) if match else None


def parse_dumplog(text):
    s = sections(text)
    carried = s.get("Inventory", []) + [l for name, lines in s.items() if name.startswith("Contents of")
                                         for l in lines]
    inventory = [m.group(1) for line in carried if (m := _ITEM.match(line))]
    attributes = [l.strip() for l in s.get("Final Attributes", []) if l.strip()]
    vanquished = " ".join(s.get("Vanquished creatures", []))
    return {
        "inventory": inventory,
        "attributes": attributes,
        "conducts": [l.strip() for l in s.get("Voluntary challenges", []) if l.strip()],
        "vanquished": _int(re.search(r"(\d+) creatures vanquished", vanquished)),
        "ac": _int(re.search(r"Your armor class was (-?\d+)", " ".join(s.get("Basics", [])))),
        "xl": _int(re.search(r"a level (\d+) ", " ".join(s.get("Background", [])))),
        "events": [(int(m.group(1)), m.group(2).strip())
                   for line in s.get("Major events", []) if (m := _EVENT.match(line))],
        "reflection": any("reflection" in a for a in attributes),
        "magic_resistance": any("magic-protected" in a for a in attributes),
        "bag_of_holding": any("bag of holding" in i for i in inventory),
        "wands": sorted({m.group(1).strip() for i in inventory if (m := _WAND.search(i))}),
    }
```

- [ ] **Step 5: Replace `bench/reference.py`**

```python
"""Summary of imported real ascensions (the yardstick for the ascension ladder)."""
import re
import statistics
from collections import Counter, defaultdict

from .importers import parse_dumplog

_REPEAT = re.compile(r"\s*\(\d+(st|nd|rd|th) time\)$")


def _spread(values):
    if not values:
        return {"median": None, "q1": None, "q3": None}
    if len(values) == 1:
        return {"median": values[0], "q1": values[0], "q3": values[0]}
    q1, _, q3 = statistics.quantiles(values, n=4)
    return {"median": statistics.median(values), "q1": q1, "q3": q3}


def _median(values):
    values = [v for v in values if v is not None]
    return statistics.median(values) if values else None


def summary(refs, min_share=0.5):
    n = len(refs)
    if not n:
        return {"ascensions": 0}
    achieved = Counter(a for r in refs for a in set(r["record"].get("achievements", [])))
    dumps = [parse_dumplog(r["dumplog"]) for r in refs if r["dumplog"]]
    timelines = [d["events"] for d in dumps if d["events"]]
    first_turns = defaultdict(list)
    for events in timelines:
        first = {}
        for turn, text in events:
            first.setdefault(_REPEAT.sub("", text), turn)  # "killed Famine (2nd time)" -> first kill
        for event, turn in first.items():
            first_turns[event].append(turn)
    milestones = sorted(({"event": e, "median_turn": statistics.median(t), "share": len(t) / len(timelines)}
                         for e, t in first_turns.items() if len(t) / len(timelines) >= min_share),
                        key=lambda m: m["median_turn"])
    out = {
        "ascensions": n,
        "with_dumplog": len(dumps),
        "with_timeline": len(timelines),
        "turns": _spread(sorted(int(r["record"].get("turns", 0)) for r in refs)),
        "roles": Counter(r["role"] for r in refs).most_common(),
        "achievements": sorted(((a, c / n) for a, c in achieved.items()), key=lambda x: -x[1]),
        "milestones": milestones,
    }
    if dumps:
        m = len(dumps)
        wands = Counter(w for d in dumps for w in d["wands"])
        out.update(reflection=sum(d["reflection"] for d in dumps) / m,
                   magic_resistance=sum(d["magic_resistance"] for d in dumps) / m,
                   bag_of_holding=sum(d["bag_of_holding"] for d in dumps) / m,
                   xl=_median([d["xl"] for d in dumps]), ac=_median([d["ac"] for d in dumps]),
                   wands=[(w, c / m) for w, c in wands.most_common(10)])
    return out
```

- [ ] **Step 6: Run the tests to verify they pass**

Run: `uv run pytest -q tests/test_bench_importers.py tests/test_bench_mcp.py tests/test_bench_server.py`
Expected: all passed

- [ ] **Step 7: Run the whole suite**

Run: `uv run pytest -q -m ""`
Expected: all passed

- [ ] **Step 8: Commit**

```bash
git add bench/importers.py bench/reference.py tests/test_bench_importers.py tests/data/bench_xlog_sample.txt tests/data/bench_dumplog_sample.txt
git commit -m "feat(bench): import real ascensions from xlogfiles and dumplogs

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

---

### Task 11: End-to-end check, validation run and docs

**Files:**
- Create: `tests/test_bench_e2e.py`
- Modify: `README.md` (new section), `autoascend/PORTING.md` (one paragraph)

**Interfaces:**
- Consumes: everything above.

- [ ] **Step 1: Write the slow end-to-end test**

`tests/test_bench_e2e.py`:

```python
import sys
import time
from pathlib import Path

import pytest

from bench import gitrefs
from bench.runner import ProcessWorker
from bench.scheduler import Scheduler
from bench.store import Store

REPO = Path(__file__).resolve().parent.parent


@pytest.mark.slow
def test_two_real_games_from_a_worktree(tmp_path):
    sha, _ = gitrefs.resolve(REPO, "HEAD")
    store = Store(tmp_path / "r.db")

    def spawn(s):
        return ProcessWorker(Path(sys.executable), gitrefs.ensure_worktree(REPO, s, tmp_path / "wt"),
                             tmp_path / "worker.log")

    sched = Scheduler(store, spawn, slots=2)
    job = sched.submit("baseline", {"ref": "HEAD", "sha": sha, "games": 2})
    end = time.time() + 900
    while sched.job is not None or store.next_queued() is not None:
        assert time.time() < end, (tmp_path / "worker.log").read_text()[-2000:]
        sched.tick()
        time.sleep(0.2)
    assert store.job(job)["state"] == "done"
    games = store.games(sha)
    assert len(games) == 2 and all("max_depth" in g and "end_reason" in g for g in games)
    gitrefs.prune(REPO, tmp_path / "wt", now=time.time() + 30 * 86400)
```

Run: `uv run pytest -q -m slow tests/test_bench_e2e.py`
Expected: 1 passed (takes a few minutes; it plays two real games).

- [ ] **Step 2: Commit the test**

```bash
git add tests/test_bench_e2e.py
git commit -m "test(bench): two real games through a worktree

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```

- [ ] **Step 3: Seed stored games from today's benchmark files**

The 576 games of `unstick.jsonl` were played on the code of `aa4b1cf` (its child commits only touched docs); the 1152 games of `choke.jsonl` + `choke2.jsonl` on `choke-points`:

```bash
S=/tmp/claude-1000/-home-user-screens/4a293844-eb33-4141-85e6-eea2c42956c6/scratchpad
uv run screens-bench import results $S/unstick.jsonl --ref aa4b1cf
uv run screens-bench import results $S/choke.jsonl --ref choke-points
uv run screens-bench import results $S/choke2.jsonl --ref choke-points
```

Expected: `stored 576 games under aa4b1cf...`, then `stored 576 games under b31e926...` twice.

- [ ] **Step 4: Validation run through MCP**

Start the server via the MCP tools (reconnect MCP servers in Claude Code so `.mcp.json` is picked up, or run `uv run screens-bench serve` in the background). Then call `bench_experiment(candidate="choke-points", baseline="aa4b1cf")`, and run `uv run screens-bench wait <job_id>` as a background shell command.

Expected: the server tops up `aa4b1cf` from 576 to 1152 games (about 15 minutes at 11 workers) and judges each checkpoint on the first N games per side. Final verdict `no measurable difference` at 1152 (or `open` at earlier checkpoints). If it says `better` or `worse`, that is a real finding to report, not a bug.

While it runs, open `http://localhost:8765/` and check: job progress updates every 2 s, games per minute and time left show, the experiment table fills.

- [ ] **Step 5: Import real ascensions**

```bash
uv run screens-bench import xlog https://www.hardfought.org/xlogfiles/nethack50/xlogfile
uv run screens-bench import xlog https://www.hardfought.org/xlogfiles/nethack36/xlogfile
uv run screens-bench import dumplogs --limit 200
```

Expected: about 130 + 558 ascensions added; up to 200 dumplogs fetched (about 4 minutes at one request per second). The Ascenders section then shows turns to ascend, milestones with median turns (from the 5.0 timelines), and gear shares.

- [ ] **Step 6: Document it**

Append to `README.md`:

```markdown
## Bench server (for working on the bot)

`uv run screens-bench serve` starts a local server on http://localhost:8765 that plays bot
games on demand, stores every game per commit, and compares commits:

- **Baseline:** play a commit up to N games (`main` by default); the page's dashboard shows
  killers, depths, outcomes and crashes of the newest `main` commit with games.
- **Experiment:** candidate branch vs baseline, judged on one metric (default "reached Dlvl
  6+") at 192/384/576/1152 games per side; stored baseline games are reused.
- **Ascenders:** `screens-bench import xlog <url>` and `screens-bench import dumplogs` load
  real ascensions from public servers (e.g. hardfought.org) as a yardstick.

Claude drives it through the MCP server in `.mcp.json`. Only committed code can be
benchmarked; each commit runs from its own worktree under `~/.cache/screens-bench/`.
Results live in `~/.local/share/screens-bench/results.db`.
```

Append to `autoascend/PORTING.md`:

```markdown
## Bench server (2026-10-20)

Benchmarks now run through `screens-bench` (see README). The choke-points validation
experiment (`choke-points` vs `aa4b1cf`, metric dlvl6) ended as: <fill in the verdict line
printed by `screens-bench wait`>.
```

Replace the `<fill in ...>` text with the actual verdict line from Step 4 before committing (state, checkpoint, difference and interval).

- [ ] **Step 7: Full suite and commit**

Run: `uv run pytest -q -m ""`
Expected: all passed

```bash
git add README.md autoascend/PORTING.md
git commit -m "docs: bench server usage and validation result

Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>"
```
