# AutoAscend port notes

Upstream: maciej-sypetkowski/autoascend @ 8527910 (MIT).
Target: Python 3.13, NLE 1.3.0 (gymnasium), numpy 2, modern numba/opencv.

## Removed
- visualization/, rl_utils.py, rl_scoring.init_fight2_model (torch/RL, tile viewer)
- utils.plot_dashboard (matplotlib/seaborn)
- nltk (replaced by agent._edit_distance)

## Changes
- character.py, item/inventory.py: regex literals with invalid escapes (`\d`, `\.`, `\?`, `\]`) made raw strings (SyntaxWarning on 3.12+, future error). Behavior unchanged.
- env_wrapper.py: rewritten for NLE 1.3.0 / gymnasium (`reset()->(obs, info)`, 5-tuple `step()`, `env.actions` instead of `env._actions`); no seeding patch, no visualizer, no fork/reload/interactive tooling; per-step `on_step` callback; role pinning by re-rolling `reset()` (as upstream `bin/main.py --role` did). End-reason parsing made non-asserting and keeps the cause of death.
- agent.py: `BLStats(*blstats[:26])` — tolerate extra blstats fields in newer NLE.
- agent.py: `cursor_pos` casts `tty_cursor` (uint8) to int. Under NumPy 2 (NEP 50) `uint8(0) - 1` is 255, not -1 as under NumPy 1 — a silent behavior change. Tests now turn overflow RuntimeWarnings into errors.
- soko_solver/maps.py: the map text is indented 4 columns but the solution coordinates
  are not, so every Sokoban attempt died on the first move (`assert ... == BOULDER`).
  The indent is now stripped; `tests/test_soko_solver.py` replays all 8 solutions.
- global_logic.py (screensaver tuning, not a port fix): upstream farmed Dlvl 1 until
  XL 8, which took 15-25k turns and most games fainted from hunger there. Now the bot
  leaves Dlvl 1 once Hungry and goes on to the Mines as before. Farming Dlvl 3 instead
  was tried (4,000 turns, or until XL 8) and gave shallower games: deaths moved to Dlvl 3.
- plans.py (screensaver feature): the fixed milestone order became per-game plans; four
  secret strategies (pilgrim = upstream order, daredevil, sightseer, treasure) and new
  milestones EXPLORE_MINETOWN, LOOT_SOKOBAN_PRIZE, RETURN_TO_SURFACE, LEAVE_DUNGEON.
- env_wrapper.py: NLE reports leaving the dungeon with end_status DEATH; the final screen
  says "escaped the dungeon [max level N]", which is now reported as `ESCAPED: ...`.
- Observed: the final game-over observation has all-zero blstats; `game.run_game` keeps the last non-zero turn/depth.

## Benchmark (2026-10-16, 50 games, `scripts/benchmark.py -n 50 -j 10`)

```
games            : 50
median score     : 5952.5
median max depth : 3.0
median turns     : 19001.0
exceptions       : 4
watchdog         : 0
  3x AssertionError:
  1x AssertionError: ('TODO: nested containers', set(), [a partly
```

Reference: upstream AutoAscend's NeurIPS 2021 challenge median score was 5,300
(Hambro et al., "Insights From the NeurIPS 2021 NetHack Challenge", arXiv:2203.11889).
The port's median (5,952) is in line with it. Most deaths involve fainting from
hunger; the same report notes a "very high incidence of death due to 'fainted of
starvation'" for challenge agents, and a traced game showed the port's eating
works (corpses, rations, prayer at Fainting), so this is upstream behavior, not a
port regression. Remaining exceptions are upstream `AssertionError`s (e.g. "TODO:
nested containers"); they end the game and the screensaver starts a new one.

## Strategies benchmark (2026-10-18, 36 games per strategy)

| | pilgrim | daredevil | sightseer | treasure |
|---|---|---|---|---|
| median max depth | 5 | 4 | 5 | 4 |
| deepest | 8 | 13 | 9 | 11 |
| Dlvl 8+ | 3% | 8% | 14% | 22% |
| visited Mines | 47% | 33% | 61% | 36% |
| visited Sokoban | 3% | 0% | 0% | 8% (levels reached 2, 2, 1) |
| escaped | - | - | 2 | 1 (empty-handed) |
| crashed | 1 | 1 | 4 | 0 |

Both escape strategies win sometimes. Daredevil does not dive: GO_DOWN uses the same
explore-every-level travel as the other milestones, so it is not deeper than the rest.
Sightseer crashes were upstream assertions while exploring Minetown ("Your hands seem
to be too busy", an artifact blast, turn inactivity, nested containers).

## Strategies benchmark after follow-up fixes (2026-10-18, 36 games per strategy)

| | pilgrim | daredevil | sightseer | treasure |
|---|---|---|---|---|
| median max depth | 5 | **7.5** | 4 | 5 |
| deepest | 12 | **20** | 8 | 12 |
| Dlvl 8+ / 10+ | 14% / 6% | **50% / 19%** | 3% / 0% | 17% / 6% |
| visited Mines | 61% | 56% | 53% | 28% |
| visited Sokoban | 8% (solved twice) | 0% | 0% | 8% (solved once) |
| escaped | - | - | **4** | 1 (empty-handed, after solving all of Sokoban) |
| crashed | 1 | 0 | 2 | 2 |

DIVE turned daredevil into the deepest strategy. The treasure game that solved Sokoban
still left without the prize; one sample, not yet investigated.

## Escape tuning (2026-10-18, 48 games per escape strategy)

Retreat home directly (no exploring detours, item gathering or pet waiting on
RETURN_TO_SURFACE) and bail out home when Weak with no food while prayer is on
cooldown; treasure also gives up on Sokoban after 8000 turns.

| | sightseer before | sightseer after | treasure before | treasure after |
|---|---|---|---|---|
| escaped | 11% | **21%** | 3% | **19%** (all empty-handed) |
| escaped after Dlvl 4+ | 11% | 17% | 3% | 10% |
| median max depth | 4 | 5 | 5 | 5 |
| visited Mines | 53% | 62% | 28% | 33% |
| visited Sokoban | 0% | 0% | 8% | 2% |

A first version that bailed out at the first Weak (before praying) gave 52% / 62%
escapes, but nearly all from Dlvl 2-3; the prayer-cooldown gate removed those.
Treasure's prize stays out of reach: few games reach Sokoban, and a reached
Sokoban is sometimes judged unsolvable (`sokoban_dropped`), which skips the loot.

## Role-tilted strategies (2026-10-18, 192 unforced games)

Strategy picked after reset with weights by role tier (strong bar/sam/val/mon get
pilgrim/treasure 70%, weak arc/tou/rog/hea/wiz get sightseer/daredevil 80%).

| | pilgrim (42) | daredevil (49) | sightseer (54) | treasure (47) |
|---|---|---|---|---|
| median max depth | 6 | 5 | 4 | 4 |
| Dlvl 8+ / 10+ | 17% / 7% | 29% / 12% | 2% / 0% | 9% / 4% |
| escaped | - | - | **20%** | 15% (empty-handed) |
| Sokoban visited | 5% | - | - | 2% |

Pilgrim was tried Sokoban-first in this run: 34/42 died during FIND_SOKOBAN,
because finding the Sokoban stairs explores every level of Dlvl 6-10 in full
(`levels_to_explore_to_get_to`, "TODO: one level below oracle"). Reverted to
Mines first. Daredevil's Dlvl 10+ fell from 19% as it now gets more weak roles.

## Wiki rules (2026-10-18, 192 unforced games each)

| | baseline | + Oracle-guided Sokoban search | + pray when Weak | + avoid ']' mimics |
|---|---|---|---|---|
| hunger deaths | - | 30 | 29 | 22 |
| mimic deaths | - | 2 | 8 | 8 |
| Sokoban visits / solved to top / dropped | 3 / 2 / 1 | 7 / 2 / 2 | 13 / 8 / 7 | 10 / 4 / 3 |

Kept: Oracle-guided search (the Sokoban stairs are always one floor below the Oracle)
and praying at Weak (Weak is already major trouble). Reverted: avoiding ']' strange
objects, since the mimics that kill this bot are not the shop ones. Roughly half of
all Sokoban visits end in `sokoban_dropped`, which is what a live-board solver would fix.

## Live Sokoban solver (2026-10-18)

`soko_solver/search.py` is the fallback when the stored solution no longer fits the board:
traps filled one at a time (A* per trap with push distances, backtracking), tested on
NetHack's own `sokoban.des` (disturbed half-played boards: 10/11) and on real boards
captured from failed games (`tests/data/soko_real_*.json`).

Real games (144 forced treasure runs): every live-solver call first failed. Causes found
from captured boards: squares only ever seen under items were missing from the floor
(fixed); the player was not allowed to cross pits (fixed); one board was a true deadlock
(two boulders frozen in a corridor). Still open: the stored solution sometimes derails
early on the top level (5-8 boulders moved, all 16-18 holes open), which is beyond the
10 s search. Treasure escapes with the prize are now seen (2/96 in one run).

Seeded replays (2026-10-18): planned pushes failed because a monster being fought stood
in the only path; the executor now waits a turn (up to 20) instead of giving up. In 192
same-seed treasure games afterwards the solver found plans and executed pushes, but no
game was won through it: most solver calls are true deadlocks or a top level derailed
early, and 8 of 13 characters that reached Sokoban were killed there by monsters. The
puzzle is no longer the main obstacle; surviving Dlvl 6-9 at XL 7-9 is.
