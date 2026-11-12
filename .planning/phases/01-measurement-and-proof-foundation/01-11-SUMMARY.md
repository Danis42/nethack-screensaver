---
phase: 01-measurement-and-proof-foundation
plan: 11
subsystem: bench
tags: [resume, started, tool-games, mcp, job-lifecycle]

requires:
  - phase: 01-10
    provides: check_seed and TOOL_KINDS (tool block 0-999)
provides:
  - "Store.resume/interrupted, App.resume, POST /api/jobs/<id>/resume, MCP bench_resume and bench_shutdown, serve --resume (D-08)"
  - "Store.started/first_game_at/job_game_count from games or tool_games rows; App.job adds started, first_game_at, games_played, games_reused; status adds started; MCP bench_job; wait prints started (MEAS-09)"
  - "tool_games table; Store.add_tool_game/tool_games; add_game refuses results with a stage (MEAS-08)"
  - "bench/toolruns.py and --record/--data on scripts/staged_run.py, scenario_run.py, rewind.py"
affects: [01-12 funnel, 01-14 skeleton proof and long runs, claim checker (started rule)]

actuals:
  tasks: 3
  commits: 4     # MEASURED: git rev-list --count fd38f07..7752b04 before the SUMMARY commit
plan_head_before: fd38f07842bbd6608ed04f60948727b2d51e1b7b
plan_head_after: 7752b04dd50727daf81684375a88980d76b5f9cc

tech-stack:
  added: []
  patterns:
    - "A job is started iff a games or tool_games row carries its job_id; no surface reads 'started' from the job state"

key-files:
  created:
    - bench/toolruns.py
    - tests/test_bench_tool_games.py
  modified:
    - bench/store.py
    - bench/server.py
    - bench/cli.py
    - bench/mcp_server.py
    - scripts/staged_run.py
    - scripts/scenario_run.py
    - scripts/rewind.py
    - tests/test_bench_store.py
    - tests/test_bench_server.py
    - tests/test_bench_mcp.py
    - tests/test_check_claims.py

key-decisions:
  - "games_reused = stored seeds of the job key in the window minus the job's own rows; a fully reused baseline is done but never started"
  - "Recording refuses a dirty checkout (git status --porcelain without untracked files) so every tool row maps to a commit"

requirements-completed: [MEAS-09, MEAS-08]

coverage:
  - id: D1
    description: "Interrupted job resumes under its id and plays each remaining seed once; non-interrupted resume is 400, unknown 404; serve --resume"
    requirement: MEAS-09
    verification:
      - kind: unit
        ref: "tests/test_bench_server.py::test_an_interrupted_job_resumes_under_its_id_and_plays_each_seed_once, ::test_only_interrupted_jobs_resume_over_http; tests/test_bench_mcp.py tool-name set"
        status: pass
    human_judgment: false
  - id: D2
    description: "Started only from game rows (running but not started; fully reused baseline not started); bench_job reports it"
    requirement: MEAS-09
    verification:
      - kind: unit
        ref: "tests/test_bench_store.py::test_started_means_a_game_row_exists; tests/test_bench_server.py (running/not started, fully reused); tests/test_bench_mcp.py::test_bench_job_reports_started_and_first_game_at"
        status: pass
    human_judgment: false
  - id: D3
    description: "tool_games rows invisible to natural reads; stage guard; toolruns refuses non-tool seeds/kinds/short shas; shared job id sequence"
    requirement: MEAS-08
    verification:
      - kind: unit
        ref: "tests/test_bench_tool_games.py (6 tests)"
        status: pass
    human_judgment: false
  - id: D4
    description: "A real staged/scenario/rewind run with --record writes tool rows under a job id"
    requirement: MEAS-08
    human_judgment: true
    rationale: "The scripts were checked with --help and the toolruns path by unit tests; no full recorded game run was made in this plan"

duration: 8 min
completed: 2026-11-12
---

# Phase 1 Plan 11: Job lifecycle (resume, started, tool runs) Summary

**Interrupted bench jobs resume under their own ID. Every bench surface (job API, status, MCP, `wait`) reports a job as started only once a game row exists. Staged, scenario and rewind runs can be recorded with job IDs in a separate `tool_games` table that natural reads never see.**

## Performance

- **Duration:** 8 min (measured between start and end markers)
- **Completed:** 2026-11-12
- **Tasks:** 3 (tracer, TDD, auto)
- **Executed:** inline in the main session (no executor subagent)

## Task Commits

1. **Task 1 (tracer):** `1776ae7`
2. **Task 2 (TDD):** RED `377d406`, GREEN `819f7bc`
3. **Task 3:** `7752b04`

## TDD Gate Compliance

Task 2 RED `377d406`: 8 failed (no `started`, `tool_games`, `add_tool_game`, stage guard or `bench_job`). GREEN `819f7bc`: the four test files pass, and the full suite passes.

## Deviations from Plan

**1. [Rule 1 - Bug] Two claim-checker tests assumed no tool_games table**
- `tests/test_check_claims.py` built its database with `Store` and then created `tool_games` itself; the Store now creates it. The "older database" test drops the table first, and the tool-row test inserts with the new columns.
- Commit: 819f7bc.

**2. [Process] The resume test resumes through `App.resume`; HTTP covers the refusal cases**
- The interrupted-then-resumed run uses `App.resume` on a fresh App over the same file (a restarted server). The HTTP route is tested for the 400 (done job) and 404 (unknown job) answers.

**3. [Rule 2 - Missing critical] rewind keeps going after a crashed seed and reports it**
- To finish a recorded job as failed instead of leaving it running, `run_seed` errors are caught per seed. Without `--record` they are now printed as `FAILED seed N: ...` at the end; before, a crashing thread lost the seed silently.

**Total deviations:** 3. **Impact:** none on scope.

## Issues Encountered

None.

## Verification output

- Task files: 52 passed (Task 2); `tests/test_bench_tool_games.py`: 6 passed.
- `screens-bench serve --help` lists `--resume`. `--help` of all three scripts lists `--record`.
- `grep -c 'CREATE TABLE IF NOT EXISTS tool_games' bench/store.py`: 1. `grep -c 'def bench_resume' bench/mcp_server.py`: 1.
- Full non-slow suite at `7752b04`: 802 passed, 6 skipped, 16 deselected.

## User Setup Required

None. To survive a reboot, start the server with `uv run screens-bench serve --resume`.

## Next Phase Readiness

Ready for 01-12 (stage funnel).

## Self-Check: PASSED
