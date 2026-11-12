---
phase: 01-measurement-and-proof-foundation
plan: 12
subsystem: bench
tags: [funnel, wilson, stage-metrics, mcp, dashboard]

requires:
  - phase: 01-05
    provides: quest_portal ladder stage (D-21), 18 RUNGS
  - phase: 01-08
    provides: keyed Store.games reads (rep, lgen mode, env, window)
  - phase: 01-10
    provides: seeds.TOOL block and window checks
provides:
  - "bench/funnel.py: STAGES (18 keys) and funnel(games) with marginal reach, Wilson lo/hi, conditional rate, excluded/flagged counts"
  - "funnel_for in bench/server.py, shared by App.funnel, GET /api/funnel, MCP bench_funnel and `screens-bench funnel`"
  - "stage_<key> rate metrics (18); rung median and rung<N> metrics removed"
  - "report.summary() carries the funnel; ladder rows are marginal reach with Wilson; dashboard Funnel table"
affects: [01-13 sequential decisions (stage metrics), 01-14 skeleton proof, 01-16 baseline funnel and proof index]

actuals:
  tasks: 2
  commits: 4     # MEASURED: git rev-list --count 55e85ee..9e2d094 before the SUMMARY commit
plan_head_before: 55e85eec34ebdc36a8dbaf1eba68cd30ef2f40f9
plan_head_after: 9e2d0941198f0fcbdc28038424fed08cf9dd95ff

tech-stack:
  added: []
  patterns:
    - "A stage is reached when its key is in the stored ladder dict (marginal reach); no decision reads the rung number"

key-files:
  created:
    - bench/funnel.py
    - tests/test_bench_funnel.py
  modified:
    - bench/server.py
    - bench/mcp_server.py
    - bench/cli.py
    - bench/metrics.py
    - bench/report.py
    - bench/static/index.html
    - scripts/seeded_report.py
    - tests/test_bench_mcp.py
    - tests/test_bench_metrics.py
    - tests/test_bench_server.py
    - tests/test_seeded_scripts.py

key-decisions:
  - "Funnel of a job reads baseline jobs only; an experiment job is refused with a message (two commits, no single funnel)"
  - "App.funnel defaults env_id to the server's env; the CLI reads every env unless --env is given (it builds no fingerprint)"
  - "Ladder rows carry `order` (the rung number for display) instead of `rung`"

requirements-completed: [MEAS-02]

coverage:
  - id: D1
    description: "funnel(): 18 rows in ladder order, empty input gives n 0 and null rates, Wilson from bench.stats, same-turn stages count twice, order-independent, exclusions and flags counted, conditional rate"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_bench_funnel.py (7 funnel tests)"
        status: pass
    human_judgment: false
  - id: D2
    description: "App.funnel reads natural rows in the window, refuses the tool block, ignores rep 1 rows, reads a baseline job's spec; API, MCP and CLI return the same JSON; bad parameters are 400"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_bench_funnel.py::test_app_funnel_*, ::test_replicate_rows_do_not_change_the_funnel, ::test_api_mcp_and_cli_agree"
        status: pass
    human_judgment: false
  - id: D3
    description: "No bench code reads rung; 18 stage_<key> metrics; summary carries the funnel; dashboard Funnel table"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_bench_funnel.py::test_no_decision_path_reads_rung; tests/test_bench_metrics.py::test_stage_metrics_skip_games_without_a_ladder, ::test_summary_carries_the_funnel"
        status: pass
    human_judgment: false
  - id: D4
    description: "The dashboard renders the Funnel table against the live server"
    requirement: MEAS-02
    human_judgment: true
    rationale: "Checked by a JS syntax check and the served-page test only; the running bench server still has the old code until it is restarted"

duration: not measured
completed: 2026-11-12
---

# Phase 1 Plan 12: Stage-key funnel Summary

**The bench now reports a natural-game funnel over all 18 ladder stages: hits/n, rate and a 95% Wilson interval per stage, plus the rate conditional on the previous stage. It is shown through `/api/funnel`, the MCP tool `bench_funnel`, `screens-bench funnel` and the dashboard. The `rung` number no longer drives any metric or decision.**

## Performance

- **Duration:** not measured
- **Completed:** 2026-11-12
- **Tasks:** 2 (tracer TDD, auto TDD)
- **Executed:** inline in the main session (no executor subagent)

## Task Commits

1. **Task 1 (tracer):** RED `0c6a152`, GREEN `937393d`
2. **Task 2:** RED `3428cd6`, GREEN `9e2d094`

## TDD Gate Compliance

Task 1 RED `0c6a152`: collection error (no `bench.funnel`). GREEN `937393d`: 48 passed; only `test_no_decision_path_reads_rung` (Task 2's test) still failed.
Task 2 RED `3428cd6`: 5 failed (rung guard, stage metrics, ladder rows, summary funnel, server ladder keys). GREEN `9e2d094`: 111 passed in the four task files.

## Deviations from Plan

**1. [Rule 3 - Blocking] `scripts/seeded_report.py` read `row['rung']` from `ladder_rows`**
- Ladder rows now carry `order`; the script's ladder table reads that. One line. Commit `9e2d094`.

**2. [Rule 1 - Test fix] `test_ladder_all_games_uses_unseeded_games_too` used rung-only games**
- Its unseeded games had `rung: 3` but a ladder with only `mines`. Under marginal reach they now carry the ladder their rung implies, and the assertions are unchanged. Commit `3428cd6`.

**3. [Process] The CLI `funnel` has `--repo` and `--env`**
- `--repo` lets the tests resolve refs in their own repository. `--env` exists because the CLI builds no env fingerprint, so by default it reads every env.

**Total deviations:** 3. **Impact:** none on scope.

## Issues Encountered

None. The live database has no experiment whose metric is a removed `rung*` metric (`SELECT ... WHERE json_extract(spec,'$.metric') LIKE 'rung%'` returned no rows), so resuming old jobs cannot hit a missing metric.

## Verification output

- `uv run python -m pytest -q tests/test_bench_funnel.py tests/test_bench_metrics.py tests/test_bench_server.py tests/test_seeded_scripts.py`: 111 passed.
- `uv run screens-bench funnel --help | grep -c -- '--lo'`: 2.
- `python -c "...METRICS..."` acceptance check: `ok` (0 rung metrics, 18 stage metrics).
- `grep -c 'def wilson' bench/funnel.py`: 0. `grep -c '<h3>Funnel</h3>' bench/static/index.html`: 1.
- Full non-slow suite at `9e2d094`: 813 passed, 6 skipped, 16 deselected.

## User Setup Required

Restart the bench server so `/api/funnel` and `bench_funnel` are live: `uv run screens-bench serve --resume`.

## Next Phase Readiness

Ready for 01-13 (sequential statistics in the bench; experiments now pick `stage_<key>` metrics).

## Self-Check: PASSED
