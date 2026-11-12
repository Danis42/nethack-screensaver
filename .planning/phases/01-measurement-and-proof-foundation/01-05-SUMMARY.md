---
phase: 01-measurement-and-proof-foundation
plan: 05
subsystem: bot-and-bench
tags: [lgen, worker-protocol, sokoban-telemetry, ladder, quest-portal]

requires:
  - phase: 01-01
    provides: rebuilt NLE at the pinned fork commit (set_initial_seeds takes lgen), scripts/play_compare.py
  - phase: 01-04
    provides: "# fact:" citation in ladder.py kept intact
provides:
  - "run_game(lgen=...) and GameResult.lgen; ValueError on lgen 0 and lgen without seed"
  - "bench worker protocol 'play <seed> <lgen>'; parse() -> (ok, seed, lgen); ProcessWorker.play(seed, lgen)"
  - "events sokoban_map_not_found, sokoban_unsolvable, sokoban_drop_level_<dunlev>, quest_portal_found"
  - "ladder stage quest_portal right before quest (18 rungs), Facts.quest_portal_found"
affects: [01-08 seed windows (lgen jobs), 01-12 funnel, 01-14 pilot and baseline commit, 01-16 Sokoban cause]

actuals:
  tasks: 3
  commits: 6     # MEASURED: git rev-list --count 17e9084..4d7a342 before the SUMMARY commit
plan_head_before: 17e9084795d85a82976de5d1e2af5687083cc717
plan_head_after: 4d7a342b798cba0dd9e1ce7964a5258786a2f9b8
pre_bot_changes: e7ed363072cb64ebdc99b6d54e501d1b6ec09cbc

tech-stack:
  added: []
  patterns:
    - "New stats_logger counters must be registered in StatsLogger._values; log_event on an unknown name raises KeyError mid-game"

key-files:
  created: []
  modified:
    - nethack_screensaver/game.py
    - bench/worker.py
    - bench/runner.py
    - autoascend/global_logic.py
    - autoascend/ladder.py
    - autoascend/stats_logger.py
    - tests/test_bench_runner.py
    - tests/test_game.py
    - tests/test_ladder.py
    - tests/test_bench_server.py
    - tests/test_stats_logger.py
    - tests/test_bench_metrics.py
    - tests/test_seeded_scripts.py
    - tests/test_quest_portal.py

key-decisions:
  - "quest_portal is reached by the portal trap glyph on the level map, the activation message, or being in the Quest dungeon"
  - "quest_portal_found is logged once per game, on the first Dungeons-of-Doom step where the condition holds"
  - "sokoban_drop_level_1..4 registered explicitly (Sokoban level_number is dunlev 1 = top, 4 = entry)"

requirements-completed: [MEAS-04, MEAS-03, MEAS-02]

coverage:
  - id: D1
    description: "lgen goes runner -> worker -> run_game -> set_initial_seeds and comes back in the result; old commits leave it out; lgen 0 and lgen without seed refused"
    requirement: MEAS-04
    verification:
      - kind: unit
        ref: "tests/test_bench_runner.py (lgen cases, parse), tests/test_game.py (refusal cases)"
        status: pass
      - kind: command
        ref: "run_game(seed=1000, lgen=10001000, max_steps=300) twice: identical, 169 turns (ok 169 1)"
        status: pass
    human_judgment: false
  - id: D2
    description: "Sokoban drop cause and level are logged; play unchanged"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_stats_logger.py (every logged event and every drop level is registered)"
        status: pass
      - kind: command
        ref: "scripts/play_compare.py seeds 1000-1019, e7ed363 vs 4d7a342, ignoring events/ladder/rung: 20/20 identical"
        status: pass
    human_judgment: false
  - id: D3
    description: "quest_portal stage before quest; facts from glyph or message; 18 rungs"
    requirement: MEAS-02
    verification:
      - kind: unit
        ref: "tests/test_ladder.py (stage order, portal-found vs Quest, ladder_facts), tests/test_bench_server.py (18 rows)"
        status: pass
    human_judgment: false

duration: 16 min
completed: 2026-11-12
---

# Phase 1 Plan 05: lgen plumbing, Sokoban drop telemetry, Quest portal stage Summary

**Bench games can now take an NLE level-generation seed end to end. The bot logs whether Sokoban was dropped because no stored map matched or because the board could not be solved, and on which level. The ladder reports the Quest portal as its own stage. A 20-seed comparison shows play is unchanged.**

## Performance

- **Duration:** 16 min (including two runs of the 20-seed comparison)
- **Completed:** 2026-11-12
- **Tasks:** 3 (tracer TDD, auto, auto TDD)
- **Executed:** inline in the main session (no executor subagent)

## Accomplishments

- `run_game(lgen=)`, `GameResult.lgen`, worker line `play <seed> <lgen>`, `ProcessWorker.play(seed, lgen)`.
- Sokoban drop telemetry: `sokoban_map_not_found`, `sokoban_unsolvable`, `sokoban_drop_level_<n>`; `sokoban_dropped` kept as is.
- `quest_portal` stage (D-21) with detector and `quest_portal_found` event.

## Play-unchanged proof (T-01-19)

`pre_bot_changes` = `e7ed363072cb64ebdc99b6d54e501d1b6ec09cbc` (after Task 1, before the telemetry commit). Compared against `4d7a342b798cba0dd9e1ce7964a5258786a2f9b8` with `scripts/play_compare.py --seeds 1000-1019 --jobs 10 --ignore events --ignore ladder --ignore rung`. The summary line, verbatim:

```
{"compared": 20, "identical": 20, "watchdog_skipped": [], "differing_seeds": []}
```

Reach in those 20 games (a separate replay of the same seeds on `4d7a342`):
- Sokoban entered: 7 (seeds 1006, 1007, 1008, 1011, 1012, 1018, 1019).
- Quest portal stage reached: 3 (1001, 1002, 1016). Quest portal level message seen: 6 (1001, 1002, 1005, 1006, 1010, 1016).
- **Early Sokoban signal:** all 7 Sokoban games logged `sokoban_unsolvable` + `sokoban_drop_level_4`, none `sokoban_map_not_found`. On these seeds, the stored map matches but both solvers fail on the entry level. This is 20 games, not the baseline; plan 01-16 writes the cause from the full baseline.

## lgen tracer check

`run_game(seed=1000, lgen=10001000, max_steps=300)` twice: identical on turns, max_depth, score, end_reason and last_messages; 169 turns, depth 1. Plan 01-01 recorded the same seed and step budget without lgen at 198 turns, so lgen changes the generated game.

## Task Commits

1. **Task 1 (tracer, TDD):** RED `1e7f953`, GREEN `e7ed363`
2. **Task 2:** `1d7c441`
3. **Task 3 (TDD):** RED `07cb2fc`, GREEN `b5342a4`, fix `4d7a342`

## TDD Gate Compliance

- Task 1 RED `1e7f953`: 6 failed (TypeError on the new lgen keyword and parse's 3-tuple; the APIs did not exist yet). GREEN `e7ed363`: 54 passed.
- Task 3 RED `07cb2fc`: 7 failed. GREEN `b5342a4`, completed by `4d7a342` (see deviation 2).

## Deviations from Plan

**1. [Rule 1 - Bug] New counters registered in stats_logger.py**
- Found during: Task 2 (full suite: `test_stats_logger_knows_every_logged_event` failed).
- Issue: `StatsLogger._values` is a plain dict, so `log_event` on an unregistered name raises KeyError. In the map-not-found branch, a KeyError would replace the AssertionError the bot handles, which changes play.
- Fix: registered `sokoban_map_not_found`, `sokoban_unsolvable`, `sokoban_drop_level_1..4`, `quest_portal_found`; added a test for the f-string level names (the regex test cannot see them).
- Files: autoascend/stats_logger.py, tests/test_stats_logger.py (not in files_modified). Commits: 1d7c441, b5342a4.

**2. [Rule 1 - Bug] Other tests assumed 17 rungs, and a GlobalLogic fake lacked the new state**
- Found during: Task 3. `b5342a4` was committed while the full suite had 7 failures (my commit chain did not stop on the test result). Fixed in the next commit `4d7a342`, after which the full suite passed.
- Fix: rung counts 17 -> 18 in tests/test_bench_metrics.py, tests/test_game.py and tests/test_seeded_scripts.py. The `_portal_logic` fake in tests/test_quest_portal.py now sets `_quest_portal_found_logged` and gives its level an `objects` map.
- Commit: 4d7a342.

**3. [Process] Checks run with `.venv/bin/python` instead of `uv run`**
- This avoids an implicit `uv sync`. The play comparison needed absolute interpreter paths: the first attempt with relative `.venv/bin/python` failed with FileNotFoundError before playing.

**Total deviations:** 3. **Impact:** test-only and registration changes; no change to play (proven above).

## Threat Flags

T-01-18 mitigated (`run_game` refuses lgen 0). T-01-19 mitigated (20/20 identical). T-01-20 mitigated (`parse` accepts at most two integers).

## Issues Encountered

One commit (`b5342a4`) landed with a failing suite and was fixed by `4d7a342`. From here on, commits are chained on the test exit code, not on a piped `tail`.

## Verification output

- Full non-slow suite at `4d7a342`: 738 passed, 6 skipped, 16 deselected.
- `grep -c 'set_initial_seeds(env.nethack, seed, seed, False, lgen)' nethack_screensaver/game.py`: 1. `grep -cE '^(import|from) bench' bench/worker.py`: 0.
- RUNGS check: `ok` (18 keys, quest_portal right before quest, numbered 1..18). `grep -c quest_portal autoascend/ladder.py`: 3.
- `git show 1d7c441 -- autoascend/global_logic.py`: four added `log_event(` lines, nothing removed.

## User Setup Required

None.

## Next Phase Readiness

Ready for 01-07. Plan 01-14 must run the pilot and baseline on a commit at or after `4d7a342`.

## Self-Check: PASSED
