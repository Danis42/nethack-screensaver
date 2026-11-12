---
phase: 01-measurement-and-proof-foundation
plan: 02
subsystem: testing
tags: [mcnemar, msprt, sequential-test, power-analysis, scipy, simulation, bench-statistics]

requires:
  - phase: none
    provides: statistics module stands alone (stdlib, numpy, scipy only)
provides:
  - "bench/sequential.py: exact McNemar, Beta(1,1) mixture log likelihood ratio, judge_sequential verdict (better | worse | no detectable effect >= MDE | open), contiguous_prefix"
  - "bench/power.py: exact McNemar power and MDE, deterministic simulated sequential power, MDE and sample size, plan() declaration dict"
  - "scripts/sim_sequential.py and the committed report 01-SIM-SEQUENTIAL.json: false-positive rate under repeated checking, next to the legacy design"
  - "bench.stats.wilson no longer divides by zero at n = 0; the checkpoint judges are marked descriptive only"
affects: [01-13 scheduler and experiment API wiring, 01-15 lgen pilot (sets DEFAULT_DISCORDANCE), Phase 2 experiments]

actuals:
  tokens: 8230   # chars/4 over the realized diff: 29482 chars of code and tests plus 3434 chars of report
  tasks: 3
  commits: 5     # MEASURED: git rev-list --count bfdc221..b410f5f before the SUMMARY commit
plan_head_before: bfdc221853e581adc115825358e3ed50e4781c16
plan_head_after: b410f5fb9d4b97c8ad576395aecb0e595c489be6

tech-stack:
  added: []
  patterns:
    - "Decisions use looks at contiguous seed prefixes only; the verdict walks cumulative (n, b, c) looks and stops at the first log LR >= log(1/alpha)"
    - "Simulated power uses per-block RNG streams ([seed, block]) and inverse-CDF draws, so it is deterministic, prefix-consistent in n and rises with delta"

key-files:
  created:
    - bench/sequential.py
    - bench/power.py
    - scripts/sim_sequential.py
    - tests/test_bench_sequential.py
    - tests/test_bench_power.py
    - .planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json
  modified:
    - bench/stats.py
    - tests/test_bench_stats.py

key-decisions:
  - "Beta(1,1) mixture prior (PRIOR_A = 1.0), rejection at log LR >= log(1/alpha); validity checked by simulation, not only by citation"
  - "Looks are cumulative (n, b, c) tuples from contiguous seed prefixes; the verdict stops at the first crossing and keeps it"
  - "Sequential power is simulated per block of seeds (default 96) with common random numbers; sample size is the smallest block multiple reaching the target power"
  - "DEFAULT_DISCORDANCE stays None until the lgen pilot (plan 01-15); callers pass psi"

requirements-completed: [MEAS-06]

coverage:
  - id: D1
    description: "Exact McNemar and the Beta(1,1) mixture always-valid test turn contiguous-prefix looks into a verdict, with the rejection rule pinned at the exact boundary (b = 7 open, b = 8 crosses at alpha 0.05)"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_sequential.py (15 tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "log LR is finite for b + c = 20,000, exact McNemar returns 1.0 for b + c = 0, wilson(0, 0) is (0, 1)"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_sequential.py#test_mixture_lr_stays_finite_for_huge_counts; tests/test_bench_stats.py#test_wilson_without_games_is_the_whole_interval"
        status: pass
    human_judgment: false
  - id: D3
    description: "Exact McNemar MDE matches the research table within 0.0005 and a deterministic simulated power, MDE and sample size exist for the sequential test"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_power.py (23 tests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "A committed, re-runnable simulation shows the mixture test's false-positive rate stays at or below alpha under repeated checking, next to the legacy design's inflated rate"
    requirement: MEAS-06
    verification:
      - kind: integration
        ref: ".venv/bin/python scripts/sim_sequential.py --out .planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json (exit 0; second run byte-identical)"
        status: pass
    human_judgment: false

duration: 5min
completed: 2026-11-12
status: complete
---

# Phase 1 Plan 02: Exact McNemar, always-valid sequential test and power calculator Summary

**Paired statistics for the bench: exact McNemar plus a Beta(1,1)-mixture always-valid test on discordant pairs, an exact and simulated power/MDE/sample-size calculator, and a committed simulation showing 1.1-3.7% false positives under repeated checking against 7.0-7.7% for the legacy checkpoint design.**

## Performance

- **Duration:** about 5 min wall clock
- **Started:** 2026-11-12T17:27:28Z
- **Completed:** 2026-11-12T17:33Z
- **Tasks:** 3
- **Files modified:** 8 (6 created, 2 modified)

## Accomplishments

- `bench/sequential.py` (stdlib + scipy, no numpy): `discordant`, `mcnemar_exact`, `log_mixture_lr` (log space, `math.lgamma`), `anytime_p`, `SeqVerdict`, `judge_sequential`, `contiguous_prefix`, constants `NO_EFFECT` and `PRIOR_A`. At alpha 0.05, `log_mixture_lr(7, 0) = 2.7726` stays under `log(20) = 2.9957` and `log_mixture_lr(8, 0) = 3.3480` crosses it; both are asserted.
- `bench/power.py`: `mcnemar_power`, `mcnemar_mde` (bisection to 1e-5), `sequential_power`, `sequential_mde`, `sequential_sample_size`, `plan`, `DEFAULT_DISCORDANCE = None`. Measured MDEs: n 400 psi .05 -> 0.03206; 1000/.2 -> 0.04041; 2000/.3 -> 0.03476; 10000/.4 -> 0.01782 (research table: 0.0321, 0.0404, 0.0348, 0.0178). `sequential_power(4000, 0.2, 0.03, block=96) = 0.83475` (research run: 0.83). `plan(0.03, 0.2)` gives `n_planned = 3744` (a multiple of 96) and `mcnemar_mde_at_n = 0.0207`.
- `scripts/sim_sequential.py` plus the report `.planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json` (seed 20261112, 20,000 reps per cell). Before simulating, the script checks its vectorised rules against `bench.sequential.log_mixture_lr` and `bench.stats.judge_paired`.
- `bench/stats.py`: `wilson(k, 0, z)` returns `(0.0, 1.0)`; the docstring marks `judge`, `judge_paired`, `judge_paired_numeric` and `CHECKPOINTS` as descriptive only.

## Simulation results (from the committed report, null: delta 0, 20,000 reps per cell)

| Design | psi 0.05 | psi 0.2 | psi 0.4 |
|--------|----------|---------|---------|
| mixture, look every 96 seeds up to 10,000 | 2.21% | 1.49% | 1.06% |
| mixture, look after every discordant pair up to 2,000 | 3.66% | 3.54% | 3.61% |
| legacy Wald checkpoints (z99 at 192/384/576/1152, z95 at 2304) | 7.03% | 7.72% | 7.31% |
| exact McNemar peeked every 20 pairs up to 2,000 | 32.9% | 33.7% | 33.3% |

All six mixture cells are `ok: true` (rate <= alpha + 3 se). Research table values: legacy about 7.3-7.7%, mixture every pair 3.7%, McNemar peeking 33.6%. The every-pair rows do not depend on psi (psi only sets how many seeds a pair costs), so the three psi columns repeat one experiment with independent random streams.

Power (mixture test, a look every 96 seeds): psi .2 delta .03 n_max 4000 power 0.831, median stop 2304 seeds (1920 among winners); .2/.04/3000 power 0.950; .1/.02/6000 power 0.952; .3/.05/3000 power 0.952.

## Task Commits

1. **Task 1: Paired outcomes to a sequential verdict (tracer, TDD)**
   - RED: `e081a13` (test)
   - GREEN: `253eeaf` (feat)
2. **Task 2: Power calculator (TDD)**
   - RED: `5e5b5a2` (test)
   - GREEN: `b5abb9f` (feat)
3. **Task 3: Simulation report** - `b410f5f` (feat)

REFACTOR: none needed for either TDD task. **Plan metadata:** the SUMMARY commit containing this file, then a STATE/ROADMAP commit.

## Files Created/Modified

- `bench/sequential.py` - exact McNemar, mixture LR, verdict, prefix helper
- `bench/power.py` - exact and simulated power, MDE, sample size, plan
- `scripts/sim_sequential.py` - null and power simulation, JSON report, exit 1 on a mixture null cell above its bound
- `tests/test_bench_sequential.py` - 15 tests including a seeded peeking-null simulation (2,000 reps, 500 pairs, rate must be > 0 and <= 0.05)
- `tests/test_bench_power.py` - 23 tests (MDE table, monotonicity, determinism, sample size boundary, input validation)
- `tests/test_bench_stats.py` - wilson at n = 0
- `bench/stats.py` - wilson n = 0 case, docstring
- `.planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json` - committed report

## Decisions Made

- Beta(1,1) prior as in the research; priors change power, not validity.
- The verdict stops at the first crossing and reports that look's n, b, c; a later fall-back cannot undo it (tested).
- `sequential_power` draws each block from its own stream `default_rng([seed, block])` and uses inverse-CDF binomial draws with a shared uniform. That makes power deterministic, consistent across n_max prefixes, and rising in delta, so the bisections in MDE and sample size are well behaved.
- Hooking into the scheduler and the experiment API is left to plan 01-13, as planned.

## TDD Gate Compliance

- **Task 1 RED** `e081a13`: `tests/test_bench_sequential.py` and the wilson test, with a placeholder `bench/sequential.py` whose functions return empty values so the run fails on assertions, not on import (same reading of "tests first" as plan 01-01). Command: `.venv/bin/python -m pytest -q tests/test_bench_sequential.py tests/test_bench_stats.py --junitxml=red02.xml`, exit 1, 15 failed and 16 passed. The JUnit report went through `gsd_run check tdd-red-evidence` with target `test_mixture_lr_boundary_at_alpha_005` and returned `RED_EVIDENCE_OK` (`target_test_failed`).
  - Semantic assessment: the target executed and failed on `assert 0.0 == approx(2.7726)` for the planned log LR value, not on a setup, import or fixture fault. One test (the peeking null) first passed vacuously because the placeholder never rejects; it was tightened to also require a rejection rate above zero before the RED run, so it fails on its own assertion in the recorded run.
- **Task 1 GREEN** `253eeaf`: 31 passed.
- **Task 2 RED** `5e5b5a2`: `tests/test_bench_power.py` with a placeholder `bench/power.py`; exit 1, 21 failed and 2 passed. A first classifier attempt with a parametrized target name returned `INVALID_RED` (`no_target_test_failure`, because the report names the case with its parameters); re-running the classifier with the non-parametrized target `test_exact_power_at_the_mde_is_the_target` returned `RED_EVIDENCE_OK`.
  - Semantic assessment: target failed on `1.0 == approx(0.8)` from the placeholder power, the planned assertion that power at the MDE equals the target.
- **Task 2 GREEN** `b5abb9f`: 23 passed on the first run.
- **REFACTOR:** none; no commit.
- The RED record files were written to the session scratchpad, not committed.
- The plan-level gate grep `git log -E --grep='^(test|feat)\(0*1-0*2\):'` also matches two commits of an earlier, unrelated project history that used the same `01-02` scope (`40f9a81`, `c490948`); this plan's commits are the five listed above.

## Deviations from Plan

None - plan executed exactly as written. (Small tightening inside Task 1: the peeking-null test asserts `0 < rate <= alpha` so it cannot pass vacuously; this is within the plan's behaviour bullet.)

## Process note

Per the sequential-execution instruction, the stale-ledger rule applied: `$(git rev-parse --git-dir)/gsd-plan-head-before-01-02` was overwritten with `bfdc221853e581adc115825358e3ed50e4781c16` before the first commit, and `commits: 5` is measured from it.

## Authentication Gates

None.

## Known Stubs

None. The placeholder modules of the two RED commits were replaced in GREEN.

## Threat Flags

None. Pure statistics logic: no network, file or auth surface beyond the script writing its `--out` path. T-01-05 (false wins under peeking): mitigated by the committed simulation and the exact-threshold tests. T-01-06 (power numbers): mitigated by the pinned MDE table values and a seeded, deterministic power simulation. T-01-SC: no packages added.

## Issues Encountered

None.

## Verification output

- `.venv/bin/python -m pytest -q tests/test_bench_sequential.py tests/test_bench_power.py tests/test_bench_stats.py`: `54 passed in 4.47s`.
- Full non-slow suite: `624 passed, 6 skipped, 16 deselected in 63.89s`.
- `.venv/bin/python scripts/sim_sequential.py --out .planning/phases/01-measurement-and-proof-foundation/01-SIM-SEQUENTIAL.json`: exit 0; a second run to a scratch path was byte-identical (`cmp`).
- Report assertion (6 mixture cells all ok, 4 power cells): printed `ok`; the report has 12 null cells and records seed 20261112.
- Acceptance checks: `grep -c 'import numpy' bench/sequential.py` printed 0; `judge_sequential([(50, 8, 0)], ...)` state printed `better`; `plan(0.03, 0.2)['n_planned'] % 96` printed 0; `grep -c '^DEFAULT_DISCORDANCE = None' bench/power.py` printed 1.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Plan 01-13 can wire `judge_sequential`, `contiguous_prefix` and `plan` into the scheduler and the experiment API; `SeqVerdict.as_dict()` is the stored shape. `orient()` in `bench/metrics.py` still flips better/worse for lower-is-better metrics and applies to the state string unchanged.
- psi is still unknown; plan 01-15 sets `DEFAULT_DISCORDANCE` from the lgen pilot. The simulated null assumes distinct seeds behave as independent draws (research assumption A2); an A/A on different seed sets remains the check for that.

---
*Phase: 01-measurement-and-proof-foundation*
*Completed: 2026-11-12*

## Self-Check: PASSED

- Files found: bench/sequential.py, bench/power.py, scripts/sim_sequential.py, tests/test_bench_sequential.py, tests/test_bench_power.py, tests/test_bench_stats.py, 01-SIM-SEQUENTIAL.json
- Commits found on HEAD: e081a13, 253eeaf, 5e5b5a2, b5abb9f, b410f5f (`evaluation-scope --commits-only` resolved with commits)
