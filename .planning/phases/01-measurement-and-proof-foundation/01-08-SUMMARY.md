---
phase: 01-measurement-and-proof-foundation
plan: 08
subsystem: bench
tags: [seed-windows, store-schema-2, migration, env-fingerprint, lgen, replicate, mcp]

requires:
  - phase: 01-01
    provides: bench/provenance.py (env_fingerprint, env_id, lock_blob)
  - phase: 01-05
    provides: ProcessWorker.play(seed, lgen=) and the 'play <seed> <lgen>' protocol
provides:
  - "bench/seeds.py: DEV, CONFIRM, FINAL_LO, TOOL, BASELINE_WINDOW, AA_WINDOW, LGEN_OFFSET, USE_LGEN, LGEN_MODES, NATURAL_KINDS, TOOL_KINDS, range_of, window, lgen_for"
  - "Store schema 2: games columns seed, lgen, env_id, rep (indexed games_by_key), envs table, in-place migration of schema-1 files"
  - "Keyed store reads: seeds, played, games_by_seed, games, count with (lo, hi, lgen_mode, env_id, rep)"
  - "Scheduler fills the spec's half-open window [lo, hi) in ascending order under the job key (lgen mode, env_id, rep); lgen dispatch; fails jobs whose worker cannot echo lgen"
  - "App(env=...) records env_id, env and lock blobs in every job; start_baseline(lo, hi, lgen, replicate), start_experiment(lo, lgen)"
  - "MCP bench_baseline(lo, hi, lgen, replicate); cli build_app fingerprints the worker interpreter once"
affects: [01-10 seed-range policy, 01-11 job lifecycle, 01-12 funnel, 01-13 sequential experiments, 01-14 baseline and A/A, 01-15 lgen pilot]

actuals:
  tasks: 2
  commits: 3     # MEASURED: git rev-list --count 684116f..994f74a before the SUMMARY commit
plan_head_before: 684116f8db369b02890e8cc46656d85b8e82703f
plan_head_after: 994f74a1ebf45c4c328c3667e0a0775652095ef7

tech-stack:
  added: []
  patterns:
    - "Game key = (sha, seed, lgen IS NULL, env_id, rep); every reuse and pairing query filters on it; None for lgen_mode/env_id means no filter, rep defaults to 0"
    - "Schema migration runs inside the constructor before the key index is created (the index needs the new columns)"

key-files:
  created:
    - bench/seeds.py
  modified:
    - bench/store.py
    - bench/scheduler.py
    - bench/server.py
    - bench/cli.py
    - bench/mcp_server.py
    - tests/bench_fakes.py
    - tests/test_bench_store.py
    - tests/test_bench_scheduler.py
    - tests/test_bench_server.py
    - tests/test_bench_mcp.py

key-decisions:
  - "A job's key is computed once when the job starts and stored on each slot at dispatch, so results are written under the key they were played for"
  - "Job specs without a seed window (older bench) fail on start with a message, instead of guessing 0..N-1"
  - "Store.shas() counts rep 0 rows only, like every summary read"
  - "Experiments default to the baseline window start (1000) and span CHECKPOINTS[-1] seeds"

requirements-completed: [MEAS-07, MEAS-05, MEAS-01, MEAS-04]

coverage:
  - id: D1
    description: "Explicit half-open seed windows, ascending order, bad windows refused, old specs refused"
    requirement: MEAS-07
    verification:
      - kind: unit
        ref: "tests/test_bench_scheduler.py::test_a_baseline_window_plays_exactly_its_seeds_in_ascending_order, ::test_a_job_spec_without_a_seed_window_fails; tests/test_bench_server.py::test_empty_or_bad_windows_are_refused"
        status: pass
    human_judgment: false
  - id: D2
    description: "Schema 2 with indexed key columns, schema-1 migration with seed backfill, env table"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_bench_store.py::test_a_schema_1_database_is_migrated_with_the_seed_backfilled, ::test_keyed_reads_use_the_window_env_and_replicate, ::test_environments_are_stored_by_id"
        status: pass
    human_judgment: false
  - id: D3
    description: "Job spec records seeds, env_id, env and lock blob"
    requirement: MEAS-01
    verification:
      - kind: unit
        ref: "tests/test_bench_server.py::test_a_baseline_on_a_window_records_seeds_env_and_lock_blob"
        status: pass
    human_judgment: false
  - id: D4
    description: "lgen modes kept apart (8 rows for 4 seeds), lgen = seed + 10,000,000, replicate rows out of reads, lgen-incapable commit fails, MCP forwards parameters"
    requirement: MEAS-04
    verification:
      - kind: unit
        ref: "tests/test_bench_scheduler.py (Task 2 tests), tests/test_bench_server.py (lgen/replicate validation), tests/test_bench_mcp.py::test_bench_baseline_forwards_window_lgen_and_replicate"
        status: pass
    human_judgment: false

duration: 6 min
completed: 2026-11-12
---

# Phase 1 Plan 08: Seed windows, game key and env recording Summary

**Bench jobs now play an explicit seed window and store each game under its full key: commit, seed, lgen mode, NLE environment and replicate. Every job records the environment fingerprint and the commit's `uv.lock` blob. A schema-1 database is migrated in place with its seeds backfilled.**

## Performance

- **Duration:** 6 min (measured between start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 2 (tracer, TDD)
- **Executed:** inline in the main session (no executor subagent)

## Accomplishments

- `bench/seeds.py` with the D-07/D-17 constants, `range_of`, `window`, `lgen_for`.
- Store schema 2 and `_migrate_v1()`; keyed reads on indexed columns. `json_extract(json, '$.seed')` is left only in the backfill (`grep -c` = 1).
- Scheduler: windows, ascending order, job key, lgen dispatch, lgen-incapable commits fail the job.
- Server, CLI and MCP take and record windows, lgen mode, replicate and env.

## Task Commits

1. **Task 1 (tracer):** `827e108`
2. **Task 2 (TDD):** RED `0276c46`, GREEN `994f74a`

## TDD Gate Compliance

Task 2 RED `0276c46`: 4 failed (FakeWorker had no `lgen` parameter, MCP `bench_baseline` had no window/lgen/replicate). The replicate test and the server lgen/replicate validation tests already passed at RED, because the scheduler key and the server validation were written with Task 1 (see deviation 1). GREEN `994f74a`: 46 passed in the three files.

## Deviations from Plan

**1. [Process] Task 2's scheduler and server logic landed in the Task 1 commit**
- The job key (lgen mode, env_id, rep), the lgen dispatch and the lgen-incapable check are computed in the same places Task 1 rewrote (`tick`, `_dispatch`, `_collect`), and the server validation sits in the same new `start_baseline`. Writing them once avoided rewriting those functions twice. Task 2's RED therefore failed only on the test double and the MCP tool; the other Task 2 tests are regression tests for code from `827e108`.

**2. [Rule 2 - Missing critical] `Store.shas()` reads rep 0 only**
- Not in the plan's list, but replicate rows must stay out of every summary read; `shas()` feeds per-commit game counts.

**3. [Process] Existing scheduler tests use window [0, N)**
- Their specs were converted with a `_bspec` helper whose window starts at 0, so their meaning is unchanged; the new tests use 1000-based windows.

**Total deviations:** 3. **Impact:** none on scope.

## Threat Flags

T-01-15 mitigated: `window()` coerces with `int()`, requires 0 <= lo < hi; lgen and replicate are allow-listed. T-01-16 mitigated: env_id and lgen mode are in every reuse and pairing query. T-01-17 mitigated: the migration only adds columns and backfills; tested on a schema-1 file. The live `results.db` is migrated the next time the bench server starts.

## Issues Encountered

None.

## Verification output

- `tests/test_bench_store.py tests/test_bench_scheduler.py tests/test_bench_server.py tests/test_bench_mcp.py`: pass.
- The plan's store check printed `ok`.
- `tests/test_seeded_scripts.py` (replay_check, seeded_report against schema 2): 58 passed.
- Full non-slow suite at `994f74a`: 759 passed, 6 skipped, 16 deselected.

## User Setup Required

None. The bench server prints `bench env <env_id> nle <commit>` at start.

## Next Phase Readiness

Ready for 01-09 (fact tranche, research notes) and 01-10 (seed-range policy).

## Self-Check: PASSED
