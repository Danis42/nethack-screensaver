---
phase: 01-measurement-and-proof-foundation
plan: 13
subsystem: bench
tags: [sequential-test, power, mde, scheduler, mcp, gitrefs]

requires:
  - phase: 01-02
    provides: bench/sequential.py (judge_sequential, discordant, NO_EFFECT) and bench/power.py (plan, mcnemar_mde, sequential_mde)
  - phase: 01-12
    provides: stage_<key> rate metrics experiments can declare
provides:
  - "start_experiment(candidate, baseline, metric, mde, discordance, alpha, power, block, lo, lgen, gate, allow_new_baseline): spec.declared = power.plan(...), window [lo, lo + n_planned), spec.block"
  - "Scheduler: look k on the contiguous prefix [lo, lo + min((k+1)*block, n_planned)), judged with judge_sequential; result.looks [{n, b, c, log_lr}]; status {look, prefix, n_planned, baseline, candidate}"
  - "App.power, GET /api/power, MCP bench_power, `screens-bench power`"
  - "Pitfall 6 guard: baseline without stored games in the window is refused unless allow_new_baseline"
  - "gitrefs.resolve refuses refs starting with '-'"
affects: [01-14 skeleton proof and pilot, 01-15 baseline and A/A, Phase 2 change loop (every experiment)]

actuals:
  tasks: 2
  commits: 4     # MEASURED: git rev-list --count 0f49a7e..027c406 before the SUMMARY commit
plan_head_before: 0f49a7e80bb7a4d157831e3c3e5018b55f9bfaee
plan_head_after: 027c406948237e8ea11a77eea72cc08f0ed3d292

tech-stack:
  added: []
  patterns:
    - "An experiment's verdict is a function of contiguous seed prefixes only; completion order never reaches the test"

key-files:
  created: []
  modified:
    - bench/scheduler.py
    - bench/server.py
    - bench/cli.py
    - bench/mcp_server.py
    - bench/gitrefs.py
    - bench/static/index.html
    - tests/test_bench_scheduler.py
    - tests/test_bench_server.py
    - tests/test_bench_mcp.py
    - tests/test_bench_gitrefs.py

key-decisions:
  - "Looks are recomputed from stored games on every judgement and replayed from look 0 after a resume; the same data gives the same looks, so a resumed experiment reaches the same verdict"
  - "When games without the metric's field are skipped, the last look (prefix = n_planned) ends as NO_EFFECT even though pairs < n_planned, so such a job cannot stay open forever"
  - "Experiment specs without `declared` (older bench) fail at pick-up with an explanation; the live DB has no experiment jobs, so nothing existing is affected"
  - "The Pitfall 6 guard reads under the job key (lgen mode, server env_id)"

requirements-completed: [MEAS-06]

coverage:
  - id: D1
    description: "mde required (0 < mde < 1), discordance required while no pilot value exists; spec.declared equals power.plan and the window is [lo, lo + n_planned)"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_server.py::test_an_experiment_must_declare_its_mde, ::test_a_started_experiment_stores_its_declared_plan"
        status: pass
    human_judgment: false
  - id: D2
    description: "Clear win ends at the first look with one looks entry; identical outcomes run to n_planned and end NO_EFFECT; a withheld seed (lo + 5) blocks judging with two other blocks done; lower-is-better flips via orient"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_scheduler.py::test_clear_win_is_decided_at_the_first_look, ::test_identical_outcomes_run_to_the_planned_size, ::test_a_gap_in_the_prefix_blocks_judging, ::test_a_lower_is_better_metric_flips_the_verdict"
        status: pass
    human_judgment: false
  - id: D3
    description: "Power over App, HTTP, MCP and CLI agree; Pitfall 6 refusal and the allow_new_baseline override; dash refs refused before git"
    requirement: MEAS-06
    verification:
      - kind: unit
        ref: "tests/test_bench_server.py::test_power_plans_or_reports_the_mde_at_n, ::test_power_cli_prints_the_plan, ::test_an_experiment_needs_a_stored_baseline; tests/test_bench_mcp.py::test_bench_power_matches_the_api, ::test_bench_experiment_can_start_a_new_baseline; tests/test_bench_gitrefs.py::test_refs_starting_with_a_dash_are_refused_before_git"
        status: pass
    human_judgment: false
  - id: D4
    description: "A real experiment on the live bench reaches a sequential verdict"
    requirement: MEAS-06
    human_judgment: true
    rationale: "Only fake-worker runs in this plan; the first real experiments run after the baseline (plans 01-14/01-15)"

duration: not measured
completed: 2026-11-12
---

# Phase 1 Plan 13: Sequential statistics in the bench Summary

**Experiments now declare their MDE before the run. `power.plan` fixes the planned size. The scheduler judges only contiguous seed prefixes, one block per look, with the always-valid sequential test. The power calculator is available over HTTP, MCP and the CLI. The old checkpoint/Wald machinery no longer decides anything.**

## Performance

- **Duration:** not measured
- **Completed:** 2026-11-12
- **Tasks:** 2 (tracer TDD, auto TDD)
- **Executed:** inline in the main session (no executor subagent)

## Task Commits

1. **Task 1 (tracer):** RED `348b976`, GREEN `411b167`
2. **Task 2:** RED `a4013ac`, GREEN `027c406`

## TDD Gate Compliance

Task 1 RED `348b976`: 14 failed. The gap test already passed on the old code, because the old checkpoint scheduler also needed a full prefix; it now guards the new path. GREEN `411b167`: 64 passed in the three task files, and the full suite passed (820).
Task 2 RED `a4013ac`: 7 failed. GREEN `027c406`: 49 passed in the three task files.

## Deviations from Plan

**1. [Rule 2 - Missing critical] Dashboard read the removed checkpoint fields**
- `bench/static/index.html` showed `v.checkpoint`/`v.detectable` and `p.checkpoint`. It now shows n/n_planned, b and c, the always-valid p and the declared MDE, plus look/prefix progress. Old verdicts are labelled as the old checkpoint design. Commit `411b167`.

**2. [Rule 2 - Missing critical] A job could stay open forever when games lack the metric's field**
- `judge_sequential` reports NO_EFFECT only once n reaches n_planned. With skipped games, n stays below that, so the last look is forced to NO_EFFECT. Commit `411b167`.

**3. [Process] Task 1 tests store baseline games before starting experiments**
- This lets them pass both before and after Task 2's Pitfall 6 guard, with no rewrite.

**Total deviations:** 3. **Impact:** none on scope.

## Known leftovers (not in this plan's files)

- `scripts/bench_watch.py` and `scripts/seeded_report.py` (verdict listing) still describe the checkpoint design. They only read stored verdicts, and `verdict.get("checkpoint")` is tolerant, so nothing crashes. They were not rewritten.

## Verification output

- Task 1 files: 64 passed. AST check: `ok` (scheduler imports `judge_sequential`, neither `CHECKPOINTS` nor `judge_paired`).
- Task 2 files: 49 passed. `screens-bench power --mde 0.03 --discordance 0.2` → `ok 3744`. `grep -c 'def bench_power' bench/mcp_server.py`: 1.
- Full non-slow suite at `027c406`: 826 passed, 6 skipped, 16 deselected.
- Live DB: `SELECT state, COUNT(*) FROM jobs WHERE kind='experiment' GROUP BY state` returned no rows.

## User Setup Required

Restart the bench server (`uv run screens-bench serve --resume`) so `/api/power`, `bench_power` and the new experiment path are live.

## Next Phase Readiness

01-14 is next. It is not autonomous: it proves the skeleton on the live DB, and you pick the lgen pilot's second commit and adoption rule.

## Self-Check: PASSED
