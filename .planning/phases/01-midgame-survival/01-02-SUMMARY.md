---
phase: 01-midgame-survival
plan: 02
subsystem: testing
tags: [sokoban, determinism, bench, pythonhashseed]

requires: []
provides:
  - "solve(..., max_seconds=None) means no wall-clock deadline in the Sokoban solver"
  - "SOKOBAN_LIVE_MAX_STATES = 40,000 used by the live solver, measured at 8.4 s worst case"
  - "Bench workers start with PYTHONHASHSEED=0"
affects: [01-05]

actuals:
  tokens: 2200
  tasks: 2
  commits: 2
plan_head_before: 704a1531769f6b6f1c6ef136c1965deaa0b4a708
plan_head_after: 40f9a812635a6d13b403f02a5df518637b0c04a8
commits: 2

tech-stack:
  added: []
  patterns:
    - "Deterministic budget (state count) instead of wall clock for anything that changes game actions"

key-files:
  created: []
  modified: [autoascend/soko_solver/search.py, autoascend/global_logic.py, tests/test_soko_search.py, bench/runner.py, tests/test_bench_runner.py]

key-decisions:
  - "SOKOBAN_LIVE_MAX_STATES = 40,000: largest of 20k/30k/40k/50k that stays under 10 s on the worst board (soko3-2 minus spare boulders: 8.4 s; 50k took 10.6 s)"
  - "The no-deadline budget applies to all games (bench and screensaver), so worst case stays near 10 s, inside both screen watchdogs"

requirements-completed: [MEAS-03]

coverage:
  - id: D1
    description: "Live Sokoban solving stops on a fixed state budget only; same pushes under any load"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_soko_search.py#test_no_wall_clock_limit_gives_the_same_pushes_under_load"
        status: pass
      - kind: unit
        ref: "tests/test_soko_search.py#test_state_budget_alone_ends_an_unsolvable_search"
        status: pass
    human_judgment: false
  - id: D2
    description: "Live budget worst case stays near the old 10 s limit (measured, recorded beside the constant)"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_soko_search.py#test_live_budget_stays_within_the_old_time_limit"
        status: pass
    human_judgment: false
  - id: D3
    description: "Bench workers run with PYTHONHASHSEED=0"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_bench_runner.py#test_worker_runs_with_a_fixed_hash_seed"
        status: pass
    human_judgment: false

duration: 9min
completed: 2026-10-23
status: complete
---

# Phase 1 Plan 02: Deterministic Sokoban budget and hash seed Summary

**The live Sokoban solver now stops only on a 40,000-state budget (measured 8.4 s worst case, no `time.monotonic` deadline), and bench workers are pinned to `PYTHONHASHSEED=0`, removing the last load and hash-seed influences on a seeded game.**

## Performance

- **Duration:** 9 min (about 16:24Z to 16:33Z)
- **Tasks:** 2 of 2
- **Files:** 5 modified

## Accomplishments

- `solve(max_seconds=None)` uses a deadline of `math.inf`; defaults (300,000 states, 10.0 s) are unchanged, so existing callers and tests behave as before.
- Measurement on the idle-ish machine (load average about 1.6) for soko3-2 minus spare boulders, `max_seconds=None`: 20,000 states 3.7 s, 30,000 5.8 s, 40,000 8.4 s, 50,000 10.6 s. 40,000 is the largest at or under 10 s. Recorded next to the constant in `global_logic.py`.
- `_solve_live_sokoban` passes `max_states=SOKOBAN_LIVE_MAX_STATES, max_seconds=None`.
- Worker env is `{**os.environ, "PYTHONPATH": ..., "PYTHONHASHSEED": "0"}`; the test sets a different value in the server environment and sees "0" in the child. It failed before the change (RED) and passes after.
- The load test discriminates: with a clock jumping 1000 s per call, the default time limit makes soko3-1 return None, while `max_seconds=None` returns the same pushes as the unpatched run.
- Other boards at 40,000 states (idle): soko1-1 5.7 s, soko1-2 4.0 s, soko3-2 6.4 s (unmodified), soko2-1 1.2 s; all unsolved from the start as before (they rely on stored solutions). soko2-2, 3-1, 4-1, 4-2 solve in under 1 s.

## Task Commits

1. Task 1 (tracer): measured state budget, no wall clock - `c490948`
2. Task 2: PYTHONHASHSEED=0 for workers - `40f9a81`

## Verification

- `uv run pytest -q -m ""`: 271 passed, 5 skipped, 5 xfailed, 1 xpassed.
- `uv run pytest -q tests/test_soko_search.py -k "wall_clock or state_budget or live_budget"`: 3 passed.
- `uv run pytest -q tests/test_bench_runner.py`: 6 passed (including the hash seed test).
- `git log --format=%h 704a153..HEAD -- pyproject.toml uv.lock` prints nothing (no new package, T-01-SC).
- Acceptance greps: `SOKOBAN_LIVE_MAX_STATES = ` (one line with measured seconds), `max_seconds=None` in `_solve_live_sokoban`, `"PYTHONHASHSEED": "0"` in `bench/runner.py`.

## Deviations from Plan

**1. [Rule 1 - Bug in plan] Test level soko2-1 replaced by soko3-1**
- **Found during:** Task 1
- **Issue:** The plan's test used `solve(*LEVELS["soko2-1"])` as the expected result, but soko2-1 is not solvable from the start within any budget (returns None; it is one of the stored-solution levels marked xfail). The assertion `expected is not None` failed and, without it, the test would be vacuous (None equals None).
- **Fix:** Used soko3-1 (277 pushes in about 0.5 s), which solves quickly and makes the test meaningful.
- **Files modified:** tests/test_soko_search.py
- **Commit:** c490948

**Total deviations:** 1 auto-fixed (test level choice). **Impact:** none on behaviour; the behaviour under test is the same.

## Issues Encountered

None. The bench server was not restarted (per plan); the hash seed pin takes effect when plan 01-05 restarts it from `main`.

## Known Stubs

None.

## Threat Flags

None. T-01-03 mitigated (budget measured, test asserts under 20 s, far below the 60 s / 120 s watchdogs); T-01-04 accepted; T-01-SC clean.

## Next Phase Readiness

Ready for the next plan. Games that reach Sokoban no longer depend on machine load; a smaller budget means very large boards that used to be solved in 10 s on an idle machine only up to 40,000 states, but those boards (soko1-1, 1-2, 2-1, 3-2 from scratch) already needed the stored solutions.

## Self-Check: PASSED

- FOUND: autoascend/soko_solver/search.py, autoascend/global_logic.py, tests/test_soko_search.py, bench/runner.py, tests/test_bench_runner.py
- FOUND commits: c490948, 40f9a81
