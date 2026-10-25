# Phase 2: Real Descent - Research

**Researched:** 2026-10-25 (inline, Claude)
**Domain:** AutoAscend descent logic, stuck levels, Mines' End and Quest portal recognition, bench measurement
**Confidence:** HIGH for the code and data findings (read from main and from the bench store); MEDIUM for
NetHack behaviour notes (from the 3.6 source as remembered, each marked where a plan must verify it)

## Summary

Phase 1 left `p1-final` = `3fca503` (2304 seeded Valkyrie pilgrim games stored). Its games say the pilgrim
route rarely runs as written: 1415 of 2304 games (61%) end in the `DIVE` milestone, the fallback the
`ProgressWatch` switches to after 2500 turns without a new level or milestone. Only 2 games reach the
route's own `GO_DOWN`. Every one of the 201 games that reached Dlvl 15+ was diving. Stuck levels are the
phase's main lever: 545 diving games logged `stuck_diving` (no downstairs found while diving), 401 of them
at Dlvl 5+.

**Primary recommendation:** measure first (exact Mines' End rung, a context row for every stuck event, the
end level, the watchdog stack), store `p2-baseline`, then attack stuck causes one at a time in the order the
diagnosis gives, then the Quest portal.

## Findings from the stored games (p1-final, 2304 seeds)

| Fact | Number | Source |
|------|--------|--------|
| final milestone DIVE | 1415 (61.4%) | `milestone` field |
| final milestone FIND_GNOMISH_MINES / FIND_MINETOWN / FIND_SOKOBAN | 289 / 307 / 238 | same |
| final milestone GO_DOWN / FIND_MINES_END | 2 / 15 | same |
| games that never reached the Mines (no rung) | 534 (23%): 277 still in FIND_GNOMISH_MINES, 244 diving | `ladder` empty |
| diving games with `stuck_diving` >= 1 | 545; 401 at Dlvl 5+ | `stuck_diving`, `depth_at_end` |
| starved | 606 (26.3%); 353 of them diving, 102 in FIND_GNOMISH_MINES, 101 in FIND_MINETOWN | end_reason |
| Dlvl 15+ (rung 7) | 210 (9.1%), all but one diving | ladder report |
| Quest entered (rung key `quest`) | 20 games, median XL 10, all by accident | `ladder` |
| watchdog endings | 49 (2.1%), median Dlvl 24 | end_reason |
| diving games ending above their max depth | 166 | depth_at_end < max_depth |

The ROADMAP's "rung7 baseline 2%" and "single accidental Quest game" come from the mixed-strategy bench
and are superseded (CONTEXT D-05).

## Code map

- `autoascend/plans.py`: `Milestone`, `Plan` (`advance`, `dive_instead`), `ProgressWatch(limit)`;
  pilgrim route for dwarves: BE_ON_FIRST_LEVEL, FIND_GNOMISH_MINES, FIND_MINETOWN, FIND_SOKOBAN,
  SOLVE_SOKOBAN, FIND_MINES_END, GO_DOWN.
- `autoascend/global_logic.py`: `STUCK_TURNS = 2500`; `current_strategy()` picks a target level per
  milestone; `FIND_MINES_END` targets `(GNOMISH_MINES, 9)` with condition "on Mines level 9" (TODO) - in
  an 8-level Mines it can never complete, so it ends through `_stuck()` and `dive_instead()`;
  `FIND_MINETOWN` targets `(GNOMISH_MINES, 4)` (TODO); on `_stuck()`: not diving -> `dive_instead()`;
  diving in the Mines -> `_mines_dive_over = True`; diving elsewhere -> counter `stuck_diving`;
  `dive()` takes the nearest known `>`.
- `autoascend/ladder.py`: `_mines_end` = Mines level >= 9, or level 8 with no `>` seen for 1000 turns
  (`MINES_END_WAIT`) - a proxy (DESC-01).
- `nethack_screensaver/game.py`: `run_game`, `_DeathContext` (observation-only), `_ScreenWatchdog`
  (itimer + turn stall), `GameResult` fields.
- `bench/metrics.py`: one line per metric; "better" means a higher rate, so a "fewer stuck games"
  metric must be phrased positively.

## NetHack facts the plans rely on

- **Mines depth (verified 2026-10-25 by reading memory):** the Mines have 8 or 9 levels
  (`dungeons[2].num_dunlevs`; seeds 1-8: 8,8,9,9,9,9,8,8), Mines' End is the last one.
- **Reading the dungeon layout (verified):** NLE loads libnethack from a memfd (`/memfd:nle.so` in
  `/proc/self/maps`); the lowest mapping address of that inode is the load base; `nm -D --defined-only -S`
  on `site-packages/nle/libnethack.so` gives `dungeons` (896 bytes = 16 x 56), `n_dgns`,
  `dungeon_topology` (56 bytes). `struct dungeon`: dname[24], proto[15], boneid, d_flags (4 bytes) at 40,
  entry_lev/num_dunlevs/dunlev_ureached (int8) at 44/45/46, ledger_start/depth_start (int32) at 48/52.
  `dungeon_topology`: 20 d_levels (2 bytes each) from offset 0 (oracle first), 4 int8 dnums at 40
  (tower, sokoban, mines, quest = 6, 4, 2, 3), then qstart, qlocate, nemesis, knox, mineend, sokoend at
  44..54 - `d_mineend_level` read (2, 8) on seed 1 and (2, 9) on seed 3. With several NLE instances in one
  process each has its own memfd; `run_game` holds one at a time, take the newest inode (plan 02-01 must
  test this against a second env).
- **Quest portal level (NetHack 3.6 do.c, MEDIUM):** on arriving at the level with the Quest's magic
  portal (`at_dgn_entrance("The Quest")`) the hero gets "You receive a faint telepathic message from
  <leader>..." the first time, a shorter reminder on later visits, while the quest is not done or
  expelled. The portal is a hidden trap (MAGIC_PORTAL) found by stepping on it or by searching next to it
  (about 1 in 8 per search, luck-dependent); stepping on it moves the hero to Quest level 1 (rung 8,
  "entered Home 1"). The portal is on Dlvl 11-16. Below XL 14 the leader only says to come back; the hero
  can step back through the arrival portal. Plan 02-07 must verify the wording against a recorded game
  (`last_messages`) or `nld_study.py` text from human games before relying on it.
- **Bottom of a dungeon:** no `>` exists on Mines' End; holes and trap doors cannot exist there.

## Candidate experiments (ranked by expected gain per bench hour; the diagnosis may reorder)

1. **Stuck cause #1** (DESC-03): chosen by a fixed rule from the stuck reports: downstairs seen but not
   reachable (boulder, locked door, water: kick/force/push), downstairs never seen with the reachable map
   exhausted (cheese: read unknown scrolls for magic mapping / teleport, jump into a known hole or trap door;
   new versus the dropped "smarter search"), or the route's target unreachable (milestone skips).
2. **Mines' End on the real bottom** (DESC-01 bot side): finish FIND_MINES_END on a Mines level >= 8 that
   has no `>` once its reachable map is explored, instead of waiting 2500 turns for the stuck watch.
3. **Stuck cause #2** (DESC-02/03): the next bucket.
4. **Quest portal on purpose** (DESC-05): recognise the telepathic message, walk/search the level for the
   portal, step through, come back, keep descending.

## Common pitfalls

1. **Measurement that changes play.** New observation code that calls agent methods with caches (`bfs()`)
   could change a game. Guard: `replay_check` against `p1-final` before the baseline (CONTEXT D-03).
2. **Metric direction.** `_verdict` calls a positive difference `better`; a "fewer stuck" metric must count
   the good outcome (`free5`: did not end stuck at Dlvl 5+).
3. **Rung 6 redefinition.** After 02-01 rung 6 counts differently, so `p1-*` rung6 numbers are not
   comparable; every Phase 2 comparison is against `p2-baseline`.
4. **Memory reads in a forked worker.** The bench worker plays games in one long process; each game makes a
   new env (new memfd). Always resolve the base per game, never cache it across games.
5. **Long stuck searches feed starvation.** A tactic that keeps the hero on a stuck level longer can trade
   stuck endings for starvation; `starved` is a mechanism metric for every stuck experiment.

## Validation Architecture

| Property | Value |
|----------|-------|
| Framework | pytest (`uv run pytest -q`; slow games `-m slow`) |
| Quick run | `uv run pytest -q tests/test_ladder.py tests/test_game.py tests/test_dungeon_truth.py` |
| Full suite | `uv run pytest -q -m ""` |
| Bench evidence | `scripts/seeded_report.py verdict / pairs / ladder / stuck`, `scripts/replay_check.py` |

| Requirement | Behaviour | Test type | Command |
|-------------|-----------|-----------|---------|
| DESC-01 | memory reader returns Mines size 8 on seed 1, 9 on seed 3, and the Mines' End level | unit (real env) | `uv run pytest -q tests/test_dungeon_truth.py` |
| DESC-01 | rung 6 fires on arrival at the true bottom, never before; falls back when truth is missing | unit | `uv run pytest -q tests/test_ladder.py -k mines_end` |
| DESC-01 | an 8-level and a 9-level baseline game record rung 6 at arrival | bench data | `seeded_report.py ladder p2-baseline` + `deaths` rows (plan 02-03) |
| DESC-02/03 | every stuck event leaves a context row; `free5` metric | unit + bench | `uv run pytest -q tests/test_game.py -k stuck`; `seeded_report.py stuck` |
| DESC-02..05 | changes kept only on paired `better` | bench | `seeded_report.py verdict <exp> --expect better` |
| DESC-05 | portal message recognised, portal walk, return | unit + smoke | `uv run pytest -q tests/test_quest_portal.py`; smoke seeds with `events.quest_portal_entered` |
| all | measurement changes do not change play | bench data | `scripts/replay_check.py p1-final p2-baseline --fields <shared> --skip-end watchdog` exit 0 |

Wave 0 gaps: `tests/test_dungeon_truth.py` and `tests/test_quest_portal.py` do not exist yet (created by
plans 02-01 and 02-07).

## Sources

- main `2f9f211` source (files above); bench store `results.db` games of `3fca503`
- NetHack 3.6.6 behaviour as in the source (dungeon.c, do.c, quest.c, trap.c); verified parts marked above
- Phase 1 PORTING.md (experiment log, dropped ideas), PROJECT.md Out of Scope
