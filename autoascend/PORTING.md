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

### Experiments

Current baseline: `0b097073adb3071f8e5c2aea954618a3320a5bc7` (pilgrim-only baseline)

| # | Branch | Cause | Candidate | Baseline | Metric | Verdict | Diff [lo, hi] (points) | Decision |
|---|--------|-------|-----------|----------|--------|---------|------------------------|----------|
