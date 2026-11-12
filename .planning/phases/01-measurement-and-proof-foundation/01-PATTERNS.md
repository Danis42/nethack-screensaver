# Phase 1: Measurement and Proof Foundation - Pattern Map

**Mapped:** 2026-11-12
**Files analyzed:** 24 (new + modified)
**Analogs found:** 22 / 24
(Note: RESEARCH.md was read to line 442 of 603; file list taken from its Recommended Project Structure and Patterns 1-14.)
All analog paths below were checked with `git ls-files` (tracked source; no gitignored mirrors).

## File Classification

| New/Modified File | Role | Data Flow | Closest Analog | Match |
|---|---|---|---|---|
| `pyproject.toml` (nle git source), `uv.lock` | config | n/a | itself (`[tool.uv.sources]`) | exact |
| `.mcp.json` (drop hard-coded interpreter) | config | n/a | itself | exact |
| `bench/seeds.py` | utility (pure logic) | transform | `bench/stats.py` (stdlib-only pure module) | role-match |
| `bench/funnel.py` | utility (pure logic) | transform | `bench/metrics.py` + `bench/report.py` | role-match |
| `bench/sequential.py` | utility (stats) | transform | `bench/stats.py` | exact |
| `bench/power.py` | utility (stats) | transform | `bench/stats.py` | role-match |
| `bench/provenance.py` | service | request-response (subprocess query) | `bench/gitrefs.py`, `bench/runner.py` | role-match |
| `bench/store.py` (schema v2, `tool_games`, `resume`, `started`) | model/store | CRUD | itself | exact |
| `bench/scheduler.py` (seed ranges, prefix looks) | service | batch/event | itself | exact |
| `bench/server.py` (`start_*` validation, resume route) | controller | request-response | itself | exact |
| `bench/mcp_server.py` (`bench_resume`, `bench_power`, `bench_funnel`) | controller | request-response | itself | exact |
| `bench/worker.py` (`play <seed> [lgen]`) | service | request-response | itself (`can_seed`) | exact |
| `bench/toolruns.py` | utility | CRUD | `scripts/replay_check.py` + `bench/store.py` | role-match |
| `bench/metrics.py` / `bench/report.py` / `bench/static/index.html` (remove `rung`) | modify | transform | itself | exact |
| `nethack_screensaver/game.py` (`run_game(lgen=)`, `GameResult.lgen`) | service | request-response | itself (`seed` handling) | exact |
| `scripts/check_claims.py` | utility (hook) | request-response | none (see below); `scripts/replay_check.py` for CLI/exit-code style | partial |
| `scripts/facts.py` | utility (CLI) | batch | `scripts/replay_check.py` | role-match |
| `scripts/sim_sequential.py` | utility (CLI) | batch | `scripts/staged_run.py` (JSON lines) | role-match |
| `facts/FACTS.toml` | config/data | n/a | `nethack_screensaver/config.py` (tomllib) | partial |
| `.claude/settings.json` | config | event-driven | none | none |
| `tests/test_bench_{seeds,funnel,sequential,power,provenance,tool_games}.py` | test | n/a | `tests/test_bench_stats.py`, `tests/test_bench_store.py` | exact |
| `tests/test_check_claims.py`, `tests/test_facts.py` | test | n/a | `tests/test_bench_store.py` | role-match |
| `tests/test_bench_scheduler.py` additions | test | n/a | itself + `tests/bench_fakes.py` | exact |
| Sokoban detector test (`tests/test_ladder.py` addition) | test | n/a | `tests/test_ladder.py` | exact |

## Pattern Assignments

### `bench/sequential.py`, `bench/power.py`, `bench/seeds.py`, `bench/funnel.py` (pure logic)

**Analog:** `bench/stats.py` (lines 1-60). Module docstring, stdlib `math`, frozen dataclass verdict with `as_dict`, constants at top.

```python
"""Intervals for comparing rates, and the checkpoint verdicts of an experiment."""
import math
from dataclasses import asdict, dataclass

CHECKPOINTS = (192, 384, 576, 1152, 2304)
Z95 = 1.959963984540054

def wilson(k, n, z):
    """Wilson score interval for k successes out of n."""
    p = k / n          # <-- add n == 0 guard (RESEARCH: divides by zero)
    ...

@dataclass(frozen=True)
class Verdict:
    state: str  # better | worse | no measurable difference | open
    ...
    def as_dict(self):
        return {**asdict(self), "detectable": self.detectable}
```
Reuse `wilson` from here in `funnel.py` (do not copy). `sequential.py` returns a `Verdict`-like dataclass with the same `state` vocabulary so `orient()` in `bench/metrics.py` (lines 79-83) keeps working. Use `scipy.stats.binomtest` and the `log_mixture_lr` snippet from RESEARCH "Code Examples". No `bench` imports of game code.

**Test analog:** `tests/test_bench_stats.py` lines 1-30: flat `test_<behaviour>` functions, `pytest.approx`, published-example comments, e.g. `assert judge(286, 576, 262, 576, 576).state == "open"`.

### `bench/funnel.py` and `rung` removal

**Analog:** `bench/metrics.py` lines 60-77 (the metric registry to modify):
```python
Metric("rung", "highest ascension-ladder rung", "median", lambda g: g["rung"]),
] + [Metric(f"rung{r.number}", f"reached rung {r.number}+ ({r.title})", "rate",
            lambda g, n=r.number: g["rung"] >= n) for r in RUNGS]}
```
Replace the generated entries with `stage_<key>` rate metrics: `lambda g, k=r.key: k in g["ladder"]` (default-arg capture, same idiom as `n=r.number`). `r.key` comes from `autoascend/ladder.py` `RUNGS`/`BY_KEY` (bench may import it; it is stdlib only). Also edit `bench/report.py:19` and `bench/static/index.html:119`.
Games lacking `ladder` are counted separately (the `evaluate()` loop at `bench/metrics.py:~90` already uses `try/except KeyError` for missing fields; follow that).

### `bench/store.py` (schema v2, `tool_games`, `resume`, `started`)

**Analog:** itself. Schema pattern (lines 8-24) and guarded constructor (lines 34-48):
```python
SCHEMA_VERSION = 1
_SCHEMA = """
CREATE TABLE IF NOT EXISTS games (
    id INTEGER PRIMARY KEY, sha TEXT NOT NULL, job_id INTEGER,
    finished_at REAL NOT NULL, json TEXT NOT NULL);
CREATE INDEX IF NOT EXISTS games_by_sha ON games (sha, id);
...
elif int(row["value"]) != SCHEMA_VERSION:
    raise RuntimeError(f"{path} has schema {row['value']}, this code expects {SCHEMA_VERSION}")
```
Note: `_SCHEMA` uses `CREATE TABLE IF NOT EXISTS`; the v1 to v2 migration (`ALTER TABLE ... ADD COLUMN`, backfill `seed` from `json_extract`) must run before the version check raises. Put new tables in `_SCHEMA`, columns via migration step.

Write/read helpers to reuse (lines 50-67): `self._one/_all/_write` under `self._lock`.
```python
def add_game(self, sha, job_id, result, finished_at=None):
    return self._write("INSERT INTO games (sha, job_id, finished_at, json) VALUES (?, ?, ?, ?)",
                       (sha, job_id, finished_at or time.time(), json.dumps(result))).lastrowid
```
Add here: raise on `result.get("stage")`, final-range seed guard, populate `seed/lgen/env_id/rep` columns. Replace the `json_extract` scans in `seeds()` / `games_by_seed()` (lines 71-85) with indexed `seed` column queries filtered by `rep = 0`.

Resume, modelled on `interrupt_unfinished` (lines 125-128):
```python
return self._write("UPDATE jobs SET state = 'interrupted', ended_at = ? "
                   "WHERE state IN ('queued', 'running')", (time.time(),)).rowcount
```
`resume(job_id)`: same style, `WHERE id = ? AND state = 'interrupted'` setting `state='queued', ended_at=NULL`.

**Test analog:** `tests/test_bench_store.py` lines 1-30 (`Store(tmp_path / "r.db")`, `_game(**extra)` helper, `pytest.raises`, reopening test).

### `bench/scheduler.py` (explicit seed ranges, contiguous-prefix looks)

**Analog:** itself. Spots to change (verified lines):
- docstring lines 3-4 ("seeds 0 .. N-1") and `_targets()` (120-125), `_played()` (165-167), `_wanted()` (169-176) all use `range(target)`; replace with `spec["seeds"] = {lo, hi}`.
```python
def _wanted(self):
    for sha, target in self._targets():
        taken = self.store.seeds(sha) | self._inflight[sha]
        for seed in range(target):
            if seed not in taken:
                return sha, seed
```
- `_judge()` (127-163) pairs by `range(need)` with `try/except KeyError  # a game without the metric's field`; keep that, swap `judge_paired` for the new sequential test fed contiguous prefixes only.
- `_dispatch()` (178-198): add the range assert before `slot.worker.play(seed)`; error handling pattern `except (OSError, ValueError) as e: self._worker_died(...)`.

**Test analog:** `tests/bench_fakes.py` (`FakeWorker(sha, make, log, seeded=True)`, `game(depth)`) with `tests/conftest.py::run_until_idle`.

### `bench/server.py` (`start_baseline`, `start_experiment`, resume) and `bench/mcp_server.py`

**Analog:** itself. Server (lines 33-60):
```python
def start_baseline(self, ref="main", games=576):
    games = int(games)
    if games < 1:
        raise ValueError("games must be at least 1")
    sha, subject = self._sha(ref)
    with self.lock:
        return {"job_id": self.scheduler.submit(
            "baseline", {"ref": ref, "sha": sha, "subject": subject, "games": games})}
```
Validation = `raise ValueError(...)` before `with self.lock`; spec dict stored via `scheduler.submit`. Add `seeds`, `env`, `declared` (mde required) to the spec the same way. MCP tool style (`bench/mcp_server.py` ~lines 72-79):
```python
@mcp.tool()
def bench_experiment(candidate: str, baseline: str = "main", metric: str = "dlvl6") -> dict:
    """A/B experiment ... Returns job_id; ..."""
    return _call("POST", "/api/jobs", {"kind": "experiment", ...})
```
New tools `bench_resume`, `bench_power`, `bench_funnel` copy this: docstring + `_call(METHOD, path, body/query)`. Do not expose `clean_attempt` creation here.

### `bench/worker.py` (lgen) and `nethack_screensaver/game.py`

**Analog:** itself. Worker (lines 15-40): protocol parse accepts `play [seed]`; backward-compat idiom:
```python
can_seed = "seed" in inspect.signature(run_game).parameters  # older commits cannot
...
result = asdict(run_game(watchdog_seconds=120, seed=seed))
```
Extend `parse()` to `play <seed> [lgen]`, gate on `"lgen" in inspect.signature(run_game).parameters`. Worker must not import `bench`.
`game.py`: add `lgen: int | None = None` to `GameResult` next to `seed` (line 65, comment style `# ...`, default keeps old log lines loadable) and pass at line 317:
```python
type(env.nethack).set_initial_seeds(env.nethack, seed, seed, False)   # add lgen=...
```
Never pass `lgen=0` (means off); use `seed + LGEN_OFFSET`.

### `bench/provenance.py`

**Analog:** `bench/gitrefs.py` (subprocess git wrapper) and `bench/runner.py` (worker interpreter subprocess, env). Copy their subprocess-call style; run `WORKER_PYTHON -I -c ...` reading `importlib.metadata.distribution("nle").read_text("direct_url.json")` (RESEARCH Pattern 1). Server must not import `nle`.

### `bench/toolruns.py` + `scripts/staged_run.py`, `scenario_run.py`, `rewind.py` (`--record`)

**Analog:** `scripts/replay_check.py` lines 1-30: opens store via `from bench.cli import DATA, REPO` / `from bench.store import Store`, argparse, exit codes documented in the docstring, field-list constant `FIELDS`, `SHOW` constant. Copy this CLI skeleton. Scripts print one JSON line per result (`print(json.dumps(asdict(r)))`, per CLAUDE.md) and add the job ID line.

### `scripts/facts.py`, `scripts/sim_sequential.py`

**Analog:** `scripts/replay_check.py` (docstring-with-usage, argparse, exit-code contract). `facts/FACTS.toml` loading: `tomllib` as in `nethack_screensaver/config.py` (binary-mode `open(path, "rb")`). `sim_sequential.py` prints JSON lines; fixed RNG seeds.

### `scripts/check_claims.py` (Stop hook) and `.claude/settings.json`

**No in-repo analog** (no existing hook script; `.claude/settings.json` does not exist). Use RESEARCH Pattern 12 (hook JSON contract, read-only sqlite URI `file:<db>?mode=ro`, `set_authorizer`, `git cat-file -e <40hex>^{commit}`). Stdlib only, runs under any `python3`, crash-safe exit 0 plus audit log `.claude/claim-checks.jsonl` (gitignore it). Borrow only: narrow `except (OSError, ValueError):  # <why>` style from `bench/importers.py`, and read-only DB open pattern from `scripts/replay_check.py`. Tests: `tests/data/claims_*.txt` corpus; test style from `tests/test_bench_store.py`.

### `tests/test_facts.py`

Citations are comments `# fact:<id>`; test greps `autoascend/`, `nethack_screensaver/`, `bench/` and asserts ids exist in `facts/FACTS.toml`. Skip source-quote checks when `reference/` is absent (`pytest.mark.skipif`). Style analog: `tests/test_imports.py` / `tests/test_config.py` (flat functions, `tmp_path`).

### Sokoban detector test

**Analog:** `tests/test_ladder.py` (existing detector tests; `Ladder.observe(Facts...)`), detector at `autoascend/ladder.py:83-84, 111-112`, fixtures `tests/data/soko_real_*.json`. Add a case that feeds a solved top-level (`(SOKOBAN, 1)`, `SOKOBAN_DRAWN` squares, trap seen then none left) and asserts `sokoban_solved` fires once.

## Shared Patterns

### Pure-logic modules, one-way dependencies
**Source:** `bench/stats.py`, `autoascend/ladder.py` ("standard library only"). **Apply to:** `seeds`, `funnel`, `sequential`, `power`. No game imports; the worker never imports `bench`.

### Narrow exceptions with a reason comment
**Source:** `bench/scheduler.py` (`except KeyError:  # a game without the metric's field`), `bench/importers.py`. **Apply to:** all new code; no bare `except`.

### Validation before lock, state under lock
**Source:** `bench/server.py` `start_*`. **Apply to:** all new `App` methods (ValueError for bad input).

### Store writes through `_write`, reads through `_one/_all`
**Source:** `bench/store.py:50-62`. **Apply to:** all new Store methods (`resume`, `started`, `tool_games` insert).

### Test conventions
**Source:** `tests/test_bench_store.py`, `tests/bench_fakes.py`. Flat `test_<long_behaviour_name>`, `tmp_path` stores, `FakeWorker`; shared helpers imported as top-level modules (`from bench_fakes import ...`).

### Backward-compatible GameResult / worker fields
**Source:** `GameResult` defaults (`game.py:65-68`), `can_seed` (`worker.py:26`). **Apply to:** `lgen` and any new field.

## No Analog Found

| File | Role | Data Flow | Reason |
|---|---|---|---|
| `scripts/check_claims.py` | hook | request-response | No Claude Code hook exists in repo; use RESEARCH Pattern 12 |
| `.claude/settings.json` | config | event-driven | File absent; only `settings.local.json` exists; verify the `command` argument form against hooks docs |
| `facts/FACTS.toml` | data | n/a | New artifact; schema in RESEARCH Pattern 13 |

## Metadata

**Analog search scope:** `bench/`, `scripts/replay_check.py`, `tests/`, `nethack_screensaver/game.py`
**Files read:** `bench/{stats,store,scheduler,server,mcp_server,worker,metrics}.py` (partial), `tests/{bench_fakes,test_bench_stats,test_bench_store}.py`, `scripts/replay_check.py`
**Pattern extraction date:** 2026-11-12

## Additions (plan revision, 2026-11-12)

Files the plans create that the first mapping did not list. Paths checked with `git ls-files`; new files are marked as such.

| New File | Role | Closest Analog | Match | Notes |
|---|---|---|---|---|
| `scripts/fresh_clone_check.py` (new) | utility (CLI) | `scripts/replay_check.py` (docstring with usage and exit codes, argparse) plus `bench/gitrefs.py` (`subprocess.run` git wrapper, ValueError on failure) | partial | No in-repo script clones the repo or runs `uv sync`; copy the CLI skeleton and the subprocess style only |
| `scripts/play_compare.py` (new) | utility (CLI, batch) | `scripts/staged_run.py` (one subprocess per game, `ThreadPoolExecutor`, JSON result line, `seeds()` range parser) and `bench/runner.py` (worker env: `PYTHONPATH`, `PYTHONHASHSEED=0`, single-thread BLAS, `fixed_clock.preload_env`) | role-match | Field list copied from `scripts/replay_check.py` `FIELDS` |
| `scripts/lgen_pilot.py` (new) | utility (CLI, analysis) | `scripts/seeded_report.py` (`pairs` command: per-seed pairing of two commits with a METRICS function) and `scripts/replay_check.py` (store reads, JSON output) | role-match | Statistics from `bench/sequential.py` and `bench/stats.py`; no copy of interval code |
| `facts/FACTS.toml` (new) | data | none | no analog | Only the loading pattern exists: `nethack_screensaver/config.py` reads TOML with `tomllib` in binary mode |
| `tests/fake_logic.py` (new) | test helper | `_fake_logic` in `tests/test_ladder.py` (moved here) and `tests/bench_fakes.py` (plain-module helper convention) | exact | Imported as `from fake_logic import fake_logic` |
