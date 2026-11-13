---
phase: 01-measurement-and-proof-foundation
reviewed: 2026-11-14T00:00:00Z
depth: standard
files_reviewed: 42
files_reviewed_list:
  - autoascend/castle.py
  - autoascend/combat/stair_escape.py
  - autoascend/digging.py
  - autoascend/global_logic.py
  - autoascend/ladder.py
  - autoascend/medusa.py
  - autoascend/passtune.py
  - autoascend/prayer.py
  - autoascend/quest_portal.py
  - autoascend/stats_logger.py
  - autoascend/telepathy.py
  - bench/cli.py
  - bench/funnel.py
  - bench/gitrefs.py
  - bench/mcp_server.py
  - bench/metrics.py
  - bench/power.py
  - bench/provenance.py
  - bench/report.py
  - bench/runner.py
  - bench/scheduler.py
  - bench/seeds.py
  - bench/sequential.py
  - bench/server.py
  - bench/static/index.html
  - bench/stats.py
  - bench/store.py
  - bench/toolruns.py
  - bench/worker.py
  - .gitignore
  - nethack_screensaver/game.py
  - scripts/check_claims.py
  - scripts/facts.py
  - scripts/fresh_clone_check.py
  - scripts/lgen_pilot.py
  - scripts/play_compare.py
  - scripts/replay_check.py
  - scripts/rewind.py
  - scripts/scenario_run.py
  - scripts/seeded_report.py
  - scripts/sim_sequential.py
  - scripts/staged_run.py
findings:
  critical: 3
  warning: 4
  info: 5
  total: 12
status: issues_found
---

# Phase 1: Code Review Report

**Reviewed:** 2026-11-14
**Depth:** standard
**Files Reviewed:** 42 (plus `nethack_screensaver/staging.py`, which changed in the same range)
**Status:** issues_found

## Summary

Bot-side check: an AST comparison of old and new source shows that `castle`, `stair_escape`, `digging`, `medusa`, `passtune`, `prayer`, `quest_portal` and `telepathy` changed in comments only. `ladder.py` and `global_logic.py` changed measurement-side only: new Facts field, new `quest_portal` rung, `SOKOBAN_TRAPS`, and telemetry counters. No play change was found. `lgen` off still calls `play(seed)` with no lgen, so the existing seeds replay as before. `.venv/bin/python -m pytest -q` gives 842 passed, 6 skipped, 16 deselected, and `scripts/facts.py check --source` is clean.

The scheduler's seed-prefix logic, the sequential test and the seed-range guards held up under review. I did not find a way to judge an experiment on a non-contiguous prefix or to store final-range seeds outside clean attempts. The defects are in the read side (summaries pool different game keys), in provenance on resume, and in the claim checker.

## Critical Issues

### CR-01: `/api/results`, `/api/games`, `/api/dashboard` pool games across lgen modes and environments

**File:** `bench/server.py:208-217`, `bench/server.py:225-233`, `bench/store.py:133-134`, `bench/store.py:155-161`
**Issue:** `App.results`, `App.games` and `App.dashboard` call `store.games(sha)` and `store.count(sha)` with no `lgen_mode` and no `env_id`. Only `rep` is filtered. In this bench database the commit `e5b5a7f5...` has 10,000 lgen-off rows (seeds 1000-10999) and 400 lgen-on rows (seeds 1000-1399, pilot jobs 3-6), all with `rep = 0`. So `bench_results(ref=...)`, the dashboard rates, the funnel table and `bench_games` count seeds 1000-1399 twice, under two different dungeons. The owner quotes these numbers as progress, which is exactly the double-counting the key columns were added to prevent. Any future env change adds the same pollution, because rows from another env also pass this read. The new `funnel_for` filters correctly and so disagrees with `/api/results` for the same commit.
**Fix:** Give the read paths the same key as the jobs.
```python
def _natural(self):  # key of this server's natural games
    return {"lgen_mode": seeds.USE_LGEN, "env_id": self.env_id}

games = self.store.games(sha, rep=0, **self._natural())
# same in games() and dashboard(); count(sha, ...) needs the same filters
```
Let `/api/results` and `/api/games` take optional `lgen`, `env_id`, `lo` and `hi` query parameters, as `/api/funnel` does.

### CR-02: Resuming a job tags games with the old `env_id` although the new interpreter played them

**File:** `bench/scheduler.py:89`, `bench/scheduler.py:123`, `bench/server.py:150-166`, `bench/cli.py:41-45`
**Issue:** The game key's `env_id` comes from the job spec (`job["key"]["env_id"] = spec.get("env_id")`), and it is written into every stored game (`add_game(..., env_id=slot.env_id)`). The spec was fixed when the job was created. `serve --resume` and `POST /api/jobs/N/resume` requeue an interrupted job under the same spec without comparing `spec["env_id"]` to the running server's `App.env_id`. After the NLE rebuild or a `uv sync` that made the restart necessary, the resumed job plays with the new interpreter, but every game is stored under the old env_id. Those rows are reused as if they came from the old env and are paired with the old env's games, so the env part of the key can be wrong. The project's own `play_compare.py` exists because an NLE rebuild is a live scenario.
**Fix:** Refuse the resume when the env differs.
```python
def resume(self, job_id):
    job = ...
    if job["spec"].get("env_id") != self.env_id:
        raise ValueError(f"job {job['id']} was created under env {job['spec'].get('env_id')}, this server runs "
                         f"{self.env_id}; start a new job")
```
Do the same check in `cli._serve` for `--resume`, and check it again in `Scheduler.tick` as a guard.

### CR-03: The claim checker skips any sentence containing a future or conditional word, so an unproven claim next to one passes

**File:** `scripts/check_claims.py:71-72`, `scripts/check_claims.py:99`
**Issue:** `FUTURE_RE` includes `can|may|if|once|until|next|I'll|we'll|should`, and `find_claims` drops the whole sentence when any of them appears. A sentence has no boundary at `;` or `,`, so the claim and the future clause hide each other. Verified against the code (an empty-proof run of `run()`):
- `"I started the bench run, which can take an hour."` gives no claim and the reply passes.
- `"Job 7 has started; next I'll check the funnel."` gives no claim, whatever job 7 is.

These are the usual handoff phrasings, so the tripwire is silent in the commonest case. A start claim of this form needs no proof at all.
**Fix:** Apply the future test to the clause around the claim verb, not the sentence. Split on `[;,]` and on " and "/" but ", and test each clause. Keep only forward-looking auxiliaries (`will|would|going to|plan to|about to|I'll|we'll|let me`) as exemptions, and drop `can|may|if|once|until|next` from the exemption list, since they usually modify another clause.
```python
_CLAUSE_RE = re.compile(r"[;,]\s+|\s+(?:and|but|which)\s+", re.I)
for clause in _CLAUSE_RE.split(sentence):
    if clause.endswith("?") or FUTURE_RE.search(clause):
        continue
    ...
```

## Warnings

### WR-01: A resumed tool job wedges the scheduler

**File:** `bench/scheduler.py:78-93`, `bench/scheduler.py:148-150`, `bench/store.py:233-245`, `bench/cli.py:41-47`
**Issue:** Tool runs (`staged`, `scenario`, `rewind`) are stored as jobs with `spec["seeds"]` as a list. If the script is killed, the job stays `running`. At the next `serve`, `interrupt_unfinished` marks it `interrupted`, and `serve --resume` (or `POST /api/jobs/N/resume`) requeues every interrupted job, tool jobs included. `tick()` then accepts it (`"seeds" in spec` is true), sets it `running`, and `_judge` calls `self._window()`, which does `seeds["lo"]` on a list and raises TypeError on every tick. The job stays `self.job`, so no other job is dispatched until someone calls stop. Reproduced with a `toolruns.record_run` job followed by `interrupt_unfinished`, `resume` and `Scheduler.tick()`: the TypeError repeats on every tick and `sch.job` stays set. The loop in `App.loop` swallows the error into `scheduler.error`.
**Fix:** Resume only natural kinds, and have the scheduler fail non-natural jobs.
```python
# Store.resume: ... WHERE id = ? AND state = 'interrupted' AND kind IN ('baseline', 'experiment')
# Scheduler.tick, after next_queued():
if job["kind"] not in seedlib.NATURAL_KINDS:
    self.store.set_job(job["id"], "failed", {"error": f"{job['kind']} jobs are not run by the scheduler"})
    return
```

### WR-02: The claim checker accepts proofs that prove nothing

**File:** `scripts/check_claims.py:122-143`, `scripts/check_claims.py:161-189`, `scripts/check_claims.py:58-62`
**Issue:** Four ways to pass an unproven claim, each checked against the code:
1. A self-satisfying query is valid proof: `Job 7 finished and the baseline improved to 80%. [query: SELECT 1 => 1]` passes. The query need not read any table or relate to the claim.
2. A result claim ("passed", "finished", "improved") with any existing job passes. `verify_job` with `need_started=False` checks only that the id exists, not the job's state (`done`/`failed`/`running`) and not that it is the job the sentence is about. `Job 8 passed, rate rose to 12%. see job 1` passes.
3. A result claim's numbers are never compared with the stored results.
4. Start words miss common forms: "began", "submitted", "kicked-off", "spawned", "starting". "I submitted job 12 and the run began." yields no claim.

**Fix:** Require a query proof to read `games`, `jobs` or `tool_games` (check the authorizer's SQLITE_READ table name and reject queries that read none). For a result claim, require the cited job's state to be `done`, and compare a cited number with the query result. Extend `START_WORDS` with `began|begun|submitted|spawned|starting|kicked-off`.

### WR-03: `replay_check.py` can report an A/A as identical when it compared a game to itself, or across lgen modes and envs

**File:** `scripts/replay_check.py:60-69`
**Issue:** The 01-15 A/A evidence ("1999/1999 identical") comes from this script. Three gaps:
- `replay_check A A` with the default `--rep-a 0 --rep-b 0` resolves both sides to the same rows and reports every field identical, with exit 0. Nothing refuses the same sha under the same rep.
- `--lgen` defaults to "any", so `games_by_seed` takes the first row per seed by id regardless of lgen mode. On the sha with both modes stored (see CR-01) the two sides can be paired across modes.
- There is no `env_id` option at all, so a rep-0 game from one env and a rep-1 game from another are paired silently, and an env-change A/A would not show up as a key mismatch.

**Fix:** Refuse `sha_a == sha_b and rep_a == rep_b`. Make `--lgen` required (or default to `seeds.USE_LGEN`). Add `--env-a/--env-b`, defaulting to the env of the stored rows, and refuse to compare rows whose env differs unless asked to.

### WR-04: `scripts/facts.py check` never runs `measured` queries and passes silently when the bench DB is absent

**File:** `scripts/facts.py:191-209`, `scripts/facts.py:79-84`
**Issue:** A `measured` fact needs only a `job` integer and/or a `query` string. `_check_measured_jobs` checks only that the job id exists, and only when `~/.local/share/screens-bench/results.db` exists. It ignores `SCREENS_BENCH_DATA`, which `check_claims.py` honours. A fact with just a `query` is never executed, so a measured fact with a made-up query passes. When the DB is missing it prints a notice and returns no errors, so `check` exits 0 with all measured jobs unverified. If the schema lacks a `jobs` table, `sqlite3.OperationalError` is not caught.
**Fix:** Run each `measured` query read-only and compare its first cell with an `expected` field, like `check_claims.verify_query`. Use the same data-dir resolution as `check_claims._paths`. Exit non-zero (or require `--allow-missing-db`) when measured facts exist and the DB cannot be read. Catch `sqlite3.Error`.

## Info

### IN-01: `quest_portal_found` in Facts is not limited to the Dungeons of Doom

**File:** `autoascend/global_logic.py:613-617`, `autoascend/global_logic.py:749-759`, `autoascend/ladder.py:93`
**Issue:** `_update_portal` guards the telemetry event with `level.dungeon_number == Level.DUNGEONS_OF_DOOM`. The Facts field `quest_portal_found=self._quest_portal_found_here(level)` has no such guard. The vault portal to Fort Ludios also shows `S_magic_portal`, and the message `You activated a magic portal!` is shared, so a bot that enters Ludios would be credited with the `quest_portal` rung. `grep -i ludios autoascend/*.py` shows no code that goes there deliberately, so this is rare and affects only the measurement.
**Fix:** In `ladder.py` use `(f.quest_portal_found and f.dungeon == DOOM) or f.dungeon == QUEST`.

### IN-02: The documented `mde` example fails at the default discordance

**File:** `bench/power.py:39-41`, `bench/mcp_server.py` (`bench_experiment`, `bench_power` docstrings), `bench/cli.py` (`power --mde` help)
**Issue:** The docs and CLI help say "MDE (smallest effect worth detecting, e.g. 0.03)". `power._check` requires `mde <= psi`, and `DEFAULT_DISCORDANCE` is 0.019, so `--mde 0.03` raises `ValueError` unless `--discordance` is also passed. `cli._power` does not catch it and prints a traceback.
**Fix:** Change the example to a value at or below 0.019, or say that a larger mde needs a larger `discordance`. Catch `ValueError` in `_power` and print `{"error": ...}` with exit 2, as `_funnel` does.

### IN-03: `facts.py` accepts degenerate source quotes

**File:** `scripts/facts.py:105-143`
**Issue:** A quote of only whitespace is truthy, so `entry.get("quote")` passes the "needs a quote" rule, and then `quote = _normalise(...)` is empty, so `if quote and not found` never fires and no source match is checked. A one-character quote matches almost any cited range.
**Fix:** Require `len(_normalise(quote)) >= 12` (or similar) in `_entry_errors`.

### IN-04: `screens-bench wait` exits 0 for `interrupted` and `stopped` jobs

**File:** `bench/cli.py:67-70`
**Issue:** `END_STATES` now includes `interrupted`, and `_wait` returns 1 only for `failed`. A background `wait` for a job whose server restarted therefore reports success to the caller.
**Fix:** Return 0 only for `done`; return 3 for `interrupted` and `stopped`.

### IN-05: `scripts/lgen_pilot.py` pairs games with `{g["seed"]: g}`, which keeps the last duplicate and fails on a game with no seed

**File:** `scripts/lgen_pilot.py:42-47`
**Issue:** `Store.games_by_seed` keeps the first row per seed, but `pair_by_seed` builds a dict from a list, so a duplicate row for a seed resolves to the last one. A row without a `seed` key raises KeyError. In the current DB the windows are clean, so this does not bite today.
**Fix:** Use `store.games_by_seed(...)` for the pairing, or `setdefault` plus `g.get("seed")`.

---

_Reviewed: 2026-11-14_
_Reviewer: Claude (gsd-code-reviewer)_
_Depth: standard_
