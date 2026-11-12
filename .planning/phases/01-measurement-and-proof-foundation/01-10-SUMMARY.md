---
phase: 01-measurement-and-proof-foundation
plan: 10
subsystem: bench
tags: [seed-ranges, refusal-policy, clean-attempt, gate]

requires:
  - phase: 01-08
    provides: bench/seeds.py ranges and windows, seed-window job specs, schema 2 store
provides:
  - "bench/seeds.py: CLEAN_KIND, GATE_RE, check_window(lo, hi, kind, gate), check_seed(seed, kind, gate)"
  - "App.start_baseline/start_experiment(gate=...) refuse wrong ranges before a job exists and record seeds.range and gate"
  - "POST /api/jobs accepts only KINDS_OVER_HTTP (baseline, experiment); clean_attempt is never creatable over HTTP or MCP"
  - "Scheduler._dispatch refuses out-of-range seeds before any play; Store.add_game refuses final-range seeds unless job_kind == clean_attempt"
  - "MCP bench_baseline(gate=...)"
affects: [01-11 job lifecycle, 01-13 experiments, 01-14 baseline and A/A, Phase 7 clean attempts]

actuals:
  tasks: 2
  commits: 4     # MEASURED: git rev-list --count af94ed7..bfbb241 before the SUMMARY commit
plan_head_before: af94ed7b76fd4216b98f952417d456c7ca8e50f1
plan_head_after: bfbb2416572533bac8b6cb40159c545d354103d0

tech-stack:
  added: []
  patterns:
    - "Three enforcement points for the final range: App.start_*, Scheduler._dispatch, Store.add_game"

key-files:
  created:
    - tests/test_bench_seeds.py
  modified:
    - bench/seeds.py
    - bench/server.py
    - bench/mcp_server.py
    - bench/scheduler.py
    - bench/store.py
    - tests/test_bench_server.py
    - tests/test_bench_mcp.py
    - tests/test_bench_scheduler.py
    - tests/test_bench_store.py

key-decisions:
  - "Natural windows must lie inside one range; a window spanning dev and confirm is refused"
  - "The store guards only the final range, so imports of old seeded games keep working"

requirements-completed: [MEAS-07]

coverage:
  - id: D1
    description: "Range boundaries exact and half-open; natural, tool and clean kinds checked; confirm needs a GATE_RE gate"
    requirement: MEAS-07
    verification:
      - kind: unit
        ref: "tests/test_bench_seeds.py"
        status: pass
    human_judgment: false
  - id: D2
    description: "Final range refused at App, scheduler and store; clean_attempt not creatable over HTTP; MCP forwards gate"
    requirement: MEAS-07
    verification:
      - kind: unit
        ref: "tests/test_bench_server.py (final, gate, HTTP 400), tests/test_bench_scheduler.py (dispatch refusals), tests/test_bench_store.py (add_game guard, job_kind), tests/test_bench_mcp.py (gate)"
        status: pass
    human_judgment: false

duration: 4 min
completed: 2026-11-12
---

# Phase 1 Plan 10: Seed-range refusal policy Summary

**Bench jobs on the wrong seed range are refused before they exist and again before any game is played or stored. Confirm-range windows need a named phase gate, and final-range seeds are reserved for clean attempts, which neither HTTP nor MCP can create.**

## Performance

- **Duration:** 4 min (measured between start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 2 (both TDD)
- **Executed:** inline in the main session (no executor subagent)

## Accomplishments

- `check_window` / `check_seed` implement D-07, D-17 and D-22 with messages naming the range and rule.
- API, scheduler and store each refuse final-range seeds (success criterion 4 refusal test).
- `KINDS_OVER_HTTP` limits job creation over HTTP to baseline and experiment.

## Task Commits

1. **Task 1 (tracer, TDD):** RED `60351b5`, GREEN `577a8d1`
2. **Task 2 (TDD):** RED `48083cf`, GREEN `bfbb241`

## TDD Gate Compliance

Task 1 RED: 15 failed (no `check_window`, no gate parameter, the HTTP handler did not name clean_attempt). Task 2 RED: 4 failed (no dispatch check, no `job_kind`, no store guard). Both GREEN commits pass their files, and the full suite passes.

## Deviations from Plan

**1. [Rule 3 - Blocking] Existing scheduler tests moved from window 0 to window 1000**
- They used seeds from 0 (plan 01-08 kept their old meaning), which the new dispatch check correctly refuses as the tool block. Their windows, pre-stored seeds and expected seed lists now start at 1000; the lgen test expects 10,001,000-10,001,002.
- Commit: 48083cf.

**Total deviations:** 1. **Impact:** test-only.

## Threat Flags

The policy guards against accidental misuse, not an adversary: Claude can reach the HTTP API, so the owner reviews jobs by range (module docstring of `tests/test_bench_seeds.py`). No clean_attempt route, MCP tool or CLI command was added (`grep -c clean_attempt bench/mcp_server.py` = 0).

## Issues Encountered

None.

## Verification output

- `tests/test_bench_seeds.py tests/test_bench_server.py tests/test_bench_mcp.py`: 51 passed. `tests/test_bench_scheduler.py tests/test_bench_store.py`: 33 passed.
- Full non-slow suite at `bfbb241`: 790 passed, 6 skipped, 16 deselected.
- `grep -c 'check_window(' bench/server.py`: 2. `grep -c 'check_seed(' bench/scheduler.py`: 1.

## User Setup Required

None.

## Next Phase Readiness

Ready for 01-11.

## Self-Check: PASSED
