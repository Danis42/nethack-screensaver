# Roadmap: screens

## Overview

The screensaver, the secret strategies, the bench server, the ascension ladder and the seeded
paired bench are already built and working on local `main`. What is left is the project's real
objective: a bot that ascends. The eight phases below are roadmap sub-projects 1-8 from
`docs/ROADMAP.md`, in that order, each climbing a stretch of the 17-rung ladder: first survive the
midgame so more games reach Minetown and Sokoban, then descend for real, gear up, and take on
Medusa, the Castle, the Quest, Gehennom and finally the Planes. Every phase is judged the same way:
one change per experiment on the seeded paired `screens-bench` against a stored pilgrim-only
baseline, reading ladder rung metrics. Reaching a rung is progress; rung 17 is the goal.

Notes on the shape:
- Rung targets are copied from `docs/ROADMAP.md`. Where two phases list the same rung (6, 8, 9) the
  later phase owns finishing the behaviour; the earlier one supplies what it needs.
- Nothing above rung 8 has ever been reached in a natural game, so Phases 4-8 are exercised with the
  staged-start harness built in Phase 4 (STAGE-01), reported separately from natural-play numbers.
  Only the final Phase 8 criterion is a natural, unstaged ascension.
- Humans do the Quest (Phase 6) before Medusa (median turn 22426 vs 29317). The order here follows
  `docs/ROADMAP.md`; Phases 4-6 can be reordered later with `/gsd-phase` since Phase 6 does not need
  Phases 4-5.
- Granularity: no `.planning/config.json` exists yet, so the default applies; eight phases are used
  because the project's own roadmap defines eight sub-projects, each with its own spec, plan and build.

## Delivered Before This Roadmap

Existing capabilities, recorded in PROJECT.md "Validated"; none of these are phases to build:
- Screensaver, launcher, zsh hook, renderer, config and game log (v0.1.0)
- AutoAscend port to Python 3.13 / NLE 1.3.0 and the four secret strategies, with pilgrim-only as the default (v0.2.0, `dbab398`)
- Bench server with status page, MCP tools, JSON API, real-ascension import (687 yardstick ascensions)
- Ascension ladder: 17 rungs, `GameResult.ladder` / `rung`, `rung`/`rung1`..`rung17` metrics (main `2653410`)
- Seeded, paired experiments: `run_game(seed=...)`, `play <seed>`, paired verdict (merged `9ff6a6f`)

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work, equal to roadmap sub-project numbers 1-8
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Midgame Survival** - Sharpen the bench, baseline the pilgrim route, then cut the deaths on Dlvl 4-12 (rungs 2-6)
- [ ] **Phase 2: Real Descent** - Finish the Mines, keep descending past the Big Room, find downstairs reliably, reach the Quest on purpose (rungs 6-8)
- [ ] **Phase 3: Gearing Up** - Wands, rings, armour, protection, reflection, magic resistance (rungs 7-9)
- [ ] **Phase 4: Medusa's Level** - Late-game test harness, then survive and cross Medusa (rung 9)
- [ ] **Phase 5: Castle and Wishes** - Get into the Castle, take the wand of wishing, wish well (rung 10)
- [ ] **Phase 6: The Quest** - Reach XL 14, pass the leader, kill the nemesis, bring back the Bell (rung 8)
- [ ] **Phase 7: Gehennom** - Mazes, Vlad's Tower, Wizard's Tower, invocation (rungs 11-14)
- [ ] **Phase 8: Planes and Ascension** - Climb out with the Amulet, cross the Planes, offer it (rungs 15-17)

## Phase Details

### Phase 1: Midgame Survival
**Goal**: The pilgrim bot dies measurably less often on Dlvl 4-12, so more games reach Minetown, Sokoban and Mines' End, and the bench can see 1-3 point effects.
**Depends on**: Nothing (first phase); builds on the delivered ladder and seeded bench
**Requirements**: MEAS-01, MEAS-02, MEAS-03, SURV-01, SURV-02, SURV-03, SURV-04, SURV-05, SURV-06
**Rungs targeted**: 2-6
**Success Criteria** (what must be TRUE):
  1. A seeded A/A control (same commit on both sides of a `screens-bench` experiment) ends with "no measurable difference" and an interval clearly narrower than the unseeded ~3.5-point detectable difference.
  2. A pilgrim-only baseline of `main` (seeds 0..575) is stored, and its 17-rung table (games per rung, median turn against the yardstick) is written into `autoascend/PORTING.md`, with the older mixed-strategy numbers marked not comparable.
  3. Resting to full HP, starvation, wand/ray users, and ants/killer bees each have a recorded paired verdict: `better` changes are merged to `main`, the rest are dropped and logged with their interval; the three unmerged branches (`threat-model`, `flee-upstairs`, `choke-points`) are each re-judged once on the seeded bench.
  4. The final `main` of this phase against the pilgrim-only baseline gives a paired `better` verdict on `rung2` (Minetown+), and rungs 3-6 are not worse.
**Plans:** 14 plans

Plans:
- [ ] 01-01-PLAN.md — Seeded games replay across processes and dates (moon from the seed) and record their death context
- [ ] 01-02-PLAN.md — Live Sokoban solver on a measured state budget, workers with a fixed hash seed
- [ ] 01-03-PLAN.md — Read-only seeded-bench tools: verdict, pairs, ladder, killers, deaths, replay check, seeded smoke runs
- [ ] 01-04-PLAN.md — NLD-NAO human study: prayer-outcome strings and Dlvl 4-12 food/prayer habits (D-10)
- [ ] 01-05-PLAN.md — Seeded A/A control and D-04 gate; STATUS.md/handoff.txt become pointers (D-02)
- [ ] 01-06-PLAN.md — Bench calibration: divergence controls, lgen and 2304-checkpoint decisions
- [ ] 01-07-PLAN.md — Pilgrim-only baseline stored and tabled (MEAS-02); survival-tuning removed
- [ ] 01-08-PLAN.md — Starvation: diagnosis with bot and human data, killer order, one or two experiments
- [ ] 01-09-PLAN.md — Rest to full HP before exploring on, judged on the bench
- [ ] 01-10-PLAN.md — Ants and killer bees: diagnosis-chosen new tactic, judged on the bench
- [ ] 01-11-PLAN.md — Wand and ray users: diagnosis-chosen tactic, judged on the bench
- [ ] 01-12-PLAN.md — Re-judge threat-model, choke-points, flee-upstairs once each (SURV-05)
- [ ] 01-13-PLAN.md — Done bar: final main vs baseline, rung2 better and rungs 3-6 not worse (D-14)
- [ ] 01-14-PLAN.md — D-13 branch cleanup behind a one-way decision checkpoint

### Phase 2: Real Descent
**Goal**: The bot completes the Mines, goes back up and keeps descending the main dungeon past the Oracle and the Big Room, reliably finds downstairs, and enters the Quest portal on purpose.
**Depends on**: Phase 1
**Requirements**: DESC-01, DESC-02, DESC-03, DESC-04, DESC-05
**Rungs targeted**: 6-8
**Success Criteria** (what must be TRUE):
  1. In both an 8-level and a 9-level Mines game, rung 6 (Mines' End) is recorded on arrival at the real bottom level, with no waiting-timer proxy.
  2. Fewer games end stuck on a level they cannot leave (`unsticks` and watchdog end reasons at Dlvl 5+) than in the Phase 1 result, shown as a paired verdict.
  3. The share of games reaching Dlvl 15+ (`rung7`, baseline 2%) is higher than in the Phase 1 result, paired verdict `better`.
  4. Rung 8 is recorded in more games than the single accidental baseline game, with a recorded game showing the bot recognising the Quest portal level and stepping through on purpose.
**Plans**: TBD

### Phase 3: Gearing Up
**Goal**: The bot arrives deep wearing and carrying what real ascenders do: armour with low AC, magic resistance, reflection, and working wands and rings.
**Depends on**: Phase 2
**Requirements**: GEAR-01, GEAR-02, GEAR-03, GEAR-04, GEAR-05, GEAR-06, GEAR-07
**Rungs targeted**: 7-9
**Success Criteria** (what must be TRUE):
  1. Bench results show, per game, final XL, AC, magic resistance, reflection, bag of holding, wands and rings, next to the real-ascender figures (MR 100%, bag of holding 99%, reflection 83%, median XL 23, AC -38).
  2. Median final AC is measurably better, and the share of games with a magic-resistance source and with a reflection source is measurably higher, each as a paired verdict against the Phase 2 result.
  3. Recorded games show wands and rings being identified and used on purpose, and the crash rate in a 576-game run is not higher than before (no new exception types).
  4. The Dlvl 15+ share (`rung7`) beats the Phase 2 result, and games that reach Dlvl 15+ carry what Medusa needs (reflection or a blindfold, plus a way over water) in a measurable share.
**Plans**: TBD

### Phase 4: Medusa's Level
**Goal**: The bot arrives on Medusa's level, survives her gaze, crosses the water and takes the downstairs; a late-game test harness makes this checkable without playing 20 levels first.
**Depends on**: Phase 3
**Requirements**: STAGE-01, MED-01, MED-02, MED-03
**Rungs targeted**: 9
**Success Criteria** (what must be TRUE):
  1. A bench game can start at a chosen late-game situation (Medusa's level with a standard kit), and staged results are reported separately, leaving natural-play rung rates untouched.
  2. Rung 9 is recorded only on Medusa's level itself (unit-tested and seen in a staged game), and a "crossed Medusa" fact is stored in the result when the level below is reached.
  3. In staged games the bot survives the gaze and takes the downstairs in a recorded share of runs (rate stored in `autoascend/PORTING.md`), including at least one game that crosses.
**Plans**: TBD

### Phase 5: Castle and Wishes
**Goal**: The bot gets into the Castle, takes the wand of wishing, and turns the wishes into gear it then wears.
**Depends on**: Phase 4
**Requirements**: CAST-01, CAST-02, CAST-03
**Rungs targeted**: 10
**Success Criteria** (what must be TRUE):
  1. Rung 10 is recorded on the Castle level exactly (unit-tested), and staged games show the bot getting in past the moat and drawbridge.
  2. A staged game ends with the wand of wishing in the bot's inventory, recorded as a fact in the result.
  3. After wishing, the inventory holds items from the defined wish list and the bot wears or uses them, shown by the stored inventory of staged games.
**Plans**: TBD

### Phase 6: The Quest
**Goal**: The bot reaches XL 14, is accepted by its Quest leader, clears the Quest and returns with the Bell of Opening.
**Depends on**: Phase 3 (and Phase 2's Quest portal entry)
**Requirements**: QUEST-01, QUEST-02, QUEST-03
**Rungs targeted**: 8
**Success Criteria** (what must be TRUE):
  1. Bench results show final XL, and the share of games reaching XL 14 is recorded per role and rises over the Phase 3 result.
  2. A staged game at the Quest home level with an XL 14 character shows the leader accepting the bot and the bot descending the Quest levels to the nemesis.
  3. A game ends with the Bell of Opening in inventory, stored as a bench-visible fact, for several of the roles the bot is randomly dealt.
**Plans**: TBD

### Phase 7: Gehennom
**Goal**: The bot enters Gehennom, descends its mazes, takes the Candelabrum and the Book of the Dead, and performs the invocation to get the Amulet of Yendor.
**Depends on**: Phase 5, Phase 6
**Requirements**: GEH-01, GEH-02, GEH-03, GEH-04
**Rungs targeted**: 11-14
**Success Criteria** (what must be TRUE):
  1. Staged games from the Castle drop into Gehennom (rung 11) and descend several maze levels, finding the downstairs on levels that are mazes rather than rooms.
  2. Rungs 12 (Vlad's Tower) and 13 (Book of the Dead in inventory) are each recorded exactly, and staged games take the Candelabrum and the Book.
  3. A staged game with Bell, Candelabrum and Book finds the vibrating square, completes the invocation (rung 14) and ends with the Amulet of Yendor in inventory.
**Plans**: TBD

### Phase 8: Planes and Ascension
**Goal**: The bot climbs out carrying the Amulet, crosses the Elemental Planes, reaches the Astral Plane and offers the Amulet, ending the game as an ascension.
**Depends on**: Phase 7
**Requirements**: PLANE-01, PLANE-02, PLANE-03
**Rungs targeted**: 15-17
**Success Criteria** (what must be TRUE):
  1. A staged game with the Amulet climbs out of the dungeon and enters the Elemental Planes (rung 15), crossing all four through their portals.
  2. A staged game reaches the Astral Plane (rung 16), finds its own god's altar and offers the Amulet, so the game's end reason says "ascended" (rung 17).
  3. At least one natural, unstaged seeded bench game on the pilgrim route ends "ascended", recorded in the bench results as rung 17 (the project's core objective).
  4. The same code run by the screensaver itself plays a game to its ascension ending on screen without breaking the terminal.
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4 -> 5 -> 6 -> 7 -> 8 (decimal insertions run between their neighbours)

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Midgame Survival | 0/14 | Planned | - |
| 2. Real Descent | 0/TBD | Not started | - |
| 3. Gearing Up | 0/TBD | Not started | - |
| 4. Medusa's Level | 0/TBD | Not started | - |
| 5. Castle and Wishes | 0/TBD | Not started | - |
| 6. The Quest | 0/TBD | Not started | - |
| 7. Gehennom | 0/TBD | Not started | - |
| 8. Planes and Ascension | 0/TBD | Not started | - |
