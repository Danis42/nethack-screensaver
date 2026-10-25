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
- nethack_screensaver/game.py (Phase 1, determinism): seeded games build `NetHackChallenge(fix_moon_phase=True)`, so
  the moon phase, Friday the 13th and night come from the seed, not the calendar. Screensaver games (no seed) keep
  the real clock. `GameResult` gained death-context fields (`last_messages`, `prayers`, `zaps_seen`, `hp_at_end`,
  `max_hp_at_end`, `hunger_at_end`, `depth_at_end`, `food_at_end`) and `events` (bot counters); all default, so old
  stored JSON still loads.
- soko_solver/search.py, global_logic.py (Phase 1, determinism): the live Sokoban solver ends on a state budget only,
  `SOKOBAN_LIVE_MAX_STATES = 40_000` with no wall-clock limit (worst board: 40,000 states in 8.4 s), so the same seed
  solves the same way under any machine load.
- stats_logger.py: `counters()` and `add()` expose the bot's event counters for `GameResult.events`.
- prayer.py (new, Phase 1): `prayer_outcome` classifies prayer messages taken from NLD-NAO human games. Not used by
  the bot yet.
- bench/runner.py: bench workers run with `PYTHONHASHSEED=0`, so set and dict-of-str order is the same in every game.
- nethack_screensaver/fixed_clock.py (new, Phase 1, determinism): NetHack reads the clock at game start
  (`u.ubirthday`) and names shopkeepers from it; `fix_moon_phase` does not cover that. A small LD_PRELOAD library
  replaces libc `time()` with `NLE_FIXED_TIME`, and `run_game` sets it per seed (`1_000_000_000 + seed * 257`, so
  every seed gets its own name bucket). Python's clocks and the watchdog keep real time. Bench workers load the
  library and run with one BLAS/OpenMP thread (`OMP_NUM_THREADS=1` etc.); `scripts/benchmark.py --seeds`
  restarts itself with the library loaded.

## Benchmark (2026-10-16, 50 games, `scripts/benchmark.py -n 50 -j 10`)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

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

## Survival on Dlvl 6-9 (2026-10-19, 192 unforced games each)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Two identical baselines differ by about ±10 games on "reached Dlvl 6+", so only large
effects show. Deaths on Dlvl 6-9 have no dominant cause (ants 7, rays 5, floating-eye
freezes 3 of 43); over all depths, floating-eye freezes cost 6-8 games.

| | baseline | baseline 2 | + no floating-eye melee | + rest on Elbereth |
|---|---|---|---|---|
| reached Dlvl 6+ / 10+ | 60 / 9 | 71 / 9 | 71 / 13 | 61 / 6 |
| died on Dlvl 6-9 | 43 | 53 | 49 | 47 |
| escapes | 12 | 14 | 19 | 18 |
| ant deaths / gaze freezes | 13 / 8 | 11 / 6 | 8 / 1 | 11 / 0 |
| crashes | 4 | 4 | 9 | 5 |

Kept: never melee a seen floating eye (the bot did it when `allow_attack_all` left only
attacks). Also fixed: a missing `sokoban_live_solved` stat crashed every game whose
Sokoban level the live solver finished. Elbereth works when written (monsters hit the
bot on it in 2 of 109 cases), but in 64 of 109 the bot walked off within 30 turns,
often at a few HP; ~15% of dust engravings come out misspelled and get rewritten.
Resting on Elbereth below half HP until 80% gave no gain (more fainting deaths), not kept.

## Hunger (2026-10-19, 192 unforced games each)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Diagnostics: most characters that starve carry no food and live on prayer (566 of 643
prayers succeeded); death comes when a game drags on until a prayer is too early. Long
games were stuck (way home blocked, endless search for Sokoban or the Mines). Some
characters prayed when Weak while carrying food rations, because prayer is the top
emergency action. Waiting next to peaceful monsters that block a path (shopkeeper by the
door, gnomes in Mines passages) was tried: escapes fell from 39-46 to 28, not kept.

| | before | eat carried food at Weak + dive after 2500 turns without progress |
|---|---|---|
| reached Dlvl 6+ / 10+ | 69 / 10 | 81 / **23** |
| hunger deaths | 25 | 25 (14 now while diving on Dlvl 2-5) |
| escapes | 16 | 11 |
| goals pilgrim / daredevil / sightseer / treasure | 0/46, 6/51, 9/50, 0/45 | 0/40, 8/56, 8/56, 0/40 |
| games that gave up their route to dive | - | 45 |

Prayer facts (NetHack wiki, Prayer timeout): a successful prayer resets the timeout to
rnz(350), usually 50-1000; major trouble needs it below 200; 95% safe only after ~1230
turns. The bot prays at 500 (HP) / 400 (hunger) turns.

Stuck divers (diagnostic, 192 games): 44 had a diving character with no new level for
3000+ turns: 20 in the Gnomish Mines (diving ignored Mines downstairs and tried to climb
back out through a blocked route), 23 in the main dungeon with no downstairs found (only
4 carried a pick-axe). Fix: divers in the Mines head down the Mines; when stuck there
(Mines' End) they go back and dive the main dungeon. Result: Dlvl 6+ / 10+ 84 / 20,
escapes 15, hunger deaths still 25 (three runs in a row), now split into early starvation
of weak roles on Dlvl 2-4 (turn 1300-4500) and long games (6000+ turns).

Downstairs search (2026-10-19): searching a dead end ~25 times instead of ~11 (each search
finds an adjacent hidden passage with ~1/7 chance) plus a bonus for walls near large
unexplored areas, used only when nothing is left to visit. Games with a 2500-turn spell
of diving without finding a way down went from 11 to 22 per 192; Dlvl 6+ 92 -> 76. Not
kept. Note: two 192-game runs of identical code gave 15 and 3 escapes and 20 / 14 games
at Dlvl 10+, so single runs are noisier than assumed for rarer outcomes.

## Sokoban first, digging down, boulders (2026-10-20, 576 unforced games each)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Measured on 576 games each, since 192-game runs proved too noisy (sightseer escapes varied
from 10 to 24 between runs that do not change sightseers).

| | baseline | + Sokoban-first pilgrim (human/elf/orc) | + dig down | + push boulders |
|---|---|---|---|---|
| reached Dlvl 6+ / 10+ | 241 / 54 | 251 / 67 | 253 / 55 | 262 / 68 |
| hunger deaths | 73 | 62 | 75 | 74 |
| pilgrims: median depth / Dlvl 10+ | 5 / 22 | 5 / 22 | 6 / 14 | 6 / 19 |
| stuck-diver games / stuck spells | 56 / 102 | 52 / 114 | 55 / 141 | 55 / 163 |
| crashes (cyclic panic) | 18 | 11 | 9 | 13 |

Kept: Sokoban-first pilgrims for races the Mines natives attack (neutral on depth, more
Sokoban). Reverted: digging down (escape at critical HP with a known wand of digging, or
when stuck) and pushing boulders when stuck; neither freed stuck divers measurably.

## Crashes (2026-10-20, 576 unforced games each)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Every crash was a "Cyclic Panic": NetHack refused an action without game time passing and
the bot asked again until the turn-inactivity guard (200 steps) ended the game. Crash
reports now name where each error was raised and the bot's call chain.

| | baseline | + six cause fixes | + kick, rings, stale boxes | + unstick safety net |
|---|---|---|---|---|
| crashes | 9 | 6 | 7 | 2 |
| reached Dlvl 6+ / 10+ | 244 / 45 | 262 / 55 | 259 / 63 | 263 / 60 |
| escapes | 41 | 30 | 25 | 33 |
| median turns | 4929 | 4816 | 4984 | 4934 |

Cause fixes: drop spare items when Overtaxed (can't eat); stop putting on armour NetHack
refuses (boots while trapped); parse inventory lines NLE cuts at 80 characters and worn
rings; treat containers NetHack calls "empty" as empty (also clears remembered contents);
leave items at the bottom of a pit we teeter at the edge of; no kicking for 100 turns after
NetHack refuses a kick (wounded legs). The long tail (wield what is wielded, loot without
a free hand, ...) is caught by the safety net: after 100 steps without game time the bot
searches once and replans (`unsticks` in results). It fired in 2 of 576 games; one healer
stayed stuck ~3000 turns before dying. Left: polymorphed "physically incapable of picking
anything up" and ball-and-chain parsing (1 each).

## Bench server (2026-10-20)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Benchmarks now run through `screens-bench` (see README). The choke-points validation
experiment (`choke-points` vs `aa4b1cf`, metric dlvl6, 1152 games per side, of which 1728
imported from the earlier benchmark files) ended as: no measurable difference at 1152,
difference +0.3% (95% interval -3.7% .. +4.4%; smaller real effects than about 4 points
cannot be seen at this size). The first choke run's +4 points at 576 stayed "open".

Imported yardstick: 687 ascensions from hardfought.org (NetHack 5.0 and 3.6), 199 with
dumplogs. Median turns: Mines 1173, Minetown 3538, Sokoban 9022 (solved 12412), Quest
22426, Medusa 29317, Gehennom 34155, invocation 49741, ascension 53630 (5.0 timelines).
At the end 100% have magic resistance, 99% a bag of holding, 83% reflection; median XL 23,
AC -38; wands of teleportation 89%, death 83%, digging 64%.

## Ascension ladder baseline (2026-10-21, 576 unforced games of `2653410`)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

First baseline with the ladder (sub-project 0, `autoascend/ladder.py`). "Reached" counts
games whose highest rung is this one or higher; turns are medians of the games that
recorded the rung. No ladder errors; 4 crashes (Cyclic Panic, inventory parsing).

| # | Rung | Reached | Our median turn | Ascenders' median turn |
|---|------|---------|-----------------|------------------------|
| 1 | Gnomish Mines | 331 (57%) | 2566 | 1173 |
| 2 | Minetown | 165 (29%) | 5787 | 3538 |
| 3 | Oracle | 126 (22%) | 5769 | — |
| 4 | Sokoban | 54 (9%) | 7323 | 9022 |
| 5 | Sokoban solved | 30 (5%) | 9832 | 12412 |
| 6 | Mines' End | 25 (4%) | 8617 | 10853 |
| 7 | Dlvl 15+ | 11 (2%) | 11538 | — |
| 8 | Quest | 1 | 12806 | 22426 |
| 9-17 | Medusa … Ascended | 0 | — | — |

Highest rung per game: 0: 245, 1: 166, 2: 39, 3: 72, 4: 24, 5: 5, 6: 14, 7: 10, 8: 1; the
median game reaches rung 1 for every strategy. Sokoban was solved (rung recorded) in 5
games, all treasure hunters. The one Quest game was a monk pilgrim who stepped into the
Quest portal on Dlvl 15 at turn 12806 and died to a xorn there. Other numbers as before:
Dlvl 6+ 49%, Dlvl 10+ 12%, median depth 5, median 5258 turns.

## Threat model (2026-10-21, rung2 = Minetown+, 1152 unforced games per side, baseline `2653410`)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Idea: judge monsters by NetHack's own numbers (monster level, speed and attack dice from
NetHack 3.6.6 `monst.c`, hit chance as in `mattacku`) instead of AutoAscend's name lists
and fixed HP limits. Branch `threat-model` (not merged; it holds the generated attack
table `autoascend/combat/monster_data.py`, the generator and `combat/threat.py`).

| Variant | Commit | rung2 | Verdict |
|---------|--------|-------|---------|
| baseline | `2653410` | 26.8% | — |
| all three predicates (dangerous, faster, near death at HP <= 2 x damage/turn) | `46a7003` | 23.1% | worse, -3.7 [-7.3, -0.2] |
| real danger + real speed, upstream near-death limits (16 / 8) | `ace25e2` | 24.3% | no measurable difference, -2.5 [-6.1, +1.0] |
| real danger only (upstream speed list and limits) | `fdf6b48` | 24.6% | no measurable difference, -2.3 [-5.8, +1.3] |

All variants include the fix of `elbereth_action` counting weak monsters as weak.
With the first variant ant deaths rose (soldier ant 35 -> 49) and giant bat deaths fell
(33 -> 18); the bot wrote Elbereth 35% more often. "Near death" stops the bot from
striking first, and against fast monsters that only gives them free hits; "faster" for
ants doubles their Elbereth weight, and a dust Elbereth (73% success) costs a turn.
AutoAscend's heuristics are tuned around its own lists, so swapping the lists alone does
not help. Noise check: the baseline's two halves of 576 games differ by 3.6 points.
Next: learn from recorded human games what actually saves characters on Dlvl 3-8.

## Flee upstairs from fast insects (2026-10-21, rung2, 1152 unforced games per side)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Idea from human games (NLD-NAO part `aa`, 3.6 games Dlvl 4+): of 682 players who survived
a soldier ant 31% went upstairs soon after seeing it, of 145 it killed 6%. Rule (branch
`flee-upstairs`, `a535f7a`, not merged): in a fight with a soldier/fire/giant ant or killer
bee within 6 squares, climb the up stairs if on them, else step toward stairs within 8
steps; not on Dlvl 1, only in the main dungeon and the Mines, 150-turn cooldown per level.
It fired in 200 of 1152 games; insect deaths 96 vs 89; rung2 23.6% vs 26.8%: no
measurable difference (-3.2 [-6.7, +0.3]).

**Control (A/A) test:** `0c7acbc` (same code as `2653410`, only docs changed) against
`2653410`: -2.3 [-5.9, +1.2], no measurable difference. So the baseline sample came out
high, and every experiment against it (threat model x3, flee) looked 2-4 points worse
without being worse: none of them differs measurably from changing nothing. All code-
identical games pooled: rung2 25.6% (2304 games). Lesson: unseeded games need a fresh or
pooled baseline; next, seed both sides with the same games so dungeon luck cancels out.

## Ascension route only (2026-10-21, main `dbab398`)

*Not comparable with Phase 1 numbers: mixed strategies and/or unseeded games (see "Phase 1: seeded pilgrim-only bench").*

Every game plays the pilgrim route now (`strategy = "random"` in the config brings the
mix of all four plans back). In the 1152 games of `2653410` pilgrims reached Minetown+ in
35%, daredevils and sightseers in 20%: the other plans diluted every measurement.
New baselines are needed; numbers before this change are not comparable.

## Phase 1: seeded pilgrim-only bench (2026-10-23)

Rules, names and ledger: `.planning/phases/01-midgame-survival/01-EXPERIMENT-PROTOCOL.md`.

survival-tuning `ade24fb74a0f141745633820eb0eba66cfd04ad5`: no commits main lacks; deleted 2026-10-24; its three stashes ("On survival-tuning") are kept.

### Determinism (MEAS-03)

A seeded game now plays the same way every time, on any machine load: the moon phase comes
from the seed (`fix_moon_phase`), the live Sokoban solver stops on a state budget only
(40,000 states, at most 8.4 s, no wall-clock limit), bench workers run with
`PYTHONHASHSEED=0` and one BLAS thread, and NetHack's start time is pinned per seed
(`fixed_clock`, so shopkeeper names come from the seed). What still does not replay: the
120 s screen watchdog (a game that hangs ends "watchdog"; replay checks skip and list those
seeds), and unseeded screensaver games, which use the real clock on purpose. Tests:
`tests/test_replay.py` (same seed in two fresh processes gives the same game and sees the
pinned time), `tests/test_fixed_clock.py`.

### A/A control

Attempt 1 (job 9, 2026-10-23): `6ce5ac50d334232a20f08dda58410c131b12df6a` against its
docs-only twin `be40c7c9f6874d958a37ec0f17ac775f480c9c02`, rung2, 1152 seeds per side.
Verdict no measurable difference (0.0 [0.0, 0.0]), but the replay check failed: 44 of 1149
seeds played differently. Cause: the start time picks shopkeeper names; 43 seeds differed
only in names, seed 1127 in play (reproduced by faking the start time: 4067 turns at one
time, 4754 at another). Fix: `e3f0dd7` (`fixed_clock`).

Attempt 2 (job 10, 2026-10-23): `p1-aa-base` = `e3f0dd7ab7054901d93dab9ef586b50154fb963a`,
`p1-aa-twin` = `2c567b5b5deb60bc9147b79437f62dba3d473dcf` (docs only), rung2, 1152 seeds
(0..1151) per side. Verdict: no measurable difference, 0.0 [0.0, 0.0] points; rung2 26.1%
(301 of 1152) on both sides. Replay check: 1149 seeds compared, 0 mismatched; 3 skipped
(watchdog: seeds 227, 436, 690). Speed: 39.2 games/min against 36.2 for job 9 (+8%, 11
workers, whole-run average).

This proves the bench replays identical code identically; it says nothing yet about how
small a real difference it can see (that is plan 01-06).

A/A control: passed for `e3f0dd7ab7054901d93dab9ef586b50154fb963a`

Attempt 3, Valkyrie only (job 13, 2026-10-24): the owner fixed the character to a dwarvish
Valkyrie until the first ascension (`CHARACTER = "val-dwa-fem-law"` in `game.py`, `"@"` for
random characters). `p1-valk-base` = `0b097073adb3071f8e5c2aea954618a3320a5bc7`,
`p1-valk-twin` = `00006e4f07d28bf93218fd7be1f7e0214a99c69a` (docs only), rung2, 1152 seeds
per side: no measurable difference, 0.0 [0.0, 0.0]; replay check 1133 seeds compared, 0
mismatched, 19 skipped (watchdog: seeds 13, 43, 70, 210, 217, 326, 350, 376, 404, 478, 506,
643, 672, 680, 741, 768, 801, 901, 1100). 23.5 games/min (longer games).

Valkyrie ladder (1152 games): Mines 73%, Minetown 44%, Oracle 29%, Sokoban 18%, Sokoban
solved 15%, Mines' End 14%, Dlvl 15+ 8%, Quest 2%, Medusa 1% (10 games, the first ever); all
roles before: Minetown 26%, nothing past the Quest. Every watchdog game is a deep one
(Dlvl 11-28, rung 7-8): the 120 s watchdog ends the best games, a problem for later rungs.

A/A control: passed for `0b097073adb3071f8e5c2aea954618a3320a5bc7`

### Bench speed

One BLAS/OpenMP thread per worker (shipped in `e3f0dd7`, before it 11 workers ran ~34
threads each on 12 cores): 36.2 -> 39.2 games/min (+8%, whole-run averages of the two
2304-game A/A jobs). Below the 10% bar set in plan 01-06, but kept: it is part of the gated
SHA and removes multi-threaded float sums as a replay risk; the A/A replay check covered it
(1149 seeds, 0 mismatched).

Turn cap: not adopted. In the 1152 games of `p1-aa-base` (turns as the time measure; wall
time per game is not stored) turn deciles are 2296, 3163, 3914, 4963, 5719, 6702, 7792,
9505, 13235, max 43361.

| Cap T | Games longer | Share of all turns past T | First reach rung 2-6 after T |
|-------|--------------|---------------------------|------------------------------|
| 20k   | 40           | 3.1%                      | 6 (0.52%)                    |
| 30k   | 10           | 0.6%                      | 1 (0.09%)                    |
| 50k   | 0            | 0.0%                      | 0                            |

The rule needed >= 25% of the time past T: long games are rare and cheap.

### Bench resolution (calibration)

Divergence controls: the bot's own RNG seed 1 instead of 0 (`AGENT_ARGS seed=1`), nothing
else, against the same seeds (2026-10-24). Valkyrie only; the first control (job 11, all
roles, `calib/agent-seed-1` vs `p1-aa-base`) gave q 0.317, half-width 3.3 points, before
the switch.

| Variant | Candidate | Baseline | n | n10 | n01 | q | diff | half-width | MDE80 |
|---------|-----------|----------|---|-----|-----|---|------|------------|-------|
| current seeding (job 14) | `calib/valk-agent-seed-1` | `p1-valk-base` | 1152 | 287 | 247 | 0.464 | +3.5 | 3.93 | 5.6 |
| lgen seeded (job 15) | `calib/valk-lgen-agent-seed-1` | `calib/valk-lgen` | 1152 | 243 | 248 | 0.426 | -0.4 | 3.77 | 5.4 |

A changed bot RNG alone changes the rung2 outcome of 43-46% of Valkyrie seeds: the dungeon
is the same, the bot's path through it is not, so pairing removes little noise.

- lgen: not adopted. It needed half-width <= 3.73 (h0 - 0.2) and no new exception type; it
  gave 3.77 and brought ZeroDivisionError and OverflowError cyclic panics that `p1-valk-base`
  lacks (24 exceptions each). No second A/A: `p1-valk-base` stays the measurement code.
- 2304 checkpoint: adopted (`b5960c2`), h = 3.93 > 2.0. It changes no game, so the A/A
  replay proof stands.

`calib/agent-seed-1`, `calib/lgen`, `calib/lgen-agent-seed-1`, `calib/valk-agent-seed-1`,
`calib/valk-lgen` and `calib/valk-lgen-agent-seed-1` are calibration-only branches, kept unmerged.

Bench resolution: half-width 2.8 points on rung2 at 2304 games per side (MDE80 about 4.0 points; projected for 2304 as h/sqrt(2)); level generation seeded: no; checkpoints: (192, 384, 576, 1152, 2304).

### Screening metric

To drop losing ideas early, each metric's resolution was measured on the Valkyrie divergence
control (`calib/valk-agent-seed-1` vs `p1-valk-base`, first 384 seeds), as half-width (95%)
divided by the SD of per-game values (smaller is better). Numeric metrics use the new paired
mean-difference judge (`bench.stats.judge_paired_numeric`, `seeded_report.py pairs --metric <numeric>`).

| Metric | Kind | Half-width at 384 | Standardized |
|--------|------|-------------------|--------------|
| rung2 | rate | 8.8 points | 0.177 |
| rung (highest rung, 0-17) | numeric | 0.42 rungs | 0.182 |
| depth | numeric | 0.92 levels | 0.185 |
| turns | numeric | 1516 turns | 0.186 |
| score | numeric | 3929 points | 0.190 |

`deep_turns` (turns on Dlvl 4-12) is not derivable from stored games (no per-level turns), so it
was skipped. No numeric metric beats rung2 (the bar was 20% smaller): screening stays on rung2.
Rule (protocol step 7a): at 384 seeds, drop if the rung2 80% interval lies entirely below 0;
otherwise run on to the full rung2 verdict, which alone decides merges.

### Pilgrim-only baseline

Pilgrim-only baseline: `0b097073adb3071f8e5c2aea954618a3320a5bc7`

Code = main after plans 01-01..01-06 plus the owner's Valkyrie-only switch: every game a dwarvish
Valkyrie on the pilgrim route (Mines first), seeded games, moon and start time from the seed,
level generation not seeded separately.

Ladder, seeds 0..575, n = 576:

| # | Rung | Reached | Our median turn | Ascenders' median turn |
|---|------|---------|-----------------|------------------------|
| 1 | Gnomish Mines | 408 (71%) | 3604 | 1173 |
| 2 | Minetown | 250 (43%) | 7057 | 3538 |
| 3 | Oracle | 167 (29%) | 7948 | - |
| 4 | Sokoban | 97 (17%) | 11987 | 9022 |
| 5 | Sokoban solved | 79 (14%) | 14198 | 12412 |
| 6 | Mines' End | 75 (13%) | 11610 | 10853 |
| 7 | Dlvl 15+ | 47 (8%) | 17232.5 | - |
| 8 | Quest | 11 (2%) | 24718 | 22426 |
| 9 | Medusa | 6 (1%) | 21779 | 29317 |
| 10 | Castle | 0 (0%) | - | - |
| 11 | Gehennom | 0 (0%) | - | 34155 |
| 12 | Vlad's Tower | 0 (0%) | - | 44189 |
| 13 | Wizard's Tower | 0 (0%) | - | 49072 |
| 14 | Invocation | 0 (0%) | - | 49741 |
| 15 | Elemental Planes | 0 (0%) | - | 53180 |
| 16 | Astral Plane | 0 (0%) | - | 53518 |
| 17 | Ascended | 0 (0%) | - | 53630 |

Ladder, seeds 0..2303, n = 2304:

| # | Rung | Reached | Our median turn | Ascenders' median turn |
|---|------|---------|-----------------|------------------------|
| 1 | Gnomish Mines | 1687 (73%) | 3643 | 1173 |
| 2 | Minetown | 1011 (44%) | 7235 | 3538 |
| 3 | Oracle | 680 (30%) | 9051.5 | - |
| 4 | Sokoban | 409 (18%) | 11878.5 | 9022 |
| 5 | Sokoban solved | 349 (15%) | 14529.5 | 12412 |
| 6 | Mines' End | 335 (15%) | 12106.5 | 10853 |
| 7 | Dlvl 15+ | 192 (8%) | 17199.5 | - |
| 8 | Quest | 33 (1%) | 15403 | 22426 |
| 9 | Medusa | 14 (1%) | 20809.5 | 29317 |
| 10 | Castle | 0 (0%) | - | - |
| 11 | Gehennom | 0 (0%) | - | 34155 |
| 12 | Vlad's Tower | 0 (0%) | - | 44189 |
| 13 | Wizard's Tower | 0 (0%) | - | 49072 |
| 14 | Invocation | 0 (0%) | - | 49741 |
| 15 | Elemental Planes | 0 (0%) | - | 53180 |
| 16 | Astral Plane | 0 (0%) | - | 53518 |
| 17 | Ascended | 0 (0%) | - | 53630 |

For orientation only (not comparable: all roles, unseeded, mixed strategies): the 2026-10-21
table of `2653410` had Minetown+ 28% and nothing past the Quest; all-role pilgrims in the
Phase 1 A/A had Minetown+ 26%.

Killers, seeds 0..2303, n = 2304, all depths (top rows; rows overlap):

| Ending | Count | % of games | % of deaths | Median depth | Median turns |
|--------|-------|------------|-------------|--------------|--------------|
| starved | 576 | 25.0% | 26.1% | 5 | 9022 |
| ants | 193 | 8.4% | 8.8% | 6 | 8028 |
| killer bee | 60 | 2.6% | 2.7% | 5 | 6471 |
| wand | 89 | 3.9% | 4.0% | 3 | 2739 |
| rays | 116 | 5.0% | 5.3% | 6 | 8190 |
| breath | 4 | 0.2% | 0.2% | 11 | 17105 |
| exception | 48 | 2.1% | - | 11 | 17148 |
| watchdog | 46 | 2.0% | - | 24 | 22928 |
| escaped/other endings | 182 | 7.9% | - | 7 | 9163.5 |
| gray unicorn | 36 | 1.6% | 1.6% | 6 | 7171 |
| mumak | 33 | 1.4% | 1.5% | 8 | 10947 |
| leocrotta | 27 | 1.2% | 1.2% | 10 | 10435 |
| Woodland-elf | 25 | 1.1% | 1.1% | 7 | 8985 |
| hill orc | 23 | 1.0% | 1.0% | 4 | 7342 |
| troll | 21 | 0.9% | 1.0% | 12 | 14550 |
| black unicorn | 20 | 0.9% | 0.9% | 6.5 | 8542.5 |
| owlbear | 19 | 0.8% | 0.9% | 8 | 12456 |
| rothe | 17 | 0.7% | 0.8% | 4 | 7090 |
| Green-elf | 17 | 0.7% | 0.8% | 10 | 10703 |
| vampire lord | 16 | 0.7% | 0.7% | 11 | 9346.5 |
| wolf | 16 | 0.7% | 0.7% | 6 | 6996.5 |
| gargoyle | 15 | 0.7% | 0.7% | 10 | 10145 |
| Uruk-hai | 15 | 0.7% | 0.7% | 6 | 7429 |
| werewolf | 15 | 0.7% | 0.7% | 6 | 6516 |

Killers, seeds 0..2303, games that ended on Dlvl 4-12 (n = 1710; top rows):

| Ending | Count | % of games | % of deaths | Median depth | Median turns |
|--------|-------|------------|-------------|--------------|--------------|
| starved | 419 | 24.5% | 25.0% | 5 | 8942 |
| ants | 182 | 10.6% | 10.9% | 6 | 7943 |
| killer bee | 59 | 3.5% | 3.5% | 5 | 6469 |
| wand | 35 | 2.0% | 2.1% | 4 | 5118 |
| rays | 78 | 4.6% | 4.7% | 7 | 9384 |
| breath | 4 | 0.2% | 0.2% | 11 | 17105 |
| exception | 25 | 1.5% | - | 7 | 13639 |
| watchdog | 5 | 0.3% | - | 11 | 14533 |
| escaped/other endings | 151 | 8.8% | - | 7 | 8446 |
| gray unicorn | 36 | 2.1% | 2.1% | 6 | 7171 |
| mumak | 32 | 1.9% | 1.9% | 8 | 10868.5 |
| Woodland-elf | 25 | 1.5% | 1.5% | 7 | 8985 |
| leocrotta | 22 | 1.3% | 1.3% | 10 | 9184 |
| black unicorn | 20 | 1.2% | 1.2% | 6.5 | 8542.5 |
| hill orc | 20 | 1.2% | 1.2% | 4.5 | 7521 |
| owlbear | 19 | 1.1% | 1.1% | 8 | 12456 |
| wolf | 16 | 0.9% | 1.0% | 6 | 6996.5 |
| Green-elf | 16 | 0.9% | 1.0% | 9 | 10471 |
| vampire lord | 15 | 0.9% | 0.9% | 11 | 9245 |
| Uruk-hai | 15 | 0.9% | 0.9% | 6 | 7429 |
| werewolf | 15 | 0.9% | 0.9% | 6 | 6516 |
| troll | 14 | 0.8% | 0.8% | 11 | 18331.5 |
| rothe | 14 | 0.8% | 0.8% | 4.5 | 6705 |
| watch captain | 14 | 0.8% | 0.8% | 6.5 | 9588 |

Starvation ends 25% of all games (26% of deaths), three times the next killer (ants 8%).


### Starvation diagnosis (D-09, D-10)

`seeded_report.py starvation p1-baseline --seeds 2304`: 576 starvation games (25% of all games;
starved, or killed while fainted). Buckets, first match wins: a failed prayer in the last 1000
turns; food carried at the end; a successful prayer in the last 1000 turns; no prayer then.

| Bucket | Games | % of starvation games | Median turns | Median depth | Top roles | fainted-kill | starved | early | long | stuck |
|---|---|---|---|---|---|---|---|---|---|---|
| failed-prayer | 481 | 83.5% | 9125 | 5 | val | 377 | 104 | 40 | 372 | 138 |
| food-carried | 7 | 1.2% | 9105 | 5 | val | 2 | 5 | 1 | 6 | 1 |
| prayer-cooldown | 85 | 14.8% | 8320 | 5 | val | 85 | 0 | 8 | 54 | 15 |
| prayer-unused | 0 | 0.0% | - | - | - | 0 | 0 | 0 | 0 | 0 |
| other | 3 | 0.5% | 7884 | 4 | val | 3 | 0 | 1 | 2 | 1 |

Failed prayers per game: 1 in 195 games, 2+ in 286 (59%); median gap from the previous prayer to
the first failed one: 851 turns. 567 of the 576 starvers carried no food at all at the end.

The bot lives on prayer: across all 2304 games it prayed 12,689 times, 0.49 prayers per 1000
turns, median gap 868 turns; 8.9% of prayers failed (1125). Next to the humans of
`01-HUMAN-STUDY.md` (Dlvl 4-12): humans who got through prayed 0.15 per 1000 turns with a median
gap of 2,715 turns and 2.8% failures; human starvers 0.34 per 1000, gap 946, 14.9% failed. So the
bot prays like a human starver, three times as often as a survivor, every ~870 turns for hunger
("Your stomach feels content"), and when the prayer timeout happens to be long the prayer fails
and the next ones fail too ("Thou art arrogant", lost levels). Humans eat 2.8 meals per 1000
turns; the bot's meals and hunger time are not stored, so those human rows cannot be matched.

Ranked causes (in scope unless marked):
1. Repeated prayers after a failure (failed-prayer, 2+ failures in 59%): each further failure costs
   luck and levels while fainting. Experiment 1.
2. No food supply (98% carry no food at the end, every bucket): the bot eats corpses and prays,
   but does not keep food. Experiment 2 (see its entry: the 20% bucket rule does not see it,
   because every bucket shares it).
3. Prayer-cooldown (14.8%): food gone and the prayer timeout not over.
4. `stuck` tags (138 of 481 failed-prayer games, 29%): below 50% in every bucket, so no bucket is
   out of scope.

### Killer order (D-07)

Baseline shares on Dlvl 4-12 (games that ended there, n = 1710): starvation 24.5%, ants and killer
bees 14.1% (10.6 + 3.5), wand users and rays 6.6% (2.0 + 4.6). Order for the following plans:
- starvation (01-08): largest share, and the cause is a single habit (prayer as food), so one
  change can move many games per bench hour;
- rest to full HP (01-09): acts on every HP-driven death at once, including ants and zaps, and
  its plumbing is reused;
- ants and bees (01-10): second largest band killer, a fight-or-flee rule per monster type;
- wand and ray users (01-11): mixed causes (striking wands, monster rays, breath, divine lightning)
  need the zap/prayer context first, so less gain per hour;
- the three old branches (01-12..01-14, one plan each): prior near zero (PORTING.md control test).

### Ants and bees diagnosis (SURV-04)

`seeded_report.py insects p1-baseline --seeds 2304` (baseline `0b09707`): 253 insect deaths, 56 of them
while fainted from hunger (starvation's, excluded). The other 197:

| Killer | Games | % of all games | % of Dlvl 4-12 deaths | Median depth | Median XL |
|---|---|---|---|---|---|
| soldier ant | 105 | 4.6% | 6.1% | 6 | 7 |
| giant ant | 16 | 0.7% | 0.9% | 4 | 5 |
| fire ant | 34 | 1.5% | 1.7% | 6 | 7 |
| killer bee | 42 | 1.8% | 2.4% | 5 | 6 |

A1 prayer unused (no prayer in the last 1000 turns): 24.4%. A2 poison in the last messages: 26.4%.
Rule (fixed in plan 01-10 before the numbers): pray-earlier if A1 >= 40%; else poison-resistance if
A2 >= 25%; else close-door. **Tactic: poison-resistance** (eat fresh killer bee and soldier ant corpses
when healthy). It differs from the dropped tries: doorway fighting, threat numbers and fleeing upstairs
change how the fight is fought; this changes the hero before the next fight (3.6 poison can kill
outright or drain Str; resistance removes both). The guides agree: "Eat any corpse that is safe and has a
chance of granting poison resistance" (Furey's tips, nethackwiki).

### Wand and ray users diagnosis (SURV-03)

`seeded_report.py zappers p1-baseline --seeds 2304`: 209 wand and ray deaths (9.1% of games).

| Class | Games | % of zapper deaths | % of all games | Median depth | Median XL | Top killers |
|---|---|---|---|---|---|---|
| Z1 divine (lightning/disintegration within 10 turns of a prayer) | 8 | 3.8% | 0.3% | 6.5 | 7 | bolt of lightning 8 |
| Z2 warned (2+ zaps seen, or "zaps" before the last message) | 160 | 76.6% | 6.9% | 4 | 4.5 | wand 81, magic missile 38, bolt of fire 20 |
| Z3 breath ("blast of") | 4 | 1.9% | 0.2% | 11 | 9 | disintegration 2 |
| Z4 unwarned | 37 | 17.7% | 1.6% | 6 | 7 | bolt of fire 10, death ray 10 |

Rule (fixed in plan 01-11 before the numbers): stop-praying-after-failure if Z1 >= 30% and not on main; else
leave-breath-line if Z3 is the largest of Z2-Z4; else leave-zap-line. **Tactic: leave-zap-line.** The bench's
`rays` metric is 96% monster zaps: divine lightning (3.8%) and breath (1.9%) are small. Most zapper deaths are
early (median Dlvl 4, XL 4-5: gnome lords and dwarves with wands in the Mines) after the bot saw at least two zaps.

### Stuck diagnosis (DESC-03)
Rule (plan 02-05, fixed before the numbers): among the Current baseline games failing `free5`, the bucket of
their last stuck report; stairs-unreachable >= 35% -> clear-way; else stairs-reachable >= 35% -> take-it;
else no-way-found >= 35% -> escape-cheese; else -> frontier-first.

Shares (410 games of `6502ae3`): explore-left 27.6%, stairs-unreachable 26.1%, stairs-reachable 24.9%,
no-way-found 19.3%, no-report 2.2%. No bucket reaches 35% -> **frontier-first**.

Sub-causes seen in a replay (seed 2242, Mines level 2, Dlvl 5): the stuck watch counts turns since the last new
level, so it fired while the bot was still uncovering a part of the level it had just found (frontier 10 at
distance 7-17); about 1400 of the 2500 turns before were searches at one dead end, useless in the Mines.

Tactic: when the stuck watch fires and the reachable map has squares beside unexplored map, walk to the nearest
one directly (ignoring the explorer's search scoring), until none is left or 1000 turns pass, once per level;
then try the level again. New: the dropped ideas searched harder for hidden passages; this stops giving up on
a level whose known map is not finished.

### Experiments

Phase 1 final baseline: `3fca503215e1a3de57e775378a1598fb05a40c20` (exp/shop-door, kept 2026-10-24; before: `0b097073adb3071f8e5c2aea954618a3320a5bc7` pilgrim-only baseline)

| # | Branch | Cause | Candidate | Baseline | Metric | Verdict | Diff [lo, hi] (points) | Decision |
|---|--------|-------|-----------|----------|--------|---------|------------------------|----------|
| 1 | `exp/starvation-1` | repeated failed prayers | `a8e8065` | `0b09707` | rung2 | no measurable difference @ 2304 | +0.0 [-0.2, +0.2] | dropped |
| 2 | `exp/starvation-2` | stuck on levels with a hidden way on | `9ca5d8b` | `0b09707` | rung2 | no measurable difference @ 2304 | -1.1 [-3.9, +1.7] | dropped |
| 3 | `exp/rest-to-full` | HP-driven deaths (rest, food-scaled) | `894084d` | `0b09707` | rung2 | no measurable difference @ 2304 | -1.5 [-4.2, +1.2] | dropped |
| 4 | `exp/ants-bees` | ants and bees (poison resistance corpses) | `9ca4f31` | `0b09707` | rung2 | worse @ 2304 | -1.5 [-2.6, -0.3] | dropped |
| 5 | `exp/shop-door` | angry shopkeepers (kicked shop doors) | `3fca503` | `0b09707` | rung2 | better @ 384 | +3.1 [+0.8, +5.4] | kept |
| 6 | `exp/zappers` | wand and ray users (leave zap lines) | `d7d5e6b` | `3fca503` | rung2 | no measurable difference @ 2304 | +0.1 [-0.8, +0.9] | dropped |
| 7 | `rejudge/threat-model` | old branch re-judged (real danger only) | `8284811` | `3fca503` | rung2 | no measurable difference @ 2304 | +0.3 [-1.2, +1.7] | dropped |
| 8 | `rejudge/choke-points` | old branch re-judged (fight from corridors) | `339a63c` | `3fca503` | rung2 | no measurable difference @ 2304 | +1.2 [-0.1, +2.5] | dropped |
| 9 | `rejudge/flee-upstairs` | old branch re-judged (flee up stairs) | `757aad8` | `3fca503` | rung2 | no measurable difference @ 2304 | +0.5 [-0.9, +1.9] | dropped |

#### Experiment 1: `exp/starvation-1` - repeated prayers after a failed one
- Requirement / decisions: SURV-02 (D-07, D-08, D-09); decision-table row "failed-prayer, at least 50% with 2+ failures" (59%)
- Change: `Agent.pray` classifies its messages with `prayer_outcome`; after a failure `is_safe_to_pray` is False for `PRAYER_FAILURE_PAUSE` = 1000 turns (`autoascend/agent.py`); counter `prayer_failed`
- Candidate `a8e8065c58609c416be1441200370f3c953a73c5`; baseline `0b097073adb3071f8e5c2aea954618a3320a5bc7`; primary metric `rung2` (152 of 576 baseline starvers, 26%, had rung >= 2: below the 60% rule); games: screen at 384 (protocol 7a), then to the last checkpoint (diagnosis-backed)
- Mechanism metrics: `starved`, `died`, `events.prayer_failed`
- Screen (384 seeds, 80%): rung2 +0.3 [-0.1, +0.6], 1 of 384 seeds differs; not dropped
- Job 17: Verdict: no measurable difference at 2304 games per side, diff +0.0 points, 95% interval [-0.2, +0.2]
- Mechanism: starved +0.7 [+0.3, +1.2] (worse: 21 games starve that did not, 4 the other way); died +0.2 [+0.0, +0.4]; counter prayer_failed fired in 557 of 2304 games; crashes: same type (RuntimeError Cyclic Panic, 43 vs 48)
- Reading: pausing prayer after a failure only moves the death: a hero with no food who may not pray starves anyway, a little more often. The cause is the empty food supply, not the prayer timing (experiment 2).
- Decision: dropped (branch `exp/starvation-1` kept at `a8e8065c58609c416be1441200370f3c953a73c5`)

#### Experiment 2: `exp/starvation-2` - starvers stuck on levels whose way on is hidden
- Requirement / decisions: SURV-02 (D-07, D-08, D-09). Recorded deviation from the 20% bucket rule: the next
  bucket (prayer-cooldown, 14.8%) is below 20%, but 567 of 576 starvers carried no food, so the food supply
  was diagnosed instead (local replays, scratch counters, not merged).
- Diagnosis: 22 starvers vs 22 long survivors: kills 5.3 vs 14.0 per 1000 turns, a similar share of corpses
  eaten (27% vs 30%). 44 starvers: median 3,900 turns (quartiles 1,800-6,700) since their last new level at
  death, 29 of 44 over 2,500; most in DIVE with no downstairs found, some on Dlvl 1-2 with half the map unseen
  (seeds 3, 65). 4 of 44 lost 1,000+ turns waiting beside a floating eye (fight2 "let it drift off"; later).
- Change: `far_side_walls` (`autoascend/exploration_logic.py`): squares beside the outermost wall on a side of
  the map with 8+ columns 95% unseen get the dead-end search bonus (250). mklev sorts rooms by x and joins
  neighbours, so that wall holds the (often secret) door on. Earlier 2026-10-19 search change bundled
  more searches per dead end with a vaguer bonus; this is the geometry alone. Counter `far_side_search`.
- Candidate `9ca5d8b2024e65a15dac6ba9b423d8dadf39d6f6`; baseline `0b097073adb3071f8e5c2aea954618a3320a5bc7`; primary metric `rung2` (26% of baseline starvers had rung >= 2: below the 60% rule); games: screen at 384, then to the last checkpoint (diagnosis-backed)
- Smoke (29 seeds): counter fired in 29 of 29; seed 3 Dlvl 1 -> 12, seed 65 Dlvl 2 -> 9; one Cyclic Panic (inventory.py:501, a type in 6 baseline games)
- Mechanism metrics: `starved`, `depth`, `dlvl10`, `crashed`
- Screen (384 seeds, 80%): rung2 +2.9 [-1.5, +7.3]; not dropped. Job 18 was interrupted at 1,517 games (bench server
  stopped by the host under memory pressure); job 19 resumed it from the stored games.
- Job 19: Verdict: no measurable difference at 2304 games per side, diff -1.1 points, 95% interval [-3.9, +1.7]
- Mechanism: starved +0.3 [-2.2, +2.7]; depth -0.14 [-0.44, +0.15] levels; dlvl10 -0.7 [-3.2, +1.9]; crashed +0.0
  [-0.8, +0.9]; counter far_side_search fired in 2304 of 2304 games; crashes: same types (Cyclic Panic 49 vs 48,
  watchdog 33 vs 46)
- Reading: the bonus applies on nearly every level while exits are still unvisited, so it reshuffles every game
  (838 of 2304 games change their starved result) without a net gain; the
  two smoke rescues (seeds 3, 65) were balanced by games it slowed. A later variant should fire only when
  nothing is left to visit (stuck), which is where the diagnosis found the hidden-way levels.
- Decision: dropped (branch `exp/starvation-2` kept at `9ca5d8b2024e65a15dac6ba9b423d8dadf39d6f6`)

#### Experiment 3: `exp/rest-to-full` - rest before exploring on, target scaled by food
- Requirement / decisions: SURV-01 (D-07 killer order); owner revision 2026-10-24: rest "close to full
  depending on how much food there is", not always to full
- Change: `autoascend/rest.py` `should_rest`, wired as `GlobalLogic.rest_to_full()` first in the exploration
  preempt list: with no hostile in view, search in 20-turn chunks up to a target that depends on the food
  cushion (carried edible nutrition + 900 if a hunger prayer is safe): >= 800 -> full HP (start below 90%);
  else Not Hungry, or Hungry with some food -> 85% (start below 75%); Hungry with nothing, or Weak -> no rest.
  400 resting turns per level at most. Counters `rest_start`, `rest_turns`. Regen below XL 10 is 1 HP per
  42/(XL+2)+1 turns (wiki Hit points), so each missing HP costs the same; food sets how many to buy.
- Candidate `894084deb01bfc8bf76ff2db1ffe0fa9a532778c` (first `6448532ae1b628e932152739ed58ff0c982562d3`, job 20, stopped at 1,278 games: seed 990
  looped on an empty-bag menu and two workers grew to 11 GB; rebased onto fix `16a6cb8`, which plays seeds 0-21
  identically to the baseline); baseline `0b097073adb3071f8e5c2aea954618a3320a5bc7`;
  primary metric `rung2` (777 of 1631 baseline deaths not from hunger or crashes, 48%, had rung >= 2: below
  the 60% rule); games: screen at 384, then to the last checkpoint (diagnosis-backed)
- Smoke (22 seeds): rest_start fired in 20 of 22, no exceptions, no watchdog; median rest_turns about 600 per game
- Mechanism metrics: `died`, `ants`, `rays`, `starved` (resting spends food), median `events.rest_turns`
- Screen (384 seeds, 80%): rung2 -0.3 [-4.7, +4.2]; not dropped
- Job 21: Verdict: no measurable difference at 2304 games per side, diff -1.5 points, 95% interval [-4.2, +1.2]
- Mechanism: starved +2.3 [-0.2, +4.8] (leaning worse); died +1.0 [-0.1, +2.1]; ants -0.5 [-2.0, +1.1];
  dlvl6 -1.3 [-4.0, +1.4]; dlvl10 -1.6 [-4.1, +0.9]; rested in 2259 of 2304 games, median 549 rest turns per
  game; crashes: same types, fewer (Cyclic Panic 38 vs 48, watchdog 30 vs 46)
- Reading: resting buys HP with food, and food is the bottleneck (25% of games starve). The few ant deaths it
  saves are paid back in starvation. Revisit once the food supply is fixed (Phase 2, stuck levels).
- Decision: dropped (branch `exp/rest-to-full` kept at `894084deb01bfc8bf76ff2db1ffe0fa9a532778c`)

#### Experiment 4: `exp/ants-bees` - poison resistance from killer bee and soldier ant corpses
- Requirement / decisions: SURV-04 (D-07, D-08, D-11 cheese allowed); tactic chosen by the rule in
  `### Ants and bees diagnosis (SURV-04)` (A2 poison 26.4% >= 25%)
- Change: `poison_corpse_ok` (`autoascend/agent.py`): fresh (< 50 turns) killer bee and soldier ant corpses are
  edible when HP >= 2/3 of max and > 15 (the poison costs rnd(15) HP and rnd(4) Str without resistance);
  "You feel healthy" sets `Agent.poison_resistant`, after which every poisonous corpse is edible (safe food).
  Counter `eat_for_poison_res`.
- Candidate `9ca4f3199664f4a2b80b100e798b78ac44332197`; baseline `0b097073adb3071f8e5c2aea954618a3320a5bc7`; primary metric `rung2` (74 of 197
  baseline insect deaths not while fainted, 38%, had rung >= 2: below the 60% rule); games: screen at 384, then to
  the last checkpoint (diagnosis-backed)
- Smoke (22 baseline insect-death seeds): counter fired in 8 of 22, no exceptions, no watchdog
- Mechanism metrics: `ants`, `died`, `starved`, insect killer counts (`seeded_report.py insects`) on both sides,
  `eat_for_poison_res`
- Screen (384 seeds, 80%): rung2 +0.0 [-1.8, +1.8]; not dropped
- Job 22: Verdict: worse at 2304 games per side, diff -1.5 points, 95% interval [-2.6, -0.3]
- Mechanism: ants +0.3 [-0.6, +1.2]; starved +0.3 [-0.9, +1.5]; dlvl6 -0.5 [-1.4, +0.4]; dlvl10 -1.1
  [-2.5, +0.4]; died +1.1 [+0.3, +1.9] (a game ending in DEATH instead of a crash or watchdog: crashes fell,
  exception 45 vs 48, watchdog 26 vs 46). Insect deaths 253 on both sides (soldier ant 106 vs 105, giant ant
  19 vs 16, killer bee 37 vs 42); A2 poison share 25.9% vs 26.4%
- Reading: eating the corpses does not reduce insect deaths; the bot dies to the first swarm, before a corpse
  can help, and the HP-cost of the poison (and the turns spent eating) cost depth elsewhere.
- Decision: dropped (branch `exp/ants-bees` kept at `9ca4f3199664f4a2b80b100e798b78ac44332197`)

### Shopkeeper diagnosis (SURV-03)
Found while smoking `exp/zappers`: 93 of 2304 baseline games (4.0%) die to a named zapper on Dlvl 2-5 at rung 0,
an angry shopkeeper with a wand of striking or magic missile (the zap-line regex matched none of them). Replays of
10 of them with the full message log: 9 read "Closed for inventory", find the door locked and kick it in ("How dare
you break my door?"); the tenth fought Keystone Kops after a shop theft. The 81 "killed by a wand" deaths are
mostly these.

#### Experiment 5: `exp/shop-door` - never kick a closed shop's door
- Requirement / decisions: SURV-03 (wand and ray users; shopkeepers are the largest named group)
- Change: reading "Closed for inventory" marks the orthogonal neighbours as `Level.closed_shop_door`; explore's
  `open_neighbor_doors` does not kick those (it still tries to open them). Counter `shop_door_spared`.
- Candidate `3fca503215e1a3de57e775378a1598fb05a40c20`; baseline `0b097073adb3071f8e5c2aea954618a3320a5bc7`; primary metric
  `rung2` (the targeted deaths are at rung 0); games: screen at 384, then to the last checkpoint
- Smoke (11 baseline shopkeeper-death seeds): counter fired in 11 of 11, no exceptions, no watchdog; all 11 now
  die later (median Dlvl 8, before Dlvl 2-5)
- Mechanism metrics: `rays`, `died`, `dlvl6`, `dlvl10`, `starved`
- Screen (384 seeds, 80%): rung2 +3.1 [+2.0, +4.3]; not dropped
- Job 23: Verdict: better at 384 games per side (sequential stop), diff +3.1 points, 95% interval [+0.8, +5.4]
- Mechanism (384): rays -4.2 [-6.8, -1.5]; dlvl6 +4.7 [+1.9, +7.5]; dlvl10 +2.1 [+0.2, +4.0]; starved +1.6
  [-0.1, +3.2] (games that live longer starve more); died -0.3; ants +0.5. Crashes: same types (Cyclic Panic
  5 vs 5), watchdog 9 vs 8
- Decision: kept; merged to `main` (code identical to `3fca503`), 426 tests pass. New current baseline `3fca503`.

#### Experiment 6: `exp/zappers` - leave the zap line of a monster seen zapping
- Requirement / decisions: SURV-03; tactic leave-zap-line from `### Wand and ray users diagnosis (SURV-03)` (Z2 warned
  76.6%); after Experiment 5 the target is the unnamed zappers ("The <monster> zaps"): 50 of 2304 games on `0b09707`
- Change: `drop_zap_line_moves` (`autoascend/combat/fight_heur.py`): in `fight2`, drop moves that end on a row,
  column or diagonal within 8 squares of a monster seen zapping in the last 300 turns (unless every move would),
  +10 to kept moves while standing on such a line. Counter `zap_line_dodge`.
- Candidate `d7d5e6b1442b9467005b1213febc1584c2b31ca3` (36588cb rebased onto the shop-door baseline); baseline
  `3fca503215e1a3de57e775378a1598fb05a40c20`; primary metric `rung2` (19 of 50 targeted deaths, 38%, had rung >= 2:
  below the 60% rule); games: screen at 384, then to the last checkpoint
- Smoke (22 baseline unnamed-zapper death seeds): counter fired in 9 of 22, no exceptions, no watchdog
- Mechanism metrics: `rays`, `died`, `dlvl6`, `dlvl10`
- Screen (384 seeds, 80%): rung2 +0.8 [-0.4, +2.0]; not dropped (rays +1.3 [+0.2, +2.4] at 384, leaning worse)
- Job 24: Verdict: no measurable difference at 2304 games per side, diff +0.1 points, 95% interval [-0.8, +0.9]
- Mechanism: rays +0.2 [-0.5, +0.9]; died +0.1; dlvl6 -0.4 [-1.1, +0.4]; dlvl10 +0.2 [-0.8, +1.2]; crashes: same
  types, exception 51 vs 50, watchdog 45 vs 49
- Reading: the dodge fired in 9 of 22 smoke games but ray deaths did not fall; most rays come from monsters the bot
  has not seen zap yet (first zap kills or the zapper is out of sight), and dodging moves cost tempo in the fight.
- Decision: dropped (branch `exp/zappers` kept at `d7d5e6b1442b9467005b1213febc1584c2b31ca3`)
- Shop-door effect over 2304 seeds (baseline store): named-zapper (shopkeeper) deaths 118 on `0b09707`, 34 on
  `3fca503`

#### Experiment 7: `rejudge/threat-model` - re-judge the old threat model (variant fdf6b48, real danger only)
- Requirement / decisions: SURV-05 (D-12 each old branch judged once on the seeded bench, D-13)
- Change: `threat-model` code diff (`fdf6b48` against its merge base `2f75c61`): `combat/threat.py`,
  `combat/monster_data.py` (generated by `scripts/gen_monster_data.py`), `monster_utils.py` danger from real
  monster data, `fight_heur.py` 2 lines; the docs/superpowers history files are left out
- Candidate `82848115dd0faad1d2e48dba3142bb1a484947f2` (original `fdf6b48e7ca9792c5944d6f969fc51f7adf434d9`); baseline
  `3fca503215e1a3de57e775378a1598fb05a40c20`; primary metric `rung2`; games: screen at 384, then to the last checkpoint
- Smoke (seeds 0-21): 440 tests pass; 20 died, seed 15 Cyclic Panic AssertionError (baseline seed 15: Cyclic Panic
  AssertionError at inventory.py, same type), seed 2 watchdog at depth 23 (baseline seed 13 watchdog)
- Mechanism metrics: `died`, `ants`, `dlvl6`, `dlvl10`
- Screen (384 seeds, 80%): rung2 +0.3 [-2.1, +2.6]; not dropped
- Job 25: Verdict: no measurable difference at 2304 games per side, diff +0.3 points, 95% interval [-1.2, +1.7]
- Mechanism: died +0.8 [-0.1, +1.6]; ants -0.2 [-1.4, +0.9]; dlvl6 -1.0 [-2.3, +0.3]; dlvl10 -1.6 [-3.2, -0.0]
  (leaning worse); crashes: fewer (exception 40 vs 50, watchdog 37 vs 49), same types
- Decision: dropped (branches `threat-model` `fdf6b48` and `rejudge/threat-model` `8284811` kept for plan 01-16)

#### Experiment 8: `rejudge/choke-points` - re-judge the old choke-point fighting branch
- Requirement / decisions: SURV-05 (D-12 judged once, D-13)
- Change: `choke-points` code diff (`b31e926` against its merge base `aa4b1cf`): `combat/fight_heur.py` prefers
  fighting from a corridor or doorway square when several hostiles are near; `tests/test_choke_points.py`
- Candidate `339a63c5c31f5891d4dcfb1c87d556ab25600272` (original `b31e926`); baseline
  `3fca503215e1a3de57e775378a1598fb05a40c20`; primary metric `rung2`; games: screen at 384, then to the last checkpoint
- Smoke (seeds 0-21): 431 tests pass; 19 died, 1 Cyclic Panic AssertionError, 2 watchdog (both types in the
  baseline); median depth 9
- Mechanism metrics: `died`, `ants`, `dlvl6`, `dlvl10`
- Screen (384 seeds, 80%): rung2 +2.9 [+0.9, +4.8]; not dropped
- Job 26: Verdict: no measurable difference at 2304 games per side, diff +1.2 points, 95% interval [-0.1, +2.5]
- Mechanism: died -0.5 [-1.5, +0.4]; ants +0.1 [-0.9, +1.1]; dlvl6 +0.3 [-0.8, +1.4]; dlvl10 +0.3 [-1.2, +1.9];
  starved +0.3; crashes: exception 63 vs 50 (more, same Cyclic Panic types), watchdog 46 vs 49
- Reading: the closest miss so far, but the deeper metrics do not move, so the rung2 gain is early-game only.
- Decision: dropped (branches `choke-points` `b31e926` and `rejudge/choke-points` `339a63c` kept for plan 01-16)

#### Experiment 9: `rejudge/flee-upstairs` - re-judge the old flee-upstairs branch
- Requirement / decisions: SURV-05 (D-12 judged once, D-13)
- Change: `flee-upstairs` code diff (`a535f7a` against its merge base `0c7acbc`): `fight_heur.flee_upstairs_action`
  climbs (or walks to) the up stairs when a dangerous monster (soldier ant, killer bee, ...) is near; counter
  `flee_upstairs`. Rebase conflicts: kept both stats_logger counters; kept main's `game.py` (the branch's
  `GameResult.flee_upstairs` field is dropped, the counter is in `events`)
- Candidate `757aad8893bfd9155f14e9122aec1e122b8b51c5` (original `a535f7a`); baseline
  `3fca503215e1a3de57e775378a1598fb05a40c20`; primary metric `rung2`; games: screen at 384, then to the last checkpoint
- Smoke (seeds 0-21): 433 tests pass; flee_upstairs fired in 8 of 22; 21 died, 1 watchdog, no exceptions
- Mechanism metrics: `died`, `ants`, `dlvl6`, `dlvl10`
- Screen (384 seeds, 80%): rung2 -0.3 [-2.4, +1.9]; not dropped
- Job 27: Verdict: no measurable difference at 2304 games per side, diff +0.5 points, 95% interval [-0.9, +1.9]
- Mechanism: died +0.4 [-0.5, +1.3]; ants +0.3 [-0.7, +1.3]; dlvl6 +0.4 [-0.7, +1.4]; dlvl10 +0.3 [-1.2, +1.8];
  crashes: same types, exception 46 vs 50, watchdog 43 vs 49
- Decision: dropped (branches `flee-upstairs` `a535f7a` and `rejudge/flee-upstairs` `757aad8` kept for plan 01-16)

### Phase 1 result (SURV-06)
Final main `p1-final` = `3fca503215e1a3de57e775378a1598fb05a40c20` (Current baseline; main differs only in
PORTING.md) against the pilgrim-only baseline `p1-baseline` = `0b097073adb3071f8e5c2aea954618a3320a5bc7`.

| metric | job | verdict | checkpoint | diff [lo, hi] in points |
|--------|-----|---------|------------|-------------------------|
| rung2 | 28 | better | 384 | +3.1 [+0.8, +5.4] |
| rung3 | 29 | better | 576 | +1.7 [+0.2, +3.3] |
| rung4 | 30 | better | 1152 | +0.9 [+0.2, +1.6] |
| rung5 | 31 | better | 1152 | +1.0 [+0.2, +1.8] |
| rung6 | 32 | better | 384 | +1.8 [+0.1, +3.6] |

Each row is its own paired job on stored games (D-14 decision rule: rung2 `better` and no rung3-6 `worse`).
The single kept change is exp/shop-door; the gain is small (1-3 points per rung) but is seen on every rung.

Phase 1 result: met (rung2 +3.1 [+0.8, +5.4] points; rungs 3-6 not worse)

### Branch cleanup (D-13)
All three old survival branches were judged once (experiments 7-9) and none was kept, so both the original and
its `rejudge/` copy are due for deletion. Owner choice (2026-10-25): archive-tags - each SHA is kept as a
local `archive/` tag (restore with `git branch <name> archive/<name>`), then the branch is deleted.

| branch | full SHA | verdict | interval (points) | status |
|--------|----------|---------|-------------------|--------|
| `threat-model` | `fdf6b48e7ca9792c5944d6f969fc51f7adf434d9` | no measurable difference (job 25) | +0.3 [-1.2, +1.7] | archived as tag `archive/threat-model`, branch deleted 2026-10-25 |
| `rejudge/threat-model` | `82848115dd0faad1d2e48dba3142bb1a484947f2` | no measurable difference (job 25) | +0.3 [-1.2, +1.7] | archived as tag `archive/rejudge-threat-model`, branch deleted 2026-10-25 |
| `choke-points` | `b31e9266c67b6dff19d0bf576577d887e9809adb` | no measurable difference (job 26) | +1.2 [-0.1, +2.5] | archived as tag `archive/choke-points`, branch deleted 2026-10-25 |
| `rejudge/choke-points` | `339a63c5c31f5891d4dcfb1c87d556ab25600272` | no measurable difference (job 26) | +1.2 [-0.1, +2.5] | archived as tag `archive/rejudge-choke-points`, branch deleted 2026-10-25 |
| `flee-upstairs` | `a535f7a872d0bf9fd790cddeddacaad781cf3c90` | no measurable difference (job 27) | +0.5 [-0.9, +1.9] | archived as tag `archive/flee-upstairs`, branch deleted 2026-10-25 |
| `rejudge/flee-upstairs` | `757aad8893bfd9155f14e9122aec1e122b8b51c5` | no measurable difference (job 27) | +0.5 [-0.9, +1.9] | archived as tag `archive/rejudge-flee-upstairs`, branch deleted 2026-10-25 |

## Phase 2: real descent

Phase 2 baseline: `6502ae339853c3d24570865816b1ddedfe19b566` (tag `p2-baseline`, job 33, 2304 seeded games)
Current baseline: `6502ae339853c3d24570865816b1ddedfe19b566`

Measurement only on top of `p1-final`: exact Mines' End rung from the game's own dungeon table (02-01), a stuck
report each time the stuck watch gives up, end level, watchdog stack, metric `free5` (02-02/02-03).

**Replay against p1-final** (`replay_check.py p1-final p2-baseline --fields <shared> --skip-end watchdog`):
2255 seeds compared, 1 mismatched, exit 1. The one mismatch is seed 689, whose crash text names
`global_logic.py:458` versus `:476`: the file grew by the stuck-report lines, the crash is the same. With
`end_reason` left out: 2255 compared, 0 mismatched, exit 0. Play is unchanged; the gate's exit 1 is accepted
for this reason (deviation from plan 02-03, which asked for exit 0 on the full list).

**Ladder** (2304 games): Mines 1770 (77%), Minetown 1074 (47%), Oracle 748 (32%), Sokoban 466 (20%), Sokoban
solved 407 (18%), Mines' End 395 (17%), Dlvl 15+ 210 (9.1%), Quest 38 (1.6%), Medusa 18 (0.8%), Castle 0.

**DESC-01 evidence:** seed 0 has a 9-level Mines and records Mines' End at turn 12583; seed 2 has an 8-level
Mines and records it at turn 13010 (sizes read with `dungeon_truth`). The old proxy could not fire on an
8-level Mines before 1000 turns without a `>`; rung 6 now counts arrivals on the real bottom.

**free5** = 82.2% (1894 of 2304); 410 games end stuck at Dlvl 5+. By the cause of their last stuck report:

| Bucket | Games | % | Median Dlvl | closed doors > 0 | boulders > 0 | going up |
|---|---|---|---|---|---|---|
| stairs-unreachable | 107 | 26.1% | 6 | 23 | 59 | 56 |
| stairs-reachable | 102 | 24.9% | 6.5 | 37 | 66 | 55 |
| explore-left | 113 | 27.6% | 9 | 35 | 57 | 2 |
| no-way-found | 79 | 19.3% | 7 | 26 | 26 | 11 |
| no-report | 9 | 2.2% | 7 | 0 | 0 | 0 |

All 3088 stuck events: DIVE 1673, FIND_GNOMISH_MINES 504, FIND_MINETOWN 441, FIND_SOKOBAN 390, FIND_MINES_END
63; by dungeon Mines 1800, Dungeons of Doom 1209, Sokoban 79. Stuck endings: death 221, starved 128,
watchdog 49, exception 11. Watchdog stacks sit in exploration searches (`to_search_func`, `_level_dfs`,
`open_visit_search`) at median Dlvl 24: slow searches on big deep levels, not one loop.

Plan 02-05 rule (35%): no bucket reaches 35% -> **frontier-first** (explore-left is also the largest bucket).
About half of the stairs buckets are going up (out of the Mines), which the stuck tactics must cover.

### Experiments

| # | branch | cause | candidate | baseline | metric | verdict | diff [lo, hi] | decision |
|---|--------|-------|-----------|----------|--------|---------|---------------|----------|
| 10 | `exp/mines-end` | Mines' End goal ends on the real bottom (screen) | `b06d9fe` | `6502ae3` | rung7 | no measurable difference @ 2304 | +0.0 [-0.2, +0.3] | dropped |
| 11 | `exp/stuck-1` | frontier-first when stuck (DESC-03 rule) | `73c4584` | `6502ae3` | free5 | pending | - | - |

#### Experiment 10: `exp/mines-end` - Mines' End goal ends on the real bottom, judged from the screen
- Requirement / decisions: DESC-01 (D-04: screen only, no memory)
- Change: `mines_bottom_reached` in `autoascend/global_logic.py` (Mines level >= 9, or level 8 with no `>` and
  no frontier) is the FIND_MINES_END condition, replacing "Mines level 9", which an 8-level Mines never meets
- Candidate `b06d9fe4e48afa9436080f8bcbe43293a4778fdc`; baseline `6502ae339853c3d24570865816b1ddedfe19b566`; primary metric `rung7` (the
  change ends the Mines' End stay early, so more games should reach Dlvl 15+); games: to the last checkpoint
  (diagnosis-backed)
- Smoke (19 seeds with an 8-level Mines and rung 6 in p2-baseline): counter fired in 3; exceptions 2
  (monster_tracker ValueError, item_manager AssertionError: both types in p2-baseline), watchdog 1
- Job 34: Verdict: no measurable difference at 2304 games per side, diff +0.0 points, 95% interval [-0.2, +0.3]
  (9 discordant pairs)
- Mechanism: rung6 -0.1 [-0.2, +0.0]; starved +0.0 [+0.0, +0.0]; free5 -0.1 [-0.4, +0.1]; counter
  `mines_end_by_screen` fired in 22 of 2304 games; crashes: same types, exception 52 vs 50, watchdog 49 vs 49
- Why so small: few games still follow FIND_MINES_END (63 stuck events in the baseline); most reach the Mines
  bottom while diving, where the stuck watch already sends them back up
- Decision: dropped (branch `exp/mines-end` kept at `b06d9fe4e48afa9436080f8bcbe43293a4778fdc`)

#### Experiment 11: `exp/stuck-1` - frontier-first when the stuck watch fires
- Requirement / decisions: DESC-03, DESC-02 (rule in `### Stuck diagnosis (DESC-03)`)
- Change: `GlobalLogic._frontier_first` in `autoascend/global_logic.py`: when stuck, walk to the nearest reachable
  square beside unexplored map until none is left or 1000 turns pass (once per level), then retry the level
- Candidate `73c45844eb41c36e3970a2c08340f746dd492684`; baseline `6502ae339853c3d24570865816b1ddedfe19b566`; primary metric `free5` (the tactic
  targets games that end stuck on Dlvl 5+); games: to the last checkpoint (diagnosis-backed)
- Smoke (12 explore-left seeds + seeds 0-9): counter fired in 15 of 22; 1 exception (inventory.py
  AssertionError, a type in p2-baseline), no watchdog
- Mechanism (planned): starved, rung2, rung6, rung7, turns, counter `frontier_first`
- Verdict: pending
