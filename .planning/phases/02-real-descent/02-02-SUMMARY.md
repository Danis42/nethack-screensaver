---
phase: 02-real-descent
plan: 02
subsystem: measurement
tags: [stuck, watchdog, metrics]
requires: [02-01]
provides:
  - "autoascend/stuck.py: stuck_report(...) rows (turn, dungeon, level, dlvl, milestone, target, wants_up, down/up seen/reachable, frontier, closed_doors, boulders); GlobalLogic.stuck_reports (last 50); counter stuck_report_error"
  - "GameResult.stuck_reports, dungeon_at_end, level_at_end, watchdog_stack"
  - "bench metric free5 (did not end stuck on a Dlvl 5+ level) and bench.metrics.ended_stuck"
affects: [02-03, 02-05, 02-06]
key-decisions:
  - "Agent.bfs() is deterministic and caches only the current step's own result, so the report calls it directly"
  - "Reports carry the target level and whether the way starts upwards: the smoke showed many games stuck on Mines levels 1-6 while heading up (FIND_SOKOBAN, DIVE after Mines' End), where the down-staircase facts alone mislead"
plan_head_before: decf180
plan_head_after: 9486569
---

# Plan 02-02 Summary: stuck reports, end level, watchdog stack, free5

## Deviation

- **Direction added (Rule 2, missing for correctness):** the first smoke rows (seed 2, 6) were stuck
  going up out of the Mines with a reachable `>`; the plan's fields only described down stairs. Reports
  now also record `target`, `wants_up`, `up_seen`, `up_reachable`, and the 02-03 buckets judge the
  staircase the bot needed.

## Verification

- `uv run pytest -q`: 450 passed, 5 skipped (fast suite); stuck/free5/watchdog tests in test_plans,
  test_game, test_bench_metrics
- Smoke `scripts/benchmark.py --seeds 0-21 -j 11`: stuck_reports>0 in 18 of 22 games; 0 stuck_report_error;
  0 ladder_truth_error; the one watchdog game (seed 13, Dlvl 24) recorded its stack, innermost
  `item/inventory.py:870 gather_items`; 1 Cyclic Panic exception (seed 15)
- Play unchanged: all 22 smoke games equal p1-final's stored games on turns, end_reason, max_depth,
  score and last_messages
- `git diff --stat decf180..9486569 -- autoascend`: global_logic.py (report call in the stuck branch, attribute,
  _report_stuck), stuck.py (new), stats_logger.py (counter); no decision branch changed
