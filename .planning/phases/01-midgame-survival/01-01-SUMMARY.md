---
phase: 01-midgame-survival
plan: 01
subsystem: testing
tags: [nle, determinism, fix_moon_phase, bench, death-context]

requires: []
provides:
  - "Seeded games take moon phase, Friday the 13th and night from the seed (NLE fix_moon_phase); unseeded games keep the real clock"
  - "Replay tests proving a seed plays the same game in fresh processes, in one long-lived process (A,B,A) and on any calendar day"
  - "Death context on every GameResult: last_messages, prayers, zaps_seen, hp/max_hp/hunger/depth_at_end, food_at_end, events"
  - "StatsLogger.counters() and StatsLogger.add(name, n)"
affects: [01-03, 01-05, 01-06, 01-08, 01-09, 01-10, 01-11]

actuals:
  tokens: 3175
  tasks: 2
  commits: 2
plan_head_before: 191e4afe16a8dc23b1be373d4c123ff18d52dede
plan_head_after: 918a44e04ae531f913bfc09082518b36d5a89913
commits: 2

tech-stack:
  added: []
  patterns:
    - "Observation-only observer (_DeathContext.observe(obs)) so diagnostics cannot act on the game"
    - "Agent reads for diagnostics happen after wrapper.main() returns, wrapped in try/except (like _has_loot)"

key-files:
  created: [tests/test_replay.py]
  modified: [nethack_screensaver/game.py, autoascend/stats_logger.py, tests/test_game.py, tests/test_stats_logger.py]

key-decisions:
  - "fix_moon_phase=seed is not None: only seeded (bench) games are calendar-independent; the screensaver keeps the real moon"
  - "Edible-food rule duplicated in game.py (_edible_food) instead of refactoring Agent.edible_inventory_food, so agent behaviour cannot change"
  - "lgen left unchanged in set_initial_seeds (decided in plan 01-06)"

patterns-established:
  - "Replay test: child program printing JSON of frame hash plus result, run under different PYTHONHASHSEED values"

requirements-completed: [MEAS-03]

coverage:
  - id: D1
    description: "Seeded game takes its moon from the seed; unseeded keeps the real clock"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_game.py#test_seeded_game_takes_the_moon_from_the_seed"
        status: pass
      - kind: unit
        ref: "tests/test_game.py#test_unseeded_game_keeps_the_real_moon"
        status: pass
      - kind: integration
        ref: "tests/test_replay.py#test_the_seed_decides_the_moon"
        status: pass
    human_judgment: false
  - id: D2
    description: "One seed replays frame for frame across fresh processes (different PYTHONHASHSEED) and A,B,A in one process"
    requirement: MEAS-03
    verification:
      - kind: integration
        ref: "tests/test_replay.py#test_fresh_processes_replay_the_same_game"
        status: pass
      - kind: integration
        ref: "tests/test_replay.py#test_one_process_replays_seed_a_after_seed_b"
        status: pass
    human_judgment: false
  - id: D3
    description: "Every result carries its death context and the observer is observation-only"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_game.py (messages, prayer, zaps, end_state, food_at_end, events tests); tests/test_stats_logger.py#test_counters_and_add"
        status: pass
    human_judgment: false

duration: 6min
completed: 2026-10-23
status: complete
---

# Phase 1 Plan 01: Deterministic seeds and death context Summary

**Seeded bench games take moon phase/Friday-13th/night from the seed via NLE `fix_moon_phase`, replay frame for frame across processes, and every GameResult now records how the game ended (last messages, prayers, monster zaps, end HP/hunger/depth, food carried, bot counters).**

## Performance

- **Duration:** 6 min (2026-10-23T16:18:02Z to 16:24:08Z)
- **Tasks:** 2 of 2
- **Files:** 1 created, 4 modified

## Accomplishments

- `run_game` builds `NetHackChallenge(no_progress_timeout=1000, fix_moon_phase=seed is not None)`. Verified the test is real: with the fix forced off, `test_the_seed_decides_the_moon` fails.
- `_DeathContext` (signature `observe(self, obs)`, no wrapper/agent access) tracks the last 8 distinct message lines, prayers (turn plus the next 4 lines, kept even if unfinished at game end), monster zaps, and the last non-zero-blstats HP/max HP/hunger/depth.
- `_food_at_end` and `_events` read the agent only after `wrapper.main()` returned; `StatsLogger.counters()`/`add()` added without touching `get_stats_dict`.
- Three slow replay tests (all pass, ~35 s): seeds 3 and 10 in four parallel fresh processes (PYTHONHASHSEED 1/2) match on frame hash, frame count and all compared result fields; seed 3, 10, 3 in one process replays seed 3 exactly; seed 49 shows "Friday the 13th" and seed 3 "full moon" regardless of today's date.
- Sample real game (seed 3, 3000 steps) produced: hp 24/24, hunger 1, depth 3, food_at_end 7, events `{'agent_panic': 13}`.

## Task Commits

1. Task 1 (tracer): moon from the seed, last messages, replay tests - `90a08b3`
2. Task 2: prayers, zaps, end state, food, events, counters - `918a44e`

## Verification

- `uv run pytest -q -m ""`: 267 passed, 5 skipped, 5 xfailed, 1 xpassed (full suite incl. slow).
- `uv run pytest -q -m slow tests/test_replay.py`: 3 passed.
- `git diff 191e4af..HEAD -- pyproject.toml uv.lock` is empty (no new dependency).
- Acceptance greps and the `GameResult` field / `observe` signature checks all pass.

## Deviations from Plan

None - plan executed exactly as written. Minor test detail: fake inventory items needed `is_container` because `flatten_items` calls it; one extra test (`test_unfinished_prayer_is_kept_when_the_game_ends`) added beyond the six listed.

**Total deviations:** 0.

## Issues Encountered

None. Games that end through the 120 s screen watchdog remain the accepted non-replay source (documented for plan 01-05).

## Known Stubs

None.

## Threat Flags

None. The observer is observation-only (T-01-01 mitigated, signature asserted), no packages were added (T-01-SC).

## Next Phase Readiness

Ready for 01-02. `GameResult` consumers (scripts in 01-03, A/A in 01-05, diagnosis in 01-08..01-11) can rely on the new defaulted fields; old stored JSON still loads.

## Self-Check: PASSED

- FOUND: tests/test_replay.py, nethack_screensaver/game.py, autoascend/stats_logger.py
- FOUND commits: 90a08b3, 918a44e
