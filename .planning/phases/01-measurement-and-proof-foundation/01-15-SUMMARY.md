---
phase: 01-measurement-and-proof-foundation
plan: 15
subsystem: bench
tags: [lgen-pilot, decision, baseline, a-a, pre-registration]

requires:
  - phase: 01-14
    provides: pilot pre-registration (09b79fbb306764b9fae898b2c00a2e22158e4587) and pilot jobs 3-6
provides:
  - "scripts/lgen_pilot.py (0ad1c14) and its result for jobs 3/4/5/6 in 01-LGEN-PILOT.md"
  - "decision keep-lgen-off; bench.seeds.USE_LGEN = off; bench.power.DEFAULT_DISCORDANCE = 0.019 (14493a5b56cda92bb0ecb9eb3bcff3356f0d5217)"
  - "scripts/replay_check.py A/A options --rep-a/--rep-b, --lo/--hi, --lgen, --skip-both, --json (9c9ada2)"
  - "01-BASELINE.md pre-registered in 539b31eabc1b11c90f7f2b84cb5348a0acf1da63; baseline job 7 started, A/A job 8 queued"
affects: [01-16 proof index, Phase 2 experiments (baseline_sha e5b5a7f525bc51b8008f665173600aba80de466d)]

actuals:
  tasks: 3
  commits: 7     # MEASURED: 5645fda, 0ad1c14, cb117ae, 9c9ada2 (previous session); 14493a5, 539b31e, 8118fd2, cbd307c (this session)
plan_head_before: 02881b0
plan_head_after: cbd307ccc443ac81adcc8f9c72a1988dbf319a80

tech-stack:
  added: []
  patterns:
    - "Decision constants cite the decision record and the job IDs that produced them"

key-files:
  created:
    - scripts/lgen_pilot.py
    - tests/test_lgen_pilot.py
    - .planning/phases/01-measurement-and-proof-foundation/01-BASELINE.md
  modified:
    - bench/seeds.py
    - bench/power.py
    - tests/test_bench_power.py
    - scripts/replay_check.py
    - tests/test_seeded_scripts.py
    - .planning/phases/01-measurement-and-proof-foundation/01-LGEN-PILOT.md

key-decisions:
  - "keep-lgen-off by rule-strict: psi_on - psi_off = +0.005, 95% paired interval [-0.0070, +0.0170], not below 0 (jobs 3/4/5/6)"
  - "DEFAULT_DISCORDANCE 0.019 = Wilson upper bound of psi on dlvl10 with lgen off (b 2, c 0, n 400), rounded up; small because commit B's change is small (Pitfall 11)"

requirements-completed: [MEAS-04]

coverage:
  - id: D1
    description: "Pilot analysed and decided by the pre-registered rule; USE_LGEN and DEFAULT_DISCORDANCE set"
    requirement: MEAS-04
    verification:
      - kind: unit
        ref: "tests/test_lgen_pilot.py (5 passed); Task 1 verify printed 'ok keep-lgen-off 0.019'"
        status: pass
    human_judgment: false
  - id: D2
    description: "A/A comparison command with one-sided watchdog as mismatch"
    requirement: MEAS-05
    verification:
      - kind: unit
        ref: "tests/test_seeded_scripts.py (64 passed)"
        status: pass
    human_judgment: false
  - id: D3
    description: "Baseline and A/A pre-registered before their jobs; baseline job 7 started; A/A job 8 queued; bot of main == bot of A"
    requirement: MEAS-05
    verification:
      - kind: integration
        ref: "Task 3 verifies printed 'ok 7 8' and 'ok: bot of main == bot of e5b5a7f525'"
        status: pass
    human_judgment: false

duration: not measured
completed: 2026-11-13
---

# Phase 1 Plan 15: lgen decision, A/A command, baseline start Summary

**The lgen pilot (jobs 3, 4, 5, 6; 400 paired seeds each, 0 unpaired) decided keep-lgen-off under rule-strict. Discordance on dlvl10 was 2 of 400 with lgen off and 4 of 400 with lgen on. The paired difference +0.005 has the 95% interval [-0.0070, +0.0170], which is not below 0. The 10,000-game natural baseline of commit e5b5a7f525bc51b8008f665173600aba80de466d is job 7: it started with its first game row at 2026-11-13 16:10:02 and reused 400 games. The A/A rerun is job 8: queued, not started.**

## Task Commits

1. **Task 1:** tests 5645fda, script 0ad1c14 (previous session); decision and constants 14493a5b56cda92bb0ecb9eb3bcff3356f0d5217
2. **Task 2:** tests cb117ae, implementation 9c9ada2 (previous session)
3. **Task 3:** pre-registration 539b31eabc1b11c90f7f2b84cb5348a0acf1da63, prereg_commit line 8118fd2, job record cbd307ccc443ac81adcc8f9c72a1988dbf319a80

## Deviations from Plan

**1. [Rule 1 - test pinned the old value] tests/test_bench_power.py asserted DEFAULT_DISCORDANCE is None**
- That test was a placeholder until the pilot. It now asserts 0.019 and cites the jobs. 64 tests passed (power, server and pilot).

**Total deviations:** 1. **Impact:** none on scope.

## Concern for the owner

DEFAULT_DISCORDANCE 0.019 is very small because commit B rarely changed dlvl10 (2 flips in 400 seeds). Experiments sized with it assume few games diverge. A change that diverges games more (most Phase 2 changes) should pass an explicit --discordance, otherwise it will be undersized. 31% of seeds already differ somewhere in the full result, even though dlvl10 rarely flips.

## Next Phase Readiness

Plan 01-16 needs job 7 and job 8 done: about 5.4 h for the baseline's 9,600 own games plus about 1.1 h for the A/A, at the measured 29.75 games per minute. After a reboot: `uv run screens-bench serve --resume`.

## Self-Check: PASSED
