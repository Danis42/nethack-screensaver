---
phase: 02-real-descent
plan: 01
subsystem: measurement
tags: [ladder, mines-end, dungeon-truth]
requires: []
provides:
  - "nethack_screensaver/dungeon_truth.py: read(seeds) -> DungeonTruth(mines_levels, mines_end, quest_dnum, quest_depth_start)"
  - "ladder.Facts.mines_end_level; rung 6 = standing on the real last Mines level when known"
  - "counter ladder_truth_error (fallback to the old proxy)"
affects: [02-03, 02-04]
key-decisions:
  - "The libnethack copy of the current game is picked by its (core, disp) seeds in nle_seeds: neither /proc maps order nor memfd inode numbers follow creation order (the plan's 'newest memfd' rule failed a 4-env test)"
  - "Only GlobalLogic.ladder_facts reads truth_mines_end_level; autoascend never imports the reader (CONTEXT D-04)"
plan_head_before: 29624bc
---

# Plan 02-01 Summary: exact Mines' End rung

The ladder now knows the real Mines size of the running game (8 or 9 levels) from NetHack's own
dungeon table and records rung 6 on arrival at the true last level; without the layout it falls back
to the old proxy and counts `ladder_truth_error`.

## Deviation

- **Instance selection (Rule 1, bug):** the plan said "newest memfd inode". A test with four live envs
  showed inode numbers are not in creation order. Each libnethack copy stores its seeds in `nle_seeds`,
  so `read(seeds)` takes the game's `get_current_seeds()[:2]` and uses the matching copy (identical
  seeds mean an identical dungeon, so any match is right). Tested with envs for seeds 3, 1, 8, 4 alive at once.
- A bare `nethack.Nethack()` in the new tests wrote `nle.ttyrec3.bz2` into the repo root; removed, tests
  now pass `ttyrec=None`.

## Verification

- `uv run pytest -q tests/test_dungeon_truth.py`: 6 passed (seed 1 -> 8 levels, seed 3 -> 9, four envs, unknown seeds, no game, no nm)
- `uv run pytest -q -m ""`: 442 passed, 5 skipped, 5 xfailed, 1 xpassed
- `git grep -n dungeon_truth -- autoascend`: nothing; `truth_mines_end_level` only in global_logic.py (attribute + ladder_facts)
- No package added (`pyproject.toml`, `uv.lock` untouched)

Bench evidence for 8- and 9-level games comes with p2-baseline (plan 02-03).
