---
phase: 01-midgame-survival
plan: 05
subsystem: measurement
tags: [a/a-control, determinism, replay, bench, fixed-clock]

requires: [01-01, 01-02, 01-03]
provides:
  - "nethack_screensaver/fixed_clock.py: LD_PRELOAD time() shim; seeded games see start time 1_000_000_000 + seed*257"
  - "bench workers: shim loaded, one BLAS/OpenMP thread"
  - "PORTING.md `## Phase 1: seeded pilgrim-only bench` with Determinism (MEAS-03), A/A control and the gate line for e3f0dd7ab7054901d93dab9ef586b50154fb963a"
affects: [01-06, 01-07]

commits: 3
key-files:
  created:
    - nethack_screensaver/fixed_clock.py
    - tests/test_fixed_clock.py
  modified:
    - nethack_screensaver/game.py
    - bench/runner.py
    - scripts/benchmark.py
    - tests/test_game.py
    - tests/test_replay.py
    - tests/test_bench_runner.py
    - autoascend/PORTING.md

key-decisions:
  - "A/A #1 (job 9) failed the D-04 replay gate (44/1149 seeds): NetHack's start time picks shopkeeper names. Stopped and fixed (e3f0dd7) instead of proceeding"
  - "One BLAS thread per worker kept although the gain was +8% (36.2 -> 39.2 games/min), below 01-06's 10% bar: it is inside the gated SHA (reverting needs another A/A) and removes multi-threaded float sums as a replay risk"
---

# Plan 01-05 Summary: seeded A/A control

**Result: gate passed.** `p1-aa-base` (`e3f0dd7`) against its docs-only twin `p1-aa-twin`
(`2c567b5`), job 10, rung2, 1152 seeds per side: no measurable difference, 0.0 [0.0, 0.0];
rung2 26.1% on both sides. Replay check: 1149 seeds compared, 0 mismatched, 3 watchdog seeds
skipped (227, 436, 690).

## What happened

1. A/A #1 (job 9, `be40c7c` vs `6ce5ac5`): verdict fine, replay failed on 44 seeds. 43 differed
   only in shopkeeper names, seed 1127 played a different game. Cause reproduced by faking the
   start time. NLE's `fix_moon_phase` does not pin `u.ubirthday`.
2. Fix `e3f0dd7`: `fixed_clock` LD_PRELOAD shim, pinned per seed in `run_game`; bench workers
   load it and run one BLAS thread. Full suite 408 passed.
3. A/A #2 (job 10): passed as above. Speed 39.2 games/min (job 9: 36.2).
4. PORTING.md record and gate line (`6fdbbf4`).

## Deviations

- Extra fix commit (`e3f0dd7`) and a second A/A run, per D-04 (stop and fix).
- 01-06 Task 0 step 1-2 (thread env and its speed/replay check) are done here: the env shipped
  with the fix, the replay was checked over 1149 seeds instead of 384, speed recorded above.
  Only the turn-cap analysis of Task 0 remains.
