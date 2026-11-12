---
phase: 01-measurement-and-proof-foundation
plan: 06
subsystem: ladder
tags: [sokoban, detector, hand-game, fixtures, MEAS-03]

requires:
  - phase: 01-05
    provides: Sokoban drop telemetry and the quest_portal stage on the ladder
provides:
  - "soko-top stage and ladder observation in handplay (Task 1, 296bc0c)"
  - "Detector fix: sokoban_solved waits for holes and pits only (a0a9799)"
  - "tests/data/soko_top_hand_start.json and soko_top_hand_solved.json, both observations of the played hand game"
  - "tests/test_sokoban_detector.py (bot-path Facts, builder agreement, fire-once, trap-seen-first); tests/fake_logic.py"
  - "01-SOKOBAN-DETECTOR.md"
affects: [01-16 written cause of the Sokoban zero, Phase 2 Sokoban fixes]

actuals:
  tasks: 2
  commits: 6     # 296bc0c, af94ed7, a0a9799, 55e85ee (before the reboot), 33e4722, f156861
plan_head_before: 74266ea8e66e5afcb8d5aee695bfa4181fd6083a
plan_head_after: f1568612707a159b7e127f8770cab0c5a0aa203b

key-files:
  created:
    - tests/fake_logic.py
    - tests/test_sokoban_detector.py
    - tests/data/soko_top_hand_solved.json
    - .planning/phases/01-measurement-and-proof-foundation/01-SOKOBAN-DETECTOR.md
    - .planning/hand-games/soko-top/tools/
  modified:
    - tests/test_ladder.py
    - .planning/hand-games/soko-top/NOTES.md
    - .planning/hand-games/soko-top/meta.json

key-decisions:
  - "The plan's 'live solver on the live board' failed on the exact board too (745 s, no plan); attempt 4 used the stored 3.6 solution placed on the true board read from dat/soko1-2.lua and checked by simulation, then played it by hand in the real game"
  - "The solved fixture keeps the rolling boulder trap in `traps` (board_from_observation mirrors the solver's reader, left for Phase 2); the test asserts traps == [[18, 46]] instead of the plan's stale `not traps`"

requirements-completed: []   # MEAS-03's second half (written cause of 0/2304) is plan 01-16

coverage:
  - id: D1
    description: "sokoban_solved fires once, at the turn the last hole is filled (T882), in a played game observed by the real Ladder"
    requirement: MEAS-03
    verification:
      - kind: manual
        ref: "handplay `ladder` at T897: reached {'sokoban': 1, 'sokoban_solved': 882}; pushes-attempt4.log"
        status: pass
    human_judgment: false
  - id: D2
    description: "Bot-path Facts agree with observation_facts on both fixtures; Ladder fires once, never without the start board"
    requirement: MEAS-03
    verification:
      - kind: unit
        ref: "tests/test_sokoban_detector.py (5 tests)"
        status: pass
    human_judgment: false

duration: not measured
completed: 2026-11-13
---

# Phase 1 Plan 06: Sokoban detector against a played hand game Summary

**The top Sokoban level (5.0 soko1-2, seed 7) was solved by hand in attempt 4, and the real Ladder fired `sokoban_solved` exactly once, at T882, the turn the last hole was filled. A regression test replays the recorded start and solved boards through the bot's own Facts builder.**

## Task Commits

1. **Task 1:** `296bc0c` (soko-top stage, ladder in handplay); fixes along the way: `af94ed7`, `a0a9799`
2. **Task 2:** before the reboot `55e85ee` (attempts 1-3 recorded); now test `33e4722`, records `f156861`

## Deviations from Plan

**1. [Rule 3 - Blocking] The live solver could not plan the level**
- `solve()` found no plan within 3,000,000 states, even on the exact board from `dat/soko1-2.lua` (745 s). Attempt 4 played the stored 3.6 solution placed on the true board. It was simulated push by push first (415 pushes), and runs were ended where the boulder actually dropped. The game was still played in the real handplay server, so no board was computed or simulated in place of the game.

**2. [Rule 1 - Wrong check] `not traps` on the solved fixture**
- The rolling boulder trap stays on a solved 5.0 level, and `board_from_observation` keeps it on purpose (a0a9799 left the solver's trap set for Phase 2). The test asserts it is the only one left.

**3. [Process] Wizard-mode help for the hero, none touching a boulder or trap**
- Healing, a weapon, a unicorn horn, and a forced prayer, each logged with its turn in `pushes-attempt4.log`. The bare-handed staged hero would otherwise have died to an ape and a xan.

## Findings for plan 01-16 (cause of 0/2304)

- The stored 3.6 solution fits the 5.0 walls; its row runs assume 3.6 hole positions.
- In Sokoban, giant mimics disguise themselves as boulders (makemon.c `set_mimic_sym`); one sat at screen (41,15).
- A boulder pushed onto the 5.0 rolling boulder trap is launched and rolls into the next open hole; stepping on the trap released nothing.
- Travel does not cross the rolling boulder trap; explicit steps do.

## Verification output

- `uv run python -m pytest -q tests/test_sokoban_detector.py tests/test_ladder.py`: 34 passed.
- Full non-slow suite at `33e4722`: 831 passed, 6 skipped, 16 deselected.
- `grep -c 'def _fake_logic' tests/test_ladder.py`: 0.

## Self-Check: PASSED
